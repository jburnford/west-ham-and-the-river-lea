// The baked yard atlas images match their sources: rerun scripts/bake_yard_atlas.py after editing
// factory-yards.json or docs/factory-yards.js, or the page shows yards painted from older data.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';

const root = new URL('../', import.meta.url);
const read = (path) => readFileSync(new URL(path, root));
const sha = (bytes) => createHash('sha256').update(bytes).digest('hex').slice(0, 16);

const meta = JSON.parse(read('docs/data/factory-yards-atlas.json'));
for (const [path, hash] of Object.entries(meta.sources))
  assert.equal(hash, sha(read(`docs/${path}`)), `Stale yard atlas (${path} changed): rerun scripts/bake_yard_atlas.py`);
for (const size of [4096, 2048]) {
  const image = read(`docs/data/factory-yards-atlas-${size}.webp`);
  assert.equal(image.toString('latin1', 0, 4), 'RIFF');
  assert.equal(image.toString('latin1', 8, 12), 'WEBP');
  assert.equal(sha(image), meta.images[size].sha256, `factory-yards-atlas-${size}.webp is not the baked image`);
}
console.log(`Yard atlas: 4096 and 2048 px images current for ${Object.keys(meta.sources).length} sources.`);
