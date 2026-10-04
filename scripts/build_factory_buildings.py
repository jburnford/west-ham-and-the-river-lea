"""Build the district's individually registered factory ranges and evidence audit.

No building is generated from an industrial parcel. Every range has an authored
map envelope; elevation and roof assumptions remain separate from that evidence.
"""
import json
import math
from pathlib import Path

import numpy as np
from shapely import set_precision
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
from factory_street_clearance import street_clearances

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
    streets, frontage_streets = street_clearances(street_traces['roads'])
    old = json.loads((ROOT/'data/maps/city-mills-building-register.json').read_text())
    exact = {p['id']: p['footprintPixels'] for b in old['buildings'] for p in b.get('parts', [])}
    alignment = json.loads((ROOT/'data/maps/factory-footprint-alignment.json').read_text())
    aligned = {b['modelId']: b for b in alignment['buildings']}
    group_registers = ['data/maps/ink-works-footprint-alignment.json', 'data/maps/sawmill-footprint-alignment.json',
                       'data/maps/oil-wharf-footprint-alignment.json', 'data/maps/howards-footprint-alignment.json',
                       'data/maps/sugar-house-footprint-alignment.json', 'data/maps/west-sugar-footprint-alignment.json',
                       'data/maps/crystal-barber-footprint-alignment.json', 'data/maps/abbey-west-footprint-alignment.json',
                       'data/maps/bow-works-footprint-alignment.json', 'data/maps/hunt-works-footprint-alignment.json',
                       'data/maps/lascelles-ultramarine-footprint-alignment.json',
                       'data/maps/williams-asphalte-footprint-alignment.json',
                       'data/maps/refinery-printing-footprint-alignment.json',
                       'data/maps/kendrick-usher-footprint-alignment.json',
                       'data/maps/three-mills-north-footprint-alignment.json',
                       'data/maps/three-mills-south-footprint-alignment.json',
                       'data/maps/three-mills-landmark-footprint-alignment.json',
                       'data/maps/ratner-footprint-alignment.json',
                       'data/maps/albion-footprint-alignment.json',
                       'data/maps/bow-flour-footprint-alignment.json',
                       'data/maps/rubber-felt-footprint-alignment.json',
                       'data/maps/cook-soap-footprint-alignment.json',
                       'data/maps/bow-magnet-footprint-alignment.json',
                       'data/maps/lime-works-footprint-alignment.json',
                       'data/maps/mill-brush-footprint-alignment.json',
                       'data/maps/bow-brewery-footprint-alignment.json',
                       'data/maps/mineral-water-footprint-alignment.json',
                       'data/maps/jeffrey-glue-footprint-alignment.json',
                       'data/maps/marshgate-chemical-footprint-alignment.json',
                       'data/maps/alderson-rope-footprint-alignment.json',
                       'data/maps/ritchie-jute-footprint-alignment.json',
                       'data/maps/crown-johnson-footprint-alignment.json',
                       'data/maps/western-trades-footprint-alignment.json',
                       'data/maps/east-channelsea-south-footprint-alignment.json',
                       'data/maps/east-channelsea-upper-footprint-alignment.json',
                       'data/maps/east-channelsea-north-footprint-alignment.json',
                       'data/maps/bromley-gasworks-footprint-alignment.json',
                       'data/maps/leather-cloth-footprint-alignment.json',
                       'data/maps/berger-starch-footprint-alignment.json']
    compounds = [json.loads((ROOT/path).read_text()) for path in group_registers]
    structure_alignment = {}
    map_traces = {}
    direct_ids, local_ids = set(), set()
    for register in compounds:
        additions = register.get('additionalSites', [])
        assert not {s['id'] for s in raw['sites']}.intersection(s['id'] for s in additions), 'Duplicate added site'
        raw['sites'].extend(additions)
        added_sites = {s['id'] for s in additions}
        raw['excludedSites'] = [s for s in raw['excludedSites'] if s['id'] not in added_sites]
        for id in register.get('supersedesLocalTransfers', []):
            assert id in local_ids, 'Superseded local transfer must exist'
            local_ids.remove(id)
            map_traces.pop(id)
        map_traces.update({b['modelId']: b for b in register.get('mapTracedBuildings', []) + register.get('locallyTransferredBuildings', [])})
        direct_ids.update(b['modelId'] for b in register.get('mapTracedBuildings', []))
        local_ids.update(b['modelId'] for b in register.get('locallyTransferredBuildings', []))
        removed = {b['id'] for b in register.get('removedBuildings', [])}
        raw['buildings'] = [b for b in raw['buildings'] if b['id'] not in removed] + register.get('additionalBuildings', [])
        raw.setdefault('reclassifiedFeatures', []).extend(register.get('removedBuildings', []))
        removed_structures = {s['id'] for s in register.get('removedStructures', [])}
        assert removed_structures <= {s['id'] for s in raw['structures']}, 'Unknown removed structure'
        raw['structures'] = [s for s in raw['structures'] if s['id'] not in removed_structures]
        raw.setdefault('reclassifiedStructures', []).extend(register.get('removedStructures', []))
        fitted_plant = register.get('tanks', []) + register.get('mappedPlants', [])
        raw['structures'] = [s for s in raw['structures'] if s['id'] not in {t['id'] for t in fitted_plant}] + fitted_plant
        raw['structures'] += register.get('additionalStructures', [])
        for move in register.get('holderAdjustments', []):
            holder = next(h for h in raw['holders'] if h['id'] == move['id'])
            holder.update(x=move['x'], z=move['z'], positionEvidence=move['positionEvidence'])
        assert not set(aligned).intersection(b['modelId'] for b in register['buildings'])
        assert not set(structure_alignment).intersection(s['id'] for s in register['structures'])
        aligned.update({b['modelId']: b for b in register['buildings']})
        structure_alignment.update({s['id']: s for s in register['structures']})
    if any(r.get('additionalSites') for r in compounds):
        raw['scope'] += '; reviewed industrial roofs between Channelsea and the Woolwich railway'
        raw['scopeNotes'].append('Eastern strip roof exteriors follow the OS plan and supplied footprints; new heights, storeys and roof forms remain explicit estimates without asserted Goad coverage.')
    raw['sources']['author-os-footprints-1891-96'] = {
        'file': alignment['source'], 'registration': alignment['sourceCRS'],
        'method': ' '.join([alignment['method'], *[r['method'] for r in compounds]])}
    buildings, polys, water_checks = [], [], []
    for row in raw['buildings']:
        row = dict(row)
        if row['id'] in exact:
            row['footprintPixels'] = exact[row['id']]
        if row['id'] in map_traces:
            row.update({k:v for k,v in map_traces[row['id']].items() if k != 'modelId'})
        correction = aligned.get(row['id'])
        if correction:
            if 'waterInterface' in correction:
                assert correction.get('waterReview') and not row.get('bankTrim')
                row.update(waterInterface=correction['waterInterface'],waterReview=correction['waterReview'])
            if 'landmarkDetails' in correction:
                row['landmarkDetails'] = correction['landmarkDetails']
            if 'priorSiteId' in correction:
                assert row['siteId']==correction['priorSiteId']
                row.update(siteId=correction['siteId'], priorSiteId=correction['priorSiteId'],
                           siteAttributionEvidence=correction['siteAttributionEvidence'])
            row.update(name=correction['name'], worldFootprint=correction['worldFootprint'], priorFootprint=correction['priorFootprint'],
                       priorRotation=correction['priorRotationDegrees'],
                       footprintSource='author-os-footprints-1891-96',
                       footprintAlignment=correction['comparison'], priorFootprintEvidence=row['footprintEvidence'],
                       footprintEvidence=correction['review'],
                       eavesHeight=correction['preservedHeight'], roofRise=correction['preservedRoofRise'],
                       roofBays=correction['preservedRoofBays'], roofAxis=correction['preservedRoofAxis'])
            if 'sourceFid' in correction:
                row['sourceFootprintFid'] = correction['sourceFid']
            if 'groupId' in correction:
                row.update(sourceFootprintFids=correction['sourceFids'], footprintGroup=correction['groupId'],
                           worldHoles=correction['worldHoles'])
        points = footprint(row, raw['sources'][row['source']])
        polygon = Polygon(points, row.get('worldHoles', []))
        assert polygon.is_valid and polygon.area > 2, row['id']
        centre = polygon.centroid
        # First map edge fixes orientation. Roof divisions are modelling choices,
        # not an assertion that an insurance compartment had a separate roof.
        edge = points[1] - points[0]
        if correction:
            angle = math.radians(correction['footprintRotationDegrees'])
        elif 'footprintRotationDegrees' in row:
            angle = math.radians(row['footprintRotationDegrees'])
        else:
            angle = math.atan2(edge[1], edge[0])
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
    assert set(frontage_streets)<=set(ids), 'Unknown frontage-clearance model'
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
        street_exclusion = frontage_streets.get(b['id'],streets)
        q = original.difference(water.buffer(.12)) if b.get('bankTrim') else original
        street_cut = q.intersection(street_exclusion).area
        if street_cut > .1:
            b['streetTrimAreaM2'] = round(street_cut, 2)
            b['streetTrimEvidence'] = 'Registered 1893 OS street and pavement corridor takes precedence over the approximate range envelope; source footprint retained.'
        q = set_precision(q.difference(street_exclusion).difference(occupied), .001)
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
        if item['id'] in structure_alignment:
            correction = structure_alignment[item['id']]
            item.update(x=round(correction['centre'][0], 3), z=round(correction['centre'][1], 3),
                        rotation=correction['rotation'], priorPosition=correction['priorCentre'],
                        priorPositionEvidence=item['positionEvidence'], positionEvidence=correction['review'])
            if 'sourceFid' in correction:
                item.update(sourceFootprintFid=correction['sourceFid'], sourcePolygons=correction['sourcePolygons'])
            if 'radius' in correction:
                item.update(radius=correction['radius'], priorRadius=correction['priorRadius'],
                            profileEvidence=correction['profileEvidence'])
            if 'parentBuildingId' in correction:
                item.update(parentBuildingId=correction['parentBuildingId'], parentFractions=correction['parentFractions'])
        structures.append(item)
    chimneys = [s for s in structures if s['kind'] == 'chimney']
    result['structures'] = structures
    result['reclassifiedFeatures'] = raw.get('reclassifiedFeatures', [])
    result['reclassifiedStructures'] = raw.get('reclassifiedStructures', [])
    result['footprintAlignment'] = {'matchedRanges': len(aligned), 'source': alignment['source'],
        'register': 'data/maps/factory-footprint-alignment.json',
        'groupRegisters': group_registers, 'reviewedGroups': sum(len(r['groups']) for r in compounds),
        'directMapTraces': len(direct_ids),
        'locallyTransferredRanges': len(local_ids),
        'groupTransferredChimneys': sum('transferGroup' in s and 'sourceFid' not in s for s in structure_alignment.values()),
        'matchedChimneyBases': sum('sourceFid' in s for s in structure_alignment.values()),
        'parentTransferredChimneys': sum('parentBuildingId' in s for s in structure_alignment.values())}
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
