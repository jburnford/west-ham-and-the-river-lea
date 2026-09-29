"""Convert vision readings of OS five-foot height annotations to points and
compare them with the EPFL text-spotting sample.

Inputs
  reference/spot-heights/readings/<mosaic>.json   one file per mosaic read
  reference/spot-heights/mosaics/<mosaic>.json    sidecar with the tile origin
  EPFL layer (EPSG:27700), default path below, override with --epfl

Outputs
  reference/spot-heights/readings.geojson   WGS84 points, one per distinct
      annotation (readings of the same mark from overlapping mosaics are
      merged), with bng_e / bng_n, value, type, confidence, views
  reference/spot-heights/evaluation.json    the comparison, machine readable
  a compact table on stdout

Matching: every EPFL label containing a digit whose centroid falls inside a
mosaic that was read is matched to the nearest merged reading within 12 m of
the label centroid; failing that, within 12 m of the label polygon (bench-mark
pheons sit well away from the centre of their long text).
Values are compared as written, then with the decimal point re-inserted
(EPFL often drops it: '2450' -> 24.50, '64' -> 6.4).

Only five-foot material is evaluated: m18_* readings and mosaics, and in
--heights mode the marks whose layers include the five-foot (q18_* 25-inch
and s18_* 1848-51 marks are skipped, since EPFL spotted the five-foot sheets).

--heights [PATH] evaluates the multi-reader merge instead
(reference/spot-heights/heights.geojson from spot_height_merge.py) over every
mosaic listed in its mosaics_read, with the same matching logic. It writes
evaluation_heights.json (or --out) and leaves readings.geojson and
evaluation.json untouched. A disputed mark also counts as agreeing when EPFL
matches one of its alternative values (reported in the note).
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

import geopandas as gpd
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).resolve().parent))
from spot_height_mosaics import (FROM_BNG, TO_BNG, DEFAULT_LAYER, lonlat_to_global_pixel,  # noqa: E402
                                 mosaic_dir, pixel_to_coords)

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'reference/spot-heights'
EPFL = Path('/mnt/c/Users/jic823/Dropbox/2026/10k_text_london_OS_1890s.geojson')
MATCH_M = 12.0
MERGE_M = 6.0


def load_readings():
    """Five-foot (m18_*) readings only: the EPFL sample spots the 1890s five-foot sheets."""
    rows = []
    for path in sorted((BASE / 'readings').glob('*.json')):
        if not path.name.startswith('m'):
            continue
        doc = json.loads(path.read_text())
        meta = json.loads((mosaic_dir(doc['mosaic']) / f"{doc['mosaic']}.json").read_text())
        for i, r in enumerate(doc['readings']):
            c = pixel_to_coords(meta, r['px'] + 0.5, r['py'] + 0.5)
            rows.append({**r, 'mosaic': doc['mosaic'], 'idx': i, **c})
    return rows


def mosaic_footprint(name: str) -> Polygon:
    meta = json.loads((mosaic_dir(name) / f'{name}.json').read_text())
    w, h = meta['width_px'], meta['height_px']
    ring = []
    for px, py in [(0, 0), (w / 2, 0), (w, 0), (w, h / 2), (w, h), (w / 2, h), (0, h), (0, h / 2)]:
        c = pixel_to_coords(meta, px, py)
        ring.append((c['bng_e'], c['bng_n']))
    return Polygon(ring)


def merge(rows):
    """Greedy merge of readings of the same mark seen in overlapping mosaics."""
    order = {'high': 0, 'medium': 1, 'low': 2}
    rows = sorted(rows, key=lambda r: order[r['confidence']])
    clusters = []
    for r in rows:
        best = None
        for c in clusters:
            if c['type'] != r['type']:
                continue
            d = math.hypot(c['bng_e'] - r['bng_e'], c['bng_n'] - r['bng_n'])
            if d <= MERGE_M and (best is None or d < best[0]):
                best = (d, c)
        if best:
            c = best[1]
            c['views'].append(r)
        else:
            clusters.append({'type': r['type'], 'bng_e': r['bng_e'], 'bng_n': r['bng_n'], 'views': [r]})
    out = []
    for k, c in enumerate(clusters):
        v = c['views']
        e = sum(x['bng_e'] for x in v) / len(v)
        n = sum(x['bng_n'] for x in v) / len(v)
        spread = max(math.hypot(x['bng_e'] - e, x['bng_n'] - n) for x in v)
        values = sorted({x['value_ft'] for x in v})
        lead = v[0]  # highest-confidence view
        lon, lat = FROM_BNG.transform(e, n)
        out.append({
            'id': f'sh{k:03d}', 'type': c['type'], 'value_ft': lead['value_ft'], 'raw': lead['raw'],
            'confidence': lead['confidence'] if len(values) == 1 else 'low',
            'bng_e': round(e, 2), 'bng_n': round(n, 2), 'lon': lon, 'lat': lat,
            'n_views': len(v), 'view_spread_m': round(spread, 2),
            'value_conflict': values if len(values) > 1 else None,
            'mosaics': [f"{x['mosaic']}@{x['px']},{x['py']}" for x in v],
            'notes': lead['notes'],
        })
    return out


NUM = re.compile(r'\d+(?:[.·]\d+)?')


def candidate_values(label: str):
    """(value, how) pairs a label could stand for."""
    out = []
    for tok in NUM.findall(label):
        tok = tok.replace('·', '.')
        out.append((float(tok), 'as written'))
        if '.' not in tok:
            if len(tok) >= 2:
                out.append((int(tok) / 10, 'decimal restored (1 dp)'))
            if len(tok) >= 3:
                out.append((int(tok) / 100, 'decimal restored (2 dp)'))
        else:
            digits = tok.replace('.', '')
            if len(digits) >= 3:  # decimal in the wrong place
                out.append((int(digits) / 100, 'decimal moved (2 dp)'))
                out.append((int(digits) / 10, 'decimal moved (1 dp)'))
    return out


def compare(merged, footprint, epfl_path: Path):
    g = gpd.read_file(epfl_path)
    if g.crs is None or g.crs.to_epsg() != 27700:
        g = g.to_crs(27700)
    g = g[g['label'].astype(str).str.contains(r'\d')].copy()
    g['cent'] = g.geometry.centroid
    g = g[g['cent'].within(footprint)]
    used = set()
    rows = []
    for _, lab in g.sort_values('id').iterrows():
        cx, cy = lab['cent'].x, lab['cent'].y
        best, basis = None, 'centroid'
        for m in merged:
            d = math.hypot(m['bng_e'] - cx, m['bng_n'] - cy)
            if d <= MATCH_M and (best is None or d < best[0]):
                best = (d, m)
        if best is None:
            # A bench-mark pheon can sit 15-20 m from the centre of its long
            # 'B.M.xx.xx' text, so fall back to distance from the text box.
            for m in merged:
                d = lab.geometry.distance(Point(m['bng_e'], m['bng_n']))
                if d <= MATCH_M and (best is None or d < best[0]):
                    best, basis = (d, m), 'text box'
        row = {'epfl_id': int(lab['id']), 'epfl_label': lab['label'],
               'epfl_e': round(cx, 1), 'epfl_n': round(cy, 1)}
        if best is None:
            # nearest reading at any distance, for diagnosis
            near = min(merged, key=lambda m: math.hypot(m['bng_e'] - cx, m['bng_n'] - cy))
            dn = math.hypot(near['bng_e'] - cx, near['bng_n'] - cy)
            row.update(category='c', note=f"nearest reading {near['raw']} at {dn:.1f} m")
        else:
            _, m = best
            used.add(m['id'])
            d = math.hypot(m['bng_e'] - cx, m['bng_n'] - cy)
            poly_d = lab.geometry.distance(Point(m['bng_e'], m['bng_n']))
            row.update(reading_id=m['id'], reading=m['raw'], reading_value=m['value_ft'],
                       dist_m=round(d, 1), dist_to_polygon_m=round(poly_d, 1), match_basis=basis)
            how = None
            for val, h in candidate_values(str(lab['label'])):
                if abs(val - m['value_ft']) < 1e-6:
                    how = h
                    break
            alt = None
            if how != 'as written' and m.get('values'):
                for val, h in candidate_values(str(lab['label'])):
                    hit = next((v for v in m['values'] if abs(val - v) < 1e-6), None)
                    if hit is not None and h == 'as written':
                        alt = hit
                        break
            if alt is not None:
                row.update(category='a', note=f"value agrees with disputed alternative {alt} "
                                              f"(merge chose {m['value_ft']})")
            elif how == 'as written':
                row.update(category='a', note='value agrees')
            elif how:
                row.update(category='b', note=f'agrees only with {how} -> likely dropped/misplaced decimal')
            else:
                row.update(category='b', note='value disagrees')
            if basis != 'centroid':
                row['note'] += f' [matched on text box, {poly_d:.1f} m]'
        rows.append(row)
    unmatched = [m for m in merged if m['id'] not in used]
    return rows, unmatched


def load_heights(path: Path):
    """heights.geojson (spot_height_merge.py) -> merged-style dicts + mosaics read."""
    gj = json.loads(path.read_text())
    merged = []
    skipped = 0
    for f in gj['features']:
        p = f['properties']
        if DEFAULT_LAYER not in p.get('layers', [p.get('layer', DEFAULT_LAYER)]):
            skipped += 1  # 25-inch-only or 1848-51 skeleton mark: not on the sheets EPFL spotted
            continue
        lon, lat = f['geometry']['coordinates']
        merged.append({
            'id': p['id'], 'type': p['type'], 'value_ft': p['value_ft'], 'raw': p['raw'],
            'confidence': p['confidence'], 'bng_e': p['bng_e'], 'bng_n': p['bng_n'], 'lon': lon, 'lat': lat,
            'n_views': p['n_readings'], 'view_spread_m': p.get('spread_m', 0.0),
            'value_conflict': p.get('values') if p.get('disputed') else None,
            'values': p.get('values') if p.get('disputed') else None,
            'readers': p.get('readers', []), 'mosaics': p.get('mosaics', []), 'notes': p.get('notes', ''),
        })
    mosaics = gj.get('mosaics_read') or sorted({m for x in merged for m in x['mosaics']})
    others = [m for m in mosaics if not m.startswith('m')]
    mosaics = [m for m in mosaics if m.startswith('m')]
    if skipped or others:
        print(f'{path.name}: evaluating five-foot marks only; ignored {skipped} mark(s) seen only on other '
              f'layers and {len(others)} non-five-foot mosaic(s)')
    return merged, mosaics, gj


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--epfl', type=Path, default=EPFL)
    ap.add_argument('--heights', nargs='?', type=Path, const=BASE / 'heights.geojson', default=None,
                    metavar='PATH', help='evaluate the multi-reader merge (default path heights.geojson)')
    ap.add_argument('--out', type=Path, default=None,
                    help='with --heights: evaluation output (default evaluation_heights.json)')
    args = ap.parse_args()

    heights_mode = args.heights is not None
    if heights_mode:
        merged, mosaics, gj = load_heights(args.heights)
        raw = None
    else:
        raw = load_readings()
        mosaics = sorted({r['mosaic'] for r in raw})
        merged = merge(raw)
    footprint = unary_union([mosaic_footprint(m) for m in mosaics])

    # --- landmark check -------------------------------------------------
    meta = json.loads((BASE / 'mosaics/m18_131069_87140.json').read_text())
    ps = pixel_to_coords(meta, 490, 540)  # centre of the drawn Abbey Mills Pumping Station
    print(f"Landmark: Abbey Mills Pumping Station drawn at m18_131069_87140 px 490,540 -> "
          f"BNG {ps['bng_e']:.0f} {ps['bng_n']:.0f}; lon/lat {ps['lon']:.5f} {ps['lat']:.5f}")
    wd_lon, wd_lat = -(2.9 / 3600), 51 + 31 / 60 + 50.5 / 3600  # Wikidata Q4664040 P625
    we, wn = TO_BNG.transform(wd_lon, wd_lat)
    gx, gy = lonlat_to_global_pixel(wd_lon, wd_lat, 18)
    print(f"          Wikidata P625 -> BNG {we:.0f} {wn:.0f}, mosaic px "
          f"{gx - meta['tile_x0'] * 256:.0f},{gy - meta['tile_y0'] * 256:.0f} "
          f"(offset {math.hypot(we - ps['bng_e'], wn - ps['bng_n']):.0f} m, site-level coordinate)")

    # --- geojson ----------------------------------------------------------
    if not heights_mode:
        feats = []
        for m in merged:
            props = {k: v for k, v in m.items() if k not in ('lon', 'lat')}
            feats.append({'type': 'Feature', 'properties': props,
                          'geometry': {'type': 'Point', 'coordinates': [round(m['lon'], 7), round(m['lat'], 7)]}})
        gj = {'type': 'FeatureCollection', 'name': 'os-five-foot-1893-height-readings',
              'crs_note': 'WGS84 lon/lat; bng_e/bng_n are EPSG:27700; heights in feet above Ordnance Datum (Liverpool)',
              'features': feats}
        (BASE / 'readings.geojson').write_text(json.dumps(gj, indent=1, ensure_ascii=False))

    # --- summary of readings --------------------------------------------
    by_type = {}
    for m in merged:
        by_type.setdefault(m['type'], []).append(m['value_ft'])
    if heights_mode:
        n_raw = sum(m['n_views'] for m in merged)
        readers = sorted({r for m in merged for r in m['readers']})
        print(f"\n{args.heights.name}: {n_raw} readings from {len(mosaics)} mosaics (readers {', '.join(readers)}) "
              f"-> {len(merged)} distinct marks")
    else:
        n_raw = len(raw)
        print(f"\n{len(raw)} readings from {len(mosaics)} mosaics -> {len(merged)} distinct annotations")
    for t, vals in sorted(by_type.items()):
        print(f"  {t:11s} n={len(vals):3d}  range {min(vals):5.2f} - {max(vals):5.2f} ft")
    multi = [m for m in merged if m['n_views'] > 1]
    if multi:
        spreads = sorted(m['view_spread_m'] for m in multi)
        what = 'seen more than once' if heights_mode else 'seen in >1 mosaic'
        print(f"  {what}: {len(multi)}; position spread median {spreads[len(spreads) // 2]:.1f} m, "
              f"max {spreads[-1]:.1f} m")
    conflicts = [m for m in merged if m['value_conflict']]
    for m in conflicts:
        print(f"  value conflict between views: {m['id']} {m['value_conflict']}")

    # --- comparison -----------------------------------------------------
    rows, unmatched = compare(merged, footprint, args.epfl)
    print(f"\nEPFL labels with digits inside the {len(mosaics)} mosaics read: {len(rows)}")
    print(f"{'cat':3s} {'epfl_id':>7s} {'EPFL label':26s} {'reading':12s} {'d_m':>5s}  note")
    for r in sorted(rows, key=lambda r: (r['category'], r['epfl_id'])):
        print(f"{r['category']:3s} {r['epfl_id']:7d} {r['epfl_label'][:26]:26s} "
              f"{r.get('reading', '-'):12s} {r.get('dist_m', float('nan')):5.1f}  {r['note']}")
    counts = {c: sum(1 for r in rows if r['category'] == c) for c in 'abc'}
    print(f"\n(a) matched, value agrees: {counts['a']}   (b) matched, value differs: {counts['b']}   "
          f"(c) EPFL label, no reading: {counts['c']}   (d) readings with no EPFL label: {len(unmatched)}")

    out = (args.out or BASE / 'evaluation_heights.json') if heights_mode else BASE / 'evaluation.json'
    doc = {
        'mosaics_read': mosaics, 'n_readings': n_raw, 'n_distinct': len(merged),
        'match_radius_m': MATCH_M, 'merge_radius_m': MERGE_M,
        'epfl_rows': rows, 'unmatched_readings': [m['id'] for m in unmatched],
        'counts': {**counts, 'd': len(unmatched)},
    }
    if heights_mode:
        doc['source'] = str(args.heights)
    out.write_text(json.dumps(doc, indent=1, ensure_ascii=False))


if __name__ == '__main__':
    main()
