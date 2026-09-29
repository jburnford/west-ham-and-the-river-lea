"""Compare yard interpretation with the archived georeferenced OS tiles."""
import json
from pathlib import Path
from PIL import Image,ImageDraw
from factory_map_sources import mosaic

ROOT=Path(__file__).resolve().parents[1]
source=json.loads((ROOT/'data/maps/sawmill-yard.json').read_text())
yards=json.loads((ROOT/'docs/data/factory-yards.json').read_text())
yard=next(s for s in yards['sites'] if s['id']==797)
bounds=source['source']['mosaicBounds']
pixels,_,to_pixel=mosaic(bounds)
im=Image.fromarray(pixels);draw=ImageDraw.Draw(im)
def line(points,color,width):
    draw.line([tuple(p) for p in to_pixel(points)],fill=color,width=width)
for ring in source['parcel']:line(ring,'#007f64',3)
for track in yards['tracks']:line(track['points'],'#b32929',3)
for item in yard['stock']:line(item['footprint'],'#315ac4',2)
crop=to_pixel([[bounds[0],bounds[1]],[bounds[2],bounds[3]]])
im=im.crop(tuple(map(int,[*crop[0],*crop[1]])))
out=ROOT/'reference/factory-building-survey/review/sawmill-yard-overlay.png'
im.save(out)
print('OS overlay: green = restored GIS parcel, red = traced yard tracks, blue = inferred timber stacks.')
