"""Match mill/wharf exteriors and attach interpreted landmark details to them."""
import json
from pathlib import Path
from shapely import affinity, set_precision
from shapely.geometry import Polygon, Point, LineString, box, shape
from shapely.ops import unary_union
from prepare_ink_works_alignment import axis, rings
from prepare_three_mills_north_alignment import polygon
from factory_alignment_records import record_group
from factory_map_sources import mosaic

ROOT=Path(__file__).resolve().parents[1]
SPECS=[('house-west',[14650],['house-west']),
       ('house-main',[35019,17973],['house-main']),
       ('house-east',[37328],['house-east']),
       ('house-tail',[62255,545510],['house-tail']),
       ('clock',[5360],['clock-kilns','clock']),
       ('wharf',[4800,3046],['wharf','wharf-south'])]


def build():
    load=lambda p:json.loads((ROOT/p).read_text())
    before=load('reference/footprint-model-alignment/three-mills-landmarks-before.json')
    models={b['id']:b for b in before['buildings']}
    wanted={f for _,fs,_ in SPECS for f in fs}
    source={f['properties']['sourceFid']:polygon(affinity.affine_transform(shape(f['geometry']),[1,0,0,-1,-538900,183209]))
        for f in load('reference/historic-building-footprints-2026-09-28/current-scene-buildings-bng.geojson')['features'] if f['properties']['sourceFid'] in wanted}
    groups,corrections=[],[]
    for name,fids,ids in SPECS:
        target=polygon(set_precision(unary_union([source[f] for f in fids]),.001))
        angle=axis(target,models[ids[-1] if name=='clock' else ids[0]]['rotation'])
        local=affinity.rotate(target,-angle,origin=(0,0));x0,y0,x1,y1=local.bounds
        parts,division=[target],None
        if name=='clock':
            cut=-652.8
            cells=[box(x0-1,y0-1,cut,y1+1),box(cut,y0-1,x1+1,y1+1)]
            division='Western kilns 844/845 and main mill 842 share OS exterior 5360; internal cut is interpreted from the Goad kiln strip. Northern mapped projection retains the stair/clock tower.'
        elif name=='wharf':
            cut=32.8
            cells=[box(x0-1,y0-1,x1+1,cut),box(x0-1,cut,x1+1,y1+1)]
            division='Join source polygons across their artificial straight seam. Retain the two prior warehouse roof ranges, divided near the mapped bend; this internal division is interpreted, not the source seam.'
        if len(ids)>1:
            parts=[polygon(set_precision(affinity.rotate(local.intersection(cell),angle,origin=(0,0)),.001)) for cell in cells]
        group,rows=record_group('three-mills-landmarks-'+name,fids,source,models,ids,
            [models[id]['name'] for id in ids],target,parts,angle,division)
        if name=='house-main':
            # Sample the actual long walls instead of placing weatherboarding
            # on a symmetric bounding box around an irregular centroid.
            coords=list(local.exterior.coords)
            facades=[]
            for sign in [-1,1]:
                candidates=[(a,b) for a,b in zip(coords,coords[1:])
                    if abs(b[0]-a[0])>abs(b[1]-a[1])*2
                    and ((a[1]+b[1])/2<(y0+y1)/2)==(sign<0)]
                a,b=max(candidates,key=lambda pair:abs(pair[1][0]-pair[0][0]))
                pts=[(a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t) for t in [.05,.95]]
                facades.append([list(affinity.rotate(Point(p),angle,origin=(0,0)).coords)[0] for p in pts])
            rows[0]['landmarkDetails']=dict(houseFacades=facades,
                evidence='Weatherboarded facade span attached to mapped exterior walls; elevations, windows and dormers remain interpreted.')
        if name=='clock':
            to_world=lambda x,y:list(affinity.rotate(Point(x,y),angle,origin=(0,0)).coords)[0]
            rows[0]['landmarkDetails']=dict(kilnCaps=[dict(centre=to_world(-654.95,y),radius=1.95,height=5.7) for y in [276,284]],
                tower=dict(centre=to_world(-655.75,269.65),width=4.0,baseHeight=12,lanternHeight=5.5,spireHeight=3.6),
                evidence='Two interpreted kiln caps fit inside the western strip; clock/stair tower attaches to its mapped northern projection. Prior vertical dimensions retained; horizontal dimensions fitted to the footprint.')
        groups.append(group);corrections.extend(rows)
    result=dict(source='Author-supplied london_buildings_1891-96_corr_v1.gpkg',sourceCRS='EPSG:3857 reprojected through BNG; scene origin E538900,N183209',
        method='Explicit House/Clock Mill and wharf OS/Goad matches; mapped millrace relationships retained, landmark details attached to corrected footprints.',
        groups=groups,buildings=corrections,structures=[],
        deferred=[dict(feature='Small northern House Mill projections, freestanding plant and southern Clock Mill projection',reason='Separate plant/low annex interpretation; no additional full-height volumes.')])
    (ROOT/'data/maps/three-mills-landmark-footprint-alignment.json').write_text(json.dumps(result,indent=2)+'\n')
    roads=load('data/maps/district-road-traces.json')
    lane=next(q for q in roads['roads'] if q['name']=='Three Mills Lane')
    branch=next(q for q in roads['roads'] if q['name']=='Three Mills Lane beside distillery')
    for road in [lane,branch]:
        if 'threeMillsLandmarkAlignment' not in road:
            road['threeMillsLandmarkAlignment']={k:road[k] for k in ['points','sourcePixels','width','kind','bridgeSpans']}
    lane['points']=lane['threeMillsLandmarkAlignment']['points'][:6]+[[-611,397],[-601,396],[-589,394.2],[-583.5,394.2],[-575,396.2],[-570,395]]+lane['threeMillsLandmarkAlignment']['points'][-2:]
    lane['buildingClearanceReviews']=[dict(modelIds=['house-tail','clock-kilns'],shoulderWidth=.9,
        evidence='Re-read OS mill-court bend retains the 7 m carriageway. A 0.9 m pavement allowance at the kiln/tail pinch preserves both supplied walls; minimum opposing exterior gap is 9.469 m.')]
    lane['threeMillsLandmarkAlignment']['review']='OS centreline follows the open mill court north of the clock/stair projection. Western approach, main Lea bridge and distillery junction retained.'
    branch['points']=[[-559.938,391.703],[-559.5,387],[-561,379],[-564,369.588]]
    branch.update(width=2.2,kind='path')
    branch['threeMillsLandmarkAlignment']['review']='OS labels this eastern route F.P.; re-read footpath east of office 742 with an interpreted 2.2 m width. Its existing provisional water crossing follows the corrected route.'
    span=dict(branch['bridgeSpans'][0]);span['points']=[[-560.4375,382],[-561,379],[-564,369.588]]
    span['evidence']='Provisional narrow footpath deck/culvert at the independently registered bank; route corrected to pass east of mapped office 742. Structure and level remain uncertain.'
    branch['bridgeSpans']=[span]
    for road in [lane,branch]:
        _,_,pixel=mosaic(road['sourceBounds']);road['sourcePixels']=pixel(road['points']).round(3).tolist()
    later=ROOT/'data/maps/remaining-trades-context-alignment.json'
    if later.exists():
        from prepare_remaining_trades_context import apply_context
        apply_context(roads,json.loads(later.read_text()),names={'Three Mills Lane'})
    (ROOT/'data/maps/district-road-traces.json').write_text(json.dumps(roads,indent=2)+'\n')
    print('Three Mills landmarks: eight existing ranges in six groups; mapped facade/tower/cap anchors and corrected mill-court routes.')

if __name__=='__main__':build()
