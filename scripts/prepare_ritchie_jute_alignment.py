"""Author reviewed Ritchie jute mill exteriors and Goad process compartments.

The immutable saved scene supplies roof/elevation profiles. Source IDs and
compartment boundaries were reviewed against original Goad F4 and OS maps;
routine scene builds require only the saved alignment register.
"""
import json
import math
from pathlib import Path

from shapely import affinity, set_precision
from shapely.geometry import Point, Polygon, LineString, box, shape
from shapely.ops import split, unary_union

from factory_alignment_records import record_group
from prepare_ink_works_alignment import axis, rings
from prepare_three_mills_north_alignment import polygon

ROOT = Path(__file__).resolve().parents[1]
BASELINE = 'reference/footprint-model-alignment/remaining-trades-before.json'
SOURCE_CACHE = 'reference/footprint-model-alignment/remaining-trades-source-shapes.json'
BOUNDS = [-710, -880, -470, -620]
MAIN_IDS = ['ritchie-spinning', 'ritchie-calendering', 'ritchie-warehouse',
            'ritchie-press', 'ritchie-boilers', 'ritchie-preparing',
            'ritchie-smithy', 'ritchie-batching']
# Explicit fire-compartment cuts in the locally registered original Goad plan.
# Their endpoints are extended to the complete OS exterior. The precise roof
# divisions remain interpreted because OS maps the continuous mill body.
CUTS = {
    'spinning-east': [[1968, 432], [2000, 575], [2011, 632], [2028, 719], [2069, 884]],
    'batching-north': [[1806, 923], [2069, 884]],
    'warehouse-west': [[2078, 410], [2107, 548]],
    'boilers-north': [[2000, 575], [2107, 548]],
    'press-north': [[2107, 522], [2243, 490]],
    'press-west': [[2175, 502], [2175, 650]],
    'boiler-engine-gap': [[1800, 690], [2250, 690]],
    'smithy-north': [[2069, 884], [2230, 850]],
    'smithy-west': [[2069, 884], [2083, 955]],
}


def halfplane(cut, inside):
    """One explicitly selected side of an extended original-plan partition."""
    a, b = cut
    dx, dy = b[0]-a[0], b[1]-a[1]
    line = LineString([(a[0]-dx*1000, a[1]-dy*1000),
                       (b[0]+dx*1000, b[1]+dy*1000)])
    pieces = list(split(box(-10000, -10000, 10000, 10000), line).geoms)
    assert len(pieces) == 2
    return next(p for p in pieces if p.covers(Point(inside)))


