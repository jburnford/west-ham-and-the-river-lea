"""Exercise flooding on the actual 3D landscape with software WebGL."""
import json
from pathlib import Path
from playwright.async_api import async_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'scenes/channelsea-sewer-panorama/review'

async def review_landscape_flood(url):
    OUT.mkdir(parents=True,exist_ok=True)
    errors=[]
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True,args=['--no-sandbox','--enable-webgl','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage'])
        page=await browser.new_page(viewport={'width':960,'height':700},device_scale_factor=1)
        page.set_default_timeout(120000)
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('console',lambda m:(errors.append(m.text),print(m.text[:400],flush=True)) if m.type=='error' else None)
        await page.goto(url+'/?flood=1&quality=lite')
        await page.wait_for_function('window.landscapeFloodReview?.state',timeout=300000)
        print('3D landscape flooding ready',flush=True)
        await page.wait_for_timeout(1500)
        initial=await page.evaluate('landscapeFloodReview.state')
        river=await page.evaluate('panoramaReview.riverNetwork')
        connections=river['reviewedConnections']
        assert {'three-mills','pudding-mill','bow-locks','abbey-mill'} <= {r['id'] for r in connections}
        assert all(r['capacity'] is None for r in connections)
        print(await page.evaluate('JSON.stringify({triangles:panoramaReview.triangles,drawCalls:panoramaReview.drawCalls,quality:panoramaReview.quality})'),flush=True)
        assert initial['floodedLandM2']>100000 and initial['enabled']
        sewer=await page.evaluate('panoramaReview.sewerCrossing')
        assert sewer['bounds']['enclosure']['count']>=2
        assert sewer['bounds']['enclosure']['max'][1]-sewer['bounds']['enclosure']['min'][1]>2
        await page.screenshot(path=str(OUT/'landscape-flood-overview.png'))
        await page.locator('#landscape-stage').fill('1.9')
        low=await page.evaluate('landscapeFloodReview.state');assert low['floodedLandM2']==0
        await page.locator('#landscape-stage').fill('4.5')
        high=await page.evaluate('landscapeFloodReview.state');assert high['floodedLandM2']>initial['floodedLandM2']
        await page.click('#landscape-toggle');assert not (await page.evaluate('landscapeFloodReview.state'))['enabled']
        await page.screenshot(path=str(OUT/'landscape-flood-dry.png'))
        await page.click('#landscape-mills')
        await page.screenshot(path=str(OUT/'core-river-three-mills-dry.png'))
        await page.click('#landscape-toggle');await page.click('#landscape-mills')
        await page.screenshot(path=str(OUT/'landscape-flood-three-mills.png'))
        await page.click('#landscape-sewer')
        assert await page.evaluate('panoramaReview.sewerCrossing')==sewer
        await page.screenshot(path=str(OUT/'landscape-flood-sewer.png'))
        await page.locator('#landscape-stage').fill('2.5');await page.click('#landscape-rise')
        await page.wait_for_function('landscapeFloodReview.state.levelODN>2.5')
        await page.click('#landscape-rise')
        await page.click('#landscape-overview')
        await page.set_viewport_size({'width':390,'height':844})
        await page.locator('#landscape-stage').fill('3.5')
        assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        await page.screenshot(path=str(OUT/'landscape-flood-mobile.png'))
        assert not errors,errors
        await browser.close()
    (OUT/'landscape-flood-browser-checks.json').write_text(json.dumps({'status':'PASS','initial':initial,'low':low,'high':high,'riverConnections':connections,'errors':errors,'checks':['actual 3D landscape','reviewed core connections loaded','river stage control','dry comparison','raise/pause','three camera views','sewer enclosure preserved','390px mobile no overflow']},indent=2)+'\n')
    print('Landscape flood browser checks passed.',flush=True)
