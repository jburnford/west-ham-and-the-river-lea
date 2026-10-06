"""Depression hierarchy for volume flooding (FLOOD_MODEL_PLAN.md section 4.6, Phase V).

The connection grid (build_landscape_flood.py) says at what level a source reaches each cell; a basin then goes from dry
to full as soon as the source passes its rim. Here the same 2 m ground is split into hollows that fill with a volume of
water, lowest ground first:

1. Hollows smaller than MIN_AREA_CELLS at their rim are filled (area closing), and hollows shallower than MIN_DEPTH are
   filled to their rim, repeatedly, so the hierarchy keeps only hollows that hold a useful volume.
2. Every remaining land minimum seeds a leaf basin: its catchment by a minimax priority flood. Water cells
   are outlets: tidal (the tide polygons) or river (other mapped water), one outlet per connected patch of each.
3. The leaves merge in order of the saddle between them (Kruskal). Two hollows that meet make a parent basin at the
   saddle level. A hollow that meets an outlet, or ground already draining to one, is attached there: above its spill
   level its water runs out to that outlet (rain) and, the other way, a source standing above that level pours in
   over the crest (tide, surge or river).
4. Each basin has a stage-volume table on a common 5 cm level grid, from its lowest level to its spill level (attached
   basins and closed basins run on to TOP_ODN, for water standing above the crest from a source).

All levels are ODN metres. Cells are 2 m; volumes are cubic metres.
"""
import numpy as np
from numba import njit
from scipy.ndimage import label as nd_label
from skimage.morphology import area_closing, local_minima

STEP = 0.05                  # stage-table interval, metres
MIN_DEPTH = 0.05             # hollows shallower than this are filled to their rim (plan section 4.6)
MIN_AREA_CELLS = 250         # hollows smaller than this at their rim (0.1 ha of 2 m cells) are filled
MIN_OUTLET_CELLS = 25        # water patches smaller than this (0.01 ha) are treated as ground
TOP_ODN = 6.5                # stage tables of attached and closed basins run to this level
WALL = 1.0e4                 # cells outside the modelled ground


def prepare(bed, inside, water, tidal, kind):
    """Classify cells. Returns (hier, land, outlet_labels, outlet_tidal, enclosed): the hierarchy bed (bed with small
    hollows closed), land cells, outlet patch labels (1..n, 0 elsewhere), whether each patch is tidal, and the inside
    cells cut off from every outlet by unmodelled ground (they never take part)."""
    mapped = (water >= .5) & inside & (kind != 2)      # retaining walls and shut structures across water are ground
    is_tidal = mapped & (tidal >= .5)
    labels = np.zeros(bed.shape, np.int32)
    tidal_flags = []
    n = 0
    for mask, flag in ((is_tidal, True), (mapped & ~is_tidal, False)):
        lab, count = nd_label(mask)
        sizes = np.bincount(lab.ravel(), minlength=count + 1)
        keep = np.flatnonzero(sizes >= MIN_OUTLET_CELLS)
        keep = keep[keep > 0]
        remap = np.zeros(count + 1, np.int32)
        remap[keep] = n + 1 + np.arange(len(keep))
        labels = np.where(remap[lab] > 0, remap[lab], labels)
        tidal_flags += [flag] * len(keep)
        n += len(keep)
    outlet = labels > 0
    land = inside & ~outlet
    # Area closing over the whole grid, the outside a wall. Islands of modelled ground walled in by the outside close towards WALL; they are
    # cut off from every source and are dropped.
    f = np.where(inside, bed.astype(np.float64), WALL)
    closed = area_closing(f, area_threshold=MIN_AREA_CELLS, connectivity=1)
    enclosed = land & (closed > WALL / 2)
    land &= ~enclosed
    hier = np.where(land, closed, bed.astype(np.float64))
    return hier, land, labels, np.array(tidal_flags, bool), enclosed


