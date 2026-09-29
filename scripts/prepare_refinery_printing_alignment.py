"""Match the refinery, printing works and machinery-depot ranges.

Requires the private source extract and immutable refinery-printing-before
snapshot. Saved authoring JSON is sufficient for routine builds.
"""
import json
from pathlib import Path
from shapely import affinity, set_precision
from shapely.geometry import Polygon, Point, LineString, shape
from shapely.ops import unary_union
from prepare_ink_works_alignment import axis, rings
from factory_map_sources import mosaic

ROOT = Path(__file__).resolve().parents[1]
SPECS = [
    ('printing-colour',[299098],['site567-range-1']),
    ('printing-engine',[435489,808632],['site567-range-2']),
    ('printing-varnish',[236310,835502,1030800,1052054],['site567-range-3']),
    ('varnish-boiling',[859743],['site567-range-4']),
    ('varnish-store',[693111],['site567-range-5']),
    ('depot-658',[486602],['site567-range-6']),
    ('depot-factory',[222267],['site567-range-7']),
    ('depot-654',[150510],['site567-range-8']),
    ('depot-666',[87744],['site567-range-9']),
    ('depot-smithy',[38428],['site567-range-10']),
    ('depot-stables',[23884],['site567-range-11']),
    ('printing-east',[299237,829931],['site567-range-12']),
]
NAMES = ['Colour-mixing range', 'Printing-ink engine and southern rooms',
         'Printing-ink varnish range', 'Varnish-boiling room', 'Varnish store',
         'Machinery depot room, Goad 658', 'Machinery depot factory',
         'Machinery depot low range, Goad 654', 'Machinery depot shed, Goad 666',
         'Machinery depot smithy, Goad 664/662', 'Machinery depot stables and boiler house',
         'Eastern printing-ink factory and northern room']
ADDITIONS = [
    ('652','Machinery depot room, Goad 652',[872149]),
    ('686','Oil stores, Goad 686',[822606,842580]),
    ('685','Oil stores, Goad 685',[753096]),
    ('684','Oil stores, Goad 684',[554547]),
    ('682','Tar-boiling room, Goad 682',[311225]),
]
TRACE_BOUNDS = [-670,20,-585,65]
TRACE_PIXELS = [[237,152],[345,106],[347,119],[309,135],[313,147],
                [303,151],[304,159],[290,164],[287,157],[241,175]]



