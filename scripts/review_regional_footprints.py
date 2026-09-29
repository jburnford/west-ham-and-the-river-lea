"""Exercise regional plans through the local application's normal UI."""
import asyncio
import json
import os
from pathlib import Path
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'scenes/channelsea-sewer-panorama/review'

async def review():
    OUT.mkdir(parents=True,exist_ok=True)
    errors=[]
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True,env=dict(os.environ,GALLIUM_DRIVER='d3d12',MESA_D3D12_DEFAULT_ADAPTER_NAME='NVIDIA'),args=['--no-sandbox','--enable-webgl','--use-angle=gl','--ignore-gpu-blocklist','--enable-unsafe-swiftshader','--disable-dev-shm-usage'])
        page=await browser.new_page(viewport={'width':1440,'height':1000},device_scale_factor=1)
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
        await page.goto('http://127.0.0.1:4175/?view=west-ham-region&quality=full')
        await page.wait_for_function('window.panoramaReview?.regionalFootprints?.overviewReady',timeout=180000)
        await page.wait_for_timeout(2500)
        reports={}
        for view in ['west-ham-region','forest-gate-plan','plaistow-plan','west-ham-region']:
            await page.locator('#destination').select_option(view)
            await page.wait_for_timeout(3000)
            await page.wait_for_function('window.panoramaReview.regionalFootprints.loading===0',timeout=60000)
            reports[view]=await page.evaluate('window.panoramaReview')
            await page.screenshot(path=str(OUT/f'{view}.png'))
            print(f'Captured {view}: {reports[view]["regionalFootprints"]}',flush=True)
        await page.locator('#regional-footprints').uncheck()
        await page.wait_for_function('window.panoramaReview.regionalFootprints.enabled===false')
        await page.locator('#regional-footprints').check()
        await page.wait_for_function('window.panoramaReview.regionalFootprints.enabled===true')
        await page.locator('#map-open').click()
        await page.locator('#map-scope').select_option('region')
        assert await page.locator('#plan svg').get_attribute('viewBox')=='-4500 -5891 11200 12700'
        await page.screenshot(path=str(OUT/'regional-map.png'))
        await page.locator('#plan svg').click(position={'x':180,'y':240})
        await page.wait_for_timeout(2000)
        assert not await page.locator('#map-dialog').is_visible()
        reports['map-travel']=await page.evaluate('window.panoramaReview')
        await page.locator('#travel-toggle').click()
        await page.wait_for_timeout(2500)
        reports['bridge']=await page.evaluate('window.panoramaReview')
        await page.screenshot(path=str(OUT/'regional-bridge-regression.png'))
        assert reports['bridge']['movement']['mode']=='bridge'
        assert not errors,errors
        assert all(not r['regionalFootprints']['failedTiles'] for r in reports.values())
        assert all(r['regionalFootprints']['loadedDetailTiles']<=20 for r in reports.values())
        (OUT/'regional-footprints-checks.json').write_text(json.dumps({'views':reports,'errors':errors},indent=2)+'\n')
        await browser.close()
        print('Regional navigation, plan tiles, layer switch, map travel and bridge return passed.',flush=True)
if __name__=='__main__':asyncio.run(review())
