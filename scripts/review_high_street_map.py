"""Overlay the added ranges, retained source axes and vista path on the OS mosaic."""
import json
from pathlib import Path
from PIL import Image,ImageDraw
from factory_map_sources import mosaic
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_text())
data=load('docs/data/high-street-frontages.json');raw=load('data/maps/high-street-frontages.json');factories=load('docs/data/factory-buildings.json')
a,_,pixel=mosaic(data['source']['mosaicBounds']);im=Image.fromarray(a);draw=ImageDraw.Draw(im)
for b in factories['buildings']:
 for p in b['renderPolygons']:
  xy=[tuple(q) for q in pixel(p['outer'])];draw.line(xy+[xy[0]],fill='#557aaa',width=2)
for b in data['buildings']:
 for p in b['renderPolygons']:
  xy=[tuple(q) for q in pixel(p['outer'])];draw.line(xy+[xy[0]],fill='#c1272d',width=3)
 draw.text(tuple(pixel([[b['x'],b['z']]])[0]),b['id'].split('-')[-1],fill='#c1272d',stroke_width=1,stroke_fill='white')
bank=data['vista']['bank'];draw.line([tuple(q) for q in pixel([[x+bank['pathLandOffset'],z] for x,z in bank['samples']])],fill='green',width=4)
out=ROOT/'reference/wall-river-vista';out.mkdir(parents=True,exist_ok=True);im.save(out/'high-street-frontages-overlay.png')
print('Saved OS overlay: existing factories blue, added ranges red, provisional path green.')
