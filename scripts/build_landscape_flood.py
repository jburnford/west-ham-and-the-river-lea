"""Connected-flood levels over the whole drawn ground of the c.1900 model.

The ground the page draws (scripts/sample_drawn_ground.mjs) is sampled every metre over the modelled ground: the
regional marsh landscape (main-landscape weight > 0), the river network and river system water and the core. Railway
and sewer embankments and retaining walls are composed on top at their drawn heights. One-metre samples are reduced to
2 m cells keeping the highest sample, so narrow banks and walls stay closed. For each source of water (the tidal reaches
now; the mill ponds and the Navigation in Phase 2 of FLOOD_MODEL_PLAN.md) every cell stores its connection level: the
lowest water level at which that source reaches it over the ground (a minimax path). The page shows a cell wet when the
source stands above that level.

Outputs (docs/data/landscape-flood-1900.*): a 2 m grid over the back rivers, Three Mills and the core (`fine`), and a
10 m grid over the rest of the modelled ground (`coarse`, each cell the lowest connection level of its 2 m cells). Levels
are stored as unsigned 16-bit centimetres above -10 m ODN; 65535 is unreachable, outside the model or above the cap.
"""
import hashlib
import heapq
import json
import os
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import shapely
from shapely.geometry import LineString, Polygon
from skimage.morphology import reconstruction

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / 'docs/data'
inputs = []

CELL = 2                      # metres, the connection grid
COARSE = 10                   # metres, the regional display grid (5 x 5 cells)
FINE_BOX = (-1300, -981, 600, 1199)    # x0, z0, x1, z1: Stratford back rivers, Three Mills, the core and the old box
LEGACY_BOX = (-510, -320, 550, 832)    # the task A-D flood box, kept for comparison
THAMES_EDGE_M = 30           # the Thames and a band along its shore are the closed edge of the model
CAP_ODN = 8.0                 # connection levels above this are stored as unreachable
NONE = 65535
STAGES = [1.9, 2.5, 3.5, 4.5, 5.5]


def read(name, binary=False):
    path = PUBLIC / name
    inputs.append(path)
    return path.read_bytes() if binary else json.loads(path.read_text())


def connection_levels(bed, seeds):
    """Minimum stage reaching each cell over four-neighbour surface paths (reference implementation)."""
    height, width = bed.shape
    result = np.full(bed.size, np.inf)
    flat = bed.ravel()
    heap = []
    for i in np.flatnonzero(seeds):
        result[i] = flat[i]
        heap.append((float(flat[i]), int(i)))
    heapq.heapify(heap)
    while heap:
        level, i = heapq.heappop(heap)
        if level != result[i]:
            continue
        x = i % width
        neighbours = []
        if x: neighbours.append(i - 1)
        if x + 1 < width: neighbours.append(i + 1)
        if i >= width: neighbours.append(i - width)
        if i + width < flat.size: neighbours.append(i + width)
        for j in neighbours:
            candidate = max(level, float(flat[j]))
            if candidate < result[j]:
                result[j] = candidate
                heapq.heappush(heap, (candidate, j))
    return result.reshape(height, width)


def fast_connection_levels(bed, seeds, barrier=None):
    """The same minimax levels by greyscale reconstruction by erosion (four-neighbour), for large grids.
    Cells in `barrier` never carry water and come back as inf."""
    big = float(np.nanmax(bed)) + 1000.0
    mask = bed.astype(np.float64).copy()
    if barrier is not None:
        mask[barrier] = big
    seed = np.full_like(mask, big)
    seed[seeds] = mask[seeds]
    cross = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], bool)
    out = reconstruction(seed, mask, method='erosion', footprint=cross)
    out[out >= big] = np.inf
    return out


def encode(levels):
    out = np.full(levels.shape, NONE, np.uint16)
    ok = np.isfinite(levels) & (levels <= CAP_ODN)
    out[ok] = np.clip(np.round((levels[ok] + 10.0) * 100.0), 0, NONE - 1).astype(np.uint16)
    return out


