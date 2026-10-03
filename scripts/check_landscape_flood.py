"""Check connected flooding, overtopping thresholds and source integrity."""
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.ndimage import label
from build_landscape_flood import connection_levels

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
meta=json.loads((ROOT/'docs/data/landscape-flood-1900.json').read_text())
shape=(meta['height'],meta['width'])
arrays={k:np.fromfile(ROOT/'docs/data'/meta['files'][k],dtype='<f4').reshape(shape) for k in ['bed','connection','riverFraction','support']}
assert all(np.isfinite(a).all() for a in arrays.values())
assert np.all(arrays['connection']>=arrays['bed'])
for path,digest in meta['inputHashes'].items():
    assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,path
assert (arrays['support']==0).any() and (arrays['support']==1).any()
seeds=arrays['riverFraction']>=.5
areas=[]
for stage in [1.9,2.5,3.5,4.5,5.5]:
    # Independent connectivity labels validate the heap's threshold formulation.
    eligible=arrays['bed']<stage
    components,_=label(eligible)
    reached_ids=np.unique(components[seeds&eligible]);reached_ids=reached_ids[reached_ids!=0]
    expected=np.isin(components,reached_ids)
    actual=arrays['connection']<stage
    assert np.array_equal(expected,actual)
    area=float((actual*(arrays['bed']<stage-.05)*(1-arrays['riverFraction'])).sum()*meta['step']**2)
    areas.append(area)
assert all(b>=a for a,b in zip(areas,areas[1:]))
assert areas[0]==0 and areas[2]>100000
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'landscape-flood-numerical-checks.json').write_text(json.dumps({'status':'PASS','areaM2':meta['areaM2'],'stagesODN':[1.9,2.5,3.5,4.5,5.5],'floodedLandM2':areas,'checks':['enclosed low bowl stays dry','bank overtopping threshold','opening permits lower-stage access','no diagonal leakage','independent component validation','monotonic inundation','source hashes','provenance retained'],'interpretation':'Geometry checks, not hydraulic or historical calibration.'},indent=2)+'\n')
print('Landscape connected-inundation checks passed.',areas)