@njit(cache=True)
def _priority_flood(g, valid, markers):
    """Grow the markers over the valid cells, each cell taking the marker that reaches it at the lowest level, where a
    path's level is the highest ground on it (four-neighbour). Ties go to the earlier push. Returns the labels."""
    height, width = g.shape
    flat_g = g.ravel()
    flat_valid = valid.ravel()
    labels = markers.ravel().copy()
    n = flat_g.size
    heap_level = np.empty(n, np.float64)
    heap_order = np.empty(n, np.int64)
    heap_cell = np.empty(n, np.int64)
    size = 0
    counter = 0
    for c in range(n):
        if labels[c] > 0:
            heap_level[size] = flat_g[c]; heap_order[size] = counter; heap_cell[size] = c
            counter += 1
            i = size
            size += 1
            while i > 0:
                p = (i - 1) // 2
                if heap_level[p] < heap_level[i] or (heap_level[p] == heap_level[i] and heap_order[p] < heap_order[i]):
                    break
                heap_level[p], heap_level[i] = heap_level[i], heap_level[p]
                heap_order[p], heap_order[i] = heap_order[i], heap_order[p]
                heap_cell[p], heap_cell[i] = heap_cell[i], heap_cell[p]
                i = p
    while size > 0:
        level, c = heap_level[0], heap_cell[0]
        size -= 1
        heap_level[0] = heap_level[size]; heap_order[0] = heap_order[size]; heap_cell[0] = heap_cell[size]
        i = 0
        while True:
            l, r, m = 2 * i + 1, 2 * i + 2, i
            if l < size and (heap_level[l] < heap_level[m] or (heap_level[l] == heap_level[m] and heap_order[l] < heap_order[m])):
                m = l
            if r < size and (heap_level[r] < heap_level[m] or (heap_level[r] == heap_level[m] and heap_order[r] < heap_order[m])):
                m = r
            if m == i:
                break
            heap_level[m], heap_level[i] = heap_level[i], heap_level[m]
            heap_order[m], heap_order[i] = heap_order[i], heap_order[m]
            heap_cell[m], heap_cell[i] = heap_cell[i], heap_cell[m]
            i = m
        x = c % width
        for k in range(4):
            if k == 0:
                if x == 0: continue
                d = c - 1
            elif k == 1:
                if x == width - 1: continue
                d = c + 1
            elif k == 2:
                if c < width: continue
                d = c - width
            else:
                if c + width >= n: continue
                d = c + width
            if labels[d] > 0 or not flat_valid[d]:
                continue
            labels[d] = labels[c]
            v = max(level, flat_g[d])
            heap_level[size] = v; heap_order[size] = counter; heap_cell[size] = d
            counter += 1
            i = size
            size += 1
            while i > 0:
                p = (i - 1) // 2
                if heap_level[p] < heap_level[i] or (heap_level[p] == heap_level[i] and heap_order[p] < heap_order[i]):
                    break
                heap_level[p], heap_level[i] = heap_level[i], heap_level[p]
                heap_order[p], heap_order[i] = heap_order[i], heap_order[p]
                heap_cell[p], heap_cell[i] = heap_cell[i], heap_cell[p]
                i = p
    return labels.reshape(height, width)


def leaves(hier, land, outlet_labels):
    """Leaf catchments: labels 1..n_land for land leaves, then n_land + outlet label for outlet cells; 0 elsewhere.
    Outlet cells keep their own ground: a half-water cell on a bank top is a high outlet, so the land behind it does
    not drain to the channel below the crest."""
    outlet = outlet_labels > 0
    g = np.where(land | outlet, hier, WALL)
    minima = local_minima(g, connectivity=1, allow_borders=True) & land
    seeds, n_land = nd_label(minima)
    markers = seeds.astype(np.int32)
    markers[outlet] = n_land + outlet_labels[outlet]
    return _priority_flood(g, land | outlet, markers), n_land


