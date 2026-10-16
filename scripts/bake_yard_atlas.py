"""Paint the factory-yard surface atlas once, in headless Chromium, and save it as WebP for the page to load.

The page used to paint this 4096 px canvas (tens of thousands of gradient patches, then a per-pixel grain pass)
on every visit, which was most of its load time. The painting code is still docs/factory-yards.js
(paintYardAtlas), so the baked image and the page's fallback cannot drift apart.

Run after build_factory_yards.py and before build_scene_manifest.py:
    python3 scripts/bake_yard_atlas.py [--quality Q]
Writes docs/data/factory-yards-atlas-{4096,2048}.webp and factory-yards-atlas.json (the source hashes that
check_yard_atlas.mjs compares, so a stale atlas fails npm test).
"""
import argparse
import base64
import functools
import hashlib
import http.server
import json
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
SIZES = (4096, 2048)


def source_hashes():
    return {
        name: hashlib.sha256((DOCS / name).read_bytes()).hexdigest()[:16]
        for name in ('data/factory-yards.json', 'factory-yards.js', 'lib/prng.js')
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--quality', type=float, default=0.9, help='WebP quality 0-1; 1 is near-lossless, not lossless')
    args = parser.parse_args()
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(DOCS))
    handler.log_message = lambda *a: None
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    port = server.server_address[1]
    out = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
        page = browser.new_page()
        page.set_default_timeout(900_000)
        page.goto(f'http://127.0.0.1:{port}/data/factory-yards-atlas.json')  # any same-origin page
        for size in SIZES:
            encoded = page.evaluate(
                """async ([size, quality]) => {
                  const { paintYardAtlas } = await import('/factory-yards.js');
                  const yards = await (await fetch('/data/factory-yards.json', { cache: 'no-store' })).json();
                  const canvas = document.createElement('canvas');
                  canvas.width = canvas.height = size;
                  paintYardAtlas(canvas, yards);
                  const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/webp', quality));
                  if (blob.type !== 'image/webp') throw new Error('This browser cannot encode WebP: ' + blob.type);
                  const bytes = new Uint8Array(await blob.arrayBuffer());
                  let text = '';
                  for (let i = 0; i < bytes.length; i += 0x8000) text += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
                  return btoa(text);
                }""",
                [size, args.quality],
            )
            data = base64.b64decode(encoded)
            (DOCS / f'data/factory-yards-atlas-{size}.webp').write_bytes(data)
            out[str(size)] = {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()[:16]}
            print(f'factory-yards-atlas-{size}.webp: {len(data) / 1e6:.2f} MB')
        browser.close()
    server.shutdown()
    meta = {'sources': source_hashes(), 'quality': args.quality, 'images': out}
    (DOCS / 'data/factory-yards-atlas.json').write_text(json.dumps(meta, indent=1) + '\n')


if __name__ == '__main__':
    main()
