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
from shapely import segmentize, constrained_delaunay_triangles, contains_xy, distance as shapely_distance, points as shapely_points
from housing_frontages import split_at_streets

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = (538900, 183209)  # Historic England's approximate bridge grid reference
project = Transformer.from_crs(4326, 27700, always_xy=True).transform
SEWER_WATER_SETBACK = 1.5  # metres between drawn water and the earth bank; the end wall stands in it
SEWER_BANK_LATTICE = (2, 0)  # x, z phase (mod 12 m) of the bank sample grid
SEWER_ROAD_SETBACK = 1.5  # metres between street edge and bank; build_infrastructure.py used roads.buffer(1.5)
# Interpreted earthwork form of the embankment (task T8); see EarthBank.
SEWER_TOE_SEED = 1864  # seeds the toe wander and slope variation; any fixed value reproduces the same bank
SEWER_TOE_AMPLITUDE = 2.0  # metres; bound on the toe's wander either side of the 22 m half base
SEWER_BANK_SPACING = 5  # metres between slope sample rows along the bank near the scene
SEWER_BANK_ROWS = (0, .25, .5, .78)  # slope fractions (crest edge 0 to toe 1) of the sample rows
# Route beyond the OS VIII.32 trace and the High Street correction (task T1c).
# Crest centreline points read from the OS London five-foot plan, 1893-96 revision
# (NLS tiles, layer os-london-five-foot-1893, via factory_map_sources.mosaic), in
# scene metres. Reading accuracy about 2-4 m: points sit on the crest between the
# mapped slope hachures and the "NORTHERN OUTFALL SEWER" lettering.
# West: from the open embankment's end at the east kerb of Wick Lane, across the
# Lea at Old Ford, to the first point of the High Street correction's westernRoute.
SEWER_WEST_TRACE = [(-1790.5, -702.5), (-1752.9, -688.3), (-1681.7, -664.0), (-1632.2, -645.8), (-1588.7, -630.2),
                    (-1542.0, -621.0), (-1475.4, -607.4), (-1440.0, -600.9), (-1394.6, -587.3)]
# Wick Lane centreline where it passes the sewer (five-foot plan; the lane is not
# traced as a street in this model). The covered sewer continues west of it.
SEWER_WICK_LANE_CROSSING = (-1798.9, -702.8)
# East: replaces the 1400 m straight extrapolation beyond the last OS VIII.32 point
# (349.54, 51.25). The first point lies on that extrapolation, which agrees with the
# five-foot crest within 2 m as far as here; then the mapped bend south-east across
# the London, Tilbury and Southend Railway and through Plaistow, to the edge of the
# five-foot sheet coverage at about x 2290 (no tiles exist further east).
SEWER_EAST_TRACE = [(697.8, 39.78), (722.8, 43.3), (739.6, 53.1), (760.6, 67.0), (804.9, 96.7), (870.2, 141.1),
                    (1154.3, 318.7), (1430.6, 480.5), (1581.4, 546.9), (1667.9, 574.9), (1750.1, 585.3),
                    (1922.1, 610.2), (2176.8, 665.6), (2289.2, 687.0)]
# Beyond the five-foot coverage the route continues on the last mapped bearing to
# x 2700 (Blind Lane, the West Ham borough boundary on the OS six-inch second edition,
# which shows the embankment on this line within a few metres), inside the
# landscape's base ground (to x 2750) and at the fog distance from the scene centre.
SEWER_EAST_END_X = 2700.0
SEWER_PORTAL_SETBACK = 0.3  # metres; the bank ends this far east of the portal face, inside the headwall


