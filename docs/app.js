// Interaction layer for the published front end: page, controls, plans and loading.
// Scene construction lives in the imported modules; shared helpers come from ./lib.
import * as THREE from './vendor/three/three.module.js';
import { photoDetails } from './photo-details.js';
import { factoryBuildings } from './factory-buildings.js';
import { factoryYards } from './factory-yards.js';
import { housingDetails } from './housing.js';
import { regionalFootprints } from './regional-footprints.js';
import { wallRiverVista } from './wall-river-vista.js';
import { sewerSurfaceHeight } from './sewer-levels.js';
import { sewerCrossing } from './sewer-crossing.js';
import { realism } from './realism.js';
import { lighting } from './lighting.js';
import { infrastructure } from './infrastructure.js';
import { tramRails } from './tram-rails.js';
import { mappedTrees } from './mapped-trees.js';
import { loadTerrain, terrainDetails } from './terrain-details.js';
import { loadRiverNetwork, riverNetwork } from './river-network.js';
import { loadRiverSystem, applyRiverSystem, riverSystem, installRiverExplorer } from './river-system.js';
import { loadMainLandscape, applyMainLandscape, mainLandscapeGround } from './main-landscape.js';
import { loadHistoricElevation, applyHistoricElevation, historicGround } from './historic-elevation.js';
import { tideControls } from './tides.js';
import { createDistrictNavigator, districtViews, factoryViews, viewPose } from './district-navigation.js';
import { createRandom } from './lib/prng.js';
import { createGroundSampler } from './lib/ground-sampler.js';
import { flatSurface, box as libBox, cylinder as libCylinder, beam as libBeam } from './lib/geometry.js';

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const rad = Math.PI / 180;
const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
// Quality tier. Phones and small tablets get a lighter scene: the full build holds
// several hundred megabytes of geometry, which mobile browsers will not tolerate.
// Override for testing with ?quality=lite or ?quality=full.
const requestedQuality = new URLSearchParams(location.search).get('quality');
const lite = requestedQuality
  ? requestedQuality === 'lite'
  : new URLSearchParams(location.search).has('flood') ||
    (matchMedia('(pointer: coarse)').matches && Math.min(screen.width, screen.height) < 900) ||
    (navigator.deviceMemory !== undefined && navigator.deviceMemory <= 4);
// ?export=1 keeps vertex buffers on the CPU and tags scene layers so scripts/export_gltf.py can write glTF.
const exportMode = new URLSearchParams(location.search).has('export');

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
  explore: null, // keeps whatever the reader was looking at
};
const state = { ...poses.arrival };
let activeStop = 'hero',
  pendingArrival = true;

let renderer, scene, camera, data, walker, surfaces, tide, regionalPlans, setFloodWater;
const plans = [];
const host = $('#panorama');

