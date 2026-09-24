"""Browser checks and review screenshots. Start the site on 127.0.0.1:4173 first."""
import asyncio
import json
import sys
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'scenes/channelsea-sewer-panorama/review'


async def check():
    REVIEW.mkdir(exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, timeout=15000, args=[
            '--no-sandbox', '--enable-webgl', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'])
        page = await browser.new_page(viewport={'width': 1440, 'height': 1000})
        errors, remote, console_errors = [], [], []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('console', lambda m: console_errors.append(m.text) if m.type == 'error' else None)
        page.on('request', lambda r: remote.append(r.url) if not r.url.startswith('http://127.0.0.1:4173/') else None)
        await page.goto('http://127.0.0.1:4173/')
        await page.wait_for_function('window.panoramaReview?.ready === true')
        initial = await page.evaluate('window.panoramaReview')
        assert initial['camera'][1] == 9
        assert initial['movement']['along'] == 0 and initial['movement']['across'] == 5.5
        assert initial['drawCalls'] < 30
        assert initial['reflection']['drawCalls'] < 30
        await page.screenshot(path=REVIEW / 'south-desktop.png', full_page=True)
        await page.locator('#panorama canvas').screenshot(path=REVIEW / 'south-scene.png')
        print('South view captured; checking other views and movement.', flush=True)
        for stop, yaw in [('homes', 320), ('north', 25), ('mill',346), ('pumping', 274), ('gas', 201)]:
            await page.click(f'[data-stop="{stop}"]')
            state = await page.evaluate('window.panoramaReview')
            assert state['yaw'] == yaw and state['camera'] == initial['camera']
            assert await page.locator(f'[data-stop="{stop}"]').get_attribute('aria-pressed') == 'true'
            await page.screenshot(path=REVIEW / f'{stop}-desktop.png', full_page=True)
        if '--visual-only' in sys.argv:
            # Focused rerender after surface-only refinements; retain the full
            # interaction report from the preceding successful browser check.
            await page.click('[data-side="north"]')
            await page.click('[data-stop="north"]')
            await page.screenshot(path=REVIEW / 'north-side-desktop.png', full_page=True)
            await page.locator('#panorama canvas').screenshot(path=REVIEW / 'north-scene.png')
            await page.set_viewport_size({'width': 390, 'height': 844})
            await page.click('#reset')
            await page.screenshot(path=REVIEW / 'south-mobile.png', full_page=True)
            await page.click('[data-side="north"]')
            await page.click('[data-stop="north"]')
            await page.screenshot(path=REVIEW / 'north-mobile.png', full_page=True)
            assert await page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            assert not errors and not console_errors and not remote, (errors, console_errors, remote)
            report = {'checks': ['six desktop views', 'both bridge sides', 'mobile north/south views',
                                 'no horizontal overflow', 'no page or shader errors', 'no external requests'],
                      'initial_render': initial, 'limits': 'Focused visual check after the full interaction suite; software rendering only.'}
            (REVIEW / 'visual-checks.json').write_text(json.dumps(report, indent=2) + '\n')
            print(json.dumps(report, indent=2))
            await browser.close()
            return
        await page.click('#map-open')
        assert await page.locator('#map-dialog').evaluate('(d) => d.open')
        await page.screenshot(path=REVIEW / 'location-map.png')
        await page.keyboard.press('Escape')
        assert not await page.locator('#map-dialog').evaluate('(d) => d.open')
        assert await page.locator('#map-open').evaluate('(b) => b === document.activeElement')
        await page.locator('#panorama').focus()
        await page.keyboard.press('ArrowRight')
        assert (await page.evaluate('window.panoramaReview.yaw')) == 206
        await page.keyboard.press('Home')
        assert (await page.evaluate('window.panoramaReview.yaw')) == 184
        await page.click('#zoom-in')
        assert (await page.evaluate('window.panoramaReview.fov')) < 56
        await page.click('#reset')
        bounds = await page.locator('#panorama').bounding_box()
        x,y = bounds['x']+bounds['width']/2,bounds['y']+bounds['height']/2
        await page.mouse.move(x,y); await page.mouse.down()
        await page.mouse.move(x+120,y+30,steps=5); await page.mouse.up()
        assert (await page.evaluate('window.panoramaReview.yaw')) != 184
        assert (await page.evaluate('window.panoramaReview.camera')) == initial['camera']
        # Moving changes position, preserves eye height and updates the location-map cone.
        await page.click('#reset')
        await page.locator('#panorama').focus()
        await page.keyboard.down('w')
        await page.wait_for_timeout(350)
        await page.keyboard.up('w')
        moved=await page.evaluate('window.panoramaReview')
        assert moved['camera'] != initial['camera'] and moved['camera'][1] == 9
        assert moved['yaw'] == initial['yaw']
        await page.click('[data-side="north"]')
        north=await page.evaluate('window.panoramaReview')
        assert north['movement']['across'] == -5.5
        assert north['movement']['along'] == moved['movement']['along']
        await page.click('[data-stop="north"]')
        assert (await page.evaluate('window.panoramaReview.camera')) == north['camera']
        assert abs(float(await page.locator('#camera-marker').get_attribute('cx'))-north['camera'][0]) < 1e-8
        assert abs(float(await page.locator('#camera-marker').get_attribute('cy'))-north['camera'][2]) < 1e-8
        await page.screenshot(path=REVIEW / 'north-side-desktop.png',full_page=True)
        await page.locator('#panorama canvas').screenshot(path=REVIEW / 'north-scene.png')
        # Holding movement into a limit must not leave the allowed rectangle.
        await page.locator('#panorama').focus()
        await page.keyboard.down('w')
        await page.wait_for_timeout(250)
        await page.click('#map-open')  # Opening a dialog also releases a held key.
        stopped=await page.evaluate('window.panoramaReview.camera')
        await page.wait_for_timeout(150)
        assert await page.evaluate('window.panoramaReview.camera') == stopped
        await page.keyboard.up('w');await page.keyboard.press('Escape')
        p=await page.evaluate('window.panoramaReview.movement')
        assert abs(p['along'])<=24 and abs(p['across'])<=5.5
        await page.locator('#panorama').focus();await page.keyboard.press('Home')
        assert (await page.evaluate('window.panoramaReview.camera')) == initial['camera']
        await page.click('#evidence-open')
        assert await page.locator('#evidence-dialog').evaluate('(d) => d.open')
        await page.keyboard.press('Escape')
        await page.set_viewport_size({'width': 390, 'height': 844})
        await page.click('#reset')
        await page.screenshot(path=REVIEW / 'south-mobile.png',full_page=True)
        assert await page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        await page.click('[data-side="north"]')
        assert (await page.evaluate('window.panoramaReview.movement.across')) == -5.5
        await page.locator('[data-walk="right"]').focus()
        await page.keyboard.press('Enter')
        assert (await page.evaluate('window.panoramaReview.movement.along')) != 0
        await page.screenshot(path=REVIEW / 'bridge-controls-mobile.png',full_page=True)
        await page.click('#reset')
        await page.click('[data-stop="pumping"]')
        assert (await page.evaluate('window.panoramaReview.yaw')) == 274
        assert await page.locator('#story').is_visible()
        await page.click('[data-stop="homes"]')
        assert (await page.evaluate('window.panoramaReview.yaw')) == 320
        await page.locator('#story summary').click()
        assert '1865' in await page.locator('#story').inner_text()
        assert 'six West Ham' in await page.locator('#story').inner_text()
        await page.click('[data-stop="north"]')
        assert (await page.evaluate('window.panoramaReview.yaw')) == 25
        assert 'Streets beyond the railway' in await page.locator('#story').inner_text()
        await page.screenshot(path=REVIEW / 'north-mobile.png',full_page=True)
        await page.click('#map-open')
        assert await page.locator('#map-dialog').is_visible()
        await page.keyboard.press('Escape')
        # Simulate missing WebGL: stories and vector map must remain usable.
        fallback = await browser.new_page()
        await fallback.add_init_script("""const original = HTMLCanvasElement.prototype.getContext;
            HTMLCanvasElement.prototype.getContext = function(type, ...args) {
                return type.startsWith('webgl') ? null : original.call(this, type, ...args);
            };""")
        await fallback.goto('http://127.0.0.1:4173/')
        await fallback.wait_for_selector('#plan svg', state='attached')
        assert 'could not open' in await fallback.locator('#loading').inner_text()
        assert await fallback.locator('[data-side="north"]').is_disabled()
        assert await fallback.locator('[data-walk="forward"]').is_disabled()
        await fallback.click('[data-stop="gas"]')
        assert 'Fuel for a growing city' in await fallback.locator('#story').inner_text()
        await fallback.click('#map-open')
        assert await fallback.locator('#map-dialog').is_visible()
        assert not errors, errors
        assert not console_errors, console_errors
        assert not remote, remote
        report = {'desktop': '1440 × 1000', 'mobile': '390 × 844',
                  'checks': ['WebGL render', 'bounded bridge movement and fixed eye height', 'six story stops preserve position', 'keyboard turns/reset',
                             'cross-side controls', 'movement stops on dialog opening', 'live camera map marker', 'mobile movement controls',
                             'pointer drag', 'zoom', 'map dialog and focus return', 'evidence dialog',
                             'mobile overflow', 'WebGL fallback', 'no external requests', 'no page or shader errors',
                             'bounded draw calls in main and reflection passes'],
                  'initial_render': initial,
                  'limits': 'Software-rendered Chromium smoke checks; not a physical-phone performance audit.'}
        (REVIEW/'browser-checks.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report,indent=2))
        await browser.close()


if __name__ == '__main__':
    asyncio.run(check())
