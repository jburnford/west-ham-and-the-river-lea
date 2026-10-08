"""Extend bank relief along the existing GIS waterways, outside the detailed core.

Plan geometry stays with the supplied Lower_River_Lea layer. Sections are modelling
estimates, not a DEM or a traced low-water survey. No modern waterways are added.

Bank faces (land within 8 m of the mapped channels) are triangulated in bands
between offset lines of the mapped shoreline, so the waterline, the high-water
line and the crest are smooth polylines that follow the shoreline. Channel beds
and ground beyond 8 m stay on the 1 m grid; the cells cut by the shoreline or
by the 8 m line are clipped and triangulated so the two meshes share every
vertex. Retaining-wall routes lie on the shoreline and so on mesh edges.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
import shapely
from scipy.ndimage import distance_transform_edt, gaussian_filter, maximum_filter, median_filter, uniform_filter1d
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components, dijkstra
from scipy.spatial import cKDTree
from shapely import contains_xy, segmentize
from shapely.geometry import Polygon, LineString, box
from shapely.ops import unary_union, linemerge
from marsh_ditches import geometry as ditch_geometry, apply_sections
from core_river_connections import build as reviewed_connections, combined as connection_geometry
from river_bank_sections import Distance
import tide_levels as tl
from back_river_profile import profile as back_river_profile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/data'
WALL_WIDTH = .32
# Offsets (m) of the shore-following lines that carry the bank vertices. 0 is
# the mapped shoreline, 0.16 the land face of a retaining wall standing on it;
# 0.5 m spacing covers the shelf and the bank crest, 1 m the back slope. Beyond
# 8 m every section is gentle enough for the 1 m grid. No line lies on the
# tidal outline (TIDE_SHELF_M): vertices there would fall either side of it at
# random, and the landscape keeps native heights inside it but raises outside.
TIDE_SHELF_M = 5
RING_OFFSETS = [0, WALL_WIDTH/2, .5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, TIDE_SHELF_M-.1, TIDE_SHELF_M+.1, 5.5, 6, 7, 8]
ALONG_SHORE = 1.0
SLIVER_M = .25
EDGE_TOL = 2e-4  # m: float32 positions resolve about 1e-4 m at these coordinates
MERGE_TOL = 5e-3  # m: vertices closer than this (clipping noise) are one vertex
CORE_WALL_SEARCH_M = 15
# The core terrain (0.4 m grid, river-terrain build) has no mesh edges on a moved
# wall line, so the landscape wall fill would drag ground teeth up its water
# face there. Core walls are therefore only proposed, not moved, until the core
# mesh or the landscape builder can carry them.
APPLY_CORE_WALL_RELOCATION = False
SHORE_OFFSET_M = tl.SHORE_OFFSET_M  # mean (raster - exact) shoreline distance over land nodes within 5 m
BUILT_OFFSET_M = .45  # the same for distance to sites and roads, within 3 m


def polygons(geometry):
    return [g for g in getattr(geometry, 'geoms', [geometry])
            if g.geom_type == 'Polygon' and not g.is_empty]


def rings(geometry):
    return [[list(r.coords) for r in [p.exterior, *p.interiors]] for p in polygons(geometry)]


def smooth(a, b, values):
    t = np.clip((values-a)/(b-a), 0, 1)
    return t*t*(3-2*t)


def grid_noded(geometry):
    """Add a vertex wherever a ring crosses a whole-metre grid line.

    Grid cells clipped by the ring then share every vertex with the bank bands
    on its other side, so the mesh has no cracks or T-junctions there.
    """
    def ring(coords):
        coords = np.asarray(coords, dtype=float)
        out = []
        for p, q in zip(coords[:-1], coords[1:]):
            t, pts = [0.], [p]
            for k in (0, 1):
                if q[k] == p[k]:
                    continue
                lo, hi = sorted((p[k], q[k]))
                values = np.arange(np.ceil(lo), np.floor(hi)+1)
                s = (values-p[k])/(q[k]-p[k])
                crossing = p+np.outer(s, q-p)
                crossing[:, k] = values  # exactly on the grid line
                t.extend(s)
                pts.extend(crossing)
            t = np.asarray(t)
            order = np.argsort(t, kind='stable')
            t, pts = t[order], np.asarray(pts)[order]
            keep = (t < 1) & np.r_[True, np.diff(t) > 1e-12]
            out.append(pts[keep])
        out.append(coords[-1:])
        return np.vstack(out)
    return shapely.MultiPolygon([Polygon(ring(p.exterior.coords), [ring(h.coords) for h in p.interiors])
                                 for p in polygons(geometry)])


def relocate_core_walls(routes, core, river, buildings):
    """Move retaining-wall routes inside the detailed core to the core's bank line.

    There the GIS outline is the low-water line about 7.5 m inside the core
    terrain's own channel section (its exposed tidal mud). The bank line is the
    landward edge of that mud, found along the wall's land-side normal every
    1 m, then median- and mean-filtered along the wall. Within 10 m of the core
    boundary the offset tapers to zero, joining the network shoreline. A route
    whose new line would pass through mapped buildings is left where it is:
    there the buildings, not the mud edge, front the river.
    """
    x0, z0, x1, z1 = core['bounds'];step = core['step']
    props = np.fromfile(OUT/core['propertyFile'], 'u1').reshape(core['height'], core['width'], 4)
    # Same test as the main landscape's preserved tidal mud.
    mud = (props[..., 3] > 200) & (props[..., 2] < 80)

    def mud_at(p):
        i = np.round((p[..., 0]-x0)/step).astype(int);j = np.round((p[..., 1]-z0)/step).astype(int)
        ok = (i >= 0) & (i < core['width']) & (j >= 0) & (j < core['height'])
        return ok & mud[j.clip(0, core['height']-1), i.clip(0, core['width']-1)]

    def depth_inside(p):
        return np.minimum(np.minimum(p[..., 0]-x0, x1-p[..., 0]), np.minimum(p[..., 1]-z0, z1-p[..., 1]))
    march = np.arange(0, CORE_WALL_SEARCH_M+1e-9, .1)
    clear_run = int(round(1/.1))+1
    moved_routes, records, kept = [], [], []
    for index, route in enumerate(routes):
        if depth_inside(np.asarray(route)).max() <= 0:
            moved_routes.append(route);continue
        line = LineString(route)
        p = shapely.get_coordinates(line.interpolate(np.linspace(0, line.length, max(2, int(np.ceil(line.length))+1))))
        tangent = np.gradient(uniform_filter1d(p, size=7, axis=0, mode='nearest'), axis=0)
        tangent /= np.linalg.norm(tangent, axis=1)[:, None]
        normal = np.column_stack([-tangent[:, 1], tangent[:, 0]])
        # Land side: fewer wet samples 1-5 m out, as the landscape wall fill decides.
        probe = np.arange(1, 5.01, 1)[None, :, None]
        wet = [contains_xy(river, *(p[:, None, :]+sign*normal[:, None, :]*probe).reshape(-1, 2).T).sum() for sign in (1, -1)]
        normal *= 1 if wet[0] < wet[1] else -1
        flags = mud_at(p[:, None, :]+normal[:, None, :]*march[None, :, None])
        # Edge: the first point followed by at least 1 m without mud.
        run = np.cumsum(np.pad(flags, ((0, 0), (0, clear_run))), axis=1)
        clear = (run[:, clear_run-1:clear_run-1+len(march)]-np.pad(run, ((0, 0), (1, 0)))[:, :len(march)]) == 0
        edge = np.where(clear.any(axis=1), march[np.argmax(clear, axis=1)], np.nan)
        inside = depth_inside(p)
        edge[inside <= 0] = 0
        if np.isnan(edge).all():
            moved_routes.append(route);continue
        good = ~np.isnan(edge)
        edge = np.interp(np.arange(len(edge)), np.flatnonzero(good), edge[good])
        offset = uniform_filter1d(median_filter(edge, size=7, mode='nearest'), size=5, mode='nearest')
        offset *= smooth(0, 10, inside)
        moved = p+normal*offset[:, None]
        # Vertices every 2 m inside the core; the original vertices outside it.
        station = np.linspace(0, line.length, len(p))
        keep = np.unique(np.r_[np.arange(0, len(moved), 2), len(moved)-1])
        keep = keep[inside[keep] > 0]
        original = np.asarray(route, dtype=float)
        outside_core = depth_inside(original) <= 0
        merged = sorted([(station[k], moved[k].tolist()) for k in keep] +
                        [(line.project(shapely.Point(q)), q.tolist()) for q in original[outside_core]], key=lambda v: v[0])
        new_route = [q for _, q in merged]
        deep = inside > 10 if (inside > 10).any() else inside > 0
        through = LineString(new_route).intersection(buildings).length
        if through > 1:
            hit = contains_xy(buildings, *(p[:, None, :]+normal[:, None, :]*march[None, :, None]).reshape(-1, 2).T).reshape(len(p), -1)
            first = np.where(hit.any(axis=1), march[np.argmax(hit, axis=1)], np.nan)
            moved_routes.append(route)
            kept.append({'routeIndex': index, 'lengthMetres': round(line.length, 1),
                         'mudEdgeMedianOffsetMetres': round(float(np.median(edge[deep])), 2),
                         'buildingsCrossedByMudEdgeLineMetres': round(float(through), 1),
                         'nearestBuildingMedianOffsetMetres': round(float(np.nanmedian(first[deep])), 2),
                         'shareWithBuildingInsideMudEdge': round(float((first[deep] < edge[deep]).mean()), 2)})
            continue
        moved_routes.append(new_route)
        records.append({'routeIndex': index, 'priorRoute': route,
                        'meanOffsetMetres': round(float(offset[inside > 0].mean()), 2),
                        'maxOffsetMetres': round(float(offset.max()), 2),
                        'maxDistanceFromMudEdgeMetres': round(float(np.abs(offset-edge)[deep].max()), 2)})
    return moved_routes, records, kept


def edge_distances(p, corners):
    """Signed distance of points p (n, 2) from each edge of triangles (n, 3, 2);
    edge i is opposite corner i; positive inside."""
    a, b, d = corners[:, 0], corners[:, 1], corners[:, 2]
    det = (b[:, 0]-a[:, 0])*(d[:, 1]-a[:, 1])-(b[:, 1]-a[:, 1])*(d[:, 0]-a[:, 0])
    u = ((p[:, 0]-a[:, 0])*(d[:, 1]-a[:, 1])-(p[:, 1]-a[:, 1])*(d[:, 0]-a[:, 0]))/det
    v = ((b[:, 0]-a[:, 0])*(p[:, 1]-a[:, 1])-(b[:, 1]-a[:, 1])*(p[:, 0]-a[:, 0]))/det
    weights = np.column_stack([1-u-v, u, v])
    lengths = np.column_stack([np.hypot(*(d-b).T), np.hypot(*(a-d).T), np.hypot(*(b-a).T)])
    return weights*np.abs(det)[:, None]/lengths, weights


def insert_vertices(triangles, xz, todo):
    """Make each vertex in `todo` (in no triangle yet) a mesh vertex.

    The triangle containing it is split in three, or, if the vertex lies on an
    edge (within EDGE_TOL), both triangles on that edge are split in two, so
    the surface is unchanged and no T-junction is made. A vertex within
    EDGE_TOL of a corner is left out of the triangles. Returns the triangles
    and, per vertex, the index of the containing triangle and its weights.
    """
    tree = cKDTree(xz[triangles].mean(axis=1))
    q = xz[todo]
    owner = np.full(len(q), -1);weights = np.zeros((len(q), 3))
    for near in (16, 256):
        open_ = np.flatnonzero(owner < 0)
        if not len(open_):
            break
        _, candidates = tree.query(q[open_], k=near)
        for j in range(near):
            still = owner[open_] < 0
            if not still.any():
                break
            rows, c = open_[still], candidates[still, j]
            _, w = edge_distances(q[rows], xz[triangles[c]])
            ok = (w >= -1e-9).all(axis=1)
            owner[rows[ok]] = c[ok];weights[rows[ok]] = w[ok]
    found = np.flatnonzero(owner >= 0)
    gap, _ = edge_distances(q[found], xz[triangles[owner[found]]])
    on_edge = np.abs(gap) < EDGE_TOL
    n = len(xz)
    edge_key = np.sort(np.stack([triangles[:, [1, 2]], triangles[:, [2, 0]], triangles[:, [0, 1]]], axis=1), axis=2)
    edge_key = edge_key[..., 0]*n+edge_key[..., 1]
    order = np.argsort(edge_key.ravel(), kind='stable');sorted_keys = edge_key.ravel()[order]
    members = {}
    for row, k in enumerate(found):
        if on_edge[row].sum() > 1:
            continue  # at a corner: the vertex already exists there
        t = owner[k];members.setdefault(t, []).append(todo[k])
        for i in np.flatnonzero(on_edge[row]):
            lo, hi = np.searchsorted(sorted_keys, [edge_key[t, i], edge_key[t, i]+1])
            for other in order[lo:hi]//3:
                if other != t:
                    members.setdefault(other, []).append(todo[k])
    added = []
    for t, points in members.items():
        local = [tuple(triangles[t])]
        for p in points:
            for k, corners in enumerate(local):
                gap, _ = edge_distances(xz[p][None], xz[list(corners)][None])
                gap = gap[0]
                if (gap < -EDGE_TOL).any():
                    continue
                near = np.flatnonzero(np.abs(gap) < EDGE_TOL)
                if len(near) == 0:
                    a, b, d = corners;local[k:k+1] = [(a, b, p), (b, d, p), (d, a, p)]
                elif len(near) == 1:
                    o, e1, e2 = (corners[(near[0]+i) % 3] for i in range(3))
                    local[k:k+1] = [(o, e1, p), (o, p, e2)]
                    for m, other in enumerate(local):
                        if m not in (k, k+1) and e1 in other and e2 in other:
                            i = [c for c in range(3) if other[c] not in (e1, e2)][0]
                            o2, f1, f2 = (other[(i+j) % 3] for j in range(3))
                            local[m:m+1] = [(o2, f1, p), (o2, p, f2)]
                            break
                break
        added.extend(local)
    keep = np.ones(len(triangles), bool);keep[list(members)] = False
    return np.vstack([triangles[keep], np.array(added, dtype=triangles.dtype).reshape(-1, 3)]), owner, weights, owner >= 0


def section(X, Z, water, outside, inside, shore, tidal_bank, built_distance, east, context, floor, bed=None):
    """Interpreted bank and bed heights. Works on the 1 m grid (raster distances)
    or on any points (exact distances to the mapped geometry). floor: the silted
    back-river thalweg of the nearest water (data/maps/back-river-beds.json), NaN
    where the nearest water keeps the generic bed. bed: the silted bed at points inside the
    back rivers' regional reaches beyond the network's channels (NaN elsewhere), which they take."""
    # Generic low bank sections elsewhere; the broader grassy east bank on Wall
    # River is informed by the author's c1900 photograph, not the 1948 aerial.
    # The author dates the later engineered embankments to the 1930s.
    wall_east = np.nan_to_num((X-east >= 0) & (X-east < 16)).astype(float)
    wall_east *= smooth(-210, -175, Z)*(1-smooth(300, 355, Z))
    variation = .93 + .07*np.sin(Z*.041)*np.sin(X*.029)
    # Tidal banks take the OS towing-path crest (data/maps/os-tide-levels.json);
    # retained water keeps the earlier 1.65 m interpretive crest.
    crest = (np.where(tidal_bank, tl.CREST, 1.65) + .10*wall_east)*variation
    width = 7 + 7*wall_east
    height = -.1 + (crest+.1)*smooth(0, 3, shore)*(1-smooth(4, width, shore))
    # Back rivers: a silted bed above low water (F2); its bank face starts from the bed edge.
    silted = tidal_bank & ~np.isnan(floor)
    floor = np.where(silted, floor, tl.BED_FLOOR)
    bed_edge = np.where(silted, floor+tl.BACK_RIVER_EDGE, tl.BED_EDGE)
    tidal_bed = np.where(silted, tl.silted_bed(inside, floor, context.get('siltedRamp')), tl.tidal_bed(inside))
    height = np.where(water, np.where(tidal_bank, tidal_bed, .06-.25-.17*np.minimum(inside, 9)), height)
    # Existing site envelopes and road corridors keep their ground datum. These
    # are industrial plots, not evidence for continuous walls along every plot.
    clearance = smooth(0, 3, built_distance)
    height = np.where(water, height, -.1+(height+.1)*clearance)
    # Match Channelsea's exposed shelves at its existing water datum. The GIS
    # remains the low-water route anchor, not a claimed high-water survey.
    sediment = tidal_bank * (1-smooth(4.5,7.5,outside)) * clearance
    shelf = tl.tidal_shelf(shore, crest, bed_edge)
    height = np.where(~water, height*(1-sediment)+shelf*sediment, height)
    # OS mud flats between the low-water outline and the high-water mark.
    # Boundary included: a mesh vertex on a traced high-water line takes the flat's rim.
    flat = shapely.intersects_xy(tl.flats, X, Z) & ~water
    height = np.where(flat, tl.mud_flat(shore), height)
    # Up to just above high water at a traced high-water line (tide_levels.flat_rim).
    height[flat] = tl.flat_rim(height[flat], shapely.points(X[flat], Z[flat]))
    flat_height = height.copy()
    sediment = np.where(flat, 1., sediment)
    # Local photograph study: a worn path on a raised grassy east bank, with
    # timber details rendered separately. Metric section remains an estimate.
    support=np.zeros_like(height)
    vista=context['vista']
    if vista is not None:
        bank=vista['bank']
        offset=X-east
        profile=np.interp(np.nan_to_num(offset,nan=-100),
                          [0,1,4.8,8.5,15,20],[0,.65,bank['crestHeight'],bank['crestHeight'],bank['crestHeight'],-.1])
        # The face starts at the bed edge (the silted Wall River edge since F2).
        profile += bed_edge*(1-np.clip(np.nan_to_num(offset, nan=-100), 0, 1))
        blend=smooth(bank['zStart']-10,bank['zStart'],Z)*(1-smooth(bank['zEnd'],bank['zEnd']+10,Z))
        active_bank=(offset>=0)&(offset<=20)&(~water)
        height=np.where(active_bank,height*(1-blend)+profile*blend,height)
        # Photograph path and mapped continuation must meet without a floating
        # ribbon or a vertical end. Feather earth into the surrounding bank.
        for connection in context['vistaConnections']:
            route=connection['route'];radius=connection['width']/2
            for a,b in zip(route,route[1:]):
                dx,dz=b[0]-a[0],b[2]-a[2]
                t=np.clip(((X-a[0])*dx+(Z-a[2])*dz)/(dx*dx+dz*dz),0,1)
                distance=np.hypot(X-a[0]-t*dx,Z-a[2]-t*dz)
                weight=(1-smooth(radius+.2,radius+4,distance))*(~water)
                target=a[1]+t*(b[1]-a[1])
                height=height*(1-weight)+target*weight
                support=np.maximum(support,weight)
        # Grass above the muddy bank face, including the raised photo section.
        sediment*=1-smooth(tl.HIGH-.1,tl.HIGH+.4,height)
    # The old patch tapers to -.1 at its boundary. Match that seam precisely.
    x0, z0, x1, z1 = context['coreBounds']
    dx, dz = np.maximum(np.maximum(x0-X, X-x1), 0), np.maximum(np.maximum(z0-Z, Z-z1), 0)
    core_distance = np.hypot(dx, dz)
    # Tidal channels meet the core below low water (tide_levels.seam), so the
    # seam does not dam them; land and still water meet it at -0.1 as before.
    inside_tidal = context['insideTidal'] if context.get('insideTidal') is not None else inside*tidal_bank
    edge = tl.seam(inside_tidal)
    # On an OS mud flat both meshes meet on the flat (tide_levels.flat_seam and flat_rim; land()
    # passes shore as the exact distance plus SHORE_OFFSET_M).
    edge = np.where(flat, flat_height, edge)
    height = edge+(height-edge)*smooth(0, 3, core_distance)
    # A tiny offset prevents coplanar flicker where the outer apron meets the
    # surrounding ground; the detailed core itself remains untouched.
    height += .004*smooth(0, 1, core_distance)
    height,ditch_mud,marsh_active=apply_sections(X,Z,height)
    # Mill/bridge decks stay above the channel. Do not leave a terrain plug
    # beneath a reviewed passage after generic bank or ditch shaping.
    passage_mask=contains_xy(context['passages'],X,Z)
    height[passage_mask]=np.minimum(height[passage_mask],-.7)
    tidal_passage=contains_xy(context['tidalPassages'],X,Z)
    height[tidal_passage]=np.minimum(height[tidal_passage],tl.SEAM_BED)
    # Passages between back rivers take their thalweg (back-river-beds.json passages).
    silted_passage=contains_xy(context['siltedPassages'],X,Z)
    height[silted_passage]=floor[silted_passage]
    if bed is not None:
        regional=np.isfinite(bed)
        height[regional]=bed[regional];sediment[regional]=1
    sediment=np.maximum(sediment*(1-smooth(tl.HIGH,tl.CREST,height)),ditch_mud)
    return height, sediment, support, marsh_active, core_distance


def build():
    plan = json.loads((OUT/'ground-plan.json').read_text())
    # Factory coverage extends beyond the old western clip to the Old Lea.
    west = ROOT/'data/maps/factory-west-context.json'
    if west.exists():
        plan['rivers'].extend(json.loads(west.read_text())['rivers'])
    core = json.loads((OUT/'river-terrain.json').read_text())
    infrastructure = json.loads((OUT/'infrastructure.json').read_text())
    channels = {r['id']: unary_union([Polygon(p[0], p[1:]) for p in r['polygons']])
                for r in plan['rivers']}
    connections=reviewed_connections(plan['rivers'])
    passages=connection_geometry(connections)
    river = unary_union(list(channels.values())+[passages])
    # Author's hydrological distinction: the Old Lea/navigation above the
    # Limehouse Cut lock retains water; river channels elsewhere share the tide.
    retained_ids = {18, 22, 10018, 10022}
    east_context=json.loads((ROOT/'data/maps/east-channelsea-context-alignment.json').read_text())
    isolated_ids={r['id'] for r in east_context['additionalRivers']}
    # The OS maps disconnected moat pools and a drain, not their hydraulic links.
    # Show these at the shared illustrative low datum without animating a tide.
    # Above the OS tidal limit at Abbey Mill (data/maps/os-tide-levels.json) the
    # Channelsea is still water at the retained level, like the Old Lea.
    head_ids = tl.ABOVE_TIDAL_LIMIT
    tidal = unary_union([g for key,g in channels.items() if key not in retained_ids|isolated_ids|head_ids]+[connection_geometry(connections,tidal_only=True)])
    patch = box(*core['bounds'])
    # Mesh shoreline: the mapped outline with gaps under 0.5 m between channel
    # pieces closed (source-window joins, e.g. at x = -1050) and water slivers
    # under 0.5 m wide removed (clip tails). Neither is a channel or a bank.
    mesh_water = river.buffer(SLIVER_M, join_style='mitre').buffer(-2*SLIVER_M, join_style='mitre').buffer(SLIVER_M, join_style='mitre')
    # Sample only a narrow corridor at runtime; the generation grid is temporary.
    minx, minz, maxx, maxz = np.array(river.bounds).astype(int) + [-18, -18, 18, 18]
    x, z = np.arange(minx, maxx+1), np.arange(minz, maxz+1)
    X, Z = np.meshgrid(x, z)
    # The raster of the mapped outline sets the mesh extent and the bed.
    water = contains_xy(river, X, Z)
    outside = distance_transform_edt(~water)
    _, nearest = distance_transform_edt(~water, return_indices=True)
    tidal_cells = contains_xy(tidal, X, Z)
    tidal_bank = tidal_cells[nearest[0],nearest[1]]
    # Silted back-river thalweg (data/maps/back-river-beds.json, scripts/back_river_profile.py): rising
    # along the water from the outlet at Three Mills to the heads at the Old Lea and the Navigation,
    # over the network's channels and the regional reaches beyond them alike; each point takes its
    # nearest water's.
    silted_ids = set(tl.back_rivers['passages']['raised'])
    silted_connections = [r for r in connections['connections'] if r['id'] in silted_ids]
    back = back_river_profile()
    biz, bix = back.cells(X, Z)
    on_grid = (X == back.X[biz, bix]) & (Z == back.Z[biz, bix])
    silted_cell = on_grid & back.silted[biz, bix]
    floor_cells = np.where(silted_cell, back.floor[biz, bix], np.nan)
    floor_bank = floor_cells[nearest[0], nearest[1]]
    inside = distance_transform_edt(water)
    shore = gaussian_filter(outside-inside, .65)
    # East edge of Wall River (channel 1) along each quarter-metre row; whole
    # metre rows are the grid rows.
    wall = channels[1]
    rows = np.arange(minz, maxz+.125, .25)
    east_rows = []
    for zz in rows:
        cut = wall.intersection(LineString([(minx, zz), (maxx, zz)]))
        east_rows.append(cut.bounds[2] if not cut.is_empty else np.nan)
    east_rows = np.array(east_rows)

    def east_at(zv):
        f = np.clip((zv-minz)/.25, 0, len(rows)-1)
        i = np.minimum(np.floor(f).astype(int), len(rows)-2)
        t = f-i
        between = east_rows[i]*(1-t)+east_rows[i+1]*t
        return np.where(t < 1e-9, east_rows[i], np.where(t > 1-1e-9, east_rows[i+1], between))
    east = east_at(z.astype(float))[:, None]
    # Existing site envelopes and road corridors keep their ground datum.
    sites = unary_union([Polygon(p[0], p[1:]) for s in plan['sites']+east_context['additionalYards'] for p in s['polygons']])
    roads = unary_union([LineString(r['route']).buffer(r['width']/2+2)
                         for r in infrastructure['roads']])
    built = contains_xy(sites.union(roads), X, Z)
    vista_path=ROOT/'data/maps/wall-river-vista.json'
    context = {'vista': json.loads(vista_path.read_text()) if vista_path.exists() else None,
               'vistaConnections': json.loads((OUT/'high-street-frontages.json').read_text())['vista']['connections']
               if vista_path.exists() else [],
               'coreBounds': core['bounds'], 'passages': passages,
               'tidalPassages': connection_geometry({'connections': [r for r in connections['connections'] if r['id'] not in silted_ids]}, tidal_only=True),
               'siltedPassages': connection_geometry({'connections': silted_connections})}
    # Exact distance into tidal water for grid nodes at the core boundary, where
    # this mesh and the core (0.4 m grid) must meet at the same seam level.
    cx0, cz0, cx1, cz1 = core['bounds']
    core_gap = np.hypot(np.maximum(np.maximum(cx0-X, X-cx1), 0), np.maximum(np.maximum(cz0-Z, Z-cz1), 0))
    inside_tidal = inside*tidal_bank
    near = (core_gap < 3.5) & water
    pts = shapely.points(X[near], Z[near])
    inside_tidal[near] = np.where(shapely.covers(tidal, pts), shapely.distance(pts, tidal.boundary), 0)
    context['insideTidal'] = inside_tidal
    # A silted bed reaches its thalweg on the centreline of a channel narrower than twice its ramp:
    # the ramp is the deepest point within the ramp distance (the local half-width), at least 1 m.
    ramp = tl.BACK_RIVER_SECTION['rampMetres']
    context['siltedRamp'] = np.clip(maximum_filter(inside, size=2*ramp+1), 1, ramp)
    # Raster section: channel beds and the extent of the mesh. Land heights are
    # recomputed below from exact distances to the mapped shoreline.
    height, sediment, support, marsh_active, core_distance = section(
        X, Z, water, outside, inside, shore, tidal_bank, distance_transform_edt(~built), east, context, floor_bank,
        np.where(silted_cell & ~water, back.bed[biz, bix], np.nan))
    context['insideTidal'] = context['siltedRamp'] = None
    # Grid points in a closed join gap are channel bed: give them the mean bed
    # of their mapped-water neighbours. Every other bed point is unchanged.
    gap = contains_xy(mesh_water, X, Z) & ~water
    if gap.any():
        h, w, m = np.pad(height, 1), np.pad(sediment, 1), np.pad(water, 1).astype(float)
        shifted = lambda a, dz, dx: a[1+dz:a.shape[0]-1+dz, 1+dx:a.shape[1]-1+dx]
        moves = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        count = sum(shifted(m, *d) for d in moves)
        height[gap] = (sum(shifted(h*m, *d) for d in moves)/np.maximum(count, 1))[gap]
        sediment[gap] = (sum(shifted(w*m, *d) for d in moves)/np.maximum(count, 1))[gap]
    water = contains_xy(mesh_water, X, Z)
    # The low-water stream (back-river-beds.json lowWaterStream): the Lea's water running down the
    # silted beds from their heads when the tide is out, level across the channel at the thalweg plus
    # its depth (none on the Pudding Mill River), never below low water; through the regional reaches
    # to the Old Lea as well. The scene draws the higher of it and the tide. Its mesh covers the 1 m
    # bed cells it wets: the network's drawn bed on its channels, the shared section beyond them.
    stream_bed = back.bed.copy()
    mine = silted_cell & water
    stream_bed[biz[mine], bix[mine]] = height[mine]
    stream_wet = back.silted & (stream_bed < back.stream-.005)
    corner = lambda a: (a[:-1, :-1], a[:-1, 1:], a[1:, :-1], a[1:, 1:])
    stream_cells = np.logical_and.reduce(corner(back.silted)) & np.logical_or.reduce(corner(stream_wet))
    bw = back.X.shape[1]
    a = (np.arange(back.X.size).reshape(back.X.shape)[:-1, :-1])[stream_cells]
    stream_triangles = np.stack([a, a+bw, a+1, a+1, a+bw, a+bw+1], axis=1).reshape(-1, 3)
    stream_nodes, stream_indices = np.unique(stream_triangles, return_inverse=True)
    stream_positions = np.column_stack([back.X.ravel()[stream_nodes], back.stream.ravel()[stream_nodes], back.Z.ravel()[stream_nodes]]).astype('<f4')
    assert np.isfinite(stream_positions).all() and (stream_positions[:, 1] >= tl.LOW).all()
    ditch_raw,marsh,ditches,ditch_parts,_=ditch_geometry()
    # At working plots the bank cannot occupy a wide grass slope. A narrow
    # retaining edge holds the same interpreted crest; material/design unresolved.
    # The Channelsea head above Abbey Mill is still water but a working, navigable
    # frontage: its works keep the retaining edges they had while it was drawn tidal.
    head = unary_union([g for key,g in channels.items() if key in head_ids])
    retaining=river.boundary.intersection(tidal.union(head).buffer(.01)).intersection(sites.buffer(3)).difference(roads)
    wall_routes=[list(segmentize(g,4).coords) for g in getattr(retaining,'geoms',[retaining]) if g.geom_type=='LineString' and g.length>1]
    # River walls the OS draws (data/maps/os-river-walls.json): the shoreline along each traced
    # line becomes a retaining route too, where the plot rule above has not already made one.
    os_walls=json.loads((ROOT/'data/maps/os-river-walls.json').read_text());os_wall_records=[]
    # A traced wall may carry a street along its top (Marshgate Lane); only the road bridges interrupt it.
    bridge_spans=unary_union([LineString(b['route']).buffer(b['width']/2+2) for b in infrastructure['roadBridges']])
    for w in os_walls['walls']:
        near=LineString(w['line']).buffer(os_walls['toleranceMetres'],cap_style=2)
        shore=river.boundary.intersection(tidal.buffer(.01)).intersection(near).difference(bridge_spans).difference(retaining.buffer(.05))
        shore=linemerge(shore) if shore.geom_type=='MultiLineString' else shore
        added=[list(segmentize(g,4).coords) for g in getattr(shore,'geoms',[shore]) if g.geom_type=='LineString' and g.length>1]
        os_wall_records.append({'id':w['id'],'routeIndices':list(range(len(wall_routes),len(wall_routes)+len(added))),
                                'lengthMetres':round(sum(LineString(r).length for r in added),2),'tracedLengthMetres':round(LineString(w['line']).length,2)})
        wall_routes+=added
    factories = json.loads((OUT/'factory-buildings.json').read_text())
    frontages = json.loads((OUT/'high-street-frontages.json').read_text())
    buildings = unary_union([Polygon(q['outer'], q['holes']) for b in factories['buildings']+frontages['buildings'] for q in b['renderPolygons']] +
                            [Polygon(b['footprint']) for b in plan['neighbourhood']['houses']+plan['neighbourhood']['terraces']])
    moved_routes, relocated, not_relocated = relocate_core_walls(wall_routes, core, river, buildings)
    if APPLY_CORE_WALL_RELOCATION:
        wall_routes = moved_routes
    else:
        for record in relocated:
            record['proposedRoute'] = moved_routes[record['routeIndex']]

    # Land section from exact distances to the mapped geometry, not its 1 m raster.
    river_distance, tidal_distance = Distance(mesh_water), Distance(tidal)
    built_distance = Distance(sites.union(roads))

    def land(px, pz):
        pts = shapely.points(px, pz)
        d = river_distance(pts)
        near_tidal = tidal_distance(pts) <= d+2*SLIVER_M
        # The sections were set out on the 1 m raster, whose node-to-node
        # distances ran on average SHORE_OFFSET_M (shoreline) and BUILT_OFFSET_M
        # (sites, roads) beyond the exact distance. Keep that placement.
        b = built_distance(pts)
        ix = np.clip(np.round(px-minx).astype(int), 0, len(x)-1);iz = np.clip(np.round(pz-minz).astype(int), 0, len(z)-1)
        h, s, _, _, _ = section(px, pz, np.zeros(len(px), bool), d+SHORE_OFFSET_M, np.zeros(len(px)), d+SHORE_OFFSET_M,
                                near_tidal, np.where(b > 0, b+BUILT_OFFSET_M, 0), east_at(pz), context, floor_bank[iz, ix],
                                back.bed_at(px, pz))
        return h, s, d+SHORE_OFFSET_M

    # Keep complete 1 m cells, excluding the core at its integer boundaries.
    active = ((outside < 21) | (support>0) | marsh_active | contains_xy(tl.flats.buffer(21), X, Z)) & (core_distance > 0)
    cells = active[:-1, :-1] | active[1:, :-1] | active[:-1, 1:] | active[1:, 1:]
    cx, cz = X[:-1, :-1]+.5, Z[:-1, :-1]+.5
    x0, z0, x1, z1 = core['bounds']
    cells &= ~((cx > x0) & (cx < x1) & (cz > z0) & (cz < z1))
    a = (np.arange(X.size).reshape(X.shape)[:-1, :-1])[cells]
    grid_triangles = np.stack([a, a+len(x), a+1, a+1, a+len(x), a+len(x)+1], axis=1).reshape(-1, 3)
    # Vertex order of the former all-grid mesh is kept (river-system and
    # landscape builds index it); shore-following vertices are appended.
    used = np.unique(grid_triangles)

    # Shore-following bands between offset lines of the mapped shoreline.
    shoreline = grid_noded(mesh_water)
    outer = grid_noded(mesh_water.buffer(RING_OFFSETS[-1], quad_segs=8))
    offsets = [shoreline]+[segmentize(mesh_water.buffer(d, quad_segs=8), ALONG_SHORE) for d in RING_OFFSETS[1:-1]]+[outer]
    pieces = []
    for inner_ring, outer_ring in zip(offsets, offsets[1:]):
        pieces.extend(polygons(outer_ring.difference(inner_ring).difference(patch)))
    # Grid cells cut by the shoreline or the 8 m line keep only their part
    # outside the bands, triangulated on the shared vertices.
    ci, cj = np.nonzero(cells)
    boxes = shapely.box(x[cj], z[ci], x[cj]+1, z[ci]+1)
    cell_tree = shapely.STRtree(boxes)
    cut_shore = np.zeros(len(boxes), bool);cut_outer = np.zeros(len(boxes), bool)
    def short_pieces(g):
        out = []
        for line in shapely.get_parts(g.boundary):
            c = shapely.get_coordinates(line)
            out.extend(LineString(c[i:i+9]) for i in range(0, len(c)-1, 8))
        return out
    cut_shore[cell_tree.query(short_pieces(shoreline), predicate='intersects')[1]] = True
    cut_outer[cell_tree.query(short_pieces(outer), predicate='intersects')[1]] = True
    wet = contains_xy(mesh_water, x[cj]+.5, z[ci]+.5)
    banded = contains_xy(outer, x[cj]+.5, z[ci]+.5) & ~wet
    whole = ~cut_shore & ~cut_outer & ~banded
    for part in shapely.intersection(boxes[cut_shore], shoreline):
        pieces.extend(p for p in polygons(part) if p.area > 1e-9)
    for part in shapely.difference(boxes[cut_outer], outer):
        pieces.extend(p for p in polygons(part) if p.area > 1e-9)
    tri = shapely.get_parts(shapely.constrained_delaunay_triangles(np.array(pieces, dtype=object)))
    coords = shapely.get_coordinates(tri).reshape(-1, 4, 2)[:, :3]
    # Clipping at the core boundary can leave last-digit noise; snap to it.
    for k, edge in ((0, x0), (0, x1), (1, z0), (1, z1)):
        near = np.abs(coords[..., k]-edge) < MERGE_TOL
        coords[..., k][near] = edge
    flat = coords.reshape(-1, 2)
    rounded = np.round(flat)
    on_node = (np.abs(flat-rounded) < MERGE_TOL).all(axis=1)
    flat[on_node] = rounded[on_node]
    node = ((flat[:, 1]-minz)*len(x)+(flat[:, 0]-minx)).astype(np.int64)
    slot = np.searchsorted(used, node).clip(0, len(used)-1)
    on_node &= used[slot] == node
    # Merge the copies of each new vertex (shared by neighbouring pieces).
    free, free_inverse = np.unique(flat[~on_node], axis=0, return_inverse=True)
    pairs = cKDTree(free).query_pairs(MERGE_TOL, output_type='ndarray')
    graph = coo_matrix((np.ones(len(pairs)), (pairs[:, 0], pairs[:, 1])), shape=(len(free), len(free)))
    _, label = connected_components(graph, directed=False)
    first = np.empty(label.max()+1, dtype=np.int64)
    first[label[::-1]] = np.arange(len(free))[::-1]  # lowest index per merged vertex
    new_xz = free[first]
    vertex = np.empty(len(flat), dtype=np.int64)
    vertex[on_node] = slot[on_node]
    vertex[~on_node] = len(used)+label[free_inverse.ravel()]
    shore_triangles = vertex.reshape(-1, 3)
    grid_xz = np.column_stack([X.ravel()[used], Z.ravel()[used]]).astype(float)
    xz = np.vstack([grid_xz, new_xz])
    # Triangles from the grid cells that are neither cut nor inside a band.
    keep = np.zeros(cells.shape, bool)
    keep[ci[whole], cj[whole]] = True
    a = (np.arange(X.size).reshape(X.shape)[:-1, :-1])[keep]
    kept = np.searchsorted(used, np.stack([a, a+len(x), a+1, a+1, a+len(x), a+len(x)+1], axis=1).reshape(-1, 3))
    triangles = np.vstack([kept, shore_triangles])
    # Orient every triangle like the grid's, and drop slivers of zero area.
    p0, p1, p2 = xz[triangles[:, 0]], xz[triangles[:, 1]], xz[triangles[:, 2]]
    cross = (p1[:, 0]-p0[:, 0])*(p2[:, 1]-p0[:, 1])-(p1[:, 1]-p0[:, 1])*(p2[:, 0]-p0[:, 0])
    triangles = triangles[np.abs(cross) > 1e-9]
    cross = cross[np.abs(cross) > 1e-9]
    triangles[cross > 0] = triangles[cross > 0][:, [0, 2, 1]]

    # Heights: channel-bed grid vertices keep the raster bed; every other
    # vertex takes the bank section at its exact distance from the shoreline.
    grid_wet = water.ravel()[used]
    y = np.empty(len(xz));silt = np.empty(len(xz));distance = np.zeros(len(xz))
    y[:len(used)][grid_wet] = height.ravel()[used][grid_wet]
    silt[:len(used)][grid_wet] = sediment.ravel()[used][grid_wet]
    dry = np.r_[~grid_wet, np.ones(len(new_xz), bool)]
    y[dry], silt[dry], distance[dry] = land(xz[dry, 0], xz[dry, 1])
    # Former grid vertices inside the bands become vertices of the band mesh,
    # on its surface, so every vertex (and every vertex index of the former
    # grid) still names a point of the drawn ground.
    referenced = np.zeros(len(xz), bool);referenced[triangles.ravel()] = True
    inner = np.flatnonzero(~referenced)
    before = triangles
    triangles, owner, weights, found = insert_vertices(before, xz, inner)
    for values in (y, silt, distance):
        values[inner[found]] = (weights[found]*values[before[owner[found]]]).sum(axis=1)
    # On an OS mud flat they take their own section instead (task D): a band triangle can reach
    # across the traced high-water line to marsh beyond it, which left a hole in the flat's rim.
    on_flat = inner[found][shapely.intersects_xy(tl.flats, *xz[inner[found]].T) & ~contains_xy(mesh_water, *xz[inner[found]].T)]
    y[on_flat], silt[on_flat], distance[on_flat] = land(xz[on_flat, 0], xz[on_flat, 1])
    positions = np.column_stack([xz[:, 0], y, xz[:, 1]]).astype('<f4')
    # Slivers that float32 rounding makes flat are dropped (zero area); none may reverse.
    stored = positions[triangles][:, :, [0, 2]].astype(float)
    turn = (stored[:, 1, 0]-stored[:, 0, 0])*(stored[:, 2, 1]-stored[:, 0, 1])-(stored[:, 1, 1]-stored[:, 0, 1])*(stored[:, 2, 0]-stored[:, 0, 0])
    triangles, turn = triangles[np.abs(turn) > 1e-8], turn[np.abs(turn) > 1e-8]
    assert (turn < 0).all(), f'{int((turn > 0).sum())} triangles reversed by float32 rounding'
    indices = triangles.astype('<u4').ravel()
    referenced[:] = False;referenced[triangles.ravel()] = True
    # Vertex colour distinguishes submerged/silty edges from the grassy crest.
    grass = np.array([1., 1., 1.])
    silt_colour = np.array([.70, .65, .54])
    green = smooth(.2, 2.8, distance)[:, None]
    # The OS mud flats are silt out to the high-water mark, however far from the channel.
    green[shapely.intersects_xy(tl.flats, positions[:, 0], positions[:, 2])] = 0
    colors = np.clip((silt_colour*(1-green)+grass*green)*255, 0, 255).astype('uint8')
    positions.tofile(OUT/'river-network.f32')
    stream_positions.tofile(OUT/'river-network.stream.f32')
    stream_indices.astype('<u4').tofile(OUT/'river-network.stream.u32')
    indices.tofile(OUT/'river-network.u32')
    colors.tofile(OUT/'river-network.rgb')
    (np.clip(silt,0,1)*255).astype('uint8').tofile(OUT/'river-network.silt')
    landcover=np.column_stack([contains_xy(sites,positions[:,0],positions[:,2]),
        contains_xy(Polygon(plan['neighbourhood']['garden']['footprint']),positions[:,0],positions[:,2])])
    (landcover.astype('uint8')*255).tofile(OUT/'river-network.cover')
    # Remove the flat floor below channels as well as the existing terrain patch.
    ground = box(-2750, -2750, 2750, 2750).difference(river.buffer(14).union(tl.flats.buffer(14)).union(patch).union(marsh))
    # Confine the animated surface to river-side shelves. A whole-scene plane
    # would flood the lower marsh through the back of its embankments.
    core_beds = unary_union([Polygon(p[0], p[1:]) for p in plan['bankStudies']])
    retained = unary_union([g for key,g in channels.items() if key in retained_ids|isolated_ids|head_ids])
    tide_envelope = tidal.buffer(TIDE_SHELF_M).union(core_beds.intersection(patch))
    tide_envelope = tide_envelope.difference(sites.union(roads).difference(tidal))
    # OS mud flats out to the high-water mark (data/maps/os-tide-levels.json).
    tide_envelope = tide_envelope.union(tl.flats.difference(roads))
    tide_envelope = tide_envelope.difference(marsh.union(ditches).union(retained))
    lock_gaps=unary_union([Polygon(p[0],p[1:]) for r in connections['connections']
        if not r['tidalDisplay'] for p in r['polygons']]).difference(unary_union(list(channels.values())))
    tide_envelope=tide_envelope.difference(lock_gaps)
    meta = {
        'positionFile': 'river-network.f32', 'indexFile': 'river-network.u32', 'colorFile': 'river-network.rgb',
        'sedimentFile': 'river-network.silt',
        'landcoverFile': 'river-network.cover',
        'waterLevel':core['waterLevel'],
        'tide':{'low':tl.LOW, 'high':tl.HIGH,
                'cycleSeconds':90, 'polygons':rings(tide_envelope),
                'register':'data/maps/os-tide-levels.json',
                'evidence':'High and low water of ordinary tides from the OS five-foot plan and Trinity High Water (data/maps/os-tide-levels.json): high 3.41 m ODN, low about OD, rising and falling in step over the river-side shelves and the OS mud flats. Not a tide prediction or hydraulic simulation; excludes the retained Old Lea, the Channelsea above the tidal limit at Abbey Mill and the marsh drains.'},
        'lowWaterStream':{'positionFile':'river-network.stream.f32','indexFile':'river-network.stream.u32',
                          'vertices':len(stream_positions),'triangles':len(stream_triangles),
                          'depthMetres':{str(k):v for k,v in sorted(tl.BACK_RIVER_STREAM.items())},
                          'levelRange':[float(stream_positions[:,1].min()),float(stream_positions[:,1].max())],
                          'register':'data/maps/back-river-beds.json',
                          'evidence':'The Lea running down the silted back rivers when the tide is out: a foot over the thalweg (the author), sloping from the heads to Three Mills; none on the Pudding Mill River. Drawn still; the tide covers it as it rises. An estimate, not a hydraulic calculation.'},
        'backRiverBeds':{'register':'data/maps/back-river-beds.json',
                         'registerSha256':hashlib.sha256(tl.BACK_RIVER_REGISTER.read_bytes()).hexdigest(),
                         'channelIds':sorted(tl.BACK_RIVER_ABOVE),'aboveProfileMetres':{str(k):v for k,v in sorted(tl.BACK_RIVER_ABOVE.items())},
                         'outletSceneY':tl.BACK_RIVER_PROFILE['outlet']['sceneY'],'headSceneY':tl.BACK_RIVER_PROFILE['headSceneY'],'maxFloorSceneY':tl.BACK_RIVER_MAX_FLOOR,
                         'edgeAboveFloorMetres':tl.BACK_RIVER_EDGE,'siltedPassages':sorted(silted_ids),
                         'waterPolygons':rings(back.geometry),'unreachedCells':back.unreached,
                         'evidence':'Estimated silted beds of the Stratford back rivers, rising from just below low water at Three Mills to shoals at the heads where they leave the Old Lea and the Navigation; the Pudding Mill River worst (data/maps/back-river-beds.json). Not a survey.'},
        'retainingEdges':{'routes':wall_routes,'crestHeight':tl.CREST,'baseHeight':tl.WALL_BASE,'width':WALL_WIDTH,
                          'evidence':'Interpretive flood-retaining edges where tidal river banks (and the Channelsea head above Abbey Mill) meet GIS industrial plots. Presence, material and individual sections require photograph/engineering-plan verification. Not the 1930s concrete embankments.',
                          'osRiverWalls':{'register':'data/maps/os-river-walls.json','walls':os_wall_records,
                                          'method':f"the mapped shoreline within {os_walls['toleranceMetres']} m of each OS-traced wall line (inside the tidal channels, outside road bridges and existing routes; a street may run along the wall top)"},
                          'coreWallRelocation':{'applied':APPLY_CORE_WALL_RELOCATION,
                              'notAppliedReason':'the core terrain (river-terrain, 0.4 m grid) has no mesh edges on the moved wall lines, so the main-landscape wall fill raises ground cells on the water side of the wall (teeth up its face, seen in a scratch rebuild) and its land-side test (wet samples 1-5 m out) becomes a tie; move them once the core mesh carries the wall lines or the landscape builder clears core wall faces',
                              'routes':relocated,'notRelocated':not_relocated,
                              'notRelocatedReason':'mapped factory buildings stand inside the core channel section along these walls, many within 1-2 m of the GIS outline, and the core terrain mud runs under them; the mud edge would put the wall through buildings, so the walls stay on the GIS outline (the building frontage is the real bank line there; the core channel section needs trimming to it in the river-terrain build)',
                              'method':'routes inside the detailed core moved from the GIS outline to the landward edge of the core terrain exposed tidal mud (river-terrain.rgba, the same test as the main landscape uses), found along the land-side normal every 1 m, median-filtered over 7 m and averaged over 5 m; tapered to zero within 10 m of the core boundary; vertices every 2 m; proposedRoute is the bank-line route, priorRoute the route in use (applied only if APPLY_CORE_WALL_RELOCATION)',
                              'evidence':'Mapped: the GIS outline and the industrial plot the wall fronts. Estimated: the core channel section (river-terrain build, an interpretation of Figure 2.4 and the author), so the new line is the interpreted bank line of that section, not a surveyed wall. The former routes stood on the low-water line about 7.5 m inside that section, on preserved tidal mud.'}},
        'marshDitches':{'features':[{**f,'renderPolygons':rings(g),'retainedAreaM2':round(g.area,2)} for f,g in zip(ditch_raw['features'],ditch_parts)],
                        'waterPolygons':rings(ditches.difference(patch)), 'marshPolygons':rings(marsh),
                        'levels':ditch_raw['levels'],'policy':ditch_raw['policy']},
        'retainedWaterChannelIds':sorted(retained_ids),
        'aboveTidalLimitChannelIds':sorted(head_ids),
        'isolatedWaterChannelIds':sorted(isolated_ids),
        'reviewedConnections':connections,
        'isolatedWaterEvidence':'OS-mapped separate moat pools and eastern drain. Flat illustrative low water only; hydraulic connection and historical water levels are unresolved.',
        'tidalChannelIds':sorted(set(channels)-retained_ids-isolated_ids-head_ids),
        'tidalEvidence':'Author correction: tidal margins throughout except Old Lea north of the Limehouse Cut lock. GIS ids 18,22,10018,10022 identify that retained reach; Bow Creek id 0 remains tidal. Widths and sections inferred, not reconstructed tidal hydraulics.',
        'vertices': len(positions), 'triangles': len(triangles), 'step': 1, 'baseGround': rings(ground),
        'bankMesh': {'method': 'land within 8 m of the mapped channels is triangulated (constrained Delaunay) in bands between offset lines of the mapped shoreline; channel beds and ground beyond 8 m keep the 1 m grid, whose cells cut by the shoreline or the 8 m line are clipped and share their vertices with the bands',
                     'ringOffsetsMetres': RING_OFFSETS, 'alongShoreSpacingMetres': ALONG_SHORE,
                     'meshShoreline': {'method': f'the GIS outline closed and then opened by {SLIVER_M} m (mitred), so gaps under {2*SLIVER_M} m between channel pieces and water slivers under {2*SLIVER_M} m wide do not make banks; the drawn water polygons are unchanged',
                                       'gapsClosedM2': round(mesh_water.difference(river).area, 2),
                                       'sliversIgnoredM2': round(river.difference(mesh_water).area, 2)},
                     'gridVertices': len(used), 'shoreVertices': len(new_xz),
                     'gridVerticesInsertedInBands': int(found.sum()),
                     'gridVerticesNote': 'every vertex of the former 1 m grid keeps its index and position; inside the bands it is inserted into the band triangle that contains it, at that triangle\'s height, so the surface is unchanged',
                     'unreferencedVertices': int((~referenced).sum()),
                     'evidence': 'Mapped: the GIS channel outlines (the shoreline and every offset line follow them). Estimated: all bank and bed heights. They use the same interpreted sections as before; land distances are now exact distances to the mapped shoreline and to sites and roads, plus the mean offset of the former 1 m raster distances '
                                 f'({SHORE_OFFSET_M} m and {BUILT_OFFSET_M} m), so each section keeps its former placement but no longer steps row by row with the raster.'},
        'channels': [{'id': r['id'], 'name': 'Three Mills Wall River' if r['id'] == 1 else r['name'],
                      'sourceName': r['name']} for r in plan['rivers']],
        'source': 'data/maps/panorama-source-context.geojson; supplied Lower_River_Lea.geojson and Industry_1893-95.geojson; data/maps/east-channelsea-context-alignment.json for OS-traced moat/drain pools and local east-bank reconciliation',
        'planSha256': hashlib.sha256((OUT/'ground-plan.json').read_bytes()).hexdigest(),
        'evidence': 'Author identifies Wall River west of Mill Mead and marsh below rivers at high tide. Wall River photo supplies the local raised bank/path section; data/maps/marsh-ditches.json supplies map-traced drains. Heights, widths, bed depths and retaining-edge sections remain inferred, not a surveyed wall inventory.',
        'chronology': 'The author dates later engineered embankments to the 1930s. EAW014561 (16 April 1948) is comparison evidence only; its embankments, channel alterations and factory forms are not backdated into this scene. Prescott Cut remains excluded.',
        'limitations': ['Generic bank sections are a terrain scaffold, not a surveyed reconstruction.',
                       'City Mills masonry banks, openings and crossings visible in the circa 1897 photograph still require registered plan tracing.',
                       'Source GIS industry polygons are site parcels, not individual building footprints.'],
        'heightRange': [float(positions[:, 1].min()), float(positions[:, 1].max())],
    }
    assert np.isfinite(positions).all()
    assert not np.any((positions[:, 0] > x0) & (positions[:, 0] < x1) &
                      (positions[:, 2] > z0) & (positions[:, 2] < z1))
    assert np.max(indices) < len(positions)
    assert ground.intersection(river).area < .001
    # Beds lie below the still-water datum, except the silted back rivers (back-river-beds.json),
    # which lie between low and high water.
    assert np.all(height[water & (core_distance > 3) & np.isnan(floor_bank)] < .06)
    assert np.all(height[water & ~np.isnan(floor_bank)] < tl.HIGH)
    (OUT/'river-network.json').write_text(json.dumps(meta, separators=(',', ':'))+'\n')
    print(f'River network: {len(channels)} source features, {len(positions):,} vertices '
          f'({int(referenced.sum()):,} in triangles), {len(triangles):,} triangles; core and waterways clear.')


if __name__ == '__main__':
    build()
