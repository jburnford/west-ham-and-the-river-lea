"""Native cached review panels and source-outline overlays for the river system."""
import json,hashlib
from factory_map_sources import mosaic
from PIL import Image,ImageDraw
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'reference/lower-lea-connection-review'
r=json.load(open(ROOT/'docs/data/lower-lea-region/index.json'))
areas={'lea-bridge-head':(535150,186250,536500,187350,16),'old-ford-network':(536800,184200,537600,184750,17),'channelsea-route':(537500,184950,537880,185340,17),
       'lea-bridge-network':(535750,186100,537100,187400,16),'limehouse-cut-network':(536100,180650,538400,182550,16),
       'hackney-crossings':(536550,185000,537050,185550,17),'bromley-passage':(538020,182030,538340,182420,17)}
meta={}
for name,(e0,n0,e1,n1,z) in areas.items():
 a,w,p=mosaic((e0-538900,183209-n1,e1-538900,183209-n0),zoom=z,layer='os-six-inch-2nd')
 path=out/(name+'.png');im=Image.fromarray(a);im.save(path)
 meta[name]={'path':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'zoom':z,'boundsBNG':[e0,n0,e1,n1],'size':[a.shape[1],a.shape[0]],'cornersBNG':(w([[0,0],[a.shape[1],0],[a.shape[1],a.shape[0]],[0,a.shape[0]]])*[1,-1]+[538900,183209]).tolist()}
 d=ImageDraw.Draw(im)
 for k,color in [('Lower_River_Lea','red'),('Water_1895','magenta')]:
  for row in r['layers'][k]:
   for poly in row['polygons']:
    q=p([[e-538900,183209-n]for e,n in poly[0]]);d.line([tuple(v)for v in q],fill=color,width=2)
    xs,ys=q[:,0],q[:,1]
    if max(xs)>0 and min(xs)<a.shape[1] and max(ys)>0 and min(ys)<a.shape[0]:
     d.text((max(0,min(a.shape[1]-70,xs.mean())),max(0,min(a.shape[0]-20,ys.mean()))),row['id'].split('-')[-1],fill=color,stroke_width=1)
 im.save(out/(name+'-source-overlay.png'))
(out/'river-system-panels.json').write_text(json.dumps(meta,indent=2)+'\n')
