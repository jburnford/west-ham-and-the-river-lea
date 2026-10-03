// Height lookup against the ground meshes that are actually drawn.
//
// Several modules need "the ground here": seating buildings and yard stock,
// placing tufts, closing bridge fills, meeting sewer bank toes. The earlier
// sampler read source grids that the landscape pass no longer draws, so objects
// floated or sank wherever the two disagreed. This builds a uniform-grid index
// over triangle meshes (indexed or plain soups) and returns the highest surface
// under a point, which for terrain is the visible ground.
//
// Positions are flat [x, y, z, ...] Float32Arrays in scene metres.

export function createGroundSampler(meshes, { cellSize = 6 } = {}) {
  // Gather triangles as (source, vertex index triple) without copying positions.
  const sources = meshes.filter((m) => m && m.positions && m.positions.length >= 9);
  let triangleCount = 0;
  for (const m of sources)
    triangleCount += m.indices ? Math.floor(m.indices.length / 3) : Math.floor(m.positions.length / 9);
  const triSource = new Uint8Array(triangleCount);
  const triA = new Uint32Array(triangleCount),
    triB = new Uint32Array(triangleCount),
    triC = new Uint32Array(triangleCount);
  let minX = Infinity,
    minZ = Infinity,
    maxX = -Infinity,
    maxZ = -Infinity,
    t = 0;
  sources.forEach((m, s) => {
    const p = m.positions;
    const n = m.indices ? Math.floor(m.indices.length / 3) : Math.floor(p.length / 9);
    for (let i = 0; i < n; i++) {
      const a = m.indices ? m.indices[i * 3] : i * 3,
        b = m.indices ? m.indices[i * 3 + 1] : i * 3 + 1,
        c = m.indices ? m.indices[i * 3 + 2] : i * 3 + 2;
      triSource[t] = s;
      triA[t] = a;
      triB[t] = b;
      triC[t] = c;
      t++;
      for (const v of [a, b, c]) {
        const x = p[v * 3],
          z = p[v * 3 + 2];
        if (x < minX) minX = x;
        if (x > maxX) maxX = x;
        if (z < minZ) minZ = z;
        if (z > maxZ) maxZ = z;
      }
    }
  });
  if (!triangleCount) return { sample: () => null, triangles: 0, cells: 0 };
  const cols = Math.ceil((maxX - minX) / cellSize) + 1,
    rows = Math.ceil((maxZ - minZ) / cellSize) + 1;
  const cellOf = (x, z) => Math.floor((z - minZ) / cellSize) * cols + Math.floor((x - minX) / cellSize);
  // Two-pass CSR build: count references per cell, prefix-sum, then fill.
  const counts = new Uint32Array(cols * rows + 1);
  const bounds = (i) => {
    const p = sources[triSource[i]].positions;
    const xs = [p[triA[i] * 3], p[triB[i] * 3], p[triC[i] * 3]],
      zs = [p[triA[i] * 3 + 2], p[triB[i] * 3 + 2], p[triC[i] * 3 + 2]];
    return [Math.min(...xs), Math.min(...zs), Math.max(...xs), Math.max(...zs)];
  };
  for (let i = 0; i < triangleCount; i++) {
    const [x0, z0, x1, z1] = bounds(i);
    const c0 = cellOf(x0, z0),
      c1 = cellOf(x1, z1);
    const colSpan = (c1 % cols) - (c0 % cols),
      rowSpan = Math.floor(c1 / cols) - Math.floor(c0 / cols);
    for (let r = 0; r <= rowSpan; r++) for (let c = 0; c <= colSpan; c++) counts[c0 + r * cols + c + 1]++;
  }
  for (let i = 1; i < counts.length; i++) counts[i] += counts[i - 1];
  const refs = new Uint32Array(counts[counts.length - 1]);
  const fill = new Uint32Array(cols * rows);
  for (let i = 0; i < triangleCount; i++) {
    const [x0, z0, x1, z1] = bounds(i);
    const c0 = cellOf(x0, z0),
      c1 = cellOf(x1, z1);
    const colSpan = (c1 % cols) - (c0 % cols),
      rowSpan = Math.floor(c1 / cols) - Math.floor(c0 / cols);
    for (let r = 0; r <= rowSpan; r++)
      for (let c = 0; c <= colSpan; c++) {
        const cell = c0 + r * cols + c;
        refs[counts[cell] + fill[cell]++] = i;
      }
  }
  // Highest drawn surface under (x, z), or null when no triangle covers the point.
  function sample(x, z) {
    if (x < minX || x > maxX || z < minZ || z > maxZ) return null;
    const cell = cellOf(x, z);
    let best = null;
    for (let k = counts[cell]; k < counts[cell + 1]; k++) {
      const i = refs[k],
        p = sources[triSource[i]].positions;
      const ax = p[triA[i] * 3],
        az = p[triA[i] * 3 + 2],
        bx = p[triB[i] * 3],
        bz = p[triB[i] * 3 + 2],
        cx = p[triC[i] * 3],
        cz = p[triC[i] * 3 + 2];
      const det = (bx - ax) * (cz - az) - (cx - ax) * (bz - az);
      if (Math.abs(det) < 1e-9) continue;
      const u = ((x - ax) * (cz - az) - (cx - ax) * (z - az)) / det,
        v = ((bx - ax) * (z - az) - (x - ax) * (bz - az)) / det;
      if (u < -1e-6 || v < -1e-6 || u + v > 1 + 1e-6) continue;
      const y = p[triA[i] * 3 + 1] * (1 - u - v) + p[triB[i] * 3 + 1] * u + p[triC[i] * 3 + 1] * v;
      if (best === null || y > best) best = y;
    }
    return best;
  }
  return { sample, triangles: triangleCount, cells: cols * rows, bounds: [minX, minZ, maxX, maxZ] };
}
