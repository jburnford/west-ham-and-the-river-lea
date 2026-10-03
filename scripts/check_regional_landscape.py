"""Independent source/geometry checks and solver boundary regressions."""
import hashlib
import json
from pathlib import Path

import numpy as np
import shapely
from scipy.sparse import coo_matrix
from shapely.geometry import Polygon

from build_regional_landscape import solve_correction

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'docs/data/lower-lea-region'

# Two disconnected rows stand for opposite sides of a waterway. An anchor
# on one row must not adjust the other; near values decay without a hard seam.
rows = np.r_[np.arange(4), np.arange(5,9)]
cols = rows+1
adj = coo_matrix((np.ones(16), (np.r_[rows,cols], np.r_[cols,rows])), shape=(10,10)).tocsr()
fixed = np.zeros(10,dtype=bool);fixed[0]=True
target = np.zeros(10);target[0]=4
out, error = solve_correction(adj, np.zeros(10), fixed, target, 2)
assert out[0]==4 and np.all(out[5:]==0)
assert (np.diff(out[:5])<0).all() and out[4]>0
assert error<1e-7
fixed[4]=True;target[4]=1
out,_ = solve_correction(adj, np.full(10,2.), fixed, target,2)
assert out[0]==4 and out[4]==1 and np.all(out[5:]==2)

meta=json.loads((OUT/'landscape-1900.json').read_text())
for path,digest in meta['inputHashes'].items():
    assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,path
shape=(meta['height'],meta['width'])
height=np.fromfile(OUT/meta['heightFile'],'<f4').reshape(shape)
kind=np.fromfile(OUT/meta['kindFile'],'u1').reshape(shape)
prior=np.fromfile(OUT/meta['broadReliefFile'],'<f4').reshape(shape)
distance=np.fromfile(OUT/meta['anchorDistanceFile'],'<f4').reshape(shape)
trial=np.fromfile(OUT/'elevation-trial.odn.f32','<f4').reshape(shape)
trial_support=np.fromfile(OUT/'elevation-trial.support.u8','u1').reshape(shape)
modern=np.fromfile(OUT/'terrain-2003.f32','<f4').reshape(shape)
ground=np.fromfile(OUT/meta['groundFile'],'<f4').reshape(shape)
ground_kind=np.fromfile(OUT/meta['groundKindFile'],'u1').reshape(shape)
early_weight=np.fromfile(OUT/meta['earlyMarshWeightFile'],'<f4').reshape(shape)
early_base=np.fromfile(OUT/meta['earlyMarshFile'],'<f4').reshape(shape)
assert np.array_equal(np.isfinite(height),np.isin(kind,[1,2,3,4,6,7,8,9,10,11,12,13,14]))
assert np.array_equal(np.isfinite(ground),np.isfinite(height))
assert np.array_equal(ground_kind==1,np.isfinite(trial)&(early_weight==0))
assert np.array_equal(height[kind==1],trial[kind==1])
assert np.array_equal(kind==5,trial_support==2)
assert not np.isfinite(height[kind==5]).any()
assert np.isfinite(height).sum()>np.isfinite(trial).sum()*2
assert np.isfinite(height).sum()*meta['cellSizeMetres']**2/1e6==meta['landAreaKm2']
assert np.array_equal(np.isfinite(height),(np.isfinite(modern)|np.isfinite(trial))&(trial_support!=2))
prior_weight=np.fromfile(OUT/meta['marshPriorWeightFile'],'<f4').reshape(shape)
assert np.isclose(meta['marshPriorODNMetres'],(12-1.3)*.3048)
assert not (kind==7).any(), 'Regional early evidence supersedes the isolated 12 ft patch'
assert np.max(abs(prior[early_weight==1]-early_base[early_weight==1]))<2e-6
assert (distance[kind==3]<=meta['policy']['correctionDecayMetres']).all()
assert (distance[kind==4]>meta['policy']['correctionDecayMetres']).all()
assert (distance[np.isin(kind,[1,2])]==0).all()
for c in meta['historicalControlCells']:
    assert ground_kind[c['row'],c['col']]==(14 if c['boundaryBlendWeight'] else 2)
    assert c['visibleInSurface']==bool(kind[c['row'],c['col']]==2)
    expected=c['modelGroundODNMetres'] if c['boundaryBlendWeight'] else c['heightODNMetres']
    assert abs(float(ground[c['row'],c['col']])-expected)<2e-6
