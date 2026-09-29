"""Check the rendered bank data against the author's retained/tidal distinction."""
import json
from pathlib import Path
import numpy as np
from shapely import contains_xy
from shapely.geometry import Polygon
from shapely.ops import unary_union

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
assert 0 in meta['tidalChannelIds'],'Bow Creek must remain tidal'
x,y,z=positions.T
channels={r['id']:unary_union([Polygon(p[0],p[1:]) for p in r['polygons']]) for r in ground['rivers']+factory['westContext']['rivers']}
tidal=unary_union([g for k,g in channels.items() if k not in retained])
old=unary_union([g for k,g in channels.items() if k in retained])
tide=unary_union([Polygon(p[0],p[1:]) for p in meta['tide']['polygons']])
drains=unary_union([Polygon(p[0],p[1:]) for f in meta['marshDitches']['features'] for p in f['renderPolygons']])
marsh=unary_union([Polygon(p[0],p[1:]) for p in meta['marshDitches']['marshPolygons']])
assert tide.is_valid
assert tide.intersection(old).area<.001,'Animated tide entered retained Old Lea'
assert tide.intersection(drains.union(marsh)).area<.001,'Animated tide entered marsh or isolated drains'
assert tidal.difference(tide).area<.001,'Animated tide missed a tidal channel'
assert tide.difference(tidal).area>10000,'No room for water to cover the mud shelves'
assert meta['tide']['low']==meta['waterLevel']<meta['tide']['high']<meta['retainingEdges']['crestHeight']
assert meta['tide']['high']<=1.1,'Regular tide must not restore the rejected 1.4 m flood-like setting'
assert meta['retainingEdges']['crestHeight']-meta['tide']['high']>=.5
# Exclude confluences: a tidal neighbour may legitimately supply the near bank.
old_margin=old.buffer(7).difference(old).difference(tidal.buffer(10))
mask=contains_xy(old_margin,x,z)
assert mask.sum()>1000
assert np.max(silt[mask])==0,'Tidal mud leaked into the retained Old Lea reach'
for key in [0,1,2,3,13,14]:
 g=channels[key]
 mask=contains_xy(g.buffer(8).difference(g),x,z)&(y>meta['waterLevel'])&(silt>180)
 assert mask.sum()>100,(key,'missing exposed tidal shelf')
 assert np.percentile(y[mask],95)<1.4,(key,'mud on bank crest')
print('Tide checks passed: exposed shelves on six reaches; moving water covers tidal channels and shelves, excludes Old Lea, marsh and drains, and stays below retaining crests.')
