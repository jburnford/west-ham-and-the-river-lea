"""Check reviewed Bow Brewery source coverage, open court and inferred chimney."""
import math
import sys

from shapely import affinity
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

from factory_alignment_checks import check_register, load

preflight = '--preflight' in sys.argv
expected = {f'west-259-{i}' for i in range(1, 8)}
check_register('bow-brewery', expected, 7, 0, 'mill-brush-brewery-before',
               preflight=preflight, later_registers=['mill-brush', 'mineral-water'])
r = load('data/maps/bow-brewery-footprint-alignment.json')
before = load('reference/footprint-model-alignment/mill-brush-brewery-before.json')
rows = {b['modelId']: b for b in r['buildings']}
shapes = {id: Polygon(b['worldFootprint'], b['worldHoles']) for id, b in rows.items()}
body = unary_union(list(shapes.values()))
assert body.distance(Point(r['retainedOpenCourt']['worldPoint'])) > 2
assert len(shapes['west-259-1'].interiors) == 1, 'Northeast small source hole filled'
assert not r.get('additionalBuildings') and not r.get('removedBuildings')
used = {f for g in r['groups'] for f in g['sourceFids']}
assert not used.intersection(r['excludedFrontage']['sourceFids'])
assert shapes['west-259-4'].distance(shapes['west-259-5']) > 10.4, 'Southern court bridged'
stack = r['structures'][0]
old = next(s for s in before['structures'] if s['id'] == stack['id'])
assert stack['preservedHeight'] == old['height'] == 30
assert stack['parentBuildingId'] == 'west-259-6'
assert 'sourceFid' not in stack, 'Inferred chimney mislabelled as mapped base'
centre = Point(stack['centre'])
half = old['radius'] * 1.2
plinth = affinity.rotate(box(centre.x-half, centre.y-half, centre.x+half, centre.y+half),
                        stack['rotation'], origin=centre)
assert shapes[stack['parentBuildingId']].covers(plinth)
if not preflight:
    scene = load('docs/data/factory-buildings.json')
    assert sum(b['siteId'] == 259 for b in scene['buildings']) == 7
    actual = next(s for s in scene['structures'] if s['id'] == stack['id'])
    assert math.dist([actual['x'], actual['z']], stack['centre']) < .001
    assert actual['parentBuildingId'] == stack['parentBuildingId']
    for key in ['height', 'radius', 'topRadiusRatio', 'section', 'material', 'baseHeight']:
        assert actual[key] == old[key], (stack['id'], key)
print('Bow Brewery: seven complete source exteriors, pale central court, excluded P.H. frontage, source hole and contained inferred chimney pass.')
