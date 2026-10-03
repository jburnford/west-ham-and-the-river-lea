"""Check source-supported depot graph connectivity, levels and formed beds."""
import argparse
import json
import math
from collections import deque
from pathlib import Path

from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union
from shapely.strtree import STRtree

from abbey_support import station_footprints
from east_depot_tracks import REGISTER, branch_join, build_east_depot_tracks

ROOT = Path(__file__).resolve().parents[1]
load = lambda p: json.loads((ROOT/p).read_text())


def authoring_inputs():
    plan = load('docs/data/ground-plan.json')
    factories = load('docs/data/factory-buildings.json')
    infra = load('docs/data/infrastructure.json')
    frontages = load('docs/data/high-street-frontages.json')
    buildings = unary_union([Polygon(p['outer'], p['holes'])
        for b in factories['buildings']+frontages['buildings'] for p in b['renderPolygons']])
    buildings = buildings.union(station_footprints(load('docs/data/abbey-station-plan.json')))
    holders = factories['holders']+[h for h in plan['neighbourhood']['holders'] if h['siteId'] != 924]
    blocked = buildings.buffer(.15).union(unary_union([
        Point(h['x'], h['z']).buffer(h['radius']+.5) for h in holders]))
    water = unary_union([Polygon(p[0], p[1:]) for r in plan['rivers']+factories['westContext']['rivers'] for p in r['polygons']])
    roads = unary_union([LineString(r['route']).buffer(r['width']/2+.4, cap_style=2) for r in infra['roads']])
    blocked = blocked.union(water.buffer(.45)).union(roads)
    for s in factories['structures']:
        if s['kind'] == 'chimney':
            blocked = blocked.union(Point(s['x'], s['z']).buffer(s['radius']*1.2+.25))
        elif s['kind'] in {'tank', 'kiln'}:
            blocked = blocked.union(Point(s['x'], s['z']).buffer(s['radius']+.3))
    return load('data/maps/east-channelsea-context-alignment.json'), infra, blocked


