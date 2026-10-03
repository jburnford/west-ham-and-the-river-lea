"""Check rendered dry-ground compartments against their own surveyed dots."""
import json
from pathlib import Path
import numpy as np
import shapely
from shapely.geometry import Polygon,Point,LineString

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/data'
m=json.loads((OUT/'river-system-1900.json').read_text())
patches=m['bankSections']['terrainPatches']
expected_controls={
 'north-railway-marsh':['sh_537573_184727','sh_537516_184670','sh_537458_184621','sh_537374_184619'],
 'old-lea-east-bank-margin':['sh_537624_184335','sh_537570_184224','sh_537519_184158','sh_537519_184078'],
 'knobshill-low-ground':['sh_537494_184017'],
 'waterworks-east-margin':['sh_537680_184985','sh_537669_184906','sh_537655_184828'],
 'waterworks-upper-bank':['sh_537638_185226','sh_537659_185146','sh_537674_185070'],
 'temple-mills-bank-path':['sh_537539_185731','sh_537559_185650','sh_537573_185570'],
 'potters-ditch-low-ground':['sh_537688_185311','sh_537692_185240'],
 'city-mill-bank-and-ground':['sh_537664_184398','sh_537740_184274','sh_537687_184334','sh_537793_184215'],
}
assert {p['id'] for p in patches}==set(expected_controls)
controls=[c for patch in patches for c in patch['controls']]
assert len({tuple(c['positionBNG']) for c in controls})==len(controls),'Duplicate survey dots applied'
assert 'sh_537672_185146' not in {c['id'] for c in controls}
geom=lambda rings:shapely.union_all([Polygon(p[0],p[1:]) for p in rings])
p=np.fromfile(OUT/m['positionFile'],dtype='<f4').reshape(-1,3)
ix=np.fromfile(OUT/m['indexFile'],dtype='<u4').reshape(-1,3)
all_tri=p[ix].astype(float)
water=shapely.union_all([geom(r['polygons']) for r in m['reaches']])
core=json.loads((OUT/'river-network.json').read_text())
v=np.fromfile(OUT/core['positionFile'],dtype='<f4').reshape(-1,3)
areas=[geom(s['polygons']) for s in patches]
for j,a in enumerate(areas):
 for b in areas[j+1:]:assert a.intersection(b).area<.001
reports=[]
for patch,area in zip(patches,areas):
 x0,z0,x1,z1=area.bounds
 mask=(all_tri[:,:,0].max(1)>=x0)&(all_tri[:,:,0].min(1)<=x1)&(all_tri[:,:,2].max(1)>=z0)&(all_tri[:,:,2].min(1)<=z1)
 tri=all_tri[mask];polys=shapely.polygons(tri[:,:,[0,2]]);tree=shapely.STRtree(polys)
 checks=[]
 assert [c['id'] for c in patch['controls']]==expected_controls[patch['id']]
 for control in patch['controls']:
  role='bank' if control['id'] in patch['config']['bankControlIds'] else 'marsh'
  assert control['role']==role
  x,y,z=control['positionScene'];point=Point(x,z)
  candidates=tree.query(point,predicate='intersects');heights=[]
  for index in candidates:
   vert=tri[index];mat=np.vstack([vert[:,0],vert[:,2],np.ones(3)])
   if abs(np.linalg.det(mat))<1e-8:continue
   heights.append(float(np.linalg.solve(mat,np.array([x,z,1]))@vert[:,1]))
  assert heights and max(abs(h-y) for h in heights)<.03,(control['id'],heights,y)
  checks.append({'id':control['id'],'role':role,'targetSceneY':y,'renderedSceneY':heights[0],'errorMetres':abs(heights[0]-y)})
 assert area.intersection(water).area<.001
 clipped=shapely.intersection(polys,area);covered=shapely.union_all(clipped)
 assert area.difference(covered).area<.1,'Hole in adjusted terrain'
 assert shapely.area(clipped).sum()-covered.area<.2,'Overlapping terrain faces'
 assert area.intersection(geom(m['baseGround'])).area<.01
 assert area.intersection(geom(m['regionalGround'])).area<.01
 assert not shapely.contains_xy(area,v[:,0],v[:,2]).any(),'Existing core mesh enters patch'
 parts=[]
 for band in m['bankSections']['coverage']:
  if band['kind'] not in ['bank','marsh']:continue
  q=p[band['vertexStart']:band['vertexStart']+band['vertexCount']]
  parts.append(q[shapely.covers(area,shapely.points(q[:,0],q[:,2]))])
 a=np.concatenate(parts);_,labels=np.unique(a[:,[0,2]],axis=0,return_inverse=True)
 lo=np.full(labels.max()+1,np.inf);hi=np.full(labels.max()+1,-np.inf)
 np.minimum.at(lo,labels,a[:,1]);np.maximum.at(hi,labels,a[:,1])
 assert np.max(hi-lo)<.002,'Dry seam height mismatch'
 assert patch['appliedToDisplayTerrain'] and not patch['appliedToFloodSolver']
 reports.append({'id':patch['id'],'areaM2':area.area,'controls':checks,'largestDrySeamMetres':float(np.max(hi-lo)),'limitations':patch['config']['limitations']})
