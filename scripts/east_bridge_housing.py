"""Bounded native OS roof-axis corrections beside Bridge Road.

The original district review remains readable; this later register replaces
only the listed roof axes after that review, retaining IDs and height estimates.
"""
import copy
import json
import math
from pathlib import Path

from PIL import Image,ImageDraw
from shapely import affinity
from shapely.geometry import box
from factory_map_sources import mosaic

ROOT=Path(__file__).resolve().parents[1]
REGISTER='data/maps/east-bridge-road-housing.json'
BASELINE='reference/footprint-model-alignment/east-bridge-road-housing-before.json'
BARNBY_BASELINE='reference/footprint-model-alignment/east-barnby-housing-before.json'
BARNBY_BOUNDS=[-110,-820,350,-250]
FRONTAGE_BASELINE='reference/footprint-model-alignment/east-st-thomas-frontage-housing-before.json'
RETURN_BASELINE='reference/footprint-model-alignment/east-bridge-road-block-return-housing-before.json'
RETURN_IDS={'district-leywick-morley-west-west-return',
    'district-leywick-morley-east-east-return'}
SUPPRESSED_IDS={'district-rokeby-barnby','district-rokeby-hotham','district-rokeby-randal','district-leywick-morley-west-east-return'}
BOUNDS=[-110,-820,170,-250]
# Native shaded roof-body axes beside Bridge Road and on both sides of Barnby Street.
AXES={
    'district-hotham-randal-west-return':[[799,853],[828,927]],
    'district-randal-skelton-west-return':[[856,1000],[882,1068]],
    'district-leywick-morley-east-west-return':[[932,1180],[955,1236]],
    'os-row-32':[[805,568],[1215,413]],
    'os-row-33':[[830,610],[1140,498]],
    'os-row-26-part-1':[[774,1305],[892,1263]],
    'os-row-39-part-1':[[548,656],[564,650]],
    'os-row-40-part-1':[[555,739],[710,685]],
    'os-row-41-part-1':[[577,826],[715,779]],
    'os-row-42-part-1':[[650,875],[742,843]],
    'os-row-43-part-1':[[675,953],[773,922]],
    'os-row-44-part-1':[[710,1030],[793,1002]],
    'os-row-45-part-1':[[716,1128],[850,1084]],
    'os-row-46':[[712,1209],[885,1150]],
    'os-row-47':[[469,570],[505,666]],
    'os-row-48-part-1':[[543,746],[563,813]],
    'os-row-49-part-1':[[603,901],[635,985]],
    'os-row-50':[[676,1059],[702,1132]],
}
def read(path):return json.loads((ROOT/path).read_text())
def rectangle(row):
    return affinity.translate(affinity.rotate(box(-row['width']/2,-row['depth']/2,row['width']/2,row['depth']/2),-row['rotation']),row['x'],row['z'])
