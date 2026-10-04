"""Prepare the register for the Safety Oil Wharf petroleum store at Bromley (new site 9010), on the Lea south of Three Mills,
from GeoPackage outlines and Goad's vol. F sheet 16 (July 1893). The GIS industry layer has no parcel here.

Writes data/maps/safety-oil-wharf-footprint-alignment.json.
"""
from pathlib import Path

from goad_site_register import make_register

ROOT = Path(__file__).resolve().parents[1]
NOTE = ('Goad Insurance Plan of London, North East District vol. F sheet 16, July 1893 '
        '(reference/factory-building-survey/goad-f16.tiff)')

SITES = {
    9010: ('Safety Oil Wharf, Bromley (petroleum store)',
           'Lettered "Safety Oil Wharf, Bromley" with "Petroleum in barrels" and "Empty barrels" on Goad F16 (block 644); the OS draws the '
           'building without a name and the GIS industry layer has no site here.'),
}
B = [
    (739, 9010, 'petroleum-store', 'petroleum store', 1, 'brick',
     'Goad 644 "Safety ... Bromley ... Petroleum in barrels", pink (brick), marked 1, with an internal division wall.',
     {'eavesHeight': 4.5}),
    (44482, 9010, 'van-shed', 'van shed', 1, 'brick', 'Goad 642 "Van shed", marked 1.', {}),
]

if __name__ == '__main__':
    r = make_register(
        ROOT/'data/maps/safety-oil-wharf-footprint-alignment.json', sheet='goad-f16', sheet_note=NOTE, date='2026-10-04',
        name='Safety Oil Wharf, Bromley', sites=SITES, buildings=B,
        method=('4 October 2026: the 1,775 m² outline south of Three Mills was drawn only as a flat plan; Goad F16 identifies it as a '
                'petroleum store. New site 9010 (no GIS parcel), two buildings on their GeoPackage outlines '
                '(see scripts/prepare_safety_oil_wharf_alignment.py).'),
        notes=['Barrel stacks on the open ground ("Empty barrels") are not modelled.'])
    print(len(r['additionalBuildings']), 'buildings')
