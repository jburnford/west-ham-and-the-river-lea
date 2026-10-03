"""Exercise the regional evidence map without loading the full 3D scene."""
import json
from pathlib import Path
from playwright.async_api import async_playwright

OUT=Path(__file__).resolve().parents[1]/'scenes/channelsea-sewer-panorama/review'

async def review_lower_lea_region(url):
 OUT.mkdir(parents=True,exist_ok=True);errors=[]
 async with async_playwright() as p:
  browser=await p.chromium.launch(headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  page=await browser.new_page(viewport={'width':1280,'height':1000},device_scale_factor=1)
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
  await page.goto(url+'/lower-lea-region.html')
  await page.wait_for_function('window.lowerLeaRegionReview?.ready')
  initial=await page.evaluate('lowerLeaRegionReview');assert initial['summary']['primaryReaches']==23
  assert initial['terrainYear']=='2003' and not initial['historicalDEM']
  assert initial['elevationView']=='coverage'
  assert initial['audit']['usableRoadCandidates']>900
  assert initial['trial']['ground']>100 and initial['trial']['road']>900
  assert initial['audit']['regionalSupplementObservations']==63
  assert initial['terrainExclusions']==20
  assert await page.locator('#elevation-priorities button').count()>0
  await page.get_by_text('Unusual height differences',exact=True).click()
  await page.locator('[data-observation="sh_540148_182306"]').click()
  assert 'observed 3.4 ft' in await page.locator('#selection').inner_text()
  await page.locator('[data-observation="sh_537434_182618"]').click()
  assert 'railway-cutting geometry' in await page.locator('#selection').inner_text()
  white_post=page.locator('[data-observation="sh_536970_184484"]')
  if await white_post.count():
   await white_post.click()
   assert 'Retain the clear 16.4 ft White Post Lane dot' in await page.locator('#selection').inner_text()
  else:
   # New nearby readings can remove a previous >1m holdout residual without
   # changing the reviewed dot. Do not require a resolved outlier to persist.
   white=await page.evaluate("""async()=>{const a=await (await fetch('./data/lower-lea-region/elevation-audit.json')).json();return a.records.find(r=>r.id==='sh_536970_184484');}""")
   assert white['value_ft']==16.4 and white['auditStatus']=='reviewed-road'
  await page.click('#whole')
  await page.select_option('#surface-filter','ground')
  ground_count=await page.evaluate('lowerLeaRegionReview.visibleMarks')
  await page.select_option('#surface-filter','road')
  assert (await page.evaluate('lowerLeaRegionReview.visibleMarks'))>ground_count
  await page.select_option('#surface-filter','usable')
  await page.select_option('#elevation-view','trial')
  assert 'interpolation experiment' in await page.locator('#elevation-notice').inner_text()
  await page.screenshot(path=str(OUT/'lower-lea-elevation-trial.png'),full_page=True)
  await page.click('#western')
  western=await page.evaluate('lowerLeaRegionReview.view')
  assert western[2]-western[0]<2000
  await page.screenshot(path=str(OUT/'lower-lea-elevation-western.png'),full_page=True)
  await page.click('#marsh-lanes')
  northern=await page.evaluate('lowerLeaRegionReview.view')
  # Fit includes the new western marsh traverse and the eastern lane dots.
  assert northern[0]<536287 and northern[2]>537817
  assert northern[1]<185259 and northern[3]>186233
  assert northern[2]-northern[0]<2500
  await page.screenshot(path=str(OUT/'lower-lea-elevation-northern.png'),full_page=True)
  await page.click('#eastern')
  eastern=await page.evaluate('lowerLeaRegionReview.view')
  assert eastern[0]<537773 and eastern[2]>538165
  assert eastern[1]<185267 and eastern[3]>185578
  assert eastern[2]-eastern[0]<1500
  await page.screenshot(path=str(OUT/'lower-lea-elevation-eastern.png'),full_page=True)
  await page.select_option('#elevation-view','coverage')
  await page.locator('#elevation-priorities button').first.click()
  assert 'source' in (await page.locator('#selection').inner_text()).lower()
  await page.click('#whole')
  assert await page.locator('#network-review p').count()==4
  assert await page.locator('a[href*="on:six-inch-2nd"]').count()==1
  await page.screenshot(path=str(OUT/'lower-lea-region-overview.png'),full_page=True)
  await page.click('#current');current=await page.evaluate('lowerLeaRegionReview.view');assert current[2]-current[0]<2000
  await page.check('#all-marks');assert (await page.evaluate('lowerLeaRegionReview.visibleMarks'))>initial['visibleMarks']
  await page.select_option('#reach','Lower_River_Lea-0');assert 'Bow Creek' in await page.locator('#selection').inner_text()
  await page.locator('#gap-list button').first.click();assert 'provisional cartographic continuity' in await page.locator('#selection').inner_text()
  assert await page.locator('#navigation-list button').count()==4
  await page.locator('#navigation-list button').first.click();assert 'Navigation interface' in await page.locator('#selection').inner_text()
  await page.locator('#navigation-list button').filter(has_text='mapped open junction').click();assert 'No gate is shown' in await page.locator('#selection').inner_text()
  await page.locator('[data-site="abbey-corn-mill"]').click();assert 'not the exact structure footprint' in await page.locator('#selection').inner_text()
  assert (await page.evaluate('lowerLeaRegionReview.selectedSite'))=='abbey-corn-mill'
  await page.locator('[data-site="waterworks-flood-gate"]').click();assert 'Flood Gate' in await page.locator('#selection').inner_text()
  await page.locator('[data-site="city-mill"]').click();assert 'Chemical' in await page.locator('#selection').inner_text()
  await page.locator('[data-site="marshgate-lock"]').click();assert 'under-bridge water route' in await page.locator('#selection').inner_text()
  await page.locator('[data-site="pudding-mill"]').click();assert 'do not create an open-water bypass' in await page.locator('#selection').inner_text()
  await page.locator('[data-site="old-ford-side-floodgate"]').click();assert 'separate control' in await page.locator('#selection').inner_text()
  await page.locator('[data-site="temple-mills-weir"]').click();assert 'Weir is explicitly labelled' in await page.locator('#selection').inner_text()
  assert await page.locator('#period-comparisons p').count()==7
  await page.locator('[data-site="three-mills"]').click()
  assert 'single mill-control group' in await page.locator('#selection').inner_text()
  assert (await page.evaluate('lowerLeaRegionReview.connectionReview.structureRoutes'))==3
  await page.screenshot(path=str(OUT/'lower-lea-region-three-mills.png'),full_page=True)
  await page.locator('[data-site="bow-locks"]').click()
  assert 'lock-controlled connection' in await page.locator('#selection').inner_text()
  await page.select_option('#reach','Lower_River_Lea-0');assert (await page.evaluate('lowerLeaRegionReview.selectedSite')) is None
  await page.locator('#gap-list button').first.click()
  await page.screenshot(path=str(OUT/'lower-lea-region-gap.png'),full_page=True)
  await page.click('#whole');await page.check('#revision');await page.check('#first')
  await page.uncheck('#relief');await page.check('#relief')
  await page.select_option('#elevation-view','off')
  canvas=page.locator('#map');await canvas.scroll_into_view_if_needed();b=await canvas.bounding_box()
  await page.mouse.move(b['x']+b['width']*.6,b['y']+b['height']*.4)
  assert '2003' in await page.locator('#inspect').inner_text()
  await page.select_option('#elevation-view','coverage')
  await page.mouse.move(b['x']+b['width']*.61,b['y']+b['height']*.4)
  assert 'Nearest ground/street candidate' in await page.locator('#inspect').inner_text()
  await page.select_option('#elevation-view','trial')
  await page.mouse.move(b['x']+b['width']*.62,b['y']+b['height']*.4)
  assert 'trial' in (await page.locator('#inspect').inner_text()).lower()
  await page.select_option('#elevation-view','coverage')
  before=await page.evaluate('lowerLeaRegionReview.view');await canvas.focus();await page.keyboard.press('+')
  after=await page.evaluate('lowerLeaRegionReview.view');assert after[2]-after[0]<before[2]-before[0]
  await page.keyboard.press('ArrowRight');assert (await page.evaluate('lowerLeaRegionReview.view'))[0]>after[0]
  await page.keyboard.press('Home')
  await page.mouse.move(b['x']+b['width']*.5,b['y']+b['height']*.5);await page.mouse.down();await page.mouse.move(b['x']+b['width']*.55,b['y']+b['height']*.55);await page.mouse.up()
  assert (await page.evaluate('lowerLeaRegionReview.view'))!=initial['view']
  await page.click('#whole');await page.uncheck('#all-marks');await page.uncheck('#revision');await page.uncheck('#first')
  await page.set_viewport_size({'width':390,'height':844});await page.evaluate('scrollTo(0,0)')
  assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  await page.screenshot(path=str(OUT/'lower-lea-region-mobile.png'),full_page=True)
  await page.goto(url+'/lower-lea-region.html?elevation=trial&area=western')
  await page.wait_for_function('window.lowerLeaRegionReview?.ready')
  assert (await page.evaluate('lowerLeaRegionReview.elevationView'))=='trial'
  assert (await page.evaluate('lowerLeaRegionReview.view'))==western
  await page.goto(url+'/lower-lea-region.html?elevation=trial&area=northern')
  await page.wait_for_function('window.lowerLeaRegionReview?.ready')
  assert (await page.evaluate('lowerLeaRegionReview.view'))==northern
  await page.goto(url+'/lower-lea-region.html?elevation=trial&area=eastern')
  await page.wait_for_function('window.lowerLeaRegionReview?.ready')
  assert (await page.evaluate('lowerLeaRegionReview.view'))==eastern
  await page.goto(url+'/lower-lea-region.html?elevation=landscape')
  await page.wait_for_function('window.lowerLeaRegionReview?.ready')
  assert (await page.evaluate('lowerLeaRegionReview.elevationView'))=='landscape'
  assert (await page.evaluate('lowerLeaRegionReview.landscape.landAreaKm2'))>40
  assert 'Working 1900 landscape' in await page.locator('#elevation-notice').inner_text()
  await page.set_viewport_size({'width':1280,'height':1000})
  await page.screenshot(path=str(OUT/'lower-lea-working-landscape-map.png'),full_page=True)
  await page.select_option('#elevation-view','landscape-evidence')
  assert 'rose' in await page.locator('#elevation-notice').inner_text()
  await page.goto(url+'/lower-lea-landscape.html')
  await page.wait_for_function('window.lowerLeaLandscapeReview?.ready')
  landscape=await page.evaluate('lowerLeaLandscapeReview')
  assert landscape['renderedTriangles']==landscape['triangleCount'] and landscape['triangleCount']>100000
  await page.screenshot(path=str(OUT/'lower-lea-working-landscape-3d.png'),full_page=True)
  await page.select_option('#landscape-colour','evidence')
  assert (await page.evaluate('lowerLeaLandscapeReview.colourMode'))=='evidence'
  await page.select_option('#landscape-scale','1')
  assert (await page.evaluate('lowerLeaLandscapeReview.scale'))==1
  await page.click('#landscape-north')
  assert (await page.evaluate('lowerLeaLandscapeReview.radius'))<landscape['radius']
  await page.screenshot(path=str(OUT/'lower-lea-working-landscape-evidence.png'),full_page=True)
  await page.click('#landscape-marsh')
  assert (await page.evaluate('lowerLeaLandscapeReview.radius'))==1000
  await page.screenshot(path=str(OUT/'lower-lea-city-mill-marsh-evidence.png'),full_page=True)
  await page.select_option('#landscape-colour','height')
  await page.select_option('#landscape-scale','4')
  await page.screenshot(path=str(OUT/'lower-lea-city-mill-marsh-height.png'),full_page=True)
  await page.click('#landscape-pudding-city')
  assert (await page.evaluate('lowerLeaLandscapeReview.target'))==[-825,0,-640]
  await page.screenshot(path=str(OUT/'lower-lea-pudding-city-marsh-height.png'),full_page=True)
  await page.select_option('#landscape-colour','evidence')
  assert 'cottage garden' in await page.locator('#landscape-legend').inner_text()
  await page.screenshot(path=str(OUT/'lower-lea-pudding-city-marsh-evidence.png'),full_page=True)
  await page.goto(url+'/lower-lea-landscape.html?area=pudding-city')
  await page.wait_for_function('window.lowerLeaLandscapeReview?.ready && lowerLeaLandscapeReview.radius===1000')
  assert (await page.evaluate('lowerLeaLandscapeReview.target'))==[-825,0,-640]
  await page.select_option('#landscape-scale','1')
  await page.screenshot(path=str(OUT/'lower-lea-pudding-city-marsh-true-scale.png'),full_page=True)
  await page.select_option('#landscape-surface','ground')
  assert (await page.evaluate('lowerLeaLandscapeReview.surfaceMode'))=='ground'
  ground_state=await page.evaluate('lowerLeaLandscapeReview')
  assert not ground_state['structuresVisible'] and ground_state['renderedTriangles']==ground_state['groundTriangleCount']
  await page.click('#landscape-mill-meads')
  await page.screenshot(path=str(OUT/'lower-lea-mill-meads-ground.png'),full_page=True)
  await page.select_option('#landscape-surface','surface')
  surface_state=await page.evaluate('lowerLeaLandscapeReview')
  assert surface_state['structuresVisible'] and surface_state['structureTriangleCount']>100000
  assert surface_state['renderedTriangles']==surface_state['groundTriangleCount']+surface_state['structureTriangleCount']
  await page.screenshot(path=str(OUT/'lower-lea-mill-meads-surfaces.png'),full_page=True)
  await page.check('#landscape-observations')
  assert (await page.evaluate('lowerLeaLandscapeReview.observationsVisible'))
  await page.click('#landscape-plaistow')
  await page.screenshot(path=str(OUT/'lower-lea-plaistow-surface-evidence.png'),full_page=True)
  await page.uncheck('#landscape-observations')
  await page.click('#landscape-south')
  canvas=page.locator('#landscape-frame canvas');await canvas.focus();await page.keyboard.press('Home')
  assert (await page.evaluate('lowerLeaLandscapeReview.radius'))==landscape['radius']
  await page.keyboard.press('+')
  assert (await page.evaluate('lowerLeaLandscapeReview.radius'))<landscape['radius']
  b=await canvas.bounding_box()
  await page.mouse.click(b['x']+b['width']*.5,b['y']+b['height']*.5)
  assert 'provisional ODN' in await page.locator('#landscape-inspect').inner_text()
  await page.set_viewport_size({'width':390,'height':844});await page.evaluate('scrollTo(0,0)')
  assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  await page.screenshot(path=str(OUT/'lower-lea-working-landscape-mobile.png'),full_page=True)
  await page.goto(url+'/lower-lea-marsh-evidence.html')
  assert 'Forty-five' in await page.locator('main').inner_text()
  assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  for src in await page.locator('img').evaluate_all('(imgs)=>imgs.map(i=>({complete:i.complete,width:i.naturalWidth}))'):
   assert src['complete'] and src['width']>0
  await page.set_viewport_size({'width':1280,'height':1000})
  await page.screenshot(path=str(OUT/'lower-lea-marsh-analysis.png'),full_page=True)
  assert not errors,errors
  await browser.close()
 (OUT/'lower-lea-region-browser-checks.json').write_text(json.dumps({'status':'PASS','initial':initial,'landscape':landscape,'errors':errors,'checks':['working landscape map and evidence modes','3D mesh render and height inspection','true/exaggerated scale and evidence colours','3D keyboard and mobile controls','regional overview','ground and street eligibility filters','coverage versus trial modes','Chargeable Lane residual inspection','cached source gap priorities','trial deep link','historical vs 2003 label','current domain','height layers','river selection','gap inspection','water layer toggles','ground inspector','keyboard zoom/pan/reset','pointer pan','390px mobile no overflow']},indent=2)+'\n')
 print('Regional landscape, 3D view and elevation evidence browser checks passed.',flush=True)
