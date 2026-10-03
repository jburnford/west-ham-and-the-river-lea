// The shared helper library must behave exactly like the inline copies it replaces.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createRandom } from '../docs/lib/prng.js';
import { sampleVertexGrid, containsPoint } from '../docs/lib/grid.js';
import { signedArea, createTriangleBatcher } from '../docs/lib/geometry.js';
import { gridSample } from '../docs/historic-elevation.js';

// Deterministic and identical to the pasted generator.
const a = createRandom(73),
  b = createRandom(73);
let seed = 73;
const inline = () => {
  seed = (seed * 1664525 + 1013904223) >>> 0;
  return seed / 4294967296;
};
for (let i = 0; i < 1000; i++) {
  const v = a();
  assert.equal(v, b());
  assert.equal(v, inline());
  assert(v >= 0 && v < 1);
}

// Grid sampling agrees with the existing historic-elevation sampler on the real 1900 grid.
const root = new URL('../docs/data/', import.meta.url);
const meta = JSON.parse(readFileSync(new URL('terrain-1900.json', root)));
const values = new Float32Array(readFileSync(new URL(meta.files.scene, root)).buffer.slice(0));
const random = createRandom(11);
for (let i = 0; i < 2000; i++) {
  const x = meta.bounds[0] - 50 + random() * (meta.bounds[2] - meta.bounds[0] + 100);
  const z = meta.bounds[1] - 50 + random() * (meta.bounds[3] - meta.bounds[1] + 100);
  assert.equal(sampleVertexGrid(values, meta, x, z), gridSample(values, meta, x, z));
}
assert(containsPoint(meta, meta.bounds[0], meta.bounds[1]) && !containsPoint(meta, meta.bounds[0] - 1, meta.bounds[1]));
// Exact vertex hits return the stored value.
assert.equal(
  sampleVertexGrid(values, meta, meta.bounds[0] + 10 * meta.step, meta.bounds[1] + 7 * meta.step),
  values[7 * meta.width + 10]
);

// Winding and batching.
assert(
  signedArea([
    [0, 0],
    [1, 0],
    [1, 1],
    [0, 1],
  ]) > 0
);
assert(
  signedArea([
    [0, 0],
    [0, 1],
    [1, 1],
    [1, 0],
  ]) < 0
);
const batcher = createTriangleBatcher();
const m1 = {},
  m2 = {};
batcher.quad(m1, [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]);
batcher.triangle(m2, [0, 0, 0], [1, 0, 0], [0, 0, 1]);
assert.equal(batcher.size, 2);
const built = [];
const fakeTHREE = {
  BufferGeometry: class {
    setAttribute(name, attr) {
      this[name] = attr;
    }
    computeVertexNormals() {}
  },
  Float32BufferAttribute: class {
    constructor(array, size) {
      this.array = array;
      this.size = size;
    }
  },
  Mesh: class {
    constructor(geometry, material) {
      this.geometry = geometry;
      this.material = material;
    }
  },
};
batcher.build(fakeTHREE, { add: (mesh) => built.push(mesh) });
assert.equal(built.length, 2);
assert.equal(built[0].geometry.position.array.length, 18);
assert.equal(built[1].geometry.position.array.length, 9);
console.log(
  'Shared library: PRNG matches inline generator, grid sampler matches historic elevation on 2000 points, winding and batching pass.'
);
