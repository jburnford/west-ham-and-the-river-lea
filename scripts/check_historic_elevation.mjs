// Exercise the actual browser loader and sampler against generated assets.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {loadHistoricElevation,applyHistoricElevation,gridSample} from '../docs/historic-elevation.js';
const load=async (url,type='json')=>{
  const bytes=readFileSync(new URL('../docs/'+url.replace(/^\.\//,''),import.meta.url));
  return type==='json'?JSON.parse(bytes):bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength);
};
assert.equal(await loadHistoricElevation(load,'baseline'),null);
for(const year of ['1850','1888','1897','1898','1904','1928'])
  await assert.rejects(()=>loadHistoricElevation(load,year),/needs dated observations/);
const elevation=await loadHistoricElevation(load,'1900');
await assert.rejects(()=>loadHistoricElevation(async (url,type)=>{
  const result=await load(url,type);
  return url.endsWith('drainage-1900.json')?{...result,geometryEpoch:'1928'}:result;
},'1900'),/Drainage\/terrain epoch mismatch/);
assert(elevation.drainage.waterTriangles.length>0);
assert(elevation.drainage.renderedReach.waterSceneY<0,'Drain must not inherit the old flat scene water level');
const terrain=await load('./data/river-terrain.json');
terrain.levels=new Float32Array(await load('./data/'+terrain.heightFile,'buffer'));
const riverNetwork=await load('./data/river-network.json');
riverNetwork.positions=new Float32Array(await load('./data/'+riverNetwork.positionFile,'buffer'));
const originalCore=terrain.levels.slice(),originalNetwork=riverNetwork.positions.slice();
const data={terrain,riverNetwork,elevation};
applyHistoricElevation(data);
assert(elevation.review.coreVerticesChanged>0);
assert(elevation.review.networkVerticesChanged>0);
for(let i=0;i<riverNetwork.positions.length;i+=3){
  assert.equal(riverNetwork.positions[i],originalNetwork[i]);
  assert.equal(riverNetwork.positions[i+2],originalNetwork[i+2]);
  if(!elevation.weight(originalNetwork[i],originalNetwork[i+2]))assert.equal(riverNetwork.positions[i+1],originalNetwork[i+1]);
}
for(let j=0;j<terrain.height;j++)for(let i=0;i<terrain.width;i++){
  const x=terrain.bounds[0]+i*terrain.step,z=terrain.bounds[1]+j*terrain.step,index=j*terrain.width+i;
  if(!elevation.weight(x,z))assert.equal(terrain.levels[index],originalCore[index]);
}
const tiny={bounds:[0,0,1,1],step:1,width:2,height:2};
assert.equal(gridSample(new Float32Array([0,2,4,6]),tiny,.5,.5),3);
assert.equal(gridSample(new Float32Array([0,2,4,6]),tiny,1,1),6);
// Datum conversion is shared; numerical map labels must not set water levels.
assert.equal(riverNetwork.tide.low,.06);
assert.equal(riverNetwork.tide.high,1.1);
console.log(JSON.stringify({status:'PASS',epoch:elevation.review.epoch,
  coreVerticesChanged:elevation.review.coreVerticesChanged,
  networkVerticesChanged:elevation.review.networkVerticesChanged,
  checks:['browser loader','unsupported epoch refusal','baseline comparison mode','sampler edges',
          'horizontal geometry exact','protected and exterior heights exact','tide levels unchanged']},null,2));
