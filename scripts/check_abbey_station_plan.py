"""Check Abbey Mills' rendered body dimensions against its source-linked plan."""
import json,math
from pathlib import Path
from shapely.geometry import Polygon,box,Point
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
print(f'Abbey Mills: {fit:.1%} main-body/boiler outline agreement, source-linked chimney centres, no water intrusion.')
