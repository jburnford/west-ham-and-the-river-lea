"""Work manifest for the multi-reader spot-height extraction.

reference/spot-heights/manifest.json is the single source of truth for which
mosaics exist, their priority, and who has claimed / finished reading them.
Every update takes an exclusive lock (manifest.json.lock) and is written to a
temporary file that is then renamed over the manifest, so concurrent readers
never see a half-written file and concurrent claims cannot overwrite each other.

Layers (see LAYER_SETS): m18_* five-foot 1893-96 (mosaics/, tiers 1-3),
q18_* 25-inch gap fill (mosaics-25inch/, tier 4, zone gap_fill), s18_* 1848-51
skeleton survey (mosaics-1848/, tier 5, zone skeleton_1848). Entries without a
'layer' key are five-foot. Every subcommand that selects takes --layer
(a layer id or a name prefix: m18, q18, s18).

Subcommands
  build [--reset]              (re)build from every layer's lattice_index.json;
                               keeps existing reader state unless --reset
  extend                       append entries for mosaics of any layer that
                               are not in the manifest yet (new ranks after the
                               current last rank); existing entries untouched
  next N [--exclude-readers R ...] [--only-read] [--max-readers K] [--layer L]
                               print the next N mosaics by priority. Default:
                               mosaics nobody has read or claimed. With
                               --exclude-readers: mosaics none of R has touched
                               (for a second independent read); --only-read
                               restricts to mosaics already read by someone else.
  claim <reader> N [same filters as next]
                               atomically pick the next N and assign them
  assign <reader> <mosaic ...> claim specific mosaics for a reader
  done <reader> <mosaic ...>   mark finished (the readings file must exist)
  release <reader> <mosaic ...> undo a claim that was not finished
  sync                         mark done every (mosaic, reader) that has a
                               readings file but is not yet recorded
  status                       counts by zone / state, per-reader totals, and
                               consistency checks against readings/

A reader's readings file is readings/<mosaic>.<reader>.json (legacy
readings/<mosaic>.json belongs to reader opus-a).
"""
from __future__ import annotations

import argparse
import contextlib
import fcntl
import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'reference/spot-heights'
MANIFEST = BASE / 'manifest.json'
LOCK = BASE / 'manifest.json.lock'
INDEX = BASE / 'mosaics/lattice_index.json'
FIVE_FOOT = 'os-london-five-foot-1893'
# layer id -> (name prefix, lattice index, priority scheme)
LAYER_SETS = {
    FIVE_FOOT: ('m18', INDEX, 'five_foot'),
    'os-25-inch-london': ('q18', BASE / 'mosaics-25inch/lattice_index.json', 'gap_fill'),
    'os-london-skeleton-5280': ('s18', BASE / 'mosaics-1848/lattice_index.json', 'skeleton_1848'),
}
READINGS = BASE / 'readings'
LEGACY_READER = 'opus-a'

# Priority: the Queen Elizabeth Olympic Park footprint first (the area that has
# changed most), then the Abbey Mills / Channelsea / Bow Creek / Plaistow marsh
# tier, then everything else by distance from the park box.
OLYMPIC_BOX = (537000.0, 183300.0, 539200.0, 185900.0)  # E0, N0, E1, N1 (BNG)
OLYMPIC_CENTRE = (538100.0, 184600.0)
SECONDARY_BOX = (537800.0, 180600.0, 541000.0, 183300.0)  # Abbey Mills, Channelsea S, Bow Creek, Plaistow marsh
ABBEY_MILLS = (538723.0, 183221.0)
EMPTY_BLANK_FRAC = 0.97  # mosaics this blank carry no map to read


def now() -> str:
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def inside(box, e, n) -> bool:
    return box[0] <= e <= box[2] and box[1] <= n <= box[3]


def dist_to_box(box, e, n) -> float:
    dx = max(box[0] - e, 0.0, e - box[2])
    dy = max(box[1] - n, 0.0, n - box[3])
    return math.hypot(dx, dy)


def entry_layer(m: dict) -> str:
    return m.get('layer', FIVE_FOOT)


