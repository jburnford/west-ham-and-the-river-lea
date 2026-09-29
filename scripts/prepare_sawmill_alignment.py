"""Prepare the reviewed Imperial mill and Towers courtyard footprint groups.

The OS fixes the external outline. Internal mill divisions retain the Goad
arrangement and elevations but remain interpreted. No nearest-feature selection.
"""
import json
import math
from pathlib import Path

import numpy as np
from shapely import affinity, set_precision
from shapely.geometry import Polygon, Point, box, shape
from shapely.ops import unary_union

from build_factory_buildings import footprint
from prepare_ink_works_alignment import axis, rings

ROOT = Path(__file__).resolve().parents[1]
FRAME_CENTRE = (-1045, -42)
FRAME_ANGLE = 36


def local(g):
    return affinity.translate(affinity.rotate(g, -FRAME_ANGLE, origin=FRAME_CENTRE),
                              -FRAME_CENTRE[0], -FRAME_CENTRE[1])


def world(g):
    return affinity.translate(affinity.rotate(g, FRAME_ANGLE, origin=(0, 0)), *FRAME_CENTRE)


def build():
    raw = json.loads((ROOT/'data/maps/factory-building-traces.json').read_text())
    rows = {b['id']: b for b in raw['buildings']}
    scene = json.loads((ROOT/'docs/data/factory-buildings.json').read_text())
    models = {b['id']: b for b in scene['buildings']}
    # Cuts follow the mapped western steps and the Goad arrangement: two links,
    # tall transverse mill, three parallel mill/veneer ranges and eastern strip.
    # These are authored interpretation coordinates, not measured OS party walls.
    cuts = [
        ('imperial-covered-link', [-100, -100, -16, -10.8]),
        ('imperial-mill-link', [-16, -100, -11.2, -10.8]),
        ('imperial-small-mill', [-100, -10.8, -11.2, 11.5]),
        ('imperial-east-range', [-11.2, -100, 100, -15.8]),
        ('imperial-veneer', [-100, 11.5, 100, 100]),
        ('imperial-basement-mill', [-11.2, -2, 100, 11.5]),
        ('imperial-iron-mill', [-11.2, -15.8, 100, -2]),
    ]
    specs = [
        ('imperial-main', [858, 24984], [id for id, _ in cuts]),
        ('imperial-stable', [58007, 94509], ['imperial-stable']),
        ('imperial-engine', [201211], ['imperial-engine']),
        ('imperial-office', [638578], ['imperial-office']),
        ('towers-north', [436569, 226632, 564637], ['site797-os-1']),
        ('towers-east', [750620, 580324, 613094, 576605], ['site797-os-2']),
        ('towers-west', [754482, 480984, 571284, 561604], ['site797-os-3']),
        ('towers-south', [485487], ['site797-os-4']),
    ]
    wanted = {fid for _, fids, _ in specs for fid in fids}
    source = json.loads((ROOT/'reference/historic-building-footprints-2026-09-28/current-scene-buildings-bng.geojson').read_text())
    geometries = {f['properties']['sourceFid']: affinity.affine_transform(shape(f['geometry']), [1, 0, 0, -1, -538900, 183209])
                  for f in source['features'] if f['properties']['sourceFid'] in wanted}
    groups, corrections = [], []
    for name, fids, ids in specs:
        target = unary_union([geometries[fid] for fid in fids])
        if target.geom_type == 'MultiPolygon' and len(target.geoms) == 1:
            target = target.geoms[0]
        assert target.geom_type == 'Polygon' and target.is_valid, name
        parts = [world(local(target).intersection(box(*bounds))) for _, bounds in cuts] if name=='imperial-main' else [target]
        parts = [set_precision(p, .001) for p in parts]
        assert unary_union(parts).symmetric_difference(target).area < .1, name
        originals = [Polygon(footprint(rows[id], raw['sources'][rows[id]['source']])) for id in ids]
        before = unary_union(originals)
        groups.append({'id': name, 'sourceFids': fids, 'modelIds': ids,
                       'sourcePolygons': [rings(p) for fid in fids for p in geometries[fid].geoms],
                       'previousUnionIoU': before.intersection(target).area/before.union(target).area,
                       'division': {'frameCentre': FRAME_CENTRE, 'frameAngleDegrees': FRAME_ANGLE,
                                    'windows': [{'modelId': id, 'bounds': bounds} for id, bounds in cuts],
                                    'method': 'Map-reviewed compartments fitted together to the combined OS outline. Cut lines preserve the Goad arrangement, not measured party walls.'} if name=='imperial-main' else None})
        if name == 'imperial-office':
            groups[-1]['boundaryOverlapReview'] = {
                'neighbourGroup': 'imperial-main',
                'sourceOverlapAreaM2': target.intersection(geometries[858]).area,
                'evidence': 'Office outline 638578 overlaps main outline 858 by about 0.20 square metres. Retain both source boundaries; the taller veneer store takes precedence at the rendered seam.'}
        for id, old, part in zip(ids, originals, parts):
            assert part.geom_type == 'Polygon' and part.is_valid, id
            model = models[id]
            a, b = list(old.exterior.coords)[:2]
            previous = math.degrees(math.atan2(b[1]-a[1], b[0]-a[0]))
            angle = previous+(FRAME_ANGLE-previous+45) % 90-45 if name=='imperial-main' else axis(target, previous)
            review = ('OS external boundary reviewed with July 1893 Goad F2. '+
                      ('Seven Goad compartments partition the shared main outline; internal cuts remain interpreted. ' if name=='imperial-main' else
                       'Adjacent OS polygons grouped as one existing range. ' if len(fids)>1 else 'Individual source outline. ')+
                      ('Towers is a separate slaughterhouse tenancy, not a sawmill production range. ' if name.startswith('towers-') else '')+
                      'Retain earlier uses, floor evidence, roof materials, eaves heights and roof interpretations.')
            corrections.append({'modelId': id, 'siteId': 797, 'name': model['name'], 'groupId': name,
                'sourceFids': fids, **({'sourceFid': fids[0]} if len(fids)==1 else {}),
                'worldFootprint': rings(part)[0], 'worldHoles': rings(part)[1:],
                'priorFootprint': np.array(old.exterior.coords)[:-1].round(3).tolist(),
                'priorRotationDegrees': previous, 'footprintRotationDegrees': angle,
                'preservedHeight': model['height'], 'preservedRoofRise': model['roofRise'],
                'preservedRoofBays': model['roofBays'], 'preservedRoofAxis': model['roofAxis'],
                'preservedEvidence': {key: rows[id].get(key) for key in
                    ['floorMark', 'storeysEstimate', 'roofMaterial', 'louvredUpperStorey', 'basement', 'useEvidence']},
                'review': review, 'comparison': {'centroidShiftMetres': old.centroid.distance(part.centroid),
                    'areaRatio': part.area/old.area, 'axisChangeDegrees': angle-previous}})
    # No distinct OS base for this internal boiler chimney. Transfer its Goad
    # position with the basement mill, keeping its relative location in that room.
    id = 'stack-797-2663-1901'
    original = next(s for s in raw['structures'] if s['id']==id)
    a, b, x, z = raw['sources'][original['source']]['pixelToWorld']
    u, v = original['pixelPosition']
    old_centre = [a*u-b*v+x, b*u+a*v+z]
    parent = next(r for r in corrections if r['modelId']=='imperial-basement-mill')
    old_parent = Polygon(parent['priorFootprint'])
    new_parent = Polygon(parent['worldFootprint'])
    old_local = affinity.rotate(old_parent, -parent['priorRotationDegrees'], origin=(0, 0))
    old_point = affinity.rotate(Point(old_centre), -parent['priorRotationDegrees'], origin=(0, 0))
    ob = old_local.bounds
    fraction = [(old_point.x-ob[0])/(ob[2]-ob[0]), (old_point.y-ob[1])/(ob[3]-ob[1])]
    new_local = affinity.rotate(new_parent, -parent['footprintRotationDegrees'], origin=(0, 0))
    nb = new_local.bounds
    new_point = affinity.rotate(Point(nb[0]+fraction[0]*(nb[2]-nb[0]), nb[1]+fraction[1]*(nb[3]-nb[1])),
                                parent['footprintRotationDegrees'], origin=(0, 0))
    assert new_parent.contains(new_point)
    stack = {'id': id, 'centre': list(new_point.coords)[0], 'priorCentre': old_centre,
             'parentBuildingId': parent['modelId'], 'rotation': parent['footprintRotationDegrees'],
             'preservedHeight': original['height'], 'parentFractions': fraction,
             'review': 'Internal Goad boiler chimney moved with the corrected basement mill using its relative room position. No separate OS base identified; location and 30 m height remain interpreted.'}
    result = {'source': 'Author-supplied london_buildings_1891-96_corr_v1.gpkg',
        'sourceCRS': 'EPSG:3857 reprojected through BNG to scene x/z; origin E538900,N183209',
        'method': 'Explicit reviewed Imperial mill and separate Towers courtyard groups; OS outer boundaries retain Goad compartments and elevation evidence. Millimetre rounding only.',
        'mapReview': ['OS five-foot mosaic m18_131060_87140', 'July 1893 Goad volume F sheet 2'],
        'groups': groups, 'buildings': corrections, 'structures': [stack],
        'retainedEarlierMatches': ['imperial-stoves', 'imperial-stable-cover'],
        'deferred': [{'sourceFid': 455070, 'reason': 'Additional engine-side boiler/plant outline lacks a separate existing model; retained in the regional plan layer pending plant review.'},
                     {'reason': 'Small projections, gate/plant symbols and apparatus without existing modeled counterparts remain outside this range-alignment pass.'}]}
    (ROOT/'data/maps/sawmill-footprint-alignment.json').write_text(json.dumps(result, indent=2)+'\n')
    print(f'{len(corrections)} ranges in {len(groups)} reviewed groups; internal chimney transferred with its parent; two prior matches retained.')


if __name__ == '__main__':
    build()
