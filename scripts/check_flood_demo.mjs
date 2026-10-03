import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {FloodModel,makeBed,parameters} from '../docs/flood-solver.js';
const data=JSON.parse(readFileSync(new URL('../docs/data/flood-demo-1900.json',import.meta.url)));
for(const [p,h] of Object.entries(data.inputHashes))assert.equal(createHash('sha256').update(readFileSync(new URL('../'+p,import.meta.url))).digest('hex'),h,`Stale source ${p}`);
assert.equal(data.width*data.height,21600);
assert(data.bed.every(Number.isFinite));assert(data.kind.some(k=>k===0)&&data.kind.some(k=>k===1));
const params=parameters(data),normal=makeBed(data,params),shifted=makeBed(data,{...params,verticalShift:.3});
for(let i=0;i<normal.length;i++)assert(Math.abs(shifted[i]-normal[i]-.3)<1e-10);
for(let i=0;i<normal.length;i++)if(data.roadInfluence[i]===1&&data.channelInfluence[i]===0)
 assert(Math.abs(normal[i]-data.roadHeight[i])<1e-6,'Use paving, not subgrade');
assert(data.railwayHeightReview.inheritedFormationODN>data.railwayHeightReview.deckEstimateODN);
for(const formation of data.railFormationRangeODN)
 assert(data.railwayHeightReview.deckEstimateODN-data.bridgeRoofAllowanceMetres-formation-data.railAboveFormationMetres>3);
const results={};
function run(name,p){
 const m=new FloodModel(data,p);let peakWet=0,maxError=0;
 for(let t=0;t<=3600;t+=60){m.advance(t);const s=m.stats();peakWet=Math.max(peakWet,s.wetAreaM2);maxError=Math.max(maxError,Math.abs(s.massError));}
 const s={...m.stats(),peakWetAreaM2:peakWet,maxMassErrorM3:maxError};
 assert(s.maxMassErrorM3<1e-5);assert(m.h.every(h=>h>=0&&Number.isFinite(h)));
 results[name]={parameters:m.p,...s};console.log(name,JSON.stringify({eastVolume:s.eastVolume,wet:s.wetAreaM2,peakWet,culvertNet:s.culvertNetVolume,error:s.massError}));return s;
}
const open=run('eastern-inflow-open',{peak:1.65}),blocked=run('eastern-inflow-blocked',{peak:1.65,gate:'blocked'});
assert(open.culvertNetVolume>100);assert.equal(blocked.culvertNetVolume,0);
assert(blocked.eastVolume>open.eastVolume+100,'Blocking the drain must retain more eastern water');
const gated=run('western-surge-gated',{preset:'surge',peak:1.45}),reverse=run('western-surge-open',{preset:'surge',peak:1.45,gate:'both'});
assert(gated.culvertNetVolume>=0);assert(reverse.culvertNetVolume<0,'An unrestricted submerged crossing must admit return flow');
const rain=run('rain-pump-off',{preset:'rain',rain:30,gate:'blocked'}),pump=run('rain-pump-on',{preset:'rain',rain:30,gate:'blocked',pump:true});
assert(Math.abs(rain.rainVolume-.03*data.width*data.height*data.cellSizeMetres**2)<1e-5);
assert(pump.pumpVolume>0&&pump.eastVolume<rain.eastVolume,'Test pump should remove eastern water');
const out=new URL('../scenes/channelsea-sewer-panorama/review/',import.meta.url);mkdirSync(out,{recursive:true});
writeFileSync(new URL('flood-demo-numerical-checks.json',out),JSON.stringify({status:'PASS',results,checks:['source hashes','road paving surface','all dependent heights shifted together','rail formation/bridge clearance range','wetting and nonnegative depth','water balance','blocked vs open drainage','surge backflow control','rainfall volume','pump failure comparison'],historicalValidation:'Not calibrated to an historical event'},null,2)+'\n');
console.log('PASS: six full-hour flood experiments and dependent surface checks.');
