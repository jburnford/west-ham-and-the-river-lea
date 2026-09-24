"""Register manually read tree symbols from the author's later OS screenshot."""
import json
from pathlib import Path
import numpy as np
from pyproj import Transformer
from shapely.geometry import Point, Polygon, LineString, box
from shapely.ops import unary_union

ROOT=Path(__file__).resolve().parents[1]
source=json.loads((ROOT/'data/maps/tree-traces.json').read_text())
s=json.loads((ROOT/'data/maps/os-neighbourhood-traces.json').read_text())['sheets']['32']
a=np.array([complex(*c['pixel']) for c in source['controls']])
b=np.array([complex(*c['target']) for c in source['controls']])
scale=np.sum(np.conjugate(a-a.mean())*(b-b.mean()))/np.sum(abs(a-a.mean())**2)
offset=b.mean()-scale*a.mean()
rms=float(np.sqrt(np.mean(abs(a*scale+offset-b)**2)))
assert rms<3, rms
project=Transformer.from_crs(4326,27700,always_xy=True).transform
def local(p):
    q=complex(*p)*scale+offset
    u,v=q.real*1888/1800,q.imag*1888/1800
    left,top,right,bottom=s['neatline'];west,south,east,north=s['bounds']
    e,n=project(west+(east-west)*(u-left)/(right-left),north-(north-south)*(v-top)/(bottom-top))
    return round(e-538900,3),round(183209-n,3)
data=json.loads((ROOT/'docs/data/ground-plan.json').read_text())
infra=json.loads((ROOT/'docs/data/infrastructure.json').read_text())
water=unary_union([Polygon(p[0],p[1:]) for r in data['rivers'] for p in r['polygons']])
roads=unary_union([LineString(r['route']).buffer(r['width']/2+.5) for r in infra['roads']])
station=box(-212,-23,-158,-3).union(box(-195,-37,-175,11))
trees=[]
for tree in source['trees']:
    x,z=local(tree['pixel']);p=Point(x,z)
    assert not water.covers(p), tree
    assert not roads.covers(p), tree
    assert not station.buffer(1).covers(p), tree
    trees.append({**tree,'x':x,'z':z})
result={'source':'data/maps/tree-traces.json','datePolicy':source['datePolicy'],
        'registration':{'scale':[scale.real,scale.imag],'offset':[offset.real,offset.imag],
                        'rmsTargetPixels':rms,'limits':'Internal fit only; inherited OS registration is approximate.'},'trees':trees}
(ROOT/'docs/data/mapped-trees.json').write_text(json.dumps(result,indent=2)+'\n')
print(f'{len(trees)} mapped tree symbols; fit RMS {rms:.2f} target pixels; water, road and station checks passed.')
