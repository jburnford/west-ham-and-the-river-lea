"""Check rendered mill compartments, courtyard, transferred stack and access."""
import json
import math
from pathlib import Path

from shapely import affinity
from shapely.geometry import Polygon, Point, LineString
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
load = lambda path: json.loads((ROOT/path).read_text())
register = load('data/maps/sawmill-footprint-alignment.json')
scene = load('docs/data/factory-buildings.json')
models = {b['id']: b for b in scene['buildings']}
corrections = {b['modelId']: b for b in register['buildings']}
assert len(corrections) == len(register['buildings']) == 14
assert {b['id'] for b in scene['buildings'] if b['siteId']==797} == set(corrections) | set(register['retainedEarlierMatches'])
earlier = [load('data/maps/factory-footprint-alignment.json'), load('data/maps/ink-works-footprint-alignment.json')]
used_sources = {fid for r in earlier for b in r['buildings'] for fid in b.get('sourceFids', [b.get('sourceFid')])}
used_models = {b['modelId'] for r in earlier for b in r['buildings']}
assert not used_models.intersection(corrections)
assert scene['footprintAlignment']['matchedRanges'] == len(used_models) + len(corrections) == 53
results = []
for group in register['groups']:
    assert not used_sources.intersection(group['sourceFids']), group['id']
    used_sources.update(group['sourceFids'])
    source = unary_union([Polygon(p[0], p[1:]) for p in group['sourcePolygons']])
    allowed = Polygon()
    if 'boundaryOverlapReview' in group:
        neighbour = next(g for g in register['groups'] if g['id']==group['boundaryOverlapReview']['neighbourGroup'])
        allowed = unary_union([Polygon(p[0], p[1:]) for p in neighbour['sourcePolygons']])
        assert math.isclose(source.intersection(allowed).area, group['boundaryOverlapReview']['sourceOverlapAreaM2'], abs_tol=.001)
    targets, rendered, originals = [], [], []
    for id in group['modelIds']:
        r, b = corrections[id], models[id]
        target = Polygon(r['worldFootprint'], r['worldHoles'])
        actual = unary_union([Polygon(p['outer'], p['holes']) for p in b['renderPolygons']])
        assert target.is_valid and actual.is_valid, id
        assert b['footprintGroup'] == group['id'] == r['groupId']
        assert b['sourceFootprintFids'] == r['sourceFids'] == group['sourceFids']
        # Triangulation rounds vertices to millimetres, including shared cuts.
        assert actual.difference(target).area < .02 and target.difference(actual).difference(allowed.buffer(.001)).area < .08, (id, 'unreviewed compartment clipping')
        # Millimetre rounding along a long shared cut can leave a tiny sliver;
        # the renderer partitions it once, as checked by the factory audit.
        assert all(target.intersection(other).area < .02 for other in targets), id
        for key, saved in [('height', 'preservedHeight'), ('roofRise', 'preservedRoofRise'), ('roofBays', 'preservedRoofBays')]:
            assert math.isclose(b[key], r[saved]), (id, key)
        assert b['roofAxis'] == r['preservedRoofAxis']
        assert all(b.get(k)==v for k, v in r['preservedEvidence'].items()), (id, 'lost Goad evidence')
        originals.append(Polygon(r['priorFootprint'])); targets.append(target); rendered.append(actual)
    original, target, actual = map(unary_union, [originals, targets, rendered])
    assert target.symmetric_difference(source).area < .1, (group['id'], 'incomplete group')
    before = original.intersection(source).area / original.union(source).area
    after = actual.intersection(source).area / actual.union(source).area
    assert math.isclose(before, group['previousUnionIoU'], abs_tol=.0001)
    assert after > (.995 if 'boundaryOverlapReview' in group else .999) and after > before, (group['id'], before, after)
    results.append({'id': group['id'], 'beforeIoU': before, 'renderedIoU': after})

stack = next(s for s in scene['structures'] if s['id']==register['structures'][0]['id'])
transfer = register['structures'][0]
parent = models[transfer['parentBuildingId']]
actual = unary_union([Polygon(p['outer'], p['holes']) for p in parent['renderPolygons']])
assert actual.covers(Point(stack['x'], stack['z']).buffer(stack['radius']*1.2)), 'Stack leaves its parent mill'
assert stack['height'] == transfer['preservedHeight'] and stack['parentBuildingId'] == parent['id']
assert 'sourceFootprintFid' not in stack, 'Transferred internal stack misrepresented as an OS base match'
local = affinity.rotate(Polygon(parent['footprint']), -parent['rotation'], origin=(0, 0))
point = affinity.rotate(Point(stack['x'], stack['z']), -parent['rotation'], origin=(0, 0))
x0, z0, x1, z1 = local.bounds
assert math.dist([(point.x-x0)/(x1-x0), (point.y-z0)/(z1-z0)], transfer['parentFractions']) < .0001

road = next(r for r in load('data/maps/district-road-traces.json')['roads'] if r['name']=='Cook’s Road')
line = LineString(road['points'])
site = unary_union([Polygon(b['footprint'], b.get('worldHoles', [])) for b in scene['buildings'] if b['siteId']==797])
assert line.buffer(road['width']/2+1.1, join_style=2).intersection(site).area < .01, 'Cook’s Road cuts the mill'
for bridge in road['bridgeSpans']:
    assert LineString(bridge['points']).difference(line.buffer(.001)).length < .001, 'Bridge connection moved'
infra = load('docs/data/infrastructure.json')
actual_road = next(r for r in infra['roads'] if r['name']==road['name'])
assert LineString(actual_road['route']).hausdorff_distance(line) < .01, 'Stale infrastructure'
surfaces = unary_union([Polygon(t) for key in ['roadTriangles', 'pathTriangles', 'shoulderTriangles'] for t in infra[key]])
assert surfaces.intersection(site).area < .02, 'Road surface under mill or courtyard ranges'
northern = unary_union([Polygon(models[f'site797-os-{i}']['footprint']) for i in range(1, 5)])
assert northern.convex_hull.covers(Point(-1105, -137)) and northern.distance(Point(-1105, -137)) > 2, 'Towers courtyard lost'
(ROOT/'reference/footprint-model-alignment/verified-sawmill-groups.json').write_text(json.dumps(results, indent=2)+'\n')
print(f'Sawmill: 14 additional ranges in 8 groups; minimum {min(r["renderedIoU"] for r in results):.3%} source agreement; Goad evidence, courtyard, stack and road clearances retained.')
