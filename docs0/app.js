import * as THREE from './vendor/three/three.module.js';
import { photoDetails } from './photo-details.js';
import { realism } from './realism.js';
import { lighting } from './lighting.js';
import { infrastructure } from './infrastructure.js';
import { mappedTrees } from './mapped-trees.js';
import { loadTerrain, terrainDetails } from './terrain-details.js';
import { createBridgeWalker } from './bridge-movement.js';

const $ = (selector) => document.querySelector(selector);
const rad = Math.PI / 180;
const state = { yaw: 184, pitch: -11, fov: 56 };
const stops = {
  river: { yaw: 184, pitch: -11, fov: 56, title: 'A river at work',
    text: 'Look south from the crossing. Barges used these waterways to carry supplies to riverside works. The river linked local jobs to the needs of a much larger city.',
    detail: 'The wide 1900 photograph shows exposed riverbed, east-bank works and Bromley’s holders beyond them. Gardens lay south of the pumping station on the western side. Railway routes follow the OS map: one behind the factories, another across the distance north of Bromley gasworks. Garden beds, railway levels and building elevations remain interpretations.',
    source: 'Book figure 4; OS London VIII.32 and VIII.42; author’s identification of the gardens.' },
  pumping: { yaw: 274, pitch: 1, fov: 58, title: 'Where the sewage went',
    text: 'Abbey Mills lifted sewage into London’s higher-level drainage system. You are standing above part of that system: the Northern Outfall Sewer. A public walking route ran over infrastructure carrying the city’s waste.',
    detail: 'The pumping station lies west of this crossing. Its arched windows, steep roofs, dormers and central lantern draw on the modern photograph; its two lost chimneys draw on the period view. Their dimensions and visibility still need to be checked against the maps and period photographs.',
    source: 'Book chapter 3; Historic England listings for Abbey Mills and the sewer bridge.' },
  gas: { yaw: 201, pitch: 0, fov: 43, title: 'Fuel for a growing city',
    text: 'Beyond the bend lay Bromley’s gasworks. Gas holders stored fuel before it reached homes and workplaces. This was one part of an industrial landscape that brought employment and environmental costs close together.',
    detail: 'Seven holder locations now form a group, using a site plan and the listed records. Their two-tier frames represent the earlier arrangement; gas-bell heights are estimates. Nine holders existed historically, so this group remains incomplete. West Ham Gas Works stood in another direction, beyond the houses to the north-west.',
    source: 'Historic England holder listings; Bromley gasworks site plan, figure 2-2.' },
  homes: { yaw: 320, pitch: 0, fov: 58, title: 'Living beside the works',
    text: 'This was a place to live as well as work. Four pairs of houses stood on Abbey Lane, with the West Ham gasworks nearby. Homes, industry and the sewer shared a small area.',
    detail: 'The eight Abbey Lane houses date to 1865. Their positions, surrounding terrace rows and six West Ham gas-holder circles follow OS sheets revised in 1893. Roberts Road, Beck Road and Lucas Road lay beyond the sewer to the north-west; more housing stood across the river on Abbey Road. Mill Meads remained open. The map registration is approximate; heights, household divisions and facade details are interpretations.',
    source: 'OS London VIII.32 and VIII.22, revised 1893, published 1895; Historic England: 116–130 Abbey Lane, listing 1080983.' },
  north: { yaw: 25, pitch: 0, fov: 50, title: 'Streets beyond the railway',
    text: 'Look north and north-east. Long rows of houses spread beyond the railway goods yard, with more streets east of Abbey Road. Industry stood beside a densely inhabited neighbourhood.',
    detail: 'The northern housing follows rows on OS sheet VIII.22 and the adjoining area shown in the supplied map mosaic. The railway yard separates groups of streets; Abbey Marsh remains open farther east. These are simplified building-row envelopes, with estimated heights and facade divisions. Distant buildings overlap from this low viewpoint, so the location map shows their arrangement more clearly.',
    source: 'OS London VIII.22 and the author-supplied OS map mosaic. Approximate registration; interpreted building elevations.' },
  mill: { yaw: 346, pitch: -2, fov: 55, title: 'An older working river',
    text: 'Just north of the crossing stood Abbey Mill, labelled as a corn mill on the OS map. Milling was part of the river’s working history long before the pumping station and gasworks.',
    detail: 'The book’s mill illustration dates to about 1800. Its windmill is not evidence of a surviving windmill a century later, so this scene shows only a provisional mill building at the mapped site.',
    source: 'OS London VIII.32: Abbey Mill (Corn); book figure 1, c1800.' }
};