def resolve_layer(arg: str | None) -> str | None:
    """--layer value (layer id or name prefix m18/q18/s18) -> layer id."""
    if not arg:
        return None
    if arg in LAYER_SETS:
        return arg
    for layer, (prefix, _, _) in LAYER_SETS.items():
        if arg.rstrip('_') == prefix:
            return layer
    sys.exit(f'unknown layer {arg!r}; use one of {list(LAYER_SETS)} or {[v[0] for v in LAYER_SETS.values()]}')


def reading_path(mosaic: str, reader: str) -> Path | None:
    p = READINGS / f'{mosaic}.{reader}.json'
    if p.exists():
        return p
    if reader == LEGACY_READER and (READINGS / f'{mosaic}.json').exists():
        return READINGS / f'{mosaic}.json'
    return None


# ----------------------------------------------------------------- io + lock

@contextlib.contextmanager
def locked():
    LOCK.touch(exist_ok=True)
    with open(LOCK) as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)


def load() -> dict:
    if not MANIFEST.exists():
        sys.exit(f'{MANIFEST} not found; run: python3 {Path(__file__).name} build')
    return json.loads(MANIFEST.read_text())


def save(doc: dict) -> None:
    doc['updated'] = now()
    tmp = MANIFEST.with_name(f'.manifest.{os.getpid()}.tmp')
    tmp.write_text(json.dumps(doc, indent=1, ensure_ascii=False))
    os.replace(tmp, MANIFEST)


# --------------------------------------------------------------------- build

def five_foot_zone(E: float, N: float) -> tuple[str, int, float]:
    """(zone, tier 1-3, key) of the five-foot priority scheme."""
    if inside(OLYMPIC_BOX, E, N):
        return 'olympic_park', 1, math.hypot(E - OLYMPIC_CENTRE[0], N - OLYMPIC_CENTRE[1])
    if inside(SECONDARY_BOX, E, N):
        return 'other', 2, math.hypot(E - ABBEY_MILLS[0], N - ABBEY_MILLS[1])
    return 'other', 3, dist_to_box(OLYMPIC_BOX, E, N)


def index_entries(layer: str) -> list[dict]:
    """Manifest entries (without rank or reader state) from one layer's lattice index."""
    prefix, index, scheme = LAYER_SETS[layer]
    if not index.exists():
        return []
    idx = json.loads(index.read_text())
    entries = []
    for e in idx['mosaics']:
        if e['status'] == 'skipped_no_tiles':
            continue
        E, N = e['centre_bng']
        sub = None
        if scheme == 'five_foot':
            zone, tier, key = five_foot_zone(E, N)
        elif scheme == 'gap_fill':
            zone, tier, key = 'gap_fill', 4, math.hypot(E - ABBEY_MILLS[0], N - ABBEY_MILLS[1])
        else:  # skeleton_1848: tier 5, ordered inside by the five-foot zone logic
            _, sub, key = five_foot_zone(E, N)
            zone, tier = 'skeleton_1848', 5
        written = e['status'] in ('written', 'existing_identical', 'existing_differs')
        empty = e.get('blank_frac', 1.0) >= EMPTY_BLANK_FRAC
        m = {
            'name': e['name'], 'x0': e['tile_x0'], 'y0': e['tile_y0'],
            'missing_tiles': e['missing'], 'blank_frac': e.get('blank_frac'),
            'centroid_bng': [round(E, 1), round(N, 1)],
            'priority_zone': zone, 'tier': tier, 'priority_key_m': round(key, 1),
            'available': written and not empty,
            'skip_reason': None if written and not empty else
            ('more than half the tiles missing' if not written else 'blank (outside the sheets)'),
            'readers': [], 'assigned': {}, 'done': {},
        }
        if layer != FIVE_FOOT:  # five-foot entries keep their original keys
            m['layer'] = layer
        if sub is not None:
            m['subtier'] = sub
        entries.append(m)
    return entries


def sort_key(m: dict):
    return (m['tier'], m.get('subtier', 0), m['priority_key_m'], m['name'])


