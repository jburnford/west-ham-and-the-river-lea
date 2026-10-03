"""Check GIS route coverage, exact rendered joins and the OS low-level passage."""
import argparse
import hashlib
import json
import math
from pathlib import Path

from shapely.geometry import LineString, Point, Polygon, shape
from shapely.ops import unary_union

from north_london_connection import (FEATURE_IDS, IDENT, REGISTER,
    apply_mainline_crossing, build_north_london_connection, parts, project_gis, read)

ROOT = Path(__file__).resolve().parents[1]


def run(preflight=False):
    raw = read(REGISTER)
    infra = read('docs/data/infrastructure.json')
    scene = read('docs/data/factory-buildings.json')
    ground = read('docs/data/ground-plan.json')
    old = next(r for r in infra['railways'] if r.get('id') == raw['join']['railwayId'])
    water = unary_union([Polygon(p[0],p[1:]) for r in ground['rivers']+scene['westContext']['rivers'] for p in r['polygons']])
    prior_main = next(r for r in infra['railways'] if r.get('detailedMainline'))
    base_water = water
    water = water.union(unary_union([Polygon(p[0],p[1:]) for p in prior_main['northernWater']]))
    roads = unary_union([LineString(r['route']).buffer(r['width']/2) for r in infra['roads']])
    buildings = unary_union([Polygon(p['outer'],p['holes']) for b in scene['buildings'] for p in b['renderPolygons']])
    if preflight:
        railway = build_north_london_connection(water,roads,buildings,old)
        if prior_main.get('mainlineExtension'):
            from great_eastern import build_great_eastern
            prior_main = build_great_eastern(base_water,roads,buildings,ground['neighbourhood']['sewer'])
        main = apply_mainline_crossing(prior_main,railway,water,roads,buildings)
    else:
        railway = next(r for r in infra['railways'] if r.get('id') == IDENT)
        main = prior_main
    assert railway['railFeatureIds'] == FEATURE_IDS
    assert railway['register'] == REGISTER and railway['detailedRailway']
    assert raw['junction']['status'] == 'native-reviewed-underpass'
    assert raw['sourceSha256'] == hashlib.sha256((ROOT/'docs/maps/data/Rail_1895.geojson').read_bytes()).hexdigest()
    features = {f['id']:f for f in read('docs/maps/data/Rail_1895.geojson')['features']}
    for fid, coords in zip(FEATURE_IDS,raw['sourcePolylines']):
        assert LineString(coords).equals_exact(project_gis(shape(features[fid]['geometry'])),.000001)
    line = LineString(railway['route']); reference = LineString(raw['referenceRoute'])
    deviation = line.hausdorff_distance(reference)
    assert deviation < 12, f'Route leaves approximate GIS alignment: {deviation:.3f}m'
    assert abs(railway['route'][0][0]+1700) < .001
    assert line.is_simple and all(math.isfinite(v) for s in railway['stations'] for v in s)
    grades = [abs(b[2]-a[2])/(b[5]-a[5]) for a,b in zip(railway['stations'],railway['stations'][1:])]
    assert max(grades) < .015
    end = railway['stations'][-1]; join = old['stations'][railway['join']['stationIndex']]
    assert end[:5] == join[:5]
    # Compare actual 3D rail headers, including both rails of both tracks.
    for offset in [-1.8-.7175,-1.8+.7175,1.8-.7175,1.8+.7175]:
        a=[end[0]+end[3]*offset,end[2]+.46,end[1]+end[4]*offset]
        b=[join[0]+join[3]*offset,join[2]+.46,join[1]+join[4]*offset]
        assert math.dist(a,b) < .000001
    assert LineString(railway['route']).buffer(railway['crestHalfWidth'],cap_style=2).intersection(buildings).area < .01
    source_water = unary_union([Polygon(p[0],p[1:]) for p in raw['northernWaterContext']])
    extra = unary_union([Polygon(p[0],p[1:]) for p in railway['northernWater']])
    assert extra.intersection(water).area < .001
    assert extra.symmetric_difference(source_water.difference(water)).area < .01
    earth = unary_union([Polygon([(p[0],p[2]) for p in tri]) for tri in railway['embankment']])
    assert earth.intersection(water.union(extra).union(roads)).area < .01
    extension = main['mainlineExtension']; saved = raw['mainlineExtension']
    assert extension['register'] == REGISTER and extension['railFeatureId'] == 'way/198781682'
    assert main['route'][:len(saved['priorRoute'])] == saved['priorRoute']
    assert main['stations'][:len(saved['priorStations'])] == saved['priorStations']
    assert len(main['route']) > len(saved['priorRoute'])
    assert 60 < extension['extensionLength'] < 100
    assert LineString(saved['sourcePolyline']).equals_exact(project_gis(shape(features['way/198781682']['geometry'])),.000001)
    add = LineString([saved['priorRoute'][-1],*extension['addedRoute']])
    source_main = LineString(saved['sourcePolyline'])
    prior_offset = Point(saved['priorRoute'][-1]).distance(source_main)
    assert abs(extension['priorEndpointGisOffset']-prior_offset) < .000001
    assert max(Point(p).distance(source_main) for p in add.coords) <= prior_offset+.1
    assert Point(add.coords[-1]).distance(source_main) < .001
    assert extension['minimumRailheadToSoffit'] >= 4.39-.0001
    passage = unary_union([Polygon(p[0],p[1:]) for p in extension['underpassPolygon']])
    assert passage.difference(Point(extension['crossingPoint']).buffer(70.001)).area < .001
    upper_earth = unary_union([Polygon([(p[0],p[2]) for p in tri]) for tri in main['embankment']])
    assert upper_earth.intersection(passage).area < .01
    cross_d = LineString(main['route']).project(Point(extension['crossingPoint']))
    bridges = [b for b in main['bridges'] if b['start'] < cross_d < b['end']]
    assert len(bridges)==1 and bridges[0]['end']-bridges[0]['start'] > 10
    assert bridges[0]['end'] < main['stations'][-1][5], 'GE bridge ends at old clipped route boundary'
    assert extension['addedUnderpassAbutmentEdges'], 'Missing underpass earth-cut closure'
    assert all(pair in main['retainingEdges'] for pair in extension['addedUnderpassAbutmentEdges'])
    for a,b in main['retainingEdges']:
        assert LineString([(a[0],a[2]),(b[0],b[2])]).intersection(passage.buffer(-.001)).length < .001
    print(f'{IDENT}: {line.length:.1f}m connected route; maximum GIS deviation{deviation:.2f}m, grade{max(grades)*100:.2f}%; exact4rail-head join; {extension["extensionLength"]:.1f}m GE append with intact original prefix and4.39m interpreted underpass clearance'+(' (authoring preflight).' if preflight else ' (published).'))


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--preflight',action='store_true')
    run(parser.parse_args().preflight)
