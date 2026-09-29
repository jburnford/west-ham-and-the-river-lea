"""Stage the author's prototype readings without assigning a Newlyn or scene height.

Source observations remain untouched. Surface categories are provisional routing
for review, not verification of Claude's readings or their absolute positions.
"""
import json
import math
from collections import Counter
from pathlib import Path
from pyproj import Transformer

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'reference/spot-heights/readings.geojson'
OUT=ROOT/'reference/topography-research-2026-09-28/historic-controls'
OUT.mkdir(parents=True,exist_ok=True)
data=json.loads(SOURCE.read_text())
project=Transformer.from_crs(4326,27700,always_xy=True)
# Explicitly described low ground only; do not route every non-benchmark to DTM.
low_ground={'sh022','sh033','sh034','sh037'}
drain_banks={f'sh{i:03}' for i in range(72,78)}
features=[]
errors=[]
for feature in data['features']:
    p=dict(feature['properties'])
    e,n=project.transform(*feature['geometry']['coordinates'])
    delta=math.hypot(e-p['bng_e'],n-p['bng_n'])
    errors.append(delta)
    assert delta<.1,(p['id'],delta)
    text=p['notes'].lower()
    if p['type']=='bench_mark': surface='benchmark_mount_unresolved'
    elif p['id'] in low_ground:surface='low_ground_candidate'
    elif p['id'] in drain_banks:surface='drain_bank_or_water_mark_review'
    elif 'sewer' in text and 'top' in text:surface='sewer_crest_candidate'
    elif any(s in text for s in ['wall','bank','towpath','towing path','footpath']):surface='bank_or_path_candidate'
    elif any(s in text for s in ['street','road','lane','bridge','yard','gate']):surface='road_yard_or_structure_candidate'
    else:surface='unresolved'
    p.update({
        'sourceFile':'reference/spot-heights/readings.geojson',
        'height_m_liverpool':round(p['value_ft']*.3048,6),
        'height_m_odn':None,'scene_y':None,
        'scene_x':round(p['bng_e']-538900,2),'scene_z':round(183209-p['bng_n'],2),
        'datumStatus':'Liverpool per prototype; no Newlyn correction or scene vertical alignment',
        'surfaceReviewClass':surface,
        'terrainInterpolationEnabled':False,
        'positionStatus':'Prototype reports ±3 m with visible dot, ±5–10 m otherwise; per-point positional confidence not yet structured',
    })
    features.append({'type':'Feature','properties':p,'geometry':feature['geometry']})
assert len({f['properties']['id'] for f in features})==len(features)
report={
    'source':str(SOURCE.relative_to(ROOT)),'features':len(features),
    'types':dict(Counter(f['properties']['type'] for f in features)),
    'confidence':dict(Counter(f['properties']['confidence'] for f in features)),
    'surfaceReviewClasses':dict(Counter(f['properties']['surfaceReviewClass'] for f in features)),
    'maxCoordinateRoundTripErrorMetres':max(errors),
    'note':'Coordinate consistency is not map registration accuracy. Values and interpretations have not been independently reread.',
    'nextSteps':['Separate value confidence from dot/position confidence.',
                 'Resolve ambiguous drain marks before using them as land or water controls.',
                 'Determine benchmark mounting context before treating a mark as ground.',
                 'Verify Liverpool datum and local Newlyn relation before comparing absolute elevations.',
                 'Replace the 0–40 ft hard range with regional plausibility flags; NE relief can exceed 40 ft.',
                 'Use independent reviewed samples to estimate extraction accuracy; repeated crops are not independent evidence.']}
(OUT/'prototype-controls.geojson').write_text(json.dumps({'type':'FeatureCollection','name':'prototype-historical-height-controls','features':features},indent=2)+'\n')
(OUT/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
