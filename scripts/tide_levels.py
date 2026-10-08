"""Tide levels, tidal limit and mud flats from data/maps/os-tide-levels.json.

Shared by build_river_network.py and build_river_terrain.py so the network and
the detailed core use the same levels and meet at the same seam.
"""
import json
from pathlib import Path

import numpy as np
import shapely
from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT/'data/maps/os-tide-levels.json'
raw = json.loads(REGISTER.read_text())
LOW = raw['lowWater']['sceneY']
HIGH = raw['highWater']['sceneY']
RETAINED = raw['retainedLevel']['sceneY']
CREST = raw['tidalBankCrest']['sceneY']
ABOVE_TIDAL_LIMIT = set(raw['tidalLimit']['aboveTidalLimitChannelIds'])
S = raw['sections']
BED_EDGE = LOW+S['bedEdgeAboveLowWaterMetres']
BED_FLOOR = LOW-S['bedDepthBelowLowWaterMetres']
SEAM_BED = LOW-S['seamBelowLowWaterMetres']
MUD_TOP = HIGH-S['mudTopBelowHighWaterMetres']
WALL_BASE = LOW-S['wallBaseBelowLowWaterMetres']
flats = unary_union([Polygon(f['polygon']) for f in raw['mudFlats']])
shapely.prepare(flats)
# Traced high-water lines on the landward side of a flat, where it meets its bank (task D).
high_water_lines = unary_union([LineString(line) for f in raw['mudFlats'] for line in f.get('highWaterLines', [])])
RIM_TOP = HIGH-.06  # just under the water, as the core caps its mud (build_river_terrain.py)
# Silted back-river beds above low water (data/maps/back-river-beds.json, task E F2).
BACK_RIVER_REGISTER = ROOT/'data/maps/back-river-beds.json'
back_rivers = json.loads(BACK_RIVER_REGISTER.read_text())
BACK_RIVER_PROFILE = back_rivers['profile']
# Channel id -> metres its thalweg stands above the outlet-to-head profile (the Pudding Mill River's extra silt).
BACK_RIVER_ABOVE = {i: g['aboveProfileMetres'] for g in back_rivers['groups'] for i in g['channelIds']}
BACK_RIVER_STREAM = {i: g['streamDepthMetres'] for g in back_rivers['groups'] for i in g['channelIds']}
BACK_RIVER_MAX_FLOOR = BACK_RIVER_PROFILE['headSceneY']+max(BACK_RIVER_ABOVE.values())
BACK_RIVER_SECTION = back_rivers['section']
BACK_RIVER_EDGE = BACK_RIVER_SECTION['edgeAboveFloorMetres']


def smooth(a, b, v):
    t = np.clip((v-a)/(b-a), 0, 1)
    return t*t*(3-2*t)


def tidal_bed(inside):
    """Bed inside the mapped (low-water) outline, by distance in from the shore."""
    return BED_EDGE+(BED_FLOOR-BED_EDGE)*smooth(0, S['bedRampMetres'], inside)


def silted_bed(inside, floor, ramp=None):
    """Back-river bed inside the mapped outline: falling evenly from edgeAboveFloorMetres above the
    thalweg (floor) at the shoreline to it on the centreline, over ramp (the local half-width, at most
    rampMetres), so the low-water stream runs in a narrow channel cut into the silt."""
    edge = floor+BACK_RIVER_EDGE
    ramp = BACK_RIVER_SECTION['rampMetres'] if ramp is None else ramp
    return edge+(floor-edge)*np.clip(inside/ramp, 0, 1)


def back_river_thalweg(to_outlet, to_head, above):
    """Thalweg on the outlet-to-head profile (back-river-beds.json profile): t = a/(a+b) of the
    distances along the water to the outlet (a) and the nearest head (b), plus the channel's extra."""
    t = to_outlet/np.maximum(to_outlet+to_head, 1e-9)
    p = BACK_RIVER_PROFILE
    return p['outlet']['sceneY']+(p['headSceneY']-p['outlet']['sceneY'])*t+above


def tidal_shelf(shore, top=CREST, edge=BED_EDGE):
    """Generic tidal bank face outside the outline, by distance out from the shore; a back river's
    face starts from its silted bed edge (edge)."""
    return edge+(top-edge)*smooth(0, S['shelfMetres'], shore)


def mud_flat(shore):
    """Mud between the low-water outline and the OS high-water mark."""
    return BED_EDGE+(MUD_TOP-BED_EDGE)*smooth(0, S['mudRampMetres'], shore)


def flat_rim(height, points):
    """A flat rises over flatRimMetres to just under high water and holds that for the last metre
    before its traced high-water line, where the OS bank begins, so the moving water meets the bank
    instead of standing over a strip of ground below it (the metre keeps the rim on the network's
    1 m bands). height: flat heights at points (shapely points on the flat)."""
    if high_water_lines.is_empty or not len(height):
        return height
    t = 1-smooth(1, 1+S['flatRimMetres'], shapely.distance(high_water_lines, points))
    return height+np.maximum(0, RIM_TOP-height)*t


# build_river_network.py sets its land sections out at the exact distance from the mapped shoreline
# plus this mean raster offset (its SHORE_OFFSET_M); the core uses the same at its boundary.
SHORE_OFFSET_M = .35


def flat_seam(distance):
    """Level where a mesh meets the detailed core's boundary on an OS mud flat, outside the mapped
    water: the flat's own profile at the exact distance from the shoreline, so both meshes meet on
    the flat instead of dipping to the -0.1 land seam across it."""
    return mud_flat(distance+SHORE_OFFSET_M)


def seam(inside_tidal):
    """Level where a mesh meets the detailed core's boundary: -0.1 on land and in
    still water, SEAM_BED in tidal water, feathered by distance in from the shore."""
    return -.1+(SEAM_BED+.1)*smooth(0, S['seamRampMetres'], inside_tidal)
