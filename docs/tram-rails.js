// Horse-tram rails on Stratford High Street, about 1900. Register: docs/data/tram-rails.json.
// Flush grooved rails only: no poles, wires, cars or horses. The OS five-foot plan draws
// double track; the gauge, rail widths, rise and colours are documented estimates.
// The rails follow the High Street route in infrastructure.json at run time and sit on the
// sett surface the reader sees (road triangles or bridge deck), a few millimetres proud.
import { highStreetSurfaceHeight } from './sewer-levels.js';
import { roadProfileHeight } from './road-levels.js';

const MAX_STEP = 4, // metres between cross-sections on plain road
  MIN_STEP = 0.05,
  FIT_TOLERANCE = 0.002, // metres; subdivide until the rail follows the surface this closely
  DECK_TOP = 0.02, // bridge deck sett layer: infrastructure.js draws a 0.02 m box at bridge.height
  ROAD_OFFSET = 0.065, // infrastructure.js draws road triangles at ground + 0.065
  GAP_REACH = 0.75; // metres: widest hole in the drawn road the rails are carried across

// Mirrors ground() in infrastructure.js so the rails meet the road it draws.
// scripts/check_tram_rails.mjs compares the result with the real infrastructure meshes.
export function roadGround(data, level) {
  const infra = data.infrastructure,
    [x0, z0, x1, z1] = data.terrain.bounds,
    profiles = infra.roads.map((r) => r.elevationProfile).filter(Boolean),
    epoch = data.elevation?.meta.epoch;
  return (x, z) => {
    for (const p of profiles) {
      const y = roadProfileHeight(x, z, p, epoch);
      if (y !== null) return y - ROAD_OFFSET;
    }
    let h =
      data.mainLandscape?.weight(x, z) > 0
        ? level(x, z)
        : x >= x0 && x <= x1 && z >= z0 && z <= z1
          ? Math.max(0.12, level(x, z))
          : 0.12;
    const highStreet = highStreetSurfaceHeight(x, z, infra.sewerHighStreet);
    if (!data.mainLandscape || highStreet > 0.1850001) h = Math.max(h, highStreet - ROAD_OFFSET);
    for (const bridge of infra.roadBridges)
      for (let i = 1; i < bridge.route.length; i++) {
        const a = bridge.route[i - 1],
          b = bridge.route[i],
          dx = b[0] - a[0],
          dz = b[1] - a[1];
        const t = Math.max(0, Math.min(1, ((x - a[0]) * dx + (z - a[1]) * dz) / (dx * dx + dz * dz)));
        h = Math.max(h, bridge.height - ROAD_OFFSET - Math.hypot(x - a[0] - t * dx, z - a[1] - t * dz) * 0.12);
      }
    return h;
  };
}

// The named High Street routes joined end to end.
export function tramRoute(infra, names) {
  const roads = names.map((name) => {
    const road = infra.roads.find((r) => r.name === name);
    if (!road) throw new Error(`Tram route road missing: ${name}`);
    return road;
  });
  const route = roads[0].route.map((p) => [...p]);
  for (const road of roads.slice(1)) {
    const [a, b] = [route.at(-1), road.route[0]];
    if (Math.hypot(a[0] - b[0], a[1] - b[1]) > 0.05) throw new Error(`Tram route break before ${road.name}`);
    route.push(...road.route.slice(1).map((p) => [...p]));
  }
  return { route, width: Math.min(...roads.map((r) => r.width)) };
}

