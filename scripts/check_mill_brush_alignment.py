"""Mill/brush complete source boundaries, courts, heights and square plinths."""
import argparse
import math
from pathlib import Path

from shapely import affinity
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

from factory_alignment_checks import check_register, load
from factory_street_clearance import street_clearances

parser = argparse.ArgumentParser()
parser.add_argument('--preflight', action='store_true')
args = parser.parse_args()
before = load('reference/footprint-model-alignment/mill-brush-brewery-before.json')
expected = {b['id'] for b in before['buildings'] if b['siteId'] in [257, 258]}
check_register('mill-brush', expected, 9, 0, 'mill-brush-brewery-before',
    preflight=args.preflight, permitted_water=['site257-mill', 'site258-dry'],
    later_registers=['bow-brewery', 'mineral-water'])
r = load('data/maps/mill-brush-footprint-alignment.json')
rows = {c['modelId']: c for c in r['buildings']}
bodies = {i: Polygon(c['worldFootprint'], c['worldHoles']) for i, c in rows.items()}
assert len(bodies['site257-mill'].interiors) == 1
assert len(bodies['site258-fibre'].interiors) == 1
assert {c['siteId'] for i,c in rows.items() if i.startswith('site257-')} == {257}
assert bodies['site257-engine'].touches(bodies['site257-south'])
assert bodies['site258-dry'].intersection(bodies['site258-warehouse']).area < .001
assert bodies['site258-stoves'].intersection(bodies['site258-coppers']).area < .001
identity = next(g for g in r['groups'] if g['id'] == 'st-thomas-south-room')['correctedIdentity']
assert identity['goadRoom'] == '858' and identity['priorRectPixels'][:2] == [1010, 1817]
assert len(r['structures']) == 2 and not r.get('removedBuildings') and not r.get('additionalBuildings')
prior_structures = {s['id']: s for s in before['structures']}
scene = load('docs/data/factory-buildings.json')
current = {s['id']: s for s in scene['structures']}
streets, _ = street_clearances(load('data/maps/district-road-traces.json')['roads'])
water = unary_union([Polygon(p[0], p[1:]) for q in
    load('docs/data/ground-plan.json')['rivers']+scene['westContext']['rivers'] for p in q['polygons']])
water_rows = [c for c in r['buildings'] if c.get('waterInterface')]
assert {c['modelId'] for c in water_rows} == {'site257-mill', 'site258-dry'}
for c in water_rows:
    interface = c['waterInterface']
    assert c['waterReview'] == interface['evidence']
    assert interface['riverId'] == (8 if c['modelId'] == 'site257-mill' else 9)
    river = next(q for q in load('docs/data/ground-plan.json')['rivers']
                 if q['id'] == interface['riverId'])
    assert river['polygons'] == interface['retainedRiverPolygons']
    mapped_water = unary_union([Polygon(p[0], p[1:]) for p in river['polygons']])
    overlap = bodies[c['modelId']].intersection(mapped_water).area
    assert abs(overlap-interface['observedOverlapAreaM2']) < .000001
    assert bodies[c['modelId']].intersection(water.difference(mapped_water)).area < .000001
    assert 29.84 < overlap < 29.85 if interface['riverId'] == 8 else 10.60 < overlap < 10.61
    if not args.preflight:
        published = next(b for b in scene['buildings'] if b['id'] == c['modelId'])
        assert published['waterInterface'] == interface and published['waterReview'] == c['waterReview']
others = [Polygon(b['footprint'], b.get('worldHoles', []))
          for b in scene['buildings'] if b['id'] not in expected]
all_used = {}
for path in sorted((Path(__file__).resolve().parents[1]/'data/maps').glob('*footprint-alignment.json')):
    if path.name == 'mill-brush-footprint-alignment.json': continue
    other = load(str(path.relative_to(Path(__file__).resolve().parents[1])))
    for g in other.get('groups', other.get('buildings', [])):
        for fid in g.get('sourceFids', [g.get('sourceFid')]):
            all_used.setdefault(fid, []).append(path.name)
    for key in ['structures', 'tanks', 'mappedPlants']:
        for s in other.get(key, []):
            fid = s.get('sourceFid', s.get('sourceFootprintFid'))
            if fid is not None: all_used.setdefault(fid, []).append(path.name)
own_fids = [f for g in r['groups'] for f in g['sourceFids']]
assert not set(own_fids).intersection(all_used), set(own_fids).intersection(all_used)
for c in r['structures']:
    old = prior_structures[c['id']]
    assert c['preservedHeight'] == old['height']
    assert c['sourceFid'] not in all_used and c['sourceFid'] not in own_fids
    centre = Point(c['centre'])
    radius = c.get('radius', old['radius'])
    plinth = affinity.rotate(box(centre.x-radius*1.2, centre.y-radius*1.2,
        centre.x+radius*1.2, centre.y+radius*1.2), c['rotation'], origin=centre)
    base = unary_union([Polygon(p[0], p[1:]) for p in c['sourcePolygons']])
    assert base.covers(plinth), c['id']
    assert centre.distance(base.centroid) < .001
    assert plinth.intersection(unary_union(list(bodies.values())+others+[streets, water])).area < .001, c['id']
    if c['sourceFid'] == 1041835:
        assert Polygon(bodies['site258-fibre'].interiors[0]).covers(plinth)
        assert old['mappedHeightFeet'] == 60
    else:
        assert c['sourceFid'] == 1073893 and old['mappedHeightFeet'] == 50
    if not args.preflight:
        actual = current[c['id']]
        assert actual['height'] == old['height'] and actual['section'] == old['section']
        assert actual['radius'] == radius and actual['sourceFootprintFid'] == c['sourceFid']
        assert math.dist([actual['x'], actual['z']], c['centre']) < .001
print('Mill/brush: three mill and seven Smith ranges, two enclosed chimney openings, corrected mill room 858, and two contained square chimney plinths pass.')