PRIORITY = {
    'tier1': {'zone': 'olympic_park', 'box_bng': OLYMPIC_BOX, 'rank_by': f'distance from {OLYMPIC_CENTRE}'},
    'tier2': {'zone': 'other', 'box_bng': SECONDARY_BOX,
              'note': 'Abbey Mills, Channelsea south, Bow Creek, Plaistow marsh',
              'rank_by': f'distance from Abbey Mills {ABBEY_MILLS}'},
    'tier3': {'zone': 'other', 'rank_by': 'distance from the Olympic Park box edge'},
}
PRIORITY_EXTRA = {
    'tier4': {'zone': 'gap_fill', 'layer': 'os-25-inch-london', 'prefix': 'q18',
              'note': 'OS 25-inch (1:2500) mosaics where the five-foot mosaic is skipped or >25% missing',
              'rank_by': f'distance from Abbey Mills {ABBEY_MILLS}'},
    'tier5': {'zone': 'skeleton_1848', 'layer': 'os-london-skeleton-5280', 'prefix': 's18',
              'note': 'OS London 1:5,280 skeleton survey 1848-51, whole extent; a separate (earlier) '
                      'observation, never merged with 1890s marks',
              'rank_by': 'subtier 1-3 = the five-foot tier 1-3 zone logic, then that tier\'s distance key'},
}


def build(reset: bool) -> None:
    entries = [m for layer in LAYER_SETS for m in index_entries(layer)]
    entries.sort(key=sort_key)
    with locked():
        old = {}
        if MANIFEST.exists() and not reset:
            old = {m['name']: m for m in json.loads(MANIFEST.read_text())['mosaics']}
        for k, m in enumerate(entries, 1):
            m['priority_rank'] = k
            prev = old.get(m['name'])
            if prev:
                m['readers'], m['assigned'], m['done'] = prev['readers'], prev.get('assigned', {}), prev.get('done', {})
        # legacy prototype readings
        for m in entries:
            if (READINGS / f"{m['name']}.json").exists() and LEGACY_READER not in m['readers']:
                m['readers'].append(LEGACY_READER)
                m['assigned'][LEGACY_READER] = 'prototype'
                m['done'][LEGACY_READER] = 'prototype'
        tiers = {m['tier'] for m in entries}
        doc = {
            'description': 'Spot-height reading manifest: OS London five-foot 1893-96, zoom 18, 4x4-tile mosaics, '
                           '1-tile overlap. Single source of truth; update only via scripts/spot_height_manifest.py.',
            'priority': {**PRIORITY, **{k: v for k, v in PRIORITY_EXTRA.items() if int(k[4:]) in tiers}},
            'reading_file': 'readings/<mosaic>.<reader>.json (legacy readings/<mosaic>.json = opus-a)',
            'created': now(),
            'mosaics': entries,
        }
        save(doc)
    print(f'{len(entries)} mosaics in manifest ({sum(m["available"] for m in entries)} available) -> {MANIFEST}')


def extend() -> None:
    """Append mosaics not yet in the manifest; never touches existing entries."""
    with locked():
        doc = load()
        have = {m['name'] for m in doc['mosaics']}
        new = [m for layer in LAYER_SETS for m in index_entries(layer) if m['name'] not in have]
        new.sort(key=sort_key)
        last = max((m['priority_rank'] for m in doc['mosaics']), default=0)
        for k, m in enumerate(new, last + 1):
            m['priority_rank'] = k
        doc['mosaics'].extend(new)
        tiers = {m['tier'] for m in doc['mosaics']}
        for k, v in PRIORITY_EXTRA.items():
            if int(k[4:]) in tiers and k not in doc['priority']:
                doc['priority'][k] = v
        doc.setdefault('layers', {})
        for layer, (prefix, index, _) in LAYER_SETS.items():
            if any(entry_layer(m) == layer for m in doc['mosaics']):
                doc['layers'].setdefault(layer, {'prefix': prefix,
                                                 'folder': str(index.parent.relative_to(BASE)) + '/'})
        if new:
            save(doc)
    by = {}
    for m in new:
        by[(m['tier'], entry_layer(m))] = by.get((m['tier'], entry_layer(m)), 0) + 1
    print(f'extend: {len(new)} new mosaic(s) appended'
          + (f' (ranks {new[0]["priority_rank"]}-{new[-1]["priority_rank"]})' if new else ''))
    for (t, layer), n in sorted(by.items()):
        print(f'  tier {t} {layer}: {n} ({sum(1 for m in new if m["tier"] == t and m["available"])} available)')


