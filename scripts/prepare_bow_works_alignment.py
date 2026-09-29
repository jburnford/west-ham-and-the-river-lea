"""Reviewed Bow Bridge matches and direct OS tracing of the omitted works body.

Requires the private source extract, OS tiles and immutable bow-works-before.json.
Saved authoring JSON is sufficient for routine builds.
"""
import json
import math
from pathlib import Path
from shapely import affinity, set_precision
from shapely.geometry import Polygon, Point, LineString, box, shape
from shapely.ops import unary_union, split
from prepare_ink_works_alignment import axis, rings
from prepare_howards_alignment import partition
from factory_map_sources import mosaic

ROOT=Path(__file__).resolve().parents[1]
BOUNDS=[-860,65,-735,225]
# Exterior read from the OS five-foot map. Supplied annex outlines take precedence
# at shared walls; the five internal divisions are read approximately from Goad.
BODY_PIXELS=[[232,251],[261,223],[288,245],[310,226],[334,252],[328,258],
 [339,269],[336,272],[356,291],[350,295],[409,400],[415,397],
 [419,417.6],[409.3,423.3],[420.3,445.8],[428,460],
 [447.1,497.9],[449.5,502.5],[451.3,506.3],[455.4,522.4],
 [459.5,541.7],[410.9,557.9],[384,498.7],[352.9,434.3],
 [350,411],[320,335],[310,329],[298,315]]
CUTS=[[[309,326],[370,294]],[[329,379],[405,343]],
      [[352,434],[420,418]],[[384,498.7],[450,478]]]
SPECS=[
 ('animal-charcoal-500',[7377],['site254-charcoal-500']),
 ('bone-mill-506',[9935],['site254-range-13']),
 ('mill-annex-508',[236456],['site254-mill-annex-508']),
 ('bones-shed-522',[42611],['site254-range-3']),
 ('stable-518',[624951],['site254-range-4']),
 ('crushing-524',[214735,1012516,1027327,900941],['site254-range-9','site254-range-8']),
 ('boiling-532-536',[9807],['site254-range-7','site254-range-10','site254-range-11']),
]
NAMES={1:'Bow Bridge bone store, Goad 514',2:'Bow Bridge tallow factory and bone boiling, Goad 516',
 3:'Bow Bridge western bones shed, Goad 522',4:'Bow Bridge stable and bone store, Goad 518',
 5:'Bow Bridge central stores, Goad 520',6:'Bow Bridge bone-manure factory, Goad 526/528',
 7:'Bow Bridge boiling houses and office, Goad 532/536',8:'Bow Bridge southern crushing rooms, Goad 524',
 9:'Bow Bridge northern crushing rooms, Goad 524',10:'Bow Bridge western lower boiling compartment',
 11:'Bow Bridge lower spinning compartment, Goad 534/540',12:'Bow Bridge sulphate-of-ammonia factory and retorts, Goad 510/512',
 13:'Bow Bridge bone mill, Goad 506'}