let renderer, scene, camera, data, cone, walker, cameraMarker, cameraLabel, surfaces;
const host = $('#panorama');
const story = $('#story');
function selectStop(id) {
  stopWalking();
  const stop = stops[id];
  Object.assign(state, { yaw: stop.yaw, pitch: stop.pitch, fov: stop.fov });
  document.querySelectorAll('[data-stop]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.stop === id)));
  story.innerHTML = `<h2>${stop.title}</h2><p>${stop.text}</p><details><summary>Look a little deeper</summary><p>${stop.detail}</p></details><p class="source">${stop.source}</p>`;
  update();
}
document.querySelectorAll('[data-stop]').forEach(b => b.addEventListener('click', () => selectStop(b.dataset.stop)));
function resetView() { walker?.reset();selectStop('river'); }
$('#reset').addEventListener('click', resetView);
$('#zoom-in').addEventListener('click', () => { state.fov = Math.max(30, state.fov - 8); update(); });
$('#zoom-out').addEventListener('click', () => { state.fov = Math.min(90, state.fov + 8); update(); });
for (const name of ['map', 'evidence']) {
  const dialog = $(`#${name}-dialog`);
  $(`#${name}-open`).addEventListener('click', () => {stopWalking();dialog.showModal();});
  dialog.querySelector('[data-close]').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', e => { if (e.target === dialog) {
    const r = dialog.getBoundingClientRect();
    if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) dialog.close();
  }});
}
let drag;
const held=new Set();
const walkingKeys={KeyW:'forward',KeyA:'left',KeyS:'back',KeyD:'right'};
let walkFrame=0,lastWalkTime=0;
function moveStep(distance) {
  if(!walker || !renderer || !held.size) return;
  const forward=Number(held.has('forward'))-Number(held.has('back'));
  const right=Number(held.has('right'))-Number(held.has('left'));
  const magnitude=Math.hypot(forward,right);
  if(!magnitude) return;
  const before=walker.world(),yaw=state.yaw*rad;
  walker.move((Math.sin(yaw)*forward+Math.cos(yaw)*right)*distance/magnitude,
              (-Math.cos(yaw)*forward+Math.sin(yaw)*right)*distance/magnitude);
  if(walker.world().some((v,i)=>v!==before[i])) update();
}
function walkTick(time) {
  walkFrame=0;
  if(!held.size || !renderer) return;
  moveStep(Math.min((time-lastWalkTime)/1000,.05)*3);
  lastWalkTime=time;walkFrame=requestAnimationFrame(walkTick);
}
function startWalking(direction) {
  if(!renderer || held.has(direction)) return;
  held.add(direction);moveStep(.5);
  document.querySelector(`[data-walk="${direction}"]`).dataset.active='true';
  if(!walkFrame) {lastWalkTime=performance.now();walkFrame=requestAnimationFrame(walkTick);}
}
function stopWalking(direction) {
  if(direction) held.delete(direction);else held.clear();
  document.querySelectorAll('[data-walk]').forEach(b=>b.dataset.active=String(held.has(b.dataset.walk)));
  if(!held.size) {cancelAnimationFrame(walkFrame);walkFrame=0;}
}
document.querySelectorAll('[data-walk]').forEach(button=>{
  button.addEventListener('pointerdown',e=>{
    if(e.button!==0) return;
    e.preventDefault();button.focus({preventScroll:true});button.setPointerCapture(e.pointerId);
    startWalking(button.dataset.walk);
  });
  for(const event of ['pointerup','pointercancel','lostpointercapture']) button.addEventListener(event,()=>stopWalking(button.dataset.walk));
  // Keyboard/screen-reader activation makes one step; pointer activation is handled above.
  button.addEventListener('click',e=>{if(e.detail===0) {startWalking(button.dataset.walk);stopWalking();}});
});
document.querySelectorAll('[data-side]').forEach(button=>button.addEventListener('click',()=>{
  stopWalking();walker?.side(button.dataset.side);update();
}));
window.addEventListener('keyup',e=>{if(walkingKeys[e.code]) stopWalking(walkingKeys[e.code]);});
window.addEventListener('blur',()=>{stopWalking();drag=null;});
document.addEventListener('visibilitychange',()=>{if(document.hidden) stopWalking();});
document.addEventListener('focusin',e=>{if(e.target!==host && !e.target.closest('#bridge-controls')) stopWalking();});
host.addEventListener('blur',()=>stopWalking());
host.addEventListener('pointerdown', e => {
  if (e.button !== 0) return;
  host.focus({ preventScroll: true }); host.setPointerCapture(e.pointerId);
  drag = { id: e.pointerId, x: e.clientX, y: e.clientY };
});
host.addEventListener('pointermove', e => {
  if (!drag || e.pointerId !== drag.id) return;
  state.yaw -= (e.clientX - drag.x) * 0.14;
  state.pitch += (e.clientY - drag.y) * 0.12;
  drag.x = e.clientX; drag.y = e.clientY; update();
});
for (const event of ['pointerup', 'pointercancel', 'lostpointercapture']) host.addEventListener(event, () => { drag = null; });
host.addEventListener('keydown', e => {
  if(e.altKey || e.ctrlKey || e.metaKey) return;
  if(walkingKeys[e.code]) {e.preventDefault();startWalking(walkingKeys[e.code]);return;}
  const actions = { ArrowLeft: () => state.yaw -= 5, ArrowRight: () => state.yaw += 5,
    ArrowUp: () => state.pitch += 4, ArrowDown: () => state.pitch -= 4,
    '+': () => state.fov -= 5, '=': () => state.fov -= 5, '-': () => state.fov += 5,
    Home: resetView };
  if (actions[e.key]) { e.preventDefault(); actions[e.key](); update(); }
});

