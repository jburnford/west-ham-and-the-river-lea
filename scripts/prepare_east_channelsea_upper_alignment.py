"""Restore reviewed enclosed roofs in the upper eastern Channelsea strip.

The source extract supplies exteriors only. Heights, floor counts, roof pitches
and bays below are explicit new modelling estimates, never surveyed elevations.
Open coal sidings, platforms, wharf yards and stone-working cells are excluded.
"""
import json
import math
from pathlib import Path

from shapely import affinity, set_precision
from shapely.geometry import Polygon, shape
from shapely.ops import unary_union

from factory_alignment_records import record_group
from prepare_ink_works_alignment import axis, rings
from prepare_three_mills_north_alignment import polygon

ROOT = Path(__file__).resolve().parents[1]
BASELINE = 'reference/footprint-model-alignment/east-channelsea-before.json'
CACHE = 'reference/footprint-model-alignment/east-channelsea-source-shapes.json'
BOUNDS = [-260, -920, 130, -220]
# IDs were established by inspection of the unmodified OS plan and source
# overlays. Industrial sites are named on that plan; station identity follows
# the labelled Stratford Market (Vegetables) roof, alongside Goods/Coal Depot.
SPECS = [
    ('globe-main', 9003, [2945, 343877], 'Globe Mill crushing range and eastern annex', 6.9, 2,
     'Shaded eastern body explicitly labelled Globe Mill (Crushing), north of the moat and west of the north–south railway. Keep its eastern attached annex; exclude the unshaded numbered roof/yard frame along the north side.'),
    ('globe-west', 9003, [27970, 73030, 913372, 1013095, 1108307], 'Globe Mill western crushing range', 3.8, 1,
     'Contiguous shaded western compartments immediately west of the labelled eastern crushing mill. Include the shaded western-end projection and retain supplied party-wall seams in provenance; one low roof interpretation covers the complete joined exterior.'),
    ('globe-south-west', 9003, [8500], 'Globe Mill southern western range', 3.8, 1,
     'Western shaded roof compartment of the continuous Globe Mill southern body immediately north of the Moat. The source party wall divides it from the central range; the clear lane to the small northern compound building remains open.'),
    ('globe-south-central', 9003, [39385], 'Globe Mill southern central range', 3.8, 1,
     'Central shaded roof compartment of the continuous Globe Mill body along the north bank of the Moat. Retain the supplied party walls and recessed eastern seam rather than filling the working lane north.'),
    ('globe-south-east', 9003, [9303], 'Globe Mill southern eastern range', 3.8, 1,
     'Eastern shaded southern Globe Mill roof beside the Moat, below the explicitly labelled crushing mill. Its northern lane remains open. The small circular outline1103852 at the roof edge is not an independently established enclosed roof or chimney and remains deferred.'),
    ('globe-riverside', 9003, [9468], 'Globe Mill western riverside range', 3.8, 1,
     'Detached long diagonally shaded roof between Channelsea and the Globe Mill compound, north of the Moat mouth. Keep the separating access lane and the river outside its complete supplied exterior.'),
    ('globe-compound', 9003, [835513, 756608, 288654, 752568], 'Globe Mill small western compound building', 3.8, 1,
     'Four contiguous diagonally shaded roof compartments in the small detached building between the Victoria Stone Works southern wall and Globe Mill southern roofs. One joined exterior retains the four supplied source identities; white lanes on all sides stay open.'),
    ('victoria-stone-main', 9004, [198], 'Victoria Stone Works western shed', 5.5, 1,
     'Large shaded enclosed western body inside the labelled Victoria Stone Works, bounded by riverside siding and eastern access lane. The separate unshaded 20-cell working grid is excluded; the open railway fan remains outside this building.'),
    ('victoria-corn-main', 497, [4975, 304906], 'Victoria Mills corn mill and attached projection', 6.9, 2,
     'Shaded riverside corn-mill body immediately west of the printed Victoria Mills (Corn) label. Include the attached southeastern projection; keep the northern Caledonian Wharf shed under its own reviewed site identity.'),
    ('stratford-market-roof', 9002, [79], 'Stratford Market covered vegetable-market range', 6.0, 1,
     'Long shaded roof explicitly labelled Stratford Market (Vegetables), beside the Great Eastern Goods & Coal Depot and Woolwich branch. Western source2832 is a separate narrow track-side/loading strip whose complete continuous roof is not established. Northern source1539 is a shaded mapped covered station-associated body, distinct from the white platform immediately east; its precise enclosure, canopy arrangement and height remain unresolved. Both features are deferred for separate context/architectural interpretation rather than included in this market roof.'),
    ('caledonian-riverside', 9005, [24043], 'Caledonian Wharf riverside shed', 3.8, 1,
     'Small shaded riverside body on the southern edge of the labelled Caledonian Wharf, immediately north of the independently mapped Victoria corn mill. Exact wharf tenure boundary remains approximate; the OS building identity is distinct.'),
    ('caledonian-east', 9005, [82361], 'Caledonian Wharf eastern covered strip', 3.8, 1,
     'Separate stippled southern strip inside the Caledonian Wharf boundary, east of its riverside shed. Open wharf ground between this strip and the road remains outside the model.'),
    ('halling-north', 9006, [183011], 'Halling Wharf northern riverside shed', 3.8, 1,
     'Small shaded rectangular roof on the north edge of the printed Halling Wharf parcel, south of Channelsea Road. Wharf platform and open coal-depot yard are excluded.'),
    ('halling-south', 9006, [34815], 'Halling Wharf southern warehouse', 3.8, 1,
     'Long shaded southern Halling Wharf body beside the access entrance and coal-depot boundary. Its source outline retains the angled ends and roadside projection.'),
    ('stratford-wharf-north', 9007, [31966, 201071], 'Stratford Wharf northern warehouse', 3.8, 1,
     'Joined shaded northern warehouse at the labelled Stratford Wharf, west of the Short Road domestic frontage. Repeated dwelling yards east and the large unshaded wharf working area south are excluded.'),
]
SITE_NAMES = {497: 'Victoria Mills (Corn)', 9002: 'Stratford Market (Vegetables)',
    9003: 'Globe Mill (Crushing)', 9004: 'Victoria Stone Works',
    9005: 'Caledonian Wharf', 9006: 'Halling Wharf', 9007: 'Stratford Wharf'}


