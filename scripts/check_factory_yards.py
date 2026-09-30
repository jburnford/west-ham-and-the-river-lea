"""Check that interpreted yard detail preserves mapped clearances."""
import json
import math
from pathlib import Path
from shapely.geometry import Polygon, Point, LineString
from shapely.ops import unary_union
from shapely.affinity import rotate,translate
from abbey_support import station_footprints

ROOT = Path(__file__).resolve().parents[1]
def load(name):
    return json.loads((ROOT/'docs/data'/name).read_text())
def polygons(rows):
    return unary_union([Polygon(p[0], p[1:]) for p in rows])

yards = load('factory-yards.json')
plan = load('ground-plan.json')
factories = load('factory-buildings.json')
frontages = load('high-street-frontages.json')
infra = load('infrastructure.json')
buildings = unary_union([Polygon(p['outer'], p['holes'])
    for b in factories['buildings'] + frontages['buildings'] for p in b['renderPolygons']])
buildings = buildings.union(station_footprints(load('abbey-station-plan.json')))
water = unary_union([polygons(r['polygons'])
    for r in plan['rivers'] + factories['westContext']['rivers']])
roads = unary_union([LineString(r['route']).buffer(r['width']/2, cap_style=2)
    for r in infra['roads']])
holders = unary_union([Point(h['x'], h['z']).buffer(h['radius'])
    for h in factories['holders'] + [h for h in plan['neighbourhood']['holders'] if h['siteId'] != 924]])
chimneys = unary_union([Point(s['x'],s['z']).buffer(s['radius']*1.2)
    for s in factories['structures'] if s['kind']=='chimney'])
tanks = unary_union([Point(s['x'],s['z']).buffer(s['radius'])
    for s in factories['structures'] if s['kind'] in {'tank','kiln'}])
blocked = unary_union([buildings, water, roads, holders, chimneys, tanks])
used = Polygon()
stocks = routes = 0
for site in yards['sites']:
    surface = polygons(site['polygons'])
    assert surface.is_valid and surface.area > 0, site['id']
    assert surface.intersection(blocked).area < .05, ('blocked surface', site['id'])
    assert surface.intersection(used).area < .05, ('overlapping surfaces', site['id'])
    used = used.union(surface)
    stock_footprints=[]
    for route in site['wearRoutes']:
        assert surface.buffer(.03).covers(LineString(route)), ('wear route', site['id'])
        routes += 1
    for stock in site['stock']:
        # Largest group is the timber/coal stack: conservative bounding circle.
        footprint = Polygon(stock['footprint']) if 'footprint' in stock else Point(stock['x'], stock['z']).buffer(2.05)
        if stock['kind'] in ['deals','boards']:
            # Reconstruct the renderer's conservative rectangular extents and
            # rotation, independently of the placement footprint in the data.
            length,width=stock['length'],stock['width']
            rectangle=Polygon([[-length/2-.06,-width/2-.06],[length/2+.06,-width/2-.06],
                               [length/2+.06,width/2+.06],[-length/2-.06,width/2+.06]])
            actual=translate(rotate(rectangle,-math.degrees(stock['angle']),origin=(0,0)),stock['x'],stock['z'])
            assert footprint.buffer(.002).covers(actual), ('stack bounds',site['id'])
            assert all(footprint.distance(other)>2 for other in stock_footprints), 'Timber working aisle obstructed'
        stock_footprints.append(footprint)
        assert surface.covers(footprint), ('stock outside yard', site['id'])
        assert footprint.intersection(blocked).area < .001, ('stock obstruction', site['id'])
        assert all(footprint.distance(LineString(r)) > .9 for r in site['wearRoutes']), ('stock in circulation', site['id'])
        stocks += 1
assert stocks == yards['counts']['stockGroups']
assert routes == yards['counts']['wearRoutes']
sawmill=next(s for s in yards['sites'] if s['id']==797)
sawmill_surface=polygons(sawmill['polygons'])
assert sawmill_surface.bounds[0]<-1190, 'Sawmill parcel still clipped at former scene boundary'
for track in yards['tracks']:
    route=LineString(track['points'])
    assert route.buffer(.95).intersection(blocked).area<.01, ('Track obstruction',track['id'])
    track_surface=polygons(next(s for s in yards['sites'] if s['id']==track.get('siteId',797))['polygons'])
    assert track_surface.buffer(.02).covers(route), ('Track outside its mapped yard',track['id'])
    if 'sourceTrackId' in track:
        assert track['gauge']==1.435 and track['sleeperWidth']==2.4
    assert all(Polygon(s['footprint']).distance(route)>2.9 for s in sawmill['stock']), ('Timber obstructs track',track['id'])
assert 'oilwharf-6' not in {b['id'] for b in factories['buildings']}, 'Yard track misclassified as building'
print(f"{len(yards['sites'])} valid yard surfaces, {routes} clear wear routes, {stocks} stock groups; mapped roads, buildings, water and holders clear.")
