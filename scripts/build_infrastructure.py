"""Map-traced streets and interpreted raised railway formations."""
import json, math
from pathlib import Path
import numpy as np
from pyproj import Transformer
from shapely.geometry import Polygon, LineString, Point, MultiPoint, box
from shapely.ops import unary_union, triangulate
from shapely import affinity, segmentize

ROOT=Path(__file__).resolve().parents[1]
def read(path):return json.loads((ROOT/path).read_text())
data=read('docs/data/ground-plan.json');sw=read('docs/data/southwest-context.json')
traces=read('data/maps/road-traces.json');sheets=read('data/maps/os-neighbourhood-traces.json')['sheets']
project=Transformer.from_crs(4326,27700,always_xy=True).transform
fits={}
for name,s in sheets.items():
    if 'controls' not in s:continue
    a=np.array([complex(*c['pixel']) for c in s['controls']]);b=np.array([complex(*c['target']) for c in s['controls']])
    scale=np.sum(np.conjugate(a-a.mean())*(b-b.mean()))/np.sum(abs(a-a.mean())**2)
    fits[name]=(scale,b.mean()-scale*a.mean())
def point(sheet,p,pixel_width):
    if sheet=='southwest':return (np.array([p[0]*3511/pixel_width,p[1]*3511/pixel_width,1])@np.array(sw['transform'])).tolist()
    width=2048 if sheet=='overview' else 1888
    u,v=[x*width/pixel_width for x in p];s=sheets[sheet]
    if sheet in fits:
        scale,offset=fits[sheet];q=scale*complex(u,v)+offset
        return point(s['registrationToSheet'],[q.real,q.imag],1888)
    left,top,right,bottom=s['neatline'];west,south,east,north=s['bounds']
    e,n=project(west+(east-west)*(u-left)/(right-left),north-(north-south)*(v-top)/(bottom-top))
    return [e-538900,183209-n]
def rectangle(b):
    return affinity.translate(affinity.rotate(box(-b['width']/2,-b['depth']/2,b['width']/2,b['depth']/2),-b.get('rotation',0)),b['x'],b['z'])
water=unary_union([Polygon(p[0],p[1:]) for r in data['rivers'] for p in r['polygons']])
buildings=unary_union([rectangle(b).buffer(.5) for b in data['factoryStudies']+data['neighbourhood']['mappedFactories']+data['neighbourhood']['terraces']+data['neighbourhood']['houses']+sw['rows']+sw['industrialRanges']+[data['neighbourhood']['mill']]])
road_shapes=[];shoulders=[];paths=[];routes=[];bridges=[]
surface_shapes={s:[] for s in ['macadam','setts','cinder']}
explicit_decks=[]
for r in traces['roads']:
    for span in r.get('bridgeSpans',[]):
        route=[point(r['sheet'],p,r['pixelWidth']) for p in span['points']]
        line=LineString(route)
        bridges.append({'id':span['id'],'name':r['name'],'route':route,'width':r['width'],
                        'height':span['height'],'surface':r['surface'],'evidence':span['evidence']})
        # Keep surface triangles off the deck, including the dry gap in the river GIS.
        explicit_decks.append(line.buffer(r['width']/2+1.1,cap_style=2))
deck_exclusion=unary_union(explicit_decks)
for r in traces['roads']:
    points=[point(r['sheet'],p,r['pixelWidth']) for p in r['points']];line=LineString(points)
    w=r['width'];route={**r,'route':[[round(x,2),round(z,2)] for x,z in points]};routes.append(route)
    corridor=line.buffer(w/2,join_style=2,cap_style=2).difference(buildings)
    ground=corridor.difference(water.buffer(.6)).difference(deck_exclusion)
    (paths if r['kind']=='path' else road_shapes).append(ground)
    if r['kind']!='path':surface_shapes[r['surface']].append(ground)
    if r['kind']!='path':shoulders.append(line.buffer(w/2+1.1,join_style=2,cap_style=2).difference(buildings).difference(water.buffer(.6)).difference(deck_exclusion))
    # Only the named mapped crossings receive a road deck over water.
    if r['name'] in ['Three Mills Lane','Three Mills entrance'] and not r.get('bridgeSpans'):
        crossing=line.intersection(water.buffer(2))
        for part in getattr(crossing,'geoms',[crossing]):
            if part.geom_type=='LineString' and 1<part.length<65:
                bridges.append({'name':r['name'],'route':list(part.coords),'width':w,'height':1.8,'evidence':'Mapped crossing; road deck height and structure interpreted.'})
roads=unary_union(road_shapes);shoulder=unary_union(shoulders).difference(roads);path=unary_union(paths).difference(roads)
def triangles(g,max_edge=5):
    result=[]
    for p in getattr(g,'geoms',[g]):
        if p.geom_type!='Polygon' or p.area<.05:continue
        tolerant=p.buffer(.00001)
        for t in triangulate(segmentize(p,max_edge)):
            if tolerant.covers(t):result.append([[round(x,3),round(z,3)] for x,z in list(t.exterior.coords)[:3]])
    return result
