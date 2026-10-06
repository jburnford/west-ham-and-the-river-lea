// Connected water at a uniform stage over the whole modelled ground (FLOOD_MODEL_PLAN.md, Phase 1).
// Two grids from scripts/build_landscape_flood.py: 2 m over the back rivers, Three Mills and the core, and 10 m over
// the rest of the regional landscape. Levels arrive as uint16 centimetres; this module only evaluates them.
const NONE_ODN = 100; // stand-in for "never wet" on the GPU (half floats stop at 65504)

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

export async function installLandscapeFlood({ THREE, scene, load, render, travel, setWater }) {
  const meta = await load('./data/landscape-flood-1900.json');
  if (meta.epoch !== '1900' || meta.schemaVersion !== 2) throw Error('Flood surface requires the 1900 landscape');
  const f = meta.files;
  const [fineBed, fineConnection, fineWater, fineSupport, coarseBed, coarseConnection] = await Promise.all(
    [f.fineBed, f.fineConnection, f.fineWater, f.fineSupport, f.coarseBed, f.coarseConnection].map((name) =>
      load(`./data/${name}`, 'buffer')
    )
  );
  const data = {
    meta,
    fine: {
      bed: decodeLevels(meta, fineBed),
      connection: decodeLevels(meta, fineConnection),
      water: new Uint8Array(fineWater),
      support: new Uint8Array(fineSupport),
    },
    coarse: { bed: decodeLevels(meta, coarseBed), connection: decodeLevels(meta, coarseConnection) },
  };
  for (const [key, grid] of [
    ['fine', data.fine],
    ['coarse', data.coarse],
  ])
    for (const array of Object.values(grid))
      if (array.length !== meta[key].width * meta[key].height) throw Error(`Invalid ${key} flood grid`);

  const levelUniform = { value: meta.defaultLevelODN };
  const [bx0, bz0, bx1, bz1] = meta.fine.bounds;
  // Half-float textures filter linearly on every WebGL2 device, so the shoreline is a contour of the interpolated
  // connection field rather than the cell outlines.
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
          vec3 shallow=vec3(0.24,0.68,0.79),deep=vec3(0.035,0.25,0.42);
          gl_FragColor=vec4(mix(shallow,deep,clamp(depth/2.0,0.0,1.0)),0.76);
          #include <tonemapping_fragment>
          #include <colorspace_fragment>
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
  const meshes = [surface(data.coarse, meta.coarse, true), surface(data.fine, meta.fine, false)];
  meshes[0].name = 'Connected inundation, regional 10 m grid — provisional 1900';
  meshes[1].name = 'Connected inundation, 2 m grid — provisional 1900';

  const panel = document.createElement('section');
  panel.className = 'landscape-flood-panel';
  panel.setAttribute('aria-label', 'Landscape flooding');
  const map = { width: meta.coarse.width, height: meta.coarse.height };
  panel.innerHTML = `<p class="flood-kicker">1900 · WHOLE-MODEL TEST</p><h2>Water across the low ground</h2>
    <p>Raise the tidal river and watch water reach connected low ground across ${(meta.areaM2 / 1e6).toFixed(1)} km² of the modelled marsh, from Lea Bridge to the Thames.</p>
    <label for="landscape-stage">River level <output id="landscape-stage-value"></output></label>
    <input id="landscape-stage" type="range" min="${meta.minLevelODN}" max="${meta.maxLevelODN}" step="0.05" value="${meta.defaultLevelODN}">
    <div class="flood-actions"><button id="landscape-rise">Raise water</button><button id="landscape-toggle" aria-pressed="true">Show dry comparison</button></div>
    <p id="landscape-flood-stats" role="status"></p>
    <div class="flood-actions"><button id="landscape-overview">Overview</button><button id="landscape-mills">Three Mills</button><button id="landscape-sewer">Sewer crossing</button></div>
    <p class="flood-caveat">Possible extent at a chosen level, not a dated flood or a prediction. Only the tide is a source so far; the mill ponds, the Navigation and rain come next. Outside the core the regional ground is still the early-marsh surface, lower than the 1890s levels, so water there is overstated.</p>
    <details><summary>Depth map and assumptions</summary><canvas id="landscape-depth-map" width="${map.width}" height="${map.height}" role="img" aria-label="North-up map of connected flooding"></canvas>
      <p>North ↑ · Pale to dark blue: shallow to deep water.</p>
      <p>The model admits water from the tidal reaches over the intervening banks. It does not fill every low spot. All tidal reaches share one test level; the Abbey Mill gates are shut against the tide. The Thames frontage is treated as walled.</p>
      <p>Existing embankments retain the scene’s interpreted heights, including the unresolved railway levels. Buildings remain visible; indoor flooding is not calculated. Heights use the provisional ODN reference.</p>
      <a href="./lower-lea-region.html">Regional expansion: Lea Bridge to the Thames</a><br>
      <a href="./data/landscape-flood-1900.json">Surface provenance</a> · <a href="./flood-demo.html">Local drainage experiment</a>
    </details><a class="flood-exit" href="./">Return to normal landscape</a>`;
  document.querySelector('.stage').append(panel);
  document.body.classList.add('is-flood-view');
  const $ = (id) => panel.querySelector('#' + id);
  let enabled = true,
    level = meta.defaultLevelODN,
    timer = null;
  // The depth map is the 10 m grid, with each fine-box pixel the lowest of its 2 m cells.
  const mapBed = Float32Array.from(data.coarse.bed),
    mapConnection = Float32Array.from(data.coarse.connection),
    mapWater = new Float32Array(map.width * map.height),
    ratio = meta.coarse.step / meta.fine.step,
    ci0 = (bx0 - meta.coarse.bounds[0]) / meta.coarse.step,
    cj0 = (bz0 - meta.coarse.bounds[1]) / meta.coarse.step;
  for (let j = 0; j < meta.fine.height; j++)
    for (let i = 0; i < meta.fine.width; i++) {
      const s = j * meta.fine.width + i,
        t = (cj0 + Math.floor(j / ratio)) * map.width + ci0 + Math.floor(i / ratio);
      if (i % ratio === 0 && j % ratio === 0) mapBed[t] = mapConnection[t] = NONE_ODN;
      mapBed[t] = Math.min(mapBed[t], data.fine.bed[s]);
      mapConnection[t] = Math.min(mapConnection[t], data.fine.connection[s]);
      mapWater[t] = Math.max(mapWater[t], data.fine.water[s] / 255);
    }
  const canvas = $('landscape-depth-map'),
    ctx = canvas.getContext('2d'),
    pixels = ctx.createImageData(map.width, map.height);
  function paintMap() {
    for (let i = 0; i < mapBed.length; i++) {
      const depth = level - mapBed[i],
        wet = enabled && level > mapConnection[i] && depth > 0.015;
      const t = Math.max(0, Math.min(1, depth / 2));
      let c = wet ? [61 - 52 * t, 173 - 109 * t, 201 - 94 * t] : mapWater[i] > 0.5 ? [86, 116, 114] : [163, 158, 122];
      if (!wet && mapBed[i] > 4) c = [109, 112, 88];
      if (mapBed[i] >= NONE_ODN) c = [226, 224, 215];
      pixels.data.set([...c, 255], i * 4);
    }
    ctx.putImageData(pixels, 0, 0);
  }
  function apply() {
    const stats = floodMetrics(data, level);
    levelUniform.value = level;
    for (const mesh of meshes) {
      mesh.position.y = level - meta.verticalReference.odnMinusSceneYMetres + 0.018;
      mesh.visible = enabled;
    }
    setWater(enabled ? level : null);
    $('landscape-stage').value = level;
    $('landscape-stage-value').textContent = `${level.toFixed(2)} m ODN`;
    $('landscape-toggle').textContent = enabled ? 'Show dry comparison' : 'Show flooding';
    $('landscape-toggle').setAttribute('aria-pressed', String(enabled));
    $('landscape-flood-stats').textContent = enabled
      ? `${(stats.floodedLandM2 / 10000).toFixed(1)} hectares of land connected (${(stats.fineLandM2 / 10000).toFixed(1)} around the core) · up to ${stats.maxLandDepth.toFixed(1)} m deep near the core`
      : 'Dry comparison — original landscape and river level.';
    paintMap();
    render();
    window.landscapeFloodReview.state = {
      ...stats,
      enabled,
      epoch: meta.epoch,
      bounds: meta.bounds,
      method: meta.method,
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
    level = value;
    apply();
  }
  window.landscapeFloodReview = {
    setLevel,
    setEnabled: (value) => {
      enabled = Boolean(value);
      apply();
    },
    state: null,
  };
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
    if (level >= meta.maxLevelODN) level = meta.minLevelODN;
    $('landscape-rise').textContent = 'Pause rise';
    timer = setInterval(() => {
      setLevel(Math.min(meta.maxLevelODN, Math.round((level + 0.05) * 100) / 100));
      if (level >= meta.maxLevelODN) pause();
    }, 350);
  });
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) pause();
  });
  const overview = () => travel({ position: [850, 1100, 1330], target: [-50, 0, 245], fov: 58 });
  $('landscape-overview').addEventListener('click', overview);
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
