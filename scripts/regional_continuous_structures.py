"""Continuous longitudinal profiles and a fine mesh for narrow earthworks.

The coarse raster is sampled from the same profiles. Elevated water crossings
are separate mesh surfaces, never ground or implicit hydraulic barriers.
"""
import numpy as np
import shapely
from scipy.ndimage import distance_transform_edt, map_coordinates
from scipy.spatial import cKDTree
from shapely.geometry import LineString, Polygon
from shapely.ops import substring


def polygon_bng(polygons):
    return shapely.union_all([Polygon([(538900+x,183209-z) for x,z in p[0]],
        [[(538900+x,183209-z) for x,z in ring] for ring in p[1:]]) for p in polygons])


def continuous_profile(stations, levels, query, length, closed=False):
    """Linear along-feature interpolation, with no radius cut-off islands."""
    order=np.argsort(stations);stations=np.asarray(stations)[order];levels=np.asarray(levels)[order]
    unique=np.unique(stations)
    values=np.array([np.median(levels[stations==s]) for s in unique])
    if closed:
        return np.interp(np.mod(query,length),np.r_[unique[-1]-length,unique,unique[0]+length],np.r_[values[-1],values,values[0]])
    return np.interp(query,unique,values)


class Banks:
    def __init__(self,network,audit,config):
        self.config=config
        self.water=shapely.union_all([polygon_bng(r['polygons']) for r in network['reaches']])
        self.openings=shapely.union_all([LineString([(538900+x,183209-z) for x,z in l]) for l in network['bankSections']['openBoundaries']])
        shore=self.water.boundary.difference(self.openings.buffer(.05))
        self.lines=[l for l in shapely.get_parts(shapely.line_merge(shore)) if l.length>1]
        self.tree=shapely.STRtree(self.lines)
        segments=[];parents=[];starts=[]
        for j,line in enumerate(self.lines):
            coords=np.array(line.coords);lengths=np.linalg.norm(np.diff(coords,axis=0),axis=1)
            segments.extend(np.stack([coords[:-1],coords[1:]],axis=1));parents.extend([j]*len(lengths));starts.extend(np.r_[0,np.cumsum(lengths)[:-1]])
        self.segments=shapely.linestrings(np.array(segments));self.segment_tree=shapely.STRtree(self.segments)
        self.segment_parents=np.array(parents);self.segment_starts=np.array(starts)
        self.controls=[[] for l in self.lines]
        for r in audit['records']:
            if r['type']!='spot' or r['confidence']!='high' or r['disputed'] or r.get('setting_conflict'):continue
            if r['surfaceFamily'] not in ('wall','bank-or-embankment') or r['setting'] not in ('wall_top','embankment_top'):continue
            p=shapely.Point(r['positionBNG']);j=int(self.tree.nearest(p));line=self.lines[j]
            if line.distance(p)>config['bankObservationMatchMetres']:continue
            self.controls[j].append({**r,'chainageMetres':line.project(p)})
        accepted=[r for records in self.controls for r in records]
        assert accepted,'No bank-top controls available'
        self.regional_tree=cKDTree([r['positionBNG'] for r in accepted])
        self.regional_values=np.array([r['provisionalODNMetres'] for r in accepted])
        self.accepted_ids=sorted({r['id'] for r in accepted})
        self.metadata=[]
        for j,(line,records) in enumerate(zip(self.lines,self.controls)):
            stations=[r['chainageMetres'] for r in records]
            self.metadata.append({'id':f'bank-{j:03d}','lengthMetres':line.length,'closed':line.is_ring,
                'routeBNG':list(shapely.simplify(line,.15).coords),
                'controls':[{'id':r['id'],'chainageMetres':r['chainageMetres'],'heightODNMetres':r['provisionalODNMetres']} for r in records],
                'heightMethod':'along-bank interpolation and endpoint continuation' if records else 'inferred regional crest continuation; no direct reading on this component',
                'largestUnanchoredIntervalMetres':max(np.diff(sorted(stations)+[line.length]).tolist()+[min(stations)]) if stations else line.length})

    def crest(self,xy):
        points=shapely.points(xy);segments=self.segment_tree.nearest(points);indices=self.segment_parents[segments];values=np.empty(len(xy))
        for j in np.unique(indices):
            selected=indices==j;line=self.lines[j];records=self.controls[j]
            if records:
                near=segments[selected];chain=self.segment_starts[near]+shapely.line_locate_point(self.segments[near],points[selected])
                values[selected]=continuous_profile([r['chainageMetres'] for r in records],
                    [r['provisionalODNMetres'] for r in records],chain,line.length,line.is_ring)
            else:
                # All accepted crests contribute continuously; no switch in
                # nearest-k membership introduces a step on an unsampled bank.
                p=xy[selected];num=np.zeros(len(p));den=np.zeros(len(p))
                for q,v in zip(self.regional_tree.data,self.regional_values):
                    d=((p-q)**2).sum(axis=1);w=1/(d+200**2)**2
                    num+=w*v;den+=w
                values[selected]=num/den
        return values


