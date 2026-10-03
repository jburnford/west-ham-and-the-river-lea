"""Build the review scene's metric ground plan. Requires pyproj and shapely."""
import json
import math
import random
from pathlib import Path

from pyproj import Transformer
from shapely.geometry import shape, box, Polygon, Point, MultiPoint, LineString
from shapely.geometry.polygon import orient
from shapely.ops import transform, triangulate, unary_union
from shapely.affinity import rotate
from housing_frontages import split_at_streets

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = (538900, 183209)  # Historic England's approximate bridge grid reference
project = Transformer.from_crs(4326, 27700, always_xy=True).transform
SEWER_WATER_SETBACK = 1.5  # metres between drawn water and the earth bank; the end wall stands in it
SEWER_BANK_LATTICE = (2, 0)  # x, z phase (mod 12 m) of the bank sample grid
SEWER_ROAD_SETBACK = 1.5  # metres between street edge and bank; build_infrastructure.py used roads.buffer(1.5)


def drawn_water(result):
    """Water surfaces as docs/app.js and docs/river-system.js draw them.

    The tidal shelves, retained channels, ditches, pools and regional water are
    derived later (build_river_network.py, build_river_system.py) from this
    plan's rivers, not from the sewer, so the previous build's files are read
    here. Rerun this script after those builders change the water. Without
    them, fall back to the mapped rivers widened by the 5 m tidal shelf.
    """
    out = ROOT/'docs/data'
    rings = lambda polygons: [Polygon(p[0], p[1:]).buffer(0) for p in polygons]
    rivers = [p for f in result['rivers'] for p in f['polygons']]
    try:
        network = json.loads((out/'river-network.json').read_text())
        system = json.loads((out/'river-system-1900.json').read_text())
        west = json.loads((out/'factory-buildings.json').read_text())['westContext']['rivers']
        terrain = json.loads((out/'river-terrain.json').read_text())
    except FileNotFoundError:
        return unary_union(rings(rivers)).buffer(5)
    retained = set(network['retainedWaterChannelIds']) | set(network.get('isolatedWaterChannelIds') or [])
    shapes = rings(network['tide']['polygons'])
    shapes += rings([p for c in network['reviewedConnections']['connections'] if not c['tidalDisplay'] for p in c['polygons']])
    shapes += rings([p for f in result['rivers']+west if f['id'] in retained for p in f['polygons']])
    shapes += rings([p for f in network['marshDitches']['features'] for p in f['renderPolygons']])
    shapes += rings(system['waterPolygons'])
    shapes += [Polygon([(x+rx*math.cos(i*math.pi/16), z+rz*math.sin(i*math.pi/16)) for i in range(32)])
               for x, z, rx, rz in terrain.get('pools', [])]
    return unary_union(shapes)


def sewer_road_openings(line):
    """Street corridors the sewer banks are cut for, as docs/data/infrastructure.json
    traces them (the road list there is assembled from several trace files).

    The routes and widths do not depend on the sewer, so the previous build's
    file is read here, as drawn_water() reads the water. Paths stay buried, as
    before, and Stratford High Street keeps its enclosed-sewer treatment in
    build_infrastructure.py. Returns {name: (route record, corridor)}.
    """
    try:
        roads = json.loads((ROOT/'docs/data/infrastructure.json').read_text())['roads']
        high_street = json.loads((ROOT/'data/maps/sewer-high-street.json').read_text())['crossing']['road']
    except FileNotFoundError:
        return {}
    footprint = line.buffer(22+SEWER_ROAD_SETBACK, join_style=2)
    out = {}
    for r in roads:
        if r['kind'] == 'path' or r['name'] == high_street:
            continue
        corridor = LineString(r['route']).buffer(r['width']/2, join_style=2, cap_style=2)
        if corridor.intersects(footprint):
            out[r['name']] = (r, corridor)
    return out


