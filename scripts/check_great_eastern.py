"""Geometric clearance and continuity checks for the northern main line."""
import json,math
from pathlib import Path
from shapely.geometry import Polygon,LineString,Point
from shapely.ops import unary_union

ROOT=Path(__file__).resolve().parents[1]
def read(path):return json.loads((ROOT/path).read_text())
def polygons(rows):return unary_union([Polygon(p[0],p[1:]) for p in rows])
infra=read('docs/data/infrastructure.json');plan=read('docs/data/ground-plan.json')
factories=read('docs/data/factory-buildings.json')
rail=next(r for r in infra['railways'] if r.get('detailedMainline'))
line=LineString(rail['route']);foot=polygons(rail['footprint'])
water=unary_union([polygons(r['polygons']) for r in plan['rivers']+factories['westContext']['rivers']]+[polygons(rail['northernWater'])])
roads=unary_union([Polygon(t) for t in infra['roadTriangles']])
sewer=LineString(plan['neighbourhood']['sewer']['route']).buffer(plan['neighbourhood']['sewer']['baseWidth']/2)
buildings=unary_union([Polygon(p['outer'],p['holes']) for b in factories['buildings'] for p in b['renderPolygons']])
assert foot.is_valid
for name,blocked in [('water',water),('roads',roads),('sewer',sewer),('buildings',buildings)]:
    assert foot.intersection(blocked).area<.05, ('Embankment obstruction',name)
assert line.buffer(rail['crestHalfWidth']).intersection(buildings).area<1
for a,b in zip(rail['stations'],rail['stations'][1:]):
    length=math.dist(a[:2],b[:2]);assert 0<length<2.1
    assert abs(b[2]-a[2])/length<.025, 'Abrupt railway gradient'
    assert abs(math.hypot(a[3],a[4])-1)<1e-6
assert rail['length']>1500
assert rail['sewerCrossing']['minimumSoffit']-rail['sewerCrossing']['surfaceHeight']>3
assert sum(b['sewer'] for b in rail['bridges'])==1
assert rail['stations'][0][0]<-1450 and rail['stations'][-1][1]<-1200
assert rail['tracks']==4 and rail['gauge']==1.435
assert (rail['tracks']-1)*rail['trackSpacing']/2+1.3<rail['crestHalfWidth']
for triangle in rail['embankment']:
    assert all(math.isfinite(v) for p in triangle for v in p)
    assert all(-.1<=p[1]<=11.51 for p in triangle)
print(f"Great Eastern: {rail['length']} m continuous corridor; {len(rail['bridges'])} clear bridge gaps; no earth fill in mapped roads, rivers, sewer or factory buildings; sewer headroom >3 m.")
