"""Continuous, provenance-labelled surface for a small controlled flood experiment."""
import hashlib
import json
from pathlib import Path
import numpy as np
from shapely import distance, points, line_locate_point
from shapely.geometry import LineString, Point, box
from historic_elevation import sample_grid, smooth
from manor_road import profile

ROOT=Path(__file__).resolve().parents[1]
load=lambda p:json.loads((ROOT/p).read_text())
config=load('data/maps/flood-demo-1900.json')
meta=load('docs/data/terrain-1900.json')
graph=load('docs/data/drainage-connections-1900.json')
infra=load('docs/data/infrastructure.json')
assert config['epoch']==meta['epoch']==graph['geometryEpoch']=='1900'
cs=config['cellSizeMetres'];x0,z0,x1,z1=config['bounds']
x=np.arange(x0+cs/2,x1,cs);z=np.arange(z0+cs/2,z1,cs);X,Z=np.meshgrid(x,z);ps=points(X,Z)
shape=(meta['height'],meta['width'])
def grid(key,dtype='<f4'):return np.fromfile(ROOT/'docs/data'/meta['files'][key],dtype=dtype).reshape(shape)
weight=sample_grid(grid('weight'),meta['bounds'],1,X,Z)
existing=sample_grid(grid('scene'),meta['bounds'],1,X,Z)+meta['verticalReference']['odnMinusSceneYMetres']
road_mask=sample_grid(grid('roadMask','u1'),meta['bounds'],1,X,Z)>0
drain_mask=sample_grid(grid('drainageMask','u1'),meta['bounds'],1,X,Z)>0
supported=(weight>=.999)&~road_mask&~drain_mask
controls=[c for c in meta['controls'] if c['position'][0]>=0 and c['position'][1]>=400]
# Fill the small gaps using the same period observations, separately by compartment.
base=np.zeros_like(X)
for eastern in [False,True]:
    local=[c for c in controls if (c['position'][0]>270)==eastern]
    ds=np.array([np.hypot(X-c['position'][0],Z-c['position'][1]) for c in local]);w=1/np.maximum(ds,.5)**2
    y=np.array([c['heightODNMetres'] for c in local])
    fit=(w*y[:,None,None]).sum(axis=0)/w.sum(axis=0)
    base=np.where((X>=270)==eastern,fit,base)
base=np.where(supported,existing,base)
kind=np.where(supported,1,0).astype('u1')  # observed-field interpolation vs estimated gap
roads=next(r for r in infra['roads'] if r.get('elevationProfile'))
p=roads['elevationProfile']
road_route=p['route']
# Reviewed N/S route continued only to the experiment's closed edges.
extended=[road_route[0][:1]+[z0-10],*road_route,road_route[-1][:1]+[z1+10]]
road_line=LineString(extended);road_d=distance(ps,road_line)
road_h=profile(p,X,Z)[0]+meta['verticalReference']['odnMinusSceneYMetres']
road_influence=1-smooth(p['widthMetres']/2,p['widthMetres']/2+3,road_d)
rail_names={r['name'] for r in graph['crossingAudit']['railwayIntersections']}
rail_routes=[r for r in infra['railways'] if r['name'] in rail_names]
rail_d=np.minimum.reduce([distance(ps,LineString(r['route'])) for r in rail_routes])
rail_influence=1-smooth(config['railTopHalfWidth'],config['railFootHalfWidth'],rail_d)
section=graph['culvertSection'];culvert=next(c for c in section['cases'] if c['id']==section['defaultCase'])
west=[e for e in graph['edges'] if e['id'] in ['west-first','west-second']]
west_route=[q for e in west for q in e['route']]
west_route=[[x0-4,west_route[0][1]],*west_route]
east_route=next(e['route'] for e in graph['edges'] if e['id']=='east-channel')
western=LineString(west_route);eastern=LineString(east_route)
channel_bed=np.full_like(X,100.)
channel_influence=np.zeros_like(X)
for line,invert,slope,westward in [(western,culvert['westInvertODN'],config['westernChannelSlope'],True),(eastern,culvert['eastInvertODN'],0,False)]:
    d=distance(ps,line);s=line_locate_point(line,ps)
    bed=invert-(line.length-s)*slope if westward else np.full_like(X,invert)
    f=1-smooth(config['channelBedWidthMetres']/2,config['channelTopWidthMetres']/2,d)
    active=f>channel_influence
    channel_bed=np.where(active,bed,channel_bed);channel_influence=np.maximum(f,channel_influence)
