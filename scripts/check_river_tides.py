"""Check the rendered bank data against the author's retained/tidal distinction."""
import json
from pathlib import Path
import numpy as np
from shapely import contains_xy
from shapely.geometry import Polygon
from shapely.ops import unary_union

import tide_levels as tl
ROOT=Path(__file__).resolve().parents[1]
def load(name):return json.loads((ROOT/name).read_text())
meta=load('docs/data/river-network.json')
core=load('docs/data/river-terrain.json')
ground=load('docs/data/ground-plan.json')
factory=load('docs/data/factory-buildings.json')
positions=np.fromfile(ROOT/'docs/data'/meta['positionFile'],dtype='<f4').reshape(-1,3)
silt=np.fromfile(ROOT/'docs/data'/meta['sedimentFile'],dtype='uint8')
assert len(silt)==len(positions)==meta['vertices']
assert meta['waterLevel']==core['waterLevel']==.06
retained={18,22,10018,10022}
assert set(meta['retainedWaterChannelIds'])==retained
assert set(meta['tidalChannelIds']).isdisjoint(retained)
head=set(meta['aboveTidalLimitChannelIds'])
assert head=={12,13}==tl.ABOVE_TIDAL_LIMIT,'Channelsea above Abbey Mill must stay above the tidal limit'
assert set(meta['tidalChannelIds']).isdisjoint(head)
assert 0 in meta['tidalChannelIds'],'Bow Creek must remain tidal'
x,y,z=positions.T
channels={r['id']:unary_union([Polygon(p[0],p[1:]) for p in r['polygons']]) for r in ground['rivers']+factory['westContext']['rivers']}
isolated=set(meta['isolatedWaterChannelIds'])
assert isolated=={1301,1302,1303}
assert isolated.isdisjoint(meta['tidalChannelIds'])
tidal=unary_union([g for k,g in channels.items() if k not in retained|isolated|head])
old=unary_union([g for k,g in channels.items() if k in retained])
above=unary_union([g for k,g in channels.items() if k in head])
tide=unary_union([Polygon(p[0],p[1:]) for p in meta['tide']['polygons']])
drains=unary_union([Polygon(p[0],p[1:]) for f in meta['marshDitches']['features'] for p in f['renderPolygons']])
marsh=unary_union([Polygon(p[0],p[1:]) for p in meta['marshDitches']['marshPolygons']])
assert tide.is_valid
assert tide.intersection(unary_union([g for k,g in channels.items() if k in isolated])).area<.001,'Animated tide entered isolated eastern water'
assert tide.intersection(old).area<.001,'Animated tide entered retained Old Lea'
assert tide.intersection(above).area<.001,'Animated tide passed the tidal limit at Abbey Mill'
assert tide.intersection(drains.union(marsh)).area<.001,'Animated tide entered marsh or isolated drains'
assert tidal.difference(tide).area<.001,'Animated tide missed a tidal channel'
assert tide.difference(tidal).area>10000,'No room for water to cover the mud shelves'
# Levels come from the OS register (data/maps/os-tide-levels.json).
assert (meta['tide']['low'],meta['tide']['high'],meta['retainingEdges']['crestHeight'])==(tl.LOW,tl.HIGH,tl.CREST)
assert meta['tide']['low']<meta['waterLevel']<meta['tide']['high']<meta['retainingEdges']['crestHeight']
assert meta['retainingEdges']['crestHeight']-meta['tide']['high']>=.5
assert meta['retainingEdges']['baseHeight']<meta['tide']['low'],'Walls must reach below low water'
# The OS mud flats are tidal: inside the moving water, exposed at low water, covered at high.
assert tl.flats.difference(tide).area<1,'OS mud flat outside the tidal water'
flat=contains_xy(tl.flats.difference(tidal.buffer(1)),x,z)
assert flat.sum()>2000
assert np.percentile(y[flat],5)>meta['tide']['low'] and np.percentile(y[flat],95)<meta['tide']['high'],'Mud flat not between low and high water'
assert np.median(silt[flat])>200,'Mud flat not drawn as mud'
# Tidal channels hold water at low water away from their edges.
deep=contains_xy(tidal.buffer(-4),x,z)&(contains_xy(Polygon([(-1300,-1000),(300,-1000),(300,1400),(-1300,1400)]),x,z))
assert deep.sum()>10000 and np.percentile(y[deep],90)<meta['tide']['low'],'Tidal bed above low water'
# Exclude confluences: a tidal neighbour may legitimately supply the near bank.
old_margin=old.buffer(7).difference(old).difference(tidal.buffer(10))
mask=contains_xy(old_margin,x,z)
assert mask.sum()>1000
assert np.max(silt[mask])==0,'Tidal mud leaked into the retained Old Lea reach'
for key in [0,1,2,3,14]:
 g=channels[key]
 mask=contains_xy(g.buffer(8).difference(g),x,z)&(y>meta['tide']['low'])&(silt>180)
 assert mask.sum()>100,(key,'missing exposed tidal shelf')
 assert np.percentile(y[mask],95)<meta['tide']['high']+.5,(key,'mud on bank crest')
# No tidal mud along the still Channelsea above Abbey Mill.
for key in head:
 g=channels[key]
 mask=contains_xy(g.buffer(8).difference(g.buffer(1)),x,z)&(z<-60)
 assert mask.sum()>100 and np.percentile(silt[mask],90)<120,(key,'tidal mud above the tidal limit')
print('Tide checks passed: OS levels; exposed shelves on five reaches and the OS mud flats; moving water covers tidal channels, shelves and flats, stops at Abbey Mill, excludes Old Lea, marsh and drains, and stays below retaining crests.')
