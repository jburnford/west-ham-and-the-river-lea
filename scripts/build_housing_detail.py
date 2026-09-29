"""Interpret dense terraced housing and shared rear plots around mapped streets.

Source rows stay intact in ground-plan/southwest-context. This derived layer
records modest frontage adjustments and explicitly interpreted house plots.
"""
import json
import math
from pathlib import Path

from shapely import affinity, voronoi_polygons
from shapely.geometry import Polygon, Point, LineString, MultiPoint, box
from shapely.ops import unary_union, nearest_points
from abbey_support import station_footprints

ROOT = Path(__file__).resolve().parents[1]
def load(name):
    return json.loads((ROOT/name).read_text())
def rect(b):
    return affinity.translate(affinity.rotate(box(-b['width']/2,-b['depth']/2,b['width']/2,b['depth']/2),-b['rotation']),b['x'],b['z'])
def parts(shape):
    return [p for p in getattr(shape,'geoms',[shape]) if p.geom_type=='Polygon' and p.area>.3]
def rings(shape):
    return [[[list(p) for p in q.exterior.coords][:-1],*[list(map(list,r.coords))[:-1] for r in q.interiors]] for q in parts(shape)]
def local_rect(row,u0,v0,u1,v1):
    return affinity.translate(affinity.rotate(box(u0,v0,u1,v1),-row['rotation'],origin=(0,0)),row['x'],row['z'])
def world(row,u,v):
    theta=math.radians(-row['rotation']);c,s=math.cos(theta),math.sin(theta)
    return [row['x']+u*c-v*s,row['z']+u*s+v*c]

def mapped_refinement(original):
    from build_panorama_data import project, ORIGIN
    survey=load('data/maps/mill-meads-housing.json')
    sheet=load('data/maps/os-neighbourhood-traces.json')['sheets'][survey['sheet']]
    left,top,right,bottom=sheet['neatline'];west,south,east,north=sheet['bounds']
    def point(p):
        e,n=project(west+(east-west)*(p[0]-left)/(right-left),north-(north-south)*(p[1]-top)/(bottom-top))
        return [e-ORIGIN[0],ORIGIN[1]-n]
    rows={r['id']:r for r in original}
    for item in survey['rows']:
        a,b=point(item['a']),point(item['b']);dx,dz=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dz)
        previous=rows.get(item['id'],{})
        rows[item['id']]={**previous,'id':item['id'],'group':'district','x':(a[0]+b[0])/2,'z':(a[1]+b[1])/2,
                         'width':length,'depth':item['depth']*length/math.dist(item['a'],item['b']),
                         'rotation':-math.degrees(math.atan2(dz,dx)),'wallHeight':6.4,'houseCount':item['houseCount'],
                         'street':item['street'],'block':item['block'],'mappedRefinement':True,'maxYardDepth':60 if item['block'] else 18,
                         'clearanceAdjustment':item.get('clearanceAdjustment'),
                         'sourceSheet':survey['sheet'],'sourceAxis':[item['a'],item['b']],
                         'evidence':survey['evidence'],'addedReturn':not bool(previous)}
    return list(rows.values()),{key:Polygon([point(p) for p in ring]) for key,ring in survey['blocks'].items()}

