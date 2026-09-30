"""Author reviewed foundry, moulding and western chemical-range exteriors.

Source IDs and identities come from explicit raw OS/source/model inspection.
The immutable baseline supplies profiles only; ordinary builds read the saved
register and do not require the ignored evidence cache or map tiles.
"""
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
BASELINE = 'reference/footprint-model-alignment/remaining-trades-before.json'
REVIEW = ('Explicit cached OS five-foot raw plan, source outlines and immutable prior model comparison; '
          'inherited estimated heights and roof profiles retained. No original Goad corroboration asserted. ')
SPECS = [
    ('western-foundry-main', [1852], ['west-563-1', 'west-563-4'],
     ['London and Glasgow Foundry — main hall', 'London and Glasgow Foundry — southern return'],
     'Complete continuous eastern foundry body, including its southern return and western reentrants. The previous furnace envelope overlapped the main hall; two retained profiles divide the body along an interpreted chord through the mapped western recess.'),
    ('western-foundry-middle', [57404], ['west-563-2'],
     ['London and Glasgow Foundry — middle workshop'],
     'Separate shaded middle foundry workshop west of the printed works name. The previous broad moulding-shop envelope covered the unshaded labelled court; this correction retains the complete separate workshop.'),
    ('western-foundry-west', [61749], ['west-563-3', 'west-563-5'],
     ['London and Glasgow Foundry — western workshop', 'London and Glasgow Foundry — interpreted gate compartment'],
     'Complete shaded western foundry body beside Hancock Road. The former fitting shop and gate office overlapped; their existing profiles occupy disjoint interpreted compartments inside this body. OS establishes the exterior, not the exact internal division or room uses.'),
    ('western-moulding-main', [1070], ['west-941-1', 'west-941-2', 'west-941-4'],
     ['Ornamental Moulding Works — main workshop', 'Ornamental Moulding Works — northern projection', 'Ornamental Moulding Works — southwestern return'],
     'Complete large shaded moulding-works exterior. Three preserved profiles are divided at the mapped northern reentrant and southwestern notch, using interpreted chords. The low southwestern return follows the actual projecting end rather than the previous rectangle overlapping the main range.'),
    ('western-moulding-south', [155914], ['west-941-3'],
     ['Ornamental Moulding Works — southern end room'],
     'Independent lobed southern room at the mapped reentrant of the main body; its detailed outer corners and low interpreted profile remain separate from the main body.'),
    ('western-moulding-east', [30174], ['west-941-5'],
     ['Ornamental Moulding Works — southeastern shed'],
     'Complete separately shaded southeastern shed within the moulding-works yard, west of Three Mills Lane. The former small river-side envelope sampled only its northern corner. Existing road-corridor conflict is declared separately; the source exterior is not displaced or trimmed.'),
    ('western-chemical-middle', [4791], ['west-230-1'],
     ['Western chemical works — central hall (site 230 attribution unresolved)'],
     'Complete shaded rectangular central hall south of the printed Crown Chemical Works yard. OS does not identify this southern body as Crown or Imperial; retain the scene site ID while deferring tenant identity rather than asserting the inherited Crown mixing-hall name.'),
    ('western-chemical-west', [4998, 3433], ['west-230-2'],
     ['Western chemical works — western hall (site 230 attribution unresolved)'],
     'Two touching shaded western hall compartments with a common mapped boundary form the complete angular exterior. The former six-corner range covered only portions of both. OS does not establish the tenant name or the inherited process use.'),
    ('western-crown-southwest', [60948], ['west-230-3'],
     ['Crown Chemical Works — southwest process range (site 230 ID retained)'],
     'Separate shaded southwest process range beside the southern boundary of the printed Crown Chemical Works parcel. The previous east-process envelope ran north into its open yard and east into the adjacent range. Match this complete shaded body only; process use and site-number attribution remain interpreted.'),
    ('western-crown-southeast', [8484, 237824], ['west-230-4'],
     ['Crown Chemical Works — southeast range and end room (site 230 ID retained)'],
     'Two touching shaded components form the complete eastern range with its southern end room beside the Crown Chemical Works yard. Keep the low prior profile; no river-front ownership or store use is established by OS.'),
    ('western-chemical-rear', [55876], ['west-230-5'],
     ['Western chemical works — rear range (site 230 attribution unresolved)'],
     'Separate shaded rear range behind the central hall. The former U-shaped envelope enclosed an unshaded rear court and crossed several small boundaries; retain this complete shaded compartment without filling the rear court or merging unresolved small cells.'),
    ('western-crown-main', [609], ['west-230-6', 'west-230-7'],
     ['Crown Chemical Works — interpreted southern roof range (site 230 ID retained)', 'Crown Chemical Works — interpreted northern roof range (site 230 ID retained)'],
     'Complete large Crown Chemical Works roof body. Native OS pixels show the same diagonal hatch as the adjacent mapped roofs, distinct from the clear western court; the supplied extract classifies this source as a regular building. The two previous small office/shed envelopes lay within this body. Their useful height and roof profiles are retained across an explicitly interpreted transverse division, without asserting office/shed functions, floor counts or an OS internal wall.'),
]


