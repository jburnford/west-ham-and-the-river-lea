"""Check Jeffrey glue exteriors, compartment cuts, preserved ranges and plinths."""
import argparse
import math
from pathlib import Path

from shapely import affinity
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

from factory_alignment_checks import check_register, load
from factory_street_clearance import street_clearances
from prepare_jeffrey_glue_alignment import validate_render_changes

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--preflight', action='store_true')
args = parser.parse_args()
before = load('reference/footprint-model-alignment/marshgate-trades-before.json')
retained = {'site790-884': 77857, 'site790-raw': 49851}
expected = {b['id'] for b in before['buildings'] if b['siteId'] == 790} - set(retained)
check_register('jeffrey-glue', expected, 7, 0, 'marshgate-trades-before',
    preflight=args.preflight, later_registers=['marshgate-chemical', 'alderson-rope'])
r = load('data/maps/jeffrey-glue-footprint-alignment.json')
scene = load('docs/data/factory-buildings.json')
prior = {b['id']: b for b in before['buildings']}
models = {b['id']: b for b in scene['buildings']}
assert {b['modelId']: b['sourceFid'] for b in r['retainedExistingMatches']} == retained
for ident, fid in retained.items():
    old, current = prior[ident], models[ident]
    assert old['sourceFootprintFid'] == current['sourceFootprintFid'] == fid
    assert old['footprint'] == current['footprint']
    if ident == 'site790-raw':
        assert old['renderPolygons'] == current['renderPolygons']
    for key in ['height', 'roofRise', 'roofAxis', 'roofBays', 'rotation']:
        assert old[key] == current[key], (ident, key)
assert not any(r.get(k) for k in ['additionalBuildings', 'removedBuildings',
    'mapTracedBuildings', 'locallyTransferredBuildings', 'removedStructures'])
rows = {c['modelId']: c for c in r['buildings']}
assert {c['modelId'] for c in r['renderChanges']} == {'site790-884'}
validate_render_changes(r['renderChanges'], before, scene, rows, args.preflight)
bodies = {ident: Polygon(c['worldFootprint'], c['worldHoles']) for ident, c in rows.items()}
groups = {g['id']: g for g in r['groups']}
western = groups['jeffrey-west-coppers']['divisionParameters']
assert western['attachedStairSourceFid'] == 749900
assert western['northernMainDepthFraction'] == 43/75
central = groups['jeffrey-central-process']['divisionParameters']
assert central['longitudinalWidths'] == [39, 67, 49]
assert central['middleDepths'] == [48, 33]
assert groups['jeffrey-central-process']['modelIds'] == ['site790-888', 'site790-890', 'site790-890s', 'site790-892']
assert bodies['site790-886'].intersection(bodies['site790-886s']).area < .001
for left, right in [('site790-888', 'site790-890'), ('site790-890', 'site790-890s'),
        ('site790-890', 'site790-892'), ('site790-896', 'site790-898'), ('site790-900', 'site790-902')]:
    assert bodies[left].distance(bodies[right]) < .002, (left, right)
assert bodies['site790-882'].distance(Polygon(prior['site790-884']['footprint'])) > .5

# Audit every saved register, including unintegrated companion authoring passes
# and structures/plants whose independent bases are not building group members.
all_used = {}
for path in sorted((ROOT / 'data/maps').glob('*footprint-alignment.json')):
    if path.name == 'jeffrey-glue-footprint-alignment.json':
        continue
    other = load(str(path.relative_to(ROOT)))
    for g in other.get('groups', other.get('buildings', [])):
        for fid in g.get('sourceFids', [g.get('sourceFid')]):
            if fid is not None:
                all_used.setdefault(fid, []).append(path.name)
    for key in ['structures', 'tanks', 'mappedPlants']:
        for plant in other.get(key, []):
            fids = plant.get('sourceFids', plant.get('sourceFootprintFids', []))
            fids = list(fids) + [plant.get('sourceFid'), plant.get('sourceFootprintFid')]
            for fid in fids:
                if fid is not None:
                    all_used.setdefault(fid, []).append(path.name)
own_fids = [fid for g in r['groups'] for fid in g['sourceFids']]
assert len(own_fids) == len(set(own_fids))
assert not set(own_fids).intersection(all_used), set(own_fids).intersection(all_used)
prior_structures = {s['id']: s for s in before['structures']}
actual_structures = {s['id']: s for s in scene['structures']}
others = [Polygon(b['footprint'], b.get('worldHoles', []))
          for b in scene['buildings'] if b['id'] not in expected]
streets, _ = street_clearances(load('data/maps/district-road-traces.json')['roads'])
water = unary_union([Polygon(p[0], p[1:]) for q in
    load('docs/data/ground-plan.json')['rivers'] + scene['westContext']['rivers'] for p in q['polygons']])
obstacles = unary_union(list(bodies.values()) + others + [streets, water])
assert len(r['structures']) == 2
assert {s['sourceFid'] for s in r['structures']} == {1154281, 1194922}
for s in r['structures']:
    old = prior_structures[s['id']]
    assert s['sourceFid'] not in all_used and s['sourceFid'] not in own_fids
    assert s['preservedHeight'] == old['height']
    assert s['priorRadius'] == old['radius'] and 0 < s['radius'] <= old['radius']
    centre = Point(s['centre'])
    base = unary_union([Polygon(p[0], p[1:]) for p in s['sourcePolygons']])
    halfside = s['radius']*1.2
    plinth = affinity.rotate(box(centre.x-halfside, centre.y-halfside,
        centre.x+halfside, centre.y+halfside), s['rotation'], origin=centre)
    assert base.covers(plinth), s['id']
    assert centre.distance(base.centroid) < .001
    assert plinth.intersection(obstacles).area < .001, s['id']
    if s['sourceFid'] == 1194922:
        assert old['mappedHeightFeet'] == 50
    else:
        assert 'mappedHeightFeet' not in old and old['height'] == 22
    if not args.preflight:
        current = actual_structures[s['id']]
        assert current['height'] == old['height'] and current['section'] == old['section']
        assert current['sourceFootprintFid'] == s['sourceFid']
        assert current['radius'] == s['radius'] and current['rotation'] == s['rotation']
        assert math.dist([current['x'], current['z']], s['centre']) < .001
deferred_fids = {fid for d in r['deferred'] for fid in d.get('sourceFids', [])}
assert {1062461, 1148002, 930555, 1081689, 1135005} <= deferred_fids
assert not deferred_fids.intersection(set(own_fids) | {s['sourceFid'] for s in r['structures']})
print('Jeffrey glue: Goad compartment cuts, open north yard, two existing matches, global source IDs, unchanged elevations and two contained square chimney plinths pass.')
