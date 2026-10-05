"""Shore-conforming banks and submerged beds for the regional river extension.

Each band is triangulated as a constrained polygon: no rectangular grid teeth
at the waterline, no banks across polygon joins, no cut-off planes at tile seams.
"""
import numpy as np
import shapely
from shapely.geometry import Polygon, LineString, GeometryCollection
from build_lower_lea_region import polygons, rings
import tide_levels as tl


def smooth(a, b, v):
    t=np.clip((v-a)/(b-a),0,1)
    return t*t*(3-2*t)


def lines(g):
    if g.geom_type in ('LineString','LinearRing'):return [g]
    return [line for part in getattr(g,'geoms',[]) for line in lines(part)]


class Distance:
    """Exact point distance using a spatial index of short boundary pieces."""
    def __init__(self,g):
        self.geometry=g
        self.area=g.geom_type in ('Polygon','MultiPolygon')
        shapely.prepare(g)
        pieces=[]
        for line in lines(g.boundary if self.area else g):
            coords=np.asarray(line.coords)
            pieces.extend(LineString(coords[i:min(i+17,len(coords))]) for i in range(0,len(coords)-1,16))
        self.tree=shapely.STRtree(pieces)
    def __call__(self,pts):
        if not len(self.tree.geometries):return np.full(len(pts),np.inf)
        near=self.tree.nearest(pts)
        d=shapely.distance(pts,self.tree.geometries[near])
        if self.area:d[shapely.covers(self.geometry,pts)]=0
        return d


