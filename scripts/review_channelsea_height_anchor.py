#!/usr/bin/env python3
"""Compare historic sewer controls with OS legacy marks and dated EA terrain.

Research outputs only: never edits height observations or scene geometry.
Requires the two OS downloads in the output directory; unzip supports their
Deflate64 archive, which Python's zipfile reader does not support.
"""
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import zipfile

os.environ.setdefault('MPLCONFIGDIR', '/tmp/channelsea-anchor-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / 'reference/topography-research-2026-09-28'
OUT = RESEARCH / 'channelsea-height-anchor'
IDS = ['sh_538859_183220', 'sh_539019_183171', 'sh_539092_183155',
       'sh_538854_183190']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    source = ROOT / 'reference/spot-heights/heights.geojson'
    snapshot = source.read_bytes()
    by_id = {f['properties']['id']: f['properties']
             for f in json.loads(snapshot)['features']}
    with (OUT / 'LiverpoolToNewlyn.csv').open(encoding='utf-8-sig', newline='') as f:
        offsets = {r['gridsquare']: r for r in csv.DictReader(f)}
    archive = OUT / 'CompleteBenchMarkArchive.zip'
    raw = subprocess.check_output(['unzip', '-p', str(archive),
                                   'CompleteBenchMarkArchive.csv'])
    nearby = []
    for row in csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))):
        if row['NG LETTERS'] != 'TQ':
            continue
        e, n = 500000 + float(row['EASTING'])*10, 100000 + float(row['NORTHING'])*10
        if np.hypot(e-538900, n-183209) <= 450:
            nearby.append({'bng_e': e, 'bng_n': n, 'archiveRecord': row})

    tile_name = 'DTM_V0027976_20030222_20030222.tif'
    with zipfile.ZipFile(RESEARCH / 'tiles-2003/TQ3580.zip') as z:
        tile_bytes = z.read(tile_name)
    im = Image.open(io.BytesIO(tile_bytes))
    pixel = im.tag_v2[33550][0]
    left, top = im.tag_v2[33922][3:5]
    assert pixel == 1 and im.size == (2000, 2000)
    native = np.array(im, dtype=float)
    native[(native < -100) | (native > 300)] = np.nan
    modern = Image.open(RESEARCH / 'west-ham-buffer-modern-dtm-10m.tif')
    modern_a = np.array(modern)
    meta = json.loads((RESEARCH / 'early-terrain-2003-10m.json').read_text())
    west, south, east, north = meta['boundsBNG']
    assert modern.size == (meta['width'], meta['height'])
    controls = []
    for key in IDS:
        p = dict(by_id[key])
        e, n = p['bng_e'], p['bng_n']
        square = f'TQ{int((e-500000)//1000):02d}{int((n-100000)//1000):02d}'
        correction = float(offsets[square]['height'])
        converted = (p['value_ft'] + correction)*0.3048
        r, c = int((top-n)//pixel), int((e-left)//pixel)
        window = native[r-3:r+4, c-3:c+4]
        mr, mc = int((north-n)//10), int((e-west)//10)
        samples = {'native2003Cell_m': float(native[r, c]),
                   'native2003_7x7m_minMedianMax_m': np.nanpercentile(window, [0, 50, 100]).tolist(),
                   'modern10mCell_m': float(modern_a[mr, mc])}
        controls.append({'sourceRecord': p, 'osCorrectionRecord': offsets[square],
                         'conditionalHeightODN_m': round(converted, 6),
                         'terrainSamples': samples,
                         'terrainComparisonApplicable': p['type'] == 'spot',
                         'native2003CellMinusHistoric_m': round(float(native[r, c])-converted, 6)
                         if p['type'] == 'spot' else None})
    old_bm = controls[-1]
    p = old_bm['sourceRecord']
    closest = min(nearby, key=lambda b: np.hypot(b['bng_e']-p['bng_e'], b['bng_n']-p['bng_n']))
    assert closest['archiveRecord']['DATUM'] == 'N'
    candidate = {'historicId': p['id'], 'archive': closest,
                 'separation_m': float(np.hypot(closest['bng_e']-p['bng_e'], closest['bng_n']-p['bng_n'])),
                 'archiveMinusHistoric_m': round(float(closest['archiveRecord']['HEIGHT'])-old_bm['conditionalHeightODN_m'], 6),
                 'status': 'Candidate only: match physical wall/mark and check rebuilding; proximity and height agreement do not prove identity.'}
    parapet = next(b for b in nearby if b['bng_e'] == 538880 and b['bng_n'] == 183200)
    ground_estimate = float(parapet['archiveRecord']['HEIGHT'])-float(parapet['archiveRecord']['HEIGHT ABOVE GROUND'])
    report = {
        'status': 'Research comparison; no scene or source-reading changes',
        'sourceSnapshotSHA256': hashlib.sha256(snapshot).hexdigest(),
        'sources': [
            {'file': 'LiverpoolToNewlyn.csv', 'sha256': digest(OUT/'LiverpoolToNewlyn.csv'),
             'url': 'https://www.ordnancesurvey.co.uk/documents/gps/LiverpoolToNewlyn.csv'},
            {'file': archive.name, 'sha256': digest(archive),
             'url': 'https://www.ordnancesurvey.co.uk/documents/resources/CompleteBenchMarkArchive.zip'},
            {'file': tile_name, 'sha256': hashlib.sha256(tile_bytes).hexdigest(), 'surveyDate': '2003-02-22'},
            {'file': modern.filename, 'sha256': digest(Path(modern.filename)), 'description': '2022 composite, 10 m WCS extract; not a current survey'}],
        'controls': controls, 'candidateBenchmarkMatch': candidate,
        'parapetCheck': {'archive': parapet, 'approximateSupportingSurfaceODN_m': round(ground_estimate, 3),
                         'interpretation': '9.880 m mark minus approximate 0.7 m height above ground gives 9.18 m; supporting surface needs confirmation.'},
        'nearbyArchiveBenchmarks': nearby,
        'limitations': [
            'Historic Liverpool datum follows collection attribution; sheet margin not independently verified.',
            'OS conversion is an approximate local correction, not centimetre-accurate calibration.',
            'Archive verification in 1977 is not evidence of present survival; blank levelling dates remain unknown.',
            'Historic positions and rounded archive grid references have uncertainty of metres.',
            'Bridge rebuilt/widened 1900–1902; crest, walkway, parapet, benchmark and sewer invert are distinct surfaces.',
            'Terrain raster is not a benchmark measurement; bridge removal and steep edges affect samples.',
            '2003 and modern products differ in resolution, filtering, sampling and geoid realization.',
            'Agreement supports approximate continuity; no universal scene offset has been established.'],
        'nextStep': 'Use approximately 9.2–9.3 m ODN as a provisional crest reference for a bounded trial, retaining uncertainty and checking adjacent controls before adopting a scene datum.'}
    (OUT/'comparison.json').write_text(json.dumps(report, indent=2)+'\n')

    fig, ax = plt.subplots(figsize=(11, 6), constrained_layout=True)
    bounds = (538800, 539160, 183100, 183290)
    w, e, s, n = bounds
    crop = native[int(top-n):int(top-s), int(w-left):int(e-left)]
    plot = ax.imshow(crop, extent=bounds, vmin=0, vmax=11, cmap='terrain', interpolation='nearest')
    for i, item in enumerate(controls):
        p = item['sourceRecord']
        ax.scatter(p['bng_e'], p['bng_n'], c='black', s=25)
        ax.annotate(f"{p['value_ft']:g} ft → {item['conditionalHeightODN_m']:.2f} m*",
                    (p['bng_e'], p['bng_n']), xytext=(5, 12 if i != 2 else -22),
                    textcoords='offset points', fontsize=9,
                    bbox={'facecolor': 'white', 'alpha': .85, 'edgecolor': 'none'})
    for bm in [closest, parapet]:
        ax.scatter(bm['bng_e'], bm['bng_n'], marker='+', s=110, c='red')
        ax.annotate(f"OS mark {float(bm['archiveRecord']['HEIGHT']):.3f} m",
                    (bm['bng_e'], bm['bng_n']), xytext=(12, -28), textcoords='offset points', fontsize=9,
                    arrowprops={'arrowstyle': '-'}, bbox={'facecolor': 'white', 'alpha': .85, 'edgecolor': 'none'})
    ax.set(xlabel='BNG easting (m)', ylabel='BNG northing (m)',
           title='Channelsea sewer crossing: historic controls and 2003 terrain\n*Conditional Liverpool-to-Newlyn conversion; red crosses = OS legacy benchmarks')
    ax.ticklabel_format(style='plain', useOffset=False)
    fig.colorbar(plot, ax=ax, label='EA 2003 DTM height (m ODN); bridges may be filtered')
    fig.savefig(OUT/'comparison.png', dpi=160)
    plt.close(fig)
    print(json.dumps({'candidateBenchmark': candidate, 'parapetSurfaceEstimate_m': ground_estimate,
                      'controls': [{k: x[k] for k in ['conditionalHeightODN_m', 'terrainSamples', 'native2003CellMinusHistoric_m']} for x in controls]}, indent=2))


if __name__ == '__main__':
    main()
