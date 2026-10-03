"""Interpret working surfaces inside mapped parcels; keep mapped routes clear."""
import json
import math
import random
from pathlib import Path
from shapely.geometry import Polygon,LineString,Point
from shapely.affinity import rotate,translate
from shapely.geometry import box
from shapely.ops import unary_union,nearest_points
from abbey_support import station_footprints
from victoria_stone_grid import build_victoria_stone_grid

ROOT=Path(__file__).resolve().parents[1]
load=lambda path:json.loads((ROOT/path).read_text())
def parts(g):return [p for p in getattr(g,'geoms',[g]) if p.geom_type=='Polygon' and p.area>3]
def rings(g):return [[[list(q) for q in r.coords] for r in [p.exterior,*p.interiors]] for p in parts(g)]

def sawmill_stock(free,water,circulation):
    """Interpreted seasoning rows aligned with the registered sawmill ranges."""
    angle=36
    safe=free.buffer(-3).difference(water.buffer(4)).difference(circulation)
    local=rotate(safe,-angle,origin=(0,0))
    xmin,zmin,xmax,zmax=local.bounds
    rng=random.Random(7971900);objects=[]
    for row,z in enumerate(range(math.floor(zmin/6)*6,math.ceil(zmax),6)):
        # Broader transverse working aisles, plus some empty stack positions.
        if row%6==3:continue
        for x in range(math.floor(xmin/12)*12,math.ceil(xmax),12):
            if rng.random()<.17:continue
            kind='deals' if rng.random()<.6 else 'boards'
            length=rng.choice([4.5,5.4,6.3,7.2]);width=rng.choice([1.9,2.2,2.5])
            footprint=rotate(translate(box(-length/2-.12,-width/2-.08,length/2+.12,width/2+.08),xoff=x,yoff=z),angle,origin=(0,0))
            if not safe.covers(footprint.buffer(1)):continue
            centre=footprint.centroid
            objects.append({'x':round(centre.x,3),'z':round(centre.y,3),'kind':kind,
              'angle':-math.radians(angle),'length':length,'width':width,
              'layers':rng.randint(12,19) if kind=='deals' else rng.randint(18,26),
              'shade':rng.randrange(3),'footprint':[list(p) for p in footprint.exterior.coords]})
    return objects

