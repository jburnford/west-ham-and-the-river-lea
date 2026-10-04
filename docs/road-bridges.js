// Road bridge structures about 1900: arches, piers, abutments, spandrels, parapets, railings and
// wing walls under and beside the decks recorded in infrastructure.json roadBridges.
// Register: data/maps/road-bridge-forms.json, copied here as bridgeForms (scripts/check_road_bridges.mjs
// fails if the copies differ). Structural families come from the bridge records; spans follow the
// drawn water; rises, ring depths, parapets and every other dimension are estimates.
// The road surface itself (deck setts and footways) stays in infrastructure.js, unchanged.
import { createTriangleBatcher } from './lib/geometry.js';

export const bridgeForms = {
  description:
    'Structural form chosen for each road bridge in docs/data/infrastructure.json roadBridges, about 1900: arches, abutments, piers, parapets or railings, and wing walls. The bridge records (route, width, deck height, style, arch count) are not changed here; this register adds the structure under and beside the deck. docs/road-bridges.js carries an identical copy as bridgeForms, and scripts/check_road_bridges.mjs fails if the two differ.',
  frame:
    'Stations are metres along each bridge route from its first point. Offsets are metres across it, positive on the left (the normal (-uz, ux)). An abutment face lies at station abutment + skew * offset, so skew is the shift of the face per metre across the deck. Heights are scene y metres; the static water surface is y 0.06 and the animated tide reaches y 1.1.',
  sources: [
    {
      id: 'vch',
      citation:
        'Victoria County History, Essex VI, pp. 57-61, as cited in each roadBridges evidence string for the structural family (stone or brick arch, deck).',
      use: 'Structural family only. The text is not held in this repository and was not read for this task; spans, rises, ring depths and parapet forms are estimates.',
    },
    {
      id: 'road-trace-notes',
      citation: 'data/maps/district-road-traces.json notes',
      use: 'Bow Bridge is one granite-faced span completed 1839; St Thomas brick arch count is not established by the written source; High Street bridge names follow the nineteenth-century transposition; the three lane connections are provisional, with deck or culvert unresolved.',
    },
    {
      id: 'os-five-foot',
      citation:
        'OS London five-foot plan, 1893-96 revision, NLS tiles read with scripts/factory_map_sources.py mosaic() at zoom 18 (about 0.4 m per pixel)',
      use: 'Named crossings and the parapet or road edge lines across each river. At this resolution the abutment faces under the deck cannot be read; the plan does show each crossing as one continuous carriageway between buildings.',
    },
    {
      id: 'os-heights',
      citation:
        'data/maps/lower-lea-region/height-observations.opus-2026-10-02.geojson (OS 25-inch, 1893-96 revision, feet above OD Liverpool)',
      use: "Bench marks cut on the Pegs Hole Bridge parapet, at St Michael's Bridge and on the hatched south parapet of the Bow Bridge east approach show masonry parapets there. Spot heights on the crossings are compared with the recorded deck heights in the T12a report; they are not used to change any height.",
    },
    {
      id: 'photo-catalogue',
      citation: 'reference/photo-review-2026-10-03/reports/photo-catalogue.md',
      use: 'No archive image shows these bridges, so no elevation detail is copied from a photograph.',
    },
    {
      id: 'drawn-water',
      citation:
        'Water polygons as drawn by docs/app.js (tide, reviewed connections, retained rivers, marsh ditches, river system)',
      use: 'Abutment stations sit at the drawn water edges measured along each route on the centreline and both deck edges (waterEdges below). They are model measurements, not surveyed abutments.',
    },
  ],
  defaults: {
    springing: 0.5,
    parapetHeight: 1,
    copingHeight: 0.12,
    parapetThickness: 0.45,
    railingHeight: 1.05,
    clearZoneMargin: 2,
    evidence:
      'Estimates for every bridge: springing 0.44 m above the static water so the arch feet stand clear of it; masonry parapet 1.0 m plus 0.12 m coping (about 1.1 m above the carriageway, 1.0 m above the footway); railings 1.05 m. Approach fill is not drawn within 2 m of either deck edge between the abutment faces.',
  },
  bridges: {
    'bow-bridge': {
      form: 'stone-arch',
      arches: 1,
      abutments: [3, 29.5],
      skew: 0.4,
      crownDepth: 0.9,
      ringDepth: 0.6,
      abutmentLength: 2.5,
      waterEdges: { centre: [2, 29], left: [6.5, 30.5], right: [0, 27.25] },
      evidence:
        'Documented: one granite-faced span completed 1839 (road-trace notes), stone family (VCH as cited); bench mark on the hatched south parapet of the east approach (OS 25-inch). Mapped: the crossing on the OS five-foot plan. Measured in the model: the River Lea crosses the route obliquely, so the abutment faces follow the bank with a skew of 0.4 m per metre. Estimated: one segmental arch of 26.5 m along the road, crown soffit 0.9 m below the deck, springing 0.5 m, ring and parapet dimensions. The 1901-06 rebuilding is not shown.',
    },
    'pegshole-bridge': {
      form: 'stone-arch',
      arches: 2,
      abutments: [8, 27],
      skew: 0,
      pier: 1.8,
      crownDepth: 0.6,
      ringDepth: 0.45,
      abutmentLength: 2.5,
      waterEdges: { centre: [10.75, 24.75], left: [5.75, 29], right: [9.75, 25.5] },
      evidence:
        "Documented: stone family and two arches (VCH as cited, in the record). Mapped: Peg's Hole Bridge over the Three Mills Back River on the OS five-foot plan; bench mark on its parapet and a spot height at the bridge crown (OS 25-inch). Measured in the model: the water widens on the left (south-east) edge, so the abutments are set between the centreline and edge water lines. Estimated: two segmental arches of 8.6 m on a 1.8 m river pier with cutwaters, rise, ring and parapet dimensions.",
    },
    'st-thomas-bridge': {
      form: 'brick-arch',
      arches: 1,
      abutments: [7, 15.75],
      skew: 0,
      crownDepth: 0.6,
      ringDepth: 0.35,
      abutmentLength: 2,
      waterEdges: { centre: [8.5, 15], left: [3, 19.25], right: [8.75, 15.75] },
      evidence:
        "Documented: brick family (VCH as cited); the arch count is not established by the written source (road-trace notes). Mapped: Sir Thomas D'Akers Bridge over the western Waterworks arm (OS five-foot plan). Measured in the model: centreline water 8.5-15 m; the drawn water flares on the left edge and is left partly under the abutment there. Estimated: one segmental brick arch of 8.75 m with three brick rings, rise and parapet dimensions; a brick parapet with stone coping.",
    },
    'st-michaels-bridge': {
      form: 'stone-arch',
      arches: 1,
      abutments: [8, 20.75],
      skew: -0.18,
      crownDepth: 0.7,
      ringDepth: 0.5,
      abutmentLength: 2.5,
      waterEdges: { centre: [8.5, 20.25], left: [7.25, 19.25], right: [9.5, 21.25] },
      evidence:
        "Documented: stone family (VCH as cited). Mapped: St Michael's Bridge over the eastern Waterworks arm (OS five-foot plan) with a bench mark at the bridge (OS 25-inch). Measured in the model: both drawn banks cross the route at the same oblique angle, skew -0.18 m per metre. Estimated: one segmental arch of 12.75 m, rise, ring and parapet dimensions.",
    },
    'channelsea-high-street-bridge': {
      form: 'stone-arch',
      arches: 1,
      abutments: [20.75, 31],
      skew: -0.3,
      crownDepth: 0.65,
      ringDepth: 0.45,
      abutmentLength: 2.5,
      waterEdges: { centre: [21.25, 30.25], left: [18.75, 29.75], right: [23.25, 32.5] },
      evidence:
        'Documented: stone family (VCH as cited). Mapped: Channel Sea Bridge on the OS five-foot plan, with tramway spot heights on it (OS 25-inch). Measured in the model: the Channelsea crosses the route obliquely, skew -0.3 m per metre. Estimated: one segmental arch of 10.25 m, rise, ring and parapet dimensions. The long route either side of the water is drawn as walled approach, as before.',
    },
    'three-mills-lea-bridge': {
      form: 'iron-deck',
      abutments: [23.75, 38.5],
      girderDepth: 0.8,
      abutmentLength: 1.5,
      waterEdges: { centre: [24.25, 38], left: [24.25, 37], right: [24.25, 38.25] },
      evidence:
        "Recorded style deck (the record's archCount 1 is retained in infrastructure.json but a deck has no arch). Mapped: Three Mills Bridge over the River Lea on the OS five-foot plan, with a bench mark at its west abutment (OS 25-inch). Measured in the model: water 24.25-38 m on the route. Estimated: wrought-iron girders 0.8 m deep on brick abutments, timber deck, iron railings; walled approaches on the land either side.",
    },
    'abbey-mill-crossing': {
      form: 'slab-deck',
      abutments: [19.5, 28],
      abutmentLength: 1.2,
      waterEdges: { centre: [24.5, 27.5], left: [22.25, 27.5], right: [20, 25.75] },
      evidence:
        'The record has no structural style; its 0.4 m slab and brick parapets are kept as drawn before, because the T3 landscape holds the bank 0.1 m below that slab. Measured in the model: the two channel cuts reach 20-27.5 m on the route. Added estimate: brick abutments at the water edges. Construction remains interpreted, as the record says.',
    },
    'marshgate-lane-connection-0': {
      form: 'timber-deck',
      provisional: true,
      abutments: [7, 16],
      beamDepth: 0.35,
      abutmentLength: 1.2,
      waterEdges: { centre: [7.75, 15.25], left: [8, 17.25], right: [7.25, 13.5] },
      evidence:
        'Provisional connection (record): deck versus culvert unresolved and not a documented named bridge. Drawn as the plainest reading, a timber deck on timber beams and brick abutments at the drawn water edges, with timber railings. All dimensions estimated.',
    },
    'hunts-lane-connection-0': {
      form: 'iron-deck',
      provisional: true,
      abutments: [2.75, 19.25],
      girderDepth: 0.6,
      abutmentLength: 1.2,
      waterEdges: { centre: [3.25, 18.75], left: [3.75, 20.5], right: [2.25, 17.25] },
      evidence:
        "Provisional Cook's Road connection (record): deck versus culvert unresolved. The drawn water is 15.5 m wide on the route, too long for plain timber beams without river trestles, so iron girders on brick abutments are drawn, with iron railings. All dimensions estimated.",
    },
    'three-mills-lane-beside-distillery-connection-0': {
      form: 'timber-deck',
      provisional: true,
      abutments: [7.5, 12.93],
      beamDepth: 0.3,
      abutmentLength: 1,
      waterEdges: { centre: [15.75, null], left: [16, null], right: [8, null] },
      evidence:
        'Provisional footpath deck or culvert (record). The drawn water reaches the route only on its right edge from 8 m and runs on beyond the route end, so the second abutment is put at the route end. Timber deck, beams and railings on brick abutments; all dimensions estimated.',
    },
  },
};