def compartment_parts(target, registration):
    a, b, x, z = registration
    spine = CUTS['spinning-east']
    main_mask = Polygon([[-10000, -10000], [1800, -10000], *spine,
                        [4000, 10000], [-10000, 10000]])
    main_mask = main_mask.intersection(halfplane(CUTS['batching-north'], [1800, 800]))
    rounded_target = set_precision(target, .001)
    remaining = Polygon(rounded_target.exterior.coords, [h.coords for h in rounded_target.interiors])
    parts = []
    def take(mask):
        nonlocal remaining
        world_mask = affinity.affine_transform(mask, [a, -b, b, a, x, z])
        piece = polygon(remaining.intersection(world_mask).buffer(0))
        remaining = remaining.difference(piece).buffer(0)
        parts.append(piece)
    take(main_mask)
    take(halfplane(CUTS['warehouse-west'], [2000, 450]).intersection(
         halfplane(CUTS['boilers-north'], [2000, 450])))
    take(halfplane(CUTS['press-north'], [2150, 420]))
    take(halfplane(CUTS['press-west'], [2250, 550]).intersection(box(-10000, -10000, 10000, 650)))
    # This separator crosses the open engine-room recess, so the complete
    # supplied engine edge determines the boiler boundary, including its bevel.
    take(halfplane(CUTS['boiler-engine-gap'], [2050, 600]))
    # Reserve the smithy and batching; the eastern preparing range is the
    # remaining body north of the two southern cuts, beside the separate engine.
    smithy_mask = halfplane(CUTS['smithy-north'], [2150, 920]).intersection(
                  halfplane(CUTS['smithy-west'], [2200, 920]))
    preparing_mask = halfplane(CUTS['smithy-north'], [2130, 800]).intersection(
                     halfplane(CUTS['batching-north'], [2130, 800]))
    take(preparing_mask)
    take(smithy_mask)
    if remaining.geom_type == 'MultiPolygon':
        pieces = sorted(remaining.geoms, key=lambda p: p.area, reverse=True)
        assert sum(p.area for p in pieces[1:]) < .0001
        remaining = pieces[0]
    parts.append(polygon(remaining))
    def clean_spurs(p):
        # GEOS can leave zero-width boundary retracing at a cut/exterior
        # junction. Remove the backward collinear tip before millimetre
        # renderer rounding could turn that numerical spur into a crossing.
        points = list(p.exterior.coords)[:-1]
        changed = True
        while changed:
            changed = False
            for i, q in enumerate(points):
                prev, nxt = points[i-1], points[(i+1) % len(points)]
                u, v = (prev[0]-q[0], prev[1]-q[1]), (nxt[0]-q[0], nxt[1]-q[1])
                length = math.hypot(*u)
                if length and u[0]*v[0]+u[1]*v[1] > 0 and abs(u[0]*v[1]-u[1]*v[0])/length < 1e-7:
                    del points[i]
                    changed = True
                    break
        cleaned = polygon(Polygon(points, [h.coords for h in p.interiors]))
        assert cleaned.symmetric_difference(p).area < 1e-5
        return cleaned
    parts = [clean_spurs(p) for p in parts]
    assert unary_union(parts).symmetric_difference(target).area < .1
    return parts


def fitted_chimney(old, fid, base):
    centre = Point(round(base.centroid.x, 3), round(base.centroid.y, 3))
    # The renderer uses a 16-sided circular plinth with radius 1.2 times
    # the shaft radius. Inscribe its complete circumcircle, not just the shaft.
    radius = min(old['radius'], math.floor(centre.distance(base.boundary)/1.2*1000)/1000)
    return dict(id=old['id'], sourceFid=fid, sourcePolygons=[rings(base)],
        centre=[centre.x, centre.y], rotation=old['rotation'], radius=radius,
        priorRadius=old['radius'], priorCentre=[old['x'], old['z']],
        preservedHeight=old['height'], preservedSection=old['section'],
        plinthRadiusMultiplier=1.2, rendererPlinthSides=16,
        profileEvidence='Interpreted round shaft radius reduced so the complete 1.2-times-radius renderer plinth fits inside the independently mapped round OS symbol at the rounded mapped centroid. The symbol does not establish a measured shaft diameter; section and printed 200-foot height retained.',
        review='Original Goad F4 explicitly labels the round boiler-flue chimney 200 feet at the boiler/engine junction. Independent OS source 940622 occupies that junction; assigned by process-room context.')


