"""Georeference the 1805 OS Old Series Sheet 1 scan and cut Web Mercator XYZ tiles.

Inputs
  reference/author-supplied-2026-09-25/os-old-series-sheet1-essex-1805.jpg   (8758 x 6262 scan)
  data/maps/os-old-series-sheet1-1805-gcps.json   control points and the fitted affine (pixel -> EPSG:3857)

Output
  docs/maps/tiles/os-old-series-sheet1-1805/{z}/{x}/{y}.webp  for zooms MINZ..MAXZ, transparent outside the neat line
  docs/maps/tiles/os-old-series-sheet1-1805/metadata.json

Method
  A single affine transform fitted by least squares to parish-church crosses on the sheet against present-day
  church coordinates (OpenStreetMap). RMS about 80 m on the ground, which is close to the sheet's own accuracy.
  Each tile is rendered by inverse-mapping its pixel grid through the affine into scan coordinates and resampling
  with OpenCV (area filter when shrinking, cubic when near native scale). The scan is 6.6 m per pixel, so zoom 14
  (about 6 m per pixel here) is the native limit; higher zooms would only upsample.

Usage:  python3 scripts/georef_sheet1_1805.py [--maxzoom 14] [--minzoom 6]
"""
from __future__ import annotations
import argparse, json, math, time
from pathlib import Path
import numpy as np, cv2
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

