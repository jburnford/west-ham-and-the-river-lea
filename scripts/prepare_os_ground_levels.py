#!/usr/bin/env python3
"""Write data/maps/os-ground-levels.json: every OS five-foot spot height and bench
mark inside the core box and the Stratford zone north of it (task E, F1),
classified and assigned to the ground it measures.

Each reading (reference/spot-heights/heights.geojson, feet above OD Liverpool)
is converted to scene y with the project datum and given
- a category: 'ground' (a spot height on the ground surface: street, yard, marsh,
  open ground, bank foot, towing path), 'mark' (an OS bench mark, cut on a wall,
  post, building or bridge and standing above the ground) or 'structure' (a spot
  height on a bridge deck, wall or bank top, rail or building);
- a zone (for the report and the check);
- a use: 'premises' (the yard level of a ground-plan site whose premises pad the
  main landscape draws), 'street' (the level of a drawn street corridor), 'marsh'
  (open ground between works: the marsh correction), 'terrace' (open ground,
  undrawn streets and towing paths on the Bromley/Bow terrace west of the Lea and
  Bow Creek: the same correction of the regional ground), 'stratford' (any other
  ground reading in the Stratford zone north of the core: the same correction,
  task E F1), or 'none' with a reason.

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
SUPPORT_MIN = .9          # T21: High Street readings below this regional early-marsh weight were not applied (T21 decision 1)
# T22: the terrace zone, where the main landscape now draws the regional ground corrected to the OS readings
# (scripts/build_main_landscape.py TERRACE_ZONE): the core box west of x = -628 (T21's west strip; east of it T21's marsh rules apply
# unchanged).
TERRACE_ZONE = [-1280, -240, -628, 1160]
TERRACE_FEATHER_M = 60    # outside the core box the main landscape fades from the terrace over this band (west, north, south)
# Task E, F1 (author, 6 October 2026): the Stratford zone north of the core box, from the High Street to the Waterworks
# River flood gate and Temple Mills, where the rain-up-river flood plays out. The main landscape draws the regional
# ground there corrected to every OS ground reading on the drawn marsh (as T22 did on the terrace); readings where the
# regional early-marsh support is 0 (Stratford town and Hackney Wick on the terrace, which the model does not draw)
# are not applied. North of the zone the correction fades out over STRATFORD_FEATHER_M.
STRATFORD_ZONE = [-1800, -2450, -150, -240]
STRATFORD_FEATHER_M = 60
# Railways the OS draws at grade in the Stratford zone (no embankment or cutting hatching): the ground beside them is
# held at their formation less the 0.1 m at-grade lift (railway-levels.json atGrade), as rail_side_controls does in the
# core box. Chainages are along the railway as built in docs/data/infrastructure.json (its stations).
STRATFORD_AT_GRADE_RAILWAYS = [
    {'railwayId': 'north-london-connection', 'from': 495, 'to': 770,
     'evidence': 'OS five-foot plan: the Victoria Park Branch has no hatching from the east abutment of the Waterworks '
                 'River bridge (bridge ends at chainage 487) past Lea Junction to Channel Sea Junction; the hatched low bank '
                 'resumes on the High Meads curve at about 780. F1 fitted the ground here to the open-ground readings 30-100 m '
                 'south of the line (20.7 ft, 18.5 ft) and buried the tracks. The OS rail reading at Lea Junction (16.6 ft, '
                 'rail top 2.83 scene) puts the formation about 0.6 m under the kept 3.0; the formation is not changed here.'},
]
STREET_REACH_M = 6        # a street reading belongs to a drawn street within half its width + this
PREMISES_REACH_M = 1.5      # a yard reading belongs to a site pad within this distance of its outline

# Readings whose use differs from the rules, with the reason (evidence first, then interpretation).
GAS_RAMP = ('on the gas works road at the foot of the hatched approach embankment of the Bow Creek road bridge, which descends '
            'east across the works (21.1, 16.3 and 14.0 ft, then 5.6 ft at the east fence); the road and its ramp are not drawn and '
            'the works yard either side stands at 16-18 ft, so the reading is not the yard level')
SHORT_WALL = ('on the Short Wall, the lane along the top of the Lea river wall (16.9-17.9 ft, about 2.6 m above Mill Meads): '
              'the drawn Three Mills Wall lane lies inside the river network tidal outline, where the native bank heights are kept, '
              'so raising it to the OS means building the wall and bank under it (a structure; decision 4), not a street level')
TOWING_PATH = ('towing path along the river bank: the reader set embankment_top (the path runs on the bank top above the '
               'water), but the path is the ground surface beside the river, and the bank crest the main landscape draws '
               'from the high-confidence bank-top readings stands at it; applied as terrace ground (T22)')
RAILS_IN_YARD = ('rails at grade in the East London Soap Works yard (the reader set railway: "taken as rails at grade in the works '
                 'yard"); a works siding laid in the yard surface, so the reading is the yard level; applied as terrace ground (T22)')
DECISIONS = {
    'sh_537671_183381': {'category': 'ground', 'use': 'terrace', 'reason': RAILS_IN_YARD},
    'sh_537723_183428': {'category': 'ground', 'use': 'terrace', 'reason': RAILS_IN_YARD+'; at the foot of the G.E.R. bank by a works building'},
    'sh_538149_182179': {'category': 'structure', 'use': 'none', 'reason': 'St Leonard\'s Street on Four Mills Bridge over the Limehouse Cut (OS: the street crosses the Cut here; Bromley Lock beside it): a bridge-deck level; the model draws neither the street nor the bridge here, only the Cut water (T22)'},
    'sh_537975_183046': {'category': 'ground', 'use': 'terrace', 'reason': TOWING_PATH},
    'sh_538047_183035': {'category': 'ground', 'use': 'terrace', 'reason': TOWING_PATH},
    'sh_538057_182062': {'category': 'ground', 'use': 'terrace', 'reason': TOWING_PATH+' (Limehouse Cut)'},
    'sh_538072_183022': {'category': 'ground', 'use': 'terrace', 'reason': TOWING_PATH},
    'sh_538085_182100': {'category': 'ground', 'use': 'terrace', 'reason': TOWING_PATH+' (Limehouse Cut)'},
    'sh_538087_182975': {'category': 'ground', 'use': 'terrace', 'reason': TOWING_PATH},
    'sh_538128_182907': {'category': 'ground', 'use': 'terrace', 'reason': TOWING_PATH},
    'sh_538201_182860': {'category': 'ground', 'use': 'terrace', 'reason': TOWING_PATH},
    'sh_538236_182814': {'category': 'ground', 'use': 'terrace', 'reason': TOWING_PATH},
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
    'sh_538088_183603': {'use': 'none', 'reason': 'no survey dot found (position = the figures, medium confidence) and the figures fall inside the drawn City Mill River, 2.4 m from its edge; "by Laboratory Yard", whose ground the reading cannot place (task E, F1)'},
    'sh_537108_184276': {'use': 'none', 'reason': 'Hertford Union Canal towing path at the head of Bottom Lock (medium confidence), west of the Lea Navigation, 7 m from the canal: the regional early-marsh support is 0.09 here, at the edge of the drawn marsh, and the support is not extended within 15 m of mapped water (task E, F1), so the model does not draw this ground'},
    'sh_538584_183464': {'use': 'none', 'reason': 'low confidence: the second digit is ambiguous (8 or 6) and the dot was not located; it would set the West Ham Gas Works pad (site 873) at 0.45 m on a single uncertain figure (task E, F1)'},
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
    'sh_538304_182814': 'Three Mills Lane at the east bank of the Lea: the Three Mills Lea bridge deck (T22: re-levelled to the OS 21.2 ft, 4.23 m; prior 2.2 m) ends 25 m short of the drawn east water edge, so the lane crosses drawn water and the bank face rises from it; the street level cannot be met until the bridge is lengthened (structure, T21 decision 3)',
    'sh_538458_183000': 'between two parallel drains, inside the drawn marsh-ditch polygons (the strip between the drains is narrower than the drawn drains), where the native drain section is kept',
    'sh_538459_183075': 'between two parallel drains at their junction, inside the drawn marsh-ditch polygons, where the native drain section is kept',
    'sh_538508_182732': 'at the corner of the distillery grounds on the Channelsea edge: the river network tidal face rises at 1:1.5 from the drawn tidal shelf (T11), where the OS level implies a quay edge',
    # T22: the terrace west of the Lea and Bow Creek (measured on the T22 build).
    'sh_538201_182860': 'towing path on the Lea west bank, but inside the drawn river (GIS channel outline), 4 m from its edge: the drawn water is wider than the OS channel here, so the reading falls on the channel bed',
    'sh_538085_182100': 'Limehouse Cut towing path 1.0 m from the drawn Cut edge: the coarse river-system bank triangles span from the canal-face coping to the bank behind, so the drawn surface at the dot lies between them',
    'sh_538236_182814': 'towing path dot 1.2 m from the drawn Lea water edge: the model draws a 3 m earth bank face from the water edge to the bank crest (T11/T14 bank band); the crest itself stands at the OS level 2-3 m back',
    'sh_538047_183035': 'towing path dot 1.5 m from the drawn Lea water edge, on the 3 m earth bank face; the crest stands at the OS level behind it',
    'sh_538072_183022': 'towing path dot 1.5 m from the drawn Lea water edge, on the 3 m earth bank face; the crest stands at the OS level behind it',
    'sh_538128_182907': 'towing path dot 1.9 m from the drawn Lea water edge, on the 3 m earth bank face; the crest stands at the OS level behind it',
    'sh_537628_183260': 'Old Ford towing path inside the bank band (within 14 m of the regional shoreline), where the model draws the regional bank crest (2.98 m, interpolated along the bank from bank-top readings elsewhere); the OS towing path below the Old Ford Road slope is 0.7 m lower',
    'sh_537671_183228': 'Old Ford towing path inside the bank band, where the model draws the regional bank crest (2.98 m); the OS towing path is 0.9 m lower',
    # Task E, F1: the Stratford zone north of the core (measured on the F1 build).
    'sh_538638_184032': 'road by Channel Sea Court, but 0.2 m inside the drawn Channelsea outline (the drawn water is wider than the OS channel here), so the reading falls on the channel bed',
    'sh_537676_184472': 'enclosure corner 0.6 m from the drawn Waterworks River edge, on the 3 m earth bank face the bank band draws from the water edge',
    'sh_537688_185311': 'path at a field edge 0.2 m from the drawn water edge at Temple Mills, on the bank face',
    'sh_537617_185329': 'ground at the B.M. 18.08 pheon, 1.9 m from the drawn Waterworks River edge, on the bank face (medium confidence: no dot of its own)',
    'sh_537578_183470': 'Lea towing path at the north face of the G.E.R. bridge west of the core box: on the river-network bank face of the Lea, which keeps its native section there',
    'sh_537932_183520': 'lane beside the Pudding Mill River west of the Rope Works, inside the river-network tidal outline (3 m from the drawn channel), where the native shelf heights are kept (as the Short Wall lane in the core)',
    'sh_537982_183457': 'lane opposite the Brush & Fibre Works, inside the river-network tidal outline 4 m from the drawn channel, where the native shelf heights are kept',
    'sh_537888_183583': 'lane south from the G.E.R. bridge, 5 m from the drawn Pudding Mill River, on the bank face beside the river-network tidal outline',
    'sh_538145_183543': 'lane east of Marshgate Lane Works, 5 m from the drawn City Mill River, on the bank face beside the river-network tidal outline',
    'sh_538530_183620': 'Union Street junction 4.4 m outside the West Ham Gas Works premises pad (site 873, a T21 marsh-supported estimate at 0.15 m with no OS yard reading): the pad\'s 1:1.5 edge batter draws the junction down to it',
    'sh_537369_183796': 'Lea towing path at the Old Ford, 2.5 m from the drawn water, inside the bank band where the model draws the regional bank crest; the OS towing path is lower',
    'sh_537632_183892': 'track by the Bone Works on the bank edge, 7 m from the drawn water, inside the bank band where the model draws the regional bank crest',
    'sh_538516_183577': 'Stanley Road (medium confidence), 9.5 m from the Stanley Road gasworks junction corridor: on the 1:1.5 batter from that corridor\'s own street level',
    'sh_538666_183895': 'Channel Sea Road at its north end, 7 m from the North Street corridor and below the High Street causeway: on the 1:1.5 batters from those streets\' own levels',
    'sh_537524_183535': 'towing path north of the railway bridge by the Bow Goods Station, '+'at the edge of the drawn marsh beside water: the regional early-marsh support is 0.43 here and the Stratford support extension stops 15 m from mapped water (a raised weight beside a channel the meshes do not draw put a sill across it), so the drawn ground is only partly the corrected landscape',
    'sh_538531_184294': 'beside the G.E.R. Woolwich Branch bridge (the note puts the dot by the parapet), '+'at the edge of the drawn marsh beside water: the regional early-marsh support is 0.57 here and the Stratford support extension stops 15 m from mapped water (a raised weight beside a channel the meshes do not draw put a sill across it), so the drawn ground is only partly the corrected landscape',
    'sh_538536_184373': 'open ground by the Foot Bridge south of Stratford Low Level, '+'at the edge of the drawn marsh beside water: the regional early-marsh support is 0.25 here and the Stratford support extension stops 15 m from mapped water (a raised weight beside a channel the meshes do not draw put a sill across it), so the drawn ground is only partly the corrected landscape',
    'sh_537296_183634': 'Old Ford Road by the Smithy on the terrace west of the Lea, at the edge of the regional marsh outline: the next reading up the road (6.94 m, 87 m north) lies beyond it and is not applied, so the correction has no control on that side and the drawn ground falls towards the regional ground',
    'sh_537161_185652': 'open Hackney Marsh inside the Lea meander, 6.6 m from the drawn Lea, inside the bank band where the model draws the regional bank crest of the Temple Mills Road approach',
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
    # The regional marsh outline: the ground the main landscape mesh draws (task E, F1).
    outline = Polygon([(e-538900, 183209-n) for e, n in meta['regionalMarshBaseline']['config']['outlineBNG']])

    def weight(x, z):
        rc = np.array([[(n1-(183209-z))/step-.5], [((538900+x)-e0)/step-.5]])
        return float(map_coordinates(support, rc, order=1, mode='constant', cval=0)[0])

    ltsr = LineString(next(r['route'] for r in infra['railways'] if r['name'].startswith('London, Tilbury')))
    high = LineString(next(r['route'] for r in infra['roads'] if r['name'] == 'Stratford High Street'))
    high_north = shapely.union_all([LineString(r['route']) for r in infra['roads'] if r['name'].startswith('Stratford High Street')])

    def zone(x, z):
        q = Point(x, z)
        if in_stratford(x, z):
            if high_north.distance(q) <= 45:
                return 'stratford-high-street'
            return 'temple-mills' if z < -1800 else 'stratford-marsh'
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
    def in_terrace(x, z):
        return TERRACE_ZONE[0] <= x <= TERRACE_ZONE[2] and TERRACE_ZONE[1] <= z <= TERRACE_ZONE[3]

    def in_stratford(x, z):
        # The zone lies north of the core box (it shares the core's north edge, which stays with the core).
        return STRATFORD_ZONE[0] <= x <= STRATFORD_ZONE[2] and STRATFORD_ZONE[1] <= z < STRATFORD_ZONE[3]

    def centre(g):
        return list(g.representative_point().coords)[0]

    # Sites the main landscape draws a premises pad for: centre inside the marsh support and outside the terrace
    # zone and its feather band (T21's rule). Inside them (T22) a site is padded only where the OS gives its yard level:
    # a yard-setting reading within PREMISES_REACH_M of its outline; its other ground is the OS-corrected terrace.
    def in_terrace_band(x, z):
        # the zone and its feather band outside the core box (build_main_landscape.py terrace_weight > 0)
        zx0, zz0, zx1, zz1 = TERRACE_ZONE
        return x <= zx1 and zx0-TERRACE_FEATHER_M < x and zz0-TERRACE_FEATHER_M < z < zz1+TERRACE_FEATHER_M

    padded = {i: v for i, v in sites.items() if weight(*centre(v[1])) > 0 and not in_terrace_band(*centre(v[1]))}
    terrace_sites = {i: v for i, v in sites.items() if in_terrace_band(*centre(v[1]))}
    streets = [(r['name'], LineString(r['route']), r['width']) for r in infra['roads'] if r.get('kind') != 'path' and len(r['route']) > 1]

    readings = []
    for f in sorted(heights['features'], key=lambda f: f['properties']['id']):
        p = f['properties']; x, z = p['bng_e']-538900, 183209-p['bng_n']
        if not (CORE[0] <= x <= CORE[2] and CORE[1] <= z <= CORE[3]) and not in_stratford(x, z):
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
        elif in_stratford(x, z) and (w <= 0 or not outline.contains(q)):
            why = ('outside the drawn marsh: ' + ('the regional early-marsh support is 0 here' if w <= 0 else 'beyond the regional marsh outline, the ground the landscape mesh draws')
                   + ' (Stratford town or Hackney Wick on the terrace, or the Lea Navigation banks beyond the modelled ground), which the model does not draw (task E, F1)')
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
                elif p.get('setting') == 'yard':
                    near = sorted((g.distance(q), sid) for sid, (_, g) in terrace_sites.items())
                    if near and near[0][0] <= PREMISES_REACH_M:
                        site = near[0][1]
            if road:
                use = 'street'; item['road'] = road
            elif site is not None:
                use = 'premises'; item['siteId'] = site; item['siteName'] = sites[site][0]
            elif in_terrace(x, z) and (zone(x, z) == 'west-strip' or (zone(x, z) == 'high-street' and w < SUPPORT_MIN)):
                use = 'terrace'
            elif in_stratford(x, z):
                use = 'stratford'
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
        'description': 'Every OS London five-foot (1891-96) spot height and bench mark inside the core box and the Stratford zone north of it (task E, F1), converted to scene y and assigned to the ground it measures. scripts/build_main_landscape.py draws premises pads from the premises readings, street corridors from the street readings and corrects the marsh between works to the marsh readings; scripts/check_os_ground_levels.mjs compares the drawn ground with every reading. Generated by scripts/prepare_os_ground_levels.py (rules and per-reading decisions there).',
        'coreBox': CORE, 'datum': DATUM,
        'source': 'reference/spot-heights/heights.geojson (layer os-london-five-foot-1893; readers\' setting, notes and confidence kept)',
        'rules': {
            'category': {'ground': 'spot height with setting street, yard, marsh, open_ground, embankment_foot, other or unset (towing path, works ground)',
                         'mark': 'bench mark (type bench_mark): the level of the mark, which stands above the ground',
                         'structure': 'spot height with setting bridge, building, wall_top, embankment_top or railway'},
            'support': f'T21 left the west strip (x < -628) and the High Street readings where the regional early-marsh support weight is below {SUPPORT_MIN} unapplied (T21 decision 1); since T22 the main landscape applies over the whole terrace zone {TERRACE_ZONE} (the core box west of x -628), and elsewhere around each applied reading',
            'street': f'a street-setting reading within half the street width + {STREET_REACH_M} m of a drawn street (not a path) sets that street corridor (with the regional street readings)',
            'premises': f'any other non-marsh ground reading within {PREMISES_REACH_M} m of a ground-plan site the main landscape pads (centre in the marsh support, outside the terrace zone) sets that pad; inside the terrace zone a yard-setting reading within {PREMISES_REACH_M} m of a site sets (and creates) its pad',
            'marsh': 'remaining ground readings (marsh, open ground, bank feet, footpaths, undrawn tracks) correct the marsh between works',
            'terrace': 'remaining ground readings in the west strip, and High Street readings below the T21 support threshold, inside the terrace zone (open ground, streets the model does not draw, towing paths, yards of sites without a pad) correct the regional terrace ground in the same way',
            'stratford': f'task E, F1: inside the Stratford zone {STRATFORD_ZONE} (north of the core box, the High Street to Temple Mills) every ground reading on the drawn marsh that is not a street or premises reading (marsh, open ground, made ground, yards, undrawn tracks and streets, bank feet) corrects the regional ground, as on the terrace; street and premises readings there are controls of the same correction too; readings where the regional early-marsh support is 0 are not applied',
        },
        'exceptionMetres': EXCEPTION_M,
        'terraceZone': TERRACE_ZONE, 'terraceFeatherMetres': TERRACE_FEATHER_M,
        'stratfordZone': STRATFORD_ZONE, 'stratfordFeatherMetres': STRATFORD_FEATHER_M,
        'stratfordAtGradeRailways': STRATFORD_AT_GRADE_RAILWAYS,
        'zones': {'west-strip': 'x < -628 (the Bromley/Bow terrace west of the Lea and Bow Creek), outside the High Street band',
                  'high-street': 'within 45 m of the Stratford High Street centreline',
                  'three-mills': 'x -628..-300 north of z 620 (Three Mills, Mill Meads, Abbey Lane west)',
                  'abbey-mills': 'x -300..120, z < 340 (Abbey Mills, the pumping station, the Channelsea at Abbey Mills)',
                  'channelsea-east': 'x >= 120 (Abbey Road east, Manor Road, the Woolwich branch)',
                  'ltsr-corridor': 'within 35 m of the LT&SR centreline east of x -640',
                  'bromley-gasworks': 'x -628..-150, z > 620 (the Bromley gas works and the marsh east of it)',
                  'abbey-marsh-south': 'x -150..120, z > 340 (the marsh south of the LT&SR)',
                  'stratford-high-street': 'Stratford zone (north of the core box): within 45 m of the Stratford High Street centrelines',
                  'stratford-marsh': 'Stratford zone, z -1800..-240: Stratford Marsh, the Carpenters Road district, the back rivers north of the High Street',
                  'temple-mills': 'Stratford zone, z < -1800: Temple Mills and the head of the Waterworks River and the Channelsea'},
        'premises': premises, 'streets': road_controls,
        'readings': readings,
    }
    OUT.write_text(json.dumps(register, indent=1, ensure_ascii=False)+'\n')
    from collections import Counter
    print(Counter((r['zone'], r['use']) for r in readings))


if __name__ == '__main__':
    main()
