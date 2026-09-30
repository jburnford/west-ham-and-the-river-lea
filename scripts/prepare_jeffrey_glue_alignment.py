"""Author explicit Jeffrey glue-works OS/Goad F3 matches and mapped bases."""
import json
import math
from pathlib import Path

from shapely import affinity, set_precision
from shapely.geometry import Point, Polygon, box, shape
from shapely.ops import unary_union

from factory_alignment_records import record_group
from prepare_ink_works_alignment import axis, rings
from prepare_three_mills_north_alignment import polygon

ROOT = Path(__file__).resolve().parents[1]
SPECS = [
    ('jeffrey-north-workshop', [388162], ['site790-882']),
    ('jeffrey-west-coppers', [43437, 749900], ['site790-886', 'site790-886s']),
    ('jeffrey-central-process', [12708], ['site790-888', 'site790-890', 'site790-890s', 'site790-892']),
    ('jeffrey-east-coppers', [134571], ['site790-896']),
    ('jeffrey-east-south', [138986], ['site790-898']),
    ('jeffrey-east-north', [792210], ['site790-900']),
    ('jeffrey-east-end', [214661], ['site790-902']),
]
REVIEWS = {
    'jeffrey-north-workshop': 'Separate northern one-floor Goad room 882, with the OS bevelled western end retained; the yard between this range and the mechanics shop stays open.',
    'jeffrey-west-coppers': 'Goad room 886 has two-floor steam-jacketed coppers above a one-floor covered southern compartment and an attached western stair. The complete OS coppers body and stair are retained. The transverse division follows inherited 43:32 compartment depths; the stair remains with the northern higher range. Its exact internal roof boundary is interpreted.',
    'jeffrey-central-process': 'The continuous OS exterior contains Goad western room 888, middle covered coppers and southern process compartment 890, and eastern warehouse 892/894. Longitudinal divisions follow inherited 39:67:49 compartment widths; the middle transverse cut follows 48:33 depths. All compartment elevations and roof parameters are retained; internal roof boundaries remain interpreted.',
    'jeffrey-east-coppers': 'Complete separate two-floor concrete-ceiling steam-coppers body 896. The mapped western 50-foot chimney and additional eastern chimney symbol lie outside this source body.',
    'jeffrey-east-south': 'Separate southern one-floor Goad room 898, retaining the small north-edge recess around the independently mapped western chimney and the eastern source boundary.',
    'jeffrey-east-north': 'Separate one-floor northern end room 900; the small coal-yard symbol north of this range is retained as unmodelled context.',
    'jeffrey-east-end': 'Complete one-floor eastern end room 902, keeping its distinct boundary against southern room 898 and northern room 900.',
}


