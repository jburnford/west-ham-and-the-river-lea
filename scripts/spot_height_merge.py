"""Merge every reader's spot-height readings into one QA'd point layer.

Inputs
  reference/spot-heights/readings/<mosaic>.json           legacy, reader opus-a
  reference/spot-heights/readings/<mosaic>.<reader>.json  one file per reader
  reference/spot-heights/mosaics/<mosaic>.json            sidecars (georeference), m18_* five-foot
  reference/spot-heights/mosaics-25inch/<mosaic>.json     q18_* 25-inch (1:2500) 1893-96
  reference/spot-heights/mosaics-1848/<mosaic>.json       s18_* 1:5,280 skeleton survey 1848-51
  (--readings-dir DIR reads another folder instead of readings/, --extra FILE...
  adds files; both then require explicit --out and --report.)

Outputs
  reference/spot-heights/heights.geojson   WGS84 points, one per distinct mark
  reference/spot-heights/qa_report.md      inter-reader agreement and checks

Setting. Every mark carries setting (closed vocabulary in spot_height_setting.py:
marsh, open_ground, street, yard, embankment_top, embankment_foot, wall_top,
bridge, railway, building, water, other), setting_source ('reader' when any
reading of the mark gives a valid setting, else 'inferred' from the notes by
spot_height_setting.infer_setting, else 'unknown' with setting null) and
setting_conflict (true when the readings of that source disagree; the majority
wins, ties go to the best-confidence reading). Marks whose inferred setting
rests only on the value (notes say just "open ground": below 15 ft marsh,
otherwise open_ground) also carry setting_rule: "value_fallback". Reading files
are never modified.

Clustering. Readings (mosaic px -> EPSG:27700 via the sidecar) are grouped
when they have the same type, lie within 6 m of a reading already in the
cluster and agree in
value (identical, or within 0.15 ft). Two readings from the same file are never
merged (a reader listing two marks means two marks). A second pass then joins
any clusters of the same type within 6 m whose values disagree by more than
0.15 ft, provided they came from different files: that is one mark read two
ways, and the result is flagged disputed: true with all values listed.

Layers. The folder and layer come from the mosaic prefix (spot_height_mosaics.
mosaic_dir / LAYERS). Readings are only ever clustered within one survey epoch:
m18 five-foot and q18 25-inch (both the 1890s levelling) may form one mark;
s18 1848-51 skeleton readings never join either, even at the same spot, and
their marks get ids sk_E_N (1890s marks keep sh_E_N). Within a layer values
agree within 0.15 ft; across layers the coarser layer's rounding is allowed
(max(0.15, half a unit of the fewer decimal places): a whole-foot 25-inch 8
agrees with a five-foot 8.3, 9 does not). Each mark carries layer (that of the
winning reading; five-foot first on ties), layers, scale and survey_dates;
datum and source come from the winning reading's sidecar, except that
five-foot marks keep 'OD Liverpool' / 'OS 1:1056 London 1891-96 via NLS'.
Decimal places are checked per layer (five-foot spot 1 / B.M. 2; 25-inch spot
0 / B.M. 1; skeleton spot 1 / B.M. 1), and raw must spell value_ft ('?' stands
for a doubtful digit; a trailing '?' may also just flag doubt).
"""
from __future__ import annotations

import argparse
import json
import math
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from spot_height_mosaics import (DEFAULT_LAYER, FROM_BNG, LAYERS, meta_info, mosaic_dir,  # noqa: E402
                                 pixel_to_coords)

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'reference/spot-heights'
LEGACY_READER = 'opus-a'
MERGE_M = 6.0
VALUE_TOL = 0.15
RANGE = (0.0, 120.0)  # Lea valley 0-50; gravel terrace (Forest Gate, Leytonstone, Wanstead Flats) to ~100
CONF = {'high': 0, 'medium': 1, 'low': 2}
NAME = re.compile(r'^([mqs]\d+_\d+_\d+)(?:\.([A-Za-z0-9_-]+))?\.json$')
SKELETON_LAYER = 'os-london-skeleton-5280'
# primary-layer preference when one mark is seen on several layers (finest scale first)
LAYER_ORDER = {DEFAULT_LAYER: 0, 'os-25-inch-london': 1, SKELETON_LAYER: 2}
LAYER_SHORT = {DEFAULT_LAYER: 'five-foot', 'os-25-inch-london': '25-inch', SKELETON_LAYER: 'skeleton 1848-51'}
# five-foot marks keep exactly the strings heights.geojson has always carried
FIVE_FOOT_DATUM = 'OD Liverpool'
FIVE_FOOT_SOURCE = 'OS 1:1056 London 1891-96 via NLS'


