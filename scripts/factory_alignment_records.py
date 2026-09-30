"""Shared authoring records for explicitly reviewed factory/source matches."""
import math
from shapely.geometry import Polygon
from shapely.ops import unary_union
from prepare_ink_works_alignment import rings


def record_group(group_id, fids, source, models, ids, names, target, parts, angle,
                 division=None, additional=False,
                 review_prefix='Explicit OS/Goad F17 match; previous elevations and roofs retained. '):
    assert len(ids)==len(names)==len(parts)
    raw = unary_union([source[f] for f in fids])
    prior = unary_union([Polygon(models[id]['footprint']) for id in ids])
    group = dict(id=group_id, modelIds=ids, sourceFids=fids,
                 sourcePolygons=[rings(source[f]) for f in fids],
                 reconciledPolygons=[rings(target)],
                 previousUnionIoU=prior.intersection(raw).area/prior.union(raw).area,
                 additional=additional, division=division)
    corrections = []
    for id, name, p in zip(ids, names, parts):
        b = models[id]
        old = Polygon(b['footprint'])
        corrections.append(dict(modelId=id, siteId=b['siteId'], name=name,
            groupId=group_id, sourceFids=fids,
            **({'sourceFid':fids[0]} if len(fids)==1 else {}),
            worldFootprint=rings(p)[0], worldHoles=rings(p)[1:],
            priorFootprint=b['footprint'], priorRotationDegrees=b['rotation'],
            footprintRotationDegrees=angle, preservedHeight=b['height'],
            preservedRoofRise=b['roofRise'], preservedRoofAxis=b['roofAxis'],
            preservedRoofBays=b['roofBays'],
            review=review_prefix+(division or 'Supplied exterior retained.'),
            comparison=dict(centroidShiftMetres=old.centroid.distance(p.centroid),
                areaRatio=p.area/old.area, axisChangeDegrees=angle-b['rotation'])))
    return group, corrections


def fitted_tank(old, fid, outline, position_evidence):
    """Fit around the rounded centre actually emitted to the renderer."""
    from shapely.geometry import Point
    centre = Point(round(outline.centroid.x, 3), round(outline.centroid.y, 3))
    return dict(old, sourceFootprintFid=fid, sourcePolygons=[rings(outline)],
        priorStructure=old, positionEvidence=position_evidence,
        radiusEvidence='Inscribed circular body at the rounded mapped centroid; equal-area radius retained for comparison.') | dict(x=centre.x, z=centre.y,
        radius=math.floor(centre.distance(outline.boundary)*1000)/1000,
        equalAreaRadius=round(math.sqrt(outline.area/math.pi),3))
