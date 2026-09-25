// Interaction layer for the docs2 redesign. Scene construction, materials,
// terrain and infrastructure are Astra's modules, used unchanged.
import * as THREE from './vendor/three/three.module.js';
import { photoDetails } from './photo-details.js';
import { realism } from './realism.js';
import { lighting } from './lighting.js';
import { infrastructure } from './infrastructure.js';
import { mappedTrees } from './mapped-trees.js';
import { loadTerrain, terrainDetails } from './terrain-details.js';
import { createBridgeWalker } from './bridge-movement.js';

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const rad = Math.PI / 180;
const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
// Quality tier. Phones and small tablets get a lighter scene: the full build holds
// several hundred megabytes of geometry, which mobile browsers will not tolerate.
// Override for testing with ?quality=lite or ?quality=full.
const requestedQuality = new URLSearchParams(location.search).get('quality');
const lite = requestedQuality ? requestedQuality === 'lite'
  : (matchMedia('(pointer: coarse)').matches && Math.min(screen.width, screen.height) < 900)
    || (navigator.deviceMemory !== undefined && navigator.deviceMemory <= 4);

// Camera poses. `hero` is the arrival view; the poster frame was rendered at `arrival`.
const poses = {
  arrival: { yaw: 194, pitch: -3, fov: 71 },
  hero: { yaw: 184, pitch: -8, fov: 62 },
  river: { yaw: 184, pitch: -11, fov: 56 },
  pumping: { yaw: 274, pitch: 1, fov: 58 },
  gas: { yaw: 201, pitch: 0, fov: 43 },
  homes: { yaw: 320, pitch: 0, fov: 58 },
  north: { yaw: 25, pitch: 0, fov: 50 },
  mill: { yaw: 346, pitch: -2, fov: 55 },
  explore: null // keeps whatever the reader was looking at
};
const state = { ...poses.arrival };
let activeStop = 'hero', pendingArrival = true;

let renderer, scene, camera, data, walker, surfaces;
const plans = [];
const host = $('#panorama');

/* ---------- Camera tweening ---------- */
let tweenFrame = 0;
const easeInOut = t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
function interruptTween() { if (tweenFrame) { cancelAnimationFrame(tweenFrame); tweenFrame = 0; } }
// Any deliberate look/zoom/walk means the reader is exploring: stop the tween and clear the title.
function userInteracted() { interruptTween(); dismissHero(); }
function goTo(pose, duration = 1500) {
  if (!pose) return;
  interruptTween();
  if (reduceMotion || duration <= 0) { Object.assign(state, pose); update(); return; }
  const from = { ...state };
  const dyaw = ((pose.yaw - from.yaw + 540) % 360) - 180;
  const start = performance.now();
  const frame = (now) => {
    const t = Math.min(1, (now - start) / duration), k = easeInOut(t);
    state.yaw = from.yaw + dyaw * k;
    state.pitch = from.pitch + (pose.pitch - from.pitch) * k;
    state.fov = from.fov + (pose.fov - from.fov) * k;
    // Schedule (or clear) before rendering so the diagnostic sees the final state.
    tweenFrame = t < 1 ? requestAnimationFrame(frame) : 0;
    update();
  };
  tweenFrame = requestAnimationFrame(frame);
}

/* ---------- Scroll narrative ---------- */
const header = $('#site-header'), hero = $('#hero');
function dismissHero() { hero.classList.add('is-dismissed'); }
$('#hero-close').addEventListener('click', dismissHero);
function activate(id) {
  if (id === activeStop) return;
  activeStop = id;
  $$('.step').forEach(s => s.classList.toggle('is-active', s.dataset.stop === id));
  $$('[data-chapter]').forEach(a => { if (a.dataset.chapter === id) a.setAttribute('aria-current', 'true'); else a.removeAttribute('aria-current'); });
  document.body.classList.toggle('is-explore', id === 'explore');
  header.classList.toggle('is-scrolled', id !== 'hero');
  if (!pendingArrival && renderer) goTo(poses[id]); else update();
}
// A step becomes active when it crosses the middle band of the viewport.
const stepObserver = new IntersectionObserver(entries => {
  for (const e of entries) if (e.isIntersecting) activate(e.target.dataset.stop);
}, { rootMargin: '-45% 0px -45% 0px', threshold: 0 });
$$('.step').forEach(step => stepObserver.observe(step));
let scrollTick = false;
function onScroll() {
  if (scrollTick) return; scrollTick = true;
  requestAnimationFrame(() => {
    scrollTick = false;
    const p = Math.min(1, Math.max(0, scrollY / (innerHeight * .45)));
    hero.style.opacity = String(1 - p);
    hero.style.transform = `translateY(${-p * 36}px)`;
    hero.style.visibility = p >= 1 ? 'hidden' : '';
  });
}
addEventListener('scroll', onScroll, { passive: true }); onScroll();

