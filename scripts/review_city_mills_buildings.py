"""Build a local evidence sheet for individual City Mills buildings.

No geometry or reference imagery is copied into the public viewer. The source
register retains unknown heights/roofs as null until they can be assessed.
"""
import hashlib
import json
import math
import os
from pathlib import Path

os.environ.setdefault('MPLCONFIGDIR', '/tmp/mpl-city-mills')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
from shapely.geometry import Polygon
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reference/city-mills-howards/building-review'


def fit(controls):
    source = [complex(*c['pixel']) for c in controls]
    target = [complex(*c['target']) for c in controls]
    sm, tm = sum(source)/len(source), sum(target)/len(target)
    a = sum((s-sm).conjugate()*(t-tm) for s, t in zip(source, target)) / sum(abs(s-sm)**2 for s in source)
    b = tm-a*sm
    residuals = [abs(a*s+b-t) for s, t in zip(source, target)]
    return a, b, {'scale': abs(a), 'rotationDegrees': math.degrees(math.atan2(a.imag, a.real)),
                  'coefficients': [a.real, a.imag, b.real, b.imag],
                  'radialRms': math.sqrt(sum(r*r for r in residuals)/len(residuals)),
                  'residuals': residuals}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    register = json.loads((ROOT/'data/maps/city-mills-building-register.json').read_text())
    source = ROOT/register['source']['image']
    assert hashlib.sha256(source.read_bytes()).hexdigest() == register['source']['sha256']
    a, b, author_fit = fit(register['registration']['authorScreenshot']['controls'])
    c, d, goad_fit = fit(register['registration']['goadToAuthor']['controls'])

    def point(p):
        z = a*(c*complex(*p)+d)+b
        return [z.real, z.imag]

    scene = json.loads((ROOT/'docs/data/ground-plan.json').read_text())
    site = next(f for f in scene['sites'] if f['id'] == register['siteId'])
    parcel = unary_union([Polygon(r[0], r[1:]) for r in site['polygons']])
    water = unary_union([Polygon(r[0], r[1:]) for f in scene['rivers'] for r in f['polygons']])
    records = []
    group = register['buildings'][0]
    envelope = Polygon([point(p) for p in group['footprintPixels']])
    assert envelope.is_valid and envelope.area > 0
    assert parcel.covers(envelope), 'Review footprint must remain inside the premises'
    assert envelope.intersection(water).area == 0, 'Review footprint must not close a channel'
    for part in group['mapParts']:
        world = [point(p) for p in part['footprintPixels']]
        poly = Polygon(world)
        assert poly.is_valid and poly.area > 0, part['id']
        assert parcel.covers(poly) and poly.intersection(water).area == 0, part['id']
        records.append({'id': part['id'], 'mapReference': part['mapReference'],
                        'footprint': [[round(x, 2), round(z, 2)] for x, z in world],
                        'approximateAreaM2': round(poly.area),
                        'outsideEnvelopeM2': round(poly.difference(envelope).area, 2),
                        'heightMetres': None, 'roof': None})
    overlaps = []
    for i, p in enumerate(records):
        for q in records[i+1:]:
            area = Polygon(p['footprint']).intersection(Polygon(q['footprint'])).area
            assert area < .1, (p['id'], q['id'], area)
            if area: overlaps.append({'parts': [p['id'], q['id']], 'areaM2': area})
    report = {'sourceRegister': 'data/maps/city-mills-building-register.json',
              'authorToWorld': author_fit, 'goadToAuthorPixels': goad_fit,
              'goadFitRadialRmsMetres': goad_fit['radialRms']*abs(a),
              'accuracyWarning': register['registration']['warning'],
              'envelope': {'id': group['id'], 'footprint': [point(p) for p in group['footprintPixels']],
                           'approximateAreaM2': round(envelope.area)},
              'parts': records, 'roundingOverlaps': overlaps, 'publishedGeometry': False}
    (OUT/'registered-parts.json').write_text(json.dumps(report, indent=2)+'\n')

    colours = ['#196caa', '#ad3f68', '#aa7615', '#27816d']
    fig, ax = plt.subplots(figsize=(11, 10))
    ax.imshow(Image.open(source))
    for part, colour in zip(group['mapParts'], colours):
        poly = Polygon(part['footprintPixels'])
        x, y = poly.exterior.xy
        ax.plot(x, y, color=colour, linewidth=2)
        centre = poly.representative_point()
        ax.annotate(part['mapReference'], (centre.x, centre.y), xytext=(4, -8), textcoords='offset points',
                    fontsize=12, color=colour, bbox={'facecolor': 'white', 'alpha': .92, 'edgecolor': colour})
        for line in part.get('internalLinesPixels', []):
            ax.plot(*zip(*line), linestyle='--', color=colour, linewidth=1.5)
    ax.set(xlim=(1900, 2370), ylim=(2010, 1645), xlabel='Original TIFF pixel x', ylabel='Original TIFF pixel y',
           title='Howards: Quinine Department — mapped parts, July 1893')
    fig.text(.1, .04, 'Goad F3 / British Library 152637. Outlines are manual interpretations.\n'
                      'Plan partitions do not establish separate roofs. Heights remain unresolved.', fontsize=10)
    fig.subplots_adjust(bottom=.15)
    fig.savefig(OUT/'quinine-parts.png', dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 10))
    for features, colour in [(scene['rivers'], '#bddde8'), ([site], '#e4ddcb')]:
        for feature in features:
            for rings in feature['polygons']:
                x, z = zip(*rings[0])
                ax.fill(x, z, color=colour)
    for part, colour in zip(records, colours):
        p = Polygon(part['footprint'])
        ax.fill(*p.exterior.xy, color=colour, alpha=.75)
        q = p.representative_point()
        ax.text(q.x, q.y, part['mapReference'], fontsize=8, color='white', ha='center', va='center')
    ax.set(xlim=(-790, -650), ylim=(-150, -415), aspect='equal', xlabel='Local x (east), metres',
           ylabel='Local z (south), metres', title='First building group within Howards premises')
    ax.grid(alpha=.2)
    fig.text(.08, .025, 'Provisional registration through author screenshot and existing GIS parcel.\n'
                       'Internal fit agreement is not independent geographical accuracy.', fontsize=9)
    fig.subplots_adjust(bottom=.12)
    fig.savefig(OUT/'quinine-registration.png', dpi=160)
    plt.close(fig)
    print(f"Recorded {len(records)} mapped parts; footprint checks passed; no public geometry generated.")
    print(f"Approximate envelope: {envelope.area:.0f} m². Source-corner fit RMS: {report['goadFitRadialRmsMetres']:.2f} m (internal agreement only).")
    print(OUT)


if __name__ == '__main__':
    main()