/* ---------- Camera tweening ---------- */
let tweenFrame = 0;
const easeInOut = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
function interruptTween() {
  if (tweenFrame) {
    cancelAnimationFrame(tweenFrame);
    tweenFrame = 0;
  }
}
// Any deliberate look/zoom/walk means the reader is exploring: stop the tween and clear the title.
function userInteracted() {
  interruptTween();
  dismissHero();
}
function goTo(pose, duration = 1500) {
  if (!pose) return;
  interruptTween();
  if (reduceMotion || duration <= 0) {
    Object.assign(state, pose);
    update();
    return;
  }
  const from = { ...state };
  const dyaw = ((pose.yaw - from.yaw + 540) % 360) - 180;
  const start = performance.now();
  const frame = (now) => {
    const t = Math.min(1, (now - start) / duration),
      k = easeInOut(t);
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
const header = $('#site-header'),
  hero = $('#hero');
function dismissHero() {
  hero.classList.add('is-dismissed');
}
$('#hero-close').addEventListener('click', dismissHero);
function activate(id) {
  if (walker?.mode === 'district' || id === activeStop) return;
  activeStop = id;
  $$('.step').forEach((s) => s.classList.toggle('is-active', s.dataset.stop === id));
  $$('[data-chapter]').forEach((a) => {
    if (a.dataset.chapter === id) a.setAttribute('aria-current', 'true');
    else a.removeAttribute('aria-current');
  });
  document.body.classList.toggle('is-explore', id === 'explore');
  header.classList.toggle('is-scrolled', id !== 'hero');
  if (!pendingArrival && renderer) goTo(poses[id]);
  else update();
}
// A step becomes active when it crosses the middle band of the viewport.
const stepObserver = new IntersectionObserver(
  (entries) => {
    for (const e of entries) if (e.isIntersecting) activate(e.target.dataset.stop);
  },
  { rootMargin: '-45% 0px -45% 0px', threshold: 0 }
);
$$('.step').forEach((step) => stepObserver.observe(step));
let scrollTick = false;
function onScroll() {
  if (scrollTick) return;
  scrollTick = true;
  requestAnimationFrame(() => {
    scrollTick = false;
    const p = Math.min(1, Math.max(0, scrollY / (innerHeight * 0.45)));
    hero.style.opacity = String(1 - p);
    hero.style.transform = `translateY(${-p * 36}px)`;
    hero.style.visibility = p >= 1 ? 'hidden' : '';
  });
}
addEventListener('scroll', onScroll, { passive: true });
onScroll();

/* ---------- Controls ---------- */
function resetView() {
  stopWalking();
  walker?.reset();
  if (activeStop === 'hero') hero.classList.remove('is-dismissed');
  goTo(poses[activeStop] || poses.hero, 900);
}
$('#reset').addEventListener('click', resetView);
$$('[data-chapter]').forEach((link) =>
  link.addEventListener('click', () => {
    if (walker?.mode === 'district') resetView();
  })
);
$('#zoom-in').addEventListener('click', () => {
  userInteracted();
  state.fov = Math.max(30, state.fov - 8);
  update();
});
$('#zoom-out').addEventListener('click', () => {
  userInteracted();
  state.fov = Math.min(90, state.fov + 8);
  update();
});

const destinations = new Map();
function travelTo(view) {
  if (!renderer || !walker) return;
  stopWalking();
  userInteracted();
  walker.flyTo(view.position);
  Object.assign(state, view.target ? viewPose(walker.world(), view.target) : { pitch: -35, fov: 62 });
  if (view.fov) state.fov = view.fov;
  update();
  host.focus({ preventScroll: true });
}
function populateDestinations() {
  const bridgeNames = {
    'bow-bridge': 'Bow Bridge',
    'pegshole-bridge': 'Pegshole Bridge',
    'st-thomas-bridge': 'St Thomas’s Bridge',
    'st-michaels-bridge': 'St Michael’s / Harrow Bridge',
    'channelsea-high-street-bridge': 'Channelsea Bridge — High Street',
    'three-mills-lea-bridge': 'Three Mills Bridge',
    'abbey-mill-crossing': 'Abbey Mill bridge',
  };
  const bridgeViews = data.infrastructure.roadBridges.map((b) => {
    const a = b.route[0],
      z = b.route.at(-1),
      x = (a[0] + z[0]) / 2,
      y = (a[1] + z[1]) / 2;
    return {
      id: b.id,
      name: (bridgeNames[b.id] || b.name) + (b.provisional ? ' (provisional connection)' : ''),
      position: [x - 60, 28, y + 70],
      target: [x, b.height / 2, y],
    };
  });
  for (const [label, views] of [
    ['Areas', districtViews],
    ['Factories', factoryViews(data.factoryBuildings)],
    ['Bridges', bridgeViews],
  ]) {
    const group = document.createElement('optgroup');
    group.label = label;
    for (const view of views) {
      destinations.set(view.id, view);
      const option = document.createElement('option');
      option.value = view.id;
      option.textContent = view.name;
      group.append(option);
    }
    $('#destination').append(group);
  }
}
$('#destination').addEventListener('change', (e) => {
  const view = destinations.get(e.target.value);
  if (view) travelTo(view);
});
$('#regional-footprints').addEventListener('change', (e) => {
  regionalPlans?.setVisible(e.target.checked);
  $$('.regional-building-plan').forEach((image) => (image.style.display = e.target.checked ? '' : 'none'));
});
$('#travel-toggle').addEventListener('click', () => {
  if (walker?.mode === 'district') resetView();
  else travelTo({ position: [walker.world()[0], 100, walker.world()[2]] });
});

const dialog = $('#map-dialog');
$('#map-scope').addEventListener('change', (e) => {
  const plan = plans.find((p) => p.labels);
  if (plan) setPlanScope(plan, e.target.value === 'region');
});
for (const id of ['#map-open', '#map-open-2', '#minimap'])
  $(id).addEventListener('click', () => {
    stopWalking();
    dialog.showModal();
  });
dialog.querySelector('[data-close]').addEventListener('click', () => dialog.close());
dialog.addEventListener('click', (e) => {
  if (e.target !== dialog) return;
  const r = dialog.getBoundingClientRect();
  if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) dialog.close();
});

let drag;
const held = new Set();
const walkingKeys = { KeyW: 'forward', KeyA: 'left', KeyS: 'back', KeyD: 'right', KeyE: 'up', KeyQ: 'down' };
let walkFrame = 0,
  lastWalkTime = 0;
function moveStep(distance) {
  if (!walker || !renderer || !held.size) return;
  const forward = Number(held.has('forward')) - Number(held.has('back'));
  const right = Number(held.has('right')) - Number(held.has('left'));
  const magnitude = Math.hypot(forward, right);
  const vertical = Number(held.has('up')) - Number(held.has('down'));
  if (!magnitude && !vertical) return;
  const divisor = Math.max(1, magnitude);
  const before = walker.world(),
    yaw = state.yaw * rad;
  walker.move(
    ((Math.sin(yaw) * forward + Math.cos(yaw) * right) * distance) / divisor,
    ((-Math.cos(yaw) * forward + Math.sin(yaw) * right) * distance) / divisor,
    vertical * distance
  );
  if (walker.world().some((v, i) => v !== before[i])) update();
}
function walkTick(time) {
  walkFrame = 0;
  if (!held.size || !renderer) return;
  moveStep(
    Math.min((time - lastWalkTime) / 1000, 0.05) * (walker.mode === 'district' ? Number($('#travel-speed').value) : 3)
  );
  lastWalkTime = time;
  walkFrame = requestAnimationFrame(walkTick);
}
function startWalking(direction) {
  if (!renderer || held.has(direction) || (walker.mode === 'bridge' && ['up', 'down'].includes(direction))) return;
  userInteracted();
  held.add(direction);
  moveStep(0.5);
  $(`[data-walk="${direction}"]`).dataset.active = 'true';
  if (!walkFrame) {
    lastWalkTime = performance.now();
    walkFrame = requestAnimationFrame(walkTick);
  }
}
function stopWalking(direction) {
  if (direction) held.delete(direction);
  else held.clear();
  $$('[data-walk]').forEach((b) => (b.dataset.active = String(held.has(b.dataset.walk))));
  if (!held.size) {
    cancelAnimationFrame(walkFrame);
    walkFrame = 0;
  }
}
$$('[data-walk]').forEach((button) => {
  button.addEventListener('pointerdown', (e) => {
    if (e.button !== 0) return;
    e.preventDefault();
    button.focus({ preventScroll: true });
    button.setPointerCapture(e.pointerId);
    startWalking(button.dataset.walk);
  });
  for (const event of ['pointerup', 'pointercancel', 'lostpointercapture'])
    button.addEventListener(event, () => stopWalking(button.dataset.walk));
  // Keyboard/screen-reader activation makes one step; pointer activation is handled above.
  button.addEventListener('click', (e) => {
    if (e.detail === 0) {
      startWalking(button.dataset.walk);
      stopWalking();
    }
  });
});
$$('[data-side]').forEach((button) =>
  button.addEventListener('click', () => {
    stopWalking();
    walker?.side(button.dataset.side);
    update();
  })
);
addEventListener('keyup', (e) => {
  if (walkingKeys[e.code]) stopWalking(walkingKeys[e.code]);
});
addEventListener('blur', () => {
  stopWalking();
  drag = null;
});
document.addEventListener('visibilitychange', () => {
  if (document.hidden) stopWalking();
});
document.addEventListener('focusin', (e) => {
  if (e.target !== host && !e.target.closest('#bridge-controls')) stopWalking();
});
host.addEventListener('blur', () => stopWalking());
host.addEventListener('pointerdown', (e) => {
  if (e.button !== 0) return;
  host.focus({ preventScroll: true });
  host.setPointerCapture(e.pointerId);
  drag = { id: e.pointerId, x: e.clientX, y: e.clientY, touch: e.pointerType === 'touch' };
});
host.addEventListener('pointermove', (e) => {
  if (!drag || e.pointerId !== drag.id) return;
  if (Math.abs(e.clientX - drag.x) + Math.abs(e.clientY - drag.y) > 2) dismissHero();
  interruptTween();
  state.yaw -= (e.clientX - drag.x) * 0.14;
  // On touch outside explore mode the browser owns vertical movement (page scroll).
  if (!drag.touch || walker?.mode === 'district' || document.body.classList.contains('is-explore'))
    state.pitch += (e.clientY - drag.y) * 0.12;
  drag.x = e.clientX;
  drag.y = e.clientY;
  update();
});
for (const event of ['pointerup', 'pointercancel', 'lostpointercapture'])
  host.addEventListener(event, () => {
    drag = null;
  });
function navigationKeydown(e) {
  if (e.target.closest('select, input')) return;
  if (e.altKey || e.ctrlKey || e.metaKey) return;
  if (walkingKeys[e.code]) {
    e.preventDefault();
    startWalking(walkingKeys[e.code]);
    return;
  }
  const actions = {
    ArrowLeft: () => (state.yaw -= 5),
    ArrowRight: () => (state.yaw += 5),
    ArrowUp: () => (state.pitch += 4),
    ArrowDown: () => (state.pitch -= 4),
    '+': () => (state.fov -= 5),
    '=': () => (state.fov -= 5),
    '-': () => (state.fov += 5),
    Home: resetView,
  };
  if (actions[e.key]) {
    e.preventDefault();
    if (e.key !== 'Home') userInteracted();
    else interruptTween();
    actions[e.key]();
    update();
  }
}
host.addEventListener('keydown', navigationKeydown);
$('#bridge-controls').addEventListener('keydown', navigationKeydown);

/* ---------- Render + readouts ---------- */
const rose = $('#rose'),
  bearing = $('#bearing');
function update() {
  state.yaw = ((state.yaw % 360) + 360) % 360;
  state.pitch = Math.max(-85, Math.min(75, state.pitch));
  const flying = walker?.mode === 'district';
  document.body.classList.toggle('is-roaming', Boolean(flying));
  $('#flight-controls').hidden = !flying;
  $('#bridge-sides').hidden = Boolean(flying);
  $('#travel-toggle').textContent = flying ? 'Return to the bridge' : 'Fly over the district';
  state.fov = Math.max(30, Math.min(90, state.fov));
  const directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
  bearing.textContent = `${directions[Math.round(state.yaw / 45) % 8]} · ${Math.round(state.yaw)}°`;
  rose.style.transform = `rotate(${-state.yaw}deg)`;
  if (camera && renderer) {
    camera.position.fromArray(walker.world());
    regionalPlans?.update(camera);
    if (scene.fog) scene.fog.density = 0.00065 / (1 + Math.max(0, camera.position.y - 400) / 260);
    camera.near = Math.max(0.15, camera.position.y / 100);
    camera.fov = state.fov;
    camera.updateProjectionMatrix();
    camera.lookAt(
      camera.position
        .clone()
        .add(
          new THREE.Vector3(
            Math.sin(state.yaw * rad) * Math.cos(state.pitch * rad),
            Math.sin(state.pitch * rad),
            -Math.cos(state.yaw * rad) * Math.cos(state.pitch * rad)
          )
        )
    );
    surfaces?.reflect(camera);
    renderer.render(scene, camera);
  }
  if (walker && plans.length) {
    // Three.js FOV is vertical; show the actual horizontal field on the plan.
    const halfAngle = Math.atan(Math.tan((state.fov * rad) / 2) * (camera?.aspect || 1.5));
    const a = state.yaw * rad - halfAngle,
      b = state.yaw * rad + halfAngle,
      r = 420;
    const [cx, _, cz] = walker.world();
    for (const plan of plans) {
      if (!plan.labels) setPlanScope(plan, cx < -1650 || cx > 1300 || cz < -1350 || cz > 1600);
      plan.cone.setAttribute(
        'd',
        `M${cx},${cz} L${cx + Math.sin(a) * r},${cz - Math.cos(a) * r} A${r},${r} 0 0 1 ${cx + Math.sin(b) * r},${cz - Math.cos(b) * r} Z`
      );
      plan.marker.setAttribute('cx', cx);
      plan.marker.setAttribute('cy', cz);
      plan.label?.setAttribute('x', cx + 25);
      plan.label?.setAttribute('y', cz - 22);
    }
    const p = walker.snapshot(),
      side = p.across > 2 ? 'South side' : p.across < -2 ? 'North side' : 'Centre';
    $('#walk-position').textContent = flying
      ? `Flying · height ${Math.round(walker.world()[1])} m`
      : `${side} · ${Math.round(Math.abs(p.along))} m from centre`;
    if (!flying) $('#destination').value = '';
    $$('[data-side]').forEach((b) =>
      b.setAttribute(
        'aria-pressed',
        String(Math.abs(p.across - (b.dataset.side === 'north' ? -p.limits.across : p.limits.across)) < 0.01)
      )
    );
  }
  // Read-only diagnostic for browser checks (same shape as the docs/ build, plus narrative state).
  window.panoramaReview = {
    ...state,
    revision: window.sceneRevision,
    camera: camera?.position.toArray(),
    ready: Boolean(renderer),
    quality: lite ? 'lite' : 'full',
    destinationCount: destinations.size,
    activeStop,
    tweening: Boolean(tweenFrame),
    movement: walker?.snapshot(),
    reflection: surfaces?.reflectionStats,
    terrain: data?.terrain?.review,
    lighting: scene?.userData.lighting,
    elevation: data?.elevation?.review,
    mainLandscape: data?.mainLandscape?.review,
    sewerCrossing: scene?.userData.sewerCrossing,
    infrastructure: scene?.userData.infrastructure,
    tramRails: scene?.userData.tramRails,
    mappedTrees: scene?.userData.mappedTrees,
    riverNetwork: scene?.userData.riverNetwork,
    riverSystem: scene?.userData.riverSystem,
    tide: tide?.snapshot(),
    tideObjects: scene?.userData.tideObjects,
    gardens: scene?.userData.gardenReview,
    factoryBuildings: scene?.userData.factoryBuildings,
    factoryYards: scene?.userData.factoryYards,
    housing: scene?.userData.housingDetails,
    regionalFootprints: regionalPlans?.stats,
    railConnections: scene?.userData.railConnections,
    greatEastern: scene?.userData.greatEastern,
    highStreetFrontages: scene?.userData.highStreetFrontages,
    wallRiverVista: scene?.userData.wallRiverVista,
    stationStudy: scene?.userData.stationStudy,
    stationSupport: scene?.userData.stationSupport,
    triangles: renderer?.info.render.triangles,
    drawCalls: renderer?.info.render.calls,
  };
}

/* ---------- Plans (dialog map + HUD inset) ---------- */
function planPath(polygons) {
  return polygons
    .map((poly) => poly.map((ring) => ring.map((p, i) => `${i ? 'L' : 'M'}${p.join(',')}`).join(' ') + 'Z').join(' '))
    .join(' ');
}
function setPlanScope(plan, regional) {
  if (plan.regional === regional) return;
  plan.regional = regional;
  const [a, b, c, d] = data.regionalFootprints.bounds;
  plan.svg.setAttribute('viewBox', regional ? `${a} ${b} ${c - a} ${d - b}` : plan.viewBox);
  plan.marker.setAttribute('r', regional ? (plan.labels ? 65 : 140) : plan.markerRadius);
  plan.label?.setAttribute('font-size', regional ? '90' : '24');
  if (plan.label) plan.label.style.fontSize = regional ? '90px' : '';
}
function buildPlan(container, { viewBox, labels = true, markerRadius = 8, strokeScale = 1 }) {
  const ns = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(ns, 'svg');
  svg.setAttribute('viewBox', viewBox);
  svg.setAttribute('role', 'img');
  svg.setAttribute(
    'aria-label',
    'Historical building plans for West Ham and the surrounding region. Click the map to fly there.'
  );
  function element(tag, attrs, text) {
    const el = document.createElementNS(ns, tag);
    Object.entries(attrs).forEach(([k, v]) => el.setAttribute(k, v));
    if (text) el.textContent = text;
    svg.append(el);
    return el;
  }
  const region = data.regionalFootprints,
    [rx, rz, rx1, rz1] = region.bounds;
  for (const file of [region.waterContext, region.overview])
    element('image', {
      href: window.sceneAssetUrl?.(`./data/regional-footprints/${file}`) || `./data/regional-footprints/${file}`,
      x: rx,
      y: rz,
      width: rx1 - rx,
      height: rz1 - rz,
      preserveAspectRatio: 'none',
      class: file === region.overview ? 'regional-building-plan' : 'regional-water-plan',
    });
  [...data.rivers, ...data.factoryBuildings.westContext.rivers].forEach((r) =>
    element('path', { d: planPath(r.polygons), fill: '#9bb8b7', 'fill-rule': 'evenodd' })
  );
  data.riverNetwork.reviewedConnections.connections.forEach((r) =>
    element('path', { d: planPath(r.polygons), fill: '#9bb8b7', 'fill-rule': 'evenodd' })
  );
  element('path', { d: planPath(data.riverSystem.waterPolygons), fill: '#9bb8b7', 'fill-rule': 'evenodd' });
  for (const r of data.infrastructure.railways)
    if (r.northernWater) element('path', { d: planPath(r.northernWater), fill: '#9bb8b7', 'fill-rule': 'evenodd' });
  for (const ditch of data.riverNetwork.marshDitches.features)
    element('path', { d: planPath(ditch.renderPolygons), fill: '#809796', 'fill-rule': 'evenodd' });
  element('polygon', { points: data.stationPlan.worldFootprint.map((p) => p.join(',')).join(' '), fill: '#79634e' });
  data.sites.forEach((s) =>
    element('path', {
      d: planPath(s.polygons),
      fill: '#c1b49e',
      stroke: '#a8977d',
      'stroke-width': strokeScale,
      'fill-rule': 'evenodd',
    })
  );
  data.infrastructure.roads.forEach((r) =>
    element('polyline', {
      points: r.route.map((p) => p.join(',')).join(' '),
      fill: 'none',
      stroke: '#e9ddbf',
      'stroke-width': r.width + 2,
      'stroke-linejoin': 'round',
    })
  );
  data.infrastructure.roadBridges.forEach((b) =>
    element('polyline', {
      points: b.route.map((p) => p.join(',')).join(' '),
      fill: 'none',
      stroke: '#8d633e',
      'stroke-width': b.width,
      'stroke-linejoin': 'round',
    })
  );
  data.neighbourhood.holders.forEach((h) =>
    element('circle', {
      cx: h.x,
      cy: h.z,
      r: h.radius,
      fill: '#728c8150',
      stroke: '#496d61',
      'stroke-width': 2 * strokeScale,
    })
  );
  [...data.neighbourhood.houses, ...data.neighbourhood.terraces].forEach((h) =>
    element('polygon', { points: h.footprint.map((p) => p.join(',')).join(' '), fill: '#9e6851' })
  );
  data.neighbourhood.mappedFactories.forEach((h) =>
    element('polygon', { points: h.footprint.map((p) => p.join(',')).join(' '), fill: '#79634e' })
  );
  data.neighbourhood.garden.beds.forEach((b) =>
    element('rect', {
      x: b.x - b.width / 2,
      y: b.z - b.depth / 2,
      width: b.width,
      height: b.depth,
      transform: `rotate(${b.rotation || 0} ${b.x} ${b.z})`,
      fill: '#789069',
    })
  );
  data.infrastructure.railways.forEach((r) =>
    element('polyline', {
      points: r.route.map((p) => p.join(',')).join(' '),
      fill: 'none',
      stroke: '#4a4e4c',
      'stroke-width': 5 * strokeScale,
      'stroke-dasharray': `${10 * strokeScale} ${4 * strokeScale}`,
    })
  );
  element('polyline', {
    points: data.neighbourhood.sewer.route.map((p) => p.join(',')).join(' '),
    fill: 'none',
    stroke: '#68786c',
    'stroke-width': 15,
  });
  element('polygon', {
    points: walker
      .corners()
      .map((p) => p.join(','))
      .join(' '),
    fill: '#f5f2e9',
    stroke: '#ad792f',
    'stroke-width': 2 * strokeScale,
  });
  data.factoryBuildings.buildings.forEach((b) =>
    b.renderPolygons.forEach((p) =>
      element('path', { d: planPath([[p.outer, ...p.holes]]), fill: '#79634e', 'fill-rule': 'evenodd' })
    )
  );
  data.stationPlan.supportingBuildings.forEach((b) =>
    b.renderPolygons.forEach((p) =>
      element('path', { d: planPath([[p.outer, ...p.holes]]), fill: '#79634e', 'fill-rule': 'evenodd' })
    )
  );
  data.highStreetFrontages.buildings.forEach((b) =>
    b.renderPolygons.forEach((p) =>
      element('path', { d: planPath([[p.outer, ...p.holes]]), fill: '#9e6851', 'fill-rule': 'evenodd' })
    )
  );
  const bank = data.highStreetFrontages.vista.bank;
  element('path', {
    d: bank.samples.map(([x, z], i) => `${i ? 'L' : 'M'}${x + bank.pathLandOffset},${z}`).join(' '),
    fill: 'none',
    stroke: '#af9879',
    'stroke-width': bank.pathWidth,
  });
  for (const c of data.highStreetFrontages.vista.connections)
    element('polyline', {
      points: c.route.map(([x, , z]) => `${x},${z}`).join(' '),
      fill: 'none',
      stroke: '#af9879',
      'stroke-width': c.width,
    });
  const cone = element('path', { fill: '#bb8d3540', stroke: '#ad792f', 'stroke-width': 2 * strokeScale });
  const marker = element('circle', {
    cx: 0,
    cy: 0,
    r: markerRadius,
    fill: '#233d3b',
    stroke: '#f5f2e9',
    'stroke-width': 3 * strokeScale,
  });
  let label;
  if (labels) {
    element('text', { x: -1040, y: 155 }, 'Bow Bridge');
    element('text', { x: -690, y: -265, transform: 'rotate(-51 -690 -265)' }, 'High Street');
    element('text', { x: -850, y: -460 }, 'City Mills');
    element('text', { x: -1050, y: 110 }, 'Sugar House Lane');
    element('text', { x: -790, y: 470 }, 'Three Mills');
    element('text', { x: -45, y: -80 }, 'Corn mill');
    label = element('text', { x: 25, y: -22 }, 'You are here');
    for (const [x, z, name, dx, dz] of [
      [-185, -13, 'Abbey Mills', -205, -65],
      [-311, 650, 'Bromley gasworks', 30, 130],
      [-92, -117, 'Abbey Lane houses', 30, 0],
      [-230, -320, 'West Ham gasworks', -230, -100],
    ]) {
      element('circle', { cx: x, cy: z, r: 8, fill: '#233d3b', stroke: '#f5f2e9', 'stroke-width': 3 });
      element('text', { x: x + dx, y: z + dz }, name);
    }
    element('text', { x: 220, y: 260 }, 'Channelsea');
    element('text', { x: 220, y: 292 }, '& Abbey Creek');
    element('path', {
      d: 'M440,-280 L440,-380 M425,-350 L440,-380 L455,-350',
      stroke: '#233d3b',
      'stroke-width': 4,
      fill: 'none',
    });
    element('text', { x: 430, y: -400 }, 'N');
    element('path', {
      d: 'M230,900 L430,900 M230,890 L230,910 M430,890 L430,910',
      stroke: '#233d3b',
      'stroke-width': 3,
      fill: 'none',
    });
    element('text', { x: 260, y: 940 }, '200 metres');
  }
  if (labels) {
    svg.addEventListener('click', (e) => {
      if (!renderer) return;
      const point = new DOMPoint(e.clientX, e.clientY).matrixTransform(svg.getScreenCTM().inverse());
      dialog.close();
      travelTo({
        position: [point.x, Math.max($('#map-scope').value === 'region' ? 500 : 80, walker.world()[1]), point.y],
      });
    });
  }
  container.append(svg);
  plans.push({ cone, marker, label, svg, viewBox, labels, markerRadius, regional: false });
}

/* ---------- Scene (unchanged construction from docs/app.js) ---------- */
function buildScene() {
  if (lite) data.terrain = downsampleTerrain(data.terrain, 2);
  renderer = new THREE.WebGLRenderer({ antialias: !lite, alpha: false, powerPreference: 'low-power' });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, lite ? 1 : 1.75));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(state.fov, 1, 0.15, 18000);
  camera.position.fromArray(walker.world());
  scene.userData.lighting = lighting(THREE, renderer, scene, lite ? { shadowMapSize: 1024, softShadows: false } : {});
  surfaces = realism(THREE, renderer, scene, data, lite ? { reflectionWidth: 256, reflectionHeight: 192 } : {});
  const materials = surfaces.materials;
  const random = createRandom(73);
  const surface = (polygons, material, y) => flatSurface(THREE, scene, polygons, material, y);
  // Layer tags on everything added to the scene. They serve the glTF export and the diagnostic;
  // rendering ignores them. Each mark names what follows until the next mark.
  let layerStart = scene.children.length,
    layerName = null;
  const mark = (name) => {
    if (layerName)
      for (const child of scene.children.slice(layerStart)) child.traverse((o) => (o.userData.layer ??= layerName));
    layerStart = scene.children.length;
    layerName = name;
  };
  mark('ground');
  surface(data.riverNetwork.baseGround, materials.land, -0.1);
  historicGround({ THREE, scene, material: materials.land, elevation: data.elevation });
  mainLandscapeGround({ THREE, scene, material: materials.land, landscape: data.mainLandscape });
  scene.userData.riverNetwork = riverNetwork({ THREE, scene, materials, data: data.riverNetwork, surfaces });
  scene.userData.riverSystem = riverSystem({ THREE, scene, data: data.riverSystem, materials, surfaces });
  // Water belongs to waterways, not the rectangular boundary of a terrain tile.
  // A blanket plane exposed a straight water seam where that tile tapered down.
  surface(data.riverNetwork.tide.polygons, materials.water, data.riverNetwork.waterLevel);
  surface(
    data.riverNetwork.reviewedConnections.connections.filter((r) => !r.tidalDisplay).flatMap((r) => r.polygons),
    materials.water,
    data.riverNetwork.waterLevel
  );
  const retainedIds = new Set([
    ...data.riverNetwork.retainedWaterChannelIds,
    ...(data.riverNetwork.isolatedWaterChannelIds ?? []),
  ]);
  surface(
    [...data.rivers, ...data.factoryBuildings.westContext.rivers]
      .filter((r) => retainedIds.has(r.id))
      .flatMap((r) => r.polygons),
    materials.water,
    data.riverNetwork.waterLevel
  );
  surface(
    data.riverNetwork.marshDitches.features.flatMap((f) => f.renderPolygons),
    materials.water,
    data.riverNetwork.waterLevel
  );
  for (const [x, z, rx, rz] of data.terrain.pools) {
    const ring = Array.from({ length: 33 }, (_, i) => [
      x + rx * Math.cos((i * Math.PI) / 16),
      z + rz * Math.sin((i * Math.PI) / 16),
    ]);
    surface([[ring]], materials.water, data.riverNetwork.waterLevel);
  }
  surface(data.riverNetwork.tide.polygons, materials.tidalWater, data.riverNetwork.tide.low);
  // Module-facing helpers keep their (parent, ...) signature; the shared versions take THREE first.
  const box = (parent, ...args) => libBox(THREE, parent, ...args);
  const cylinder = (parent, ...args) => libCylinder(THREE, parent, ...args);
  const beam = (parent, ...args) => libBeam(THREE, parent, ...args);
  mark('terrain');
  const terrain = terrainDetails({
    THREE,
    scene,
    materials,
    data,
    box,
    cylinder,
    beam,
    random,
    density: lite ? 0.3 : 1,
  });
  scene.userData.gardenReview = terrain.gardenReview;
  mark('yards');
  scene.userData.factoryYards = factoryYards({
    THREE,
    scene,
    materials,
    data,
    level: terrain.level,
    box,
    cylinder,
    lite,
  });
  mark('infrastructure');
  scene.userData.infrastructure = infrastructure({ THREE, scene, materials, data, box, level: terrain.level });
  scene.userData.tramRails = tramRails({ THREE, scene, data, level: terrain.level });
  mark('trees');
  scene.userData.mappedTrees = mappedTrees({ THREE, scene, data, level: terrain.level, beam });
  surfaces.weather(terrain.terrainMaterial);
  data.terrain.review = {
    clods: terrain.clodCount,
    sheds: terrain.sheds,
    gardenBeds: data.neighbourhood.garden.beds.length,
    gardenAreaM2: data.neighbourhood.garden.cultivableAreaM2,
    vegetationTufts: terrain.vegetationCount,
    rills: data.terrain.rills,
    pools: data.terrain.pools.length,
    heightRange: data.terrain.heightRange,
  };
  const detail = photoDetails({ THREE, scene, materials, box, cylinder, beam, random });
  const surveyedFactories = new Set(data.factoryBuildings.sites.map((s) => s.id));
  mark('factory-buildings');
  scene.userData.factoryBuildings = factoryBuildings({
    THREE,
    scene,
    materials,
    data: data.factoryBuildings,
    box,
    cylinder,
    beam,
  });
  scene.userData.highStreetFrontages = factoryBuildings({
    THREE,
    scene,
    materials,
    data: data.highStreetFrontages,
    box,
    cylinder,
    beam,
  });
  scene.userData.wallRiverVista = wallRiverVista({
    THREE,
    scene,
    materials,
    data: data.highStreetFrontages.vista,
    box,
    beam,
  });
  mark('study-buildings');
  for (const b of data.factoryStudies) if (!surveyedFactories.has(b.siteId)) detail.factory(b);
  for (const b of data.neighbourhood.mappedFactories) {
    if (surveyedFactories.has(b.siteId)) continue;
    // Orient the long roof axis along the traced range; facade subdivisions are inferred.
    detail.factory({ ...b, width: b.depth, depth: b.width, rotation: b.rotation - 90, mapped: true });
  }
  // One deliberately simple chimney per site listed in the ground plan, whose record also holds the study dimensions.
  const chimneys = data.neighbourhood.studyChimneys;
  for (const id of chimneys.siteIds) {
    if (surveyedFactories.has(id)) continue;
    const b =
      data.factoryStudies.find((b) => b.siteId === id) ||
      data.neighbourhood.mappedFactories.find((b) => b.siteId === id);
    if (b) {
      const lift = b.landscapeLift ?? 0;
      cylinder(scene, b.x, 0.15 + lift, b.z, chimneys.topRadius, chimneys.baseRadius, chimneys.height, materials.brick);
      cylinder(
        scene,
        b.x,
        chimneys.height - 1 + lift,
        b.z,
        chimneys.capRadius,
        chimneys.capRadius,
        1.4,
        materials.brick
      );
    }
  }
  // Barge placements interpret the 1900 photograph and are recorded in the ground plan, not here.
  mark('waterfront');
  const barges = data.neighbourhood.barges.map((b) => [b.x, b.z, b.heading, b.laden]);
  for (const spec of barges) detail.barge(...spec);
  surfaces.excludeBargeHolds(barges);
  detail.waterfront();
  detail.station(data.stationPlan);
  scene.userData.stationSupport = factoryBuildings({
    THREE,
    scene,
    materials,
    box,
    cylinder,
    beam,
    data: {
      buildings: data.stationPlan.supportingBuildings,
      sites: [{ id: 'abbey-support' }],
      holders: [],
      structures: [],
    },
  });
  detail.mill(data.neighbourhood.mill);
  mark('gas-holders');
  // Sites with individually registered holders supersede their earlier map-traced circles.
  const registeredHolderSites = new Set(data.factoryBuildings.holders.map((h) => h.siteId));
  [
    ...data.neighbourhood.holders.filter((h) => !registeredHolderSites.has(h.siteId)),
    ...data.factoryBuildings.holders,
  ].forEach((h) => detail.holder(h));
  mark('housing');
  data.neighbourhood.houses.forEach((h) => detail.houses(h));
  data.neighbourhood.terraces.forEach((h) => detail.terrace(h));
  // Author-supplied southwest context: distant terraces and works around
  // Three Mills/Bromley. Row axes and industrial ranges remain approximate.
  data.southwest.rows.forEach((h) => detail.terrace(h));
  scene.userData.housingDetails = housingDetails({ THREE, scene, materials, data, level: terrain.level, box });
  mark('study-buildings');
  for (const b of data.southwest.industrialRanges) {
    if (surveyedFactories.has(b.siteId)) continue;
    detail.factory({ ...b, width: b.depth, depth: b.width, rotation: b.rotation - 90, mapped: true });
  }
  mark('sewer');
  // Continuous elevated sewer: mapped bends, interpreted bank profile and distant extensions.
  const sewer = data.neighbourhood.sewer;
  const cover = (x, z) => sewerSurfaceHeight(x, z, sewer, data.infrastructure.sewerHighStreet);
  // The crest is grassed where it covers the earth bank (and the sewer inside it); the stone
  // deck shows only over the openings the bank stops at: water, railway and streets.
  const bankCells = new Map();
  const bankCell = (x, z) => `${Math.floor(x / 10)},${Math.floor(z / 10)}`;
  for (const tri of data.infrastructure.sewerBanks) {
    const xs = tri.map((p) => p[0]),
      zs = tri.map((p) => p[2]);
    for (let i = Math.floor(Math.min(...xs) / 10); i <= Math.floor(Math.max(...xs) / 10); i++)
      for (let j = Math.floor(Math.min(...zs) / 10); j <= Math.floor(Math.max(...zs) / 10); j++) {
        const key = `${i},${j}`;
        if (!bankCells.has(key)) bankCells.set(key, []);
        bankCells.get(key).push(tri);
      }
  }
  const overBank = (x, z) =>
    (bankCells.get(bankCell(x, z)) || []).some(([a, b, c]) => {
      const side = (p, q) => (q[0] - p[0]) * (z - p[2]) - (q[2] - p[2]) * (x - p[0]);
      const s = [side(a, b), side(b, c), side(c, a)];
      return s.every((v) => v >= 0) || s.every((v) => v <= 0);
    });
  const crestVertices = { earth: [], deck: [] };
  for (const source of data.infrastructure.sewerCrestTriangles) {
    const tri = source.map(([x, z]) => [x, cover(x, z), z]);
    const [a, b, c] = tri;
    if ((b[0] - a[0]) * (c[2] - a[2]) - (b[2] - a[2]) * (c[0] - a[0]) > 0) tri.reverse();
    const kind = overBank((a[0] + b[0] + c[0]) / 3, (a[2] + b[2] + c[2]) / 3) ? 'earth' : 'deck';
    crestVertices[kind].push(...tri.flat());
  }
  for (const [kind, vertices] of Object.entries(crestVertices)) {
    if (!vertices.length) continue;
    const crestGeometry = new THREE.BufferGeometry();
    crestGeometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
    if (kind === 'earth') {
      // Same texture mapping as the bank slopes, so crest and slope read as one grassed earthwork.
      const uv = [];
      for (let i = 0; i < vertices.length; i += 3) uv.push(vertices[i] / 5500, -vertices[i + 2] / 5500);
      crestGeometry.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
    }
    crestGeometry.computeVertexNormals();
    scene.add(new THREE.Mesh(crestGeometry, kind === 'earth' ? materials.ground : materials.stone));
  }
  const bankGeometry = new THREE.BufferGeometry();
  const sewerBanks = data.infrastructure.sewerBanks.map((tri) =>
    tri.map(([x, y, z]) => [
      x,
      // Toes follow the detailed ground sampler, not the 10 m landscape raster, which ignores bank crests.
      (y * cover(x, z)) / sewer.height + (1 - y / sewer.height) * terrain.level(x, z),
      z,
    ])
  );
  bankGeometry.setAttribute('position', new THREE.Float32BufferAttribute(sewerBanks.flat(2), 3));
  bankGeometry.setAttribute(
    'uv',
    new THREE.Float32BufferAttribute(
      sewerBanks.flat().flatMap(([x, _, z]) => [x / 5500, -z / 5500]),
      2
    )
  );
  bankGeometry.computeVertexNormals();
  scene.add(new THREE.Mesh(bankGeometry, materials.ground));
  function routeSegment(a, b) {
    const dx = b[0] - a[0],
      dz = b[1] - a[1],
      length = Math.hypot(dx, dz);
    const group = new THREE.Group();
    group.position.set((a[0] + b[0]) / 2, 0, (a[1] + b[1]) / 2);
    group.rotation.y = -Math.atan2(dz, dx);
    scene.add(group);
    return { group, length };
  }
  for (let i = 1; i < sewer.route.length; i++) {
    const a = sewer.route[i - 1],
      b = sewer.route[i],
      steps = Math.ceil(Math.hypot(b[0] - a[0], b[1] - a[1]) / 3);
    for (let j = 0; j < steps; j++) {
      const p = a.map((v, k) => v + ((b[k] - v) * j) / steps),
        q = a.map((v, k) => v + ((b[k] - v) * (j + 1)) / steps);
      const { group, length } = routeSegment(p, q),
        ha = cover(...p),
        hb = cover(...q);
      // Enclosed cover remains below the carriageway at High Street.
      group.position.y = (ha + hb) / 2;
      group.rotation.z = Math.atan2(hb - ha, length);
      box(group, 0, -0.5, 0, length, 0.48, sewer.crestWidth, materials.stone);
    }
  }
  // Join the parapets at bends so walking closer does not reveal gaps between segments.
  scene.userData.sewerCrossing = sewerCrossing({
    THREE,
    scene,
    sewer,
    crossing: data.infrastructure.sewerHighStreet,
    level: terrain.level,
    materials,
  });
  for (const edge of data.infrastructure.sewerRailEdges) {
    for (let i = 1; i < edge.length; i++) {
      const { group, length } = routeSegment(edge[i - 1], edge[i]);
      const ha = cover(...edge[i - 1]),
        hb = cover(...edge[i]);
      group.position.y = (ha + hb) / 2;
      group.rotation.z = Math.atan2(hb - ha, length);
      box(group, 0, 1.05, 0, length, 0.1, 0.1, materials.iron);
      box(scene, edge[i - 1][0], ha, edge[i - 1][1], 0.1, 1.1, 0.1, materials.iron);
    }
  }
  mark(null);
  // Static scene: combine surfaces by material so detail does not cost a draw call per window.
  // Two passes with preallocated typed arrays: the previous push-into-JS-array build held
  // several times the final buffer size in memory, which is what mobile browsers ran out of.
  scene.updateMatrixWorld(true);
  const batches = new Map(),
    originals = [];
  // Export keeps layers separable at the cost of more draw calls; the live page batches per material only.
  const batchKey = (object) =>
    exportMode ? `${object.material.uuid}|${object.userData.layer || 'untagged'}` : object.material;
  const materialName = (material) =>
    Object.keys(materials).find((key) => materials[key] === material) || material.userData.surface || 'material';
  scene.traverse((object) => {
    if (!object.isMesh || object.userData.keepIndexed) return;
    originals.push(object);
    const count = object.geometry.index ? object.geometry.index.count : object.geometry.getAttribute('position').count;
    const batch = batches.get(batchKey(object)) || {
      count: 0,
      offset: 0,
      material: object.material,
      layer: object.userData.layer || 'untagged',
    };
    batch.count += count;
    batches.set(batchKey(object), batch);
  });
  for (const batch of batches.values()) {
    batch.position = new Float32Array(batch.count * 3);
    batch.normal = new Float32Array(batch.count * 3);
    batch.uv = new Float32Array(batch.count * 2);
  }
  for (const object of originals) {
    const geometry = object.geometry.index ? object.geometry.toNonIndexed() : object.geometry.clone();
    if (!object.material.userData.preserveUV) surfaces.metricUV(geometry, object.geometry);
    geometry.applyMatrix4(object.matrixWorld);
    const batch = batches.get(batchKey(object)),
      count = geometry.getAttribute('position').count;
    for (const [name, size] of [
      ['position', 3],
      ['normal', 3],
      ['uv', 2],
    ]) {
      const attribute = geometry.getAttribute(name);
      if (attribute) batch[name].set(attribute.array.subarray(0, count * size), batch.offset * size);
    }
    batch.offset += count;
    geometry.dispose();
    object.removeFromParent();
    object.geometry.dispose();
  }
  for (const batch of batches.values()) {
    const material = batch.material;
    const geometry = new THREE.BufferGeometry();
    for (const [name, size] of [
      ['position', 3],
      ['normal', 3],
      ['uv', 2],
    ])
      geometry.setAttribute(name, new THREE.BufferAttribute(batch[name], size));
    geometry.computeBoundingSphere();
    surfaces.weather(material);
    const mesh = new THREE.Mesh(geometry, material);
    mesh.name = `batch:${materialName(material)}`;
    mesh.userData.layer = batch.layer;
    mesh.castShadow = ![
      materials.ground,
      materials.land,
      materials.water,
      materials.tidalWater,
      materials.bed,
      materials.plot,
    ].includes(material);
    mesh.receiveShadow = true;
    scene.add(mesh);
  }
  const tidalMeshes = [],
    floatingMeshes = [];
  scene.traverse((o) => {
    if (!o.isMesh) return;
    if (o.material === materials.tidalWater) tidalMeshes.push(o);
    if (o.material.userData.tidalFloat) floatingMeshes.push(o);
  });
  const applyTideState = (state) => {
    for (const mesh of tidalMeshes) {
      mesh.position.y = state.level - state.low;
      mesh.visible = state.level > state.low + 0.00001;
    }
    for (const mesh of floatingMeshes) mesh.position.y = state.level - state.low;
    if (!scene.userData.floodSimplifiedWater && scene.userData.tideObjects?.waterOffsets[0] !== state.level - state.low)
      renderer.shadowMap.needsUpdate = true;
    surfaces.setTideLevel(state.level);
    scene.userData.tideObjects = {
      waterOffsets: tidalMeshes.map((o) => o.position.y),
      bargeOffsets: floatingMeshes.map((o) => o.position.y),
    };
  };
  tide = tideControls({ config: data.riverNetwork.tide, render: update, apply: applyTideState });
  const floodWaterMeshes = [];
  scene.traverse((object) => {
    if (object.isMesh && [materials.water, materials.tidalWater].includes(object.material))
      floodWaterMeshes.push([object, object.material]);
  });
  const plainFloodWater = new THREE.MeshStandardMaterial({ color: 0x477987, roughness: 0.9 });
  setFloodWater = (levelODN) => {
    if (tide.snapshot().playing) tide.pause();
    const current = tide.snapshot();
    // Depth colours carry the information in this experiment. Avoid rendering
    // the whole district twice more for reflections at each slider movement.
    scene.userData.floodSimplifiedWater = levelODN !== null;
    for (const [mesh, original] of floodWaterMeshes) mesh.material = levelODN === null ? original : plainFloodWater;
    applyTideState(
      levelODN === null
        ? current
        : { ...current, level: levelODN - data.elevation.meta.verticalReference.odnMinusSceneYMetres }
    );
  };
  // Only object transforms change during the tide: release the CPU copy of every vertex
  // buffer once it has been uploaded, roughly halving the retained memory.
  const releaseArray = function () {
    this.array = null;
  };
  if (!exportMode)
    scene.traverse((object) => {
      if (!object.isMesh) return;
      for (const attribute of Object.values(object.geometry.attributes)) attribute.onUpload(releaseArray);
      object.geometry.index?.onUpload(releaseArray);
    });
  regionalPlans = regionalFootprints({
    THREE,
    scene,
    data: data.regionalFootprints,
    level: terrain.level,
    landMaterial: materials.land,
    existingGround: data.riverNetwork.baseGround,
    regionalGround: data.riverSystem.regionalGround,
    landscapeActive: Boolean(data.mainLandscape),
    lite,
    render: () => requestAnimationFrame(update),
  });
  host.append(renderer.domElement);
  renderer.domElement.setAttribute('aria-hidden', 'true');
  renderer.domElement.addEventListener('webglcontextlost', (e) => {
    e.preventDefault();
    stopWalking();
    tide?.pause();
    renderer = null;
    $('#tide-level').disabled = $('#tide-play').disabled = true;
    $$('[data-walk],[data-side]').forEach((b) => (b.disabled = true));
    host.classList.remove('is-ready');
    stall('The 3D view paused. Reload to restore it. You can still read the stories and open the location map.');
    update();
  });
  const resize = () => {
    if (!renderer) return;
    const { width, height } = host.getBoundingClientRect();
    renderer.setSize(width, height, false);
    camera.aspect = width / height;
    update();
  };
  new ResizeObserver(resize).observe(host);
  resize();
}

