"""Derive Abbey's supporting ranges and access routes from saved source evidence."""
import json
import math
from pathlib import Path

from pyproj import Transformer
from shapely import affinity
from shapely.geometry import Polygon
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]


def build_support():
    raw = json.loads((ROOT/'data/maps/abbey-supporting-buildings.json').read_text())
    buildings = []
    for row in raw['buildings']:
        polygons = [Polygon(r[0], r[1:]) for r in row['sourcePolygons']]
        footprint = unary_union(polygons)
        centre = footprint.centroid
        corners = list(footprint.minimum_rotated_rectangle.exterior.coords)
        a, b = max(zip(corners, corners[1:]), key=lambda pair: math.dist(*pair))
        angle = math.degrees(math.atan2(b[1]-a[1], b[0]-a[0])) % 180
        local = affinity.rotate(affinity.translate(footprint, -centre.x, -centre.y), -angle, origin=(0, 0))
        x0, z0, x1, z1 = local.bounds
        buildings.append({
            **row, 'siteId': 'abbey-support', 'x': centre.x, 'z': centre.y,
            'rotation': angle, 'localBounds': [[x0, z0], [x1, z1]],
            'width': x1-x0, 'depth': z1-z0, 'roofAxis': 'x', 'roofBays': 1,
            'baseHeight': .12, 'material': 'brick',
            'footprint': list(map(list, polygons[0].exterior.coords))[:-1],
            'renderPolygons': [{'outer': list(map(list, p.exterior.coords))[:-1],
                                'holes': [list(map(list, h.coords))[:-1] for h in p.interiors]}
                               for p in polygons],
            'evidence': raw['evidence'],
        })
    registration = raw['pathRegistration']
    project = Transformer.from_crs(3857, 27700, always_xy=True)
    world_size = registration['tileSize'] * 2**registration['zoom']
    circumference = 2 * math.pi * 6378137

    def world(pixel):
        gx = registration['tileX']*registration['tileSize'] + pixel[0]
        gy = registration['tileY']*registration['tileSize'] + pixel[1]
        e, n = project.transform((gx/world_size-.5)*circumference, (.5-gy/world_size)*circumference)
        return [round(e-538900, 3), round(183209-n, 3)]

    paths = [{**p, 'sheet': 'scene', 'pixelWidth': 1,
              'points': [world(pt) for pt in p['mosaicPixels']],
              'surfaceEvidence': p['evidence']} for p in raw['paths']]
    return buildings, paths, raw['replaceRoadNames']


def station_footprints(plan):
    """Shared exclusion geometry for roads, yards, trees and housing plots."""
    return unary_union([Polygon(plan['worldFootprint']),
                        *[Polygon(c['worldFootprint']) for c in plan['chimneys']],
                        *[Polygon(p['outer'], p['holes']) for b in plan['supportingBuildings']
                          for p in b['renderPolygons']]])
