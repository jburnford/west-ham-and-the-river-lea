"""Prepare the register for Samuel Berger & Co.'s rice starch works (site 250, Bromley).

Geometry comes from the author's 1891-96 OS building GeoPackage. The large shaded outline (fid 85)
is divided into the compartments that Goad's July 1893 insurance plan (vol. F sheet 16) draws inside
it; each division is read in a site-local frame aligned with the works' walls and recorded below as
u/v limits, so the cut can be repeated or revised. Storeys follow the Goad figures where legible.

Writes data/maps/berger-starch-footprint-alignment.json. Rerun only to regenerate that register.
"""
import gzip
import json
import math
from pathlib import Path

from shapely import wkt
from shapely.affinity import affine_transform
from shapely.geometry import Polygon, box, shape
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
E0, N0 = 538900, 183209
OUT = ROOT/'data/maps/berger-starch-footprint-alignment.json'
SOURCE = ROOT/'reference/historic-building-footprints-2026-09-28/west-ham-buffer-buildings-bng.geojson.gz'
GOAD = 'goad-f16'

# Site-local frame: origin at the west corner of fid 85, u along the works' long walls (-21.6 degrees
# from scene x), v across them (towards Love Lane). Scene x = ox + u cos - v sin; z = oz + u sin + v cos.
FRAME = {'origin': [-1027.2, 555.3], 'rotationDegrees': -21.6}

GOAD_NOTE = ('Goad Insurance Plan of London, North East District vol. F sheet 16, July 1893 '
             '(reference/factory-building-survey/goad-f16.tiff), block F.196 "Samuel Berger & Co. Rice Starch Works", '
             'marked "Admission refused" (a sketch survey from outside)')

# Compartments inside fid 85: (id suffix, Goad letters, name, u0, u1, v0, v1, storeys, Goad reading, roof axis)
COMPARTMENTS = [
    ('stoves-west', 'No. 4, stoves, stove holes', 'drying stove range (No. 4)', -6, 14, 0, 50, 2,
     'Goad draws a long range of stove cells with "Stove holes" along the west wall and "No. 4" at the north end; '
     'no storey figure is legible.', 'z'),
    ('boxing-room', 'V', 'boxing room (V)', 14, 22, 0, 50, 2, 'Goad "V Boxing room &c", storey figure 2.', 'z'),
    ('stoves-t', 'T', 'drying stoves (T)', 22, 33, 10, 50, 2,
     'Goad "T Stoves" with "Stove holes" along its east wall; storey figure not legible.', 'z'),
    ('no3-j1', 'No. 3, J1', 'warehouse ends (No. 3, J1)', 13, 26, -12, 10, 2, 'Goad "No. 3" and "J1", each marked 2.', 'x'),
    ('warehouse-j', 'J', 'warehouse with floating room over (J)', 26, 43.5, -12, 10, 2,
     'Goad "J Whse: 1st floating rm. over", marked 2.', 'x'),
    ('range-h', 'H', 'range H', 43.5, 56.5, -12, 10, 2.5, 'Goad "H", marked 2 1/2; use not lettered.', 'z'),
    ('mill-g', 'G', 'mill and stones (G)', 56.5, 64, -12, 0, 2.5, 'Goad "G Mill & stones", marked 2 1/2.', 'z'),
    ('engine-boilers', 'E, F', 'engine and boiler house (E, F)', 56.5, 66, 0, 15, 1,
     'Goad "E" with "Eng." (steam engine) and "F" with two hatched steam-boiler symbols; no storey figure, read as one tall storey.', 'z'),
    ('soda-ash-s', 'S', 'soda ash range with scraping room over (S)', 33, 44, 10, 50, 2,
     'Goad "S Soda ash &c 1st, scraping rm. over" (two floors).', 'z'),
    ('vats-r', 'R', 'vats and pumps range (R)', 44, 56.5, 10, 44, 2, 'Goad "R Vats, pumps &c", marked 2.', 'z'),
    ('stable-k', 'K', 'stable with engineer\'s shop over (K)', 56.5, 81, 15, 19.5, 2,
     'Goad "K Stable, engineer &c over" (two floors).', 'x'),
    ('settling-p', 'P', 'settling slides (P)', 56.5, 81, 19.5, 34, 1.5, 'Goad "P Settling slides &c", marked 1 1/2.', 'x'),
    ('settling-o', 'O', 'settling vats and boxing room (O)', 56.5, 81, 34, 44, 1.5,
     'Goad "O Settling vats & boxing room", marked 1 1/2.', 'x'),
    ('store-n', 'N', 'store with vats over (N)', 44, 81, 44, 56, 2, 'Goad "Store" and "N Vats over" (two floors) along the Love Lane wall; its north edge is read from a dashed Goad line at about v 44.', 'x'),
    ('settling-l', 'L', 'settling vats with packing room over (L)', 81, 100, 12, 30, 2,
     'Goad "L Settling vats & packing over", marked 2.', 'x'),
    ('settling-m', 'M', 'settling vats (M)', 81, 100, 30, 52, 1.5,
     'Goad "M Settling vats", marked 1=2 (one and two storeys).', 'x'),
    ('stoves-south', 'Stoves', 'south drying stoves', -6, 14, 50, 70, 2,
     'Goad "Stoves" on Love Lane; storey figure read as 2 but faint.', 'x'),
    ('frame-room-z', 'Z', 'frame room (Z)', 14, 33, 50, 70, 1.5, 'Goad "Z Frame room", marked 1=2.', 'z'),
]

