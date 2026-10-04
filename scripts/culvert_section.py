"""Provisional culvert sections constrained by the separately observed road profile."""
import hashlib
import json
from pathlib import Path
import numpy as np
from shapely.geometry import LineString, Point
from manor_road import profile
from spot_height_mosaics import pixel_to_coords
from railway_levels import formation_at_point

ROOT=Path(__file__).resolve().parents[1]
CONFIG='data/maps/culvert-section-1900.json'
load=lambda p:json.loads((ROOT/p).read_text())

def build_section(graph,infra,drainage):
    spec=load(CONFIG)
    if graph['geometryEpoch']!=spec['geometryEpoch']:raise ValueError('Culvert section needs period review')
    crossing=next(e for e in graph['edges'] if e['id']=='crossing')
    line=LineString(crossing['route']);length=line.length
    road=next(r for r in infra['roads'] if r.get('elevationProfile'))
    p=road['elevationProfile'];datum=p['verticalReference'];offset=datum['odnMinusSceneYMetres']
    footprint=LineString(p['route']).buffer(p['widthMetres']/2+p['shoulderMetres'],cap_style=2)
    road_span=line.intersection(footprint)
    assert road_span.geom_type=='LineString'
    a,b=sorted(line.project(Point(q)) for q in road_span.coords)
    stations=np.linspace(a,b,101)
    positions=np.array([line.interpolate(s).coords[0] for s in stations])
    road_heights=profile(p,positions[:,0],positions[:,1])[0]+offset
    bed=drainage['renderedReach']['bedSceneY']+offset
    cases=[]
    for case in spec['cases']:
        assert all(case[k]>0 for k in ['widthMetres','heightMetres','eastToWestSlope'])
        east=bed-case['inletLoweringMetres'];west=east-length*case['eastToWestSlope']
        inverts=west+stations*case['eastToWestSlope']
        covers=road_heights-inverts-case['heightMetres']-spec['roofThicknessMetres']
        minimum=float(covers.min())
        cases.append({**case,'eastInvertODN':east,'westInvertODN':west,
                      'fallEastToWestMetres':east-west,'openingAreaM2':case['widthMetres']*case['heightMetres'],
                      'minimumRoadCoverMetres':minimum,'fitsCoverAssumption':minimum>=spec['minimumCoverMetres'],
                      'approachRegradingRequired':case['inletLoweringMetres']>0,
                      'capacityM3s':None,'hydraulicallyEnabled':False})
    review=spec['railwayHeightReview'];sidecar=f"reference/spot-heights/mosaics/{review['mosaic']}.json"
    meta=load(sidecar);spots=[]
    for c in review['roadBridgeSpots']:
        for reader in review['readers']:
            assert any(r['type']=='spot' and r['setting']=='bridge' and r['value_ft']==c['valueFeet']
                       and np.hypot(r['px']-c['pixel'][0],r['py']-c['pixel'][1])<3 for r in load(reader)['readings'])
        pos=pixel_to_coords(meta,*c['pixel'])
        spots.append({**c,'position':[pos['bng_e']-538900,183209-pos['bng_n']],
                      'heightODN':(c['valueFeet']+datum['liverpoolToNewlynFeet'])*.3048})
    bridge=LineString([c['position'] for c in spots])
    rail=next(r for r in infra['railways'] if r['name']==p['railway']['name'])
    hit=bridge.intersection(LineString(rail['route']))
    assert hit.geom_type=='Point'
    fraction=bridge.project(hit)/bridge.length
    deck=spots[0]['heightODN']*(1-fraction)+spots[1]['heightODN']*fraction
    # The prior constant formation (kept for the record) and the OS level profile that replaced it.
    formation=rail.get('priorFormationHeight',rail['formationHeight'])+offset
    review={**review,'spots':spots,'crossingPosition':list(hit.coords[0]),'deckEstimateODN':deck,
            'inheritedFormationODN':formation,'formationAboveDeckMetres':formation-deck,
            'distanceFromDrainCrossingMetres':hit.distance(line),
            'constantFormationConflictsWithRoadBridge':formation>=deck,
            'calibratedFloodBarrier':False}
    if rail.get('levelProfile'):
        profiled=formation_at_point(rail,hit.x,hit.y)+offset
        review.update({'profileFormationODN':profiled,'profileFormationBelowDeckMetres':deck-profiled,
                       'profileConflictsWithRoadBridge':profiled>=deck,
                       'profileSource':rail['levelProfile']['register'],
                       'profileStatus':'The constant 5.5 m formation was replaced by the OS level profile (at grade here: formation 0.1 m above the OS ground readings); the road bridge now passes over the line.'})
    inputs=[CONFIG,sidecar,sidecar.replace('.json','.png'),*review['readers']]
    return {**spec,'cases':cases,'railwayHeightReview':review,'lengthMetres':length,
            'route':crossing['route'],'assumedApproachBedODN':bed,
            'roadSpan':{'stations':stations.tolist(),'surfaceODN':road_heights.tolist()},
            'railwayCrossings':[{'name':r['name'],'station':line.project(Point(r['position'])),
                                 'formationODN':r['sceneFormationHeight']+offset}
                                for r in graph['crossingAudit']['railwayIntersections']],
            'verticalReference':datum,
            'inputHashes':{k:hashlib.sha256((ROOT/k).read_bytes()).hexdigest() for k in inputs}}
