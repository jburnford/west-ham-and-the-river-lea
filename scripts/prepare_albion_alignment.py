"""Reconcile Albion exteriors and reject the former soap-yard envelope."""
import json
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Polygon, LineString, Point, shape
from shapely.ops import unary_union, split, nearest_points
from prepare_ink_works_alignment import axis, rings
from prepare_three_mills_north_alignment import polygon
from factory_alignment_records import record_group

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ('Explicit OS Albion match; previous estimated elevations and roofs retained. '
          'No Goad corroboration asserted. ')
REMOVAL = ('Raw OS mosaic and annotated OS source review show the prior polygon crossing '
           'the southwest Soap Works (Disused) yard boundary. Its northwestern rectangle '
           'is unshaded; the southeast portion is open yard, with a parcel boundary '
           'continuing through the former footprint. No enclosed shaded manufacturing '
           'range supports this envelope. Removal is based on positive yard-boundary '
           'evidence, not merely absence from the supplied extract.')


def build():
    load = lambda p: json.loads((ROOT / p).read_text())
    before = load('reference/footprint-model-alignment/ratner-albion-before.json')
    models = {b['id']: b for b in before['buildings']}
    cached = load('reference/footprint-model-alignment/ratner-albion-source-shapes.json')
    source = {fid: polygon(shape(cached[str(fid)])) for fid in [4945, 107344, 4270, 222333]}
    groups, buildings = [], []
    north = polygon(set_precision(unary_union([source[4945], source[107344]]), .001))
    south = polygon(set_precision(unary_union([source[4270], source[222333]]), .001))
    # The eastern spur has a mapped reentrant corner. Join that corner to the
    # opposite wall to retain the prior shed as an explicit roof interpretation.
    notch = (-829.577, 219.634)
    upper_wall = LineString([(-835.530, 216.670), (-822.561, 209.513)])
    opposite = upper_wall.interpolate(upper_wall.project(Point(notch)))
    # Snap the cut endpoints to the actual rounded exterior.
    edge = south.boundary
    a = nearest_points(edge, opposite)[0]
    b = nearest_points(edge, Point(notch))[0]
    pieces = list(split(south, LineString([a, b])).geoms)
    assert len(pieces) == 2, 'Eastern shed chord must divide the exterior once'
    shed = min(pieces, key=lambda p: p.area)
    store = max(pieces, key=lambda p: p.area)
    specs = [
        ('albion-north', [4945, 107344], ['west-421-1'], north, [north],
         'Two supplied polygons join at an artificial seam; the mapped northern Albion range retains its courtyard-facing reentrants.'),
        ('albion-south', [4270, 222333], ['west-421-2', 'west-421-3'], south, [store, shed],
         'Southern body and western projection join across an artificial source seam. The small eastern spur is divided at its mapped reentrant corner by an interpreted roof boundary; OS supplies the combined exterior, not this internal roof division.'),
    ]
    for gid, fids, ids, target, parts, division in specs:
        angle = axis(target, models[ids[0]]['rotation'])
        group, rows = record_group(gid, fids, source, models, ids,
            [models[i]['name'] for i in ids], target, parts, angle, division,
            review_prefix=REVIEW)
        groups.append(group)
        buildings.extend(rows)
        emitted = unary_union([Polygon(row['worldFootprint'], row['worldHoles']) for row in rows])
        assert emitted.symmetric_difference(target).area < .01
        assert all(parts[i].intersection(parts[j]).area < .01
                   for i in range(len(parts)) for j in range(i))
    stack = next(s for s in before['structures'] if s['id'] == 'west-421-4-stack')
    result = dict(source='Author-supplied london_buildings_1891-96_corr_v1.gpkg; cached OS London five-foot 1893 mosaic',
        sourceCRS='EPSG:3857 reprojected through BNG; scene origin E538900,N183209',
        method='Explicit OS exteriors for Albion; separate northern/southern bodies preserve the open courtyard. Southwest disused-soap-yard envelope rejected after raw map review.',
        groups=groups, buildings=buildings, structures=[],
        removedBuildings=[dict(models['west-421-4'], review=REMOVAL)],
        removedStructures=[dict(stack, review='Prior 25 m chimney was inferred from the rejected west-421-4 manufacturing envelope, not transcribed from an OS chimney symbol. The tiny independent source outline 1018263 is not identified as a chimney; its function remains deferred.')],
        evidenceImages=['reference/footprint-model-alignment/albion-soap-yard-evidence.png', 'reference/footprint-model-alignment/ratner-albion-soap-raw.png', 'reference/footprint-model-alignment/ratner-albion-source.png', 'reference/footprint-model-alignment/ratner-albion-models.png'],
        yardEvidenceCrop=load('reference/footprint-model-alignment/albion-soap-yard-evidence.json'),
        deferred=[dict(sourceFid=1018263, reason='Small boundary-side outline, 5.644 m²; no positive chimney symbol or reliable function. Retain as source evidence without introducing a full-height range or stack.')])
    (ROOT / 'data/maps/albion-footprint-alignment.json').write_text(json.dumps(result, indent=2) + '\n')
    gap = north.distance(south)
    assert gap > 0
    print(f'Albion: three ranges, four unique source polygons, courtyard gap {gap:.3f} m; false soap-yard range and inferred chimney removed.')
    for row in buildings:
        print(row['modelId'], 'area', round(Polygon(row['worldFootprint']).area, 3), 'height', row['preservedHeight'], 'roof rise', round(row['preservedRoofRise'], 3))


if __name__ == '__main__':
    build()
