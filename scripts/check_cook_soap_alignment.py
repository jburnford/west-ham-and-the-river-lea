"""Cook source coverage, retained elevations, courts and actual square plinths."""
import argparse
import math
from shapely import affinity
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union
from factory_alignment_checks import check_register, load
from factory_street_clearance import street_clearances

parser = argparse.ArgumentParser()
parser.add_argument('--preflight', action='store_true')
args = parser.parse_args()
before = load('reference/footprint-model-alignment/soap-wharves-before.json')
expected = {b['id'] for b in before['buildings'] if b['siteId']==796}
check_register('cook-soap',expected,21,0,'soap-wharves-before',preflight=args.preflight,
    later_registers=['bow-magnet','lime-works'],scene_counts=(545,{796:31}))
r = load('data/maps/cook-soap-footprint-alignment.json')
rows = {c['modelId']:c for c in r['buildings']}
bodies = {id:Polygon(c['worldFootprint'],c['worldHoles']) for id,c in rows.items()}
assert len(bodies['cook-engines'].interiors)==0
# The Mabbers court is open to the road: an exterior notch, not a hole.
assert bodies['cook-engines'].convex_hull.area-bodies['cook-engines'].area>20
assert len(unary_union([bodies['cook-manure-shed'],bodies['cook-mechanics'],bodies['cook-tallow']]).interiors)==2
assert {c['id'] for c in r['structures']} == {s['id'] for s in before['structures'] if s.get('siteId')==796}
old = {s['id']:s for s in before['structures']}
scene = load('docs/data/factory-buildings.json')
current = {s['id']:s for s in scene['structures']}
streets,_ = street_clearances(load('data/maps/district-road-traces.json')['roads'])
water = unary_union([Polygon(p[0],p[1:]) for q in load('docs/data/ground-plan.json')['rivers']+scene['westContext']['rivers'] for p in q['polygons']])
others = [Polygon(b['footprint'],b.get('worldHoles',[])) for b in scene['buildings'] if b['id'] not in expected]
for c in r['structures']:
    prior = old[c['id']]
    assert c['preservedHeight']==prior['height']
    radius=c.get('radius',prior['radius'])
    centre=Point(c['centre'])
    plinth=affinity.rotate(box(centre.x-radius*1.2,centre.y-radius*1.2,
        centre.x+radius*1.2,centre.y+radius*1.2),c['rotation'],origin=centre)
    if 'sourceFid' in c:
        source=unary_union([Polygon(p[0],p[1:]) for p in c['sourcePolygons']])
        assert source.covers(plinth),c['id']
        assert centre.distance(source.centroid)<.001
        assert not any(c['sourceFid'] in g['sourceFids'] for g in r['groups'])
        assert plinth.intersection(unary_union(list(bodies.values()))).area<.001,c['id']
    else:
        assert c['parentBuildingId']=='cook-export'
        assert bodies[c['parentBuildingId']].covers(plinth)
        assert prior['mappedHeightFeet']==50 and radius==prior['radius']
    assert plinth.intersection(unary_union(others+[water,streets])).area<.001,c['id']
    if not args.preflight:
        actual=current[c['id']]
        assert actual['height']==prior['height'] and actual['section']==prior['section']
        assert actual['radius']==radius
        assert math.dist([actual['x'],actual['z']],c['centre'])<.001
        if 'sourceFid' in c:assert actual['sourceFootprintFid']==c['sourceFid']
        else:assert 'sourceFootprintFid' not in actual
assert r['structures'][0]['preservedHeight']==36.576
assert r['structures'][1]['radius']==.46 and r['structures'][2]['radius']==.58
print('Cook: all 31 ranges retain elevations; two enclosed openings, the open court and three mapped chimney bases stay open; four square plinths fit their reviewed positions.')
