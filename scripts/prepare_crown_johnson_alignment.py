"""Review Crown/Johnson works against OS exteriors and Goad F3 alterations."""
import json
import math
from pathlib import Path
from shapely import affinity, set_precision
from shapely.geometry import Polygon, Point, box, shape
from shapely.ops import unary_union
from factory_alignment_records import record_group
from factory_map_sources import mosaic
from prepare_ink_works_alignment import axis, rings
from prepare_three_mills_north_alignment import polygon

ROOT=Path(__file__).resolve().parents[1]
BOUNDS=[-955,-165,-815,-65]
# Missing middle of the shaded southern waterside range, between supplied caps.
TRACE_PIXELS=[[400,278],[435,253],[444,267],[411,293]]
SPECS=[('north',[359606],[1]),('main',[151775,405118],[2]),
       ('ovens-tanks',[200526,558226,473300,915520],[3,4,5]),
       ('east-upper',[817408],[6]),('east-lower',[84296,767359],[8]),
       ('west-north',[486490],[9]),('west-store',[857997,35573],[10])]

def build():
    load=lambda p:json.loads((ROOT/p).read_text())
    before=load('reference/footprint-model-alignment/remaining-trades-before.json')
    models={b['id']:b for b in before['buildings']}
    source={int(f):polygon(shape(g)) for f,g in load('reference/footprint-model-alignment/remaining-trades-source-shapes.json').items()}
    groups,rows=[],[]
    for key,fs,ns in SPECS:
        ids=[f'site398-range-{n}' for n in ns]
        target=polygon(set_precision(unary_union([source[f] for f in fs]),.001))
        angle=axis(target,models[ids[0]]['rotation']);parts=[target]
        evidence='OS supplies the exterior. Goad labels Johnson & Hooper under alterations and has a broader northern process body; room identity and inherited elevations remain approximate.'
        if key=='ovens-tanks':
            # The western Goad ovens/tanks are divided within one OS room;
            # eastern574/576 remain one inherited low roof interpretation.
            west=source[200526];angle=axis(west,models[ids[0]]['rotation'])
            local=affinity.rotate(west,-angle,origin=(0,0));x0,z0,x1,z1=local.bounds
            mask=affinity.rotate(box(-10000,-10000,10000,(z0+z1)/2),angle,origin=(0,0))
            a=polygon(set_precision(west.intersection(mask),.001))
            b=polygon(set_precision(west.difference(mask),.001))
            parts=[a,b,polygon(set_precision(unary_union([source[f] for f in fs[1:]]),.001))]
            evidence+=' The northern ovens and southern tank-room split within200526 is interpreted, not an OS internal wall; the eastern rooms retain a single existing profile.'
        names=[models[id]['name'] for id in ids]
        g,cs=record_group('crown-johnson-'+key,fs,source,models,ids,names,target,parts,angle,evidence,
            review_prefix='Explicit OS exterior review against Goad F3 and the previous approximate envelopes; keep prior roof and elevation interpretation. ')
        groups.append(g);rows.extend(cs)
    _,world,_=mosaic(BOUNDS)
    # Supplied terminal walls take precedence over manually read seam endpoints.
    traced=polygon(set_precision(unary_union([source[760489],Polygon(world(TRACE_PIXELS))]).difference(source[767359]),.001))
    b=models['site398-range-7']
    direct=dict(modelId=b['id'],name='Crown / Johnson southern waterside range, Goad578',
        worldFootprint=rings(traced)[0],worldHoles=rings(traced)[1:],priorFootprint=b['footprint'],
        footprintRotationDegrees=axis(traced,b['rotation']),footprintSource='os-1893-direct-trace',
        footprintEvidence='Southern shaded OS range is partly missing from the supplied extract. Retain supplied western cap760489, trace the missing middle and stop at independently supplied eastern room767359. Goad578 confirms the long enclosed range above the lock; previous shoreline trim is superseded by this reviewed exterior.',
        eavesHeight=b['height'],roofRise=b['roofRise'],roofAxis=b['roofAxis'],roofBays=b['roofBays'])
    old=next(s for s in before['structures'] if s['siteId']==398)
    base=source[1018184];centre=Point(round(base.centroid.x,3),round(base.centroid.y,3));angle=axis(base,old['rotation'])
    lo,hi=0.,old['radius']
    for _ in range(50):
        radius=(lo+hi)/2
        plinth=affinity.rotate(box(centre.x-radius*1.2,centre.y-radius*1.2,centre.x+radius*1.2,centre.y+radius*1.2),angle,origin=centre)
        if base.covers(plinth):lo=radius
        else:hi=radius
    stack=dict(id=old['id'],sourceFid=1018184,sourcePolygons=[rings(base)],centre=[centre.x,centre.y],rotation=angle,
        radius=math.floor(lo*1000)/1000,priorRadius=old['radius'],priorCentre=[old['x'],old['z']],preservedHeight=old['height'],
        review='Goad square chimney on the western edge of process room586 corresponds to the independent OS square1018184 between the western store and northern process rooms. Circular948832 is a separate northern plant symbol and is not substituted by proximity.',
        profileEvidence='Complete rotated square plinth fitted inside the mapped symbol. Existing22m height remains an estimate; no printed measurement is asserted.')
    result=dict(source='Author-supplied london_buildings_1891-96_corr_v1.gpkg; cached OS five-foot mosaic; original July1893 Goad F3',
        method='Nine retained ranges matched explicitly to OS exteriors; missing southern roof traced with supplied terminal walls. Goad alterations and approximate compartment identities recorded separately.',
        groups=groups,buildings=rows,structures=[stack],mapTracedBuildings=[direct],
        directTrace=dict(mosaicBounds=BOUNDS,mosaicPixels=TRACE_PIXELS,includedSourceFids=[760489],exclusionSourceFids=[767359],sourcePolygons=[rings(traced)]),
        deferred=[dict(sourceFids=[125888,861166,948832,236176],reason='Separate northern buildings, plant and lane-edge body are not absorbed into the inherited main process block. Goad shows the works under alterations; additional room/plant modelling needs separate review.'),
                  dict(feature='Goad northern compound and floor marks',reason='OS has separated bodies where Goad presents a broader connected works under alterations. Exact temporal sequence, internal room attribution and several inherited floor estimates remain unresolved; this pass fixes exterior placement without claiming a full architectural reconstruction.')])
    (ROOT/'data/maps/crown-johnson-footprint-alignment.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Crown/Johnson: nine source-linked ranges, one southern direct trace, one mapped chimney base.')

if __name__=='__main__':build()
