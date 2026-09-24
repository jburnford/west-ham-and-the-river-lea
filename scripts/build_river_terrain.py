"""Original inferred tidal terrain; Figure 2.4 is a visual reference, not a DEM.

Keeps the GIS channel routes as anchors. Low-water margins, depths, drainage
rills and the Mill Mead flood bank are interpretations, in the local datum.
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import distance_transform_edt, map_coordinates, gaussian_filter
from shapely import contains_xy
from shapely.geometry import Polygon, LineString, box
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/data'
data = json.loads((OUT / 'ground-plan.json').read_text())
rng = np.random.default_rng(241900)
step = .4
bounds = [-235., -320., 65., 350.]
x = np.arange(bounds[0], bounds[2] + step / 2, step)
z = np.arange(bounds[1], bounds[3] + step / 2, step)
X, Z = np.meshgrid(x, z)
nz, nx = X.shape
patch = box(*bounds)
river = unary_union([Polygon(p[0], p[1:]) for r in data['rivers'] for p in r['polygons']])
southern_bed = unary_union([Polygon(p[0], p[1:]) for p in data['bankStudies']])
# Northern mud shelves follow both banks of the mapped upstream channel.
# Their width is inferred; the southern island is retained from the prior study.
northern_bed = river.buffer(7.5).intersection(box(x[0],z[0],x[-1],0))
bed = unary_union([southern_bed,northern_bed])
water = contains_xy(river, X, Z)
on_bed = contains_xy(bed, X, Z)
outside_distance = distance_transform_edt(~water) * step
inside_distance = distance_transform_edt(water) * step
signed = gaussian_filter(outside_distance - inside_distance, 2)


def noise(scale, seed):
    """Smooth nonperiodic noise sampled in world metres."""
    rand = np.random.default_rng(seed)
    grid = rand.random((int((z[-1]-z[0])/scale)+4, int((x[-1]-x[0])/scale)+4))
    return map_coordinates(grid, [(Z-z[0])/scale+1, (X-x[0])/scale+1], order=3, mode='nearest')


def smooth(a, b, v):
    t = np.clip((v-a)/(b-a), 0, 1)
    return t*t*(3-2*t)


coarse, middle, fine = noise(13, 17), noise(2.8, 82), noise(.55, 116)
# The irregular tidal margin varies around the mapped route, not its centreline.
shore = signed + (middle-.5)*.8 + (fine-.5)*.12
height = .34 + .12*coarse
height = np.where(on_bed, .06 + 1.25*smooth(0, 6, shore), height)
clods = np.maximum(0, fine-.39)**1.4 * .68
height += on_bed * smooth(.3, 2, shore) * ((middle-.5)*.33 + clods)
height = np.where(shore < 0, .06 - .35*smooth(0, 2, -shore) - 1.45*smooth(0, 10, -shore), height)

# River-right, facing south: a raised, irregular bank with lower Mill Mead behind.
# Derive its plan from the outer western channel edge at each north/south section.
edges = []
for zz in z:
    section = river.intersection(LineString([(x[0], zz), (x[-1], zz)]))
    lines = [g for g in getattr(section, 'geoms', [section]) if not g.is_empty and g.geom_type == 'LineString']
    edges.append(min(g.bounds[0] for g in lines) if lines else edges[-1])
edges = np.array(edges)
bank_offset = edges[:, None] - X
bank_start = smooth(8, 24, Z) * (1-smooth(318, 350, Z))
crest = 2.85 + .19*np.sin(Z*.031) + .15*(middle-.5)
bank_shape = smooth(-.4, 5.5, bank_offset) * (1-smooth(9, 22, bank_offset))
bank_height = .3 + bank_shape * crest * bank_start
height = np.maximum(height, np.where((bank_offset > 0) & ~water, bank_height, -100))
height += bank_shape * bank_start * (fine-.5)*.12

# Short meandering drainage cuts lead out into the two main channels.
# Their individual positions are interpretive surface detail, not mapped drains.
rill_canvas = Image.new('L', (nx, nz)); draw = ImageDraw.Draw(rill_canvas)
rills = []
for zz in np.arange(16, 250, 9):
    cross = river.intersection(LineString([(x[0], zz), (x[-1], zz)]))
    lines = sorted([g for g in getattr(cross, 'geoms', [cross]) if not g.is_empty and g.geom_type == 'LineString'], key=lambda g:g.bounds[0])
    if len(lines) < 2:
        continue
    left, right = lines[0].bounds[2], lines[-1].bounds[0]
    for side, start in [(1, left-.8), (-1, right+.8)]:
        length = min((right-left)*.43, rng.uniform(4, 11))
        path = [[start+side*t, zz+np.sin(t*.8)*.55 + t*.12] for t in np.arange(0, length, .3)]
        if len(path) > 2:
            draw.line([((px-x[0])/step, (pz-z[0])/step) for px,pz in path], fill=255, width=1)
            rills.append(path)
for zz in np.arange(-290, -12, 11):
    cross = river.intersection(LineString([(x[0],zz),(x[-1],zz)]))
    lines=[g for g in getattr(cross,'geoms',[cross]) if not g.is_empty and g.geom_type=='LineString']
    if not lines: continue
    west,east=min(g.bounds[0] for g in lines),max(g.bounds[2] for g in lines)
    for side,start in [(-1,west+.6),(1,east-.6)]:
        length=rng.uniform(3.5,6.5)
        path=[[start+side*t,zz+np.sin(t*.9)*.45+t*.1] for t in np.arange(0,length,.25)]
        draw.line([((px-x[0])/step,(pz-z[0])/step) for px,pz in path],fill=255,width=1)
        rills.append(path)
rill_distance = distance_transform_edt(np.asarray(rill_canvas) == 0)*step
cut = np.exp(-(rill_distance/.48)**2) * smooth(.3, 1.4, shore) * on_bed
height = height*(1-cut*.98) - cut*.04

# Isolated shallow pools in the churned bed; connected creeks retain their depth.
pools = []
for _ in range(200):
    ix, iz = rng.integers(0, nx), rng.integers(int((-220-z[0])/step),int((200-z[0])/step))
    if not on_bed[iz,ix] or not 1 < signed[iz,ix] < 12 or bank_shape[iz,ix]*bank_start[iz,ix] > .3:
        continue
    px,pz = x[ix],z[iz]; rx,rz = rng.uniform(.8,2),rng.uniform(1.3,3.5)
    oval = ((X-px)/rx)**2 + ((Z-pz)/rz)**2
    depression = np.clip(1-oval,0,1)
    height = np.where(oval < 1, np.minimum(height, .015 + oval*.8), height)
    pools.append([round(px,2),round(pz,2),round(rx,2),round(rz,2)])

# Taper the patch into the surrounding flat study without vertical seams.
edge_distance = np.minimum.reduce([X-x[0],x[-1]-X,Z-z[0],z[-1]-Z])
blend = smooth(0, 3, edge_distance)
height = height*blend + (-.1)*(1-blend)

# Depth, moisture and bank mask for physically distinct material responses.
depth = np.clip((.06-height)/2.4, 0, 1)
wetness = np.maximum(1-smooth(.04, .95, height), np.exp(-rill_distance*1.8)*.55*on_bed)
sediment_coverage=on_bed.astype(float)*(1-smooth(1.2,2.4,height)*np.clip(bank_shape*bank_start,0,1))
properties = np.stack([depth, wetness, np.clip(bank_shape*bank_start,0,1), sediment_coverage],axis=-1)
height.astype('<f4').tofile(OUT / 'river-terrain.f32')
(np.clip(properties,0,1)*255).astype('uint8').tofile(OUT / 'river-terrain.rgba')
# Land use, not an assertion of a surveyed vegetation cover or species mix.
# 0 open grass/weeds; 1 working industrial ground; 2 cultivated allotments.
industrial=unary_union([Polygon(p[0],p[1:]) for s in data['sites'] for p in s['polygons']])
landcover=np.zeros((nz,nx),dtype='uint8')
landcover[contains_xy(industrial,X,Z)]=1
landcover[contains_xy(Polygon(data['neighbourhood']['garden']['footprint']),X,Z)]=2
landcover.tofile(OUT/'river-terrain.landcover')

def rings(geom):
    return [list(geom.exterior.coords)] + [list(r.coords) for r in geom.interiors]

def polygons(geom):
    return [rings(g) for g in getattr(geom, 'geoms', [geom]) if g.geom_type == 'Polygon' and not g.is_empty]

# Keep the rest of the original waterways and industrial ground pads intact.
outside_rivers = polygons(river.difference(patch))
outside_sites = []
for site in data['sites']:
    geom = unary_union([Polygon(p[0],p[1:]) for p in site['polygons']])
    outside_sites.extend(polygons(geom.difference(patch)))
meta = {'bounds': bounds, 'step':step, 'width':nx, 'height':nz, 'waterLevel':.06,
        'heightFile':'river-terrain.f32', 'propertyFile':'river-terrain.rgba','landcoverFile':'river-terrain.landcover',
        'outsideRivers':outside_rivers, 'outsideSites':outside_sites,
        'bankRoute':[[round(float(edges[i]-7),2),round(float(z[i]),2)] for i in range(round((20-z[0])/step),round((325-z[0])/step),round(4/step))],
        'rills':len(rills), 'pools':pools,
        'evidence':'Figure 2.4 and author identification of the raised river-right bank and low Mill Mead. Heights, depths, rills, pools and bank section are interpretations, not surveyed levels.',
        'heightRange':[round(float(height.min()),3),round(float(height.max()),3)]}
(OUT / 'river-terrain.json').write_text(json.dumps(meta,separators=(',',':'))+'\n')

assert np.isfinite(height).all()
assert height[water & (edge_distance > 3)].mean() < .06
assert np.median(height[(bank_offset > 5)&(bank_offset < 9)&(Z > 30)&(Z < 200)]) > 2.2
assert np.median(height[contains_xy(Polygon(data['neighbourhood']['garden']['footprint']),X,Z)]) < .8
print(f'Terrain: {nx} × {nz}; height range {meta["heightRange"]}; {len(rills)} rills, {len(pools)} pools. Channel depth, bank crest and low garden checks passed.')
