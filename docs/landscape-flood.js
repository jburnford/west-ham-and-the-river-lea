// First landscape-wide experiment: connected water at a uniform stage.
// This deliberately has no simulated clock, discharge or event attribution.
export function floodMetrics(data, level) {
  if (!Number.isFinite(level)) throw Error('A finite water level is required');
  let area = 0,
    volume = 0,
    maxDepth = 0,
    supportedArea = 0,
    cells = 0;
  const cellArea = data.meta.step ** 2;
  for (let i = 0; i < data.bed.length; i++) {
    const depth = level - data.bed[i];
    if (level <= data.connection[i] || depth <= 0.05) continue;
    const land = 1 - data.riverFraction[i];
    area += land * cellArea;
    volume += land * cellArea * depth;
    if (land > 0.5) maxDepth = Math.max(maxDepth, depth);
    supportedArea += data.support[i] * cellArea;
    cells++;
  }
  return {
    levelODN: level,
    floodedLandM2: area,
    geometricVolumeM3: volume,
    maxLandDepth: maxDepth,
    supportedFieldAreaM2: supportedArea,
    wetCells: cells,
  };
}

export async function installLandscapeFlood({ THREE, scene, load, render, travel, setWater }) {
  const meta = await load('./data/landscape-flood-1900.json');
  if (meta.epoch !== '1900') throw Error('Flood surface requires the 1900 landscape');
  const keys = ['bed', 'connection', 'riverFraction', 'support'];
  const buffers = await Promise.all(keys.map((k) => load(`./data/${meta.files[k]}`, 'buffer')));
  const data = { meta, ...Object.fromEntries(keys.map((k, i) => [k, new Float32Array(buffers[i])])) };
  const count = meta.width * meta.height;
  for (const k of keys)
    if (data[k].length !== count || !data[k].every(Number.isFinite)) throw Error('Invalid flood grid');
  const packed = new Float32Array(count * 4);
  for (let i = 0; i < count; i++)
    packed.set([data.bed[i], data.connection[i], data.riverFraction[i], data.support[i]], i * 4);
  const texture = new THREE.DataTexture(packed, meta.width, meta.height, THREE.RGBAFormat, THREE.FloatType);
  texture.minFilter = texture.magFilter = THREE.NearestFilter;
  texture.needsUpdate = true;
  const levelUniform = { value: meta.defaultLevelODN };
  const material = new THREE.ShaderMaterial({
    uniforms: { surface: { value: texture }, stage: levelUniform },
    transparent: true,
    depthWrite: false,
    side: THREE.DoubleSide,
    vertexShader:
      'varying vec2 uvFlood; void main(){uvFlood=vec2(uv.x,1.0-uv.y);gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}',
    fragmentShader: `uniform sampler2D surface;uniform float stage;varying vec2 uvFlood;
      void main(){vec4 cell=texture2D(surface,uvFlood);float depth=stage-cell.r;
        if(stage<=cell.g || depth<=0.015)discard;
        vec3 shallow=vec3(0.24,0.68,0.79),deep=vec3(0.035,0.25,0.42);
        gl_FragColor=vec4(mix(shallow,deep,clamp(depth/2.0,0.0,1.0)),0.76);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`,
  });
  const [x0, z0, x1, z1] = meta.bounds;
  const mesh = new THREE.Mesh(new THREE.PlaneGeometry(x1 - x0, z1 - z0), material);
  mesh.name = 'Connected landscape inundation — provisional 1900';
  mesh.rotation.x = -Math.PI / 2;
  mesh.position.set((x0 + x1) / 2, 0, (z0 + z1) / 2);
  mesh.renderOrder = 6;
  scene.add(mesh);
  const framePoints = [
    [x0, z0],
    [x1, z0],
    [x1, z1],
    [x0, z1],
    [x0, z0],
  ].map(([x, z]) => new THREE.Vector3(x, 0, z));
  const outline = new THREE.Line(
    new THREE.BufferGeometry().setFromPoints(framePoints),
    new THREE.LineDashedMaterial({ color: 0xf5d99e, dashSize: 12, gapSize: 8, transparent: true, opacity: 0.7 })
  );
  outline.computeLineDistances();
  scene.add(outline);
  const panel = document.createElement('section');
  panel.className = 'landscape-flood-panel';
  panel.setAttribute('aria-label', 'Landscape flooding');
  panel.innerHTML = `<p class="flood-kicker">1900 · FIRST LANDSCAPE TEST</p><h2>Water across the low ground</h2>
    <p>Raise the river and watch water reach connected low ground across ${(meta.areaM2 / 1e6).toFixed(2)} km² of the landscape.</p>
    <label for="landscape-stage">River level <output id="landscape-stage-value"></output></label>
    <input id="landscape-stage" type="range" min="${meta.minLevelODN}" max="${meta.maxLevelODN}" step="0.05" value="${meta.defaultLevelODN}">
    <div class="flood-actions"><button id="landscape-rise">Raise water</button><button id="landscape-toggle" aria-pressed="true">Show dry comparison</button></div>
    <p id="landscape-flood-stats" role="status"></p>
    <div class="flood-actions"><button id="landscape-overview">Overview</button><button id="landscape-mills">Three Mills</button><button id="landscape-sewer">Sewer crossing</button></div>
    <p class="flood-caveat">Possible extent at a chosen level, not a dated flood or a prediction. Banks and much of the ground are provisional. Lowering the slider removes water immediately; drainage and ponding come later.</p>
    <details><summary>Depth map and assumptions</summary><canvas id="landscape-depth-map" width="${meta.width}" height="${meta.height}" role="img" aria-label="North-up map of connected flooding"></canvas>
      <p>North ↑ · Pale to dark blue: shallow to deep water. Gold outline in the landscape: model boundary. Terrain outside it has no flood calculation.</p>
      <p>The model admits water from mapped tidal reaches over the intervening banks. It does not fill every low spot. All tidal reaches share one test level; mill gates, rainfall, runoff, drains and flow speed are later layers.</p>
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
  const map = $('landscape-depth-map'),
    ctx = map.getContext('2d'),
    pixels = ctx.createImageData(meta.width, meta.height);
  function paintMap() {
    for (let i = 0; i < count; i++) {
      const depth = level - data.bed[i],
        wet = enabled && level > data.connection[i] && depth > 0.015;
      const t = Math.max(0, Math.min(1, depth / 2));
      let c = wet
        ? [61 - 52 * t, 173 - 109 * t, 201 - 94 * t]
        : data.riverFraction[i] > 0.5
          ? [86, 116, 114]
          : [163, 158, 122];
      if (!wet && data.bed[i] > 4) c = [109, 112, 88];
      pixels.data.set([...c, 255], i * 4);
    }
    ctx.putImageData(pixels, 0, 0);
  }
  function apply() {
    const stats = floodMetrics(data, level);
    levelUniform.value = level;
    mesh.position.y = level - meta.verticalReference.odnMinusSceneYMetres + 0.018;
    outline.position.y = mesh.position.y + 0.1;
    mesh.visible = outline.visible = enabled;
    setWater(enabled ? level : null);
    $('landscape-stage').value = level;
    $('landscape-stage-value').textContent = `${level.toFixed(2)} m ODN`;
    $('landscape-toggle').textContent = enabled ? 'Show dry comparison' : 'Show flooding';
    $('landscape-toggle').setAttribute('aria-pressed', String(enabled));
    $('landscape-flood-stats').textContent = enabled
      ? `${(stats.floodedLandM2 / 10000).toFixed(1)} hectares of land connected · up to ${stats.maxLandDepth.toFixed(1)} m deep`
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
