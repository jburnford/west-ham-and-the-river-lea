"""Author the northern Three Mills OS/Goad matches; private inputs needed only here."""
import json
import math
from pathlib import Path
from shapely import affinity, set_precision
from shapely.geometry import Polygon, Point, box, shape
from shapely.ops import unary_union
from prepare_ink_works_alignment import axis, rings
from factory_map_sources import mosaic
from factory_alignment_records import record_group

ROOT = Path(__file__).resolve().parents[1]
SPECS = [
    ('dwelling-802',[738916],[1]),('dwelling-803',[494587],[2]),
    ('dwelling-804',[428628],[3]),('dwelling-805',[511713],[4]),
    ('dwelling-806',[569447],[5]),('room-808',[138138],[7]),
    ('range-818',[30608,63457],[8]),('engine-boilers',[9057,125904],[9,10,11,12]),
    ('ranges-820-822',[7180,921093],[13,14]),('ranges-840-838',[1622],[16,17]),
    ('range-836',[17105],[18]),('ranges-832-834',[26002],[19]),
    ('range-830',[5218],[20]),('room-826',[886593],[29]),
    ('room-828',[118464],['828']),
]
NAMES = {1:'Three Mills dwelling, Goad 802',2:'Three Mills dwelling, Goad 803',
    3:'Three Mills dwelling, Goad 804',4:'Three Mills dwelling, Goad 805',5:'Three Mills dwelling, Goad 806',
    7:'Three Mills northern room, Goad 808',8:'Three Mills northern range, Goad 818',
    9:'Three Mills engine rooms, Goad 812',10:'Three Mills boiler room 814, eastern bay',
    11:'Three Mills boiler room 814, western bay',12:'Three Mills boiler room, Goad 816',
    13:'Three Mills process range, Goad 820',14:'Three Mills process range, Goad 822',
    16:'Three Mills three-floor range, Goad 840',17:'Three Mills three-floor range, Goad 838',
    18:'Three Mills process range, Goad 836',19:'Three Mills rooms, Goad 832/834',
    20:'Three Mills range, Goad 830',29:'Three Mills northern timber room, Goad 826',
    '828':'Three Mills eastern timber room, Goad 828'}
BOUNDS = [-580,325,-390,405]
DIRECT = [[467,219],[515,215],[518,255],[471,262]]

def ident(n):return f'site419-range-{n}' if isinstance(n,int) else f'site419-{n}'

def polygon(p):
    if p.geom_type=='MultiPolygon' and len(p.geoms)==1:p=p.geoms[0]
    assert p.geom_type=='Polygon' and p.is_valid
    return p


