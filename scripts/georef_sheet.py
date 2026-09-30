"""Georeference a scanned map sheet from a control-point file and cut Web Mercator XYZ tiles.

Generalisation of georef_sheet1_1805.py. The control-point JSON (data/maps/<name>-gcps.json) carries:
  scan            path to the scan, relative to the repository root
  neat_line       {left, right, top, bottom} pixel bounds of the map face (optional; whole image if absent)
  gcps            [{name, px:[x,y], lonlat:[lon,lat]}]  (the affine is refitted from these on every run)
  tiles           {out, minzoom, maxzoom, format, quality}   out relative to the repository root

Fit: least-squares affine, scan pixel -> EPSG:3857. Residuals (ground metres) and leave-one-out error are
printed and written back into the JSON so the record stays honest. Tiles are inverse-mapped through the
affine with OpenCV (area pre-shrink when reducing, cubic near native scale) and written as WebP or PNG with
transparency outside the neat line.

Usage:  python3 scripts/georef_sheet.py data/maps/chapman-andre-1777-gcps.json [--fit-only]
"""
from __future__ import annotations
import argparse, json, math, time
from pathlib import Path
import numpy as np, cv2
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

ROOT = Path(__file__).resolve().parents[1]
R = 6378137.0
ORIGIN = math.pi * R


def merc(lon, lat):
    return R * math.radians(lon), R * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


def lonlat(x, y):
    return math.degrees(x / R), math.degrees(2 * math.atan(math.exp(y / R)) - math.pi / 2)


