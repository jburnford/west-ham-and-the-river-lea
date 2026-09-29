"""Shared map-derived marsh geometry and inferred sections for both terrain meshes."""
import json
from functools import lru_cache
from pathlib import Path
import numpy as np
from shapely import contains_xy, distance, points
from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union

ROOT=Path(__file__).resolve().parents[1]
def load(name):return json.loads((ROOT/name).read_text())
def smooth(a,b,v):
 t=np.clip((v-a)/(b-a),0,1);return t*t*(3-2*t)

@lru_cache(maxsize=1)
def geometry():
 raw=load('data/maps/marsh-ditches.json');ground=load('docs/data/ground-plan.json')
 factories=load('docs/data/factory-buildings.json');infra=load('docs/data/infrastructure.json')
 water=unary_union([Polygon(p[0],p[1:]) for r in ground['rivers']+factories['westContext']['rivers'] for p in r['polygons']])
 buildings=unary_union([Polygon(p['outer'],p['holes']) for b in factories['buildings']+load('docs/data/high-street-frontages.json')['buildings'] for p in b['renderPolygons']]+
  [Polygon(b['footprint']) for b in ground['neighbourhood']['houses']+ground['neighbourhood']['terraces']])
 roads=unary_union([LineString(r['route']).buffer(r['width']/2+1) for r in infra['roads']])
 paths=load('docs/data/high-street-frontages.json')['vista']['connections']
 roads=roads.union(unary_union([LineString([(p[0],p[2]) for p in c['route']]).buffer(c['width']/2+1) for c in paths]))
 sites=unary_union([Polygon(p[0],p[1:]) for s in ground['sites'] for p in s['polygons']])
 # The river bank is a defence, not an open ditch outlet. Preserve its crest
 # until a sluice/culvert is independently identified and modelled.
 protected=water.buffer(10).union(roads).union(buildings.buffer(1))
 ditch_parts=[LineString(f['route']).buffer(f['width']/2,cap_style=2,join_style=2).difference(protected) for f in raw['features']]
 ditches=unary_union(ditch_parts)
 marsh=Polygon(raw['marshFootprint']).difference(sites).union(ditches.buffer(3)).difference(protected)
 return raw,marsh,ditches,ditch_parts,protected

def apply_sections(X,Z,height):
 raw,marsh,ditches,_,_=geometry()
 active=contains_xy(marsh,X,Z);mud=np.zeros_like(height)
 vertices=points(X[active],Z[active]);inside=contains_xy(ditches,X[active],Z[active])
 signed=distance(vertices,ditches.boundary)*np.where(inside,-1,1)
 ground=raw['levels']['marshGround']+.025*np.sin(X[active]*.039)*np.sin(Z[active]*.027)
 profile=np.where(inside,.26+ (raw['levels']['ditchBed']-.26)*smooth(0,1.8,-signed),
                  .26+(ground-.26)*smooth(0,2,signed))
 feather=smooth(0,3,distance(vertices,marsh.boundary))
 # Fully retain the bank section around ditch ends as well as their middles.
 feather=np.maximum(feather,1-smooth(0,1.5,np.maximum(signed,0)))
 height[active]=height[active]*(1-feather)+profile*feather
 mud[active]=(1-smooth(0,2,np.maximum(signed,0)))*feather
 return height,mud,active
