"""Prepare explicitly reviewed Oil Wharf ranges, tank positions and yard evidence.

OS source polygons fix building plans; July 1893 Goad F2 distinguishes stores,
open ground and tanks. This is not automatic nearest-feature matching.
"""
import json
import math
from pathlib import Path
from pyproj import Transformer
from shapely import affinity, set_precision
from shapely.geometry import shape, Polygon, Point
from shapely.ops import unary_union
from prepare_ink_works_alignment import axis, rings
from build_factory_buildings import footprint

ROOT = Path(__file__).resolve().parents[1]

def build():
    load=lambda p:json.loads((ROOT/p).read_text())
    raw=load('data/maps/factory-building-traces.json')
    rows={b['id']:b for b in raw['buildings']}
    models={b['id']:b for b in load('docs/data/factory-buildings.json')['buildings']}
    project=Transformer.from_crs(3857,27700,always_xy=True)
    span=2*math.pi*6378137;scale=256*2**18
    def world(pixel):
        u,v=pixel
        e,n=project.transform(((131060*256+u)/scale-.5)*span,(.5-(87140*256+v)/scale)*span)
        return [round(e-538900,3),round(183209-n,3)]
    source={f['properties']['sourceFid']:affinity.affine_transform(shape(f['geometry']),[1,0,0,-1,-538900,183209])
            for f in load('reference/historic-building-footprints-2026-09-28/current-scene-buildings-bng.geojson')['features']}
    # Existing IDs are retained when the earlier range represented the same
    # mapped feature. Additional ranges have explicit source IDs, not parcel fills.
    specs=[
        ('oilwharf-1',[5843],'Petroleum store F','Petroleum in barrels on Goad F2; roof form and eaves height remain interpreted.'),
        ('oilwharf-3',[85938],'Roadside store N','Store N beside the filling shed on Goad F2.'),
        ('oilwharf-4',[857458,788844,234020,709244],'Detached petroleum store C','Detached C range on Goad F2; one existing range covers adjacent OS compartments.'),
        ('oilwharf-5',[705774,750552,742081,693202,680145,730406,683899],'Cook’s Road dwellings beside the wharf','Dwelling row on Goad F2; contextual housing, not an oil-production range. Existing elevation retained pending housing review.'),
        ('oilwharf-7',[13285,15121,205514],'Northern petroleum stores B and annexe A','Petroleum in barrels in B1/B2 with annexe A on Goad F2; outer boundary retained as one existing range.'),
        ('oilwharf-store-e',[14095],'Petroleum store E','Petroleum in barrels, E on Goad F2; inferred one-storey envelope.'),
        ('oilwharf-store-annex',[35525,583733],'Eastern store annexes','Attached B/G ranges adjoining petroleum store F on Goad F2; elevations interpreted.'),
        ('oilwharf-office',[692188,776579,904389,923683,1297524,1132988,1173979],'Office beside filling shed','Office 538 on Goad F2, with narrow attached OS compartments; elevation interpreted.'),
        ('oilwharf-pump',[185430],'Detached iron-roof range','Small detached range 544 on Goad F2, annotated iron roof; specific use unresolved.'),
    ]
    groups=[];corrections=[];additions=[]
    for id,fids,name,evidence in specs:
        poly=unary_union([source[f] for f in fids]);assert poly.geom_type=='Polygon' and poly.is_valid,id
        poly=set_precision(poly,.001)
        is_new=id not in rows
        if is_new:
            row={'id':id,'siteId':9001,'source':'os-1893','name':name,'worldFootprint':rings(poly)[0],
                 'storeysEstimate':1,'material':'brick','roof':'gable','eavesHeight':3.8,
                 'roofRise':1.8,'roofBays':1,'roofAxis':'x','footprintEvidence':evidence,
                 'heightEvidence':'One-storey envelope inferred; no measured eaves height.',
                 'roofEvidence':'Pitched form interpreted; iron covering recorded only where labelled.',
                 'useEvidence':evidence}
            if id=='oilwharf-pump':row['roofMaterial']='iron'
            additions.append(row)
            model={'height':3.8,'roofRise':1.8,'roofBays':1,'roofAxis':'x'}
            old=poly;previous=0
        else:
            row=rows[id];model=models[id];old=Polygon(footprint(row,raw['sources'][row['source']]))
            a,b=list(old.exterior.coords)[:2];previous=math.degrees(math.atan2(b[1]-a[1],b[0]-a[0]))
        angle=axis(poly,previous)
        groups.append({'id':id,'modelIds':[id],'sourceFids':fids,'sourcePolygons':[rings(p) for fid in fids for p in source[fid].geoms],
                       'newModel':is_new,'previousUnionIoU':None if is_new else old.intersection(poly).area/old.union(poly).area})
        corrections.append({'modelId':id,'siteId':9001,'name':name,'groupId':id,'sourceFids':fids,
            **({'sourceFid':fids[0]} if len(fids)==1 else {}),'worldFootprint':rings(poly)[0],'worldHoles':rings(poly)[1:],
            'priorFootprint':rings(old)[0],'priorRotationDegrees':previous,'footprintRotationDegrees':angle,
            'preservedHeight':model['height'],'preservedRoofRise':model['roofRise'],
            'preservedRoofBays':model['roofBays'],'preservedRoofAxis':model['roofAxis'],
            'review':f'OS outline reviewed with July 1893 Goad F2. {evidence}',
            'comparison':{'centroidShiftMetres':None if is_new else old.centroid.distance(poly.centroid),
                          'areaRatio':None if is_new else poly.area/old.area,'axisChangeDegrees':angle-previous}})
    # OS circles are missing from the supplied extract for two of the four
    # active tanks. Trace their centres/radii on the same georeferenced mosaic.
    # Match the two hand-read circle centres to their supplied outline centres
    # before transferring the missing pair; the datasets differ locally by ~1.7 m.
    tank_controls=[(73371,[259,489]),(74874,[234,554])]
    offsets=[[source[fid].centroid.x-world(pixel)[0],source[fid].centroid.y-world(pixel)[1]]
             for fid,pixel in tank_controls]
    tank_offset=[sum(q[i] for q in offsets)/len(offsets) for i in range(2)]
    tank_specs=[('plant-6',73371,None),('plant-7',74874,None),('plant-8',None,[238,516]),
                ('oilwharf-tank-west',None,[203,533]),('oilwharf-disused-tank',73958,None)]
    tanks=[]
    for id,fid,pixel in tank_specs:
        old=next((s for s in raw['structures'] if s['id']==id),None)
        if fid:
            poly=source[fid];centre=list(poly.centroid.coords)[0];radius=math.sqrt(poly.area/math.pi)
        else:
            centre=[a+b for a,b in zip(world(pixel),tank_offset)]
            radius=math.dist(world(pixel),world([pixel[0]+16.5,pixel[1]]))
        tanks.append({'id':id,'siteId':9001,'kind':'tank','x':round(centre[0],3),'z':round(centre[1],3),
             'radius':round(radius,3),'height':4,'source':'os-1893','status':'disused' if fid==73958 else 'mapped petroleum tank',
             'evidence':'Circular plan on OS; July 1893 Goad F2 identifies '+('a disused tank.' if fid==73958 else 'four iron petroleum tanks.')+' Height and top profile inferred.',
             'positionEvidence':'Supplied OS outline centre and equal-area radius.' if fid else 'Centre and 16.5-pixel radius read from OS five-foot mosaic m18_131060_87140, translated using the two neighbouring source circles; absent from supplied extract.',
             **({'sourceFootprintFid':fid,'sourcePolygons':[rings(p) for p in source[fid].geoms]} if fid else {'mosaicPixels':pixel,'mosaicRadiusPixels':16.5,'registrationOffset':tank_offset}),
             'priorStructure':old})
    # Approximate working envelope traced inside the mapped roadside, wharf
    # limits and bank. This is not a cadastral parcel or a surveyed surface edge.
    yard_pixels=[[-80,275],[14,192],[110,268],[225,354],[305,410],[425,465],
                 [428,520],[417,558],[408,596],[342,604],[190,570],[22,458],[-76,395],[-95,334]]
    removed=[]
    for id,reason in [('oilwharf-0','Large rectangle occupies mapped open barrel-storage ground on OS and Goad; not a building.'),
                      ('oilwharf-8','Rectangle occupies open timber-yard ground beside the corrected Towers courtyard; no separate building on OS or Goad.')]:
        removed.append({'id':id,'reason':reason,'priorRecord':rows[id]})
    seams=[]
    targets={b['modelId']:Polygon(b['worldFootprint'],b['worldHoles']) for b in corrections}
    targets['oilwharf-2']=Polygon(models['oilwharf-2']['footprint'])
    for a,b in [('oilwharf-1','oilwharf-store-e'),('oilwharf-2','oilwharf-office')]:
        seams.append({'models':[a,b],'sourceOverlapAreaM2':targets[a].intersection(targets[b]).area,
                      'review':'Adjacent supplied outlines overlap slightly; keep source boundaries and partition the rendered seam once.'})
    result={'source':'Author-supplied london_buildings_1891-96_corr_v1.gpkg',
        'sourceCRS':'EPSG:3857 reprojected through BNG; scene origin E538900,N183209',
        'method':'Explicit OS/Goad-reviewed Oil Wharf ranges, four petroleum tanks and one disused tank; open storage cleared of spurious models.',
        'mapReview':['OS five-foot mosaics m18_131060_87140 and m18_131057_87140','July 1893 Goad volume F sheet 2'],
        'groups':groups,'buildings':corrections,'structures':[], 'additionalBuildings':additions,
        'boundaryOverlapReviews':seams,
        'removedBuildings':removed,'tanks':tanks,'tankControls':[{'sourceFid':fid,'mosaicPixels':pixel} for fid,pixel in tank_controls],
        'retainedEarlierMatches':['oilwharf-2'],
        'yard':{'id':9001,'name':'Oil Wharf','mosaicPixels':yard_pixels,'polygons':[[[world(p) for p in yard_pixels]]],
                'evidence':'Working envelope traced from period map, clipped against buildings, tanks, road and registered water. Boundary, wear and barrel positions interpreted.'},
        'deferred':['Lime & cement wharf kilns and associated ranges east of the oil yard require a separate apparatus pass.',
                    'Tiny detached source features, cranes, boundary stones and precise gates are not modelled.',
                    'The adjacent dwelling row retains its previous elevation pending the grouped housing pass.']}
    (ROOT/'data/maps/oil-wharf-footprint-alignment.json').write_text(json.dumps(result,indent=2)+'\n')
    print(f'{len(corrections)} reviewed ranges ({len(additions)} newly represented); two spurious masses removed; five mapped tanks.')

if __name__=='__main__':build()
