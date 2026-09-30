// Historic maps page: dated NLS tile layers stacked on one map, with the book's GIS on top.
/* global L */
const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];
const cfg = await (await fetch('./layers.json')).json();
const tileBase = cfg.tileBase[cfg.source];
const editions = [...cfg.layers].sort((a, b) => a.year - b.year);
const byId = Object.fromEntries(editions.map((e) => [e.id, e]));

/* ---------- Map ---------- */
const map = L.map('map', { zoomControl: false, minZoom: 9, maxZoom: 20, attributionControl: false, zoomSnap: 0.5 });
map.createPane('base'); map.getPane('base').style.zIndex = 150;
map.createPane('stack'); map.getPane('stack').style.zIndex = 200;
map.createPane('cmpLeft'); map.getPane('cmpLeft').style.zIndex = 210; map.getPane('cmpLeft').classList.add('compare-pane');
map.createPane('cmpRight'); map.getPane('cmpRight').style.zIndex = 211; map.getPane('cmpRight').classList.add('compare-pane');
map.createPane('water'); map.getPane('water').style.zIndex = 400;
map.createPane('sites'); map.getPane('sites').style.zIndex = 410;
map.createPane('lines'); map.getPane('lines').style.zIndex = 420;
map.createPane('bounds'); map.getPane('bounds').style.zIndex = 430;
L.control.zoom({ position: 'bottomright' }).addTo(map);
if (!window.matchMedia('(max-width: 820px)').matches) L.control.scale({ position: 'bottomright', imperial: true, maxWidth: 160 }).addTo(map);
L.control.attribution({ position: 'bottomright', prefix: false }).addAttribution(cfg.credit).addTo(map);

function tileLayer(path, edition, pane) {
  // `path` is relative to the NLS tile base unless the edition carries its own `url` template
  // (used for layers hosted with the site, such as the georeferenced 1805 sheet).
  const url = edition.url || `${tileBase}/${path}/{z}/{x}/{y}.png`;
  const options = {
    pane, minZoom: 6, maxZoom: 20, maxNativeZoom: edition.maxNative, minNativeZoom: edition.minZoom,
    className: `edition edition-${edition.id}`, crossOrigin: false, updateWhenIdle: true, keepBuffer: 2
  };
  if (edition.bounds) options.bounds = L.latLngBounds([edition.bounds[1], edition.bounds[0]], [edition.bounds[3], edition.bounds[2]]);
  return L.tileLayer(url, options);
}
// One entry per edition: a group of tile layers (county series) or a single one, addressed uniformly.
function makeEdition(edition, pane) {
  const paths = edition.paths || [edition.path || edition.id];
  const layers = paths.map((p) => tileLayer(p, edition, pane));
  const group = L.layerGroup(layers);
  group.setOpacity = (o) => layers.forEach((l) => l.setOpacity(o));
  group.tileLayers = layers;
  return group;
}
const stackLayers = Object.fromEntries(editions.map((e) => [e.id, makeEdition(e, 'stack')]));
const state = { mode: 'stack', on: new Set(), opacity: {}, active: null, cmpLeft: null, cmpRight: null };
for (const e of editions) state.opacity[e.id] = 1;

/* ---------- Edition list ---------- */
const list = $('#layer-list');
for (const e of editions) {
  const li = document.createElement('li'); li.className = 'layer'; li.dataset.id = e.id;
  li.innerHTML = `<input type="checkbox" id="on-${e.id}" aria-label="Show ${e.title}, ${e.label}">
    <label class="head" for="on-${e.id}"><span class="year">${e.label}</span><span class="title">${e.title}</span></label>
    <div class="controls"><input type="range" min="0" max="100" value="100" aria-label="Opacity of ${e.title}"><span class="pct">100%</span></div>
    <p class="info">${e.note || ''}</p>`;
  list.append(li);
  li.querySelector('input[type=checkbox]').addEventListener('change', (ev) => setOn(e.id, ev.target.checked, true));
  li.querySelector('input[type=range]').addEventListener('input', (ev) => setOpacity(e.id, ev.target.value / 100));
}
function setOn(id, on, fromUser) {
  const layer = stackLayers[id], li = list.querySelector(`[data-id="${id}"]`);
  li.querySelector('input[type=checkbox]').checked = on;
  li.classList.toggle('is-on', on);
  if (on) { state.on.add(id); if (state.mode === 'stack' && !map.hasLayer(layer)) layer.addTo(map); layer.setOpacity(state.opacity[id]); }
  else { state.on.delete(id); if (map.hasLayer(layer)) map.removeLayer(layer); }
  if (on || fromUser) setActive(on ? id : [...state.on].at(-1) || null);
  syncOrder(); writeHash();
}
function setOpacity(id, o) {
  state.opacity[id] = o; stackLayers[id].setOpacity(o);
  const li = list.querySelector(`[data-id="${id}"]`);
  li.querySelector('input[type=range]').value = Math.round(o * 100); li.querySelector('.pct').textContent = `${Math.round(o * 100)}%`;
}
function syncOrder() {
  // Later editions draw above earlier ones so the stack reads as time.
  for (const e of editions) if (map.hasLayer(stackLayers[e.id])) stackLayers[e.id].tileLayers.forEach((l) => l.bringToFront());
}
function setActive(id) {
  state.active = id;
  $$('.layer').forEach((li) => li.classList.toggle('is-active', li.dataset.id === id));
  if (id) { const i = editions.findIndex((e) => e.id === id); time.value = i; }
  paintTimeline();
}

