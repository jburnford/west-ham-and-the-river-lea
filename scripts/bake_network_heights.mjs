// Final river-network vertex positions, composed exactly as the page composes them (app.js: historic elevation,
// then the river system's corrections, then the main landscape's heights), written as little-endian float32 x,y,z.
// Used by build_lite_meshes.py, which simplifies the drawn mesh for the lite (phone) tier.
//   node scripts/bake_network_heights.mjs OUT.f32
import { readFileSync, writeFileSync } from 'node:fs';
import { loadRiverNetwork } from '../docs/river-network.js';
import { loadHistoricElevation, applyHistoricElevation } from '../docs/historic-elevation.js';
import { loadRiverSystem, applyRiverSystem } from '../docs/river-system.js';
import { loadMainLandscape, applyMainLandscape } from '../docs/main-landscape.js';

const out = process.argv[2];
if (!out) throw new Error('usage: node scripts/bake_network_heights.mjs OUT.f32');
const load = async (url, type = 'json') => {
  const b = readFileSync(new URL('../docs/' + url.replace(/^\.\//, ''), import.meta.url));
  return type === 'json' ? JSON.parse(b) : b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength);
};
globalThis.location = { search: '' };

const data = await load('./data/ground-plan.json');
data.terrain = await load('./data/river-terrain.json');
data.terrain.levels = new Float32Array(await load('./data/' + data.terrain.heightFile, 'buffer'));
for (const [key, file] of Object.entries({
  infrastructure: 'infrastructure',
  factoryBuildings: 'factory-buildings',
  highStreetFrontages: 'high-street-frontages',
  factoryYards: 'factory-yards',
  housingDetail: 'housing-detail',
  stationPlan: 'abbey-station-plan',
}))
  data[key] = await load(`./data/${file}.json`);
data.riverNetwork = await loadRiverNetwork(load);
data.elevation = await loadHistoricElevation(load);
applyHistoricElevation(data);
data.riverSystem = await loadRiverSystem(load);
applyRiverSystem(data);
applyMainLandscape(data, await loadMainLandscape(load));
const p = data.riverNetwork.positions;
writeFileSync(out, Buffer.from(p.buffer, p.byteOffset, p.byteLength));
console.log(`river network: ${p.length / 3} vertices baked to ${out}`);
