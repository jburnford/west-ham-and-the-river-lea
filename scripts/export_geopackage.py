"""Export the model's vector data as a GeoPackage in EPSG:27700 (British National Grid).

Every polygon, line and point in docs/data is in the scene frame: metres east (x) and
south (z) of the bridge origin recorded in ground-plan.json. This script converts them
back to eastings and northings and writes one layer per model component so the
reconstruction can be opened in QGIS, joined to other datasets, or deposited.

Attribute columns carry the evidence and source text already held in the data files.
Heights are in metres; where the JSON gives both eaves and ridge they are both kept.

    python3 scripts/export_geopackage.py            # writes exports/gis/west-ham-model-1900.gpkg
    python3 scripts/export_geopackage.py --verify   # also reads every layer back and reports counts
"""
import json
import math
import sys
from pathlib import Path

import geopandas as gpd
import pyogrio
from shapely.geometry import LineString, MultiPolygon, Point, Polygon
from shapely.validation import make_valid

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'docs/data'
OUT = ROOT / 'exports/gis/west-ham-model-1900.gpkg'
CRS = 'EPSG:27700'


def load(name):
    return json.loads((DATA / name).read_text())


GROUND = load('ground-plan.json')
ORIGIN = GROUND['origin']
assert ORIGIN['crs'] == CRS and ORIGIN['axes'] == 'x east; z south; metres', ORIGIN
E0, N0 = ORIGIN['easting'], ORIGIN['northing']


def bng(point):
    """Scene [x, z] (or [x, y, z]) to (easting, northing)."""
    x, z = (point[0], point[2]) if len(point) == 3 else (point[0], point[1])
    return (E0 + x, N0 - z)


def ring(points):
    return [bng(p) for p in points]


def polygon(rings):
    """rings[0] is the outer ring, the rest are holes, in the data files' convention."""
    outer, holes = rings[0], rings[1:]
    if len(outer) < 3:
        return None
    geom = Polygon(ring(outer), [ring(h) for h in holes if len(h) >= 3])
    return geom if geom.is_valid else make_valid(geom)


def multipolygon(polygons):
    """polygons is a list of ring lists. Returns one (Multi)Polygon."""
    parts = [polygon(rings) for rings in polygons]
    parts = [p for p in parts if p is not None and not p.is_empty]
    if not parts:
        return None
    flat = []
    for p in parts:
        flat.extend(p.geoms if hasattr(p, 'geoms') else [p])
    flat = [g for g in flat if g.geom_type == 'Polygon']
    return flat[0] if len(flat) == 1 else MultiPolygon(flat)


def render_polygons(components):
    """[{outer:[...], holes:[[...]]}] to a (Multi)Polygon."""
    return multipolygon([[c['outer'], *c.get('holes', [])] for c in components])


def line(points):
    pts = [bng(p) for p in points]
    return LineString(pts) if len(pts) >= 2 else None


ROTATION_SIGN = None


def rectangle(x, z, width, depth, rotation=0.0):
    """Rotated rectangle footprint. The sign convention is calibrated against rows that carry both
    a footprint and a rotation, so this never silently mirrors the model."""
    a = math.radians(rotation or 0.0) * ROTATION_SIGN
    c, s = math.cos(a), math.sin(a)
    corners = [(-width / 2, -depth / 2), (width / 2, -depth / 2), (width / 2, depth / 2), (-width / 2, depth / 2)]
    return Polygon([bng((x + u * c - v * s, z + u * s + v * c)) for u, v in corners])


def calibrate_rotation(rows):
    global ROTATION_SIGN
    best = None
    for sign in (1, -1):
        ROTATION_SIGN = sign
        worst = 0.0
        for r in rows:
            if not r.get('footprint') or len(r['footprint']) != 4:
                continue
            rect = list(rectangle(r['x'], r['z'], r['width'], r['depth'], r.get('rotation', 0)).exterior.coords)[:4]
            given = ring(r['footprint'])
            err = min(max(math.dist(p, q) for p, q in zip(rect, given[k:] + given[:k])) for k in range(4))
            err = min(err, min(max(math.dist(p, q) for p, q in zip(rect, (given[k:] + given[:k])[::-1])) for k in range(4)))
            worst = max(worst, err)
        if best is None or worst < best[1]:
            best = (sign, worst)
    ROTATION_SIGN, worst = best
    if worst > 0.5:
        raise SystemExit(f'Could not calibrate the rectangle rotation convention (worst corner error {worst:.2f} m)')
    return worst


