"""Source-map overlay for the district road additions; archive imagery stays outside docs/."""
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/book-website-matplotlib')
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from factory_map_sources import mosaic
ROOT=Path(__file__).resolve().parents[1]
d=json.loads((ROOT/'data/maps/district-road-traces.json').read_text())
f=json.loads((ROOT/'docs/data/factory-buildings.json').read_text())
im,_,pixel=mosaic([-1450,-650,250,600])
fig,ax=plt.subplots(figsize=(22,16));ax.imshow(im)
for b in f['buildings']:
 for p in b['renderPolygons']:
  xy=pixel(p['outer']+[p['outer'][0]]);ax.plot(xy[:,0],xy[:,1],color='blue',lw=.3,alpha=.5)
for i,r in enumerate(d['roads']):
 p=pixel(r['points']);ax.plot(p[:,0],p[:,1],color='red',lw=1.5)
 ax.text(*p[len(p)//2],str(i+1),color='red',fontsize=10,bbox={'facecolor':'white','alpha':.8,'pad':1})
 for b in r['bridgeSpans']:
  p=pixel(b['points']);ax.plot(p[:,0],p[:,1],color='lime',lw=4)
ax.set(xlim=(600,3400),ylim=(3250,100),title='1893 OS: new streets in red, bridge spans in green, factory ranges in blue')
fig.savefig(ROOT/'reference/district-streets/trace-overlay.png',dpi=100,bbox_inches='tight');plt.close(fig)
print('Street overlay saved outside docs/.')
