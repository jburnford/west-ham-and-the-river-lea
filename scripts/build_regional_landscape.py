"""Compose historical anchors and explicitly estimated broad regional relief."""
import hashlib
import json
from pathlib import Path

import numpy as np
import shapely
from PIL import Image
from scipy.ndimage import gaussian_filter, distance_transform_edt
from scipy.sparse import coo_matrix, diags
from scipy.sparse.csgraph import dijkstra
from scipy.sparse.linalg import cg
from shapely.geometry import Polygon
from shapely.geometry import shape as geometry_shape
from regional_marsh_baseline import early_marsh_field
from regional_surface_layers import add_later_surfaces
from regional_continuous_structures import add_continuous_structures

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/data/lower-lea-region'


def solve_correction(adjacency, base, fixed, targets, decay_cells):
    """Screened harmonic residual, with exact Dirichlet historical anchors.

    A disconnected component with no historical anchor has zero adjustment.
    The screen anchors the far field to broad modern relief; it is an explicit
    modelling assumption, not inferred historical support.
    """
    degree = np.asarray(adjacency.sum(axis=1)).ravel()
    unknown = ~fixed
    residual = np.zeros(len(base))
    residual[fixed] = targets[fixed] - base[fixed]
    matrix = diags(degree + 1 / decay_cells**2) - adjacency
    system = matrix[unknown][:, unknown].tocsr()
    rhs = adjacency[unknown][:, fixed] @ residual[fixed]
    solution, info = cg(system, rhs, M=diags(1 / system.diagonal()),
                        rtol=1e-8, atol=1e-9, maxiter=3000)
    if info:
        raise RuntimeError(f'Landscape correction failed to converge: {info}')
    residual[unknown] = solution
    return base + residual, float(np.max(np.abs(system @ solution - rhs), initial=0))