def layer_decimals(layer: str) -> dict:
    """{'spot': dp, 'bench_mark': dp} for a layer (five-foot rules for unknown layers)."""
    return LAYERS.get(layer, LAYERS[DEFAULT_LAYER]).get('decimals', {'spot': 1, 'bench_mark': 2})


def value_tol(a: dict, b: dict) -> float:
    """Largest value difference at which readings a and b agree: VALUE_TOL within a
    layer; across layers also half a unit of the coarser rounding (whole-foot 8 ~ 8.3)."""
    if a['layer'] == b['layer']:
        return VALUE_TOL
    dp = min(layer_decimals(a['layer']).get(a['type'], 1), layer_decimals(b['layer']).get(b['type'], 1))
    return max(VALUE_TOL, 0.5 * 10 ** -dp)


def agree(a: dict, b: dict) -> bool:
    return abs(a['value_ft'] - b['value_ft']) <= value_tol(a, b) + 1e-9


# ----------------------------------------------------------------- loading

def load_readings(base: Path = BASE, readers: list[str] | None = None, only: list[Path] | None = None,
                  readings_dir: Path | None = None, extra: list[Path] | None = None):
    rows, files, warnings = [], [], []
    rdir = Path(readings_dir) if readings_dir else base / 'readings'
    paths = [Path(p) for p in only] if only else sorted(rdir.glob('*.json'))
    if extra and not only:
        paths += [Path(p) for p in extra]
    infos: dict[str, dict] = {}
    seen_names = set()
    for path in paths:
        m = NAME.match(path.name)
        if not m:
            warnings.append(f'{path.name}: file name not <m18|q18|s18>_X_Y.json or <m18|q18|s18>_X_Y.<reader>.json; '
                            f'ignored')
            continue
        if path.name in seen_names:
            warnings.append(f'{path.name}: given twice ({path}); second copy ignored')
            continue
        seen_names.add(path.name)
        mosaic, reader = m.group(1), m.group(2) or LEGACY_READER
        if readers and reader not in readers:
            continue
        try:
            doc = json.loads(path.read_text())
        except json.JSONDecodeError as e:
            warnings.append(f'{path.name}: invalid JSON ({e}); ignored')
            continue
        if doc.get('mosaic', mosaic) != mosaic:
            warnings.append(f"{path.name}: 'mosaic' field {doc.get('mosaic')} disagrees with file name")
        if doc.get('reader') and doc['reader'] != reader:
            warnings.append(f"{path.name}: 'reader' field {doc['reader']} disagrees with file name")
        side = mosaic_dir(mosaic) / f'{mosaic}.json'
        if not side.exists():
            warnings.append(f'{path.name}: no sidecar {side.name}; ignored')
            continue
        meta = json.loads(side.read_text())
        if mosaic not in infos:
            infos[mosaic] = meta_info({'name': mosaic, **meta})
        info = infos[mosaic]
        fid = path.name
        files.append({'file': fid, 'path': str(path), 'mosaic': mosaic, 'reader': reader, 'layer': info['layer'],
                      'n': len(doc.get('readings', [])),
                      'unreadable_regions': doc.get('unreadable_regions', []),
                      'crop_bounds_checked': doc.get('crop_bounds_checked')})
        for i, r in enumerate(doc.get('readings', [])):
            missing = [k for k in ('type', 'value_ft', 'px', 'py', 'confidence') if k not in r]
            if missing:
                warnings.append(f'{fid}#{i}: missing {missing}; ignored')
                continue
            if r['confidence'] not in CONF:
                warnings.append(f"{fid}#{i}: confidence {r['confidence']!r} not high/medium/low; treated as low")
                r = {**r, 'confidence': 'low'}
            if not (0 <= r['px'] <= meta['width_px'] and 0 <= r['py'] <= meta['height_px']):
                warnings.append(f"{fid}#{i}: px,py {r['px']},{r['py']} outside the mosaic")
            c = pixel_to_coords(meta, r['px'] + 0.5, r['py'] + 0.5)
            rows.append({**r, 'raw': r.get('raw', str(r['value_ft'])), 'notes': r.get('notes', ''),
                         'mosaic': mosaic, 'reader': reader, 'file': fid, 'idx': i,
                         'bng_e': c['bng_e'], 'bng_n': c['bng_n'],
                         'layer': info['layer'], 'epoch': info['epoch'], '_info': info})
    return rows, files, warnings


# -------------------------------------------------------------- clustering

def _centre(views):
    return (sum(v['bng_e'] for v in views) / len(views), sum(v['bng_n'] for v in views) / len(views))


