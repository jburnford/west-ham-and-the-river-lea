"""Overlay the modelled railway on the archived, georeferenced OS tiles."""
import json
from pathlib import Path
from PIL import Image, ImageDraw
from factory_map_sources import mosaic

ROOT = Path(__file__).resolve().parents[1]
source = json.loads((ROOT/'data/maps/great-eastern-mainline.json').read_text())
infra = json.loads((ROOT/'docs/data/infrastructure.json').read_text())
rail = next(r for r in infra['railways'] if r.get('detailedMainline'))
for name, bounds in [('overview', source['source']['overviewBounds']),
                     ('east', source['source']['eastBounds'])]:
    pixels, _, to_pixel = mosaic(bounds)
    image = Image.fromarray(pixels)
    draw = ImageDraw.Draw(image)
    for polygon in rail['footprint']:
        for ring in polygon:
            draw.line([tuple(p) for p in to_pixel(ring)], fill='#16806d', width=3)
    draw.line([tuple(p) for p in to_pixel(rail['route'])], fill='#b32929', width=4)
    crop = to_pixel([[bounds[0], bounds[1]], [bounds[2], bounds[3]]])
    image = image.crop(tuple(map(int, [*crop[0], *crop[1]])))
    image.thumbnail((1900, 1500))
    image.save(ROOT/f'reference/factory-building-survey/review/great-eastern-{name}-overlay.png')
print('OS overlays: red = main-line centre; green = interpreted embankment footprint.')
