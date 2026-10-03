"""Render regional atlas bounds against legacy edge repetition in one scene."""
import asyncio
import base64
import json
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'scenes/channelsea-sewer-panorama/review'

async def review(url='http://127.0.0.1:4175'):
    OUT.mkdir(parents=True, exist_ok=True)
    errors = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox', '--enable-webgl', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--disable-dev-shm-usage'])
        page = await browser.new_page(viewport={'width':1100, 'height':760}, device_scale_factor=1)
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
        async def app(route):
            source = (ROOT/'docs/app.js').read_text()
            source = source.replace('height, .15, 5000', 'height, .15, 18000')
            source = source.replace('surfaces.reflect(view); renderer.render(scene, view);', 'scene.fog.density=.00006; surfaces.reflect(view); renderer.render(scene, view);')
            await route.fulfill(body=source, content_type='text/javascript')
        async def realism(route):
            source = (ROOT/'docs/realism.js').read_text()
            # Review-only uniform reproduces the old unbounded sampling without
            # removing either texture or changing any geometry/material colours.
            source = source.replace('shader.uniforms.contactMap =', "(window.atlasReviewShaders ||= []).push(shader); shader.uniforms.reviewBounded={value:1}; shader.uniforms.contactMap =")
            source = source.replace('float atlasCoverage', 'uniform float reviewBounded; float atlasCoverage')
            source = source.replace('return inside.x*inside.y;', 'return mix(1.0,inside.x*inside.y,reviewBounded);')
            await route.fulfill(body=source, content_type='text/javascript')
        await page.route('**/app.js*', app)
        await page.route('**/realism.js*', realism)
        await page.goto(url+'/?river-review&quality=lite')
        await page.wait_for_function('Boolean(window.riverNetworkReview)', timeout=300000)
        print('Atlas review scene ready', flush=True)
        views = {
            'region': {'position':[1500,2400,3200], 'target':[-1250,0,-600], 'fov':78},
            'north': {'position':[-650,880,-1390], 'target':[-1275,0,-3080], 'fov':65},
            'core': {'position':[-290,110,480], 'target':[-285,0,260], 'fov':58},
        }
        for name, view in views.items():
            for mode, bounded in [('legacy',0), ('bounded',1)]:
                await page.evaluate('(v)=>atlasReviewShaders.forEach(s=>s.uniforms.reviewBounded.value=v)', bounded)
                capture = await page.evaluate('(v)=>riverNetworkReview(v)', view)
                (OUT/f'atlas-{name}-{mode}.png').write_bytes(base64.b64decode(capture.split(',')[1]))
                print(f'Captured {name}: {mode}', flush=True)
        state = await page.evaluate('panoramaReview')
        prior = json.loads((OUT/'river-system-browser-checks.json').read_text())
        assert state['sewerCrossing'] == prior['sewer'], 'Sewer enclosure changed'
        assert not errors, errors
        await browser.close()
    comparison = check_captures()
    (OUT/'regional-material-checks.json').write_text(json.dumps({'status':'PASS', 'views':views, **comparison, 'sewerUnchanged':True, 'errors':errors}, indent=2)+'\n')
    print('Regional material browser checks passed', flush=True)

def check_captures():
    from PIL import Image, ImageChops
    regional = ImageChops.difference(Image.open(OUT/'atlas-region-legacy.png').convert('RGB'), Image.open(OUT/'atlas-region-bounded.png').convert('RGB'))
    assert regional.getbbox(), 'Comparison did not exercise the atlas boundary correction'
    # The upper half sees beyond the district; compare the local foreground.
    local_before = Image.open(OUT/'atlas-core-legacy.png').convert('RGB')
    local_after = Image.open(OUT/'atlas-core-bounded.png').convert('RGB')
    crop = (0, local_before.height//2, local_before.width, local_before.height)
    core = ImageChops.difference(local_before.crop(crop), local_after.crop(crop))
    assert core.getbbox() is None, 'Local appearance changed inside atlas bounds'
    return {'regionalDifferenceBounds':regional.getbbox(), 'coreForegroundPixelsUnchanged':True}

if __name__ == '__main__':
    asyncio.run(review())