class Grid:
    """Spatial hash of cluster centres, cell = MERGE_M."""

    def __init__(self):
        self.cells = defaultdict(set)

    @staticmethod
    def key(e, n):
        return int(e // MERGE_M), int(n // MERGE_M)

    def add(self, c):
        c['cell'] = self.key(c['e'], c['n'])
        self.cells[c['cell']].add(c['cid'])

    def remove(self, c):
        self.cells[c['cell']].discard(c['cid'])

    def near(self, e, n):
        i, j = self.key(e, n)
        for di in (-2, -1, 0, 1, 2):
            for dj in (-2, -1, 0, 1, 2):
                yield from self.cells.get((i + di, j + dj), ())


def cluster(rows):
    rows = sorted(rows, key=lambda r: (CONF[r['confidence']], r['file'], r['idx']))
    clusters: dict[int, dict] = {}
    grid = Grid()

    def update(c, views):
        grid.remove(c)
        c['views'] += views
        c['files'] |= {v['file'] for v in views}
        c['e'], c['n'] = _centre(c['views'])
        grid.add(c)

    for r in rows:
        best = None
        for cid in grid.near(r['bng_e'], r['bng_n']):
            c = clusters[cid]
            if c['type'] != r['type'] or c['epoch'] != r['epoch'] or r['file'] in c['files']:
                continue
            if not agree(c['views'][0], r):
                continue
            d = min(math.hypot(v['bng_e'] - r['bng_e'], v['bng_n'] - r['bng_n']) for v in c['views'])
            if d <= MERGE_M and (best is None or d < best[0]):
                best = (d, c)
        if best:
            update(best[1], [r])
        else:
            cid = len(clusters)
            clusters[cid] = {'cid': cid, 'type': r['type'], 'epoch': r['epoch'], 'views': [r], 'files': {r['file']},
                             'e': r['bng_e'], 'n': r['bng_n']}
            grid.add(clusters[cid])
    # second pass: same mark read with different values in different files -> disputed
    for cid in sorted(clusters):
        a = clusters.get(cid)
        if a is None:
            continue
        again = True
        while again:
            again = False
            for oid in sorted(grid.near(a['e'], a['n'])):
                if oid == cid:
                    continue
                b = clusters[oid]
                if a['type'] != b['type'] or a['epoch'] != b['epoch'] or a['files'] & b['files']:
                    continue
                if min(math.hypot(u['bng_e'] - v['bng_e'], u['bng_n'] - v['bng_n'])
                       for u in a['views'] for v in b['views']) <= MERGE_M:
                    grid.remove(b)
                    del clusters[oid]
                    update(a, b['views'])
                    again = True
                    break
    return list(clusters.values())


def summarise(clusters):
    marks = []
    for c in clusters:
        v = sorted(c['views'], key=lambda r: (LAYER_ORDER.get(r['layer'], 9), CONF[r['confidence']],
                                              r['file'], r['idx']))
        e, n = _centre(v)
        # value groups (member agrees with the group's first reading; across layers the
        # coarser rounding is allowed): votes weighted by distinct readers, then the
        # finer layer, then confidence
        groups: list[list[dict]] = []
        for r in v:
            g = next((g for g in groups if agree(g[0], r)), None)
            if g is None:
                groups.append([r])
            else:
                g.append(r)
        ranked = sorted(groups, key=lambda g: (-len({r['reader'] for r in g}),
                                               min(LAYER_ORDER.get(r['layer'], 9) for r in g),
                                               min(CONF[r['confidence']] for r in g), -len(g)))
        lead = ranked[0][0]
        values = sorted({r['value_ft'] for r in v})
        readers = sorted({r['reader'] for r in v})
        # different readers giving different values on the same layer is a dispute even
        # within tolerance; across layers only a value outside tolerance is
        split = any(a['reader'] != b['reader'] and a['layer'] == b['layer'] and a['value_ft'] != b['value_ft']
                    for i, a in enumerate(v) for b in v[i + 1:])
        disputed = len(groups) > 1 or split
        info = lead['_info']
        five = lead['layer'] == DEFAULT_LAYER
        lon, lat = FROM_BNG.transform(e, n)
        spread = max(math.hypot(r['bng_e'] - e, r['bng_n'] - n) for r in v)
        marks.append({
            'type': c['type'], 'value_ft': lead['value_ft'], 'raw': lead['raw'],
            'confidence': min((r['confidence'] for r in v), key=CONF.get),
            'n_readings': len(v), 'readers': readers,
            'mosaics': sorted({r['mosaic'] for r in v}),
            'bng_e': round(e, 2), 'bng_n': round(n, 2), 'lon': lon, 'lat': lat,
            'spread_m': round(spread, 2),
            'layer': lead['layer'],
            'layers': sorted({r['layer'] for r in v}, key=lambda s: (LAYER_ORDER.get(s, 9), s)),
            'epoch': c['epoch'],
            'scale': info['scale'], 'survey_dates': info['survey_dates'],
            'datum': FIVE_FOOT_DATUM if five else info['datum'],
            'source': FIVE_FOOT_SOURCE if five else info['geojson_source'],
            'disputed': disputed,
            'values': values if disputed else None,
            'values_by_reader': ({rd: sorted({r['value_ft'] for r in v if r['reader'] == rd}) for rd in readers}
                                 if disputed else None),
            'views': [f"{r['reader']}:{r['mosaic']}@{r['px']},{r['py']}={r['value_ft']}({r['confidence'][0]})"
                      for r in v],
            'notes': lead['notes'],
            '_v': v,
        })
    marks.sort(key=lambda m: (-m['bng_n'], m['bng_e']))
    seen = Counter()
    for m in marks:
        prefix = 'sk' if m['epoch'] == LAYERS[SKELETON_LAYER]['epoch'] else 'sh'
        base = f"{prefix}_{m['bng_e']:.0f}_{m['bng_n']:.0f}"
        seen[base] += 1
        m['id'] = base if seen[base] == 1 else f'{base}_{seen[base]}'
    return marks


# ----------------------------------------------------------------- setting

from spot_height_setting import SETTINGS, VALUE_FALLBACK, classify_rule  # noqa: E402


def assign_settings(marks):
    """setting / setting_source / setting_conflict (/ setting_rule) for each mark from
    its readings: reader-supplied values win over inference; majority, ties to the
    first reading in the mark's view order (best confidence first). setting_rule is
    VALUE_FALLBACK when every inferred vote for the winning setting rested on the
    value alone, else None."""
    for m in marks:
        per = [classify_rule(r) for r in m['_v']]
        src = 'reader' if any(p[1] == 'reader' for p in per) else 'inferred'
        votes = [(s, rule) for s, sr, rule in per if sr == src]
        m['setting_rule'] = None
        if not votes:
            m['setting'], m['setting_source'], m['setting_conflict'] = None, 'unknown', False
            continue
        cnt = Counter(s for s, _ in votes)
        top = max(cnt.values())
        m['setting'] = next(s for s, _ in votes if cnt[s] == top)
        m['setting_source'] = src
        m['setting_conflict'] = len(cnt) > 1
        if src == 'inferred' and all(rule == VALUE_FALLBACK for s, rule in votes if s == m['setting']):
            m['setting_rule'] = VALUE_FALLBACK
    return marks


def setting_checks(rows):
    """A reading's optional 'setting' must be one of SETTINGS."""
    return [f"{r['file']}#{r['idx']} {r['type']} {r['raw']!r}: setting {r['setting']!r} not one of "
            + ', '.join(SETTINGS) for r in rows if 'setting' in r and r['setting'] not in SETTINGS]


# ---------------------------------------------------------------------- QA

def decimals(raw: str, value: float) -> int | None:
    m = re.search(r'(\d+)\s*[.·•]\s*(\d+)\s*$', raw or '')
    if m:
        return len(m.group(2))
    s = repr(float(value))
    return len(s.split('.')[1].rstrip('0')) if '.' in s else 0


RAW_NUM = re.compile(r'([\d?]+)(?:\s*[.·•]\s*([\d?]+))?\s*$')


def raw_problem(raw: str, value: float) -> str | None:
    """None when raw spells value_ft ('?' = one doubtful digit; a trailing '?' may
    instead just flag doubt), else what is wrong."""
    m = RAW_NUM.search(raw or '')
    if not m or not re.search(r'\d', m.group(0)):
        return 'raw has no figure to compare with value_ft'
    cands = [(m.group(1), m.group(2) or '')]
    whole, frac = cands[0]
    if frac.endswith('?'):
        cands.append((whole, frac[:-1]))
    elif not frac and whole.endswith('?') and len(whole) > 1:
        cands.append((whole[:-1], ''))
    for w, f in cands:
        d = len(f)
        if abs(round(value, d) - value) > 1e-9:
            continue
        pat = w.replace('?', r'\d') + (r'\.' + f.replace('?', r'\d') if d else '')
        if re.fullmatch(pat, f'{value:.{d}f}'):
            return None
    return f'raw does not match value_ft {value}'


def checks(rows):
    out = []
    for r in rows:
        tag = f"{r['file']}#{r['idx']} {r['type']} {r['raw']!r} ({r['value_ft']})"
        if not (RANGE[0] <= r['value_ft'] <= RANGE[1]):
            out.append(f'{tag}: value outside plausible {RANGE[0]:g}-{RANGE[1]:g} ft')
        dp = decimals(r['raw'], r['value_ft'])
        layer = r.get('layer', DEFAULT_LAYER)
        want = layer_decimals(layer)
        what = '' if layer == DEFAULT_LAYER else f" ({LAYER_SHORT.get(layer, layer)} layer)"
        if r['type'] == 'bench_mark' and dp != want['bench_mark']:
            out.append(f"{tag}: bench mark not written to {want['bench_mark']} dp{what}")
        if r['type'] == 'spot' and dp != want['spot']:
            out.append(f"{tag}: spot height not written to {want['spot']} dp{what}"
                       + (' (whole feet: raw "8", value_ft 8)' if want['spot'] == 0 else ''))
        rp = raw_problem(r['raw'], r['value_ft'])
        if rp:
            out.append(f'{tag}: {rp}')
        if r['type'] not in ('spot', 'bench_mark'):
            out.append(f"{tag}: unexpected type {r['type']!r}")
    return out


def pair_stats(rows, files, marks):
    """Agreement for every mosaic read by two or more readers."""
    by_mosaic = defaultdict(set)
    for f in files:
        by_mosaic[f['mosaic']].add(f['reader'])
    multi = {m: sorted(rs) for m, rs in by_mosaic.items() if len(rs) >= 2}
    res = []
    for mosaic, readers in sorted(multi.items()):
        for i, ra in enumerate(readers):
            for rb in readers[i + 1:]:
                both = agree = exact = only_a = only_b = 0
                dists, disputes = [], []
                for mk in marks:
                    va = [r for r in mk['_v'] if r['mosaic'] == mosaic and r['reader'] == ra]
                    vb = [r for r in mk['_v'] if r['mosaic'] == mosaic and r['reader'] == rb]
                    if va and vb:
                        both += 1
                        a, b = va[0], vb[0]
                        dists.append(math.hypot(a['bng_e'] - b['bng_e'], a['bng_n'] - b['bng_n']))
                        if abs(a['value_ft'] - b['value_ft']) < 1e-9:
                            exact += 1
                        if abs(a['value_ft'] - b['value_ft']) <= VALUE_TOL + 1e-9:
                            agree += 1
                        else:
                            disputes.append(f"{mk['id']} {mk['type']}: {ra} {a['raw']} vs {rb} {b['raw']}")
                    elif va:
                        only_a += 1
                    elif vb:
                        only_b += 1
                res.append({'mosaic': mosaic, 'a': ra, 'b': rb, 'both': both, 'exact': exact, 'agree': agree,
                            'only_a': only_a, 'only_b': only_b, 'dists': dists, 'disputes': disputes})
    return res


def layer_table(marks) -> list[str]:
    """'Marks by layer' section: by each mark's primary layer."""
    L = ['', '## Marks by layer', '',
         "Primary layer of each mark (the winning reading's; five-foot first). 1890s layers (five-foot, "
         "25-inch) may share a mark; the 1848-51 skeleton never joins them (ids sk_E_N).", '',
         '| layer | scale | epoch | n | spot | bench_mark | high | medium | low | disputed | also on another layer '
         '| median ft | range ft |',
         '|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|']
    for lay in sorted({m['layer'] for m in marks}, key=lambda s: (LAYER_ORDER.get(s, 9), s)):
        ms = [m for m in marks if m['layer'] == lay]
        cc = Counter(m['confidence'] for m in ms)
        tc = Counter(m['type'] for m in ms)
        vals = sorted(m['value_ft'] for m in ms)
        L.append(f"| {LAYER_SHORT.get(lay, lay)} | {ms[0]['scale']} | {ms[0]['epoch']} | {len(ms)} | {tc['spot']} | "
                 f"{tc['bench_mark']} | {cc['high']} | {cc['medium']} | {cc['low']} | "
                 f"{sum(m['disputed'] for m in ms)} | {sum(len(m['layers']) > 1 for m in ms)} | "
                 f"{statistics.median(vals):.1f} | {vals[0]:.2f}-{vals[-1]:.2f} |")
    return L


def report(rows, files, marks, warnings, path: Path):
    L = ['# Spot-height merge: QA report', '']
    readers = Counter(f['reader'] for f in files)
    mosaics = sorted({f['mosaic'] for f in files})
    L.append(f'{len(rows)} readings in {len(files)} files ({len(mosaics)} mosaics; readers: '
             + ', '.join(f'{r} {n}' for r, n in sorted(readers.items())) + f') -> **{len(marks)} distinct marks**.')
    L.append(f'Clustering: same type, within {MERGE_M:g} m, value within {VALUE_TOL} ft; '
             f'same-file readings never merged; disagreeing values at one spot flagged as disputed.')
    L.append('')
    L.append('## Marks by type and confidence')
    L.append('')
    L.append('| type | n | high | medium | low | disputed | range ft |')
    L.append('|---|---:|---:|---:|---:|---:|---|')
    for t in sorted({m['type'] for m in marks}):
        ms = [m for m in marks if m['type'] == t]
        cc = Counter(m['confidence'] for m in ms)
        vals = [m['value_ft'] for m in ms]
        L.append(f"| {t} | {len(ms)} | {cc['high']} | {cc['medium']} | {cc['low']} | "
                 f"{sum(m['disputed'] for m in ms)} | {min(vals):.2f}-{max(vals):.2f} |")
    nread = Counter(len(m['readers']) for m in marks)
    L.append('')
    L.append('Marks seen by 1 / 2 / 3+ readers: '
             f"{nread[1]} / {nread[2]} / {sum(v for k, v in nread.items() if k >= 3)}; "
             f"seen in more than one mosaic: {sum(len(m['mosaics']) > 1 for m in marks)}.")
    multi = [m for m in marks if m['n_readings'] > 1]
    if multi:
        sp = sorted(m['spread_m'] for m in multi)
        L.append(f'Position spread of repeated readings (max distance from mark centre): '
                 f'median {statistics.median(sp):.1f} m, 90th pct {sp[int(0.9 * (len(sp) - 1))]:.1f} m, '
                 f'max {sp[-1]:.1f} m.')
    L += layer_table(marks)
    if any('setting_source' in m for m in marks):
        L.append('')
        L.append('## Marks by setting')
        L.append('')
        L.append('| setting | n | spot | bench_mark | high | medium | low | from reader | inferred | '
                 'of which value fallback | setting conflict | median ft | range ft |')
        L.append('|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|')
        for st in list(SETTINGS) + [None]:
            ms = [m for m in marks if m.get('setting') == st]
            if not ms:
                continue
            cc = Counter(m['confidence'] for m in ms)
            tc = Counter(m['type'] for m in ms)
            sc = Counter(m['setting_source'] for m in ms)
            vals = sorted(m['value_ft'] for m in ms)
            L.append(f"| {st or 'unknown'} | {len(ms)} | {tc['spot']} | {tc['bench_mark']} | {cc['high']} | "
                     f"{cc['medium']} | {cc['low']} | {sc['reader']} | {sc['inferred']} | "
                     f"{sum(m.get('setting_rule') == VALUE_FALLBACK for m in ms)} | "
                     f"{sum(m['setting_conflict'] for m in ms)} | {statistics.median(vals):.1f} | "
                     f"{vals[0]:.2f}-{vals[-1]:.2f} |")
        unk = sum(m.get('setting') is None for m in marks)
        L.append('')
        L.append(f"Setting from readers for {sum(m['setting_source'] == 'reader' for m in marks)} marks, inferred "
                 f"from notes (spot_height_setting.py) for {sum(m['setting_source'] == 'inferred' for m in marks)}, "
                 f"unknown for {unk} ({unk / max(1, len(marks)):.1%}).")
    L.append('')
    L.append('## Inter-reader agreement (mosaics read by two or more readers)')
    L.append('')
    pairs = pair_stats(rows, files, marks)
    if not pairs:
        L.append('No mosaic has been read by two readers yet.')
    else:
        L.append('| mosaic | readers | both | value agrees (<=0.15) | exact | only A | only B | '
                 'pos. spread median / max m |')
        L.append('|---|---|---:|---:|---:|---:|---:|---|')
        tot = Counter()
        alld = []
        for p in pairs:
            d = sorted(p['dists'])
            ds = f'{statistics.median(d):.1f} / {d[-1]:.1f}' if d else '-'
            L.append(f"| {p['mosaic']} | {p['a']} / {p['b']} | {p['both']} | {p['agree']} | {p['exact']} | "
                     f"{p['only_a']} | {p['only_b']} | {ds} |")
            for k in ('both', 'agree', 'exact', 'only_a', 'only_b'):
                tot[k] += p[k]
            alld += d
        union = tot['both'] + tot['only_a'] + tot['only_b']
        L.append('')
        if tot['both']:
            L.append(f"Overall: value agreement {tot['agree']}/{tot['both']} = {tot['agree'] / tot['both']:.1%} "
                     f"(exact {tot['exact'] / tot['both']:.1%}); marks found by both readers "
                     f"{tot['both']}/{union} = {tot['both'] / union:.1%}; position spread median "
                     f"{statistics.median(alld):.1f} m.")
        L.append('')
        L.append('### Disputes')
        ds = [d for p in pairs for d in p['disputes']]
        L += [f'- {d}' for d in ds] or ['None.']
    L.append('')
    L.append('## Cross-reader agreement on shared marks (any mosaic, including overlap strips)')
    L.append('')
    shared = [m for m in marks if len(m['readers']) >= 2]
    if not shared:
        L.append('No mark has been read by two readers yet.')
    else:
        ok = exact = 0
        dd = []
        for m in shared:
            per = defaultdict(list)
            for r in m['_v']:
                per[r['reader']].append(r)
            vals = [r['value_ft'] for r in m['_v']]
            ok += all(agree(a, b) for i, a in enumerate(m['_v']) for b in m['_v'][i + 1:])
            exact += len(set(vals)) == 1
            cs = [_centre(v) for v in per.values()]
            dd += [math.hypot(a[0] - b[0], a[1] - b[1]) for i, a in enumerate(cs) for b in cs[i + 1:]]
        dd.sort()
        L.append(f'{len(shared)} marks read by 2+ readers: value agreement (<= {VALUE_TOL} ft) {ok}/{len(shared)} '
                 f'= {ok / len(shared):.1%}, exact {exact}/{len(shared)} = {exact / len(shared):.1%}; '
                 f'distance between readers\' positions median {statistics.median(dd):.1f} m, max {dd[-1]:.1f} m.')
        L.append('These come from overlap strips between neighbouring mosaics read by different readers; '
                 'they are not a substitute for full double reads of whole mosaics.')
    L.append('')
    L.append('## All disputed marks')
    L.append('')
    disp = [m for m in marks if m['disputed']]
    L += [f"- {m['id']} {m['type']} values {m['values_by_reader']} ({'; '.join(m['views'])})" for m in disp] \
        or ['None.']
    L.append('')
    L.append('## Value histogram (2 ft bins, distinct marks)')
    L.append('')
    bins = Counter(int(m['value_ft'] // 2) * 2 for m in marks)
    if bins:
        top = max(bins.values())
        L.append('```')
        for b in range(min(bins), max(bins) + 2, 2):
            n = bins.get(b, 0)
            L.append(f'{b:5.0f}-{b + 2:<3.0f} ft {n:4d} ' + '#' * max(0, round(40 * n / top)))
        L.append('```')
    L.append('')
    L.append('## Rule checks (per reading)')
    L.append('')
    ck = checks(rows) + setting_checks(rows)
    if all(r.get('layer', DEFAULT_LAYER) == DEFAULT_LAYER for r in rows):
        L += [f'- {c}' for c in ck] or ['All readings pass: spots 1 dp, bench marks 2 dp, values 0-120 ft.']
    else:
        L += [f'- {c}' for c in ck] or ['All readings pass: five-foot spots 1 dp / bench marks 2 dp, 25-inch '
                                        'spots 0 dp / bench marks 1 dp, skeleton spots and bench marks 1 dp; raw '
                                        'matches value_ft; values 0-120 ft.']
    near = []
    for i, a in enumerate(marks):
        for b in marks[i + 1:]:
            if a['type'] != b['type'] and a['epoch'] == b['epoch'] \
                    and math.hypot(a['bng_e'] - b['bng_e'], a['bng_n'] - b['bng_n']) <= 3:
                near.append(f"- {a['id']} {a['type']} {a['raw']} and {b['id']} {b['type']} {b['raw']} within 3 m "
                            f"(one mark typed two ways?)")
    if near:
        L.append('')
        L.append('Different types at the same spot:')
        L += near
    ur = [(f['file'], u) for f in files for u in (f['unreadable_regions'] or [])]
    L.append('')
    L.append(f'## Unreadable regions reported: {len(ur)}')
    for fid, u in ur[:200]:
        box = [u.get(k) for k in ('px0', 'py0', 'px1', 'py1')] if 'px0' in u else u.get('box', u.get('bbox'))
        L.append(f"- {fid}: {box} {u.get('reason', '')}")
    if warnings:
        L.append('')
        L.append('## Input warnings')
        L += [f'- {w}' for w in warnings]
    path.write_text('\n'.join(L) + '\n')
    return pairs


def write_geojson(marks, files, path: Path):
    feats = []
    for m in marks:
        props = {
            'id': m['id'], 'type': m['type'], 'value_ft': m['value_ft'], 'raw': m['raw'],
            'confidence': m['confidence'], 'n_readings': m['n_readings'], 'readers': m['readers'],
            'mosaics': m['mosaics'], 'bng_e': m['bng_e'], 'bng_n': m['bng_n'], 'spread_m': m['spread_m'],
            'layer': m['layer'], 'layers': m['layers'], 'scale': m['scale'], 'survey_dates': m['survey_dates'],
            'datum': m['datum'], 'source': m['source'],
            'disputed': m['disputed'],
        }
        if m['disputed']:
            props['values'] = m['values']
            props['values_by_reader'] = m['values_by_reader']
        props['views'] = m['views']
        props['notes'] = m['notes']
        props['setting'] = m.get('setting')
        props['setting_source'] = m.get('setting_source', 'unknown')
        props['setting_conflict'] = m.get('setting_conflict', False)
        if m.get('setting_rule'):
            props['setting_rule'] = m['setting_rule']
        feats.append({'type': 'Feature', 'properties': props,
                      'geometry': {'type': 'Point', 'coordinates': [round(m['lon'], 7), round(m['lat'], 7)]}})
    gj = {'type': 'FeatureCollection', 'name': 'os-five-foot-1893-heights',
          'crs_note': 'WGS84 lon/lat; bng_e/bng_n are EPSG:27700; heights in feet above Ordnance Datum (Liverpool)',
          'mosaics_read': sorted({f['mosaic'] for f in files}),
          'files': sorted(f['file'] for f in files),
          'features': feats}
    tmp = path.with_suffix('.geojson.tmp')
    tmp.write_text(json.dumps(gj, indent=1, ensure_ascii=False))
    tmp.replace(path)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out', type=Path, default=BASE / 'heights.geojson')
    ap.add_argument('--report', type=Path, default=BASE / 'qa_report.md')
    ap.add_argument('--readers', nargs='+', help='only use files from these readers (default: all)')
    ap.add_argument('--readings-dir', type=Path, default=None, metavar='DIR',
                    help='read reading files from DIR instead of reference/spot-heights/readings '
                         '(requires --out and --report)')
    ap.add_argument('--extra', nargs='+', type=Path, default=None, metavar='FILE',
                    help='also merge these reading files (e.g. test files kept outside readings/; '
                         'requires --out and --report)')
    ap.add_argument('--check', nargs='+', type=Path, metavar='FILE',
                    help='validate reading file(s) only: schema, name, rules; writes nothing')
    args = ap.parse_args()
    if (args.readings_dir or args.extra) and not args.check and (
            args.out == BASE / 'heights.geojson' or args.report == BASE / 'qa_report.md'):
        ap.error('--readings-dir / --extra need explicit --out and --report (so the real outputs are not '
                 'overwritten)')
    if args.check:
        rows, files, warnings = load_readings(only=args.check)
        problems = warnings + checks(rows)
        for f in files:
            if f['crop_bounds_checked'] is None:
                problems.append(f"{f['file']}: no crop_bounds_checked list")
            if 'reader' not in json.loads(Path(f['path']).read_text()) and f['reader'] != LEGACY_READER:
                problems.append(f"{f['file']}: no 'reader' field")
        dup = Counter((r['file'], r['type'], r['value_ft'], round(r['px'] / 8), round(r['py'] / 8)) for r in rows)
        problems += [f'{k[0]}: {k[1]} {k[2]} listed twice at about {k[3] * 8},{k[4] * 8}' for k, n in dup.items() if n > 1]

        problems += setting_checks(rows)
        print(f"{len(rows)} readings in {len(files)} file(s); {len(problems)} problem(s)")
        nos = sum('setting' not in r for r in rows)
        if nos:
            print(f'  note: {nos} reading(s) without a setting field (see READING_GUIDE.md, '
                  f'"Setting field"); the merge will infer them from notes')
        for lay in sorted({f['layer'] for f in files} - {DEFAULT_LAYER}, key=lambda s: (LAYER_ORDER.get(s, 9), s)):
            dp = layer_decimals(lay)
            print(f"  note: {LAYER_SHORT.get(lay, lay)} layer: spots {dp['spot']} dp, bench marks "
                  f"{dp['bench_mark']} dp; raw must spell value_ft")
        for p in problems:
            print(f'  {p}')
        sys.exit(1 if problems else 0)
    rows, files, warnings = load_readings(readers=args.readers, readings_dir=args.readings_dir, extra=args.extra)
    marks = assign_settings(summarise(cluster(rows)))
    write_geojson(marks, files, args.out)
    pairs = report(rows, files, marks, warnings, args.report)
    cc = Counter((m['type'], m['confidence']) for m in marks)
    print(f"{len(rows)} readings, {len(files)} files, {len({f['mosaic'] for f in files})} mosaics -> "
          f"{len(marks)} distinct marks ({sum(m['disputed'] for m in marks)} disputed)")
    for t in sorted({m['type'] for m in marks}):
        print(f"  {t:11s} " + '  '.join(f"{c} {cc[(t, c)]}" for c in CONF))
    print(f'  mosaics read by 2+ readers: {len({p["mosaic"] for p in pairs})}')
    lc = Counter(m['layer'] for m in marks)
    print('  layers: ' + ', '.join(f"{LAYER_SHORT.get(k, k)} {lc[k]}"
                                   for k in sorted(lc, key=lambda s: (LAYER_ORDER.get(s, 9), s)))
          + f" (marks on 2+ layers {sum(len(m['layers']) > 1 for m in marks)})")
    sc = Counter(m['setting'] or 'unknown' for m in marks)
    print('  setting: ' + ', '.join(f'{k} {v}' for k, v in sc.most_common())
          + f" (reader {sum(m['setting_source'] == 'reader' for m in marks)}, "
          f"inferred {sum(m['setting_source'] == 'inferred' for m in marks)})")
    if warnings:
        print(f'  {len(warnings)} input warning(s), see {args.report.name}')
    print(f'-> {args.out}\n-> {args.report}')


if __name__ == '__main__':
    main()
