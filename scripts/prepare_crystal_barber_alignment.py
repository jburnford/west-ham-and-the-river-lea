"""Prepare reviewed Crystal Wharf / Barber OS matches and open-yard corrections.

Uses the private supplied-footprint extract and immutable pre-pass snapshot.
Routine builds require only the saved authoring register.
"""
import json
from pathlib import Path
from shapely import affinity, set_precision
from shapely.geometry import Polygon, Point, shape
from shapely.ops import unary_union
from prepare_ink_works_alignment import axis, rings
from factory_map_sources import mosaic

ROOT = Path(__file__).resolve().parents[1]
# Goad F3 compartments compared visually with the supplied OS polygons.
MATCHES = [
    (17, 'Barber bone shed, Goad 584', [58217]),
    (18, 'Barber southern sheds, Goad 586', [876117,861491,779418,1022359]),
    (19, 'Winstone southern ink factory, Goad 608', [7904]),
    (20, 'Barber southern courtyard range, Goad 590', [106314,886541]),
    (21, 'Barber detached riverside shed', [948364]),
    (22, 'Barber northern sheds, Goad 582', [522928,983780]),
    (23, 'Cooperage wood shed, Goad 544', [31541]),
    (28, 'Cooperage office and dwelling, Goad 542', [43792,917323,1005134,1098911]),
]
ADDITIONS = [
    ('talbot-538','Talbot works western range, Goad 538',[162727],3.8),
    ('dane-536','Dane main ink-factory range, Goad 536',[233717,58252],3.8),
    ('dane-534','Dane eastern room, Goad 534',[847367],3.8),
    ('dane-532','Dane engine/boiler compartment, Goad 532',[764441,823951],3.8),
    ('dane-530','Dane eastern boiler compartment, Goad 530',[818468],3.8),
    ('dane-528','Dane low eastern range, Goad 528',[802979],5.35),
    ('dane-526','Dane riverside range, Goad 526',[147902],3.8),
    ('dane-540','Dane front sheds, Goad 540',[726560,845958],3.8),
    ('barber-bone-annex','Barber bone-shed eastern annex',[502860],3.8),
    ('barber-592','Barber long riverside shed, Goad 592',[686523],3.8),
    ('barber-588','Barber stable/loft range, Goad 588',[834933,544999],3.8),
    ('ink-south-annex','Southern ink-factory attached rooms',[510096,890726],3.8),
    ('ink-610','Southern ink-factory shed, Goad 610',[895545,859284,991908,968388,757132],3.8),
]


