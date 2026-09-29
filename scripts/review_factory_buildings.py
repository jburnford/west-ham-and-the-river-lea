"""Render district factory checks through the real application, locally only."""
import asyncio
import argparse
import json
from functools import partial
from http.server import ThreadingHTTPServer
from threading import Thread

import review_river_network as runner
from playwright.async_api import async_playwright

runner.REPORT_NAME = 'factory-buildings-checks.json'
runner.VIEWS = {
    'great-eastern-overview': {'position': [-1350, 340, -80], 'target': [-880, 5, -650], 'fov': 68},
    'great-eastern-soap-bank': {'position': [-1240, 5, -150], 'target': [-1280, 8, -194], 'fov': 64},
    'great-eastern-sewer-bridge': {'position': [-1005, 9.1, -491], 'target': [-930, 9.1, -471], 'fov': 60},
    'great-eastern-city-river': {'position': [-860, 8, -450], 'target': [-915, 7, -504], 'fov': 60},
    'great-eastern-north': {'position': [-650, 150, -900], 'target': [-460, 5, -1150], 'fov': 62},
    'great-eastern-track-level': {'position': [-1060, 13, -375], 'target': [-975, 12, -450], 'fov': 60},
    'factories-city': {'position': [-800, 230, -95], 'target': [-745, 0, -330], 'fov': 58},
    'factories-howards-south': {'position': [-720, 17, -175], 'target': [-716, 10, -280], 'fov': 66},
    'factories-marshgate': {'position': [-1050, 220, -170], 'target': [-881, 0, -335], 'fov': 62},
    'factories-sugar-north': {'position': [-900, 210, 220], 'target': [-747, 0, -20], 'fov': 65},
    'factories-sugar-house': {'position': [-725, 23, -5], 'target': [-647, 12, -41], 'fov': 48},
    'factories-sugar-south': {'position': [-910, 200, 410], 'target': [-704, 0, 148], 'fov': 60},
    'factories-three-mills': {'position': [-666, 110, 555], 'target': [-527, 0, 401], 'fov': 66},
    'factories-three-mills-low': {'position': [-650, 9, 405], 'target': [-584, 10, 399], 'fov': 65},
    'factories-old-lea': {'position': [-1350, 240, 90], 'target': [-1107, 0, -175], 'fov': 65},
    'factories-soap-front': {'position': [-1340, 12, -95], 'target': [-1260, 12, -110], 'fov': 62},
    'factories-sawmill-ranges': {'position': [-1100, 50, 15], 'target': [-1045, 4, -45], 'fov': 58},
    'factories-jute': {'position': [-520, 135, -590], 'target': [-640, 2, -775], 'fov': 62},
    'factories-sawmill-yard': {'position': [-950, 150, 65], 'target': [-1100, 0, -85], 'fov': 58},
    'factories-sawmill-stacks': {'position': [-1080, 5, -55], 'target': [-1135, 1.2, -105], 'fov': 60},
    'factories-west-ham-gas': {'position': [-417, 205, -82], 'target': [-214, 0, -345], 'fov': 62},
    'factories-bromley-holders': {'position': [-680, 270, 870], 'target': [-309, 0, 646], 'fov': 65},
    'factories-bromley-production': {'position': [-630, 260, 1440], 'target': [-365, 0, 1100], 'fov': 65},
    'factories-bridge-regression': {'position': [0, 9.2, 0], 'target': [-20, 0, 180], 'fov': 56},
}

