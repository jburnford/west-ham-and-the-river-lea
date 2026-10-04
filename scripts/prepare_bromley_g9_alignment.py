"""Prepare the register for Four Mills Distillery (site 417) and Sun Flour Mills (site 418, GIS "Bromley Mills (Flour)"),
from GeoPackage outlines and Goad's London East vol. G sheet 9 (February 1894).

Writes data/maps/bromley-g9-footprint-alignment.json.
"""
from pathlib import Path

from goad_site_register import make_register

ROOT = Path(__file__).resolve().parents[1]
SHEET = 'goad-g9-1'
NOTE = ('Goad Insurance Plan of London, East vol. G sheet 9 (part 1), dated February 1894, 40 ft to the inch '
        '(reference/factory-building-survey/goad-g9-1.tiff)')

SITES = {
    417: ('Four Mills Distillery',
          'Named "Four Mills Distillery" on the OS five-foot plan and "Four Mills Distillery (silent)" on Goad G9 (February 1894): '
          'the distillery was not working when surveyed. Granaries, mill, malting floors with kilns, brew house, still house, '
          'spirit stores and backhouses are lettered.'),
    418: ('Sun Flour Mills',
          'Named "Sun Mills (Corn)" on the OS five-foot plan, "Bromley Mills (Flour)" in the GIS site layer and "Sun Flour Mills" on '
          'Goad G9, on the island between the Limehouse Cut and the Lea.'),
}

