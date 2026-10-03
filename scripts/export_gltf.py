"""Export the assembled 3D scene to binary glTF, one layer per file.

The scene is built by the browser, where the procedural textures and geometry
exist, so this drives headless Chromium against the local site with ?export=1.
app.js tags everything it adds to the scene with a layer name; this script lists
the layers with their triangle counts and writes the requested ones to
exports/gltf/<layer>.glb, then checks each file's structure and records the
scene origin in the glTF asset extras so the model can be placed in BNG.

    python3 -m http.server 4173 --bind 127.0.0.1 --directory docs
    python3 scripts/export_gltf.py --list
    python3 scripts/export_gltf.py factory-buildings housing
    python3 scripts/export_gltf.py --all --quality lite
"""
import asyncio
import base64
import json
import struct
import sys
import time
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'exports/gltf'
SLICE = 24 * 1024 * 1024


def arg(name, default=None):
    return next((a.split('=', 1)[1] for a in sys.argv if a.startswith(f'--{name}=')), default)


def validate_and_tag(path, origin, layer, revision):
    """Check the GLB container and write the origin into asset.extras."""
    data = bytearray(path.read_bytes())
    magic, version, length = struct.unpack_from('<4sII', data, 0)
    assert magic == b'glTF' and version == 2, (magic, version)
    assert length == len(data), (length, len(data))
    json_length, json_type = struct.unpack_from('<II', data, 12)
    assert json_type == 0x4E4F534A, json_type
    gltf = json.loads(bytes(data[20:20 + json_length]).decode())
    gltf.setdefault('asset', {})['extras'] = {
        'origin': origin, 'layer': layer, 'sceneRevision': revision,
        'axes': 'x east, y up, z south; metres from the origin (glTF Y-up)',
        'placement': 'easting = origin.easting + x; northing = origin.northing - z',
        'source': 'West Ham and the River Lea reconstruction; interpretive, see repository evidence notes',
    }
    body = json.dumps(gltf, separators=(',', ':')).encode()
    body += b' ' * (-len(body) % 4)
    rest = data[20 + json_length:]
    out = bytearray(struct.pack('<4sII', b'glTF', 2, 12 + 8 + len(body) + len(rest)))
    out += struct.pack('<II', len(body), json_type) + body + rest
    path.write_bytes(out)
    stats = {k: len(gltf.get(k, [])) for k in ('meshes', 'accessors', 'materials', 'textures', 'images', 'nodes')}
    bin_length = struct.unpack_from('<I', rest, 0)[0] if len(rest) >= 8 else 0
    stats['binaryBytes'] = bin_length
    return stats


async def main():
    url = arg('url', 'http://127.0.0.1:4173')
    quality = arg('quality', 'full')
    wanted = [a for a in sys.argv[1:] if not a.startswith('--')]
    OUT.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=[
            '--no-sandbox', '--enable-webgl', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'])
        page = await browser.new_page(viewport={'width': 1280, 'height': 800})
        page.set_default_timeout(900000)
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
        await page.goto(f'{url}/?export=1&quality={quality}')
        await page.wait_for_function('window.panoramaReview?.ready === true && Boolean(window.sceneExport)')
        layers = await page.evaluate('window.sceneExport.layers()')
        origin = await page.evaluate('window.sceneExport.origin')
        revision = await page.evaluate('window.sceneRevision')
        print(f'{"layer":<22}{"meshes":>8}{"triangles":>12}')
        for entry in layers:
            print(f'{entry["layer"]:<22}{entry["meshes"]:>8}{entry["triangles"]:>12,}')
        if '--list' in sys.argv or (not wanted and '--all' not in sys.argv):
            await browser.close()
            return
        names = [e['layer'] for e in layers] if '--all' in sys.argv else wanted
        unknown = [n for n in names if n not in {e['layer'] for e in layers}]
        if unknown:
            raise SystemExit(f'Unknown layers: {unknown}')
        manifest = {'quality': quality, 'sceneRevision': revision, 'origin': origin, 'layers': {}}
        for name in names:
            started = time.time()
            size = await page.evaluate('(layer) => window.sceneExport.prepare(layer)', name)
            path = OUT / f'{name}.glb'
            with path.open('wb') as handle:
                for offset in range(0, size, SLICE):
                    chunk = await page.evaluate('([o, n]) => window.sceneExport.slice(o, n)', [offset, min(SLICE, size - offset)])
                    handle.write(base64.b64decode(chunk))
            await page.evaluate('window.sceneExport.release()')
            stats = validate_and_tag(path, origin, name, revision)
            entry = next(e for e in layers if e['layer'] == name)
            manifest['layers'][name] = {**entry, 'file': path.name, 'bytes': path.stat().st_size, **stats}
            print(f'{name}: {path.stat().st_size / 1e6:.1f} MB, {stats["meshes"]} meshes, {stats["textures"]} textures, {time.time() - started:.0f}s')
        (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=1))
        await browser.close()
    if errors:
        print('Page errors:\n  ' + '\n  '.join(errors))
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
