"""Replace the northern eastern-strip sketch with individually reviewed OS roofs.

Authoring uses immutable source geometry and native OS pixels. Normal scene
builds consume the saved register without map tiles or ignored evidence files.
All new elevations and roof profiles are explicit modelling estimates.
"""
import json
import math
from pathlib import Path

from shapely import affinity, set_precision
from shapely.geometry import Polygon, shape
from shapely.ops import unary_union

from factory_alignment_records import record_group
from factory_map_sources import mosaic
from prepare_ink_works_alignment import axis, rings
from prepare_three_mills_north_alignment import polygon

ROOT = Path(__file__).resolve().parents[1]
NAME = 'east-channelsea-north'
BASELINE = 'reference/footprint-model-alignment/east-channelsea-before.json'
CACHE = 'reference/footprint-model-alignment/east-channelsea-source-shapes.json'
BOUNDS = [-120, -350, 240, 120]
SITE_NAMES = {560: 'Brush Works', 561: 'Hardware Manufactory',
    965: 'Langthorn Chemical Works', 562: 'Varnish and Japan Works',
    253: 'Abbey Bleaching and Chemical Works / Old Abbey Candle Works',
    9009: 'Abbey Road public house and eastern frontage roofs'}
# Explicit map/source matches; open courtyards and tiny uncertain plant are not
# selected merely because their source feature is near an industrial parcel.
SPECS = [
    ('brush-main', 560, [6805, 664984], 'Brush Works — main roof and northern annex', 5.5,
     'Complete shaded northern Brush Works body and separate attached northeastern annex. Native wall/blue-paint review reconciles only the northern main-roof edge against the moat; the annex and other walls remain unchanged.'),
    ('hardware-yard-room', 561, [801118], 'Hardware Manufactory — detached yard room', 3.2,
     'Separate small shaded square body in the eastern hardware court; the surrounding unshaded court is excluded.'),
    ('hardware-end-room', 561, [384628, 1097233, 1024082], 'Hardware Manufactory — southern room and attached steps', 4.0,
     'Shaded transverse southern room with its small attached edge projections, distinct from the directly traced main L-shaped roof. Exact stair/room function remains interpreted.'),
    ('langthorn-northwest', 965, [31499], 'Langthorn Chemical Works — northwest detached range', 3.8,
     'Separate shaded northwest body beside the east Channelsea bank, south of the moat-side access and north of the long riverside roof.'),
    ('langthorn-riverside', 965, [3926, 13676], 'Langthorn / Varnish works — northern riverside range', 6.0,
     'Two adjacent shaded riverside compartments form the complete long northern body. The map does not establish a precise Langthorn/Varnish tenancy division inside this joined exterior.'),
    ('langthorn-west-inner', 965, [8294, 112396, 497449], 'Langthorn Chemical Works — western inner range', 4.8,
     'Complete shaded western inner range and attached northern rooms. Keep the mapped narrow interior opening instead of filling it with a parcel-wide factory mass.'),
    ('langthorn-central', 965, [5181, 682778, 917020], 'Langthorn Chemical Works — central hall', 6.0,
     'Shaded central hall with its two small attached northern compartments; the broad labelled eastern court remains open.'),
    ('langthorn-north', 965, [7602, 46922], 'Langthorn Chemical Works — northern cross-range', 5.5,
     'Two touching shaded compartments beneath the western moat. Preserve their complete combined exterior and the open court immediately south.'),
    ('langthorn-covered', 965, [97658], 'Langthorn Chemical Works — crosshatched covered range', 3.5,
     'Distinct crosshatched narrow covered strip along the northern hall; roof material and precise canopy/process purpose remain unresolved.'),
    ('langthorn-northeast', 965, [184121, 555902, 1022167], 'Langthorn Chemical Works — northeastern rooms', 3.8,
     'Small touching northeastern roof components beside the access lane between the moat/Brush and Langthorn compounds; adjoining blue water is excluded.'),
    ('varnish-riverside-middle', 562, [12581], 'Varnish and Japan Works — middle riverside range', 4.8,
     'Separate shaded middle riverside compartment south of the Langthorn/Varnish northern body.'),
    ('varnish-riverside-south', 562, [34582], 'Varnish and Japan Works — southern riverside room', 3.8,
     'Separate shaded angled southern riverside room. The bank-side open tip and adjoining road/access remain clear.'),
    ('varnish-west-cross', 562, [34466, 411578], 'Varnish and Japan Works — western cross-range', 4.5,
     'Shaded western cross-range and attached small west end; open space between it and the riverside bodies is retained.'),
    ('varnish-southwest', 562, [20825], 'Varnish and Japan Works — southwest courtyard range', 5.0,
     'Separate shaded southwest range north of the Old Abbey Candle / Abbey Chemical complex; retain the reentrant around its small central court-facing symbol.'),
    ('varnish-middle', 562, [24249], 'Varnish and Japan Works — middle longitudinal range', 4.8,
     'Separate shaded longitudinal roof at the middle of the labelled Varnish and Japan Works; adjacent courts and tank/plant symbols remain open.'),
    ('varnish-small-north', 562, [111090], 'Varnish and Japan Works — small northern room', 3.5,
     'Separate small shaded northern room beside the middle court; no shaft height or process function inferred from neighbouring circles.'),
    ('varnish-northwest', 562, [10183], 'Varnish and Japan Works — northwest cross-range', 5.5,
     'Complete shaded northwestern cross-range south of the broad Langthorn access/court boundary.'),
    ('varnish-northeast', 562, [8233], 'Varnish and Japan Works — northeast cross-range', 5.5,
     'Complete separately shaded northeastern cross-range, retaining its irregular southern recesses and eastern roof edge.'),
    ('varnish-east-cross', 562, [34765, 408189], 'Varnish and Japan Works — eastern cross-range', 4.5,
     'Two touching eastern cross-range components retain their shared seam in source provenance and complete external boundary.'),
    ('varnish-lane-south', 562, [16729, 161188, 262064], 'Varnish and Japan Works — southern lane-side rooms', 5.0,
     'Connected shaded lane-side components form the complete southern exterior, with the small independent western/southern stair-foot symbols kept outside.'),
    ('varnish-lane-north', 562, [104719, 784571], 'Varnish and Japan Works — northern lane-side range', 4.0,
     'Shaded northern lane-side body and attached north room, separate from the eastern gate room and southern lane-side body.'),
    ('varnish-gate-room', 562, [89814, 835600], 'Varnish and Japan Works — eastern gate-side room', 3.8,
     'Shaded separate eastern gate-side room and small adjoining southern component. Exact gate/office use is an interpretation; the open street entrance remains excluded.'),
    ('abbey-riverside-north', 253, [5488], 'Old Abbey Candle / Abbey Chemical Works — northern riverside hall', 6.0,
     'Complete shaded northern riverside hall below the Varnish compound. OS labels the adjoining works Old Abbey Candle and Abbey Chemical; no bleaching-room identity is asserted.'),
    ('abbey-north-room', 253, [15942], 'Old Abbey Candle / Abbey Chemical Works — northern courtyard room', 5.0,
     'Separate shaded northern courtyard room below the Varnish compound; preserve the yard openings between it and the adjoining broad roofs.'),
    ('abbey-north-cross', 253, [18874, 353354], 'Old Abbey Candle Works — northern cross-range and east return', 5.5,
     'Shaded northern cross-range and attached eastern return beside the printed Old Abbey Candle Works court. The labelled unshaded court beneath the roof stays open.'),
    ('abbey-river-middle', 253, [133264, 52178], 'Abbey Chemical Works — middle riverside rooms', 4.5,
     'Two touching shaded middle riverside rooms alongside the Abbey Chemical court; retain their complete body without covering the large western courtyard.'),
    ('abbey-river-cross', 253, [57354], 'Abbey Chemical Works — riverside cross-range', 4.0,
     'Narrow shaded lateral riverside roof immediately south of the northern hall; unshaded land on its western side remains context.'),
    ('abbey-river-south', 253, [82298], 'Abbey Chemical Works — southern riverside range', 4.0,
     'Long shaded southern range beside the western court, north of the separate Abbey Lane domestic frontage; domestic source row is excluded.'),
    ('abbey-central-west', 253, [137038, 161762], 'Abbey Chemical Works — central western rooms', 4.8,
     'Two touching shaded central western rooms; nearby unshaded interior enclosures and tiny equipment are not converted into full-height roofs.'),
    ('abbey-central-east', 253, [109563, 34611], 'Abbey Chemical Works — central eastern roof', 5.5,
     'Complete shaded central eastern roof from two touching source components, including its mapped northern and southern reentrants.'),
    ('abbey-road-pub', 9009, [35039], 'Abbey Road — mapped public-house main roof', 6.4,
     'Shaded roadside roof explicitly marked P.H., east of Abbey Road opposite the Varnish/Old Abbey compounds. No public-house name or surveyed floor count is supplied.'),
    ('abbey-road-rear-small', 9009, [989245], 'Abbey Road public-house — small rear room', 2.8,
     'Tiny separate shaded rear room attached by an access gap to the P.H. parcel; low ancillary profile is estimated and exact domestic/service use unresolved.'),
    ('abbey-road-west-room', 9009, [823319], 'Abbey Road eastern frontage — western room', 3.5,
     'Separate shaded small western component in the roadside frontage group south of the P.H.; no existing housing footprint occupies it.'),
    ('abbey-road-middle-room', 9009, [673568], 'Abbey Road eastern frontage — middle room', 3.8,
     'Separate shaded middle component of the eastern frontage group, beside the western room and larger eastern roof.'),
    ('abbey-road-east-room', 9009, [167040], 'Abbey Road eastern frontage — eastern range', 4.5,
     'Shaded larger eastern body of the frontage group between Abbey Road and the railway-facing open ground; tenancy is not established.'),
    ('abbey-road-south-room', 9009, [217173], 'Abbey Road eastern frontage — detached southern room', 3.8,
     'Separate shaded southern room in the eastern roadside parcel; existing refined housing has no corresponding roof here.'),
]
HARDWARE_PIXELS = [[585.38, 390.15], [612.60, 381.16], [618.15, 397.44],
    [626.5, 415.2], [643.5, 407.2], [657.5, 454.5], [647.0, 460.5],
    [658.5, 481.0], [692.5, 461.0], [706.0, 483.0], [644.5, 519.0]]


