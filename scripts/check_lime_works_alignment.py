"""Check lime rooms, separate kiln envelopes, prior profiles and local clearances."""
import math
import sys
from shapely.geometry import Polygon, Point, LineString
from shapely.ops import unary_union
from factory_alignment_checks import check_register, load

preflight='--preflight' in sys.argv
check_register('lime-works',{f'site255-os-{i}' for i in range(1,5)},4,0,
    'soap-wharves-before',preflight=preflight,later_registers=['cook-soap','bow-magnet'])
r=load('data/maps/lime-works-footprint-alignment.json')
scene=load('docs/data/factory-buildings.json')
body=unary_union([Polygon(b['worldFootprint'],b['worldHoles']) for b in r['buildings']])
water=unary_union([Polygon(p[0],p[1:]) for river in
    load('docs/data/ground-plan.json')['rivers']+scene['westContext']['rivers'] for p in river['polygons']])
roads=unary_union([LineString(q['points']).buffer(q['width']/2+1.1) for q in load('data/maps/district-road-traces.json')['roads']])
assert body.distance(Point(-950,132))>1, 'Old false shed across the yard survives'
assert len(r['mappedPlants'])==2
for c in r['mappedPlants']:
    actual=c if preflight else next(s for s in scene['structures'] if s['id']==c['id'])
    source=Polygon(c['sourcePolygons'][0][0])
    centre=Point(actual['x'],actual['z'])
    circle=centre.buffer(actual['radius'])
    assert centre.distance(source.centroid)<.001
    assert actual['kind']=='kiln' and actual['height']==c['priorStructure']['height']==7
    assert actual['sourceFootprintFid']==c['sourceFootprintFid']
    assert abs(math.pi*c['equalAreaRadius']**2-source.area)<.03
    assert 0<=centre.distance(source.boundary)-actual['radius']<.001
    assert circle.difference(source).area<.001
    for obstruction in [body,roads,water]:assert circle.intersection(obstruction).area<.001,actual['id']
    if not preflight:assert actual==c
a,b=r['mappedPlants']
assert math.dist([a['x'],a['z']],[b['x'],b['z']])>a['radius']+b['radius']+.1
assert len(r['mappedPlants'][1]['sourcePolygons'][0])==2, 'Lost mapped eastern kiln throat'
print('Lime works: four separate rooms, two contained kiln bodies, retained heights/throat evidence and clear yard pass.')
