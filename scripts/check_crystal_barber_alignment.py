"""Audit Crystal Wharf open ground, Barber rooms, inherited roofs and chimneys."""
import json
import math
from pathlib import Path
from shapely import affinity
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union

ROOT=Path(__file__).resolve().parents[1]
load=lambda p:json.loads((ROOT/p).read_text())
r=load('data/maps/crystal-barber-footprint-alignment.json')
scene=load('docs/data/factory-buildings.json')
models={b['id']:b for b in scene['buildings']}
corrections={b['modelId']:b for b in r['buildings']}
assert len(corrections)==len(r['groups'])==21
assert len(r['additionalBuildings'])==13
removed={b['id'] for b in r['removedBuildings']}
assert removed=={f'site964-range-{n}' for n in [24,25,26,27]}
assert not removed.intersection(models)
assert set(r['supersedesDeferred'])=={f'site964-range-{n}' for n in range(17,29)}
assert set(r['supersedesDeferred'])-removed <= set(corrections)
registers=[load('data/maps/factory-footprint-alignment.json')]+[load(p) for p in scene['footprintAlignment']['groupRegisters']]
assert sum(len(q['buildings']) for q in registers)==scene['footprintAlignment']['matchedRanges']
aligned={b['modelId'] for q in registers for b in q['buildings']}
site_ids={b['id'] for b in scene['buildings'] if b['siteId']==964 and '-infill-' not in b['id']}  # task F infill ranges are core-infill-footprint-alignment.json's
assert len(site_ids)==40 and site_ids<=aligned
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
    id=group['modelIds'][0];c,b=corrections[id],models[id]
    target=Polygon(c['worldFootprint'],c['worldHoles'])
    actual=unary_union([Polygon(p['outer'],p['holes']) for p in b['renderPolygons']])
    assert b['footprintGroup']==group['id'] and b['sourceFootprintFids']==group['sourceFids']
    assert Polygon(b['footprint'],b['worldHoles']).symmetric_difference(target).area<.001
    assert target.symmetric_difference(source).area<.1,(id,'source mismatch')
    assert actual.symmetric_difference(target).area<.01,(id,'unexpected clipping')
    for key,saved in [('height','preservedHeight'),('roofRise','preservedRoofRise'),('roofBays','preservedRoofBays'),('roofAxis','preservedRoofAxis')]:
        assert b[key]==c[saved],(id,key)
    assert abs(b['rotation']-c['footprintRotationDegrees'])<.0001
    assert b['heightEvidence'] and b['roofEvidence']
    agreement=actual.intersection(source).area/actual.union(source).area
    assert agreement>.9995 and (group['additional'] or agreement>group['previousUnionIoU']),(id,agreement)
    results.append(dict(id=group['id'],previousIoU=group['previousUnionIoU'],renderedIoU=agreement))

plan=load('docs/data/ground-plan.json')
water=unary_union([Polygon(p[0],p[1:]) for river in plan['rivers']+scene['westContext']['rivers'] for p in river['polygons']])
streets=unary_union([LineString(q['points']).buffer(q['width']/2+1.1,cap_style=2,join_style=2)
                    for q in load('data/maps/district-road-traces.json')['roads']])
for id in corrections:
    p=Polygon(models[id]['footprint'],models[id]['worldHoles'])
    assert p.intersection(water.buffer(.12)).area<.01,(id,'water')
    assert p.intersection(streets).area<.01,(id,'street')
volumes=unary_union([Polygon(p['outer'],p['holes']) for b in scene['buildings'] for p in b['renderPolygons']])
for c in r['structures']:
    s=next(s for s in scene['structures'] if s['id']==c['id'])
    assert Point(s['x'],s['z']).distance(Point(c['centre']))<.001
    assert s['height']==c['preservedHeight']
    if 'sourceFid' in c:
        base=unary_union([Polygon(p[0],p[1:]) for p in c['sourcePolygons']])
        assert s['sourceFootprintFid']==1230955 and s['radius']==.5 and s['height']==22
        half=s['radius']*1.2/math.sqrt(2)
        plinth=affinity.translate(affinity.rotate(box(-half,-half,half,half),s['rotation']),s['x'],s['z'])
        assert plinth.difference(base).area<.001
        assert plinth.intersection(volumes).area<.001,'Mapped chimney opening was filled by a roof'
    else:
        assert s['mappedHeightFeet']==50 and s['height']==15.24
        assert Polygon(models['site964-dane-532']['footprint']).contains(Point(s['x'],s['z']))
# The additional southern annex retains its separate small mapped opening even
# though that minor feature is not yet given an interpreted 3D structure.
assert models['site964-ink-south-annex']['worldHoles']
assert models['site964-range-7']['height']==16.2 and models['site964-range-7']['roofBays']==2
yards=load('docs/data/factory-yards.json')['sites']
for record,points in zip(r['yards'],[[(-680,-110),(-706,-120)],[(-632,-13),(-650,4)]]):
    yard=next(y for y in yards if y['id']==record['id'])
    surface=unary_union([Polygon(p[0],p[1:]) for p in yard['polygons']])
    envelope=unary_union([Polygon(p[0],p[1:]) for p in record['polygons']])
    assert surface.difference(envelope).area<.001 and surface.area>300
    assert all(surface.covers(Point(p)) for p in points),(record['id'],'missing mapped open ground')
    assert not yard['stock']
    assert surface.intersection(volumes).area<.01
assert all(not volumes.covers(Point(p)) for p in [(-680,-110),(-706,-120)]),'Crystal Wharf yard was filled by a replacement block'
(ROOT/'reference/footprint-model-alignment/verified-crystal-barber.json').write_text(json.dumps(results,indent=2)+'\n')
print(f'Crystal/Barber: 21 aligned ranges, 13 additions, four open-yard blocks removed, two corrected chimneys; all 40 eastern ranges source-linked. Minimum rendered agreement {min(v["renderedIoU"] for v in results):.3%}.')