/* ---------- Timeline ---------- */
const time = $('#time'), ticks = $('#ticks'), timeLabel = $('#time-label');
time.max = editions.length - 1;
ticks.innerHTML = editions.map((e) => `<span>${e.year}</span>`).join('');
function paintTimeline() {
  const i = Number(time.value), e = editions[i];
  $$('#ticks span').forEach((s, k) => s.classList.toggle('is-active', k === i));
  timeLabel.innerHTML = `<b>${e.label}</b>${e.title}`;
}
time.addEventListener('input', () => {
  const e = editions[Number(time.value)];
  if (state.mode === 'stack') {
    // Scrubbing shows one edition at a time; stacking is done with the checkboxes.
    for (const other of editions) if (other.id !== e.id && state.on.has(other.id)) setOn(other.id, false, false);
    setOn(e.id, true, false);
  } else {
    setCompare('right', e.id);
  }
  paintTimeline();
});

/* ---------- Compare mode ---------- */
const panel = $('#panel');
const cmpLayers = { left: null, right: null };
const divider = document.createElement('div'); divider.className = 'divider'; divider.hidden = true;
divider.innerHTML = '<span class="divider-label left"></span><span class="divider-label right"></span>';
map.getContainer().append(divider);
let split = 0.5;
const selLeft = $('#cmp-left'), selRight = $('#cmp-right');
for (const sel of [selLeft, selRight]) sel.innerHTML = editions.map((e) => `<option value="${e.id}">${e.label} · ${e.title}</option>`).join('');
selLeft.addEventListener('change', () => setCompare('left', selLeft.value));
selRight.addEventListener('change', () => setCompare('right', selRight.value));
function setCompare(side, id) {
  const pane = side === 'left' ? 'cmpLeft' : 'cmpRight';
  if (cmpLayers[side]) map.removeLayer(cmpLayers[side]);
  cmpLayers[side] = makeEdition(byId[id], pane).addTo(map);
  state[side === 'left' ? 'cmpLeft' : 'cmpRight'] = id;
  (side === 'left' ? selLeft : selRight).value = id;
  divider.querySelector(`.divider-label.${side}`).textContent = byId[id].label;
  if (side === 'right') { time.value = editions.findIndex((e) => e.id === id); paintTimeline(); }
  applyClip(); writeHash();
}
function applyClip() {
  if (state.mode !== 'compare') return;
  const rect = map.getContainer().getBoundingClientRect();
  // Keep the handle clear of the side panel on wide screens.
  const panelRect = panel.getBoundingClientRect();
  const minX = window.matchMedia('(max-width: 820px)').matches ? 24 : Math.max(24, panelRect.right - rect.left + 28);
  const x = Math.max(minX, Math.min(rect.width - 24, Math.round(rect.width * split)));
  divider.style.left = `${x}px`;
  // Tile containers are zero-size boxes at the layer origin, so express the clip in layer
  // points: inset(top right bottom left) with negative values extends past the box.
  const nw = map.containerPointToLayerPoint([0, 0]), se = map.containerPointToLayerPoint(map.getSize());
  const cx = map.containerPointToLayerPoint([x, 0]).x;
  for (const [side, layer] of Object.entries(cmpLayers)) {
    if (!layer) continue;
    for (const tl of layer.tileLayers) {
      const c = tl.getContainer(); if (!c) continue;
      c.style.clipPath = side === 'left'
        ? `inset(${nw.y}px ${-cx}px ${-se.y}px ${nw.x}px)`
        : `inset(${nw.y}px ${-se.x}px ${-se.y}px ${cx}px)`;
    }
  }
}
map.on('move zoom moveend zoomend viewreset resize load layeradd', applyClip);
let dragging = false;
divider.addEventListener('pointerdown', (e) => { dragging = true; divider.setPointerCapture(e.pointerId); map.dragging.disable(); e.preventDefault(); });
divider.addEventListener('pointermove', (e) => {
  if (!dragging) return;
  const rect = map.getContainer().getBoundingClientRect();
  split = Math.min(0.98, Math.max(0.02, (e.clientX - rect.left) / rect.width)); applyClip();
});
for (const ev of ['pointerup', 'pointercancel', 'lostpointercapture']) divider.addEventListener(ev, () => { dragging = false; map.dragging.enable(); });
divider.addEventListener('keydown', (e) => { if (e.key === 'ArrowLeft') split = Math.max(0.02, split - 0.02); else if (e.key === 'ArrowRight') split = Math.min(0.98, split + 0.02); else return; e.preventDefault(); applyClip(); });
divider.tabIndex = 0; divider.setAttribute('role', 'slider'); divider.setAttribute('aria-label', 'Comparison divider');

