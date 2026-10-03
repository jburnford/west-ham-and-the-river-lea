"""Export the model's terrain grids as GeoTIFFs in EPSG:27700 (British National Grid).

Reads the scene's binary Float32/Uint8 grids plus their JSON metadata from docs/data,
converts the local scene frame (metres east and south of the bridge origin) back to
eastings and northings, and writes one GeoTIFF per grid into exports/gis/terrain/.

Scene Y is the renderer's vertical unit. Where the 1900 vertical reference is known
an additional *_odn.tif is written by adding the recorded ODN offset. That offset is
provisional (see terrain-1900.json verticalReference) and is copied into the TIFF
metadata so nobody mistakes it for a survey calibration.

No GDAL or rasterio needed: tifffile writes the GeoTIFF tags directly.

    python3 scripts/export_terrain_geotiff.py            # writes exports/gis/terrain/
    python3 scripts/export_terrain_geotiff.py --verify   # also reads every file back
"""
import json
import sys
from pathlib import Path

import numpy as np
import tifffile

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'docs/data'
OUT = ROOT / 'exports/gis/terrain'

# GeoTIFF key ids (OGC GeoTIFF 1.1).
MODEL_PIXEL_SCALE, MODEL_TIEPOINT, GEO_KEY_DIRECTORY = 33550, 33922, 34735
GDAL_METADATA, GDAL_NODATA = 42112, 42113
RASTER_IS_AREA, RASTER_IS_POINT = 1, 2


def load_json(name):
    return json.loads((DATA / name).read_text())


def origin():
    o = load_json('ground-plan.json')['origin']
    assert o['crs'] == 'EPSG:27700' and o['axes'] == 'x east; z south; metres', o
    return o['easting'], o['northing']


def write_geotiff(path, grid, *, x0, z0, step, registration, description, metadata, nodata=None):
    """Write a north-up GeoTIFF. Row 0 is the smallest scene z, i.e. the northern edge.

    registration: RASTER_IS_POINT when grid values are samples at (x0 + i*step, z0 + j*step);
    RASTER_IS_AREA when (x0, z0) is the outer corner of the first cell.
    """
    easting, northing = origin()
    tiepoint = (0.0, 0.0, 0.0, float(easting + x0), float(northing - z0), 0.0)
    keys = (1, 1, 0, 3,
            1024, 0, 1, 1,             # GTModelTypeGeoKey = projected
            1025, 0, 1, registration,  # GTRasterTypeGeoKey
            3072, 0, 1, 27700)         # ProjectedCSTypeGeoKey = British National Grid
    items = ''.join(f'<Item name="{k}">{v}</Item>' for k, v in metadata.items())
    extratags = [
        (MODEL_PIXEL_SCALE, 'd', 3, (float(step), float(step), 0.0), True),
        (MODEL_TIEPOINT, 'd', 6, tiepoint, True),
        (GEO_KEY_DIRECTORY, 'H', len(keys), keys, True),
        (GDAL_METADATA, 's', 0, f'<GDALMetadata>{items}</GDALMetadata>', True),
    ]
    if nodata is not None:
        extratags.append((GDAL_NODATA, 's', 0, str(nodata), True))
    path.parent.mkdir(parents=True, exist_ok=True)
    tifffile.imwrite(path, np.ascontiguousarray(grid), description=description,
                     compression='zlib', extratags=extratags, metadata=None)
    return path


def grid_from(file, dtype, width, height):
    values = np.fromfile(DATA / file, dtype=dtype)
    if values.size != width * height:
        raise SystemExit(f'{file}: {values.size} values, expected {width}x{height}')
    return values.reshape(height, width)


