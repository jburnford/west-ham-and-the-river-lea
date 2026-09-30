"""Check factory source coverage and separation from the neighbouring church."""
import sys
from shapely.geometry import Polygon, shape
from shapely.ops import unary_union
from factory_alignment_checks import check_register, load

check_register('mineral-water',{f'west-792-{i}' for i in range(1,4)},3,0,
    'mill-brush-brewery-before',preflight='--preflight' in sys.argv,
    later_registers=['mill-brush','bow-brewery'])
r=load('data/maps/mineral-water-footprint-alignment.json')
source=load('reference/footprint-model-alignment/mill-brush-brewery-source-shapes.json')
body=unary_union([Polygon(b['worldFootprint'],b['worldHoles']) for b in r['buildings']])
church=shape(source['5167'])
assert body.distance(church)>1
assert not r.get('removedBuildings') and not r.get('additionalBuildings') and not r['structures']
assert {f for g in r['groups'] for f in g['sourceFids']}=={108407,27009,154380,32892,235227,825734}
assert body.area>660 and body.area<665
print('Mineral water: three mapped ranges, retained roof profiles and clear church/court pass.')
