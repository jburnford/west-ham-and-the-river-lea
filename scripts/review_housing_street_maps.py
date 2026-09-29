"""Overlay corrected housing axes and streets on their original map sheets.

Blue envelopes precede the generated junction splits; omitted axes are excluded.
"""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
import os
os.chdir(ROOT)
from PIL import Image,ImageDraw
import json,math
Image.MAX_IMAGE_PIXELS=300000000
p=json.load(open('data/maps/os-neighbourhood-traces.json'));roads=json.load(open('data/maps/road-traces.json'))['roads'];h=json.load(open('data/maps/housing-road-traces.json'));roads=[r for r in roads if r['name'] not in h['replaceNames']]+h['roads']
Path('reference/housing-street-audit').mkdir(parents=True,exist_ok=True)
for sheet in ['32','22','overview']:
 width=2048 if sheet=='overview' else 1888
 src=Image.open(p['sheets'][sheet]['file']).convert('RGB');src=src.resize((width,round(src.height*width/src.width)));d=ImageDraw.Draw(src)
 for i,r in enumerate(p['rows']):
  if r.get('sheet','32')!=sheet or h['housingCorrections'].get('os-row-'+str(i+1),{}).get('omit'):continue
  r={**r,**h['housingCorrections'].get('os-row-'+str(i+1),{})};a,b=r['a'],r['b'];dx=b[0]-a[0];dy=b[1]-a[1];n=math.hypot(dx,dy);v=[-dy/n*r['depth']/2,dx/n*r['depth']/2]
  corners=[(a[0]-v[0],a[1]-v[1]),(b[0]-v[0],b[1]-v[1]),(b[0]+v[0],b[1]+v[1]),(a[0]+v[0],a[1]+v[1])]
  d.line(corners+[corners[0]],fill='blue',width=2);d.text(((a[0]+b[0])/2,(a[1]+b[1])/2),str(i+1),fill='blue',stroke_width=1,stroke_fill='white')
 for r in roads:
  if r['sheet']!=sheet:continue
  pts=[(x*width/r['pixelWidth'],y*width/r['pixelWidth']) for x,y in r['points']];d.line(pts,fill='red',width=2)
 src.save('reference/housing-street-audit/updated-'+sheet+'.png')
 print(sheet,src.size)
