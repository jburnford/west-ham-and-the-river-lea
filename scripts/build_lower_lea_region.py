"""Build a regional coverage/topology review, not a calibrated historical DEM."""
import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image
from pyproj import Transformer
from shapely import make_valid, union_all
from shapely.geometry import Polygon, box, shape
from shapely.ops import transform, nearest_points

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'data/maps/lower-lea-region'
RESEARCH=ROOT/'reference/topography-research-2026-09-28'
OUT=ROOT/'docs/data/lower-lea-region'


def polygons(g):
    if g.geom_type=='Polygon': return [g]
    return [p for part in getattr(g,'geoms',[]) for p in polygons(part)]


def rings(g):
    return [[[list(c) for c in r.coords] for r in [p.exterior,*p.interiors]] for p in polygons(g)]


def build():
    OUT.mkdir(parents=True,exist_ok=True)
    config=json.loads((SOURCE/'config.json').read_text())
    bounds=config['reviewBoundsBNG'];region=box(*bounds)
    project=Transformer.from_crs(4326,27700,always_xy=True).transform
    paths=[SOURCE/'config.json',SOURCE/'sources.json']
    layers={};repairs=[];nodes=[];geoms=[]
    for name in ['Lower_River_Lea','Water_1895','Water_First_Series','TQ_TidalWater']:
        path=SOURCE/'sources'/f'{name}.geojson';paths.append(path)
        features=json.loads(path.read_text())['features'];rows=[]
        for index,f in enumerate(features):
            if not f.get('geometry'): continue
            original=transform(project,shape(f['geometry']))
            if original.is_empty or not original.envelope.intersects(region): continue
            # Overlapping water polygon parts are a union of water coverage.
            # Repairing an invalid MultiPolygon as one object can turn overlap
            # into an artificial dry hole. Repair parts first, then union them.
            valid=union_all([p for part in polygons(original) for p in polygons(make_valid(part))]) if not original.is_valid else original
            area_before=original.area
            if not original.is_valid:
                repairs.append({'source':name,'index':index,'sourceObjectId':f['properties'].get('OBJECTID'),
                    'originalAreaM2':area_before,'repairedAreaM2':valid.area,
                    'areaChangeM2':valid.area-area_before,'method':'make_valid on individual polygon parts, then union of water coverage on projected copy',
                    'needsMapReview':True})
            clipped=valid.intersection(region)
            if not polygons(clipped): continue
            props=f['properties'];identifier=f'{name}-{index}'
            row={'id':identifier,'sourceIndex':index,'sourceProperties':props,
                 'name':props.get('Name') or props.get('Type') or 'Unnamed water feature',
                 'type':props.get('Type'),'polygons':rings(clipped),
                 'periodStatus':'source attribution, not independently verified',
                 'hydraulicStatus':'unreviewed','repaired':not original.is_valid}
            rows.append(row)
            if name=='Lower_River_Lea':
                for part,g in enumerate(polygons(clipped)):
                    nodes.append({'id':f'{identifier}-part-{part}','reachId':identifier,'name':row['name'],
                        'areaM2':g.area,'boundsBNG':list(g.bounds)})
                    geoms.append(g)
        layers[name]=rows
    contacts=[];near=[];parents=list(range(len(nodes)))
    def root(i):
        while parents[i]!=i: i=parents[i]
        return i
    for a in range(len(nodes)):
        for b in range(a+1,len(nodes)):
            distance=geoms[a].distance(geoms[b])
            if distance>config['nearConnectionMetres']:continue
            pa,pb=nearest_points(geoms[a],geoms[b])
            pair={'a':nodes[a]['id'],'b':nodes[b]['id'],'distanceMetres':distance,
                  'routeBNG':[list(pa.coords[0]),list(pb.coords[0])],
                  'hydraulicStatus':'unreviewed — map geometry alone does not establish passage'}
            if distance<=config['contactToleranceMetres']:
                pair['overlapAreaM2']=geoms[a].intersection(geoms[b]).area
                contacts.append(pair);parents[root(b)]=root(a)
            else:near.append(pair)
    components={}
    for i,node in enumerate(nodes):components.setdefault(root(i),[]).append(node['id'])
    topology={'nodes':nodes,'contacts':contacts,'nearConnections':near,'components':list(components.values()),
              'policy':'Components describe geometric contact only; no flow direction or open/closed gate state inferred.'}

    # Keep map continuity separate from hydraulic passage. Controls can also
    # occur inside one polygon, so a join audit cannot replace the site register.
    review_path=SOURCE/'connection-review.json';paths.append(review_path)
    review=json.loads(review_path.read_text())
    for source in review['sources'].values():
        paths.append(ROOT/source['path'])
    navigation=set(review['navigationReachIds'])
    by_id={n['id']:n for n in nodes}
    overrides={frozenset((r['a'],r['b'])):r for r in review['connectionReviews']}
    found=set()
    for pair in contacts+near:
        key=frozenset((pair['a'],pair['b']))
        ra,rb=(by_id[pair[k]]['reachId'] for k in ['a','b'])
        crossing=(ra in navigation)!=(rb in navigation)
        pair['navigationInterface']=crossing
        pair['reviewCategory']='navigation-interface-review' if crossing else 'unreviewed-contact'
        pair['reviewNote']='Navigation interface: establish the actual passage and any control; do not assume either unrestricted flow or a closed gate.' if crossing else 'Map contact alone does not establish hydraulic passage.'
        if key in overrides:
            assert not crossing or overrides[key]['category']=='mapped-navigation-junction', 'Navigation continuity requires explicit junction evidence'
            pair['reviewCategory']=overrides[key]['category']
            pair['reviewNote']=overrides[key]['note'];found.add(key)
            pair['evidence']=overrides[key].get('evidence',[])
        pair['hydraulicPassage']=None
    assert found==set(overrides), 'Connection review references a missing pair'
    topology['provisionalContinuityLinks']=[{'a':p['a'],'b':p['b']} for p in near if p['reviewCategory']=='provisional-mapping-seam']
    review['navigationInterfaces']=[p for p in contacts+near if p['navigationInterface']]
    geometry_by_id={n['id']:g for n,g in zip(nodes,geoms)}
    for route in review['structureRoutes']:
        ga,gb=(geometry_by_id[route[k]] for k in ['a','b'])
        pa,pb=nearest_points(ga,gb)
        route['distanceMetres']=ga.distance(gb)
        route['routeBNG']=[list(pa.coords[0]),list(pb.coords[0])]
        route['hydraulicPassage']=None
        route['schematic']=True
        ra,rb=(by_id[route[k]]['reachId'] for k in ['a','b'])
        if (ra in navigation)!=(rb in navigation):
            review['navigationInterfaces'].append({**route,'navigationInterface':True,
                'reviewCategory':'mapped-lock-passage','reviewNote':route['note']})
    review['counts']={'provisionalMappingSeams':len(topology['provisionalContinuityLinks']),
        'navigationInterfaces':len(review['navigationInterfaces']),'controlSites':len(review['controlSites']),
        'structureRoutes':len(review['structureRoutes']),
        'mappedNavigationJunctions':sum(p['reviewCategory']=='mapped-navigation-junction' for p in contacts+near)}

    # Snapshot height candidates separately so an ongoing transcription cannot
    # silently change this review. Refresh is an explicit source update.
    height_path=SOURCE/'height-observations.snapshot.geojson'
    if not height_path.exists():
        height_path.write_bytes((ROOT/'reference/spot-heights/heights.geojson').read_bytes())
    paths.append(height_path)
    observations=json.loads(height_path.read_text())['features']
    surface_path=SOURCE/'height-surface-review-1900.json';paths.append(surface_path)
    surface_review=json.loads(surface_path.read_text())
    assert surface_review['sourceSnapshotSHA256']==hashlib.sha256(height_path.read_bytes()).hexdigest()
    surface_by_id={r['id']:r for r in surface_review['observations']}
    assert len(surface_by_id)==len(surface_review['observations'])
    # New direct readings live beside, never inside, the frozen transcription.
    supplement_path=SOURCE/'height-observations.additional.geojson';paths.append(supplement_path)
    supplement=json.loads(supplement_path.read_text())['features']
    original_ids={f['properties']['id'] for f in observations}
    extra_ids=[f['properties']['id'] for f in supplement]
    assert len(set(extra_ids))==len(extra_ids) and not original_ids.intersection(extra_ids)
    assert set(extra_ids)<=surface_by_id.keys(),'Additional readings need direct map reviews'
    observations=observations+supplement
    for row in surface_by_id.values():
        for key in ['mosaic','registration','detailCrop']:paths.append(ROOT/row[key])
        assert hashlib.sha256((ROOT/row['mosaic']).read_bytes()).hexdigest()==row['mosaicSHA256']
    terrain_meta_path=ROOT/'docs/data/terrain-1900.json';paths.append(terrain_meta_path)
    historic=json.loads(terrain_meta_path.read_text());approved={c['id'] for c in historic['controls']}
    marks=[]
    for f in observations:
        p=f['properties'];e,n=p.get('bng_e'),p.get('bng_n')
        if e is None or n is None or not region.covers(shape({'type':'Point','coordinates':[e,n]})):continue
        marks.append({k:p.get(k) for k in ['id','type','value_ft','confidence','setting','disputed','setting_conflict','layer','survey_dates','datum']}|
                     {'positionBNG':[e,n],'appliedFieldControl':p['id'] in approved,
                      'observationSource':p.get('observationSource',str(height_path.relative_to(ROOT)))})
        if p['id'] in surface_by_id:
            row=surface_by_id[p['id']]
            assert p['value_ft']==row['expectedValueFeet'] and p['type']==row['sourceType']
            marks[-1].update(setting=row['setting'],positionBNG=row['positionBNG'],
                setting_conflict=False,surfaceReview=row,sourceSetting=p['setting'],
                sourceSettingConflict=p.get('setting_conflict',False))
    assert surface_by_id.keys() <= {m['id'] for m in marks}
    # Crop the existing research raster exactly on its native 10m lattice. Missing
    # cells remain NaN; neither height observations nor modern terrain fill them.
    meta_path=RESEARCH/'early-terrain-2003-10m.json';paths.append(meta_path)
    meta=json.loads(meta_path.read_text());raster_path=RESEARCH/meta['heightFile'];paths.append(raster_path)
    full=np.fromfile(raster_path,dtype='<f4').reshape(meta['height'],meta['width'])
    step=meta['cellSizeMetres'];assert step==config['cellSizeMetres']
    e0,n0,e1,n1=bounds;se0,sn0,se1,sn1=meta['boundsBNG']
    assert all(v%step==0 for v in [e0-se0,e1-se0,sn1-n0,sn1-n1])
    assert se0<=e0<e1<=se1 and sn0<=n0<n1<=sn1
    crop=full[(sn1-n1)//step:(sn1-n0)//step,(e0-se0)//step:(e1-se0)//step].copy()
    crop.astype('<f4').tofile(OUT/'terrain-2003.f32')
    valid=np.isfinite(crop);valid.astype('u1').tofile(OUT/'terrain-valid.u8')
    stops=np.array([-2,0,2,5,10,20,35]);colours=np.array([[92,122,123],[133,164,146],[176,188,145],[210,202,164],[189,161,126],[151,126,104],[229,221,199]])
    rgb=np.stack([np.interp(np.nan_to_num(crop),stops,colours[:,k]) for k in range(3)],axis=-1)
    gy,gx=np.gradient(np.nan_to_num(crop),step)
    neighbours=valid & np.roll(valid,1,0)&np.roll(valid,-1,0)&np.roll(valid,1,1)&np.roll(valid,-1,1)
    shade=np.where(neighbours,np.clip(1-.7*gx+.5*gy,.65,1.12),1)
    rgb=np.clip(rgb*shade[:,:,None],0,255).astype('u1');rgb[~valid]=[226,224,215]
    Image.fromarray(rgb).save(OUT/'terrain-2003.png')
    bx0,bz0,bx1,bz1=json.loads((ROOT/'docs/data/landscape-flood-1900.json').read_text())['bounds']
    paths.append(ROOT/'docs/data/landscape-flood-1900.json')
    current_bounds=[538900+bx0,183209-bz1,538900+bx1,183209-bz0]
    core_network_path=ROOT/'docs/data/river-network.json';paths.append(core_network_path)
    core_connections=json.loads(core_network_path.read_text()).get('reviewedConnections',{})
    result={**config,'schemaVersion':1,'coordinateSystem':'EPSG:27700; metres; north-up',
            'coreIntegration':{'connections':[r['id'] for r in core_connections.get('connections',[])],
                'status':'Reviewed local passages applied to core terrain and water surfaces; dynamic capacities remain uncalibrated',
                'pendingRegionalRoutes':core_connections.get('pendingRegionalRoutes',[])},
            'layers':layers,'repairs':repairs,'topology':topology,'heightMarks':marks,'connectionReview':review,
            'heightSurfaceReview':{'source':str(surface_path.relative_to(ROOT)),
                'reviewedMarks':len(surface_by_id),'appliedToTerrain':False},
            'currentFloodBoundsBNG':current_bounds,
            'terrain':{'date':'2003','historicalDEM':False,'width':crop.shape[1],'height':crop.shape[0],
                'cellSizeMetres':step,'orientation':'rows north to south, cell centres',
                'heightFile':'terrain-2003.f32','validMaskFile':'terrain-valid.u8','preview':'terrain-2003.png',
                'validAreaPercent':round(float(valid.mean()*100),2),'missingCells':int((~valid).sum()),
                'minimumODN':float(crop[valid].min()),'maximumODN':float(crop[valid].max()),
                'attribution':'Environment Agency LiDAR, Open Government Licence',
                'limitations':'2003 relief includes later earthworks. River water returns are not bathymetry. Gaps stay missing; no historical controls applied in this preview.'},
            'summary':{'reviewAreaKm2':region.area/1e6,'primaryReaches':len(layers['Lower_River_Lea']),
                'polygonParts':len(nodes),'geometricComponents':len(components),'nearConnections':len(near),
                'heightMarks':len(marks),'settings':dict(Counter(m['setting'] for m in marks)),
                'appliedFieldControls':sum(m['appliedFieldControl'] for m in marks)},
            'nextWork':['Review northern and Thames endpoint coverage against period sheets',
                'Resolve near-connections and locate locks, mills, gates and weirs',
                'Review historical ground, street and bank controls separately',
                'Correct later earthworks before using this regional relief for c1900 flooding',
                'Choose hydraulic margins from relief and flood routes, not this review rectangle'],
            'inputHashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    (OUT/'index.json').write_text(json.dumps(result,separators=(',',':'))+'\n')
    print(json.dumps(result['summary'],indent=2));print(f'Valid 2003 terrain in review window: {result["terrain"]["validAreaPercent"]}%')


if __name__=='__main__':build()