/* ---------- Controls ---------- */
function resetView() { stopWalking(); walker?.reset(); if (activeStop === 'hero') hero.classList.remove('is-dismissed'); goTo(poses[activeStop] || poses.hero, 900); }
$('#reset').addEventListener('click', resetView);
$('#zoom-in').addEventListener('click', () => { userInteracted(); state.fov = Math.max(30, state.fov - 8); update(); });
$('#zoom-out').addEventListener('click', () => { userInteracted(); state.fov = Math.min(90, state.fov + 8); update(); });

const dialog = $('#map-dialog');
for (const id of ['#map-open', '#map-open-2', '#minimap']) $(id).addEventListener('click', () => { stopWalking(); dialog.showModal(); });
dialog.querySelector('[data-close]').addEventListener('click', () => dialog.close());
dialog.addEventListener('click', e => {
  if (e.target !== dialog) return;
  const r = dialog.getBoundingClientRect();
  if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) dialog.close();
});

let drag;
const held = new Set();
const walkingKeys = { KeyW: 'forward', KeyA: 'left', KeyS: 'back', KeyD: 'right' };
let walkFrame = 0, lastWalkTime = 0;
function moveStep(distance) {
  if (!walker || !renderer || !held.size) return;
  const forward = Number(held.has('forward')) - Number(held.has('back'));
  const right = Number(held.has('right')) - Number(held.has('left'));
  const magnitude = Math.hypot(forward, right);
  if (!magnitude) return;
  const before = walker.world(), yaw = state.yaw * rad;
  walker.move((Math.sin(yaw) * forward + Math.cos(yaw) * right) * distance / magnitude,
              (-Math.cos(yaw) * forward + Math.sin(yaw) * right) * distance / magnitude);
  if (walker.world().some((v, i) => v !== before[i])) update();
}
function walkTick(time) {
  walkFrame = 0;
  if (!held.size || !renderer) return;
  moveStep(Math.min((time - lastWalkTime) / 1000, .05) * 3);
  lastWalkTime = time; walkFrame = requestAnimationFrame(walkTick);
}
function startWalking(direction) {
  if (!renderer || held.has(direction)) return;
  userInteracted();
  held.add(direction); moveStep(.5);
  $(`[data-walk="${direction}"]`).dataset.active = 'true';
  if (!walkFrame) { lastWalkTime = performance.now(); walkFrame = requestAnimationFrame(walkTick); }
}
function stopWalking(direction) {
  if (direction) held.delete(direction); else held.clear();
  $$('[data-walk]').forEach(b => b.dataset.active = String(held.has(b.dataset.walk)));
  if (!held.size) { cancelAnimationFrame(walkFrame); walkFrame = 0; }
}
$$('[data-walk]').forEach(button => {
  button.addEventListener('pointerdown', e => {
    if (e.button !== 0) return;
    e.preventDefault(); button.focus({ preventScroll: true }); button.setPointerCapture(e.pointerId);
    startWalking(button.dataset.walk);
  });
  for (const event of ['pointerup', 'pointercancel', 'lostpointercapture']) button.addEventListener(event, () => stopWalking(button.dataset.walk));
  // Keyboard/screen-reader activation makes one step; pointer activation is handled above.
  button.addEventListener('click', e => { if (e.detail === 0) { startWalking(button.dataset.walk); stopWalking(); } });
});
$$('[data-side]').forEach(button => button.addEventListener('click', () => { stopWalking(); walker?.side(button.dataset.side); update(); }));
addEventListener('keyup', e => { if (walkingKeys[e.code]) stopWalking(walkingKeys[e.code]); });
addEventListener('blur', () => { stopWalking(); drag = null; });
document.addEventListener('visibilitychange', () => { if (document.hidden) stopWalking(); });
document.addEventListener('focusin', e => { if (e.target !== host && !e.target.closest('#bridge-controls')) stopWalking(); });
host.addEventListener('blur', () => stopWalking());
host.addEventListener('pointerdown', e => {
  if (e.button !== 0) return;
  host.focus({ preventScroll: true }); host.setPointerCapture(e.pointerId);
  drag = { id: e.pointerId, x: e.clientX, y: e.clientY, touch: e.pointerType === 'touch' };
});
host.addEventListener('pointermove', e => {
  if (!drag || e.pointerId !== drag.id) return;
  if (Math.abs(e.clientX - drag.x) + Math.abs(e.clientY - drag.y) > 2) dismissHero();
  interruptTween();
  state.yaw -= (e.clientX - drag.x) * 0.14;
  // On touch outside explore mode the browser owns vertical movement (page scroll).
  if (!drag.touch || document.body.classList.contains('is-explore')) state.pitch += (e.clientY - drag.y) * 0.12;
  drag.x = e.clientX; drag.y = e.clientY; update();
});
for (const event of ['pointerup', 'pointercancel', 'lostpointercapture']) host.addEventListener(event, () => { drag = null; });
host.addEventListener('keydown', e => {
  if (e.altKey || e.ctrlKey || e.metaKey) return;
  if (walkingKeys[e.code]) { e.preventDefault(); startWalking(walkingKeys[e.code]); return; }
  const actions = { ArrowLeft: () => state.yaw -= 5, ArrowRight: () => state.yaw += 5,
    ArrowUp: () => state.pitch += 4, ArrowDown: () => state.pitch -= 4,
    '+': () => state.fov -= 5, '=': () => state.fov -= 5, '-': () => state.fov += 5,
    Home: resetView };
  if (actions[e.key]) { e.preventDefault(); if (e.key !== 'Home') userInteracted(); else interruptTween(); actions[e.key](); update(); }
});

