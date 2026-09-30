"""Review Alderson's OS exteriors against Goad F3, including the omitted ropewalk."""
import json
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Polygon, LineString, shape
from shapely.ops import unary_union, split
from factory_alignment_records import record_group
from factory_map_sources import mosaic
from prepare_ink_works_alignment import axis, rings
from prepare_three_mills_north_alignment import polygon

ROOT=Path(__file__).resolve().parents[1]
BOUNDS=[-1025,-440,-895,-285]
ROPEWALK_PIXELS=[[83,201],[97,190],[227,394],[213,403]]
CUTS=[[[218,377],[260,350]],[[222,390],[262,363]]]

def build():
    load=lambda p:json.loads((ROOT/p).read_text())
    before=load('reference/footprint-model-alignment/marshgate-trades-before.json')
    models={b['id']:b for b in before['buildings']}
    source={int(f):polygon(shape(g)) for f,g in load('reference/footprint-model-alignment/marshgate-trades-source-shapes.json').items()}
    _,world,_=mosaic(BOUNDS)
    groups,rows=[],[]
    specs=[('east',[12830],['eaststore','810','814']),
           ('806',[461669],['806']),('808',[916613,1016515,903814],['808']),
           ('816',[766953],['816'])]
    for key,fs,suffixes in specs:
        ids=['site791-'+s for s in suffixes]
        target=polygon(set_precision(unary_union([source[f] for f in fs]),.001))
        parts=[target]
        division=None
        if key=='east':
            parts=[];remaining=target
            for cut in CUTS:
                a,b=world(cut);d=b-a
                pieces=list(split(remaining,LineString([a-d*10,b+d*10])).geoms)
                assert len(pieces)==2
                pieces.sort(key=lambda p:p.centroid.y)
                parts.append(pieces[0]);remaining=pieces[1]
            parts.append(remaining)
            division='Continuous OS eastern exterior, with approximate transverse Goad divisions between long stores802/804, projecting room810 and terminal store814. The former810 envelope was misplaced in the central yard.'
        names=[models[id]['name'] for id in ids]
        g,cs=record_group('alderson-rope-'+key,fs,source,models,ids,names,target,parts,
                          axis(target,models[ids[0]]['rotation']),division,
                          review_prefix='OS exterior identified against original Goad F3; prior low elevations and roof interpretation retained. ')
        groups.append(g);rows.extend(cs)
    trace=polygon(set_precision(Polygon(world(ROPEWALK_PIXELS)).difference(source[766953]),.001))
    b=models['site791-ropewalk']
    direct=dict(modelId=b['id'],name=b['name'],worldFootprint=rings(trace)[0],worldHoles=rings(trace)[1:],
                priorFootprint=b['footprint'],footprintRotationDegrees=axis(trace,b['rotation']),
                footprintSource='os-1893-direct-trace',
                footprintEvidence='Long shaded western ropewalk800 is absent from the supplied extract. Trace its OS exterior from the railway boundary to the separately mapped terminal816; retain that supplied terminal wall. Goad confirms a continuous one-storey wooden ropewalk. Unshaded western yard frames excluded.',
                eavesHeight=b['height'],roofRise=b['roofRise'],roofAxis=b['roofAxis'],roofBays=b['roofBays'])
    result=dict(source='Author-supplied london_buildings_1891-96_corr_v1.gpkg; cached OS London five-foot1893 mosaic; original Goad1893 F3',
        method='Explicit OS/Goad matches, direct trace of missing western ropewalk, removal of an unsupported open-yard envelope.',
        groups=groups,buildings=rows,structures=[],mapTracedBuildings=[direct],
        roadRenderChanges=[dict(modelId=id,
            contextRegister='data/maps/alderson-rope-context-alignment.json',
            preservedFootprint=models[id]['footprint'],
            preservedProfile={key:models[id][key] for key in ['height','roofRise','roofAxis','roofBays','rotation']},
            priorRenderPolygons=models[id]['renderPolygons'],
            evidence=('Existing source-linked drying-house exterior retained; moving the lane restores its previously clipped frontage.' if id=='site791-dry' else
                'Inherited unaligned ink envelope retained; only clipping against the independently reviewed lane changes. Full ink exterior review remains pending.'))
            for id in ['site940-firelighter','site940-24','site791-dry']],
        directTrace=dict(mosaicBounds=BOUNDS,mosaicPixels=ROPEWALK_PIXELS,divisionPixels=CUTS,
                         exclusionSourceFids=[766953],sourcePolygons=[rings(trace)]),
        removedBuildings=[dict(id='site791-north',siteId=791,priorFootprint=models['site791-north']['footprint'],
            reason='The former rectPixels[1088,278,57,43,-1] lies in the open central yard on original Goad F3. OS also shows open ground here; no northern cross-workshop is supported.',
            reclassification='Open rope works yard')],
        deferred=[dict(sourceFids=[918260,901356,990514,875824,861307,931009],
                       reason='Separate small yard sheds812 and drying-house ancillary strips have no reliable current counterpart; retain for ancillary review. Unshaded western frames are not enclosed full-height buildings.')],
        retainedSourceLinks=[dict(modelId='site791-dry',sourceFid=107330)])
    (ROOT/'data/maps/alderson-rope-footprint-alignment.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Alderson rope: six source-linked ranges, one direct ropewalk trace, one unsupported yard envelope removed.')

if __name__=='__main__':build()
