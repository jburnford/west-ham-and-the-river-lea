// Road bridges: arches clear the water, nothing stands in the channel but abutment footings and
// river piers, parapets on both sides, and the drawn road surface along every bridge route is
// exactly as it was before the structures were drawn (other modules, the tram rails among them,
// read that surface). Builds the real infrastructure() module, as the tram-rail check does.
//   node scripts/check_road_bridges.mjs                 run the check
//   node scripts/check_road_bridges.mjs --write-sample  print a fresh road-surface sample
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import * as THREE from 'three';
import { loadHistoricElevation, applyHistoricElevation } from '../docs/historic-elevation.js';
import { loadRiverNetwork } from '../docs/river-network.js';
import { loadRiverSystem, applyRiverSystem } from '../docs/river-system.js';
import { loadMainLandscape, applyMainLandscape } from '../docs/main-landscape.js';
import { createGroundSampler } from '../docs/lib/ground-sampler.js';
import { box as libBox } from '../docs/lib/geometry.js';
import { infrastructure } from '../docs/infrastructure.js';
import { bridgeForms, bridgeLayout, bridgeClearance, roadBridges } from '../docs/road-bridges.js';

const load = async (url, type = 'json') => {
  const b = readFileSync(new URL('../docs/' + url.replace(/^\.\//, ''), import.meta.url));
  return type === 'json' ? JSON.parse(b) : b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength);
};
globalThis.location = { search: '' };

// Data assembled in the same order as app.js.
const data = await load('./data/ground-plan.json');
data.terrain = await load('./data/river-terrain.json');
data.terrain.levels = new Float32Array(await load('./data/' + data.terrain.heightFile, 'buffer'));
for (const [key, file] of Object.entries({
  infrastructure: 'infrastructure',
  factoryBuildings: 'factory-buildings',
  highStreetFrontages: 'high-street-frontages',
  factoryYards: 'factory-yards',
  housingDetail: 'housing-detail',
  stationPlan: 'abbey-station-plan',
}))
  data[key] = await load(`./data/${file}.json`);
data.riverNetwork = await loadRiverNetwork(load);
data.elevation = await loadHistoricElevation(load);
applyHistoricElevation(data);
data.riverSystem = await loadRiverSystem(load);
applyRiverSystem(data);
applyMainLandscape(data, await loadMainLandscape(load));
data.drawnGround = createGroundSampler([
  data.elevation && { positions: data.elevation.grids.extension },
  data.mainLandscape && { positions: data.mainLandscape.grids.groundMesh },
  { positions: data.riverNetwork.positions, indices: data.riverNetwork.indices },
  { positions: data.riverSystem.positions, indices: data.riverSystem.indices },
]);
// terrainDetails().level, which app.js hands to infrastructure().
const t = data.terrain,
  [x0, z0, x1, z1] = t.bounds;
function level(x, z) {
  if (x < x0 || x > x1 || z < z0 || z > z1) {
    const drawn = data.drawnGround.sample(x, z);
    if (drawn !== null && drawn !== undefined) return drawn;
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

const canvasContext = new Proxy({}, { get: () => () => undefined, set: () => true });
globalThis.document = { createElement: () => ({ width: 0, height: 0, getContext: () => canvasContext }) };
const scene = new THREE.Scene();
const plain = () => new THREE.MeshStandardMaterial();
const materials = { stone: plain(), ground: plain(), iron: plain(), wood: plain(), brick: plain() };
const review = infrastructure({
  THREE,
  scene,
  materials,
  data: { ...data, infrastructure: { ...data.infrastructure, railways: [] } },
  box: (parent, ...args) => libBox(THREE, parent, ...args),
  level,
});
scene.updateMatrixWorld(true);
const bridges = data.infrastructure.roadBridges;

// The drawn road surface: meshes carrying the generated sett/macadam/cinder texture.
const roadPositions = [];
scene.traverse((o) => {
  if (!o.isMesh || !o.material.map) return;
  const g = (o.geometry.index ? o.geometry.toNonIndexed() : o.geometry.clone()).applyMatrix4(o.matrixWorld);
  for (const v of g.getAttribute('position').array) roadPositions.push(v);
});
const drawnRoad = createGroundSampler([{ positions: new Float32Array(roadPositions) }], { cellSize: 4 });
const frame = (b) => {
  const [a, c] = [b.route[0], b.route.at(-1)],
    length = Math.hypot(c[0] - a[0], c[1] - a[1]);
  return { a, length, ux: (c[0] - a[0]) / length, uz: (c[1] - a[1]) / length };
};
// Stations every metre along the straight chord from 4 m before to 4 m beyond the route, on the
// centreline and on each carriageway side clear of the footways.
function roadSample(b) {
  const { a, length, ux, uz } = frame(b),
    side = Math.max(0, b.width / 2 - 1.6),
    rows = [];
  for (const v of [-side, 0, side]) {
    const row = [];
    for (let s = -4; s <= length + 4; s += 1) {
      const y = drawnRoad.sample(a[0] + ux * s - uz * v, a[1] + uz * s + ux * v);
      row.push(y === null ? null : Math.round(y * 1000) / 1000);
    }
    rows.push(row);
  }
  return rows;
}
if (process.argv.includes('--write-sample')) {
  console.log(JSON.stringify(Object.fromEntries(bridges.map((b) => [b.id, roadSample(b)]))));
  process.exit(0);
}

// Drawn road surface after the T13 road retrace (3 October 2026), from --write-sample: right side, centre, left side.
// Refresh with --write-sample whenever a road or bridge span is deliberately moved.
// prettier-ignore
const BEFORE = {
  'abbey-mill-crossing': [
    [1.974, 1.934, 1.892, 1.845, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.7, 1.828, 1.908, 1.949],
    [1.966, 1.925, 1.883, 1.841, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.811, 1.853, 1.894, 1.935],
    [1.957, 1.915, 1.802, 1.681, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.82, 1.588, 1.698, 1.807, 1.916],
  ],
  'bow-bridge': [
    [3.969, 4.104, 4.207, 4.25, 4.272, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.256, 4.208, 4.139, 4.07],
    [4.019, 4.149, 4.278, 4.408, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.461, 4.337, 4.211, 4.085],
    [4.051, 4.13, 4.209, 4.255, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.82, 4.257, 4.207, 4.141, 4.074],
  ],
  'pegshole-bridge': [
    [2.255, 2.324, 2.393, 2.452, 3.02, 3.02, 3.02, 3.02, 3.02, 3.02, 3.02, 3.02, 3.02, 3.02, 3.02, 3.02, 3.02, 3.02, 3.02, 3.02, 3.02, 3.02, 3.02, 2.454, 2.506, 2.58, 2.602],
    [2.338, 2.452, 2.566, 2.667, 3.02, 3.02, 3.02, 3.02, 3.02, 3.02, 3.02, 3.02, 3.02, 3.02, 3.02, 3.02, 3.02, 3.02, 3.02, 3.02, 3.02, 3.02, 3.02, 2.629, 2.54, 2.473, 2.406],
    [2.387, 2.418, 2.442, 2.463, 3.02, 3.02, 3.02, 3.02, 3.02, 3.02, 3.02, 3.02, 3.02, 3.02, 3.02, 3.02, 3.02, 3.02, 3.02, 3.02, 3.02, 3.02, 3.02, 2.441, 2.392, 2.343, 2.217],
  ],
  'st-thomas-bridge': [
    [2.54, 2.416, 2.217, 2.053, 2.072, 2.62, 2.62, 2.62, 2.62, 2.62, 2.62, 2.62, 2.62, 2.085, 2.353, 2.405, 2.434],
    [2.402, 2.376, 2.349, 2.346, 2.36, 2.62, 2.62, 2.62, 2.62, 2.62, 2.62, 2.62, 2.62, 2.359, 2.343, 2.34, 2.35],
    [2.304, 2.225, 2.124, 2.052, null, 2.62, 2.62, 2.62, 2.62, 2.62, 2.62, 2.62, 2.62, 2.071, 2.051, 2.124, 2.222],
  ],
  'st-michaels-bridge': [
    [2.12, 2.236, 2.356, 2.427, 2.82, 2.82, 2.82, 2.82, 2.82, 2.82, 2.82, 2.82, 2.82, 2.82, 2.82, 2.82, 2.82, 2.82, 2.82, 2.82, 2.258, 2.24, 2.23, 2.22],
    [2.375, 2.45, 2.526, 2.554, 2.82, 2.82, 2.82, 2.82, 2.82, 2.82, 2.82, 2.82, 2.82, 2.82, 2.82, 2.82, 2.82, 2.82, 2.82, 2.82, 2.511, 2.435, 2.37, 2.307],
    [2.526, 2.426, 2.326, 2.252, 2.82, 2.82, 2.82, 2.82, 2.82, 2.82, 2.82, 2.82, 2.82, 2.82, 2.82, 2.82, 2.82, 2.82, 2.82, 2.82, 2.261, 2.324, 2.423, 2.361],
  ],
  'channelsea-high-street-bridge': [
    [2.557, 2.627, 2.694, 2.753, 3.32, 3.32, 3.32, 3.32, 3.32, 3.32, 3.32, 3.32, 3.32, 3.32, 3.32, 3.32, 3.32, 3.32, 3.32, 2.761, 2.722, 2.659, 2.584],
    [2.558, 2.683, 2.809, 2.935, 3.32, 3.32, 3.32, 3.32, 3.32, 3.32, 3.32, 3.32, 3.32, 3.32, 3.32, 3.32, 3.32, 3.32, 3.32, 2.984, 2.856, 2.726, 2.595],
    [2.558, 2.626, 2.694, 2.752, 3.32, 3.32, 3.32, 3.32, 3.32, 3.32, 3.32, 3.32, 3.32, 3.32, 3.32, 3.32, 3.32, 3.32, 3.32, 2.76, 2.723, 2.657, 2.591],
  ],
  'marshgate-lane-connection-0': [
    [1.414, 1.607, 1.804, 2.001, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 2.168, 2.126, 2.039],
    [1.325, 1.509, 1.693, 1.877, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 2.465, 2.285, 2.106, 1.926],
    [1.235, 1.42, 1.604, 1.81, 2.024, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.841, 1.983, 1.993, 1.813],
  ],
  'hunts-lane-connection-0': [
    [null, null, 1.41, 1.515, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.287, 1.144, 1.02, 0.935],
    [null, 1.184, 1.289, 1.393, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.38, 1.237, 1.095, 0.97],
    [0.982, 1.057, 1.161, 1.265, 1.369, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, null, null, null, null, null, null, null, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.299, 1.203, 1.107, 1.011],
  ],
  'three-mills-lea-bridge': [
    [1.563, 1.714, 1.865, 1.921, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 1.918, 1.851, 1.784, 1.659],
    [1.595, 1.746, 1.898, 2.049, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.08, 1.931, 1.782, 1.633],
    [1.627, 1.771, 1.838, 1.905, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 2.22, 1.93, 1.876, 1.757, 1.608],
  ],
  'three-mills-lane-beside-distillery-connection-0': [
    [null, null, null, null, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, null, null, null, null],
    [null, null, null, null, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, null, null, null, null],
    [null, null, null, null, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, null, null, null, null],
  ],
};

const waterLevel = data.riverNetwork.waterLevel,
  tideHigh = data.riverNetwork.tide.high;

// 1. The register and the module copy agree, and every bridge record has a form of its family.
const register = JSON.parse(readFileSync(new URL('../data/maps/road-bridge-forms.json', import.meta.url)));
assert.deepEqual(
  bridgeForms,
  register,
  'docs/road-bridges.js bridgeForms differs from data/maps/road-bridge-forms.json'
);
for (const b of bridges) {
  const form = bridgeForms.bridges[b.id];
  assert(form, `No structural form for ${b.id}`);
  const family = b.style === 'deck' ? /-deck$/ : b.style ? new RegExp(`^${b.style}$`) : /^slab-deck$/;
  assert.match(form.form, family, `${b.id}: form ${form.form} does not match recorded style ${b.style}`);
  if (b.style?.endsWith('-arch')) assert.equal(form.arches, b.archCount, `${b.id}: arch count`);
  assert.equal(Boolean(form.provisional), Boolean(b.provisional), `${b.id}: provisional flag`);
}

// 2. Road surface along every bridge route unchanged.
for (const b of bridges) {
  const now = roadSample(b);
  now.forEach((row, r) =>
    row.forEach((y, i) => {
      const was = BEFORE[b.id][r][i];
      assert(
        y === was || (y !== null && was !== null && Math.abs(y - was) <= 0.001),
        `${b.id}: road surface at station ${i - 4} m, row ${r}, was ${was}, now ${y}`
      );
    })
  );
}

// 3. Abutments where the register puts them, at the drawn banks, and arch crowns clear the water.
const layouts = bridges.map((b) => bridgeLayout(b, bridgeForms.bridges[b.id]));
for (const l of layouts) {
  const [r0, r1] = l.form.abutments;
  // Registered abutments must already lie where the module may put them, or it would move them:
  // deck abutment bodies under the deck; arch abutment faces (each along its own bank where the
  // register gives one skew per abutment) inside the route ends at both deck edges.
  assert(Math.abs(l.a0 - r0) < 1e-9 && Math.abs(l.a1 - r1) < 1e-9, `${l.bridge.id}: abutments moved under the deck`);
  // Where the register lists the drawn bank edges across the deck, each face lies within 1 m of
  // them at every offset whose edge falls inside the route (water beyond a route end, under the
  // approach, cannot be met by a face on the deck).
  const edges = l.form.bankEdges;
  if (!edges) continue;
  edges.offsets.forEach((v, j) =>
    [edges.start[j], edges.end[j]].forEach((edge, i) => {
      if (edge === null || edge < 0 || edge > l.frame.length) return;
      const off = l.face(i, v) - edge;
      assert(
        Math.abs(off) <= 1,
        `${l.bridge.id}: abutment face ${i} at offset ${v} m lies ${off.toFixed(2)} m from the drawn water edge`
      );
    })
  );
}
for (const l of layouts.filter((l) => l.arches.length)) {
  assert(l.crown - waterLevel >= 0.3, `${l.bridge.id}: crown soffit ${l.crown} m within 0.3 m of the water`);
  assert(l.springing > waterLevel, `${l.bridge.id}: springing below the water`);
  // Splayed arches change span across the deck: the rise must suit the span at both deck edges too.
  for (const span of [l.span, ...l.edgeSpans])
    assert(l.rise > 0 && l.rise / span <= 0.5, `${l.bridge.id}: impossible segmental rise ${l.rise} on ${span}`);
}

// 4. Nothing in the channel below the water except abutment footings, river piers and the
// wing walls that turn the abutments into the banks.
const built = roadBridges({
  THREE,
  scene: new THREE.Scene(),
  materials,
  bridges,
  level,
  waterLevel,
  collect: true,
});
const retained = new Set([
  ...data.riverNetwork.retainedWaterChannelIds,
  ...(data.riverNetwork.isolatedWaterChannelIds ?? []),
]);
const water = [
  ...data.riverNetwork.tide.polygons,
  ...data.riverNetwork.reviewedConnections.connections.filter((r) => !r.tidalDisplay).flatMap((r) => r.polygons),
  ...[...data.rivers, ...data.factoryBuildings.westContext.rivers]
    .filter((r) => retained.has(r.id))
    .flatMap((r) => r.polygons),
  ...data.riverNetwork.marshDitches.features.flatMap((f) => f.renderPolygons),
  ...data.riverSystem.waterPolygons,
];
const inRing = (x, z, ring) => {
  let hit = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, zi] = ring[i],
      [xj, zj] = ring[j];
    if (zi > z !== zj > z && x < xi + ((z - zi) * (xj - xi)) / (zj - zi)) hit = !hit;
  }
  return hit;
};
const box2 = (ring) => {
  const xs = ring.map((p) => p[0]),
    zs = ring.map((p) => p[1]);
  return [Math.min(...xs), Math.min(...zs), Math.max(...xs), Math.max(...zs)];
};
const waterBoxes = water.map((p) => box2(p[0]));
const inWater = (x, z) =>
  water.some(
    (p, i) =>
      x >= waterBoxes[i][0] &&
      x <= waterBoxes[i][2] &&
      z >= waterBoxes[i][1] &&
      z <= waterBoxes[i][3] &&
      inRing(x, z, p[0]) &&
      !p.slice(1).some((h) => inRing(x, z, h))
  );
const footings = new Set(['abutment', 'pier', 'cutwater', 'wing']);
const submerged = {};
for (const part of built.parts) {
  const pos = part.positions;
  for (let i = 0; i < pos.length; i += 3) {
    if (pos[i + 1] >= waterLevel - 1e-6 || !inWater(pos[i], pos[i + 2])) continue;
    submerged[`${part.bridge}/${part.part}`] = (submerged[`${part.bridge}/${part.part}`] || 0) + 1;
    assert(footings.has(part.part), `${part.bridge}: ${part.part} below the water at ${pos[i]}, ${pos[i + 2]}`);
  }
}

// 5. Parapets (or railings) on both sides of every non-provisional bridge, the full route length.
for (const b of bridges) {
  const sides = ['left', 'right'].map((side) =>
    built.parts.filter((p) => p.bridge === b.id && (p.part === `parapet-${side}` || p.part === `railing-${side}`))
  );
  if (b.provisional) continue;
  const { a, length, ux, uz } = frame(b);
  sides.forEach((list, i) => {
    assert(list.length, `${b.id}: no ${i ? 'right' : 'left'} parapet`);
    let top = -Infinity,
      sMin = Infinity,
      sMax = -Infinity;
    for (const p of list)
      for (let j = 0; j < p.positions.length; j += 3) {
        top = Math.max(top, p.positions[j + 1]);
        const s = (p.positions[j] - a[0]) * ux + (p.positions[j + 2] - a[1]) * uz;
        sMin = Math.min(sMin, s);
        sMax = Math.max(sMax, s);
      }
    assert(top >= b.height + 0.9, `${b.id}: parapet top ${top.toFixed(2)} m, under 0.9 m above the deck`);
    assert(sMin <= 0.05 && sMax >= length - 0.05, `${b.id}: parapet does not run the full span`);
  });
}

// 6. No approach fill between the abutment faces: the earth meshes from infrastructure() stay
// outside every clear zone (a 0.3 m tolerance for the 0.25 m edge subdivision).
const clearance = bridgeClearance(bridges);
let fillVertices = 0;
scene.traverse((o) => {
  if (!o.isMesh || o.material.map || o.material.color.getHex() !== 0x777463) return;
  const pos = o.geometry.getAttribute('position').array;
  for (let i = 0; i < pos.length; i += 3) {
    fillVertices++;
    const [x, z] = [pos[i], pos[i + 2]];
    if (!clearance.inside(x, z)) continue;
    const near = [
      [0.3, 0],
      [-0.3, 0],
      [0, 0.3],
      [0, -0.3],
    ].some(([dx, dz]) => !clearance.inside(x + dx, z + dz));
    assert(near, `Approach fill under a bridge span at ${x.toFixed(2)}, ${z.toFixed(2)}`);
  }
});
assert(fillVertices > 0, 'No approach fill drawn at all');

// Landscape report for the landscape task (T12b): where the drawn ground stands inside an arch,
// above a deck underside, or above the water under the span. Not asserted.
const landscape = layouts.map((l) => {
  const { frame: f, width, height } = l,
    half = width / 2;
  let insideArch = 0,
    aboveDeck = 0,
    dryUnderSpan = 0,
    samples = 0,
    worst = null;
  for (let v = -half; v <= half + 1e-6; v += half / 4) {
    const arches = l.section ? l.section(v).arches : [];
    for (let s = l.face(0, v); s <= l.face(1, v); s += 0.25) {
      const [x, z] = f.at(s, v),
        y = level(x, z),
        archHere = arches.find((a) => s >= a.from && s <= a.to),
        roof = archHere ? l.soffit(archHere, s) : (l.deckUnderside ?? l.springing);
      samples++;
      if (y > waterLevel) dryUnderSpan++;
      if (y > roof - 0.05 && (!worst || y - roof > worst.by))
        worst = { by: +(y - roof).toFixed(2), station: +s.toFixed(2), offset: +v.toFixed(2) };
      if (archHere && y > roof - 0.05) insideArch++;
      if (y > height) aboveDeck++;
    }
  }
  let overDeck = null;
  for (let s = 0; s <= f.length; s += 0.5)
    for (const v of [-half, 0, half]) {
      const y = level(...f.at(s, v));
      if (y > height - 0.05 && (!overDeck || y - height > overDeck.by))
        overDeck = { by: +(y - height).toFixed(2), station: s, offset: v };
    }
  return {
    id: l.bridge.id,
    groundTouchesSoffitOrDeckUnderside: worst,
    groundAboveDeckOnRoute: overDeck,
    shareOfSpanSamplesWithGroundAboveWater: +(dryUnderSpan / samples).toFixed(2),
    shareInsideArch: +(insideArch / samples).toFixed(2),
    shareAboveDeck: +(aboveDeck / samples).toFixed(2),
  };
});

console.log(
  JSON.stringify(
    {
      status: 'PASS',
      waterLevel,
      tideHigh,
      structures: { meshes: built.meshes, triangles: built.triangles, infrastructureReview: review.bridgeStructures },
      bridges: built.bridges,
      submergedVertices: submerged,
      landscape,
    },
    null,
    1
  )
);
console.log(
  'Road bridges: register matches, road surface unchanged, arch crowns clear the water, only footings and piers in the channel, parapets both sides, no fill under the spans.'
);
