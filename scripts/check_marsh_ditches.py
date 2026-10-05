"""Check mapped ditch coverage, bank protection and rendered relative levels."""
import json
from pathlib import Path
import numpy as np
from shapely import contains_xy
from shapely.geometry import Polygon,LineString
from shapely.ops import unary_union
from marsh_ditches import geometry

ROOT=Path(__file__).resolve().parents[1]
load=lambda p:json.loads((ROOT/p).read_text())
raw,marsh,ditches,parts,protected=geometry()
meta=load('docs/data/river-network.json');core=load('docs/data/river-terrain.json')
assert len(meta['marshDitches']['features'])==len(raw['features'])==13
assert ditches.intersection(protected).area<.001
for f,p in zip(raw['features'],parts):
 original=LineString(f['route']).buffer(f['width']/2,cap_style=2,join_style=2)
 assert p.is_valid and p.area/original.area>.95,(f['id'],'lost mapped coverage')
positions=np.fromfile(ROOT/'docs/data/river-network.f32',dtype='<f4').reshape(-1,3)
x0,z0,x1,z1=core['bounds'];step=core['step']
X,Z=np.meshgrid(np.linspace(x0,x1,core['width']),np.linspace(z0,z1,core['height']))
H=np.fromfile(ROOT/'docs/data'/core['heightFile'],dtype='<f4').reshape(X.shape)
all_points=np.vstack([positions,np.column_stack([X.ravel(),H.ravel(),Z.ravel()])])
x,y,z=all_points.T
interior=contains_xy(ditches.buffer(-1.2),x,z)
assert interior.sum()>1000
assert np.percentile(y[interior],95)<core['waterLevel'],'Ditches painted on uncut ground'
dry=marsh.buffer(-5).difference(ditches.buffer(5))
mask=contains_xy(dry,x,z)
assert mask.sum()>10000
assert core['waterLevel']<np.median(y[mask])<meta['tide']['high']
assert np.percentile(y[mask],99)<meta['tide']['high']
assert meta['retainingEdges']['crestHeight']>meta['tide']['high']
# A mapped gap across a footpath must survive rather than become an invented outlet.
a=parts[4];b=parts[5]
assert a.distance(b)>2,'Central footpath interruption filled in'
for bed in load('docs/data/ground-plan.json')['neighbourhood']['garden']['beds']:
 from shapely.geometry import box
 footprint=Polygon(bed['footprint']) if 'footprint' in bed else box(bed['x']-bed['width']/2,bed['z']-bed['depth']/2,bed['x']+bed['width']/2,bed['z']+bed['depth']/2)
 assert footprint.intersection(ditches).area<.001,'Allotment over mapped ditch'
length=sum(LineString(f['route']).length for f in raw['features'])
print(f'Marsh checks passed: 13 mapped reaches ({length:.0f} m), cut beds, lower marsh, protected river banks, clear allotments and retained path gaps.')