# Retain the raised sewer, but let mapped streets pass under its crest.
sewer_banks=[]
road_openings=roads.buffer(1.5)
for tri in data['neighbourhood']['sewer']['banks']:
    polygon=Polygon([(p[0],p[2]) for p in tri])
    if polygon.area<.0001:continue
    if not polygon.intersects(road_openings):sewer_banks.append(tri);continue
    coefficients=np.linalg.solve(np.array([[p[0],p[2],1] for p in tri]),np.array([p[1] for p in tri]))
    for cut in triangles(polygon.difference(road_openings),8):
        sewer_banks.append([[x,round(float(np.dot([x,z,1],coefficients)),3),z] for x,z in cut])
railways=[]
for r in data['neighbourhood']['railways']:
    line=LineString(r['route']);height=5.5
    # The rail deck spans the gaps; earth slopes stop at water and streets below.
    openings=water.buffer(2).union(roads.buffer(2))
    footprint=line.buffer(17,join_style=2).difference(openings).difference(buildings)
    samples=[]
    for p in getattr(footprint,'geoms',[footprint]):
        if p.geom_type!='Polygon':continue
        p=segmentize(p,5);samples.extend(p.exterior.coords)
        for hole in p.interiors:samples.extend(hole.coords)
    for d in np.arange(0,line.length,4):
        c=line.interpolate(d);a=line.interpolate(max(0,d-1));b=line.interpolate(min(line.length,d+1))
        dx,dz=b.x-a.x,b.y-a.y;length=math.hypot(dx,dz)
        for offset in [-13,-9,-4.5,0,4.5,9,13]:
            q=Point(c.x-dz/length*offset,c.y+dx/length*offset)
            if footprint.contains(q):samples.append((q.x,q.y))
    tolerant=footprint.buffer(.00001)
    rail_triangles=[list(t.exterior.coords)[:3] for t in triangulate(MultiPoint(samples)) if tolerant.covers(t)]
    mesh=[]
    for tri in rail_triangles:
        mesh.append([[x,round(.05+height*max(0,min(1,(17-line.distance(Point(x,z)))/12.5)),3),z] for x,z in tri])
    crossings=[]
    cuts=line.intersection(openings)
    for part in getattr(cuts,'geoms',[cuts]):
        if part.geom_type=='LineString' and part.length>1:crossings.append(list(part.coords))
    railways.append({**r,'formationHeight':height,'embankment':mesh,'crossings':crossings,'evidence':r['evidence']+' Raised formation at 5.5 m above local marsh datum, side slopes and bridge details interpreted from author direction; not surveyed levels.'})
result={'sources':'data/maps/road-traces.json; OS housing registration; southwest holder registration',
        'limitations':'Centrelines approximate; widths, paving, railway levels and bridge structures interpreted. Registration can differ by tens of metres. Buildings and waterways clipped out of road surface; named mapped crossings bridged separately.',
        'roads':routes,'roadTriangles':triangles(roads),'shoulderTriangles':triangles(shoulder),'pathTriangles':triangles(path),'roadBridges':bridges,'railways':railways,'sewerBanks':sewer_banks}
remaining=roads
result['roadSurfaces']={}
for kind in ['setts','macadam','cinder']:
    patch=unary_union(surface_shapes[kind]).intersection(remaining)
    result['roadSurfaces'][kind]=triangles(patch)
    remaining=remaining.difference(patch)
assert remaining.area<.01
result['surfacePolicy']=traces['surfacePolicy']
assert roads.intersection(water).area<.01
assert roads.intersection(buildings).area<.01
mill_spans=[b for b in bridges if b['name']=='Abbey Lane']
assert len(mill_spans)==1
mill_span=mill_spans[0];span_line=LineString(mill_span['route'])
lane_line=LineString(next(r for r in routes if r['name']=='Abbey Lane')['route'])
assert span_line.difference(lane_line.buffer(.01)).is_empty
assert all(not water.buffer(.6).covers(Point(p)) for p in mill_span['route'])
assert not span_line.buffer(mill_span['width']/2,cap_style=2).intersects(rectangle(data['neighbourhood']['mill']))
assert roads.intersection(deck_exclusion).area<.01
road_mesh_area=sum(Polygon(t).area for t in result['roadTriangles'])
assert abs(road_mesh_area-roads.area)/roads.area<.002,(road_mesh_area,roads.area)
assert all(r['formationHeight']>4 for r in railways)
assert all(math.isfinite(v) for r in railways for t in r['embankment'] for p in t for v in p)
(ROOT/'docs/data/infrastructure.json').write_text(json.dumps(result,separators=(',',':'))+'\n')
print(f"Infrastructure: {len(routes)} street/lane traces, {len(bridges)} road crossing segments, {len(railways)} raised railway routes; road/building/water checks passed.")
