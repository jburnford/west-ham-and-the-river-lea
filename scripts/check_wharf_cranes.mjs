// Wharf and yard cranes: register and built file agree, every crane stands on open ground near
// its OS symbol, wharf cranes face drawn water, and the page module builds them.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import * as THREE from 'three';
import { wharfCranes, craneParts } from '../docs/wharf-cranes.js';

const root = new URL('../', import.meta.url);
const read = (path) => readFileSync(new URL(path, root));
const json = (path) => JSON.parse(read(path));
const sha = (path) => createHash('sha256').update(read(path)).digest('hex');

const built = json('docs/data/wharf-cranes.json');
const register = json('data/maps/os-cranes.json');
assert.equal(
  built.registerSha256,
  sha('data/maps/os-cranes.json'),
  'Stale wharf-cranes.json: rerun scripts/build_wharf_cranes.py'
);
for (const [path, hash] of Object.entries(built.inputHashes)) assert.equal(hash, sha(path), `Stale source ${path}`);
assert.equal(built.cranes.length, register.cranes.length);

// Even-odd point-in-polygon on [x, z] rings.
const inside = (rings, x, z) => {
  let c = false;
  for (const ring of rings)
    for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
      const [xi, zi] = ring[i],
        [xj, zj] = ring[j];
      if (zi > z !== zj > z && x < ((xj - xi) * (z - zi)) / (zj - zi) + xi) c = !c;
    }
  return c;
};
const water = [
  ...json('docs/data/ground-plan.json').rivers.flatMap((r) => r.polygons),
  ...json('docs/data/river-system-1900.json').reaches.flatMap((r) => r.polygons || []),
];
const buildings = json('docs/data/factory-buildings.json').buildings.map((b) => [b.footprint]);

for (const crane of built.cranes) {
  const source = register.cranes.find((c) => c.id === crane.id);
  assert.ok(source, crane.id);
  const offset = Math.hypot(crane.x - source.x, crane.z - source.z);
  assert.ok(
    offset <= 3 && Math.abs(offset - crane.movedMetres) < 0.01,
    `${crane.id}: placed ${offset.toFixed(2)} m from its OS dot`
  );
  assert.ok(!water.some((p) => inside(p, crane.x, crane.z)), `${crane.id}: post in drawn water`);
  assert.ok(!buildings.some((p) => inside(p, crane.x, crane.z)), `${crane.id}: post inside a modelled building`);
  const h = (crane.headingDegrees * Math.PI) / 180,
    tip = [crane.x + built.form.jibReach * Math.cos(h), crane.z + built.form.jibReach * Math.sin(h)];
  assert.ok(!buildings.some((p) => inside(p, ...tip)), `${crane.id}: jib tip inside a modelled building`);
  if (crane.setting === 'wharf')
    assert.ok(
      crane.distanceToTargetMetres < 8,
      `${crane.id}: wharf crane ${crane.distanceToTargetMetres} m from water`
    );
  assert.ok(crane.positionEvidence && crane.headingEvidence);
}

// The jib rises from the post to a tip beyond the base, above the post top's tie anchorage height.
const parts = craneParts(built.form);
const jib = parts[2];
assert.ok(jib.b[0] > built.form.baseSize && jib.b[1] > jib.a[1]);

// Module builds one merged mesh per material, all at the given ground level.
const scene = new THREE.Scene();
const material = new THREE.MeshBasicMaterial();
const result = wharfCranes({
  THREE,
  scene,
  data: { wharfCranes: built },
  level: () => 2,
  materials: { stone: material, iron: material, wood: material },
});
assert.equal(result.cranes, built.cranes.length);
const meshes = [];
scene.traverse((o) => o.isMesh && meshes.push(o));
assert.equal(meshes.length, 3, 'one merged mesh per material');
const bounds = new THREE.Box3();
meshes.forEach((m) => bounds.expandByObject(m));
assert.ok(Math.abs(bounds.min.y - 2) < 1e-6, 'crane bases sit on the ground level');
console.log(
  `Wharf cranes: ${built.cranes.length} on open ground at their OS symbols (${built.cranes.filter((c) => c.movedMetres).length} set back from the drawn water), ${built.deferred.length} deferred; module builds ${meshes.length} meshes.`
);