def annotate_road_ends(ends, line, roads, crest_width):
    """Name the street beside each road-facing bank end. Where the street
    passes under the sewer, roadAxis is its centreline chord across the deck
    (crest edge to crest edge), which docs/sewer-crossing.js uses for the arch."""
    crest = line.buffer(crest_width/2, join_style=2)
    for end in ends:
        if end['kind'] != 'road':
            continue
        middle = LineString([(p[0], p[2]) for p in end['points']]).interpolate(.5, normalized=True)
        name = min(roads, key=lambda n: roads[n][1].buffer(SEWER_ROAD_SETBACK).boundary.distance(middle))
        record, _ = roads[name]
        end['road'] = name
        end['roadWidth'] = record['width']
        under = LineString(record['route']).intersection(crest)
        if under.geom_type == 'LineString' and not under.is_empty:
            coords = list(under.coords)
            end['roadAxis'] = [[round(x, 2), round(z, 2)] for x, z in (coords[0], coords[-1])]
    return ends


def densify_bank_ends(piece, line, obstacles, step=2):
    """Add outline vertices along obstacle-facing ends, every 2 m and at the
    crest edge, so the triangulated bank keeps its full profile up to the end
    wall instead of sagging to the toe height between distant corners."""
    edges = [o.boundary.buffer(.02) for o in obstacles.values()]
    crest = line.buffer(7.5, join_style=2).boundary

    def ring(coords):
        out = []
        for a, b in zip(coords[:-1], coords[1:]):
            out.append(a)
            segment = LineString([a, b])
            if not any(e.covers(segment) for e in edges):
                continue
            cut = segment.intersection(crest)
            stops = {segment.project(Point(p)) for g in getattr(cut, 'geoms', [cut]) if not g.is_empty for p in g.coords}
            n = int(segment.length//step)
            stops.update(segment.length*i/(n+1) for i in range(1, n+1))
            for t in sorted(stops):
                if .2 < t < segment.length-.2:
                    p = segment.interpolate(t)
                    out.append((p.x, p.y))
        out.append(coords[-1])
        return out
    return Polygon(ring(list(piece.exterior.coords)), [ring(list(h.coords)) for h in piece.interiors])


def sewer_bank_ends(pieces, line, obstacles, height):
    """Runs of bank outline that face an obstacle, for the brick end walls.

    Each run follows the outline with positive signed area in (x, z), so for a
    step (dx, dz) the obstacle lies towards (dz, -dx). Points carry the bank
    height in the same [x, y, z] convention as the bank triangles; chainage is
    where the run crosses the sewer centreline.
    """
    ends = []
    for kind, obstacle in obstacles.items():
        edge = obstacle.boundary.buffer(.02)
        for piece in pieces:
            for ring in [piece.exterior, *piece.interiors]:
                coords = list(ring.coords)[:-1]
                n = len(coords)
                on = [edge.covers(LineString([coords[i], coords[(i+1) % n]])) for i in range(n)]
                if all(on) or not any(on):
                    continue
                start = next(i for i in range(n) if on[i] and not on[i-1])
                run = []
                for k in range(n+1):
                    i = (start+k) % n
                    if on[i] and k < n:
                        run.append(i)
                        continue
                    if run:
                        points = [coords[j] for j in run]+[coords[(run[-1]+1) % n]]
                        path = LineString(points)
                        if path.length > 1:
                            # Chainage where the end crosses the sewer centreline.
                            cross = path.intersection(line)
                            at = cross if cross.geom_type == 'Point' else path.interpolate(.5, normalized=True)
                            ends.append({'kind': kind, 'chainage': round(line.project(at), 2),
                                         'points': [[round(x, 2), height(x, z), round(z, 2)] for x, z in points]})
                        run = []
    return sorted(ends, key=lambda e: e['chainage'])


def neighbourhood():
    context = json.loads((ROOT/'data/maps/neighbourhood-context.json').read_text())
    traces = json.loads((ROOT/'data/maps/os-neighbourhood-traces.json').read_text())
    # Similarity registration preserves angles and scale in the supplied mosaic.
    registrations = {}
    for name,s in traces['sheets'].items():
        if 'registrationToSheet' not in s:
            continue
        source = [complex(*c['pixel']) for c in s['controls']]
        target = [complex(*c['target']) for c in s['controls']]
        mean_source,mean_target = sum(source)/len(source),sum(target)/len(target)
        scale = sum((u-mean_source).conjugate()*(v-mean_target) for u,v in zip(source,target)) / sum(abs(u-mean_source)**2 for u in source)
        offset = mean_target-scale*mean_source
        fit = [scale.real,scale.imag,offset.real,offset.imag]
        registrations[name] = fit
        rms = math.sqrt(sum(abs(scale*u+offset-v)**2 for u,v in zip(source,target))/(2*len(source)))
        context.setdefault('registrationChecks',{})[name] = {
            'rmsTargetPixels':round(rms,3),
            'fit':fit, 'note':'Fit consistency only; not independent absolute geographic accuracy.'}

    def point(sheet, pixel):
        s = traces['sheets'][sheet]
        if sheet in registrations:
            a,b,tx,ty = registrations[sheet]
            u,v = pixel
            return point(s['registrationToSheet'],[a*u-b*v+tx,b*u+a*v+ty])
        left, top, right, bottom = s['neatline']
        west, south, east, north = s['bounds']
        u, v = pixel
        e, n = project(west+(east-west)*(u-left)/(right-left),
                       north-(north-south)*(v-top)/(bottom-top))
        return [round(e-ORIGIN[0], 2), round(ORIGIN[1]-n, 2)]

    def row(sheet, a, b, depth):
        pa, pb = point(sheet,a), point(sheet,b)
        dx, dz = pb[0]-pa[0], pb[1]-pa[1]
        length = math.hypot(dx,dz)
        pixels = math.dist(a,b)
        d = depth*length/pixels
        corners = [[round(p[0]+sign*(-dz/length)*d/2,2),
                    round(p[1]+sign*(dx/length)*d/2,2)]
                   for p,sign in [(pa,-1),(pb,-1),(pb,1),(pa,1)]]
        return {'x': round((pa[0]+pb[0])/2,2), 'z': round((pa[1]+pb[1])/2,2),
                'width': round(length,2), 'depth': round(d,2),
                'rotation': round(-math.degrees(math.atan2(dz,dx)),2),
                'footprint': corners, 'sourceSheet': sheet}

    context['houses'] = []
    for i,h in enumerate(traces['abbeyPairs']):
        x,y = h['centre']
        # Main envelopes follow the row, which rises gently eastwards on the scan.
        spec = row('32',[x-h['width']/2,y+1.7],[x+h['width']/2,y-1.7],h['depth'])
        context['houses'].append(dict(spec,id=f'abbey-pair-{i+1}',wallHeight=6.5,
            evidence='OS VIII.32 envelope and position; architectural form from listing 1080983; height interpreted.'))
    context['terraces'] = []
    frontage_audit = json.loads((ROOT/'data/maps/housing-road-traces.json').read_text())
    housing_streets = [(r['name'],LineString([point(r['sheet'],p) for p in r['points']]),r['width'])
                       for r in frontage_audit['roads'] if r['sheet'] not in ['scene','southwest']]
    for i,r in enumerate(traces['rows']):
        correction = frontage_audit['housingCorrections'].get(f'os-row-{i+1}', {})
        if correction.get('omit'):
            context.setdefault('omittedTerraces', []).append({'id':f'os-row-{i+1}', **correction})
            continue
        r = {**r, **correction}
        spec = row(r.get('sheet','32'),r['a'],r['b'],r['depth'])
        spec = dict(spec,id=f'os-row-{i+1}',street=r['street'],
            wallHeight=6.4, bays=max(2,round(spec['width']/5.2)),
            evidence='Main row envelope traced from OS; household divisions, height and facade are interpretations.',
            frontageAudit=correction.get('evidence'))
        context['terraces'].extend(split_at_streets(spec,housing_streets))
    for i,h in enumerate(traces['holders']):
        x,z = point(h['sheet'],h['centre'])
        edge = point(h['sheet'],[h['centre'][0]+h['radius'],h['centre'][1]])
        context['holders'].append({'id':f'west-ham-os-{i+1}','siteId':873,'x':x,'z':z,
            'radius':round(math.dist([x,z],edge),2),'height':26,'columns':24,
            'bellHeight':14 if i%2 else 20,
            'evidence':'OS VIII.32 / VIII.22 circle location and radius; frame height, column count and bell elevation interpreted.'})
    context['registration'] = traces['registration']
    context['housingExclusions'] = [{'name':r['name'],'footprint':[point(r['sheet'],p) for p in r['polygon']]}
                                    for r in traces.get('exclusions',[])]
    s=traces['sewer']; anchor=point(s['sheet'],s['anchorPixel'])
    route=[[round(x-anchor[0],2),round(z-anchor[1],2)] for x,z in [point(s['sheet'],p) for p in s['centreline']]]
    for end,other,insert in [(route[0],route[1],0),(route[-1],route[-2],None)]:
        length=math.dist(end,other)
        extension=[round(end[i]+(end[i]-other[i])*s['extensionMetres']/length,2) for i in [0,1]]
        if insert==0: route.insert(0,extension)
        else: route.append(extension)
    context['sewer']=dict(s,route=route)
    correction_path=ROOT/'data/maps/sewer-high-street.json'
    if correction_path.exists():
        correction=json.loads(correction_path.read_text())
        context['sewer']['priorUncorrectedRoute']=route
        context['sewer']['route']=correction['westernRoute']+route[1:]
        context['sewer']['alignmentEvidence']=correction['evidence']
    context['railways']=[]
    for railway in traces['railways']:
        route=[]
        for part in railway['parts']:
            route.extend([point(part['sheet'],p) for p in part['points']])
        context['railways'].append({'name':railway['name'],'route':route,'tracks':railway['tracks'],
            'evidence':'Route traced from OS; track spacing, sleepers and level are schematic.'})
    garden=traces['garden']
    context['garden']={'footprint':[point(garden['sheet'],p) for p in garden['polygon']], 'evidence':garden['evidence']}
    # Keep the larger allotment interpretation clear of mapped paths and lanes.
    road_traces=json.loads((ROOT/'data/maps/road-traces.json').read_text())['roads']
    context['garden']['accessCorridors']=[{'route':[point('32',[v*1888/r['pixelWidth'] for v in p]) for p in r['points']], 'width':r['width']}
                                        for r in road_traces if r['sheet']=='32']
    context['mappedFactories']=[]
    for f in traces['factoryFrontages']:
        spec=row(f['sheet'],f['a'],f['b'],f['depth'])
        context['mappedFactories'].append(dict(spec,siteId=f['siteId'],name=f['name'],height=f['height'],
            evidence='Simplified main-range envelope read from OS; height, roof form and facade interpretation from photographs.'))
    context['sources']['os_traces'] = {n:s['source'] for n,s in traces['sheets'].items()}
    return context


def rings(polygon):
    return [[[round(x - ORIGIN[0], 2), round(ORIGIN[1] - y, 2)]
             for x, y in ring.coords]
            for ring in [polygon.exterior, *polygon.interiors]]


def build():
    source = json.loads((ROOT / 'data/maps/panorama-source-context.geojson').read_text())
    result = {'origin': {'easting': ORIGIN[0], 'northing': ORIGIN[1],
                         'crs': 'EPSG:27700', 'axes': 'x east; z south; metres'},
              'rivers': [], 'sites': [], 'factoryStudies': [], 'bankStudies': [], 'bankRelief': []}
    for feature in source['features']:
        p = feature['properties']
        geom = transform(project, shape(feature['geometry'])).simplify(0.4, preserve_topology=True)
        polygons = [geom] if geom.geom_type == 'Polygon' else list(geom.geoms)
        polygons = [g for g in polygons if g.geom_type == 'Polygon']
        entry = {'id': p['source_index'], 'name': p.get('Map_Name') or p.get('Name'),
                 'polygons': [rings(poly) for poly in polygons]}
        point = geom.representative_point()
        entry['anchor'] = [round(point.x - ORIGIN[0], 2), round(ORIGIN[1] - point.y, 2)]
        result['rivers' if p['kind'] == 'river' else 'sites'].append(entry)
        if p['kind'] == 'river':
            # A schematic inset, NOT a reconstructed low-water line.
            water = geom.buffer(-7)
            pieces = [water] if water.geom_type == 'Polygon' else list(water.geoms)
            entry['insetWater'] = [rings(g) for g in pieces if not g.is_empty and g.geom_type == 'Polygon']
            if p['source_index'] == 14:
                # The GIS traces two narrow channels. Fill the foreground between them
                # with an explicitly inferred exposed-bed study, following the photo.
                from shapely.geometry import LineString
                west, east = [], []
                for z in range(0, 341, 10):
                    section = geom.intersection(LineString([(538500, ORIGIN[1]-z), (539100, ORIGIN[1]-z)]))
                    if not section.is_empty:
                        west.append((section.bounds[0]-8, ORIGIN[1]-z))
                        east.append((section.bounds[2]+8, ORIGIN[1]-z))
                bank = Polygon(west+east[::-1])
                result['bankStudies'] = [rings(bank)]
                exposed = bank.difference(geom)
                patches = [exposed] if exposed.geom_type == 'Polygon' else list(exposed.geoms)
                for patch in patches:
                    if patch.geom_type != 'Polygon':
                        continue
                    samples = list(patch.exterior.coords)
                    for hole in patch.interiors:
                        samples.extend(hole.coords)
                    minx,miny,maxx,maxy = patch.bounds
                    for x in range(int(minx),int(maxx)+1,3):
                        for y in range(int(miny),int(maxy)+1,3):
                            if patch.contains(Point(x,y)):
                                samples.append((x,y))
                    for triangle in triangulate(MultiPoint(samples)):
                        if not patch.covers(triangle):
                            continue
                        vertices = []
                        # Reverse winding after northing is mapped to south-positive z.
                        for x,y in list(triangle.exterior.coords)[:3]:
                            lx,lz = x-ORIGIN[0],ORIGIN[1]-y
                            edge = min(1,Point(x,y).distance(patch.boundary)/4)
                            # Inferred relief only. Tapers to zero at channels and study edges.
                            height = .04 + edge*(.65+.18*math.sin(lx*.8+lz*.3)+.1*math.sin(lz*1.3))
                            vertices.append([round(lx,2),round(height,3),round(lz,2)])
                        result['bankRelief'].append(vertices)
        elif p['source_index'] in (874, 875, 876, 1125, 253, 562, 965):
            # Keep study blocks inside their site without treating the whole plot as a building.
            minx, miny, maxx, maxy = geom.bounds
            for x in range(int(minx)+12, int(maxx), 22):
                for y in range(int(miny)+14, int(maxy), 29):
                    width, depth = 18, 25
                    footprint = box(x-width/2, y-depth/2, x+width/2, y+depth/2)
                    if geom.covers(footprint):
                        result['factoryStudies'].append({'siteId': p['source_index'],
                            'x': round(x-ORIGIN[0], 2), 'z': round(ORIGIN[1]-y, 2),
                            'width': width, 'depth': depth, 'height': 9 + ((x+y)%4)*2,
                            'evidence': 'Illustrative mass inside a mapped industrial site; not a surveyed footprint.'})
    output = ROOT / 'docs/data/ground-plan.json'
    # Reviewed local bank reconciliation; retain the opposite bank and the
    # old millrace instead of trimming the mapped factory walls to the old GIS.
    for bank_name in ['city-mills-bank-alignment.json', 'west-sugar-bank-alignment.json', 'bow-works-bank-alignment.json', 'hunt-works-bank-alignment.json', 'bow-magnet-bank-alignment.json']:
        bank_path = ROOT/'data/maps'/bank_name
        correction = json.loads(bank_path.read_text())
        river = next(r for r in result['rivers'] if r['id']==correction['riverId'])
        ring = river['polygons'][correction['polygonIndex']][correction['ringIndex']]
        for change in correction['replacements']:
            assert math.dist(ring[change['vertex']], change['priorPoint']) < .02, 'Bank source changed; review controls'
            ring[change['vertex']] = change['point']
        assert all(Polygon(p[0],p[1:]).is_valid for p in river['polygons'])
        river['bankAlignment'] = correction
    from prepare_east_channelsea_context import apply_water_context
    east_context=json.loads((ROOT/'data/maps/east-channelsea-context-alignment.json').read_text())
    apply_water_context(result,east_context)
    result['neighbourhood'] = neighbourhood()
    context=result['neighbourhood']
    context['mill']={'name':'Abbey Mill (Corn)','siteId':252,'x':-11.97,'z':-58.22,'width':14,'depth':8,'height':11.5,'rotation':11.7,
        'evidence':'OS VIII.32 names Abbey Mill (Corn); Main southern mill mass re-anchored to OS VIII.32 pixel (1090,625) at 1800 px width, clear of the mapped lane crossing; author suggests the c1800 mill building form probably continued into c1900, analogous to nearby Three Mills. Interlocking gables, boarded upper floors and masonry base are inferred from Figure 1; height is estimated. Windmill omitted.'}
    replaced={f['siteId'] for f in context['mappedFactories']}
    result['factoryStudies']=[f for f in result['factoryStudies'] if f['siteId'] not in replaced]

    # Scene facts the renderer used to hardcode. Each is an interpretation, recorded here so every consumer sees the same world.
    context['studyChimneys']={'siteIds':[874,875,876,1125,562,965],'height':36,'baseRadius':2.1,'topRadius':1.5,'capRadius':1.9,
        'evidence':'One deliberately simple chimney per chosen site, placed at the range centre; sites with individually registered ranges omit it. Heights and radii are study assumptions, not surveyed stacks.'}
    context['barges']=[{'x':20,'z':49,'heading':-10,'laden':True},{'x':25,'z':73,'heading':8,'laden':True},
        {'x':-26,'z':37,'heading':5,'laden':False},{'x':-35,'z':95,'heading':-8,'laden':True}]
    context['bargesEvidence']='Lighter positions, headings and loads interpret the 1900 photograph; none is a surveyed mooring.'
    facades={253:{'curvedRoof':True,'lightBrick':True},512:{'lightBrick':True},875:{'sparseUpperArches':True}}
    for f in result['factoryStudies']+context['mappedFactories']:
        if f['siteId'] in facades:f['facade']=dict(facades[f['siteId']],evidence='Facade treatment interpreted from the period photographs; not a documented elevation.')
    line=LineString(context['sewer']['route'])
    # Earth banks stop at the water the browser actually draws and at the railway
    # corridor; the elevated crest spans them. Bank ends get brick end walls
    # (docs/sewer-crossing.js), so no open wedge or bare ground lies under the deck.
    water=unary_union([Polygon(p[0],p[1:]) for f in result['rivers'] for p in f['polygons']])
    rail=unary_union([LineString(r['route']).buffer(6) for r in context['railways']])
    drawn=drawn_water(result)
    # The embankment fills small marsh pools rather than bridging them.
    drawn=unary_union([g for g in getattr(drawn,'geoms',[drawn]) if g.area>=50])
    obstacles={'water':drawn.buffer(SEWER_WATER_SETBACK),'railway':rail}
    bank=line.buffer(22,join_style=2).difference(unary_union(list(obstacles.values())))
    crest=line.buffer(7.5,join_style=2)
    context['sewer']['crest']=[[[[round(x,2),round(z,2)] for x,z in crest.exterior.coords]]]
    # Drop slivers left between water bodies; they cannot carry an embankment.
    pieces=[densify_bank_ends(p,line,obstacles) for p in getattr(bank,'geoms',[bank]) if p.area>=20]
    # The allotment layout keeps the bank outline it was laid out against;
    # street openings through the embankment do not move the garden.
    garden_bank=unary_union(pieces)
    # Streets pass under the sewer (Abbey Lane, Mill Meads works road) or meet
    # its toe; the bank stops 1.5 m from the street and gets a brick end wall.
    roads=sewer_road_openings(line)
    if roads:
        obstacles['road']=unary_union([c for _,c in roads.values()]).buffer(SEWER_ROAD_SETBACK)
        bank=line.buffer(22,join_style=2).difference(unary_union(list(obstacles.values())))
        pieces=[densify_bank_ends(p,line,obstacles) for p in getattr(bank,'geoms',[bank]) if p.area>=20]
    bank_height=lambda x,z:round(max(0,min(7.25,(22-line.distance(Point(x,z)))*7.25/14.5)),2)
    context['sewer']['banks']=[]
    for piece in pieces:
        samples=list(piece.exterior.coords)
        for hole in piece.interiors:samples.extend(hole.coords)
        minx,minz,maxx,maxz=piece.bounds
        # One fixed 12 m lattice for every piece, so moving a bank end only
        # re-triangulates near that end. Its phase keeps the High Street
        # stretch on the lattice it was first triangulated on.
        x0,z0=int(minx)-(int(minx)-SEWER_BANK_LATTICE[0])%12,int(minz)-(int(minz)-SEWER_BANK_LATTICE[1])%12
        for x in range(x0,int(maxx)+1,12):
            for z in range(z0,int(maxz)+1,12):
                if piece.contains(Point(x,z)):samples.append((x,z))
        for tri in triangulate(MultiPoint(samples)):
            if piece.covers(tri):
                context['sewer']['banks'].append([[round(x,2),bank_height(x,z),round(z,2)] for x,z in list(tri.exterior.coords)[:3][::-1]])
    ends=sewer_bank_ends([orient(p) for p in pieces],line,obstacles,bank_height)
    context['sewer']['bankEnds']=annotate_road_ends(ends,line,roads,context['sewer']['crestWidth'])
    context['sewer']['bankEndsEvidence']=('Bank ends follow the drawn water edge, set back '+str(SEWER_WATER_SETBACK)+' m, and the 6 m railway corridor. '
        'The position of each end is derived from the mapped channel and railway; the brick end wall, its 0.8 m thickness and its '
        'footing are interpreted, not a surveyed abutment. '
        'Road ends stand '+str(SEWER_ROAD_SETBACK)+' m from the traced street corridors (docs/data/infrastructure.json roads, '
        'Stratford High Street and paths excepted), so their positions follow the mapped streets. Where a street passes under the '
        'sewer, the brick arch carrying the deck, its segmental form, rise and springing height are interpreted, not a documented structure.')
    garden=Polygon(context['garden']['footprint']).difference(water.buffer(8)).difference(garden_bank)
    access=unary_union([LineString(r['route']).buffer(r['width']/2+1) for r in context['garden']['accessCorridors']])
    garden=garden.difference(access)
    ditch_path=ROOT/'data/maps/marsh-ditches.json'
    if ditch_path.exists():
        ditches=json.loads(ditch_path.read_text())
        garden=garden.difference(unary_union([LineString(f['route']).buffer(f['width']/2+3) for f in ditches['features']]))
    context['garden']['beds']=[]
    # Inferred allotment divisions: align groups with the mapped field edge,
    # leave shared access strips, and avoid repeating one identical bed tile.
    rng=random.Random(1893)
    origin=(garden.centroid.x,garden.centroid.y);angle=-15
    local=rotate(garden,-angle,origin=origin)
    minx,minz,maxx,maxz=local.bounds
    z=minz+2;row=0
    while z<maxz:
        depth=rng.uniform(16,24);x=minx+2+(row%2)*4;column=0
        while x<maxx:
            width=rng.uniform(8,13)
            footprint=rotate(box(x,z,x+width,z+depth),angle,origin=origin)
            if garden.covers(footprint) and rng.random()>.09:
                centre=footprint.centroid
                context['garden']['beds'].append({'x':round(centre.x,3),'z':round(centre.y,3),
                    'width':round(width,3),'depth':round(depth,3),'rotation':angle,
                    'footprint':[[round(a,3),round(b,3)] for a,b in footprint.exterior.coords],
                    'seed':rng.randrange(100000),'shed':rng.random()<.09})
            x+=width+(3.8 if column%4==3 else 1.5);column+=1
        z+=depth+(4.5 if row%3==2 else 2.2);row+=1
    context['garden']['layoutEvidence']='Inferred plot divisions and planting, aligned with the mapped field edge. Varied sizes and shared access gaps are visual interpretations, not traced household boundaries.'
    context['garden']['cultivableAreaM2']=round(garden.area)
    output.write_text(json.dumps(result, separators=(',', ':')) + '\n')
    print(f'Built {len(result["rivers"])} rivers and {len(result["sites"])} industrial sites: {output}')


if __name__ == '__main__':
    build()
