import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import * as THREE from '../docs/vendor/three/three.module.js';
import {sewerCrossing} from '../docs/sewer-crossing.js';
import {createBridgeWalker} from '../docs/bridge-movement.js';
const load=p=>JSON.parse(readFileSync(new URL('../docs/data/'+p,import.meta.url)));
const sewer=load('ground-plan.json').neighbourhood.sewer;
const crossing=load('infrastructure.json').sewerHighStreet;
function build(heightShift=0,groundShift=0) {
  const scene=new THREE.Scene(),s={...sewer,height:sewer.height+heightShift};
  const material=new THREE.MeshBasicMaterial();
  const report=sewerCrossing({THREE,scene,sewer:s,crossing,level:()=>groundShift,
    materials:{iron:material,brick:material}});
  return {scene,report,walker:createBridgeWalker(s)};
}
const before=build(),raised=build(.8),lowerGround=build(0,-.7);
assert(before.report.bounds.enclosure.count>=2);
assert.equal(before.report.bounds.abutment.count,2);
// Raycast actual enclosure meshes under the walking surface at both channels
// and the centre. A surviving platform alone cannot satisfy this check.
for(const d of [-24,-12,0,12,24]) for(const across of [-5,0,5]) {
  const [x,,z]=before.walker.world(d,across);
  const ray=new THREE.Raycaster(new THREE.Vector3(x,-10,z),new THREE.Vector3(0,1,0));
  const hits=ray.intersectObjects(before.scene.children,true).filter(h=>h.object.name==='enclosure');
  assert(hits.length>0,`Missing sewer below crossing at ${d}, ${across}`);
  assert(hits[0].point.y<sewer.height-2,'Only the platform remains');
  assert(hits[0].point.y>1.1,'Enclosure obstructs illustrative high water');
}
const close=(a,b)=>assert(Math.abs(a-b)<1e-5,`${a} != ${b}`);
for(const face of ['min','max']) close(raised.report.bounds.enclosure[face][1]-before.report.bounds.enclosure[face][1],.8);
close(raised.report.bounds.abutment.max[1]-before.report.bounds.abutment.max[1],.8);
close(raised.report.bounds.abutment.min[1],before.report.bounds.abutment.min[1]);
close(raised.walker.world()[1]-before.walker.world()[1],.8);
close(lowerGround.report.bounds.abutment.min[1]-before.report.bounds.abutment.min[1],-.7);
assert.deepEqual(lowerGround.report.bounds.enclosure,before.report.bounds.enclosure);
close(lowerGround.report.bounds.abutment.max[1],before.report.bounds.abutment.max[1]);
console.log('PASS: actual sewer enclosure spans both channels; deck, walker and support tops track sewer height; foundations track ground independently.');
