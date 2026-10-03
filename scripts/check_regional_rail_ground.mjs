// Exercise the runtime adjustment path against the generated infrastructure.
import fs from 'node:fs';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import { applyRiverSystem } from '../docs/river-system.js';

const root = fileURLToPath(new URL('../docs/data/', import.meta.url));
const read = (file) => JSON.parse(fs.readFileSync(root + file, 'utf8'));
const system = read('river-system-1900.json'),
  infra = read('infrastructure.json');
assert(system.railwayGroundAdjustments.length > 0);
const expected = structuredClone(infra);
for (const change of system.railwayGroundAdjustments) {
  const rail = expected.railways.find((r) => r.id === change.railwayId);
  assert(change.afterY < rail.formationHeight);
  rail.embankment[change.triangle][change.vertex][1] = change.afterY;
}
const core = read('river-network.json'),
  buffer = fs.readFileSync(root + core.positionFile);
core.positions = new Float32Array(buffer.buffer.slice(buffer.byteOffset, buffer.byteOffset + buffer.byteLength));
const data = { riverSystem: system, infrastructure: infra, riverNetwork: core };
applyRiverSystem(data);
assert.deepEqual(data.infrastructure, expected, 'Other infrastructure changed during runtime fitting');
assert.throws(() => applyRiverSystem(data), /does not match/, 'Stale source geometry was accepted');
console.log(
  'Railway adjustment runtime passed: fitted earth slope, other infrastructure intact, stale geometry rejected.'
);
