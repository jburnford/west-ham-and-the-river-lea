"""Audit historical surface evidence before extending the regional terrain.

Distances describe evidence coverage, never a calibrated height uncertainty or
permission to interpolate across a waterway, embankment or change of epoch.
"""
import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np
import shapely
from PIL import Image
from scipy.spatial import cKDTree
from shapely.geometry import Polygon, box

from regional_elevation_sources import load_supplement
from regional_opus_sources import IMPORT_PATH, load_update

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/data/lower-lea-region'
GROUND = {'marsh', 'open_ground', 'embankment_foot'}
FAMILIES = {'street': 'road', 'bridge': 'bridge', 'yard': 'yard',
            'railway': 'railway', 'building': 'building',
            'embankment_top': 'bank-or-embankment', 'wall_top': 'wall'}


def family(mark):
    if mark['type'] == 'bench_mark':
        return 'benchmark'
    if mark.get('sourceUseRestriction'):
        return mark['sourceUseRestriction']['role']
    return 'ground' if mark['setting'] in GROUND else FAMILIES.get(mark['setting'], 'unknown')


def classify(mark, source, epochs, water_overlap=False):
    """Keep source reliability separate from the surface an observation measures."""
    review = mark.get('surfaceReview', {})
    core = epochs['epochs']['1900']
    reviewed = bool(review) or bool(mark.get('regionalSurfaceReview')) or mark['id'] in core['surfaceReviews']
    reasons = []
    if review.get('duplicateOf'):
        reasons.append('confirmed-duplicate')
    if review.get('terrainUse', '').lower().startswith('withheld'):
        reasons.append('review-withheld')
    epoch = epochs['observationSources'].get(mark['layer'], {}).get('epoch')
    if epoch not in core['allowedObservationEpochs']:
        reasons.append('epoch-not-allowed')
    if mark['datum'] != 'OD Liverpool':
        reasons.append('datum-unresolved')
    if mark['disputed']:
        reasons.append('reading-disputed')
    resolved = (mark['id'] in core.get('surfaceConflictResolutions', {})
                or bool(mark.get('regionalSurfaceReview', {}).get('surfaceConflictResolution')))
    if mark['setting_conflict'] and not resolved:
        reasons.append('surface-conflict')
    confidence = review.get('valueConfidence', mark['confidence'])
    if confidence != 'high':
        reasons.append('reading-or-dot-' + confidence)
    if water_overlap and family(mark) in {'ground', 'road'}:
        reasons.append('surface-dot-inside-mapped-water')
    inferred = (source.get('setting_source') != 'reader'
                or source.get('setting_rule') == 'value_fallback') and not reviewed
    role = family(mark)
    if role not in {'ground', 'road'}:
        status = 'separate-surface'
    elif reasons:
        status = role + '-needs-review'
    elif reviewed:
        status = 'reviewed-' + role
    elif inferred:
        status = 'inferred-' + role
        reasons.append('surface-inferred-from-notes-or-value')
    else:
        status = 'candidate-' + role
    return status, reasons, epoch, reviewed


def nearest(points, records):
    if not records:
        return np.full(len(points), np.inf)
    return cKDTree([r['positionBNG'] for r in records]).query(points)[0]


