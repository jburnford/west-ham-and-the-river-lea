"""Trace visible open working ground at three OS-labelled Channelsea wharves."""
import json
from pathlib import Path
from PIL import Image, ImageDraw
from shapely.geometry import Polygon, shape
from shapely.ops import unary_union
from factory_map_sources import mosaic

ROOT = Path(__file__).resolve().parents[1]
BOUNDS = [-280, -1020, 20, -470]
CACHE = 'reference/footprint-model-alignment/east-channelsea-source-shapes.json'
BASELINE = 'reference/footprint-model-alignment/east-wharf-yards-before.json'
# Full native mosaic pixels, not rescaled screenshot coordinates. Stratford
# follows the exposed working ground around its shaded roofs: it does not
# claim a complete cadastral tenure parcel or incorporate the domestic yards.
TRACES = {
    9007: [[155,778],[173,772],[178,766],[201,787],[205,782],
           [209,786],[214,780],[209,776],[229,754],[282,815],
           [250,834],[244,814],[178,843],[191,878],[218,926],
           [262,907],[303,962],[277,980],[231,981],[231,961],
           [198,962],[198,982],[184,983],[188,978]],
    9005: [[175,983],[277,980],[324,1051],[287,1074],
           [279,1092],[183,1107],[179,1036],[176,1035]],
    9006: [[196,1225],[295,1218],[332,1290],[233,1335],
           [213,1355],[207,1357]],
}
NAMES = {9007: 'Stratford Wharf', 9005: 'Caledonian Wharf', 9006: 'Halling Wharf'}


def polygon_rows(geometry):
    return [[[list(q) for q in ring.coords] for ring in [p.exterior, *p.interiors]]
            for p in getattr(geometry, 'geoms', [geometry])
            if p.geom_type == 'Polygon' and p.area > .01]


def build():
    load = lambda p: json.loads((ROOT / p).read_text())
    raw, world, pixel = mosaic(BOUNDS)
    cache = {int(fid): shape(g) for fid, g in load(CACHE).items()}
    baseline = ROOT / BASELINE
    if not baseline.exists():
        old = load('docs/data/factory-yards.json')
        assert not ({9005,9006,9007} & {s['id'] for s in old['sites']})
        baseline.write_text(json.dumps(dict(sites=old['sites'], tracks=old['tracks']), separators=(',', ':'))+'\n')
    yards = []
    for site, pixels in TRACES.items():
        parcel = Polygon(world(pixels).round(3))
        assert parcel.is_valid, site
        excluded = sorted(fid for fid, p in cache.items() if p.intersects(parcel))
        protected = unary_union([cache[fid] for fid in excluded])
        ground = parcel.difference(protected.buffer(.15))
        yards.append(dict(id=site, name=NAMES[site], tracePixels=pixels,
            worldTrace=[list(q) for q in parcel.exterior.coords],
            excludedSourceFids=excluded, polygons=polygon_rows(ground),
            surface='earth', allowStock=False,
            evidence='Visible open ground traced from the native OS five-foot plan. Shaded roof and covered-strip outlines, including source buildings not yet modelled in 3D, are excluded. The renderer additionally clears current roofs, roads and river banks. Domestic rear plots remain outside the traced ground.',
            interpretation='Earth surface appearance and any clear wear route are visual estimates. No commodity stock, quay elevation, retaining wall height or precise wharf ownership is inferred.'))
    result = dict(source='Cached OS London five-foot map, 1893 revision; author-supplied historic building outlines',
        bounds=BOUNDS, sourceCache=CACHE, baseline=BASELINE,
        evidenceImage='reference/footprint-model-alignment/east-wharf-yards-os.png',
        coordinates='Full native mosaic pixels; scene x=BNG E-538900, z=183209-BNG N',
        yards=yards,
        deferred=['Stratford Wharf northern and southern stippled roof/covered areas need separate building classification; they remain outside this working surface.',
                  'Halling Wharf western stepped outline remains ground context; this trace does not establish a raised quay or its elevation.'])
    (ROOT/'data/maps/east-wharf-yards.json').write_text(json.dumps(result, indent=2)+'\n')
    overlay = Image.new('RGBA', (raw.shape[1], raw.shape[0]))
    draw = ImageDraw.Draw(overlay)
    for yard in yards:
        for polygon in yard['polygons']:
            draw.polygon([tuple(q) for q in pixel(polygon[0])], fill=(200,130,0,75), outline='red', width=1)
            for hole in polygon[1:]:
                draw.polygon([tuple(q) for q in pixel(hole)], fill=(0,0,0,0))
    Image.alpha_composite(Image.fromarray(raw).convert('RGBA'), overlay).crop(
        (120,710,380,1380)).resize((1040,2680)).save(ROOT/result['evidenceImage'])
    print('Three native OS wharf working surfaces; all supplied building outlines excluded; no stock added.')


if __name__ == '__main__':
    build()
