"""Check reviewed High Street compounds, shared rooms and the neighbouring boundary."""
import json
import math
from pathlib import Path
from shapely import affinity
from shapely.geometry import Polygon,Point,LineString,box
from shapely.ops import unary_union

ROOT=Path(__file__).resolve().parents[1]
load=lambda p:json.loads((ROOT/p).read_text())
r=load('data/maps/abbey-west-footprint-alignment.json');s=load('docs/data/factory-buildings.json')
models={b['id']:b for b in s['buildings']};corrections={c['modelId']:c for c in r['buildings']}
assert len(corrections)==18 and len(r['groups'])==15 and len(r['additionalBuildings'])==4
assert {b['id'] for b in r['removedBuildings']}=={'site256-range-4'}
assert 'site256-range-4' not in models
for site,count in [(256,5),(572,3),(573,8)]:
 ids={b['id'] for b in s['buildings'] if b['siteId']==site}
 assert len(ids)==count and ids<=set(corrections)
registers=[load('data/maps/factory-footprint-alignment.json')]+[load(p) for p in s['footprintAlignment']['groupRegisters']]
assert sum(len(q['buildings']) for q in registers)==s['footprintAlignment']['matchedRanges']
used=set()
for q in registers:
 if q==r:continue
 for g in q.get('groups',q['buildings']):used.update(g.get('sourceFids',[g.get('sourceFid')]))
water=unary_union([Polygon(p[0],p[1:]) for river in load('docs/data/ground-plan.json')['rivers']+s['westContext']['rivers'] for p in river['polygons']])
roads=unary_union([LineString(q['points']).buffer(q['width']/2+1.1,cap_style=2,join_style=2) for q in load('data/maps/district-road-traces.json')['roads']])
results=[]
for group in r['groups']:
 assert not used.intersection(group['sourceFids']),group['id']
 used.update(group['sourceFids'])
 source=unary_union([Polygon(p[0],p[1:]) for p in group['sourcePolygons']])
 target=unary_union([Polygon(corrections[id]['worldFootprint'],corrections[id]['worldHoles']) for id in group['modelIds']])
 actual=unary_union([Polygon(p['outer'],p['holes']) for id in group['modelIds'] for p in models[id]['renderPolygons']])
 assert target.symmetric_difference(source).area<.1,group['id']
 street=source.intersection(roads).area
 if group['id']==r['roadBoundaryReview']['groupId']:
  assert abs(street-r['roadBoundaryReview']['sourceOverlapAreaM2'])<.001
 else:assert street<.01,group['id']
 assert actual.symmetric_difference(target.difference(roads)).area<.04,group['id']
 assert actual.intersection(water.buffer(.12)).area<.01,group['id']
 assert actual.intersection(roads).area<.01,group['id']
 agreement=source.intersection(actual).area/source.union(actual).area
 assert agreement>.999 and (set(group['modelIds'])<={a['id'] for a in r['additionalBuildings']} or agreement>group['previousUnionIoU'])
 for id in group['modelIds']:
  b=models[id];c=corrections[id]
  assert b['sourceFootprintFids']==group['sourceFids'] and b['footprintGroup']==group['id']
  for key,saved in [('height','preservedHeight'),('roofRise','preservedRoofRise'),('roofBays','preservedRoofBays'),('roofAxis','preservedRoofAxis')]:assert b[key]==c[saved],(id,key)
  assert abs(b['rotation']-c['footprintRotationDegrees'])<.0001
  assert b['heightEvidence'] and b['roofEvidence']
 results.append(dict(id=group['id'],previousIoU=group['previousUnionIoU'],renderedIoU=agreement))
# Shared source footprints retain three starch and two pickle compartments.
assert [len(g['modelIds']) for g in r['groups'][:2]]==[3,2]
for g in r['groups'][:2]:
 parts=[Polygon(corrections[id]['worldFootprint']) for id in g['modelIds']]
 assert sum(p.area for p in parts)-unary_union(parts).area<.01
stack=next(t for t in s['structures'] if t['id']=='stack-573-487-2965');c=r['structures'][0]
assert stack['height']==22 and stack['radius']==1.05 and stack['sourceFootprintFid']==993523
assert Point(stack['x'],stack['z']).distance(Point(c['centre']))<.001
base=unary_union([Polygon(p[0],p[1:]) for p in c['sourcePolygons']])
half=stack['radius']*1.2/math.sqrt(2)
plinth=affinity.translate(affinity.rotate(box(-half,-half,half,half),stack['rotation']),stack['x'],stack['z'])
assert plinth.difference(base).area<.001
volumes=unary_union([Polygon(p['outer'],p['holes']) for b in s['buildings'] for p in b['renderPolygons']])
assert plinth.intersection(volumes).area<.001
continuation=load('data/maps/bow-works-footprint-alignment.json')
assert set(continuation['supersedesLocalTransfers'])=={c['modelId'] for c in r['locallyTransferredBuildings']}
continued={c['modelId'] for c in continuation['buildings']+continuation['mapTracedBuildings']}
for c in r['locallyTransferredBuildings']:
 b=models[c['modelId']]
 assert c['modelId'] not in corrections and c['modelId'] in continued
 for key,saved in [('height','eavesHeight'),('roofRise','roofRise'),('roofBays','roofBays'),('roofAxis','roofAxis')]:assert b[key]==c[saved]
 for id in corrections:
  assert Polygon(b['footprint']).intersection(Polygon(models[id]['footprint'])).area<.01,(b['id'],id)
(ROOT/'reference/footprint-model-alignment/verified-abbey-west.json').write_text(json.dumps(results,indent=2)+'\n')
print(f'High Street compounds: 18 aligned ranges in 15 groups, four additions, one domestic reclassification and mapped Hogarth chimney; neighbour transfers superseded by the Bow works review. Minimum rendered agreement {min(q["renderedIoU"] for q in results):.3%}.')
