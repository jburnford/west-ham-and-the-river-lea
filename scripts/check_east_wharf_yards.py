"""Check native registration, protected plots, clearances and retained yards."""
import json
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon, shape
from shapely.ops import unary_union
from factory_map_sources import mosaic

ROOT = Path(__file__).resolve().parents[1]
load = lambda p: json.loads((ROOT / p).read_text())
union = lambda rows: unary_union([Polygon(p[0], p[1:]) for p in rows])
reg = load('data/maps/east-wharf-yards.json')
yards = load('docs/data/factory-yards.json')
current = {s['id']: s for s in yards['sites']}
before = load(reg['baseline'])
cache = {int(fid): shape(g) for fid, g in load(reg['sourceCache']).items()}
_, world, _ = mosaic(reg['bounds'])
assert {s['id'] for s in reg['yards']} == {9005,9006,9007}
for row in reg['yards']:
    parcel = Polygon(row['worldTrace'])
    assert parcel.is_valid
    assert np.max(np.abs(world(row['tracePixels'])-np.asarray(row['worldTrace'][:-1]))) < .00051
    protected = unary_union([s for s in cache.values() if s.intersects(parcel)])
    source = union(row['polygons'])
    assert source.difference(parcel).area < .001
    assert source.intersection(protected).area < .001, ('source roof covered', row['id'])
    rendered = current[row['id']]
    surface = union(rendered['polygons'])
    assert surface.area > 150, ('missing wharf surface', row['id'])
    assert surface.difference(source).area < .001
    assert surface.intersection(protected).area < .001, ('unmodelled source roof covered', row['id'])
    assert not rendered['stock'] and row['allowStock'] is False
# This bounded addition must not consume an existing yard or alter its stock.
for old in before['sites']:
    assert current[old['id']] == old, ('unrelated yard changed', old['id'])
assert yards['tracks'] == before['tracks'], 'Wharf work changed a siding'
assert len(current) == len(before['sites'])+3
print('Three native OS wharf surfaces clear all supplied roof outlines; all 88 earlier yards and tracks preserved; no stock added.')
