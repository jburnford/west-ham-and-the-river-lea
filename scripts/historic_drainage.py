"""Dated drainage evidence and a bounded, explicitly assumed open-channel section."""
import hashlib
import json
from pathlib import Path

import numpy as np
from shapely import distance, points
from shapely.geometry import LineString, box
from spot_height_mosaics import pixel_to_coords
from historic_elevation import smooth

ROOT=Path(__file__).resolve().parents[1]
SOURCE='data/maps/historic-drainage-1900.json'


def evidence():
    raw=json.loads((ROOT/SOURCE).read_text())
    hashes={SOURCE:hashlib.sha256((ROOT/SOURCE).read_bytes()).hexdigest()}
    def convert(mosaic,pixel):
        name=f'reference/spot-heights/mosaics/{mosaic}.json'
        meta=json.loads((ROOT/name).read_text())
        for path in [name,name.replace('.json','.png')]:
            hashes[path]=hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
        p=pixel_to_coords(meta,*pixel)
        return [round(p['bng_e']-538900,4),round(183209-p['bng_n'],4)]
    for f in raw['features']:f['route']=[convert(f['mosaic'],p) for p in f['pixels']]
    for s in raw['sluices']:
        s.update(position=convert(s['mosaic'],s['pixel']),positionStatus='approximate map location',
                 invertODNMetres=None,gateOperation=None)
    raw['inputHashes']=hashes
    return raw


def apply_section(epoch,X,Z,target,weight):
    raw=evidence()
    if epoch!=raw['geometryEpoch']:raise ValueError('Drainage needs its own period review')
    spec=raw['sectionAssumptions']
    feature=next(f for f in raw['features'] if f['render'])
    line=LineString(feature['route']).intersection(box(*spec['renderBounds']))
    if line.geom_type!='LineString':raise ValueError('Expected one bounded drainage reach')
    dist=distance(points(X,Z),line)
    x0,z0,x1,z1=spec['renderBounds']
    edge=np.minimum.reduce([X-x0,x1-X,Z-z0,z1-Z])
    mask=(dist<spec['topWidthMetres']/2)&(edge>0)
    if not np.all(weight[mask]>=.999):raise ValueError('Drainage would alter unsupported/protected ground')
    bed=float(target[mask].min()-spec['depthBelowLowestRimMetres'])
    profile=(1-smooth(spec['bedWidthMetres']/2,spec['topWidthMetres']/2,dist))*smooth(0,spec['boundaryFeatherMetres'],edge)
    result=target.copy()
    result[mask]+=(bed-target[mask])*profile[mask]
    raw['renderedReach']={'id':feature['id'],'route':list(map(list,line.coords)),
        'lengthMetres':line.length,'bedSceneY':bed,
        'waterSceneY':bed+spec['standingWaterDepthMetres'],
        'modifiedGridNodes':int(np.count_nonzero(result!=target)),
        'boundaryIsPhysical':False,'hydraulicConnection':None}
    return result,raw,mask,line


def water_triangles(mesh,raw):
    """Clip water to the actual rendered bed triangles, including model-end fades."""
    level=raw['renderedReach']['waterSceneY']
    line=LineString(raw['renderedReach']['route'])
    centres=mesh.mean(axis=1)
    near=distance(points(centres[:,0],centres[:,2]),line)<raw['sectionAssumptions']['topWidthMetres']
    selected=mesh[near & (mesh[:,:,1].min(axis=1)<level)]
    out=[]
    for tri in selected:
        poly=[]
        for a,b in zip(tri,np.roll(tri,-1,axis=0)):
            if a[1]<level:poly.append(a.copy())
            if (a[1]<level)!=(b[1]<level):poly.append(a+(b-a)*((level-a[1])/(b[1]-a[1])))
        for i in range(1,len(poly)-1):
            face=np.array([poly[0],poly[i],poly[i+1]])
            face[:,1]=level+.003
            out.append(face.tolist())
    raw['waterTriangles']=out
    if not out:raise ValueError('Drain water has no visible bed footprint')