B = [
    # Four Mills Distillery
    (1799, 417, 'granaries-2-3', 'granaries 2 and 3 (formerly spirit store)', 4, 'brick',
     'Goad "Granaries 3 . 2" marked "2, 3 & 4th" and "Formerly spirit store 1st"; four floors.', {}),
    (6305, 417, 'granary-1', 'granary 1', 4, 'brick', 'Goad "Granaries 1" marked "2, 3 & 4th"; four floors.', {}),
    (3386, 417, 'malting-floors', 'malting floors, malt store and kilns', 3, 'brick',
     'Goad "Malting floors" marked 3 and "Malt store 2nd" over a row of five kilns (four brick cones, one slate-clad cone).', {}),
    (6640, 417, 'mill', 'mill', 4, 'brick', 'Goad "Mill" marked 4.', {}),
    (2627, 417, 'brew-house', 'brew house and underback room', 3, 'brick',
     'Goad "Brew house" and "Underback room", marked 1-3 and 2-3, with "iron, wood & slate roof".', {}),
    (74560, 417, 'engine-room-2-stores', 'engine room no. 2 and stores', 2.5, 'brick', 'Goad "Eng. room No. 2" and "Stores", marked 2-3.', {}),
    (115247, 417, 'engine-room-1', 'engine room no. 1', 2, 'brick', 'Goad "Eng. room No. 1, conc. roof" beside the boilers.', {}),
    (41772, 417, 'grain-tanks', 'iron grain tanks', 2, 'metal', 'Goad "Iron grain tanks 50\' over", coloured grey (metal); the tanks stand on a frame.',
     {'roofMaterial': 'iron'}),
    (353957, 417, 'spirit-store-meter', 'methylated spirit store and meter house', 1, 'brick', 'Goad "Meth. spirit store" and "Meter house".', {}),
    (3031, 417, 'bonded-warehouse', 'formerly bonded warehouse and spirit store', 2, 'brick',
     'Goad "Formerly bonded whse." and "Spirit store", each marked "1-2 & B" (one and two storeys with basement).',
     {'clipBox': [-750, -718, 1100, 1128]}),
    (3031, 417, 'still-house', 'still house', 3, 'brick', 'Goad "Still house", marked 1-3.', {'clipBox': [-750, -718, 1128, 1149]}),
    (19168, 417, 'boiler-house', 'boiler house', 1, 'brick', 'Goad hatched steam boilers under grey-blue skylights.', {'roofGlazing': True}),
    (45871, 417, 'engine-room-3-offices', 'engine room no. 3 and offices', 2, 'brick', 'Goad "Eng. room No. 3, conc. roof" and "Offs.", marked 2.', {}),
    (3754, 417, 'backhouse-north', 'backhouse', 2, 'brick', 'Goad "Backhouse", marked 2.', {}),
    (43106, 417, 'backhouse-south-west', 'south backhouse', 2, 'brick', 'Goad "Backhouse", marked 2.', {}),
    (47930, 417, 'backhouse-south-east', 'south backhouse', 2, 'brick', 'Goad "Backhouse", marked 2.', {}),
    (31539, 417, 'charger-house', 'charger house', 2, 'brick', 'Goad "Charger house", marked 2.', {}),
    (21630, 417, 'stables', 'stables', 1, 'brick', 'Goad "Stables" with a yellow (wood) range along one side; one storey read.', {}),
    (206348, 417, 'pump-room', 'pump room', 1, 'brick', 'Goad "Pump room" by the wash pit.', {}),
    (647715, 417, 'charger-room', 'charger room', 1, 'brick', 'Goad "Charger room".', {}),
    # Sun Flour Mills
    (13577, 418, 'grain-silos', 'grain silos', 2.5, 'brick',
     'Goad "Grain silos, solid wood construction, iron bottoms forming ceiling of ground floor", marked 2 1/2.', {'clipBox': [-708, -694.5, 984, 1004]}),
    (13577, 418, 'flour-warehouse-3', 'flour warehouse 3', 4, 'brick', 'Goad "(3) Flour whse." with "4th" floor marks.',
     {'clipBox': [-694.5, -686, 984, 1004]}),
    (12693, 418, 'flour-warehouse-2', 'flour warehouse 2 and wheat cleaning', 4.5, 'brick',
     'Goad "(2) Flour whse.", marked 4 1/2, with "Wheat cleaning" at its south end.', {}),
    (59940, 418, 'mill-1', 'mill (15 sets of rollers)', 4.5, 'brick', 'Goad "(1) Mill (15 sets rollers)", marked 4 1/2.', {}),
    (16094, 418, 'boilers-offices', 'boiler house, coal store and offices', 1.5, 'brick',
     'Goad hatched boilers and "Coals" (one storey) with offices and a cyclone room marked 2 at the north-east corner.', {}),
    (395799, 418, 'cyclone-room', 'cyclone room', 1, 'brick', 'Goad "Cyclone room" beside the boilers.', {}),
    (522192, 418, 'bag-room', 'bag room', 1, 'brick', 'Goad "Bag room", marked 1.', {}),
    (456957, 418, 'dwelling', 'dwelling', 2, 'brick', 'Goad "D." (dwelling) at 504, marked 2.', {}),
    (609259, 418, 'office', 'office', 2, 'brick', 'Goad "Off. 1st" at 506.', {}),
    (195530, 418, 'north-shed-a', 'north shed', 1, 'brick', 'Goad range at 500-502 north of the mill.', {}),
    (215121, 418, 'north-shed-b', 'north shed', 1, 'brick', 'Goad range at 500-502 north of the mill.', {}),
    (253707, 418, 'north-shed-c', 'north shed', 1, 'brick', 'Goad range at 500-502 north of the mill.', {}),
]
CHIMNEYS = [
    (880792, 417, 'stack-417-140ft', 140,
     'Goad prints an octagonal chimney symbol marked "140\'" between the still house and the backhouse (drawn round: the renderer has no octagon)',
     'round'),
]
KILNS = [
    (417, 'kiln-417-1', -735.0, 1027.2, 2.9, 16.0, 'First of four circles lettered "Kilns, brick cones" under the malt store'),
    (417, 'kiln-417-2', -728.6, 1026.8, 2.9, 16.0, 'Second of four circles lettered "Kilns, brick cones"'),
    (417, 'kiln-417-3', -722.2, 1026.4, 2.9, 16.0, 'Third of four circles lettered "Kilns, brick cones"'),
    (417, 'kiln-417-4', -715.4, 1025.8, 2.9, 16.0, 'Fourth of four circles lettered "Kilns, brick cones"'),
    (417, 'kiln-417-5', -707.4, 1025.0, 2.9, 16.0, 'Circle lettered "Kiln, slate clad cone"'),
]

if __name__ == '__main__':
    r = make_register(
        ROOT/'data/maps/bromley-g9-footprint-alignment.json', sheet=SHEET, sheet_note=NOTE, date='2026-10-04',
        name='Four Mills Distillery and Sun Flour Mills', sites=SITES, buildings=B, chimneys=CHIMNEYS, kilns=KILNS,
        method=('4 October 2026: first models for sites 417 and 418 (previously excluded as outside the western riverside corridor). '
                'One building per GeoPackage outline, two outlines divided on walls Goad draws; Goad G9 (February 1894) supplies names, '
                'uses, storeys, construction, the 140 ft chimney and the malting kilns (see scripts/prepare_bromley_g9_alignment.py).'),
        notes=['Goad G9 part 1 is registered to the GeoPackage by the building-colour fit described in berger-starch-footprint-alignment.json '
               '(median local misfit 0.5 m on two windows).',
               'The distillery is marked "silent" (not working) in February 1894; the model shows the buildings, not their use.'])
    print(len(r['additionalBuildings']), 'buildings,', len(r['additionalStructures']), 'structures')
