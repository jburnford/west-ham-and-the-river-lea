import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { sewerSurfaceHeight, highStreetSurfaceHeight } from '../docs/sewer-levels.js';
const load = (name) => JSON.parse(readFileSync(new URL(`../${name}`, import.meta.url)));
const infrastructure = load('docs/data/infrastructure.json');
const sewer = load('docs/data/ground-plan.json').neighbourhood.sewer;
const crossing = infrastructure.sewerHighStreet;
const [x, z] = crossing.centre;
assert.equal(sewerSurfaceHeight(x, z, sewer, crossing), highStreetSurfaceHeight(x, z, crossing));
assert.equal(sewerSurfaceHeight(0, 0, sewer, crossing), 7.4, 'Keep the Channelsea reference level');
const distance = (p, a, b) => {
  const dx = b[0] - a[0],
    dz = b[1] - a[1],
    t = Math.max(0, Math.min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dz) / (dx * dx + dz * dz)));
  return Math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dz);
};
const roadDistance = (p) =>
  Math.min(...crossing.roadRoute.slice(1).map((b, i) => distance(p, crossing.roadRoute[i], b)));
for (const edge of infrastructure.sewerRailEdges)
  for (const p of edge) assert(roadDistance(p) > crossing.roadWidth / 2 + 1.2, 'Railing across High Street');
for (const tri of infrastructure.sewerCrestTriangles) {
  const centre = [tri.reduce((s, p) => s + p[0], 0) / 3, tri.reduce((s, p) => s + p[1], 0) / 3];
  assert(roadDistance(centre) > crossing.roadWidth / 2 + 1, 'Walkway overlaps carriageway');
}
for (let d = -220; d < 220; d++) {
  const change = sewerSurfaceHeight(x + d + 1, z, sewer, crossing) - sewerSurfaceHeight(x + d, z, sewer, crossing);
  assert(Math.abs(change) < 0.04, 'Abrupt cover gradient');
}
console.log('Sewer/High Street: crossing levels meet, road clear of walkway and railings, Channelsea datum retained.');
