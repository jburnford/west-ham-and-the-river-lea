"""Upscaled, labelled crops of spot-height mosaics for vision-model readers.

Mosaic names resolve to their folder by prefix: m18_* (five-foot) in
reference/spot-heights/mosaics/, q18_* (25-inch gap fill) in mosaics-25inch/,
s18_* (1848-51 skeleton survey) in mosaics-1848/.

All positions printed on the crops and on stdout are MOSAIC pixel coordinates
(px, py from the top-left of the 1024 px mosaic), so a reader can report them
straight into the readings JSON without any arithmetic.

Modes
  sweep <mosaic> [--crop 448 --min-overlap 64 --scale 2 --grid 64]
      Cut the mosaic into a 3 x 3 grid of 448 px crops (origins 0, 288, 576,
      i.e. 160 px overlap, never less than --min-overlap), upscale 2x with
      LANCZOS and draw a thin grid every 64 mosaic px, labelled in a margin
      with mosaic coordinates. Prints each file and its mosaic-pixel bounds.
  zoom <mosaic> <px> <py> [--scale 6] [--half 40]
      Crop (px-half .. px+half) around one mosaic pixel, upscale, mark the
      requested pixel with an open crosshair (the centre is left clear so the
      survey dot is not hidden) and label ticks in mosaic pixels.
  sheet <mosaic>
      Best-effort detection of OS sheet joins: a sharp step in the paper tint
      along x (vertical join) or y (horizontal join), evaluated per 256 px band.

Output directory: --out DIR, else $CLAUDE_SCRATCHPAD/crops/<mosaic>/, else
this session's scratchpad (see DEFAULT_SCRATCH). Readers running in another
session should pass --out explicitly.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from spot_height_mosaics import font, mosaic_dir  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
MOSAICS = ROOT / 'reference/spot-heights/mosaics'
DEFAULT_SCRATCH = Path('/tmp/claude-1000/-home-jic823-book-website/'
                       '77193617-f881-4ca3-975a-bc875ce1ab9e/scratchpad')
MISSING_RGB = (200, 200, 200)
LINE = (230, 0, 150, 90)
LABEL = (190, 0, 110)


def out_dir(args, mosaic: str) -> Path:
    if args.out:
        d = Path(args.out)
    else:
        base = Path(os.environ['CLAUDE_SCRATCHPAD']) if os.environ.get('CLAUDE_SCRATCHPAD') else DEFAULT_SCRATCH
        d = base / 'crops' / mosaic
    d.mkdir(parents=True, exist_ok=True)
    return d


def load(mosaic: str) -> tuple[Image.Image, dict]:
    """Mosaic by name; the folder follows the prefix (m18_* mosaics/,
    q18_* mosaics-25inch/, s18_* mosaics-1848/)."""
    mosaic = Path(mosaic).name.removesuffix('.png').removesuffix('.grid')
    try:
        folder = mosaic_dir(mosaic)
    except ValueError as e:
        sys.exit(str(e))
    png = folder / f'{mosaic}.png'
    if not png.exists():
        sys.exit(f'no mosaic {png}')
    meta = json.loads((folder / f'{mosaic}.json').read_text())
    if meta.get('layer', 'os-london-five-foot-1893') != 'os-london-five-foot-1893':
        print(f"{mosaic}: layer {meta['layer']} ({meta.get('scale', '')}), {meta.get('source', '')}")
    return Image.open(png).convert('RGB'), meta


def crop_padded(img: Image.Image, x0: int, y0: int, x1: int, y1: int) -> Image.Image:
    """Crop that may extend past the mosaic edge (padded with missing-tile grey)."""
    out = Image.new('RGB', (x1 - x0, y1 - y0), MISSING_RGB)
    sx0, sy0, sx1, sy1 = max(x0, 0), max(y0, 0), min(x1, img.width), min(y1, img.height)
    if sx1 > sx0 and sy1 > sy0:
        out.paste(img.crop((sx0, sy0, sx1, sy1)), (sx0 - x0, sy0 - y0))
    return out


def framed(crop: Image.Image, x0: int, y0: int, scale: float, step: int, lines: bool,
           margin: int = 30, title: str = '') -> tuple[Image.Image, ImageDraw.ImageDraw]:
    """Upscale crop and put it in a white frame with mosaic-pixel tick labels."""
    big = crop.resize((round(crop.width * scale), round(crop.height * scale)), Image.LANCZOS)
    W, H = big.width + 2 * margin, big.height + 2 * margin
    top = margin + (16 if title else 0)
    canvas = Image.new('RGB', (W, H + top - margin), (255, 255, 255))
    canvas.paste(big, (margin, top))
    base = canvas.convert('RGBA')
    layer = Image.new('RGBA', base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = font(11)
    x1, y1 = x0 + crop.width, y0 + crop.height
    first_x = math.ceil(x0 / step) * step
    first_y = math.ceil(y0 / step) * step
    for v in range(first_x, x1 + 1, step):
        X = margin + (v - x0) * scale
        if lines:
            d.line([(X, top), (X, top + big.height)], fill=LINE, width=1)
        for yy in (top - 6, top + big.height):
            d.line([(X, yy), (X, yy + 6)], fill=LABEL + (255,), width=1)
        lab = str(v)
        tw = d.textlength(lab, font=f)
        d.text((X - tw / 2, top - 19), lab, fill=LABEL + (255,), font=f)
        d.text((X - tw / 2, top + big.height + 7), lab, fill=LABEL + (255,), font=f)
    for v in range(first_y, y1 + 1, step):
        Y = top + (v - y0) * scale
        if lines:
            d.line([(margin, Y), (margin + big.width, Y)], fill=LINE, width=1)
        for xx in (margin - 6, margin + big.width):
            d.line([(xx, Y), (xx + 6, Y)], fill=LABEL + (255,), width=1)
        lab = str(v)
        tw = d.textlength(lab, font=f)
        d.text((margin - 7 - tw, Y - 7), lab, fill=LABEL + (255,), font=f)
        d.text((margin + big.width + 7, Y - 7), lab, fill=LABEL + (255,), font=f)
    if title:
        d.text((margin, 3), title, fill=(0, 0, 0, 255), font=font(12))
    img = Image.alpha_composite(base, layer).convert('RGB')
    return img, top


def sweep_origins(size: int, crop: int, min_overlap: int) -> list[int]:
    if crop >= size:
        return [0]
    n = math.ceil((size - min_overlap) / (crop - min_overlap))
    return [round(i * (size - crop) / (n - 1)) for i in range(n)]


def cmd_sweep(a) -> None:
    img, meta = load(a.mosaic)
    name = meta['name']
    d = out_dir(a, name)
    xs = sweep_origins(img.width, a.crop, a.min_overlap)
    ys = sweep_origins(img.height, a.crop, a.min_overlap)
    missing = meta.get('missing_tiles', [])
    print(f'{name}: {len(ys)} x {len(xs)} crops of {a.crop} px, x origins {xs}, y origins {ys}, '
          f'overlap {a.crop - (xs[1] - xs[0]) if len(xs) > 1 else 0} px, scale {a.scale}x, grid {a.grid} px')
    if missing:
        print(f'  missing tiles (grey fill): {missing}')
    for r, y0 in enumerate(ys):
        for c, x0 in enumerate(xs):
            x1, y1 = min(x0 + a.crop, img.width), min(y0 + a.crop, img.height)
            title = f'{name}  r{r}c{c}  mosaic px x {x0}-{x1}, y {y0}-{y1}  ({a.scale:g}x)'
            out, _ = framed(img.crop((x0, y0, x1, y1)), x0, y0, a.scale, a.grid, True, title=title)
            path = d / f'{name}_r{r}c{c}.png'
            out.save(path)
            print(f'  {path}  bounds [{x0}, {y0}, {x1}, {y1}]')


def cmd_zoom(a) -> None:
    img, meta = load(a.mosaic)
    name = meta['name']
    d = out_dir(a, name)
    h = a.half
    x0, y0 = a.px - h, a.py - h
    crop = crop_padded(img, x0, y0, a.px + h + 1, a.py + h + 1)
    step = 10 if h <= 60 else 20 if h <= 120 else 50
    title = f'{name}  zoom at px {a.px},{a.py}  ({a.scale:g}x, +-{h} px)'
    out, top = framed(crop, x0, y0, a.scale, step, a.lines, margin=34, title=title)
    dr = ImageDraw.Draw(out)
    cx = 34 + (a.px - x0 + 0.5) * a.scale
    cy = top + (a.py - y0 + 0.5) * a.scale
    gap, arm = max(3 * a.scale, 10), max(5 * a.scale, 16)
    col = (0, 120, 255)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        dr.line([(cx + dx * gap, cy + dy * gap), (cx + dx * (gap + arm), cy + dy * (gap + arm))], fill=col, width=2)
    path = d / f'{name}_zoom_{a.px}_{a.py}_s{a.scale:g}.png'
    out.save(path)
    print(f'{path}  bounds [{x0}, {y0}, {a.px + h + 1}, {a.py + h + 1}]  crosshair at mosaic px {a.px},{a.py} '
          f'(ticks every {step} px)')


# ------------------------------------------------------------ sheet joins

def paper_profile(arr: np.ndarray, axis: int) -> np.ndarray:
    """Median paper colour of each line across a band (axis=0: per column).

    Paper is bright and warm (R >= G >= B); the blue-green water wash, the
    grey missing-tile fill and the pure white outside the sheets are excluded."""
    import warnings
    rgb = arr.astype(float)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    lum = rgb.mean(2)
    blank = (rgb.min(2) >= 254) | (np.abs(rgb - 200).max(2) < 1)
    paper = (lum > 222) & ~blank & (r >= g) & (g >= b - 1) & (r - b >= 4)
    masked = np.where(paper[..., None], rgb, np.nan)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        prof = np.nanmedian(masked, axis=axis)
    count = paper.sum(axis=axis)
    prof[count < 25] = np.nan
    return prof


def _med(x):
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        return np.nanmedian(x, 0)


def steps(prof: np.ndarray, win: int = 12, wide: int = 60, thresh: float = 12.0) -> list[tuple[int, float, list]]:
    """Sharp AND persistent tint steps: the change must be visible between
    12 px windows either side and still hold between 60 px windows."""
    n = len(prof)
    score = np.zeros(n)
    for i in range(win + 2, n - win - 2):
        left, right = prof[i - win - 1:i - 1], prof[i + 1:i + win + 1]
        if np.isnan(left).any(axis=1).mean() > 0.4 or np.isnan(right).any(axis=1).mean() > 0.4:
            continue
        dl, dr = _med(left), _med(right)
        diff = np.abs(dr - dl).sum()
        if diff < thresh:
            continue
        wl, wr = _med(prof[max(0, i - wide):i - 1]), _med(prof[i + 1:i + wide])
        if np.isnan(wl).any() or np.isnan(wr).any():
            continue
        wdiff = np.abs(wr - wl).sum()
        if wdiff >= 0.75 * thresh and np.sign((wr - wl).sum()) == np.sign((dr - dl).sum()):
            score[i] = diff
    out = []
    i = 0
    while i < n:
        if score[i] > 0:
            j = i
            while j < n and score[j] > 0:
                j += 1
            k = i + int(np.argmax(score[i:j]))
            left = _med(prof[max(0, k - win - 1):k - 1])
            right = _med(prof[k + 1:k + win + 1])
            out.append((k, float(score[k]), [left.round().tolist(), right.round().tolist()]))
            i = j + win
        else:
            i += 1
    return out


def detect_joins(img: Image.Image, band: int = 256) -> list[dict]:
    arr = np.asarray(img)
    H, W = arr.shape[:2]
    hits = {'x': [], 'y': []}  # 'x' = vertical join at a given px
    for b0 in range(0, H, band):
        for pos, sc, cols in steps(paper_profile(arr[b0:b0 + band], axis=0)):
            hits['x'].append((pos, b0, sc, cols))
    for b0 in range(0, W, band):
        for pos, sc, cols in steps(paper_profile(arr[:, b0:b0 + band], axis=1)):
            hits['y'].append((pos, b0, sc, cols))
    joins = []
    for axis, hs in hits.items():
        groups = []
        for h in sorted(hs):
            if groups and abs(h[0] - groups[-1][-1][0]) <= 12:
                groups[-1].append(h)
            else:
                groups.append([h])
        for g in groups:
            bands = sorted({h[1] for h in g})
            joins.append({'orientation': 'vertical' if axis == 'x' else 'horizontal',
                          'at': ('px' if axis == 'x' else 'py'),
                          'pos': round(sum(h[0] for h in g) / len(g)),
                          'bands': bands, 'band': band,
                          'step': round(max(h[2] for h in g)),
                          'paper': g[0][3],
                          'likely': len(bands) >= 2 or max(h[2] for h in g) >= 24})
    return sorted(joins, key=lambda j: (not j['likely'], j['orientation'], j['pos']))


def cmd_sheet(a) -> None:
    img, meta = load(a.mosaic)
    joins = detect_joins(img)
    print(f"{meta['name']}: OS sheet joins from paper-tint steps (best effort)")
    shown = 0
    for j in joins:
        if not j['likely'] and not a.all:
            continue
        other = 'y' if j['at'] == 'px' else 'x'
        extent = ', '.join(f"{other} {b}-{b + j['band']}" for b in j['bands'])
        tag = 'LIKELY ' if j['likely'] else 'weak   '
        print(f"  {tag}{j['orientation']:10s} join at {j['at']} ~{j['pos']}  over {extent}  "
              f"(step {j['step']}; paper {j['paper'][0]} -> {j['paper'][1]})")
        shown += 1
    if not shown:
        print('  no sheet join detected' + ('' if a.all else ' (use --all to list weak candidates)'))
    if meta.get('missing_tiles'):
        print(f"  missing tiles (grey fill, not a join): {meta['missing_tiles']}")
    print('  Expect 1-2 px line offsets and a tint change along a join; figures cut by it may be split.')


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='mode', required=True)
    s = sub.add_parser('sweep')
    s.add_argument('mosaic')
    s.add_argument('--crop', type=int, default=448)
    s.add_argument('--min-overlap', type=int, default=64)
    s.add_argument('--scale', type=float, default=2)
    s.add_argument('--grid', type=int, default=64)
    s.add_argument('--out')
    z = sub.add_parser('zoom')
    z.add_argument('mosaic')
    z.add_argument('px', type=int)
    z.add_argument('py', type=int)
    z.add_argument('--scale', type=float, default=6)
    z.add_argument('--half', type=int, default=40)
    z.add_argument('--lines', action='store_true', help='draw grid lines inside the crop as well as ticks')
    z.add_argument('--out')
    sh = sub.add_parser('sheet')
    sh.add_argument('mosaic')
    sh.add_argument('--all', action='store_true', help='also list weak single-band candidates')
    a = ap.parse_args()
    {'sweep': cmd_sweep, 'zoom': cmd_zoom, 'sheet': cmd_sheet}[a.mode](a)


if __name__ == '__main__':
    main()
