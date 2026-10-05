import { sewerSurfaceHeight } from './sewer-levels.js';

// Exterior massing at Channelsea, not a surveyed sewer section or invert.
// The 1900–02 rebuilding straddles our scene date: do not silently assign its
// five barrels / two central piers to the earlier three-barrel bridge.
export const crossingAssumptions = Object.freeze({
  halfLength: 30,
  coverDepth: 0.5,
  enclosureDepth: 2.9,
  abutmentLength: 3,
  foundationEmbedment: 0.6,
  status: 'provisional exterior; rebuilding phase unresolved',
  source: 'https://historicengland.org.uk/listing/the-list/list-entry/1392549',
});

export function sewerCrossing({ THREE, scene, sewer, crossing, level, materials }) {
  const spec = crossingAssumptions;
  const route = sewer.route;
  const anchor = route.findIndex((p) => Math.hypot(...p) < 0.01);
  if (anchor < 1) throw new Error('Channelsea sewer anchor missing');
  const distances = [0];
  for (let i = 1; i < route.length; i++)
    distances.push(distances[i - 1] + Math.hypot(route[i][0] - route[i - 1][0], route[i][1] - route[i - 1][1]));
  const origin = distances[anchor];
  function point(d) {
    const s = origin + d,
      i = distances.findIndex((v, j) => j > 0 && v >= s);
    if (i < 1) throw new Error('Sewer route does not cover Channelsea crossing');
    const t = (s - distances[i - 1]) / (distances[i] - distances[i - 1]);
    return route[i - 1].map((v, k) => v + (route[i][k] - v) * t);
  }
  const cover = (p) => sewerSurfaceHeight(...p, sewer, crossing);
  function section(d, width) {
    const p = point(d),
      a = point(d - 0.01),
      b = point(d + 0.01);
    const incoming = [p[0] - a[0], p[1] - a[1]],
      outgoing = [b[0] - p[0], b[1] - p[1]];
    const normal = (v) => {
      const n = Math.hypot(...v);
      return [-v[1] / n, v[0] / n];
    };
    const na = normal(incoming),
      nb = normal(outgoing),
      sum = [na[0] + nb[0], na[1] + nb[1]];
    const n = Math.hypot(...sum),
      m = sum.map((v) => v / n),
      scale = width / 2 / (m[0] * na[0] + m[1] * na[1]);
    return [-1, 1].map((side) => [p[0] + side * m[0] * scale, p[1] + side * m[1] * scale]);
  }
  const group = new THREE.Group();
  group.name = 'channelsea-sewer-crossing';
  scene.add(group);
  const bounds = {};
  function box(parent, kind, x, y, z, w, h, d, material) {
    if (!(h > 0)) throw new Error(`Invalid Channelsea ${kind} height`);
    const mesh = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), material);
    mesh.position.set(x, y + h / 2, z);
    mesh.name = kind;
    parent.add(mesh);
    return mesh;
  }
  // Iron trough between two stations (metres from the Channelsea anchor), under
  // the deck. Include every mapped bend, so the enclosure remains directly below
  // the deck. Its soffit never drops below floor (see spanAssumptions); the
  // Channelsea trough keeps its full depth.
  function trough(parent, from, to, floor = -Infinity, maxStep = Infinity) {
    const stops = [from, ...distances.map((d) => d - origin).filter((d) => d > from && d < to), to];
    for (let i = stops.length - 1; i > 0; i--) {
      const parts = Math.ceil((stops[i] - stops[i - 1]) / maxStep);
      for (let k = parts - 1; k > 0; k--) stops.splice(i, 0, stops[i - 1] + ((stops[i] - stops[i - 1]) * k) / parts);
    }
    const depth = (h) => Math.min(spec.enclosureDepth, h - spec.coverDepth - floor);
    let count = 0;
    for (let i = 1; i < stops.length; i++) {
      const a = point(stops[i - 1]),
        b = point(stops[i]);
      const length = Math.hypot(b[0] - a[0], b[1] - a[1]),
        ha = cover(a),
        hb = cover(b);
      const span = new THREE.Group();
      span.position.set((a[0] + b[0]) / 2, (ha + hb) / 2, (a[1] + b[1]) / 2);
      span.rotation.y = -Math.atan2(b[1] - a[1], b[0] - a[0]);
      span.rotation.z = Math.atan2(hb - ha, length);
      parent.add(span);
      const enclosureDepth = Math.min(depth(ha), depth(hb));
      if (!(enclosureDepth > 0.5)) throw new Error('Sewer trough too shallow above high water');
      const bottom = -spec.coverDepth - enclosureDepth,
        width = sewer.crestWidth - 0.6;
      // Miter both ends: independent rectangular boxes leave an open wedge on
      // the outside of a bend, even when their centre lines meet.
      const sa = section(stops[i - 1], width),
        sb = section(stops[i], width);
      const ring = [sa[1], sa[0], sb[0], sb[1]],
        tops = [ha, ha, hb, hb].map((h) => h - spec.coverDepth),
        depths = [ha, ha, hb, hb].map(depth);
      const vertices = [
        ...ring.flatMap(([x, z], j) => [x, tops[j] - depths[j], z]),
        ...ring.flatMap(([x, z], j) => [x, tops[j], z]),
      ];
      const geometry = new THREE.BufferGeometry();
      geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
      geometry.setIndex([
        0, 1, 2, 0, 2, 3, 4, 7, 6, 4, 6, 5, 0, 4, 5, 0, 5, 1, 1, 5, 6, 1, 6, 2, 2, 6, 7, 2, 7, 3, 3, 7, 4, 3, 4, 0,
      ]);
      geometry.computeVertexNormals();
      const enclosure = new THREE.Mesh(geometry, materials.iron);
      enclosure.name = 'enclosure';
      parent.add(enclosure);
      count++;
      // Restrained plate-girder relief, informed by the local Abbey Mills photograph.
      // Spacing and section sizes are interpretation, not measured details.
      for (const side of [-1, 1]) {
        for (const y of [bottom, bottom + enclosureDepth - 0.12])
          box(span, 'girder-flange', 0, y, side * (width / 2), length + 0.15, 0.12, 0.18, materials.iron);
        for (let x = -length / 2 + 0.4; x < length / 2; x += 2.4)
          box(span, 'girder-stiffener', x, bottom, side * (width / 2), 0.12, enclosureDepth, 0.18, materials.iron);
      }
    }
    return count;
  }
  trough(group, -spec.halfLength, spec.halfLength);
  // Foundations follow local ground; their tops follow the sewer, independently.
  // Each abutment stands just proud of the brick end wall where the earth bank
  // stops at the drawn Channelsea; no new in-channel pier.
  for (const d of abutmentStations(sewer, origin, spec)) {
    const p = point(d),
      a = point(d - 0.1),
      b = point(d + 0.1);
    const angle = Math.atan2(b[1] - a[1], b[0] - a[0]),
      axis = [Math.cos(angle), Math.sin(angle)];
    const samples = [level(...p)];
    for (const along of [-spec.abutmentLength / 2, spec.abutmentLength / 2])
      for (const across of [-sewer.crestWidth / 2, sewer.crestWidth / 2])
        samples.push(level(p[0] + along * axis[0] - across * axis[1], p[1] + along * axis[1] + across * axis[0]));
    const bottom = Math.min(...samples) - spec.foundationEmbedment;
    const top = cover(p) - spec.coverDepth - spec.enclosureDepth;
    const support = box(
      group,
      'abutment',
      p[0],
      bottom,
      p[1],
      spec.abutmentLength,
      top - bottom,
      sewer.crestWidth,
      materials.brick
    );
    support.rotation.y = -angle;
  }
  // Every other water crossing gets the Channelsea treatment: an iron trough under
  // the deck, running into the bank behind both end walls, on brick abutments just
  // proud of those walls, with piers only where the clear span exceeds the
  // Channelsea's (which has none). Interpretation, not surveyed structures.
  const along = (s) => s - origin;
  const frame = (s) => {
    const p = point(along(s)),
      a = point(along(s) - 0.05),
      b = point(along(s) + 0.05),
      n = Math.hypot(b[0] - a[0], b[1] - a[1]);
    const u = [(b[0] - a[0]) / n, (b[1] - a[1]) / n];
    return { p, u, n: [-u[1], u[0]] };
  };
  const at = (s, t) => {
    const f = frame(s);
    return [f.p[0] + f.n[0] * t, f.p[1] + f.n[1] * t];
  };
  const soffit = (s) => {
    const h = cover(point(along(s)));
    return h - spec.coverDepth - Math.min(spec.enclosureDepth, h - spec.coverDepth - spanAssumptions.minimumSoffit);
  };
  const spansGroup = new THREE.Group();
  spansGroup.name = 'sewer-water-spans';
  scene.add(spansGroup);
  const [westStation, eastStation] = abutmentStations(sewer, origin, spec);
  const channelseaClear = eastStation - westStation - spec.abutmentLength;
  const half = sewer.crestWidth / 2;
  const spans = [];
  for (const [first, last] of waterSpans(sewer, distances)) {
    if (first.chainage < origin && last.chainage > origin) continue; // the Channelsea, above
    const geometry = faceSink();
    const runs = [first, last].map((run, k) => {
      const sign = k === 0 ? 1 : -1; // direction from this bank end towards the water
      const local = run.points.map(([x, , z]) => locateOnRoute(sewer.route, distances, x, z));
      const inside = local.filter((q) => Math.abs(q.t) <= half);
      const edge = (target) => {
        for (let i = 1; i < local.length; i++) {
          const a = local[i - 1],
            b = local[i];
          if ((a.t - target) * (b.t - target) <= 0 && a.t !== b.t)
            return a.s + ((b.s - a.s) * (target - a.t)) / (b.t - a.t);
        }
        return local.reduce((best, q) => (Math.abs(q.t - target) < Math.abs(best.t - target) ? q : best)).s;
      };
      const sl = edge(-half),
        sr = edge(half);
      const cos = Math.max(0.3, sewer.crestWidth / Math.hypot(sr - sl, sewer.crestWidth));
      const shift = (endWallAssumptions.thickness + 0.2) / cos;
      const front = [sl + sign * shift, sr + sign * shift];
      return {
        sign,
        front,
        deep: sign > 0 ? Math.min(...inside.map((q) => q.s)) : Math.max(...inside.map((q) => q.s)),
      };
    });
    const [a, b] = runs;
    // Abutments: a block between the wall face and 3 m behind it, its faces
    // parallel to the bank end (skewed with the channel), its sides along the deck.
    const abutmentCentres = [];
    for (const run of runs) {
      const corners = [
        [run.front[0], -half],
        [run.front[1], half],
        [run.front[1] - run.sign * spec.abutmentLength, half],
        [run.front[0] - run.sign * spec.abutmentLength, -half],
      ];
      const plan = corners.map(([s, t]) => at(s, t));
      abutmentCentres.push([0, 1].map((k) => +(plan.reduce((sum, p) => sum + p[k], 0) / 4).toFixed(2)));
      const ground = corners.map(([s, t]) => level(...at(s, t)));
      const bottom = Math.min(...ground) - spec.foundationEmbedment;
      prism(
        geometry,
        corners.map(([s, t]) => at(s, t)),
        corners.map(() => bottom),
        corners.map(([s]) => soffit(s))
      );
    }
    // Clear span along the centreline between the abutment faces.
    const clear = (b.front[0] + b.front[1]) / 2 - (a.front[0] + a.front[1]) / 2;
    const piers = clear > channelseaClear ? Math.ceil(clear / channelseaClear) - 1 : 0;
    for (let i = 1; i <= piers; i++) {
      const s = (a.front[0] + a.front[1]) / 2 + (clear * i) / (piers + 1),
        l = spanAssumptions.pierLength / 2;
      const corners = [
        [s - l, -half],
        [s + l, -half],
        [s + l, half],
        [s - l, half],
      ];
      const bottom = Math.min(...corners.map(([q, t]) => level(...at(q, t)))) - spec.foundationEmbedment;
      prism(
        geometry,
        corners.map(([q, t]) => at(q, t)),
        corners.map(() => bottom),
        corners.map(([q]) => soffit(q))
      );
    }
    const supports = new THREE.BufferGeometry();
    supports.setAttribute('position', new THREE.Float32BufferAttribute(geometry.positions, 3));
    supports.computeVertexNormals();
    const mesh = new THREE.Mesh(supports, materials.brick);
    mesh.name = 'span-support';
    spansGroup.add(mesh);
    const troughFrom = a.deep - spanAssumptions.troughEmbedment,
      troughTo = b.deep + spanAssumptions.troughEmbedment;
    const troughs = trough(
      spansGroup,
      along(troughFrom),
      along(troughTo),
      spanAssumptions.minimumSoffit,
      spanAssumptions.maximumSegment
    );
    const middle = point(along((first.chainage + last.chainage) / 2));
    spans.push({
      chainage: [first.chainage, last.chainage],
      length: +(last.chainage - first.chainage).toFixed(2),
      clearSpan: +clear.toFixed(2),
      piers,
      abutments: abutmentCentres.length,
      abutmentCentres,
      troughSegments: troughs,
      trough: [+troughFrom.toFixed(2), +troughTo.toFixed(2)],
      soffit: +Math.min(soffit(troughFrom), soffit(troughTo)).toFixed(2),
      middle: middle.map((v) => +v.toFixed(2)),
    });
  }
  const portal = sewerPortal({ THREE, scene, sewer, cover, level, materials });
  const endWalls = bankEndWalls({ THREE, scene, sewer, cover, level, material: materials.brick });
  const roadArches = sewerRoadArches({ THREE, scene, sewer, cover, level, material: materials.brick });
  group.updateMatrixWorld(true);
  for (const kind of ['enclosure', 'abutment']) {
    const extent = new THREE.Box3();
    let count = 0;
    group.traverse((o) => {
      if (o.isMesh && o.name === kind) {
        extent.union(new THREE.Box3().setFromObject(o));
        count++;
      }
    });
    bounds[kind] = { count, min: extent.min.toArray(), max: extent.max.toArray() };
  }
  return {
    status: spec.status,
    floodReady: false,
    deckHeight: cover([0, 0]),
    bounds,
    endWalls,
    roadArches,
    spans: { count: spans.length, referenceClearSpan: +channelseaClear.toFixed(2), spans },
    portal,
  };
}

