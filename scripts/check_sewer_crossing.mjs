import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import * as THREE from '../docs/vendor/three/three.module.js';
import { sewerCrossing } from '../docs/sewer-crossing.js';
import { createBridgeWalker } from '../docs/bridge-movement.js';
const load = (p) => JSON.parse(readFileSync(new URL('../docs/data/' + p, import.meta.url)));
const sewer = load('ground-plan.json').neighbourhood.sewer;
const crossing = load('infrastructure.json').sewerHighStreet;
function build(heightShift = 0, groundShift = 0) {
  const scene = new THREE.Scene(),
    s = { ...sewer, height: sewer.height + heightShift };
  const material = new THREE.MeshBasicMaterial();
  const report = sewerCrossing({
    THREE,
    scene,
    sewer: s,
    crossing,
    level: () => groundShift,
    materials: { iron: material, brick: material },
  });
  return { scene, report, walker: createBridgeWalker(s) };
}
const before = build(),
  raised = build(0.8),
  lowerGround = build(0, -0.7);
assert(before.report.bounds.enclosure.count >= 2);
assert.equal(before.report.bounds.abutment.count, 2);
// Raycast actual enclosure meshes under the walking surface at both channels
// and the centre. A surviving platform alone cannot satisfy this check.
for (const d of [-24, -12, 0, 12, 24])
  for (const across of [-5, 0, 5]) {
    const [x, , z] = before.walker.world(d, across);
    const ray = new THREE.Raycaster(new THREE.Vector3(x, -10, z), new THREE.Vector3(0, 1, 0));
    const hits = ray.intersectObjects(before.scene.children, true).filter((h) => h.object.name === 'enclosure');
    assert(hits.length > 0, `Missing sewer below crossing at ${d}, ${across}`);
    assert(hits[0].point.y < sewer.height - 2, 'Only the platform remains');
    assert(hits[0].point.y > 1.1, 'Enclosure obstructs illustrative high water');
  }
const close = (a, b) => assert(Math.abs(a - b) < 1e-5, `${a} != ${b}`);
for (const face of ['min', 'max'])
  close(raised.report.bounds.enclosure[face][1] - before.report.bounds.enclosure[face][1], 0.8);
close(raised.report.bounds.abutment.max[1] - before.report.bounds.abutment.max[1], 0.8);
close(raised.report.bounds.abutment.min[1], before.report.bounds.abutment.min[1]);
close(raised.walker.world()[1] - before.walker.world()[1], 0.8);
close(lowerGround.report.bounds.abutment.min[1] - before.report.bounds.abutment.min[1], -0.7);
assert.deepEqual(lowerGround.report.bounds.enclosure, before.report.bounds.enclosure);
close(lowerGround.report.bounds.abutment.max[1], before.report.bounds.abutment.max[1]);
// Every other water span gets the Channelsea treatment (T1c): an actual trough
// under the deck at mid-span, clear of illustrative high water, on two brick
// abutments, with piers only where the clear span exceeds the Channelsea's.
const waterEnds = sewer.bankEnds.filter((e) => e.kind === 'water');
const spans = before.report.spans;
assert.equal(spans.count, waterEnds.length / 2 - 1, 'A water span other than the Channelsea is missing');
const hitsAt = ([x, z], name, from = -10, dir = 1) =>
  new THREE.Raycaster(new THREE.Vector3(x, from, z), new THREE.Vector3(0, dir, 0))
    .intersectObjects(before.scene.children, true)
    .filter((h) => h.object.name === name);
for (const span of spans.spans) {
  const hits = hitsAt(span.middle, 'enclosure');
  assert(span.troughSegments > 0 && hits.length > 0, `No trough under the deck at chainage ${span.chainage}`);
  assert(hits[0].point.y >= 1.1, `Trough obstructs illustrative high water at chainage ${span.chainage}`);
  assert.equal(span.abutments, 2, `Abutments missing at chainage ${span.chainage}`);
  for (const centre of span.abutmentCentres)
    assert(hitsAt(centre, 'span-support', 50, -1).length > 0, `No abutment at ${centre}`);
  const piers =
    span.clearSpan > spans.referenceClearSpan ? Math.ceil(span.clearSpan / spans.referenceClearSpan) - 1 : 0;
  assert.equal(span.piers, piers, `Pier count at chainage ${span.chainage}`);
}
if (sewer.portal) {
  assert(before.report.portal && before.report.endWalls.kinds.includes('portal'), 'Wick Lane portal missing');
  assert(before.report.portal.top > sewer.height + 1, 'Portal parapet below the walk');
}
console.log(
  `PASS: actual sewer enclosure spans both channels; deck, walker and support tops track sewer height; foundations track ground independently; ${spans.count} further water spans have a trough and abutments${sewer.portal ? '; Wick Lane portal present' : ''}.`
);
