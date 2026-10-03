// Shared mesh-building helpers. Scene modules used to define their own copies
// of these; new code should import them so the conventions stay identical.
//
// Conventions: scene x runs east, z runs south, y is up. Polygon rings are
// arrays of [x, z]; a polygon is [outerRing, ...holeRings]; a polygon list is
// an array of those. Triangles are [a, b, c] with [x, y, z] vertices.

// Convert a polygon (outer ring plus holes) to a THREE.Shape lying in the xz plane.
export function polygonShape(THREE, rings) {
  const shape = new THREE.Shape(rings[0].map(([x, z]) => new THREE.Vector2(x, -z)));
  for (const ring of rings.slice(1)) shape.holes.push(new THREE.Path(ring.map(([x, z]) => new THREE.Vector2(x, -z))));
  return shape;
}

// Add one flat mesh per polygon at height y. Returns the meshes.
export function flatSurface(THREE, parent, polygons, material, y = 0) {
  const meshes = [];
  for (const rings of polygons) {
    const mesh = new THREE.Mesh(new THREE.ShapeGeometry(polygonShape(THREE, rings)), material);
    mesh.rotation.x = -Math.PI / 2;
    mesh.position.y = y;
    parent.add(mesh);
    meshes.push(mesh);
  }
  return meshes;
}

// Axis-aligned box whose base sits at y. Returns the mesh.
export function box(THREE, parent, x, y, z, width, height, depth, material) {
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(width, height, depth), material);
  mesh.position.set(x, y + height / 2, z);
  parent.add(mesh);
  return mesh;
}

// Vertical cylinder (or cone) whose base sits at y. Returns the mesh.
export function cylinder(THREE, parent, x, y, z, radiusTop, radiusBottom, height, material, segments = 16) {
  const mesh = new THREE.Mesh(new THREE.CylinderGeometry(radiusTop, radiusBottom, height, segments), material);
  mesh.position.set(x, y + height / 2, z);
  parent.add(mesh);
  return mesh;
}

// Thin cylinder between two [x, y, z] points. Returns the mesh.
export function beam(THREE, parent, a, b, radius, material) {
  const av = new THREE.Vector3(...a),
    bv = new THREE.Vector3(...b),
    delta = bv.clone().sub(av);
  const mesh = new THREE.Mesh(new THREE.CylinderGeometry(radius, radius, delta.length(), 6), material);
  mesh.position.copy(av.add(bv).multiplyScalar(0.5));
  mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), delta.normalize());
  parent.add(mesh);
  return mesh;
}

// Collects triangles per material into flat position arrays, then builds one
// mesh per material. Replaces the inline tri/quad batchers in several modules.
export function createTriangleBatcher() {
  const batches = new Map();
  const batch = (material) => {
    if (!batches.has(material)) batches.set(material, { positions: [], uv: [] });
    return batches.get(material);
  };
  return {
    // a, b, c are [x, y, z]; optional uv is [[u, v], [u, v], [u, v]].
    triangle(material, a, b, c, uv) {
      const target = batch(material);
      target.positions.push(...a, ...b, ...c);
      if (uv) target.uv.push(...uv.flat());
    },
    // Two triangles for the quad a-b-c-d (counter-clockwise seen from the front).
    quad(material, a, b, c, d, uv) {
      this.triangle(material, a, b, c, uv && [uv[0], uv[1], uv[2]]);
      this.triangle(material, a, c, d, uv && [uv[0], uv[2], uv[3]]);
    },
    // Build and add one mesh per material. Returns the meshes.
    build(THREE, parent, { name = '', castShadow = true, receiveShadow = true } = {}) {
      const meshes = [];
      for (const [material, { positions, uv }] of batches) {
        if (!positions.length) continue;
        const geometry = new THREE.BufferGeometry();
        geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
        if (uv.length === (positions.length / 3) * 2)
          geometry.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
        geometry.computeVertexNormals();
        const mesh = new THREE.Mesh(geometry, material);
        mesh.name = name;
        mesh.castShadow = castShadow;
        mesh.receiveShadow = receiveShadow;
        parent.add(mesh);
        meshes.push(mesh);
      }
      return meshes;
    },
    get size() {
      return batches.size;
    },
  };
}

// Signed area of a ring of [x, z] points; positive when counter-clockwise in xz.
export function signedArea(ring) {
  let sum = 0;
  for (let i = 0; i < ring.length; i++) {
    const [x0, z0] = ring[i],
      [x1, z1] = ring[(i + 1) % ring.length];
    sum += x0 * z1 - x1 * z0;
  }
  return sum / 2;
}