def boundary_pairs(labels, hier):
    """Every four-neighbour cell pair across a leaf boundary: (leaf a, leaf b, saddle level, cell a, cell b), sorted by
    saddle (stable, so the result does not depend on the sort implementation)."""
    flat = labels.ravel()
    h = hier.ravel()
    idx = np.arange(flat.size).reshape(labels.shape)
    a_cells = np.concatenate([idx[:, :-1].ravel(), idx[:-1, :].ravel()])
    b_cells = np.concatenate([idx[:, 1:].ravel(), idx[1:, :].ravel()])
    la, lb = flat[a_cells], flat[b_cells]
    keep = (la != lb) & (la > 0) & (lb > 0)
    a_cells, b_cells, la, lb = a_cells[keep], b_cells[keep], la[keep], lb[keep]
    saddle = np.maximum(h[a_cells], h[b_cells])
    order = np.lexsort((b_cells, a_cells, saddle))
    return la[order] - 1, lb[order] - 1, saddle[order], a_cells[order], b_cells[order]


@njit(cache=True)
def _find(uf, a):
    while uf[a] != a:
        uf[a] = uf[uf[a]]
        a = uf[a]
    return a


@njit(cache=True)
def _kruskal(n_land, n_out, pa, pb, ps, pca, pcb):
    """Merge leaves in saddle order. Nodes 0..n_land-1 are land leaves, n_land..n_land+n_out-1 outlets, then parents.
    For every node: parent, the two children, its spill level, the leaf across the saddle it spills into (spill_to),
    the leaf of its own on the saddle (spill_from), the saddle cells, and whether it is attached (spills to ground that
    drains to an outlet, or to an outlet)."""
    n_leaf = n_land + n_out
    cap = 2 * n_leaf
    parent = np.full(cap, -1, np.int64)
    child0 = np.full(cap, -1, np.int64)
    child1 = np.full(cap, -1, np.int64)
    spill = np.full(cap, np.inf)
    formation = np.full(cap, np.nan)
    spill_to = np.full(cap, -1, np.int64)
    spill_from = np.full(cap, -1, np.int64)
    spill_cell = np.full(cap, -1, np.int64)
    attached = np.zeros(cap, np.bool_)
    uf = np.arange(n_leaf)
    top = np.arange(n_leaf)
    rooted = np.zeros(n_leaf, np.bool_)
    rooted[n_land:] = True
    n = n_leaf
    for e in range(len(pa)):
        a, b, s, cell = pa[e], pb[e], ps[e], pca[e]
        ca, cb = _find(uf, a), _find(uf, b)
        if ca == cb:
            continue
        if rooted[ca] and rooted[cb]:
            uf[cb] = ca
            continue
        if not rooted[ca] and not rooted[cb]:
            ta, tb = top[ca], top[cb]
            parent[ta] = n
            parent[tb] = n
            child0[n] = ta
            child1[n] = tb
            formation[n] = s
            spill[ta] = s
            spill[tb] = s
            spill_to[ta] = b
            spill_from[ta] = a
            spill_to[tb] = a
            spill_from[tb] = b
            spill_cell[ta] = cell
            spill_cell[tb] = cell
            uf[cb] = ca
            top[ca] = n
            n += 1
            continue
        if rooted[ca]:   # make cb the rooted side
            ca, cb = cb, ca
            a, b = b, a
            cell = pcb[e]
        t = top[ca]
        spill[t] = s
        spill_to[t] = b
        spill_from[t] = a
        spill_cell[t] = cell
        attached[t] = True
        uf[ca] = cb
    return (parent[:n], child0[:n], child1[:n], spill[:n], formation[:n], spill_to[:n], spill_from[:n],
            spill_cell[:n], attached[:n])


def hierarchy(hier, land, outlet_labels):
    labels, n_land = leaves(hier, land, outlet_labels)
    n_out = int(outlet_labels.max())
    pa, pb, ps, pca, pcb = boundary_pairs(labels, hier)
    tree = _kruskal(n_land, n_out, pa, pb, ps, pca, pcb)
    return labels, n_land, n_out, tree, (pa, pb, ps)


