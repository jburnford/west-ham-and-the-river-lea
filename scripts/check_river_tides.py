"""Check the rendered bank data against the author's retained/tidal distinction."""
import json
from pathlib import Path
import numpy as np
from shapely import contains_xy
from shapely.geometry import Polygon, LineString, Point
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
# No tidal water across a street that has no bridge deck: streets run on over culverted
# passages (the House Mill race passes under Three Mills Lane on a deck since task D).
infrastructure=load('docs/data/infrastructure.json')
decks=unary_union([LineString(b['route']).buffer(b['width']/2+2,cap_style=2) for b in infrastructure['roadBridges']])
streets=unary_union([LineString(r['route']).buffer(r['width']/2,cap_style=2,join_style=2) for r in infrastructure['roads'] if len(r['route'])>1]).difference(decks)
assert tide.intersection(streets).difference(tidal).area<1,'Tidal water drawn across a street'
# Tidal channels hold water at low water away from their edges, except the silted back rivers.
silted=unary_union([channels[k] for k in tl.BACK_RIVER_ABOVE])
deep=contains_xy(tidal.difference(silted).buffer(-4),x,z)&(contains_xy(Polygon([(-1300,-1000),(300,-1000),(300,1400),(-1300,1400)]),x,z))
assert deep.sum()>10000 and np.percentile(y[deep],90)<meta['tide']['low'],'Tidal bed above low water'
# The silted back rivers (data/maps/back-river-beds.json): a low-water stream at Three Mills, the
# bed rising to shoals at the heads, the Pudding Mill River dry at low water; all covered at high water.
silt_meta=meta['backRiverBeds'];profile=tl.BACK_RIVER_PROFILE
assert silt_meta['channelIds']==sorted(tl.BACK_RIVER_ABOVE) and silt_meta['maxFloorSceneY']==tl.BACK_RIVER_MAX_FLOOR
bed=contains_xy(silted.buffer(-1),x,z)
assert bed.sum()>10000 and y[bed].min()>=profile['outlet']['sceneY']-.01 and y[bed].max()<meta['tide']['high'],'silted bed outside its range'
# The heads lie in the regional reaches (river-system-1900.json), so the thalweg is read from both meshes.
system=load('docs/data/river-system-1900.json')
sysp=np.fromfile(ROOT/'docs/data'/system['positionFile'],dtype='<f4').reshape(-1,3)
back_water=unary_union([Polygon(q[0],q[1:]) for q in silt_meta['waterPolygons']])
both=np.vstack([positions,sysp]);both=both[contains_xy(back_water.buffer(-1),both[:,0],both[:,2])]
assert set(system['tidalReachIds'])>={'Lower_River_Lea-4','Lower_River_Lea-7','Lower_River_Lea-8'},'regional back rivers not tidal'
def thalweg(point,radius=25):
 near=np.hypot(both[:,0]-point[0],both[:,2]-point[1])<radius
 assert near.sum()>20,point
 return both[near,1].min()
assert abs(thalweg(profile['outlet']['point'])-profile['outlet']['sceneY'])<.1,'no low-water stream at Three Mills'
assert thalweg(profile['outlet']['point'])<meta['tide']['low']
for h in profile['heads']:
 assert thalweg(h['point'])>profile['headSceneY']-.35,(h['what'],'head not silted')
pudding=contains_xy(unary_union([channels[k] for g in tl.back_rivers['groups'] if g['aboveProfileMetres']>0 for k in g['channelIds']]).buffer(-1),x,z)
assert pudding.sum()>1000 and y[pudding].min()>meta['tide']['low']+1,'Pudding Mill River not dry at low water'
# The low-water stream (lowWaterStream): the Lea down the silted beds from the heads to Three Mills,
# a foot over the thalweg, never below low water; none on the Pudding Mill River.
stream=meta['lowWaterStream']
sp=np.fromfile(ROOT/'docs/data'/stream['positionFile'],dtype='<f4').reshape(-1,3)
si=np.fromfile(ROOT/'docs/data'/stream['indexFile'],dtype='<u4')
assert len(sp)==stream['vertices'] and len(si)==stream['triangles']*3 and si.max()<len(sp)
assert sp[:,1].min()>=meta['tide']['low'] and sp[:,1].max()<=profile['headSceneY']+.31,'stream outside its levels'
passages=unary_union([Polygon(q[0],q[1:]) for r in meta['reviewedConnections']['connections'] if r['id'] in meta['backRiverBeds']['siltedPassages'] for q in r['polygons']])
assert contains_xy(back_water.buffer(1.5),sp[:,0],sp[:,2]).all(),'stream outside the back rivers'
from back_river_profile import profile as back_river_profile
back=back_river_profile()
def has_stream(point):
 iz,ix=back.cells(np.array([point[0]]),np.array([point[1]]))
 return float(back.stream[iz,ix][0]-back.floor[iz,ix][0])>.05
for p_ in [profile['outlet']['point']]+[h['point'] for h in profile['heads'] if has_stream(h['point'])]:
 assert (np.hypot(sp[:,0]-p_[0],sp[:,2]-p_[1])<15).any(),(p_,'stream does not reach it')
pudding_core=unary_union([channels[k] for g in tl.back_rivers['groups'] if g['streamDepthMetres']==0 for k in g['channelIds']]).difference(
 unary_union([channels[k] for g in tl.back_rivers['groups'] if g['streamDepthMetres']>0 for k in g['channelIds']]).buffer(25))
assert not contains_xy(pudding_core,sp[:,0],sp[:,2]).any(),'stream in the Pudding Mill River'
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
print('Tide checks passed: OS levels; silted back-river beds at the register and their low-water stream; exposed shelves on five reaches and the OS mud flats; moving water covers tidal channels, shelves and flats, stops at Abbey Mill, excludes Old Lea, marsh and drains, and stays below retaining crests.')
