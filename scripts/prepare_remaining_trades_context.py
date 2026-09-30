"""Replay independently reviewed OS street controls beside the remaining trades."""
import copy
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

from factory_map_sources import mosaic
from factory_street_clearance import street_clearances

ROOT = Path(__file__).resolve().parents[1]
REGISTER = 'data/maps/remaining-trades-context-alignment.json'
BASELINE = 'reference/footprint-model-alignment/remaining-trades-roads-before.json'
load = lambda p: json.loads((ROOT/p).read_text())
digest = lambda data: hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
CROWN_BOUNDS = [-960, -235, -785, -40]
CROWN_PIXELS = [[570,625],[537,581],[515,545],[503,513],[496,478],
                [491,435],[470,400],[442,370],[410,335]]
WESTERN_BOUNDS = [-750,365,-635,440]
WESTERN_PIXELS = [[340,374],[459,366]]
REVIEW = ('Re-read the complete unmodified OS mosaic. The southern Marshgate arm previously '
          'ran through Crown/Johnson instead of the public street east of its walls. Follow '
          'that street and keep the last two mill approach controls and the separate northern '
          'arm. At the ornamental moulding shed, Three Mills Lane follows the middle of the '
          'mapped street a little south of the former western bridge approach. Retain both '
          '7 m carriageways and ordinary 1.1 m shoulders. No building clearance exception, '
          'new road link, or river change is introduced.')


def apply_context(roads, register, names=None):
    """Apply only this pass's registered controls, including after earlier preparations."""
    for correction in register['roads']:
        if names is not None and correction['name'] not in names:
            continue
        road = next(r for r in roads['roads'] if r['name'] == correction['name'])
        assert road['width'] == correction['width']
        assert road['bridgeSpans'] in [correction['priorBridgeSpans'], correction['bridgeSpans']]
        if road['name'] == 'Marshgate Lane':
            assert road['points'] in [correction['priorPoints'], correction['points']]
            road['points'] = copy.deepcopy(correction['points'])
        else:
            assert road['points'][:3] == correction['priorPoints'][:3]
            assert road['points'][3:5] in [correction['priorPoints'][3:5], correction['points'][3:5]]
            road['points'][3:5] = copy.deepcopy(correction['points'][3:5])
        road['bridgeSpans'] = copy.deepcopy(correction['bridgeSpans'])
        _, _, pixel = mosaic(road['sourceBounds'])
        road['sourcePixels'] = pixel(road['points']).round(3).tolist()
        road['remainingTradesContextAlignment'] = dict(register=REGISTER, review=register['review'])


