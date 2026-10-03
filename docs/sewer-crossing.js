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
  // Include every mapped bend, so the enclosure remains directly below the deck.
  const stops = [
    -spec.halfLength,
    ...distances.map((d) => d - origin).filter((d) => d > -spec.halfLength && d < spec.halfLength),
    spec.halfLength,
  ];
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
    group.add(span);
    const bottom = -spec.coverDepth - spec.enclosureDepth,
      width = sewer.crestWidth - 0.6;
    // Miter both ends: independent rectangular boxes leave an open wedge on
    // the outside of a bend, even when their centre lines meet.
    const sa = section(stops[i - 1], width),
      sb = section(stops[i], width);
    const ring = [sa[1], sa[0], sb[0], sb[1]],
      tops = [ha, ha, hb, hb].map((h) => h - spec.coverDepth);
    const vertices = [
      ...ring.flatMap(([x, z], j) => [x, tops[j] - spec.enclosureDepth, z]),
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
    group.add(enclosure);
    // Restrained plate-girder relief, informed by the local Abbey Mills photograph.
    // Spacing and section sizes are interpretation, not measured details.
    for (const side of [-1, 1]) {
      for (const y of [bottom, bottom + spec.enclosureDepth - 0.12])
        box(span, 'girder-flange', 0, y, side * (width / 2), length + 0.15, 0.12, 0.18, materials.iron);
      for (let x = -length / 2 + 0.4; x < length / 2; x += 2.4)
        box(span, 'girder-stiffener', x, bottom, side * (width / 2), 0.12, spec.enclosureDepth, 0.18, materials.iron);
    }
  }
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
  const endWalls = bankEndWalls({ THREE, scene, sewer, cover, level, material: materials.brick });
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
  return { status: spec.status, floodReady: false, deckHeight: cover([0, 0]), bounds, endWalls };
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

// Brick end walls where the earth bank stops at drawn water or the railway
// corridor, so the bank does not end in an open wedge under the deck. Each run
// keeps the bank on its left: for a step (dx, dz) the wall faces (dz, -dx).
// Wall tops follow the bank surface exactly as app.js lifts the bank vertices.
function bankEndWalls({ THREE, scene, sewer, cover, level, material }) {
  const spec = endWallAssumptions;
  const ends = sewer.bankEnds || [];
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
