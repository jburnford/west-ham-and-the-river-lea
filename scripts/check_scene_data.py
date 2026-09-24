"""Check spatial invariants that could silently produce a misleading scene."""
import json
from pathlib import Path

from pyproj import Transformer
from shapely.geometry import Point, Polygon, box, LineString
from shapely.affinity import rotate
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT/'docs/data/ground-plan.json').read_text())
assert data['origin']['easting'] == 538900
assert data['origin']['northing'] == 183209
lon, lat = Transformer.from_crs(27700, 4326, always_xy=True).transform(538900, 183209)
assert abs(lon-0.0010593154) < 1e-7 and abs(lat-51.5307115265) < 1e-7


def geometry(feature):
    return unary_union([Polygon(rings[0], rings[1:]) for rings in feature['polygons']])


sites = {f['id']: geometry(f) for f in data['sites']}
for block in data['factoryStudies']:
    x,z,w,d = [block[key] for key in ['x','z','width','depth']]
    # Small tolerance allows for the 0.4 m simplification applied after the containment fit.
    assert sites[block['siteId']].buffer(0.5).covers(box(x-w/2,z-d/2,x+w/2,z+d/2)), block
river = geometry(next(f for f in data['rivers'] if f['id'] == 14))
assert river.distance(Point(0,0)) < 25, 'Bridge anchor must lie near the mapped channel'
assert sites[924].buffer(20).covers(Point(-268,706)), 'Bromley anchor must lie at its gasworks'
context=data['neighbourhood']
assert len(context['houses']) == 4, 'Four pairs, not four individual houses'
assert sum(h['siteId']==924 for h in context['holders']) == 7
assert sum(h['siteId']==873 for h in context['holders']) == 6
for h in context['holders']:
    # Independent map/plan registration and simplified site outlines differ slightly.
    footprint = Point(h['x'],h['z']).buffer(h['radius'])
    assert sites[h['siteId']].buffer(3).covers(footprint), h['id']
for i,h in enumerate(context['holders']):
    for other in context['holders'][i+1:]:
        assert Point(h['x'],h['z']).distance(Point(other['x'],other['z'])) > h['radius']+other['radius'], 'Holder studies must not overlap'
water = unary_union([geometry(f) for f in data['rivers']])
assert len(context['terraces']) == 92
assert context['registrationChecks']['overview']['rmsTargetPixels'] < 2
for row in context['terraces']+context['houses']:
    footprint = Polygon(row['footprint'])
    assert footprint.is_valid and footprint.area > 20
    assert footprint.intersection(water).area < 1, row['id']
    for exclusion in context['housingExclusions']:
        assert footprint.intersection(Polygon(exclusion['footprint'])).area < 1, (row['id'],exclusion['name'])
sewer=context['sewer']
route=LineString(sewer['route'])
assert route.length > 3500 and route.distance(Point(0,0)) < .1
assert sewer['height'] == 7.4
for triangle in sewer['banks']:
    assert all(0 <= y <= 7.4 for x,y,z in triangle)
    footprint=Polygon([(x,z) for x,y,z in triangle])
    assert footprint.intersection(water).area < .1, 'Earth banks must leave waterways open'
assert len(context['railways']) == 3
assert len(context['garden']['beds']) > 20
garden_access=unary_union([LineString(r['route']).buffer(r['width']/2) for r in context['garden']['accessCorridors']])
for bed in context['garden']['beds']:
    x,z=bed['x'],bed['z']
    footprint=box(x-bed['width']/2,z-bed['depth']/2,x+bed['width']/2,z+bed['depth']/2)
    assert footprint.intersection(water).area == 0
    assert footprint.intersection(garden_access).area == 0
for factory in context['mappedFactories']:
    assert Polygon(factory['footprint']).intersection(water).area < 1
mill=context['mill']
footprint=rotate(box(mill['x']-mill['width']/2,mill['z']-mill['depth']/2,mill['x']+mill['width']/2,mill['z']+mill['depth']/2),-mill['rotation'],origin=(mill['x'],mill['z']))
# The enlarged OS mill/crossing reading supersedes the old parcel-fitted anchor.
# Its north edge differs from the independently simplified GIS parcel by 3.54 m.
assert sites[mill['siteId']].buffer(4).covers(footprint)
assert len(data['bankStudies']) == 1
for triangle in data['bankRelief']:
    assert all(0 <= y < 1.2 for x,y,z in triangle), 'Relief must stay within the documented study range'
    footprint = Polygon([(x,z) for x,y,z in triangle])
    assert footprint.intersection(river).area < 0.25, 'Raised bed must not close mapped channels'
for feature in data['rivers'] + data['sites']:
    assert geometry(feature).is_valid, feature['id']
print(f'Geographic checks passed: {len(sites)} sites; {len(data["factoryStudies"])} contained building studies; bridge and gasworks anchors.')
