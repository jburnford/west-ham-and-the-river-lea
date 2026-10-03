import { gardens } from './gardens.js';
import { createRandom } from './lib/prng.js';
// Inferred landform and working surfaces, based on Figure 2.4.
// Original geometry only; source photograph is not used as a surface texture.
export async function loadTerrain(load) {
  // Optional loader lets the page report download progress; default keeps plain fetch.
  const json = load
    ? (url) => load(url, 'json')
    : async (url) => {
        const r = await fetch(url);
        if (!r.ok) throw new Error('River terrain metadata unavailable');
        return r.json();
      };
  const buffer = load
    ? (url) => load(url, 'buffer')
    : async (url) => {
        const r = await fetch(url);
        if (!r.ok) throw new Error(`Terrain asset unavailable: ${url}`);
        return r.arrayBuffer();
      };
  const terrain = await json('./data/river-terrain.json');
  const files = await Promise.all(
    [terrain.heightFile, terrain.propertyFile, terrain.landcoverFile].map((file) => buffer(`./data/${file}`))
  );
  terrain.levels = new Float32Array(files[0]);
  terrain.properties = new Uint8Array(files[1]);
  terrain.landcover = new Uint8Array(files[2]);
  if (
    terrain.levels.length !== terrain.width * terrain.height ||
    terrain.properties.length !== terrain.levels.length * 4 ||
    terrain.landcover.length !== terrain.levels.length
  )
    throw new Error('Terrain dimensions do not match');
  terrain.mudImage = new Image();
  terrain.mudImage.src =
    window.sceneAssetUrl?.('./assets/textures/tidal-mud-v1.png') || './assets/textures/tidal-mud-v1.png';
  await terrain.mudImage.decode();
  return terrain;
}

