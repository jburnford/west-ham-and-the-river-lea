"""Check the actual published factory geometry, coverage and period constraints."""
import json
import math
from pathlib import Path

from shapely.geometry import Polygon, Point, LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parents[1]
factory = json.loads((ROOT/'docs/data/factory-buildings.json').read_text())
plan = json.loads((ROOT/'docs/data/ground-plan.json').read_text())
rows = factory['buildings']
assert len({b['id'] for b in rows}) == len(rows)
known = {s['id'] for s in factory['sites'] + factory['excludedSites']} | {s['siteId'] for s in factory['retainedLandmarks']}
assert all(s['id'] in known for s in plan['sites']), 'Every original industrial parcel needs a scope decision'
assert {b['siteId'] for b in rows} == {s['id'] for s in factory['sites']}
assert all(sum(b['siteId'] == s['id'] for b in rows) == s['buildingCount'] for s in factory['sites'])
water = unary_union([Polygon(p[0], p[1:]) for r in plan['rivers'] + factory['westContext']['rivers'] for p in r['polygons']])
polys = []
for b in rows:
    assert b['source'] in factory['sources'] and b['heightEvidence'] and b['roofEvidence'], b['id']
    assert 0 < b['height'] < 35 and 0 <= b['roofRise'] < 9, b['id']
    parts = [Polygon(p['outer'], p['holes']) for p in b['renderPolygons']]
    assert parts and all(p.is_valid and p.area > .1 for p in parts), b['id']
    p = unary_union(parts)
    assert p.difference(Polygon(b['footprint']).buffer(.003)).area < .02, b['id']
    if b['id'] in {'site257-mill','site258-dry'}:
        interface=b['waterInterface']
        river=next(r for r in plan['rivers'] if r['id']==interface['riverId'])
        local=unary_union([Polygon(q[0],q[1:]) for q in river['polygons']])
        assert b['waterReview']
        assert abs(p.intersection(local).area-interface['observedOverlapAreaM2'])<.02,b['id']
        assert p.intersection(water.difference(local)).area<.01,b['id']
    elif b['id'] not in {'howards-644', 'house-main', 'house-tail', 'clock-kilns'}:
        assert p.intersection(water).area < 1, ('Unreviewed river obstruction', b['id'])
    else:
        assert b.get('waterReview'), b['id']
    polys.append(p)
tree = STRtree(polys)
for i, p in enumerate(polys):
    for j in tree.query(p, predicate='intersects'):
        if j < i:
            assert p.intersection(polys[j]).area < .15, ('Overlapping rendered ranges', rows[i]['id'], rows[j]['id'])
holders = factory['holders'] + [h for h in plan['neighbourhood']['holders'] if h['siteId'] != 924]
assert len(factory['holders']) == 9
assert {h['id'] for h in factory['holders']} == {f'bromley-{n}' for n in range(1, 10)}
for i, h in enumerate(holders):
    p = Point(h['x'], h['z']).buffer(h['radius'])
    assert p.intersection(water).area < 1, h['id']
    for q in polys:
        assert p.intersection(q).area < .1, ('Building inside holder', h['id'])
    for other in holders[:i]:
        assert Point(h['x'], h['z']).distance(Point(other['x'], other['z'])) > h['radius'] + other['radius']
sugar = next(b for b in rows if b['id'] == 'site964-range-7')
assert sugar['date'] == '1882' and sugar['storeys'] == 5 and sugar['roofBays'] == 2
assert all(h['height'] == 23 for h in factory['holders']), 'No later third-tier holder additions'
stacks = [s for s in factory['structures'] if s['kind'] == 'chimney']
infra = json.loads((ROOT/'docs/data/infrastructure.json').read_text())
streets = unary_union([LineString(r['route']).buffer(r['width']/2) for r in infra['roads']])
assert len(stacks) == factory['counts']['chimneys']
assert len({s['id'] for s in stacks}) == len(stacks)
for i, s in enumerate(stacks):
    assert s['siteId'] in {site['id'] for site in factory['sites']}
    assert (s.get('pixelPosition') or s.get('parentBuildingId')) and s['positionEvidence'] and s['heightEvidence'] and s['profileEvidence']
    if s.get('evidenceType') in {'map-and-photograph', 'photograph-interpretation', 'map-interpretation'}:
        assert s['supportingSources'] and all(k in factory['sources'] for k in s['supportingSources'])
    else:
        assert s['symbolKey'] in factory['symbolKeys']
    assert s['section'] in {'square', 'round'} and 8 < s['height'] < 80
    if 'mappedHeightFeet' in s:
        assert math.isclose(s['height'], s['mappedHeightFeet']*.3048, abs_tol=.0001), s['id']
    centre = Point(s['x'], s['z'])
    if s.get('parentBuildingId'):
        parent_index = next(j for j, b in enumerate(rows) if b['id'] == s['parentBuildingId'])
        assert polys[parent_index].contains(centre), ('Roof flue outside parent building', s['id'])
    base = centre.buffer(s['radius']*1.2)
    assert base.intersection(water).area < .01, ('Chimney in river', s['id'])
    assert base.intersection(streets).area < .01, ('Chimney in street', s['id'])
    assert all(base.distance(Point(h['x'], h['z'])) > h['radius'] for h in holders), s['id']
    for b, q in zip(rows, polys):
        if q.contains(centre):
            assert s['height']+s['baseHeight'] > b['height']+b['roofRise'], ('Buried chimney', s['id'], b['id'])
    for other in stacks[:i]:
        assert centre.distance(Point(other['x'], other['z'])) > s['radius']+other['radius'], ('Duplicate/intersecting shafts', s['id'], other['id'])
assert sum('mappedHeightFeet' in s for s in stacks) == factory['counts']['chimneysWithMappedHeights']
print(f"{len(stacks)} registered chimneys: mapped feet converted, crowns above roofs, bases clear of rivers, roads, holders and other shafts.")
print(f"Factory checks passed: {len(factory['sites'])} sites, {len(rows)} ranges, all original parcels accounted for; nine Bromley holders, six West Ham holders, no unreviewed channel obstructions or overlapping building volumes.")
