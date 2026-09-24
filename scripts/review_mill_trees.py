"""Focused desktop views of the corrected mill crossing and map-positioned trees."""
import asyncio,json
from pathlib import Path
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT/'scenes/channelsea-sewer-panorama/review'
async def review():
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True,args=['--no-sandbox','--enable-webgl','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
        page=await browser.new_page(viewport={'width':1920,'height':1200});page.set_default_timeout(90000)
        errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
        await page.goto('http://127.0.0.1:4173/')
        await page.wait_for_function('window.panoramaReview?.ready === true',timeout=90000)
        await page.add_style_tag(content='.view-top,.view-bottom {visibility:hidden !important}')
        canvas=page.locator('#panorama canvas')
        await page.click('[data-stop="pumping"]')
        await canvas.screenshot(path=REVIEW/'mapped-trees-station.png')
        print('Pumping station trees captured.',flush=True)
        await page.click('[data-side="north"]');await page.click('[data-stop="mill"]')
        await canvas.screenshot(path=REVIEW/'mill-bridge-aligned.png')
        bounds=await page.locator('#panorama').bounding_box();cx,cy=bounds['x']+bounds['width']/2,bounds['y']+bounds['height']/2
        await page.mouse.move(cx,cy);await page.mouse.down();await page.mouse.move(cx,cy-100);await page.mouse.up()
        await canvas.screenshot(path=REVIEW/'mill-bridge-river.png')
        print('Mill crossing captured.',flush=True)
        await page.click('[data-side="south"]');await page.click('[data-stop="river"]')
        await canvas.screenshot(path=REVIEW/'mapped-trees-south.png')
        await page.mouse.move(cx,cy);await page.mouse.down();await page.mouse.move(cx-343,cy+21);await page.mouse.up()
        await canvas.screenshot(path=REVIEW/'mapped-gardens.png')
        diagnostic=await page.evaluate('window.panoramaReview')
        assert diagnostic['mappedTrees']['count']==16
        assert diagnostic['terrain']['gardenBeds']>250
        assert diagnostic['infrastructure']['roadRoutes']==50
        assert not errors,errors
        report={'checks':['16 map-positioned trees','expanded allotments rendered','station, mill crossing and both river directions rendered','50 road traces retained','no page/shader errors'], 'render':diagnostic,'scope':'Desktop landscape review; later-map trees and broader allotment extent explicitly interpreted for c1900.'}
        (REVIEW/'mill-trees-checks.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report,indent=2),flush=True);await browser.close()
if __name__=='__main__':asyncio.run(review())
