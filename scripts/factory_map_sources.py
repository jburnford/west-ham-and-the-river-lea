"""Read the already downloaded NLS map tiles in local scene coordinates."""
from functools import lru_cache
from pathlib import Path
import math

import numpy as np
from PIL import Image
from pyproj import Transformer

ROOT = Path(__file__).resolve().parents[1]
TO_MERCATOR = Transformer.from_crs(27700, 3857, always_xy=True)
FROM_MERCATOR = Transformer.from_crs(3857, 27700, always_xy=True)
SHIFT = 20037508.342789244


@lru_cache(maxsize=256)
def tile(layer, zoom, x, y):
    path = ROOT/f'reference/nls-tiles/{layer}/{zoom}/{x}/{y}.png'
    if not path.exists():
        raise FileNotFoundError(path)
    return np.asarray(Image.open(path).convert('RGB'))


def mosaic(bounds, zoom=18, layer='os-london-five-foot-1893'):
    """Return unmodified tile samples, with reversible pixel/scene transforms."""
    west, north, east, south = bounds
    mx0, my1 = TO_MERCATOR.transform(538900+west, 183209-north)
    mx1, my0 = TO_MERCATOR.transform(538900+east, 183209-south)
    step = 2*SHIFT/(2**zoom)
    tx0, tx1 = [math.floor((x+SHIFT)/step) for x in [mx0, mx1]]
    ty0, ty1 = [math.floor((SHIFT-y)/step) for y in [my1, my0]]
    canvas = np.full(((ty1-ty0+1)*256, (tx1-tx0+1)*256, 3), 255, dtype=np.uint8)
    for tx in range(tx0, tx1+1):
        for ty in range(ty0, ty1+1):
            canvas[(ty-ty0)*256:(ty-ty0+1)*256, (tx-tx0)*256:(tx-tx0+1)*256] = tile(layer, zoom, tx, ty)
    pixel = step/256
    left, top = tx0*step-SHIFT, SHIFT-ty0*step

    def to_world(points):
        points = np.asarray(points)
        e, n = FROM_MERCATOR.transform(left+points[:, 0]*pixel, top-points[:, 1]*pixel)
        return np.column_stack([np.asarray(e)-538900, 183209-np.asarray(n)])

    def to_pixel(points):
        points = np.asarray(points)
        x, y = TO_MERCATOR.transform(points[:, 0]+538900, 183209-points[:, 1])
        return np.column_stack([(np.asarray(x)-left)/pixel, (top-np.asarray(y))/pixel])

    return canvas, to_world, to_pixel
