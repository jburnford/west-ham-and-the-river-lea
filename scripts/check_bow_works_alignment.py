"""Verify Bow Bridge source matches, direct traces, chimney bases and bank clearance."""
import json
import math
from pathlib import Path
from shapely import affinity
from shapely.geometry import Polygon,Point,LineString,box
from shapely.ops import unary_union

ROOT=Path(__file__).resolve().parents[1]
load=lambda p:json.loads((ROOT/p).read_text())
r=load('data/maps/bow-works-footprint-alignment.json');s=load('docs/data/factory-buildings.json')
models={b['id']:b for b in s['buildings']};cs={c['modelId']:c for c in r['buildings']};direct={c['modelId']:c for c in r['mapTracedBuildings']}
assert len(cs)==10 and len(r['groups'])==7 and len(direct)==5 and len(r['additionalBuildings'])==2
assert set(cs)|set(direct)|{'site254-range-14','site254-range-15'}=={b['id'] for b in s['buildings'] if b['siteId']==254}
assert {b['id'] for b in r['additionalBuildings']}=={'site254-charcoal-500','site254-mill-annex-508'}
assert set(r['supersedesLocalTransfers'])=={'site254-range-12','site254-range-13'}
assert s['footprintAlignment']['directMapTraces']==11 and s['footprintAlignment']['locallyTransferredRanges']==2
registers=[load('data/maps/factory-footprint-alignment.json')]+[load(p) for p in s['footprintAlignment']['groupRegisters']]
assert sum(len(q['buildings']) for q in registers)==s['footprintAlignment']['matchedRanges']
used=set()
for q in registers:
 if q==r:continue
 for g in q.get('groups',q['buildings']):used.update(g.get('sourceFids',[g.get('sourceFid')]))
results=[]
for g in r['groups']:
 assert not used.intersection(g['sourceFids']),g['id'];used.update(g['sourceFids'])
 source=unary_union([Polygon(p[0],p[1:]) for p in g['sourcePolygons']])
 parts=[Polygon(cs[id]['worldFootprint'],cs[id]['worldHoles']) for id in g['modelIds']]
 target=unary_union(parts)
 actual=unary_union([Polygon(p['outer'],p['holes']) for id in g['modelIds'] for p in models[id]['renderPolygons']])
 assert target.symmetric_difference(source).area<.1,g['id']
 assert sum(p.area for p in parts)-target.area<.01,g['id']
 assert actual.symmetric_difference(target).area<.01,g['id']
 score=actual.intersection(source).area/actual.union(source).area
 assert score>.9995,g['id']
 assert set(g['modelIds'])<={b['id'] for b in r['additionalBuildings']} or score>g['previousUnionIoU']
 for id in g['modelIds']:
  b,c=models[id],cs[id]
  assert b['sourceFootprintFids']==g['sourceFids'] and b['footprintGroup']==g['id']
  assert abs(b['rotation']-c['footprintRotationDegrees'])<.0001
  for key,saved in [('height','preservedHeight'),('roofRise','preservedRoofRise'),('roofAxis','preservedRoofAxis'),('roofBays','preservedRoofBays')]:assert b[key]==c[saved]
 results.append(dict(id=g['id'],previousIoU=g['previousUnionIoU'],renderedIoU=score))
trace=unary_union([Polygon(p[0],p[1:]) for p in r['directTrace']['sourcePolygons']])
parts=[]
for id,c in direct.items():
 b=models[id];p=Polygon(b['footprint'],b['worldHoles']);parts.append(p)
 assert b['footprintSource']=='os-1893-direct-trace' and 'sourceFootprintFids' not in b
 assert p.hausdorff_distance(Polygon(c['worldFootprint'],c['worldHoles']))<.001
 rendered=unary_union([Polygon(q['outer'],q['holes']) for q in b['renderPolygons']])
 assert p.symmetric_difference(rendered).area<.01,id
 for key,saved in [('height','eavesHeight'),('roofRise','roofRise'),('roofAxis','roofAxis'),('roofBays','roofBays')]:assert b[key]==c[saved]
 assert abs(b['rotation']-c['footprintRotationDegrees'])<.0001
