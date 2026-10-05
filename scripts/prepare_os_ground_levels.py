#!/usr/bin/env python3
"""Write data/maps/os-ground-levels.json: every OS five-foot spot height and bench
mark inside the core box, classified and assigned to the ground it measures.

Each reading (reference/spot-heights/heights.geojson, feet above OD Liverpool)
is converted to scene y with the project datum and given
- a category: 'ground' (a spot height on the ground surface: street, yard, marsh,
  open ground, bank foot, towing path), 'mark' (an OS bench mark, cut on a wall,
  post, building or bridge and standing above the ground) or 'structure' (a spot
  height on a bridge deck, wall or bank top, rail or building);
- a zone (for the report and the check);
- a use: 'premises' (the yard level of a ground-plan site whose premises pad the
  main landscape draws), 'street' (the level of a drawn street corridor), 'marsh'
  (open ground between works: the marsh correction), or 'none' with a reason.

The rules are below; DECISIONS lists every reading whose use differs from the
rule, with the reason. scripts/build_main_landscape.py reads the register;
scripts/check_os_ground_levels.mjs re-reads the spot heights and the drawn
ground. Deterministic: run again after the spot-height collection changes.
"""
import json
from pathlib import Path

import numpy as np
import shapely
from shapely.geometry import LineString, Point, Polygon
from scipy.ndimage import map_coordinates

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'data/maps/os-ground-levels.json'
CORE = [-1280, -240, 280, 1160]
DATUM = {'liverpoolToNewlynFeet': -1.3, 'footMetres': 0.3048, 'odnMinusSceneYMetres': 1.83544,
         'formula': 'scene y = (feet + liverpoolToNewlynFeet) x 0.3048 - odnMinusSceneYMetres',
         'source': 'docs/data/terrain-1900.json verticalReference (channelsea-crest-v1)'}
GROUND_SETTINGS = {'street', 'yard', 'marsh', 'open_ground', 'embankment_foot'}
STRUCTURE_SETTINGS = {'bridge', 'building', 'wall_top', 'embankment_top', 'railway'}
SUPPORT_MIN = .9          # High Street readings below this regional early-marsh weight are not applied (decision 1)
STREET_REACH_M = 6        # a street reading belongs to a drawn street within half its width + this
PREMISES_REACH_M = 1.5      # a yard reading belongs to a site pad within this distance of its outline

# Readings whose use differs from the rules, with the reason (evidence first, then interpretation).
GAS_RAMP = ('on the gas works road at the foot of the hatched approach embankment of the Bow Creek road bridge, which descends '
            'east across the works (21.1, 16.3 and 14.0 ft, then 5.6 ft at the east fence); the road and its ramp are not drawn and '
            'the works yard either side stands at 16-18 ft, so the reading is not the yard level')
SHORT_WALL = ('on the Short Wall, the lane along the top of the Lea river wall (16.9-17.9 ft, about 2.6 m above Mill Meads): '
              'the drawn Three Mills Wall lane lies inside the river network tidal outline, where the native bank heights are kept, '
              'so raising it to the OS means building the wall and bank under it (a structure; decision 4), not a street level')
