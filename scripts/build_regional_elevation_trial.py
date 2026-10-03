"""Ground + street interpolation experiment, isolated from scene/flood terrain."""
import hashlib
import json
from pathlib import Path

import numpy as np
import shapely
from PIL import Image
from scipy.spatial import Delaunay
from shapely.geometry import Polygon

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/data/lower-lea-region'
MAX_EDGE = 500.0  # Exploratory limit, not a demonstrated historical support radius.
STATUSES = {'reviewed-ground', 'candidate-ground', 'reviewed-road', 'candidate-road'}


def triangulate(records, water):
    xy = np.array([r['positionBNG'] for r in records])
    values = np.array([r['provisionalODNMetres'] for r in records])
    tin = Delaunay(xy)
    vertices = xy[tin.simplices]
    longest = np.linalg.norm(vertices - np.roll(vertices, 1, axis=1), axis=2).max(axis=1)
    polygons = shapely.polygons(vertices)
    crosses_water = shapely.intersects(polygons, water)
    accepted = (longest <= MAX_EDGE) & ~crosses_water
    return tin, values, accepted, longest, crosses_water


def sample(tin, values, accepted, xy):
    simplex = tin.find_simplex(xy)
    valid = (simplex >= 0) & accepted[np.maximum(simplex, 0)]
    result = np.full(len(xy), np.nan)
    index = simplex[valid]
    delta = xy[valid] - tin.transform[index, 2]
    bary = np.einsum('nij,nj->ni', tin.transform[index, :2], delta)
    weights = np.column_stack([bary, 1-bary.sum(axis=1)])
    result[valid] = (values[tin.simplices[index]] * weights).sum(axis=1)
    return result