function update() {
  state.yaw = (state.yaw % 360 + 360) % 360;
  state.pitch = Math.max(-55, Math.min(40, state.pitch));
  state.fov = Math.max(30, Math.min(90, state.fov));
  const directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
  $('#bearing').textContent = `${directions[Math.round(state.yaw / 45) % 8]} · ${Math.round(state.yaw)}°`;
  if (camera && renderer) {
    camera.position.fromArray(walker.world());
    camera.fov = state.fov; camera.updateProjectionMatrix();
    camera.lookAt(camera.position.clone().add(new THREE.Vector3(
      Math.sin(state.yaw * rad) * Math.cos(state.pitch * rad), Math.sin(state.pitch * rad),
      -Math.cos(state.yaw * rad) * Math.cos(state.pitch * rad))));
    surfaces?.reflect(camera);
    renderer.render(scene, camera);
  }
  if (cone) {
    // Three.js FOV is vertical; show the actual horizontal field on the plan.
    const halfAngle = Math.atan(Math.tan(state.fov * rad / 2) * (camera?.aspect || 1.5));
    const a = state.yaw * rad - halfAngle, b = state.yaw * rad + halfAngle, r = 420;
    const [cx,_,cz]=walker.world();
    cone.setAttribute('d', `M${cx},${cz} L${cx+Math.sin(a)*r},${cz-Math.cos(a)*r} A${r},${r} 0 0 1 ${cx+Math.sin(b)*r},${cz-Math.cos(b)*r} Z`);
    cameraMarker.setAttribute('cx',cx);cameraMarker.setAttribute('cy',cz);
    cameraLabel.setAttribute('x',cx+25);cameraLabel.setAttribute('y',cz-22);
  }
  if(walker) {
    const p=walker.snapshot(),side=p.across>2?'South side':p.across<-2?'North side':'Centre';
    $('#walk-position').textContent=`${side} · ${Math.round(Math.abs(p.along))} m from centre`;
    document.querySelectorAll('[data-side]').forEach(b=>b.setAttribute('aria-pressed',String(Math.abs(p.across-(b.dataset.side==='north'?-p.limits.across:p.limits.across))<.01)));
  }
  // A read-only diagnostic aids geographic and interaction checks in the review build.
  window.panoramaReview = { ...state, camera: camera?.position.toArray(), ready: Boolean(renderer),
    movement:walker?.snapshot(),
    reflection:surfaces?.reflectionStats, terrain:data?.terrain?.review, lighting:scene?.userData.lighting,
    infrastructure:scene?.userData.infrastructure,
    mappedTrees:scene?.userData.mappedTrees,
    stationStudy:scene?.userData.stationStudy,
    triangles: renderer?.info.render.triangles, drawCalls: renderer?.info.render.calls };
}

