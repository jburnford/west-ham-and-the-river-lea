"""Railway formation level profiles from data/maps/railway-levels.json.

The register gives, per railway in the core box, a profile [chainage, formation y,
basis] taken from OS rail-level, bank-top and ground readings, and (for the
LT&SR and the Abbey Mills curve) a revised route. build_infrastructure.py calls
apply() on each plain railway record; the result carries the profile so the
landscape, bridge, yard and drainage builders and docs/infrastructure.js read
one set of levels. Railways without a register entry are returned unchanged.
"""
import json
from pathlib import Path

import numpy as np
from shapely.geometry import LineString, Point

ROOT = Path(__file__).resolve().parents[1]
REGISTER = 'data/maps/railway-levels.json'


def load():
    return json.loads((ROOT/REGISTER).read_text())


def scene_y(feet, datum):
    return (feet + datum['liverpoolToNewlynFeet'])*datum['footMetres']-datum['odnMinusSceneYMetres']


def profile_arrays(profile):
    """(chainage, formation) arrays of a register or built profile."""
    if isinstance(profile, dict):
        return np.asarray(profile['chainage'], float), np.asarray(profile['formation'], float)
    return np.array([p[0] for p in profile], float), np.array([p[1] for p in profile], float)


def formation_at(rail, s):
    """Formation level at chainage s (scalar or array) along a built railway record."""
    profile = rail.get('levelProfile')
    if not profile:
        return np.full(np.shape(s), rail['formationHeight'], float) if np.ndim(s) else float(rail['formationHeight'])
    c, f = profile_arrays(profile)
    return np.interp(s, c, f)


def formation_at_point(rail, x, z):
    line = LineString(rail['route'])
    return float(formation_at(rail, line.project(Point(x, z))))


def apply(rail, register=None):
    """Route and level profile for a plain railway record; unchanged if not in the register."""
    reg = register or load()
    spec = reg['railways'].get(rail['name'])
    if spec is None:
        return rail
    out = dict(rail)
    if 'route' in spec:
        assert spec['priorRoute'] == rail['route'], f"{rail['name']}: register priorRoute differs from the traced route"
        out['route'] = spec['route']
        out['priorRoute'] = spec['priorRoute']
        out['routeEvidence'] = spec['routeEvidence']
    c, f = profile_arrays(spec['profile'])
    assert np.all(np.diff(c) > 0), f"{rail['name']}: profile chainages must increase"
    length = LineString(out['route']).length
    assert c[0] <= 1e-6 and abs(c[-1]-length) < .5, (rail['name'], c[0], c[-1], length)
    out['priorFormationHeight'] = spec['priorFormationHeight']
    out['formationHeight'] = round(float(f.max()), 3)
    out['levelProfile'] = {'chainage': c.tolist(), 'formation': f.tolist(),
                           'basis': [p[2] for p in spec['profile']],
                           'railTopAboveFormation': reg['railStack']['railTopAboveFormationMetres'],
                           'crestHalfWidth': reg['embankment']['crestHalfWidthMetres'],
                           'sideSlope': reg['embankment']['sideSlopeHorizontalPerVertical'],
                           'register': REGISTER,
                           'segments': spec['segments']}
    return out


def bank_level(crest, distance, crest_half, side, toe):
    """Embankment surface: the crest out to crest_half, then falling at 1 in `side` to the toe level."""
    return np.maximum(toe, crest-np.maximum(0, distance-crest_half)/side)


def level_stations(rail):
    """[x, z, formation, chainage] at every route vertex and profile point, in chainage order."""
    line = LineString(rail['route'])
    c, f = profile_arrays(rail['levelProfile'])
    vertex = [line.project(Point(p)) for p in rail['route']]
    stations = sorted({round(float(s), 3) for s in [*vertex, *c] if -1e-6 <= s <= line.length+1e-6})
    out = []
    for s in stations:
        p = line.interpolate(s)
        out.append([round(p.x, 3), round(p.y, 3), round(float(np.interp(s, c, f)), 3), s])
    return out