// End wall form, not a surveyed abutment: thickness, coping and footing are interpretation.
export const endWallAssumptions = Object.freeze({ thickness: 0.8, coping: 0.1, foundationEmbedment: 0.6 });

// Abutment centres relative to the Channelsea anchor. The bank end chainages
// come from the builder (neighbourhood.sewer.bankEnds); without them, keep the
// earlier positions one metre inside the enclosure ends.
function abutmentStations(sewer, origin, spec) {
  const fallback = [-spec.halfLength + 1, spec.halfLength - 1];
  const ends = (sewer.bankEnds || []).filter((e) => e.kind === 'water').map((e) => e.chainage - origin);
  const west = Math.max(...ends.filter((d) => d < 0 && d > -spec.halfLength));
  const east = Math.min(...ends.filter((d) => d > 0 && d < spec.halfLength));
  if (!Number.isFinite(west) || !Number.isFinite(east)) return fallback;
  const face = endWallAssumptions.thickness + 0.2;
  return [west + face - spec.abutmentLength / 2, east - face + spec.abutmentLength / 2];
}

// Water spans other than the Channelsea, not surveyed structures: how far the
// trough runs into the bank, its lowest soffit and the pier size are interpretation.
// minimumSoffit keeps the trough 0.3 m above high water (river-network.json
// tide.high, 1.58 m, data/maps/os-tide-levels.json; 1.4 m when high water was 1.1 m)
// where the sewer descends towards Stratford High Street and the deck is low; the
// sewer section there is unresolved.
export const spanAssumptions = Object.freeze({
  troughEmbedment: 2,
  minimumSoffit: 1.9,
  maximumSegment: 6,
  pierLength: 2,
});

