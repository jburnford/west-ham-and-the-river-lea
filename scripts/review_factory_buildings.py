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
    parser.add_argument('--view', help='Capture one named view from the selected review')
    args = parser.parse_args()
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
    if args.view:
        if args.view not in runner.VIEWS:parser.error('Unknown selected view: '+args.view)
        runner.VIEWS={args.view:runner.VIEWS[args.view]}
        runner.REPORT_NAME=args.view+'-checks.json'
        action=runner.review
    if args.url:
        asyncio.run(action(args.url.rstrip('/')))
        raise SystemExit
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(runner.QuietHandler, directory=str(runner.ROOT/'docs')))
    Thread(target=server.serve_forever, daemon=True).start()
    try:
        asyncio.run(action(f'http://127.0.0.1:{server.server_port}'))
    finally:
        server.shutdown()
