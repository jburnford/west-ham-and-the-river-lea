"""Reconcile rubber/oilskin and felt OS exteriors; reject domestic envelopes."""
import json
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Polygon, Point, shape
from shapely.ops import unary_union
from prepare_ink_works_alignment import axis, rings
from prepare_three_mills_north_alignment import polygon
from factory_alignment_records import record_group

ROOT = Path(__file__).resolve().parents[1]
PREFIX = ('Explicit OS rubber/oilskin or felt exterior match; elevations and roofs '
          'remain interpretations. No Goad corroboration asserted. ')
SPECS = [
    ('rubber-east', 'west-423-1', [19653],
     'The former main rectangle covered the unshaded labelled manufacturing court. '
     'Move that existing main-range profile onto the shaded eastern U-shaped '
     'factory body; retain both open recesses rather than roofing the yard.'),
    ('rubber-northwest-east', 'west-423-2', [80446],
     'Eastern shaded northwest room; the supplied 0.696 m division from 185796 '
     'is retained conservatively because the raw OS line does not establish a continuous roof.'),
    ('rubber-northwest-west', 'west-423-2-northwest', [185796],
     'Restore the separately outlined western northwest room. It reuses the '
     'former northwest-store elevation and roof profile as an interpretation; '
     'this height is not separately measured. Preserve the source division from 80446.'),
    ('felt-west', 'west-424-1', [15902, 131228, 116562, 834137, 131038],
     'Contiguous shaded western felt body, including its northern attached rooms. '
     'The middle courtyard recess remains open; northern domestic source 80995 is excluded.'),
    ('felt-east', 'west-424-2', [39619, 117398],
     'Contiguous east-facing felt range; school outline 718124 beyond its northern '
     'boundary is excluded. Preserve the open court between western and eastern bodies.'),
    ('felt-south', 'west-424-3', [167043, 146487, 566260],
     'Contiguous southern felt body; retain the adjoining courtyard passage '
     'and the separate chapel-yard boundary to the south.'),
]


