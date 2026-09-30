"""Author reviewed Marshgate Lane chemical OS/Goad F3 matches."""
import json
import math
from pathlib import Path

from shapely import affinity, set_precision
from shapely.geometry import LineString, Point, box, shape
from shapely.ops import split, unary_union

from factory_alignment_records import record_group
from prepare_ink_works_alignment import axis, rings
from prepare_three_mills_north_alignment import polygon
from prepare_jeffrey_glue_alignment import render_change

ROOT = Path(__file__).resolve().parents[1]
SPECS = [
    ('chemical-west-drying', [546576], ['site939-880']),
    ('chemical-south-drying', [194335], ['site939-914']),
    ('chemical-middle', [21207], ['site939-918', 'site939-920']),
    ('chemical-east-engine', [788233, 994006], ['site939-928']),
    ('chemical-rectifying', [280205, 762991], ['site939-934']),
    ('chemical-riverside', [155012], ['site939-936', 'site939-938']),
]
REVIEWS = {
    'chemical-west-drying': 'Retained two-floor western drying body below the open yard 884. Its stepped west and south edges remain. The touching northeast one-floor cap is deferred separately, rather than raised to this range\'s two-floor height.',
    'chemical-south-drying': 'The separate Goad 914 drying house south of the western process ranges follows the stepped OS body. Its east notch around the separately mapped small plant symbol remains open; the southern timber shed and open flank strips are not absorbed into this roof.',
    'chemical-middle': 'Complete middle brick process body. The inherited model IDs 918/920 and south-bay allocation are retained as interpreted roof compartments: Goad places 920 on the broad brick body and 918/922 on the adjoining western timber process rooms. Exact internal room identification and the inherited transverse cut are unresolved; neither ID establishes a surveyed OS party wall.',
    'chemical-east-engine': 'Complete eastern engine/boiler band adjoining the already source-linked eastern chemical range. The touching northern small room joins the longer hatched engine/boiler room 928. The separate southern square chimney symbol and northern yard/tank symbols remain distinct.',
    'chemical-rectifying': 'Separate Goad RECTIFYING range 934 east of the main works includes its narrow eastern yellow compartment and broader brick body. Both supplied touching outlines belong to this retained range; prior height and roof interpretation retained.',
    'chemical-riverside': 'Separate southern yard block beside the creek, with Goad north room 936 and south room 938 retained as two roof compartments. The shared OS exterior remains complete and the rest of the yard stays open. The transverse room division is fitted from the Goad boundary at pixel y1748 between outer endpoints y1709 and y1777; OS does not establish that party wall.',
}


