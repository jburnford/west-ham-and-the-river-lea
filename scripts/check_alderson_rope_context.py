"""Check the corrected OS lane against mapped rope and neighbouring roofs."""
from prepare_east_channelsea_context import prior_rivers
import argparse
import hashlib
import json
import math
from pathlib import Path

from shapely.geometry import LineString, Polygon
from factory_alignment_checks import load
from factory_map_sources import mosaic
from factory_street_clearance import street_clearances

parser = argparse.ArgumentParser()
parser.add_argument('--preflight', action='store_true')
args = parser.parse_args()
digest = lambda data: hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
r = load('data/maps/alderson-rope-context-alignment.json')
roads = load('data/maps/district-road-traces.json')['roads']
prior = load('data/maps/mill-brush-context-alignment.json')
north = next(q for q in roads if q['name'] == r['road']['name'])
west = next(q for q in roads if q['name'] == prior['road']['name'])
assert north['points'] == r['road']['points']
assert north['points'][:9] == prior['additionalRoad']['points'][:9]
assert r['road']['priorPoints'] == prior['additionalRoad']['points']
assert len(north['points']) == 14 and not north['bridgeSpans']
remaining=Path(__file__).resolve().parents[1]/'data/maps/remaining-trades-context-alignment.json'
expected_west=next(c for c in load('data/maps/remaining-trades-context-alignment.json')['roads'] if c['name']==west['name']) if remaining.exists() else prior['road']
if remaining.exists():
    assert expected_west['priorPoints']==prior['road']['points']
    assert expected_west['priorBridgeSpans']==prior['road']['priorBridgeSpans']
assert west['points']==expected_west['points'] and west['bridgeSpans']==expected_west.get('bridgeSpans',prior['road']['priorBridgeSpans'])
assert west['width'] == north['width'] == r['road']['width'] == 7
assert not north.get('buildingClearanceReviews')
assert sum(q['name'] == north['name'] for q in roads) == 1
_, world, pixel = mosaic(r['road']['reviewedSourceBounds'])
assert world(r['road']['reviewedSourcePixels']).round(3).tolist() == north['points'][9:]
_, _, source_pixel = mosaic(north['sourceBounds'])
assert source_pixel(north['points']).round(3).tolist() == north['sourcePixels']
scene = load('docs/data/factory-buildings.json')
assert digest(prior_rivers(load('docs/data/ground-plan.json')['rivers'],load('data/maps/east-channelsea-context-alignment.json'))) == r['retainedRiverGeometrySha256']['ground']
assert digest(scene['westContext']['rivers']) == r['retainedRiverGeometrySha256']['west']
streets, _ = street_clearances(roads)
line = LineString(north['points'])
models = {b['id']: b for b in scene['buildings']}
checked = []
for name in ['alderson-rope', 'marshgate-chemical', 'jeffrey-glue', 'mill-brush']:
    for b in load(f'data/maps/{name}-footprint-alignment.json')['buildings']:
        p = Polygon(b['worldFootprint'], b['worldHoles'])
        assert p.intersection(streets).area < .01, b['modelId']
        checked.append(b['modelId'])
for ident in ['site791-dry', 'site939-912', 'site939-926', 'site790-884', 'site790-raw']:
    b = models[ident]
    p = Polygon(b['footprint'], b.get('worldHoles', []))
    assert p.intersection(streets).area < .01, ident
    checked.append(ident)
dry = Polygon(models['site791-dry']['footprint'])
assert dry.distance(line) > 5.17
old_line = LineString(r['road']['priorPoints'])
before = load('reference/footprint-model-alignment/marshgate-trades-before.json')
for c in r['inheritedInkAlignmentLimits']:
    b = next(b for b in before['buildings'] if b['id'] == c['modelId'])
    p = Polygon(b['footprint'], b.get('worldHoles', []))
    assert c['evidence'] and c['priorOverlapAreaM2'] > 0
    assert abs(p.intersection(old_line.buffer(4.6, cap_style=2, join_style=2)).area-c['priorOverlapAreaM2']) < .000001
    assert abs(p.intersection(line.buffer(4.6, cap_style=2, join_style=2)).area-c['overlapAreaM2']) < .000001
if not args.preflight:
    infra = load('docs/data/infrastructure.json')
    for road in [west, north]:
        actual = next(q for q in infra['roads'] if q['name'] == road['name'])
        assert len(actual['route']) == len(road['points'])
        assert all(math.dist(a, b) < .008 for a, b in zip(actual['route'], road['points']))
print(f'Alderson context: 7 m OS lane and normal shoulder clear {len(checked)} mapped ranges; first nine controls, split, bridges and rivers retained; provisional ink limits documented.')
