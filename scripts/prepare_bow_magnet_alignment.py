"""Prepare OS-reviewed Bow Bridge/Magnet Wharf exteriors and retained roofs."""
import json
from pathlib import Path

from shapely import affinity, set_precision
from shapely.geometry import LineString, Polygon, box, shape
from shapely.ops import split, unary_union

from factory_alignment_records import record_group
from prepare_ink_works_alignment import axis
from prepare_three_mills_north_alignment import polygon

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ('Explicit Bow Bridge/Magnet Wharf OS exterior match; previous interpreted '
          'heights and roof parameters retained. No Goad corroboration asserted. ')


def build():
    load = lambda p: json.loads((ROOT / p).read_text())
    before = load('reference/footprint-model-alignment/soap-wharves-before.json')
    models = {b['id']: b for b in before['buildings']}
    cached = load('reference/footprint-model-alignment/soap-wharves-source-shapes.json')
    fids = [2353, 794220, 541892, 183603, 787, 917385, 861481, 900939,
            7065, 9687, 94493, 1066963, 110013, 787670, 1168226, 75128, 769262,
            6798, 13037, 918851, 1011497, 1229557, 36727, 160418]
    source = {fid: polygon(shape(cached[str(fid)])) for fid in fids}

    def joined(fs):
        return polygon(set_precision(unary_union([source[f] for f in fs]), .001))

    works_fids = [787, 917385, 861481, 900939]
    works = joined(works_fids)
    # The large OS body has no reliable internal roof boundary. Retain the old
    # low western compartment and its relative area, inside the complete source
    # exterior; this cut is explicitly an elevation interpretation.
    # Use the inherited diagonal roof grid. The minimum bounding rectangle is
    # driven by the oblique river wall and would turn the roofs away from the
    # mapped eastern face; it is unsuitable for this irregular building.
    roof_angle = models['site789-os-3']['rotation']
    angle = roof_angle + 90
    local = affinity.rotate(works, -angle, origin=(0, 0))
    prior = [Polygon(models[f'site789-os-{i}']['footprint']) for i in [3, 4]]
    fraction = prior[1].area / sum(p.area for p in prior)
    lo, bottom, hi, top = local.bounds
    for _ in range(60):
        cut = (lo + hi) / 2
        area = local.intersection(box(-10000, -10000, cut, 10000)).area
        if area < works.area * fraction:
            lo = cut
        else:
            hi = cut
    cut = round((lo + hi) / 2, 3)
    # Compute the shared chord once. Independently rounding a clipped part and
    # subtracting it from the exterior creates a tiny triangular seam where the
    # chord meets the oblique bank edge. Splitting in floating precision gives
    # both parts identical intersection vertices before millimetre rounding.
    chord = affinity.rotate(LineString([(cut, -10000), (cut, 10000)]),
                            angle, origin=(0, 0))
    parts = list(split(set_precision(works, 0), chord).geoms)
    assert len(parts) == 2
    low, main = sorted(parts, key=lambda p: affinity.rotate(
        p, -angle, origin=(0, 0)).centroid.x)
    low, main = [polygon(set_precision(p, .001)) for p in [low, main]]

    foundry_fids = [13037, 918851, 1011497, 1229557]
    east_raw = source[36727]
    foundry = joined(foundry_fids)
    seam = east_raw.intersection(unary_union([source[f] for f in foundry_fids]))
    east = polygon(set_precision(east_raw.difference(
        unary_union([source[f] for f in foundry_fids])), .001))
    specs = [
        ('bow-granary', [2353], ['site789-os-1'], joined([2353]), None,
         'Complete shaded Bow Granary exterior, including its reentrant northern corners. The prior low elevation is retained; map shading establishes the building plan, not its storey count.'),
        ('bow-granary-east', [794220, 541892, 183603], ['site789-os-2'], joined([794220, 541892, 183603]), None,
         'Three touching shaded rooms beside the granary form its attached eastern range; earlier roof and height interpretation retained.'),
        ('bow-main-works', works_fids, ['site789-os-3', 'site789-os-4'], works, [main, low],
         'Complete broad soap/chemical works body with three attached projections. A western low roof compartment preserves the previous area proportion; its internal cut and uses remain interpretations. The unshaded eastern yard remains open.'),
        ('bow-north-west', [7065], ['site789-os-5'], joined([7065]), None,
         'Western long northern range; its full stepped riverside tip and the open yard to its west are retained.'),
        ('bow-north-east', [9687], ['site789-os-6'], joined([9687]), None,
         'Eastern long northern range follows its separate supplied outline; the neighbouring wharf body is not absorbed.'),
        ('bow-front-room', [94493, 1066963], ['site789-os-7'], joined([94493, 1066963]), None,
         'Detached southern yard/frontage range with its tiny touching northwest projection. Exact use remains unresolved from OS alone.'),
        ('bow-river-room', [110013, 787670, 1168226], ['site789-os-8'], joined([110013, 787670, 1168226]), None,
         'Three touching riverside rooms adjoining the northern western range. The narrow open separation to the western rear sheds is retained.'),
        ('bow-north-front', [75128, 769262], ['site789-os-9'], joined([75128, 769262]), None,
         'Lower frontage strip and touching eastern end room of the northern body; detached roadside rooms remain separate source context.'),
        ('magnet-west', [6798], ['site788-os-1'], joined([6798]), None,
         'Complete western iron-foundry body with the mapped reentrant court edge retained.'),
        ('magnet-main', foundry_fids, ['site788-os-2'], foundry, None,
         'Main foundry body and three tiny touching southern frontage compartments; mapped court and side wing remain distinct.'),
        ('magnet-east', [36727], ['site788-os-3'], east, None,
         'Separate eastern range. Its 2.276 m2 digitized overlap with source 13037 is removed in favour of the main foundry source; the raw outline is saved.'),
        ('magnet-court-wing', [160418], ['site788-os-4'], joined([160418]), None,
         'Existing small range is relocated from its overlapping eastern rectangle to the actual court-side wing; its low elevation and roof are retained. The tiny mapped court notch remains open.'),
    ]
    groups, buildings = [], []
    for gid, fs, ids, target, parts, division in specs:
        group, rows = record_group(gid, fs, source, models, ids,
            [models[i]['name'] for i in ids], target, parts or [target],
            axis(target, models[ids[0]]['rotation']), division, review_prefix=REVIEW)
        if gid == 'bow-main-works':
            for row in rows:
                row['footprintRotationDegrees'] = roof_angle
                row['comparison']['axisChangeDegrees'] = roof_angle-row['priorRotationDegrees']
            group['divisionParameters'] = dict(axisDegrees=angle, localX=cut,
                lowAreaFraction=fraction, evidence='Inherited relative envelope areas; inferred internal roof division, not a mapped party wall.')
        if gid == 'magnet-east':
            group['sourceReconciliation'] = dict(
                method='Remove documented intersecting source seam from east range; main foundry source has precedence.',
                precedenceGroup='magnet-main', excludedSourceFids=foundry_fids,
                removedAreaM2=seam.area,
                evidence='OS shows adjoining main/east roof compartments; the source edge intrudes about 0.3 m into its neighbour and does not support two overlapping buildings.')
        groups.append(group)
        buildings.extend(rows)
    assert len(buildings) == 13 and len(groups) == 12
    result = dict(
        source='Author-supplied london_buildings_1891-96_corr_v1.gpkg; cached OS London five-foot 1893 mosaic',
        sourceCRS='EPSG:3857 reprojected through BNG; scene origin E538900,N183209',
        method='Explicit OS-reviewed complete wharf exteriors and compartments; inherited height/roof interpretations; one recorded foundry source overlap.',
        groups=groups, buildings=buildings, structures=[],
        evidenceImages=[f'reference/footprint-model-alignment/bow-magnet-{kind}.png' for kind in ['raw', 'source', 'models']],
        deferred=[
            dict(sourceFids=[394946, 954626, 814043], reason='Separate shaded Bow yard sheds have no existing counterpart after preserving the main low roof compartment; retain regional source outlines pending ancillary range review.'),
            dict(sourceFids=[851394, 513574, 803238, 818116], reason='Small northern waterside and detached rooms remain regional source context; no room absorbed into the nearest wharf range.'),
            dict(sourceFids=[260466, 481365, 408954, 288389, 684363, 111463, 153755], reason='Neighbouring roadside rooms show distinct domestic/yard patterns; their use and separate ownership need a housing or ancillary pass.'),
            dict(sourceFids=[820699, 1252119], reason='Detached Magnet roadside room and tiny court-side toilet/plant notch remain source context. No supported chimney location is established at either wharf.')])
    (ROOT / 'data/maps/bow-magnet-footprint-alignment.json').write_text(json.dumps(result, indent=2)+'\n')
    print(f'Bow/Magnet: 13 retained ranges in 12 groups; foundry source overlap {seam.area:.6f} m2; OS-only evidence.')


if __name__ == '__main__':
    build()
