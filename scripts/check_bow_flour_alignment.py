"""Focused saved/runtime Bow Flour geometry and inferred boiler-plant checks."""
import argparse
import math

from shapely.geometry import Point, Polygon
from factory_alignment_checks import check_register, load

parser = argparse.ArgumentParser()
parser.add_argument('--preflight', action='store_true')
args = parser.parse_args()
check_register('bow-flour', {f'west-422-{i}' for i in range(1, 7)}, 5, 0,
    'west-mills-before', preflight=args.preflight,
    scene_counts=(546, {422: 6}))
r = load('data/maps/bow-flour-footprint-alignment.json')
cs = {c['modelId']: c for c in r['buildings']}
boiler = Polygon(cs['west-422-6']['worldFootprint'], cs['west-422-6']['worldHoles'])
seam = next(g for g in r['groups'] if g['id'] == 'bow-flour-rear')['sourceReconciliation']
assert .18 < seam['removedAreaM2'] < .19
assert boiler.area > 83 and cs['west-422-6']['preservedHeight'] == 5.5
c = r['structures'][0]
assert c['id'] == 'west-422-6-stack' and c['preservedHeight'] == 32
old = next(s for s in load('reference/footprint-model-alignment/west-mills-before.json')['structures'] if s['id'] == c['id'])
assert old['radius'] == 1.25 and boiler.covers(Point(c['centre']).buffer(old['radius']*1.2))
if not args.preflight:
    stack = next(s for s in load('docs/data/factory-buildings.json')['structures'] if s['id'] == c['id'])
    assert stack['height'] == 32 and stack['radius'] == old['radius']
    assert stack['parentBuildingId'] == 'west-422-6' and 'sourceFootprintFid' not in stack
    assert math.dist([stack['x'], stack['z']], c['centre']) < .001
print('Bow Flour: complete low north tip, recorded source seam and contained inferred chimney pass.')
