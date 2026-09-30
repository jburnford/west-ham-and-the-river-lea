"""Apply the saved OS carriageway reconciliation after Bow Flour preparation."""
import json
from pathlib import Path
from factory_map_sources import mosaic, TO_MERCATOR, SHIFT

ROOT=Path(__file__).resolve().parents[1]

def build():
    path=ROOT/'data/maps/district-road-traces.json'
    roads=json.loads(path.read_text())
    register=json.loads((ROOT/'data/maps/bow-magnet-context-alignment.json').read_text())
    for correction in register['roads']:
        road=next(r for r in roads['roads'] if r['name']==correction['name'])
        assert road['points'] in [correction['priorPoints'],correction['points']]
        assert road['width']==correction['width']
        road['points']=correction['points']
        road['bridgeSpans']=correction['bridgeSpans']
        if 'sourceBounds' in road:
            _,_,pixel=mosaic(road['sourceBounds'])
            road['sourcePixels']=pixel(road['points']).round(3).tolist()
        else:
            assert road['sourceMosaic']=='m18_131060_87140'
            step=2*SHIFT/(2**18*256)
            projected=[TO_MERCATOR.transform(538900+x,183209-z) for x,z in road['points']]
            road['sourcePixels']=[[round((x+SHIFT)/step-131060*256,3),round((SHIFT-y)/step-87140*256,3)] for x,y in projected]
        road['bowMagnetAlignment']=dict(register='data/maps/bow-magnet-context-alignment.json',review=register['review'])
    path.write_text(json.dumps(roads,indent=2)+'\n')
    print('Bow/Magnet context: saved High Street and Cook’s Road carriageway/connection controls applied.')

if __name__=='__main__':build()
