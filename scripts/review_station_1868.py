"""Review original station geometry informed by the author-supplied engraving."""
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
        await canvas.screenshot(path=REVIEW/'station-1868-wide.png')
        print('Station silhouette captured.',flush=True)
        await page.click('[data-side="north"]')
        await page.locator('#panorama').focus()
        for _ in range(3):await page.keyboard.press('+')
        bounds=await page.locator('#panorama').bounding_box();cx,cy=bounds['x']+bounds['width']/2,bounds['y']+bounds['height']/2
        await page.mouse.move(cx,cy);await page.mouse.down();await page.mouse.move(cx,cy+36);await page.mouse.up()
        await canvas.screenshot(path=REVIEW/'station-1868-detail.png')
        diagnostic=await page.evaluate('window.panoramaReview')
        assert diagnostic['stationStudy']['chimneys']==2
        assert diagnostic['stationStudy']['wingEndBays']==5
        assert diagnostic['mappedTrees']['count']==16
        assert not errors,errors
        report={'checks':['station and both chimney silhouettes rendered','closer view from north side of bridge','no page/shader errors'], 'render':diagnostic,'scope':'Desktop architectural study; engraving proportions and survival into c1900 interpreted.'}
        (REVIEW/'station-1868-checks.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report,indent=2),flush=True);await browser.close()
if __name__=='__main__':asyncio.run(review())
