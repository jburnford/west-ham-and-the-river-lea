"""Prepare reviewed High Street starch, tin-box and confectionery footprints.

Private OS extract and immutable abbey-west-before.json are needed only here.
Routine builds consume the saved register. Internal room divisions are estimates.
"""
import json
from pathlib import Path
from shapely import affinity, set_precision
from shapely.geometry import Polygon, LineString, box, shape
from shapely.ops import unary_union
from prepare_ink_works_alignment import axis, rings

ROOT=Path(__file__).resolve().parents[1]
# Explicit exterior correspondences reviewed on OS and July 1893 Goad F3/F17.
SPECS=[
 ('starch-main',[2797],['site256-range-1','site256-range-2','site256-range-3'],'starch'),
 ('pickle-frontage',[25658],['site256-range-5','site256-range-6'],'pickle'),
 ('tin-store-840',[827748],['site572-range-1'],None),
 ('tin-japanning',[22346,1039391,838929],['site572-range-2'],None),
 ('tin-factory',[26098,652278,927475],['site572-range-3'],None),
 ('hogarth-main',[1902],['site573-range-1'],None),
 ('hogarth-west',[33537,113174],['site573-range-2'],None),
 ('hogarth-stables',[630397,573866],['site573-range-3'],None),
 ('hogarth-east-north',[803805,819962,895955,759665,929602,378215,879848,446583,1098357,822447],['site573-range-4'],None),
 ('hogarth-engine',[35713],['site573-engine-624'],None),
 ('hogarth-corrugated-shed',[506627],['site573-corrugated-shed'],None),
 ('hogarth-east-south',[704311,518575,187931,854638,998507,1034297,610175],['site573-east-south'],None),
 ('hogarth-south-end',[16280],['site573-south-end-635'],None),
 ('bow-office-502',[493587],['site254-range-15'],None),
 ('bow-smithy-504',[492587,838996],['site254-range-14'],None),
]
NAMES={
 'site256-range-1':'Harvey and Neville starch factory, northern range',
 'site256-range-2':'Harvey and Neville starch stoves, Goad 668',
 'site256-range-3':'Harvey and Neville southern starch rooms, Goad 658–662',
 'site256-range-5':'Adjacent pickle/preserve factory, northern compartment',
 'site256-range-6':'Adjacent pickle/preserve factory, southern compartment',
 'site572-range-1':'Bryant and May eastern store, Goad 840',
 'site572-range-2':'Bryant and May japanning room and stoves, Goad 844',
 'site572-range-3':'Bryant and May tin-box factory and stair, Goad 842',
 'site573-range-1':'Hogarth confectionery main factory, Goad 620/622',
 'site573-range-2':'Hogarth western rooms, office and dwelling, Goad 626/628',
 'site573-range-3':'Hogarth riverside stables and stores, Goad 634',
 'site573-range-4':'Hogarth eastern confectionery rooms, northern section',
 'site573-engine-624':'Hogarth engine and boiler room, Goad 624',
 'site573-corrugated-shed':'Hogarth corrugated-iron courtyard shed',
 'site573-east-south':'Hogarth eastern confectionery rooms, southern section',
 'site573-south-end-635':'Hogarth southern end range, Goad 635',
 'site254-range-15':'Bow Bridge bone works office, Goad 502',
 'site254-range-14':'Bow Bridge bone works smithy, Goad 504',
}


