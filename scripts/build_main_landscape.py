"""Apply the regional marsh reconstruction to the detailed industrial scene.

Preserve native mesh topology, beds, railway grades and sewer cover. Refit dry
land and embankment feet; supply coherent premises levels for seating buildings.
"""
import hashlib
import json
from pathlib import Path
import numpy as np
import shapely
from scipy.spatial import cKDTree
from scipy.ndimage import distance_transform_edt, map_coordinates
from shapely.geometry import Polygon, LineString, box
from shapely.ops import transform
from regional_continuous_structures import Banks, polygon_bng

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/data';inputs=[]
def read(path,binary=False):
    p=ROOT/path;inputs.append(p)
    return np.fromfile(p,'<f4') if binary else json.loads(p.read_text())
def local(g):return transform(lambda e,n:(np.asarray(e)-538900,183209-np.asarray(n)),g)
def geometry(parts):return shapely.union_all([Polygon(p[0],p[1:]) for p in parts])
def rings(g):return [[list(p.exterior.coords),*[list(r.coords) for r in p.interiors]] for p in shapely.get_parts(g) if p.geom_type=='Polygon' and p.area>1e-6]
meta=read('docs/data/lower-lea-region/landscape-1900.json');shape=(meta['height'],meta['width']);step=meta['cellSizeMetres'];e0,n0,e1,n1=meta['boundsBNG'];offset=meta['verticalReference']['odnMinusSceneYMetres']
ground=read('docs/data/lower-lea-region/'+meta['groundFile'],True).reshape(shape)-offset
support=read('docs/data/lower-lea-region/'+meta['earlyMarshWeightFile'],True).reshape(shape)
final=read('docs/data/lower-lea-region/'+meta['heightFile'],True).reshape(shape)-offset
valid=np.isfinite(ground);nearest=distance_transform_edt(~valid,return_distances=False,return_indices=True);filled=ground[tuple(nearest)]
plan=read('docs/data/ground-plan.json');infra=read('docs/data/infrastructure.json');network=read('docs/data/river-network.json');system=read('docs/data/river-system-1900.json');core=read('docs/data/river-terrain.json');historic=read('docs/data/terrain-1900.json');audit=read('docs/data/lower-lea-region/elevation-audit.json');config=read('data/maps/lower-lea-region/continuous-embankments-1900.json')
banks=Banks(system,audit,config);water=local(banks.water).union(geometry([p for r in plan['rivers'] for p in r['polygons']])).union(geometry([p for f in network['marshDitches']['features'] for p in f['renderPolygons']]))
shapely.prepare(water)
# The river network's own tidal water (the tide polygons the scene draws as
# water, rising and falling over the network's river-side shelves) is water to
# the bank blend and the edge batters as well: neither raises ground inside it,
# so the network keeps its own bank faces there. Street levels, retaining-wall
# sides and the fill behind those walls (which stand inside this outline) keep
# the regional mask above. Within TIDAL_BUILDING_M of a mapped
# building the outline is not applied: the building frontage (its wharf or
# quay ground) keeps the bank blend, falling at 1:1.5 to the tidal shelf.
tidal=geometry(network['tide']['polygons'])  # blend_water (below) once building footprints are known
def sample(grid,points):
    rc=np.array([(n1-(183209-points[:,1]))/step-.5,((538900+points[:,0])-e0)/step-.5])
    return map_coordinates(grid,rc,order=1,mode='constant',cval=0)
