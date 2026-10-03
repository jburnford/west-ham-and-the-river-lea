"""Verify regional source integrity, crop registration and topology audit."""
import hashlib
import json
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon, shape, box
from shapely import union_all
from shapely.ops import transform
from pyproj import Transformer

ROOT=Path(__file__).resolve().parents[1]
PUBLIC=ROOT/'docs/data/lower-lea-region'
d=json.loads((PUBLIC/'index.json').read_text())
for path,digest in d['inputHashes'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,path
t=d['terrain'];a=np.fromfile(PUBLIC/t['heightFile'],dtype='<f4').reshape(t['height'],t['width'])
mask=np.fromfile(PUBLIC/t['validMaskFile'],dtype='u1').reshape(a.shape)
assert np.array_equal(mask,np.isfinite(a))
assert (~np.isfinite(a)).sum()==t['missingCells']>0
meta=json.loads((ROOT/'reference/topography-research-2026-09-28/early-terrain-2003-10m.json').read_text())
src=np.fromfile(ROOT/'reference/topography-research-2026-09-28'/meta['heightFile'],dtype='<f4').reshape(meta['height'],meta['width'])
e0,n0,e1,n1=d['reviewBoundsBNG'];offsetx=(e0-meta['boundsBNG'][0])//10;offsety=(meta['boundsBNG'][3]-n1)//10
assert np.array_equal(a,src[offsety:offsety+t['height'],offsetx:offsetx+t['width']],equal_nan=True)
assert not t['historicalDEM'] and t['date']=='2003'
parts={}
raw=json.loads((ROOT/'data/maps/lower-lea-region/sources/Lower_River_Lea.geojson').read_text())['features']
project=Transformer.from_crs(4326,27700,always_xy=True).transform
for reach in d['layers']['Lower_River_Lea']:
 derived=[]
 for i,rings in enumerate(reach['polygons']):
  g=Polygon(rings[0],rings[1:]);assert g.is_valid
  derived.append(g)
  parts[f'{reach["id"]}-part-{i}']=g
 # A repair must not create dry holes where valid original water parts overlap.
 original=transform(project,shape(raw[reach['sourceIndex']]['geometry']))
 original_parts=list(original.geoms) if original.geom_type=='MultiPolygon' else [original]
 combined=union_all(derived)
 for p in original_parts:
  if p.is_valid:assert p.intersection(box(*d['reviewBoundsBNG'])).difference(combined).area<1e-5
assert set(parts)=={n['id'] for n in d['topology']['nodes']}
assert len(parts)==sum(map(len,d['topology']['components']))
for group in ['contacts','nearConnections']:
 for p in d['topology'][group]:
  distance=parts[p['a']].distance(parts[p['b']]);assert abs(distance-p['distanceMetres'])<1e-6
  assert 'unreviewed' in p['hydraulicStatus']
  assert distance<=.05 if group=='contacts' else .05<distance<=15
assert d['summary']['primaryReaches']==23 and d['summary']['appliedFieldControls']==13
assert sum(m['appliedFieldControl'] for m in d['heightMarks'])==13
marks={m['id']:m for m in d['heightMarks']}
for identifier in ['sh_537687_184334','sh_537793_184215']:
 m=marks[identifier]
 assert m['setting']=='marsh' and m['sourceSetting']=='embankment_top'
 assert m['surfaceReview']['surfaceRole']=='adjacent-ground'
 assert not m['appliedFieldControl'] and not m['setting_conflict']
lane=marks['sh_537648_185504']
assert lane['setting']=='street' and lane['surfaceReview']['mapPixel']==[868,456]
assert np.linalg.norm(np.array(lane['positionBNG'])-np.array([
 lane['surfaceReview']['original']['bng_e'],lane['surfaceReview']['original']['bng_n']]))>8
assert d['heightSurfaceReview']['reviewedMarks']==28
for identifier in ['sh_537687_184334','sh_537793_184215']:
 assert marks[identifier]['surfaceReview']['terrainUse'].startswith('Resolved:')
for identifier,pixel in [('sh_537664_184398',[35,364]),('sh_537740_184274',[231,706])]:
 assert marks[identifier]['surfaceReview']['mapPixel']==pixel
 assert marks[identifier]['setting']=='embankment_top'
for identifier,pixel in [('sh_537688_185311',[933,211]),('sh_537692_185240',[939,401])]:
 assert marks[identifier]['surfaceReview']['mapPixel']==pixel
 assert marks[identifier]['surfaceReview']['surfaceRole']=='adjacent-ground'
assert marks['sh_537688_185311']['setting']=='open_ground'
# Newly transcribed dots retain their own provenance without rewriting the snapshot.
from spot_height_mosaics import pixel_to_coords
supplement_path='data/maps/lower-lea-region/height-observations.additional.geojson'
supplement=json.loads((ROOT/supplement_path).read_text())['features']
assert len(supplement)==1 and d['summary']['heightMarks']==3938
for feature in supplement:
 props=feature['properties'];mark=marks[props['id']]
 assert mark['observationSource']==supplement_path
 registration=json.loads((ROOT/props['registration']).read_text())
 coords=pixel_to_coords(registration,*props['mapPixel'])
 assert np.linalg.norm(np.array(mark['positionBNG'])-[coords['bng_e'],coords['bng_n']])<.01
 assert np.linalg.norm(np.array(project(*feature['geometry']['coordinates']))-mark['positionBNG'])<.01
 assert mark['surfaceReview']['surfaceRole']=='bank-path' and mark['value_ft']==16.8
duplicate=marks['sh_537672_185146']['surfaceReview']
assert duplicate['duplicateOf']=='sh_537659_185146'
assert duplicate['terrainUse'].startswith('Withheld duplicate')
assert duplicate['positionBNG']==marks['sh_537659_185146']['positionBNG']
assert marks['sh_537638_185226']['surfaceReview']['mapPixel']==[795,440]
for identifier in ['sh_537680_184985','sh_537669_184906','sh_537655_184828']:
 assert marks[identifier]['surfaceReview']['surfaceRole']=='bank-margin'
for identifier in ['sh_537458_184621','sh_537374_184619']:
 assert marks[identifier]['setting']=='embankment_foot'
 assert marks[identifier]['surfaceReview']['surfaceRole']=='adjacent-ground'
assert marks['sh_537494_184017']['surfaceReview']['surfaceRole']=='adjacent-ground'
assert marks['sh_537494_184017']['setting']=='marsh'
for identifier in ['sh_537519_184158','sh_537519_184078']:
 assert marks[identifier]['surfaceReview']['surfaceRole']=='bank-margin'
 assert marks[identifier]['setting']=='embankment_top'
assert not d['heightSurfaceReview']['appliedToTerrain']
assert all(r['needsMapReview'] for r in d['repairs'])
review=d['connectionReview'];nav=set(review['navigationReachIds'])
nodes={n['id']:n for n in d['topology']['nodes']}
pairs=d['topology']['contacts']+d['topology']['nearConnections']
expected={frozenset((p['a'],p['b'])) for p in pairs
          if (nodes[p['a']]['reachId'] in nav)!=(nodes[p['b']]['reachId'] in nav)}
expected.update(frozenset((p['a'],p['b'])) for p in review['structureRoutes']
                if (nodes[p['a']]['reachId'] in nav)!=(nodes[p['b']]['reachId'] in nav))
assert expected=={frozenset((p['a'],p['b'])) for p in review['navigationInterfaces']}
assert len(expected)==4
assert any(p['distanceMetres']==0 for p in review['navigationInterfaces'])
for p in pairs:
 assert p['hydraulicPassage'] is None
 if p['reviewCategory']=='provisional-mapping-seam':
  assert nodes[p['a']]['name']==nodes[p['b']]['name'] and p['distanceMetres']<.5
  assert not ({nodes[p['a']]['reachId'],nodes[p['b']]['reachId']} & nav)
assert len(d['topology']['provisionalContinuityLinks'])==3
for site in review['controlSites']:
 assert not site['activeInSolver']
 if site['positionBNG'] is not None:
  assert 'period-map-comparison' in site['evidence'] and 'mapPixelReview' in site
  assert len(site['positionBNG'])==2
 assert all(site[k] is None for k in ['crestODN','sillODN','openingWidthMetres','operatingState'])
 assert set(site['reachIds']) <= {n['reachId'] for n in nodes.values()}
 assert set(site['evidence']) <= set(review['sources'])
assert all(not s['activeInSolver'] for s in review['excludedStructures'])
assert {'author-abbey-map','author-waterworks-map','author-city-mills-map','author-bow-back-map'} <= set(review['sources'])
route=next(r for r in review['routeConstraints'] if r['id']=='bow-back-marshgate-under-bridge')
assert not route['roadDeckIsChannelBed'] and route['unrestrictedHydraulicPassage'] is None
assert 'Lower_River_Lea-22' not in route['reachIds']  # eastern bridge is not the western navigation gap
route=next(r for r in review['routeConstraints'] if r['id']=='pudding-through-mill')
assert not route['inventParallelBypass'] and not route['buildingFootprintIsSolidDam']
assert route['capacity'] is None and not route['unrestrictedHydraulicPassage']
for r in review['structureRoutes']:
 assert abs(parts[r['a']].distance(parts[r['b']])-r['distanceMetres'])<1e-6
 assert r['schematic'] and r['hydraulicPassage'] is None
mouth=next(p for p in pairs if p['reviewCategory']=='mapped-navigation-junction')
assert mouth['navigationInterface'] and mouth['evidence']==['author-navigation-map']
assert {nodes[mouth[k]]['reachId'] for k in ['a','b']}=={'Lower_River_Lea-17','Lower_River_Lea-22'}
assert not next(r for r in review['routeConstraints'] if r['id']=='bow-back-navigation-mouth')['inventGateAtMouth']
old_ford=next(r for r in review['routeConstraints'] if r['id']=='old-ford-side-connection')
assert old_ford['navigationLockAndSideGateAreSeparate'] and old_ford['operatingState'] is None
assert {'old-ford-lock','old-ford-side-floodgate'} <= {s['id'] for s in review['controlSites']}
crop_dir=ROOT/'reference/lower-lea-connection-review'
crop_meta=json.loads((crop_dir/'map-crops.json').read_text())
for site_crops in crop_meta.values():
 for c in site_crops.values():
  assert hashlib.sha256((crop_dir/c['image']).read_bytes()).hexdigest()==c['imageSHA256']
  for path,digest in c['sourceTileHashes'].items():
   assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest
assert len(review['periodComparisons'])==7
mill=next(r for r in review['routeConstraints'] if r['id']=='three-mills-through-buildings')
assert not mill['buildingFootprintIsSolidDam'] and not mill['inventParallelBypass']
assert mill['countCapacityOncePerControlGroup'] and mill['capacity'] is None
assert parts[mill['upstreamNodes'][0]].intersects(parts[mill['upstreamNodes'][1]])
links=[r for r in review['structureRoutes'] if r['siteId']=='three-mills']
assert len(links)==1 and links[0]['a'] in mill['upstreamNodes'] and links[0]['b']==mill['downstreamNode']
assert 25<links[0]['distanceMetres']<27  # wider than the initial automatic gap search
lock=next(r for r in review['structureRoutes'] if r['siteId']=='bow-locks')
assert 15<lock['distanceMetres']<16 and lock['category']=='lock-passage'
six_inch=json.loads((crop_dir/'six-inch-review.json').read_text())
assert six_inch['layerId']=='six-inch-2nd'
for c in six_inch['areas'].values():
 assert hashlib.sha256((crop_dir/c['image']).read_bytes()).hexdigest()==c['imageSHA256']
 for path,digest in c['sourceTileHashes'].items():
  assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest
missing=next(f for f in review['networkReview']['findings'] if f['id']=='upper-channelsea-interruption')
assert abs(parts['Lower_River_Lea-10-part-0'].distance(parts['Lower_River_Lea-11-part-0'])-missing['endpointSeparationMetres'])<1e-6
out=ROOT/'scenes/channelsea-sewer-panorama/review';out.mkdir(parents=True,exist_ok=True)
(out/'lower-lea-region-data-checks.json').write_text(json.dumps({'status':'PASS','summary':d['summary'],'connectionReview':review['counts'],'checks':['source hashes','exact north-up source crop','missing terrain retained','2003 distinct from 1900','valid derived primary polygons','all polygon parts audited','reported gap distances','hydraulic links unreviewed','only existing controls applied','navigation contacts audited including zero-distance joins','mapping seams separate from hydraulic passage','unknown capacities and positions not fabricated','rejected proposal excluded','author map crops retained and hashed']},indent=2)+'\n')
print('Regional coverage data checks passed.')
