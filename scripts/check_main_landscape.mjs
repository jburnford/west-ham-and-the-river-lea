// Verify the actual main-scene integration against all generated asset dimensions.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { loadHistoricElevation, applyHistoricElevation } from '../docs/historic-elevation.js';
import { loadRiverNetwork } from '../docs/river-network.js';
import { loadRiverSystem, applyRiverSystem } from '../docs/river-system.js';
import { loadMainLandscape, applyMainLandscape } from '../docs/main-landscape.js';
const load = async (url, type = 'json') => {
  const b = readFileSync(new URL('../docs/' + url.replace(/^\.\//, ''), import.meta.url));
  return type === 'json' ? JSON.parse(b) : b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength);
};
globalThis.location = { search: '?terrainEpoch=baseline' };
assert.equal(await loadMainLandscape(load), null);
globalThis.location.search = '?mainLandscape=baseline';
assert.equal(await loadMainLandscape(load), null);
globalThis.location.search = '';
const data = await load('./data/ground-plan.json');
for (const [key, file] of Object.entries({
  terrain: 'river-terrain',
  infrastructure: 'infrastructure',
  factoryBuildings: 'factory-buildings',
  highStreetFrontages: 'high-street-frontages',
  factoryYards: 'factory-yards',
  housingDetail: 'housing-detail',
  stationPlan: 'abbey-station-plan',
}))
  data[key] = await load(`./data/${file}.json`);
data.terrain.levels = new Float32Array(await load('./data/' + data.terrain.heightFile, 'buffer'));
data.riverNetwork = await loadRiverNetwork(load);
data.riverSystem = await loadRiverSystem(load);
data.elevation = await loadHistoricElevation(load, '1900');
applyHistoricElevation(data);
applyRiverSystem(data);
const rails = JSON.stringify(
    data.infrastructure.railways.map((r) => ({ stations: r.stations, route: r.route, bridges: r.bridges }))
  ),
  sewer = JSON.stringify(data.neighbourhood.sewer);
const oldXYZ = data.riverSystem.positions.slice(),
  oldCore = data.terrain.levels.slice();
const properties = new Uint8Array(await load('./data/' + data.terrain.propertyFile, 'buffer'));
const shapes = JSON.stringify(
  data.factoryBuildings.buildings.map((b) => [b.height, b.width, b.depth, b.renderPolygons])
);
const landscape = await loadMainLandscape(load);
applyMainLandscape(data, landscape);
assert(data.mainLandscape.review.active);
assert(data.mainLandscape.review.seatedObjects > 500);
assert.equal(
  JSON.stringify(
    data.infrastructure.railways.map((r) => ({ stations: r.stations, route: r.route, bridges: r.bridges }))
  ),
  rails
);
assert.equal(JSON.stringify(data.neighbourhood.sewer), sewer);
assert.equal(
  JSON.stringify(data.factoryBuildings.buildings.map((b) => [b.height, b.width, b.depth, b.renderPolygons])),
  shapes
);
for (let i = 0; i < oldXYZ.length; i += 3) {
  assert.equal(data.riverSystem.positions[i], oldXYZ[i]);
  assert.equal(data.riverSystem.positions[i + 2], oldXYZ[i + 2]);
}
assert(oldCore.some((y, i) => Math.abs(y - data.terrain.levels[i]) > 0.1));
let mud = 0;
for (let i = 0; i < oldCore.length; i++)
  if (properties[i * 4 + 3] > 200 && properties[i * 4 + 2] < 80) {
    assert(Math.abs(oldCore[i] - data.terrain.levels[i]) < 1e-5);
    mud++;
  }
assert(mud > 10000, 'Exposed tidal mud must retain its existing channel section');
assert.equal(landscape.grids.groundMesh.length, landscape.meta.groundMeshVertices * 3);
assert.equal(landscape.grids.extension.length, data.elevation.grids.extension.length / 3);
for (const p of landscape.meta.probes) {
  const [x, z] = p.scenePosition;
  assert(landscape.weight(x, z) > 0.99);
  assert(Math.abs(landscape.level(x, z) - p.groundSceneY) < 0.15, p.name);
}
const p = landscape.meta.probes;
assert(Math.abs(p[0].groundSceneY - p[1].groundSceneY) < 0.5, 'Pudding–City marsh must not become an isolated mound');
assert(p[0].groundSceneY > p[2].groundSceneY && p[2].groundSceneY > p[3].groundSceneY, 'Regional marsh progression');
assert.equal(landscape.level(1e6, 1e6, 7), 7);
console.log(
  JSON.stringify(
    {
      status: 'PASS',
      seatedObjects: landscape.review.seatedObjects,
      probes: p,
      checks: [
        'default main integration active',
        'baseline opt-outs',
        'native topology',
        'exposed tidal mud preserved',
        'building dimensions',
        'rail grades and bridges',
        'sewer route and height',
        'regional marsh progression',
        'extension dimensions',
        'outer ground unchanged',
      ],
    },
    null,
    2
  )
);
