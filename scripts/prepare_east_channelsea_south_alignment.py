"""Replace eastern industrial sketch masses with reviewed OS roof exteriors.

OS supplies plans only. Low industrial elevations and repeated gables remain
explicit interpretations; no fire-insurance plan or measured height is claimed.
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

ROOT=Path(__file__).resolve().parents[1]
NAME='east-channelsea-south'
BASELINE='reference/footprint-model-alignment/east-channelsea-before.json'
CACHE='reference/footprint-model-alignment/east-channelsea-source-shapes.json'
# Each listed source was checked against the original OS shading and compound.
# Small ancillary roofs are included; tiny unclassified equipment is deferred.
SPECS={
 9008:[71034,900327,958178,264568,919166,22715,842532,821774,818910,510912],
 874: [7362,26110,117212,12619,11571,771974,952571,16916,725887,5848,839396,692521,467943,615130,98677,4679],
 512: [782342,136652,804835,4761,881988,971092,898550,512784,948443,967143,814633,855439,83490,11522,737795],
 513: [445306,737250,8787,957626,604384,524757],
 875: [1023185,773893,489984],
 876: [159,625837,887572,595218,918929,909850,370011,790607,1036619,1640,22943,7552,35379,1066495,83268,867522,707076],
 1125:[78145,69120,11488,103154,7992,855354,549786,868911,698929,792924,549997,106621,650619,303696,916386,786785],
}
LABELS={874:'Stirling Chemical Works',512:'Phoenix Black Works',513:'Printing Ink Works',
        875:'West Ham Chemical Works',876:'Abbey Mills Chemical Works',1125:'Oil and Stearine Works',9008:'Abbey Stores Yard (West Ham Corporation)'}
# Pixels from a 2x native cached-map crop. The crop origin is (105,247) in
# mosaic([-30,160,110,275]); local -10,-1 pixel offset registers the printed
# shared wall to independent source159 (approximately 1.9 m correction).
DIRECT_PIXELS=[[64,282],[577,196],[566,133],[458,148],[450,86],
               [189,128],[194,164],[112,178],[114,209],[89,217],[84,238],[74,241]]

def profile(p,ident,site,name,height=None):
    angle=axis(p,0)
    q=affinity.rotate(p,-angle,origin=p.centroid)
    width=q.bounds[2]-q.bounds[0];depth=q.bounds[3]-q.bounds[1]
    roof_axis='x' if width>=depth else 'z';span=depth if roof_axis=='x' else width
    bays=max(1,math.ceil(span/14));rise=min(3.6,max(.8,span/bays*.25))
    h=height if height is not None else 6.9 if p.area>180 else 3.8
    return dict(id=ident,siteId=site,source='os-1893',name=name,
        worldFootprint=rings(p)[0],worldHoles=rings(p)[1:],
        footprintRotationDegrees=angle,eavesHeight=h,roofRise=rise,
        roofAxis=roof_axis,roofBays=bays,material='brick',roof='gable',
        storeysEstimate=2 if h>6 else 1,
        footprintEvidence='Individually reviewed roof exterior on the original cached OS five-foot map and supplied building extract.',
        heightEvidence=f'Estimated {h:g} m eaves for a low industrial range; no measured elevation or fire-insurance floor annotation available for this record.',
        roofEvidence='Interpreted simple gables, with repeated bays over broad roofs. OS records the exterior, not these roof pitches or divisions.')

def build():
    cached=json.loads((ROOT/CACHE).read_text())
    source={int(k):polygon(shape(v)) for k,v in cached.items() if int(k) in {f for fs in SPECS.values() for f in fs}}
    missing={f for fs in SPECS.values() for f in fs}-source.keys()
    assert not missing,missing
    groups=[];rows=[];added=[]
    for sid,fids in SPECS.items():
        for index,fid in enumerate(fids,1):
            exclusions={7992:[78145,855354],303696:[916386]}.get(fid,[])
            raw_target=source[fid].difference(unary_union([source[f] for f in exclusions])) if exclusions else source[fid]
            target=polygon(set_precision(raw_target,.001))
            ident=f'east-{sid}-{fid}'
            label=LABELS[sid]+(' — main roof' if fid==159 else f' — range {index}')
            b=profile(target,ident,sid,label,3.8 if sid==9008 else None)
            added.append(b)
            template=dict(b,footprint=b['worldFootprint'],rotation=b['footprintRotationDegrees'],height=b['eavesHeight'])
            g,bs=record_group(ident,[fid],source,{ident:template},[ident],[label],target,[target],b['footprintRotationDegrees'],
                 'Complete individually shaded OS roof retained. Supplied recesses and interior openings remain open.',additional=True,
                 review_prefix='Original cached OS five-foot map and supplied exterior reviewed together; no Goad coverage asserted. ')
            g['previousUnionIoU']=0
            for correction in bs:
                correction.update(priorFootprint=[],additionalModel=True,profileEvidence=b['heightEvidence']+' '+b['roofEvidence'])
            if exclusions:
                g['sourceReconciliation']=dict(excludedSourceFids=exclusions,removedAreaM2=source[fid].area-raw_target.area,
                    evidence='Small source digitisation overlap along independently mapped adjacent roof edges; give the separate neighbouring range its full supplied exterior.')
            groups.append(g);rows.extend(bs)
    _,to_world,_=mosaic([-30,160,110,275])
    coordinates=to_world([[105+(x-10)/2,247+(y-1)/2] for x,y in DIRECT_PIXELS])
    target=Polygon(coordinates)
    # Exact mapped shared wall controls take precedence over raster line width.
    neighbours=unary_union([source[f] for f in [159,625837,887572,595218]])
    target=polygon(target.difference(neighbours))
    target=polygon(set_precision(target,.001))
    direct=profile(target,'east-875-main-direct',875,'West Ham Chemical Works — directly traced main roof',6.9)
    direct.update(footprintSource='os-1893-direct-trace',footprintEvidence='Main West Ham Chemical Works roof omitted from supplied extract; traced from OS hatching and locally registered to the shared Abbey Mills wall.')
    added.append(direct)
    result=dict(source='Author-supplied london_buildings_1891-96_corr_v1.gpkg; original cached OS London five-foot map',
      sourceCRS='EPSG:3857 reprojected through BNG; scene origin E538900,N183209',baseline=BASELINE,
      method='Replace six unreviewed industrial sketch compounds and the municipal stores yard with complete individually reviewed OS roofs. Heights and gables are estimates; no fire-insurance coverage claimed.',
      additionalSites=[dict(id=s,name=n,sources=['os-1893'],coverage='Individual OS-mapped ranges',notes='OS roof exteriors reviewed; eaves, roof forms and internal process identities remain estimates.') for s,n in LABELS.items()],
      additionalBuildings=added,groups=groups,buildings=rows,structures=[],
      mapTracedBuildings=[dict(direct,modelId=direct['id'])],
      directMapTraces=[dict(modelId=direct['id'],worldFootprint=direct['worldFootprint'],worldHoles=direct['worldHoles'],
        nativeMosaicBounds=[-30,160,110,275],cropOriginPixels=[105,247],cropScale=2,pixels=DIRECT_PIXELS,
        localPixelOffset=[-10,-1],evidence='Shaded main northern roof, locally tied to source159 shared wall; exclude the small unshaded northwest enclosure and northeast yard.')],
      evidenceImages=['reference/footprint-model-alignment/strip-middle-raw.png','reference/footprint-model-alignment/strip-middle-source.png','reference/footprint-model-alignment/strip-south-raw.png','reference/footprint-model-alignment/strip-south-source.png'],
      deferred=[dict(feature='Tiny equipment and chimney symbols',reason='Unclassified tiny source polygons are not promoted automatically into buildings or stacks. Previous generic 36 m sketch chimneys are superseded; a dedicated map/photo chimney review remains needed.'),
        dict(feature='Internal process divisions and elevations',reason='No fire-insurance room plan used. Roof bays and low eaves are visual interpretations, not surveyed architectural claims.'),
        dict(feature='Abbey Mills southern roof',reason='Sources1640,22943,7552 are diagonally hatched roof across an OS sheet seam. Native map review confirms a roof, not the adjoining unshaded yard; southern footpath remains outside.'),
        dict(feature='Eastern ancillary attribution',reason='Detached roofs35379,1066495,83268,867522,707076 share the lane beside Abbey Mills works; exact individual tenancy is not established.')])
    (ROOT/f'data/maps/{NAME}-footprint-alignment.json').write_text(json.dumps(result,indent=2)+'\n')
    print(NAME,len(rows),'source-linked roofs and one direct OS roof; seven sites.')

if __name__=='__main__':build()
