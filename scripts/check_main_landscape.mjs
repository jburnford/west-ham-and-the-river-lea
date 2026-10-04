// Verify the actual main-scene integration against all generated asset dimensions.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import * as THREE from 'three';
import { createGroundSampler } from '../docs/lib/ground-sampler.js';
import { box as libBox } from '../docs/lib/geometry.js';
import { infrastructure } from '../docs/infrastructure.js';
import { loadHistoricElevation, applyHistoricElevation } from '../docs/historic-elevation.js';
import { loadRiverNetwork } from '../docs/river-network.js';
import { loadRiverSystem, applyRiverSystem } from '../docs/river-system.js';
import { loadMainLandscape, applyMainLandscape } from '../docs/main-landscape.js';
const load = async (url, type = 'json') => {
  const b = readFileSync(new URL('../docs/' + url.replace(/^\.\//, ''), import.meta.url));
  return type === 'json' ? JSON.parse(b) : b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength);
};
globalThis.location = { search: '?terrainEpoch=baseline' };
assert.equal(await loadMainLandscape(load), null);
globalThis.location.search = '?mainLandscape=baseline';
assert.equal(await loadMainLandscape(load), null);
globalThis.location.search = '';
const data = await load('./data/ground-plan.json');
for (const [key, file] of Object.entries({
  terrain: 'river-terrain',
  infrastructure: 'infrastructure',
  factoryBuildings: 'factory-buildings',
  highStreetFrontages: 'high-street-frontages',
  factoryYards: 'factory-yards',
  housingDetail: 'housing-detail',
  stationPlan: 'abbey-station-plan',
}))
  data[key] = await load(`./data/${file}.json`);
data.terrain.levels = new Float32Array(await load('./data/' + data.terrain.heightFile, 'buffer'));
data.riverNetwork = await loadRiverNetwork(load);
data.riverSystem = await loadRiverSystem(load);
data.elevation = await loadHistoricElevation(load, '1900');
applyHistoricElevation(data);
applyRiverSystem(data);
const rails = JSON.stringify(
    data.infrastructure.railways.map((r) => ({ stations: r.stations, route: r.route, bridges: r.bridges }))
  ),
  sewer = JSON.stringify(data.neighbourhood.sewer);
const oldXYZ = data.riverSystem.positions.slice(),
  oldCore = data.terrain.levels.slice();
const properties = new Uint8Array(await load('./data/' + data.terrain.propertyFile, 'buffer'));
const shapes = JSON.stringify(
  data.factoryBuildings.buildings.map((b) => [b.height, b.width, b.depth, b.renderPolygons])
);
const landscape = await loadMainLandscape(load);
applyMainLandscape(data, landscape);
assert(data.mainLandscape.review.active);
assert(data.mainLandscape.review.seatedObjects > 500);
assert.equal(
  JSON.stringify(
    data.infrastructure.railways.map((r) => ({ stations: r.stations, route: r.route, bridges: r.bridges }))
  ),
  rails
);
assert.equal(JSON.stringify(data.neighbourhood.sewer), sewer);
assert.equal(
  JSON.stringify(data.factoryBuildings.buildings.map((b) => [b.height, b.width, b.depth, b.renderPolygons])),
  shapes
);
for (let i = 0; i < oldXYZ.length; i += 3) {
  assert.equal(data.riverSystem.positions[i], oldXYZ[i]);
  assert.equal(data.riverSystem.positions[i + 2], oldXYZ[i + 2]);
}
assert(oldCore.some((y, i) => Math.abs(y - data.terrain.levels[i]) > 0.1));
let mud = 0;
for (let i = 0; i < oldCore.length; i++)
  if (properties[i * 4 + 3] > 200 && properties[i * 4 + 2] < 80) {
    assert(Math.abs(oldCore[i] - data.terrain.levels[i]) < 1e-5);
    mud++;
  }
assert(mud > 10000, 'Exposed tidal mud must retain its existing channel section');
assert.equal(landscape.grids.groundMesh.length, landscape.meta.groundMeshVertices * 3);
assert.equal(landscape.grids.extension.length, data.elevation.grids.extension.length / 3);
for (const p of landscape.meta.probes) {
  const [x, z] = p.scenePosition;
  assert(landscape.weight(x, z) > 0.99);
  assert(Math.abs(landscape.level(x, z) - p.groundSceneY) < 0.15, p.name);
}
const p = landscape.meta.probes;
assert(Math.abs(p[0].groundSceneY - p[1].groundSceneY) < 0.5, 'Pudding–City marsh must not become an isolated mound');
assert(p[0].groundSceneY > p[2].groundSceneY && p[2].groundSceneY > p[3].groundSceneY, 'Regional marsh progression');
assert.equal(landscape.level(1e6, 1e6, 7), 7);
// Road bridges and road corridors (roadBridgeClearance in build_main_landscape.py). No landscape vertex inside a
// road-bridge span footprint (between the drawn low-water edges under the deck, out to 2 m beyond each deck edge)
// stands above the water edge, except preserved tidal mud in the core tile, the surveyed channel bed asserted
// unchanged above (counted separately). No drawn ground stands more than 0.05 m above the drawn street, footway or path
// surface anywhere: docs/infrastructure.js lays each road triangle on the ground under its vertices, so ground can
// only show through between them.
const clearance = landscape.meta.roadBridgeClearance;
assert(clearance, 'Road-bridge clearance record missing');
assert.deepEqual(
  Object.keys(clearance.footprints).sort(),
  data.infrastructure.roadBridges.map((b) => b.id).sort(),
  'Every road bridge has a span footprint'
);
const inRing = (x, z, ring) => {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, zi] = ring[i],
      [xj, zj] = ring[j];
    if (zi > z !== zj > z && x < ((xj - xi) * (z - zi)) / (zj - zi) + xi) inside = !inside;
  }
  return inside;
};
const coreXYZ = new Float32Array(data.terrain.levels.length * 3),
  coreMud = new Uint8Array(data.terrain.levels.length);
