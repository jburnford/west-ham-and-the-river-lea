"""Check evidence eligibility, geometry, datum, and trial coverage independently."""
import copy
import hashlib
import json
from pathlib import Path

import numpy as np
import shapely
from scipy.spatial import cKDTree
from shapely.geometry import Polygon

from build_regional_elevation_audit import classify
from build_regional_elevation_trial import sample, triangulate
from regional_elevation_sources import load_supplement

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'docs/data/lower-lea-region'
audit = json.loads((OUT/'elevation-audit.json').read_text())
trial = json.loads((OUT/'elevation-trial.json').read_text())
epochs = json.loads((ROOT/'data/maps/terrain-epochs.json').read_text())
network = json.loads((ROOT/'docs/data/river-system-1900.json').read_text())
for product in [audit, trial]:
    for path, digest in product['inputHashes'].items():
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == digest, path
assert hashlib.sha256((ROOT/'data/maps/lower-lea-region/height-observations.snapshot.geojson').read_bytes()).hexdigest() == '1f3f1b90cc2b3ac090447a34067dcf282143d9886f33ab7e30238dda68efe638'
records = {r['id']:r for r in audit['records']}
added,_,exclusions,_,supplement = load_supplement(ROOT)
assert audit['summary']['baselineObservations']==3938
assert len(records) == audit['summary']['observations'] == 3938+len(added)+audit['summary']['opusAddedObservations']
assert len(added)==63
assert records['sh_537434_182618']['value_ft']==44.9  # Genuine high road beside cutting.
assert len({r['id'] for r in audit['records']})==len(audit['records'])
assert sum(r['id']=='sh_537107_184529' for r in audit['records'])==1  # Overlapping 15.9ft map reading.
for mark in added:
    assert records[mark['id']]['directSurfaceReview']
    assert records[mark['id']]['auditStatus'] in {'reviewed-ground','reviewed-road'}
assert len(exclusions)==20
assert audit['summary']['opusAddedObservations']==336
assert audit['opusUpdate']['movedIdsMatched']==44
for identifier in ['sh_537888_183583','sh_537932_183520','sh_537982_183457','sh_537567_183390','sh_538012_183391','sh_538055_183341']:
    assert records[identifier]['auditStatus']=='separate-surface'
    assert records[identifier]['surfaceFamily']=='bank-or-embankment'
# Merged coordinates must not introduce a second copy of an existing reading.
assert 'sh_539343_186840' not in records and 'sh_539342_186840' in records
assert 'sh_536601_184205' not in records  # Near the reviewed 47.8ft dot; withheld.
assert sum(audit['summary']['auditStatuses'].values()) == len(records)
assert records['sh_537672_185146']['auditReasons'][:2] == ['confirmed-duplicate','review-withheld']
# Regressions: a street is useful surface evidence; a deck/BM is not ground;
# unresolved digits, a wrong epoch or a water-overlapped dot need review.
street = copy.deepcopy(next(r for r in records.values() if r['auditStatus']=='candidate-road'))
source = {'setting_source':'reader'}
assert classify(street,source,epochs)[0]=='candidate-road'
bad = dict(street,confidence='low')
assert classify(bad,source,epochs)[0]=='road-needs-review'
bad = dict(street,layer='os-london-skeleton-5280')
assert 'epoch-not-allowed' in classify(bad,source,epochs)[1]
assert classify(street,source,epochs,True)[0]=='road-needs-review'
assert classify(dict(street,type='bench_mark'),source,epochs)[0]=='separate-surface'
assert classify(dict(street,setting='bridge'),source,epochs)[0]=='separate-surface'
assert classify(dict(street,setting='embankment_top'),source,epochs)[0]=='separate-surface'
assert classify(street,{'setting_source':'inferred'},epochs)[0]=='inferred-road'
# Keep resolved ground-surface conflicts and City Mill's formerly withheld dots.
assert records['sh_538960_182471']['auditStatus']=='reviewed-ground'
assert records['sh_539032_182447']['auditStatus']=='reviewed-ground'
for identifier in ['sh_538062_184289','sh_538137_184254']:
    assert records[identifier]['auditStatus']=='reviewed-road'
assert all(not m['name'].startswith('s18_') for m in audit['cachedPeriodMosaics'])
assert next(c for c in audit['reviewPriorityCells'] if c['id']=='536500-184000')['cachedMosaics']
for identifier in ['sh_537687_184334','sh_537793_184215']:
    assert records[identifier]['auditStatus']=='reviewed-ground'

for identifier,original in [('sh_537095_184901','street'),('sh_537146_184841','open_ground')]:
    assert records[identifier]['sourceSetting']==original
    assert records[identifier]['setting']=='embankment_top'
    assert records[identifier]['auditStatus']=='separate-surface'
for identifier in ['sh_537448_185530','sh_537519_185495','sh_537817_185541','sh_537737_185522']:
    assert records[identifier]['auditStatus']=='reviewed-road'

