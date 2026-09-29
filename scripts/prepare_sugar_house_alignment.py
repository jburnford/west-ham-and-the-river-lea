"""Build explicit OS/Goad matches for the cooperage and Winstone compound.

Requires the private source extract and saved pre-alignment snapshot. Routine
scene builds consume the saved register; no nearest-feature selection occurs.
"""
import json
from pathlib import Path
from shapely import affinity, set_precision
from shapely.geometry import Polygon, shape, box
from shapely.ops import unary_union
from prepare_howards_alignment import partition
from prepare_ink_works_alignment import axis, rings
from factory_map_sources import mosaic

ROOT = Path(__file__).resolve().parents[1]
# Exterior matches inspected on OS five-foot mapping and July 1893 Goad F3.
SPECS = [
    ('winstone-main', [1, 3, 4, 6], [1231]),
    ('winstone-south-east', [2], [91401]),
    ('winstone-acid-chamber', [5], [305125, 1075088]),
    ('sugar-house-1882', [7], [13976]),
    ('cooperage-east', [8], [10438, 950788, 952756]),
    ('cooperage-boiler-range', [9], [193674]),
    ('cooperage-beam-and-cellar', [10, 11], [10706]),
    ('cooperage-boiler-room', [12], [832965]),
    ('cooperage-office', [13], [823808, 837886]),
    ('cooperage-sawmill', [15], [4803]),
    ('cooperage-mechanical-shop', [16], [619800]),
]
# Lower compartments present on both maps, omitted by the earlier coarse ranges.
ADDITIONS = [
    ('site964-cooperage-west', 'Cooperage western sawmill, Goad 566', [101293],
     'Goad 566: one-storey sawmill adjoining the cooperage; roof form interpreted.'),
    ('site964-cooperage-stable', 'Cooperage stable, Goad 578', [65393],
     'Goad 578: one-storey stable south of the sawmill; roof form interpreted.'),
    ('site964-cooperage-south', 'Cooperage southern rooms, Goad 580 and eastern annex', [112632, 329600],
     'Goad 580 and adjoining low range: one-storey rooms below the cooperage; exact roof divisions interpreted.'),
]


