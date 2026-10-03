"""Complete the OS depot siding fan with connected, graded formation beds.

Normal builds need only saved map registers and infrastructure, not map tiles
or ignored authoring evidence. Heights are model interpretations.
"""
import heapq
import json
import math
from pathlib import Path

from shapely import constrained_delaunay_triangles
from shapely.geometry import LineString, Point, Polygon

ROOT = Path(__file__).resolve().parents[1]
REGISTER = 'data/maps/east-depot-junctions.json'


def _load():
    return json.loads((ROOT/REGISTER).read_text())


def branch_join(infra, register=None):
    r = register or _load()
    spec = r['branchJoin']
    branch = next(q for q in infra['railways'] if q['name'] == spec['railwayName'])
    a, b = branch['route'][:2]
    dx, dz = b[0]-a[0], b[1]-a[1]
    length = math.hypot(dx, dz)
    assert 0 < spec['chainageMetres'] < length
    t, offset = spec['chainageMetres']/length, spec['trackOffsetMetres']
    point = [a[0]+dx*t-dz/length*offset, a[1]+dz*t+dx/length*offset]
    return point, branch['formationHeight']


def _unit(a, b):
    dx, dz = b[0]-a[0], b[1]-a[1]
    length = math.hypot(dx, dz)
    return [dx/length, dz/length]


def _approach(controls, exit_tangent, treatment):
    """Turn gently onto the shared rail direction within the mapped fan."""
    previous, end = controls[-2:]
    original_length = math.dist(previous, end)
    incoming = _unit(previous, end)
    length = min(treatment['maximumApproachLengthMetres'], original_length)
    start = [end[j]-incoming[j]*length for j in range(2)]
    straight = min(treatment['finalStraightMetres'], length/3)
    near = [end[j]-exit_tangent[j]*straight for j in range(2)]
    span = math.dist(start, near)
    count = max(2, math.ceil(span/2))
    curve = []
    for i in range(1, count+1):
        t = i/count
        h00, h10 = 2*t**3-3*t**2+1, t**3-2*t**2+t
        h01, h11 = -2*t**3+3*t**2, t**3-t**2
        curve.append([h00*start[j]+h10*incoming[j]*span+
                      h01*near[j]+h11*exit_tangent[j]*span for j in range(2)])
    prefix = controls[:-1]
    if math.dist(prefix[-1], start) > .000001:
        prefix = [*prefix, start]
    return [*prefix, *curve, end]


def _distances(edges, target='branch'):
    graph = {}
    for a, b, points in edges:
        length = LineString(points).length
        graph.setdefault(a, []).append((b, length))
        graph.setdefault(b, []).append((a, length))
    distance, queue = {target: 0.0}, [(0.0, target)]
    while queue:
        cost, a = heapq.heappop(queue)
        if cost != distance[a]:
            continue
        for b, length in graph[a]:
            next_cost = cost+length
            if next_cost < distance.get(b, math.inf):
                distance[b] = next_cost
                heapq.heappush(queue, (next_cost, b))
    assert set(distance) == set(graph), 'Every depot stem must reach the branch'
    return distance


def _level_approach(edges, distances, infra, register):
    """Hold running-line height throughout either existing branch bank."""
    profile = register['profile']
    banks = [q for q in infra['railways']
             if q['name'] == register['branchJoin']['railwayName']
             or q.get('id') in profile['bankRailwayIds']]
    assert len(banks) == 2
    corridors = [(LineString(q['route']), q.get('baseHalfWidth', 17)+
                  profile['bankOverlapSleeperAllowanceMetres']) for q in banks]
    required = profile['minimumLevelApproachMetres']
    for a, b, points in edges:
        line = LineString(points)
        count = max(1, math.ceil(line.length/2))
        for i in range(count+1):
            d = line.length*i/count
            point = line.interpolate(d)
            if any(point.distance(bank) <= width for bank, width in corridors):
                required = max(required, distances[b]+line.length-d)
    # Include a full station and rounding margin before the first bank overlap.
    return math.ceil((required+2)/10)*10


def _bed(points, heights, blocked, profile):
    """Sloped filled formation from rail crest to the existing ground datum."""
    line = LineString(points)
    crest = profile['crestHalfWidthMetres']
    ground = profile['groundHeight']
    slope = profile['sideSlopeHorizontalPerVertical']
    maximum_base = crest+max(0, max(heights)-ground)*slope
    local_blocked = blocked.intersection(line.buffer(maximum_base+1))
    chainages = [0.0]
    for a, b in zip(points, points[1:]):
        chainages.append(chainages[-1]+math.dist(a, b))

    def levels(x, z):
        d = line.project(Point(x, z))
        # All output stations are <=2m apart; this lookup is bounded and small.
        from bisect import bisect_right
        i = min(len(points)-2, max(0, bisect_right(chainages, d)-1))
        span = chainages[i+1]-chainages[i]
        t = min(1, max(0, (d-chainages[i])/span)) if span else 0
        height = heights[i]+(heights[i+1]-heights[i])*t
        base = crest+max(0, height-ground)*slope
        transverse = line.distance(Point(x, z))
        ratio = min(1, max(0, (base-transverse)/(base-crest))) if base > crest else 1
        return ground+(height-ground)*ratio

    rows = []
    for i, ((x, z), height) in enumerate(zip(points, heights)):
        a, b = points[max(0, i-1)], points[min(len(points)-1, i+1)]
        dx, dz = b[0]-a[0], b[1]-a[1]
        length = math.hypot(dx, dz)
        normal = (-dz/length, dx/length)
        base = crest+max(0, height-ground)*slope
        rows.append([[x+normal[0]*offset, z+normal[1]*offset]
                     for offset in [-base, -crest, crest, base]])
    triangles = []
    for a, b in zip(rows, rows[1:]):
        for j in range(3):
            cell = Polygon([a[j], a[j+1], b[j+1], b[j]])
            if not cell.is_valid:
                cell = cell.buffer(0)
            clipped = cell if local_blocked.is_empty else cell.difference(local_blocked)
            for poly in getattr(clipped, 'geoms', [clipped]):
                if poly.geom_type != 'Polygon' or poly.area < .00001:
                    continue
                for tri in constrained_delaunay_triangles(poly).geoms:
                    triangles.append([[x, levels(x, z), z]
                                      for x, z in list(tri.exterior.coords)[:3]])
    return triangles


