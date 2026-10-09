"""Check all refinery/depot ranges, mapped shafts and the narrow lane frontage."""
import json
import math
from pathlib import Path
from shapely import affinity
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union
from factory_map_sources import mosaic
from factory_street_clearance import street_clearances

ROOT = Path(__file__).resolve().parents[1]
load = lambda p:json.loads((ROOT/p).read_text())
r = load('data/maps/refinery-printing-footprint-alignment.json')
s = load('docs/data/factory-buildings.json')
models = {b['id']:b for b in s['buildings']}
cs = {b['modelId']:b for b in r['buildings']}
assert len(cs)==17 and len(r['groups'])==17 and len(r['additionalBuildings'])==5
ids = set(cs)|{'site567-range-13'}
assert ids=={b['id'] for b in s['buildings'] if b['siteId']==567 and '-infill-' not in b['id']}  # task F infill ranges are core-infill-footprint-alignment.json's
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
    target = unary_union([Polygon(cs[id]['worldFootprint'],cs[id]['worldHoles']) for id in g['modelIds']])
    actual = unary_union([Polygon(p['outer'],p['holes']) for id in g['modelIds'] for p in models[id]['renderPolygons']])
    assert target.symmetric_difference(source).area<.05,g['id']
    assert actual.symmetric_difference(target).area<.02,g['id']
    score = actual.intersection(source).area/actual.union(source).area
    assert score>.9995
    if not g['additional']:assert score>g['previousUnionIoU'],g['id']
    for id in g['modelIds']:
        b,c = models[id],cs[id]
        assert b['footprintGroup']==g['id'] and b['sourceFootprintFids']==g['sourceFids']
        for key,saved in [('height','preservedHeight'),('roofRise','preservedRoofRise'),('roofAxis','preservedRoofAxis'),('roofBays','preservedRoofBays')]:assert b[key]==c[saved]
        assert abs(b['rotation']-c['footprintRotationDegrees'])<.0001
    results.append(dict(id=g['id'],previousIoU=g['previousUnionIoU'],sourceIoU=score))
assert len(r['mapTracedBuildings'])==1
c = r['mapTracedBuildings'][0]
_,world,_ = mosaic(c['mosaicBounds'])
reference = Polygon(world(c['mosaicPixels']))
b = models[c['modelId']]
actual = unary_union([Polygon(p['outer'],p['holes']) for p in b['renderPolygons']])
assert reference.symmetric_difference(actual).area<.05
assert b['footprintSource']=='os-1893-direct-trace' and 'sourceFootprintFids' not in b
for key,saved in [('height','eavesHeight'),('roofRise','roofRise'),('roofAxis','roofAxis'),('roofBays','roofBays')]:assert b[key]==c[saved]
roads = load('data/maps/district-road-traces.json')['roads']
lane = next(q for q in roads if q['name']=='Sugar House Lane')
passage = next(q for q in roads if q['name']=='Sugar House Lane works passage')
change = lane['refineryPrintingAlignment']
prior = change['priorPoints']
refinery_points = lane.get('kendrickUsherAlignment',{}).get('priorPoints',lane['points'])
assert refinery_points==prior[:10]+change['replacementPoints']+prior[12:]
assert len(refinery_points)==len(prior)+2 and lane['width']==5.2 and passage['width']==4
prior_passage = passage['refineryPrintingAlignment']['priorPoints']
assert passage['points'][1:-1]==prior_passage[1:-1]
assert passage['points'][-1]==[prior_passage[-1][0],round(prior_passage[-1][1]-4.2,3)]
assert LineString(lane['points']).distance(Point(passage['points'][0]))<.001
review = lane['buildingClearanceReviews'][0]
assert set(review['modelIds'])=={'site567-range-1','site567-range-2','site947-range-24','site947-range-25'}
assert review['shoulderWidth']==.55
gap = Polygon(models['site947-range-24']['footprint']).distance(Polygon(models['site567-range-1']['footprint']))
assert 6.71<gap<6.72 and lane['width']+2*.55<gap<lane['width']+2*1.1
streets,frontage_streets = street_clearances(roads)
plan = load('docs/data/ground-plan.json')
water = unary_union([Polygon(p[0],p[1:]) for q in plan['rivers']+s['westContext']['rivers'] for p in q['polygons']])
body = unary_union([Polygon(models[id]['footprint'],models[id].get('worldHoles',[])) for id in ids])
assert body.intersection(water.buffer(.12)).area<.01
for id in ids|set(review['modelIds']):
    p = Polygon(models[id]['footprint'],models[id].get('worldHoles',[]))
    assert p.intersection(frontage_streets.get(id,streets)).area<.01,id
    actual = unary_union([Polygon(q['outer'],q['holes']) for q in models[id]['renderPolygons']])
    assert p.symmetric_difference(actual).area<.02,id
    if id in ids:
        for b in s['buildings']:
            if b['id']!=id:assert p.intersection(Polygon(b['footprint'],b.get('worldHoles',[]))).area<.04,(id,b['id'])
for c in r['structures']:
    stack = next(t for t in s['structures'] if t['id']==c['id'])
    assert stack['height']==c['preservedHeight']==22 and stack['radius']==c['radius']
    assert stack['sourceFootprintFid']==c['sourceFid']
    assert Point(stack['x'],stack['z']).distance(Point(c['centre']))<.001
    base = unary_union([Polygon(p[0],p[1:]) for p in c['sourcePolygons']])
    half = stack['radius']*1.2/math.sqrt(2)
    plinth = affinity.translate(affinity.rotate(box(-half,-half,half,half),stack['rotation']),stack['x'],stack['z'])
    assert plinth.difference(base).area<.001
    assert plinth.intersection(body).area<.001
    assert plinth.intersection(streets).area<.001
(ROOT/'reference/footprint-model-alignment/verified-refinery-printing.json').write_text(json.dumps(results,indent=2)+'\n')
print(f'Refinery/printing: 17 source-linked ranges, one direct trace, five additions, two mapped chimney bases and retained façades through the narrow lane; minimum source agreement {min(v["sourceIoU"] for v in results):.3%}.')
