"""Audit the Oil Wharf buildings, five tanks and open working yard."""
import json
import math
from pathlib import Path
from shapely.geometry import Polygon, Point, LineString
from shapely.ops import unary_union

ROOT=Path(__file__).resolve().parents[1]
load=lambda p:json.loads((ROOT/p).read_text())
r=load('data/maps/oil-wharf-footprint-alignment.json');scene=load('docs/data/factory-buildings.json')
models={b['id']:b for b in scene['buildings']};corrections={b['modelId']:b for b in r['buildings']}
assert len(corrections)==9 and len(r['additionalBuildings'])==4
assert {b['id'] for b in scene['buildings'] if b['siteId']==9001}==set(corrections)|{'oilwharf-2'}
assert not {b['id'] for b in r['removedBuildings']}.intersection(models)
assert {b['id'] for b in r['removedBuildings']}.issubset({b.get('id') for b in scene['reclassifiedFeatures']})
registers=[load('data/maps/factory-footprint-alignment.json')]+[load(p) for p in scene['footprintAlignment']['groupRegisters']]
assert sum(len(q['buildings']) for q in registers)==scene['footprintAlignment']['matchedRanges']
assert scene['footprintAlignment']['matchedRanges']>=62
used=set();results=[]
for q in registers:
    if q==r:continue
    for g in q.get('groups',q['buildings']):used.update(g.get('sourceFids',[g.get('sourceFid')]))
for group in r['groups']:
    id=group['modelIds'][0];b=models[id];c=corrections[id]
    assert not used.intersection(group['sourceFids']),id
    used.update(group['sourceFids'])
    source=unary_union([Polygon(p[0],p[1:]) for p in group['sourcePolygons']])
    actual=unary_union([Polygon(p['outer'],p['holes']) for p in b['renderPolygons']])
    target=Polygon(c['worldFootprint'],c['worldHoles'])
    assert source.is_valid and actual.is_valid and target.symmetric_difference(source).area<.08,id
    allowed=unary_union([Polygon(models[other]['footprint']) for seam in r['boundaryOverlapReviews']
                        if id in seam['models'] for other in seam['models'] if other!=id])
    assert actual.difference(target).area<.02 and target.difference(actual).difference(allowed.buffer(.001)).area<.08,id
    iou=actual.intersection(source).area/actual.union(source).area
    assert iou>.998,id
    if not group['newModel']:
        old=Polygon(c['priorFootprint']);before=old.intersection(source).area/old.union(source).area
        assert iou>before and math.isclose(before,group['previousUnionIoU'],abs_tol=.0001),id
    for key,saved in [('height','preservedHeight'),('roofRise','preservedRoofRise'),('roofBays','preservedRoofBays'),('roofAxis','preservedRoofAxis')]:
        assert b[key]==c[saved],(id,key)
    results.append({'id':id,'renderedIoU':iou,'newModel':group['newModel']})
for seam in r['boundaryOverlapReviews']:
    a,b=[Polygon(models[id]['footprint']) for id in seam['models']]
    assert math.isclose(a.intersection(b).area,seam['sourceOverlapAreaM2'],abs_tol=.001)
plan=load('docs/data/ground-plan.json');infra=load('docs/data/infrastructure.json')
water=unary_union([Polygon(p[0],p[1:]) for river in plan['rivers']+scene['westContext']['rivers'] for p in river['polygons']])
buildings=unary_union([Polygon(p['outer'],p['holes']) for b in scene['buildings'] for p in b['renderPolygons']])
roads=unary_union([Polygon(t) for key in ['roadTriangles','pathTriangles','shoulderTriangles'] for t in infra[key]])
tanks=[s for s in scene['structures'] if s['siteId']==9001 and s['kind']=='tank']
assert len(tanks)==5 and sum(t['status']=='disused' for t in tanks)==1
envelope=Polygon(r['yard']['polygons'][0][0])
for i,t in enumerate(tanks):
    circle=Point(t['x'],t['z']).buffer(t['radius'],quad_segs=64)
    assert circle.intersection(unary_union([buildings,water,roads])).area<.01,(t['id'],'tank obstruction')
    assert envelope.covers(circle.buffer(1)),(t['id'],'working envelope cuts tank surround')
    for other in tanks[:i]:
        assert math.dist([t['x'],t['z']],[other['x'],other['z']])>t['radius']+other['radius'],(t['id'],other['id'])
    if 'sourceFootprintFid' in t:
        source=unary_union([Polygon(p[0],p[1:]) for p in t['sourcePolygons']])
        assert Point(t['x'],t['z']).distance(source.centroid)<.001
        assert abs(math.pi*t['radius']**2-source.area)<.03
    else:
        assert t['mosaicPixels'] and t['registrationOffset'] and 'sourceFootprintFid' not in t
    assert t['height']==4
    if t['priorStructure']:assert t['height']==t['priorStructure']['height']
assert buildings.distance(Point(-1176,-65))>8,'Open barrel yard still filled by a building'
yards=load('docs/data/factory-yards.json');yard=next(s for s in yards['sites'] if s['id']==9001)
surface=unary_union([Polygon(p[0],p[1:]) for p in yard['polygons']])
assert surface.covers(Point(-1176,-65)) and len(yard['stock'])>0
assert all(s['kind']=='barrels' for s in yard['stock'])
road_bodies=unary_union([Polygon(t) for t in infra['roadTriangles']])
assert surface.intersection(buildings.union(water).union(road_bodies)).area<.05
for t in tanks:assert surface.intersection(Point(t['x'],t['z']).buffer(t['radius'])).area<.01
for route in yard['wearRoutes']:assert surface.buffer(.03).covers(LineString(route))
(ROOT/'reference/footprint-model-alignment/verified-oil-wharf.json').write_text(json.dumps(results,indent=2)+'\n')
print(f'Oil Wharf: 10 source-linked ranges, 5 clear tanks, open barrel yard; minimum new group agreement {min(x["renderedIoU"] for x in results):.3%}.')
