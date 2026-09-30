"""Extend bank relief along the existing GIS waterways, outside the detailed core.

Plan geometry stays with the supplied Lower_River_Lea layer. Sections are modelling
estimates, not a DEM or a traced low-water survey. No modern waterways are added.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter
from shapely import contains_xy, segmentize
from shapely.geometry import Polygon, LineString, box
from shapely.ops import unary_union
from marsh_ditches import geometry as ditch_geometry, apply_sections

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/data'


def polygons(geometry):
    return [g for g in getattr(geometry, 'geoms', [geometry])
            if g.geom_type == 'Polygon' and not g.is_empty]


def rings(geometry):
    return [[list(r.coords) for r in [p.exterior, *p.interiors]] for p in polygons(geometry)]


def smooth(a, b, values):
    t = np.clip((values-a)/(b-a), 0, 1)
    return t*t*(3-2*t)


def build():
    plan = json.loads((OUT/'ground-plan.json').read_text())
    # Factory coverage extends beyond the old western clip to the Old Lea.
    west = ROOT/'data/maps/factory-west-context.json'
    if west.exists():
        plan['rivers'].extend(json.loads(west.read_text())['rivers'])
    core = json.loads((OUT/'river-terrain.json').read_text())
    infrastructure = json.loads((OUT/'infrastructure.json').read_text())
    channels = {r['id']: unary_union([Polygon(p[0], p[1:]) for p in r['polygons']])
                for r in plan['rivers']}
    river = unary_union(list(channels.values()))
    # Author's hydrological distinction: the Old Lea/navigation above the
    # Limehouse Cut lock retains water; the other scene channels share the tide.
    retained_ids = {18, 22, 10018, 10022}
    tidal = unary_union([g for key,g in channels.items() if key not in retained_ids])
    patch = box(*core['bounds'])
    # Sample only a narrow corridor at runtime; the generation grid is temporary.
    minx, minz, maxx, maxz = np.array(river.bounds).astype(int) + [-18, -18, 18, 18]
    x, z = np.arange(minx, maxx+1), np.arange(minz, maxz+1)
    X, Z = np.meshgrid(x, z)
    water = contains_xy(river, X, Z)
    outside = distance_transform_edt(~water)
    _, nearest = distance_transform_edt(~water, return_indices=True)
    tidal_cells = contains_xy(tidal, X, Z)
    tidal_bank = tidal_cells[nearest[0],nearest[1]]
    inside = distance_transform_edt(water)
    shore = gaussian_filter(outside-inside, .65)
    # Generic low bank sections elsewhere; the broader grassy east bank on Wall
    # River is informed by the author's c1900 photograph, not the 1948 aerial.
    # The author dates the later engineered embankments to the 1930s.
    wall = channels[1]
    east = []
    for zz in z:
        cut = wall.intersection(LineString([(minx, zz), (maxx, zz)]))
        east.append(cut.bounds[2] if not cut.is_empty else np.nan)
    east = np.array(east)[:, None]
    wall_east = np.nan_to_num((X-east >= 0) & (X-east < 16)).astype(float)
    wall_east *= smooth(-210, -175, Z)*(1-smooth(300, 355, Z))
    variation = .93 + .07*np.sin(Z*.041)*np.sin(X*.029)
    crest = (1.65 + .10*wall_east)*variation
    width = 7 + 7*wall_east
    height = -.1 + (crest+.1)*smooth(0, 3, shore)*(1-smooth(4, width, shore))
    height = np.where(water, .06-.25-.17*np.minimum(inside, 9), height)
    # Existing site envelopes and road corridors keep their ground datum. These
    # are industrial plots, not evidence for continuous walls along every plot.
    east_context=json.loads((ROOT/'data/maps/east-channelsea-context-alignment.json').read_text())
    sites = unary_union([Polygon(p[0], p[1:]) for s in plan['sites']+east_context['additionalYards'] for p in s['polygons']])
    roads = unary_union([LineString(r['route']).buffer(r['width']/2+2)
                         for r in infrastructure['roads']])
    built = contains_xy(sites.union(roads), X, Z)
    clearance = smooth(0, 3, distance_transform_edt(~built))
    height = np.where(water, height, -.1+(height+.1)*clearance)
    # Match Channelsea's exposed shelves at its existing water datum. The GIS
    # remains the low-water route anchor, not a claimed high-water survey.
    sediment = tidal_bank * (1-smooth(4.5,7.5,outside)) * clearance
    shelf = .06 + 1.59*smooth(0,5,shore)
    height = np.where(~water, height*(1-sediment)+shelf*sediment, height)
    # Local photograph study: a worn path on a raised grassy east bank, with
    # timber details rendered separately. Metric section remains an estimate.
    vista_path=ROOT/'data/maps/wall-river-vista.json'
    support=np.zeros_like(height)
    if vista_path.exists():
        vista=json.loads(vista_path.read_text());bank=vista['bank']
        offset=X-east
        profile=np.interp(np.nan_to_num(offset,nan=-100),
                          [0,1,4.8,8.5,15,20],[.08,.65,bank['crestHeight'],bank['crestHeight'],bank['crestHeight'],-.1])
        blend=smooth(bank['zStart']-10,bank['zStart'],Z)*(1-smooth(bank['zEnd'],bank['zEnd']+10,Z))
        active_bank=(offset>=0)&(offset<=20)&(~water)
        height=np.where(active_bank,height*(1-blend)+profile*blend,height)
        # Photograph path and mapped continuation must meet without a floating
        # ribbon or a vertical end. Feather earth into the surrounding bank.
        generated=json.loads((OUT/'high-street-frontages.json').read_text())['vista']
        for connection in generated['connections']:
            route=connection['route'];radius=connection['width']/2
            for a,b in zip(route,route[1:]):
                dx,dz=b[0]-a[0],b[2]-a[2]
                t=np.clip(((X-a[0])*dx+(Z-a[2])*dz)/(dx*dx+dz*dz),0,1)
                distance=np.hypot(X-a[0]-t*dx,Z-a[2]-t*dz)
                weight=(1-smooth(radius+.2,radius+4,distance))*(~water)
                target=a[1]+t*(b[1]-a[1])
                height=height*(1-weight)+target*weight
                support=np.maximum(support,weight)
        # Grass above the muddy bank face, including the raised photo section.
        sediment*=1-smooth(1.25,1.95,height)
    # The old patch tapers to -.1 at its boundary. Match that seam precisely.
    x0, z0, x1, z1 = core['bounds']
    dx, dz = np.maximum(np.maximum(x0-X, X-x1), 0), np.maximum(np.maximum(z0-Z, Z-z1), 0)
    core_distance = np.hypot(dx, dz)
    height = -.1+(height+.1)*smooth(0, 3, core_distance)
    # A tiny offset prevents coplanar flicker where the outer apron meets the
    # surrounding ground; the detailed core itself remains untouched.
    height += .004*smooth(0, 1, core_distance)
    height,ditch_mud,marsh_active=apply_sections(X,Z,height)
    sediment=np.maximum(sediment*(1-smooth(1.1,1.65,height)),ditch_mud)
    ditch_raw,marsh,ditches,ditch_parts,_=ditch_geometry()
    # At working plots the bank cannot occupy a wide grass slope. A narrow
    # retaining edge holds the same interpreted crest; material/design unresolved.
    retaining=river.boundary.intersection(tidal.buffer(.01)).intersection(sites.buffer(3)).difference(roads)
    wall_routes=[list(segmentize(g,4).coords) for g in getattr(retaining,'geoms',[retaining]) if g.geom_type=='LineString' and g.length>1]
    # Keep complete 1 m cells, excluding the core at its integer boundaries.
    active = ((outside < 21) | (support>0) | marsh_active) & (core_distance > 0)
    cells = active[:-1, :-1] | active[1:, :-1] | active[:-1, 1:] | active[1:, 1:]
    cx, cz = X[:-1, :-1]+.5, Z[:-1, :-1]+.5
    cells &= ~((cx > x0) & (cx < x1) & (cz > z0) & (cz < z1))
    a = (np.arange(X.size).reshape(X.shape)[:-1, :-1])[cells]
    triangles = np.stack([a, a+len(x), a+1, a+1, a+len(x), a+len(x)+1], axis=1).reshape(-1, 3)
    used, inverse = np.unique(triangles, return_inverse=True)
    positions = np.stack([X.ravel()[used], height.ravel()[used], Z.ravel()[used]], axis=1).astype('<f4')
    indices = inverse.astype('<u4')
    # Vertex colour distinguishes submerged/silty edges from the grassy crest.
    grass = np.array([1., 1., 1.])
    silt = np.array([.70, .65, .54])
    green = smooth(.2, 2.8, outside.ravel()[used])[:, None]
    colors = np.clip((silt*(1-green)+grass*green)*255, 0, 255).astype('uint8')
    positions.tofile(OUT/'river-network.f32')
    indices.tofile(OUT/'river-network.u32')
    colors.tofile(OUT/'river-network.rgb')
    (np.clip(sediment.ravel()[used],0,1)*255).astype('uint8').tofile(OUT/'river-network.silt')
    landcover=np.column_stack([contains_xy(sites,positions[:,0],positions[:,2]),
        contains_xy(Polygon(plan['neighbourhood']['garden']['footprint']),positions[:,0],positions[:,2])])
    (landcover.astype('uint8')*255).tofile(OUT/'river-network.cover')
    # Remove the flat floor below channels as well as the existing terrain patch.
    ground = box(-2750, -2750, 2750, 2750).difference(river.buffer(14).union(patch).union(marsh))
    # Confine the animated surface to river-side shelves. A whole-scene plane
    # would flood the lower marsh through the back of its embankments.
    core_beds = unary_union([Polygon(p[0], p[1:]) for p in plan['bankStudies']])
    retained = unary_union([g for key,g in channels.items() if key in retained_ids])
    tide_envelope = tidal.buffer(5).union(core_beds.intersection(patch))
    tide_envelope = tide_envelope.difference(sites.union(roads).difference(tidal))
    tide_envelope = tide_envelope.difference(marsh.union(ditches).union(retained))
    meta = {
        'positionFile': 'river-network.f32', 'indexFile': 'river-network.u32', 'colorFile': 'river-network.rgb',
        'sedimentFile': 'river-network.silt',
        'landcoverFile': 'river-network.cover',
        'waterLevel':core['waterLevel'],
        'tide':{'low':core['waterLevel'], 'high':ditch_raw['levels']['illustrativeHighWater'],
                'cycleSeconds':90, 'polygons':rings(tide_envelope),
                'evidence':'Illustrative synchronised rise and fall within interpreted river-side shelves. Not a tide prediction or hydraulic simulation; excludes retained Old Lea and marsh drains.'},
        'retainingEdges':{'routes':wall_routes,'crestHeight':1.65,'baseHeight':-.55,'width':.32,
                          'evidence':'Interpretive flood-retaining edges where tidal river banks meet GIS industrial plots. Presence, material and individual sections require photograph/engineering-plan verification. Not the 1930s concrete embankments.'},
        'marshDitches':{'features':[{**f,'renderPolygons':rings(g),'retainedAreaM2':round(g.area,2)} for f,g in zip(ditch_raw['features'],ditch_parts)],
                        'waterPolygons':rings(ditches.difference(patch)), 'marshPolygons':rings(marsh),
                        'levels':ditch_raw['levels'],'policy':ditch_raw['policy']},
        'retainedWaterChannelIds':sorted(retained_ids),
        'tidalChannelIds':sorted(set(channels)-retained_ids),
        'tidalEvidence':'Author correction: tidal margins throughout except Old Lea north of the Limehouse Cut lock. GIS ids 18,22,10018,10022 identify that retained reach; Bow Creek id 0 remains tidal. Widths and sections inferred, not reconstructed tidal hydraulics.',
        'vertices': len(used), 'triangles': len(triangles), 'step': 1, 'baseGround': rings(ground),
        'channels': [{'id': r['id'], 'name': 'Three Mills Wall River' if r['id'] == 1 else r['name'],
                      'sourceName': r['name']} for r in plan['rivers']],
        'source': 'data/maps/panorama-source-context.geojson; supplied Lower_River_Lea.geojson and Industry_1893-95.geojson',
        'planSha256': hashlib.sha256((OUT/'ground-plan.json').read_bytes()).hexdigest(),
        'evidence': 'Author identifies Wall River west of Mill Mead and marsh below rivers at high tide. Wall River photo supplies the local raised bank/path section; data/maps/marsh-ditches.json supplies map-traced drains. Heights, widths, bed depths and retaining-edge sections remain inferred, not a surveyed wall inventory.',
        'chronology': 'The author dates later engineered embankments to the 1930s. EAW014561 (16 April 1948) is comparison evidence only; its embankments, channel alterations and factory forms are not backdated into this scene. Prescott Cut remains excluded.',
        'limitations': ['Generic bank sections are a terrain scaffold, not a surveyed reconstruction.',
                       'City Mills masonry banks, openings and crossings visible in the circa 1897 photograph still require registered plan tracing.',
                       'Source GIS industry polygons are site parcels, not individual building footprints.'],
        'heightRange': [float(positions[:, 1].min()), float(positions[:, 1].max())],
    }
    assert np.isfinite(positions).all()
    assert not np.any((positions[:, 0] > x0) & (positions[:, 0] < x1) &
                      (positions[:, 2] > z0) & (positions[:, 2] < z1))
    assert np.max(indices) < len(used)
    assert ground.intersection(river).area < .001
    assert np.all(height[water & (core_distance > 3)] < .06)
    (OUT/'river-network.json').write_text(json.dumps(meta, separators=(',', ':'))+'\n')
    print(f'River network: {len(channels)} source features, {len(used):,} vertices, {len(triangles):,} triangles; core and waterways clear.')


if __name__ == '__main__':
    build()
