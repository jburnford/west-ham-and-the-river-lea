"""Shared checks for saved factory matches and their published geometry."""
import json
import math
from itertools import combinations
from pathlib import Path
from shapely.geometry import Polygon, Point, LineString
from shapely.ops import unary_union
from factory_street_clearance import street_clearances

ROOT = Path(__file__).resolve().parents[1]
load = lambda p:json.loads((ROOT/p).read_text())


def later_reviews(scene, register_name, extra_names=()):
    """Only exempt later reviews or explicit companion passes sharing a baseline."""
    paths=scene['footprintAlignment']['groupRegisters']
    current=f'data/maps/{register_name}-footprint-alignment.json'
    later=paths[paths.index(current)+1:] if current in paths else []
    later=list(dict.fromkeys(later+[f'data/maps/{name}-footprint-alignment.json' for name in extra_names]))
    return [load(path) for path in later if (ROOT/path).exists()]


def reviewed_ids(registers):
    return {row.get('modelId',row.get('id')) for r in registers for key in
            ['buildings','removedBuildings','mapTracedBuildings','locallyTransferredBuildings','renderChanges','roadRenderChanges']
            for row in r.get(key,[])}


def check_render_changes(registers, models):
    """Constrain derived clipping changes while retaining the original model."""
    for register in registers:
        for c in register.get('roadRenderChanges',[]):
            b=models[c['modelId']]
            assert b['footprint']==c['preservedFootprint']
            assert all(b[key]==value for key,value in c['preservedProfile'].items())
            context=load(c['contextRegister'])
            road=context['road']
            width=road['width']/2+road['ordinaryShoulderWidth']
            corridors=[LineString(road[key]).buffer(width,cap_style=2,join_style=2)
                       for key in ['priorPoints','points']]
            prior=unary_union([Polygon(p['outer'],p['holes']) for p in c['priorRenderPolygons']])
            actual=unary_union([Polygon(p['outer'],p['holes']) for p in b['renderPolygons']])
            delta=prior.symmetric_difference(actual)
            # Re-rounding the clipped polygon shifts existing long edge segments
            # by fractions of a millimetre after adding intersection vertices.
            remainder=delta.difference(unary_union(corridors).buffer(.0015))
            assert remainder.area<.01,c['modelId']
            assert remainder.difference(prior.boundary.buffer(.0015)).area<.00001,c['modelId']
            assert actual.intersection(corridors[1].buffer(-.0015)).area<.001,c['modelId']
            assert actual.difference(Polygon(b['footprint']).buffer(.0015)).area<.001,c['modelId']
        for c in register.get('renderChanges',[]):
            b=models[c['modelId']]
            assert b['footprint']==c['preservedFootprint'],c['modelId']
            for key,value in c['preservedProfile'].items():
                assert b[key]==value,(c['modelId'],key)
            geometry=lambda ps:unary_union([Polygon(p['outer'],p['holes']) for p in ps])
            prior=geometry(c['priorRenderPolygons'])
            expected=geometry(c['expectedRenderPolygons'])
            actual=geometry(b['renderPolygons'])
            assert actual.symmetric_difference(expected).area<.00001,c['modelId']
            added,lost=actual.difference(prior),prior.difference(actual)
            assert added.area<=c['maximumAddedAreaM2'] and lost.area<=c['maximumRemovedAreaM2']
            assert abs(added.area-c['addedAreaM2'])<.00001
            assert abs(lost.area-c['removedAreaM2'])<.00001
            baseline=ROOT/c['baseline']
            if baseline.exists():
                old={b['id']:b for b in load(c['baseline'])['buildings']}
                neighbors=unary_union([Polygon(scene[id]['footprint'],scene[id].get('worldHoles',[]))
                    for scene in [old,models] for id in c['neighborModelIds']])
                precision=c['roundingBoundaryBufferMetres']
                remainder=added.union(lost).difference(neighbors.buffer(precision))
                assert remainder.area<=c['maximumRoundingAreaM2']
                assert remainder.difference(Polygon(b['footprint']).boundary.buffer(precision)).area<.00001


