"""GIS-led northern railway route; native OS supplies the junction interpretation.

Routine infrastructure builds read the saved register. Running this module only
re-authors that register from the repository GIS and existing Woolwich stations.
All formation levels, rail spacing and bridge construction remain interpreted.
"""
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from pyproj import Transformer
from scipy.interpolate import CubicSpline, CubicHermiteSpline
from shapely import constrained_delaunay_triangles, make_valid, segmentize
from shapely.geometry import LineString, Point, Polygon, box, shape
from shapely.ops import nearest_points, substring, transform, unary_union
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parents[1]
REGISTER = 'data/maps/north-london-connection.json'
IDENT = 'north-london-connection'
FEATURE_IDS = ['way/198582978', 'way/198582965', 'way/198582968']
PROJECTION = Transformer.from_crs(4326, 27700, always_xy=True)


def read(path):
    return json.loads((ROOT/path).read_text())


def parts(g, kind='Polygon'):
    return [p for p in getattr(g, 'geoms', [g]) if p.geom_type == kind and not p.is_empty]


def rings(g):
    return [[[list(q) for q in r.coords] for r in [p.exterior, *p.interiors]] for p in parts(g)]


def project_gis(g):
    def local(x, y, z=None):
        e, n = PROJECTION.transform(x, y)
        return e-538900, 183209-n
    return make_valid(transform(local, g))


def end_centre(g, p, q):
    # The middle of g's cross-section 1 m inside its end at p, across the direction p->q
    # (as build_river_system.py does for a centreline passage).
    u = np.subtract(q, p)/max(np.linalg.norm(np.subtract(q, p)), 1e-9); n = np.array([-u[1], u[0]])
    c = np.subtract(p, u)
    chord = g.intersection(LineString([c-200*n, c+200*n]))
    pp = [x for x in getattr(chord, 'geoms', [chord]) if x.geom_type == 'LineString' and not x.is_empty]
    if not pp:
        return np.asarray(p, float)
    return np.asarray(min(pp, key=lambda x: x.distance(Point(c))).interpolate(.5, normalized=True).coords[0])


def canal_passage():
    # The Hackney Cut runs on under the line, but its two 1895 water pieces stop either side of it.
    # Same route as the river system's crossing-517-518: between the middles of the facing ends.
    features = read('docs/maps/data/Water_1895.geojson')['features']
    a, b = (project_gis(shape(features[i]['geometry'])) for i in (517, 518))
    pa, pb = nearest_points(a, b)
    ca, cb = np.asarray(pa.coords[0]), np.asarray(pb.coords[0])
    for _ in range(3):
        ca, cb = end_centre(a, ca, cb), end_centre(b, cb, ca)
    return dict(route=[ca.tolist(), cb.tolist()], width=16.0, waterPieces=['Water_1895-517', 'Water_1895-518'],
        evidence='The OS shows the Hackney Cut running straight on under the Victoria Park branch; the 1895 water pieces stop either side of the line. Same passage as crossing-517-518 in the river system; the embankment opens over it like other water.')