def build_east_depot_tracks(east, infra, blocked):
    """Return 11 full stems + three shared throat edges, with absolute levels.

    Each row has points, heights/formationHeights, railTopHeights and
    formationTriangles. `heights` is an alias for formationHeights, not terrain
    offsets. Rail/sleeper rendering must use the saved absolute level profile.
    """
    r = _load()
    controls = r['worldControls']
    branch, branch_height = branch_join(infra, r)
    west, east_tip = controls['westernThroat'][0], controls['easternThroat'][0]
    shared = controls['westernThroat'][-1]
    assert shared == controls['easternThroat'][-1] == controls['branchApproach'][0]
    stems = east['railSidings']
    assert len(stems) == 11
    edges, originals, source_controls = [], {}, {}
    outgoing = {'west': _unit(*controls['westernThroat'][:2]),
                'east': _unit(*controls['easternThroat'][:2]),
                'shared': _unit(*controls['branchApproach'][:2])}
    branch_row = next(q for q in infra['railways'] if q['name'] == r['branchJoin']['railwayName'])
    outgoing['branch'] = _unit(*branch_row['route'][:2])
    for source in stems:
        ident = source['id']
        assert source['points'][-1] == r['sourceSidingEndpoints'][ident]
        destination = 'west' if source['groupIndex'] < 4 else 'east'
        tip = west if destination == 'west' else east_tip
        # The reviewed paired stems converge at the mapped turnout. Preserve
        # every upstream source control; reconcile only the final short tip.
        assert math.dist(source['points'][-1], tip) < 1.8
        points = [*source['points'][:-1], tip]
        source_controls[ident] = points
        edges.append((ident, destination, _approach(points, outgoing[destination], r['junctionTreatment'])))
        originals[ident] = source
    for a, b, points in [('west', 'shared', controls['westernThroat']),
                         ('east', 'shared', controls['easternThroat']),
                         ('shared', 'branch', [*controls['branchApproach'], branch])]:
        source_controls[a] = points
        edges.append((a, b, _approach(points, outgoing[b], r['junctionTreatment'])))
    distances = _distances(edges)
    profile = r['profile']
    plateau = _level_approach(edges, distances, infra, r)
    grade = abs(branch_height-profile['yardFormationHeight'])/profile['gradeLengthMetres']
    assert grade <= profile['maximumGradient']
    def level(remaining):
        t = min(1, max(0, 1-(remaining-plateau)/profile['gradeLengthMetres']))
        return profile['yardFormationHeight']+(branch_height-profile['yardFormationHeight'])*t
    result = []
    for a, b, controls in edges:
        line = LineString(controls)
        assert distances[a] >= distances[b]
        assert abs(distances[a]-distances[b]-line.length) < .000001
        assert line.buffer(1.25, cap_style=2).intersection(blocked).area < .01, (a, 'rail clearance')
        # Include each authored bend exactly so no spline cuts a mapped throat.
        stations = [list(controls[0])]
        for p, q in zip(controls, controls[1:]):
            count = max(1, math.ceil(math.dist(p, q)/2))
            stations += [[p[0]+(q[0]-p[0])*i/count, p[1]+(q[1]-p[1])*i/count]
                         for i in range(1, count+1)]
        samples, heights = [0.0], []
        for p, q in zip(stations, stations[1:]):
            samples.append(samples[-1]+math.dist(p, q))
        for d in samples:
            remaining = distances[b]+line.length-d
            heights.append(level(remaining))
        heights[-1] = level(distances[b])
        ident = a if a in originals else 'east-depot-'+a+'-throat'
        row = dict(id=ident, siteId=13011, points=stations,
                   gauge=r['branchJoin']['gauge'], sleeperWidth=2.4,
                   heights=heights, formationHeights=heights,
                   railTopHeights=[h+r['branchJoin']['railTopAboveFormationMetres'] for h in heights],
                   sourceNodes=[a, b], sourceTrackId=a if a in originals else None,
                   sourceControls=source_controls[a], routingControls=controls,
                   distanceToBranch=[distances[a], distances[b]],
                   gradeLengthMetres=profile['gradeLengthMetres'], maximumGradient=grade,
                   levelApproachMetres=plateau,
                   formationTriangles=_bed(stations, heights, blocked, profile),
                   profileEvidence=profile['evidence'],
                   evidence=(originals[a]['evidence'] if a in originals else r['method'])+
                       ' Complete mapped throat retained beyond yard-parcel limits; exact branch-track join uses saved junction register. No Goad evidence asserted.')
        result.append(row)
    return result