DECISIONS = {
    'sh_538907_182862': {'category': 'ground', 'use': 'marsh', 'reason': "reader setting 'railway', but the note reads 'road north of railway': a road level beside the line, taken as ground by the railway level register (LT&SR control at chainage 664.6)"},
    'sh_538886_182938': {'use': 'none', 'reason': 'figures ambiguous (17.3 or 17.8 ft) and the dot not confirmed; 1.3 m above the B.M. 13.17 ft cut on the Abbey Mills Chemical Works building 18 m south-east (a bench mark stands above its ground), so not the works yard; probably on the river-wall bank (17.9 ft 30 m north)'},
    'sh_538462_182436': {'use': 'none', 'reason': GAS_RAMP},
    'sh_538592_182437': {'use': 'none', 'reason': GAS_RAMP},
    'sh_538640_182438': {'use': 'none', 'reason': 'marsh-level road outside the gas works fence, east of the hatched gasholder bank (low confidence); the ground-plan outline of site 924 reaches over it, so the works pad covers the reading'},
    'sh_538681_182464': {'use': 'none', 'reason': 'marsh-level road curving round the foot of the hatched gasholder bank, outside the works fence; the ground-plan outline of site 924 reaches over it, so the works pad covers the reading'},
    'sh_538735_182518': {'use': 'marsh', 'reason': 'marsh-level ground by the embankment outside the gas works fence (4 m beyond the site 924 outline), not the works yard'},
    'sh_538525_182269': {'use': 'none', 'reason': 'gas works made ground 9 m outside the ground-plan outline of site 924 (the OS works fence lies beyond the outline on the south-east side); not a marsh level, and the pad stops at the outline'},
    'sh_538572_182205': {'use': 'none', 'reason': 'gas works made ground (a dotted track by the B.M. 18.45 building) 6 m outside the ground-plan outline of site 924; not a marsh level, and the pad stops at the outline'},
    'sh_538316_183215': {'use': 'none', 'reason': 'on the Short Wall, the raised lane along the Lea bank, 30 m north of where the drawn Three Mills Wall lane begins; a lane level, not marsh ground'},
    'sh_538337_183143': {'use': 'none', 'reason': SHORT_WALL},
    'sh_538345_183055': {'use': 'none', 'reason': SHORT_WALL},
    'sh_539164_183422': {'category': 'structure', 'use': 'none', 'reason': 'on the walled band (a raised band between retaining walls) beside the Woolwich branch north of Abbey Road'},
    'sh_539156_183134': {'use': 'none', 'reason': 'Manor Road dips to 3.4 ft where it passes under the Northern Outfall Sewer aqueduct, beside the bank; a local road cutting under the aqueduct (Manor Road is 8.4 ft 73 m south), and Manor Road is not drawn here'},
    'sh_538851_183160': {'use': 'none', 'reason': 'on the strip between the Channelsea and the toe of the sewer bank, at the level of the river-bank crest beside it (18.9 ft, as the embankment-top reading sh_538858_183162 two metres away): a bank-top level, not marsh; as a marsh control it raised a 3.5 m mound over the mud flats'},
    'sh_538776_182863': {'use': 'none', 'reason': 'low confidence, dot not located; 1.6-1.8 m above the Abbey Creek Wharf readings (10.9-11.6 ft) 40-70 m south; probably on the end of the Long Wall bank at the wharf head'},
}

# Applied readings the drawn ground still misses by more than EXCEPTION_M, and why (T21 measurements;
# scripts/check_os_ground_levels.mjs holds every other applied reading to EXCEPTION_M).
EXCEPTION_M = 0.6
MESH20 = ('the 20 m regional ground mesh (main-landscape groundMesh) spans the gas works pad edge here with tilted '
          'triangles, so the drawn ground between its vertices does not follow the pad and its 1:1.5 batter')
EXCEPTIONS = {
    'sh_538735_182518': MESH20+' (4 m outside the site 924 outline)',
    'sh_538412_182627': MESH20+' (beside Bow Creek below the LT&SR embankment)',
    'sh_538279_182756': 'on the bank top 1.6 m from the drawn Lea water south of Three Mills Bridge: the model draws an earth bank face rising from the water edge over 3 m (T11/T14 bank band), where the OS level implies a quay or wall edge',
    'sh_538304_182814': 'Three Mills Lane at the east bank of the Lea: the Three Mills Lea bridge deck (road-traces, 2.2 m; OS 21.2 ft on the bridge, 4.23 m) ends 25 m short of the drawn east water edge, so the lane crosses drawn water and the bank face rises from it; the street level cannot be met until the bridge is re-levelled and lengthened (structure, decision 3)',
    'sh_538458_183000': 'between two parallel drains, inside the drawn marsh-ditch polygons (the strip between the drains is narrower than the drawn drains), where the native drain section is kept',
    'sh_538459_183075': 'between two parallel drains at their junction, inside the drawn marsh-ditch polygons, where the native drain section is kept',
    'sh_538508_182732': 'at the corner of the distillery grounds on the Channelsea edge: the river network tidal face rises at 1:1.5 from the drawn tidal shelf (T11), where the OS level implies a quay edge',
}


