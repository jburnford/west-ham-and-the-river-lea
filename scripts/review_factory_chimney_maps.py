"""Reproduce the visual evidence cards for each traced factory chimney."""
import json
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
raw = json.loads((ROOT/'data/maps/factory-building-traces.json').read_text())
stacks = [s for s in raw['structures'] if s['kind'] == 'chimney' and s.get('symbolKey')]
out = ROOT/'reference/factory-building-survey/review/chimneys'
out.mkdir(parents=True, exist_ok=True)
originals = {}
for source in {s['source'] for s in stacks}:
    originals[source] = Image.open(ROOT/raw['sources'][source]['file']).convert('RGB')
for page in range((len(stacks)+11)//12):
    canvas = Image.new('RGB', (1440, 1260), '#f7f2e8')
    draw = ImageDraw.Draw(canvas)
    for i, s in enumerate(stacks[page*12:(page+1)*12]):
        x, y = s['pixelPosition']
        cx, cy = (i % 4)*360, (i // 4)*420
        crop = originals[s['source']].crop((x-48, y-48, x+48, y+48)).resize((336, 336))
        canvas.paste(crop, (cx+12, cy+64))
        draw.text((cx+12, cy+5), s['id'], fill='black')
        draw.text((cx+12, cy+23), s['name'], fill='black')
        height = f"{s['mappedHeightFeet']}' on map" if 'mappedHeightFeet' in s else 'Height estimated'
        draw.text((cx+12, cy+41), f"{s['source']} | {height}", fill='black')
        # Marginal ticks locate the trace centre without covering the symbol.
        draw.line((cx+176, cy+403, cx+184, cy+403), fill='#c0392b', width=3)
        draw.line((cx+7, cy+228, cx+7, cy+236), fill='#c0392b', width=3)
    canvas.save(out/f'symbols-{page+1}.jpg', quality=93)
print(f'{len(stacks)} source-symbol cards written to {out}')
