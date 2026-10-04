"""Prepare the register for Jukes, Coulson, Stokes & Co.'s St Leonard's Works (site 794) and H. B. Walmsley & Sons'
Bromley Maltings (site 229), from GeoPackage outlines and Goad's London East vol. G sheet 10 (February 1894).

Writes data/maps/bromley-g10-footprint-alignment.json.
"""
from pathlib import Path

from goad_site_register import make_register

ROOT = Path(__file__).resolve().parents[1]
SHEET = 'goad-g10'
NOTE = ('Goad Insurance Plan of London, East vol. G sheet 10, dated February 1894, 40 ft to the inch '
        '(reference/factory-building-survey/goad-g10.tiff)')

SITES = {
    794: ("Jukes, Coulson, Stokes & Co. St Leonard's Works",
          'Named "St. Leonard\'s Works (Iron)" on the OS five-foot plan and "Jukes, Coulson, Stokes & Co., Engineers, St Leonards '
          'Works" on Goad G10 (February 1894).'),
    229: ('H. B. Walmsley & Sons Bromley Maltings',
          'Named "Bromley Maltings" on the OS five-foot plan and "H. B. Walmsley & Sons, Bromley Maltings" on Goad G10 '
          '(February 1894), with five numbered malting-floor blocks and brick-cone kilns.'),
}

