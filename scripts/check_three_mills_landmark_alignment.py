"""Verify mill footprints, attached landmark details and the retained crossings."""
import argparse
from shapely import affinity
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union
from factory_alignment_checks import check_register, load, ROOT

IDS={'house-west','house-main','house-east','house-tail','clock','clock-kilns','wharf','wharf-south'}


def check(preflight=False):
    check_register('three-mills-landmark',IDS,6,0,'three-mills-landmarks-before',
        preflight,permitted_water={'house-main','clock-kilns'},scene_counts=(547,{419:38}))
    r=load('data/maps/three-mills-landmark-footprint-alignment.json')
    cs={c['modelId']:c for c in r['buildings']}
    kiln=cs['clock-kilns'];p=Polygon(kiln['worldFootprint'])
    details=kiln['landmarkDetails'];caps=details['kilnCaps'];t=details['tower']
    for cap in caps:
        assert Point(cap['centre']).buffer(cap['radius']).difference(p).area<.001
        assert cap['height']==5.7
    assert Point(caps[0]['centre']).distance(Point(caps[1]['centre']))>sum(c['radius'] for c in caps)
    footprint=affinity.translate(affinity.rotate(box(-t['width']/2,-t['width']/2,t['width']/2,t['width']/2),
        kiln['footprintRotationDegrees'],origin=(0,0)),*t['centre'])
    assert footprint.difference(p).area<.001
    assert (t['baseHeight'],t['lanternHeight'],t['spireHeight'])==(12,5.5,3.6)
    assert all(footprint.distance(Point(c['centre']))>c['radius'] for c in caps)
    house=cs['house-main'];p=Polygon(house['worldFootprint'])
    for face in house['landmarkDetails']['houseFacades']:
        assert all(Point(v).distance(p.boundary)<.001 for v in face)
        assert LineString(face).difference(p.buffer(.15)).length<.01
    roads=load('data/maps/district-road-traces.json')['roads']
    lane=next(q for q in roads if q['name']=='Three Mills Lane')
    branch=next(q for q in roads if q['name']=='Three Mills Lane beside distillery')
    prior=lane['threeMillsLandmarkAlignment']
    later=ROOT/'data/maps/remaining-trades-context-alignment.json'
    expected_points=prior['points'][:6]
    expected_bridges=prior['bridgeSpans']
    if later.exists():
        correction=next(c for c in load('data/maps/remaining-trades-context-alignment.json')['roads'] if c['name']==lane['name'])
        assert correction['priorPoints'][:6]==prior['points'][:6]
        assert correction['priorBridgeSpans']==prior['bridgeSpans']
        expected_points=correction['points'][:6]
        expected_bridges=correction['bridgeSpans']
    assert lane['points'][:6]==expected_points and lane['points'][-2:]==prior['points'][-2:]
    assert lane['width']==prior['width']==7 and lane['bridgeSpans']==expected_bridges
    assert branch['kind']=='path' and branch['width']==2.2
    assert branch['points'][0]==lane['points'][-2]
    assert len(branch['bridgeSpans'])==1 and branch['bridgeSpans'][0]['provisional']
    assert LineString(branch['bridgeSpans'][0]['points']).difference(LineString(branch['points']).buffer(.001)).length<.001
    if not preflight:
        scene=load('docs/data/factory-buildings.json');models={b['id']:b for b in scene['buildings']}
        for id in ['house-main','clock-kilns']:assert models[id]['landmarkDetails']==cs[id]['landmarkDetails']
        plan=load('docs/data/ground-plan.json')
        water=unary_union([Polygon(p[0],p[1:]) for q in plan['rivers']+scene['westContext']['rivers'] for p in q['polygons']])
        assert 15<Polygon(models['house-main']['footprint']).intersection(water).area<17
        assert 9<Polygon(models['clock-kilns']['footprint']).intersection(water).area<10
        assert all(models[id].get('waterReview') for id in ['house-main','clock-kilns'])
    print('Mapped facade anchors, two separate kiln caps, northern clock tower, millrace relationships and route connections pass.')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--preflight',action='store_true')
    check(parser.parse_args().preflight)
