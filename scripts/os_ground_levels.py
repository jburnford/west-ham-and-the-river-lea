"""OS five-foot ground levels for the main landscape (data/maps/os-ground-levels.json).

The register (scripts/prepare_os_ground_levels.py) assigns every OS spot height
in the core box to the ground it measures. This module turns it into what
scripts/build_main_landscape.py draws:

- premises levels: a site pad takes its own yard readings. With one reading the
  pad is level; with several it is their inverse-distance surface (power 2,
  distances under PAD_SOFTEN_M counted as PAD_SOFTEN_M), which honours each
  reading and is level where they agree. docs/main-landscape.js seats a
  building on the same surface at its centre (premisesLevel).
- street levels: a street corridor takes its own street readings, which are
  road-surface levels: the corridor ground is DECK_ROAD_OFFSET below them.
- the marsh correction: between works, the regional early-marsh ground is
  corrected to the marsh, open-ground, bank-foot and track readings (and, beside
  the railways the OS draws at grade, to the ground level the railway level
  register takes there) by a Gaussian-process interpolation of the residuals
  within each dry compartment (no correction crosses a river), decaying to no
  correction about 2.5 x MARSH_LENGTH_M from the nearest reading.
- support: where an applied reading lies outside the regional early-marsh
  support, the main landscape applies within SUPPORT_RADIUS_M of it, feathered
  over SUPPORT_FEATHER_M.
- the terrace (T22): inside the register's terraceZone the correction also takes
  the terrace readings (open ground, undrawn streets, towing paths), the street
  readings (at the ground under the road surface) and the yard readings, and the
  regional bank crest along the shorelines where no reading is near
  (bank_controls), so the regional terrace ground meets the OS everywhere there.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
import shapely
from scipy.ndimage import label, distance_transform_edt, map_coordinates
from shapely.geometry import LineString

ROOT = Path(__file__).resolve().parents[1]
REGISTER = 'data/maps/os-ground-levels.json'
PAD_SOFTEN_M = 3.0
MARSH_LENGTH_M = 40.0
MARSH_NOISE_M = 0.1
GRID_STEP_M = 2.0
GRID_MARGIN_M = 60.0
SUPPORT_RADIUS_M = 30.0
SUPPORT_FEATHER_M = 20.0
RAIL_SIDE_OFFSET_M = 9.0
RAIL_SIDE_SPACING_M = 20.0
APPLIED = ('premises', 'street', 'marsh', 'terrace')
ROAD_SURFACE_OFFSET = 0.065   # street readings are road-surface levels; the ground under the road is this much lower
BANK_CONTROL_SPACING_M = 15.0  # terrace zone: regional bank-crest controls along the shorelines (build_main_landscape.py)
BANK_CONTROL_INLAND_M = 4.0
BANK_CONTROL_CLEAR_M = 15.0
BANK_CONTROL_BRIDGE_M = 30.0


def load():
    return json.loads((ROOT/REGISTER).read_text())


def digest():
    return hashlib.sha256((ROOT/REGISTER).read_bytes()).hexdigest()


def premises_level(controls, q):
    """Pad level at plan points q (N,2) from controls [[x, z, y], ...] (docs/main-landscape.js premisesLevel)."""
    c = np.asarray(controls, float); q = np.asarray(q, float)
    if len(c) == 1:
        return np.full(len(q), c[0, 2])
    d = np.maximum(PAD_SOFTEN_M, np.hypot(q[:, None, 0]-c[None, :, 0], q[:, None, 1]-c[None, :, 1]))
    w = 1/(d*d)
    return (w*c[None, :, 2]).sum(axis=1)/w.sum(axis=1)


def premises(register):
    """{siteId: (controls [[x, z, y]], ids)} from the register's premises readings."""
    by = {r['id']: r for r in register['readings']}
    out = {}
    for sid, item in register['premises'].items():
        rs = [by[i] for i in item['controlIds']]
        out[int(sid)] = ([[r['position'][0], r['position'][1], r['sceneY']] for r in rs], item['controlIds'])
    return out


def streets(register):
    """{road name: [(id, x, z, road-surface y)]}."""
    by = {r['id']: r for r in register['readings']}
    return {name: [(i, *by[i]['position'], by[i]['sceneY']) for i in ids] for name, ids in register['streets'].items()}


