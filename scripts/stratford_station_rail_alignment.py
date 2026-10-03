"""Native OS running-pair correction and bounded station bank exclusions.

The station body is an obstacle to interpreted earth slopes, not evidence for
changing the rails, their level, or unresolved booking-office construction.
"""
import copy
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from scipy.interpolate import CubicSpline
from shapely import affinity
from shapely.geometry import LineString, Polygon, shape
from shapely.ops import unary_union
from PIL import Image, ImageDraw

from factory_map_sources import mosaic

ROOT = Path(__file__).resolve().parents[1]
BASELINE = 'reference/footprint-model-alignment/stratford-station-rail-before.json'
SOURCE = 'reference/historic-building-footprints-2026-09-28/current-scene-buildings-bng.geojson'
NATIVE_BOUNDS = [-260, -940, 100, -580]
CONTROL_X = {12:298.0, 13:426.0, 14:563.0, 15:655.5}
# Reviewed covered station bodies and associated mapped station structures.
# The thin western body68571 may be a platform/canopy: no height is assigned.
STATION_IDS = [1539, 66331, 50615, 803279, 977663, 778814, 1057916,
               68571, 837163, 150512, 281895, 885148, 1053094, 1055163]
BOOKING_IDS = [50615, 803279, 977663, 778814, 1057916]


def read(path):
    return json.loads((ROOT/path).read_text())


def running_line(record, mainline_route):
    main = LineString(mainline_route)
    d = record['mainlineJoinChainage']
    a,b = main.interpolate(d-.5),main.interpolate(d+.5)
    tangent = np.array([b.x-a.x,b.y-a.y]); tangent /= np.linalg.norm(tangent)
    points = np.asarray(record['route'])
    distances = np.r_[0,np.cumsum(np.linalg.norm(np.diff(points,axis=0),axis=1))]
    tail = np.array([140.62,-272.37])-points[-1]; tail /= np.linalg.norm(tail)
    spline = CubicSpline(distances,points,bc_type=((1,tangent),(1,tail)),axis=0)
    return LineString(spline(np.linspace(0,distances[-1],math.ceil(distances[-1]/2)+1)))


def author_review(record):
    """Add only four station controls to the existing Market correction."""
    prior = read(BASELINE)
    revised = copy.deepcopy(record)
    _,world,pixel = mosaic(NATIVE_BOUNDS)
    controls = []
    for index,x in CONTROL_X.items():
        sample = [x,float(pixel([prior['route'][index]])[0][1])]
        point = world([sample]).round(3).tolist()[0]
        revised['route'][index] = point
        controls.append(dict(index=index,priorPoint=prior['route'][index],point=point,
            reviewedSourceBounds=NATIVE_BOUNDS,reviewedSourcePixels=[sample]))
    features = read(SOURCE)['features']
    bodies = {}
    for feature in features:
        fid = feature['properties']['sourceFid']
        if fid in STATION_IDS:
            bodies[fid] = affinity.affine_transform(shape(feature['geometry']),
                [1,0,0,-1,-538900,183209])
    assert set(bodies)==set(STATION_IDS)
    revision = dict(
        source=SOURCE,sourceSha256=hashlib.sha256((ROOT/SOURCE).read_bytes()).hexdigest(),
        sourceTransform=[1,0,0,-1,-538900,183209],
        sourceFeatureIds=STATION_IDS,bookingFeatureIds=BOOKING_IDS,
        reviewedSourceBounds=NATIVE_BOUNDS,controls=controls,
        stationBodies=[dict(sourceFid=fid,geometry=bodies[fid].__geo_interface__) for fid in STATION_IDS],
        bankOnly=True,preservedCrestShoulderMetres=.51,
        evidence='Native OS running rails east of the shaded western station body1539 and between the northern waiting-room/platform bodies. Station formation slopes stop at these mapped bodies. No roof height, new retaining wall, platform architecture or complete station track layout is asserted.',
        bookingLimit='Booking-office bodies at the road bridge span the apparent rail approach. Their precise over-track function/height remains unresolved; the interpreted running crest and a0.51m shoulder survive here. Source intersection is not permission to move native rails or remove their support.',
        evidenceImages=['reference/footprint-model-alignment/stratford-station-rail-native.png',
                        'reference/footprint-model-alignment/stratford-station-rail-after.png'])
    revised['stationFormationReview'] = revision
    revised['eastChannelseaRailAlignment']['review'] = (
        'Native OS running-line corridor east of Stratford Market roof79 and shaded station body1539. '
        'Re-read seven controls12–18; station controls12–15 follow the running pair between station bodies. '
        'Mainline join/curve controls0–11 and branch tail19–20 retained. Gauge, spacing, formation profile and join levels retained. '
        'Mapped station bodies bound only interpreted bank toes; unresolved booking-office bridge approach keeps rail support.')
    note = dict(baseline=BASELINE,baselineSha256=hashlib.sha256((ROOT/BASELINE).read_bytes()).hexdigest(),
        changedControlIndices=list(CONTROL_X),replacements=controls,
        review=revision['evidence'],bookingLimit=revision['bookingLimit'])
    return revised,note


def station_formation_obstacles(record, mainline_route):
    """Protect mapped station bodies outside the running crest and shoulder.

    The existing builder adds0.5m to its building mask. The extra0.01m keeps
    that tolerance outside the whole original crest; rails and track support
    remain continuous at the unresolved over-track booking structure.
    """
    review = record.get('stationFormationReview')
    if not review:
        return Polygon()
    line = running_line(record,mainline_route)
    crest = line.buffer(record['crestHalfWidth']+review['preservedCrestShoulderMetres'],
        cap_style=2,join_style=2)
    return unary_union([shape(row['geometry']) for row in review['stationBodies']]).difference(crest)


def save_evidence(record):
    raw,_,pixel=mosaic(NATIVE_BOUNDS)
    native=Image.fromarray(raw)
    native.save(ROOT/record['stationFormationReview']['evidenceImages'][0])
    im=native.copy();draw=ImageDraw.Draw(im)
    main=next(r for r in read('docs/data/infrastructure.json')['railways'] if r.get('detailedMainline'))
    for route,colour in [(read(BASELINE),'red'),(record,'green')]:
        draw.line([tuple(q) for q in pixel(running_line(route,main['route']).coords)],fill=colour,width=3)
    for row in record['stationFormationReview']['stationBodies']:
        body=shape(row['geometry'])
        for poly in getattr(body,'geoms',[body]):
            draw.line([tuple(q) for q in pixel(poly.exterior.coords)],fill='blue',width=1)
    im.save(ROOT/record['stationFormationReview']['evidenceImages'][1])