# Separate GeoPackage outlines on the works.
SEPARATE = [
    (5106, 'warehouse-a', 'A', 'warehouse (A)', 2, 'brick',
     'Goad "A Whse." marked 2; a struck "40" inside the range is not read as a height.'),
    (122409, 'office-b', 'B, D', 'office and dwelling (B, D) on the north street', 2.5, 'brick',
     'Goad "D Dwg." (dwelling, figure read as 3) and "B Off." (office, figure read as 2-3); taken together as 2 1/2.'),
    (702216, 'range-c', 'C', 'range C on the north street', 2, 'brick', 'Goad "C"; figure read as 2.'),
    (777789, 'dwelling-d1', 'D1', 'dwelling D1', 2, 'brick', 'Goad "D1"; no storey figure legible.'),
    (825899, 'dwelling-d-west', 'D', 'dwelling beside D1', 2, 'brick', 'Goad dwelling range west of "D Dwg."; no figure legible.'),
    (418306, 'cart-shed', 'Carts &c', 'cart shed', 1, 'brick', 'Goad "Carts &c" at the north end of L.'),
    (325406, 'carpenters-shop-w', 'W', "carpenter's shop (W)", 1, 'wood',
     'Goad "W Carp. &c", coloured yellow (wood) and marked "Br. & timber"; one storey.'),
    (868225, 'lean-to-ef', '', 'lean-to beside the engine house', 1, 'brick',
     'Narrow shaded outline against the engine and boiler house; not lettered on Goad.'),
]
CHIMNEY_FID = 966028
MAIN_FID = 85


def load_outlines(fids):
    rows = json.loads(gzip.decompress(SOURCE.read_bytes()))['features']
    out = {}
    for f in rows:
        fid = f['properties'].get('sourceFid')
        if fid in fids:
            g = affine_transform(shape(f['geometry']), [1, 0, 0, -1, -E0, N0]).buffer(0)
            out[fid] = g
    missing = set(fids) - set(out)
    assert not missing, missing
    return out


def local_to_world(u, v):
    (ox, oz), t = FRAME['origin'], math.radians(FRAME['rotationDegrees'])
    return ox + u*math.cos(t) - v*math.sin(t), oz + u*math.sin(t) + v*math.cos(t)


def rect(u0, u1, v0, v1):
    return Polygon([local_to_world(u, v) for u, v in [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]])


def ring(g):
    g = g.simplify(0.15)
    if g.geom_type == 'MultiPolygon':
        g = max(g.geoms, key=lambda p: p.area)
    coords = [[round(x, 3), round(z, 3)] for x, z in list(g.exterior.coords)[:-1]]
    if not Polygon(coords).is_valid:
        fixed = Polygon(coords).buffer(0)
        fixed = max(getattr(fixed, 'geoms', [fixed]), key=lambda p: p.area)
        coords = [[round(x, 3), round(z, 3)] for x, z in list(fixed.exterior.coords)[:-1]]
    assert Polygon(coords).is_valid
    return coords


