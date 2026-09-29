"""Fit an interpreted Greek-cross body to the author's historical outline."""
import json,math
from pathlib import Path
from scipy.optimize import differential_evolution
from shapely.geometry import shape,box,Polygon
from shapely import affinity
from shapely.ops import unary_union
ROOT=Path(__file__).resolve().parents[1]
fs=json.loads((ROOT/'reference/historic-building-footprints-2026-09-28/current-scene-buildings-bng.geojson').read_text())['features']
byid={f['properties']['sourceFid']:affinity.affine_transform(shape(f['geometry']),[1,0,0,-1,-538900,183209]) for f in fs}
target=byid[459]
# Period-map inspection separates the rear boiler band from the ornate cross.
# Local measurements follow the long straight mapped edges; minor projections
# remain part of the source outline, not invented room divisions.
def footprint(v):
 x,z,angle=v
 p=unary_union([box(-37,-16,37,4),box(-21,-3,21,17),box(-8,-21.5,8,31)])
 return affinity.translate(affinity.rotate(p,angle,origin=(0,0)),x,z)
def score(v):
 p=footprint(v);return 1-p.intersection(target).area/p.union(target).area
fit=differential_evolution(score,[(-182,-179),(-15,-12),(35,37)],seed=1868,tol=1e-8,popsize=10,maxiter=120,polish=True)
v=fit.x;p=footprint(v);old=box(-212,-23,-158,-3).union(box(-195,-37,-175,11))
theta=math.radians(v[2]);cs,sn=math.cos(theta),math.sin(theta)
def world(x,z):return [round(v[0]+x*cs-z*sn,3),round(v[1]+x*sn+z*cs,3)]
maincentre=world(0,4.75)
result={'source':'Author-supplied london_buildings_1891-96_corr_v1.gpkg; OS five-foot mosaic m18_131069_87140',
 'sourceFid':459,'sourceCRS':'EPSG:3857 transformed through BNG','worldOriginBNG':[538900,183209],
 'centre':maincentre,'angleDegrees':round(v[2],5),'mainLength':42,'mainDepth':20,'mainOffsetZ':2.25,'crossWidth':16,'crossLength':52.5,
 'boilerWings':[{'x':x,'z':-10.75,'width':29,'depth':20,'height':7.8,'roofRise':3.5} for x in [-22.5,22.5]],
 'worldFootprint':[[round(x,3),round(z,3)] for x,z in list(p.exterior.coords)[:-1]],
 'sourcePolygons':[[[list(pt) for pt in q.exterior.coords][:-1],*[list(map(list,h.coords))[:-1] for h in q.interiors]] for q in target.geoms],
 'chimneys':[{'sourceFid':fid,'centre':[round(byid[fid].centroid.x,3),round(byid[fid].centroid.y,3)],'worldFootprint':list(map(list,list(byid[fid].geoms[0].exterior.coords)[:-1]))} for fid in [257848,277380]],
 'fit':{'previousIoU':old.intersection(target).area/old.union(target).area,'bodyIoU':1-fit.fun},
 'evidence':'Main Greek cross and lower rear boiler wings separated by reading the period OS map and photographs. Body rectangles and orientation fitted to outline; ornamental projections and vertical dimensions interpreted. Not a measured elevation.'}
(ROOT/'data/maps/abbey-station-plan.json').write_text(json.dumps(result,indent=2)+'\n')
(ROOT/'docs/data/abbey-station-plan.json').write_text(json.dumps(result,separators=(',',':'))+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['worldFootprint','sourcePolygons','chimneys']},indent=2))
