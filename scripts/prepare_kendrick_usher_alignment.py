"""Match both Kendrick works and Usher, retaining explicit OS sheet-seam completions.

Authoring requires the private footprint extract, cached OS map and immutable
kendrick-usher-before snapshot. Routine scene builds use the saved register.
"""
import json
from pathlib import Path
from shapely import affinity, set_precision
from shapely.geometry import Polygon, shape
from shapely.ops import unary_union
from prepare_ink_works_alignment import axis, rings
from factory_map_sources import mosaic

ROOT = Path(__file__).resolve().parents[1]
BOUNDS = [-775,95,-675,205]
SPECS = [
    ('kendrick-north-stables',569,'site569-range-2',[709193,707542],'Kendrick northern stables'),
    ('kendrick-north-factory',569,'site569-range-3',[20821],'Kendrick northern boiler works'),
    ('usher-north',570,'site570-range-1',[667726,664504],'Usher northern rooms, Goad 608/610'),
    ('usher-south',570,'site570-range-3',[763215],'Usher southern room, Goad 614'),
    ('usher-engine',570,'site570-range-4',[802249,892564,1182516],'Usher engine and boiler rooms, Goad 616'),
    ('kendrick-south-factory',571,'site571-range-1',[186608],'Kendrick southern boiler works, Goad 622'),
    ('usher-varnish',570,'site570-612',[767195],'Usher varnish-coppers room, Goad 612'),
    ('kendrick-south-east',571,'site571-620',[189399],'Kendrick eastern two-floor room, Goad 620'),
]
# Coordinates refer to the full cached mosaic, not cropped review images.
COMPLETIONS = {
    'kendrick-north-factory':[[328,55],[342,50],[350,69],[328,78]],
    'kendrick-south-factory':[[328,262],[378,242],[384,256.8],[328,280.5]],
}
DIRECT = [[340,135],[371,122],[384,151]]


def polygon(g):
    if g.geom_type=='MultiPolygon' and len(g.geoms)==1:g=g.geoms[0]
    assert g.geom_type=='Polygon' and g.is_valid
    return g


