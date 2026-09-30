"""Prepare bounded OS context for the strip between Channelsea and the railway.

Writes the reviewed register/evidence only. Integration helpers let the parent
apply the proposed road and new water without replacing existing bank geometry.
"""
import copy
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from skimage.measure import find_contours
from shapely.geometry import Polygon, LineString, shape

from factory_map_sources import mosaic

ROOT = Path(__file__).resolve().parents[1]
REGISTER = 'data/maps/east-channelsea-context-alignment.json'
BASELINE = 'reference/footprint-model-alignment/east-channelsea-context-before.json'
load = lambda p: json.loads((ROOT/p).read_text())
digest = lambda data: hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':')).encode()).hexdigest()
ROAD_BOUNDS = [-100,-200,235,330]
GOODS_BOUNDS = [-220,-650,160,-245]
# Keep the public lane up to the mapped chemical entrance. The former south
# extension crossed shaded roofs 159/1640/7552 and is not a through street.
ROAD_PIXELS = [[705,335],[718,410],[729,485],[746,595],[760,663],
               [772,699],[773,713],[763,750],[750,800],[735,875],
               [718,970],[714,1030],[707,1090],[701,1125]]
SIDING_GROUPS = [
    [[281,329],[334,531],[377,636],[465,737],[552,789],[654,816],[748,825],[800,827]],
    [[315,314],[394,544],[423,632],[481,704],[568,771],[681,811],[800,827]],
    [[365,312],[438,521],[489,647],[550,727],[625,780],[711,812],[800,827]],
    [[408,289],[488,518],[531,629],[576,709],[661,775],[730,808],[800,827]],
    [[476,254],[550,465],[596,579],[644,672],[694,724],[752,769],[860,825],[950,878]],
    [[522,228],[597,431],[641,532],[683,625],[742,699],[817,749],[885,810],[950,878]],
]
DEPOT_PIXELS = [[215,304],[302,300],[381,274],[427,241],[518,207],[549,192],
                [585,179],[625,167],[683,306],[769,520],[851,700],[951,880],
                [900,906],[828,880],[703,860],[601,845],[492,831],[411,804],
                [353,754],[312,680],[279,596],[253,498],[237,394]]
STORES_PIXELS = [[715,345],[722,407],[732,484],[754,634],[749,661],[738,675],
                 [716,672],[650,650],[595,633],[533,617],[495,597],[485,537],
                 [478,450],[528,443],[595,418],[662,381]]


def blue_boundary(canvas, bounds):
    """Recover the reviewed blue paint pool, retaining separate mapped pools.

    Colour extraction is restricted to a manually inspected water feature crop;
    it does not classify buildings, parcels or map-wide land use. Fill internal
    letter/ink holes and simplify by one source pixel, never by model geometry.
    """
    x0,y0,x1,y1 = bounds
    cut = canvas[y0:y1,x0:x1].astype(int)
    blue = (cut[:,:,2]-cut[:,:,0] > 10) & (cut[:,:,1]-cut[:,:,0] > 8)
    labels,_ = ndimage.label(blue)
    areas = np.bincount(labels.ravel()); areas[0] = 0
    mask = ndimage.binary_fill_holes(labels == areas.argmax())
    contour = max(find_contours(mask.astype(float),.5),key=len)
    p = Polygon([(x+x0,y+y0) for y,x in contour]).simplify(1,preserve_topology=True)
    assert p.is_valid
    return [list(q) for q in p.exterior.coords][:-1]


def apply_road_context(district, register):
    """Add a scene-coordinate override of the former sheet-coordinate road."""
    road = copy.deepcopy(register['road']['preparedRoad'])
    matches = [r for r in district['roads'] if r['name'] == road['name']]
    if matches:
        assert len(matches) == 1 and matches[0] == road
    else:
        district['roads'].append(road)