def build():
    paths = []

    def read(path):
        p = ROOT / path
        paths.append(p)
        return json.loads(p.read_text())

    region = read('docs/data/lower-lea-region/index.json')
    epochs = read('data/maps/terrain-epochs.json')
    network = read('docs/data/river-system-1900.json')
    core = read('docs/data/terrain-1900.json')
    regional_review = read('data/maps/lower-lea-region/regional-elevation-review-1900.json')
    eligibility = {r['id']:r for r in regional_review.get('eligibilityReviews',[])}
    for r in eligibility.values():
        paths.extend(ROOT/r[key] for key in ['mosaic','registration','reviewCrop'])
    # Opus continues transcribing independently. Freeze this build's work-state
    # inventory as well as its readings, so live claims cannot invalidate it.
    opus_manifest = read(IMPORT_PATH)
    manifest = read(opus_manifest['manifestSnapshot'])
    assert hashlib.sha256((ROOT/opus_manifest['manifestSnapshot']).read_bytes()).hexdigest()==opus_manifest['manifestSHA256']
    sources = {}
    for filename in ['height-observations.snapshot.geojson', 'height-observations.additional.geojson']:
        for f in read('data/maps/lower-lea-region/' + filename)['features']:
            sources[f['properties']['id']] = f['properties']
    paths.append(Path(__file__).resolve())
    # Reconciled current geometry, including reviewed passages; scene -> BNG.
    water = shapely.union_all([
        Polygon([(538900+x, 183209-z) for x, z in p[0]],
                [[(538900+x, 183209-z) for x, z in ring] for ring in p[1:]])
        for reach in network['reaches'] for p in reach['polygons']])
    network_water = water
    added,added_sources,exclusions,added_paths,supplement = load_supplement(ROOT)
    assert not set(added_sources).intersection(sources),'Supplement duplicates an existing ID'
    sources.update(added_sources);paths.extend(added_paths)
    water = shapely.union_all([water,*[Polygon(r['polygonBNG']) for r in exclusions]])
    datum = epochs['verticalReference']
    marks = region['heightMarks'] + added
    marks,sources,opus_update,opus_paths = load_update(ROOT,marks,sources)
    paths.extend(opus_paths)
    wet = shapely.intersects(shapely.points([m['positionBNG'] for m in marks]), water)
    records = []
    for m, overlap in zip(marks, wet):
        if m['id'] in eligibility:
            r = eligibility[m['id']]
            assert m['value_ft']==r['expectedValueFeet'] and m['setting']==r['setting']
            if r.get('surfaceConflictResolution'):
                assert m['setting_conflict'] and r.get('reviewedSetting')
            m = {**m,'sourceSetting':m['setting'],
                 'setting':r.get('reviewedSetting',m['setting']),'regionalSurfaceReview':r}
        source = sources[m['id']]
        status, reasons, epoch, reviewed = classify(m, source, epochs, bool(overlap))
        records.append({**m, 'surfaceFamily': family(m), 'auditStatus': status,
                        'auditReasons': reasons, 'observationEpoch': epoch,
                        'directSurfaceReview': reviewed,
                        'provisionalODNMetres': round((m['value_ft']+datum['liverpoolToNewlynFeet'])*.3048, 6),
                        'settingSource': source.get('setting_source'),
                        'settingRule': source.get('setting_rule'),
                        'notes': source.get('notes'), 'mosaics': source.get('mosaics', []),
                        'sourceViews': source.get('views', []),
                        'readerCount': len(source.get('readers', [])),
                        'positionSpreadMetres': source.get('spread_m'),
                        'mappedWaterOverlap': bool(overlap)})

    pairs = []
    tree = cKDTree([r['positionBNG'] for r in records])
    for a, b in sorted(tree.query_pairs(5)):
        ra, rb = records[a], records[b]
        confirmed = (ra.get('surfaceReview', {}).get('duplicateOf') == rb['id']
                     or rb.get('surfaceReview', {}).get('duplicateOf') == ra['id'])
        pairs.append({'ids': [ra['id'], rb['id']],
                      'distanceMetres': round(float(np.linalg.norm(np.subtract(ra['positionBNG'], rb['positionBNG']))), 3),
                      'differenceFeet': round(abs(ra['value_ft']-rb['value_ft']), 3),
                      'families': [ra['surfaceFamily'], rb['surfaceFamily']],
                      'status': 'confirmed-duplicate' if confirmed else 'nearby-pair-review',
                      'action': 'Withhold duplicate; retain reviewed canonical observation.' if confirmed else 'Retain distinct observations unless map dots prove duplication.'})
    # A large nearby difference is a review lead, not an automatic correction.
    ground = [r for r in records if r['surfaceFamily'] == 'ground']
    conflicts = []
    for a, b in sorted(cKDTree([r['positionBNG'] for r in ground]).query_pairs(30)):
        ra, rb = ground[a], ground[b]
        difference = abs(ra['provisionalODNMetres']-rb['provisionalODNMetres'])
        if difference > 1:
            conflicts.append({'ids': [ra['id'], rb['id']], 'differenceMetres': round(difference, 4),
                              'action': 'Check dot, surface and intervening earthwork; real relief may explain difference.'})

    candidates = [r for r in records if r['auditStatus'] in {'reviewed-ground', 'candidate-ground'}]
    reviewed = [r for r in records if r['auditStatus'] == 'reviewed-ground']
    roads = [r for r in records if r['auditStatus'] in {'reviewed-road', 'candidate-road'}]
    surface_candidates = candidates + roads
    e0, n0, e1, n1 = region['reviewBoundsBNG']
    step = 50
    east, north = np.meshgrid(np.arange(e0+step/2, e1, step), np.arange(n1-step/2, n0, -step))
    points = np.column_stack([east.ravel(), north.ravel()])
    distances, reviewed_distances = nearest(points, candidates), nearest(points, reviewed)
    surface_distances = nearest(points, surface_candidates)
    geometries = shapely.points(points)
    dry = ~shapely.intersects(geometries, water)
    corridor = dry & (shapely.distance(geometries, network_water) <= 750)
    # Explicit working distances, not statistical confidence intervals.
    classes = np.select([~dry, surface_distances <= 100, surface_distances <= 250, surface_distances <= 500], [0, 1, 2, 3], default=4).astype('u1')
    colours = np.array([[118,188,199], [116,168,134], [201,215,157], [231,196,139], [215,179,170]], dtype='u1')
    Image.fromarray(colours[classes].reshape(*east.shape, 3)).save(OUT/'elevation-coverage.png')
    for name, values in [('ground-distance', distances), ('reviewed-ground-distance', reviewed_distances), ('surface-distance', surface_distances)]:
        values.astype('<f4').tofile(OUT/(name+'.f32'))
    classes.tofile(OUT/'elevation-coverage.u8')

    # Distinguish unread cached period sheets from gaps outside the cached
    # extent. Never offer 1848 sheets as replacements for 1890s observations.
    cached = []
    record_mosaics = Counter(m for r in records if r['id'] not in added_sources for m in r['mosaics'])
    added_mosaics = Counter(m for r in records if r['id'] in added_sources for m in r['mosaics'])
    for row in manifest['mosaics']:
        name = row['name']
        if not name.startswith(('m18_','q18_')):
            continue
        folder = 'mosaics' if name.startswith('m18_') else 'mosaics-25inch'
        meta_path = ROOT/'reference/spot-heights'/folder/(name+'.json')
        image_path = meta_path.with_suffix('.png')
        if not meta_path.exists() or not image_path.exists():
            continue
        meta = json.loads(meta_path.read_text())
        corners = [v for k,v in meta['corners'].items() if k!='centre']
        b = [min(c['bng_e'] for c in corners),min(c['bng_n'] for c in corners),
             max(c['bng_e'] for c in corners),max(c['bng_n'] for c in corners)]
        if not box(*b).intersects(box(e0,n0,e1,n1)):
            continue
        paths.append(meta_path)
        cached.append({'name':name,'boundsBNG':b,'image':str(image_path.relative_to(ROOT)),
                       'layer':meta.get('layer'),'manifestAvailable':bool(row.get('available')),
                       'completedReads':len(row.get('done',{})), 'snapshotRecords':record_mosaics[name],
                       'regionalSupplementRecords':added_mosaics[name],
                       'missingTiles':len(meta.get('missing_tiles',[]))})
    cells = []
    for n in range(n0, n1, 500):
        for e in range(e0, e1, 500):
            inside = (points[:,0] >= e) & (points[:,0] < e+500) & (points[:,1] >= n) & (points[:,1] < n+500)
            selected = [r for r in records if e <= r['positionBNG'][0] < e+500 and n <= r['positionBNG'][1] < n+500]
            focus = inside & corridor
            if not focus.any():
                continue
            unresolved = [r for r in selected if r['auditStatus'] in {'ground-needs-review', 'inferred-ground', 'road-needs-review', 'inferred-road'}]
            sparse = int(np.count_nonzero(focus & (surface_distances > 250))) * step**2
            maps = [m for m in cached if box(*m['boundsBNG']).intersects(box(e,n,e+500,n+500))]
            unread = [m['name'] for m in maps if m['manifestAvailable'] and m['completedReads']==0 and m['snapshotRecords']==0 and m['regionalSupplementRecords']==0]
            cells.append({'id': f'{e}-{n}', 'boundsBNG': [e,n,e+500,n+500],
                          'corridorDrySampleAreaM2': int(focus.sum())*step**2,
                          'beyond250mSampleAreaM2': sparse,
                          'nearestGroundDistanceAtCentreMetres': round(float(nearest(np.array([[e+250,n+250]]), candidates)[0]), 1),
                          'nearestSurfaceDistanceAtCentreMetres': round(float(nearest(np.array([[e+250,n+250]]), surface_candidates)[0]), 1),
                          'statusCounts': dict(Counter(r['auditStatus'] for r in selected)),
                          'surfaceReviewIds': [r['id'] for r in unresolved],
                          'mosaics': sorted({m for r in selected for m in r['mosaics']}),
                          'cachedMosaics': [m['name'] for m in maps], 'cachedUnreadMosaics':unread,
                          'sourceCoverageStatus': 'cached-unread-maps' if unread else 'cached-maps-review-readings' if maps else 'outside-cached-period-map-coverage',
                          'action': 'Review existing ground/street candidates and map dots.' if unresolved else 'Search source maps for ground or lane/street levels; check raised approaches and bank crossings.'})
    cells.sort(key=lambda c: (-c['beyond250mSampleAreaM2'], -len(c['surfaceReviewIds']), c['id']))
    patches = network['bankSections']['terrainPatches']

    def coverage(mask):
        return {'drySampleAreaKm2': round(float(mask.sum()*step**2/1e6), 4),
                'withinMetresPercent': {str(d): round(float(np.mean(distances[mask] <= d)*100), 2) for d in [100,250,500]},
                'groundAndRoadWithinMetresPercent': {str(d): round(float(np.mean(surface_distances[mask] <= d)*100), 2) for d in [100,250,500]},
                'reviewedWithin250mPercent': round(float(np.mean(reviewed_distances[mask] <= 250)*100), 2)}

    result = {'schemaVersion': 1, 'targetEpoch': '1900', 'boundsBNG': region['reviewBoundsBNG'],
              'status': 'evidence audit; no new terrain or flood elevations applied',
              'verticalReference': datum, 'temporalPolicy': epochs['temporalPolicy'],
              'records': records, 'nearbyPairs': pairs, 'localGroundDifferences': conflicts,
              'regionalSupplement':{'observations':len(added),'scope':supplement['scope'],
                                    'withheldCandidates':supplement['withheldCandidates'],
                                    'overlapChecks':supplement.get('overlapChecks',[]),
                                    'outlierDecisions':supplement.get('outlierDecisions',[]),
                                    'reviewAreas':{area:[min(r['positionBNG'][0] for r in records if r.get('regionalSurfaceReview',{}).get('reviewArea')==area)-150,
                                                        min(r['positionBNG'][1] for r in records if r.get('regionalSurfaceReview',{}).get('reviewArea')==area)-150,
                                                        max(r['positionBNG'][0] for r in records if r.get('regionalSurfaceReview',{}).get('reviewArea')==area)+150,
                                                        max(r['positionBNG'][1] for r in records if r.get('regionalSurfaceReview',{}).get('reviewArea')==area)+150]
                                                   for area in sorted({r['regionalSurfaceReview']['reviewArea'] for r in records if r.get('regionalSurfaceReview',{}).get('reviewArea')})}},
              'terrainExclusions':exclusions,
              'opusUpdate':opus_update,
              'summary': {'observations': len(records), 'surfaceFamilies': dict(Counter(r['surfaceFamily'] for r in records)),
                          'baselineObservations':len(region['heightMarks']),'regionalSupplementObservations':len(added),
                          'opusAddedObservations':opus_update['newObservations'],
                          'auditStatuses': dict(Counter(r['auditStatus'] for r in records)),
                          'reasons': dict(Counter(reason for r in records for reason in r['auditReasons'])),
                          'usableGroundCandidates': len(candidates), 'reviewedGround': len(reviewed),
                          'usableRoadCandidates': len(roads), 'usableSurfaceCandidates': len(surface_candidates),
                          'nearbyPairs': len(pairs), 'localGroundDifferences': len(conflicts),
                          'surveyDates': dict(Counter(r['survey_dates'] for r in records)),
                          'datumCounts': dict(Counter(r['datum'] for r in records)),
                          'reviewWindowCoverage': coverage(dry), 'riverCorridorCoverage': coverage(corridor)},
              'existingTerrain': {'patchCount': len(patches), 'patchAreaM2': sum(p['areaM2'] for p in patches),
                                  'patchControlIds': sorted({c['id'] for p in patches for c in p['controls']}),
                                  'coreControlIds': [c['id'] for c in core['controls']],
                                  'policy': 'Preserve reviewed surface functions and structural protections; a reviewed control is not always fitted exactly at a protected structure.'},
              'grid': {'cellSizeMetres': step, 'width': east.shape[1], 'height': east.shape[0],
                       'orientation': 'rows north to south; cell centres; EPSG:27700',
                       'preview': 'elevation-coverage.png', 'classesFile': 'elevation-coverage.u8',
                       'distanceFile': 'ground-distance.f32', 'reviewedDistanceFile': 'reviewed-ground-distance.f32',
                       'surfaceDistanceFile': 'surface-distance.f32',
                       'legend': {'0': 'mapped water or reviewed canal/structure exclusion', '1': 'ground or street candidate within 100 m',
                                  '2': 'within 100–250 m', '3': 'within 250–500 m', '4': 'over 500 m'},
                       'limitations': 'Euclidean proximity only, across all barriers. Counts estimate area from 50 m cell centres. Nearby evidence does not establish a surveyed surface or same-compartment interpolation support. Candidate readings have conditional date/datum attribution.'},
              'reviewPriorityCells': cells,
              'cachedPeriodMosaics': cached,
              'methodDecision': {
                  'ground': 'Build constrained interpolation within mapped dry compartments using ground AND street levels. Compare local linear triangulation with local inverse-distance interpolation using held-out observations and separate ground/road validation. Keep observation roles through fitting; keep bridge decks, bank crests, railways and building benchmarks out of general ground interpolation.',
                  'streets': 'Street dots anchor the contemporary developed surface at their measured levels. Marsh lanes may constrain neighbouring ground approximately where better evidence is absent. Treat lane-to-marsh relief as an uncertain local difference, not a reason to discard the lane level. No automatic fill subtraction or large fill assumption for built-up streets; review industrial fill and raised approaches separately.',
                  'userWorkingAssumption': 'The author expects marsh lanes often to be only slightly raised and ordinary pre-mechanised street fill generally limited. This is a reconstruction prior to test locally, not a measured fill thickness or a rule for every industrial site.',
                  'support': 'Audit 100/250/500 m distances are review bins, not interpolation radii. Establish support by compartment, control distribution and validation; do not fill every cell merely to make a complete raster.',
                  'gaps': 'Use priority cells for targeted source review. Unsupported terrain must carry an explicit fallback/uncertainty class; the 2003 surface remains a dated comparison, never an automatic c1900 fill.',
                  'transitions': 'Reconcile adjoining ground and structure edges on one terrain, preserving reviewed surfaces, water passages and core protections. Review transitions before applying to the scene or solver.',
                  'validation': 'Check source/datum provenance, held-out heights, barrier crossings, sparse-cell behaviour and mesh joins; numerical control fit alone cannot demonstrate historical accuracy.'},
              'inputHashes': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    (OUT/'elevation-audit.json').write_text(json.dumps(result, separators=(',', ':'))+'\n')
    print(json.dumps(result['summary'], indent=2))


if __name__ == '__main__':
    build()
