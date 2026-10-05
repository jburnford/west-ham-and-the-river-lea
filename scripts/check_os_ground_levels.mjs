// OS five-foot ground levels (data/maps/os-ground-levels.json): the register's copies of the spot heights, and the
// drawn ground at every reading the main landscape applies. Builds the ground the page draws (terrainDetails().level,
// as app.js assembles it) and the real road meshes from infrastructure(), then compares each applied reading with the
// drawn road surface (street readings) or the drawn ground (premises and marsh readings).
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import * as THREE from 'three';
import { loadHistoricElevation, applyHistoricElevation } from '../docs/historic-elevation.js';
import { loadRiverNetwork } from '../docs/river-network.js';
import { loadRiverSystem, applyRiverSystem } from '../docs/river-system.js';
import { loadMainLandscape, applyMainLandscape, premisesLevel } from '../docs/main-landscape.js';
import { createGroundSampler } from '../docs/lib/ground-sampler.js';
import { box as libBox } from '../docs/lib/geometry.js';
import { infrastructure } from '../docs/infrastructure.js';

const root = new URL('../', import.meta.url);
const json = (path) => JSON.parse(readFileSync(new URL(path, root)));
const load = async (url, type = 'json') => {
  const b = readFileSync(new URL('docs/' + url.replace(/^\.\//, ''), root));
  return type === 'json' ? JSON.parse(b) : b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength);
};
globalThis.location = { search: '' };
const register = json('data/maps/os-ground-levels.json');

// 1. Register copies of the OS readings: every spot height and bench mark in the core box, value, position and
// scene level as in the collection and the project datum.
const [bx0, bz0, bx1, bz1] = register.coreBox,
  d = register.datum;
const sceneY = (feet) => (feet + d.liverpoolToNewlynFeet) * d.footMetres - d.odnMinusSceneYMetres;
const source = new Map();
for (const f of json('reference/spot-heights/heights.geojson').features) {
  const p = f.properties,
    x = p.bng_e - 538900,
    z = 183209 - p.bng_n;
  if (x >= bx0 && x <= bx1 && z >= bz0 && z <= bz1) source.set(p.id, { ...p, x, z });
}
assert.equal(register.readings.length, source.size, 'Register and spot-height collection differ in the core box');
for (const r of register.readings) {
  const s = source.get(r.id);
  assert(s, `${r.id} is not in the spot-height collection`);
  assert.equal(r.valueFeet, s.value_ft, r.id);
  assert(Math.hypot(r.position[0] - s.x, r.position[1] - s.z) < 0.01, `${r.id} position`);
  assert(Math.abs(r.sceneY - sceneY(s.value_ft)) < 0.001, `${r.id} scene level`);
  assert(['premises', 'street', 'marsh', 'none'].includes(r.use), `${r.id} use`);
  if (r.use === 'none') assert(r.reason, `${r.id}: a reading not applied must say why`);
  if (r.use !== 'none') assert.equal(r.category, 'ground', `${r.id}: only ground readings are applied`);
  if (r.exception) assert.notEqual(r.use, 'none', `${r.id}: exceptions are applied readings`);
}

// 2. The drawn ground, assembled as app.js does.
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
const landscape = await loadMainLandscape(load);
applyMainLandscape(data, landscape);
data.drawnGround = createGroundSampler([
  data.elevation && { positions: data.elevation.grids.extension },
  data.mainLandscape && { positions: data.mainLandscape.grids.groundMesh },
  { positions: data.riverNetwork.positions, indices: data.riverNetwork.indices },
  { positions: data.riverSystem.positions, indices: data.riverSystem.indices },
]);
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
infrastructure({
  THREE,
  scene,
  materials: { stone: plain(), ground: plain(), iron: plain(), wood: plain(), brick: plain() },
  data: { ...data, infrastructure: { ...data.infrastructure, railways: [] } },
  box: (parent, ...args) => libBox(THREE, parent, ...args),
  level,
});
scene.updateMatrixWorld(true);
const roadPositions = [];
scene.traverse((o) => {
  if (!o.isMesh || !o.material.map) return;
  const g = (o.geometry.index ? o.geometry.toNonIndexed() : o.geometry.clone()).applyMatrix4(o.matrixWorld);
  for (const v of g.getAttribute('position').array) roadPositions.push(v);
});
const drawnRoad = createGroundSampler([{ positions: new Float32Array(roadPositions) }], { cellSize: 4 });

// 3. Applied readings against the drawn ground or road.
const limit = register.exceptionMetres;
const rows = [];
for (const r of register.readings.filter((r) => r.use !== 'none')) {
  const [x, z] = r.position,
    road = r.use === 'street' ? drawnRoad.sample(x, z) : null,
    drawn = road ?? level(x, z);
  rows.push({ id: r.id, use: r.use, zone: r.zone, residual: drawn - r.sceneY, exception: r.exception });
}
const kept = rows.filter((r) => !r.exception),
  abs = kept.map((r) => Math.abs(r.residual)).sort((a, b) => a - b),
  pct = (q) => abs[Math.min(abs.length - 1, Math.floor(q * abs.length))];
for (const r of kept)
  assert(Math.abs(r.residual) <= limit, `${r.id} (${r.use}, ${r.zone}): drawn - OS ${r.residual.toFixed(2)} m`);
assert(pct(0.5) <= 0.3, `Median |drawn - OS| ${pct(0.5).toFixed(2)} m`);
assert(pct(0.9) <= limit, `90th percentile |drawn - OS| ${pct(0.9).toFixed(2)} m`);
assert(kept.length >= 80, 'Too few applied readings');

// 4. Premises pads: each register premises reading is a control of its pad, and docs/main-landscape.js
// premisesLevel() meets it within 0.1 m.
const pads = new Map(landscape.meta.siteGround.map((p) => [p.siteId, p]));
for (const [siteId, item] of Object.entries(register.premises)) {
  const pad = pads.get(+siteId);
  assert(pad, `Site ${siteId} has OS yard readings but no premises pad`);
  for (const id of item.controlIds) {
    assert(pad.sourceIds.includes(id), `${id} is not a control of site ${siteId}`);
    const r = register.readings.find((q) => q.id === id);
    assert(
      Math.abs(premisesLevel(pad, ...r.position) - r.sceneY) < 0.1,
      `${id}: site ${siteId} pad misses its reading`
    );
  }
}

console.log(
  JSON.stringify({
    status: 'PASS',
    readings: register.readings.length,
    applied: rows.length,
    byUse: Object.fromEntries(['premises', 'street', 'marsh'].map((u) => [u, rows.filter((r) => r.use === u).length])),
    medianAbsMetres: +pct(0.5).toFixed(3),
    p90AbsMetres: +pct(0.9).toFixed(3),
    worstKept: kept.reduce((w, r) => (Math.abs(r.residual) > Math.abs(w.residual) ? r : w)),
    exceptions: rows.filter((r) => r.exception).map((r) => [r.id, +r.residual.toFixed(2)]),
  })
);
console.log('OS ground levels: register matches the spot heights; the drawn ground meets every applied reading.');
