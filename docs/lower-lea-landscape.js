import * as THREE from './vendor/three/three.module.js';
const $ = (id) => document.getElementById(id),
  base = './data/lower-lea-region/';
async function fetchData(name, binary = false) {
  const r = await fetch(base + name);
  if (!r.ok) throw Error(`Cannot load ${name}`);
  return binary ? r.arrayBuffer() : r.json();
}
try {
  const meta = await fetchData('landscape-1900.json');
  const [raw, kindsRaw, facesRaw, groundRaw, groundKindsRaw] = await Promise.all(
    [meta.heightFile, meta.kindFile, meta.displayMesh.faceFile, meta.groundFile, meta.groundKindFile].map((n) =>
      fetchData(n, true)
    )
  );
  const surfaceHeights = new Float32Array(raw),
    surfaceKinds = new Uint8Array(kindsRaw),
    groundHeights = new Float32Array(groundRaw),
    groundKinds = new Uint8Array(groundKindsRaw),
    faces = new Uint32Array(facesRaw);
  let heights = surfaceHeights,
    kinds = surfaceKinds,
    surfaceMode = 'surface';
  if (
    heights.length !== meta.width * meta.height ||
    kinds.length !== heights.length ||
    faces.length !== meta.displayMesh.triangleCount * 3
  )
    throw Error('Landscape data size mismatch');
  const structureMeta = meta.continuousStructures.fineMesh;
  const [structureRaw, structureKindsRaw] = await Promise.all(
    [structureMeta.positionFile, structureMeta.kindFile].map((n) => fetchData(n, true))
  );
  const structureOriginal = new Float32Array(structureRaw),
    structureKinds = new Uint8Array(structureKindsRaw);
  if (structureOriginal.length !== structureMeta.vertexCount * 3 || structureKinds.length !== structureMeta.vertexCount)
    throw Error('Structural mesh data size mismatch');
  const observations = await fetchData('marsh-evidence/later-surface-evidence.json');
  const frame = $('landscape-frame'),
    scene = new THREE.Scene();
  scene.background = new THREE.Color('#dbe6e7');
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  frame.append(renderer.domElement);
  renderer.domElement.tabIndex = 0;
  renderer.domElement.setAttribute(
    'aria-label',
    'Three dimensional Lower Lea landscape. Arrow keys rotate; plus and minus zoom; Home resets.'
  );
  const camera = new THREE.PerspectiveCamera(42, 1, 10, 50000),
    geometry = new THREE.BufferGeometry();
  const positions = new Float32Array(heights.length * 3),
    colours = new Float32Array(positions.length);
  const [e0, n0, e1, n1] = meta.boundsBNG,
    cx = (e0 + e1) / 2,
    cn = (n0 + n1) / 2,
    step = meta.cellSizeMetres;
  const stops = [-1, 0, 2, 5, 10, 20, 35],
    rgb = [
      [90, 122, 116],
      [133, 164, 146],
      [176, 188, 145],
      [210, 202, 164],
      [189, 161, 126],
      [151, 126, 104],
      [229, 221, 199],
    ];
  const evidence = [
    '#ebe8e2',
    '#3e7854',
    '#2e5e45',
    '#ceb982',
    '#c0a69c',
    '#76bcc7',
    '#7ba682',
    '#9bbe97',
    '#a18b58',
    '#90bea6',
    '#bd946f',
    '#977b61',
    '#af974f',
    '#9184ad',
    '#acb091',
    '#747f94',
  ];
  const pointGeometry = new THREE.BufferGeometry(),
    pointPositions = new Float32Array(observations.length * 3);
  const pointColours = new Float32Array(observations.length * 3);
  observations.forEach((r, i) =>
    new THREE.Color(r.usedInMappedLayer ? '#203f73' : '#b83e32').toArray(pointColours, i * 3)
  );
  pointGeometry.setAttribute('position', new THREE.BufferAttribute(pointPositions, 3));
  pointGeometry.setAttribute('color', new THREE.BufferAttribute(pointColours, 3));
  const marks = new THREE.Points(
    pointGeometry,
    new THREE.PointsMaterial({ size: 6, sizeAttenuation: false, vertexColors: true, depthTest: false })
  );
  marks.visible = false;
  marks.renderOrder = 2;
  scene.add(marks);
  const structureGeometry = new THREE.BufferGeometry(),
    structurePositions = structureOriginal.slice(),
    structureColours = new Float32Array(structureOriginal.length);
  structureGeometry.setAttribute('position', new THREE.BufferAttribute(structurePositions, 3));
  structureGeometry.setAttribute('color', new THREE.BufferAttribute(structureColours, 3));
  const structures = new THREE.Mesh(
    structureGeometry,
    new THREE.MeshLambertMaterial({
      vertexColors: true,
      side: THREE.DoubleSide,
      polygonOffset: true,
      polygonOffsetFactor: -1,
      polygonOffsetUnits: -1,
    })
  );
  scene.add(structures);
  const colour = new THREE.Color();
  let scale = 4,
    colourMode = 'height';
  function updateMesh() {
    observations.forEach((r, i) =>
      pointPositions.set([r.positionBNG[0] - cx, r.heightODNMetres * scale, cn - r.positionBNG[1]], i * 3)
    );
    pointGeometry.attributes.position.needsUpdate = true;
    pointGeometry.computeBoundingSphere();
    for (let i = 0; i < heights.length; i++) {
      const row = Math.floor(i / meta.width),
        col = i % meta.width;
      // Fine continuous structures replace the aliased bank/formation bumps.
      const value = surfaceMode === 'surface' && [12, 13].includes(kinds[i]) ? groundHeights[i] : heights[i],
        h = Number.isFinite(value) ? value : 0;
      positions.set([e0 + (col + 0.5) * step - cx, h * scale, cn - (n1 - (row + 0.5) * step)], i * 3);
      if (colourMode === 'evidence') colour.set(evidence[kinds[i]]);
      else {
        let lo = 0;
        while (lo < stops.length - 2 && h > stops[lo + 1]) lo++;
        const t = THREE.MathUtils.clamp((h - stops[lo]) / (stops[lo + 1] - stops[lo]), 0, 1);
        colour.setRGB(...[0, 1, 2].map((k) => (rgb[lo][k] * (1 - t) + rgb[lo + 1][k] * t) / 255), THREE.SRGBColorSpace);
      }
      colour.toArray(colours, i * 3);
    }
    structures.visible = surfaceMode === 'surface';
    for (let i = 0; i < structureKinds.length; i++) {
      const h = structureOriginal[i * 3 + 1];
      structurePositions[i * 3 + 1] = h * scale;
      if (colourMode === 'evidence') colour.set(evidence[structureKinds[i]]);
      else {
        let lo = 0;
        while (lo < stops.length - 2 && h > stops[lo + 1]) lo++;
        const t = THREE.MathUtils.clamp((h - stops[lo]) / (stops[lo + 1] - stops[lo]), 0, 1);
        colour.setRGB(...[0, 1, 2].map((k) => (rgb[lo][k] * (1 - t) + rgb[lo + 1][k] * t) / 255), THREE.SRGBColorSpace);
      }
      colour.toArray(structureColours, i * 3);
    }
    structureGeometry.attributes.position.needsUpdate = true;
    structureGeometry.attributes.color.needsUpdate = true;
    structureGeometry.computeVertexNormals();
    structureGeometry.computeBoundingSphere();
    geometry.attributes.position.needsUpdate = true;
    geometry.attributes.color.needsUpdate = true;
    geometry.computeVertexNormals();
    geometry.computeBoundingSphere();
    $('landscape-legend').textContent =
      colourMode === 'evidence'
        ? 'Green: historical interpolation · Dark green: control cell · Mint: regional 1848 marsh estimate · Light green: reviewed local marsh · Ochre: bank or cottage garden · Brown: street or yard · Gold: continuous river/canal bank · Purple: railway/sewer · Slate: elevated water span · Grey-green: approximate marsh boundary · Tan: estimate near historical anchors · Rose: distant or disconnected modern-relief estimate.'
        : 'Colour follows elevation. Switch to Evidence and estimates to see where historical levels constrain the surface.';
    if (marks.visible)
      $('landscape-legend').textContent +=
        ' Reading markers: blue contributes to a mapped surface fit; red still lacks a match. Markers are drawn over the terrain; their heights do not create surrounding fill.';
  }
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute('color', new THREE.BufferAttribute(colours, 3));
  geometry.setIndex(new THREE.BufferAttribute(faces, 1));
  const mesh = new THREE.Mesh(geometry, new THREE.MeshLambertMaterial({ vertexColors: true, side: THREE.DoubleSide }));
  scene.add(mesh);
  scene.add(new THREE.HemisphereLight(0xffffff, 0x6c7463, 2));
  const sun = new THREE.DirectionalLight(0xffffff, 2);
  sun.position.set(-3000, 7000, -4000);
  scene.add(sun);
  const target = new THREE.Vector3(0, 0, 0);
  let radius = 10500,
    yaw = 0,
    pitch = 0.72,
    drag = null;
  function render() {
    camera.position.set(
      target.x + radius * Math.cos(pitch) * Math.sin(yaw),
      target.y + radius * Math.sin(pitch),
      target.z + radius * Math.cos(pitch) * Math.cos(yaw)
    );
    camera.lookAt(target);
    renderer.render(scene, camera);
    $('landscape-state').textContent =
      `${surfaceMode === 'ground' ? 'Underlying ground' : '1900 surfaces'} · ${scale}× vertical scale · ${meta.landAreaKm2.toFixed(2)} km² land · ${colourMode === 'height' ? 'elevation colours' : 'evidence colours'}`;
    window.lowerLeaLandscapeReview = {
      ready: true,
      scale,
      colourMode,
      surfaceMode,
      observationsVisible: marks.visible,
      triangleCount: faces.length / 3 + (structures.visible ? structureMeta.triangleCount : 0),
      groundTriangleCount: faces.length / 3,
      structureTriangleCount: structureMeta.triangleCount,
      structuresVisible: structures.visible,
      landAreaKm2: meta.landAreaKm2,
      renderedTriangles: renderer.info.render.triangles,
      target: target.toArray(),
      radius,
    };
  }
  function resize() {
    const w = frame.clientWidth,
      h = frame.clientHeight;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    render();
  }
  function whole() {
    target.set(0, 0, 0);
    radius = 10500;
    yaw = 0;
    pitch = 0.72;
    render();
  }
  $('landscape-whole').onclick = whole;
  $('landscape-north').onclick = () => {
    target.set(537500 - cx, 0, cn - 185900);
    radius = 3500;
    render();
  };
  $('landscape-marsh').onclick = () => {
    target.set(537810 - cx, 0, cn - 184310);
    radius = 1000;
    render();
  };
  $('landscape-pudding-city').onclick = () => {
    target.set(537675 - cx, 0, cn - 184140);
    radius = 1000;
    render();
  };
  $('landscape-south').onclick = () => {
    target.set(538000 - cx, 0, cn - 181400);
    radius = 4000;
    render();
  };
  $('landscape-mill-meads').onclick = () => {
    target.set(538700 - cx, 0, cn - 183050);
    radius = 2200;
    render();
  };
  $('landscape-plaistow').onclick = () => {
    target.set(540050 - cx, 0, cn - 181950);
    radius = 3300;
    render();
  };
  $('landscape-observations').onchange = () => {
    marks.visible = $('landscape-observations').checked;
    updateMesh();
    render();
  };
  $('landscape-surface').onchange = () => {
    surfaceMode = $('landscape-surface').value;
    heights = surfaceMode === 'ground' ? groundHeights : surfaceHeights;
    kinds = surfaceMode === 'ground' ? groundKinds : surfaceKinds;
    updateMesh();
    render();
  };
  $('landscape-scale').onchange = () => {
    scale = Number($('landscape-scale').value);
    updateMesh();
    render();
  };
  $('landscape-colour').onchange = () => {
    colourMode = $('landscape-colour').value;
    updateMesh();
    render();
  };
  const canvas = renderer.domElement;
  canvas.addEventListener('pointerdown', (e) => {
    drag = { x: e.clientX, y: e.clientY, startX: e.clientX, startY: e.clientY, moved: false };
    canvas.setPointerCapture(e.pointerId);
  });
  canvas.addEventListener('pointermove', (e) => {
    if (!drag) return;
    const dx = e.clientX - drag.x,
      dy = e.clientY - drag.y;
    drag.moved ||= Math.hypot(e.clientX - drag.startX, e.clientY - drag.startY) > 4;
    yaw -= dx * 0.005;
    pitch = THREE.MathUtils.clamp(pitch + dy * 0.004, 0.12, 1.5);
    drag.x = e.clientX;
    drag.y = e.clientY;
    render();
  });
  canvas.addEventListener('pointerup', (e) => {
    if (drag && !drag.moved) {
      const rect = canvas.getBoundingClientRect(),
        ray = new THREE.Raycaster();
      ray.setFromCamera(
        new THREE.Vector2(
          ((e.clientX - rect.left) / rect.width) * 2 - 1,
          1 - ((e.clientY - rect.top) / rect.height) * 2
        ),
        camera
      );
      ray.params.Points.threshold = 10;
      const pointHit = marks.visible ? ray.intersectObject(marks)[0] : null;
      if (pointHit) {
        const r = observations[pointHit.index];
        $('landscape-inspect').textContent =
          `${r.id} · ${r.family}, ${r.valueFeet} ft (${r.heightODNMetres.toFixed(2)} m provisional ODN) · ${r.usedInMappedLayer ? 'used in a mapped surface fit' : 'not yet matched to a mapped surface'}. ${r.notes}`;
        drag = null;
        return;
      }
      const hit = ray.intersectObjects(structures.visible ? [structures, mesh] : [mesh])[0];
      if (hit?.object === structures) {
        const vertex = hit.faceIndex * 3;
        const feature = meta.continuousStructures.features.find(
          (f) => vertex >= f.vertexStart && vertex < f.vertexStart + f.vertexCount
        );
        $('landscape-inspect').textContent =
          `${feature?.name || 'Continuous structure'} · ${(hit.point.y / scale).toFixed(2)} m provisional ODN. ${feature?.method || ''}`;
        drag = null;
        return;
      }
      if (hit) {
        const east = hit.point.x + cx,
          north = cn - hit.point.z,
          col = Math.floor((east - e0) / step),
          row = Math.floor((n1 - north) / step),
          i = row * meta.width + col;
        $('landscape-inspect').textContent =
          `E ${east.toFixed(0)}, N ${north.toFixed(0)} · displayed surface ${(hit.point.y / scale).toFixed(2)} m provisional ODN. Nearest grid cell: ${meta.kindLegend[kinds[i]]}.`;
      } else
        $('landscape-inspect').textContent =
          'No ground surface here: outside the mesh, missing coverage, or a water/structure exclusion.';
    }
    drag = null;
  });
  canvas.addEventListener('pointercancel', () => (drag = null));
  canvas.addEventListener(
    'wheel',
    (e) => {
      e.preventDefault();
      radius = THREE.MathUtils.clamp(radius * (e.deltaY > 0 ? 1.1 : 1 / 1.1), 300, 20000);
      render();
    },
    { passive: false }
  );
  canvas.addEventListener('keydown', (e) => {
    if (!['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', '+', '=', '-', 'Home'].includes(e.key)) return;
    e.preventDefault();
    if (e.key === 'Home') {
      whole();
      return;
    }
    if (e.key === 'ArrowLeft') yaw -= 0.1;
    if (e.key === 'ArrowRight') yaw += 0.1;
    if (e.key === 'ArrowUp') pitch = Math.min(1.5, pitch + 0.08);
    if (e.key === 'ArrowDown') pitch = Math.max(0.12, pitch - 0.08);
    if (['+', '='].includes(e.key)) radius = Math.max(300, radius / 1.15);
    if (e.key === '-') radius = Math.min(20000, radius * 1.15);
    render();
  });
  $('landscape-summary').textContent =
    `${meta.landAreaKm2.toFixed(2)} km² of modelled land. The regional marsh base uses ${meta.regionalMarshBaseline.acceptedEarlyProxies} selected early low-lane and ground-margin readings across ${meta.regionalMarshBaseline.fullWeightAreaKm2.toFixed(2)} km², refined by later marsh observations. Mapped streets, yards, banks and railway/sewer formations have separate surface estimates. Switch to Underlying ground to compare. Beyond the marsh envelope, the earlier historical interpolation and provisional modern-derived relief remain. Narrow banks, railways and the full sewer crest use a separate continuous mesh with ${structureMeta.maximumShoreSegmentMetres} m edge sampling. The broad ground display is ${meta.displayMesh.spacingMetres} m; the working grid is ${step} m.`;
  updateMesh();
  new ResizeObserver(resize).observe(frame);
  resize();
  const area = new URLSearchParams(location.search).get('area');
  if (['pudding-city', 'mill-meads', 'plaistow'].includes(area)) $('landscape-' + area).click();
} catch (error) {
  $('landscape-state').textContent = `Landscape could not load: ${error.message}`;
  $('landscape-state').classList.add('error');
  throw error;
}
