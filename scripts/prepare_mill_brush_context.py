"""Separate mapped Marshgate approaches; remove the old shortcut through the mill."""
import json
from pathlib import Path
from factory_map_sources import mosaic

ROOT=Path(__file__).resolve().parents[1]

def build():
    register=json.loads((ROOT/'data/maps/mill-brush-context-alignment.json').read_text())
    path=ROOT/'data/maps/district-road-traces.json'
    roads=json.loads(path.read_text())
    correction=register['road']
    road=next(r for r in roads['roads'] if r['name']==correction['name'])
    remaining=ROOT/'data/maps/remaining-trades-context-alignment.json'
    if remaining.exists():
        saved=next(c for c in json.loads(remaining.read_text())['roads'] if c['name']==road['name'])
        if road['points']==saved['points']:
            assert road['bridgeSpans']==saved['bridgeSpans']
            road['points']=saved['priorPoints']
            road['bridgeSpans']=saved['priorBridgeSpans']
    assert road['points'] in [correction['priorPoints'],correction['points']]
    assert road['width']==correction['width'] and road['bridgeSpans']==correction['priorBridgeSpans']
    road['points']=correction['points']
    road['millBrushAlignment']=dict(register='data/maps/mill-brush-context-alignment.json',review=register['review'])
    north=register['additionalRoad']
    for r in [road,north]:
        _,_,pixel=mosaic(r['sourceBounds'])
        r['sourcePixels']=pixel(r['points']).round(3).tolist()
    roads['roads']=[r for r in roads['roads'] if r['name']!=north['name']]+[north]
    later=ROOT/'data/maps/alderson-rope-context-alignment.json'
    if later.exists():
        from prepare_alderson_rope_context import apply_context
        apply_context(roads,json.loads(later.read_text()))
    if remaining.exists():
        from prepare_remaining_trades_context import apply_context
        apply_context(roads,json.loads(remaining.read_text()),names={'Marshgate Lane'})
    path.write_text(json.dumps(roads,indent=2)+'\n')
    print('Marshgate Lane: two mapped approaches; shortcut through the mill removed; existing crossing retained.')

if __name__=='__main__':build()