const ARCH_FORMS = new Set(['stone-arch', 'brick-arch']);

// Stations along a polyline route; positions at (station, offset), offset positive on the left.
export function routeFrame(route) {
  const segments = [];
  let length = 0;
  for (let i = 1; i < route.length; i++) {
    const a = route[i - 1],
      b = route[i],
      l = Math.hypot(b[0] - a[0], b[1] - a[1]);
    segments.push({ a, s0: length, length: l, ux: (b[0] - a[0]) / l, uz: (b[1] - a[1]) / l });
    length += l;
  }
  const segmentAt = (s) => segments.find((g) => s <= g.s0 + g.length) || segments.at(-1);
  // Beyond either end the first or last segment is extended.
  const at = (s, v = 0) => {
    const g = s < 0 ? segments[0] : segmentAt(s),
      d = s - g.s0;
    return [g.a[0] + g.ux * d - g.uz * v, g.a[1] + g.uz * d + g.ux * v];
  };
  const tangent = (s) => {
    const g = s < 0 ? segments[0] : segmentAt(s);
    return [g.ux, g.uz];
  };
  // Station and offset of a plan point, from the nearest segment.
  const project = (x, z) => {
    let best = null;
    segments.forEach((g, i) => {
      const dx = x - g.a[0],
        dz = z - g.a[1];
      // Interior segment ends are clamped; the first and last segments run on beyond the route.
      let t = dx * g.ux + dz * g.uz;
      if (i > 0) t = Math.max(0, t);
      if (i < segments.length - 1) t = Math.min(g.length, t);
      const dist = Math.hypot(dx - g.ux * t, dz - g.uz * t);
      if (!best || dist < best.dist) best = { s: g.s0 + t, v: -dx * g.uz + dz * g.ux, dist };
    });
    return best;
  };
  return { segments, length, at, tangent, project };
}

