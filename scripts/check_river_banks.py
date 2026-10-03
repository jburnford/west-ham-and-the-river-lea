"""Validate rendered bank coverage, passage clearance and open source boundaries."""
import json
from pathlib import Path
import numpy as np
import shapely
from shapely.geometry import Polygon,LineString
from river_bank_sections import Distance

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/data'
m=json.loads((OUT/'river-system-1900.json').read_text());s=m['bankSections']
p=np.fromfile(OUT/m['positionFile'],dtype='<f4').reshape(-1,3)
i=np.fromfile(OUT/m['indexFile'],dtype='<u4').reshape(-1,3)
mud=np.fromfile(OUT/m['sedimentFile'],dtype='u1')
cover=np.fromfile(OUT/m['landcoverFile'],dtype='u1').reshape(-1,2)
faces=np.fromfile(OUT/m['faceFile'],dtype='<f4').reshape(-1,3)
uv=np.fromfile(OUT/m['faceUVFile'],dtype='<f4').reshape(-1,2)
assert len(mud)==len(cover)==len(p) and len(faces)==len(uv)==m['faceVertices']
assert np.isfinite(p).all() and np.isfinite(faces).all() and np.isfinite(uv).all()
assert mud.max()==255 and mud.min()==0 and cover[:,0].max()==255
geom=lambda parts:shapely.union_all([Polygon(r[0],r[1:]) for r in parts])
water=shapely.union_all([geom(r['polygons']) for r in m['reaches']])
banks=geom(s['bankPolygons']);shapely.prepare(banks)
assert banks.intersection(water).area<.001,'Bank footprint intrudes into mapped water'
bank_coverage=sum(c['areaM2'] for c in s['coverage'] if c['kind']=='bank')
assert abs(bank_coverage-banks.area)<.01,'Bank envelope has unmeshed strips'
for section in s['coverage']:
    if section['kind']=='bed':
        y=p[section['vertexStart']:section['vertexStart']+section['vertexCount'],1]
        assert y.max()<=m['waterLevel']-.349,'Submerged shoreline vertex spiked to bank-top level'
tri=p[i].astype(float)
cross=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])[:,1]
assert cross.min()>-.01,'Downward-facing ground triangles'
centres=tri.mean(axis=1)
land=shapely.contains_xy(banks,centres[:,0],centres[:,2])
rendered_bank_area=np.abs(cross[land]).sum()/2
assert abs(rendered_bank_area-banks.area)<banks.area*.0002,'Rendered banks do not cover their footprint'
assert p[:,1].min()<m['waterLevel']-1.5 and p[:,1].max()>m['waterLevel']+1.4
assert s['modelledShoreLengthMetres']>40000 and s['canalFacingLengthMetres']>4000
# A bank wall must run along the outside shoreline, never across a connection.
face_points=shapely.points(faces[:,0],faces[:,2])
distance=Distance(water.boundary)(face_points)
assert distance.max()<.002,'Canal facing crosses or departs from the mapped shoreline'
openings=shapely.union_all([LineString(r) for r in s['openBoundaries']])
assert Distance(openings)(face_points).min()>13.99,'Wall closes a source boundary'
assert banks.intersection(openings.buffer(13.99)).area<.001
groups=s['materialGroups']
assert sum(g['count'] for g in groups)==i.size and groups[1]['count']>1000
# Index acceleration must retain exact geometric distances.
sample=shapely.points(p[::max(1,len(p)//100),0],p[::max(1,len(p)//100),2])
assert np.allclose(Distance(water)(sample),shapely.distance(sample,water),atol=1e-8)
report={'status':'PASS','shoreLengthMetres':s['modelledShoreLengthMetres'],
        'canalFacingLengthMetres':s['canalFacingLengthMetres'],'bankAreaM2':banks.area,
        'renderedBankAreaM2':rendered_bank_area,'maximumFacingOffsetMetres':float(distance.max()),
        'checks':['continuous shore-conforming bank coverage','channel and confluence clearance',
                  'open source boundaries','submerged beds and raised banks','sediment and coping materials',
                  'upward ground winding','exact spatial-index distances'],
        'limitations':['Profiles and masonry materials are interpreted; no surveyed crest or bed calibration.']}
(ROOT/'scenes/channelsea-sewer-panorama/review/river-banks-checks.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