def build():
    load = lambda p: json.loads((ROOT/p).read_text())
    before = load(BASELINE)
    models = {b['id']: b for b in before['buildings']}
    cached = load(SOURCE_CACHE)
    source = {fid: polygon(shape(cached[str(fid)])) for fid in [36, 37110, 382213, 8221, 940622]}
    registration = load('data/maps/factory-building-traces.json')['sources']['goad-f4-jute']['pixelToWorld']
    groups, buildings = [], []
    target = source[36]
    parts = compartment_parts(target, registration)
    group, rows = record_group('ritchie-main-mill', [36], source, models, MAIN_IDS,
        [models[i]['name'] for i in MAIN_IDS], target, parts,
        axis(target, models['ritchie-spinning']['rotation']),
        'The complete OS mill exterior contains spinning/winding/weaving, calendering, warehouse/bag room, store/press room, boilers/economiser, preparing, smithy and batching/store. Explicit Goad process boundaries divide the compound body; the exact roof boundaries remain interpreted. Western steps and southern attached projections remain within their mapped exterior.',
        review_prefix='Original July 1893 Goad F4 and cached OS five-foot comparison; prior heights and roof parameters retained. ')
    group['divisionParameters'] = dict(sourcePlan='goad-f4-jute', pixelToWorld=registration,
        planFramePartitionControls=CUTS, modelOrder=MAIN_IDS,
        evidence='Goad labelled process identities and their original compartment order. Engine-side upper boundary follows the independent OS engine-room exterior. Press-west and boiler-engine-gap selectors cross open OS recesses; they preserve complete detached room edges. Remaining partition controls extend the original Goad compartment divisions to mapped OS outer walls; precise roof splits remain interpreted.')
    groups.append(group); buildings.extend(rows)
    for key, fid, ident, evidence in [
        ('engine-room', 37110, 'ritchie-engine', 'Separate shaded OS engine room within the eastern process recess; Goad room D explicitly marks 750 HP, below the economiser and 200-foot boiler flue.'),
        ('office', 382213, 'ritchie-office', 'Separate small frontage office opposite the engine room. The prior Goad registration placed it too far north; the OS source retains its individual Carpenters Road exterior.'),
        ('jute-warehouse', 8221, 'ritchie-jute-store', 'Detached shaded OS warehouse south of the mill and west of Biggstaff Road housing. Original Goad room M labels JUTE WHSE; the open temporary-stack yard remains outside the model.')]:
        p = polygon(set_precision(source[fid], .001))
        g, rows = record_group('ritchie-'+key, [fid], source, models, [ident],
            [models[ident]['name']], p, [p], axis(p, models[ident]['rotation']), evidence,
            review_prefix='Original July 1893 Goad F4 and cached OS five-foot comparison; prior heights and roof parameters retained. ')
        groups.append(g); buildings.extend(rows)
    old = next(s for s in before['structures'] if s['id'] == 'stack-1017-2126-603')
    result = dict(source='Author-supplied london_buildings_1891-96_corr_v1.gpkg; cached OS London five-foot mosaic; original July 1893 Goad F4',
        sourceCRS='EPSG:3857 reprojected through BNG; scene origin E538900,N183209',
        baseline=BASELINE, method='Explicit process-room identity review, complete OS exterior coverage with interpreted Goad compartment cuts, eleven retained ranges and one independently mapped round 200-foot chimney. Prior elevations and roof profiles retained.',
        groups=groups, buildings=buildings, structures=[fitted_chimney(old, 940622, source[940622])],
        mapReview=['Unmodified cached OS five-foot mosaic inspected, then source and prior model overlays.',
                   'Original July 1893 Goad F4 inspected raw and with the complete OS exterior/source overlay; named industrial rooms, detached warehouse and printed 200-foot chimney reviewed.'],
        evidenceImages=[f'reference/footprint-model-alignment/ritchie-jute-{s}.png' for s in
            ['raw', 'source', 'before-models', 'goad', 'goad-source', 'after-models', 'after-goad']],
        deferred=[dict(feature='Textile trade label discrepancy', reason='Goad labels jute, spinning, winding and weaving; OS labels London Spinning Mills (Cotton). Retain the existing jute interpretation and record both map labels.'),
                  dict(feature='Roof divisions and levels', reason='The continuous OS outer body has no measured roof elevations. Goad identifies process compartments; exact roof cuts, roof glazing and metric heights remain inherited interpretations.'),
                  dict(feature='Temporary jute stacks', reason='Goad labels stacks in the open western yard. No permanent enclosed storage footprint inferred.'),
                  dict(feature='Detached warehouse two-floor annotation', reason='Original Goad M warehouse has a two-floor numeral; existing one-floor elevation retained for this footprint pass. Elevation review is deferred rather than silently changing the inherited profile.')])
    (ROOT/'data/maps/ritchie-jute-footprint-alignment.json').write_text(json.dumps(result, indent=2)+'\n')
    print('Ritchie jute: eleven ranges in four source groups; round 200-foot chimney with contained complete plinth.')


if __name__ == '__main__':
    build()