// Plan layout of one bridge: abutment faces, arches and piers in arch-frame stations
// (station - skew * offset), and the levels that follow from the record and the form.
export function bridgeLayout(bridge, form, defaults = bridgeForms.defaults) {
  const frame = routeFrame(bridge.route),
    width = bridge.width,
    height = bridge.height,
    skew = form.skew || 0,
    abutmentLength = form.abutmentLength ?? 1.2;
  let [a0, a1] = form.abutments;
  // Abutment bodies stay under the recorded deck.
  a0 = Math.max(a0, abutmentLength);
  a1 = Math.min(a1, frame.length - abutmentLength);
  const layout = { bridge, form, frame, width, height, skew, abutmentLength, a0, a1, arches: [], piers: [] };
  if (ARCH_FORMS.has(form.form)) {
    const n = form.arches,
      pier = n > 1 ? form.pier : 0,
      span = (a1 - a0 - (n - 1) * pier) / n,
      springing = form.springing ?? defaults.springing,
      crown = height - form.crownDepth,
      rise = crown - springing,
      radius = (span * span) / 4 / rise / 2 + rise / 2;
    for (let i = 0; i < n; i++) {
      const from = a0 + i * (span + pier);
      layout.arches.push({ from, to: from + span, mid: from + span / 2 });
      if (i) layout.piers.push({ from: from - pier, to: from });
    }
    Object.assign(layout, { span, springing, crown, rise, radius, ringDepth: form.ringDepth });
    layout.soffit = (arch, xa) =>
      springing + Math.sqrt(Math.max(0, radius * radius - (xa - arch.mid) ** 2)) - (radius - rise);
  } else {
    const depth = form.form === 'iron-deck' ? form.girderDepth : form.form === 'timber-deck' ? form.beamDepth : 0;
    layout.deckUnderside = form.form === 'slab-deck' ? height - 0.4 : height - 0.12 - depth;
    layout.span = a1 - a0;
  }
  return layout;
}

