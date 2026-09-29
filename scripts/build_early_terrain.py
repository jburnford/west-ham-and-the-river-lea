#!/usr/bin/env python3
"""Reduce dated EA rasters to a research mosaic; never fill historical gaps silently."""
import hashlib
import io
import json
from pathlib import Path
import warnings
import zipfile

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from shapely import contains_xy
from shapely.geometry import shape

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reference/topography-research-2026-09-28'
STEP = 10
study_meta = json.loads((OUT / 'study-area.json').read_text())
west, south, east, north = study_meta['boundsBNG']
nx, ny = (east-west)//STEP, (north-south)//STEP
study = shape(json.loads((OUT / 'study-area.geojson').read_text())['features'][1]['geometry'])
X, Y = np.meshgrid(west+(np.arange(nx)+.5)*STEP, north-(np.arange(ny)+.5)*STEP)
inside = contains_xy(study, X, Y)
height = np.full((ny, nx), np.nan, dtype='float32')
support = np.zeros((ny, nx), dtype='float32')
source_id = np.zeros((ny, nx), dtype='uint16')
selected = json.loads((OUT / 'selected-downloads.json').read_text())
entries, files, seen = [], [], set()
for record in selected:
    archive = OUT / 'tiles-2003' / (record['tile']['id']+'.zip')
    assert zipfile.is_zipfile(archive), f'Incomplete archive: {archive}'
    with zipfile.ZipFile(archive) as z:
        for name in z.namelist():
            if name.endswith('.tif') and name not in seen:
                seen.add(name)
                entries.append((name.split('_')[-2], float(record['resolution']['id']), archive, name))
    with archive.open('rb') as stream:
        checksum = hashlib.file_digest(stream, 'sha256').hexdigest()
    files.append({'file':str(archive.relative_to(OUT)), 'url':record['uri']+'?subscription-key=public',
                  'bytes':archive.stat().st_size, 'sha256':checksum})

# Latest 2003 date wins valid overlap; at equal dates the finer source wins.
entries.sort(key=lambda item: (item[0], -item[1], item[3]))
source_records = []
for date, resolution, archive, name in entries:
    with zipfile.ZipFile(archive) as z:
        data = z.read(name)  # Reading also checks the ZIP CRC.
    im = Image.open(io.BytesIO(data))
    scale = im.tag_v2[33550]
    tie = im.tag_v2[33922]
    pixel = scale[0]
    left, top = tie[3] - tie[0]*pixel, tie[4] + tie[1]*pixel
    assert scale[1] == pixel and pixel in (.5, 1), (name, scale)
    assert date.startswith('2003'), name
    factor = int(STEP/pixel)
    assert im.width % factor == im.height % factor == 0
    col, row = round((left-west)/STEP), round((north-top)/STEP)
    assert abs(left-(west+col*STEP)) < .01 and abs(top-(north-row*STEP)) < .01
    h, w = im.height//factor, im.width//factor
    r0, r1, c0, c1 = max(0,row), min(ny,row+h), max(0,col), min(nx,col+w)
    if r0>=r1 or c0>=c1 or not inside[r0:r1,c0:c1].any():
        continue
    a = np.asarray(im).copy()
    a[(a < -100) | (a > 300)] = np.nan
    blocks = a.reshape(h,factor,w,factor).transpose(0,2,1,3).reshape(h,w,-1)
    fraction = np.isfinite(blocks).mean(axis=-1)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', RuntimeWarning)
        reduced = np.nanmedian(blocks, axis=-1)
    reduced[fraction < .5] = np.nan
    reduced = reduced[r0-row:r1-row,c0-col:c1-col]
    fraction = fraction[r0-row:r1-row,c0-col:c1-col]
    valid = np.isfinite(reduced) & inside[r0:r1,c0:c1]
    dest = height[r0:r1,c0:c1]
    dest[valid] = reduced[valid]
    support[r0:r1,c0:c1][valid] = fraction[valid]
    source_records.append({'id':len(source_records)+1,'file':name,'archive':archive.name,
                           'surveyDate':date,'resolutionMetres':pixel,
                           'sha256':hashlib.sha256(data).hexdigest()})
    source_id[r0:r1,c0:c1][valid] = len(source_records)
    if len(source_records)%20 == 0:
        print(f'Processed {len(source_records)} source rasters', flush=True)

assert np.all(source_id[np.isfinite(height)] > 0)
assert not np.isfinite(height[~inside]).any()
height.astype('<f4').tofile(OUT / 'early-terrain-2003-10m.f32')
source_id.astype('<u2').tofile(OUT / 'early-terrain-2003-10m.sources.u16')
support.astype('<f4').tofile(OUT / 'early-terrain-2003-10m.support.f32')
np.savez_compressed(OUT / 'early-terrain-2003-10m.npz', height=height, source_id=source_id,
                    support=support, inside=inside, bounds=np.array([west,south,east,north]))

