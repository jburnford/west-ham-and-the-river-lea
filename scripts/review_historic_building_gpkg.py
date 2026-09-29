#!/usr/bin/env python3
"""Read the author's London footprints without changing the source or live scene."""
import collections
import csv
import gzip
import json
from pathlib import Path
import sqlite3

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
import numpy as np
from pyproj import Transformer
from shapely import from_wkb, make_valid
from shapely.geometry import Polygon, box, mapping, shape
from shapely.ops import transform
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path('/mnt/c/Users/jic823/Dropbox/2026/london_buildings_1891-96_corr_v1.gpkg')
OUT = ROOT / 'reference/historic-building-footprints-2026-09-28'
OUT.mkdir(parents=True, exist_ok=True)
TABLE = 'london_buildings_1891-96_corr_v1'
study = shape(json.loads((ROOT/'reference/topography-research-2026-09-28/study-area.geojson').read_text())['features'][1]['geometry'])
to_source = Transformer.from_crs(27700,3857,always_xy=True).transform
to_bng = Transformer.from_crs(3857,27700,always_xy=True).transform
bounds = transform(to_source,study).bounds
core = box(538900-1650,183209-1600,538900+550,183209+1350)

def unpack(blob):
    assert blob[:2] == b'GP' and blob[2] == 0
    envelope = (blob[3] >> 1) & 7
    size = {0:0,1:32,2:48,3:48,4:64}[envelope]
    return from_wkb(blob[8+size:])

connection = sqlite3.connect('file:'+str(SOURCE)+'?mode=ro',uri=True)
sql = f'''SELECT b.fid,b.buil_class,b.geom FROM "{TABLE}" b
JOIN "rtree_{TABLE}_geom" r ON b.fid=r.id
WHERE r.maxx>=? AND r.minx<=? AND r.maxy>=? AND r.miny<=?'''
rows = connection.execute(sql,(bounds[0],bounds[2],bounds[1],bounds[3]))
geometries, core_features, classes = [], [], collections.Counter()
invalid, empty = 0, 0
feature_path = OUT/'west-ham-buffer-buildings-bng.geojson.gz'
with gzip.open(feature_path,'wt',encoding='utf-8') as stream:
    stream.write('{"type":"FeatureCollection","crs":{"type":"name","properties":{"name":"EPSG:27700"}},"features":[')
    for fid,category,blob in rows:
        geometry = transform(to_bng,unpack(blob))
        if not geometry.is_valid:
            invalid += 1
            geometry = make_valid(geometry)
        if geometry.is_empty or geometry.area <= 0:
            empty += 1
            continue
        if not geometry.intersects(study):
            continue
        properties = {'sourceFid':fid,'buil_class':category}
        feature = {'type':'Feature','properties':properties,'geometry':mapping(geometry)}
        if geometries:
            stream.write(',')
        stream.write(json.dumps(feature,separators=(',',':')))
        geometries.append(geometry)
        classes[str(category)] += 1
        if geometry.intersects(core):
            core_features.append(feature)
        if len(geometries)%20000 == 0:
            print(f'Selected {len(geometries)} historical footprints',flush=True)
    stream.write(']}')
connection.close()
(OUT/'current-scene-buildings-bng.geojson').write_text(json.dumps({'type':'FeatureCollection',
    'crs':{'type':'name','properties':{'name':'EPSG:27700'}},'features':core_features},separators=(',',':')))

# Measure overlap for review only; neither layer is assumed perfect ground truth.
core_geometries = [shape(f['geometry']) for f in core_features]
tree = STRtree(core_geometries)
factory = json.loads((ROOT/'docs/data/factory-buildings.json').read_text())
housing = json.loads((ROOT/'docs/data/housing-detail.json').read_text())
audits, overlays = [], {'factory':[],'housing':[]}
for kind,records in [('factory',factory['buildings']),('housing',housing['rows'])]:
    for record in records:
        if not record.get('footprint'):
            continue
        polygon = make_valid(Polygon([(538900+x,183209-z) for x,z in record['footprint']]))
        overlays[kind].append(polygon)
        matches = tree.query(polygon,predicate='intersects')
        from shapely.ops import unary_union
        intersection = unary_union([polygon.intersection(core_geometries[i]) for i in matches])
        audits.append({'type':kind,'modelId':record['id'],'siteId':record.get('siteId'),
                       'name':record.get('name',record.get('street','')),
                       'footprintAreaM2':round(polygon.area,2),
                       'overlapPercent':round(100*intersection.area/polygon.area,1),
                       'intersectingSourceFeatures':len(matches)})
