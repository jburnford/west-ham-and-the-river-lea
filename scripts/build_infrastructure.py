"""Map-traced streets and interpreted raised railway formations."""
import json, math
from pathlib import Path
import numpy as np
from pyproj import Transformer
from shapely.geometry import Polygon, LineString, Point, MultiPoint, box
from shapely.ops import unary_union, triangulate
from shapely import affinity, segmentize, constrained_delaunay_triangles, set_precision
from shapely.errors import GEOSException
from great_eastern import build_great_eastern
from abbey_support import station_footprints
from manor_road import evidence as manor_evidence, road_trace, align_railway

ROOT=Path(__file__).resolve().parents[1]
def read(path):return json.loads((ROOT/path).read_text())
data=read('docs/data/ground-plan.json');sw=read('docs/data/southwest-context.json')
traces=read('data/maps/road-traces.json')
district=read('data/maps/district-road-traces.json')
factories=read('docs/data/factory-buildings.json')
housing=read('data/maps/housing-road-traces.json')
replaced={r['name'] for r in district['roads']} | set(housing['replaceNames'])
traces['roads']=[r for r in traces['roads'] if r['name'] not in replaced]+district['roads']+housing['roads']
housing_review=read('data/maps/district-housing-review.json')
housing_roads=housing_review['roads']
housing_names={r['name'] for r in housing_roads}|set(housing_review.get('removeRoadNames',[]))
traces['roads']=[r for r in traces['roads'] if r['name'] not in housing_names]+housing_roads
station=read('docs/data/abbey-station-plan.json')
traces['roads']=[r for r in traces['roads'] if r['name'] not in station['replaceRoadNames']]+station['accessPaths']
manor=manor_evidence()
traces['roads'].append(road_trace(manor))
sheets=read('data/maps/os-neighbourhood-traces.json')['sheets']
project=Transformer.from_crs(4326,27700,always_xy=True).transform
fits={}
for name,s in sheets.items():
    if 'controls' not in s:continue
    a=np.array([complex(*c['pixel']) for c in s['controls']]);b=np.array([complex(*c['target']) for c in s['controls']])
    scale=np.sum(np.conjugate(a-a.mean())*(b-b.mean()))/np.sum(abs(a-a.mean())**2)
    fits[name]=(scale,b.mean()-scale*a.mean())
def point(sheet,p,pixel_width):
    if sheet=='scene':return p
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
water=unary_union([Polygon(p[0],p[1:]) for r in data['rivers']+factories['westContext']['rivers'] for p in r['polygons']])
surveyed={s['id'] for s in factories['sites']}
legacy=[b for b in data['factoryStudies']+data['neighbourhood']['mappedFactories']+sw['industrialRanges'] if b.get('siteId') not in surveyed]
legacy+=read('docs/data/housing-detail.json')['rows']+data['neighbourhood']['houses']+[data['neighbourhood']['mill']]
buildings=unary_union([rectangle(b).buffer(.3) for b in legacy]+[Polygon(p['outer'],p['holes']).buffer(.15) for b in factories['buildings'] for p in b['renderPolygons']])
buildings=buildings.union(station_footprints(station).buffer(.15))

