"""Stitch OS London five-foot (1893) XYZ tiles into overlapping mosaics for
reading spot heights, bench marks and water levels.

Each mosaic is SIZE x SIZE tiles (default 4 x 4 = 1024 px) and neighbouring
mosaics overlap by one tile (step = SIZE - 1), so an annotation that falls on a
mosaic edge is whole in at least one neighbour.

For every mosaic three files are written to reference/spot-heights/mosaics/:

  m18_<x0>_<y0>.png        the plain stitched mosaic
  m18_<x0>_<y0>.grid.png   the same with a light 128 px grid and pixel labels,
                           to help a vision model report positions
  m18_<x0>_<y0>.json       sidecar: tile origin, missing tiles, corner
                           coordinates in EPSG:3857 / 4326 / 27700

Pixel convention: (px, py) are continuous mosaic pixel coordinates measured
from the top-left corner of the mosaic; the centre of pixel column i is i+0.5.
Global Web-Mercator pixel = tile_origin * 256 + (px, py) at the mosaic zoom.
Use pixel_to_coords() (importable) for exact conversion.

Usage:
  python3 scripts/spot_height_mosaics.py --x 131063 131072 --y 87134 87149

Full-extent run (lattice anchored on the prototype mosaics, existing files left
untouched when identical, mostly-missing mosaics recorded but not written):
  python3 scripts/spot_height_mosaics.py --x 131045 131122 --y 87099 87195 \
      --align 131063 87134 --max-missing-frac 0.5 --keep-existing \
      --index lattice_index.json --workers 8

25-inch gap fill (--layer / --prefix): build q18_* mosaics from the NLS
25-inch 'london' layer only at the five-foot lattice positions whose five-foot
mosaic is skipped or more than 25% missing, into mosaics-25inch/:
  python3 scripts/spot_height_mosaics.py --layer os-25-inch-london --prefix q18 \
      --positions-from reference/spot-heights/mosaics/lattice_index.json \
      --where-missing-gt 0.25 --max-missing-frac 0.5 \
      --out reference/spot-heights/mosaics-25inch --index lattice_index.json --workers 8

1848-51 skeleton survey, whole extent, same lattice, into mosaics-1848/:
  python3 scripts/spot_height_mosaics.py --layer os-london-skeleton-5280 --prefix s18 \
      --x 131045 131122 --y 87099 87195 --align 131063 87134 --max-missing-frac 0.5 \
      --out reference/spot-heights/mosaics-1848 --index lattice_index.json --workers 8

Mosaic names carry their source: m18_* = five-foot (mosaics/), q18_* =
25-inch (mosaics-25inch/), s18_* = 1848-51 skeleton (mosaics-1848/).
mosaic_dir(name) resolves a name to its folder.
"""
from __future__ import annotations

import argparse
import contextlib
import json
import math
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from pyproj import Transformer