/* ---------- Render + readouts ---------- */
const rose = $('#rose'), bearing = $('#bearing');
function update() {
  state.yaw = (state.yaw % 360 + 360) % 360;
  state.pitch = Math.max(-55, Math.min(40, state.pitch));
  state.fov = Math.max(30, Math.min(90, state.fov));
  const directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
  bearing.textContent = `${directions[Math.round(state.yaw / 45) % 8]} · ${Math.round(state.yaw)}°`;
  rose.style.transform = `rotate(${-state.yaw}deg)`;
  if (camera && renderer) {
    camera.position.fromArray(walker.world());
    camera.fov = state.fov; camera.updateProjectionMatrix();
    camera.lookAt(camera.position.clone().add(new THREE.Vector3(
      Math.sin(state.yaw * rad) * Math.cos(state.pitch * rad), Math.sin(state.pitch * rad),
      -Math.cos(state.yaw * rad) * Math.cos(state.pitch * rad))));
    surfaces?.reflect(camera);
    renderer.render(scene, camera);
  }
  if (walker && plans.length) {
    // Three.js FOV is vertical; show the actual horizontal field on the plan.
    const halfAngle = Math.atan(Math.tan(state.fov * rad / 2) * (camera?.aspect || 1.5));
    const a = state.yaw * rad - halfAngle, b = state.yaw * rad + halfAngle, r = 420;
    const [cx, _, cz] = walker.world();
    for (const plan of plans) {
      plan.cone.setAttribute('d', `M${cx},${cz} L${cx + Math.sin(a) * r},${cz - Math.cos(a) * r} A${r},${r} 0 0 1 ${cx + Math.sin(b) * r},${cz - Math.cos(b) * r} Z`);
      plan.marker.setAttribute('cx', cx); plan.marker.setAttribute('cy', cz);
      plan.label?.setAttribute('x', cx + 25); plan.label?.setAttribute('y', cz - 22);
    }
    const p = walker.snapshot(), side = p.across > 2 ? 'South side' : p.across < -2 ? 'North side' : 'Centre';
    $('#walk-position').textContent = `${side} · ${Math.round(Math.abs(p.along))} m from centre`;
    $$('[data-side]').forEach(b => b.setAttribute('aria-pressed', String(Math.abs(p.across - (b.dataset.side === 'north' ? -p.limits.across : p.limits.across)) < .01)));
  }
  // Read-only diagnostic for browser checks (same shape as the docs/ build, plus narrative state).
  window.panoramaReview = { ...state, camera: camera?.position.toArray(), ready: Boolean(renderer), quality: lite ? 'lite' : 'full',
    activeStop, tweening: Boolean(tweenFrame), movement: walker?.snapshot(),
    reflection: surfaces?.reflectionStats, terrain: data?.terrain?.review, lighting: scene?.userData.lighting,
    infrastructure: scene?.userData.infrastructure, mappedTrees: scene?.userData.mappedTrees,
    stationStudy: scene?.userData.stationStudy,
    triangles: renderer?.info.render.triangles, drawCalls: renderer?.info.render.calls };
}

