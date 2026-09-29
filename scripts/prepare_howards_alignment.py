"""Prepare reviewed Howards OS groups while retaining Goad compartments and elevations.

Requires the private OS extract and saved pre-alignment review snapshot.
Routine builds use the committed register, including its full source evidence.
"""
SPECS=[
('north-wood-sawmill',['500','502'],[86755]),
('north-main-mill',['504','508'],[17759,79701]),
('north-west-mill',['506'],[352020]),
('north-east-mill',['514'],[493054]),
('north-mill-room',['518'],[617331]),
('north-mill-annex',['516'],[795093,951114]),
('north-workshop',['510','512'],[629449]),
('process-house',['520'],[762880]),
('furnace',['522'],[962329,1005196]),
('timber-process',['524'],[1136568]),
('sewer-range',['526'],[844044]),
('stove',['534'],[953401,1107792,1229738]),
('small-workshop',['530'],[849955]),
('small-timber',['528'],[972500,1122680]),
('central-workshops',['538w','538n','538s'],[5931]),
('central-annexes',['540w','540','540e'],[799478,840883,608349,711771]),
('eastern-timber',['542'],[108295,92599]),
('boiler',['544'],[40783]),
('river-workshop',['546'],[773324]),
('north-drying',['548n'],[92987]),
('warehouse',['548'],[25080,889763]),
('salts-compound',['550','552','554','boracic','564','566n'],[1734]),
('north-east-court',['558'],[643608]),
('river-store',['560'],[128078]),
('corner-shed',['562'],[94953]),
('epsom-stable',['566','stable'],[60345]),
('south-works',['568'],[246135,906595,987224,1003602]),
('vans',['570'],[297181]),
('coal-store',['572'],[122969]),
('ether-court',['574','578','580'],[820785,882988,794892]),
('court-cross-shed',['582'],[895058]),
('soda',['584'],[62453,828208]),
('soda-annex',['586'],[824224]),
('acid',['588','590'],[9302]),
('acid-south',['616'],[232398,825213,827802]),
('acid-east',['618'],[879051,959484,920022]),
('engine',['592'],[811001,728053,923419]),
('steam-workshops',['594','596','598'],[21708,548379,554266,980100,950780,1062036]),
('south-process',['600','602','604'],[762412,776332,803311,747629,390865,436514]),
('south-bay',['606'],[154373]),
('quinine',['636','638','640','642'],[3544,139232,936547]),
('creek-south',['646'],[823292]),
('creek-north',['648'],[791472]),
('mill-west',['652'],[272286]),
('mill-rooms',['660'],[860299,905451]),
('mercurial-store',['658'],[794027,928835]),
('mercurial-potash',['660b','662','666','662c','664','668','664b','670'],[1814,171555,188114,578399]),
('warehouse-south',['672'],[32488]),
('warehouse-west',['warehouse-west'],[800765,739238,218716,938383,955666]),
('warehouse-east',['674'],[218267,924367]),
('cocaine',['676'],[25418,946238,1009763]),
('cocaine-tail',['678'],[692840,766236]),
('office-north',['680'],[82965]),
('office-south',['682'],[17230]),
]

import json
import math
from pathlib import Path
from collections import defaultdict
import numpy as np
from shapely import affinity, set_precision
from shapely.geometry import Polygon, Point, box, shape
from shapely.ops import unary_union
from prepare_ink_works_alignment import axis, rings
from factory_map_sources import mosaic

ROOT=Path(__file__).resolve().parents[1]

def partition(originals, target, previous, angle):
    """Fit the existing Goad compartment grid inside an explicitly matched OS group.

    No source selection occurs here. Exterior bounds are surveyed; internal
    cuts use the proportions of the earlier Goad traces and remain interpreted.
    """
    old=[affinity.rotate(p,-previous,origin=(0,0)) for p in originals]
    oldbox=unary_union(old).bounds
    local=affinity.rotate(target,-angle,origin=(0,0))
    bounds=local.bounds
    normalized=[]
    for p in old:
        q=affinity.translate(p,-oldbox[0],-oldbox[1])
        normalized.append(affinity.scale(q,1/(oldbox[2]-oldbox[0]),1/(oldbox[3]-oldbox[1]),origin=(0,0)))
    xs=sorted({0,1,*[v for p in normalized for v in [p.bounds[0],p.bounds[2]]]})
    ys=sorted({0,1,*[v for p in normalized for v in [p.bounds[1],p.bounds[3]]]})
    cells=defaultdict(list)
    for x0,x1 in zip(xs,xs[1:]):
        for y0,y1 in zip(ys,ys[1:]):
            if (x1-x0)*(y1-y0)<1e-8:continue
            centre=Point((x0+x1)/2,(y0+y1)/2)
            owner=min(range(len(old)),key=lambda i:(normalized[i].distance(centre),normalized[i].centroid.distance(centre)))
            cell=box(bounds[0]+x0*(bounds[2]-bounds[0]),bounds[1]+y0*(bounds[3]-bounds[1]),bounds[0]+x1*(bounds[2]-bounds[0]),bounds[1]+y1*(bounds[3]-bounds[1]))
            cells[owner].append(local.intersection(cell))
    return [set_precision(affinity.rotate(unary_union(cells[i]),angle,origin=(0,0)),.001) for i in range(len(old))]