def build():
    ground=load('docs/data/ground-plan.json');sw=load('docs/data/southwest-context.json')
    infra=load('docs/data/infrastructure.json');factories=load('docs/data/factory-buildings.json');frontages=load('docs/data/high-street-frontages.json')
    original=[{**r,'group':'district'} for r in ground['neighbourhood']['terraces']]+[{**r,'group':'southwest'} for r in sw['rows']]
    original,blocks=mapped_refinement(original)
    from district_housing import apply_review
    original,blocks=apply_review(original,blocks)
    rows=[]
    housing=[rect(r) for r in original]+[rect(r) for r in ground['neighbourhood']['houses']]
    factory=unary_union([Polygon(p['outer'],p['holes']) for b in factories['buildings']+frontages['buildings'] for p in b['renderPolygons']])
    factory=factory.union(station_footprints(load('docs/data/abbey-station-plan.json')))
    water=unary_union([Polygon(p[0],p[1:]) for r in ground['rivers']+factories['westContext']['rivers'] for p in r['polygons']])
    road_lines=[(r['name'],LineString(r['route']),r['width']) for r in infra['roads']]
    streets=unary_union([line.buffer(width/2+1.25,cap_style=2,join_style=2) for _,line,width in road_lines])
    rails=unary_union([LineString(r['route']).buffer(9) for r in infra['railways']])
    holders=unary_union([Point(h['x'],h['z']).buffer(h['radius']+1) for h in factories['holders']+ground['neighbourhood']['holders']])
    landscape=unary_union([factory.buffer(.3),water.buffer(2.5),rails,holders])
    fixed=landscape.union(streets)
    from district_housing import fit_additions
    original=fit_additions(original,landscape.union(unary_union([line.buffer(width/2+.25,cap_style=2,join_style=2) for _,line,width in road_lines])))
    fitted={r['id']:r for r in original}
    for block in load('data/maps/district-housing-review.json')['blocks']:
        if 'boundary' not in block:blocks['district-'+block['id']]=unary_union([rect(fitted[id]) for id in block['members']]).convex_hull
    housing=[rect(r) for r in original]+[rect(r) for r in ground['neighbourhood']['houses']]
    for index,row in enumerate(original):
        theta=math.radians(-row['rotation']);u=(math.cos(theta),math.sin(theta));normal=(-u[1],u[0])
        centre=Point(row['x'],row['z']);candidates=[]
        for name,line,width in road_lines:
            if (row.get('mappedRefinement') or row.get('districtReviewed')) and row.get('street') and name!=row['street']:continue
            if line.distance(centre)>row['width']/2+40:continue
            for a,b in zip(line.coords,list(line.coords)[1:]):
                length=math.dist(a,b)
                if not length or abs(((b[0]-a[0])*u[0]+(b[1]-a[1])*u[1])/length)<.85:continue
                segment=LineString([a,b]);target=nearest_points(centre,segment)[1]
                direction=1 if (target.x-centre.x)*normal[0]+(target.y-centre.y)*normal[1]>0 else -1
                access=LineString([centre,target]).difference(housing[index].buffer(.1))
                if any(access.intersection(q).length>.2 for j,q in enumerate(housing) if j!=index):continue
                candidates.append((segment.distance(centre)-width/2,name,segment,width,direction))
        if not candidates:raise ValueError(f"No clear parallel frontage: {row['id']}")
        _,name,street,width,sign=min(candidates,key=lambda x:x[0])
        samples=[Point(*world(row,row['width']*t,sign*row['depth']/2)) for t in [-.4,-.2,0,.2,.4]]
        gap=min(p.distance(street)-width/2 for p in samples)
        desired=0 if row.get('mappedRefinement') or row.get('districtReviewed') else max(0,min(8,gap-1.6));shift=desired
        others=unary_union([q for j,q in enumerate(housing) if j!=index])
        blockers=fixed.union(others).union(unary_union([rect(r) for r in rows]))
        while shift>.1:
            candidate=affinity.translate(housing[index],normal[0]*sign*shift,normal[1]*sign*shift)
            if candidate.intersection(blockers).area<.05:break
            shift=max(0,shift-.5)
        moved={**row,'sourceCentre':[row['x'],row['z']],'x':round(row['x']+normal[0]*sign*shift,3),'z':round(row['z']+normal[1]*sign*shift,3),
               'frontSign':sign,'frontStreet':name,'frontageShiftM':round(shift,3),'bays':row.get('houseCount',max(2,round(row['width']/4.6)))}
        moved['footprint']=[list(p) for p in rect(moved).exterior.coords][:-1]
        rows.append(moved)
    occupied=unary_union([fixed,*[rect(r) for r in rows],*[rect(r) for r in ground['neighbourhood']['houses']]])
    seeds=[];homes=[]
    for row in rows:
        bay=row['width']/row['bays'];rear=-row['frontSign']
        for i in range(row['bays']):
            u=-row['width']/2+(i+.5)*bay;v=rear*(row['depth']/2+.15)
            seeds.append(world(row,u,v));homes.append((row,i,u,bay,rear))
    cells=list(voronoi_polygons(MultiPoint(seeds),ordered=True).geoms)
    plots=[];courts=[];extensions=[];privies=[]
    for cell,(row,i,u,bay,rear),seed in zip(cells,homes,seeds):
        v0=rear*row['depth']/2;v1=v0+rear*row.get('maxYardDepth',18)
        region=local_rect(row,u-bay/2,min(v0,v1),u+bay/2,max(v0,v1))
        if row.get('block'):region=region.intersection(blocks[row['block']])
        clipped=cell.intersection(region).difference(occupied)
        # Keep the component attached to this house, not isolated scraps beyond obstructions.
        touching=[q for q in parts(clipped) if q.distance(Point(seed))<.3]
        if not touching:continue
        plot=max(touching,key=lambda q:q.area)
        if plot.area<3:continue
        record={'id':f"{row['id']}-yard-{i+1}",'rowId':row['id'],'bay':i,'polygons':rings(plot),'areaM2':round(plot.area,3)}
        plots.append(record)
        # Modest scullery and privy, within this plot. Shared party-wall side alternates in pairs.
        side=-1 if i%2==0 else 1
        eu=u+side*(bay/2-1.03);ev=v0+rear*1.4
        ext=local_rect(row,eu-.82,ev-1.4,eu+.82,ev+1.4)
        if plot.buffer(.02).covers(ext):
            extensions.append({'plotId':record['id'],'rowId':row['id'],'u':eu,'v':ev,'width':1.64,'depth':2.8,'height':2.65,'footprint':rings(ext)[0][0]})
        for distance in [14,11,8,5]:
            pv=v0+rear*distance;pu=u-side*(bay/2-.82)
            privy=local_rect(row,pu-.65,pv-.7,pu+.65,pv+.7)
            if plot.buffer(.01).covers(privy) and not privy.intersects(ext):
                privies.append({'plotId':record['id'],'rowId':row['id'],'u':pu,'v':pv,'width':1.3,'depth':1.4,'height':1.9,'footprint':rings(privy)[0][0]});break
    # Union lines once: adjacent plots share the same rear/party wall, with no automatic back lane.
    boundaries=unary_union([Polygon(p['polygons'][0][0],p['polygons'][0][1:]).boundary for p in plots])
    rearwalls=boundaries.difference(unary_union([rect(r).buffer(.1) for r in rows])).difference(fixed.buffer(.12))
    walls=[]
    for line in getattr(rearwalls,'geoms',[rearwalls]):
        if line.geom_type!='LineString':continue
        for a,b in zip(line.coords,list(line.coords)[1:]):
            if math.dist(a,b)>.35:walls.append([list(a),list(b)])
    # Forecourts fill the broad accidental grass margins; street paving remains the mapped surface.
    court_blockers=unary_union([landscape,*[rect(r) for r in rows],*[rect(r) for r in ground['neighbourhood']['houses']],*[Polygon(p['polygons'][0][0],p['polygons'][0][1:]) for p in plots],*[line.buffer(width/2+.02,cap_style=2,join_style=2) for _,line,width in road_lines]])
    for row in rows:
        sign=row['frontSign'];v0=sign*row['depth']/2;v1=v0+sign*10
        poly=local_rect(row,-row['width']/2,min(v0,v1),row['width']/2,max(v0,v1)).difference(court_blockers)
        court=unary_union([q for q in parts(poly) if q.distance(rect(row))<.05])
        if not court.is_empty:
            courts.append({'rowId':row['id'],'polygons':rings(court)})
            court_blockers=court_blockers.union(court)
    result={'evidence':'Mapped row envelopes and streets underpin a visual interpretation of dense two-storey terraces. Household widths, frontage adjustments, shared rear plots, walls, sculleries and privies are estimated. No new rear access lanes are implied.',
            'rows':rows,'plots':plots,'walls':walls,'forecourts':courts,'extensions':extensions,'privies':privies,
            'counts':{'rows':len(rows),'houses':len(homes),'rearYards':len(plots),'sculleries':len(extensions),'privies':len(privies),'adjustedFrontages':sum(r['frontageShiftM']>.1 for r in rows)}}
    (ROOT/'docs/data/housing-detail.json').write_text(json.dumps(result,separators=(',',':'))+'\n')
    print(result['counts'])

if __name__=='__main__':build()