def build():
    inputs = [Path(__file__).resolve(), ROOT/'scripts/regional_marsh_baseline.py',
              ROOT/'scripts/regional_surface_layers.py', ROOT/'scripts/regional_continuous_structures.py']

    def read(path, dtype=None):
        p = ROOT / path
        inputs.append(p)
        return np.fromfile(p, dtype) if dtype else json.loads(p.read_text())

    policy = read('data/maps/lower-lea-region/regional-landscape-policy-1900.json')
    early_config = read(policy['regionalMarshBaselineFile'])
    early_review = read(early_config['reviewFile'])
    for observation in early_review['observations']:
        for path,digest in observation['sourceHashes'].items():
            source=ROOT/path
            assert hashlib.sha256(source.read_bytes()).hexdigest()==digest,path
            inputs.append(source)
    infrastructure = read('docs/data/infrastructure.json')
    ground_plan=read('docs/data/ground-plan.json')
    yards=ground_plan['sites']
    structures_config=read('data/maps/lower-lea-region/continuous-embankments-1900.json')
    for review in structures_config.get('surfaceReview',[]):
        source=ROOT/review['source'];assert hashlib.sha256(source.read_bytes()).hexdigest()==review['sourceSha256']
        inputs.append(source)
    compartments = [read(path) for path in policy.get('marshCompartmentFiles', [])]
    for compartment in compartments:
        for path, digest in compartment['sourceHashes'].items():
            source = ROOT / path
            assert hashlib.sha256(source.read_bytes()).hexdigest() == digest, path
            inputs.append(source)
    region = read('docs/data/lower-lea-region/index.json')
    trial = read('docs/data/lower-lea-region/elevation-trial.json')
    audit = read('docs/data/lower-lea-region/elevation-audit.json')
    network = read('docs/data/river-system-1900.json')
    marsh_ditches = read('data/maps/marsh-ditches.json')
    shape = (trial['height'], trial['width'])
    step = trial['cellSizeMetres']
    modern = read('docs/data/lower-lea-region/' + region['terrain']['heightFile'], '<f4').reshape(shape)
    historical = read('docs/data/lower-lea-region/' + trial['heightFile'], '<f4').reshape(shape)
    support = read('docs/data/lower-lea-region/' + trial['supportFile'], 'u1').reshape(shape)
    assert region['reviewBoundsBNG'] == trial['boundsBNG']
    assert region['terrain']['cellSizeMetres'] == step
    e0, n0, e1, n1 = trial['boundsBNG']
    east, north = np.meshgrid(np.arange(e0 + step/2, e1, step), np.arange(n1 - step/2, n0, -step))
    xy = np.column_stack([east.ravel(), north.ravel()])
    exclusions = shapely.union_all([
        Polygon([(538900+x, 183209-z) for x, z in p[0]],
                [[(538900+x, 183209-z) for x, z in ring] for ring in p[1:]])
        for reach in network['reaches'] for p in reach['polygons']] +
        [Polygon(r['polygonBNG']) for r in audit['terrainExclusions']])
    valid_modern = np.isfinite(modern) & (support != 2)
    sigma = policy['modernReliefSigmaMetres'] / step
    numerator = gaussian_filter(np.where(valid_modern, modern, 0).astype(float), sigma)
    denominator = gaussian_filter(valid_modern.astype(float), sigma)
    base = np.divide(numerator, denominator, out=np.zeros(shape), where=denominator > 0)
    # Smoothing is only a broad relief prior, not a new observation. Retain
    # source gaps except where historical interpolation supplies the surface.
    domain = (valid_modern | np.isfinite(historical)) & (support != 2)
    base[~valid_modern & np.isfinite(historical)] = historical[~valid_modern & np.isfinite(historical)]
    marsh_prior = policy['marshPrior']
    prior_fields = []
    for patch in network['bankSections']['terrainPatches']:
        if patch['id'] in marsh_prior['fieldPatchIds']:
            prior_fields.extend(Polygon([(538900+x,183209-z) for x,z in p[0]],
                                [[(538900+x,183209-z) for x,z in ring] for ring in p[1:]]) for p in patch['polygons'])
    if marsh_prior['includeMappedMarshDitchesFootprint']:
        prior_fields.append(Polygon([(538900+x,183209-z) for x,z in marsh_ditches['marshFootprint']]))
    prior_field = shapely.union_all(prior_fields).buffer(-marsh_prior['interiorSetbackMetres'])
    in_marsh = shapely.contains_xy(prior_field, east, north) & domain
    prior_weight = np.zeros(shape)
    prior_weight[in_marsh] = np.clip(shapely.distance(shapely.points(xy[in_marsh.ravel()]), prior_field.boundary) /
                                           marsh_prior['boundaryTransitionMetres'], 0, 1)
    marsh_prior_odn = (marsh_prior['heightFeet']+trial['verticalReference']['liverpoolToNewlynFeet'])*.3048
    base[in_marsh] += prior_weight[in_marsh]*(marsh_prior_odn-base[in_marsh])
    # A mapped marsh compartment must not retain modern infill around its
    # perimeter. Separate historical bank/garden surfaces are fitted below.
    for compartment in compartments:
        selected = shapely.contains_xy(geometry_shape(compartment['geometryBNG']), east, north) & domain
        base[selected] = marsh_prior_odn
        prior_weight[selected] = 1
    early_base, early_weight, early_distance = early_marsh_field(
        early_config, early_review, east, north, trial['verticalReference']['liverpoolToNewlynFeet'])
    early_weight[~domain]=0
    early_full=(early_weight>=1)&domain
    base += early_weight*(early_base-base)
    prior_weight[early_full]=0
    # Road-to-road triangles are not underlying marsh ground. Keep the
    # original experiment intact, but constrain this substrate only with
    # actual later ground controls inside the regional marsh envelope.
    fixed = np.isfinite(historical)&~early_full
    targets = historical.copy()
    anchor_cells = {}
    records = {r['id']:r for r in audit['records']}
    substrate_deferred = []
    for control in trial['controls']:
        e, n = control['positionBNG']
        col, row = int(np.floor((e-e0)/step)), int(np.floor((n1-n)/step))
        if not (0 <= row < shape[0] and 0 <= col < shape[1]) or not domain[row, col] or fixed[row, col]:
            continue
        if early_full[row,col]:
            record=records[control['id']]
            if control['family']!='ground':
                continue
            if record['setting']!='marsh' and record['auditStatus']!='reviewed-ground':
                substrate_deferred.append(control['id'])
                continue
        centre = [east[row, col], north[row, col]]
        if shapely.intersects(shapely.LineString([(e, n), centre]), exclusions):
            continue
        anchor_cells.setdefault((row, col), []).append(control)
    isolated = []
    for (row, col), controls in anchor_cells.items():
        fixed[row, col] = True
        targets[row, col] = np.median([c['heightODNMetres'] for c in controls])
        isolated.append({'row':row, 'col':col, 'ids':[c['id'] for c in controls],
                         'heightODNMetres':float(targets[row, col]),
                         'note':'Nearest 10 m cell; median if multiple controls share a cell. Not an exact point-sampled surface.'})
    # Existing reviewed field boundaries let sparse marsh dots constrain the
    # field estimate, rather than merely pinholes in a later made-ground prior.
    # Keep this interpreted support separate from the accepted TIN and controls.
    marsh_mask = np.zeros(shape, dtype=bool)
    marsh_estimates = []
    records = {r['id']:r for r in audit['records']}
    historical_fixed = fixed.copy()
    compartment_mask = np.zeros(shape, dtype=bool)
    raised_mask = np.zeros(shape, dtype=bool)
    raised_targets = np.full(shape,np.nan)
    compartment_estimates = []
    for compartment in compartments:
        field = geometry_shape(compartment['geometryBNG'])
        field_mask = shapely.contains_xy(field, east, north) & domain
        surfaces = []
        # These estimates stay within their mapped footprints. They cannot
        # supply a general marsh level or enlarge historical TIN coverage.
        for surface in compartment['separateSurfaces']:
            control = records[surface['sourceObservationId']]
            assert control['value_ft'] == surface['heightFeet']
            surfaces.append((surface['id'], geometry_shape(surface['geometryBNG']),
                             np.full(shape, control['provisionalODNMetres']), [control['id']]))
        for patch_id in compartment['bankPatchIds']:
            patch = next(p for p in network['bankSections']['terrainPatches'] if p['id'] == patch_id)
            bank = shapely.union_all([Polygon([(538900+x,183209-z) for x,z in p[0]],
                [[(538900+x,183209-z) for x,z in ring] for ring in p[1:]]) for p in patch['polygons']])
            controls = sorted(patch['controls'], key=lambda c:c['positionBNG'][1])
            assert all(c['role'] == 'bank' for c in controls)
            bank_heights = np.interp(north, [c['positionBNG'][1] for c in controls],
                                    [c['heightODNMetres'] for c in controls])
            surfaces.append((patch_id, bank, bank_heights, [c['id'] for c in controls]))
        separate = []
        for surface_id, footprint, levels, source_ids in surfaces:
            selected = shapely.contains_xy(footprint, east, north) & field_mask & ~fixed
            raised_targets[selected] = levels[selected]
            raised_mask |= selected
            separate.append({'id':surface_id, 'sourceIds':source_ids, 'cells':int(selected.sum())})
        selected = shapely.contains_xy(field.buffer(-compartment['interiorSetbackMetres']), east, north) & domain & ~fixed & ~raised_mask & ~early_full
        targets[selected] = (compartment['marshHeightFeet']+trial['verticalReference']['liverpoolToNewlynFeet'])*.3048
        fixed[selected] = True
        compartment_mask |= selected
        compartment_estimates.append({'id':compartment['id'], 'cells':int(selected.sum()),
            'areaKm2':round(float(selected.sum()*step**2/1e6),4), 'heightFeet':compartment['marshHeightFeet'],
            'status':'working marsh prior within reviewed field; not surveyed interior', 'separateSurfaces':separate})
    for estimate in policy.get('localMarshEstimates', []):
        patch = next(p for p in network['bankSections']['terrainPatches'] if p['id']==estimate['patchId'])
        field = shapely.union_all([
            Polygon([(538900+x,183209-z) for x,z in p[0]],
                    [[(538900+x,183209-z) for x,z in ring] for ring in p[1:]])
            for p in patch['polygons']]).buffer(-estimate['interiorSetbackMetres'])
        controls = sorted([records[i] for i in estimate['controlIds']], key=lambda r:r['positionBNG'][1])
        assert all(c['auditStatus']=='reviewed-ground' for c in controls)
        field_heights = np.interp(north, [c['positionBNG'][1] for c in controls],
                                 [c['provisionalODNMetres'] for c in controls])
        selected = shapely.contains_xy(field, east, north) & domain & ~fixed
        targets[selected] = field_heights[selected]
        fixed[selected] = True
        marsh_mask |= selected
        marsh_estimates.append({**estimate, 'cells':int(selected.sum()),
                                'areaKm2':round(float(selected.sum()*step**2/1e6),4),
                                'sourceValuesFeet':[c['value_ft'] for c in controls],
                                'heightRangeODNMetres':[float(field_heights[selected].min()),float(field_heights[selected].max())]})
    grid_ids = np.arange(domain.size).reshape(shape)
    pairs = []
    for a, b in [(grid_ids[:, :-1], grid_ids[:, 1:]), (grid_ids[:-1], grid_ids[1:])]:
        ok = domain.ravel()[a] & domain.ravel()[b]
        # Model-source boundary only, never a hydraulic barrier: residuals
        # from modern/non-marsh terrain must not raise the early substrate.
        ok &= early_full.ravel()[a] == early_full.ravel()[b]
        aa, bb = a[ok], b[ok]
        clear = ~shapely.intersects(shapely.linestrings(np.stack([xy[aa], xy[bb]], axis=1)), exclusions)
        pairs.append((aa[clear], bb[clear]))
    a = np.concatenate([p[0] for p in pairs]); b = np.concatenate([p[1] for p in pairs])
    compact = np.full(domain.size, -1, dtype=int)
    compact[domain.ravel()] = np.arange(domain.sum())
    ai, bi = compact[a], compact[b]
    adjacency = coo_matrix((np.ones(2*len(a)), (np.r_[ai, bi], np.r_[bi, ai])),
                           shape=(int(domain.sum()), int(domain.sum()))).tocsr()
    print(f'Solving {domain.sum()} land cells; {historical_fixed.sum()} historical and {(fixed & ~historical_fixed).sum()} estimated constraint cells.', flush=True)
    result, solver_error = solve_correction(adjacency, base[domain], fixed[domain], targets[domain],
                                             policy['correctionDecayMetres']/step)
    height = np.full(shape, np.nan)
    height[domain] = result
    # The old historical TIN was fixed through the partial-weight edge strip,
    # overriding the base blend. Apply this explicitly estimated transition
    # after the two correction domains are solved. Extend only the small
    # interior historical residual to meet the actual marsh-side surface.
    transition=(early_weight>0)&(early_weight<1)&domain
    nearest=distance_transform_edt(~early_full,return_distances=False,return_indices=True)
    edge_target=early_base+(height[tuple(nearest)]-base[tuple(nearest)])
    height[transition]=(1-early_weight[transition])*height[transition]+early_weight[transition]*edge_target[transition]
    distance = np.full(shape, np.inf)
    distance[domain] = dijkstra(adjacency, directed=False, indices=np.flatnonzero(historical_fixed[domain]),
                                min_only=True) * step
    kind = np.zeros(shape, dtype='u1')
    kind[domain] = 4
    kind[domain & (distance <= policy['correctionDecayMetres'])] = 3
    kind[prior_weight >= 1] = 7
    kind[early_full] = 9
    kind[fixed] = 2
    kind[marsh_mask] = 6
    kind[compartment_mask] = 7
    kind[np.isfinite(historical)&~early_full] = 1
    kind[transition]=14
    kind[support == 2] = 5
    ground_kind=kind.copy()
    ground, surface_layers = add_later_surfaces(height,kind,east,north,early_full,
        exclusions,audit,trial,infrastructure,yards,trial['verticalReference'])
    continuous=add_continuous_structures(height,kind,ground,east,north,exclusions,network,
        audit,infrastructure,ground_plan['neighbourhood']['sewer'],trial['verticalReference'],structures_config,OUT)
    surface_layers['features'].extend(continuous['features'])
    used=set(surface_layers['usedSourceIds'])|set(continuous['usedSourceIds'])
    surface_layers['usedSourceIds']=sorted(used)
    surface_layers['unplacedSurfaceObservationIds']=[i for i in surface_layers['unplacedSurfaceObservationIds'] if i not in used]
    height[raised_mask]=raised_targets[raised_mask]
    kind[raised_mask]=8
    for c in isolated:
        c['visibleInSurface']=bool(kind[c['row'],c['col']]==2)
        c['boundaryBlendWeight']=float(early_weight[c['row'],c['col']]) if transition[c['row'],c['col']] else 0
        c['modelGroundODNMetres']=float(ground[c['row'],c['col']])
    ground_kind.tofile(OUT/'landscape-1900.ground-kind.u8')
    ground.astype('<f4').tofile(OUT/'landscape-1900.ground.f32')
    np.where(early_weight>0,early_base,np.nan).astype('<f4').tofile(OUT/'landscape-1900.early-marsh.f32')
    early_weight.astype('<f4').tofile(OUT/'landscape-1900.early-weight.f32')
    early_distance.astype('<f4').tofile(OUT/'landscape-1900.early-distance.f32')
    height.astype('<f4').tofile(OUT/'landscape-1900.odn.f32')
    base = np.where(domain, base, np.nan)
    base.astype('<f4').tofile(OUT/'landscape-1900.broad-relief.f32')
    kind.tofile(OUT/'landscape-1900.kind.u8')
    distance.astype('<f4').tofile(OUT/'landscape-1900.anchor-distance.f32')
    prior_weight.astype('<f4').tofile(OUT/'landscape-1900.marsh-prior-weight.f32')
    palette = np.array([[235,232,226], [62,120,84], [46,94,69], [206,185,130], [192,166,156], [118,188,199], [123,166,130], [155,190,151], [161,139,88], [144,190,166], [189,148,111], [151,123,97], [175,151,79], [145,132,173], [172,176,145]], dtype='u1')
    Image.fromarray(palette[kind]).save(OUT/'landscape-1900.evidence.png')
    colours = np.array([[90,122,116], [133,164,146], [176,188,145], [210,202,164], [189,161,126], [151,126,104], [229,221,199]])
    rgb = np.stack([np.interp(np.nan_to_num(height), [-1,0,2,5,10,20,35], colours[:,k]) for k in range(3)], axis=-1)
    # Shading is visual only. A masked neighbour does not create a cliff.
    dx = np.zeros(shape); dz = np.zeros(shape)
    good = domain[:, 1:] & domain[:, :-1]
    dx[:, :-1] = np.where(good, np.nan_to_num(height[:, 1:] - height[:, :-1]) / step, 0)
    good = domain[1:] & domain[:-1]
    dz[:-1] = np.where(good, np.nan_to_num(height[1:] - height[:-1]) / step, 0)
    shade = np.clip(.88 + .5*(-dx + dz), .55, 1.15)
    rgb = np.clip(rgb * shade[..., None], 0, 255).astype('u1')
    rgb[~domain] = [235,232,226]; rgb[support == 2] = [118,188,199]
    Image.fromarray(rgb).save(OUT/'landscape-1900.png')
    # A 20 m display mesh uses the same height field. Reject the complete face,
    # not just its vertices, wherever a narrow water/structure exclusion cuts it.
    corners = grid_ids[:-2:2, :-2:2].ravel()
    faces = np.concatenate([np.column_stack([corners, corners+2*shape[1], corners+2]),
                            np.column_stack([corners+2, corners+2*shape[1], corners+2*shape[1]+2])])
    faces = faces[domain.ravel()[faces].all(axis=1)]
    faces = faces[~shapely.intersects(shapely.polygons(xy[faces]), exclusions)]
    faces.astype('<u4').tofile(OUT/'landscape-1900.faces.u32')
    counts = {str(k):{'cells':int((kind == k).sum()), 'areaKm2':round(float((kind == k).sum()*step**2/1e6), 4)} for k in range(15)}
    meta = {'schemaVersion':1, 'targetEpoch':'1900', 'status':'working landscape; estimated areas retain modern-relief uncertainty; not applied to detailed scene or flood solver',
            'boundsBNG':trial['boundsBNG'], 'cellSizeMetres':step, 'width':shape[1], 'height':shape[0],
            'orientation':'rows north to south; cell centres; EPSG:27700', 'verticalReference':trial['verticalReference'],
            'heightFile':'landscape-1900.odn.f32', 'kindFile':'landscape-1900.kind.u8',
            'broadReliefFile':'landscape-1900.broad-relief.f32', 'anchorDistanceFile':'landscape-1900.anchor-distance.f32',
            'marshPriorWeightFile':'landscape-1900.marsh-prior-weight.f32', 'marshPriorODNMetres':marsh_prior_odn,
            'groundFile':'landscape-1900.ground.f32', 'groundKindFile':'landscape-1900.ground-kind.u8', 'earlyMarshFile':'landscape-1900.early-marsh.f32',
            'earlyMarshWeightFile':'landscape-1900.early-weight.f32', 'earlyMarshDistanceFile':'landscape-1900.early-distance.f32',
            'preview':'landscape-1900.png', 'evidencePreview':'landscape-1900.evidence.png',
            'displayMesh':{'faceFile':'landscape-1900.faces.u32', 'triangleCount':len(faces), 'spacingMetres':20,
                           'vertexOrder':'Full 10 m raster row-major; faces select every second sample. No face intersects a mapped exclusion.'},
            'kindLegend':{'0':'missing source coverage', '1':'historical ground/street interpolation', '2':'historical control at nearest grid cell',
                          '3':'estimated relief within 350 m dry-grid travel of a historical anchor', '4':'distant or disconnected modern-relief estimate', '5':'water or reviewed structure exclusion; no ground/bed estimate',
                          '6':'local marsh estimate from reviewed ground readings and field boundaries',
                          '7':'12 ft marsh prior, adjusted by nearby historical ground/street constraints; estimated',
                          '8':'local bank or cottage-garden surface estimate; not marsh ground',
                          '9':'regional marsh estimate from 1848–51 low-lane/ground evidence, adjusted by later ground controls',
                          '10':'later street level within mapped road corridor',
                          '11':'later yard estimate within mapped premises',
                          '12':'continuous river/canal bank profile; observed and inferred crest heights',
                          '13':'railway or sewer formation; measured levels where available, otherwise existing interpretation',
                          '14':'approximate marsh-edge transition; blended estimate, not a surveyed height',
                          '15':'elevated railway/sewer water span; fine mesh only, not ground'},
            'localMarshEstimates':marsh_estimates,
            'marshCompartmentEstimates':compartment_estimates,
            'regionalMarshBaseline':{'config':early_config,'regions':early_review['regions'],
                'selectedEarlyReadings':len(early_review['observations']),
                'acceptedEarlyProxies':sum(r['baselineUse'] for r in early_review['observations']),
                'edgeTransitionAreaKm2':round(float(transition.sum()*step**2/1e6),4),
                'fullWeightAreaKm2':round(float(early_full.sum()*step**2/1e6),4)},
            'continuousStructures':continuous,
            'laterSurfaceLayers':surface_layers, 'deferredSubstrateObservationIds':substrate_deferred,
            'policy':policy, 'method':'Regional marsh substrate from selected 1848–51 low-lane/ground proxies, with later ground anchors. Later street, yard, bank/wall and railway/sewer surfaces stay within mapped footprints. The partial-weight edge strip explicitly blends the solved outer surface toward the adjacent marsh residual; it is not an exact historical control surface. Outside the marsh envelope, retain the previous historical TIN and corrected 100 m broad modern prior. Correction decay length is 350 m; no correction edge crosses mapped exclusions or the boundary of the fully early-derived substrate. This source boundary does not define a hydraulic barrier. Original ground/street TIN experiment remains separate and unchanged.',
            'counts':counts, 'landAreaKm2':round(float(domain.sum()*step**2/1e6),4), 'historicalControlCells':isolated,
            'earlierMarshConstraintsApplied':sum(r['baselineUse'] for r in early_review['observations']), 'solverMaxEquationResidual':solver_error,
            'limitations':['Outside the mapped marsh envelope, estimated relief may retain later fill, cuttings and drainage changes; no uniform 30 cm accuracy claim.',
                           'Gaussian broad relief is a regional prior; only the historical correction is confined by the dry-edge graph.',
                           'Ten metre cells cannot resolve every narrow bank, road or drain. Structures and hydraulic connections still require reconciliation.',
                           'Early marsh support consists mostly of low-lane proxies; sparse field interiors are estimated. Datum and envelope boundaries remain provisional.',
                           'Continuous banks, railways and sewer surfaces are reconstructed along mapped features. Unsampled crest heights remain estimates; the fine mesh and the coarse raster are not yet integrated into regional flood barriers.',
                           'No missing ground is silently converted to zero elevation or a hydraulic wall.'],
            'inputHashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}}
    (OUT/'landscape-1900.json').write_text(json.dumps(meta, indent=2)+'\n')
    print(json.dumps({'landAreaKm2':meta['landAreaKm2'], 'counts':counts, 'isolatedControlCells':len(isolated), 'solverError':solver_error}, indent=2))


if __name__ == '__main__':
    build()