def prepare():
    features = {f['id']: f for f in read('docs/maps/data/Rail_1895.geojson')['features']}
    source = [project_gis(shape(features[f]['geometry'])) for f in FEATURE_IDS]
    assert all(g.geom_type == 'LineString' for g in source)
    assert all(Point(a.coords[-1]).distance(Point(b.coords[0])) < .001 for a, b in zip(source, source[1:]))
    infra = read('docs/data/infrastructure.json')
    old = next(r for r in infra['railways'] if r.get('id') == 'woolwich-northern-connection')
    old_control = read('data/maps/woolwich-northern-connection.json')['route'][11]
    j = min(range(len(old['stations'])), key=lambda i: Point(old['stations'][i][:2]).distance(Point(old_control)))
    station = old['stations'][j]
    start = source[0].intersection(box(-1700, -2000, 1000, 1000))
    assert start.geom_type == 'LineString'
    end = substring(source[2], 0, source[2].project(Point(station[:2])))
    coords = list(start.coords)+list(source[1].coords)[1:]+list(end.coords)[1:]
    reference = LineString(coords)
    main = next(r for r in infra['railways'] if r.get('detailedMainline'))
    # The saved prior main line is immutable across routine integration/replay.
    if (ROOT/REGISTER).exists():
        baseline = read(REGISTER).get('mainlineExtension')
        if baseline:
            main = dict(main, route=baseline['priorRoute'], stations=baseline['priorStations'],
                length=baseline['priorLength'], bridges=baseline['priorBridgeRanges'],
                northernWater=baseline.get('priorNorthernWater',main['northernWater']))
    cross = reference.intersection(LineString(main['route']))
    assert cross.geom_type == 'Point'
    # Retain the GIS main-line crossing as an explicit spline control.
    cross_d = reference.project(cross)
    d = 0.0
    controls = [coords[0]]
    for a, b in zip(coords, coords[1:]):
        step = math.dist(a, b)
        if d < cross_d < d+step:
            controls.append(tuple(cross.coords[0]))
        controls.append(b)
        d += step
    controls[-1] = tuple(station[:2])
    area = reference.buffer(65, cap_style=2).envelope
    water, water_sources = [], []
    for layer in ['Water_1895', 'Lower_River_Lea']:
        for i, feature in enumerate(read('docs/maps/data/'+layer+'.geojson')['features']):
            g = project_gis(shape(feature['geometry']))
            if not g.intersects(area):
                continue
            clipped = g.intersection(area)
            pp = [p for p in parts(clipped) if p.area > 1]
            if pp:
                water.extend(pp)
                water_sources.append(dict(layer=layer, featureId=feature.get('id'), featureIndex=i))
    raw = dict(id=IDENT, name='North London / Victoria Park branch connection',
        register=REGISTER, railFeatureIds=FEATURE_IDS,
        source='Repository Rail_1895.geojson, WGS84 reprojected through BNG; local x=E-538900,z=183209-N',
        sourceSha256=hashlib.sha256((ROOT/'docs/maps/data/Rail_1895.geojson').read_bytes()).hexdigest(),
        sourcePolylines=[list(g.coords) for g in source], referenceRoute=list(reference.coords), route=controls,
        westClipX=-1700, tracks=2, trackSpacing=3.6, gauge=1.435,
        crestHalfWidth=4.5, baseHalfWidth=17, formationHeight=3.0,
        canalPassage=canal_passage(),
        canalLift=dict(formation=5.5, holdTo=100.0, rampTo=400.0, evidence='Interpreted (task E, author): the line crosses the Lee Navigation (Hackney Cut) on a bridge above the towing paths (OS 21-22 ft, about 4.3-4.5 m scene; White Post Lane bridge parapet B.M. 23.68 ft), and the OS hatches the embankment west of the cut. The traced 3.0 m formation stood more than a metre under the towing paths, so the rails ran into the canal banks either side of the bridge. Lifted to 5.5 m over the cut (girder soffit about 4.85 m), held to chainage 100 and eased back to the traced 3.0 m by chainage 400, before the Old Lea and Waterworks River bridges. Levels are estimates; no rail level is read here.'),
        join=dict(railwayId=old['id'], referenceControlIndex=11, stationIndex=j,
            point=station[:2], height=station[2], normal=station[3:5], chainage=station[5]),
        junction=dict(point=list(cross.coords[0]), sourceChainage=cross_d,
            mainlineId=main['id'], mainlineChainage=LineString(main['route']).project(cross),
            formationHeight=3.0, mainlineFormationHeight=main['formationHeight'],
            interpretation='Native OS independently reviewed: Victoria Park rails terminate at the west edge of the continuous diagonal GE rails and resume east at Stratford Station Low Level. No diamond/turnout across the main; interpreted underpass retained.',
            status='native-reviewed-underpass'),
        northernWaterContext=rings(unary_union(water)), waterSources=water_sources,
        mainlineExtension=dict(railFeatureId='way/198781682',
            sourcePolyline=list(project_gis(shape(features['way/198781682']['geometry'])).coords),
            priorRoute=main['route'], priorStations=main['stations'],
            priorLength=main['length'], priorBridgeRanges=main['bridges'],
            priorNorthernWater=main['northernWater'],
            extensionTargetLength=85.0,
            evidence='Bounded continuation along supplied GE mainline beyond the former cropped endpoint. Original route/station prefix and chainages remain exact; append a smooth tangent transition, and restore the OS-confirmed low-level underpass opening without changing the four original track profiles.'),
        evidence='GIS ways retain the missing northwestern route and upper Woolwich continuation. Native OS shows Victoria Park Branch, Central/Fork Junction and Stratford Station Low Level. The existing southern connector chord remains a separate route. Exact historical rail levels, turnout arrangement and construction are unresolved.',
        levelEvidence='Interpreted lower formation3.0m at the OS-confirmed underpass, smoothly joining the existing Woolwich station. Existing GE formation8.5m yields4.39m from lower rail head to upper deck soffit; exact historical elevations remain unmeasured.',
        evidenceImages=['reference/footprint-model-alignment/east-channelsea-gis-network-audit.png',
            'reference/footprint-model-alignment/north-london-gis-before-after.png',
            'reference/footprint-model-alignment/north-london-junction-native.png'])
    (ROOT/REGISTER).write_text(json.dumps(raw, indent=2)+'\n')
    print(f'{IDENT}: {reference.length:.1f}m GIS route; exact Woolwich station{j}; {len(water_sources)} water features retained.')


