"""Desktop renders for the terrain/texture study; no phone or UI development."""
import argparse
import asyncio
import json
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'scenes/channelsea-sewer-panorama/review'
parser = argparse.ArgumentParser()
parser.add_argument('--prefix', choices=['terrain', 'lighting'], default='terrain')
PREFIX = parser.parse_args().prefix


async def review():
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True, timeout=15000, args=[
            '--no-sandbox','--enable-webgl','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
        page=await browser.new_page(viewport={'width':1920,'height':1200})
        page.set_default_timeout(90000)
        errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
        await page.goto('http://127.0.0.1:4173/')
        await page.wait_for_function('window.panoramaReview?.ready === true',timeout=90000)
        # Hide overlays only in these review exports so the terrain is unobstructed.
        await page.add_style_tag(content='.view-top,.view-bottom { visibility:hidden !important; }')
        canvas=page.locator('#panorama canvas')
        await canvas.screenshot(path=REVIEW/f'{PREFIX}-south.png')
        print('South terrain captured.',flush=True)
        await page.locator('#panorama').focus()
        await page.keyboard.press('ArrowDown')
        await canvas.screenshot(path=REVIEW/f'{PREFIX}-mud-close.png')
        print('Mud and channels captured.',flush=True)
        # Turn toward the river-right embankment and low allotments.
        bounds=await page.locator('#panorama').bounding_box()
        cx,cy=bounds['x']+bounds['width']/2,bounds['y']+bounds['height']/2
        await page.mouse.move(cx,cy);await page.mouse.down()
        await page.mouse.move(cx-214,cy);await page.mouse.up()
        await canvas.screenshot(path=REVIEW/f'{PREFIX}-mill-mead.png')
        print('Embankment and allotments captured.',flush=True)
        await page.keyboard.press('Home')
        await page.mouse.move(cx,cy);await page.mouse.down()
        await page.mouse.move(cx-414,cy+67);await page.mouse.up()
        await canvas.screenshot(path=REVIEW/f'{PREFIX}-southwest.png')
        print('Southwest distance captured.',flush=True)
        if PREFIX=='lighting':
            await page.locator('#panorama').focus()
            for _ in range(5):await page.keyboard.press('+')
            await canvas.screenshot(path=REVIEW/'lighting-three-mills.png')
        await page.keyboard.press('Home')
        await page.click('[data-side="north"]')
        await page.click('[data-stop="mill"]')
        await canvas.screenshot(path=REVIEW/f'{PREFIX}-abbey-mill.png')
        await page.locator('#panorama').focus()
        await page.mouse.move(cx,cy);await page.mouse.down()
        await page.mouse.move(cx,cy-100);await page.mouse.up()
        await canvas.screenshot(path=REVIEW/f'{PREFIX}-north-river.png')
        print('Northern river captured.',flush=True)
        await page.click('[data-stop="north"]')
        await canvas.screenshot(path=REVIEW/f'{PREFIX}-north-context.png')
        if PREFIX=='lighting':
            # East-facing roads/railway, matching the author's missing-network view.
            await page.mouse.move(cx,cy);await page.mouse.down()
            await page.mouse.move(cx-464,cy-30);await page.mouse.up()
            await canvas.screenshot(path=REVIEW/'lighting-roads-railway.png')
            print('Roads and raised railway captured.',flush=True)
        assert not errors,errors
        report={'checks':['south landscape','mud and channel relief','Mill Mead bank and allotments',
                          'southwest distant landscape','northern river mud and depth','Abbey Mill interpretation without windmill',
                          'north context preserved','no page or shader errors'],
                'render':await page.evaluate('window.panoramaReview'),
                'scope':'Desktop landscape study only; no phone or website-development checks.'}
        if PREFIX=='lighting':report['checks']+=['east-facing roads and raised railway','Three Mills distant landmark','overcast lighting from both bridge sides','open ground grass/weeds with separate sediment and working yards']
        (REVIEW/f'{PREFIX}-checks.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report,indent=2),flush=True)
        await browser.close()


if __name__=='__main__': asyncio.run(review())
