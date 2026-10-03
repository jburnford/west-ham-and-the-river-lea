"""Replay the mapped, open Victoria Stone working grid without map dependencies."""
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTER = 'data/maps/victoria-stone-working-grid.json'


def build_victoria_stone_grid():
    """Return one ground-atlas context record; never an enclosed building."""
    return copy.deepcopy(json.loads((ROOT / REGISTER).read_text()))