def build_north_london_connection(water, roads, buildings, existing_connector):
    raw = read(REGISTER)
    points = np.array(raw['route'])
    dist = np.r_[0, np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))]
    head = points[1]-points[0]; head /= np.linalg.norm(head)
    # The target is an existing emitted station, so all four rail heads coincide.
    ref = raw['join']['point']
    j = min(range(len(existing_connector['stations'])), key=lambda i: math.dist(existing_connector['stations'][i][:2], ref))
    join = existing_connector['stations'][j]
    points[-1] = join[:2]
    tail = np.array([join[4], -join[3]])
    spline = CubicSpline(dist, points, bc_type=((1, head), (1, tail)), axis=0)
    line = LineString(spline(np.linspace(0, dist[-1], math.ceil(dist[-1]/2)+1)))
    junction_d = line.project(Point(raw['junction']['point']))
    lift = raw.get('canalLift')
    def height(d):
        t = max(0, min(1, (d-junction_d)/(line.length-junction_d)))
        h = raw['junction']['formationHeight']+(join[2]-raw['junction']['formationHeight'])*(.5-.5*math.cos(math.pi*t))
        if lift and d < lift['rampTo']:
            # Over the Hackney Cut (canalLift): held at its formation, then eased back to the traced level.
            u = max(0, min(1, (d-lift['holdTo'])/(lift['rampTo']-lift['holdTo'])))
            h = max(h, lift['formation']+(h-lift['formation'])*(.5-.5*math.cos(math.pi*u)))
        return h
    source_water = unary_union([Polygon(p[0], p[1:]) for p in raw['northernWaterContext']])
    existing_water = water.union(unary_union([Polygon(p[0],p[1:])
        for p in raw['mainlineExtension']['priorNorthernWater']]))
    extra = source_water.difference(existing_water)
    all_water = existing_water.union(source_water)
    if 'canalPassage' in raw:
        # The Hackney Cut under the bridge (no GIS water there): open the embankment over it.
        canal = raw['canalPassage']
        all_water = all_water.union(LineString(canal['route']).buffer(canal['width']/2))
    openings = all_water.buffer(2.5).union(roads.buffer(2))
    crest, base = raw['crestHalfWidth'], raw['baseHalfWidth']
    corridor = line.buffer(crest, cap_style=2)
    obstruction = corridor.intersection(buildings).area
    assert obstruction < .01, f'{IDENT} railway crest intersects buildings: {obstruction:.3f}m²'
    footprint = line.buffer(base, cap_style=2, join_style=2).difference(openings).difference(buildings.buffer(.5))
    stations = []
    for d in np.linspace(0, line.length, math.ceil(line.length/2)+1):
        c = line.interpolate(d); a = line.interpolate(max(0, d-.5)); b = line.interpolate(min(line.length, d+.5))
        dx, dz = b.x-a.x, b.y-a.y; length = math.hypot(dx, dz)
        stations.append([c.x, c.y, height(d), -dz/length, dx/length, float(d)])
    stations[-1][:5] = join[:5]
    def point(s, v):
        return [s[0]+s[3]*v, s[1]+s[4]*v]
    def bank_height(x, z):
        ratio = max(0, min(1, (base-line.distance(Point(x, z)))/(base-crest)))
        return -.09+(height(line.project(Point(x, z)))+.09)*ratio
    mesh = []
    for a, b in zip(stations, stations[1:]):
        for left, right in zip([-base, -crest, 0, crest], [-crest, 0, crest, base]):
            cell = Polygon([point(a, left), point(a, right), point(b, right), point(b, left)]).intersection(footprint)
            for poly in parts(cell):
                for tri in constrained_delaunay_triangles(poly).geoms:
                    mesh.append([[x, round(bank_height(x, z), 3), z] for x, z in list(tri.exterior.coords)[:3]])
    walls = []
    for p in parts(segmentize(footprint, 3)):
        for ring in [p.exterior, *p.interiors]:
            for a, b in zip(ring.coords, list(ring.coords)[1:]):
                ha, hb = bank_height(*a), bank_height(*b)
                if max(ha, hb) > .5:
                    walls.append([[a[0], ha, a[1]], [b[0], hb, b[1]]])
    bridges = []
    for cut in parts(line.intersection(openings), 'LineString'):
        if cut.length < 1:
            continue
        start, end = sorted([line.project(Point(cut.coords[0])), line.project(Point(cut.coords[-1]))])
        bridges.append(dict(start=start, end=end, sewer=False))
    banks = []
    clipping_edge = area_boundary(raw)
    for p in parts(source_water):
        for boundary in [p.exterior, *p.interiors]:
            coords = list(segmentize(LineString(boundary), 2).coords)
            for a, b in zip(coords, coords[1:]):
                mid = Point((a[0]+b[0])/2, (a[1]+b[1])/2)
                # Avoid constructing banks at the rectangle clipping seam or on
                # an already rendered channel edge.
                if mid.distance(clipping_edge) < .01 or mid.distance(existing_water) < .1:
                    continue
                dx, dz = b[0]-a[0], b[1]-a[1]; length = math.hypot(dx, dz)
                if not length:
                    continue
                normal = [-dz/length, dx/length]
                if source_water.covers(Point(mid.x+normal[0]*.1, mid.y+normal[1]*.1)):
                    normal = [-normal[0], -normal[1]]
                banks.append([[a[0], .06, a[1]], [b[0], .06, b[1]],
                    [b[0]+normal[0]*2, 1.65, b[1]+normal[1]*2], [a[0]+normal[0]*2, 1.65, a[1]+normal[1]*2]])
    return dict(raw, detailedRailway=True, route=[[s[0], s[1]] for s in stations],
        stations=stations, embankment=mesh, retainingEdges=walls, bridges=bridges,
        crossings=[], footprint=rings(footprint), northernWater=rings(extra), northernBanks=banks,
        length=line.length, join=dict(raw['join'], stationIndex=j, point=join[:2], height=join[2], normal=join[3:5], chainage=join[5]))


