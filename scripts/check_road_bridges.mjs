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

// Drawn road surface after T18 (4 October 2026: deck ends flush with the deck and level across the road,
// deck-end footways, Marshgate Lane retraced), from --write-sample on the round-2 cascade landscape (4 October 2026): right side, centre, left side.
// Refreshed by T22 (4 October 2026): the terrace drawn at its OS levels (approaches at Bow, Pegs Hole, St Thomas,
// St Michael's and the two lane connections rise onto their decks instead of sagging to the bridge cone) and Three
// Mills Bridge re-levelled to its OS deck level (4.23 m, was 2.2 m); no other deck station changed (T22_REPORT.md).
// Refreshed by task A (5 October 2026): Pegs Hole Bridge re-levelled to its OS crown (3.59 m, was 3.0 m) and the
// Marshgate Lane and Cook's Road connection decks to their lane levels (2.93 m and 2.8 m, were 1.5 m); TASK_A_REPORT.md.
// Refreshed by task B (5 October 2026): Marshgate Lane level beside its Pudding Mill River wall (approach to the
// connection deck, up to 0.3 m); TASK_B_REPORT.md.
// Refreshed by task C (5 October 2026): the tide re-levelled to the OS (data/maps/os-tide-levels.json); only the
// Hunts Lane connection's west approach moved (up to 0.022 m, the bank under it), then, after the core-tongue mud
// face and the House Mill race culvert, St Thomas and St Michael's by 0.001 m and Hunts Lane by up to 0.009 m more;
// TASK_C_REPORT.md.
// Refresh with --write-sample whenever a road, bridge span or the landscape under an approach is deliberately changed.
// prettier-ignore
const BEFORE = {
  'abbey-mill-crossing': [
    [1.974,  1.934,  1.892,  1.848,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.817,  1.865,  1.909,  1.95],
    [1.966,  1.925,  1.883,  1.842,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.814,  1.855,  1.896,  1.936],
    [1.957,  1.915,  1.876,  1.836,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.82,  1.806,  1.845,  1.884,  1.922],
  ],
  'bow-bridge': [
    [4.32,  4.44,  4.56,  4.72,  4.8,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.757,  4.584,  4.527,  4.53],
    [4.32,  4.44,  4.56,  4.68,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.732,  4.646,  4.561,  4.475],
    [4.32,  4.44,  4.56,  4.726,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.82,  4.757,  4.584,  4.464,  4.42],
  ],
  'pegshole-bridge': [
    [3.11,  3.23,  3.35,  3.52,  3.61,  3.61,  3.61,  3.61,  3.61,  3.61,  3.61,  3.61,  3.61,  3.61,  3.61,  3.61,  3.61,  3.61,  3.61,  3.61,  3.61,  3.61,  3.61,  3.529,  3.356,  3.236,  3.116],
    [3.11,  3.23,  3.35,  3.47,  3.61,  3.61,  3.61,  3.61,  3.61,  3.61,  3.61,  3.61,  3.61,  3.61,  3.61,  3.61,  3.61,  3.61,  3.61,  3.61,  3.61,  3.61,  3.61,  3.477,  3.357,  3.238,  3.119],
    [3.11,  3.23,  3.35,  3.52,  3.61,  3.61,  3.61,  3.61,  3.61,  3.61,  3.61,  3.61,  3.61,  3.61,  3.61,  3.61,  3.61,  3.61,  3.61,  3.61,  3.61,  3.61,  3.61,  3.529,  3.356,  3.236,  3.121],
  ],
  'st-thomas-bridge': [
    [2.525,  2.554,  2.36,  2.53,  null,  2.62,  2.62,  2.62,  2.62,  2.62,  2.62,  2.62,  2.62,  2.599,  2.513,  2.354,  2.325],
    [2.647,  2.635,  2.623,  2.612,  2.6,  2.62,  2.62,  2.62,  2.62,  2.62,  2.62,  2.62,  2.62,  2.595,  2.526,  2.503,  2.48],
    [2.769,  2.64,  2.36,  2.53,  2.6,  2.62,  2.62,  2.62,  2.62,  2.62,  2.62,  2.62,  2.62,  2.599,  2.516,  2.354,  2.536],
  ],
  'st-michaels-bridge': [
    [2.335,  2.44,  2.56,  2.71,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.773,  2.611,  2.482,  2.362],
    [2.442,  2.527,  2.612,  2.697,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.722,  2.602,  2.482,  2.362],
    [2.549,  2.48,  2.56,  2.728,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.773,  2.606,  2.482,  2.362],
  ],
  'channelsea-high-street-bridge': [
    [2.82,  2.94,  3.06,  3.216,  3.32,  3.32,  3.32,  3.32,  3.32,  3.32,  3.32,  3.32,  3.32,  3.32,  3.32,  3.32,  3.32,  3.32,  3.32,  3.278,  3.117,  2.988,  2.868],
    [2.82,  2.94,  3.06,  3.18,  3.32,  3.32,  3.32,  3.32,  3.32,  3.32,  3.32,  3.32,  3.32,  3.32,  3.32,  3.32,  3.32,  3.32,  3.32,  3.228,  3.108,  2.988,  2.868],
    [2.82,  2.94,  3.06,  3.227,  3.32,  3.32,  3.32,  3.32,  3.32,  3.32,  3.32,  3.32,  3.32,  3.32,  3.32,  3.32,  3.32,  3.32,  3.32,  3.278,  3.118,  2.988,  2.868],
  ],
  'marshgate-lane-connection-0': [
    [2.645,  2.645,  2.729,  2.896,  2.95,  2.95,  2.95,  2.95,  2.95,  2.95,  2.95,  2.95,  2.95,  2.95,  2.95,  2.95,  2.95,  2.95,  2.95,  2.95,  2.95,  2.95,  2.95,  2.95,  2.95,  2.95,  2.95,  2.95,  2.95,  2.95,  2.931,  2.95,  2.982,  null],
    [2.645,  2.645,  2.693,  2.811,  2.95,  2.95,  2.95,  2.95,  2.95,  2.95,  2.95,  2.95,  2.95,  2.95,  2.95,  2.95,  2.95,  2.95,  2.95,  2.95,  2.95,  2.95,  2.95,  2.95,  2.95,  2.95,  2.95,  2.95,  2.95,  2.95,  2.945,  2.965,  2.997,  3.02],
    [2.645,  2.645,  2.666,  2.786,  2.925,  2.95,  2.95,  2.95,  2.95,  2.95,  2.95,  2.95,  2.95,  2.95,  2.95,  null,  null,  null,  null,  null,  null,  2.95,  2.95,  2.95,  2.95,  2.95,  2.95,  2.95,  2.95,  2.93,  2.95,  2.98,  3.004,  3.033],
  ],
  'hunts-lane-connection-0': [
    [null,  null,  null,  2.761,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.768,  2.629,  2.556,  2.585],
    [null,  2.704,  2.686,  2.741,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.755,  2.615,  2.55,  2.576],
    [2.732,  2.667,  2.661,  2.721,  2.797,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  null,  null,  null,  null,  null,  null,  null,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.82,  2.739,  2.578,  2.553,  2.565],
  ],
  'three-mills-lea-bridge': [
    [3.75,  3.87,  3.993,  4.143,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.189,  4.027,  3.894,  3.774],
    [3.75,  3.87,  3.992,  4.111,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.189,  4.028,  3.894,  3.774],
    [3.75,  3.87,  3.99,  4.152,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.25,  4.191,  4.024,  3.894,  3.774],
  ],
  'house-mill-race-crossing': [
    [2.688,  2.689,  2.687,  2.694,  2.702,  2.726,  2.726,  2.726,  2.726,  2.726,  2.726,  2.705,  2.697,  2.69,  2.689],
    [2.688,  2.675,  2.663,  2.67,  2.726,  2.726,  2.726,  2.726,  2.726,  2.726,  2.726,  2.706,  2.683,  2.675,  2.677],
    [2.665,  2.65,  2.639,  2.675,  2.726,  2.726,  2.726,  2.726,  2.726,  2.726,  2.726,  2.726,  2.683,  2.66,  2.664],
  ],
  'three-mills-lane-beside-distillery-connection-0': [
    [null,  null,  null,  null,  1.52,  1.52,  1.52,  1.52,  1.52,  1.52,  1.52,  1.52,  1.52,  1.52,  1.52,  1.52,  1.52,  null,  null,  null,  null],
    [null,  null,  null,  null,  1.52,  1.52,  1.52,  1.52,  1.52,  1.52,  1.52,  1.52,  1.52,  1.52,  1.52,  1.52,  1.52,  null,  null,  null,  null],
    [null,  null,  null,  null,  1.52,  1.52,  1.52,  1.52,  1.52,  1.52,  1.52,  1.52,  1.52,  1.52,  1.52,  1.52,  1.52,  null,  null,  null,  null],
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

// 5. Parapets (or railings) on both sides of every non-provisional bridge, the full route length,
// except where the register records that the map draws none (parapets false), and then none at all.
for (const b of bridges) {
  const sides = ['left', 'right'].map((side) =>
    built.parts.filter((p) => p.bridge === b.id && (p.part === `parapet-${side}` || p.part === `railing-${side}`))
  );
  if (bridgeForms.bridges[b.id].parapets === false) {
    assert(
      sides.every((list) => !list.length),
      `${b.id}: parapet drawn where the register has none`
    );
    continue;
  }
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
  'Road bridges: register matches, road surface unchanged, arch crowns clear the water, only footings and piers in the channel, parapets both sides (none where the map draws none), no fill under the spans.'
);
