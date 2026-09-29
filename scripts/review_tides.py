"""Check actual tide controls, reflections, and before/after river views."""
import asyncio
import base64
import json
import os
from playwright.async_api import async_playwright
from review_river_network import OUT

async def main():
    OUT.mkdir(parents=True, exist_ok=True)
    errors=[]
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True,env=dict(os.environ,
            GALLIUM_DRIVER='d3d12',MESA_D3D12_DEFAULT_ADAPTER_NAME='NVIDIA'),args=[
            '--no-sandbox','--enable-webgl','--use-angle=gl','--ignore-gpu-blocklist',
            '--enable-unsafe-swiftshader','--disable-dev-shm-usage'])
        page=await browser.new_page(viewport={'width':1440,'height':1000},reduced_motion='reduce')
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
        await page.goto('http://127.0.0.1:4175/?river-review&quality=full&view=wall-vista')
        await page.wait_for_function('Boolean(window.riverNetworkReview)',timeout=180000)
        assert not await page.evaluate('panoramaReview.tide.playing'),'Must start paused, including reduced-motion preference'
        await page.locator('.tide-controls summary').click()
        views={
            'garden-ground':{'position':[-295,4,160],'target':[-335,1,215],'fov':60},
            'terrain-seam':{'position':[-375,180,180],'target':[-235,0,90],'fov':60},
            'coal-barge':{'position':[5,12,32],'target':[20,1,49],'fov':52},
            'empty-barge':{'position':[-40,12,24],'target':[-26,1,37],'fov':52},
            'wall':{'position':[-625,6,-262],'target':[-638,3,-105],'fov':48},
            'channelsea':{'position':[0,9.2,0],'target':[-20,0,180],'fov':56},
            'marsh':{'position':[-710,260,320],'target':[-400,0,70],'fov':60}}
        states={}
        garden=await page.evaluate('panoramaReview.gardens')
        assert garden['plots']>80 and garden['patches']>200
        assert garden['sheds']<garden['plots']*.15 and garden['fallow']>0
        assert any(p[0]<-235 for p in garden['surfaceSamples']) and any(p[0]>-235 for p in garden['surfaceSamples'])
        for name,value in [('low',0),('high',100)]:
            await page.locator('#tide-level').fill(str(value))
            states[name]=await page.evaluate('panoramaReview.tide')
            assert abs(states[name]['level']-({'low':.06,'high':1.1}[name]))<1e-9
            offsets=await page.evaluate('panoramaReview.tideObjects')
            assert offsets['bargeOffsets'] and offsets['waterOffsets']
            assert all(abs(v-(states[name]['level']-.06))<1e-9 for values in offsets.values() for v in values)
            assert await page.evaluate('panoramaReview.reflection.planes')==({'low':1,'high':2}[name])
            assert await page.evaluate('panoramaReview.reflection.excludedBargeHolds')==4
            for view_name,view in views.items():
                image=await page.evaluate('(view)=>riverNetworkReview(view)',view)
                (OUT/f'tide-{view_name}-{name}.png').write_bytes(base64.b64decode(image.split(',')[1]))
            print(f'Captured {name} tide on Wall River, Channelsea, marsh and both barge types',flush=True)
        await page.locator('#tide-play').click()
        await page.wait_for_function('panoramaReview.tide.level < 1.09',timeout=20000)
        assert 'Falling' in await page.locator('#tide-state').text_content()
        await page.locator('#tide-play').click()
        paused=await page.evaluate('panoramaReview.tide')
        await page.wait_for_timeout(350)
        assert paused==await page.evaluate('panoramaReview.tide')
        await page.locator('#tide-play').click()
        await page.locator('#tide-level').fill('50')
        assert not await page.evaluate('panoramaReview.tide.playing')
        assert abs(await page.evaluate('panoramaReview.tide.level')-.58)<1e-9
        await page.locator('#tide-level').focus()
        await page.keyboard.press('ArrowRight')
        assert await page.locator('#tide-level').input_value()=='51'
        await page.set_viewport_size({'width':390,'height':844})
        await page.screenshot(path=str(OUT/'tide-controls-mobile.png'))
        box=await page.locator('.tide-controls').bounding_box()
        assert 0<=box['x'] and box['x']+box['width']<=390
        assert box['y']+box['height']<844
        assert not errors,errors
        (OUT/'tide-checks.json').write_text(json.dumps({'states':states,'paused':paused,'gardens':garden,'errors':errors},indent=2)+'\n')
        await browser.close()
        print('Tide controls passed: high/low, falling animation, pause, manual scrub, keyboard, mobile bounds and two reflection planes.',flush=True)

if __name__=='__main__':asyncio.run(main())