function setMode(mode) {
  state.mode = mode;
  $$('[data-mode]').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.mode === mode)));
  $('#compare-block').hidden = mode !== 'compare';
  $('#layer-list').closest('.block').hidden = mode === 'compare';
  divider.hidden = mode !== 'compare';
  if (mode === 'compare') {
    for (const id of state.on) map.removeLayer(stackLayers[id]);
    const right = state.cmpRight || state.active || editions.find((e) => e.default).id;
    let left = state.cmpLeft || (byId[right].year > 1880 ? 'five-foot-1860s' : 'five-foot-1893');
    if (left === right) left = editions.find((e) => e.id !== right && e.year !== byId[right].year).id;
    setCompare('left', left); setCompare('right', right);
  } else {
    for (const side of ['left', 'right']) if (cmpLayers[side]) { map.removeLayer(cmpLayers[side]); cmpLayers[side] = null; }
    for (const id of state.on) stackLayers[id].addTo(map);
    syncOrder(); setActive(state.active);
  }
  writeHash();
}
$$('[data-mode]').forEach((b) => b.addEventListener('click', () => setMode(b.dataset.mode)));

/* ---------- Vector overlays ---------- */
const TYPE_COLORS = { 'Brewing': '#b15928', 'Distillery': '#d19144', 'Chemical': '#6a3d9a', 'Varnish Colour and Paint': '#9b6fb0', 'Tar': '#3d2a5a', 'Asphalt': '#555555', 'Oil and Petroleum': '#b2df8a', 'Soap Candle Tallow and Oil': '#33a02c', 'Coal Gas': '#d4b100', 'Electrical': '#f768a1', 'Metal': '#e31a1c', 'Engineering': '#fb9a99', 'Arms and Munitions': '#ff3d00', 'Shipyard': '#67001f', 'Timber Mill': '#8c510a', 'Timber Yard': '#bf812d', 'Cooperage': '#dfc27d', 'Grain Mill': '#ffdd66', 'Granary': '#e6c200', 'Food': '#ff7f00', 'Tobacco': '#9e0142', 'Leather and Skins': '#7f4a1f', 'Cloth and Clothing': '#fdbf6f', 'Fiber': '#f4a582', 'Rope': '#c49a6c', 'Rubber and Gutta-Percha': '#cc4c02', 'Paper': '#cab2d6', 'Printing': '#6b6b6b', 'Glass': '#f1b6da', 'Furnishings': '#bc8f8f', 'Building': '#a0522d', 'General': '#999999' };
const colorFor = (t) => TYPE_COLORS[t] || '#777';
const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const PANES = { industry: 'sites', water: 'water', dock: 'water', rail: 'lines', boundary: 'bounds', lcc: 'bounds' };
const styles = {
  industry: (f) => ({ pane: 'sites', color: '#1b1b1b', weight: .7, fillColor: colorFor(f.properties.Type), fillOpacity: .78 }),
  water: () => ({ pane: 'water', color: '#3a7f9c', weight: .6, fillColor: '#7fb6cc', fillOpacity: .55 }),
  dock: () => ({ pane: 'water', color: '#123b6b', weight: .9, fillColor: '#2c6aa8', fillOpacity: .7 }),
  rail: () => ({ pane: 'lines', color: '#1c1c1c', weight: 2.2, dashArray: '7 4', opacity: .9 }),
  boundary: () => ({ pane: 'bounds', color: '#d6a54d', weight: 2.4, fill: false, dashArray: '2 6', lineCap: 'round' }),
  lcc: () => ({ pane: 'bounds', color: '#b22222', weight: 1.6, fill: false })
};
const popups = {
  industry: (p) => `<b>${esc(p.Type || 'Industry')}</b><h3>${esc(p.Map_Name || p.Full_name || p.Short_name || 'Unnamed site')}</h3>${p.Products ? `<div>${esc(p.Products)}</div>` : ''}${p.First_Date || p.Last_Date ? `<div class="small">On the maps ${esc(p.First_Date || '?')}–${esc(p.Last_Date || '?')}</div>` : ''}${p.Web_Link ? `<a href="${esc(p.Web_Link)}" target="_blank" rel="noopener">More about this site</a>` : ''}`,
  dock: (p) => `<b>Dock</b><h3>${esc(p.Name || 'Dock')}</h3>${p.Year_Built ? `<div>Built ${esc(p.Year_Built)}${p.Year_End ? `, closed ${esc(p.Year_End)}` : ''}</div>` : ''}`,
  water: (p) => `<b>${esc(p.Type || 'Water')}</b><h3>${esc(p.Name || 'Watercourse')}</h3>`,
  rail: (p) => `<b>${esc(p.kind || 'Railway')}</b><h3>${esc(p.name || 'Railway')}</h3>`,
  boundary: () => `<b>Boundary</b><h3>County Borough of West Ham, 1911</h3>`,
  lcc: () => `<b>Boundary</b><h3>London County Council</h3>`
};
const vectorLayers = {};
const vlist = $('#vector-list');
for (const v of cfg.vectors) {
  const li = document.createElement('li');
  const sw = { industry: '#6a3d9a', water: '#7fb6cc', dock: '#2c6aa8', rail: '#1c1c1c', boundary: '#d6a54d', lcc: '#b22222' }[v.kind];
  li.innerHTML = `<label class="check"><input type="checkbox" data-vector="${v.id}"><span><span class="swatch" style="background:${sw}"></span>${esc(v.title)}</span></label>`;
  vlist.append(li);
  li.querySelector('input').addEventListener('change', (ev) => toggleVector(v.id, ev.target.checked));
}
async function toggleVector(id, on) {
  const v = cfg.vectors.find((x) => x.id === id);
  if (!vectorLayers[id]) {
    const data = await (await fetch(v.file)).json();
    vectorLayers[id] = L.geoJSON(data, {
      style: styles[v.kind], pane: PANES[v.kind], interactive: v.kind !== 'boundary' && v.kind !== 'lcc',
      onEachFeature: (f, l) => { if (popups[v.kind]) l.bindPopup(popups[v.kind](f.properties)); }
    });
    if (v.kind === 'industry') buildLegend(data);
  }
  if (on) vectorLayers[id].addTo(map); else map.removeLayer(vectorLayers[id]);
  $(`[data-vector="${id}"]`).checked = on;
  writeHash();
}
const legendTypes = new Set();
function buildLegend(data) {
  for (const f of data.features) if (f.properties.Type) legendTypes.add(f.properties.Type);
  $('#legend').innerHTML = Object.keys(TYPE_COLORS).filter((t) => legendTypes.has(t)).map((t) => `<span><span class="swatch" style="background:${colorFor(t)}"></span>${esc(t)}</span>`).join('');
}

