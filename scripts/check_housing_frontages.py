"""Audit every rendered housing range against parallel, rendered street frontage."""
import json, math
from pathlib import Path
from shapely import affinity
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import unary_union, nearest_points
ROOT=Path(__file__).resolve().parents[1]
load=lambda p:json.loads((ROOT/p).read_text())
ground=load('docs/data/ground-plan.json');sw=load('docs/data/southwest-context.json');infra=load('docs/data/infrastructure.json')
houses=load('docs/data/housing-detail.json')['rows']+ground['neighbourhood']['houses']
def rectangle(b):
 return affinity.translate(affinity.rotate(box(-b['width']/2,-b['depth']/2,b['width']/2,b['depth']/2),-b['rotation']),b['x'],b['z'])
polys={b['id']:rectangle(b) for b in houses}
items=list(polys.items())
for i,(key,polygon) in enumerate(items):
 for other,other_polygon in items[i+1:]:
  assert polygon.intersection(other_polygon).area<2,(key,other,'overlapping housing')
obstacles=unary_union(list(polys.values()))
rendered=unary_union([Polygon(t) for t in infra['roadTriangles']+infra['pathTriangles']]).buffer(.1)
roads=[(r['name'],LineString(r['route']),r['width']) for r in infra['roads']]
report=[]
for b in houses:
 poly=polys[b['id']];theta=math.radians(-b['rotation']);u=(math.cos(theta),math.sin(theta))
 samples=[Point(b['x']+u[0]*t*b['width'],b['z']+u[1]*t*b['width']) for t in [-.4,-.3,-.2,-.1,0,.1,.2,.3,.4]]
 candidates=[]
 for name,line,width in roads:
  overlap=line.intersection(poly).length
  assert overlap<.15,(b['id'],name,'road through housing',overlap)
  segments=[LineString([a,z]) for a,z in zip(line.coords,list(line.coords)[1:]) if abs(sum((z[i]-a[i])*u[i] for i in [0,1])/math.dist(a,z))>.8]
  if not segments:continue
  parallel=unary_union(segments);gaps=[];accessible=[]
  for sample in samples:
   target=nearest_points(sample,parallel)[1];gap=max(0,sample.distance(target)-width/2-b['depth']/2)
   approach=LineString([sample,target]).difference(poly.buffer(.15))
   gaps.append(gap)
   accessible.append(gap<=16 and rendered.distance(target)<.5 and approach.intersection(obstacles).length<.2)
  candidates.append({'street':name,'coverage':sum(accessible)/9,'meanGapM':sum(gaps)/9,'maxGapM':max(gaps)})
 best=min(candidates,key=lambda c:(-c['coverage'],c['meanGapM']))
 report.append({'id':b['id'],'sourceRowId':b.get('sourceRowId',b['id']),**{k:round(v,3) if isinstance(v,float) else v for k,v in best.items()}})
failures=[r for r in report if r['coverage']<7/9 or r['maxGapM']>22]
out=ROOT/'reference/housing-street-audit';out.mkdir(parents=True,exist_ok=True)
(out/'frontage-checks.json').write_text(json.dumps({'rows':report,'failures':failures,'limits':'16 m frontage reach and 22 m maximum gap allow front gardens and approximate envelopes; this is a geometric access check, not proof of historical access rights.'},indent=2)+'\n')
assert not failures,json.dumps(failures,indent=2)
print(f'Housing frontage check passed: {len(houses)} rendered ranges, no roads through houses, parallel street access along at least 7/9 sampled frontage points per range.')
