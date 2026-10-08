"""The silted back-river beds and their low-water stream over all the back-river water, network and
regional (data/maps/back-river-beds.json, task E F2).

Shared by build_river_network.py (the detailed channels) and build_river_system.py (the regional
reaches up to the Old Lea), so both meshes draw one bed and one stream, rising along the water from
the outlet at Three Mills to the heads where the rivers leave the Old Lea and the Navigation.
"""
import json
from functools import lru_cache
from pathlib import Path

import numpy as np
import shapely
from scipy.ndimage import distance_transform_edt, gaussian_filter, maximum_filter
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
from shapely.geometry import Polygon, box
from shapely.ops import transform

import tide_levels as tl
from core_river_connections import build as reviewed_connections, combined as connection_geometry

ROOT = Path(__file__).resolve().parents[1]
INPUTS = ['data/maps/back-river-beds.json', 'docs/data/ground-plan.json', 'data/maps/factory-west-context.json',
          'docs/data/lower-lea-region/index.json']


def geometry(parts):
    return shapely.union_all([Polygon(p[0], p[1:]) for p in parts])


class Profile:
    def __init__(self):
        read = lambda p: json.loads((ROOT/p).read_text())
        plan, west, region = read('docs/data/ground-plan.json'), read('data/maps/factory-west-context.json'), read('docs/data/lower-lea-region/index.json')
        silted_ids = set(tl.BACK_RIVER_ABOVE)
        # The network's corrected channels (the west context's ids are 10000 + the source index).
        current = {}
        for r in plan['rivers']+west['rivers']:
            key = r['id']-10000 if 10000 <= r['id'] < 11000 else r['id']
            current.setdefault(key, []).append(geometry(r['polygons']))
        current = {k: shapely.union_all(v) for k, v in current.items()}
        # Each back river as the river system draws it: the regional outline with the network's
        # corrected channel in place of the regional one inside its box (build_river_system.py).
        local = lambda g: transform(lambda e, n: (np.asarray(e)-538900, 183209-np.asarray(n)), g)
        self.channels = {}
        for row in region['layers']['Lower_River_Lea']:
            key = row['sourceIndex']
            if key not in silted_ids:
                continue
            g = local(geometry(row['polygons']))
            if key in current:
                g = g.difference(box(*current[key].bounds)).union(current[key])
            self.channels[key] = g
        assert set(self.channels) == silted_ids, silted_ids-set(self.channels)
        rivers = plan['rivers']
        self.connections = reviewed_connections(rivers)
        raised = set(tl.back_rivers['passages']['raised'])
        self.passages = [r for r in self.connections['connections'] if r['id'] in raised]
        assert {r['id'] for r in self.passages} == raised
        passage_geometry = {r['id']: connection_geometry({'connections': [r]}) for r in self.passages}
        # Joins under 0.5 m between pieces (the source-window edge at x -1050) are closed, as the
        # network's mesh shoreline closes them (build_river_network.py SLIVER_M).
        self.geometry = shapely.union_all(list(self.channels.values())+list(passage_geometry.values()))
        self.geometry = self.geometry.buffer(.6, join_style='mitre').buffer(-.6, join_style='mitre')
        shapely.prepare(self.geometry)
        # 1 m grid on whole metres, as the network's raster.
        x0, z0, x1, z1 = np.array(self.geometry.bounds).astype(int)+[-20, -20, 21, 21]
        self.x0, self.z0 = x0, z0
        x, z = np.arange(x0, x1+1), np.arange(z0, z1+1)
        X, Z = np.meshgrid(x, z)
        silted, above_sum, depth_sum = np.zeros(X.shape, bool), np.zeros(X.shape), np.zeros(X.shape)
        for key, g in self.channels.items():
            cell = shapely.contains_xy(g, X, Z) & ~silted
            silted |= cell;above_sum[cell] = tl.BACK_RIVER_ABOVE[key];depth_sum[cell] = tl.BACK_RIVER_STREAM[key]
        for r in self.passages:
            cell = shapely.contains_xy(passage_geometry[r['id']], X, Z) & ~silted
            members = [k for k in r['channelIds'] if k in tl.BACK_RIVER_ABOVE]
            silted |= cell
            above_sum[cell] = np.mean([tl.BACK_RIVER_ABOVE[k] for k in members])
            depth_sum[cell] = np.mean([tl.BACK_RIVER_STREAM[k] for k in members])
        # Closed joins take their values from the nearest channel cell.
        assigned = silted.copy()
        silted = shapely.contains_xy(self.geometry, X, Z) | assigned
        _, near = distance_transform_edt(~assigned, return_indices=True)
        fill = silted & ~assigned
        above_sum[fill], depth_sum[fill] = above_sum[near[0], near[1]][fill], depth_sum[near[0], near[1]][fill]
        self.silted = silted
        # Distances along the water (8-connected) from the outlet and from the heads.
        index = np.full(X.shape, -1);index[silted] = np.arange(silted.sum())
        rows, cols, steps = [], [], []
        h, w = X.shape
        for dz, dx in ((0, 1), (1, 0), (1, 1), (1, -1)):
            a = index[:h-dz, max(0, -dx):w-max(0, dx)]
            b = index[dz:, max(0, dx):w-max(0, -dx)]
            both = (a >= 0) & (b >= 0)
            rows.append(a[both]);cols.append(b[both]);steps.append(np.full(both.sum(), np.hypot(dz, dx)))
        graph = coo_matrix((np.concatenate(steps), (np.concatenate(rows), np.concatenate(cols))), shape=(silted.sum(),)*2).tocsr()
        sx, sz = X[silted], Z[silted]
        def along(points):
            seeds = np.flatnonzero(np.min([np.hypot(sx-px, sz-pz) for px, pz in points], axis=0) <= 6)
            assert len(seeds), points
            return dijkstra(graph, directed=False, indices=seeds, min_only=True)
        profile = tl.BACK_RIVER_PROFILE
        to_outlet, to_head = along([profile['outlet']['point']]), along([hd['point'] for hd in profile['heads']])
        self.unreached = int((~np.isfinite(to_outlet) | ~np.isfinite(to_head)).sum())
        assert self.unreached < 50, f'{self.unreached} silted cells not connected to the outlet and a head'
        to_outlet[~np.isfinite(to_outlet)], to_head[~np.isfinite(to_head)] = 1, 0
        sigma = tl.BACK_RIVER_SECTION['blendSigmaMetres']
        weight = np.maximum(gaussian_filter(silted.astype(float), sigma), 1e-9)
        above = gaussian_filter(above_sum*silted, sigma)/weight
        depth = gaussian_filter(depth_sum*silted, sigma)/weight
        self.floor = np.full(X.shape, np.nan)
        self.floor[silted] = tl.back_river_thalweg(to_outlet, to_head, above[silted])
        self.stream = np.full(X.shape, np.nan)
        self.stream[silted] = np.maximum(tl.LOW, self.floor[silted]+depth[silted])
        # The section by the shared formula (the network's raster gives the same on its channels).
        inside = distance_transform_edt(silted)
        ramp = tl.BACK_RIVER_SECTION['rampMetres']
        self.ramp = np.clip(maximum_filter(inside, size=2*ramp+1), 1, ramp)
        self.inside = inside
        self.bed = np.where(silted, tl.silted_bed(inside, np.nan_to_num(self.floor), self.ramp), np.nan)
        _, self.nearest = distance_transform_edt(~silted, return_indices=True)
        self.X, self.Z = X, Z

    def cells(self, x, z):
        ix = np.clip(np.round(np.asarray(x)-self.x0).astype(int), 0, self.X.shape[1]-1)
        iz = np.clip(np.round(np.asarray(z)-self.z0).astype(int), 0, self.X.shape[0]-1)
        return iz, ix

    def nearest_floor(self, x, z):
        """The thalweg of the nearest silted water, and the distance to it (grid metres)."""
        iz, ix = self.cells(x, z)
        nz, nx = self.nearest[0][iz, ix], self.nearest[1][iz, ix]
        return self.floor[nz, nx], np.hypot(nz-iz, nx-ix)

    def bed_at(self, x, z):
        """The silted bed at points inside the back-river water (NaN elsewhere)."""
        iz, ix = self.cells(x, z)
        inside = shapely.contains_xy(self.geometry, x, z)
        return np.where(inside, self.bed[iz, ix], np.nan)


@lru_cache(maxsize=1)
def profile():
    return Profile()