for (let j = 0; j < data.terrain.height; j++)
  for (let i = 0; i < data.terrain.width; i++) {
    const k = j * data.terrain.width + i;
    coreMud[k] = properties[k * 4 + 3] > 200 && properties[k * 4 + 2] < 80 ? 1 : 0;
    coreXYZ.set(
      [
        data.terrain.bounds[0] + i * data.terrain.step,
        data.terrain.levels[k],
        data.terrain.bounds[1] + j * data.terrain.step,
      ],
      k * 3
    );
  }
const vertexSets = {
  core: coreXYZ,
  network: data.riverNetwork.positions,
  system: data.riverSystem.positions,
  extension: data.elevation.grids.extension,
  groundMesh: landscape.grids.groundMesh,
};
const spanReport = {};
for (const [id, polygons] of Object.entries(clearance.footprints)) {
  const all = polygons.flatMap((p) => p[0]),
    bx = [Math.min(...all.map((p) => p[0])), Math.max(...all.map((p) => p[0]))],
    bz = [Math.min(...all.map((p) => p[1])), Math.max(...all.map((p) => p[1]))];
  let vertices = 0,
    highest = -Infinity,
    mudVertices = 0,
    highestMud = -Infinity;
  for (const [key, positions] of Object.entries(vertexSets))
    for (let i = 0; i < positions.length; i += 3) {
      const x = positions[i],
        z = positions[i + 2];
      if (x < bx[0] || x > bx[1] || z < bz[0] || z > bz[1]) continue;
      if (!polygons.some((p) => inRing(x, z, p[0]) && !p.slice(1).some((h) => inRing(x, z, h)))) continue;
      if (key === 'core' && coreMud[i / 3]) {
        mudVertices++;
        highestMud = Math.max(highestMud, positions[i + 1]);
        continue;
      }
      vertices++;
      highest = Math.max(highest, positions[i + 1]);
    }
  spanReport[id] = { vertices, highest: +highest.toFixed(3), mudVertices, highestMud: +highestMud.toFixed(3) };
  assert(vertices + mudVertices > 0, `${id}: no landscape vertex in its span footprint`);
  assert(
    highest <= clearance.waterEdge + 1e-3,
    `${id}: ground ${highest.toFixed(2)} m in the span, above the water edge`
  );
}
// The drawn road surface, built by the real module (railways are not needed here).
data.drawnGround = createGroundSampler([
  { positions: data.elevation.grids.extension },
  { positions: landscape.grids.groundMesh },
  { positions: data.riverNetwork.positions, indices: data.riverNetwork.indices },
  { positions: data.riverSystem.positions, indices: data.riverSystem.indices },
]);
const tile = data.terrain,
  [tx0, tz0, tx1, tz1] = tile.bounds;