// Track centreline: the road route with each corner replaced by a circular curve, as rails are
// laid, so the gauge holds through the bends. Arcs are split finely enough to sag under 1 mm.
export function curvedPath(route, radius) {
  const path = [route[0]];
  for (let i = 1; i < route.length - 1; i++) {
    const [a, b, c] = [route[i - 1], route[i], route[i + 1]],
      la = Math.hypot(b[0] - a[0], b[1] - a[1]),
      lc = Math.hypot(c[0] - b[0], c[1] - b[1]),
      ua = [(b[0] - a[0]) / la, (b[1] - a[1]) / la],
      uc = [(c[0] - b[0]) / lc, (c[1] - b[1]) / lc],
      turn = Math.atan2(ua[0] * uc[1] - ua[1] * uc[0], ua[0] * uc[0] + ua[1] * uc[1]);
    if (Math.abs(turn) < 1e-4) {
      path.push(b);
      continue;
    }
    // Keep each curve within the middle of its two straights.
    const r = Math.min(radius, (0.45 * Math.min(la, lc)) / Math.tan(Math.abs(turn) / 2)),
      tangent = r * Math.tan(Math.abs(turn) / 2),
      start = [b[0] - ua[0] * tangent, b[1] - ua[1] * tangent],
      side = Math.sign(turn),
      centre = [start[0] - ua[1] * r * side, start[1] + ua[0] * r * side],
      steps = Math.max(1, Math.ceil(Math.abs(turn) / (2 * Math.acos(1 - 0.001 / r)))),
      a0 = Math.atan2(start[1] - centre[1], start[0] - centre[0]);
    for (let k = 0; k <= steps; k++) {
      const angle = a0 + (turn * k) / steps;
      path.push([centre[0] + r * Math.cos(angle), centre[1] + r * Math.sin(angle)]);
    }
  }
  path.push(route.at(-1));
  return path.filter((p, i) => i === 0 || Math.hypot(p[0] - path[i - 1][0], p[1] - path[i - 1][1]) > 1e-6);
}

// Bridge decks the rails cross, as oriented rectangles with their sett top level.
export function tramDecks(infra, ids) {
  return ids.flatMap((id) => {
    const bridge = infra.roadBridges.find((b) => b.id === id);
    if (!bridge) throw new Error(`Tram bridge missing: ${id}`);
    return bridge.route.slice(1).map((b, i) => {
      const a = bridge.route[i],
        length = Math.hypot(b[0] - a[0], b[1] - a[1]);
      return {
        id,
        a,
        ux: (b[0] - a[0]) / length,
        uz: (b[1] - a[1]) / length,
        length,
        width: bridge.width,
        top: bridge.height + DECK_TOP,
      };
    });
  });
}

export function deckAt(decks, x, z) {
  let best = null;
  for (const d of decks) {
    const along = (x - d.a[0]) * d.ux + (z - d.a[1]) * d.uz,
      across = -(x - d.a[0]) * d.uz + (z - d.a[1]) * d.ux;
    if (along >= 0 && along <= d.length && Math.abs(across) <= d.width / 2 && (!best || d.top > best.top)) best = d;
  }
  return best;
}