ROOT = Path(__file__).resolve().parents[1]
SCAN = ROOT / 'reference/author-supplied-2026-09-25/os-old-series-sheet1-essex-1805.jpg'
GCPS = ROOT / 'data/maps/os-old-series-sheet1-1805-gcps.json'
OUT = ROOT / 'docs/maps/tiles/os-old-series-sheet1-1805'
R = 6378137.0
ORIGIN = math.pi * R


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--minzoom', type=int, default=6)
    ap.add_argument('--maxzoom', type=int, default=14)
    ap.add_argument('--format', choices=['webp', 'png'], default='webp', help='webp (lossy, ~5x smaller) or png')
    ap.add_argument('--quality', type=int, default=82)
    args = ap.parse_args()

    meta = json.loads(GCPS.read_text())
    A = np.array(meta['affine_px_to_3857'], dtype=np.float64)  # 2x3: [X;Y] = A @ [px;py;1]
    Ainv = cv2.invertAffineTransform(A)                          # 2x3: [px;py] = Ainv @ [X;Y;1]
    neat = meta['neat_line']                                     # {left, right, top, bottom_left, bottom_right, seam}

    print('loading scan…', flush=True)
    src = np.array(Image.open(SCAN).convert('RGB'))
    H, W = src.shape[:2]
    # Alpha: inside the neat line; the two engraved plates have different bottom margins.
    alpha = np.zeros((H, W), np.uint8)
    alpha[neat['top']:neat['bottom_left'], neat['left']:neat['seam']] = 255
    alpha[neat['top']:neat['bottom_right'], neat['seam']:neat['right']] = 255
    src = np.dstack([src, alpha])

    # Sheet extent in mercator from the neat-line corners.
    corners = np.array([[neat['left'], neat['top']], [neat['right'], neat['top']],
                        [neat['right'], neat['bottom_right']], [neat['left'], neat['bottom_left']]], np.float64)
    M = (A @ np.c_[corners, np.ones(4)].T).T
    minx, miny, maxx, maxy = M[:, 0].min(), M[:, 1].min(), M[:, 0].max(), M[:, 1].max()
    def lonlat(x, y): return math.degrees(x / R), math.degrees(2 * math.atan(math.exp(y / R)) - math.pi / 2)
    west, south = lonlat(minx, miny); east, north = lonlat(maxx, maxy)
    print(f'extent lon {west:.4f}..{east:.4f} lat {south:.4f}..{north:.4f}', flush=True)

    total = 0; t0 = time.time()
    for z in range(args.minzoom, args.maxzoom + 1):
        n = 2 ** z; tile_m = 2 * ORIGIN / n; px_m = tile_m / 256
        tx0, tx1 = int((minx + ORIGIN) // tile_m), int((maxx + ORIGIN) // tile_m)
        ty0, ty1 = int((ORIGIN - maxy) // tile_m), int((ORIGIN - miny) // tile_m)
        # source pixels per tile pixel decides the filter
        scale = px_m / (math.hypot(A[0, 0], A[1, 0]))
        interp = cv2.INTER_AREA if scale > 1.2 else cv2.INTER_CUBIC
        count = 0
        for tx in range(tx0, tx1 + 1):
            for ty in range(ty0, ty1 + 1):
                X0 = -ORIGIN + tx * tile_m; Y0 = ORIGIN - ty * tile_m
                # pixel-centre grid in mercator
                xs = X0 + (np.arange(256) + 0.5) * px_m
                ys = Y0 - (np.arange(256) + 0.5) * px_m
                GX, GY = np.meshgrid(xs, ys)
                mapx = (Ainv[0, 0] * GX + Ainv[0, 1] * GY + Ainv[0, 2]).astype(np.float32)
                mapy = (Ainv[1, 0] * GX + Ainv[1, 1] * GY + Ainv[1, 2]).astype(np.float32)
                if mapx.max() < 0 or mapy.max() < 0 or mapx.min() > W or mapy.min() > H:
                    continue
                if scale > 1.2:
                    # INTER_AREA is not supported by remap; pre-shrink the needed window then remap linearly.
                    x_lo, x_hi = int(max(0, np.floor(mapx.min()) - 2)), int(min(W, np.ceil(mapx.max()) + 2))
                    y_lo, y_hi = int(max(0, np.floor(mapy.min()) - 2)), int(min(H, np.ceil(mapy.max()) + 2))
                    if x_hi <= x_lo or y_hi <= y_lo: continue
                    win = src[y_lo:y_hi, x_lo:x_hi]
                    f = 1.0 / scale
                    small = cv2.resize(win, (max(1, int(round(win.shape[1] * f))), max(1, int(round(win.shape[0] * f)))), interpolation=cv2.INTER_AREA)
                    fx = small.shape[1] / win.shape[1]; fy = small.shape[0] / win.shape[0]
                    tile = cv2.remap(small, (mapx - x_lo) * fx, (mapy - y_lo) * fy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
                else:
                    tile = cv2.remap(src, mapx, mapy, cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
                if tile[..., 3].max() == 0:
                    continue
                # Straight alpha: zero colour where transparent so edges do not fringe.
                tile[tile[..., 3] < 8] = 0
                p = OUT / str(z) / str(tx) / f'{ty}.{args.format}'
                p.parent.mkdir(parents=True, exist_ok=True)
                if args.format == 'webp':
                    cv2.imwrite(str(p), cv2.cvtColor(tile, cv2.COLOR_RGBA2BGRA), [cv2.IMWRITE_WEBP_QUALITY, args.quality])
                else:
                    cv2.imwrite(str(p), cv2.cvtColor(tile, cv2.COLOR_RGBA2BGRA), [cv2.IMWRITE_PNG_COMPRESSION, 6])
                count += 1
        total += count
        print(f'z{z}: {count} tiles ({time.time() - t0:.0f}s)', flush=True)

    (OUT / 'metadata.json').write_text(json.dumps({
        'name': 'os-old-series-sheet1-1805', 'format': args.format, 'minzoom': args.minzoom, 'maxzoom': args.maxzoom,
        'bounds': [west, south, east, north], 'tiles': total,
        'source': 'Ordnance Survey One-inch Old Series, Sheet 1 (Essex and the Thames), published 18 April 1805 by Lt Col Mudge, Tower of London; author-supplied scan',
        'georeferencing': {'method': 'affine least squares on parish-church crosses vs OpenStreetMap church coordinates',
                           'rms_ground_m': meta.get('rms_ground_m'), 'control_points': len(meta['gcps']), 'gcps_file': str(GCPS.relative_to(ROOT))},
        'attribution': 'OS Old Series Sheet 1, 1805 (out of copyright); georeferenced 2026 for West Ham and the River Lea'
    }, indent=2) + '\n')
    size = sum(f.stat().st_size for f in OUT.rglob(f'*.{args.format}')) / 1e6
    print(f'done: {total} tiles, {size:.1f} MB -> {OUT}')


if __name__ == '__main__':
    main()
