// Volume flooding over the basin hierarchy (FLOOD_MODEL_PLAN.md section 4.6, Phase V).
// scripts/flood_basins.py splits the ground into hollows that merge at their saddles; each has a stage-volume table.
// Water arrives as volumes and fills the lowest ground first:
// - rain: a storm total on each hollow's catchment, less what the marsh sluices drain in the low-water windows;
// - the tide (raised by a surge) and the river: weir flow over each crest while the source stands above it.
// A full hollow spills into the hollow across its saddle, or out to the water it is attached to. Pure functions:
// the page and the checks call them with the same model.

export const TIDE_PERIOD_HOURS = 12.42;
const EPS = 1e-6;
const STEPS_PER_TIDE = 372; // two-minute steps
const DRY = -100;

// Typed copies of the builder's description and quick lookups. `volumes` is the Float32 table file.
export function basinModel(volume, volumes) {
  const n = volume.nodes,
    count = n.count,
    nLand = n.landLeaves,
    nLeaf = nLand + n.outlets,
    grid = volume.levelGrid;
  const num = (a) => Float64Array.from(a, (v) => (v === null ? Infinity : v));
  const model = {
    count,
    nLand,
    nLeaf,
    grid,
    parameters: volume.parameters,
    parent: Int32Array.from(n.parent),
    child0: Int32Array.from(n.child0),
    child1: Int32Array.from(n.child1),
    spill: num(n.spillODN),
    formation: num(n.formationODN),
    lowest: Float64Array.from(n.lowestODN),
    spillTo: Int32Array.from(n.spillTo),
    spillFrom: Int32Array.from(n.spillFrom),
    attached: Uint8Array.from(n.attached),
    catchment: Float64Array.from(n.catchmentM2),
    tableFirst: Int32Array.from(n.tableFirst),
    tableOffset: Int32Array.from(n.tableOffset),
    tableLength: Int32Array.from(n.tableLength),
    tables: volumes instanceof Float32Array ? volumes : new Float32Array(volumes),
    outletTidal: n.outletTidal,
    crests: new Map(Object.entries(n.crests).map(([k, v]) => [Number(k), v])),
    sluices: volume.sluices,
  };
  // The attached basin at the top of each node's subtree, and each node's sluices (a sluice drains every basin that
  // contains its hollow).
  model.top = new Int32Array(count);
  for (let i = 0; i < count; i++) {
    let m = i;
    while (model.parent[m] >= 0) m = model.parent[m];
    model.top[i] = m;
  }
  model.sluicesUnder = Array.from({ length: count }, () => []);
  volume.sluices.forEach((s, k) => {
    for (let m = s.leaf; m >= 0; m = model.parent[m]) model.sluicesUnder[m].push(k);
  });
  model.capacity = new Float64Array(count);
  for (let i = 0; i < count; i++) {
    if (isOutlet(model, i)) continue;
    const limit = Number.isFinite(model.spill[i]) ? model.spill[i] : grid.topODN;
    model.capacity[i] = volumeAt(model, i, limit);
  }
  // Attached basins in the order the tide reaches them: by crest level, then by how far they sit from the water.
  const hops = (r) => {
    let k = 0;
    for (let m = r; !isOutlet(model, m); m = model.top[model.spillTo[m]]) k++;
    return k;
  };
  model.attachOrder = [...Array(count).keys()]
    .filter((i) => model.attached[i])
    .sort((a, b) => model.spill[a] - model.spill[b] || hops(a) - hops(b) || a - b);
  return model;
}

export function isOutlet(model, i) {
  return i >= model.nLand && i < model.nLeaf;
}

// Volume in basin i (its whole subtree) when it stands at level h, from its table (linear between 5 cm steps).
export function volumeAt(model, i, h) {
  const length = model.tableLength[i];
  if (!length) return 0;
  const k = (h - model.grid.baseODN) / model.grid.step - model.tableFirst[i],
    o = model.tableOffset[i],
    t = model.tables;
  if (k <= 0) return Math.max(0, t[o]);
  if (k >= length - 1) return t[o + length - 1];
  const j = Math.floor(k),
    f = k - j;
  return t[o + j] * (1 - f) + t[o + j + 1] * f;
}