// Plan test for the space between the abutment faces, within a margin either side of the deck.
// Approach fill must not be drawn there.
export function bridgeClearance(bridges, forms = bridgeForms) {
  const margin = forms.defaults.clearZoneMargin;
  const zones = bridges
    .filter((b) => forms.bridges[b.id])
    .map((b) => {
      const layout = bridgeLayout(b, forms.bridges[b.id], forms.defaults),
        reach = b.width / 2 + margin,
        xs = b.route.map((p) => p[0]),
        zs = b.route.map((p) => p[1]),
        pad = reach + Math.abs(layout.skew) * reach;
      return {
        layout,
        reach,
        box: [Math.min(...xs) - pad, Math.min(...zs) - pad, Math.max(...xs) + pad, Math.max(...zs) + pad],
      };
    });
  const near = (x0, z0, x1, z1) =>
    zones.filter(
      (q) =>
        Math.max(x0, x1) >= q.box[0] &&
        Math.min(x0, x1) <= q.box[2] &&
        Math.max(z0, z1) >= q.box[1] &&
        Math.min(z0, z1) <= q.box[3]
    );
  const insideZone = (q, x, z) => {
    const p = q.layout.frame.project(x, z),
      xa = p.s - q.layout.skew * p.v;
    return xa > q.layout.a0 && xa < q.layout.a1 && Math.abs(p.v) <= q.reach;
  };
  return {
    zones,
    inside: (x, z) => near(x, z, x, z).some((q) => insideZone(q, x, z)),
    // Pieces of the edge a-b ([x, y, z] points) that lie outside every clear zone.
    outside(a, b) {
      const candidates = near(a[0], a[2], b[0], b[2]);
      if (!candidates.length) return [[a, b]];
      const n = Math.max(1, Math.ceil(Math.hypot(b[0] - a[0], b[2] - a[2]) / 0.25)),
        lerp = (t) => a.map((v, i) => v + (b[i] - v) * t),
        runs = [];
      let start = null;
      for (let i = 0; i < n; i++) {
        const m = lerp((i + 0.5) / n),
          out = !candidates.some((q) => insideZone(q, m[0], m[2]));
        if (out && start === null) start = i;
        if (!out && start !== null) {
          runs.push([lerp(start / n), lerp(i / n)]);
          start = null;
        }
      }
      if (start !== null) runs.push([lerp(start / n), b]);
      return runs;
    },
  };
}

