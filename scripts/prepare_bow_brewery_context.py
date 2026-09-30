"""Apply the documented brewery pavement pinch without moving the carriageway."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def build():
    register=json.loads((ROOT/'data/maps/bow-brewery-frontage-alignment.json').read_text())
    path=ROOT/'data/maps/district-road-traces.json'
    roads=json.loads(path.read_text())
    road=next(r for r in roads['roads'] if r['name']==register['road'])
    assert road['width']==12
    review={k:register[k] for k in ['id','modelIds','shoulderWidth','evidence']}
    road['buildingClearanceReviews']=[r for r in road.get('buildingClearanceReviews',[]) if r.get('id')!=review['id']]+[review]
    path.write_text(json.dumps(roads,indent=2)+'\n')
    print('Bow Brewery: 0.78 m local pavement; 12 m High Street carriageway retained.')

if __name__=='__main__':build()
