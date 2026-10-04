// Railway bridges about 1900, and the railway earthworks the main landscape adds or removes.
// Register: data/maps/railway-bridge-forms.json, copied here as railwayBridgeForms
// (scripts/check_railway_embankments.mjs fails if the copies differ). The earthworks themselves
// (embankment kept off drawn water and building footprints, brick abutment, wing and retaining
// faces, earth ends) are built by scripts/build_main_landscape.py into main-landscape-1900.json
// railwaySlopes[].works; this module only draws them. Bridge decks, girders and piers are drawn
// from the register; their forms and dimensions are estimates (see each record's evidence).
import { createTriangleBatcher } from './lib/geometry.js';

export const railwayBridgeForms = /* REGISTER */ {
  description:
    'Railway bridges whose openings the main landscape keeps clear of embankment (scripts/build_main_landscape.py RAIL_OPENINGS; main-landscape-1900.json railwayWorks), and the treatment of each raised railway line end, about 1900. The railway routes and formation heights in docs/data/infrastructure.json are not changed here. docs/railway-bridges.js carries an identical copy as railwayBridgeForms, and scripts/check_railway_embankments.mjs fails if the two differ.',
  frame:
    "route-start bridges: stations are metres along the straight line from the railway route's first point through its second, negative before the first point; offsets are metres across it, positive on the left (the normal (-uz, ux)). An abutment face is given by its stations on the centreline (centre) and on the left and right main girder lines (offset +girderOffset and -girderOffset); a pier line by its centreline station and its skew, the shift of its station per metre of offset. chainage bridges: start and end are metres along the railway route, as in that railway's own bridges list. Heights are scene y metres; the static water is y 0.06. Measured stations are on the centreline and at offsets +-4.15 m (LT&SR girder lines) or +-4.5 m (North London crest edges).",
  sources: [
    {
      id: 'os-five-foot',
      citation:
        'OS London five-foot plan, 1893-96 revision, NLS tiles read with scripts/factory_map_sources.py mosaic() at zoom 18 (about 0.38 m per pixel)',
      use: "The railway alignments across Bow Creek and the Hackney Cut, the creek and canal edges, the embankment hachures, and the lines continuing beyond the model's route ends. The deck structure, piers and abutment faces under a deck cannot be read in plan at this scale.",
    },
    {
      id: 'os-25-inch',
      citation: 'OS 25-inch London sheets, 1890s revision, NLS tiles at zoom 17, read the same way',
      use: 'Cross-check of the Bow Creek crossing (high- and low-water marks, BOW CREEK lettering) and the Hackney Cut crossing.',
    },
    {
      id: 'drawn-water',
      citation:
        'Low-water polygons as the main landscape builder masks them: river-system water polygons, ground-plan rivers and marsh ditches',
      use: 'Abutment faces stand at the drawn water edge (0.4 m back from it). The stations below are model measurements of the walls the builder draws, not surveyed abutments.',
    },
    {
      id: 'photo-catalogue',
      citation: 'reference/photo-review-2026-10-03/reports/photo-catalogue.md',
      use: 'No archive image of either bridge is used; no detail is copied from a photograph.',
    },
  ],
  bridges: {
    'ltsr-bow-creek': {
      railway: 'London, Tilbury and Southend Railway',
      frame: 'route-start',
      replacesCrossing: 0,
      form: 'half-through-plate-girder',
      spans: 2,
      girderOffset: 4.15,
      girderDepth: 1.9,
      girderAboveFormation: 0.65,
      bearing: 0.6,
      abutments: {
        west: {
          centre: -8.3,
          left: -13.04,
          right: -3.07,
        },
        east: {
          centre: 36.36,
          left: 32.46,
          right: 40.26,
        },
      },
      piers: [
        {
          centre: 12.98,
          skew: -1.08,
          thickness: 1.6,
        },
      ],
      approach: {
        from: 0,
        to: -16.8,
      },
      waterEdges: {
        centre: [-7.66, 33.62],
        left: [-12.51, 29.72],
        right: [-2.44, 37.51],
      },
      evidence:
        "Mapped (OS five-foot and 25-inch): the LT&SR crossing Bow Creek on a continuous structure, the rails unbroken from bank to bank with a footbridge (F.B.) alongside on the north, the line continuing west past Bow Pottery on embankment, and the creek's high- and low-water marks. Measured in the model: the traced route begins in the creek, 7.7 m east of the drawn west water edge on the centreline; the drawn water spans stations -7.7 to 33.6 on the centreline, the banks crossing the line at about 50 degrees. Interpreted: brick abutments with in-line wings on both drawn banks, two half-through wrought-iron plate-girder spans of about 21 and 23 m on one brick river pier set parallel to the banks, girders 1.9 m deep standing 0.65 m above the formation. No pier is visible on the OS plan, where a pier under the deck would not show; the pier, spans and girder depth are estimates. West of the abutment the traced line is not modelled: the fill is carried at formation level to station -16.8 and closed there by an earth end.",
    },
    'nl-hackney-cut': {
      railway: 'North London / Victoria Park branch connection',
      frame: 'chainage',
      start: 62.8,
      end: 82.3,
      waterEdges: {
        centre: [64.54, 80.76],
        left: [65.29, 81.51],
        right: [63.82, 80.01],
      },
      abutments: {
        west: {
          centre: 64.14,
          left: 64.89,
        },
        east: {
          centre: 81.17,
          left: 81.92,
          right: 80.42,
        },
      },
      evidence:
        "Mapped (OS five-foot): the Victoria Park branch crossing the Lee Navigation (Hackney Cut) on a bridge beside Hackney Wick Works, the canal running on under the line, and the line continuing west on embankment. The traced embankment ran unbroken over the drawn canal (77 triangles over its water). Measured in the model: the drawn canal spans chainage 63.8 to 81.5 across the crest (64.5 to 80.8 on the centreline); the abutment faces stand at 64.1 and 81.2 on the centreline. On the right-hand crest edge the traced fill already stopped at chainage 51.3, where it had been cut back from the branch's northern water; that notch now has the same brick face. Interpreted: brick abutments with in-line wings at the canal edges and the same iron girder deck the model draws at this railway's other bridges, at the traced 3.0 m formation, which leaves only about 2.3 m under the girders; the formation height is the traced, unmeasured value and is not changed here.",
    },
  },
  lineEnds: {
    'london-tilbury-and-southend-west': {
      railway: 'London, Tilbury and Southend Railway',
      point: [-605.37, 605.86],
      treatment: 'west abutment on the drawn bank, level approach to station -16.8, earth end at the side slope',
      osShowsLineContinuing: true,
      evidence:
        'OS five-foot: the line continues west across Bow Creek past Bow Pottery towards Bromley. Carrying it on would need a route beyond the traced one, which this register does not add.',
    },
    'north-london-connection-west': {
      railway: 'North London / Victoria Park branch connection',
      point: [-1700.0, -1376.09],
      treatment: 'earth end at the side slope',
      osShowsLineContinuing: true,
      evidence:
        "OS five-foot: the Victoria Park branch continues west on embankment past Hackney Wick Works and the Phoenix Chemical Works beyond the traced route's clip at x -1700 (north-london-connection westClipX). The model's ground runs on to about x -2700, so this is not the model edge; carrying the line there needs route data, not changed here.",
    },
    'great-eastern-mainline-west': {
      railway: 'Great Eastern Railway — main line',
      point: [-1483.61, -26.01],
      treatment: 'earth end at the side slope',
      osShowsLineContinuing: true,
      evidence:
        'OS five-foot: the main line continues west-south-west on embankment through Bow Junction. Not the model edge; route data not changed here.',
    },
    'great-eastern-mainline-east': {
      railway: 'Great Eastern Railway — main line',
      point: [-316.36, -1277.9],
      treatment: 'earth end at the side slope',
      osShowsLineContinuing: true,
      evidence:
        'OS five-foot: the main line continues north-east into Stratford Station. Not the model edge; route data not changed here.',
    },
  },
}; /* END REGISTER */

