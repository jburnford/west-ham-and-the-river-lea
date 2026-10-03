#!/usr/bin/env python3
"""Check epoch isolation, supported heights, preserved features and mesh coverage."""
import copy
import hashlib
import json
import os
from pathlib import Path

os.environ.setdefault('MPLCONFIGDIR', '/tmp/historic-elevation-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import Polygon, box, shape
from shapely.ops import unary_union

from historic_elevation import apply_grid, sample_grid, select_controls

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'reference/topography-research-2026-09-28/terrain-epochs'
DATA = ROOT/'docs/data'
config = json.loads((ROOT/'data/maps/terrain-epochs.json').read_text())
meta = json.loads((DATA/'terrain-1900.json').read_text())
audit = np.load(OUT/'1900-audit.npz')
catalogue = json.loads((OUT/'1900-observations.json').read_text())
controls = select_controls(catalogue['observations'], config, '1900')
assert len(controls) == 13
assert all(p['type']=='spot' and p['layer']=='os-london-five-foot-1893' for p in controls)
assert meta['geometryEpoch']=='1900' and not meta['floodReady']
assert meta['floodScenarios'][0]['waterLevelODNMetres'] is None
for path, expected in meta['inputHashes'].items():
    assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==expected, f'Stale overlay: rebuild after {path}'

# Same location at a different date stays a distinct observation, and cannot
# influence 1900 even if its value is radically different.
earlier = {**controls[0], 'id': 'sk_test', 'layer': 'os-london-skeleton-5280', 'value_ft': 100}
assert select_controls(catalogue['observations']+[earlier], config, '1900') == controls
bad = copy.deepcopy(config)
bad['epochs']['1900']['controlIds'] = ['sk_test']
try:
    select_controls([earlier], bad, '1900')
    raise AssertionError('Earlier observation leaked into 1900')
except ValueError:
    pass
try:
    select_controls(catalogue['observations'], config, '1850')
    raise AssertionError('1900 geometry was allowed for 1850')
except ValueError:
    pass
for field, value in [('type', 'bench_mark'), ('setting', 'wall_top'), ('disputed', True), ('confidence', 'low'), ('setting_conflict', True)]:
    changed = copy.deepcopy(controls)
    changed[0][field] = value
    try:
        select_controls(changed, config, '1900')
        raise AssertionError(f'Unsafe ground control: {field}')
    except ValueError:
        pass

baseline, final, weight = audit['baseline'], audit['final'], audit['weight']
assert np.isfinite(final).all() and weight.min()==0 and weight.max()==1
assert np.array_equal(final[weight==0], baseline[weight==0])
assert not weight[audit['protected']].any()
assert not any(edge.any() for edge in [weight[0],weight[-1],weight[:,0],weight[:,-1]])
odn = np.fromfile(DATA/meta['files']['odn'], dtype='<f4').reshape(final.shape)
assert np.array_equal(np.isfinite(odn), weight>=.999)
assert np.allclose(odn[weight>=.999], (final+config['verticalReference']['odnMinusSceneYMetres'])[weight>=.999], atol=1e-6)
source_heights = [(p['value_ft']+config['verticalReference']['liverpoolToNewlynFeet'])*.3048 for p in controls]
field_odn=odn[~audit['drainage'] & ~audit['road']]
assert np.nanmin(field_odn)>=min(source_heights)-.002 and np.nanmax(field_odn)<=max(source_heights)+.002

# Compartments are independent of the larger export rectangle: no ground
# adjustment in the gap across Manor Road or beyond the old Mill Mead domain.
x0,z0,x1,z1 = meta['bounds']
xx,zz = np.meshgrid(np.arange(x0,x1+1),np.arange(z0,z1+1))
domain_union = unary_union([box(*d['bounds']) for d in meta['interpolationDomains']])
from shapely import contains_xy
assert not weight[~contains_xy(domain_union,xx,zz)].any()
assert not weight[(xx>200)&(xx<275)&(zz>515)&(zz<720)&~audit['road']].any()
assert len(meta['interpolationDomains'])==5
for c in meta['controls']:
    if c['sourceSettingConflict']:
        assert c['surfaceConflictResolution']['useAs']=='adjacent-ground-approximation'

# Mesh covers exactly the piece removed from the existing flat floor. This
# catches holes/overlaps, not merely finite coordinates.
network = json.loads((DATA/'river-network.json').read_text())
old_ground = unary_union([Polygon(p[0], p[1:]) for p in network['baseGround']])
new_ground = unary_union([Polygon(p[0], p[1:]) for p in meta['replacementBaseGround']])
extension = old_ground.intersection(domain_union)
assert new_ground.union(extension).symmetric_difference(old_ground).area<1e-5
vertices = np.fromfile(DATA/meta['files']['extension'], dtype='<f4').reshape(-1,3,3)
cross = np.cross(vertices[:,1]-vertices[:,0],vertices[:,2]-vertices[:,0])[:,1]
assert cross.min()>=-1e-6
assert abs(cross.sum()/2-extension.area)<.05

# The same overlay leaves every channel/structure-protected vertex unchanged.
positions = np.fromfile(DATA/'river-network.f32',dtype='<f4').reshape(-1,3)
transformed = apply_grid(positions[:,1],positions[:,0],positions[:,2],audit['target'],weight,meta['bounds'])
outside = (positions[:,0]<meta['bounds'][0]) | (positions[:,0]>meta['bounds'][2]) | (positions[:,2]<meta['bounds'][1]) | (positions[:,2]>meta['bounds'][3])
assert np.array_equal(transformed[outside], positions[outside,1])
assert np.max(abs(final-baseline))<2
# Independent source readings not used to fit the eastern zone. These are
# unmade path/plot margins, so they check local consistency, not absolute datum
# accuracy or the entire district's error. Native source crops were reviewed.
held_out = []
for key in ['sh_539261_182554', 'sh_539334_182552', 'sh_539365_182550']:
    assert key not in config['epochs']['1900']['controlIds']
    p = next(p for p in catalogue['observations'] if p['id']==key)
    assert p['type']=='spot' and p['confidence']=='high' and not p['disputed']
    x,z = p['bng_e']-538900,183209-p['bng_n']
    observed = (p['value_ft']+config['verticalReference']['liverpoolToNewlynFeet'])*.3048
    modelled = float(sample_grid(final,meta['bounds'],1,x,z))+meta['verticalReference']['odnMinusSceneYMetres']
    assert sample_grid(weight,meta['bounds'],1,x,z)>.999
    assert abs(modelled-observed)<.2
    held_out.append({'id':key,'observedODNMetres':observed,'modelledODNMetres':modelled,
                     'residualMetres':modelled-observed,'sourceSettingConflict':p.get('setting_conflict'),
                     'interpretation':'Unmade path/plot margin; independent local comparison, not exact field-ground or datum validation'})
report = {'status':'PASS', 'checks':['source hashes', 'no cross-epoch mixing', '1850 geometry guard',
          'benchmark/wall/disputed/low-confidence exclusions', 'protected features unchanged',
          'zero change at trial boundary', 'NaN outside supported ODN export', 'extension ground coverage and winding',
          'network outside trial unchanged', 'separate interpolation compartments',
          'reviewed marsh/path approximations retain source conflicts', 'three held-out local height comparisons'],
          'heldOutComparisons':held_out, 'supportedAreaM2':meta['supportedAreaM2'],
          'affectedAreaM2':meta['affectedAreaM2'], 'changeRangeMetres':meta['changeRangeMetres'],
          'maskedControlIds':[p['id'] for p in meta['controls'] if p['appliedWeightAtObservation']<.999],
          'maskedControlNote':'Measured ground falls within interpreted infrastructure protection/transition; these points constrain adjacent open ground but are not fitted at the protected locations.'}
(OUT/'checks.json').write_text(json.dumps(report,indent=2)+'\n')

fig, axes = plt.subplots(1,3,figsize=(14,8),constrained_layout=True)
x0,z0,x1,z1 = meta['bounds']
for ax, values, title, cmap, lo, hi in zip(axes,
        [np.where(weight>0,final+meta['verticalReference']['odnMinusSceneYMetres'],np.nan),final-baseline,weight],
        ['1900 ground trial (m ODN)', 'Change from scene scaffold (m)', 'Historical-ground support / blend'],
        ['terrain','RdBu_r','viridis'],[.7,-1.1,0],[2.2,1.1,1]):
    im = ax.imshow(values,extent=[x0,x1,z1,z0],cmap=cmap,vmin=lo,vmax=hi,interpolation='nearest')
    ax.set(title=title,xlabel='Scene x, east (m)',ylabel='Scene z, south (m)')
    for c in meta['controls']:
        ax.plot(*c['position'],'k+',markersize=7)
    fig.colorbar(im,ax=ax,shrink=.6)
fig.savefig(OUT/'1900-terrain-review.png',dpi=150)
plt.close(fig)
print(json.dumps(report,indent=2))
