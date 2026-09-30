"""Check the eastern upper-strip additions and explicit platform exclusions."""
import argparse
from pathlib import Path

from shapely.geometry import Polygon, shape
from shapely.ops import unary_union

from factory_alignment_checks import check_register, load
from prepare_east_channelsea_upper_alignment import BASELINE, CACHE, SPECS, SITE_NAMES
from prepare_ink_works_alignment import rings
from prepare_three_mills_north_alignment import polygon

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--preflight', action='store_true')
args = parser.parse_args()
r = load('data/maps/east-channelsea-upper-footprint-alignment.json')
before = load(BASELINE)
scene = load('docs/data/factory-buildings.json')
expected = {'east-upper-'+key for key, *_ in SPECS}
pending_water = {'east-upper-victoria-corn-main', 'east-upper-caledonian-riverside'}
# Authoring checks permit only these explicitly identified bank conflicts.
# Published checks require the independently reviewed bank to clear both roofs.
check_register('east-channelsea-upper', expected, len(SPECS), 0,
    'east-channelsea-before', preflight=args.preflight,
    permitted_water=pending_water if args.preflight else (),
    later_registers=['east-channelsea-south'])
assert r['baseline'] == BASELINE and r['structures'] == []
assert not any(r.get(k) for k in ['removedBuildings', 'removedStructures',
    'mapTracedBuildings', 'locallyTransferredBuildings', 'additionalStructures',
    'renderChanges', 'roadRenderChanges'])
old_ids = {b['id'] for b in before['buildings']}
assert not expected.intersection(old_ids)
additions = {b['id']: b for b in r['additionalBuildings']}
rows = {b['modelId']: b for b in r['buildings']}
assert set(additions) == set(rows) == expected
old_sites = {s['id'] for s in before['sites']}
assert {s['id']: s['name'] for s in r['additionalSites']} == {
    site: name for site, name in SITE_NAMES.items() if site not in old_sites}
assert {c['id'] for c in r['additionalSites']}.isdisjoint(old_sites)
source = load(CACHE)
by_group = {g['id']: g for g in r['groups']}
for key, site, fids, name, height, floors, evidence in SPECS:
    ident = 'east-upper-'+key
    c, b, g = rows[ident], additions[ident], by_group[ident]
    assert b['siteId'] == c['siteId'] == site and b['name'] == c['name'] == name
    assert g['modelIds'] == [ident] and g['sourceFids'] == fids
    assert g['additional'] is True and g['previousUnionIoU'] == 0
    assert c['additionalModel'] is True and c['priorFootprint'] == []
    assert g['sourcePolygons'] == [rings(polygon(shape(source[str(fid)]))) for fid in fids]
    assert c['worldFootprint'] == b['worldFootprint'] and c['worldHoles'] == b['worldHoles']
    assert c['preservedHeight'] == b['eavesHeight'] == height
    assert b['storeysEstimate'] == floors
    for key, field in [('roofRise','preservedRoofRise'), ('roofAxis','preservedRoofAxis'), ('roofBays','preservedRoofBays')]:
        assert b[key] == c[field]
    assert 'interpreted' in b['heightEvidence'].lower() and 'estimate' in b['heightEvidence'].lower()
    assert 'interpreted' in b['roofEvidence'].lower()
    body = Polygon(b['worldFootprint'], b['worldHoles'])
    assert body.is_valid and body.area > 20
# No platform/holder/railfan polygons may enter the enclosed-roof groups.
fids = {fid for g in r['groups'] for fid in g['sourceFids']}
assert not fids.intersection({2832,1539,4882,3020,1686,1703,1103852})
assert {2832,1539} <= {fid for d in r['deferred'] for fid in d.get('sourceFids',[])}
assert {model for c in r['pendingContext'] for model in c['modelIds']} == pending_water
# Include independently fitted structures when checking global source IDs.
used = set()
for path in sorted((ROOT/'data/maps').glob('*footprint-alignment.json')):
    if path.name == 'east-channelsea-upper-footprint-alignment.json':
        continue
    other = load(str(path.relative_to(ROOT)))
    for group in other.get('groups', other.get('buildings',[])):
        used.update(group.get('sourceFids',[group.get('sourceFid')]))
    for key in ['structures','tanks','mappedPlants','additionalStructures']:
        for c in other.get(key,[]):
            used.update(c.get('sourceFootprintFids',[c.get('sourceFid',c.get('sourceFootprintFid'))]))
assert fids.isdisjoint(used)
if not args.preflight:
    actual = {b['id']: b for b in scene['buildings']}
    sites = {s['id']: s for s in scene['sites']}
    for site in r['additionalSites']:
        assert sites[site['id']]['name'] == site['name']
    for ident, c in additions.items():
        b = actual[ident]
        assert b['siteId'] == c['siteId'] and b['height'] == c['eavesHeight']
        assert b['material'] == c['material'] and b['roof'] == c['roof']
        assert b['heightEvidence'] == c['heightEvidence'] and b['roofEvidence'] == c['roofEvidence']
print(f'Eastern upper strip: {len(SPECS)} source-linked additions, {len(r["additionalSites"])} named sites, declared elevation estimates, platform/working-yard exclusions and globally unique source IDs pass.'+
      (' Two explicit river-bank conflicts require independent context reconciliation before published checks.' if args.preflight else ''))
