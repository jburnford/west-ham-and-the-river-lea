"""Setting of a spot-height mark: what kind of ground the height describes.

Readers record `setting` per reading (closed vocabulary, SETTINGS below). For
readings written before the field existed, infer_setting() classifies the
free-text `notes` (and the type) with ordered keyword rules. The merge
(spot_height_merge.py) applies it at merge time; the reading files are never
modified.

How a note is classified
  1. The note is split into clauses at ';'. Readers put the place first
     ("Hackney Cut towing path; dot left of figures; 8x"), so the first clause
     that yields a setting wins.
  2. Names are masked: the word(s) before a street or watercourse suffix
     (Marsh Lane, Bridge Road, Park Road, Waterworks River, Station Road) do not
     count as setting keywords, and the suffix itself counts as 'street'.
  3. A few phrases are decided on the whole clause: "foot of the ...
     embankment/bank" -> embankment_foot; "water level" (unless negated) -> water.
  4. The clause is cut at the first landmark preposition (by, near, beside,
     opposite, "north of", under, over, where ...): "road north of the sewer" is a
     road, not the sewer bank. Parentheses are set aside; a parenthesis that
     names a bridge, bank or wall ("High Street (bridge approach)") overrides
     a lower-priority head.
  5. In what is left, the highest-priority setting whose keywords occur wins:
     embankment_foot > water > bridge > wall_top > embankment_top > yard >
     railway > building > marsh > open_ground > (generic open ground) > street.
     Place words decide marsh (marsh, meads, level, moor, osier bed) versus
     open_ground (park, field, garden, allotment, nursery, brick field,
     cemetery, recreation ground). Notes that say only "open ground", "ground",
     "track", "strip", "enclosure" or "between drains" fall back on the value:
     below 15 ft -> marsh, otherwise open_ground (rule 'value_fallback').
  6. Bench marks: a parapet anywhere in the note -> bridge; a bench mark whose
     place is only a street is on a building or wall at street level ->
     building.
  7. If no clause head yields anything, a street named in the landmark part
     ("written below B.M.25.88 on West Ham Lane") -> street. Otherwise unknown.

CLI (tuning report over the reading files; writes nothing):
  python3 scripts/spot_height_setting.py                # table, unknown share, 30 examples
  python3 scripts/spot_height_setting.py --examples 50 --seed 2
  python3 scripts/spot_height_setting.py --list unknown  # every reading left unknown
  python3 scripts/spot_height_setting.py --list bridge   # every reading inferred as bridge
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
READINGS = ROOT / 'reference/spot-heights/readings'

# closed vocabulary, in documentation order
SETTINGS = {
    'marsh': 'low wet ground: marsh, meads, level, moor, osier bed, grazing by the foreshore; '
             'open ground in the Lea / Channelsea / Bow Creek valley below about 15 ft',
    'open_ground': 'parks, recreation grounds, fields, gardens, allotments, nurseries, brick fields, '
                   'cemeteries and other unbuilt ground on the terrace',
    'street': 'road, lane, pavement, street corner',
    'yard': 'works yard, goods yard, made ground in premises',
    'embankment_top': 'crest of a railway, sewer or flood bank; towing path on a bank',
    'embankment_foot': 'ground at the foot of a bank (even if on a road)',
    'wall_top': 'river wall, quay, lock side, canal wall',
    'bridge': 'bridge deck, approach ramp, parapet B.M.',
    'railway': 'dot on the rails at grade (not on an embankment)',
    'building': 'B.M. on a building or ordinary wall at street level, or a figure on a building',
    'water': 'a genuine water level (rare)',
    'other': 'none of the above',
}
SOURCES = ('reader', 'inferred', 'unknown')
VALUE_FALLBACK = 'value_fallback'
MARSH_BELOW_FT = 15.0  # generic 'open ground' below this is marsh, at or above it open_ground
# 'open' is internal: unbuilt ground with no place word, resolved by value to marsh / open_ground
PRIORITY = ['embankment_foot', 'water', 'bridge', 'wall_top', 'embankment_top', 'yard', 'railway',
            'building', 'other', 'marsh', 'open_ground', 'open', 'street']
# bench marks are cut on structures: a building/wall named in the note outranks yard and railway
PRIORITY_BM = ['embankment_foot', 'water', 'bridge', 'wall_top', 'embankment_top', 'building', 'yard',
               'railway', 'other', 'marsh', 'open_ground', 'open', 'street']
OVERRIDE_FROM_PARENS = {'bridge', 'embankment_foot', 'embankment_top', 'wall_top'}

W = r"[\w'’.&-]+"  # one word of a name
STREET_SUFFIX = (r'road|roads|rd|street|streets|lane|grove|terrace|terraces|avenue|place|broadway|crescent|'
                 r'row|walk|square|gardens|hill|parade|mews|passage|station')
WATER_SUFFIX = r'river|creek|cut|canal|ditch|drain|dock|docks'

# phrases that are names, not settings (applied before masking)
NAME_FIXES = [
    (re.compile(r'\bshort wall\b'), 'NAME street'),                  # a street called Short Wall
    (re.compile(r'\blong wall\b(?! river)'), 'NAME wall-top'),       # the Long Wall (river wall, Three Mills)
    (re.compile(r'\bwall river\b'), 'NAME river'),                   # Three Mills Wall River
    (re.compile(r'\b(?:low level|high level)\b'), 'NAME'),           # Stratford Low Level (station)
    (re.compile(r'\b(?:c\.c\. at l\.w\.)'), 'NAME'),                 # boundary note 'C.C. at L.W.'
    (re.compile(r'\bground level at\b'), 'NAME at'),
    (re.compile(r'\bvictoria park\b'), 'NAME'),
    (re.compile(r'\brailway boundary\b'), 'boundary'),               # railway boundary wall = ordinary wall
    (re.compile(r'\boverlap strip\b'), 'overlap'),
    (re.compile(r'\b(fire|police) station\b'), r'\1-station'),        # a building, not the railway
    # the grounds or garden of a building are open ground, not the building
    (re.compile(r"\b(?:vicarage|cottage|institute|church|convent|school|house|hall|room)(?:'s)? (?=grounds?\b|garden\b|plot\b)"),
     'NAME '),
]
# a name word is never a preposition or article ('near station bridge' keeps its 'near')
STOP = (r'(?!(?:by|near|beside|opposite|behind|past|towards?|to|of|at|on|in|into|and|or|a|an|the|from|off|'
        r'under|over|above|below|across|along|inside|within|outside|where|north|south|east|west)\b)')
NAME_WORD = STOP + W
MASK_STREET = re.compile(rf'\b{NAME_WORD}\s+(?=(?:{STREET_SUFFIX})\b)')
# watercourse names are capitalised in the notes (Waterworks River, City Mill River); matched on the
# original case so 'bank between the river' keeps its 'bank'
MASK_WATER = re.compile(rf"\b(?:[A-Z][\w'’.&-]*\s+){{1,2}}(?=(?i:{WATER_SUFFIX})\b)")
# where the dot or pheon sits relative to the lettering: never a setting
REL_TEXT = re.compile(r"\b(?:about |some |~)?(?:\d+(?:-\d+)? ?px )?(?:directly |just |immediately )?"
                      r"(?:above|below|under|beneath|left|right|over)(?:-(?:left|right))?(?: of)? "
                      r"(?:the )?(?:stacked |two-line )?(?:b\.m\. ?)?(?:text|figures?|lettering)\b")

FOOT = re.compile(r"\b(?:foot|bottom|base|toe)\b(?:/\w+)?(?: line)? of (?:the )?(?:[\w.&'’/-]+ ){0,5}?"
                  r"(?:embankment|bank|slope|ramp|wall|wall-top)s?\b"
                  r"|\b(?:embankment|bank) foot\b"
                  r"|\b(?:under|below|beneath) the (?:[\w.&'’/-]+ ){0,3}?embankment\b(?! hatching)")
WATER_LEVEL = re.compile(r'\bwater[- ]level\b')
WATER_NEG = re.compile(r'\b(?:not|no|could be|might be|may be|possibl\w*|rather than)\s+(?:a\s+)?water[- ]level')
# guide: figures over a channel are wall tops (dot on the bank); figures on foreshore are embankment tops
OVER_WATER = re.compile(r"^(?:figures?|figure written|written)? ?over the (?:[\w'.-]+ ){0,2}?"
                        r"(?:channel|channelsea|river|cut|creek|lea|water)\b")
FORESHORE = re.compile(r'\b(?:foreshore|mud)\b')

CUT = re.compile(r"\b(?:by|near|beside|besides|opposite|behind|past|towards?|next to|close to|alongside|"
                 r"adjoining|along|a?round|facing|off|from|under|beneath|below|above|over|across|beyond|outside|inside|within|"
                 r"where|crossing the|in front of|on the (?:[\w-]+ )?side of|"
                 r"(?:north|south|east|west|n|s|e|w|ne|nw|se|sw)(?:[- ]?(?:east|west))? of)\b")
# a head made only of these words says nothing; after 'over' the next words are the setting
FILLER = re.compile(r"^(?:\W|\b(?:text|figures?|figure|written|drawn|directly|just|mark|dot|pheon|point|"
                    r"the|a|an|stacked|b\.m\.|NAME)\b)*$")

WALL_WATER = re.compile(r"\b(?:river|canal|cut|lock|channel|creek|dock|towing|tow|quay|wharf|sea|lea|water|"
                        r"hachured|embankment)\b[^;]*\bwalls?\b|\bwalls?\b[^;]*\b(?:river|canal|lock|channel|creek|"
                        r"dock|quay)\b|\bwall[- ]top\b|\btop of (?:the )?[\w ]{0,20}wall\b")

KEYWORDS = {
    'bridge': [r'\bbridges?\b', r'\bparapets?\b', r'\bviaduct\b', r'\bfootbridge\b', r'\bf\.b\.',
               r'\babutments?\b', r'\bculverts?\b', r'\baqueduct\b', r'\bapproach ramp\b'],
    'wall_top': [r'\bquay\b', r'\block\b(?!-keeper)', r'\block[- ](?:side|head|wall|gates?)\b', r'\bsluice\b',
                 r'\bweir\b', r'\bflood ?gates?\b', r'\bcoping\b'],
    'embankment_top': [r'\bembankments?\b', r'\bembanked\b', r'\bbanks?\b', r'\btowing[- ]?paths?\b',
                       r'\btow[- ]?paths?\b', r'\bsewer\b', r'\boutfall\b', r'\bcrest\b', r'\blevee\b',
                       r'\bspoil\b', r'\bforeshore\b'],
    'yard': [r'\byards?\b', r'\bworks\b', r'\bgoods\b', r'\bdepot\b', r'\bpremises\b', r'\bwharf\b',
             r'\bdistillery\b', r'\bfactory\b', r'\bmills?\b', r'\bmade ground\b', r'\bforecourt\b',
             r'\bgas ?works\b', r'\btimber\b', r'\bcoal\b', r'\bmanure\b', r'\bmanufactory\b'],
    'railway': [r'\brailway\b', r'\brly\b', r'\bg\.?e\.?r\b\.?', r'\bl\.?t\.? ?& ?s\.?r\b', r'\bn\.?l\.?r\b',
                r'\brails?\b', r'\bsidings?\b', r'\bplatforms?\b', r'\bsignal\b', r'\bloop\b', r'\bbranch\b',
                r'\btracks\b', r'\bturntable\b',
                r'\b(?:low level|main|running|up|down|rail|railway|goods|southend|woolwich|north london|'
                r'NAME)\s+lines?\b', r'\bNAME junction\b', r'(?<!-)\bstation\b'],
    'building': [r'\bbuildings?\b', r'\bhouses?\b', r'\bcottages?\b', r'\bchurch\b', r'\bchapel\b',
                 r'\bschools?\b', r'\bp\.?h\.', r'\binn\b', r'\bhotel\b', r'\balmshouses\b', r'\bhall\b',
                 r'\binstitute\b', r'\bconvent\b', r'\bmission\b', r'\blodge\b', r'\bshops?\b', r'\boffices?\b',
                 r'\bp\.o\.', r'\bvicarage\b', r'\bshed\b', r'\bblock\b', r'\bwalls?\b', r'\bporch\b',
                 r'\b(?:fire|police)-station\b',
                 r'\bbuilding line\b'],
    'other': [],  # only readers use 'other'
    'marsh': [r'\bmarsh(?:es)?\b', r'\bmeads?\b', r'\bmeadows?\b', r'\bmoors?\b', r'\b[oa]zier',
              r'\bosier', r'\bplaistow level\b', r'(?<!same )(?<!water )\blevel\b(?! crossing)',
              r'\bgrazing\b'],
    'open_ground': [r'\bparks?\b', r'\brecreation\b', r'\bfields?\b', r'\bgarden\b', r'\ballotments?\b',
                    r'\bnursery\b', r'\bnurseries\b', r'\bbrick ?fields?\b', r'\bcemetery\b', r'\bchurchyard\b',
                    r'\bburial ground\b', r'\bgrounds\b', r'\bplot\b', r'\blot\b', r'\bflats\b',
                    r'\bamong trees\b', r'\bband ?stand\b'],
    # unbuilt ground without a place word: marsh or open_ground by value (VALUE_FALLBACK)
    'open': [r'\bopen ground\b', r'(?<!raised )(?<!made )(?<!shaded )(?<!tinted )\bground\b', r'\bpasture\b',
             r'\benclosure\b', r'\bstrips?\b', r'\btrack\b',
             r'\bbetween (?:the )?(?:two )?(?:parallel )?(?:NAME )?drains\b', r'\bunbuilt\b'],
    'street': [rf'\b(?:{STREET_SUFFIX})\b', r'\bjunction\b', r'\bcorner\b', r'\bcrossing\b', r'\bcrossroads\b',
               r'\bkerb\b', r'\bpavement\b', r'\bfootway\b', r'\bfoot ?path\b', r'\bpaths?\b', r'\broadway\b',
               r'\bcarriageway\b', r'\btramway\b', r'\btram\b', r'\bhighway\b', r'\bportway\b', r'\bfork\b',
               r'\bfrontage\b', r'\bfront\b', r'\bNAME approach\b'],
}
KW = {s: [re.compile(p) for p in ps] for s, ps in KEYWORDS.items()}


def _norm(text: str) -> str:
    t = MASK_WATER.sub('NAME ', (text or '').replace('’', "'")).lower().replace('name ', 'NAME ')
    for rx, rep in NAME_FIXES:
        t = rx.sub(rep, t)
    t = MASK_STREET.sub('NAME ', t)
    t = REL_TEXT.sub(' ', t)
    return t


def _parens(clause: str) -> tuple[str, list[str]]:
    inner = re.findall(r'\(([^()]*)\)', clause)
    return re.sub(r'\([^()]*\)', ' ', clause), inner


def _cats(text: str, is_bm: bool) -> list[tuple[str, str]]:
    """All (setting, keyword) hits in text, before priority resolution."""
    out = []
    if WALL_WATER.search(text):
        out.append(('wall_top', 'wall by water'))
    for s, rxs in KW.items():
        for rx in rxs:
            m = rx.search(text)
            if not m:
                continue
            kw = m.group(0).strip()
            if s == 'building' and kw.startswith('wall') and WALL_WATER.search(text):
                continue
            if s == 'railway' and kw == 'station' and is_bm:
                out.append(('building', 'station (B.M.)'))
                continue
            out.append((s, kw))
    return out


def _resolve(hits, is_bm: bool):
    if not hits:
        return None, None
    order = PRIORITY_BM if is_bm else PRIORITY
    return min(hits, key=lambda h: order.index(h[0]))


def _segment(body: str) -> str:
    """The head of a clause: text before the first landmark preposition. A head of
    filler words followed by 'over' ('figures over the works yard') continues after it."""
    m = CUT.search(body)
    if not m:
        return body
    head = body[:m.start()]
    if FILLER.match(head) and m.group(0) == 'over':
        # figures written over a terrace or row of houses are on a building
        rest = re.sub(r'\b(?:terrace|terraces|row|houses)\b', 'building', body[m.end():])
        n = CUT.search(rest)
        return rest[:n.start()] if n else rest
    return head


def _head(clause: str, is_bm: bool):
    """Setting from one clause (already normalised), or (None, None)."""
    if FOOT.search(clause) or FOOT.search(re.sub(r'\s*\([^()]*\)', '', clause)):
        return 'embankment_foot', 'foot of bank'
    if WATER_LEVEL.search(clause) and not WATER_NEG.search(clause):
        return 'water', 'water level'
    body, inner = _parens(clause)
    if not is_bm and OVER_WATER.search(body.strip()):
        return 'wall_top', 'figures over channel'
    head = _segment(body)
    # 'open ground between the Loop and the main line': a setting named before 'between' wins
    b = re.search(r'\bbetween\b', head)
    if b and _cats(head[:b.start()], is_bm):
        head = head[:b.start()]
    # 'Gladstone Road at park gate', 'Broadway at the churchyard': after 'at', only a
    # structure (bridge, bank, wall) or the railway overrides a setting already named
    a = re.search(r'\bat\b', head)
    pre = _cats(head[:a.start()], is_bm) if a else []
    if pre:
        post = [h for h in _cats(head[a.end():], is_bm) if h[0] in OVERRIDE_FROM_PARENS | {'railway'}]
        s, kw = _resolve(pre + post, is_bm)
    else:
        s, kw = _resolve(_cats(head, is_bm), is_bm)
    for p in inner:
        cats = _cats(p, is_bm)
        ps, pkw = _resolve([h for h in cats if h[0] in OVERRIDE_FROM_PARENS or s is None], is_bm)
        order = PRIORITY_BM if is_bm else PRIORITY
        if ps and (s is None or order.index(ps) < order.index(s)):
            s, kw = ps, f'({pkw})'
    return s, kw


def infer_setting(notes: str, type_: str = 'spot', raw: str = '',
                  value_ft: float | None = None) -> tuple[str | None, str | None]:
    """(setting, rule) inferred from a reading's notes; (None, None) if nothing fits.
    Unbuilt ground with no place word is marsh below MARSH_BELOW_FT and open_ground
    otherwise; its rule then starts with VALUE_FALLBACK."""
    s, kw = _infer(notes, type_, raw)
    if s == 'open':
        low = value_ft is not None and value_ft < MARSH_BELOW_FT
        return ('marsh' if low else 'open_ground'), f'{VALUE_FALLBACK} ({kw}, {value_ft} ft)'
    return s, kw


def _infer(notes: str, type_: str, raw: str):
    is_bm = type_ == 'bench_mark' or (raw or '').upper().startswith('B.M')
    t = _norm(notes)
    clauses = [c.strip() for c in t.split(';') if c.strip()]
    if is_bm and re.search(r'\bparapet', t):
        return 'bridge', 'parapet (B.M.)'
    s = kw = None
    for c in clauses:
        s, kw = _head(c, is_bm)
        if s:
            break
    if s is None and clauses:
        body, _ = _parens(clauses[0])
        if re.search(rf'\b(?:{STREET_SUFFIX})\b', body):
            s, kw = 'street', 'street named after landmark'
        elif re.search(r'\bpark\b', body):
            s, kw = 'open_ground', 'park named after landmark'
    if s is None and re.search(r'\b(?:dot|tick)s? (?:\w+ ){0,3}(?:on|between) the rails\b', t):
        s, kw = ('embankment_top', 'dot on rails + embankment') if 'embankment' in t else ('railway', 'dot on rails')
    if s is None:
        return None, None
    if is_bm and s == 'street':
        return 'building', f'{kw} (B.M. at street level)'
    return s, kw


def classify_rule(reading: dict) -> tuple[str | None, str, str | None]:
    """(setting, setting_source, setting_rule) for one reading dict: the reader's value
    if it is in the vocabulary, else the inference, else (None, 'unknown', None).
    setting_rule is VALUE_FALLBACK when the inference rested on the value alone."""
    s = reading.get('setting')
    if s in SETTINGS:
        return s, 'reader', None
    s, kw = infer_setting(reading.get('notes', ''), reading.get('type', 'spot'), reading.get('raw', ''),
                          reading.get('value_ft'))
    if not s:
        return None, 'unknown', None
    return s, 'inferred', (VALUE_FALLBACK if kw and kw.startswith(VALUE_FALLBACK) else None)


def classify(reading: dict) -> tuple[str | None, str]:
    """(setting, setting_source) for one reading dict (see classify_rule)."""
    return classify_rule(reading)[:2]


def keyword_hits(notes: str, type_: str = 'spot') -> set[str]:
    """Every setting whose keywords occur anywhere in the note (for the tuning table)."""
    t = _norm(notes)
    hits = {s for s, _ in _cats(t, type_ == 'bench_mark')}
    if FOOT.search(t):
        hits.add('embankment_foot')
    if WATER_LEVEL.search(t) and not WATER_NEG.search(t):
        hits.add('water')
    return hits


# ----------------------------------------------------------------------- CLI

def _load(folder: Path):
    rows = []
    for p in sorted(folder.glob('*.json')):
        try:
            doc = json.loads(p.read_text())
        except json.JSONDecodeError:
            continue
        for i, r in enumerate(doc.get('readings', [])):
            rows.append({**r, 'file': p.name, 'idx': i})
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--dir', type=Path, default=READINGS)
    ap.add_argument('--examples', type=int, default=30)
    ap.add_argument('--seed', type=int, default=1893)
    ap.add_argument('--list', metavar='SETTING', help="print every reading with this outcome ('unknown' too)")
    args = ap.parse_args()
    rows = _load(args.dir)
    res = []
    for r in rows:
        if r.get('setting') in SETTINGS:
            s, rule, src = r['setting'], 'reader', 'reader'
        else:
            s, rule = infer_setting(r.get('notes', ''), r.get('type', 'spot'), r.get('raw', ''), r.get('value_ft'))
            src = 'inferred' if s else 'unknown'
        res.append((r, s or 'unknown', rule, src))
    if args.list:
        for r, s, rule, _ in res:
            if s == args.list:
                print(f"{r['file'][:28]:28s} {r['raw']:>10s}  [{rule}]  {r.get('notes', '')}")
        return
    n = len(res)
    cols = list(SETTINGS)
    print(f'{n} readings in {len({r["file"] for r in rows})} files; '
          f'reader-supplied setting: {sum(src == "reader" for *_, src in res)}')
    print('\nAssigned setting (rows) x settings whose keywords occur anywhere in the note (columns):')
    cols_hit = cols + ['open']
    abbrev = {'marsh': 'marsh', 'open_ground': 'open_gr', 'open': 'generic', 'street': 'street', 'yard': 'yard', 'embankment_top': 'emb_top',
              'embankment_foot': 'emb_ft', 'wall_top': 'wall', 'bridge': 'bridge', 'railway': 'rail',
              'building': 'bldg', 'water': 'water', 'other': 'other'}
    print(f"{'':16s}{'n':>6s} {'%':>6s} " + ' '.join(f'{abbrev[c]:>7s}' for c in cols_hit))
    for s in cols + ['unknown']:
        sub = [r for r, ss, *_ in res if ss == s]
        if not sub:
            continue
        hc = Counter(h for r in sub for h in keyword_hits(r.get('notes', ''), r.get('type', 'spot')))
        print(f'{s:16s}{len(sub):6d} {len(sub) / n:6.1%} ' + ' '.join(f'{hc[c]:7d}' for c in cols_hit))
    unk = sum(s == 'unknown' for _, s, *_ in res)
    print(f'\nunknown: {unk}/{n} = {unk / n:.1%}')
    fb = Counter(s for _, s, rule, _ in res if rule and rule.startswith(VALUE_FALLBACK))
    print(f'value fallback (generic open ground, split at {MARSH_BELOW_FT:g} ft): '
          + (', '.join(f'{k} {v}' for k, v in sorted(fb.items())) or 'none'))
    given = [r for r in rows if r.get('setting') in SETTINGS]
    if given:
        inf = [(r['setting'], infer_setting(r.get('notes', ''), r.get('type', 'spot'), r.get('raw', ''),
                                            r.get('value_ft'))[0]) for r in given]
        ok = sum(a == b for a, b in inf)
        print(f'classifier check on {len(given)} reader-supplied settings: inferred value agrees for {ok} '
              f'({ok / len(given):.0%}); disagreements: '
              + (', '.join(f'{a}->{b}' for a, b in inf if a != b) or 'none'))
    print('\nMost frequent deciding keywords per setting:')
    by = defaultdict(Counter)
    for _, s, rule, _ in res:
        if rule:
            by[s][re.sub(r', [-\d.]+ ft\)$|, None ft\)$', ')', rule)] += 1
    for s in cols:
        if by[s]:
            print(f'  {s:16s} ' + ', '.join(f'{k} {v}' for k, v in by[s].most_common(10)))
    print(f'\n{args.examples} random readings (seed {args.seed}):')
    rnd = random.Random(args.seed)
    for r, s, rule, _ in rnd.sample(res, min(args.examples, n)):
        print(f"  {s:15s} [{rule}] {r['raw']}: {r.get('notes', '')[:110]}")


if __name__ == '__main__':
    main()