def prune(hier, land, outlet_labels, log=print):
    """Fill leaf hollows shallower than MIN_DEPTH to their rim until none is left; returns the final hierarchy."""
    hier = hier.copy()
    for round_ in range(40):
        labels, n_land, n_out, tree, pairs = hierarchy(hier, land, outlet_labels)
        spill = tree[3]
        lab = labels.ravel()
        is_land = (lab > 0) & (lab <= n_land)
        lowest = np.full(n_land, np.inf)
        np.minimum.at(lowest, lab[is_land] - 1, hier.ravel()[is_land])
        depth = spill[:n_land] - lowest
        # A flat that already stands at its rim (depth 0, e.g. one cell level with the water beside it) stays a leaf
        # of no volume: filling cannot change it.
        shallow = np.flatnonzero(np.isfinite(depth) & (depth < MIN_DEPTH) & (depth > 1e-9))
        log(f'  hierarchy round {round_}: {n_land} hollows, {n_out} outlets, {len(shallow)} shallower than {MIN_DEPTH} m')
        if not len(shallow):
            return hier, labels, n_land, n_out, tree, pairs
        fill = np.zeros(n_land + 1)
        fill[:] = -np.inf
        fill[shallow + 1] = spill[shallow]
        raise_to = np.where(lab <= n_land, fill[np.minimum(lab, n_land)], -np.inf).reshape(hier.shape)
        hier = np.where(land, np.maximum(hier, raise_to), hier)
    raise RuntimeError('pruning did not converge')


def leaf_tables(hier, labels, n_land, h0, n_levels):
    """Volume below each grid level h0 + k*STEP for every land leaf: (n_land, n_levels) float64, cubic metres."""
    lab = labels.ravel()
    sel = (lab > 0) & (lab <= n_land)
    leaf = lab[sel] - 1
    h = hier.ravel()[sel]
    # Cell with ground h is under water at level L when h < L: first counted at bin k = floor((h - h0) / STEP) + 1.
    k = np.clip(np.floor((h - h0) / STEP).astype(np.int64) + 1, 0, n_levels)
    count = np.zeros((n_land, n_levels + 1))
    total = np.zeros((n_land, n_levels + 1))
    np.add.at(count, (leaf, k), 1.0)
    np.add.at(total, (leaf, k), h)
    count = np.cumsum(count, axis=1)[:, :n_levels]
    total = np.cumsum(total, axis=1)[:, :n_levels]
    levels = h0 + STEP * np.arange(n_levels)
    return 4.0 * (levels[None, :] * count - total), np.bincount(leaf, minlength=n_land) * 4.0


def subtree_order(n_leaf, child0, child1, parent):
    """Depth-first leaf order and, per node, its leaf range [start, end) in that order."""
    n = len(parent)
    start = np.zeros(n, np.int64)
    end = np.zeros(n, np.int64)
    order = []
    for root in np.flatnonzero(parent < 0):
        stack = [(int(root), False)]
        while stack:
            node, done = stack.pop()
            if node < n_leaf:
                start[node] = len(order)
                order.append(node)
                end[node] = len(order)
                continue
            if done:
                start[node] = start[child0[node]]
                end[node] = end[child1[node]]
                continue
            stack.append((node, True))
            stack.append((int(child1[node]), False))
            stack.append((int(child0[node]), False))
    # Children are visited child0 then child1, so a parent's leaves are contiguous.
    return np.array(order, np.int64), start, end


