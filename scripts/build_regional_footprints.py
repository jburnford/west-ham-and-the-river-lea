#!/usr/bin/env python3
"""Publish lightweight plan tiles; retain the source vectors in local research files."""
import gzip
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw
from pyproj import Transformer
from shapely import make_valid
from shapely.geometry import Polygon, LineString, Point, shape, box
from shapely.ops import transform, unary_union

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/data/regional-footprints'
OUT.mkdir(parents=True,exist_ok=True)
REF=ROOT/'reference/historic-building-footprints-2026-09-28'
STUDY=ROOT/'reference/topography-research-2026-09-28'
west,south,east,north=json.loads((STUDY/'study-area.json').read_text())['boundsBNG']
ox,oz=538900,183209
bounds=[west-ox,oz-north,east-ox,oz-south]
extent=box(west,south,east,north)
def read(file):return json.loads((ROOT/file).read_text())
def local(points):return make_valid(Polygon([(ox+x,oz-z) for x,z in points]))
mask=[]
for file in ['docs/data/factory-buildings.json','docs/data/high-street-frontages.json']:
    for b in read(file)['buildings']:mask.append(local(b['footprint']).buffer(2))
for b in read('docs/data/housing-detail.json')['rows']:mask.append(local(b['footprint']).buffer(4))
plan=read('docs/data/ground-plan.json')
for b in plan['neighbourhood']['houses']:mask.append(local(b['footprint']).buffer(2))
for h in plan['neighbourhood']['holders']:mask.append(Point(ox+h['x'],oz-h['z']).buffer(h['radius']+2))
for r in read('docs/data/infrastructure.json')['roads']:
    mask.append(LineString([(ox+x,oz-z) for x,z in r['route']]).buffer(r['width']/2+1))
station=read('docs/data/abbey-station-plan.json')
mask.append(local(station['worldFootprint']).buffer(2))
for chimney in station['chimneys']:mask.append(local(chimney['worldFootprint']).buffer(1))
mask=unary_union(mask)
def polygons(g):
    if g.geom_type=='Polygon':yield g
    elif hasattr(g,'geoms'):
        for child in g.geoms:yield from polygons(child)

# A coarse atlas is always available; one-metre tiles replace it close to the camera.
scale=3072/(north-south)
size=(math.ceil((east-west)*scale),3072)
overview=Image.new('L',size,0); overview_draw=ImageDraw.Draw(overview)
tile_size=1000
tiles={}
def draw_polygon(draw,p,left,top,scale,fill):
    draw.polygon([((x-left)*scale,(top-y)*scale) for x,y in p.exterior.coords],fill=fill)
    for hole in p.interiors:draw.polygon([((x-left)*scale,(top-y)*scale) for x,y in hole.coords],fill=0)
with gzip.open(REF/'west-ham-buffer-buildings-bng.geojson.gz','rt') as stream:
    features=json.load(stream)['features']
source_count=len(features)
used=masked=0
for f in features:
    g=shape(f['geometry'])
    if g.intersects(mask):
        g=g.difference(mask);masked+=1
    g=g.intersection(extent)
    if g.is_empty:continue
    used+=1
    for polygon in polygons(g):
        draw_polygon(overview_draw,polygon,west,north,scale,255)
        x0,y0,x1,y1=polygon.bounds
        for ix in range(math.floor(x0/tile_size),math.floor(x1/tile_size)+1):
            for iy in range(math.floor(y0/tile_size),math.floor(y1/tile_size)+1):
                key=(ix,iy)
                if key not in tiles:
                    im=Image.new('L',(1024,1024),0);tiles[key]=(im,ImageDraw.Draw(im))
                draw_polygon(tiles[key][1],polygon,ix*tile_size,(iy+1)*tile_size,1024/tile_size,255)
    if used%50000==0:print(f'Rasterised {used} footprints',flush=True)
del features

def save_alpha(mask,path):
    image=Image.new('RGBA',mask.size,(104,91,72,0));image.putalpha(mask);image.save(path,optimize=True)
save_alpha(overview,OUT/'overview.png')
records=[]
for (ix,iy),(image,_) in sorted(tiles.items()):
    if image.getbbox() is None:continue
    file=f'{ix}-{iy}.png';save_alpha(image,OUT/file)
    records.append({'id':f'{ix}-{iy}','file':file,'bounds':[ix*tile_size-ox,oz-(iy+1)*tile_size,(ix+1)*tile_size-ox,oz-iy*tile_size]})

# Context water is a historical plan, not a new tidal/height model.
water=Image.new('RGBA',size,(0,0,0,0));wd=ImageDraw.Draw(water)
project=Transformer.from_crs(4326,27700,always_xy=True).transform
water_features=json.loads(Path('/home/jic823/swipe_map/site/data/Water_1895.geojson').read_text())['features']
for f in water_features:
    g=make_valid(transform(project,shape(f['geometry'])))
    if not g.intersects(extent):continue
    for p in polygons(g.intersection(extent)):
        wd.polygon([((x-west)*scale,(north-y)*scale) for x,y in p.exterior.coords],fill=(112,139,139,255))
        for ring in p.interiors:wd.polygon([((x-west)*scale,(north-y)*scale) for x,y in ring.coords],fill=(0,0,0,0))
water.save(OUT/'water-context.png',optimize=True)
meta={'bounds':bounds,'sourceDate':'1891–96','sourceFootprints':source_count,'drawnFootprints':used,
      'maskedAgainstModelsOrRoads':masked,'resolutionMetres':tile_size/1024,
      'overview':'overview.png','waterContext':'water-context.png','tiles':records,
      'method':'Flat plan tiles from author-supplied GeoPackage, reprojected to BNG. Existing model footprints and roads masked. Source vectors and IDs retained in research extract.',
      'heightStatus':'No elevations or invented building heights. Regional ground is provisional flat context pending terrain integration.',
      'source':'london_buildings_1891-96_corr_v1.gpkg; author supplied',
      'waterSource':'Existing project Water_1895.geojson; flat contextual plan outside detailed river scene'}
(OUT/'index.json').write_text(json.dumps(meta,indent=2)+'\n')
print(f'{used:,} visible source features; {len(records)} tiles; {sum(p.stat().st_size for p in OUT.iterdir())/1e6:.2f} MB')
