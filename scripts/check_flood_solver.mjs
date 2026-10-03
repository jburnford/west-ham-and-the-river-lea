import assert from 'node:assert/strict';
import { FloodModel, culvertDischarge, parameters } from '../docs/flood-solver.js';
const small = (w, h, bed) => ({
  epoch: '1900',
  width: w,
  height: h,
  cellSizeMetres: 2,
  bed,
  kind: Array(w * h).fill(0),
  boundaries: [],
  manningField: 0.055,
});
const near = (a, b, e = 1e-7) => assert(Math.abs(a - b) < e, `${a} != ${b}`);
// Lake at rest over uneven submerged ground: pressure gradient must be zero.
const uneven = small(
  12,
  8,
  Array.from({ length: 96 }, (_, i) => (i % 7) * 0.06)
);
let m = new FloodModel(
  uneven,
  {},
  uneven.bed.map((z) => 1 - z)
);
m.advance(120);
for (let i = 0; i < m.n; i++) near(m.h[i] + m.bed[i], 1);
near(m.stats().massError, 0);
// Uniform rainfall has an exact storage solution, including initially dry cells.
m = new FloodModel(small(10, 10, Array(100).fill(0)), { preset: 'rain', rain: 36 });
m.advance(100);
for (const h of m.h) near(h, 0.001);
near(m.stats().massError, 0);
// A continuous wall must not leak into lower, disconnected ground.
const wall = small(
  9,
  5,
  Array.from({ length: 45 }, (_, i) => (i % 9 === 4 ? 3 : 0))
);
m = new FloodModel(
  wall,
  {},
  wall.bed.map((_, i) => (i % 9 < 4 ? 1 : 0))
);
m.advance(120);
for (let i = 0; i < m.n; i++) if (i % 9 > 4) near(m.h[i], 0);
near(m.stats().massError, 0);
// Wetting a dry bed preserves water and nonnegative depths.
const dry = small(20, 4, Array(80).fill(0));
m = new FloodModel(
  dry,
  {},
  dry.bed.map((_, i) => (i % 20 < 4 ? 0.4 : 0))
);
m.advance(120);
assert(m.h.every((h) => h >= 0 && Number.isFinite(h)));
assert(m.h.some((h, i) => i % 20 > 10 && h > 0.01));
near(m.stats().massError, 0);
// A culvert bypasses a barrier only when its gate allows it.
const c = {
  eastCell: 2,
  westCell: 0,
  eastInvertODN: 0.1,
  westInvertODN: 0,
  widthMetres: 0.9,
  heightMetres: 0.6,
  lengthMetres: 45,
};
const link = { ...small(3, 1, [0, 10, 0.1]), culvert: c };
for (const gate of ['east-to-west', 'both', 'blocked']) {
  const f = new FloodModel(link, { gate }, [0.2, 0, 0.9]);
  f.advance(10);
  near(f.stats().massError, 0);
  assert(f.h.every((h) => h >= 0));
  if (gate === 'blocked') near(f.h[0], 0.2);
  else assert(f.h[0] > 0.2);
}
const p = parameters(link);
assert(culvertDischarge(c, 0.3, 1, p, link) === 0);
assert(culvertDischarge(c, 0.3, 1, { ...p, gate: 'both' }, link) < 0);
assert(culvertDischarge(c, 0.05, 0, p, link) === 0);
assert(culvertDischarge({ ...c, lengthMetres: 90 }, 1, 0.2, p, link) < culvertDischarge(c, 1, 0.2, p, link));
near(culvertDischarge(c, 1, 0.2, p, link), culvertDischarge(c, 1.3, 0.5, { ...p, verticalShift: 0.3 }, link));
// Withdrawals are counted and cannot pump a cell below its bed.
m = new FloodModel(link, { pump: true, gate: 'blocked' }, [0, 0, 0.1]);
m.advance(20);
assert(m.pumpVolume > 0);
near(m.stats().massError, 0);
assert(m.h[2] >= 0);
// A prescribed stage is a logged source, not an overwrite of cell depth.
const open = { ...small(8, 2, Array(16).fill(0)), boundaries: [{ cell: 0, side: 'west', width: 2 }] };
m = new FloodModel(open);
m.advance(120);
assert(m.boundaryIn > 0);
near(m.stats().massError, 0);
assert.throws(() => new FloodModel({ ...open, epoch: '1928' }), /1900/);
assert.throws(() => new FloodModel(open, { peak: NaN }), /Invalid/);
// Smooth shallow-water motion should converge under a halved time step.
const wave = small(40, 2, Array(80).fill(0)),
  initial = wave.bed.map((_, i) => 0.5 + 0.05 * Math.cos((Math.PI * ((i % 40) + 0.5)) / 40));
const coarse = new FloodModel(wave, {}, initial),
  fine = new FloodModel(wave, {}, initial);
while (coarse.time < 60 - 1e-8) coarse.step(Math.min(0.5, 60 - coarse.time));
while (fine.time < 60 - 1e-8) fine.step(Math.min(0.25, 60 - fine.time));
const rms = Math.sqrt(coarse.h.reduce((s, h, i) => s + (h - fine.h[i]) ** 2, 0) / coarse.n);
assert(rms < 0.002, `Time-step convergence failed: ${rms}`);
near(coarse.stats().massError, 0);
near(fine.stats().massError, 0);
console.log(
  `PASS: lake at rest, analytic rain storage, impermeable wall, wetting/drying, conservative culvert, gate reversal, pipe resistance, datum consistency, pumping, logged boundaries and time-step refinement (RMS ${rms.toExponential(2)} m).`
);
