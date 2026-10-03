"""Check native replay, open grid topology, clearances and published context."""
import argparse
import json
import math

from shapely.geometry import LineString, Polygon, shape
from shapely.ops import unary_union

from factory_map_sources import mosaic
from prepare_victoria_stone_grid import BOUNDS, PIXELS
from victoria_stone_grid import ROOT, REGISTER, build_victoria_stone_grid


def read(path):
    return json.loads((ROOT / path).read_text())


def check(preflight=False):
    grid = build_victoria_stone_grid()
    assert json.dumps(grid, sort_keys=True) == json.dumps(build_victoria_stone_grid(), sort_keys=True)
    assert grid['register'] == REGISTER and grid['sourceFids'] == []
    assert grid['representation'] == 'ground-atlas-lines' and grid['addedHeight'] == 0
    assert 'interpreted' in grid['appearanceEvidence'] and 'not established' in grid['heightEvidence']
    assert grid['reviewedSourceBounds'] == BOUNDS and grid['reviewedSourcePixels'] == PIXELS
    _, world, _ = mosaic(BOUNDS)
    assert grid['worldNodes'] == [world(row).round(3).tolist() for row in PIXELS]
    assert (grid['rows'], grid['columns']) == (4, 5)
    assert len(grid['worldNodes']) == 5 and all(len(r) == 6 for r in grid['worldNodes'])
    assert len(grid['cells']) == 20 and len(grid['dividers']) == 49
    assert len({c['id'] for c in grid['cells']}) == 20
    assert len({d['id'] for d in grid['dividers']}) == 49
    body = Polygon(grid['worldOutline'])
    assert body.is_valid and 880 < body.area < 960
    assert abs(body.area - grid['areaM2']) < 1e-8
    cells = [Polygon(c['worldOutline']) for c in grid['cells']]
    assert all(c.is_valid and 30 < c.area < 65 for c in cells)
    assert all(c['open'] for c in grid['cells'])
    union = unary_union(cells)
    assert union.symmetric_difference(body).area < 1e-8
    assert abs(sum(c.area for c in cells) - union.area) < 1e-8
    edges = {}
    for c in grid['cells']:
        points = c['worldOutline']
        for a, b in zip(points, points[1:]+points[:1]):
            key = tuple(sorted((tuple(a), tuple(b))))
            edges[key] = edges.get(key, 0)+1
    actual = {tuple(sorted(map(tuple, d['points']))): d for d in grid['dividers']}
    assert set(actual) == set(edges) and len(actual) == 49
    assert sum(v == 1 for v in edges.values()) == 18
    assert sum(v == 2 for v in edges.values()) == 31
    assert all(actual[k]['exterior'] == (v == 1) for k, v in edges.items())
    assert all(5 < LineString(d['points']).length < 10 for d in grid['dividers'])
    assert all(math.isfinite(v) for row in grid['worldNodes'] for p in row for v in p)
    context = read('data/maps/east-channelsea-context-alignment.json')
    yard = next(y for y in context['additionalYards'] if y['id'] == grid['yardId'])
    assert body.difference(Polygon(yard['polygons'][0][0])).area < 1e-8
    source = read('reference/footprint-model-alignment/east-channelsea-source-shapes.json')
    assert not any(shape(g).intersects(body) for g in source.values())
    infra = read('docs/data/infrastructure.json')
    factories = read('docs/data/factory-buildings.json')
    plan = read('docs/data/ground-plan.json')
    buildings = unary_union([Polygon(b.get('worldFootprint', b['footprint']), b.get('worldHoles', []))
                            for b in factories['buildings']])
    roads = unary_union([LineString(r['route']).buffer(r['width']/2+.25, cap_style=2)
                         for r in infra['roads']])
    water = unary_union([Polygon(p[0], p[1:]) for r in plan['rivers']+
                         factories['westContext']['rivers'] for p in r['polygons']])
    tracks = read('docs/data/factory-yards.json')['tracks']
    trackmask = unary_union([LineString(t['points']).buffer(t.get('sleeperWidth', 1.8)/2+.15)
                            for t in tracks])
    bank = unary_union([Polygon([(x,z) for x,y,z in t]) for r in infra['railways']
                        for t in r['embankment']])
    for name, blocked in [('buildings', buildings), ('roads', roads), ('water', water),
                          ('sidings', trackmask), ('running-line banks', bank)]:
        assert body.intersection(blocked).area < 1e-6, name
    assert all((ROOT / image).exists() for image in grid['evidenceImages'])
    if not preflight:
        published = read('docs/data/factory-yards.json').get('workingGrids', [])
        assert [g for g in published if g['id'] == grid['id']] == [grid]
    print('Victoria Stone: 20 open OS cells, 49 unique boundaries, native replay, '
          'yard/building/road/water/rail clearances and byte-idempotence pass.' +
          (' Published context replay passes.' if not preflight else ''))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--preflight', action='store_true')
    check(parser.parse_args().preflight)
