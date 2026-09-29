"""Local-only desktop views of the expanded river banks; serves only docs/."""
import asyncio
import base64
from functools import partial
from http.server import ThreadingHTTPServer
import json
import os
from threading import Thread

from playwright.async_api import async_playwright
from render_social_film import ROOT, QuietHandler

OUT = ROOT/'scenes/channelsea-sewer-panorama/review'
REPORT_NAME = 'river-network-checks.json'
SOFTWARE_GL = False
VIEWS = {
    'river-network-overview': {'position': [-560, 1000, 620], 'target': [-490, 0, -100], 'fov': 65},
    'three-mills-wall-south': {'position': [-639, 8, -163], 'target': [-592, 1, 50], 'fov': 55},
    'three-mills-wall-bank': {'position': [-607, 6, -35], 'target': [-568, 1, 165], 'fov': 58},
    'three-mills-junction': {'position': [-710, 100, 520], 'target': [-570, 0, 310], 'fov': 60},
    'river-core-regression': {'position': [0, 9.2, 0], 'target': [-20, 0, 180], 'fov': 56},
    'marsh-housing-coverage': {'position': [-470, 350, 20], 'target': [-450, 0, -320], 'fov': 62},
    'city-mills-existing-coverage': {'position': [-800, 250, -40], 'target': [-709, 0, -350], 'fov': 60},
}


async def review(url):
    OUT.mkdir(parents=True, exist_ok=True)
    errors = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, env=dict(os.environ,
            GALLIUM_DRIVER='d3d12', MESA_D3D12_DEFAULT_ADAPTER_NAME='NVIDIA'), args=[
            '--no-sandbox', '--enable-webgl', '--use-angle=swiftshader' if SOFTWARE_GL else '--use-angle=gl', '--ignore-gpu-blocklist',
            '--enable-unsafe-swiftshader', '--disable-dev-shm-usage'])
        page = await browser.new_page(viewport={'width': 1600, 'height': 1000}, device_scale_factor=1)
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
        await page.goto(url+'/?river-review&quality=full')
        await page.wait_for_function('Boolean(window.riverNetworkReview)', timeout=180000)
        for name, view in VIEWS.items():
            data = await page.evaluate('(view) => riverNetworkReview(view)', view)
            (OUT/f'{name}.png').write_bytes(base64.b64decode(data.split(',')[1]))
            print(f'Captured {name}', flush=True)
        report = {'views': VIEWS, 'errors': errors,
                  'graphicsBackend': 'swiftshader' if SOFTWARE_GL else 'gl',
                  'render': await page.evaluate('window.panoramaReview')}
        (OUT/REPORT_NAME).write_text(json.dumps(report, indent=2)+'\n')
        await browser.close()
        assert not errors, errors
        print(f'All {len(VIEWS)} views rendered without browser or shader errors.', flush=True)


if __name__ == '__main__':
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(ROOT/'docs')))
    Thread(target=server.serve_forever, daemon=True).start()
    try:
        asyncio.run(review(f'http://127.0.0.1:{server.server_port}'))
    finally:
        server.shutdown()