assert meta['earlierMarshConstraintsApplied']==45
assert np.max(abs((ground-early_base)[kind==9]))<.8, 'Modern/non-marsh relief leaked into the regional marsh substrate'
assert np.array_equal(height[~np.isin(kind,[8,10,11,12,13])],ground[~np.isin(kind,[8,10,11,12,13])],equal_nan=True)
assert np.array_equal(ground_kind==14,(early_weight>0)&(early_weight<1)&np.isfinite(ground))
# Approximate source-domain boundaries must not become terrain escarpments.
for a,b in [(np.s_[:,:-1],np.s_[:,1:]),(np.s_[:-1,:],np.s_[1:,:])]:
    edge=((ground_kind[a]==9)&(ground_kind[b]==14))|((ground_kind[a]==14)&(ground_kind[b]==9))
    assert np.max(abs(ground[a][edge]-ground[b][edge]))<.3
assert meta['solverMaxEquationResidual']<1e-6
assert sum(c['cells'] for c in meta['counts'].values())==height.size

# Check full display faces independently, including water narrower than one
# mesh edge. Nonfinite samples and exclusions must never acquire a mesh face.
network=json.loads((ROOT/'docs/data/river-system-1900.json').read_text())
audit=json.loads((OUT/'elevation-audit.json').read_text())
water=shapely.union_all([
    Polygon([(538900+x,183209-z) for x,z in p[0]],
            [[(538900+x,183209-z) for x,z in ring] for ring in p[1:]])
    for r in network['reaches'] for p in r['polygons']]+
    [Polygon(r['polygonBNG']) for r in audit['terrainExclusions']])
# The City Mill field estimate must follow the two marsh readings, remain
# inside the reviewed compartment, and not copy the higher cottage/bank levels.
patch=next(p for p in network['bankSections']['terrainPatches'] if p['id']=='city-mill-bank-and-ground')
field=shapely.union_all([Polygon([(538900+x,183209-z) for x,z in p[0]],
    [[(538900+x,183209-z) for x,z in ring] for ring in p[1:]]) for p in patch['polygons']]).buffer(-5)
rows,cols=np.where(kind==6)
assert len(rows)>100
east=535000+(cols+.5)*10;north=187000-(rows+.5)*10
assert shapely.contains_xy(field,east,north).all()
records={r['id']:r for r in audit['records']}
low,high=[records[i] for i in ['sh_537793_184215','sh_537687_184334']]
expected=np.interp(north,[low['positionBNG'][1],high['positionBNG'][1]],
    [low['provisionalODNMetres'],high['provisionalODNMetres']])