/* ---------- Plans (dialog map + HUD inset) ---------- */
function planPath(polygons) {
  return polygons.map(poly => poly.map(ring => ring.map((p, i) => `${i ? 'L' : 'M'}${p.join(',')}`).join(' ') + 'Z').join(' ')).join(' ');
}
function buildPlan(container, { viewBox, labels = true, markerRadius = 8, strokeScale = 1 }) {
  const ns = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(ns, 'svg');
  svg.setAttribute('viewBox', viewBox);
  svg.setAttribute('role', 'img'); svg.setAttribute('aria-label', 'Plan of the crossing, housing to the north-west and north-east, West Ham gasworks to the north-west, Abbey Mills to the west and Bromley gasworks to the south-west.');
  function element(tag, attrs, text) {
    const el = document.createElementNS(ns, tag);
    Object.entries(attrs).forEach(([k, v]) => el.setAttribute(k, v));
    if (text) el.textContent = text;
    svg.append(el); return el;
  }
  data.rivers.forEach(r => element('path', { d: planPath(r.polygons), fill: '#9bb8b7', 'fill-rule': 'evenodd' }));
  data.sites.forEach(s => element('path', { d: planPath(s.polygons), fill: '#c1b49e', stroke: '#a8977d', 'stroke-width': strokeScale, 'fill-rule': 'evenodd' }));
  data.neighbourhood.holders.forEach(h => element('circle', { cx: h.x, cy: h.z, r: h.radius, fill: '#728c8150', stroke: '#496d61', 'stroke-width': 2 * strokeScale }));
  [...data.neighbourhood.houses, ...data.neighbourhood.terraces].forEach(h => element('polygon', { points: h.footprint.map(p => p.join(',')).join(' '), fill: '#9e6851' }));
  data.neighbourhood.mappedFactories.forEach(h => element('polygon', { points: h.footprint.map(p => p.join(',')).join(' '), fill: '#79634e' }));
  data.neighbourhood.garden.beds.forEach(b => element('rect', { x: b.x - b.width / 2, y: b.z - b.depth / 2, width: b.width, height: b.depth, fill: '#789069' }));
  data.neighbourhood.railways.forEach(r => element('polyline', { points: r.route.map(p => p.join(',')).join(' '), fill: 'none', stroke: '#4a4e4c', 'stroke-width': 5 * strokeScale, 'stroke-dasharray': `${10 * strokeScale} ${4 * strokeScale}` }));
  element('polyline', { points: data.neighbourhood.sewer.route.map(p => p.join(',')).join(' '), fill: 'none', stroke: '#68786c', 'stroke-width': 15 });
  element('polygon', { points: walker.corners().map(p => p.join(',')).join(' '), fill: '#f5f2e9', stroke: '#ad792f', 'stroke-width': 2 * strokeScale });
  const cone = element('path', { fill: '#bb8d3540', stroke: '#ad792f', 'stroke-width': 2 * strokeScale });
  const marker = element('circle', { cx: 0, cy: 0, r: markerRadius, fill: '#233d3b', stroke: '#f5f2e9', 'stroke-width': 3 * strokeScale });
  let label;
  if (labels) {
    element('text', { x: -45, y: -80 }, 'Corn mill');
    label = element('text', { x: 25, y: -22 }, 'You are here');
    for (const [x, z, name, dx, dz] of [[-185, -13, 'Abbey Mills', -205, -65], [-311, 650, 'Bromley gasworks', 30, 130], [-92, -117, 'Abbey Lane houses', 30, 0], [-230, -320, 'West Ham gasworks', -230, -100]]) {
      element('circle', { cx: x, cy: z, r: 8, fill: '#233d3b', stroke: '#f5f2e9', 'stroke-width': 3 });
      element('text', { x: x + dx, y: z + dz }, name);
    }
    element('text', { x: 220, y: 260 }, 'Channelsea');
    element('text', { x: 220, y: 292 }, '& Abbey Creek');
    element('path', { d: 'M440,-280 L440,-380 M425,-350 L440,-380 L455,-350', stroke: '#233d3b', 'stroke-width': 4, fill: 'none' });
    element('text', { x: 430, y: -400 }, 'N');
    element('path', { d: 'M230,900 L430,900 M230,890 L230,910 M430,890 L430,910', stroke: '#233d3b', 'stroke-width': 3, fill: 'none' });
    element('text', { x: 260, y: 940 }, '200 metres');
  }
  container.append(svg);
  plans.push({ cone, marker, label });
}

