"""Match mineral-water ranges to OS, preserving church and open yard space."""
import json
from pathlib import Path
from shapely import set_precision
from shapely.geometry import shape
from shapely.ops import unary_union
from factory_alignment_records import record_group
from prepare_ink_works_alignment import axis
from prepare_three_mills_north_alignment import polygon

ROOT=Path(__file__).resolve().parents[1]
SPECS=[
    (1,[108407,27009],'Mineral water works — northern bottling range',
     'Shaded northern strip and attached broad middle room. The earlier envelope lay southwest over the open court and St Mary’s church; neither is part of this factory volume.'),
    (2,[154380,32892],'Mineral water works — southern range',
     'Two touching southern compartments, including the angled southern end. Retain the existing low roof profile; no measured elevation is asserted.'),
    (3,[235227,825734],'Mineral water works — eastern service rooms',
     'Two touching eastern service compartments. Relocate the old small-yard envelope off the church nave. Room use remains interpreted; OS establishes separate shaded exteriors.')]

def build():
    load=lambda p:json.loads((ROOT/p).read_text())
    before=load('reference/footprint-model-alignment/mill-brush-brewery-before.json')
    models={b['id']:b for b in before['buildings']}
    cached=load('reference/footprint-model-alignment/mill-brush-brewery-source-shapes.json')
    source={f:polygon(shape(cached[str(f)])) for _,fs,_,_ in SPECS for f in fs}
    groups,rows=[],[]
    for n,fs,name,evidence in SPECS:
        id=f'west-792-{n}'
        target=polygon(set_precision(unary_union([source[f] for f in fs]),.001))
        group,corrections=record_group(f'mineral-water-{n}',fs,source,models,[id],[name],
            target,[target],axis(target,models[id]['rotation']),evidence,
            review_prefix='Explicit OS mineral-water works exterior match; prior interpreted heights and roofs retained. No Goad corroboration asserted. ')
        groups.append(group);rows.extend(corrections)
    result=dict(source='Author-supplied london_buildings_1891-96_corr_v1.gpkg; cached OS London five-foot 1893 mosaic',
        sourceCRS='EPSG:3857 reprojected through BNG; scene origin E538900,N183209',
        method='Three existing profiles relocated onto explicitly reviewed shaded factory ranges; church and open western court excluded.',
        groups=groups,buildings=rows,structures=[],
        evidenceImages=[f'reference/footprint-model-alignment/mineral-water-{kind}.png' for kind in ['raw','source','models','after']],
        excludedContext=[dict(sourceFids=[5167],reason='St Mary’s Church, with nave/aisle columns and labelled churchyard; never a mineral-water works range.'),
                         dict(sourceFids=[52934,344113,1186767],reason='Separate church/school-side buildings south of the works court; ownership and use not established as factory ranges.')],
        deferred=[dict(sourceFids=[44811,643220,1059979,1130193],reason='Separate northern cross-range and small terminal features have no current counterpart; retain source context for ancillary-building review.')])
    (ROOT/'data/maps/mineral-water-footprint-alignment.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Mineral water: three retained ranges in three groups; church and open western court excluded.')

if __name__=='__main__':build()