def scalar(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return json.dumps(value)


def frame(records, geometry_key='geometry'):
    rows = [r for r in records if r.get(geometry_key) is not None and not r[geometry_key].is_empty]
    if not rows:
        return None
    attrs = [{k: scalar(v) for k, v in r.items() if k != geometry_key} for r in rows]
    return gpd.GeoDataFrame(attrs, geometry=[r[geometry_key] for r in rows], crs=CRS)


def write(layer, records, written):
    gdf = frame(records)
    if gdf is None:
        print(f'  {layer}: nothing to write')
        return
    gdf.to_file(OUT, layer=layer, driver='GPKG', engine='pyogrio', mode='a' if OUT.exists() else 'w')
    written[layer] = len(gdf)
    print(f'  {layer}: {len(gdf)} features')


def pick(record, *keys):
    return {k: record.get(k) for k in keys if k in record}


BUILDING_FIELDS = ('id', 'siteId', 'name', 'source', 'mapReference', 'material', 'roof', 'roofMaterial', 'roofAxis', 'roofBays',
                   'roofRise', 'storeys', 'storeysEstimate', 'height', 'eavesHeight', 'baseHeight', 'floorMark', 'streetFrontage',
                   'footprintSource', 'footprintEvidence', 'heightEvidence', 'roofEvidence', 'evidence', 'areaM2', 'renderAreaM2')


def building_record(b, site_names=None):
    rec = pick(b, *BUILDING_FIELDS)
    if site_names and b.get('siteId') in site_names:
        rec['siteName'] = site_names[b['siteId']]
    if b.get('renderPolygons'):
        rec['geometry'] = render_polygons(b['renderPolygons'])
    elif b.get('footprint'):
        rec['geometry'] = polygon([b['footprint']])
    else:
        rec['geometry'] = rectangle(b['x'], b['z'], b['width'], b['depth'], b.get('rotation', 0))
    return rec


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if OUT.exists():
        OUT.unlink()
    written = {}
    housing = load('housing-detail.json')
    worst = calibrate_rotation(housing['rows'])
    print(f'Rectangle rotation convention calibrated on housing rows (worst corner error {worst:.3f} m, sign {ROTATION_SIGN})')

    n = GROUND['neighbourhood']
    write('scene_origin', [{'easting': E0, 'northing': N0, 'note': 'Scene origin: approximate listed grid reference of the Northern Outfall Sewer bridge; scene x east, z south in metres',
                            'geometry': Point(E0, N0)}], written)

    # Mapped GIS outlines.
    write('industrial_sites', [{**pick(s, 'id', 'name'), 'geometry': multipolygon(s['polygons'])} for s in GROUND['sites']], written)
    write('rivers_gis', [{**pick(r, 'id', 'name'), 'geometry': multipolygon(r['polygons'])} for r in GROUND['rivers']], written)

    # Buildings.
    fb = load('factory-buildings.json')
    site_names = {s['id']: s['name'] for s in fb['sites']}
    write('factory_sites_registered', [{**pick(s, 'id', 'name', 'coverage', 'notes', 'buildingCount'), 'sources': scalar(s.get('sources')),
                                        'geometry': multipolygon(next((g['polygons'] for g in GROUND['sites'] if g['id'] == s['id']), []))} for s in fb['sites']], written)
    write('factory_buildings', [building_record(b, site_names) for b in fb['buildings']], written)
    hsf = load('high-street-frontages.json')
    write('high_street_frontages', [building_record(b) for b in hsf['buildings']], written)
    station = load('abbey-station-plan.json')
    write('abbey_mills_station', [{'name': 'Abbey Mills pumping station, main building envelope', 'source': station['source'], 'evidence': station['evidence'],
                                   'geometry': polygon([station['worldFootprint']])}]
          + [{'name': f"Abbey Mills chimney {i + 1}", 'sourceFid': c['sourceFid'], 'geometry': polygon([c['worldFootprint']])} for i, c in enumerate(station['chimneys'])]
          + [building_record(b) for b in station['supportingBuildings']], written)
    write('station_access_paths', [{**pick(p, 'name', 'width', 'kind', 'surface', 'evidence', 'sheet', 'surfaceEvidence'), 'geometry': line(p['points'])} for p in station['accessPaths']], written)
    surveyed = {s['id'] for s in fb['sites']}
    studies = [{**pick(b, 'siteId', 'name', 'height', 'evidence', 'sourceSheet'), 'kind': 'factory study', 'supersededByRegistered': b['siteId'] in surveyed,
                'geometry': rectangle(b['x'], b['z'], b['width'], b['depth'], b.get('rotation', 0))} for b in GROUND['factoryStudies']]
    studies += [{**pick(b, 'siteId', 'name', 'height', 'evidence', 'sourceSheet'), 'kind': 'OS-mapped factory range', 'supersededByRegistered': b['siteId'] in surveyed,
                 'geometry': polygon([b['footprint']]) if b.get('footprint') else rectangle(b['x'], b['z'], b['width'], b['depth'], b.get('rotation', 0))} for b in n['mappedFactories']]
    sw = load('southwest-context.json')
    studies += [{**pick(b, 'siteId', 'name', 'height', 'evidence'), 'kind': 'southwest industrial range', 'supersededByRegistered': b['siteId'] in surveyed,
                 'geometry': rectangle(b['x'], b['z'], b['width'], b['depth'], b.get('rotation', 0))} for b in sw['industrialRanges']]
    write('factory_study_envelopes', studies, written)
    mill = n['mill']
    write('abbey_mill', [{**pick(mill, 'name', 'siteId', 'height', 'evidence'), 'geometry': rectangle(mill['x'], mill['z'], mill['width'], mill['depth'], mill.get('rotation', 0))}], written)

    # Housing.
    write('housing_rows', [{**pick(r, 'id', 'street', 'group', 'wallHeight', 'bays', 'sourceSheet', 'evidence', 'width', 'depth'),
                            'geometry': polygon([r['footprint']])} for r in housing['rows']], written)
    write('housing_plots', [{**pick(p, 'id', 'rowId', 'bay', 'areaM2'), 'geometry': multipolygon(p['polygons'])} for p in housing['plots']], written)
    write('housing_forecourts', [{**pick(p, 'rowId'), 'geometry': multipolygon(p['polygons'])} for p in housing['forecourts']], written)
    write('housing_rear_extensions', [{**pick(p, 'plotId', 'rowId', 'height'), 'geometry': polygon([p['footprint']])} for p in housing['extensions']], written)
    write('housing_privies', [{**pick(p, 'plotId', 'rowId', 'height'), 'geometry': polygon([p['footprint']])} for p in housing['privies']], written)
    write('housing_plot_walls', [{'geometry': line(w)} for w in housing['walls']], written)
    write('abbey_lane_houses', [{**pick(h, 'id', 'sourceSheet', 'wallHeight', 'evidence'), 'geometry': polygon([h['footprint']])} for h in n['houses']], written)

    # Gas holders and factory structures.
    holders = [{**pick(h, 'id', 'siteId', 'radius', 'height', 'columns', 'bellHeight', 'evidence', 'source'), 'group': 'neighbourhood',
                'geometry': Point(bng((h['x'], h['z']))).buffer(h['radius'], 32)} for h in n['holders']]
    holders += [{**pick(h, 'id', 'siteId', 'radius', 'height', 'columns', 'bellHeight', 'evidence', 'source'), 'group': 'registered factory',
                 'geometry': Point(bng((h['x'], h['z']))).buffer(h['radius'], 32)} for h in fb['holders']]
    write('gas_holders', holders, written)
    write('factory_structures', [{**pick(s, 'id', 'siteId', 'kind', 'count', 'rotation', 'radius', 'height', 'baseHeight', 'section', 'material',
                                         'mappedHeightFeet', 'topRadiusRatio', 'source', 'evidence'),
                                  'siteName': site_names.get(s.get('siteId')),
                                  'geometry': Point(bng((s['x'], s['z'])))} for s in fb['structures']], written)

    # Transport and the sewer.
    infra = load('infrastructure.json')
    write('roads', [{**pick(r, 'name', 'sheet', 'width', 'kind', 'surface', 'surfaceEvidence', 'alignmentEvidence'), 'geometry': line(r['route'])} for r in infra['roads']], written)
    write('road_bridges', [{**pick(b, 'id', 'name', 'height', 'width', 'surface', 'style', 'archCount', 'provisional', 'evidence'), 'geometry': line(b['route'])} for b in infra['roadBridges']], written)
    write('railways', [{**pick(r, 'name', 'tracks', 'formationHeight', 'evidence', 'detailedMainline', 'detailedRailway'), 'geometry': line(r['route'])} for r in infra['railways']], written)
    write('railway_crossings', [{'railway': r['name'], 'geometry': line(c)} for r in infra['railways'] for c in r.get('crossings', []) if len(c) >= 2], written)
    sewer = n['sewer']
    write('northern_outfall_sewer', [{**pick(sewer, 'crestWidth', 'baseWidth', 'height', 'evidence', 'alignmentEvidence', 'sheet'), 'geometry': line(sewer['route'])}], written)

    # Water.
    rn = load('river-network.json')
    write('marsh_ditches', [{**pick(d, 'id', 'width', 'retainedAreaM2'), 'geometry': multipolygon(d['renderPolygons'])} for d in rn['marshDitches']['features']], written)
    write('marsh_polygons_1900', [{'levels': scalar(rn['marshDitches']['levels']), 'geometry': multipolygon([rings])} for rings in rn['marshDitches']['marshPolygons']], written)
    write('river_connections_reviewed', [{**pick(c, 'id', 'category', 'visualWidthMetres', 'widthStatus', 'bedSceneY', 'bedStatus', 'tidalDisplay'),
                                          'channelIds': scalar(c.get('channelIds')), 'evidence': scalar(c.get('evidence')),
                                          'geometry': multipolygon(c['polygons'])} for c in rn['reviewedConnections']['connections']], written)
    write('tidal_water_extent', [{'low': rn['tide']['low'], 'high': rn['tide']['high'], 'evidence': rn['tide']['evidence'], 'geometry': multipolygon([rings])} for rings in rn['tide']['polygons']], written)
    write('retaining_edges', [{'crestHeight': rn['retainingEdges']['crestHeight'], 'baseHeight': rn['retainingEdges']['baseHeight'], 'width': rn['retainingEdges']['width'],
                               'evidence': rn['retainingEdges']['evidence'], 'geometry': line(r)} for r in rn['retainingEdges']['routes']], written)
    rs = load('river-system-1900.json')
    write('river_system_reaches', [{**pick(r, 'id', 'name', 'role'), 'provenance': scalar(r.get('provenance')), 'epoch': rs['epoch'],
                                    'geometry': multipolygon(r['polygons'])} for r in rs['reaches']], written)
    write('river_system_water', [{'epoch': rs['epoch'], 'waterLevelSceneY': rs['waterLevel'], 'geometry': multipolygon([rings])} for rings in rs['waterPolygons']], written)

    # Yards, gardens, trees.
    fy = load('factory-yards.json')
    write('factory_yards', [{**pick(s, 'id', 'surface', 'areaM2'), 'siteName': site_names.get(s.get('id')), 'geometry': multipolygon(s['polygons'])} for s in fy['sites']], written)
    write('yard_tracks', [{**pick(t, 'id', 'gauge', 'kind', 'evidence'), 'geometry': line(t['points'])} for t in fy['tracks']], written)
    garden = n['garden']
    write('allotment_garden', [{'cultivableAreaM2': garden['cultivableAreaM2'], 'evidence': garden['evidence'], 'layoutEvidence': garden['layoutEvidence'],
                                'geometry': polygon([garden['footprint']])}], written)
    write('allotment_beds', [{'geometry': rectangle(b['x'], b['z'], b['width'], b['depth'], b.get('rotation', 0))} for b in garden['beds']], written)
    trees = load('mapped-trees.json')
    write('mapped_trees', [{**pick(t, 'id', 'group', 'height', 'crownRadius'), 'source': trees['source'], 'datePolicy': trees['datePolicy'],
                            'geometry': Point(bng((t['x'], t['z'])))} for t in trees['trees']], written)

    total = sum(written.values())
    print(f'Wrote {len(written)} layers, {total} features, to {OUT.relative_to(ROOT)}')
    if '--verify' in sys.argv:
        layers = pyogrio.list_layers(OUT)
        assert len(layers) == len(written), (len(layers), len(written))
        for name, _ in layers:
            gdf = gpd.read_file(OUT, layer=name, engine='pyogrio')
            assert len(gdf) == written[name], name
            assert gdf.crs.to_epsg() == 27700, name
            bad = (~gdf.geometry.is_valid).sum()
            if bad:
                print(f'  warning: {name} has {bad} invalid geometries')
        origin_layer = gpd.read_file(OUT, layer='scene_origin', engine='pyogrio')
        assert tuple(origin_layer.geometry[0].coords[0]) == (E0, N0)
        print(f'Verified {len(layers)} layers read back with matching counts and EPSG:27700.')


if __name__ == '__main__':
    main()
