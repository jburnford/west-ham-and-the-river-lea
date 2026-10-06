// Volume flooding (FLOOD_MODEL_PLAN.md section 4.6, Phase V): the router on a hand-built model, then the acceptance
// cases on the built 1900 model: volume conserved, monotone inputs, no water above its basin level, and the author's
// cases (Mill Meads wets early, a just-overtopping surge part-fills it, the pumping-station ground is dry on an
// ordinary day).
import assert from 'node:assert/strict';
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { basinModel, routeFlood, volumeAt, levelAt, wetQuads } from '../docs/lib/flood-volume.js';

const close = (a, b, tol, what) => assert(Math.abs(a - b) <= tol, `${what}: ${a} vs ${b}`);
const balance = (L) => {
  const inn = L.rain + L.tide + L.river,
    out = L.stored + L.spilled + L.returned + L.drained + L.unrouted;
  return Math.abs(inn - out) / Math.max(1, inn);
};

// Two box hollows: A (10 ha, floor 0) and B (30 ha, floor 0.5) meet at 1.0 m and form P, which spills to the tidal
// outlet T over a 100 m crest (50 two-metre edges) at 2.0 m.
function synthetic({ sluice = false } = {}) {
  const step = 0.05,
    grid = { baseODN: 0, step, count: 61, topODN: 3 },
    at = (k) => k * step;
  const range = (k0, k1, f) => Array.from({ length: k1 - k0 + 1 }, (_, n) => f(at(k0 + n)));
  const VA = (h) => 1e5 * Math.max(0, h),
    VB = (h) => 3e5 * Math.max(0, h - 0.5);
  const tables = [range(0, 20, VA), range(9, 20, VB), [], range(20, 60, (h) => VA(h) + VB(h))];
  const offsets = [0];
  for (const t of tables) offsets.push(offsets.at(-1) + t.length);
  const volume = {
    levelGrid: grid,
    parameters: { weirCoefficient: 1.6, edgeWidthMetres: 2 },
    nodes: {
      count: 4,
      landLeaves: 2,
      outlets: 1,
      outletTidal: [true],
      parent: [3, 3, -1, -1],
      child0: [-1, -1, -1, 0],
      child1: [-1, -1, -1, 1],
      spillODN: [1, 1, null, 2],
      formationODN: [null, null, null, 1],
      lowestODN: [0, 0.5],
      spillTo: [1, 0, -1, 2],
      spillFrom: [0, 1, -1, 0],
      attached: [0, 0, 0, 1],
      catchmentM2: [1e6, 1e6],
      tableFirst: [0, 9, 0, 20],
      tableOffset: offsets.slice(0, 4),
      tableLength: tables.map((t) => t.length),
      crests: { 3: [[200, 50]] },
    },
    sluices: sluice ? [{ id: 's', leaf: 1, sillODN: 0, dischargeM3PerSecond: 0.1, outlet: 2 }] : [],
  };
  return basinModel(volume, Float32Array.from(tables.flat()));
}
const tide = { lowODN: -1, highODN: 1.5, riverLevelODN: 0 };
{
  const m = synthetic();
  close(volumeAt(m, 3, 1.5), 1e5 * 1.5 + 3e5, 1, 'parent table');
  close(levelAt(m, 0, 5e4), 0.5, 1e-6, 'level from volume');
  // 10 mm: each hollow keeps its own rain.
  let r = routeFlood(m, { ...tide, rainMm: 10 });
  close(r.levels[0], 0.1, 1e-6, 'A level');
  close(r.levels[1], 0.5 + 1 / 30, 1e-6, 'B level');
  // 150 mm: A overflows into B, both fill to the saddle, the rest stands in P above it.
  r = routeFlood(m, { ...tide, rainMm: 150 });
  close(r.levels[0], 1 + 5e4 / 4e5, 1e-6, 'merged level');
  assert.equal(r.levels[0], r.levels[1]);
  close(r.ledger.stored, 3e5, 1e-3, 'stored');
  // 1000 mm: P fills to its crest and the rest runs out to the tide.
  r = routeFlood(m, { ...tide, rainMm: 1000 });
  close(r.levels[0], 2, 1e-6, 'full at the crest');
  close(r.ledger.spilled, 2e6 - 6.5e5, 1e-3, 'spilled');
  // No tide over the crest at ordinary high water (1.5 < 2.0).
  r = routeFlood(m, { ...tide, surgeM: 0.4 });
  assert.equal(r.ledger.tide, 0);
  // A surge 5 cm over the crest for one tide puts a thin sheet in the bottom of A, not a full basin.
  r = routeFlood(m, { ...tide, surgeM: 0.55 });
  assert(r.ledger.tide > 0 && r.levels[0] < 1, `thin sheet ${r.levels[0]}`);
  assert.equal(r.levels[1] < 0, true, 'B stays dry until A spills');
  // A long high surge fills P to the tide and no higher; the rest goes back.
  r = routeFlood(m, { ...tide, surgeM: 1, tides: 6 });
  close(r.levels[0], 2.5, 1e-6, 'level of the surge');
  assert(r.ledger.returned > 0);
  // A sluice drains B only while the tide outside is below its sill.
  const s = synthetic({ sluice: true });
  r = routeFlood(s, { ...tide, rainMm: 100 });
  assert(r.ledger.drained > 0 && r.ledger.drained < 1e5);
  close(r.ledger.drained, 0.1 * 3600 * 12.42 * (Math.acos(0.2) / Math.PI), 30, 'tide-locked window');
  const locked = routeFlood(s, { ...tide, lowODN: 0.1, rainMm: 100 });
  assert.equal(locked.ledger.drained, 0);
  for (const out of [r, locked]) assert(balance(out.ledger) < 1e-9);
}

