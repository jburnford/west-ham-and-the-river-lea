"""Check corrected road, bridge and bank against the mill and wharf exteriors."""
import math
from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union
from factory_alignment_checks import load
from factory_street_clearance import street_clearances

register=load('data/maps/bow-flour-context-alignment.json')
roads=load('data/maps/district-road-traces.json')['roads']
road=next(r for r in roads if r['name']==register['road']['name'])
prior=register['road']
later=load('data/maps/bow-magnet-context-alignment.json')['roads'][0]
assert later['priorPoints'][2:]==prior['priorPoints'][2:]
assert road['points']==later['points'] and road['width']==12
assert road['points'][:2]==[[round(x+5.7,3),round(z+7,3)] for x,z in prior['priorPoints'][:2]]
assert road['bridgeSpans'][1:]==prior['priorBridgeSpans'][1:]
bridge=road['bridgeSpans'][0]
oldbridge=prior['priorBridgeSpans'][0]
assert math.isclose(math.dist(*bridge['points']),math.dist(*oldbridge['points']),abs_tol=.001)
line=LineString(road['points'])
assert line.buffer(2).covers(LineString(bridge['points'])), 'Bridge leaves the corrected carriageway'
streets,_=street_clearances(roads)
alignment=load('data/maps/bow-flour-footprint-alignment.json')
buildings={b['modelId']:Polygon(b['worldFootprint'],b['worldHoles']) for b in alignment['buildings']}
for id,p in buildings.items():assert p.distance(streets)>.08,(id,'road frontage')
context=load('data/maps/factory-west-context.json')
river=next(r for r in context['rivers'] if r['id']==register['bank']['riverId'])
ring=river['polygons'][0][0]
water=Polygon(ring)
assert water.is_valid
assert buildings['west-422-4'].distance(water)>.4
for c in register['bank']['replacements']:
    assert ring[c['vertex']]==c['point']
    assert math.dist(c['point'],c['priorPoint'])==2
oldring=[list(p) for p in ring]
for c in register['bank']['replacements']:oldring[c['vertex']]=c['priorPoint']
oldwater=Polygon(oldring)
assert water.difference(oldwater).area<.001
assert 0<oldwater.area-water.area<100
for x in [-1110,-1100,-1090,-1085]:
    assert water.intersection(LineString([(x,30),(x,90)])).length>24, 'Wharf channel pinched'
scene=load('docs/data/factory-buildings.json')
runtime=next(r for r in scene['westContext']['rivers'] if r['id']==river['id'])
assert runtime==river
infra=load('docs/data/infrastructure.json')
route=next(r for r in infra['roads'] if r['name']==road['name'])
assert len(route['route'])==len(road['points'])
assert all(math.dist(a,b)<.008 for a,b in zip(route['route'],road['points']))
print('Bow Flour context: intact 12 m road/bridge, clear mapped façades, local wharf-bank correction and open channel pass.')
