import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {roadProfileHeight} from '../docs/road-levels.js';
import {loadHistoricElevation} from '../docs/historic-elevation.js';
const load=async(url,type='json')=>{
  const b=readFileSync(new URL('../docs/'+url.replace(/^\.\//,''),import.meta.url));
  return type==='json'?JSON.parse(b):b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength);
};
const infra=await load('./data/infrastructure.json'),elevation=await loadHistoricElevation(load,'1900');
const p=infra.roads.find(r=>r.elevationProfile).elevationProfile;
for(const c of p.controls) {
  const [x,z]=c.position,h=roadProfileHeight(x,z,p,'1900');
  assert(Math.abs(h-c.heightScene)<1e-6);
  assert(Math.abs(elevation.level(x,z)+.065-h)<.002,'Paving must contact the adjusted ground');
  for(const epoch of [undefined,'baseline','1850','1888','1897','1904','1928'])assert.equal(roadProfileHeight(x,z,p,epoch),null);
}
assert.equal(roadProfileHeight(0,0,p,'1900'),null,'Profile must not reach the sewer');
console.log('PASS: browser road sampler, measured spot heights, ground contact, bounded influence and epoch guards.');