// Highest drawn road surface under a point: road triangles (linear between their vertices,
// as the mesh is drawn) or a bridge deck. Falls back to the ground formula if neither.
function surfaceSampler(data, ground, route, width, decks) {
  const reach = width / 2 + 2,
    cell = 8;
  let minX = Infinity,
    minZ = Infinity,
    maxX = -Infinity,
    maxZ = -Infinity;
  for (const [x, z] of route) {
    minX = Math.min(minX, x - reach);
    maxX = Math.max(maxX, x + reach);
    minZ = Math.min(minZ, z - reach);
    maxZ = Math.max(maxZ, z + reach);
  }
  const cols = Math.ceil((maxX - minX) / cell) + 1,
    rows = Math.ceil((maxZ - minZ) / cell) + 1,
    cells = new Map();
  for (const list of Object.values(data.infrastructure.roadSurfaces))
    for (const tri of list) {
      const xs = tri.map((p) => p[0]),
        zs = tri.map((p) => p[1]);
      const ax = Math.max(minX, Math.min(...xs)),
        bx = Math.min(maxX, Math.max(...xs)),
        az = Math.max(minZ, Math.min(...zs)),
        bz = Math.min(maxZ, Math.max(...zs));
      if (ax > bx || az > bz) continue;
      const entry = { tri, h: null };
      for (let j = Math.floor((az - minZ) / cell); j <= Math.floor((bz - minZ) / cell); j++)
        for (let i = Math.floor((ax - minX) / cell); i <= Math.floor((bx - minX) / cell); i++) {
          const key = j * cols + i;
          if (!cells.has(key)) cells.set(key, []);
          cells.get(key).push(entry);
        }
    }
  const segmentDistance = (x, z, a, b) => {
    const dx = b[0] - a[0],
      dz = b[1] - a[1],
      t = Math.max(0, Math.min(1, ((x - a[0]) * dx + (z - a[1]) * dz) / (dx * dx + dz * dz)));
    return Math.hypot(x - a[0] - t * dx, z - a[1] - t * dz);
  };
  return (x, z) => {
    const deck = deckAt(decks, x, z);
    let y = deck ? deck.top : -Infinity,
      kind = deck ? 'deck' : null,
      nearest = null;
    const ci = Math.floor((x - minX) / cell),
      cj = Math.floor((z - minZ) / cell);
    const visit = (i, j, home) => {
      if (i < 0 || j < 0 || i >= cols || j >= rows) return;
      for (const entry of cells.get(j * cols + i) || []) {
        const [a, b, c] = entry.tri;
        const det = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1]);
        if (Math.abs(det) < 1e-12) continue;
        const u = ((b[1] - c[1]) * (x - c[0]) + (c[0] - b[0]) * (z - c[1])) / det,
          v = ((c[1] - a[1]) * (x - c[0]) + (a[0] - c[0]) * (z - c[1])) / det,
          w = 1 - u - v;
        entry.h ||= entry.tri.map((p) => ground(p[0], p[1]) + ROAD_OFFSET);
        const h = u * entry.h[0] + v * entry.h[1] + w * entry.h[2];
        if (u < -1e-9 || v < -1e-9 || w < -1e-9) {
          if (kind !== null) continue;
          const d = Math.min(segmentDistance(x, z, a, b), segmentDistance(x, z, b, c), segmentDistance(x, z, c, a));
          if (!nearest || d < nearest.d) nearest = { d, h };
          continue;
        }
        if (home && h > y) {
          y = h;
          kind = 'road';
        }
      }
    };
    visit(ci, cj, true);
    if (kind !== null) return { y, kind };
    // Neighbouring cells only matter when looking for the nearest triangle across a hole.
    for (const di of [-1, 0, 1]) for (const dj of [-1, 0, 1]) if (di || dj) visit(ci + di, cj + dj, false);
    // A small hole in the drawn road (at the west end of Bow Bridge and a sliver at the Channelsea
    // approach junction): carry the rail across on the plane of the nearest road triangle.
    if (nearest && nearest.d <= GAP_REACH) return { y: nearest.h, kind: 'gap' };
    return { y: ground(x, z) + ROAD_OFFSET, kind: 'fallback' };
  };
}

