"""Physical continuity and provenance checks for the regional scene extension."""
import hashlib
import json
from pathlib import Path
import numpy as np
import shapely
from shapely.geometry import Polygon, LineString, Point
from shapely.ops import transform
from spot_height_mosaics import pixel_to_coords

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/data'
meta=json.loads((OUT/'river-system-1900.json').read_text())
geometry=lambda parts:shapely.union_all([Polygon(p[0],p[1:]) for p in parts])
g={r['id']:geometry(r['polygons']) for r in meta['reaches']}
assert all(p.is_valid for p in g.values())
positions=np.fromfile(OUT/meta['positionFile'],dtype='<f4').reshape(-1,3)
indices=np.fromfile(OUT/meta['indexFile'],dtype='<u4')
assert len(positions)==meta['vertices'] and len(indices)==meta['triangles']*3
assert np.isfinite(positions).all() and indices.max()<len(positions)
for path,digest in meta['inputHashes'].items():
    assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,path
for row in meta['crossings']:
    assert row['capacity'] is None and row['gateState'] is None
    for key in row.get('joins',[]):assert g[row['id']].intersects(g[key]),(row['id'],key)
assert g['lea-bridge-navigation'].intersects(g['lea-bridge-river'])
assert g['thames-mouth-context'].intersects(g['Lower_River_Lea-0'])
assert not g['Water_1895-508'].intersects(g['Lower_River_Lea-0']), 'Cut incorrectly merged directly with tidal creek'
assert g['Water_1895-508'].intersects(g['Lower_River_Lea-18'])
# Test physical coverage, not only a graph which could hide disconnected parts
# within one GIS feature. Small reconciliation fragments are reported honestly.
full=shapely.union_all(list(g.values()))
parts=list(full.geoms) if full.geom_type=='MultiPolygon' else [full]
main=max(parts,key=lambda p:p.area)
for key in ['Water_1895-521','Water_1895-550','Lower_River_Lea-10','Lower_River_Lea-11',
            'Lower_River_Lea-5','Lower_River_Lea-6','Lower_River_Lea-0']:
    assert main.intersection(g[key]).area>g[key].area*.99,key
assert next(p for p in meta['crossings'] if p['category']=='mapped-weir-review')['widthMetres']==3
route=next(p for p in meta['crossings'] if p['id']=='channelsea-works-passage')['route']
assert len(route)>10 and LineString(route).length>200,'Channelsea reduced to a straight shortcut'
assert meta['corePreserved'] and not meta['floodDomainChanged']
# A narrowly reviewed shore correction must not change other banks or joins.
review=json.loads((ROOT/'data/maps/lower-lea-region/waterworks-margin-surface-1900.json').read_text())['shorelineReview']
registration=json.loads((ROOT/review['registration']).read_text())
xy=[pixel_to_coords(registration,*p) for p in review['landExclusionPixels']]
land=Polygon([(q['bng_e']-538900,183209-q['bng_n']) for q in xy])
region=json.loads((OUT/'lower-lea-region/index.json').read_text())
original=geometry(next(r['polygons'] for r in region['layers']['Lower_River_Lea'] if r['id']==review['reachId']))
original=transform(lambda e,n:(np.asarray(e)-538900,183209-np.asarray(n)),original)
corrected=g[review['reachId']];removed=original.difference(corrected)
assert corrected.difference(original).area<1e-6,'Shore correction added water'
assert removed.difference(land).area<1e-6,'Unreviewed shoreline changed'
assert 0<removed.area<review['maximumRemovedAreaM2']
assert len(shapely.get_parts(original))==len(shapely.get_parts(corrected))
for key,other in g.items():
 if key!=review['reachId']:
  assert (original.distance(other)<.05)==(corrected.distance(other)<.05),(key,'Shore correction changed a connection')
q=pixel_to_coords(registration,811,741);dot=Point(q['bng_e']-538900,183209-q['bng_n'])
assert original.covers(dot) and corrected.distance(dot)>.5,'15.2ft land dot not reconciled'
caps=np.fromfile(OUT/'river-network.f32',dtype='<f4').reshape(-1,3)[meta['coreBedCorrections']]
flood=json.loads((OUT/'landscape-flood-1900.json').read_text())
x0,z0,x1,z1=flood['bounds']
assert not ((caps[:,0]>=x0)&(caps[:,0]<=x1)&(caps[:,2]>=z0)&(caps[:,2]<=z1)).any(), 'River extension changed the local flood bed'
report={'status':'PASS','mappedPieces':len(g),'crossings':len(meta['crossings']),
        'mainConnectedAreaM2':main.area,'minorReconciliationFragmentsM2':sorted([p.area for p in parts if p!=main],reverse=True),
        'limitations':['Contact is geometric, not unrestricted hydraulic connectivity.',
                       'Small source/core reconciliation fragments remain for the next visual cleanup.']}
path=ROOT/'scenes/channelsea-sewer-panorama/review/river-system-checks.json'
path.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
