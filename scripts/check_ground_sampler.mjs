// The drawn-ground sampler must return the visible surface: at every mesh vertex it must be at least
// that vertex's height, and it must be fast enough to build at page load.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createGroundSampler } from '../docs/lib/ground-sampler.js';
import { createRandom } from '../docs/lib/prng.js';
const root = new URL('../docs/data/', import.meta.url);
const f32 = (name) => new Float32Array(readFileSync(new URL(name, root)).buffer.slice(0));
const u32 = (name) => new Uint32Array(readFileSync(new URL(name, root)).buffer.slice(0));
const landscape = JSON.parse(readFileSync(new URL('main-landscape-1900.json', root)));
const network = JSON.parse(readFileSync(new URL('river-network.json', root)));
const extension = f32('terrain-1900.extension.f32');
const extensionHeights = f32(landscape.files.extension);
for (let i = 0; i < extensionHeights.length; i++) extension[i * 3 + 1] = extensionHeights[i];
const ground = f32(landscape.files.groundMesh);
const positions = f32(network.positionFile),
  indices = u32(network.indexFile);
const heights = f32(landscape.files.network);
for (let i = 0; i < heights.length; i++) positions[i * 3 + 1] = heights[i];
const started = performance.now();
const sampler = createGroundSampler([{ positions: extension }, { positions: ground }, { positions, indices }]);
const buildMs = performance.now() - started;
assert(sampler.triangles > 1_000_000, sampler.triangles);
assert(buildMs < 15000, `build took ${buildMs} ms`);
const random = createRandom(5);
let checked = 0,
  misses = 0;
for (const [p, count] of [
  [extension, extension.length / 3],
  [ground, ground.length / 3],
  [positions, positions.length / 3],
]) {
  for (let k = 0; k < 2000; k++) {
    const v = Math.floor(random() * count),
      x = p[v * 3],
      y = p[v * 3 + 1],
      z = p[v * 3 + 2];
    const s = sampler.sample(x, z);
    if (s === null) {
      misses++;
      continue;
    }
    assert(s >= y - 1e-3, `sampled ${s} below vertex ${y} at ${x},${z}`);
    checked++;
  }
}
assert(misses < 60, `${misses} vertex positions not covered`);
const t0 = performance.now();
for (let k = 0; k < 20000; k++) sampler.sample(-4500 + random() * 11000, -5800 + random() * 12500);
const perSample = (performance.now() - t0) / 20000;
assert(perSample < 0.05, `${perSample} ms per sample`);
console.log(
  `Ground sampler: ${sampler.triangles.toLocaleString()} triangles indexed in ${buildMs.toFixed(0)} ms; ${checked} vertex checks pass (${misses} uncovered edges); ${(perSample * 1000).toFixed(1)} µs per sample.`
);
