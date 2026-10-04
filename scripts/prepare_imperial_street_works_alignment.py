"""Prepare the register for the works between Imperial Street and the LT&SR at Bromley (sites 514, 795, 942, 516).

Alex. Cleugh's jute spinning mill, Fraser & Fraser's boiler and tank works, F. Brayne & Co.'s pottery and
J. B. Day's engineering shop, as drawn on Goad's July 1893 insurance plan vol. F sheet 16 (block numbers
F.201-F.206). Geometry is one building per outline of the author's 1891-96 OS building GeoPackage; Goad
supplies names, uses, storeys, construction (pink brick, yellow wood, grey metal), skylights, boilers,
chimneys and kilns. Writes data/maps/imperial-street-works-footprint-alignment.json.
"""
import json
import math
from pathlib import Path

from shapely.geometry import Point, Polygon

from prepare_berger_starch_alignment import load_outlines, ring

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'data/maps/imperial-street-works-footprint-alignment.json'
GOAD = ('Goad Insurance Plan of London, North East District vol. F sheet 16, July 1893 '
        '(reference/factory-building-survey/goad-f16.tiff)')

SITES = {
    514: ('Alex. Cleugh jute spinning mill (Imperial Spinning Mills)',
          'Named "Imperial Spinning Mills (Hemp & Jute)" on the OS five-foot plan and "Alex. Cleugh Jute Spinning Mill" with a '
          '"Jute drying yard" on Goad F16 (July 1893).'),
    795: ('Fraser & Fraser boiler and tank works',
          'Named "Steam Boiler Works" on the OS five-foot plan and "Fraser & Fraser, Boiler & Tank Works" (block F.206) on Goad F16.'),
    942: ('F. Brayne & Co. pottery (Bow Pottery)',
          'Named "Bow Pottery" on the OS five-foot plan and "F. Brayne & Co. Pottery" with four kilns on Goad F16, beside the moat and dock.'),
    516: ('J. B. Day engineering works and wheelwright (Iron Works)',
          'Named "Iron Works" and "Van & Wheel Works" on the OS five-foot plan; Goad F16 block F.201 names "J. B. Day, Engineer" and '
          'a "Wheelwright" on the same yard.'),
}