function planPath(polygons) {
  return polygons.map(poly => poly.map(ring => ring.map((p, i) => `${i ? 'L' : 'M'}${p.join(',')}`).join(' ') + 'Z').join(' ')).join(' ');
}
function buildPlan() {
  const ns = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(ns, 'svg');
  svg.setAttribute('viewBox', '-700 -950 1400 1930');
  svg.setAttribute('role', 'img'); svg.setAttribute('aria-label', 'Plan of the crossing, housing to the north-west and north-east, West Ham gasworks to the north-west, Abbey Mills to the west and Bromley gasworks to the south-west.');
  function element(tag, attrs, text) {
    const el = document.createElementNS(ns, tag);
    Object.entries(attrs).forEach(([k,v]) => el.setAttribute(k,v));
    if (text) el.textContent = text;
    svg.append(el); return el;
  }
  data.rivers.forEach(r => element('path', { d: planPath(r.polygons), fill: '#9bb8b7', 'fill-rule': 'evenodd' }));
  data.sites.forEach(s => element('path', { d: planPath(s.polygons), fill: '#c1b49e', stroke: '#a8977d', 'stroke-width': 1, 'fill-rule': 'evenodd' }));
  data.neighbourhood.holders.forEach(h=>element('circle',{cx:h.x,cy:h.z,r:h.radius,fill:'#728c8150',stroke:'#496d61','stroke-width':2}));
  [...data.neighbourhood.houses,...data.neighbourhood.terraces].forEach(h=>element('polygon',{points:h.footprint.map(p=>p.join(',')).join(' '),fill:'#9e6851'}));
  data.neighbourhood.mappedFactories.forEach(h=>element('polygon',{points:h.footprint.map(p=>p.join(',')).join(' '),fill:'#79634e'}));
  element('text',{x:-45,y:-80},'Corn mill');
  data.neighbourhood.garden.beds.forEach(b=>element('rect',{x:b.x-b.width/2,y:b.z-b.depth/2,width:b.width,height:b.depth,fill:'#789069'}));
  data.neighbourhood.railways.forEach(r=>element('polyline',{points:r.route.map(p=>p.join(',')).join(' '),fill:'none',stroke:'#4a4e4c','stroke-width':5,'stroke-dasharray':'10 4'}));
  element('polyline', {points:data.neighbourhood.sewer.route.map(p=>p.join(',')).join(' '), fill:'none', stroke:'#68786c', 'stroke-width':15 });
  element('polygon',{id:'walk-bounds',points:walker.corners().map(p=>p.join(',')).join(' '),fill:'#f5f2e9',stroke:'#ad792f','stroke-width':2});
  cone = element('path', { fill:'#bb8d3540', stroke:'#ad792f', 'stroke-width':2 });
  cameraMarker=element('circle',{id:'camera-marker',cx:0,cy:0,r:8,fill:'#233d3b',stroke:'#f5f2e9','stroke-width':3});
  cameraLabel=element('text',{x:25,y:-22},'You are here');
  for (const [x,z,label,dx,dz] of [[-185,-13,'Abbey Mills',-205,-65],[-311,650,'Bromley gasworks',30,130],[-92,-117,'Abbey Lane houses',30,0],[-230,-320,'West Ham gasworks',-230,-100]]) {
    element('circle',{cx:x,cy:z,r:8,fill:'#233d3b',stroke:'#f5f2e9','stroke-width':3});
    element('text',{x:x+dx,y:z+dz},label);
  }
  element('text',{x:220,y:260},'Channelsea');
  element('text',{x:220,y:292},'& Abbey Creek');
  element('path',{d:'M440,-280 L440,-380 M425,-350 L440,-380 L455,-350',stroke:'#233d3b','stroke-width':4,fill:'none'});
  element('text',{x:430,y:-400},'N');
  element('path',{d:'M230,900 L430,900 M230,890 L230,910 M430,890 L430,910',stroke:'#233d3b','stroke-width':3,fill:'none'});
  element('text',{x:260,y:940},'200 metres');
  $('#plan').append(svg);
}