// Pure geometry: positions, colours and indices of every rail strip, plus the edge lines the
// check measures. `spec` is docs/data/tram-rails.json.
export function buildTramRailGeometry({ data, level, spec }) {
  const infra = data.infrastructure,
    { track, rail } = spec,
    { route, width } = tramRoute(infra, spec.route.roads),
    path = curvedPath(route, track.curveRadiusMetres),
    decks = tramDecks(infra, spec.route.followsBridgeDecks),
    ground = roadGround(data, level),
    surface = surfaceSampler(data, ground, route, width, decks);
  // Lateral bands from the road centreline: per rail, lip | groove | head, groove on the gauge side.
  const g = track.gaugeMetres / 2,
    centres = track.form === 'double' ? [-track.trackCentreSpacingMetres / 2, track.trackCentreSpacingMetres / 2] : [0];
  const rails = [];
  centres.forEach((c, t) =>
    [-1, 1].forEach((side) => {
      const at = (d) => c + side * d;
      rails.push({
        track: t,
        side,
        strips: [
          ['lip', at(g - rail.grooveWidthMetres - rail.lipWidthMetres), at(g - rail.grooveWidthMetres)],
          ['groove', at(g - rail.grooveWidthMetres), at(g)],
          ['head', at(g), at(g + rail.headWidthMetres)],
        ],
      });
    })
  );
  const offsets = [...new Set(rails.flatMap((r) => r.strips.flatMap((s) => [s[1], s[2]])))];
  // Chainage of each track-centreline vertex.
  const chain = [0];
  for (let i = 1; i < path.length; i++)
    chain.push(chain[i - 1] + Math.hypot(path[i][0] - path[i - 1][0], path[i][1] - path[i - 1][1]));
  const total = chain.at(-1);
  const segmentNormal = (i) => {
    const [a, b] = [path[i], path[i + 1]],
      l = Math.hypot(b[0] - a[0], b[1] - a[1]);
    return [-(b[1] - a[1]) / l, (b[0] - a[0]) / l];
  };
  // A station's centre and offset direction; mitred at path vertices so offset lines stay parallel.
  function station(s) {
    let i = chain.findIndex((v, k) => k > 0 && v >= s - 1e-9) - 1;
    if (i < 0) i = path.length - 2;
    const t = (s - chain[i]) / (chain[i + 1] - chain[i]),
      p = [path[i][0] + (path[i + 1][0] - path[i][0]) * t, path[i][1] + (path[i + 1][1] - path[i][1]) * t];
    let n = segmentNormal(i),
      scale = 1;
    const vertex = Math.abs(s - chain[i + 1]) < 1e-6 ? i + 1 : Math.abs(s - chain[i]) < 1e-6 ? i : -1;
    if (vertex > 0 && vertex < path.length - 1) {
      const n1 = segmentNormal(vertex - 1),
        n2 = segmentNormal(vertex),
        m = [n1[0] + n2[0], n1[1] + n2[1]],
        l = Math.hypot(...m);
      n = [m[0] / l, m[1] / l];
      scale = 1 / (n[0] * n1[0] + n[1] * n1[1]);
    }
    const points = new Map();
    for (const o of offsets) {
      const x = p[0] + n[0] * o * scale,
        z = p[1] + n[1] * o * scale,
        { y, kind } = surface(x, z);
      points.set(o, { x, z, y: y + rail.headAboveSettsMetres, kind });
    }
    return { s, points };
  }
  // Fixed stations: path ends and vertices, and both sides of every deck end.
  const fixed = new Set(chain);
  for (const d of decks)
    for (let i = 1; i < path.length; i++) {
      const [a, b] = [path[i - 1], path[i]];
      const ua = (a[0] - d.a[0]) * d.ux + (a[1] - d.a[1]) * d.uz,
        ub = (b[0] - d.a[0]) * d.ux + (b[1] - d.a[1]) * d.uz;
      for (const edge of [0, d.length]) {
        if ((ua - edge) * (ub - edge) > 0 || ua === ub) continue;
        const f = (edge - ua) / (ub - ua),
          across = -(a[0] + (b[0] - a[0]) * f - d.a[0]) * d.uz + (a[1] + (b[1] - a[1]) * f - d.a[1]) * d.ux;
        if (Math.abs(across) > d.width / 2) continue;
        const s = chain[i - 1] + f * (chain[i] - chain[i - 1]);
        for (const e of [-MIN_STEP, -0.001, 0.001, MIN_STEP]) if (s + e > 0 && s + e < total) fixed.add(s + e);
      }
    }
  const sorted = [...fixed].sort((a, b) => a - b).filter((s, i, a) => i === 0 || s - a[i - 1] > 1e-6);
  const stations = [station(sorted[0])];
  // Adaptive subdivision: add a midpoint wherever a straight rail would leave the surface.
  function fill(a, b) {
    if (b.s - a.s <= MIN_STEP) return stations.push(b);
    const mid = station((a.s + b.s) / 2);
    const bad =
      b.s - a.s > MAX_STEP ||
      offsets.some((o) => {
        const pa = a.points.get(o),
          pb = b.points.get(o),
          pm = mid.points.get(o);
        return Math.abs((pa.y + pb.y) / 2 - pm.y) > FIT_TOLERANCE;
      });
    if (!bad) return stations.push(b);
    fill(a, mid);
    fill(mid, b);
  }
  for (let k = 1; k < sorted.length; k++) fill(stations.at(-1), station(sorted[k]));
  // Strips: two vertices per station (inner, outer edge), quads between stations.
  const colours = Object.fromEntries(
    Object.entries(rail.colours).map(([k, hex]) => [k, [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255)])
  );
  const positions = [],
    colors = [],
    indices = [];
  const fallbackAt = [],
    gapAt = [];
  let fallback = 0,
    gaps = 0,
    deckSamples = 0,
    minRise = Infinity,
    maxRise = -Infinity;
  for (const r of rails)
    for (const [name, inner, outer] of r.strips) {
      const base = positions.length / 3;
      stations.forEach((st, k) => {
        for (const o of [inner, outer]) {
          const p = st.points.get(o);
          positions.push(p.x, p.y, p.z);
          colors.push(...colours[name]);
          if (p.kind === 'fallback' && fallback++ < 5) fallbackAt.push([+p.x.toFixed(2), +p.z.toFixed(2)]);
          if (p.kind === 'gap' && gaps++ < 5) gapAt.push([+p.x.toFixed(2), +p.z.toFixed(2)]);
          if (p.kind === 'deck') deckSamples++;
        }
        if (k) {
          const q = base + (k - 1) * 2;
          // Upward-facing winding for either side of the centreline.
          if (outer > inner) indices.push(q, q + 1, q + 2, q + 1, q + 3, q + 2);
          else indices.push(q, q + 2, q + 1, q + 1, q + 2, q + 3);
        }
      });
    }
  // Rail height above the drawn surface halfway between stations (stations themselves are exact).
  // Intervals that straddle a deck end are skipped: there the rail steps within MIN_STEP.
  for (let k = 1; k < stations.length; k++)
    for (const o of offsets) {
      const pa = stations[k - 1].points.get(o),
        pb = stations[k].points.get(o);
      if (pa.kind !== pb.kind) continue;
      const rise = (pa.y + pb.y) / 2 - surface((pa.x + pb.x) / 2, (pa.z + pb.z) / 2).y;
      minRise = Math.min(minRise, rise);
      maxRise = Math.max(maxRise, rise);
    }
  // Edge lines for the check: gauge (running) edge and outer head edge of each rail.
  const lines = rails.map((r) => ({
    track: r.track,
    side: r.side,
    gauge: stations.map((st) => {
      const p = st.points.get(r.strips[2][1]);
      return [p.x, p.y, p.z];
    }),
    outer: stations.map((st) => {
      const p = st.points.get(r.strips[2][2]);
      return [p.x, p.y, p.z];
    }),
  }));
  return {
    positions: new Float32Array(positions),
    colors: new Float32Array(colors),
    indices: new Uint32Array(indices),
    route,
    width,
    decks,
    lines,
    review: {
      form: track.form,
      tracks: centres.length,
      rails: rails.length,
      gaugeMetres: track.gaugeMetres,
      trackCentreSpacingMetres: track.form === 'double' ? track.trackCentreSpacingMetres : 0,
      routeLengthMetres: Math.round(total * 10) / 10,
      stations: stations.length,
      vertices: positions.length / 3,
      triangles: indices.length / 3,
      deckSamples,
      fallbackSamples: fallback,
      fallbackAt,
      gapSamples: gaps,
      gapAt,
      riseMetres: [Math.round(minRise * 10000) / 10000, Math.round(maxRise * 10000) / 10000],
      bridges: spec.route.followsBridgeDecks,
      overhead: 'none',
      register: 'docs/data/tram-rails.json',
    },
  };
}

