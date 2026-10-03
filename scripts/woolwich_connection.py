"""Continue the existing branch through its mapped curve onto the main line."""
import json, math
from pathlib import Path
import numpy as np
from scipy.interpolate import CubicSpline
from shapely import segmentize, constrained_delaunay_triangles
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

ROOT=Path(__file__).resolve().parents[1]
def parts(g,kind='Polygon'):
    return [p for p in getattr(g,'geoms',[g]) if p.geom_type==kind and not p.is_empty]

def build_woolwich_connection(water,roads,buildings,mainline,station_formation_obstacles=None):
    raw=json.loads((ROOT/'data/maps/woolwich-northern-connection.json').read_text())
    points=np.array(raw['route']);dist=np.r_[0,np.cumsum(np.linalg.norm(np.diff(points,axis=0),axis=1))]
    main=LineString(mainline['route']);s=raw['mainlineJoinChainage']
    a,b=main.interpolate(s-.5),main.interpolate(s+.5)
    tangent=np.array([b.x-a.x,b.y-a.y]);tangent/=np.linalg.norm(tangent)
    tail=np.array([140.62,-272.37])-points[-1];tail/=np.linalg.norm(tail)
    spline=CubicSpline(dist,points,bc_type=((1,tangent),(1,tail)),axis=0)
    line=LineString(spline(np.linspace(0,dist[-1],math.ceil(dist[-1]/2)+1)))
    crest,base=raw['crestHalfWidth'],raw['baseHalfWidth']
    def height(d):
        t=min(1,d/460)
        return raw['formationHeight']+(raw['joinHeight']-raw['formationHeight'])*(.5+.5*math.cos(math.pi*t))
    northern_water=unary_union([Polygon(p[0],p[1:]) for p in mainline['northernWater']])
    openings=water.union(northern_water).buffer(2.5).union(roads.buffer(2))
    corridor=line.buffer(crest,cap_style=2,join_style=2)
    obstruction=corridor.intersection(buildings).area
    assert obstruction<1, f'Northern branch overlaps buildings: {obstruction:.1f} m²'
    footprint=line.buffer(base,cap_style=2,join_style=2).difference(openings).difference(buildings.buffer(.5))
    # Native station bodies bound interpreted earth toes only. The ordinary
    # building/crest assertion above remains intact. At the booking bridge the
    # reviewed obstacle already excludes the running crest and its shoulder.
    station_cut = (Polygon() if station_formation_obstacles is None
                   else station_formation_obstacles.buffer(.5))
    prior_earth_area=footprint.area
    footprint=footprint.difference(station_cut)
    # Dense transverse strips give the banks a flat crest and sloping toes;
    # polygon clipping preserves bridge openings at roads and waterways.
    stations=[]
    for d in np.linspace(0,line.length,math.ceil(line.length/2)+1):
        c=line.interpolate(d);a=line.interpolate(max(0,d-.5));b=line.interpolate(min(line.length,d+.5))
        dx,dz=b.x-a.x,b.y-a.y;length=math.hypot(dx,dz)
        stations.append([c.x,c.y,height(d),-dz/length,dx/length,float(d)])
    def bank_height(x,z):
        ratio=max(0,min(1,(base-line.distance(Point(x,z)))/(base-crest)))
        return -.09+(height(line.project(Point(x,z)))+.09)*ratio
    def point(s,v):return [s[0]+s[3]*v,s[1]+s[4]*v]
    mesh=[]
    for a,b in zip(stations,stations[1:]):
        for left,right in zip([-base,-crest,0,crest],[-crest,0,crest,base]):
            cell=Polygon([point(a,left),point(a,right),point(b,right),point(b,left)]).intersection(footprint)
            for poly in parts(cell):
                for tri in constrained_delaunay_triangles(poly).geoms:
                    mesh.append([[x,round(bank_height(x,z),3),z] for x,z in list(tri.exterior.coords)[:3]])
    walls=[]
    for polygon in parts(segmentize(footprint,3)):
        for ring in [polygon.exterior,*polygon.interiors]:
            for a,b in zip(ring.coords,list(ring.coords)[1:]):
                ha,hb=bank_height(*a),bank_height(*b)
                edge=LineString([a,b])
                if not station_cut.is_empty and edge.intersection(station_cut.boundary.buffer(.005)).length>.9*edge.length:
                    continue  # No invented elevated retaining wall at station.
                if max(ha,hb)>.5:walls.append([[a[0],ha,a[1]],[b[0],hb,b[1]]])
    bridges=[]
    for cut in parts(line.intersection(openings),'LineString'):
        if cut.length<1:continue
        start,end=sorted([line.project(Point(cut.coords[0])),line.project(Point(cut.coords[-1]))])
        bridges.append({'start':start,'end':end,'sewer':False})
    return {**raw,'detailedRailway':True,'route':[[s[0],s[1]] for s in stations],
            'stations':stations,'embankment':mesh,'retainingEdges':walls,'bridges':bridges,
            'crossings':[],'length':line.length,'footprint':[[[list(q) for q in r.coords] for r in [p.exterior,*p.interiors]] for p in parts(footprint)],
            'northernWater':[],'northernBanks':[],
            'stationFormationExclusionApplied':{'bankOnly':True,'priorEarthAreaM2':prior_earth_area,
                'excludedEarthAreaM2':prior_earth_area-footprint.area,
                'preservedCrestShoulderMetres':raw.get('stationFormationReview',{}).get('preservedCrestShoulderMetres',0)},
            'connection':{'mainlinePoint':raw['route'][0],'branchPoint':raw['route'][-1],'mainlineHeight':raw['joinHeight'],'branchHeight':raw['formationHeight']}}
