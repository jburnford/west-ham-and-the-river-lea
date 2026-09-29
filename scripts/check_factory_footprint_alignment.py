"""Verify actual rendered geometry against the registered source corrections."""
import json
import math
from pathlib import Path
from shapely import affinity
from shapely.geometry import Polygon,Point,box
from shapely.ops import unary_union
ROOT=Path(__file__).resolve().parents[1]
reg=json.loads((ROOT/'data/maps/factory-footprint-alignment.json').read_text())['buildings']
scene=json.loads((ROOT/'docs/data/factory-buildings.json').read_text());models={b['id']:b for b in scene['buildings']}
assert len({r['sourceFid'] for r in reg})==len(reg),'Ambiguous many-to-one match'
results=[]
for r in reg:
 b=models[r['modelId']];target=Polygon(r['worldFootprint']);original=Polygon(r['priorFootprint'])
 rendered=unary_union([Polygon(p['outer'],p['holes']) for p in b['renderPolygons']])
 before=target.intersection(original).area/target.union(original).area
 after=target.intersection(rendered).area/target.union(rendered).area
 assert target.is_valid and rendered.is_valid
 assert after>before and after>.85,(b['id'],before,after)
 assert Polygon(b['footprint']).symmetric_difference(target).area<.001,b['id']
 assert b['sourceFootprintFid']==r['sourceFid']
 assert math.isclose(b['height'],r['preservedHeight']) and math.isclose(b['roofRise'],r['preservedRoofRise'])
 assert b['roofBays']==r['preservedRoofBays'] and b['roofAxis']==r['preservedRoofAxis']
 results.append({'id':b['id'],'sourceFid':r['sourceFid'],'beforeIoU':before,'renderedIoU':after})
out=ROOT/'reference/footprint-model-alignment/verified-matches.json';out.write_text(json.dumps(results,indent=2)+'\n')
print(f'{len(results)} source-linked ranges: every rendered outline improves; height and roof interpretations preserved.')
print(f'Median rendered IoU: {sorted(r["renderedIoU"] for r in results)[len(results)//2]:.3f}; minimum {min(r["renderedIoU"] for r in results):.3f}.')

# Many-to-one matches are permitted only inside an explicitly reviewed group.
compound=json.loads((ROOT/'data/maps/ink-works-footprint-alignment.json').read_text())
corrections={r['modelId']:r for r in compound['buildings']}
assert len(corrections)==len(compound['buildings'])==13
assert not set(corrections).intersection(r['modelId'] for r in reg)
used_sources={r['sourceFid'] for r in reg}
used_models=set()
group_results=[]
for group in compound['groups']:
 assert not used_sources.intersection(group['sourceFids']),group['id']
 used_sources.update(group['sourceFids'])
 assert not used_models.intersection(group['modelIds']),group['id']
 used_models.update(group['modelIds'])
 source=unary_union([Polygon(r[0],r[1:]) for r in group['sourcePolygons']])
 originals=[];targets=[];rendered=[]
 for id in group['modelIds']:
  r=corrections[id];b=models[id]
  target=Polygon(r['worldFootprint'],r['worldHoles'])
  actual=unary_union([Polygon(p['outer'],p['holes']) for p in b['renderPolygons']])
  assert target.is_valid and actual.is_valid,id
  assert r['groupId']==group['id'] and b['footprintGroup']==group['id']
  assert b['sourceFootprintFids']==group['sourceFids']==r['sourceFids']
  assert Polygon(b['footprint'],b['worldHoles']).symmetric_difference(target).area<.001,id
  missing=target.difference(actual)
  allowed=Polygon()
  if 'boundaryOverlapReview' in group:
   neighbour=next(g for g in compound['groups'] if g['id']==group['boundaryOverlapReview']['neighbourGroup'])
   allowed=unary_union([Polygon(p[0],p[1:]) for p in neighbour['sourcePolygons']])
  assert actual.difference(target).area<.01 and missing.difference(allowed.buffer(.001)).area<.06,(id,'unreviewed compartment clipping')
  for key,saved in [('height','preservedHeight'),('roofRise','preservedRoofRise'),('roofBays','preservedRoofBays')]:
   assert math.isclose(b[key],r[saved]),(id,key)
  assert b['roofAxis']==r['preservedRoofAxis']
  assert b['floorMark'] and b['heightEvidence'] and b['roofEvidence']
  assert all(target.intersection(p).area<.01 for p in targets),(id,'overlapping compartments')
  originals.append(Polygon(r['priorFootprint']));targets.append(target);rendered.append(actual)
 target=unary_union(targets);actual=unary_union(rendered);original=unary_union(originals)
 assert target.symmetric_difference(source).area<.1,(group['id'],'missing boundary or hole')
 before=original.intersection(source).area/original.union(source).area
 after=actual.intersection(source).area/actual.union(source).area
 assert after>.998 and after>before,(group['id'],before,after)
 if 'boundaryOverlapReview' in group:
  assert math.isclose(source.intersection(allowed).area,group['boundaryOverlapReview']['sourceOverlapAreaM2'],abs_tol=.001)
 assert math.isclose(before,group['previousUnionIoU'],abs_tol=.0001)
 group_results.append({'id':group['id'],'beforeIoU':before,'renderedIoU':after})
assert used_models==set(corrections),'Orphan correction'
stacks={s['id']:s for s in scene['structures']}
for r in compound['structures']:
 s=stacks[r['id']];source=unary_union([Polygon(p[0],p[1:]) for p in r['sourcePolygons']])
 assert Point(s['x'],s['z']).distance(source.centroid)<.001,r['id']
 assert s['sourceFootprintFid']==r['sourceFid'] and s['height']==r['preservedHeight']
west=stacks['stack-940-1310-710']
chamber=models['site940-26']
holes=unary_union([Polygon(h) for p in chamber['renderPolygons'] for h in p['holes']])
assert holes.covers(Point(west['x'],west['z'])),'West chimney hole lost under roof'
half=west['radius']*1.2/math.sqrt(2)
base=affinity.translate(affinity.rotate(box(-half,-half,half,half),west['rotation']),west['x'],west['z'])
assert base.difference(holes).area<.001,'Rendered chimney plinth exceeds the mapped opening'
assert set(r['modelId'] for r in compound['deferred']).isdisjoint(corrections)
(ROOT/'reference/footprint-model-alignment/verified-ink-groups.json').write_text(json.dumps(group_results,indent=2)+'\n')
print(f'{len(corrections)} additional ranges in {len(group_results)} reviewed groups: minimum {min(r["renderedIoU"] for r in group_results):.3%} rendered source agreement, retained compartments/hole and 3 aligned chimney bases.')