/* ---------- Scene (unchanged construction from docs/app.js) ---------- */
function buildScene() {
  if (lite) data.terrain = downsampleTerrain(data.terrain, 2);
  renderer = new THREE.WebGLRenderer({ antialias: !lite, alpha: false, powerPreference: 'low-power' });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, lite ? 1 : 1.75));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(state.fov, 1, 0.15, 3200);
  camera.position.fromArray(walker.world());
  scene.userData.lighting = lighting(THREE, renderer, scene, lite ? { shadowMapSize: 1024, softShadows: false } : {});
  surfaces = realism(THREE, renderer, scene, data, lite ? { reflectionWidth: 256, reflectionHeight: 192 } : {});
  const materials = surfaces.materials;
  let seed = 73;
  const random = () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; };
  const groundShape = new THREE.Shape([new THREE.Vector2(-2750, -2750), new THREE.Vector2(2750, -2750), new THREE.Vector2(2750, 2750), new THREE.Vector2(-2750, 2750)]);
  const [tx0, tz0, tx1, tz1] = data.terrain.bounds;
  groundShape.holes.push(new THREE.Path([[tx0, -tz0], [tx0, -tz1], [tx1, -tz1], [tx1, -tz0]].map(([x, y]) => new THREE.Vector2(x, y))));
  const ground = new THREE.Mesh(new THREE.ShapeGeometry(groundShape), materials.ground);
  ground.rotation.x = -Math.PI / 2; ground.position.y = -0.1; scene.add(ground);
  function surface(polygons, material, y) {
    for (const rings of polygons) {
      const shape = new THREE.Shape(rings[0].map(([x, z]) => new THREE.Vector2(x, -z)));
      for (const ring of rings.slice(1)) shape.holes.push(new THREE.Path(ring.map(([x, z]) => new THREE.Vector2(x, -z))));
      const mesh = new THREE.Mesh(new THREE.ShapeGeometry(shape), material);
      mesh.rotation.x = -Math.PI / 2; mesh.position.y = y; scene.add(mesh);
    }
  }
  surface(data.terrain.outsideRivers, materials.water, .06);
  surface([[[[tx0, tz0], [tx1, tz0], [tx1, tz1], [tx0, tz1], [tx0, tz0]]]], materials.water, .06);
  surface(data.terrain.outsideSites, materials.plot, .08);
  function box(parent, x, y, z, w, h, d, material) {
    const mesh = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), material); mesh.position.set(x, y + h / 2, z); parent.add(mesh); return mesh;
  }
  function cylinder(parent, x, y, z, r1, r2, h, material, segments = 16) {
    const mesh = new THREE.Mesh(new THREE.CylinderGeometry(r1, r2, h, segments), material); mesh.position.set(x, y + h / 2, z); parent.add(mesh); return mesh;
  }
  function beam(parent, a, b, r, material) {
    const av = new THREE.Vector3(...a), bv = new THREE.Vector3(...b), delta = bv.clone().sub(av);
    const mesh = new THREE.Mesh(new THREE.CylinderGeometry(r, r, delta.length(), 6), material);
    mesh.position.copy(av.add(bv).multiplyScalar(0.5)); mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), delta.normalize()); parent.add(mesh);
  }
  const terrain = terrainDetails({ THREE, scene, materials, data, box, cylinder, beam, random, density: lite ? .3 : 1 });
  scene.userData.infrastructure = infrastructure({ THREE, scene, materials, data, box, level: terrain.level });
  scene.userData.mappedTrees = mappedTrees({ THREE, scene, data, level: terrain.level, beam });
  surfaces.weather(terrain.terrainMaterial);
  data.terrain.review = { clods: terrain.clodCount, sheds: terrain.sheds, gardenBeds: data.neighbourhood.garden.beds.length, gardenAreaM2: data.neighbourhood.garden.cultivableAreaM2, vegetationTufts: terrain.vegetationCount, rills: data.terrain.rills, pools: data.terrain.pools.length, heightRange: data.terrain.heightRange };
  const detail = photoDetails({ THREE, scene, materials, box, cylinder, beam, random });
  for (const b of data.factoryStudies) detail.factory(b);
  for (const b of data.neighbourhood.mappedFactories) {
    // Orient the long roof axis along the traced range; facade subdivisions are inferred.
    detail.factory({ ...b, width: b.depth, depth: b.width, rotation: b.rotation - 90, mapped: true });
  }
  // One deliberately simple chimney per chosen site. Locations/heights are study assumptions.
  for (const id of [874, 875, 876, 1125, 562, 965]) {
    const b = data.factoryStudies.find(b => b.siteId === id) || data.neighbourhood.mappedFactories.find(b => b.siteId === id);
    if (b) { cylinder(scene, b.x, 0.15, b.z, 1.5, 2.1, 36, materials.brick); cylinder(scene, b.x, 35, b.z, 1.9, 1.9, 1.4, materials.brick); }
  }
  detail.barge(20, 49, -10, true);
  detail.barge(25, 73, 8, true);
  detail.barge(-26, 37, 5, false);
  detail.barge(-35, 95, -8, true);
  detail.waterfront();
  detail.station();
  detail.mill(data.neighbourhood.mill);
  detail.threeMills();
  data.neighbourhood.holders.forEach(h => detail.holder(h));
  data.neighbourhood.houses.forEach(h => detail.houses(h));
  data.neighbourhood.terraces.forEach(h => detail.terrace(h));
  // Author-supplied southwest context: distant terraces and works around
  // Three Mills/Bromley. Row axes and industrial ranges remain approximate.
  data.southwest.rows.forEach(h => detail.terrace(h));
  for (const b of data.southwest.industrialRanges) {
    detail.factory({ ...b, width: b.depth, depth: b.width, rotation: b.rotation - 90, mapped: true });
  }
  // Continuous elevated sewer: mapped bends, interpreted bank profile and distant extensions.
  const sewer = data.neighbourhood.sewer;
  surface(sewer.crest, materials.stone, sewer.height);
  const bankGeometry = new THREE.BufferGeometry();
  const sewerBanks = data.infrastructure.sewerBanks;
  bankGeometry.setAttribute('position', new THREE.Float32BufferAttribute(sewerBanks.flat(2), 3));
  bankGeometry.setAttribute('uv', new THREE.Float32BufferAttribute(sewerBanks.flat().flatMap(([x, _, z]) => [x / 5500, -z / 5500]), 2));
  bankGeometry.computeVertexNormals(); scene.add(new THREE.Mesh(bankGeometry, materials.ground));
  function routeSegment(a, b) {
    const dx = b[0] - a[0], dz = b[1] - a[1], length = Math.hypot(dx, dz);
    const group = new THREE.Group(); group.position.set((a[0] + b[0]) / 2, 0, (a[1] + b[1]) / 2);
    group.rotation.y = -Math.atan2(dz, dx); scene.add(group); return { group, length };
  }
  for (let i = 1; i < sewer.route.length; i++) {
    const { group, length } = routeSegment(sewer.route[i - 1], sewer.route[i]);
    // Shallow fascia makes the spanning crest legible over channels without blocking them.
    box(group, 0, 6.9, 0, length, .48, 15, materials.stone);
  }
  // Join the parapets at bends so walking closer does not reveal gaps between segments.
  const normals = sewer.route.slice(1).map((p, i) => {
    const a = sewer.route[i], length = Math.hypot(p[0] - a[0], p[1] - a[1]);
    return [-(p[1] - a[1]) / length, (p[0] - a[0]) / length];
  });
  for (const offset of [-7.3, 7.3]) {
    const edge = sewer.route.map((p, i) => {
      const a = normals[Math.max(0, i - 1)], b = normals[Math.min(i, normals.length - 1)];
      const n = [a[0] + b[0], a[1] + b[1]], length = Math.hypot(...n); n[0] /= length; n[1] /= length;
      const scale = offset / (n[0] * a[0] + n[1] * a[1]); return [p[0] + n[0] * scale, p[1] + n[1] * scale];
    });
    for (let i = 1; i < edge.length; i++) {
      const { group, length } = routeSegment(edge[i - 1], edge[i]);
      box(group, 0, 8.45, 0, length, .1, .1, materials.iron);
      for (let x = -length / 2; x < length / 2; x += 5) box(group, x, 7.4, 0, .1, 1.1, .1, materials.iron);
    }
  }
  // Static scene: combine surfaces by material so detail does not cost a draw call per window.
  // Two passes with preallocated typed arrays: the previous push-into-JS-array build held
  // several times the final buffer size in memory, which is what mobile browsers ran out of.
  scene.updateMatrixWorld(true);
  const batches = new Map(), originals = [];
  scene.traverse(object => {
    if (!object.isMesh || object.userData.keepIndexed) return;
    originals.push(object);
    const count = object.geometry.index ? object.geometry.index.count : object.geometry.getAttribute('position').count;
    const batch = batches.get(object.material) || { count: 0, offset: 0 };
    batch.count += count; batches.set(object.material, batch);
  });
  for (const batch of batches.values()) {
    batch.position = new Float32Array(batch.count * 3); batch.normal = new Float32Array(batch.count * 3); batch.uv = new Float32Array(batch.count * 2);
  }
  for (const object of originals) {
    const geometry = object.geometry.index ? object.geometry.toNonIndexed() : object.geometry.clone();
    if (!object.material.userData.preserveUV) surfaces.metricUV(geometry, object.geometry);
    geometry.applyMatrix4(object.matrixWorld);
    const batch = batches.get(object.material), count = geometry.getAttribute('position').count;
    for (const [name, size] of [['position', 3], ['normal', 3], ['uv', 2]]) {
      const attribute = geometry.getAttribute(name);
      if (attribute) batch[name].set(attribute.array.subarray(0, count * size), batch.offset * size);
    }
    batch.offset += count; geometry.dispose();
    object.removeFromParent(); object.geometry.dispose();
  }
  for (const [material, batch] of batches) {
    const geometry = new THREE.BufferGeometry();
    for (const [name, size] of [['position', 3], ['normal', 3], ['uv', 2]]) geometry.setAttribute(name, new THREE.BufferAttribute(batch[name], size));
    geometry.computeBoundingSphere();
    surfaces.weather(material);
    const mesh = new THREE.Mesh(geometry, material);
    mesh.castShadow = ![materials.ground, materials.water, materials.bed, materials.plot].includes(material);
    mesh.receiveShadow = true; scene.add(mesh);
  }
  // The scene never changes after this point: release the CPU copy of every vertex
  // buffer once it has been uploaded, roughly halving the retained memory.
  const releaseArray = function () { this.array = null; };
  scene.traverse(object => {
    if (!object.isMesh) return;
    for (const attribute of Object.values(object.geometry.attributes)) attribute.onUpload(releaseArray);
    object.geometry.index?.onUpload(releaseArray);
  });
  host.append(renderer.domElement);
  renderer.domElement.setAttribute('aria-hidden', 'true');
  renderer.domElement.addEventListener('webglcontextlost', e => {
    e.preventDefault(); stopWalking(); renderer = null;
    $$('[data-walk],[data-side]').forEach(b => b.disabled = true);
    host.classList.remove('is-ready'); stall('The 3D view paused. Reload to restore it. You can still read the stories and open the location map.'); update();
  });
  const resize = () => {
    if (!renderer) return;
    const { width, height } = host.getBoundingClientRect(); renderer.setSize(width, height, false); camera.aspect = width / height; update();
  };
  new ResizeObserver(resize).observe(host); resize();
}