def build():
    load = lambda p: json.loads((ROOT/p).read_text())
    before = load('reference/footprint-model-alignment/sugar-before.json')
    models = {b['id']: b for b in before['buildings']}
    wanted = {fid for _, _, fids in SPECS for fid in fids}
    wanted.update(fid for _, _, fids, _ in ADDITIONS for fid in fids)
    wanted.add(1142465)  # Boiler chimney opening within the main sawmill outline.
    source = {f['properties']['sourceFid']: affinity.affine_transform(shape(f['geometry']), [1,0,0,-1,-538900,183209])
              for f in load('reference/historic-building-footprints-2026-09-28/current-scene-buildings-bng.geojson')['features']
              if f['properties']['sourceFid'] in wanted}
    specs = [(name, [f'site964-range-{i}' for i in refs], fids) for name, refs, fids in SPECS]
    additional = []
    for id, name, fids, evidence in ADDITIONS:
        target = set_precision(unary_union([source[f] for f in fids]), .001)
        assert target.geom_type == 'Polygon', id
        row = {'id':id, 'siteId':964, 'source':'goad-f3-sugar', 'name':name,
               'worldFootprint':rings(target)[0], 'worldHoles':rings(target)[1:],
               'footprintEvidence':'OS supplied exterior matched by the Goad department position; '+evidence,
               'floorMark':'1', 'eavesHeight':3.8, 'heightEvidence':evidence+' Eaves height 3.8 m is an estimate.',
               'roofEvidence':evidence, 'roofRise':2.2, 'roofBays':1, 'roofAxis':'x', 'material':'brick'}
        additional.append(row)
        models[id] = {**row, 'footprint':row['worldFootprint'], 'height':3.8,
                      'rotation':models['site964-range-8']['rotation']}
        specs.append((id.removeprefix('site964-'), [id], fids))
    groups, corrections = [], []
    for name, ids, fids in specs:
        original = [Polygon(models[id]['footprint']) for id in ids]
        previous = models[ids[0]]['rotation']
        target = set_precision(unary_union([source[f] for f in fids]), .001)
        assert target.geom_type == 'Polygon' and target.is_valid, (name, target.geom_type)
        angle = axis(target, previous)
        division = None
        if name == 'winstone-main':
            # The oblique southern street edge controls the minimum rectangle,
            # but the main factory walls and roofs follow the northern wall.
            angle = -11.60
            local = affinity.rotate(target, -angle, origin=(0,0))
            old_bounds = [affinity.rotate(p, -previous, origin=(0,0)).bounds for p in original]
            old_union = unary_union([affinity.rotate(p, -previous, origin=(0,0)) for p in original]).bounds
            x0,y0,x1,y1 = local.bounds
            def mapped(value, dimension):
                return (x0,y0)[dimension] + (value-old_union[dimension])/(old_union[dimension+2]-old_union[dimension]) * (x1-x0,y1-y0)[dimension]
            west = local.intersection(box(x0-1,y0-1,mapped(old_bounds[2][2],0),y1+1))
            rest = local.difference(west)
            east = rest.intersection(box(mapped(old_bounds[3][0],0),y0-1,x1+1,y1+1))
            rest = rest.difference(east)
            south = rest.intersection(box(x0-1,mapped(old_bounds[1][1],1),x1+1,y1+1))
            parts = [set_precision(affinity.rotate(p,angle,origin=(0,0)),.001) for p in [rest.difference(south),south,west,east]]
            division = 'Retain Goad northern, southern, west and east ranges using prior frontage proportions; main roof axis follows the OS northern wall, not the oblique southern street edge.'
        elif name == 'cooperage-beam-and-cellar':
            # OS 10706 joins differently oriented Goad ranges at this elbow.
            west = target.intersection(box(-1000,-1000,-699.11,1000))
            parts = [set_precision(p,.001) for p in [west,target.difference(west)]]
            division = 'Goad beam house and arched-cellar range meet at the mapped elbow near scene x=-699.11; retain their separate roof directions.'
        else:
            parts = partition(original, target, previous, angle) if len(ids)>1 else [target]
        assert all(p.geom_type == 'Polygon' and p.is_valid and p.area>2 for p in parts), (name, [(p.geom_type,p.area) for p in parts])
        assert unary_union(parts).symmetric_difference(target).area<.15, name
        groupid = 'sugar-'+name
        old = unary_union(original)
        groups.append({'id':groupid, 'modelIds':ids, 'sourceFids':fids,
                       'sourcePolygons':[rings(p) for fid in fids for p in source[fid].geoms],
                       'division':division,
                       'additional':ids[0] in {a['id'] for a in additional},
                       'previousUnionIoU':old.intersection(unary_union([source[f] for f in fids])).area/old.union(unary_union([source[f] for f in fids])).area})
        for id, old, part in zip(ids, original, parts):
            b = models[id]
            member_angle = axis(part, b['rotation']) if name == 'cooperage-beam-and-cellar' else angle
            name_override = {'site964-range-15':'Cooperage banding warehouse and sawmill, Goad 552/554',
                             'site964-range-5':'Winstone printing-ink acid chamber, Goad 594'}
            corrections.append({'modelId':id, 'siteId':964, 'name':name_override.get(id,b['name']),
                'groupId':groupid, 'sourceFids':fids, **({'sourceFid':fids[0]} if len(fids)==1 else {}),
                'worldFootprint':rings(part)[0], 'worldHoles':rings(part)[1:],
                'priorFootprint':rings(old)[0], 'priorRotationDegrees':b['rotation'], 'footprintRotationDegrees':member_angle,
                'preservedHeight':b['height'], 'preservedRoofRise':b['roofRise'], 'preservedRoofAxis':b['roofAxis'], 'preservedRoofBays':b['roofBays'],
                'review':'Explicit OS/Goad F3 exterior match; retain researched height and roof interpretation. '+(groups[-1]['division'] or 'Mapped exterior and openings retained.'),
                'comparison':{'centroidShiftMetres':old.centroid.distance(part.centroid),'areaRatio':part.area/old.area,'axisChangeDegrees':member_angle-b['rotation']}})
    original = next(s for s in before['structures'] if s['id']=='stack-964-1425-3049')
    g = source[1142465]
    chimney = {'id':original['id'], 'sourceFid':1142465, 'sourcePolygons':[rings(p) for p in g.geoms],
               'centre':list(g.centroid.coords)[0], 'rotation':next(b['footprintRotationDegrees'] for b in corrections if b['modelId']=='site964-range-15'),
               'priorCentre':[original['x'],original['z']], 'preservedHeight':original['height'],
               'priorRadius':original['radius'], 'radius':.65,
               'profileEvidence':'Square shaft and crown remain interpreted; radius reduced from 1.05 to 0.65 m so the rendered plinth fits the mapped opening with clearance. Shaft height is unchanged.',
               'review':'Goad sawmill boiler chimney matched to OS base 1142465 inside the source 4803 opening; retain previous shaft height and fit the base within the opening.'}
    seams = []
    for i,a in enumerate(corrections):
        pa = Polygon(a['worldFootprint'],a['worldHoles'])
        for b in corrections[:i]:
            area = pa.intersection(Polygon(b['worldFootprint'],b['worldHoles'])).area
            if area>.02:
                assert area<1,(a['modelId'],b['modelId'],area)
                seams.append({'models':[a['modelId'],b['modelId']], 'sourceOverlapAreaM2':area,
                              'review':'Small shared-edge overlap in supplied outlines; retain evidence and partition rendered seam once.'})
    accounted = {b['modelId'] for b in corrections} | {'site964-range-14'}
    yard_bounds = [-750,-108,-607,5]
    yard_pixels = [[348,258],[525,266],[541,348],[551,423],[569,475],
                   [488,489],[451,496],[444,461],[374,478],[292,434],
                   [279,407],[288,376],[308,337],[330,311],[346,302]]
    _, to_world, _ = mosaic(yard_bounds)
    yard = {'id':96401, 'parentSiteId':964, 'name':'Chippindale cooperage and sawmill yard',
            'polygons':[[to_world(yard_pixels).round(3).tolist()]],
            'mosaicBounds':yard_bounds, 'mosaicPixels':yard_pixels,
            'stockType':'timber', 'allowStock':True,
            'evidence':'Working-yard envelope follows the inspected OS boundary and Goad cooperage/timber yard. Buildings, roads and the river are excluded during generation. Surface finish and sparse timber stock are interpreted; this is not a surveyed cadastral boundary.'}
    result = {'source':'Author-supplied london_buildings_1891-96_corr_v1.gpkg',
              'sourceCRS':'EPSG:3857 reprojected through BNG; scene origin E538900,N183209',
              'method':'Explicit OS/Goad cooperage and Winstone groups; retained elevation evidence and interpreted internal compartments.',
              'mapReview':['Georeferenced OS five-foot 1893-96 mosaic','July 1893 Goad volume F sheet 3'],
              'groups':groups, 'buildings':corrections, 'additionalBuildings':additional,
              'yard':yard,
              'structures':[chimney], 'boundaryOverlapReviews':seams,
              'roadBoundaryReview':{'road':'Sugar House Lane', 'modelId':'site964-range-10',
                  'sourceOverlapAreaM2':.0381454,
                  'review':'The street/pavement buffer clips a 0.038 m² corner sliver at the beam-house entrance; retain both map traces and clear this small seam in the renderer.'},
              'previouslyAligned':['site964-range-14'],
              'deferred':[{'modelId':b['id'], 'reason':'Northern Crystal Wharf or southern Barber group awaits separate OS/Goad review; not included in this cooperage/Winstone pass.'}
                          for b in before['buildings'] if b['siteId']==964 and b['id'] not in accounted]}
    (ROOT/'data/maps/sugar-house-footprint-alignment.json').write_text(json.dumps(result,indent=2)+'\n')
    print(f'{len(corrections)} source-linked ranges in {len(groups)} groups, including {len(additional)} added low cooperage compartments; one chimney base. {len(result["deferred"])} ranges await separate review.')

if __name__ == '__main__':
    build()