def export_core_terrain(written, odn_offset):
    """The detailed 0.4 m Channelsea tile: interpreted baseline plus the 1900 main-landscape heights."""
    t = load_json('river-terrain.json')
    x0, z0 = t['bounds'][0], t['bounds'][1]
    common = dict(x0=x0, z0=z0, step=t['step'], registration=RASTER_IS_POINT)
    base = dict(source='docs/data/river-terrain.json', evidence=t['evidence'], units='scene Y metres')
    levels = grid_from(t['heightFile'], np.float32, t['width'], t['height'])
    written.append(write_geotiff(OUT / 'core-terrain-baseline-sceneY.tif', levels, **common,
                                 description='Channelsea detailed terrain, interpreted baseline, scene Y', metadata=base))
    landcover = grid_from(t['landcoverFile'], np.uint8, t['width'], t['height'])
    written.append(write_geotiff(OUT / 'core-terrain-landcover.tif', landcover, **common,
                                 description='Channelsea detailed terrain land cover classes (0 open, 1 and 2 mapped covers)',
                                 metadata={**base, 'units': 'class code'}))
    properties = np.fromfile(DATA / t['propertyFile'], dtype=np.uint8).reshape(t['height'], t['width'], 4)
    written.append(write_geotiff(OUT / 'core-terrain-sediment-mask.tif', properties[:, :, 3], **common,
                                 description='Channelsea detailed terrain sediment mask (alpha channel of the property grid)',
                                 metadata={**base, 'units': '0-255 mask'}))
    main = DATA / 'main-landscape-1900.json'
    if main.exists():
        m = json.loads(main.read_text())
        core = grid_from(m['files']['core'], np.float32, t['width'], t['height'])
        meta = {**base, 'source': 'docs/data/main-landscape-1900.json core replacement', 'epoch': m['epoch'],
                'status': m['status'], 'limitations': ' | '.join(m['limitations'])}
        written.append(write_geotiff(OUT / 'core-terrain-1900-main-landscape-sceneY.tif', core, **common,
                                     description='Channelsea detailed terrain as rendered in the 1900 main landscape, scene Y', metadata=meta))
        if odn_offset is not None:
            written.append(write_geotiff(OUT / 'core-terrain-1900-main-landscape-odn.tif', core + np.float32(odn_offset), **common,
                                         description='Channelsea detailed terrain as rendered in the 1900 main landscape, provisional ODN metres',
                                         metadata={**meta, 'units': 'metres above ODN (provisional)', 'odnMinusSceneYMetres': odn_offset}))


def export_historic_terrain(written):
    """The 1 m dated open-ground reconstruction from terrain-<epoch>.json."""
    catalogue = load_json('terrain-epochs.json')
    offsets = {}
    for epoch, entry in catalogue['epochs'].items():
        if not entry.get('asset'):
            continue
        meta = load_json(entry['asset'])
        ref = meta.get('verticalReference', {})
        offset = ref.get('odnMinusSceneYMetres')
        offsets[epoch] = offset
        x0, z0 = meta['bounds'][0], meta['bounds'][1]
        common = dict(x0=x0, z0=z0, step=meta['step'], registration=RASTER_IS_POINT)
        base = {'source': f"docs/data/{entry['asset']}", 'epoch': meta['epoch'], 'geometryEpoch': meta['geometryEpoch'],
                'continuityAssumption': meta.get('continuityAssumption', ''),
                'verticalReference': json.dumps(ref)}
        descriptions = {
            'target': ('reconstructed open-ground level from dated observations, scene Y', 'scene Y metres'),
            'scene': ('rendered ground after blending with the detailed scene, scene Y', 'scene Y metres'),
            'weight': ('support weight of dated observations, 0 none to 1 full', 'weight 0-1'),
            'odn': ('reconstructed open-ground level, provisional ODN metres', 'metres above ODN (provisional)'),
        }
        for key, file in meta['files'].items():
            if key not in descriptions:
                continue  # extension is a triangle list, exported as geometry elsewhere
            grid = grid_from(file, np.float32, meta['width'], meta['height'])
            text, units = descriptions[key]
            written.append(write_geotiff(OUT / f'historic-terrain-{epoch}-{key}.tif', grid, **common,
                                         description=f'Historic terrain {epoch}: {text}', metadata={**base, 'units': units}))
        odn_file = DATA / f'terrain-{epoch}.odn.f32'
        if 'odn' not in meta['files'] and odn_file.exists():
            grid = grid_from(odn_file.name, np.float32, meta['width'], meta['height'])
            written.append(write_geotiff(OUT / f'historic-terrain-{epoch}-odn.tif', grid, **common,
                                         description=f'Historic terrain {epoch}: reconstructed open-ground level, provisional ODN metres',
                                         metadata={**base, 'units': 'metres above ODN (provisional)'}))
        for mask in ('drainage-mask', 'road-mask', 'zones'):
            file = DATA / f'terrain-{epoch}.{mask}.u8'
            if file.exists():
                grid = grid_from(file.name, np.uint8, meta['width'], meta['height'])
                written.append(write_geotiff(OUT / f'historic-terrain-{epoch}-{mask}.tif', grid, **common,
                                             description=f'Historic terrain {epoch}: {mask} (class codes)', metadata={**base, 'units': 'class code'}))
    return offsets