class EarthBank:
    """Interpreted earth form of the Northern Outfall Sewer embankment.

    Documented: a 15 m crest, 44 m base and about 7.4 m height (the sewer
    record). Interpreted: everything about the section between crest edge and
    toe. The toe outline uses rounded joins and caps, not mitres. Each toe wanders
    independently up to SEWER_TOE_AMPLITUDE either side of the 22 m half base,
    as a seeded sum of three long waves (zero mean, so the base stays 44 m on
    average). The slope is a convex shoulder and concave foot: a blend of a
    straight batter and a smoothstep, with the blend varying slowly along each
    side, plus a low swell (at most 0.1 m) that vanishes at crest edge and toe.
    Heights are returned in the bank convention (docs/app.js scales y by
    cover / sewer height): the full sewer height at the crest edge, so slope
    and grassed crest meet without a step, 0.1 lower under the crest sheet
    (no coincident faces) and 0 at the toe. The straight profile stopped at
    7.25, which left a strip of the deck slab showing along the crest edge.
    """

    def __init__(self, line, top, crest_half=7.5, toe=22, seed=SEWER_TOE_SEED, amplitude=SEWER_TOE_AMPLITUDE, origin=0):
        rng = random.Random(seed)
        self.line, self.length = line, line.length
        # Chainage the waves are measured from. The T1c western extension moved the
        # route start; keeping the waves on the earlier chainage keeps the bank form
        # (and its triangles) unchanged along the stretch that was already modelled.
        self.origin = origin
        self.crest_half, self.toe, self.top, self.under_crest = crest_half, toe, top, top-.1
        shares, bands = (.5, .3, .2), ((120, 180), (55, 85), (28, 40))
        self.toe_waves = {side: [(amplitude*s, rng.uniform(*b), rng.uniform(0, 2*math.pi)) for s, b in zip(shares, bands)]
                          for side in (1, -1)}
        self.blend_waves = {side: (rng.uniform(70, 110), rng.uniform(0, 2*math.pi)) for side in (1, -1)}
        self.swell_waves = {side: (rng.uniform(18, 26), rng.uniform(0, 2*math.pi)) for side in (1, -1)}

    def taper(self, d):
        # The route ends taper to plain round caps (the west one is cut by the portal), so both toes agree there.
        return max(0, min(1, d/60, (self.length-d)/60))

    def toe_offset(self, d, side):
        wave = sum(a*math.sin(2*math.pi*(d-self.origin)/w+p) for a, w, p in self.toe_waves[side])
        return self.toe+self.taper(d)*wave

    def locate(self, x, z):
        p = Point(x, z)
        d = self.line.project(p)
        c = self.line.interpolate(d)
        a, b = self.line.interpolate(max(0, d-.5)), self.line.interpolate(min(self.length, d+.5))
        side = 1 if (b.x-a.x)*(z-c.y)-(b.y-a.y)*(x-c.x) >= 0 else -1
        return d, side, math.hypot(x-c.x, z-c.y), c

    def height(self, x, z):
        d, side, dist, _ = self.locate(x, z)
        if dist < self.crest_half-.01:
            return self.under_crest
        if dist <= self.crest_half:
            return self.top
        u = (dist-self.crest_half)/(self.toe_offset(d, side)-self.crest_half)
        if u >= 1:
            return 0
        w, p = self.blend_waves[side]
        k = .5+.15*math.sin(2*math.pi*(d-self.origin)/w+p)
        fall = (1-k)*u+k*u*u*(3-2*u)
        w, p = self.swell_waves[side]
        swell = .1*self.taper(d)*math.sin(math.pi*u)*math.sin(2*math.pi*(d-self.origin)/w+p)
        return round(max(0, min(self.top, self.top*(1-fall)+swell)), 2)

    def radial(self, x, z, u):
        """Move (x, z) along its offset from the centreline to slope fraction u."""
        d, side, dist, c = self.locate(x, z)
        if dist < 1e-6:
            return None
        r = self.crest_half+u*(self.toe_offset(d, side)-self.crest_half)
        return (c.x+(x-c.x)*r/dist, c.y+(z-c.y)*r/dist)

    def footprint(self, step=4):
        outline = segmentize(self.line.buffer(self.toe, quad_segs=16), step)
        ring = [q for q in (self.radial(x, z, 1) for x, z in outline.exterior.coords[:-1]) if q]
        shape = Polygon(ring).buffer(0)
        return max(getattr(shape, 'geoms', [shape]), key=lambda g: g.area)

    def rows(self, spacing=SEWER_BANK_SPACING, near=1300):
        """Sample rows along the slope at SEWER_BANK_ROWS, closer near the scene."""
        out = []
        for side in (1, -1):
            for u in SEWER_BANK_ROWS:
                curve = self.line.offset_curve(side*(self.crest_half+u*(self.toe-self.crest_half)), quad_segs=8)
                for part in getattr(curve, 'geoms', [curve]):
                    for i, (x, z) in enumerate(segmentize(part, spacing).coords):
                        if math.hypot(x, z) > near and i % 3:
                            continue
                        q = self.radial(x, z, u)
                        if q:
                            out.append(q)
        return out


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
    # The crest edge of the EarthBank profile (radially 7.5 m from the centreline,
    # so rounded at bends); the mitred crest sheet differs by at most 0.07 m there.
    crest = line.buffer(7.5, quad_segs=8).boundary

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


