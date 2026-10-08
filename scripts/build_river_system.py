"""Extend the actual scene's waterways; do not expand its flood experiment.

Period source polygons, explicit crossing records and map-pixel traces remain
separate, with no automatic conversion of geometric contact to hydraulic flow.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
import shapely
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import nearest_points, transform
from factory_map_sources import mosaic
from build_lower_lea_region import polygons, rings
from river_bank_sections import build_banks
from regional_marsh_surface import MarshSurface, TerrainSurfaces
import tide_levels as tl
from back_river_profile import profile as back_river_profile, INPUTS as back_inputs

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'docs/data'
REVIEW = ROOT/'reference/lower-lea-connection-review'


def geometry(parts):
    return shapely.union_all([Polygon(p[0], p[1:]) for p in parts])


def build():
    paths = []
    def read(path):
        path = ROOT/path; paths.append(path)
        return json.loads(path.read_text())
    config = read('data/maps/lower-lea-region/river-system-1900.json')
    sections = read('data/maps/lower-lea-region/bank-sections-1900.json')
    waterworks_config=read('data/maps/lower-lea-region/waterworks-margin-surface-1900.json')
    shore_review=waterworks_config['shorelineReview']
    registration=read(shore_review['registration'])
    paths.append(ROOT/shore_review['mosaic'])
    from spot_height_mosaics import pixel_to_coords
    coords=[pixel_to_coords(registration,*p) for p in shore_review['landExclusionPixels']]
    shore_land=Polygon([(p['bng_e']-538900,183209-p['bng_n']) for p in coords])
    assert shore_land.is_valid
    region = read('docs/data/lower-lea-region/index.json')
    core = read('docs/data/river-network.json')
    plan = read('docs/data/ground-plan.json')
    west = read('data/maps/factory-west-context.json')
    terrain = read('docs/data/river-terrain.json')
    elevation = read('docs/data/terrain-1900.json')
    panels = read('reference/lower-lea-connection-review/river-system-panels.json')
    paths.extend(ROOT/p['path'] for p in panels.values())
    six = read('reference/lower-lea-connection-review/six-inch-review.json')
    panels['six-inch-south'] = {
        'boundsBNG': six['areas']['six-inch-south']['requestedBoundsBNG'],
        'zoom': six['areas']['six-inch-south']['zoom'],
        'path': 'reference/lower-lea-connection-review/six-inch-south.png'}
    # Cache-based georeferencing gives the original XYZ transform, not a hand
    # fitted affine approximation. Every trace keeps the native pixel vertices.
    worlds = {}
    for name in {t['panel'] for t in config['traces']} | {'six-inch-south'}:
        p = panels[name]; e0,n0,e1,n1 = p['boundsBNG']
        _, world, _ = mosaic((e0-538900,183209-n1,e1-538900,183209-n0),
                             zoom=p['zoom'],layer='os-six-inch-2nd')
        worlds[name] = world; paths.append(ROOT/p['path'])

    local = lambda g: transform(lambda e,n: (np.asarray(e)-538900,183209-np.asarray(n)), g)
    current_by_id = {}
    for row in plan['rivers']+west['rivers']:
        key = row['id']-10000 if 10000 <= row['id'] < 11000 else row['id']
        current_by_id.setdefault(key,[]).append(geometry(row['polygons']))
    current_by_id = {k:shapely.union_all(v) for k,v in current_by_id.items()}
    geoms = {}; reaches = []
    def add(identifier, name, g, role, provenance):
        assert g.is_valid and not g.is_empty, identifier
        geoms[identifier] = g
        reaches.append({'id':identifier,'name':name,'role':role,'polygons':rings(g),
                        'provenance':provenance,'capacity':None,'gateState':None})
    for row in region['layers']['Lower_River_Lea']:
        g = local(geometry(row['polygons']))
        if row['sourceIndex'] in current_by_id:
            corrected = current_by_id[row['sourceIndex']]
            g = g.difference(box(*corrected.bounds)).union(corrected)
        provenance={'layer':'Lower_River_Lea','sourceIndex':row['sourceIndex']}
        if row['id']==shore_review['reachId']:
            removed=g.intersection(shore_land);g=g.difference(shore_land)
            assert 0<removed.area<shore_review['maximumRemovedAreaM2']
            provenance['shorelineReview']={'source':'data/maps/lower-lea-region/waterworks-margin-surface-1900.json',
                'removedAreaM2':removed.area,'removedPolygons':rings(removed),'method':shore_review['method']}
        add(row['id'],row['name'],g,
            'navigation' if row['sourceIndex'] in [18,22] else 'river',
            provenance)
    supplementary = {r['sourceIndex']:r for r in region['layers']['Water_1895']}
    for group in config['supplementaryReaches']:
        for key in group['sourceIndices']:
            row = supplementary[key]
            add(row['id'],group['name'],local(geometry(row['polygons'])),group['role'],
                {'layer':'Water_1895','sourceIndex':key,'review':'six-inch blue water'})

    crossings = []
    def end_centre(g, p, q):
        # The middle of g's cross-section 1 m inside its end at p, across the direction p->q.
        u = np.subtract(q, p)/max(np.linalg.norm(np.subtract(q, p)), 1e-9); n = np.array([-u[1], u[0]])
        c = np.subtract(p, u)
        chord = g.intersection(LineString([c-200*n, c+200*n]))
        parts = [x for x in getattr(chord, 'geoms', [chord]) if x.geom_type == 'LineString' and not x.is_empty]
        if not parts: return np.asarray(p, float)
        best = min(parts, key=lambda x: x.distance(Point(c)))
        return np.asarray(best.interpolate(.5, normalized=True).coords[0])
    def passage(identifier, a, b, width, category, evidence, note='', centreline=False):
        pa,pb = nearest_points(geoms[a],geoms[b])
        route = [list(pa.coords[0]),list(pb.coords[0])]
        if centreline:
            # A channel cut in two by the source (the Hackney Cut under the Victoria Park branch): the passage runs
            # between the middles of the two facing ends, not between their nearest corners (which set it 12 m east).
            ca, cb = np.asarray(route[0]), np.asarray(route[1])
            for _ in range(3):
                ca, cb = end_centre(geoms[a], ca, cb), end_centre(geoms[b], cb, ca)
            # Each end reaches 1 m into its piece so the passage overlaps both.
            route = [ca.tolist(), cb.tolist()]
        g = LineString(route).buffer(width/2)
        add(identifier,identifier,g,'passage',{'evidence':evidence})
        crossings.append({'id':identifier,'a':a,'b':b,'widthMetres':width,
                          'category':category,'route':route,'capacity':None,
                          'gateState':None,'note':note,'evidence':evidence})
    for row in config['mappedCrossings']:
        passage(f"crossing-{row['a']}-{row['b']}",f"Water_1895-{row['a']}",
                f"Water_1895-{row['b']}",row['width'],row['category'],row['evidence'],row.get('note',''),row.get('centreline',False))
    for pair in region['topology']['nearConnections']:
        # Only previously reviewed mapping seams / mill / weir openings.
        category = pair['reviewCategory']
        if category not in {'provisional-mapping-seam','mapped-navigation-junction','mill-site-review','mapped-weir-review','channel-junction-review'}:
            continue
        # Parts refer to the same source reach in two Bow Creek seams.
        a,b = pair['a'].rsplit('-part-',1)[0],pair['b'].rsplit('-part-',1)[0]
        route = [[e-538900,183209-n] for e,n in pair['routeBNG']]
        identifier = 'regional-'+pair['a']+'-'+pair['b']
        width = 3
        add(identifier,identifier,LineString(route).buffer(width/2),'passage',{'evidence':pair['reviewNote']})
        crossings.append({'id':identifier,'a':a,'b':b,'category':category,'route':route,
                          'widthMetres':width,'capacity':None,'gateState':None})
    for row in core['reviewedConnections']['connections']:
        add('core-'+row['id'],row['id'],geometry(row['polygons']),'passage',{'evidence':'reviewed reconciled core passage'})
    for row in config['traces']:
        route = worlds[row['panel']](row['pixels'])
        # Explicit endpoints can be corrected to their source banks, but only
        # over a short map-registration discrepancy; record each correction.
        snaps = []
        for key in row['joins']:
            g = geoms[key]
            if g.intersects(LineString(route).buffer(row['width']/2)): continue
            distances = [Point(route[i]).distance(g) for i in [0,-1]]
            endpoint = 0 if distances[0] < distances[1] else -1
            point = nearest_points(Point(route[endpoint]),g)[1]
            distance = min(distances)
            assert distance < 25, (row['id'],key,distance)
            snaps.append({'reach':key,'distanceMetres':distance})
            route = np.vstack([point.coords[0],route]) if endpoint == 0 else np.vstack([route,point.coords[0]])
        add(row['id'],row['name'],LineString(route).buffer(row['width']/2),row['role'],
            {'panel':row['panel'],'nativePixels':row['pixels'],'endpointAdjustments':snaps,'note':row['note']})
        crossings.append({'id':row['id'],'category':row['category'],'route':route.tolist(),
            'widthMetres':row['width'],'capacity':None,'gateState':None,'joins':row['joins']})
    t = config['thamesContext']
    g = Polygon(worlds[t['panel']](np.asarray(t['pixels'])+t['cropOrigin']))
    add('thames-mouth-context','Thames at the Bow Creek mouth',g,'estuary',{'panel':t['panel'],'note':t['note']})

    # Bow Creek is tidal to the Thames (author, 5 October 2026): its regional reach, the
    # Thames mouth and the seams between its parts take the tide (data/maps/os-tide-levels.json).
    tidal_ids=[r['id'] for r in reaches if r['id'] in ('Lower_River_Lea-0','thames-mouth-context')
               or r['id'].startswith('regional-Lower_River_Lea-0-') or r['id']=='core-seam-Lower_River_Lea-0-part-1-Lower_River_Lea-0-part-2']
    # The silted back rivers are tidal up to where they leave the Old Lea and the Navigation
    # (data/maps/back-river-beds.json, scripts/back_river_profile.py): their regional reaches and the
    # passages between them, every reach lying mostly in the back-river water.
    back=back_river_profile();paths.extend(ROOT/p for p in back_inputs)
    back_water=back.geometry.buffer(.5)
    tidal_ids+=[r['id'] for r in reaches if r['id'] not in tidal_ids and geoms[r['id']].intersection(back_water).area>.5*geoms[r['id']].area]
    tidal_water=shapely.union_all([geoms[k] for k in tidal_ids])
    # The locally corrected banks take precedence over the raw regional GIS.
    current = shapely.union_all([geometry(r['polygons']) for r in plan['rivers']+west['rivers']]+
                                [geometry(r['polygons']) for r in core['reviewedConnections']['connections']])
    protected = current.buffer(22).union(box(*terrain['bounds'])).union(box(*elevation['bounds']))
    full_water = shapely.union_all(list(geoms.values()))
    extension = full_water.difference(protected)
    # Preserve the detailed core wholesale. The overlap reaches the existing
    # water, while only the extra banks/bed require a new coarse terrain mesh.
    display_water = full_water.difference(current.buffer(.01))
    # The drawn regional water also leaves out every other surface the scene
    # draws as network water at the same level (docs/app.js): the tidal
    # polygons, marsh-ditch render polygons and terrain pools. The tidal
    # polygons reach past `current` into regional channels at junctions, where
    # two coplanar planes showed as straight seams. Only the drawn planes are
    # trimmed; display_water still sets the bed corrections and ground cuts, so
    # the beds under the trimmed areas stay covered by the network's water.
    pools=[Polygon([(x+rx*np.cos(i*np.pi/16),z+rz*np.sin(i*np.pi/16)) for i in range(33)])
           for x,z,rx,rz,*_ in terrain['pools']]
    network_water=shapely.union_all([current,geometry(core['tide']['polygons']),
        geometry([p for f in core['marshDitches']['features'] for p in f['renderPolygons']]),*pools])
    drawn_water=display_water.difference(network_water.buffer(.01))
    # Clipped to the channels: never outside the mapped reaches, whose edges
    # are the bank lines the regional bank sections are built from.
    assert drawn_water.difference(full_water).area<1e-6
    assert drawn_water.intersection(network_water).area<1e-6
    # Approach roads at the road-bridge deck ends (T18): where the drawn regional water runs on
    # past a deck end under the approach (the deck corners, cut for the pre-T13 road), the drawn
    # street, footway and deck-end footway surfaces of docs/data/infrastructure.json win within
    # 12 m beyond each route end. Only the drawn plane is trimmed, as above.
    approach_infrastructure=read('docs/data/infrastructure.json')
    approach_surfaces=shapely.union_all([Polygon(t) for t in sum(approach_infrastructure['roadSurfaces'].values(),[])
        +approach_infrastructure['shoulderTriangles']]+[Polygon([q[:2] for q in t]) for r in approach_infrastructure.get('deckEndFootways',[]) for t in r['triangles']])
    approach_zones=[]
    for bridge in approach_infrastructure['roadBridges']:
        r=bridge['route'];reach=bridge['width']/2+1.1
        for a,c in ((r[1],r[0]),(r[-2],r[-1])):
            length=float(np.hypot(c[0]-a[0],c[1]-a[1]));ux,uz=(c[0]-a[0])/length,(c[1]-a[1])/length
            at=lambda s,v:(c[0]+ux*s-uz*v,c[1]+uz*s+ux*v)
            approach_zones.append(Polygon([at(0,-reach),at(12,-reach),at(12,reach),at(0,reach)]))
    approach_cut=approach_surfaces.intersection(shapely.union_all(approach_zones)).buffer(.01,join_style='mitre')
    # Only the pieces that reach under an approach are cut, so the others keep their rings as before.
    kept=[]
    for piece in getattr(drawn_water,'geoms',[drawn_water]):
        if piece.intersection(approach_cut).area<1e-9:kept.append(piece);continue
        cut=piece.difference(approach_cut)
        kept.extend(g for g in getattr(cut,'geoms',[cut]) if g.geom_type=='Polygon' and g.area>1e-9)
    drawn_water=shapely.MultiPolygon(kept)
    # Remove artificial bank caps at the former clipped endpoints only. Keep
    # all existing buildings, bridge decks and sewer structure coordinates.
    network_path=OUT/core['positionFile'];paths.append(network_path)
    network_positions=np.fromfile(network_path,dtype='<f4').reshape(-1,3)
    caps=shapely.contains_xy(display_water,network_positions[:,0],network_positions[:,2])
    under_tide=shapely.contains_xy(tidal_water,network_positions[:,0],network_positions[:,2])
    # The silted back-river banks (river-network.json backRiverBeds, F2) stand above -0.7 at the
    # shoreline by design; where a regional outline runs just past the mapped one they are not caps.
    # They and the network vertices inside the back rivers' regional reaches (which carry the silted bed)
    # are not caps either, under the tide or not.
    near_silted=shapely.dwithin(back.geometry,shapely.points(network_positions[:,[0,2]]),1.5)
    core_bed_corrections=np.flatnonzero(caps & ~under_tide & (network_positions[:,1]>-.7) & ~near_silted).tolist()
    tidal_core_bed_corrections=np.flatnonzero(caps & under_tide & (network_positions[:,1]>tl.SEAM_BED) & ~near_silted).tolist()
    # But network vertices inside the silted water itself (back_river_profile, outside the network's own channels)
    # standing over its bed are the bank the network built round its channels' clipped ends at the old core edge:
    # they go down to the shared silted bed (the bed of the nearest silted cell where theirs lies just outside).
    iz,ix=back.cells(network_positions[:,0],network_positions[:,2])
    silted_bed=back.bed[back.nearest[0][iz,ix],back.nearest[1][iz,ix]]
    in_silted=caps&shapely.contains_xy(back.geometry,network_positions[:,0],network_positions[:,2])
    silted_caps=np.flatnonzero(in_silted&(network_positions[:,1]>silted_bed+.05))
    silted_core_bed_corrections=[[int(i),round(float(silted_bed[i]),3)] for i in silted_caps]
    # Source-window boundaries are openings, not physical banks. They are
    # registered in the same native map coordinates as the Thames trace.
    thames_points=worlds[t['panel']](np.asarray(t['pixels'])+t['cropOrigin'])
    open_cuts=[]
    for i,a in enumerate(t['pixels']):
        j=(i+1)%len(t['pixels']);b=t['pixels'][j]
        if (a[0]==b[0]==0) or (a[1]==b[1]==560):
            open_cuts.append(LineString([thames_points[i],thames_points[j]]))
    upstream=geoms['Water_1895-521']
    open_cuts.append(upstream.boundary.intersection(box(-5000,-3791.02,0,-3790.98)))
    # Keep existing built ground and road surfaces at their original levels.
    factories=read('docs/data/factory-buildings.json')
    housing=read('docs/data/housing-detail.json')
    infrastructure=read('docs/data/infrastructure.json')
    flat_ground=shapely.union_all([Polygon(b['footprint']) for b in factories['buildings']+housing['rows']]
        +[LineString(r['route']).buffer(r['width']/2) for r in infrastructure['roads']])
    marsh_config=read('data/maps/lower-lea-region/marsh-surface-1900.json')
    bank_config=read('data/maps/lower-lea-region/bank-margin-surface-1900.json')
    knobshill_config=read('data/maps/lower-lea-region/knobshill-ground-surface-1900.json')
    upper_waterworks_config=read('data/maps/lower-lea-region/waterworks-upper-bank-surface-1900.json')
    temple_config=read('data/maps/lower-lea-region/temple-mills-bank-path-1900.json')
    potters_config=read('data/maps/lower-lea-region/potters-ditch-ground-surface-1900.json')
    city_mill_config=read('data/maps/lower-lea-region/city-mill-ground-surface-1900.json')
    paths.extend(ROOT/city_mill_config['boundaryReview'][key] for key in ['mosaic','registration','detailCrop'])
    paths.extend(ROOT/potters_config['boundaryReview'][key] for key in ['mosaic','registration','detailCrop'])
    paths.extend(ROOT/knobshill_config['boundaryReview'][key] for key in ['mosaic','registration','detailCrop'])
    height_review=read('data/maps/lower-lea-region/height-surface-review-1900.json')
    datum=read('data/maps/terrain-epochs.json')['verticalReference']
    paths.append(ROOT/'scripts/regional_marsh_surface.py')
    marsh=TerrainSurfaces([MarshSurface(c,height_review,datum,full_water,geoms,protected,flat_ground,infrastructure['railways'])
        for c in [marsh_config,bank_config,knobshill_config,waterworks_config,upper_waterworks_config,temple_config,potters_config,city_mill_config]])
    p,ix,silt,cover,faces,face_uv,bank_envelope,bank_sections=build_banks(
        full_water,protected,reaches,geoms,sections,open_cuts,flat_ground,marsh=marsh,tidal=tidal_water,back=back)
    # Drawn tidal water moves with the network's tide; the rest stays still.
    tidal_drawn=drawn_water.intersection(tidal_water)
    still_drawn=drawn_water.difference(tidal_water)
    p.tofile(OUT/'river-system-1900.f32');ix.tofile(OUT/'river-system-1900.u32')
    silt.tofile(OUT/'river-system-1900.silt');cover.tofile(OUT/'river-system-1900.cover')
    faces.tofile(OUT/'river-system-1900.faces.f32');face_uv.tofile(OUT/'river-system-1900.face-uv.f32')
    # Cut the same added river corridors out of the flat placeholder floors.
    cut=bank_envelope.union(display_water)
    core_ground=geometry(elevation['replacementBaseGround']).difference(cut)
    regional_ground=box(-25000,-25000,25000,25000).difference(box(-2750,-2750,2750,2750).union(cut))
    # Graph is an inventory of contact; gate states/capacities deliberately null.
    contacts=[]
    for i,a in enumerate(reaches):
        for b in reaches[i+1:]:
            if geoms[a['id']].distance(geoms[b['id']]) < .05:
                contacts.append([a['id'],b['id']])
    meta={'epoch':'1900','status':'mapped network geometry; hydraulic operation uncalibrated',
          'reaches':reaches,'crossings':crossings,'contacts':contacts,
          'controlSites':region['connectionReview']['controlSites'],
          'waterPolygons':rings(still_drawn),'tidalWaterPolygons':rings(tidal_drawn),'tidalReachIds':tidal_ids,
          'tideLow':tl.LOW,'tideRegister':'data/maps/os-tide-levels.json','extensionPolygons':rings(extension),
          'baseGround':rings(core_ground),'regionalGround':rings(regional_ground),
          'positionFile':'river-system-1900.f32','indexFile':'river-system-1900.u32',
          'sedimentFile':'river-system-1900.silt','landcoverFile':'river-system-1900.cover',
          'faceFile':'river-system-1900.faces.f32','faceUVFile':'river-system-1900.face-uv.f32',
          'faceVertices':len(faces),'bankSections':bank_sections,
          'vertices':len(p),'triangles':len(ix)//3,'waterLevel':core['waterLevel'],
          'coreBedCorrections':core_bed_corrections,'siltedCoreBedCorrections':silted_core_bed_corrections,'tidalCoreBedCorrections':tidal_core_bed_corrections,'tidalCoreBedLevel':tl.SEAM_BED,
          'railwayGroundAdjustments':[row for surface in marsh.surfaces for row in surface.railway_adjustments()],
          'bounds':list(full_water.bounds),'corePreserved':True,'floodDomainChanged':False,
          'sectionAssumption':config['sectionAssumption'],'dateNote':config['dateNote'],
          'inputHashes':{str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}}
    (OUT/'river-system-1900.json').write_text(json.dumps(meta,separators=(',',':'))+'\n')
    print(f'Built {len(reaches)} mapped pieces, {len(crossings)} explicit passages; {len(ix)//3} extra terrain triangles.')


if __name__=='__main__':build()
