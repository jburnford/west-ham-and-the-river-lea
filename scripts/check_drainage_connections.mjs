import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {analyseConnections} from '../docs/drainage-connections.js';
const root=new URL('../',import.meta.url),data=JSON.parse(readFileSync(new URL('docs/data/drainage-connections-1900.json',root)));
for(const [path,sha] of Object.entries(data.inputHashes))
  assert.equal(createHash('sha256').update(readFileSync(new URL(path,root))).digest('hex'),sha,`Stale source: ${path}`);
const reachable=(scenario,start)=>analyseConnections(data,scenario,start).reachable;
const east=['east-trace-boundary','manor-east'];
const west=['middle-junction','railway-west','west-junction'];
const connected=[...east,...west].sort();
assert.equal(data.defaultScenario,'east-to-west');
assert.deepEqual(reachable(data.defaultScenario,'manor-east'),connected);
assert.deepEqual(reachable('evidence-only','manor-east'),east);
assert.deepEqual(reachable('evidence-only','west-junction'),['west-junction']);
assert.deepEqual(reachable('crossing-blocked','manor-east'),east);
assert.deepEqual(reachable('crossing-blocked','west-junction'),west);
assert.deepEqual(reachable('east-to-west','manor-east'),connected);
assert.deepEqual(reachable('east-to-west','west-junction'),west);
assert.deepEqual(reachable('west-to-east','manor-east'),east);
assert.deepEqual(reachable('west-to-east','west-junction'),connected);
for(const side of ['manor-east','west-junction'])assert.deepEqual(reachable('both-ways',side),connected);
for(const s of data.scenarios)assert.deepEqual(reachable(s.id,'manor-road-north'),['manor-road-north']);
for(const epoch of ['1850','1888','1897','1904','1928'])assert.throws(()=>analyseConnections(data,'both-ways','manor-east',epoch),/period evidence/);
assert.throws(()=>analyseConnections(data,'invented','manor-east'),/Unknown/);
assert.throws(()=>analyseConnections(data,'both-ways','invented'),/Unknown/);
assert.equal(data.hydraulicReady,false);
assert(data.nodes.every(n=>n.outfallConfirmed===false && n.invertODNMetres===null));
assert(data.edges.every(e=>e.capacityM3s===null && e.invertODNMetres===null));
for(const e of data.edges)for(const [key,p] of [['from',e.route[0]],['to',e.route.at(-1)]]) {
  const node=data.nodes.find(n=>n.id===e[key]);assert(node);
  assert(Math.hypot(p[0]-node.position[0],p[1]-node.position[1])<.001);
}
assert(data.crossingAudit.lengthMetres>40&&data.crossingAudit.lengthMetres<50);
assert.equal(data.crossingAudit.railwayIntersections.length,2);
assert.equal(data.crossingAudit.roadGeometryPresentAtCrossing,true);
assert(data.crossingAudit.nearestModelRoadMetres<.01);
// The rendered 206m section endpoints must not replace the full mapped trace.
assert(data.edges.find(e=>e.id==='east-channel').lengthMetres>data.renderedReach.lengthMetres+90);
console.log('PASS: source hashes, graph endpoints, five scenarios, both one-way directions, isolated sluice, epoch guards and no invented outfall/capacity.');
