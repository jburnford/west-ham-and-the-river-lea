"""Map-informed distant massing southwest of the Channelsea viewpoint."""
import json
import math
from pathlib import Path

import numpy as np
from shapely.geometry import Polygon, LineString, box
from shapely.ops import unary_union
from shapely import affinity

ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'docs/data/ground-plan.json').read_text())
traces=json.loads((ROOT/'data/maps/southwest-context-traces.json').read_text())
holders={h['id']:h for h in data['neighbourhood']['holders']}
a=np.array([[*c['pixel'],1] for c in traces['holderControls']])
b=np.array([[holders[c['id']]['x'],holders[c['id']]['z']] for c in traces['holderControls']])
transform=np.linalg.lstsq(a,b,rcond=None)[0]
residual=float(np.sqrt(np.mean(np.sum((a@transform-b)**2,axis=1))))
scale=traces['sourceSize'][0]/traces['tracePixelWidth']
def world(p): return np.array([p[0]*scale,p[1]*scale,1])@transform
river=unary_union([Polygon(p[0],p[1:]) for r in data['rivers'] for p in r['polygons']])
railways=unary_union([LineString(r['route']).buffer(7) for r in data['neighbourhood']['railways']])
sites={s['id']:unary_union([Polygon(p[0],p[1:]) for p in s['polygons']]) for s in data['sites']}
industrial_land=unary_union(list(sites.values()))
names={s['id']:s['name'] for s in data['sites']}
rows=[]; omitted=[]
for i,row in enumerate(traces['rows']):
    start,end=map(world,row['axis']);center=(start+end)/2
    width=float(np.linalg.norm(end-start));depth=row['width']*scale*np.sqrt(abs(np.linalg.det(transform[:2])))
    angle=math.degrees(math.atan2(end[1]-start[1],end[0]-start[0]))
    footprint=affinity.translate(affinity.rotate(box(-width/2,-depth/2,width/2,depth/2),angle),*center)
    if footprint.intersects(river.buffer(2)) or footprint.intersects(railways):
        omitted.append({'row':i,'reason':'approximate trace conflicts with existing mapped water or railway'});continue
    industrial_overlap=footprint.intersection(industrial_land).area/footprint.area
    if industrial_overlap>.15:
        omitted.append({'row':i,'reason':'approximate trace overlaps mapped industrial land',
                        'overlapFraction':round(industrial_overlap,3)});continue
    assert industrial_overlap<=.15
    rows.append({'id':f'southwest-row-{i+1}','area':row['area'],'x':round(float(center[0]),2),'z':round(float(center[1]),2),
                 'width':round(width,2),'depth':round(float(depth),2),'rotation':round(-angle,2),'wallHeight':6.4,
                 'bays':max(2,round(width/5.2)), 'evidence':'Approximate main row axis from southwest screenshot; model registration uses modern-base holder centres. Elevation and house divisions interpreted.'})

ranges=[]
for site_id in traces['industrialSites']:
    site=sites[site_id]
    usable=site.buffer(-3).difference(river.buffer(2)).difference(railways)
    if usable.is_empty:continue
    parts=[g for g in getattr(usable,'geoms',[usable]) if g.geom_type=='Polygon']
    if not parts:continue
    part=max(parts,key=lambda p:p.area);rectangle=part.minimum_rotated_rectangle
    corners=list(rectangle.exterior.coords);edges=[np.subtract(corners[i+1],corners[i]) for i in range(4)]
    axis=max(edges,key=np.linalg.norm);angle=math.degrees(math.atan2(axis[1],axis[0]));center=part.centroid
    aligned=affinity.rotate(part,-angle,origin=center)
    xmin,zmin,xmax,zmax=aligned.bounds
    # Several low ranges with open space between them, not a solid parcel block.
    for j,(zbase,length_factor) in enumerate([(zmin+7,.76),(zmax-7,.66)]):
        length=min(85,(xmax-xmin)*length_factor);depth=min(14,max(6,(zmax-zmin)*.22))
        rect=box(center.x-length/2,zbase-depth/2,center.x+length/2,zbase+depth/2)
        for _ in range(15):
            candidate=affinity.rotate(rect,angle,origin=center)
            if usable.covers(candidate):break
            rect=affinity.scale(rect,.88,.88,origin=rect.centroid)
        else:continue
        if candidate.area<40:continue
        c=candidate.centroid;length=rect.bounds[2]-rect.bounds[0];depth=rect.bounds[3]-rect.bounds[1]
        ranges.append({'siteId':site_id,'name':names[site_id],'x':round(c.x,2),'z':round(c.y,2),
                       'width':round(length,2),'depth':round(depth,2),'rotation':round(-angle,2),
                       'height':12 if site_id==419 else 7+(site_id+j)%5,
                       'evidence':'Interpreted distant range contained in mapped industrial site; courtyard massing informed by southwest screenshot.'})
        assert site.covers(candidate) and not candidate.intersects(river)

result={'source':traces['source'],'transform':transform.tolist(),'controlResidualMetres':round(residual,3),
        'registrationLimit':'Residual measures fit to the existing holder model only, not accuracy of historical sheet overlays. Historical building positions may differ by tens of metres.',
        'rows':rows,'industrialRanges':ranges,'omittedRows':omitted}
(ROOT/'docs/data/southwest-context.json').write_text(json.dumps(result,indent=2)+'\n')
print(f'Southwest: {len(rows)} distant terrace rows, {len(ranges)} contained industrial ranges; {len(omitted)} conflicting rows omitted. Holder-control fit {residual:.2f} m (not historical positional accuracy).')