assert np.max(abs(height[rows,cols]-expected))<2e-6
assert np.ptp(height[kind==6])<=.4*.3048+2e-6
assert height[kind==6].max()<(13.9-1.3)*.3048-.8
faces=np.fromfile(OUT/meta['displayMesh']['faceFile'],'<u4').reshape(-1,3)
assert len(faces)==meta['displayMesh']['triangleCount']
assert faces.max()<height.size and np.isfinite(height.ravel()[faces]).all()
e0,n0,e1,n1=meta['boundsBNG'];step=meta['cellSizeMetres']
xy=np.column_stack([e0+(np.arange(height.size)%shape[1]+.5)*step,
                    n1-(np.arange(height.size)//shape[1]+.5)*step])
assert not shapely.intersects(shapely.polygons(xy[faces]),water).any()
# Regression: the Pudding–City compartment is WEST of City Mill. The earlier
# eastern-field correction left this large 2003 made-ground plateau untouched.
compartment=json.loads((ROOT/'data/maps/lower-lea-region/pudding-city-marsh-1900.json').read_text())
field=shapely.from_geojson(json.dumps(compartment['geometryBNG']))
inside=shapely.contains_xy(field.buffer(-5),xy[:,0],xy[:,1]).reshape(shape)&np.isfinite(height)
assert inside.sum()>800
nominal=inside&(kind==9)
assert nominal.sum()>750
assert np.max(abs(height[nominal]-(12-1.3)*.3048))<.3
assert np.isin(kind[inside],[1,2,8,9,10,11,12,13]).all()
for e,n in [(537650,184200),(537750,184200),(537650,184100),(537750,184100),(537650,184000),(537750,184000)]:
    row,col=int((n1-n)//step),int((e-e0)//step)
    assert kind[row,col]==9,(e,n,int(kind[row,col]))
    assert abs(float(height[row,col])-(12-1.3)*.3048)<.3,(e,n,float(height[row,col]))
garden=shapely.from_geojson(json.dumps(compartment['separateSurfaces'][0]['geometryBNG']))
garden_cells=shapely.contains_xy(garden,xy[:,0],xy[:,1]).reshape(shape)&(kind==8)
assert garden_cells.sum()>=4
assert np.max(abs(height[garden_cells]-(13.9-1.3)*.3048))<2e-6
bank_cells=(kind==8)&~garden_cells
assert bank_cells.sum()>20
assert height[bank_cells].min()>(17-1.3)*.3048
assert height[bank_cells].max()<=(18.6-1.3)*.3048+2e-6
assert shapely.contains_xy(field,xy[kind.ravel()==8,0],xy[kind.ravel()==8,1]).all()
# No nominal marsh constraint reaches the works farther south.
assert not field.intersects(shapely.box(537850,183719,537943,183824))
assert field.bounds[1]>183900
# Source review is reproducible without relying on the early interpolator.
from spot_height_mosaics import pixel_to_coords
from regional_surface_layers import polygons_bng
from shapely.geometry import LineString
review=json.loads((ROOT/'data/maps/lower-lea-region/marsh-baseline-1848-review.json').read_text())
assert len(review['observations'])==57
accepted=[r for r in review['observations'] if r['baselineUse']]
assert len(accepted)==45 and all(r['role'] in ('lane-proxy','ground-margin') for r in accepted)
for r in review['observations']:
    source=json.loads((ROOT/'reference/spot-heights/mosaics-1848'/f"{r['mosaic']}.json").read_text())
    coords=pixel_to_coords(source,*r['pixel'])
    assert np.max(abs(np.array(r['positionBNG'])-np.array([coords['bng_e'],coords['bng_n']])))<.001
    for path,digest in r['sourceHashes'].items():
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest
for region in review['regions']:
    values=[r['valueFeet'] for r in accepted if r['region']==region['id']]
    assert len(values)==region['count']
    assert np.isclose(np.median(values),region['medianFeet'])
    assert [min(values),max(values)]==region['observedRangeFeet']
infra=json.loads((ROOT/'docs/data/infrastructure.json').read_text())
yards=json.loads((ROOT/'docs/data/ground-plan.json').read_text())['sites']
roads=shapely.union_all([LineString([(538900+x,183209-z) for x,z in r['route']]).buffer(r['width']/2+3) for r in infra['roads']])
yard_geometry=shapely.union_all([polygons_bng(y['polygons']) for y in yards])
rail_geometry=shapely.union_all([polygons_bng(r['footprint']) if r.get('footprint') else LineString([(538900+x,183209-z) for x,z in r['route']]).buffer(r.get('baseHalfWidth',15)) for r in infra['railways']])
sewer=json.loads((ROOT/'docs/data/ground-plan.json').read_text())['neighbourhood']['sewer']
sewer_geometry=LineString([(538900+x,183209-z) for x,z in sewer['route']]).buffer(sewer['baseWidth']/2,join_style=2)
for category,geom in [(10,roads),(11,yard_geometry),(12,water.buffer(14)),(13,shapely.union_all([rail_geometry,sewer_geometry]))]:
    cells=xy[kind.ravel()==category]
    assert len(cells)>0 and shapely.covers(geom,shapely.points(cells)).all(),category
    if category in (10,11):assert (early_weight[kind==category]==1).all()
used=set(meta['laterSurfaceLayers']['usedSourceIds'])
assert used=={id for f in meta['laterSurfaceLayers']['features'] for id in f['sourceIds']}
assert used.isdisjoint(meta['laterSurfaceLayers']['unplacedSurfaceObservationIds'])
assert all(records[id]['type']=='spot' for id in used)
for id in meta['deferredSubstrateObservationIds']:
    assert all(id not in c['ids'] for c in meta['historicalControlCells'])
# Each mesh vertex uses the shared raster value; no per-tile height offsets.
assert np.isfinite(height).any() and np.nanmin(height)>-100 and np.nanmax(height)<100
print('PASS: historical values, isolated controls, source hashes, missing masks, correction boundaries/decay, evidence classes, and water-safe 3D faces.')