def apply_water_context(ground, register):
    """Apply reviewed east-bank vertices, then append disconnected water pools."""
    for correction in register.get('bankCorrections',[]):
        river = next(r for r in ground['rivers'] if r['id']==correction['riverId'])
        ring = river['polygons'][correction['polygonIndex']][correction['ringIndex']]
        expected = copy.deepcopy(correction['priorRing'])
        for replacement in correction['replacements']:
            expected[replacement['vertex']] = replacement['point']
        assert ring in [correction['priorRing'],expected]
        river['polygons'][correction['polygonIndex']][correction['ringIndex']] = expected
    for river in register['additionalRivers']:
        addition = {k:copy.deepcopy(river[k]) for k in ['id','name','polygons','evidence']}
        matches = [r for r in ground['rivers'] if r['id'] == addition['id']]
        if matches:
            assert matches == [addition]
        else:
            ground['rivers'].append(addition)


def build(apply_road=False):
    baseline_path = ROOT/BASELINE
    if not baseline_path.exists():
        infra = load('docs/data/infrastructure.json')
        ground = load('docs/data/ground-plan.json')
        factories = load('docs/data/factory-buildings.json')
        baseline = dict(
            districtRoads=load('reference/footprint-model-alignment/east-channelsea-roads-before.json'),
            sourceRoad=next(r for r in load('data/maps/road-traces.json')['roads'] if r['name']=='Mill Meads works road'),
            builtRoads=infra['roads'],
            railways=[{k:r[k] for k in ['name','route','tracks'] if k in r} for r in infra['railways']],
            groundRivers=ground['rivers'],westRivers=factories['westContext']['rivers'])
        baseline_path.write_text(json.dumps(baseline,indent=2)+'\n')
    before = load(BASELINE)
    register = dict(
        source='Unmodified cached georeferenced OS London five-foot 1893 mosaic; no Goad corroboration asserted',
        method='Native OS review of the whole Channelsea/Woolwich railway strip, followed by bounded road, blue water, open-parcel and siding traces. Roof hatching is retained as buildings, not classed as open yard.',
        baseline=BASELINE,baselineSha256=digest(before),
        areaBounds=[-250,-800,280,390],
        retainedRiverGeometrySha256=dict(ground=digest(before['groundRivers']),west=digest(before['westRivers'])),
        retainedRailwayRoutesSha256=digest(before['railways']),evidenceImages=[])
    canvas,world,pixel = mosaic(ROAD_BOUNDS)
    points = world(ROAD_PIXELS).round(3).tolist()
    prior = next(r for r in before['builtRoads'] if r['name']=='Mill Meads works road')
    points[0] = prior['route'][0]
    road = dict(name=prior['name'],sheet='scene',points=points,width=6,kind='street',
        surface='setts',pixelWidth=canvas.shape[1],sourceBounds=ROAD_BOUNDS,
        sourcePixels=pixel(points).round(3).tolist(),bridgeSpans=[],
        alignmentEvidence='OS works lane re-read at native scale, ending at the chemical entrance. The former southern extension cut across shaded chemical roofs and does not establish a through road or bridge.',
        surfaceEvidence=before['sourceRoad']['surfaceEvidence'],
        eastChannelseaContextAlignment=dict(register=REGISTER))
    register['road'] = dict(name=road['name'],priorRoute=prior['route'],priorSourceRoad=before['sourceRoad'],
        reviewedSourceBounds=ROAD_BOUNDS,reviewedSourcePixels=ROAD_PIXELS,
        preparedRoad=road,ordinaryShoulderWidth=1.1,
        review='Retain the Abbey Lane junction and interpreted 6 m width. Fit the eastern industrial frontage and stop at the mapped entrance; no road is inferred through the retained southern roofs or to the separate footbridge.')
    water_specs = [
        (1301,'Langthorn/Globe western moat',GOODS_BOUNDS,[550,1100,819,1240]),
        (1302,'Brush Works eastern moat',GOODS_BOUNDS,[818,1080,910,1130]),
        (1303,'Eastern chemical works drain',ROAD_BOUNDS,[825,880,1075,1345]),
    ]
    register['additionalRivers'] = []
    for ident,name,bounds,crop in water_specs:
        raw,w,_ = mosaic(bounds)
        pixels = blue_boundary(raw,crop)
        ring = w(pixels).round(3).tolist()
        register['additionalRivers'].append(dict(id=ident,name=name,polygons=[[ring]],
            reviewedSourceBounds=bounds,reviewedSourcePixels=pixels,bluePaintCrop=crop,
            areaM2=Polygon(ring).area,
            evidence='Native OS blue water paint traced inside a manually reviewed crop. Existing banks and rivers retained; separate moat pools and the drain terminal remain disconnected. Water level, bed depth and any covered hydraulic connection are not established.'))
    register['additionalYards'] = []
    for ident,name,bounds,pixels in [
        (13011,'Stratford Market goods and coal depot',GOODS_BOUNDS,DEPOT_PIXELS),
        (9008,'Abbey Stores Yard',ROAD_BOUNDS,STORES_PIXELS)]:
        _,w,_ = mosaic(bounds);ring = w(pixels).round(3).tolist()
        assert Polygon(ring).is_valid
        register['additionalYards'].append(dict(id=ident,name=name,polygons=[[ring]],
            reviewedSourceBounds=bounds,reviewedSourcePixels=pixels,
            surface='cinder' if ident==13011 else 'earth',allowStock=False,
            evidence='OS-labelled open working compound. Parcel is a yard extent, not a roof; mapped buildings, water, streets and siding corridors must be subtracted by the yard builder. Surface material is interpreted; no blanket stock scattering.'))
    _,goods_world,_ = mosaic(GOODS_BOUNDS)
    register['railSidings'] = []
    for index,pixels in enumerate(SIDING_GROUPS):
        line = LineString(goods_world(pixels))
        # The OS fan has a single western track and five paired coal sidings.
        # Trace their centres directly; retain schematic rail profile/height.
        offsets = [0] if index==0 else [-1.7,1.7]
        for side,offset in enumerate(offsets):
            track = line if offset==0 else line.offset_curve(offset,join_style=2)
            register['railSidings'].append(dict(id=f'east-depot-{index}-{side}',
                points=[[round(x,3),round(z,3)] for x,z in track.coords],
                reviewedSourceBounds=GOODS_BOUNDS,reviewedSourcePixels=pixels,
                groupIndex=index,centreOffsetMetres=offset,
                evidence='OS coal/depot siding fan re-read west of Stratford Market roofs. One western track and five paired stems; pair spacing, rail profile and yard-level elevation interpreted. Existing Woolwich and main railway routes remain fixed.'))
    water = [Polygon(r['polygons'][0][0]) for r in register['additionalRivers']]
    sources = load('reference/footprint-model-alignment/east-channelsea-source-shapes.json')
    limits = []
    for fid,geometry in sources.items():
        body = shape(geometry)
        for r,p in zip(register['additionalRivers'],water):
            area = p.intersection(body).area
            if area > .01:
                limits.append(dict(sourceFid=int(fid),riverId=r['id'],overlapAreaM2=area,
                    evidence='Independent source wall differs locally from the OS water paint. This is a source alignment observation, not permission for an authored roof to overlap water; the model exterior needs native OS reconciliation.'))
    register['sourceWaterAlignmentLimits'] = limits
    # These are the east-bank vertices, read at native map scale beside solid
    # riverside roofs. Retain the opposite bank and both river terminals exactly.
    prior_river = next(r for r in before['groundRivers'] if r['id']==13)
    prior_ring = prior_river['polygons'][0][0]
    replacements = []
    bank_specs = [
        ('upper',[-260,-700,-170,-615],{5:181,6:181,7:182,8:182},['4975','24043']),
        ('lower',[-110,-245,20,-100],{28:251,29:256,30:267,31:275,32:294,34:395,35:416,36:433},
         ['31499','3926','13676','12581','5488','57354']),
    ]
    for label,bounds,controls,fids in bank_specs:
        raw,w,p = mosaic(bounds)
        revised = copy.deepcopy(prior_ring)
        for vertex,x in controls.items():
            sample = [x,float(p([prior_ring[vertex]])[0][1])]
            point = w([sample]).round(3).tolist()[0]
            revised[vertex] = point
            replacements.append(dict(vertex=vertex,priorPoint=prior_ring[vertex],point=point,
                reviewedSourceBounds=bounds,reviewedSourcePixels=[sample],
                evidence='Native OS bank edge beside the solid riverside exterior. The old independently registered channel edge entered the wall; only the river-facing east-bank control is corrected.'))
        im = Image.fromarray(raw)
        stem = f'reference/footprint-model-alignment/east-channelsea-bank-{label}'
        im.save(ROOT/(stem+'-raw.png'));draw=ImageDraw.Draw(im)
        draw.line([tuple(q) for q in p(prior_ring)],fill='red',width=2)
        draw.line([tuple(q) for q in p(revised)],fill='blue',width=2)
        for fid in fids:
            body=shape(sources[fid])
            for polygon in getattr(body,'geoms',[body]):
                draw.line([tuple(q) for q in p(polygon.exterior.coords)],fill='green',width=2)
        im.save(ROOT/(stem+'-after.png'))
        register['evidenceImages'] += [stem+'-raw.png',stem+'-after.png']
    new_ring = copy.deepcopy(prior_ring)
    for replacement in replacements:
        new_ring[replacement['vertex']] = replacement['point']
    assert Polygon(new_ring).is_valid
    bank_roofs = ['4975','24043','31499','3926','13676','12581','5488','57354']
    register['bankCorrections'] = [dict(riverId=13,polygonIndex=0,ringIndex=0,
        priorRing=prior_ring,replacements=replacements,
        sourceFids=[int(fid) for fid in bank_roofs],
        priorAreaM2=Polygon(prior_ring).area,areaM2=Polygon(new_ring).area,
        review='Re-read only the native OS eastern Channelsea bank at Victoria/Corn/Caledonian and Langthorn/Abbey chemical walls. Twelve existing controls corrected; opposite-bank controls, ring length, river terminals and every other existing river retained. These are solid shaded riverside ranges, not over-water roofs. No building trimming or blanket water exception.',
        sourceRoofWaterAreasM2=[dict(sourceFid=int(fid),
            priorArea=shape(sources[fid]).intersection(Polygon(prior_ring).buffer(.12)).area,
            area=shape(sources[fid]).intersection(Polygon(new_ring).buffer(.12)).area) for fid in bank_roofs])]
    for label,bounds in [('north',GOODS_BOUNDS),('south',ROAD_BOUNDS)]:
        raw,_,p = mosaic(bounds);im = Image.fromarray(raw)
        stem = f'reference/footprint-model-alignment/east-channelsea-context-{label}'
        im.save(ROOT/(stem+'-raw.png'));draw = ImageDraw.Draw(im)
        for river in register['additionalRivers']:
            pts = p(river['polygons'][0][0]);draw.line([tuple(q) for q in pts]+[tuple(pts[0])],fill='blue',width=2)
        for yard in register['additionalYards']:
            pts = p(yard['polygons'][0][0]);draw.line([tuple(q) for q in pts]+[tuple(pts[0])],fill='orange',width=2)
        if label=='north':
            for track in register['railSidings']:
                draw.line([tuple(q) for q in p(track['points'])],fill='purple',width=2)
        else:
            draw.line([tuple(q) for q in p(prior['route'])],fill='red',width=3)
            draw.line([tuple(q) for q in p(points)],fill='green',width=3)
        im.save(ROOT/(stem+'-after.png'))
        register['evidenceImages'] += [stem+'-raw.png',stem+'-after.png']
    (ROOT/REGISTER).write_text(json.dumps(register,indent=2)+'\n')
    if apply_road:
        district=load('data/maps/district-road-traces.json')
        apply_road_context(district,register)
        (ROOT/'data/maps/district-road-traces.json').write_text(json.dumps(district,indent=2)+'\n')
    print('East Channelsea register: mapped works lane, three blue water bodies, two open yards, eleven coal/depot siding traces and twelve east-bank controls reviewed.' + (' Road override applied.' if apply_road else ' Shared context inputs unchanged.'))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--apply-road','--apply',action='store_true')
    build(parser.parse_args().apply_road)
