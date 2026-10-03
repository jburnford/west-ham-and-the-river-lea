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
road_fits=[]
for feature in meta['laterSurfaceLayers']['features']:
    if feature['kind']!=10:continue
    road=next(r for r in infra['roads'] if r['name']==feature['name'])
    line=LineString(road['route']);ids=feature['sourceIds']
    positions=np.array([[records[id]['positionBNG'][0]-538900,183209-records[id]['positionBNG'][1]] for id in ids])
    levels=np.array([records[id]['provisionalODNMetres']-offset for id in ids])
    road_fits.append((road,line.buffer(road['width']/2+3),positions,levels,cKDTree(positions),ids))
road_tree=shapely.STRtree([fit[1] for fit in road_fits])
def road_levels(points,result):
    matches=road_tree.query(shapely.points(points),predicate='within')
    if not matches.size:return result
    for j in np.unique(matches[1]):
        indices=matches[0][matches[1]==j];road,footprint,positions,levels,tree,ids=road_fits[j]
        d,ii=tree.query(points[indices],k=min(4,len(positions)))
        if d.ndim==1:d=d[:,None];ii=ii[:,None]
        links=shapely.linestrings(np.stack([np.broadcast_to(points[indices,None,:],(*ii.shape,2)),positions[ii]],axis=2).reshape(-1,2,2))
        clear=~shapely.intersects(links,water).reshape(ii.shape)
        w=np.where(clear&(d<=120),1/np.maximum(d,3)**2,0);total=w.sum(axis=1);ok=total>0
        result[indices[ok]]=(levels[ii[ok]]*w[ok]).sum(axis=1)/total[ok]
    return result

def base(points):
    result=sample(filled,points)
    matches=pad_tree.query(shapely.points(points),predicate='within')
    if matches.size:
        for j in np.unique(matches[1]):result[matches[0][matches[1]==j]]=pads[j]['groundSceneY']
    return road_levels(points,result)

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
MASONRY_REACH_M=1.5;LIP_M=.6;lip_vertices={}
masonry=shapely.union_all([LineString(r['route']) for r in system['bankSections']['canalFacingRoutes']]+[LineString(r) for r in network['retainingEdges']['routes'] if len(r)>1])
steep_patches=[t for t in system['bankSections']['terrainPatches'] if t['config']['shoreTransitionMetres'][1]<=LIP_M]
masonry_zone=masonry.buffer(MASONRY_REACH_M);patch_zone=geometry([p for t in steep_patches for p in t['polygons']])
raised_shore=masonry_zone.union(patch_zone)
for zone in (masonry_zone,patch_zone,raised_shore):shapely.prepare(zone)
def blend_surface(points,old,bank=True,key='groundMesh'):
    w=weight(points);out=np.asarray(old,dtype=float).copy();selected=w>0
    if not selected.any():return out
    p=points[selected];g=base(p);wet=shapely.contains_xy(water,p[:,0],p[:,1]);old_y=out[selected]
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
            levels=(network['waterLevel']+.02)*(1-rise)+levels*rise
            g[margin]=levels
    # Bed and drain-water vertices retain their native geometry and levels.
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

