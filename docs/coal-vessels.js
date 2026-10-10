// Original, source-informed vessel studies. Dimensions, cargo and placements live
// in coal-traffic.json; these are representative types, not identified ships.
import { box, cylinder, beam } from './lib/geometry.js';
import { createRandom } from './lib/prng.js';

export function vesselPoint(vessel, x, z) {
  const a = (vessel.heading * Math.PI) / 180;
  return [vessel.x + x * Math.cos(a) + z * Math.sin(a), vessel.z - x * Math.sin(a) + z * Math.cos(a)];
}

export function vesselHolds(spec) {
  return spec.vessels.flatMap((v) =>
    spec.forms[v.form].holds.map((h) => ({
      centre: vesselPoint(v, 0, h.z),
      heading: v.heading,
      halfWidth: h.width / 2,
      minZ: -h.length / 2,
      maxZ: h.length / 2,
      endCurve: 0,
    }))
  );
}

// Local bow is -z. Cross sections include the submerged bottom, rounded bilges,
// narrowing shoulders, a raked stem and rising end decks. There is no top cap:
// each deck is built around its real open cargo hatch, never over the coal.
export function hullSections(form) {
  const factors =
    form.kind === 'collier' || form.kind === 'tug'
      ? [
          [-1, 0.02],
          [-0.96, 0.24],
          [-0.88, 0.6],
          [-0.72, 0.88],
          [-0.5, 0.98],
          [-0.25, 1],
          [0, 1],
          [0.35, 1],
          [0.65, 0.91],
          [0.84, 0.69],
          [0.96, 0.36],
          [1, 0.12],
        ]
      : [
          [-1, 0.3],
          [-0.96, 0.62],
          [-0.87, 0.91],
          [-0.72, 1],
          [-0.4, 1],
          [0, 1],
          [0.4, 1],
          [0.72, 1],
          [0.87, 0.91],
          [0.96, 0.62],
          [1, 0.3],
        ];
  return factors.map(([t, width]) => ({
    z: (t * form.length) / 2,
    w: (width * form.beam) / 2,
    y: form.freeboard + form.sheer * Math.pow(Math.abs(t), 4),
    t,
  }));
}

