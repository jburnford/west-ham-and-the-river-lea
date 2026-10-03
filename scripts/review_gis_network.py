"""Compare supplied railway/water/dock vectors with the current scene in metres."""
import json
import os
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR', '/tmp/channelsea-matplotlib')
from matplotlib import pyplot as plt
from pyproj import Transformer
from shapely import make_valid
from shapely.geometry import shape, box, mapping, LineString, Polygon
from shapely.ops import transform

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reference/footprint-model-alignment'
project = Transformer.from_crs(4326, 27700, always_xy=True).transform
area = box(-1700, -1500, 650, 1250)

def local(x, y, z=None):
    e, n = project(x, y)
    return e-538900, 183209-n

def parts(g):
    if hasattr(g, 'geoms'):
        for child in g.geoms:
            yield from parts(child)
    else:
        yield g

def read(path):
    return json.loads((ROOT/path).read_text())

features = []
fig, ax = plt.subplots(figsize=(12, 14))
for name, color in [('Water_1895', '#8fbee8'), ('Lower_River_Lea', '#438cba'),
                    ('Docks', '#16618b'), ('Rail_1895', '#d84239')]:
    for feature in read('docs/maps/data/'+name+'.geojson')['features']:
        g = make_valid(transform(local, shape(feature['geometry']))).intersection(area)
        if g.is_empty:
            continue
        features.append({'type': 'Feature', 'geometry': mapping(g), 'properties': {
            'layer': name, 'featureId': feature.get('id'), **feature['properties']}})
        for p in parts(g):
            if p.geom_type == 'Polygon':
                ax.fill(*p.exterior.xy, color=color, alpha=.35)
            elif p.geom_type == 'LineString':
                label = 'GIS railway' if not any(l.get_label() == 'GIS railway' for l in ax.lines) else None
                ax.plot(*p.xy, color=color, lw=2, label=label)
for index, railway in enumerate(read('docs/data/infrastructure.json')['railways']):
    g = LineString(railway['route'])
    ax.plot(*g.xy, '--', color='#111', lw=1.5, label='Scene railway' if index == 0 else None)
    ax.text(*g.interpolate(.5, normalized=True).coords[0], railway['name'].replace('Great Eastern Railway', 'GER'), fontsize=7)
for building in read('docs/data/factory-buildings.json')['buildings']:
    for p in building['renderPolygons']:
        g = Polygon(p['outer'], p['holes'])
        ax.fill(*g.exterior.xy, color='#73694c', alpha=.45)
ax.set(xlim=(-1700, 650), ylim=(1250, -1500), xlabel='Scene east (m)', ylabel='Scene south (m)',
       title='Repository GIS railway/water/docks with current scene routes')
ax.set_aspect('equal')
ax.legend()
fig.tight_layout()
fig.savefig(OUT/'east-channelsea-gis-network-audit.png', dpi=150)
(OUT/'east-channelsea-gis-network-extract.geojson').write_text(json.dumps({
    'type': 'FeatureCollection',
    'coordinateSystem': 'Local metres: x=BNG easting-538900, z=183209-BNG northing',
    'source': 'docs/maps/data; provenance in docs/maps/data/README.md. Invalid source polygons repaired for this diagnostic only.',
    'features': features}, indent=2)+'\n')
print(f'{len(features)} local GIS features saved with scene comparison.')
