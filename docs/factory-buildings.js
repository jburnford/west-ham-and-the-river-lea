// Individually registered period-map envelopes. Elevations remain reconstructions.
// Batched surfaces keep the several hundred ranges inexpensive to draw.
import { createRandom } from './lib/prng.js';
export function factoryBuildings({ THREE, scene, materials: m, data, box, cylinder, beam }) {
  const batches = new Map();
  const pale = m.wood.clone();
  pale.color.set('#bcb9aa');
  const stock = m.brick.clone();
  stock.color.set('#918575');
  const redbrick = m.brick.clone();
  redbrick.color.set('#946653');
  const sootInterior = m.dark.clone();
  sootInterior.side = THREE.BackSide;
  const frame = m.wood.clone();
  frame.color.set('#827d6e');
  const ironRoof = m.iron.clone();
  ironRoof.color.set('#787d7b');
  ironRoof.roughness = 0.78;
  ironRoof.metalness = 0.28;
  const sheet = document.createElement('canvas');
  sheet.width = sheet.height = 128;
  const sheetContext = sheet.getContext('2d');
  const sheetRandom = createRandom(1893);
  for (let x = 0; x < 128; x++) {
    const shade = Math.round(155 + 18 * Math.cos((x * Math.PI) / 8));
    sheetContext.fillStyle = `rgb(${shade},${shade},${shade})`;
    sheetContext.fillRect(x, 0, 1, 128);
  }
  for (let n = 0; n < 1800; n++) {
    sheetContext.fillStyle = sheetRandom() > 0.5 ? 'rgba(73,63,50,.12)' : 'rgba(205,207,200,.10)';
    sheetContext.fillRect(sheetRandom() * 128, sheetRandom() * 128, 1, 2);
  }
  const sheetMap = new THREE.CanvasTexture(sheet);
  sheetMap.colorSpace = THREE.SRGBColorSpace;
  sheetMap.wrapS = sheetMap.wrapT = THREE.RepeatWrapping;
  sheetMap.repeat.set(0.5, 0.5);
  ironRoof.map = sheetMap;
  ironRoof.bumpMap = sheetMap.clone();
  ironRoof.bumpMap.colorSpace = THREE.NoColorSpace;
  ironRoof.bumpMap.needsUpdate = true;
  ironRoof.bumpScale = 0.012;
  ironRoof.userData.surface = 'roof';
  const walls = { brick: stock, redbrick, wood: m.wood, metal: m.iron, pale };
  function tri(material, a, b, c) {
    if (!batches.has(material)) batches.set(material, { positions: [], uv: [] });
    const batch = batches.get(material);
    batch.positions.push(...a, ...b, ...c);
    const normal = new THREE.Vector3()
      .subVectors(new THREE.Vector3(...b), new THREE.Vector3(...a))
      .cross(new THREE.Vector3().subVectors(new THREE.Vector3(...c), new THREE.Vector3(...a)));
    const roof = Math.abs(normal.y) > Math.max(Math.abs(normal.x), Math.abs(normal.z));
    for (const p of [a, b, c])
      batch.uv.push(
        (roof ? p[0] : Math.abs(normal.x) > Math.abs(normal.z) ? p[2] : p[0]) / 5500,
        (roof ? p[2] : p[1]) / 5500
      );
  }
  function quad(material, a, b, c, d) {
    tri(material, a, b, c);
    tri(material, a, c, d);
  }
  // Clip each roof plane to its own footprint, including adjoining-range cutouts.
  function clip(poly, axis, value, greater) {
    const result = [];
    for (let i = 0; i < poly.length; i++) {
      const a = poly[i],
        b = poly[(i + 1) % poly.length],
        ia = greater ? a[axis] >= value - 1e-7 : a[axis] <= value + 1e-7,
        ib = greater ? b[axis] >= value - 1e-7 : b[axis] <= value + 1e-7;
      if (ia) result.push(a);
      if (ia !== ib) {
        const t = (value - a[axis]) / (b[axis] - a[axis]);
        result.push(a.map((v, j) => v + (b[j] - v) * t));
      }
    }
    return result;
  }
  const counts = {
    sites: data.sites.length,
    ranges: 0,
    roofPlanes: 0,
    windows: 0,
    holders: data.holders.length,
    siteRanges: {},
    chimneys: 0,
    chimneysWithMappedHeights: 0,
    siteChimneys: {},
    chimneyTops: [],
    tanks: [],
    kilns: [],
    landmarks: [],
  };
  for (const b of data.buildings) {
    const angle = (b.rotation * Math.PI) / 180,
      c = Math.cos(angle),
      s = Math.sin(angle);
    const toLocal = ([x, z]) => [(x - b.x) * c + (z - b.z) * s, -(x - b.x) * s + (z - b.z) * c];
    const world = ([u, v], y) => [b.x + u * c - v * s, y + (b.landscapeLift ?? 0), b.z + u * s + v * c];
    const base = b.baseHeight ?? 0.12,
      h = b.height,
      wall = b.finish === 'pale' ? pale : walls[b.material] || stock;
    const roofMaterial = b.roofMaterial === 'iron' ? ironRoof : m.roof;
    const axis = b.roofAxis === 'x' ? 1 : 0;
    const lo = b.localBounds[0][axis],
      hi = b.localBounds[1][axis],
      bay = (hi - lo) / b.roofBays;
    const roofHeight = (p) => {
      const fraction = Math.min(0.999999, Math.max(0, (p[axis] - lo) / (hi - lo))) * b.roofBays;
      return base + h + b.roofRise * (b.roof === 'lean' ? fraction % 1 : 1 - Math.abs(2 * (fraction % 1) - 1));
    };
    const components = b.renderPolygons || [{ outer: b.footprint, holes: [] }];
    for (const component of components) {
      const local = component.outer.map(toLocal),
        holes = component.holes.map((r) => r.map(toLocal));
      // Signed area determines outward winding for walls and roof surfaces.
      const signedArea = (ring) =>
        ring.reduce(
          (sum, p, i) => sum + p[0] * ring[(i + 1) % ring.length][1] - ring[(i + 1) % ring.length][0] * p[1],
          0
        );
      if (signedArea(local) < 0) local.reverse();
      // Interior walls face into the opening, including mapped chimney wells.
      for (const hole of holes) if (signedArea(hole) > 0) hole.reverse();
      for (const ring of [local, ...holes])
        for (let i = 0; i < ring.length; i++) {
          const a = ring[i],
            z = ring[(i + 1) % ring.length],
            length = Math.hypot(z[0] - a[0], z[1] - a[1]);
          const divisions = [0, 1];
          for (let k = 0; k <= b.roofBays * 2; k++) {
            const t = (lo + (k * bay) / 2 - a[axis]) / (z[axis] - a[axis]);
            if (t > 1e-6 && t < 1 - 1e-6) divisions.push(t);
          }
          divisions.sort((a, b) => a - b);
          const at = (t) => a.map((v, j) => v + (z[j] - v) * t);
          for (let j = 1; j < divisions.length; j++) {
            const u = at(divisions[j - 1]),
              v = at(divisions[j]);
            if (base > 0.2) quad(wall, world(u, 0), world(u, base), world(v, base), world(v, 0));
            quad(wall, world(u, base), world(u, roofHeight(u)), world(v, roofHeight(v)), world(v, base));
          }
          // Fenestration is an explicit typological estimate; no random apparatus.
          if (length < 5) continue;
          const normal = [((z[1] - a[1]) / length) * 0.035, (-(z[0] - a[0]) / length) * 0.035];
          const bays = b.facadeBays || Math.max(1, Math.floor(length / 4.1));
          if (b.facadeBays)
            for (let k = 0; k <= bays; k++) {
              // Sugar House: five bays and stepped brick buttresses in ASE Fig21.
              const t = k / bays,
                half = 0.18 / length;
              const u = at(Math.max(0, t - half)),
                v = at(Math.min(1, t + half));
              for (const [bottom, top, outset] of [
                [0, 7.4, 0.3],
                [7.4, h, 0.18],
              ]) {
                const un = u.map((q, j) => q + (normal[j] * outset) / 0.035),
                  vn = v.map((q, j) => q + (normal[j] * outset) / 0.035);
                quad(
                  wall,
                  world(un, base + bottom),
                  world(un, base + top),
                  world(vn, base + top),
                  world(vn, base + bottom)
                );
                quad(
                  wall,
                  world(u, base + bottom),
                  world(u, base + top),
                  world(un, base + top),
                  world(un, base + bottom)
                );
                quad(
                  wall,
                  world(vn, base + bottom),
                  world(vn, base + top),
                  world(v, base + top),
                  world(v, base + bottom)
                );
              }
            }
          for (let floor = 0; floor < Math.max(1, Math.floor(b.storeys)); floor++)
            for (let k = 0; k < bays; k++) {
              const t = (k + 0.5) / bays,
                half = Math.min(0.65, (length / bays) * 0.2) / length;
              const u = at(t - half).map((v, j) => v + normal[j]),
                v = at(t + half).map((v, j) => v + normal[j]);
              const bottom = base + 1.2 + floor * 3.1,
                top = Math.min(base + h - 0.55, bottom + 1.75);
              if (top <= bottom) continue;
              // The attached weatherboard panel supplies its own openings. Do not
              // leave the generic masonry windows and projecting frames underneath.
              if (top > 2.2 && b.landmarkDetails?.houseFacades) {
                const [wx, , wz] = world(at(t), 0);
                const clad = b.landmarkDetails.houseFacades.some(([p, q]) => {
                  const dx = q[0] - p[0],
                    dz = q[1] - p[1],
                    length2 = dx * dx + dz * dz;
                  const along = ((wx - p[0]) * dx + (wz - p[1]) * dz) / length2;
                  return (
                    along >= 0 &&
                    along <= 1 &&
                    Math.abs((wx - p[0]) * dz - (wz - p[1]) * dx) / Math.sqrt(length2) < 0.02
                  );
                });
                if (clad) continue;
              }
              quad(m.window, world(u, bottom), world(u, top), world(v, top), world(v, bottom));
              if (b.louvredUpperStorey && floor === Math.floor(b.storeys) - 1) {
                // Goad explicitly notes louvred windows; dimensions are interpreted.
                for (let y = bottom; y < top; y += 0.22)
                  quad(frame, world(u, y), world(u, y + 0.075), world(v, y + 0.075), world(v, y));
                continue;
              }
              // Simple joinery and a projecting sill give the estimated openings
              // depth at walking distance. No tenant-specific facade is implied.
              const opening = (t0, t1, y0, y1, outset, material) => {
                const p = at(t0).map((q, j) => q + (normal[j] * outset) / 0.035),
                  r = at(t1).map((q, j) => q + (normal[j] * outset) / 0.035);
                quad(material, world(p, y0), world(p, y1), world(r, y1), world(r, y0));
              };
              const jamb = 0.055 / length;
              opening(t - half - jamb, t - half, bottom - 0.055, top + 0.055, 0.06, frame);
              opening(t + half, t + half + jamb, bottom - 0.055, top + 0.055, 0.06, frame);
              opening(t - half, t + half, top, top + 0.055, 0.06, frame);
              opening(t - half, t + half, (top + bottom) / 2 - 0.025, (top + bottom) / 2 + 0.025, 0.065, frame);
              opening(t - 0.022 / length, t + 0.022 / length, bottom, top, 0.065, frame);
              opening(t - half - jamb, t + half + jamb, bottom - 0.1, bottom, 0.13, m.stone);
              counts.windows++;
            }
          if (b.streetFrontage && length > 6) {
            // Plain entrances: occupancy and shop-front designs are not established.
            for (let k = 0; k < bays; k += 2) {
              const t = (k + 0.24) / bays,
                half = 0.45 / length;
              const u = at(Math.max(0.03, t - half)).map((v, j) => v + normal[j] * 1.2);
              const v = at(Math.min(0.97, t + half)).map((v, j) => v + normal[j] * 1.2);
              quad(m.wood, world(u, base), world(u, base + 2.1), world(v, base + 2.1), world(v, base));
            }
          }
        }
      // Triangulate concave footprints first, then clip each triangle to roof bands.
      const vectors = local.map((p) => new THREE.Vector2(...p)),
        all = [...local, ...holes.flat()];
      const triangles = THREE.ShapeUtils.triangulateShape(
        vectors,
        holes.map((r) => r.map((p) => new THREE.Vector2(...p)))
      );
      for (let k = 0; k < b.roofBays * 2; k++)
        for (const indices of triangles) {
          let p = indices.map((i) => all[i]);
          p = clip(p, axis, lo + (k * bay) / 2, true);
          p = clip(p, axis, lo + ((k + 1) * bay) / 2, false);
          const planeMaterial = b.roofGlazing && k % 2 === 1 ? m.window : roofMaterial;
          for (let j = 2; j < p.length; j++)
            tri(
              planeMaterial,
              world(p[0], roofHeight(p[0])),
              world(p[j], roofHeight(p[j])),
              world(p[j - 1], roofHeight(p[j - 1]))
            );
        }
    }
    counts.ranges++;
    counts.roofPlanes += b.roofBays * 2;
    counts.siteRanges[b.siteId] = (counts.siteRanges[b.siteId] || 0) + 1;
    // Landmark treatments are chosen by the data's landmarkDetails.kind, never by building ID.
    if (b.landmarkDetails?.kind === 'mill-house') {
      const g = new THREE.Group();
      g.position.set(b.x, b.landscapeLift ?? 0, b.z);
      g.rotation.y = -angle;
      scene.add(g);
      {
        // Weatherboarded central upper facade and attic dormers: surviving mill character.
        const facades = b.landmarkDetails?.houseFacades;
        if (facades)
          for (const [a, z] of facades) {
            const face = new THREE.Group(),
              length = Math.hypot(z[0] - a[0], z[1] - a[1]);
            face.position.set((a[0] + z[0]) / 2, b.landscapeLift ?? 0, (a[1] + z[1]) / 2);
            face.rotation.y = -Math.atan2(z[1] - a[1], z[0] - a[0]);
            scene.add(face);
            box(face, 0, 2.2, 0, length, h - 2.2, 0.1, pale);
            for (let x = -length * 0.4; x <= length * 0.41; x += length * 0.2)
              for (const y of [3.1, 6.2, 8.1])
                for (const sign of [-1, 1]) box(face, x, y, sign * 0.08, 1.05, 1.5, 0.05, m.window);
          }
        if (facades) counts.landmarks.push({ id: 'house-main-facades', segments: facades });
        for (const sign of [-1, 1]) {
          if (!facades) {
            box(g, 0, 2.2, sign * (b.depth / 2 + 0.03), b.width * 0.62, h - 2.2, 0.08, pale);
            for (let x = -b.width * 0.25; x <= b.width * 0.26; x += b.width * 0.125)
              for (const y of [3.1, 6.2, 8.1]) box(g, x, y, sign * (b.depth / 2 + 0.1), 1.05, 1.5, 0.05, m.window);
          }
          for (let x = -b.width * 0.25; x <= b.width * 0.3; x += b.width * 0.25) {
            const z = sign * b.depth * 0.3,
              dormerBase = roofHeight([x, z - sign * 0.7]) - 0.6;
            box(g, x, dormerBase, z, 1.7, 1.45, 1.4, pale);
            box(g, x, dormerBase + 0.15, sign * (b.depth * 0.3 + 0.73), 1.1, 1, 0.06, m.window);
            box(g, x, dormerBase + 1.45, z, 2, 0.12, 1.7, m.roof);
          }
        }
      }
    }
    if (b.landmarkDetails?.kind === 'kilns-and-tower') {
      const g = new THREE.Group();
      g.position.set(b.x, b.landscapeLift ?? 0, b.z);
      g.rotation.y = -angle;
      scene.add(g);
      const detail = b.landmarkDetails;
      if (detail?.kilnCaps)
        for (const cap of detail.kilnCaps) {
          const [x, z] = toLocal(cap.centre);
          cylinder(g, x, b.height, z, 0.4, cap.radius, cap.height, m.roof, 16);
          counts.landmarks.push({ id: 'clock-kiln-cap', centre: cap.centre, radius: cap.radius });
        }
      else
        for (const z of [-b.depth * 0.25, b.depth * 0.25])
          cylinder(g, 0, b.height, z, 0.4, Math.min(b.width, b.depth * 0.5) * 0.65, 5.7, m.roof, 16);
      const tower = detail?.tower,
        [tx, tz] = tower ? toLocal(tower.centre) : [-b.width * 0.7, -b.depth * 0.25];
      const width = tower?.width ?? 4.6,
        baseHeight = tower?.baseHeight ?? 12,
        lanternHeight = tower?.lanternHeight ?? 5.5;
      box(g, tx, 0, tz, width, baseHeight, width, stock);
      cylinder(g, tx, baseHeight, tz, width * 0.5, width * 0.565, lanternHeight, pale, 8);
      cylinder(g, tx, baseHeight + lanternHeight, tz, 0, width * 0.565, tower?.spireHeight ?? 3.6, m.roof, 8);
      if (tower) counts.landmarks.push({ id: 'clock-tower', centre: tower.centre, width });
      for (const sign of [-1, 1]) {
        const dial = new THREE.Mesh(new THREE.CircleGeometry(0.85, 24), pale);
        dial.position.set(tx, 15.4, tz + sign * width * 0.54);
        if (sign < 0) dial.rotation.y = Math.PI;
        g.add(dial);
        box(g, tx, 15.4, tz + sign * width * 0.55, 0.07, 0.65, 0.06, m.iron);
        box(g, tx + 0.2, 15.38, tz + sign * width * 0.55, 0.45, 0.07, 0.06, m.iron);
      }
    }
  }
  for (const [material, batch] of batches) {
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(batch.positions, 3));
    geometry.setAttribute('uv', new THREE.Float32BufferAttribute(batch.uv, 2));
    geometry.computeVertexNormals();
    const mesh = new THREE.Mesh(geometry, material);
    mesh.name = 'Registered factory ranges';
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    scene.add(mesh);
  }
  for (const p of data.structures) {
    if (p.kind === 'purifierBank') {
      const g = new THREE.Group();
      g.position.set(p.x, p.landscapeLift ?? 0, p.z);
      g.rotation.y = (-p.rotation * Math.PI) / 180;
      scene.add(g);
      for (let i = 0; i < p.count; i++) {
        const x = (i - (p.count - 1) / 2) * 9;
        box(g, x, 0.2, 0, 7, 1.8, 6, m.iron);
        box(g, x, 2, 0, 7.3, 0.15, 6.3, m.dark);
      }
    } else if (p.kind === 'chimney') {
      const g = new THREE.Group();
      g.name = p.id;
      g.position.set(p.x, (p.baseHeight ?? 0.34) + (p.landscapeLift ?? 0), p.z);
      g.rotation.y = (-(p.rotation ?? 0) * Math.PI) / 180;
      scene.add(g);
      const iron = p.material === 'iron',
        material = iron ? m.iron : stock;
      const sides = p.section === 'square' ? 4 : 16,
        turn = sides === 4 ? Math.PI / 4 : 0;
      const radius = p.radius,
        top = radius * (p.topRadiusRatio ?? (iron ? 0.88 : 0.62)),
        rim = top * (iron ? 1.08 : 1.2);
      const plinth = iron ? 0.45 : 1.1,
        crown = iron ? 0.15 : 0.45,
        throat = top * 0.63;
      const tube = (y, height, r0, r1, mat) => {
        const mesh = new THREE.Mesh(new THREE.CylinderGeometry(r1, r0, height, sides, 1, true), mat);
        mesh.position.y = y + height / 2;
        mesh.rotation.y = turn;
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        g.add(mesh);
      };
      tube(-0.4, plinth + 0.4, radius * 1.2, radius * 1.2, stock);
      tube(plinth, p.height - plinth - crown, radius, top, material);
      tube(p.height - crown, crown, rim, rim, material);
      // Recessed soot-dark throat, with an actual opening through the crown.
      // No capped cylinder across the mouth: overhead views can see its depth.
      tube(p.height - 1.5, 1.5, throat, throat, sootInterior);
      const dark = cylinder(g, 0, p.height - 1.55, 0, throat, throat, 0.05, m.dark, sides);
      dark.rotation.y = turn;
      const vertices = [];
      const ring = (inner, outer, y) => {
        for (let i = 0; i < sides; i++) {
          const a = turn + (i * 2 * Math.PI) / sides,
            b = turn + ((i + 1) * 2 * Math.PI) / sides;
          const at = (r, t) => [r * Math.sin(t), y, r * Math.cos(t)];
          vertices.push(
            ...at(inner, a),
            ...at(outer, a),
            ...at(outer, b),
            ...at(inner, a),
            ...at(outer, b),
            ...at(inner, b)
          );
        }
      };
      ring(throat, rim, p.height);
      ring(radius, radius * 1.2, plinth);
      const geometry = new THREE.BufferGeometry();
      geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
      geometry.computeVertexNormals();
      const lip = new THREE.Mesh(geometry, material);
      lip.receiveShadow = true;
      lip.castShadow = true;
      g.add(lip);
      counts.chimneys++;
      if (p.mappedHeightFeet) counts.chimneysWithMappedHeights++;
      counts.siteChimneys[p.siteId] = (counts.siteChimneys[p.siteId] || 0) + 1;
      counts.chimneyTops.push({
        id: p.id,
        position: [p.x, (p.baseHeight ?? 0.34) + (p.landscapeLift ?? 0) + p.height, p.z],
        section: p.section,
        material: p.material,
      });
    } else {
      cylinder(
        scene,
        p.x,
        0.1 + (p.landscapeLift ?? 0),
        p.z,
        p.radius,
        p.radius,
        p.height,
        p.kind === 'kiln' ? stock : m.iron,
        20
      );
      if (p.kind === 'tank')
        counts.tanks.push({
          id: p.id,
          position: [p.x, 0.1 + (p.landscapeLift ?? 0), p.z],
          radius: p.radius,
          height: p.height,
        });
      if (p.kind === 'kiln')
        counts.kilns.push({
          id: p.id,
          position: [p.x, 0.1 + (p.landscapeLift ?? 0), p.z],
          radius: p.radius,
          height: p.height,
        });
    }
  }
  return { ...counts, batchedMeshes: batches.size };
}
