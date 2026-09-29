"""Prepare Williams/French Asphalte matches from the private OS extract.

Routine builds use the saved register. Direct OS traces and the sheet-edge
completion remain distinct from the supplied source polygons.
"""
import json
from pathlib import Path
from shapely import affinity, set_precision
from shapely.geometry import Polygon, Point, box, shape
from shapely.ops import unary_union
from prepare_ink_works_alignment import axis, rings
from factory_map_sources import mosaic

ROOT = Path(__file__).resolve().parents[1]
BOUNDS = [-665,75,-575,140]
# Pixel coordinates in the unmodified cached five-foot OS mosaic. The source
# polygons end at the sheet seam; the eastern walls remain visible in the map.
COMPLETION = [[310.86,321.62],[311.09,317.79],[324,342],[340,370],[311.13,382.27]]
DIRECT = {
    6: [[311.46,280.15],[337.43,265.47],[352.45,299.1],[311.09,317.79]],
    9: [[311.09,317.79],[352.45,299.1],[367,323],[324,342]],
}
SPECS = [
    ('asphalte-dwelling',[1],[179094]),
    ('asphalte-stables',[2],[65438]),
    ('asphalte-west',[3,4,10,11],[5501,739969]),
    ('asphalte-engine',[5],[190393,499290]),
    ('asphalte-tank',[7],[161128]),
    ('asphalte-boilers',[8],[114965]),
    ('williams-694',[12],[225068]),
    ('williams-696',[13],[693774]),
    ('williams-698',[14],[64119]),
    ('williams-700',[15],[108655]),
    ('williams-702',[16],[445081,59238]),
    ('ultramarine-boundary-lean-to',[17],[656439]),
    ('williams-706',[18],[148247]),
    ('williams-704',['704'],[585845]),
]
NAMES = {
    1:'French Asphalte dwelling, Goad 668',2:'French Asphalte stables, Goad 670',
    3:'French Asphalte northern low bay, Goad 674',4:'French Asphalte concrete range, Goad 674',
    5:'French Asphalte engine room',6:'French Asphalte northern process room, Goad 680',
    7:'French Asphalte tank-over boiler bay',8:'French Asphalte eastern boilers, Goad 678',
    9:'French Asphalte storage, Goad 676',10:'French Asphalte furnace range, Goad 672',
    11:'French Asphalte southern iron-roof bay, Goad 672',12:'Williams wharf room, Goad 694',
    13:'Williams wharf office, Goad 696',14:'Williams wharf northern warehouse, Goad 698',
    15:'Williams wharf western room, Goad 700',16:'Williams wharf range, Goad 702',
    17:'British Ultramarine northern boundary lean-to',18:'Williams wharf riverside warehouse, Goad 706',
    '704':'Williams wharf eastern room, Goad 704',
}


