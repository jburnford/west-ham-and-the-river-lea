"""Correct the OS northern Marshgate frontage beside Alderson's rope works."""
import hashlib
import json
from pathlib import Path

from shapely.geometry import LineString, Polygon
from factory_map_sources import mosaic

ROOT = Path(__file__).resolve().parents[1]
REGISTER = 'data/maps/alderson-rope-context-alignment.json'
BOUNDS = [-1025, -440, -895, -285]
PIXELS = [[286, 408], [276, 379], [244, 308], [196, 218], [165, 163]]
REVIEW = ('Raw OS five-foot map re-read along the lane between the eastern rope-works wall and the eastern street edge. Preserve northern-arm controls0–8, then fit the south bend clear of the mapped drying house and follow the eastern rope frontage to the lane head at the railway underpass boundary. The former tail cut through the mapped eastern rope roof and extended into the railway. Existing interpreted 7 m carriageway and normal 1.1 m shoulder retained; no new road connection or bridge inferred.')
load = lambda p: json.loads((ROOT/p).read_text())
digest = lambda data: hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def apply_context(roads, register):
    correction = register['road']
    road = next(r for r in roads['roads'] if r['name'] == correction['name'])
    assert road['points'] in [correction['priorPoints'], correction['points']]
    assert road['width'] == correction['width'] and road['bridgeSpans'] == correction['priorBridgeSpans']
    road['points'] = correction['points']
    _, _, pixel = mosaic(road['sourceBounds'])
    road['sourcePixels'] = pixel(road['points']).round(3).tolist()
    road['aldersonRopeAlignment'] = dict(register=REGISTER, review=register['review'])


def build():
    roads = load('data/maps/district-road-traces.json')
    prior = load('data/maps/mill-brush-context-alignment.json')['additionalRoad']
    road = next(r for r in roads['roads'] if r['name'] == prior['name'])
    others = {r['name']: r for r in roads['roads'] if r['name'] != prior['name']}
    _, world, _ = mosaic(BOUNDS)
    points = prior['points'][:9] + world(PIXELS).round(3).tolist()
    old_line, new_line = LineString(prior['points']), LineString(points)
    before = load('reference/footprint-model-alignment/marshgate-trades-before.json')
    ink_limits = []
    for ident in ['site940-firelighter', 'site940-24']:
        b = next(b for b in before['buildings'] if b['id'] == ident)
        body = Polygon(b['footprint'], b.get('worldHoles', []))
        ink_limits.append(dict(modelId=ident,
            priorOverlapAreaM2=body.intersection(old_line.buffer(4.6, cap_style=2, join_style=2)).area,
            overlapAreaM2=body.intersection(new_line.buffer(4.6, cap_style=2, join_style=2)).area,
            evidence='Inherited unaligned Goad rectangle differs from the OS wall beside this lane; already intersects the prior route. Existing renderer clips provisional roofs against roads. This pass retains the mapped lane and defers an independent ink-building outline review.'))
    register = dict(source='Cached georeferenced OS London five-foot 1893 mosaic; original July 1893 Goad F3 for rope range context',
        review=REVIEW, road=dict(name=prior['name'], priorPoints=prior['points'], points=points,
            width=7, priorBridgeSpans=prior['bridgeSpans'],
            reviewedSourceBounds=BOUNDS, reviewedSourcePixels=PIXELS,
            preservedPointCount=9, ordinaryShoulderWidth=1.1),
        inheritedInkAlignmentLimits=ink_limits,
        retainedRiverGeometrySha256=dict(
            ground=digest(load('reference/footprint-model-alignment/mill-brush-brewery-ground-before.json')['rivers']),
            west=digest(before['westContext']['rivers'])),
        evidenceImages=['reference/footprint-model-alignment/alderson-rope-road-raw.png',
            'reference/footprint-model-alignment/alderson-rope-road-grid.png',
            'reference/footprint-model-alignment/alderson-rope-road-after.png',
            'reference/footprint-model-alignment/alderson-rope-goad.png'])
    apply_context(roads, register)
    assert {r['name']: r for r in roads['roads'] if r['name'] != prior['name']} == others
    assert road['points'][:9] == prior['points'][:9]
    (ROOT/REGISTER).write_text(json.dumps(register, indent=2)+'\n')
    (ROOT/'data/maps/district-road-traces.json').write_text(json.dumps(roads, indent=2)+'\n')
    print('Alderson context: northern Marshgate tail follows the OS lane; 7 m width, first nine controls, split, bridges and rivers retained.')


if __name__ == '__main__':
    build()
