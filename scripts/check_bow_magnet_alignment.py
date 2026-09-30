"""Focused Bow Bridge/Magnet Wharf saved/runtime source geometry checks."""
import argparse

from shapely.geometry import Polygon
from factory_alignment_checks import check_register, load

parser = argparse.ArgumentParser()
parser.add_argument('--preflight', action='store_true')
args = parser.parse_args()
expected = {f'site789-os-{i}' for i in range(1, 10)} | {f'site788-os-{i}' for i in range(1, 5)}
check_register('bow-magnet', expected, 12, 0, 'soap-wharves-before',
               preflight=args.preflight, later_registers=('cook-soap', 'lime-works'))
r = load('data/maps/bow-magnet-footprint-alignment.json')
cs = {c['modelId']: c for c in r['buildings']}
assert not r['structures'] and not r.get('removedBuildings')
assert cs['site789-os-4']['preservedHeight'] == 3.8
assert cs['site788-os-4']['preservedHeight'] == 3.8
seam = next(g for g in r['groups'] if g['id'] == 'magnet-east')['sourceReconciliation']
assert 2.27 < seam['removedAreaM2'] < 2.28
parts = [Polygon(cs[f'site789-os-{i}']['worldFootprint'], cs[f'site789-os-{i}']['worldHoles']) for i in [3, 4]]
assert parts[0].intersection(parts[1]).area < .001
wing = Polygon(cs['site788-os-4']['worldFootprint'], cs['site788-os-4']['worldHoles'])
assert 81 < wing.area < 83
print('Bow/Magnet: complete source exteriors, open court edges, low roof compartments and recorded foundry seam pass.')
