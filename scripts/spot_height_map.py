#!/usr/bin/env python3
"""Build an interactive Leaflet map of every merged OS height mark.

Reads reference/spot-heights/heights.geojson and manifest.json and writes
reference/spot-heights/map.html, a single self-contained page (Leaflet from a
CDN; the 1890s basemaps are the local NLS tiles in reference/nls-tiles).

Points: colour = height band (one-hue blue ramp, validated), shape = type
(circle spot height, triangle bench mark), red ring = disputed.
Coverage: the 3x3-tile core of every five-foot mosaic, grey outline if read,
dashed orange if still unread, so the gaps are visible.
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SH = ROOT / "reference" / "spot-heights"
OUT = SH / "map.html"
# approximate West Ham study box (BNG E0, E1, N0, N1); a rectangle, not the parish boundary
BOX = (536800, 542700, 180400, 186700)


def tile_ll(x, y, z=18):
    n = 2 ** z
    lon = x / n * 360 - 180
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    return lat, lon


def main():
    g = json.loads((SH / "heights.geojson").read_text())
    pts = []
    for f in g["features"]:
        p = f["properties"]
        lon, lat = f["geometry"]["coordinates"][:2]
        layer = "25-inch" if "25" in p.get("layer", "") else "five-foot"
        notes = (p.get("notes") or "").replace("\n", " ")
        pts.append([
            round(lat, 7), round(lon, 7), p["value_ft"],
            "B.M." if p.get("type") == "bench_mark" else "spot",
            p.get("setting") or "unknown", p.get("confidence", ""), layer,
            1 if p.get("disputed") else 0, p.get("n_readings", 1),
            len(p.get("readers", [])), notes[:180], p.get("id", ""),
            round(p.get("bng_e", 0)), round(p.get("bng_n", 0)),
        ])

    man = json.loads((SH / "manifest.json").read_text())["mosaics"]
    cells = []
    for m in man:
        if not m["name"].startswith("m18_") or not m.get("available"):
            continue
        x0, y0 = m["x0"], m["y0"]
        n_lat, w_lon = tile_ll(x0, y0)
        s_lat, e_lon = tile_ll(x0 + 3, y0 + 3)
        e, n = m["centroid_bng"]
        inside = BOX[0] <= e <= BOX[1] and BOX[2] <= n <= BOX[3]
        status = "read" if m.get("done") else ("unread" if inside else "outside")
        cells.append([round(s_lat, 6), round(w_lon, 6), round(n_lat, 6),
                      round(e_lon, 6), status, m["name"]])

    n_read = sum(1 for c in cells if c[4] == "read")
    n_unread = sum(1 for c in cells if c[4] == "unread")
    from pyproj import Transformer
    tr = Transformer.from_crs(27700, 4326, always_xy=True)
    sw = tr.transform(BOX[0], BOX[2]); ne = tr.transform(BOX[1], BOX[3])
    box = [round(sw[1], 6), round(sw[0], 6), round(ne[1], 6), round(ne[0], 6)]
    html = TEMPLATE.replace("__POINTS__", json.dumps(pts, separators=(",", ":")))
    html = html.replace("__CELLS__", json.dumps(cells, separators=(",", ":")))
    html = html.replace("__BOX__", json.dumps(box))
    html = html.replace("__NPTS__", f"{len(pts):,}")
    html = html.replace("__NREAD__", str(n_read)).replace("__NUNREAD__", str(n_unread))
    OUT.write_text(html)
    print(f"{len(pts)} marks, {n_read} read / {n_unread} unread five-foot sheets -> {OUT}")


TEMPLATE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>West Ham OS height marks, 1890s</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
:root{--surface-1:#fcfcfb;--text-primary:#0b0b0b;--text-secondary:#52514e;--text-muted:#77766f;--grid:#e4e3df;
 --b1:#86b6ef;--b2:#3987e5;--b3:#256abf;--b4:#184f95;--b5:#0d366b;--unread:#eb6834;--read:#8a8986;--critical:#d03b3b}
*{box-sizing:border-box}
body{margin:0;font:14px/1.4 system-ui,-apple-system,"Segoe UI",sans-serif;color:var(--text-primary);background:var(--surface-1)}
header{padding:12px 16px 4px}
h1{font-size:18px;margin:0 0 2px}
.sub{color:var(--text-secondary);margin:0}
.filters{display:flex;flex-wrap:wrap;gap:6px 18px;align-items:center;padding:8px 16px;border-bottom:1px solid var(--grid)}
.filters fieldset{border:0;margin:0;padding:0;display:flex;flex-wrap:wrap;gap:4px 10px;align-items:center}
.filters legend{float:left;font-weight:600;margin-right:6px;color:var(--text-secondary)}
.filters label{white-space:nowrap;cursor:pointer}
.filters button{font:inherit;padding:2px 8px;border:1px solid var(--grid);background:#fff;border-radius:4px;cursor:pointer}
#wrap{display:flex;height:calc(100vh - 150px);min-height:480px}
#map{flex:1}
aside{width:270px;padding:10px 14px;overflow:auto;border-left:1px solid var(--grid)}
aside h2{font-size:13px;margin:12px 0 6px;color:var(--text-secondary);text-transform:uppercase;letter-spacing:.04em}
.row{display:flex;align-items:center;gap:8px;margin:3px 0}
.sw{width:14px;height:14px;border-radius:50%;border:2px solid var(--surface-1);box-shadow:0 0 0 1px #c9c8c3;flex:none}
svg.k{flex:none}
table{border-collapse:collapse;width:100%;font-size:12.5px}
td,th{padding:2px 4px;text-align:right;border-bottom:1px solid var(--grid)}
td:first-child,th:first-child{text-align:left}
#count{font-weight:600}
.leaflet-tooltip{font:12.5px/1.4 system-ui,sans-serif;width:280px;white-space:normal}
.tt-v{font-size:15px;font-weight:700}
.tt-m{color:var(--text-secondary)}
</style></head><body>
<header><h1>OS height marks read from the 1890s maps, West Ham</h1>
<p class="sub">__NPTS__ marks in feet above Ordnance Datum (Liverpool). Hover a mark for its reading. Five-foot sheets inside the study box: __NREAD__ read, __NUNREAD__ not yet read.</p></header>
<div class="filters">
 <fieldset id="f-set"><legend>Setting</legend></fieldset>
 <fieldset><legend>Type</legend>
  <label><input type="checkbox" class="f-type" value="spot" checked> spot height</label>
  <label><input type="checkbox" class="f-type" value="B.M." checked> bench mark</label></fieldset>
 <fieldset><legend>Map</legend>
  <label><input type="checkbox" class="f-lay" value="five-foot" checked> five-foot</label>
  <label><input type="checkbox" class="f-lay" value="25-inch" checked> 25-inch</label></fieldset>
 <fieldset><legend>Show</legend>
  <label><input type="checkbox" id="f-disp"> disputed only</label>
  <label><input type="checkbox" id="f-cov" checked> sheet coverage</label></fieldset>
 <button id="b-ground" type="button" title="Hide wall tops, bridges and buildings">ground only</button>
 <button id="b-all" type="button">all settings</button>
 <span>Showing <span id="count"></span></span>
</div>
<div id="wrap"><div id="map" role="img" aria-label="Map of OS height marks in West Ham"></div>
<aside>
 <h2>Height, feet</h2><div id="lg-h"></div>
 <h2>Type</h2>
 <div class="row"><svg class="k" width="16" height="16"><circle cx="8" cy="8" r="5" fill="#3987e5" stroke="#fcfcfb" stroke-width="2"/></svg> spot height</div>
 <div class="row"><svg class="k" width="16" height="16"><path d="M8 2 L14 13 L2 13 Z" fill="#3987e5" stroke="#fcfcfb" stroke-width="1.5"/></svg> bench mark</div>
 <div class="row"><svg class="k" width="16" height="16"><circle cx="8" cy="8" r="5" fill="#3987e5" stroke="#d03b3b" stroke-width="2.5"/></svg> disputed (readers disagree)</div>
 <h2>Five-foot sheets</h2>
 <div class="row"><svg class="k" width="16" height="16"><rect x="2" y="2" width="12" height="12" fill="none" stroke="#8a8986" stroke-width="1"/></svg> read</div>
 <div class="row"><svg class="k" width="16" height="16"><rect x="2" y="2" width="12" height="12" fill="#eb6834" fill-opacity=".18" stroke="#eb6834" stroke-width="1.5" stroke-dasharray="3 2"/></svg> not yet read, inside study box</div>
 <div class="row"><svg class="k" width="16" height="16"><rect x="2" y="2" width="12" height="12" fill="none" stroke="#b5b4ae" stroke-width="1" stroke-dasharray="1 2"/></svg> outside study box (later buffer)</div>
 <div class="row"><svg class="k" width="16" height="16"><rect x="2" y="2" width="12" height="12" fill="none" stroke="#0b0b0b" stroke-width="1.5"/></svg> study box (a rectangle, not the parish boundary)</div>
 <h2>Shown, by setting</h2>
 <table id="tbl" aria-label="Counts of shown marks by setting"><thead><tr><th>setting</th><th>marks</th><th>median ft</th></tr></thead><tbody></tbody></table>
 <p class="tt-m" style="font-size:12px;margin-top:10px">Basemaps: NLS OS five-foot 1891–96 and 25-inch, CC-BY National Library of Scotland (local tiles); OpenStreetMap needs a connection. Outside the coverage grid no five-foot tiles were downloaded.</p>
</aside></div>
<script>
const P=__POINTS__, C=__CELLS__, BOX=__BOX__;
const BANDS=[[-1,8,'#86b6ef','under 8 (marsh)'],[8,15,'#3987e5','8–15'],[15,25,'#256abf','15–25 (made ground, quays)'],[25,40,'#184f95','25–40 (terrace)'],[40,1e9,'#0d366b','40 and over']];
const band=v=>BANDS.find(b=>v>=b[0]&&v<b[1]);
const SETTINGS=['marsh','open_ground','street','yard','embankment_top','embankment_foot','railway','wall_top','bridge','building','other','water','unknown'];
const GROUND=new Set(['marsh','open_ground','street','yard','embankment_top','embankment_foot','railway','other','unknown']);
const present=new Set(P.map(p=>p[4]));
const fs=document.getElementById('f-set');
SETTINGS.filter(s=>present.has(s)).forEach(s=>{const l=document.createElement('label');l.innerHTML=`<input type="checkbox" class="f-s" value="${s}" checked> ${s.replace('_',' ')}`;fs.appendChild(l)});
document.getElementById('lg-h').innerHTML=BANDS.map(b=>`<div class="row"><span class="sw" style="background:${b[2]}"></span>${b[3]}</div>`).join('');

const map=L.map('map',{preferCanvas:true,maxZoom:21});
map.fitBounds(L.latLngBounds(P.map(p=>[p[0],p[1]])).pad(.05));
const plain=L.layerGroup();
const ff=L.tileLayer('../nls-tiles/os-london-five-foot-1893/{z}/{x}/{y}.png',{minZoom:10,maxZoom:21,maxNativeZoom:18,opacity:.75,attribution:'NLS OS five-foot 1891–96 (CC-BY)'}).addTo(map);
const q25=L.tileLayer('../nls-tiles/os-25-inch-london/{z}/{x}/{y}.png',{minZoom:10,maxZoom:21,maxNativeZoom:18,opacity:.75,attribution:'NLS OS 25-inch (CC-BY)'});
const osm=L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:21,maxNativeZoom:19,attribution:'&copy; OpenStreetMap contributors'});
L.control.layers({'OS five-foot, 1891–96 (local)':ff,'OS 25-inch, 1890s (local)':q25,'OpenStreetMap (online)':osm,'No basemap':plain},{},{collapsed:false,position:'topright'}).addTo(map);
L.control.scale({imperial:true}).addTo(map);
const R=L.canvas({padding:.5,tolerance:4});
L.Canvas.include({_updateTri(layer){if(!this._drawing||layer._empty())return;const p=layer._point,c=this._ctx,r=Math.max(Math.round(layer._radius),1);c.beginPath();c.moveTo(p.x,p.y-r*1.25);c.lineTo(p.x+r*1.15,p.y+r*.85);c.lineTo(p.x-r*1.15,p.y+r*.85);c.closePath();this._fillStroke(c,layer)}});
const Tri=L.CircleMarker.extend({_updatePath(){this._renderer._updateTri(this)}});

const STY={read:{renderer:R,color:'#8a8986',weight:.6,fill:false,interactive:false},
 unread:{renderer:R,color:'#eb6834',weight:1.6,dashArray:'4 3',fillColor:'#eb6834',fillOpacity:.18,interactive:true},
 outside:{renderer:R,color:'#b5b4ae',weight:.6,dashArray:'1 3',fill:false,interactive:false}};
const cov=L.layerGroup(C.map(c=>{const r=L.rectangle([[c[0],c[1]],[c[2],c[3]]],STY[c[4]]);if(c[4]==='unread')r.bindTooltip(`${c[5]}: not yet read`,{sticky:true});return r}));
cov.addLayer(L.rectangle([[BOX[0],BOX[1]],[BOX[2],BOX[3]]],{renderer:R,color:'#0b0b0b',weight:1.5,fill:false,interactive:false}));

const esc=s=>String(s).replace(/[&<>"]/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[ch]));
const marks=P.map(p=>{const b=band(p[2]),o={renderer:R,radius:p[3]==='B.M.'?5.5:5,fillColor:b[2],fillOpacity:1,color:p[7]?'#d03b3b':'#fcfcfb',weight:p[7]?2.5:1.5};
 const m=p[3]==='B.M.'?new Tri([p[0],p[1]],o):L.circleMarker([p[0],p[1]],o);
 m.bindTooltip(`<div class="tt-v">${p[2]} ft</div><div>${p[3]==='B.M.'?'Bench mark':'Spot height'} · ${esc(p[4].replace('_',' '))} · ${p[6]} map</div><div class="tt-m">confidence ${p[5]}; ${p[8]} reading${p[8]>1?'s':''} by ${p[9]} reader${p[9]>1?'s':''}${p[7]?'; <b>disputed</b>':''}</div><div class="tt-m">BNG ${p[12]}, ${p[13]}</div>${p[10]?`<div class="tt-m">${esc(p[10])}</div>`:''}`,{direction:'top',offset:[0,-6]});
 m._p=p;return m});
const shown=L.layerGroup().addTo(map);
function apply(){const S=new Set([...document.querySelectorAll('.f-s:checked')].map(i=>i.value)),T=new Set([...document.querySelectorAll('.f-type:checked')].map(i=>i.value)),Y=new Set([...document.querySelectorAll('.f-lay:checked')].map(i=>i.value)),D=document.getElementById('f-disp').checked;
 shown.clearLayers();const by={};let n=0;
 for(const m of marks){const p=m._p;if(S.has(p[4])&&T.has(p[3])&&Y.has(p[6])&&(!D||p[7])){shown.addLayer(m);n++;(by[p[4]]=by[p[4]]||[]).push(p[2])}}
 document.getElementById('count').textContent=n.toLocaleString()+' marks';
 const med=a=>{a=a.slice().sort((x,y)=>x-y);const k=a.length>>1;return a.length%2?a[k]:(a[k-1]+a[k])/2};
 document.querySelector('#tbl tbody').innerHTML=SETTINGS.filter(s=>by[s]).map(s=>`<tr><td>${s.replace('_',' ')}</td><td>${by[s].length}</td><td>${med(by[s]).toFixed(1)}</td></tr>`).join('');
 if(document.getElementById('f-cov').checked)cov.addTo(map);else cov.remove();}
document.querySelectorAll('.filters input').forEach(i=>i.addEventListener('change',apply));
document.getElementById('b-ground').onclick=()=>{document.querySelectorAll('.f-s').forEach(i=>i.checked=GROUND.has(i.value));apply()};
document.getElementById('b-all').onclick=()=>{document.querySelectorAll('.f-s').forEach(i=>i.checked=true);apply()};
apply();
const rad=()=>{const z=map.getZoom();return z<=13?2.6:z===14?3.4:z===15?4.2:5};
function resize(){const r=rad();for(const m of marks){m.setRadius(m._p[3]==='B.M.'?r*1.1:r);m.setStyle({weight:r<4?1:(m._p[7]?2.5:1.5)})}}
map.on('zoomend',resize);resize();
const readCells=cov.getLayers().filter(r=>r.options.color==='#8a8986');
map.on('zoomend',()=>{const hide=map.getZoom()>=16;readCells.forEach(r=>r.setStyle({opacity:hide?0:1}))});
</script></body></html>
"""

if __name__ == "__main__":
    main()
