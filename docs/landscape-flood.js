// Flooding over the whole modelled ground (FLOOD_MODEL_PLAN.md, Phases 1 and V).
// Two views of the grids from scripts/build_landscape_flood.py (2 m over the back rivers, Three Mills and the core,
// 10 m over the rest of the regional landscape):
// - volume (default): rain, the tide and the river arrive as volumes and fill the lowest ground first
//   (docs/lib/flood-volume.js routes them over the basin hierarchy);
// - connected extent: every cell a source reaches below a chosen level, at that level (the Phase 1 view).
// Levels arrive as uint16 centimetres; this module only evaluates them.
import { basinModel, routeFlood, wetQuads } from './lib/flood-volume.js';

const NONE_ODN = 100; // stand-in for "never wet" on the GPU (half floats stop at 65504)
const MIN_DEPTH = 0.015;

export function decodeLevels(meta, buffer) {
  const raw = new Uint16Array(buffer),
    out = new Float32Array(raw.length);
  for (let i = 0; i < raw.length; i++) out[i] = raw[i] === meta.encoding.none ? NONE_ODN : raw[i] / 100 - 10;
  return out;
}

// Land connected at a level: exact on the fine grid, from the builder's stage table outside it.
export function floodMetrics(data, level) {
  if (!Number.isFinite(level)) throw Error('A finite water level is required');
  const { fine, meta } = data,
    cellArea = meta.fine.step ** 2;
  let area = 0,
    volume = 0,
    maxDepth = 0,
    supportedArea = 0,
    cells = 0;
  for (let i = 0; i < fine.bed.length; i++) {
    const depth = level - fine.bed[i];
    if (level <= fine.connection[i] || depth <= 0.05) continue;
    const land = 1 - fine.water[i] / 255;
    area += land * cellArea;
    volume += land * cellArea * depth;
    if (land > 0.5) maxDepth = Math.max(maxDepth, depth);
    supportedArea += (fine.support[i] / 255) * cellArea;
    cells++;
  }
  const table = meta.stageTable,
    k = Math.max(0, Math.min(table.length - 2, Math.floor((level - table[0].stageODN) / 0.05))),
    t = Math.max(0, Math.min(1, (level - table[k].stageODN) / (table[k + 1].stageODN - table[k].stageODN))),
    lerp = (key) => table[k][key] * (1 - t) + table[k + 1][key] * t;
  const outsideM2 = lerp('outsideFineHa') * 1e4;
  return {
    levelODN: level,
    floodedLandM2: area + outsideM2,
    fineLandM2: area,
    outsideFineLandM2: outsideM2,
    geometricVolumeM3: volume + lerp('outsideFineVolumeM3'),
    maxLandDepth: maxDepth,
    supportedFieldAreaM2: supportedArea,
    wetCells: cells,
  };
}

// Land under water in the volume view: hollow cells (not outlets, not mapped water) below their basin's level. A
// regional 10 m cell counts when the mean ground of its 2 m cells in that basin is under water.
export function volumeMetrics(data, model, levels) {
  const count = (grid, area, water, skip) => {
    let wet = 0,
      deepest = 0;
    for (let i = 0; i < grid.basin.length; i++) {
      const id = grid.basin[i] - 1;
      if (id < 0 || id >= model.nLand || (water && water[i] >= 128) || skip?.(i)) continue;
      const depth = levels[id] - grid.bed[i];
      if (depth > MIN_DEPTH) {
        wet += area;
        deepest = Math.max(deepest, depth);
      }
    }
    return [wet, deepest];
  };
  const [fineM2, fineDepth] = count(data.fine, data.meta.fine.step ** 2, data.fine.water),
    { coarse, fine } = data.meta,
    [cx0, cz0] = coarse.bounds,
    [bx0, bz0, bx1, bz1] = fine.bounds,
    // Regional cells under the fine box are counted there, on the 2 m grid.
    underFine = (i) => {
      const x = cx0 + ((i % coarse.width) + 0.5) * coarse.step,
        z = cz0 + (Math.floor(i / coarse.width) + 0.5) * coarse.step;
      return x > bx0 && x < bx1 && z > bz0 && z < bz1;
    },
    [outsideM2] = count({ basin: data.coarse.basin, bed: data.coarse.basinBed }, coarse.step ** 2, null, underFine);
  return {
    floodedLandM2: fineM2 + outsideM2,
    fineLandM2: fineM2,
    outsideFineLandM2: outsideM2,
    maxLandDepth: fineDepth,
  };
}

