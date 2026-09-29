"""Check reviewed western compounds, duplicate removal, channel and road access."""
import json
import math
from pathlib import Path
from shapely import affinity
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union

ROOT=Path(__file__).resolve().parents[1]
load=lambda p:json.loads((ROOT/p).read_text())
r=load('data/maps/west-sugar-footprint-alignment.json')
scene=load('docs/data/factory-buildings.json')
models={b['id']:b for b in scene['buildings']}
corrections={b['modelId']:b for b in r['buildings']}
assert len(corrections)==38 and len(r['groups'])==34
assert len(r['additionalBuildings'])==11
assert set(corrections)=={b['id'] for b in scene['buildings'] if b['siteId']==947}
assert {b['id'] for b in r['removedBuildings']}=={'site569-range-1','site569-range-4'}
assert not set(models).intersection(b['id'] for b in r['removedBuildings'])
assert {b['id'] for b in scene['buildings'] if b['siteId']==569}=={'site569-range-2','site569-range-3'}
registers=[load('data/maps/factory-footprint-alignment.json')]+[load(p) for p in scene['footprintAlignment']['groupRegisters']]
assert sum(len(q['buildings']) for q in registers)==scene['footprintAlignment']['matchedRanges']
used=set()
for register in registers:
    if register==r:continue
    for group in register.get('groups',register['buildings']):
        used.update(group.get('sourceFids',[group.get('sourceFid')]))
results=[]
for group in r['groups']:
    assert not used.intersection(group['sourceFids']),group['id']
    used.update(group['sourceFids'])
    source=unary_union([Polygon(p[0],p[1:]) for p in group['sourcePolygons']])
    targets=[];actuals=[]
    for id in group['modelIds']:
        c,b=corrections[id],models[id]
        target=Polygon(c['worldFootprint'],c['worldHoles'])
        actual=unary_union([Polygon(p['outer'],p['holes']) for p in b['renderPolygons']])
        assert b['footprintGroup']==group['id'] and b['sourceFootprintFids']==group['sourceFids']
        assert Polygon(b['footprint'],b['worldHoles']).symmetric_difference(target).area<.001
        assert all(target.intersection(p).area<.01 for p in targets),(id,'compartment overlap')
        for key,saved in [('height','preservedHeight'),('roofRise','preservedRoofRise'),('roofBays','preservedRoofBays'),('roofAxis','preservedRoofAxis')]:
            assert b[key]==c[saved],(id,key)
        assert abs(b['rotation']-c['footprintRotationDegrees'])<.0001
        targets.append(target);actuals.append(actual)
    target,actual=map(unary_union,[targets,actuals])
    assert target.symmetric_difference(source).area<.15,group['id']
    allowed=unary_union([Polygon(models[id]['footprint'],models[id].get('worldHoles',[]))
        for seam in r['boundaryOverlapReviews'] if set(group['modelIds']).intersection(seam['models'])
        for id in seam['models'] if id not in group['modelIds']])
    assert target.difference(actual).difference(allowed.buffer(.002)).area<.08,(group['id'],'unreviewed clipping')
    agreement=actual.intersection(source).area/actual.union(source).area
    assert agreement>.998,(group['id'],agreement)
    assert group['additional'] or agreement>group['previousUnionIoU']
    results.append(dict(id=group['id'],renderedIoU=agreement))

plan=load('docs/data/ground-plan.json')
water=unary_union([Polygon(p[0],p[1:]) for river in plan['rivers']+scene['westContext']['rivers'] for p in river['polygons']])
roads=load('data/maps/district-road-traces.json')['roads']
from factory_street_clearance import street_clearances
streets,frontage_streets=street_clearances(roads)
for id in corrections:
    p=Polygon(models[id]['footprint'],models[id]['worldHoles'])
    assert p.intersection(water.buffer(.12)).area<.01,(id,'water')
    overlap=p.intersection(frontage_streets.get(id,streets)).area
    if id==r['roadBoundaryReview']['modelId']:
        assert abs(overlap-r['roadBoundaryReview']['sourceOverlapAreaM2'])<.002
    else:
        assert overlap<.01,(id,'street')
bank=load('data/maps/west-sugar-bank-alignment.json')
river=next(q for q in plan['rivers'] if q['id']==bank['riverId'])
ring=river['polygons'][bank['polygonIndex']][bank['ringIndex']]
assert Polygon(ring).is_valid
for change in bank['replacements']:
    assert ring[change['vertex']]==change['point']
assert {c['vertex'] for c in bank['replacements']}=={39,40,41,42,49,50,51,52,53,54}
assert LineString(ring[38:46]).distance(LineString(ring[47:56]))>2,'Channel pinched shut'
lane=next(q for q in roads if q['name']=='Sugar House Lane')
assert lane['points'][:2]==lane['westSugarAlignment']['priorPoints'][:2]
assert lane['williamsAsphalteAlignment']['priorPoints'][-7:-1]==lane['westSugarAlignment']['priorPoints'][-7:-1]
assert lane['lascellesUltramarineAlignment']['priorPoints'][-1]==lane['westSugarAlignment']['priorPoints'][-1]
assert lane['width']==5.2 and lane['westSugarAlignment']['priorWidth']==7
passage=next(q for q in roads if q['name']=='Sugar House Lane works passage')
assert LineString(lane['points']).distance(Point(passage['points'][0]))<.002
for c in r['structures']:
    s=next(s for s in scene['structures'] if s['id']==c['id'])
    assert Point(s['x'],s['z']).distance(Point(c['centre']))<.001
    assert s['height']==c['preservedHeight']
    if 'sourceFid' in c:
        base=unary_union([Polygon(p[0],p[1:]) for p in c['sourcePolygons']])
        half=s['radius']*1.2/math.sqrt(2)
        plinth=affinity.translate(affinity.rotate(box(-half,-half,half,half),s['rotation']),s['x'],s['z'])
        assert plinth.difference(base).area<.02,(s['id'],'plinth exceeds mapped base')
    else:
        parent=Polygon(models['site947-range-18']['footprint'])
        assert parent.contains(Point(s['x'],s['z']))
yard=next(y for y in load('docs/data/factory-yards.json')['sites'] if y['id']==r['yard']['id'])
surface=unary_union([Polygon(p[0],p[1:]) for p in yard['polygons']])
envelope=unary_union([Polygon(p[0],p[1:]) for p in r['yard']['polygons']])
assert surface.difference(envelope).area<.001 and surface.area>2000
assert all(surface.covers(Point(p)) for p in [(-752,11),(-778,31),(-737,93)])
assert not yard['stock'],'No unsupported equipment/stock inferred in the restored western yard'
(ROOT/'reference/footprint-model-alignment/verified-west-sugar.json').write_text(json.dumps(results,indent=2)+'\n')
print(f'West Sugar House: 38 ranges, 34 groups, 11 additions, two duplicates removed and four chimneys; clear channel/roads; minimum rendered group agreement {min(v["renderedIoU"] for v in results):.3%}.')
