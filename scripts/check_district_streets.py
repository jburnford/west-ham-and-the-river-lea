"""Check period bridge families, district road continuity, and factory clearance."""
import json
from pathlib import Path
from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union
ROOT=Path(__file__).resolve().parents[1]
load=lambda p:json.loads((ROOT/p).read_text())
data=load('docs/data/infrastructure.json');factories=load('docs/data/factory-buildings.json')
roads=unary_union([Polygon(t) for t in data['roadTriangles']])
bridges={b['id']:b for b in data['roadBridges']}
expected={'bow-bridge':('stone-arch',1),'pegshole-bridge':('stone-arch',2),'st-thomas-bridge':('brick-arch',1),'st-michaels-bridge':('stone-arch',1),'channelsea-high-street-bridge':('stone-arch',1)}
for key,(style,count) in expected.items():
 b=bridges[key];assert b['style']==style and b['archCount']==count
 assert b['height']>1 and LineString(b['route']).length>5
assert sum(b.get('provisional',False) for b in bridges.values())==3
for b in factories['buildings']:
 for p in b['renderPolygons']:
  overlap=Polygon(p['outer'],p['holes']).intersection(roads).area
  assert overlap<.15,(b['id'],overlap)
covered=roads.union(unary_union([LineString(b['route']).buffer(b['width']/2+1.1,cap_style=2) for b in bridges.values()])).buffer(.03)
report={}
for r in data['roads']:
 if r['sheet']!='scene':continue
 missing=LineString(r['route']).difference(covered)
 report[r['name']]={'lengthM':round(LineString(r['route']).length,1),'uncoveredCentrelineM':round(missing.length,2)}
 # The north approach has a short unresolved GIS-bank discrepancy outside
 # the explicit Channelsea span. Do not invent an extra historical bridge.
 tolerance=5 if r['name']=='Stratford High Street — Channelsea approach' else 1
 assert missing.length<tolerance,(r['name'],missing.length)
assert report['Three Mills Lane']['uncoveredCentrelineM']<1
authored=load('data/maps/road-traces.json')['roads']
district=load('data/maps/district-road-traces.json')['roads']
housing=load('data/maps/housing-road-traces.json')
replaced={r['name'] for r in district}|set(housing['replaceNames'])
expected_routes=[r for r in authored if r['name'] not in replaced]+district+housing['roads']
housing_review=load('data/maps/district-housing-review.json')
review=housing_review['roads']
names={r['name'] for r in review}|set(housing_review.get('removeRoadNames',[]))
expected_routes=[r for r in expected_routes if r['name'] not in names]+review
assert [r['name'] for r in data['roads']]==[r['name'] for r in expected_routes]
report['limitations']=['Short Channelsea north-approach bank discrepancy remains within the measured 5 m bound.','Three short lane connections are provisional GIS-bank reconciliations, not independently documented bridge designs.']
out=ROOT/'reference/district-streets/geometry-checks.json';out.write_text(json.dumps(report,indent=2)+'\n')
print(f"District streets passed: {len(data['roads'])} routes, five documented High Street bridge families, factory clearance and a continuous western Three Mills approach. Channelsea bank discrepancy recorded separately.")