road_shapes=[];road_names=[];shoulders=[];paths=[];routes=[];bridges=[]
surface_shapes={s:[] for s in ['macadam','setts','cinder']}
explicit_decks=[]
for r in traces['roads']:
    for span in r.get('bridgeSpans',[]):
        route=[point(r['sheet'],p,r['pixelWidth']) for p in span['points']]
        line=LineString(route)
        bridges.append({**{k:v for k,v in span.items() if k not in ['points']},'id':span['id'],'name':r['name'],'route':route,'width':r['width'],
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
    if r['kind']!='path':road_names.append(r['name'])
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
        try:mesh=constrained_delaunay_triangles(segmentize(p,max_edge))
        except GEOSException:
            # GEOS can fail to find a convex corner on long slivers with near-collinear
            # vertices (the Bridge Road shoulder after the October 2026 retrace). Snap
            # that polygon alone to 1 µm, well below the 1 mm output rounding, and retry.
            p=set_precision(p,1e-6);tolerant=p.buffer(.00001)
            mesh=constrained_delaunay_triangles(segmentize(p,max_edge))
        for t in mesh.geoms:
            if tolerant.covers(t):result.append([[round(x,3),round(z,3)] for x,z in list(t.exterior.coords)[:3]])
    return result
# Deck ends (data/maps/road-bridge-forms.json, deckEndEvidence): at each end of a bridge with deck
# footways the street footway is carried onto the deck footway over a taper, its kerb line drawing
# in from the street carriageway edge to the deck footway kerb. docs/infrastructure.js draws these
# strips (deckEndFootways), rising to the deck footway top; they are kept out of the carriageway,
# street footway and path meshes drawn here, but not out of `roads`, which the railway and sewer
# openings below still read as before.
bridge_defaults=read('data/maps/road-bridge-forms.json')['defaults']
deck_fw=bridge_defaults['deckFootway'];taper=bridge_defaults['deckEndFootwayTaper'];street_fw=bridge_defaults['streetFootway']
street_corridors=[(r['name'],LineString([point(r['sheet'],p,r['pixelWidth']) for p in r['points']]).buffer(r['width']/2,join_style=2,cap_style=2))
                  for r in traces['roads'] if r['kind']!='path']
deck_end_footways=[];deck_end_zones=[]
def deck_end_zone(bridge,side_name,q0,q1):
    """The deck-end footway strips beyond route point q1 (q0 is the route point before it), laid
    along the approach road's own centreline, which can turn at the deck end."""
    road=min((r for r in routes if r['name']==bridge['name']),key=lambda r:LineString(r['route']).distance(Point(q1)))
    line=LineString(road['route']);half=road['width']/2;kerb=bridge['width']/2-deck_fw['inset']-deck_fw['width']/2
    t0=line.project(Point(q1));sign=1 if line.project(Point(q0))<t0 else -1
    def frame(s):
        t=min(line.length,max(0,t0+sign*s));a=line.interpolate(max(0,t-.05));b=line.interpolate(min(line.length,t+.05))
        p=line.interpolate(t);ux,uz=(b.x-a.x)*sign,(b.y-a.y)*sign;n=math.hypot(ux,uz)
        return p,ux/n,uz/n
    stations=list(np.arange(-.5,taper+1e-9,.5))
    inner=lambda s:kerb+(half-kerb)*min(1,max(0,s/taper))
    # Beyond the deck-end line (square to the last deck segment), so the strip meets the deck edge.
    length=math.hypot(q1[0]-q0[0],q1[1]-q0[1]);ex,ez=(q1[0]-q0[0])/length,(q1[1]-q0[1])/length
    beyond=Polygon([(q1[0]-ez*40,q1[1]+ex*40),(q1[0]-ez*40+ex*40,q1[1]+ex*40+ez*40),(q1[0]+ez*40+ex*40,q1[1]-ex*40+ez*40),(q1[0]+ez*40,q1[1]-ex*40)])
    def at(s,v):
        # On the deck axis carried on at the deck end, turning onto the road's own line by the
        # end of the taper (the connection decks meet their lanes at a bend).
        p,ux,uz=frame(s);a=min(1,max(0,s/taper))
        road_pt=(p.x-uz*v,p.y+ux*v);deck_pt=(q1[0]+ex*s-ez*v,q1[1]+ez*s+ex*v)
        return (deck_pt[0]+(road_pt[0]-deck_pt[0])*a,deck_pt[1]+(road_pt[1]-deck_pt[1])*a)
    sides=[]
    for side in (-1,1):
        edge_in=[at(s,side*inner(s)) for s in stations];edge_out=[at(s,side*(half+street_fw)) for s in stations]
        sides.append(Polygon(edge_in+edge_out[::-1]).buffer(0))
    zone=unary_union(sides).intersection(beyond)
    others=unary_union([g for name,g in street_corridors if name!=bridge['name']])
    zone=zone.difference(buildings).difference(water.buffer(.6)).difference(others).difference(deck_exclusion)
    zone=unary_union([g for g in getattr(zone,'geoms',[zone]) if g.geom_type=='Polygon' and g.area>.05])
    if zone.is_empty:return
    deck_end_zones.append(zone)
    def rise(x,z):
        # Station beyond the deck end, measured as the strip is laid: on the deck axis at the deck
        # end, along the road by the end of the taper.
        s_deck=(x-q1[0])*ex+(z-q1[1])*ez;s_road=sign*(line.project(Point(x,z))-t0);a=min(1,max(0,s_deck/taper))
        return round(min(1,max(0,1-(s_deck*(1-a)+s_road*a)/taper)),4)
    deck_end_footways.append({'bridge':bridge['id'],'end':side_name,'triangles':[[[x,z,rise(x,z)] for x,z in tri] for tri in triangles(zone,1)]})
for bridge in bridges:
    if bridge.get('style') and bridge['width']-2*deck_fw['inset']-deck_fw['width']>=deck_fw['minCarriageway']:
        deck_end_zone(bridge,'start',bridge['route'][1],bridge['route'][0])
        deck_end_zone(bridge,'end',bridge['route'][-2],bridge['route'][-1])
deck_ends=unary_union(deck_end_zones);drawn_roads=roads.difference(deck_ends)
# High Street passes over the enclosed sewer. Abbey Lane and Mill Meads works
# road pass under it on interpreted brick arches (docs/sewer-crossing.js).
sewer=data['neighbourhood']['sewer'];sewer_line=LineString(sewer['route'])
crossing_spec=read('data/maps/sewer-high-street.json')['crossing']
high_street=next(r for r in routes if r['name']==crossing_spec['road'])
street_line=LineString(high_street['route'])
crossing=sewer_line.intersection(street_line)
assert crossing.geom_type=='Point'
crossing_spec={**crossing_spec,'centre':[crossing.x,crossing.y],'roadRoute':high_street['route'],'roadWidth':high_street['width']}
street_opening=street_line.buffer(high_street['width']/2+1.1,cap_style=2)
sewer_crest=sewer_line.buffer(sewer['crestWidth']/2,join_style=2).difference(street_opening)
portal=sewer.get('portal')
if portal:
    # The open embankment ends at the Wick Lane portal: the crest stops flush with
    # the portal face instead of running on in a round cap (as build_panorama_data.py).
    (px,pz),(dx,dz)=portal['point'],portal['direction'];nx,nz,r=-dz,dx,80
    sewer_crest=sewer_crest.difference(Polygon([(px+nx*r,pz+nz*r),(px-nx*r,pz-nz*r),(px-nx*r-dx*r,pz-nz*r-dz*r),(px+nx*r-dx*r,pz+nz*r-dz*r)]))
sewer_edges=[]
for sign in [-1,1]:
 edge=sewer_line.offset_curve(sign*7.3,join_style=2).difference(street_opening.buffer(.15))
 for part in getattr(edge,'geoms',[edge]):
  if part.geom_type=='LineString':sewer_edges.append(list(segmentize(part,4).coords))
sewer_banks=[]
# build_panorama_data.py already stops the banks 1.5 m short of the streets it
# names in bankEnds (kind 'road') and walls those ends; only the remaining
# streets (Stratford High Street) are cut here, exactly as before.
precut={e['road'] for e in sewer.get('bankEnds',[]) if e['kind']=='road'}
road_openings=unary_union([g for g,n in zip(road_shapes,road_names) if n not in precut]).buffer(1.5)
for tri in data['neighbourhood']['sewer']['banks']:
    polygon=Polygon([(p[0],p[2]) for p in tri])
    if polygon.area<.0001:continue
    if not polygon.intersects(road_openings):sewer_banks.append(tri);continue
    coefficients=np.linalg.solve(np.array([[p[0],p[2],1] for p in tri]),np.array([p[1] for p in tri]))
    for cut in triangles(polygon.difference(road_openings),8):
        sewer_banks.append([[x,round(float(np.dot([x,z,1],coefficients)),3),z] for x,z in cut])
# No opening through the embankment is mapped for any path: path traces end at
# the bank toe (the Mill Mead riverbank path is drawn in two parts).
sewer_footprint=unary_union([Polygon([(p[0],p[2]) for p in t]).buffer(1e-5) for t in sewer_banks if Polygon([(p[0],p[2]) for p in t]).area>1e-6])
assert path.intersection(sewer_footprint).area<.01,'A path runs through the sewer embankment'
# Split the crest along the bank outline, so docs/app.js can grass the crest over
# the earth bank and keep the stone deck over the openings without a sawtooth
# seam. Only crest triangles touching an opening are re-triangulated; the rest,
# including the whole High Street stretch, keep their earlier triangulation.
crest_deck=sewer_crest.difference(sewer_footprint.buffer(.005,join_style=2)).difference(street_opening.buffer(3)).simplify(.02)
crest_triangles=[];redo=[]
for t in triangles(sewer_crest,4):
    (redo if Polygon(t).intersects(crest_deck.buffer(.01)) else crest_triangles).append(t)
redo=unary_union([Polygon(t) for t in redo])
crest_triangles+=triangles(redo.difference(crest_deck),4)+triangles(redo.intersection(crest_deck),4)
railways=[]
branch_connection=read('data/maps/woolwich-northern-connection.json')
from railway_levels import load as load_levels, apply as apply_levels, level_stations, bank_level
from shapely.ops import substring
levels_register=load_levels()
for r in data['neighbourhood']['railways']:
    r=align_railway(r,manor)
    if r['name']=='Great Eastern Railway, Woolwich branch':
        r={**r,'route':[branch_connection['existingBranchStart'],*r['route'][1:]],
           'evidence':r['evidence']+' '+branch_connection['alignmentNote']}
    # Formation levels (and the LT&SR / Abbey Mills curve routes) from the OS level register.
    r=apply_levels(r,levels_register);spec=levels_register['railways'].get(r['name'],{})
    line=LineString(r['route'])
    chain,formation=np.array(r['levelProfile']['chainage']),np.array(r['levelProfile']['formation'])
    def level(s):return float(np.interp(s,chain,formation))
    # The rail deck spans the gaps; earth slopes stop at water and streets below. A street the OS
    # shows crossing on the level (the register's crossings with osForm 'level crossing') is not an
    # opening: the line runs on through at its formation and the street is drawn at rail level over it.
    level_crossings=[substring(line,*spec['crossings'][k]['chainage']).buffer(15,cap_style=2) for k in spec.get('crossings',{}) if spec['crossings'][k].get('osForm')=='level crossing']
    street_openings=roads.buffer(2).difference(unary_union(level_crossings)) if level_crossings else roads.buffer(2)
    openings=water.buffer(2).union(street_openings)
    # Register bridges (the LT&SR over the G.E.R. and Manor Road): no earth between the abutment faces.
    register_spans=[]
    for bridge in spec.get('bridges',[]):
        s0,s1=bridge['chainage'];p=bridge.get('pier');t=bridge.get('pierThickness',0)/2
        spans=[(s0,p-t),(p+t,s1)] if p is not None else [(s0,s1)]
        register_spans+=[(bridge,a,b) for a,b in spans]
    register_cut=unary_union([substring(line,b['chainage'][0],b['chainage'][1]).buffer(18,cap_style=2) for b in spec.get('bridges',[])]) if spec.get('bridges') else Polygon()
    footprint=line.buffer(17,join_style=2).difference(openings).difference(register_cut).difference(buildings)
    samples=[]
    for p in getattr(footprint,'geoms',[footprint]):
        if p.geom_type!='Polygon':continue
        p=segmentize(p,5);samples.extend(p.exterior.coords)
        for hole in p.interiors:samples.extend(hole.coords)
    for d in np.arange(0,line.length,4):
        c=line.interpolate(d);a=line.interpolate(max(0,d-1));b=line.interpolate(min(line.length,d+1))
        dx,dz=b.x-a.x,b.y-a.y;length=math.hypot(dx,dz)
        for offset in [-13,-11,-9,-7.5,-6,-4.5,0,4.5,6,7.5,9,11,13]:  # rows across the 1:1.75 side slopes
            q=Point(c.x-dz/length*offset,c.y+dx/length*offset)
            if footprint.contains(q):samples.append((q.x,q.y))
    tolerant=footprint.buffer(.00001)
    rail_triangles=[list(t.exterior.coords)[:3] for t in triangulate(MultiPoint(samples)) if tolerant.covers(t)]
    mesh=[]
    crest_half,side=r['levelProfile']['crestHalfWidth'],r['levelProfile']['sideSlope']
    def bank(x,z):
        # Crest 0.05 m above the formation at its chainage, side slopes at the register's 1 in 1.75
        # (measured on the OS hatching) down to 0.05 m, or 0.2 m below a lower formation; the main
        # landscape refits them to the drawn ground.
        f=level(line.project(Point(x,z)))
        return round(float(bank_level(f+.05,line.distance(Point(x,z)),crest_half,side,min(.05,f-.2))),3)
    for tri in rail_triangles:
        mesh.append([[x,bank(x,z),z] for x,z in tri])
    crossings=[];details=[]
    cuts=line.intersection(openings)
    for part in getattr(cuts,'geoms',[cuts]):
        if part.geom_type!='LineString' or part.length<=1:continue
        a,b=sorted(line.project(Point(q)) for q in (part.coords[0],part.coords[-1]))
        if any(a<bb['chainage'][1] and b>bb['chainage'][0] for bb in spec.get('bridges',[])):continue
        crossings.append(list(part.coords));details.append({'chainage':[round(a,2),round(b,2)],'formation':round(level((a+b)/2),3),'kind':'mapped opening (water or street)'})
    for bridge,a,b in register_spans:
        crossings.append([list(q) for q in substring(line,a,b).coords])
        details.append({'chainage':[round(a,2),round(b,2)],'formation':bridge['deckFormation'],'kind':'register bridge','id':bridge['id']})
    level_note=(' Formation levels from the OS level register (data/maps/railway-levels.json): '+'; '.join(f"{g['kind']} {g['from']}-{g['to']} m" for g in spec['segments'])+'.') if spec else ''
    railways.append({**r,'embankment':mesh,'crossings':crossings,'crossingDetails':details,'levelStations':level_stations(r),
                     'evidence':r['evidence']+(level_note or ' Raised formation at 5.5 m above local marsh datum, side slopes and bridge details interpreted from author direction; not surveyed levels.')})
# Clearances under the register bridges: deck soffit (the drawn iron deck is 0.5 m deep) over the
# rail top of a railway passing beneath and over the OS ground readings of a road beneath.
for rail in railways:
    spec=levels_register['railways'].get(rail['name'],{});line=LineString(rail['route']);records=[]
    for bridge in spec.get('bridges',[]):
        soffit=bridge['deckFormation']-.5;under=[]
        for item in bridge['crosses']:
            if 'groundSpotHeights' in item:
                ids={c['spotHeight']:c for c in spec['controls']}
                ground=max(ids[i]['sceneY'] for i in item['groundSpotHeights'])
                under.append({'what':item['what'],'level':ground,'basis':'highest OS road reading under the span','clearanceMetres':round(soffit-ground,2)})
                continue
            other=next(o for o in railways if o['name'].startswith(item['what'].replace('G.E.R.','Great Eastern Railway,')))
            hit=LineString(other['route']).intersection(line)
            s=LineString(other['route']).project(hit);top=float(np.interp(s,other['levelProfile']['chainage'],other['levelProfile']['formation']))+other['levelProfile']['railTopAboveFormation']
            under.append({'what':item['what'],'level':round(top,3),'basis':f"rail top of the traced {other['name']} at its chainage {s:.1f} (the trace runs about 12 m east of the OS rails here, under the Manor Road span)",'clearanceMetres':round(soffit-top,2)})
        records.append({'id':bridge['id'],'deckFormation':bridge['deckFormation'],'soffit':round(soffit,3),'under':under})
    if records:rail['levelProfile']['bridges']=records
railways.append(build_great_eastern(water,roads,buildings,sewer))
from woolwich_connection import build_woolwich_connection
from stratford_station_rail_alignment import station_formation_obstacles
branch_road_clearance=unary_union([LineString(r['route']).buffer(r['width']/2) for r in routes])
station_bank_obstacles=station_formation_obstacles(branch_connection,railways[-1]['route'])
railways.append(build_woolwich_connection(water,branch_road_clearance,buildings,railways[-1],station_bank_obstacles))
from north_london_connection import build_north_london_connection, apply_mainline_crossing
northern=build_north_london_connection(water,branch_road_clearance,buildings,railways[-1])
railways[-2]=apply_mainline_crossing(railways[-2],northern,water,branch_road_clearance,buildings)
railways.append(northern)
result={'sources':'data/maps/road-traces.json; data/maps/district-road-traces.json; data/maps/great-eastern-mainline.json; OS housing registration; southwest holder registration',
        'limitations':'Centrelines approximate; widths, paving, railway levels and bridge structures interpreted. Registration can differ by tens of metres. Buildings and waterways clipped out of road surface; named mapped crossings bridged separately.',
        'roads':routes,'roadTriangles':triangles(drawn_roads),'shoulderTriangles':triangles(shoulder.difference(deck_ends)),'pathTriangles':triangles(path.difference(deck_ends) if path.intersection(deck_ends).area>1e-9 else path),'roadBridges':bridges,'railways':railways,'sewerBanks':sewer_banks}
result['sewerHighStreet']=crossing_spec
result['sewerCrestTriangles']=crest_triangles
result['sewerRailEdges']=sewer_edges
remaining=drawn_roads
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
assert abs(road_mesh_area-drawn_roads.area)/drawn_roads.area<.002,(road_mesh_area,drawn_roads.area)
result['deckEndFootways']=deck_end_footways
result['districtSources']=district['sources']
result['districtNotes']=district['notes']
result['housingSources']=housing['sources']
result['housingNotes']='Street-facing envelopes and junction breaks audited together. Rear plots are not treated as lanes. Widths and facades remain approximate; see housing-road-traces.json for corrections and omissions.'
# Railways in the core box follow the OS level register; the others keep their traced heights.
assert all(r.get('levelProfile') or r['formationHeight']>4 or
           (r.get('id')=='north-london-connection' and r['formationHeight']==3)
           for r in railways)
# The Abbey Mills curve meets the LT&SR and the Woolwich branch at one level.
by_name={r['name']:r for r in railways}
curve_rail=by_name['Abbey Mills junction curve']
for end,other in [(0,'London, Tilbury and Southend Railway'),(-1,'Great Eastern Railway, Woolwich branch')]:
    o=by_name[other];s=LineString(o['route']).project(Point(curve_rail['route'][end]))
    assert abs(curve_rail['levelProfile']['formation'][end]-np.interp(s,o['levelProfile']['chainage'],o['levelProfile']['formation']))<.01,('junction level',other)
assert all(math.isfinite(v) for r in railways for t in r['embankment'] for p in t for v in p)
(ROOT/'docs/data/infrastructure.json').write_text(json.dumps(result,separators=(',',':'))+'\n')
print(f"Infrastructure: {len(routes)} street/lane traces, {len(bridges)} road crossing segments, {len(railways)} raised railway routes; road/building/water checks passed.")