export async function installLandscapeFlood({ THREE, scene, load, render, travel, setWater }) {
  const meta = await load('./data/landscape-flood-1900.json');
  if (meta.epoch !== '1900' || meta.schemaVersion !== 3) throw Error('Flood surface requires the 1900 landscape');
  const f = meta.files;
  const names = ['fineBed', 'fineConnection', 'fineWater', 'fineSupport', 'coarseBed', 'coarseConnection'];
  names.push('fineBasin', 'coarseBasin', 'coarseBasinBed', 'basinVolumes');
  const buffers = Object.fromEntries(
    await Promise.all(names.map(async (key) => [key, await load(`./data/${f[key]}`, 'buffer')]))
  );
  const data = {
    meta,
    fine: {
      bed: decodeLevels(meta, buffers.fineBed),
      connection: decodeLevels(meta, buffers.fineConnection),
      water: new Uint8Array(buffers.fineWater),
      support: new Uint8Array(buffers.fineSupport),
      basin: new Uint16Array(buffers.fineBasin),
    },
    coarse: {
      bed: decodeLevels(meta, buffers.coarseBed),
      connection: decodeLevels(meta, buffers.coarseConnection),
      basin: new Uint16Array(buffers.coarseBasin),
      basinBed: decodeLevels(meta, buffers.coarseBasinBed),
    },
  };
  for (const [key, grid] of [
    ['fine', data.fine],
    ['coarse', data.coarse],
  ])
    for (const array of Object.values(grid))
      if (array.length !== meta[key].width * meta[key].height) throw Error(`Invalid ${key} flood grid`);
  const model = basinModel(meta.volume, new Float32Array(buffers.basinVolumes));
  const offset = meta.verticalReference.odnMinusSceneYMetres;
  const scenarios = meta.volume.scenarios;
  const tideRange = { lowODN: meta.volume.tideODN.low, highODN: meta.volume.tideODN.high };

  // Connected extent: one plane per grid, the shoreline a contour of the interpolated connection field.
  const levelUniform = { value: meta.defaultLevelODN };
  const [bx0, bz0, bx1, bz1] = meta.fine.bounds;
  const colour = `vec3 shallow=vec3(0.24,0.68,0.79),deep=vec3(0.035,0.25,0.42);
          gl_FragColor=vec4(mix(shallow,deep,clamp(depth/2.0,0.0,1.0)),0.76);
          #include <tonemapping_fragment>
          #include <colorspace_fragment>`;
  function surface(grid, { width, height, bounds }, outsideFine) {
    const packed = new Uint16Array(width * height * 2);
    for (let i = 0; i < width * height; i++) {
      packed[i * 2] = THREE.DataUtils.toHalfFloat(grid.bed[i]);
      packed[i * 2 + 1] = THREE.DataUtils.toHalfFloat(grid.connection[i]);
    }
    const texture = new THREE.DataTexture(packed, width, height, THREE.RGFormat, THREE.HalfFloatType);
    texture.minFilter = texture.magFilter = THREE.LinearFilter;
    texture.needsUpdate = true;
    const material = new THREE.ShaderMaterial({
      uniforms: {
        surface: { value: texture },
        stage: levelUniform,
        fineBox: { value: new THREE.Vector4(bx0, bz0, bx1, bz1) },
      },
      defines: outsideFine ? { OUTSIDE_FINE: 1 } : {},
      transparent: true,
      depthWrite: false,
      side: THREE.DoubleSide,
      vertexShader: `varying vec2 uvFlood;varying vec2 worldXZ;
        void main(){uvFlood=vec2(uv.x,1.0-uv.y);vec4 w=modelMatrix*vec4(position,1.0);worldXZ=w.xz;
          gl_Position=projectionMatrix*viewMatrix*w;}`,
      fragmentShader: `uniform sampler2D surface;uniform float stage;uniform vec4 fineBox;varying vec2 uvFlood;varying vec2 worldXZ;
        void main(){
          #ifdef OUTSIDE_FINE
          if(worldXZ.x>fineBox.x&&worldXZ.x<fineBox.z&&worldXZ.y>fineBox.y&&worldXZ.y<fineBox.w)discard;
          #endif
          vec2 cell=texture2D(surface,uvFlood).rg;float depth=stage-cell.r;
          if(stage<=cell.g||depth<=0.015)discard;
          ${colour}
        }`,
    });
    const [x0, z0, x1, z1] = bounds;
    const mesh = new THREE.Mesh(new THREE.PlaneGeometry(x1 - x0, z1 - z0), material);
    mesh.rotation.x = -Math.PI / 2;
    mesh.position.set((x0 + x1) / 2, 0, (z0 + z1) / 2);
    mesh.renderOrder = 6;
    scene.add(mesh);
    return mesh;
  }
  const connectedMeshes = [surface(data.coarse, meta.coarse, true), surface(data.fine, meta.fine, false)];
  connectedMeshes[0].name = 'Connected inundation, regional 10 m grid — provisional 1900';
  connectedMeshes[1].name = 'Connected inundation, 2 m grid — provisional 1900';

  // Volume view: water drawn at each basin's level, rebuilt only when an input changes. The regional surface runs on
  // under the fine box's edge and is cut where the 2 m surface begins (its first cell centres), so no seam shows.
  const half = meta.fine.step / 2;
  const volumeMaterial = (outsideFine) =>
    new THREE.ShaderMaterial({
      uniforms: { fineBox: { value: new THREE.Vector4(bx0 + half, bz0 + half, bx1 - half, bz1 - half) } },
      defines: outsideFine ? { OUTSIDE_FINE: 1 } : {},
      transparent: true,
      depthWrite: false,
      side: THREE.DoubleSide,
      // Sheets a few centimetres deep would otherwise fight the ground beneath them.
      polygonOffset: true,
      polygonOffsetFactor: -2,
      polygonOffsetUnits: -4,
      vertexShader: `attribute float depth;varying float vDepth;varying vec2 worldXZ;
        void main(){vDepth=depth;vec4 w=modelMatrix*vec4(position,1.0);worldXZ=w.xz;gl_Position=projectionMatrix*viewMatrix*w;}`,
      fragmentShader: `uniform vec4 fineBox;varying float vDepth;varying vec2 worldXZ;
        void main(){float depth=vDepth;if(depth<=${MIN_DEPTH})discard;
          #ifdef OUTSIDE_FINE
          if(worldXZ.x>fineBox.x&&worldXZ.x<fineBox.z&&worldXZ.y>fineBox.y&&worldXZ.y<fineBox.w)discard;
          #endif
          ${colour}
        }`,
    });
  const volumeMeshes = ['coarse', 'fine'].map((key) => {
    const mesh = new THREE.Mesh(new THREE.BufferGeometry(), volumeMaterial(key === 'coarse'));
    mesh.name = `Volume flooding, ${key === 'fine' ? '2 m' : 'regional 10 m'} grid — provisional 1900`;
    mesh.position.y = 0.018 - offset;
    mesh.renderOrder = 6;
    mesh.frustumCulled = false;
    scene.add(mesh);
    return mesh;
  });
  // Regional quads wholly inside the fine box are not built at all.
  const cs = meta.coarse.step,
    insideFine = (x, z) =>
      x - cs / 2 > bx0 + half && x + cs / 2 < bx1 - half && z - cs / 2 > bz0 + half && z + cs / 2 < bz1 - half;
  const gridOf = (key) => {
    const g = meta[key];
    return {
      ids: data[key].basin,
      bed: (data[key].basinBed ?? data[key].bed).map((v) => (v >= NONE_ODN ? NaN : v)),
      width: g.width,
      height: g.height,
      x0: g.bounds[0],
      z0: g.bounds[1],
      step: g.step,
    };
  };
  const grids = { coarse: gridOf('coarse'), fine: gridOf('fine') };
  function drawVolume(levels) {
    ['coarse', 'fine'].forEach((key, n) => {
      const q = wetQuads(grids[key], levels, MIN_DEPTH, key === 'coarse' ? insideFine : null),
        geometry = new THREE.BufferGeometry();
      geometry.setAttribute('position', new THREE.BufferAttribute(q.positions, 3));
      geometry.setAttribute('depth', new THREE.BufferAttribute(q.depths, 1));
      geometry.setIndex(new THREE.BufferAttribute(q.indices, 1));
      volumeMeshes[n].geometry.dispose();
      volumeMeshes[n].geometry = geometry;
    });
  }

  const presets = scenarios.presets,
    c = scenarios.controls,
    first = presets[0];
  const durationOptions = c.durationTides.map((d) => `<option value="${d.tides}">${d.label}</option>`).join('');
  const panel = document.createElement('section');
  panel.className = 'landscape-flood-panel';
  panel.setAttribute('aria-label', 'Landscape flooding');
  const map = { width: meta.coarse.width, height: meta.coarse.height };
  panel.innerHTML = `<p class="flood-kicker">1890s · FLOOD MODEL TEST</p><h2>Water across the low ground</h2>
    <div class="flood-actions flood-modes" role="group" aria-label="View">
      <button id="flood-mode-volume" aria-pressed="true">Volume</button><button id="flood-mode-connected" aria-pressed="false">Connected extent</button></div>
    <div id="flood-volume-controls">
      <p>Rain, the tide and the river arrive as volumes. Water fills the lowest hollows first and spills on when they are full; the marsh sluices drain only while the tide outside is low.</p>
      <div class="flood-actions" role="group" aria-label="Scenarios">${presets.map((p) => `<button data-preset="${p.id}">${p.label}</button>`).join('')}</div>
      <p id="flood-preset-caption" class="flood-caveat"></p>
      <label for="flood-rain">Rain <output id="flood-rain-value"></output></label>
      <input id="flood-rain" type="range" min="${c.rainMm.min}" max="${c.rainMm.max}" step="${c.rainMm.step}" value="${first.rainMm}">
      <label for="flood-duration">Over</label>
      <select id="flood-duration">${durationOptions}</select>
      <label for="flood-surge">Surge above ordinary high water <output id="flood-surge-value"></output></label>
      <input id="flood-surge" type="range" min="${c.surgeM.min}" max="${c.surgeM.max}" step="${c.surgeM.step}" value="${first.surgeM}">
      <label for="flood-river">River held at <output id="flood-river-value"></output></label>
      <input id="flood-river" type="range" min="${c.riverLevelODN.min}" max="${c.riverLevelODN.max}" step="${c.riverLevelODN.step}" value="${first.riverLevelODN}">
    </div>
    <div id="flood-connected-controls" hidden>
      <p>Raise the tidal river and watch water reach connected low ground across ${(meta.areaM2 / 1e6).toFixed(1)} km² of the modelled marsh. Every reachable hollow fills at once: an upper bound, not a flood.</p>
      <label for="landscape-stage">River level <output id="landscape-stage-value"></output></label>
      <input id="landscape-stage" type="range" min="${meta.minLevelODN}" max="${meta.maxLevelODN}" step="0.05" value="${meta.defaultLevelODN}">
      <div class="flood-actions"><button id="landscape-rise">Raise water</button></div>
    </div>
    <div class="flood-actions"><button id="landscape-toggle" aria-pressed="true">Show dry comparison</button></div>
    <p id="landscape-flood-stats" role="status"></p>
    <p id="flood-ledger" class="flood-caveat"></p>
    <div class="flood-actions"><button id="landscape-overview">Overview</button><button id="landscape-meads">Mill Meads</button><button id="landscape-mills">Three Mills</button><button id="landscape-sewer">Sewer crossing</button></div>
    <p class="flood-caveat">A test of the mechanisms, not a dated flood or a prediction. Rain totals, weir and sluice figures are estimates; the mill ponds and the Lea flow come in Phase 2. Water is shown at the peak of the chosen conditions.</p>
    <details><summary>Depth map and assumptions</summary><canvas id="landscape-depth-map" width="${map.width}" height="${map.height}" role="img" aria-label="North-up map of flooding"></canvas>
      <p>North ↑ · Pale to dark blue: shallow to deep water.</p>
      <p>Volume view: ${meta.volume.stats.hollows} hollows merge at their saddles into a hierarchy; each has a stage–volume table. All rain on a hollow's catchment runs into it (no soakage, no town sewers). The tide and the river pour over a crest by a weir rule while they stand above it. The marsh sluices run at an estimated ${meta.volume.parameters.sluiceDischargeM3PerSecond} m³/s each while the water outside is below their sill.</p>
      <p>Hollows smaller than ${meta.volume.parameters.minAreaHa} ha or shallower than ${meta.volume.parameters.minDepthMetres * 100} cm are filled. The Abbey Mill gates are shut against the tide; the Thames frontage is treated as walled. Buildings remain visible; indoor flooding is not calculated. Heights use the provisional ODN reference.</p>
      <a href="./lower-lea-region.html">Regional expansion: Lea Bridge to the Thames</a><br>
      <a href="./data/landscape-flood-1900.json">Surface provenance</a> · <a href="./flood-demo.html">Local drainage experiment</a>
    </details><a class="flood-exit" href="./">Return to normal landscape</a>`;
  document.querySelector('.stage').append(panel);
  document.body.classList.add('is-flood-view');
  const $ = (id) => panel.querySelector('#' + id);
  let enabled = true,
    mode = 'volume',
    stage = meta.defaultLevelODN,
    timer = null,
    inputs = { ...first, preset: first.id },
    result = null;

  // The depth map is the 10 m grid; each fine-box pixel takes the lowest of its 2 m cells.
  const ratio = meta.coarse.step / meta.fine.step,
    ci0 = (bx0 - meta.coarse.bounds[0]) / meta.coarse.step,
    cj0 = (bz0 - meta.coarse.bounds[1]) / meta.coarse.step,
    mapBed = Float32Array.from(data.coarse.bed),
    mapConnection = Float32Array.from(data.coarse.connection),
    mapBasin = Uint16Array.from(data.coarse.basin),
    mapBasinBed = Float32Array.from(data.coarse.basinBed),
    mapWater = new Float32Array(map.width * map.height);
  for (let j = 0; j < meta.fine.height; j++)
    for (let i = 0; i < meta.fine.width; i++) {
      const s = j * meta.fine.width + i,
        t = (cj0 + Math.floor(j / ratio)) * map.width + ci0 + Math.floor(i / ratio);
      if (i % ratio === 0 && j % ratio === 0) {
        mapBed[t] = mapConnection[t] = NONE_ODN;
        mapBasin[t] = 0;
      }
      if (data.fine.bed[s] < mapBed[t]) {
        mapBed[t] = mapBasinBed[t] = data.fine.bed[s];
        mapBasin[t] = data.fine.basin[s];
      }
      mapConnection[t] = Math.min(mapConnection[t], data.fine.connection[s]);
      mapWater[t] = Math.max(mapWater[t], data.fine.water[s] / 255);
    }
  const canvas = $('landscape-depth-map'),
    ctx = canvas.getContext('2d'),
    pixels = ctx.createImageData(map.width, map.height);
  function paintMap() {
    for (let i = 0; i < mapBed.length; i++) {
      let depth;
      if (mode === 'volume') depth = mapBasin[i] && result ? result.levels[mapBasin[i] - 1] - mapBasinBed[i] : -1;
      else depth = stage > mapConnection[i] ? stage - mapBed[i] : -1;
      const wet = enabled && depth > MIN_DEPTH,
        t = Math.max(0, Math.min(1, depth / 2));
      let c = wet ? [61 - 52 * t, 173 - 109 * t, 201 - 94 * t] : mapWater[i] > 0.5 ? [86, 116, 114] : [163, 158, 122];
      if (!wet && mapBed[i] > 4) c = [109, 112, 88];
      if (mapBed[i] >= NONE_ODN) c = [226, 224, 215];
      pixels.data.set([...c, 255], i * 4);
    }
    ctx.putImageData(pixels, 0, 0);
  }

  const hectares = (m2) => (m2 / 10000).toFixed(1);
  const thousands = (m3) => `${Math.round(m3 / 1000).toLocaleString('en-GB')} thousand m³`;
  function apply() {
    let stats;
    for (const mesh of connectedMeshes) mesh.visible = enabled && mode === 'connected';
    for (const mesh of volumeMeshes) mesh.visible = enabled && mode === 'volume';
    $('flood-volume-controls').hidden = mode !== 'volume';
    $('flood-connected-controls').hidden = mode !== 'connected';
    $('flood-mode-volume').setAttribute('aria-pressed', String(mode === 'volume'));
    $('flood-mode-connected').setAttribute('aria-pressed', String(mode === 'connected'));
    if (mode === 'volume') {
      result = routeFlood(model, { ...tideRange, ...inputs });
      drawVolume(result.levels);
      stats = volumeMetrics(data, model, result.levels);
      const L = result.ledger;
      setWater(enabled ? tideRange.highODN + inputs.surgeM : null);
      $('flood-rain').value = inputs.rainMm;
      $('flood-rain-value').textContent = `${inputs.rainMm} mm`;
      $('flood-duration').value = String(inputs.tides);
      $('flood-surge').value = inputs.surgeM;
      $('flood-surge-value').textContent = `${inputs.surgeM.toFixed(2)} m`;
      $('flood-river').value = inputs.riverLevelODN;
      $('flood-river-value').textContent = `${inputs.riverLevelODN.toFixed(2)} m ODN`;
      $('flood-preset-caption').textContent =
        presets.find((p) => p.id === inputs.preset)?.caption ?? 'Custom conditions.';
      $('flood-ledger').textContent = enabled
        ? `Rain ${thousands(L.rain)}; in over the banks ${thousands(L.tide + L.river - L.returned)}; drained by the sluices ${thousands(L.drained)}; run off to the rivers ${thousands(L.spilled)}; standing on the land ${thousands(L.stored)}.`
        : '';
    } else {
      stats = floodMetrics(data, stage);
      levelUniform.value = stage;
      for (const mesh of connectedMeshes) mesh.position.y = stage - offset + 0.018;
      setWater(enabled ? stage : null);
      $('landscape-stage').value = stage;
      $('landscape-stage-value').textContent = `${stage.toFixed(2)} m ODN`;
      $('flood-ledger').textContent = '';
    }
    $('landscape-toggle').textContent = enabled ? 'Show dry comparison' : 'Show flooding';
    $('landscape-toggle').setAttribute('aria-pressed', String(enabled));
    $('landscape-flood-stats').textContent = enabled
      ? `${hectares(stats.floodedLandM2)} hectares of land under water (${hectares(stats.fineLandM2)} around the core) · up to ${stats.maxLandDepth.toFixed(1)} m deep near the core`
      : 'Dry comparison — original landscape and river level.';
    paintMap();
    render();
    window.landscapeFloodReview.state = {
      ...stats,
      mode,
      enabled,
      inputs: mode === 'volume' ? { ...inputs } : { levelODN: stage },
      ledger: mode === 'volume' ? { ...result.ledger } : null,
      epoch: meta.epoch,
      bounds: meta.bounds,
      method: mode === 'volume' ? 'fill-and-spill-volume' : meta.method,
    };
  }
  function pause() {
    clearInterval(timer);
    timer = null;
    $('landscape-rise').textContent = 'Raise water';
  }
  function setLevel(value) {
    if (!Number.isFinite(value) || value < meta.minLevelODN || value > meta.maxLevelODN)
      throw Error('Water level outside test range');
    stage = value;
    apply();
  }
  function setInputs(next) {
    const merged = { ...inputs, ...next };
    for (const key of ['rainMm', 'surgeM', 'riverLevelODN']) {
      const { min, max } = c[key];
      if (!Number.isFinite(merged[key]) || merged[key] < min || merged[key] > max) throw Error(`${key} outside range`);
    }
    if (!c.durationTides.some((d) => d.tides === merged.tides)) throw Error('Unknown duration');
    inputs = merged;
    apply();
  }
  const setPreset = (id) => {
    const p = presets.find((q) => q.id === id);
    if (!p) throw Error(`Unknown preset ${id}`);
    setInputs({ rainMm: p.rainMm, tides: p.tides, surgeM: p.surgeM, riverLevelODN: p.riverLevelODN, preset: id });
  };
  const setMode = (value) => {
    if (value !== 'volume' && value !== 'connected') throw Error('Unknown flood view');
    pause();
    mode = value;
    apply();
  };
  window.landscapeFloodReview = {
    setLevel,
    setInputs,
    setPreset,
    setMode,
    setEnabled: (value) => {
      enabled = Boolean(value);
      apply();
    },
    state: null,
  };
  for (const button of panel.querySelectorAll('[data-preset]'))
    button.addEventListener('click', () => setPreset(button.dataset.preset));
  const control = (id, key) =>
    $(id).addEventListener('input', () => setInputs({ [key]: Number($(id).value), preset: null }));
  control('flood-rain', 'rainMm');
  control('flood-surge', 'surgeM');
  control('flood-river', 'riverLevelODN');
  $('flood-duration').addEventListener('change', () =>
    setInputs({ tides: Number($('flood-duration').value), preset: null })
  );
  $('flood-mode-volume').addEventListener('click', () => setMode('volume'));
  $('flood-mode-connected').addEventListener('click', () => setMode('connected'));
  $('landscape-stage').addEventListener('input', () => {
    pause();
    setLevel(Number($('landscape-stage').value));
  });
  $('landscape-toggle').addEventListener('click', () => {
    pause();
    enabled = !enabled;
    apply();
  });
  $('landscape-rise').addEventListener('click', () => {
    if (timer) {
      pause();
      return;
    }
    enabled = true;
    if (stage >= meta.maxLevelODN) stage = meta.minLevelODN;
    $('landscape-rise').textContent = 'Pause rise';
    timer = setInterval(() => {
      setLevel(Math.min(meta.maxLevelODN, Math.round((stage + 0.05) * 100) / 100));
      if (stage >= meta.maxLevelODN) pause();
    }, 350);
  });
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) pause();
  });
  const overview = () => travel({ position: [850, 1100, 1330], target: [-50, 0, 245], fov: 58 });
  $('landscape-overview').addEventListener('click', overview);
  $('landscape-meads').addEventListener('click', () =>
    travel({ position: [-120, 120, 420], target: [-300, 0, 180], fov: 62 })
  );
  $('landscape-mills').addEventListener('click', () =>
    travel({ position: [-430, 200, 800], target: [-280, 0, 300], fov: 62 })
  );
  $('landscape-sewer').addEventListener('click', () =>
    travel({ position: [100, 90, 160], target: [-30, 3, 0], fov: 65 })
  );
  overview();
  apply();
  return { pause, meta };
}
