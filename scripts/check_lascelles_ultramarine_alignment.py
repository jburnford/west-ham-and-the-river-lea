"""Check the six works ranges, explicit sheet joins, shaft opening and lane."""
import json
import math
from pathlib import Path
from shapely import affinity
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
load = lambda p: json.loads((ROOT/p).read_text())
r = load('data/maps/lascelles-ultramarine-footprint-alignment.json')
s = load('docs/data/factory-buildings.json')
models = {b['id']:b for b in s['buildings']}
cs = {c['modelId']:c for c in r['buildings']}
assert len(cs)==6 and len(r['groups'])==5
assert set(cs)=={b['id'] for b in s['buildings'] if b['siteId'] in [565,566] and b['id']!='site568-range-17'}
registers = [load('data/maps/factory-footprint-alignment.json')]+[load(p) for p in s['footprintAlignment']['groupRegisters']]
used = set()
for q in registers:
    if q==r:continue
    for g in q.get('groups',q['buildings']):used.update(g.get('sourceFids',[g.get('sourceFid')]))
plan = load('docs/data/ground-plan.json')
water = unary_union([Polygon(p[0],p[1:]) for river in plan['rivers']+s['westContext']['rivers'] for p in river['polygons']])
road_rows = load('data/maps/district-road-traces.json')['roads']
roads = unary_union([LineString(q['points']).buffer(q['width']/2+1.1,cap_style=2,join_style=2) for q in road_rows])
results = []
for g in r['groups']:
    assert not used.intersection(g['sourceFids']),g['id']
    used.update(g['sourceFids'])
    source = unary_union([Polygon(p[0],p[1:]) for p in g['sourcePolygons']])
    reference = unary_union([Polygon(p[0],p[1:]) for p in g['reconciledPolygons']])
    parts = [Polygon(cs[id]['worldFootprint'],cs[id]['worldHoles']) for id in g['modelIds']]
    target = unary_union(parts)
    actual = unary_union([Polygon(p['outer'],p['holes']) for id in g['modelIds'] for p in models[id]['renderPolygons']])
    if 'sheetJoin' in g:
        join = Polygon(g['sheetJoin']['worldPolygon'])
        assert source.geom_type=='MultiPolygon' and len(source.geoms)==2
        assert reference.symmetric_difference(source.union(join)).area<.06,g['id']
        # Serialized source edges retain full precision; authoring unions use
        # the millimetre grid, accounting for small boundary slivers.
        assert abs(reference.difference(source).area-g['sheetJoin']['addedAreaM2'])<.03
        assert 19<g['sheetJoin']['addedAreaM2']<23
        # Both long join edges must stay on the narrow source sheet border.
        assert join.bounds[2]-join.bounds[0]<2
    else:
        assert reference.symmetric_difference(source).area<.05
    assert reference.geom_type=='Polygon' and reference.is_valid
    assert target.symmetric_difference(reference).area<.03,g['id']
    assert sum(p.area for p in parts)-target.area<.01,g['id']
    assert actual.symmetric_difference(target).area<.03,g['id']
    assert target.intersection(water.buffer(.12)).area<.01,g['id']
    assert target.intersection(roads).area<.01,g['id']
    raw_score = actual.intersection(source).area/actual.union(source).area
    score = actual.intersection(reference).area/actual.union(reference).area
    assert score>.9995 and raw_score>g['previousUnionIoU']
    for id in g['modelIds']:
        b,c = models[id],cs[id]
        assert b['sourceFootprintFids']==g['sourceFids'] and b['footprintGroup']==g['id']
        for key,saved in [('height','preservedHeight'),('roofRise','preservedRoofRise'),('roofAxis','preservedRoofAxis'),('roofBays','preservedRoofBays')]:assert b[key]==c[saved]
        assert abs(b['rotation']-c['footprintRotationDegrees'])<.0001
    results.append(dict(id=g['id'],previousIoU=g['previousUnionIoU'],rawSourceIoU=raw_score,reconciledIoU=score))
stack = next(t for t in s['structures'] if t['id']=='stack-566-1203-1650')
c = r['structures'][0]
assert stack['mappedHeightFeet']==60 and stack['height']==18.288 and stack['radius']==1.05
assert stack['sourceFootprintFid']==986471
assert Point(stack['x'],stack['z']).distance(Point(c['centre']))<.001
base = unary_union([Polygon(p[0],p[1:]) for p in c['sourcePolygons']])
half = stack['radius']*1.2/math.sqrt(2)
plinth = affinity.translate(affinity.rotate(box(-half,-half,half,half),stack['rotation']),stack['x'],stack['z'])
assert plinth.difference(base).area<.001
volumes = unary_union([Polygon(p['outer'],p['holes']) for b in s['buildings'] for p in b['renderPolygons']])
assert plinth.intersection(volumes).area<.001
holes = unary_union([Polygon(h) for id in ['site566-range-2','site566-range-3'] for p in models[id]['renderPolygons'] for h in p['holes']])
assert plinth.difference(holes).area<.001,'Lost chimney opening'
lane = next(q for q in road_rows if q['name']=='Sugar House Lane')
prior = lane['lascellesUltramarineAlignment']['priorPoints']
assert lane['williamsAsphalteAlignment']['priorPoints'][:-1]==prior[:-1] and lane['width']==5.2
assert lane['points'][-1]==[round(prior[-1][0]-3.5,3),prior[-1][1]]
old_corridor = LineString(prior).buffer(3.7,cap_style=2,join_style=2)
assert old_corridor.intersection(Polygon(models['site566-range-1']['footprint'])).area>34
# No adjacent works may depend on clipping away a newly aligned range.
body = unary_union([Polygon(models[id]['footprint'],models[id]['worldHoles']) for id in cs])
for b in s['buildings']:
    if b['id'] not in cs:assert body.intersection(Polygon(b['footprint'],b.get('worldHoles',[]))).area<.02,b['id']
(ROOT/'reference/footprint-model-alignment/verified-lascelles-ultramarine.json').write_text(json.dumps(results,indent=2)+'\n')
print(f'Lascelles/Ultramarine: six ranges, two recorded sheet joins, 60-foot chimney opening and clear lane; minimum reconciled agreement {min(v["reconciledIoU"] for v in results):.3%}.')