def build():
    meta = read('terrain-1900.json')
    network = read('river-network.json')
    system = read('river-system-1900.json')
    infra = read('infrastructure.json')
    plan = read('ground-plan.json')
    landscape = read('main-landscape-1900.json')
    assert meta['epoch'] == meta['geometryEpoch'] == '1900'
    for key in ('core', 'network', 'system', 'extension', 'groundMesh', 'level', 'weight'):
        read(landscape['files'][key], True)
    offset = meta['verticalReference']['odnMinusSceneYMetres']

    # The modelled ground: the regional landscape's weight field, plus every water polygon and the core.
    field = landscape['field']
    fx0, fz0, fx1, fz1 = field['bounds']
    fstep = field['step']
    weight = np.frombuffer(read(landscape['files']['weight'], True), '<f4').reshape(field['height'], field['width'])
    rows, cols = np.nonzero(weight > 0)
    x0, z0 = int(fx0 + fstep * cols.min()), int(fz0 + fstep * rows.min())
    x1, z1 = int(fx0 + fstep * (cols.max() + 1)), int(fz0 + fstep * (rows.max() + 1))
    width, height = x1 - x0, z1 - z0
    assert width % COARSE == 0 and height % COARSE == 0
    assert (FINE_BOX[0] - x0) % COARSE == 0 and (FINE_BOX[1] - z0) % COARSE == 0
    tide = shapely.union_all([Polygon(r[0], r[1:]) for r in network['tide']['polygons']]
                             + [Polygon(r[0], r[1:]) for r in system['tidalWaterPolygons']])
    water = shapely.union_all([tide] + [Polygon(r[0], r[1:]) for r in system['waterPolygons']]
                              + [Polygon(p[0], p[1:]) for r in plan['rivers'] for p in r['polygons']])
    # The Thames frontage east of Bow Creek is not modelled (no river wall; the regional ground there is the flat
    # outer level), so the Thames is left out: the tide enters the model up Bow Creek only.
    thames = shapely.union_all([Polygon(p[0], p[1:]) for r in system['reaches'] if r['id'] == 'thames-mouth-context' for p in r['polygons']]).buffer(THAMES_EDGE_M)
    tide = tide.difference(thames)
    shapely.prepare(tide); shapely.prepare(water); shapely.prepare(thames)
    core = read('river-terrain.json')['bounds']

    # Road paving over the old box (the road mask is only stored there), as the renderer composes it.
    tx0, tz0 = meta['bounds'][:2]
    road = np.frombuffer(read(meta['files']['roadMask'], True), 'u1').reshape(meta['height'], meta['width']) > 0
    old_weight = np.frombuffer(read(meta['files']['weight'], True), '<f4').reshape(meta['height'], meta['width'])

    rail = [np.asarray(t, float) for r in infra['railways'] for t in r['embankment']]
    sewer = plan['neighbourhood']['sewer']
    crossing = infra['sewerHighStreet']

    def cover(x, z):
        distance = np.hypot(x - crossing['centre'][0], z - crossing['centre'][1])
        t = np.clip((distance - 12) / crossing['sewerApproachLength'], 0, 1)
        return crossing['surfaceHeight'] + (sewer['height'] - crossing['surfaceHeight']) * t * t * (3 - 2 * t)

    sewer_tris = [np.array([[x, y * cover(x, z) / sewer['height'], z] for x, y, z in tri]) for tri in infra['sewerBanks']]
    sewer_tris += [np.array([[x, cover(x, z), z] for x, z in tri]) for tri in infra['sewerCrestTriangles']]
    structure_tris = rail + sewer_tris
    tri_lo = np.array([t[:, [0, 2]].min(0) for t in structure_tris]); tri_hi = np.array([t[:, [0, 2]].max(0) for t in structure_tris])
    walls = [(np.asarray(r, float), np.asarray(c, float), False) for r, c in zip(network['retainingEdges']['routes'], landscape['retainingEdgeCrests']) if len(r) >= 2]
    # Control structures that shut the tide out (data/maps/lea-control-structures.json tideBarrier), drawn as walls
    # across the channel at their estimated tops. They also close the channel for the tidal seeds behind them.
    register_path = ROOT / 'data/maps/lea-control-structures.json'
    inputs.append(register_path)
    barriers = [(np.asarray(s['crossLine']['scene'], float), s['tideBarrier']['sceneY'], s['id'])
                for s in json.loads(register_path.read_text())['structures'] if s.get('tideBarrier') and s.get('crossLine')]
    walls += [(line, np.full(len(line), level), True) for line, level, _ in barriers]

    shape2 = (height // CELL, width // CELL)
    bed = np.empty(shape2, np.float32)
    tidal_fraction = np.empty(shape2, np.float32)
    water_fraction = np.empty(shape2, np.float32)
    inside = np.empty(shape2, bool)
    kind = np.empty(shape2, np.uint8)
    support = np.zeros(shape2, np.float32)
    with tempfile.TemporaryDirectory() as tmp:
        drawn = Path(tmp) / 'drawn.f32'
        subprocess.run(['node', str(ROOT / 'scripts/sample_drawn_ground.mjs'), str(x0), str(z0), str(width), str(height), '1', str(drawn)],
                       check=True, capture_output=True)
        ground_all = np.memmap(drawn, '<f4', mode='r', shape=(height, width))
        strip = 200
        xs = np.arange(x0, x1, dtype=float)
        for r0 in range(0, height, strip):
            r1 = min(height, r0 + strip)
            zs = np.arange(z0 + r0, z0 + r1, dtype=float)
            X, Z = np.meshgrid(xs, zs)
            ground = np.array(ground_all[r0:r1], np.float32)
            assert np.isfinite(ground).all()
            k = np.zeros(ground.shape, np.uint8)
            tidal = shapely.contains_xy(tide, X, Z)
            wi = np.clip(((X - fx0) / fstep).astype(int), 0, field['width'] - 1)
            wj = np.clip(((Z - fz0) / fstep).astype(int), 0, field['height'] - 1)
            modelled = (weight[wj, wi] > 0) | shapely.contains_xy(water, X, Z)
            modelled |= (X >= core[0]) & (X <= core[2]) & (Z >= core[1]) & (Z <= core[3])
            modelled &= ~shapely.contains_xy(thames, X, Z)
            mapped_water = shapely.contains_xy(water, X, Z)
            # Road paving and the historic support field, inside the old 1 m box.
            oi, oj = (X - tx0).astype(int), (Z - tz0).astype(int)
            old = (X >= tx0) & (oi < meta['width']) & (Z >= tz0) & (oj < meta['height'])
            paved = np.zeros_like(old); paved[old] = road[oj[old], oi[old]]
            ground[paved] += .065; k[paved] = 4
            supported = np.zeros_like(old); supported[old] = old_weight[oj[old], oi[old]] >= .999
            k[supported & (k == 0)] = 1

            def raster(tri, category):
                a, b, c = tri
                ix0, ix1 = int(max(0, np.floor(min(a[0], b[0], c[0])) - x0)), int(min(width - 1, np.ceil(max(a[0], b[0], c[0])) - x0))
                iz0, iz1 = int(max(r0, np.floor(min(a[2], b[2], c[2])) - z0)), int(min(r1 - 1, np.ceil(max(a[2], b[2], c[2])) - z0))
                if ix1 < ix0 or iz1 < iz0: return
                den = (b[2] - c[2]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[2] - c[2])
                if abs(den) < 1e-9: return
                sl = np.s_[iz0 - r0:iz1 - r0 + 1, ix0:ix1 + 1]
                xx, zz = X[sl], Z[sl]
                u = ((b[2] - c[2]) * (xx - c[0]) + (c[0] - b[0]) * (zz - c[2])) / den
                v = ((c[2] - a[2]) * (xx - c[0]) + (a[0] - c[0]) * (zz - c[2])) / den
                ins = (u >= -1e-8) & (v >= -1e-8) & (u + v <= 1 + 1e-8) & ~tidal[sl]
                y = u * a[1] + v * b[1] + (1 - u - v) * c[1]
                raised = ins & (y > ground[sl])
                ground[sl][raised] = y[raised]
                k[sl][raised] = category

            zlo, zhi = z0 + r0 - 1, z0 + r1 + 1
            for n in np.flatnonzero((tri_hi[:, 1] >= zlo) & (tri_lo[:, 1] <= zhi)):
                raster(structure_tris[n], 2)
            # Drawn retaining walls, at their copings, with a one-metre halo so no sample falls between.
            for route, crest, across_water in walls:
                if route[:, 1].max() + 2 < zlo or route[:, 1].min() - 2 > zhi: continue
                lo = np.floor(route.min(0) - 2).astype(int); hi = np.ceil(route.max(0) + 2).astype(int)
                ix0, ix1 = max(0, lo[0] - x0), min(width - 1, hi[0] - x0)
                iz0, iz1 = max(r0, lo[1] - z0), min(r1 - 1, hi[1] - z0)
                if ix1 < ix0 or iz1 < iz0: continue
                sl = np.s_[iz0 - r0:iz1 - r0 + 1, ix0:ix1 + 1]
                wall = shapely.contains_xy(LineString(route).buffer(1), X[sl], Z[sl])
                if across_water:
                    tidal[sl][wall] = False   # a shut structure is neither water nor a seed
                else:
                    wall &= ~tidal[sl]
                if not wall.any(): continue
                q = np.column_stack([X[sl][wall], Z[sl][wall]])
                top = crest[np.argmin(((q[:, None, :] - route[None, :, :]) ** 2).sum(-1), axis=1)]
                cells = ground[sl]; kk = k[sl]
                idx = np.nonzero(wall); up = cells[idx] < top
                cells[idx[0][up], idx[1][up]] = top[up]; kk[idx[0][up], idx[1][up]] = 2
            k[tidal] = 3
            ground += offset

            def blocks(a):
                h = a.shape[0] // CELL
                return a[:h * CELL].reshape(h, CELL, width // CELL, CELL).transpose(0, 2, 1, 3)
            s0, s1 = r0 // CELL, r1 // CELL
            bed[s0:s1] = blocks(ground).max(axis=(2, 3))
            tidal_fraction[s0:s1] = blocks(tidal).mean(axis=(2, 3))
            water_fraction[s0:s1] = blocks(mapped_water).mean(axis=(2, 3))
            inside[s0:s1] = blocks(modelled).any(axis=(2, 3))
            kind[s0:s1] = blocks(k).max(axis=(2, 3))
            support[s0:s1] = blocks(k == 1).mean(axis=(2, 3))
            print(f'  rows {r0}-{r1} of {height}', flush=True)

    seeds = (tidal_fraction >= .5) & inside
    assert seeds.sum() > 1000
    tidal_conn = fast_connection_levels(bed, seeds, barrier=~inside)
    if os.environ.get('FLOOD_DUMP'):   # full 2 m arrays, for diagnosis
        np.savez(os.environ['FLOOD_DUMP'], bed=bed, conn=tidal_conn, inside=inside, tidal=tidal_fraction, kind=kind, origin=np.array([x0, z0]))
    assert np.all(tidal_conn[inside] >= bed[inside] - 1e-6)

    # Fine grid over FINE_BOX; coarse grid (lowest of each 5 x 5 block) over the rest.
    fi0, fj0 = int((FINE_BOX[0] - x0) // CELL), int((FINE_BOX[1] - z0) // CELL)
    fi1, fj1 = (FINE_BOX[2] - x0) // CELL, (FINE_BOX[3] - z0) // CELL
    fine = np.s_[fj0:fj1, fi0:fi1]
    f = COARSE // CELL
    ch, cw = shape2[0] // f, shape2[1] // f

    def cblocks(a):
        return a[:ch * f, :cw * f].reshape(ch, f, cw, f).transpose(0, 2, 1, 3).reshape(ch, cw, f * f)
    coarse_conn = cblocks(np.where(inside, tidal_conn, np.inf)).min(axis=2)
    coarse_inside = cblocks(inside).any(axis=2)
    coarse_bed = cblocks(np.where(inside, bed, np.inf)).min(axis=2)
    ci0, cj0, ci1, cj1 = fi0 // f, fj0 // f, fi1 // f, fj1 // f
    coarse_conn[cj0:cj1, ci0:ci1] = np.inf
    coarse_conn[~coarse_inside] = np.inf

    files = {'fineBed': 'landscape-flood-1900.fine-bed.u16', 'fineConnection': 'landscape-flood-1900.fine-connection.u16',
             'fineWater': 'landscape-flood-1900.fine-water.u8', 'fineSupport': 'landscape-flood-1900.fine-support.u8',
             'coarseConnection': 'landscape-flood-1900.coarse-connection.u16', 'coarseBed': 'landscape-flood-1900.coarse-bed.u16'}
    for old in PUBLIC.glob('landscape-flood-1900.*'):
        if old.name != 'landscape-flood-1900.json' and old.name not in files.values():
            old.unlink()
    encode(np.where(inside[fine], bed[fine], np.inf)).tofile(PUBLIC / files['fineBed'])
    encode(np.where(inside[fine], tidal_conn[fine], np.inf)).tofile(PUBLIC / files['fineConnection'])
    np.round(water_fraction[fine] * 255).astype('u1').tofile(PUBLIC / files['fineWater'])
    np.round(support[fine] * 255).astype('u1').tofile(PUBLIC / files['fineSupport'])
    encode(coarse_conn).tofile(PUBLIC / files['coarseConnection'])
    encode(np.where(np.isfinite(coarse_conn), coarse_bed, np.inf)).tofile(PUBLIC / files['coarseBed'])

    # Land connected at each stage, on the 2 m grid: the whole model, the fine box, the rest, and the old box.
    land = inside & (water_fraction < .5)
    area = CELL * CELL
    lx0, lz0 = (LEGACY_BOX[0] - x0) // CELL, (LEGACY_BOX[1] - z0) // CELL
    lx1, lz1 = (LEGACY_BOX[2] - x0) // CELL, (LEGACY_BOX[3] - z0) // CELL
    in_fine = np.zeros(shape2, bool); in_fine[fine] = True
    in_old = np.zeros(shape2, bool); in_old[lz0:lz1, lx0:lx1] = True
    edge = inside & ~(np.roll(inside, 1, 0) & np.roll(inside, -1, 0) & np.roll(inside, 1, 1) & np.roll(inside, -1, 1))
    table = []
    for s in np.round(np.arange(1.5, 6.01, .05), 2):
        wet = (tidal_conn < s) & (bed < s - .05)
        lw = wet & land
        table.append({'stageODN': float(s), 'landHa': round(float(lw.sum() * area / 1e4), 2),
                      'fineHa': round(float((lw & in_fine).sum() * area / 1e4), 2),
                      'outsideFineHa': round(float((lw & ~in_fine).sum() * area / 1e4), 2),
                      'outsideFineVolumeM3': round(float(((s - bed) * (lw & ~in_fine)).sum() * area)),
                      'legacyBoxHa': round(float((lw & in_old).sum() * area / 1e4), 2),
                      'modelEdgeCells': int((wet & edge).sum())})
    out = {'epoch': '1900', 'method': 'connected-stage-per-source', 'schemaVersion': 2,
           'cellMetres': CELL, 'sources': ['tidal'],
           'encoding': {'type': 'uint16', 'odnMetres': 'value / 100 - 10', 'none': NONE, 'capODN': CAP_ODN,
                        'waterAndSupport': 'uint8 fraction x 255 (fineWater: share of the cell inside any mapped water polygon)'},
           'fine': {'bounds': list(FINE_BOX), 'step': CELL, 'width': fi1 - fi0, 'height': fj1 - fj0},
           'coarse': {'bounds': [x0, z0, x0 + cw * COARSE, z0 + ch * COARSE], 'step': COARSE, 'width': cw, 'height': ch,
                      'note': 'Lowest connection level of each 10 m block; blank inside the fine box and outside the modelled ground.'},
           'bounds': list(FINE_BOX), 'legacyBounds': list(LEGACY_BOX), 'files': files,
           'verticalReference': meta['verticalReference'], 'defaultLevelODN': 3.5, 'minLevelODN': 1.9, 'maxLevelODN': 5.5,
           'stageTable': table,
           'groundSource': 'the drawn ground (scripts/sample_drawn_ground.mjs, as the page draws it), sampled every metre, with railway and sewer embankments and retaining walls at their drawn copings composed on top (road paving inside the old box only); 2 m cells keep their highest sample',
           'modelledGround': 'main-landscape weight > 0, every mapped water polygon and the core tile; cells outside never carry water',
           'seedPolicy': 'Cells at least half inside the tidal polygons (river network tide and river system tidal water), less the Thames context reach; all tidal reaches share the test stage.',
           'reviewedRiverConnections': network['reviewedConnections'],
           'areaM2': int(inside.sum() * area),
           'limitations': [
               'Geometric connected inundation, not a flow or event simulation: no speed, timing, rainfall, mill operation or ponding on recession (FLOOD_MODEL_PLAN.md phases 2-4).',
               'The Thames and a 30 m band along its shore are the closed edge of the model: the regional marsh has no Thames river wall east of Bow Creek (its ground runs at about 1.8-1.9 m ODN to the water), so the tide enters only up Bow Creek. This assumes the Thames wall held.',
               'Land figures exclude every mapped water polygon (tidal or not).',
               'One source so far: the tidal reaches at a single test level. The back rivers above Three Mills are still tidal in the model; the mill ponds and the Navigation come in Phase 2.',
               'Water stops at the edge of the modelled ground (the regional landscape envelope); stageTable.modelEdgeCells counts wet cells there.',
               'Most ground and bank heights remain scene interpretations; only the old box carries the historic support field.',
               'Two-metre cells keep the highest one-metre sample, broadening narrow barriers slightly. The regional grid shows the lowest level of each 10 m block.',
               'Buildings remain visible; indoor flooding is not calculated. Heights use the provisional ODN reference.'],
           'inputHashes': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}}
    (PUBLIC / 'landscape-flood-1900.json').write_text(json.dumps(out, indent=1) + '\n')
    for r in table:
        if r['stageODN'] in STAGES:
            print(f"{r['stageODN']:.1f} m ODN: {r['landHa']:.2f} ha land connected (fine box {r['fineHa']:.2f}, "
                  f"old box {r['legacyBoxHa']:.2f}, model edge cells {r['modelEdgeCells']})")
    print(f'Built {shape2[1]}x{shape2[0]} connection grid over {out["areaM2"]/1e6:.2f} km² of modelled ground.')


if __name__ == '__main__':
    build()
