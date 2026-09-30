"""Author reviewed St Thomas mill and Augustus Smith OS/Goad F3 matches."""
import json
import math
from pathlib import Path

from shapely import affinity, set_precision
from shapely.geometry import LineString, Point, Polygon, box, shape
from shapely.ops import split, unary_union

from factory_alignment_records import record_group
from prepare_ink_works_alignment import axis, rings
from prepare_three_mills_north_alignment import polygon

ROOT = Path(__file__).resolve().parents[1]
# Preserve the pre-review channel heads. Goad establishes a covered millrace
# interface and an explicitly labelled warehouse overhang, not displaced banks.
WATER_POLYGONS = {
    8: [[[[-1050.0, -441.85], [-1028.83, -427.61], [-1020.58, -417.71], [-1006.66, -398.39], [-1003.07, -388.58], [-992.06, -363.96], [-979.54, -342.71], [-975.12, -335.93], [-968.32, -328.21], [-960.33, -320.19], [-941.91, -303.89], [-911.66, -258.31], [-892.29, -224.89], [-885.47, -211.5], [-891.62, -207.77], [-908.89, -240.69], [-921.02, -260.61], [-933.66, -278.85], [-943.71, -290.93], [-966.76, -314.12], [-987.59, -337.37], [-998.67, -357.1], [-1008.61, -378.08], [-1011.28, -379.35], [-1013.28, -391.42], [-1028.65, -413.26], [-1040.57, -425.4], [-1050.0, -432.64], [-1050.0, -441.85]]]],
    9: [[[[-868.07, -186.6], [-827.84, -113.58], [-813.6, -115.74], [-795.3, -121.81], [-787.36, -125.7], [-782.71, -115.81], [-823.43, -102.01], [-835.04, -97.47], [-842.76, -93.25], [-846.45, -98.49], [-839.4, -104.81], [-840.12, -123.48], [-844.16, -131.94], [-850.48, -142.01], [-868.38, -164.78], [-875.27, -178.28], [-873.02, -179.9], [-874.55, -182.42], [-868.07, -186.6]]]],
}
SPECS = [
    ('st-thomas-main', [5319], ['site257-mill']),
    ('st-thomas-engine', [828523], ['site257-engine']),
    ('st-thomas-south-room', [832881, 966459], ['site257-south']),
    ('smith-brush', [64628, 764378], ['site258-brush']),
    ('smith-fibre', [22190, 553943, 442961], ['site258-fibre']),
    ('smith-drying', [41501], ['site258-dry']),
    ('smith-warehouse', [602713], ['site258-warehouse']),
    ('smith-coppers-stoves', [19138, 842299, 701026], ['site258-coppers', 'site258-stoves']),
    ('smith-east-drying', [724119, 936507, 820609], ['site258-east-dry']),
]
REVIEWS = {
    'st-thomas-main': 'Complete St Thomas corn mill / Edward Barry patent-food exterior, including the west and north steps and the enclosed chimney opening. Goad F3 shows the four-floor main body; existing selected elevation retained.',
    'st-thomas-engine': 'Small southern attached timber engine/boiler bay, Goad E & B / 34. The separate room 858 remains a separate retained range.',
    'st-thomas-south-room': 'Separate southern mill room 858 and its touching small east projection. The inherited Goad rectangle 1010,1817 was wrongly placed in the neighbouring Augustus Smith warehouse; room 858 is identified by its attachment immediately south of the mill engine bay, not by nearest distance to that misplaced rectangle. Existing low elevation retained; exact ancillary use remains uncertain.',
    'smith-brush': 'Goad two-floor brush-factory frontage and its touching southeast end compartment follow both supplied OS outlines; the northern yard remains open.',
    'smith-fibre': 'Complete western fibre-process body and attached rooms around the independently mapped southern chimney. The central enclosed chimney opening remains empty. Internal uses and relative elevations remain inherited interpretations.',
    'smith-drying': 'Complete western timber warehouse/drying room, with its western overhanging corner and stepped southern edge. Retain the original drying-room interpretation and low roof.',
    'smith-warehouse': 'Separate southern office/dwelling/warehouse band, shown as OFF & D below the timber WHSE on Goad. The existing warehouse model is retained on this distinct small OS exterior; exact office/store allocation is unresolved.',
    'smith-coppers-stoves': 'Goad northern coppers/fibre-machinery compartments and southern stoves/STORE room fitted within the complete OS body. A transverse cut follows the inherited 29:56 compartment depths; its precise location remains interpreted. The two attached northern timber compartments belong to the coppers range.',
    'smith-east-drying': 'Three touching eastern drying-room outlines form the separate Goad two-floor drying range. All stepped end compartments retained.',
}