def build():
    load = lambda p: json.loads((ROOT/p).read_text())
    before = load('reference/footprint-model-alignment/refinery-printing-before.json')
    models = {b['id']:b for b in before['buildings']}
    specs = [(name,fids,ids) for name,fids,ids in SPECS]
    names = {f'site567-range-{i}':name for i,name in enumerate(NAMES,1)}
    wanted = {f for _,fids,_ in SPECS for f in fids}|{f for _,_,fids in ADDITIONS for f in fids}|{1201365,1146475}
    source = {f['properties']['sourceFid']:affinity.affine_transform(shape(f['geometry']),[1,0,0,-1,-538900,183209])
              for f in load('reference/historic-building-footprints-2026-09-28/current-scene-buildings-bng.geojson')['features']
              if f['properties']['sourceFid'] in wanted}
    additions = []
    for suffix,name,fids in ADDITIONS:
        p = set_precision(unary_union([source[f] for f in fids]),.001)
        if p.geom_type=='MultiPolygon' and len(p.geoms)==1:p=p.geoms[0]
        assert p.geom_type=='Polygon' and p.is_valid
        id = f'site567-{suffix}'
        row = dict(id=id,siteId=567,source='goad-f17',name=name,
            worldFootprint=rings(p)[0],worldHoles=rings(p)[1:],floorMark='1',material='brick',roof='gable',
            footprintEvidence='Separate room shown on Goad F17 and matched to the supplied OS exterior.',
            heightEvidence='Goad one-floor room; 3.8 m eaves is interpreted, not a measured elevation.',
            roofEvidence='Roof form and rise interpreted; Goad 682 labels an iron roof.',
            eavesHeight=3.8,roofRise=1.2 if p.area<50 else 1.6,roofAxis='x',roofBays=1)
        if suffix=='682':
            row.pop('floorMark')
            row.update(storeysEstimate=1,heightEvidence='Low tar-boiling room with an iron roof on Goad; one floor and 3.8 m eaves are interpreted, not a measured elevation.')
        additions.append(row)
        models[id] = {**row,'height':row['eavesHeight'],'footprint':row['worldFootprint'],'rotation':-24.8174}
        names[id] = name
        specs.append((f'depot-{suffix}',fids,[id]))
    groups, corrections = [], []
    for name,fids,ids in specs:
        raw = unary_union([source[f] for f in fids])
        target = set_precision(raw,.001)
        if target.geom_type=='MultiPolygon' and len(target.geoms)==1:
            target = target.geoms[0]
        assert target.geom_type=='Polygon' and target.is_valid, (name,target.geom_type)
        old = [Polygon(models[id]['footprint']) for id in ids]
        angle = axis(target,models[ids[0]]['rotation'])
        parts = [target]
        assert all(p.geom_type=='Polygon' and p.is_valid and p.area>2 for p in parts)
        prior = unary_union(old)
        group = dict(id=name,modelIds=ids,sourceFids=fids,
                     sourcePolygons=[rings(p) for f in fids for p in getattr(source[f],'geoms',[source[f]])],
                     reconciledPolygons=[rings(target)],
                     previousUnionIoU=prior.intersection(raw).area/prior.union(raw).area,
                     additional=ids[0] in {b['id'] for b in additions})
        groups.append(group)
        for id,p,old in zip(ids,parts,old):
            b = models[id]
            corrections.append(dict(modelId=id,siteId=b['siteId'],name=names[id],groupId=name,sourceFids=fids,
                **({'sourceFid':fids[0]} if len(fids)==1 else {}),
                worldFootprint=rings(p)[0],worldHoles=rings(p)[1:],priorFootprint=rings(old)[0],
                priorRotationDegrees=b['rotation'],footprintRotationDegrees=angle,
                preservedHeight=b['height'],preservedRoofRise=b['roofRise'],preservedRoofAxis=b['roofAxis'],preservedRoofBays=b['roofBays'],
                review='Explicit OS/Goad F17 match. Prior heights and roofs retained; supplied recesses and separate rooms preserved.',
                comparison=dict(centroidShiftMetres=old.centroid.distance(p.centroid),areaRatio=p.area/old.area,axisChangeDegrees=angle-b['rotation'])))
    structures = []
    for id,fid,radius in [('stack-567-1092-649',1201365,.45),('stack-567-1123-748',1146475,.55)]:
        old = next(s for s in before['structures'] if s['id']==id)
        g = source[fid]
        structures.append(dict(id=id,sourceFid=fid,sourcePolygons=[rings(p) for p in getattr(g,'geoms',[g])],
            centre=list(g.centroid.coords)[0],rotation=axis(g,old['rotation']),priorCentre=[old['x'],old['z']],
            preservedHeight=old['height'],radius=radius,priorRadius=old['radius'],
            profileEvidence=f'Interpreted shaft radius reduced to {radius} m to fit the mapped base; previous inferred 22 m height retained.',
            review='Goad chimney symbol matched to the independent OS base beside the printing engine/depot room.'))
    b = models['site567-range-13']
    _,world,_ = mosaic(TRACE_BOUNDS)
    p = set_precision(Polygon(world(TRACE_PIXELS)),.001)
    trace = dict(modelId=b['id'],name='Northern storage shed, Goad 688',
        worldFootprint=rings(p)[0],worldHoles=[],priorFootprint=b['footprint'],
        mosaicBounds=TRACE_BOUNDS,mosaicPixels=TRACE_PIXELS,footprintSource='os-1893-direct-trace',
        footprintRotationDegrees=axis(p,b['rotation']),
        footprintEvidence='Exterior and southern projections traced directly from the cached OS five-foot map. The shed is absent from the supplied extract; Goad labels storage sheds 688.',
        eavesHeight=b['height'],roofRise=b['roofRise'],roofAxis=b['roofAxis'],roofBays=b['roofBays'])
    result = dict(source='Author-supplied london_buildings_1891-96_corr_v1.gpkg',
        sourceCRS='EPSG:3857 reprojected through BNG; scene origin E538900,N183209',
        method='Explicit refinery/printing/machinery-depot OS/Goad matches; one direct OS storage-shed trace; five omitted rooms restored; existing elevations retained.',
        mapReview=['Georeferenced OS five-foot 1893–96 mosaic','July 1893 Goad volume F sheet 17'],
        groups=groups,buildings=corrections,structures=structures,additionalBuildings=additions,mapTracedBuildings=[trace],
        deferred=[dict(sourceFids=[1004609,964482,775297,774492],reason='Small plant/projections and ramp structures need separate classification. No enclosed building volume asserted.'),
                  dict(feature='Northern open bay adjoining Goad 660',reason='Map linework differs from supplied extract; retain the separately matched enclosed rooms and defer the open bay.')])
    (ROOT/'data/maps/refinery-printing-footprint-alignment.json').write_text(json.dumps(result,indent=2)+'\n')
    roads = load('data/maps/district-road-traces.json')
    lane = next(r for r in roads['roads'] if r['name']=='Sugar House Lane')
    passage = next(r for r in roads['roads'] if r['name']=='Sugar House Lane works passage')
    for road in [lane,passage]:
        saved = road.get('refineryPrintingAlignment',{})
        road['refineryPrintingAlignment'] = dict(priorPoints=saved.get('priorPoints',road['points']),
            priorSourcePixels=saved.get('priorSourcePixels',road['sourcePixels']))
    prior = lane['refineryPrintingAlignment']['priorPoints']
    replacement = [[-719.909,61.771],[-718.799,70],[-713.570,83],[-706.232,98.507]]
    lane['points'] = prior[:10]+replacement+prior[12:]
    lane['refineryPrintingAlignment'].update(replacementSlice=[10,12],replacementPoints=replacement,
        review='Local centreline re-read within the OS lane beside the printing works. Two additional bend controls and small endpoint shifts clear the supplied façades on both sides; carriageway width remains 5.2 m.')
    lane['buildingClearanceReviews'] = [dict(modelIds=['site567-range-1','site567-range-2','site947-range-24','site947-range-25'],
        shoulderWidth=.55,evidence='Opposing supplied façades leave a minimum 6.712 m gap. Keep the 5.2 m carriageway and mapped walls; the earlier assumed 1.1 m pavements narrow here. The 0.55 m minimum clearance is interpreted, not surveyed pavement width.')]
    prior = passage['refineryPrintingAlignment']['priorPoints']
    line = LineString(lane['points'])
    start = line.interpolate(line.project(Point(prior[0])))
    passage['points'] = [[round(start.x,3),round(start.y,3)],*prior[1:-1],[prior[-1][0],round(prior[-1][1]-4.2,3)]]
    passage['refineryPrintingAlignment'].update(review='Reconnect the passage to the corrected lane and move its eastern endpoint 4.2 m north to follow the mapped gap above storage shed 688. Width and middle control retained.')
    for road in [lane,passage]:
        _,_,pixel = mosaic(road['sourceBounds'])
        road['sourcePixels'] = pixel(road['points']).round(3).tolist()
    (ROOT/'data/maps/district-road-traces.json').write_text(json.dumps(roads,indent=2)+'\n')
    print(f'{len(corrections)} source-linked ranges in {len(groups)} groups; one directly traced storage shed, five added rooms and two mapped chimney bases.')



if __name__=='__main__':build()
