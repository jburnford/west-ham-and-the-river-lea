"""Check derived housing clearance, shared plots and outbuilding placement."""
from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union
from build_housing_detail import load, rect

detail=load('docs/data/housing-detail.json')
ground=load('docs/data/ground-plan.json');sw=load('docs/data/southwest-context.json')
infra=load('docs/data/infrastructure.json');factories=load('docs/data/factory-buildings.json')
original=ground['neighbourhood']['terraces']+sw['rows']
survey=load('data/maps/mill-meads-housing.json')
district=load('data/maps/district-housing-review.json')
from east_bridge_housing import SUPPRESSED_IDS
expected_ids={r['id'] for r in original}|{r['id'] for r in survey['rows']}|{r['id'] for r in district['rows']}
assert expected_ids-SUPPRESSED_IDS=={r['id'] for r in detail['rows']}
rows={r['id']:r for r in detail['rows']}
assert all(rows[id].get('districtReviewed') for id in district['reviewedOriginalRows'])
assert set(district['reviewedOriginalRows'])=={r['id'] for r in original if r['id'] not in {p['id'] for p in survey['rows']}}
houses=unary_union([rect(r) for r in detail['rows']+ground['neighbourhood']['houses']])
roads=unary_union([LineString(r['route']).buffer(r['width']/2,cap_style=2,join_style=2) for r in infra['roads']])
water=unary_union([Polygon(p[0],p[1:]) for river in ground['rivers']+factories['westContext']['rivers'] for p in river['polygons']])
plots={p['id']:Polygon(p['polygons'][0][0],p['polygons'][0][1:]) for p in detail['plots']}
yards=unary_union(list(plots.values()))
assert sum(p.area for p in plots.values())-yards.area<.01,'Overlapping back yards'
for name,obstacle in [('houses',houses),('streets',roads),('rivers',water)]:
    assert yards.intersection(obstacle).area<.01,('Back yards intrude into',name)
for item in detail['extensions']+detail['privies']:
    assert plots[item['plotId']].buffer(.025).covers(Polygon(item['footprint'])),item
for item in detail['extensions']:
    assert Polygon(item['footprint']).distance(rect(rows[item['rowId']]))<.01,'Detached scullery'
courts=[Polygon(r[0],r[1:]) for p in detail['forecourts'] for r in p['polygons']]
forecourts=unary_union(courts)
assert sum(p.area for p in courts)-forecourts.area<.01,'Overlapping forecourts'
assert forecourts.intersection(yards.union(houses).union(roads).union(water)).area<.01,'Overlapping court surface'
assert len(plots)>len(original)*10,'Missing household plots'
assert len(detail['extensions'])>len(plots)*.8,'Missing sculleries'
corner=next(r for r in load('data/maps/east-bridge-road-housing.json')['rows'] if r['id']=='os-row-39-part-1')
for r in detail['rows']:
    if r['id']==corner['id']:
        # The OS review replaces a fictitious garden-end terrace with one
        # mapped corner body, whose 6.36 m width exceeds the terrace-bay limit.
        assert r['bays']==corner['houseCount']==1
        assert abs(r['width']-corner['geometry']['width'])<.005
        assert 6<r['width']<7
    else:
        assert 2.7<=r['width']/r['bays']<=6,('Unexpected household width',r['id'])
for id in district.get('focusedReview',{}).get('addedRows',[])+district.get('focusedReview',{}).get('revisedRows',[]):
    assert rect(rows[id]).intersection(roads).area<.05,('Re-traced housing overlaps full carriageway',id)
# Biggerstaff's carriageway belongs between its two terrace fronts, not behind
# the mill-side range (the earlier road registration followed the rear plots).
mill=rows['district-biggerstaff-mill-side'];opposite=rows['district-biggerstaff-preston']
cross_street=LineString([(mill['x'],mill['z']),(opposite['x'],opposite['z'])])
biggerstaff=LineString(next(r['route'] for r in infra['roads'] if r['name']=='Biggerstaff Road'))
assert cross_street.crosses(biggerstaff),'Biggerstaff Road is not between its terrace fronts'
for source in survey['rows']:
    assert rows[source['id']]['bays']==source['houseCount'],source['id']
    assert rect(rows[source['id']]).intersection(roads).area<.05,('Mapped range overlaps full carriageway',source['id'])
assert all(rows[f'os-row-{i}' if i!=4 else 'os-row-4-part-1']['bays']==16 for i in range(2,7))
from statistics import mean
area=lambda id:mean(p['areaM2'] for p in detail['plots'] if p['rowId']==id)
assert area('os-row-8-part-1')>area('os-row-2')*1.5,'Lost contrast between deep and compact plots'
print(f"Housing detail passed: {len(rows)} rows, {len(plots)} separate yards; road/water clearance, attached sculleries and contained outbuildings.")