# A direct track review resolves one source surface conflict without erasing
# that flag or bypassing confidence and water checks.
track = records['sh_537933_185280']
assert track['sourceSetting']=='marsh' and track['setting_conflict']
assert track['setting']=='street' and track['auditStatus']=='reviewed-road'
assert classify(dict(track,confidence='low'),source,epochs)[0]=='road-needs-review'
assert classify(track,source,epochs,True)[0]=='road-needs-review'
unresolved = dict(track,regionalSurfaceReview={})
assert 'surface-conflict' in classify(unresolved,source,epochs)[1]
for identifier in ['sh_538093_185578','sh_538122_185509','sh_538165_185318',
                   'sh_538096_185297','sh_537773_185267','sh_537854_185282']:
    assert records[identifier]['auditStatus']=='reviewed-road'

controls = trial['controls']
assert len({r['id'] for r in controls}) == len(controls)
assert {r['family'] for r in controls} == {'road','ground'}
assert len(controls) == audit['summary']['usableSurfaceCandidates']
for c in controls:
    r = records[c['id']]
    assert not r['mappedWaterOverlap'] and not r['auditReasons']
    assert abs(c['heightODNMetres']-(r['value_ft']-1.3)*.3048)<1e-6
assert 'sh_540148_182306' in {c['id'] for c in controls}  # Low Chargeable Lane dot retained.

water = shapely.union_all([
    Polygon([(538900+x,183209-z) for x,z in p[0]],
            [[(538900+x,183209-z) for x,z in ring] for ring in p[1:]])
    for reach in network['reaches'] for p in reach['polygons']])
water = shapely.union_all([water,*[Polygon(r['polygonBNG']) for r in audit['terrainExclusions']]])
assert all(r['areaM2']>0 for r in audit['terrainExclusions'])
xy = np.array([c['positionBNG'] for c in controls])
values = np.array([c['heightODNMetres'] for c in controls])
indices = np.array(trial['acceptedTriangles'])
vertices = xy[indices]
assert not shapely.intersects(shapely.polygons(vertices),water).any()
assert np.linalg.norm(vertices-np.roll(vertices,1,axis=1),axis=2).max()<=trial['maximumTriangleEdgeMetres']+1e-7
e0,n0,e1,n1 = trial['boundsBNG']
step = trial['cellSizeMetres']
east,north = np.meshgrid(np.arange(e0+step/2,e1,step),np.arange(n1-step/2,n0,-step))
grid = np.column_stack([east.ravel(),north.ravel()])
heights = np.fromfile(OUT/trial['heightFile'],dtype='<f4')
support = np.fromfile(OUT/trial['supportFile'],dtype='u1')
assert len(heights)==len(support)==trial['width']*trial['height']
assert np.array_equal(np.isfinite(heights),support==1)
wet = shapely.intersects(shapely.points(grid),water)
assert np.array_equal(wet,support==2)
for exclusion in audit['terrainExclusions']:
    assert shapely.covers(water,Polygon(exclusion['polygonBNG']).representative_point())
assert heights[np.isfinite(heights)].min()>=values.min()-1e-5
assert heights[np.isfinite(heights)].max()<=values.max()+1e-5
# Independent plane calculation at every supported raster cell. Vertices shared
# by adjacent triangles use the same control values, preventing height seams.
surface_domain = shapely.union_all(shapely.polygons(vertices))
assert shapely.covers(surface_domain,shapely.points(grid[support==1])).all()
tin,h,ok,_,_ = triangulate([records[c['id']] for c in controls],water)
centroids = vertices.mean(axis=1)
assert np.max(abs(sample(tin,h,ok,centroids)-values[indices].mean(axis=1)))<1e-7
rendered = sample(tin,h,ok,grid)
assert np.array_equal(np.isfinite(rendered),np.isfinite(heights))
assert np.nanmax(abs(rendered-heights))<2e-6
# Evidence-distance rasters have matching orientation and distinguish the gain
# from street evidence without pretending to measure vertical uncertainty.
g = audit['grid'];s = g['cellSizeMetres']
ex,ny = np.meshgrid(np.arange(e0+s/2,e1,s),np.arange(n1-s/2,n0,-s))
q = np.column_stack([ex.ravel(),ny.ravel()])
distances = np.fromfile(OUT/g['surfaceDistanceFile'],dtype='<f4')
expected = cKDTree(xy).query(q)[0]
assert np.max(abs(expected-distances))<.001
ground = np.fromfile(OUT/g['distanceFile'],dtype='<f4')
assert (distances<=ground+.001).all()
validation = trial['validation']['observations']
assert {r['id'] for r in validation}=={c['id'] for c in controls}
assert all(r['fold']==int(hashlib.sha256(r['id'].encode()).hexdigest()[:8],16)%5 for r in validation)
assert audit['existingTerrain']['patchCount']==8
assert len(audit['existingTerrain']['patchControlIds'])==24
print('PASS: eligibility (including streets), dates/datum, immutable source, all water/long-edge exclusions, raster support and continuity, distance coverage, holdout accounting, existing patch inventory.')