/* ---------- Places ---------- */
const placesEl = $('#places');
cfg.places.forEach((p, i) => {
  const b = document.createElement('button'); b.type = 'button';
  b.innerHTML = `<span>${String(i + 1).padStart(2, '0')}</span>${esc(p.title)}`;
  b.addEventListener('click', () => goPlace(p));
  placesEl.append(b);
});
function goPlace(p) {
  map.flyTo(p.center, p.zoom, { duration: 1.2 });
  const html = `<b>Place</b><h3>${esc(p.title)}</h3><div>${esc(p.text)}</div>${p.link ? `<a class="place-link" href="${esc(p.link)}">${esc(p.linkText || 'Open')}</a>` : ''}`;
  map.once('moveend', () => L.popup({ maxWidth: 300 }).setLatLng(p.center).setContent(html).openOn(map));
  if (window.matchMedia('(max-width: 820px)').matches) collapsePanel(true);
}
// The panorama's standpoint, always marked.
const standpoint = L.circleMarker([51.5318, -0.0037], { pane: 'bounds', radius: 7, color: '#0f1716', weight: 2, fillColor: '#d6a54d', fillOpacity: 1 }).addTo(map);
standpoint.bindPopup(`<b>Panorama</b><h3>Above the Channelsea</h3><div>The Northern Outfall Sewer crossing, the standpoint of the 3D view.</div><a class="place-link" href="../">Stand on the crossing</a>`);

