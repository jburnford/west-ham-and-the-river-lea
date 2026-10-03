"""Structural check of exported glTF layers: container, accessor bounds, origin tag.

    python3 scripts/check_gltf.py                 # every exports/gltf/*.glb
    python3 scripts/check_gltf.py exports/gltf/sewer.glb
"""
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# The flyable district plus margin, in scene metres; anything outside is a transform error.
LIMITS = {'x': (-5000, 7500), 'y': (-30, 400), 'z': (-6500, 7500)}


def read_glb(path):
    data = path.read_bytes()
    magic, version, length = struct.unpack_from('<4sII', data, 0)
    assert magic == b'glTF' and version == 2 and length == len(data), (path.name, magic, version, length, len(data))
    json_length, json_type = struct.unpack_from('<II', data, 12)
    assert json_type == 0x4E4F534A
    gltf = json.loads(data[20:20 + json_length].decode())
    bin_length, bin_type = struct.unpack_from('<II', data, 20 + json_length)
    assert bin_type == 0x004E4942, bin_type
    return gltf, bin_length


def check(path):
    gltf, bin_length = read_glb(path)
    extras = gltf.get('asset', {}).get('extras', {})
    assert extras.get('origin', {}).get('crs') == 'EPSG:27700', f'{path.name}: origin tag missing'
    meshes = gltf.get('meshes', [])
    assert meshes, f'{path.name}: no meshes'
    triangles = 0
    lo = [float('inf')] * 3
    hi = [float('-inf')] * 3
    for mesh in meshes:
        for primitive in mesh['primitives']:
            position = gltf['accessors'][primitive['attributes']['POSITION']]
            count = gltf['accessors'][primitive['indices']]['count'] if 'indices' in primitive else position['count']
            triangles += count // 3
            for i in range(3):
                lo[i] = min(lo[i], position['min'][i])
                hi[i] = max(hi[i], position['max'][i])
    for i, axis in enumerate('xyz'):
        a, b = LIMITS[axis]
        assert a <= lo[i] and hi[i] <= b, f'{path.name}: {axis} extent {lo[i]:.1f}..{hi[i]:.1f} outside {a}..{b}'
    buffers = sum(b['byteLength'] for b in gltf['buffers'])
    assert buffers == bin_length, (buffers, bin_length)
    images = len(gltf.get('images', []))
    print(f'{path.name}: {len(meshes)} meshes, {triangles:,} triangles, {len(gltf.get("materials", []))} materials, '
          f'{images} images, {bin_length / 1e6:.1f} MB binary; x {lo[0]:.0f}..{hi[0]:.0f}, y {lo[1]:.1f}..{hi[1]:.1f}, z {lo[2]:.0f}..{hi[2]:.0f}; '
          f'layer {extras.get("layer")}')
    return triangles


def main():
    paths = [Path(a) for a in sys.argv[1:]] or sorted((ROOT / 'exports/gltf').glob('*.glb'))
    if not paths:
        raise SystemExit('No .glb files found; run scripts/export_gltf.py first.')
    total = sum(check(p) for p in paths)
    print(f'{len(paths)} files pass: GLB container, origin tag, in-district extents, buffer sizes. {total:,} triangles in all.')


if __name__ == '__main__':
    main()