// The level of basin i holding volume v: the inverse of volumeAt.
export function levelAt(model, i, v) {
  const length = model.tableLength[i],
    o = model.tableOffset[i],
    t = model.tables,
    base = model.grid.baseODN + model.tableFirst[i] * model.grid.step,
    step = model.grid.step;
  if (!length || v <= t[o]) return v > 0 ? base : DRY;
  for (let j = 1; j < length; j++)
    if (t[o + j] >= v) return base + step * (j - 1 + (v - t[o + j - 1]) / Math.max(EPS, t[o + j] - t[o + j - 1]));
  return base + step * (length - 1);
}

// The tide (ODN) at time t hours after low water: the docs/tides.js cosine, its high water raised by the surge.
export function tideAt(t, { lowODN, highODN, surgeM = 0 }) {
  const phase = t / TIDE_PERIOD_HOURS;
  return lowODN + ((highODN + surgeM - lowODN) * (1 - Math.cos(phase * Math.PI * 2))) / 2;
}

// Weir flow (m³/s) over a crest profile [[levelCm, edges], ...] from water standing at h on the source side.
export function crestFlow(profile, h, coefficient, edgeWidth) {
  let q = 0;
  for (const [cm, edges] of profile) {
    const head = h - cm / 100;
    if (head > 0) q += coefficient * edgeWidth * edges * head ** 1.5;
  }
  return q;
}

// Route one scenario. inputs: rainMm (storm total), tides (duration, in tides), surgeM, riverLevelODN, and the tide
// range lowODN/highODN. Returns the level of every leaf and outlet (DRY when empty), the stored volume of every
// basin, and the volume ledger.
export function routeFlood(model, inputs) {
  const { rainMm = 0, tides = 1, surgeM = 0, riverLevelODN, lowODN, highODN } = inputs;
  const p = model.parameters,
    count = model.count,
    vol = new Float64Array(count),
    overFull = new Uint8Array(count),
    sourceKind = new Array(count),
    hours = tides * TIDE_PERIOD_HOURS,
    dt = TIDE_PERIOD_HOURS / STEPS_PER_TIDE,
    tide = { lowODN, highODN, surgeM },
    ledger = { rain: 0, tide: 0, river: 0, stored: 0, spilled: 0, returned: 0, drained: 0, unrouted: 0 };
  const outsideLevel = (outlet, t) => (model.outletTidal[outlet - model.nLand] ? tideAt(t, tide) : riverLevelODN);

  // Sluices run while the water outside stands below the sill (tide-locking), at their estimated discharge.
  const remaining = model.sluices.map((s) => {
    let open = 0;
    for (let k = 0; k < STEPS_PER_TIDE; k++) if (outsideLevel(s.outlet, (k + 0.5) * dt) < s.sillODN) open += dt;
    return s.dischargeM3PerSecond * open * 3600 * tides;
  });
  const add = (i, v) => {
    for (let m = i; m >= 0; m = model.parent[m]) vol[m] += v;
  };
  const full = (i) => vol[i] >= model.capacity[i] - EPS;

  // Pour v into node `start`. `root` and `limit` are set for water from a source: at that attached basin the water
  // may stand above the crest, up to the source's level; what it cannot hold goes back to the source.
  function pour(v, start, root = -1, limit = -Infinity) {
    let i = start;
    while (v > EPS) {
      if (isOutlet(model, i)) {
        ledger.spilled += v;
        return;
      }
      for (const s of model.sluicesUnder[i]) {
        const d = Math.min(v, remaining[s]);
        remaining[s] -= d;
        ledger.drained += d;
        v -= d;
      }
      if (v <= EPS) return;
      const room = model.capacity[i] - vol[i];
      if (room > EPS) {
        const a = Math.min(room, v);
        add(i, a);
        v -= a;
        if (v <= EPS) return;
      }
      if (i === root) {
        const extra = Math.max(0, volumeAt(model, i, limit) - vol[i]),
          a = Math.min(extra, v);
        if (a > 0) {
          add(i, a);
          overFull[i] = 1;
        }
        ledger.returned += v - a;
        return;
      }
      const parent = model.parent[i];
      if (parent >= 0) {
        const sibling = model.child0[parent] === i ? model.child1[parent] : model.child0[parent];
        i = full(sibling) ? parent : model.spillTo[i];
      } else if (model.spillTo[i] >= 0) i = model.spillTo[i];
      else {
        ledger.unrouted += v;
        return;
      }
    }
  }

  // Rain on every hollow's catchment.
  for (let leaf = 0; leaf < model.nLand; leaf++) {
    const v = (rainMm / 1000) * model.catchment[leaf];
    ledger.rain += v;
    pour(v, leaf);
  }

  // Sources over the crests, from the water outwards.
  for (const r of model.attachOrder) {
    const target = model.spillTo[r],
      profile = model.crests.get(r);
    if (!profile) continue;
    let kind, cap;
    if (isOutlet(model, target)) {
      kind = model.outletTidal[target - model.nLand] ? 'tide' : 'river';
      cap = kind === 'tide' ? highODN + surgeM : riverLevelODN;
    } else {
      // Ground that drains to water only carries the source on if the source already stands in it.
      const above = model.top[target];
      if (!overFull[above]) continue;
      kind = sourceKind[above];
      cap = levelAt(model, above, vol[above]);
    }
    if (cap <= model.spill[r] + EPS) continue;
    let inflow = 0;
    if (kind === 'tide') {
      for (let k = 0; k < STEPS_PER_TIDE; k++)
        inflow +=
          crestFlow(profile, Math.min(cap, tideAt((k + 0.5) * dt, tide)), p.weirCoefficient, p.edgeWidthMetres) * dt;
      inflow *= 3600 * tides;
    } else inflow = crestFlow(profile, cap, p.weirCoefficient, p.edgeWidthMetres) * hours * 3600;
    ledger[kind] += inflow;
    sourceKind[r] = kind;
    pour(inflow, model.spillFrom[r], r, cap);
  }

  // Levels: a basin whose own lake stands above its formation level sets the level of everything below it.
  const levels = new Float64Array(model.nLeaf).fill(DRY);
  function resolve(i, inherited) {
    if (isOutlet(model, i)) return;
    if (i < model.nLand) {
      levels[i] = inherited ?? levelAt(model, i, vol[i]);
      return;
    }
    const a = model.child0[i],
      b = model.child1[i];
    let own = inherited;
    if (own === null && vol[i] > vol[a] + vol[b] + EPS) own = levelAt(model, i, vol[i]);
    resolve(a, own);
    resolve(b, own);
  }
  for (let i = 0; i < count; i++) if (model.parent[i] < 0 && !isOutlet(model, i)) resolve(i, null);
  for (let i = model.nLand; i < model.nLeaf; i++)
    levels[i] = model.outletTidal[i - model.nLand] ? highODN + surgeM : riverLevelODN;
  for (let i = 0; i < count; i++) if (model.parent[i] < 0 && !isOutlet(model, i)) ledger.stored += vol[i];
  return { levels, volumes: vol, overFull, ledger };
}

