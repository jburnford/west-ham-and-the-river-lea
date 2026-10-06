"""Check connected flooding, overtopping thresholds and source integrity (whole-model grid, schema 2)."""
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.ndimage import label
from build_landscape_flood import connection_levels, fast_connection_levels
import flood_basins

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'scenes/channelsea-sewer-panorama/review'
# A low bowl behind a bank must stay dry below the bank, even though its bed is low.
bed=np.zeros((7,9));bed[:,3]=3
seeds=np.zeros_like(bed,dtype=bool);seeds[:,0]=True
threshold=connection_levels(bed,seeds)
assert threshold[3,7]==3
assert not ((threshold<2)&(np.indices(bed.shape)[1]>3)).any()
bed[3,3]=1
opened=connection_levels(bed,seeds)
assert opened[3,7]==1
# Four-neighbour connectivity must not leak diagonally through touching banks.
bed=np.array([[0,5],[5,0]],dtype=float)
assert connection_levels(bed,np.array([[1,0],[0,0]],dtype=bool))[1,1]==5
# The fast reconstruction used on the whole grid agrees with the reference, barriers included.
rng=np.random.default_rng(7)
for _ in range(20):
    b=rng.random((30,40))*5;s=rng.random(b.shape)<.03;bar=(rng.random(b.shape)<.1)&~s
    ref=connection_levels(np.where(bar,np.inf,b),s);ref[bar]=np.inf
    fast=fast_connection_levels(b,s,bar)
    assert np.array_equal(np.isinf(ref),np.isinf(fast)) and np.allclose(ref[np.isfinite(ref)],fast[np.isfinite(fast)])

# Basin hierarchy (Phase V): two hollows behind a bank, a channel beyond it. The channel's edge cell is half water but
# carries the bank crest, so the hollow behind it must spill at the crest, not at its own rim on the land side.
bed=np.full((12,20),3.0);bed[:, 15:]=0.0             # channel at 0 m from column 15
bed[2:10,2:6]=1.0;bed[2:10,8:12]=1.5                  # hollow A (1.0 m floor) and hollow B (1.5 m floor)
bed[:,6:8]=2.0                                        # saddle between them at 2.0
bed[:,14]=4.0                                         # bank crest, inside the water polygon's edge cell
inside=np.ones(bed.shape,bool);water=np.zeros(bed.shape);water[:,14]=.5;water[:,15:]=1;tidal=water.copy();kind=np.zeros(bed.shape,np.uint8)
saved=flood_basins.MIN_AREA_CELLS;flood_basins.MIN_AREA_CELLS=4
hier,land,out,tflag,enclosed=flood_basins.prepare(bed,inside,water,tidal,kind)
hier,labels,n_land,n_out,tree,pairs=flood_basins.prune(hier,land,out,log=lambda *a:None)
flood_basins.MIN_AREA_CELLS=saved
parent,child0,child1,spill,formation,spill_to,spill_from,spill_cell,attached=tree
assert n_out==1 and tflag.all()
a,b=labels[5,3]-1,labels[5,9]-1
assert a!=b and a<n_land and b<n_land
assert spill[a]==2.0 and spill[b]==2.0 and parent[a]==parent[b]
p=parent[a]
assert attached[p] and spill_to[p]==n_land and spill[p]==4.0, (spill[p],)
# Shallow hollows are filled to their rim; the stage tables are monotone and match the cells.
vol,catch=flood_basins.leaf_tables(hier,labels,n_land,0.0,int(round(5/flood_basins.STEP))+1)
assert np.all(np.diff(vol,axis=1)>=-1e-9)
k=int(round(2.0/flood_basins.STEP))
assert abs(vol[a,k]-4*(2.0-1.0)*32)<1e-6 and abs(vol[b,k]-4*(2.0-1.5)*32)<1e-6

meta=json.loads((ROOT/'docs/data/landscape-flood-1900.json').read_text())
assert meta['schemaVersion']==3
for path,digest in meta['inputHashes'].items():
    assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,path
none=meta['encoding']['none']
def levels(key,grid):
    raw=np.fromfile(ROOT/'docs/data'/meta['files'][key],dtype='<u2').reshape(meta[grid]['height'],meta[grid]['width'])
    out=raw/100-10;out[raw==none]=np.inf;return out
fb,fc=levels('fineBed','fine'),levels('fineConnection','fine')
cb,cc=levels('coarseBed','coarse'),levels('coarseConnection','coarse')
river=np.fromfile(ROOT/'docs/data'/meta['files']['fineWater'],dtype='u1').reshape(fb.shape)/255
# No water on ground above its level: a connection level is never below the ground it covers.
assert np.all(fc[np.isfinite(fc)]>=fb[np.isfinite(fc)]-0.011)
assert np.all(cc[np.isfinite(cc)]>=cb[np.isfinite(cc)]-0.011)
# The fine box is blank on the coarse grid, so no cell is drawn twice.
s=meta['coarse']['step'];x0,z0=meta['coarse']['bounds'][:2];bx0,bz0,bx1,bz1=meta['fine']['bounds']
assert np.isinf(cc[(bz0-z0)//s:(bz1-z0)//s,(bx0-x0)//s:(bx1-x0)//s]).all()
# Independent component labels on the fine grid reproduce the stored levels for the tidal cells' components.
seeds=(river>=.5)&np.isfinite(fc)&(fc<=fb+.011)
areas=[]
for stage in [1.9,2.5,3.5,4.5,5.5]:
    actual=fc<stage
    components,_=label(fb<stage)
    reached=np.unique(components[seeds&(fb<stage)]);reached=reached[reached!=0]
    # Every fine cell wet at this stage lies in a component that either holds a tidal seed or reaches the fine
    # box edge (water from the regional grid enters there).
    edge=np.zeros_like(actual);edge[0,:]=edge[-1,:]=edge[:,0]=edge[:,-1]=True
    via_edge=np.unique(components[edge&actual]);via_edge=via_edge[via_edge!=0]
    assert np.isin(components[actual],np.concatenate([reached,via_edge])).all()
    areas.append(float((actual*(fb<stage-.05)*(1-river)).sum()*meta['fine']['step']**2))
assert all(b>=a for a,b in zip(areas,areas[1:]))
table={r['stageODN']:r for r in meta['stageTable']}
assert all(table[b]['landHa']>=table[a]['landHa'] for a,b in zip(sorted(table),sorted(table)[1:]))
# Below the old low-water level only channel-edge cells may count as land.
assert table[1.9]['landHa']<2 and table[3.5]['landHa']>table[2.5]['landHa']
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'landscape-flood-numerical-checks.json').write_text(json.dumps({'status':'PASS','areaM2':meta['areaM2'],'stagesODN':[1.9,2.5,3.5,4.5,5.5],
    'fineLandM2':areas,'wholeModelHa':[table[s]['landHa'] for s in [1.9,2.5,3.5,4.5,5.5]],'legacyBoxHa':[table[s]['legacyBoxHa'] for s in [1.9,2.5,3.5,4.5,5.5]],
    'checks':['enclosed low bowl stays dry','bank overtopping threshold','opening permits lower-stage access','no diagonal leakage','fast reconstruction equals reference',
              'no water on ground above its level','fine box blank on the coarse grid','independent component validation','monotonic inundation','source hashes','basin hierarchy: saddles, bank-crest outlet cells, stage tables'],
    'interpretation':'Geometry checks, not hydraulic or historical calibration.'},indent=2)+'\n')
print('Landscape connected-inundation checks passed.',[round(a/1e4,2) for a in areas])