// The built model.
const D = new URL('../docs/data/', import.meta.url);
const meta = JSON.parse(readFileSync(new URL('landscape-flood-1900.json', D)));
assert.equal(meta.schemaVersion, 3);
const file = (key) => readFileSync(new URL(meta.files[key], D));
const m = basinModel(meta.volume, new Float32Array(file('basinVolumes').buffer.slice(0)));
const ids = new Uint16Array(file('fineBasin').buffer.slice(0)),
  bedRaw = new Uint16Array(file('fineBed').buffer.slice(0)),
  none = meta.encoding.none,
  bed = Float32Array.from(bedRaw, (v) => (v === none ? NaN : v / 100 - 10)),
  F = meta.fine;
assert(ids.every((v) => v <= m.nLeaf));
// Basin cells without stored ground stand above the 8 m ODN cap (the sewer bank and the high ground west of the Lea,
// as in the Phase 1 grid): never wet.
let capped = 0;
for (let i = 0; i < ids.length; i++) if (ids[i] && !Number.isFinite(bed[i])) capped++;
assert(capped < 0.15 * ids.length, `${capped} basin cells without ground`);
for (let i = 0; i < m.count; i++) {
  const t = m.tables.subarray(m.tableOffset[i], m.tableOffset[i] + m.tableLength[i]);
  for (let k = 1; k < t.length; k++) assert(t[k] >= t[k - 1] - 1e-3, `table ${i} not monotone`);
}
const base = {
  lowODN: meta.volume.tideODN.low,
  highODN: meta.volume.tideODN.high,
  riverLevelODN: meta.volume.scenarios.presets[0].riverLevelODN,
};
const cell = (x, z) => Math.floor((z - F.bounds[1]) / 2) * F.width + Math.floor((x - F.bounds[0]) / 2);
const meadsLeaf = ids[cell(-300, 200)] - 1,
  meads = m.top[meadsLeaf],
  stationCell = cell(-181, -14),
  station = ids[stationCell] - 1;
assert(meadsLeaf >= 0 && meadsLeaf < m.nLand && m.attached[meads]);
const run = (inputs) => routeFlood(m, { ...base, ...inputs });

// Conservation and monotonicity over a grid of inputs.
const rains = [0, 5, 10, 20, 35, 50, 80, 150],
  surges = [0, 0.2, 0.4, 0.6, 1, 1.7],
  durations = [1, 2, 6],
  rivers = [1.895, 2.5, 3.4];
let worst = 0;
const results = new Map();
for (const tides of durations)
  for (const riverLevelODN of rivers)
    for (const surgeM of surges)
      for (const rainMm of rains) {
        const r = run({ rainMm, surgeM, tides, riverLevelODN });
        worst = Math.max(worst, balance(r.ledger));
        assert(r.levels.every(Number.isFinite));
        assert(r.ledger.unrouted === 0);
        results.set(`${tides}|${riverLevelODN}|${surgeM}|${rainMm}`, r.levels);
      }