def profile(target, ident, site, name, height, evidence):
    angle = axis(target, 0)
    local = affinity.rotate(target, -angle, origin=(0, 0))
    width, depth = local.bounds[2]-local.bounds[0], local.bounds[3]-local.bounds[1]
    roof_axis = 'x' if width >= depth else 'z'
    span = depth if roof_axis == 'x' else width
    bays = max(1, math.ceil(span/14))
    rise = min(3.2, max(.6, span/bays*.23))
    return dict(id=ident, siteId=site, source='os-1893', name=name,
        worldFootprint=rings(target)[0], worldHoles=rings(target)[1:],
        footprintRotationDegrees=angle, eavesHeight=height, roofRise=rise,
        roofAxis=roof_axis, roofBays=bays, material='brick', roof='gable',
        storeysEstimate=2 if site == 9009 and height > 6 else 1,
        footprintEvidence=evidence+' Exterior reviewed against the raw cached OS five-foot map; industrial parcel polygons are never extruded.',
        heightEvidence=f'New estimated {height:g} m eaves; no measured height or fire-insurance storey annotation is available. The OS map supplies plan geometry only.',
        roofEvidence='Simple pitched industrial roofs and repeated bays are new modelling interpretations; exact ridge height, pitch, material and internal roof arrangement are not established by the OS plan.')