def chord_parts(body, a, b, extension=100):
    """Cut on a declared mapped-corner chord extended past both exteriors."""
    dx, dz = b[0]-a[0], b[1]-a[1]
    line = LineString([(a[0]-extension*dx, a[1]-extension*dz), (b[0]+extension*dx, b[1]+extension*dz)])
    parts = [polygon(set_precision(p, .001)) for p in split(body, line).geoms]
    assert len(parts) == 2 and all(p.area > 2 for p in parts)
    return parts


def build():
    load = lambda p: json.loads((ROOT/p).read_text())
    before = load(BASELINE)
    models = {b['id']: b for b in before['buildings']}
    cached = load('reference/footprint-model-alignment/remaining-trades-source-shapes.json')
    source = {fid: polygon(shape(cached[str(fid)])) for _, fs, *_ in SPECS for fid in fs}
    groups, rows = [], []
    for gid, fids, ids, names, evidence in SPECS:
        target = polygon(set_precision(unary_union([source[f] for f in fids]), .001))
        reconciliation = None
        if gid == 'western-moulding-main':
            # The supplied main/body outlines overlap across a roughly 2 cm
            # shared-wall strip. Assign that strip to the separate end room;
            # the raw map shows adjoining walls, not overlapping volumes.
            overlap = source[1070].intersection(source[155914]).area
            target = polygon(set_precision(source[1070].difference(source[155914]), .001))
            reconciliation = dict(excludedSourceFids=[155914], removedAreaM2=overlap,
                evidence='Explicit OS common-wall review: supplied main body 1070 and southern room 155914 overlap by 0.166794 m² in a narrow digitisation seam. Assign the strip to the independently mapped southern room; preserve its complete exterior and do not overlap the two building volumes.')
        angle = axis(target, models[ids[0]]['rotation'])
        parts, division = [target], None
        if gid == 'western-foundry-main':
            chord = [[-830.106, 270.986], [-820.226, 288.688]]
            pieces = chord_parts(target, *chord)
            hall = max(pieces, key=lambda p: p.centroid.x)
            parts = [hall, min(pieces, key=lambda p: p.centroid.x)]
            division = dict(chords=[chord], method='Interpreted continuation of the main hall western wall from its mapped recess to the opposing southern wall; complete exterior retained.')
        elif gid == 'western-foundry-west':
            local = affinity.rotate(target, -angle, origin=(0, 0))
            low_x, low_z, high_x, high_z = local.bounds
            fraction = 5.805/(17.342+5.805)
            cut = low_x+(high_x-low_x)*fraction
            mask = affinity.rotate(box(-10000, -10000, cut, 10000), angle, origin=(0, 0))
            gate = polygon(set_precision(target.intersection(mask), .001))
            shop = polygon(set_precision(target.difference(gate), .001))
            parts = [shop, gate]
            division = dict(frameAngleDegrees=angle, localXCut=cut, westernGateWidthFraction=fraction,
                inheritedCompartmentWidthsMetres=[17.342, 5.805],
                method='Interpreted western gate strip retains the relative prior workshop/gate widths; OS supplies one continuous body, not this internal roof boundary.')
        elif gid == 'western-moulding-main':
            north_chord = [[-731.457, 352.242], [-709.786, 367.875]]
            west_chord = [[-746.871, 375.864], [-754.866, 370.468]]
            pieces = chord_parts(target, *north_chord)
            north = min(pieces, key=lambda p: p.centroid.y)
            remainder = max(pieces, key=lambda p: p.centroid.y)
            pieces = chord_parts(remainder, *west_chord, extension=.01)
            main, lean = sorted(pieces, key=lambda p: p.area, reverse=True)
            parts = [main, north, lean]
            division = dict(chords=[north_chord, west_chord],
                method='Interpreted roof chords join mapped northern and southwestern reentrants to opposite exterior walls; all source corners retained. No OS roof or party-wall transcription asserted.')
        elif gid == 'western-crown-main':
            local = affinity.rotate(target, -angle, origin=(0, 0))
            low_x, low_z, high_x, high_z = local.bounds
            prior_local = [affinity.rotate(Polygon(models[ident]['footprint']), -angle, origin=(0, 0)) for ident in ids]
            widths = [p.bounds[2]-p.bounds[0] for p in prior_local]
            northern_fraction = widths[1]/sum(widths)
            cut = low_x+(high_x-low_x)*northern_fraction
            mask = affinity.rotate(box(-10000, -10000, cut, 10000), angle, origin=(0, 0))
            north = polygon(set_precision(target.intersection(mask), .001))
            south = polygon(set_precision(target.difference(north), .001))
            parts = [south, north]
            division = dict(frameAngleDegrees=angle, localXCut=cut,
                northernWidthFraction=northern_fraction, inheritedProfileWidthsMetres=widths,
                method='Interpreted transverse roof cut preserves the relative widths of the two prior profiles in the complete source-body frame. OS hatch establishes the exterior only; no mapped internal division, office/shed identity or measured elevations asserted.')
        group, corrections = record_group(gid, fids, source, models, ids, names,
            target, parts, angle, evidence, review_prefix=REVIEW)
        if division:
            group['divisionParameters'] = division
        if reconciliation:
            group['sourceReconciliation'] = reconciliation
        assert unary_union(parts).symmetric_difference(target).area < .001
        assert all(parts[i].intersection(parts[j]).area < .001 for i in range(len(parts)) for j in range(i))
        groups.append(group)
        rows.extend(corrections)
    structure_ids = {'west-563-4-stack', 'west-941-1-stack', 'west-230-3-stack', 'west-230-1-stack'}
    structures = []
    corrections = {b['modelId']: b for b in rows}
    for old in before['structures']:
        if old['id'] not in structure_ids:
            continue
        parent_id = old['parentBuildingId']
        row = corrections[parent_id]
        body = Polygon(row['worldFootprint'], row['worldHoles'])
        angle = row['footprintRotationDegrees']
        theta = math.radians(angle)
        u, v = old['localPosition']
        centre = Point(round(round(body.centroid.x, 3)+u*math.cos(theta)-v*math.sin(theta), 3),
                       round(round(body.centroid.y, 3)+u*math.sin(theta)+v*math.cos(theta), 3))
        half = old['radius']*1.2
        plinth = affinity.rotate(box(centre.x-half, centre.y-half, centre.x+half, centre.y+half), angle, origin=centre)
        assert body.covers(plinth), old['id']
        local = affinity.rotate(body, -angle, origin=body.centroid)
        low_x, low_z, high_x, high_z = local.bounds
        fractions = [(body.centroid.x+u-low_x)/(high_x-low_x), (body.centroid.y+v-low_z)/(high_z-low_z)]
        structures.append(dict(id=old['id'], centre=[centre.x, centre.y], rotation=angle,
            priorCentre=[old['x'], old['z']], preservedHeight=old['height'],
            parentBuildingId=parent_id, parentFractions=fractions,
            preservedLocalPosition=old['localPosition'], priorStructure=old,
            review='Existing inferred process chimney transferred with its unchanged parent-local offset into the corrected parent range. '
                'Full 1.2-times-radius plinth remains contained. OS does not establish an independent chimney base here; '
                'this is an inherited modelling interpretation, not a mapped position or measured shaft. No nearby circle or small symbol is used as a source match. '
                'All previous shaft height, radius, taper, material and section parameters are retained.'))
    assert len(structures) == 4
    result = dict(source='Author-supplied london_buildings_1891-96_corr_v1.gpkg; cached OS London five-foot 1893 mosaic',
        sourceCRS='EPSG:3857 reprojected through BNG; scene origin E538900,N183209',
        method='Explicit OS foundry, moulding and western chemical exteriors, including the complete hatched Crown roof body 609; interpreted cuts preserve all seventeen existing height and roof profiles. Four inferred shafts retain their profiles and parent-local offsets within corrected parents. Site 230 tenant identity remains partly unresolved.',
        groups=groups, buildings=rows, structures=structures,
        immutableBaseline=BASELINE,
        mapReview=['Unmodified georeferenced OS five-foot mosaic inspected, followed by labelled supplied-source and immutable model overlays; enlarged foundry, moulding, chemical and rear-court details inspected.',
            'Available original Goad F2, F3, F17, F18 and F19 inspected for geographic coverage. None covers these western sites; the relevant F16 sheet is absent from the local cache. No original Goad corroboration, floor annotation or shaft height is claimed.',
            'Source 609 independently re-examined at native pixel resolution and with nearest-neighbour enlargement. Clean patch comparisons establish diagonal roof hatch matching known roof bodies 3433 and 8484, unlike the clear western court; supplied buil_class=regular corroborates the building classification. Empty interior detail does not establish open yard.'],
        evidenceImages=[f'reference/footprint-model-alignment/western-trades-{suffix}.png' for suffix in ['raw', 'source', 'models', 'after-models']]
            +[f'reference/footprint-model-alignment/western-trades-{site}-{suffix}.png' for site in ['foundry', 'moulding', 'chemical'] for suffix in ['raw', 'source', 'models', 'after-models']]
            +['reference/footprint-model-alignment/western-trades-road-conflict.png']
            +[f'reference/footprint-model-alignment/western-trades-609-{suffix}.png' for suffix in ['native', 'nearest', 'clean-style-comparison']],
        contextConflicts=[dict(modelId='west-941-5', sourceFids=[30174],
            context='Immutable baseline Three Mills Lane clearance corridor, superseded by remaining-trades-context-alignment.json',
            baselineIntersectionAreaM2=4.938650859901102, maximumIntersectionAreaM2=4.95,
            resolutionRegister='data/maps/remaining-trades-context-alignment.json',
            evidence='Raw OS places the shaded shed immediately northwest of Three Mills Lane. The supplied complete exterior entered the baseline interpreted road clearance corridor by about 4.94 m². Parent context review corrected the route; this footprint register retains the complete shed without shifting or trimming it.')],
        siteIdentityReview=dict(siteId=230, inheritedSiteName='Imperial Works (washing chemicals)',
            inheritedBuildingNamePrefix='Crown chemical works',
            mappedNorthernRoofBody='Crown Chemical Works', mappedRoofSourceFid=609,
            matchedCrownRangeIds=['west-230-3', 'west-230-4', 'west-230-6', 'west-230-7'],
            unresolvedTenantRangeIds=['west-230-1', 'west-230-2', 'west-230-5'],
            evidence='The printed Crown label lies on the northern diagonally hatched roof body 609, with separate shaded eastern ranges beside it. The west/south bodies stand separately across the clear western court. Supplied site 230 spans these bodies but is called Imperial washing chemicals. Preserve numeric scene identity, use neutral names for southern bodies, and defer tenant reconciliation to the site-context register.'),
        deferred=[dict(sourceFids=[917595, 1191902, 1144930, 117857, 930281, 1186065], reason='Foundry small circles and ancillary edge symbols have no established chimney/function correspondence; not used to replace the inferred shaft.'),
            dict(sourceFids=[999349, 943501, 997319], reason='Small moulding-works northern edge symbols remain ancillary context; no positive chimney identity or current counterpart.'),
            dict(sourceFids=[350020, 532590, 974528, 89127, 1098125, 202006], reason='Separate western boundary-side rooms and tiny symbols beside the Crown main roof body have no current counterpart. The open court west of the main body is excluded, while the hatched main roof 609 is retained completely.'),
            dict(sourceFids=[783209, 842951, 1118090, 920483, 1006894], reason='Small chemical hall attachments or independent plant symbols require room/base classification; no unsupported addition or shaft correspondence.'),
            dict(sourceFids=[809090, 821004, 743842, 795218, 902909], reason='Separate rear cells and open-court boundaries remain context; retain the clearly shaded east rear range 55876 without filling the courtyard.')])
    (ROOT/'data/maps/western-trades-footprint-alignment.json').write_text(json.dumps(result, indent=2)+'\n')
    print('Western trades: seventeen retained ranges in twelve reviewed groups; complete Crown roof 609; four inferred shafts transferred with unchanged profiles; tenant identity deferred.')


if __name__ == '__main__':
    build()