def node_tables(leaf_volume, n_land, n_leaf, tree, h0):
    """Stage-volume table of every basin on the common level grid h0 + k*STEP: from the grid level at or below its
    lowest ground (a leaf) or its formation level (a parent) to the first grid level at or above its spill level, or to
    TOP_ODN for basins that are attached (a source can stand above the crest) or never spill. Returns
    (first grid index, values) per node; outlets get empty tables."""
    parent, child0, child1, spill, formation, _, _, _, attached = tree
    n_levels = leaf_volume.shape[1]
    order, start, end = subtree_order(n_leaf, child0, child1, parent)
    rows = np.zeros((len(order) + 1, n_levels))
    is_land = order < n_land
    rows[1:][is_land] = leaf_volume[order[is_land]]
    prefix = np.cumsum(rows, axis=0)
    first, tables = [], []
    for n in range(len(parent)):
        if n_land <= n < n_leaf:
            first.append(0); tables.append(np.zeros(0))
            continue
        volume = prefix[end[n]] - prefix[start[n]]
        wet = np.flatnonzero(volume > 0)
        k_low = max(0, (wet[0] - 1) if len(wet) else 0)
        base = formation[n] if n >= n_leaf else h0 + STEP * k_low
        k0 = int(np.floor((base - h0) / STEP + 1e-9))
        top = TOP_ODN if (attached[n] or not np.isfinite(spill[n])) else spill[n]
        k1 = min(n_levels - 1, int(np.ceil((top - h0) / STEP - 1e-9)))
        first.append(k0); tables.append(volume[k0:k1 + 1])
    return np.array(first), tables


def crest_profiles(labels, hier, n_land, n_leaf, tree, pairs):
    """For each attached basin, the crest it shares with the leaf it spills into: the saddle level of every 2 m cell
    edge across that boundary, in centimetres, with counts. A source standing above the crest pours in over it."""
    parent, child0, child1, spill, _, spill_to, _, _, attached = tree
    pa, pb, ps = pairs
    # The attached basin above each land leaf (walk up to the top of its unattached subtree).
    top = np.arange(len(parent))
    for leaf in range(n_land):
        n = leaf
        while parent[n] >= 0:
            n = parent[n]
        top[leaf] = n
    profiles = {}
    for a, b, s in zip(pa, pb, ps):
        for p, q in ((a, b), (b, a)):
            if p >= n_land:
                continue
            r = top[p]
            if attached[r] and spill_to[r] == q:
                profiles.setdefault(int(r), []).append(int(round(s * 100)))
    out = {}
    for r, cm in profiles.items():
        levels, counts = np.unique(np.array(cm), return_counts=True)
        out[r] = [[int(l), int(c)] for l, c in zip(levels, counts)]
    return out, top


SLUICE_DISCHARGE = 0.3       # m³/s per marsh sluice while it runs (estimate; see basin_model)
SLUICE_SEARCH_M = 16         # a sluice drains the lowest hollow within this distance
WEIR_C = 1.6                 # broad-crested weir coefficient, m^0.5/s (estimate; 1.7 is the ideal sharp-edged value)