def build():
    load = lambda p:json.loads((ROOT/p).read_text())
    before = load('reference/footprint-model-alignment/kendrick-usher-before.json')
    models = {b['id']:b for b in before['buildings']}
    wanted = {f for _,_,_,fids,_ in SPECS for f in fids}|{1154445,16620}
    source = {f['properties']['sourceFid']:polygon(affinity.affine_transform(shape(f['geometry']),[1,0,0,-1,-538900,183209]))
              for f in load('reference/historic-building-footprints-2026-09-28/current-scene-buildings-bng.geojson')['features']
              if f['properties']['sourceFid'] in wanted}
    _,world,pixel = mosaic(BOUNDS)
    additions, groups, corrections = [], [], []
    for name,site,id,fids,title in SPECS:
        raw = unary_union([source[f] for f in fids])
        target = set_precision(raw,.001)
        completion = None
        if name in COMPLETIONS:
            pixels = COMPLETIONS[name]
            if name=='kendrick-south-factory':
                # Join the actual western corners of the independently supplied
                # eastern room; the intervening exterior is visible on the OS.
                end = source[189399]
                corners = list(end.exterior.coords)[:-1]
                upper = min(corners,key=lambda p:sum((a-b)**2 for a,b in zip(pixel([p])[0],[377.88,242.09])))
                lower = min(corners,key=lambda p:sum((a-b)**2 for a,b in zip(pixel([p])[0],[384.06,256.81])))
                pixels = [pixels[0],pixel([upper])[0].tolist(),pixel([lower])[0].tolist(),pixels[-1]]
            completion = set_precision(Polygon(world(pixels)),.001)
            target = target.union(completion)
            if name=='kendrick-south-factory':target=target.difference(set_precision(source[189399],.001))
        target = polygon(target)
        if name=='kendrick-north-factory':
            # Resolve the tiny independent-digitisation overlap in favour of
            # the already matched western works; keep both original outlines.
            target = polygon(target.difference(set_precision(source[16620],.001)))
        added = id not in models
        if added:
            two = site==571
            row = dict(id=id,siteId=site,source='goad-f17',name=title,
                worldFootprint=rings(target)[0],worldHoles=rings(target)[1:],material='brick',roof='gable',
                footprintEvidence='Separate Goad F17 room matched to the supplied OS exterior.',
                heightEvidence=('Goad two-floor room; 6.9 m eaves is interpreted.' if two else 'Low varnish-coppers room; one floor and 3.8 m eaves are interpreted.'),
                roofEvidence='Roof form and rise interpreted from the existing factory vocabulary.',
                eavesHeight=6.9 if two else 3.8,roofRise=1.5 if two else 1.2,roofAxis='x',roofBays=1)
            row.update({'floorMark':'2'} if two else {'storeysEstimate':1})
            additions.append(row)
            models[id]={**row,'height':row['eavesHeight'],'footprint':row['worldFootprint'],'rotation':-24.8174}
        b = models[id]
        old = Polygon(b['footprint'])
        angle = axis(target,b['rotation'])
        group = dict(id=name,modelIds=[id],sourceFids=fids,
            sourcePolygons=[rings(source[f]) for f in fids],reconciledPolygons=[rings(target)],additional=added,
            previousUnionIoU=old.intersection(raw).area/old.union(raw).area)
        if completion is not None:
            group['mapCompletion']=dict(worldPolygon=rings(completion)[0],mosaicBounds=BOUNDS,mosaicPixels=pixels,
                addedAreaM2=target.difference(raw).area,
                evidence='Supplied outlines stop at the OS sheet seam. Missing exterior traced from the cached OS map; seam joins remain interpreted.')
        if name=='kendrick-north-factory':
            group['adjacentSourceExclusion'] = dict(sourceFid=16620,modelId='site947-range-25',areaM2=raw.intersection(source[16620]).area)
        groups.append(group)
        corrections.append(dict(modelId=id,siteId=site,name=title,groupId=name,sourceFids=fids,
            **({'sourceFid':fids[0]} if len(fids)==1 else {}),
            worldFootprint=rings(target)[0],worldHoles=rings(target)[1:],priorFootprint=rings(old)[0],
            priorRotationDegrees=b['rotation'],footprintRotationDegrees=angle,
            preservedHeight=b['height'],preservedRoofRise=b['roofRise'],preservedRoofAxis=b['roofAxis'],preservedRoofBays=b['roofBays'],
            review='Explicit OS/Goad F17 match; existing elevations retained. '+group.get('mapCompletion',{}).get('evidence','Supplied exterior retained.'),
            comparison=dict(centroidShiftMetres=old.centroid.distance(target.centroid),areaRatio=target.area/old.area,axisChangeDegrees=angle-b['rotation'])))
    # Follow the vector engine-room seam exactly instead of making overlapping
    # rounded raster/vector edges. The independently mapped shaft is a hole.
    seam = source[892564]
    corners = list(seam.exterior.coords)[:-1]
    shared = []
    for approx in [[328.66,175.39],[329.23,174.42],[329.24,160.5],[328.87,159.57]]:
        shared.append(min(corners,key=lambda p:sum((a-b)**2 for a,b in zip(pixel([p])[0],approx))))
    pixels = DIRECT+[pixel([p])[0].tolist() for p in shared]+[[347,153]]
    trace_outer = set_precision(Polygon(world(pixels)),.001)
    engine = next(Polygon(c['worldFootprint'],c['worldHoles']) for c in corrections if c['modelId']=='site570-range-4')
    target = polygon(trace_outer.difference(engine).difference(set_precision(source[1154445],.001)))
    b = models['site570-range-2']
    trace = dict(modelId=b['id'],name='Usher main printing-ink factory, Goad 606',
        worldFootprint=rings(target)[0],worldHoles=rings(target)[1:],priorFootprint=b['footprint'],
        mosaicBounds=BOUNDS,mosaicPixels=pixels,footprintSource='os-1893-direct-trace',footprintRotationDegrees=axis(target,b['rotation']),
        footprintEvidence='L-shaped exterior traced from the cached OS map where supplied building geometry is absent beyond the sheet seam. Western internal division follows the retained engine-room source edge; independent chimney base 1154445 remains open.',
        eavesHeight=b['height'],roofRise=b['roofRise'],roofAxis=b['roofAxis'],roofBays=b['roofBays'])
    old = next(s for s in before['structures'] if s['id']=='stack-570-959-1000')
    g = source[1154445]
    stack = dict(id=old['id'],sourceFid=1154445,sourcePolygons=[rings(g)],centre=list(g.centroid.coords)[0],
        rotation=axis(g,old['rotation']),priorCentre=[old['x'],old['z']],preservedHeight=old['height'],radius=.5,priorRadius=old['radius'],
        profileEvidence='Interpreted half-metre shaft radius fits the independent mapped base; printed 40 ft height retained.',
        review='Goad Usher engine chimney matched to independent OS base 1154445.')
    result = dict(source='Author-supplied london_buildings_1891-96_corr_v1.gpkg',
        sourceCRS='EPSG:3857 reprojected through BNG; scene origin E538900,N183209',
        method='Explicit Kendrick north/south and Usher OS/Goad matches; two sheet-seam completions, one direct L-shaped trace and two restored rooms. Existing elevations retained.',
        mapReview=['Georeferenced OS five-foot 1893–96 mosaic','July 1893 Goad volume F sheet 17'],
        groups=groups,buildings=corrections,additionalBuildings=additions,mapTracedBuildings=[trace],structures=[stack],
        deferred=[dict(sourceFids=[1135652],reason='Small external projection beside Usher 614 needs classification; no enclosed building volume asserted.'),
                  dict(feature='Goad 622 construction status',reason='Labelled under construction July 1893; the OS shows the continuous southern footprint. Retain the existing interpreted completed low roof for the c.1900 scene.'),
                  dict(feature='Kendrick northern 1–2 floor annotation',reason='Retain the existing one-floor model; exact boundary of the taller bay is uncertain.')])
    (ROOT/'data/maps/kendrick-usher-footprint-alignment.json').write_text(json.dumps(result,indent=2)+'\n')
    roads = load('data/maps/district-road-traces.json')
    lane = next(r for r in roads['roads'] if r['name']=='Sugar House Lane')
    saved = lane.get('kendrickUsherAlignment',{})
    prior = saved.get('priorPoints',lane['points'])
    controls = world([[354,50],[362,69]]).round(3).tolist()
    lane['points'] = prior[:14]+controls+prior[14:]
    lane['kendrickUsherAlignment'] = dict(priorPoints=prior,priorSourcePixels=saved.get('priorSourcePixels',lane['sourcePixels']),
        insertionIndex=14,insertedPoints=controls,
        review='Two local OS lane-centre controls clear the completed Kendrick northern façade. Existing controls and 5.2 m carriageway retained.')
    _,_,road_pixel = mosaic(lane['sourceBounds'])
    lane['sourcePixels'] = road_pixel(lane['points']).round(3).tolist()
    (ROOT/'data/maps/district-road-traces.json').write_text(json.dumps(roads,indent=2)+'\n')
    print('Kendrick/Usher: eight source-linked ranges, two seam completions, one direct trace, two added rooms and one mapped 40 ft chimney.')


if __name__=='__main__':build()
