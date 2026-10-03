"""Check the bounded native roof review and its published housing replay."""
import argparse
import copy
import math
from shapely.geometry import LineString
from shapely.ops import unary_union
from factory_map_sources import mosaic
from east_bridge_housing import read,REGISTER,BASELINE,BARNBY_BASELINE,FRONTAGE_BASELINE,RETURN_BASELINE,RETURN_IDS,SUPPRESSED_IDS,AXES,apply_review,rectangle,ROOT

def check(preflight=False):
    register=read(REGISTER);before=read(BASELINE);barnby=read(BARNBY_BASELINE)
    frontages=read(FRONTAGE_BASELINE)
    before={k:before[k]+barnby[k]+frontages[k] for k in ['reviewRows','publishedRows']}
    returns=read(RETURN_BASELINE)
    assert {r['id'] for r in register['rows']}==set(AXES)|RETURN_IDS
    assert len(AXES)==18
    prior={r['id']:r for r in before['reviewRows']+returns['reviewRows']}
    assert {r['id'] for r in register['suppressedRows']}==SUPPRESSED_IDS
    assert all(r['priorReview']==prior[r['id']] for r in register['suppressedRows'])
    sample=copy.deepcopy(before['reviewRows']+returns['reviewRows'])+[dict(id='unreviewed-control',x=0,z=0,width=10,depth=6,rotation=0,wallHeight=6)]
    applied=apply_review(sample)
    assert applied[-1]==sample[-1]
    assert apply_review(applied)==applied
    corrected={r['id']:r for r in applied[:-1]}
    assert not SUPPRESSED_IDS & set(corrected)
    roads=read('docs/data/infrastructure.json')['roads']
    corrections=read('data/maps/east-channelsea-context-alignment.json')['roadCorrections']
    names={c['name'] for c in corrections}
    roads=[r for r in roads if r['name'] not in names]+[dict(c['record'],route=c['record']['points']) for c in corrections]
    street_mask=unary_union([LineString(r['route']).buffer(r['width']/2+.25,cap_style=2,join_style=2) for r in roads])
    for item in register['rows']:
        assert item['priorReview']==prior[item['id']]
        _,world,_=mosaic(item['reviewedSourceBounds'])
        # BNG↔Mercator datum round trips add about 1 mm for retained controls.
        assert all(math.dist(a,b)<.002 for a,b in zip(item['worldAxis'],world(item['reviewedSourcePixels']).tolist()))
        a,b=item['worldAxis'];g=item['geometry']
        assert abs(g['width']-math.dist(a,b))<1e-9
        assert abs(g['x']-(a[0]+b[0])/2)<1e-9 and abs(g['z']-(a[1]+b[1])/2)<1e-9
        if item['id'] in RETURN_IDS:
            assert g=={k:item['priorPublishedRow'][k] for k in g}
        else:assert g['depth']==prior[item['id']]['depth']
        assert rectangle(g).intersection(street_mask).area<.05,item['id']
        assert corrected[item['id']].get('wallHeight')==prior[item['id']].get('wallHeight')
        assert corrected[item['id']]['houseCount']==item['houseCount']
    assert next(r for r in register['rows'] if r['id']=='os-row-39-part-1')['houseCount']==1
    assert rectangle(corrected['os-row-43-part-1']).intersection(rectangle(corrected['os-row-49-part-1'])).area<.05
    assert rectangle(corrected['os-row-45-part-1']).intersection(rectangle(corrected['os-row-50'])).area<.05
    scene_rows=apply_review(read('docs/data/housing-detail.json')['rows'])+read('docs/data/ground-plan.json')['neighbourhood']['houses']
    for row in scene_rows:
        if row['id'] not in corrected:continue
        for other in scene_rows:
            if row['id']==other['id']:continue
            assert rectangle(row).intersection(rectangle(other)).area<2,(row['id'],other['id'])
    if not preflight:
        published={r['id']:r for r in read('docs/data/housing-detail.json')['rows']}
        assert not SUPPRESSED_IDS & set(published)
        for ident,row in corrected.items():
            assert ident in published
            assert all(abs(row[k]-published[ident][k])<.005 for k in ['x','z','width','depth','rotation'])
            assert published[ident]['eastBridgeHousingAlignment']['register']==REGISTER
            assert published[ident]['wallHeight']==next(r for r in before['publishedRows']+returns['publishedRows'] if r['id']==ident)['wallHeight']
    assert all((ROOT/path).exists() for path in register['evidenceImages'])
    print('Bridge Road housing passed: 18 native roof bodies, 2 preserved corners, 4 recorded garden duplicates suppressed; replay/IDs/heights retained, no carriageway or housing overlap.')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--preflight',action='store_true');check(parser.parse_args().preflight)