def rail_side_controls(infra, core_box):
    """Ground beside the railways where the OS draws no embankment: the railway level register's
    at-grade formation less its 0.1 m lift, RAIL_SIDE_OFFSET_M either side of the line."""
    out = []
    for rail in infra['railways']:
        profile = rail.get('levelProfile')
        if not profile:
            continue
        line = LineString(rail['route']); chain = np.asarray(profile['chainage']); formation = np.asarray(profile['formation'])
        lift = profile.get('atGradeFormationAboveGroundMetres', .1)
        for seg in profile.get('segments', []):
            if seg['kind'] != 'at-grade':
                continue
            n = max(2, int(np.ceil((seg['to']-seg['from'])/RAIL_SIDE_SPACING_M))+1)
            for s in np.linspace(seg['from'], seg['to'], n):
                a = line.interpolate(max(0, s-1)); b = line.interpolate(min(line.length, s+1)); c = line.interpolate(s)
                ux, uz = b.x-a.x, b.y-a.y; L = np.hypot(ux, uz); ux, uz = ux/L, uz/L
                y = float(np.interp(s, chain, formation))-lift
                for side in (-1, 1):
                    x, z = c.x-uz*side*RAIL_SIDE_OFFSET_M, c.y+ux*side*RAIL_SIDE_OFFSET_M
                    if core_box[0] <= x <= core_box[2] and core_box[1] <= z <= core_box[3]:
                        out.append({'id': f"{rail['name']}@{s:.0f}{'L' if side > 0 else 'R'}", 'position': [x, z], 'sceneY': y,
                                    'kind': 'rail-side', 'railway': rail['name'], 'chainage': round(float(s), 1)})
    return out


def in_terrace_zone(register, p):
    z = register.get('terraceZone')
    return bool(z) and z[0] <= p[0] <= z[2] and z[1] <= p[1] <= z[3]


def marsh_controls(register, infra):
    """Controls of the correction: marsh and terrace readings, and (T22) inside the terrace zone also the street readings
    (at the ground under the road surface) and the yard readings, so the terrace surface passes through every OS ground
    level there and the streets and pads meet it without steps."""
    rs = []
    for r in register['readings']:
        if r['use'] in ('marsh', 'terrace') or (r['use'] in ('street', 'premises') and in_terrace_zone(register, r['position'])):
            rs.append({'id': r['id'], 'position': r['position'], 'kind': 'reading',
                       'sceneY': r['sceneY']-(ROAD_SURFACE_OFFSET if r['use'] == 'street' else 0)})
    return rs+rail_side_controls(infra, register['coreBox'])


def bank_controls(register, banks, crest, water, offset_local, infra):
    """Terrace zone (T22): the regional bank crest (from the OS bank-top readings along each bank) as controls every
    BANK_CONTROL_SPACING_M along the shorelines, BANK_CONTROL_INLAND_M inland, where no OS ground reading lies within
    BANK_CONTROL_CLEAR_M, and not on a street corridor (+5 m) or within BANK_CONTROL_BRIDGE_M of a road
    bridge. Without them the regional ground runs at terrace height to the water's edge where no reading
    says otherwise (it stood 2-3 m above the towing paths), and the bank band then draws that height at the shore."""
    # Not on streets or bridge approaches (raised above the bank on the OS: the High Street at Bow Bridge).
    keep_off = shapely.union_all([LineString(r['route']).buffer(r['width']/2+5) for r in infra['roads'] if r.get('kind') != 'path' and len(r['route']) > 1]
                                 + [LineString(b['route']).buffer(BANK_CONTROL_BRIDGE_M) for b in infra['roadBridges']])
    shapely.prepare(keep_off)
    readings = np.array([r['position'] for r in register['readings'] if r['use'] in APPLIED and in_terrace_zone(register, r['position'])], float)
    from scipy.spatial import cKDTree
    tree = cKDTree(readings) if len(readings) else None
    out = []
    for j, line in enumerate(banks.lines):
        local = offset_local(line)
        n = int(np.ceil(local.length/BANK_CONTROL_SPACING_M))
        for k in range(n+1):
            s = min(local.length, k*BANK_CONTROL_SPACING_M)
            a = local.interpolate(max(0, s-1)); b = local.interpolate(min(local.length, s+1)); c = local.interpolate(s)
            ux, uz = b.x-a.x, b.y-a.y; L = np.hypot(ux, uz)
            if L < 1e-6:
                continue
            ux, uz = ux/L, uz/L
            for side in (-1, 1):
                p = (c.x-uz*side*BANK_CONTROL_INLAND_M, c.y+ux*side*BANK_CONTROL_INLAND_M)
                if not in_terrace_zone(register, p) or water.contains(shapely.Point(p)) or keep_off.contains(shapely.Point(p)):
                    continue
                if tree is not None and tree.query(p)[0] < BANK_CONTROL_CLEAR_M:
                    continue
                out.append({'id': f'bank-{j:03d}@{s:.0f}{"L" if side > 0 else "R"}', 'position': [round(p[0], 2), round(p[1], 2)],
                            'sceneY': float(crest(np.array([[c.x, c.y]]))[0]), 'kind': 'bank-crest'})
    return out


