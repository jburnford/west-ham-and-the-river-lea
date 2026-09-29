"""Load the current scene with deliberately stale module/data cache entries."""
import asyncio
import base64
from functools import partial
from http.server import ThreadingHTTPServer
import json
import os
from threading import Thread
from urllib.parse import urlparse

from playwright.async_api import async_playwright
from review_river_network import ROOT,OUT,QuietHandler

STALE={'/app.js','/terrain-details.js','/river-network.js','/gardens.js','/data/ground-plan.json'}
class CacheFixture(QuietHandler):
    def do_GET(self):
        parsed=urlparse(self.path)
        if parsed.path=='/warm-cache':
            body=b'<!doctype html><title>Cache regression fixture</title>'
        elif parsed.path in STALE and not parsed.query:
            body=(b'{"stale":true}' if parsed.path.endswith('.json')
                  else b'throw new Error("Stale scene module was reused");')
        else:
            return super().do_GET()
        self.send_response(200)
        self.send_header('Content-Type','application/json' if parsed.path.endswith('.json') else 'text/html' if parsed.path=='/warm-cache' else 'text/javascript')
        self.send_header('Cache-Control','public, max-age=31536000, immutable')
        self.send_header('Content-Length',str(len(body)))
        self.end_headers();self.wfile.write(body)

async def review(url):
    errors=[];requests=[];OUT.mkdir(parents=True,exist_ok=True)
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True,env=dict(os.environ,
            GALLIUM_DRIVER='d3d12',MESA_D3D12_DEFAULT_ADAPTER_NAME='NVIDIA'),args=[
            '--no-sandbox','--enable-webgl','--use-angle=gl','--ignore-gpu-blocklist',
            '--enable-unsafe-swiftshader','--disable-dev-shm-usage'])
        page=await browser.new_page(viewport={'width':1440,'height':1000},reduced_motion='reduce')
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
        await page.goto(url+'/warm-cache')
        # Normal fetches store long-lived stale entries; no request interception
        # is used, because Playwright routing would disable the browser cache.
        await page.evaluate('(paths)=>Promise.all(paths.map(p=>fetch(p).then(r=>r.text())))',list(STALE))
        page.on('request',lambda r:requests.append(r.url))
        await page.goto(url+'/?view=marsh-ditches&river-review&quality=full&scene=cache-test')
        await page.wait_for_function('Boolean(window.riverNetworkReview)',timeout=180000)
        report=await page.evaluate('panoramaReview')
        assert report['gardens']['plots']==153
        assert report['revision']==json.loads((ROOT/'docs/scene-manifest.json').read_text())['revision']
        stale_requests=[u for u in requests if urlparse(u).path in STALE and not urlparse(u).query]
        assert not stale_requests,stale_requests
        for path in STALE:
            assert any(urlparse(u).path==path and 'v=' in urlparse(u).query for u in requests),path
        image=await page.evaluate('(view)=>riverNetworkReview(view)',
            {'position':[-110,220,445],'target':[-305,0,205],'fov':60})
        (OUT/'gardens-cache-regression.png').write_bytes(base64.b64decode(image.split(',')[1]))
        assert not errors,errors
        (OUT/'preview-cache-checks.json').write_text(json.dumps({
            'revision':report['revision'],'plots':report['gardens']['plots'],
            'staleCacheEntries':sorted(STALE),'staleRequests':stale_requests,'errors':errors},indent=2)+'\n')
        await browser.close()
        print(f'Cache regression passed: five stale entries bypassed; scene {report["revision"]}, 153 plots, no browser errors.',flush=True)

if __name__=='__main__':
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(CacheFixture,directory=str(ROOT/'docs')))
    Thread(target=server.serve_forever,daemon=True).start()
    try:asyncio.run(review(f'http://127.0.0.1:{server.server_port}'))
    finally:server.shutdown()
