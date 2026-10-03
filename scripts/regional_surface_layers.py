"""Later surfaces are confined to their mapped footprints above marsh ground.

No benchmark is a ground control. Unlocated yards and other surface observations
remain in the evidence register rather than becoming arbitrary raised discs.
"""
import numpy as np
import shapely
from scipy.spatial import cKDTree
from shapely.geometry import LineString, Polygon


def polygons_bng(polygons):
    return shapely.union_all([Polygon([(538900+x, 183209-z) for x,z in p[0]],
        [[(538900+x,183209-z) for x,z in ring] for ring in p[1:]]) for p in polygons])


def add_later_surfaces(height, kind, east, north, marsh_mask, exclusions, audit,
                       trial, infrastructure, yards, datum):
    ground = height.copy()
    xy = np.column_stack([east.ravel(), north.ravel()])
    eligible = marsh_mask.ravel() & np.isfinite(height.ravel())
    records = [r for r in audit['records'] if r['type']=='spot' and r['confidence']=='high'
               and not r['disputed'] and not r.get('setting_conflict')]
    roads = [c for c in trial['controls'] if c['family']=='road']
    summary = []
    source_ids = set()

    def indices_in(footprint):
        x0,y0,x1,y1 = footprint.bounds
        candidates = np.flatnonzero(eligible & (xy[:,0]>=x0)&(xy[:,0]<=x1)&(xy[:,1]>=y0)&(xy[:,1]<=y1))
        return candidates[shapely.contains_xy(footprint, xy[candidates,0], xy[candidates,1])]

    def fit(footprint, controls, maximum_distance, taper=None):
        cells = indices_in(footprint)
        if not len(cells) or not controls:
            return np.array([], dtype=int), np.array([]), []
        positions = np.array([c['positionBNG'] for c in controls])
        values = np.array([c.get('heightODNMetres', c.get('provisionalODNMetres')) for c in controls])
        distances, ii = cKDTree(positions).query(xy[cells], k=min(4,len(controls)))
        if distances.ndim==1:
            distances=distances[:,None];ii=ii[:,None]
        lines = shapely.linestrings(np.stack([np.broadcast_to(xy[cells,None,:], (*ii.shape,2)), positions[ii]],axis=2).reshape(-1,2,2))
        clear = ~shapely.intersects(lines, exclusions).reshape(ii.shape)
        weights = np.where(clear & (distances<=maximum_distance), 1/np.maximum(distances,3)**2, 0)
        usable = weights.sum(axis=1)>0
        cells=cells[usable];weights=weights[usable];ii=ii[usable]
        levels=(values[ii]*weights).sum(axis=1)/weights.sum(axis=1)
        if taper:
            t=np.clip(shapely.distance(shapely.points(xy[cells]),footprint.boundary)/taper,0,1)
            levels=ground.ravel()[cells]+t*(levels-ground.ravel()[cells])
        used=[controls[i] for i in np.unique(ii[weights>0])]
        return cells,levels,used

    def apply(name, category, cells, levels, controls, method):
        if not len(cells):return
        height.ravel()[cells]=levels;kind.ravel()[cells]=category
        source_ids.update(c['id'] for c in controls)
        summary.append({'name':name,'kind':category,'cells':len(cells),
            'sourceIds':[c['id'] for c in controls], 'method':method,
            'heightRangeODNMetres':[float(levels.min()),float(levels.max())],
            'differenceFromEstimatedGroundMetres':[float((levels-ground.ravel()[cells]).min()),float((levels-ground.ravel()[cells]).max())]})

    # Ordinary streets remain useful evidence. Their levels fit the traced
    # street, rather than raising every field in a road-to-road TIN triangle.
    for road in infrastructure['roads']:
        route=LineString([(538900+x,183209-z) for x,z in road['route']])
        width=road['width']/2+3  # grid representation of the mapped corridor
        controls=[c for c in roads if route.distance(shapely.Point(c['positionBNG']))<=width+7]
        cells,levels,used_controls=fit(route.buffer(width),controls,120)
        apply(road['name'],10,cells,levels,used_controls,'Mapped street corridor; accepted street levels within 120 m, no water-crossing fit. Width includes 3 m grid allowance.')

    for yard in yards:
        footprint=polygons_bng(yard['polygons'])
        controls=[c for c in records if c['surfaceFamily']=='yard' and footprint.covers(shapely.Point(c['positionBNG']))]
        cells,levels,used_controls=fit(footprint,controls,180,taper=8)
        apply(yard['name'],11,cells,levels,used_controls,'Same mapped premises only; yard readings within 180 m; 8 m estimated edge transition. No level inferred from a building benchmark.')

    used=sorted(source_ids)
    unplaced=[c['id'] for c in records if c['surfaceFamily'] in ('road','yard','wall','bank-or-embankment','railway')
              and c['id'] not in source_ids]
    return ground, {'features':summary,'usedSourceIds':used,'unplacedSurfaceObservationIds':unplaced,
        'unplacedScope':'All high-confidence undisputed, non-conflicted spot readings in the frozen regional audit, including locations outside the early-marsh envelope; lack of use here does not mean missing from the original TIN.',
        'policy':'Surface-specific fits, not additions to general marsh controls. Continuous narrow structures are composed separately from longitudinal profiles and a fine mesh.'}
