"""Compare added western works and the northern rail link with archived OS tiles."""
import json
from pathlib import Path
from PIL import Image, ImageDraw
from factory_map_sources import mosaic

ROOT=Path(__file__).resolve().parents[1]
read=lambda p:json.loads((ROOT/p).read_text())
survey=read('data/maps/west-bank-industry.json')
factories=read('docs/data/factory-buildings.json')
infra=read('docs/data/infrastructure.json')
out=ROOT/'reference/western-completion';out.mkdir(parents=True,exist_ok=True)
for name,frame in survey['frames'].items():
    pixels,_,to_pixel=mosaic(frame['bounds']);im=Image.fromarray(pixels);d=ImageDraw.Draw(im)
    for b in factories['buildings']:
        if b.get('mapFrame')!=name or b['source']!='os-west-bank-1893':continue
        for poly in b['renderPolygons']:
            points=[tuple(p) for p in to_pixel(poly['outer'])]
            d.line(points+[points[0]],fill='#b32929',width=3)
        p=tuple(to_pixel([[b['x'],b['z']]])[0]);d.text(p,b['id'],fill='#b32929',stroke_width=1,stroke_fill='white')
    im.save(out/f'{name}-buildings.png')
extension=next(r for r in infra['railways'] if r.get('id')=='woolwich-northern-connection')
pixels,_,to_pixel=mosaic(extension['source']['bounds']);im=Image.fromarray(pixels);d=ImageDraw.Draw(im)
for r in infra['railways']:
    points=[tuple(p) for p in to_pixel(r['route'])]
    d.line(points,fill='#b32929' if r.get('detailedMainline') else '#16785b',width=4)
for rings in extension['footprint']:
    for ring in rings:d.line([tuple(p) for p in to_pixel(ring)],fill='#4077a1',width=2)
im.thumbnail((1500,1800));im.save(out/'woolwich-connection-map.png')
print('Saved western factory and railway map overlays to',out)
