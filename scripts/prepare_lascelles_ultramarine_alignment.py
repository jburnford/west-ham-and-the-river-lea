"""Match Lascelles and Ultramarine, recording the OS sheet-join reconciliation.

Requires the private source extract and immutable lascelles-ultramarine-before
snapshot. Saved authoring JSON is sufficient for routine builds.
"""
import json
from pathlib import Path
from shapely import affinity, set_precision
from shapely.geometry import Polygon, shape
from shapely.ops import unary_union
from prepare_ink_works_alignment import axis, rings
from prepare_howards_alignment import partition
from factory_map_sources import mosaic

ROOT = Path(__file__).resolve().parents[1]
# Read from the paired source edges at the OS sheet join. This narrow strip is
# registration reconciliation, not an independently supplied building outline.
JOIN_MAIN = [[-620.186,194.235],[-620.092,194.786],[-619.777,212.057],
             [-619.762,212.316],[-618.433,211.402],[-618.972,194.102],[-618.918,193.593]]
JOIN_SOUTH = [[-619.762,212.316],[-619.668,212.867],[-619.375,228.621],
              [-618.094,227.619],[-618.502,211.582],[-618.433,211.402]]
SPECS = [
    ('lascelles-main', [6127], ['site565-range-1'], None),
    ('lascelles-south-628', [102625], ['site565-range-2'], None),
    ('lascelles-north-626', [473976], ['site565-range-3'], None),
    ('ultramarine-main', [5241,4566], ['site566-range-1'], JOIN_MAIN),
    ('ultramarine-south', [13778,48472], ['site566-range-2','site566-range-3'], JOIN_SOUTH),
]
NAMES = {
    'site565-range-1': 'Lascelles stone and terra cotta factory',
    'site565-range-2': 'Lascelles southern range, Goad 628',
    'site565-range-3': 'Lascelles northern range, Goad 626',
    'site566-range-1': 'British Ultramarine main process house',
    'site566-range-2': 'British Ultramarine southern upper bay',
    'site566-range-3': 'British Ultramarine southern boiler bay',
}


