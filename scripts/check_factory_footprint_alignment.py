"""Verify actual rendered geometry against the registered source corrections."""
import json
import math
from pathlib import Path
from shapely.geometry import Polygon
from shapely.ops import unary_union
ROOT=Path(__file__).resolve().parents[1]
reg=json.loads((ROOT/'data/maps/factory-footprint-alignment.json').read_text())['buildings']
scene=json.loads((ROOT/'docs/data/factory-buildings.json').read_text());models={b['id']:b for b in scene['buildings']}
assert len({r['sourceFid'] for r in reg})==len(reg),'Ambiguous many-to-one match'
results=[]
for r in reg:
 b=models[r['modelId']];target=Polygon(r['worldFootprint']);original=Polygon(r['priorFootprint'])
 rendered=unary_union([Polygon(p['outer'],p['holes']) for p in b['renderPolygons']])
 before=target.intersection(original).area/target.union(original).area
 after=target.intersection(rendered).area/target.union(rendered).area
 assert target.is_valid and rendered.is_valid
 assert after>before and after>.85,(b['id'],before,after)
 assert Polygon(b['footprint']).symmetric_difference(target).area<.001,b['id']
 assert b['sourceFootprintFid']==r['sourceFid']
 assert math.isclose(b['height'],r['preservedHeight']) and math.isclose(b['roofRise'],r['preservedRoofRise'])
 assert b['roofBays']==r['preservedRoofBays'] and b['roofAxis']==r['preservedRoofAxis']
 results.append({'id':b['id'],'sourceFid':r['sourceFid'],'beforeIoU':before,'renderedIoU':after})
out=ROOT/'reference/footprint-model-alignment/verified-matches.json';out.write_text(json.dumps(results,indent=2)+'\n')
print(f'{len(results)} source-linked ranges: every rendered outline improves; height and roof interpretations preserved.')
print(f'Median rendered IoU: {sorted(r["renderedIoU"] for r in results)[len(results)//2]:.3f}; minimum {min(r["renderedIoU"] for r in results):.3f}.')
