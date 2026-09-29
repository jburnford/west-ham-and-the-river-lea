"""Build the district's individually registered factory ranges and evidence audit.

No building is generated from an industrial parcel. Every range has an authored
map envelope; elevation and roof assumptions remain separate from that evidence.
"""
import json
import math
from pathlib import Path

import numpy as np
from shapely import set_precision
from shapely.geometry import Polygon, Point, LineString
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]


def footprint(row, source):
    if 'worldFootprint' in row:
        return np.array(row['worldFootprint'])
    if 'footprintPixels' in row:
        points = np.array(row['footprintPixels'])
    else:
        x, y, w, h, angle = row['rectPixels']
        theta = math.radians(angle)
        rotation = np.array([[math.cos(theta), -math.sin(theta)],
                             [math.sin(theta), math.cos(theta)]])
        points = np.array([[-w/2, -h/2], [w/2, -h/2], [w/2, h/2], [-w/2, h/2]]) @ rotation.T + [x, y]
    a, b, x, z = source['pixelToWorld']
    return points @ np.array([[a, b], [-b, a]]) + [x, z] + row.get('placementOffset', [0, 0])


def build():
    raw = json.loads((ROOT/'data/maps/factory-building-traces.json').read_text())
    western = json.loads((ROOT/'data/maps/west-bank-industry.json').read_text())
    western_ids = {s['id'] for s in western['sites']}
    raw['sources']['os-west-bank-1893'] = {
        **raw['sources']['os-1893'],
        'registration': 'Georeferenced NLS tiles, with individually recorded source-frame pixels and world footprints in west-bank-industry.json.',
        'frames': western['frames']}
    raw['sites'] += [{k:v for k,v in s.items() if k!='polygons'} for s in western['sites']]
    raw['buildings'] += western['buildings']
    raw['structures'] += western['structures']
    raw['excludedSites'] = [s for s in raw['excludedSites'] if s['id'] not in western_ids]
    for site in raw['excludedSites']:
        if site['reason']=='West of Old Lea':
            site['reason']='Outside the added Three Mills–main-line western riverside corridor'
    raw['scope'] += '; western Old Lea industrial frontage from Three Mills to the railway'
    raw['scopeNotes'].append(western['scope']+' '+western['evidence'])
    plan = json.loads((ROOT/'docs/data/ground-plan.json').read_text())
    west = json.loads((ROOT/'data/maps/factory-west-context.json').read_text())
    west['sites'] = western['sites']
    water = unary_union([Polygon(p[0], p[1:]) for r in plan['rivers'] + west['rivers'] for p in r['polygons']])
    street_traces = json.loads((ROOT/'data/maps/district-road-traces.json').read_text())
    streets = unary_union([LineString(r['points']).buffer(r['width']/2+1.1, cap_style=2, join_style=2) for r in street_traces['roads']])
    old = json.loads((ROOT/'data/maps/city-mills-building-register.json').read_text())
    exact = {p['id']: p['footprintPixels'] for b in old['buildings'] for p in b.get('parts', [])}
    alignment = json.loads((ROOT/'data/maps/factory-footprint-alignment.json').read_text())
    aligned = {b['modelId']: b for b in alignment['buildings']}
    raw['sources']['author-os-footprints-1891-96'] = {
        'file': alignment['source'], 'registration': alignment['sourceCRS'],
        'method': alignment['method']}
    buildings, polys, water_checks = [], [], []
    for row in raw['buildings']:
        row = dict(row)
        if row['id'] in exact:
            row['footprintPixels'] = exact[row['id']]
        correction = aligned.get(row['id'])
        if correction:
            row.update(worldFootprint=correction['worldFootprint'], priorFootprint=correction['priorFootprint'],
                       priorRotation=correction['priorRotationDegrees'],
                       footprintSource='author-os-footprints-1891-96', sourceFootprintFid=correction['sourceFid'],
                       footprintAlignment=correction['comparison'], priorFootprintEvidence=row['footprintEvidence'],
                       footprintEvidence=correction['review'],
                       eavesHeight=correction['preservedHeight'], roofRise=correction['preservedRoofRise'],
                       roofBays=correction['preservedRoofBays'], roofAxis=correction['preservedRoofAxis'])
        points = footprint(row, raw['sources'][row['source']])
        polygon = Polygon(points)
        assert polygon.is_valid and polygon.area > 2, row['id']
        centre = polygon.centroid
        # First map edge fixes orientation. Roof divisions are modelling choices,
        # not an assertion that an insurance compartment had a separate roof.
        edge = points[1] - points[0]
        angle = math.radians(correction['footprintRotationDegrees']) if correction else math.atan2(edge[1], edge[0])
        along, across = np.array([math.cos(angle), math.sin(angle)]), np.array([-math.sin(angle), math.cos(angle)])
        local = (points - [centre.x, centre.y]) @ np.array([along, across]).T
        low, high = local.min(axis=0), local.max(axis=0)
        mark = row.get('floorMark')
        storeys = row.get('storeysEstimate', {'1': 1, '1½': 1.5, '1=2': 1.5, '2': 2, '3': 3, '4': 4}.get(mark, 1))
        height = row.get('eavesHeight', 3.8 + (storeys-1)*3.1)
        width, depth = high-low
        roof_axis = row.get('roofAxis', 'x' if width >= depth else 'z')
        span = depth if roof_axis == 'x' else width
        bays = row.get('roofBays', max(1, math.ceil(span/17)))
        rise = row.get('roofRise', min(4.5, max(1.0, span/bays*.27)))
        item = {**row, 'footprint': points.round(3).tolist(), 'x': round(centre.x, 3), 'z': round(centre.y, 3),
                'rotation': round(math.degrees(angle), 4), 'localBounds': [low.tolist(), high.tolist()],
                'width': round(width, 3), 'depth': round(depth, 3), 'storeys': storeys,
                'height': height, 'roofRise': rise, 'roofAxis': roof_axis, 'roofBays': bays,
                'areaM2': round(polygon.area, 2)}
        buildings.append(item)
        polys.append(polygon)
        wet = polygon.intersection(water).area
        if wet > 1:
            water_checks.append({'id': row['id'], 'areaM2': round(wet, 2),
                                 'fraction': round(wet/polygon.area, 3),
                                 'review': row.get('waterReview', 'Registration/bank comparison required')})
    ids = [b['id'] for b in buildings]
    assert len(ids) == len(set(ids)), 'Duplicate range ID'
    site_ids = {s['id'] for s in raw['sites']}
    assert {b['siteId'] for b in buildings} == site_ids, 'Every surveyed factory must have ranges'
    assert not site_ids.intersection({s['id'] for s in raw['excludedSites']})
    # Rounded envelopes sometimes intersect at a shared wall. Partition that
    # volume once, retaining both source records and every alteration's area.
    # Taller ranges take precedence so a low annexe cannot cut away a warehouse.
    live_holders = raw['holders'] + [h for h in plan['neighbourhood']['holders'] if h['siteId'] != 924]
    occupied = unary_union([Point(h['x'], h['z']).buffer(h['radius']+.4, resolution=32) for h in live_holders])
    render_polys = [None] * len(buildings)
    adjustments = []
    for i in sorted(range(len(buildings)), key=lambda i: (-buildings[i]['height'], polys[i].area, buildings[i]['id'])):
        b, original = buildings[i], polys[i]
        q = original.difference(water.buffer(.12)) if b.get('bankTrim') else original
        street_cut = q.intersection(streets).area
        if street_cut > .1:
            b['streetTrimAreaM2'] = round(street_cut, 2)
            b['streetTrimEvidence'] = 'Registered 1893 OS street and pavement corridor takes precedence over the approximate range envelope; source footprint retained.'
        q = set_precision(q.difference(streets).difference(occupied), .001)
        if not q.is_empty:
            occupied = occupied.union(q)
        parts = [p for p in getattr(q, 'geoms', [q]) if p.geom_type == 'Polygon' and p.area > .1]
        render_polys[i] = unary_union(parts)
        b['renderPolygons'] = [{'outer': np.array(p.exterior.coords)[:-1].round(3).tolist(),
                                'holes': [np.array(r.coords)[:-1].round(3).tolist() for r in p.interiors]} for p in parts]
        b['renderAreaM2'] = round(sum(p.area for p in parts), 2)
        if original.area - b['renderAreaM2'] > 1:
            adjustments.append({'id': b['id'], 'sourceAreaM2': round(original.area, 2),
                                'renderAreaM2': b['renderAreaM2'], 'bankTrim': b.get('bankTrim', False),
                                'streetTrimAreaM2': b.get('streetTrimAreaM2', 0),
                                'reason': 'Clear registered 1893 street corridors; partition rounded overlapping envelopes, clear mapped holder rings, and apply explicitly flagged shoreline trims.'})
    overlaps = []
    for i, a in enumerate(polys):
        for j in range(i):
            b = polys[j]
            if a.intersects(b):
                area = a.intersection(b).area
                if area > 3 and area/min(a.area, b.area) > .12:
                    overlaps.append({'a': ids[i], 'b': ids[j], 'areaM2': round(area, 2),
                                     'fractionOfSmaller': round(area/min(a.area, b.area), 2)})
    sites = [{**s, 'buildingCount': sum(b['siteId'] == s['id'] for b in buildings)} for s in raw['sites']]
    for holder in raw['holders']:
        p = Point(holder['x'], holder['z']).buffer(holder['radius'])
        assert p.intersection(water).area < 1, holder['id']
        assert not any(p.intersection(q).area > 1 for q in polys), holder['id']
    result = {k: raw[k] for k in ['schemaVersion', 'date', 'scope', 'method', 'sources', 'scopeNotes', 'excludedSites', 'retainedLandmarks', 'structures', 'holders']}
    structures = []
    for row in raw['structures']:
        item = dict(row)
        if 'parentBuildingId' in row:
            parent = next(b for b in buildings if b['id'] == row['parentBuildingId'])
            u, v = row['localPosition']
            angle = math.radians(parent['rotation'])
            item.update(x=round(parent['x']+u*math.cos(angle)-v*math.sin(angle), 3),
                        z=round(parent['z']+u*math.sin(angle)+v*math.cos(angle), 3),
                        rotation=parent['rotation'])
        if 'pixelPosition' in row:
            u, v = row['pixelPosition']
            a, b, x, z = raw['sources'][row['source']]['pixelToWorld']
            item.update(x=round(a*u-b*v+x, 3), z=round(b*u+a*v+z, 3))
        structures.append(item)
    chimneys = [s for s in structures if s['kind'] == 'chimney']
    result['structures'] = structures
    result['footprintAlignment'] = {'matchedRanges': len(aligned), 'source': alignment['source'], 'register': 'data/maps/factory-footprint-alignment.json'}
    result['symbolKeys'] = raw.get('symbolKeys', {})
    result.update(sites=sites, buildings=buildings, counts={'sites': len(sites), 'ranges': len(buildings),
                  'chimneys': len(chimneys), 'chimneysWithMappedHeights': sum('mappedHeightFeet' in s for s in chimneys),
                  'bromleyHolders': len(raw['holders']), 'retainedLandmarks': len(raw['retainedLandmarks'])})
    result['westContext'] = west
    (ROOT/'docs/data/factory-buildings.json').write_text(json.dumps(result, separators=(',', ':'))+'\n')
    final_wet = [{'id': b['id'], 'areaM2': round(q.intersection(water).area, 2), 'review': b.get('waterReview')}
                 for b, q in zip(buildings, render_polys) if q.intersection(water).area > 1]
    audit = {'counts': result['counts'], 'sourceWaterIntersections': water_checks, 'sourceRangeOverlaps': overlaps,
             'renderAdjustments': adjustments, 'waterIntersections': final_wet,
             'fullyCoveredRanges': [b['id'] for b in buildings if not b['renderPolygons']]}
    out = ROOT/'reference/factory-building-survey/review'
    out.mkdir(parents=True, exist_ok=True)
    (out/'geometry-audit.json').write_text(json.dumps(audit, indent=2)+'\n')
    print(json.dumps({'counts': result['counts'], 'waterChecks': len(water_checks), 'overlapChecks': len(overlaps)}))


if __name__ == '__main__':
    build()