// Water surface for one grid (fine 2 m or regional 10 m): a quad between every four cell centres with a wet corner.
// Each corner stands at its basin's level when wet, or at the highest wet level of the quad when dry, and carries
// its depth (level - ground; negative when dry) so the shader can cut the shoreline where the interpolated depth
// crosses zero. ids hold basin id + 1 (0: none); bed holds ODN ground (NaN: none). `skip(x, z)` drops quads (the
// regional grid inside the fine box). Returns { positions (x, odn, z), depths, indices, quads }.
export function wetQuads({ ids, bed, width, height, x0, z0, step }, levels, minDepth = 0.015, skip = null) {
  const level = new Float32Array(width * height).fill(NaN);
  for (let i = 0; i < level.length; i++) {
    const id = ids[i];
    if (id && Number.isFinite(bed[i]) && levels[id - 1] > bed[i] + minDepth) level[i] = levels[id - 1];
  }
  const positions = [],
    depths = [],
    indices = [];
  const corner = [0, 1, width, width + 1];
  let quads = 0;
  for (let j = 0; j < height - 1; j++)
    for (let i = 0; i < width - 1; i++) {
      const c = j * width + i;
      let top = -Infinity;
      for (const k of corner) if (level[c + k] > top) top = level[c + k];
      if (top === -Infinity) continue;
      const x = x0 + (i + 0.5) * step,
        z = z0 + (j + 0.5) * step;
      if (skip && skip(x + step / 2, z + step / 2)) continue;
      const base = positions.length / 3;
      corner.forEach((k, n) => {
        const y = Number.isNaN(level[c + k]) ? top : level[c + k],
          ground = Number.isFinite(bed[c + k]) ? bed[c + k] : y + 10;
        positions.push(x + (n & 1) * step, y, z + (n >> 1) * step);
        depths.push(y - ground);
      });
      indices.push(base, base + 2, base + 1, base + 1, base + 2, base + 3);
      quads++;
    }
  return {
    positions: Float32Array.from(positions),
    depths: Float32Array.from(depths),
    indices: Uint32Array.from(indices),
    quads,
  };
}
