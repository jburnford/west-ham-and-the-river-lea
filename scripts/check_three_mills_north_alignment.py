"""Check northern Three Mills matches, provisional shed, mapped plant and passage."""
import json
import math
from pathlib import Path
from shapely import affinity
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union
from factory_map_sources import mosaic
from factory_street_clearance import street_clearances

ROOT = Path(__file__).resolve().parents[1]
load = lambda p:json.loads((ROOT/p).read_text())
r = load('data/maps/three-mills-north-footprint-alignment.json')
s = load('docs/data/factory-buildings.json')
models = {b['id']:b for b in s['buildings']}
cs = {b['modelId']:b for b in r['buildings']}
assert len(cs)==20 and len(r['groups'])==15 and len(r['additionalBuildings'])==1
ids=set(cs)|{c['modelId'] for c in r['mapTracedBuildings']+r['locallyTransferredBuildings']}
assert len(ids)==22
assert len([b for b in s['buildings'] if b['siteId']==419])==38
registers = [load('data/maps/factory-footprint-alignment.json')]+[load(p) for p in s['footprintAlignment']['groupRegisters']]
used = set()
for register in registers:
    if register==r:continue
    for g in register.get('groups',register['buildings']):used.update(g.get('sourceFids',[g.get('sourceFid')]))
results = []
for g in r['groups']:
    assert not used.intersection(g['sourceFids']),g['id']
    used.update(g['sourceFids'])
    source = unary_union([Polygon(p[0],p[1:]) for p in g['sourcePolygons']])
    target = unary_union([Polygon(cs[id]['worldFootprint'],cs[id]['worldHoles']) for id in g['modelIds']])
    actual = unary_union([Polygon(p['outer'],p['holes']) for id in g['modelIds'] for p in models[id]['renderPolygons']])
    assert target.symmetric_difference(source).area<.05,g['id']
    assert actual.symmetric_difference(target).area<.02,g['id']
    score = actual.intersection(source).area/actual.union(source).area
    assert score>.9995
    if not g['additional']:assert score>g['previousUnionIoU'],g['id']
    for id in g['modelIds']:
        b,c = models[id],cs[id]
        assert b['footprintGroup']==g['id'] and b['sourceFootprintFids']==g['sourceFids']
        for key,saved in [('height','preservedHeight'),('roofRise','preservedRoofRise'),('roofAxis','preservedRoofAxis'),('roofBays','preservedRoofBays')]:assert b[key]==c[saved]
        assert abs(b['rotation']-c['footprintRotationDegrees'])<.0001
    results.append(dict(id=g['id'],previousIoU=g['previousUnionIoU'],sourceIoU=score))
assert len(r['mapTracedBuildings'])==1
c = r['mapTracedBuildings'][0]
_,world,_ = mosaic(c['mosaicBounds'])
reference = Polygon(world(c['mosaicPixels']))
b = models[c['modelId']]
actual = unary_union([Polygon(p['outer'],p['holes']) for p in b['renderPolygons']])
assert reference.symmetric_difference(actual).area<.05
assert b['footprintSource']=='os-1893-direct-trace' and 'sourceFootprintFids' not in b
for key,saved in [('height','eavesHeight'),('roofRise','roofRise'),('roofAxis','roofAxis'),('roofBays','roofBays')]:assert b[key]==c[saved]
c=r['locallyTransferredBuildings'][0]
b=models[c['modelId']]
assert b['footprintSource']=='goad-f17-local-transfer' and 'sourceFootprintFids' not in b
assert b['goadCentrePixels']==[1221,2459]
raw=load('data/maps/factory-building-traces.json')
a,bcoef,tx,tz=raw['sources']['goad-f17']['pixelToWorld']
goad=lambda x,y:Point(a*x-bcoef*y+tx,bcoef*x+a*y+tz)
offsets=[]
for n,fid in zip(range(1,6),c['registrationSourceFids']):
    group=next(g for g in r['groups'] if g['sourceFids']==[fid])
    source=Polygon(group['sourcePolygons'][0][0]).centroid
    row=next(q for q in raw['buildings'] if q['id']==f'site419-range-{n}')
    mapped=goad(*row['rectPixels'][:2])
    offsets.append((source.x-mapped.x,source.y-mapped.y))