def render_change(models, corrections, ident, neighbor_ids, evidence):
    """Predict one unchanged range's overlap partition from reviewed neighbours.

    The renderer rounds the result after subtracting higher-priority ranges.
    All inputs are immutable baseline geometry and saved reviewed outlines;
    published render geometry is never an authoring input.
    """
    old = models[ident]
    original = Polygon(old['worldFootprint'], old.get('worldHoles', []))
    prior = unary_union([Polygon(p['outer'], p['holes']) for p in old['renderPolygons']])
    neighbors = [Polygon(corrections[n]['worldFootprint'], corrections[n]['worldHoles'])
                 for n in neighbor_ids]
    priority = (-old['height'], original.area, ident)
    assert all((-models[n]['height'], p.area, n) < priority
               for n, p in zip(neighbor_ids, neighbors))
    predicted = polygon(set_precision(original.difference(unary_union(neighbors)), .001))
    # Saved render rings are ordinary floating-point geometries. Drop the
    # transient GEOS precision model before calculating their exact deltas.
    predicted = Polygon(predicted.exterior.coords, [r.coords for r in predicted.interiors])
    gained, lost = predicted.difference(prior), prior.difference(predicted)
    delta = gained.union(lost)
    context = unary_union(neighbors + [Polygon(models[n]['footprint'],
                         models[n].get('worldHoles', [])) for n in neighbor_ids])
    rounding = delta.difference(context.buffer(.0015))
    assert rounding.difference(original.boundary.buffer(.0015)).area < .000001
    return dict(modelId=ident, baseline='reference/footprint-model-alignment/marshgate-trades-before.json',
        neighborModelIds=neighbor_ids,
        priorRenderPolygons=old['renderPolygons'],
        expectedRenderPolygons=[dict(outer=rings(predicted)[0], holes=rings(predicted)[1:])],
        preservedFootprint=old['footprint'], preservedWorldHoles=old.get('worldHoles', []),
        preservedProfile={key: old[key] for key in ['height', 'roofRise', 'roofAxis', 'roofBays', 'rotation']},
        addedAreaM2=gained.area, removedAreaM2=lost.area,
        maximumAddedAreaM2=gained.area+.000001, maximumRemovedAreaM2=lost.area+.000001,
        changeBounds=list(delta.bounds), precisionGridMetres=.001,
        roundingBoundaryBufferMetres=.0015, maximumRoundingAreaM2=rounding.area+.000001,
        evidence=evidence+' Expected rendering is derived from the immutable authored exterior minus the declared higher-priority reviewed neighbours, then rounded to the renderer\'s 1 mm grid. Tiny additional edge slivers are bounded rounding changes on the unchanged exterior; no footprint or elevation correction is authorized.')


def validate_render_changes(records, before, scene, corrections, preflight=False):
    """Validate exact predicted rendering and bounded neighbour/rounding deltas."""
    old_models = {b['id']: b for b in before['buildings']}
    actual_models = {b['id']: b for b in scene['buildings']}
    for c in records:
        ident = c['modelId']
        old, actual = old_models[ident], actual_models[ident]
        assert c['baseline'] == 'reference/footprint-model-alignment/marshgate-trades-before.json'
        assert c['priorRenderPolygons'] == old['renderPolygons']
        assert c['preservedFootprint'] == old['footprint'] == actual['footprint']
        assert c['preservedWorldHoles'] == old.get('worldHoles', []) == actual.get('worldHoles', [])
        for key, value in c['preservedProfile'].items():
            assert old[key] == actual[key] == value, (ident, key)
        body = Polygon(c['preservedFootprint'], c['preservedWorldHoles'])
        prior = unary_union([Polygon(p['outer'], p['holes']) for p in c['priorRenderPolygons']])
        predicted = unary_union([Polygon(p['outer'], p['holes']) for p in c['expectedRenderPolygons']])
        gained, lost = predicted.difference(prior), prior.difference(predicted)
        assert abs(gained.area-c['addedAreaM2']) < .0000001
        assert abs(lost.area-c['removedAreaM2']) < .0000001
        assert gained.area <= c['maximumAddedAreaM2'] < gained.area+.000002
        assert lost.area <= c['maximumRemovedAreaM2'] < lost.area+.000002
        assert predicted.difference(body.buffer(.0015)).area < .000001
        delta = gained.union(lost)
        assert all(abs(a-b) < .0000001 for a, b in zip(delta.bounds, c['changeBounds']))
        context = unary_union([Polygon(old_models[n]['footprint'], old_models[n].get('worldHoles', []))
            for n in c['neighborModelIds']] + [Polygon(corrections[n]['worldFootprint'],
                corrections[n]['worldHoles']) for n in c['neighborModelIds']])
        assert c['precisionGridMetres'] == .001 and c['roundingBoundaryBufferMetres'] == .0015
        rounding = delta.difference(context.buffer(.0015))
        assert rounding.area <= c['maximumRoundingAreaM2'] < rounding.area+.000002
        assert rounding.difference(body.boundary.buffer(.0015)).area < .000001
        if not preflight:
            rendered = unary_union([Polygon(p['outer'], p['holes']) for p in actual['renderPolygons']])
            assert rendered.symmetric_difference(predicted).area < .0000001, ident