def build():
    load = lambda p: json.loads((ROOT/p).read_text())
    cached = load(CACHE)
    wanted = {fid for _, _, fs, *_ in SPECS for fid in fs}
    source = {fid: polygon(shape(cached[str(fid)])) for fid in wanted}
    moats = load('data/maps/east-channelsea-context-alignment.json')['additionalRivers']
    moat = unary_union([Polygon(p[0], p[1:]) for q in moats for p in q['polygons']])
    groups, rows, additions = [], [], []
    for key, site, fids, name, height, evidence in SPECS:
        raw = unary_union([source[fid] for fid in fids])
        target = polygon(set_precision(raw, .001))
        reconciliation = None
        if key == 'brush-main':
            # The independently read blue-fill boundary reveals a tiny source
            # north-wall error. Change only this edge, not the moat or all banks.
            mask = moat.buffer(.121)
            target = polygon(set_precision(raw.difference(mask), .001))
            reconciliation = dict(contextRegister='data/maps/east-channelsea-context-alignment.json',
                riverIds=[q['id'] for q in moats], waterPolygons=[p for q in moats for p in q['polygons']],
                sourceRemovedAreaM2=raw.intersection(mask).area,
                clearanceMetres=.121, maximumRemovedAreaM2=5,
                maximumBoundaryShiftMetres=.8,
                evidence='Native OS roof hatch and blue-paint boundary inspected together. The supplied Brush north edge enters the precisely traced moat by about 1.77 m². Re-read only the northern wall on the dry side of the mapped blue edge, retaining 0.121 m clearance within raster line-width uncertainty; every other wall and northeastern annex remains supplied source geometry.')
        ident = 'east-north-'+key
        addition = profile(target, ident, site, name, height, evidence)
        template = dict(addition, footprint=addition['worldFootprint'], rotation=addition['footprintRotationDegrees'], height=height)
        group, corrections = record_group(ident, fids, source, {ident: template},
            [ident], [name], target, [target], addition['footprintRotationDegrees'], evidence,
            additional=True, review_prefix='Explicit raw OS roof shading/source outline comparison; new estimated roof and height profile, no Goad evidence asserted. ')
        group['previousUnionIoU'] = 0
        if reconciliation:
            group['mappedWaterReconciliation'] = reconciliation
        for correction in corrections:
            correction.update(priorFootprint=[], additionalModel=True,
                profileEvidence=addition['heightEvidence']+' '+addition['roofEvidence'])
        groups.append(group); rows.extend(corrections); additions.append(addition)
    _, to_world, _ = mosaic(BOUNDS)
    raw_hardware = Polygon(to_world(HARDWARE_PIXELS))
    neighbours = unary_union([source[f] for f in [6805, 664984, 384628, 1097233, 1024082]])
    hardware = polygon(set_precision(raw_hardware.difference(neighbours), .001))
    direct = profile(hardware, 'east-north-hardware-main-direct', 561,
        'Hardware Manufactory — directly traced main L-shaped roof', 5.5,
        'Large shaded L-shaped hardware roof omitted from the supplied building extract. Trace its exterior from native OS pixels, registering its northern shared wall to the Brush source and excluding the separately source-mapped southern transverse room/steps. The eastern court remains open.')
    direct['footprintSource'] = 'os-1893-direct-trace'
    additions.append(direct)
    result = dict(source='Author-supplied london_buildings_1891-96_corr_v1.gpkg; native cached OS London five-foot mosaic',
        sourceCRS='EPSG:3857 reprojected through BNG; scene origin E538900,N183209', baseline=BASELINE,
        method='Replace northern Channelsea–railway sketch blocks with independently reviewed shaded roof exteriors at Brush, Hardware, Langthorn, Varnish/Japan and Abbey works, plus the missing Abbey Road frontage roofs. Every new height and roof form is estimated; no original fire-insurance coverage is asserted. Open courts, moat, railway ground and domestic frontage stay distinct.',
        additionalSites=[dict(id=site, name=name, sources=['os-1893'], coverage='Individual OS-mapped ranges',
            notes='Roof exteriors are mapped; new heights, roof forms, materials and process-room identities are estimates. Site 253 retains the supplied Bleaching/chemical grouping although OS separately labels Abbey Chemical and Old Abbey Candle Works. Context ID9009 is a model grouping, not an original cadastral parcel ID.') for site, name in SITE_NAMES.items()],
        additionalBuildings=additions, groups=groups, buildings=rows, structures=[],
        mapTracedBuildings=[dict(direct, modelId=direct['id'])],
        directMapTraces=[dict(modelId=direct['id'], mosaicBounds=BOUNDS, nativePixels=HARDWARE_PIXELS,
            excludedSourceFids=[6805, 664984, 384628, 1097233, 1024082],
            rawWorldFootprint=rings(raw_hardware)[0], sourceBoundaryReconciliationAreaM2=raw_hardware.intersection(neighbours).area,
            evidence='Native pixel grid and raw hatching inspected; this large L-shaped roof has no supplied source exterior. Neighbour source walls control the shared boundaries. No open courtyard polygon or nearest source is substituted.')],
        evidenceImages=[f'reference/footprint-model-alignment/east-channelsea-north-{s}.png' for s in ['raw', 'source', 'models', 'after']]
            +[f'reference/footprint-model-alignment/east-channelsea-north-{site}-{s}.png' for site in ['brush-hardware', 'langthorn', 'varnish', 'bleach'] for s in ['raw', 'source', 'after']]
            +['reference/footprint-model-alignment/east-channelsea-north-hardware-grid.png', 'reference/footprint-model-alignment/east-channelsea-north-brush-water.png'],
        openCourtReviews=[dict(worldPoint=[5, -222], evidence='Unshaded Langthorn eastern court inside the labelled works, below the northern roof and east of the central hall.'),
            dict(worldPoint=[76, -247], evidence='Unshaded eastern Hardware court beside the main L-shaped body; the small independently mapped yard room is separate.'),
            dict(worldPoint=[31, -106], evidence='Unshaded Abbey Chemical works southern court, between the central shaded body and the Abbey Lane domestic row.')],
        excludedContext=[dict(sourceFids=[763616, 755784, 758385, 788681, 748547, 775554, 768865, 758786, 558092, 674517, 258434],
            reason='Separate Abbey Lane domestic frontage and returns; existing refined housing is not duplicated as factory roofs.'),
            dict(sourceFids=[11904], reason='Separate unshaded outlined former St Mary’s Abbey site beside the eastern lane; not a manufacturing roof.')],
        deferred=[dict(sourceFids=[950740, 1034495, 1010855, 1107451, 1030235, 975118, 1051015, 700003, 863588, 841028, 883606, 892241, 955971, 875039, 457114, 933151, 886014, 905774, 831918, 877726, 957798, 664000, 284852, 777060, 779356, 915686],
            reason='Tiny stairs, chimney/equipment bases, interior enclosures and unattached ancillary symbols require classification; no full-height building or tall chimney is inferred merely from a small source polygon.'),
            dict(feature='Building storeys and roofs', reason='Original fire-insurance coverage has not been established. New low eaves and gable bays are declared estimates, not transcribed floor counts.'),
            dict(feature='Langthorn/Varnish and Abbey tenancy divisions', reason='Supplied industrial parcels and printed OS works names differ locally. Roof geometry is independently mapped; exact historic tenant and process boundaries remain unresolved.')])
    (ROOT/f'data/maps/{NAME}-footprint-alignment.json').write_text(json.dumps(result, indent=2)+'\n')
    print(f'{NAME}: {len(rows)} source-linked roofs plus one directly traced Hardware roof; six sites, estimated profiles and open courts.')


if __name__ == '__main__':
    build()