// Lighter terrain for the lite tier: sample every `stride`-th grid cell. Bounds are kept,
// so world-space lookups, the river-bed texture and the sediment mask stay aligned.
function downsampleTerrain(t, stride) {
  const width = Math.ceil(t.width / stride),
    height = Math.ceil(t.height / stride);
  const levels = new Float32Array(width * height),
    landcover = new Uint8Array(width * height),
    properties = new Uint8Array(width * height * 4);
  for (let z = 0; z < height; z++)
    for (let x = 0; x < width; x++) {
      const src = Math.min(t.height - 1, z * stride) * t.width + Math.min(t.width - 1, x * stride),
        dst = z * width + x;
      levels[dst] = t.levels[src];
      landcover[dst] = t.landcover[src];
      properties.set(t.properties.subarray(src * 4, src * 4 + 4), dst * 4);
    }
  return { ...t, width, height, step: t.step * stride, levels, landcover, properties };
}

/* ---------- Loading with progress ---------- */
const loadingText = $('#loading-text'),
  loadingFill = $('#loading-fill'),
  loadingBox = $('#loading');
const progress = { loaded: 0, total: 0 };
function paint(fraction) {
  const f = fraction ?? Math.min(0.92, progress.loaded / Math.max(progress.total, 1));
  loadingFill.style.width = `${Math.max(4, Math.round(f * 100))}%`;
}
function stall(message) {
  loadingText.textContent = message;
  loadingBox.classList.add('is-stalled');
}
async function load(url, type = 'json') {
  const response = await fetch(window.sceneAssetUrl?.(url) || url, { cache: 'no-store' });
  if (!response.ok) throw new Error(`${url} unavailable`);
  const declared = Number(response.headers.get('content-length')) || 0;
  progress.total += declared;
  if (!response.body) return type === 'json' ? response.json() : response.arrayBuffer();
  const reader = response.body.getReader(),
    chunks = [];
  let received = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    chunks.push(value);
    received += value.length;
    progress.loaded += value.length;
    paint();
  }
  if (!declared) progress.total += received;
  const bytes = new Uint8Array(received);
  let offset = 0;
  for (const chunk of chunks) {
    bytes.set(chunk, offset);
    offset += chunk.length;
  }
  return type === 'json' ? JSON.parse(new TextDecoder().decode(bytes)) : bytes.buffer;
}

