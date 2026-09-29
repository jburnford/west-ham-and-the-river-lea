"""Save reviewed exterior matches west of the cooperage, retaining elevations.

Requires the private source extract and immutable west-sugar-before.json review
snapshot. Routine scene builds consume the saved register without either file.
"""
import json
from pathlib import Path
from shapely import affinity, set_precision
from shapely.geometry import Polygon, Point, shape, box
from shapely.ops import unary_union
from prepare_howards_alignment import partition
from prepare_ink_works_alignment import axis, rings
from factory_map_sources import mosaic

ROOT = Path(__file__).resolve().parents[1]
# Matches established by inspecting OS five-foot mapping and Goad F3 together.
SPECS = [
    ('hodson-factory-warehouse', [1, 5], [6409, 636932]),
    ('hodson-machinery', [2], [5689]),
    ('victoria-tenements', [3], [128336, 144618]),
    ('victoria-south', [4], [799473]),
    ('hodson-boiler', [6], [797193]),
    ('hodson-perimeter', [7, 9, 8], [6324]),
    ('hodson-central', [10], [34752]),
    ('dane-iron-hyeg', [11], [18585, 923455, 1270030]),
    ('dane-north-calcining', [12], [544763]),
    ('dane-calcining', [13], [12488]),
    ('dane-linseed-boiling', [14], [119554, 150448, 1179925]),
    ('winstone-boiler', [15], [831387]),
    ('winstone-north', [16], [40968]),
    ('winstone-main', [17], [268585, 36326]),
    ('winstone-river-rooms', [18], [389987, 716775]),
    ('winstone-south', [19], [84864, 822254, 835362]),
    ('winstone-west-sheds', [20], [117402]),
    ('winstone-south-west-room', [21], [198868]),
    ('wildash-west', [22], [41327, 621997]),
    ('wildash-east', [23, 24], [410242, 950604]),
    ('wildash-south-east', [25], [16620]),
    ('wildash-river-rooms', [26], [488518, 83785, 546611]),
    ('wildash-central', [27], [221031]),
]
ADDITIONS = [
    ('hodson-street', 'Hodson street ranges, Goad 810/812', [119774, 713012, 711459], 3.8),
    ('hodson-south-shed', 'Hodson southern shed, Goad 832', [423706], 3.8),
    ('dane-stable', 'Dane northern street room, Goad 842', [169983], 3.8),
    ('dane-south-room', 'Dane southern iron-roof room, Goad 848', [692523], 5.35),
    ('winstone-east-shed', 'Winstone long shed, Goad 852', [743515], 3.8),
    ('winstone-east-room', 'Winstone street range, Goad 850', [288165, 1080265], 3.8),
    ('winstone-west-store', 'Winstone western store, Goad 862', [673766], 3.8),
    ('winstone-south-store', 'Winstone detached southern store, Goad 871', [795158, 988220], 3.8),
    ('winstone-east-store', 'Winstone eastern store, Goad 872', [695210, 972781], 3.8),
    ('winstone-south-east-room', 'Winstone southern street room, Goad 874', [749125, 924622, 1266004, 901101, 1139767, 1101464], 3.8),
    ('winstone-large-hall', 'Winstone riverside hall, Goad 880', [6789], 5.35),
]


