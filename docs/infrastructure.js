// Approximate mapped streets and rail corridors; surfaces/levels are interpretations.
import { highStreetSurfaceHeight } from './sewer-levels.js';
import { greatEastern } from './great-eastern.js';
import { roadProfileHeight } from './road-levels.js';
import { createRandom } from './lib/prng.js';
import { bridgeClearance, roadBridges } from './road-bridges.js';
import {
  railwayWorks,
  addedBridgeIntervals,
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
    for (const bridge of infra.roadBridges)
      for (let i = 1; i < bridge.route.length; i++) {
        const a = bridge.route[i - 1],
          b = bridge.route[i],
          dx = b[0] - a[0],
          dz = b[1] - a[1];
        const t = Math.max(0, Math.min(1, ((x - a[0]) * dx + (z - a[1]) * dz) / (dx * dx + dz * dz)));
        const distance = Math.hypot(x - a[0] - t * dx, z - a[1] - t * dz);
        h = Math.max(h, bridge.height - 0.065 - distance * 0.12);
      }
    return h;
  };
  const clearance = bridgeClearance(infra.roadBridges);
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
      if (bridge.surface) box(g, 0, bridge.height, 0, length, 0.02, bridge.width, roads[bridge.surface]);
      if (bridge.style)
        for (const sign of [-1, 1])
          box(g, 0, bridge.height + 0.025, sign * (bridge.width / 2 - 0.9), length, 0.12, 1.15, pavement);
    }
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
          bridges: [...railway.bridges, ...addedBridgeIntervals(railway)],
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
      replaced = replacedCrossings(railway);
    for (let i = 1; i < railway.route.length; i++) {
      const { g, length } = segment(railway.route[i - 1], railway.route[i]);
      box(g, 0, h, 0, length, 0.24, 8.6, ballast);
      for (const track of [-1.8, 1.8]) {
        for (const rail of [-0.718, 0.718]) box(g, 0, h + 0.33, track + rail, length, 0.13, 0.09, m.iron);
        for (let x = -length / 2; x < length / 2; x += 2.5) box(g, x, h + 0.24, track, 0.22, 0.18, 2.4, m.wood);
      }
    }
    for (const [index, crossing] of railway.crossings.entries()) {
      // A crossing with a register bridge is drawn by railway-bridges.js.
      if (replaced.has(index)) continue;
      for (let i = 1; i < crossing.length; i++) {
        const { g, length } = segment(crossing[i - 1], crossing[i]);
        box(g, 0, h - 0.5, 0, length, 0.5, 8.6, m.iron);
        for (const sign of [-1, 1]) box(g, 0, h - 0.5, sign * 4.15, length, 1.15, 0.22, m.iron);
      }
      // Abutments at the gap edges keep water/road space clear beneath the span.
      for (const end of [0, crossing.length - 1]) {
        const a = crossing[end],
          b = crossing[end === 0 ? 1 : end - 1],
          { g } = segment(a, b);
        const q = new THREE.Group();
        q.position.set(a[0], 0, a[1]);
        q.rotation.y = g.rotation.y;
        scene.add(q);
        box(q, 0, 0.05, 0, 1.3, h - 0.55, 9, m.brick);
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
