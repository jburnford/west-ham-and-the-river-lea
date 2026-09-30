"""Check reviewed western trade exteriors, profiles and deferred identities."""
import argparse
import math
from pathlib import Path

from shapely import affinity
from shapely.geometry import Point, Polygon, box, shape
from shapely.ops import unary_union

from factory_alignment_checks import check_register, load
from prepare_western_trades_alignment import BASELINE, SPECS

ROOT = Path(__file__).resolve().parents[1]


def check(preflight=False):
    register = load('data/maps/western-trades-footprint-alignment.json')
    before = load(BASELINE)
    prior = {b['id']: b for b in before['buildings']}
    scene = load('docs/data/factory-buildings.json')
    models = {b['id']: b for b in scene['buildings']}
    expected = {ident for _, _, ids, *_ in SPECS for ident in ids}
    rows = {b['modelId']: b for b in register['buildings']}
    assert set(rows) == expected and len(expected) == 17
    groups = {g['id']: g for g in register['groups']}
    assert len(groups) == 12
    assert not any(register.get(k) for k in ['additionalBuildings', 'mapTracedBuildings',
        'locallyTransferredBuildings', 'tanks', 'mappedPlants', 'removedStructures', 'removedBuildings'])
    shapes = {ident: Polygon(row['worldFootprint'], row['worldHoles']) for ident, row in rows.items()}
    for ident, row in rows.items():
        old = prior[ident]
        assert row['priorFootprint'] == old['footprint']
        assert row['priorRotationDegrees'] == old['rotation']
        for key, saved in [('height', 'preservedHeight'), ('roofRise', 'preservedRoofRise'),
            ('roofAxis', 'preservedRoofAxis'), ('roofBays', 'preservedRoofBays')]:
            assert row[saved] == old[key], (ident, key)
        assert shapes[ident].is_valid and shapes[ident].area > 2
        if not preflight:
            assert models[ident]['name'] == row['name']
    for gid, fids, ids, *_ in SPECS:
        group = groups[gid]
        assert group['sourceFids'] == fids and group['modelIds'] == ids
        source = unary_union([Polygon(p[0], p[1:]) for p in group['sourcePolygons']])
        if reconciliation := group.get('sourceReconciliation'):
            assert gid == 'western-moulding-main'
            assert reconciliation['excludedSourceFids'] == [155914]
            room = Polygon(groups['western-moulding-south']['sourcePolygons'][0][0])
            assert abs(source.intersection(room).area-reconciliation['removedAreaM2']) < .000001
            source = source.difference(room)
        authored = unary_union([shapes[ident] for ident in ids])
        saved = unary_union([Polygon(p[0], p[1:]) for p in group['reconciledPolygons']])
        # Rounded cut endpoints subdivide long exterior edges by less than
        # 0.45 mm; their floating-point area delta stays below 0.005 m².
        assert saved.symmetric_difference(authored).area < .005
        assert saved.hausdorff_distance(authored) < .0005
        assert source.hausdorff_distance(authored) < .0015
        for n, ident in enumerate(ids):
            assert all(shapes[ident].intersection(shapes[other]).area < .001 for other in ids[:n])
    assert groups['western-foundry-main']['divisionParameters']['chords'] == [[[-830.106, 270.986], [-820.226, 288.688]]]
    gate = groups['western-foundry-west']['divisionParameters']
    assert gate['westernGateWidthFraction'] == 5.805/(17.342+5.805)
    assert groups['western-moulding-main']['divisionParameters']['chords'] == [
        [[-731.457, 352.242], [-709.786, 367.875]],
        [[-746.871, 375.864], [-754.866, 370.468]]]
    # The old lean-to/gate overlaps disappear without flattening their profiles.
    assert shapes['west-563-3'].intersection(shapes['west-563-5']).area < .001
    assert shapes['west-941-1'].intersection(shapes['west-941-4']).area < .001
    assert shapes['west-563-2'].distance(unary_union([shapes['west-563-1'], shapes['west-563-4']])) > 3
    assert shapes['west-941-5'].distance(shapes['west-941-3']) > 30

    # Every saved alignment pass participates, including independent companion
    # authoring registers not yet integrated into the scene builder.
    own_fids = [fid for group in register['groups'] for fid in group['sourceFids']]
    assert len(own_fids) == len(set(own_fids)) == 14
    others = {}
    for path in sorted((ROOT/'data/maps').glob('*footprint-alignment.json')):
        if path.name == 'western-trades-footprint-alignment.json':
            continue
        other = load(str(path.relative_to(ROOT)))
        for group in other.get('groups', other.get('buildings', [])):
            for fid in group.get('sourceFids', [group.get('sourceFid')]):
                if fid is not None:
                    others.setdefault(fid, []).append(path.name)
        for key in ['structures', 'tanks', 'mappedPlants', 'additionalStructures']:
            for row in other.get(key, []):
                fids = row.get('sourceFids', row.get('sourceFootprintFids', []))
                for fid in list(fids)+[row.get('sourceFid'), row.get('sourceFootprintFid')]:
                    if fid is not None:
                        others.setdefault(fid, []).append(path.name)
    assert not set(own_fids).intersection(others), {fid: others[fid] for fid in set(own_fids).intersection(others)}
    # Verify against the complete author extract, when cached locally. This is
    # an authoring check only, never a routine scene-build dependency.
    full_path = ROOT/'reference/historic-building-footprints-2026-09-28/current-scene-buildings-bng.geojson'
    if full_path.exists():
        source = {f['properties']['sourceFid']: affinity.affine_transform(shape(f['geometry']),
            [1, 0, 0, -1, -538900, 183209]) for f in load(str(full_path.relative_to(ROOT)))['features']
            if f['properties']['sourceFid'] in own_fids}
        assert set(source) == set(own_fids)
        for group in register['groups']:
            for fid, rings in zip(group['sourceFids'], group['sourcePolygons']):
                assert source[fid].symmetric_difference(Polygon(rings[0], rings[1:])).area < .000001

    crown = groups['western-crown-main']
    assert crown['sourceFids'] == [609]
    assert crown['modelIds'] == ['west-230-6', 'west-230-7']
    division = crown['divisionParameters']
    widths = division['inheritedProfileWidthsMetres']
    assert division['northernWidthFraction'] == widths[1]/sum(widths)
    for ident, width in zip(crown['modelIds'], widths):
        previous_local = affinity.rotate(Polygon(prior[ident]['footprint']), -division['frameAngleDegrees'], origin=(0, 0))
        assert abs(previous_local.bounds[2]-previous_local.bounds[0]-width) < .000001
        assert 'interpreted' in rows[ident]['name']
        assert 'office' not in rows[ident]['name'] and 'shed' not in rows[ident]['name']
    source_crown = shape(load('reference/footprint-model-alignment/remaining-trades-source-shapes.json')['609'])
    whole_crown = unary_union([shapes[ident] for ident in crown['modelIds']])
    assert source_crown.symmetric_difference(whole_crown).area < .1
    assert source_crown.area > 1958 and whole_crown.area > 1958
    assert whole_crown.distance(Point(-716, 463)) > 8, 'Clear western court filled'
    old_structures = {s['id']: s for s in before['structures']}
    stacks = {s['id']: s for s in register['structures']}
    expected_stacks = {s['id'] for s in before['structures'] if s.get('siteId') in [563, 941, 230]}
    assert set(stacks) == expected_stacks and len(expected_stacks) == 4
    for ident, row in stacks.items():
        old = old_structures[ident]
        assert row['priorStructure'] == old
        assert row['parentBuildingId'] == old['parentBuildingId']
        assert row['preservedLocalPosition'] == old['localPosition']
        assert row['preservedHeight'] == old['height']
        assert 'not a transcribed OS chimney symbol' in old['positionEvidence']
        assert 'No nearby circle or small symbol' in row['review']
        assert 'sourceFid' not in row and 'sourcePolygons' not in row
        parent = shapes[row['parentBuildingId']]
        angle = math.radians(row['rotation'])
        u, v = old['localPosition']
        expected_centre = [round(round(parent.centroid.x, 3)+u*math.cos(angle)-v*math.sin(angle), 3),
                           round(round(parent.centroid.y, 3)+u*math.sin(angle)+v*math.cos(angle), 3)]
        assert row['centre'] == expected_centre
        centre = Point(row['centre'])
        half = old['radius']*1.2
        plinth = affinity.rotate(box(centre.x-half, centre.y-half, centre.x+half, centre.y+half), row['rotation'], origin=centre)
        assert parent.covers(plinth)
        if not preflight:
            actual = next(s for s in scene['structures'] if s['id'] == ident)
            assert math.dist([actual['x'], actual['z']], row['centre']) < .001
            assert actual['parentBuildingId'] == row['parentBuildingId']
            for key in ['height', 'radius', 'topRadiusRatio', 'baseHeight', 'section', 'material']:
                assert actual[key] == old[key], (ident, key)
    identities = register['siteIdentityReview']
    assert identities['siteId'] == 230 and identities['mappedRoofSourceFid'] == 609
    assert identities['mappedNorthernRoofBody'] == 'Crown Chemical Works'
    assert set(identities['matchedCrownRangeIds']) == {'west-230-3', 'west-230-4', 'west-230-6', 'west-230-7'}
    for ident in identities['unresolvedTenantRangeIds']:
        assert 'attribution unresolved' in rows[ident]['name']
    deferred = {fid for item in register['deferred'] for fid in item.get('sourceFids', [])}
    assert not deferred.intersection(own_fids)
    assert {917595, 1006894, 809090, 821004, 743842, 795218, 902909} <= deferred
    assert register['contextConflicts'][0]['modelId'] == 'west-941-5'
    assert register['contextConflicts'][0]['sourceFids'] == [30174]
    print('Western trades: seventeen complete reviewed exteriors including Crown 609, disjoint interpreted cuts, immutable profiles, global source IDs, four contained inferred shafts and deferred site identity pass.')
    # Use the strict shared clearance policy against the current reviewed
    # context, including the formerly conflicting Three Mills Lane shed.
    check_register('western-trades', expected, 12, 0, 'remaining-trades-before',
        preflight=preflight, later_registers=['ritchie-jute', 'crown-johnson'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--preflight', action='store_true')
    check(parser.parse_args().preflight)
