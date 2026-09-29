"""Audit cooperage/Winstone source geometry, inherited elevations and lane access."""
import json
import math
from pathlib import Path
from shapely import affinity
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
load = lambda p: json.loads((ROOT/p).read_text())
r = load('data/maps/sugar-house-footprint-alignment.json')
scene = load('docs/data/factory-buildings.json')
models = {b['id']:b for b in scene['buildings']}
corrections = {b['modelId']:b for b in r['buildings']}
assert len(corrections) == 18 and len(r['groups']) == 14
assert len(r['additionalBuildings']) == 3 and len(r['deferred']) == 12
accounted = list(corrections) + r['previouslyAligned'] + [b['modelId'] for b in r['deferred']]
assert len(accounted) == len(set(accounted)) == 31
assert set(accounted) == {b['id'] for b in scene['buildings'] if b['siteId']==964}
registers = [load('data/maps/factory-footprint-alignment.json')] + [load(path) for path in scene['footprintAlignment']['groupRegisters']]
assert sum(len(q['buildings']) for q in registers) == scene['footprintAlignment']['matchedRanges']
used = set()
for register in registers:
    if register == r:
        continue
    for group in register.get('groups', register['buildings']):
        used.update(group.get('sourceFids', [group.get('sourceFid')]))
results = []
for group in r['groups']:
    assert not used.intersection(group['sourceFids']), group['id']
    used.update(group['sourceFids'])
    source = unary_union([Polygon(p[0],p[1:]) for p in group['sourcePolygons']])
    targets, actuals, previous = [], [], []
    for id in group['modelIds']:
        c, b = corrections[id], models[id]
        target = Polygon(c['worldFootprint'],c['worldHoles'])
        actual = unary_union([Polygon(p['outer'],p['holes']) for p in b['renderPolygons']])
        assert b['footprintGroup'] == group['id'] and b['sourceFootprintFids'] == group['sourceFids']
        assert Polygon(b['footprint'],b['worldHoles']).symmetric_difference(target).area < .001
        assert all(target.intersection(p).area < .01 for p in targets), (id,'compartment overlap')
        for key, saved in [('height','preservedHeight'),('roofRise','preservedRoofRise'),('roofBays','preservedRoofBays'),('roofAxis','preservedRoofAxis')]:
            assert b[key] == c[saved], (id,key)
        assert abs(b['rotation']-c['footprintRotationDegrees']) < .0001
        assert b['heightEvidence'] and b['roofEvidence']
        targets.append(target); actuals.append(actual); previous.append(Polygon(c['priorFootprint']))
    target, actual, old = map(unary_union, [targets, actuals, previous])
    assert target.symmetric_difference(source).area < .15, group['id']
    allowed = unary_union([Polygon(models[id]['footprint'],models[id].get('worldHoles',[]))
        for seam in r['boundaryOverlapReviews'] if set(group['modelIds']).intersection(seam['models'])
        for id in seam['models'] if id not in group['modelIds']])
    assert target.difference(actual).difference(allowed.buffer(.002)).area < .08, (group['id'],'unreviewed clipping')
    assert actual.difference(target).area < .05, group['id']
    before = old.intersection(source).area / old.union(source).area
    after = actual.intersection(source).area / actual.union(source).area
    assert abs(before-group['previousUnionIoU']) < .0001
    assert after > .998 and (group['additional'] or after>before), (group['id'],before,after)
    results.append({'id':group['id'], 'beforeIoU':before, 'renderedIoU':after})

# Retain the five-storey 1882 warehouse and its paired roof, separate from the
# lower adjoining ranges whose precise construction dates remain uncertain.
sugar = models['site964-range-7']
assert sugar['date']=='1882' and sugar['storeys']==5 and sugar['roofBays']==2
assert sugar['height']==16.2 and sugar['roofRise']==3 and sugar['material']=='redbrick'
beam, cellar = models['site964-range-10'], models['site964-range-11']
assert beam['roofAxis']=='z' and cellar['roofAxis']=='x'
beam_direction = (beam['rotation']+90)%180
cellar_direction = cellar['rotation']%180
assert 30 < abs((beam_direction-cellar_direction+90)%180-90) < 50

c = r['structures'][0]
stack = next(s for s in scene['structures'] if s['id']==c['id'])
base_source = unary_union([Polygon(p[0],p[1:]) for p in c['sourcePolygons']])
assert Point(stack['x'],stack['z']).distance(base_source.centroid)<.001
assert stack['sourceFootprintFid']==1142465 and stack['height']==c['preservedHeight']
assert stack['radius']==c['radius'] and stack['priorRadius']==c['priorRadius']
holes = unary_union([Polygon(h) for p in models['site964-range-15']['renderPolygons'] for h in p['holes']])
half = stack['radius']*1.2/math.sqrt(2)
plinth = affinity.translate(affinity.rotate(box(-half,-half,half,half),stack['rotation']),stack['x'],stack['z'])
assert plinth.difference(holes).area<.001, 'Chimney plinth protrudes into the sawmill roof'

roads = {q['name']:q for q in load('data/maps/district-road-traces.json')['roads']}
lane, passage = [roads[name] for name in ['Sugar House Lane','Sugar House Lane works passage']]
assert lane['points'][:3]==lane['sugarHouseAlignment']['priorPoints'][:3]
assert lane['points'][6:]==lane['sugarHouseAlignment']['priorPoints'][6:]
assert LineString(lane['points']).distance(Point(passage['points'][0]))<.002
assert lane['width']==7 and passage['width']==4
for road in [lane,passage]:
    corridor = LineString(road['points']).buffer(road['width']/2+1.1,cap_style=2,join_style=2)
    for id in corrections:
        overlap = corridor.intersection(Polygon(models[id]['footprint'])).area
        review = r['roadBoundaryReview']
        if road['name']==review['road'] and id==review['modelId']:
            assert abs(overlap-review['sourceOverlapAreaM2'])<.002
        else:
            assert overlap<.01,(road['name'],id)

yard = next(y for y in load('docs/data/factory-yards.json')['sites'] if y['id']==r['yard']['id'])
surface = unary_union([Polygon(p[0],p[1:]) for p in yard['polygons']])
envelope = unary_union([Polygon(p[0],p[1:]) for p in r['yard']['polygons']])
assert surface.difference(envelope).area<.001 and surface.area>3000
assert all(surface.covers(Point(p)) for p in [(-690,-75),(-680,-40),(-710,-35)])
assert yard['stock'] and all(s['kind']=='timber' for s in yard['stock'])

(ROOT/'reference/footprint-model-alignment/verified-sugar-house.json').write_text(json.dumps(results,indent=2)+'\n')
print(f'Sugar House: 18 source-linked ranges in 14 groups, three added low compartments, mapped chimney opening and clear lanes; minimum rendered group agreement {min(v["renderedIoU"] for v in results):.3%}.')