B = [
    # St Leonard's Works
    (4165, 794, 'north-range', 'north range and fitting shop', 1.5, 'metal',
     'Goad "Fitting shop" and the storage range along the railway, coloured grey (metal), marked 1 and 1=2.',
     {'roofMaterial': 'iron'}),
    (4373, 794, 'smithy', 'smithy', 1, 'brick', 'Goad "Smithy", pink with a long grey-blue skylight, marked 1.',
     {'roofGlazing': True, 'eavesHeight': 5.0}),
    (8829, 794, 'furnace-range', 'furnace range', 1, 'metal', 'Goad grey (metal) range with "Furnaces" either side of the chimney, marked 1.',
     {'roofMaterial': 'iron'}),
    (493848, 794, 'boiler-house', 'boiler house with tank over', 2, 'brick', 'Goad hatched boiler "(25 h.p.)" with "Tank over".', {}),
    (36498, 794, 'hardware-store-north', 'hardware storage (skylit)', 1.5, 'brick',
     'Goad "Hardware storage" with a grey-blue skylight, marked 1=2.', {'roofGlazing': True}),
    (47726, 794, 'hardware-store-south', 'hardware storage', 1.5, 'brick', 'Goad "Hardware storage", marked 1=2.', {}),
    (40493, 794, 'offices', 'offices and stores', 3, 'brick', 'Goad "Off., Stores &c", marked 3 & B (three storeys and basement).', {}),
    (748957, 794, 'north-east-shed', 'north-east shed', 1, 'wood', 'Goad yellow (wood) and grey shed at 514, marked 1.', {}),
    (55640, 794, 'carpenters-store', "carpenter's shop and storage", 2, 'brick', 'Goad "Carp. 2nd" over storage (518-520).', {}),
    (436425, 794, 'riverside-range', 'riverside range', 1, 'brick', 'Goad 516 by the river wall, marked 1.', {}),
    # Bromley Maltings
    (1125, 229, 'malting-1-2', 'malting floors 1 and 2 with west kilns and firing rooms', 4, 'brick',
     'Goad "(1&2) Malting floors" with "4th" floor marks and a "4" figure; firing rooms and kilns ("Bk. cone", "slate clad pyramid") at the north-west end.', {}),
    (6311, 229, 'malting-3', 'malting floors 3', 3, 'brick', 'Goad "(3) Malting floors", marked 3 & B and 2 & B.', {}),
    (6647, 229, 'malting-4', 'malting floors 4', 4, 'brick', 'Goad "(4) Malting floors" with "4th" floor marks.', {}),
    (5678, 229, 'malting-5', 'malting floors 5', 3.5, 'brick', 'Goad "(5) Malting floors", marked 3 1/2.', {}),
    (24364, 229, 'malt-store-kilns', 'malt store, firing room and kilns', 2, 'brick',
     'Goad "Malt store", "Firing 1st" and three "Kilns, brick cones", marked 2.', {}),
    (254293, 229, 'iron-roof-yard', 'iron roof over yard', 1, 'metal', 'Goad "Iron roof over yard".', {'roofMaterial': 'iron'}),
    (493395, 229, 'south-kilns-west', 'south kiln house', 2, 'brick', 'Goad "Kilns, brick cones" (614).', {}),
    (186409, 229, 'south-kilns-east', 'south kiln house', 2, 'brick', 'Goad "Kilns, brick cones" (612).', {}),
    (763811, 229, 'south-kilns-middle', 'south kiln house', 2, 'brick', 'Goad kiln house between the two south brick cones.', {}),
    (9630, 229, 'grain-store', 'grain store and grain cleaning', 2, 'brick',
     'Goad "Grain store" and "(6) Grain cleaning"; no storey figure legible, 2 is an explicit estimate. Outside the GIS site parcel but '
     'part of Walmsley\'s premises on Goad.', {}),
    (248431, 229, 'south-range', 'range north of the grain store', 1, 'brick', 'Goad 610, marked 1.', {}),
    (777657, 229, 'cut-shed-a', 'shed on the Limehouse Cut', 1, 'wood', 'Goad yellow (wood) range on the Limehouse Cut wharf (642).', {}),
    (819591, 229, 'cut-shed-b', 'shed on the Limehouse Cut', 1, 'wood', 'Goad yellow (wood) range on the Limehouse Cut wharf (642).', {}),
    (897699, 229, 'cut-shed-c', 'shed on the Limehouse Cut', 1, 'wood', 'Goad yellow (wood) range on the Limehouse Cut wharf.', {}),
]
CHIMNEYS = [(1013609, 794, 'stack-794-furnaces', 80, 'Goad prints a chimney symbol marked "80" between the two furnace houses')]
KILNS = [
    (229, 'kiln-229-628', -723.6, 875.2, 2.4, 16.0, 'Kiln 628, a circle lettered "Kiln, Bk. cone"'),
    (229, 'kiln-229-639', -698.4, 845.6, 2.4, 14.0, 'Kiln 639, one of three circles lettered "Kilns, brick cones"'),
    (229, 'kiln-229-638', -697.2, 852.4, 2.4, 14.0, 'Kiln 638, one of three circles lettered "Kilns, brick cones"'),
    (229, 'kiln-229-637', -698.8, 858.8, 2.4, 14.0, 'Kiln 637, one of three circles lettered "Kilns, brick cones"'),
    (229, 'kiln-229-622', -677.6, 877.2, 2.6, 15.0, 'Kiln 622, a circle lettered "Kilns, brick cones"'),
    (229, 'kiln-229-620', -670.0, 874.8, 2.6, 15.0, 'Kiln 620, a circle lettered "Kilns, brick cones"'),
    (229, 'kiln-229-614', -692.0, 904.8, 2.8, 12.0, 'South kiln 614, a circle lettered "Kilns, brick cones"'),
    (229, 'kiln-229-612', -684.4, 904.4, 2.8, 12.0, 'South kiln 612, a circle lettered "Kilns, brick cones"'),
]

if __name__ == '__main__':
    r = make_register(
        ROOT/'data/maps/bromley-g10-footprint-alignment.json', sheet=SHEET, sheet_note=NOTE, date='2026-10-04',
        name="St Leonard's Works and Bromley Maltings", sites=SITES, buildings=B, chimneys=CHIMNEYS, kilns=KILNS,
        method=('4 October 2026: first models for sites 794 and 229 (previously excluded as outside the western riverside corridor). '
                'One building per GeoPackage outline; Goad G10 (February 1894, a year later than the OS revision) supplies names, '
                'uses, storeys, construction colours, skylights, boilers, the 80 ft chimney and the malting kilns '
                '(see scripts/prepare_bromley_g10_alignment.py).'),
        notes=['Goad G10 is registered to the GeoPackage by the building-colour fit described in berger-starch-footprint-alignment.json '
               '(median local misfit 0.5 m on three windows).',
               'Square slate-clad pyramid kilns at the maltings are inside the malting ranges and are not drawn separately.'])
    print(len(r['additionalBuildings']), 'buildings,', len(r['additionalStructures']), 'structures')
