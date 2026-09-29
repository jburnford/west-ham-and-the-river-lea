"""Author eight southern Three Mills matches using shared alignment records.

Private source extract and immutable before snapshot are authoring inputs only.
"""
import json
from pathlib import Path
from shapely import affinity, set_precision
from shapely.geometry import shape, box
from shapely.ops import unary_union
from prepare_ink_works_alignment import axis
from prepare_three_mills_north_alignment import polygon, ident
from factory_alignment_records import record_group, fitted_tank

ROOT = Path(__file__).resolve().parents[1]
SPECS = [
    ('grain-process', [344], [21,22,23,24]),
    ('room-854', [132768,396886], [25]),
    ('range-854-856', [34266,835014], [26]),
    ('range-858', [27300,27774,26435,64758,38030,912850,822473,809347], [27]),
    ('gas-house-860', [36050], [28]),
]
NAMES = {21:'Three Mills grain warehouse and kilns, Goad 846/848',
    22:'Three Mills two-floor process range, Goad 850',
    23:'Three Mills central low process range', 24:'Three Mills eastern range, Goad 852',
    25:'Three Mills southern room, Goad 854',
    26:'Three Mills narrow range and timber annex, Goad 854/856',
    27:'Three Mills two-floor process block, Goad 858',
    28:'Three Mills gas house, Goad 860'}
TANKS = [('distillery-tank-1270',464133), ('distillery-tank-1333',458700),
         ('distillery-tank-1387',462633)]


def build():
    load = lambda p:json.loads((ROOT/p).read_text())
    before = load('reference/footprint-model-alignment/three-mills-south-before.json')
    models = {b['id']:b for b in before['buildings']}
    wanted = {f for _,fs,_ in SPECS for f in fs}|{f for _,f in TANKS}
    source = {f['properties']['sourceFid']:polygon(affinity.affine_transform(
        shape(f['geometry']),[1,0,0,-1,-538900,183209]))
        for f in load('reference/historic-building-footprints-2026-09-28/current-scene-buildings-bng.geojson')['features']
        if f['properties']['sourceFid'] in wanted}
    groups, corrections = [], []
    for name,fids,numbers in SPECS:
        ids = [ident(n) for n in numbers]
        target = polygon(set_precision(unary_union([source[f] for f in fids]),.001))
        angle = axis(target,models[ids[0]]['rotation'])
        parts, division = [target], None
        if len(ids)>1:
            local = affinity.rotate(target,-angle,origin=(0,0))
            x0,y0,x1,y1 = local.bounds
            # The western cut follows the open notch between warehouse and
            # process rooms; the remaining widths follow the Goad proportions.
            west_cut = -626.0
            cuts = [x0-1,west_cut,west_cut+(x1-west_cut)*80/231,
                    west_cut+(x1-west_cut)*171/231,x1+1]
            parts = [polygon(set_precision(affinity.rotate(local.intersection(
                box(a,y0-1,b,y1+1)),angle,origin=(0,0)),.001))
                for a,b in zip(cuts,cuts[1:])]
            division = ('Warehouse/process cut follows the southern open notch. '
                'Other west/east divisions use the prior Goad width proportions; '
                'internal walls and elevations remain interpreted because Goad records an outside sketch survey. '
                'The existing warehouse model retains its height across the kiln end; no separate kiln elevation is asserted.')
        group, rows = record_group('three-mills-south-'+name,fids,source,models,
            ids,[NAMES[n] for n in numbers],target,parts,angle,division)
        groups.append(group)
        corrections.extend(rows)
    tanks = [fitted_tank(next(s for s in before['structures'] if s['id']==id),
        fid,source[fid],'Independent OS circular outline identified as Goad tanks 863/864/865; inferred 6 m height retained.')
        for id,fid in TANKS]
    result = dict(source='Author-supplied london_buildings_1891-96_corr_v1.gpkg',
        sourceCRS='EPSG:3857 reprojected through BNG; scene origin E538900,N183209',
        method='Explicit southern Three Mills OS/Goad matches for eight existing ranges and three tank outlines; prior elevations retained.',
        mapReview=['Georeferenced OS five-foot 1893–96 mosaic',
            'July 1893 Goad F17; admission refused, sketch survey from outside observation'],
        groups=groups,buildings=corrections,structures=[],tanks=tanks,
        deferred=[dict(feature='House/Clock Mills and wharf ranges',reason='Coordinated millrace and landmark continuation.'),
            dict(feature='Northern gangways 167022/29937, rounded feature 219295 and small wall projections',
                 reason='Different roof/plant interpretation required; not extended to the neighbouring full-height building.'),
            dict(feature='Circular features 444596/486835 and small gas-house projections',
                 reason='No existing model; plant classification and gas apparatus remain separate work.')])
    (ROOT/'data/maps/three-mills-south-footprint-alignment.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Three Mills south: eight ranges in five groups and three fitted tanks.')


if __name__=='__main__':
    build()