/* ---------- Modern reference ---------- */
const modern = L.tileLayer('https://services.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}', { pane: 'base', maxZoom: 20, maxNativeZoom: 16, attribution: 'Modern base: Tiles © Esri, HERE, Garmin, OpenStreetMap contributors' });
$('#modern').addEventListener('change', (e) => { if (e.target.checked) modern.addTo(map); else map.removeLayer(modern); writeHash(); });

/* ---------- Panel (mobile) ---------- */
const panelToggle = $('#panel-toggle');
function collapsePanel(collapsed) { panel.classList.toggle('is-collapsed', collapsed); panelToggle.setAttribute('aria-expanded', String(!collapsed)); }
panelToggle.addEventListener('click', () => collapsePanel(!panel.classList.contains('is-collapsed')));
if (window.matchMedia('(max-width: 820px)').matches) collapsePanel(true);

/* ---------- Shareable state in the hash ---------- */
function writeHash() {
  const c = map.getCenter();
  const parts = [map.getZoom().toFixed(1), c.lat.toFixed(5), c.lng.toFixed(5)];
  if (state.mode === 'compare') parts.push(`cmp:${state.cmpLeft}|${state.cmpRight}`);
  else parts.push(`on:${[...state.on].map((id) => state.opacity[id] < 1 ? `${id}@${Math.round(state.opacity[id] * 100)}` : id).join(',')}`);
  const vs = Object.keys(vectorLayers).filter((id) => map.hasLayer(vectorLayers[id]));
  if (vs.length) parts.push(`v:${vs.join(',')}`);
  if (map.hasLayer(modern)) parts.push('modern');
  history.replaceState(null, '', `#${parts.join('/')}`);
}
function readHash() {
  const h = location.hash.slice(1).split('/');
  const out = { on: [], vectors: null, cmp: null, modern: false, view: null };
  if (h.length >= 3 && !Number.isNaN(Number(h[0]))) out.view = { zoom: Number(h[0]), center: [Number(h[1]), Number(h[2])] };
  for (const p of h.slice(3)) {
    if (p.startsWith('on:')) out.on = p.slice(3).split(',').filter(Boolean).map((s) => { const [id, op] = s.split('@'); return { id, op: op ? Number(op) / 100 : 1 }; });
    else if (p.startsWith('cmp:')) { const [l, r] = p.slice(4).split('|'); out.cmp = { l, r }; }
    else if (p.startsWith('v:')) out.vectors = p.slice(2).split(',').filter(Boolean);
    else if (p === 'modern') out.modern = true;
  }
  return out;
}
map.on('moveend', writeHash);

/* ---------- Start ---------- */
const init = readHash();
if (init.view) map.setView(init.view.center, init.view.zoom); else map.setView(cfg.home.center, cfg.home.zoom);
const startOn = init.on.length ? init.on.filter((o) => byId[o.id]) : editions.filter((e) => e.default).map((e) => ({ id: e.id, op: 1 }));
for (const o of startOn) { setOpacity(o.id, o.op); setOn(o.id, true, false); }
const startVectors = init.vectors ?? cfg.vectors.filter((v) => v.default).map((v) => v.id);
for (const id of startVectors) if (cfg.vectors.some((v) => v.id === id)) toggleVector(id, true);
if (init.modern) { $('#modern').checked = true; modern.addTo(map); }
if (init.cmp && byId[init.cmp.l] && byId[init.cmp.r]) { state.cmpLeft = init.cmp.l; state.cmpRight = init.cmp.r; setMode('compare'); }
paintTimeline();
window.mapsReview = { map, state, editions: editions.map((e) => e.id) };
