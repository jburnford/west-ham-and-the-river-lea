"""Author Ratner OS exteriors with explicitly interpreted roof compartments."""
import json
from pathlib import Path
from shapely import affinity, set_precision
from shapely.geometry import Point, Polygon, box, shape
from shapely.ops import unary_union
from prepare_ink_works_alignment import axis
from prepare_three_mills_north_alignment import polygon
from factory_alignment_records import record_group

ROOT = Path(__file__).resolve().parents[1]


def build():
    load = lambda path: json.loads((ROOT/path).read_text())
    before = load('reference/footprint-model-alignment/ratner-albion-before.json')
    models = {b['id']: b for b in before['buildings']}
    cached = load('reference/footprint-model-alignment/ratner-albion-source-shapes.json')
    source = {fid: polygon(shape(cached[str(fid)])) for fid in [395, 10793]}
    target = source[395]
    # The OS shows a northern open court between the western and eastern arms.
    # Preserve the earlier office/plant identities as interpreted compartments:
    # these cuts are roof divisions, not independently mapped exterior walls.
    local = affinity.rotate(target, 30, origin=(0, 0))
    office = local.intersection(box(-1000, -400, -880, -279))
    plant = local.intersection(box(-865, -400, -800, -273))
    main = local.difference(unary_union([office, plant]))
    parts = [polygon(set_precision(affinity.rotate(p, -30, origin=(0, 0)), .001))
             for p in [main, plant, office]]
    ids = ['west-420-1', 'west-420-3', 'west-420-4']
    division = ('Western office occupies the western courtyard arm; northeast plant occupies the eastern head. '
                'Internal cuts in the -30 degree review frame are west arm z=-279 and northeast head x=-865,z=-273. '
                'These are interpreted roof compartments retaining previous identities/elevations, not OS party walls; '
                'their disjoint union preserves the complete U-shaped exterior and open northern courtyard.')
    prefix = 'Explicit Ratner OS exterior match; previous interpreted elevations and roofs retained. '
    group, rows = record_group('ratner-main', [395], source, models, ids,
        [models[id]['name'] for id in ids], target, parts, -30, division,
        review_prefix=prefix)
    river = polygon(set_precision(source[10793], .001))
    river_id = 'west-420-2'
    angle = axis(river, models[river_id]['rotation'])
    river_group, river_rows = record_group('ratner-river', [10793], source, models,
        [river_id], [models[river_id]['name']], river, [river], angle,
        review_prefix=prefix)
    old = next(s for s in before['structures'] if s['id'] == 'west-420-3-stack')
    parent = parts[1]
    centre = Point(round(parent.centroid.x, 3), round(parent.centroid.y, 3))
    assert parent.contains(centre.buffer(old['radius'])), 'Inferred chimney must fit its parent'
    stack = dict(id=old['id'], centre=list(centre.coords)[0], rotation=-30,
        priorCentre=[old['x'], old['z']], preservedHeight=old['height'],
        parentBuildingId='west-420-3', parentFractions=[.5, .5],
        review='Inferred process chimney transferred to the corrected northeast plant compartment centroid, '
               'with the entire 1.2 m radius inside its parent. Not an OS chimney symbol or measured position; '
               'previous height 28 m, radius 1.2 m and profile retained.')
    union = unary_union(parts)
    assert union.symmetric_difference(target).area < .05
    assert sum(p.area for p in parts)-union.area < .001
    assert all(p.is_valid for p in parts+[river])
    # This explicit point in the northern courtyard must remain outside every range.
    court = Point(-911, 185)
    assert not unary_union(parts+[river]).covers(court)
    result = dict(source='Author-supplied london_buildings_1891-96_corr_v1.gpkg',
        sourceCRS='EPSG:3857 reprojected through BNG; scene origin E538900,N183209',
        method='Reviewed Ratner OS matches: complete courtyard exterior split into interpreted existing roof compartments; separate eastern room. Existing elevations retained.',
        groups=[group, river_group], buildings=rows+river_rows, structures=[stack],
        deferred=[dict(sourceFids=[964640, 966740, 967834],
            reason='Small separate outlines at plant corners may be projections or process plant; no full-height additions or mapped chimney attribution without further evidence.')])
    (ROOT/'data/maps/ratner-footprint-alignment.json').write_text(json.dumps(result, indent=2)+'\n')
    print(f'Ratner: 4 existing ranges, 2 source exteriors; partition error {union.symmetric_difference(target).area:.6f} m2; inferred stack boundary clearance {centre.distance(parent.boundary):.3f} m.')


if __name__ == '__main__':
    build()
