"""Check rubber/felt source coverage, courts and retained/removal evidence."""
import math
import sys
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
from factory_alignment_checks import check_register, load

IDS = {'west-423-1', 'west-423-2', 'west-423-2-northwest',
       'west-424-1', 'west-424-2', 'west-424-3'}
preflight = '--preflight' in sys.argv
check_register('rubber-felt', IDS, 6, 0, 'west-mills-before',
               preflight=preflight, later_registers=['bow-flour'])
r = load('data/maps/rubber-felt-footprint-alignment.json')
before = load('reference/footprint-model-alignment/west-mills-before.json')
old_models = {b['id']: b for b in before['buildings']}
rows = {b['modelId']: b for b in r['buildings']}
shapes = {id: Polygon(b['worldFootprint'], b['worldHoles']) for id, b in rows.items()}
body = unary_union(list(shapes.values()))
court = Polygon(old_models['west-423-1']['footprint']).centroid
assert body.distance(court) > 14, 'Former manufacturing court filled'
assert not body.covers(Point(-1202, 104)), 'Western felt recess filled'
assert shapes['west-424-1'].distance(shapes['west-424-2']) > 5.46, 'Felt middle court closed'
assert .69 < shapes['west-423-2'].distance(shapes['west-423-2-northwest']) < .70
assert len(r['additionalBuildings']) == 1
assert {b['id'] for b in r['removedBuildings']} == {'west-423-3', 'west-423-5'}
assert {s['id'] for s in r['removedStructures']} == {'west-423-process-stack'}
for key in ['removedBuildings', 'removedStructures']:
    originals = {b['id']: b for b in before['buildings' if key == 'removedBuildings' else 'structures']}
    for b in r[key]:
        assert b['review']
        assert all(b[k] == v for k, v in originals[b['id']].items()), 'Lost prior record'
stack = r['structures'][0]
old_stack = next(s for s in before['structures'] if s['id'] == stack['id'])
assert stack['preservedHeight'] == old_stack['height'] == 24
assert shapes[stack['parentBuildingId']].covers(Point(stack['centre']).buffer(old_stack['radius'] * 1.2))
assert 'sourceFid' not in stack, 'Inferred chimney mislabelled as mapped base'
if not preflight:
    scene = load('docs/data/factory-buildings.json')
    for site, count in [(423, 3), (424, 3)]:
        assert sum(b['siteId'] == site for b in scene['buildings']) == count
    for key, runtime in [('removedBuildings', 'reclassifiedFeatures'),
                         ('removedStructures', 'reclassifiedStructures')]:
        for removed in r[key]:
            assert next(b for b in scene[runtime] if b.get('id') == removed['id']) == removed
    actual = next(s for s in scene['structures'] if s['id'] == stack['id'])
    assert math.dist([actual['x'], actual['z']], stack['centre']) < .001
    assert actual['radius'] == old_stack['radius'] and actual['height'] == 24
    for key in ['topRadiusRatio', 'section', 'material', 'baseHeight']:
        assert actual[key] == old_stack[key]
print('Rubber/felt: six mapped ranges, open courts/division, complete domestic removal records and contained inferred 24 m chimney pass.')