export function coalVessels({ THREE, scene, spec, materials, tideLow, waterLevel, lite = false }) {
  const fleet = new THREE.Group();
  fleet.name = 'Coal traffic — steam colliers, lighters and Lea barges';
  scene.add(fleet);
  const materialCache = new Map();
  // Original seamless coal aggregate fills the gaps between the small 3D pieces.
  const grainRandom = createRandom(6143),
    cells = Array.from({ length: 32 * 32 }, () => ({ x: grainRandom(), y: grainRandom(), tone: grainRandom() })),
    grainPixels = new Uint8Array(256 * 256 * 4),
    grainHeights = new Uint8Array(256 * 256 * 4);
  for (let py = 0; py < 256; py++)
    for (let px = 0; px < 256; px++) {
      const x = px / 8,
        y = py / 8,
        ix = Math.floor(x),
        iy = Math.floor(y);
      let nearest = Infinity,
        second = Infinity,
        tone = 0;
      for (let dy = -1; dy <= 1; dy++)
        for (let dx = -1; dx <= 1; dx++) {
          const cell = cells[((iy + dy + 32) % 32) * 32 + ((ix + dx + 32) % 32)],
            d = (ix + dx + cell.x - x) ** 2 + (iy + dy + cell.y - y) ** 2;
          if (d < nearest) {
            second = nearest;
            nearest = d;
            tone = cell.tone;
          } else if (d < second) second = d;
        }
      const edge = Math.min(1, (Math.sqrt(second) - Math.sqrt(nearest)) * 7),
        v = Math.round((115 + tone * 95) * (0.42 + edge * 0.58)),
        h = Math.round(40 + 160 * edge * Math.max(0.2, 1 - Math.sqrt(nearest) * 0.55)),
        i = (py * 256 + px) * 4;
      grainPixels.set([v, v, v, 255], i);
      grainHeights.set([h, h, h, 255], i);
    }
  const fineCoalMap = new THREE.DataTexture(grainPixels, 256, 256),
    fineCoalBump = new THREE.DataTexture(grainHeights, 256, 256);
  fineCoalMap.colorSpace = THREE.SRGBColorSpace;
  for (const texture of [fineCoalMap, fineCoalBump]) {
    texture.wrapS = texture.wrapT = THREE.RepeatWrapping;
    texture.repeat.setScalar(1 / (spec.appearance?.coalGrainTileMetres ?? 2));
    texture.magFilter = THREE.LinearFilter;
    texture.minFilter = THREE.LinearMipmapLinearFilter;
    texture.generateMipmaps = true;
    texture.needsUpdate = true;
  }
  const colour = (name, hex, mode) => {
    const key = `${name}:${hex}:${mode}`;
    if (!materialCache.has(key)) {
      const source = name === 'coal' ? materials.coal : name === 'wood' ? materials.wood : materials.iron;
      const m = source.clone();
      m.color.set(hex);
      m.roughness = name === 'coal' ? 0.55 : 0.9;
      m.metalness = name === 'iron' ? 0.12 : 0;
      m.side = THREE.DoubleSide;
      m.userData.surface = `vessel-${name}`;
      if (name === 'coal' && fineCoalMap) {
        m.map = fineCoalMap;
        m.bumpMap = fineCoalBump;
        m.bumpScale = 0.012;
      }
      if (mode === 'tidal') m.userData.tidalFloat = true;
      materialCache.set(key, m);
    }
    return materialCache.get(key);
  };
  const counts = { collier: 0, lighter: 0, 'lea-barge': 0, tug: 0, workers: 0, coalChunks: 0 };
  const byId = new Map();
  const B = (p, x, y, z, w, h, d, m) => box(THREE, p, x, y, z, w, h, d, m);
  const C = (p, x, y, z, rt, rb, h, m, n = 8) => cylinder(THREE, p, x, y, z, rt, rb, h, m, n);
  const E = (p, a, b, r, m) => beam(THREE, p, a, b, r, m);
  const quad = (a, b, c, d) => [...a, ...b, ...c, ...a, ...c, ...d];
  function mesh(parent, positions, material, name, indices = null) {
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    if (indices) geometry.setIndex(indices);
    geometry.computeVertexNormals();
    const object = new THREE.Mesh(geometry, material);
    object.name = name;
    parent.add(object);
    return object;
  }
  function rope(parent, points, material, radius = 0.026) {
    const geometry = new THREE.TubeGeometry(
      new THREE.CatmullRomCurve3(points.map((p) => new THREE.Vector3(...p))),
      lite ? 8 : 16,
      radius,
      5,
      false
    );
    const object = new THREE.Mesh(geometry, material);
    parent.add(object);
    return object;
  }
  // Soft procedural puffs suggest the steam working river in Wyllie's view.
  // Static visual atmosphere, not an emissions or wind simulation.
  const smokePixels = new Uint8Array(32 * 32 * 4);
  for (let y = 0; y < 32; y++)
    for (let x = 0; x < 32; x++) {
      const r = Math.hypot((x - 15.5) / 15.5, (y - 15.5) / 15.5),
        i = (y * 32 + x) * 4;
      smokePixels.set([255, 255, 255, Math.round(255 * Math.pow(Math.max(0, 1 - r), 2))], i);
    }
  const smokeMap = new THREE.DataTexture(smokePixels, 32, 32);
  smokeMap.needsUpdate = true;
  smokeMap.magFilter = THREE.LinearFilter;
  function smoke(parent, y, z, scale, mode, random) {
    const positions = [];
    for (let i = 0; i < (lite ? 16 : 28); i++) {
      const t = i / (lite ? 15 : 27);
      positions.push(
        (t * 3 + (random() - 0.5) * t) * scale,
        y + t * 7 * scale,
        z + t * 6 * scale + (random() - 0.5) * t * scale
      );
    }
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    const material = new THREE.PointsMaterial({
      color: '#575952',
      map: smokeMap,
      size: 3.1 * scale,
      opacity: 0.24,
      transparent: true,
      depthWrite: false,
    });
    if (mode === 'tidal') material.userData.tidalFloat = true;
    const points = new THREE.Points(geometry, material);
    points.name = 'Steam vessel smoke — interpreted atmosphere';
    parent.add(points);
  }
  function worker(parent, x, y, z, angle, pose, m) {
    const g = new THREE.Group();
    g.position.set(x, y, z);
    g.rotation.y = angle;
    g.name = `Coal worker — ${pose}`;
    parent.add(g);
    const bent = pose === 'shovel';
    const hauling = pose === 'haul',
      random = createRandom(417 + counts.workers * 131),
      shift = (random() - 0.5) * 0.09,
      phase = (counts.workers % 3) / 2;
    g.scale.setScalar(0.96 + random() * 0.08);
    const hip = [shift, bent ? 0.79 : hauling ? 0.88 - phase * 0.06 : 0.88, bent ? 0.12 : 0.03],
      shoulder = [
        shift * 0.5,
        bent ? 1.13 : hauling ? 1.36 - phase * 0.1 : 1.36,
        bent ? -0.34 : hauling ? 0.11 + phase * 0.06 : -0.05,
      ];
    // Rounded boots, tapered trouser legs and bent knees replace the rigid rods.
    const ellipsoid = (centre, scale, material, segments = 8, rings = 4) => {
      const object = new THREE.Mesh(new THREE.SphereGeometry(1, segments, rings), material);
      object.position.fromArray(centre);
      object.scale.fromArray(scale);
      g.add(object);
      return object;
    };
    const limb = (a, b, ra, rb, material, depth = 0.92) => {
      const av = new THREE.Vector3(...a),
        bv = new THREE.Vector3(...b),
        d = bv.clone().sub(av);
      const object = new THREE.Mesh(new THREE.CylinderGeometry(rb, ra, d.length(), 8), material);
      object.position.copy(av.add(bv).multiplyScalar(0.5));
      object.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), d.normalize());
      object.scale.z = depth;
      g.add(object);
    };
    for (const sign of [-1, 1]) {
      const footZ = sign * (bent ? 0.19 : hauling ? 0.12 + phase * 0.06 : 0.04);
      const ankle = [sign * 0.14, 0.14, footZ],
        knee = [sign * 0.14 + shift * 0.4, bent ? 0.43 : 0.49, footZ - (bent ? 0.15 : 0.035)],
        thigh = [hip[0] + sign * 0.1, hip[1], hip[2]];
      ellipsoid([ankle[0], 0.055, footZ - 0.065], [0.056, 0.055, 0.15], m.dark, 10, 6);
      limb(ankle, knee, 0.066, 0.084, m.trousers);
      ellipsoid(knee, [0.084, 0.086, 0.085], m.trousers, 6);
      limb(knee, thigh, 0.084, 0.11, m.trousers);
    }
    ellipsoid(hip, [0.17, 0.13, 0.105], m.trousers);
    // A four-ring cloth torso has shoulders and a waist rather than a cylindrical trunk.
    const levels = [0, 0.22, 0.76, 1],
      widths = [0.17, 0.175, 0.215, 0.18],
      positions = [],
      indices = [];
    const torsoPoint = (ring, i) => {
      const t = levels[ring],
        a = (i * Math.PI) / 6;
      return [
        hip[0] + (shoulder[0] - hip[0]) * t + Math.cos(a) * widths[ring],
        hip[1] + (shoulder[1] - hip[1]) * t,
        hip[2] + (shoulder[2] - hip[2]) * t + Math.sin(a) * widths[ring] * 0.62,
      ];
    };
    for (let j = 0; j < levels.length; j++)
      for (let i = 0; i < 12; i++) {
        positions.push(...torsoPoint(j, i));
        if (j > 0) {
          const a = (j - 1) * 12 + i,
            b = j * 12 + i,
            c = j * 12 + ((i + 1) % 12),
            d = (j - 1) * 12 + ((i + 1) % 12);
          indices.push(a, b, c, a, c, d);
        }
      }
    mesh(g, positions, m.cloth, 'Loose work shirt and waist', indices);
    ellipsoid([shoulder[0], shoulder[1] - 0.02, shoulder[2]], [0.185, 0.075, 0.11], m.cloth);
    C(g, shoulder[0], shoulder[1] + 0.025, shoulder[2], 0.045, 0.05, 0.09, m.skin, 6);
    const headCentre = [shoulder[0], shoulder[1] + 0.19, shoulder[2] - 0.025];
    const head = ellipsoid(headCentre, [0.101, 0.123, 0.103], m.skin, 8, 6);
    head.rotation.x = bent ? -0.28 : hauling ? 0.12 : 0.04;
    ellipsoid([headCentre[0], headCentre[1] - 0.01, headCentre[2] - 0.1], [0.025, 0.032, 0.035], m.skin, 6);
    const cap = ellipsoid([headCentre[0], headCentre[1] + 0.09, headCentre[2] + 0.008], [0.115, 0.048, 0.11], m.cap);
    cap.rotation.z = shift;
    ellipsoid([headCentre[0], headCentre[1] + 0.064, headCentre[2] - 0.096], [0.1, 0.012, 0.068], m.cap, 6);
    const hands = bent
      ? [
          [-0.08, 0.72, -0.69],
          [0.1, 0.99, -0.5],
        ]
      : hauling
        ? [
            [-0.065, 1.63 + phase * 0.1, -0.28],
            [0.06, 1.77 - phase * 0.05, -0.29],
          ]
        : [
            [-0.17, 1.0, -0.33],
            [0.16, 1.08, -0.29],
          ];
    for (let i = 0; i < 2; i++) {
      const sign = i === 0 ? -1 : 1,
        upper = [shoulder[0] + sign * 0.18, shoulder[1] - 0.035, shoulder[2]],
        elbow = [
          sign * (hauling ? 0.21 : 0.25),
          (shoulder[1] + hands[i][1]) / 2 - (hauling ? 0.1 : 0.06),
          hauling ? -0.18 : -0.26,
        ];
      limb(upper, elbow, 0.09, 0.068, m.cloth);
      ellipsoid(elbow, [0.067, 0.068, 0.067], m.cloth, 6);
      const cuff = elbow.map((v, k) => v + (hands[i][k] - v) * 0.38);
      limb(elbow, cuff, 0.068, 0.059, m.cloth);
      limb(cuff, hands[i], 0.049, 0.034, m.skin);
      ellipsoid(hands[i], [0.036, 0.059, 0.034], m.skin, 6);
    }
    if (bent) {
      const direction = new THREE.Vector3(...hands[0]).sub(new THREE.Vector3(...hands[1])),
        tip = new THREE.Vector3(...hands[1]).addScaledVector(direction, (hands[1][1] - 0.13) / -direction.y),
        top = new THREE.Vector3(...hands[1]).addScaledVector(direction, -0.8);
      E(g, top.toArray(), tip.toArray(), 0.026, m.wood);
      const spade = B(g, tip.x, 0.07, tip.z - 0.07, 0.23, 0.045, 0.32, m.dark);
      spade.rotation.x = -0.25;
    }
    g.updateMatrix();
    g.userData.grip = new THREE.Vector3(...hands[1]).applyMatrix4(g.matrix).toArray();
    counts.workers++;
    return g;
  }
  function coal(parent, h, form, fraction, m, random) {
    const nx = lite ? 6 : 12,
      nz = lite ? 12 : 24;
    const width = h.width - 0.18,
      length = h.length - 0.18;
    const peaks = form.coalPeaks ?? 1;
    const at = (x, z) => {
      let along = 0;
      for (let i = 0; i < peaks; i++) {
        const centre = h.z + ((i - (peaks - 1) / 2) * length) / peaks;
        const radius = peaks === 1 ? length / 2 : length / (peaks * 1.35);
        along = Math.max(along, Math.pow(Math.max(0, 1 - Math.pow((z - centre) / radius, 2)), 0.55));
      }
      return (
        form.freeboard -
        0.2 +
        fraction *
          (0.36 +
            (form.coalHeapHeight ?? 0.72) * Math.pow(Math.max(0, 1 - Math.pow(x / (width / 2), 2)), 0.65) * along) +
        0.07 * Math.sin(x * 8.7 + z * 2.1) * Math.cos(z * 4.3)
      );
    };
    const positions = [],
      indices = [];
    for (let j = 0; j <= nz; j++)
      for (let i = 0; i <= nx; i++) {
        const x = -width / 2 + (i * width) / nx,
          z = h.z - length / 2 + (j * length) / nz;
        positions.push(x, at(x, z), z);
        if (j < nz && i < nx) {
          const a = j * (nx + 1) + i,
            b = a + nx + 1;
          indices.push(a, b, b + 1, a, b + 1, a + 1);
        }
      }
    mesh(parent, positions, m.coal, 'Uneven coal load and fines', indices);
    const pieces = Array.from({ length: 4 }, (_, variant) => {
      const geometry = new THREE.IcosahedronGeometry(1, 0),
        p = geometry.attributes.position;
      for (let i = 0; i < p.count; i++) {
        const x = p.getX(i),
          y = p.getY(i),
          z = p.getZ(i);
        const f = 1 + 0.27 * Math.sin(x * 7 + y * 13 + z * 17 + variant);
        p.setXYZ(i, x * f, y * f * (variant === 0 ? 0.55 : 1), z * f);
      }
      geometry.computeVertexNormals();
      return geometry;
    });
    const chunks = lite ? 55 : Math.round(h.width * h.length * 5);
    for (let i = 0; i < chunks; i++) {
      const x = (random() - 0.5) * width,
        z = h.z + (random() - 0.5) * length;
      const r =
        (spec.appearance?.coalPieceRadiusMin ?? 0.018) +
        Math.pow(random(), 1.7) *
          ((spec.appearance?.coalPieceRadiusMax ?? 0.072) - (spec.appearance?.coalPieceRadiusMin ?? 0.018));
      const object = new THREE.Mesh(pieces[i % pieces.length], i % 7 === 0 ? m.coalLight : m.coal);
      object.position.set(x, at(x, z) + r * 0.3, z);
      object.scale.set(r * (0.85 + random() * 0.5), r * (0.65 + random() * 0.55), r * (0.85 + random() * 0.5));
      object.rotation.set(random() * 3, random() * 3, random() * 3);
      parent.add(object);
    }
    counts.coalChunks += chunks;
  }
  for (const v of spec.vessels) {
    const form = spec.forms[v.form],
      mode = v.water;
    const g = new THREE.Group();
    g.name = v.label;
    g.position.set(v.x, mode === 'tidal' ? tideLow : waterLevel, v.z);
    g.rotation.y = (v.heading * Math.PI) / 180;
    g.userData.vesselId = v.id;
    fleet.add(g);
    byId.set(v.id, { group: g, vessel: v, form });
    counts[form.kind]++;
    const m = {
      hull: colour(
        form.kind === 'collier' || form.kind === 'tug' ? 'iron' : 'wood',
        form.hullColour ?? '#343731',
        mode
      ),
      red: colour('iron', '#745046', mode),
      dark: colour('iron', '#272c29', mode),
      deck: colour('wood', '#8b806a', mode),
      wood: colour('wood', '#686049', mode),
      rope: colour('wood', '#9a8d70', mode),
      cabin: colour('wood', '#aca78e', mode),
      glass: colour('iron', '#344845', mode),
      coal: colour('coal', '#41433d', mode),
      coalLight: colour('coal', '#55574d', mode),
      cloth: colour('cloth', ['#55554a', '#555c5b', '#686455'][counts.workers % 3], mode),
      trousers: colour('cloth', '#3b3e38', mode),
      cap: colour('cloth', '#3d403a', mode),
      skin: colour('skin', '#927e65', mode),
    };
    const random = createRandom(v.seed);
    const stations = hullSections(form);
    const cross = (s) => [
      [-s.w, s.y, s.z],
      [-s.w, -0.15, s.z * 0.99],
      [-s.w * 0.82, -form.draft * 0.7, s.z * 0.94],
      [-s.w * 0.44, -form.draft, s.z * 0.86],
      [s.w * 0.44, -form.draft, s.z * 0.86],
      [s.w * 0.82, -form.draft * 0.7, s.z * 0.94],
      [s.w, -0.15, s.z * 0.99],
      [s.w, s.y, s.z],
    ];
    const positions = [];
    for (let i = 1; i < stations.length; i++) {
      const a = cross(stations[i - 1]),
        b = cross(stations[i]);
      for (let j = 0; j < a.length - 1; j++) positions.push(...quad(a[j], a[j + 1], b[j + 1], b[j]));
    }
    for (const index of [0, stations.length - 1]) {
      const ring = cross(stations[index]);
      for (let i = 1; i < ring.length - 1; i++) positions.push(...ring[0], ...ring[i], ...ring[i + 1]);
    }
    mesh(g, positions, m.hull, 'Hull shell with submerged bilges');
    for (const sign of [-1, 1]) {
      rope(
        g,
        stations.map((s) => [sign * s.w, s.y + 0.06, s.z]),
        m.red,
        form.kind === 'collier' ? 0.105 : 0.075
      );
      rope(
        g,
        stations.map((s) => [sign * s.w * 1.006, -0.02, s.z]),
        m.wood,
        0.075
      );
    }
    const deck = new THREE.Shape(stations.map((s) => new THREE.Vector2(-s.w, -s.z)));
    for (const s of [...stations].reverse()) deck.lineTo(s.w, -s.z);
    deck.closePath();
    for (const h of form.holds) {
      const path = new THREE.Path();
      path.moveTo(-h.width / 2, -h.z + h.length / 2);
      path.lineTo(h.width / 2, -h.z + h.length / 2);
      path.lineTo(h.width / 2, -h.z - h.length / 2);
      path.lineTo(-h.width / 2, -h.z - h.length / 2);
      path.closePath();
      deck.holes.push(path);
    }
    const deckMesh = new THREE.Mesh(new THREE.ShapeGeometry(deck), m.deck);
    deckMesh.rotation.x = -Math.PI / 2;
    deckMesh.position.y = form.freeboard;
    g.add(deckMesh);
    // End decks rise to meet the sheer; the horizontal walkways remain beside the holds.
    for (const sign of [-1, 1]) {
      const end = stations.filter((s) => sign * s.t >= 0.72);
      for (let i = 1; i < end.length; i++) {
        const a = end[i - 1],
          b = end[i];
        mesh(g, quad([-a.w, a.y, a.z], [a.w, a.y, a.z], [b.w, b.y, b.z], [-b.w, b.y, b.z]), m.deck, 'Raised end deck');
      }
    }
    for (const h of form.holds) {
      const floor = form.kind === 'collier' ? -0.5 : -0.38;
      B(g, 0, floor - 0.08, h.z, h.width, 0.08, h.length, m.wood);
      for (const sign of [-1, 1]) {
        B(g, sign * (h.width / 2 + 0.06), floor, h.z, 0.12, form.freeboard - floor + 0.15, h.length + 0.24, m.hull);
        B(g, 0, floor, h.z + sign * (h.length / 2 + 0.06), h.width, form.freeboard - floor + 0.15, 0.12, m.hull);
      }
      if (v.laden) coal(g, h, form, v.loadFraction ?? 1, m, random);
      else
        for (let z = h.z - h.length / 2 + 0.4; z < h.z + h.length / 2; z += 1.2) {
          B(g, 0, floor, z, h.width, 0.09, 0.12, m.wood);
          for (const sign of [-1, 1])
            B(g, sign * (h.width / 2 - 0.1), floor, z, 0.12, form.freeboard - floor, 0.13, m.wood);
        }
    }
    for (const sign of [-1, 1])
      for (const side of [-1, 1]) {
        const z = sign * form.length * 0.39,
          x = side * form.beam * 0.27;
        C(g, x, form.freeboard, z, 0.065, 0.09, 0.32, m.dark);
        E(g, [x - 0.22, form.freeboard + 0.28, z], [x + 0.22, form.freeboard + 0.28, z], 0.04, m.dark);
        const coil = new THREE.Mesh(new THREE.TorusGeometry(0.25, 0.035, 5, 14), m.rope);
        coil.rotation.x = Math.PI / 2;
        coil.position.set(x, form.freeboard + 0.04, z + 0.38);
        g.add(coil);
      }
    if (form.kind === 'collier') {
      const f = form.freeboard,
        aft = form.length * 0.33;
      B(g, 0, f, aft, form.beam * 0.7, 2.15, 7.2, m.cabin);
      B(g, 0, f + 2.15, aft, form.beam * 0.76, 0.16, 7.5, m.deck);
      B(g, 0, f + 2.31, aft - 0.8, 3.2, 1.85, 2.9, m.wood);
      B(g, 0, f + 4.16, aft - 0.8, 3.6, 0.14, 3.25, m.dark);
      for (const x of [-1, 0, 1]) B(g, x, f + 2.95, aft - 2.28, 0.65, 0.83, 0.035, m.glass);
      for (const sign of [-1, 1]) {
        B(g, sign * 1.62, f + 2.95, aft - 0.8, 0.04, 0.83, 1.55, m.glass);
        for (const z of [aft - 2.7, aft, aft + 2.7]) {
          const port = C(g, sign * form.beam * 0.35, f + 0.9, z, 0.19, 0.19, 0.02, m.dark);
          port.rotation.z = Math.PI / 2;
        }
      }
      const funnelZ = aft - 4.6;
      C(g, 0, f, funnelZ, 0.76, 0.88, 6.9, m.dark, 14);
      C(g, 0, f + 3.2, funnelZ, 0.78, 0.78, 2.5, m.red, 14);
      C(g, 0, f + 6.5, funnelZ, 0.79, 0.79, 0.45, m.dark, 14);
      smoke(g, f + 7, funnelZ, 1, mode, random);
      for (const x of [-1.7, 1.7]) {
        C(g, x, f, funnelZ + 1.7, 0.19, 0.19, 2.5, m.cabin);
        const cowl = new THREE.Mesh(new THREE.TorusGeometry(0.3, 0.19, 6, 8, Math.PI / 2), m.cabin);
        cowl.position.set(x, f + 2.5, funnelZ + 1.7);
        g.add(cowl);
      }
      // Two cargo masts, stays and a slewed derrick over the receiving lighter.
      for (const z of form.masts) {
        C(g, 0, f, z, 0.105, 0.22, 12, m.wood, 10);
        for (const sign of [-1, 1])
          rope(
            g,
            [
              [0, f + 11, z],
              [sign * form.beam * 0.4, f + 0.2, z + 5],
            ],
            m.dark,
            0.018
          );
        rope(
          g,
          [
            [0, f + 11, z],
            [0, f + 0.15, z - 8],
          ],
          m.dark,
          0.018
        );
        C(g, 0, f + 0.2, z - 1.6, 0.35, 0.35, 0.6, m.dark);
      }
      const boat = new THREE.Group();
      boat.position.set(-form.beam * 0.34, f + 2.4, aft + 1);
      boat.scale.set(0.8, 0.45, 1.8);
      const dinghy = new THREE.Mesh(
        new THREE.SphereGeometry(1.2, 10, 6, 0, Math.PI * 2, Math.PI / 2, Math.PI / 2),
        m.wood
      );
      boat.add(dinghy);
      g.add(boat);
      for (const sign of [-1, 1])
        E(
          g,
          [-form.beam * 0.34, f + 2.4, aft + 1 + sign * 2],
          [-form.beam * 0.34, f + 4.2, aft + 1 + sign * 2],
          0.055,
          m.dark
        );
      // Navigation rails and companion ladder, kept modest at district scale.
      for (const sign of [-1, 1]) {
        for (let z = aft - 3.6; z < aft + 3.6; z += 1.1)
          C(g, sign * form.beam * 0.36, f + 2.31, z, 0.025, 0.025, 0.85, m.dark, 5);
        E(
          g,
          [sign * form.beam * 0.36, f + 3.16, aft - 3.6],
          [sign * form.beam * 0.36, f + 3.16, aft + 3.6],
          0.025,
          m.dark
        );
      }
      worker(g, 1, f + 2.31, aft + 1.8, Math.PI, 'stand', m);
    } else if (form.kind === 'tug') {
      const f = form.freeboard;
      B(g, 0, f, 1.6, 3.4, 0.95, 6.1, m.cabin);
      B(g, 0, f + 0.95, 1.6, 3.6, 0.12, 6.4, m.deck);
      B(g, 0, f, -3.3, 2.55, 1.6, 2.2, m.wood);
      B(g, 0, f + 1.6, -3.3, 2.9, 0.13, 2.55, m.dark);
      for (const x of [-0.7, 0.7]) B(g, x, f + 0.86, -4.42, 0.65, 0.6, 0.035, m.glass);
      C(g, 0, f + 0.95, -0.25, 0.43, 0.5, 4.15, m.dark, 12);
      C(g, 0, f + 3, -0.25, 0.46, 0.46, 1.2, m.red, 12);
      C(g, 0, f + 5, -0.25, 0.49, 0.49, 0.15, m.dark, 12);
      smoke(g, f + 5.2, -0.25, 0.55, mode, random);
      for (const sign of [-1, 1]) {
        const x = sign * 1.18;
        rope(
          g,
          [
            [x, f + 1.1, 1.9],
            [x, f + 2.6, 1.9],
            [x, f + 3, 2.25],
            [x, f + 3, 2.65],
          ],
          m.cabin,
          0.16
        );
        for (const z of [-5, -3, -1, 1, 3, 5]) {
          const port = C(g, sign * form.beam * 0.48, f - 0.35, z, 0.095, 0.095, 0.035, m.dark, 10);
          port.rotation.z = Math.PI / 2;
          C(g, sign * form.beam * 0.43, f, z, 0.022, 0.022, 0.8, m.cabin, 5);
        }
        for (const y of [f + 0.48, f + 0.78])
          E(g, [sign * form.beam * 0.43, y, -6], [sign * form.beam * 0.43, y, 5.5], 0.022, m.cabin);
      }
      C(g, 0, f, -6, 0.055, 0.11, 4.7, m.wood);
      E(g, [0, f + 4.4, -6], [0, f + 0.12, -8], 0.017, m.dark);
      C(g, 0, f, 6, 0.12, 0.18, 0.7, m.dark);
      worker(g, -1.55, f, 5.4, Math.PI / 2, 'stand', m);
    } else {
      // No modern engine/cabin: low open lighter with end working decks and sweeps.
      const aft = form.length * 0.4;
      B(g, 0, form.freeboard, aft, 0.1, 0.55, 0.12, m.dark);
      E(g, [0, form.freeboard + 0.55, form.length * 0.48], [1.25, form.freeboard + 0.95, aft - 1.8], 0.05, m.wood);
      if (v.worker !== false) {
        const figure = worker(g, -0.7, form.freeboard + form.sheer * 0.25, aft, -Math.PI / 2, v.workPose ?? 'stand', m);
        E(g, figure.userData.grip, [form.beam * 0.9, -0.2, aft - 2], 0.04, m.wood);
        B(g, form.beam * 0.9, -0.25, aft - 2, 0.17, 0.4, 0.5, m.wood);
      }
      for (const sign of [-1, 1])
        for (const z of [-form.length * 0.3, form.length * 0.3]) {
          const fender = new THREE.Mesh(new THREE.SphereGeometry(0.23, 8, 6), m.rope);
          fender.scale.set(0.75, 1.8, 0.75);
          fender.position.set((sign * form.beam) / 2, 0.2, z);
          g.add(fender);
        }
    }
    g.userData.materials = m;
  }
  // Transfer tableaux: rig, basket, trough and workers move with the collier.
  // The coal-whipping prints supply the handling vocabulary, not a measured rig.
  for (const transfer of spec.transfers) {
    const ship = byId.get(transfer.collier),
      lighter = byId.get(transfer.lighter);
    const g = ship.group,
      m = g.userData.materials,
      f = ship.form.freeboard;
    const dx = lighter.vessel.x - ship.vessel.x,
      dz = lighter.vessel.z - ship.vessel.z;
    const a = g.rotation.y,
      lx = dx * Math.cos(a) - dz * Math.sin(a),
      lz = dx * Math.sin(a) + dz * Math.cos(a);
    const z = transfer.holdZ,
      side = Math.sign(lx),
      edge = (side * ship.form.beam) / 2;
    const manual = transfer.method === 'manual-whip';
    const tip = [manual ? edge + side * 0.5 : lx * 0.8, f + (manual ? 5.8 : 7.5), z];
    if (manual) {
      const stage = f + 2.2;
      B(g, side * 2.3, stage - 0.12, z + 0.5, 3.6, 0.12, 2.2, m.wood);
      for (const x of [0.5, 4.1])
        for (const dz of [-0.5, 1.5]) {
          E(g, [side * x, f, z + dz], [side * x, stage, z + dz], 0.08, m.wood);
        }
      for (const x of [0.5, 4.1]) E(g, [side * x, f, z - 0.6], [side * x, f + 5.8, z - 0.6], 0.11, m.wood);
      E(g, [side * 0.5, f + 5.8, z - 0.6], [tip[0], tip[1], z], 0.12, m.wood);
      // Three separate lanyards run to the raised gang. The fourth man handles
      // the basket at the rail and the receiving man trims the lighter's load.
      for (const x of [1, 2.2, 3.4]) {
        const figure = worker(g, side * x, stage, z + 0.7, 0, 'haul', m);
        rope(g, [[tip[0], tip[1], z], [side * x, f + 5.8, z - 0.6], figure.userData.grip], m.rope, 0.022);
      }
      for (const sign of [-1, 1])
        E(g, [side * (0.5 + sign * 0.18), f, z + 2], [side * (0.5 + sign * 0.18), stage, z + 1], 0.045, m.wood);
      for (let y = 0.3; y < 2.2; y += 0.3)
        E(g, [side * 0.32, f + y, z + 2 - y / 2.2], [side * 0.68, f + y, z + 2 - y / 2.2], 0.03, m.wood);
    } else {
      E(g, [0, f + 0.6, transfer.mastZ], tip, 0.115, m.wood);
      E(g, [0, f + 11, transfer.mastZ], tip, 0.025, m.dark);
      rope(g, [tip, [1, f + 5, transfer.mastZ], [0.65, f + 1.8, transfer.mastZ + 0.72]], m.rope, 0.022);
      worker(g, 0.65, f, transfer.mastZ + 1, 0, 'haul', m);
    }
    const basketY = f + 3;
    E(g, tip, [tip[0], basketY + 0.85, z], 0.023, m.rope);
    if (transfer.method === 'early-grab') {
      // A modest twin-jaw grab study, hung from a winch-operated cargo derrick.
      // The GIHS account supports introduction near 1900, not this exact model.
      for (const sign of [-1, 1]) {
        const profile = [
          [0, 0.8],
          [sign * 0.5, 0.42],
          [sign * 0.72, 0.05],
          [sign * 0.45, -0.25],
          [0, -0.3],
        ];
        const positions = [];
        for (let i = 1; i < profile.length; i++) {
          const [ax, ay] = profile[i - 1],
            [bx, by] = profile[i];
          positions.push(
            ...quad(
              [tip[0] + ax, basketY + ay, z - 0.6],
              [tip[0] + bx, basketY + by, z - 0.6],
              [tip[0] + bx, basketY + by, z + 0.6],
              [tip[0] + ax, basketY + ay, z + 0.6]
            )
          );
        }
        for (const dz of [-0.6, 0.6]) {
          for (let i = 1; i < profile.length - 1; i++)
            positions.push(
              tip[0] + profile[0][0],
              basketY + profile[0][1],
              z + dz,
              tip[0] + profile[i][0],
              basketY + profile[i][1],
              z + dz,
              tip[0] + profile[i + 1][0],
              basketY + profile[i + 1][1],
              z + dz
            );
          E(g, [tip[0], basketY + 1.3, z + dz], [tip[0] + sign * 0.5, basketY + 0.42, z + dz], 0.045, m.dark);
        }
        mesh(g, positions, m.dark, 'Early grab — paired metal scoops');
      }
      E(g, tip, [tip[0], basketY + 1.3, z], 0.025, m.dark);
    } else {
      C(g, tip[0], basketY, z, 0.55, 0.4, 0.7, m.wood, 12);
      C(g, tip[0], basketY + 0.58, z, 0.56, 0.56, 0.1, m.dark, 12);
      for (const sign of [-1, 1])
        E(g, [tip[0] + sign * 0.48, basketY + 0.65, z], [tip[0], basketY + 0.95, z], 0.025, m.rope);
      for (let y = basketY + 0.1; y < basketY + 0.65; y += 0.14) {
        const band = new THREE.Mesh(new THREE.TorusGeometry(0.44 + (0.12 * (y - basketY)) / 0.7, 0.018, 4, 12), m.rope);
        band.rotation.x = Math.PI / 2;
        band.position.set(tip[0], y, z);
        g.add(band);
      }
    }
    // Open trough slopes from the ship's side to the receiving hold, with raised sides.
    const start = [edge, f + 1.2, z],
      end = [lx, lighter.form.freeboard + 0.6, lz];
    const d = new THREE.Vector3(...end).sub(new THREE.Vector3(...start));
    const trough = B(
      g,
      (start[0] + end[0]) / 2,
      (start[1] + end[1]) / 2 - 0.06,
      (start[2] + end[2]) / 2,
      1.05,
      0.12,
      d.length(),
      m.wood
    );
    trough.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), d.clone().normalize());
    for (const sign of [-1, 1])
      E(g, [start[0], start[1] + 0.15, z + sign * 0.53], [end[0], end[1] + 0.15, end[2] + sign * 0.53], 0.065, m.wood);
    worker(g, edge - side * 0.55, f, z + 1.05, (side * Math.PI) / 2, 'shovel', m);
    const receiver = lighter.group,
      lm = receiver.userData.materials;
    worker(receiver, 0, lighter.form.freeboard + 0.45, -2, Math.PI / 2, 'shovel', lm);
    rope(
      g,
      [
        [edge, f + 0.2, z - 3],
        [(edge + lx) / 2, 0.2, lz - 3],
        [lx - side * lighter.form.beam * 0.27, lighter.form.freeboard + 0.2, lz - 3],
      ],
      m.rope,
      0.035
    );
  }
  for (const tow of spec.tows) {
    const a = byId.get(tow.from),
      b = byId.get(tow.to);
    const start = vesselPoint(a.vessel, 0, a.form.length * 0.43);
    const end = vesselPoint(b.vessel, 0, -b.form.length * 0.43);
    const mode = a.vessel.water;
    const y = mode === 'tidal' ? tideLow : waterLevel;
    rope(
      fleet,
      [
        [start[0], y + a.form.freeboard + 0.2, start[1]],
        [(start[0] + end[0]) / 2, y + 0.15, (start[1] + end[1]) / 2],
        [end[0], y + b.form.freeboard + 0.2, end[1]],
      ],
      colour('wood', '#9a8d70', mode),
      0.035
    );
  }
  let triangles = 0;
  fleet.traverse((o) => {
    if (!o.isMesh) return;
    o.castShadow = o.receiveShadow = true;
    triangles += (o.geometry.index?.count ?? o.geometry.attributes.position.count) / 3;
  });
  return {
    vessels: spec.vessels.length,
    ...counts,
    transfers: spec.transfers.length,
    triangles,
    waterMasks: vesselHolds(spec).length,
    placements: spec.vessels.map((v) => ({ id: v.id, kind: spec.forms[v.form].kind, water: v.water, x: v.x, z: v.z })),
    evidenceStatus: spec.status,
  };
}