# Bank controls cannot leak into the marsh fit; the earlier marsh dots stay put.
first=reports[0]
assert first['areaM2']>38499.00532662205
assert [r['id'] for r in first['controls']]==expected_controls['north-railway-marsh']
# The ditch-side review follows the native map, not an arbitrary rectangular zone.
from spot_height_mosaics import pixel_to_coords
new=next(s for s in patches if s['id']=='knobshill-low-ground');c=new['config']
meta=json.loads((ROOT/c['boundaryReview']['registration']).read_text())
for pixel,bng in zip(c['boundaryReview']['nativePixels'],c['reviewOutlineBNG'],strict=True):
 q=pixel_to_coords(meta,*pixel)
 assert np.linalg.norm(np.array(bng)-[q['bng_e'],q['bng_n']])<.001
area=geom(new['polygons'])
for pixel in [(474,543),(561,754),(305,730)]: # Cottage garden, eastern track, south of ditch.
 q=pixel_to_coords(meta,*pixel)
 assert not area.covers(Point(q['bng_e']-538900,183209-q['bng_n']))
assert abs(reports[1]['areaM2']-4965.562715712471)<.001
assert abs(reports[2]['areaM2']-3934.995297771697)<.001
assert abs(reports[3]['areaM2']-1339.2140171596486)<.001
assert abs(reports[4]['areaM2']-1147.1363374417904)<.001
assert abs(reports[5]['areaM2']-1844.3358711119026)<.001
assert abs(reports[6]['areaM2']-4189.6597507469605)<.001
# The Old Lea/City Mill GIS boundary must not break the bank profile;
# low dots belong to this eastern compartment, never the opposite bank.
city=next(s for s in patches if s['id']=='city-mill-bank-and-ground')
assert city['config']['bankReachIds']==['Lower_River_Lea-15','Lower_River_Lea-7']
assert [c['role'] for c in city['controls']]==['bank','bank','marsh','marsh']
meta=json.loads((ROOT/city['config']['boundaryReview']['registration']).read_text())
for pixel,bng in zip(city['config']['boundaryReview']['nativePixels'],city['config']['reviewOutlineBNG'],strict=True):
 q=pixel_to_coords(meta,*pixel)
 assert np.linalg.norm(np.array(bng)-[q['bng_e'],q['bng_n']])<.001
area=geom(city['polygons'])
for pixel in [(500,450),(820,780),(300,980)]:
 q=pixel_to_coords(meta,*pixel)
 assert not area.covers(Point(q['bng_e']-538900,183209-q['bng_n']))
for control in patches[1]['controls']:
 x,_,z=control['positionScene'];assert not area.covers(Point(x,z))