function drawnLevel(x, z) {
  if (x < tx0 || x > tx1 || z < tz0 || z > tz1) {
    const drawn = data.drawnGround.sample(x, z);
    if (drawn !== null && drawn !== undefined) return drawn;
    if (data.mainLandscape.weight(x, z) > 0) return data.mainLandscape.level(x, z);
    if (data.elevation?.weight(x, z) > 0) return data.elevation.level(x, z);
    return data.riverNetwork.marshLevel(x, z);
  }
  const fx = Math.max(0, Math.min(tile.width - 1.001, (x - tx0) / tile.step)),
    fz = Math.max(0, Math.min(tile.height - 1.001, (z - tz0) / tile.step));
  const i = Math.floor(fx),
    j = Math.floor(fz),
    u = fx - i,
    v = fz - j,
    at = (a, b) => tile.levels[b * tile.width + a];
  return (at(i, j) * (1 - u) + at(i + 1, j) * u) * (1 - v) + (at(i, j + 1) * (1 - u) + at(i + 1, j + 1) * u) * v;
}
const canvasContext = new Proxy({}, { get: () => () => undefined, set: () => true });
globalThis.document = { createElement: () => ({ width: 0, height: 0, getContext: () => canvasContext }) };
const roadScene = new THREE.Scene();
const plainMaterial = () => new THREE.MeshStandardMaterial();
infrastructure({
  THREE,
  scene: roadScene,
  materials: {
    stone: plainMaterial(),
    ground: plainMaterial(),
    iron: plainMaterial(),
    wood: plainMaterial(),
    brick: plainMaterial(),
  },
  data: { ...data, infrastructure: { ...data.infrastructure, railways: [] } },
  box: (parent, ...args) => libBox(THREE, parent, ...args),
  level: drawnLevel,
});
roadScene.updateMatrixWorld(true);
// Carriageways carry the generated paving texture; footways and paths have their own colours.
const surfacePositions = { carriageway: [], footway: [], path: [] };
roadScene.traverse((o) => {
  if (!o.isMesh) return;
  const colour = o.material.color.getHexString(),
    kind = o.material.map ? 'carriageway' : colour === 'aaa392' ? 'footway' : colour === '9b9078' ? 'path' : null;
  if (!kind) return;
  const g = (o.geometry.index ? o.geometry.toNonIndexed() : o.geometry.clone()).applyMatrix4(o.matrixWorld);
  for (const v of g.getAttribute('position').array) surfacePositions[kind].push(v);
});
const roadTriangles = {
  carriageway: Object.values(data.infrastructure.roadSurfaces).flat(),
  footway: data.infrastructure.shoulderTriangles,
  path: data.infrastructure.pathTriangles,
};
// A footway can stand above the carriageway edge beside it (each follows the ground under its own vertices), so
// the ground is compared with the highest drawn street, footway or path surface at each sample.
const surfaceSamplers = Object.values(surfacePositions).map((positions) =>
  createGroundSampler([{ positions: new Float32Array(positions) }], { cellSize: 4 })
);
const drawnRoad = (x, z) => {
  let top = null;
  for (const sampler of surfaceSamplers) {
    const y = sampler.sample(x, z);
    if (y !== null && y !== undefined && (top === null || y > top)) top = y;
  }
  return top;
};
// Preserved tidal mud in the core tile keeps its surveyed section (asserted above), so a road edge over it is not
// counted; samples whose core cell touches mud are reported separately.
const onMud = (x, z) => {
  if (x < tx0 || x > tx1 || z < tz0 || z > tz1) return false;
  const i = Math.min(tile.width - 2, Math.floor((x - tx0) / tile.step)),
    j = Math.min(tile.height - 2, Math.floor((z - tz0) / tile.step));
  return [0, 1].some((a) => [0, 1].some((b) => coreMud[(j + b) * tile.width + i + a]));
};
const corridorReport = {};
for (const [kind, triangles] of Object.entries(roadTriangles)) {
  let samples = 0,
    mudSamples = 0,
    worst = { by: -Infinity };
  const offending = [];
  for (const [a, b, c] of triangles) {
    const edge = Math.max(
      Math.hypot(b[0] - a[0], b[1] - a[1]),
      Math.hypot(c[0] - b[0], c[1] - b[1]),
      Math.hypot(a[0] - c[0], a[1] - c[1])
    );
    const n = Math.max(1, Math.ceil(edge));
    for (let i = 0; i <= n; i++)
      for (let j = 0; j <= n - i; j++) {
        const u = i / n,
          v = j / n,
          x = a[0] * (1 - u - v) + b[0] * u + c[0] * v,
          z = a[1] * (1 - u - v) + b[1] * u + c[1] * v,
          road = drawnRoad(x, z);
        if (road === null) continue; // a hole in the road mesh
        if (onMud(x, z)) {
          mudSamples++;
          continue;
        }
        samples++;
        const by = drawnLevel(x, z) - road;
        if (by > worst.by) worst = { by: +by.toFixed(3), at: [+x.toFixed(2), +z.toFixed(2)] };
        if (by > 0.05) offending.push([x, z]);
      }
  }
  corridorReport[kind] = { samples, offending: offending.length, worst, onPreservedMud: mudSamples };
  assert(samples > 1000, `${kind}: road surface not sampled`);
  assert.equal(
    offending.length,
    0,
    `${kind}: ground stands more than 0.05 m above the road, worst ${JSON.stringify(worst)}`
  );
}
console.log(
  JSON.stringify(
    {
      status: 'PASS',
      seatedObjects: landscape.review.seatedObjects,
      roadBridgeSpans: spanReport,
      roadCorridorSamples: corridorReport,
      probes: p,
      checks: [
        'default main integration active',
        'baseline opt-outs',
        'native topology',
        'exposed tidal mud preserved',
        'building dimensions',
        'rail grades and bridges',
        'sewer route and height',
        'regional marsh progression',
        'extension dimensions',
        'outer ground unchanged',
        'no ground in a road-bridge span above the water edge',
        'no ground above a drawn road surface',
      ],
    },
    null,
    2
  )
);
