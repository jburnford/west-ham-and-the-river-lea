"""Build a dated topology audit without altering terrain or creating an outlet."""
import hashlib
import json
from pathlib import Path
from shapely.geometry import LineString,Point,box
from shapely.ops import substring
from historic_drainage import evidence
from spot_height_mosaics import pixel_to_coords
from culvert_section import build_section

ROOT=Path(__file__).resolve().parents[1]
load=lambda path:json.loads((ROOT/path).read_text())
CONFIG='data/maps/drainage-connections-1900.json'


def build():
    spec=load(CONFIG);source=evidence();rendered=load('docs/data/drainage-1900.json')
    if spec['geometryEpoch']!=source['geometryEpoch']:raise ValueError('Connection/source epoch mismatch')
    if rendered['geometryEpoch']!=source['geometryEpoch']:raise ValueError('Rendered drainage epoch mismatch')
    east=next(f for f in source['features'] if f['id']=='plaistow-east-drain')
    west=next(f for f in source['features'] if f['id']=='junction-west-drain-candidate')
    sluices={s['id']:s for s in source['sluices']}
    west_line=LineString(west['route']);middle=west_line.project(Point(sluices['middle-junction']['position']))
    positions={'west-junction':west['route'][0],'middle-junction':list(west_line.interpolate(middle).coords)[0],
               'railway-west':west['route'][-1],'manor-east':east['route'][0],
               'east-trace-boundary':east['route'][-1],'manor-road-north':sluices['manor-road-north']['position']}
    labels=['Western sluice','Middle sluice','Railway-side sluice','Eastern channel entrance','Trace continues beyond review','Northern sluice — unconnected']
    nodes=[{'id':key,'name':name,'position':list(pos),'invertODNMetres':None,
            'kind':'trace-boundary' if key=='east-trace-boundary' else 'sluice-location' if key in sluices else 'channel-entrance',
            'outfallConfirmed':False} for (key,pos),name in zip(positions.items(),labels)]
    edges=[]
    def edge(id,a,b,route,kind):
        edges.append({'id':id,'from':a,'to':b,'route':list(map(list,route)),
                      'kind':kind,'lengthMetres':LineString(route).length,
                      'invertODNMetres':None,'capacityM3s':None})
    edge('west-first','west-junction','middle-junction',substring(west_line,0,middle).coords,'candidate-drain')
    edge('west-second','middle-junction','railway-west',substring(west_line,middle,west_line.length).coords,'candidate-drain')
    edge('crossing','railway-west','manor-east',[positions['railway-west'],positions['manor-east']],'possible-culvert')
    edge('east-channel','manor-east','east-trace-boundary',east['route'],'mapped-channel')
    corridor=LineString(edges[2]['route']);infra=load('docs/data/infrastructure.json')
    window=box(0,400,650,640);railways=[];crossings=[]
    for rail in infra['railways']:
        line=LineString(rail['route']);hit=line.intersection(corridor)
        if not hit.is_empty:
            crossings.append({'name':rail['name'],'position':list(hit.coords)[0],
                              'sceneFormationHeight':rail.get('formationHeight'),'heightStatus':'inherited interpretation, not a surveyed crossing level'})
        clipped=line.intersection(window)
        for part in getattr(clipped,'geoms',[clipped]):
            if part.geom_type=='LineString':railways.append({'name':rail['name'],'route':list(map(list,part.coords))})
    road=spec['roadContext'];sidecar=f"reference/spot-heights/mosaics/{road['mosaic']}.json";meta=load(sidecar)
    route=[]
    for pixel in road['pixels']:
        p=pixel_to_coords(meta,*pixel);route.append([p['bng_e']-538900,183209-p['bng_n']])
    nearest=min(LineString(r['route']).distance(corridor) for r in infra['roads'])
    manor=next((r for r in infra['roads'] if r.get('elevationProfile')),None)
    if manor:route=manor['route']
    inputs=[CONFIG,'docs/data/infrastructure.json','docs/data/drainage-1900.json','docs/data/terrain-1900.json',sidecar,
            'reference/spot-heights/mosaics-1848/s18_131072_87146.png',
            'reference/spot-heights/mosaics-1848/s18_131075_87146.png']
    inputs += [r['file'] for r in spec['evidenceReview'] if 'file' in r]
    result={**spec,'nodes':nodes,'edges':edges,'railways':railways,
            'roadContext':{**road,'route':route},'crossingAudit':{
                'lengthMetres':corridor.length,'railwayIntersections':crossings,
                'nearestModelRoadMetres':nearest,'roadGeometryPresentAtCrossing':nearest<10,
                'roadHeightStatus':manor['elevationProfile']['heightStatus'] if manor else None,
                'warning':('Manor Road is restored here with map-based road heights. Railway height and the culvert section remain provisional; the road surface does not establish a hydraulic opening.' if manor else 'Historical Manor Road is absent from current road geometry here. Do not infer a hydraulic opening through the road or railway.')},
            'renderedReach':rendered['renderedReach'],'observationEpoch':source['observationEpoch'],
            'inputHashes':{**source['inputHashes'],**{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in inputs}}}
    result['culvertSection']=build_section(result,infra,rendered)
    result['inputHashes'].update(result['culvertSection']['inputHashes'])
    path=ROOT/'docs/data/drainage-connections-1900.json';path.write_text(json.dumps(result,indent=2)+'\n')
    print(f"Built {len(nodes)} nodes, {len(edges)} reaches, {len(spec['scenarios'])} scenarios; candidate crossing {corridor.length:.1f} m, {len(crossings)} railway routes.")


if __name__=='__main__':build()
