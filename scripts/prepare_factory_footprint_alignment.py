"""Prepare a reviewed first batch of one-to-one factory footprint corrections.

Run only to regenerate the authoring register; the scene builder consumes the
saved register without needing the private regional source extract.
"""
import json
import math
from pathlib import Path
from shapely.geometry import shape,Polygon
from shapely import affinity
from shapely.strtree import STRtree
from shapely.ops import unary_union
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reference/footprint-model-alignment';OUT.mkdir(exist_ok=True)
fs=json.loads((ROOT/'reference/historic-building-footprints-2026-09-28/current-scene-buildings-bng.geojson').read_text())['features']
gs=[affinity.affine_transform(shape(f['geometry']),[1,0,0,-1,-538900,183209]) for f in fs];tree=STRtree(gs)
scene=json.loads((ROOT/'docs/data/factory-buildings.json').read_text())
models=scene['buildings'];ps=[Polygon(b.get('priorFootprint',b['footprint'])) for b in models];mt=STRtree(ps)
# Individual detached ink-works ranges reviewed together on the overlay.
ink={f'site940-{n}' for n in [4,5,6,12,14,16,17,18,19,20,21,22,23]}
protected={'clock','house-west','howards-540w'}
plan=json.loads((ROOT/'docs/data/ground-plan.json').read_text())
water=unary_union([Polygon(p[0],p[1:]) for r in plan['rivers']+scene['westContext']['rivers'] for p in r['polygons']])
register=[];audit=[];used=set()
for b,p in zip(models,ps):
 candidates=[]
 for idx in tree.query(p.buffer(5)):
  g=gs[idx];area=p.intersection(g).area
  if area:candidates.append((area/p.union(g).area,int(idx)))
 if not candidates:continue
 iou,idx=max(candidates);g=gs[idx];fid=fs[idx]['properties']['sourceFid'];shift=p.centroid.distance(g.centroid);ratio=g.area/p.area
 reason=None
 if b['id'] in protected:reason='Architectural/photo-specific range retained for separate review'
 elif not (iou>=.6 or (b['id'] in ink and iou>=.3)):reason='Insufficient one-to-one overlap'
 elif shift>4 or not .65<=ratio<=1.4:reason='Larger displacement or area change needs individual review'
 elif len(g.geoms)!=1 or g.geoms[0].interiors:reason='Multipart or courtyard building needs compartment review'
 elif g.intersection(water).area>min(.5,p.intersection(water).area+.1):reason='Conflicts with current river-bank geometry; needs joint bank review'
 elif fid in used:reason='Source footprint already assigned'
 else:
  competitors=[models[j]['id'] for j in mt.query(g) if models[j]['id']!=b['id'] and g.intersection(ps[j]).area>max(2,.18*ps[j].area)]
  if competitors:reason='Source also covers another modeled range: '+', '.join(competitors)
 if reason:
  audit.append({'modelId':b['id'],'sourceFid':fid,'iou':round(iou,4),'status':reason});continue
 q=g.geoms[0].simplify(.05,preserve_topology=True)
 # Choose the source's orthogonal axis closest to the previous roof axis.
 rect=list(q.minimum_rotated_rectangle.exterior.coords)
 old=b.get('priorRotation',math.degrees(math.atan2(p.exterior.coords[1][1]-p.exterior.coords[0][1],p.exterior.coords[1][0]-p.exterior.coords[0][0])))
 angles=[math.degrees(math.atan2(z[1]-a[1],z[0]-a[0])) for a,z in zip(rect,rect[1:])]
 angle=min((old+(ang-old+90)%180-90 for ang in angles),key=lambda ang:abs(ang-old))
 register.append({'modelId':b['id'],'siteId':b['siteId'],'name':b['name'],'sourceFid':fid,
  'worldFootprint':[[round(x,3),round(z,3)] for x,z in list(q.exterior.coords)[:-1]],
  'priorFootprint':b.get('priorFootprint',b['footprint']),'priorRotationDegrees':old,'footprintRotationDegrees':round(angle,5),
  'preservedHeight':b['height'],'preservedRoofRise':b['roofRise'],'preservedRoofBays':b['roofBays'],'preservedRoofAxis':b['roofAxis'],
  'review': 'One-to-one source outline; preserve the previously researched use, height and roof form. Ink-works ranges inspected together on the site comparison.',
  'comparison':{'previousIntersectionOverUnion':round(iou,4),'centroidShiftMetres':round(shift,3),'areaRatio':round(ratio,4),'axisChangeDegrees':round(angle-old,3)}})
 used.add(fid)
result={'source':'Author-supplied london_buildings_1891-96_corr_v1.gpkg','sourceCRS':'EPSG:3857 reprojected to EPSG:27700','worldOriginBNG':[538900,183209],'date':'2026-09-28','method':'Reviewed one-to-one geometry corrections. Complex compounds and architectural landmarks require separate review; source feature IDs retained. Source boundary simplification tolerance 0.05 m.','buildings':register}
(ROOT/'data/maps/factory-footprint-alignment.json').write_text(json.dumps(result,indent=2)+'\n')
(OUT/'deferred-candidates.json').write_text(json.dumps(audit,indent=2)+'\n')
print(f'{len(register)} corrections at {len({r["siteId"] for r in register})} sites')
for r in register:print(r['modelId'],r['sourceFid'],r['comparison'])
