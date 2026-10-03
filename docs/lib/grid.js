// Bilinear sampling of regular height grids stored row-major, row 0 at the
// smallest z. Shared by the terrain, elevation and marsh modules so every
// lookup interpolates the same way.

// Sample a grid whose values sit at the vertices (x0 + i*step, z0 + j*step).
// `meta` needs bounds [x0, z0, x1, z1], step, width and height. Coordinates
// outside the grid are clamped to its edge.
export function sampleVertexGrid(values, meta, x, z) {
  const fx = Math.max(0, Math.min(meta.width - 1, (x - meta.bounds[0]) / meta.step));
  const fz = Math.max(0, Math.min(meta.height - 1, (z - meta.bounds[1]) / meta.step));
  const i = Math.min(Math.floor(fx), meta.width - 2),
    j = Math.min(Math.floor(fz), meta.height - 2);
  const u = fx - i,
    v = fz - j;
  const at = (a, b) => values[b * meta.width + a];
  return (at(i, j) * (1 - u) + at(i + 1, j) * u) * (1 - v) + (at(i, j + 1) * (1 - u) + at(i + 1, j + 1) * u) * v;
}

// True when (x, z) lies inside the grid's bounds, inclusive.
export function containsPoint(meta, x, z) {
  return x >= meta.bounds[0] && x <= meta.bounds[2] && z >= meta.bounds[1] && z <= meta.bounds[3];
}
