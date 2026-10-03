"""Compare the author's 1891–96 building footprints with the modelled buildings.

Writes two reports under reference/photo-review-2026-10-03/ (local, ignored):
  footprint-gap-audit.json          every footprint in the district window with its model coverage
  footprint-gaps-started-zones.json the uncovered footprints inside the started zones, attributed to sites

Footprint source: reference/historic-building-footprints-2026-09-28/west-ham-buffer-buildings-bng.geojson.gz
(the project's extract of london_buildings_1891-96_corr_v1.gpkg, EPSG:27700). Coverage is the share of a
footprint's area under any modelled building polygon. Under 30 % counts as uncovered, 30–70 % as partial.

    python3 scripts/footprint_gap_audit.py
"""
import collections
import json
import math
from pathlib import Path

import geopandas as gpd
from shapely.affinity import affine_transform
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'docs/data'
OUT = ROOT / 'reference/photo-review-2026-10-03'
SOURCE = ROOT / 'reference/historic-building-footprints-2026-09-28/west-ham-buffer-buildings-bng.geojson.gz'
E0, N0 = 538900, 183209
WINDOW = (-1650, -1350, 1300, 1600)  # scene metres, the location-map extent
NEIGHBOURHOOD = 60  # metres around modelled buildings that count as "started"


def load(name):
    return json.loads((DATA / name).read_text())


def poly(rings):
    try:
        g = Polygon(rings[0], rings[1:]).buffer(0)
        return g if not g.is_empty else None
    except Exception:
        return None


def rect(b):
    a = -math.radians(b.get('rotation', 0))
    c, s = math.cos(a), math.sin(a)
    w, d = b['width'], b['depth']
    return Polygon([(b['x'] + u * c - v * s, b['z'] + u * s + v * c) for u, v in [(-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2)]])


