"""Street and bank buildings between the separately registered factory ranges."""
import json,math
from pathlib import Path
from shapely.geometry import Polygon,LineString,Point,box
from shapely.ops import unary_union
from shapely import affinity
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_text())
def rectangle(b):return affinity.translate(affinity.rotate(box(-b['width']/2,-b['depth']/2,b['width']/2,b['depth']/2),-b['rotation']),b['x'],b['z'])
raw=load('data/maps/high-street-frontages.json');plan=load('docs/data/ground-plan.json');factories=load('docs/data/factory-buildings.json');infra=load('docs/data/infrastructure.json')
water=unary_union([Polygon(p[0],p[1:]) for r in plan['rivers']+factories['westContext']['rivers'] for p in r['polygons']])
existing=unary_union([Polygon(p['outer'],p['holes']) for b in factories['buildings'] for p in b['renderPolygons']]+[rectangle(b) for b in plan['neighbourhood']['houses']+plan['neighbourhood']['terraces']])
streets=unary_union([LineString(r['route']).buffer(r['width']/2+.8,cap_style=2,join_style=2) for r in infra['roads']])
occupied=existing.buffer(.3).union(water.buffer(.3)).union(streets)
result={'source':raw['source'],'policy':raw['policy'],'sites':[],'holders':[],'structures':[],'buildings':[],'omitted':[]}
vista=load('data/maps/wall-river-vista.json')
wall=unary_union([Polygon(p[0],p[1:]) for r in plan['rivers'] if r['id']==1 for p in r['polygons']])
vista['bank']['samples']=[]
for z in range(vista['bank']['zStart'],vista['bank']['zEnd']+1,2):
 cut=wall.intersection(LineString([[-1000,z],[0,z]]))
 assert not cut.is_empty
 vista['bank']['samples'].append([round(cut.bounds[2],3),z])
result['vista']=vista
bridge_defaults=load('data/maps/road-bridge-forms.json')['defaults']
def deck_end_level(x,z,street):
 """docs/road-bridges.js deckEndLevel: the deck road level at each route end, level across the
 approach band and falling at approachGrade along the road, blended to the deck within deckEndBlend."""
 h=street
 for bridge in infra['roadBridges']:
  route=bridge['route'];band=bridge['width']/2+bridge_defaults['streetFootway'];deck=bridge['height']-.065;best=None;s0=0
  for i in range(1,len(route)):
   (ax,az),(bx,bz)=route[i-1],route[i];length=math.hypot(bx-ax,bz-az);ux,uz=(bx-ax)/length,(bz-az)/length
   t=(x-ax)*ux+(z-az)*uz
   if i>1:t=max(0,t)
   if i<len(route)-1:t=min(length,t)
   dist=math.hypot(x-ax-ux*t,z-az-uz*t)
   if best is None or dist<best[2]:best=(s0+t,-(x-ax)*uz+(z-az)*ux,dist)
   s0+=length
  s,v,_=best;d=math.hypot(max(0,-s,s-s0),max(0,abs(v)-band))
  h=max(h,deck-bridge_defaults['approachGrade']*d)
  if d<bridge_defaults['deckEndBlend']:
   q=d/bridge_defaults['deckEndBlend'];h=deck+(h-deck)*q*q*(3-2*q)
 return h
for connection in vista['connections']:
 if 'bankStart' in connection:
  bank_route=[]
  for z in range(connection['bankStart'],connection['bankEnd']+1,2):
   cut=wall.intersection(LineString([[-1000,z],[0,z]]))
   bank_route.append([round(cut.bounds[2]+vista['bank']['pathLandOffset'],3),vista['bank']['crestHeight'],z])
  connection['route']=bank_route+connection['route'][1:]
 # Share the exact existing endpoint, so a small source rounding error cannot open a seam.
 if connection['id']=='high-street-access':
  x,z=vista['bank']['samples'][0];connection['route'][-1]=[x+vista['bank']['pathLandOffset'],vista['bank']['crestHeight'],z]
  x,_,z=connection['route'][0]
  ground=deck_end_level(x,z,.12)
  connection['route'][0][1]=ground+.04
 # Mitered ribbon, retaining the exact width/level at the photograph segment.
 route=connection['route'];sections=[]
 for i,(x,y,z) in enumerate(route):
  a=route[max(0,i-1)];b=route[min(len(route)-1,i+1)]
  dx,dz=b[0]-a[0],b[2]-a[2];length=math.hypot(dx,dz)
  nx,nz=dz/length,-dx/length
  if (connection['id']=='high-street-access' and i==len(route)-1) or ('bankStart' in connection and i<len(route)-2):nx,nz=1,0
  w=connection['width']/2
  sections.append([[x-nx*w,y+.025,z-nz*w],[x+nx*w,y+.025,z+nz*w]])
 connection['sections']=sections
for r in raw['ranges']:
 p=Polygon(r['footprint']);q=p.difference(occupied)
 parts=[x for x in getattr(q,'geoms',[q]) if x.geom_type=='Polygon' and x.area>8]
 if not parts:
  result['omitted'].append({'id':r['id'],'reason':'Covered by an existing range or mapped street/water corridor.'});continue
 q=unary_union(parts);occupied=occupied.union(q.buffer(.25));a,b=r['footprint'][:2];angle=math.atan2(b[1]-a[1],b[0]-a[0]);c=p.centroid;local=affinity.rotate(p,-math.degrees(angle),origin=c);bounds=[local.bounds[0]-c.x,local.bounds[1]-c.y,local.bounds[2]-c.x,local.bounds[3]-c.y]
 result['buildings'].append({**r,'siteId':'high-street-frontages','streetFrontage':True,'x':c.x,'z':c.y,'rotation':math.degrees(angle),'width':bounds[2]-bounds[0],'depth':bounds[3]-bounds[1],'storeys':r['storeysEstimate'],'roofAxis':'x','roofBays':1,'localBounds':[bounds[:2],bounds[2:]],'material':'brick','renderPolygons':[{'outer':list(x.exterior.coords)[:-1],'holes':[list(t.coords)[:-1] for t in x.interiors]} for x in parts],'sourceAreaM2':round(p.area,2),'renderAreaM2':round(q.area,2),'retainedFraction':round(q.area/p.area,3),'trimEvidence':'Existing registered factories/housing and mapped streets/water take precedence; no solid building across an entrance or channel.'})
 assert q.intersection(existing).area<.01 and q.intersection(water).area<.01 and q.intersection(streets).area<.01
(ROOT/'docs/data/high-street-frontages.json').write_text(json.dumps(result,indent=2)+'\n')
print(f"High Street: {len(result['buildings'])} retained ranges; {len(result['omitted'])} already-covered or conflicting envelopes omitted.")
for r in result['buildings']:
 if r['retainedFraction']<.65:print(r['id'],r['name'],r['retainedFraction'])
