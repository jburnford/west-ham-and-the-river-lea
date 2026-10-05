"""Verify the mapped streets, preserved context and explicit roof clipping effects."""
from prepare_east_channelsea_context import prior_rivers
import argparse
import hashlib
import json
import math
from pathlib import Path

from shapely.geometry import LineString, Point, Polygon, shape
from shapely.ops import unary_union

from factory_alignment_checks import load, ROOT
from factory_map_sources import mosaic
from factory_street_clearance import street_clearances

digest = lambda data: hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def check(preflight=False):
    register = load('data/maps/remaining-trades-context-alignment.json')
    prior = load(register['baseline'])
    assert digest(prior) == register['baselineSha256']
    roads = load('data/maps/district-road-traces.json')
    actual = {r['name']:r for r in roads['roads']}
    old = {r['name']:r for r in prior['roads']}
    changed = {r['name'] for r in register['roads']}
    eastern=load('data/maps/east-channelsea-context-alignment.json')['road']['preparedRoad']
    assert actual[eastern['name']]==eastern
    assert set(actual) == set(old)|{eastern['name']}
    for name in set(actual)-changed-{eastern['name']}:
        assert actual[name] == old[name], name
    for correction in register['roads']:
        road = actual[correction['name']]
        assert road['points'] == correction['points']
        assert road['width'] == correction['width'] == 7
        assert correction['ordinaryShoulderWidth'] == 1.1
        assert road['bridgeSpans'] == correction['bridgeSpans']
        assert road.get('buildingClearanceReviews',[]) == old[road['name']].get('buildingClearanceReviews',[])
        retained = {k:v for k,v in road.items() if k not in ['points','sourcePixels','bridgeSpans','remainingTradesContextAlignment']}
        expected = {k:v for k,v in old[road['name']].items() if k not in ['points','sourcePixels','bridgeSpans','remainingTradesContextAlignment']}
        assert retained == expected
        _, world, _ = mosaic(correction['reviewedSourceBounds'])
        traced = world(correction['reviewedSourcePixels']).round(3).tolist()
        _, _, pixel = mosaic(road['sourceBounds'])
        assert pixel(road['points']).round(3).tolist() == road['sourcePixels']
        bridge = road['bridgeSpans'][0]
        previous_bridge = correction['priorBridgeSpans'][0]
        # T22 re-levelled Three Mills Bridge to its OS spot height; the prior estimated height is kept as priorHeight.
        relevel = ['points','evidence','height','priorHeight','heightEvidence']
        assert {k:v for k,v in bridge.items() if k not in relevel} == {k:v for k,v in previous_bridge.items() if k not in relevel}
        assert bridge.get('priorHeight', bridge['height']) == previous_bridge['height']
        if road['name'] == 'Marshgate Lane':
            assert road['points'][:-2] == traced
            assert road['points'][-2:] == correction['priorPoints'][-2:]
            assert bridge['points'] == road['points'][2:5]
            assert LineString(bridge['points']).difference(LineString(road['points']).buffer(.001)).length < .001
            mill = load('data/maps/mill-brush-context-alignment.json')
            assert correction['priorPoints'] == mill['road']['points']
            assert correction['priorBridgeSpans'] == mill['road']['priorBridgeSpans']
        else:
            assert road['points'][3:5] == traced
            assert road['points'][:3] == correction['priorPoints'][:3]
            assert road['points'][5:] == correction['priorPoints'][5:]
            assert Point(bridge['points'][0]).distance(LineString(road['points'][3:5])) < .001
            assert bridge['points'][1:] == previous_bridge['points'][1:]
    streets, overrides = street_clearances(roads['roads'])
    previous_streets, previous_overrides = street_clearances(prior['roads'])
    mapped_count = 0
    for path in sorted((ROOT/'data/maps').glob('*-footprint-alignment.json')):
        alignment = json.loads(path.read_text())
        for key in ['buildings','mapTracedBuildings','additionalBuildings','locallyTransferredBuildings']:
            for row in alignment.get(key,[]):
                if not row.get('modelId'):
                    continue
                ident = row['modelId']
                p = Polygon(row['worldFootprint'],row.get('worldHoles',[]))
                old_area = p.intersection(previous_overrides.get(ident,previous_streets)).area
                area = p.intersection(overrides.get(ident,streets)).area
                # Earlier clear mapped roofs must stay clear. Existing unrelated
                # pinches stay within their recorded earlier exclusion amount.
                assert area < max(.01,old_area+.001), (ident,old_area,area)
                if path.name in ['crown-johnson-footprint-alignment.json','western-trades-footprint-alignment.json','mill-brush-footprint-alignment.json']:
                    assert area < .01, (ident,area)
                mapped_count += 1
    source = load('reference/footprint-model-alignment/remaining-trades-source-shapes.json')
    shed = shape(source['30174'])
    assert shed.intersection(streets).area < .001
    assert shed.distance(LineString(actual['Three Mills Lane']['points'])) > 4.6
    before = load('reference/footprint-model-alignment/remaining-trades-before.json')
    effects = []
    for row in before['buildings']:
        p = Polygon(row['footprint'],row.get('worldHoles',[]))
        ident = row['id']
        a = p.intersection(previous_overrides.get(ident,previous_streets)).area
        z = p.intersection(overrides.get(ident,streets)).area
        if abs(a-z) > .01:
            effects.append(dict(modelId=ident,priorRoadExclusionAreaM2=a,roadExclusionAreaM2=z,changeAreaM2=z-a))
    assert effects == register['priorSceneRoadExclusionEffects']
    assert all(r['changeAreaM2'] < 0 for r in effects), 'No new exclusion of an unreviewed neighbour'
    ground = load('docs/data/ground-plan.json')
    scene = load('docs/data/factory-buildings.json')
    assert digest(prior_rivers(ground['rivers'],load('data/maps/east-channelsea-context-alignment.json'))) == register['retainedRiverGeometrySha256']['ground']
    assert digest(scene['westContext']['rivers']) == register['retainedRiverGeometrySha256']['west']
    water = unary_union([Polygon(p[0],p[1:]) for r in ground['rivers']+scene['westContext']['rivers'] for p in r['polygons']])
    for correction in register['roads']:
        bridge = correction['bridgeSpans'][0]
        assert LineString(bridge['points']).intersection(water).length > 5
        if correction['name'] == 'Marshgate Lane':
            assert all(Point(p).distance(water) > 5 for p in [bridge['points'][0],bridge['points'][-1]])
        if not preflight:
            built = next(r for r in load('docs/data/infrastructure.json')['roads'] if r['name'] == correction['name'])
            assert len(built['route']) == len(correction['points'])
            assert all(math.dist(a,b) < .008 for a,b in zip(built['route'],correction['points']))
    assert all((ROOT/p).exists() for p in register['evidenceImages'])
    print(f'Remaining-trades context: Crown/Johnson and shed clear; {mapped_count} mapped roof checks, both existing crossings, mill split, untouched roads and rivers pass; {len(effects)} prior roof exclusions reduced.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--preflight',action='store_true')
    check(parser.parse_args().preflight)