with (OUT/'model-overlap-review.csv').open('w') as stream:
    writer = csv.DictWriter(stream,fieldnames=list(audits[0]))
    writer.writeheader();writer.writerows(audits)
summary={'source':str(SOURCE),'date':'2026-09-28','sourceBytes':SOURCE.stat().st_size,
         'sourceLayer':TABLE,'sourceCRS':'EPSG:3857','outputCRS':'EPSG:27700',
         'sourceFields':['fid','geom','buil_class'],'sourceHasElevation':False,
         'studyArea':'1911 West Ham county borough plus 3000 m buffer',
         'selection':'Whole footprints intersecting study area; not cut at boundary',
         'regionalFootprints':len(geometries),'currentSceneFootprints':len(core_features),
         'regionalClasses':dict(classes),'invalidCandidateGeometriesRepaired':invalid,
         'emptyCandidateGeometriesSkipped':empty,
         'modelOverlap':{kind:{'count':sum(a['type']==kind for a in audits),
             'medianOverlapPercent':float(np.median([a['overlapPercent'] for a in audits if a['type']==kind])),
             'below20Percent':[a['modelId'] for a in audits if a['type']==kind and a['overlapPercent']<20]}
             for kind in overlays},
         'limitations':'Geometric overlap is a review aid, not an accuracy score. Class definitions and redistribution licence not supplied. Individual polygon counts are not house counts. No live scene changes.'}
(OUT/'inspection.json').write_text(json.dumps(summary,indent=2)+'\n')

def rings(items):
    for item in items:
        if item.geom_type=='Polygon':
            yield np.asarray(item.exterior.coords)/1000
        elif hasattr(item,'geoms'):
            yield from rings(item.geoms)

fig,axes=plt.subplots(1,2,figsize=(15,10),constrained_layout=True)
axes[0].add_collection(PolyCollection(list(rings(geometries)),facecolors='#49544c',edgecolors='none'))
axes[1].add_collection(PolyCollection(list(rings(core_geometries)),facecolors='#879587',edgecolors='none',alpha=.8))
for kind,colour in [('factory','#b44b22'),('housing','#245ac2')]:
    axes[1].add_collection(PolyCollection(list(rings(overlays[kind])),facecolors='none',edgecolors=colour,linewidths=.6,label='Current '+kind+' footprints'))
for ax,area in zip(axes,[study,core]):
    x,y=area.exterior.xy;ax.plot(np.asarray(x)/1000,np.asarray(y)/1000,color='#253328',linewidth=.8)
    a,b,c,d=area.bounds;ax.set_xlim(a/1000,c/1000);ax.set_ylim(b/1000,d/1000)
    ax.set_aspect('equal');ax.set_facecolor('#f4f0e7')
    ax.set_xlabel('BNG easting (km)');ax.set_ylabel('Northing (km)')
axes[0].set_title(f'1891–96 footprints in the 3 km study area\n{len(geometries):,} source polygons')
axes[1].set_title(f'Existing scene alignment review\n{len(core_features):,} source polygons; no automatic repositioning')
axes[1].legend(loc='lower left')
fig.suptitle('Historical building footprints supplied by the author',fontsize=16)
fig.savefig(OUT/'building-footprint-review.png',dpi=170)
plt.close(fig)
print(json.dumps({k:summary[k] for k in ['regionalFootprints','currentSceneFootprints','regionalClasses','modelOverlap']},indent=2))
