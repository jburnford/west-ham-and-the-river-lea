"""Reconcile Bow Road and the wharf bank against the reviewed OS map.

Cached map tiles are required for authoring; routine builds use saved JSON.
"""
import json
from pathlib import Path
from factory_map_sources import mosaic

ROOT=Path(__file__).resolve().parents[1]
load=lambda p:json.loads((ROOT/p).read_text())
save=lambda p,data:(ROOT/p).write_text(json.dumps(data,indent=2)+'\n')


def build():
    road_path='data/maps/district-road-traces.json'
    bank_path='data/maps/factory-west-context.json'
    register_path='data/maps/bow-flour-context-alignment.json'
    roads=load(road_path)
    context=load(bank_path)
    road=next(r for r in roads['roads'] if r['name']=='Stratford High Street')
    river=next(r for r in context['rivers'] if r['id']==10022)
    ring=river['polygons'][0][0]
    if (ROOT/register_path).exists():
        register=load(register_path)
    else:
        register=dict(
            source='Cached OS London five-foot 1893 map; supplied outlines 6296, 664578, 783709, 6191, 247343 and 970043',
            evidenceImage='reference/footprint-model-alignment/bow-flour-context-before.png',
            road=dict(name=road['name'],priorPoints=road['points'],priorSourcePixels=road['sourcePixels'],
                      priorBridgeSpans=road['bridgeSpans'],offset=[5.7,7.0],
                      review='First two road controls and Bow Bridge span moved 5.7 m east and 7 m south to the visible Bow Road carriageway. The former line ran along the north frontage and through the mill. Retain the interpreted 12 m carriageway and all eastern controls/bridges.'),
            bank=dict(riverId=10022,polygonIndex=0,ringIndex=0,
                      replacements=[dict(vertex=i,priorPoint=ring[i],point=[ring[i][0],ring[i][1]-2]) for i in [100,101]],
                      review='Two wharf-side bank controls move 2 m north to follow the mapped riverside wall and clear the supplied Albion Wharf exterior. Opposite bank and remaining channel controls retained; this is local map reconciliation, not a surveyed shoreline.'))
    correction=register['road']
    dx,dz=correction['offset']
    road['points']=[[round(x+dx,3),round(z+dz,3)] if i<2 else [x,z]
                    for i,(x,z) in enumerate(correction['priorPoints'])]
    road['bridgeSpans']=json.loads(json.dumps(correction['priorBridgeSpans']))
    bridge=next(b for b in road['bridgeSpans'] if b['id']=='bow-bridge')
    bridge['points']=[[round(x+dx,3),round(z+dz,3)] for x,z in bridge['points']]
    bridge['alignmentEvidence']=correction['review']
    _,_,pixel=mosaic(road['sourceBounds'])
    road['sourcePixels']=pixel(road['points']).round(3).tolist()
    road['bowFlourAlignment']=dict(register=register_path,review=correction['review'])
    for change in register['bank']['replacements']:
        assert ring[change['vertex']] in [change['priorPoint'],change['point']]
        ring[change['vertex']]=change['point']
    river['bowFlourAlignment']=dict(register=register_path,review=register['bank']['review'])
    save(register_path,register)
    save(road_path,roads)
    save(bank_path,context)
    print('Bow Flour context: two Bow Road controls and its bridge span; two wharf-bank controls reconciled.')


if __name__=='__main__':
    build()
