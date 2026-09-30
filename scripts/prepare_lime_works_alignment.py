"""Match the lime works' separate rooms and two existing kiln bodies to OS."""
import json
import math
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Polygon, Point, shape
from factory_alignment_records import record_group
from prepare_ink_works_alignment import axis, rings
from prepare_three_mills_north_alignment import polygon

ROOT=Path(__file__).resolve().parents[1]
SPECS=[(1,79566),(2,18540),(3,109441),(4,403081)]


def build():
    load=lambda p:json.loads((ROOT/p).read_text())
    before=load('reference/footprint-model-alignment/soap-wharves-before.json')
    models={b['id']:b for b in before['buildings']}
    cached=load('reference/footprint-model-alignment/soap-wharves-source-shapes.json')
    source={fid:polygon(shape(cached[str(fid)])) for fid in [f for _,f in SPECS]+[1022949,914794]}
    groups,rows=[],[]
    for n,fid in SPECS:
        id=f'site255-os-{n}'
        target=polygon(set_precision(source[fid],.001))
        group,corrections=record_group(f'lime-works-{n}',[fid],source,models,[id],
            [models[id]['name']],target,[target],axis(target,models[id]['rotation']),
            review_prefix='Explicit OS lime-works shaded exterior; previous interpreted elevation and roof retained. No Goad corroboration asserted. ')
        groups.append(group);rows.extend(corrections)
    plants=[]
    for id,fid in [('plant-4',1022949),('plant-5',914794)]:
        old=next(p for p in before['structures'] if p['id']==id)
        outline=source[fid]
        exterior=Polygon(outline.exterior)
        centre=Point(round(exterior.centroid.x,3),round(exterior.centroid.y,3))
        radius=math.floor(centre.distance(exterior.boundary)*1000)/1000
        plants.append(dict(old, x=centre.x,z=centre.y,radius=radius,
            sourceFootprintFid=fid,sourcePolygons=[rings(outline)],priorStructure=old,
            equalAreaRadius=round(math.sqrt(exterior.area/math.pi),3),
            positionEvidence='Existing kiln matched to the inspected OS circular opening; rounded centroid of its outer mapped envelope.',
            radiusEvidence='Inscribed circular body inside the outer mapped envelope; full source outline retained including the eastern throat hole.',
            heightEvidence='Previous inferred 7 m height retained; OS supplies the plan, not a measured elevation.',
            geometryEvidence='Existing simple cylindrical kiln body retained. Mapped throat and enclosing rectangular plant are evidence for a future architectural pass, not a roofed building outline.'))
    result=dict(source='Author-supplied london_buildings_1891-96_corr_v1.gpkg; cached OS London five-foot 1893 mosaic',
        sourceCRS='EPSG:3857 reprojected through BNG; scene origin E538900,N183209',
        method='Four separate shaded OS room exteriors replace broad overlapping envelopes. Two existing kiln bodies follow circular source envelopes; elevations and roof profiles remain interpreted.',
        groups=groups,buildings=rows,structures=[],mappedPlants=plants,
        evidenceImages=[f'reference/footprint-model-alignment/lime-works-{s}.png' for s in ['raw','source','models']],
        deferred=[dict(sourceFids=[1024423,1043598],reason='Additional northern and western kiln openings have no existing plant counterparts; retain source context pending the separate kiln architecture pass.'),
                  dict(sourceFids=[802500,940660,942970,953056,973685,475237,647344,124623],reason='Ancillary rooms and kiln enclosures are separate source evidence. Do not extend the four current room envelopes over circular openings or add inferred full-height bodies without reviewing their relationship to the kiln apparatus.')])
    (ROOT/'data/maps/lime-works-footprint-alignment.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Lime works: four source-linked rooms; two existing 7 m kiln bodies fitted to mapped circles.')


if __name__=='__main__':build()