def check_register(register_name, expected_ids, expected_groups, expected_tanks, before_name,
                   preflight=False, permitted_water=(), later_registers=(), scene_counts=None):
    r = load(f'data/maps/{register_name}-footprint-alignment.json')
    scene = load('docs/data/factory-buildings.json')
    models = {b['id']:b for b in scene['buildings']}
    if preflight:
        for b in r.get('additionalBuildings',[]):
            models[b['id']]={**b,'height':b['eavesHeight'],'footprint':b['worldFootprint']}
    cs = {c['modelId']:c for c in r['buildings']}
    assert set(cs)==set(expected_ids)
    assert len(r['groups'])==expected_groups and len(r.get('tanks',[]))==expected_tanks
    shapes = {id:Polygon(c['worldFootprint'],c['worldHoles']) for id,c in cs.items()}
    used = set()
    for path in [scene['footprintAlignment']['register']]+scene['footprintAlignment']['groupRegisters']:
        if path==f'data/maps/{register_name}-footprint-alignment.json':continue
        other = load(path)
        for g in other.get('groups',other['buildings']):
            used.update(g.get('sourceFids',[g.get('sourceFid')]))
    results = []
    for g in r['groups']:
        assert not used.intersection(g['sourceFids']),g['id']
        used.update(g['sourceFids'])
        raw_source = unary_union([Polygon(p[0],p[1:]) for p in g['sourcePolygons']])
        source = raw_source
        if reconciliation:=g.get('sourceReconciliation'):
            assert reconciliation['evidence'] and reconciliation['excludedSourceFids']
            exclusions=[]
            for fid in reconciliation['excludedSourceFids']:
                matches=[Polygon(p[0],p[1:]) for other in r['groups']
                         for source_id,p in zip(other['sourceFids'],other['sourcePolygons']) if source_id==fid]
                assert len(matches)==1,(g['id'],fid)
                exclusions.extend(matches)
            source=raw_source.difference(unary_union(exclusions))
            assert abs(raw_source.area-source.area-reconciliation['removedAreaM2'])<.001
            reconciled=unary_union([Polygon(p[0],p[1:]) for p in g['reconciledPolygons']])
            assert reconciled.symmetric_difference(source).area<.1,g['id']
            assert reconciled.hausdorff_distance(source)<.0015,g['id']
        target = unary_union([shapes[id] for id in g['modelIds']])
        # Millimetre rounding along the large warehouse perimeter accumulates
        # 0.074 m², while every point remains within 1.5 mm of its source.
        assert target.is_valid and target.symmetric_difference(source).area<.1,g['id']
        assert target.difference(source.buffer(.0015)).area<.0001,g['id']
        assert source.difference(target.buffer(.0015)).area<.0001,g['id']
        score = target.intersection(source).area/target.union(source).area
        assert score>.9995,g['id']
        if not g.get('additional'):assert score>g['previousUnionIoU'],g['id']
        for id in g['modelIds']:
            b,c = models[id],cs[id]
            for key,saved in [('height','preservedHeight'),('roofRise','preservedRoofRise'),
                              ('roofAxis','preservedRoofAxis'),('roofBays','preservedRoofBays')]:
                assert b[key]==c[saved],(id,key)
            if not preflight:
                assert b['footprintGroup']==g['id'] and b['sourceFootprintFids']==g['sourceFids']
                actual = unary_union([Polygon(p['outer'],p['holes']) for p in b['renderPolygons']])
                assert actual.symmetric_difference(shapes[id]).area<.02,id
                assert abs(b['rotation']-c['footprintRotationDegrees'])<.0001
        results.append(dict(id=g['id'],previousIoU=g['previousUnionIoU'],sourceIoU=score,
                            rawSourceIoU=target.intersection(raw_source).area/target.union(raw_source).area))
    # Direct map traces participate in the same neighbor/road/water checks.
    direct_ids={c['modelId'] for c in r.get('mapTracedBuildings',[])}
    shapes.update({c['modelId']:Polygon(c['worldFootprint'],c.get('worldHoles',[]))
                   for c in r.get('mapTracedBuildings',[])})
    streets,frontages = street_clearances(load('data/maps/district-road-traces.json')['roads'])
    water = unary_union([Polygon(p[0],p[1:]) for q in
        load('docs/data/ground-plan.json')['rivers']+scene['westContext']['rivers'] for p in q['polygons']])
    removed_ids={b['id'] for b in r.get('removedBuildings',[])}
    all_shapes = {id:shapes.get(id,Polygon(b['footprint'],b.get('worldHoles',[]))) for id,b in models.items() if id not in removed_ids}
    for id,p in shapes.items():
        if id not in permitted_water:assert p.intersection(water.buffer(.12)).area<.01,id
        assert p.intersection(frontages.get(id,streets)).area<.01,id
        for other,q in all_shapes.items():
            if id!=other:assert p.intersection(q).area<.04,(id,other)
    body = unary_union(list(all_shapes.values()))
    circles = []
    for c in r.get('tanks',[]):
        tank = c if preflight else next(t for t in scene['structures'] if t['id']==c['id'])
        base = unary_union([Polygon(p[0],p[1:]) for p in c['sourcePolygons']])
        centre = Point(tank['x'],tank['z'])
        assert centre.distance(base.centroid)<.001
        assert tank['height']==c['priorStructure']['height']
        assert tank['sourceFootprintFid']==c['sourceFootprintFid']
        assert abs(math.pi*tank['equalAreaRadius']**2-base.area)<.025
        assert 0<=centre.distance(base.boundary)-tank['radius']<.001
        circle = centre.buffer(tank['radius'])
        for obstruction in [body,streets,water]:assert circle.intersection(obstruction).area<.001,tank['id']
        assert circle.difference(base).area<.001
        circles.append(circle)
    for a,b in combinations(circles,2):assert a.distance(b)>.1
    if not preflight:
        later=later_reviews(scene,register_name,later_registers)
        check_render_changes([r]+later,models)
        added=[b for r in later for b in r.get('additionalBuildings',[])]
        removed=[b for r in later for b in r.get('removedBuildings',[])]
        if scene_counts:
            total,sites = scene_counts
            assert len(scene['buildings'])==total+len(added)-len(removed)
            for site,count in sites.items():
                delta=sum(b.get('siteId')==site for b in added)-sum(b.get('siteId')==site for b in removed)
                assert sum(b['siteId']==site for b in models.values())==count+delta
        path = ROOT/f'reference/footprint-model-alignment/{before_name}.json'
        later_ids=reviewed_ids(later)
        later_structures={s['id'] for r in later for key in ['structures','tanks','mappedPlants','removedStructures'] for s in r.get(key,[])}
        if path.exists():
            before = load(path)
            for b in before['buildings']:
                own_render_ids={c['modelId'] for key in ['renderChanges','roadRenderChanges'] for c in r.get(key,[])}
                if b['id'] in set(cs)|direct_ids|later_ids|removed_ids|own_render_ids:continue
                old = unary_union([Polygon(p['outer'],p['holes']) for p in b['renderPolygons']])
                actual = unary_union([Polygon(p['outer'],p['holes']) for p in models[b['id']]['renderPolygons']])
                assert old.symmetric_difference(actual).area<.01,b['id']
            for old in before['structures']:
                own_structures={s['id'] for key in ['structures','tanks','mappedPlants','removedStructures'] for s in r.get(key,[])}
                if old['id'] not in own_structures|later_structures and old.get('parentBuildingId') not in later_ids:
                    assert old==next(t for t in scene['structures'] if t['id']==old['id']),old['id']
        (ROOT/f'reference/footprint-model-alignment/verified-{register_name}.json').write_text(json.dumps(results,indent=2)+'\n')
    print(f'{register_name}: {len(cs)} ranges, {expected_tanks} fitted tanks, source coverage, heights and clearances pass'+
          (' (authoring preflight).' if preflight else '; other buildings and plant retained.'))
