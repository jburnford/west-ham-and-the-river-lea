"""Apply reviewed passage locations to the existing scene without moving banks.

Widths are explicit visual assumptions, not surveyed discharge sections. Locks
remain separate from tidal seeds. Raw GIS and building footprints are untouched.
"""
import hashlib
import json
from pathlib import Path
from shapely.geometry import Polygon, LineString, Point
from shapely.ops import unary_union, nearest_points
import tide_levels as tl

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
    # A passage under a street with no bridge deck is culverted there (the House Mill
    # race under Three Mills Lane, task C): the street runs on over it, so the passage
    # is not drawn as open water or cut into the ground under the street.
    infrastructure=json.loads((ROOT/'docs/data/infrastructure.json').read_text())
    decks=unary_union([LineString(b['route']).buffer(b['width']/2+2,cap_style=2) for b in infrastructure['roadBridges']])
    streets={r['name']:LineString(r['route']).buffer(r['width']/2,cap_style=2,join_style=2) for r in infrastructure['roads'] if len(r['route'])>1}
    undecked=unary_union(list(streets.values())).difference(decks)
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
        culvert=patch.intersection(undecked)
        culverted=[name for name,g in streets.items() if g.intersection(culvert).area>.5] if culvert.area>.5 else []
        if culverted:
            # Cut square to the passage over the stretch under the street, so the new
            # shoreline is two straight lines (a cut along the street's outline left
            # slivers that float32 rounding reversed in the network mesh).
            under=line.intersection(undecked)
            stations=[line.project(Point(c)) for g in getattr(under,'geoms',[under]) for c in g.coords]
            cut=LineString([line.interpolate(min(stations)),line.interpolate(max(stations))]).buffer(width,cap_style=2)
            culvert=patch.intersection(cut);patch=patch.difference(cut)
        rows.append({'id':identifier,'channelIds':ids,'category':category,
            'route':list(line.coords),'polygons':rings(patch),'visualWidthMetres':width,
            'widthStatus':'inferred display width; not a hydraulic capacity',
            'bedSceneY':-.7,'bedStatus':'provisional submerged bed matching scene datum; not surveyed bathymetry',
            'capacity':None,'gateState':None,
            # A passage into a channel above the tidal limit (the Abbey Mill race,
            # data/maps/os-tide-levels.json) is the step between still head and tide.
            'tidalDisplay':category!='lock-passage' and not set(ids)&tl.ABOVE_TIDAL_LIMIT,'sourceEndpointsBNG':r['routeBNG'],
            'evidence':r.get('evidence',[]),'note':r.get('note',r.get('reviewNote','')),
            **({'culvertedUnder':culverted,'culvertAreaM2':round(culvert.area,2)} if culverted else {})})
    return {'epoch':'1900','connections':rows,'deferred':deferred,
        'reviewSha256':digest,
        'policy':'Reviewed geometric passages in the core scene. Mill and lock capacities are uncalibrated; a common display tide is not unrestricted hydraulic flow.',
        'pendingRegionalRoutes':['Limehouse Cut branch geometry','Upper Channelsea works corridor and remaining outer reaches'],
        'sourceReview':'data/maps/lower-lea-region/connection-review.json'}


def combined(data,tidal_only=False):
    return geometry([p for r in data['connections'] if not tidal_only or r['tidalDisplay'] for p in r['polygons']])
