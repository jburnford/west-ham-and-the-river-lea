"""Prepare visually reviewed Bow Brewery OS exteriors from the fixed baseline."""
import json
from pathlib import Path

from shapely import affinity, set_precision
from shapely.geometry import Point, box, shape
from shapely.ops import unary_union

from factory_alignment_records import record_group
from prepare_ink_works_alignment import axis
from prepare_three_mills_north_alignment import polygon

ROOT = Path(__file__).resolve().parents[1]
PREFIX = ('Explicit Bow Brewery OS exterior match; prior estimated elevations '
          'and roof profiles retained. No Goad corroboration asserted. ')
SPECS = [
    ('brewery-northeast', 'west-259-1', [7367, 550364],
     'Complete shaded irregular northeast roof and touching small southwest room. '
     'The enlarged raw OS crop distinguishes this stippled roof from the pale central '
     'brewery court. Preserve the small interior source hole; its function is unresolved.'),
    ('brewery-west', 'west-259-2', [5599, 396988],
     'Complete shaded irregular western body and its touching narrow east connector. '
     'The frontage terraces remain separate: the old diagonal envelope crossed their '
     'rear rooms. Preserve the reentrant unshaded court edges rather than closing them.'),
    ('brewery-north', 'west-259-3', [14349, 1031857, 1073949],
     'Relocate the prior northern-office profile onto the actual shaded northern '
     'brewery range and its two touching southern rooms. The prior rectangle straddled '
     'the separately labelled P.H. frontage. Its office use and two-storey height remain '
     'interpretations; exclude that public-house outline and neighbouring frontage rooms.'),
    ('brewery-southwest', 'west-259-4', [10218, 870225, 978252],
     'Complete shaded southwest southern range and two touching northern rooms. '
     'The former long envelope crossed the pale central court between this body '
     'and the separately mapped southeast body; keep that court open.'),
    ('brewery-southeast', 'west-259-5', [9963, 814662, 988405, 966155, 1123854],
     'Complete separately shaded southeast southern body and touching northern '
     'rooms. Move the inherited southeast-store profile onto this complete body, '
     'preserving its estimated elevation. Keep the detached narrow roadside '
     'room 533922 separate rather than bridging its intervening open division.'),
    ('brewery-yard-workshop', 'west-259-6', [750604, 518082, 1004639, 1053469],
     'Complete shaded detached western yard workshop and its two touching southern '
     'projections. Preserve the pale yard to its east and the separate nearby service room.'),
    ('brewery-service-room', 'west-259-7', [916095],
     'Actual small shaded service room beside the western yard. Move the inherited '
     'boiler/service elevation onto this outline; specific boiler use remains inferred. '
     'The existing chimney plinth cannot fit in its narrow plan and is separately reviewed.'),
]


def build():
    load = lambda p: json.loads((ROOT / p).read_text())
    before = load('reference/footprint-model-alignment/mill-brush-brewery-before.json')
    models = {b['id']: b for b in before['buildings']}
    cached = load('reference/footprint-model-alignment/mill-brush-brewery-source-shapes.json')
    source = {f: polygon(shape(cached[str(f)])) for _, _, fs, _ in SPECS for f in fs}
    groups, rows = [], []
    for gid, id, fids, decision in SPECS:
        target = polygon(set_precision(unary_union([source[f] for f in fids]), .001))
        group, corrections = record_group(gid, fids, source, models, [id],
            [models[id]['name']], target, [target], axis(target, models[id]['rotation']),
            decision, review_prefix=PREFIX)
        groups.append(group)
        rows.extend(corrections)
    old_stack = next(s for s in before['structures'] if s['id'] == 'west-259-7-stack')
    parent_id = 'west-259-6'
    parent_row = next(b for b in rows if b['modelId'] == parent_id)
    parent = polygon(unary_union([source[f] for f in parent_row['sourceFids']]))
    centre = Point(round(parent.centroid.x, 3), round(parent.centroid.y, 3))
    half = old_stack['radius'] * 1.2
    plinth = affinity.rotate(box(centre.x-half, centre.y-half,
                                centre.x+half, centre.y+half),
                            parent_row['footprintRotationDegrees'], origin=centre)
    assert parent.covers(plinth), 'Full existing chimney plinth must fit its parent'
    stack = dict(id=old_stack['id'], centre=list(centre.coords)[0],
        priorCentre=[old_stack['x'], old_stack['z']],
        preservedHeight=old_stack['height'], rotation=parent_row['footprintRotationDegrees'],
        parentBuildingId=parent_id, parentFractions=[.5, .5],
        review='No independently mapped OS chimney base is established for the existing '
               'boiler stack. Its inferred position transfers to the neighbouring corrected '
               'yard workshop because the narrow service-room outline cannot contain the '
               'existing square plinth. The full rotated plinth, half-side radius × 1.2, '
               'fits inside this parent. Preserve the prior 30 m height, 1.3 m radius '
               'and tapered brick profile; location, height and industrial use remain interpretations.')
    result = dict(
        source='Author-supplied london_buildings_1891-96_corr_v1.gpkg; cached OS London five-foot 1893 mosaic',
        sourceCRS='EPSG:3857 reprojected through BNG; scene origin E538900,N183209',
        method='Explicit raw-OS reviewed brewery roof exteriors; seven existing profiles retained, pale central court open, public-house frontage excluded, inferred chimney transferred with full plinth containment.',
        groups=groups, buildings=rows, structures=[stack],
        evidenceImages=[f'reference/footprint-model-alignment/bow-brewery-{suffix}.png'
                        for suffix in ['raw', 'source', 'models', 'roof-detail', 'after']],
        retainedOpenCourt=dict(worldPoint=[-1044, 197],
            evidence='Pale central Bow Brewery court in the raw OS crop, between the stippled northern, western and southern roofs; the former south envelope crossed its eastern portion.'),
        excludedFrontage=dict(sourceFids=[40425, 162287, 331413, 610498, 669893],
            evidence='The P.H. label is inside 40425, with separately drawn adjoining northern rooms and western terrace frontage. Brewery ownership/use of those rooms is not independently established; no nearest-envelope absorption.'),
        deferred=[
            dict(sourceFids=[533922, 981055, 1030891], reason='Separate narrow shaded roadside yard room and touching small rooms; no remaining independently matched existing profile. Keep its division from the southeast body open.'),
            dict(sourceFids=[11380, 9628, 5797, 31349, 75471], reason='Further shaded southern compound roofs outside the seven reviewed baseline envelopes. No additional elevation or brewery ownership allocation is inferred in this pass.'),
            dict(sourceFids=[1107834], reason='Tiny interior outline in the northeast roof hole. Its plant/chimney attribution is unresolved; do not assign the existing remote boiler chimney or fill the source hole.'),
            dict(sourceFids=[1023233, 1043516, 1111779, 1264262], reason='Small western room/plant outlines and a minor source seam remain separate regional source context; no extra high industrial volumes are inferred.')])
    (ROOT / 'data/maps/bow-brewery-footprint-alignment.json').write_text(json.dumps(result, indent=2)+'\n')
    print('Bow Brewery: seven retained ranges in seven groups; one inferred 30 m chimney transferred with complete plinth containment.')


if __name__ == '__main__':
    build()
