"""Build a self-contained viewer of the EPFL text labels inside the 1911 County Borough of West Ham.

Reads reference/epfl-london-os-text/londonos_texts_postcorrected.gpkg (EPSG:27700), keeps labels whose
centre falls inside docs/maps/data/WestHam_1911.geojson, reduces each text box to its four corners in
WGS84, and writes one HTML file with Leaflet and the data inline, over the NLS five-foot (1890s) tiles.

Output: reference/epfl-london-os-text/west-ham-text.html (under /reference/, ignored by Git).
"""
import html
import json
from pathlib import Path

import geopandas as gpd
from shapely.geometry import shape

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'reference/epfl-london-os-text/londonos_texts_postcorrected.gpkg'
OUT = ROOT / 'reference/epfl-london-os-text/west-ham-text.html'
BOUNDARY = ROOT / 'docs/maps/data/WestHam_1911.geojson'
LEAFLET = ROOT / 'docs/vendor/leaflet'
STATUS = {'claude_unchanged': 0, 'claude_corrected': 1, 'excluded_nonletter_unchanged': 2,
          'blank_unchanged': 3, 'model_error_unchanged': 4}


def main():
    borough = gpd.read_file(BOUNDARY).to_crs(27700)
    area = borough.union_all()
    labels = gpd.read_file(SRC, bbox=tuple(area.bounds), engine='pyogrio')
    labels = labels[labels.geometry.centroid.within(area)].copy()
    labels['box'] = labels.geometry.minimum_rotated_rectangle()
    boxes = gpd.GeoSeries(labels['box'], crs=27700).to_crs(4326)
    rows = []
    for (_, r), b in zip(labels.iterrows(), boxes):
        corners = [[round(y, 6), round(x, 6)] for x, y in list(b.exterior.coords)[:4]]
        rows.append([r['label_corrected'] or '', r['label_raw'] or '', STATUS.get(r['ocr_status'], 4), corners])
    outline = [[[round(y, 6), round(x, 6)] for x, y in poly.exterior.coords]
               for poly in getattr(borough.to_crs(4326).union_all(), 'geoms', [borough.to_crs(4326).union_all()])]
    counts = {k: sum(1 for x in rows if x[2] == v) for k, v in STATUS.items()}
    page = TEMPLATE.replace('/*LEAFLET_CSS*/', (LEAFLET / 'leaflet.css').read_text()) \
                   .replace('/*LEAFLET_JS*/', (LEAFLET / 'leaflet.js').read_text()) \
                   .replace('/*DATA*/', 'const LABELS=' + json.dumps(rows, ensure_ascii=False, separators=(',', ':'))
                            + ';const OUTLINE=' + json.dumps(outline, separators=(',', ':')) + ';') \
                   .replace('__COUNT__', f'{len(rows):,}') \
                   .replace('__CORRECTED__', f"{counts['claude_corrected']:,}")
    OUT.write_text(page)
    print(f'{len(rows):,} labels inside West Ham ({counts}); wrote {OUT} ({OUT.stat().st_size/1e6:.1f} MB)')