def apply_mainline_crossing(main, newroute, water, roads, buildings):
    """Append the cropped GE end and cut only the OS-confirmed lower passage."""
    raw = read(REGISTER)
    review = raw['mainlineExtension']
    assert main['route'] == review['priorRoute'], 'GE route changed since native junction review'
    assert main['stations'] == review['priorStations'], 'GE stations changed since native junction review'
    assert raw['junction']['status'] == 'native-reviewed-underpass'
    source = LineString(review['sourcePolyline'])
    old = main['stations'][-1]
    source_d = source.project(Point(old[:2]))
    target_d = source_d+review['extensionTargetLength']
    target = source.interpolate(target_d)
    a, b = source.interpolate(target_d-.5), source.interpolate(target_d+.5)
    end_tangent = np.array([b.x-a.x, b.y-a.y]); end_tangent /= np.linalg.norm(end_tangent)
    head_tangent = np.array([old[4], -old[3]])
    length = math.dist(old[:2], list(target.coords)[0])
    spline = CubicHermiteSpline([0, length], [old[:2], list(target.coords)[0]],
        [head_tangent, end_tangent], axis=0)
    extension = LineString(spline(np.linspace(0, length, math.ceil(length/2)+1)))
    added = []
    for d in np.linspace(0, extension.length, math.ceil(extension.length/2)+1)[1:]:
        c = extension.interpolate(d); a = extension.interpolate(max(0, d-.5)); b = extension.interpolate(min(extension.length, d+.5))
        dx, dz = b.x-a.x, b.y-a.y; norm = math.hypot(dx, dz)
        added.append([c.x, c.y, old[2], -dz/norm, dx/norm, old[5]+float(d)])
    stations = main['stations']+added
    main_line = LineString([s[:2] for s in stations])
    low_line = LineString(newroute['route'])
    cross = main_line.intersection(low_line)
    assert cross.geom_type == 'Point', 'Expected one main/low-level crossing'
    # This opening covers the complete lower formation; embankment retains
    # exact unaffected triangles, with only intersecting faces subdivided.
    passage = low_line.buffer(newroute['crestHalfWidth']+2.0, cap_style=2).intersection(cross.buffer(70))
    all_water = water.union(unary_union([Polygon(p[0], p[1:]) for p in newroute['northernWater']+main['northernWater']]))
    openings = all_water.buffer(2.5).union(roads.buffer(2)).union(passage)
    crest, base = main['crestHalfWidth'], main['baseHalfWidth']
    extension_footprint = extension.buffer(base, cap_style=2, join_style=2).difference(openings).difference(buildings.buffer(.5))
    assert extension.buffer(crest, cap_style=2).intersection(buildings).area < .01
    def clip_triangle(triangle, exclusion):
        poly = Polygon([(p[0], p[2]) for p in triangle])
        if poly.intersection(exclusion).area < .000001:
            return [triangle]
        cut = poly.difference(exclusion)
        if cut.is_empty:
            return []
        mat = np.array([[p[0], p[2], 1] for p in triangle])
        coefficients = np.linalg.solve(mat, [p[1] for p in triangle])
        rows = []
        for p in parts(cut):
            for tri in constrained_delaunay_triangles(p).geoms:
                rows.append([[x, float(np.dot([x,z,1], coefficients)), z] for x,z in list(tri.exterior.coords)[:3]])
        return rows
    mesh = [q for triangle in main['embankment'] for q in clip_triangle(triangle, passage)]
    def bank_height(x,z):
        ratio=max(0,min(1,(base-extension.distance(Point(x,z)))/(base-crest)))
        return -.09+(old[2]+.09)*ratio
    segment_stations = [old]+added
    def point(s,v): return [s[0]+s[3]*v,s[1]+s[4]*v]
    for a,b in zip(segment_stations,segment_stations[1:]):
        for left,right in zip([-base,-crest,0,crest],[-crest,0,crest,base]):
            cell=Polygon([point(a,left),point(a,right),point(b,right),point(b,left)]).intersection(extension_footprint)
            for p in parts(cell):
                for tri in constrained_delaunay_triangles(p).geoms:
                    mesh.append([[x,bank_height(x,z),z] for x,z in list(tri.exterior.coords)[:3]])
    walls=[]
    for a,b in main['retainingEdges']:
        line=LineString([(a[0],a[2]),(b[0],b[2])])
        if not line.intersects(passage):
            walls.append([a,b]);continue
        for q in parts(line.difference(passage),'LineString'):
            pair=[]
            for x,z in [q.coords[0],q.coords[-1]]:
                t=line.project(Point(x,z))/line.length
                pair.append([x,a[1]+t*(b[1]-a[1]),z])
            walls.append(pair)
    for p in parts(segmentize(extension_footprint,3)):
        for ring in [p.exterior,*p.interiors]:
            for a,b in zip(ring.coords,list(ring.coords)[1:]):
                # No new retaining end wall across the old/new seam.
                if max(Point(a).distance(Point(old[:2])),Point(b).distance(Point(old[:2]))) < base+1:
                    continue
                ha,hb=bank_height(*a),bank_height(*b)
                if max(ha,hb)>.5:walls.append([[a[0],ha,a[1]],[b[0],hb,b[1]]])
    # Close the newly exposed old/new earth cut with abutment faces. Read
    # their upper edge from the actual clipped triangle planes, so no hollow
    # cut or invented wall height remains at the lower passage.
    old_footprint=unary_union([Polygon(p[0],p[1:]) for p in main['footprint']])
    revised_footprint=old_footprint.difference(passage).union(extension_footprint)
    mesh_polys=[Polygon([(p[0],p[2]) for p in tri]) for tri in mesh]
    tree=STRtree(mesh_polys)
    def cut_height(x,z):
        point=Point(x,z)
        candidates=[int(i) for i in tree.query(point.buffer(.00001)) if mesh_polys[int(i)].distance(point)<.00002]
        if not candidates:
            nearest=int(tree.nearest(point))
            assert mesh_polys[nearest].distance(point)<.05, 'Cut edge beyond sampled bank mesh'
            candidates=[nearest]
        i=min(candidates,key=lambda i:mesh_polys[i].distance(point))
        tri=mesh[i]
        mat=np.array([[p[0],p[2],1] for p in tri])
        coefficients=np.linalg.solve(mat,[p[1] for p in tri])
        return float(np.dot([x,z,1],coefficients))
    abutments=[]
    for p in parts(segmentize(revised_footprint,3)):
        for ring in [p.exterior,*p.interiors]:
            for a,b in zip(ring.coords,list(ring.coords)[1:]):
                edge=LineString([a,b]);mid=edge.interpolate(.5,normalized=True)
                if mid.distance(passage.boundary)<.00001 and edge.length>.00001:
                    pair=[[a[0],cut_height(*a),a[1]],[b[0],cut_height(*b),b[1]]]
                    if max(q[1] for q in pair)>.5:
                        walls.append(pair);abutments.append(pair)
    ranges=[]
    for cut in parts(main_line.intersection(openings),'LineString'):
        if cut.length<1:continue
        start,end=sorted([main_line.project(Point(cut.coords[0])),main_line.project(Point(cut.coords[-1]))])
        if end>old[5] or cut.intersects(passage):ranges.append(dict(start=start,end=end,sewer=False))
    # Coalesce overlapping ranges with the inherited road/water bridges.
    bridges=[]
    for q in sorted(main['bridges']+ranges,key=lambda q:q['start']):
        if bridges and q['start']<=bridges[-1]['end']:
            bridges[-1]['end']=max(bridges[-1]['end'],q['end']);bridges[-1]['sewer'] |= q['sewer']
        else:bridges.append(dict(q))
    metadata=dict(register=REGISTER,railFeatureId=review['railFeatureId'],
        priorRoute=main['route'],priorStations=main['stations'],priorLength=main['length'],
        priorBridgeRanges=main['bridges'],
        addedRoute=[s[:2] for s in added],addedStations=added,
        crossingPoint=list(cross.coords[0]),underpassPolygon=rings(passage),
        lowerRailwayId=newroute['id'],lowerFormationHeight=raw['junction']['formationHeight'],
        upperFormationHeight=old[2],minimumRailheadToSoffit=old[2]-.65-(raw['junction']['formationHeight']+.46),
        evidence=review['evidence'],extensionLength=extension.length,
        addedUnderpassAbutmentEdges=abutments,
        priorEndpointGisOffset=Point(old[:2]).distance(source),
        sourceAlignmentEvidence='Retain the OS-authored GE endpoint and tangent exactly; reconcile its25.885m offset to the generalized GIS within the bounded85m continuation. The new endpoint lies on the supplied GIS centreline.')
    return dict(main,route=[s[:2] for s in stations],stations=stations,length=stations[-1][5],
        embankment=mesh,retainingEdges=walls,bridges=bridges,
        footprint=rings(revised_footprint),
        mainlineExtension=metadata)


def area_boundary(raw):
    return LineString(raw['referenceRoute']).buffer(65, cap_style=2).envelope.boundary


if __name__ == '__main__':
    prepare()