// The embankment triangles to draw for a railway, its brick faces and a summary, after the main
// landscape's railway works (none without the main landscape).
export function railwayWorks(railway, mainLandscape) {
  const profile = mainLandscape?.meta.railwaySlopes?.find((p) => p.name === railway.name),
    works = profile?.works;
  if (!works) return { embankment: railway.embankment, walls: [], removed: 0, added: 0 };
  const removed = new Set(works.removedTriangles);
  return {
    embankment: [...railway.embankment.filter((_, i) => !removed.has(i)), ...works.addedTriangles],
    walls: works.walls,
    removed: removed.size,
    added: works.addedTriangles.length,
  };
}

// Bridge intervals the register adds to a detailed railway's own bridges list (great-eastern.js
// draws its standard girder deck over them).
export function addedBridgeIntervals(railway) {
  return Object.entries(railwayBridgeForms.bridges)
    .filter(([, b]) => b.railway === railway.name && b.frame === 'chainage')
    .map(([id, b]) => ({ start: b.start, end: b.end, sewer: false, register: id }));
}

export function replacedCrossings(railway) {
  return new Set(
    Object.values(railwayBridgeForms.bridges)
      .filter((b) => b.railway === railway.name && b.frame === 'route-start')
      .map((b) => b.replacesCrossing)
  );
}