def build():
 load=lambda p:json.loads((ROOT/p).read_text())
 before=load('reference/footprint-model-alignment/bow-works-before.json');models={b['id']:b for b in before['buildings']}
 wanted={f for _,fids,_ in SPECS for f in fids}|{1011348,1044201,1089134,1172266}
 source={f['properties']['sourceFid']:affinity.affine_transform(shape(f['geometry']),[1,0,0,-1,-538900,183209])
  for f in load('reference/historic-building-footprints-2026-09-28/current-scene-buildings-bng.geojson')['features'] if f['properties']['sourceFid'] in wanted}
 additions=[]
 for id,fid,name,height in [('site254-charcoal-500',7377,'Bow Bridge animal-charcoal warehouse, Goad 500',6.9),
                           ('site254-mill-annex-508',236456,'Bow Bridge mill annex, Goad 508',3.8)]:
  g=set_precision(source[fid],.001);g=list(g.geoms)[0] if g.geom_type=='MultiPolygon' else g
  row=dict(id=id,siteId=254,source='goad-f17',name=name,worldFootprint=rings(g)[0],worldHoles=rings(g)[1:],eavesHeight=height,
   roofRise=2.2,roofAxis='x',roofBays=1,material='brick',footprintEvidence='Separate OS exterior identified with the Goad F17 room.',
   heightEvidence=f'Goad compartment/floor evidence informs interpreted {height} m eaves; not a measured elevation.',
   roofEvidence='Pitched roof interpretation; supplied exterior does not establish roof or elevation.')
  additions.append(row);models[id]={**row,'footprint':row['worldFootprint'],'height':height,'rotation':-24.8174}
 groups=[];corrections=[]
 for name,fids,ids in SPECS:
  target=set_precision(unary_union([source[f] for f in fids]),.001)
  if target.geom_type=='MultiPolygon' and len(target.geoms)==1:target=target.geoms[0]
  assert target.geom_type=='Polygon' and target.is_valid,name
  old=[Polygon(models[id]['footprint'],models[id].get('worldHoles',[])) for id in ids]
  angle=axis(target,models[ids[0]]['rotation'])
  parts=partition(old,target,models[ids[0]]['rotation'],angle) if len(ids)>1 else [target]
  assert all(p.geom_type=='Polygon' and p.is_valid for p in parts),name
  division='Existing Goad compartment proportions fitted within the shared exterior; internal cuts remain interpreted.' if len(ids)>1 else None
  groupid='bow-works-'+name;previous=unary_union(old)
  groups.append(dict(id=groupid,modelIds=ids,sourceFids=fids,sourcePolygons=[rings(p) for f in fids for p in getattr(source[f],'geoms',[source[f]])],
   division=division,previousUnionIoU=previous.intersection(target).area/previous.union(target).area))
  for id,p,prior in zip(ids,parts,old):
   b=models[id];number=int(id.rsplit('-',1)[1]) if '-range-' in id else None
   corrections.append(dict(modelId=id,siteId=254,name=NAMES[number] if number else b['name'],groupId=groupid,sourceFids=fids,
    **({'sourceFid':fids[0]} if len(fids)==1 else {}),worldFootprint=rings(p)[0],worldHoles=rings(p)[1:],priorFootprint=rings(prior)[0],
    priorRotationDegrees=b['rotation'],footprintRotationDegrees=angle,preservedHeight=b['height'],preservedRoofRise=b['roofRise'],
    preservedRoofAxis=b['roofAxis'],preservedRoofBays=b['roofBays'],
    review='OS supplied exterior reviewed against Goad F17; keep prior elevation and roof interpretation. '+(division or 'Individual mapped range.'),
    comparison=dict(centroidShiftMetres=prior.centroid.distance(p.centroid),areaRatio=p.area/prior.area,axisChangeDegrees=angle-b['rotation'])))
 _,world,pixel=mosaic(BOUNDS)
 body=Polygon(world(BODY_PIXELS))
 assert body.is_valid
 # Reconcile traced edges with adjacent supplied annexes/mill and chimney bases.
 exclusions=unary_union([source[f] for f in [9935,236456,42611,624951,214735,1012516,1027327,900941,9807,1011348,1044201,1089134]])
 traced=body.difference(exclusions)
 if traced.geom_type=='MultiPolygon':
  fragments=sorted(traced.geoms,key=lambda p:-p.area);assert sum(p.area for p in fragments[1:])<1
  traced=fragments[0]
 parts=[];remaining=traced
 for endpoints in CUTS:
  a,b=world(endpoints);dx,dy=b-a
  pieces=list(split(remaining,LineString([a-[dx*20,dy*20],b+[dx*20,dy*20]])).geoms)
  assert len(pieces)==2
  pieces.sort(key=lambda p:p.centroid.y);parts.append(pieces[0]);remaining=pieces[1]
 parts.append(remaining)
 direct=[]
 for n,p in zip([12,1,2,5,6],parts):
  b=models[f'site254-range-{n}'];p=set_precision(p,.001)
  assert p.geom_type=='Polygon' and p.is_valid and p.area>10
  direct.append(dict(modelId=b['id'],name=NAMES[n],worldFootprint=rings(p)[0],worldHoles=rings(p)[1:],priorFootprint=b['footprint'],
    footprintRotationDegrees=axis(p,b['rotation']),footprintSource='os-1893-direct-trace',
    footprintEvidence='Exterior read directly from OS five-foot mosaic because the continuous body is absent from the supplied extract. Internal Goad room divisions are approximate; independent supplied annexes and chimney openings are retained.',
    eavesHeight=b['height'],roofRise=b['roofRise'],roofAxis=b['roofAxis'],roofBays=b['roofBays']))
 structures=[]
 for id,fid,radius in [('stack-254-442-518',1011348,1.2),('stack-254-537-1118',1089134,.8),('stack-254-366-1182',1172266,.65)]:
  old=next(s for s in before['structures'] if s['id']==id);g=source[fid]
  structures.append(dict(id=id,sourceFid=fid,sourcePolygons=[rings(p) for p in getattr(g,'geoms',[g])],centre=list(g.centroid.coords)[0],
   rotation=axis(g,old['rotation']),priorCentre=[old['x'],old['z']],preservedHeight=old['height'],radius=radius,priorRadius=old['radius'],
   profileEvidence='Interpreted shaft radius reduced to fit the independently mapped plinth; retain printed height and shaft section.',
   review='Goad chimney symbol matched to independent supplied OS base. Printed height retained.'))
 old=next(s for s in before['structures'] if s['id']=='stack-254-499-1162');g=source[9807];angle=axis(g,old['rotation']);local=affinity.rotate(g,-angle,origin=(0,0));x0,z0,x1,z1=local.bounds
 centre=affinity.rotate(Point(x0+.69*(x1-x0),z0+.32*(z1-z0)),angle,origin=(0,0))
 structures.append(dict(id=old['id'],centre=list(centre.coords)[0],rotation=angle,priorCentre=[old['x'],old['z']],preservedHeight=old['height'],
   transferGroup='bow-works-boiling-532-536',review='Eastern boiling-house Goad chimney transferred within the corrected range. No independent OS base supplied; inferred 22 m height retained.'))
 # The western retort chimney is separately drawn and marked 50 feet on Goad.
 g=source[1044201];centre=list(g.centroid.coords)[0]
 added_stack=dict(id='stack-254-retorts-50ft',siteId=254,source='goad-f17',kind='chimney',name='Bow Bridge retort chimney',
  x=round(centre[0],3),z=round(centre[1],3),height=15.24,mappedHeightFeet=50,heightEvidence='50 feet printed at the retort chimney on July 1893 Goad F17; converted at 0.3048 m/ft.',
  radius=.85,section='square',material='brick',baseHeight=.34,rotation=axis(g,-24.8174),sourceFootprintFid=1044201,
  sourcePolygons=[rings(p) for p in getattr(g,'geoms',[g])],symbolKey='goad-symbol-key-1926',
  positionEvidence='Goad western retort chimney matched to independent supplied OS base 1044201.',
  profileEvidence='Interpreted square tapered shaft and crown; radius fitted inside the mapped plinth, not a measured elevation profile.')
 added_stack['pixelPosition']=[339,425]
 a,b,tx,tz=before['sources']['goad-f17']['pixelToWorld'];u,v=added_stack['pixelPosition']
 structures.append(dict(id=added_stack['id'],sourceFid=1044201,sourcePolygons=added_stack['sourcePolygons'],centre=centre,
  rotation=added_stack['rotation'],priorCentre=[a*u-b*v+tx,b*u+a*v+tz],preservedHeight=15.24,
  review=added_stack['positionEvidence']))
 # The next site's coarse north rectangle intrudes into the exact boiling range.
 # Keep its size/elevation, correcting the frontage provisionally until site564.
 b=models['site564-range-1'];p=affinity.translate(Polygon(b['footprint']),0,2)
 transfer=dict(modelId=b['id'],worldFootprint=rings(p)[0],priorFootprint=b['footprint'],localOffsetMetres=[0,2],
  eavesHeight=b['height'],roofRise=b['roofRise'],roofBays=b['roofBays'],roofAxis=b['roofAxis'],
  footprintEvidence='Local 2 m southward correction of the adjoining Goad room clears the mapped boiling-house exterior 9807 and improves its fit inside 1461. Full site564 compartment review remains pending; no independent source-linked match claimed.')
 result=dict(source='Author-supplied london_buildings_1891-96_corr_v1.gpkg',sourceCRS='EPSG:3857 reprojected through BNG; scene origin E538900,N183209',
  method='Explicit Bow Bridge OS/Goad matches plus separately recorded direct OS trace for the missing continuous works body; interpreted room divisions and elevations retained.',
  mapReview=['Georeferenced OS five-foot 1893–96 mosaic','July 1893 Goad volume F sheet 17'],groups=groups,buildings=corrections,
  additionalBuildings=additions,mapTracedBuildings=direct,structures=structures,additionalStructures=[added_stack],locallyTransferredBuildings=[transfer],
  supersedesLocalTransfers=['site254-range-12','site254-range-13'],
  directTrace=dict(mosaicBounds=BOUNDS,mosaicPixels=BODY_PIXELS,divisionPixels=CUTS,exclusionSourceFids=[9935,236456,42611,624951,214735,1012516,1027327,900941,9807,1011348,1044201,1089134],
   sourcePolygons=[rings(traced)],review='OS fixes the omitted exterior; supplied adjoining polygons take precedence at shared walls. Goad room cuts are estimates. Tiny disconnected tracing seams below 1 m² are discarded.'),
  deferred=[dict(feature='Open-under structure 530, water tower, tanks and small plant projections',reason='Source plans retained; no new full-height building assigned without separate plant/structure interpretation.'),
            dict(feature='Adjoining site564',reason='Northern range provisionally moved 2 m south to clear the boiling range; full site pass remains next.')])
 (ROOT/'data/maps/bow-works-footprint-alignment.json').write_text(json.dumps(result,indent=2)+'\n')
 # Reconcile this works frontage against the OS and supplied outlines. The
 # opposite bank and wider Old Lea connections are outside this local pass.
 baseline=next(r for r in load('reference/footprint-model-alignment/bow-works-ground-before.json')['rivers'] if r['id']==18)
 ring=baseline['polygons'][0][0];replacements=[]
 for i,dx in [(30,-1.8),(31,-1.8),(32,-1.8),(33,-2.0),(34,-5.3),(35,-5.3),(36,-4.1),(37,-4.1),(38,-4.1),(39,-3.2)]:
  prior=ring[i];point=[round(prior[0]+dx,3),prior[1]]
  replacements.append(dict(vertex=i,priorPoint=prior,point=point,mosaicPixel=pixel([point])[0].round(3).tolist()))
 bank=dict(riverId=18,polygonIndex=0,ringIndex=0,mosaicBounds=BOUNDS,replacements=replacements,
  source='OS five-foot map and reviewed supplied works frontages',registration='Local lateral reconciliation of simplified River Lea bank controls against the building frontage; not surveyed shore dimensions.',
  evidence='The previous bank crosses mapped warehouse, mill, bones shed and boiling-house walls. Shift ten works-side controls west while preserving the opposite bank and the wider river connections.')
 (ROOT/'data/maps/bow-works-bank-alignment.json').write_text(json.dumps(bank,indent=2)+'\n')
 print(f'Bow works: {len(corrections)} supplied-outline ranges, {len(direct)} directly traced ranges, two added rooms and five reviewed chimneys.')


if __name__=='__main__':build()
