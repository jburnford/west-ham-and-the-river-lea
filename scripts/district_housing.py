"""Apply the recorded district housing review, retaining source and block identity."""
import json, math
from pathlib import Path
from pyproj import Transformer
from shapely.geometry import Polygon, Point, box
from shapely import affinity
from shapely.ops import unary_union
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text())
def rectangle(r):return affinity.translate(affinity.rotate(box(-r['width']/2,-r['depth']/2,r['width']/2,r['depth']/2),-r['rotation']),r['x'],r['z'])
def sheet_point(sheet,p):
    if sheet=='scene':return p
    sheets=read('data/maps/os-neighbourhood-traces.json')['sheets'];s=sheets[sheet]
    if 'registrationToSheet' in s:
        a=[complex(*c['pixel']) for c in s['controls']];b=[complex(*c['target']) for c in s['controls']];ma=sum(a)/len(a);mb=sum(b)/len(b)
        scale=sum((u-ma).conjugate()*(v-mb) for u,v in zip(a,b))/sum(abs(u-ma)**2 for u in a)
        q=scale*(complex(*p)-ma)+mb
        return sheet_point(s['registrationToSheet'],[q.real,q.imag])
    left,top,right,bottom=s['neatline'];west,south,east,north=s['bounds']
    e,n=Transformer.from_crs(4326,27700,always_xy=True).transform(west+(east-west)*(p[0]-left)/(right-left),north-(north-south)*(p[1]-top)/(bottom-top))
    return [e-538900,183209-n]

def apply_review(original,blocks):
    survey=read('data/maps/district-housing-review.json');rows={r['id']:r for r in original}
    for item in survey['rows']:
        old=rows.get(item['id'],{});r={**old,**item}
        if 'axis' in item:
            a,b=[sheet_point(item.get('sheet','scene'),p) for p in item['axis']]
            dx,dz=b[0]-a[0],b[1]-a[1]
            r.update(x=(a[0]+b[0])/2,z=(a[1]+b[1])/2,width=math.hypot(dx,dz),rotation=-math.degrees(math.atan2(dz,dx)))
        r.update(group=item.get('group',old.get('group','district')),wallHeight=item.get('wallHeight',6.4),districtReviewed=True,
                 sourceSheet=item.get('sheet',old.get('sourceSheet','scene')),addedReturn=not bool(old),
                 evidence=survey['evidence'],maxYardDepth=item.get('maxYardDepth',32))
        rows[r['id']]=r
    # The recorded block members enclose the rear plots; masks follow front edges,
    # so plots stop at cross streets and do not run through to the next block.
    for b in survey['blocks']:
        members=[rows[id] for id in b['members']]
        envelope=unary_union([rectangle(r) for r in members]).convex_hull
        if 'boundary' in b:envelope=Polygon([sheet_point(b.get('sheet','scene'),p) for p in b['boundary']])
        key='district-'+b['id'];blocks[key]=envelope
        for r in members:r['block']=key;r['maxYardDepth']=80
    return list(rows.values()),blocks

def fit_additions(rows, obstacles):
    """Fit new ranges and explicitly re-traced ranges to roads and neighbours.

    The source axis is retained in each record. Existing ranges only move when
    marked fitToStreet by a subsequent source review; Mill Meads stays fixed.
    """
    from shapely.geometry import LineString
    from shapely.ops import nearest_points
    road_data=read('docs/data/infrastructure.json')['roads']
    needs_fit=lambda r:r.get('districtReviewed') and (r.get('addedReturn') or r.get('fitToStreet'))
    retained=[r for r in rows if not needs_fit(r)]
    additions=[r for r in rows if needs_fit(r)]
    failures=[]
    for row in additions:
        row=dict(row)
        # Source main-body axes can sit well behind the frontage at this scale.
        # Fit the street face before trimming ends, keeping the street's mapped width.
        streets=[r for r in road_data if r['name']==row.get('street')]
        for street in streets:
            line=LineString(street['route']);centre=Point(row['x'],row['z'])
            target=nearest_points(centre,line)[1];angle=math.radians(-row['rotation']);normal=(-math.sin(angle),math.cos(angle))
            signed=(target.x-row['x'])*normal[0]+(target.y-row['z'])*normal[1]
            move=max(0,min(30,abs(signed)-street['width']/2-row['depth']/2-2))
            direction=1 if signed>0 else -1
            row['x']+=normal[0]*direction*move;row['z']+=normal[1]*direction*move
        nearby=[rectangle(r).buffer(.12) for r in retained if math.hypot(r['x']-row['x'],r['z']-row['z'])<(r['width']+row['width'])/2+50]
        blocked=unary_union([obstacles,*nearby])
        angle=math.radians(-row['rotation']);normal=(-math.sin(angle),math.cos(angle))
        best=None
        for shift in [0,.5,-.5,1,-1,1.5,-1.5,2,-2,3,-3,4,-4,5,-5]:
            for depth in [row['depth'],max(5.2,row['depth']-.8)]:
                cx=row['x']+normal[0]*shift;cz=row['z']+normal[1]*shift
                local=affinity.rotate(affinity.translate(blocked,-cx,-cz),row['rotation'],origin=(0,0))
                band=local.intersection(box(-row['width']/2-.01,-depth/2-.15,row['width']/2+.01,depth/2+.15))
                intervals=[box(g.bounds[0]-.15,-1,g.bounds[2]+.15,1) for g in getattr(band,'geoms',[band]) if not g.is_empty]
                line=LineString([(-row['width']/2,0),(row['width']/2,0)]).difference(unary_union(intervals))
                spans=[p for p in getattr(line,'geoms',[line]) if p.geom_type=='LineString' and p.length>=5.6]
                if not spans:continue
                span=max(spans,key=lambda p:p.length)
                if span.length<row['width']*.42:continue
                mid=span.interpolate(.5,normalized=True).x
                candidate={**row,'x':cx+math.cos(angle)*mid,'z':cz+math.sin(angle)*mid,'width':span.length,'depth':depth}
                if rectangle(candidate).intersection(blocked).area>.01:continue
                cost=(row['width']-span.length)+abs(shift)*1.4+(row['depth']-depth)*2
                if best is None or cost<best[0]:best=(cost,candidate,shift)
        if best is None:
            failures.append(row['id']);continue
        _,fitted,shift=best
        fitted['houseCount']=max(2,min(round(row['houseCount']*fitted['width']/row['width']),int(fitted['width']/2.8)))
        fitted['fitAdjustment']={'offsetM':shift,'sourceWidthM':row['width'],'retainedWidthM':fitted['width']}
        retained.append(fitted)
    if failures:raise ValueError('Re-read added housing ranges: '+', '.join(failures))
    return retained
