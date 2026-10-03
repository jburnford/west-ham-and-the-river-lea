"""Apply reviewed passage locations to the existing scene without moving banks.

Widths are explicit visual assumptions, not surveyed discharge sections. Locks
remain separate from tidal seeds. Raw GIS and building footprints are untouched.
"""
import hashlib
import json
from pathlib import Path
from shapely.geometry import Polygon, LineString, Point
from shapely.ops import unary_union, nearest_points

ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT/'docs/data/lower-lea-region/index.json'


def geometry(items):
    return unary_union([Polygon(p[0],p[1:]) for p in items])


def rings(g):
    parts=[g] if g.geom_type=='Polygon' else list(getattr(g,'geoms',[]))
    return [[list(p.exterior.coords),*[list(h.coords) for h in p.interiors]] for p in parts if p.geom_type=='Polygon']


def build(rivers):
    review=json.loads(REVIEW.read_text())
    source='data/maps/lower-lea-region/connection-review.json'
    digest=hashlib.sha256((ROOT/source).read_bytes()).hexdigest()
    assert review['inputHashes'].get(source)==digest, 'Rebuild the regional review after editing connection evidence'
    channels={}
    for r in rivers:
        key=r['id']-10000 if 10000<=r['id']<10100 else r['id']
        channels[key]=channels.get(key,Polygon()).union(geometry(r['polygons']))
    rows=[];deferred=[]
    specifications=[]
    for r in review['connectionReview']['structureRoutes']:
        specifications.append((r,r['siteId'],4.0 if r['category']=='lock-passage' else 3.0,r['category']))
    for r in review['topology']['nearConnections']:
        if r['reviewCategory'] in ['provisional-mapping-seam','mapped-navigation-junction','mill-site-review']:
            category='mill-passage' if r['reviewCategory']=='mill-site-review' else 'mapping-seam'
            specifications.append((r,'abbey-mill' if category=='mill-passage' else f"seam-{r['a']}-{r['b']}",2.0 if category=='mill-passage' else 3.0,category))
    for r,identifier,width,category in specifications:
        ids=[int(r[k].split('-')[1]) for k in ['a','b']]
        anchors=[(p[0]-538900,183209-p[1]) for p in r['routeBNG']]
        if any(i not in channels for i in ids):
            deferred.append({'id':identifier,'reason':'Outside existing detailed scene coverage'});continue
        # Project onto already reconciled core banks, not the older raw GIS.
        pa,pb=[nearest_points(Point(p),channels[i])[1] for p,i in zip(anchors,ids)]
        if any(Point(p).distance(q)>12 for p,q in zip(anchors,[pa,pb])):
            deferred.append({'id':identifier,'reason':'Outside clipped scene or bank reconciliation requires review'});continue
        line=LineString([pa,pb])
        if line.length<.01:continue
        patch=line.buffer(width/2,cap_style=1)
        # Preserve overlaps at both ends so rounding cannot leave a dry seam.
        assert patch.intersection(channels[ids[0]]).area>0 and patch.intersection(channels[ids[1]]).area>0
        rows.append({'id':identifier,'channelIds':ids,'category':category,
            'route':list(line.coords),'polygons':rings(patch),'visualWidthMetres':width,
            'widthStatus':'inferred display width; not a hydraulic capacity',
            'bedSceneY':-.7,'bedStatus':'provisional submerged bed matching scene datum; not surveyed bathymetry',
            'capacity':None,'gateState':None,
            'tidalDisplay':category!='lock-passage','sourceEndpointsBNG':r['routeBNG'],
            'evidence':r.get('evidence',[]),'note':r.get('note',r.get('reviewNote',''))})
    return {'epoch':'1900','connections':rows,'deferred':deferred,
        'reviewSha256':digest,
        'policy':'Reviewed geometric passages in the core scene. Mill and lock capacities are uncalibrated; a common display tide is not unrestricted hydraulic flow.',
        'pendingRegionalRoutes':['Limehouse Cut branch geometry','Upper Channelsea works corridor and remaining outer reaches'],
        'sourceReview':'data/maps/lower-lea-region/connection-review.json'}


def combined(data,tidal_only=False):
    return geometry([p for r in data['connections'] if not tidal_only or r['tidalDisplay'] for p in r['polygons']])