// Chainage s along the route and signed offset t (towards the route normal
// [-dz, dx], as section() uses) of the nearest route point.
function locateOnRoute(route, distances, x, z) {
  let best = null;
  for (let i = 1; i < route.length; i++) {
    const a = route[i - 1],
      dx = route[i][0] - a[0],
      dz = route[i][1] - a[1],
      length = Math.hypot(dx, dz);
    const u = Math.min(1, Math.max(0, ((x - a[0]) * dx + (z - a[1]) * dz) / (length * length)));
    const d = Math.hypot(x - a[0] - u * dx, z - a[1] - u * dz);
    if (!best || d < best.d)
      best = { d, s: distances[i - 1] + u * length, t: ((x - a[0]) * -dz + (z - a[1]) * dx) / length };
  }
  return best;
}

// Pairs of consecutive water bank ends that face each other across a channel:
// the first has the water ahead (higher chainage), the second behind it.
function waterSpans(sewer, distances) {
  const runs = (sewer.bankEnds || [])
    .filter((e) => e.kind === 'water' && e.points.length > 1)
    .map((e) => {
      const p = e.points,
        i = Math.floor((p.length - 2) / 2);
      const [ax, , az] = p[i],
        [bx, , bz] = p[i + 1];
      const n = Math.hypot(bx - ax, bz - az) || 1,
        mx = (ax + bx) / 2,
        mz = (az + bz) / 2;
      // For a step (dx, dz) along a run the water lies towards (dz, -dx).
      const here = locateOnRoute(sewer.route, distances, mx, mz).s,
        water = locateOnRoute(sewer.route, distances, mx + (bz - az) / n, mz - (bx - ax) / n).s;
      return { ...e, ahead: water > here };
    })
    .sort((a, b) => a.chainage - b.chainage);
  const spans = [];
  for (let i = 0; i + 1 < runs.length; i++)
    if (runs[i].ahead && !runs[i + 1].ahead) {
      spans.push([runs[i], runs[i + 1]]);
      i++;
    }
  return spans;
}