// Station of an abutment face or pier line at offset o, from its centre/left/right stations.
export function faceStation(face, o, g) {
  if (face.skew !== undefined) return face.centre + face.skew * o;
  const side = o >= 0 ? face.left : face.right;
  return face.centre + ((side - face.centre) * Math.abs(o)) / g;
}

export function bridgeFrame(railway) {
  const [a, b] = railway.route,
    length = Math.hypot(b[0] - a[0], b[1] - a[1]),
    u = [(b[0] - a[0]) / length, (b[1] - a[1]) / length],
    n = [-u[1], u[0]];
  return { a, u, n, at: (s, o, y) => [a[0] + u[0] * s + n[0] * o, y, a[1] + u[1] * s + n[1] * o] };
}

export function railwayBridges({ THREE, scene, materials: m, railways, level, box, ballast }) {
  const batch = createTriangleBatcher(),
    iron = m.iron,
    brick = m.brick.clone(),
    review = [];
  brick.side = THREE.DoubleSide;
  // A plan quad a-b-c-d (each [x, z]) extruded from y0 to y1, all faces, uv in metres.
  function prism(material, quad, y0, y1) {
    // Order the corners so the top faces up (and the sides out).
    const [a, b, c] = quad,
      up = (b[1] - a[1]) * (c[0] - a[0]) - (b[0] - a[0]) * (c[1] - a[1]),
      corners = up >= 0 ? quad : [...quad].reverse();
    const top = corners.map(([x, z]) => [x, y1, z]),
      bottom = corners.map(([x, z]) => [x, y0, z]),
      plan = (p) => [p[0], p[2]];
    batch.quad(material, top[0], top[1], top[2], top[3], top.map(plan));
    batch.quad(material, bottom[3], bottom[2], bottom[1], bottom[0], bottom.map(plan));
    for (let i = 0; i < 4; i++) {
      const j = (i + 1) % 4,
        run = Math.hypot(corners[j][0] - corners[i][0], corners[j][1] - corners[i][1]);
      batch.quad(material, bottom[i], bottom[j], top[j], top[i], [
        [0, y0],
        [run, y0],
        [run, y1],
        [0, y1],
      ]);
    }
  }
  for (const [id, form] of Object.entries(railwayBridgeForms.bridges)) {
    if (form.frame !== 'route-start') continue;
    const railway = railways.find((r) => r.name === form.railway);
    if (!railway) continue;
    const f = bridgeFrame(railway),
      h = railway.formationHeight,
      g = form.girderOffset,
      top = h + form.girderAboveFormation,
      soffit = top - form.girderDepth,
      west = (o) => faceStation(form.abutments.west, o, g),
      east = (o) => faceStation(form.abutments.east, o, g),
      xz = (s, o) => {
        const p = f.at(s, o, 0);
        return [p[0], p[2]];
      };
    let girders = 0,
      stiffeners = 0;
    // Main girders: one per span on each side, from bearing to bearing; web, flanges, stiffeners.
    for (const side of [1, -1]) {
      const o = side * g,
        stops = [west(o) - form.bearing, ...form.piers.map((p) => faceStation(p, o, g)), east(o) + form.bearing];
      for (let k = 1; k < stops.length; k++) {
        const s0 = stops[k - 1] + (k > 1 ? 0.03 : 0),
          s1 = stops[k] - (k < stops.length - 1 ? 0.03 : 0),
          plate = (half, y0, y1) =>
            prism(iron, [xz(s0, o - half), xz(s1, o - half), xz(s1, o + half), xz(s0, o + half)], y0, y1);
        plate(0.06, soffit + 0.04, top - 0.04);
        plate(0.25, top - 0.04, top);
        plate(0.25, soffit, soffit + 0.04);
        girders++;
        for (let s = s0 + 0.75; s < s1 - 0.3; s += 1.5) {
          prism(
            iron,
            [xz(s - 0.05, o - 0.2), xz(s + 0.05, o - 0.2), xz(s + 0.05, o + 0.2), xz(s - 0.05, o + 0.2)],
            soffit,
            top
          );
          stiffeners++;
        }
      }
    }
    // Deck plate between the girders, ends on the abutment faces; cross girders beneath it.
    const d = g - 0.06;
    // In two halves, so each end follows the abutment face through its centreline station.
    for (const side of [d, -d])
      prism(iron, [xz(west(0), 0), xz(east(0), 0), xz(east(side), side), xz(west(side), side)], h - 0.3, h);
    let crossGirders = 0;
    for (let s = Math.max(west(d), west(-d)) + 1; s < Math.min(east(d), east(-d)) - 0.5; s += 2) {
      prism(iron, [xz(s - 0.12, -d), xz(s + 0.12, -d), xz(s + 0.12, d), xz(s - 0.12, d)], soffit + 0.35, h - 0.3);
      crossGirders++;
    }
    // River piers parallel to the banks: brick shaft and a stone cap under the girder bearings.
    for (const pier of form.piers) {
      const reach = g + 0.9,
        corner = (o, t) => xz(faceStation(pier, o, g) + t, o),
        foot = Math.min(level(...xz(pier.centre, 0)), -1.2) - 0.3,
        t = pier.thickness / 2;
      prism(brick, [corner(-reach, -t), corner(-reach, t), corner(reach, t), corner(reach, -t)], foot, soffit - 0.35);
      prism(
        m.stone,
        [
          corner(-reach - 0.2, -t - 0.15),
          corner(-reach - 0.2, t + 0.15),
          corner(reach + 0.2, t + 0.15),
          corner(reach + 0.2, -t - 0.15),
        ],
        soffit - 0.35,
        soffit
      );
    }
    // Track on the bridge and the approach west of the traced route's first point.
    const [s0, s1] = [form.approach.to, form.approach.from],
      group = new THREE.Group(),
      length = s1 - s0,
      mid = f.at((s0 + s1) / 2, 0, 0);
    group.position.set(mid[0], 0, mid[2]);
    group.rotation.y = -Math.atan2(f.u[1], f.u[0]);
    scene.add(group);
    box(group, 0, h, 0, length, 0.24, 8.6, ballast);
    for (const track of [-1.8, 1.8]) {
      for (const rail of [-0.718, 0.718]) box(group, 0, h + 0.33, track + rail, length, 0.13, 0.09, iron);
      for (let x = -length / 2 + 1.25; x < length / 2; x += 2.5)
        box(group, x, h + 0.24, track, 0.22, 0.18, 2.4, m.wood);
    }
    review.push({
      id,
      railway: railway.name,
      form: form.form,
      deck: { from: [west(g), west(0), west(-g)], to: [east(g), east(0), east(-g)], height: h },
      girders,
      stiffeners,
      crossGirders,
      piers: form.piers.length,
    });
  }
  const meshes = batch.build(THREE, scene, { name: 'railway-bridge-structure' });
  return { bridges: review, meshes: meshes.length };
}

// Brick faces from main-landscape railway works: quads [top a, top b, foot b, foot a].
export function railwayWalls({ THREE, scene, materials: m, walls, name }) {
  if (!walls.length) return null;
  const batch = createTriangleBatcher(),
    brick = m.brick.clone();
  brick.side = THREE.DoubleSide;
  for (const [a, b, c, d] of walls) {
    const run = Math.hypot(b[0] - a[0], b[2] - a[2]);
    batch.quad(brick, d, c, b, a, [
      [0, d[1]],
      [run, c[1]],
      [run, b[1]],
      [0, a[1]],
    ]);
  }
  return batch.build(THREE, scene, { name });
}
