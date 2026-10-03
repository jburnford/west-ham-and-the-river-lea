// Mapped open spaces; surfacing, wear and stock placement are interpretations.
import { createRandom } from './lib/prng.js';
export function factoryYards({ THREE, scene, materials: m, data, level, box, cylinder, lite = false }) {
  const yards = data.factoryYards,
    [x0, z0, x1, z1] = yards.bounds,
    w = x1 - x0,
    d = z1 - z0;
  const canvas = document.createElement('canvas');
  canvas.width = canvas.height = lite ? 2048 : 4096;
  const ctx = canvas.getContext('2d'); // Transparent outside mapped open yard space.
  ctx.scale(canvas.width / w, canvas.height / d);
  ctx.translate(-x0, -z0);
  const shape = (polygons) => {
    ctx.beginPath();
    for (const rings of polygons)
      for (const ring of rings) {
        ring.forEach(([x, z], i) => (i ? ctx.lineTo(x, z) : ctx.moveTo(x, z)));
        ctx.closePath();
      }
  };
  const palette = {
    earth: ['#807767', '#746c5e', '#8b806d'],
    cinder: ['#686961', '#727169', '#60645f'],
    stone: ['#979184', '#878779', '#a39a88'],
  };
  const path = (route) => {
    ctx.beginPath();
    route.forEach(([x, z], i) => (i ? ctx.lineTo(x, z) : ctx.moveTo(x, z)));
  };
  for (const site of yards.sites) {
    const random = createRandom(site.id + 9283);
    ctx.save();
    shape(site.polygons);
    ctx.clip('evenodd');
    ctx.fillStyle = palette[site.surface][Math.abs(site.id) % 3];
    ctx.fillRect(...[site.bounds[0], site.bounds[1], site.bounds[2] - site.bounds[0], site.bounds[3] - site.bounds[1]]);
    // Unique, overlapping soft patches across each parcel, never a repeating
    // four-metre tile. Cinder, compacted ground and pale stone dust mix locally.
    for (let i = 0; i < Math.min(650, site.areaM2 / 32); i++) {
      const x = site.bounds[0] + random() * (site.bounds[2] - site.bounds[0]),
        z = site.bounds[1] + random() * (site.bounds[3] - site.bounds[1]);
      const r = 1.5 + random() * 11,
        gradient = ctx.createRadialGradient(x, z, 0, x, z, r);
      const dark = random() < 0.58;
      gradient.addColorStop(0, dark ? 'rgba(38,39,33,.16)' : 'rgba(194,180,151,.17)');
      gradient.addColorStop(1, 'rgba(90,83,69,0)');
      ctx.fillStyle = gradient;
      ctx.beginPath();
      ctx.ellipse(x, z, r, r * (0.3 + random() * 0.55), random() * Math.PI, 0, Math.PI * 2);
      ctx.fill();
    }
    // Dirt and damp collect at range edges. Keep the broad centre usable.
    ctx.lineJoin = 'round';
    ctx.strokeStyle = 'rgba(39,40,34,.18)';
    ctx.lineWidth = 2.1;
    for (const edge of yards.buildingEdges) {
      if (
        !edge.some(
          ([x, z]) =>
            x > site.bounds[0] - 2 && x < site.bounds[2] + 2 && z > site.bounds[1] - 2 && z < site.bounds[3] + 2
        )
      )
        continue;
      path(edge);
      ctx.stroke();
    }
    ctx.lineCap = 'round';
    for (const route of site.wearRoutes) {
      ctx.strokeStyle = 'rgba(179,165,135,.16)';
      ctx.lineWidth = 4.5;
      path(route);
      ctx.stroke();
      ctx.strokeStyle = 'rgba(152,142,119,.27)';
      ctx.lineWidth = 2.7;
      path(route);
      ctx.stroke();
      const [a, b] = route,
        dx = b[0] - a[0],
        dz = b[1] - a[1],
        length = Math.hypot(dx, dz);
      for (const side of [-1, 1]) {
        ctx.strokeStyle = 'rgba(46,45,37,.19)';
        ctx.lineWidth = 0.22;
        path(route.map(([x, z]) => [x - ((side * dz) / length) * 0.72, z + ((side * dx) / length) * 0.72]));
        ctx.stroke();
      }
    }
    // Irregular little damp hollows, painted into the surface rather than
    // another water plane that would respond to the river tide.
    for (let i = 0; i < Math.min(12, site.areaM2 / 1700); i++) {
      const x = site.bounds[0] + random() * (site.bounds[2] - site.bounds[0]),
        z = site.bounds[1] + random() * (site.bounds[3] - site.bounds[1]);
      ctx.fillStyle = 'rgba(48,55,49,.17)';
      ctx.beginPath();
      ctx.ellipse(x, z, 0.8 + random() * 1.5, 0.3 + random() * 0.6, random() * Math.PI, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.restore();
  }
  // OS-mapped open working grids stay on the existing ground surface. Their
  // boundary appearance is interpreted; no roof or apparatus elevation is
  // inferred from the empty cells.
  let workingGrids = 0,
    openWorkingCells = 0,
    workingGridBoundaries = 0;
  for (const grid of yards.workingGrids ?? []) {
    ctx.save();
    shape([[grid.worldOutline]]);
    ctx.clip('evenodd');
    ctx.strokeStyle = grid.lineColour;
    ctx.lineWidth = grid.lineWidth;
    ctx.lineJoin = 'round';
    ctx.lineCap = 'butt';
    for (const divider of grid.dividers) {
      path(divider.points);
      ctx.stroke();
      workingGridBoundaries++;
    }
    workingGrids++;
    openWorkingCells += grid.cells.filter((cell) => cell.open).length;
    ctx.restore();
  }
  ctx.save();
  ctx.strokeStyle = 'rgba(91,84,69,.34)';
  ctx.lineWidth = 2;
  ctx.lineCap = 'round';
  // Ground-level tracks leave a worn strip; connected depot approaches also
  // have a separately modelled, interpreted formation above this yard surface.
  for (const track of yards.tracks) {
    path(track.points);
    ctx.stroke();
  }
  ctx.restore();
  // Let grass intrude into exposed margins with a variable-width feather.
  // Erasing the atlas reveals the actual land material, without extending dirt
  // into roads or water. The builder keeps these brushes clear of built edges.
  ctx.save();
  ctx.globalCompositeOperation = 'destination-out';
  for (const [x, z, radius] of yards.softEdges) {
    const fade = ctx.createRadialGradient(x, z, 0, x, z, radius);
    fade.addColorStop(0, 'rgba(0,0,0,1)');
    fade.addColorStop(0.3, 'rgba(0,0,0,.9)');
    fade.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = fade;
    ctx.beginPath();
    ctx.arc(x, z, radius, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.restore();
  // Fine aggregate has no grid or mirrored repetition. It is baked once into
  // this district-wide map, and filtered by ordinary texture mipmaps at distance.
  ctx.resetTransform();
  const pixels = ctx.getImageData(0, 0, canvas.width, canvas.height);
  let grain = 7743;
  for (let i = 0; i < pixels.data.length; i += 4) {
    grain = (grain * 1664525 + 1013904223) >>> 0;
    const delta = ((grain >>> 24) / 255 - 0.5) * 12;
    pixels.data[i] += delta;
    pixels.data[i + 1] += delta;
    pixels.data[i + 2] += delta;
  }
  ctx.putImageData(pixels, 0, 0);
  const map = new THREE.CanvasTexture(canvas);
  map.colorSpace = THREE.SRGBColorSpace;
  map.anisotropy = 4;
  // Paint the existing land meshes. A second, almost coincident ground mesh
  // caused speckling and could intersect the bank/terrain near the gasworks.
  m.land.userData.yardAtlas = map;
  m.land.userData.yardBounds = new THREE.Vector4(x0, z0, w, d);
  const required = new Set(),
    sampled = new Map();
  const trackRuns = yards.tracks.map((track) => {
    const run = [];
    const point = (i, t = 0) => {
      const a = track.points[i],
        b = track.points[Math.min(i + 1, track.points.length - 1)];
      const height = (values) => (values ? values[i] + ((values[i + 1] ?? values[i]) - values[i]) * t : null);
      return [
        a[0] + (b[0] - a[0]) * t,
        a[1] + (b[1] - a[1]) * t,
        height(track.formationHeights),
        height(track.railTopHeights),
      ];
    };
    for (let i = 1; i < track.points.length; i++) {
      const a = track.points[i - 1],
        b = track.points[i],
        n = Math.ceil(Math.hypot(b[0] - a[0], b[1] - a[1]));
      for (let j = 0; j < n; j++) run.push(point(i - 1, j / n));
    }
    run.push(point(track.points.length - 1));
    return { run, gauge: track.gauge ?? 1.1, sleeperWidth: track.sleeperWidth ?? 1.8 };
  });
  for (const [x, z] of trackRuns.flatMap((track) => track.run)) {
    const ix = Math.floor(x),
      iz = Math.floor(z);
    for (const [dx, dz] of [
      [0, 0],
      [1, 0],
      [0, 1],
      [1, 1],
    ])
      required.add(`${ix + dx},${iz + dz}`);
  }
  for (const site of yards.sites)
    for (const item of site.stock) {
      const x = Math.floor(item.x),
        z = Math.floor(item.z);
      for (const [dx, dz] of [
        [0, 0],
        [1, 0],
        [0, 1],
        [1, 1],
      ])
        required.add(`${x + dx},${z + dz}`);
    }
  const network = data.riverNetwork.positions;
  for (let i = 0; i < network.length; i += 3) {
    const key = `${network[i]},${network[i + 2]}`;
    if (required.has(key)) sampled.set(key, network[i + 1]);
  }
  function stockLevel(x, z) {
    if (data.mainLandscape?.weight(x, z) > 0) return level(x, z);
    const [bx, bz, ex, ez] = data.terrain.bounds;
    if (x >= bx && x <= ex && z >= bz && z <= ez) return level(x, z);
    const ix = Math.floor(x),
      iz = Math.floor(z),
      u = x - ix,
      v = z - iz;
    const at = (dx, dz) => sampled.get(`${ix + dx},${iz + dz}`) ?? -0.1;
    return (at(0, 0) * (1 - u) + at(1, 0) * u) * (1 - v) + (at(0, 1) * (1 - u) + at(1, 1) * u) * v;
  }
  const earthTriangles = yards.tracks.flatMap((track) => track.formationTriangles ?? []);
  const ballastTriangles = [];
  function meshTriangles(triangles, material) {
    if (!triangles.length) return;
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(triangles.flat(2), 3));
    geometry.computeVertexNormals();
    const mesh = new THREE.Mesh(geometry, material);
    mesh.receiveShadow = true;
    scene.add(mesh);
  }
  const formationMaterial = m.ground.clone();
  formationMaterial.side = THREE.DoubleSide;
  meshTriangles(earthTriangles, formationMaterial);
  let trackMetres = 0,
    connectedTrackMetres = 0;
  for (const { run, gauge, sleeperWidth } of trackRuns)
    for (let i = 1; i < run.length; i++) {
      const a = run[i - 1],
        b = run[i],
        dx = b[0] - a[0],
        dz = b[1] - a[1],
        length = Math.hypot(dx, dz);
      if (length < 0.001) continue;
      trackMetres += length;
      const x = (a[0] + b[0]) / 2,
        z = (a[1] + b[1]) / 2,
        y = stockLevel(x, z);
      const connected = a[3] !== null && b[3] !== null;
      const railTop = connected ? (a[3] + b[3]) / 2 : y + 0.12;
      const sleeper = box(
        scene,
        x,
        connected ? railTop - 0.22 : y + 0.01,
        z,
        0.15,
        connected ? 0.15 : 0.045,
        sleeperWidth,
        m.wood
      );
      sleeper.rotation.y = -Math.atan2(dz, dx);
      if (connected) {
        connectedTrackMetres += length;
        const edge = (p, side) => [p[0] - (dz / length) * side * 1.4, p[2] + 0.18, p[1] + (dx / length) * side * 1.4];
        const corners = [edge(a, -1), edge(a, 1), edge(b, 1), edge(b, -1)];
        ballastTriangles.push([corners[0], corners[1], corners[2]], [corners[0], corners[2], corners[3]]);
      }
      for (const side of [-1, 1]) {
        const rise = connected ? b[3] - a[3] : 0,
          depth = connected ? 0.13 : 0.065;
        const rail = box(
          scene,
          x - (((side * dz) / length) * gauge) / 2,
          railTop - depth,
          z + (((side * dx) / length) * gauge) / 2,
          Math.hypot(length, rise) + 0.02,
          depth,
          connected ? 0.09 : 0.045,
          m.iron
        );
        rail.quaternion.setFromUnitVectors(new THREE.Vector3(1, 0, 0), new THREE.Vector3(dx, rise, dz).normalize());
      }
    }
  const trackBallast = m.stone.clone();
  trackBallast.color.set('#69685e');
  trackBallast.side = THREE.DoubleSide;
  meshTriangles(ballastTriangles, trackBallast);
  // Fresh sawn timber reads differently from dark wharf planking. Three shared
  // materials keep the individual boards batchable with restrained variation.
  const lumber = ['#b9a079', '#aa916d', '#c7b28b'].map((color) => {
    const material = m.wood.clone();
    material.color.set(color);
    material.bumpScale = 0.006;
    material.userData.surface = 'sawnTimber';
    return material;
  });
  let stocks = 0,
    timberStacks = 0;
  for (const site of yards.sites)
    for (const item of site.stock) {
      const group = new THREE.Group();
      group.position.set(item.x, stockLevel(item.x, item.z) + 0.015, item.z);
      group.rotation.y = item.angle;
      scene.add(group);
      stocks++;
      if (item.kind === 'deals' || item.kind === 'boards') {
        timberStacks++;
        const thickness = item.kind === 'deals' ? 0.075 : 0.038,
          boardWidth = item.kind === 'deals' ? 0.24 : 0.18;
        const columns = Math.floor(item.width / (boardWidth + 0.022)),
          span = columns * (boardWidth + 0.022) - 0.022;
        const supports = [-item.length * 0.36, 0, item.length * 0.36];
        for (const x of supports) box(group, x, 0, 0, 0.2, 0.22, span + 0.12, m.wood);
        const material = lumber[item.shade];
        for (let layer = 0; layer < item.layers; layer++) {
          const base = 0.22 + layer * (thickness + 0.028);
          for (let col = 0; col < columns; col++) {
            const offset = 0.055 * Math.sin(layer * 2.3 + col * 4.7 + item.x);
            const length = item.length - 0.07 * (1 + Math.sin(layer * 1.7 + col * 2.1));
            box(
              group,
              offset,
              base,
              (col - (columns - 1) / 2) * (boardWidth + 0.022),
              length,
              thickness,
              boardWidth,
              material
            );
          }
          if (layer < item.layers - 1)
            for (const x of supports)
              box(group, x, base + thickness, 0, 0.055, 0.028, span, lumber[(item.shade + 1) % 3]);
        }
      } else if (item.kind === 'timber') {
        for (let layer = 0; layer < 4; layer++)
          for (let row = 0; row < 4; row++)
            box(group, 0, 0.15 + layer * 0.18, (row - 1.5) * 0.32, 3.5 - layer * 0.1, 0.14, 0.27, m.wood);
        for (const x of [-1.2, 1.2]) box(group, x, 0, 0, 0.25, 0.15, 1.6, m.dark);
      } else if (item.kind === 'bales') {
        // Goad marks temporary jute stacks in this yard; stack positions and
        // wrapped bale dimensions are interpretive, not mapped individual stock.
        for (const [x, z, y] of [
          [-0.55, -0.4, 0],
          [0.55, -0.4, 0],
          [-0.55, 0.4, 0],
          [0.55, 0.4, 0],
          [0, 0, 0.7],
        ]) {
          box(group, x, y, z, 0.95, 0.66, 0.72, lumber[1]);
          for (const dx of [-0.28, 0.28]) {
            box(group, x + dx, y + 0.66, z, 0.035, 0.018, 0.74, m.dark);
            for (const side of [-1, 1]) box(group, x + dx, y, z + side * 0.365, 0.035, 0.67, 0.018, m.dark);
          }
        }
      } else if (item.kind === 'barrels') {
        for (const [x, z] of [
          [-0.6, -0.5],
          [0.5, -0.4],
          [-0.3, 0.55],
        ]) {
          cylinder(group, x, 0, z, 0.34, 0.3, 1.05, m.wood, 12);
          for (const y of [0.14, 0.77]) cylinder(group, x, y, z, 0.351, 0.351, 0.055, m.iron, 12);
        }
      } else if (item.kind === 'iron') {
        for (let i = 0; i < 5; i++) {
          const pipe = new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.18, 2.8, 10), m.iron);
          pipe.rotation.z = Math.PI / 2;
          pipe.position.set(0, 0.2 + (i > 2 ? 0.34 : 0), ((i % 3) - 1) * 0.4);
          group.add(pipe);
        }
      } else if (item.kind === 'coal' || item.kind === 'stone') {
        const pile = new THREE.Mesh(new THREE.IcosahedronGeometry(1, 1), item.kind === 'coal' ? m.coal : m.stone);
        pile.scale.set(1.5, 0.65, 1.05);
        pile.position.y = 0.25;
        pile.rotation.y = 0.7;
        group.add(pile);
        for (const x of [-1.6, 1.6]) box(group, x, 0, 0, 0.1, 0.7, 2.4, m.wood);
        box(group, 0, 0, 1.2, 3.3, 0.7, 0.1, m.wood);
      } else {
        for (const [x, z, size] of [
          [-0.65, -0.4, 0.9],
          [0.6, 0, 1],
          [-0.5, 0.7, 0.7],
        ]) {
          box(group, x, 0, z, size, size * 0.8, size, m.wood);
          for (const dx of [-0.34, 0.34])
            box(group, x + dx * size, 0, z + size / 2 + 0.015, 0.06, size * 0.8, 0.03, m.dark);
        }
      }
    }
  return {
    ...yards.counts,
    stockGroups: stocks,
    timberStacks,
    trackMetres: Math.round(trackMetres),
    connectedTrackMetres: Math.round(connectedTrackMetres),
    formationTriangles: earthTriangles.length,
    atlasSize: canvas.width,
    workingGrids,
    openWorkingCells,
    workingGridBoundaries,
  };
}
