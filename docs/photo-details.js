// Original geometry informed by the local photo references. See PHOTO_LAYERS.md.
// Dimensions and placement remain study assumptions; no photo is used as a texture.
export function photoDetails({ THREE, scene, materials: m, box, cylinder, beam, random }) {
  const brickLight = m.brick.clone();
  brickLight.color.set('#b2ab96');
  const red = m.brick.clone();
  red.color.set('#8d6f58');
  const trim = m.stone.clone();
  trim.color.set('#99978b');
  const green = m.iron.clone();
  green.color.set('#62776d');

  function archShape(w, h) {
    const s = new THREE.Shape(),
      r = w / 2;
    s.moveTo(-r, 0);
    s.lineTo(r, 0);
    s.lineTo(r, h - r);
    s.absarc(0, h - r, r, 0, Math.PI, false);
    s.lineTo(-r, 0);
    return s;
  }
  function arch(parent, x, y, z, w, h, rotation = 0, frame = trim) {
    const g = new THREE.Group();
    g.position.set(x, y, z);
    g.rotation.y = rotation;
    parent.add(g);
    const outer = archShape(w + 0.5, h + 0.25),
      inner = archShape(w, h);
    outer.holes.push(new THREE.Path(inner.getPoints(16)));
    g.add(
      new THREE.Mesh(new THREE.ExtrudeGeometry(outer, { depth: 0.22, bevelEnabled: false, curveSegments: 8 }), frame)
    );
    const glass = new THREE.Mesh(new THREE.ShapeGeometry(inner, 12), m.window);
    glass.position.z = 0.02;
    g.add(glass);
    box(g, 0, 0, 0.05, 0.09, h, 0.06, trim);
    for (let v = 0.9; v < h - 0.4; v += 1.1) box(g, 0, v, 0.05, w, 0.06, 0.06, trim);
    box(g, 0, -0.14, 0.08, w + 0.6, 0.2, 0.4, trim);
    return g;
  }
  function curveBeam(parent, points, r, material) {
    const curve = new THREE.CatmullRomCurve3(points.map((p) => new THREE.Vector3(...p)));
    parent.add(new THREE.Mesh(new THREE.TubeGeometry(curve, 32, r, 5, false), material));
  }
  function roofLoft(parent, levels, material = m.roof) {
    const vertices = [];
    for (let i = 1; i < levels.length; i++) {
      const [y0, w0, d0] = levels[i - 1],
        [y1, w1, d1] = levels[i];
      const lower = [
        [-w0 / 2, y0, -d0 / 2],
        [w0 / 2, y0, -d0 / 2],
        [w0 / 2, y0, d0 / 2],
        [-w0 / 2, y0, d0 / 2],
      ];
      const upper = [
        [-w1 / 2, y1, -d1 / 2],
        [w1 / 2, y1, -d1 / 2],
        [w1 / 2, y1, d1 / 2],
        [-w1 / 2, y1, d1 / 2],
      ];
      for (let j = 0; j < 4; j++) {
        const k = (j + 1) % 4;
        for (const v of [lower[j], upper[j], upper[k], lower[j], upper[k], lower[k]]) vertices.push(...v);
      }
    }
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
    geometry.computeVertexNormals();
    parent.add(new THREE.Mesh(geometry, material));
  }
  function finial(parent, x, y, z, h = 3) {
    cylinder(parent, x, y, z, 0.05, 0.09, h, m.iron, 6);
    cylinder(parent, x, y + h * 0.65, z, 0.22, 0.22, 0.35, trim, 8);
    beam(parent, [x - 0.5, y + h * 0.82, z], [x + 0.5, y + h * 0.82, z], 0.055, m.iron);
  }
  function station(plan) {
    const g = new THREE.Group();
    g.name = 'Abbey Mills pumping station';
    g.position.set(plan.centre[0], plan.landscapeLift ?? 0, plan.centre[1]);
    const theta = (plan.angleDegrees * Math.PI) / 180;
    g.rotation.y = -theta;
    scene.add(g);
    const L = plan.mainLength,
      D = plan.crossLength,
      mainDepth = plan.mainDepth,
      crossWidth = plan.crossWidth,
      offset = plan.mainOffsetZ;
    const brickLight = m.brick.clone();
    brickLight.color.set('#b9ac82');
    const red = m.brick.clone();
    red.color.set('#a16c51');
    const trim = m.stone.clone();
    trim.color.set('#b4af9c');
    // Author's supplied Mary Evans 1868 engraving: original geometry only.
    // Relative silhouettes guide these estimates; this is not a measured elevation.
    function stationArch(parent, x, y, z, w, h, rotation = 0) {
      const a = arch(parent, x, y, z, w, h, rotation, red),
        r = w / 2 + 0.15;
      for (let i = 0; i < 11; i++) {
        const angle = ((i + 0.5) * Math.PI) / 11;
        const block = box(
          a,
          Math.cos(angle) * r,
          h - w / 2 + Math.sin(angle) * r - 0.13,
          0.25,
          0.25,
          0.3,
          0.16,
          i % 2 ? red : trim
        );
        block.rotation.z = angle - Math.PI / 2;
      }
      return a;
    }
    function octagonalRoof(parent, x, z, profile) {
      for (let i = 1; i < profile.length; i++) {
        const [y0, r0] = profile[i - 1],
          [y1, r1] = profile[i];
        cylinder(parent, x, y0, z, r1, r0, y1 - y0, m.roof, 8);
      }
    }
    // The mapped outline includes lower boiler wings behind the ornate cross.
    for (const wing of plan.boilerWings) {
      const boiler = new THREE.Group();
      boiler.position.set(wing.x, 0, wing.z);
      g.add(boiler);
      box(boiler, 0, 0, 0, wing.width, wing.height, wing.depth, brickLight);
      box(boiler, 0, 0.25, 0, wing.width + 0.4, 0.3, wing.depth + 0.4, trim);
      box(boiler, 0, wing.height - 0.45, 0, wing.width + 0.5, 0.3, wing.depth + 0.5, trim);
      roofLoft(boiler, [
        [wing.height, wing.width + 0.7, wing.depth + 0.7],
        [wing.height + wing.roofRise, wing.width + 0.7, 0.12],
      ]);
      for (const sign of [-1, 1])
        for (let x = -wing.width / 2 + 3; x < wing.width / 2 - 1; x += 4.6)
          stationArch(boiler, x, 1.2, sign * (wing.depth / 2 + 0.02), 2.1, 4.6, sign === 1 ? 0 : Math.PI);
    }
    for (const [w, d, zShift] of [
      [L, mainDepth, offset],
      [crossWidth, D, 0],
    ]) {
      const arm = new THREE.Group();
      arm.position.z = zShift;
      g.add(arm);
      box(arm, 0, 0, 0, w, 13, d, brickLight);
      for (const y of [0.35, 6.4, 12.7]) {
        box(arm, 0, y, 0, w + 0.5, 0.3, d + 0.5, trim);
      }
      roofLoft(arm, [
        [13, w + 1, d + 1],
        [18, w - 4, d - 5],
        [20, w - 12, d - 12],
      ]);
      box(arm, 0, 19.9, 0, w - 12, 0.15, d - 12, m.roof);
      for (const sign of [-1, 1]) {
        for (let x = -w / 2 + 4; x < w / 2 - 2; x += 5.6) {
          if (w === crossWidth || Math.abs(x) < crossWidth / 2 + 1) continue;
          for (const [y, h] of [
            [1.2, 4.8],
            [8, 3.5],
          ])
            stationArch(arm, x, y, sign * (d / 2 + 0.02), 2.5, h, sign === 1 ? 0 : Math.PI);
        }
        for (let z = -d / 2 + 4; z < d / 2 - 2; z += 5.6) {
          if (d === mainDepth || Math.abs(z - offset) < mainDepth / 2 + 1) continue;
          for (const [y, h] of [
            [1.2, 4.8],
            [8, 3.5],
          ])
            stationArch(arm, sign * (w / 2 + 0.02), y, z, 2.5, h, sign === 1 ? Math.PI / 2 : -Math.PI / 2);
        }
      }
    }
    // Five-bay arm ends: paired storeys, projecting piers and central porch.
    for (const [x, z, angle, width] of [
      [0, D / 2, 0, crossWidth],
      [L / 2, offset, Math.PI / 2, mainDepth],
      [0, -D / 2, Math.PI, crossWidth],
      [-L / 2, offset, -Math.PI / 2, mainDepth],
    ]) {
      const front = new THREE.Group();
      front.position.set(x, 0, z);
      front.rotation.y = angle;
      front.scale.x = width / 20;
      g.add(front);
      for (const bx of [-7.2, -3.6, 0, 3.6, 7.2]) {
        stationArch(front, bx, 1.15, 0.04, 2.45, 4.7);
        const window = stationArch(front, bx, 7.8, 0.04, 2.45, bx === 0 ? 4.0 : 3.65);
        // Slender internal columns give the upper openings more depth.
        for (const dx of [-0.47, 0.47]) cylinder(window, dx, 0.15, 0.18, 0.055, 0.055, 2.75, trim, 6);
      }
      for (const bx of [-9, -5.4, -1.8, 1.8, 5.4, 9]) {
        box(front, bx, 0.4, 0.16, 0.4, 12.1, 0.38, trim);
        box(front, bx, 6.2, 0.25, 0.62, 0.4, 0.55, trim);
      }
      const porch = new THREE.Group();
      porch.position.z = 0.7;
      front.add(porch);
      for (const bx of [-1.7, 1.7]) {
        box(porch, bx, 0.4, 0, 0.55, 4.1, 1.4, brickLight);
        box(porch, bx, 4.35, 0.05, 0.8, 0.35, 1.5, trim);
      }
      stationArch(porch, 0, 0.4, 0.78, 2.8, 4.65);
      roofLoft(
        porch,
        [
          [5.15, 4.3, 2],
          [6.25, 0.06, 2],
        ],
        trim
      );
      for (let bx = -9.5; bx < 10; bx += 1.3) box(front, bx, 12, 0.1, 0.45, 0.65, 0.6, trim);
    }
    // Dormers project from the steep lower roof slopes.
    for (const x of [-L / 2 + 4.5, L / 2 - 4.5])
      for (const sign of [-1, 1]) {
        const dormer = new THREE.Group();
        dormer.position.set(x, 14, offset + sign * (mainDepth / 2 - 1));
        dormer.rotation.y = sign === 1 ? 0 : Math.PI;
        g.add(dormer);
        box(dormer, 0, 0, 0, 3.5, 3, 2.5, trim);
        arch(dormer, 0, 0.3, 1.28, 2, 2.5, 0, trim);
        const cap = new THREE.Mesh(new THREE.ConeGeometry(2.5, 1.6, 4), m.roof);
        cap.rotation.y = Math.PI / 4;
        cap.position.y = 3.7;
        dormer.add(cap);
        finial(dormer, 0, 4.4, 0, 1.3);
      }
    for (const z of [-D / 2 + 6, D / 2 - 6])
      for (const sign of [-1, 1]) {
        const dormer = new THREE.Group();
        dormer.position.set(sign * (crossWidth / 2 - 1), 14, z);
        dormer.rotation.y = (sign * Math.PI) / 2;
        g.add(dormer);
        box(dormer, 0, 0, 0, 3.2, 2.7, 2.5, trim);
        stationArch(dormer, 0, 0.2, 1.28, 1.8, 2.3);
        roofLoft(dormer, [
          [2.7, 3.6, 2.9],
          [4.0, 0.05, 2.9],
        ]);
        finial(dormer, 0, 4.0, 0, 1.3);
      }
    // More compact lantern, below the tall chimney crowns as in the engraving.
    cylinder(g, 0, 17.5, 0, 5.8, 6.3, 3.5, m.roof, 8);
    cylinder(g, 0, 20.6, 0, 4.8, 5.8, 1.1, m.roof, 8);
    cylinder(g, 0, 21, 0, 4.7, 4.7, 8, red, 8);
    for (let i = 0; i < 8; i++) {
      const angle = ((i + 0.5) * Math.PI) / 4,
        rr = 4.7 * Math.cos(Math.PI / 8) + 0.04;
      const face = stationArch(g, Math.sin(angle) * rr, 21.4, Math.cos(angle) * rr, 2.4, 6.8, angle);
      for (const dx of [-0.48, 0.48]) cylinder(face, dx, 0.2, 0.17, 0.07, 0.07, 5.8, green, 6);
      beam(face, [-1.5, 6.9, 0.05], [0, 8.3, 0.05], 0.14, trim);
      beam(face, [0, 8.3, 0.05], [1.5, 6.9, 0.05], 0.14, trim);
      const edge = (i * Math.PI) / 4;
      cylinder(g, Math.sin(edge) * 4.8, 20.8, Math.cos(edge) * 4.8, 0.2, 0.26, 8.5, trim, 8);
      finial(g, Math.sin(edge) * 4.8, 29.3, Math.cos(edge) * 4.8, 1.4);
    }
    octagonalRoof(g, 0, 0, [
      [29, 5.2],
      [29.5, 5.4],
      [31, 4.4],
      [32.8, 2.3],
      [34.2, 0.25],
    ]);
    finial(g, 0, 34.2, 0, 2.5);
    // Corner turrets and cornice teeth visible in the modern architectural reference.
    for (const [x, z] of [
      [-crossWidth / 2 - 1, offset - mainDepth / 2 - 1],
      [-crossWidth / 2 - 1, offset + mainDepth / 2 + 1],
      [crossWidth / 2 + 1, offset - mainDepth / 2 - 1],
      [crossWidth / 2 + 1, offset + mainDepth / 2 + 1],
    ]) {
      cylinder(g, x, 8, z, 1.9, 2.2, 9.5, brickLight, 8);
      octagonalRoof(g, x, z, [
        [17.5, 2.7],
        [18, 2.8],
        [19.3, 1.8],
        [20.8, 0.2],
      ]);
      finial(g, x, 20.8, z, 2);
      for (let i = 0; i < 8; i++) {
        const a = ((i + 0.5) * Math.PI) / 4;
        arch(g, x + Math.sin(a) * 1.82, 14.3, z + Math.cos(a) * 1.82, 0.6, 1.8, a, trim);
      }
    }
    for (let x = -L / 2 + 1; x < L / 2; x += 1.5)
      for (const z of [offset - mainDepth / 2 - 0.25, offset + mainDepth / 2 + 0.25])
        box(g, x, 12, z, 0.6, 0.7, 0.7, trim);
    // Fine ridge cresting and pinnacles break the previously plain roof silhouette.
    for (let x = -L / 2 + 6; x <= L / 2 - 6; x += 1.2)
      if (Math.abs(x) > 6) {
        beam(g, [x - 0.5, 20.2, 0], [x, 20.95, 0], 0.045, m.iron);
        beam(g, [x, 20.95, 0], [x + 0.5, 20.2, 0], 0.045, m.iron);
      }
    for (let z = -D / 2 + 6; z <= D / 2 - 6; z += 1.2)
      if (Math.abs(z) > 6) {
        beam(g, [0, 20.2, z - 0.5], [0, 20.95, z], 0.045, m.iron);
        beam(g, [0, 20.95, z], [0, 20.2, z + 0.5], 0.045, m.iron);
      }
    // Broad decorated bases, slender shafts and pointed openwork crowns.
    // Base centres come from the period map; upper profiles remain interpreted.
    for (const chimney of plan.chimneys) {
      const dx = chimney.centre[0] - plan.centre[0],
        dz = chimney.centre[1] - plan.centre[1];
      const x = dx * Math.cos(theta) + dz * Math.sin(theta),
        z = -dx * Math.sin(theta) + dz * Math.cos(theta);
      const stack = new THREE.Group();
      stack.position.set(x, 0, z);
      stack.scale.set(0.68, 1, 0.68);
      g.add(stack);
      cylinder(stack, 0, 0, 0, 5.7, 6.4, 0.65, trim, 8);
      cylinder(stack, 0, 0.65, 0, 4.6, 5.7, 5.4, brickLight, 8);
      cylinder(stack, 0, 6.05, 0, 5.7, 4.6, 0.55, trim, 8);
      cylinder(stack, 0, 6.6, 0, 2.55, 5.7, 1.8, brickLight, 8);
      cylinder(stack, 0, 8.4, 0, 2.5, 2.5, 0.4, trim, 8);
      for (let i = 0; i < 8; i++) {
        const angle = ((i + 0.5) * Math.PI) / 4,
          rr = 4.9;
        stationArch(stack, Math.sin(angle) * rr, 1.25, Math.cos(angle) * rr, 1.35, 3.7, angle);
      }
      cylinder(stack, 0, 8.8, 0, 1.55, 2.25, 35.2, brickLight, 8);
      const radius = (y) => 2.25 - ((y - 8.8) * 0.7) / 35.2;
      for (let y = 11; y < 43; y += 3.3) {
        cylinder(stack, 0, y, 0, radius(y) + 0.035, radius(y) + 0.035, 0.13, trim, 8);
        // Sparse diagonal masonry ribs suggest the engraved shaft's diaper pattern.
        for (let i = 0; i < 8; i++) {
          const a = ((i + 0.5) * Math.PI) / 4,
            nx = Math.sin(a),
            nz = Math.cos(a),
            tx = Math.cos(a),
            tz = -Math.sin(a),
            rr = radius(y) * 0.924 + 0.015;
          const p = (u, v) => [nx * rr + tx * u, y + v, nz * rr + tz * u];
          beam(stack, p(-0.5, 0), p(0.5, 2.5), 0.035, red);
          beam(stack, p(0.5, 0), p(-0.5, 2.5), 0.035, red);
        }
      }
      cylinder(stack, 0, 44, 0, 2.1, 1.55, 0.8, trim, 8);
      cylinder(stack, 0, 44.8, 0, 2.2, 2.2, 0.35, trim, 16);
      cylinder(stack, 0, 45.15, 0, 1.35, 1.65, 2.0, brickLight, 8);
      cylinder(stack, 0, 47.15, 0, 0.22, 1.15, 5.7, brickLight, 8);
      for (let i = 0; i < 8; i++) {
        const a = (i * Math.PI) / 4,
          s = Math.sin(a),
          c = Math.cos(a);
        curveBeam(
          stack,
          [
            [s * 1.9, 45.2, c * 1.9],
            [s * 1.25, 47, c * 1.25],
            [s * 1.45, 49, c * 1.45],
            [s * 0.65, 51.6, c * 0.65],
            [s * 0.2, 53, c * 0.2],
          ],
          0.095,
          trim
        );
        finial(stack, s * 1.45, 49, c * 1.45, 2.2);
      }
      finial(stack, 0, 52.85, 0, 1.8);
    }
    scene.userData.stationStudy = {
      reference: 'Mary Evans 45687726, supplied 1868 engraving',
      wingEndBays: 5,
      chimneys: 2,
      chimneyHeight: 54.65,
      lanternHeight: 36.7,
      dimensionsInterpreted: true,
      sourceFootprintFid: plan.sourceFid,
      centre: plan.centre,
      angleDegrees: plan.angleDegrees,
      mainLength: L,
      crossLength: D,
      boilerWings: plan.boilerWings.length,
      chimneyCentres: plan.chimneys.map((c) => c.centre),
      footprintFit: plan.fit,
    };
    return g;
  }
  function factory(b) {
    const g = new THREE.Group();
    g.position.set(b.x, 0.15 + (b.landscapeLift ?? 0), b.z);
    scene.add(g);
    g.rotation.y = ((b.rotation || 0) * Math.PI) / 180;
    // Keep the mapped envelope. Roof divisions/elevations are comparative studies,
    // not identifications of individual buildings in the historic photographs.
    const curved = b.siteId === 253,
      sections = b.mapped ? Math.max(1, Math.round(b.depth / 23)) : 1;
    const span = b.depth / sections;
    for (let section = 0; section < sections; section++) {
      const part = new THREE.Group();
      part.position.z = -b.depth / 2 + (section + 0.5) * span;
      g.add(part);
      const w = b.width,
        d = span,
        h = b.height - (section % 3) * 0.65;
      const wall = b.siteId === 512 || b.siteId === 253 ? brickLight : m.brick;
      box(part, 0, 0, 0, w, h, d, wall);
      // Low pitched industrial ranges, with a raised ventilator on selected roofs.
      roofLoft(part, [
        [h, w + 0.65, d + 0.35],
        [h + 2.6, 0.08, d + 0.35],
      ]);
      for (const sign of [-1, 1]) {
        const front = new THREE.Group();
        front.position.z = sign * (d / 2 + 0.02);
        front.rotation.y = sign === 1 ? 0 : Math.PI;
        part.add(front);
        const shape = new THREE.Shape();
        shape.moveTo(-w / 2, h);
        shape.lineTo(w / 2, h);
        if (curved) {
          shape.lineTo(w / 2, h + 0.65);
          shape.quadraticCurveTo(0, h + 6.5, -w / 2, h + 0.65);
        } else {
          shape.lineTo(0, h + 2.6);
        }
        shape.closePath();
        front.add(
          new THREE.Mesh(new THREE.ExtrudeGeometry(shape, { depth: 0.3, bevelEnabled: false, curveSegments: 12 }), wall)
        );
        if (curved) {
          const oculus = new THREE.Mesh(new THREE.CircleGeometry(0.64, 16), m.window);
          oculus.position.set(0, h + 1.2, 0.32);
          front.add(oculus);
          const ring = new THREE.Mesh(new THREE.TorusGeometry(0.78, 0.12, 5, 16), wall);
          ring.position.set(0, h + 1.2, 0.34);
          front.add(ring);
        }
        // Tall loading entrance and narrower windows break the repeated frontage.
        box(front, 0, 0.08, 0.32, 2.5, Math.min(4, h - 1), 0.18, m.wood);
        for (const x of [-w * 0.31, w * 0.31]) {
          arch(front, x, 1.25, 0.32, 1.65, 2.8, 0, wall);
          if (h > 10) arch(front, x, 5.6, 0.32, 1.5, 2.5, 0, wall);
        }
        box(front, 0, 0.04, 0.3, w, 0.38, 0.4, m.stone);
        for (let z = -d / 2 + 2.5, bay = 0; z < d / 2 - 1; z += 4.3, bay++) {
          const side = new THREE.Group();
          side.position.set(sign * (w / 2 + 0.025), 0, z);
          side.rotation.y = sign === 1 ? Math.PI / 2 : -Math.PI / 2;
          part.add(side);
          if (bay % 5 === 2) {
            box(side, 0, 0.1, 0.08, 2.2, 3.8, 0.16, m.wood);
            box(side, 0, 3.9, 0.17, 2.6, 0.22, 0.45, wall);
            for (const x of [-0.85, -0.42, 0, 0.42, 0.85]) box(side, x, 0.15, 0.18, 0.025, 3.65, 0.02, m.dark);
          } else arch(side, 0, 1.4, 0.08, 1.6, 2.8, 0, wall);
          if (h > 9.5 && !(b.siteId === 875 && bay % 3 === 1)) arch(side, 0, 5.7, 0.08, 1.5, 2.5, 0, wall);
          box(side, -2.05, 0, 0.05, 0.42, h, 0.4, wall);
        }
        // Eaves shadows, rainwater pipes and a dark plinth ground each range.
        box(part, sign * (w / 2 + 0.2), h - 0.2, 0, 0.32, 0.22, d + 0.6, m.iron);
        box(part, sign * (w / 2 + 0.04), 0.05, 0, 0.12, 0.55, d, m.dark);
        for (const z of [-d / 2 + 0.5, d / 2 - 0.5]) {
          cylinder(part, sign * (w / 2 + 0.26), 0.2, z, 0.075, 0.075, h, m.iron, 6);
          beam(part, [sign * (w / 2 + 0.26), 0.4, z], [sign * (w / 2 + 0.65), 0.15, z], 0.08, m.iron);
        }
      }
      if ((section + b.siteId) % 2 === 0) {
        box(part, 0, h + 2.35, 0, 2.2, 0.65, d * 0.62, m.dark);
        roofLoft(part, [
          [h + 3, 3, d * 0.65],
          [h + 3.55, 0.08, d * 0.65],
        ]);
        for (let z = -d * 0.27; z < d * 0.3; z += 1.3) box(part, 0, h + 2.35, z, 2.25, 0.65, 0.1, m.wood);
      }
      box(part, 0, h + 2.55, 0, 0.18, 0.16, d + 0.5, m.stone);
    }
    return g;
  }
  const floatingMaterials = new Map();
  const holdFloor = m.wood.clone();
  holdFloor.color.set('#75654d');
  function barge(x, z, angle, loaded) {
    const g = new THREE.Group();
    g.position.set(x, 0.14, z);
    g.rotation.y = (angle * Math.PI) / 180;
    scene.add(g);
    const shape = new THREE.Shape();
    shape.moveTo(-2.7, -7.8);
    shape.bezierCurveTo(-2.7, -11.8, 2.7, -11.8, 2.7, -7.8);
    shape.lineTo(2.7, 7.2);
    shape.bezierCurveTo(2.7, 11.3, -2.7, 11.3, -2.7, 7.2);
    shape.closePath();
    const hole = new THREE.Path();
    hole.moveTo(-2.05, -6.8);
    hole.lineTo(-2.05, 6.4);
    hole.quadraticCurveTo(0, 8, 2.05, 6.4);
    hole.lineTo(2.05, -6.8);
    hole.closePath();
    shape.holes.push(hole);
    const hull = new THREE.Mesh(
      new THREE.ExtrudeGeometry(shape, {
        depth: 1.45,
        bevelEnabled: true,
        bevelSize: 0.12,
        bevelThickness: 0.1,
        bevelSegments: 1,
        steps: 1,
        curveSegments: 16,
      }),
      m.wood
    );
    hull.rotation.x = -Math.PI / 2;
    g.add(hull);
    // A closed bottom follows the entire curved hull, including both ends.
    // The former rectangular floor left gaps near the rounded end sections.
    const bottomShape = shape.clone();
    bottomShape.holes = [];
    const bottom = new THREE.Mesh(
      new THREE.ExtrudeGeometry(bottomShape, { depth: 0.12, bevelEnabled: false, curveSegments: 16 }),
      holdFloor
    );
    bottom.rotation.x = -Math.PI / 2;
    bottom.position.y = 0.24;
    g.add(bottom);
    for (let xx = -1.75; xx < 2; xx += 0.35) box(g, xx, 0.361, 0, 0.018, 0.012, 12.7, m.dark);
    // Outer rubbing strakes and transverse timbers frame a visibly hollow hold.
    const rim = shape.getPoints(32).map((p) => [p.x, 1.54, -p.y]);
    curveBeam(g, rim, 0.12, m.wood);
    curveBeam(
      g,
      rim.map(([a, _, c]) => [a, 0.5, c]),
      0.1,
      m.dark
    );
    for (const zz of [-5.5, 0, 5.5]) box(g, 0, 1.3, zz, 4.7, 0.18, 0.23, m.wood);
    for (const zz of [-8.4, 8.4]) {
      box(g, 0, 1.5, zz, 0.25, 0.2, 2.2, m.wood);
      cylinder(g, 0, 1.5, zz, 0.18, 0.18, 0.5, m.iron, 8);
      box(g, 0, 1.9, zz, 0.9, 0.12, 0.15, m.iron);
    }
    // Plank seams on solid end decks and small cleats suggest the scale of a working lighter.
    for (let xx = -2; xx <= 2; xx += 0.4) for (const zz of [-8.1, 8]) box(g, xx, 1.48, zz, 0.025, 0.04, 2.6, m.dark);
    if (loaded) {
      // A continuous load beneath densely packed angular coal and fines.
      // Several intersecting humps, not a few large rounded boulders.
      const mound = (x, z) =>
        0.85 +
        1.8 * Math.pow(Math.max(0, 1 - (x / 2.05) ** 2), 0.8) * Math.pow(Math.max(0, 1 - (z / 7.2) ** 2), 0.7) +
        0.13 * Math.sin(z * 1.7 + x * 3.1) * Math.max(0, 1 - Math.abs(x) / 2.1);
      const geometry = new THREE.PlaneGeometry(4.05, 14, 20, 60);
      geometry.rotateX(-Math.PI / 2);
      const p = geometry.getAttribute('position');
      for (let i = 0; i < p.count; i++) p.setY(i, mound(p.getX(i), p.getZ(i)) + (random() - 0.5) * 0.12);
      geometry.computeVertexNormals();
      g.add(new THREE.Mesh(geometry, m.coal));
      const pieces = Array.from({ length: 7 }, (_, variant) => {
        const geometry = new THREE.IcosahedronGeometry(1, 0),
          p = geometry.getAttribute('position');
        for (let i = 0; i < p.count; i++) {
          const x = p.getX(i),
            y = p.getY(i),
            z = p.getZ(i),
            factor = 1 + 0.3 * Math.sin(x * 7 + y * 13 + z * 17 + variant);
          p.setXYZ(i, x * factor, y * factor, z * factor);
        }
        geometry.computeVertexNormals();
        return geometry;
      });
      for (let i = 0; i < 1450; i++) {
        const xx = (random() - 0.5) * 3.9,
          zz = (random() - 0.5) * 13.5;
        const radius = 0.045 + Math.pow(random(), 2) * 0.19;
        const chunk = new THREE.Mesh(pieces[i % pieces.length], m.coal);
        chunk.scale.set(radius * (0.7 + random()), radius * (0.6 + random() * 0.8), radius * (0.7 + random()));
        chunk.position.set(xx, mound(xx, zz) + radius * 0.12, zz);
        chunk.rotation.set(random() * 3, random() * 3, random() * 3);
        g.add(chunk);
      }
    }
    curveBeam(
      g,
      [
        [0, 1.9, -8.4],
        [1, 0.8, -11],
        [2, 0.1, -14],
      ],
      0.045,
      m.wood
    );
    // Separate material batches let the lighters follow the water without
    // rebuilding their hulls or thousands of coal fragments.
    g.traverse((object) => {
      if (!object.isMesh) return;
      if (!floatingMaterials.has(object.material)) {
        const material = object.material.clone();
        material.userData.tidalFloat = true;
        floatingMaterials.set(object.material, material);
      }
      object.material = floatingMaterials.get(object.material);
    });
    return g;
  }
  function waterfront() {
    const wharf = [
      [23, 25],
      [32, 55],
      [40, 90],
      [21, 116],
      [4, 132],
    ];
    for (let i = 1; i < wharf.length; i++) {
      const [ax, az] = wharf[i - 1],
        [bx, bz] = wharf[i],
        length = Math.hypot(bx - ax, bz - az),
        a = Math.atan2(bx - ax, bz - az);
      for (let y = 0.1; y < 2.8; y += 0.35) {
        const plank = box(scene, (ax + bx) / 2, y, (az + bz) / 2, 0.55, 0.29, length, m.wood);
        plank.rotation.y = a;
      }
      for (let d = 0; d < length; d += 3) {
        const t = d / length;
        cylinder(scene, ax + (bx - ax) * t, 0, az + (bz - az) * t, 0.24, 0.3, 3.2, m.wood, 7);
      }
      const cap = box(scene, (ax + bx) / 2, 2.8, (az + bz) / 2, 1.1, 0.2, length, m.wood);
      cap.rotation.y = a;
    }
    // Mooring posts stand on both banks; ropes sag to their attachment points.
    for (const [x, z] of [
      [29, 46],
      [36, 71],
      [-31, 34],
      [-40, 92],
    ]) {
      cylinder(scene, x, 0, z, 0.3, 0.4, 2.1, m.wood, 8);
      curveBeam(
        scene,
        [
          [x, 1.8, z],
          [x + 2, 0.8, z + 4],
          [x + 4, 1.8, z + 8],
        ],
        0.055,
        m.wood
      );
    }
  }
  function holder(spec) {
    const g = new THREE.Group();
    g.position.set(spec.x, spec.landscapeLift ?? 0, spec.z);
    g.scale.set(spec.radius / 31, spec.height / 28, spec.radius / 31);
    scene.add(g);
    const bellTop = (spec.bellHeight * 28) / spec.height;
    cylinder(g, 0, 0, 0, 30, 30, 2, m.stone, 56);
    cylinder(g, 0, 2, 0, 28, 28, bellTop - 2, m.bell, 56);
    cylinder(g, 0, bellTop, 0, 24, 28, 1.8, m.bell, 56);
    for (let i = 0; i < spec.columns; i++) {
      const a = (i * Math.PI * 2) / spec.columns,
        b = ((i + 1) * Math.PI * 2) / spec.columns,
        x = Math.cos(a) * 31,
        z = Math.sin(a) * 31;
      cylinder(g, x, 2, z, 0.32, 0.48, 26, m.iron, 8);
      for (const y of [2, 14, 27]) {
        cylinder(g, x, y, z, 0.7, 0.7, 0.7, trim, 8);
        cylinder(g, x, y + 0.7, z, 0.45, 0.65, 0.5, m.iron, 8);
      }
      for (const y of [15, 28]) {
        const ex = Math.cos(b) * 31,
          ez = Math.sin(b) * 31;
        beam(g, [x, y, z], [ex, y, ez], 0.2, m.iron);
        beam(g, [x, y - 0.9, z], [ex, y - 0.9, ez], 0.18, m.iron);
        // Shallow lattice girders, not the later full-height diagonal alterations.
        for (let j = 0; j < 4; j++) {
          const t = j / 4,
            u = (j + 1) / 4;
          beam(g, [x + (ex - x) * t, y, z + (ez - z) * t], [x + (ex - x) * u, y - 0.9, z + (ez - z) * u], 0.07, m.iron);
        }
      }
      const bx = Math.cos(a) * 28.04,
        bz = Math.sin(a) * 28.04;
      beam(g, [bx, 2, bz], [bx, bellTop, bz], 0.07, m.iron);
    }
    for (const y of [bellTop * 0.3, bellTop * 0.55, bellTop * 0.8, bellTop]) {
      const ring = new THREE.Mesh(new THREE.TorusGeometry(28.06, 0.065, 4, 56), m.iron);
      ring.rotation.x = Math.PI / 2;
      ring.position.y = y;
      g.add(ring);
    }
    return g;
  }
  function houses(spec) {
    const g = new THREE.Group();
    g.position.set(spec.x, spec.landscapeLift ?? 0, spec.z);
    g.rotation.y = (spec.rotation * Math.PI) / 180;
    scene.add(g);
    const w = spec.width,
      d = spec.depth,
      h = spec.wallHeight;
    box(g, 0, 0, 0, w, h, d, brickLight);
    roofLoft(g, [
      [h, w + 0.7, d + 0.7],
      [h + 3, w - 5, 1],
    ]);
    box(g, 0, h + 2.95, 0, w - 5, 0.1, 1, m.roof);
    for (const y of [0.35, 3.3, 6.1]) box(g, 0, y, 0, w + 0.25, 0.15, d + 0.25, red);
    for (const sign of [-1, 1]) {
      // Paired entrances, round-headed windows and projecting gabled end bays.
      box(g, sign * 4.5, 0, d / 2 + 0.5, 3.8, h, 1.4, brickLight);
      const bay = new THREE.Group();
      bay.position.set(sign * 4.5, 0, d / 2 + 0.5);
      g.add(bay);
      roofLoft(
        bay,
        [
          [h, 4.3, 2],
          [h + 2, 0.05, 2],
        ],
        m.roof
      );
      for (const y of [1, 4]) arch(g, sign * 4.5, y, d / 2 + 1.23, 1.5, 2.1, 0, red);
      arch(g, sign * 1.2, 0.15, d / 2 + 0.05, 1.2, 2.6, 0, red);
      arch(g, sign * 1.2, 4, d / 2 + 0.05, 1.3, 2.1, 0, red);
      for (const xx of [1.4, 4.5]) for (const y of [1, 4]) arch(g, sign * xx, y, -d / 2 - 0.05, 1.3, 2.1, Math.PI, red);
      box(g, sign * 3, h + 1.3, -1, 1.1, 2.8, 0.85, m.brick);
      box(g, sign * 3, h + 3.9, -1, 1.4, 0.25, 1.1, trim);
      for (const xx of [-0.25, 0.25]) cylinder(g, sign * 3 + xx, h + 4.2, -1, 0.12, 0.15, 0.6, red, 8);
    }
    return g;
  }
  function terrace(spec) {
    const g = new THREE.Group();
    g.position.set(spec.x, spec.landscapeLift ?? 0, spec.z);
    g.rotation.y = (spec.rotation * Math.PI) / 180;
    scene.add(g);
    const w = spec.width,
      d = spec.depth,
      h = spec.wallHeight,
      bay = w / spec.bays,
      front = spec.frontSign ?? 1;
    // A continuous party-wall terrace; household divisions and elevations are interpreted.
    box(g, 0, 0, 0, w, h, d, brickLight);
    roofLoft(g, [
      [h, w + 0.32, d + 0.4],
      [h + 2.15, w + 0.32, 0.08],
    ]);
    box(g, 0, h + 2.12, 0, w + 0.32, 0.12, 0.18, m.roof);
    for (const sign of [-1, 1]) {
      box(g, 0, h - 0.12, sign * (d / 2 + 0.12), w, 0.13, 0.15, m.iron);
      box(g, 0, 0.06, sign * (d / 2 + 0.015), w, 0.32, 0.06, red);
    }
    for (let i = 0; i < spec.bays; i++) {
      const x = -w / 2 + (i + 0.5) * bay,
        doorSide = i % 2 === 0 ? -1 : 1;
      const window = (xx, y, sign, ww = 1.02) => {
        const z = sign * (d / 2 + 0.05);
        box(g, xx, y, z, ww, 1.55, 0.1, m.window);
        box(g, xx, y - 0.1, z + sign * 0.04, ww + 0.16, 0.12, 0.2, trim);
        box(g, xx, y + 1.56, z, ww + 0.18, 0.16, 0.16, red);
        box(g, xx, y + 0.74, z + sign * 0.06, ww, 0.055, 0.045, trim);
        box(g, xx, y, z + sign * 0.06, 0.045, 1.55, 0.045, trim);
      };
      for (const offset of [-bay * 0.23, bay * 0.23]) window(x + offset, 3.9, front);
      window(x - doorSide * bay * 0.23, 1.05, front);
      const doorX = x + doorSide * bay * 0.23,
        z = front * (d / 2 + 0.055);
      box(g, doorX, 0.08, z, 0.86, 2.08, 0.09, i % 3 === 0 ? green : m.wood);
      box(g, doorX, 2.18, z, 0.86, 0.28, 0.09, m.window);
      box(g, doorX, 2.48, z, 1.04, 0.15, 0.19, red);
      box(g, doorX, 0.01, z + front * 0.21, 1.02, 0.1, 0.5, trim);
      window(x, 3.9, -front, 0.95);
      window(x - doorSide * bay * 0.22, 1.12, -front, 0.8);
      box(g, x + doorSide * bay * 0.23, 0.08, -front * (d / 2 + 0.05), 0.78, 2.05, 0.09, m.wood);
      if (i % 2 === 0) {
        const party = -w / 2 + (i + 1) * bay;
        box(g, party, h + 1.35, 0, 1.1, 1.85, 0.72, m.brick);
        box(g, party, h + 3.17, 0, 1.3, 0.19, 0.94, trim);
        for (const offset of [-0.36, 0, 0.36]) cylinder(g, party + offset, h + 3.36, 0, 0.095, 0.13, 0.58, red, 6);
        for (const sign of [-1, 1]) box(g, party, 0, sign * (d / 2 + 0.09), 0.075, h, 0.075, m.iron);
      }
    }
    return g;
  }
  function mill(spec) {
    const g = new THREE.Group();
    g.position.set(spec.x, spec.landscapeLift ?? 0, spec.z);
    g.rotation.y = (spec.rotation * Math.PI) / 180;
    scene.add(g);
    const w = spec.width,
      d = spec.depth,
      h = spec.height;
    const boarding = m.wood.clone();
    boarding.color.set('#9a9e93');
    const boardsDark = m.wood.clone();
    boardsDark.color.set('#666d65');
    const tiles = m.roof.clone();
    tiles.color.set('#7b7160');
    // The c1800 image informs the interlocking gables, weatherboard upper floors
    // and masonry base. Survival of this form in 1900 is the author's hypothesis.
    box(g, 0, 0, 0, w, 3.1, d, brickLight);
    const ranges = [
      { x: -w * 0.325, w: w * 0.35, d: d * 0.94, h: h + 0.6, ridge: 'z' },
      { x: 0, w: w * 0.3, d: d, h: h - 0.35, ridge: 'x' },
      { x: w * 0.325, w: w * 0.35, d: d * 0.94, h: h - 0.05, ridge: 'z' },
    ];
    for (const range of ranges) {
      const part = new THREE.Group();
      part.position.x = range.x;
      g.add(part);
      box(part, 0, 3.1, 0, range.w, range.h - 3.1, range.d, boarding);
      const rise = range.ridge === 'z' ? 2.55 : 2.25;
      const top = range.ridge === 'z' ? [range.h + rise, 0.06, range.d + 0.3] : [range.h + rise, range.w + 0.3, 0.06];
      roofLoft(part, [[range.h, range.w + 0.35, range.d + 0.35], top], tiles);
      // Timber gable infill and thin horizontal lap boards carry the mill's scale.
      for (const sign of [-1, 1]) {
        if (range.ridge === 'z') {
          const shape = new THREE.Shape();
          shape.moveTo(-range.w / 2, range.h);
          shape.lineTo(range.w / 2, range.h);
          shape.lineTo(0, range.h + rise);
          shape.closePath();
          const face = new THREE.Mesh(new THREE.ShapeGeometry(shape), boarding);
          face.position.z = sign * (range.d / 2 + 0.01);
          if (sign < 0) face.rotation.y = Math.PI;
          part.add(face);
          box(part, 0, range.h + 0.45, sign * (range.d / 2 + 0.025), 0.65, 0.65, 0.06, m.window);
        }
        for (let y = 3.1; y < range.h; y += 0.22) {
          box(part, 0, y, sign * (range.d / 2 + 0.025), range.w, 0.035, 0.06, boardsDark);
          box(part, sign * (range.w / 2 + 0.025), y, 0, 0.06, 0.035, range.d, boardsDark);
        }
        for (const y of [3.9, 6.65, 9.35]) {
          if (y + 1.05 > range.h) continue;
          for (const x of [-range.w * 0.24, range.w * 0.24]) {
            box(part, x, y, sign * (range.d / 2 + 0.06), 0.72, 1.03, 0.06, m.window);
            for (const edge of [-1, 1])
              box(part, x + edge * 0.4, y - 0.05, sign * (range.d / 2 + 0.095), 0.085, 1.14, 0.07, boarding);
            box(part, x, y - 0.08, sign * (range.d / 2 + 0.1), 0.94, 0.1, 0.12, boarding);
            box(part, x, y + 0.48, sign * (range.d / 2 + 0.105), 0.74, 0.055, 0.06, boarding);
          }
          box(part, sign * (range.w / 2 + 0.055), y, 0, 0.06, 1.03, 0.76, m.window);
        }
      }
    }
    for (const sign of [-1, 1]) {
      for (const x of [-w * 0.32, 0, w * 0.32]) {
        arch(g, x, 0.22, sign * (d / 2 + 0.06), 1.6, 2.45, sign === 1 ? 0 : Math.PI, brickLight);
        box(g, x, 0.22, sign * (d / 2 + 0.12), 1.45, 2.1, 0.09, m.wood);
      }
      for (const x of [-w * 0.18, w * 0.18]) {
        box(g, x, 0.08, sign * (d / 2 + 0.18), 0.24, 3.05, 0.25, m.wood);
        beam(
          g,
          [x, 0.9, sign * (d / 2 + 0.18)],
          [x + (x < 0 ? 0.75 : -0.75), 3.03, sign * (d / 2 + 0.18)],
          0.1,
          m.wood
        );
      }
    }
    // A low sloping wheel-house cover follows the earlier image's waterside form.
    // Mechanism and hydraulic levels are not reconstructed from that image.
    const cover = new THREE.Group();
    cover.position.set(-w * 0.27, 0, d / 2 + 0.65);
    g.add(cover);
    box(cover, 0, 0, 0, 3.3, 1.3, 2, brickLight);
    const hood = box(cover, 0, 1.35, 0, 3.6, 0.14, 2.35, tiles);
    hood.rotation.x = -0.42;
    box(cover, 0, 0.1, 1.02, 1.15, 1.03, 0.06, m.dark);
    box(g, w * 0.39, h - 1, -d * 0.28, 0.8, 2.2, 0.65, brickLight);
    // Deliberately no windmill tower, cap or sails in the c1900 interpretation.
    return g;
  }
  function threeMills() {
    // Separate from Abbey Mill. Listed grid references locate these distant studies:
    // House Mill TQ3828582826; Clock Mill TQ3833482799. Dimensions/rotation estimated.
    const pale = m.wood.clone();
    pale.color.set('#c0bdb0');
    const house = new THREE.Group();
    house.position.set(-615, 0, 383);
    house.rotation.y = -0.28;
    scene.add(house);
    box(house, 0, 0, 0, 36, 10, 16, brickLight);
    box(house, 0, 2.2, -8.04, 22, 7.8, 0.12, pale);
    for (let y = 2.3; y < 10; y += 0.27) box(house, 0, y, -8.12, 22, 0.035, 0.04, m.wood);
    roofLoft(house, [
      [10, 36.6, 16.6],
      [16, 36.6, 0.06],
    ]);
    for (const sign of [-1, 1]) {
      for (let i = 0; i < 10; i++)
        for (const y of [1, 4, 7]) {
          const x = -16.2 + i * 3.6;
          box(house, x, y, sign * 8.15, 1.15, 1.8, 0.08, m.window);
          box(house, x, y - 0.1, sign * 8.2, 1.4, 0.14, 0.18, pale);
        }
      for (const y of [11, 13.5])
        for (const x of [-10, 0, 10]) {
          const z = sign * (y === 11 ? 5.7 : 2.4);
          box(house, x, y, z, 2, 1.5, 1.6, pale);
          box(house, x, y + 0.15, z + sign * 0.85, 1.3, 1.05, 0.08, m.window);
          box(house, x, y + 1.5, z, 2.3, 0.15, 1.9, m.roof);
        }
    }
    const clock = new THREE.Group();
    clock.position.set(-566, 0, 410);
    clock.rotation.y = -0.28;
    scene.add(clock);
    box(clock, -4, 0, 0, 32, 13.5, 14, m.brick);
    const clockRoof = new THREE.Group();
    clockRoof.position.x = -4;
    clock.add(clockRoof);
    roofLoft(clockRoof, [
      [13.5, 32.5, 14.5],
      [17, 32.5, 0.06],
    ]);
    for (const sign of [-1, 1])
      for (let i = 0; i < 8; i++)
        for (const y of [1, 4.1, 7.2, 10.3]) {
          const x = -18 + i * 4;
          box(clock, x, y, sign * 7.05, 1.3, 1.95, 0.1, m.window);
          box(clock, x, y - 0.12, sign * 7.12, 1.55, 0.15, 0.18, trim);
        }
    // Drying kilns and clock turret; later replacement cowls are omitted.
    for (const z of [-4.8, 4.8]) {
      box(clock, 18, 0, z, 11, 9, 9.4, m.brick);
      cylinder(clock, 18, 9, z, 0.45, 7.2, 7, m.roof, 16);
    }
    const tx = 12,
      tz = 12;
    box(clock, tx, 0, tz, 5.2, 10, 5.2, brickLight);
    cylinder(clock, tx, 10, tz, 2.8, 3.1, 4, brickLight, 8);
    cylinder(clock, tx, 14, tz, 2.25, 2.6, 3.8, pale, 8);
    cylinder(clock, tx, 17.8, tz, 1.8, 2.3, 1.9, pale, 8);
    cylinder(clock, tx, 19.7, tz, 0, 2.3, 2, m.roof, 8);
    for (const sign of [-1, 1]) {
      const dial = new THREE.Mesh(new THREE.CircleGeometry(0.82, 20), pale);
      dial.position.set(tx, 16.2, tz + sign * 2.48);
      if (sign < 0) dial.rotation.y = Math.PI;
      clock.add(dial);
      box(clock, tx, 16.2, tz + sign * 2.51, 0.06, 0.59, 0.04, m.iron);
      box(clock, tx + 0.19, 16.15, tz + sign * 2.52, 0.43, 0.06, 0.04, m.iron);
    }
    finial(clock, tx, 21.7, tz, 1.5);
    return { house, clock };
  }
  return { station, factory, barge, waterfront, holder, houses, terrace, mill, threeMills };
}