# -------------------------------------------------------------- selection

def select(doc, n, exclude, only_read, max_readers, layer=None):
    out = []
    for m in sorted(doc['mosaics'], key=lambda m: m['priority_rank']):
        if not m['available']:
            continue
        if layer and entry_layer(m) != layer:
            continue
        rd = m['readers']
        if exclude:
            if any(r in rd for r in exclude) or len(rd) >= max_readers:
                continue
            if only_read and not m['done']:
                continue
        elif rd:
            continue
        out.append(m)
        if len(out) >= n:
            break
    return out


def show(ms):
    for m in ms:
        e, n = m['centroid_bng']
        print(f"{m['name']}  rank {m['priority_rank']:4d}  tier {m['tier']}  {m['priority_zone']:13s} "
              f"E {e:.0f} N {n:.0f}  missing {m['missing_tiles']}  readers {','.join(m['readers']) or '-'}"
              + (f"  layer {entry_layer(m)}" if entry_layer(m) != FIVE_FOOT else ''))


def assign(doc, reader, names) -> list[str]:
    by = {m['name']: m for m in doc['mosaics']}
    got = []
    for name in names:
        m = by.get(name)
        if m is None:
            print(f'unknown mosaic {name}', file=sys.stderr)
            continue
        if not m['available']:
            print(f'{name}: not available ({m["skip_reason"]})', file=sys.stderr)
            continue
        if reader in m['readers']:
            print(f'{name}: already assigned to {reader}', file=sys.stderr)
            continue
        if m['readers']:
            print(f'{name}: note, also read/claimed by {",".join(m["readers"])} (second read)', file=sys.stderr)
        m['readers'].append(reader)
        m['assigned'][reader] = now()
        got.append(name)
    return got


