"""Download NLS georeferenced map tiles for the West Ham study area.

Reads a layer registry (data/maps/nls-layers.json), fetches every XYZ tile
inside the study bounding box for each layer's zoom range, records a manifest
and writes a georeferenced quick-look mosaic per layer.

Tiles are CC-BY National Library of Scotland material; credit line
"Reproduced with the permission of the National Library of Scotland" with a
link to https://maps.nls.uk/ is required wherever they are shown.

Usage:
  python3 scripts/fetch_nls_tiles.py                 # all layers in the registry
  python3 scripts/fetch_nls_tiles.py --layer essex   # one layer id
  python3 scripts/fetch_nls_tiles.py --dry-run       # counts only

Output: reference/nls-tiles/<layer-id>/{z}/{x}/{y}.png plus manifest.json and
quicklooks/. The reference/ directory is excluded from the public repository.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / 'data/maps/nls-layers.json'
OUT = ROOT / 'reference/nls-tiles'
USER_AGENT = 'west-ham-river-lea-research/1.0 (+https://github.com/jburnford/west-ham-and-the-river-lea; jic823@usask.ca)'
WORKERS = 6
RETRIES = 3


def lon_to_x(lon: float, z: int) -> float:
    return (lon + 180.0) / 360.0 * 2 ** z


def lat_to_y(lat: float, z: int) -> float:
    r = math.radians(lat)
    return (1.0 - math.log(math.tan(r) + 1.0 / math.cos(r)) / math.pi) / 2.0 * 2 ** z


def tile_range(bbox, z):
    west, south, east, north = bbox
    x0, x1 = int(math.floor(lon_to_x(west, z))), int(math.floor(lon_to_x(east, z)))
    y0, y1 = int(math.floor(lat_to_y(north, z))), int(math.floor(lat_to_y(south, z)))
    n = 2 ** z
    return max(0, x0), min(n - 1, x1), max(0, y0), min(n - 1, y1)


def clip_bbox(a, b):
    if not b:
        return a
    return (max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3]))


def fetch(url: str) -> tuple[int, bytes | None]:
    request = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    for attempt in range(RETRIES):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.status, response.read()
        except urllib.error.HTTPError as error:
            if error.code == 404 or error.code == 403:
                return error.code, None
            time.sleep(1.5 * (attempt + 1))
        except (urllib.error.URLError, TimeoutError, OSError):
            time.sleep(1.5 * (attempt + 1))
    return 0, None


def download_layer(layer: dict, study_bbox, dry_run: bool) -> dict:
    layer_id = layer['id']
    base = layer['url'].rstrip('/')
    bbox = clip_bbox(study_bbox, layer.get('bounds'))
    zooms = range(layer['minzoom'], layer['maxzoom'] + 1)
    jobs = []
    for z in zooms:
        x0, x1, y0, y1 = tile_range(bbox, z)
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                jobs.append((z, x, y))
    summary = {'id': layer_id, 'url_template': f'{base}/{{z}}/{{x}}/{{y}}.png', 'bbox': list(bbox),
               'zooms': [zooms.start, zooms.stop - 1], 'tiles_requested': len(jobs), 'tiles_ok': 0,
               'tiles_missing': 0, 'tiles_failed': 0, 'tiles_skipped_existing': 0, 'bytes': 0,
               'per_zoom': {}, 'started': time.strftime('%Y-%m-%dT%H:%M:%S')}
    for z in zooms:
        x0, x1, y0, y1 = tile_range(bbox, z)
        summary['per_zoom'][str(z)] = {'x': [x0, x1], 'y': [y0, y1], 'count': (x1 - x0 + 1) * (y1 - y0 + 1)}
    print(f"[{layer_id}] {len(jobs)} tiles, z{zooms.start}-{zooms.stop - 1}, bbox {[round(v, 4) for v in bbox]}", flush=True)
    if dry_run:
        return summary

    out_dir = OUT / layer_id
    lock = threading.Lock()
    digest = hashlib.sha256()

    def work(job):
        z, x, y = job
        path = out_dir / str(z) / str(x) / f'{y}.png'
        if path.exists() and path.stat().st_size > 0:
            return 'existing', path.stat().st_size
        status, data = fetch(f'{base}/{z}/{x}/{y}.png')
        if status == 200 and data:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            return 'ok', len(data)
        if status in (403, 404):
            return 'missing', 0
        return 'failed', 0

    done = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = [pool.submit(work, job) for job in jobs]
        for future in as_completed(futures):
            kind, size = future.result()
            with lock:
                done += 1
                if kind == 'ok':
                    summary['tiles_ok'] += 1; summary['bytes'] += size
                elif kind == 'existing':
                    summary['tiles_skipped_existing'] += 1; summary['bytes'] += size
                elif kind == 'missing':
                    summary['tiles_missing'] += 1
                else:
                    summary['tiles_failed'] += 1
                if done % 1000 == 0 or done == len(jobs):
                    print(f"[{layer_id}] {done}/{len(jobs)} ok={summary['tiles_ok']} existing={summary['tiles_skipped_existing']} "
                          f"missing={summary['tiles_missing']} failed={summary['tiles_failed']} {summary['bytes'] / 1e6:.1f} MB", flush=True)
    summary['finished'] = time.strftime('%Y-%m-%dT%H:%M:%S')
    return summary


def quicklook(layer: dict, study_bbox, zoom: int) -> dict | None:
    """Stitch downloaded tiles at one zoom into a PNG with an EPSG:3857 world file."""
    try:
        from PIL import Image
    except ImportError:
        return None
    layer_id = layer['id']
    bbox = clip_bbox(study_bbox, layer.get('bounds'))
    zoom = min(zoom, layer['maxzoom'])
    x0, x1, y0, y1 = tile_range(bbox, zoom)
    width, height = (x1 - x0 + 1) * 256, (y1 - y0 + 1) * 256
    canvas = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    found = 0
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            path = OUT / layer_id / str(zoom) / str(x) / f'{y}.png'
            if not path.exists():
                continue
            try:
                canvas.paste(Image.open(path).convert('RGBA'), ((x - x0) * 256, (y - y0) * 256))
                found += 1
            except OSError:
                continue
    if not found:
        return None
    ql_dir = OUT / 'quicklooks'
    ql_dir.mkdir(parents=True, exist_ok=True)
    png = ql_dir / f'{layer_id}-z{zoom}.png'
    canvas.convert('RGB').save(png, optimize=True)
    # World file: Web Mercator metres per pixel at this zoom, origin at the mosaic's top-left.
    origin_shift = 20037508.342789244
    metres_per_tile = 2 * origin_shift / 2 ** zoom
    pixel = metres_per_tile / 256
    left = -origin_shift + x0 * metres_per_tile
    top = origin_shift - y0 * metres_per_tile
    (ql_dir / f'{layer_id}-z{zoom}.pgw').write_text(f'{pixel:.6f}\n0.0\n0.0\n{-pixel:.6f}\n{left + pixel / 2:.3f}\n{top - pixel / 2:.3f}\n')
    (ql_dir / f'{layer_id}-z{zoom}.png.aux.xml').write_text(
        '<PAMDataset><SRS>EPSG:3857</SRS></PAMDataset>\n')
    return {'file': str(png.relative_to(ROOT)), 'zoom': zoom, 'tiles': found, 'size_px': [width, height]}


def main():
    global WORKERS
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--layer', action='append', help='layer id from the registry (repeatable)')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--quicklook-zoom', type=int, default=15)
    parser.add_argument('--workers', type=int, default=WORKERS, help='parallel requests (default %d)' % WORKERS)
    args = parser.parse_args()
    WORKERS = args.workers

    registry = json.loads(REGISTRY.read_text())
    study_bbox = tuple(registry['study_bbox'])
    layers = [l for l in registry['layers'] if not args.layer or l['id'] in args.layer]
    if not layers:
        sys.exit('No matching layers in registry')
    OUT.mkdir(parents=True, exist_ok=True)
    manifest_path = OUT / 'manifest.json'
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {'layers': {}}
    manifest['study_bbox'] = list(study_bbox)
    manifest['source'] = registry.get('source')
    manifest['licence'] = registry.get('licence')
    manifest['attribution'] = registry.get('attribution')
    for layer in layers:
        summary = download_layer(layer, study_bbox, args.dry_run)
        summary.update({k: layer.get(k) for k in ('title', 'series', 'dates', 'scale', 'nls_layer_name', 'notes')})
        if not args.dry_run:
            summary['quicklook'] = quicklook(layer, study_bbox, args.quicklook_zoom)
            manifest['layers'][layer['id']] = summary
            manifest['updated'] = time.strftime('%Y-%m-%dT%H:%M:%S')
            manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
        else:
            print(json.dumps({k: summary[k] for k in ('id', 'tiles_requested', 'zooms')}))
    if not args.dry_run:
        total = sum(l['tiles_ok'] + l['tiles_skipped_existing'] for l in manifest['layers'].values())
        size = sum(l['bytes'] for l in manifest['layers'].values()) / 1e6
        print(f'Done: {total} tiles, {size:.1f} MB across {len(manifest["layers"])} layers -> {OUT}')


if __name__ == '__main__':
    main()
