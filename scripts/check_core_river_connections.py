"""Verify core passage continuity, terrain clearance and lock/tidal separation."""
import hashlib
import json
from pathlib import Path
import numpy as np
from shapely import contains_xy
from shapely.geometry import Polygon, Point, LineString
from shapely.ops import unary_union
from core_river_connections import geometry

ROOT=Path(__file__).resolve().parents[1];D=ROOT/'docs/data'
load=lambda name:json.loads((D/name).read_text())
network=load('river-network.json');terrain=load('terrain-1900.json');flood=load('landscape-flood-1900.json')
data=network['reviewedConnections']
assert data==terrain['reviewedRiverConnections']==flood['reviewedRiverConnections']
assert data['reviewSha256']==hashlib.sha256((ROOT/data['sourceReview']).read_bytes()).hexdigest()
rivers=load('ground-plan.json')['rivers']+load('factory-buildings.json')['westContext']['rivers']
channels={}
for r in rivers:
 k=r['id']-10000 if 10000<=r['id']<10100 else r['id']
 channels[k]=channels.get(k,Polygon()).union(geometry(r['polygons']))
water=unary_union(list(channels.values()));tide=geometry(network['tide']['polygons'])
positions=np.fromfile(D/network['positionFile'],dtype='<f4').reshape(-1,3)
core=load('river-terrain.json');levels=np.fromfile(D/core['heightFile'],dtype='<f4').reshape(core['height'],core['width'])
xx,zz=np.meshgrid(core['bounds'][0]+np.arange(core['width'])*core['step'],core['bounds'][1]+np.arange(core['height'])*core['step'])
assert {'three-mills','pudding-mill','bow-locks','abbey-mill'} <= {r['id'] for r in data['connections']}
for r in data['connections']:
 patch=geometry(r['polygons']);assert patch.is_valid
 assert r['capacity'] is None and r['gateState'] is None
 a,b=r['channelIds']
 assert patch.intersection(channels[a]).area>0 and patch.intersection(channels[b]).area>0
 if r['id']=='three-mills':
  assert channels[1].distance(channels[2])<.02  # one shared mill group, not two parallel capacities
  assert sum(q['id']=='three-mills' for q in data['connections'])==1
 if r['category']=='lock-passage':
  assert tide.intersection(patch.difference(water)).area<1e-6
 else:
  # A retained bank at the open Navigation mouth can legitimately clip one end.
  assert tide.intersection(patch).area>0
 # Test interiors (away from polygon/raster rounding) in each terrain mesh.
 interior=patch.buffer(-.2)
 mask=contains_xy(interior,positions[:,0],positions[:,2])
 if mask.any():assert positions[mask,1].max()<network['waterLevel']
 mask=contains_xy(interior,xx,zz)
 if mask.any():assert levels[mask].max()<network['waterLevel']
assert sum(r['category']=='lock-passage' for r in data['connections'])==1
out=ROOT/'scenes/channelsea-sewer-panorama/review/core-river-connections-checks.json'
out.write_text(json.dumps({'status':'PASS','connections':[r['id'] for r in data['connections']],
 'checks':['shared terrain/render/flood connection data','both banks overlapped','mill group not duplicated','lock gap not a tidal seed','submerged passage beds in both meshes','capacities and gate states remain unassigned']},indent=2)+'\n')
print(f"Core river checks passed: {len(data['connections'])} reviewed passages/seams.")
