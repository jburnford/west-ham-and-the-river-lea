"""Render arbitrary camera views of the scene to PNG, headlessly.

Uses the site's ?river-review mode, where app.js exposes window.riverNetworkReview
({position, target, fov}) → PNG data URL. Cameras come from a JSON list
[{"label", "position": [x,y,z], "target": [x,y,z], "fov"}] or from the named
destinations in district-navigation.js. Serve docs on 4173 first.

    python3 scripts/render_views.py cameras.json --out reference/photo-review-2026-10-03/views
    python3 scripts/render_views.py --destinations three-mills-west,bromley --out ...
    python3 scripts/render_views.py --all-destinations --out ...

A camera may carry "tide": 0 (low water) to 1 (high water), set through the tide slider.
"""
import asyncio
import base64
import json
import sys
import time
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]


def arg(name, default=None):
    return next((a.split('=', 1)[1] for a in sys.argv if a.startswith(f'--{name}=')), default)


async def main():
    url = arg('url', 'http://127.0.0.1:4173')
    quality = arg('quality', 'full')
    out = Path(arg('out', 'reference/photo-review-2026-10-03/views'))
    out = out if out.is_absolute() else ROOT / out
    out.mkdir(parents=True, exist_ok=True)
    width, height = int(arg('width', 1280)), int(arg('height', 720))
    files = [a for a in sys.argv[1:] if not a.startswith('--')]
    cameras = []
    for f in files:
        cameras += json.loads(Path(f).read_text())
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=[
            '--no-sandbox', '--enable-webgl', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'])
        page = await browser.new_page(viewport={'width': width, 'height': height})
        page.set_default_timeout(900000)
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        await page.goto(f'{url}/?river-review=1&quality={quality}')
        await page.wait_for_function('window.panoramaReview?.ready === true && typeof window.riverNetworkReview === "function"')
        if '--all-destinations' in sys.argv or arg('destinations'):
            views = await page.evaluate("import('./district-navigation.js').then((m) => m.districtViews)")
            wanted = arg('destinations')
            wanted = set(wanted.split(',')) if wanted else None
            for v in views:
                if wanted is None or v['id'] in wanted:
                    cameras.append({'label': v['id'], 'position': v['position'], 'target': v['target'], 'fov': v.get('fov', 62)})
        index = []
        for camera in cameras:
            started = time.time()
            if 'tide' in camera:
                # Optional tide stage, 0 (low water) to 1 (high water), through the page's own slider.
                await page.evaluate('''(t) => {
                    const s = document.querySelector('#tide-level');
                    s.value = String(Math.round(t * 100));
                    s.dispatchEvent(new Event('input'));
                }''', camera['tide'])
            data_url = await page.evaluate('(c) => window.riverNetworkReview(c)', {'position': camera['position'], 'target': camera['target'], 'fov': camera.get('fov', 55)})
            path = out / f"{camera['label']}.png"
            path.write_bytes(base64.b64decode(data_url.split(',', 1)[1]))
            index.append({**camera, 'file': path.name})
            print(f"{camera['label']}: {path.name} ({time.time() - started:.1f}s)")
        (out / 'index.json').write_text(json.dumps(index, indent=1))
        await browser.close()
    print(f'{len(index)} views written to {out}')
    if errors:
        print('Page errors:\n  ' + '\n  '.join(errors))
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