def build():
    load = lambda p: json.loads((ROOT/p).read_text())
    before = load('reference/footprint-model-alignment/lascelles-ultramarine-before.json')
    models = {b['id']:b for b in before['buildings']}
    wanted = {f for _,fids,_,_ in SPECS for f in fids} | {986471}
    source = {f['properties']['sourceFid']:affinity.affine_transform(shape(f['geometry']),[1,0,0,-1,-538900,183209])
              for f in load('reference/historic-building-footprints-2026-09-28/current-scene-buildings-bng.geojson')['features']
              if f['properties']['sourceFid'] in wanted}
    groups, corrections = [], []
    for name,fids,ids,join in SPECS:
        raw = unary_union([source[f] for f in fids])
        target = set_precision(raw,.001)
        if join:
            target = unary_union([target,Polygon(join)])
        if target.geom_type=='MultiPolygon' and len(target.geoms)==1:
            target = target.geoms[0]
        assert target.geom_type=='Polygon' and target.is_valid, (name,target.geom_type)
        old = [Polygon(models[id]['footprint']) for id in ids]
        angle = axis(target,models[ids[0]]['rotation'])
        parts = partition(old,target,models[ids[0]]['rotation'],angle) if len(ids)>1 else [target]
        assert all(p.geom_type=='Polygon' and p.is_valid and p.area>2 for p in parts)
        prior = unary_union(old)
        group = dict(id=name,modelIds=ids,sourceFids=fids,
                     sourcePolygons=[rings(p) for f in fids for p in getattr(source[f],'geoms',[source[f]])],
                     reconciledPolygons=[rings(target)],
                     previousUnionIoU=prior.intersection(raw).area/prior.union(raw).area,
                     division='Earlier Goad bay proportions retained within the corrected southern exterior; internal division remains interpreted.' if len(ids)>1 else None)
        if join:
            group['sheetJoin'] = dict(worldPolygon=join,addedAreaM2=target.difference(raw).area,
                evidence='OS source outlines stop at opposing edges of a roughly 1.2 m sheet-registration gap. Goad shows continuous rooms. Join only the paired seam edges; retain all outside walls and mapped chimney holes.')
        groups.append(group)
        for id,p,old in zip(ids,parts,old):
            b = models[id]
            corrections.append(dict(modelId=id,siteId=b['siteId'],name=NAMES[id],groupId=name,sourceFids=fids,
                **({'sourceFid':fids[0]} if len(fids)==1 else {}),
                worldFootprint=rings(p)[0],worldHoles=rings(p)[1:],priorFootprint=rings(old)[0],
                priorRotationDegrees=b['rotation'],footprintRotationDegrees=angle,
                preservedHeight=b['height'],preservedRoofRise=b['roofRise'],preservedRoofAxis=b['roofAxis'],preservedRoofBays=b['roofBays'],
                review='OS/Goad F17 exterior match. Prior heights and roofs retained. '+(group.get('sheetJoin',{}).get('evidence','Individual supplied exterior.')),
                comparison=dict(centroidShiftMetres=old.centroid.distance(p.centroid),areaRatio=p.area/old.area,axisChangeDegrees=angle-b['rotation'])))
    old = next(s for s in before['structures'] if s['id']=='stack-566-1203-1650')
    g = source[986471]
    structures = [dict(id=old['id'],sourceFid=986471,sourcePolygons=[rings(p) for p in getattr(g,'geoms',[g])],
        centre=list(g.centroid.coords)[0],rotation=axis(g,old['rotation']),priorCentre=[old['x'],old['z']],preservedHeight=old['height'],
        review='Goad 60-foot Ultramarine shaft matched to independent OS base 986471 inside the retained southern roof opening; prior interpreted profile retained.')]
    result = dict(source='Author-supplied london_buildings_1891-96_corr_v1.gpkg',
        sourceCRS='EPSG:3857 reprojected through BNG; scene origin E538900,N183209',
        method='Explicit Lascelles and British Ultramarine OS/Goad matches; narrow OS sheet-join corrections separately recorded; prior heights and roof interpretations retained.',
        mapReview=['Georeferenced OS five-foot 1893–96 mosaic','July 1893 Goad volume F sheet 17'],
        groups=groups,buildings=corrections,structures=structures,
        deferred=[dict(sourceFids=[1105121,908578],reason='Small projections need separate plant/service classification.'),
                  dict(feature='Northern Williams wharf rooms and boundary lean-to',sourceFids=[108655,445081,59238,585845,656439],
                       reason='Existing adjoining site568 ranges retained. Review with the full Williams/French Asphalte compound, including boundary attribution and the unmodelled 704 room.')])
    (ROOT/'data/maps/lascelles-ultramarine-footprint-alignment.json').write_text(json.dumps(result,indent=2)+'\n')
    roads = load('data/maps/district-road-traces.json')
    lane = next(r for r in roads['roads'] if r['name']=='Sugar House Lane')
    previous = lane.get('lascellesUltramarineAlignment', {})
    prior = previous.get('priorPoints', lane['points'])
    prior_pixels = previous.get('priorSourcePixels', lane['sourcePixels'])
    lane['points'] = [list(p) for p in prior]
    lane['points'][-1] = [round(prior[-1][0]-3.5,3),prior[-1][1]]
    _,_,pixel = mosaic(lane['sourceBounds'])
    lane['sourcePixels'] = [list(p) for p in prior_pixels]
    lane['sourcePixels'][-1] = pixel([lane['points'][-1]])[0].round(3).tolist()
    lane['lascellesUltramarineAlignment'] = dict(priorPoints=prior,priorSourcePixels=prior_pixels,
        review='Final lane control reconciled 3.5 m west against the OS gap between Lascelles and Ultramarine. Earlier coarse corridor cut 34 m² from the mapped process house. Existing width and all upstream controls retained; centreline remains interpreted.',
        finalPoint=lane['points'][-1],sourceBounds=lane['sourceBounds'])
    (ROOT/'data/maps/district-road-traces.json').write_text(json.dumps(roads,indent=2)+'\n')
    print('Lascelles/Ultramarine: six ranges in five groups; two explicit map-sheet joins and one mapped chimney base.')
    for g in groups:
        if 'sheetJoin' in g: print(g['id'],'join area',round(g['sheetJoin']['addedAreaM2'],3),'m²')


if __name__=='__main__':build()
