"""Check new northern-strip roofs, explicit map trace and open context."""
import argparse
import math
from pathlib import Path

from shapely import affinity
from shapely.geometry import Point, Polygon, shape
from shapely.ops import unary_union

from factory_alignment_checks import load
from factory_street_clearance import street_clearances
from prepare_east_channelsea_north_alignment import BASELINE, NAME, SITE_NAMES, SPECS

ROOT = Path(__file__).resolve().parents[1]


def check(preflight=False):
    r = load(f'data/maps/{NAME}-footprint-alignment.json')
    before = load(BASELINE)
    scene = load('docs/data/factory-buildings.json')
    additions = {b['id']: b for b in r['additionalBuildings']}
    rows = {b['modelId']: b for b in r['buildings']}
    groups = {g['id']: g for g in r['groups']}
    expected = {'east-north-'+key for key, *_ in SPECS}
    direct_id = 'east-north-hardware-main-direct'
    assert len(additions) == 37 and len(groups) == len(rows) == len(expected) == 36
    assert set(rows) == set(groups) == expected
    assert set(additions) == expected | {direct_id}
    assert {s['id'] for s in r['additionalSites']} == set(SITE_NAMES)
    assert {b['modelId'] for b in r['mapTracedBuildings']} == {direct_id}
    assert not any(r.get(key) for key in ['removedBuildings', 'removedStructures', 'structures', 'tanks', 'locallyTransferredBuildings'])
    assert not set(additions).intersection(b['id'] for b in before['buildings'])
    shapes = {ident: Polygon(b['worldFootprint'], b['worldHoles']) for ident, b in additions.items()}
    own_fids = []
    for key, site, fids, name, height, _ in SPECS:
        ident = 'east-north-'+key
        group, row, addition = groups[ident], rows[ident], additions[ident]
        assert group['sourceFids'] == fids and group['modelIds'] == [ident]
        assert group['additional'] and group['previousUnionIoU'] == 0
        assert row['additionalModel'] and row['priorFootprint'] == []
        assert addition['siteId'] == site and addition['name'] == name
        assert row['preservedHeight'] == addition['eavesHeight'] == height
        for key, preserved in [('roofRise', 'preservedRoofRise'), ('roofAxis', 'preservedRoofAxis'), ('roofBays', 'preservedRoofBays')]:
            assert row[preserved] == addition[key]
        assert shapes[ident].is_valid and shapes[ident].area > 2
        assert addition['source'] == 'os-1893'
        assert 'estimated' in addition['heightEvidence'] and 'interpretations' in addition['roofEvidence']
        source = unary_union([Polygon(p[0], p[1:]) for p in group['sourcePolygons']])
        target = shapes[ident]
        if reconciliation := group.get('mappedWaterReconciliation'):
            assert ident == 'east-north-brush-main'
            water = unary_union([Polygon(p[0], p[1:]) for p in reconciliation['waterPolygons']])
            mask = water.buffer(reconciliation['clearanceMetres'])
            expected_source = source.difference(mask)
            assert abs(source.intersection(mask).area-reconciliation['sourceRemovedAreaM2']) < .000001
            assert reconciliation['sourceRemovedAreaM2'] < reconciliation['maximumRemovedAreaM2'] == 5
            assert source.hausdorff_distance(target) < reconciliation['maximumBoundaryShiftMetres'] == .8
            assert target.intersection(water.buffer(.12)).area < .001
            assert source.intersection(target).area/source.union(target).area > .99
            source = expected_source
        assert source.symmetric_difference(target).area < .1
        assert source.hausdorff_distance(target) < .0015
        assert target.difference(source.buffer(.0015)).area < .0001
        own_fids.extend(fids)
    assert len(own_fids) == len(set(own_fids))
    assert len(shapes['east-north-langthorn-west-inner'].interiors) == 1
    for record in r['openCourtReviews']:
        assert not unary_union(list(shapes.values())).covers(Point(record['worldPoint'])), record
    # The omitted L-shaped roof is a direct map trace, not a nearest feature.
    trace = r['directMapTraces'][0]
    assert trace['modelId'] == direct_id and trace['nativePixels']
    assert trace['excludedSourceFids'] == [6805, 664984, 384628, 1097233, 1024082]
    raw = Polygon(trace['rawWorldFootprint'])
    sources = {fid: Polygon(ring[0], ring[1:]) for g in r['groups'] for fid, ring in zip(g['sourceFids'], g['sourcePolygons'])}
    neighbours = unary_union([sources[fid] for fid in trace['excludedSourceFids']])
    expected_direct = raw.difference(neighbours)
    assert abs(raw.intersection(neighbours).area-trace['sourceBoundaryReconciliationAreaM2']) < .000001
    assert expected_direct.symmetric_difference(shapes[direct_id]).area < .1
    assert expected_direct.hausdorff_distance(shapes[direct_id]) < .0015
    assert 600 < shapes[direct_id].area < 1500, shapes[direct_id].area

    all_used = {}
    for path in sorted((ROOT/'data/maps').glob('*footprint-alignment.json')):
        if path.name == f'{NAME}-footprint-alignment.json':
            continue
        other = load(str(path.relative_to(ROOT)))
        for group in other.get('groups', other.get('buildings', [])):
            for fid in group.get('sourceFids', [group.get('sourceFid')]):
                if fid is not None:
                    all_used.setdefault(fid, []).append(path.name)
        for key in ['structures', 'tanks', 'mappedPlants', 'additionalStructures']:
            for row in other.get(key, []):
                for fid in list(row.get('sourceFids', row.get('sourceFootprintFids', [])))+[row.get('sourceFid'), row.get('sourceFootprintFid')]:
                    if fid is not None:
                        all_used.setdefault(fid, []).append(path.name)
    assert not set(own_fids).intersection(all_used), {f: all_used[f] for f in set(own_fids).intersection(all_used)}
    excluded = {fid for q in r['excludedContext'] for fid in q['sourceFids']}
    deferred = {fid for q in r['deferred'] for fid in q.get('sourceFids', [])}
    assert not set(own_fids).intersection(excluded | deferred)
    # Audit source rings against the full source extract when locally present.
    full = ROOT/'reference/historic-building-footprints-2026-09-28/current-scene-buildings-bng.geojson'
    if full.exists():
        original = {f['properties']['sourceFid']: affinity.affine_transform(shape(f['geometry']),
            [1, 0, 0, -1, -538900, 183209]) for f in load(str(full.relative_to(ROOT)))['features']
            if f['properties']['sourceFid'] in own_fids}
        assert set(original) == set(own_fids)
        assert all(original[fid].symmetric_difference(sources[fid]).area < .000001 for fid in own_fids)
    print(f'{NAME}: 37 new roofs, full source provenance, bounded Brush north-edge reconciliation, direct Hardware trace, interpreted profiles and open courts pass.')

    streets, frontages = street_clearances(load('data/maps/district-road-traces.json')['roads'])
    context = load('data/maps/east-channelsea-context-alignment.json')
    # Parent context integration may not yet have placed the new precise moat
    # in ground-plan.json; use it for authoring clearance regardless.
    rivers = load('docs/data/ground-plan.json')['rivers']+scene['westContext']['rivers']+context['additionalRivers']
    water = unary_union([Polygon(p[0], p[1:]) for q in rivers for p in q['polygons']])
    models = {b['id']: b for b in scene['buildings']}
    all_shapes = {ident: shapes.get(ident, Polygon(b['footprint'], b.get('worldHoles', []))) for ident, b in models.items()}
    all_shapes.update(shapes)
    housing = [Polygon(b['footprint']) for b in load('docs/data/housing-detail.json')['rows']]
    for ident, target in shapes.items():
        assert target.intersection(water.buffer(.12)).area < .01, (ident, 'water', target.intersection(water.buffer(.12)).area)
        assert target.intersection(frontages.get(ident, streets)).area < .01, (ident, 'road')
        for other, body in all_shapes.items():
            if ident != other:
                assert target.intersection(body).area < .04, (ident, other, target.intersection(body).area)
        assert all(target.intersection(body).area < .04 for body in housing), (ident, 'existing housing')
        if not preflight:
            actual = models[ident]
            expected = additions[ident]
            for field, saved in [('height', 'eavesHeight'), ('roofRise', 'roofRise'), ('roofAxis', 'roofAxis'), ('roofBays', 'roofBays')]:
                assert actual[field] == expected[saved], (ident, field)
            assert actual['name'] == expected['name']
            assert math.isclose(actual['rotation'], expected['footprintRotationDegrees'], abs_tol=.0001)
            render = unary_union([Polygon(p['outer'], p['holes']) for p in actual['renderPolygons']])
            assert target.symmetric_difference(render).area < .02, ident
    if not preflight:
        # Additional roofs should not modify previous authored exteriors or
        # elevations. Exempt only existing models explicitly reviewed by a
        # concurrently integrated register; context clipping is checked there.
        reviewed = set()
        for path in scene['footprintAlignment']['groupRegisters']:
            if path == f'data/maps/{NAME}-footprint-alignment.json':
                continue
            other = load(path)
            for key in ['buildings', 'mapTracedBuildings', 'locallyTransferredBuildings', 'removedBuildings']:
                reviewed.update(b.get('modelId', b.get('id')) for b in other.get(key, []))
        for old in before['buildings']:
            if old['id'] in reviewed:
                continue
            actual = models[old['id']]
            assert actual['footprint'] == old['footprint'], old['id']
            for field in ['height', 'roofRise', 'roofAxis', 'roofBays', 'rotation']:
                assert actual[field] == old[field], (old['id'], field)
        assert sum(b['siteId'] in SITE_NAMES for b in models.values()) == 37
    print(f'{NAME}: roads, water, neighbouring ranges and existing housing clear'+(' (authoring preflight).' if preflight else '; published profiles/rendering and existing exteriors retained.'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--preflight', action='store_true')
    check(parser.parse_args().preflight)
