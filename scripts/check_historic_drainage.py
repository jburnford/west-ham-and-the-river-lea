"""Check physical rendering, period isolation and unconfirmed flood connections."""
import json
from pathlib import Path
import numpy as np
from shapely.geometry import LineString,Point,Polygon,box
from shapely.ops import unary_union
from historic_drainage import evidence,apply_section
from historic_elevation import apply_grid

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'docs/data'
meta=json.loads((DATA/'terrain-1900.json').read_text())
d=json.loads((DATA/meta['drainageFile']).read_text())
fresh=evidence()
for key in ['features','sluices','connections','inputHashes']:assert d[key]==fresh[key]
assert d['geometryEpoch']=='1900' and not d['floodReady']
assert len(d['sluices'])==4
assert all(s['invertODNMetres'] is None and s['gateOperation'] is None for s in d['sluices'])
assert all(not c['hydraulicallyEnabled'] for c in d['connections'])
assert not d['renderedReach']['boundaryIsPhysical']
assert d['renderedReach']['hydraulicConnection'] is None
for epoch in ['1850','1888','1897','1904','1928']:
    try:apply_section(epoch,np.zeros((1,1)),np.zeros((1,1)),np.zeros((1,1)),np.ones((1,1)))
    except ValueError:pass
    else:raise AssertionError('Drainage silently reused for another epoch')
a=np.load(ROOT/'reference/topography-research-2026-09-28/terrain-epochs/1900-audit.npz')
mask=a['drainage'];assert mask.any() and (a['weight'][mask]>=.999).all()
assert not (mask&a['protected']).any()
export=np.fromfile(DATA/meta['files']['drainageMask'],dtype='u1').reshape(mask.shape)
assert np.array_equal(export,mask)
line=LineString(d['renderedReach']['route']);spec=d['sectionAssumptions']
assert 200<line.length<210
for c in meta['controls']:
    assert line.distance(Point(c['position']))>spec['topWidthMetres']/2
mesh=np.fromfile(DATA/meta['files']['extension'],dtype='<f4').reshape(-1,3)
expected=apply_grid(np.full(len(mesh),-.1),mesh[:,0],mesh[:,2],a['target'],a['weight'],meta['bounds'])
assert np.allclose(mesh[:,1],expected,atol=2e-6)
water=np.array(d['waterTriangles'])
cross=np.cross(water[:,1]-water[:,0],water[:,2]-water[:,0])[:,1]
assert cross.min()>-1e-8 and cross.sum()>0
wet=unary_union([Polygon(face[:,[0,2]]) for face in water])
assert wet.difference(box(*spec['renderBounds'])).area<1e-6
assert wet.difference(line.buffer(spec['topWidthMetres']/2+1)).area<1e-6
assert np.allclose(water[:,:,1],d['renderedReach']['waterSceneY']+.003)
# A constant illustrative water level sits above the bed and below field rims.
assert d['renderedReach']['bedSceneY']<d['renderedReach']['waterSceneY']
assert not np.isnan(a['final'][mask]).any()
result={'status':'PASS','renderedLengthMetres':line.length,'waterAreaM2':wet.area,
        'modifiedGridNodes':d['renderedReach']['modifiedGridNodes'],
        'checks':['source trace reproducible','other epochs rejected','unverified connections disabled',
                  'structures protected','controls outside excavation','exported section mask',
                  'rendered bed matches exported grid','water clipped to rendered bed and model boundary']}
(ROOT/'reference/topography-research-2026-09-28/terrain-epochs/drainage-checks.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
