"""Build the mapped northern railway corridor with provisional vertical levels."""
import json,math
from pathlib import Path
import numpy as np
from scipy.interpolate import PchipInterpolator
from shapely.geometry import Polygon,LineString,Point,MultiPoint
from shapely.ops import unary_union,triangulate
from shapely import segmentize

ROOT=Path(__file__).resolve().parents[1]
def parts(g,kind='Polygon'):
    return [p for p in getattr(g,'geoms',[g]) if p.geom_type==kind and not p.is_empty]
def rings(g):
    return [[[list(q) for q in r.coords] for r in [p.exterior,*p.interiors]] for p in parts(g)]

def build_great_eastern(water,roads,buildings,sewer):
    raw=json.loads((ROOT/'data/maps/great-eastern-mainline.json').read_text())
    points=np.array(raw['route']);spline=PchipInterpolator(points[:,0],points[:,1])
    xs=np.linspace(points[0,0],points[-1,0],int((points[-1,0]-points[0,0])/2)+1)
    line=LineString(np.column_stack([xs,spline(xs)]))
    # Source outlines beyond the former north crop; avoid duplicate water faces.
    extra=unary_union([Polygon(p[0],p[1:]) for p in raw['northernWaterContext']]).difference(water)
    all_water=water.union(extra)
    sewer_line=LineString(sewer['route']);sewer_cross=line.intersection(sewer_line)
    assert sewer_cross.geom_type=='Point', 'Expected one sewer crossing'
    peak=line.project(sewer_cross)
    def height_at(distance):
        ratio=min(1,abs(distance-peak)/240)
        return raw['formationHeight']+(raw['sewerFormationHeight']-raw['formationHeight'])*(.5+.5*math.cos(math.pi*ratio))
    def height(x,z):return height_at(line.project(Point(x,z)))
    crest=raw['crestHalfWidth'];base=raw['baseHalfWidth']
    openings=all_water.buffer(2.5).union(roads.buffer(2)).union(sewer_line.buffer(sewer['baseWidth']/2+2))
    footprint=line.buffer(base,cap_style=2,join_style=2).difference(openings).difference(buildings.buffer(.5))
    samples=[]
    for p in parts(segmentize(footprint,4)):
        samples.extend(p.exterior.coords)
        for hole in p.interiors:samples.extend(hole.coords)
    stations=[]
    for distance in np.linspace(0,line.length,math.ceil(line.length/2)+1):
        c=line.interpolate(distance);a=line.interpolate(max(0,distance-.5));b=line.interpolate(min(line.length,distance+.5))
        dx,dz=b.x-a.x,b.y-a.y;length=math.hypot(dx,dz);nx,nz=-dz/length,dx/length
        stations.append([round(c.x,3),round(c.y,3),round(height_at(distance),3),nx,nz,float(distance)])
        for offset in [-base,-20,-14,-crest,0,crest,14,20,base]:
            q=Point(c.x+nx*offset,c.y+nz*offset)
            if footprint.covers(q):samples.append((q.x,q.y))
    def bank_height(x,z):
        fraction=max(0,min(1,(base-line.distance(Point(x,z)))/(base-crest)))
        return -.09+(height(x,z)+.09)*fraction
    mesh=[];tolerant=footprint.buffer(.00001)
    for triangle in triangulate(MultiPoint(samples)):
        if tolerant.covers(triangle):
            mesh.append([[x,round(bank_height(x,z),3),z] for x,z in list(triangle.exterior.coords)[:3]])
    walls=[]
    for polygon in parts(segmentize(footprint,3)):
        for ring in [polygon.exterior,*polygon.interiors]:
            for a,b in zip(ring.coords,list(ring.coords)[1:]):
                ha,hb=bank_height(*a),bank_height(*b)
                if max(ha,hb)>.5:walls.append([[a[0],ha,a[1]],[b[0],hb,b[1]]])
    bridges=[]
    for cut in parts(line.intersection(openings),'LineString'):
        if cut.length<1:continue
        start,end=sorted([line.project(Point(cut.coords[0])),line.project(Point(cut.coords[-1]))])
        bridges.append({'start':start,'end':end,'sewer':start<=peak<=end})
    corridor=line.buffer(crest,cap_style=2)
    obstruction=corridor.intersection(buildings).area
    assert obstruction<1, f'Rail formation overlaps registered buildings: {obstruction:.1f} m²'
    # Additional channel margins are low tidal banks, not new railway fill.
    banks=[]
    for p in [segmentize(LineString(q),2) for q in raw['northernWaterBankLines']]:
        ring=list(p.coords)
        for a,b in zip(ring,ring[1:]):
            dx,dz=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dz)
            if not length:continue
            mid=Point((a[0]+b[0])/2,(a[1]+b[1])/2)
            # Do not create a dam along a clipping seam through the source river.
            if mid.distance(water)<.1:continue
            normal=[-dz/length,dx/length]
            if all_water.covers(Point(mid.x+normal[0]*.1,mid.y+normal[1]*.1)):normal=[-normal[0],-normal[1]]
            banks.append([[a[0],.06,a[1]],[b[0],.06,b[1]],
              [b[0]+normal[0]*2,1.65,b[1]+normal[1]*2],[a[0]+normal[0]*2,1.65,a[1]+normal[1]*2]])
    return {**{k:raw[k] for k in ['id','name','tracks','trackSpacing','gauge','formationHeight','evidence']},
      'detailedMainline':True,'route':[[s[0],s[1]] for s in stations],
      'stations':stations,'embankment':mesh,'retainingEdges':walls,'bridges':bridges,
      'crossings':[],'crestHalfWidth':crest,'baseHalfWidth':base,'footprint':rings(footprint),
      'northernWater':rings(extra),'northernBanks':banks,'length':round(line.length,1),
      'sewerCrossing':{'point':list(sewer_cross.coords[0]),'chainage':peak,'surfaceHeight':sewer['height'],
                       'minimumSoffit':min(height_at(b['start'])-.65 for b in bridges if b['sewer'])}}
