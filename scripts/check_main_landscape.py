"""Check source freshness, water beds and the main scene's marsh geometry."""
import hashlib
import json
from pathlib import Path
import numpy as np
import shapely
from shapely.geometry import Polygon
from scipy.ndimage import map_coordinates
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'docs/data'
def read(name):return json.loads((D/name).read_text())
def rings(parts):return shapely.union_all([Polygon(p[0],p[1:]) for p in parts])
def f32(name):return np.fromfile(D/name,'<f4')
m=read('main-landscape-1900.json');h=read('terrain-1900.json');system=read('river-system-1900.json');net=read('river-network.json');plan=read('ground-plan.json')
for path,digest in m['inputHashes'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,path
assert len(set(m['files'].values()))==len(m['files']),'Asset names must not collide'
water=shapely.union_all([rings(system['waterPolygons']),rings([p for r in plan['rivers'] for p in r['polygons']]),rings([p for f in net['marshDitches']['features'] for p in f['renderPolygons']])])
shapely.prepare(water)
checks={}
for key,source in [('network',net),('system',system)]:
 p=f32(source['positionFile']).reshape(-1,3);before=p[:,1].copy();after=f32(m['files'][key]);wet=shapely.contains_xy(water,p[:,0],p[:,2])
 if key=='network':
  rc=np.array([(p[:,2]-h['bounds'][1])/h['step'],(p[:,0]-h['bounds'][0])/h['step']])
  w=map_coordinates(f32(h['files']['weight']).reshape(h['height'],h['width']),rc,order=1,mode='constant',cval=0)
  target=map_coordinates(f32(h['files']['target']).reshape(h['height'],h['width']),rc,order=1,mode='nearest')
  before+=w*(target-before);idx=np.array(system['coreBedCorrections']);before[idx]=np.minimum(-.7,before[idx])
 assert np.max(abs(after[wet]-before[wet]))<2e-6,f'{key}: water bed changed'
 checks[key+'WaterVerticesPreserved']=int(wet.sum())
mesh=f32(m['files']['groundMesh']).reshape(-1,3,3)
centres=mesh.mean(axis=1);assert not shapely.contains_xy(water,centres[:,0],centres[:,2]).any(),'New ground blocks a waterway'
a=mesh[:,1,[0,2]]-mesh[:,0,[0,2]];b=mesh[:,2,[0,2]]-mesh[:,0,[0,2]]
assert (a[:,0]*b[:,1]-a[:,1]*b[:,0]<=1e-4).all(),'Ground triangles face downward'
# Independently interpolate the actual background triangles at the two marsh
# comparison points; these points lie between the narrow native river meshes.
triangles=shapely.polygons(mesh[:,:,[0,2]])
tree=shapely.STRtree(triangles)
for probe in m['probes'][:2]:
    point=np.array(probe['scenePosition']);candidates=tree.query(shapely.Point(point),predicate='intersects')
    assert len(candidates),probe['name']+' has no rendered ground'
    for i in candidates:
        triangle=mesh[i];xz=triangle[:,[0,2]]
        weights=np.linalg.solve(np.vstack([xz.T,np.ones(3)]),[*point,1])
        rendered_y=float(weights@triangle[:,1])
        assert abs(rendered_y-probe['groundSceneY'])<.03,(probe['name'],rendered_y)
checks.update(status='PASS',backgroundTriangles=len(mesh),streetControls=len(m['roadControlIds']),sourceHashes=len(m['inputHashes']))
print(json.dumps(checks,indent=2))
