import { makeBed, parameters } from './flood-solver.js';
const $ = (id) => document.getElementById(id);
const terrain = await fetch('./data/flood-demo-1900.json')
  .then((r) => {
    if (!r.ok) throw Error('Could not load flood surface');
    return r.json();
  })
  .catch((e) => {
    $('status').textContent = e.message;
    throw e;
  });
let runs = [],
  selected = 0,
  follow = true,
  playing = false,
  timer = null,
  generation = 0,
  dirty = false;
const duration = terrain.durationSeconds,
  interval = terrain.frameIntervalSeconds;
const gateName = { 'east-to-west': 'Drain east to west', both: 'Open in both directions', blocked: 'Blocked drain' };
function input() {
  return parameters(terrain, {
    preset: $('preset').value,
    peak: Number($('peak').value),
    gate: $('gate').value,
    rain: Number($('rain').value),
    pump: $('pump').value === 'on',
    railFormation: Number($('rail').value),
    verticalShift: Number($('shift').value),
  });
}
function stop() {
  generation++;
  for (const r of runs) r.worker?.terminate();
  $('cancel').hidden = true;
  pause();
  if (window.floodDemoReview) window.floodDemoReview.status = 'stopped';
}
function pause() {
  playing = false;
  clearInterval(timer);
  $('play').textContent = 'Play';
}
function count() {
  return runs.length ? Math.min(...runs.map((r) => r.frames.length)) : 0;
}
function card(r) {
  const article = document.createElement('article');
  article.className = 'map-card';
  article.innerHTML =
    '<div class="map-head"><h2></h2><p></p></div><canvas width="1080" height="400" role="img"></canvas><div class="metrics"><div class="metric"><strong data-value="area">0</strong><span>hectares flooded</span></div><div class="metric"><strong data-value="depth">0</strong><span>deepest water, metres</span></div><div class="metric"><strong data-value="flow">0</strong><span>culvert flow, m³/s → west</span></div></div>';
  article.querySelector('h2').textContent = gateName[r.params.gate];
  article.querySelector('p').textContent =
    `${r.params.preset === 'rain' ? 'Rain test' : `Peak ${r.params.peak.toFixed(2)} m ODN at ${r.params.preset === 'surge' ? 'west' : 'east'}`} · ${r.params.rain} mm/h rain · railway ${(r.params.railFormation + r.params.verticalShift).toFixed(1)} m · pump ${r.params.pump ? 'on' : 'off'}`;
  r.canvas = article.querySelector('canvas');
  r.card = article;
  r.canvas.setAttribute('aria-label', `Flood depth map: ${gateName[r.params.gate]}`);
  r.canvas.addEventListener('pointermove', (e) => inspect(r, e));
  $('maps').append(article);
}
function inspect(r, e) {
  const rect = r.canvas.getBoundingClientRect(),
    x = ((e.clientX - rect.left) / rect.width) * 1080,
    z = ((e.clientY - rect.top) / rect.height) * 400;
  const ix = Math.floor(((x - 30) / 1020) * terrain.width),
    iz = Math.floor(((z - 42) / 302) * terrain.height);
  if (ix < 0 || ix >= terrain.width || iz < 0 || iz >= terrain.height) return;
  const i = iz * terrain.width + ix,
    f = r.frames[selected];
  if (!f) return;
  $('inspect').textContent =
    `${gateName[r.params.gate]} · ground ${r.bed[i].toFixed(2)} m ODN · water ${f.depth[i].toFixed(2)} m deep · ${terrain.kindLegend[terrain.kind[i]]}.`;
}
function renderMap(r, f) {
  const ctx = r.canvas.getContext('2d'),
    off = document.createElement('canvas');
  off.width = terrain.width;
  off.height = terrain.height;
  const g = off.getContext('2d'),
    pixels = g.createImageData(off.width, off.height);
  for (let i = 0; i < f.depth.length; i++) {
    const h = f.depth[i],
      y = r.bed[i],
      t = Math.max(0, Math.min(1, (y - 0.4) / 1.8));
    let c = [Math.round(163 + 42 * t), Math.round(173 + 20 * t), Math.round(136 + 14 * t)];
    if (terrain.kind[i] === 3) c = [195, 183, 157];
    if (terrain.kind[i] === 2) c = [157, 150, 130];
    if (terrain.kind[i] === 4) c = [118, 143, 128];
    if (h > 0.005) {
      const a = Math.min(0.94, 0.3 + h * 2),
        v = Math.min(1, h);
      const water = [Math.round(128 - 109 * v), Math.round(198 - 142 * v), Math.round(217 - 129 * v)];
      c = c.map((v, k) => Math.round(v * (1 - a) + water[k] * a));
    }
    if (
      $('evidence').checked &&
      terrain.kind[i] !== 1 &&
      ((i % terrain.width) + Math.floor(i / terrain.width)) % 6 === 0
    )
      c = [130, 96, 60];
    pixels.data.set([...c, 255], i * 4);
  }
  g.putImageData(pixels, 0, 0);
  ctx.fillStyle = '#fffcf4';
  ctx.fillRect(0, 0, 1080, 400);
  ctx.imageSmoothingEnabled = false;
  ctx.drawImage(off, 30, 42, 1020, 302);
  const xy = (p) => [
    30 + ((p[0] - terrain.bounds[0]) / (terrain.bounds[2] - terrain.bounds[0])) * 1020,
    42 + ((p[1] - terrain.bounds[1]) / (terrain.bounds[3] - terrain.bounds[1])) * 302,
  ];
  function line(route, color, dash, width = 2) {
    ctx.save();
    ctx.beginPath();
    ctx.rect(30, 42, 1020, 302);
    ctx.clip();
    ctx.beginPath();
    route.forEach((p, i) => {
      const q = xy(p);
      i ? ctx.lineTo(...q) : ctx.moveTo(...q);
    });
    ctx.strokeStyle = color;
    ctx.lineWidth = width;
    ctx.setLineDash(dash);
    ctx.stroke();
    ctx.restore();
  }
  for (const rail of terrain.routes.rail) line(rail, '#514c3c', [7, 4], 1.4);
  line(terrain.routes.road, '#8d7657', [], 1.4);
  line(
    terrain.culvert.route,
    r.params.gate === 'blocked' ? '#a85535' : '#173f3b',
    r.params.gate === 'blocked' ? [3, 4] : [],
    3
  );
  ctx.fillStyle = '#365346';
  ctx.font = '16px system-ui';
  ctx.fillText('N ↑', 32, 29);
  ctx.fillText('Railways', 420, 29);
  ctx.fillText('Manor Road', 560, 29);
  ctx.font = '14px system-ui';
  ctx.fillText('Western test outlet', 32, 376);
  ctx.textAlign = 'right';
  ctx.fillText('Eastern test boundary', 1048, 376);
  ctx.textAlign = 'left';
  ctx.strokeStyle = '#3c5245';
  ctx.lineWidth = 2;
  ctx.setLineDash([]);
  ctx.beginPath();
  ctx.moveTo(480, 360);
  ctx.lineTo(574, 360);
  ctx.stroke();
  ctx.fillText('50 m', 510, 385);
  r.card.querySelector('[data-value=area]').textContent = (f.stats.wetAreaM2 / 10000).toFixed(2);
  r.card.querySelector('[data-value=depth]').textContent = f.stats.maxDepth.toFixed(2);
  r.card.querySelector('[data-value=flow]').textContent = f.stats.culvertFlow.toFixed(3);
}
function render() {
  const available = count();
  if (!available) return;
  selected = Math.min(selected, available - 1);
  $('time').max = available - 1;
  $('time').value = selected;
  $('time').disabled = false;
  $('play').disabled = available < 2;
  $('download').disabled = false;
  const f = runs[0].frames[selected];
  $('clock').textContent = `${Math.round(f.stats.time / 60)} min`;
  runs.forEach((r) => renderMap(r, r.frames[selected]));
  $('balance').textContent = runs
    .map((r) => {
      const s = r.frames[selected].stats;
      return `${gateName[r.params.gate]}: stored ${s.volume.toFixed(1)} m³; initial ${s.initialVolume.toFixed(1)}, boundary in ${s.boundaryIn.toFixed(1)}, boundary out ${s.boundaryOut.toFixed(1)}, rainfall ${s.rainVolume.toFixed(1)}, pumping ${s.pumpVolume.toFixed(1)} m³. Balance error ${s.massError.toExponential(2)} m³.`;
    })
    .join(' ');
  window.floodDemoReview = {
    status: runs.every((r) => r.done) ? 'complete' : 'running',
    selectedTime: f.stats.time,
    frames: available,
    runs: runs.map((r) => ({ params: r.params, stats: r.frames[selected].stats })),
    epoch: terrain.epoch,
  };
}
function start(compare = false) {
  let p;
  try {
    p = input();
  } catch (e) {
    $('status').textContent = e.message;
    return;
  }
  stop();
  const id = generation;
  selected = 0;
  follow = true;
  dirty = false;
  runs = [];
  $('maps').replaceChildren();
  $('maps').classList.toggle('comparison', compare);
  window.floodDemoReview = { status: 'running', frames: 0, runs: [], epoch: terrain.epoch };
  $('status').textContent = 'Calculating water movement…';
  $('cancel').hidden = false;
  const settings = [p];
  if (compare) settings.push({ ...p, gate: p.gate === 'blocked' ? 'east-to-west' : 'blocked' });
  for (const params of settings) {
    const r = { params, frames: [], bed: makeBed(terrain, params), done: false };
    runs.push(r);
    card(r);
    const worker = (r.worker = new Worker('./flood-worker.js', { type: 'module' }));
    worker.onmessage = ({ data }) => {
      if (id !== generation) return;
      if (data.type === 'ready') r.bed = data.bed;
      if (data.type === 'error') {
        $('status').textContent = `Calculation stopped: ${data.message}`;
        stop();
        return;
      }
      if (data.type === 'frame') {
        r.frames.push(data);
        if (follow) selected = Math.max(0, count() - 1);
        render();
        $('status').textContent =
          `Calculating: ${Math.round(((Math.max(0, count() - 1) * interval) / duration) * 100)}% of one modelled hour.${dirty ? ' Settings changed; rerun to apply them.' : ''}`;
      }
      if (data.type === 'done') {
        r.done = true;
        worker.terminate();
        if (runs.every((r) => r.done)) {
          $('status').textContent = dirty
            ? 'Previous experiment complete. Settings changed; rerun to apply them.'
            : 'Experiment complete. Play the sequence or move the time slider.';
          $('cancel').hidden = true;
          render();
        }
      }
    };
    worker.onerror = (e) => {
      $('status').textContent = `Calculation stopped: ${e.message}`;
      stop();
    };
    worker.postMessage({ terrain, params, duration, interval });
  }
}
$('run').addEventListener('click', () => start());
$('compare').addEventListener('click', () => start(true));
$('cancel').addEventListener('click', () => {
  stop();
  $('status').textContent = 'Calculation stopped. Existing frames remain available.';
});
$('time').addEventListener('input', () => {
  follow = false;
  pause();
  selected = Number($('time').value);
  render();
});
$('evidence').addEventListener('change', render);
$('play').addEventListener('click', () => {
  if (playing) {
    pause();
    return;
  }
  follow = false;
  playing = true;
  if (selected >= count() - 1) selected = 0;
  $('play').textContent = 'Pause';
  render();
  timer = setInterval(() => {
    if (selected >= count() - 1) {
      pause();
      return;
    }
    selected++;
    render();
  }, 350);
});
$('preset').addEventListener('change', () => {
  $('rain').value = $('preset').value === 'rain' ? 30 : 0;
  $('peak').disabled = $('preset').value === 'rain';
  $('peak').value = $('preset').value === 'surge' ? '1.65' : '1.65';
});
for (const id of ['preset', 'peak', 'gate', 'rain', 'pump', 'rail', 'shift'])
  $(id).addEventListener('change', () => {
    dirty = true;
    $('status').textContent =
      'Settings changed. Run an experiment to apply them; displayed results retain their previous settings.';
  });
$('download').addEventListener('click', () => {
  const result = {
    title: 'Controlled 1900 flood experiment',
    epoch: terrain.epoch,
    cellSizeMetres: terrain.cellSizeMetres,
    bounds: terrain.bounds,
    width: terrain.width,
    height: terrain.height,
    selectedTime: runs[0].frames[selected].stats.time,
    limitations: terrain.limitations,
    inputHashes: terrain.inputHashes,
    runs: runs.map((r) => ({
      parameters: r.params,
      stats: r.frames[selected].stats,
      depthMetres: Array.from(r.frames[selected].depth),
      bedODNMetres: Array.from(r.bed),
    })),
  };
  const url = URL.createObjectURL(new Blob([JSON.stringify(result)], { type: 'application/json' }));
  const a = document.createElement('a');
  a.href = url;
  a.download = 'plaistow-flood-demo.json';
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
$('support').textContent =
  `${(terrain.supportedFieldFraction * 100).toFixed(1)}% of grid locations had fully supported field interpolation before the explicit road, railway and drainage sections were applied. The remaining ground gaps use nearby period observations, separately by compartment. Switch on “Show assumed ground” to see surfaces requiring additional assumptions.`;
start();
