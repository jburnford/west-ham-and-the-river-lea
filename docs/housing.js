// Household divisions and yard fittings are interpretations within mapped blocks.
export function housingDetails({ THREE, scene, materials: m, data, level, box }) {
  const detail = data.housingDetail,
    rows = new Map(detail.rows.map((r) => [r.id, r]));
  const brick = m.brick.clone();
  brick.color.set('#807963');
  const cap = m.brick.clone();
  cap.color.set('#726b5b');
  const paving = ['#837e70', '#8b8373', '#777568'].map((c) => {
    const v = m.stone.clone();
    v.color.set(c);
    return v;
  });
  const required = new Set(),
    sampled = new Map();
  const request = ([x, z]) => {
    const ix = Math.floor(x),
      iz = Math.floor(z);
    for (const [a, b] of [
      [0, 0],
      [1, 0],
      [0, 1],
      [1, 1],
    ])
      required.add(`${ix + a},${iz + b}`);
  };
  const world = (r, u, v) => {
    const a = (-r.rotation * Math.PI) / 180;
    return [r.x + u * Math.cos(a) - v * Math.sin(a), r.z + u * Math.sin(a) + v * Math.cos(a)];
  };
  for (const p of [...detail.plots, ...detail.forecourts])
    for (const rings of p.polygons) for (const ring of rings) ring.forEach(request);
  for (const [a, b] of detail.walls) {
    request(a);
    request(b);
    request([(a[0] + b[0]) / 2, (a[1] + b[1]) / 2]);
  }
  for (const s of [...detail.extensions, ...detail.privies]) request(world(rows.get(s.rowId), s.u, s.v));
  const network = data.riverNetwork.positions;
  for (let i = 0; i < network.length; i += 3) {
    const key = `${network[i]},${network[i + 2]}`;
    if (required.has(key)) sampled.set(key, network[i + 1]);
  }
  function ground(x, z) {
    if (data.mainLandscape?.weight(x, z) > 0) return level(x, z);
    const [bx, bz, ex, ez] = data.terrain.bounds;
    if (x >= bx && x <= ex && z >= bz && z <= ez) return level(x, z);
    const ix = Math.floor(x),
      iz = Math.floor(z),
      u = x - ix,
      v = z - iz,
      at = (a, b) => sampled.get(`${ix + a},${iz + b}`) ?? -0.1;
    return (at(0, 0) * (1 - u) + at(1, 0) * u) * (1 - v) + (at(0, 1) * (1 - u) + at(1, 1) * u) * v;
  }
  function surface(polygons, material) {
    const vertices = [];
    for (const rings of polygons) {
      const contours = rings.map((r) => r.map(([x, z]) => new THREE.Vector2(x, z))),
        flat = rings.flat();
      for (const triangle of THREE.ShapeUtils.triangulateShape(contours[0], contours.slice(1))) {
        const pts = triangle.map((i) => flat[i]);
        if ((pts[1][0] - pts[0][0]) * (pts[2][1] - pts[0][1]) - (pts[1][1] - pts[0][1]) * (pts[2][0] - pts[0][0]) > 0)
          pts.reverse();
        for (const [x, z] of pts) vertices.push(x, ground(x, z) + 0.025, z);
      }
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
    geo.computeVertexNormals();
    scene.add(new THREE.Mesh(geo, material));
  }
  detail.plots.forEach((p, i) => surface(p.polygons, paving[i % 3]));
  detail.forecourts.forEach((p) => surface(p.polygons, paving[1]));
  for (const [a, b] of detail.walls) {
    const dx = b[0] - a[0],
      dz = b[1] - a[1],
      length = Math.hypot(dx, dz),
      x = (a[0] + b[0]) / 2,
      z = (a[1] + b[1]) / 2;
    const g = new THREE.Group();
    g.position.set(x, ground(x, z), z);
    g.rotation.y = -Math.atan2(dz, dx);
    scene.add(g);
    box(g, 0, 0, 0, length, 1.55, 0.16, brick);
    box(g, 0, 1.55, 0, length + 0.03, 0.09, 0.21, cap);
  }
  function outbuilding(s, privy = false) {
    const r = rows.get(s.rowId),
      [x, z] = world(r, s.u, s.v),
      rear = -r.frontSign;
    const g = new THREE.Group();
    g.position.set(x, ground(x, z), z);
    g.rotation.y = (r.rotation * Math.PI) / 180;
    scene.add(g);
    box(g, 0, 0, 0, s.width, s.height, s.depth, brick);
    const roof = box(g, 0, s.height, 0, s.width + 0.18, 0.13, s.depth + 0.2, m.roof);
    roof.rotation.x = rear * 0.12;
    box(g, 0, 0.08, rear * (s.depth / 2 + 0.018), privy ? 0.57 : 0.7, privy ? 1.55 : 1.95, 0.05, m.wood);
    if (!privy) box(g, s.width / 2 + 0.02, 1.2, 0, 0.04, 0.72, 0.65, m.window);
  }
  detail.extensions.forEach((s) => outbuilding(s));
  detail.privies.forEach((s) => outbuilding(s, true));
  return { ...detail.counts, sharedWallSegments: detail.walls.length };
}
