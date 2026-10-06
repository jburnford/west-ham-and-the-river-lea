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


def smooth(a, b, v):
    t = np.clip((v-a)/(b-a), 0, 1)
    return t*t*(3-2*t)


def tidal_bed(inside):
    """Bed inside the mapped (low-water) outline, by distance in from the shore."""
    return BED_EDGE+(BED_FLOOR-BED_EDGE)*smooth(0, S['bedRampMetres'], inside)


def tidal_shelf(shore, top=CREST):
    """Generic tidal bank face outside the outline, by distance out from the shore."""
    return BED_EDGE+(top-BED_EDGE)*smooth(0, S['shelfMetres'], shore)


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