def prepare():
    before=read(BASELINE);barnby=read(BARNBY_BASELINE)
    returns=read(RETURN_BASELINE)
    frontages=read(FRONTAGE_BASELINE)
    before={k:before[k]+barnby[k]+returns[k]+frontages[k] for k in ['reviewRows','publishedRows']}
    old={r['id']:r for r in before['reviewRows']}
    published={r['id']:r for r in before['publishedRows']}
    raw,world,pixel=mosaic(BOUNDS);rows=[]
    for ident,axis in AXES.items():
        bounds=BARNBY_BOUNDS if ident in {'os-row-32','os-row-33'} else BOUNDS
        _,source_world,_=mosaic(bounds)
        a,b=source_world(axis).round(3).tolist();dx,dz=b[0]-a[0],b[1]-a[1]
        geometry=dict(x=(a[0]+b[0])/2,z=(a[1]+b[1])/2,width=math.hypot(dx,dz),rotation=-math.degrees(math.atan2(dz,dx)),depth=old[ident]['depth'])
        house_count=1 if ident=='os-row-39-part-1' else max(1,round(geometry['width']/4.6))
        rows.append(dict(id=ident,priorReview=old[ident],priorPublishedRow=published[ident],reviewedSourceBounds=bounds,reviewedSourcePixels=axis,worldAxis=[a,b],geometry=geometry,houseCount=house_count,
            classification='One mapped shaded Barnby/Barry corner body; formerly mistaken for a continuous terrace over unshaded gardens.' if ident=='os-row-39-part-1' else 'Mapped shaded roof band; perpendicular corner bodies and unshaded gardens excluded.'))
    return_before=read(RETURN_BASELINE)
    return_prior={r['id']:r for r in return_before['reviewRows']}
    for previous in return_before['publishedRows']:
        ident=previous['id']
        if ident not in RETURN_IDS:continue
        geometry={k:previous[k] for k in ['x','z','width','depth','rotation']}
        angle=math.radians(-geometry['rotation']);half=geometry['width']/2
        axis=[[geometry['x']+sign*half*math.cos(angle),geometry['z']+sign*half*math.sin(angle)] for sign in [-1,1]]
        rows.append(dict(id=ident,priorReview=return_prior[ident],priorPublishedRow=previous,
            reviewedSourceBounds=BOUNDS,reviewedSourcePixels=pixel(axis).tolist(),worldAxis=axis,geometry=geometry,
            houseCount=previous.get('houseCount',previous['bays']),retainedPublishedGeometry=True,
            classification='Preserve the exact previously published perpendicular corner body in the two affected housing blocks. This is bounded preservation of earlier mapped work, not a new mapping claim. All later reviewed roof bodies and carriageways clear these existing shapes; repeating automatic fitting from the original broader axis would change established geometry and fit order.'))
    register=dict(baseline=BASELINE,barnbyBaseline=BARNBY_BASELINE,frontageBaseline=FRONTAGE_BASELINE,returnBaseline=RETURN_BASELINE,source='Unmodified cached OS London five-foot 1893 mosaic',
        method='Native roof-body axes re-read at the affected Bridge Road junction/frontages. Roof shading, street gaps and corner returns distinguish the bodies from back plots. IDs and height estimates retained; range lengths/centres/angles follow mapped roofs. House counts are estimates from mapped range lengths; one prior long terrace is a single corner body. No road-buffer trimming used.',rows=rows,
        evidenceImages=['reference/footprint-model-alignment/east-bridge-road-housing-raw.png','reference/footprint-model-alignment/east-bridge-road-housing-after.png'])
    register['suppressedRows']=[dict(id=ident,priorReview=old[ident],priorPublishedRow=published[ident],
        reason='The native OS shows one frontage band, already represented by a separate registered row. This second parallel envelope lies in unshaded rear gardens and projections; suppress the duplicate rather than moving it onto the existing frontage.') for ident in sorted(SUPPRESSED_IDS)]
    register['cornerReconciliations']={
        'os-row-26-part-1':['district-leywick-morley-east-west-return'],
        'os-row-41-part-1':['district-barnby-hotham-west-return'],
        'os-row-43-part-1':['os-row-49-part-1','district-hotham-randal-west-return'],
        'os-row-45-part-1':['os-row-50']}
    register['cornerReconciliationEvidence']='Main transverse hatch bands end before the separately represented perpendicular corner roofs. Surviving corners are reviewed or preserved as recorded per row; four explicitly registered garden duplicates are suppressed. No blanket shared-roof overlap exception.'
    im=Image.fromarray(raw);d=ImageDraw.Draw(im)
    for item in rows:
        for r,colour in [(item['priorPublishedRow'],'red'),({**item['priorReview'],**item['geometry']},'blue')]:
            d.line([tuple(q) for q in pixel(rectangle(r).exterior.coords)],fill=colour,width=2)
        d.text(tuple(pixel([[item['geometry']['x'],item['geometry']['z']]])[0]),item['id'].replace('os-row-',''),fill='blue')
    bridge=read('data/maps/east-channelsea-context-alignment.json')['roadCorrections'][0]['record']
    d.line([tuple(q) for q in pixel(bridge['points'])],fill='green',width=3)
    Image.fromarray(raw).save(ROOT/register['evidenceImages'][0]);im.save(ROOT/register['evidenceImages'][1])
    barnby_raw,_,barnby_pixel=mosaic(BARNBY_BOUNDS)
    barnby_image=Image.fromarray(barnby_raw);barnby_draw=ImageDraw.Draw(barnby_image)
    for item in rows:
        if item['id'] in {'os-row-32','os-row-33'}:
            barnby_draw.line([tuple(q) for q in barnby_pixel(rectangle(item['geometry']).exterior.coords)],fill='blue',width=2)
    barnby_road=next(c['record'] for c in read('data/maps/east-channelsea-context-alignment.json')['roadCorrections'] if c['name']=='Barnby Street')
    barnby_draw.line([tuple(q) for q in barnby_pixel(barnby_road['points'])],fill='green',width=2)
    barnby_evidence='reference/footprint-model-alignment/east-barnby-housing-after.png'
    barnby_image.crop((460,375,1350,760)).resize((1780,770)).save(ROOT/barnby_evidence)
    register['evidenceImages'].append(barnby_evidence)
    (ROOT/REGISTER).write_text(json.dumps(register,indent=2)+'\n')
    return register
def apply_review(original):
    register=read(REGISTER);changes={r['id']:r for r in register['rows']};result=[];found=set()
    for source in original:
        if source['id'] in SUPPRESSED_IDS:
            removed=next(r for r in register['suppressedRows'] if r['id']==source['id'])
            assert any(all(abs(source[k]-expected[k])<.005 for k in ['x','z','width','depth','rotation']) for expected in [removed['priorReview'],removed['priorPublishedRow']]),source['id']
            continue
        if source['id'] not in changes:
            result.append(copy.deepcopy(source));continue
        change=changes[source['id']];found.add(source['id'])
        keys=['x','z','width','depth','rotation']
        assert any(all(abs(source[k]-expected[k])<.005 for k in keys) for expected in [change['priorReview'],change['priorPublishedRow'],change['geometry']]),source['id']
        row=copy.deepcopy(source);row.update(change['geometry'])
        row['houseCount']=change['houseCount']
        row.update(mappedRefinement=True,districtReviewed=True,addedReturn=False,fitToStreet=False,
            eastBridgeHousingAlignment=dict(register=REGISTER,priorCentre=[change['priorReview']['x'],change['priorReview']['z']],sourceAxis=change['worldAxis']),
            evidence=register['method'])
        result.append(row)
    assert found==set(changes),(found,set(changes))
    return result
if __name__=='__main__':
    prepare();print('Bridge Road native roof register prepared: 18 corrected bodies, 2 preserved corners and 4 suppressed garden duplicates; retained IDs and height estimates unchanged.')
