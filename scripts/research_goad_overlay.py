"""Read-only navigation of the public Layers of London Goad overlay.

Captures are research references, never runtime site assets. Each sheet's
printed date takes precedence over the viewer's broad '1887' layer label.
"""
import argparse
import asyncio
import json
from pathlib import Path
from pyproj import Transformer
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'reference/factory-building-survey/layers-of-london'
URL = 'https://www.layersoflondon.org/map/overlays/goad-1887'
TO_LONLAT = Transformer.from_crs(27700, 4326, always_xy=True)

async def run(all_sites=False):
    OUT.mkdir(parents=True, exist_ok=True)
    data = json.loads((ROOT/'docs/data/factory-buildings.json').read_text())
    visits = []
    for site in data['sites']:
        if not all_sites and site['id'] not in (796, 797):
            continue
        rows = [b for b in data['buildings'] if b['siteId'] == site['id']]
        visits.append({'id': str(site['id']), 'name': site['name'],
            'x': sum(b['x'] for b in rows)/len(rows),
            'z': sum(b['z'] for b in rows)/len(rows)})
    visits.append({'id': 'ritchie-jute', 'name': 'Ritchie & Sons, London Spinning Mills', 'x': -610, 'z': -750})
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
        page = await browser.new_page(viewport={'width': 1600, 'height': 1200})
        await page.goto(URL, wait_until='domcontentloaded', timeout=60000)
        await page.get_by_text('Use this overlay', exact=True).click()
        await page.get_by_text('Close tray', exact=True).click()
        await page.get_by_text('Hide pins', exact=True).click()
        await page.wait_for_function('window.store?.mapViewport?.deckRef?.deck')
        for site in visits:
            longitude, latitude = TO_LONLAT.transform(538900+site['x'], 183209-site['z'])
            await page.evaluate('p=>store.mapViewport.setCenter({coordinates:[p.longitude,p.latitude],zoom:18})',
                                {'longitude': longitude, 'latitude': latitude})
            await page.wait_for_timeout(6500)
            state = await page.evaluate('({longitude:store.mapViewport.deckRef.deck.props.viewState.longitude,latitude:store.mapViewport.deckRef.deck.props.viewState.latitude,zoom:store.mapViewport.deckRef.deck.props.viewState.zoom})')
            assert abs(state['longitude']-longitude)<.0001 and state['zoom']==18, state
            await page.screenshot(path=str(OUT/f"site-{site['id']}.png"))
            site.update({'longitude': longitude, 'latitude': latitude, 'zoom': 18, 'verifiedViewport': state})
            print(f"Captured {site['id']}: {site['name']}", flush=True)
        (OUT/'navigation.json').write_text(json.dumps({'url': URL, 'visits': visits,
            'dateCaution': 'Viewer layer label is not the date of each constituent sheet.'}, indent=2)+'\n')
        await browser.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--all-sites', action='store_true')
    asyncio.run(run(parser.parse_args().all_sites))
