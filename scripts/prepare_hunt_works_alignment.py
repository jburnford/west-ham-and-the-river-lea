"""Reviewed Hunt soap-works OS matches; Goad room divisions remain interpreted.

Preparation needs the private footprint extract and immutable hunt-works-before
snapshot. Routine factory builds need only the saved authoring register.
"""
import json
from pathlib import Path
from shapely import affinity, set_precision
from shapely.geometry import Polygon, Point, shape
from shapely.ops import unary_union
from prepare_ink_works_alignment import axis, rings
from prepare_howards_alignment import partition

ROOT = Path(__file__).resolve().parents[1]
SPECS = [
    ('main-process', [1461, 938428], [f'site564-range-{n}' for n in range(1, 6)]),
    ('stables-554', [73603], ['site564-range-6']),
    ('dwelling-552', [381084], ['site564-range-7']),
    ('western-furnaces', [100277], ['site564-furnaces']),
    ('office-laboratory-538', [842322], ['site564-laboratory-538']),
    ('engine-room', [858006], ['site564-engine']),
]
NAMES = {
    1: 'Hunt northern boiling, cutting, drying and packing rooms',
    2: 'Hunt central soap-making rooms and boiler compartment 544',
    3: 'Hunt southern process bay, Goad 548',
    4: 'Hunt southeastern process compartment, Goad 550',
    5: 'Hunt eastern smithy, Goad 542',
    6: 'Hunt stables, Goad 554',
    7: 'Hunt dwelling, Goad 552',
}


