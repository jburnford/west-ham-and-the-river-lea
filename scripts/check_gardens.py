"""Validate interpreted garden divisions and continuity across the old tile edge."""
import json
import sys
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union

ROOT=Path(__file__).resolve().parents[1]
load=lambda path:json.loads((ROOT/path).read_text())
ground=load('docs/data/ground-plan.json');garden=ground['neighbourhood']['garden']
ditches=load('data/maps/marsh-ditches.json')
drain_clearance=unary_union([LineString(f['route']).buffer(f['width']/2+2.9) for f in ditches['features']])
plots=[Polygon(b['footprint']) for b in garden['beds']]
assert len(plots)>80 and len(plots)<220
assert len({round(b['width']) for b in garden['beds']})>3
assert sum(b['shed'] for b in garden['beds'])<len(plots)*.15
for plot in plots:
 assert plot.is_valid and Polygon(garden['footprint']).buffer(.005).covers(plot)
 assert plot.intersection(drain_clearance).area<.001
assert abs(sum(p.area for p in plots)-unary_union(plots).area)<.001,'Overlapping plots'

core=load('docs/data/river-terrain.json');network=load('docs/data/river-network.json')
positions=np.fromfile(ROOT/'docs/data'/network['positionFile'],dtype='<f4').reshape(-1,3)
cover=np.fromfile(ROOT/'docs/data'/network['landcoverFile'],dtype='uint8').reshape(-1,2)
assert len(cover)==len(positions)
core_h=np.fromfile(ROOT/'docs/data'/core['heightFile'],dtype='<f4').reshape(core['height'],core['width'])
core_cover=np.fromfile(ROOT/'docs/data'/core['landcoverFile'],dtype='uint8').reshape(core_h.shape)
x0,z0,_,_=core['bounds'];matches=0
for i in np.where((positions[:,0]==x0)&(positions[:,2]>50)&(positions[:,2]<250))[0]:
 z=positions[i,2];index=(z-z0)/core['step'];lo=int(index);f=index-lo
 h=core_h[lo,0]*(1-f)+core_h[lo+1,0]*f
 # Different 0.4 m / 1 m tessellations may differ by millimetres at ditch slopes.
 assert abs(h-positions[i,1])<.012,'Height step along the marsh join'
 c=core_cover[round(index),0]
 assert bool(cover[i,0])==(c==1) and bool(cover[i,1])==(c==2),'Land cover changes at the tile boundary'
 matches+=1
assert matches>100
if '--rendered' in sys.argv:
 report=load('scenes/channelsea-sewer-panorama/review/tide-checks.json')['gardens']
 assert report['plots']==len(plots),'Stale browser report'
 grid={(float(x),float(z)):float(y) for x,y,z in positions}
 def actual_ground(x,z):
  if core['bounds'][0]<=x<core['bounds'][2] and core['bounds'][1]<=z<core['bounds'][3]:
   u=(x-x0)/core['step'];v=(z-z0)/core['step'];ix=int(u);iz=int(v);u-=ix;v-=iz
   a,b,c,d=core_h[iz,ix],core_h[iz,ix+1],core_h[iz+1,ix],core_h[iz+1,ix+1]
   if (ix+iz)%2:
    return a+(d-c)*u+(c-a)*v if u<v else a+(b-a)*u+(d-b)*v
  else:
   ix=int(np.floor(x));iz=int(np.floor(z));u=x-ix;v=z-iz
   a,b,c,d=[grid.get(p,-.1) for p in [(ix,iz),(ix+1,iz),(ix,iz+1),(ix+1,iz+1)]]
  return a+(b-a)*u+(c-a)*v if u+v<=1 else d+(c-d)*(1-u)+(b-d)*(1-v)
 clearance=[y-actual_ground(x,z) for x,z,y in report['surfaceSamples']]
 assert min(clearance)>.02,('Buried rendered garden surface',min(clearance))
 assert max(clearance)<.2,('Floating garden surface',max(clearance))
 print(f'Rendered soil check: {len(clearance)} points, clearance {min(clearance):.3f}–{max(clearance):.3f} m above actual terrain triangles.')
print(f'Garden checks passed: {len(plots)} varied plots, no overlaps or blocked drains, and {matches} matching terrain/cover samples across the former seam.')
