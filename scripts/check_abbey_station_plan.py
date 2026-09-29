"""Check Abbey Mills' rendered body dimensions against its source-linked plan."""
import json,math
from pathlib import Path
from shapely.geometry import Polygon,box,Point,LineString
from shapely import affinity
from shapely.ops import unary_union
ROOT=Path(__file__).resolve().parents[1]
p=json.loads((ROOT/'docs/data/abbey-station-plan.json').read_text())
def world(g):return affinity.translate(affinity.rotate(g,p['angleDegrees'],origin=(0,0)),*p['centre'])
L,D=p['mainLength'],p['crossLength'];a,b=p['mainDepth'],p['crossWidth'];dz=p['mainOffsetZ']
parts=[box(-L/2,dz-a/2,L/2,dz+a/2),box(-b/2,-D/2,b/2,D/2)]
for w in p['boilerWings']:parts.append(box(w['x']-w['width']/2,w['z']-w['depth']/2,w['x']+w['width']/2,w['z']+w['depth']/2))
body=world(unary_union(parts));outline=Polygon(p['worldFootprint']);source=unary_union([Polygon(r[0],r[1:]) for r in p['sourcePolygons']])
assert body.symmetric_difference(outline).area<.12
fit=body.intersection(source).area/body.union(source).area
assert fit>.95 and fit>p['fit']['previousIoU']
assert len(p['chimneys'])==2
for c in p['chimneys']:
 assert Polygon(c['worldFootprint']).centroid.distance(Point(c['centre']))<.002
 assert not body.intersects(Polygon(c['worldFootprint']))
plan=json.loads((ROOT/'docs/data/ground-plan.json').read_text())
water=unary_union([Polygon(r[0],r[1:]) for feature in plan['rivers'] for r in feature['polygons']])
assert body.intersection(water).area<.01,'Station obstructs water'
author=json.loads((ROOT/'data/maps/abbey-supporting-buildings.json').read_text())
expected={b['sourceFid']:b for b in author['buildings']}
support=p['supportingBuildings']
assert len(support)==len(expected)==12
assert {b['sourceFid'] for b in support}==set(expected)
ditches=json.loads((ROOT/'docs/data/river-network.json').read_text())['marshDitches']
water=water.union(unary_union([Polygon(r[0],r[1:]) for f in ditches['features'] for r in f['renderPolygons']]))
occupied=[body,*[Polygon(c['worldFootprint']) for c in p['chimneys']]]
for b in support:
 rendered=unary_union([Polygon(r['outer'],r['holes']) for r in b['renderPolygons']])
 source=unary_union([Polygon(r[0],r[1:]) for r in expected[b['sourceFid']]['sourcePolygons']])
 assert rendered.is_valid and rendered.symmetric_difference(source).area<.001,b['id']
 assert rendered.intersection(water).area<.001,('Water intrusion',b['id'])
 assert all(rendered.intersection(other).area<.01 for other in occupied),('Overlapping volumes',b['id'])
 occupied.append(rendered)
 # Roof planes in the shared factory renderer cover precisely these local bounds.
 local=affinity.rotate(affinity.translate(rendered,-b['x'],-b['z']),-b['rotation'],origin=(0,0))
 lo,hi=b['localBounds']
 assert local.difference(box(*lo,*hi).buffer(.001)).area<.001,b['id']
 assert b['height']>0 and b['roofRise']>0 and b['roofBays']==1
 if b.get('parentSourceFid'):
  parent=next(x for x in support if x['sourceFid']==b['parentSourceFid'])
  assert b['height']<parent['height']
  assert rendered.distance(Polygon(parent['footprint']))<1
occupied=unary_union(occupied)
infra=json.loads((ROOT/'docs/data/infrastructure.json').read_text())
surfaces=unary_union([Polygon(t) for key in ['roadTriangles','shoulderTriangles','pathTriangles'] for t in infra[key]])
assert surfaces.intersection(occupied).area<.01,'Road surface through station buildings'
paths={r['name']:r for r in p['accessPaths']}
assert len(paths)==5
actual=[r for r in infra['roads'] if r['name'] in paths]
assert len(actual)==5,'Missing or duplicated station routes'
for r in actual:
 assert LineString(r['route']).hausdorff_distance(LineString(paths[r['name']]['points']))<.01
 assert LineString(r['route']).intersection(occupied).length<.15,('Access through building',r['name'])
 assert LineString(r['route']).buffer(r['width']/2).intersection(water).area<.01,('Access over drain',r['name'])
approach=next(r for r in actual if r['name']=='Pumping station approach')
lane=next(r for r in infra['roads'] if r['name']=='Abbey Lane')
assert Point(approach['route'][0]).distance(LineString(lane['route']))<.2,'Entrance disconnected from Abbey Lane'
for tree in json.loads((ROOT/'docs/data/mapped-trees.json').read_text())['trees']:
 assert not occupied.buffer(1).covers(Point(tree['x'],tree['z'])),'Tree within a station building'
assert json.loads((ROOT/'data/maps/abbey-station-plan.json').read_text())==p,'Stale runtime plan'
print(f'Abbey Mills: {fit:.1%} main-body/boiler agreement; 12 exact source-linked supporting volumes; 5 access routes; clear water, drains, roads and trees.')