def model_polygons():
    gp, fb, hs = load('ground-plan.json'), load('factory-buildings.json'), load('housing-detail.json')
    hf, st, sw = load('high-street-frontages.json'), load('abbey-station-plan.json'), load('southwest-context.json')
    n = gp['neighbourhood']
    models = []
    for kind, source in [('factory', fb['buildings']), ('frontage', hf['buildings']), ('station-support', st['supportingBuildings'])]:
        for b in source:
            models += [(kind, b['id'], poly([c['outer'], *c.get('holes', [])])) for c in b['renderPolygons']]
    models.append(('station', 'abbey-mills', poly([st['worldFootprint']])))
    models += [('housing-row', r['id'], poly([r['footprint']])) for r in hs['rows']]
    models += [('housing-rear', p['plotId'], poly([p['footprint']])) for p in hs['extensions'] + hs['privies']]
    models += [('house', h['id'], poly([h['footprint']])) for h in n['houses']]
    models += [('mapped-factory', b['siteId'], poly([b['footprint']]) if b.get('footprint') else rect(b)) for b in n['mappedFactories']]
    models += [('study', b['siteId'], rect(b)) for b in gp['factoryStudies']]
    models += [('southwest-range', b['siteId'], rect(b)) for b in sw['industrialRanges']]
    models.append(('mill', 'abbey-mill', rect(n['mill'])))
    models += [('holder', h['id'], Point(h['x'], h['z']).buffer(h['radius'])) for h in n['holders'] + fb['holders']]
    models = [(k, i, g) for k, i, g in models if g is not None]
    sites = {s['id']: (s['name'], unary_union([poly(r) for r in s['polygons'] if poly(r)])) for s in gp['sites']}
    registered = {s['id'] for s in fb['sites']}
    # Started zones: registered sites plus a neighbourhood around modelled buildings (not the generated rear outbuildings).
    core = [g for k, _, g in models if k not in ('housing-rear',)]
    started = unary_union([sites[i][1] for i in registered if i in sites] + [g.buffer(NEIGHBOURHOOD) for g in core])
    return models, sites, started


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    x0, z0, x1, z1 = WINDOW
    window_bng = box(E0 + x0, N0 - z1, E0 + x1, N0 - z0)
    fp = gpd.read_file(f'/vsigzip/{SOURCE.relative_to(ROOT)}', engine='pyogrio', bbox=tuple(window_bng.bounds))
    to_scene = lambda g: affine_transform(g, [1, 0, 0, -1, -E0, N0])
    models, sites, started = model_polygons()
    model_union = unary_union([g for _, _, g in models])
    site_union = unary_union([g for _, g in sites.values()])
    rows = []
    for _, r in fp.iterrows():
        g = to_scene(r.geometry).buffer(0)
        if g.is_empty or not g.intersects(box(*WINDOW)):
            continue
        rows.append({'sourceFid': int(r['sourceFid']) if r.get('sourceFid') is not None else None, 'class': r.get('buil_class'),
                     'area': round(g.area, 1), 'covered': round(g.intersection(model_union).area / g.area, 3),
                     'industrial': g.intersection(site_union).area / g.area > .5, 'centroid': [round(c, 1) for c in g.centroid.coords[0]],
                     'started': started.contains(g.centroid), 'wkt': g.wkt})
    uncovered = [r for r in rows if r['covered'] < .3]
    partial = [r for r in rows if .3 <= r['covered'] < .7]
    fp_union = unary_union([Polygon() if False else gpd.GeoSeries.from_wkt([r['wkt']])[0] for r in rows]) if rows else Polygon()
    unsupported = []
    for k, i, g in models:
        if not g.intersects(box(*WINDOW)) or k == 'housing-rear':
            continue
        cov = g.intersection(fp_union).area / g.area if g.area else 1
        if cov < .3:
            unsupported.append({'kind': k, 'id': i, 'area': round(g.area), 'footprintSupport': round(cov, 2), 'centroid': [round(c, 1) for c in g.centroid.coords[0]]})
    (OUT / 'footprint-gap-audit.json').write_text(json.dumps({
        'window': WINDOW, 'source': str(SOURCE.relative_to(ROOT)), 'counts': {'footprints': len(rows), 'uncovered': len(uncovered), 'partial': len(partial)},
        'uncovered': sorted(uncovered, key=lambda r: -r['area']), 'partial': partial, 'unsupportedModels': sorted(unsupported, key=lambda r: -r['area'])}, indent=1))
    inside = [r for r in uncovered if r['started']]
    by_site = collections.defaultdict(lambda: {'count': 0, 'areaM2': 0, 'name': ''})
    for r in inside:
        p = Point(*r['centroid'])
        hit = next((i for i, (_, g) in sites.items() if g.contains(p)), None)
        key = str(hit) if hit else 'outside-sites'
        by_site[key]['count'] += 1
        by_site[key]['areaM2'] += r['area']
        by_site[key]['name'] = sites[hit][0] if hit else 'outside industrial sites'
        r['siteId'] = hit
    for v in by_site.values():
        v['areaM2'] = round(v['areaM2'])
    (OUT / 'footprint-gaps-started-zones.json').write_text(json.dumps({
        'startedZoneAreaKm2': round(started.area / 1e6, 2), 'counts': {'uncoveredInStartedZones': len(inside), 'areaM2': round(sum(r['area'] for r in inside)),
        'over100m2': sum(1 for r in inside if r['area'] >= 100)}, 'bySite': dict(sorted(by_site.items(), key=lambda kv: -kv[1]['areaM2'])),
        'uncovered': sorted(inside, key=lambda r: -r['area'])}, indent=1))
    print(f'{len(rows)} footprints in window; {len(uncovered)} uncovered, {len(partial)} partial; {len(inside)} uncovered inside started zones '
          f'({sum(1 for r in inside if r["area"] >= 100)} over 100 m²); {len(unsupported)} model polygons without footprint support.')


if __name__ == '__main__':
    main()
