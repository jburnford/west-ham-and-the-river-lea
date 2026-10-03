#!/usr/bin/env python3
"""Audit downloaded PLA peaks against raw spreadsheets and compare NRFA flows.

Inputs remain unmodified. Outputs are research constraints, not Three Mills
survey heights or a continuous flood hydrograph.
"""
import csv
import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reference/topography-research-2026-09-28/flood-evidence'
BODC = OUT / 'bodc'
EVENTS = ['1897-11-29', '1898-10-29', '1904-12-30', '1928-01-07']
STATIONS = [
    ('4_Southend.txt', 'Southend', 6, 18, 3.3726),
    ('6_Tilbury.txt', 'Gravesend (Tilbury Dock)', 7, 10, 3.475),
    ('7-8_Silvertown.txt', 'Gallions Pier (Albert Dock)', 7, 10, 3.475),
    ('10-11_London_Bridge.txt', 'Old Swan Pier', 7, 10, 3.459),
]


def main():
    sheet = openpyxl.load_workbook(BODC/'1928_AllSites.xlsx', data_only=True)['01']
    raw_rows = {}
    day = None
    for number, row in enumerate(sheet.iter_rows(min_row=5, values_only=True), 5):
        if isinstance(row[0], (int, float)):
            day = int(row[0])
        if day is not None and row[1]:
            raw_rows[(day, row[1])] = (number, row)
    peaks = []
    window = []
    for filename, name, day, col, offset in STATIONS:
        rows = []
        with (BODC/filename).open() as f:
            next(f)
            for number, row in enumerate(csv.reader(f), 2):
                when = datetime.strptime(row[0], '%d/%m/%Y %H:%M:%S')
                if datetime(1928, 1, 5) <= when < datetime(1928, 1, 10):
                    entry = {'station': name, 'timeAsPublished': when.isoformat(),
                             'heightODNMetres': float(row[1]), 'highWater': int(row[2]) == 1,
                             'file': filename, 'line': number}
                    window.append(entry)
                    if datetime(1928, 1, 6, 18) <= when < datetime(1928, 1, 7, 6) and entry['highWater']:
                        rows.append(entry)
        peak = max(rows, key=lambda r: r['heightODNMetres'])
        number, raw = raw_rows[(day, name)]
        feet = raw[col] + raw[col+1]/12
        # Reproduce the authors' feet conversion (3.281 feet per metre).
        # Offsets are station-specific, not a universal Trinity correction.
        calculated = feet/3.281 + offset
        assert abs(calculated-peak['heightODNMetres']) < .00011, (name, calculated, peak)
        hour = raw[col+2] % 12 + (12 if col == 18 else 0)
        raw_time = datetime(1928, 1, day, hour, raw[col+3])
        assert raw_time.isoformat() == peak['timeAsPublished']
        peaks.append({**peak, 'rawSpreadsheetRow': number, 'rawSheet': '01',
                      'rawHeightAboveTHWFeet': feet, 'conversionOffsetMetres': offset,
                      'offsetEvidence': 'Inayatillah et al. Table 3 (https://www.nature.com/articles/s41597-022-01223-7/tables/4); London Bridge also checked against master1.m',
                      'rawPeakChecked': True, 'threeMillsHeightODNMetres': None})
    flows = []
    for station in ['38001', '39001']:
        for kind in ['gdf', 'ndf']:
            filename = f'{station}-{kind}.json'
            data = json.loads((OUT/filename).read_text())
            assert data['station']['id'] == int(station)
            assert data['data-type']['units'] == 'm3/s'
            stream = data['data-stream']
            lookup = dict(zip(stream[::2], stream[1::2]))
            for event in EVENTS:
                date = datetime.fromisoformat(event)
                nearby = [{'date': (date+timedelta(days=i)).date().isoformat(),
                           'flowM3PerSecond': lookup.get((date+timedelta(days=i)).date().isoformat())}
                          for i in range(-14, 15)]
                flows.append({'station': int(station), 'series': kind, 'event': event,
                              'eventDayMeanM3PerSecond': lookup[event], 'window': nearby,
                              'sourceFile': filename})
    inputs = [BODC/'1928_AllSites.xlsx'] + [BODC/s[0] for s in STATIONS]
    inputs += list(OUT.glob('*-?df.json')) + [OUT/'station-info.json']
    report = {'status': 'PASS', 'sources': {
        'tides': 'https://doi.org/10.5285/b66afb2c-cd53-7de9-e053-6c86abc0d251',
        'conversionCode': 'https://github.com/ivanhaigh/Thames-Sea-Level-Data',
        'flows': 'https://nrfaapps.ceh.ac.uk/nrfa/nrfa-api.html'},
        'acknowledgement': 'Data from the UK National River Flow Archive; PLA tide data digitised by Haigh et al. (2021), NERC EDS BODC NOC.',
        'inputSHA256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
        'peaks1928': peaks, 'publishedTideWindow': window, 'dailyFlows': flows,
        'limitations': [
            'Published decimal places do not imply millimetre historical accuracy.',
            'Some published noon records roll into the next date: 6 January 12:42 PM Old Swan becomes 7 January 00:42; 12:20 PM Gallions similarly becomes 00:20. Peak rows checked separately. Do not interpolate the unreviewed series into a hydrograph.',
            'THW offsets retained from published series/code; no remote gauge level assigned to Three Mills.',
            'Daily means are not instantaneous flood peaks; naturalised flows are adjusted estimates, not observed historical discharge.',
            'Feildes Weir early readings affected by sluices and mills; until 1931 daily flows derived from three lock-keeper readings. Kingston historical series derived from Teddington, with limited early accuracy.',
            'These flow values do not identify a surge without tide predictions and observations.'
        ]}
    (OUT/'event-comparison.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'status': report['status'], 'peaks1928': peaks,
                      'eventFlows': [{k:v for k,v in r.items() if k!='window'} for r in flows]}, indent=2))


if __name__ == '__main__':
    main()