def build():
    audit_path = OUT/'elevation-audit.json'
    network_path = ROOT/'docs/data/river-system-1900.json'
    review_path = ROOT/'data/maps/lower-lea-region/regional-elevation-review-1900.json'
    review = json.loads(review_path.read_text())
    audit = json.loads(audit_path.read_text())
    network = json.loads(network_path.read_text())
    records = sorted([r for r in audit['records'] if r['auditStatus'] in STATUSES], key=lambda r:r['id'])
    water = shapely.union_all([
        Polygon([(538900+x,183209-z) for x,z in p[0]],
                [[(538900+x,183209-z) for x,z in ring] for ring in p[1:]])
        for reach in network['reaches'] for p in reach['polygons']])
    water = shapely.union_all([water,*[Polygon(r['polygonBNG']) for r in audit['terrainExclusions']]])
    tin, values, accepted, longest, crosses_water = triangulate(records, water)
    e0,n0,e1,n1 = audit['boundsBNG']
    step = 10
    east,north = np.meshgrid(np.arange(e0+step/2,e1,step), np.arange(n1-step/2,n0,-step))
    xy = np.column_stack([east.ravel(),north.ravel()])
    heights = sample(tin,values,accepted,xy)
    wet = shapely.intersects(shapely.points(xy),water)
    heights[wet] = np.nan
    heights.astype('<f4').tofile(OUT/'elevation-trial.odn.f32')
    support = np.where(wet,2,np.isfinite(heights).astype('u1')).astype('u1')
    support.tofile(OUT/'elevation-trial.support.u8')
    stops = [-1,0,2,5,10,20,35]
    colours = np.array([[90,122,116],[133,164,146],[176,188,145],[210,202,164],[189,161,126],[151,126,104],[229,221,199]])
    rgb = np.stack([np.interp(np.nan_to_num(heights),stops,colours[:,k]) for k in range(3)],axis=-1).astype('u1')
    rgb[~np.isfinite(heights)] = [235,232,226]
    rgb[wet] = [118,188,199]
    Image.fromarray(rgb.reshape(*east.shape,3)).save(OUT/'elevation-trial.png')

    # Deterministic five-fold holdout: report only supported predictions, plus
    # the fraction withheld by sparse coverage/water. Report road and ground
    # errors separately so street agreement cannot hide poor marsh estimates.
    folds = np.array([int(hashlib.sha256(r['id'].encode()).hexdigest()[:8],16)%5 for r in records])
    errors = []
    for fold in range(5):
        train = [r for r,k in zip(records,folds) if k != fold]
        held = [r for r,k in zip(records,folds) if k == fold]
        ft,fv,fa,_,_ = triangulate(train,water)
        predictions = sample(ft,fv,fa,np.array([r['positionBNG'] for r in held]))
        for r,pred in zip(held,predictions):
            errors.append({'id':r['id'],'family':r['surfaceFamily'],'fold':fold,
                           'predictedODNMetres':float(pred) if np.isfinite(pred) else None,
                           'errorMetres':float(pred-r['provisionalODNMetres']) if np.isfinite(pred) else None})
    validation = {}
    for role in ['ground','road']:
        rows = [r for r in errors if r['family']==role]
        err = np.array([r['errorMetres'] for r in rows if r['errorMetres'] is not None])
        validation[role] = {'heldOut':len(rows),'supportedPredictions':len(err),
                            'meanAbsoluteErrorMetres':round(float(np.mean(abs(err))),3) if len(err) else None,
                            'p90AbsoluteErrorMetres':round(float(np.percentile(abs(err),90)),3) if len(err) else None,
                            'meanSignedErrorMetres':round(float(np.mean(err)),3) if len(err) else None}
    paths = [audit_path,network_path,review_path,Path(__file__).resolve()]
    for row in review['targetedChecks']:
        paths.extend(ROOT/row[key] for key in ['mosaic','registration','reviewCrop'])
        if row.get('contextCrop'):
            paths.append(ROOT/row['contextCrop'])
    result = {'schemaVersion':1,'targetEpoch':'1900','status':'interpolation experiment; not applied to scene or flood solver',
              'boundsBNG':audit['boundsBNG'],'cellSizeMetres':step,'width':east.shape[1],'height':east.shape[0],
              'orientation':'rows north to south; cell centres; EPSG:27700',
              'heightFile':'elevation-trial.odn.f32','supportFile':'elevation-trial.support.u8','preview':'elevation-trial.png',
              'supportLegend':{'0':'unsupported; NaN height','1':'trial interpolation','2':'mapped water or canal/structure exclusion; no bed estimate'},
              'terrainExclusions':audit['terrainExclusions'],
              'verticalReference':audit['verticalReference'],
              'method':'Piecewise linear triangulation of ground and street observations, excluding every triangle touching mapped water or reviewed canal/structure exclusions, or with an edge longer than 500 m. No extrapolation, modern terrain fill, bank heights or benchmark offsets.',
              'maximumTriangleEdgeMetres':MAX_EDGE,
              'streetPolicy':audit['methodDecision']['streets'],
              'workingStandard':review['workingStandard'],
              'floodInterpretation':review['floodInterpretation'],
              'targetedMapChecks':review['targetedChecks']+audit['regionalSupplement']['outlierDecisions'],
              'limitations':['500 m is an experimental spacing limit, not established accuracy.',
                             'Linear triangles have continuous heights along shared edges but discontinuous slopes.',
                             'Water geometry constrains interpolation; road/rail earthworks and other dry-land barriers still need reconciliation.',
                             'Marsh lane and developed street levels are retained without an invented fill correction; adjoining ground differences remain uncertain.',
                             'Blank regions are unsupported, not flat ground. Surface-domain edges are not physical banks.',
                             'Reviewed display patches and detailed core remain unchanged; this trial does not replace them.',
                             'Holdout residuals test internal consistency; they do not validate datum, date, fill thickness or historical accuracy.'],
              'counts':{'controls':len(records),'ground':sum(r['surfaceFamily']=='ground' for r in records),
                        'road':sum(r['surfaceFamily']=='road' for r in records),'triangles':len(accepted),
                        'acceptedTriangles':int(accepted.sum()),'waterCrossingTriangles':int(crosses_water.sum()),
                        'controlsInAcceptedTriangles':len(np.unique(tin.simplices[accepted])),
                        'longEdgeTriangles':int((longest>MAX_EDGE).sum()),
                        'sampledSupportAreaKm2':round(float(np.isfinite(heights).sum()*step**2/1e6),4)},
              'controls':[{'id':r['id'],'positionBNG':r['positionBNG'],'heightODNMetres':r['provisionalODNMetres'],
                           'family':r['surfaceFamily'],'status':r['auditStatus']} for r in records],
              'acceptedTriangles':tin.simplices[accepted].tolist(),
              'validation':{'method':'five deterministic folds by observation ID','bySurface':validation,'observations':errors},
              'largeResidualReview': sorted([r for r in errors if r['errorMetres'] is not None and abs(r['errorMetres'])>1],key=lambda r:-abs(r['errorMetres'])),
              'inputHashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    (OUT/'elevation-trial.json').write_text(json.dumps(result,separators=(',',':'))+'\n')
    print(json.dumps({'counts':result['counts'],'holdout':validation},indent=2))


if __name__=='__main__':
    build()
