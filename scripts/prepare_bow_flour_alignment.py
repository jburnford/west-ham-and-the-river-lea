"""Author reviewed Bow Flour/Albion Wharf OS exteriors and retained elevations."""
import json
from pathlib import Path

from shapely import set_precision
from shapely.geometry import LineString, Point, Polygon, shape
from shapely.ops import split, unary_union

from factory_alignment_records import record_group
from prepare_ink_works_alignment import axis
from prepare_three_mills_north_alignment import polygon

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ('Explicit Bow Flour/Albion Wharf OS exterior match; previous interpreted '
          'elevations and roof parameters retained. No Goad corroboration asserted. ')


def build():
    load = lambda p: json.loads((ROOT / p).read_text())
    before = load('reference/footprint-model-alignment/west-mills-before.json')
    models = {b['id']: b for b in before['buildings']}
    cached = load('reference/footprint-model-alignment/west-mills-source-shapes.json')
    fids = [6296, 664578, 783709, 22581, 133193, 1006180,
            6191, 247343, 970043, 147640]
    source = {fid: polygon(shape(cached[str(fid)])) for fid in fids}

    def joined(fs):
        return polygon(set_precision(unary_union([source[f] for f in fs]), .001))

    mill = joined([6296])
    # The OS supplies one exterior. The existing low boiler compartment receives
    # the complete north tip, divided across its mapped shoulder; this chord is
    # an interpreted roof boundary, not a separately surveyed party wall.
    shoulder = [(-1072.315258978866, 107.47283158812206),
                (-1061.7409962262027, 108.2313596016611)]
    # Exact source vertices anchor the finite chord; an extended line would cut
    # a second tiny reentrant corner beyond the intended northern tip.
    pieces = list(split(source[6296], LineString(shoulder)).geoms)
    assert len(pieces) == 2
    boiler, main = sorted(pieces, key=lambda p: p.area)
    boiler, main = [polygon(set_precision(p, .001)) for p in [boiler, main]]
    rear_fids = [22581, 133193, 1006180]
    rear_raw = unary_union([source[f] for f in rear_fids])
    seam = rear_raw.intersection(source[6296])
    rear = polygon(set_precision(joined(rear_fids).difference(mill), .001))
    specs = [
        ('bow-flour-main', [6296], ['west-422-1', 'west-422-6'], mill, [main, boiler],
         'Single supplied mill exterior includes the complete northern tip. Main mill and lower boiler house are partitioned across the mapped shoulder; the internal roof chord and uses remain interpretations. The lower compartment retains its 5.5 m eaves and original roof parameters.'),
        ('bow-flour-roadfront', [664578, 783709], ['west-422-2'], joined([664578, 783709]), None,
         'Two touching shaded OS rooms form the road-front building. The previous broad rectangle extended into open yard; the complete smaller supplied exterior is retained.'),
        ('bow-flour-rear', rear_fids, ['west-422-3'], rear, None,
         'Rear warehouse, attached eastern strip and its small joining room form one contiguous mapped exterior. A 0.185 m2 conflicting digitized seam with the northern mill tip is trimmed in favour of source 6296; raw source polygons are retained separately.'),
        ('albion-wharf-riverside', [6191, 247343, 970043], ['west-422-4'], joined([6191, 247343, 970043]), None,
         'Riverside wharf body and its touching western strip and northern end room are joined across source seams. The mapped reentrant southern courtyard edge remains open.'),
        ('albion-wharf-western', [147640], ['west-422-5'], joined([147640]), None,
         'Retain only the principal shaded western body. Store use is inherited and uncertain from OS alone; adjacent sources 745243 and 775257 show likely domestic roof/toilet patterns and are explicitly deferred.'),
    ]
    groups, buildings = [], []
    for gid, fs, ids, target, parts, division in specs:
        parts = parts or [target]
        angle = axis(parts[0], models[ids[0]]['rotation'])
        group, rows = record_group(gid, fs, source, models, ids,
            [models[i]['name'] for i in ids], target, parts, angle, division,
            review_prefix=REVIEW)
        if gid == 'bow-flour-main':
            row = rows[1]
            row['footprintRotationDegrees'] = axis(boiler, models[row['modelId']]['rotation'])
            row['comparison']['axisChangeDegrees'] = row['footprintRotationDegrees']-row['priorRotationDegrees']
        if gid == 'bow-flour-rear':
            group['sourceReconciliation'] = dict(
                method='Remove the documented shared digitization overlap from the rear group; complete mill source 6296 has precedence.',
                precedenceGroup='bow-flour-main', excludedSourceFids=[6296],
                removedAreaM2=seam.area,
                evidence='The supplied western mill-tip edge and eastern rear-strip edge conflict by a narrow sliver; OS shows adjoining shaded bodies, not two intersecting buildings.')
            group['rawSourceIoU'] = target.intersection(rear_raw).area/target.union(rear_raw).area
        emitted = unary_union([Polygon(c['worldFootprint'], c['worldHoles']) for c in rows])
        assert emitted.symmetric_difference(target).area < .02
        groups.append(group)
        buildings.extend(rows)
    bodies = [Polygon(c['worldFootprint'], c['worldHoles']) for c in buildings]
    assert all(p.is_valid for p in bodies)
    assert all(p.intersection(q).area < .001 for i, p in enumerate(bodies) for q in bodies[:i])
    old = next(s for s in before['structures'] if s['id'] == 'west-422-6-stack')
    centre = Point(round(boiler.centroid.x, 3), round(boiler.centroid.y, 3))
    assert boiler.covers(centre.buffer(old['radius']*1.2))
    stack = dict(id=old['id'], centre=[centre.x, centre.y],
        rotation=buildings[1]['footprintRotationDegrees'],
        priorCentre=[old['x'], old['z']], preservedHeight=old['height'],
        parentBuildingId='west-422-6', parentFractions=[.5, .5],
        review='Existing inferred boiler chimney transferred to the corrected north-tip compartment centroid; the entire shaft and 1.2-times-radius plinth fit inside the parent. No OS chimney symbol or measured location is asserted. Prior 32 m height, 1.25 m radius and shaft profile retained.')
    result = dict(
        source='Author-supplied london_buildings_1891-96_corr_v1.gpkg; cached OS London five-foot 1893 mosaic',
        sourceCRS='EPSG:3857 reprojected through BNG; scene origin E538900,N183209',
        method='Reviewed complete OS exteriors; mill north tip retains lower boiler interpretation. Explicit shared source seam reconciliation, uncertain western use and ancillary omissions recorded.',
        groups=groups, buildings=buildings, structures=[stack],
        evidenceImages=['reference/footprint-model-alignment/bow-flour-raw.png',
                        'reference/footprint-model-alignment/bow-flour-source.png',
                        'reference/footprint-model-alignment/bow-flour-models.png'],
        deferred=[
            dict(sourceFids=[745243, 775257], reason='Adjacent western shaded rooms show likely domestic roof/toilet patterns. Their uncertain use does not justify extending the industrial store; retain as regional source context pending housing review.'),
            dict(sourceFids=[835826], reason='Small separately digitized rear projection lies about 0.162 m from the rear body. No reliable elevation evidence supports a full-height annex; not silently bridged into the warehouse.'),
            dict(sourceFids=[730314], reason='OS shows circular plant/tank, not a building. No existing tank model belongs to this pass; leave in source context pending plant review.'),
            dict(sourceFids=[33474, 220606, 228988, 491144, 861723], reason='Other shaded bodies in Albion Wharf have no existing reviewed model counterpart in these six ranges. Do not absorb them into nearby warehouses; retain regional outlines pending a separate ancillary-building review.')])
    (ROOT / 'data/maps/bow-flour-footprint-alignment.json').write_text(json.dumps(result, indent=2)+'\n')
    print(f'Bow Flour/Albion Wharf: six ranges in five groups; raw shared seam {seam.area:.6f} m2; boiler centroid plinth clearance {centre.distance(boiler.boundary)-old["radius"]*1.2:.3f} m.')


if __name__ == '__main__':
    build()