def build():
    load=lambda p:json.loads((ROOT/p).read_text())
    before=load('reference/footprint-model-alignment/crystal-barber-before.json')
    models={b['id']:b for b in before['buildings']}
    wanted={fid for _,_,fids in MATCHES for fid in fids}|{fid for _,_,fids,_ in ADDITIONS for fid in fids}|{1230955}
    source={f['properties']['sourceFid']:affinity.affine_transform(shape(f['geometry']),[1,0,0,-1,-538900,183209])
            for f in load('reference/historic-building-footprints-2026-09-28/current-scene-buildings-bng.geojson')['features']
            if f['properties']['sourceFid'] in wanted}
    specs=[(f'site964-range-{n}',name,fids) for n,name,fids in MATCHES]
    additions=[]
    for suffix,name,fids,height in ADDITIONS:
        target=set_precision(unary_union([source[f] for f in fids]),.001)
        assert target.geom_type=='Polygon' and target.is_valid,suffix
        id='site964-'+suffix
        evidence='Separately drawn Goad/OS room; the supplied outline fixes its exterior, while roof shape and elevation remain interpreted.'
        row=dict(id=id,siteId=964,source='goad-f3-sugar',name=name,
            worldFootprint=rings(target)[0],worldHoles=rings(target)[1:],
            footprintEvidence=evidence,eavesHeight=height,
            heightEvidence=f'{height} m eaves is an estimate informed by the low Goad room; not a measured elevation.',
            roofEvidence=evidence,roofRise=1.6 if target.area<85 else 2.2,roofBays=1,roofAxis='x',material='brick')
        if suffix=='dane-528':
            row.update(floorMark='1½',heightEvidence='Goad 528 marks 1½ floors; interpreted 5.35 m eaves, not a measured elevation.')
        additions.append(row)
        models[id]={**row,'footprint':row['worldFootprint'],'height':height,'rotation':0.0 if suffix.startswith(('dane','talbot')) else -10.0}
        specs.append((id,name,fids))
    groups=[];corrections=[]
    for id,name,fids in specs:
        b=models[id];old=Polygon(b['footprint'],b.get('worldHoles',[]))
        target=set_precision(unary_union([source[f] for f in fids]),.001)
        assert target.geom_type=='Polygon' and target.is_valid,id
        angle=axis(target,b['rotation'])
        groupid='crystal-barber-'+id.removeprefix('site964-')
        groups.append(dict(id=groupid,modelIds=[id],sourceFids=fids,sourcePolygons=[rings(p) for f in fids for p in source[f].geoms],
            additional=id in {a['id'] for a in additions},
            previousUnionIoU=old.intersection(target).area/old.union(target).area))
        corrections.append(dict(modelId=id,siteId=964,name=name,groupId=groupid,
            sourceFids=fids,**({'sourceFid':fids[0]} if len(fids)==1 else {}),
            worldFootprint=rings(target)[0],worldHoles=rings(target)[1:],priorFootprint=rings(old)[0],
            priorRotationDegrees=b['rotation'],footprintRotationDegrees=angle,
            preservedHeight=b['height'],preservedRoofRise=b['roofRise'],preservedRoofAxis=b['roofAxis'],preservedRoofBays=b['roofBays'],
            review='Explicit OS/Goad F3 exterior match. Retain previous height/roof interpretation; keep mapped openings and the adjoining open yards.',
            comparison=dict(centroidShiftMetres=old.centroid.distance(target.centroid),areaRatio=target.area/old.area,axisChangeDegrees=angle-b['rotation'])))
    removed=[{**models[f'site964-range-{n}'],
              'review':'The original Goad rectangle covers labelled open Crystal Wharf/cooperage yard, not a roof. Remove this volume; separately reviewed additions follow the actual northern factory row.'}
             for n in [24,25,26,27]]
    # The southern source includes a small chimney base between the courtyard
    # and eastern shed. Do not absorb its opening into either building volume.
    original=next(s for s in before['structures'] if s['id']=='stack-964-1658-3500')
    base=source[1230955]
    structures=[dict(id=original['id'],sourceFid=1230955,sourcePolygons=[rings(p) for p in base.geoms],
        centre=list(base.centroid.coords)[0],rotation=axis(base,original['rotation']),priorCentre=[original['x'],original['z']],
        preservedHeight=original['height'],radius=.5,priorRadius=original['radius'],
        profileEvidence='Interpreted shaft radius narrows from 1.05 to 0.5 m so the plinth fits the small mapped base. Previous inferred 22 m height is retained; profile is not a measured elevation.',
        review='Goad southern boiler chimney matched to independent OS base 1230955 in the opening between the courtyard range and riverside shed; shaft height retained.')]
    original=next(s for s in before['structures'] if s['id']=='stack-964-1869-2754')
    # No separate OS base is supplied in the northern boiler row. Place the
    # Goad shaft near its southern dividing wall, retaining the printed 50 ft.
    parent=next(c for c in corrections if c['modelId']=='site964-dane-532')
    g=Polygon(parent['worldFootprint']);angle=parent['footprintRotationDegrees']
    local=affinity.rotate(g,-angle,origin=(0,0));x0,y0,x1,y1=local.bounds
    centre=affinity.rotate(Point(x0+.72*(x1-x0),y0+.80*(y1-y0)),angle,origin=(0,0))
    structures.append(dict(id=original['id'],centre=list(centre.coords)[0],rotation=angle,
        priorCentre=[original['x'],original['z']],preservedHeight=original['height'],
        transferGroup=parent['groupId'],
        review='Goad boiler chimney transferred within corrected compartment 532 near its southern dividing wall. No independent OS base supplied; retain printed 50 ft (15.24 m) height.'))
    seams=[]
    for i,a in enumerate(corrections):
        p=Polygon(a['worldFootprint'],a['worldHoles'])
        for b in corrections[:i]:
            overlap=p.intersection(Polygon(b['worldFootprint'],b['worldHoles'])).area
            if overlap>.005:
                assert overlap<1,(a['modelId'],b['modelId'],overlap)
                seams.append(dict(models=[a['modelId'],b['modelId']],sourceOverlapAreaM2=overlap,
                    review='Small overlap between supplied shared-wall outlines; keep source evidence and partition the rendered seam.'))
    yards=[]
    for id,name,bounds,pixels in [
        (96402,'Crystal Wharf and Talbot working yard',[-725,-137,-625,-72],
         [[77,198],[295,210],[306,227],[310,263],[89,259],[84,238]]),
        (96403,'Barber and southern ink-works yards',[-678,-33,-613,42],
         [[198,235],[313,211],[333,302],[344,362],[222,383],[207,296],[192,248]]),
    ]:
        _,to_world,_=mosaic(bounds)
        points=to_world(pixels).round(3).tolist()
        assert Polygon(points).is_valid
        yards.append(dict(id=id,parentSiteId=964,name=name,polygons=[[points]],
            mosaicBounds=bounds,mosaicPixels=pixels,allowStock=False,
            evidence='Working-ground envelope read from the inspected OS/Goad fences and wharf frontage. Exclude buildings, roads, chimneys and water during generation. Surface finish is interpreted; this is not a cadastral boundary or evidence of a single occupier. No stock/equipment added.'))
    result=dict(source='Author-supplied london_buildings_1891-96_corr_v1.gpkg',
        sourceCRS='EPSG:3857 reprojected through BNG; scene origin E538900,N183209',
        method='Reviewed Crystal Wharf, Barber and southern ink-works exterior matches; remove open-yard misinterpretations and retain separate map/elevation evidence.',
        mapReview=['Georeferenced OS five-foot 1893-96 mosaic','July 1893 Goad volume F sheet 3'],
        buildings=corrections,groups=groups,additionalBuildings=additions,removedBuildings=removed,structures=structures,boundaryOverlapReviews=seams,yards=yards,
        supersedesDeferred=[f'site964-range-{n}' for n in range(17,29)],
        deferred=[dict(feature='Small isolated features and plant bases, including 1217966, 1065632 and 1242744',
                       reason='Not independently identified as complete building volumes; retain supplied flat plans pending feature review.')])
    (ROOT/'data/maps/crystal-barber-footprint-alignment.json').write_text(json.dumps(result,indent=2)+'\n')
    print(f'Crystal/Barber: {len(corrections)} matched ranges in {len(groups)} groups; {len(additions)} additions, four open-yard rectangles removed, two corrected chimneys.')


if __name__=='__main__':
    build()
