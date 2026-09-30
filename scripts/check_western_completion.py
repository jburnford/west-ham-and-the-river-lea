"""Check the new railway joins and the added west-bank industrial geometry."""
import json, math
from pathlib import Path
from shapely.geometry import Polygon, Point, LineString
from shapely.ops import unary_union
from district_housing import rectangle

ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text())
infra=read('docs/data/infrastructure.json');factories=read('docs/data/factory-buildings.json')
survey=read('data/maps/west-bank-industry.json');houses=read('docs/data/housing-detail.json')['rows']
extension=next(r for r in infra['railways'] if r.get('id')=='woolwich-northern-connection')
main=next(r for r in infra['railways'] if r.get('detailedMainline'))
branch=next(r for r in infra['railways'] if r['name']=='Great Eastern Railway, Woolwich branch')
assert math.dist(extension['route'][-1],branch['route'][0])<.001,'Gap at old branch endpoint'
assert abs(extension['stations'][-1][2]-branch['formationHeight'])<.001,'Vertical step at branch'
line=LineString(main['route']);s=extension['mainlineJoinChainage']
p=line.interpolate(s);a=line.interpolate(s-.5);b=line.interpolate(s+.5)
dx,dz=b.x-a.x,b.y-a.y;length=math.hypot(dx,dz);normal=(-dz/length,dx/length)
start=extension['stations'][0]
for offset,main_offset in [(-1.8,1.8),(1.8,5.4)]:
    actual=[start[0]+start[3]*offset,start[1]+start[4]*offset]
    expected=[p.x+normal[0]*main_offset,p.y+normal[1]*main_offset]
    assert math.dist(actual,expected)<.08,('Tracks do not meet the main-line pair',actual,expected)
assert abs(start[2]-main['formationHeight'])<.001
grades=[abs(b[2]-a[2])/(b[5]-a[5]) for a,b in zip(extension['stations'],extension['stations'][1:])]
assert max(grades)<.015,'Abrupt branch grade'
roads=unary_union([LineString(r['route']).buffer(r['width']/2) for r in infra['roads']])
water=unary_union([Polygon(p[0],p[1:]) for r in read('docs/data/ground-plan.json')['rivers']+factories['westContext']['rivers'] for p in r['polygons']])
water=water.union(unary_union([Polygon(p[0],p[1:]) for p in main['northernWater']]))
factory_polys={b['id']:unary_union([Polygon(p['outer'],p['holes']) for p in b['renderPolygons']]) for b in factories['buildings']}
homes=unary_union([rectangle(r) for r in houses])
formation=LineString(extension['route']).buffer(extension['crestHalfWidth'],cap_style=2)
assert formation.intersection(homes).area<.01,'Railway through houses'
assert formation.intersection(unary_union(list(factory_polys.values()))).area<.01,'Railway through factories'
earth=unary_union([Polygon([(p[0],p[2]) for p in tri]) for tri in extension['embankment']])
assert earth.intersection(roads.union(water)).area<.01,'Earth fills a bridge opening'
new_ids={s['id'] for s in survey['sites']}
assert not new_ids.intersection({s['id'] for s in factories['excludedSites']})
reclassified={b['id']:b for b in factories.get('reclassifiedFeatures',[]) if 'id' in b}
retained_western=0
for b in survey['buildings']:
    if b['id'] in reclassified:
        assert b['id'] not in factory_polys,('Reclassified western feature still rendered',b['id'])
        continue
    g=factory_polys[b['id']]
    assert not g.is_empty,('Unrendered western building',b['id'])
    assert g.intersection(homes.union(roads).union(water)).area<.1,('Western building obstruction',b['id'])
    retained_western+=1
print(f"Western completion passed: {extension['length']:.1f} m connected railway, matching track pairs and levels, maximum grade {max(grades)*100:.2f}%; {len(new_ids)} sites / {retained_western} clear western ranges.")