ROOT = Path(__file__).resolve().parents[1]
NLS_TILES = ROOT / 'reference/nls-tiles'
DEFAULT_LAYER = 'os-london-five-foot-1893'
TILES = NLS_TILES / DEFAULT_LAYER
OUT = ROOT / 'reference/spot-heights/mosaics'
OUT_25INCH = ROOT / 'reference/spot-heights/mosaics-25inch'
OUT_1848 = ROOT / 'reference/spot-heights/mosaics-1848'
# Per tile layer: human-readable source, map scale, survey dates, height datum
# and survey epoch. The merge only clusters readings of the same epoch (the
# 1890s five-foot and 25-inch sheets share one levelling; the 1848-51 skeleton
# survey is a separate observation even at the same spot). The five-foot
# 'source' is exactly the string the original sidecars carry; 'geojson_source'
# is the string heights.geojson has always used for five-foot marks.
LAYERS = {
    'os-london-five-foot-1893': {
        'source': 'NLS OS London five-foot (1:1056) 1893-96 XYZ tiles',
        'geojson_source': 'OS 1:1056 London 1891-96 via NLS',
        'scale': '1:1056',
        'survey_dates': '1891-95 (published 1893-96)',
        'datum': 'OD Liverpool',
        'epoch': '1890s',
        'decimals': {'spot': 1, 'bench_mark': 2},
    },
    'os-25-inch-london': {
        'source': "NLS OS 25-inch (1:2500) 'london' layer XYZ tiles; over West Ham the Essex county "
                  'series, 1893-96 revision (edition per sheet not verified)',
        'scale': '1:2500',
        'survey_dates': 'c.1893-96 revision (inferred, see mosaics-25inch/lattice_index.json edition_notes)',
        'datum': 'OD Liverpool',
        'epoch': '1890s',
        # spot heights are whole feet (italic, beside a small + or dot); B.M.s 1 dp
        'decimals': {'spot': 0, 'bench_mark': 1},
    },
    'os-london-skeleton-5280': {
        'source': 'OS London 1:5,280 skeleton survey 1848-51 (Metropolitan Commission of Sewers levelling), '
                  'NLS XYZ tiles',
        'scale': '1:5280',
        'survey_dates': '1848-51',
        'datum': 'OD Liverpool (inferred: no datum note on the tiles; B.M.s agree with the 1890s '
                 'OD Liverpool values to a few tenths of a foot; see mosaics-1848/lattice_index.json datum_notes)',
        'epoch': '1848-51',
        'decimals': {'spot': 1, 'bench_mark': 1},
    },
}
# First letter of a mosaic name -> folder and layer
# (m18_* five-foot, q18_* 25-inch, s18_* 1848-51 skeleton).
PREFIX_DIRS = {'m': OUT, 'q': OUT_25INCH, 's': OUT_1848}
PREFIX_LAYERS = {'m': 'os-london-five-foot-1893', 'q': 'os-25-inch-london', 's': 'os-london-skeleton-5280'}
TILE = 256
R = 6378137.0  # Web Mercator sphere radius
GRID = 128

TO_BNG = Transformer.from_crs('EPSG:4326', 'EPSG:27700', always_xy=True)
FROM_BNG = Transformer.from_crs('EPSG:27700', 'EPSG:4326', always_xy=True)


def mosaic_dir(name: str) -> Path:
    """Folder holding mosaic <name> (png, grid.png and sidecar json)."""
    name = Path(name).name
    try:
        return PREFIX_DIRS[name[0]]
    except (KeyError, IndexError):
        raise ValueError(f'mosaic name {name!r} has no known prefix (m18_*, q18_*, s18_*)') from None


def layer_of(name: str) -> str:
    return PREFIX_LAYERS.get(Path(name).name[:1], DEFAULT_LAYER)


def layer_info(layer: str) -> dict:
    if layer in LAYERS:
        return LAYERS[layer]
    reg = ROOT / 'data/maps/nls-layers.json'
    try:
        doc = json.loads(reg.read_text())
        for entry in doc['layers'] if isinstance(doc, dict) else doc:
            if entry.get('id') == layer:
                return {'source': f"NLS {entry.get('title', layer)} XYZ tiles", 'scale': entry.get('scale', ''),
                        'survey_dates': entry.get('dates', ''), 'datum': 'unverified', 'epoch': layer}
    except (OSError, ValueError, KeyError):
        pass
    return {'source': f'NLS {layer} XYZ tiles', 'scale': '', 'survey_dates': '', 'datum': 'unverified',
            'epoch': layer}


def meta_info(meta: dict) -> dict:
    """Layer, source, scale, survey dates, datum and epoch for a sidecar; old
    five-foot sidecars lack some keys, which then come from LAYERS."""
    layer = meta.get('layer') or layer_of(meta.get('name', 'm'))
    info = layer_info(layer)
    out = {'layer': layer}
    for k in ('source', 'scale', 'survey_dates', 'datum', 'epoch'):
        out[k] = meta.get(k) or info.get(k, '')
    out['geojson_source'] = info.get('geojson_source') or out['source']
    return out


# ---------------------------------------------------------------- coordinates

def global_pixel_to_lonlat(gx: float, gy: float, z: int) -> tuple[float, float]:
    """Global pixel (tile*256 + offset) at zoom z -> WGS84 lon, lat."""
    n = TILE * 2 ** z
    lon = gx / n * 360.0 - 180.0
    lat = math.degrees(math.atan(math.sinh(math.pi * (1.0 - 2.0 * gy / n))))
    return lon, lat


