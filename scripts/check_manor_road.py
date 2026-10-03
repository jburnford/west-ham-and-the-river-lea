"""Check road source heights, ground contact, rail clearance and stable structures."""
import hashlib
import json
import argparse
from pathlib import Path
import numpy as np
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union
from manor_road import evidence, profile, domain
from historic_elevation import sample_grid

ROOT=Path(__file__).resolve().parents[1]
load=lambda p:json.loads((ROOT/p).read_text())
spec=evidence();infra=load('docs/data/infrastructure.json');meta=load('docs/data/terrain-1900.json')
road=next(r for r in infra['roads'] if r['name']==spec['name'])
assert road['elevationProfile']==spec
for p,h in spec['inputHashes'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h
rail=next(r for r in infra['railways'] if r['name']==spec['railway']['name'])
line=LineString(road['route']);track=LineString(rail['route'])
assert line.distance(track)>road['width']/2+1.1+4.3, 'Road shoulders overlap rail ballast'
assert rail['formationHeight']==5.5, 'No surveyed formation height has been supplied'
assert 180<line.length<185
mesh=unary_union([Polygon(t) for t in infra['roadSurfaces']['macadam'] if Polygon(t).distance(line)<.01])
assert line.buffer(road['width']/2-.01,cap_style=2).difference(mesh).area<.1
grid=np.fromfile(ROOT/'docs/data'/meta['files']['scene'],dtype='<f4').reshape(meta['height'],meta['width'])
weight=np.fromfile(ROOT/'docs/data'/meta['files']['weight'],dtype='<f4').reshape(grid.shape)
mask=np.fromfile(ROOT/'docs/data'/meta['files']['roadMask'],dtype='u1').reshape(grid.shape)
drain=np.fromfile(ROOT/'docs/data'/meta['files']['drainageMask'],dtype='u1').reshape(grid.shape)
assert mask.any() and not (mask&drain).any()
for c in spec['controls']:
    p=LineString(spec['route']).interpolate(c['distance'])
    ground=float(sample_grid(grid,meta['bounds'],1,p.x,p.y))
    assert abs(ground+.065-c['heightScene'])<.001
    assert sample_grid(weight,meta['bounds'],1,p.x,p.y)>.999
    assert abs(c['heightScene']+meta['verticalReference']['odnMinusSceneYMetres']-c['heightODN'])<1e-8
# The modelled channel retains its pre-road section, independently of road grade.
water=load('docs/data/drainage-1900.json')['renderedReach']
assert abs(water['waterSceneY']-(-1.0115393))<1e-6
# Optional immediate regression check against an explicitly supplied old build.
parser=argparse.ArgumentParser()
parser.add_argument('--compare-before',type=Path)
before=parser.parse_args().compare_before
if before is not None:
    old=json.loads(before.read_text())
    for key in ['sewerBanks','sewerHighStreet','sewerCrestTriangles','sewerRailEdges','roadBridges']:
        assert old[key]==infra[key],key
    for r in old['railways']:
        if r['name']!=rail['name']:
            assert r==next(q for q in infra['railways'] if q['name']==r['name']),r['name']
print(f'PASS: {line.length:.1f} m Manor Road, three source heights and terrain contact, {line.distance(track):.2f} m minimum road/rail centreline separation; drainage and sewer preserved.')
