"""Reviewed Edward Cook OS exteriors; preserve the labelled Goad compartments."""
import json
import math
from pathlib import Path
from shapely import affinity, set_precision
from shapely.geometry import Point, Polygon, box, shape
from shapely.ops import nearest_points, unary_union
from factory_alignment_records import record_group
from prepare_howards_alignment import partition
from prepare_ink_works_alignment import axis, rings
from prepare_three_mills_north_alignment import polygon

ROOT = Path(__file__).resolve().parents[1]
SPECS = [
 ('riverside-soap', [35042, 24177, 1048739], ['soap-boiling']),
 ('main-soap-house', [511, 861259, 882462, 999484, 967287], ['steam-west', 'steam-east', 'warehouse', 'office']),
 ('railway-process', [1438, 735111, 1164527], ['export', 'bone-west', 'bone-east', 'bone-tower']),
 ('manure-tallow', [849, 48730, 693662, 793581], ['manure-shed', 'mechanics', 'tallow']),
 ('western-boiler', [50998, 939920, 923263], ['boiler-west']),
 ('economiser-engine', [655771], ['engine']),
 ('eastern-boiler', [54011], ['boiler-east']),
 ('sacks', [20647], ['sacks']),
 ('wood-store', [50577, 908778], ['wood-store']),
 ('grain-mill', [30683], ['granary']),
 ('grease-store', [19704], ['grease']),
 ('skin-dressing', [140755, 761604], ['skin-dressing']),
 ('horse-slaughter', [32816, 18905], ['slaughter']),
 ('mess', [166384], ['mess']),
 ('empties', [35146], ['empties']),
 ('machinery', [60257], ['machine-store']),
 ('tallow-boilers', [68897], ['tallow-boilers']),
 ('french', [13578, 763411, 804686], ['french']),
 ('box-factory', [46172, 981404], ['box-factory']),
 ('mabbers', [7236, 648664, 947514, 1144182, 906995, 1197116, 161769], ['manure-stable', 'fodder', 'engines']),
 ('southern-store', [7172, 1026642], ['store']),
]
REVIEW = 'Explicit OS exterior and July 1893 Goad F2 room comparison; prior elevations and roof parameters retained. '