def build():
    load = lambda p: json.loads((ROOT/p).read_text())
    before = load(BASELINE)
    cached = load(CACHE)
    wanted = {fid for _, _, fs, *_ in SPECS for fid in fs}
    source = {fid: polygon(shape(cached[str(fid)])) for fid in wanted}
    previous_ids = {b['id'] for b in before['buildings']}
    groups, buildings, additions = [], [], []
    for key, site, fids, name, height, storeys, evidence in SPECS:
        ident = 'east-upper-'+key
        assert ident not in previous_ids
        raw = unary_union([source[fid] for fid in fids])
        exclusions = [9303] if key == 'globe-south-central' else []
        reconciled = raw.difference(unary_union([source[fid] for fid in exclusions])) if exclusions else raw
        target = polygon(set_precision(reconciled, .001))
        angle = axis(target, 0)
        local = affinity.rotate(target, -angle, origin=(0, 0))
        x0, z0, x1, z1 = local.bounds
        width, depth = x1-x0, z1-z0
        roof_axis = 'x' if width >= depth else 'z'
        span = depth if roof_axis == 'x' else width
        bays = max(1, math.ceil(span/17))
        rise = min(3.5, max(1.2, span/bays*.22))
        outer, holes = rings(target)[0], rings(target)[1:]
        addition = dict(id=ident, siteId=site, source='os-1893', name=name,
            worldFootprint=outer, worldHoles=holes, footprintRotationDegrees=angle,
            storeysEstimate=storeys, material='brick', roof='gable',
            eavesHeight=height, roofRise=rise, roofAxis=roof_axis, roofBays=bays,
            footprintEvidence=evidence+' The supplied OS exterior is independently registered; no industrial parcel is extruded.',
            heightEvidence='New interpreted '+str(storeys)+'-floor profile; metric eaves height is a conservative modelling estimate. The OS footprint does not supply storey count or measured elevation.',
            roofEvidence='New interpreted industrial pitched roof and repeated bays. Exact pitch, ridge levels, building materials and roof arrangement are not measured by this plan.')
        synthetic = dict(addition, footprint=outer, height=height, rotation=angle)
        g, rows = record_group('east-upper-'+key, fids, source, {ident: synthetic},
            [ident], [name], target, [target], angle, evidence, additional=True,
            review_prefix='Raw georeferenced OS five-foot plan and source outlines inspected. Newly added range; elevation and roof profile are declared interpretations. ')
        g['previousUnionIoU'] = 0
        if exclusions:
            g['sourceReconciliation'] = dict(excludedSourceFids=exclusions,
                removedAreaM2=raw.area-reconciled.area,
                evidence='Adjacent supplied39385 and9303 overlap by1.023m² along their separately digitized wavy shared roof seam. Native OS shows one party-wall seam and a continuous southern roof exterior. Assign the overlap to9303 and subtract it from39385; preserve every exterior point and the complete compound union.')
        for row in rows:
            row.update(priorFootprint=[], additionalModel=True,
                profileEvidence=addition['heightEvidence']+' '+addition['roofEvidence'])
        groups.append(g); buildings.extend(rows); additions.append(addition)
    existing_sites = {s['id'] for s in before['sites']}
    sites = [dict(id=site, name=name, coverage='Explicit OS exterior review; new interpreted building elevations',
        sources=['os-1893'],
        notes='Named on the period OS five-foot map. Building outlines are mapped; heights, materials, storeys and roof profiles remain modelling estimates. Numeric site IDs above9000 group context roofs and do not claim original cadastral parcel identifiers.')
        for site, name in SITE_NAMES.items() if site not in existing_sites]
    result = dict(source='Author-supplied london_buildings_1891-96_corr_v1.gpkg; cached OS London five-foot mosaic',
        sourceCRS='EPSG:3857 reprojected through BNG; scene origin E538900,N183209', baseline=BASELINE,
        method='Restore independently reviewed enclosed industrial/market roofs east of Channelsea and west of the north–south railway. Exteriors are map/source evidence; every new roof/elevation profile is explicitly interpreted. Open wharf yards, railway sidings and unshaded plant/platform outlines remain context.',
        groups=groups, buildings=buildings, structures=[], additionalBuildings=additions, additionalSites=sites,
        evidenceImages=[f'reference/footprint-model-alignment/east-channelsea-upper-{s}.png' for s in
            ['raw', 'source', 'before', 'after', 'globe-raw', 'globe-source', 'globe-before', 'globe-after', 'station-raw', 'station-source', 'victoria-raw', 'victoria-source']],
        pendingContext=[dict(modelIds=['east-upper-victoria-corn-main','east-upper-caledonian-riverside','east-upper-globe-riverside'],
            feature='Existing Channelsea bank',
            evidence='The current generalized river edge intersects complete OS riverside roof outlines. Raw OS shows a clear bank/wharf boundary alongside these buildings. Retain full roof exteriors; coordinate a local river-bank correction before final rendering checks.')],
        deferred=[dict(sourceFids=[2832], reason='Long narrow western Stratford Market track-side/loading strip, distinct from the main shaded market roof79. The source polygon does not establish a complete continuous roof; retain for bounded loading/platform context pending separate canopy/roof classification.'),
            dict(sourceFids=[1539], reason='Northern Stratford Market Station feature is a solid shaded mapped covered body, distinct from the white platform/track-side space immediately east. Exact enclosure versus canopy, architectural function, roof arrangement and height remain unresolved. Defer its 3D interpretation with the station railway context; do not classify it as an unshaded open platform.'),
            dict(feature='Victoria Stone Works 20-cell grid', reason='Twenty unshaded cells are now registered in data/maps/victoria-stone-working-grid.json and drawn as ground-level boundaries. Apparatus identity, material and elevation remain deferred; no blanket roof is inferred.'),
            dict(feature='Open Great Eastern Goods & Coal Depot', reason='Sidings, buffers, fans and working lanes are clearly mapped but open. Railway context review is separate from these enclosed roof additions.'),
            dict(feature='Globe northern working strip', reason='Unshaded divided outline immediately north of the shaded crushing ranges. Preserve as low ancillary/context frames pending classification; no invented full-height northern roof.'),
            dict(feature='Stratford Wharf domestic frontage', reason='Short Road/Prospect Road rear yards and repeated dwelling outlines are distinct from the northern warehouse. Housing should be reviewed in its own pass.'),
            dict(sourceFids=[1103852], reason='Small circular outline at the southern Globe roof edge; the OS plan does not establish a roof or stack elevation. Keep as unresolved plant/stack context pending specific classification.'),
            dict(feature='New elevations', reason='No original Goad height/roof evidence established for these additions. Every height, storey count, brick material and pitched/bayed roof is a declared typological interpretation.')])
    (ROOT/'data/maps/east-channelsea-upper-footprint-alignment.json').write_text(json.dumps(result, indent=2)+'\n')
    print(f'Eastern upper strip: {len(additions)} newly reviewed roofs in {len(sites)} additional sites; no platforms, railway fans or working-yard grids extruded.')


if __name__ == '__main__':
    build()
