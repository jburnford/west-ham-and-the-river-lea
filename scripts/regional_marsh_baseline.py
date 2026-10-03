"""Regional early-marsh prior; source roles remain separate from the estimate."""
import numpy as np
import shapely
from scipy.spatial import cKDTree
from shapely.geometry import Polygon


def early_marsh_field(config, review, east, north, datum_offset_feet):
    accepted = [r for r in review['observations'] if r['baselineUse']]
    assert all(r['role'] in ('lane-proxy', 'ground-margin') for r in accepted)
    points = np.array([r['positionBNG'] for r in accepted])
    values = np.array([r['valueFeet'] for r in accepted])
    xy = np.column_stack([east.ravel(), north.ravel()])
    spec = config['interpolation']
    distances = cKDTree(points).query(xy, k=1)[0]
    numerator=np.zeros(east.size);denominator=np.zeros(east.size)
    # All observations participate continuously. Hard nearest-k membership
    # produced visible steps where the fourth neighbour changed.
    for point,value in zip(points,values):
        squared=((xy-point)**2).sum(axis=1)
        weights=np.exp(-squared/spec['distanceTaperMetres']**2)/(squared+spec['smoothingMetres']**2)**(spec['power']/2)
        numerator+=weights*value;denominator+=weights
    feet=numerator/denominator
    height = ((feet + datum_offset_feet)*.3048).reshape(east.shape)
    outline = Polygon(config['outlineBNG'])
    assert outline.is_valid
    inside = shapely.contains_xy(outline, east, north)
    blend = np.zeros(east.shape)
    d = shapely.distance(shapely.points(xy[inside.ravel()]), outline.boundary)
    t = np.clip(d/config['edgeTransitionMetres'], 0, 1)
    blend[inside] = t*t*(3-2*t)
    return height, blend, distances.reshape(east.shape)