// Closed vertical prism over a convex plan quad, with per-corner bottom and top.
function prism({ quad }, corners, bottoms, tops) {
  const cx = corners.reduce((s, p) => s + p[0], 0) / corners.length,
    cz = corners.reduce((s, p) => s + p[1], 0) / corners.length;
  const low = corners.map(([x, z], i) => [x, bottoms[i], z]),
    high = corners.map(([x, z], i) => [x, tops[i], z]);
  for (let i = 0; i < corners.length; i++) {
    const j = (i + 1) % corners.length;
    const out = [(corners[i][0] + corners[j][0]) / 2 - cx, 0, (corners[i][1] + corners[j][1]) / 2 - cz];
    quad(low[i], low[j], high[j], high[i], out);
  }
  quad(high[0], high[1], high[2], high[3], [0, 1, 0]);
  quad(low[0], low[1], low[2], low[3], [0, -1, 0]);
}

// Portal form, not a documented structure: headwall depth, parapet, width beyond
// the deck, coping and the blind arch ring are interpretation.
export const portalAssumptions = Object.freeze({
  westOfFace: 1.2,
  intoBank: 0.35,
  parapet: 1.2,
  beyondDeck: 1,
  copingDepth: 0.2,
  copingOverhang: 0.12,
  archSpan: 10,
  archRise: 2.4,
  crownBelowDeck: 0.9,
  ringDepth: 0.45,
  ringProjection: 0.1,
  foundationEmbedment: 0.6,
});

