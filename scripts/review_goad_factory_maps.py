"""Compare each refined factory with its original Goad sheet and OS context."""
import json
from pathlib import Path
from PIL import Image, ImageDraw
from factory_map_sources import mosaic

ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'docs/data/factory-buildings.json').read_text())
OUT=ROOT/'reference/factory-building-survey/review'
for name,site,bounds in [('soap',796,[-1340,-380,-1000,-30]),
                        ('sawmill',797,[-1250,-185,-950,35]),
                        ('jute',1017,[-850,-1050,-250,-480])]:
    rows=[b for b in data['buildings'] if b['siteId']==site]
    pixels,_,to_pixel=mosaic(bounds)
    image=Image.fromarray(pixels);draw=ImageDraw.Draw(image)
    for b in rows:
        draw.line([tuple(p) for p in to_pixel(b['footprint']+[b['footprint'][0]])],fill='#b32929',width=3)
    crop=to_pixel([[bounds[0],bounds[1]],[bounds[2],bounds[3]]])
    image=image.crop(tuple(map(int,[*crop[0],*crop[1]])))
    image.thumbnail((1600,1600));image.save(OUT/f'goad-{name}-os-overlay.png')
    mapped=[b for b in rows if b['source'].startswith('goad-f')]
    source=data['sources'][mapped[0]['source']]
    image=Image.open(ROOT/source['file']).convert('RGB');draw=ImageDraw.Draw(image)
    points=[p for b in mapped for p in b['footprintPixels']]
    for b in mapped:
        p=b['footprintPixels'];draw.line([tuple(q) for q in p+[p[0]]],fill='#00785b',width=2)
    crop=(min(p[0] for p in points)-35,min(p[1] for p in points)-35,
          max(p[0] for p in points)+35,max(p[1] for p in points)+35)
    image=image.crop(crop);image.thumbnail((1800,1400));image.save(OUT/f'goad-{name}-source-overlay.png')
print('Three factory comparisons saved: original Goad compartments and OS registration.')
