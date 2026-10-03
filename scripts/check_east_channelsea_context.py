"""Check the bounded eastern road, water, yard and goods-siding register."""
import argparse
import copy
import json
import math
from pathlib import Path
import numpy as np
from scipy.interpolate import CubicSpline

from shapely.geometry import LineString, Point, Polygon, shape, box
from shapely import affinity
from shapely.ops import unary_union

from factory_map_sources import mosaic
from abbey_support import station_footprints
from prepare_east_channelsea_context import (ROOT,REGISTER,BASELINE,load,digest,
    apply_water_context,apply_road_context,prior_rivers,blue_boundary)


def check(preflight=False):
    register=load(REGISTER);before=load(BASELINE)
    assert digest(before)==register['baselineSha256']
    assert digest(before['groundRivers'])==register['retainedRiverGeometrySha256']['ground']
    assert digest(before['westRivers'])==register['retainedRiverGeometrySha256']['west']
    ground=dict(rivers=copy.deepcopy(before['groundRivers']))
    apply_water_context(ground,register)
    expected=copy.deepcopy(ground)
    apply_water_context(ground,register)
    assert ground==expected, 'Water application is not idempotent'
    assert prior_rivers(ground['rivers'],register)==before['groundRivers']
    for correction in register['bankCorrections']:
        old=Polygon(correction['priorRing'])
        actual=next(r for r in ground['rivers'] if r['id']==correction['riverId'])
        ring=actual['polygons'][correction['polygonIndex']][correction['ringIndex']]
        p=Polygon(ring)
        assert p.is_valid and len(ring)==len(correction['priorRing'])
        assert set(q['vertex'] for q in correction['replacements'])=={5,6,7,8,25,26,27,28,29,30,31,32,34,35,36}
        replacements={q['vertex']:q for q in correction['replacements']}
        for index,q in enumerate(ring):
            assert q==(replacements[index]['point'] if index in replacements else correction['priorRing'][index])
        assert ring[40:]==correction['priorRing'][40:]
        assert ring[:5]==correction['priorRing'][:5]
        assert abs(p.area-correction['areaM2'])<.000001
        assert abs(old.area-correction['priorAreaM2'])<.000001
        assert p.difference(old).area<.01
        for replacement in correction['replacements']:
            _,world,_=mosaic(replacement['reviewedSourceBounds'])
            assert world(replacement['reviewedSourcePixels']).round(3).tolist()[0]==replacement['point']
    for river in register['additionalRivers']:
        canvas,world,_=mosaic(river['reviewedSourceBounds'])
        assert blue_boundary(canvas,river['bluePaintCrop'])==river['reviewedSourcePixels']
        ring=world(river['reviewedSourcePixels']).round(3).tolist()
        assert river['polygons']==[[ring]]
        assert Polygon(ring).is_valid and Polygon(ring).area>100
        assert abs(Polygon(ring).area-river['areaM2'])<.000001
    water=unary_union([Polygon(p[0],p[1:]) for r in ground['rivers']+before['westRivers'] for p in r['polygons']])
    additions=[Polygon(r['polygons'][0][0]) for r in register['additionalRivers']]
    for index,p in enumerate(additions):
        assert all(p.distance(q)>.5 for q in additions[:index])
    sources=load('reference/footprint-model-alignment/east-channelsea-source-shapes.json')
    for correction in register['bankCorrections']:
        for row in correction['sourceRoofWaterAreasM2']:
            body=shape(sources[str(row['sourceFid'])])
            old=Polygon(correction['priorRing']).buffer(.12)
            actual=Polygon(next(r for r in ground['rivers'] if r['id']==correction['riverId'])['polygons'][0][0]).buffer(.12)
            assert abs(body.intersection(old).area-row['priorArea'])<.000001
            assert abs(body.intersection(actual).area-row['area'])<.000001
            assert row['priorArea']>0 and row['area']<.001
    # The independent source wall discrepancy at Brush is recorded, but is not
    # used to waive authored model/water checks below.
    assert {q['sourceFid'] for q in register['sourceWaterAlignmentLimits']}=={6805}
    assert all(q['riverId']==1302 and q['overlapAreaM2']<2 for q in register['sourceWaterAlignmentLimits'])
    road=register['road']['preparedRoad'];line=LineString(road['points'])
    assert road['width']==6 and not road['bridgeSpans']
    assert road['points'][0]==register['road']['priorRoute'][0]
    _,world,pixel=mosaic(register['road']['reviewedSourceBounds'])
    assert road['points'][1:]==world(register['road']['reviewedSourcePixels']).round(3).tolist()[1:]
    assert road['sourcePixels']==pixel(road['points']).round(3).tolist()
    assert line.intersection(water).length<.001
    assert len(road['points'])==14
    for fid in ['159','1640','7552','22943','370011','35379']:
        assert shape(sources[fid]).intersection(line.buffer(4.1,cap_style=2,join_style=2)).area<.01, fid
    district=copy.deepcopy(before['districtRoads'])
    apply_road_context(district,register)
    saved=copy.deepcopy(district);apply_road_context(district,register)
    assert saved==district
    assert [r for r in district['roads'] if r['name']!=road['name']]==before['districtRoads']['roads']
    assert len(register['additionalYards'])==3
    assert {y['id'] for y in register['additionalYards']}=={9008,13011,13013}
    depot=Polygon(next(y for y in register['additionalYards'] if y['id']==13011)['polygons'][0][0])
    for yard in register['additionalYards']:
        _,world,_=mosaic(yard['reviewedSourceBounds'])
        assert yard['polygons']==[[world(yard['reviewedSourcePixels']).round(3).tolist()]]
        assert Polygon(yard['polygons'][0][0]).is_valid and not yard['allowStock']
    assert len(register['railSidings'])==11
    for track in register['railSidings']:
        t=LineString(track['points'])
        assert t.length>100 and t.difference(depot.buffer(3)).length<.01
        assert t.intersection(water.buffer(1.2)).length<.001
        for fid in ['79','2832']:
            assert t.buffer(1.2).intersection(shape(sources[fid])).area<.01,(track['id'],fid)
    rail=register['railCorrection']
    assert {c['name'] for c in register['roadCorrections']}=={'Bridge Road','Barnby Street','St Thomas Road','Hotham Street','Randal Street','Canning Street','Leywick Street','Morley Street'}
    bridge_correction=register['roadCorrections'][0]
    assert bridge_correction['name']=='Bridge Road' and bridge_correction['path']=='data/maps/housing-road-traces.json'
    assert load(bridge_correction['baseline'])==bridge_correction['priorRecord']
    assert digest(bridge_correction['priorRecord'])==bridge_correction['baselineSha256']
    bridge_record=bridge_correction['record']
    assert bridge_record['width']==bridge_correction['priorRecord']['width']==8
    _,bridge_world,_=mosaic(bridge_correction['reviewedSourceBounds'])
    assert bridge_record['points']==bridge_world(bridge_correction['reviewedSourcePixels']).round(3).tolist()
    bridge_road=LineString(bridge_record['points']).buffer(5.1,cap_style=2,join_style=2)
    for correction in register['roadCorrections'][1:]:
        assert correction['priorRecord'] in load(correction['baseline'])
        assert correction['record']['width']==correction['priorRecord']['width']
        indices=correction['changedControlIndices']
        assert indices==([0,1,2] if correction['name'] in {'Barnby Street','Morley Street'} else [3,4,5,6] if correction['name']=='St Thomas Road' else [0])
        assert all(q==correction['priorRoute'][index] for index,q in enumerate(correction['record']['points']) if index not in indices)
        if indices==[0]:
            assert LineString(bridge_record['points']).distance(Point(correction['record']['points'][0]))<.001
    for track in register['railSidings'][-4:]:
        assert LineString(track['points']).buffer(1.4).intersection(bridge_road).area<.01,track['id']
    assert load(rail['baseline'])==rail['priorRecord']
    assert digest(rail['priorRecord'])==rail['baselineSha256']
    prior_record=rail['priorRecord'];revised_record=rail['record']
    assert revised_record['route'][:12]==prior_record['route'][:12]
    assert revised_record['route'][19:]==prior_record['route'][19:]
    assert {k:v for k,v in revised_record.items() if k not in ['route','eastChannelseaRailAlignment','stationFormationReview']}=={k:v for k,v in prior_record.items() if k!='route'}
    assert [q['index'] for q in rail['replacements']]==[12,13,14,15,16,17,18]
    for replacement in rail['replacements']:
        _,world,_=mosaic(replacement['reviewedSourceBounds'])
        assert replacement['point']==world(replacement['reviewedSourcePixels']).round(3).tolist()[0]
        assert revised_record['route'][replacement['index']]==replacement['point']
        assert prior_record['route'][replacement['index']]==replacement['priorPoint']
    main=LineString(next(r for r in before['railways'] if r['name']=='Great Eastern Railway — main line')['route'])
    join=revised_record['mainlineJoinChainage']
    a,b=main.interpolate(join-.5),main.interpolate(join+.5)
    tangent=np.array([b.x-a.x,b.y-a.y]);tangent/=np.linalg.norm(tangent)
    points=np.asarray(revised_record['route'])
    tail=np.array([140.62,-272.37])-points[-1];tail/=np.linalg.norm(tail)
    distances=np.r_[0,np.cumsum(np.linalg.norm(np.diff(points,axis=0),axis=1))]
    spline=CubicSpline(distances,points,bc_type=((1,tangent),(1,tail)),axis=0)
    rail_line=LineString(spline(np.linspace(0,distances[-1],math.ceil(distances[-1]/2)+1)))
    assert rail_line.distance(shape(sources['79']))>revised_record['crestHalfWidth']+.15
    rail_crest=rail_line.buffer(revised_record['crestHalfWidth'],cap_style=2,join_style=2)
    for building in load('docs/data/factory-buildings.json')['buildings']:
        body=Polygon(building['footprint'],building.get('worldHoles',[]))
        assert body.intersection(rail_crest).area<.01,building['id']
    plan=load('docs/data/ground-plan.json');factories=load('docs/data/factory-buildings.json')
    southwest=load('docs/data/southwest-context.json');surveyed={s['id'] for s in factories['sites']}
    legacy=[b for b in plan['factoryStudies']+plan['neighbourhood']['mappedFactories']+southwest['industrialRanges'] if b.get('siteId') not in surveyed]
    legacy+=load('docs/data/housing-detail.json')['rows']+plan['neighbourhood']['houses']+[plan['neighbourhood']['mill']]
    legacy_polygons=[]
    for building in legacy:
        rectangle=affinity.translate(affinity.rotate(box(-building['width']/2,-building['depth']/2,building['width']/2,building['depth']/2),-building.get('rotation',0)),building['x'],building['z']).buffer(.3)
        assert rectangle.intersection(rail_crest).area<.01,building.get('id',building.get('name'))
        legacy_polygons.append(rectangle)
    full_building_mask=unary_union(legacy_polygons+[Polygon(p['outer'],p['holes']).buffer(.15) for b in factories['buildings'] for p in b['renderPolygons']])
    full_building_mask=full_building_mask.union(station_footprints(load('docs/data/abbey-station-plan.json')).buffer(.15))
    assert full_building_mask.intersection(rail_crest).area<.01
    roofs_checked=set()
    for name in ['east-channelsea-north','east-channelsea-upper','east-channelsea-south']:
        path=ROOT/f'data/maps/{name}-footprint-alignment.json'
        if not path.exists():
            continue
        model_register=json.loads(path.read_text())
        for key in ['buildings','mapTracedBuildings','additionalBuildings']:
            for row in model_register.get(key,[]):
                if not row.get('worldFootprint'):
                    continue
                body=Polygon(row['worldFootprint'],row.get('worldHoles',[]))
                assert body.intersection(water.buffer(.12)).area<.01,row.get('modelId')
                assert body.intersection(line.buffer(4.1,cap_style=2,join_style=2)).area<.01,row.get('modelId')
                roofs_checked.add(row.get('modelId',row.get('id')) or tuple(map(tuple,row['worldFootprint'])))
    if not preflight:
        built_ground=load('docs/data/ground-plan.json')
        assert built_ground['rivers']==ground['rivers']
        scene=load('docs/data/factory-buildings.json')
        assert scene['westContext']['rivers']==before['westRivers']
        infra=load('docs/data/infrastructure.json')
        built=next(r for r in infra['roads'] if r['name']==road['name'])
        assert built['width']==6 and len(built['route'])==len(road['points'])
        assert all(math.dist(a,b)<.008 for a,b in zip(built['route'],road['points']))
        old_rails={r['name']:r for r in before['railways']}
        new_rails=[r for r in infra['railways'] if r.get('id')=='north-london-connection']
        assert len(new_rails)<=1
        assert len(infra['railways'])==len(before['railways'])+len(new_rails)
        for built_rail in infra['railways']:
            if built_rail.get('id')=='woolwich-northern-connection':
                assert load(rail['path'])==revised_record
                sampled_route=[[rail_line.interpolate(d).x,rail_line.interpolate(d).y] for d in np.linspace(0,rail_line.length,math.ceil(rail_line.length/2)+1)]
                assert built_rail['route']==sampled_route
                assert all(built_rail[k]==revised_record[k] for k in ['tracks','trackSpacing','gauge','crestHalfWidth','baseHalfWidth','formationHeight','joinHeight'])
            elif built_rail.get('id')=='north-london-connection':
                northern_register=load('data/maps/north-london-connection.json')
                assert northern_register['id']==built_rail['id']
                assert northern_register['railFeatureIds']==['way/198582978','way/198582965','way/198582968']
                assert built_rail['detailedRailway'] is True
                assert built_rail['railFeatureIds']==northern_register['railFeatureIds']
            elif built_rail.get('detailedMainline') and built_rail.get('mainlineExtension'):
                northern_register=load('data/maps/north-london-connection.json')
                extension=built_rail['mainlineExtension'];prior_extension=northern_register['mainlineExtension']
                assert extension['railFeatureId']==prior_extension['railFeatureId']=='way/198781682'
                assert prior_extension['priorRoute']==old_rails[built_rail['name']]['route']
                assert extension['priorRoute']==prior_extension['priorRoute']
                assert extension['priorStations']==prior_extension['priorStations']
                assert built_rail['route']==prior_extension['priorRoute']+extension['addedRoute']
                assert built_rail['stations']==prior_extension['priorStations']+extension['addedStations']
                assert 60<extension['extensionLength']<100
                assert built_rail['tracks']==old_rails[built_rail['name']]['tracks']
            else:
                assert {k:built_rail[k] for k in ['name','route','tracks'] if k in built_rail}==old_rails[built_rail['name']]
        old_roads={r['name']:r for r in before['builtRoads']}
        corrected_roads={c['name']:c for c in register['roadCorrections']}
        for built_road in infra['roads']:
            if built_road['name'] in corrected_roads:
                correction=corrected_roads[built_road['name']]
                assert len(built_road['route'])==len(correction['record']['points'])
                assert all(math.dist(a,b)<.008 for a,b in zip(built_road['route'],correction['record']['points']))
                assert built_road['width']==correction['record']['width']
                assert next(r for r in load(correction['path'])['roads'] if r['name']==correction['name'])==correction['record']
            elif built_road['name']!=road['name']:
                assert built_road['route']==old_roads[built_road['name']]['route'],built_road['name']
        yards=load('docs/data/factory-yards.json')
        for ident in [9008,13011,13013]:
            assert next(y for y in yards['sites'] if y['id']==ident)['areaM2']>500
        tracks=[t for t in yards['tracks'] if t.get('siteId')==13011]
        assert len(tracks)>=6
    assert all((ROOT/path).exists() for path in register['evidenceImages'])
    print(f'East Channelsea context: mapped lane and entrance, 15 bounded bank controls, 3 separate OS water bodies, 3 yards and 11 depot sidings pass; {len(roofs_checked)} authored roofs clear water/road; 7 station/Market rail controls clear all factory roofs with existing profile and joins retained.')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--preflight',action='store_true')
    check(parser.parse_args().preflight)