def add_continuous_structures(height,kind,ground,east,north,exclusions,network,
                              audit,infrastructure,sewer,datum,config,out):
    shape=height.shape;step=float(east[0,1]-east[0,0]);e0=east[0,0]-step/2;n1=north[0,0]+step/2
    bounds=[e0,n1-shape[0]*step,e0+shape[1]*step,n1]
    cx=(bounds[0]+bounds[2])/2;cn=(bounds[1]+bounds[3])/2
    window=shapely.box(*bounds);xy=np.column_stack([east.ravel(),north.ravel()])
    valid=np.isfinite(ground);nearest=distance_transform_edt(~valid,return_distances=False,return_indices=True)
    filled=ground[tuple(nearest)]
    def sample(points):
        rc=np.array([(n1-points[:,1])/step-.5,(points[:,0]-e0)/step-.5])
        return map_coordinates(filled,rc,order=1,mode='nearest')
    positions=[];categories=[];features=[];vertex_count=0
    def emit(name,category,area,level,bands,source_ids,method,deck=False):
        nonlocal vertex_count
        area=area.intersection(window)
        if not deck:area=area.difference(exclusions)
        if area.is_empty:return
        print('  continuous structure:',name,flush=True)
        # Raster samples use exactly this continuous profile, never a dot radius.
        mask=valid.ravel()&shapely.contains_xy(area,xy[:,0],xy[:,1])
        cells=np.flatnonzero(mask)
        if not deck and len(cells):
            values=level(xy[cells]);take=values>=height.ravel()[cells]-1e-6
            height.ravel()[cells[take]]=values[take];kind.ravel()[cells[take]]=category
        start=vertex_count;pieces=[]
        for band in bands:
            a=shapely.segmentize(band.intersection(area),config['shoreSamplingMetres'])
            if a.is_empty:continue
            triangles=shapely.get_parts(shapely.constrained_delaunay_triangles(a))
            triangles=triangles[shapely.area(triangles)>1e-7]
            if not len(triangles):continue
            coords=shapely.get_coordinates(triangles).reshape(-1,4,2)[:,:3,:].reshape(-1,2)
            unique,inverse=np.unique(coords,axis=0,return_inverse=True)
            z=level(unique)[inverse]
            vertices=np.column_stack([coords[:,0]-cx,z,cn-coords[:,1]])
            # Per-face vertices allow independently reviewed overlapping surfaces.
            pieces.append(vertices);vertex_count+=len(vertices)
        if pieces:
            vertices=np.concatenate(pieces);positions.append(vertices.astype('<f4'))
            categories.append(np.full(len(vertices),category,dtype='u1'))
        features.append({'name':name,'kind':category,'cells':0 if deck else int(mask.sum()),
            'sourceIds':source_ids,'method':method,'vertexStart':start,'vertexCount':vertex_count-start,
            'elevatedWaterCrossing':deck,'areaM2':area.area,
            'heightRangeODNMetres':[float(vertices[:,1].min()),float(vertices[:,1].max())] if pieces else [],
            'footprintGeoJSON':shapely.to_geojson(area)})

    banks=Banks(network,audit,config);width=config['bankBaseWidthMetres'];crest_width=config['bankCrestWidthMetres']
    guard=banks.openings.buffer(width+.1)
    area=banks.water.buffer(width).difference(banks.water).difference(guard)
    def bank_level(points):
        g=sample(points);pts=shapely.points(points);near=banks.segment_tree.nearest(pts);d=shapely.distance(pts,banks.segments[near])
        t=np.clip((width-d)/(width-crest_width),0,1)
        return g+t*np.maximum(0,banks.crest(points)-g)
    bands=[];previous=banks.water
    for distance in [3,6,10,width]:
        outer=banks.water.buffer(distance);bands.append(outer.difference(previous));previous=outer
    emit('Continuous river and canal banks',12,area,bank_level,bands,banks.accepted_ids,
         'Continuous union-shoreline profile; levels interpolate by along-bank chainage. Unanchored components use an explicitly inferred regional crest continuation. Confluences and source-window openings remain open.')

    rail_profiles=[]
    for rail in infrastructure['railways']:
        line=LineString([(538900+x,183209-z) for x,z in rail['route']]);half=rail.get('baseHalfWidth',15)
        crest=rail.get('crestHalfWidth',max(3,rail.get('tracks',1)*2))
        area=polygon_bng(rail['footprint']) if rail.get('footprint') else line.buffer(half)
        records=[r for r in audit['records'] if r['surfaceFamily']=='railway' and r['type']=='spot' and r['confidence']=='high' and not r['disputed'] and not r.get('setting_conflict') and r['id'] not in config.get('excludedRailwayControlIds',[]) and line.distance(shapely.Point(r['positionBNG']))<=half+8]
        stations=[line.project(shapely.Point(r['positionBNG'])) for r in records]
        levels=[r['provisionalODNMetres'] for r in records]
        fallback=rail['formationHeight']+datum['odnMinusSceneYMetres']
        source_stations=np.array(rail.get('stations',[]))
        if len(source_stations):
            fallback_stations=source_stations[:,5]
            fallback_levels=source_stations[:,2]+datum['odnMinusSceneYMetres']
        else:
            fallback_stations=np.array([0,line.length]);fallback_levels=np.array([fallback,fallback])
        def rail_crest(points):
            station=shapely.line_locate_point(line,shapely.points(points))
            return continuous_profile(stations,levels,station,line.length) if records else np.interp(station,fallback_stations,fallback_levels)
        def rail_level(points):
            g=sample(points);d=shapely.distance(shapely.points(points),line)
            weight=np.clip((half-d)/max(1,half-crest),0,1)
            return g+weight*np.maximum(0,rail_crest(points)-g)
        buffers=[line.buffer(d) for d in [crest,(crest+half)/2,half]]
        bands=[buffers[0],buffers[1].difference(buffers[0]),area.difference(buffers[1])]
        emit(rail['name'],13,area,rail_level,bands,[r['id'] for r in records],
             'Continuous formation profile along the mapped route. Direct railway readings interpolate by chainage without a distance cut-off; no readings means the existing interpreted station grades, including graded junction connections. Mapped water crossings remain openings in the earthwork.')
        bridge_areas=[substring(line,max(0,b['start']-1),min(line.length,b['end']+1)).buffer(crest,cap_style=2) for b in rail.get('bridges',[])]
        crossing=shapely.union_all([line.buffer(crest,cap_style=2).intersection(banks.water),*bridge_areas])
        emit(rail['name']+' — bridge spans',15,crossing,rail_crest,[crossing],[r['id'] for r in records],
             'Raised railway deck over mapped water and explicit bridge intervals; visual cover only, excluded from ground raster and hydraulic barriers.',deck=True)
        rail_profiles.append({'name':rail['name'],'routeBNG':list(line.coords),'lengthMetres':line.length,
            'controlIds':[r['id'] for r in records],'stationsMetres':stations,'levelsODNMetres':levels,'fallbackODNMetres':fallback,'bridgeIntervals':rail.get('bridges',[]),'existingGradeStationsMetres':fallback_stations.tolist(),
            'existingGradeODNMetres':fallback_levels.tolist()})

    line=LineString([(538900+x,183209-z) for x,z in sewer['route']]);half=sewer['baseWidth']/2;crest=sewer['crestWidth']/2
    crossing=infrastructure['sewerHighStreet'];crossxy=np.array([538900+crossing['centre'][0],183209-crossing['centre'][1]])
    def sewer_crest(points):
        d=np.linalg.norm(points-crossxy,axis=1);t=np.clip((d-12)/crossing['sewerApproachLength'],0,1)
        return crossing['surfaceHeight']+(sewer['height']-crossing['surfaceHeight'])*t*t*(3-2*t)+datum['odnMinusSceneYMetres']
    def sewer_level(points):
        g=sample(points);d=shapely.distance(shapely.points(points),line)
        weight=np.clip((half-d)/(half-crest),0,1)
        return g+weight*np.maximum(0,sewer_crest(points)-g)
    buffers=[line.buffer(d,join_style=2) for d in [crest,(crest+half)/2,half]]
    bands=[buffers[0],buffers[1].difference(buffers[0]),buffers[2].difference(buffers[1])]
    emit('Northern Outfall Sewer — full crest and banks',13,buffers[2],sewer_level,bands,[],
         'Continuous full-width sewer cover and side slopes on the existing centreline, including inferred end extension. Existing smooth High Street cover profile retained; no sewer invert inferred.')
    spans=buffers[0].intersection(banks.water)
    emit('Northern Outfall Sewer — water spans',15,spans,sewer_crest,[spans],[],
         'Continuous elevated sewer cover over mapped rivers. Separate deck geometry, not a ground fill or hydraulic barrier.',deck=True)
    vertices=np.concatenate(positions);kinds=np.concatenate(categories)
    vertices.tofile(out/'landscape-1900.structures.f32');kinds.tofile(out/'landscape-1900.structure-kind.u8')
    return {'features':features,'usedSourceIds':sorted({i for f in features for i in f['sourceIds']}),
        'bankProfiles':banks.metadata,'railProfiles':rail_profiles,
        'sewerProfile':{'routeBNG':list(line.coords),'lengthMetres':line.length,'crestWidthMetres':sewer['crestWidth'],
                        'nominalCrestODNMetres':sewer['height']+datum['odnMinusSceneYMetres'],
                        'highStreetCoverODNMetres':crossing['surfaceHeight']+datum['odnMinusSceneYMetres']},
        'fineMesh':{'positionFile':'landscape-1900.structures.f32','kindFile':'landscape-1900.structure-kind.u8',
            'vertexCount':len(vertices),'triangleCount':len(vertices)//3,'maximumShoreSegmentMetres':config['shoreSamplingMetres'],
            'coordinates':'Non-indexed triangles: east minus region centre, provisional ODN metres, region northing centre minus northing. Float32 little endian.',
            'originBNG':[cx,cn],'elevatedCrossingKind':15},
        'policy':config}
