"""Rebuild the explicitly reviewed ink-works groups; never select nearest shapes.

Requires the private source extract. Routine scene builds use the saved register.
The paired Goad compartments share an OS outline; their division remains an
interpretation based on the earlier traced proportions, not an OS party wall.
"""
import json
import math
from pathlib import Path

import numpy as np
from shapely import affinity, set_precision
from shapely.geometry import Polygon, box, shape
from shapely.ops import unary_union

from build_factory_buildings import footprint

ROOT = Path(__file__).resolve().parents[1]


def rings(p):
    return [list(map(list, r.coords))[:-1] for r in [p.exterior, *p.interiors]]


def axis(g, previous):
    corners = list(g.minimum_rotated_rectangle.exterior.coords)
    angles = [math.degrees(math.atan2(b[1]-a[1], b[0]-a[0])) for a, b in zip(corners, corners[1:])]
    return min((previous+(a-previous+90) % 180-90 for a in angles), key=lambda a: abs(a-previous))


def build():
    raw = json.loads((ROOT/'data/maps/factory-building-traces.json').read_text())
    rows = {b['id']: b for b in raw['buildings']}
    scene = json.loads((ROOT/'docs/data/factory-buildings.json').read_text())
    models = {b['id']: b for b in scene['buildings']}
    source = json.loads((ROOT/'reference/historic-building-footprints-2026-09-28/current-scene-buildings-bng.geojson').read_text())
    wanted = {2452, 3305, 250895, 310941, 130019, 22797, 236901, 581251,
              102264, 52500, 52044, 592063, 1002254, 1087528, 954257}
    geometries = {f['properties']['sourceFid']: affinity.affine_transform(shape(f['geometry']), [1, 0, 0, -1, -538900, 183209])
                  for f in source['features'] if f['properties']['sourceFid'] in wanted}
    # Source IDs and member order were established by inspecting both OS and Goad.
    specs = [
        ('lampblack-west', [2452], ['26', '25'], 1),
        ('lampblack-east', [3305], ['29', '28'], 1),
        ('grinding-bays', [250895], ['9', '10'], 0),
        ('warehouse-offices', [102264, 52500], ['2'], None),
        ('grinding-house', [52044, 592063], ['4'], None),
        ('lampblack-chamber', [310941], ['27'], None),
        ('lampblack-store', [130019], ['30'], None),
        ('boiler-house', [22797], ['23'], None),
        ('mixing-bay-7', [236901], ['7'], None),
        ('mixing-bay-8', [581251], ['8'], None),
    ]
    groups, corrections = [], []
    for name, fids, refs, split_axis in specs:
        ids = ['site940-'+ref for ref in refs]
        originals = [Polygon(footprint(rows[id], raw['sources'][rows[id]['source']])) for id in ids]
        previous = math.degrees(math.atan2(originals[0].exterior.coords[1][1]-originals[0].exterior.coords[0][1],
                                           originals[0].exterior.coords[1][0]-originals[0].exterior.coords[0][0]))
        target = unary_union([geometries[fid] for fid in fids])
        if target.geom_type == 'MultiPolygon' and len(target.geoms) == 1:
            target = target.geoms[0]
        assert target.geom_type == 'Polygon' and target.is_valid, name
        angle = axis(target, previous)
        local = affinity.rotate(target, -angle, origin=(0, 0))
        bounds = local.bounds
        parts = [target]
        division = None
        if split_axis is not None:
            # Keep the relative widths of the prior Goad traces, fitting both
            # together so their external boundary equals the complete OS shape.
            old_bounds = [affinity.rotate(p, -previous, origin=(0, 0)).bounds for p in originals]
            widths = [b[split_axis+2]-b[split_axis] for b in old_bounds]
            fraction = widths[0]/sum(widths)
            cut = bounds[split_axis] + (bounds[split_axis+2]-bounds[split_axis])*fraction
            x0, z0, x1, z1 = bounds
            low = box(x0-1, z0-1, cut, z1+1) if split_axis == 0 else box(x0-1, z0-1, x1+1, cut)
            first = local.intersection(low)
            parts = [affinity.rotate(p, angle, origin=(0, 0)) for p in [first, local.difference(first)]]
            division = {'axis': 'x' if split_axis == 0 else 'z', 'firstMemberFraction': fraction,
                        'method': 'Relative compartment widths retained from the existing Goad traces, fitted within the complete OS outline.'}
        parts = [set_precision(p, .001) for p in parts]
        group_id = 'ink-'+name
        before = unary_union(originals)
        groups.append({'id': group_id, 'sourceFids': fids, 'modelIds': ids,
                       'sourcePolygons': [rings(p) for fid in fids for p in geometries[fid].geoms],
                       'division': division,
                       'previousUnionIoU': before.intersection(target).area/before.union(target).area})
        if name == 'lampblack-east':
            groups[-1]['boundaryOverlapReview'] = {
                'neighbourGroup': 'ink-lampblack-store',
                'sourceOverlapAreaM2': target.intersection(geometries[130019]).area,
                'evidence': 'Source outlines 3305 and 130019 overlap by about 0.77 square metres at their shared edge. Retain both source boundaries; give the smaller store precedence in the rendered seam.'}
        for id, old, part in zip(ids, originals, parts):
            assert part.geom_type == 'Polygon' and part.is_valid, id
            model = models[id]
            review = ('OS outer boundary reviewed with Goad sheet F3. '+
                      ('Paired Goad compartments share this source; the internal division follows earlier traced proportions and remains interpreted. ' if division else
                       'Adjacent OS polygons grouped under the retained Goad range. ' if len(fids)>1 else 'Individual mapped range. ')+
                      'Retain the Goad use, floor evidence, eaves height and roof interpretation; retain source holes.')
            corrections.append({'modelId': id, 'siteId': 940, 'name': model['name'], 'groupId': group_id,
                'sourceFids': fids, **({'sourceFid': fids[0]} if len(fids)==1 else {}),
                'worldFootprint': rings(part)[0], 'worldHoles': rings(part)[1:],
                'priorFootprint': np.array(old.exterior.coords)[:-1].round(3).tolist(),
                'priorRotationDegrees': previous, 'footprintRotationDegrees': angle,
                'preservedHeight': model['height'], 'preservedRoofRise': model['roofRise'],
                'preservedRoofBays': model['roofBays'], 'preservedRoofAxis': model['roofAxis'],
                'review': review, 'comparison': {'centroidShiftMetres': old.centroid.distance(part.centroid),
                    'areaRatio': part.area/old.area, 'axisChangeDegrees': angle-previous}})
    stacks = []
    for id, fid in [('stack-940-1310-710', 1002254), ('stack-940-1596-685', 1087528), ('stack-940-1352-907', 954257)]:
        original = next(s for s in raw['structures'] if s['id']==id)
        a, b, x, z = raw['sources'][original['source']]['pixelToWorld']
        u, v = original['pixelPosition']
        g = geometries[fid]
        stacks.append({'id': id, 'sourceFid': fid, 'centre': [g.centroid.x, g.centroid.y],
                       'sourcePolygons': [rings(p) for p in g.geoms],
                       'priorCentre': [a*u-b*v+x, b*u+a*v+z],
                       'rotation': axis(g, -40), 'preservedHeight': original['height'],
                       'review': 'Goad chimney symbol compared with the small OS base polygon beside its process range; retain height and shaft profile. West stack occupies the mapped hole in source 2452.'})
    result = {'source': 'Author-supplied london_buildings_1891-96_corr_v1.gpkg',
              'sourceCRS': 'EPSG:3857 reprojected through BNG to scene x/z; origin E538900,N183209',
              'method': 'Explicitly reviewed groups; OS external boundaries with retained Goad compartments, uses and elevations. Millimetre coordinate rounding only.',
              'mapReview': ['OS five-foot mosaic m18_131063_87137', 'July 1893 Goad volume F sheet 3'],
              'groups': groups, 'buildings': corrections, 'structures': stacks,
              'deferred': [{'modelId': id, 'reason': 'Clearly drawn on OS and Goad but absent from the supplied building extract here. Retain the Goad range pending a separate map-boundary trace; do not snap it to a neighbouring polygon.'}
                           for id in ['site940-firelighter', 'site940-24']]}
    (ROOT/'data/maps/ink-works-footprint-alignment.json').write_text(json.dumps(result, indent=2)+'\n')
    print(f'{len(corrections)} ranges in {len(groups)} reviewed groups; {len(stacks)} chimney bases; 2 source omissions deferred.')


if __name__ == '__main__':
    build()