def correction_grid(controls, prior, water, core_box, west_limit):
    """Residual correction (control - prior) on a GRID_STEP_M grid over the core box east of
    west_limit, plus GRID_MARGIN_M. Gaussian-process mean (squared-exponential kernel, length
    MARSH_LENGTH_M, noise MARSH_NOISE_M) per dry compartment of the river mask; tapered to zero
    over the margin outside the box. Returns (grid, meta, residuals)."""
    x0, z0 = west_limit-GRID_MARGIN_M, core_box[1]-GRID_MARGIN_M
    x1, z1 = core_box[2]+GRID_MARGIN_M, core_box[3]+GRID_MARGIN_M
    xs = np.arange(x0, x1+1e-9, GRID_STEP_M); zs = np.arange(z0, z1+1e-9, GRID_STEP_M)
    X, Z = np.meshgrid(xs, zs)
    wet = shapely.contains_xy(water, X, Z)
    comp, count = label(~wet)
    # Wet cells take the compartment of the nearest dry cell (a reading on a bank edge).
    nearest = distance_transform_edt(wet, return_distances=False, return_indices=True)
    comp_any = comp[tuple(nearest)]
    pos = np.array([c['position'] for c in controls], float)
    res = np.array([c['sceneY'] for c in controls], float)-prior(pos)
    ci = np.clip(np.round((pos[:, 1]-z0)/GRID_STEP_M).astype(int), 0, len(zs)-1)
    cj = np.clip(np.round((pos[:, 0]-x0)/GRID_STEP_M).astype(int), 0, len(xs)-1)
    ccomp = comp_any[ci, cj]
    grid = np.zeros(X.shape)
    for k in np.unique(ccomp):
        sel = np.flatnonzero(ccomp == k); p = pos[sel]; r = res[sel]
        d2 = ((p[:, None, :]-p[None, :, :])**2).sum(-1)
        K = np.exp(-d2/(2*MARSH_LENGTH_M**2))+MARSH_NOISE_M**2*np.eye(len(sel))
        alpha = np.linalg.solve(K, r)
        cells = np.flatnonzero((comp_any == k).ravel())
        for chunk in np.array_split(cells, max(1, len(cells)//20000)):
            q = np.column_stack([X.ravel()[chunk], Z.ravel()[chunk]])
            kq = np.exp(-((q[:, None, :]-p[None, :, :])**2).sum(-1)/(2*MARSH_LENGTH_M**2))
            # No overshoot beyond the compartment's own residual range.
            grid.ravel()[chunk] = np.clip(kq@alpha, min(0, r.min()), max(0, r.max()))
    outside = np.maximum.reduce([west_limit-X, core_box[1]-Z, X-core_box[2], Z-core_box[3], np.zeros_like(X)])
    grid *= np.clip(1-outside/GRID_MARGIN_M, 0, 1)
    grid[X < west_limit-GRID_MARGIN_M] = 0
    meta = {'bounds': [float(x0), float(z0), float(xs[-1]), float(zs[-1])], 'step': GRID_STEP_M, 'width': len(xs), 'height': len(zs)}
    return grid, meta, res


def sample(grid, meta, q):
    rc = np.array([(q[:, 1]-meta['bounds'][1])/meta['step'], (q[:, 0]-meta['bounds'][0])/meta['step']])
    return map_coordinates(grid, rc, order=1, mode='constant', cval=0)


def support_extension(register, field_points):
    """Support weight at the regional field points (N,2) from the applied readings."""
    # The terrace zone has its own full support (T22); its readings do not extend the support beyond it.
    pos = np.array([r['position'] for r in register['readings'] if r['use'] in APPLIED and not in_terrace_zone(register, r['position'])], float)
    from scipy.spatial import cKDTree
    d, _ = cKDTree(pos).query(field_points, k=1)
    t = np.clip((d-SUPPORT_RADIUS_M)/SUPPORT_FEATHER_M, 0, 1)
    return 1-t*t*(3-2*t)
