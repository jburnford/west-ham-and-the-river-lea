"""Check local bank/road reconciliation and preserve unrelated controls."""
import math
from shapely.geometry import Polygon, LineString, Point
from factory_alignment_checks import load
from factory_street_clearance import street_clearances

context=load('data/maps/bow-magnet-context-alignment.json')
roads=load('data/maps/district-road-traces.json')['roads']
for correction in context['roads']:
    road=next(r for r in roads if r['name']==correction['name'])
    assert road['points']==correction['points'] and road['width']==correction['width']
    assert road['bridgeSpans']==correction['bridgeSpans']
    if road['name']=='Stratford High Street':
        assert road['points'][:2]==correction['priorPoints'][:2]
        assert road['points'][4:]==correction['priorPoints'][3:]
        assert LineString(correction['priorPoints'][2:4]).distance(Point(road['points'][3]))<.000001
        assert road['bridgeSpans']==correction['priorBridgeSpans']
    else:
        assert road['points'][:10]==correction['priorPoints'][:10]
        bridge=road['bridgeSpans'][0]
        assert bridge['provisional'] and bridge['height']==1.5
        assert LineString(bridge['points']).difference(LineString(road['points']).buffer(.001)).length<.001
    actual=next(r for r in load('docs/data/infrastructure.json')['roads'] if r['name']==road['name'])
    assert all(math.dist(a,b)<.008 for a,b in zip(actual['route'],road['points']))

bank=load('data/maps/bow-magnet-bank-alignment.json')
river=next(r for r in load('docs/data/ground-plan.json')['rivers'] if r['id']==17)
prior=next(r for r in load('reference/footprint-model-alignment/soap-wharves-ground-before.json')['rivers'] if r['id']==17)
ring=river['polygons'][0][0]
old=prior['polygons'][0][0]
changes={c['vertex']:c for c in bank['replacements']}
for i,p in enumerate(ring):
    assert p==(changes[i]['point'] if i in changes else old[i])
water=Polygon(ring)
assert water.is_valid
retained=next(r for r in load('docs/data/ground-plan.json')['rivers'] if r['id']==22)
assert all(water.intersection(Polygon(p[0],p[1:])).area<.001 for p in retained['polygons'])
for z in [-60,-30,0,50,75]:
    assert water.intersection(LineString([(-1060,z),(-920,z)])).length>12
streets,_=street_clearances(roads)
for b in load('data/maps/bow-magnet-footprint-alignment.json')['buildings']:
    p=Polygon(b['worldFootprint'],b['worldHoles'])
    assert p.intersection(water.buffer(.12)).area<.01,b['modelId']
    assert p.intersection(streets).area<.01,b['modelId']
assert LineString(bridge['points']).intersection(water).length>10
assert water.distance(Point(bridge['points'][-1]))>2
print('Bow/Magnet context: mapped exteriors clear, opposite bank/earlier roads preserved, channel open and provisional crossing connected.')
