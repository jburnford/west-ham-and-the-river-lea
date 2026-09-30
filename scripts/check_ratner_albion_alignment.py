"""Check Sol-authored western compounds, courtyard openings and plant decisions."""
import math
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
from factory_alignment_checks import check_register, load, later_reviews

check_register('ratner',{f'west-420-{i}' for i in range(1,5)},2,0,
    'ratner-albion-before',scene_counts=(547,{420:4}))
check_register('albion',{f'west-421-{i}' for i in range(1,4)},2,0,
    'ratner-albion-before',later_registers=['ratner'],scene_counts=(546,{421:3}))
scene=load('docs/data/factory-buildings.json')
models={b['id']:b for b in scene['buildings']}
ratner=load('data/maps/ratner-footprint-alignment.json')
albion=load('data/maps/albion-footprint-alignment.json')
ratner_body=unary_union([Polygon(models[f'west-420-{i}']['footprint']) for i in range(1,5)])
assert not ratner_body.covers(Point(-911,185)), 'Ratner court filled'
north=Polygon(models['west-421-1']['footprint'])
south=unary_union([Polygon(models[f'west-421-{i}']['footprint']) for i in [2,3]])
assert north.distance(south)>3.7, 'Albion passage closed'
assert len(albion['removedBuildings'])==len(albion['removedStructures'])==1
for key, runtime, removed_id in [('removedBuildings','reclassifiedFeatures','west-421-4'),
                                ('removedStructures','reclassifiedStructures','west-421-4-stack')]:
    row=albion[key][0]
    assert row['id']==removed_id and row['review']
    assert next(r for r in scene[runtime] if r.get('id')==removed_id)==row
assert 'west-421-4' not in models
assert 'west-421-4-stack' not in {s['id'] for s in scene['structures']}
later=later_reviews(scene,'albion')
added=[s for r in later for s in r.get('additionalStructures',[]) if s['kind']=='chimney']
removed=[s for r in later for s in r.get('removedStructures',[]) if s['kind']=='chimney']
assert scene['counts']['chimneys']==89+len(added)-len(removed)
assert scene['counts']['chimneysWithMappedHeights']==20+sum('mappedHeightFeet' in s for s in added)-sum('mappedHeightFeet' in s for s in removed)
stack=next(s for s in scene['structures'] if s['id']=='west-420-3-stack')
c=ratner['structures'][0]
assert stack['height']==c['preservedHeight']==28 and stack['radius']==1.2
assert math.dist([stack['x'],stack['z']],c['centre'])<.001
assert stack['parentBuildingId']=='west-420-3' and 'sourceFootprintFid' not in stack
assert Polygon(models['west-420-3']['footprint']).covers(Point(stack['x'],stack['z']).buffer(stack['radius']*1.2))
print('Ratner/Albion: seven source-linked ranges, two open courts, contained inferred chimney and evidence-backed building/chimney removal pass.')