function buildScene() {
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, powerPreference: 'low-power' });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.75));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(state.fov, 1, 0.15, 3200);
  camera.position.fromArray(walker.world());
  scene.userData.lighting = lighting(THREE, renderer, scene);
  surfaces = realism(THREE, renderer, scene, data);
  const materials = surfaces.materials;
  let seed = 73;
  const random = () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; };
  const groundShape=new THREE.Shape([new THREE.Vector2(-2750,-2750),new THREE.Vector2(2750,-2750),new THREE.Vector2(2750,2750),new THREE.Vector2(-2750,2750)]);
  const [tx0,tz0,tx1,tz1]=data.terrain.bounds;
  groundShape.holes.push(new THREE.Path([[tx0,-tz0],[tx0,-tz1],[tx1,-tz1],[tx1,-tz0]].map(([x,y])=>new THREE.Vector2(x,y))));
  const ground = new THREE.Mesh(new THREE.ShapeGeometry(groundShape), materials.ground);
  ground.rotation.x = -Math.PI/2; ground.position.y=-0.1; scene.add(ground);
  function surface(polygons, material, y) {
    for (const rings of polygons) {
      const shape = new THREE.Shape(rings[0].map(([x,z]) => new THREE.Vector2(x,-z)));
      for (const ring of rings.slice(1)) shape.holes.push(new THREE.Path(ring.map(([x,z]) => new THREE.Vector2(x,-z))));
      const mesh = new THREE.Mesh(new THREE.ShapeGeometry(shape), material);
      mesh.rotation.x = -Math.PI/2; mesh.position.y=y; scene.add(mesh);
    }
  }
  surface(data.terrain.outsideRivers,materials.water,.06);
  surface([[[[tx0,tz0],[tx1,tz0],[tx1,tz1],[tx0,tz1],[tx0,tz0]]]],materials.water,.06);
  surface(data.terrain.outsideSites,materials.plot,.08);
  function box(parent,x,y,z,w,h,d,material) {
    const mesh = new THREE.Mesh(new THREE.BoxGeometry(w,h,d),material); mesh.position.set(x,y+h/2,z); parent.add(mesh); return mesh;
  }
  function cylinder(parent,x,y,z,r1,r2,h,material,segments=16) {
    const mesh = new THREE.Mesh(new THREE.CylinderGeometry(r1,r2,h,segments),material); mesh.position.set(x,y+h/2,z); parent.add(mesh);return mesh;
  }
  function beam(parent,a,b,r,material) {
    const av=new THREE.Vector3(...a),bv=new THREE.Vector3(...b),delta=bv.clone().sub(av);
    const mesh=new THREE.Mesh(new THREE.CylinderGeometry(r,r,delta.length(),6),material);
    mesh.position.copy(av.add(bv).multiplyScalar(0.5)); mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),delta.normalize());parent.add(mesh);
  }
  const terrain=terrainDetails({THREE,scene,materials,data,box,cylinder,beam,random});
  scene.userData.infrastructure=infrastructure({THREE,scene,materials,data,box,level:terrain.level});
  scene.userData.mappedTrees=mappedTrees({THREE,scene,data,level:terrain.level,beam});
  surfaces.weather(terrain.terrainMaterial);
  data.terrain.review={clods:terrain.clodCount,sheds:terrain.sheds,gardenBeds:data.neighbourhood.garden.beds.length,gardenAreaM2:data.neighbourhood.garden.cultivableAreaM2,vegetationTufts:terrain.vegetationCount,rills:data.terrain.rills,pools:data.terrain.pools.length,heightRange:data.terrain.heightRange};
  const detail = photoDetails({ THREE, scene, materials, box, cylinder, beam, random });
  for (const b of data.factoryStudies) detail.factory(b);
  for (const b of data.neighbourhood.mappedFactories) {
    // Orient the long roof axis along the traced range; facade subdivisions are inferred.
    detail.factory({...b,width:b.depth,depth:b.width,rotation:b.rotation-90,mapped:true});
  }
  // One deliberately simple chimney per chosen site. Locations/heights are study assumptions.
  for(const id of [874,875,876,1125,562,965]) {
    const b=data.factoryStudies.find(b=>b.siteId===id) || data.neighbourhood.mappedFactories.find(b=>b.siteId===id);
    if(b) {cylinder(scene,b.x,0.15,b.z,1.5,2.1,36,materials.brick);cylinder(scene,b.x,35,b.z,1.9,1.9,1.4,materials.brick);}
  }
  detail.barge(20,49,-10,true);
  detail.barge(25,73,8,true);
  detail.barge(-26,37,5,false);
  detail.barge(-35,95,-8,true);
  detail.waterfront();
  detail.station();
  detail.mill(data.neighbourhood.mill);
  detail.threeMills();
  data.neighbourhood.holders.forEach(h=>detail.holder(h));
  data.neighbourhood.houses.forEach(h=>detail.houses(h));
  data.neighbourhood.terraces.forEach(h=>detail.terrace(h));
  // Author-supplied southwest context: distant terraces and works around
  // Three Mills/Bromley. Row axes and industrial ranges remain approximate.
  data.southwest.rows.forEach(h=>detail.terrace(h));
  for(const b of data.southwest.industrialRanges) {
    detail.factory({...b,width:b.depth,depth:b.width,rotation:b.rotation-90,mapped:true});
  }
  // Continuous elevated sewer: mapped bends, interpreted bank profile and distant extensions.
  const sewer=data.neighbourhood.sewer;
  surface(sewer.crest,materials.stone,sewer.height);
  const bankGeometry=new THREE.BufferGeometry();
  const sewerBanks=data.infrastructure.sewerBanks;
  bankGeometry.setAttribute('position',new THREE.Float32BufferAttribute(sewerBanks.flat(2),3));
  bankGeometry.setAttribute('uv',new THREE.Float32BufferAttribute(sewerBanks.flat().flatMap(([x,_,z])=>[x/5500,-z/5500]),2));
  bankGeometry.computeVertexNormals();scene.add(new THREE.Mesh(bankGeometry,materials.ground));
  function routeSegment(a,b) {
    const dx=b[0]-a[0],dz=b[1]-a[1],length=Math.hypot(dx,dz);
    const group=new THREE.Group();group.position.set((a[0]+b[0])/2,0,(a[1]+b[1])/2);
    group.rotation.y=-Math.atan2(dz,dx);scene.add(group);return {group,length};
  }
  for(let i=1;i<sewer.route.length;i++) {
    const {group,length}=routeSegment(sewer.route[i-1],sewer.route[i]);
    // Shallow fascia makes the spanning crest legible over channels without blocking them.
    box(group,0,6.9,0,length,.48,15,materials.stone);
  }
  // Join the parapets at bends so walking closer does not reveal gaps between segments.
  const normals=sewer.route.slice(1).map((p,i)=>{
    const a=sewer.route[i],length=Math.hypot(p[0]-a[0],p[1]-a[1]);
    return [-(p[1]-a[1])/length,(p[0]-a[0])/length];
  });
  for(const offset of [-7.3,7.3]) {
    const edge=sewer.route.map((p,i)=>{
      const a=normals[Math.max(0,i-1)],b=normals[Math.min(i,normals.length-1)];
      const n=[a[0]+b[0],a[1]+b[1]],length=Math.hypot(...n);n[0]/=length;n[1]/=length;
      const scale=offset/(n[0]*a[0]+n[1]*a[1]);return [p[0]+n[0]*scale,p[1]+n[1]*scale];
    });
    for(let i=1;i<edge.length;i++) {
      const {group,length}=routeSegment(edge[i-1],edge[i]);
      box(group,0,8.45,0,length,.1,.1,materials.iron);
      for(let x=-length/2;x<length/2;x+=5) box(group,x,7.4,0,.1,1.1,.1,materials.iron);
    }
  }
  // Static scene: combine surfaces by material so detail does not cost a draw call per window.
  scene.updateMatrixWorld(true);
  const batches=new Map(),originals=[];
  scene.traverse(object=>{
    if(!object.isMesh || object.userData.keepIndexed) return;
    originals.push(object);
    const geometry=object.geometry.index?object.geometry.toNonIndexed():object.geometry.clone();
    if(!object.material.userData.preserveUV) surfaces.metricUV(geometry,object.geometry);
    geometry.applyMatrix4(object.matrixWorld);
    const batch=batches.get(object.material)||{position:[],normal:[],uv:[]};
    for(const name of ['position','normal','uv']) {
      const attribute=geometry.getAttribute(name);
      if(attribute) for(const value of attribute.array) batch[name].push(value);
      else for(let i=0;i<geometry.getAttribute('position').count*(name==='uv'?2:3);i++) batch[name].push(0);
    }
    batches.set(object.material,batch);geometry.dispose();
  });
  for(const mesh of originals) {mesh.removeFromParent();mesh.geometry.dispose();}
  for(const [material,batch] of batches) {
    const geometry=new THREE.BufferGeometry();
    for(const name of ['position','normal','uv']) geometry.setAttribute(name,new THREE.Float32BufferAttribute(batch[name],name==='uv'?2:3));
    geometry.computeBoundingSphere();
    surfaces.weather(material);
    const mesh=new THREE.Mesh(geometry,material);
    mesh.castShadow=![materials.ground,materials.water,materials.bed,materials.plot].includes(material);
    mesh.receiveShadow=true;scene.add(mesh);
  }
  $('#loading').remove();host.append(renderer.domElement);
  document.querySelectorAll('[data-walk],[data-side]').forEach(b=>b.disabled=false);
  renderer.domElement.setAttribute('aria-hidden','true');
  renderer.domElement.addEventListener('webglcontextlost',e=>{
    e.preventDefault();stopWalking();renderer=null;
    document.querySelectorAll('[data-walk],[data-side]').forEach(b=>b.disabled=true);
    host.insertAdjacentHTML('beforeend','<p id="loading">The 3D view paused. Reload to restore it. You can still read the stories and open the location map.</p>');update();
  });
  const resize = () => {
    if (!renderer) return;
    const {width,height}=host.getBoundingClientRect();renderer.setSize(width,height,false);camera.aspect=width/height;update();
  };
  new ResizeObserver(resize).observe(host);resize();
}