mapped=goad(*c['goadCentrePixels'])
expected=Point(mapped.x+sum(q[0] for q in offsets)/5,mapped.y+sum(q[1] for q in offsets)/5)
assert Polygon(b['footprint']).centroid.distance(expected)<.001
assert abs(Polygon(b['footprint']).area-Polygon(c['priorFootprint']).area)<.01
for key,saved in [('height','eavesHeight'),('roofRise','roofRise'),('roofAxis','roofAxis'),('roofBays','roofBays')]:assert b[key]==c[saved]
roads=load('data/maps/district-road-traces.json')['roads']
lane=next(q for q in roads if q['name']=='Three Mills Lane')
entrance=next(q for q in roads if q['name']=='Three Mills entrance')
passage=next(q for q in roads if q['name']=='Three Mills distillery passage')
prior_lane = lane.get('threeMillsLandmarkAlignment', {}).get('points', lane['points'])
assert prior_lane==lane['threeMillsNorthAlignment']['priorPoints'][:10] and lane['width']==7
assert passage['points'][0]==lane['points'][-1] and passage['points'][-1]==entrance['points'][0]
assert passage['width']==entrance['width']==5.2 and len(lane['bridgeSpans'])==1
streets,frontage_streets=street_clearances(roads)
plan=load('docs/data/ground-plan.json')
water=unary_union([Polygon(p[0],p[1:]) for q in plan['rivers']+s['westContext']['rivers'] for p in q['polygons']])
body=unary_union([Polygon(models[id]['footprint'],models[id].get('worldHoles',[])) for id in ids])
assert body.intersection(water.buffer(.12)).area<.01
for id in ids:
    p=Polygon(models[id]['footprint'],models[id].get('worldHoles',[]))
    assert p.intersection(frontage_streets.get(id,streets)).area<.01,id
    actual=unary_union([Polygon(q['outer'],q['holes']) for q in models[id]['renderPolygons']])
    assert p.symmetric_difference(actual).area<.03,id
    for b in s['buildings']:
        if b['id']!=id:assert p.intersection(Polygon(b['footprint'],b.get('worldHoles',[]))).area<.04,(id,b['id'])
oldroad=unary_union([LineString(q['threeMillsNorthAlignment']['priorPoints']).buffer(q['threeMillsNorthAlignment']['priorWidth']/2+1.1) for q in [lane,entrance]])
assert body.intersection(oldroad).area>250
c=r['structures'][0]
stack=next(t for t in s['structures'] if t['id']==c['id'])
assert stack['height']==c['preservedHeight']==31 and stack['radius']==1.5
assert stack['sourceFootprintFid']==892638
assert Point(stack['x'],stack['z']).distance(Point(c['centre']))<.001
base=unary_union([Polygon(p[0],p[1:]) for p in c['sourcePolygons']])
plinth=Point(stack['x'],stack['z']).buffer(stack['radius']*1.2)
assert plinth.difference(base).area<.001
assert plinth.intersection(body).area<.001 and plinth.intersection(streets).area<.001
assert len(r['tanks'])==2
for c in r['tanks']:
    tank=next(t for t in s['structures'] if t['id']==c['id'])
    base=unary_union([Polygon(p[0],p[1:]) for p in c['sourcePolygons']])
    assert tank['height']==c['priorStructure']['height']==6
    assert Point(tank['x'],tank['z']).distance(base.centroid)<.001
    assert abs(math.pi*tank['equalAreaRadius']**2-base.area)<.025
    assert 0<base.centroid.distance(base.boundary)-tank['radius']<.001
    circle=Point(tank['x'],tank['z']).buffer(tank['radius'])
    assert circle.difference(base).area<.001
    assert circle.intersection(body).area<.01 and circle.intersection(streets).area<.01 and circle.intersection(water).area<.01
a,b=r['tanks']
assert Point(a['x'],a['z']).distance(Point(b['x'],b['z']))>a['radius']+b['radius']+.1
# Preserve untouched ranges, allowing the separately checked southern and landmark continuations.
south_path = ROOT/'data/maps/three-mills-south-footprint-alignment.json'
south_ids = {c['modelId'] for c in load(south_path)['buildings']} if south_path.exists() else set()
landmark_path=ROOT/'data/maps/three-mills-landmark-footprint-alignment.json'
if landmark_path.exists():south_ids.update(c['modelId'] for c in load(landmark_path)['buildings'])
before_path=ROOT/'reference/footprint-model-alignment/three-mills-before.json'
if before_path.exists():
    before=load(before_path)
    for b in before['buildings']:
        if b['id'] not in ids|south_ids:
            old=unary_union([Polygon(p['outer'],p['holes']) for p in b['renderPolygons']])
            current=unary_union([Polygon(p['outer'],p['holes']) for p in models[b['id']]['renderPolygons']])
            assert old.symmetric_difference(current).area<.01,b['id']
(ROOT/'reference/footprint-model-alignment/verified-three-mills-north.json').write_text(json.dumps(results,indent=2)+'\n')
print('Three Mills north: 20 linked ranges, direct trace, provisional shed, mapped chimney/tanks and clear works passage pass; other previously reviewed ranges retained.')
