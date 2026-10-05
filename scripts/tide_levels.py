"""Tide levels, tidal limit and mud flats from data/maps/os-tide-levels.json.

Shared by build_river_network.py and build_river_terrain.py so the network and
the detailed core use the same levels and meet at the same seam.
"""
import json
from pathlib import Path

import numpy as np
import shapely
from shapely.geometry import Polygon
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


def seam(inside_tidal):
    """Level where a mesh meets the detailed core's boundary: -0.1 on land and in
    still water, SEAM_BED in tidal water, feathered by distance in from the shore."""
    return -.1+(SEAM_BED+.1)*smooth(0, S['seamRampMetres'], inside_tidal)