# Default surface includes local rail earthwork, paving and the two open approaches.
def surface(formation):
    h=base*(1-rail_influence)+formation*rail_influence
    h=h*(1-road_influence)+road_h*road_influence
    return h+(np.minimum(h,channel_bed)-h)*channel_influence
bed=surface(config['railFormationODN'])
kind=np.where(rail_influence>0,2,kind);kind=np.where(road_influence>0,3,kind);kind=np.where(channel_influence>0,4,kind)
def cell(pos):
    i=int((pos[0]-x0)/cs);j=int((pos[1]-z0)/cs)
    assert 0<=i<len(x) and 0<=j<len(z)
    return j*len(x)+i
cross=next(e for e in graph['edges'] if e['id']=='crossing')
west_cell=cell(cross['route'][0]);east_cell=cell(cross['route'][-1])
# Ensure the 2m cell receiving a portal has the barrel invert, not an averaged bank.
for i,h in [(west_cell,culvert['westInvertODN']),(east_cell,culvert['eastInvertODN'])]:
    bed.flat[i]=min(bed.flat[i],h);channel_bed.flat[i]=h;channel_influence.flat[i]=1;kind.flat[i]=4
boundaries=[]
for side,i,line in [('west',0,western),('east',len(x)-1,eastern)]:
    js=np.flatnonzero(distance(points(np.full(len(z),x[i]),z),line)<config['channelBedWidthMetres']/2+cs/2)
    assert len(js)>0
    for j in js:boundaries.append({'cell':int(j*len(x)+i),'side':side,'width':cs})
# No buildings are present in this field trial. Fail if later site geometry reaches it.
buildings=load('docs/data/factory-buildings.json')['buildings']
from shapely.geometry import Polygon
assert not any(Polygon(p['outer'],p['holes']).intersection(box(x0,z0,x1,z1)).area>.1 for b in buildings for p in b['renderPolygons'])
paths=['data/maps/flood-demo-1900.json','docs/data/terrain-1900.json','docs/data/infrastructure.json','docs/data/drainage-connections-1900.json','docs/data/factory-buildings.json']
paths += ['docs/data/'+meta['files'][k] for k in ['scene','weight','roadMask','drainageMask']]
arrays={k:np.round(v,6).ravel().tolist() for k,v in {'ground':base,'bed':bed,'railInfluence':rail_influence,'roadInfluence':road_influence,'roadHeight':road_h,'channelInfluence':channel_influence,'channelBed':channel_bed}.items()}
out={**config,'width':len(x),'height':len(z),'verticalReference':meta['verticalReference'],**arrays,'kind':kind.ravel().tolist(),
     'kindLegend':{'0':'estimated ground between supported areas','1':'supported historical field interpolation','2':'provisional railway earthwork','3':'map-based road profile / bounded continuation','4':'assumed drain section'},
     'supportedFieldFraction':float(supported.mean()),'boundaries':boundaries,
     'culvert':{**culvert,'westCell':west_cell,'eastCell':east_cell,'lengthMetres':section['lengthMetres'],'route':cross['route']},
     'routes':{'west':west_route,'east':east_route,'road':extended,'rail':[r['route'] for r in rail_routes]},
     'railwayHeightReview':section['railwayHeightReview'],
     'historicalValidation':{'status':'not event-calibrated','eventYears':[1888,1897,1904,1928],'waterBoundaryStatus':'synthetic test hydrographs','floodMarkODN':None},
     'inputHashes':{q:hashlib.sha256((ROOT/q).read_bytes()).hexdigest() for q in paths}}
assert np.isfinite(bed).all()
assert section['railwayHeightReview']['deckEstimateODN']-config['bridgeRoofAllowanceMetres']-config['railFormationRangeODN'][1]-config['railAboveFormationMetres']>3
(ROOT/'docs/data/flood-demo-1900.json').write_text(json.dumps(out,separators=(',',':'))+'\n')
print(f'Built {len(x)}x{len(z)} cells, {cs}m resolution, {100*supported.mean():.1f}% supported field grid; remaining surfaces explicitly classified.')