def build():
    load = lambda p: json.loads((ROOT/p).read_text())
    before = load('reference/footprint-model-alignment/soap-wharves-before.json')
    models = {b['id']: b for b in before['buildings']}
    cached = load('reference/footprint-model-alignment/soap-wharves-source-shapes.json')
    source = {int(f): polygon(shape(g)) for f,g in cached.items()}
    groups, buildings = [], []
    transfers = {}
    for label, fids, refs in SPECS:
        ids = ['cook-'+ref for ref in refs]
        target = polygon(set_precision(unary_union([source[f] for f in fids]), .001))
        old = [Polygon(models[i]['footprint']) for i in ids]
        angle = axis(target, models[ids[0]]['rotation'])
        parts = partition(old, target, models[ids[0]]['rotation'], angle) if len(ids)>1 else [target]
        if label == 'mabbers':
            # Transverse cuts retain the stable / fodder / engine ordering. The
            # open courtyard lies wholly in the southern engine compartment; generic
            # proportional cells would incorrectly fragment roofs across it.
            centre = target.centroid
            local = affinity.rotate(target, -angle, origin=centre)
            parts = [set_precision(affinity.rotate(local.intersection(box(-2000, z0, 0, z1)), angle, origin=centre), .001)
                     for z0,z1 in [(-2000,-253),(-253,-249),(-249,0)]]
        for id,p in zip(ids,parts):
            assert p.geom_type == 'Polygon' and p.is_valid and p.area>2, (id,p.geom_type,p.area)
        division = ('Goad room proportions fitted within the complete OS boundary. Interior roof divisions and room uses remain interpretations; exterior steps, chimney openings and courts follow OS.' if len(ids)>1 else 'Complete individual OS exterior; Goad supplies the retained room use.')
        group, rows = record_group('cook-soap-'+label, fids, source, models, ids,
            [models[i]['name'] for i in ids], target, parts, angle, division, review_prefix=REVIEW)
        if label=='mabbers':
            group['division'] = dict(method='Two transverse interpreted roof cuts retain stable, fodder and engine order while keeping the complete OS courtyard notch inside the southern engine range.',
                frameCentre=[target.centroid.x,target.centroid.y],frameAngleDegrees=angle,
                rotatedSceneZCuts=[-253,-249],courtEvidence='Small unshaded court between the eastern stable wing and southwestern engine room remains an open reentrant notch; generic proportional cuts would fragment two roofs across this opening.')
        groups.append(group); buildings.extend(rows)
        transfers[label] = (unary_union(old), target, models[ids[0]]['rotation'], angle)
    structures = []
    mapped = [('stack-796-2061-607',849114,None,'Goad economiser chimney with printed 120-foot height'),
              ('stack-796-2245-647',1141408,.46,'Goad tallow/mechanics chimney at the small OS opening'),
              ('stack-796-2636-921',1096338,.58,'Goad horse-bone-boiling chimney at the eastern OS end symbol')]
    for id,fid,radius,note in mapped:
        old = next(s for s in before['structures'] if s['id']==id)
        base = source[fid]
        centre = Point(round(base.centroid.x,3),round(base.centroid.y,3))
        angle = axis(base,old['rotation'])
        radius = radius or old['radius']
        plinth = affinity.rotate(box(centre.x-radius*1.2,centre.y-radius*1.2,
            centre.x+radius*1.2,centre.y+radius*1.2),angle,origin=centre)
        assert base.covers(plinth),id
        row = dict(id=id,sourceFid=fid,sourcePolygons=[rings(base)],centre=[centre.x,centre.y],
            rotation=angle,priorCentre=[old['x'],old['z']],preservedHeight=old['height'],
            review=note+' compared by department and symbol position with the distinct supplied OS outline; retain existing shaft height. OS fixes the base location; shaft section, taper and crown remain inferred.')
        if radius!=old['radius']:
            row.update(radius=radius,priorRadius=old['radius'],
                profileEvidence='Interpreted square shaft narrowed to fit the distinct small OS symbol outline; 1.2-times-radius square plinth entirely contained. Existing height and square section retained; footprint symbol is not a measured shaft diameter.')
        structures.append(row)
    old = next(s for s in before['structures'] if s['id']=='stack-796-1834-537')
    parent = next(c for c in buildings if c['modelId']=='cook-export')
    oldlocal = affinity.rotate(Polygon(parent['priorFootprint']),-parent['priorRotationDegrees'],origin=(0,0))
    newparent = Polygon(parent['worldFootprint'],parent['worldHoles'])
    newlocal = affinity.rotate(newparent,-parent['footprintRotationDegrees'],origin=(0,0))
    oldpoint = affinity.rotate(Point(old['x'],old['z']),-parent['priorRotationDegrees'],origin=(0,0))
    a,b,c,d = oldlocal.bounds; u,v=(oldpoint.x-a)/(c-a),(oldpoint.y-b)/(d-b)
    a,b,c,d = newlocal.bounds
    transfer = affinity.rotate(Point(a+u*(c-a),b+v*(d-b)),parent['footprintRotationDegrees'],origin=(0,0))
    # The earlier hand read lies on the room edge. Move to the closest point
    # within an inset that contains the entire square plinth, recording both.
    safe = newparent.buffer(-old['radius']*1.2*math.sqrt(2)-.01)
    centre = nearest_points(safe,transfer)[0] if not safe.covers(transfer) else transfer
    centre = Point(round(centre.x,3),round(centre.y,3))
    assert newparent.covers(centre.buffer(old['radius']*1.2*math.sqrt(2)))
    structures.append(dict(id=old['id'],centre=[centre.x,centre.y],rotation=parent['footprintRotationDegrees'],
        priorCentre=[old['x'],old['z']],preservedHeight=old['height'],parentBuildingId='cook-export',parentFractions=[u,v],
        unadjustedTransferCentre=[transfer.x,transfer.y],localAdjustmentMetres=[centre.x-transfer.x,centre.y-transfer.y],
        review='Goad printed 50-foot export chimney transferred proportionally with its corrected room, then inset from the mapped wall to contain the whole interpreted square plinth. No independent OS base asserted; printed height, radius and section retained.'))
    result = dict(source='Author-supplied london_buildings_1891-96_corr_v1.gpkg; cached OS London five-foot mosaic',
        sourceCRS='EPSG:3857 reprojected through BNG; scene origin E538900,N183209',
        method='Reviewed complete OS exteriors, retaining Goad F2 uses and relative internal compartments with prior elevations and roof parameters. Separate open courts, two enclosed manure/tallow openings and mapped chimney openings retained.',
        groups=groups, buildings=buildings, structures=structures,
        mapReview=['Cached georeferenced OS five-foot 1893 mosaic', 'Original Goad July 1893 volume F sheet 2', 'Author-supplied undated Cook engraving guides existing relative elevations only; no metric dimensions read from engraving.'],
        evidenceImages=['reference/footprint-model-alignment/cook-source.png','reference/footprint-model-alignment/cook-models.png','reference/footprint-model-alignment/cook-goad-crop.png','reference/footprint-model-alignment/cook-process.png','reference/footprint-model-alignment/cook-southern.png','reference/footprint-model-alignment/cook-eastern.png','reference/footprint-model-alignment/cook-after-models.png'],
        deferred=[dict(sourceFids=[13879,12096,25946,30636,37914,35805,17043],reason='Railway-side rooms east of Mabbers are additional mapped context with no current Cook model counterpart; retain outlines pending distinct tenancy/ancillary review.'),dict(sourceFids=[34761,95782,952868,567006,1182796,822654,90030,918262,471064,1102114],reason='Additional narrow covers, dwellings, tank/plant and small yard rooms lack existing counterparts; retain source context pending a separate ancillary pass.')])
    (ROOT/'data/maps/cook-soap-footprint-alignment.json').write_text(json.dumps(result,indent=2)+'\n')
    print(f'Cook: {len(buildings)} ranges in {len(groups)} groups.')

if __name__ == '__main__': build()