# (fid, site, key, name, storeys, material, Goad reading, extra fields)
BUILDINGS = [
    # Cleugh jute spinning mill
    (1989, 514, 'spinning-mill', 'spinning and preparing sheds', 1, 'brick',
     'Goad "Spinning" and "Preparing" sheds marked 1, with grey skylight bands between pink roof strips and the note '
     '"Iron & tile roofs".', {'roofGlazing': True, 'footprintRotationDegrees': 56.6, 'roofAxis': 'x', 'roofBays': 4,
                               'eavesHeight': 5.0}),
    (154514, 514, 'jute-shed', 'jute shed', 1, 'brick', 'Goad "Jute shed" (716), marked 1.', {}),
    (627583, 514, 'yarn-store', 'yarn store', 1, 'brick', 'Goad "Yarn store" (714), marked 1.', {}),
    (800652, 514, 'north-west-range', 'north-west range of the mill', 1, 'brick',
     'Goad draws this as part of the mill\'s north-west corner; no separate use or figure.', {}),
    (190508, 514, 'engine-house', 'engine and boiler house', 2, 'brick',
     'Goad "E. & B." (engine and boilers, 30 h.p.), marked 2.', {}),
    (244144, 514, 'boiler-house', 'boiler house', 1, 'brick', 'Goad draws two hatched steam-boiler symbols here.', {}),
    (765044, 514, 'smithy', 'smithy', 1, 'brick', 'Goad "Smithy" (726) on the Private Road.', {}),
    (862074, 514, 'stores-north', 'stores', 1.5, 'brick', 'Goad "Stores" (728), marked 1 1/2.', {}),
    (881387, 514, 'stores-south', 'stores', 1.5, 'brick', 'Goad "Stores" (728), marked 1 1/2.', {}),
    (832259, 514, 'office', 'office', 1, 'brick', 'Goad "Off." (office) at 728.', {}),
    (681437, 514, 'iron-shed', 'iron shed', 1, 'metal', 'Goad 730, coloured grey (a metal building in the Goad key).',
     {'roofMaterial': 'iron'}),
    (941497, 514, 'shaker-house', 'shaker house', 1, 'brick', 'Goad "Shaker" at the south end of the preparing shed.', {}),
    # Fraser & Fraser boiler and tank works
    (5337, 795, 'erecting-shed', 'erecting shed', 1, 'wood',
     'Goad 694, coloured yellow (wood), "(20 h.p.)", marked 1; one tall storey for boiler erecting is an interpretation.',
     {'eavesHeight': 6.5}),
    (1291, 795, 'boiler-shop', 'boiler shop', 1.5, 'brick',
     'Goad block F.206 main shop, pink and yellow (brick with timber parts), marked 1=2, with a grey skylight band.',
     {'roofGlazing': True, 'footprintRotationDegrees': 64.7, 'roofAxis': 'x', 'roofBays': 4, 'eavesHeight': 7.0}),
    (91116, 795, 'pattern-shop', 'pattern-making shop', 2, 'brick', 'Goad "Pattern making &c" (688), marked 2.', {}),
    (269476, 795, 'wood-upper-range', 'range with timber upper floor', 2, 'brick', 'Goad "Wood 2nd" (wooden second floor), 686.', {}),
    (894699, 795, 'furnace', 'furnace house', 1, 'metal', 'Goad "Furnace" (685), coloured grey (metal).', {'roofMaterial': 'iron'}),
    (661674, 795, 'iron-shed', 'iron shed', 1, 'metal', 'Goad 692, coloured grey (metal).', {'roofMaterial': 'iron'}),
    (719732, 795, 'boiler-house', 'boiler house', 1, 'brick', 'Goad draws a hatched steam-boiler symbol here (682).', {}),
    (554920, 795, 'tank-over-store', 'store with tank over', 2, 'brick', 'Goad "Tank over" and "2 Stores &c" (678).', {}),
    (115148, 795, 'stores', 'stores', 2, 'brick', 'Goad "2 Stores &c" (676).', {}),
    (687782, 795, 'coal-store', 'coal store', 1, 'brick', 'Goad "Coal" (674).', {}),
    (9387, 795, 'tank-works', 'tank works', 1, 'metal',
     'Goad "Tank works" (670-672), coloured grey (a metal building); one tall storey is an interpretation.',
     {'roofMaterial': 'iron', 'eavesHeight': 6.0}),
    (106983, 795, 'west-shed', 'west timber shed', 1, 'wood', 'Goad 702, coloured yellow (wood).', {}),
    (147151, 795, 'stable', 'stable', 1.5, 'brick', 'Goad "Stable" (700), marked 1 1/2.', {}),
    (344984, 795, 'pattern-store', 'pattern-making range', 2, 'brick', 'Goad "2 Pattern making &c" (698).', {}),
    (253598, 795, 'store', 'store', 2, 'brick', 'Goad "2 Store" (696).', {}),
    (117732, 795, 'east-stores', 'stores beside the railway', 2, 'brick', 'Goad "2 Stores" along the railway.', {}),
    (279662, 795, 'boundary-shed', 'boundary shed', 1, 'wood',
     'Narrow range on the boundary with the pottery; Goad draws it with crossed lines and no figure.', {}),
    (876230, 795, 'shed-west-a', 'small shed', 1, 'brick', 'Small range at 690; Goad figure 1.', {}),
    (867925, 795, 'shed-west-b', 'small shed', 1, 'brick', 'Small range at 690; Goad figure 1.', {}),
    # F. Brayne & Co. pottery
    (3054, 942, 'kiln-range', 'kiln range', 2, 'brick',
     'Goad 650-658, marked 2, enclosing four circles lettered "Kiln".', {}),
    (44276, 942, 'north-range', 'north range', 1, 'brick', 'Goad 660-662, pink with a grey (metal) part; figure read as 1.', {}),
    (35348, 942, 'stages', 'drying stages', 1.5, 'wood',
     'Goad "Stage" twice (664, 666), coloured yellow (wood); 1 1/2 storeys is an interpretation of a staged shed.', {}),
    (743908, 942, 'stable', 'stable', 1, 'brick', 'Goad "Stable" and "P" (668).', {}),
    (748025, 942, 'south-shed', 'south shed', 1, 'brick', 'Goad south range beside the tank works; figure read as 1.', {}),
    (152515, 942, 'south-range', 'south range', 2, 'brick', 'Goad 654, marked 2.', {}),
    (92148, 942, 'engine-house', 'engine house', 2, 'brick', 'Goad "(14 h.p.)" with a hatched boiler, marked 2 (650).', {}),
    (209877, 942, 'east-range', 'east range', 2, 'brick', 'Goad 648-650, marked 2.', {}),
    (175315, 942, 'east-shed', 'east timber shed', 1, 'wood', 'Goad 646, coloured yellow (wood).', {}),
    (746448, 942, 'dock-shed', 'shed by the dock', 1, 'wood', 'Goad 648, coloured yellow (wood).', {}),
    # J. B. Day engineer and the wheelwright
    (105524, 516, 'engineers-shop', "engineer's shop", 1, 'wood', 'Goad 550 "J. B. Day Engineer", coloured yellow (wood), marked 1.', {}),
    (598823, 516, 'iron-shed', 'iron shed', 1, 'metal', 'Goad 551, coloured grey (metal), with a round boiler or engine symbol.',
     {'roofMaterial': 'iron'}),
    (669680, 516, 'timber-shed', 'timber shed', 1, 'wood', 'Goad 560, coloured yellow (wood).', {}),
    (897393, 516, 'small-shed', 'small timber shed', 1, 'wood', 'Goad 556-558, coloured yellow (wood).', {}),
    (18667, 516, 'wheelwright', "wheelwright's shop", 1, 'brick', 'Goad 562 "Wheelwright", marked 1 (a separate occupier on the same yard).', {}),
    (53563, 516, 'wheelwright-south', "wheelwright's south range", 1, 'brick', 'Goad 564-568 beside the wheelwright, figure read as 1.', {}),
]

