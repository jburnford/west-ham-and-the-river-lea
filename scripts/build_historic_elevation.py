#!/usr/bin/env python3
"""Build a dated, bounded terrain overlay from an immutable reading snapshot.

The earlier scene assets remain the comparison scaffold. Buildings, roads,
railways, sewer, water and drainage corridors are protected, except the explicitly
reviewed local road earthwork and separately modelled drainage section.
The same grid transforms both terrain meshes; additional tessellated ground
replaces the old flat floor wherever the trial extends beyond those meshes.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import shapely
from shapely import contains_xy, distance, points
from shapely.geometry import LineString, Point, Polygon, box, mapping
from shapely.ops import unary_union

from historic_elevation import apply_grid, sample_grid, select_controls, smooth
from historic_drainage import apply_section, water_triangles
from manor_road import evidence as manor_evidence, profile as road_profile, domain as road_domain

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT/'docs/data'
RESEARCH = ROOT/'reference/topography-research-2026-09-28/terrain-epochs'


def load(path):
    return json.loads((ROOT/path).read_text())


def polygons(geom):
    return [g for g in getattr(geom, 'geoms', [geom]) if g.geom_type == 'Polygon' and not g.is_empty]


def rings(geom):
    return [[list(p.exterior.coords), *[list(h.coords) for h in p.interiors]] for p in polygons(geom)]


def from_rings(items):
    return unary_union([Polygon(p[0], p[1:]) for p in items])


def build(epoch_id, refresh_snapshot=False):
    config = load('data/maps/terrain-epochs.json')
    epoch = config['epochs'][epoch_id]
    if epoch['geometryEpoch'] != epoch_id:
        raise ValueError(f'Epoch {epoch_id} has no reviewed period geometry; refusing to backdate the 1900 scene')
    RESEARCH.mkdir(parents=True, exist_ok=True)
    pointer = RESEARCH/'observation-snapshot.json'
    if refresh_snapshot or not pointer.exists():
        raw = (ROOT/'reference/spot-heights/heights.geojson').read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        snapshot = RESEARCH/f'heights-{digest[:16]}.geojson'
        if not snapshot.exists():
            snapshot.write_bytes(raw)
        pointer.write_text(json.dumps({'file': snapshot.name, 'sha256': digest}, indent=2)+'\n')
    snapshot_info = json.loads(pointer.read_text())
    raw = (RESEARCH/snapshot_info['file']).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == snapshot_info['sha256']
    observations = [f['properties'] for f in json.loads(raw)['features']]
    controls = select_controls(observations, config, epoch_id)
    bounds = epoch['trialBounds']
    x0, z0, x1, z1 = bounds
    step = epoch['cellSizeMetres']
    assert step == 1
    x, z = np.arange(x0, x1+step, step), np.arange(z0, z1+step, step)
    X, Z = np.meshgrid(x, z)
    trial = box(*bounds)
    datum = config['verticalReference']
    controls_by_id = {p['id']: p for p in controls}
    target = np.zeros_like(X, dtype=float)
    support = np.zeros_like(X, dtype=float)
    source_zone = np.zeros_like(X, dtype=np.uint8)
    for zone_index, zone in enumerate(epoch['zones'], start=1):
        ps = [controls_by_id[key] for key in zone['controlIds']]
        distances = np.array([np.hypot(X-(p['bng_e']-538900), Z-(183209-p['bng_n'])) for p in ps])
        heights = np.array([(p['value_ft']+datum['liverpoolToNewlynFeet'])*.3048-datum['odnMinusSceneYMetres'] for p in ps])
        # Rounded source positions are not exact interpolation nodes. The 0.5 m
        # softening avoids singularities without fitting distant zones together.
        w = 1/np.maximum(distances, .5)**2
        fitted = (w*heights[:, None, None]).sum(axis=0)/w.sum(axis=0)
        radius = zone['maximumDistanceMetres']
        influence = 1-smooth(radius*.65, radius, distances.min(axis=0))
        # Separate compartments: enlarging the export rectangle must not carry
        # old controls across a river/railway into a newly added ground zone.
        zx0, zz0, zx1, zz1 = zone['supportBounds']
        zone_edge = np.minimum.reduce([X-zx0, zx1-X, Z-zz0, zz1-Z])
        influence *= smooth(0, zone['boundaryFeatherMetres'], zone_edge)
        stronger = influence > support
        target[stronger] = fitted[stronger]
        source_zone[stronger] = zone_index
        support = np.maximum(support, influence)

    plan = load('docs/data/ground-plan.json')
    infra = load('docs/data/infrastructure.json')
    factory = load('docs/data/factory-buildings.json')
    frontages = load('docs/data/high-street-frontages.json')
    station = load('docs/data/abbey-station-plan.json')
    network = load('docs/data/river-network.json')
    core = load('docs/data/river-terrain.json')
    water = from_rings([p for r in plan['rivers']+factory['westContext']['rivers'] for p in r['polygons']])
    passages=from_rings([p for r in network['reviewedConnections']['connections'] for p in r['polygons']])
    water=water.union(passages)
    sites = from_rings([p for s in plan['sites'] for p in s['polygons']])
    built = unary_union([Polygon(p['outer'], p['holes'])
                         for b in factory['buildings']+frontages['buildings'] for p in b['renderPolygons']]
                        + [Polygon(b['footprint']) for b in station['supportingBuildings']]
                        + [Polygon(station['worldFootprint'])]
                        + [Polygon(b['footprint']) for b in plan['neighbourhood']['houses']+plan['neighbourhood']['terraces']])
    holders = unary_union([Point(h['x'], h['z']).buffer(h['radius']+5) for h in plan['neighbourhood']['holders']+factory['holders']])
    roads = unary_union([LineString(r['route']).buffer(r['width']/2+3) for r in infra['roads']])
    rail = unary_union([LineString(r['route']).buffer(r.get('baseHalfWidth', 17)+4) for r in infra['railways']])
    sewer = LineString(plan['neighbourhood']['sewer']['route']).buffer(plan['neighbourhood']['sewer']['baseWidth']/2+4)
    drains = from_rings([p for f in network['marshDitches']['features'] for p in f['renderPolygons']]).buffer(4)
    # Protect bank crests and structures as well as water. Epoch-specific masks
    # are retained separately for future flood/earthwork review, never flattened.
    protections = {'river-and-bank': water.buffer(23), 'industrial-sites': sites,
                   'buildings': built.buffer(6), 'gas-holders': holders, 'roads': roads,
                   'railway': rail, 'sewer': sewer, 'drainage': drains}
    protected = unary_union(list(protections.values())).intersection(trial.buffer(20))
    clearance = distance(points(X, Z), protected)
    weight = support*smooth(2, epoch['protectionFeatherMetres'], clearance)
    # Preserve exact zeroes (also at the boundary) for unchanged geometry checks.
    weight[weight < 1e-7] = 0
    weight = weight.astype('<f4')
    target = target.astype('<f4')
    target, drainage, drainage_mask, drainage_line = apply_section(epoch_id,X,Z,target,weight)
    road=manor_evidence()
    if road['geometryEpoch']!=epoch_id:raise ValueError('Road needs its own period review')
    road_height,road_weight=road_profile(road,X,Z)
    road_area=road_domain(road)
    # A reviewed road cutting replaces only its own inherited road/rail-foot
    # protection. Rail decks, sewer, buildings and channels are not lowered.
    other_protected=unary_union([g for k,g in protections.items() if k not in {'roads','railway'}])
    assert not road_area.intersects(other_protected)
    combined=weight*(1-road_weight)+road_weight
    target=np.divide(target*weight*(1-road_weight)+(road_height-.065)*road_weight,
                     combined,out=target.astype(float),where=combined>0).astype('<f4')
    weight=combined.astype('<f4')
    protected=protected.difference(road_area)
    protections['roads']=protections['roads'].difference(road_area)
    protections['railway']=protections['railway'].difference(road_area)
    road_mask=road_weight>0

    # Reconstruct the original scene ground sampler on the same 1 m nodes.
    baseline = np.full(X.shape, -.1)
    positions = np.fromfile(PUBLIC/network['positionFile'], dtype='<f4').reshape(-1, 3)
    inside = (positions[:, 0]>=x0)&(positions[:, 0]<=x1)&(positions[:, 2]>=z0)&(positions[:, 2]<=z1)
    # T14 meshed the banks along the shoreline, adding off-grid vertices; only the 1 m grid vertices are interpolation nodes here.
    inside &= (positions[:, 0]==np.round(positions[:, 0])) & (positions[:, 2]==np.round(positions[:, 2]))
    local = positions[inside]
    baseline[(local[:, 2]-z0).astype(int), (local[:, 0]-x0).astype(int)] = local[:, 1]
    cx0, cz0, cx1, cz1 = core['bounds']
    core_levels = np.fromfile(PUBLIC/core['heightFile'], dtype='<f4').reshape(core['height'], core['width'])
    in_core = (X>=cx0)&(X<=cx1)&(Z>=cz0)&(Z<=cz1)
    baseline[in_core] = sample_grid(core_levels, core['bounds'], core['step'], X[in_core], Z[in_core])
    final = baseline+(target-baseline)*weight
    # Absolute supported-ground export: NaN means unsupported, protected or
    # transition, never zero elevation. This is NOT a complete flood solver DEM.
    odn = np.where(weight>=.999, final+datum['odnMinusSceneYMetres'], np.nan).astype('<f4')
    prefix = f'terrain-{epoch_id}'
    for suffix, values in [('target.f32', target), ('weight.f32', weight), ('scene.f32', final.astype('<f4')), ('odn.f32', odn)]:
        values.tofile(PUBLIC/f'{prefix}.{suffix}')
    source_zone.tofile(PUBLIC/f'{prefix}.zones.u8')
    drainage_mask.astype('u1').tofile(PUBLIC/f'{prefix}.drainage-mask.u8')
    road_mask.astype('u1').tofile(PUBLIC/f'{prefix}.road-mask.u8')

    # Replace the flat ground only, without drawing over river/core meshes.
    base_ground = from_rings(network['baseGround'])
    road_bounds=list(road_area.bounds)
    domains = unary_union([box(*zone['supportBounds']) for zone in epoch['zones']]+[box(*road_bounds)])
    extension = base_ground.intersection(domains)
    xx, zz = np.meshgrid(np.arange(x0, x1, 2), np.arange(z0, z1, 2))
    cells = shapely.box(xx.ravel(), zz.ravel(), xx.ravel()+2, zz.ravel()+2)
    # Resolve narrow channel banks without multiplying the whole landscape mesh.
    refine=(distance(points(xx.ravel()+1,zz.ravel()+1),drainage_line)<5) | (distance(points(xx.ravel()+1,zz.ravel()+1),road_area)<2)
    fine=[]
    for dx,dz in [(0,0),(1,0),(0,1),(1,1)]:
        ax,az=xx.ravel()[refine]+dx,zz.ravel()[refine]+dz
        fine.append(shapely.box(ax,az,ax+1,az+1))
    cells=np.concatenate([cells[~refine],*fine])
    pieces = shapely.intersection(cells, extension)
    faces = shapely.get_parts(shapely.constrained_delaunay_triangles(pieces))
    coords = shapely.get_coordinates(faces).reshape(-1, 4, 2)[:, :3]
    vertices = coords.reshape(-1, 2)
    ys = apply_grid(np.full(len(vertices), -.1), vertices[:, 0], vertices[:, 1], target, weight, bounds)
    mesh = np.column_stack([vertices[:, 0], ys, vertices[:, 1]]).reshape(-1, 3, 3)
    # Three.js x/z up-facing winding.
    cross = np.cross(mesh[:, 1]-mesh[:, 0], mesh[:, 2]-mesh[:, 0])[:, 1]
    mesh[cross<0] = mesh[cross<0, ::-1]
    mesh.astype('<f4').tofile(PUBLIC/f'{prefix}.extension.f32')
    water_triangles(mesh,drainage)
    (PUBLIC/f'drainage-{epoch_id}.json').write_text(json.dumps(drainage,separators=(',',':'))+'\n')

    # Audit all nearby readings, including excluded/earlier ones, without losing
    # their original notes or recombining observations at a shared location.
    nearby = [p for p in observations if x0-100 <= p['bng_e']-538900 <= x1+100 and z0-100 <= 183209-p['bng_n'] <= z1+100]
    catalogue = {'schemaVersion': 1, 'snapshot': snapshot_info,
                 'dateProfiles': config['observationSources'], 'observations': nearby,
                 'crossEpochMerge': False}
    (RESEARCH/f'{epoch_id}-observations.json').write_text(json.dumps(catalogue, indent=2)+'\n')
    provenance = []
    for p in controls:
        px, pz = p['bng_e']-538900, 183209-p['bng_n']
        protected_by = [name for name, geom in protections.items()
                        if geom.distance(Point(px, pz)) < epoch['protectionFeatherMetres']]
        provenance.append({'id': p['id'], 'position': [px, pz], 'valueFeet': p['value_ft'],
                           'heightODNMetres': round((p['value_ft']+datum['liverpoolToNewlynFeet'])*.3048, 6),
                           'layer': p['layer'], 'surveyYears': config['observationSources'][p['layer']]['surveyYears'],
                           'setting': p['setting'], 'notes': p['notes'],
                           'appliedWeightAtObservation': float(sample_grid(weight, bounds, step, px, pz)),
                           'nearbyProtectionCategories': protected_by,
                           'surfaceReview': epoch['surfaceReviews'].get(p['id']),
                           'sourceSettingConflict': bool(p.get('setting_conflict')),
                           'surfaceConflictResolution': epoch.get('surfaceConflictResolutions', {}).get(p['id']),
                           'conflictReview': epoch.get('protectionConflictReviews', {}).get(p['id']),
                           'appliedHeightODNMetres': float(sample_grid(final, bounds, step, px, pz)+datum['odnMinusSceneYMetres'])})
    inputs = ['data/maps/terrain-epochs.json', 'data/maps/historic-flood-events.json', 'docs/data/ground-plan.json', 'docs/data/infrastructure.json',
              'docs/data/factory-buildings.json', 'docs/data/high-street-frontages.json', 'docs/data/abbey-station-plan.json',
              'docs/data/river-network.json', 'docs/data/river-network.f32', 'docs/data/river-terrain.json', 'docs/data/river-terrain.f32']
    meta = {'schemaVersion': 1, 'epoch': epoch_id, 'targetYear': epoch['targetYear'], 'geometryEpoch': epoch['geometryEpoch'],
            'bounds': bounds, 'step': step, 'width': len(x), 'height': len(z),
            'drainageFile': f'drainage-{epoch_id}.json',
            'drainageNote': 'Open-channel bed and standing water are assumed sections; marked separately from interpolated field ground. Faded ends are model boundaries, not barriers.',
            'verticalReference': datum, 'continuityAssumption': epoch['continuityAssumption'],
            'files': {k: f'{prefix}.{v}' for k, v in {'target': 'target.f32', 'weight': 'weight.f32', 'scene': 'scene.f32',
                       'odn': 'odn.f32', 'zones': 'zones.u8', 'extension': 'extension.f32', 'drainageMask': 'drainage-mask.u8', 'roadMask':'road-mask.u8'}.items()},
            'replacementBaseGround': rings(base_ground.difference(domains)), 'extensionVertices': int(mesh.size//3),
            'interpolationDomains': [{'id': zone['id'], 'bounds': zone['supportBounds'],
                                      'boundaryFeatherMetres': zone['boundaryFeatherMetres']} for zone in epoch['zones']]+[{'id':'manor-road-profile','bounds':road_bounds,'boundaryFeatherMetres':road['groundFeatherMetres']}],
            'roadProfiles':[road],
            'reviewedRiverConnections':network['reviewedConnections'],
            'controls': provenance, 'observationSnapshotSHA256': snapshot_info['sha256'],
            'inputHashes': {**{p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in inputs},**drainage['inputHashes'],**road['inputHashes']},
            'groundUncertaintyMetres': epoch['groundUncertaintyMetres'],
            'datumUncertaintyMetres': datum['estimatedUncertaintyMetres'],
            'supportedAreaM2': int(np.sum(weight>=.999)), 'affectedAreaM2': int(np.sum(weight>0)),
            'changeRangeMetres': [float(np.min(final-baseline)), float(np.max(final-baseline))],
            'supportLegend': {'weight=0': 'unchanged earlier scaffold or protected feature', '0<weight<1': 'transition; not flood-analysis support', 'weight=1': 'interpolated historical ground, road subgrade or assumed drainage section; not a measured cell', 'drainageMask=1': 'assumed channel section replaces field-ground interpolation', 'roadMask=1':'Road earthwork; ground is 0.065 m below paving, separately profiled from map road-surface spots'},
            'zoneIds': {str(i): zone['id'] for i, zone in enumerate(epoch['zones'], start=1)},
            'floodReady': False, 'floodScenarios': config['floodScenarios'],
            'floodLimitations': ['Protected barrier/structure heights remain inherited interpretations', 'Event dates recorded; site-specific water boundary levels, drainage connectivity and documented failures still unresolved', 'ODN raster includes supported ground and road subgrade; compose roadProfiles surface heights before hydraulic use; NaN elsewhere', 'Existing tide animation remains illustrative and is not a flood simulation'],
            'temporalPolicy': config['temporalPolicy']}
    (PUBLIC/f'{prefix}.json').write_text(json.dumps(meta, separators=(',', ':'))+'\n')
    (PUBLIC/'terrain-epochs.json').write_text(json.dumps({'schemaVersion': 1, 'activeEpoch': config['activeEpoch'],
            'epochs': {key: {'targetYear': val['targetYear'], 'status': val['status'],
                            'asset': f'terrain-{key}.json' if key == epoch_id else None} for key, val in config['epochs'].items()}}, indent=2)+'\n')
    (RESEARCH/f'{epoch_id}-protection.geojson').write_text(json.dumps({'type': 'FeatureCollection',
            'features': [{'type': 'Feature', 'properties': {'category': key, 'geometryEpoch': epoch_id,
                          'datesOfConstruction': None, 'heightStatus': 'inherited interpretation; not flood validated'},
                          'geometry': mapping(geom.intersection(trial))} for key, geom in protections.items()]})+'\n')
    np.savez_compressed(RESEARCH/f'{epoch_id}-audit.npz', baseline=baseline, final=final, weight=weight,
                        target=target, drainage=drainage_mask, road=road_mask, protected=contains_xy(protected, X, Z), bounds=bounds)
    assert np.isfinite(final).all()
    assert np.all(weight[contains_xy(protected, X, Z)] == 0)
    assert np.array_equal(final[weight==0], baseline[weight==0])
    print(json.dumps({k: meta[k] for k in ['epoch', 'supportedAreaM2', 'affectedAreaM2', 'changeRangeMetres', 'extensionVertices', 'controls']}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--epoch', default='1900')
    parser.add_argument('--refresh-observations', action='store_true', help='Capture a new immutable snapshot of the live collection')
    args = parser.parse_args()
    build(args.epoch, args.refresh_observations)
