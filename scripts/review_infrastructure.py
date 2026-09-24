"""Focused final check of map-based roads, railway levels and open ground."""
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
        await page.click('[data-side="north"]');await page.click('[data-stop="north"]')
        await page.locator('#panorama').focus()
        bounds=await page.locator('#panorama').bounding_box();cx,cy=bounds['x']+bounds['width']/2,bounds['y']+bounds['height']/2
        await page.mouse.move(cx,cy);await page.mouse.down();await page.mouse.move(cx-214,cy-30);await page.mouse.up()
        await page.locator('#panorama canvas').screenshot(path=REVIEW/'lighting-roads-railway.png')
        diagnostic=await page.evaluate('window.panoramaReview')
        assert diagnostic['infrastructure']['roadRoutes']==50
        assert diagnostic['infrastructure']['raisedRailways']==3
        assert diagnostic['terrain']['vegetationTufts']>0
        assert not errors,errors
        report={'checks':['final map traces: 50 routes','three raised railway routes','open-ground vegetation present','no page/shader errors'], 'render':diagnostic,'scope':'Focused desktop infrastructure review after removing the uncertain eastern rear-plot trace.'}
        (REVIEW/'infrastructure-checks.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report,indent=2),flush=True);await browser.close()
if __name__=='__main__':asyncio.run(review())