def build():
    load = lambda p: json.loads((ROOT / p).read_text())
    before = load('reference/footprint-model-alignment/hunt-works-before.json')
    models = {b['id']: b for b in before['buildings']}
    wanted = {fid for _, fids, _ in SPECS for fid in fids} | {1013155}
    source = {
        f['properties']['sourceFid']: affinity.affine_transform(shape(f['geometry']), [1, 0, 0, -1, -538900, 183209])
        for f in load('reference/historic-building-footprints-2026-09-28/current-scene-buildings-bng.geojson')['features']
        if f['properties']['sourceFid'] in wanted
    }
    additions = []
    for id, fid, name in [
        ('site564-furnaces', 100277, 'Hunt western furnace rooms'),
        ('site564-laboratory-538', 842322, 'Hunt office and laboratory, Goad 538'),
        ('site564-engine', 858006, 'Hunt southern engine room'),
    ]:
        p = set_precision(source[fid], .001)
        p = list(p.geoms)[0] if p.geom_type == 'MultiPolygon' else p
        row = dict(id=id, siteId=564, source='goad-f17', name=name,
                   worldFootprint=rings(p)[0], worldHoles=rings(p)[1:],
                   eavesHeight=3.8, roofRise=1.3, roofAxis='x', roofBays=1, material='brick',
                   footprintEvidence='Separate supplied OS exterior reviewed against the labelled Goad F17 room.',
                   heightEvidence='Interpreted low 3.8 m eaves; Goad use and floor marks do not establish a measured elevation.',
                   roofEvidence='Low pitched roof interpretation; no roof profile supplied by the footprint.')
        additions.append(row)
        models[id] = {**row, 'height': row['eavesHeight'], 'footprint': row['worldFootprint'], 'rotation': -24.8174}
    groups, corrections = [], []
    for name, fids, ids in SPECS:
        target = set_precision(unary_union([source[f] for f in fids]), .001)
        if target.geom_type == 'MultiPolygon' and len(target.geoms) == 1:
            target = target.geoms[0]
        assert target.geom_type == 'Polygon' and target.is_valid, name
        old = [Polygon(models[id]['footprint']) for id in ids]
        angle = axis(target, models[ids[0]]['rotation'])
        parts = partition(old, target, models[ids[0]]['rotation'], angle) if len(ids) > 1 else [target]
        assert all(p.geom_type == 'Polygon' and p.is_valid and p.area > 2 for p in parts), name
        previous = unary_union(old)
        groupid = 'hunt-works-' + name
        groups.append(dict(id=groupid, modelIds=ids, sourceFids=fids,
                           sourcePolygons=[rings(p) for f in fids for p in getattr(source[f], 'geoms', [source[f]])],
                           division='Existing Goad room proportions fitted to the combined OS exterior; internal cuts remain interpreted.' if len(ids) > 1 else None,
                           previousUnionIoU=previous.intersection(target).area / previous.union(target).area))
        for id, p, prior in zip(ids, parts, old):
            b = models[id]
            name = NAMES[int(id.rsplit('-', 1)[1])] if '-range-' in id else b['name']
            corrections.append(dict(modelId=id, siteId=564, name=name, groupId=groupid, sourceFids=fids,
                **({'sourceFid': fids[0]} if len(fids) == 1 else {}),
                worldFootprint=rings(p)[0], worldHoles=rings(p)[1:], priorFootprint=rings(prior)[0],
                priorRotationDegrees=b['rotation'], footprintRotationDegrees=angle,
                preservedHeight=b['height'], preservedRoofRise=b['roofRise'],
                preservedRoofAxis=b['roofAxis'], preservedRoofBays=b['roofBays'],
                review='Explicit OS/Goad F17 comparison. Retain use and prior elevation/roof interpretation. ' + (groups[-1]['division'] or 'Independent mapped exterior.'),
                comparison=dict(centroidShiftMetres=prior.centroid.distance(p.centroid), areaRatio=p.area / prior.area,
                                axisChangeDegrees=angle - b['rotation'])))
    structures = []
    old = next(s for s in before['structures'] if s['id'] == 'stack-564-546-1422')
    g = source[1013155]
    structures.append(dict(id=old['id'], sourceFid=1013155,
        sourcePolygons=[rings(p) for p in getattr(g, 'geoms', [g])], centre=list(g.centroid.coords)[0],
        rotation=axis(g, old['rotation']), priorCentre=[old['x'], old['z']], preservedHeight=old['height'],
        review='Goad boiler chimney matched to the independent OS base; retain printed 80-foot height and interpreted shaft profile.'))
    old = next(s for s in before['structures'] if s['id'] == 'stack-564-322-1325')
    # This Goad stack has no independent base in the supplied extract. Preserve
    # its proportional location within the corrected main compound.
    group = groups[0]
    angle = corrections[0]['footprintRotationDegrees']
    prior = affinity.rotate(unary_union([Polygon(models[id]['footprint']) for id in group['modelIds']]), -models['site564-range-1']['rotation'], origin=(0, 0))
    target = affinity.rotate(unary_union([source[f] for f in group['sourceFids']]), -angle, origin=(0, 0))
    point = affinity.rotate(Point(old['x'], old['z']), -models['site564-range-1']['rotation'], origin=(0, 0))
    x0, z0, x1, z1 = prior.bounds
    u, v = (point.x-x0)/(x1-x0), (point.y-z0)/(z1-z0)
    x0, z0, x1, z1 = target.bounds
    point = affinity.rotate(Point(x0+u*(x1-x0), z0+v*(z1-z0)), angle, origin=(0, 0))
    # Goad places the shaft just inside the process rooms beside the western
    # furnace wing. A local adjustment retains that relationship after fitting.
    point = affinity.translate(point, 2, 2)
    structures.append(dict(id=old['id'], centre=list(point.coords)[0], rotation=angle,
        priorCentre=[old['x'], old['z']], preservedHeight=old['height'], transferGroup=group['id'],
        localAdjustmentMetres=[2, 2],
        review='Goad western shaft transferred proportionally with the corrected main rooms, then adjusted 2 m east and south to retain its position inside the process rooms beside the furnace wing. No independent OS base claimed. Inferred 22 m height retained.'))
    result = dict(source='Author-supplied london_buildings_1891-96_corr_v1.gpkg',
        sourceCRS='EPSG:3857 reprojected through BNG; scene origin E538900,N183209',
        method='Explicit Hunt soap-works OS/Goad matches, with earlier room divisions and elevation interpretations retained.',
        mapReview=['Georeferenced OS five-foot 1893–96 mosaic', 'July 1893 Goad volume F sheet 17; admission refused annotation limits interior evidence'],
        groups=groups, buildings=corrections, additionalBuildings=additions, structures=structures,
        supersedesLocalTransfers=['site564-range-1'],
        deferred=[dict(sourceFids=[859135, 1062021, 1001071, 969335, 1228456],
                       reason='Tank/platform and minor service projections remain plant details; do not assign generic full-height rooms.'),
                  dict(feature='Western empties strip and small sheds', reason='Open storage and lightweight structures on Goad need separate yard/plant interpretation.')])
    (ROOT / 'data/maps/hunt-works-footprint-alignment.json').write_text(json.dumps(result, indent=2) + '\n')
    ground = load('reference/footprint-model-alignment/hunt-works-ground-before.json')
    ring = next(r for r in ground['rivers'] if r['id'] == 18)['polygons'][0][0]
    replacements = [dict(vertex=i, priorPoint=ring[i], point=[round(ring[i][0]-dx, 3), ring[i][1]])
                    for i, dx in [(39, 1), (40, 3.5)]]
    bank = dict(riverId=18, polygonIndex=0, ringIndex=0, replacements=replacements,
                source='OS five-foot map and supplied furnace outline 100277',
                registration='Local reconciliation of the simplified bank with the mapped furnace wall; not a surveyed shoreline.',
                evidence='Two works-side controls clear the restored western furnace range. Vertex 39 follows the prior Bow Bridge correction; the opposite bank is retained.')
    (ROOT / 'data/maps/hunt-works-bank-alignment.json').write_text(json.dumps(bank, indent=2) + '\n')
    print(f'Hunt: {len(corrections)} supplied-outline ranges in {len(groups)} groups; three additions and two corrected chimneys.')


if __name__ == '__main__':
    build()
