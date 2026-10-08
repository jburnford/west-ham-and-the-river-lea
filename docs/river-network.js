// Bank sections are interpretations; channel outlines retain their GIS provenance.
export async function loadRiverNetwork(load) {
  const data = await load('./data/river-network.json');
  const files = await Promise.all(
    [data.positionFile, data.indexFile, data.colorFile]
      .concat(data.sedimentFile, data.landcoverFile)
      .map((file) => load(`./data/${file}`, 'buffer'))
  );
  data.positions = new Float32Array(files[0]);
  data.indices = new Uint32Array(files[1]);
  data.colors = new Uint8Array(files[2]);
  data.sediment = new Uint8Array(files[3]);
  data.landcover = new Uint8Array(files[4]);
  if (
    data.positions.length !== data.vertices * 3 ||
    data.colors.length !== data.positions.length ||
    data.indices.length !== data.triangles * 3 ||
    data.sediment.length !== data.vertices ||
    data.landcover.length !== data.vertices * 2
  )
    throw new Error('River network dimensions do not match');
  // The low-water stream down the silted back rivers (data/maps/back-river-beds.json).
  if (data.lowWaterStream) {
    const stream = data.lowWaterStream;
    const [p, i] = await Promise.all([stream.positionFile, stream.indexFile].map((f) => load(`./data/${f}`, 'buffer')));
    stream.positions = new Float32Array(p);
    stream.indices = new Uint32Array(i);
    if (stream.positions.length !== stream.vertices * 3 || stream.indices.length !== stream.triangles * 3)
      throw new Error('Low-water stream dimensions do not match');
  }
  // Garden beds and sheds also extend west of the detailed Channelsea grid.
  // Sample the new marsh there instead of placing those objects at zero height.
  const points = data.marshDitches.marshPolygons.flat(2),
    xs = points.map((p) => p[0]),
    zs = points.map((p) => p[1]);
  const x0 = Math.floor(Math.min(...xs)) - 2,
    z0 = Math.floor(Math.min(...zs)) - 2,
    x1 = Math.ceil(Math.max(...xs)) + 2,
    z1 = Math.ceil(Math.max(...zs)) + 2;
  const width = x1 - x0 + 1,
    levels = new Float32Array(width * (z1 - z0 + 1)).fill(NaN);
  for (let i = 0; i < data.positions.length; i += 3) {
    const x = data.positions[i],
      z = data.positions[i + 2];
    if (x >= x0 && x <= x1 && z >= z0 && z <= z1) levels[(z - z0) * width + x - x0] = data.positions[i + 1];
  }
  data.marshLevel = (x, z) => {
    if (x < x0 || x >= x1 || z < z0 || z >= z1) return 0;
    const ix = Math.floor(x),
      iz = Math.floor(z),
      u = x - ix,
      v = z - iz,
      at = (a, b) => levels[(b - z0) * width + a - x0];
    const values = [at(ix, iz), at(ix + 1, iz), at(ix, iz + 1), at(ix + 1, iz + 1)];
    if (!values.every(Number.isFinite)) return 0;
    return (values[0] * (1 - u) + values[1] * u) * (1 - v) + (values[2] * (1 - u) + values[3] * u) * v;
  };
  return data;
}

