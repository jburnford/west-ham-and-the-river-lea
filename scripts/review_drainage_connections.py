"""Exercise the actual interactive topology study without loading the 3D scene."""
import json
from pathlib import Path
from playwright.async_api import async_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'scenes/channelsea-sewer-panorama/review'


async def review_connections(url):
    OUT.mkdir(parents=True,exist_ok=True)
    states={};errors=[]
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
        page=await browser.new_page(viewport={'width':1180,'height':1050},device_scale_factor=1)
        page.on('pageerror',lambda e:errors.append(str(e)))
        await page.goto(url+'/drainage-connections.html')
        await page.wait_for_function('Boolean(window.drainageConnectionReview)')
        default=await page.evaluate('window.drainageConnectionReview')
        assert default['scenario']=='east-to-west' and len(default['reachable'])==5
        states['default']=default
        await page.wait_for_function('Boolean(window.culvertSectionReview)')
        assert (await page.evaluate('window.culvertSectionReview'))['id']=='working'
        for case,fits,regrade in [('compact',True,False),('working',True,False),('large-shallow',False,False),('large-deep',True,True)]:
            await page.select_option('#culvert-case',case)
            section=await page.evaluate('window.culvertSectionReview')
            assert section['fitsCoverAssumption']==fits and section['approachRegradingRequired']==regrade
            assert await page.evaluate('window.drainageConnectionReview')==default
            states['section-'+case]=section
        await page.select_option('#culvert-case','working')
        for scenario,count in [('evidence-only',2),('crossing-blocked',2),('east-to-west',5),('west-to-east',2),('both-ways',5)]:
            await page.select_option('#scenario',scenario)
            result=await page.evaluate('window.drainageConnectionReview')
            assert len(result['reachable'])==count and not result['hydraulicReady']
            states[scenario]=result
        await page.screenshot(path=str(OUT/'drainage-connections-open.png'),full_page=True)
        await page.select_option('#scenario','east-to-west')
        await page.select_option('#start','west-junction')
        assert len((await page.evaluate('window.drainageConnectionReview'))['reachable'])==3
        await page.select_option('#scenario','west-to-east')
        assert len((await page.evaluate('window.drainageConnectionReview'))['reachable'])==5
        # Keyboard selection of the unconnected northern sluice must not create a link.
        node=page.locator('[aria-label="Start at Northern sluice — unconnected"]')
        await node.focus();await page.keyboard.press('Enter')
        assert (await page.evaluate('window.drainageConnectionReview'))['reachable']==['manor-road-north']
        await page.set_viewport_size({'width':390,'height':844})
        await page.select_option('#scenario','evidence-only');await page.select_option('#start','manor-east')
        assert await page.evaluate('document.documentElement.scrollWidth<=window.innerWidth')
        await page.screenshot(path=str(OUT/'drainage-connections-mobile.png'),full_page=True)
        await page.select_option('#culvert-case','large-shallow')
        assert 'Does not fit' in await page.locator('#culvert-result').inner_text()
        assert await page.evaluate('document.documentElement.scrollWidth<=window.innerWidth')
        await page.screenshot(path=str(OUT/'culvert-section-rejected-mobile.png'),full_page=True)
        assert not errors,errors
        await browser.close()
    report={'status':'PASS','states':states,'errors':errors,
            'checks':['default represents preferred east-to-west drainage','all five scenarios','both starting sides',
                      'one-way reversal','keyboard node selection','four culvert sections and cover limits',
                      'section selector does not change hydraulic topology','mobile no overflow','no browser errors']}
    (OUT/'drainage-connections-ui-checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Drainage connection browser checks passed.',flush=True)
