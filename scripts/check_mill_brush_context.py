"""Check mapped approach separation, unchanged streams and brewery frontage."""
import math
from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union
from factory_alignment_checks import load
from factory_street_clearance import street_clearances

r=load('data/maps/mill-brush-context-alignment.json')
roads=load('data/maps/district-road-traces.json')['roads']
west=next(q for q in roads if q['name']==r['road']['name'])
north=next(q for q in roads if q['name']==r['additionalRoad']['name'])
from pathlib import Path
remaining=Path(__file__).resolve().parents[1]/'data/maps/remaining-trades-context-alignment.json'
expected_west=next(c for c in load('data/maps/remaining-trades-context-alignment.json')['roads'] if c['name']==west['name']) if remaining.exists() else r['road']
if remaining.exists():
    assert expected_west['priorPoints']==r['road']['priorPoints'][:7]
    assert expected_west['priorBridgeSpans']==r['road']['priorBridgeSpans']
assert west['points']==expected_west['points']
assert west['bridgeSpans']==expected_west.get('bridgeSpans',r['road']['priorBridgeSpans'])
later=Path(__file__).resolve().parents[1]/'data/maps/alderson-rope-context-alignment.json'
expected_north=load('data/maps/alderson-rope-context-alignment.json')['road']['points'] if later.exists() else r['additionalRoad']['points']
assert north['points']==expected_north and not north['bridgeSpans']
assert west['width']==north['width']==7
assert r['additionalRoad']['points'][7:]==r['road']['priorPoints'][11:]
assert north['points'][:9]==r['additionalRoad']['points'][:9]
assert sum(q['name']==north['name'] for q in roads)==1
street,frontages=street_clearances(roads)
for b in load('data/maps/mill-brush-footprint-alignment.json')['buildings']:
    assert Polygon(b['worldFootprint'],b['worldHoles']).intersection(street).area<.01,b['modelId']
prior=load('reference/footprint-model-alignment/mill-brush-brewery-ground-before.json')
assert load('docs/data/ground-plan.json')['rivers']==prior['rivers'], 'Water heads moved despite millrace/overhang evidence'
infra=load('docs/data/infrastructure.json')
for road in [west,north]:
    actual=next(q for q in infra['roads'] if q['name']==road['name'])
    assert len(actual['route'])==len(road['points'])
    assert all(math.dist(a,b)<.008 for a,b in zip(actual['route'],road['points']))
brew=load('data/maps/bow-brewery-frontage-alignment.json')
high=next(q for q in roads if q['name']==brew['road'])
assert high['width']==12
review=next(q for q in high['buildingClearanceReviews'] if q['id']==brew['id'])
assert review['shoulderWidth']==.78 and review['modelIds']==['west-259-2']
b=next(b for b in load('data/maps/bow-brewery-footprint-alignment.json')['buildings'] if b['modelId']=='west-259-2')
p=Polygon(b['worldFootprint'],b['worldHoles'])
assert 6.787<p.distance(LineString(high['points']))<6.789
assert p.intersection(frontages[b['modelId']]).area<.001
assert .59<p.intersection(street).area<.61
print('Mill/brush context: separate clear approaches, unchanged water heads and brewery pavement pinch pass.')
