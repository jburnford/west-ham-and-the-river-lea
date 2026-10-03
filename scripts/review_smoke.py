"""Load the main scene headlessly and record its diagnostic snapshot.

Used to prove that a refactor changed nothing: run it before and after, then
diff the two JSON files. Volatile fields (timings, revision hashes) are dropped
so only scene content remains. Start the site first:

    python3 -m http.server 4173 --bind 127.0.0.1 --directory docs
    python3 scripts/review_smoke.py before            # writes review/smoke-before.json and .png
    ... make changes ...
    python3 scripts/review_smoke.py after --compare before
"""
import asyncio
import json
import sys
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'scenes/channelsea-sewer-panorama/review'
# Timings, hashes and asynchronous texture-download counters are not scene content.
VOLATILE = {'revision', 'tweening', 'tide', 'loadedDetailTiles', 'loading'}


def strip(value):
    if isinstance(value, dict):
        return {k: strip(v) for k, v in sorted(value.items()) if k not in VOLATILE}
    if isinstance(value, list):
        return [strip(v) for v in value]
    if isinstance(value, float):
        return round(value, 4)
    return value


async def snapshot(label, url, quality):
    REVIEW.mkdir(exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=[
            '--no-sandbox', '--enable-webgl', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'])
        page = await browser.new_page(viewport={'width': 1280, 'height': 800})
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
        await page.goto(f'{url}/?quality={quality}')
        await page.wait_for_function('window.panoramaReview?.ready === true', timeout=600000)
        # Let the arrival tween settle so the camera pose is deterministic.
        await page.wait_for_function('window.panoramaReview?.tweening === false', timeout=60000)
        review = strip(await page.evaluate('window.panoramaReview'))
        review['pageErrors'] = errors
        out = REVIEW / f'smoke-{label}.json'
        out.write_text(json.dumps(review, indent=1, sort_keys=True))
        # Whole-viewport capture with CSS animations frozen: the canvas fade-in kept the
        # element-stability wait from ever settling under the software renderer.
        try:
            await page.screenshot(path=REVIEW / f'smoke-{label}.png', animations='disabled', timeout=120000)
        except Exception as error:  # the JSON snapshot is the comparison; the image is a courtesy
            print(f'screenshot skipped: {str(error).splitlines()[0]}')
        await browser.close()
    print(f'{label}: ready, {len(errors)} page errors, {review.get("triangles")} triangles, {review.get("drawCalls")} draw calls → {out.relative_to(ROOT)}')
    return review


def compare(a, b):
    def walk(x, y, path=''):
        if isinstance(x, dict) and isinstance(y, dict):
            for k in sorted(set(x) | set(y)):
                yield from walk(x.get(k), y.get(k), f'{path}.{k}')
        elif x != y:
            yield path, x, y
    diffs = list(walk(a, b))
    for path, x, y in diffs[:40]:
        print(f'  {path}: {json.dumps(x)[:80]} → {json.dumps(y)[:80]}')
    return diffs


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    label = args[0] if args else 'smoke'
    url = next((a.split('=', 1)[1] for a in sys.argv if a.startswith('--url=')), 'http://127.0.0.1:4173')
    quality = next((a.split('=', 1)[1] for a in sys.argv if a.startswith('--quality=')), 'full')
    review = asyncio.run(snapshot(label, url, quality))
    if review['pageErrors']:
        print('Page errors:\n  ' + '\n  '.join(review['pageErrors']))
    if '--compare' in sys.argv:
        other = sys.argv[sys.argv.index('--compare') + 1]
        before = json.loads((REVIEW / f'smoke-{other}.json').read_text())
        diffs = compare(before, review)
        print(f'{len(diffs)} differences against {other}')
        sys.exit(1 if diffs or review['pageErrors'] else 0)
    sys.exit(1 if review['pageErrors'] else 0)


if __name__ == '__main__':
    main()
