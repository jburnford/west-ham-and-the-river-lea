import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { selectCulvertCase } from '../docs/culvert-section.js';
const graph = JSON.parse(readFileSync(new URL('../docs/data/drainage-connections-1900.json', import.meta.url)));
const data = graph.culvertSection;
assert.equal(data.defaultCase, 'working');
for (const c of data.cases) {
  assert(c.eastInvertODN > c.westInvertODN);
  assert(Math.abs(c.eastInvertODN - c.westInvertODN - data.lengthMetres * c.eastToWestSlope) < 1e-10);
  // Recompute the minimum roof cover from the road profile, not case flags.
  const covers = data.roadSpan.stations.map(
    (s, i) =>
      data.roadSpan.surfaceODN[i] -
      (c.westInvertODN + s * c.eastToWestSlope + c.heightMetres + data.roofThicknessMetres)
  );
  assert(Math.abs(Math.min(...covers) - c.minimumRoadCoverMetres) < 1e-10);
  assert.equal(c.fitsCoverAssumption, Math.min(...covers) >= data.minimumCoverMetres);
  assert.equal(c.capacityM3s, null);
  assert.equal(c.hydraulicallyEnabled, false);
  assert.equal(selectCulvertCase(data, c.id).hydraulicReady, false);
  assert.equal(c.approachRegradingRequired, c.inletLoweringMetres > 0);
}
const get = (id) => selectCulvertCase(data, id);
assert(get('working').fitsCoverAssumption);
assert(!get('large-shallow').fitsCoverAssumption);
assert(get('large-deep').fitsCoverAssumption && get('large-deep').approachRegradingRequired);
assert(Math.abs(get('large-deep').eastInvertODN - get('working').eastInvertODN + 0.3) < 1e-10);
assert(Math.abs(get('large-deep').minimumRoadCoverMetres - get('working').minimumRoadCoverMetres) < 1e-10);
for (const epoch of ['1850', '1888', '1897', '1904', '1928'])
  assert.throws(() => selectCulvertCase(data, 'working', epoch), /period evidence/);
assert.throws(() => selectCulvertCase(data, 'missing'), /Unknown/);
const r = data.railwayHeightReview;
assert(r.constantFormationConflictsWithRoadBridge && r.formationAboveDeckMetres > 1.3);
// The OS level profile (data/maps/railway-levels.json) that replaced the constant formation passes under the bridge.
assert(!r.profileConflictsWithRoadBridge && r.profileFormationBelowDeckMetres > 3);
assert(r.distanceFromDrainCrossingMetres > 270 && r.distanceFromDrainCrossingMetres < 285);
assert.equal(r.calibratedFloodBarrier, false);
// Scenarios must not replace unobserved inverts or enable the hydraulic graph.
assert(graph.edges.every((e) => e.invertODNMetres === null && e.capacityM3s === null));
assert.equal(graph.hydraulicReady, false);
console.log(
  'PASS: section grade, independent cover calculation, oversized opening rejection, deeper approach requirement, railway bridge conflict and epoch isolation.'
);