modern_im = Image.open(OUT / 'west-ham-buffer-modern-dtm-10m.tif')
assert modern_im.size == (nx,ny)
modern = np.asarray(modern_im).copy()
modern[(modern < -100) | ~inside] = np.nan
both = np.isfinite(height) & np.isfinite(modern)
# Differences are screening evidence only: datum corrections and water masking outstanding.
change = np.where(both, modern-height, np.nan)
meta = {'date':'2026-09-28','status':'Research surface, not scene-integrated',
        'boundsBNG':[west,south,east,north], 'cellSizeMetres':STEP,'width':nx,'height':ny,
        'orientation':'Rows north to south; columns west to east; cell-centre samples',
        'heightFile':'early-terrain-2003-10m.f32','missingValue':'NaN',
        'method':'Median of 10 m cells, at least 50% valid source pixels; latest 2003 date wins; finer source wins ties; no gap filling',
        'validAreaPercent':round(np.isfinite(height).sum()/inside.sum()*100,2),
        'validAreaKm2':round(np.isfinite(height).sum()*STEP*STEP/1e6,3),
        'sourceRasterCount':len(source_records),'archives':files,'sources':source_records,
        'datumCaution':'EA source ODN heights retain original survey geoid/transform; no OSGM91/02-to-15 adjustment yet. Current scene has arbitrary local datum.',
        'comparisonCaution':'Modern WCS 10 m samples compared with old 10 m medians. Water returns, different processing and datum versions affect differences. Not an earthwork-volume estimate.',
        'changePercentilesMetres':dict(zip(['p05','median','p95'],np.nanpercentile(change,[5,50,95]).tolist()))}
samples = {}
for label,(px,py) in {'Three Mills':(538373,182808),'Abbey Mills':(538715,183222),
                      'City Mills':(538155,183539),'Forest Gate':(540500,185500),
                      'Stadium vicinity':(538000,184500),'Northeastern high ground':(540500,187500)}.items():
    c,r=int((px-west)/STEP),int((north-py)/STEP)
    old=height[r-5:r+6,c-5:c+6]; now=modern[r-5:r+6,c-5:c+6]
    samples[label]={'centreBNG':[px,py],'windowMetres':110,
                    'median2003':round(float(np.nanmedian(old)),3),
                    'medianModern':round(float(np.nanmedian(now)),3),
                    'medianPairedDifference':round(float(np.nanmedian(now-old)),3),
                    'validPairedCells':int((np.isfinite(old)&np.isfinite(now)).sum())}
meta['sampleWindows']=samples
(OUT / 'early-terrain-2003-10m.json').write_text(json.dumps(meta,indent=2)+'\n')

fig,axes=plt.subplots(1,3,figsize=(18,8),constrained_layout=True)
extent=[west/1000,east/1000,south/1000,north/1000]
for ax,a,title in zip(axes,[height,modern,change],['2003 terrain mosaic','Modern comparison surface','Apparent change: modern minus 2003']):
    diff = ax is axes[2]
    cmap=plt.get_cmap('RdBu_r' if diff else 'terrain').copy()
    cmap.set_bad('#ddd8cf')
    image=ax.imshow(a,extent=extent,cmap=cmap,
                    vmin=-6 if diff else 0,vmax=6 if diff else 35,interpolation='nearest')
    ax.set_title(title)
    for feature in json.loads((OUT/'study-area.geojson').read_text())['features']:
        geom=shape(feature['geometry'])
        for polygon in list(geom.geoms) if geom.geom_type=='MultiPolygon' else [geom]:
            px,py=polygon.exterior.xy;ax.plot(np.array(px)/1000,np.array(py)/1000,color='#243d4d',linewidth=.8)
    for label,px,py in [('Three Mills',538373,182808),('Stratford',539000,184500),('Forest Gate',540500,185500)]:
        ax.plot(px/1000,py/1000,'k.',markersize=3)
        ax.annotate(label,(px/1000,py/1000),xytext=(4,3),textcoords='offset points',fontsize=7)
    ax.set_xlabel('BNG easting (km)');ax.set_ylabel('Northing (km)')
    fig.colorbar(image,ax=ax,shrink=.55,label='Metres difference' if diff else 'Metres above source datum')
fig.suptitle(f"West Ham and 3 km surroundings — 2003 valid terrain coverage {meta['validAreaPercent']}%",fontsize=16)
fig.text(.5,.005,'Grey gaps remain unfilled. Difference colours are clipped at ±6 m; datum/processing/water differences remain. EA data © Environment Agency, OGL.',ha='center',fontsize=9)
fig.savefig(OUT/'early-modern-terrain-comparison.png',dpi=150)
plt.close(fig)
print(json.dumps({k:meta[k] for k in ['validAreaPercent','validAreaKm2','sourceRasterCount','changePercentilesMetres']},indent=2))
