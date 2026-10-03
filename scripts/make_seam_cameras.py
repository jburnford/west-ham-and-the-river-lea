"""Generate the low-viewpoint camera list for the elevation seam sweep.

Cameras sit 2–4 m above the local ground beside waterways, bridge approaches,
railway toes and the sewer, looking along or across the feature, so that
floating objects, free-standing walls, sheared fills and bank cliffs are visible.
Writes reference/photo-review-2026-10-03/cameras-seams.json for render_views.py.
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'docs/data'
OUT = ROOT / 'reference/photo-review-2026-10-03/cameras-seams.json'


def load(name):
    return json.loads((DATA / name).read_text())


def along(route, spacing):
    """Points every `spacing` metres along a polyline, with the local heading."""
    points = []
    carry = 0.0
    for (ax, az), (bx, bz) in zip(route, route[1:]):
        length = math.hypot(bx - ax, bz - az)
        if length == 0:
            continue
        ux, uz = (bx - ax) / length, (bz - az) / length
        d = carry
        while d <= length:
            points.append((ax + ux * d, az + uz * d, ux, uz))
            d += spacing
        carry = d - length
    return points


def main():
    cameras = []
    infra, gp, rn = load('infrastructure.json'), load('ground-plan.json'), load('river-network.json')

    # The author's four screenshots, approximated.
    cameras += [
        {'label': 'author-1-sewer-bridge-west', 'position': [-45, 1.5, 60], 'target': [20, 6, 10], 'fov': 70},
        {'label': 'author-2-bromley-holder-bank', 'position': [-300, 2, 640], 'target': [-250, 1, 520], 'fov': 62},
        {'label': 'author-3-junction-fins-a', 'position': [-700, 3, 450], 'target': [-640, 0, 400], 'fov': 62},
        {'label': 'author-4-north-railway', 'position': [-820, 3, -520], 'target': [-820, 2, -700], 'fov': 60},
    ]

    # West bank hotspots, Three Mills to Bromley: look across the river from the water side and along the bank.
    for i, z in enumerate(range(600, 1301, 100)):
        cameras.append({'label': f'lea-west-bank-across-{z}', 'position': [-560, 2.5, z], 'target': [-680, 0, z], 'fov': 62})
        cameras.append({'label': f'lea-west-bank-along-{z}', 'position': [-640, 3, z], 'target': [-640, 0, z + 120], 'fov': 62})
    cameras.append({'label': 'extension-cliff-149-449', 'position': [-120, 2.5, 470], 'target': [-149, 1, 449], 'fov': 62})
    cameras.append({'label': 'network-steps-1100-700', 'position': [-1070, 3, -660], 'target': [-1100, 0, -700], 'fov': 62})

    # Channelsea and Abbey Creek: along the water at 2 m.
    for z in range(-300, 701, 125):
        cameras.append({'label': f'channelsea-along-{z}', 'position': [15, 2, z], 'target': [15, 0.5, z + 150], 'fov': 62})

    # Every road bridge: approach fill from 40 m back on each side, and the span from the water.
    for b in infra['roadBridges']:
        (ax, az), (bx, bz) = b['route'][0], b['route'][-1]
        ux, uz = bx - ax, bz - az
        n = math.hypot(ux, uz) or 1
        ux, uz = ux / n, uz / n
        mx, mz = (ax + bx) / 2, (az + bz) / 2
        cameras.append({'label': f"bridge-{b['id']}-approach-a", 'position': [ax - ux * 40, 3, az - uz * 40], 'target': [mx, b['height'] / 2, mz], 'fov': 60})
        cameras.append({'label': f"bridge-{b['id']}-approach-b", 'position': [bx + ux * 40, 3, bz + uz * 40], 'target': [mx, b['height'] / 2, mz], 'fov': 60})
        cameras.append({'label': f"bridge-{b['id']}-span", 'position': [mx - uz * 45, 1.5, mz + ux * 45], 'target': [mx, b['height'] / 2, mz], 'fov': 60})

    # Railway toes: every 300 m along each route, looking at the embankment from 35 m off.
    for r in infra['railways']:
        for i, (x, z, ux, uz) in enumerate(along(r['route'], 300)):
            cameras.append({'label': f"rail-{r['name'].split(' ')[0].lower()}-{i}", 'position': [x - uz * 35, 2.5, z + ux * 35], 'target': [x, r.get('formationHeight', 5) / 2, z], 'fov': 60})

    # Sewer toes: every 200 m along the route, both sides.
    for i, (x, z, ux, uz) in enumerate(along(gp['neighbourhood']['sewer']['route'], 200)):
        for side, sign in (('n', -1), ('s', 1)):
            cameras.append({'label': f'sewer-toe-{i}{side}', 'position': [x - uz * sign * 30, 2, z + ux * sign * 30], 'target': [x, 4, z], 'fov': 60})

    # Reviewed river connections (the extended reaches): look along each from its first route point.
    for c in rn['reviewedConnections']['connections']:
        (ax, az), (bx, bz) = c['route'][0], c['route'][-1]
        cameras.append({'label': f"connection-{c['id']}", 'position': [ax, 2.5, az], 'target': [bx, 0, bz], 'fov': 62})

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(cameras, indent=1))
    print(f'{len(cameras)} cameras written to {OUT.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