def cmd_status(doc) -> None:
    ms = doc['mosaics']
    avail = [m for m in ms if m['available']]
    print(f"manifest: {len(ms)} lattice mosaics, {len(avail)} available, "
          f"{len(ms) - len(avail)} skipped ({sum(1 for m in ms if m['skip_reason'] and 'missing' in m['skip_reason'])} "
          f"mostly missing, {sum(1 for m in ms if m['skip_reason'] and 'blank' in m['skip_reason'])} blank)")
    for zone in ('olympic_park', 'other', 'gap_fill', 'skeleton_1848'):
        z = [m for m in avail if m['priority_zone'] == zone]
        if not z and zone in ('gap_fill', 'skeleton_1848'):
            continue
        done = [m for m in z if m['done']]
        claimed = [m for m in z if m['readers'] and not m['done']]
        multi = [m for m in z if len(m['done']) >= 2]
        print(f"  {zone:13s} {len(z):4d} available | read {len(done):4d} | claimed, unfinished {len(claimed):3d} | "
              f"unread {len(z) - len(done) - len(claimed):4d} | read by 2+ {len(multi)}")
    for t in sorted({m['tier'] for m in ms} | {1, 2, 3}):
        z = [m for m in avail if m['tier'] == t]
        layers = sorted({entry_layer(m) for m in ms if m['tier'] == t})
        tag = f"  [{', '.join(layers)}]" if layers and layers != [FIVE_FOOT] else ''
        ranks = [m['priority_rank'] for m in ms if m['tier'] == t]
        rr = f", ranks {min(ranks)}-{max(ranks)}" if ranks else ''
        print(f"  tier {t}: {len(z)} available, {sum(1 for m in z if m['done'])} read, "
              f"{sum(1 for m in z if m['readers'] and not m['done'])} claimed{rr}{tag}")
    readers = {}
    for m in ms:
        for r in m['readers']:
            s = readers.setdefault(r, [0, 0])
            s[0] += 1
            s[1] += r in m['done']
    for r, (a, d) in sorted(readers.items()):
        print(f"  reader {r:12s} assigned {a:4d}  done {d:4d}")
    # consistency with readings/
    problems = []
    for m in ms:
        for r in m['done']:
            if reading_path(m['name'], r) is None:
                problems.append(f"{m['name']}: marked done by {r} but no readings file")
    by_name = {m['name']: m for m in ms}
    names = set(by_name)
    for p in sorted(READINGS.glob('*.json')):
        parts = p.name[:-5].split('.')
        mosaic, reader = parts[0], parts[1] if len(parts) > 1 else LEGACY_READER
        if mosaic not in names:
            problems.append(f'{p.name}: mosaic not in manifest')
            continue
        m = by_name[mosaic]
        if reader not in m['done']:
            problems.append(f"{p.name}: readings file exists but not marked done "
                            f"({'claimed' if reader in m['readers'] else 'not claimed'})")
    print(f"  consistency: {len(problems)} issue(s)")
    for p in problems[:30]:
        print(f"    {p}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    b = sub.add_parser('build')
    b.add_argument('--reset', action='store_true')
    sub.add_parser('extend')

    def filters(p):
        p.add_argument('--exclude-readers', nargs='+', default=[], metavar='R')
        p.add_argument('--only-read', action='store_true')
        p.add_argument('--max-readers', type=int, default=2,
                       help='with --exclude-readers, skip mosaics that already have this many readers')
        p.add_argument('--layer', default=None, metavar='L',
                       help='only mosaics of this layer (id, or prefix m18 / q18 / s18)')
    nx = sub.add_parser('next')
    nx.add_argument('n', type=int)
    filters(nx)
    cl = sub.add_parser('claim')
    cl.add_argument('reader')
    cl.add_argument('n', type=int)
    filters(cl)
    for name in ('assign', 'done', 'release'):
        p = sub.add_parser(name)
        p.add_argument('reader')
        p.add_argument('mosaics', nargs='+')
    sub.add_parser('status')
    sub.add_parser('sync')
    a = ap.parse_args()

    if a.cmd == 'build':
        build(a.reset)
    elif a.cmd == 'extend':
        extend()
    elif a.cmd == 'next':
        show(select(load(), a.n, a.exclude_readers, a.only_read, a.max_readers, resolve_layer(a.layer)))
    elif a.cmd == 'status':
        cmd_status(load())
    else:
        with locked():
            doc = load()
            if a.cmd == 'claim':
                ex = a.exclude_readers or []
                lay = resolve_layer(a.layer)
                picks = select(doc, a.n, ex + [a.reader] if ex else [], a.only_read, a.max_readers, lay) \
                    if ex else select(doc, a.n, [], False, 0, lay)
                got = assign(doc, a.reader, [m['name'] for m in picks])
            elif a.cmd == 'assign':
                got = assign(doc, a.reader, a.mosaics)
            elif a.cmd == 'done':
                got = []
                by = {m['name']: m for m in doc['mosaics']}
                for name in a.mosaics:
                    m = by.get(name)
                    if m is None:
                        print(f'unknown mosaic {name}', file=sys.stderr)
                    elif reading_path(name, a.reader) is None:
                        print(f'{name}: no readings/{name}.{a.reader}.json; not marked', file=sys.stderr)
                    else:
                        if a.reader not in m['readers']:
                            m['readers'].append(a.reader)
                            m['assigned'][a.reader] = now()
                        m['done'][a.reader] = now()
                        got.append(name)
            elif a.cmd == 'sync':
                got = []
                by = {m['name']: m for m in doc['mosaics']}
                for p in sorted(READINGS.glob('*.json')):
                    parts = p.name[:-5].split('.')
                    mosaic, reader = parts[0], parts[1] if len(parts) > 1 else LEGACY_READER
                    m = by.get(mosaic)
                    if m is None or reader in m['done']:
                        continue
                    if reader not in m['readers']:
                        m['readers'].append(reader)
                        m['assigned'][reader] = 'sync'
                    m['done'][reader] = now()
                    got.append(f'{mosaic} {reader}')
            else:  # release
                got = []
                by = {m['name']: m for m in doc['mosaics']}
                for name in a.mosaics:
                    m = by.get(name)
                    if m and a.reader in m['readers'] and a.reader not in m['done']:
                        m['readers'].remove(a.reader)
                        m['assigned'].pop(a.reader, None)
                        got.append(name)
                    else:
                        print(f'{name}: not an unfinished claim of {a.reader}', file=sys.stderr)
            if got:
                save(doc)
        print(f'{a.cmd} {getattr(a, "reader", "")}: {len(got)} mosaic(s)')
        for g in got:
            print(g)


if __name__ == '__main__':
    main()
