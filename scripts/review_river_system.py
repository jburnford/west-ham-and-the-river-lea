"""Check the full river view, separate from the existing local flood demo."""
import json
from pathlib import Path
from playwright.async_api import async_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'scenes/channelsea-sewer-panorama/review'

async def review_river_system(url,banks_only=False):
    OUT.mkdir(parents=True,exist_ok=True);errors=[]
    previous=json.loads((OUT/'river-system-browser-checks.json').read_text()) if (OUT/'river-system-browser-checks.json').exists() else None
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True,args=['--no-sandbox','--enable-webgl','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage'])
        page=await browser.new_page(viewport={'width':1100,'height':760},device_scale_factor=1)
        page.set_default_timeout(120000)
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('console',lambda m:(errors.append(m.text),print(m.text[:400],flush=True)) if m.type=='error' else print(m.text[:400],flush=True) if m.type=='warning' else None)
        await page.goto(url+'/?rivers=1&quality=lite')
        await page.wait_for_function('window.panoramaReview?.riverSystem && document.querySelector("[data-river-view]")',timeout=300000)
        print('Full river system loaded',flush=True)
        state=await page.evaluate('panoramaReview');sewer=state['sewerCrossing']
        assert state['riverSystem']['pieces']>=60
        assert not state['riverSystem']['floodDomainChanged']
        patches=state['riverSystem']['banks']['terrainPatches']
        assert {p['id']:len(p['controls']) for p in patches}=={'north-railway-marsh':4,'old-lea-east-bank-margin':4,'knobshill-low-ground':1,'waterworks-east-margin':3,'waterworks-upper-bank':3,'temple-mills-bank-path':3,'potters-ditch-low-ground':2,'city-mill-bank-and-ground':4}
        assert state['riverSystem']['railwayGroundAdjustments']>0
        assert patches[0]['appliedToDisplayTerrain'] and not patches[0]['appliedToFloodSolver']
        assert state['riverSystem']['banks']['canalFacingLengthMetres']>1000
        assert state['riverSystem']['banks']['shoreLengthMetres']>10000
        assert state['riverSystem']['banks']['materialGroups'][1]['count']>0
        assert sewer['bounds']['enclosure']['max'][1]-sewer['bounds']['enclosure']['min'][1]>2
        if previous:assert sewer==previous['sewer'],'Bank work changed the sewer enclosure'
        assert not await page.evaluate('Boolean(window.landscapeFloodReview)')
        views=['surveyed-marsh-banks','railway-marsh-banks','surveyed-lea-banks','surveyed-pudding-banks','knobshill-marsh-banks','waterworks-margin-banks','waterworks-upper-banks','temple-mills-path-banks','potters-ditch-banks','city-mill-ground-banks','earth-river-banks','hackney-canal-banks','limehouse-canal-banks']
        if not banks_only:views=['lower-lea-rivers','lea-bridge-rivers','upper-channelsea-rivers','hackney-cut-rivers','limehouse-cut-rivers','thames-mouth-rivers']+views
        for name in views:
            await page.click(f'[data-river-view="{name}"]')
            await page.wait_for_timeout(700)
            await page.screenshot(path=str(OUT/f'river-system-{name}.png'))
            print('Captured '+name,flush=True)
        await page.set_viewport_size({'width':390,'height':844})
        assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        await page.screenshot(path=str(OUT/'river-system-mobile.png'))
        assert not errors,errors
        await browser.close()
    (OUT/'river-system-browser-checks.json').write_text(json.dumps({'status':'PASS','riverSystem':state['riverSystem'],'sewer':sewer,'views':views,'mobileWidth':390,'errors':errors},indent=2)+'\n')
    print('River system browser checks passed.',flush=True)