def build():
    fids = [MAIN_FID, CHIMNEY_FID] + [s[0] for s in SEPARATE]
    outlines = load_outlines(fids)
    main = outlines[MAIN_FID]
    # Where two rectangles overlap, the compartment listed first keeps the ground.
    pieces, taken = {}, Polygon()
    for c in COMPARTMENTS:
        pieces[c[0]] = main.intersection(rect(*c[3:7])).difference(taken)
        taken = unary_union([taken, pieces[c[0]]])
    # A compartment keeps its largest part; slivers cut off by notches in the outline go to the leftovers.
    for k, g in pieces.items():
        if g.geom_type == 'MultiPolygon':
            pieces[k] = max(g.geoms, key=lambda p: p.area)
    # Anything of fid 85 outside every rectangle joins the compartment it shares most boundary with.
    rest = main.difference(unary_union(list(pieces.values())))
    for part in getattr(rest, 'geoms', [rest]):
        if part.geom_type != 'Polygon' or part.area < 0.01:
            continue
        shared = {k: part.buffer(0.05).intersection(pieces[k]).area for k in pieces}
        best = max(shared, key=shared.get)
        merged = unary_union([pieces[best], part]).buffer(0.02, join_style=2).buffer(-0.02, join_style=2)
        assert shared[best] > 0 and merged.geom_type == 'Polygon', ('leftover does not join', best, round(part.area, 1),
                                                                    [round(c, 1) for c in part.centroid.coords[0]])
        pieces[best] = merged
    assert abs(sum(p.area for p in pieces.values()) - main.area) < 1.0, 'fid 85 not fully assigned'
    buildings = []
    for key, letters, label, u0, u1, v0, v1, storeys, reading, axis in COMPARTMENTS:
        g = pieces[key]
        assert g.geom_type == 'Polygon' and g.area > 20, (key, g.geom_type, g.area)
        buildings.append({
            'id': f'b250-{key}', 'siteId': 250, 'source': 'os-1893',
            'name': f'Berger rice starch works — {label}',
            'footprintRotationDegrees': FRAME['rotationDegrees'],
            'roofAxis': axis, 'material': 'brick', 'roof': 'gable', 'storeysEstimate': storeys,
            'footprintSource': 'author-os-footprints-1891-96', 'sourceFids': [MAIN_FID],
            'goadLetters': letters,
            'footprintEvidence': (f'Part of the single shaded outline fid {MAIN_FID} ({main.area:.0f} m²) in the author\'s 1891–96 OS '
                                  'building GeoPackage, simplified at 0.15 m; checked against the cached NLS OS London five-foot mosaic '
                                  f'(os-london-five-foot-1893). Divided along the compartment lines of {GOAD_NOTE}, registered to the '
                                  'GeoPackage by a building-mask fit (median local misfit 1.0 m, maximum 2.5 m). Cut in a site frame at '
                                  f'{FRAME["rotationDegrees"]} degrees: u {u0} to {u1} m, v {v0} to {v1} m from scene '
                                  f'({FRAME["origin"][0]}, {FRAME["origin"][1]}). The cut lines are a reading of the Goad, accurate to about 1–2 m.'),
            'heightEvidence': (f'Storeys from Goad: {reading} Eaves height is the project’s default for the storey count '
                               '(explicit estimate); Goad gives floors, not heights.'),
            'roofEvidence': ('Goad marks "T" (tiled roof) along several walls of the works; the renderer draws one roof covering, so the tile '
                             'reading is recorded but not shown. Pitched roof and its ridge direction are interpretations; Goad and the OS '
                             'draw no ridges.'),
            'functionEvidence': f'Use as lettered on {GOAD_NOTE}.',
            'worldFootprint': ring(g),
        })
    for fid, key, letters, label, storeys, material, reading in SEPARATE:
        g = outlines[fid]
        buildings.append({
            'id': f'b250-{key}', 'siteId': 250, 'source': 'os-1893',
            'name': f'Berger rice starch works — {label}',
            'material': material, 'roof': 'gable', 'storeysEstimate': storeys,
            'footprintSource': 'author-os-footprints-1891-96', 'sourceFids': [fid], 'goadLetters': letters,
            'footprintEvidence': (f'Source outline fid {fid} ({g.area:.0f} m²) from the author\'s 1891–96 OS building GeoPackage, '
                                  'simplified at 0.15 m; checked against the cached NLS OS London five-foot mosaic (os-london-five-foot-1893).'),
            'heightEvidence': (f'Storeys from {GOAD_NOTE}: {reading} Eaves height is the project default for that storey count '
                               '(explicit estimate).'),
            'roofEvidence': 'Pitched roof is an interpretation; no ridges are drawn on Goad or the OS.',
            'functionEvidence': f'As lettered on Goad sheet F16 block F.196.' if letters else 'Not lettered on Goad; function unknown.',
            'worldFootprint': ring(g),
        })
    c = outlines[CHIMNEY_FID]
    centre = c.centroid
    side = math.sqrt(c.area)
    chimney = {
        'id': 'stack-250-boiler', 'siteId': 250, 'source': 'os-1893', 'kind': 'chimney',
        'name': 'Berger rice starch works boiler chimney',
        'x': round(centre.x, 3), 'z': round(centre.y, 3), 'height': round(80*0.3048, 4), 'mappedHeightFeet': 80,
        'heightEvidence': ('"80" printed beside the Goad chimney symbol (sheet F16, block F.196), read as height in feet as on the same '
                           'sheet\'s "60\'" stack at Cleugh\'s jute mill; converted at 0.3048 m/ft. The prime is not legible here.'),
        'symbolKey': 'goad-symbol-key-1926',
        'radius': round(min(1.1, side*0.35), 2), 'section': 'square', 'material': 'brick', 'baseHeight': 0.34,
        'rotation': FRAME['rotationDegrees'], 'sourceFootprintFid': CHIMNEY_FID,
        'sourcePolygons': [[ring(c)]],
        'evidenceType': 'map-interpretation', 'supportingSources': ['author-os-footprints-1891-96', 'os-1893', GOAD],
        'positionEvidence': (f'Placed on the small square outline fid {CHIMNEY_FID} ({c.area:.1f} m²) standing alone in the yard east of the '
                             'boiler house; Goad sheet F16 draws a square chimney symbol there, beside the hatched boilers of F.'),
        'profileEvidence': 'Square section follows the mapped base; taper, crown and brickwork are interpreted, not measured.',
    }
    register = {
        'schemaVersion': 1, 'date': '2026-10-04', 'site': 250, 'name': 'Samuel Berger & Co. rice starch works',
        'source': ("Author-supplied london_buildings_1891-96_corr_v1.gpkg (project extract west-ham-buffer-buildings-bng.geojson.gz); "
                   f"cached NLS OS London five-foot mosaic (os-london-five-foot-1893); {GOAD_NOTE}"),
        'sourceCRS': 'EPSG:27700 to scene origin E538900,N183209; x east, z south, metres',
        'method': ('Berger rice starch works 4 October 2026: first models for site 250 (previously excluded as outside the western '
                   'riverside corridor, and drawn as two interpreted placeholder ranges). Footprints are GeoPackage outlines; the '
                   f'{main.area:.0f} m² main outline (fid {MAIN_FID}) is divided into the {len(COMPARTMENTS)} compartments Goad draws '
                   'inside it, cut along lines read in a site frame (see scripts/prepare_berger_starch_alignment.py). The works runs west '
                   'beyond the GIS site parcel: Goad shows the stoves, boxing room and stove holes on the Powis Road side as part of '
                   'Berger\'s works, so the whole outline is modelled.'),
        'goadRegistration': {
            'sheet': GOAD, 'file': 'reference/factory-building-survey/goad-f16.tiff',
            'url': 'https://commons.wikimedia.org/wiki/File:Insurance_Plan_of_London_North_East_District_Vol._F;_sheet_16_(BL_152670).tiff',
            'sha256': 'c13041033b6c123170b9cd790dbaf5b54dc01d3ee6d9ad97444e4c07d140d370',
            'pixelToWorld': [0.12117577, -0.10050115, -1304.00240994, 396.00371604],
            'method': ('Similarity fit: two rough controls (Ratner Safe Works, Berger works), then ECC alignment of the sheet\'s pink and '
                       'yellow building colours to the rasterised GeoPackage outlines inside the sheet, affine solution projected back to '
                       'a similarity. Local translation check in 120 m windows: median 1.0 m, 90th percentile 1.8 m, maximum 2.5 m.')},
        'siteFrame': FRAME,
        'evidenceNotes': [
            'Goad symbol reading follows the Goad key (reference/factory-building-survey/goad-symbol-key-1926.jpg, a 1926 printing): '
            'figures are storeys, "T" a tiled roof, hatched rectangles steam boilers, "Eng." a steam engine.',
            'Goad marks the works "Admission refused": its interior divisions are a sketch survey from outside and may be simplified.',
            'Small outlines on the east edge (fids 765959, 1073764, 894372) are outside the works wall on Cottage Place and are not modelled here.',
        ],
        'buildings': [], 'structures': [], 'groups': [],
        'additionalSites': [{
            'id': 250, 'name': 'Samuel Berger & Co. rice starch works', 'sources': ['os-1893'],
            'coverage': 'Individual OS-mapped ranges; compartments and storeys from Goad sheet F16',
            'notes': ('Named "Starch Works" on the OS five-foot plan and "Samuel Berger & Co. Rice Starch Works" on Goad F16 (July 1893). '
                      'Roof exteriors are mapped; compartment divisions and storeys follow Goad; heights, roof forms and materials not '
                      'shown on Goad are estimates.')}],
        'additionalBuildings': buildings,
        'additionalStructures': [chimney],
    }
    OUT.write_text(json.dumps(register, indent=2, ensure_ascii=False)+'\n')
    return register


if __name__ == '__main__':
    r = build()
    print(len(r['additionalBuildings']), 'buildings;', sum(Polygon(b['worldFootprint']).area for b in r['additionalBuildings']).__round__(0), 'm2')
