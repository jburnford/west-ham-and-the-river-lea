"""Independent collision, evidence-accounting and bank-path checks for the vista."""
import json,math
from pathlib import Path
from shapely.geometry import Polygon,LineString,Point,box
from shapely.ops import unary_union
from shapely import affinity
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_text())
def shapes(b):return unary_union([Polygon(p['outer'],p['holes']) for p in b['renderPolygons']])
def rectangle(b):return affinity.translate(affinity.rotate(box(-b['width']/2,-b['depth']/2,b['width']/2,b['depth']/2),-b['rotation']),b['x'],b['z'])
authored=load('data/maps/high-street-frontages.json');data=load('docs/data/high-street-frontages.json');ground=load('docs/data/ground-plan.json');factories=load('docs/data/factory-buildings.json');infra=load('docs/data/infrastructure.json')
assert {b['id'] for b in data['buildings']}|{b['id'] for b in data['omitted']}=={b['id'] for b in authored['ranges']}
# 34 since T17 (3 Oct 2026): the published file was last built at ed15f11, when factory range site789-os-3 covered
# high-street-06 and the builder omitted it. That factory range has since been re-registered off it, so the rebuild
# retains all 34 source ranges; the T17 re-registration of high-street-01..05, -09 and -30 does not change the count.
assert len(data['buildings'])==34
water=unary_union([Polygon(p[0],p[1:]) for r in ground['rivers']+factories['westContext']['rivers'] for p in r['polygons']])
existing=unary_union([shapes(b) for b in factories['buildings']]+[rectangle(b) for b in ground['neighbourhood']['terraces']+ground['neighbourhood']['houses']])
roads=unary_union([Polygon(t) for t in infra['roadTriangles']+infra['pathTriangles']])
polys=[]
for b in data['buildings']:
 p=shapes(b);assert p.is_valid and p.area>8,b['id']
 for label,mask in [('water',water),('existing ranges',existing),('roads',roads),('new ranges',unary_union(polys))]:assert p.intersection(mask).area<.01,(b['id'],label)
 polys.append(p)
b=data['vista']['bank'];s=b['samples'];w=b['pathWidth']/2;o=b['pathLandOffset']
path=unary_union([Polygon([[x+o-w,z],[nx+o-w,nz],[nx+o+w,nz],[x+o+w,z]]) for (x,z),(nx,nz) in zip(s,s[1:])])
assert path.intersection(water).area<.01
assert path.intersection(existing.union(unary_union(polys))).area<.01,'Path through a building'
assert all(math.isfinite(v) for p in s for v in p)
connections={c['id']:c for c in data['vista']['connections']}
for c in connections.values():
 sections=c['sections']
 ribbon=unary_union([Polygon([(v[0],v[2]) for v in [a[0],a[1],b[1],b[0]]]) for a,b in zip(sections,sections[1:])])
 assert ribbon.intersection(water).area<.01,(c['id'],'water')
 assert ribbon.intersection(existing.union(unary_union(polys))).area<.01,(c['id'],'building')
 assert all(abs(b[1]-a[1])/math.hypot(b[0]-a[0],b[2]-a[2])<.15 for a,b in zip(c['route'],c['route'][1:])),(c['id'],'steep ramp')
assert connections['high-street-access']['route'][-1]==[s[0][0]+o,b['crestHeight'],s[0][1]]
assert connections['wall-lane-north']['route'][0]==[s[-1][0]+o,b['crestHeight'],s[-1][1]]
lane=next(r for r in infra['roads'] if r['name']=='Three Mills Wall lane')
for cid,index,target in [('wall-lane-north',-1,lane['route'][0]),('wall-lane-south',0,lane['route'][-1])]:
 p=connections[cid]['route'][index];assert math.dist([p[0],p[2]],target)<.001
for cid,index in [('high-street-access',0),('wall-lane-south',-1)]:
 p=connections[cid]['route'][index];assert min(LineString(r['route']).distance(Point(p[0],p[2])) for r in infra['roads'])<.5
print('Three path connections join their intended endpoints with clear water/buildings and slopes below 15%.')
print(f'High Street/vista checks passed: {len(polys)} added ranges, all source records accounted for, clear roads/water/buildings and an unobstructed {b["zEnd"]-b["zStart"]} m photo-study path.')