assert unary_union(parts).symmetric_difference(trace).area<.12
assert sum(p.area for p in parts)-unary_union(parts).area<.01
plan=load('docs/data/ground-plan.json')
water=unary_union([Polygon(p[0],p[1:]) for river in plan['rivers']+s['westContext']['rivers'] for p in river['polygons']])
roads=unary_union([LineString(q['points']).buffer(q['width']/2+1.1,cap_style=2,join_style=2) for q in load('data/maps/district-road-traces.json')['roads']])
for b in models.values():
 if b['siteId']==254:
  p=Polygon(b['footprint'],b.get('worldHoles',[]))
  assert p.intersection(water.buffer(.12)).area<.01,(b['id'],'water')
  assert p.intersection(roads).area<.01,(b['id'],'road')
volumes=unary_union([Polygon(p['outer'],p['holes']) for b in models.values() for p in b['renderPolygons']])
stacks=[p for p in s['structures'] if p['siteId']==254];assert len(stacks)==5
assert sorted(p['mappedHeightFeet'] for p in stacks if 'mappedHeightFeet' in p)==[50,50,60,100]
for p in stacks:
 c=next(c for c in r['structures'] if c['id']==p['id'])
 assert p['height']==c['preservedHeight']
 assert Point(p['x'],p['z']).distance(Point(c['centre']))<.001
 if 'sourceFootprintFid' in p:
  base=unary_union([Polygon(q[0],q[1:]) for q in p['sourcePolygons']]);h=p['radius']*1.2/math.sqrt(2)
  plinth=affinity.translate(affinity.rotate(box(-h,-h,h,h),p['rotation']),p['x'],p['z'])
  assert plinth.difference(base).area<.001,p['id']
  assert plinth.intersection(volumes).area<.001,p['id']
 else:
  group=next(g for g in r['groups'] if g['id']==c['transferGroup'])
  body=unary_union([Polygon(q[0],q[1:]) for q in group['sourcePolygons']])
  assert body.contains(Point(p['x'],p['z'])) and p['height']==22
bank=load('data/maps/bow-works-bank-alignment.json');river=next(q for q in plan['rivers'] if q['id']==18)
ring=river['polygons'][0][0];baseline=[list(p) for p in ring]
assert len(bank['replacements'])==10
hunt_bank={c['vertex']:c for c in load('data/maps/hunt-works-bank-alignment.json')['replacements']}
for c in bank['replacements']:
 # Hunt's adjoining furnace review further reconciles the shared vertex 39.
 expected=hunt_bank.get(c['vertex'],c)['point']
 assert ring[c['vertex']]==expected;baseline[c['vertex']]=c['priorPoint']
 assert math.dist(c['priorPoint'],c['point'])<=5.3+.0001
old,new=Polygon(baseline),Polygon(ring);assert old.is_valid and new.is_valid
assert new.difference(old).area<.001 and new.area<old.area
assert min(LineString(ring[30:40]).distance(LineString(ring[a:b])) for a,b in [(6,18),(133,140)])>6,'Local Lea channel pinched shut'
# Corrected source volumes would be crossed by the former bank.
assert sum(Polygon(models[id]['footprint']).intersection(old).area for id in cs)>60
c=r['locallyTransferredBuildings'][0];b=models[c['modelId']]
assert c['modelId']=='site564-range-1' and c['localOffsetMetres']==[0,2]
assert b['footprintSource']=='author-os-footprints-1891-96' and b['sourceFootprintFids']==[1461,938428]
assert 'site564-range-1' in load('data/maps/hunt-works-footprint-alignment.json')['supersedesLocalTransfers']
for id in set(cs)|set(direct):assert Polygon(b['footprint']).intersection(Polygon(models[id]['footprint'])).area<.01
(ROOT/'reference/footprint-model-alignment/verified-bow-works.json').write_text(json.dumps(results,indent=2)+'\n')
print(f'Bow works: 10 new supplied-outline ranges, five direct OS traces, two additions, four mapped chimney bases and one transferred stack; clear roads and reconciled Lea bank. Minimum supplied-outline agreement {min(x["renderedIoU"] for x in results):.3%}.')