// Where the open embankment ends at Wick Lane and the sewer passes into cover:
// a brick headwall across the end of the deck and bank (the bank end wall runs
// down the slopes on either side), a parapet across the walk, a stone coping, and
// a blind arch ring on the west face over the line of the sewer.
function sewerPortal({ THREE, scene, sewer, cover, level, materials }) {
  const portal = sewer.portal;
  if (!portal) return null;
  const spec = portalAssumptions;
  const [px, pz] = portal.point,
    [ux, uz] = portal.direction,
    [nx, nz] = [-uz, ux];
  const at = (s, t) => [px + ux * s + nx * t, pz + uz * s + nz * t];
  const deck = cover(portal.point),
    half = sewer.crestWidth / 2 + spec.beyondDeck;
  const plan = (s0, s1, t) => [at(s0, -t), at(s1, -t), at(s1, t), at(s0, t)];
  const wall = plan(-spec.westOfFace, spec.intoBank, half);
  const bottom = Math.min(...wall.map((p) => level(...p))) - spec.foundationEmbedment,
    top = deck + spec.parapet;
  const brick = faceSink(),
    stone = faceSink();
  prism(brick, wall, [bottom, bottom, bottom, bottom], [top, top, top, top]);
  const o = spec.copingOverhang;
  const coping = plan(-spec.westOfFace - o, spec.intoBank + o, half + o);
  prism(
    stone,
    coping,
    [top, top, top, top],
    coping.map(() => top + spec.copingDepth)
  );
  // Blind segmental arch ring in dressed stone, standing proud of the west face.
  const radius = (spec.archSpan * spec.archSpan) / (8 * spec.archRise) + spec.archRise / 2,
    crown = deck - spec.crownBelowDeck,
    centre = crown - radius,
    sweep = Math.asin(spec.archSpan / 2 / radius),
    steps = 16;
  const face = -spec.westOfFace,
    proud = face - spec.ringProjection;
  const arc = (r) =>
    Array.from({ length: steps + 1 }, (_, i) => {
      const angle = -sweep + (2 * sweep * i) / steps;
      return [r * Math.sin(angle), centre + r * Math.cos(angle)];
    });
  const inner = arc(radius),
    outer = arc(radius + spec.ringDepth);
  const point3 = (s, [t, y]) => {
    const [x, z] = at(s, t);
    return [x, y, z];
  };
  for (let i = 0; i < steps; i++) {
    stone.quad(
      point3(proud, outer[i]),
      point3(proud, outer[i + 1]),
      point3(proud, inner[i + 1]),
      point3(proud, inner[i]),
      [-ux, 0, -uz]
    );
    for (const [ring, sign] of [
      [outer, 1],
      [inner, -1],
    ]) {
      const mid = [(ring[i][0] + ring[i + 1][0]) / 2, (ring[i][1] + ring[i + 1][1]) / 2 - centre];
      const normal = [nx * mid[0] * sign, mid[1] * sign, nz * mid[0] * sign];
      stone.quad(
        point3(proud, ring[i]),
        point3(proud, ring[i + 1]),
        point3(face, ring[i + 1]),
        point3(face, ring[i]),
        normal
      );
    }
  }
  for (const [i, sign] of [
    [0, -1],
    [steps, 1],
  ])
    stone.quad(point3(proud, outer[i]), point3(proud, inner[i]), point3(face, inner[i]), point3(face, outer[i]), [
      nx * sign,
      -1,
      nz * sign,
    ]);
  for (const [sink, material, name] of [
    [brick, materials.brick, 'sewer-portal'],
    [stone, materials.stone || materials.brick, 'sewer-portal-coping'],
  ]) {
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(sink.positions, 3));
    geometry.computeVertexNormals();
    const mesh = new THREE.Mesh(geometry, material);
    mesh.name = name;
    scene.add(mesh);
  }
  return {
    street: portal.street,
    width: +(2 * half).toFixed(2),
    top: +(top + spec.copingDepth).toFixed(2),
    bottom: +bottom.toFixed(2),
    archSpan: spec.archSpan,
  };
}