export function tramRails({ THREE, scene, data, level }) {
  const spec = data.tramRails;
  if (!spec) return null;
  const built = buildTramRailGeometry({ data, level, spec });
  // Register colours are sRGB; vertex colours are linear.
  const colour = new THREE.Color();
  for (let i = 0; i < built.colors.length; i += 3) {
    colour.setRGB(built.colors[i], built.colors[i + 1], built.colors[i + 2], THREE.SRGBColorSpace);
    built.colors.set([colour.r, colour.g, colour.b], i);
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(built.positions, 3));
  geometry.setAttribute('color', new THREE.BufferAttribute(built.colors, 3));
  geometry.setIndex(new THREE.BufferAttribute(built.indices, 1));
  geometry.computeVertexNormals();
  geometry.computeBoundingSphere();
  // Polygon offset keeps the thin strips in front of the setts at distance without lifting them.
  const material = new THREE.MeshStandardMaterial({
    vertexColors: true,
    roughness: 0.42,
    metalness: 0.35,
    polygonOffset: true,
    polygonOffsetFactor: -1,
    polygonOffsetUnits: -4,
  });
  material.userData.surface = 'tram-rails';
  const mesh = new THREE.Mesh(geometry, material);
  mesh.name = 'stratford-high-street-tram-rails';
  // One merged mesh, kept out of the per-material batch so its vertex colours survive.
  mesh.userData.keepIndexed = true;
  mesh.castShadow = false;
  mesh.receiveShadow = true;
  scene.add(mesh);
  return { ...built.review, meshes: 1, drawCalls: 1 };
}
