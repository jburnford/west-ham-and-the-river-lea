"""Publish the OS crane register for the page, with each crane set on land and turned to its work.

Reads data/maps/os-cranes.json (positions read from the OS five-foot plan) and writes
docs/data/wharf-cranes.json. For a wharf crane the jib points at the nearest drawn water edge;
a crane whose OS dot falls inside the drawn water or a modelled building is moved the shortest
distance onto open ground, and the move is recorded. Yard cranes point away from the nearest
modelled building, over the open yard. Dimensions are one type-based form for every crane.

    python3 scripts/build_wharf_cranes.py
"""
import hashlib
import json
import math
from pathlib import Path

from shapely.geometry import Point, Polygon
from shapely.ops import nearest_points, unary_union

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data/maps/os-cranes.json'
OUT = ROOT / 'docs/data/wharf-cranes.json'
CLEARANCE = 0.9  # metres from water edge or wall to the crane post: room for the base
# Type-based form of a hand-worked iron wharf crane, metres. Explicit estimates, not measurements.
FORM = {'baseSize': 1.6, 'baseHeight': 0.45, 'postHeight': 4.2, 'postRadius': 0.16, 'jibFoot': 0.9,
        'jibReach': 5.2, 'jibTipHeight': 6.4, 'jibRadius': 0.11, 'tieRadius': 0.035, 'winchSize': [0.7, 0.6, 0.5],
        'hookDrop': 2.2}


def polygons(path, key):
    data = json.loads((ROOT / path).read_text())
    out = []
    for item in data[key]:
        for p in item.get('polygons') or []:
            g = Polygon(p[0], p[1:]).buffer(0)
            if not g.is_empty:
                out.append(g)
    return out


def main():
    raw = SOURCE.read_bytes()
    register = json.loads(raw)
    water = unary_union(polygons('docs/data/ground-plan.json', 'rivers') + polygons('docs/data/river-system-1900.json', 'reaches'))
    factory = json.loads((ROOT / 'docs/data/factory-buildings.json').read_text())
    buildings = unary_union([Polygon(b['footprint']).buffer(0) for b in factory['buildings']])
    blocked = unary_union([water, buildings])
    cranes = []
    for c in register['cranes']:
        assert c.get('reading') and c.get('place') and c['setting'] in ('wharf', 'yard'), c['id']
        mapped = Point(c['x'], c['z'])
        point, moved = mapped, 0.0
        if blocked.buffer(CLEARANCE).contains(mapped):
            ring = blocked.buffer(CLEARANCE)
            point = nearest_points(ring.exterior if ring.geom_type == 'Polygon' else ring.boundary, mapped)[0]
            moved = mapped.distance(point)
            assert moved < 3.0, (c['id'], 'mapped dot more than 3 m inside water or a building', round(moved, 2))
        target = water if c['setting'] == 'wharf' else buildings
        edge = nearest_points(point, target)[1]
        heading = math.degrees(math.atan2(edge.y - point.y, edge.x - point.x))
        if c['setting'] == 'yard':
            heading = (heading + 360) % 360 - 180  # turn the jib away from the building, over the open yard
        reach = point.distance(edge)
        rad = math.radians(heading)
        tip = Point(point.x + FORM['jibReach'] * math.cos(rad), point.y + FORM['jibReach'] * math.sin(rad))
        assert not buildings.contains(tip), (c['id'], 'jib tip inside a modelled building')
        if c['setting'] == 'wharf':
            assert reach < 15, (c['id'], 'wharf crane more than 15 m from drawn water', round(reach, 1))
        cranes.append({
            'id': c['id'], 'x': round(point.x, 3), 'z': round(point.y, 3), 'mapped': [c['x'], c['z']],
            'movedMetres': round(moved, 2), 'headingDegrees': round(heading, 1), 'setting': c['setting'],
            'place': c['place'], 'distanceToTargetMetres': round(reach, 2),
            'positionEvidence': f"OS five-foot crane symbol: {c['reading']}."
                                + (f' Moved {moved:.2f} m onto open ground clear of the drawn water or a modelled wall.' if moved else ''),
            'headingEvidence': ('Jib turned toward the nearest drawn water edge (interpretation: the OS gives no direction).'
                                if c['setting'] == 'wharf' else
                                'Jib turned away from the nearest modelled building, over the open yard (interpretation: the OS gives no direction).')})
    out = {
        'origin': {'easting': 538900, 'northing': 183209}, 'crs': 'EPSG:27700 local metres, x east, z south, y up',
        'source': register['source'], 'method': register['method'], 'form': {**FORM, 'evidence': register['form']},
        'cranes': cranes, 'deferred': register['deferred'],
        'register': str(SOURCE.relative_to(ROOT)), 'registerSha256': hashlib.sha256(raw).hexdigest(),
        'inputHashes': {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
                        for p in ('docs/data/ground-plan.json', 'docs/data/river-system-1900.json', 'docs/data/factory-buildings.json')},
    }
    OUT.write_text(json.dumps(out, indent=1) + '\n')
    print(f"Wharf cranes: {len(cranes)} placed, {sum(1 for c in cranes if c['movedMetres'])} moved onto land, "
          f"{len(register['deferred'])} deferred.")


if __name__ == '__main__':
    main()
