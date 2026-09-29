"""Street exclusions, including explicitly reviewed narrow mapped frontages.

Carriageway widths do not change. Infrastructure clips its pavement mesh against
the retained factory walls, so a documented pinch point gets a narrower pavement
instead of losing a surveyed building façade to the default clearance estimate.
"""
from shapely.geometry import LineString
from shapely.ops import unary_union


def street_clearances(roads):
    defaults = [LineString(r['points']).buffer(r['width']/2+1.1,cap_style=2,join_style=2) for r in roads]
    overrides = {}
    for index,road in enumerate(roads):
        for review in road.get('buildingClearanceReviews',[]):
            assert 0<=review['shoulderWidth']<=1.1 and review['evidence']
            local = LineString(road['points']).buffer(road['width']/2+review['shoulderWidth'],cap_style=2,join_style=2)
            corridor = unary_union(defaults[:index]+[local]+defaults[index+1:])
            for id in review['modelIds']:
                assert id not in overrides, 'Multiple clearance exceptions need an explicit combined review'
                overrides[id] = corridor
    return unary_union(defaults),overrides
