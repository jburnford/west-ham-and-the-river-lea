"""Browser views, dry holds, tide offsets and small-screen coal fleet review."""
import argparse
import asyncio
import base64
import json
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'scenes/channelsea-sewer-panorama/review/coal-traffic'


async def review(args):
    OUT.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=[
            '--no-sandbox', '--enable-webgl', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'])
        page = await browser.new_page(viewport={'width': 1600, 'height': 1000})
        page.set_default_timeout(90000)
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
        detail_query = '&river-review=1' if args.details else ''
        await page.goto(f'{args.url}/?quality={args.quality}&view=coal-transfer{detail_query}')
        await page.wait_for_function('window.panoramaReview?.ready && !panoramaReview.tweening', timeout=300000)
        print('Coal scene built.', flush=True)
        await page.add_style_tag(content='.view-top,.view-bottom {visibility:hidden !important}')
        views = ['coal-whipping', 'coal-lea-barges'] if args.details else ['coal-transfer'] if args.first else ['coal-transfer', 'coal-whipping', 'coal-colliers', 'coal-lighter-tow', 'coal-lea-barges', 'coal-empty-barge']
        snapshots = {}
        for view in views:
            await page.locator('#destination').select_option(view)
            await page.wait_for_function('!panoramaReview.tweening')
            await page.screenshot(path=OUT/f'{view}-{args.quality}.png', animations='disabled', timeout=120000)
            diagnostic = await page.evaluate('panoramaReview')
            assert diagnostic['coalTraffic']['vessels'] == 12
            assert diagnostic['coalTraffic']['collier'] == 2
            assert diagnostic['reflection']['excludedVesselHolds'] == 24
            snapshots[view] = {k: diagnostic[k] for k in ['camera', 'triangles', 'drawCalls', 'coalTraffic', 'quality']}
            print(f'{view}: {diagnostic["triangles"]} visible triangles, {diagnostic["drawCalls"]} calls', flush=True)
        if args.details:
            # Native one-frame render through the existing camera review hook:
            # inspect bodies and hands without rebuilding the surrounding district.
            data_url = await page.evaluate('riverNetworkReview', {
                'position': [280, 3.5, 2631], 'target': [284.5, 2.7, 2637.7], 'fov': 42})
            (OUT/f'worker-detail-{args.quality}.png').write_bytes(base64.b64decode(data_url.split(',', 1)[1]))
        if not args.first and not args.fleet_only and not args.details:
            await page.locator('#destination').select_option('coal-transfer')
            await page.wait_for_function('!panoramaReview.tweening', timeout=300000)
            await page.locator('#tide-level').evaluate("el => { el.value = '100'; el.dispatchEvent(new Event('input', {bubbles: true})); }")
            diagnostic = await page.evaluate('panoramaReview')
            lift = diagnostic['tide']['high'] - diagnostic['tide']['low']
            assert diagnostic['tideObjects']['bargeOffsets']
            assert all(abs(y-lift) < 1e-6 for y in diagnostic['tideObjects']['bargeOffsets'])
            assert diagnostic['coalTraffic']['placements'][-1]['water'] == 'retained'
            await page.screenshot(path=OUT/f'coal-transfer-high-tide-{args.quality}.png', animations='disabled', timeout=120000)
            await page.locator('#tide-level').evaluate("el => { el.value = '0'; el.dispatchEvent(new Event('input', {bubbles: true})); }")
            await page.locator('#destination').select_option('pumping-station')
            await page.wait_for_function('!panoramaReview.tweening', timeout=300000)
            await page.screenshot(path=OUT/f'abbey-mills-regression-{args.quality}.png', animations='disabled', timeout=120000)
            await page.set_viewport_size({'width': 390, 'height': 844})
            await page.locator('#destination').select_option('coal-transfer')
            await page.wait_for_function('!panoramaReview.tweening', timeout=300000)
            await page.screenshot(path=OUT/f'coal-transfer-narrow-{args.quality}.png', animations='disabled', timeout=120000)
            assert await page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        assert not errors, errors
        report_name = f'review-details-{args.quality}.json' if args.details else f'review-{args.quality}.json'
        (OUT/report_name).write_text(json.dumps({'errors': errors, 'views': snapshots,
            'checks': ['12 source-informed vessels', 'dry hatch masks', 'destination views'] +
            (['native worker close view'] if args.details else [] if args.first or args.fleet_only else ['high tide floating offsets', 'Abbey Mills view', 'narrow viewport'])}, indent=2)+'\n')
        await browser.close()
    print('Coal fleet browser review passed.', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='http://127.0.0.1:4173')
    parser.add_argument('--quality', default='lite', choices=['full', 'lite'])
    parser.add_argument('--first', action='store_true')
    parser.add_argument('--fleet-only', action='store_true', help='Review all six fleet views without whole-district regression captures')
    parser.add_argument('--details', action='store_true', help='Review working figures and coal loads at close range')
    asyncio.run(review(parser.parse_args()))
