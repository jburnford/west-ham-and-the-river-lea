"""Check Crown/Johnson exteriors, southern trace and independent chimney base."""
import sys
from shapely import affinity
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union
from factory_alignment_checks import check_register, load

preflight='--preflight' in sys.argv
check_register('crown-johnson',{f'site398-range-{i}' for i in [1,2,3,4,5,6,8,9,10]},7,0,
               'remaining-trades-before',preflight=preflight,later_registers=['ritchie-jute','western-trades'])
r=load('data/maps/crown-johnson-footprint-alignment.json')
s=load('docs/data/factory-buildings.json');models={b['id']:b for b in s['buildings']}
c=r['mapTracedBuildings'][0];p=Polygon(c['worldFootprint'],c['worldHoles'])
assert p.is_valid and 120<p.area<140
assert r['directTrace']['includedSourceFids']==[760489] and r['directTrace']['exclusionSourceFids']==[767359]
if not preflight:
    b=models[c['modelId']]
    assert b['footprintSource']=='os-1893-direct-trace' and 'sourceFootprintFids' not in b
    actual=unary_union([Polygon(q['outer'],q['holes']) for q in b['renderPolygons']])
    assert actual.symmetric_difference(p).area<.01
    for key,saved in [('height','eavesHeight'),('roofRise','roofRise'),('roofAxis','roofAxis'),('roofBays','roofBays')]:
        assert b[key]==c[saved]
    assert sum(b['siteId']==398 for b in models.values())==10
stack=r['structures'][0]
assert stack['sourceFid']==1018184 and stack['preservedHeight']==22
centre=Point(stack['centre']);radius=stack['radius']
base=unary_union([Polygon(q[0],q[1:]) for q in stack['sourcePolygons']])
plinth=affinity.rotate(box(centre.x-radius*1.2,centre.y-radius*1.2,centre.x+radius*1.2,centre.y+radius*1.2),stack['rotation'],origin=centre)
assert plinth.difference(base).area<.000001
body=unary_union([Polygon(q['worldFootprint'],q['worldHoles']) for q in r['buildings']+r['mapTracedBuildings']])
assert plinth.intersection(body).area<.000001
if not preflight:
    actual=next(t for t in s['structures'] if t['id']==stack['id'])
    assert Point(actual['x'],actual['z']).distance(centre)<.001
    assert actual['height']==22 and actual['radius']==radius
print('Crown/Johnson: southern roof trace and complete mapped square plinth pass; Goad alterations remain explicit.')