def scene_y(feet):
    return (feet+DATUM['liverpoolToNewlynFeet'])*DATUM['footMetres']-DATUM['odnMinusSceneYMetres']


def load(path):
    return json.loads((ROOT/path).read_text())


def category(p):
    if p['type'] == 'bench_mark':
        return 'mark'
    s = p.get('setting')
    if s in GROUND_SETTINGS:
        return 'ground'
    if s in STRUCTURE_SETTINGS:
        return 'structure'
    return 'ground'


def main():
    heights = load('reference/spot-heights/heights.geojson')
    plan = load('docs/data/ground-plan.json')
    infra = load('docs/data/infrastructure.json')
    meta = load('docs/data/lower-lea-region/landscape-1900.json')
    shape = (meta['height'], meta['width']); e0, n0, e1, n1 = meta['boundsBNG']; step = meta['cellSizeMetres']
    support = np.fromfile(ROOT/'docs/data/lower-lea-region'/meta['earlyMarshWeightFile'], '<f4').reshape(shape)

    def weight(x, z):
        rc = np.array([[(n1-(183209-z))/step-.5], [((538900+x)-e0)/step-.5]])
        return float(map_coordinates(support, rc, order=1, mode='constant', cval=0)[0])

    ltsr = LineString(next(r['route'] for r in infra['railways'] if r['name'].startswith('London, Tilbury')))
    high = LineString(next(r['route'] for r in infra['roads'] if r['name'] == 'Stratford High Street'))

    def zone(x, z):
        q = Point(x, z)
        if ltsr.distance(q) <= 35 and x > -640:
            return 'ltsr-corridor'
        if high.distance(q) <= 45:
            return 'high-street'
        if x < -628:
            return 'west-strip'
        if z > 620 and x < -150:
            return 'bromley-gasworks'
        if x < -300:
            return 'three-mills'
        if x < 120 and z < 340:
            return 'abbey-mills'
        if x >= 120:
            return 'channelsea-east'
        return 'abbey-marsh-south'

    sites = {s['id']: (s['name'], shapely.union_all([Polygon(p[0], p[1:]) for p in s['polygons']])) for s in plan['sites']}
    # Only sites the main landscape draws a premises pad for (centre inside the marsh support).
    padded = {i: v for i, v in sites.items()
              if weight(*list(v[1].representative_point().coords)[0]) > 0}
    streets = [(r['name'], LineString(r['route']), r['width']) for r in infra['roads'] if r.get('kind') != 'path' and len(r['route']) > 1]

    readings = []
    for f in sorted(heights['features'], key=lambda f: f['properties']['id']):
        p = f['properties']; x, z = p['bng_e']-538900, 183209-p['bng_n']
        if not (CORE[0] <= x <= CORE[2] and CORE[1] <= z <= CORE[3]):
            continue
        q = Point(x, z); w = weight(x, z); cat = category(p)
        item = {'id': p['id'], 'type': p['type'], 'setting': p.get('setting'), 'confidence': p['confidence'],
                'valueFeet': p['value_ft'], 'sceneY': round(scene_y(p['value_ft']), 3),
                'position': [round(x, 2), round(z, 2)], 'zone': zone(x, z), 'category': cat,
                'supportWeight': round(w, 3), 'notes': p.get('notes')}
        use, why = 'none', None
        if cat == 'mark':
            why = 'bench mark: cut on a wall, post, building or bridge above the ground it stands on; a check, not a ground level'
        elif cat == 'structure':
            why = f"spot height on a structure ({p.get('setting')}); not the ground"
        elif zone(x, z) == 'west-strip' or (zone(x, z) == 'high-street' and w < SUPPORT_MIN):
            why = 'outside the main landscape support: the terrace west of the Lea and Bow Creek and the High Street towards Bow Bridge are drawn as the earlier flat floor, 2-9 m below the OS; not applied (T21_REPORT.md decision 1)'
        else:
            road = None
            if p.get('setting') == 'street':
                near = sorted((line.distance(q), name) for name, line, width in streets if line.distance(q) <= width/2+STREET_REACH_M)
                if near:
                    road = near[0][1]
            site = None
            if road is None and p.get('setting') != 'marsh':
                near = sorted((g.distance(q), sid) for sid, (_, g) in padded.items())
                if near and near[0][0] <= PREMISES_REACH_M:
                    site = near[0][1]
            if road:
                use = 'street'; item['road'] = road
            elif site is not None:
                use = 'premises'; item['siteId'] = site; item['siteName'] = sites[site][0]
            else:
                use = 'marsh'
        if p['id'] in DECISIONS:
            d = DECISIONS[p['id']]
            use = d['use']; why = d.get('reason')
            if 'category' in d:
                item['category'] = d['category']
            for k in ('road', 'siteId', 'siteName'):
                item.pop(k, None)
            if 'road' in d:
                item['road'] = d['road']
            if 'siteId' in d:
                item['siteId'] = d['siteId']; item['siteName'] = sites[d['siteId']][0]
            item['decision'] = True
        item['use'] = use
        if why:
            item['reason'] = why
        if p['id'] in EXCEPTIONS:
            assert use != 'none', p['id']
            item['exception'] = EXCEPTIONS[p['id']]
        readings.append(item)

    premises = {}
    for r in readings:
        if r['use'] == 'premises':
            premises.setdefault(str(r['siteId']), {'name': r['siteName'], 'controlIds': []})['controlIds'].append(r['id'])
    road_controls = {}
    for r in readings:
        if r['use'] == 'street':
            road_controls.setdefault(r['road'], []).append(r['id'])
    register = {
        'description': 'Every OS London five-foot (1891-96) spot height and bench mark inside the core box, converted to scene y and assigned to the ground it measures. scripts/build_main_landscape.py draws premises pads from the premises readings, street corridors from the street readings and corrects the marsh between works to the marsh readings; scripts/check_os_ground_levels.mjs compares the drawn ground with every reading. Generated by scripts/prepare_os_ground_levels.py (rules and per-reading decisions there).',
        'coreBox': CORE, 'datum': DATUM,
        'source': 'reference/spot-heights/heights.geojson (layer os-london-five-foot-1893; readers\' setting, notes and confidence kept)',
        'rules': {
            'category': {'ground': 'spot height with setting street, yard, marsh, open_ground, embankment_foot, other or unset (towing path, works ground)',
                         'mark': 'bench mark (type bench_mark): the level of the mark, which stands above the ground',
                         'structure': 'spot height with setting bridge, building, wall_top, embankment_top or railway'},
            'support': f'ground readings in the west strip (x < -628) and High Street readings where the regional early-marsh support weight is below {SUPPORT_MIN} are not applied (decision 1); elsewhere the main landscape applies around each applied reading',
            'street': f'a street-setting reading within half the street width + {STREET_REACH_M} m of a drawn street (not a path) sets that street corridor (with the regional street readings)',
            'premises': f'any other non-marsh ground reading within {PREMISES_REACH_M} m of a ground-plan site the main landscape pads sets that pad',
            'marsh': 'remaining ground readings (marsh, open ground, bank feet, footpaths, undrawn tracks) correct the marsh between works',
        },
        'exceptionMetres': EXCEPTION_M,
        'zones': {'west-strip': 'x < -628 (the Bromley/Bow terrace west of the Lea and Bow Creek), outside the High Street band',
                  'high-street': 'within 45 m of the Stratford High Street centreline',
                  'three-mills': 'x -628..-300 north of z 620 (Three Mills, Mill Meads, Abbey Lane west)',
                  'abbey-mills': 'x -300..120, z < 340 (Abbey Mills, the pumping station, the Channelsea at Abbey Mills)',
                  'channelsea-east': 'x >= 120 (Abbey Road east, Manor Road, the Woolwich branch)',
                  'ltsr-corridor': 'within 35 m of the LT&SR centreline east of x -640',
                  'bromley-gasworks': 'x -628..-150, z > 620 (the Bromley gas works and the marsh east of it)',
                  'abbey-marsh-south': 'x -150..120, z > 340 (the marsh south of the LT&SR)'},
        'premises': premises, 'streets': road_controls,
        'readings': readings,
    }
    OUT.write_text(json.dumps(register, indent=1, ensure_ascii=False)+'\n')
    from collections import Counter
    print(Counter((r['zone'], r['use']) for r in readings))


if __name__ == '__main__':
    main()
