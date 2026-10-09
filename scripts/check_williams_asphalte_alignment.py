"""Verify mapped exteriors, explicit OS completions, attribution and clear lane."""
import json
import math
from pathlib import Path
from shapely import affinity, set_precision
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union
from factory_map_sources import mosaic

ROOT = Path(__file__).resolve().parents[1]
load = lambda p:json.loads((ROOT/p).read_text())
r = load('data/maps/williams-asphalte-footprint-alignment.json')
s = load('docs/data/factory-buildings.json')
models = {b['id']:b for b in s['buildings']}
cs = {b['modelId']:b for b in r['buildings']}
traces = {b['modelId']:b for b in r['mapTracedBuildings']}
ids = set(cs)|set(traces)
assert len(cs)==17 and len(traces)==2 and len(r['groups'])==14
assert ids=={b['id'] for b in s['buildings'] if b['siteId']==568 and '-infill-' not in b['id']}|{'site568-range-17'}  # task F infill ranges are core-infill-footprint-alignment.json's
assert models['site568-range-17']['siteId']==566 and models['site568-range-17']['priorSiteId']==568
assert models['site568-704']['floorMark']=='2' and models['site568-704']['height']==6.9
registers = [load('data/maps/factory-footprint-alignment.json')]+[load(p) for p in s['footprintAlignment']['groupRegisters']]
used = set()
for register in registers:
    if register==r:continue
    for g in register.get('groups',register['buildings']):used.update(g.get('sourceFids',[g.get('sourceFid')]))
results = []
for g in r['groups']:
    assert not used.intersection(g['sourceFids']),g['id']
    used.update(g['sourceFids'])
    source = unary_union([Polygon(p[0],p[1:]) for p in g['sourcePolygons']])
    reference = unary_union([Polygon(p[0],p[1:]) for p in g['reconciledPolygons']])
    target = unary_union([Polygon(cs[id]['worldFootprint'],cs[id]['worldHoles']) for id in g['modelIds']])
    actual = unary_union([Polygon(p['outer'],p['holes']) for id in g['modelIds'] for p in models[id]['renderPolygons']])
    if 'mapCompletion' in g:
        c = g['mapCompletion']
        _,world,_ = mosaic(c['mosaicBounds'])
        traced = Polygon(world(c['mosaicPixels']))
        assert traced.symmetric_difference(Polygon(c['worldPolygon'])).area<.04
        assert reference.symmetric_difference(source.union(traced)).area<.06
        assert abs(reference.difference(source).area-c['addedAreaM2'])<.03
        assert 127<c['addedAreaM2']<129
    else:assert reference.symmetric_difference(source).area<.05,g['id']
    assert target.symmetric_difference(reference).area<.04,g['id']
    assert actual.symmetric_difference(target).area<.05,(g['id'],actual.symmetric_difference(target).area)
    score = actual.intersection(reference).area/actual.union(reference).area
    assert score>.9995
    raw_score = actual.intersection(source).area/actual.union(source).area
    if not g['additional']:assert raw_score>g['previousUnionIoU'],g['id']
    for id in g['modelIds']:
        b,c = models[id],cs[id]
        assert b['footprintGroup']==g['id'] and b['sourceFootprintFids']==g['sourceFids']
        for key,saved in [('height','preservedHeight'),('roofRise','preservedRoofRise'),('roofAxis','preservedRoofAxis'),('roofBays','preservedRoofBays')]:assert b[key]==c[saved]
        assert abs(b['rotation']-c['footprintRotationDegrees'])<.0001
    results.append(dict(id=g['id'],previousIoU=g['previousUnionIoU'],rawSourceIoU=raw_score,reconciledIoU=score))
for id,c in traces.items():
    _,world,_ = mosaic(c['mosaicBounds'])
    original = set_precision(Polygon(world(c['mosaicPixels'])),.001)
    source_edges = set_precision(unary_union([Polygon(p[0],p[1:]) for g in r['groups']
        if set(g['sourceFids']).intersection(c['sharedEdgeSourceFids']) for p in g['sourcePolygons']]),.001)
    reference = original.difference(source_edges)
    assert reference.symmetric_difference(Polygon(c['worldFootprint'])).area<.01
    assert abs(original.difference(reference).area-c['sharedEdgeTrimAreaM2'])<.01
    b = models[id]
    assert b['footprintSource']=='os-1893-direct-trace' and 'sourceFootprintFids' not in b
    for key,saved in [('height','eavesHeight'),('roofRise','roofRise'),('roofAxis','roofAxis'),('roofBays','roofBays')]:assert b[key]==c[saved]
    actual = unary_union([Polygon(p['outer'],p['holes']) for p in b['renderPolygons']])
    assert reference.symmetric_difference(actual).area<.03
roads = load('data/maps/district-road-traces.json')['roads']
lane = next(q for q in roads if q['name']=='Sugar House Lane')
prior = lane['williamsAsphalteAlignment']['priorPoints']
assert lane['width']==5.2
for i,(a,b) in enumerate(zip(prior,lane['refineryPrintingAlignment']['priorPoints'])):
    assert b==([round(a[0]-1.5,3),a[1]] if i in [12,13] else a)
plan = load('docs/data/ground-plan.json')
water = unary_union([Polygon(p[0],p[1:]) for q in plan['rivers']+s['westContext']['rivers'] for p in q['polygons']])
road = unary_union([LineString(q['points']).buffer(q['width']/2+1.1,cap_style=2,join_style=2) for q in roads])
body = unary_union([Polygon(models[id]['footprint'],models[id].get('worldHoles',[])) for id in ids])
assert body.intersection(water.buffer(.12)).area<.01
assert body.intersection(road).area<.01
assert body.intersection(LineString(prior).buffer(3.7,cap_style=2,join_style=2)).area>15
for id in ids:
    p = Polygon(models[id]['footprint'],models[id].get('worldHoles',[]))
    for b in s['buildings']:
        if b['id']!=id:assert p.intersection(Polygon(b['footprint'],b.get('worldHoles',[]))).area<.04,(id,b['id'])
for c in r['structures']:
    stack = next(t for t in s['structures'] if t['id']==c['id'])
    assert stack['height']==c['preservedHeight']
    assert Point(stack['x'],stack['z']).distance(Point(c['centre']))<.001
    if 'sourceFid' in c:
        assert stack['mappedHeightFeet']==60 and stack['height']==18.288
        assert stack['sourceFootprintFid']==1087863 and stack['radius']==.65
        base = unary_union([Polygon(p[0],p[1:]) for p in c['sourcePolygons']])
        half = stack['radius']*1.2/math.sqrt(2)
        plinth = affinity.translate(affinity.rotate(box(-half,-half,half,half),stack['rotation']),stack['x'],stack['z'])
        assert plinth.difference(base).area<.001
        assert plinth.intersection(body).area<.001
    else:
        assert stack['height']==22 and Polygon(models[c['parentBuildingId']]['footprint']).contains(Point(stack['x'],stack['z']))
(ROOT/'reference/footprint-model-alignment/verified-williams-asphalte.json').write_text(json.dumps(results,indent=2)+'\n')
print(f'Williams/Asphalte: 17 source-linked ranges, two direct traces, separate map completion, added 704, corrected attribution, chimneys and lane; minimum reconciled agreement {min(v["reconciledIoU"] for v in results):.3%}.')