def build():
    load = lambda p: json.loads((ROOT/p).read_text())
    before = load('reference/footprint-model-alignment/west-sugar-before.json')
    models = {b['id']: b for b in before['buildings']}
    wanted = {f for _, _, fids in SPECS for f in fids} | {f for _, _, fids, _ in ADDITIONS for f in fids}
    wanted.update([1107028, 1031260, 1108526])
    source = {f['properties']['sourceFid']: affinity.affine_transform(shape(f['geometry']), [1,0,0,-1,-538900,183209])
              for f in load('reference/historic-building-footprints-2026-09-28/current-scene-buildings-bng.geojson')['features']
              if f['properties']['sourceFid'] in wanted}
    specs = [(n, [f'site947-range-{i}' for i in ids], fids) for n, ids, fids in SPECS]
    additional = []
    for name, label, fids, height in ADDITIONS:
        g = set_precision(unary_union([source[f] for f in fids]), .001)
        assert g.geom_type == 'Polygon', (name, g.geom_type)
        id = 'site947-'+name
        evidence = 'OS exterior matched to the separately drawn Goad compartment; roof form and eaves height remain interpreted.'
        row = dict(id=id, siteId=947, source='goad-f3-sugar', name=label,
                   worldFootprint=rings(g)[0], worldHoles=rings(g)[1:],
                   footprintEvidence=evidence, eavesHeight=height,
                   heightEvidence=f'Goad low compartment; {height} m eaves is an estimate, not a measured elevation.',
                   roofEvidence=evidence, roofRise=2.2, roofBays=1, roofAxis='x', material='brick')
        additional.append(row)
        models[id] = {**row, 'footprint':row['worldFootprint'], 'height':height, 'rotation':-10.0}
        specs.append((name,[id],fids))
    groups, corrections = [], []
    for name, ids, fids in specs:
        original = [Polygon(models[id]['footprint']) for id in ids]
        target = set_precision(unary_union([source[f] for f in fids]), .001)
        assert target.geom_type == 'Polygon' and target.is_valid, name
        previous = models[ids[0]]['rotation']
        angle = axis(target, previous)
        division = None
        if name == 'hodson-factory-warehouse':
            north = target.intersection(box(-1000,-1000,0,-81.5))
            parts = [north,target.difference(north)]
            division = 'Factory 806 and southern warehouse/offices 808 retain separate elevations; their internal boundary near scene z=-81.5 is interpreted from Goad.'
        elif name == 'hodson-perimeter':
            north = target.intersection(box(-1000,-1000,0,-57))
            west = target.intersection(box(-1000,-57,-754,-34))
            # The box also touches a small return on the opposite courtyard wall.
            # Keep that return with the continuous southern/eastern compartment.
            west = max(getattr(west,'geoms',[west]),key=lambda p:p.area)
            parts = [north,west,target.difference(north.union(west))]
            division = 'Retain northern, riverside and southern perimeter compartments around the mapped court. Cuts at scene z=-57/-34 and x=-754 are interpreted; OS fixes only the exterior.'
        else:
            parts = partition(original,target,previous,angle) if len(ids)>1 else [target]
            if len(ids)>1:
                division = 'Retain earlier Goad compartment proportions within the shared exterior; internal division is interpreted.'
        parts = [set_precision(p,.001) for p in parts]
        assert all(p.geom_type=='Polygon' and p.is_valid and p.area>2 for p in parts), (name,[(p.geom_type,p.area) for p in parts])
        assert unary_union(parts).symmetric_difference(target).area<.15, name
        old = unary_union(original)
        groupid = 'west-sugar-'+name
        groups.append(dict(id=groupid, modelIds=ids, sourceFids=fids,
                           sourcePolygons=[rings(p) for f in fids for p in source[f].geoms],
                           additional=ids[0] in {a['id'] for a in additional}, division=division,
                           previousUnionIoU=old.intersection(target).area/old.union(target).area))
        for id, prior, part in zip(ids,original,parts):
            b=models[id]
            member_angle=axis(part,b['rotation']) if name=='hodson-perimeter' else angle
            corrections.append(dict(modelId=id,siteId=947,name=b['name'],groupId=groupid,
                sourceFids=fids, **({'sourceFid':fids[0]} if len(fids)==1 else {}),
                worldFootprint=rings(part)[0], worldHoles=rings(part)[1:], priorFootprint=rings(prior)[0],
                priorRotationDegrees=b['rotation'],footprintRotationDegrees=member_angle,
                preservedHeight=b['height'],preservedRoofRise=b['roofRise'],preservedRoofAxis=b['roofAxis'],preservedRoofBays=b['roofBays'],
                review='Explicit OS/Goad F3 exterior match west of the cooperage. Retain prior elevation/roof interpretation. '+(division or 'Mapped exterior retained.'),
                comparison=dict(centroidShiftMetres=prior.centroid.distance(part.centroid),areaRatio=part.area/prior.area,axisChangeDegrees=member_angle-b['rotation'])))
    structures=[]
    for suffix,fid,radius in [('1386-2594',1107028,.65),('1079-2905',1031260,1.05),('1023-3136',1108526,.65)]:
        old=next(s for s in before['structures'] if s['id']=='stack-947-'+suffix)
        g=source[fid]
        structures.append(dict(id=old['id'],sourceFid=fid,sourcePolygons=[rings(p) for p in g.geoms],
            centre=list(g.centroid.coords)[0],rotation=axis(g,old['rotation']),priorCentre=[old['x'],old['z']],
            preservedHeight=old['height'],priorRadius=old['radius'],radius=radius,
            profileEvidence='Shaft height retained; interpreted base width fitted inside the mapped plinth. Profile is not a measured elevation.',
            review='Goad chimney symbol matched to the independent OS base; height retained.'))
    old=next(s for s in before['structures'] if s['id']=='stack-947-812-3137')
    # No separate supplied base exists within room 860. Use the symbol's local
    # proportion in its mapped room, not a nearby unrelated polygon.
    g=source[389987]
    local=affinity.rotate(g, -axis(g,-8.8043),origin=(0,0)); x0,y0,x1,y1=local.bounds
    p=affinity.rotate(Point(x0+.86*(x1-x0),y0+.18*(y1-y0)),axis(g,-8.8043),origin=(0,0))
    structures.append(dict(id=old['id'],centre=list(p.coords)[0],rotation=axis(g,-8.8043),
        priorCentre=[old['x'],old['z']],preservedHeight=old['height'],transferGroup='west-sugar-winstone-river-rooms',
        review='Goad 860 chimney transferred to the north-east part of its corrected river room; no separate OS base supplied. Position within the room and shaft profile remain interpreted.'))
    seams=[]
    for i,a in enumerate(corrections):
        pa=Polygon(a['worldFootprint'],a['worldHoles'])
        for b in corrections[:i]:
            area=pa.intersection(Polygon(b['worldFootprint'],b['worldHoles'])).area
            if area>.005:
                assert area<1,(a['modelId'],b['modelId'],area)
                seams.append(dict(models=[a['modelId'],b['modelId']],sourceOverlapAreaM2=area,
                                  review='Small supplied-outline shared-wall overlap; preserve source and partition rendered seam once.'))
    yard_bounds=[-795,-30,-690,135]
    yard_points=[[-781,-22],[-737,-25],[-729,16],[-721,60],[-703,109],
                 [-750,128],[-770,100],[-787,62],[-790,40],[-784,12]]
    _,_,to_pixel=mosaic(yard_bounds)
    yard=dict(id=94701,parentSiteId=947,name='Western Sugar House Lane works yards',
        polygons=[[yard_points]],mosaicBounds=yard_bounds,mosaicPixels=to_pixel(yard_points).round(3).tolist(),
        allowStock=False,
        evidence='OS/Goad working-ground envelope between the western buildings, Sugar House Lane and Three Mills Back River. Original industrial parcels omit the Dane/Winstone/Wildash open ground. Roads, buildings, chimneys and water are excluded during generation; finish is interpreted, and this is not a cadastral boundary or evidence of a single occupier.')
    result=dict(source='Author-supplied london_buildings_1891-96_corr_v1.gpkg',
        sourceCRS='EPSG:3857 reprojected through BNG; scene origin E538900,N183209',
        method='Explicit reviewed OS/Goad matches west of the cooperage, retaining interpreted elevations and internal compartments.',
        mapReview=['Georeferenced OS five-foot 1893-96 mosaic','July 1893 Goad volume F sheet 3'],
        groups=groups,buildings=corrections,additionalBuildings=additional,structures=structures,boundaryOverlapReviews=seams,yard=yard,
        removedBuildings=[{**models[id], 'review':'Goad F17 repeats the edge of F3 block F30: label 892 and the adjoining 888/890 rooms belong to Wildash. Duplicate coarse model removed; source-linked site947 rooms retain these buildings.'}
                          for id in ['site569-range-1','site569-range-4']],
        roadBoundaryReview=dict(modelId='site947-range-5',sourceOverlapAreaM2=.0210698,
            review='A 0.021 m² pavement mitre touches the supplied warehouse corner; retain both traces and clear this tiny seam in rendering.'),
        deferred=[dict(feature='Small detached room Goad 876, tiny sheds and southern Goad 882/884 annexes',
                       reason='Require separate map tracing and roof/use review; no automatic nearest-source assignment.')])
    (ROOT/'data/maps/west-sugar-footprint-alignment.json').write_text(json.dumps(result,indent=2)+'\n')
    print(f'West Sugar House Lane: {len(corrections)} aligned ranges in {len(groups)} groups; {len(additional)} added rooms and four corrected chimneys.')


if __name__=='__main__':
    build()