// Lighter terrain for the lite tier: sample every `stride`-th grid cell. Bounds are kept,
// so world-space lookups, the river-bed texture and the sediment mask stay aligned.
function downsampleTerrain(t, stride) {
  const width = Math.ceil(t.width / stride), height = Math.ceil(t.height / stride);
  const levels = new Float32Array(width * height), landcover = new Uint8Array(width * height), properties = new Uint8Array(width * height * 4);
  for (let z = 0; z < height; z++) for (let x = 0; x < width; x++) {
    const src = Math.min(t.height - 1, z * stride) * t.width + Math.min(t.width - 1, x * stride), dst = z * width + x;
    levels[dst] = t.levels[src]; landcover[dst] = t.landcover[src];
    properties.set(t.properties.subarray(src * 4, src * 4 + 4), dst * 4);
  }
  return { ...t, width, height, step: t.step * stride, levels, landcover, properties };
}

/* ---------- Loading with progress ---------- */
const loadingText = $('#loading-text'), loadingFill = $('#loading-fill'), loadingBox = $('#loading');
const progress = { loaded: 0, total: 0 };
function paint(fraction) {
  const f = fraction ?? Math.min(.92, progress.loaded / Math.max(progress.total, 1));
  loadingFill.style.width = `${Math.max(4, Math.round(f * 100))}%`;
}
function stall(message) { loadingText.textContent = message; loadingBox.classList.add('is-stalled'); }
async function load(url, type = 'json') {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`${url} unavailable`);
  const declared = Number(response.headers.get('content-length')) || 0;
  progress.total += declared;
  if (!response.body) return type === 'json' ? response.json() : response.arrayBuffer();
  const reader = response.body.getReader(), chunks = [];
  let received = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    chunks.push(value); received += value.length; progress.loaded += value.length; paint();
  }
  if (!declared) progress.total += received;
  const bytes = new Uint8Array(received); let offset = 0;
  for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.length; }
  return type === 'json' ? JSON.parse(new TextDecoder().decode(bytes)) : bytes.buffer;
}