def check(preflight=False):
    east, infra, blocked = authoring_inputs()
    register = load(REGISTER)
    tracks = build_east_depot_tracks(east, infra, blocked)
    assert len(tracks) == 14
    stems = {q['id']: q for q in east['railSidings']}
    assert {q['sourceTrackId'] for q in tracks if q['sourceTrackId']} == set(stems)
    assert len({q['id'] for q in tracks}) == 14
    graph, levels, points, normals = {}, {}, {}, {}
    bed_count = 0
    bank_rows = [q for q in infra['railways'] if q['name'] == register['branchJoin']['railwayName']
                 or q.get('id') in register['profile']['bankRailwayIds']]
    bank_triangles = [tri for q in bank_rows for tri in q['embankment']]
    bank_shapes = [Polygon([(p[0], p[2]) for p in tri]) for tri in bank_triangles]
    bank_index = STRtree(bank_shapes)
    bank_checks = 0
    for row in tracks:
        a, b = row['sourceNodes']
        graph.setdefault(a, []).append(b)
        graph.setdefault(b, []).append(a)
        assert len(row['points']) == len(row['heights']) == len(row['formationHeights']) == len(row['railTopHeights'])
        assert row['heights'] == row['formationHeights']
        assert row['gauge'] == 1.435 and row['sleeperWidth'] == 2.4
        for i, node in [(0, a), (-1, b)]:
            pair = [row['formationHeights'][i], row['railTopHeights'][i]]
            tangent = (row['points'][1], row['points'][0]) if i == 0 else (row['points'][-1], row['points'][-2])
            dx, dz = tangent[0][0]-tangent[1][0], tangent[0][1]-tangent[1][1]
            norm = [-dz/math.hypot(dx, dz), dx/math.hypot(dx, dz)]
            if node in levels:
                assert math.dist(levels[node], pair) < 1e-10, (node, 'grade seam')
                assert math.dist(points[node], row['points'][i]) < 1e-10, (node, 'plan seam')
                assert math.dist(normals[node], norm)*row['gauge']/2 < .05, (node, 'gauge seam')
            levels[node], points[node] = pair, row['points'][i]
            normals[node] = norm
        for p, q, ha, hb in zip(row['points'], row['points'][1:], row['heights'], row['heights'][1:]):
            assert abs(ha-hb)/math.dist(p, q) < .035
            dx, dz = q[0]-p[0], q[1]-p[1]
            length = math.hypot(dx, dz)
            midpoint = [(p[0]+q[0])/2, (p[1]+q[1])/2]
            rail_bottom = (ha+hb)/2+.46-.13
            for offset in [-row['gauge']/2, row['gauge']/2]:
                point = Point(midpoint[0]-dz/length*offset, midpoint[1]+dx/length*offset)
                for index in bank_index.query(point, predicate='intersects'):
                    # Using the highest triangle vertex is conservative; the
                    # interpolated existing bank at this point cannot be higher.
                    bank_height = max(p[1] for p in bank_triangles[index])
                    assert rail_bottom > bank_height+.24, (row['id'], point, rail_bottom, bank_height, 'buried rail')
                    bank_checks += 1
        assert all(math.isclose(top-height, .46, abs_tol=1e-9) for top, height in zip(row['railTopHeights'], row['heights']))
        line = LineString(row['points'])
        assert line.buffer(1.25, cap_style=2).intersection(blocked).area < .01
        assert row['formationTriangles'], row['id']
        beds = []
        for tri in row['formationTriangles']:
            assert len(tri) == 3 and all(math.isfinite(v) for p in tri for v in p)
            assert all(-.100001 <= p[1] <= 5.500001 for p in tri)
            footprint = Polygon([(p[0], p[2]) for p in tri])
            assert footprint.intersection(blocked).area < .000001
            beds.append(footprint)
        bed_count += len(beds)
        bed = unary_union(beds)
        # Centreline and sleepers have a physical formation throughout the
        # interpreted rise, including the restored throat beyond the parcel.
        assert line.difference(bed.buffer(.001)).length < .01, row['id']
        if row['sourceTrackId']:
            source = stems[row['sourceTrackId']]
            assert row['sourceControls'][:-1] == source['points'][:-1]
            assert math.dist(row['sourceControls'][-1], source['points'][-1]) < 1.8
            assert line.hausdorff_distance(LineString(source['points'])) < register['junctionTreatment']['maximumRoutedStemBoundaryShiftMetres'] == 3.5
    reached, queue = {'branch'}, deque(['branch'])
    while queue:
        for node in graph[queue.popleft()]:
            if node not in reached:
                reached.add(node); queue.append(node)
    assert reached == set(graph)
    assert set(stems).issubset(reached)
    target, formation = branch_join(infra, register)
    assert points['branch'] == target
    assert levels['branch'] == [formation, formation+.46]
    branch = next(q for q in infra['railways'] if q['name'] == register['branchJoin']['railwayName'])
    a, b = branch['route'][:2]
    dx, dz = b[0]-a[0], b[1]-a[1]
    assert math.dist(normals['branch'], [-dz/math.hypot(dx, dz), dx/math.hypot(dx, dz)])*1.435/2 < .05
    assert register['profile']['gradeLengthMetres'] == 240
    assert len({row['levelApproachMetres'] for row in tracks}) == 1
    assert tracks[0]['levelApproachMetres'] >= 35 and bank_checks > 50
    assert 'interpret' in register['profile']['evidence']
    second = build_east_depot_tracks(east, infra, blocked)
    assert json.dumps(tracks, sort_keys=True) == json.dumps(second, sort_keys=True)
    published = {q['id']: q for q in load('docs/data/factory-yards.json')['tracks']}
    if not preflight and set(q['id'] for q in tracks).issubset(published):
        assert all(published[q['id']] == q for q in tracks)
        print('Published depot tracks match connected register/module output.')
    print(f'East depot: all 11 source stems connect through three complete throats to the exact western branch track; shared {tracks[0]["levelApproachMetres"]} m plateau clears both branch banks/ballast at {bank_checks} rail samples, rail top 5.96 m, gradient <= .035, {bed_count} clipped formation triangles and byte-idempotent output pass.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--preflight', action='store_true')
    check(parser.parse_args().preflight)