// Triangle soup whose faces are wound to face a hint direction.
function faceSink() {
  const positions = [];
  const push = (a, b, c, normal) => {
    const u = [b[0] - a[0], b[1] - a[1], b[2] - a[2]],
      v = [c[0] - a[0], c[1] - a[1], c[2] - a[2]];
    const n = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]];
    const ordered = n[0] * normal[0] + n[1] * normal[1] + n[2] * normal[2] >= 0 ? [a, b, c] : [a, c, b];
    for (const p of ordered) positions.push(...p);
  };
  const quad = (a, b, c, d, normal) => {
    push(a, b, c, normal);
    push(a, c, d, normal);
  };
  return { positions, push, quad };
}

// Brick end walls where the earth bank stops at drawn water, the railway
// corridor or a street, so the bank does not end in an open wedge. Each run
// keeps the bank on its left: for a step (dx, dz) the wall faces (dz, -dx).
// Wall tops follow the bank surface exactly as app.js lifts the bank vertices.
function bankEndWalls({ THREE, scene, sewer, cover, level, material }) {
  const spec = endWallAssumptions;
  const ends = sewer.bankEnds || [];
  const { positions, quad } = faceSink();
  let walls = 0;
  for (const end of ends) {
    const points = end.points;
    if (points.length < 2) continue;
    const outward = points.map((_, i) => {
      const a = points[Math.max(0, i - 1)],
        b = points[Math.min(points.length - 1, i + 1)];
      const dx = b[0] - a[0],
        dz = b[2] - a[2],
        n = Math.hypot(dx, dz) || 1;
      return [dz / n, -dx / n];
    });
    const sections = points.map(([x, y, z], i) => {
      const fx = x + outward[i][0] * spec.thickness,
        fz = z + outward[i][1] * spec.thickness;
      const ground = level(x, z),
        top = (y * cover([x, z])) / sewer.height + (1 - y / sewer.height) * ground + spec.coping;
      const bottom = Math.min(ground, level(fx, fz)) - spec.foundationEmbedment;
      return {
        backTop: [x, top, z],
        backBottom: [x, bottom, z],
        frontTop: [fx, top, fz],
        frontBottom: [fx, bottom, fz],
        out: [outward[i][0], 0, outward[i][1]],
      };
    });
    for (let i = 1; i < sections.length; i++) {
      const a = sections[i - 1],
        b = sections[i];
      const out = [a.out[0] + b.out[0], 0, a.out[2] + b.out[2]];
      quad(a.frontBottom, b.frontBottom, b.frontTop, a.frontTop, out);
      quad(a.backBottom, b.backBottom, b.backTop, a.backTop, [-out[0], 0, -out[2]]);
      quad(a.backTop, b.backTop, b.frontTop, a.frontTop, [0, 1, 0]);
    }
    for (const [s, sign] of [
      [sections[0], -1],
      [sections[sections.length - 1], 1],
    ]) {
      const along = [-s.out[2] * sign, 0, s.out[0] * sign];
      quad(s.backBottom, s.frontBottom, s.frontTop, s.backTop, along);
    }
    walls++;
  }
  if (!walls) return { count: 0 };
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geometry.computeVertexNormals();
  const mesh = new THREE.Mesh(geometry, material);
  mesh.name = 'bank-end-wall';
  scene.add(mesh);
  return { count: walls, kinds: [...new Set(ends.map((e) => e.kind))].sort() };
}