def build():
    path = ROOT/'data/maps/district-road-traces.json'
    roads = load('data/maps/district-road-traces.json')
    # This immutable capture must predate the correction; never refresh on replay.
    baseline = ROOT/BASELINE
    if not baseline.exists():
        baseline.write_text(json.dumps(roads, indent=2)+'\n')
    prior = load(BASELINE)
    corrections = []
    for name, bounds, pixels in [('Marshgate Lane', CROWN_BOUNDS, CROWN_PIXELS),
                                 ('Three Mills Lane', WESTERN_BOUNDS, WESTERN_PIXELS)]:
        old = next(q for q in prior['roads'] if q['name'] == name)
        _, world, _ = mosaic(bounds)
        points = world(pixels).round(3).tolist()
        if name == 'Marshgate Lane':
            points += old['points'][5:]
            bridge = copy.deepcopy(old['bridgeSpans'])
            # Both ends remain beyond the unchanged canal banks. The intermediate
            # control follows the actual street bend within this existing crossing.
            bridge[0]['points'] = points[2:5]
            explanation = ('Existing provisional crossing moved onto the mapped eastern lane; '
                           'both endpoints relocated, with one intervening road control to '
                           'follow its bend. Identity, deck style, 1.5 m height and uncertainty '
                           'retained. Exact bank alignment and deck versus culvert remain unresolved.')
        else:
            points = copy.deepcopy(old['points'])
            points[3:5] = world(pixels).round(3).tolist()
            bridge = copy.deepcopy(old['bridgeSpans'])
            route = LineString(points[3:5])
            from shapely.geometry import Point
            bridge[0]['points'][0] = list(route.interpolate(route.project(Point(bridge[0]['points'][0]))).coords)[0]
            bridge[0]['points'][0] = [round(q,3) for q in bridge[0]['points'][0]]
            explanation = ('Only the western endpoint of the existing Lea bridge moves onto '
                           'the re-read approach; eastern endpoint, identity, deck style, '
                           'single arch and 2.2 m estimated height retained.')
        bridge[0]['evidence'] = old['bridgeSpans'][0]['evidence'] + ' ' + explanation
        corrections.append(dict(name=name, priorPoints=old['points'], points=points,
            width=old['width'], priorBridgeSpans=old['bridgeSpans'], bridgeSpans=bridge,
            reviewedSourceBounds=bounds, reviewedSourcePixels=pixels,
            ordinaryShoulderWidth=1.1, bridgeReview=explanation))
    before_scene = load('reference/footprint-model-alignment/remaining-trades-before.json')
    river_hashes = dict(ground=digest(load('docs/data/ground-plan.json')['rivers']),
                        west=digest(before_scene['westContext']['rivers']))
    if (ROOT/REGISTER).exists():
        assert river_hashes == load(REGISTER)['retainedRiverGeometrySha256'], 'River geometry changed after the registered road review'
    register = dict(source='Cached georeferenced OS London five-foot 1893 mosaic; original Goad F3 for Crown/Johnson context; western approach reviewed on OS alone because Goad F16 is not cached',
        review=REVIEW, baseline=BASELINE, baselineSha256=digest(prior), roads=corrections,
        retainedRiverGeometrySha256=river_hashes,
        evidenceImages=[])
    apply_context(roads, register)
    before_street, before_overrides = street_clearances(prior['roads'])
    street, overrides = street_clearances(roads['roads'])
    effects = []
    for b in before_scene['buildings']:
        p = Polygon(b['footprint'], b.get('worldHoles', []))
        ident = b['id']
        a = p.intersection(before_overrides.get(ident, before_street)).area
        z = p.intersection(overrides.get(ident, street)).area
        if abs(a-z) > .01:
            effects.append(dict(modelId=ident, priorRoadExclusionAreaM2=a,
                                roadExclusionAreaM2=z, changeAreaM2=z-a))
    register['priorSceneRoadExclusionEffects'] = effects
    for label, bounds, footprint_name in [('marshgate',CROWN_BOUNDS,'crown-johnson'),
                                         ('western',WESTERN_BOUNDS,'western-trades')]:
        canvas, _, pixel = mosaic(bounds)
        image = Image.fromarray(canvas)
        stem = f'reference/footprint-model-alignment/remaining-trades-{label}-road'
        image.save(ROOT/(stem+'-raw.png'))
        draw = ImageDraw.Draw(image)
        name = 'Marshgate Lane' if label == 'marshgate' else 'Three Mills Lane'
        for rr, colour in [(prior,'red'), (roads,'green')]:
            road = next(q for q in rr['roads'] if q['name'] == name)
            draw.line([tuple(p) for p in pixel(road['points'])], fill=colour, width=3)
        alignment = ROOT/f'data/maps/{footprint_name}-footprint-alignment.json'
        if alignment.exists():
            r = load(str(alignment.relative_to(ROOT)))
            rows = r.get('buildings', [])+r.get('mapTracedBuildings', [])
            for b in rows:
                pts = pixel(b['worldFootprint'])
                draw.line([tuple(p) for p in pts]+[tuple(pts[0])], fill='blue', width=2)
        else:
            source = load('reference/footprint-model-alignment/remaining-trades-source-shapes.json')['30174']
            for polygon in source['coordinates']:
                pts = pixel(polygon[0])
                draw.line([tuple(p) for p in pts]+[tuple(pts[0])], fill='blue', width=2)
        image.save(ROOT/(stem+'-after.png'))
        register['evidenceImages'] += [stem+'-raw.png',stem+'-after.png']
    (ROOT/REGISTER).write_text(json.dumps(register, indent=2)+'\n')
    path.write_text(json.dumps(roads, indent=2)+'\n')
    print('Remaining-trades context: two mapped 7 m streets, existing crossings relocated, mill split and rivers retained.')


if __name__ == '__main__':
    build()
