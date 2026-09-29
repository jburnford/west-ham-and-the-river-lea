"""Audit Howards outer plans, interpreted compartments, stacks and millrace."""
import copy
import json
import math
from pathlib import Path
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union

ROOT=Path(__file__).resolve().parents[1]
load=lambda p:json.loads((ROOT/p).read_text())
r=load('data/maps/howards-footprint-alignment.json');scene=load('docs/data/factory-buildings.json')
models={b['id']:b for b in scene['buildings']};corrections={b['modelId']:b for b in r['buildings']}
assert len(corrections)==83 and len(r['groups'])==53
accounted=[b['modelId'] for key in ['buildings','mapTracedBuildings','locallyTransferredBuildings','deferred'] for b in r[key]]
assert len(accounted)==len(set(accounted))==86
assert set(accounted)=={b['id'] for b in scene['buildings'] if b['siteId']==260}
assert scene['footprintAlignment']['matchedRanges']>=145
used=set();results=[]
for path in ['data/maps/factory-footprint-alignment.json',*scene['footprintAlignment']['groupRegisters']]:
    if path=='data/maps/howards-footprint-alignment.json':continue
    q=load(path)
    for g in q.get('groups',q['buildings']):used.update(g.get('sourceFids',[g.get('sourceFid')]))
for group in r['groups']:
    assert not used.intersection(group['sourceFids']),group['id']
    used.update(group['sourceFids'])
    source=unary_union([Polygon(p[0],p[1:]) for p in group['sourcePolygons']])
    target=unary_union([Polygon(corrections[id]['worldFootprint'],corrections[id]['worldHoles']) for id in group['modelIds']])
    actual=unary_union([Polygon(p['outer'],p['holes']) for id in group['modelIds'] for p in models[id]['renderPolygons']])
    assert target.symmetric_difference(source).area<.15,group['id']
    allowed=unary_union([Polygon(models[id]['footprint'],models[id].get('worldHoles',[])) for seam in r['boundaryOverlapReviews']
                        if set(group['modelIds']).intersection(seam['models']) for id in seam['models'] if id not in group['modelIds']])
    assert target.difference(actual).difference(allowed.buffer(.002)).area<.08,group['id']
    assert actual.difference(target).area<.08,group['id']
    iou=source.intersection(actual).area/source.union(actual).area
    assert iou>.99 and iou>group['previousUnionIoU'],(group['id'],iou)
    for id in group['modelIds']:
        b=models[id];c=corrections[id]
        for key,saved in [('height','preservedHeight'),('roofRise','preservedRoofRise'),('roofBays','preservedRoofBays'),('roofAxis','preservedRoofAxis')]:assert b[key]==c[saved],(id,key)
    results.append({'id':group['id'],'before':group['previousUnionIoU'],'renderedIoU':iou})
for row in r['mapTracedBuildings']+r['locallyTransferredBuildings']:
    b=models[row['modelId']]
    assert b['footprint']==row['worldFootprint'] and 'sourceFootprintFid' not in b
    assert b['height']==row['eavesHeight'] and b['roofRise']==row['roofRise']
assert 'sourceFootprintFid' not in models['howards-620']
assert models['howards-620']['footprintEvidence'] and models['howards-620']['source']=='goad-f3-city'
stacks={s['id']:s for s in scene['structures'] if s['siteId']==260}
assert len(r['structures'])==len(stacks)==18
for row in r['structures']:
    s=stacks[row['id']]
    assert s['height']==row['preservedHeight']
    assert Point(s['x'],s['z']).distance(Point(row['centre']))<.001
    if 'sourceFid' in row:
        source=unary_union([Polygon(p[0],p[1:]) for p in row['sourcePolygons']])
        assert source.centroid.distance(Point(s['x'],s['z']))<.001
    else:assert row['transferGroup'] and len(row['groupFractions'])==2
plan=load('docs/data/ground-plan.json');bank=load(r['bankRegister'])
river=next(q for q in plan['rivers'] if q['id']==bank['riverId'])
prior=copy.deepcopy(river['polygons']);ring=prior[bank['polygonIndex']][bank['ringIndex']]
for fix in bank['replacements']:
    assert ring[fix['vertex']]==fix['point']
    ring[fix['vertex']]=fix['priorPoint']
oldwater=unary_union([Polygon(p[0],p[1:]) for p in prior])
newwater=unary_union([Polygon(p[0],p[1:]) for p in river['polygons']])
assert oldwater.is_valid and newwater.is_valid
assert len(getattr(oldwater,'geoms',[oldwater]))==len(getattr(newwater,'geoms',[newwater]))
patch=box(-785,-290,-720,-165)
assert oldwater.symmetric_difference(newwater).difference(patch).area<.01
# A narrow race remains continuous through the mill; it has not been filled to
# make the building check pass. The intentional mill crossing remains explicit.
assert newwater.covers(LineString([[-737,-280],[-734,-269],[-731.5,-259.7]]))
water=unary_union([Polygon(p[0],p[1:]) for q in plan['rivers']+scene['westContext']['rivers'] for p in q['polygons']])
for id in accounted:
    b=models[id];actual=unary_union([Polygon(p['outer'],p['holes']) for p in b['renderPolygons']])
    wet=actual.intersection(water).area
    if id=='howards-644':assert 1<wet<10 and b['waterReview']
    else:assert wet<.01,(id,wet)
(ROOT/'reference/footprint-model-alignment/verified-howards.json').write_text(json.dumps(results,indent=2)+'\n')
print(f'Howards: 83 source-linked ranges, one direct OS trace, one local Goad transfer, one deferred range; 18 chimneys. Minimum rendered group agreement {min(q["renderedIoU"] for q in results):.3%}; millrace retained.')
