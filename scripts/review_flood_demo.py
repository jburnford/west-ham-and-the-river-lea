"""Run the real worker simulation in browser; test playback, comparisons and export."""
import json
from pathlib import Path
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'scenes/channelsea-sewer-panorama/review'
async def review_flood_demo(url):
    OUT.mkdir(parents=True,exist_ok=True);errors=[]
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
        page=await browser.new_page(viewport={'width':1280,'height':1050},device_scale_factor=1)
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
        await page.goto(url+'/flood-demo.html')
        await page.wait_for_function('window.floodDemoReview?.status==="complete"',timeout=180000)
        first=await page.evaluate('window.floodDemoReview');assert first['frames']==61
        assert first['runs'][0]['stats']['wetAreaM2']>0
        assert abs(first['runs'][0]['stats']['massError'])<1e-5
        print('Default flood experiment complete',flush=True)
        # Set timeline with actual input event; inspect a cell and activate provenance.
        await page.locator('#time').fill('35');await page.locator('#time').dispatch_event('input')
        assert (await page.evaluate('window.floodDemoReview'))['selectedTime']==2100
        await page.check('#evidence')
        canvas=page.locator('canvas').first;await canvas.scroll_into_view_if_needed();box=await canvas.bounding_box()
        await page.mouse.move(box['x']+box['width']*.6,box['y']+box['height']*.5)
        assert 'm ODN' in await page.locator('#inspect').inner_text()
        await page.uncheck('#evidence')
        await page.screenshot(path=str(OUT/'flood-demo-desktop.png'),full_page=True)
        await page.click('#compare')
        await page.wait_for_function('window.floodDemoReview?.status==="complete" && window.floodDemoReview.runs.length===2',timeout=180000)
        compared=await page.evaluate('window.floodDemoReview')
        a,b=[r['stats'] for r in compared['runs']]
        assert b['eastVolume']>a['eastVolume']+100
        assert b['culvertNetVolume']==0
        print('Open/blocked browser comparison complete',flush=True)
        await page.locator('#time').fill('35');await page.locator('#time').dispatch_event('input')
        await page.screenshot(path=str(OUT/'flood-demo-comparison.png'),full_page=True)
        # Export must describe the selected frame, not final time or changed inputs.
        async with page.expect_download() as info:await page.click('#download')
        download=await info.value;path=OUT/'flood-demo-export.json';await download.save_as(path)
        exported=json.loads(path.read_text());assert exported['selectedTime']==2100
        assert len(exported['runs'])==2 and len(exported['runs'][0]['depthMetres'])==21600
        for run in exported['runs']:
            assert abs(sum(run['depthMetres'])*exported['cellSizeMetres']**2-run['stats']['volume'])<.01
        await page.click('#play');await page.wait_for_timeout(800);await page.click('#play')
        assert (await page.evaluate('window.floodDemoReview'))['selectedTime']>2100
        # Changes must not relabel old results. Cancel an active rerun safely.
        await page.select_option('#gate','both')
        assert (await page.evaluate('window.floodDemoReview'))['runs'][0]['params']['gate']=='east-to-west'
        assert 'Settings changed' in await page.locator('#status').inner_text()
        await page.click('#run');await page.wait_for_timeout(250);await page.click('#cancel')
        assert 'stopped' in await page.locator('#status').inner_text()
        # Mobile initial screen then comparison view using already tested full workers.
        await page.set_viewport_size({'width':390,'height':844})
        await page.select_option('#gate','east-to-west');await page.click('#compare')
        await page.wait_for_function('window.floodDemoReview?.status==="complete" && window.floodDemoReview.runs.length===2',timeout=180000)
        await page.locator('#time').fill('35');await page.locator('#time').dispatch_event('input')
        assert await page.evaluate('document.documentElement.scrollWidth<=window.innerWidth')
        await page.screenshot(path=str(OUT/'flood-demo-mobile.png'),full_page=True)
        assert not errors,errors
        await browser.close()
    (OUT/'flood-demo-browser-checks.json').write_text(json.dumps({'status':'PASS','default':first,'comparison':compared,'errors':errors,'checks':['real worker full-hour run','open vs blocked','water balance','timeline','play/pause','ground inspector','provenance toggle','selected-frame export','changed settings retain result labels','cancellation','390px mobile without overflow']},indent=2)+'\n')
    print('Flood demo browser checks passed.',flush=True)
