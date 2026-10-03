#!/usr/bin/env python3
"""Render the 1900 ground trial and its preserved scene baseline."""
import argparse
import asyncio
import base64
import json
from pathlib import Path

from playwright.async_api import async_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'scenes/channelsea-sewer-panorama/review'
VIEWS={
    'elevation-mill-mead': {'position':[-290,110,480], 'target':[-285,0,260], 'fov':58},
    'elevation-northwest': {'position':[-440,100,-30], 'target':[-270,0,-230], 'fov':60},
    'elevation-bridge-south': {'position':[0,9.2,0], 'target':[-60,0,200], 'fov':60},
    'elevation-bridge-north': {'position':[0,9.2,0], 'target':[-65,2,-180], 'fov':60},
    'elevation-plaistow-west': {'position':[-120,100,815], 'target':[65,-.5,650], 'fov':60},
    'elevation-plaistow-east': {'position':[540,95,775], 'target':[412,-.5,520], 'fov':60},
    'elevation-sewer-south': {'position':[3,5,65], 'target':[0,4,0], 'fov':60},
    'elevation-sewer-north': {'position':[-12,7,-30], 'target':[0,4,0], 'fov':85},
    'elevation-drainage-overview': {'position':[440,65,665], 'target':[420,-.5,580], 'fov':65},
    'elevation-drainage-close': {'position':[417,4,596], 'target':[437,-1,580], 'fov':70},
    'elevation-manor-road': {'position':[315,36,641], 'target':[272,0,555], 'fov':65},
    'elevation-manor-close': {'position':[292,4,595], 'target':[277,-.25,575], 'fov':68},
}