update();
try {
  loadingText.textContent = 'Fetching the ground plan';
  const [
    groundPlan,
    terrain,
    southwest,
    infrastructureData,
    trees,
    network,
    factories,
    frontages,
    yards,
    housing,
    regional,
    stationPlan,
    elevation,
    system,
    mainLandscape,
    tramRailsData,
  ] = await Promise.all([
    load('./data/ground-plan.json'),
    loadTerrain(load),
    load('./data/southwest-context.json'),
    load('./data/infrastructure.json'),
    load('./data/mapped-trees.json'),
    loadRiverNetwork(load),
    load('./data/factory-buildings.json'),
    load('./data/high-street-frontages.json'),
    load('./data/factory-yards.json'),
    load('./data/housing-detail.json'),
    load('./data/regional-footprints/index.json'),
    load('./data/abbey-station-plan.json'),
    loadHistoricElevation(load),
    loadRiverSystem(load),
    loadMainLandscape(load),
    load('./data/tram-rails.json'),
  ]);
  data = groundPlan;
  data.terrain = terrain;
  data.southwest = southwest;
  data.infrastructure = infrastructureData;
  data.mappedTrees = trees;
  data.riverNetwork = network;
  data.factoryBuildings = factories;
  data.highStreetFrontages = frontages;
  data.factoryYards = yards;
  data.housingDetail = housing;
  data.regionalFootprints = regional;
  data.stationPlan = stationPlan;
  data.tramRails = tramRailsData;
  data.elevation = elevation;
  applyHistoricElevation(data);
  data.riverSystem = system;
  applyRiverSystem(data);
  applyMainLandscape(data, mainLandscape);
  // Ground lookups outside the detailed tile read the meshes that are actually drawn, so objects,
  // fills and bank toes meet the surface the reader sees rather than a source grid it replaced.
  data.drawnGround = createGroundSampler([
    data.elevation && { positions: data.elevation.grids.extension },
    data.mainLandscape && { positions: data.mainLandscape.grids.groundMesh },
    { positions: data.riverNetwork.positions, indices: data.riverNetwork.indices },
    { positions: data.riverSystem.positions, indices: data.riverSystem.indices },
  ]);
  data.neighbourhood.terraces = housing.rows.filter((r) => r.group === 'district');
  data.southwest.rows = housing.rows.filter((r) => r.group === 'southwest');
  walker = createDistrictNavigator(data.neighbourhood.sewer);
  populateDestinations();
  buildPlan($('#plan'), { viewBox: '-1650 -1350 2200 2950' });
  buildPlan($('#minimap-plan'), { viewBox: '-1650 -1350 2950 2950', labels: false, markerRadius: 22, strokeScale: 3 });
  paint(0.95);
  loadingText.textContent = 'Building the landscape';
  await new Promise((resolve) => setTimeout(resolve, 40)); // let the label paint before the synchronous build
  try {
    buildScene();
    paint(1);
    if (exportMode) {
      const { installSceneExport } = await import('./scene-export.js');
      installSceneExport({ THREE, scene, origin: data.origin, revision: window.sceneRevision });
    }
    $$('[data-walk],[data-side],#travel-toggle,#destination').forEach((b) => (b.disabled = false));
    // First frame is drawn by resize(); reveal it over the poster, then ease into the hero view.
    requestAnimationFrame(() => {
      host.classList.add('is-ready');
      pendingArrival = false;
      const requestedView = destinations.get(new URLSearchParams(location.search).get('view'));
      if (requestedView) {
        $('#destination').value = requestedView.id;
        travelTo(requestedView);
      } else if (
        !new URLSearchParams(location.search).has('film') &&
        !new URLSearchParams(location.search).has('river-review') &&
        !new URLSearchParams(location.search).has('flood') &&
        !new URLSearchParams(location.search).has('rivers')
      ) {
        goTo(poses[activeStop] || poses.hero, activeStop === 'hero' ? 4200 : 1800);
      }
      setTimeout(() => $('#poster')?.remove(), 2400);
    });
    if (new URLSearchParams(location.search).has('river-review')) {
      window.riverNetworkReview = ({ position, target, fov = 48 }) => {
        interruptTween();
        stopWalking();
        stepObserver.disconnect();
        const view = new THREE.PerspectiveCamera(
          fov,
          renderer.domElement.width / renderer.domElement.height,
          0.15,
          5000
        );
        view.position.fromArray(position);
        view.lookAt(new THREE.Vector3(...target));
        surfaces.reflect(view);
        renderer.render(scene, view);
        return renderer.domElement.toDataURL('image/png');
      };
    }
    // The optional film uses the same scene, with its own unrestricted camera.
    // Keep the ordinary bridge controls and reader experience unchanged.
    if (new URLSearchParams(location.search).has('rivers')) {
      interruptTween();
      stopWalking();
      stepObserver.disconnect();
      pendingArrival = false;
      installRiverExplorer({ views: [...destinations.values()], travel: travelTo });
    } else if (new URLSearchParams(location.search).has('flood')) {
      if (data.elevation?.meta.epoch !== '1900') throw Error('Landscape flooding requires the 1900 terrain');
      interruptTween();
      stopWalking();
      stepObserver.disconnect();
      pendingArrival = false;
      const { installLandscapeFlood } = await import('./landscape-flood.js');
      await installLandscapeFlood({ THREE, scene, load, render: update, travel: travelTo, setWater: setFloodWater });
    } else if (new URLSearchParams(location.search).has('film')) {
      const { installFilm } = await import('./social-film.js');
      await installFilm({
        THREE,
        renderer,
        scene,
        surfaces,
        stop: () => {
          interruptTween();
          stopWalking();
          stepObserver.disconnect();
          pendingArrival = false;
        },
      });
    }
  } catch (error) {
    renderer = null;
    stall(
      'This browser could not open the 3D view. The still image stays, and you can explore the location map and read the stories.'
    );
    console.warn('3D view unavailable:', error.stack || error.message);
  }
  update();
} catch (error) {
  stall(
    'The landscape data could not load. Serve this folder through a local web server, then reload. The stories below are still available.'
  );
  $('#map-open').disabled = true;
  $('#map-open-2').disabled = true;
  $('#minimap').disabled = true;
  console.warn(error.message);
}
