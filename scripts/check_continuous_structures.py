"""Verify full feature coverage, chainage interpolation, spans and source roles."""
import json
from pathlib import Path
import numpy as np
import shapely
from shapely.geometry import LineString, Polygon
from regional_continuous_structures import continuous_profile, polygon_bng, Banks

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/data/lower-lea-region'
meta=json.loads((OUT/'landscape-1900.json').read_text());c=meta['continuousStructures'];mesh=c['fineMesh']
network=json.loads((ROOT/'docs/data/river-system-1900.json').read_text())
audit=json.loads((OUT/'elevation-audit.json').read_text());infra=json.loads((ROOT/'docs/data/infrastructure.json').read_text())
water=shapely.union_all([polygon_bng(r['polygons']) for r in network['reaches']])
exclusions=shapely.union_all([water,*[Polygon(r['polygonBNG']) for r in audit['terrainExclusions']]])
positions=np.fromfile(OUT/mesh['positionFile'],'<f4').reshape(-1,3)
kinds=np.fromfile(OUT/mesh['kindFile'],'u1')
assert len(positions)==mesh['vertexCount'] and len(kinds)==len(positions)
assert len(positions)%3==0 and np.isfinite(positions).all()
assert set(kinds)=={12,13,15}
xy=np.column_stack([positions[:,0]+mesh['originBNG'][0],mesh['originBNG'][1]-positions[:,2]])
# Use float64 before restoring BNG offsets; float32 BNG would lose centimetres.
xy=np.column_stack([positions[:,0].astype(float)+mesh['originBNG'][0],mesh['originBNG'][1]-positions[:,2].astype(float)])
window=shapely.box(*meta['boundsBNG']);footprints={}
for f in c['features']:
    footprint=shapely.from_geojson(f['footprintGeoJSON']);footprints[f['name']]=footprint
    start,end=f['vertexStart'],f['vertexStart']+f['vertexCount']
    assert (kinds[start:end]==f['kind']).all()
    triangles=shapely.polygons(xy[start:end].reshape(-1,3,2))
    # Equal covered area detects omitted flat crests or missing bands.
    assert abs(shapely.area(triangles).sum()-footprint.area)<max(1,footprint.area*1e-5),(f['name'],'mesh area')
    if not f['elevatedWaterCrossing']:
        assert footprint.intersection(exclusions).area<1e-5,f['name']
        assert not shapely.intersects(triangles,exclusions.buffer(-.003)).any(),f['name']
    else:
        assert f['kind']==15 and f['cells']==0
# Every centreline metre is represented by earthworks or a separate bridge.
for p in c['railProfiles']+[c['sewerProfile']]:
    name=p.get('name','Northern Outfall Sewer');line=LineString(p['routeBNG'])
    full=shapely.union_all([g for n,g in footprints.items() if n.startswith(name)])
    missing=line.intersection(window).difference(full.buffer(.002))
    assert missing.length<.01,(name,missing.length,missing.wkt[:180])
# River/canal banks follow the union shoreline, not dots or polygon joins.
bank=footprints['Continuous river and canal banks'];config=c['policy']
openings=shapely.union_all([LineString([(538900+x,183209-z) for x,z in l]) for l in network['bankSections']['openBoundaries']])
expected=water.buffer(config['bankBaseWidthMetres']).difference(water).difference(openings.buffer(config['bankBaseWidthMetres']+.1)).intersection(window).difference(exclusions)
assert bank.symmetric_difference(expected).area<.01
# No decline to marsh between sparse observations or just beyond an endpoint.
assert np.allclose(continuous_profile([100,900],[4.,6.],np.array([0,100,500,900,1200]),1200),[4,4,5,6,6])
assert np.allclose(continuous_profile([100,900],[4.,6.],np.array([0,100,900,1000]),1000,True),[5,4,6,5])
banks=Banks(network,audit,config)
long_intervals=0
for j,p in enumerate(c['bankProfiles']):
    controls=sorted(p['controls'],key=lambda r:r['chainageMetres'])
    for a,b in zip(controls,controls[1:]):
        if b['chainageMetres']-a['chainageMetres']<=180:continue
        point=LineString(p['routeBNG']).interpolate((a['chainageMetres']+b['chainageMetres'])/2)
        # Quantitative interpolation uses unsimplified source shore geometry.
        exact=banks.lines[j].interpolate((a['chainageMetres']+b['chainageMetres'])/2)
        value=banks.crest(np.array([[exact.x,exact.y]]))[0]
        assert abs(value-(a['heightODNMetres']+b['heightODNMetres'])/2)<1e-5
        long_intervals+=1
assert long_intervals>10
# Preserve the original graded junctions instead of replacing them by constants.
for p in c['railProfiles']:
    r=next(r for r in infra['railways'] if r['name']==p['name'])
    if r.get('stations'):
        assert np.allclose(p['existingGradeODNMetres'],np.array(r['stations'])[:,2]+meta['verticalReference']['odnMinusSceneYMetres'])
assert 'sh_538907_182862' not in c['usedSourceIds'], 'Footpath alongside railway is not formation'
assert c['sewerProfile']['crestWidthMetres']==15
assert c['sewerProfile']['highStreetCoverODNMetres']<c['sewerProfile']['nominalCrestODNMetres']
print(f'PASS: {long_intervals} bank intervals longer than 180 m; complete mapped rail/sewer centrelines; full crest mesh area; explicit bridge spans; open waterways; retained junction grades; excluded footpath control.')
