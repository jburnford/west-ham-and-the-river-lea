"""Find where water gets onto land in the connected-flood grid, and check drawn bank crests against the OS.

Run the flood builder with FLOOD_DUMP set first; it saves the full 2 m arrays:

    FLOOD_DUMP=/tmp/flood.npz python3 scripts/build_landscape_flood.py
    python3 scripts/flood_diagnostics.py /tmp/flood.npz pour 1500 2000      # basin at a point and where it fills from
    python3 scripts/flood_diagnostics.py /tmp/flood.npz spills 3.414        # land spill crests below a level (core box)
    python3 scripts/flood_diagnostics.py /tmp/flood.npz spills 3.414 -1800 -2450 -150 -240   # ... in another box (x0 z0 x1 z1)
    python3 scripts/flood_diagnostics.py /tmp/flood.npz banks               # os-flood-banks.json crests against their readings
    python3 scripts/flood_diagnostics.py /tmp/flood.npz readings            # OS bank-top/wall-top readings drawn > 0.5 m low

Levels in the dump are ODN; scene y = ODN - 1.835. Written during task E (October 2026).
"""
import json
import sys
from pathlib import Path

import numpy as np
from scipy.ndimage import label
from shapely.geometry import LineString, Point

ROOT = Path(__file__).resolve().parents[1]
OFFSET = 1.83544
CORE = (-1280, -240, 280, 1160)

d = np.load(sys.argv[1])
bed, conn, inside, water = d['bed'], d['conn'], d['inside'], d['water']
x0, z0 = d['origin']
readings = {r['id']: r for r in json.loads((ROOT / 'data/maps/os-ground-levels.json').read_text())['readings']}


def cell(x, z):
    return int((z - z0) // 2), int((x - x0) // 2)


def crest_near(x, z, radius_cells=3):
    j, i = cell(x, z)
    return float(bed[j - radius_cells:j + radius_cells + 1, i - radius_cells:i + radius_cells + 1].max()) - OFFSET


def pour(x, z):
    """The basin (cells at the same connection level) holding (x, z), and the cells it fills from."""
    j, i = cell(x, z)
    c = conn[j, i]
    lab, _ = label(np.abs(conn - c) < 1e-5)
    basin = lab == lab[j, i]
    print(f'basin {c:.3f} m ODN ({c - OFFSET:+.3f} scene), {basin.sum() * 4 / 1e4:.1f} ha')
    low = conn < c - 1e-5
    for dj, di in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
        for a, b in np.argwhere(basin & np.roll(low, (-dj, -di), axis=(0, 1)))[:10]:
            print(f'  fills at ({x0 + 2 * b}, {z0 + 2 * a}), ground {bed[a, b] - OFFSET:+.2f} scene, from ({x0 + 2 * (b + di)}, {z0 + 2 * (a + dj)})')


def spills(level, box=CORE):
    """Land cells that are the highest point on the water's way in (ground = connection level), below `level`."""
    land = inside & (water < .5)
    lower = np.zeros_like(land)
    behind = np.zeros_like(land)
    for sh in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
        nc, nb, nl = np.roll(conn, sh, (0, 1)), np.roll(bed, sh, (0, 1)), np.roll(land, sh, (0, 1))
        lower |= nc < conn - 1e-3
        with np.errstate(invalid='ignore'):
            behind |= (np.abs(nc - conn) < 1e-3) & (nb < conn - .05) & nl
    sp = (np.abs(bed - conn) < 1e-3) & (conn < level) & lower & behind & inside
    mask = np.zeros_like(sp)
    (ja, ia), (jb, ib) = cell(box[0], box[1]), cell(box[2], box[3])
    mask[max(0, ja):jb, max(0, ia):ib] = True
    lab, n = label(sp & mask, structure=np.ones((3, 3)))
    out = []
    for k in range(1, n + 1):
        a, b = np.argwhere(lab == k)[0]
        out.append((conn[a, b], x0 + 2 * b, z0 + 2 * a))
    for c, x, z in sorted(out):
        near = sorted(readings.values(), key=lambda r: (r['position'][0] - x) ** 2 + (r['position'][1] - z) ** 2)[0]
        print(f'{c - OFFSET:+.2f} scene ({c:.2f} ODN) at ({x}, {z}); nearest OS {near["valueFeet"]} ft {near["sceneY"]:.2f} ({near.get("setting")})')


def banks():
    for b in json.loads((ROOT / 'data/maps/os-flood-banks.json').read_text())['banks']:
        line = LineString(b['line'])
        pairs = []
        for rid in b['crestReadings']:
            p = line.interpolate(line.project(Point(readings[rid]['position'])))
            pairs.append(f"{readings[rid]['sceneY']:.2f}/{crest_near(p.x, p.y):.2f}")
        along = np.array([crest_near(*line.interpolate(t).coords[0]) for t in np.arange(0, line.length, 3)])
        print(f"{b['id']}: OS/drawn {' '.join(pairs)}; along the line min {along.min():.2f}, median {np.median(along):.2f}")


def low_readings():
    for r in readings.values():
        if r.get('setting') not in ('embankment_top', 'wall_top'):
            continue
        drawn = crest_near(*r['position'], radius_cells=4)
        if drawn - r['sceneY'] < -.5:
            print(f"{r['id']} {r['valueFeet']} ft OS {r['sceneY']:.2f} drawn {drawn:.2f} at {r['position']} {r.get('notes', '')[:60]}")


command = sys.argv[2]
if command == 'pour':
    pour(float(sys.argv[3]), float(sys.argv[4]))
elif command == 'spills':
    spills(float(sys.argv[3]) if len(sys.argv) > 3 else 3.414, tuple(map(float, sys.argv[4:8])) if len(sys.argv) > 7 else CORE)
elif command == 'banks':
    banks()
elif command == 'readings':
    low_readings()
