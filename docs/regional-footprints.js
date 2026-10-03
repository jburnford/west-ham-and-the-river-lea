// Flat historical plans. No building heights are inferred from the source polygons.
export function regionalFootprints({
  THREE,
  scene,
  data,
  level,
  landMaterial,
  existingGround,
  regionalGround,
  landscapeActive = false,
  lite,
  render,
}) {
  const group = new THREE.Group();
  group.name = 'Regional historical building plans';
  scene.add(group);
  const asset = (file) =>
    window.sceneAssetUrl?.(`./data/regional-footprints/${file}`) || `./data/regional-footprints/${file}`;
  const loader = new THREE.TextureLoader();
  const stats = {
    sourceFootprints: data.sourceFootprints,
    tiles: data.tiles.length,
    enabled: true,
    overviewReady: false,
    loadedDetailTiles: 0,
    loading: 0,
    failedTiles: [],
    ground: landscapeActive ? 'historical marsh surface with estimated premises' : 'provisional flat plan',
  };
  const setupTexture = (texture) => {
    texture.colorSpace = THREE.SRGBColorSpace;
    texture.anisotropy = 2;
    return texture;
  };
  const overview = setupTexture(
    loader.load(asset(data.overview), () => {
      stats.overviewReady = true;
      render();
    })
  );
  const material = new THREE.MeshBasicMaterial({
    map: overview,
    transparent: true,
    alphaTest: 0.08,
    depthWrite: false,
    side: THREE.DoubleSide,
    polygonOffset: true,
    polygonOffsetFactor: -1,
  });
  const [x0, z0, x1, z1] = data.bounds;
  // A neutral map ground extends the existing scene without claiming LiDAR calibration.
  // Extend only outside the original ground envelope. A blanket plane here
  // would cover submerged mud and show green through transparent river water.
  const core = existingGround
    .flat(2)
    .reduce(
      (bounds, [x, z]) => [
        Math.min(bounds[0], x),
        Math.min(bounds[1], z),
        Math.max(bounds[2], x),
        Math.max(bounds[3], z),
      ],
      [Infinity, Infinity, -Infinity, -Infinity]
    );
  const outline = new THREE.Shape(
    [
      [-25000, -25000],
      [25000, -25000],
      [25000, 25000],
      [-25000, 25000],
    ].map(([x, z]) => new THREE.Vector2(x, -z))
  );
  outline.holes.push(
    new THREE.Path(
      [
        [core[0], core[1]],
        [core[2], core[1]],
        [core[2], core[3]],
        [core[0], core[3]],
      ].map(([x, z]) => new THREE.Vector2(x, -z))
    )
  );
  const groundShapes = regionalGround?.map((rings) => {
    const shape = new THREE.Shape(rings[0].map(([x, z]) => new THREE.Vector2(x, -z)));
    for (const ring of rings.slice(1)) shape.holes.push(new THREE.Path(ring.map(([x, z]) => new THREE.Vector2(x, -z))));
    return shape;
  });
  const groundGeometry = new THREE.ShapeGeometry(groundShapes || outline);
  groundGeometry.rotateX(-Math.PI / 2);
  groundGeometry.translate(0, -0.1, 0);
  const ground = new THREE.Mesh(groundGeometry, landMaterial);
  ground.name = 'Provisional regional ground';
  scene.add(ground);
  const waterTexture = setupTexture(loader.load(asset(data.waterContext), () => render()));
  const waterOutline = new THREE.Shape(
    [
      [x0, z0],
      [x1, z0],
      [x1, z1],
      [x0, z1],
    ].map(([x, z]) => new THREE.Vector2(x, -z))
  );
  waterOutline.holes.push(outline.holes[0]);
  const waterGeometry = new THREE.ShapeGeometry(waterOutline);
  waterGeometry.rotateX(-Math.PI / 2);
  waterGeometry.translate(0, -0.085, 0);
  const waterPositions = waterGeometry.attributes.position,
    waterUV = waterGeometry.attributes.uv;
  for (let i = 0; i < waterPositions.count; i++)
    waterUV.setXY(i, (waterPositions.getX(i) - x0) / (x1 - x0), 1 - (waterPositions.getZ(i) - z0) / (z1 - z0));
  const water = new THREE.Mesh(
    waterGeometry,
    new THREE.MeshBasicMaterial({ map: waterTexture, transparent: true, alphaTest: 0.1, depthWrite: false })
  );
  water.name = 'Regional water plan';
  scene.add(water);
  const records = data.tiles.map((tile) => {
    const [a, b, c, d] = tile.bounds,
      segments = 32;
    const left = Math.max(a, x0),
      right = Math.min(c, x1),
      top = Math.max(b, z0),
      bottom = Math.min(d, z1);
    const geometry = new THREE.PlaneGeometry(right - left, bottom - top, segments, segments);
    geometry.rotateX(-Math.PI / 2);
    geometry.translate((left + right) / 2, 0, (top + bottom) / 2);
    const positions = geometry.attributes.position,
      coarseUV = new Float32Array(geometry.attributes.uv.array.length);
    const detailUV = geometry.attributes.uv.array.slice();
    for (let i = 0; i < positions.count; i++) {
      const x = positions.getX(i),
        z = positions.getZ(i);
      positions.setY(i, landscapeActive ? level(x, z) + 0.025 : Math.max(-0.06, level(x, z) + 0.025));
      detailUV[i * 2] = (x - a) / (c - a);
      detailUV[i * 2 + 1] = 1 - (z - b) / (d - b);
      coarseUV[i * 2] = (x - x0) / (x1 - x0);
      coarseUV[i * 2 + 1] = 1 - (z - z0) / (z1 - z0);
    }
    geometry.setAttribute('uv', new THREE.BufferAttribute(coarseUV.slice(), 2));
    geometry.computeBoundingSphere();
    const mesh = new THREE.Mesh(geometry, material);
    mesh.name = `Building plan ${tile.id}`;
    group.add(mesh);
    return {
      ...tile,
      mesh,
      coarseUV,
      detailUV,
      texture: null,
      loading: false,
      failed: false,
      x: (a + c) / 2,
      z: (b + d) / 2,
      distance: Infinity,
    };
  });
  let wanted = new Set(),
    active = 0,
    queue = [],
    disposed = false;
  const count = () => {
    stats.loadedDetailTiles = records.filter((r) => r.texture).length;
    stats.loading = active;
  };
  function restore(record) {
    if (!record.texture) return;
    record.texture.dispose();
    record.mesh.material.dispose();
    record.texture = null;
    record.mesh.material = material;
    record.mesh.geometry.attributes.uv.array.set(record.coarseUV);
    record.mesh.geometry.attributes.uv.needsUpdate = true;
  }
  function pump() {
    while (!disposed && active < 2 && queue.length) {
      const r = queue.shift();
      if (r.loading || r.texture || r.failed || !wanted.has(r.id)) continue;
      active++;
      r.loading = true;
      count();
      loader.load(
        asset(r.file),
        (texture) => {
          active--;
          r.loading = false;
          if (disposed || !wanted.has(r.id)) texture.dispose();
          else {
            r.texture = setupTexture(texture);
            r.mesh.material = material.clone();
            r.mesh.material.map = r.texture;
            r.mesh.geometry.attributes.uv.array.set(r.detailUV);
            r.mesh.geometry.attributes.uv.needsUpdate = true;
          }
          count();
          pump();
          render();
        },
        undefined,
        () => {
          active--;
          r.loading = false;
          r.failed = true;
          stats.failedTiles.push(r.id);
          count();
          pump();
          render();
        }
      );
    }
  }
  let lastKey = '';
  return {
    stats,
    setVisible(value) {
      stats.enabled = Boolean(value);
      group.visible = stats.enabled;
      lastKey = '';
      render();
    },
    update(camera) {
      const p = camera.position,
        key = `${Math.floor(p.x / 200)},${Math.floor(p.z / 200)},${p.y > 750},${stats.enabled}`;
      if (key === lastKey) return;
      lastKey = key;
      for (const r of records) r.distance = Math.hypot(r.x - p.x, r.z - p.z);
      const ordered = [...records].sort((a, b) => a.distance - b.distance);
      const close = stats.enabled && p.y <= 750 ? ordered.filter((r) => r.distance < 1600).slice(0, lite ? 6 : 12) : [];
      wanted = new Set(close.map((r) => r.id));
      // Keep only a small texture cache; the overview always fills unloaded areas.
      for (const r of ordered.slice(lite ? 8 : 20)) restore(r);
      queue = close.filter((r) => !r.texture && !r.loading && !r.failed);
      count();
      pump();
    },
    dispose() {
      disposed = true;
      for (const r of records) {
        restore(r);
        r.mesh.geometry.dispose();
      }
      overview.dispose();
      waterTexture.dispose();
      material.dispose();
      group.removeFromParent();
    },
  };
}