def build():
    load=lambda p:json.loads((ROOT/p).read_text())
    before=load('reference/footprint-model-alignment/howards-before.json')
    models={b['id']:b for b in before['buildings']}
    source={f['properties']['sourceFid']:affinity.affine_transform(shape(f['geometry']),[1,0,0,-1,-538900,183209]) for f in load('reference/historic-building-footprints-2026-09-28/current-scene-buildings-bng.geojson')['features']}
    groups=[];corrections=[];transfers={}
    for name,refs,fids in SPECS:
        if name=='timber-process':continue  # Tiny circle is not a defensible shed match.
        ids=['howards-'+r for r in refs]
        originals=[Polygon(models[id]['footprint']) for id in ids]
        previous=models[ids[0]]['rotation']
        target=set_precision(unary_union([source[f] for f in fids]),.001)
        assert target.geom_type=='Polygon' and target.is_valid,name
        angle=axis(target,previous)
        parts=partition(originals,target,previous,angle) if len(ids)>1 else [target]
        for id,p in zip(ids,parts):
            assert p.geom_type=='Polygon' and p.is_valid and p.area>2,(name,id,p.geom_type,p.area)
        assert unary_union(parts).symmetric_difference(target).area<.15,name
        groupid='howards-'+name
        groups.append({'id':groupid,'modelIds':ids,'sourceFids':fids,'sourcePolygons':[rings(p) for fid in fids for p in source[fid].geoms],
                       'division':'Earlier Goad compartment proportions fitted within the complete OS boundary; internal cuts interpreted.' if len(ids)>1 else None,
                       'previousUnionIoU':unary_union(originals).intersection(target).area/unary_union(originals).union(target).area})
        transfers[name]=(unary_union(originals),target,previous,angle)
        for id,old,p in zip(ids,originals,parts):
            b=models[id]
            corrections.append({'modelId':id,'siteId':260,'name':b['name'],'groupId':groupid,'sourceFids':fids,
                **({'sourceFid':fids[0]} if len(fids)==1 else {}),'worldFootprint':rings(p)[0],'worldHoles':rings(p)[1:],
                'priorFootprint':rings(old)[0],'priorRotationDegrees':previous,'footprintRotationDegrees':angle,
                'preservedHeight':b['height'],'preservedRoofRise':b['roofRise'],'preservedRoofAxis':b['roofAxis'],'preservedRoofBays':b['roofBays'],
                'review':'Explicit OS/Goad F3 comparison. Retain Goad use, floor marks, eaves height and roof interpretation. '+(groups[-1]['division'] or 'Retain the mapped exterior and holes.'),
                'comparison':{'centroidShiftMetres':old.centroid.distance(p.centroid),'areaRatio':p.area/old.area,'axisChangeDegrees':angle-previous}})
    # The old mill is omitted from the extract; trace its four walls on the OS.
    pixels=[[278,350],[325,339],[338,380],[291,391]]
    bounds=[-810,-295,-660,-165]
    _,world,_=mosaic(bounds)
    b=models['howards-644']
    traced=[{'modelId':b['id'],'worldFootprint':world(pixels).round(3).tolist(),
             'priorFootprint':b['footprint'],'mosaicBounds':bounds,'mosaicPixels':pixels,
             'footprintEvidence':'Four old-mill corners read directly from the georeferenced OS five-foot mosaic; absent from the supplied outline extract. Existing Goad and photograph-based elevation retained.',
             'footprintSource':'os-1893-direct-trace','eavesHeight':b['height'],'roofRise':b['roofRise'],'roofAxis':b['roofAxis'],'roofBays':b['roofBays']}]
    # Shed 524 lacks a defensible source match. Transfer its Goad relationship
    # to process house 520, rather than leaving it over the corrected workshop.
    b=models['howards-524'];old,target,previous,angle=transfers['process-house']
    shed=affinity.rotate(Polygon(b['footprint']),angle-previous,origin=old.centroid)
    shed=affinity.translate(shed,target.centroid.x-old.centroid.x,target.centroid.y-old.centroid.y)
    local_transfers=[{'modelId':b['id'],'worldFootprint':rings(set_precision(shed,.001))[0],
        'priorFootprint':b['footprint'],'transferGroup':'howards-process-house',
        'footprintSource':'goad-f3-local-transfer',
        'footprintEvidence':'Goad shed 524 retains its dimensions and relative position beside process house 520, translated and rotated with that reviewed OS match. No distinct supplied OS shed outline is asserted.',
        'eavesHeight':b['height'],'roofRise':b['roofRise'],'roofAxis':b['roofAxis'],'roofBays':b['roofBays']}]
    # Explicit Goad symbols belong to these locally fitted departments. Except
    # for the identifiable western mill base, positions are transferred evidence,
    # not claims of individually matched OS chimney outlines.
    stack_groups=['north-west-mill','furnace','sewer-range','stove','central-workshops','eastern-timber',
                  'salts-compound','salts-compound','salts-compound','north-east-court','north-east-court',
                  'acid','acid-south',*['mercurial-potash']*5]
    stacks=[]
    for original,group in zip(before['structures'],stack_groups):
        old,target,previous,angle=transfers[group]
        oldlocal=affinity.rotate(old,-previous,origin=(0,0)).bounds
        newlocal=affinity.rotate(target,-angle,origin=(0,0)).bounds
        point=affinity.rotate(Point(original['x'],original['z']),-previous,origin=(0,0))
        fractions=[(point.x-oldlocal[0])/(oldlocal[2]-oldlocal[0]),(point.y-oldlocal[1])/(oldlocal[3]-oldlocal[1])]
        newpoint=affinity.rotate(Point(newlocal[0]+fractions[0]*(newlocal[2]-newlocal[0]),newlocal[1]+fractions[1]*(newlocal[3]-newlocal[1])),angle,origin=(0,0))
        correction={'id':original['id'],'centre':list(newpoint.coords)[0],'rotation':angle,
            'priorCentre':[original['x'],original['z']],'preservedHeight':original['height'],
            'transferGroup':'howards-'+group,'groupFractions':fractions,
            'review':'Goad chimney symbol transferred with its explicitly reviewed local department; relative position interpreted, shaft height and profile retained.'}
        if original['id'] in {'stack-260-2132-1080','stack-260-2526-1750'}:
            fid={'stack-260-2132-1080':1092039,'stack-260-2526-1750':1223064}[original['id']];g=source[fid]
            correction.update(centre=list(g.centroid.coords)[0],sourceFid=fid,sourcePolygons=[rings(p) for p in g.geoms],
                review='Goad chimney position compared with its distinct OS base beside the western mill or acid works south range; retain existing shaft height and profile.')
        stacks.append(correction)
    seams=[]
    for i,a in enumerate(corrections):
        pa=Polygon(a['worldFootprint'],a['worldHoles'])
        for b in corrections[:i]:
            area=pa.intersection(Polygon(b['worldFootprint'],b['worldHoles'])).area
            if area>.02:
                assert area<.5,(a['modelId'],b['modelId'],area)
                seams.append({'models':[a['modelId'],b['modelId']],'sourceOverlapAreaM2':area,
                    'review':'Small shared-edge overlap in supplied adjacent outlines; retain source evidence and partition the rendered seam once.'})
    result={'source':'Author-supplied london_buildings_1891-96_corr_v1.gpkg',
        'sourceCRS':'EPSG:3857 reprojected through BNG; scene origin E538900,N183209',
        'method':'Explicit local OS/Goad matches across Howards; interpreted internal Goad compartments within surveyed outer boundaries.',
        'mapReview':['Georeferenced OS five-foot northern, middle and southern Howards mosaics','July 1893 Goad volume F sheet 3'],
        'groups':groups,'buildings':corrections,'structures':stacks, 'mapTracedBuildings':traced,'locallyTransferredBuildings':local_transfers,
        'deferred':[{'modelId':id,'reason':reason} for id,reason in [('howards-620','Detached riverside shed has no confident corresponding supplied outline; retain the Goad range pending a direct map trace.')]],
        'boundaryOverlapReviews':seams,'bankRegister':'data/maps/city-mills-bank-alignment.json'}
    (ROOT/'data/maps/howards-footprint-alignment.json').write_text(json.dumps(result,indent=2)+'\n')
    print(f'{len(corrections)} source-linked ranges in {len(groups)} groups; old mill directly traced; one shed locally transferred; one unresolved shed retained.')

if __name__=='__main__':build()
