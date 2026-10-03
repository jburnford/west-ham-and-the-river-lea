"""Bounded, dated road profile and adjacent map-traced railway alignment."""
import hashlib
import json
from pathlib import Path
import numpy as np
from shapely import distance, line_locate_point, points
from shapely.geometry import LineString, Point
from shapely.ops import substring
from spot_height_mosaics import pixel_to_coords
from historic_elevation import smooth

ROOT=Path(__file__).resolve().parents[1]
CONFIG='data/maps/manor-road-1900.json'

def evidence():
    spec=json.loads((ROOT/CONFIG).read_text())
    sidecar=f"reference/spot-heights/mosaics/{spec['mosaic']}.json"
    meta=json.loads((ROOT/sidecar).read_text())
    def convert(pixel):
        p=pixel_to_coords(meta,*pixel)
        return [p['bng_e']-538900,183209-p['bng_n']]
    route=list(map(convert,spec['pixels']));line=LineString(route)
    datum=json.loads((ROOT/'data/maps/terrain-epochs.json').read_text())['verticalReference']
    controls=[]
    for c in spec['controls']:
        # Keep independently read observations; do not modify the live catalogue.
        for reader in spec['readers']:
            matches=[r for r in json.loads((ROOT/reader).read_text())['readings']
                     if r['type']=='spot' and r['setting']=='street' and r['value_ft']==c['valueFeet']
                     and np.hypot(r['px']-c['pixel'][0],r['py']-c['pixel'][1])<4]
            assert len(matches)==1 and matches[0]['confidence']=='high'
        odn=(c['valueFeet']+datum['liverpoolToNewlynFeet'])*.3048
        controls.append({**c,'position':convert(c['pixel']),
                         'distance':line.project(Point(convert(c['pixel']))),
                         'heightODN':odn,'heightScene':odn-datum['odnMinusSceneYMetres']})
    inputs=[CONFIG,sidecar,sidecar.replace('.json','.png'),*spec['readers'],'data/maps/terrain-epochs.json']
    return {**spec,'route':route,'controls':controls,'railRoute':list(map(convert,spec['railway']['pixels'])),
            'verticalReference':datum,'inputHashes':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in inputs}}

def road_trace(spec):
    return {'name':spec['name'],'sheet':'scene','pixelWidth':1024,'points':spec['route'],
            'kind':'road','width':spec['widthMetres'],'surface':spec['surface'],
            'evidence':spec['heightStatus'],'elevationProfile':spec}

def align_railway(rail,spec):
    if rail['name']!=spec['railway']['name']:return rail
    old=LineString(rail['route']);new=spec['railRoute'];join=spec['railway']['joinLengthMetres']
    start=max(0,old.project(Point(new[0]))-join)
    end=min(old.length,old.project(Point(new[-1]))+join)
    route=[*substring(old,0,start).coords,*new,*substring(old,end,old.length).coords]
    return {**rail,'route':list(map(list,route)),
            'evidence':rail['evidence']+' Local alignment beside Manor Road retraced from 1890s map; 80 m approach joins interpreted. Formation height unchanged.'}

def profile(spec,X,Z):
    line=LineString(spec['route']);ps=points(X,Z)
    d=distance(ps,line);along=line_locate_point(line,ps)
    height=np.interp(along,[c['distance'] for c in spec['controls']],[c['heightScene'] for c in spec['controls']])
    half=spec['widthMetres']/2+spec['shoulderMetres']
    influence=1-smooth(half,half+spec['groundFeatherMetres'],d)
    return height,influence

def domain(spec):
    return LineString(spec['route']).buffer(spec['widthMetres']/2+spec['shoulderMetres']+spec['groundFeatherMetres'])
