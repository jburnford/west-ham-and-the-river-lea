"""Render the marsh reconstruction in the actual industrial scene."""
import base64
import json
from pathlib import Path
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'scenes/channelsea-sewer-panorama/review'
VIEWS={
 'main-marsh-stratford':{'position':[-1600,180,-350],'target':[-1200,1,-900],'fov':60},
 'main-marsh-mill-meads':{'position':[-600,130,420],'target':[-350,0,80],'fov':60},
 'main-marsh-abbey':{'position':[330,125,520],'target':[150,0,170],'fov':60},
 'main-marsh-sewer':{'position':[0,11,70],'target':[-40,1,-160],'fov':66},
 'main-marsh-factories':{'position':[-30,30,470],'target':[-150,0,290],'fov':62},
 'main-marsh-canal':{'position':[-1797,5,1797],'target':[-1655,.5,1695],'fov':60},
}
async def review_main_landscape(url,quick=False):
 OUT.mkdir(parents=True,exist_ok=True);errors=[]
 views={k:v for k,v in VIEWS.items() if not quick or k=='main-marsh-abbey'}
 async with async_playwright() as p:
  browser=await p.chromium.launch(headless=True,args=['--no-sandbox','--enable-webgl','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage'])
  page=await browser.new_page(viewport={'width':960,'height':600},device_scale_factor=1)
  page.on('pageerror',lambda e:(errors.append(str(e)),print(str(e),flush=True)))
  page.on('console',lambda m:(errors.append(m.text),print(m.text[:400],flush=True)) if m.type=='error' else None)
  print('Loading main industrial scene',flush=True)
  await page.goto(url+'/?river-review&quality=full')
  await page.wait_for_function('Boolean(window.riverNetworkReview)',timeout=300000)
  print('Main industrial scene ready',flush=True)
  for name,view in views.items():
   capture=await page.evaluate('(v)=>riverNetworkReview(v)',view)
   (OUT/f'{name}.png').write_bytes(base64.b64decode(capture.split(',')[1]));print('Captured '+name,flush=True)
  state=await page.evaluate('panoramaReview')
  main=state['mainLandscape'];assert main['active'] and main['seatedObjects']>500
  assert main['groundMeshVertices']>100000
  assert state['factoryBuildings']['ranges']>500
  assert state['sewerCrossing']['bounds']['enclosure']['count']>=2
  assert main['railwayGradesRetained'] and not main['floodReady']
  assert not errors,errors
  await browser.close()
 (OUT/('main-landscape-final-checks.json' if quick else 'main-landscape-checks.json')).write_text(json.dumps({'status':'PASS','views':views,'render':state,'errors':errors},indent=2)+'\n')
 print('Main landscape browser checks passed',flush=True)