async def atlas(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
        page = await browser.new_page(viewport={'width': 1440, 'height': 1050})
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        await page.goto(url+'/factory-atlas.html')
        expected = json.loads((runner.ROOT/'docs/data/factory-buildings.json').read_text())
        await page.wait_for_function('n=>document.querySelectorAll("path.range").length === n', arg=len(expected['buildings']))
        assert await page.locator('#sites option').count() == len(expected['sites'])+1
        await page.locator('#sites').select_option('964')
        await page.locator('path[aria-label^="Sugar House (1882)"]').click()
        assert '1882' in await page.locator('#details h2').inner_text()
        assert 'Five storeys' in await page.locator('#details').inner_text()
        await page.screenshot(path=str(runner.OUT/'factory-atlas-sugar.png'))
        await page.locator('#reset').click()
        assert await page.locator('#sites').input_value() == 'all'
        await page.screenshot(path=str(runner.OUT/'factory-atlas-all.png'))
        assert not errors, errors
        await browser.close()
        print(f"Factory atlas: all {len(expected['sites'])} sites, {len(expected['buildings'])} selectable ranges, source panel and reset passed.", flush=True)


async def review(url):
    await runner.review(url)
    await atlas(url)


async def chimneys(url):
    await runner.review(url)
    report = json.loads((runner.OUT/runner.REPORT_NAME).read_text())
    expected = json.loads((runner.ROOT/'docs/data/factory-buildings.json').read_text())
    actual = report['render']['factoryBuildings']
    stacks = [s for s in expected['structures'] if s['kind']=='chimney']
    assert actual['chimneys'] == len(stacks)
    assert actual['chimneysWithMappedHeights'] == sum('mappedHeightFeet' in s for s in stacks)
    assert {s['id'] for s in actual['chimneyTops']} == {s['id'] for s in stacks}
    print(f"All {len(stacks)} mapped chimneys reached the renderer.", flush=True)


async def station(url):
    await runner.review(url)
    report=json.loads((runner.OUT/runner.REPORT_NAME).read_text())
    expected=json.loads((runner.ROOT/'docs/data/abbey-station-plan.json').read_text())
    assert report['render']['stationSupport']['ranges']==len(expected['supportingBuildings'])
    assert report['render']['stationStudy']['chimneys']==len(expected['chimneys'])
    print('Station and all 12 source-linked supporting volumes reached the renderer.', flush=True)


async def ink(url):
    await runner.review(url)
    report=json.loads((runner.OUT/runner.REPORT_NAME).read_text())
    expected=json.loads((runner.ROOT/'docs/data/factory-buildings.json').read_text())
    rendered=report['render']['factoryBuildings']
    assert rendered['ranges']==len(expected['buildings'])
    tops={s['id']:s['position'] for s in rendered['chimneyTops']}
    for stack in expected['structures']:
        if stack['siteId']==940 and stack['kind']=='chimney':
            assert tops[stack['id']]==[stack['x'],stack['height']+stack['baseHeight'],stack['z']]
    print('All factory ranges and three corrected ink-works chimney positions reached the renderer.', flush=True)


async def sawmill(url):
    await runner.review(url)
    report=json.loads((runner.OUT/runner.REPORT_NAME).read_text())
    expected=json.loads((runner.ROOT/'docs/data/factory-buildings.json').read_text())
    rendered=report['render']['factoryBuildings']
    assert rendered['ranges']==len(expected['buildings']) and rendered['siteRanges']['797']==16
    stack=next(s for s in expected['structures'] if s['siteId']==797 and s['kind']=='chimney')
    top=next(s['position'] for s in rendered['chimneyTops'] if s['id']==stack['id'])
    assert top==[stack['x'],stack['height']+stack['baseHeight'],stack['z']]
    print('All 16 mill/Towers ranges and the transferred boiler chimney reached the renderer.', flush=True)


async def oil_wharf(url):
    await runner.review(url)
    report=json.loads((runner.OUT/runner.REPORT_NAME).read_text())
    expected=json.loads((runner.ROOT/'docs/data/factory-buildings.json').read_text())
    rendered=report['render']['factoryBuildings']
    assert rendered['ranges']==len(expected['buildings']) and rendered['siteRanges']['9001']==10
    tanks={s['id']:s for s in rendered['tanks']}
    for s in expected['structures']:
        if s['siteId']==9001 and s['kind']=='tank':
            assert tanks[s['id']]=={'id':s['id'],'position':[s['x'],.1,s['z']],'radius':s['radius'],'height':s['height']}
    print('All 10 Oil Wharf/context ranges and five corrected tanks reached the renderer.', flush=True)


async def howards(url):
    await runner.review(url)
    report=json.loads((runner.OUT/runner.REPORT_NAME).read_text())
    expected=json.loads((runner.ROOT/'docs/data/factory-buildings.json').read_text())
    rendered=report['render']['factoryBuildings']
    assert rendered['ranges']==len(expected['buildings']) and rendered['siteRanges']['260']==86
    tops={s['id']:s['position'] for s in rendered['chimneyTops']}
    for stack in expected['structures']:
        if stack['siteId']==260:
            assert tops[stack['id']]==[stack['x'],stack['height']+stack['baseHeight'],stack['z']]
    print('All 86 Howards ranges and 18 corrected chimney positions reached the renderer.', flush=True)


async def sugar_house(url):
    await runner.review(url)
    report=json.loads((runner.OUT/runner.REPORT_NAME).read_text())
    expected=json.loads((runner.ROOT/'docs/data/factory-buildings.json').read_text())
    rendered=report['render']['factoryBuildings']
    count=sum(b['siteId']==964 for b in expected['buildings'])
    assert rendered['ranges']==len(expected['buildings']) and rendered['siteRanges']['964']==count
    stack=next(s for s in expected['structures'] if s['id']=='stack-964-1425-3049')
    top=next(s['position'] for s in rendered['chimneyTops'] if s['id']==stack['id'])
    assert top==[stack['x'],stack['height']+stack['baseHeight'],stack['z']]
    print(f'All {count} eastern Sugar House Lane ranges and the corrected cooperage chimney reached the renderer.', flush=True)


async def lascelles_ultramarine(url):
    await runner.review(url)
    report=json.loads((runner.OUT/runner.REPORT_NAME).read_text())
    expected=json.loads((runner.ROOT/'docs/data/factory-buildings.json').read_text())
    rendered=report['render']['factoryBuildings']
    assert rendered['ranges']==len(expected['buildings'])
    assert rendered['siteRanges']['565']==3 and rendered['siteRanges']['566']==4
    stack=next(s for s in expected['structures'] if s['id']=='stack-566-1203-1650')
    top=next(s['position'] for s in rendered['chimneyTops'] if s['id']==stack['id'])
    assert top==[stack['x'],stack['height']+stack['baseHeight'],stack['z']]
    print('All seven Lascelles/Ultramarine ranges, including the reassigned lean-to, and the mapped 60-foot chimney reached the renderer.',flush=True)


async def williams_asphalte(url):
    await runner.review(url)
    report=json.loads((runner.OUT/runner.REPORT_NAME).read_text())
    expected=json.loads((runner.ROOT/'docs/data/factory-buildings.json').read_text())
    rendered=report['render']['factoryBuildings']
    assert rendered['ranges']==len(expected['buildings'])
    assert rendered['siteRanges']['568']==18 and rendered['siteRanges']['566']==4
    tops={s['id']:s['position'] for s in rendered['chimneyTops']}
    for s in expected['structures']:
        if s['siteId']==568:assert tops[s['id']]==[s['x'],s['height']+s['baseHeight'],s['z']]
    print('Williams/Asphalte: all 18 ranges, reassigned Ultramarine lean-to and both corrected chimney positions reached the renderer.',flush=True)


async def three_mills(url):
    await runner.review(url)
    report=json.loads((runner.OUT/runner.REPORT_NAME).read_text())
    expected=json.loads((runner.ROOT/'docs/data/factory-buildings.json').read_text())
    rendered=report['render']['factoryBuildings']
    assert rendered['ranges']==len(expected['buildings']) and rendered['siteRanges']['419']==38
    tops={s['id']:s['position'] for s in rendered['chimneyTops']}
    stack=next(s for s in expected['structures'] if s['id']=='stack-419-1459-2756')
    assert tops[stack['id']]==[stack['x'],stack['height']+stack['baseHeight'],stack['z']]
    tanks={s['id']:s for s in rendered['tanks']}
    for tank in expected['structures']:
        if tank['siteId']==419 and tank['kind']=='tank':
            actual=tanks[tank['id']]
            assert actual['position']==[tank['x'],.1,tank['z']]
            assert actual['radius']==tank['radius'] and actual['height']==tank['height']
    print('Three Mills: 38 site ranges, corrected boiler chimney and all five fitted tanks reached the renderer.',flush=True)


async def kendrick_usher(url):
    await runner.review(url)
    report=json.loads((runner.OUT/runner.REPORT_NAME).read_text())
    expected=json.loads((runner.ROOT/'docs/data/factory-buildings.json').read_text())
    rendered=report['render']['factoryBuildings']
    assert rendered['ranges']==len(expected['buildings'])
    assert all(rendered['siteRanges'][str(site)]==count for site,count in [(569,2),(570,5),(571,2)])
    tops={s['id']:s['position'] for s in rendered['chimneyTops']}
    stack=next(s for s in expected['structures'] if s['id']=='stack-570-959-1000')
    assert tops[stack['id']]==[stack['x'],stack['height']+stack['baseHeight'],stack['z']]
    print('Kendrick/Usher: all nine ranges and corrected 40 ft chimney reached the renderer.',flush=True)


async def refinery_printing(url):
    await runner.review(url)
    report=json.loads((runner.OUT/runner.REPORT_NAME).read_text())
    expected=json.loads((runner.ROOT/'docs/data/factory-buildings.json').read_text())
    rendered=report['render']['factoryBuildings']
    assert rendered['ranges']==len(expected['buildings']) and rendered['siteRanges']['567']==18
    tops={s['id']:s['position'] for s in rendered['chimneyTops']}
    for s in expected['structures']:
        if s['siteId']==567:assert tops[s['id']]==[s['x'],s['height']+s['baseHeight'],s['z']]
    print('Refinery/printing: all 18 ranges and both corrected chimneys reached the renderer.',flush=True)


async def hunt_works(url):
    await runner.review(url)
    report=json.loads((runner.OUT/runner.REPORT_NAME).read_text())
    expected=json.loads((runner.ROOT/'docs/data/factory-buildings.json').read_text())
    rendered=report['render']['factoryBuildings']
    assert rendered['ranges']==len(expected['buildings']) and rendered['siteRanges']['564']==10
    tops={s['id']:s['position'] for s in rendered['chimneyTops']}
    stacks=[s for s in expected['structures'] if s['siteId']==564 and s['kind']=='chimney']
    assert len(stacks)==2
    for s in stacks:assert tops[s['id']]==[s['x'],s['height']+s['baseHeight'],s['z']]
    print('All ten Hunt ranges and two corrected chimneys reached the renderer.',flush=True)


async def bow_works(url):
    await runner.review(url)
    report=json.loads((runner.OUT/runner.REPORT_NAME).read_text())
    expected=json.loads((runner.ROOT/'docs/data/factory-buildings.json').read_text())
    rendered=report['render']['factoryBuildings']
    assert rendered['ranges']==len(expected['buildings']) and rendered['siteRanges']['254']==17
    tops={s['id']:s['position'] for s in rendered['chimneyTops']}
    stacks=[s for s in expected['structures'] if s['siteId']==254 and s['kind']=='chimney']
    assert len(stacks)==5
    for s in stacks:assert tops[s['id']]==[s['x'],s['height']+s['baseHeight'],s['z']]
    print('All 17 Bow Bridge ranges and five reviewed chimney positions reached the renderer.',flush=True)


async def abbey_west(url):
    await runner.review(url)
    report=json.loads((runner.OUT/runner.REPORT_NAME).read_text())
    expected=json.loads((runner.ROOT/'docs/data/factory-buildings.json').read_text())
    rendered=report['render']['factoryBuildings']
    assert rendered['ranges']==len(expected['buildings'])
    assert all(rendered['siteRanges'][str(site)]==count for site,count in [(256,5),(572,3),(573,8)])
    stack=next(s for s in expected['structures'] if s['id']=='stack-573-487-2965')
    top=next(s['position'] for s in rendered['chimneyTops'] if s['id']==stack['id'])
    assert top==[stack['x'],stack['height']+stack['baseHeight'],stack['z']]
    print('All 16 starch/tin-box/confectionery ranges and the corrected Hogarth chimney reached the renderer.',flush=True)


async def crystal_barber(url):
    await runner.review(url)
    report=json.loads((runner.OUT/runner.REPORT_NAME).read_text())
    expected=json.loads((runner.ROOT/'docs/data/factory-buildings.json').read_text())
    rendered=report['render']['factoryBuildings']
    assert rendered['ranges']==len(expected['buildings']) and rendered['siteRanges']['964']==40
    tops={s['id']:s['position'] for s in rendered['chimneyTops']}
    for stack in expected['structures']:
        if stack['siteId']==964 and stack['kind']=='chimney':
            assert tops[stack['id']]==[stack['x'],stack['height']+stack['baseHeight'],stack['z']]
    print('All 40 eastern ranges and three corrected chimney positions reached the renderer.',flush=True)


async def west_sugar(url):
    await runner.review(url)
    report=json.loads((runner.OUT/runner.REPORT_NAME).read_text())
    expected=json.loads((runner.ROOT/'docs/data/factory-buildings.json').read_text())
    rendered=report['render']['factoryBuildings']
    assert rendered['ranges']==len(expected['buildings']) and rendered['siteRanges']['947']==38
    assert rendered['siteRanges']['569']==2
    tops={s['id']:s['position'] for s in rendered['chimneyTops']}
    for stack in expected['structures']:
        if stack['siteId']==947:
            assert tops[stack['id']]==[stack['x'],stack['height']+stack['baseHeight'],stack['z']]
    print('All 38 western ranges, four corrected chimneys and two remaining Kendrick ranges reached the renderer.',flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', help='Review an already running local preview')
    parser.add_argument('--yards-only', action='store_true', help='Check the yard surfaces without repeating the atlas review')
    parser.add_argument('--goad-only', action='store_true', help='Check the current Goad factory refinement')
    parser.add_argument('--chimneys-only', action='store_true', help='Check the mapped factory chimney skyline')
    parser.add_argument('--gasworks-only', action='store_true', help='Check gasworks production stacks and context')
    parser.add_argument('--railway-only', action='store_true', help='Check the northern railway embankment and crossings')
    parser.add_argument('--housing-only', action='store_true', help='Review terraces, shared yards and street fronts')
    parser.add_argument('--millmeads-only', action='store_true', help='Review the mapped Mill Meads housing blocks')
    parser.add_argument('--completion-only', action='store_true', help='Review the northern railway connection and western industrial bank')
    parser.add_argument('--station-only', action='store_true', help='Review Abbey Mills plan and architectural refinement')
    parser.add_argument('--footprints-only', action='store_true', help='Review source footprint alignment and retained roof detail')
    parser.add_argument('--ink-only', action='store_true', help='Review grouped ink-works footprints, workshop row and chimney opening')
    parser.add_argument('--sawmill-only', action='store_true', help='Review Imperial mill compartments, Towers courtyard, timber yard and Cook’s Road')
    parser.add_argument('--oil-wharf-only', action='store_true', help='Review Oil Wharf stores, tank yard, Cook’s Road and neighbouring sawmill')
    parser.add_argument('--howards-only', action='store_true', help='Review City Mills / Howards departments and millrace')
    parser.add_argument('--sugar-house-only', action='store_true', help='Review Sugar House, cooperage, Winstone ranges and corrected lane access')
    parser.add_argument('--west-sugar-only', action='store_true', help='Review Hodson, Dane, western Winstone and Wildash footprints, roads and riverbank')
    parser.add_argument('--crystal-barber-only', action='store_true', help='Review Crystal Wharf, Barber, southern ink works and restored open yards')
    parser.add_argument('--abbey-west-only', action='store_true', help='Review starch, tin-box and confectionery factories and the Bow Bridge boundary')
    parser.add_argument('--bow-works-only', action='store_true', help='Review Bow Bridge bone and chemical works, direct traces, chimneys and Lea bank')
    parser.add_argument('--hunt-works-only', action='store_true', help='Review Hunt soap works, shared rooms, chimneys and riverbank')
    parser.add_argument('--lascelles-ultramarine-only', action='store_true', help='Review Lascelles and Ultramarine, map joins, chimney opening and lane')
    parser.add_argument('--software-gl', action='store_true', help='Use SwiftShader for review when the hardware graphics context is unavailable')
    parser.add_argument('--williams-asphalte-only', action='store_true', help='Review Williams wharf and French Asphalte footprint alignment')
    parser.add_argument('--three-mills-south-only', action='store_true', help='Review the southern Three Mills ranges and tanks')
    parser.add_argument('--three-mills-north-only', action='store_true', help='Review the northern Three Mills distillery and mapped plant')
    parser.add_argument('--kendrick-usher-only', action='store_true', help='Review both Kendrick works and Usher printing ink')
    parser.add_argument('--refinery-printing-only', action='store_true', help='Review the refinery, machinery depot and printing works')
    parser.add_argument('--view', help='Capture one named view from the selected review')
    args = parser.parse_args()
    runner.SOFTWARE_GL = args.software_gl
    if args.yards_only:
        runner.REPORT_NAME = 'factory-yards-checks.json'
        runner.VIEWS = {name: view for name, view in runner.VIEWS.items()
                        if name in ['factories-sugar-north', 'factories-howards-south', 'factories-west-ham-gas', 'factories-sawmill-yard', 'factories-sawmill-stacks']}
    if args.railway_only:
        runner.REPORT_NAME = 'great-eastern-checks.json'
        runner.VIEWS = {name:view for name,view in runner.VIEWS.items() if name.startswith('great-eastern-')}
    if args.goad_only:
        runner.REPORT_NAME = 'goad-refinement-checks.json'
        runner.VIEWS = {name:view for name,view in runner.VIEWS.items() if name in ['factories-sawmill-yard','factories-sawmill-stacks','factories-old-lea','factories-soap-front','factories-sawmill-ranges','factories-jute']}
    action = runner.review if args.yards_only or args.railway_only else review
    if args.chimneys_only:
        runner.REPORT_NAME = 'factory-chimneys-checks.json'
        runner.VIEWS = {name:view for name,view in runner.VIEWS.items() if name in ['factories-city','factories-howards-south','factories-marshgate','factories-sugar-north','factories-sugar-south','factories-three-mills','factories-soap-front','factories-sawmill-ranges','factories-jute']}
        runner.VIEWS['chimney-crown'] = {'position':[-728,24,-326], 'target':[-732.359,18.628,-330.703], 'fov':55}
        action = chimneys
    if args.gasworks_only:
        runner.REPORT_NAME = 'gasworks-chimneys-checks.json'
        runner.VIEWS = {name:view for name,view in runner.VIEWS.items() if name in ['factories-bromley-production','factories-west-ham-gas','factories-bridge-regression']}
        runner.VIEWS['bromley-retort-houses'] = {'position':[-520,75,1360], 'target':[-340,12,1170], 'fov':60}
        runner.VIEWS['bromley-retort-roof'] = {'position':[-375,27,1190], 'target':[-386,17,1120], 'fov':60}
        action = chimneys
    if args.housing_only:
        runner.REPORT_NAME = 'housing-detail-checks.json'
        runner.VIEWS = {
            'housing-mill-meads': {'position':[-470,95,-100],'target':[-450,0,-300],'fov':60},
            'housing-gibbins-leet': {'position':[-670,170,-590],'target':[-410,0,-845],'fov':65},
            'housing-jute-mill': {'position':[-710,125,-490],'target':[-535,0,-650],'fov':60},
            'housing-gasworks': {'position':[-260,135,-210],'target':[-430,0,-410],'fov':60},
            'housing-livingstone': {'position':[-305,90,-220],'target':[-430,0,-335],'fov':60},
            'housing-north-west': {'position':[-360,150,-470],'target':[-380,0,-750],'fov':65},
            'housing-north-east': {'position':[150,180,-480],'target':[170,0,-760],'fov':65},
            'housing-east': {'position':[430,170,30],'target':[420,0,-230],'fov':65},
            'housing-western-approach': {'position':[-1040,145,690],'target':[-920,0,440],'fov':65},
        }
        import math
        homes=json.loads((runner.ROOT/'docs/data/housing-detail.json').read_text())
        row=next(r for r in homes['rows'] if r['id']=='os-row-1')
        def point(u,v,y):
            a=-math.radians(row['rotation'])
            return [row['x']+u*math.cos(a)-v*math.sin(a),y,row['z']+u*math.sin(a)+v*math.cos(a)]
        sign=row['frontSign']
        runner.VIEWS['housing-street-level']={'position':point(-12,sign*(row['depth']/2+4),1.7),'target':point(15,sign*row['depth']/2,3),'fov':68}
        runner.VIEWS['housing-back-yards']={'position':point(-26,-sign*(row['depth']/2+24),19),'target':point(1,-sign*(row['depth']/2+5),2),'fov':65}
        action = runner.review
    if args.millmeads_only:
        runner.REPORT_NAME = 'millmeads-housing-checks.json'
        runner.VIEWS = {
            'millmeads-housing-overview': {'position':[-565,135,-90],'target':[-480,0,-260],'fov':60},
            'millmeads-compact-blocks': {'position':[-578,58,-145],'target':[-515,0,-196],'fov':60},
            'millmeads-deep-plots': {'position':[-585,90,-235],'target':[-490,0,-280],'fov':60},
        }
        action = runner.review
    if args.completion_only:
        runner.REPORT_NAME='western-bank-railway-checks.json'
        runner.VIEWS={
            'woolwich-mainline-junction': {'position':[-150,160,-830],'target':[-370,0,-1030],'fov':65},
            'woolwich-northern-corridor': {'position':[180,150,-310],'target':[-80,0,-650],'fov':63},
            'western-bank-overview': {'position':[-1250,230,680],'target':[-975,0,130],'fov':62},
            'western-bow-works': {'position':[-970,100,400],'target':[-955,0,205],'fov':65},
            'western-bow-mills': {'position':[-1140,95,270],'target':[-1110,0,125],'fov':62},
            'western-three-mills': {'position':[-560,120,600],'target':[-715,0,405],'fov':62},
        }
        action=runner.review
    if args.footprints_only:
        runner.REPORT_NAME='factory-footprint-alignment-checks.json'
        runner.VIEWS={
            'footprints-ink-overhead': {'position':[-800,160,-240],'target':[-865,0,-344],'fov':60},
            'footprints-ink-lane': {'position':[-824,9,-328],'target':[-871,5,-324],'fov':65},
            'footprints-west-ham-gas': {'position':[-417,205,-82],'target':[-214,0,-345],'fov':62},
            'footprints-sawmill': {'position':[-1100,50,15],'target':[-1045,4,-45],'fov':58},
            'footprints-bromley': {'position':[-630,260,1440],'target':[-365,0,1100],'fov':65},
        }
        action=runner.review
    if args.station_only:
        runner.REPORT_NAME='abbey-station-alignment-checks.json'
        runner.VIEWS={
            'station-aligned-plan': {'position':[-181,180,0],'target':[-181,0,-10],'fov':55},
            'station-aligned-front': {'position':[-225,22,72],'target':[-181,17,-10],'fov':55},
            'station-aligned-boilers': {'position':[-125,30,-97],'target':[-181,12,-16],'fov':60},
            'station-aligned-bridge': {'position':[0,9.2,0],'target':[-182,15,-10],'fov':48},
            'station-support-site': {'position':[-230,225,45],'target':[-230,0,-25],'fov':55},
            'station-support-south': {'position':[-250,32,100],'target':[-184,5,27],'fov':60},
            'station-support-entrance': {'position':[-295,7,-112],'target':[-235,4,-35],'fov':65},
        }
        action=station
    if args.ink_only:
        runner.REPORT_NAME='ink-works-alignment-checks.json'
        runner.VIEWS={
            'ink-compound-plan': {'position':[-875,175,-345],'target':[-875,0,-346],'fov':55},
            'ink-lampblack-ranges': {'position':[-943,30,-322],'target':[-879,5,-365],'fov':62},
            'ink-workshop-row': {'position':[-868,18,-277],'target':[-848,4,-320],'fov':65},
            'ink-west-chimney-opening': {'position':[-913,31,-337],'target':[-908.2,5,-346.6],'fov':60},
        }
        action=ink
    if args.sawmill_only:
        runner.REPORT_NAME='sawmill-footprint-alignment-checks.json'
        runner.VIEWS={
            'sawmill-aligned-yard': {'position':[-1100,230,30],'target':[-1090,0,-75],'fov':60},
            'sawmill-aligned-plan': {'position':[-1045,140,-35],'target':[-1045,0,-42],'fov':52},
            'sawmill-aligned-workshops': {'position':[-1100,24,-75],'target':[-1052,7,-53],'fov':62},
            'sawmill-aligned-cooks-road': {'position':[-1087,6,-11],'target':[-1039,5,-16],'fov':60},
            'sawmill-aligned-towers': {'position':[-1125,48,-95],'target':[-1105,2,-138],'fov':58},
        }
        action=sawmill
    if args.oil_wharf_only:
        runner.REPORT_NAME='oil-wharf-alignment-checks.json'
        runner.VIEWS={
            'oil-wharf-plan': {'position':[-1163,225,-20],'target':[-1163,0,-30],'fov':55},
            'oil-wharf-tanks': {'position':[-1080,14,60],'target':[-1130,3,1],'fov':60},
            'oil-wharf-stores': {'position':[-1145,16,-48],'target':[-1190,3,-10],'fov':62},
            'oil-wharf-north': {'position':[-1165,55,-115],'target':[-1220,0,-62],'fov':65},
            'oil-wharf-road': {'position':[-1090,7,-30],'target':[-1150,4,-65],'fov':60},
            'oil-wharf-sawmill-road': {'position':[-1087,6,-11],'target':[-1039,5,-16],'fov':60},
        }
        action=oil_wharf
    if args.howards_only:
        runner.REPORT_NAME='howards-alignment-checks.json'
        runner.VIEWS={
            'howards-overview': {'position':[-810,240,-130],'target':[-727,0,-298],'fov':60},
            'howards-northern-works': {'position':[-746,115,-345],'target':[-746,0,-373],'fov':58},
            'howards-epsom-court': {'position':[-700,60,-270],'target':[-715,2,-328],'fov':60},
            'howards-quinine': {'position':[-640,55,-223],'target':[-695,5,-265],'fov':58},
            'howards-millrace': {'position':[-726,17,-220],'target':[-734,5,-270],'fov':60},
            'howards-mercurial': {'position':[-800,75,-210],'target':[-756,3,-240],'fov':60},
            'howards-southern-ranges': {'position':[-727,40,-133],'target':[-746,4,-204],'fov':58},
        }
        action=howards
    if args.sugar_house_only:
        runner.REPORT_NAME='sugar-house-alignment-checks.json'
        runner.VIEWS={
            'sugar-house-aligned-plan': {'position':[-710,170,0],'target':[-690,0,-12],'fov':58},
            'sugar-house-warehouse': {'position':[-706,24,-17],'target':[-653,11,-57],'fov':58},
            'sugar-house-cooperage': {'position':[-614,57,-5],'target':[-677,3,-38],'fov':62},
            'sugar-house-chimney-opening': {'position':[-684,36,-30],'target':[-698,3,-44],'fov':48},
            'sugar-house-winstone': {'position':[-706,65,98],'target':[-688,3,28],'fov':58},
            'sugar-house-works-passage': {'position':[-718,7,71],'target':[-668,4,48],'fov':64},
        }
        action=sugar_house
    if args.west_sugar_only:
        runner.REPORT_NAME='west-sugar-alignment-checks.json'
        runner.VIEWS={
            'west-sugar-plan': {'position':[-754,245,30],'target':[-748,0,-8],'fov':59},
            'west-sugar-hodson': {'position':[-684,80,-81],'target':[-747,4,-80],'fov':60},
            'west-sugar-river': {'position':[-803,40,-65],'target':[-762,4,-43],'fov':60},
            'west-sugar-dane': {'position':[-706,48,12],'target':[-754,3,-3],'fov':60},
            'west-sugar-winstone': {'position':[-704,72,78],'target':[-754,4,35],'fov':60},
            'west-sugar-wildash': {'position':[-695,62,146],'target':[-742,3,88],'fov':60},
            'west-sugar-lane': {'position':[-722,8,-82],'target':[-738,4,-48],'fov':62},
        }
        action=west_sugar
    if args.crystal_barber_only:
        runner.REPORT_NAME='crystal-barber-alignment-checks.json'
        runner.VIEWS={
            'crystal-plan': {'position':[-684,110,-105],'target':[-681,0,-112],'fov':60},
            'crystal-oblique': {'position':[-711,42,-70],'target':[-677,4,-117],'fov':60},
            'crystal-open-yard': {'position':[-699,8,-106],'target':[-655,3,-111],'fov':60},
            'crystal-dane-chimney': {'position':[-662,27,-104],'target':[-662,8,-120],'fov':55},
            'barber-plan': {'position':[-650,95,10],'target':[-648,0,-2],'fov':58},
            'barber-chimney': {'position':[-618,30,9],'target':[-632,3,0],'fov':50},
            'southern-ink-courtyard': {'position':[-610,48,53],'target':[-643,3,19],'fov':60},
        }
        action=crystal_barber
    if args.abbey_west_only:
        runner.REPORT_NAME='abbey-west-alignment-checks.json'
        runner.VIEWS={
            'abbey-west-plan': {'position':[-844,165,17],'target':[-844,0,12],'fov':59},
            'abbey-west-starch': {'position':[-786,50,-56],'target':[-817,4,-24],'fov':58},
            'abbey-west-high-street': {'position':[-863,11,-35],'target':[-829,5,-33],'fov':62},
            'abbey-west-tin-box': {'position':[-900,46,54],'target':[-868,3,30],'fov':58},
            'abbey-west-hogarth': {'position':[-879,65,62],'target':[-830,4,15],'fov':58},
            'abbey-west-chimney': {'position':[-854,33,39],'target':[-833,6,24],'fov':54},
            'abbey-west-bow-boundary': {'position':[-825,65,103],'target':[-832,3,53],'fov':58},
        }
        action=abbey_west
    if args.bow_works_only:
        runner.REPORT_NAME='bow-works-alignment-checks.json'
        runner.VIEWS={
            'bow-works-plan': {'position':[-814,230,132],'target':[-811,0,130],'fov':60},
            'bow-works-mill': {'position':[-888,68,105],'target':[-845,4,70],'fov':58},
            'bow-works-process': {'position':[-765,80,82],'target':[-817,5,105],'fov':60},
            'bow-works-retorts': {'position':[-841,38,124],'target':[-819,7,105],'fov':58},
            'bow-works-manure': {'position':[-726,65,169],'target':[-777,4,177],'fov':58},
            'bow-works-boiling': {'position':[-725,48,219],'target':[-765,4,207],'fov':58},
            'bow-works-riverbank': {'position':[-841,25,160],'target':[-799,5,150],'fov':62},
        }
        action=bow_works
    if args.hunt_works_only:
        runner.REPORT_NAME='hunt-works-alignment-checks.json'
        runner.VIEWS={
            'hunt-works-plan': {'position':[-752,135,244],'target':[-751,0,239],'fov':58},
            'hunt-works-process': {'position':[-703,48,267],'target':[-757,4,225],'fov':58},
            'hunt-works-furnaces': {'position':[-808,27,252],'target':[-777,4,227],'fov':58},
            'hunt-works-boilers': {'position':[-697,33,249],'target':[-739,7,235],'fov':56},
            'hunt-works-stables': {'position':[-711,19,301],'target':[-725,4,265],'fov':58},
            'hunt-works-bow-boundary': {'position':[-736,35,183],'target':[-762,4,208],'fov':60},
        }
        action=hunt_works
    if args.lascelles_ultramarine_only:
        runner.REPORT_NAME='lascelles-ultramarine-alignment-checks.json'
        runner.VIEWS={
            'lascelles-ultramarine-plan': {'position':[-645,170,223],'target':[-645,0,215],'fov':58},
            'lascelles-factory': {'position':[-700,28,265],'target':[-676,4,224],'fov':58},
            'lascelles-lane': {'position':[-679,18,261],'target':[-651,4,212],'fov':58},
            'ultramarine-process': {'position':[-578,40,244],'target':[-617,4,204],'fov':60},
            'ultramarine-chimney': {'position':[-603,29,253],'target':[-624,7,222],'fov':56},
            'ultramarine-williams-boundary': {'position':[-632,33,155],'target':[-627,4,198],'fov':62},
        }
        action=lascelles_ultramarine
    if args.williams_asphalte_only:
        runner.REPORT_NAME='williams-asphalte-alignment-checks.json'
        runner.VIEWS={
            'asphalte-plan': {'position':[-636,125,115],'target':[-636,0,110],'fov':58},
            'asphalte-process': {'position':[-669,32,157],'target':[-629,5,111],'fov':60},
            'asphalte-boilers': {'position':[-564,27,120],'target':[-606,6,97],'fov':58},
            'williams-wharf-plan': {'position':[-636,135,173],'target':[-636,0,170],'fov':58},
            'williams-wharf-river': {'position':[-560,25,195],'target':[-620,4,173],'fov':62},
            'williams-ultramarine-boundary': {'position':[-664,29,155],'target':[-632,4,191],'fov':62},
        }
        action=williams_asphalte
    if args.refinery_printing_only:
        runner.REPORT_NAME='refinery-printing-alignment-checks.json'
        runner.VIEWS={
            'refinery-printing-plan': {'position':[-672,145,74],'target':[-672,0,68],'fov':58},
            'printing-works-frontage': {'position':[-723,21,100],'target':[-702,4,79],'fov':60},
            'printing-lane-narrowing': {'position':[-719,5,67],'target':[-711,3,88],'fov':66},
            'machinery-depot-court': {'position':[-691,28,62],'target':[-667,4,89],'fov':62},
            'refinery-oil-and-tar': {'position':[-608,25,98],'target':[-640,4,75],'fov':62},
            'refinery-northern-storage': {'position':[-625,25,65],'target':[-641,3,36],'fov':62},
        }
        action=refinery_printing
    if args.kendrick_usher_only:
        runner.REPORT_NAME='kendrick-usher-alignment-checks.json'
        runner.VIEWS={
            'kendrick-usher-plan': {'position':[-717,125,160],'target':[-717,0,154],'fov':58},
            'kendrick-north-yard': {'position':[-731,24,151],'target':[-726,3,120],'fov':62},
            'kendrick-north-lane': {'position':[-694,9,127],'target':[-706,3,106],'fov':66},
            'usher-engine-court': {'position':[-731,22,168],'target':[-711,4,148],'fov':62},
            'usher-lane-frontage': {'position':[-674,20,143],'target':[-703,4,147],'fov':60},
            'kendrick-south-range': {'position':[-703,24,207],'target':[-704,4,184],'fov':64},
        }
        action=kendrick_usher
    if args.three_mills_north_only:
        runner.REPORT_NAME='three-mills-north-alignment-checks.json'
        runner.VIEWS={
            'three-mills-north-plan': {'position':[-487,155,377],'target':[-487,0,370],'fov':62},
            'three-mills-dwellings': {'position':[-535,24,329],'target':[-551,5,356],'fov':62},
            'three-mills-engine-court': {'position':[-517,28,400],'target':[-517,5,369],'fov':62},
            'three-mills-northern-tanks': {'position':[-445,23,308],'target':[-463,5,335],'fov':62},
            'three-mills-eastern-rooms': {'position':[-411,27,377],'target':[-452,7,356],'fov':62},
            'three-mills-works-passage': {'position':[-494,7,380],'target':[-533,5,389],'fov':68},
        }
        action=three_mills
    if args.three_mills_south_only:
        runner.REPORT_NAME='three-mills-south-alignment-checks.json'
        runner.VIEWS={
            'three-mills-south-plan': {'position':[-480,140,454],'target':[-480,0,437],'fov':62},
            'three-mills-south-tanks': {'position':[-479,24,495],'target':[-500,5,449],'fov':64},
            'three-mills-south-court': {'position':[-440,17,463],'target':[-463,5,420],'fov':68},
        }
        action=three_mills
    if args.view:
        if args.view not in runner.VIEWS:parser.error('Unknown selected view: '+args.view)
        runner.VIEWS={args.view:runner.VIEWS[args.view]}
        runner.REPORT_NAME=args.view+'-checks.json'
        action=three_mills if (args.three_mills_north_only or args.three_mills_south_only) else runner.review
    if args.url:
        asyncio.run(action(args.url.rstrip('/')))
        raise SystemExit
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(runner.QuietHandler, directory=str(runner.ROOT/'docs')))
    Thread(target=server.serve_forever, daemon=True).start()
    try:
        asyncio.run(action(f'http://127.0.0.1:{server.server_port}'))
    finally:
        server.shutdown()