export function terrainDetails({ THREE, scene, materials: m, data, box, cylinder, beam, random, density = 1 }) {
  const t = data.terrain,
    [x0, z0, x1, z1] = t.bounds;
  function level(x, z) {
    if (x < x0 || x > x1 || z < z0 || z > z1) {
      if (data.mainLandscape?.weight(x, z) > 0) return data.mainLandscape.level(x, z);
      if (data.elevation?.weight(x, z) > 0) return data.elevation.level(x, z);
      return data.riverNetwork.marshLevel(x, z);
    }
    const fx = Math.max(0, Math.min(t.width - 1.001, (x - x0) / t.step)),
      fz = Math.max(0, Math.min(t.height - 1.001, (z - z0) / t.step));
    const i = Math.floor(fx),
      j = Math.floor(fz),
      u = fx - i,
      v = fz - j,
      at = (a, b) => t.levels[b * t.width + a];
    return (at(i, j) * (1 - u) + at(i + 1, j) * u) * (1 - v) + (at(i, j + 1) * (1 - u) + at(i + 1, j + 1) * u) * v;
  }
  const terrainMaterial = m.land;
  const position = new Float32Array(t.width * t.height * 3),
    uv = new Float32Array(t.width * t.height * 2);
  for (let z = 0; z < t.height; z++)
    for (let x = 0; x < t.width; x++) {
      const i = z * t.width + x,
        wx = x0 + x * t.step,
        wz = z0 + z * t.step;
      position.set([wx, t.levels[i], wz], i * 3);
      uv.set([wx, wz], i * 2);
    }
  const indices = new Uint32Array((t.width - 1) * (t.height - 1) * 6);
  let k = 0;
  for (let z = 0; z < t.height - 1; z++)
    for (let x = 0; x < t.width - 1; x++) {
      const a = z * t.width + x,
        b = a + 1,
        c = a + t.width,
        d = c + 1;
      indices.set((x + z) % 2 ? [a, c, d, a, d, b] : [a, c, b, b, c, d], k);
      k += 6;
    }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(position, 3));
  geometry.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
  geometry.setIndex(new THREE.BufferAttribute(indices, 1));
  geometry.computeVertexNormals();
  const sediment = new Uint8Array(t.width * t.height),
    cover = new Uint8Array(t.width * t.height * 2);
  for (let i = 0; i < sediment.length; i++) {
    sediment[i] = t.properties[i * 4 + 3];
    cover[i * 2] = t.landcover[i] === 1 ? 255 : 0;
    cover[i * 2 + 1] = t.landcover[i] === 2 ? 255 : 0;
  }
  geometry.setAttribute('sediment', new THREE.BufferAttribute(sediment, 1, true));
  geometry.setAttribute('landCover', new THREE.BufferAttribute(cover, 2, true));
  const terrainMesh = new THREE.Mesh(geometry, terrainMaterial);
  terrainMesh.userData.keepIndexed = true;
  terrainMesh.receiveShadow = true;
  terrainMesh.castShadow = false;
  scene.add(terrainMesh);

  // Torn clods and small ridges catch light above the lower-frequency ground mesh.
  // They are flattened mud, not scattered large stones or invented refuse.
  const clod = m.bed.clone();
  clod.color.set('#555448');
  clod.bumpScale = 0.08;
  const lumps = Array.from({ length: 9 }, (_, variant) => {
    const geometry = new THREE.IcosahedronGeometry(1, 0),
      p = geometry.getAttribute('position');
    for (let i = 0; i < p.count; i++) {
      const x = p.getX(i),
        y = p.getY(i),
        z = p.getZ(i);
      const scale = 1 + 0.27 * Math.sin(x * 7.3 + y * 14.2 + z * 5.9 + variant * 1.7);
      p.setXYZ(i, x * scale, y * scale, z * scale);
    }
    geometry.computeVertexNormals();
    return geometry;
  });
  let clodCount = 0;
  for (let attempt = 0; attempt < 145000 * density; attempt++) {
    const x = -160 + random() * 205,
      z = -270 + random() * 480;
    const ix = Math.round((x - x0) / t.step),
      iz = Math.round((z - z0) / t.step),
      i = iz * t.width + ix,
      h = level(x, z);
    if (t.properties[i * 4 + 3] < 200 || t.properties[i * 4 + 2] > 80 || h < 0.09 || h > 1.9) continue;
    const radius = 0.025 + Math.pow(random(), 2) * 0.12;
    const mesh = new THREE.Mesh(lumps[clodCount % lumps.length], clod);
    mesh.scale.set(radius * (1 + random()), radius * (0.16 + random() * 0.3), radius * (0.7 + random() * 1.2));
    mesh.position.set(x, h - 0.012, z);
    mesh.rotation.set((random() - 0.5) * 0.3, random() * Math.PI, (random() - 0.5) * 0.3);
    scene.add(mesh);
    clodCount++;
  }

  // A narrow worn crest, occasional retaining timbers and irregular fence posts
  // make the river-right flood bank legible above the lower allotments.
  for (let i = 1; i < t.bankRoute.length; i++) {
    const [ax, az] = t.bankRoute[i - 1],
      [bx, bz] = t.bankRoute[i];
    if (i % 2 === 0) {
      const y = level(bx, bz);
      const post = box(scene, bx, y - 0.12, bz, 0.11, 0.9 + random() * 0.35, 0.1, m.wood);
      post.rotation.z = (random() - 0.5) * 0.13;
      if (i > 2) beam(scene, [ax, level(ax, az) + 0.55, az], [bx, y + 0.55, bz], 0.014, m.iron);
    }
    if (i % 5 === 0 && az < 180) {
      for (let p = 0; p < 4; p++) {
        const x = ax + 2.8,
          z = az + p * 0.8,
          y = level(x, z);
        const stake = box(scene, x, y - 0.45, z, 0.18, 0.8, 0.12, m.wood);
        stake.rotation.z = 0.14;
      }
    }
  }

  const garden = gardens({ THREE, scene, materials: m, data, box, cylinder, level });
  const sheds = garden.sheds;
  // Low mixed grass and coarse weeds on open land; no invented trees or species.
  // Mapped working sites, allotments, roads and exposed sediment remain clear.
  const vegetation = [];
  let vegetationCount = 0;
  const plantRandom = createRandom(902);
  const roadSegments = data.infrastructure.roads.flatMap((r) =>
    r.route.slice(1).map((b, i) => ({ a: r.route[i], b, width: r.width / 2 + 2 }))
  );
  function onRoad(x, z) {
    return roadSegments.some(({ a, b, width }) => {
      const dx = b[0] - a[0],
        dz = b[1] - a[1],
        u = Math.max(0, Math.min(1, ((x - a[0]) * dx + (z - a[1]) * dz) / (dx * dx + dz * dz)));
      return Math.hypot(x - a[0] - u * dx, z - a[1] - u * dz) < width;
    });
  }
  for (let attempt = 0; attempt < 36000 * density; attempt++) {
    const x = x0 + plantRandom() * (x1 - x0),
      z = z0 + plantRandom() * (z1 - z0);
    const ix = Math.round((x - x0) / t.step),
      iz = Math.round((z - z0) / t.step),
      i = iz * t.width + ix;
    if (
      t.landcover[i] !== 0 ||
      t.properties[i * 4 + 3] > 100 ||
      (t.levels[i] < 0.08 && !(data.elevation?.weight(x, z) > 0)) ||
      onRoad(x, z)
    )
      continue;
    const y = level(x, z),
      height = 0.18 + plantRandom() * 0.48;
    for (let blade = 0; blade < 3; blade++) {
      const angle = plantRandom() * Math.PI * 2,
        dx = Math.cos(angle) * 0.065,
        dz = Math.sin(angle) * 0.065;
      const lean = (plantRandom() - 0.5) * 0.22;
      vegetation.push(x - dx, y, z - dz, x + dx, y, z + dz, x + lean, y + height, z + 0.1);
    }
    vegetationCount++;
  }
  const grass = new THREE.MeshStandardMaterial({ color: '#838961', roughness: 1, side: THREE.DoubleSide });
  const grassGeometry = new THREE.BufferGeometry();
  grassGeometry.setAttribute('position', new THREE.Float32BufferAttribute(vegetation, 3));
  grassGeometry.computeVertexNormals();
  scene.add(new THREE.Mesh(grassGeometry, grass));
  return { level, terrainMaterial, clodCount, sheds, vegetationCount, gardenReview: garden.review };
}
