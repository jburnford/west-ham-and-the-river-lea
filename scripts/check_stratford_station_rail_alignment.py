"""Check native station controls, earth-only exclusions and unchanged joins."""
import argparse
import hashlib
import math

from shapely import affinity
from shapely.geometry import LineString, Polygon, box, shape
from shapely.ops import unary_union

from abbey_support import station_footprints
from factory_map_sources import mosaic
from stratford_station_rail_alignment import (ROOT,BASELINE,SOURCE,STATION_IDS,
    BOOKING_IDS,CONTROL_X,read,running_line,station_formation_obstacles)
from woolwich_connection import build_woolwich_connection


def check(preflight=False):
    raw=read('data/maps/woolwich-northern-connection.json')
    context=read('data/maps/east-channelsea-context-alignment.json')['railCorrection']
    prior=read(BASELINE);review=raw['stationFormationReview']
    assert context['record']==raw
    assert context['stationReview']['baseline']==BASELINE
    assert context['stationReview']['baselineSha256']==hashlib.sha256((ROOT/BASELINE).read_bytes()).hexdigest()
    changed=list(CONTROL_X)
    assert context['stationReview']['changedControlIndices']==changed
    assert all(point==prior['route'][i] for i,point in enumerate(raw['route']) if i not in changed)
    assert {k:v for k,v in raw.items() if k not in ['route','eastChannelseaRailAlignment','stationFormationReview']}=={k:v for k,v in prior.items() if k not in ['route','eastChannelseaRailAlignment']}
    assert review['source']==SOURCE and review['sourceFeatureIds']==STATION_IDS
    assert review['bookingFeatureIds']==BOOKING_IDS and review['bankOnly']
    assert review['preservedCrestShoulderMetres']==.51
    assert review['sourceSha256']==hashlib.sha256((ROOT/SOURCE).read_bytes()).hexdigest()
    features={f['properties']['sourceFid']:f for f in read(SOURCE)['features'] if f['properties']['sourceFid'] in STATION_IDS}
    for row in review['stationBodies']:
        original=affinity.affine_transform(shape(features[row['sourceFid']]['geometry']),review['sourceTransform'])
        assert shape(row['geometry']).equals_exact(original,.000001)
    _,world,_=mosaic(review['reviewedSourceBounds'])
    assert [q['index'] for q in review['controls']]==changed
    for control in review['controls']:
        assert control['reviewedSourcePixels'][0][0]==CONTROL_X[control['index']]
        assert control['point']==world(control['reviewedSourcePixels']).round(3).tolist()[0]
        assert raw['route'][control['index']]==control['point']
        assert prior['route'][control['index']]==control['priorPoint']
    infra=read('docs/data/infrastructure.json');scene=read('docs/data/factory-buildings.json');ground=read('docs/data/ground-plan.json')
    main=next(r for r in infra['railways'] if r.get('detailedMainline'))
    line=running_line(raw,main['route']);old=running_line(prior,main['route'])
    bodies={r['sourceFid']:shape(r['geometry']) for r in review['stationBodies']}
    assert old.intersection(bodies[1539]).length>90
    assert line.is_simple and line.intersection(bodies[1539]).is_empty
    assert line.distance(bodies[1539])>raw['crestHalfWidth']+.15
    for fid in [68571,837163,150512,281895,885148]:
        assert line.distance(bodies[fid])>raw['crestHalfWidth']+.15,(fid,line.distance(bodies[fid]))
    mask=station_formation_obstacles(raw,main['route'])
    crest=line.buffer(raw['crestHalfWidth'],cap_style=2,join_style=2)
    assert mask.buffer(.5).intersection(crest).area<.001
    # No arbitrary railway relocation to clear the booking roof over its approach.
    booking=unary_union([bodies[fid] for fid in BOOKING_IDS])
    assert line.intersection(booking).length>1
    water=unary_union([Polygon(p[0],p[1:]) for r in ground['rivers']+scene['westContext']['rivers'] for p in r['polygons']])
    roads=unary_union([LineString(r['route']).buffer(r['width']/2) for r in infra['roads']])
    southwest=read('docs/data/southwest-context.json');surveyed={s['id'] for s in scene['sites']}
    legacy=[b for b in ground['factoryStudies']+ground['neighbourhood']['mappedFactories']+southwest['industrialRanges'] if b.get('siteId') not in surveyed]
    legacy+=read('docs/data/housing-detail.json')['rows']+ground['neighbourhood']['houses']+[ground['neighbourhood']['mill']]
    building_parts=[affinity.translate(affinity.rotate(box(-b['width']/2,-b['depth']/2,b['width']/2,b['depth']/2),-b.get('rotation',0)),b['x'],b['z']).buffer(.3) for b in legacy]
    building_parts += [Polygon(p['outer'],p['holes']).buffer(.15) for b in scene['buildings'] for p in b['renderPolygons']]
    building_parts += [station_footprints(read('docs/data/abbey-station-plan.json')).buffer(.15)]
    buildings=unary_union(building_parts)
    if preflight:
        rail=build_woolwich_connection(water,roads,buildings,main,mask)
    else:
        rail=next(r for r in infra['railways'] if r.get('id')==raw['id'])
    assert rail['stationFormationReview']==review
    assert rail['stationFormationExclusionApplied']['excludedEarthAreaM2']>30
    assert rail['stationFormationExclusionApplied']['bankOnly']
    assert rail['route'][0]==raw['route'][0] and rail['route'][-1]==raw['route'][-1]
    assert all(rail[k]==prior[k] for k in ['gauge','tracks','trackSpacing','crestHalfWidth','baseHalfWidth','formationHeight','joinHeight','mainlineJoinChainage','mainlineTrackOffset'])
    earth=unary_union([Polygon([(p[0],p[2]) for p in tri]) for tri in rail['embankment']])
    assert earth.intersection(mask.buffer(.499)).area<.001
    assert earth.intersection(bodies[1539]).area<.001
    # The station crop does not remove track support or create a retaining wall.
    protected_crest=crest.difference(water.union(unary_union([Polygon(p[0],p[1:]) for p in main['northernWater']])).buffer(2.5)).difference(roads.buffer(2)).difference(buildings.buffer(.5))
    assert protected_crest.difference(earth.buffer(.001)).area<.05
    boundary=mask.buffer(.5).boundary.buffer(.005)
    for a,b in rail['retainingEdges']:
        edge=LineString([(a[0],a[2]),(b[0],b[2])])
        assert edge.intersection(boundary).length<=.9*edge.length+.000001
    if not preflight:
        north=next(r for r in infra['railways'] if r.get('id')=='north-london-connection')
        join=rail['stations'][north['join']['stationIndex']]
        assert north['stations'][-1][:5]==join[:5]
        for offset in [-2.5175,-1.0825,1.0825,2.5175]:
            end=north['stations'][-1]
            assert math.dist([end[0]+end[3]*offset,end[2]+.46,end[1]+end[4]*offset],[join[0]+join[3]*offset,join[2]+.46,join[1]+join[4]*offset])<.000001
    print(f'Stratford station: controls12–15 native replay;95m former station-body crossing removed; centre clearance{line.distance(bodies[1539]):.2f}m; bank-only station crop preserves crest and joins; no added station retaining wall'+(' (preflight).' if preflight else ' (published).'))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--preflight',action='store_true')
    check(parser.parse_args().preflight)