def build():
 load=lambda p:json.loads((ROOT/p).read_text())
 before=load('reference/footprint-model-alignment/abbey-west-before.json')
 models={b['id']:b for b in before['buildings']}
 wanted={fid for _,fids,_,_ in SPECS for fid in fids}|{993523}
 source={f['properties']['sourceFid']:affinity.affine_transform(shape(f['geometry']),[1,0,0,-1,-538900,183209])
         for f in load('reference/historic-building-footprints-2026-09-28/current-scene-buildings-bng.geojson')['features']
         if f['properties']['sourceFid'] in wanted}
 additions=[]
 for _,fids,ids,_ in SPECS:
  for id in ids:
   if id in models:continue
   target=set_precision(unary_union([source[f] for f in fids]),.001)
   row=dict(id=id,siteId=573,source='goad-f3-sugar',name=NAMES[id],worldFootprint=rings(target)[0],worldHoles=rings(target)[1:],
       eavesHeight=3.8,roofRise=2.2,roofBays=1,roofAxis='x',material='brick',
       footprintEvidence='Separate Goad F3 room with reviewed supplied OS exterior.',
       heightEvidence='Low room: interpreted 3.8 m eaves, not a measured elevation.',
       roofEvidence='Single pitched roof interpreted from the room; the OS exterior does not establish an elevation.')
   additions.append(row);models[id]={**row,'height':3.8,'rotation':-45.,'footprint':row['worldFootprint']}
 groups=[];corrections=[]
 for name,fids,ids,division in SPECS:
  target=unary_union([source[f] for f in fids]);target=set_precision(target,.001)
  assert target.geom_type=='Polygon' and target.is_valid,name
  angle=axis(target,models[ids[0]]['rotation']);local=affinity.rotate(target,-angle,origin=(0,0));x0,y0,x1,y1=local.bounds
  parts=[target];evidence=None
  if division=='starch':
   stove=local.intersection(box(x0+.78*(x1-x0),y0-1,x1+1,y1+1))
   rest=local.difference(stove);north=rest.intersection(box(x0-1,y0-1,x1+1,y0+.66*(y1-y0)))
   parts=[affinity.rotate(g,angle,origin=(0,0)) for g in [north,stove,rest.difference(north)]]
   evidence=dict(axisDegrees=angle,stoveCrossFraction=.78,northernLengthFraction=.66,
       review='Goad northern factory, eastern stoves and southern rooms retained inside one OS exterior. These internal cuts are approximate compartment boundaries, not surveyed party walls.')
  if division=='pickle':
   north=local.intersection(box(x0-1,y0-1,x1+1,y0+.70*(y1-y0)))
   parts=[affinity.rotate(g,angle,origin=(0,0)) for g in [north,local.difference(north)]]
   evidence=dict(axisDegrees=angle,northernLengthFraction=.70,
       review='Two prior pickle/preserve compartments share one OS outline; division remains an interpreted Goad compartment boundary.')
  parts=[set_precision(p,.001) for p in parts]
  assert all(p.geom_type=='Polygon' and p.is_valid for p in parts),name
  old=unary_union([Polygon(models[id]['footprint'],models[id].get('worldHoles',[])) for id in ids])
  groupid='abbey-west-'+name
  groups.append(dict(id=groupid,modelIds=ids,sourceFids=fids,sourcePolygons=[rings(p) for f in fids for p in getattr(source[f],'geoms',[source[f]])],
      division=evidence,previousUnionIoU=old.intersection(target).area/old.union(target).area))
  for id,part in zip(ids,parts):
   b=models[id];old=Polygon(b['footprint'],b.get('worldHoles',[]))
   corrections.append(dict(modelId=id,siteId=b['siteId'],name=NAMES[id],groupId=groupid,sourceFids=fids,
       **({'sourceFid':fids[0]} if len(fids)==1 else {}),worldFootprint=rings(part)[0],worldHoles=rings(part)[1:],priorFootprint=rings(old)[0],
       priorRotationDegrees=b['rotation'],footprintRotationDegrees=angle,preservedHeight=b['height'],preservedRoofRise=b['roofRise'],
       preservedRoofAxis=b['roofAxis'],preservedRoofBays=b['roofBays'],
       review='OS exterior explicitly compared with Goad F3/F17. Retain earlier model height and roof interpretation; source outlines do not measure elevations. '+(evidence['review'] if evidence else ''),
       comparison=dict(centroidShiftMetres=old.centroid.distance(part.centroid),areaRatio=part.area/old.area,axisChangeDegrees=angle-b['rotation'])))
 # The old fourth starch rectangle is the Goad 89 domestic frontage, not the
 # starch factory. Do not enlarge the factory into these separately mapped houses.
 removed=[{**models['site256-range-4'],'review':'Earlier factory rectangle is drawn across the Goad High Street dwelling/shop frontage (89). Remove the misclassified industrial volume; retain the regional domestic outlines for future housing alignment.'}]
 # Correct the immediate chemical-works boundary using its now registered office.
 # The two process rooms lack supplied exteriors, so record a local Goad transfer
 # separately from the source-linked count instead of assigning unrelated polygons.
 old=Polygon(models['site254-range-15']['footprint']);new=source[493587]
 offset=[new.centroid.x-old.centroid.x,new.centroid.y-old.centroid.y]
 transfers=[]
 for id in ['site254-range-12','site254-range-13']:
  b=models[id];p=affinity.translate(Polygon(b['footprint']),*offset)
  transfers.append(dict(modelId=id,worldFootprint=rings(p)[0],priorFootprint=b['footprint'],localOffsetMetres=offset,
      eavesHeight=b['height'],roofRise=b['roofRise'],roofBays=b['roofBays'],roofAxis=b['roofAxis'],
      footprintEvidence='Provisional local Goad transfer with the corrected adjacent office 502, clearing the Hogarth boundary. No independent supplied exterior: process-plant detail still awaits the Bow Bridge works pass.'))
 stack=next(s for s in before['structures'] if s['id']=='stack-573-487-2965');base=source[993523]
 structures=[dict(id=stack['id'],sourceFid=993523,sourcePolygons=[rings(p) for p in getattr(base,'geoms',[base])],
      centre=list(base.centroid.coords)[0],rotation=axis(base,stack['rotation']),priorCentre=[stack['x'],stack['z']],preservedHeight=stack['height'],
      review='Goad 624 engine chimney matched to the independent OS base 993523 beside the corrected boiler room; previous inferred 22 m height and shaft radius retained.')]
 road=next(r for r in load('data/maps/district-road-traces.json')['roads'] if r['name']=='Stratford High Street')
 corridor=LineString(road['points']).buffer(road['width']/2+1.1,cap_style=2,join_style=2)
 road_review=dict(road=road['name'],groupId='abbey-west-starch-main',sourceOverlapAreaM2=source[2797].intersection(corridor).area,
    review='About half a square metre at the starch frontage meets the existing pavement edge. Retain both source evidence and street controls; the renderer clears this small corner.')
 result=dict(source='Author-supplied london_buildings_1891-96_corr_v1.gpkg',sourceCRS='EPSG:3857 reprojected through BNG; scene origin E538900,N183209',
   method='Reviewed starch, tin-box and confectionery exterior groups; retained Goad uses/compartments and interpreted elevations, with explicit neighbouring Bow Bridge boundary transfers.',
   mapReview=['Georeferenced OS five-foot 1893–96 mosaic','July 1893 Goad volume F sheets 3 and 17'],groups=groups,buildings=corrections,
   additionalBuildings=additions,removedBuildings=removed,locallyTransferredBuildings=transfers,structures=structures,roadBoundaryReview=road_review,
   deferred=[dict(feature='Bow Bridge process ranges 12/13',reason='Locally transferred from the registered office; no independent supplied source exteriors. Full chemical works/plant review remains pending.'),
             dict(feature='Small back-frontage stores and minor starch plant features',reason='Not individually resolved in this pass; retain flat source plans pending detailed feature classification.')])
 (ROOT/'data/maps/abbey-west-footprint-alignment.json').write_text(json.dumps(result,indent=2)+'\n')
 print(f'{len(corrections)} aligned ranges in {len(groups)} groups; {len(additions)} additions, one domestic reclassification, two provisional neighbour transfers.')


if __name__=='__main__':build()
