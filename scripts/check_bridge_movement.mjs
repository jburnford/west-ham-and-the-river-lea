import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createBridgeWalker} from '../docs/bridge-movement.js';

const data=JSON.parse(readFileSync(new URL('../docs/data/ground-plan.json',import.meta.url)));
const walker=createBridgeWalker(data.neighbourhood.sewer),start=walker.world();
const crest=data.neighbourhood.sewer.crest[0][0];
function inside([x,z]) {
  let hit=false;
  for(let i=0,j=crest.length-1;i<crest.length;j=i++) {
    const [ax,az]=crest[i],[bx,bz]=crest[j];
    if((az>z)!==(bz>z) && x<(bx-ax)*(z-az)/(bz-az)+ax) hit=!hit;
  }
  return hit;
}
// Verify all corners of the permitted rectangle lie within the actual generated walkway.
for(const p of walker.corners()) {
  for(let a=0;a<Math.PI*2;a+=Math.PI/4) {
    assert(inside([p[0]+.5*Math.cos(a),p[1]+.5*Math.sin(a)]),'Walking rectangle must clear the crest edge by half a metre');
  }
}
for(let i=0;i<2000;i++) {
  walker.move(Math.sin(i*2.31)*10000,Math.cos(i*1.79)*10000);
  const p=walker.snapshot(),world=walker.world();
  assert(Math.abs(p.along)<=p.limits.along && Math.abs(p.across)<=p.limits.across);
  assert.equal(world[1],9);assert(inside([world[0],world[2]]));
}
walker.reset();walker.move(10,0);const along=walker.snapshot().along;
walker.side('north');assert.equal(walker.snapshot().along,along);assert.equal(walker.snapshot().across,-5.5);
const north=walker.world();walker.side('south');
assert(Math.abs(Math.hypot(walker.world()[0]-north[0],walker.world()[2]-north[2])-11)<1e-9);
walker.reset();assert.deepEqual(walker.world(),start);
console.log('Bridge movement checks passed: bounded rectangle, actual deck containment, both sides, fixed eye height and reset.');
