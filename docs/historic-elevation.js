// Dated terrain overlay. Geometry and observations are selected independently;
// an unsupported historical year must never display the 1900 earthworks.
// Bilinear vertex-grid sampling is shared; keep the historical export name for callers.
import { sampleVertexGrid as gridSample } from './lib/grid.js';
export { gridSample };

export async function loadHistoricElevation(
  load,
  requested = new URLSearchParams(location.search).get('terrainEpoch')
) {
  if (requested === 'baseline') return null;
  const catalogue = await load('./data/terrain-epochs.json');
  const epoch = requested || catalogue.activeEpoch,
    entry = catalogue.epochs[epoch];
  if (!entry?.asset)
    throw new Error(`Terrain for ${epoch} needs dated observations and period geometry; it is not available yet.`);
  const meta = await load(`./data/${entry.asset}`);
  if (meta.epoch !== epoch || meta.geometryEpoch !== epoch) throw new Error('Terrain/geometry epoch mismatch');
  const drainage = meta.drainageFile ? await load(`./data/${meta.drainageFile}`) : null;
  if (drainage && drainage.geometryEpoch !== epoch) throw new Error('Drainage/terrain epoch mismatch');
  const keys = ['target', 'weight', 'scene', 'extension'];
  const buffers = await Promise.all(keys.map((key) => load(`./data/${meta.files[key]}`, 'buffer')));
  const grids = Object.fromEntries(keys.map((key, i) => [key, new Float32Array(buffers[i])]));
  for (const key of keys.slice(0, 3))
    if (grids[key].length !== meta.width * meta.height)
      throw new Error('Historic terrain grid dimensions do not match');
  if (grids.extension.length !== meta.extensionVertices * 3)
    throw new Error('Historic terrain extension dimensions do not match');
  if (!keys.every((key) => grids[key].every(Number.isFinite))) throw new Error('Non-finite render terrain');
  if (!grids.weight.every((w) => w >= 0 && w <= 1)) throw new Error('Invalid terrain support weights');
  const contains = (x, z) => x >= meta.bounds[0] && x <= meta.bounds[2] && z >= meta.bounds[1] && z <= meta.bounds[3];
  const weight = (x, z) => (contains(x, z) ? gridSample(grids.weight, meta, x, z) : 0);
  const apply = (x, z, y) => {
    const w = weight(x, z);
    return w ? y + (gridSample(grids.target, meta, x, z) - y) * w : y;
  };
  return {
    meta,
    grids,
    contains,
    weight,
    apply,
    drainage,
    level: (x, z) => (contains(x, z) ? gridSample(grids.scene, meta, x, z) : null),
  };
}

export function applyHistoricElevation(data) {
  const elevation = data.elevation;
  if (!elevation) return;
  const core = data.terrain,
    network = data.riverNetwork;
  const counts = { coreVerticesChanged: 0, networkVerticesChanged: 0 };
  for (let j = 0; j < core.height; j++)
    for (let i = 0; i < core.width; i++) {
      const index = j * core.width + i,
        y = core.levels[index];
      const next = elevation.apply(core.bounds[0] + i * core.step, core.bounds[1] + j * core.step, y);
      if (Math.abs(next - y) > 1e-7) {
        core.levels[index] = next;
        counts.coreVerticesChanged++;
      }
    }
  for (let i = 0; i < network.positions.length; i += 3) {
    const y = network.positions[i + 1],
      next = elevation.apply(network.positions[i], network.positions[i + 2], y);
    if (Math.abs(next - y) > 1e-7) {
      network.positions[i + 1] = next;
      counts.networkVerticesChanged++;
    }
  }
  network.baseGround = elevation.meta.replacementBaseGround;
  elevation.review = {
    epoch: elevation.meta.epoch,
    verticalReference: elevation.meta.verticalReference,
    supportedAreaM2: elevation.meta.supportedAreaM2,
    affectedAreaM2: elevation.meta.affectedAreaM2,
    changeRangeMetres: elevation.meta.changeRangeMetres,
    controls: elevation.meta.controls,
    floodReady: false,
    floodScenarios: elevation.meta.floodScenarios,
    ...counts,
  };
  if (elevation.drainage)
    elevation.review.drainage = {
      ...elevation.drainage.renderedReach,
      sluicesRecorded: elevation.drainage.sluices.length,
      waterTriangles: elevation.drainage.waterTriangles.length,
      tideConnected: false,
      floodReady: false,
    };
}

export function historicGround({ THREE, scene, material, elevation }) {
  if (!elevation) return;
  const positions = elevation.grids.extension,
    geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  const uv = new Float32Array((positions.length / 3) * 2);
  for (let i = 0; i < positions.length / 3; i++) uv.set([positions[i * 3], positions[i * 3 + 2]], i * 2);
  geometry.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
  geometry.computeVertexNormals();
  const mesh = new THREE.Mesh(geometry, material);
  mesh.name = `Historical open ground — ${elevation.meta.epoch}`;
  mesh.receiveShadow = true;
  mesh.castShadow = false;
  scene.add(mesh);
  if (elevation.drainage) {
    const waterGeometry = new THREE.BufferGeometry();
    waterGeometry.setAttribute(
      'position',
      new THREE.Float32BufferAttribute(elevation.drainage.waterTriangles.flat(2), 3)
    );
    waterGeometry.computeVertexNormals();
    // An isolated standing-water assumption, not the tidal reflection plane.
    const waterMaterial = new THREE.MeshStandardMaterial({ color: 0x647d76, roughness: 0.32, metalness: 0.1 });
    const water = new THREE.Mesh(waterGeometry, waterMaterial);
    water.name = 'Plaistow mapped drain — assumed standing water';
    scene.add(water);
  }
}