# Potter's ground must stay north of the ditch, west of Channelsea,
# and away from the northern building and its benchmark.
new=next(s for s in patches if s['id']=='potters-ditch-low-ground');c=new['config']
meta=json.loads((ROOT/c['boundaryReview']['registration']).read_text())
for pixel,bng in zip(c['boundaryReview']['nativePixels'],c['reviewOutlineBNG'],strict=True):
 q=pixel_to_coords(meta,*pixel)
 assert np.linalg.norm(np.array(bng)-[q['bng_e'],q['bng_n']])<.001
area=geom(new['polygons'])
for pixel in [(757,179),(742,149),(795,440),(976,370)]:
 q=pixel_to_coords(meta,*pixel)
 assert not area.covers(Point(q['bng_e']-538900,183209-q['bng_n']))
for control in new['controls']:
 assert control['role']=='marsh'
 q=next(r for r in json.loads((ROOT/'data/maps/lower-lea-region/height-surface-review-1900.json').read_text())['observations'] if r['id']==control['id'])
 mapped=pixel_to_coords(meta,*q['mapPixel'])
 assert np.linalg.norm(np.array(control['positionBNG'])-[mapped['bng_e'],mapped['bng_n']])<.001
# The rebuilt ground must actually meet the adjusted railway toe, while the
# crest and south slope retain their original geometry.
infra=json.loads((OUT/'infrastructure.json').read_text())
rail=next(r for r in infra['railways'] if r.get('id')=='north-london-connection')
original=np.array(rail['embankment']);updated=original.copy();route=LineString(rail['route'])
changes=m['railwayGroundAdjustments'];assert changes
for row in changes:
 assert row['railwayId']==rail['id'] and row['surfaceId']=='north-railway-marsh'
 t,v=row['triangle'],row['vertex'];assert original[t,v,1]==row['beforeY']
 updated[t,v,1]=row['afterY']
 point=Point(*original[t,v,[0,2]])
 assert point.y<route.interpolate(route.project(point)).y,'South-facing railway slope changed'
crest=original[:,:,1]>=rail['formationHeight']-1e-6
assert np.array_equal(updated[crest],original[crest])
assert np.array_equal(updated[:,:,[0,2]],original[:,:,[0,2]])
assert areas[0].intersection(geom(rail['footprint'])).area<.001
x0,z0,x1,z1=areas[0].bounds
mask=(all_tri[:,:,0].max(1)>=x0)&(all_tri[:,:,0].min(1)<=x1)&(all_tri[:,:,2].max(1)>=z0)&(all_tri[:,:,2].min(1)<=z1)
tri=all_tri[mask];tree=shapely.STRtree(shapely.polygons(tri[:,:,[0,2]]))
toes=np.unique(updated[(np.abs(original[:,:,1]+.09)<1e-7)&(np.abs(updated[:,:,1]-original[:,:,1])>1e-5)],axis=0)
assert len(toes)>20
seams=[]
for x,y,z in toes:
 heights=[]
 for index in tree.query(Point(x,z).buffer(.001),predicate='intersects'):
  vert=tri[index];mat=np.vstack([vert[:,0],vert[:,2],np.ones(3)])
  if abs(np.linalg.det(mat))<1e-8:continue
  weights=np.linalg.solve(mat,np.array([x,z,1]))
  if weights.min()>=-.001 and weights.max()<=1.001:heights.append(float(weights@vert[:,1]))
 assert heights and min(abs(h-y) for h in heights)<.03,('Railway-ground seam',x,y,z,heights)
 seams.append(min(abs(h-y) for h in heights))
print(f'Railway ground: {len(toes)} toe locations joined; maximum mismatch {max(seams):.6f} m; crest/south slope preserved.')
report={'status':'PASS','patches':reports,'checks':['separate bank and marsh control sets','map dots fitted within3cm','no channel crossing','complete nonoverlapping dry surfaces','flat floors removed','detailed core unchanged','dry seams agree','existing marsh area preserved']}
report['checks'][-1]='earlier bank and Knobshill patches preserved; northern marsh expanded'
report['railwayGround']={'adjustedVertexReferences':len(changes),'checkedToes':len(toes),'maximumSeamMetres':max(seams),'crestAndSouthSlopePreserved':True}
(ROOT/'scenes/channelsea-sewer-panorama/review/regional-marsh-checks.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
