// Measure rendered hulls against drawn water, and verify hatch masks and float modes.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import * as THREE from 'three';
import { coalVessels, vesselPoint, vesselHolds } from '../docs/coal-vessels.js';

const read = (path) => readFileSync(new URL('../' + path, import.meta.url));
const json = (path) => JSON.parse(read(path));
const sha = (path) => createHash('sha256').update(read(path)).digest('hex');
const spec = json('docs/data/coal-traffic.json');
const system = json('docs/data/river-system-1900.json');
const network = json('docs/data/river-network.json');
assert.equal(spec.registerSha256, sha('data/maps/coal-traffic-1900.json'));
assert.equal(spec.waterSystemSha256, sha('docs/data/river-system-1900.json'));
assert.equal(spec.waterNetworkSha256, sha('docs/data/river-network.json'));
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
const water = {
  tidal: [...system.tidalWaterPolygons, ...network.tide.polygons],
  retained: system.waterPolygons,
};
const scene = new THREE.Scene();
const materials = Object.fromEntries(['iron', 'wood', 'coal'].map((k) => [k, new THREE.MeshStandardMaterial()]));
const result = coalVessels({ THREE, scene, spec, materials, tideLow: network.tide.low, waterLevel: system.waterLevel });
assert.equal(result.vessels, 12);
assert.equal(result.collier, 2);
assert.equal(result.transfers, 3);
assert.ok(result.workers >= 15);
assert.ok(result.triangles < 165000, `Fleet too heavy: ${result.triangles} triangles`);
const holds = vesselHolds(spec);
assert.equal(holds.length, 20);
scene.updateMatrixWorld(true);
for (const v of spec.vessels) {
  const group = scene.getObjectByName(v.label);
  assert.ok(group, v.id);
  assert.equal(group.position.y, v.water === 'tidal' ? network.tide.low : system.waterLevel);
  const hull = group.getObjectByName('Hull shell with submerged bilges');
  const p = hull.geometry.attributes.position;
  for (let i = 0; i < p.count; i++) {
    const point = new THREE.Vector3().fromBufferAttribute(p, i).applyMatrix4(hull.matrixWorld);
    assert.ok(
      water[v.water].some((rings) => inside(rings, point.x, point.z)),
      `${v.id}: rendered hull on land`
    );
  }
  assert.ok(p.array.every(Number.isFinite), `${v.id}: nonfinite geometry`);
  group.traverse((o) => {
    if (!o.isMesh && !o.isPoints) return;
    assert.ok(o.geometry.attributes.position.array.every(Number.isFinite), `${v.id}: nonfinite fitting geometry`);
    assert.equal(Boolean(o.material.userData.tidalFloat), v.water === 'tidal', `${v.id}: incorrect float material`);
  });
  const form = spec.forms[v.form];
  for (const h of form.holds) {
    const centre = vesselPoint(v, 0, h.z);
    const mask = holds.find((m) => Math.hypot(m.centre[0] - centre[0], m.centre[1] - centre[1]) < 1e-6);
    assert.ok(mask, `${v.id}: hatch water mask missing`);
    assert.equal(mask.halfWidth * 2, h.width);
    assert.equal(mask.maxZ - mask.minZ, h.length);
    // Transform an off-centre point back the way the water shader does.
    const world = vesselPoint(v, h.width / 3, h.z + h.length / 4);
    const a = (v.heading * Math.PI) / 180,
      dx = world[0] - centre[0],
      dz = world[1] - centre[1];
    assert.ok(Math.abs(Math.cos(a) * dx - Math.sin(a) * dz - h.width / 3) < 1e-6);
    assert.ok(Math.abs(Math.sin(a) * dx + Math.cos(a) * dz - h.length / 4) < 1e-6);
  }
}
const lite = coalVessels({
  THREE,
  scene: new THREE.Scene(),
  spec,
  materials,
  tideLow: -2,
  waterLevel: 0.06,
  lite: true,
});
assert.equal(lite.vessels, result.vessels);
assert.equal(lite.workers, result.workers);
assert.ok(lite.triangles < result.triangles * 0.6, 'Lite must reduce coal/curve geometry while retaining all vessels');
console.log(
  `Coal traffic: ${result.vessels} hulls in drawn water, ${result.workers} workers, ${holds.length} dry hatches; ${result.triangles} full / ${lite.triangles} lite triangles; tidal and retained materials checked.`
);
