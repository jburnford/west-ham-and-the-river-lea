"""Verify Alderson's mapped ranges, direct ropewalk and open central yard."""
import sys
from shapely.geometry import Polygon
from shapely.ops import unary_union
from factory_alignment_checks import check_register, load

preflight='--preflight' in sys.argv
check_register('alderson-rope',{'site791-'+s for s in ['eaststore','806','808','810','814','816']},
               4,0,'marshgate-trades-before',preflight=preflight,
               later_registers=['jeffrey-glue','marshgate-chemical'])
r=load('data/maps/alderson-rope-footprint-alignment.json')
s=load('docs/data/factory-buildings.json');models={b['id']:b for b in s['buildings']}
c=r['mapTracedBuildings'][0];p=Polygon(c['worldFootprint'],c['worldHoles'])
assert p.is_valid and 350<p.area<600
assert r['removedBuildings'][0]['id']=='site791-north'
assert r['retainedSourceLinks']==[dict(modelId='site791-dry',sourceFid=107330)]
assert models['site791-dry']['sourceFootprintFid']==107330
assert not r['structures'] and not r.get('additionalBuildings')
if not preflight:
    assert 'site791-north' not in models
    assert sum(b['siteId']==791 for b in models.values())==8
    b=models[c['modelId']]
    assert b['footprintSource']=='os-1893-direct-trace' and 'sourceFootprintFids' not in b
    actual=unary_union([Polygon(q['outer'],q['holes']) for q in b['renderPolygons']])
    assert actual.symmetric_difference(p).area<.01
    assert abs(b['rotation']-c['footprintRotationDegrees'])<.0001
    for key,saved in [('height','eavesHeight'),('roofRise','roofRise'),('roofAxis','roofAxis'),('roofBays','roofBays')]:
        assert b[key]==c[saved]
print('Alderson: direct ropewalk, retained drying house and removal of unsupported yard workshop pass.')