export function riverNetwork({ THREE, scene, materials, data, surfaces }) {
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(data.positions, 3));
  geometry.setAttribute('sediment', new THREE.BufferAttribute(data.sediment, 1, true));
  geometry.setAttribute('landCover', new THREE.BufferAttribute(data.landcover, 2, true));
  const uv = new Float32Array(data.vertices * 2);
  for (let i = 0; i < data.vertices; i++) uv.set([data.positions[i * 3], data.positions[i * 3 + 2]], i * 2);
  geometry.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
  geometry.setIndex(new THREE.BufferAttribute(data.indices, 1));
  geometry.computeVertexNormals();
  const material = materials.land;
  surfaces.weather(material);
  const mesh = new THREE.Mesh(geometry, material);
  mesh.name = 'Mapped river network banks';
  mesh.userData.keepIndexed = true;
  mesh.receiveShadow = true;
  mesh.castShadow = false;
  scene.add(mesh);
  // Batched provisional masonry edges at industrial frontages. Earth slopes
  // elsewhere are in the terrain; no continuous modern concrete lining.
  const walls = data.retainingEdges,
    vertices = [];
  const tri = (a, b, c) => vertices.push(...a, ...b, ...c);
  const quad = (a, b, c, d) => {
    tri(a, b, c);
    tri(a, c, d);
  };
  for (const [routeIndex, route] of walls.routes.entries())
    for (let i = 1; i < route.length; i++) {
      const a = route[i - 1],
        b = route[i],
        dx = b[0] - a[0],
        dz = b[1] - a[1],
        len = Math.hypot(dx, dz),
        nx = ((-dz / len) * walls.width) / 2,
        nz = ((dx / len) * walls.width) / 2;
      const ring = [
        [a[0] + nx, a[1] + nz],
        [b[0] + nx, b[1] + nz],
        [b[0] - nx, b[1] - nz],
        [a[0] - nx, a[1] - nz],
      ];
      const at = (p, y) => [p[0], y, p[1]];
      const profile = walls.crestProfiles?.[routeIndex],
        tops = profile ? [profile[i - 1], profile[i], profile[i], profile[i - 1]] : ring.map(() => walls.crestHeight);
      for (let j = 0; j < 4; j++)
        quad(
          at(ring[j], walls.baseHeight),
          at(ring[j], tops[j]),
          at(ring[(j + 1) % 4], tops[(j + 1) % 4]),
          at(ring[(j + 1) % 4], walls.baseHeight)
        );
      quad(...ring.map((p, j) => at(p, tops[j])).reverse());
    }
  const wallGeometry = new THREE.BufferGeometry();
  wallGeometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
  wallGeometry.computeVertexNormals();
  const wallMaterial = materials.brick.clone();
  wallMaterial.color.set('#787366');
  wallMaterial.side = THREE.DoubleSide;
  const wallMesh = new THREE.Mesh(wallGeometry, wallMaterial);
  wallMesh.name = 'Interpreted tidal retaining edges';
  scene.add(wallMesh);
  return {
    channels: data.channels.length,
    vertices: data.vertices,
    triangles: data.triangles,
    reviewedConnections: data.reviewedConnections.connections.map((r) => ({
      id: r.id,
      category: r.category,
      capacity: r.capacity,
    })),
    deferredConnections: data.reviewedConnections.deferred,
  };
}

// The Lea's water in the silted back rivers when the tide is out, level across each channel and sloping
// from the heads to Three Mills. It stays still (not batched, not moved with the tide): the tidal
// surface rises over it from Three Mills, so the higher of the two shows.
export function lowWaterStream({ THREE, scene, material, stream }) {
  if (!stream) return null;
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(stream.positions, 3));
  const normals = new Float32Array(stream.positions.length);
  for (let i = 1; i < normals.length; i += 3) normals[i] = 1;
  geometry.setAttribute('normal', new THREE.BufferAttribute(normals, 3));
  const uv = new Float32Array(stream.vertices * 2);
  for (let i = 0; i < stream.vertices; i++) uv.set([stream.positions[i * 3], stream.positions[i * 3 + 2]], i * 2);
  geometry.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
  geometry.setIndex(new THREE.BufferAttribute(stream.indices, 1));
  geometry.computeBoundingSphere();
  const mesh = new THREE.Mesh(geometry, material);
  mesh.name = 'Low-water stream in the back rivers';
  mesh.userData.keepIndexed = true;
  mesh.userData.fixedLevel = true;
  mesh.receiveShadow = true;
  scene.add(mesh);
  return mesh;
}