SEWER_WEST_JOIN = (-1317.819, -567.373)  # first point of data/maps/sewer-high-street.json westernRoute
SEWER_EAST_JOIN = (349.54, 51.25)  # last OS VIII.32 centreline point


def sewer_route_extensions(sewer):
    """Carry the sewer route from the Wick Lane portal to the edge of the landscape (T1c).

    Replaces the two straight end-bearing extrapolations. Mapped lengths follow the
    OS five-foot crest; the inferred length is the eastern continuation beyond the
    five-foot coverage. Adds the portal record for docs/sewer-crossing.js.
    """
    route = [list(p) for p in sewer['route']]
    assert math.dist(route[0], SEWER_WEST_JOIN) < .01 and math.dist(route[-2], SEWER_EAST_JOIN) < .01
    (ax, az), (bx, bz) = SEWER_EAST_TRACE[-2:]
    end = (SEWER_EAST_END_X, round(bz+(bz-az)*(SEWER_EAST_END_X-bx)/(bx-ax), 2))
    sewer['route'] = [list(p) for p in SEWER_WEST_TRACE]+route[:-1]+[list(p) for p in SEWER_EAST_TRACE]+[list(end)]
    length = lambda points: sum(math.dist(a, b) for a, b in zip(points[:-1], points[1:]))
    west = length(SEWER_WEST_TRACE+[SEWER_WEST_JOIN])
    east_mapped = length([SEWER_EAST_JOIN]+SEWER_EAST_TRACE)
    east_inferred = math.dist(SEWER_EAST_TRACE[-1], end)
    source = 'OS London five-foot plan, 1893-96 revision (NLS tiles, layer os-london-five-foot-1893)'
    sewer['extensionMetres'] = round(east_inferred, 1)
    sewer['routeExtensions'] = {
        'west': {'mappedMetres': round(west, 1), 'inferredMetres': 0, 'source': source,
                 'evidence': 'Crest centreline read from the five-foot plan between the slope hachures, from the east kerb of Wick Lane '
                             'across the Lea at Old Ford to the High Street correction; reading accuracy about 2-4 m. Ends at the Wick Lane '
                             'portal: west of it the sewer is covered (author direction). The plan still shows embankment slopes between Wick '
                             'Lane and the North London Railway and a penstock chamber west of the railway; that stretch is not modelled.'},
        'east': {'mappedMetres': round(east_mapped, 1), 'inferredMetres': round(east_inferred, 1), 'source': source,
                 'evidence': 'Crest centreline read from the five-foot plan east of the last OS VIII.32 point: the straight run to the bend at '
                             'x 700 (the earlier extrapolation agrees with the plan within 2 m there), the bend south-east across the London, '
                             'Tilbury and Southend Railway, and the run through Plaistow to the edge of the five-foot coverage at x 2289. '
                             'The last '+str(round(east_inferred))+' m continue that last mapped bearing to x '+str(round(SEWER_EAST_END_X))+
                             ' (Blind Lane, the West Ham boundary) and are inferred; the OS six-inch second edition shows the embankment on '
                             'this line within a few metres. The route stops there, inside the landscape base ground (to x 2750) and at '
                             'the fog distance from the scene. Streets and the railway crossed by the extensions are not modelled, so the '
                             'bank is continuous over them.'},
        'replaces': 'The earlier 1400 m straight extrapolation of the OS VIII.32 end bearing east of (349.54, 51.25), which ran north '
                    'of east past the mapped bend, and the western end at (-1317.8, -567.4) in open marsh.'}
    sewer['evidence'] = ('Centreline read from OS VIII.32 and the supplied mosaic; translated to meet the existing listed bridge anchor. '
                         'Height follows author guidance of roughly roof level. West of the High Street correction and east of OS VIII.32 '
                         'the centreline is read from the OS London five-foot plan (1893-96): '+str(round(west))+' m west to the Wick Lane '
                         'portal and '+str(round(east_mapped))+' m east to the end of five-foot coverage. The last '+str(round(east_inferred))+
                         ' m in the east continue the last mapped bearing and are inferred, not surveyed. See routeExtensions.')
    (x0, z0), (x1, z1) = SEWER_WEST_TRACE[:2]
    n = math.hypot(x1-x0, z1-z0)
    sewer['portal'] = {
        'street': 'Wick Lane', 'chainage': 0, 'point': [x0, z0], 'direction': [round((x1-x0)/n, 5), round((z1-z0)/n, 5)],
        'streetCrossing': list(SEWER_WICK_LANE_CROSSING), 'bankSetback': SEWER_PORTAL_SETBACK,
        'evidence': 'Position mapped: the east kerb of Wick Lane where it meets the sewer on the OS five-foot plan (1893-96), which '
                    'marks B.M. 35.3 at the crossing. That the open embankment begins here and the sewer is covered to the west is '
                    'author direction (Victoria Park). Interpreted, not a documented structure: the brick portal headwall across the '
                    'embankment end, its thickness, its parapet and stone coping above the walk, and the blind stone arch ring on its west face marking where '
                    'the sewer passes into cover.'}


