// Approximate mapped streets and rail corridors; surfaces/levels are interpretations.
import { highStreetSurfaceHeight } from './sewer-levels.js';
import { greatEastern } from './great-eastern.js';
import { roadProfileHeight } from './road-levels.js';
import { createRandom } from './lib/prng.js';
import { bridgeClearance, bridgeForms, deckEndLevel, roadBridges } from './road-bridges.js';
import {
  railwayWorks,
  bridgeIntervals,
  replacedCrossings,
  railwayBridges,
  railwayWalls,
} from './railway-bridges.js';
export function infrastructure({ THREE, scene, materials: m, data, box, level }) {
  const infra = data.infrastructure,
    [x0, z0, x1, z1] = data.terrain.bounds;
  // Original code-generated paving: no modern blacktop or painted road markings.
  // Surface assignment is provisional, not a claim about street adoption records.
  function roadMaterial(kind) {
    const canvas = document.createElement('canvas');
    canvas.width = canvas.height = 512;
    const ctx = canvas.getContext('2d');
    const rnd = createRandom(kind === 'setts' ? 479 : kind === 'macadam' ? 871 : 316);
    ctx.fillStyle = kind === 'setts' ? '#777970' : kind === 'macadam' ? '#aaa292' : '#938775';
    ctx.fillRect(0, 0, 512, 512);
    if (kind === 'setts')
      for (let row = 0; row < 16; row++)
        for (let col = -1; col < 9; col++) {
          const value = Math.floor(132 + rnd() * 34);
          ctx.fillStyle = `rgb(${value},${value + 1},${value - 3})`;
          ctx.fillRect(col * 64 + (row % 2) * 32 + 2, row * 32 + 2, 60, 28);
        }
    for (let i = 0; i < 40000; i++) {
      const value = kind === 'cinder' ? 45 + rnd() * 120 : 80 + rnd() * 125;
      ctx.fillStyle = `rgba(${value},${value},${value - 8},${0.05 + rnd() * 0.2})`;
      const size = kind === 'cinder' ? 1 + rnd() * 3 : 1 + rnd();
      ctx.fillRect(rnd() * 512, rnd() * 512, size, size);
    }
    const texture = new THREE.CanvasTexture(canvas);
    texture.colorSpace = THREE.SRGBColorSpace;
    texture.wrapS = texture.wrapT = THREE.RepeatWrapping;
    texture.repeat.set(0.5, 0.5);
    texture.anisotropy = 8;
    const bump = texture.clone();
    bump.colorSpace = THREE.NoColorSpace;
    bump.needsUpdate = true;
    const material = m.stone.clone();
    material.color.set('#b6af9f');
    material.map = texture;
    material.bumpMap = bump;
    material.bumpScale = kind === 'setts' ? 0.018 : kind === 'cinder' ? 0.024 : 0.009;
    material.roughness = 0.96;
    return material;
  }
  const roads = Object.fromEntries(['macadam', 'setts', 'cinder'].map((kind) => [kind, roadMaterial(kind)]));
  const pavement = m.stone.clone();
  pavement.color.set('#aaa392');
  pavement.roughness = 0.96;
  const path = m.ground.clone();
  path.color.set('#9b9078');
  const ballast = m.stone.clone();
  ballast.color.set('#605e55');
  const earth = m.ground.clone();
  earth.color.set('#777463');
  const profiles = infra.roads.map((r) => r.elevationProfile).filter(Boolean);
  const deckEnds = deckEndLevel(infra.roadBridges),
    deckFootway = bridgeForms.defaults.deckFootway;
  const profileHeight = (x, z) => {
    for (const p of profiles) {
      const y = roadProfileHeight(x, z, p, data.elevation?.meta.epoch);
      if (y !== null) return y;
    }
    return null;
  };
  const ground = (x, z) => {
    const measured = profileHeight(x, z);
    if (measured !== null) return measured - 0.065;
    let h =
      data.mainLandscape?.weight(x, z) > 0
        ? level(x, z)
        : x >= x0 && x <= x1 && z >= z0 && z <= z1
          ? Math.max(0.12, level(x, z))
          : 0.12;
    const highStreet = highStreetSurfaceHeight(x, z, infra.sewerHighStreet);
    if (!data.mainLandscape || highStreet > 0.1850001) h = Math.max(h, highStreet - 0.065);
    // Near a bridge the deck level wins: level across the road at each deck end, falling along it
    // (deckEndLevel in road-bridges.js; the rule and its estimates are in the bridge register).
    return deckEnds(x, z, h);
  };
  const clearance = bridgeClearance(infra.roadBridges);
  // The street footway carried onto each deck footway (deckEndFootways from build_infrastructure.py):
  // each vertex carries its rise weight, 0 where it meets the street footway (0.095 m above
  // ground()) and 1 at the deck end (the deck footway top). Its edges get kerb faces down to just
  // below the road, then earth fill to the drawn ground where the approach is raised.
  function deckEndFootways() {
    const rise = deckFootway.base + deckFootway.thickness - (0.095 - 0.065),
      top = [],
      kerbs = [],
      fill = [];
    for (const record of infra.deckEndFootways ?? []) {
      const edges = new Map();
      for (const tri of record.triangles) {
        const points = tri.map(([x, z, w]) => [x, ground(x, z) + 0.095 + w * rise, z]);
        const [a, b, c] = points;
        if ((b[0] - a[0]) * (c[2] - a[2]) - (b[2] - a[2]) * (c[0] - a[0]) > 0) points.reverse();
        top.push(...points.flat());
        for (let j = 0; j < 3; j++) {
          const p = points[j],
            q = points[(j + 1) % 3],
            key = [p, q]
              .map((v) => `${v[0].toFixed(3)},${v[2].toFixed(3)}`)
              .sort()
              .join('|');
          if (edges.has(key)) edges.set(key, null);
          else edges.set(key, { p, q, inner: points[(j + 2) % 3] });
        }
      }
      for (const edge of edges.values()) {
        if (!edge) continue;
        const { p, q, inner } = edge,
          low = (v) => [v[0], ground(v[0], v[2]) + 0.045, v[2]];
        // Outward: away from the triangle's third vertex.
        const ex = q[0] - p[0],
          ez = q[2] - p[2],
          side = Math.sign(ez * (inner[0] - p[0]) - ex * (inner[2] - p[2])) || 1;
        const quad = (a, b, c, d, list) => {
          // Winding chosen so the face looks away from the footway.
          if (side < 0) list.push(...a, ...b, ...c, ...a, ...c, ...d);
          else list.push(...a, ...c, ...b, ...a, ...d, ...c);
        };
        quad(p, q, low(q), low(p), kerbs);
        if (Math.max(p[1], q[1]) > 0.4)
          for (const [a, b] of clearance.outside(low(p), low(q))) {
            const ground0 = [a[0], Math.min(a[1], level(a[0], a[2])), a[2]],
              ground1 = [b[0], Math.min(b[1], level(b[0], b[2])), b[2]];
            quad(a, b, ground1, ground0, fill);
          }
      }
    }
    for (const [positions, material, name] of [
      [top, pavement, 'road-deck-end-footway'],
      [kerbs, pavement, 'road-deck-end-kerb'],
      [fill, earth, 'road-deck-end-fill'],
    ]) {
      if (!positions.length) continue;
      const geometry = new THREE.BufferGeometry();
      geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
      const uv = [];
      for (let i = 0; i < positions.length; i += 3) uv.push(positions[i], positions[i + 2] + positions[i + 1]);
      geometry.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
      geometry.computeVertexNormals();
      const mesh = new THREE.Mesh(geometry, material);
      mesh.name = name;
      scene.add(mesh);
    }
  }
  function surface(triangles, material, offset = 0, hasHeight = false, name = '') {
    const vertices = [],
      supports = [];
    for (const tri of triangles) {
      const points = tri.map((p) => (hasHeight ? p : [p[0], ground(...p) + offset, p[1]]));
      // Consistent upward winding for Shapely's x/z triangles.
      const [a, b, c] = points;
      if ((b[0] - a[0]) * (c[2] - a[2]) - (b[2] - a[2]) * (c[0] - a[0]) > 0) points.reverse();
      vertices.push(...points.flat());
      if (!hasHeight && points.some((p) => p[1] > 0.4)) {
        // Fill raised bridge approaches down to the ground instead of leaving
        // the road as a floating sheet. Internal faces disappear inside the fill.
        // The fill stops at the bridge abutment faces: none between them, under a span.
        for (let j = 0; j < 3; j++)
          for (const [a, b] of clearance.outside(points[j], points[(j + 1) % 3])) {
            // The fill reaches the drawn ground, which the landscape pass can place below 0.1 m.
            const low = (p) => [p[0], level(p[0], p[2]), p[2]];
            supports.push(...a, ...low(a), ...b, ...b, ...low(a), ...low(b));
          }
      }
    }
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
    const uv = [];
    for (let i = 0; i < vertices.length; i += 3) uv.push(vertices[i], vertices[i + 2]);
    geometry.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
    geometry.computeVertexNormals();
    const mesh = new THREE.Mesh(geometry, material);
    mesh.name = name;
    scene.add(mesh);
    if (supports.length) {
      const fill = new THREE.BufferGeometry();
      fill.setAttribute('position', new THREE.Float32BufferAttribute(supports, 3));
      const uv = [];
      for (let i = 0; i < supports.length; i += 3) uv.push(supports[i], supports[i + 1]);
      fill.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
      fill.computeVertexNormals();
      scene.add(new THREE.Mesh(fill, earth));
    }
  }
  for (const [kind, triangles] of Object.entries(infra.roadSurfaces)) surface(triangles, roads[kind], 0.065);
  surface(infra.shoulderTriangles, pavement, 0.095);
  surface(infra.pathTriangles, path, 0.05);
  function segment(a, b) {
    const length = Math.hypot(b[0] - a[0], b[1] - a[1]),
      g = new THREE.Group();
    g.position.set((a[0] + b[0]) / 2, 0, (a[1] + b[1]) / 2);
    g.rotation.y = -Math.atan2(b[1] - a[1], b[0] - a[0]);
    scene.add(g);
    return { g, length };
  }
  // The road over each bridge: deck setts and footways, as before. Other modules (the tram rails)
  // read this surface. Arches, abutments, parapets and railings come from road-bridges.js.
  for (const bridge of infra.roadBridges)
    for (let i = 1; i < bridge.route.length; i++) {
      const { g, length } = segment(bridge.route[i - 1], bridge.route[i]);
      // A flush deck (carriagewayWidth recorded) carries the street as it is: setts between the street
      // footways, which stand 0.03 m above the road as they do off the deck.
      const carriageway = bridge.carriagewayWidth ?? bridge.width;
      if (bridge.surface) box(g, 0, bridge.height, 0, length, 0.02, carriageway, roads[bridge.surface]);
      if (carriageway < bridge.width)
        for (const sign of [-1, 1])
          box(
            g,
            0,
            bridge.height,
            (sign * (bridge.width + carriageway)) / 4,
            length,
            0.03,
            (bridge.width - carriageway) / 2,
            pavement
          );
      if (bridge.style && bridge.width - 2 * deckFootway.inset - deckFootway.width >= deckFootway.minCarriageway)
        for (const sign of [-1, 1])
          box(
            g,
            0,
            bridge.height + deckFootway.base,
            sign * (bridge.width / 2 - deckFootway.inset),
            length,
            deckFootway.thickness,
            deckFootway.width,
            pavement
          );
    }
  deckEndFootways();
  const bridgeStructures = roadBridges({
    THREE,
    scene,
    materials: m,
    bridges: infra.roadBridges,
    level,
    waterLevel: data.riverNetwork.waterLevel,
  });
  // The main landscape's railway works keep embankment off drawn water and building footprints,
  // close raised line ends and add brick abutment, wing and retaining faces (railway-bridges.js).
  const railworks = {};
  for (const railway of infra.railways) {
    const works = railwayWorks(railway, data.mainLandscape),
      embankmentName = `railway-embankment:${railway.name}`;
    railworks[railway.name] = { removed: works.removed, added: works.added, wallFaces: works.walls.length };
    railwayWalls({ THREE, scene, materials: m, walls: works.walls, name: `railway-wall:${railway.name}` });
    if (railway.detailedMainline || railway.detailedRailway) {
      const detail = greatEastern({
        THREE,
        scene,
        m,
        railway: {
          ...railway,
          embankment: works.embankment,
          bridges: bridgeIntervals(railway),
        },
        box,
        surface: (triangles, ...rest) =>
          surface(triangles, ...rest, ...(triangles === works.embankment ? [embankmentName] : [])),
        ballast,
      });
      if (railway.detailedMainline) scene.userData.greatEastern = detail;
      else (scene.userData.railConnections ||= []).push(detail);
      continue;
    }
    surface(works.embankment, earth, 0, true, embankmentName);
    const h = railway.formationHeight,
      replaced = replacedCrossings(railway),
      // Formation level stations [x, z, y, chainage] from the OS level register (build_infrastructure.py);
      // a railway without them keeps one level along its route.
      stations = railway.levelStations || railway.route.map(([x, z]) => [x, z, h]);
    for (let i = 1; i < stations.length; i++) {
      const [ax, az, ay] = stations[i - 1],
        [bx, bz, by] = stations[i],
        { g, length } = segment([ax, az], [bx, bz]);
      if (length < 0.01) continue;
      // Each piece sits on its own grade: the group at the mean formation level, pitched along it.
      const run = Math.hypot(length, by - ay);
      g.position.y = (ay + by) / 2;
      g.rotation.z = Math.atan2(by - ay, length);
      box(g, 0, 0, 0, run, 0.24, 8.6, ballast);
      for (const track of [-1.8, 1.8]) {
        for (const rail of [-0.718, 0.718]) box(g, 0, 0.33, track + rail, run, 0.13, 0.09, m.iron);
        for (let x = -run / 2; x < run / 2; x += 2.5) box(g, x, 0.24, track, 0.22, 0.18, 2.4, m.wood);
      }
    }
    for (const [index, crossing] of railway.crossings.entries()) {
      // A crossing with a register bridge is drawn by railway-bridges.js.
      if (replaced.has(index)) continue;
      // Deck at the formation level of the crossing (crossingDetails, from the level register).
      const hc = railway.crossingDetails?.[index]?.formation ?? h;
      for (let i = 1; i < crossing.length; i++) {
        const { g, length } = segment(crossing[i - 1], crossing[i]);
        box(g, 0, hc - 0.5, 0, length, 0.5, 8.6, m.iron);
        for (const sign of [-1, 1]) box(g, 0, hc - 0.5, sign * 4.15, length, 1.15, 0.22, m.iron);
      }
      // Abutments at the gap edges keep water/road space clear beneath the span; they stand on the
      // drawn ground (or 0.05 m, whichever is lower) up to the deck.
      for (const end of [0, crossing.length - 1]) {
        const a = crossing[end],
          b = crossing[end === 0 ? 1 : end - 1],
          { g } = segment(a, b),
          foot = Math.min(0.05, level(a[0], a[1]) - 0.3);
        const q = new THREE.Group();
        q.position.set(a[0], 0, a[1]);
        q.rotation.y = g.rotation.y;
        scene.add(q);
        if (hc - 0.55 > foot) box(q, 0, foot, 0, 1.3, hc - 0.55 - foot, 9, m.brick);
      }
    }
  }
  const railBridges = railwayBridges({ THREE, scene, materials: m, railways: infra.railways, level, box, ballast });
  return {
    roadRoutes: infra.roads.length,
    roadBridges: infra.roadBridges.length,
    namedBridges: infra.roadBridges.map((b) => b.id || b.name),
    bridgeStructures: {
      meshes: bridgeStructures.meshes,
      triangles: bridgeStructures.triangles,
      forms: bridgeStructures.bridges.map((b) => `${b.id}: ${b.form}`),
    },
    raisedRailways: infra.railways.length,
    railFormationHeights: Object.fromEntries(infra.railways.map((r) => [r.name, r.formationHeight])),
    railwayWorks: railworks,
    railwayBridges: railBridges.bridges.map((b) => `${b.id}: ${b.form}, ${b.girders} girders, ${b.piers} pier`),
  };
}