def build():
    load = lambda p:json.loads((ROOT/p).read_text())
    before = load('reference/footprint-model-alignment/williams-asphalte-before.json')
    models = {b['id']:b for b in before['buildings']}
    wanted = {f for _,_,fids in SPECS for f in fids}|{1087863}
    source = {f['properties']['sourceFid']:affinity.affine_transform(shape(f['geometry']),[1,0,0,-1,-538900,183209])
              for f in load('reference/historic-building-footprints-2026-09-28/current-scene-buildings-bng.geojson')['features']
              if f['properties']['sourceFid'] in wanted}
    _,world,_ = mosaic(BOUNDS)
    id_for = lambda n:f'site568-range-{n}' if isinstance(n,int) else f'site568-{n}'
    added_target = set_precision(source[585845],.001)
    if added_target.geom_type=='MultiPolygon':added_target = added_target.geoms[0]
    addition = dict(id=id_for('704'),siteId=568,source='goad-f17',name=NAMES['704'],
        worldFootprint=rings(added_target)[0],worldHoles=[],floorMark='2',material='brick',roof='gable',
        footprintEvidence='Separate Goad 704 room adjoining 702, matched to OS outline 585845.',
        heightEvidence='Goad marks two floors; 6.9 m eaves is interpreted, not a measured elevation.',
        roofEvidence='Roof form and rise are interpreted.',eavesHeight=6.9,roofRise=1.6,roofAxis='z',roofBays=1)
    models[addition['id']] = {**addition,'footprint':addition['worldFootprint'],'height':6.9,'rotation':-24.8174}
    groups, corrections = [], []
    for name,numbers,fids in SPECS:
        ids = [id_for(n) for n in numbers]
        raw = unary_union([source[f] for f in fids])
        target = set_precision(raw,.001)
        completion = None
        if name=='asphalte-west':
            completion = set_precision(Polygon(world(COMPLETION)),.001)
            target = target.union(completion)
        if target.geom_type=='MultiPolygon' and len(target.geoms)==1:target = target.geoms[0]
        assert target.geom_type=='Polygon' and target.is_valid,(name,target.geom_type)
        old = [Polygon(models[id]['footprint']) for id in ids]
        previous = models[ids[0]]['rotation']
        angle = axis(target,previous)
        parts = [target]
        if len(ids)>1:
            # These four bays are successive north/south bands in Goad 674/672.
            # Keep that order across the complete OS body; nearest-cell fitting
            # of the old approximate rectangles would create a detached sliver.
            local = affinity.rotate(target,-angle,origin=(0,0))
            x0,y0,x1,y1 = local.bounds
            old_bounds = [affinity.rotate(p,-previous,origin=(0,0)).bounds for p in old]
            lo,hi = min(b[1] for b in old_bounds),max(b[3] for b in old_bounds)
            cuts = [y0]+[y0+((a[3]+b[1])/2-lo)/(hi-lo)*(y1-y0) for a,b in zip(old_bounds,old_bounds[1:])]+[y1]
            parts = [set_precision(affinity.rotate(local.intersection(box(x0-1,a,x1+1,b)),angle,origin=(0,0)),.001)
                     for a,b in zip(cuts,cuts[1:])]
            # The narrow sheet-edge tip east of the engine-room recess joins
            # the furnace bay below, rather than making a detached 674 volume.
            assert parts[1].geom_type=='MultiPolygon' and len(parts[1].geoms)==2
            main,tip = sorted(parts[1].geoms,key=lambda p:-p.area)
            assert tip.area<10
            parts[1],parts[2] = main,parts[2].union(tip)
        assert all(p.geom_type=='Polygon' and p.is_valid and p.area>2 for p in parts),name
        group = dict(id=name,modelIds=ids,sourceFids=fids,
            sourcePolygons=[rings(p) for f in fids for p in getattr(source[f],'geoms',[source[f]])],
            reconciledPolygons=[rings(target)],additional=numbers==['704'],
            previousUnionIoU=unary_union(old).intersection(raw).area/unary_union(old).union(raw).area)
        if completion is not None:
            group['division'] = 'Successive Goad north/south bands fitted to the OS body. The narrow detached sheet-edge tip joins the furnace bay below; internal boundaries remain interpreted.'
            group['mapCompletion'] = dict(worldPolygon=rings(completion)[0],mosaicBounds=BOUNDS,mosaicPixels=COMPLETION,
                addedAreaM2=target.difference(raw).area,
                evidence='Eastern side of Goad 672/674 omitted at the supplied extract sheet seam. Exterior read from OS; the seam connection and internal Goad compartment cuts are interpreted.')
        groups.append(group)
        for n,id,p,prior in zip(numbers,ids,parts,old):
            b = models[id]
            corrections.append(dict(modelId=id,siteId=566 if n==17 else 568,name=NAMES[n],groupId=name,sourceFids=fids,
                **({'sourceFid':fids[0]} if len(fids)==1 else {}),
                **({'priorSiteId':568,'siteAttributionEvidence':'Goad F17 draws this lean-to south of the Williams boundary, inside British Ultramarine.'} if n==17 else {}),
                worldFootprint=rings(p)[0],worldHoles=rings(p)[1:],priorFootprint=rings(prior)[0],
                priorRotationDegrees=b['rotation'],footprintRotationDegrees=angle,
                preservedHeight=b['height'],preservedRoofRise=b['roofRise'],preservedRoofAxis=b['roofAxis'],preservedRoofBays=b['roofBays'],
                review='Explicit OS/Goad F17 comparison; existing elevations retained. '+(group.get('mapCompletion',{}).get('evidence','Supplied mapped exterior.')),
                comparison=dict(centroidShiftMetres=prior.centroid.distance(p.centroid),areaRatio=p.area/prior.area,axisChangeDegrees=angle-b['rotation'])))
    traced = []
    for n,pixels in DIRECT.items():
        b = models[id_for(n)]
        p = set_precision(Polygon(world(pixels)),.001)
        raw_trace = p
        if n==6:
            # The map raster is coarser than the vector edges. Let the supplied
            # engine/tank outlines define both shared edges without overlap.
            p = p.difference(set_precision(unary_union([source[f] for f in [190393,499290,161128]]),.001))
        assert p.geom_type=='Polygon' and p.is_valid
        traced.append(dict(modelId=b['id'],name=NAMES[n],worldFootprint=rings(p)[0],worldHoles=[],
            priorFootprint=b['footprint'],mosaicBounds=BOUNDS,mosaicPixels=pixels,
            sharedEdgeSourceFids=[190393,499290,161128] if n==6 else [],sharedEdgeTrimAreaM2=raw_trace.difference(p).area,
            footprintSource='os-1893-direct-trace',footprintRotationDegrees=axis(p,b['rotation']),
            footprintEvidence='OS five-foot exterior directly traced where the supplied extract omits the eastern rooms. Shared sheet-seam edge reconciled with neighbouring supplied outlines; Goad compartment/use retained.',
            eavesHeight=b['height'],roofRise=b['roofRise'],roofAxis=b['roofAxis'],roofBays=b['roofBays']))
    structures = []
    for old in [s for s in before['structures'] if s['siteId']==568]:
        if old['id']=='stack-568-1713-980':
            base = source[1087863]
            c = dict(sourceFid=1087863,sourcePolygons=[rings(p) for p in getattr(base,'geoms',[base])],
                centre=list(base.centroid.coords)[0],rotation=axis(base,old['rotation']),radius=.65,priorRadius=old['radius'],
                profileEvidence='Interpreted shaft radius reduced to 0.65 m so its plinth fits the mapped base. Printed 60-foot height retained.',
                review='Goad 60-foot boiler chimney matched to the independent OS base 1087863.')
        else:
            parent = next(c for c in corrections if c['modelId']==id_for(4))
            prior = affinity.rotate(Polygon(models[id_for(4)]['footprint']),-models[id_for(4)]['rotation'],origin=(0,0)).bounds
            body = Polygon(parent['worldFootprint'])
            angle = parent['footprintRotationDegrees']
            bounds = affinity.rotate(body,-angle,origin=(0,0)).bounds
            point = affinity.rotate(Point(old['x'],old['z']),-models[id_for(4)]['rotation'],origin=(0,0))
            fractions = [(point.x-prior[0])/(prior[2]-prior[0]),(point.y-prior[1])/(prior[3]-prior[1])]
            point = affinity.rotate(Point(bounds[0]+fractions[0]*(bounds[2]-bounds[0]),bounds[1]+fractions[1]*(bounds[3]-bounds[1])),angle,origin=(0,0))
            assert body.contains(point)
            c = dict(centre=list(point.coords)[0],rotation=angle,transferGroup='asphalte-west',parentBuildingId=id_for(4),parentFractions=fractions,
                review='Goad chimney symbol transferred within the corrected 674 concrete range. No distinct supplied chimney base asserted; previous inferred 22 m height retained.')
        structures.append(dict(id=old['id'],priorCentre=[old['x'],old['z']],preservedHeight=old['height'],**c))
    result = dict(source='Author-supplied london_buildings_1891-96_corr_v1.gpkg',
        sourceCRS='EPSG:3857 reprojected through BNG; scene origin E538900,N183209',
        method='Explicit Williams/French Asphalte OS/Goad matches; separate direct traces for missing eastern rooms; OS sheet-edge completion recorded separately; existing elevations retained.',
        mapReview=['Georeferenced OS five-foot 1893–96 mosaic','July 1893 Goad volume F sheet 17'],
        groups=groups,buildings=corrections,additionalBuildings=[addition],mapTracedBuildings=traced,structures=structures,
        deferred=[dict(sourceFids=[1008000,905626,895423,915272,965896,1042207,1042217],reason='Small service projections require separate classification; no roof inferred in this pass.'),
                  dict(feature='Working-ground envelopes for Williams, Asphalte, Lascelles and Ultramarine',reason='Parcel/yard review remains separate from these building matches.')])
    (ROOT/'data/maps/williams-asphalte-footprint-alignment.json').write_text(json.dumps(result,indent=2)+'\n')
    roads = load('data/maps/district-road-traces.json')
    lane = next(r for r in roads['roads'] if r['name']=='Sugar House Lane')
    saved = lane.get('williamsAsphalteAlignment',{})
    prior = saved.get('priorPoints',lane['points'])
    pixels = saved.get('priorSourcePixels',lane['sourcePixels'])
    lane['points'] = [p[:] for p in prior]
    lane['sourcePixels'] = [p[:] for p in pixels]
    _,_,to_pixel = mosaic(lane['sourceBounds'])
    for index in [12,13]:
        lane['points'][index][0] = round(prior[index][0]-1.5,3)
        lane['sourcePixels'][index] = to_pixel([lane['points'][index]])[0].round(3).tolist()
    lane['williamsAsphalteAlignment'] = dict(priorPoints=prior,priorSourcePixels=pixels,changedIndices=[12,13],
        review='Two southern controls moved 1.5 m west within the mapped Sugar House Lane corridor; clears the supplied Asphalte dwelling and Williams 694/700 façades. Existing width and all other controls retained; centreline interpreted.')
    (ROOT/'data/maps/district-road-traces.json').write_text(json.dumps(roads,indent=2)+'\n')
    print(f'{len(corrections)} source-linked ranges, two direct OS traces, one added room, one corrected site attribution, two chimney positions.')
    print('Western body map completion:',round(groups[2]['mapCompletion']['addedAreaM2'],3),'m²')


if __name__=='__main__':build()