def fit(gcps):
    P = np.array([g['px'] for g in gcps], float)
    M = np.array([merc(*g['lonlat']) for g in gcps])
    X = np.c_[P, np.ones(len(P))]
    A, *_ = np.linalg.lstsq(X, M, rcond=None)
    lat_mid = np.mean([g['lonlat'][1] for g in gcps]); k = math.cos(math.radians(lat_mid))
    res = (M - X @ A) * k
    d = np.hypot(res[:, 0], res[:, 1])
    loo = []
    for i in range(len(gcps)):
        keep = [j for j in range(len(gcps)) if j != i]
        Ai, *_ = np.linalg.lstsq(X[keep], M[keep], rcond=None)
        loo.append(float(np.hypot(*((M[i] - X[i] @ Ai) * k))))
    report = {'rms_ground_m': float(math.sqrt((d ** 2).mean())), 'max_residual_ground_m': float(d.max()),
              'leave_one_out_rms_m': float(math.sqrt(np.mean(np.square(loo)))),
              'ground_scale_m_per_px': float(math.hypot(A[0, 0], A[1, 0]) * k),
              'rotation_deg': float(math.degrees(math.atan2(A[1, 0], A[0, 0])))}
    for g, dd, rr, l in zip(gcps, d, res, loo):
        g['residual_m'] = round(float(dd), 1); g['residual_dx_dy_m'] = [round(float(rr[0]), 1), round(float(rr[1]), 1)]; g['loo_m'] = round(l, 1)
    return A.T, report  # 2x3


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('config')
    ap.add_argument('--fit-only', action='store_true')
    args = ap.parse_args()
    cfg_path = ROOT / args.config
    cfg = json.loads(cfg_path.read_text())

    A, report = fit(cfg['gcps'])
    cfg['affine_px_to_3857'] = A.tolist(); cfg['fit'] = report
    print(f"fit: rms {report['rms_ground_m']:.0f} m, max {report['max_residual_ground_m']:.0f} m, LOO {report['leave_one_out_rms_m']:.0f} m, "
          f"{report['ground_scale_m_per_px']:.2f} m/px, rotation {report['rotation_deg']:+.2f} deg")
    for g in cfg['gcps']:
        print(f"   {g['name']:34s} {g['residual_m']:6.0f} m  (dx {g['residual_dx_dy_m'][0]:+6.0f}, dy {g['residual_dx_dy_m'][1]:+6.0f})  loo {g['loo_m']:6.0f}")
    cfg_path.write_text(json.dumps(cfg, indent=1, ensure_ascii=False) + '\n')
    if args.fit_only:
        return

    A = np.array(cfg['affine_px_to_3857'], float); Ainv = cv2.invertAffineTransform(A)
    t = cfg['tiles']; out = ROOT / t['out']; fmt = t.get('format', 'webp'); q = int(t.get('quality', 82))
    src = np.array(Image.open(ROOT / cfg['scan']).convert('RGB')); H, W = src.shape[:2]
    nl = cfg.get('neat_line') or {'left': 0, 'top': 0, 'right': W, 'bottom': H}
    alpha = np.zeros((H, W), np.uint8); alpha[nl['top']:nl['bottom'], nl['left']:nl['right']] = 255
    src = np.dstack([src, alpha])
    corners = np.array([[nl['left'], nl['top']], [nl['right'], nl['top']], [nl['right'], nl['bottom']], [nl['left'], nl['bottom']]], float)
    M = (A @ np.c_[corners, np.ones(4)].T).T
    minx, miny, maxx, maxy = M[:, 0].min(), M[:, 1].min(), M[:, 0].max(), M[:, 1].max()
    west, south = lonlat(minx, miny); east, north = lonlat(maxx, maxy)
    print(f'extent lon {west:.4f}..{east:.4f} lat {south:.4f}..{north:.4f}')

    total = 0; t0 = time.time(); px_scale = math.hypot(A[0, 0], A[1, 0])
    for z in range(t['minzoom'], t['maxzoom'] + 1):
        n = 2 ** z; tile_m = 2 * ORIGIN / n; px_m = tile_m / 256; scale = px_m / px_scale
        tx0, tx1 = int((minx + ORIGIN) // tile_m), int((maxx + ORIGIN) // tile_m)
        ty0, ty1 = int((ORIGIN - maxy) // tile_m), int((ORIGIN - miny) // tile_m)
        count = 0
        for tx in range(tx0, tx1 + 1):
            for ty in range(ty0, ty1 + 1):
                X0 = -ORIGIN + tx * tile_m; Y0 = ORIGIN - ty * tile_m
                GX, GY = np.meshgrid(X0 + (np.arange(256) + 0.5) * px_m, Y0 - (np.arange(256) + 0.5) * px_m)
                mapx = (Ainv[0, 0] * GX + Ainv[0, 1] * GY + Ainv[0, 2]).astype(np.float32)
                mapy = (Ainv[1, 0] * GX + Ainv[1, 1] * GY + Ainv[1, 2]).astype(np.float32)
                if mapx.max() < nl['left'] or mapy.max() < nl['top'] or mapx.min() > nl['right'] or mapy.min() > nl['bottom']:
                    continue
                if scale > 1.2:
                    x_lo, x_hi = int(max(0, np.floor(mapx.min()) - 2)), int(min(W, np.ceil(mapx.max()) + 2))
                    y_lo, y_hi = int(max(0, np.floor(mapy.min()) - 2)), int(min(H, np.ceil(mapy.max()) + 2))
                    if x_hi <= x_lo or y_hi <= y_lo: continue
                    win = src[y_lo:y_hi, x_lo:x_hi]; f = 1.0 / scale
                    small = cv2.resize(win, (max(1, int(round(win.shape[1] * f))), max(1, int(round(win.shape[0] * f)))), interpolation=cv2.INTER_AREA)
                    fx = small.shape[1] / win.shape[1]; fy = small.shape[0] / win.shape[0]
                    tile = cv2.remap(small, (mapx - x_lo) * fx, (mapy - y_lo) * fy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
                else:
                    tile = cv2.remap(src, mapx, mapy, cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
                if tile[..., 3].max() == 0: continue
                tile[tile[..., 3] < 8] = 0
                p = out / str(z) / str(tx) / f'{ty}.{fmt}'; p.parent.mkdir(parents=True, exist_ok=True)
                if fmt == 'webp': cv2.imwrite(str(p), cv2.cvtColor(tile, cv2.COLOR_RGBA2BGRA), [cv2.IMWRITE_WEBP_QUALITY, q])
                else: cv2.imwrite(str(p), cv2.cvtColor(tile, cv2.COLOR_RGBA2BGRA), [cv2.IMWRITE_PNG_COMPRESSION, 6])
                count += 1
        total += count; print(f'z{z}: {count} tiles ({time.time() - t0:.0f}s)', flush=True)
    size = sum(f.stat().st_size for f in out.rglob(f'*.{fmt}')) / 1e6
    (out / 'metadata.json').write_text(json.dumps({'name': out.name, 'format': fmt, 'minzoom': t['minzoom'], 'maxzoom': t['maxzoom'],
        'bounds': [west, south, east, north], 'tiles': total, 'megabytes': round(size, 1), 'source': cfg.get('sheet'), 'attribution': cfg.get('attribution'),
        'georeferencing': {'method': 'affine least squares on control points', **report, 'control_points': len(cfg['gcps']), 'gcps_file': args.config}}, indent=2) + '\n')
    print(f'done: {total} tiles, {size:.1f} MB -> {out}')


if __name__ == '__main__':
    main()