def weight(points):return sample(support,points)
records={r['id']:r for r in audit['records']};yard_features=[f for f in meta['laterSurfaceLayers']['features'] if f['kind']==11]
pads=[];pad_geoms=[]
for site in plan['sites']:
    polygon=geometry(site['polygons']);p=polygon.representative_point();centre=np.array([[p.x,p.y]])
    if weight(centre)[0]<=0:continue
    matched=next((f for f in yard_features if f['name']==site['name']),None)
    if matched:
        height=float(np.median([records[id]['provisionalODNMetres']-offset for id in matched['sourceIds']]))
        method='median of same-premises historical yard readings';ids=matched['sourceIds']
    else:
        points=np.array([list(polygon.representative_point().coords)[0],*list(shapely.get_coordinates(polygon))[::max(1,len(shapely.get_coordinates(polygon))//16)]])
        height=max(-.1,float(np.median(sample(filled,points))))
        method='marsh-supported premises estimate; retain at least the existing interpreted -0.1 m site floor';ids=[]
    pads.append({'siteId':site['id'],'name':site['name'],'groundSceneY':height,'method':method,'sourceIds':ids})
    pad_geoms.append(polygon)
pad_tree=shapely.STRtree(pad_geoms)
# Street observations stay on their mapped corridors, including their ground
# shoulders; never propagate across the wider marsh or through a watercourse.
# Footpaths (kind 'path') are not streets: a riverside path across the marsh
# lies on the ground it crosses (marsh, bank slope, yard, wall fill), its few
# centimetres of cinder drawn above that ground by docs/infrastructure.js, so it
# takes no level of its own from street readings. Only inside the Northern
# Outfall Sewer embankment footprint does a path corridor keep its former
# street level, so the embankment toes it reaches stay as they were.
sewer_zone=shapely.union_all([Polygon([(v[0],v[2]) for v in t]).buffer(0) for t in infra['sewerBanks']]+[Polygon(t).buffer(0) for t in infra['sewerCrestTriangles']]).buffer(1)
road_fits=[];path_corridors=[]
for feature in meta['laterSurfaceLayers']['features']:
    if feature['kind']!=10:continue
    road=next(r for r in infra['roads'] if r['name']==feature['name'])
    line=LineString(road['route']);ids=feature['sourceIds'];corridor=line.buffer(road['width']/2+3)
    if road.get('kind')=='path':
        corridor=corridor.intersection(sewer_zone)
        path_corridors.append({'name':road['name'],'widthMetres':road['width'],'lengthMetres':round(line.length,1),'streetReadingsNotApplied':ids,'sewerEmbankmentStubM2':round(corridor.area,1)})
        if corridor.is_empty:continue
    positions=np.array([[records[id]['positionBNG'][0]-538900,183209-records[id]['positionBNG'][1]] for id in ids])
    levels=np.array([records[id]['provisionalODNMetres']-offset for id in ids])
    road_fits.append((road,corridor,positions,levels,cKDTree(positions),ids))
road_tree=shapely.STRtree([fit[1] for fit in road_fits])
# Abbey Lane's approaches are graded to the abbey-mill-crossing deck (whose
# height is an interpretation in road-traces.json): level with the deck for
# 2 m beyond each end, then at no more than 1 in 20, so the street meets the
# deck instead of standing above it. The drawn road surface lies 0.065 m above
# this ground (docs/infrastructure.js).
DECK_GRADE=.05;DECK_LANDING_M=2;DECK_ROAD_OFFSET=.065;DECK_APPROACH_M=20
graded_decks={j:[(LineString(b['route']),b['height']-DECK_ROAD_OFFSET,b['id']) for b in infra['roadBridges'] if b['id']=='abbey-mill-crossing' and b['name']==fit[0]['name']] for j,fit in enumerate(road_fits)}
graded_decks={j:v for j,v in graded_decks.items() if v}
# A street passing under the Northern Outfall Sewer deck (a sewer bank end of
# kind 'road' with a roadAxis) keeps its own unraised ground there: the marsh
# level at the middle of the opening. Its corridor level is held to that for
# DECK_LANDING_M beyond the opening axis and may rise from it at no more than
# 1 in 20, so a reading whose 120 m reach ends under the deck (Mill Meads works
# road, 2.83 m scene at Abbey Road) neither stands under the arch nor drops off
# at the end of its reach. docs/sewer-crossing.js springs the street arch from
# the street centreline under the deck.
underpasses={}
for end in plan['neighbourhood']['sewer']['bankEnds']:
    if end.get('kind')!='road' or not end.get('roadAxis'):continue
    for j,fit in enumerate(road_fits):
        if fit[0]['name']!=end['road']:continue
        axis=LineString(end['roadAxis']);centre=np.array(axis.interpolate(.5,normalized=True).coords)
        underpasses.setdefault(j,{})[tuple(np.round(axis.coords,2).ravel())]=(axis,float(sample(filled,centre)[0]),end['road'])
underpasses={j:list(v.values()) for j,v in underpasses.items()}
def road_fit_levels(j,points):
    """Street level of corridor j at points: inverse-distance from the corridor's
    own readings, never through water; NaN where no reading is in reach."""
    road,footprint,positions,levels,tree,ids=road_fits[j];out=np.full(len(points),np.nan)
    if not len(points):return out
    d,ii=tree.query(points,k=min(4,len(positions)))
    if d.ndim==1:d=d[:,None];ii=ii[:,None]
    links=shapely.linestrings(np.stack([np.broadcast_to(points[:,None,:],(*ii.shape,2)),positions[ii]],axis=2).reshape(-1,2,2))
    clear=~shapely.intersects(links,water).reshape(ii.shape)
    w=np.where(clear&(d<=120),1/np.maximum(d,3)**2,0);total=w.sum(axis=1);ok=total>0
    out[ok]=(levels[ii[ok]]*w[ok]).sum(axis=1)/total[ok]
    for line,deck,_ in graded_decks.get(j,[]):
        reach=DECK_GRADE*np.maximum(0,shapely.distance(shapely.points(points),line)-DECK_LANDING_M)
        out=np.clip(out,deck-reach,deck+reach)
    for axis,street,_ in underpasses.get(j,[]):
        out=np.minimum(out,street+DECK_GRADE*np.maximum(0,shapely.distance(shapely.points(points),axis)-DECK_LANDING_M))
    return out
def road_levels(points,result,assigned=None):
    matches=road_tree.query(shapely.points(points),predicate='within')
    if not matches.size:return result
    for j in np.unique(matches[1]):
        indices=matches[0][matches[1]==j];value=road_fit_levels(j,points[indices]);ok=np.isfinite(value)
        result[indices[ok]]=value[ok]
        if assigned is not None:assigned[indices[ok]]=True
    return result

def base(points,edges=True):
    """Premises pads and street corridors at their own levels; with edges, the
    bank-foot frontage fill and the earth batters outside them (see below)."""
    marsh=sample(filled,points);result=marsh.copy();pad=np.zeros(len(points),bool);street=np.zeros(len(points),bool)
    matches=pad_tree.query(shapely.points(points),predicate='within')
    if matches.size:
        for j in np.unique(matches[1]):result[matches[0][matches[1]==j]]=pads[j]['groundSceneY']
        pad[matches[0]]=True
    if edges:result=frontage_levels(points,result,pad)
    result=road_levels(points,result,street)
    # A higher neighbour's batter may run into a lower yard (never over its
    # buildings), but never onto a street corridor.
    return edge_batter(points,result,street) if edges else result

# Retaining walls are masonry: the coping runs level or in gentle grades, and
# the land behind is filled to it. The crest follows the observed along-bank
# profile where the marsh reconstruction applies 6 m behind the wall (otherwise
# the original 1.65 m interpretive crest), averaged along the wall and limited
# to a gentle grade. Land side = side with fewer wet samples 1-5 m out.
retaining=network['retainingEdges'];WALL_MEAN_M=20;WALL_GRADE=.02;WALL_INLAND_M=6
WALL_TOP_M=3.4;WALL_BATTER=1.5;WALL_REACH_M=10
wall_levels=[];wall_rows=[]
for route_index,route in enumerate(retaining['routes']):
    p=np.array(route,dtype=float);seg=np.diff(p,axis=0);length=np.linalg.norm(seg,axis=1);chain=np.r_[0,np.cumsum(length)]
    usable=length>1e-9;unit=np.zeros_like(seg);unit[usable]=seg[usable]/length[usable,None];left=np.column_stack([-unit[:,1],unit[:,0]])
    if not usable.any():wall_levels.append([float(retaining['crestHeight'])]*len(p));continue
    # Densely sampled stations carry the along-wall averages.
    n=max(2,int(np.ceil(chain[-1]))+1);s=np.linspace(0,chain[-1],n)
    k=np.clip(np.searchsorted(chain,s,side='right')-1,0,len(seg)-1)
    k=np.flatnonzero(usable)[np.abs(np.flatnonzero(usable)[None,:]-k[:,None]).argmin(axis=1)]
    q=np.column_stack([np.interp(s,chain,p[:,0]),np.interp(s,chain,p[:,1])]);nq=left[k]
    wet=[sum(shapely.contains_xy(water,*(q+sign*o*nq).T).sum() for o in range(1,6)) for sign in (1,-1)]
    side=1 if wet[0]<=wet[1] else -1;nq=side*nq
    bank_crest=banks.crest(np.column_stack([538900+q[:,0],183209-q[:,1]]))-offset
    raw=retaining['crestHeight']+weight(q+WALL_INLAND_M*nq)*(bank_crest-retaining['crestHeight'])
    half=WALL_MEAN_M/2;mean=np.array([raw[abs(s-x)<=half].mean() for x in s])
    at=np.interp(chain,s,mean)
    # Grade-limited upper envelope: adjacent copings differ by at most 2 cm per metre.
    crest=(at[None,:]-WALL_GRADE*abs(chain[:,None]-chain[None,:])).max(axis=1)
    wall_levels.append(crest.tolist())
    for j in np.flatnonzero(usable):
        wall_rows.append((p[j],p[j+1],crest[j],crest[j+1],side*left[j],route_index))
wall_a=np.array([r[0] for r in wall_rows]);wall_b=np.array([r[1] for r in wall_rows]);wall_crest=np.array([[r[2],r[3]] for r in wall_rows])
wall_normal=np.array([r[4] for r in wall_rows]);wall_route=np.array([r[5] for r in wall_rows])
wall_tree=shapely.STRtree(shapely.linestrings(np.stack([wall_a,wall_b],axis=1)))
# Street corridors keep their own observed levels and building footprints keep
# their premises ground; the fill never overrides either.
factory=read('docs/data/factory-buildings.json');footprints=[]
for b in factory['buildings']:
    footprints+=[Polygon(p['outer'],p.get('holes',[])).buffer(0) for p in b.get('renderPolygons') or []]
footprints+=[shapely.Point(h['x'],h['z']).buffer(h['radius']) for h in factory['holders']]
footprints+=[Polygon(b['footprint']).buffer(0) for k in ('mappedFactories','houses','terraces') for b in plan['neighbourhood'][k] if b.get('footprint')]
wall_exclusion=shapely.union_all([fit[1] for fit in road_fits]+footprints);shapely.prepare(wall_exclusion)

# Yard and street edges. Premises pads and street corridors stay level inside
# their outlines. Outside, the ground meets them on an earth batter that falls
# at 1:1.5 from the edge until it meets the surrounding ground, so its width
# follows the level difference (at most EDGE_REACH_M). Where a raised pad stands
# within FRONTAGE_M of a regional bank, the strip between the yard edge and the
# bank is made up to the lower of the yard and bank-crest levels, so no trench
# is left at the bank foot. Neither raises water, nor ground steeper than 1:1.5
# above low water from the water's edge or above a building's ground from its
# footprint (its premises level, or its unraised ground if it has no pad).
EDGE_BATTER=1.5;EDGE_REACH_M=8;FRONTAGE_M=40;FRONTAGE_SHORE_JUMP_M=5
pad_level={p['siteId']:p['groundSceneY'] for p in pads};footprint_geoms=[];footprint_caps=[]
for b in factory['buildings']:
    for p in b.get('renderPolygons') or []:footprint_geoms.append(Polygon(p['outer'],p.get('holes',[])).buffer(0));footprint_caps.append(pad_level.get(b.get('siteId'),-np.inf))
for h in factory['holders']:footprint_geoms.append(shapely.Point(h['x'],h['z']).buffer(h['radius']));footprint_caps.append(pad_level.get(h.get('siteId'),-np.inf))
for k in ('mappedFactories','houses','terraces'):
    for b in plan['neighbourhood'][k]:
        if b.get('footprint'):footprint_geoms.append(Polygon(b['footprint']).buffer(0));footprint_caps.append(pad_level.get(b.get('siteId'),-np.inf))
# The other seated buildings: High Street frontages, housing rows, the station
# and its supporting buildings, and the corn mill (a rotated box in the scene).
station=read('docs/data/abbey-station-plan.json')
for b in [*read('docs/data/high-street-frontages.json')['buildings'],*read('docs/data/housing-detail.json')['rows'],{'footprint':station['worldFootprint']},*station['supportingBuildings']]:
    if b.get('footprint'):footprint_geoms.append(Polygon(b['footprint']).buffer(0));footprint_caps.append(pad_level.get(b.get('siteId'),-np.inf))
mill=plan['neighbourhood']['mill'];turn=np.radians(mill['rotation']);corner=np.array([[sx*mill['width']/2,sz*mill['depth']/2] for sx,sz in ((-1,-1),(1,-1),(1,1),(-1,1))])
footprint_geoms.append(Polygon(np.column_stack([mill['x']+corner[:,0]*np.cos(turn)+corner[:,1]*np.sin(turn),mill['z']-corner[:,0]*np.sin(turn)+corner[:,1]*np.cos(turn)])));footprint_caps.append(pad_level.get(mill.get('siteId'),-np.inf))
footprint_tree=shapely.STRtree(footprint_geoms);footprint_caps=np.array(footprint_caps)
TIDAL_BUILDING_M=5;tidal_frontage=shapely.union_all(footprint_geoms).buffer(TIDAL_BUILDING_M)
blend_water=water.union(tidal.difference(tidal_frontage));shapely.prepare(blend_water)
water_edges=[]
for ring in shapely.get_parts(shapely.boundary(blend_water)):
    for part in shapely.get_parts(ring):
        c=shapely.get_coordinates(part);water_edges+=list(np.stack([c[:-1],c[1:]],axis=1))
water_edge_tree=shapely.STRtree(shapely.linestrings(np.array(water_edges)))
def edge_caps(points,level,current):
    """Limit raised edge ground at points to 1:1.5 above low water from the
    water's edge, and to 1:1.5 above a building's ground from its footprint
    (its premises level, or the unraised ground for a building without one),
    so the fill neither enters the water nor buries a building wall."""
    pts=shapely.points(points);i,dw=water_edge_tree.query_nearest(pts,max_distance=EDGE_REACH_M,return_distance=True,all_matches=False)
    cap=np.full(len(points),np.inf);cap[i[0]]=network['waterLevel']+.02+dw/EDGE_BATTER
    cap[shapely.contains_xy(blend_water,points[:,0],points[:,1])]=-np.inf
    fi,fk=footprint_tree.query(pts,predicate='dwithin',distance=EDGE_REACH_M)
    if len(fi):
        floor=np.where(np.isfinite(footprint_caps[fk]),footprint_caps[fk],current[fi])
        np.minimum.at(cap,fi,floor+shapely.distance(footprint_tree.geometries[fk],pts[fi])/EDGE_BATTER)
    return np.minimum(level,np.maximum(cap,current))
def crest_at(points):return banks.crest(np.column_stack([538900+points[:,0],183209-points[:,1]]))-offset
# Bank-foot frontage: rays from the yard edge (every metre) to the nearest
# regional shoreline, kept where they are 0.6-40 m long and cross neither the
# yard, water nor a railway embankment; consecutive rays bound the strip
# between yard and bank.
shore_local=local(shapely.MultiLineString(banks.lines));pad_union=shapely.union_all(pad_geoms);frontages=[]
rail_bodies=shapely.union_all([LineString(r['route']).buffer(r.get('baseHalfWidth',15)) for r in infra['railways']]);shapely.prepare(rail_bodies)
for j,polygon in enumerate(pad_geoms):
    if polygon.distance(shore_local)>FRONTAGE_M:continue
    quads=[]
    for part in shapely.get_parts(polygon):
        q=shapely.get_coordinates(part.exterior.segmentize(1))[:-1];n=len(q)
        s=shapely.get_coordinates(shapely.shortest_line(shapely.points(q),shore_local)).reshape(-1,2,2)[:,1]
        v=s-q;length=np.linalg.norm(v,axis=1);u=v/np.maximum(length,1e-9)[:,None]
        ray=shapely.linestrings(np.stack([q+.3*u,s-.3*u],axis=1))
        ok=(length>.6)&(length<=FRONTAGE_M);ok[ok]=~shapely.intersects(ray[ok],polygon)&~shapely.intersects(ray[ok],water)&~shapely.intersects(ray[ok],rail_bodies)
        k=np.flatnonzero(ok&np.roll(ok,-1)&(np.linalg.norm(s-np.roll(s,-1,axis=0),axis=1)<=FRONTAGE_SHORE_JUMP_M));k1=(k+1)%n
        quads+=list(shapely.make_valid(shapely.polygons(np.stack([q[k],q[k1],s[k1],s[k]],axis=1))))
    strip=shapely.union_all(quads).buffer(.25).buffer(-.25).difference(pad_union).difference(water) if quads else Polygon()
    strip=shapely.union_all([g for g in shapely.get_parts(strip) if g.geom_type=='Polygon' and g.area>1])
    if not strip.is_empty:frontages.append((strip,j))
front_tree=shapely.STRtree([f[0] for f in frontages])
def frontage_levels(points,result,pad):
    if not frontages:return result
    m=front_tree.query(shapely.points(points),predicate='within')
    level=np.full(len(points),-np.inf)
    for k in np.unique(m[1]):
        idx=m[0][m[1]==k];idx=idx[~pad[idx]]
        level[idx]=np.maximum(level[idx],np.minimum(pads[frontages[k][1]]['groundSceneY'],crest_at(points[idx])))
    some=np.flatnonzero(level>result)
    if len(some):result[some]=np.maximum(result[some],edge_caps(points[some],level[some],result[some]))
    return result
# Batter sources: each outline with the level at its nearest edge point.
edge_sources=[(g,(lambda q,y=p['groundSceneY']:np.full(len(q),y))) for g,p in zip(pad_geoms,pads)]
edge_sources+=[(g,(lambda q,y=pads[j]['groundSceneY']:np.minimum(y,crest_at(q)))) for g,j in frontages]
edge_sources+=[(fit[1],(lambda q,j=j:road_fit_levels(j,q))) for j,fit in enumerate(road_fits)]
edge_tree=shapely.STRtree([s[0] for s in edge_sources]);edge_geoms=np.array([s[0] for s in edge_sources],dtype=object)
def edge_batter(points,result,street):
    cand=np.flatnonzero(~street)
    if not len(cand):return result
    pts=shapely.points(points[cand]);pi,si=edge_tree.query(pts,predicate='dwithin',distance=EDGE_REACH_M)
    if not len(pi):return result
    c=shapely.get_coordinates(shapely.shortest_line(edge_geoms[si],pts[pi])).reshape(-1,2,2);q=c[:,0];d=np.linalg.norm(c[:,1]-q,axis=1)
    top=np.full(len(si),np.nan)
    for k in np.unique(si):sel=si==k;top[sel]=edge_sources[k][1](q[sel])
    ok=np.isfinite(top);level=np.full(len(cand),-np.inf);np.maximum.at(level,pi[ok],(top-d/EDGE_BATTER)[ok])
    some=np.flatnonzero(level>result[cand])
    if len(some):
        idx=cand[some];result[idx]=np.maximum(result[idx],edge_caps(points[idx],level[some],result[idx]))
    return result
# Abbey Lane's approach keeps its graded street level through the regional bank
# band (it crosses the bank onto the deck); the bank beside it is cut back at 1:1.5.
deck_zones=[(road_fits[j][1].intersection(line.buffer(DECK_APPROACH_M)).difference(line.buffer(road_fits[j][0]['width']/2+1.1,cap_style='flat')),j) for j,v in graded_decks.items() for line,_,_ in v]
# Under the deck itself (the road-surface exclusion of build_infrastructure.py)
# the bank stays 0.1 m below the 0.4 m deck slab, rising beside it at 1:1.5.
deck_under=[(line.buffer(road_fits[j][0]['width']/2+1.1,cap_style='flat'),deck+DECK_ROAD_OFFSET-.5) for j,v in graded_decks.items() for line,deck,_ in v]
for zone in [*[d[0] for d in deck_zones],*[d[0] for d in deck_under]]:shapely.prepare(zone)
# Where no wall stands (beyond wall ends, ditch mouths) the fill is battered
# down to the water's edge at the same 1:1.5, so it never stands as a cliff.
wall_lines=shapely.union_all([LineString(r) for r in retaining['routes'] if len(r)>1])
open_shore=water.boundary.intersection(wall_lines.buffer(WALL_REACH_M+WALL_TOP_M+5)).difference(wall_lines.buffer(.3))
def wall_fill(points):
    """Land-side fill level behind retaining walls (-inf where none applies).

    Level with the coping for 3.4 m from the wall line (the 0.32 m wall plus a
    3 m berm top), then falling at 1:1.5 until it meets the surrounding ground.
    """
    level=np.full(len(points),-np.inf)
    pi,si=wall_tree.query(shapely.points(points),predicate='dwithin',distance=WALL_REACH_M)
    if not len(pi):return level
    a=wall_a[si];ab=wall_b[si]-a;ap=points[pi]-a
    t=np.clip((ap*ab).sum(axis=1)/(ab*ab).sum(axis=1),0,1);d=np.linalg.norm(ap-t[:,None]*ab,axis=1)
    # The nearest segment of each wall decides which side a point is on.
    order=np.lexsort((d,wall_route[si],pi));pi,si,t,d,ap=pi[order],si[order],t[order],d[order],ap[order]
    first=np.r_[True,(pi[1:]!=pi[:-1])|(wall_route[si][1:]!=wall_route[si][:-1])]
    land=first&((ap*wall_normal[si]).sum(axis=1)>0)
    crest=wall_crest[si,0]+t*(wall_crest[si,1]-wall_crest[si,0])
    np.maximum.at(level,pi[land],(crest-np.maximum(0,d-WALL_TOP_M)/WALL_BATTER)[land])
    level[shapely.contains_xy(wall_exclusion,points[:,0],points[:,1])]=-np.inf
    some=np.flatnonzero(np.isfinite(level))
    if len(some) and not open_shore.is_empty:
        cap=network['waterLevel']+.02+shapely.distance(shapely.points(points[some]),open_shore)/WALL_BATTER
        level[some]=np.minimum(level[some],cap)
    return level

def fill_behind_walls(points,out):
    fill=wall_fill(points);raise_=np.flatnonzero(fill>out)
    if len(raise_):
        dry=~shapely.contains_xy(water,points[raise_,0],points[raise_,1])
        out[raise_[dry]]=fill[raise_[dry]]
    return out

def surface(points,old,bank=True):
    out=blend_surface(points,old,bank)
    return fill_behind_walls(points,out)

# Recorded raised shore edges: the river system's interpreted canal faces
# (Limehouse Cut), the river network's interpretive retaining edges, and the
# reviewed river-system terrain patches whose recorded shore transition is no
# wider than the lip itself. Every other shore is an earth or canal-earth bank.
MASONRY_REACH_M=1.5;LIP_M=.6;lip_vertices={};tidal_kept={}
masonry=shapely.union_all([LineString(r['route']) for r in system['bankSections']['canalFacingRoutes']]+[LineString(r) for r in network['retainingEdges']['routes'] if len(r)>1])
steep_patches=[t for t in system['bankSections']['terrainPatches'] if t['config']['shoreTransitionMetres'][1]<=LIP_M]
masonry_zone=masonry.buffer(MASONRY_REACH_M);patch_zone=geometry([p for t in steep_patches for p in t['polygons']])
raised_shore=masonry_zone.union(patch_zone)
for zone in (masonry_zone,patch_zone,raised_shore):shapely.prepare(zone)
def blend_surface(points,old,bank=True,key='groundMesh'):
    w=weight(points);out=np.asarray(old,dtype=float).copy();selected=w>0
    if not selected.any():return out
    p=points[selected];g=base(p);wet=shapely.contains_xy(blend_water,p[:,0],p[:,1]);old_y=out[selected]
    if bank:
        bng=np.column_stack([538900+p[:,0],183209-p[:,1]]);pts=shapely.points(bng)
        near=banks.segment_tree.nearest(pts);distance=shapely.distance(pts,banks.segments[near])
        margin=(distance<14)&~wet
        if margin.any():
            d=distance[margin];crest=np.maximum(g[margin],banks.crest(bng[margin])-offset)
            inland=np.clip((14-d)/8,0,1)
            # Preserve a wet-side bank face, then crest, then dry-side toe.
            rise=np.clip(d/3,0,1);rise=rise*rise*(3-2*rise)
            levels=g[margin]+inland*(crest-g[margin])
            # An existing raised lip is kept only on a recorded raised shore
            # edge: lifted to the crest against masonry (canal faces, retaining
            # walls, whose copings follow the crest), held at its reviewed
            # height (never above the crest) in a steep-shore patch. Earth and
            # canal-earth banks take the smoothstep face above.
            lip=np.flatnonzero((d<LIP_M)&(old_y[margin]>network['waterLevel']+.5))
            q=p[margin][lip];wall=shapely.contains_xy(masonry_zone,q[:,0],q[:,1])
            held=~wall&shapely.contains_xy(patch_zone,q[:,0],q[:,1])
            levels[lip[held]]=np.minimum(levels[lip[held]],old_y[margin][lip[held]])
            tally=lip_vertices.setdefault(key,{'liftedToCrest':0,'heldAtReviewedHeight':0})
            tally['liftedToCrest']+=int(wall.sum());tally['heldAtReviewedHeight']+=int(held.sum());lip=lip[wall|held]
            rise[lip]=1
            # Graded deck approach: street level through the bank band, with
            # the bank beside it cut back at 1:1.5 from the street edge.
            pm=p[margin];zone=np.zeros(len(pm),bool)
            for approach,_ in deck_zones:zone|=shapely.contains_xy(approach,pm[:,0],pm[:,1])
            levels[zone]=g[margin][zone];rise[zone]=1
            for approach,j in deck_zones:
                near=np.flatnonzero(~zone&shapely.dwithin(approach,shapely.points(pm),EDGE_REACH_M))
                if not len(near):continue
                c=shapely.get_coordinates(shapely.shortest_line(approach,shapely.points(pm[near]))).reshape(-1,2,2)
                street=road_fit_levels(j,c[:,0]);ok=np.isfinite(street);near=near[ok]
                levels[near]=np.minimum(levels[near],street[ok]+np.linalg.norm(c[ok,1]-c[ok,0],axis=1)/EDGE_BATTER)
            for under,soffit in deck_under:
                d=shapely.distance(under,shapely.points(pm));near=(d<EDGE_REACH_M)&~zone
                levels[near]=np.minimum(levels[near],soffit+d[near]/EDGE_BATTER)
            levels=(network['waterLevel']+.02)*(1-rise)+levels*rise
            g[margin]=levels
    # Bed, drain-water and network tidal-water vertices retain their native
    # geometry and levels.
    tidal_kept[key]=tidal_kept.get(key,0)+int((wet&~shapely.contains_xy(water,p[:,0],p[:,1])).sum())
    use=~wet;out_indices=np.flatnonzero(selected)[use]
    out[out_indices]=old_y[use]+w[selected][use]*(g[use]-old_y[use])
    return out

WALL_HALF_M=retaining['width']/2;WALL_TOE_M=.3
wall_body=wall_lines.buffer(WALL_HALF_M)
def clear_wall_faces(points,new,blended,triangles):
    """Mesh triangles straddle the thin wall; a raised land vertex would drag
    a ground wedge up the wall's water face. Lower such vertices (never below
    the unfilled level) until no ground stands more than 0.3 m above low water,
    or above its unfilled height, at the face."""
    raised=new>blended+1e-6
    tri=triangles[raised[triangles].any(axis=1)]
    if not len(tri):return new
    polygons=shapely.polygons(points[tri]);cross=shapely.intersects(polygons,wall_body)
    tri=tri[cross];polygons=polygons[cross]
    pieces,owner=shapely.get_parts(shapely.difference(polygons,wall_body),return_index=True)
    outside=np.flatnonzero(shapely.area(pieces)>1e-9);pieces=pieces[outside];owner=owner[outside]
    wet=shapely.contains_xy(water,*shapely.get_coordinates(shapely.point_on_surface(pieces)).T)
    pieces=pieces[wet];owner=owner[wet]
    coords,which=shapely.get_coordinates(pieces,return_index=True);owner=owner[which]
    t=tri[owner];a=points[t[:,0]];b=points[t[:,1]];c=points[t[:,2]]
    m=np.stack([b-a,c-a],axis=2);det=np.linalg.det(m);ok=abs(det)>1e-12
    uv=np.zeros((len(t),2));uv[ok]=np.linalg.solve(m[ok],(coords-a)[ok][...,None])[...,0]
    bary=np.clip(np.column_stack([1-uv.sum(axis=1),uv]),0,1)
    limit=np.maximum(network['waterLevel']+WALL_TOE_M,(bary*blended[t]).sum(axis=1))
    excess=(bary*new[t]).sum(axis=1)-limit
    allowed=new.copy()
    for k in range(3):
        v=t[:,k];sel=ok&(excess>0)&raised[v]&(bary[:,k]>1e-6)
        np.minimum.at(allowed,v[sel],new[v[sel]]-excess[sel]/bary[sel,k])
    new=np.maximum(blended,allowed)
    # No fill-raised vertex may stand more than 2.4 m above a mesh neighbour,
    # so the fill itself never forms a vertical step (> 2.5 m over < 3 m).
    edges=np.unique(np.sort(np.concatenate([triangles[:,[0,1]],triangles[:,[1,2]],triangles[:,[2,0]]]),axis=1),axis=0)
    edges=edges[raised[edges].any(axis=1)]
    for _ in range(20):
        before=new.copy()
        for u,v in ((0,1),(1,0)):
            sel=raised[edges[:,v]];np.minimum.at(new,edges[sel,v],new[edges[sel,u]]+2.4)
        new=np.maximum(blended,new)
        if np.array_equal(before,new):break
    return new

# Junction end caps: where a river-network channel end meets the drawn
# river-system water, the network bank takes the same earth face as the
# system's own banks (water edge, smoothstep to the existing ground over
# 3 m), so no end-cap triangle leans over the system water. Recorded raised
# shore edges keep their height; no vertex is lowered more than 2.4 m below
# a mesh neighbour, so the cap never forms a new step.
END_FACE_M=3;system_water=geometry(system['waterPolygons']);shapely.prepare(system_water);end_caps={}
def cap_junction_ends(points,new,triangles):
    edge=network['waterLevel']+.02;pts=shapely.points(points)
    near=np.flatnonzero(shapely.dwithin(system_water,pts,END_FACE_M))
    near=near[(new[near]>edge)&~shapely.contains_xy(raised_shore,points[near,0],points[near,1])]
    d=shapely.distance(system_water.boundary,pts[near]);d[shapely.contains_xy(system_water,points[near,0],points[near,1])]=0
    s=np.clip(d/END_FACE_M,0,1);s=s*s*(3-2*s)
    cap=edge+s*(new[near]-edge);lower=cap<new[near]-1e-6;near=near[lower]
    out=new.copy();out[near]=cap[lower]
    if not len(near):return out
    moved=np.zeros(len(new),bool);moved[near]=True
    tri=triangles[moved[triangles].any(axis=1)]
    edges=np.unique(np.sort(np.concatenate([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]]),axis=1),axis=0)
    for _ in range(50):
        before=out.copy()
        for u,v in ((0,1),(1,0)):
            a=edges[:,u];b=edges[:,v];sel=moved[a]
            np.maximum.at(out,a[sel],np.minimum(new[a[sel]],out[b[sel]]-2.4))
        if np.array_equal(before,out):break
    changed=abs(out-new)>1e-6
    end_caps.update({'loweredVertices':int(changed.sum()),'maxLoweringMetres':float((new-out).max())})
    return out

# Tidal bank faces: network tidal-water ground keeps its native height, so
# blended ground beside it may stand no steeper than 1:1.5 above it (measured
# along mesh edges, or across the core grid), never below its own pre-blend
# height, nor in street corridors or building footprints. The bank crest is
# then reached a few metres back from the outline instead of standing as a
# cliff at its edge.
TIDAL_FACE=1.5;tidal_faced={}
def tidal_faces(key,points,blended,old,triangles=None):
    seed=shapely.contains_xy(blend_water,points[:,0],points[:,1]);free=~seed&(blended>old+1e-6)
    river=shapely.contains_xy(water,points[:,0],points[:,1]);seed&=~river
    # Street corridors and building footprints keep their blended ground.
    free&=~shapely.contains_xy(wall_exclusion,points[:,0],points[:,1])
    if not seed.any() or not free.any():return blended
    # The limit spreads over land and tidal ground, never across regional water.
    cap=np.where(seed,blended,np.inf)
    if triangles is not None:
        edges=np.unique(np.sort(np.concatenate([triangles[:,[0,1]],triangles[:,[1,2]],triangles[:,[2,0]]]),axis=1),axis=0)
        edges=edges[(~river)[edges].all(axis=1)];rise=np.linalg.norm(points[edges[:,0]]-points[edges[:,1]],axis=1)/TIDAL_FACE
        for _ in range(60):
            before=cap.copy()
            np.minimum.at(cap,edges[:,1],cap[edges[:,0]]+rise);np.minimum.at(cap,edges[:,0],cap[edges[:,1]]+rise)
            if np.array_equal(before,cap):break
    else:
        grid=(core['height'],core['width']);c=cap.reshape(grid);ok=(~river).reshape(grid)
        for _ in range(60):
            before=c.copy()
            for di,dj in ((0,1),(1,0),(1,1),(1,-1)):
                r=core['step']*np.hypot(di,dj)/TIDAL_FACE
                a=(slice(0,grid[0]-di),slice(max(0,-dj),grid[1]-max(0,dj)));b=(slice(di,grid[0]),slice(max(0,dj),grid[1]-max(0,-dj)))
                c[b]=np.where(ok[b],np.minimum(c[b],c[a]+r),np.inf);c[a]=np.where(ok[a],np.minimum(c[a],c[b]+r),np.inf)
            if np.array_equal(before,c):break
        cap=c.ravel()
    out=blended.copy();limit=free&(cap<blended);out[limit]=np.maximum(old[limit],cap[limit])
    tidal_faced[key]={'loweredVertices':int((out<blended-1e-6).sum()),'maxLoweringMetres':round(float((blended-out).max()),3)}
    return out
files={};stats={}
def export_heights(key,points,old,preserve=None,triangles=None):
    blended=blend_surface(points,old,key=key)
    if key in ('core','network'):blended=tidal_faces(key,points,blended,old,triangles)
    new=fill_behind_walls(points,blended.copy())
    if triangles is not None:new=clear_wall_faces(points,new,blended,triangles)
    if key=='network':new=cap_junction_ends(points,new,triangles)
    if preserve is not None:
        # Wall fill stands no steeper than 1:1.5 above preserved tidal mud.
        grid=(core['height'],core['width']);dist,nearest=distance_transform_edt(~preserve.reshape(grid),return_indices=True)
        cap=old[np.ravel_multi_index(tuple(nearest),grid)].ravel()+dist.ravel()*core['step']/WALL_BATTER
        new=np.maximum(blended,np.minimum(new,cap));new[preserve]=old[preserve]
    # Written after the road-bridge and road-corridor pass below.
    surfaces[key]={'points':points,'old':old,'new':new,'triangles':triangles,'preserve':preserve}
surfaces={}
def write_heights(key):
    s=surfaces[key];new=s['new'];old=s['old']
    name=f'main-landscape-1900.{key}.f32';new.astype('<f4').tofile(OUT/name);files[key]=name
    changed=abs(new-old)>1e-6;stats[key]={'vertices':len(old),'changedVertices':int(changed.sum()),'changeRangeMetres':[float((new-old).min()),float((new-old).max())]}
    print(key,stats[key],flush=True)
# Build from the already dated ground overlay, with the original topology.
def old_historic(points,old):
    target=read('docs/data/'+historic['files']['target'],True).reshape(historic['height'],historic['width']);w=read('docs/data/'+historic['files']['weight'],True).reshape(target.shape)
    rc=np.array([(points[:,1]-historic['bounds'][1])/historic['step'],(points[:,0]-historic['bounds'][0])/historic['step']])
    weights=map_coordinates(w,rc,order=1,mode='constant',cval=0);values=map_coordinates(target,rc,order=1,mode='nearest')
    return old+weights*(values-old)
xx,zz=np.meshgrid(np.arange(core['width'])*core['step']+core['bounds'][0],np.arange(core['height'])*core['step']+core['bounds'][1]);points=np.column_stack([xx.ravel(),zz.ravel()]);old=read('docs/data/'+core['heightFile'],True)
properties_path=ROOT/'docs/data'/core['propertyFile'];inputs.append(properties_path);properties=np.fromfile(properties_path,'u1').reshape(-1,4)
# Exposed tidal mud is a channel-bed study, not a marsh or flood-bank control.
intertidal=(properties[:,3]>200)&(properties[:,2]<80)
export_heights('core',points,old_historic(points,old),preserve=intertidal)
for key,description in [('network',network),('system',system)]:
    p=read('docs/data/'+description['positionFile'],True).reshape(-1,3);old=p[:,1].copy()
    if key=='network':
        old=old_historic(p[:,[0,2]],old)
        indices=np.array(system['coreBedCorrections'],dtype=int);old[indices]=np.minimum(-.7,old[indices])
    index_path=ROOT/'docs/data'/description['indexFile'];inputs.append(index_path)
    export_heights(key,p[:,[0,2]],old,triangles=np.fromfile(index_path,'<u4').reshape(-1,3).astype(np.int64))
p=read('docs/data/'+historic['files']['extension'],True).reshape(-1,3);export_heights('extension',p[:,[0,2]],p[:,1])
# Vertical canal faces retain their submerged foot and follow the coping above.
p=read('docs/data/'+system['faceFile'],True).reshape(-1,3);old=p[:,1].copy();w=weight(p[:,[0,2]]);bng=np.column_stack([538900+p[:,0],183209-p[:,2]])
new=old.copy();top=old>network['waterLevel']+.5;new[top]+=w[top]*(banks.crest(bng[top])-offset-old[top])
new.astype('<f4').tofile(OUT/'main-landscape-1900.faces.f32');files['faces']='main-landscape-1900.faces.f32'
# Scene sampling for objects outside the original detailed grids.
east,north=np.meshgrid(np.arange(e0+step/2,e1,step),np.arange(n1-step/2,n0,-step));points=np.column_stack([east.ravel()-538900,183209-north.ravel()]);values=base(points)
# Buildings without a premises pad are seated by sampling this field; cells
# whose bilinear reach (one cell diagonal) touches such a footprint keep the
# level without edge batters, so no building is lifted off its unraised ground.
unpadded=footprint_tree.query(shapely.points(points),predicate='dwithin',distance=step*np.sqrt(2))
held=np.unique(unpadded[0][~np.isfinite(footprint_caps[unpadded[1]])]);values[held]=base(points[held],edges=False);values=values.reshape(shape)
values.astype('<f4').tofile(OUT/'main-landscape-1900.level.f32');files['level']='main-landscape-1900.level.f32';support.astype('<f4').tofile(OUT/'main-landscape-1900.weight.f32');files['weight']='main-landscape-1900.weight.f32'
# Existing flat placeholder polygons need interior vertices, not just raised edges.
outline=local(Polygon(meta['regionalMarshBaseline']['config']['outlineBNG']))
original_base=geometry(system['baseGround']);original_regional=geometry(system['regionalGround'])
area=original_base.union(original_regional).intersection(outline).difference(water)
x0,z0,x1,z1=area.bounds;mesh_step=20
x,z=np.meshgrid(np.arange(np.floor(x0/mesh_step)*mesh_step,x1,mesh_step),np.arange(np.floor(z0/mesh_step)*mesh_step,z1,mesh_step))
cells=shapely.box(x.ravel(),z.ravel(),x.ravel()+mesh_step,z.ravel()+mesh_step)
parts=shapely.get_parts(shapely.intersection(cells,area));parts=parts[shapely.area(parts)>1e-5]
# Road surface triangles as docs/infrastructure.js draws them: carriageway,
# footway and path, each drawn its offset above the ground under its vertices,
# and the bridge decks (boxes at the deck height). The 20 m regional mesh is
# cut along them, so no tilted regional triangle spans a street: inside a street
# triangle the regional ground is planar with it (see the road pass below).
ROAD_SETS=[('carriageway',[t for k in infra['roadSurfaces'].values() for t in k],DECK_ROAD_OFFSET),('footway',infra['shoulderTriangles'],.095),('path',infra['pathTriangles'],.05)]
road_tri=np.array([t for _,ts,_ in ROAD_SETS for t in ts],dtype=float);road_offset=np.concatenate([np.full(len(ts),o) for _,ts,o in ROAD_SETS])
deck_tri=[];deck_ground=[]
for bridge in infra['roadBridges']:
    r=np.array(bridge['route'],dtype=float)
    for a_,c_ in zip(r[:-1],r[1:]):
        u_=(c_-a_)/np.linalg.norm(c_-a_);n_=np.array([-u_[1],u_[0]])*bridge['width']/2
        q_=[a_-n_,c_-n_,c_+n_,a_+n_];deck_tri+=[[q_[0],q_[1],q_[2]],[q_[0],q_[2],q_[3]]];deck_ground+=[bridge['height']-DECK_ROAD_OFFSET]*2
deck_tri=np.array(deck_tri);deck_ground=np.array(deck_ground)
all_road_tri=np.concatenate([road_tri,deck_tri]);road_polys=shapely.polygons(all_road_tri);surface_tree=shapely.STRtree(road_polys)
road_zone=shapely.union_all(road_polys);shapely.prepare(road_zone)
hit=np.flatnonzero(shapely.intersects(parts,road_zone));pieces=[parts[np.setdiff1d(np.arange(len(parts)),hit)]]
def polygon_parts(g):return [x for x in shapely.get_parts(g) if x.geom_type=='Polygon' and x.area>1e-6]
for k in hit:
    # Overlay the cell piece with every road triangle over it, so each face
    # lies wholly inside or outside each triangle (footway and street
    # triangles overlap, and their edges need not meet).
    faces=[parts[k]]
    for triangle in road_polys[surface_tree.query(parts[k],predicate='intersects')]:
        split=[]
        for f in faces:
            if not f.intersects(triangle):split.append(f);continue
            split+=polygon_parts(f.intersection(triangle))+polygon_parts(f.difference(triangle))
        faces=split
    pieces.append(np.array(faces,dtype=object))
parts=np.concatenate(pieces);parts=parts[shapely.area(parts)>1e-5]
triangles=shapely.get_parts(shapely.constrained_delaunay_triangles(parts));triangles=triangles[shapely.area(triangles)>1e-5]
coords=shapely.get_coordinates(triangles).reshape(-1,4,2)[:,:3,:]
# Upward scene winding.
a=coords[:,1]-coords[:,0];b=coords[:,2]-coords[:,0];cross=a[:,0]*b[:,1]-a[:,1]*b[:,0];coords[cross>0]=coords[cross>0][:,[0,2,1]]
points=coords.reshape(-1,2);heights=surface(points,np.full(len(points),-.1))
# The page reads these positions as float32; so does the road pass, so a road
# vertex on a sliver corner falls through (or not) exactly as it does there.
points=points.astype('<f4').astype(float)
surfaces['groundMesh']={'points':points,'old':np.full(len(points),-.1),'new':heights,'triangles':np.arange(len(points)).reshape(-1,3),'preserve':None}
# Road bridges and road corridors. docs/infrastructure.js draws each street,
# footway and path triangle at ground() under its vertices plus its offset:
# ground() is the drawn ground, raised within reach of a road bridge to the
# bridge cone (deck - 0.065 - 0.12 m per metre from the deck route) and on the
# High Street sewer approach; each deck is a box at the deck height. Here the
# landscape is fitted to those surfaces, in this order:
#  1. Approach embankments: under every road triangle within reach of a bridge
#     cone the ground is made up to the cone, so the approach stands on earth
#     rather than on a vertical fill curtain; beyond the road edge it falls at
#     1:1.5 to the surrounding ground. It never rises over water, nor steeper
#     than 1:1.5 above low water from the water's edge, above a building's
#     ground from its footprint (edge_caps) or above the outer edge of its own
#     mesh, so beside the river, against buildings and where no adjustable
#     mesh carries on, the road keeps a short walled or curtained approach.
#  2. Approach cuttings, on the bridge's own road: where the ground stands
#     above a deck, the road ground is cut to the deck road level for
#     DECK_LANDING_M from the deck route, then rises at no more than 1 in 20,
#     the sides of the cut at 1:1.5.
#  3. Span clearance: between the first and last drawn low water under each
#     deck (where the abutment faces stand), out to CLEAR_MARGIN_M beyond each
#     deck edge, no ground stands above the water edge (low water + 0.02 m).
#  4. No ground above a road: every landscape vertex inside a road or deck
#     triangle, or within one mesh edge of one, is held at or below the drawn
#     road surface there (the triangle's ground() values interpolated, plus
#     its offset, less up to ROAD_CAP_BELOW_M but keeping at least
#     ROAD_CAP_KEEP_M of the offset; under a deck, the deck top likewise).
#     The vertices the road's own vertices take their ground from are held so
#     in ROAD_SUPPORT_PASSES passes only, re-reading the road after each, and
#     the rest then in one pass that leaves the road where it stands; further
#     out, ground above the road is cut back at 1:1.5 (a cutting).
# Channel beds (network and system vertices in drawn water) and preserved tidal
# mud keep their heights throughout; nothing here touches level.f32, by which
# buildings without a premises pad are seated.
WATER_EDGE=network['waterLevel']+.02;BRIDGE_CONE=.12;CLEAR_MARGIN_M=2;CUT_REACH_M=40;ROAD_CAP_BELOW_M=.04;ROAD_CAP_KEEP_M=.025;ROAD_SUPPORT_PASSES=4
low_water=geometry(system['waterPolygons']).union(water);shapely.prepare(low_water)
building_union=shapely.union_all(footprint_geoms);shapely.prepare(building_union)
def protected(key):
    s=surfaces[key];q=s['points']
    if key=='core':return s['preserve'].copy()
    if key in ('network','system'):return shapely.contains_xy(low_water,q[:,0],q[:,1])
    return np.zeros(len(q),bool)
def route_frame(route):
    """docs/road-bridges.js routeFrame: station s along the route, offset v to its left."""
    r=np.array(route,dtype=float);seg=np.diff(r,axis=0);ln=np.linalg.norm(seg,axis=1);s0=np.r_[0,np.cumsum(ln)[:-1]];u=seg/ln[:,None]
    def at(s,v):
        s=np.asarray(s,dtype=float);k=np.clip(np.searchsorted(s0+ln,s-1e-9),0,len(seg)-1)
        return r[k]+u[k]*(s-s0[k])[:,None]+np.column_stack([-u[k][:,1],u[k][:,0]])*np.asarray(v,dtype=float)[:,None]
    return at,float(ln.sum())
span_footprints={}
for bridge in infra['roadBridges']:
    # Lines across the deck width set the span; beyond each deck edge, out to
    # the margin, the edge line's span carries on (a side channel there is not
    # under the bridge).
    at,length=route_frame(bridge['route']);half=bridge['width']/2;s=np.arange(0,length+1e-9,.1);strips=[];spans={}
    for v in np.arange(-half,half+1e-9,.25):
        q=at(s,np.full(len(s),v));wet=np.flatnonzero(shapely.contains_xy(low_water,q[:,0],q[:,1]))
        if len(wet) and s[wet[-1]]-s[wet[0]]>=.2:spans[v]=(s[wet[0]],s[wet[-1]])
    for v,(s0_,s1_) in spans.items():
        lo,hi=v-.125,v+.125
        if v==min(spans):lo=-half-CLEAR_MARGIN_M
        if v==max(spans):hi=half+CLEAR_MARGIN_M
        strips.append(Polygon(at(np.array([s0_,s1_,s1_,s0_]),np.array([lo,lo,hi,hi]))).buffer(0))
    if strips:span_footprints[bridge['id']]=shapely.union_all(strips).buffer(.01,join_style='mitre').buffer(-.01,join_style='mitre')
# The footprint also takes in the clear zone between the abutment faces of the
# road-bridge register (data/maps/road-bridge-forms.json, as docs/road-bridges.js
# bridgeLayout/bridgeClearance place them), where a face stands back from the
# drawn water.
bridge_forms=read('data/maps/road-bridge-forms.json')
for bridge in infra['roadBridges']:
    form=bridge_forms['bridges'].get(bridge['id'])
    if not form:continue
    at,length=route_frame(bridge['route']);half=bridge['width']/2;sk=form.get('skew',0);skews=sk if isinstance(sk,list) else [sk,sk]
    arch=form['form'] in ('stone-arch','brick-arch');d=bridge_forms['defaults']
    keep=lambda k:(d.get('abutmentEndClearance',0) if arch else form.get('abutmentLength',1.2))+abs(k)*half
    a0=max(form['abutments'][0],keep(skews[0]));a1=min(form['abutments'][1],length-keep(skews[1]));reach=half+d['clearZoneMargin'];strips=[]
    for v in np.arange(-reach,reach+1e-9,.25):
        f0=max(0,a0+skews[0]*v);f1=min(length,a1+skews[1]*v)
        if f1-f0>.05:strips.append(Polygon(at(np.array([f0,f1,f1,f0]),np.array([v-.125,v-.125,v+.125,v+.125]))).buffer(0))
    if strips:span_footprints[bridge['id']]=shapely.union_all([span_footprints.get(bridge['id'],Polygon()),*strips]).buffer(.01,join_style='mitre').buffer(-.01,join_style='mitre')
span_zone=shapely.union_all(list(span_footprints.values()));shapely.prepare(span_zone)
bridge_lines=[(LineString(b['route']),b['height']) for b in infra['roadBridges']]
def bridge_cone(q):
    out=np.full(len(q),-np.inf);pts=shapely.points(q)
    for line,h in bridge_lines:out=np.maximum(out,h-DECK_ROAD_OFFSET-BRIDGE_CONE*shapely.distance(pts,line))
    return out
def nearest_on_roads(q,reach):
    """Nearest point on a road surface or deck triangle within reach, and its distance (0 inside)."""
    pts=shapely.points(q);i,d=surface_tree.query_nearest(pts,max_distance=reach,return_distance=True,all_matches=False)
    near=np.full((len(q),2),np.nan);dist=np.full(len(q),np.inf)
    if len(i[0]):near[i[0]]=shapely.get_coordinates(shapely.shortest_line(road_polys[i[1]],pts[i[0]])).reshape(-1,2,2)[:,0];dist[i[0]]=d
    return near,dist
hsx=infra['sewerHighStreet'];hs_line=LineString(hsx['roadRoute'])
def high_street(q):
    t=np.clip((np.linalg.norm(q-np.array(hsx['centre']),axis=1)-12)/hsx['roadApproachLength'],0,1)
    lat=np.clip((shapely.distance(shapely.points(q),hs_line)-hsx['roadWidth']/2-2)/28,0,1)
    return .185+(hsx['surfaceHeight']-.185)*(1-t*t*(3-2*t))*(1-lat*lat*(3-2*lat))
road_profiles=[r['elevationProfile'] for r in infra['roads'] if r.get('elevationProfile') and r['elevationProfile'].get('geometryEpoch')==historic['epoch']]
def profile_height(q):
    out=np.full(len(q),np.nan);pts=shapely.points(q)
    for pf in road_profiles:
        line=LineString(pf['route']);ok=np.isnan(out)&(shapely.distance(pts,line)<=pf['widthMetres']/2+pf['shoulderMetres']+.01)
        out[ok]=np.interp(shapely.line_locate_point(line,pts[ok]),[c['distance'] for c in pf['controls']],[c['heightScene'] for c in pf['controls']])
    return out
cb=core['bounds']
def in_core(q):return (q[:,0]>=cb[0])&(q[:,0]<=cb[2])&(q[:,1]>=cb[1])&(q[:,1]<=cb[3])
def road_ground(q,lv):
    """docs/infrastructure.js ground() at q, given the drawn ground lv there."""
    h=np.where(field_weight(q)>0,lv,np.where(in_core(q),np.maximum(.12,lv),.12))
    hs=high_street(q);sel=hs>.1850001;h[sel]=np.maximum(h[sel],hs[sel]-DECK_ROAD_OFFSET)
    h=np.maximum(h,bridge_cone(q));pr=profile_height(q);ok=np.isfinite(pr);h[ok]=pr[ok]-DECK_ROAD_OFFSET
    return h
class Locator:
    """Barycentric weights of fixed points in a fixed triangle set (vertex indices)."""
    def __init__(self,xz,tri,q,zone=None):
        polys=shapely.polygons(xz[tri])
        if zone is not None:keep=np.flatnonzero(shapely.intersects(polys,zone));tri=tri[keep];polys=polys[keep]
        pi,ti=shapely.STRtree(polys).query(shapely.points(q),predicate='intersects')
        w,ok=barycentric(xz[tri[ti]],q[pi])
        self.pi=pi[ok];self.idx=tri[ti[ok]];self.w=w[ok];self.n=len(q)
    def top(self,y):
        out=np.full(self.n,-np.inf);np.maximum.at(out,self.pi,(self.w*y[self.idx]).sum(axis=1));return out
def barycentric(t,q):
    a,b,c=t[:,0],t[:,1],t[:,2];v0=b-a;v1=c-a;v2=q-a
    den=v0[:,0]*v1[:,1]-v1[:,0]*v0[:,1];ok=abs(den)>1e-12;den=np.where(ok,den,1)
    u=(v2[:,0]*v1[:,1]-v1[:,0]*v2[:,1])/den;v=(v0[:,0]*v2[:,1]-v2[:,0]*v0[:,1])/den
    w=np.column_stack([1-u-v,u,v]);ok&=(w>=-1e-6).all(axis=1)
    return np.clip(w,0,1)/np.clip(w,0,1).sum(axis=1,keepdims=True),ok
mesh_keys=['network','system','extension','groundMesh']
mesh_tri={k:(surfaces[k]['triangles'] if k in ('network','system') else np.arange(len(surfaces[k]['points'])).reshape(-1,3)) for k in mesh_keys}
def core_level(q):
    fx=np.clip((q[:,0]-cb[0])/core['step'],0,core['width']-1.001);fz=np.clip((q[:,1]-cb[1])/core['step'],0,core['height']-1.001)
    i=np.floor(fx).astype(int);j=np.floor(fz).astype(int);u=fx-i;v=fz-j;y=surfaces['core']['new'].reshape(core['height'],core['width'])
    return (y[j,i]*(1-u)+y[j,i+1]*u)*(1-v)+(y[j+1,i]*(1-u)+y[j+1,i+1]*u)*v
field_meta={'bounds':[e0-538900+step/2,183209-n1+step/2,e1-538900-step/2,183209-n0-step/2],'step':step,'width':shape[1],'height':shape[0]}
def vertex_grid(values,m,q):
    """docs/lib/grid.js sampleVertexGrid (clamped bilinear)."""
    fx=np.clip((q[:,0]-m['bounds'][0])/m['step'],0,m['width']-1);fz=np.clip((q[:,1]-m['bounds'][1])/m['step'],0,m['height']-1)
    i=np.minimum(np.floor(fx).astype(int),m['width']-2);j=np.minimum(np.floor(fz).astype(int),m['height']-2);u=fx-i;v=fz-j;g=values.reshape(m['height'],m['width'])
    return (g[j,i]*(1-u)+g[j,i+1]*u)*(1-v)+(g[j+1,i]*(1-u)+g[j+1,i+1]*u)*v
def field_weight(q):
    """main-landscape.js weight()."""
    fb=[e0-538900,183209-n1,e1-538900,183209-n0];w=vertex_grid(support,field_meta,q)
    w[(q[:,0]<fb[0])|(q[:,0]>fb[2])|(q[:,1]<fb[1])|(q[:,1]>fb[3])]=0
    return w
def field_level(q):
    """main-landscape.js level(): the 10 m level field blended by the marsh weight to -0.1 m."""
    return -.1+field_weight(q)*(vertex_grid(values,field_meta,q)+.1)
def drawn_level(q,locators):
    """terrainDetails().level: the core tile inside its bounds, else the highest drawn mesh."""
    out=np.full(len(q),-np.inf)
    for k,loc in locators.items():out=np.maximum(out,loc.top(surfaces[k]['new']))
    # No drawn mesh (a hole or the edge of the regional mesh): the page falls
    # back to the main landscape's 10 m level field (main-landscape.js level()).
    none=np.flatnonzero(~np.isfinite(out))
    if len(none):out[none]=field_level(q[none])
    inside=in_core(q);out[inside]=core_level(q[inside]);return out
road_pass={'embankment':{},'cutting':{},'spanClearance':{},'roadClamp':{}}
def mesh_points(key):return surfaces[key]['points']
def near_bridges(q,reach):
    pts=shapely.points(q);return np.min([shapely.distance(pts,line) for line,_ in bridge_lines],axis=0)<=reach
# 1. Approach embankments.
def mesh_boundary(key):
    """Outer-edge vertices of a mesh near the bridges, as (tree of points, vertex indices); None for the core grid.
    The regional mesh's outer edge is the edge of its area (its pieces meet along cut edges inside it)."""
    if key=='core':return None
    q=mesh_points(key);t=mesh_tri[key]
    if key=='groundMesh':
        b=np.flatnonzero(near_bridges(q,EMB_REACH_M+EDGE_REACH_M));b=b[shapely.distance(area.boundary,shapely.points(q[b]))<1e-3]
        return (shapely.STRtree(shapely.points(q[b])),b) if len(b) else None
    if key=='extension':
        _,inv=np.unique(np.round(q,3),axis=0,return_inverse=True);t=inv.reshape(-1,3);rep=np.zeros(inv.max()+1,int);rep[inv]=np.arange(len(q))
    else:rep=None
    e=np.sort(np.concatenate([t[:,[0,1]],t[:,[1,2]],t[:,[2,0]]]),axis=1);u,c=np.unique(e,axis=0,return_counts=True);b=np.unique(u[c==1])
    if rep is not None:b=rep[b]
    b=b[near_bridges(q[b],EMB_REACH_M+EDGE_REACH_M)]
    return (shapely.STRtree(shapely.points(q[b])),b) if len(b) else None
EMB_REACH_M=max((h-DECK_ROAD_OFFSET+.5)/BRIDGE_CONE for _,h in bridge_lines)+EDGE_REACH_M
for key in ['core',*mesh_keys]:
    q=mesh_points(key);new=surfaces[key]['new'];free=~protected(key)
    idx=np.flatnonzero(free&near_bridges(q,EMB_REACH_M))
    near,dist=nearest_on_roads(q[idx],EDGE_REACH_M);ok=np.isfinite(dist);idx=idx[ok];near=near[ok];dist=dist[ok]
    level=bridge_cone(near)-dist/EDGE_BATTER
    # Also no steeper than 1:1.5 above low water from any drawn low water
    # (river-system water polygons included) or from a span footprint, never
    # over either.
    level=np.minimum(level,WATER_EDGE+np.minimum(shapely.distance(low_water,shapely.points(q[idx])),shapely.distance(span_zone,shapely.points(q[idx])))/EDGE_BATTER)
    # And no steeper than 1:1.5 above the outer edge of the mesh itself (beyond
    # it lies other ground this pass does not raise), so no fill stands as a
    # cliff at a mesh boundary.
    edge=mesh_boundary(key)
    if edge is not None and len(idx):
        k,dk=edge[0].query_nearest(shapely.points(q[idx]),return_distance=True,all_matches=False)
        level[k[0]]=np.minimum(level[k[0]],new[edge[1][k[1]]]+dk/EDGE_BATTER)
    up=level>new[idx]+1e-6;idx=idx[up]
    if not len(idx):continue
    raised=np.maximum(new[idx],edge_caps(q[idx],level[up],new[idx]));gain=raised-new[idx];new[idx]=raised
    road_pass['embankment'][key]={'raisedVertices':int((gain>1e-6).sum()),'maxRaiseMetres':round(float(gain.max()),3)}
# 2. Approach cuttings, on the bridge's own road only (its corridor and
# footways, within CUT_REACH_M of the deck route); a crossing street keeps its
# own level and the cut meets it at its edge.
ROAD_SHOULDER_M=1.2;road_buffers={}
for r in infra['roads']:
    if len(r['route'])>1:road_buffers.setdefault(r['name'],[]).append(LineString(r['route']).buffer(r['width']/2+ROAD_SHOULDER_M))
cut_zones=[]
for bridge in infra['roadBridges']:
    line=LineString(bridge['route']);reach=line.buffer(CUT_REACH_M+EDGE_REACH_M)
    others=shapely.union_all([g for n,gs in road_buffers.items() if n!=bridge['name'] for g in gs if g.intersects(reach)])
    zone=shapely.union_all(road_buffers.get(bridge['name'],[])).intersection(line.buffer(CUT_REACH_M)).difference(others)
    if not zone.is_empty:shapely.prepare(others);cut_zones.append((zone,line,bridge['height'],others))
for key in ['core',*mesh_keys]:
    q=mesh_points(key);new=surfaces[key]['new'];free=~protected(key);lowered=np.zeros(len(q));pts_all=shapely.points(q)
    for zone,line,h,others in cut_zones:
        idx=np.flatnonzero(free&shapely.dwithin(zone,pts_all,EDGE_REACH_M))
        if not len(idx):continue
        near=shapely.get_coordinates(shapely.shortest_line(zone,pts_all[idx])).reshape(-1,2,2)[:,0];dist=np.linalg.norm(q[idx]-near,axis=1)
        level=h-DECK_ROAD_OFFSET+DECK_GRADE*np.maximum(0,shapely.distance(shapely.points(near),line)-DECK_LANDING_M)+dist/EDGE_BATTER
        down=level<new[idx]-1e-6
        down&=(dist<=1e-6)|~(shapely.contains_xy(building_union,q[idx,0],q[idx,1])|shapely.contains_xy(others,q[idx,0],q[idx,1]))
        idx=idx[down];lowered[idx]=np.maximum(lowered[idx],new[idx]-level[down]);new[idx]=level[down]
    if lowered.any():road_pass['cutting'][key]={'loweredVertices':int((lowered>0).sum()),'maxLoweringMetres':round(float(lowered.max()),3)}
# 3. Span clearance.
for key in ['core',*mesh_keys]:
    q=mesh_points(key);new=surfaces[key]['new']
    idx=np.flatnonzero(~protected(key)&shapely.contains_xy(span_zone,q[:,0],q[:,1]));idx=idx[new[idx]>WATER_EDGE]
    if not len(idx):continue
    road_pass['spanClearance'][key]={'loweredVertices':int(len(idx)),'maxLoweringMetres':round(float((new[idx]-WATER_EDGE).max()),3)}
    new[idx]=WATER_EDGE
# 4. No ground above a road. Margins: one mesh edge (core cell diagonal, the
# 1 m network grid diagonal, the 2 m extension grid diagonal, the longest
# incident system edge up to 3 m; the regional mesh is cut along the roads).
rv,ridx=np.unique(np.round(road_tri.reshape(-1,2),4),axis=0,return_inverse=True);ridx=ridx.reshape(-1,3)
deck_idx=len(rv)+np.arange(len(deck_tri)*3).reshape(-1,3);tri_vertices=np.concatenate([ridx,deck_idx]);tri_offset=np.r_[road_offset,np.full(len(deck_tri),DECK_ROAD_OFFSET)]
road_locators={k:Locator(mesh_points(k),mesh_tri[k],rv,road_zone.buffer(1)) for k in mesh_keys}
def edge_margin(key):
    if key=='core':return np.full(len(mesh_points(key)),core['step']*np.sqrt(2)+.01)
    if key=='groundMesh':return np.full(len(mesh_points(key)),.02)
    t=mesh_tri[key];q=mesh_points(key);m=np.zeros(len(q))
    for a_,b_ in ((0,1),(1,2),(2,0)):
        e=np.linalg.norm(q[t[:,a_]]-q[t[:,b_]],axis=1);np.maximum.at(m,t[:,a_],e);np.maximum.at(m,t[:,b_],e)
    return np.minimum(m,3.0)+.01
clamp={}
for key in ['core',*mesh_keys]:
    q=mesh_points(key);margin=edge_margin(key)
    idx=np.flatnonzero(~protected(key)&shapely.dwithin(road_zone,shapely.points(q),margin))
    # Every road or deck triangle within the margin caps the vertex, at the
    # nearest point of the triangle (overlapping street and footway triangles
    # each follow their own vertices). This includes ground under the edge of
    # a building that stands over a footway (a registration conflict between
    # frontage and street); the building keeps its own seat.
    pts=shapely.points(q[idx]);pi,ti=surface_tree.query(pts,predicate='dwithin',distance=margin[idx])
    c=shapely.get_coordinates(shapely.shortest_line(road_polys[ti],pts[pi])).reshape(-1,2,2)[:,0]
    contained=np.linalg.norm(c-q[idx][pi],axis=1)<=1e-9
    w,ok=barycentric(all_road_tri[ti],c);pi=pi[ok];ti=ti[ok];w=w[ok];contained=contained[ok]
    clamp[key]=(idx,pi,tri_vertices[ti],w,tri_offset[ti],contained)
# The drawn road takes its height from the ground at its own vertices, so
# lowering the mesh vertices that ground is interpolated from (the triangles
# or core cell containing each road vertex) lowers the road, and the next pass
# the ground beside it, and so on along the street (a steep road triangle
# over a bank would sink a whole lane). Those support vertices are therefore
# held under the road for a few passes only; every other vertex then in one
# pass, which leaves the road where it stands.
road_support={k:np.zeros(len(mesh_points(k)),bool) for k in ['core',*mesh_keys]}
for k,loc in road_locators.items():road_support[k][np.unique(loc.idx)]=True
fx=np.clip((rv[:,0]-cb[0])/core['step'],0,core['width']-1.001);fz=np.clip((rv[:,1]-cb[1])/core['step'],0,core['height']-1.001)
ci=np.floor(fx).astype(int)[in_core(rv)];cj=np.floor(fz).astype(int)[in_core(rv)]
for a_,b_ in ((0,0),(1,0),(0,1),(1,1)):road_support['core'][(cj+b_)*core['width']+ci+a_]=True
before={k:surfaces[k]['new'].copy() for k in ['core',*mesh_keys]}
G0=np.r_[road_ground(rv,drawn_level(rv,road_locators)),np.repeat(deck_ground,3)];G=G0
for _ in range(ROAD_SUPPORT_PASSES):
    for key,(idx,pi,tv,w,off,contained) in clamp.items():
        cap=np.full(len(idx),np.inf);np.minimum.at(cap,pi,(w*G[tv]).sum(axis=1)+off-np.clip(off-ROAD_CAP_KEEP_M,0,ROAD_CAP_BELOW_M))
        new=surfaces[key]['new'];low=np.flatnonzero(new[idx]>cap+1e-6);new[idx[low]]=cap[low]
    G=np.r_[road_ground(rv,drawn_level(rv,road_locators)),np.repeat(deck_ground,3)]
road_pass['roadSupport']={'passes':ROAD_SUPPORT_PASSES,'roadVertexChangeMetres':{'max':round(float(np.abs(G-G0).max()),3),'p99':round(float(np.percentile(np.abs(G-G0),99)),3)}}
for key,(idx,pi,tv,w,off,contained) in clamp.items():
    cap=np.full(len(idx),np.inf);np.minimum.at(cap,pi,(w*G[tv]).sum(axis=1)+off-np.clip(off-ROAD_CAP_KEEP_M,0,ROAD_CAP_BELOW_M))
    new=surfaces[key]['new'];low=np.flatnonzero((new[idx]>cap+1e-6)&~road_support[key][idx]);new[idx[low]]=cap[low]
G_after=np.r_[road_ground(rv,drawn_level(rv,road_locators)),np.repeat(deck_ground,3)]
road_pass['roadClamp']['roadVertexGroundChangeMetres']=round(float(np.abs(G_after-G).max()),6)
# Beyond one mesh edge from a road, ground standing above it is cut back at
# 1:1.5 from the road (a cutting), so the clamp leaves no cliff at its margin.
# These vertices touch no road triangle, so the road does not move.
road_pass['cuttingSides']={}
for key in ['core',*mesh_keys]:
    q=mesh_points(key);new=surfaces[key]['new'];margin=edge_margin(key)
    idx=np.flatnonzero(~protected(key)&shapely.dwithin(road_zone,shapely.points(q),EDGE_REACH_M))
    idx=idx[~shapely.contains_xy(building_union,q[idx,0],q[idx,1])&~road_support[key][idx]]
    pts=shapely.points(q[idx]);j,d=surface_tree.query_nearest(pts,return_distance=True,all_matches=False)
    c=shapely.get_coordinates(shapely.shortest_line(road_polys[j[1]],pts[j[0]])).reshape(-1,2,2)[:,0]
    w,ok=barycentric(all_road_tri[j[1]],c);off=tri_offset[j[1]]
    cap=(w*G[tri_vertices[j[1]]]).sum(axis=1)+off-np.clip(off-ROAD_CAP_KEEP_M,0,ROAD_CAP_BELOW_M)+np.maximum(0,d-margin[idx[j[0]]])/EDGE_BATTER
    k=idx[j[0]];low=ok&(new[k]>cap+1e-6)
    if low.any():road_pass['cuttingSides'][key]={'loweredVertices':int(low.sum()),'maxLoweringMetres':round(float((new[k][low]-cap[low]).max()),3)};new[k[low]]=cap[low]
for key in clamp:
    loss=before[key]-surfaces[key]['new']
    road_pass['roadClamp'][key]={'candidateVertices':int(len(clamp[key][0])),'loweredVertices':int((loss>1e-6).sum()),'maxLoweringMetres':round(float(loss.max()),3)}
print('ROAD PASS:',json.dumps(road_pass),flush=True)
for key in ['core','network','system','extension']:write_heights(key)
heights=surfaces['groundMesh']['new'];mesh=np.column_stack([points[:,0],heights,points[:,1]]).astype('<f4')
mesh.tofile(OUT/'main-landscape-1900.background.f32');files['groundMesh']='main-landscape-1900.background.f32'
# Retaining-edge crests (wall_levels) are computed above with the land-side fill.
# Refitting railway toes leaves every formation station unchanged.
railways=[]
for adjustment in system.get('railwayGroundAdjustments',[]):
    rail=next(r for r in infra['railways'] if r.get('id')==adjustment['railwayId'])
    rail['embankment'][adjustment['triangle']][adjustment['vertex']][1]=adjustment['afterY']
for rail in infra['railways']:
    vertices=np.array(rail['embankment']);p=vertices[:,:,[0,2]].reshape(-1,2);line=LineString(rail['route']);pts=shapely.points(p)
    d=shapely.distance(pts,line);s=shapely.line_locate_point(line,pts);stations=np.array(rail.get('stations',[]))
    # Plain railways in the core box carry an OS level profile (data/maps/railway-levels.json);
    # their embankment crest is 0.05 m above it.
    profile=rail.get('levelProfile')
    crest=np.interp(s,stations[:,5],stations[:,2]) if len(stations) else np.interp(s,profile['chainage'],profile['formation'])+.05 if profile else np.full(len(p),rail['formationHeight']+.05)
    half=rail.get('baseHalfWidth',15);crest_half=rail.get('crestHalfWidth',max(3,rail.get('tracks',1)*2));t=np.clip((half-d)/max(1,half-crest_half),0,1)
    g=base(p);old=vertices[:,:,1].ravel();target=g+t*(crest-g);w=weight(p)
    if profile and not len(stations):
        # Register railways: side slopes at the OS-measured 1 in sideSlope from the crest edge down to
        # the ground, so the toe follows the bank height; beyond the toe the earth lies 0.05 m under
        # the ground. Where the ground stands above the crest (a cutting) the old blend is kept.
        ch,side=profile['crestHalfWidth'],profile['sideSlope']
        slope=crest-np.maximum(0,d-ch)/side
        target=np.where(g<=crest,np.where(slope>=g,slope,g-.05),crest+(g-crest)*np.clip((d-ch)/max(1,half-ch),0,1))
    # Exact crest vertices and bridge geometry retain their original elevations.
    w[abs(old-crest)<.15]=0
    levels=old+w*(target-old)
    railways.append({'name':rail['name'],'heights':levels.reshape(-1,3).tolist()})

# Railway earthworks where the traced embankment meets water, buildings and
# its own ends. Routes, formation heights and every existing embankment height
# stay as above; this only removes embankment triangles (or parts of them,
# re-triangulated in their own planes) and adds earth and brick faces. The
# bridge decks, girders and piers are drawn by docs/railway-bridges.js from
# data/maps/railway-bridge-forms.json, which records the evidence.
# - Openings: no embankment stands over drawn water. Where the traced
#   embankment ran on over it (the North London branch over the Hackney Cut,
#   RAIL_OPENINGS) the fill stops RAIL_WATER_CLEAR m short of the drawn water
#   edge and a brick abutment face with in-line wings follows that edge down
#   below the bed. Where the traced embankment already stops at a mapped
#   crossing (the 2 m water and street clearance in build_infrastructure.py,
#   including the LT&SR's east bank of Bow Creek), the cut faces of the plain
#   railways take the same brick face; the new LT&SR west approach is clipped
#   to the drawn west bank the same way.
# - Buildings: where a raised embankment would reach within RAIL_GAP m of a
#   mapped building footprint, the fill stops RAIL_GAP m from the footprint and
#   a brick retaining wall holds it, so no wall of the building is buried. Not
#   done where that would cut the formation (recorded as a conflict).
# - Line ends: a raised end with nothing beyond is closed by an earth end
#   falling at the railway's own side slope to the ground (a hipped end), not
#   left as a cut. At Bow Creek the LT&SR route ends in the river, so a short
#   level approach behind the west abutment ends the same way.
RAIL_GAP=1.5;RAIL_WATER_CLEAR=.4;RAIL_WALL_MIN=.05;RAIL_FOOTING=.4;RAIL_BED=-1.2;RAIL_END_STEP=1.;RAIL_TOE_SINK=.5
RAIL_OPENINGS={'nl-hackney-cut':('North London / Victoria Park branch connection',50,95)}
# The LT&SR west approach: stations along the route's first segment from its
# first point (in Bow Creek); full section from RAIL_APPROACH[1] back to [2],
# then the hipped end. Bow Creek's drawn west edge is at station -7.7 on the
# centreline and -12.8/-2.0 at the crest edges (skew about 1.2 m per metre).
RAIL_APPROACH=('London, Tilbury and Southend Railway',14.,-16.8)
# Labels for footprint_geoms, in the order they were collected above.
footprint_labels=[f"factory {b.get('id')}" for b in factory['buildings'] for p in b.get('renderPolygons') or []]+[f"holder {h.get('id',h.get('siteId'))}" for h in factory['holders']]
footprint_labels+=[f"{k} {b.get('id')}" for k in ('mappedFactories','houses','terraces') for b in plan['neighbourhood'][k] if b.get('footprint')]
footprint_labels+=[f"frontage {b.get('id')}" for b in json.loads((ROOT/'docs/data/high-street-frontages.json').read_text())['buildings'] if b.get('footprint')]
footprint_labels+=[f"housing {b.get('id')}" for b in json.loads((ROOT/'docs/data/housing-detail.json').read_text())['rows'] if b.get('footprint')]
footprint_labels+=['station']+[f"station {b.get('id')}" for b in station['supportingBuildings'] if b.get('footprint')]+['corn mill']
assert len(footprint_labels)==len(footprint_geoms)
road_corridors=shapely.union_all([LineString(r['route']).buffer(r['width']/2) for r in infra['roads'] if len(r['route'])>1]);shapely.prepare(road_corridors)
rail_works={}
def plane_heights(tri,pts):
    """Heights at plan points pts on the plane of the 3D triangle tri."""
    (x0,y0,z0),(x1,y1,z1),(x2,y2,z2)=tri;det=(x1-x0)*(z2-z0)-(x2-x0)*(z1-z0)
    if abs(det)<1e-12:return np.full(len(pts),max(y0,y1,y2))
    a=((pts[:,0]-x0)*(z2-z0)-(x2-x0)*(pts[:,1]-z0))/det;b=((x1-x0)*(pts[:,1]-z0)-(pts[:,0]-x0)*(z1-z0))/det
    return y0+a*(y1-y0)+b*(y2-y0)
def clip_away(tris,cut):
    """Remove the parts of 3D triangles (N,3,3) inside the plan polygon cut.
    Returns removed indices, the re-triangulated remainders (heights on each
    original triangle's plane) and the remainder edges lying on the cut edge."""
    removed=[];added=[];faces=[]
    if cut.is_empty:return removed,added,faces
    # Drop sub-decimetre wiggles of buffered water edges, which leave sliver remainders.
    cut=shapely.set_precision(cut.simplify(.05),1e-3)
    polys=shapely.polygons(np.concatenate([tris[:,:,[0,2]],tris[:,:1,[0,2]]],axis=1));boundary=cut.boundary;shapely.prepare(cut);shapely.prepare(boundary)
    for i in shapely.STRtree(polys).query(cut,predicate='intersects'):
        poly=polys[i]
        if poly.area<1e-6:
            if cut.contains(poly.centroid):removed.append(int(i))
            continue
        piece=poly.difference(cut)
        if piece.area>poly.area-1e-6:continue
        removed.append(int(i))
        # Snap to the 1 mm grid the works are stored on, so neighbouring remainders share vertices.
        piece=shapely.set_precision(piece,1e-3)
        if piece.area<1e-4:continue
        for t in shapely.get_parts(shapely.constrained_delaunay_triangles(piece)):
            if t.area<1e-4:continue
            xz=shapely.get_coordinates(t)[:3];y=plane_heights(tris[i],xz)
            added.append(np.column_stack([xz[:,0],y,xz[:,1]]))
    # Faces: edges of the kept and re-triangulated earth near the cut that no longer have a
    # neighbour and lie on or inside the cut (vertices matched to 0.1 mm).
    near=set(shapely.STRtree(polys).query(cut.buffer(4.),predicate='intersects').tolist())-set(removed)
    local=[tris[i] for i in sorted(near) if polys[i].area>=1e-6]+added
    count={};first={};fresh=set()
    for n,t in enumerate(local):
        for j in range(3):
            a,b=t[j],t[(j+1)%3];k=tuple(sorted((tuple(np.round(a[[0,2]],3)),tuple(np.round(b[[0,2]],3)))))
            count[k]=count.get(k,0)+1;first[k]=(a,b)
            if n>=len(local)-len(added):fresh.add(k)
    # On or inside the cut, or within 3.5 m of it where the remainder meets a gap
    # the traced embankment already had (beside the North London branch's northern water).
    for k,c in count.items():
        a,b=first[k]
        if c!=1 or np.hypot(*(a[[0,2]]-b[[0,2]]))<=1e-4:continue
        d=shapely.distance(cut,shapely.points((a[[0,2]]+b[[0,2]])/2))
        if d<3.5:faces.append(np.array([a,b]))
    # An edge with earth on both sides (a T-junction or a snapping mismatch) is not a face.
    if faces:
        cover=shapely.union_all([Polygon(t[:,[0,2]]) for t in local if Polygon(t[:,[0,2]]).area>1e-6]).buffer(1e-4);shapely.prepare(cover)
        f=np.array(faces);mid=f[:,:,[0,2]].mean(1);d=f[:,1,[0,2]]-f[:,0,[0,2]];nrm=np.column_stack([-d[:,1],d[:,0]])/np.maximum(1e-9,np.hypot(d[:,0],d[:,1]))[:,None]
        both=shapely.contains_xy(cover,*(mid+.05*nrm).T)&shapely.contains_xy(cover,*(mid-.05*nrm).T)
        faces=[x for x,b in zip(faces,both) if not b]
    return removed,added,faces
def rail_ground(points):
    """The ground the plain embankment toes meet (base(); 0.05 m outside the marsh weight, as in the traced embankment)."""
    w=weight(points);return w*base(points)+(1-w)*.05
def wall_quads(faces,kind):
    """Brick faces from embankment edges down past the ground: to RAIL_BED beside water, else RAIL_FOOTING below ground."""
    quads=[]
    if not faces:return quads
    f=np.array(faces);ends=f[:,:,[0,2]].reshape(-1,2);g=rail_ground(ends).reshape(-1,2);wet=(shapely.distance(water,shapely.points(ends))<1.5).reshape(-1,2)
    bottom=np.where(wet,np.minimum(g,RAIL_BED),g-RAIL_FOOTING)
    for (a,b),(ga,gb),(ba,bb) in zip(f,g,bottom):
        if max(a[1]-ga,b[1]-gb)<RAIL_WALL_MIN:continue
        quads.append([a.tolist(),b.tolist(),[b[0],min(bb,b[1]),b[2]],[a[0],min(ba,a[1]),a[2]]])
    return quads
def hipped_end(profile,u,slope,ground_fn):
    """Earth end beyond a raised end profile (points (x,y,z) across the line, outward
    direction u): every profile point falls at the side slope as it moves out, to
    a toe ring sunk RAIL_TOE_SINK m into the ground (the drawn ground can lie below base())."""
    profile=np.asarray(profile,float);xz=profile[:,[0,2]];h0=np.maximum(0,profile[:,1]-ground_fn(xz));rows=[profile];sunk=[h0<=0]
    for k in range(1,int(np.ceil(h0.max()/slope/RAIL_END_STEP))+2):
        f=k*RAIL_END_STEP;q=xz+u*f;g=ground_fn(q);h=np.maximum(0,h0-slope*f)
        rows.append(np.column_stack([q[:,0],np.where(h>0,g+h,g-RAIL_TOE_SINK),q[:,1]]));sunk.append(h<=0)
    tris=[]
    for r0,r1,s0,s1 in zip(rows[:-1],rows[1:],sunk[:-1],sunk[1:]):
        for j in range(len(profile)-1):
            for t,ss in (((r0[j],r0[j+1],r1[j+1]),(s0[j],s0[j+1],s1[j+1])),((r0[j],r1[j+1],r1[j]),(s0[j],s1[j+1],s1[j]))):
                if not all(ss):tris.append(np.array(t))
    return tris
def boundary_edges(tris):
    """Edges used by one triangle (vertices matched in plan to 1 mm), less any with earth on both sides."""
    count={};first={}
    for t in tris:
        t=np.asarray(t)
        for j in range(3):
            a,b=t[j],t[(j+1)%3];k=tuple(sorted((tuple(np.round(a[[0,2]],3)),tuple(np.round(b[[0,2]],3)))))
            count[k]=count.get(k,0)+1;first[k]=(a,b)
    edges=[np.array(first[k]) for k,c in count.items() if c==1 and k[0]!=k[1]]
    if not edges:return edges
    cover=shapely.union_all([p for p in shapely.polygons([np.asarray(t)[:,[0,2]] for t in tris]) if p.area>1e-6]).buffer(1e-4);shapely.prepare(cover)
    f=np.array(edges);mid=f[:,:,[0,2]].mean(1);d=f[:,1,[0,2]]-f[:,0,[0,2]];nrm=np.column_stack([-d[:,1],d[:,0]])/np.maximum(1e-9,np.hypot(d[:,0],d[:,1]))[:,None]
    both=shapely.contains_xy(cover,*(mid+.05*nrm).T)&shapely.contains_xy(cover,*(mid-.05*nrm).T)
    return [e for e,b in zip(edges,both) if not b]
lines_by_name={r['name']:LineString(r['route']) for r in infra['railways']}
for rail,record in zip(infra['railways'],railways):
    name=rail['name'];line=lines_by_name[name];half=rail.get('baseHalfWidth',15);crest_half=rail.get('crestHalfWidth',max(3,rail.get('tracks',1)*2))
    tris=np.array(rail['embankment'],float);tris[:,:,1]=np.array(record['heights']);detailed=bool(rail.get('detailedMainline') or rail.get('detailedRailway'))
    others=shapely.union_all([LineString(r['route']).buffer(r.get('baseHalfWidth',15)) for r in infra['railways'] if r['name']!=name])
    items=[];removed=set();added=[];walls=[]
    def apply(cut,kind,ident,evidence,extra=None,source=None):
        global_tris=tris if source is None else source
        rem,add,faces=clip_away(global_tris,cut);q=wall_quads(faces,kind)
        items.append({'kind':kind,'id':ident,'removedTriangles':len(rem),'addedTriangles':len(add),'wallFaces':len(q),'wallLengthMetres':round(float(sum(np.hypot(w[1][0]-w[0][0],w[1][2]-w[0][2]) for w in q)),1),**(extra or {}),'evidence':evidence})
        return rem,add,q
    # Recorded bridge openings.
    for ident,(railway,c0,c1) in RAIL_OPENINGS.items():
        if railway!=name:continue
        band=shapely.ops.substring(line,c0,c1).buffer(half+3,cap_style='flat')
        rem,add,q=apply(water.buffer(RAIL_WATER_CLEAR).intersection(band),'opening',ident,'Mapped: the drawn water (river-system, ground-plan and ditch polygons) the line crosses. Interpreted: the fill stopping 0.4 m short of it behind a brick abutment face with in-line wings; no surveyed abutment.')
        removed|=set(rem);added+=add;walls+=q
    # Buildings beside the embankment.
    vertices=tris.reshape(-1,3);raised=vertices[:,1]-rail_ground(vertices[:,[0,2]])>RAIL_WALL_MIN
    vtree=shapely.STRtree(shapely.points(vertices[:,[0,2]]))
    crest_band=line.buffer(crest_half+.5)
    cuts=[];held=[];conflicts=[]
    # The detailed railways already stop their fill at building edges behind
    # their own retaining walls (great-eastern.js); only a footprint that the
    # fill actually enters is held off there.
    for k in footprint_tree.query(line.buffer(half+RAIL_GAP+1)):
        near=vtree.query(footprint_geoms[k] if detailed else footprint_geoms[k].buffer(RAIL_GAP),predicate='intersects')
        if not len(near) or not raised[near].any():continue
        cut=footprint_geoms[k].buffer(RAIL_GAP,join_style='mitre')
        label={'footprint':footprint_labels[k],'centre':np.round(list(footprint_geoms[k].centroid.coords)[0],1).tolist(),'distanceFromRouteMetres':round(footprint_geoms[k].distance(line),2)}
        if cut.intersects(crest_band):conflicts.append({**label,'reason':'footprint within '+str(RAIL_GAP)+' m of the formation; no wall can hold the fill off it'});continue
        cuts.append(cut);held.append(label)
    if cuts:
        rem,add,q=apply(shapely.union_all(cuts),'hold-off','buildings','Mapped: the building footprints (OS-traced, as seated in the scene). Interpreted: a brick retaining wall '+str(RAIL_GAP)+' m off each footprint where the traced embankment slope would otherwise bury its wall; no surveyed wall.',{'buildings':held})
        removed|=set(rem);added+=add;walls+=q
    if conflicts:items.append({'kind':'conflict','id':'buildings-in-formation','conflicts':conflicts,'evidence':'Recorded, not changed: a mapped footprint lies inside the traced formation (a registration conflict between the building and railway traces).'})
    # Raised line ends with nothing beyond them.
    route=np.array(rail['route'],float)
    for which,p0,p1 in (('start',route[0],route[1]),('end',route[-1],route[-2])):
        if others.contains(shapely.Point(p0)) or (name==RAIL_APPROACH[0] and which=='start'):continue
        u=(p0-p1)/np.linalg.norm(p0-p1);n=np.array([-u[1],u[0]])
        f=(vertices[:,[0,2]]-p0)@u;o=(vertices[:,[0,2]]-p0)@n;at=np.abs(f)<.05
        # A rounded or sloped end already reaches beyond the end line.
        if not at.any() or ((f>1)&(np.abs(o)<half)).any():continue
        prof=np.unique(np.round(vertices[at],4),axis=0);prof=prof[np.argsort((prof[:,[0,2]]-p0)@n)]
        keep=np.r_[True,np.diff((prof[:,[0,2]]-p0)@n)>.05];prof=prof[keep]
        rise=prof[:,1]-rail_ground(prof[:,[0,2]])
        if rise.max()<.5:continue
        slope=rise.max()/max(1,half-crest_half);end=hipped_end(prof,u,slope,rail_ground)
        # Zero-area slivers standing in the old end plane would show as a seam line on the new end.
        cf=(tris[:,:,[0,2]].mean(1)-p0)@u;pa=shapely.area(shapely.polygons(np.concatenate([tris[:,:,[0,2]],tris[:,:1,[0,2]]],axis=1)))
        removed|=set(np.flatnonzero((np.abs(cf)<.1)&(pa<1e-6)).tolist())
        end=np.array(end);rem,add,q=clip_away(end,water.buffer(RAIL_WATER_CLEAR).union(shapely.union_all([footprint_geoms[k].buffer(RAIL_GAP,join_style='mitre') for k in footprint_tree.query(shapely.Point(p0).buffer(half*2))]) if len(footprint_tree.query(shapely.Point(p0).buffer(half*2))) else Polygon()))
        kept=[t for i,t in enumerate(end) if i not in set(rem)]+add;q=wall_quads(q,'end')
        items.append({'kind':'end-fill','id':f'{which}','point':np.round(p0,2).tolist(),'heightMetres':round(float(rise.max()),2),'slope':f'1:{round(1/slope,2)}','addedTriangles':len(kept),'wallFaces':len(q),'evidence':'Interpreted: the traced line ends here inside the model; the embankment is closed by an earth end at its own side slope. The OS five-foot plan shows the line continuing beyond (see data/maps/railway-bridge-forms.json lineEnds).'})
        added+=kept;walls+=q
    # The LT&SR approach behind the Bow Creek west abutment.
    if name==RAIL_APPROACH[0]:
        a0=route[0];ua=(route[1]-a0)/np.linalg.norm(route[1]-a0);na=np.array([-ua[1],ua[0]]);crest=(rail['levelProfile']['formation'][0] if rail.get('levelProfile') else rail['formationHeight'])+.05
        offsets=np.array(sorted({*np.arange(-half,half+.01,2.),-crest_half,crest_half,*np.arange(-half-2,-half+.01,2.),*np.arange(half,half+2.01,2.)}))
        def section(st):
            xz=a0+ua*st+np.outer(offsets,na);g=rail_ground(xz);t=np.clip((half-np.abs(offsets))/max(1,half-crest_half),0,1)
            return np.column_stack([xz[:,0],np.where(t>0,g+t*(crest-g),g-RAIL_TOE_SINK),xz[:,1]])
        rows=[section(st) for st in np.arange(RAIL_APPROACH[1],RAIL_APPROACH[2]-1e-6,-RAIL_END_STEP)]
        if rows and abs(((rows[-1][0,[0,2]]-a0)@ua)-RAIL_APPROACH[2])>1e-3:rows.append(section(RAIL_APPROACH[2]))
        body=[]
        for r0,r1 in zip(rows[:-1],rows[1:]):
            for j in range(len(offsets)-1):body+=[np.array([r0[j],r0[j+1],r1[j+1]]),np.array([r0[j],r1[j+1],r1[j]])]
        body+=hipped_end(rows[-1],-ua,(crest-float(np.median(rail_ground(rows[-1][:,[0,2]]))))/max(1,half-crest_half),rail_ground)
        body=np.array(body)
        cut=water.buffer(RAIL_WATER_CLEAR).union(shapely.union_all([footprint_geoms[k].buffer(RAIL_GAP,join_style='mitre') for k in footprint_tree.query(LineString([a0+ua*RAIL_APPROACH[1],a0+ua*(RAIL_APPROACH[2]-15)]).buffer(half+3))] or [Polygon()]))
        rem,add,faces=clip_away(body,cut);kept=[t for i,t in enumerate(body) if i not in set(rem)]+add;q=wall_quads(faces,'abutment')
        # The traced embankment's rounded end on the west bank lies under the approach: not drawn.
        removed|=set(np.flatnonzero(((tris[:,:,[0,2]].mean(1)-a0)@ua)<RAIL_APPROACH[1]).tolist())
        items.append({'kind':'approach','id':'ltsr-bow-creek-west','stations':[RAIL_APPROACH[1],RAIL_APPROACH[2]],'addedTriangles':len(kept),'wallFaces':len(q),'wallLengthMetres':round(float(sum(np.hypot(w[1][0]-w[0][0],w[1][2]-w[0][2]) for w in q)),1),'evidence':'Mapped: the LT&SR crossing Bow Creek and continuing west on the OS five-foot plan, and the drawn west water edge. Interpreted: the traced route ends in the river, so the fill is carried at formation level to station '+str(RAIL_APPROACH[2])+' behind a brick west abutment on the drawn bank and closed there by an earth end at the side slope; the line beyond is not modelled.'})
        added+=kept;walls+=q
    # Cut faces of the plain railways at mapped openings (water, streets).
    if not detailed:
        final=[t for i,t in enumerate(tris) if i not in removed]+[np.asarray(t) for t in added]
        faces=[];crossing_ends=shapely.multipoints([c[k] for c in rail['crossings'] for k in (0,-1)]) if rail['crossings'] else None
        for e in boundary_edges(final):
            m=shapely.points(e[:,[0,2]].mean(0))
            # Only the cut ends at a crossing; a side cut along a ditch or street is left as traced.
            if crossing_ends is None or shapely.distance(crossing_ends,m)>half+3:continue
            if shapely.distance(water,m)<3.2 or shapely.distance(road_corridors,m)<3.2:
                if not others.contains(m):faces.append(e)
        wall_ids={tuple(np.round(np.array(w[:2])[:,[0,2]].ravel(),3)) for w in walls}
        q=[w for w in wall_quads(faces,'opening-cut') if tuple(np.round(np.array(w[:2])[:,[0,2]].ravel(),3)) not in wall_ids and tuple(np.round(np.array(w[1::-1])[:,[0,2]].ravel(),3)) not in wall_ids]
        if q:items.append({'kind':'opening-cut','id':'mapped-openings','wallFaces':len(q),'wallLengthMetres':round(float(sum(np.hypot(w[1][0]-w[0][0],w[1][2]-w[0][2]) for w in q)),1),'evidence':'Mapped: the water and street openings the traced embankment already stops at (2 m clearance). Interpreted: brick abutment and wing faces on its cut ends; no surveyed abutment.'})
        walls+=q
    if items:
        record['works']={'removedTriangles':sorted(removed),'addedTriangles':np.round(np.array([np.asarray(t) for t in added]),3).tolist() if added else [],'walls':np.round(np.array(walls),3).tolist() if walls else [],'items':items}
        rail_works[name]=[{k:v for k,v in it.items() if k!='evidence'} for it in items]
        print('RAILWAY WORKS:',name,rail_works[name],flush=True)
result={'epoch':'1900','status':'regional early-marsh ground applied to main industrial reconstruction',
    'scope':'1848-supported marsh envelope and its interpreted edge blend; existing outer terrain retained',
    'files':files,'field':{'bounds':[e0-538900,183209-n1,e1-538900,183209-n0],'step':step,'width':shape[1],'height':shape[0],'cellCentres':True},
    'replacements':stats,'groundMeshVertices':len(mesh),'groundMeshAreaM2':area.area,
    'replacementBaseGround':rings(original_base.difference(outline)),'replacementRegionalGround':rings(original_regional.difference(outline)),
    'roadControlIds':sorted({id for fit in road_fits for id in fit[-1]}),
    'siteGround':pads,'retainingEdgeCrests':wall_levels,
    'retainingEdgeFill':{'crestMethod':f'1.65 m interpretive crest blended to the observed along-bank crest by the marsh weight {WALL_INLAND_M} m behind the wall; {WALL_MEAN_M} m running mean along the wall; grade-limited upper envelope at {WALL_GRADE} m per metre',
        'fillMethod':f'land side filled level with the coping to {WALL_TOP_M} m from the wall line, then falling at 1:{WALL_BATTER} to the surrounding ground (at most {WALL_REACH_M} m); never lowers ground; water, street corridors and building footprints excluded; battered at the same slope down to unwalled shoreline and to preserved intertidal mud; in the river-network mesh, land vertices of triangles straddling a wall are held down so no ground stands more than {WALL_TOE_M} m above low water at the water face, and no filled vertex stands more than 2.4 m above a mesh neighbour',
        'evidence':'Mapped: the shoreline and GIS industrial plot edges that the interpretive wall routes follow (river-network retainingEdges; the walls themselves are not a surveyed inventory), and the high-confidence wall_top/embankment_top spot heights behind the along-bank crest profile. Estimated: the coping grade between readings, the berm width and batter, and the fill itself; no surveyed section of any wall or its backfill.'},
    'shoreLip':{'method':f'bank vertices within {LIP_M} m of the regional shoreline whose previous height stood more than 0.5 m above low water are lifted to the full crest only within {MASONRY_REACH_M} m of a recorded masonry edge (river-system canalFacingRoutes, river-network retainingEdges), and keep their previous reviewed height (capped at the crest) inside a reviewed terrain patch whose recorded shore transition is no wider than {LIP_M} m; all other shores take the 0-3 m smoothstep earth face',
        'lipVertices':lip_vertices,'steepShorePatches':[t['id'] for t in steep_patches],
        'evidence':'Mapped: the shorelines, the interpreted canal-face and retaining-edge routes, and the reviewed patch outlines. Recorded in the bank policy: earth and canal-earth profiles elsewhere ("no continuous masonry assumed on Hackney Cut"). Estimated: the 1.5 m reach of a masonry edge and the smoothstep face itself; no surveyed bank section.'},
    'junctionEndCaps':{'method':f'river-network vertices within {END_FACE_M} m of drawn river-system water (waterPolygons) are capped at the water edge (low water + 0.02 m) rising by smoothstep to their existing height {END_FACE_M} m from that water; recorded raised shore edges excluded; no vertex lowered more than 2.4 m below a mesh neighbour',
        **end_caps,
        'evidence':'Mapped: the river-system water polygons and the network channel ends that meet them. Estimated: the earth face at each junction, taken from the system bank face rather than from any survey of the confluence banks.'},
    'pathCorridors':{'method':'footpath corridors (infrastructure roads of kind "path") take no street level of their own: the ground under them is whatever the marsh, bank band, yard pads, batters and wall fill make it, and docs/infrastructure.js draws the cinder surface 0.05 m above that ground; they raise no batter of their own and do not stop the neighbouring batters or wall fill; only inside the Northern Outfall Sewer embankment footprint (bank and crest triangles, 1 m margin) does a path corridor keep its former inverse-distance street level, so the embankment toes are unchanged; streets, lanes and roads keep their street readings',
        'corridors':path_corridors,
        'evidence':'Mapped: the path centrelines and widths (OS five-foot and VIII.32 traces in infrastructure.json) and the sewer embankment footprint. Observed: none for the paths themselves; the one street reading formerly applied to the Mill Mead riverbank path (sh_538874_183253, 2.19 m scene) is an Abbey Road/Abbey Lane spot height by the Abbey Mill bridge, not a level on the path, and spread 2.2 m above the marsh along the first 120 m of the path, with a 2.4 m drop at the end of its reach. Interpreted: a riverside footpath across the marsh lies at marsh or bank level with a few centimetres of made-up cinder; its cinder thickness and any local raising are not surveyed.'},
    'networkTidalWater':{'method':'the river network tide polygons (drawn as water at low water and as tidal water rising to high water) are added to the water mask of the bank blend and the edge batters: vertices inside them keep their native river-network (or core) heights, and no batter rises from inside them, except within '+str(TIDAL_BUILDING_M)+' m of a mapped building footprint, where the building frontage keeps the bank blend; street levels, retaining-wall sides, the wall fill and the river-network wall-face clearing keep the regional water mask',
        'nativeVerticesKept':tidal_kept,'faceMethod':f'blended ground beside the outline stands no steeper than 1:{TIDAL_FACE} above the native tidal ground (along river-network mesh edges, or across the core grid), never below its own pre-blend height and not in street corridors or building footprints; the wall fill is applied afterwards as before',
        'faceLowering':tidal_faced,
        'evidence':'Mapped: the river network tidal outline (river-network.json tide.polygons) and its interpreted river-side shelves and bank faces. Estimated: those shelf and bank-face heights (river-network build) and the 1:1.5 face that rises from them to the regional bank crest outside the outline. The fill behind the interpretive retaining walls, which stand inside the outline, is unchanged.'},
    'edgeBatters':{'method':f'premises pads and street corridors stay level inside their outlines; outside, the ground meets them on an earth batter falling at 1:{EDGE_BATTER} from the nearest edge until it meets the surrounding ground (at most {EDGE_REACH_M} m), including into a lower neighbouring yard but never onto a street corridor; where a raised pad stands within {FRONTAGE_M} m of a regional bank, the strip between yard edge and bank (bounded by rays from the yard edge to the nearest shoreline that cross no water or railway embankment) is made up to the lower of the yard and bank-crest levels; neither raises water, ground steeper than 1:{EDGE_BATTER} above low water from the water edge, or ground steeper than 1:{EDGE_BATTER} above a building footprint (its premises level, or its unraised ground if it has no premises pad); the 10 m level field keeps its unbattered value in cells within one cell diagonal of a building without a premises pad, so no seated building moves',
        'frontages':[{'siteId':pads[j]['siteId'],'areaM2':round(g.area,1)} for g,j in frontages],
        'evidence':'Mapped: the premises outlines (ground-plan sites), the street routes and widths, the shorelines, and the building footprints. Observed: the same-premises yard readings and street spot heights that set the pad and corridor levels, and the bank-top readings behind the crest. Estimated: the 1:1.5 batter, its reach, and the frontage fill between yard and bank; no surveyed section of any yard edge, street embankment or wharf frontage.'},
    'abbeyMillCrossingApproach':{'method':f'Abbey Lane corridor ground level with the abbey-mill-crossing deck (deck height minus the {DECK_ROAD_OFFSET} m road-surface offset) for {DECK_LANDING_M} m beyond each deck end, then within 1 in {round(1/DECK_GRADE)} of the deck, clipped to the corridor readings; within {DECK_APPROACH_M} m of the deck the regional bank band does not lift the street, the bank beside it is cut back at 1:{EDGE_BATTER}, and under the deck the bank stays 0.1 m below the 0.4 m deck slab',
        'deckHeight':[b[1]+DECK_ROAD_OFFSET for v in graded_decks.values() for b in v][0] if graded_decks else None,
        'evidence':'Mapped: the crossing and approach alignment (OS VIII.32, road-traces.json). Observed: Abbey Lane street spot heights sh_538874_183253 (2.19 m scene, 8.1 m west of the deck) and sh_538944_183274 (2.40 m, 34 m east). Interpreted: the 1.8 m deck height (road-traces.json); the approach grade and landing are estimates made to meet it. Both readings stand above the deck, so the graded approach dips to the bridge; raising the deck in road-traces.json is the alternative.'},
    'roadBridgeClearance':{'method':f'fitted to the road surfaces docs/infrastructure.js draws (street, footway and path triangles at ground() under their vertices plus 0.065, 0.095 and 0.05 m; ground() raised within reach of a road bridge to the cone deck - {DECK_ROAD_OFFSET} - {BRIDGE_CONE} m per metre from the deck route; decks as boxes at the deck height), in order: (1) approach embankments: under road triangles the ground is made up to the bridge cone and falls beyond the road edge at 1:{EDGE_BATTER} to the surrounding ground, never over water nor steeper than 1:{EDGE_BATTER} above low water from the water edge or a span footprint, above a building from its footprint, or above the outer edge of the mesh it is in; (2) approach cuttings on the bridge\'s own road (corridor plus {ROAD_SHOULDER_M} m footway, within {CUT_REACH_M} m of the deck route, crossing streets excluded): ground no higher than the deck road level for {DECK_LANDING_M} m from the deck route, then rising at no more than 1 in {round(1/DECK_GRADE)}, sides cut at 1:{EDGE_BATTER}; (3) span clearance: inside each footprint (between the first and last drawn low water on lines parallel to the deck route across the deck width, the outermost lines\' spans carried on {CLEAR_MARGIN_M} m beyond each deck edge, together with the clear zone between the abutment faces of data/maps/road-bridge-forms.json as docs/road-bridges.js places them, out to the register\'s clear-zone margin) no ground above the water edge ({WATER_EDGE:.2f} m); (4) every other landscape vertex inside a road or deck triangle, or within one mesh edge of one, held at or below that road\'s drawn surface (its ground() values interpolated over the triangle plus the triangle\'s offset, less up to {ROAD_CAP_BELOW_M} m while keeping {ROAD_CAP_KEEP_M} m of the offset; the deck top likewise under a deck), with the vertices each road vertex takes its ground from (the mesh triangles or core cell containing it) held so in {ROAD_SUPPORT_PASSES} passes only, the road re-read after each (it follows them down: roadSupport.roadVertexChangeMetres), and every other vertex then in one pass that leaves the road where it stands; beyond one mesh edge, ground above a road is cut back at 1:{EDGE_BATTER} from it (outside building footprints); the 20 m regional mesh is cut along the road triangles so its triangles inside a street are planar with it; streets passing under the Northern Outfall Sewer keep the marsh level at the middle of the opening for {DECK_LANDING_M} m beyond the opening axis and rise from it at no more than 1 in {round(1/DECK_GRADE)}. Channel beds in drawn water and preserved tidal mud are never changed; level.f32 is not changed by this pass',
        'waterEdge':WATER_EDGE,'footprints':{k:rings(g) for k,g in span_footprints.items()},'pass':road_pass,
        'underpasses':[{'road':name,'axis':np.round(np.array(axis.coords),2).tolist(),'streetSceneY':round(street,3)} for v in underpasses.values() for axis,street,name in v],
        'evidence':'Mapped: the street, footway, path and deck geometry (infrastructure.json), the drawn low water, the building footprints and the sewer openings (ground-plan.json). Observed: none at the bridges; the deck heights are interpretations (road-traces.json) and so are the embankments, cuttings and clearances fitted to them. The Bow Bridge east approach parapet bench mark (OS 25-inch, "hatched south parapet / retaining wall") suggests a walled rather than battered approach on that side; the batter is held off the frontage buildings there in any case. The Mill Meads works road readings (2.83 m at Abbey Road, 2.10 m to the north) lie 115 m and more from the sewer: its dip under the sewer to marsh level is an interpretation, as T1b drew it.'},
    'railwaySlopes':railways,
    'railwayWorks':{'method':f'formation stations, routes and the refitted embankment heights are unchanged; per railway, works.removedTriangles lists embankment triangles not drawn and works.addedTriangles the earth drawn instead (remainders re-triangulated in their own planes, hipped ends, the LT&SR west approach); works.walls are brick faces (top edge on the earthwork, foot {RAIL_FOOTING} m below the ground or at {RAIL_BED} m beside water). No embankment stands over drawn water: at recorded bridges the fill stops {RAIL_WATER_CLEAR} m short of the water behind an abutment face with in-line wings; where a raised embankment would come within {RAIL_GAP} m of a mapped building footprint it stops {RAIL_GAP} m off behind a retaining wall, except where the footprint lies in the formation (recorded as a conflict); raised line ends with nothing beyond close with an earth end at the side slope',
        'railways':rail_works,
        'evidence':'Mapped: the railway routes and the formation they carry (infrastructure.json), the drawn water, the street corridors and the building footprints; the OS five-foot plan for the Bow Creek and Hackney Cut crossings and the line ends (data/maps/railway-bridge-forms.json). Interpreted: every abutment, wing and retaining wall, the hipped ends and the LT&SR west approach; none is a surveyed structure.'},
    'continuousBanks':{'profileCount':len(banks.lines),'sourceIds':banks.accepted_ids,'heightStatus':'observed crests interpolate along bank; unsampled components inferred'},
    'probes':[{'name':name,'scenePosition':[e-538900,183209-n],'groundSceneY':float(base(np.array([[e-538900,183209-n]]))[0])} for name,e,n in [('Pudding–City marsh',537650,184100),('Western neighbouring marsh',537300,184100),('Northern Mill Meads',538550,183200),('Abbey marsh',539200,182900),('Western Plaistow',539800,181800)]],
    'limitations':['Site pads without yard readings use a conservative premises estimate, not a measured fill thickness.','Existing railway grades, sewer cover, channel beds and water levels retained.','The flood solver has not been recalibrated to these visible geometry changes.',
        'Wall fill is limited by the 1 m river-network mesh, whose triangles straddle the 0.32 m walls: a narrow gutter (median 0.7 m deep) remains in the first metre behind many walls. Building footprints are not filled, so buildings standing within 3 m of a wall keep their premises ground. Walls in the Channelsea core stand on preserved tidal mud and have no fill.',
        'Road surfaces are drawn on the ground under their own vertices only; the landscape is fitted under them (roadBridgeClearance), not the reverse, so where a road triangle spans a bank the bank is cut back rather than the road raised over it. Preserved tidal mud under the Abbey Lane footways is not cut, and the approaches of a bridge stop where no adjustable mesh carries on (Three Mills Lea bridge west end).',
        'Yard and street batters are not drawn under building footprints or on preserved tidal mud, so a vertical face remains where a street shoulder or yard edge runs into a building; the 20 m regional ground mesh spans the batters as tilted triangles rather than resolving them.'],
    'inputHashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [*inputs,Path(__file__).resolve(),ROOT/'scripts/regional_continuous_structures.py']}}
(OUT/'main-landscape-1900.json').write_text(json.dumps(result,separators=(',',':'))+'\n')
print('MAIN LANDSCAPE:',len(mesh)//3,'new background triangles;',len(pads),'premises levels',flush=True)
