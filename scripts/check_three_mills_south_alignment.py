"""Check source coverage, preserved elevations, clearances and unchanged neighbours."""
import argparse
import json
import math
from itertools import combinations
from pathlib import Path
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
from factory_street_clearance import street_clearances

ROOT = Path(__file__).resolve().parents[1]
load = lambda p:json.loads((ROOT/p).read_text())


def check(preflight=False):
    r = load('data/maps/three-mills-south-footprint-alignment.json')
    scene = load('docs/data/factory-buildings.json')
    models = {b['id']:b for b in scene['buildings']}
    cs = {c['modelId']:c for c in r['buildings']}
    assert set(cs)=={f'site419-range-{i}' for i in range(21,29)}
    assert len(r['groups'])==5 and len(r['tanks'])==3
    shapes = {id:Polygon(c['worldFootprint'],c['worldHoles']) for id,c in cs.items()}
    used = set()
    for path in [scene['footprintAlignment']['register']]+scene['footprintAlignment']['groupRegisters']:
        if path.endswith('/three-mills-south-footprint-alignment.json'):continue
        other = load(path)
        for g in other.get('groups',other['buildings']):
            used.update(g.get('sourceFids',[g.get('sourceFid')]))
    results = []
    for g in r['groups']:
        assert not used.intersection(g['sourceFids']),g['id']
        used.update(g['sourceFids'])
        source = unary_union([Polygon(p[0],p[1:]) for p in g['sourcePolygons']])
        target = unary_union([shapes[id] for id in g['modelIds']])
        # Millimetre rounding along the large warehouse perimeter accumulates
        # 0.074 m², while every point remains within 1.5 mm of its source.
        assert target.is_valid and target.symmetric_difference(source).area<.1,g['id']
        assert target.difference(source.buffer(.0015)).area<.0001,g['id']
        assert source.difference(target.buffer(.0015)).area<.0001,g['id']
        score = target.intersection(source).area/target.union(source).area
        assert score>.9995 and score>g['previousUnionIoU'],g['id']
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
        results.append(dict(id=g['id'],previousIoU=g['previousUnionIoU'],sourceIoU=score))
    streets,frontages = street_clearances(load('data/maps/district-road-traces.json')['roads'])
    water = unary_union([Polygon(p[0],p[1:]) for q in
        load('docs/data/ground-plan.json')['rivers']+scene['westContext']['rivers'] for p in q['polygons']])
    all_shapes = {id:shapes.get(id,Polygon(b['footprint'],b.get('worldHoles',[]))) for id,b in models.items()}
    for id,p in shapes.items():
        assert p.intersection(water.buffer(.12)).area<.01,id
        assert p.intersection(frontages.get(id,streets)).area<.01,id
        for other,q in all_shapes.items():
            if id!=other:assert p.intersection(q).area<.04,(id,other)
    body = unary_union(list(all_shapes.values()))
    circles = []
    for c in r['tanks']:
        tank = c if preflight else next(t for t in scene['structures'] if t['id']==c['id'])
        base = unary_union([Polygon(p[0],p[1:]) for p in c['sourcePolygons']])
        centre = Point(tank['x'],tank['z'])
        assert centre.distance(base.centroid)<.001
        assert tank['height']==c['priorStructure']['height']==6
        assert tank['sourceFootprintFid']==c['sourceFootprintFid']
        assert abs(math.pi*tank['equalAreaRadius']**2-base.area)<.025
        assert 0<=centre.distance(base.boundary)-tank['radius']<.001
        circle = centre.buffer(tank['radius'])
        for obstruction in [body,streets,water]:assert circle.intersection(obstruction).area<.001,tank['id']
        assert circle.difference(base).area<.001
        circles.append(circle)
    for a,b in combinations(circles,2):assert a.distance(b)>.1
    if not preflight:
        assert len(scene['buildings'])==547 and len([b for b in models.values() if b['siteId']==419])==38
        path = ROOT/'reference/footprint-model-alignment/three-mills-south-before.json'
        if path.exists():
            before = load(path)
            for b in before['buildings']:
                if b['id'] in cs:continue
                old = unary_union([Polygon(p['outer'],p['holes']) for p in b['renderPolygons']])
                actual = unary_union([Polygon(p['outer'],p['holes']) for p in models[b['id']]['renderPolygons']])
                assert old.symmetric_difference(actual).area<.01,b['id']
            for old in before['structures']:
                if old['id'] not in {c['id'] for c in r['tanks']}:
                    assert old==next(t for t in scene['structures'] if t['id']==old['id']),old['id']
        (ROOT/'reference/footprint-model-alignment/verified-three-mills-south.json').write_text(json.dumps(results,indent=2)+'\n')
    print('Three Mills south: eight ranges, three fitted tanks, source coverage, heights and clearances pass'+
          (' (authoring preflight).' if preflight else '; other buildings and plant retained.'))


if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--preflight',action='store_true')
    check(parser.parse_args().preflight)
