// Brick plinths under buildings that stand on sloping ground or over a bank edge (task B, October 2026). The main
// landscape seats each building at one level (its pad, the level field or the median drawn ground under it); where
// the drawn ground under the footprint falls more than 0.3 m below that seat, scripts/build_main_landscape.py records
// a plinth (main-landscape-1900.json plinths.objects: id -> [bottom, top]) and this module draws the footprint's walls
// down from the seat to just below the lowest ground, so no building stands over a gap. Form: interpretation (a
// stepped or battered brick base was usual on sloping sites); the plinth tops are hidden under the buildings.
export function buildingPlinths({ THREE, scene, data, materials }) {
  const plinths = data.mainLandscape?.meta?.plinths?.objects;
  if (!plinths) return null;
  const rings = new Map();
  const add = (id, list) => id !== undefined && plinths[id] && list.length && rings.set(id, list);
  for (const b of data.factoryBuildings?.buildings ?? [])
    add(
      b.id,
      (b.renderPolygons ?? []).flatMap((p) => [p.outer, ...(p.holes ?? [])])
    );
  for (const b of data.highStreetFrontages?.buildings ?? [])
    add(b.id, b.renderPolygons ? b.renderPolygons.flatMap((p) => [p.outer, ...(p.holes ?? [])]) : [b.footprint]);
  for (const r of data.housingDetail?.rows ?? []) add(r.id, [r.footprint]);
  const positions = [],
    uvs = [];
  for (const [id, list] of rings) {
    const [bottom, top] = plinths[id];
    for (const ring of list) {
      if (!ring || ring.length < 3) continue;
      let run = 0;
      for (let i = 0; i < ring.length; i++) {
        const [ax, az] = ring[i],
          [bx, bz] = ring[(i + 1) % ring.length],
          length = Math.hypot(bx - ax, bz - az);
        if (!length) continue;
        // Texture coordinates in metres: along the outline, and height.
        const [u0, u1] = [run, (run += length)];
        // Both faces, so the wall reads from either side whatever the ring's winding.
        positions.push(ax, bottom, az, bx, bottom, bz, bx, top, bz, ax, bottom, az, bx, top, bz, ax, top, az);
        positions.push(ax, bottom, az, bx, top, bz, bx, bottom, bz, ax, bottom, az, ax, top, az, bx, top, bz);
        uvs.push(u0, bottom, u1, bottom, u1, top, u0, bottom, u1, top, u0, top);
        uvs.push(u0, bottom, u1, top, u1, bottom, u0, bottom, u0, top, u1, top);
      }
    }
  }
  if (!positions.length) return { plinths: 0 };
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geometry.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2));
  geometry.computeVertexNormals();
  const mesh = new THREE.Mesh(geometry, materials.brick);
  mesh.name = 'building-plinths';
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  scene.add(mesh);
  return { plinths: rings.size, triangles: positions.length / 9 };
}
