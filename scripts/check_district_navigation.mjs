import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createDistrictNavigator, districtBounds, districtViews, factoryViews, viewPose } from '../docs/district-navigation.js';
const load = name => JSON.parse(readFileSync(new URL(`../docs/data/${name}.json`, import.meta.url)));
const nav = createDistrictNavigator(load('ground-plan').neighbourhood.sewer);
const start = nav.world();
nav.move(10000, 10000, 10000);
assert.equal(nav.mode, 'bridge');
assert.equal(nav.world()[1], 9);
assert(Math.hypot(nav.world()[0], nav.world()[2]) < 30);
const views = [...districtViews, ...factoryViews(load('factory-buildings'))];
assert.equal(views.length, districtViews.length + load('factory-buildings').sites.length);
for (const view of views) {
  nav.flyTo(view.position);
  assert.deepEqual(nav.world(), view.position, `Destination ${view.name} must fit within the district`);
  const pose = viewPose(nav.world(), view.target);
  assert(Object.values(pose).every(Number.isFinite));
  assert(pose.pitch >= -85 && pose.pitch <= 75);
}
nav.move(1e6, -1e6, 1e6);
assert.deepEqual(nav.world(), [districtBounds.x[1], districtBounds.height[1], districtBounds.z[0]]);
nav.move(-1e6, 1e6, -1e6);
assert.deepEqual(nav.world(), [districtBounds.x[0], districtBounds.height[0], districtBounds.z[1]]);
nav.reset(); assert.equal(nav.mode, 'bridge'); assert.deepEqual(nav.world(), start);
nav.flyTo([-700, 80, 300]); nav.side('north'); assert.equal(nav.mode, 'bridge'); assert.equal(nav.snapshot().across, -5.5);
console.log(`District navigation: ${views.length} destinations, flight bounds, height bounds and bridge return passed.`);
