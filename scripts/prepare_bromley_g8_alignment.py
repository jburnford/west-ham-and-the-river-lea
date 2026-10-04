"""Prepare the register for R. Bell & Co.'s match and taper factory (site 475, GIS "Match Manufactory") on the Limehouse Cut,
from GeoPackage outlines and Goad's London East vol. G sheet 8 (part 1, February 1894).

Writes data/maps/bromley-g8-footprint-alignment.json.
"""
from pathlib import Path

from goad_site_register import make_register

ROOT = Path(__file__).resolve().parents[1]
SHEET = 'goad-g8-1'
NOTE = ('Goad Insurance Plan of London, East vol. G sheet 8 (part 1), dated February 1894, 40 ft to the inch '
        '(reference/factory-building-survey/goad-g8-1.tiff)')

SITES = {
    475: ('R. Bell & Co. match and taper factory',
          'Named "Match Manufactory" on the OS five-foot plan and "R. Bell & Co. Limd., Match & Taper Fac." on Goad G8 (February 1894), '
          'between the North London Railway\'s Bow Works ground and the Limehouse Cut.'),
}

B = [
    (861, 475, 'dipping-drying-range', 'dipping and drying range', 3, 'brick',
     'Goad long west range: "Cotton wax & glue", "3 store, bast., offs. 1st" and five "Dipping & drying" rooms with "Corr. iron & wood 3rd" '
     'floors and wax rooms; three storeys and basement.', {'clipBox': [-960, -910, 1058, 1151]}),
    (861, 475, 'dipping-range-south', 'south end of the dipping range', 2, 'brick',
     'Goad "2 & B. All walls & all floors conc." at the south end of the range, with tanks on the roof.', {'clipBox': [-960, -910, 1151, 1175]}),
    (8873, 475, 'mess-room-store', 'mess room and store', 2, 'brick',
     'Goad "Mess room", "Store", "Conc. walls, iron roof, wooden floor"; an upper wooden floor read as two storeys.', {'roofMaterial': 'iron'}),
    (55488, 475, 'range-528', 'range 528', 2, 'brick', 'Goad 528 with tin-clad doors; figure read as 2.', {}),
    (56213, 475, 'despatch', 'despatch department', 2, 'brick', 'Goad "Despatch dept., concrete walls" (530), marked 2.', {}),
    (50709, 475, 'engineering', 'engineering shop', 1.5, 'brick', 'Goad "Engineering" (532), marked 1-2, with a grey-blue skylight.',
     {'roofGlazing': True}),
    (57214, 475, 'match-store', 'match store', 1, 'brick', 'Goad "Match store, concrete walls" (534).', {}),
    (60051, 475, 'varnishing-room', 'varnishing room', 1, 'brick', 'Goad "Varnishing room" with two stoves (536).', {}),
    (402645, 475, 'crystallising-smithy', 'crystallising room and smithy', 1, 'wood',
     'Goad "Crystallising, wood & metal" (yellow) and "Smithy" (537-538).', {}),
    (39344, 475, 'carpenters-shop', "carpenter's shop over skillets and labels", 2, 'brick',
     'Goad "Carp. 2nd" over "Skillets & labels 1st" with a grey-blue skylight (524-526).', {'roofGlazing': True}),
    (125967, 475, 'range-524', 'range 524', 2, 'brick', 'Goad 524, marked 2.', {}),
    (150356, 475, 'range-522', 'range 522', 2, 'brick', 'Goad 522, marked 2.', {}),
    (7763, 475, 'saw-mill', 'saw mill and wood drying rooms', 1, 'brick',
     'Goad "Saw mill, conc. walls" with "Wood drying rooms" along its west side, one storey, and a skylight strip.', {'roofGlazing': True}),
    (150974, 475, 'mechanics-shop', "mechanics' shop and engine", 1, 'brick', 'Goad "Mechanics shop" with a 28 h.p. engine.', {}),
    (590975, 475, 'match-box-shed', 'match-box shed', 1, 'wood', 'Goad "Match boxes", coloured yellow (wood).', {}),
    (919865, 475, 'cut-shed', 'shed on the Limehouse Cut', 1, 'brick', 'Goad 516 by the Limehouse Cut wall.', {}),
    (811628, 475, 'cut-shed-south', 'shed on the Limehouse Cut', 1, 'brick', 'Goad 516 by the Limehouse Cut wall.', {}),
    (665473, 475, 'boiler-house', 'boiler house', 1, 'brick', 'Goad hatched boiler with "Iron chy. 20\' over" (510).', {}),
]

if __name__ == '__main__':
    r = make_register(
        ROOT/'data/maps/bromley-g8-footprint-alignment.json', sheet=SHEET, sheet_note=NOTE, date='2026-10-04',
        name='R. Bell & Co. match and taper factory', sites=SITES, buildings=B,
        method=('4 October 2026: first models for site 475 (previously excluded as outside the western riverside corridor). One building per '
                'GeoPackage outline, the long dipping range divided where Goad changes its storey figure; Goad G8 (February 1894) supplies '
                'names, uses, storeys and construction (see scripts/prepare_bromley_g8_alignment.py).'),
        notes=['Goad G8 part 1 is registered from G9 across their shared edge (Four Mills Bridge) and refined by the building-colour fit '
               '(about 0.4 m on its one matching window; treat as about 1 m).',
               'Goad draws a range "Conc. walls & iron roof, under cons. Feb. 1894" north of the factory; it has no 1891-96 GeoPackage '
               'outline and is not modelled.',
               'The boiler has an iron chimney "20\' over" the roof rather than a brick stack; it is not drawn.'])
    print(len(r['additionalBuildings']), 'buildings,', len(r['additionalStructures']), 'structures')