update();
try {
  loadingText.textContent = 'Fetching the ground plan';
  const [groundPlan, terrain, southwest, infrastructureData, trees] = await Promise.all([
    load('./data/ground-plan.json'), loadTerrain(load), load('./data/southwest-context.json'),
    load('./data/infrastructure.json'), load('./data/mapped-trees.json')]);
  data = groundPlan; data.terrain = terrain; data.southwest = southwest; data.infrastructure = infrastructureData; data.mappedTrees = trees;
  walker = createBridgeWalker(data.neighbourhood.sewer);
  buildPlan($('#plan'), { viewBox: '-700 -950 1400 1930' });
  buildPlan($('#minimap-plan'), { viewBox: '-620 -700 1240 1240', labels: false, markerRadius: 22, strokeScale: 3 });
  paint(.95); loadingText.textContent = 'Building the landscape';
  await new Promise(resolve => setTimeout(resolve, 40)); // let the label paint before the synchronous build
  try {
    buildScene();
    paint(1);
    $$('[data-walk],[data-side]').forEach(b => b.disabled = false);
    // First frame is drawn by resize(); reveal it over the poster, then ease into the hero view.
    requestAnimationFrame(() => {
      host.classList.add('is-ready');
      pendingArrival = false;
      goTo(poses[activeStop] || poses.hero, activeStop === 'hero' ? 4200 : 1800);
      setTimeout(() => $('#poster')?.remove(), 2400);
    });
  } catch (error) {
    renderer = null;
    stall('This browser could not open the 3D view. The still image stays, and you can explore the location map and read the stories.');
    console.warn('3D view unavailable:', error.message);
  }
  update();
} catch (error) {
  stall('The landscape data could not load. Serve this folder through a local web server, then reload. The stories below are still available.');
  $('#map-open').disabled = true; $('#map-open-2').disabled = true; $('#minimap').disabled = true;
  console.warn(error.message);
}
