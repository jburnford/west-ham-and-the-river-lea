"""Chemical source coverage, retained roofs, preserved links and square plinth."""
import argparse
import math
from pathlib import Path

from shapely import affinity
from shapely.geometry import Point, Polygon, box, shape
from shapely.ops import unary_union

from factory_alignment_checks import check_register, load
from factory_street_clearance import street_clearances
from prepare_jeffrey_glue_alignment import validate_render_changes

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--preflight', action='store_true')
args = parser.parse_args()
before = load('reference/footprint-model-alignment/marshgate-trades-before.json')
old_models = {b['id']: b for b in before['buildings']}
preserved = {'site939-912': 23412, 'site939-926': 7029}
expected = {b['id'] for b in before['buildings'] if b['siteId'] == 939} - preserved.keys()
check_register('marshgate-chemical', expected, 6, 0, 'marshgate-trades-before',
    preflight=args.preflight, later_registers=['jeffrey-glue', 'alderson-rope'])
r = load('data/maps/marshgate-chemical-footprint-alignment.json')
scene = load('docs/data/factory-buildings.json')
models = {b['id']: b for b in scene['buildings']}
assert not r.get('additionalBuildings') and not r.get('removedBuildings')
assert not r.get('mapTracedBuildings') and not r.get('locallyTransferredBuildings')
assert {b['modelId']: b['sourceFid'] for b in r['preservedSourceLinkedBuildings']} == preserved
for ident, fid in preserved.items():
    old, actual = old_models[ident], models[ident]
    assert actual['sourceFootprintFid'] == old['sourceFootprintFid'] == fid
    for key in ['height', 'roofRise', 'roofAxis', 'roofBays', 'footprint', 'rotation', 'worldHoles']:
        assert actual.get(key) == old.get(key), (ident, key)
rows = {c['modelId']: c for c in r['buildings']}
neighbors = dict(rows)
neighbors.update({b['modelId']: b for b in load('data/maps/jeffrey-glue-footprint-alignment.json')['buildings']})
assert {c['modelId'] for c in r['renderChanges']} == {'site939-912', 'site939-926'}
validate_render_changes(r['renderChanges'], before, scene, neighbors, args.preflight)
bodies = {ident: Polygon(c['worldFootprint'], c['worldHoles']) for ident, c in rows.items()}
assert bodies['site939-918'].touches(bodies['site939-920'])
assert bodies['site939-936'].touches(bodies['site939-938'])
assert bodies['site939-918'].intersection(bodies['site939-920']).area < .001
assert bodies['site939-936'].intersection(bodies['site939-938']).area < .001
for g in r['groups']:
    assert all(rows[i]['siteId'] == 939 for i in g['modelIds'])
    if len(g['modelIds']) == 2:
        assert g['divisionParameters']['evidence']
        assert 0 < g['divisionParameters']['northernDepthFraction'] < 1

# Check the saved cache against the complete supplied extract as well as the
# register's own rings. No nearest-feature matching enters the authoring pass.
own_fids = {fid for g in r['groups'] for fid in g['sourceFids']} | {1102599}
cached = load('reference/footprint-model-alignment/marshgate-trades-source-shapes.json')
source = load('reference/historic-building-footprints-2026-09-28/current-scene-buildings-bng.geojson')
complete = {f['properties']['sourceFid']: affinity.affine_transform(shape(f['geometry']),
    [1, 0, 0, -1, -538900, 183209]) for f in source['features']
    if f['properties']['sourceFid'] in own_fids}
assert set(complete) == own_fids
for fid in own_fids:
    assert shape(cached[str(fid)]).symmetric_difference(complete[fid]).area < .000001, fid

used = {}
for path in sorted((ROOT/'data/maps').glob('*footprint-alignment.json')):
    if path.name == 'marshgate-chemical-footprint-alignment.json': continue
    other = load(str(path.relative_to(ROOT)))
    for g in other.get('groups', other.get('buildings', [])):
        for fid in g.get('sourceFids', [g.get('sourceFid')]):
            used.setdefault(fid, []).append(path.name)
    for key in ['structures', 'tanks', 'mappedPlants']:
        for s in other.get(key, []):
            fid = s.get('sourceFid', s.get('sourceFootprintFid'))
            if fid is not None: used.setdefault(fid, []).append(path.name)
assert not own_fids.intersection(used), {f: used[f] for f in own_fids.intersection(used)}
listed = [f for g in r['groups'] for f in g['sourceFids']] + [s['sourceFid'] for s in r['structures']]
assert len(listed) == len(set(listed))
assert len(r['structures']) == 1
c = r['structures'][0]
old = next(s for s in before['structures'] if s['id'] == c['id'])
assert c['id'] == 'stack-939-1756-1440' and c['sourceFid'] == 1102599
assert c['preservedHeight'] == old['height'] == 22
assert c['priorRadius'] == old['radius'] and 0 < c['radius'] <= old['radius']
centre = Point(c['centre'])
radius = c['radius']
plinth = affinity.rotate(box(centre.x-radius*1.2, centre.y-radius*1.2,
    centre.x+radius*1.2, centre.y+radius*1.2), c['rotation'], origin=centre)
base = unary_union([Polygon(p[0], p[1:]) for p in c['sourcePolygons']])
assert base.covers(plinth)
assert centre.distance(base.centroid) < .001
streets, _ = street_clearances(load('data/maps/district-road-traces.json')['roads'])
water = unary_union([Polygon(p[0], p[1:]) for q in
    load('docs/data/ground-plan.json')['rivers']+scene['westContext']['rivers'] for p in q['polygons']])
others = [Polygon(b['footprint'], b.get('worldHoles', []))
          for b in scene['buildings'] if b['id'] not in expected]
assert plinth.intersection(unary_union(list(bodies.values())+others+[streets, water])).area < .001
assert base.symmetric_difference(complete[1102599]).area < .000001
if not args.preflight:
    actual = next(s for s in scene['structures'] if s['id'] == c['id'])
    assert actual['sourceFootprintFid'] == c['sourceFid']
    assert actual['height'] == old['height'] and actual['section'] == old['section']
    assert actual['radius'] == radius and actual['rotation'] == c['rotation']
    assert math.dist([actual['x'], actual['z']], c['centre']) < .001
print('Marshgate chemical: eight reviewed ranges, two retained source links, interpreted compartments and one contained square chimney plinth pass.')
