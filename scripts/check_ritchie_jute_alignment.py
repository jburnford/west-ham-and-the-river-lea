"""Check reviewed Ritchie mill coverage, process identity, roofs and flue base."""
import argparse
import math
from pathlib import Path

from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

from factory_alignment_checks import check_register, load
from factory_street_clearance import street_clearances
from prepare_ritchie_jute_alignment import BASELINE, SOURCE_CACHE, MAIN_IDS, CUTS, compartment_parts
from prepare_ink_works_alignment import rings

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--preflight', action='store_true')
args = parser.parse_args()
before = load(BASELINE)
prior = {b['id']: b for b in before['buildings']}
expected = {b['id'] for b in before['buildings'] if b['siteId'] == 1017}
assert len(expected) == 11
check_register('ritchie-jute', expected, 4, 0, 'remaining-trades-before',
    preflight=args.preflight, later_registers=['crown-johnson', 'western-trades'])
r = load('data/maps/ritchie-jute-footprint-alignment.json')
scene = load('docs/data/factory-buildings.json')
assert r['baseline'] == BASELINE
assert not any(r.get(k) for k in ['additionalBuildings', 'removedBuildings',
    'mapTracedBuildings', 'locallyTransferredBuildings', 'removedStructures',
    'roadRenderChanges', 'renderChanges'])
rows = {b['modelId']: b for b in r['buildings']}
groups = {g['id']: g for g in r['groups']}
assert {g['id']: g['sourceFids'] for g in r['groups']} == {
    'ritchie-main-mill': [36], 'ritchie-engine-room': [37110],
    'ritchie-office': [382213], 'ritchie-jute-warehouse': [8221]}
main = groups['ritchie-main-mill']
assert main['modelIds'] == MAIN_IDS
assert main['divisionParameters']['planFramePartitionControls'] == CUTS
registration = load('data/maps/factory-building-traces.json')['sources']['goad-f4-jute']['pixelToWorld']
assert main['divisionParameters']['pixelToWorld'] == registration
assert main['divisionParameters']['modelOrder'] == MAIN_IDS
source = Polygon(main['sourcePolygons'][0][0], main['sourcePolygons'][0][1:])
predicted = compartment_parts(source, registration)
for ident, p in zip(MAIN_IDS, predicted):
    c = rows[ident]
    assert c['worldFootprint'] == rings(p)[0] and c['worldHoles'] == rings(p)[1:], ident
for ident, c in rows.items():
    old = prior[ident]
    assert c['siteId'] == old['siteId'] == 1017
    assert c['name'] == old['name']
    assert c['priorFootprint'] == old['footprint']
    assert c['priorRotationDegrees'] == old['rotation']
    body = Polygon(c['worldFootprint'], c['worldHoles'])
    rounded = Polygon([[round(x, 3), round(y, 3)] for x, y in body.exterior.coords],
        [[[round(x, 3), round(y, 3)] for x, y in h.coords] for h in body.interiors])
    assert rounded.is_valid and rounded.symmetric_difference(body).area < .02, ident
    for key, field in [('height', 'preservedHeight'), ('roofRise', 'preservedRoofRise'),
                       ('roofAxis', 'preservedRoofAxis'), ('roofBays', 'preservedRoofBays')]:
        assert c[field] == old[key], (ident, key)
# Source IDs must be unique across every saved alignment register, including
# independently fitted structures that are not part of building groups.
used = set()
for path in sorted((ROOT/'data/maps').glob('*footprint-alignment.json')):
    if path.name == 'ritchie-jute-footprint-alignment.json':
        continue
    other = load(str(path.relative_to(ROOT)))
    for group in other.get('groups', other.get('buildings', [])):
        used.update(group.get('sourceFids', [group.get('sourceFid')]))
    for key in ['structures', 'tanks', 'mappedPlants', 'additionalStructures']:
        for entry in other.get(key, []):
            used.update(entry.get('sourceFootprintFids', [entry.get('sourceFid', entry.get('sourceFootprintFid'))]))
own_fids = {fid for g in r['groups'] for fid in g['sourceFids']}
assert not own_fids.intersection(used)
assert len(r['structures']) == 1
c = r['structures'][0]
old = next(s for s in before['structures'] if s['id'] == c['id'])
assert c['id'] == 'stack-1017-2126-603' and c['sourceFid'] == 940622
assert c['sourceFid'] not in own_fids | used
assert old['mappedHeightFeet'] == 200 and old['height'] == 200*.3048
assert c['preservedHeight'] == old['height'] == 60.96
assert c['preservedSection'] == old['section'] == 'round'
assert c['priorCentre'] == [old['x'], old['z']] and c['priorRadius'] == old['radius']
assert c['rotation'] == old['rotation']
assert c['plinthRadiusMultiplier'] == 1.2 and c['rendererPlinthSides'] == 16
base = Polygon(c['sourcePolygons'][0][0], c['sourcePolygons'][0][1:])
centre = Point(c['centre'])
assert centre.distance(base.centroid) < .001
assert 0 < c['radius'] <= old['radius']
assert c['radius'] == min(old['radius'], math.floor(centre.distance(base.boundary)/1.2*1000)/1000)
plinth = Polygon([(centre.x + c['radius']*1.2*math.sin(c['rotation']*math.pi/180+i*math.pi/8),
                   centre.y + c['radius']*1.2*math.cos(c['rotation']*math.pi/180+i*math.pi/8))
                  for i in range(16)])
assert base.covers(plinth)
bodies = [Polygon(row['worldFootprint'], row['worldHoles']) for row in r['buildings']]
bodies += [Polygon(b['footprint'], b.get('worldHoles', []))
           for b in scene['buildings'] if b['id'] not in expected]
streets, _ = street_clearances(load('data/maps/district-road-traces.json')['roads'])
water = unary_union([Polygon(p[0], p[1:]) for q in
    load('docs/data/ground-plan.json')['rivers'] + scene['westContext']['rivers'] for p in q['polygons']])
for obstacle in [unary_union(bodies), streets, water]:
    assert plinth.intersection(obstacle).area < .001
if not args.preflight:
    current = next(s for s in scene['structures'] if s['id'] == c['id'])
    assert current['sourceFootprintFid'] == c['sourceFid']
    assert current['height'] == old['height'] and current['section'] == old['section']
    assert current['mappedHeightFeet'] == 200 and current['baseHeight'] == old['baseHeight']
    assert current['rotation'] == c['rotation'] and current['radius'] == c['radius']
    assert math.dist([current['x'], current['z']], c['centre']) < .001
# Reviewable source provenance matches the immutable cache byte for byte.
cached = load(SOURCE_CACHE)
from shapely.geometry import shape
from prepare_three_mills_north_alignment import polygon
for g in r['groups']:
    assert g['sourcePolygons'] == [rings(polygon(shape(cached[str(fid)]))) for fid in g['sourceFids']]
assert c['sourcePolygons'] == [rings(polygon(shape(cached['940622'])))]
print('Ritchie jute: eleven preserved ranges, named Goad process cuts, four complete OS exteriors, unique source IDs and contained round 200-foot chimney plinth pass.')