def basin_model(bed, inside, water, tidal, kind, origin, sluices, log=print):
    """The whole Phase V basin model from the 2 m arrays of build_landscape_flood.py. Returns the hierarchy bed, the
    leaf label grid (0 none, 1.. leaf or outlet id + 1), and the JSON-ready description with its volume tables."""
    x0, z0 = origin
    hier, land, outlet_labels, outlet_tidal, enclosed = prepare(bed, inside, water, tidal, kind)
    closed_volume = float((hier - bed)[land].sum() * 4)
    hier, labels, n_land, n_out, tree, pairs = prune(hier, land, outlet_labels, log)
    depth_volume = float((hier - bed)[land].sum() * 4) - closed_volume
    n_leaf = n_land + n_out
    parent, child0, child1, spill, formation, spill_to, spill_from, spill_cell, attached = tree
    h0 = float(np.floor(hier[land].min() / STEP) * STEP) - STEP
    n_levels = int(round((TOP_ODN - h0) / STEP)) + 1
    leaf_volume, catchment = leaf_tables(hier, labels, n_land, h0, n_levels)
    first, tables = node_tables(leaf_volume, n_land, n_leaf, tree, h0)
    crests, top = crest_profiles(labels, hier, n_land, n_leaf, tree, pairs)
    width = labels.shape[1]
    lab = labels.ravel()
    is_land = (lab > 0) & (lab <= n_land)
    lowest = np.full(n_land, np.inf)
    np.minimum.at(lowest, lab[is_land] - 1, hier.ravel()[is_land])

    # Marsh sluices: each drains the lowest hollow within SLUICE_SEARCH_M of its mapped position, to the nearest water.
    out_cells = np.flatnonzero(outlet_labels.ravel() > 0)
    out_x, out_z = x0 + 2 * (out_cells % width) + 1, z0 + 2 * (out_cells // width) + 1
    sluice_records = []
    r = SLUICE_SEARCH_M // 2
    for s in sluices:
        x, z = s['position']['scene']
        j, i = int((z - z0) // 2), int((x - x0) // 2)
        win = labels[j - r:j + r + 1, i - r:i + r + 1]
        ground = np.where((win > 0) & (win <= n_land), hier[j - r:j + r + 1, i - r:i + r + 1], np.inf)
        k = int(np.argmin(ground))
        if not np.isfinite(ground.ravel()[k]):
            log(f'  sluice {s["id"]}: no hollow within {SLUICE_SEARCH_M} m; left out')
            continue
        nearest = int(np.argmin((out_x - x) ** 2 + (out_z - z) ** 2))
        outlet = int(outlet_labels.ravel()[out_cells[nearest]]) - 1
        sluice_records.append({
            'id': s['id'], 'leaf': int(win.ravel()[k]) - 1,
            'sillODN': round(float(ground.ravel()[k]), 3),
            'dischargeM3PerSecond': SLUICE_DISCHARGE,
            'outlet': n_land + outlet,
            'outletDistanceMetres': round(float(np.hypot(out_x[nearest] - x, out_z[nearest] - z)), 1)})

    offsets = np.cumsum([0] + [len(t) for t in tables])
    volumes = np.concatenate(tables).astype('<f4')
    finite = lambda v: None if not np.isfinite(v) else round(float(v), 4)
    nodes = {
        'count': int(len(parent)), 'landLeaves': n_land, 'outlets': n_out,
        'outletTidal': [bool(t) for t in outlet_tidal],
        'parent': parent.tolist(), 'child0': child0.tolist(), 'child1': child1.tolist(),
        'spillODN': [finite(v) for v in spill], 'formationODN': [finite(v) for v in formation],
        'lowestODN': [round(float(v), 4) for v in lowest],
        'spillTo': spill_to.tolist(), 'spillFrom': spill_from.tolist(), 'attached': attached.astype(int).tolist(),
        'spillAt': [None if c < 0 else [int(x0 + 2 * (c % width) + 1), int(z0 + 2 * (c // width) + 1)] for c in spill_cell],
        'catchmentM2': [int(v) for v in catchment],
        'tableFirst': first.tolist(), 'tableOffset': offsets[:-1].tolist(), 'tableLength': [len(t) for t in tables],
        'crests': {str(k): v for k, v in sorted(crests.items())},
    }
    stats = {'hollows': n_land, 'outlets': n_out, 'parents': int(len(parent) - n_leaf),
             'attached': int(attached.sum()), 'closedHollowVolumeM3': round(closed_volume),
             'shallowFilledVolumeM3': round(depth_volume), 'enclosedCells': int(enclosed.sum())}
    model = {'levelGrid': {'baseODN': round(h0, 4), 'step': STEP, 'count': n_levels, 'topODN': TOP_ODN},
             'parameters': {'weirCoefficient': WEIR_C, 'edgeWidthMetres': 2, 'minDepthMetres': MIN_DEPTH,
                            'minAreaHa': MIN_AREA_CELLS * 4 / 1e4, 'sluiceSearchMetres': SLUICE_SEARCH_M},
             'nodes': nodes, 'sluices': sluice_records, 'stats': stats}
    return hier, land, labels, n_land, n_out, model, volumes
