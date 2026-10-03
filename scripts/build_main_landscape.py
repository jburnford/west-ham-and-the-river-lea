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

def surface(points,old,bank=True):
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
            rise[(d<.6)&(old_y[margin]>network['waterLevel']+.5)]=1
            levels=(network['waterLevel']+.02)*(1-rise)+levels*rise
            g[margin]=levels
    # Bed and drain-water vertices retain their native geometry and levels.
    use=~wet;out_indices=np.flatnonzero(selected)[use]
    out[out_indices]=old_y[use]+w[selected][use]*(g[use]-old_y[use])
    return out

files={};stats={}
def export_heights(key,points,old,preserve=None):
    new=surface(points,old)
    if preserve is not None:new[preserve]=old[preserve]
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
    export_heights(key,p[:,[0,2]],old)
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
# Retaining edges use the same observed longitudinal crest profile.
wall_levels=[]
for route in network['retainingEdges']['routes']:
    p=np.array(route);bng=np.column_stack([538900+p[:,0],183209-p[:,1]]);w=weight(p)
    wall_levels.append((network['retainingEdges']['crestHeight']+w*(banks.crest(bng)-offset-network['retainingEdges']['crestHeight'])).tolist())
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
    'siteGround':pads,'retainingEdgeCrests':wall_levels,'railwaySlopes':railways,
    'continuousBanks':{'profileCount':len(banks.lines),'sourceIds':banks.accepted_ids,'heightStatus':'observed crests interpolate along bank; unsampled components inferred'},
    'probes':[{'name':name,'scenePosition':[e-538900,183209-n],'groundSceneY':float(base(np.array([[e-538900,183209-n]]))[0])} for name,e,n in [('Pudding–City marsh',537650,184100),('Western neighbouring marsh',537300,184100),('Northern Mill Meads',538550,183200),('Abbey marsh',539200,182900),('Western Plaistow',539800,181800)]],
    'limitations':['Site pads without yard readings use a conservative premises estimate, not a measured fill thickness.','Existing railway grades, sewer cover, channel beds and water levels retained.','The flood solver has not been recalibrated to these visible geometry changes.'],
    'inputHashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [*inputs,Path(__file__).resolve(),ROOT/'scripts/regional_continuous_structures.py']}}
(OUT/'main-landscape-1900.json').write_text(json.dumps(result,separators=(',',':'))+'\n')
print('MAIN LANDSCAPE:',len(mesh)//3,'new background triangles;',len(pads),'premises levels',flush=True)