def build():
    load = lambda p: json.loads((ROOT / p).read_text())
    before = load('reference/footprint-model-alignment/marshgate-trades-before.json')
    models = {b['id']: b for b in before['buildings']}
    cached = load('reference/footprint-model-alignment/marshgate-trades-source-shapes.json')
    wanted = {f for _, fs, _ in SPECS for f in fs} | {1102599}
    source = {f: polygon(shape(cached[str(f)])) for f in wanted}
    groups, buildings = [], []
    for gid, fs, ids in SPECS:
        target = polygon(set_precision(unary_union([source[f] for f in fs]), .001))
        angle = axis(target, models[ids[0]]['rotation'])
        parts = [target]
        division = None
        if len(ids) == 2:
            # Retain useful roofs within a complete exterior. These cuts are
            # explicitly interpreted and do not claim an OS internal wall.
            fraction = 108/134 if gid == 'chemical-middle' else 39/68
            local = affinity.rotate(target, -angle, origin=(0, 0))
            _, low, _, high = local.bounds
            cut = low + (high-low)*fraction
            chord = affinity.rotate(LineString([(-10000, cut), (10000, cut)]),
                                    angle, origin=(0, 0))
            pieces = list(split(set_precision(target, 0), chord).geoms)
            assert len(pieces) == 2, gid
            parts = [polygon(set_precision(p, .001)) for p in sorted(pieces,
                key=lambda p: affinity.rotate(p, -angle, origin=(0, 0)).centroid.y)]
            division = dict(frameAngleDegrees=angle, localZCut=cut,
                northernDepthFraction=fraction,
                evidence=('Inherited 26-pixel south roof depth fitted at the southern end of the 134-pixel middle range; conflicting Goad room labels and exact party wall remain unresolved.' if gid == 'chemical-middle' else
                          'Goad drawn north/south boundary y1748 between outer endpoints y1709/y1777; fitted proportion, not a measured OS party wall.'))
        group, rows = record_group(gid, fs, source, models, ids,
            [models[i]['name'] for i in ids], target, parts, angle, REVIEWS[gid],
            review_prefix='Explicit raw OS/source/model and original July 1893 Goad F3 comparison; prior heights and roof parameters retained. ')
        if division:
            group['divisionParameters'] = division
        groups.append(group)
        buildings.extend(rows)

    old = next(s for s in before['structures'] if s['id'] == 'stack-939-1756-1440')
    base = source[1102599]
    centre = Point(round(base.centroid.x, 3), round(base.centroid.y, 3))
    angle = axis(base, old['rotation'])
    lo, hi = 0., old['radius']
    for _ in range(50):
        radius = (lo+hi)/2
        plinth = affinity.rotate(box(centre.x-radius*1.2, centre.y-radius*1.2,
            centre.x+radius*1.2, centre.y+radius*1.2), angle, origin=centre)
        if base.covers(plinth): lo = radius
        else: hi = radius
    radius = math.floor(lo*1000)/1000
    stack = dict(id=old['id'], sourceFid=1102599, sourcePolygons=[rings(base)],
        centre=[centre.x, centre.y], rotation=angle, radius=radius,
        priorRadius=old['radius'], priorCentre=[old['x'], old['z']],
        preservedHeight=old['height'],
        profileEvidence='Full rotated square plinth, half-side 1.2 times interpreted shaft radius, fitted inside the independent OS square symbol at the rounded mapped centroid. The symbol locates the base but establishes no measured shaft diameter. Retained square section and 22 m height remain typological estimates; no printed shaft height established.',
        review='Original Goad F3 pixel1756,1440 is the square chimney symbol immediately SOUTH of engine/boiler room928. OS1102599 occupies the same separate southern square. Northern symbols983100/994006 are not substituted by proximity. The inherited Marine glue engine / boilers name is geographically misleading here; retained pending a separate use/name review.')
    neighbors = {b['modelId']: b for b in buildings}
    neighbors.update({b['modelId']: b for b in load('data/maps/jeffrey-glue-footprint-alignment.json')['buildings']})
    result = dict(source='Author-supplied london_buildings_1891-96_corr_v1.gpkg; cached OS London five-foot mosaic',
        sourceCRS='EPSG:3857 reprojected through BNG; scene origin E538900,N183209',
        method='Explicit reviewed chemical-works exteriors, two retained interpreted roof divisions, and independently mapped square chimney plinth; existing source-linked west/east ranges and all prior elevations/roof parameters retained.',
        groups=groups, buildings=buildings, structures=[stack],
        renderChanges=[
            render_change(models, neighbors, 'site939-912', ['site939-880'],
                'The retained source-linked western process body 912 is unchanged. Correcting the taller western drying range 880 removes its previous misplaced overlap and restores the western process roof along that interface.'),
            render_change(models, neighbors, 'site939-926',
                ['site790-888', 'site790-890s', 'site790-892', 'site790-886s'],
                'The retained source-linked eastern chemical body 926 is unchanged. Correcting adjoining Jeffrey process ranges 888/890s/892 restores previously clipped northern process roof; the corrected covered-coppers 886s interface contributes a tiny bounded new corner clip.'),
        ],
        preservedSourceLinkedBuildings=[dict(modelId='site939-912', sourceFid=23412),
                                      dict(modelId='site939-926', sourceFid=7029)],
        mapReview=['Cached georeferenced OS London five-foot 1893 mosaic: raw map, source outlines and prior model overlays inspected.', 'Original July 1893 Goad volume F sheet3: chemical works rooms880/914/920/928/934/936/938 and square chimney south of engine room inspected.'],
        evidenceImages=[f'reference/footprint-model-alignment/marshgate-chemical-{suffix}.png' for suffix in
            ['raw', 'source', 'models', 'goad', 'goad-west', 'goad-chimney', 'after-models']],
        deferred=[
            dict(sourceFids=[954335], reason='Touching northeast cap of west drying house is the separate one-floor part on Goad880. No separate existing range; do not enlarge the two-floor retained roof over it.'),
            dict(sourceFids=[993338, 814511], reason='Small plant/tank symbol in the southern drying-house east notch and separate southern timber shed915 have no existing plant/range counterpart; retained mapped context without unsupported elevations.'),
            dict(sourceFids=[975256, 1022505, 1050895, 1255197, 1255644], reason='Small western process/furnace/yard symbols beside source-linked west range remain separate mapped context; no reliable corresponding existing volume or measured height.'),
            dict(sourceFids=[983100, 988407, 1135005], reason='Northern engine-yard/tank square and tiny chemical-range appendages have no independently identified existing full-height counterpart. They are not assigned to the nearest engine roof or chimney.'),
            dict(feature='Inherited site939-918/920 internal labels and Marine glue chimney name', reason='Goad identifies middle920, adjoining timber918/922, and the chimney south of chemical engine928. Existing useful geometry/elevations preserved; exact room/name correction deferred rather than speculative reclassification.')])
    (ROOT / 'data/maps/marshgate-chemical-footprint-alignment.json').write_text(json.dumps(result, indent=2)+'\n')
    print(f'Marshgate chemical: {len(buildings)} retained ranges in {len(groups)} groups; one mapped square chimney plinth; two existing source links preserved.')


if __name__ == '__main__':
    build()