def build():
    plan=load('docs/data/ground-plan.json');factories=load('docs/data/factory-buildings.json')
    frontages=load('docs/data/high-street-frontages.json');infra=load('docs/data/infrastructure.json')
    names={s['id']:s['name'] for s in factories['sites']}
    buildings=unary_union([Polygon(p['outer'],p['holes']) for b in factories['buildings']+frontages['buildings'] for p in b['renderPolygons']])
    buildings=buildings.union(station_footprints(load('docs/data/abbey-station-plan.json')))
    live_holders=factories['holders']+[h for h in plan['neighbourhood']['holders'] if h['siteId']!=924]
    holders=unary_union([Point(h['x'],h['z']).buffer(h['radius']+.5) for h in live_holders])
    water=unary_union([Polygon(p[0],p[1:]) for r in plan['rivers']+factories['westContext']['rivers'] for p in r['polygons']])
    roads=unary_union([LineString(r['route']).buffer(r['width']/2+.4,cap_style=2) for r in infra['roads']])
    route_lines=unary_union([LineString(r['route']) for r in infra['roads']])
    chimneys=unary_union([Point(s['x'],s['z']).buffer(s['radius']*1.2+.25)
                         for s in factories['structures'] if s['kind']=='chimney'])
    oil=load('data/maps/oil-wharf-footprint-alignment.json')
    sugar=load('data/maps/sugar-house-footprint-alignment.json')
    west_sugar=load('data/maps/west-sugar-footprint-alignment.json')
    crystal_barber=load('data/maps/crystal-barber-footprint-alignment.json')
    tanks=unary_union([Point(s['x'],s['z']).buffer(s['radius']+.3)
                      for s in factories['structures'] if s['kind'] in {'tank','kiln'}])
    blocked=buildings.buffer(.15).union(holders).union(water.buffer(.45)).union(roads).union(chimneys).union(tanks)
    sawmill=load('data/maps/sawmill-yard.json')
    jute=load('data/maps/ritchie-jute.json')
    east=load('data/maps/east-channelsea-context-alignment.json')
    wharfs=load('data/maps/east-wharf-yards.json')['yards']
    sawmill_parcel=Polygon(sawmill['parcel'][0])
    track_space=sawmill_parcel.buffer(-1.2).difference(blocked.buffer(1.2))
    tracks=[]
    for row in sawmill['tracks']:
        clipped=LineString(row['points']).intersection(track_space)
        for line in getattr(clipped,'geoms',[clipped]):
            if line.geom_type=='LineString' and line.length>2:tracks.append({'id':row['id'],'points':[list(p) for p in line.coords]})
    from east_depot_tracks import build_east_depot_tracks
    tracks.extend(build_east_depot_tracks(east,infra,blocked))
    tracks_union=unary_union([LineString(t['points']) for t in tracks])
    # Give the restored full sawmill parcel precedence over anonymous context.
    western=factories['westContext'].get('sites',[])
    priority_ids={797,1017,9001,*[s['id'] for s in western],*[s['id'] for s in east['additionalYards']],*[s['id'] for s in wharfs]}
    source=[*east['additionalYards'],oil['yard'],sugar['yard'],west_sugar['yard'],*crystal_barber['yards'],{'id':797,'name':names[797],'polygons':[sawmill['parcel']]},
      {'id':1017,'name':names[1017],'polygons':[jute['parcel']]}]+western+[s for s in plan['sites'] if s['id'] not in priority_ids]+[{'id':-i-1,'name':'Western wharf context','polygons':[p]} for i,p in enumerate(factories['westContext']['yards'])]+wharfs
    used=Polygon();sites=[]
    for site in source:
        parcel=unary_union([Polygon(p[0],p[1:]) for p in site['polygons']])
        free=parcel.difference(blocked).difference(used);used=used.union(free)
        if free.area<20:continue
        name=site['name'] if site['id']==9001 else names.get(site['id'],site.get('name') or 'Industrial yard');lower=name.lower()
        kind='cinder' if any(v in lower for v in ['gas','foundry','boiler','asphalte']) else 'stone' if any(v in lower for v in ['lime','stone','terra cotta']) else 'earth'
        kind=site.get('surface',kind)
        stock='timber' if any(v in lower for v in ['saw','wood','fibre','rope']) else 'coal' if 'gas' in lower else 'stone' if kind=='stone' else 'iron' if any(v in lower for v in ['foundry','boiler','machin']) else 'barrels' if any(v in lower for v in ['oil','chemical','soap','distill','ink','varnish','howard']) else 'crates'
        if site['id']==1017:stock='bales'
        stock=site.get('stockType',stock)
        routes=[]
        for component in sorted(parts(free),key=lambda p:-p.area)[:3]:
            centre=component.representative_point();entry,road=nearest_points(component,route_lines)
            if entry.distance(road)>24:continue
            # Only show wear where a clear connection fits the open yard. Do
            # not guess paths through buildings or call these surveyed gates.
            route=LineString([entry,centre])
            if route.length>5 and component.buffer(.02).covers(route):routes.append([list(entry.coords[0]),list(centre.coords[0])])
        circulation=unary_union([LineString(r).buffer(3) for r in routes])
        if site['id'] in {797,13011}:circulation=circulation.union(tracks_union.buffer(3))
        safe=free.buffer(-2.2).difference(circulation).difference(water.buffer(4))
        # Small stock groups near ranges, never a blanket scattering over yards.
        safe=safe.intersection(buildings.buffer(14).difference(buildings.buffer(2)))
        rng=random.Random(site['id']+19400);objects=[]
        if site.get('allowStock',site['id'] in names) and not safe.is_empty:
            minx,minz,maxx,maxz=safe.bounds
            target=min(9,max(1,round(free.area/1800)))
            if site['id']==1017:target=3
            for _ in range(180):
                if len(objects)>=target:break
                x,z=rng.uniform(minx,maxx),rng.uniform(minz,maxz)
                if not safe.covers(Point(x,z).buffer(1.6)):continue
                if any(Point(x,z).distance(Point(o['x'],o['z']))<7 for o in objects):continue
                objects.append({'x':round(x,2),'z':round(z,2),'kind':stock,'angle':round(rng.uniform(-.3,.3),3)})
        if site['id']==797:objects=sawmill_stock(free,water,circulation)
        sites.append({'id':site['id'],'name':name,'surface':kind,'polygons':rings(free),
                      'bounds':list(free.bounds),'areaM2':round(free.area,2),'wearRoutes':routes,'stock':objects})
    surface=unary_union([Polygon(p[0],p[1:]) for s in sites for p in s['polygons']])
    extent=surface.bounds
    # Only exposed land edges feather into grass. Protect built edges, water,
    # road approaches, working stock and the interpreted circulation space.
    protected=unary_union([blocked.buffer(1.5),tracks_union.buffer(1.5),
      *[(Polygon(o['footprint']).buffer(1) if 'footprint' in o else Point(o['x'],o['z']).buffer(2.5)) for s in sites for o in s['stock']],
      *[LineString(r).buffer(2) for s in sites for r in s['wearRoutes']]])
    soft_edges=[]
    boundary=surface.boundary
    for edge in getattr(boundary,'geoms',[boundary]):
        count=max(1,math.ceil(edge.length/1.5))
        for i in range(count):
            point=edge.interpolate(i*edge.length/count);x,z=point.x,point.y
            radius=6+2.5*math.sin(x*.13+math.sin(z*.17))+1.5*math.sin(z*.31-x*.21)
            radius=min(radius,max(0,point.distance(protected)-.2))
            if radius>.65:soft_edges.append([round(x,3),round(z,3),round(radius,3)])
    result={'sites':sites,'bounds':[extent[0]-2,extent[1]-2,extent[2]+2,extent[3]+2],
      'workingGrids':[build_victoria_stone_grid()],
      'buildingEdges':[[list(q) for q in p.exterior.coords] for p in parts(buildings)],
      'softEdges':soft_edges,
      'tracks':tracks,'trackEvidence':sawmill['interpretation']+' Eastern depot siding centrelines follow OS; standard gauge, low yard elevation and sleepers are interpretations.',
      'evidence':'Parcel and building geometry from the existing GIS/map register. Surface materials, wear, damp patches and small stock groups are typological visual interpretations. Routes describe clear circulation space, not identified historical gates or roads.',
      'counts':{'sites':len(sites),'wearRoutes':sum(len(s['wearRoutes']) for s in sites),'stockGroups':sum(len(s['stock']) for s in sites)}}
    (ROOT/'docs/data/factory-yards.json').write_text(json.dumps(result,separators=(',',':'))+'\n')
    print('Factory yards:',result['counts'])

if __name__=='__main__':build()
