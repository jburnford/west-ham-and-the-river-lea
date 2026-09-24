"""Build the review scene's metric ground plan. Requires pyproj and shapely."""
import json
import math
from pathlib import Path

from pyproj import Transformer
from shapely.geometry import shape, box, Polygon, Point, MultiPoint, LineString
from shapely.ops import transform, triangulate, unary_union

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = (538900, 183209)  # Historic England's approximate bridge grid reference
project = Transformer.from_crs(4326, 27700, always_xy=True).transform


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
    for i,r in enumerate(traces['rows']):
        spec = row(r.get('sheet','32'),r['a'],r['b'],r['depth'])
        context['terraces'].append(dict(spec,id=f'os-row-{i+1}',street=r['street'],
            wallHeight=6.4, bays=max(2,round(spec['width']/5.2)),
            evidence='Main row envelope traced from OS; household divisions, height and facade are interpretations.'))
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
    result['neighbourhood'] = neighbourhood()
    context=result['neighbourhood']
    context['mill']={'name':'Abbey Mill (Corn)','siteId':252,'x':-11.97,'z':-58.22,'width':14,'depth':8,'height':11.5,'rotation':11.7,
        'evidence':'OS VIII.32 names Abbey Mill (Corn); Main southern mill mass re-anchored to OS VIII.32 pixel (1090,625) at 1800 px width, clear of the mapped lane crossing; author suggests the c1800 mill building form probably continued into c1900, analogous to nearby Three Mills. Interlocking gables, boarded upper floors and masonry base are inferred from Figure 1; height is estimated. Windmill omitted.'}
    replaced={f['siteId'] for f in context['mappedFactories']}
    result['factoryStudies']=[f for f in result['factoryStudies'] if f['siteId'] not in replaced]
    line=LineString(context['sewer']['route'])
    # Earth banks stop at waterways and the railway corridor; the elevated crest spans them.
    water=unary_union([Polygon(p[0],p[1:]) for f in result['rivers'] for p in f['polygons']])
    rail=unary_union([LineString(r['route']).buffer(6) for r in context['railways']])
    bridge_opening=line.intersection(Point(0,0).buffer(55)).buffer(24)
    bank=line.buffer(22,join_style=2).difference(water.buffer(2).union(rail).union(bridge_opening))
    crest=line.buffer(7.5,join_style=2)
    context['sewer']['crest']=[[[[round(x,2),round(z,2)] for x,z in crest.exterior.coords]]]
    pieces=[bank] if bank.geom_type=='Polygon' else list(bank.geoms)
    context['sewer']['banks']=[]
    for piece in pieces:
        samples=list(piece.exterior.coords)
        for hole in piece.interiors:samples.extend(hole.coords)
        minx,minz,maxx,maxz=piece.bounds
        for x in range(int(minx),int(maxx)+1,12):
            for z in range(int(minz),int(maxz)+1,12):
                if piece.contains(Point(x,z)):samples.append((x,z))
        for tri in triangulate(MultiPoint(samples)):
            if piece.covers(tri):
                context['sewer']['banks'].append([[round(x,2),round(max(0,min(7.25,(22-line.distance(Point(x,z)))*7.25/14.5)),2),round(z,2)] for x,z in list(tri.exterior.coords)[:3][::-1]])
    garden=Polygon(context['garden']['footprint']).difference(water.buffer(8)).difference(bank)
    access=unary_union([LineString(r['route']).buffer(r['width']/2+1) for r in context['garden']['accessCorridors']])
    garden=garden.difference(access)
    context['garden']['beds']=[]
    minx,minz,maxx,maxz=garden.bounds
    for x in range(int(minx),int(maxx),10):
        for z in range(int(minz),int(maxz),18):
            if garden.covers(box(x,z,x+7,z+14)):
                context['garden']['beds'].append({'x':x+3.5,'z':z+7,'width':7,'depth':14})
    context['garden']['cultivableAreaM2']=round(garden.area)
    output.write_text(json.dumps(result, separators=(',', ':')) + '\n')
    print(f'Built {len(result["rivers"])} rivers and {len(result["sites"])} industrial sites: {output}')


if __name__ == '__main__':
    build()