assert(worst < 1e-3, `volume balance ${worst}`);
const higher = (a, b, what) => {
  for (let i = 0; i < m.nLeaf; i++) assert(b[i] >= a[i] - 1e-6, `${what}: basin ${i} ${a[i]} -> ${b[i]}`);
};
for (const tides of durations)
  for (const riverLevelODN of rivers)
    for (const surgeM of surges)
      rains.slice(1).forEach((rain, n) => {
        const key = (rr, s = surgeM, t = tides) => `${t}|${riverLevelODN}|${s}|${rr}`;
        higher(results.get(key(rains[n])), results.get(key(rain)), 'more rain');
        const si = surges.indexOf(surgeM);
        if (si) higher(results.get(key(rain, surges[si - 1])), results.get(key(rain)), 'higher surge');
      });
for (const riverLevelODN of rivers)
  for (const surgeM of surges)
    for (const rainMm of [0, 50]) {
      // Longer storms add sluice time, so only the tide and the river are checked for duration.
      const at = (t) => results.get(`${t}|${riverLevelODN}|${surgeM}|${rainMm}`);
      if (!rainMm) (higher(at(1), at(2), 'longer'), higher(at(2), at(6), 'longer'));
    }

// No water on ground above its level: every wet corner of the drawn surface stands at its basin level, above ground.
const storm = run({ rainMm: 50, tides: 6 });
const surface = wetQuads(
  { ids, bed, width: F.width, height: F.height, x0: F.bounds[0], z0: F.bounds[1], step: F.step },
  storm.levels
);
const maxLevel = Math.max(...storm.levels);
for (let k = 0; k < surface.depths.length; k++) assert(surface.positions[3 * k + 1] <= maxLevel + 1e-6);

// The author's cases.
const ordinary = run({ rainMm: 0, tides: 1 });
const modest = run({ rainMm: 20, tides: 1 });
assert(ordinary.levels[meadsLeaf] < m.lowest[meadsLeaf], 'Mill Meads dry on an ordinary day');
assert(modest.levels[meadsLeaf] > m.lowest[meadsLeaf] + 0.1, 'modest rain wets the lowest Mill Meads hollow');
assert(modest.levels[meadsLeaf] < m.spill[meads] - 1, 'modest rain leaves Mill Meads far from full');
const crest = m.spill[meads],
  justOver = run({ surgeM: Math.ceil((crest - base.highODN + 0.05) * 20) / 20, tides: 1 });
assert(justOver.ledger.tide > 0);
assert(
  justOver.levels[meadsLeaf] < crest - 1,
  `a just-overtopping surge part-fills Mill Meads (${justOver.levels[meadsLeaf]})`
);
const groundAtStation = bed[stationCell];
assert(ordinary.levels[station] < groundAtStation, 'pumping-station ground dry on an ordinary day');
let stationRain = null;
for (let rain = 0; rain <= 150 && stationRain === null; rain += 5)
  if (run({ rainMm: rain, tides: 1 }).levels[station] > groundAtStation + 0.015) stationRain = rain;

const presets = Object.fromEntries(
  meta.volume.scenarios.presets.map((p) => {
    const r = run(p);
    return [
      p.id,
      {
        meadsLevelODN: +r.levels[meadsLeaf].toFixed(3),
        ledger: Object.fromEntries(Object.entries(r.ledger).map(([k, v]) => [k, Math.round(v)])),
      },
    ];
  })
);
const report = {
  status: 'PASS',
  worstVolumeBalance: worst,
  millMeads: {
    crestODN: crest,
    lowestODN: m.lowest[meadsLeaf],
    modestRain20mmLevelODN: modest.levels[meadsLeaf],
    justOvertoppingSurgeLevelODN: justOver.levels[meadsLeaf],
  },
  pumpingStation: {
    groundODN: groundAtStation,
    sameHollowAsMillMeads: station === meadsLeaf,
    firstWetRainMmOneTide: stationRain,
  },
  presets,
  checks: [
    'hand-built model: own rain, spill, merge, crest overflow, thin surge sheet, surge cap, tide-locked sluice',
    'tables monotone; basin cells have ground or stand above the storage cap',
    'volume conserved to 0.1% over 432 input combinations',
    'monotone in rain and surge; in duration for the tide and river',
    'no drawn water above its basin level',
    "author's cases: Mill Meads wets at modest rain and part-fills on a just-overtopping surge; pumping station dry on an ordinary day",
  ],
};
const out = new URL('../scenes/channelsea-sewer-panorama/review/', import.meta.url);
mkdirSync(out, { recursive: true });
writeFileSync(new URL('flood-volume-checks.json', out), JSON.stringify(report, null, 2) + '\n');
console.log(
  `Volume flooding checks passed (balance ${worst.toExponential(1)}; Mill Meads ${modest.levels[meadsLeaf].toFixed(2)} m ODN at 20 mm; pumping-station ground first wet at ${stationRain} mm in one tide).`
);