def build():
    load = lambda p: json.loads((ROOT / p).read_text())
    before = load('reference/footprint-model-alignment/mill-brush-brewery-before.json')
    models = {b['id']: b for b in before['buildings']}
    cached = load('reference/footprint-model-alignment/mill-brush-brewery-source-shapes.json')
    wanted = {f for _, fs, _ in SPECS for f in fs} | {1073893, 1041835}
    source = {f: polygon(shape(cached[str(f)])) for f in wanted}
    groups, buildings = [], []
    for gid, fs, ids in SPECS:
        target = polygon(set_precision(unary_union([source[f] for f in fs]), .001))
        angle = axis(target, models[ids[0]]['rotation'])
        parts = [target]
        if gid == 'smith-coppers-stoves':
            # Goad's horizontal coppers/stoves boundary applies to the broad
            # east body. The two northern timber rooms stay with the coppers.
            local = affinity.rotate(source[19138], -angle, origin=(0, 0))
            _, low, _, high = local.bounds
            cut = low + (high-low)*29/85
            chord = affinity.rotate(LineString([(-10000, cut), (10000, cut)]),
                                    angle, origin=(0, 0))
            body_parts = list(split(set_precision(source[19138], 0), chord).geoms)
            assert len(body_parts) == 2
            north, south = sorted(body_parts, key=lambda p: affinity.rotate(
                p, -angle, origin=(0, 0)).centroid.y)
            parts = [polygon(set_precision(unary_union([north, source[842299], source[701026]]), .001)),
                     polygon(set_precision(south, .001))]
        group, rows = record_group(gid, fs, source, models, ids,
            [models[i]['name'] for i in ids], target, parts, angle, REVIEWS[gid],
            review_prefix='Explicit cached OS five-foot and original July 1893 Goad F3 comparison; prior heights and roof parameters retained. ')
        if gid == 'smith-coppers-stoves':
            group['divisionParameters'] = dict(frameAngleDegrees=angle,
                localZCut=cut, northernMainDepthFraction=29/85,
                evidence='Inherited Goad coppers/stoves compartment depths; internal roof cut remains interpreted.')
        if gid == 'st-thomas-south-room':
            group['correctedIdentity'] = dict(goadRoom='858',
                priorRectPixels=models[ids[0]]['rectPixels'],
                evidence=REVIEWS[gid])
        if gid in ['st-thomas-main', 'smith-drying']:
            river_id = 8 if gid == 'st-thomas-main' else 9
            water = unary_union([Polygon(p[0], p[1:]) for p in WATER_POLYGONS[river_id]])
            interpretation = ('Covered millrace interface' if river_id == 8 else 'Mapped warehouse overhang')
            evidence = ('Goad F3 draws the blue Pudding Mill channel terminating against the Barry/St Thomas mill north wall, disappearing under the roof, and restarting below its engine/boiler bay. OS retains the upper channel head against the mill notch. A covered water interface is inferred; no surveyed buried channel route or structural span is claimed.' if river_id == 8 else
                'Goad F3 explicitly labels OVERHANGING along the western timber WHSE projection above the lower Pudding Mill water head. The OS warehouse source has the corresponding stepped west edge. Retain both the mapped roof exterior and pre-review channel head; exact supporting structure and level remain unknown.')
            rows[0]['waterReview'] = evidence
            saved_body = Polygon(rows[0]['worldFootprint'], rows[0]['worldHoles'])
            rows[0]['waterInterface'] = dict(riverId=river_id,
                observedOverlapAreaM2=saved_body.intersection(water).area,
                interpretation=interpretation, evidence=evidence,
                referenceCrop='reference/footprint-model-alignment/mill-brush-route-goad.png',
                osReferenceCrop='reference/footprint-model-alignment/mill-brush-south-raw.png',
                retainedRiverPolygons=WATER_POLYGONS[river_id])
        groups.append(group)
        buildings.extend(rows)

    structures = []
    for ident, fid, note in [
        ('stack-258-1149-1128', 1073893, 'Goad printed 50-foot northern fibre-works boiler chimney inside the separate northern works body; OS source 1166 retains its opening and is deferred as an unmodelled building.'),
        ('stack-258-1129-1732', 1041835, 'Goad printed 60-foot southern fibre-works chimney in the enclosed opening between the fibre-process compartments.'),
    ]:
        old = next(s for s in before['structures'] if s['id'] == ident)
        base = source[fid]
        centre = Point(round(base.centroid.x, 3), round(base.centroid.y, 3))
        angle = axis(base, old['rotation'])
        # The renderer uses a square plinth whose half-side is 1.2*radius.
        # Fit that square, rather than a circular proxy, to the actual symbol.
        lo, hi = 0., old['radius']
        for _ in range(50):
            radius = (lo+hi)/2
            plinth = affinity.rotate(box(centre.x-radius*1.2, centre.y-radius*1.2,
                centre.x+radius*1.2, centre.y+radius*1.2), angle, origin=centre)
            if base.covers(plinth): lo = radius
            else: hi = radius
        radius = math.floor(lo*1000)/1000
        structures.append(dict(id=ident, sourceFid=fid, sourcePolygons=[rings(base)],
            centre=[centre.x, centre.y], rotation=angle, radius=radius,
            priorRadius=old['radius'], priorCentre=[old['x'], old['z']],
            preservedHeight=old['height'],
            profileEvidence='Interpreted square shaft radius reduced to fit its complete 1.2-times-radius square plinth inside the independent OS chimney symbol at the rounded centroid. The symbol locates the base; it does not establish a measured shaft diameter. Existing square section and printed height retained.',
            review=note+' Matched by the Goad room/boiler context and OS opening; no nearest-building assignment.'))

    result = dict(source='Author-supplied london_buildings_1891-96_corr_v1.gpkg; cached OS London five-foot mosaic',
        sourceCRS='EPSG:3857 reprojected through BNG; scene origin E538900,N183209',
        method='Reviewed complete mill and southern Augustus Smith OS exteriors with Goad F3 room identities; one corrected misplaced mill-room identity, an interpreted coppers/stoves cut, two independently mapped chimney bases, and all prior elevations/roof parameters retained.',
        groups=groups, buildings=buildings, structures=structures,
        mapReview=['Cached georeferenced OS London five-foot 1893 mosaic, raw and source/model overlays at southern works and northern chimney.', 'Original July 1893 Goad volume F sheet 3; southern rooms, room 858, and printed 50/60-foot chimney symbols inspected.'],
        evidenceImages=[f'reference/footprint-model-alignment/mill-brush-{suffix}.png' for suffix in
            ['raw','source','models','south-raw','south-source','south-models','north-raw','north-source','north-models','goad','goad-models','goad-mill','after-models']],
        deferred=[
            dict(sourceFids=[1166, 492753, 834044, 802229], reason='Separate northern fibre works and touching rooms have no existing range counterpart. The northern chimney is independently located; broad northern buildings remain source context pending their own range/elevation review.'),
            dict(sourceFids=[848220, 839475, 864605, 744441, 917272], reason='Small southern process/boiler rooms beyond the existing stoves model remain mapped context; do not absorb them into the nearest retained roof.'),
            dict(sourceFids=[925525, 971318, 1267882, 1243388], reason='Tiny yard and side-room symbols remain deferred ancillary context, without unsupported full-height additions.'),
            dict(sourceFids=[1075308, 1100484], reason='Corn mill small northern symbol and enclosed mill chimney base are retained as source evidence/opening. There is no current corn mill chimney model; this pass adds no chimney or unsupported height.'),
            dict(sourceFids=[105484, 832905, 992504], reason='Western office/store rooms belong to the adjacent Howards side on Goad; not reassigned to the corn mill by proximity.')])
    (ROOT / 'data/maps/mill-brush-footprint-alignment.json').write_text(json.dumps(result, indent=2)+'\n')
    print(f'Mill/brush: {len(buildings)} retained ranges in {len(groups)} groups; two mapped square chimney plinths.')


if __name__ == '__main__':
    build()