def portal_cut(portal, setback=0, reach=80):
    """Half-plane west of the portal face (moved east by setback), as a polygon."""
    (x, z), (dx, dz) = portal['point'], portal['direction']
    x, z = x+dx*setback, z+dz*setback
    nx, nz = -dz, dx
    return Polygon([(x+nx*reach, z+nz*reach), (x-nx*reach, z-nz*reach),
                    (x-nx*reach-dx*reach, z-nz*reach-dz*reach), (x+nx*reach-dx*reach, z+nz*reach-dz*reach)])


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
        sewer_route_extensions(context['sewer'])
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
    # The open embankment ends at the Wick Lane portal: the bank stops just east of
    # the portal face (inside its headwall) and the crest stops flush with the face.
    portal=context['sewer'].get('portal')
    if portal:
        obstacles['portal']=portal_cut(portal,SEWER_PORTAL_SETBACK)
    earth=EarthBank(line,context['sewer']['height'],origin=line.project(Point(SEWER_WEST_JOIN)) if portal else 0)
    footprint=earth.footprint()
    bank=footprint.difference(unary_union(list(obstacles.values())))
    crest=line.buffer(7.5,join_style=2)
    if portal:
        crest=crest.difference(portal_cut(portal))
    context['sewer']['crest']=[[[[round(x,2),round(z,2)] for x,z in crest.exterior.coords]]]
    # Drop slivers left between water bodies; they cannot carry an embankment.
    pieces=[densify_bank_ends(p,line,obstacles) for p in getattr(bank,'geoms',[bank]) if p.area>=20]
    # The allotment layout keeps the bank outline it was laid out against (the
    # earlier straight 22 m mitred outline); neither the earthwork form nor the
    # street openings through the embankment move the garden.
    laid_out=line.buffer(22,join_style=2).difference(unary_union(list(obstacles.values())))
    garden_bank=unary_union([p for p in getattr(laid_out,'geoms',[laid_out]) if p.area>=20])
    # Streets pass under the sewer (Abbey Lane, Mill Meads works road) or meet
    # its toe; the bank stops 1.5 m from the street and gets a brick end wall.
    roads=sewer_road_openings(line)
    if roads:
        obstacles['road']=unary_union([c for _,c in roads.values()]).buffer(SEWER_ROAD_SETBACK)
        bank=footprint.difference(unary_union(list(obstacles.values())))
        pieces=[densify_bank_ends(p,line,obstacles) for p in getattr(bank,'geoms',[bank]) if p.area>=20]
    bank_height=earth.height
    rows=earth.rows()
    rows_x=[x for x,_ in rows];rows_z=[z for _,z in rows]
    context['sewer']['banks']=[]
    for piece in pieces:
        samples=list(piece.exterior.coords)
        for hole in piece.interiors:samples.extend(hole.coords)
        minx,minz,maxx,maxz=piece.bounds
        # The flat crest keeps a sparse fixed 12 m lattice; the slopes get rows
        # along the earth profile. Rows closer than 0.6 m to the outline are
        # left out so no sliver triangles form against the densified ends.
        x0,z0=int(minx)-(int(minx)-SEWER_BANK_LATTICE[0])%12,int(minz)-(int(minz)-SEWER_BANK_LATTICE[1])%12
        for x in range(x0,int(maxx)+1,12):
            for z in range(z0,int(maxz)+1,12):
                if line.distance(Point(x,z))<earth.crest_half-.5 and piece.contains(Point(x,z)):samples.append((x,z))
        inside=[i for i in range(len(rows)) if minx<=rows_x[i]<=maxx and minz<=rows_z[i]<=maxz]
        if inside:
            xs=[rows_x[i] for i in inside];zs=[rows_z[i] for i in inside]
            keep=contains_xy(piece,xs,zs)
            clear=shapely_distance(piece.boundary,shapely_points(list(zip(xs,zs))))>.6
            samples+=[(x,z) for x,z,k,c in zip(xs,zs,keep,clear) if k and c]
        kept=[tri for tri in triangulate(MultiPoint(samples)) if piece.covers(tri)]
        # Unconstrained Delaunay can miss concave corners of the outline; fill
        # any remainder with constrained triangles on the same vertices.
        rest=piece.difference(unary_union(kept)) if kept else piece
        for part in getattr(rest,'geoms',[rest]):
            if part.geom_type=='Polygon' and part.area>.01:
                kept+=[t for t in constrained_delaunay_triangles(part).geoms if t.area>1e-4]
        for tri in kept:
            context['sewer']['banks'].append([[round(x,2),bank_height(x,z),round(z,2)] for x,z in list(orient(tri,-1).exterior.coords)[:3]])
    ends=sewer_bank_ends([orient(p) for p in pieces],line,obstacles,bank_height)
    context['sewer']['bankEnds']=annotate_road_ends(ends,line,roads,context['sewer']['crestWidth'])
    context['sewer']['bankEndsEvidence']=('Bank ends follow the drawn water edge, set back '+str(SEWER_WATER_SETBACK)+' m, and the 6 m railway corridor. '
        'The position of each end is derived from the mapped channel and railway; the brick end wall, its 0.8 m thickness and its '
        'footing are interpreted, not a surveyed abutment. '
        'Road ends stand '+str(SEWER_ROAD_SETBACK)+' m from the traced street corridors (docs/data/infrastructure.json roads, '
        'Stratford High Street and paths excepted), so their positions follow the mapped streets. Where a street passes under the '
        'sewer, the brick arch carrying the deck, its segmental form, rise and springing height are interpreted, not a documented structure. '
        'The portal end (kind portal) stands '+str(SEWER_PORTAL_SETBACK)+' m east of the Wick Lane portal face; see portal.')
    context['sewer']['bankFormEvidence']=('Kept from the sewer record: the mapped centreline, the 15 m crest, the 44 m base (mean) and the height of '
        'about 7.4 m (author guidance); the exact nineteenth-century section is unresolved. Interpreted, not surveyed: the earthwork form between crest edge and toe. '
        'The toe outline has rounded joins and caps instead of mitred corners. Each toe wanders independently about the 22 m half base, '
        'by a seeded sum of three long waves (seed '+str(SEWER_TOE_SEED)+', wavelengths 28-180 m, amplitude bound '
        '±'+str(SEWER_TOE_AMPLITUDE)+' m, zero mean, measured along the route from its pre-T1c western start so the earlier stretch keeps its form), '
        'tapering to the plain 22 m over the last 60 m at each end of the route (the western end is cut by the Wick Lane portal). '
        'The slope is a convex shoulder and concave foot (a straight batter blended with a smoothstep, the blend varying 0.35-0.65 along '
        'each side) with a swell of at most 0.1 m that vanishes at crest edge and toe, so no slope is a single plane; the slope '
        'meets the crest at the full height. '
        'The crest stays the exact 15 m band (its outline is unchanged; the bends are gentle, so its mitres add at most 0.07 m), grassed where it covers '
        'the earth bank and the sewer inside it; the stone deck shows only where it spans water, railway or street.')
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