export function roadBridges({ THREE, scene, materials: m, bridges, level, waterLevel, collect = false }) {
  const batch = createTriangleBatcher(),
    defaults = bridgeForms.defaults,
    parts = collect ? [] : null,
    review = [];
  let tag = null;
  const record = (a, b, c) => {
    if (!parts) return;
    let entry = parts.at(-1);
    if (!entry || entry.bridge !== tag.bridge || entry.part !== tag.part)
      parts.push((entry = { ...tag, positions: [] }));
    entry.positions.push(...a, ...b, ...c);
  };
  // A planar polygon (3 or 4 [x, y, z] points) wound to face along `normal`; metre-scale UVs on the
  // face plane unless given.
  function face(material, points, normal, uv) {
    const [p0, p1, p2] = points,
      e1 = [p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]],
      e2 = [p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2]],
      cross = [e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2], e1[0] * e2[1] - e1[1] * e2[0]];
    let pts = points,
      uvs = uv;
    if (cross[0] * normal[0] + cross[1] * normal[1] + cross[2] * normal[2] < 0) {
      pts = [...points].reverse();
      uvs = uv && [...uv].reverse();
    }
    if (!uvs) {
      const flat = Math.abs(normal[1]) > 0.7,
        tl = Math.hypot(normal[2], normal[0]) || 1,
        t = [normal[2] / tl, 0, -normal[0] / tl];
      uvs = pts.map((p) => (flat ? [p[0], p[2]] : [p[0] * t[0] + p[2] * t[2], p[1]]));
    }
    batch.triangle(material, pts[0], pts[1], pts[2], [uvs[0], uvs[1], uvs[2]]);
    record(pts[0], pts[1], pts[2]);
    if (pts.length === 4) {
      batch.triangle(material, pts[0], pts[2], pts[3], [uvs[0], uvs[2], uvs[3]]);
      record(pts[0], pts[2], pts[3]);
    }
  }
  // Box from plan corners: c is [x, z] centre, u the [ux, uz] long axis; y0 to y1. No bottom face.
  function block(material, c, u, length, width, y0, y1, bottom = false) {
    if (y1 - y0 < 1e-4 || length < 1e-4) return;
    const n = [-u[1], u[0]],
      corner = (i, j, y) => [
        c[0] + (u[0] * length * i) / 2 + (n[0] * width * j) / 2,
        y,
        c[1] + (u[1] * length * i) / 2 + (n[1] * width * j) / 2,
      ];
    const sides = [
      [
        [1, -1],
        [1, 1],
        [u[0], 0, u[1]],
      ],
      [
        [-1, 1],
        [-1, -1],
        [-u[0], 0, -u[1]],
      ],
      [
        [1, 1],
        [-1, 1],
        [n[0], 0, n[1]],
      ],
      [
        [-1, -1],
        [1, -1],
        [-n[0], 0, -n[1]],
      ],
    ];
    for (const [[i0, j0], [i1, j1], normal] of sides)
      face(material, [corner(i0, j0, y0), corner(i1, j1, y0), corner(i1, j1, y1), corner(i0, j0, y1)], normal);
    face(material, [corner(-1, -1, y1), corner(1, -1, y1), corner(1, 1, y1), corner(-1, 1, y1)], [0, 1, 0]);
    if (bottom)
      face(material, [corner(-1, -1, y0), corner(1, -1, y0), corner(1, 1, y0), corner(-1, 1, y0)], [0, -1, 0]);
  }
  // Vertical wall face through plan columns [x, z, bottom, top], facing `side` (+1 left of travel).
  function wallFace(material, columns, side) {
    for (let i = 1; i < columns.length; i++) {
      const [ax, az, ab, at] = columns[i - 1],
        [bx, bz, bb, bt] = columns[i];
      if (at - ab < 1e-4 && bt - bb < 1e-4) continue;
      const l = Math.hypot(bx - ax, bz - az);
      if (l < 1e-5) continue;
      const normal = [(-(bz - az) / l) * side, 0, ((bx - ax) / l) * side];
      face(
        material,
        [
          [ax, ab, az],
          [bx, bb, bz],
          [bx, Math.max(bb, bt), bz],
          [ax, Math.max(ab, at), az],
        ],
        normal
      );
    }
  }
  const lowest = (points) => Math.min(...points.map(([x, z]) => level(x, z)));

  for (const bridge of bridges) {
    const form = bridgeForms.bridges[bridge.id];
    if (!form) continue;
    const L = bridgeLayout(bridge, form, defaults),
      { frame, width: W, height: h, skew: k, a0, a1, abutmentLength: lab } = L,
      half = W / 2,
      arch = ARCH_FORMS.has(form.form),
      body = form.form === 'brick-arch' ? m.brick : arch ? m.stone : m.brick,
      at = (xa, v) => frame.at(xa + k * v, v),
      p3 = (xa, v, y) => {
        const [x, z] = at(xa, v);
        return [x, y, z];
      },
      tangent = frame.tangent(frame.length / 2),
      u3 = [tangent[0], 0, tangent[1]];
    const set = (part) => (tag = { bridge: bridge.id, part });
    // Footing: below the lower of the drawn bed and the water, under each abutment face.
    const footing = (xa) =>
      Math.min(
        waterLevel,
        lowest([-half, -half / 2, 0, half / 2, half].flatMap((v) => [at(xa, v), at(xa + 0.5, v), at(xa - 0.5, v)]))
      ) - 0.3;
    const foot0 = footing(a0),
      foot1 = footing(a1);
    const pierFoot = L.piers.map((p) => footing((p.from + p.to) / 2));
    const info = {
      id: bridge.id,
      form: form.form,
      provisional: Boolean(form.provisional),
      abutments: [+a0.toFixed(2), +a1.toFixed(2)],
      clearSpan: +(a1 - a0 - L.piers.reduce((s, p) => s + p.to - p.from, 0)).toFixed(2),
    };

    if (arch) {
      // Soffit: each arch barrel, straight across the deck in the skewed arch frame.
      set('arch');
      for (const a of L.arches) {
        const n = Math.max(12, Math.ceil((a.to - a.from) / 0.5));
        let arc = 0;
        for (let j = 0; j < n; j++) {
          const xa = a.from + ((a.to - a.from) * j) / n,
            xb = a.from + ((a.to - a.from) * (j + 1)) / n,
            ya = L.soffit(a, xa),
            yb = L.soffit(a, xb),
            step = Math.hypot(xb - xa, yb - ya);
          face(
            body,
            [p3(xa, -half, ya), p3(xb, -half, yb), p3(xb, half, yb), p3(xa, half, ya)],
            [0, -1, 0],
            [
              [arc, -half],
              [arc + step, -half],
              [arc + step, half],
              [arc, half],
            ]
          );
          arc += step;
        }
      }
      // Abutment faces below the springing, and river piers with cutwaters.
      set('abutment');
      const springing = L.springing;
      for (const [xa, foot, dir] of [
        [a0, foot0, 1],
        [a1, foot1, -1],
      ])
        face(
          body,
          [p3(xa, -half, foot), p3(xa, half, foot), p3(xa, half, springing), p3(xa, -half, springing)],
          [u3[0] * dir, 0, u3[2] * dir]
        );
      L.piers.forEach((p, i) => {
        const foot = pierFoot[i];
        set('pier');
        for (const [xa, dir] of [
          [p.from, -1],
          [p.to, 1],
        ])
          face(
            body,
            [p3(xa, -half, foot), p3(xa, half, foot), p3(xa, half, springing), p3(xa, -half, springing)],
            [u3[0] * dir, 0, u3[2] * dir]
          );
        set('cutwater');
        const mid = (p.from + p.to) / 2,
          top = springing + 0.4;
        for (const side of [-1, 1]) {
          const v0 = side * half,
            nose = side * (half + 1.0),
            outward = [-u3[2] * side, 0, u3[0] * side];
          for (const xa of [p.from, p.to]) {
            const dir = xa === p.from ? -1 : 1,
              normal = [outward[0] + u3[0] * dir, 0, outward[2] + u3[2] * dir];
            face(body, [p3(xa, v0, foot), p3(mid, nose, foot), p3(mid, nose, top), p3(xa, v0, top)], normal);
            face(body, [p3(xa, v0, top), p3(mid, nose, top), p3(mid, v0, top + 0.6)], [normal[0], 1, normal[2]]);
          }
        }
      });
      // Spandrel walls on both faces, from the soffit (or footing, or ground on the approaches) up
      // to the deck. Columns are placed in route stations so the walls end exactly at the route ends.
      for (const side of [-1, 1]) {
        const v = side * half;
        const kinds = [];
        const xa0 = -k * v,
          xa1 = frame.length - k * v;
        const cuts = [xa0, a0 - lab, a0, ...L.arches.flatMap((a) => [a.from, a.to]), a1, a1 + lab, xa1];
        const edges = [...new Set(cuts.map((x) => Math.min(xa1, Math.max(xa0, x))))].sort((p, q) => p - q);
        for (let i = 1; i < edges.length; i++) kinds.push([edges[i - 1], edges[i]]);
        for (const [from, to] of kinds) {
          if (to - from < 1e-4) continue;
          const mid = (from + to) / 2,
            archHere = L.arches.find((a) => mid > a.from && mid < a.to),
            pierHere = L.piers.findIndex((p) => mid > p.from && mid < p.to),
            abutHere = mid >= a0 - lab && mid <= a1 + lab;
          // The wall over a pier or abutment is that pier's or abutment's side face.
          set(archHere ? 'spandrel' : pierHere >= 0 ? 'pier' : abutHere ? 'abutment' : 'approach-wall');
          const n = archHere ? Math.max(12, Math.ceil((to - from) / 0.5)) : Math.max(1, Math.ceil((to - from) / 1));
          const columns = [];
          for (let j = 0; j <= n; j++) {
            const xa = from + ((to - from) * j) / n,
              [x, z] = at(xa, v);
            const bottom = archHere
              ? L.soffit(archHere, xa)
              : pierHere >= 0
                ? pierFoot[pierHere]
                : abutHere
                  ? mid < a0
                    ? foot0
                    : foot1
                  : Math.min(h, level(x, z) - 0.4);
            columns.push([x, z, bottom, h + 0.02]);
          }
          wallFace(body, columns, side);
        }
        // Projecting arch ring (archivolt) on the face.
        set('ring');
        const proud = side * (half + 0.05);
        for (const a of L.arches) {
          const n = Math.max(12, Math.ceil((a.to - a.from) / 0.5)),
            centreY = L.springing - (L.radius - L.rise),
            outer = (xa) => {
              const dx = xa - a.mid,
                y = L.soffit(a, xa) - centreY,
                r = Math.hypot(dx, y);
              return [a.mid + (dx * (r + L.ringDepth)) / r, centreY + (y * (r + L.ringDepth)) / r];
            };
          for (let j = 0; j < n; j++) {
            const xa = a.from + ((a.to - a.from) * j) / n,
              xb = a.from + ((a.to - a.from) * (j + 1)) / n,
              [oa, ya] = outer(xa),
              [ob, yb] = outer(xb),
              sa = L.soffit(a, xa),
              sb = L.soffit(a, xb),
              out = [-u3[2] * side, 0, u3[0] * side];
            face(body, [p3(xa, proud, sa), p3(xb, proud, sb), p3(ob, proud, yb), p3(oa, proud, ya)], out);
            face(body, [p3(xa, v, sa), p3(xb, v, sb), p3(xb, proud, sb), p3(xa, proud, sa)], [0, -1, 0]);
            face(body, [p3(oa, v, ya), p3(ob, v, yb), p3(ob, proud, yb), p3(oa, proud, ya)], [0, 1, 0]);
          }
        }
        // String course just under the deck, along the whole face.
        set('string');
        const c = frame.at(frame.length / 2, side * half);
        block(m.stone, c, tangent, frame.length, 0.14, h - 0.32, h - 0.12, true);
      }
      info.arches = L.arches.length;
      info.span = +L.span.toFixed(2);
      info.springing = L.springing;
      info.crownSoffit = +L.crown.toFixed(3);
      info.rise = +L.rise.toFixed(3);
      info.crownClearance = +(L.crown - waterLevel).toFixed(3);
    } else {
      // Deck bridges: brick abutments at the water edges, walled approaches on land, a timber or
      // iron deck between, or the recorded slab.
      const under = L.deckUnderside,
        plank = form.form === 'slab-deck' ? h - 0.4 : h - 0.12;
      set('abutment');
      for (const [from, to, foot] of [
        [a0 - lab, a0, foot0],
        [a1, a1 + lab, foot1],
      ]) {
        const mid = (from + to) / 2;
        block(m.brick, frame.at(mid), frame.tangent(mid), to - from, W + 0.6, foot, plank, true);
      }
      set('deck');
      for (const g of frame.segments) {
        const mid = g.s0 + g.length / 2;
        block(form.form === 'slab-deck' ? m.stone : m.wood, frame.at(mid), [g.ux, g.uz], g.length, W, plank, h, true);
      }
      // Girders or beams over the span, bearing 0.3 m into each abutment.
      const beams =
        form.form === 'iron-deck'
          ? [-half + 0.2, ...(W > 4 ? [0] : []), half - 0.2].map((v) => [v, 0.3, m.iron])
          : form.form === 'timber-deck'
            ? (W > 3 ? [-0.375, -0.125, 0.125, 0.375] : [-0.3, 0.3]).map((f) => [f * W, 0.25, m.wood])
            : [];
      set(form.form === 'iron-deck' ? 'girder' : 'beam');
      const s0 = a0 - 0.3,
        s1 = a1 + 0.3;
      for (const g of frame.segments) {
        const from = Math.max(s0, g.s0),
          to = Math.min(s1, g.s0 + g.length);
        if (to <= from) continue;
        for (const [v, thick, material] of beams)
          block(material, frame.at((from + to) / 2, v), [g.ux, g.uz], to - from, thick, under, plank, true);
        if (form.form === 'iron-deck')
          for (let s = Math.ceil(from / 1.5) * 1.5; s < to; s += 1.5)
            block(m.iron, frame.at(s), frame.tangent(s), 0.15, W - 0.4, plank - 0.35, plank, true);
      }
      // Walled approaches on land between the route ends and the abutments.
      set('approach-wall');
      for (const side of [-1, 1])
        for (const [from, to] of [
          [0, a0 - lab],
          [a1 + lab, frame.length],
        ]) {
          if (to - from < 1e-3) continue;
          const n = Math.max(1, Math.ceil(to - from)),
            columns = [];
          for (let j = 0; j <= n; j++) {
            const s = from + ((to - from) * j) / n,
              [x, z] = frame.at(s, side * half);
            columns.push([x, z, Math.min(plank, level(x, z) - 0.4), plank]);
          }
          wallFace(m.brick, columns, side);
        }
      info.deckUnderside = +under.toFixed(3);
      info.deckClearance = +(under - waterLevel).toFixed(3);
    }

    // Parapets (masonry) or railings, both sides, the full route length.
    const masonry = arch || form.form === 'slab-deck';
    for (const side of [-1, 1]) {
      const name = side > 0 ? 'left' : 'right';
      if (masonry) {
        set(`parapet-${name}`);
        const material = form.form === 'stone-arch' ? m.stone : m.brick,
          thick = arch ? defaults.parapetThickness : 0.3,
          top = h + defaults.parapetHeight;
        for (const g of frame.segments) {
          const mid = g.s0 + g.length / 2,
            u = [g.ux, g.uz];
          block(material, frame.at(mid, side * (half - thick / 2)), u, g.length, thick, h, top);
          block(
            m.stone,
            frame.at(mid, side * (half - thick / 2)),
            u,
            g.length,
            thick + 0.1,
            top,
            top + defaults.copingHeight,
            true
          );
        }
        if (arch) {
          // End piers where the parapets meet the approaches.
          set('end-pier');
          for (const s of [0.35, frame.length - 0.35]) {
            const c = frame.at(s, side * (half - 0.35));
            block(material, c, frame.tangent(s), 0.7, 0.7, h, top + 0.25);
            block(m.stone, c, frame.tangent(s), 0.85, 0.85, top + 0.25, top + 0.37, true);
          }
        }
      } else {
        set(`railing-${name}`);
        const iron = form.form === 'iron-deck',
          material = iron ? m.iron : m.wood,
          post = iron ? 0.08 : 0.12,
          rail = defaults.railingHeight,
          v = side * (half - post / 2);
        const stations = [0];
        for (const g of frame.segments) {
          const n = Math.max(1, Math.ceil(g.length / (iron ? 1.8 : 2)));
          for (let j = 1; j <= n; j++) stations.push(g.s0 + (g.length * j) / n);
        }
        for (const s of stations)
          block(material, frame.at(Math.min(s, frame.length - 1e-6), v), frame.tangent(s), post, post, h, h + rail);
        for (const g of frame.segments) {
          const mid = g.s0 + g.length / 2;
          for (const [y, size] of [
            [h + rail - 0.07, iron ? 0.06 : 0.1],
            [h + 0.5, iron ? 0.04 : 0.08],
          ])
            block(material, frame.at(mid, v), [g.ux, g.uz], g.length, size, y, y + size * (iron ? 1 : 1.4), true);
        }
      }
    }

    // Wing walls: from each abutment corner along the bank, splayed back into the approach.
    set('wing');
    const wingLength = arch ? Math.min(5, Math.max(2, (h - L.springing) * 0.9)) : 1.5,
      wingTop = arch ? h - 0.12 : L.deckUnderside;
    for (const [xa, foot, land] of [
      [a0, foot0, -1],
      [a1, foot1, 1],
    ])
      for (const side of [-1, 1]) {
        // Along the face line (skewed), outward, then turned 30 degrees towards the land.
        const fl = Math.hypot(k, 1),
          fs = (k * side) / fl,
          fv = side / fl,
          ds = Math.cos(Math.PI / 6) * fs + Math.sin(Math.PI / 6) * land,
          dv = Math.cos(Math.PI / 6) * fv,
          dl = Math.hypot(ds, dv);
        const start = [xa + k * side * half, side * half],
          dir = [ds / dl, dv / dl],
          columns = [],
          back = [];
        const end = frame.at(start[0] + dir[0] * wingLength, start[1] + dir[1] * wingLength),
          endTop = Math.min(wingTop, Math.max(level(...end) + 0.45, (arch ? L.springing : waterLevel) + 0.3));
        for (let j = 0; j <= 5; j++) {
          const t = j / 5,
            s = start[0] + dir[0] * wingLength * t,
            v = start[1] + dir[1] * wingLength * t,
            [x, z] = frame.at(s, v),
            [bx, bz] = frame.at(s + land * 0.5, v),
            top = wingTop + (endTop - wingTop) * t,
            bottom = Math.min(foot, level(x, z) - 0.4, top);
          columns.push([x, z, bottom, top]);
          back.push([bx, bz, bottom, top]);
        }
        // Water-facing side, back side, top and end. The side sign makes each face point outward.
        const face0 = frame.at(start[0], start[1]),
          face1 = frame.at(start[0] + dir[0], start[1] + dir[1]),
          toBack = frame.at(start[0] + land, start[1]),
          cross = (face1[0] - face0[0]) * (toBack[1] - face0[1]) - (face1[1] - face0[1]) * (toBack[0] - face0[0]),
          wallSide = cross > 0 ? -1 : 1;
        wallFace(body, columns, wallSide);
        wallFace(body, back, -wallSide);
        for (let j = 1; j < columns.length; j++)
          face(
            m.stone,
            [
              [columns[j - 1][0], columns[j - 1][3], columns[j - 1][1]],
              [columns[j][0], columns[j][3], columns[j][1]],
              [back[j][0], back[j][3], back[j][1]],
              [back[j - 1][0], back[j - 1][3], back[j - 1][1]],
            ],
            [0, 1, 0]
          );
        const e = columns.at(-1),
          b = back.at(-1);
        face(
          body,
          [
            [e[0], e[2], e[1]],
            [b[0], b[2], b[1]],
            [b[0], b[3], b[1]],
            [e[0], e[3], e[1]],
          ],
          [e[0] - columns.at(-2)[0], 0, e[1] - columns.at(-2)[1]]
        );
      }

    // End closures under the deck at both route ends, set 0.05 m inside so they never fight the
    // approach fill drawn on the same line.
    for (const [s, dir] of [
      [0.05, -1],
      [frame.length - 0.05, 1],
    ]) {
      // Where an abutment reaches the route end the closure is the abutment's back.
      const reach = Math.abs(k) * half;
      set((dir < 0 ? s + reach >= a0 - lab : s - reach <= a1 + lab) ? 'abutment' : 'closure');
      const t = frame.tangent(s),
        top = arch ? h : L.deckUnderside,
        foot = lowest([-half, 0, half].map((v) => frame.at(s, v))) - 0.4;
      if (foot < top)
        face(
          body,
          [
            [...frame.at(s, -half), foot],
            [...frame.at(s, half), foot],
            [...frame.at(s, half), top],
            [...frame.at(s, -half), top],
          ].map(([x, z, y]) => [x, y, z]),
          [t[0] * dir, 0, t[1] * dir]
        );
    }
    review.push(info);
  }
  const meshes = batch.build(THREE, scene, { name: 'Road bridge structures' });
  const triangles = meshes.reduce((sum, mesh) => sum + mesh.geometry.getAttribute('position').count / 3, 0);
  return { bridges: review, meshes: meshes.length, triangles, parts };
}