TEMPLATE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>OS five-foot text labels · West Ham, 1890s</title>
<style>/*LEAFLET_CSS*/</style>
<style>
html,body{margin:0;height:100%;font:14px/1.4 system-ui,sans-serif;color:#1d2726}
#map{position:absolute;inset:0 0 0 320px;background:#e6e2d5}
aside{position:absolute;left:0;top:0;bottom:0;width:320px;box-sizing:border-box;padding:14px 16px;background:#f7f4ea;border-right:1px solid #cfc8b4;display:flex;flex-direction:column;gap:10px}
h1{font-size:17px;margin:0}
p{margin:0;font-size:12.5px;color:#4b5654}
input[type=search]{width:100%;box-sizing:border-box;padding:7px 9px;font-size:14px;border:1px solid #b9b19b;border-radius:4px}
label{font-size:13px;display:flex;gap:6px;align-items:center}
.key span{display:inline-block;width:11px;height:11px;border-radius:2px;margin-right:5px;vertical-align:-1px}
#list{flex:1;overflow:auto;border-top:1px solid #d8d1bd;padding-top:6px;font-size:13px}
#list div{padding:3px 4px;cursor:pointer;border-radius:3px;display:flex;justify-content:space-between;gap:8px}
#list div:hover{background:#ebe4cf}
#list s{color:#9a5b2a}
.lbl{font:600 11px/1 system-ui,sans-serif;color:#0b3d6b;white-space:nowrap;text-shadow:0 0 2px #fff,0 0 2px #fff,0 0 3px #fff;pointer-events:none}
.lbl.c{color:#b4501b}.lbl.x{color:#666}
</style></head><body>
<aside>
  <h1>Text on the 1890s five-foot plan · West Ham</h1>
  <p>__COUNT__ labels inside the 1911 County Borough boundary, from the EPFL text-spotting of the OS London five-foot plan (1891–96), with a post-correction pass. __CORRECTED__ labels were changed by the correction.</p>
  <input type="search" id="q" placeholder="Search, e.g. B.M., Works, Abbey" autocomplete="off">
  <label><input type="checkbox" id="onlyc"> Corrected labels only</label>
  <label><input type="checkbox" id="showx"> Include non-letter labels (numbers, marks)</label>
  <label>Map <input type="range" id="op" min="0" max="100" value="80"></label>
  <div class="key"><span style="background:#1f6fb4"></span>unchanged <span style="background:#d2691e;margin-left:10px"></span>corrected <span style="background:#888;margin-left:10px"></span>non-letter</div>
  <p id="status"></p>
  <div id="list"></div>
  <p>Text appears on the map from zoom 17. Hover a box for raw and corrected text; click a list entry to go there. Map tiles: National Library of Scotland (CC-BY).</p>
</aside>
<div id="map"></div>
<script>/*LEAFLET_JS*/</script>
<script>/*DATA*/</script>
<script>
const COLORS=['#1f6fb4','#d2691e','#888','#888','#c00'];
const map=L.map('map',{preferCanvas:true,maxZoom:20,zoomSnap:.5}).setView([51.525,0.012],14);
const tiles=L.tileLayer('https://mapseries-tilesets.s3.amazonaws.com/london_1890s/{z}/{x}/{y}.png',{maxNativeZoom:18,maxZoom:20,opacity:.8,attribution:'Reproduced with the permission of the <a href="https://maps.nls.uk/">National Library of Scotland</a>'}).addTo(map);
L.polygon(OUTLINE,{color:'#a0522d',weight:2,fill:false,dashArray:'4 5',interactive:false}).addTo(map);
const renderer=L.canvas({padding:.3});
const items=LABELS.map(([t,raw,s,c])=>{const lat=(c[0][0]+c[2][0])/2,lng=(c[0][1]+c[2][1])/2;return {t,raw,s,c,lat,lng,low:(t+' '+raw).toLowerCase()};});
const boxes=L.layerGroup().addTo(map), texts=L.layerGroup().addTo(map);
const $=id=>document.getElementById(id);
let shown=[];
function visible(){const q=$('q').value.trim().toLowerCase(),oc=$('onlyc').checked,sx=$('showx').checked;
  return items.filter(i=>(sx||i.s!==2)&&(!oc||i.s===1)&&(!q||i.low.includes(q)));}
function drawBoxes(){boxes.clearLayers();
  for(const i of shown){const p=L.polygon(i.c,{renderer,color:COLORS[i.s],weight:1,fillOpacity:.18});
    p.bindTooltip(i.s===1?`<b>${esc(i.t)}</b><br><s>${esc(i.raw)}</s> → corrected`:`<b>${esc(i.t)}</b>`,{sticky:true});boxes.addLayer(p);}}
function drawTexts(){texts.clearLayers(); if(map.getZoom()<17) return;
  const b=map.getBounds().pad(.1); let n=0;
  for(const i of shown){ if(!b.contains([i.lat,i.lng])) continue; if(++n>2500) break;
    texts.addLayer(L.marker([i.lat,i.lng],{interactive:false,icon:L.divIcon({className:'',html:`<div class="lbl ${i.s===1?'c':i.s===2?'x':''}" style="transform:translate(-50%,-50%)">${esc(i.t)}</div>`,iconSize:[0,0]})}));}}
function drawList(){const max=400;
  $('status').textContent=`${shown.length.toLocaleString()} labels shown`+(shown.length>max?` · list shows the first ${max}`:'');
  $('list').innerHTML=shown.slice(0,max).map((i,k)=>`<div data-k="${k}"><span>${esc(i.t)||'<i>(blank)</i>'}</span>${i.s===1?`<s>${esc(i.raw)}</s>`:''}</div>`).join('');}
function update(){shown=visible();drawBoxes();drawTexts();drawList();}
function esc(s){return String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}
$('list').addEventListener('click',e=>{const d=e.target.closest('[data-k]');if(!d)return;const i=shown[+d.dataset.k];map.setView([i.lat,i.lng],18.5);});
let timer;$('q').addEventListener('input',()=>{clearTimeout(timer);timer=setTimeout(update,200);});
$('onlyc').addEventListener('change',update);$('showx').addEventListener('change',update);
$('op').addEventListener('input',e=>tiles.setOpacity(e.target.value/100));
map.on('moveend zoomend',drawTexts);
update();
</script></body></html>
"""

if __name__ == '__main__':
    main()