def build_banks(water, protected, reaches, geoms, config, open_cuts, flat_ground, marsh=None, tidal=None):
    """tidal: regional water that takes the tide (data/maps/os-tide-levels.json); its beds
    sit below low water and its banks rise from the low-water edge to the tidal crest."""
    level=config['referenceLevelSceneY']
    canal=shapely.union_all([geoms[r['id']] for r in reaches if r['role']=='navigation'
        and r['id'] not in config['naturalOverrideReachIds']])
    hard=shapely.union_all([geoms[f'Water_1895-{k}'] for k in config['canalFaced']['sourceIndices']])
    # No artificial banks across the edge of the source coverage.
    openings=shapely.union_all(open_cuts)
    open_guard=openings.buffer(14)
    shore=water.boundary.difference(openings.buffer(.05))
    bank_area=water.buffer(14,quad_segs=3).difference(water).difference(protected).difference(open_guard)
    if marsh is not None:bank_area=bank_area.difference(marsh.structure_area)
    bed_area=water.difference(protected)
    extension_area=bank_area.union(bed_area)
    if marsh is not None:extension_area=extension_area.union(marsh.area)
    positions=[];sediment=[];covers=[];indices=[];offset=0;coverage=[]
    water_distance=Distance(water);canal_distance=Distance(canal);hard_distance=Distance(hard)
    protected_distance=Distance(protected);flat_distance=Distance(flat_ground)
    open_distance=Distance(openings);shore_distance=Distance(shore)
    tidal_distance=Distance(tidal) if tidal is not None and not tidal.is_empty else None

    def tidal_weight(pts,d):
        # 1 where the nearest water is tidal, fading over 5 m where tidal and still water meet.
        if tidal_distance is None:return np.zeros(len(pts))
        return 1-smooth(0,5,np.maximum(0,tidal_distance(pts)-d))

    def fields(xz, force_bed=False):
        pts=shapely.points(xz)
        # Polygon-boundary roundoff must never classify a bed vertex as dry
        # bank crest. The section being built supplies the authoritative side.
        wet=np.ones(len(pts),dtype=bool) if force_bed else shapely.covers(water,pts)
        d=water_distance(pts)
        canal_weight=1-smooth(0,5,np.maximum(0,canal_distance(pts)-d))
        hard_weight=1-smooth(0,2,np.maximum(0,hard_distance(pts)-d))
        height=[];silt=[]
        for name in ['earth','canalEarth','canalFaced']:
            p=config[name]
            height.append(level+np.interp(d,p['offsetsMetres'],p['heightsAboveWaterMetres']))
            silt.append(np.interp(d,p['offsetsMetres'],p['sediment']))
        y=height[0]*(1-canal_weight)+height[1]*canal_weight
        mud=silt[0]*(1-canal_weight)+silt[1]*canal_weight
        y=y*(1-hard_weight)+height[2]*hard_weight;mud*=1-hard_weight
        # Tidal reaches: the bank face rises from the low-water edge to the tidal crest over
        # 5 m (as the river network's), holds to 8 m, then falls to the earth profile's foot.
        tw=tidal_weight(pts,d)
        y_tidal=np.where(d<=5,tl.tidal_shelf(d),np.interp(d,[5,8,14],[tl.CREST,tl.CREST,level-.16]))
        y=y*(1-tw)+y_tidal*tw;mud=mud*(1-tw)+(1-smooth(tl.HIGH-.1,tl.HIGH+.4,y_tidal))*tw
        # Subtle longitudinal variation keeps earthen banks from looking like
        # a uniform concrete bund; masonry coping stays level.
        variation=.045*np.sin(xz[:,0]*.071+np.sin(xz[:,1]*.037))
        y+=variation*smooth(0,2,d)*(1-smooth(8,14,d))*(1-hard_weight)
        # Fade to the preserved core and existing built ground. No structures
        # are moved to make room for a bank and no riverbed is filled by this.
        seam=smooth(0,5,protected_distance(pts))*smooth(14,22,open_distance(pts))
        clearance=smooth(0,2,flat_distance(pts))
        y=-.1+(y+.1)*seam*clearance
        if marsh is not None and not force_bed:y=marsh.apply(xz,y)
        mud*=seam
        shore_depth=config['bed']['shoreDepthMetres']
        inside=shore_distance(pts)
        depth=config['bed']['riverDepthMetres']*(1-canal_weight)+config['bed']['canalDepthMetres']*canal_weight
        bed=level-shore_depth-(depth-shore_depth)*smooth(0,5,inside)
        bed=bed*(1-tw)+tl.tidal_bed(inside)*tw
        y[wet]=bed[wet];mud[wet]=1
        cover=hard_weight*(1-smooth(3.5,6,d))
        return y,mud,cover

    def mesh_area(area, kind):
        nonlocal offset
        if area.is_empty:return
        area=shapely.segmentize(area,config['mesh']['shoreSegmentMetres'])
        if kind=='marsh':
            # Interior samples prevent long triangles from flattening the
            # bank-to-marsh transition between the surveyed margins.
            step=marsh.config['meshCellMetres'];x0,z0,x1,z1=area.bounds
            x,z=np.meshgrid(np.arange(np.floor(x0/step)*step,x1,step),np.arange(np.floor(z0/step)*step,z1,step))
            cells=shapely.box(x.ravel(),z.ravel(),x.ravel()+step,z.ravel()+step)
            parts=shapely.get_parts(shapely.intersection(cells,area))
            triangles=shapely.get_parts(shapely.constrained_delaunay_triangles(parts))
        else:triangles=shapely.get_parts(shapely.constrained_delaunay_triangles(area))
        if len(triangles)==0:return
        coords=shapely.get_coordinates(triangles).reshape(-1,4,2)[:,:3,:]
        # Deduplicate within a band and orient every triangle upwards.
        cross=(coords[:,1,0]-coords[:,0,0])*(coords[:,2,1]-coords[:,0,1])-(coords[:,1,1]-coords[:,0,1])*(coords[:,2,0]-coords[:,0,0])
        coords[cross>0]=coords[cross>0][:,[0,2,1]]
        xz,inverse=np.unique(coords.reshape(-1,2),axis=0,return_inverse=True)
        y,mud,cover=fields(xz,force_bed=kind=='bed')
        if kind=='bank':
            # Polygon boundary points belong to both water and land. The land
            # side uses the dry profile; the bed side stays submerged.
            onshore=shapely.distance(shapely.points(xz),water.boundary)<1e-6
            if onshore.any():
                pts=shapely.points(xz[onshore]);h=1-smooth(0,2,hard_distance(pts))
                seam=smooth(0,5,protected_distance(pts))*smooth(14,22,open_distance(pts))
                clearance=smooth(0,2,flat_distance(pts))
                y[onshore]=-.1+((level+.02)*(1-h)+(level+1.25)*h+.1)*seam*clearance
                tw=tidal_weight(pts,np.zeros(len(pts)))
                y[onshore]=y[onshore]*(1-tw)+tl.BED_EDGE*tw
                mud[onshore]=1-h
        positions.append(np.column_stack([xz[:,0],y,xz[:,1]]));sediment.append(mud);covers.append(cover)
        indices.append(inverse+offset)
        coverage.append({'kind':kind,'areaM2':float(area.area),'triangles':len(coords),
                         'vertexStart':offset,'vertexCount':len(xz)})
        offset+=len(xz)
        print(f'  {kind} band: {len(coords):,} triangles',flush=True)

    # Concentric shore bands follow every island, bank and confluence exactly.
    offsets=config['mesh']['sectionOffsetsMetres']
    inner=water
    for distance in offsets[1:]:
        outer=water.buffer(distance,quad_segs=3)
        mesh_area(outer.difference(inner).intersection(bank_area),'bank')
        inner=outer
    previous=water
    for depth in [1.5,4]:
        inset=water.buffer(-depth,quad_segs=3)
        mesh_area(previous.difference(inset).intersection(bed_area),'bed')
        previous=inset
    mesh_area(previous.intersection(bed_area),'bed')
    if marsh is not None:mesh_area(marsh.area.difference(bank_area),'marsh')

    p=np.concatenate(positions).astype('<f4'); ix=np.concatenate(indices).ravel().astype('<u4')
    s=np.clip(np.concatenate(sediment)*255,0,255).astype('u1')
    c=np.column_stack([np.concatenate(covers)*255,np.zeros(len(p))]).astype('u1')
    triangles=ix.reshape(-1,3)
    centres=p[triangles].mean(axis=1)
    centre_points=shapely.points(centres[:,0],centres[:,2])
    coping=(water_distance(centre_points)<.451)&(hard_distance(centre_points)<.451)&(centres[:,1]>level+.9)
    normal_indices=triangles[~coping].ravel();coping_indices=triangles[coping].ravel()
    ix=np.concatenate([normal_indices,coping_indices]).astype('<u4')

    # Exact vertical canal facing at the mapped shoreline; no line is drawn
    # across a confluence, bridge opening or source-window boundary.
    hard_shore=shore.intersection(hard.buffer(.01)).difference(protected.buffer(.02)).difference(open_guard)
    if not flat_ground.is_empty:hard_shore=hard_shore.difference(flat_ground.buffer(.5))
    face=[];face_uv=[];routes=[]
    for line in lines(hard_shore):
        if line.length<.2:continue
        points=np.asarray(shapely.segmentize(line,2).coords)
        # Sample infinitesimally landward through the same profile as the bank.
        heights=np.full(len(points),level+1.25)
        seam=smooth(0,5,protected_distance(shapely.points(points)))*smooth(14,22,open_distance(shapely.points(points)))
        clearance=smooth(0,2,flat_distance(shapely.points(points)))
        heights=-.1+(heights+.1)*seam*clearance
        station=np.r_[0,np.cumsum(np.linalg.norm(np.diff(points,axis=0),axis=1))]
        for j in range(len(points)-1):
            a,b=points[j:j+2];ya,yb=heights[j:j+2];bottom=level-config['bed']['shoreDepthMetres']
            corners=[[a[0],bottom,a[1]],[b[0],bottom,b[1]],[b[0],yb,b[1]],[a[0],ya,a[1]]]
            uv=[[station[j],bottom],[station[j+1],bottom],[station[j+1],yb],[station[j],ya]]
            for k in [0,1,2,0,2,3]:face.append(corners[k]);face_uv.append(uv[k])
        routes.append({'route':points.tolist(),'topSceneY':heights.tolist(),'material':'inferred weathered brick','lengthMetres':line.length})
    stats={'method':'constrained shoreline bands','profiles':config,
        'newBankAreaM2':bank_area.area,'submergedBedAreaM2':bed_area.area,
        'modelledShoreLengthMetres':shore.difference(protected).difference(open_guard).length,
        'canalFacingLengthMetres':sum(r['lengthMetres'] for r in routes),
        'materialGroups':[{'start':0,'count':len(normal_indices),'materialIndex':0},
                          {'start':len(normal_indices),'count':len(coping_indices),'materialIndex':1}],
        'openBoundaryLengthMetres':openings.length,'coverage':coverage,
        'openBoundaries':[list(line.coords) for line in lines(openings)],
        'canalFacingRoutes':routes,'bankPolygons':rings(bank_area),
        'capacityCalibrated':False,'geometryEpoch':'1900',
        'terrainPatches':marsh.metadata() if marsh is not None else []}
    return p,ix,s,c,np.asarray(face,dtype='<f4'),np.asarray(face_uv,dtype='<f4'),extension_area,stats
