#!/usr/bin/env python3
"""Audit downloaded EA survey footprints; make a research preview, not scene terrain."""
import collections
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from pyproj import Transformer
from shapely import contains_xy, make_valid
from shapely.geometry import Point, shape
from shapely.ops import transform, unary_union

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reference/topography-research-2026-09-28'
features = json.loads((OUT / 'study-area.geojson').read_text())['features']
borough, study = [shape(f['geometry']) for f in features]
project = Transformer.from_crs(4326, 27700, always_xy=True).transform
catalogue = json.loads((OUT / 'buffer-archive-index.json').read_text())
assert len(catalogue['features']) == catalogue['numberMatched'], 'Incomplete catalogue pagination'
surveys, groups, repaired = [], collections.defaultdict(list), 0
for feature in catalogue['features']:
    geometry = transform(project, shape(feature['geometry']))
    if not geometry.is_valid:
        repaired += 1
        geometry = make_valid(geometry)
    clipped = geometry.intersection(study)
    if clipped.area < 1:
        continue
    properties = feature['properties']
    surveys.append((properties, geometry))
    groups[properties['year']].append(clipped)
unions = {year: unary_union(parts) for year, parts in groups.items()}
coverage = {year: {'records': len(groups[year]),
                   'coveragePercent': round(area.area / study.area * 100, 2)}
            for year, area in sorted(unions.items())}
places = {'Three Mills': (538373, 182808), 'Abbey Mills': (538715, 183222),
          'City Mills': (538155, 183539), 'Stratford': (539000, 184500),
          'Forest Gate': (540500, 185500)}
point_records = {name: [p for p, g in surveys if g.covers(Point(*xy))]
                 for name, xy in places.items()}
summary = {'date': '2026-09-28', 'boroughYear': 1911, 'bufferMetres': 3000,
           'boroughAreaKm2': borough.area / 1e6, 'studyAreaKm2': study.area / 1e6,
           'catalogueRecords': len(catalogue['features']), 'invalidFootprintsRepaired': repaired,
           'coverageByYear': coverage, 'sampleLocations': point_records,
           'caveat': 'Coverage is union of catalogue footprints, not verified valid raster pixels. '
                     'Sample place coordinates are approximate. Raster acquisition and pixel coverage are recorded separately in early-terrain-2003-10m.json. '
                     'Modern raster is a 10 m WCS extract of the 2022 composite, not a 1900 reconstruction.'}
(OUT / 'coverage-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
with (OUT / 'survey-inventory.csv').open('w') as stream:
    fields = ['year', 'sdflown', 'edflown', 'resolution', 'ostilename', 'polygonid',
              'dtm_name', 'transform', 'geoid']
    writer = csv.DictWriter(stream, fields, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(sorted((p for p, _ in surveys), key=lambda p: (p['year'], p['ostilename'], p['resolution'])))

im = Image.open(OUT / 'west-ham-buffer-modern-dtm-10m.tif')
height = np.asarray(im).copy()
matrix = im.tag_v2[34264]
step, west, north = matrix[0], matrix[3], matrix[7]
assert step == 10 and matrix[5] == -10
east, south = west + height.shape[1] * step, north - height.shape[0] * step
x, y = np.meshgrid(west + (np.arange(height.shape[1]) + .5)*step,
                   north - (np.arange(height.shape[0]) + .5)*step)
height[~contains_xy(study, x, y) | (height < -100)] = np.nan
assert np.isfinite(height).any()
fig, axes = plt.subplots(1, 2, figsize=(14, 9), constrained_layout=True)
extent = [west/1000, east/1000, south/1000, north/1000]
terrain = axes[0].imshow(height, extent=extent, vmin=0, vmax=35, cmap='terrain', interpolation='nearest')
fig.colorbar(terrain, ax=axes[0], shrink=.55, label='Modern ground elevation (metres ODN; colour clipped at 0/35)')
axes[0].set_title('Modern terrain: comparison only\n2022 composite, sampled to 10 m')
covered = contains_xy(unions['2003'], x, y).astype(float)
covered[~contains_xy(study, x, y)] = np.nan
axes[1].imshow(covered, extent=extent, vmin=0, vmax=1, cmap=matplotlib.colors.ListedColormap(['#eaded0', '#719b87']), interpolation='nearest')
axes[1].set_title(f"2003 LiDAR catalogue coverage: {coverage['2003']['coveragePercent']:.1f}%\nGreen = survey footprint; cream = gaps")
for ax in axes:
    for geometry, colour, width in [(study, '#343434', 1), (borough, '#172f49', 2)]:
        polygons = list(geometry.geoms) if geometry.geom_type == 'MultiPolygon' else [geometry]
        for polygon in polygons:
            px, py = polygon.exterior.xy
            ax.plot(np.array(px)/1000, np.array(py)/1000, color=colour, linewidth=width)
    for name in ['Three Mills', 'Stratford', 'Forest Gate']:
        px, py = places[name]
        ax.plot(px/1000, py/1000, 'o', color='#101010', markersize=3)
        ax.annotate(name, (px/1000, py/1000), xytext=(5, -10), textcoords='offset points', fontsize=8)
    ax.set_xlabel('British National Grid easting (km)')
    ax.set_ylabel('Northing (km)')
    ax.set_aspect('equal')
fig.suptitle('West Ham: historic borough and 3 km terrain study buffer', fontsize=16)
fig.text(.5, .005, 'Blue boundary: existing GBHGIS 1911 borough polygon. EA data © Environment Agency; OGL. Catalogue coverage does not guarantee valid heights everywhere.', ha='center', fontsize=8)
fig.savefig(OUT / 'terrain-source-review.png', dpi=150)
plt.close(fig)
print(json.dumps({'areaKm2': summary['studyAreaKm2'], 'coverageByYear': coverage,
                  'preview': str(OUT / 'terrain-source-review.png')}, indent=2))