selectStop('river');
try {
  const response = await fetch('./data/ground-plan.json');
  if(!response.ok) throw new Error('Ground plan unavailable');
  data = await response.json();
  const [terrain,contextResponse,infrastructureResponse,treesResponse]=await Promise.all([loadTerrain(),fetch('./data/southwest-context.json'),fetch('./data/infrastructure.json'),fetch('./data/mapped-trees.json')]);
  if(!treesResponse.ok) throw new Error('Mapped tree data unavailable');
  data.mappedTrees=await treesResponse.json();
  if(!infrastructureResponse.ok) throw new Error('Infrastructure data unavailable');
  data.infrastructure=await infrastructureResponse.json();
  if(!contextResponse.ok) throw new Error('Southwest scene context unavailable');
  data.terrain=terrain;data.southwest=await contextResponse.json();
  walker=createBridgeWalker(data.neighbourhood.sewer);buildPlan();
  try { buildScene(); }
  catch(error) {
    renderer=null;
    $('#loading').textContent='This browser could not open the 3D view. You can still explore the location map and read the stories.';
    console.warn('3D view unavailable:',error.message);
  }
  update();
} catch(error) {
  $('#loading').textContent='The landscape data could not load. Run the site through the local server described in the README, then reload. The stories below are still available.';
  $('#map-open').disabled=true;
  console.warn(error.message);
}
