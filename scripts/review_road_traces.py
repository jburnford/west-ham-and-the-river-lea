"""Overlay traced centrelines on source maps for local review (never public assets)."""
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/book-website-matplotlib')
import json
from pathlib import Path
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
Image.MAX_IMAGE_PIXELS=300000000
roads=json.loads((ROOT/'data/maps/road-traces.json').read_text())['roads']
sources={'32':'reference/neighbourhood-context/os-viii32.jpg',
 '42':'reference/neighbourhood-context/os-viii42.jpg',
 'overview':'reference/neighbourhood-context/northern-housing-overview.png',
 'southwest':'reference/author-map-extracts-2026-09-24/Screenshot 2026-09-24 112719c.png'}
for sheet,file in sources.items():
    im=Image.open(ROOT/file);im=im.resize((1800,round(im.height*1800/im.width)))
    fig,ax=plt.subplots(figsize=(18,13));ax.imshow(im)
    for i,r in enumerate(roads):
        if r['sheet']!=sheet:continue
        p=[(x*1800/r['pixelWidth'],y*1800/r['pixelWidth']) for x,y in r['points']]
        ax.plot(*zip(*p),color='#b01828',lw=1,alpha=.85)
        ax.text(*p[0],str(i+1),fontsize=8,color='#142a82')
    ax.set(xlim=(0,1800),ylim=(im.height,0),title='Source-map centreline review: '+sheet+' (numbers follow road-traces.json)')
    fig.savefig(ROOT/f'scenes/channelsea-sewer-panorama/review/road-map-{sheet}.png',dpi=120,bbox_inches='tight');plt.close(fig)
print('Four map overlays exported outside docs/.')