async def review(url, quick=False, sewer_only=False, drainage_only=False, manor_only=False):
    OUT.mkdir(parents=True,exist_ok=True)
    reports={}
    views={key:value for key,value in VIEWS.items() if ('manor' in key if manor_only else 'drainage' in key if drainage_only else 'sewer' in key if sewer_only else not quick or 'plaistow' in key)}
    quick=quick or sewer_only or drainage_only or manor_only
    async with async_playwright() as p:
        print('Launching terrain review browser',flush=True)
        browser=await p.chromium.launch(headless=True,args=['--no-sandbox','--enable-webgl',
            '--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage'])
        for epoch in ['1900','baseline']:
            print(f'Loading terrain scene ({epoch})',flush=True)
            page=await browser.new_page(viewport={'width':960 if quick else 1440,'height':600 if quick else 900},device_scale_factor=1)
            errors=[]
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
            await page.goto(f'{url}/?river-review&quality=full&terrainEpoch={epoch}&mainLandscape=baseline')
            await page.wait_for_function('Boolean(window.riverNetworkReview)',timeout=180000)
            print(f'Terrain scene ready ({epoch})',flush=True)
            for name,view in views.items():
                if epoch=='baseline' and 'bridge' in name:
                    continue
                capture=await page.evaluate('(view)=>riverNetworkReview(view)',view)
                (OUT/f'{name}-{epoch}.png').write_bytes(base64.b64decode(capture.split(',')[1]))
                print(f'Captured {name} ({epoch})',flush=True)
            render=await page.evaluate('window.panoramaReview')
            sewer=render['sewerCrossing']
            assert sewer['bounds']['enclosure']['count']>=2
            assert sewer['bounds']['abutment']['count']==2
            assert sewer['bounds']['enclosure']['max'][1]-sewer['bounds']['enclosure']['min'][1]>2
            assert abs(sewer['bounds']['enclosure']['max'][1]-(sewer['deckHeight']-.5))<.01
            if epoch=='1900':
                assert render['elevation']['epoch']=='1900'
                assert render['elevation']['coreVerticesChanged']>0
                assert render['elevation']['networkVerticesChanged']>0
                assert not render['elevation']['floodReady']
                drainage=render['elevation']['drainage']
                assert drainage['waterTriangles']>0 and drainage['modifiedGridNodes']>0
                assert not drainage['tideConnected'] and not drainage['floodReady']
                # High tide remains a separate, bounded illustrative state.
                await page.locator('#tide-level').evaluate("e=>{e.value=e.max;e.dispatchEvent(new Event('input',{bubbles:true}));}")
                high_view='elevation-drainage-close' if drainage_only else 'elevation-bridge-south'
                capture=await page.evaluate('(view)=>riverNetworkReview(view)',VIEWS[high_view])
                name='drainage-high-tide-1900.png' if drainage_only else 'elevation-high-tide-1900.png'
                (OUT/name).write_bytes(base64.b64decode(capture.split(',')[1]))
                after_tide=await page.evaluate('window.panoramaReview')
                assert after_tide['elevation']['drainage']==drainage,'River tide moved isolated drainage'
            else:
                assert render.get('elevation') is None
            assert not errors,errors
            reports[epoch]={'errors':errors,'render':render}
            await page.close()
        # Buildings and joined railways keep their previous metrics. Gardens
        # are allowed to follow the revised ground elevations.
        before,after=reports['baseline']['render'],reports['1900']['render']
        for key in ['factoryBuildings','stationStudy','stationSupport','railConnections','greatEastern','infrastructure','sewerCrossing']:
            assert before.get(key)==after.get(key),f'{key} unexpectedly changed'
        await browser.close()
    report={'status':'PASS','views':views,'comparisons':reports,
            'checks':['1900 overlay active','baseline mode preserved',f'{len(views)} landscape views',
                      'sewer enclosure and abutments present and aligned to deck in both epochs',
                      'isolated drainage unchanged by river tide','high tide view','building and railway diagnostics unchanged','no browser/shader errors']}
    report_name='manor-road-checks.json' if manor_only else 'historic-drainage-checks.json' if drainage_only else 'sewer-crossing-checks.json' if sewer_only else 'historic-elevation-checks.json'
    (OUT/report_name).write_text(json.dumps(report,indent=2)+'\n')
    print('Historic terrain browser checks passed.',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--url',default='http://127.0.0.1:4175')
    parser.add_argument('--quick',action='store_true',help='Review the two expanded ground areas at 960x600; retains full scene geometry, high tide and baseline diagnostics')
    parser.add_argument('--sewer-only',action='store_true',help='Review the crossing from both river sides in both terrain modes, with full geometry')
    parser.add_argument('--drainage-only',action='store_true',help='Review the mapped Plaistow drain, terrain cuts and independent water level')
    parser.add_argument('--connections-only',action='store_true',help='Review the standalone drainage connection scenarios and mobile controls')
    parser.add_argument('--manor-only',action='store_true',help='Review restored Manor Road and adjoining railway in both terrain modes')
    parser.add_argument('--flood-only',action='store_true',help='Review the flood simulator, comparisons, export and mobile controls')
    parser.add_argument('--landscape-flood-only',action='store_true',help='Review connected flooding on the actual 3D landscape')
    parser.add_argument('--region-only',action='store_true',help='Review regional Lower Lea coverage and terrain preview')
    parser.add_argument('--river-system-only',action='store_true',help='Review the expanded river system in the main scene')
    parser.add_argument('--river-banks-only',action='store_true',help='Review the three close bank views and mobile river explorer')
    parser.add_argument('--main-landscape-only',action='store_true',help='Review regional marsh levels in the main industrial reconstruction')
    args=parser.parse_args()
    if args.main_landscape_only:
        from review_main_landscape import review_main_landscape
        asyncio.run(review_main_landscape(args.url,args.quick))
    elif args.river_system_only or args.river_banks_only:
        from review_river_system import review_river_system
        asyncio.run(review_river_system(args.url,banks_only=args.river_banks_only))
    elif args.region_only:
        from review_lower_lea_region import review_lower_lea_region
        asyncio.run(review_lower_lea_region(args.url))
    elif args.landscape_flood_only:
        from review_landscape_flood import review_landscape_flood
        asyncio.run(review_landscape_flood(args.url))
    elif args.flood_only:
        from review_flood_demo import review_flood_demo
        asyncio.run(review_flood_demo(args.url))
    elif args.connections_only:
        from review_drainage_connections import review_connections
        asyncio.run(review_connections(args.url))
    else:
        asyncio.run(review(args.url,args.quick,args.sewer_only,args.drainage_only,args.manor_only))
