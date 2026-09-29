"""Check Hunt's shared exterior, retained rooms, stacks and river clearance."""
import json
import math
from pathlib import Path
from shapely import affinity
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
load = lambda p: json.loads((ROOT / p).read_text())
r = load('data/maps/hunt-works-footprint-alignment.json')
s = load('docs/data/factory-buildings.json')
models = {b['id']: b for b in s['buildings']}
corrections = {c['modelId']: c for c in r['buildings']}
assert len(corrections) == 10 and len(r['groups']) == 6 and len(r['additionalBuildings']) == 3
assert set(corrections) == {b['id'] for b in s['buildings'] if b['siteId'] == 564}
assert r['supersedesLocalTransfers'] == ['site564-range-1']
assert s['footprintAlignment']['locallyTransferredRanges'] == 2
registers = [load('data/maps/factory-footprint-alignment.json')] + [load(p) for p in s['footprintAlignment']['groupRegisters']]
used = set()
for q in registers:
    if q == r:
        continue
    for g in q.get('groups', q['buildings']):
        used.update(g.get('sourceFids', [g.get('sourceFid')]))
plan = load('docs/data/ground-plan.json')
water = unary_union([Polygon(p[0], p[1:]) for river in plan['rivers'] + s['westContext']['rivers'] for p in river['polygons']])
roads = unary_union([LineString(q['points']).buffer(q['width']/2+1.1, cap_style=2, join_style=2) for q in load('data/maps/district-road-traces.json')['roads']])
results = []
for g in r['groups']:
    assert not used.intersection(g['sourceFids']), g['id']
    used.update(g['sourceFids'])
    source = unary_union([Polygon(p[0], p[1:]) for p in g['sourcePolygons']])
    parts = [Polygon(corrections[id]['worldFootprint'], corrections[id]['worldHoles']) for id in g['modelIds']]
    target = unary_union(parts)
    actual = unary_union([Polygon(p['outer'], p['holes']) for id in g['modelIds'] for p in models[id]['renderPolygons']])
    assert target.symmetric_difference(source).area < .1, g['id']
    assert sum(p.area for p in parts) - target.area < .01, g['id']
    assert actual.symmetric_difference(target).area < .02, g['id']
    assert target.intersection(water.buffer(.12)).area < .01, g['id']
    assert target.intersection(roads).area < .01, g['id']
    agreement = actual.intersection(source).area / actual.union(source).area
    assert agreement > .9995, g['id']
    assert set(g['modelIds']) <= {a['id'] for a in r['additionalBuildings']} or agreement > g['previousUnionIoU']
    for id in g['modelIds']:
        b, c = models[id], corrections[id]
        assert b['sourceFootprintFids'] == g['sourceFids'] and b['footprintGroup'] == g['id']
        assert b['footprintSource'] == 'author-os-footprints-1891-96'
        for key, saved in [('height','preservedHeight'), ('roofRise','preservedRoofRise'), ('roofAxis','preservedRoofAxis'), ('roofBays','preservedRoofBays')]:
            assert b[key] == c[saved], (id, key)
        assert abs(b['rotation'] - c['footprintRotationDegrees']) < .0001
    results.append(dict(id=g['id'], previousIoU=g['previousUnionIoU'], renderedIoU=agreement))
assert len(r['groups'][0]['modelIds']) == 5
assert models['site564-range-7']['height'] == 6.9  # Goad's two-storey dwelling.
volumes = unary_union([Polygon(p['outer'], p['holes']) for b in s['buildings'] for p in b['renderPolygons']])
stacks = [t for t in s['structures'] if t['siteId'] == 564]
assert len(stacks) == 2
for t in stacks:
    c = next(c for c in r['structures'] if c['id'] == t['id'])
    assert t['height'] == c['preservedHeight']
    assert Point(t['x'], t['z']).distance(Point(c['centre'])) < .001
    shaft = Point(t['x'], t['z']).buffer(t['radius'])
    assert shaft.intersection(water).area < .001 and shaft.intersection(roads).area < .001
    if 'sourceFid' in c:
        assert t['mappedHeightFeet'] == 80 and t['height'] == 24.384
        assert t['sourceFootprintFid'] == 1013155
        base = unary_union([Polygon(p[0],p[1:]) for p in c['sourcePolygons']])
        h = t['radius'] * 1.2 / math.sqrt(2)
        plinth = affinity.translate(affinity.rotate(box(-h,-h,h,h),t['rotation']), t['x'], t['z'])
        assert plinth.difference(base).area < .001
        assert plinth.intersection(volumes).area < .001
    else:
        assert t['height'] == 22 and 'sourceFootprintFid' not in t
        body = unary_union([Polygon(p[0],p[1:]) for p in r['groups'][0]['sourcePolygons']])
        assert body.contains(Point(t['x'],t['z']))
# Preserve Bow Bridge's corrected boundary, without relying on renderer clipping.
bow = unary_union([Polygon(b['footprint'],b.get('worldHoles',[])) for b in models.values() if b['siteId']==254])
hunt = unary_union([Polygon(models[id]['footprint'],models[id].get('worldHoles',[])) for id in corrections])
assert bow.intersection(hunt).area < .01
bank = load('data/maps/hunt-works-bank-alignment.json')
ring = next(q for q in plan['rivers'] if q['id']==18)['polygons'][0][0]
baseline = [list(p) for p in ring]
assert [c['vertex'] for c in bank['replacements']] == [39,40]
for c in bank['replacements']:
    assert ring[c['vertex']] == c['point']
    assert math.dist(c['priorPoint'],c['point']) <= 3.5
    baseline[c['vertex']] = c['priorPoint']
old, new = Polygon(baseline), Polygon(ring)
assert new.is_valid and new.difference(old).area < .001 and new.area < old.area
assert Polygon(models['site564-furnaces']['footprint']).intersection(old).area > 15
channel = LineString(ring[39:42]).distance(LineString(ring[126:134]))
assert channel > 10, channel
(ROOT/'reference/footprint-model-alignment/verified-hunt-works.json').write_text(json.dumps(results,indent=2)+'\n')
print(f'Hunt: ten source-linked ranges, three additions, two chimneys and clear shared boundary; minimum group agreement {min(q["renderedIoU"] for q in results):.3%}; local channel {channel:.2f} m.')