def build():
    load = lambda p: json.loads((ROOT / p).read_text())
    before = load('reference/footprint-model-alignment/west-mills-before.json')
    models = {b['id']: b for b in before['buildings']}
    cached = load('reference/footprint-model-alignment/west-mills-source-shapes.json')
    source = {f: polygon(shape(cached[str(f)])) for _, _, fs, _ in SPECS for f in fs}
    template = models['west-423-2']
    added_id = 'west-423-2-northwest'
    added_target = polygon(set_precision(source[185796], .001))
    added_name = 'Rubber and oilskin — separate northwest room'
    evidence = SPECS[2][3]
    addition = dict(id=added_id, siteId=423, source=template['source'], name=added_name,
        worldFootprint=rings(added_target)[0], worldHoles=rings(added_target)[1:],
        eavesHeight=template['height'], roofRise=template['roofRise'],
        roofAxis=template['roofAxis'], roofBays=template['roofBays'],
        material=template['material'], roof=template['roof'],
        storeysEstimate=template['storeysEstimate'], footprintEvidence=evidence,
        heightEvidence='Same estimated 6.9 m eaves as the prior northwest store; no independent measured elevation.',
        roofEvidence='Same interpreted gable profile as the prior northwest store; OS supplies plan only.')
    models[added_id] = dict(addition, footprint=addition['worldFootprint'],
                           height=template['height'], rotation=template['rotation'])
    groups, rows = [], []
    for gid, id, fids, decision in SPECS:
        target = polygon(set_precision(unary_union([source[f] for f in fids]), .001))
        angle = axis(target, models[id]['rotation'])
        group, corrections = record_group(gid, fids, source, models, [id],
            [models[id]['name']], target, [target], angle, decision,
            additional=id == added_id, review_prefix=PREFIX)
        groups.append(group)
        rows.extend(corrections)
        assert target.is_valid and target.symmetric_difference(unary_union([source[f] for f in fids])).area < .05
    shapes = {b['modelId']: Polygon(b['worldFootprint'], b['worldHoles']) for b in rows}
    gap = shapes['west-423-2'].distance(shapes[added_id])
    assert .69 < gap < .70, gap
    old_stack = next(s for s in before['structures'] if s['id'] == 'west-424-3-stack')
    parent = shapes['west-424-3']
    centre = Point(round(parent.centroid.x, 3), round(parent.centroid.y, 3))
    assert parent.covers(centre.buffer(old_stack['radius'] * 1.2))
    stack = dict(id=old_stack['id'], centre=list(centre.coords)[0],
        priorCentre=[old_stack['x'], old_stack['z']], preservedHeight=old_stack['height'],
        rotation=rows[-1]['footprintRotationDegrees'], parentBuildingId='west-424-3',
        parentFractions=[.5, .5],
        review='Inferred process chimney moves into the corrected southern felt body at its centroid. '
               'Full existing plinth fits inside the parent. This is not a mapped OS chimney symbol; '
               'the prior 24 m height, 1.05 m radius and tapered brick profile remain interpreted.')
    domestic = {
        'west-423-3': [77809, 67911, 26223],
        'west-423-5': [4730, 116673],
    }
    removed = [dict(models[id], reviewedDomesticSourceFids=fids,
        review='Raw OS and annotated source review positively show the former industrial '
               'envelope on the long domestic terrace south of the manufacturing court. '
               'Repeated separate rear extensions and garden divisions, together with the '
               'Baptist Chapel parcel boundary, distinguish this frontage from the northern works. '
               'Remove its industrial volume; domestic source outlines remain available '
               'for the separate housing alignment.') for id, fids in domestic.items()]
    rubber_stack = next(s for s in before['structures'] if s['id'] == 'west-423-process-stack')
    result = dict(source='Author-supplied london_buildings_1891-96_corr_v1.gpkg; cached OS London five-foot 1893 mosaic',
        sourceCRS='EPSG:3857 reprojected through BNG; scene origin E538900,N183209',
        method='Explicit rubber/oilskin and felt OS exterior matches. Manufacturing court and felt recesses remain open; northwest source division retained. Domestic industrial misclassifications rejected after raw OS review.',
        groups=groups, buildings=rows, structures=[stack], additionalBuildings=[addition],
        removedBuildings=removed,
        removedStructures=[dict(rubber_stack,
            review='The inferred 25 m process chimney was attached to rejected domestic '
                   'envelope west-423-3, not transcribed from an OS chimney symbol. '
                   'Remove that unsupported industrial attribution and retain the full prior record.')],
        evidenceImages=[f'reference/footprint-model-alignment/rubber-felt-{suffix}.png'
                        for suffix in ['raw', 'source', 'models']],
        retainedOpenDivision=dict(sourceFids=[185796, 80446], clearWidthMetres=round(gap, 3),
            evidence='Source polygons have a narrow division; raw OS line does not conclusively identify an open passage or a roof seam, so no connector is inferred.'),
        deferred=[dict(sourceFids=[80995], reason='Domestic row north of felt west body; retain source only, housing review separate.'),
                  dict(sourceFids=[718124], reason='Mapped boys school; separate institutional outline, not felt works.'),
                  dict(sourceFids=[1013531, 977142, 901709, 1071779, 1020991, 1029602, 1037761],
                       reason='Small separate rubber-yard/northwest projections and plant outlines lack individually reviewed full-height models or chimney attribution.')])
    (ROOT / 'data/maps/rubber-felt-footprint-alignment.json').write_text(json.dumps(result, indent=2) + '\n')
    print(f'Rubber/felt: six ranges in six groups, thirteen source polygons; one addition, two domestic removals; NW division {gap:.3f} m; felt chimney retained at 24 m.')


if __name__ == '__main__':
    build()