# Chimneys: (fid or None, site, key, height feet or None, reading)
CHIMNEYS = [
    (932473, 514, 'stack-514-engine', 60, '"60\'" printed beside the Goad chimney symbol east of the engine house'),
    (1014568, 795, 'stack-795-boiler', None, 'Goad chimney symbol at 662, no height printed'),
]
# Kilns read from Goad circles inside the kiln range (scene x, z, radius); positions read on the registered sheet.
KILNS = [(-656.8, 578.6), (-647.6, 577.4), (-636.8, 575.8), (-627.2, 573.8)]
KILN_RADIUS = 2.8


def build():
    fids = [b[0] for b in BUILDINGS] + [c[0] for c in CHIMNEYS]
    outlines = load_outlines(fids)
    buildings = []
    for fid, site, key, label, storeys, material, reading, extra in BUILDINGS:
        g = outlines[fid]
        b = {
            'id': f'b{site}-{key}', 'siteId': site, 'source': 'os-1893', 'name': f'{SITES[site][0]} — {label}',
            'material': material, 'roof': 'gable', 'storeysEstimate': storeys,
            'footprintSource': 'author-os-footprints-1891-96', 'sourceFids': [fid],
            'footprintEvidence': (f'Source outline fid {fid} ({g.area:.0f} m²) from the author\'s 1891–96 OS building GeoPackage, '
                                  'simplified at 0.15 m; checked against the cached NLS OS London five-foot mosaic (os-london-five-foot-1893) '
                                  'and the registered Goad sheet F16.'),
            'heightEvidence': (f'Storeys from {GOAD}: {reading} '
                               + ('Eaves height is an explicit estimate for a tall single-storey works shed.' if 'eavesHeight' in extra
                                  else 'Eaves height is the project default for that storey count (explicit estimate).')),
            'roofEvidence': ('Pitched roof is an interpretation; Goad and the OS draw no ridges.'
                             + (' Glazed alternate roof planes stand for the skylight bands Goad colours grey-blue.' if extra.get('roofGlazing') else '')
                             + (' Iron roof follows Goad\'s grey (metal building) colour.' if extra.get('roofMaterial') == 'iron' else '')),
            'functionEvidence': f'Use as lettered on Goad sheet F16: {reading}',
            'worldFootprint': ring(g),
        }
        b.update(extra)
        buildings.append(b)
    structures = []
    for fid, site, key, feet, reading in CHIMNEYS:
        c = outlines[fid]
        side = math.sqrt(c.area)
        s = {'id': key, 'siteId': site, 'source': 'os-1893', 'kind': 'chimney', 'name': f'{SITES[site][0]} chimney',
             'x': round(c.centroid.x, 3), 'z': round(c.centroid.y, 3),
             'radius': round(min(1.1, side*0.35), 2), 'section': 'square', 'material': 'brick', 'baseHeight': 0.34,
             'rotation': 0.0, 'sourceFootprintFid': fid, 'sourcePolygons': [[ring(c)]],
             'evidenceType': 'map-interpretation', 'supportingSources': ['author-os-footprints-1891-96', 'os-1893', 'goad-f16'],
             'symbolKey': 'goad-symbol-key-1926',
             'positionEvidence': f'Placed on the small square outline fid {fid} ({c.area:.1f} m²) where {reading.split(",")[0]}.',
             'profileEvidence': 'Square section follows the mapped base; taper, crown and brickwork are interpreted, not measured.'}
        if feet:
            s.update(height=round(feet*0.3048, 4), mappedHeightFeet=feet,
                     heightEvidence=f'{reading}, read as height in feet; converted at 0.3048 m/ft.')
        else:
            s.update(height=22.0, heightEvidence=f'{reading}; 22 m is the project’s typological estimate for an unmeasured works boiler stack.')
        structures.append(s)
    kiln_range = Polygon(next(b['worldFootprint'] for b in buildings if b['id'] == 'b942-kiln-range'))
    for i, (x, z) in enumerate(KILNS, 1):
        assert kiln_range.contains(Point(x, z).buffer(KILN_RADIUS)), ('kiln outside its range', i)
        structures.append({
            'id': f'kiln-942-{i}', 'siteId': 942, 'source': 'os-1893', 'kind': 'kiln', 'x': x, 'z': z,
            'radius': KILN_RADIUS, 'height': 13.0,
            'evidence': f'Kiln {i} of the four circles lettered "Kiln" inside the kiln range on {GOAD}.',
            'positionEvidence': 'Circle centre read on the registered Goad sheet (median registration misfit 1.0 m); the OS and the GeoPackage draw the range, not the kilns.',
            'radiusEvidence': 'Goad circle diameter about 5.6 m.',
            'heightEvidence': ('Explicit estimate: 13 m, enough for a bottle kiln to rise well above a two-storey range; no height is '
                               'printed and no photograph of this pottery is in the repository.'),
            'geometryEvidence': 'Drawn with the renderer’s simple cylindrical kiln; a bottle-shaped hovel would be more faithful.',
            'supportingSources': ['goad-f16'], 'evidenceType': 'map-interpretation'})
    register = {
        'schemaVersion': 1, 'date': '2026-10-04', 'sites': list(SITES), 'name': 'Works between Imperial Street and the LT&SR, Bromley',
        'source': ("Author-supplied london_buildings_1891-96_corr_v1.gpkg (project extract west-ham-buffer-buildings-bng.geojson.gz); "
                   f"cached NLS OS London five-foot mosaic (os-london-five-foot-1893); {GOAD}, registered as in "
                   "berger-starch-footprint-alignment.json"),
        'sourceCRS': 'EPSG:27700 to scene origin E538900,N183209; x east, z south, metres',
        'method': ('4 October 2026: first models for sites 514, 795, 942 and 516 (previously excluded as outside the western riverside '
                   'corridor; 514 and 942 were drawn as interpreted placeholder ranges). One building per GeoPackage outline; Goad F16 '
                   'supplies names, uses, storeys, construction colours, skylights, boilers, chimneys and kilns '
                   '(see scripts/prepare_imperial_street_works_alignment.py).'),
        'evidenceNotes': [
            'Goad colours read with the key (reference/factory-building-survey/goad-symbol-key-1926.jpg): pink brick, yellow wood, '
            'grey metal buildings, grey-blue skylights; figures are storeys; feet are printed beside chimney symbols.',
            'Outlines under 10 m² (privies, flues, bins) are not modelled.',
        ],
        'buildings': [], 'structures': [], 'groups': [],
        'additionalSites': [{'id': sid, 'name': name, 'sources': ['os-1893'],
                             'coverage': 'Individual OS-mapped ranges; uses, storeys and construction from Goad sheet F16',
                             'notes': note + ' Roof exteriors are mapped; heights and roof forms are estimates.'}
                            for sid, (name, note) in SITES.items()],
        'additionalBuildings': buildings,
        'additionalStructures': structures,
    }
    OUT.write_text(json.dumps(register, indent=2, ensure_ascii=False)+'\n')
    return register


if __name__ == '__main__':
    r = build()
    print(len(r['additionalBuildings']), 'buildings,', len(r['additionalStructures']), 'structures')