def global_pixel_to_3857(gx: float, gy: float, z: int) -> tuple[float, float]:
    n = TILE * 2 ** z
    x = gx / n * 2 * math.pi * R - math.pi * R
    y = math.pi * R - gy / n * 2 * math.pi * R
    return x, y


def lonlat_to_global_pixel(lon: float, lat: float, z: int) -> tuple[float, float]:
    n = TILE * 2 ** z
    gx = (lon + 180.0) / 360.0 * n
    r = math.radians(lat)
    gy = (1.0 - math.log(math.tan(r) + 1.0 / math.cos(r)) / math.pi) / 2.0 * n
    return gx, gy


def pixel_to_coords(meta: dict, px: float, py: float) -> dict:
    """Mosaic pixel -> dict of EPSG:3857, WGS84 and EPSG:27700 coordinates."""
    z = meta['zoom']
    gx = meta['tile_x0'] * TILE + px
    gy = meta['tile_y0'] * TILE + py
    lon, lat = global_pixel_to_lonlat(gx, gy, z)
    mx, my = global_pixel_to_3857(gx, gy, z)
    e, nn = TO_BNG.transform(lon, lat)
    return {'lon': lon, 'lat': lat, 'x3857': mx, 'y3857': my, 'bng_e': e, 'bng_n': nn}


def bng_to_pixel(meta: dict, e: float, n: float) -> tuple[float, float]:
    lon, lat = FROM_BNG.transform(e, n)
    gx, gy = lonlat_to_global_pixel(lon, lat, meta['zoom'])
    return gx - meta['tile_x0'] * TILE, gy - meta['tile_y0'] * TILE


# -------------------------------------------------------------------- mosaics

def load_tile(z: int, x: int, y: int, tiles: Path = TILES) -> Image.Image | None:
    path = tiles / str(z) / str(x) / f'{y}.png'
    if not path.exists():
        return None
    try:
        rgba = Image.open(path).convert('RGBA')
    except OSError:
        return None
    bg = Image.new('RGBA', rgba.size, (255, 255, 255, 255))
    return Image.alpha_composite(bg, rgba).convert('RGB')


def origins(lo: int, hi: int, size: int, step: int) -> list[int]:
    """Mosaic origins covering [lo, hi] with the last one aligned to hi."""
    if hi - lo + 1 <= size:
        return [lo]
    out = list(range(lo, hi - size + 2, step))
    if out[-1] + size - 1 < hi:
        out.append(hi - size + 1)
    return out


def aligned_origins(lo: int, hi: int, size: int, step: int, anchor: int) -> list[int]:
    """Origins on the lattice anchor + k*step whose mosaics cover [lo, hi].

    Unlike origins(), the last mosaic is not shifted to end at hi, so every
    mosaic stays on one lattice (edge mosaics simply have missing tiles)."""
    first = anchor + math.floor((lo - anchor) / step) * step
    out = [first]
    while out[-1] + size - 1 < hi:
        out.append(out[-1] + step)
    return out


def build_mosaic(z: int, x0: int, y0: int, size: int, tiles: Path = TILES):
    img = Image.new('RGB', (size * TILE, size * TILE), (200, 200, 200))
    missing = []
    for dx in range(size):
        for dy in range(size):
            tile = load_tile(z, x0 + dx, y0 + dy, tiles)
            if tile is None:
                missing.append([x0 + dx, y0 + dy])
                continue
            img.paste(tile, (dx * TILE, dy * TILE))
    return img, missing