def build():
    load = lambda p: json.loads((ROOT / p).read_text())
    before = load('reference/footprint-model-alignment/marshgate-trades-before.json')
    models = {b['id']: b for b in before['buildings']}
    cached = load('reference/footprint-model-alignment/marshgate-trades-source-shapes.json')
    wanted = {f for _, fs, _ in SPECS for f in fs} | {1154281, 1194922}
    source = {f: polygon(shape(cached[str(f)])) for f in wanted}
    groups, buildings = [], []
    for gid, fids, ids in SPECS:
        target = polygon(set_precision(unary_union([source[f] for f in fids]), .001))
        angle = axis(target, models[ids[0]]['rotation'])
        parts, division = [target], None
        if gid == 'jeffrey-west-coppers':
            local = affinity.rotate(source[43437], -angle, origin=(0, 0))
            _, low, _, high = local.bounds
            cut = low + (high-low)*43/75
            north_mask = affinity.rotate(box(-10000, -10000, 10000, cut), angle, origin=(0, 0))
            north = polygon(set_precision(unary_union([source[43437].intersection(north_mask), source[749900]]), .001))
            south = polygon(target.difference(north))
            parts = [north, south]
            division = dict(frameAngleDegrees=angle, localZCut=cut,
                northernMainDepthFraction=43/75, attachedStairSourceFid=749900,
                evidence='Goad upper two-floor coppers/lower one-floor covered compartment; inherited 43:32 depths, interpreted exact roof cut.')
        if gid == 'jeffrey-central-process':
            local = affinity.rotate(target, -angle, origin=(0, 0))
            low_x, low_z, high_x, high_z = local.bounds
            cuts = [low_x+(high_x-low_x)*39/155, low_x+(high_x-low_x)*106/155]
            cut_z = low_z+(high_z-low_z)*48/81
            def part(x0, z0, x1, z1):
                mask = affinity.rotate(box(x0, z0, x1, z1), angle, origin=(0, 0))
                return polygon(set_precision(target.intersection(mask), .001))
            parts = [part(-10000, -10000, cuts[0], 10000),
                     part(cuts[0], -10000, cuts[1], cut_z),
                     part(cuts[0], cut_z, cuts[1], 10000),
                     part(cuts[1], -10000, 10000, 10000)]
            division = dict(frameAngleDegrees=angle, localXCuts=cuts, localZCut=cut_z,
                longitudinalWidths=[39, 67, 49], middleDepths=[48, 33],
                evidence='Explicit Goad 888 / covered-coppers 890 / warehouse 892 compartment order; inherited traced proportions, interpreted exact roof cuts.')
        group, rows = record_group(gid, fids, source, models, ids,
            [models[i]['name'] for i in ids], target, parts, angle, REVIEWS[gid],
            review_prefix='Explicit cached OS five-foot and original July 1893 Goad F3 comparison; prior heights and roof parameters retained. ')
        if division:
            group['divisionParameters'] = division
        groups.append(group)
        buildings.extend(rows)

    structures = []
    for ident, fid, note in [
        ('stack-790-1522-1330', 1154281, 'Western chimney at the southern foot of the coppers stair, beside Goad 886. The separate adjacent OS symbol 1062461 remains unclassified stair-foot/apron context; it is not absorbed into this base.'),
        ('stack-790-1823-1258', 1194922, 'Western of the two eastern coppers chimneys, carrying the printed Goad 50-foot annotation at the junction of rooms 896 and 898. The separate eastern symbol 1148002 has no existing shaft counterpart and is deferred.'),
    ]:
        old = next(s for s in before['structures'] if s['id'] == ident)
        base = source[fid]
        centre = Point(round(base.centroid.x, 3), round(base.centroid.y, 3))
        angle = axis(base, old['rotation'])
        lo, hi = 0., old['radius']
        for _ in range(50):
            radius = (lo+hi)/2
            plinth = affinity.rotate(box(centre.x-radius*1.2, centre.y-radius*1.2,
                centre.x+radius*1.2, centre.y+radius*1.2), angle, origin=centre)
            if base.covers(plinth): lo = radius
            else: hi = radius
        radius = math.floor(lo*1000)/1000
        structures.append(dict(id=ident, sourceFid=fid, sourcePolygons=[rings(base)],
            centre=[centre.x, centre.y], rotation=angle, radius=radius,
            priorRadius=old['radius'], priorCentre=[old['x'], old['z']],
            preservedHeight=old['height'],
            profileEvidence='Interpreted square shaft radius reduced to fit its complete rotated 1.2-times-radius square plinth inside the independent OS symbol at the rounded mapped centroid. Symbol dimensions locate the base without asserting a measured shaft diameter. Existing shaft section and height retained.',
            review=note+' Matched by original Goad chimney/room context and OS symbols; no nearest-building assignment.'))
    result = dict(source='Author-supplied london_buildings_1891-96_corr_v1.gpkg; cached OS London five-foot mosaic',
        sourceCRS='EPSG:3857 reprojected through BNG; scene origin E538900,N183209',
        method='Explicit Jeffrey glue-works complete OS exteriors reviewed against original Goad F3; inherited compartment proportions divide two compound bodies, two independently mapped square chimney bases, all previous elevations and roofs retained.',
        groups=groups, buildings=buildings, structures=structures,
        renderChanges=[render_change(models, {b['modelId']: b for b in buildings},
            'site790-884', ['site790-886'],
            'The retained source-linked mechanics shop 884 is unchanged. The reviewed taller coppers body 886 overlaps a 0.0260355 m² strip of its eastern corner; the established taller-range rendering priority removes this strip while retaining both mapped source exteriors.')],
        retainedExistingMatches=[dict(modelId='site790-884', sourceFid=77857), dict(modelId='site790-raw', sourceFid=49851)],
        mapReview=['Cached georeferenced OS London five-foot mosaic inspected raw, with source boundaries and with prior model overlays.',
            'Original July 1893 Goad volume F sheet 3 inspected raw and with source overlay through goad-f3-marsh registration; room 882, 886, 888, 890, 892/894, 896, 898, 900 and 902 identities reviewed.'],
        evidenceImages=[f'reference/footprint-model-alignment/jeffrey-glue-{suffix}.png' for suffix in
            ['raw', 'source', 'models', 'goad', 'goad-source', 'goad-west', 'goad-east', 'after-models']],
        deferred=[
            dict(sourceFids=[1062461], reason='Small adjacent western stair-foot/apron symbol outside the coppers body and independently mapped chimney 1154281; exact classification unresolved, no unsupported building addition.'),
            dict(sourceFids=[1148002], reason='Second eastern coppers chimney visible on Goad, independently mapped on OS. No existing shaft counterpart; no new shaft or elevation asserted.'),
            dict(sourceFids=[930555], reason='Northern coal-yard ancillary symbol above room 900 remains source context; no existing range counterpart.'),
            dict(sourceFids=[1081689, 1135005], reason='Tiny attached symbols at the western/southern edge of the central body remain outside its supplied exterior; exact ancillary classification unresolved.'),
            dict(feature='Western chimney height', reason='No legible printed shaft height established. The inherited 22 m estimate remains interpreted; map matching changes the base position/profile only.'),
        ])
    (ROOT / 'data/maps/jeffrey-glue-footprint-alignment.json').write_text(json.dumps(result, indent=2)+'\n')
    print('Jeffrey glue: eleven retained ranges in seven groups; two independently mapped square chimney plinths.')


if __name__ == '__main__':
    build()
