// High Street horse-tram rails: corridor, gauge, seating on the drawn road and water clearance.
// Builds the rails exactly as the page does, then measures them against the road meshes made
// by the real infrastructure() module, not against the tram module's own surface estimate.
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
import { buildTramRailGeometry, deckAt } from '../docs/tram-rails.js';

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
data.tramRails = await load('./data/tram-rails.json');
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
// terrainDetails().level, which app.js hands to infrastructure() and to the tram module.
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

const built = buildTramRailGeometry({ data, level, spec: data.tramRails });
const { route, width, decks, lines, review } = built;

// The real road and bridge-deck meshes. Railways are left out: they never carry road setts.
const canvasContext = new Proxy({}, { get: () => () => undefined, set: () => true });
globalThis.document = { createElement: () => ({ width: 0, height: 0, getContext: () => canvasContext }) };
const scene = new THREE.Scene();
const plain = () => new THREE.MeshStandardMaterial();
const materials = { stone: plain(), ground: plain(), iron: plain(), wood: plain(), brick: plain() };
infrastructure({
  THREE,
  scene,
  materials,
  data: { ...data, infrastructure: { ...data.infrastructure, railways: [] } },
  box: (parent, ...args) => libBox(THREE, parent, ...args),
  level,
});
scene.updateMatrixWorld(true);
const roadPositions = [];
scene.traverse((o) => {
  // Paved road materials carry the generated sett/macadam/cinder texture; pavements and fills do not.
  if (!o.isMesh || !o.material.map) return;
  const g = (o.geometry.index ? o.geometry.toNonIndexed() : o.geometry.clone()).applyMatrix4(o.matrixWorld);
  for (const v of g.getAttribute('position').array) roadPositions.push(v);
});
assert(roadPositions.length > 9 * 1000, 'Road meshes not built');
const drawnRoad = createGroundSampler([{ positions: new Float32Array(roadPositions) }], { cellSize: 4 });

const distanceToRoute = (x, z) => {
  let best = Infinity;
  for (let i = 1; i < route.length; i++) {
    const [a, b] = [route[i - 1], route[i]],
      dx = b[0] - a[0],
      dz = b[1] - a[1],
      s = Math.max(0, Math.min(1, ((x - a[0]) * dx + (z - a[1]) * dz) / (dx * dx + dz * dz)));
    best = Math.min(best, Math.hypot(x - a[0] - s * dx, z - a[1] - s * dz));
  }
  return best;
};
const distanceToLine = (x, z, line) => {
  let best = Infinity;
  for (let i = 1; i < line.length; i++) {
    const [a, b] = [line[i - 1], line[i]],
      dx = b[0] - a[0],
      dz = b[2] - a[2],
      l = dx * dx + dz * dz;
    if (l < 1e-12) continue;
    const s = Math.max(0, Math.min(1, ((x - a[0]) * dx + (z - a[2]) * dz) / l));
    best = Math.min(best, Math.hypot(x - a[0] - s * dx, z - a[2] - s * dz));
  }
  return best;
};
const inside = (x, z, ring) => {
  let hit = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, zi] = ring[i],
      [xj, zj] = ring[j];
    if (zi > z !== zj > z && x < xi + ((z - zi) * (xj - xi)) / (zj - zi)) hit = !hit;
  }
  return hit;
};

// 1. Geometry shape: one merged mesh, double or single track as registered, no overhead.
assert.equal(review.overhead, 'none');
assert.equal(review.rails, review.tracks * 2);
assert.equal(review.fallbackSamples, 0, 'Rail points off both road triangles and bridge decks');
const pos = built.positions;
assert.equal(pos.length % 3, 0);
assert(built.indices.every((i) => i < pos.length / 3));

// 2. Corridor: every rail vertex within the carriageway, at least 1 m clear of the kerb line.
let widest = 0;
for (let i = 0; i < pos.length; i += 3) widest = Math.max(widest, distanceToRoute(pos[i], pos[i + 2]));
assert(widest <= width / 2 - 1, `Rail ${widest.toFixed(2)} m from the High Street centreline`);

// 3. Gauge: running edges of each track 1.435 m apart within 1 cm, along the whole route.
let gaugeMin = Infinity,
  gaugeMax = -Infinity;
