"""Cross-check spot-height reading files against their neighbours' overlap strips.

Neighbouring mosaics overlap by one tile (256 px), and identical mosaics read by
two readers overlap completely. A reader who never saw the images but wrote
readings anyway produces marks that do not line up with the other readers'
marks in those shared regions. This script makes that check automatic.

For every pair of reading files on overlapping mosaics of the same layer
(m18/q18/s18 prefixes are never mixed) it:

  * converts every reading to EPSG:27700 with spot_height_mosaics.pixel_to_coords
    (each reading via its own mosaic's sidecar);
  * takes the readings of file A that lie inside B's mosaic, at least --margin px
    from B's edge, not on a missing tile of B and not inside one of B's
    unreadable_regions (grown by --margin): these are A's "covered overlap"
    readings for B;
  * pairs them one-to-one (greedy, value-agreeing then nearest first) with B's
    readings of the same type within --tol-m metres; a pair agrees in value when
    |dv| <= --tol-ft.

Per file the counts are pooled over all neighbours (a reading counts as matched
if any neighbour matched it) and a verdict is given:

  SUSPECT  >= 3 covered-overlap readings and none matched, or some neighbour has
           >= 3 readings inside this file's usable area of the shared region
           while this file has no reading there (and no unreadable_regions or
           missing tiles covering them);
           with >= 5 covered-overlap readings, under --suspect-frac (15%) matched
           (a few chance hits among invented marks);
  WEAK     some matches but fewer than --ok-frac (70%) of covered readings;
  OK       >= 70% matched, or fewer than 3 covered-overlap readings.

An otherwise OK file is also marked WEAK (flag VALUES) when >= 3 readings are
matched by position but fewer than half of them agree in value.

Files marked SUSPECT are then dropped as references and the other files are
re-scored, so one fabricated file does not drag down its genuine neighbours
(repeated until stable). Flags add detail: EMPTY (0 readings where neighbours
show marks), VALUES (under half of position matches agree in value), UNCHECKED
(no covered overlap at all).

Usage:
  python3 scripts/spot_height_overlap_check.py
  python3 scripts/spot_height_overlap_check.py --extra path/to/m18_X_Y.opus-i.UNSEEN.json
  python3 scripts/spot_height_overlap_check.py --dir some/folder --report /tmp/r.md

Reading file names: <mosaic>.<reader>.json, legacy <mosaic>.json (= opus-a);
any further dotted tags (e.g. .UNSEEN) are ignored for naming. The file's own
"mosaic"/"reader" fields win when present.

Exit status: 2 if any file is SUSPECT, else 0.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from spot_height_mosaics import mosaic_dir, pixel_to_coords  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
READINGS = ROOT / 'reference/spot-heights/readings'
REPORT = ROOT / 'reference/spot-heights/overlap_report.md'
LEGACY_READER = 'opus-a'
TILE = 256

MOSAIC_RE = re.compile(r'^([a-z])(\d+)_(\d+)_(\d+)$')
READER_RE = re.compile(r'^[a-z][a-z0-9]*(-[a-z0-9]+)*$')  # opus-i, opus-k2, ...
VERDICT_ORDER = {'SUSPECT': 0, 'WEAK': 1, 'OK': 2}


# ------------------------------------------------------------------ loading

def parse_name(path: Path) -> tuple[str | None, str | None, list[str]]:
    """<mosaic>[.<reader>][.<TAG>...].json -> (mosaic, reader, tags)."""
    parts = path.name.split('.')
    if parts[-1].lower() == 'json':
        parts = parts[:-1]
    mosaic = parts[0] if parts and MOSAIC_RE.match(parts[0]) else None
    reader, tags = None, []
    for p in parts[1:]:
        if reader is None and READER_RE.match(p):
            reader = p
        else:
            tags.append(p)
    return mosaic, reader, tags


def mosaic_meta(name: str, cache: dict) -> dict:
    if name in cache:
        return cache[name]
    m = MOSAIC_RE.match(name)
    if not m:
        raise ValueError(f'bad mosaic name {name!r}')
    meta = None
    try:
        side = mosaic_dir(name) / f'{name}.json'
        if side.exists():
            meta = json.loads(side.read_text())
    except (ValueError, OSError):
        meta = None
    if meta is None:  # rebuild the lattice geometry from the name
        meta = {'name': name, 'zoom': int(m.group(2)), 'tile_x0': int(m.group(3)),
                'tile_y0': int(m.group(4)), 'tiles_w': 4, 'tiles_h': 4, 'missing_tiles': [],
                '_no_sidecar': True}
    cache[name] = meta
    return meta


class ReadingFile:
    def __init__(self, path: Path, meta_cache: dict):
        self.path = path
        doc = json.loads(path.read_text())
        n_mosaic, n_reader, self.tags = parse_name(path)
        self.mosaic = doc.get('mosaic') or n_mosaic
        if not self.mosaic or not MOSAIC_RE.match(self.mosaic):
            raise ValueError(f'{path.name}: cannot tell which mosaic this is')
        self.warn = []
        if n_mosaic and n_mosaic != self.mosaic:
            self.warn.append(f'file says mosaic {self.mosaic}, name says {n_mosaic}')
        self.reader = doc.get('reader') or n_reader or LEGACY_READER
        if n_reader and doc.get('reader') and n_reader != doc['reader']:
            self.warn.append(f"file says reader {doc['reader']}, name says {n_reader}")
        self.label = path.name
        self.prefix = self.mosaic[0]
        self.meta = mosaic_meta(self.mosaic, meta_cache)
        z = self.meta['zoom']
        self.zoom = z
        self.gx0 = self.meta['tile_x0'] * TILE
        self.gy0 = self.meta['tile_y0'] * TILE
        self.w = self.meta.get('tiles_w', 4) * TILE
        self.h = self.meta.get('tiles_h', 4) * TILE
        self.missing = {tuple(t) for t in self.meta.get('missing_tiles') or []}
        self.unreadable = []
        for u in doc.get('unreadable_regions') or []:
            try:
                self.unreadable.append((float(u['px0']), float(u['py0']), float(u['px1']), float(u['py1'])))
            except (KeyError, TypeError, ValueError):
                continue
        self.readings = []
        for i, r in enumerate(doc.get('readings') or []):
            try:
                px, py = float(r['px']), float(r['py'])
            except (KeyError, TypeError, ValueError):
                self.warn.append(f'reading {i} has no usable px/py')
                continue
            c = pixel_to_coords(self.meta, px, py)
            v = r.get('value_ft')
            self.readings.append({
                'i': i, 'type': r.get('type'), 'value': float(v) if isinstance(v, (int, float)) else None,
                'raw': r.get('raw'), 'px': px, 'py': py,
                'gx': self.gx0 + px, 'gy': self.gy0 + py,
                'e': c['bng_e'], 'n': c['bng_n']})

    # global-pixel helpers --------------------------------------------------
    def usable(self, gx: float, gy: float, margin: float) -> bool:
        """Could this file's reader have seen a whole figure at global pixel gx,gy?"""
        px, py = gx - self.gx0, gy - self.gy0
        if not (margin <= px <= self.w - margin and margin <= py <= self.h - margin):
            return False
        tile = (int(gx // TILE), int(gy // TILE))
        if tile in self.missing:
            return False
        for x0, y0, x1, y1 in self.unreadable:
            if min(x0, x1) - margin <= px <= max(x0, x1) + margin and \
               min(y0, y1) - margin <= py <= max(y0, y1) + margin:
                return False
        return True

    def overlap_rect(self, other: 'ReadingFile'):
        x0, y0 = max(self.gx0, other.gx0), max(self.gy0, other.gy0)
        x1, y1 = min(self.gx0 + self.w, other.gx0 + other.w), min(self.gy0 + self.h, other.gy0 + other.h)
        if x1 <= x0 or y1 <= y0:
            return None
        return x0, y0, x1, y1


def load_files(dir_: Path, extra: list[Path]) -> tuple[list[ReadingFile], list[str]]:
    cache: dict = {}
    files, errors, seen = [], [], set()
    paths = sorted(p for p in dir_.glob('*.json') if MOSAIC_RE.match(p.name.split('.')[0])) if dir_ else []
    for p in list(paths) + list(extra):
        rp = p.resolve()
        if rp in seen:
            continue
        seen.add(rp)
        try:
            files.append(ReadingFile(p, cache))
        except (ValueError, OSError, KeyError) as exc:
            errors.append(f'{p}: {exc}')
    return files, errors


# ----------------------------------------------------------------- matching

def match_pair(a: ReadingFile, b: ReadingFile, args) -> dict:
    """Compare file a's readings inside b's usable area with b's readings."""
    rect = a.overlap_rect(b)
    covered = [r for r in a.readings if b.usable(r['gx'], r['gy'], args.margin)]
    # b's marks that a could have seen, for the omission test
    b_in_a = [r for r in b.readings if a.usable(r['gx'], r['gy'], args.margin)]
    a_in_rect = [r for r in a.readings
                 if rect[0] <= r['gx'] <= rect[2] and rect[1] <= r['gy'] <= rect[3]]
    cands = []
    tol2 = args.tol_m ** 2
    for ra in covered:
        for rb in b.readings:
            if ra['type'] != rb['type']:
                continue
            d2 = (ra['e'] - rb['e']) ** 2 + (ra['n'] - rb['n']) ** 2
            if d2 <= tol2:
                agree = (ra['value'] is not None and rb['value'] is not None
                         and abs(ra['value'] - rb['value']) <= args.tol_ft + 1e-9)
                cands.append((not agree, d2, ra['i'], rb['i'], agree))
    cands.sort()
    used_a, used_b, pairs = set(), set(), []
    for _, d2, ia, ib, agree in cands:
        if ia in used_a or ib in used_b:
            continue
        used_a.add(ia)
        used_b.add(ib)
        pairs.append((ia, ib, math.sqrt(d2), agree))
    return {'other': b, 'rect': rect, 'covered': {r['i'] for r in covered},
            'matched': {p[0] for p in pairs}, 'agree': {p[0] for p in pairs if p[3]},
            'pairs': pairs, 'b_in_a': len(b_in_a), 'b_in_a_found': len({p[1] for p in pairs} &
                                                                     {r['i'] for r in b_in_a}),
            'a_in_rect': len(a_in_rect)}


def neighbours(files: list[ReadingFile]) -> dict:
    nb = {id(f): [] for f in files}
    for i, a in enumerate(files):
        for b in files[i + 1:]:
            if a.prefix != b.prefix or a.zoom != b.zoom:
                continue
            if a.overlap_rect(b):
                nb[id(a)].append(b)
                nb[id(b)].append(a)
    return nb


def score(f: ReadingFile, refs: list[ReadingFile], args) -> dict:
    results = [match_pair(f, b, args) for b in refs]
    covered = set().union(*(r['covered'] for r in results)) if results else set()
    matched = set().union(*(r['matched'] for r in results)) if results else set()
    agree = set().union(*(r['agree'] for r in results)) if results else set()
    n_cov, n_match, n_agree = len(covered), len(matched & covered), len(agree & covered)
    omissions = [r for r in results if r['b_in_a'] >= args.min_n and r['a_in_rect'] == 0]
    flags = []
    if n_cov >= args.min_n and n_match == 0:
        verdict = 'SUSPECT'
    elif n_cov >= 5 and n_match / n_cov < args.suspect_frac:  # a few chance hits among invented marks
        verdict = 'SUSPECT'
    elif omissions:
        verdict = 'SUSPECT'
    elif n_cov < args.min_n:
        verdict = 'OK'
    elif n_match / n_cov >= args.ok_frac:
        verdict = 'OK'
    else:
        verdict = 'WEAK'
    values_bad = n_match >= args.min_n and n_agree / n_match < 0.5
    if verdict == 'OK' and values_bad:  # positions line up but the figures do not
        verdict = 'WEAK'
    if omissions:
        flags.append('EMPTY' if not f.readings else 'MISSING-STRIP')
    if values_bad:
        flags.append('VALUES')
    if n_cov == 0 and not any(r['b_in_a'] for r in results):
        flags.append('UNCHECKED')
    if n_cov and n_cov < args.min_n:
        flags.append('FEW')
    # neighbours' strip marks that this file found (recall), pooled
    nb_marks = sum(r['b_in_a'] for r in results)
    nb_found = sum(r['b_in_a_found'] for r in results)
    return {'file': f, 'verdict': verdict, 'flags': flags, 'n': len(f.readings), 'cov': n_cov,
            'match': n_match, 'agree': n_agree, 'nb_marks': nb_marks, 'nb_found': nb_found,
            'results': results, 'omissions': omissions}


def run(files: list[ReadingFile], args) -> list[dict]:
    nb = neighbours(files)
    excluded: set = set()
    for _ in range(5):
        scores = {id(f): score(f, [b for b in nb[id(f)] if id(b) not in excluded or id(f) in excluded], args)
                  for f in files}
        new = {k for k, s in scores.items() if s['verdict'] == 'SUSPECT'}
        if new == excluded:
            break
        excluded = new
    out = list(scores.values())
    for s in out:
        s['excluded_refs'] = [b.label for b in nb[id(s['file'])] if id(b) in excluded
                              and id(s['file']) not in excluded]
    out.sort(key=lambda s: (VERDICT_ORDER[s['verdict']],
                            (s['match'] / s['cov']) if s['cov'] else 1.0, -s['cov'], s['file'].label))
    return out


# ------------------------------------------------------------------ output

def pct(a, b):
    return f'{100 * a / b:.0f}%' if b else '-'


def row(s: dict) -> list[str]:
    f = s['file']
    nbs = ', '.join(sorted(r['other'].label.removesuffix('.json') for r in s['results'])) or 'none'
    return [s['verdict'], f.label, str(s['n']), str(s['cov']), str(s['match']), pct(s['match'], s['cov']),
            str(s['agree']), f"{s['nb_found']}/{s['nb_marks']}", ' '.join(s['flags']), nbs]


HEAD = ['verdict', 'file', 'n', 'ovl', 'match', 'match%', 'agree', 'nbr found', 'flags', 'compared with']


def print_table(scores: list[dict]) -> None:
    rows = [row(s) for s in scores]
    widths = [max(len(HEAD[i]), *(len(r[i]) for r in rows)) if rows else len(HEAD[i]) for i in range(9)]
    fmt = '  '.join(f'{{:{w}}}' for w in widths)
    print(fmt.format(*HEAD[:9]))
    for r in rows:
        print(fmt.format(*r[:9]))


def detail_lines(s: dict) -> list[str]:
    f = s['file']
    out = []
    for r in sorted(s['results'], key=lambda r: r['other'].label):
        b = r['other']
        cov = len(r['covered'])
        miss = sorted(r['covered'] - r['matched'])
        bad = [p for p in r['pairs'] if not p[3]]
        line = (f"- vs `{b.label}`: {cov} of this file's readings in its usable area, "
                f"{len(r['matched'])} matched, {len(r['agree'])} agree; it has {r['b_in_a']} marks in "
                f"this file's usable area, {r['b_in_a_found']} found here")
        if r in s['omissions']:
            line += ' **(this file has no reading in the shared region)**'
        out.append(line)
        byi = {x['i']: x for x in f.readings}
        bbyi = {x['i']: x for x in b.readings}
        if miss:
            out.append('  - unmatched: ' + '; '.join(
                f"{byi[i]['type']} {byi[i]['raw'] or byi[i]['value']} @({byi[i]['px']:.0f},{byi[i]['py']:.0f})"
                for i in miss[:12]) + (' ...' if len(miss) > 12 else ''))
        if bad:
            out.append('  - value disagreements: ' + '; '.join(
                f"{byi[ia]['raw'] or byi[ia]['value']} vs {bbyi[ib]['raw'] or bbyi[ib]['value']} "
                f"({d:.1f} m)" for ia, ib, d, _ in bad[:12]))
    if s['excluded_refs']:
        out.append('- ignored as reference (SUSPECT): ' + ', '.join(f'`{x}`' for x in s['excluded_refs']))
    for w in f.warn:
        out.append(f'- warning: {w}')
    return out


def write_report(path: Path, scores: list[dict], args, errors: list[str]) -> None:
    n_s = sum(s['verdict'] == 'SUSPECT' for s in scores)
    n_w = sum(s['verdict'] == 'WEAK' for s in scores)
    lines = [
        '# Spot-height overlap check',
        '',
        'Generated by `scripts/spot_height_overlap_check.py`. Each reading file is compared with every '
        'other file whose mosaic overlaps it (same layer; neighbours share a 256 px strip, identical '
        'mosaics overlap fully). Readings are paired across files in EPSG:27700, same type, within '
        f'{args.tol_m:g} m; values agree within {args.tol_ft:g} ft. A reading is only expected in the '
        f'other file when it lies at least {args.margin:g} px inside that mosaic, off its missing tiles '
        'and outside its `unreadable_regions`.',
        '',
        f'Files: {len(scores)}. SUSPECT: {n_s}. WEAK: {n_w}. OK: {len(scores) - n_s - n_w}.',
        '',
        'Columns: `n` readings in file; `ovl` readings in overlap covered by another file; `match` of '
        'those paired by position with some neighbour; `agree` of those also equal in value; '
        '`nbr found` neighbours\' marks in this file\'s usable shared area that this file also has.',
        '',
        'Verdicts: SUSPECT = >=3 overlap readings and none matched, or a neighbour has >=3 marks in the '
        'shared region where this file has none, or >=5 overlap readings with under '
        f'{100 * args.suspect_frac:.0f}% matched; WEAK = some matches, under '
        f'{100 * args.ok_frac:.0f}%, or >=3 position matches of which under half agree in value; OK otherwise (including <3 overlap readings). Flags: EMPTY / '
        'MISSING-STRIP (no readings where neighbours show marks), VALUES (<50% of position matches agree '
        'in value), FEW (<3 overlap readings), UNCHECKED (nothing to compare). SUSPECT files are not used '
        'as references when scoring the others.',
        '',
        '| ' + ' | '.join(HEAD) + ' |',
        '|' + '---|' * len(HEAD),
    ]
    for s in scores:
        r = row(s)
        r[1] = f'`{r[1]}`'
        lines.append('| ' + ' | '.join(r) + ' |')
    lines += ['', '## Details (worst first)', '']
    for s in scores:
        lines.append(f"### {s['verdict']} `{s['file'].label}`")
        lines.append('')
        lines += detail_lines(s) or ['- no overlapping files']
        lines.append('')
    if errors:
        lines += ['## Files not loaded', ''] + [f'- {e}' for e in errors] + ['']
    path.write_text('\n'.join(lines))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--dir', type=Path, default=READINGS, help='folder of reading files')
    ap.add_argument('--no-dir', action='store_true', help='only check the --extra files against each other')
    ap.add_argument('--extra', type=Path, nargs='*', default=[], help='further reading files (e.g. quarantined)')
    ap.add_argument('--report', type=Path, default=REPORT, help='markdown report path')
    ap.add_argument('--no-report', action='store_true')
    ap.add_argument('--tol-m', type=float, default=6.0, help='position match tolerance, metres')
    ap.add_argument('--tol-ft', type=float, default=0.15, help='value agreement tolerance, feet')
    ap.add_argument('--margin', type=float, default=12.0,
                    help='px inside the other mosaic (and around its unreadable regions) a mark must lie')
    ap.add_argument('--ok-frac', type=float, default=0.7)
    ap.add_argument('--min-n', type=int, default=3)
    ap.add_argument('--suspect-frac', type=float, default=0.15,
                    help='with >= 5 overlap readings, a match rate below this is SUSPECT (chance hits)')
    ap.add_argument('--details', action='store_true', help='print per-neighbour details for non-OK files')
    args = ap.parse_args()

    files, errors = load_files(None if args.no_dir else args.dir, args.extra)
    for e in errors:
        print(f'warning: {e}', file=sys.stderr)
    if not files:
        print('no reading files found', file=sys.stderr)
        return 1
    scores = run(files, args)
    print_table(scores)
    if args.details:
        for s in scores:
            if s['verdict'] != 'OK' or s['file'].path in args.extra:
                print(f"\n{s['verdict']} {s['file'].label}")
                print('\n'.join(detail_lines(s)))
    if not args.no_report:
        write_report(args.report, scores, args, errors)
        print(f'\nreport: {args.report}')
    return 2 if any(s['verdict'] == 'SUSPECT' for s in scores) else 0


if __name__ == '__main__':
    sys.exit(main())
