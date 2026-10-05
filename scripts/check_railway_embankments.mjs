// Railway embankments: no embankment over drawn water, the Bow Creek bridge deck continuous from
// abutment to abutment at formation height, no embankment vertex inside a mapped building footprint
// (other than the recorded formation conflicts), and no raised embankment edge left open at the
// recorded line ends and bridges. Builds the real infrastructure() module, as the road-bridge
// check does, and inspects the drawn meshes.
//   node scripts/check_railway_embankments.mjs
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
import { railwayBridgeForms, bridgeFrame, faceStation, formationAt } from '../docs/railway-bridges.js';

const load = async (url, type = 'json') => {
  const b = readFileSync(new URL('../docs/' + url.replace(/^\.\//, ''), import.meta.url));
  return type === 'json' ? JSON.parse(b) : b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength);
};
globalThis.location = { search: '' };

// The register copy in docs/railway-bridges.js matches data/maps/railway-bridge-forms.json.
const register = JSON.parse(readFileSync(new URL('../data/maps/railway-bridge-forms.json', import.meta.url)));
assert.deepStrictEqual(
  railwayBridgeForms,
  register,
  'docs/railway-bridges.js railwayBridgeForms differs from data/maps/railway-bridge-forms.json'
);

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
const rawInfrastructure = await load('./data/infrastructure.json');
data.riverNetwork = await loadRiverNetwork(load);
data.elevation = await loadHistoricElevation(load);
applyHistoricElevation(data);
data.riverSystem = await loadRiverSystem(load);
applyRiverSystem(data);
applyMainLandscape(data, await loadMainLandscape(load));
assert(data.mainLandscape, 'main landscape not loaded');
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
const materials = { stone: plain(), ground: plain(), iron: plain(), wood: plain(), brick: plain() };
const review = infrastructure({
  THREE,
  scene,
  materials,
  data,
  box: (parent, ...args) => libBox(THREE, parent, ...args),
  level,
});
scene.updateMatrixWorld(true);

// Drawn triangles per mesh-name prefix, keyed by railway name.
function trianglesNamed(prefix) {
  const out = {};
  scene.traverse((o) => {
    if (!o.isMesh || !o.name.startsWith(prefix)) return;
    const g = (o.geometry.index ? o.geometry.toNonIndexed() : o.geometry.clone()).applyMatrix4(o.matrixWorld),
      p = g.getAttribute('position').array,
      list = (out[o.name.slice(prefix.length)] ||= []);
    for (let i = 0; i < p.length; i += 9)
      list.push([
        [p[i], p[i + 1], p[i + 2]],
        [p[i + 3], p[i + 4], p[i + 5]],
        [p[i + 6], p[i + 7], p[i + 8]],
      ]);
  });
  return out;
}
const embankments = trianglesNamed('railway-embankment:'),
  walls = trianglesNamed('railway-wall:');
const railways = rawInfrastructure.railways;
assert.deepStrictEqual(
  Object.keys(embankments).sort(),
  railways.map((r) => r.name).sort(),
  'every railway embankment is drawn and named'
);

// Plan polygons and an even-odd point test with a bounding-box prefilter.
function polygonSet(polygons) {
  return polygons.map((rings) => {
    const xs = rings[0].map((p) => p[0]),
      zs = rings[0].map((p) => p[1]);
    return { rings, box: [Math.min(...xs), Math.min(...zs), Math.max(...xs), Math.max(...zs)] };
  });
}
function inside(set, x, z) {
  for (const { rings, box } of set) {
    if (x < box[0] || x > box[2] || z < box[1] || z > box[3]) continue;
    let odd = false;
    for (const ring of rings)
      for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
        const [xi, zi] = ring[i],
          [xj, zj] = ring[j];
        if (zi > z !== zj > z && x < ((xj - xi) * (z - zi)) / (zj - zi) + xi) odd = !odd;
      }
    if (odd) return true;
  }
  return false;
}

// 1. No embankment over drawn water (the low-water mask the landscape builder uses: river-system
//    reaches, ground-plan rivers and marsh ditches).
const water = polygonSet([
  ...data.riverSystem.reaches.flatMap((r) => r.polygons),
  ...data.rivers.flatMap((r) => r.polygons),
  ...data.riverNetwork.marshDitches.features.flatMap((f) => f.renderPolygons),
]);
const overWater = {};
for (const [name, tris] of Object.entries(embankments)) {
  let n = 0;
  for (const tri of tris) {
    const cx = (tri[0][0] + tri[1][0] + tri[2][0]) / 3,
      cz = (tri[0][2] + tri[1][2] + tri[2][2]) / 3;
    if (inside(water, cx, cz) || tri.some((p) => inside(water, p[0], p[2]))) n++;
  }
  overWater[name] = n;
}
assert(
  Object.values(overWater).every((n) => n === 0),
  `embankment triangles over drawn water: ${JSON.stringify(overWater)}`
);

// 2. The Bow Creek bridge: deck top continuous at formation height from abutment face to
//    abutment face on both deck edges and the centreline, each end on a brick face reaching the
//    formation.
const bow = railwayBridgeForms.bridges['ltsr-bow-creek'],
  ltsr = data.infrastructure.railways.find((r) => r.name === bow.railway),
  frame = bridgeFrame(ltsr),
  // The deck is level at the OS formation level midway between the abutment faces (railway-bridges.js).
  h = formationAt(ltsr, (bow.abutments.west.centre + bow.abutments.east.centre) / 2);
const structure = [];
scene.traverse((o) => o.isMesh && o.name === 'railway-bridge-structure' && structure.push(o));
assert(structure.length, 'railway bridge structure drawn');
const ray = new THREE.Raycaster();
const deck = {};
// Top edges of the drawn brick faces (main-landscape railway works quads: top a, top b, foot b, foot a).
assert((walls[bow.railway] || []).length, 'no brick faces drawn for the LT&SR');
const wallTops = data.mainLandscape.meta.railwaySlopes
  .find((p) => p.name === bow.railway)
  .works.walls.map((q) => [q[0], q[1]]);
function wallAt(o, s, reach) {
  // Brick face crossing the line at offset o within reach of station s, its top height there.
  let best = null;
  const a = frame.at(s - reach, o, 0),
    b = frame.at(s + reach, o, 0);
  for (const [p, q] of wallTops) {
    const d1 = [b[0] - a[0], b[2] - a[2]],
      d2 = [q[0] - p[0], q[2] - p[2]],
      den = d1[0] * d2[1] - d1[1] * d2[0];
    if (Math.abs(den) < 1e-9) continue;
    const w = [p[0] - a[0], p[2] - a[2]],
      k = (w[0] * d2[1] - w[1] * d2[0]) / den,
      l = (w[0] * d1[1] - w[1] * d1[0]) / den;
    if (k < 0 || k > 1 || l < 0 || l > 1) continue;
    const y = p[1] + (q[1] - p[1]) * l,
      station = s - reach + 2 * reach * k;
    if (!best || y > best.y) best = { station, y };
  }
  return best;
}
for (const [label, o] of [
  ['left', bow.girderOffset - 0.2],
  ['centre', 0],
  ['right', -(bow.girderOffset - 0.2)],
]) {
  const west = faceStation(bow.abutments.west, o, bow.girderOffset),
    east = faceStation(bow.abutments.east, o, bow.girderOffset);
  let gaps = 0,
    worst = 0;
  for (let s = west + 0.05; s <= east - 0.05; s += 0.5) {
    const p = frame.at(s, o, h + 0.1);
    ray.set(new THREE.Vector3(...p), new THREE.Vector3(0, -1, 0));
    const hit = ray.intersectObjects(structure, false)[0];
    if (!hit) gaps++;
    else worst = Math.max(worst, Math.abs(hit.point.y - h));
  }
  const westWall = wallAt(o, west, 0.6),
    eastWall = wallAt(o, east, 0.6);
  deck[label] = {
    from: +west.toFixed(2),
    to: +east.toFixed(2),
    gaps,
    worstOffFormation: +worst.toFixed(3),
    westAbutment: westWall && [+westWall.station.toFixed(2), +westWall.y.toFixed(2)],
    eastAbutment: eastWall && [+eastWall.station.toFixed(2), +eastWall.y.toFixed(2)],
  };
  assert.equal(gaps, 0, `Bow Creek deck has gaps on the ${label} line`);
  assert(worst <= 0.02, `Bow Creek deck top off formation height on the ${label} line: ${worst}`);
  for (const [end, wall, station] of [
    ['west', westWall, west],
    ['east', eastWall, east],
  ]) {
    assert(wall, `no brick abutment face at the ${end} end of the ${label} deck line`);
    assert(Math.abs(wall.station - station) <= 0.3, `${end} abutment face ${wall.station} off deck end ${station}`);
    // At the deck edges the traced embankment top has begun to fall (crest 4-4.5 m from the centreline).
    assert(wall.y >= h - (o === 0 ? 0.05 : 0.35), `${end} abutment face top ${wall.y} below the formation`);
  }
}

// 3. No embankment vertex inside a mapped building footprint, except recorded formation conflicts.
const plan = data,
  factory = data.factoryBuildings,
  footprints = [];
const add = (label, rings) => footprints.push({ label, set: polygonSet([rings]) });
const circle = (x, z, r) => [
  Array.from({ length: 48 }, (_, i) => [x + r * Math.cos(i / 7.64), z + r * Math.sin(i / 7.64)]),
];
for (const b of factory.buildings)
  for (const p of b.renderPolygons || []) add(`factory ${b.id}`, [p.outer, ...(p.holes || [])]);
for (const hl of factory.holders) add(`holder ${hl.id ?? hl.siteId}`, circle(hl.x, hl.z, hl.radius));
for (const k of ['mappedFactories', 'houses', 'terraces'])
  for (const b of plan.neighbourhood[k]) if (b.footprint) add(`${k} ${b.id}`, [b.footprint]);
for (const b of data.highStreetFrontages.buildings) if (b.footprint) add(`frontage ${b.id}`, [b.footprint]);
for (const b of data.housingDetail.rows) if (b.footprint) add(`housing ${b.id}`, [b.footprint]);
add('station', [data.stationPlan.worldFootprint]);
for (const b of data.stationPlan.supportingBuildings) if (b.footprint) add(`station ${b.id}`, [b.footprint]);
const conflicts = new Set(
  data.mainLandscape.meta.railwaySlopes.flatMap((p) =>
    (p.works?.items || [])
      .filter((i) => i.kind === 'conflict')
      .flatMap((i) => i.conflicts.map((c) => `${p.name}|${c.footprint}`))
  )
);
const buried = {};
for (const [name, tris] of Object.entries(embankments)) {
  const seen = new Set();
  for (const tri of tris)
    for (const [x, , z] of tri) {
      const key = `${x.toFixed(3)},${z.toFixed(3)}`;
      if (seen.has(key)) continue;
      seen.add(key);
      for (const f of footprints)
        if (inside(f.set, x, z) && !conflicts.has(`${name}|${f.label}`))
          buried[`${name}|${f.label}`] = (buried[`${name}|${f.label}`] || 0) + 1;
    }
}
assert.deepStrictEqual(buried, {}, `embankment vertices inside building footprints: ${JSON.stringify(buried)}`);
assert.equal(conflicts.size, 3, `recorded formation conflicts changed: ${[...conflicts].join('; ')}`);

// 4. No raised embankment edge left open (a box end or an open cut) within 40 m of a recorded line
//    end or bridge: every boundary edge there stands within 0.5 m of the drawn ground or carries a
//    brick face.
const sites = [
  ...Object.values(railwayBridgeForms.lineEnds).map((e) => ({ railway: e.railway, point: e.point })),
  ...Object.values(railwayBridgeForms.bridges).map((b) => {
    const r = data.infrastructure.railways.find((x) => x.name === b.railway);
    if (b.frame === 'route-start') {
      const p = bridgeFrame(r).at((b.abutments.west.centre + b.abutments.east.centre) / 2, 0, 0);
      return { railway: b.railway, point: [p[0], p[2]], reach: 45 };
    }
    const st = r.stations.find((s) => s[5] >= (b.start + b.end) / 2);
    return { railway: b.railway, point: [st[0], st[1]], reach: 30 };
  }),
];
// Plan vertex ids that treat points within 1 cm as one (the works geometry is stored to 1 mm).
const vertexIds = new Map();
function key(p) {
  const cx = Math.floor(p[0] / 0.05),
    cz = Math.floor(p[2] / 0.05);
  for (let dx = -1; dx <= 1; dx++)
    for (let dz = -1; dz <= 1; dz++)
      for (const [q, id] of vertexIds.get(`${cx + dx},${cz + dz}`) || [])
        if (Math.hypot(q[0] - p[0], q[1] - p[2]) < 0.01) return id;
  const id = String(vertexIds.size ? [...vertexIds.values()].reduce((n, l) => n + l.length, 0) : 0) + `@${cx},${cz}`;
  if (!vertexIds.has(`${cx},${cz}`)) vertexIds.set(`${cx},${cz}`, []);
  vertexIds.get(`${cx},${cz}`).push([[p[0], p[2]], id]);
  return id;
}
const open = {};
for (const site of sites) {
  const reach = site.reach ?? 40,
    near = (p) => Math.hypot(p[0] - site.point[0], p[2] - site.point[1]) < reach;
  const count = new Map(),
    edges = new Map();
  for (const tri of embankments[site.railway]) {
    // Zero-area slivers standing in a vertical plane (left by the traced triangulation) carry no edge.
    const area = Math.abs(
      (tri[1][0] - tri[0][0]) * (tri[2][2] - tri[0][2]) - (tri[2][0] - tri[0][0]) * (tri[1][2] - tri[0][2])
    );
    if (area < 2e-4) continue;
    for (let i = 0; i < 3; i++) {
      const a = tri[i],
        b = tri[(i + 1) % 3];
      if (!near(a) && !near(b)) continue;
      const k = [key(a), key(b)].sort().join('|');
      count.set(k, (count.get(k) || 0) + 1);
      edges.set(k, [a, b, tri[(i + 2) % 3], tri]);
    }
  }
  const faced = new Set();
  // The detailed railways' own retaining edges carry brick faces (great-eastern.js).
  for (const [a, b] of data.infrastructure.railways.find((r) => r.name === site.railway).retainingEdges || [])
    faced.add([key(a), key(b)].sort().join('|'));
  for (const tri of walls[site.railway] || [])
    for (let i = 0; i < 3; i++) faced.add([key(tri[i]), key(tri[(i + 1) % 3])].sort().join('|'));
  let n = 0,
    worst = 0;
  // A topological boundary edge is only open if the ground beside it, on the side away from its own
  // triangle, carries no other embankment triangle (T-junctions and slivers left by the traced
  // triangulation and by clipping are not openings).
  // An added route that continues a line (the LT&SR west of Bow Creek, data/maps/railway-levels.json) covers
  // the cross-section where the two embankments meet.
  const related = Object.keys(embankments).filter(
    (n) => n === site.railway || n.startsWith(site.railway + ',') || site.railway.startsWith(n + ',')
  );
  const local = related.flatMap((n) => embankments[n]).filter((tri) => tri.some(near));
  function covered(x, z, own) {
    for (const tri of local) {
      if (tri === own) continue;
      const [p, q, r] = tri,
        det = (q[0] - p[0]) * (r[2] - p[2]) - (r[0] - p[0]) * (q[2] - p[2]);
      if (Math.abs(det) < 1e-9) continue;
      const u = ((x - p[0]) * (r[2] - p[2]) - (r[0] - p[0]) * (z - p[2])) / det,
        v = ((q[0] - p[0]) * (z - p[2]) - (x - p[0]) * (q[2] - p[2])) / det;
      if (u >= -1e-6 && v >= -1e-6 && u + v <= 1 + 1e-6) return true;
    }
    return false;
  }
  function outsideCovered(k) {
    const [a, b, c, own] = edges.get(k),
      dx = b[0] - a[0],
      dz = b[2] - a[2],
      len = Math.hypot(dx, dz);
    let nx = -dz / len,
      nz = dx / len;
    if ((c[0] - a[0]) * nx + (c[2] - a[2]) * nz > 0) [nx, nz] = [-nx, -nz];
    return [0.25, 0.5, 0.75].every((t) => covered(a[0] + dx * t + nx * 0.05, a[2] + dz * t + nz * 0.05, own));
  }
  for (const [k, c] of count) {
    if (c !== 1 || faced.has(k)) continue;
    const [a, b] = edges.get(k);
    if (outsideCovered(k)) continue;
    const rise = Math.max(a[1] - level(a[0], a[2]), b[1] - level(b[0], b[2]));
    if (rise > 0.5) {
      if (process.env.DEBUG)
        console.log(site.railway, JSON.stringify([a, b].map((p) => p.map((v) => +v.toFixed(2)))), rise.toFixed(2));
      n++;
      worst = Math.max(worst, rise);
    }
  }
  open[`${site.railway} @ ${site.point.map((v) => v.toFixed(0)).join(',')}`] = {
    openEdges: n,
    worstRise: +worst.toFixed(2),
  };
}
assert(
  Object.values(open).every((o) => o.openEdges === 0),
  `open raised embankment edges at recorded ends and bridges: ${JSON.stringify(open)}`
);

console.log(
  JSON.stringify(
    {
      embankmentTriangles: Object.fromEntries(Object.entries(embankments).map(([k, v]) => [k, v.length])),
      wallTriangles: Object.fromEntries(Object.entries(walls).map(([k, v]) => [k, v.length])),
      overWater,
      bowCreekDeck: deck,
      formationConflicts: [...conflicts],
      openEdges: open,
      railwayBridges: review.railwayBridges,
    },
    null,
    1
  )
);
console.log('Railway embankment check passed.');
