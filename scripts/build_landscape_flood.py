"""First connected-inundation surface, composed from the existing 1900 scene.

No terrain or structure is moved. Heights and barriers retain their source
uncertainty. A uniform tidal stage is a geometric experiment, not a hydrograph.
"""
import hashlib
import heapq
import json
from pathlib import Path

import numpy as np
import shapely
from shapely.geometry import Polygon, LineString

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / 'docs/data'
inputs = []


def read(name, binary=False):
    path = PUBLIC / name
    inputs.append(path)
    return path.read_bytes() if binary else json.loads(path.read_text())


def connection_levels(bed, seeds):
    """Minimum stage reaching each cell over four-neighbour surface paths."""
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


def build():
    meta = read('terrain-1900.json')
    network = read('river-network.json')
    infra = read('infrastructure.json')
    plan = read('ground-plan.json')
    assert meta['epoch'] == meta['geometryEpoch'] == '1900'
    shape = (meta['height'], meta['width'])
    ground = np.frombuffer(read(meta['files']['scene'], True), '<f4').reshape(shape).copy()
    weight = np.frombuffer(read(meta['files']['weight'], True), '<f4').reshape(shape)
    road = np.frombuffer(read(meta['files']['roadMask'], True), 'u1').reshape(shape) > 0
    offset = meta['verticalReference']['odnMinusSceneYMetres']
    x0, z0, x1, z1 = meta['bounds']
    X, Z = np.meshgrid(np.arange(x0, x1 + 1), np.arange(z0, z1 + 1))
    kind = np.where(weight >= .999, 1, 0).astype('u1')
    polygons = [Polygon(rings[0], rings[1:]) for rings in network['tide']['polygons']]
    water = shapely.union_all(polygons)
    tidal = shapely.contains_xy(water, X, Z)
    # Road profile stores subgrade; compose its paving on top, as the renderer does.
    ground[road] += .065
    kind[road] = 4

    def raster(triangles, category):
        # The small structural meshes use exact planar triangles. Sample every
        # metre before conservative reduction so narrow barriers are not skipped.
        for tri in triangles:
            a, b, c = np.asarray(tri, dtype=float)
            lo = np.floor(np.minimum.reduce([a, b, c])[[0, 2]]).astype(int)
            hi = np.ceil(np.maximum.reduce([a, b, c])[[0, 2]]).astype(int)
            ix0, iz0 = max(0, lo[0] - x0), max(0, lo[1] - z0)
            ix1, iz1 = min(shape[1]-1, hi[0]-x0), min(shape[0]-1, hi[1]-z0)
            if ix1 < ix0 or iz1 < iz0: continue
            den = (b[2]-c[2])*(a[0]-c[0])+(c[0]-b[0])*(a[2]-c[2])
            if abs(den) < 1e-9: continue
            sl = np.s_[iz0:iz1+1, ix0:ix1+1]
            xx, zz = X[sl], Z[sl]
            u = ((b[2]-c[2])*(xx-c[0])+(c[0]-b[0])*(zz-c[2]))/den
            v = ((c[2]-a[2])*(xx-c[0])+(a[0]-c[0])*(zz-c[2]))/den
            inside = (u >= -1e-8) & (v >= -1e-8) & (u+v <= 1+1e-8) & ~tidal[sl]
            y = u*a[1]+v*b[1]+(1-u-v)*c[1]
            raised = inside & (y > ground[sl])
            ground[sl][raised] = y[raised]
            kind[sl][raised] = category

    for railway in infra['railways']:
        raster(railway['embankment'], 2)
    sewer = plan['neighbourhood']['sewer']
    crossing = infra['sewerHighStreet']

    def cover(x, z):
        distance = np.hypot(x-crossing['centre'][0], z-crossing['centre'][1])
        t = np.clip((distance-12)/crossing['sewerApproachLength'], 0, 1)
        return crossing['surfaceHeight']+(sewer['height']-crossing['surfaceHeight'])*t*t*(3-2*t)

    raster([[[x, y*cover(x, z)/sewer['height'], z] for x, y, z in tri]
            for tri in infra['sewerBanks']], 2)
    raster([[[x, cover(x, z), z] for x, z in tri] for tri in infra['sewerCrestTriangles']], 2)
    # Rendered thin retaining walls are sampled with a one-metre halo to avoid
    # losing them between raster points; no claim that this is their real width.
    walls = network['retainingEdges']
    wall_geom = shapely.union_all([LineString(r) for r in walls['routes']]).buffer(1)
    wall = shapely.contains_xy(wall_geom, X, Z) & ~tidal
    raised = wall & (ground < walls['crestHeight'])
    ground[raised] = walls['crestHeight']
    kind[raised] = 2
    kind[tidal] = 3
    ground += offset

    # 4m blocks conservatively keep the highest sampled surface. Classification
    # retains river fractions and historic support separately from barrier labels.
    step = 4
    height, width = (shape[0]-1)//step, (shape[1]-1)//step
    def blocks(a):
        return a[:height*step, :width*step].reshape(height, step, width, step).transpose(0, 2, 1, 3)
    bed = blocks(ground).max(axis=(2, 3))
    river_fraction = blocks(tidal).mean(axis=(2, 3))
    seeds = river_fraction >= .5
    # Seed channel interiors only. Bank cells still require a connected path
    # crossing the actual sampled crest; low land never becomes a river seed.
    kind4 = blocks(kind).max(axis=(2, 3))
    support = blocks((weight >= .999) & (kind == 1)).mean(axis=(2, 3))
    threshold = connection_levels(bed, seeds)
    assert np.isfinite(threshold).all() and np.all(threshold >= bed)
    assert seeds.sum() > 100
    files = {'bed': 'landscape-flood-1900.bed.f32', 'connection': 'landscape-flood-1900.connection.f32',
             'riverFraction': 'landscape-flood-1900.river.f32', 'support': 'landscape-flood-1900.support.f32',
             'kind': 'landscape-flood-1900.kind.u8'}
    for key, a in [('bed', bed), ('connection', threshold), ('riverFraction', river_fraction), ('support', support), ('kind', kind4)]:
        a.astype('u1' if key == 'kind' else '<f4').tofile(PUBLIC/files[key])
    out = {'epoch': '1900', 'method': 'connected-uniform-stage', 'step': step, 'width': width, 'height': height,
           'bounds': [x0, z0, x0+width*step, z0+height*step], 'files': files,
           'verticalReference': meta['verticalReference'], 'defaultLevelODN': 3.5,
           'minLevelODN': 1.9, 'maxLevelODN': 5.5,
           'seedPolicy': 'Cells at least half inside mapped tidal polygons; all tidal reaches share the test stage.',
           'reviewedRiverConnections':network['reviewedConnections'],
           'areaM2': width*height*step*step, 'supportedFieldAreaM2': float(support.sum()*step*step),
           'limitations': [
               'Geometric connected inundation, not a flow or event simulation. No speed, timing, rainfall, mill operation or retained ponding on recession.',
               'Only the bounded existing terrain is shown, not the whole Lea watershed. Exterior routes into the area are omitted.',
               'Most ground and bank heights remain scene interpretations; only labelled field areas have reviewed historical height support.',
               'Existing railway heights include an unresolved conflict with a road bridge; they are retained for consistency with the visible landscape.',
               'Mapped tidal reaches receive the same test level. Bridges and sewer crossings over tidal water remain open underneath; head losses are omitted.',
               'Four-metre cells retain the highest one-metre surface sample, broadening narrow barriers and simplifying shorelines.',
               'Building interiors, small drainage openings and sewer networks are not modelled. Buildings remain visible; the surface does not predict indoor flooding.',
               'Reviewed mill passages are included geometrically with inferred narrow sections. Lock water is separate from tidal seeds. Mill losses, lock operation and discharge capacities are not simulated.',
               'The provisional ODN reference is not a survey calibration; no selected level is assigned to 1888, 1897, 1904 or 1928.'
           ],
           'inputHashes': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}}
    (PUBLIC/'landscape-flood-1900.json').write_text(json.dumps(out, indent=2)+'\n')
    for level in [1.9, 2.5, 3.5, 4.5, 5.5]:
        wet = (threshold < level) & (bed < level-.05)
        print(f'{level:.1f} m ODN: {(wet*(1-river_fraction)).sum()*step*step/10000:.2f} ha land connected')
    print(f'Built {width}×{height} flood grid ({out["areaM2"]/1e6:.2f} km²).')


if __name__ == '__main__':
    build()
