"""Exercise district navigation through the actual controls on the running local site."""
import asyncio
import json
import os
from pathlib import Path
from playwright.async_api import async_playwright

OUT = Path(__file__).resolve().parents[1] / 'scenes/channelsea-sewer-panorama/review'

async def main():
    OUT.mkdir(parents=True, exist_ok=True)
    errors = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, env=dict(os.environ,
            GALLIUM_DRIVER='d3d12', MESA_D3D12_DEFAULT_ADAPTER_NAME='NVIDIA'), args=[
            '--no-sandbox', '--enable-webgl', '--use-angle=gl', '--ignore-gpu-blocklist',
            '--enable-unsafe-swiftshader', '--disable-dev-shm-usage'])
        page = await browser.new_page(viewport={'width': 1440, 'height': 1000}, reduced_motion='reduce')
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
        await page.goto('http://127.0.0.1:4175/?quality=full')
        await page.wait_for_function('window.panoramaReview?.ready', timeout=180000)
        await page.wait_for_function('!window.panoramaReview.tweening')
        start = await page.evaluate('panoramaReview.camera')
        assert await page.locator('#destination option').count() == 1 + await page.evaluate('panoramaReview.destinationCount')
        await page.locator('#destination').select_option('sewer-high-street')
        assert await page.evaluate('panoramaReview.camera') == [-615,45,-320]
        await page.locator('#destination').select_option('wall-vista')
        assert await page.evaluate('panoramaReview.camera[1]') == 6
        assert await page.evaluate('panoramaReview.highStreetFrontages.ranges') == 33
        await page.locator('#destination').select_option('bow-bridge')
        assert await page.evaluate('panoramaReview.movement.mode') == 'district'
        await page.locator('#destination').select_option('city')
        await page.wait_for_function('panoramaReview.movement.mode === "district"')
        city = await page.evaluate('panoramaReview.camera')
        assert city == [-800, 150, -95], city
        await page.keyboard.down('w')
        await page.wait_for_function('(start) => Math.hypot(...panoramaReview.camera.map((v,i) => v-start[i])) > 5', arg=city, timeout=20000)
        await page.keyboard.up('w')
        moved = await page.evaluate('panoramaReview.camera')
        assert sum((a-b)**2 for a,b in zip(city,moved))**.5 > 5, moved
        await page.keyboard.down('e')
        await page.wait_for_function('(height) => panoramaReview.camera[1] > height + 3', arg=moved[1], timeout=20000)
        await page.keyboard.up('e')
        assert (await page.evaluate('panoramaReview.camera'))[1] > moved[1] + 3
        for destination in ['sugar', 'three-mills', 'bromley', 'factory-260']:
            await page.locator('#destination').select_option(destination)
            assert await page.evaluate('panoramaReview.movement.mode') == 'district'
            await page.screenshot(path=str(OUT/f'navigation-{destination}.png'))
        await page.locator('#minimap').click()
        await page.locator('#plan svg').click(position={'x': 150, 'y': 230})
        assert not await page.locator('#map-dialog').is_visible()
        assert await page.evaluate('panoramaReview.movement.mode') == 'district'
        await page.keyboard.press('Home')
        assert await page.evaluate('panoramaReview.movement.mode') == 'bridge'
        assert await page.evaluate('panoramaReview.camera') == start
        await page.goto('http://127.0.0.1:4175/?quality=full&view=wall-vista')
        await page.wait_for_function('window.panoramaReview?.ready && panoramaReview.movement.mode === "district"', timeout=180000)
        assert await page.evaluate('panoramaReview.camera') == [-625,6,-262]
        assert await page.evaluate('panoramaReview.fov') == 48
        assert await page.locator('#destination').input_value() == 'wall-vista'
        # Restore the ordinary entry state before testing bridge reset below.
        await page.goto('http://127.0.0.1:4175/?quality=full')
        await page.wait_for_function('window.panoramaReview?.ready && !panoramaReview.tweening', timeout=180000)
        # Narrow touch layout, same loaded scene; real touch pad controls.
        await page.set_viewport_size({'width': 390, 'height': 844})
        await page.screenshot(path=str(OUT/'navigation-mobile-arrival.png'))
        await page.locator('#destination').select_option('three-mills')
        before = await page.evaluate('panoramaReview.camera')
        button = page.locator('[data-walk="forward"]')
        box = await button.bounding_box()
        await page.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2)
        await page.mouse.down()
        await page.wait_for_timeout(600)
        await page.mouse.up()
        assert await page.evaluate('panoramaReview.camera') != before
        assert await page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        await page.screenshot(path=str(OUT/'navigation-mobile.png'))
        await page.locator('#travel-toggle').click()
        assert await page.evaluate('panoramaReview.movement.mode') == 'bridge'
        assert await page.evaluate('panoramaReview.camera') == start
        (OUT/'navigation-checks.json').write_text(json.dumps({'errors': errors, 'destinations': await page.locator('#destination option').count() - 1, 'checks': ['keyboard travel', 'height', 'area and factory jumps', 'map jump', 'Home reset', 'narrow screen pad', 'return to bridge']}, indent=2))
        await browser.close()
        assert not errors, errors
        print('Navigation browser checks passed: desktop and narrow layout, keyboard, pad, map, destinations and reset.', flush=True)

asyncio.run(main())