def build():
    load=lambda p:json.loads((ROOT/p).read_text())
    before=load('reference/footprint-model-alignment/three-mills-before.json')
    models={b['id']:b for b in before['buildings']}
    wanted={f for _,fs,_ in SPECS for f in fs}|{892638,144175,145527}
    source={f['properties']['sourceFid']:polygon(affinity.affine_transform(shape(f['geometry']),[1,0,0,-1,-538900,183209]))
        for f in load('reference/historic-building-footprints-2026-09-28/current-scene-buildings-bng.geojson')['features'] if f['properties']['sourceFid'] in wanted}
    p=set_precision(source[118464],.001)
    addition=dict(id=ident('828'),siteId=419,source='goad-f17',name=NAMES['828'],
        worldFootprint=rings(p)[0],worldHoles=[],floorMark='1',material='timber',roof='gable',
        footprintEvidence='Goad 828 timber room matched to independent supplied OS exterior 118464.',
        heightEvidence='Goad one-floor mark; 3.8 m eaves interpreted, not measured.',
        roofEvidence='Low gabled roof and rise interpreted.',eavesHeight=3.8,roofRise=1.4,roofAxis='x',roofBays=1)
    models[addition['id']]={**addition,'footprint':addition['worldFootprint'],'height':3.8,'rotation':-12.8174}
    groups, corrections=[],[]
    for name,fids,numbers in SPECS:
        ids=[ident(n) for n in numbers]
        raw=unary_union([source[f] for f in fids]);target=polygon(set_precision(raw,.001))
        angle=axis(target,models[ids[0]]['rotation'])
        parts=[target];division=None
        if len(ids)>1:
            local=affinity.rotate(target,-angle,origin=(0,0));x0,y0,x1,y1=local.bounds
            if name=='engine-boilers':
                east=x0+(x1-x0)*.62;mid=y0+(y1-y0)*.48;west=x0+(east-x0)*.5
                cells=[box(x0-1,y0-1,east,mid),box(west,mid,east,y1+1),box(x0-1,mid,west,y1+1),box(east,y0-1,x1+1,y1+1)]
                division='Goad 812 northern room, 814 southern room and 816 eastern room; retain two interpreted roof bays within 814. Internal cuts are schematic, not independently mapped walls.'
            else:
                fraction=94/(94+62) if name=='ranges-820-822' else 248/(248+118)
                cut=x0+(x1-x0)*fraction;cells=[box(x0-1,y0-1,cut,y1+1),box(cut,y0-1,x1+1,y1+1)]
                division='West/east Goad compartments proportioned within the single supplied exterior; internal cut remains interpreted.'
            parts=[polygon(set_precision(affinity.rotate(local.intersection(cell),angle,origin=(0,0)),.001)) for cell in cells]
        group, rows = record_group('three-mills-north-'+name, fids, source,
            models, ids, [NAMES[n] for n in numbers], target, parts, angle,
            division, additional=numbers==['828'])
        groups.append(group)
        corrections.extend(rows)
    _,world,_=mosaic(BOUNDS);p=set_precision(Polygon(world(DIRECT)),.001);b=models[ident(15)]
    trace=dict(modelId=b['id'],name='Three Mills three-floor range, Goad 824',
        worldFootprint=rings(p)[0],worldHoles=[],priorFootprint=b['footprint'],mosaicBounds=BOUNDS,mosaicPixels=DIRECT,
        footprintSource='os-1893-direct-trace',footprintRotationDegrees=axis(p,b['rotation']),
        footprintEvidence='Four exterior corners read directly from the cached OS map; Goad 824 identifies the three-floor room. The supplied extract omits this body.',
        eavesHeight=b['height'],roofRise=b['roofRise'],roofAxis=b['roofAxis'],roofBays=b['roofBays'])
    # The former 800 rectangle was miscentred on the footpath. Re-read its Goad
    # location, then register locally against the five mapped dwelling centres.
    raw=load('data/maps/factory-building-traces.json');a,bcoef,tx,tz=raw['sources']['goad-f17']['pixelToWorld']
    goad=lambda x,y:Point(a*x-bcoef*y+tx,bcoef*x+a*y+tz)
    dwells=[next(q for q in raw['buildings'] if q['id']==ident(n)) for n in range(1,6)]
    offsets=[(source[f].centroid.x-goad(*row['rectPixels'][:2]).x,source[f].centroid.y-goad(*row['rectPixels'][:2]).y) for row,f in zip(dwells,[738916,494587,428628,511713,569447])]
    dx=sum(q[0] for q in offsets)/5;dz=sum(q[1] for q in offsets)/5
    centre=affinity.translate(goad(1221,2459),dx,dz)
    b=models[ident(6)];old=Polygon(b['footprint']);p=set_precision(affinity.translate(old,centre.x-old.centroid.x,centre.y-old.centroid.y),.001)
    local=dict(modelId=b['id'],name='Three Mills timber outbuilding, Goad 800',worldFootprint=rings(p)[0],worldHoles=[],priorFootprint=b['footprint'],
        footprintSource='goad-f17-local-transfer',footprintRotationDegrees=b['rotation'],goadCentrePixels=[1221,2459],localTranslation=[dx,dz],
        registrationSourceFids=[738916,494587,428628,511713,569447],transferGroup='three-mills-north-dwellings',
        footprintEvidence='Miscentred Goad 800 rectangle moved from the footpath to its re-read yard position, locally registered with the five supplied dwelling centres. No distinct OS outline is established; presence and exact position remain provisional.',
        eavesHeight=b['height'],roofRise=b['roofRise'],roofAxis=b['roofAxis'],roofBays=b['roofBays'])
    old=next(s for s in before['structures'] if s['id']=='stack-419-1459-2756');g=source[892638]
    stack=dict(id=old['id'],sourceFid=892638,sourcePolygons=[rings(g)],centre=list(g.centroid.coords)[0],rotation=old['rotation'],
        priorCentre=[old['x'],old['z']],preservedHeight=old['height'],radius=1.5,priorRadius=old['radius'],
        profileEvidence=old['profileEvidence'],
        review='Round Goad engine chimney matched to independent OS base 892638; inferred 31 m height and 1.5 m radius retained.')
    tanks=[]
    for id,fid in [('distillery-tank-1830',144175),('distillery-tank-1884',145527)]:
        old=next(s for s in before['structures'] if s['id']==id);g=source[fid]
        tanks.append(dict(**old,sourceFootprintFid=fid,sourcePolygons=[rings(g)],priorStructure=old,
            positionEvidence='Independent supplied OS circular outline, confirmed as Goad tanks 869/870; original inferred 6 m height.',
            radiusEvidence='Circular body fits inside the slightly irregular supplied outline. Equal-area radii would overlap the neighbouring tank by 0.078 m; fitted radii retain two separate vessels.'))
        tanks[-1].update(x=round(g.centroid.x,3),z=round(g.centroid.y,3),
            radius=math.floor(g.centroid.distance(g.boundary)*1000)/1000,
            equalAreaRadius=round(math.sqrt(g.area/math.pi),3))
    result=dict(source='Author-supplied london_buildings_1891-96_corr_v1.gpkg',sourceCRS='EPSG:3857 reprojected through BNG; scene origin E538900,N183209',
        method='Explicit northern Three Mills OS/Goad matches, one direct OS trace, one provisional local Goad transfer, mapped chimney and two tank outlines; prior elevations retained.',
        mapReview=['Georeferenced OS five-foot 1893–96 mosaic','July 1893 Goad F17, sketch from outside observation; interior evidence limited'],
        groups=groups,buildings=corrections,additionalBuildings=[addition],mapTracedBuildings=[trace],locallyTransferredBuildings=[local],structures=[stack],tanks=tanks,
        deferred=[dict(feature='Southern distillery ranges 21–28 and House/Clock Mills with wharf ranges',reason='Separate continuation; millrace crossings and landmark details need coordinated review.'),
                  dict(feature='Goad 810 metal tank stage, tank 813, narrow ditch and small projections',reason='Plant/yard features need separate classification; no generic full-height volume assigned.'),
                  dict(feature='Goad 800 outbuilding',reason='Local Goad placement only; no OS match asserted and persistence into c.1900 remains uncertain.')])
    (ROOT/'data/maps/three-mills-north-footprint-alignment.json').write_text(json.dumps(result,indent=2)+'\n')
    roads=load('data/maps/district-road-traces.json')
    lane=next(q for q in roads['roads'] if q['name']=='Three Mills Lane')
    entrance=next(q for q in roads['roads'] if q['name']=='Three Mills entrance')
    for road in [lane,entrance]:
        saved=road.get('threeMillsNorthAlignment',{})
        road['threeMillsNorthAlignment']=dict(priorPoints=saved.get('priorPoints',road['points']),
            priorSourcePixels=saved.get('priorSourcePixels',road['sourcePixels']),priorWidth=saved.get('priorWidth',road['width']))
    lane['points']=lane['threeMillsNorthAlignment']['priorPoints'][:10]
    lane['threeMillsNorthAlignment']['review']='Retain the public approach, bridge span and 7 m width through the mill entrance. The former eastern extension becomes a separately traced narrower works passage.'
    passage=dict(name='Three Mills distillery passage',sheet='scene',
        points=[lane['points'][-1],[-541,390],[-526,386.7],[-500,380.9],[-489,377.4]],
        pixelWidth=lane['pixelWidth'],sourceBounds=lane['sourceBounds'],width=5.2,kind='lane',surface='setts',bridgeSpans=[],
        alignmentEvidence='OS passage between mapped northern engine/boiler walls and ranges 840/838; 5.2 m width interpreted within the minimum 7.629 m façade gap.',
        surfaceEvidence='Interpreted factory paving; no adoption or measured pavement evidence.')
    entrance['points']=[passage['points'][-1],[-463,372],[-449,369.9],[-425,363.6]]
    entrance['width']=5.2
    entrance['threeMillsNorthAlignment']['review']='Local OS yard passage re-read between the supplied ranges and directly traced 824. Match the adjoining 5.2 m estimated carriageway; minimum opposing façade gap here is 7.925 m.'
    for road in [lane,entrance,passage]:
        _,_,pixel=mosaic(road['sourceBounds']);road['sourcePixels']=pixel(road['points']).round(3).tolist()
    roads['roads']=[q for q in roads['roads'] if q['name']!=passage['name']]+[passage]
    (ROOT/'data/maps/district-road-traces.json').write_text(json.dumps(roads,indent=2)+'\n')
    print('Three Mills north: 20 source-linked ranges, one direct trace, one provisional local transfer, one added room, one mapped chimney and two tanks.')

if __name__=='__main__':build()