files={};stats={}
def export_heights(key,points,old,preserve=None,triangles=None):
    blended=blend_surface(points,old,key=key);new=fill_behind_walls(points,blended.copy())
    if triangles is not None:new=clear_wall_faces(points,new,blended,triangles)
    if key=='network':new=cap_junction_ends(points,new,triangles)
    if preserve is not None:
        # Wall fill stands no steeper than 1:1.5 above preserved tidal mud.
        grid=(core['height'],core['width']);dist,nearest=distance_transform_edt(~preserve.reshape(grid),return_indices=True)
        cap=old[np.ravel_multi_index(tuple(nearest),grid)].ravel()+dist.ravel()*core['step']/WALL_BATTER
        new=np.maximum(blended,np.minimum(new,cap));new[preserve]=old[preserve]
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
# Existing flat placeholder polygons need interior vertices, not just raised edges.
outline=local(Polygon(meta['regionalMarshBaseline']['config']['outlineBNG']))
original_base=geometry(system['baseGround']);original_regional=geometry(system['regionalGround'])
area=original_base.union(original_regional).intersection(outline).difference(water)
x0,z0,x1,z1=area.bounds;mesh_step=20
x,z=np.meshgrid(np.arange(np.floor(x0/mesh_step)*mesh_step,x1,mesh_step),np.arange(np.floor(z0/mesh_step)*mesh_step,z1,mesh_step))
cells=shapely.box(x.ravel(),z.ravel(),x.ravel()+mesh_step,z.ravel()+mesh_step)
parts=shapely.get_parts(shapely.intersection(cells,area));parts=parts[shapely.area(parts)>1e-5]
triangles=shapely.get_parts(shapely.constrained_delaunay_triangles(parts));triangles=triangles[shapely.area(triangles)>1e-5]
coords=shapely.get_coordinates(triangles).reshape(-1,4,2)[:,:3,:]
# Upward scene winding.
a=coords[:,1]-coords[:,0];b=coords[:,2]-coords[:,0];cross=a[:,0]*b[:,1]-a[:,1]*b[:,0];coords[cross>0]=coords[cross>0][:,[0,2,1]]
points=coords.reshape(-1,2);heights=surface(points,np.full(len(points),-.1));mesh=np.column_stack([points[:,0],heights,points[:,1]]).astype('<f4')
mesh.tofile(OUT/'main-landscape-1900.background.f32');files['groundMesh']='main-landscape-1900.background.f32'
# Scene sampling for objects outside the original detailed grids.
east,north=np.meshgrid(np.arange(e0+step/2,e1,step),np.arange(n1-step/2,n0,-step));points=np.column_stack([east.ravel()-538900,183209-north.ravel()]);values=base(points).reshape(shape)
values.astype('<f4').tofile(OUT/'main-landscape-1900.level.f32');files['level']='main-landscape-1900.level.f32';support.astype('<f4').tofile(OUT/'main-landscape-1900.weight.f32');files['weight']='main-landscape-1900.weight.f32'
# Retaining-edge crests (wall_levels) are computed above with the land-side fill.
# Refitting railway toes leaves every formation station unchanged.
railways=[]
for adjustment in system.get('railwayGroundAdjustments',[]):
    rail=next(r for r in infra['railways'] if r.get('id')==adjustment['railwayId'])
    rail['embankment'][adjustment['triangle']][adjustment['vertex']][1]=adjustment['afterY']
for rail in infra['railways']:
    vertices=np.array(rail['embankment']);p=vertices[:,:,[0,2]].reshape(-1,2);line=LineString(rail['route']);pts=shapely.points(p)
    d=shapely.distance(pts,line);s=shapely.line_locate_point(line,pts);stations=np.array(rail.get('stations',[]))
    crest=np.interp(s,stations[:,5],stations[:,2]) if len(stations) else np.full(len(p),rail['formationHeight']+.05)
    half=rail.get('baseHalfWidth',15);crest_half=rail.get('crestHalfWidth',max(3,rail.get('tracks',1)*2));t=np.clip((half-d)/max(1,half-crest_half),0,1)
    g=base(p);old=vertices[:,:,1].ravel();target=g+t*(crest-g);w=weight(p)
    # Exact crest vertices and bridge geometry retain their original elevations.
    w[abs(old-crest)<.15]=0
    levels=old+w*(target-old)
    railways.append({'name':rail['name'],'heights':levels.reshape(-1,3).tolist()})
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
    'railwaySlopes':railways,
    'continuousBanks':{'profileCount':len(banks.lines),'sourceIds':banks.accepted_ids,'heightStatus':'observed crests interpolate along bank; unsampled components inferred'},
    'probes':[{'name':name,'scenePosition':[e-538900,183209-n],'groundSceneY':float(base(np.array([[e-538900,183209-n]]))[0])} for name,e,n in [('Pudding–City marsh',537650,184100),('Western neighbouring marsh',537300,184100),('Northern Mill Meads',538550,183200),('Abbey marsh',539200,182900),('Western Plaistow',539800,181800)]],
    'limitations':['Site pads without yard readings use a conservative premises estimate, not a measured fill thickness.','Existing railway grades, sewer cover, channel beds and water levels retained.','The flood solver has not been recalibrated to these visible geometry changes.',
        'Wall fill is limited by the 1 m river-network mesh, whose triangles straddle the 0.32 m walls: a narrow gutter (median 0.7 m deep) remains in the first metre behind many walls. Building footprints are not filled, so buildings standing within 3 m of a wall keep their premises ground. Walls in the Channelsea core stand on preserved tidal mud and have no fill.'],
    'inputHashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [*inputs,Path(__file__).resolve(),ROOT/'scripts/regional_continuous_structures.py']}}
(OUT/'main-landscape-1900.json').write_text(json.dumps(result,separators=(',',':'))+'\n')
print('MAIN LANDSCAPE:',len(mesh)//3,'new background triangles;',len(pads),'premises levels',flush=True)