for (let track = 0; track < review.tracks; track++) {
  const [left, right] = [-1, 1].map((side) => lines.find((l) => l.track === track && l.side === side).gauge);
  for (const p of left) {
    const g = distanceToLine(p[0], p[2], right);
    gaugeMin = Math.min(gaugeMin, g);
    gaugeMax = Math.max(gaugeMax, g);
  }
}
assert(Math.abs(gaugeMin - 1.435) <= 0.01 && Math.abs(gaugeMax - 1.435) <= 0.01, `Gauge ${gaugeMin}-${gaugeMax}`);

// 4. Seating: rail head above the drawn road or deck by no more than 0.02 m, at every vertex and
// halfway along every strip edge (except within 0.1 m of a deck end, where the deck steps up).
let riseMin = Infinity,
  riseMax = -Infinity,
  samples = 0;
const nearDeckEnd = (x, z, reach = 0.1) =>
  decks.some((d) => {
    const along = (x - d.a[0]) * d.ux + (z - d.a[1]) * d.uz;
    return Math.min(Math.abs(along), Math.abs(along - d.length)) < reach;
  });
let unsupported = 0,
  lowAt = null,
  highAt = null;
const holes = new Set();
const seat = (x, y, z) => {
  const road = drawnRoad.sample(x, z);
  if (road === null) {
    // The drawn road has small holes (west end of Bow Bridge; a sliver at the Channelsea approach
    // junction). The rails cross them on the plane of the adjoining road; only a few are tolerated.
    unsupported++;
    holes.add(`${Math.round(x)},${Math.round(z)}`);
    return;
  }
  if (y - road < riseMin) [riseMin, lowAt] = [y - road, [+x.toFixed(2), +z.toFixed(2)]];
  if (y - road > riseMax) [riseMax, highAt] = [y - road, [+x.toFixed(2), +z.toFixed(2)]];
  samples++;
};
for (const l of lines)
  for (const edge of [l.gauge, l.outer])
    edge.forEach((p, k) => {
      seat(...p);
      const q = edge[k + 1];
      if (!q) return;
      const m = [(p[0] + q[0]) / 2, (p[1] + q[1]) / 2, (p[2] + q[2]) / 2];
      if (!nearDeckEnd(m[0], m[2])) seat(...m);
    });
assert(unsupported <= 0.01 * samples, `${unsupported} rail samples over holes in the drawn road`);
assert(riseMin > 0.001, `Rail head ${riseMin.toFixed(4)} m relative to the road: buried`);
assert(riseMax <= 0.02, `Rail head ${riseMax.toFixed(4)} m above the road`);

// 5. Water: a rail vertex over any mapped river reach (the Channelsea included) must be on a deck.
const reaches = data.riverSystem.reaches;
const channelsea = reaches.filter((r) => /Channelsea/.test(r.name));
assert(channelsea.length > 0, 'Channelsea reach missing');
let overWater = 0,
  overChannelsea = 0;
for (let i = 0; i < pos.length; i += 3) {
  const [x, z] = [pos[i], pos[i + 2]];
  for (const r of reaches)
    for (const poly of r.polygons)
      if (inside(x, z, poly[0]) && !poly.slice(1).some((h) => inside(x, z, h))) {
        overWater++;
        if (channelsea.includes(r)) overChannelsea++;
        assert(deckAt(decks, x, z), `Rail over ${r.name} off the bridge deck at ${x.toFixed(2)}, ${z.toFixed(2)}`);
      }
}
assert(overChannelsea > 0, 'Rails do not cross the Channelsea bridge');

console.log(
  JSON.stringify({
    status: 'PASS',
    form: review.form,
    rails: review.rails,
    triangles: review.triangles,
    stations: review.stations,
    routeLengthMetres: review.routeLengthMetres,
    widestFromCentreline: +widest.toFixed(3),
    gauge: [+gaugeMin.toFixed(4), +gaugeMax.toFixed(4)],
    riseAboveDrawnRoad: [+riseMin.toFixed(4), +riseMax.toFixed(4)],
    lowestAt: lowAt,
    highestAt: highAt,
    seatingSamples: samples,
    samplesOverRoadHoles: unsupported,
    roadHolesNear: [...holes].slice(0, 12),
    verticesOverWaterOnDecks: overWater,
    overChannelseaOnDeck: overChannelsea,
  })
);
console.log('Tram rails: inside the High Street, standard gauge, seated on the drawn setts, water only on decks.');
