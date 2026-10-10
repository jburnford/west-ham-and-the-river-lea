// Lite (phone) river network: the simplified copy was built from the current network and landscape heights, and the
// page loader reads it with consistent dimensions. Rebuild with scripts/build_lite_meshes.py, then the scene manifest.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { loadRiverNetwork } from '../docs/river-network.js';

const data = new URL('../docs/data/', import.meta.url);
const read = (name) => readFileSync(new URL(name, data));
const sha = (name) => createHash('sha256').update(read(name)).digest('hex');

const lite = JSON.parse(read('river-network-lite.json'));
for (const [name, hash] of Object.entries(lite.inputHashes))
  assert.equal(hash, sha(name), `Stale river-network-lite.json: ${name} changed; rerun scripts/build_lite_meshes.py`);

const load = async (url, type = 'json') => {
  const b = readFileSync(new URL(url.replace(/^\.\/data\//, ''), data));
  return type === 'json' ? JSON.parse(b) : b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength);
};
const network = await loadRiverNetwork(load, { lite: true });
const mesh = network.liteMesh;
assert.equal(network.vertices, lite.sourceVertices);
assert.equal(network.triangles, lite.sourceTriangles);
assert.ok(lite.triangles < lite.sourceTriangles / 2, 'Lite network is not simplified');
let maxIndex = 0;
for (const i of mesh.indices) if (i > maxIndex) maxIndex = i;
assert.ok(maxIndex < mesh.vertices, 'Lite index out of range');
// Borders are preserved, so the drawn extent must match the full network's.
const extent = (p) => {
  const e = [Infinity, -Infinity, Infinity, -Infinity];
  for (let i = 0; i < p.length; i += 3) {
    e[0] = Math.min(e[0], p[i]);
    e[1] = Math.max(e[1], p[i]);
    e[2] = Math.min(e[2], p[i + 2]);
    e[3] = Math.max(e[3], p[i + 2]);
  }
  return e;
};
const full = extent(network.positions),
  drawn = extent(mesh.positions);
for (let k = 0; k < 4; k++) assert.ok(Math.abs(full[k] - drawn[k]) < 1e-3, 'Lite network extent differs');
console.log(
  `River network lite: current with ${Object.keys(lite.inputHashes).length} inputs; ` +
    `${lite.sourceTriangles.toLocaleString('en')} -> ${lite.triangles.toLocaleString('en')} triangles, same extent.`
);