def font(size: int):
    for name in ('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',
                 '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_grid(img: Image.Image) -> Image.Image:
    """Light 128 px grid; labels in a margin-free style at each intersection."""
    base = img.convert('RGBA')
    layer = Image.new('RGBA', base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    w, h = base.size
    f = font(11)
    for v in range(0, w + 1, GRID):
        d.line([(v, 0), (v, h)], fill=(255, 0, 160, 70), width=1)
    for v in range(0, h + 1, GRID):
        d.line([(0, v), (w, v)], fill=(255, 0, 160, 70), width=1)
    for gx in range(0, w, GRID):
        for gy in range(0, h, GRID):
            label = f'{gx},{gy}'
            tw = d.textlength(label, font=f)
            d.rectangle([gx + 1, gy + 1, gx + 3 + tw, gy + 13], fill=(255, 255, 255, 150))
            d.text((gx + 2, gy + 1), label, fill=(200, 0, 120, 230), font=f)
    return Image.alpha_composite(base, layer).convert('RGB')


def sidecar(z: int, x0: int, y0: int, size: int, missing: list, name: str,
            layer: str = DEFAULT_LAYER) -> dict:
    info = layer_info(layer)
    meta = {
        'name': name,
        'layer': layer,
        'source': info['source'],
    }
    if layer != DEFAULT_LAYER:  # five-foot sidecars stay byte-identical to the originals
        for k in ('scale', 'survey_dates', 'datum'):
            meta[k] = info.get(k, '')
    meta.update({
        'zoom': z,
        'tile_x0': x0,
        'tile_y0': y0,
        'tiles_w': size,
        'tiles_h': size,
        'tile_size': TILE,
        'width_px': size * TILE,
        'height_px': size * TILE,
        'grid_px': GRID,
        'missing_tiles': missing,
        'pixel_convention': 'px,py measured from mosaic top-left corner; global pixel = tile_origin*256 + px',
        'formula': 'lon = gx/(256*2^z)*360-180; lat = atan(sinh(pi*(1-2*gy/(256*2^z))))',
    })
    corners = {}
    for key, (px, py) in {'top_left': (0, 0), 'top_right': (size * TILE, 0),
                          'bottom_left': (0, size * TILE), 'bottom_right': (size * TILE, size * TILE),
                          'centre': (size * TILE / 2, size * TILE / 2)}.items():
        c = pixel_to_coords(meta, px, py)
        corners[key] = {k: round(v, 7 if k in ('lon', 'lat') else 2) for k, v in c.items()}
    meta['corners'] = corners
    tl, br = corners['top_left'], corners['bottom_right']
    meta['ground_m_per_px'] = round((br['bng_e'] - tl['bng_e']) / (size * TILE), 4)
    return meta


def blank_fraction(z: int, x0: int, y0: int, size: int, tiles: Path = TILES) -> float:
    """Fraction of mosaic area that is missing or fully transparent in the tiles
    (NLS tiles are transparent outside the edge of a sheet)."""
    blank = 0
    for dx in range(size):
        for dy in range(size):
            path = tiles / str(z) / str(x0 + dx) / f'{y0 + dy}.png'
            if not path.exists():
                blank += TILE * TILE
                continue
            try:
                alpha = Image.open(path).convert('RGBA').getchannel('A')
            except OSError:
                blank += TILE * TILE
                continue
            blank += alpha.histogram()[0]
    return blank / (size * size * TILE * TILE)


def _same_image(path: Path, img: Image.Image) -> bool:
    try:
        old = Image.open(path).convert('RGB')
    except OSError:
        return False
    if old.size != img.size:
        return False
    from PIL import ImageChops
    return ImageChops.difference(old, img).getbbox() is None


def process_one(job: dict) -> dict:
    """Build, check and (maybe) write one mosaic; returns an index entry."""
    z, x0, y0, size, out = job['zoom'], job['x0'], job['y0'], job['size'], Path(job['out'])
    layer = job.get('layer', DEFAULT_LAYER)
    tiles = NLS_TILES / layer
    name = f"{job.get('prefix') or f'm{z}'}_{x0}_{y0}"
    img, missing = build_mosaic(z, x0, y0, size, tiles)
    meta = sidecar(z, x0, y0, size, missing, name, layer)
    c = meta['corners']['centre']
    entry = {'name': name, 'tile_x0': x0, 'tile_y0': y0, 'missing': len(missing),
             'missing_tiles': missing, 'centre_bng': [c['bng_e'], c['bng_n']],
             'centre_lonlat': [c['lon'], c['lat']]}
    if len(missing) == size ** 2:
        entry.update(status='skipped_no_tiles', written=False, blank_frac=1.0)
        return entry
    entry['blank_frac'] = round(blank_fraction(z, x0, y0, size, tiles), 4)
    if len(missing) > job['max_missing_frac'] * size ** 2:
        entry.update(status='skipped_missing', written=False)
        return entry
    png = out / f'{name}.png'
    if job['keep_existing'] and png.exists():
        same = _same_image(png, img)
        entry.update(status='existing_identical' if same else 'existing_differs', written=False)
        return entry
    img.save(png, optimize=True)
    if job['grid']:
        draw_grid(img).save(out / f'{name}.grid.png', optimize=True)
    (out / f'{name}.json').write_text(json.dumps(meta, indent=2))
    entry.update(status='written', written=True)
    return entry


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--x', nargs=2, type=int, default=[131063, 131072], metavar=('X0', 'X1'))
    ap.add_argument('--y', nargs=2, type=int, default=[87134, 87149], metavar=('Y0', 'Y1'))
    ap.add_argument('--zoom', type=int, default=18)
    ap.add_argument('--size', type=int, default=4, help='tiles per mosaic side')
    ap.add_argument('--overlap', type=int, default=1, help='tiles shared with each neighbour')
    ap.add_argument('--out', type=Path, default=OUT)
    ap.add_argument('--align', nargs=2, type=int, metavar=('AX', 'AY'),
                    help='keep origins on the lattice AX+k*step, AY+k*step (edge mosaics not shifted)')
    ap.add_argument('--max-missing-frac', type=float, default=None,
                    help='record but do not write mosaics with more than this fraction of tiles missing')
    ap.add_argument('--keep-existing', action='store_true',
                    help='never overwrite an existing mosaic PNG; report whether its content is identical')
    ap.add_argument('--no-grid', action='store_true', help='do not write the .grid.png overview')
    ap.add_argument('--index', default='index.json', help='index file name inside --out')
    ap.add_argument('--workers', type=int, default=1)
    ap.add_argument('--layer', default=DEFAULT_LAYER,
                    help=f'tile layer under reference/nls-tiles/ (default {DEFAULT_LAYER})')
    ap.add_argument('--prefix', default=None,
                    help='mosaic name prefix (default m<zoom>, i.e. m18; use q18 for os-25-inch-london)')
    ap.add_argument('--positions-from', type=Path, metavar='INDEX',
                    help='take lattice origins from another lattice_index.json instead of --x/--y')
    ap.add_argument('--where-missing-gt', type=float, default=None, metavar='FRAC',
                    help='with --positions-from: only positions skipped there or with more than FRAC '
                         'of their tiles missing')
    args = ap.parse_args()
    if args.layer != DEFAULT_LAYER and not args.prefix:
        ap.error('--layer other than the five-foot needs an explicit --prefix (e.g. q18)')
    if args.prefix and args.prefix[0] not in PREFIX_DIRS:
        ap.error(f'--prefix must start with one of {sorted(PREFIX_DIRS)} so the tools can find the folder')
    if not (NLS_TILES / args.layer / str(args.zoom)).is_dir():
        ap.error(f'no tiles at {NLS_TILES / args.layer / str(args.zoom)}')

    step = args.size - args.overlap
    args.out.mkdir(parents=True, exist_ok=True)
    legacy = args.align is None and args.max_missing_frac is None and not args.keep_existing \
        and args.workers == 1 and not args.no_grid and args.layer == DEFAULT_LAYER \
        and args.prefix in (None, f'm{args.zoom}') and args.positions_from is None
    positions = None
    if args.positions_from:
        src = json.loads(args.positions_from.read_text())
        if src.get('size', args.size) != args.size or src.get('zoom', args.zoom) != args.zoom:
            ap.error('--positions-from index has a different size or zoom')
        step = src.get('step', step)
        thr = args.where_missing_gt
        positions = []
        for e in src['mosaics']:
            bad = e['status'].startswith('skipped') or thr is None or e['missing'] > thr * args.size ** 2
            if bad:
                positions.append((e['tile_x0'], e['tile_y0'], e['name'], e['status'], e['missing']))
        args.align = src.get('align')
        xs = sorted({p[0] for p in positions})
        ys = sorted({p[1] for p in positions})
    elif args.align:
        xs = aligned_origins(args.x[0], args.x[1], args.size, step, args.align[0])
        ys = aligned_origins(args.y[0], args.y[1], args.size, step, args.align[1])
    else:
        xs = origins(args.x[0], args.x[1], args.size, step)
        ys = origins(args.y[0], args.y[1], args.size, step)

    if legacy:  # original behaviour, unchanged
        index = []
        for x0 in xs:
            for y0 in ys:
                img, missing = build_mosaic(args.zoom, x0, y0, args.size)
                if len(missing) == args.size ** 2:
                    print(f'skip {x0},{y0}: no tiles')
                    continue
                name = f'm{args.zoom}_{x0}_{y0}'
                img.save(args.out / f'{name}.png', optimize=True)
                draw_grid(img).save(args.out / f'{name}.grid.png', optimize=True)
                meta = sidecar(args.zoom, x0, y0, args.size, missing, name)
                (args.out / f'{name}.json').write_text(json.dumps(meta, indent=2))
                c = meta['corners']['centre']
                index.append({'name': name, 'tile_x0': x0, 'tile_y0': y0, 'missing': len(missing),
                              'centre_bng': [c['bng_e'], c['bng_n']]})
                print(f'{name}: missing {len(missing):2d} tiles, centre BNG {c["bng_e"]:.0f} {c["bng_n"]:.0f}')
        (args.out / args.index).write_text(json.dumps(index, indent=2))
        print(f'{len(index)} mosaics -> {args.out}')
        return

    frac = 1.0 if args.max_missing_frac is None else args.max_missing_frac
    common = {'zoom': args.zoom, 'size': args.size, 'out': str(args.out), 'max_missing_frac': frac,
              'keep_existing': args.keep_existing, 'grid': not args.no_grid}
    if args.layer != DEFAULT_LAYER or args.prefix:
        common.update(layer=args.layer, prefix=args.prefix)
    if positions is None:
        jobs = [{**common, 'x0': x0, 'y0': y0} for x0 in xs for y0 in ys]
        print(f'{len(xs)} x {len(ys)} = {len(jobs)} lattice positions '
              f'(x {xs[0]}..{xs[-1]}, y {ys[0]}..{ys[-1]}, step {step})', flush=True)
    else:
        jobs = [{**common, 'x0': p[0], 'y0': p[1]} for p in positions]
        print(f'{len(jobs)} positions from {args.positions_from} (skipped there or more than '
              f'{args.where_missing_gt} of tiles missing), step {step}', flush=True)
    index = []
    with ProcessPoolExecutor(max_workers=max(1, args.workers)) as ex:
        for k, entry in enumerate(ex.map(process_one, jobs, chunksize=4), 1):
            index.append(entry)
            if k % 50 == 0 or entry['status'] not in ('written', 'skipped_no_tiles', 'skipped_missing'):
                print(f"[{k}/{len(jobs)}] {entry['name']}: {entry['status']}, missing {entry['missing']}",
                      flush=True)
    counts = {}
    for e in index:
        counts[e['status']] = counts.get(e['status'], 0) + 1
    doc = {'zoom': args.zoom, 'size': args.size, 'overlap': args.overlap,
           'step': step, 'align': args.align, 'max_missing_frac': frac,
           'counts': counts, 'mosaics': index}
    if args.layer != DEFAULT_LAYER or args.prefix or positions is not None:
        info = layer_info(args.layer)
        extra = {'layer': args.layer, 'prefix': args.prefix or f'm{args.zoom}',
                 'source': info['source'], 'scale': info['scale'],
                 'survey_dates': info.get('survey_dates', ''), 'datum': info.get('datum', '')}
        if positions is not None:
            by = {(p[0], p[1]): p for p in positions}
            for e in index:
                p = by[(e['tile_x0'], e['tile_y0'])]
                e['replaces'] = {'name': p[2], 'status': p[3], 'missing': p[4]}
            extra['positions_from'] = str(args.positions_from.resolve().relative_to(ROOT)) \
                if args.positions_from.resolve().is_relative_to(ROOT) else str(args.positions_from)
            extra['where_missing_gt'] = args.where_missing_gt
        old = args.out / args.index
        if old.exists():  # keep hand-written notes across rebuilds
            with contextlib.suppress(ValueError):
                prev = json.loads(old.read_text())
                for k in ('edition_notes', 'datum_notes', 'reading_notes'):
                    if k in prev:
                        extra[k] = prev[k]
        doc = {**extra, **doc}
    tmp = args.out / (args.index + '.tmp')
    tmp.write_text(json.dumps(doc, indent=1))
    os.replace(tmp, args.out / args.index)
    print(f'{counts} -> {args.out / args.index}')


if __name__ == '__main__':
    main()