// Street arch under the deck, not a documented structure: the segmental form,
// the 3 m springing above the road, the ring depth and the skew are interpretation.
export const roadArchAssumptions = Object.freeze({
  springingAboveRoad: 3,
  crownBelowDeck: 0.75,
  minimumRise: 0.8,
  ringDepth: 0.56,
  ringProjection: 0.1,
  wallEmbedment: 0.4,
});

// Where a street passes under the sewer (bankEnds of kind 'road' with a
// roadAxis), carry the deck across the opening on a brick skew arch. It springs
// from the front faces of the two bank end walls, its portals lie along the
// deck edges (parallel to the sewer) and its top is hidden in the deck slab.
function sewerRoadArches({ THREE, scene, sewer, cover, level, material }) {
  const spec = roadArchAssumptions,
    wall = endWallAssumptions.thickness;
  const openings = new Map();
  for (const end of sewer.bankEnds || []) {
    if (end.kind !== 'road' || !end.roadAxis) continue;
    const key = `${end.road}|${end.roadAxis.flat().join(',')}`;
    if (!openings.has(key)) openings.set(key, { ...end, runs: [] });
    openings.get(key).runs.push(end.points);
  }
  const { positions, push, quad } = faceSink();
  const deckSlab = (x, z) => cover([x, z]) - 0.5; // underside of the 0.48 m deck slab in app.js
  const arches = [];
  for (const opening of openings.values()) {
    const [A, B] = opening.roadAxis;
    const C = [(A[0] + B[0]) / 2, (A[1] + B[1]) / 2],
      L = Math.hypot(B[0] - A[0], B[1] - A[1]);
    const u = [(B[0] - A[0]) / L, (B[1] - A[1]) / L],
      n = [-u[1], u[0]];
    // Sewer direction on the route segment nearest the crossing.
    let s = null,
      best = Infinity;
    for (let i = 1; i < sewer.route.length; i++) {
      const a = sewer.route[i - 1],
        b = sewer.route[i],
        dx = b[0] - a[0],
        dz = b[1] - a[1],
        len = Math.hypot(dx, dz);
      const t = Math.min(1, Math.max(0, ((C[0] - a[0]) * dx + (C[1] - a[1]) * dz) / (len * len)));
      const d = Math.hypot(C[0] - a[0] - t * dx, C[1] - a[1] - t * dz);
      if (d < best) [best, s] = [d, [dx / len, dz / len]];
    }
    const su = s[0] * u[0] + s[1] * u[1],
      sn = s[0] * n[0] + s[1] * n[1];
    if (Math.abs(sn) < 0.3) continue; // street nearly parallel to the sewer: no arch
    const local = ([x, z]) => [(x - C[0]) * u[0] + (z - C[1]) * u[1], (x - C[0]) * n[0] + (z - C[1]) * n[1]];
    // Wall front faces: the bank end runs beside the deck, less the wall thickness.
    const faces = { [-1]: [], [1]: [] };
    for (const run of opening.runs)
      for (const [x, , z] of run) {
        const [a, t] = local([x, z]);
        if (Math.abs(a) <= L / 2 + 2 && t !== 0) faces[Math.sign(t)].push(Math.abs(t) - wall);
      }
    const median = (v) => v.sort((p, q) => p - q)[Math.floor(v.length / 2)];
    const fallback = opening.roadWidth / 2 + 0.7;
    const left = faces[-1].length ? median(faces[-1]) : fallback,
      right = faces[1].length ? median(faces[1]) : fallback;
    const span = left + right,
      tc = (right - left) / 2;
    const world = (a, t, y) => [C[0] + u[0] * a + n[0] * t, y, C[1] + u[1] * a + n[1] * t];
    // Road level on the street centreline under the deck. Samples at the street
    // edges (the earlier rule) can land on the landscape's corridor batter beside
    // the carriageway and flattened the arch.
    const road = Math.max(
      ...[-1, -0.5, 0, 0.5, 1].map((k) => {
        const [x, , z] = world((k * L) / 2, 0, 0);
        return level(x, z);
      })
    );
    const deck = Math.min(...[A, B, C].map((p) => deckSlab(...p)));
    const crown = deck - spec.crownBelowDeck;
    const rise = Math.max(spec.minimumRise, Math.min(span / 2, crown - road - spec.springingAboveRoad));
    const springing = crown - rise,
      radius = (span * span) / 4 / (2 * rise) + rise / 2,
      half = Math.asin(Math.min(1, span / 2 / radius));
    const arc = (r, steps = 20) =>
      Array.from({ length: steps + 1 }, (_, i) => {
        const angle = -half + (2 * half * i) / steps;
        return [tc + r * Math.sin(angle), crown - radius + r * Math.cos(angle)];
      });
    // Portals pass through the deck-edge ends of the axis, parallel to the sewer.
    const k = su / sn,
      portal = (end, t) => end * (L / 2) + t * k;
    const outwardShift = spec.ringProjection / Math.abs(sn);
    const extrude = (contour, aAt, topY) => {
      // contour in (t, y); aAt(end, t) gives the along position of each cap.
      let area = 0;
      for (let i = 0; i < contour.length; i++) {
        const [t0, y0] = contour[i],
          [t1, y1] = contour[(i + 1) % contour.length];
        area += t0 * y1 - t1 * y0;
      }
      const sign = area > 0 ? 1 : -1;
      const at = (end, [t, y]) => {
        const p = world(aAt(end, t), t, y);
        if (topY && y >= topY - 1e-6) p[1] = deckSlab(p[0], p[2]) + 0.2;
        return p;
      };
      for (let i = 0; i < contour.length; i++) {
        const p = contour[i],
          q = contour[(i + 1) % contour.length];
        const nt = sign * (q[1] - p[1]),
          ny = -sign * (q[0] - p[0]);
        quad(at(-1, p), at(-1, q), at(1, q), at(1, p), [n[0] * nt, ny, n[1] * nt]);
      }
      const triangles = THREE.ShapeUtils.triangulateShape(
        contour.map(([t, y]) => new THREE.Vector2(t, y)),
        []
      );
      for (const end of [-1, 1])
        for (const tri of triangles) push(...tri.map((i) => at(end, contour[i])), [end * u[0], 0, end * u[1]]);
    };
    // Spandrel block: from the springing to inside the deck slab, minus the intrados.
    const outer = span / 2 + spec.wallEmbedment,
      top = deck + 0.2;
    extrude(
      [[tc - outer, springing], ...arc(radius), [tc + outer, springing], [tc + outer, top], [tc - outer, top]],
      portal,
      top
    );
    // Arch ring standing slightly proud of each portal face.
    const ring = [...arc(radius + spec.ringDepth), ...arc(radius).reverse()];
    for (const end of [-1, 1])
      extrude(ring, (side, t) => portal(end, t) + (side === end ? end * outwardShift : 0), null);
    const edge = opening.roadWidth / 2;
    const clearanceAt = (t) => {
      const dt = t - tc;
      return Math.abs(dt) >= span / 2 ? springing - road : crown - radius + Math.sqrt(radius * radius - dt * dt) - road;
    };
    arches.push({
      road: opening.road,
      span: +span.toFixed(2),
      rise: +rise.toFixed(2),
      crownClearance: +(crown - road).toFixed(2),
      edgeClearance: +Math.min(clearanceAt(-edge), clearanceAt(edge)).toFixed(2),
      skewDegrees: +((Math.acos(Math.abs(sn)) * 180) / Math.PI).toFixed(1),
    });
  }
  if (!arches.length) return { count: 0 };
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geometry.computeVertexNormals();
  const mesh = new THREE.Mesh(geometry, material);
  mesh.name = 'sewer-road-arch';
  scene.add(mesh);
  return { count: arches.length, arches };
}