def export_main_landscape(written, odn_offset):
    """The 10 m regional early-marsh field applied across the main 1900 scene."""
    path = DATA / 'main-landscape-1900.json'
    if not path.exists():
        return
    m = json.loads(path.read_text())
    f = m['field']
    if not f.get('cellCentres'):
        raise SystemExit('main-landscape field is expected to describe cell centres')
    common = dict(x0=f['bounds'][0], z0=f['bounds'][1], step=f['step'], registration=RASTER_IS_AREA)
    base = {'source': 'docs/data/main-landscape-1900.json', 'epoch': m['epoch'], 'status': m['status'], 'scope': m['scope'],
            'limitations': ' | '.join(m['limitations'])}
    level = grid_from(m['files']['level'], np.float32, f['width'], f['height'])
    weight = grid_from(m['files']['weight'], np.float32, f['width'], f['height'])
    written.append(write_geotiff(OUT / 'main-landscape-1900-level-sceneY.tif', level, **common,
                                 description='Regional early-marsh ground level applied to the 1900 scene, scene Y', metadata={**base, 'units': 'scene Y metres'}))
    written.append(write_geotiff(OUT / 'main-landscape-1900-weight.tif', weight, **common,
                                 description='Regional early-marsh application weight, 0 none to 1 full', metadata={**base, 'units': 'weight 0-1'}))
    if odn_offset is not None:
        written.append(write_geotiff(OUT / 'main-landscape-1900-level-odn.tif', level + np.float32(odn_offset), **common,
                                     description='Regional early-marsh ground level applied to the 1900 scene, provisional ODN metres',
                                     metadata={**base, 'units': 'metres above ODN (provisional)', 'odnMinusSceneYMetres': odn_offset}))


def verify(paths):
    easting, northing = origin()
    for path in paths:
        with tifffile.TiffFile(path) as tif:
            assert tif.is_geotiff, path
            geo = tif.geotiff_metadata
            assert int(geo['ProjectedCSTypeGeoKey']) == 27700, (path, geo)
            tie = geo['ModelTiepoint']
            assert tie[3] - easting < 20000 and northing - tie[4] < 20000, (path, tie)
            page = tif.pages[0]
            assert page.shape[0] > 1 and page.shape[1] > 1
    print(f'Verified {len(paths)} GeoTIFFs: EPSG:27700 keys, tiepoints near the bridge origin, non-empty grids.')


def main():
    written = []
    offsets = export_historic_terrain(written)
    odn = offsets.get('1900')
    export_core_terrain(written, odn)
    export_main_landscape(written, odn)
    readme = OUT / 'README.md'
    readme.write_text(f"""# Terrain GeoTIFF exports

Generated by `scripts/export_terrain_geotiff.py` from the model grids in `docs/data`.
All files are EPSG:27700 (British National Grid). The scene origin is easting {origin()[0]},
northing {origin()[1]}, the approximate listed grid reference of the Northern Outfall Sewer bridge.

`*-sceneY.tif` hold the renderer's vertical unit. `*-odn.tif` add the provisional ODN offset
recorded in `terrain-1900.json` ({odn} m, stated uncertainty 0.3 m). That offset is a working
assumption, not a survey calibration. Grids tagged "point" are vertex samples; the 10 m main
landscape field is cell-area registered.

Files:
""" + ''.join(f'- `{p.name}`\n' for p in written))
    print(f'Wrote {len(written)} GeoTIFFs to {OUT.relative_to(ROOT)}')
    if '--verify' in sys.argv:
        verify(written)


if __name__ == '__main__':
    main()
