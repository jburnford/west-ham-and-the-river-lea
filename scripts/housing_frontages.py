"""Break coarse terrace axes at independently mapped street junctions."""
import math
from shapely.geometry import Polygon, LineString, Point
from shapely.ops import unary_union


def split_at_streets(spec, roads):
    angle = math.radians(-spec['rotation'])
    ux, uz = math.cos(angle), math.sin(angle)
    x, z, width, depth = (spec[k] for k in ['x', 'z', 'width', 'depth'])
    axis = LineString([(x-ux*width/2,z-uz*width/2),(x+ux*width/2,z+uz*width/2)])
    corners = [(px+sign*(-uz)*depth/2,pz+sign*ux*depth/2)
               for (px,pz),sign in [(axis.coords[0],-1),(axis.coords[1],-1),(axis.coords[1],1),(axis.coords[0],1)]]
    envelope = Polygon(corners)
    cuts=[]; names=[]
    for name,line,road_width in roads:
        overlap=envelope.intersection(line.buffer(road_width/2+.35,cap_style=2,join_style=2))
        if overlap.area < .05: continue
        names.append(name)
        # Project the overlap onto the long axis, retaining rectangular ranges.
        points=list(overlap.convex_hull.exterior.coords)
        distances=[axis.project(Point(p)) for p in points]
        lo,hi=max(0,min(distances)-.2),min(width,max(distances)+.2)
        if hi-lo>.05: cuts.append(LineString([axis.interpolate(lo),axis.interpolate(hi)]).buffer(.01))
    if not cuts:return [spec]
    remaining=axis.difference(unary_union(cuts))
    parts=[p for p in getattr(remaining,'geoms',[remaining]) if p.geom_type=='LineString' and p.length>=5]
    retained=sum(p.length for p in parts)/width
    if retained<.55:
        raise ValueError(f"Recheck frontage {spec['id']}: only {retained:.0%} remains at {names}")
    result=[]
    for i,part in enumerate(parts):
        c=part.interpolate(.5,normalized=True);a,b=list(part.coords)[0],list(part.coords)[-1]
        footprint=[[round(px+sign*(-uz)*depth/2,2),round(pz+sign*ux*depth/2,2)]
                   for (px,pz),sign in [(a,-1),(b,-1),(b,1),(a,1)]]
        result.append({**spec,'id':spec['id']+f'-part-{i+1}','sourceRowId':spec['id'],
                       'x':round(c.x,2),'z':round(c.y,2),'width':round(part.length,2),
                       'bays':max(2,round(part.length/5.2)),'footprint':footprint,
                       'junctionAudit':{'streets':names,'retainedFraction':round(retained,3),
                         'evidence':'Coarse row envelope divided at map-traced street junctions; individual end-house footprints remain approximate.'}})
    return result
