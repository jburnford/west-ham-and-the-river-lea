const $ = (id) => document.getElementById(id),
  canvas = $('map'),
  ctx = canvas.getContext('2d');
const response = await fetch('./data/lower-lea-region/index.json');
if (!response.ok) throw Error('Regional data unavailable');
const data = await response.json(),
  bounds = data.reviewBoundsBNG;
const [audit, trial, landscape] = await Promise.all(
  ['elevation-audit.json', 'elevation-trial.json', 'landscape-1900.json'].map(async (name) => {
    const r = await fetch('./data/lower-lea-region/' + name);
    if (!r.ok) throw Error('Elevation review unavailable: ' + name);
    return r.json();
  })
);
const landscapeRaw = await fetch('./data/lower-lea-region/' + landscape.heightFile);
const landscapeKindsRaw = await fetch('./data/lower-lea-region/' + landscape.kindFile);
if (!landscapeRaw.ok || !landscapeKindsRaw.ok) throw Error('Landscape data unavailable');
const landscapeHeights = new Float32Array(await landscapeRaw.arrayBuffer()),
  landscapeKinds = new Uint8Array(await landscapeKindsRaw.arrayBuffer());
if (landscapeHeights.length !== landscape.width * landscape.height || landscapeKinds.length !== landscapeHeights.length)
  throw Error('Landscape raster size mismatch');
const landscapeImage = new Image();
landscapeImage.src = './data/lower-lea-region/' + landscape.preview;
await landscapeImage.decode();
const landscapeEvidence = new Image();
landscapeEvidence.src = './data/lower-lea-region/' + landscape.evidencePreview;
await landscapeEvidence.decode();
const auditById = new Map(audit.records.map((r) => [r.id, r]));
const [groundDistance, surfaceDistance, trialHeights] = await Promise.all(
  [audit.grid.distanceFile, audit.grid.surfaceDistanceFile, trial.heightFile].map(async (name) => {
    const r = await fetch('./data/lower-lea-region/' + name);
    if (!r.ok) throw Error('Elevation raster unavailable: ' + name);
    return new Float32Array(await r.arrayBuffer());
  })
);
if (
  groundDistance.length !== audit.grid.width * audit.grid.height ||
  surfaceDistance.length !== groundDistance.length ||
  trialHeights.length !== trial.width * trial.height
)
  throw Error('Elevation raster size mismatch');
const [coverageImage, trialImage] = await Promise.all(
  [audit.grid.preview, trial.preview].map(async (name) => {
    const i = new Image();
    i.src = './data/lower-lea-region/' + name;
    await i.decode();
    return i;
  })
);
const raw = await fetch('./data/lower-lea-region/' + data.terrain.heightFile);
if (!raw.ok) throw Error('Regional height raster unavailable');
const heights = new Float32Array(await raw.arrayBuffer());
if (heights.length !== data.terrain.width * data.terrain.height) throw Error('Regional terrain size mismatch');
const relief = new Image();
relief.src = './data/lower-lea-region/' + data.terrain.preview;
await relief.decode();
const rivers = data.layers.Lower_River_Lea;
let view = [...bounds],
  selected = '',
  selectedSite = null,
  drag = null;
const review = data.connectionReview;
const reviewLabels = {
  'provisional-mapping-seam': 'provisional mapping seam',
  'navigation-interface-review': 'navigation interface',
  'mapped-navigation-junction': 'mapped open junction',
  'mill-site-review': 'mill passage review',
  'channel-junction-review': 'channel join review',
  'mapped-weir-review': 'mapped weir',
  'mapped-lock-passage': 'mapped lock passage',
};
const reviewColour = (g) =>
  ['provisional-mapping-seam', 'mapped-navigation-junction'].includes(g.reviewCategory)
    ? '#24754d'
    : g.navigationInterface
      ? '#973b68'
      : '#d36821';
const point = (p) => [((p[0] - view[0]) / (view[2] - view[0])) * 900, ((view[3] - p[1]) / (view[3] - view[1])) * 900];
const world = (x, y) => [view[0] + (x / 900) * (view[2] - view[0]), view[3] - (y / 900) * (view[3] - view[1])];
function fit(b, padding = 0.12) {
  const cx = (b[0] + b[2]) / 2,
    cy = (b[1] + b[3]) / 2,
    span = Math.max(b[2] - b[0], b[3] - b[1], 200) * (1 + padding);
  view = [cx - span / 2, cy - span / 2, cx + span / 2, cy + span / 2];
  draw();
}
function polygon(rings, fill, stroke, width = 1) {
  ctx.beginPath();
  for (const ring of rings)
    ring.forEach((p, i) => {
      const q = point(p);
      i ? ctx.lineTo(...q) : ctx.moveTo(...q);
    });
  if (fill) {
    ctx.fillStyle = fill;
    ctx.fill('evenodd');
  }
  if (stroke) {
    ctx.strokeStyle = stroke;
    ctx.lineWidth = width;
    ctx.stroke();
  }
}
function layer(name, fill, stroke) {
  for (const f of data.layers[name]) for (const p of f.polygons) polygon(p, fill, stroke);
}
const usable = (m) =>
  ['reviewed-ground', 'candidate-ground', 'reviewed-road', 'candidate-road'].includes(m.auditStatus);
function shownMarks() {
  return audit.records.filter((m) => {
    if ($('all-marks').checked) return true;
    const filter = $('surface-filter').value;
    return filter === 'ground'
      ? m.surfaceFamily === 'ground'
      : filter === 'road'
        ? m.surfaceFamily === 'road'
        : filter === 'review'
          ? ['ground-needs-review', 'road-needs-review', 'inferred-ground', 'inferred-road'].includes(m.auditStatus)
          : usable(m);
  });
}
function draw() {
  ctx.fillStyle = '#eeece3';
  ctx.fillRect(0, 0, 900, 900);
  const a = point([bounds[0], bounds[3]]),
    b = point([bounds[2], bounds[1]]);
  if ($('relief').checked) {
    ctx.imageSmoothingEnabled = false;
    ctx.drawImage(relief, ...a, b[0] - a[0], b[1] - a[1]);
  }
  const elevationView = $('elevation-view').value;
  if (elevationView !== 'off') {
    ctx.imageSmoothingEnabled = false;
    ctx.drawImage(
      elevationView === 'landscape'
        ? landscapeImage
        : elevationView === 'landscape-evidence'
          ? landscapeEvidence
          : elevationView === 'coverage'
            ? coverageImage
            : trialImage,
      ...a,
      b[0] - a[0],
      b[1] - a[1]
    );
  }
  ctx.strokeStyle = '#a2ad96';
  ctx.lineWidth = 1;
  ctx.strokeRect(...a, b[0] - a[0], b[1] - a[1]);
  if ($('context').checked) layer('TQ_TidalWater', 'rgba(130,145,152,.3)', '#89989d');
  if ($('first').checked) layer('Water_First_Series', null, '#976544');
  if ($('revision').checked) layer('Water_1895', null, '#a35699');
  layer('Lower_River_Lea', '#76bcc7', '#246978');
  ctx.setLineDash([4, 3]);
  for (const exclusion of audit.terrainExclusions) polygon([exclusion.polygonBNG], null, '#5a7882', 1.3);
  ctx.setLineDash([]);
  if (selectedSite)
    for (const f of rivers.filter((r) => selectedSite.reachIds.includes(r.id)))
      for (const p of f.polygons) polygon(p, 'rgba(185,97,67,.4)', '#963f32', 2);
  if (selected) {
    const f = rivers.find((r) => r.id === selected);
    for (const p of f.polygons) polygon(p, 'rgba(255,227,123,.6)', '#784117', 3);
  }
  const cb = data.currentFloodBoundsBNG,
    ca = point([cb[0], cb[3]]),
    cd = point([cb[2], cb[1]]);
  ctx.strokeStyle = '#784a9b';
  ctx.setLineDash([9, 5]);
  ctx.lineWidth = 2;
  ctx.strokeRect(...ca, cd[0] - ca[0], cd[1] - ca[1]);
  ctx.setLineDash([]);
  if ($('marks').checked)
    for (const m of shownMarks()) {
      const p = point(m.positionBNG);
      ctx.fillStyle = m.auditStatus.startsWith('reviewed-')
        ? '#155538'
        : !usable(m)
          ? '#ba4040'
          : m.surfaceFamily === 'road'
            ? '#5952a2'
            : '#b77627';
      ctx.beginPath();
      ctx.arc(...p, m.auditStatus.startsWith('reviewed-') ? 4 : 2.4, 0, Math.PI * 2);
      ctx.fill();
    }
  if ($('gaps').checked)
    for (const g of [
      ...data.topology.nearConnections,
      ...review.navigationInterfaces.filter((g) => g.distanceMetres <= data.contactToleranceMetres),
    ]) {
      const p = g.routeBNG.map(point);
      ctx.strokeStyle = reviewColour(g);
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(...p[0]);
      ctx.lineTo(...p[1]);
      ctx.stroke();
      ctx.beginPath();
      ctx.arc((p[0][0] + p[1][0]) / 2, (p[0][1] + p[1][1]) / 2, 6, 0, Math.PI * 2);
      ctx.stroke();
    }
  if ($('gaps').checked)
    for (const route of review.structureRoutes) {
      const p = route.routeBNG.map(point);
      ctx.strokeStyle = '#963f32';
      ctx.lineWidth = 3;
      ctx.setLineDash([4, 3]);
      ctx.beginPath();
      ctx.moveTo(...p[0]);
      ctx.lineTo(...p[1]);
      ctx.stroke();
      ctx.setLineDash([]);
    }
  if ($('gaps').checked)
    for (const site of review.controlSites.filter((s) => s.positionBNG)) {
      const p = point(site.positionBNG);
      ctx.fillStyle = '#963f32';
      ctx.fillRect(p[0] - 4, p[1] - 4, 8, 8);
      if (selectedSite?.id === site.id) {
        ctx.font = '15px system-ui';
        ctx.fillText(site.name, p[0] + 9, p[1] - 9);
      }
    }
  ctx.fillStyle = '#243f36';
  ctx.font = '19px system-ui';
  ctx.fillText('N ↑', 24, 34);
  const span = view[2] - view[0],
    metres = span > 3500 ? 1000 : span > 1200 ? 500 : 100;
  const length = (metres / span) * 900;
  ctx.fillStyle = 'rgba(255,252,243,.85)';
  ctx.fillRect(16, 844, length + 24, 44);
  ctx.strokeStyle = '#294339';
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.moveTo(28, 857);
  ctx.lineTo(28 + length, 857);
  ctx.stroke();
  ctx.font = '15px system-ui';
  ctx.fillStyle = '#294339';
  ctx.fillText(`${metres} m`, 28, 878);
  $('elevation-notice').textContent =
    elevationView === 'landscape'
      ? 'Working 1900 landscape: regional 1848 marsh estimates underlie separate later streets, yards, banks and railway/sewer formations. Beyond the marsh envelope, provisional relief can retain later earthworks. Water and structure exclusions have no ground or bed estimate.'
      : elevationView === 'landscape-evidence'
        ? 'Landscape evidence: green is historical interpolation, dark green is a control cell, mint is the regional 1848 marsh estimate, light green is a local marsh estimate, ochre is a local bank or cottage garden, brown is a street or yard, gold is a continuous river/canal bank profile, purple is railway/sewer formation, grey-green is the approximate marsh-edge blend, tan is an estimate near historical anchors, rose is a distant or disconnected modern-relief estimate. Grey has no source coverage.'
        : elevationView === 'coverage'
          ? 'Ground and street evidence: green within 100 m, pale green 100–250 m, tan 250–500 m, rose over 500 m from a usable candidate. Proximity can cross barriers; it is not a height-accuracy estimate.'
          : elevationView === 'trial'
            ? '1900 ground + street interpolation experiment. Grey areas have no supported estimate. Water, reviewed canal/structure areas and triangles longer than 500 m are excluded. This trial has not changed the 3D terrain or flood solver.'
            : 'The coloured ground is 2003 terrain, before historical correction. This page does not simulate regional flooding. The rectangle is a review window, not a flood boundary.';
  window.lowerLeaRegionReview = {
    ready: true,
    view: [...view],
    selected,
    selectedSite: selectedSite?.id || null,
    connectionReview: review.counts,
    summary: data.summary,
    visibleMarks: $('marks').checked ? shownMarks().length : 0,
    terrainYear: data.terrain.date,
    historicalDEM: data.terrain.historicalDEM,
    elevationView,
    audit: audit.summary,
    trial: trial.counts,
    landscape: { landAreaKm2: landscape.landAreaKm2, counts: landscape.counts },
    terrainExclusions: audit.terrainExclusions.length,
  };
}
function zoom(factor, anchor = world(450, 450)) {
  const span = Math.max(250, Math.min(18000, (view[2] - view[0]) * factor)),
    fraction = [(anchor[0] - view[0]) / (view[2] - view[0]), (anchor[1] - view[1]) / (view[3] - view[1])];
  view = [
    anchor[0] - span * fraction[0],
    anchor[1] - span * fraction[1],
    anchor[0] + span * (1 - fraction[0]),
    anchor[1] + span * (1 - fraction[1]),
  ];
  draw();
}
function coords(e) {
  const r = canvas.getBoundingClientRect();
  return [((e.clientX - r.left) / r.width) * 900, ((e.clientY - r.top) / r.height) * 900];
}
function inspect(p) {
  const ix = Math.floor((p[0] - bounds[0]) / 10),
    iy = Math.floor((bounds[3] - p[1]) / 10);
  const h =
    ix >= 0 && iy >= 0 && ix < data.terrain.width && iy < data.terrain.height
      ? heights[iy * data.terrain.width + ix]
      : NaN;
  let text = `E ${p[0].toFixed(0)}, N ${p[1].toFixed(0)} · ${Number.isFinite(h) ? `2003 ground ${h.toFixed(2)} m ODN` : 'No 2003 height at this location'}.`;
  if ($('elevation-view').value === 'coverage') {
    const x = Math.floor((p[0] - bounds[0]) / audit.grid.cellSizeMetres),
      y = Math.floor((bounds[3] - p[1]) / audit.grid.cellSizeMetres),
      i = y * audit.grid.width + x;
    text =
      `E ${p[0].toFixed(0)}, N ${p[1].toFixed(0)}. ` +
      (x >= 0 && y >= 0 && x < audit.grid.width && y < audit.grid.height
        ? `Nearest ground/street candidate: ${surfaceDistance[i].toFixed(0)} m; ground alone: ${groundDistance[i].toFixed(0)} m (50 m grid).`
        : 'Outside evidence grid.');
  } else if (['landscape', 'landscape-evidence'].includes($('elevation-view').value)) {
    const i = iy * landscape.width + ix,
      inside = ix >= 0 && iy >= 0 && ix < landscape.width && iy < landscape.height;
    const v = inside ? landscapeHeights[i] : NaN;
    text = `E ${p[0].toFixed(0)}, N ${p[1].toFixed(0)} · ${Number.isFinite(v) ? `Working landscape ${v.toFixed(2)} m provisional ODN` : 'No landscape height'}. ${inside ? landscape.kindLegend[landscapeKinds[i]] : 'Outside landscape grid'}.`;
  } else if ($('elevation-view').value === 'trial') {
    const v = ix >= 0 && iy >= 0 && ix < trial.width && iy < trial.height ? trialHeights[iy * trial.width + ix] : NaN;
    text = `E ${p[0].toFixed(0)}, N ${p[1].toFixed(0)} · ${Number.isFinite(v) ? `Trial surface ${v.toFixed(2)} m provisional ODN` : 'No trial height (unsupported or mapped water)'}.`;
  }
  if ($('marks').checked) {
    const candidates = shownMarks()
      .map((m) => ({ m, d: Math.hypot(m.positionBNG[0] - p[0], m.positionBNG[1] - p[1]) }))
      .sort((a, b) => a.d - b.d);
    if (candidates[0]?.d < ((view[2] - view[0]) / 900) * 12) {
      const m = candidates[0].m;
      text += ` ${m.id}: ${m.value_ft} ft, ${m.datum}; ${m.setting || 'unknown setting'}, ${m.confidence}; ${m.auditStatus.replaceAll('-', ' ')}. ${m.survey_dates}. ${m.auditReasons.join('; ')}. ${m.surfaceReview?.review || m.notes || ''} ${m.sourceUseRestriction?.reason || ''}`;
    }
  }
  $('inspect').textContent = text;
}
canvas.addEventListener('pointerdown', (e) => {
  drag = { p: coords(e), view: [...view] };
  canvas.setPointerCapture(e.pointerId);
});
canvas.addEventListener('pointerup', () => (drag = null));
canvas.addEventListener('pointercancel', () => (drag = null));
canvas.addEventListener('pointermove', (e) => {
  const p = coords(e);
  if (drag) {
    const s = (drag.view[2] - drag.view[0]) / 900,
      dx = (p[0] - drag.p[0]) * s,
      dy = (p[1] - drag.p[1]) * s;
    view = [drag.view[0] - dx, drag.view[1] + dy, drag.view[2] - dx, drag.view[3] + dy];
    draw();
  }
  inspect(world(...p));
});
canvas.addEventListener(
  'wheel',
  (e) => {
    e.preventDefault();
    zoom(e.deltaY > 0 ? 1.15 : 1 / 1.15, world(...coords(e)));
  },
  { passive: false }
);
canvas.addEventListener('keydown', (e) => {
  if (['+', '=', '-', 'Home', 'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(e.key)) {
    e.preventDefault();
    if (e.key === 'Home') fit(bounds, 0);
    else if (['+', '=', '-'].includes(e.key)) zoom(e.key === '-' ? 1.3 : 1 / 1.3);
    else {
      const d = (view[2] - view[0]) * 0.1,
        x = e.key === 'ArrowLeft' ? -d : e.key === 'ArrowRight' ? d : 0,
        y = e.key === 'ArrowUp' ? d : e.key === 'ArrowDown' ? -d : 0;
      view = [view[0] + x, view[1] + y, view[2] + x, view[3] + y];
      draw();
    }
  }
});
for (const id of [
  'relief',
  'context',
  'revision',
  'first',
  'marks',
  'all-marks',
  'gaps',
  'elevation-view',
  'surface-filter',
])
  $(id).addEventListener('change', draw);
$('whole').onclick = () => fit(bounds, 0);
$('north').onclick = () => fit([535300, 184200, 539000, 186900]);
$('south').onclick = () => fit([537200, 180000, 541000, 183000]);
$('current').onclick = () => fit(data.currentFloodBoundsBNG, 0.3);
$('western').onclick = () => fit(audit.regionalSupplement.reviewAreas.western, 0);
$('marsh-lanes').onclick = () => fit(audit.regionalSupplement.reviewAreas.northern, 0);
$('eastern').onclick = () => fit(audit.regionalSupplement.reviewAreas.eastern, 0);
$('zoom-in').onclick = () => zoom(1 / 1.5);
$('zoom-out').onclick = () => zoom(1.5);
for (const r of rivers) {
  const o = document.createElement('option');
  o.value = r.id;
  o.textContent = `${r.name} · source ${r.sourceIndex}`;
  $('reach').append(o);
}
$('reach').onchange = () => {
  selectedSite = null;
  selected = $('reach').value;
  const r = rivers.find((r) => r.id === selected);
  if (!r) {
    $('selection').textContent = '';
    draw();
    return;
  }
  const points = r.polygons.flat(2);
  fit([
    Math.min(...points.map((p) => p[0])),
    Math.min(...points.map((p) => p[1])),
    Math.max(...points.map((p) => p[0])),
    Math.max(...points.map((p) => p[1])),
  ]);
  $('selection').textContent =
    `${r.name}: ${r.type || 'type unrecorded'}. ${r.repaired ? 'Geometry repaired on a copy; map review needed. ' : ''}Date attribution and hydraulic connections remain unverified.`;
};
const names = new Map(data.topology.nodes.map((n) => [n.id, n.name]));
function connectionButton(g, target) {
  const button = document.createElement('button');
  button.textContent = `${names.get(g.a)} ↔ ${names.get(g.b)} · ${g.distanceMetres.toFixed(1)} m · ${reviewLabels[g.reviewCategory] || 'review'}`;
  button.onclick = () => {
    selectedSite = null;
    selected = '';
    $('reach').value = '';
    const [a, b] = g.routeBNG;
    fit([
      Math.min(a[0], b[0]) - 100,
      Math.min(a[1], b[1]) - 100,
      Math.max(a[0], b[0]) + 100,
      Math.max(a[1], b[1]) + 100,
    ]);
    $('selection').textContent = g.reviewNote + ' Hydraulic passage is not yet assigned.';
  };
  $(target).append(button);
}
for (const g of data.topology.nearConnections) connectionButton(g, 'gap-list');
for (const g of review.navigationInterfaces) connectionButton(g, 'navigation-list');
for (const site of [...review.controlSites, ...review.networkAreas]) {
  const button = document.createElement('button');
  button.textContent = site.name;
  button.dataset.site = site.id;
  button.onclick = () => {
    selected = '';
    $('reach').value = '';
    selectedSite = site;
    const points = rivers.filter((r) => site.reachIds.includes(r.id)).flatMap((r) => r.polygons.flat(2));
    fit(
      site.positionBNG
        ? [site.positionBNG[0] - 120, site.positionBNG[1] - 120, site.positionBNG[0] + 120, site.positionBNG[1] + 120]
        : [
            Math.min(...points.map((p) => p[0])),
            Math.min(...points.map((p) => p[1])),
            Math.max(...points.map((p) => p[0])),
            Math.max(...points.map((p) => p[1])),
          ]
    );
    $('selection').textContent =
      `${site.name}: ${site.note} Highlight shows associated reaches, not the exact structure footprint. ${site.positionBNG ? 'Brown square: approximate site located on the georeferenced period map. ' : ''}No hydraulic capacity assigned.`;
  };
  $('control-list').append(button);
}
$('control-summary').textContent =
  `${review.counts.controlSites} mill, lock and gate sites to review; ${review.counts.navigationInterfaces} navigation interfaces, including mapped contacts. The western Bow Back mouth is a mapped open junction; no gate is inferred there. ${review.counts.provisionalMappingSeams} other tiny gaps accepted as provisional mapping seams. Dashed brown routes show the reviewed mill and lock connections. ${data.coreIntegration.connections.length} passages/seams now have geometry in the core reconstruction. Flow capacities remain uncalibrated; wider regional routes still need tracing.`;
if (!data.topology.nearConnections.length)
  $('gap-list').textContent =
    'No separate polygon parts within the 15 m search distance. Larger gaps and controlled contacts still need review.';
for (const r of data.repairs) {
  const p = document.createElement('p');
  p.textContent = `${r.source}, feature ${r.index}: derived-copy repair; area change ${r.areaChangeM2.toFixed(2)} m². Original preserved; map review required.`;
  $('repairs').append(p);
}
for (const c of review.periodComparisons) {
  const p = document.createElement('p');
  const name = review.controlSites.find((s) => s.id === c.siteId)?.name || 'Bow Back / Navigation mouth';
  p.textContent = `${name}. Earlier: ${c.earlierObservation} Later: ${c.laterObservation} ${c.inference}`;
  $('period-comparisons').append(p);
}
for (const finding of review.networkReview.findings) {
  const p = document.createElement('p');
  p.textContent = `${finding.observation} ${finding.action}`;
  $('network-review').append(p);
}
for (const text of data.nextWork) {
  const li = document.createElement('li');
  li.textContent = text;
  $('next').append(li);
}
$('summary').textContent =
  `${data.summary.reviewAreaKm2} km² review window · ${data.summary.primaryReaches} primary reaches · ${data.summary.geometricComponents} geometric contact groups · ${data.summary.nearConnections} nearby gaps to inspect. These are not hydraulic connectivity counts.`;
$('terrain-summary').textContent =
  `${data.terrain.validAreaPercent}% valid 2003 terrain in this window. ${audit.summary.observations.toLocaleString()} historical height records, including ${audit.summary.regionalSupplementObservations} regional gap readings and ${audit.summary.opusAddedObservations} reconciled Opus additions. ${data.summary.appliedFieldControls} field controls remain applied in the detailed core.`;
const ac = audit.summary,
  cc = ac.riverCorridorCoverage;
$('audit-summary').textContent =
  `${ac.usableGroundCandidates} ground + ${ac.usableRoadCandidates} street candidates. Within the 750 m river corridor, ${cc.groundAndRoadWithinMetresPercent['250']}% of sampled dry land lies within 250 m of a candidate (${cc.withinMetresPercent['250']}% using ground alone). ${ac.reviewedGround} ground observations have direct surface review; other candidates retain transcription and surface uncertainty.`;
$('landscape-summary').textContent =
  `Working landscape: ${landscape.landAreaKm2.toFixed(2)} km² of land, including ${landscape.counts['1'].areaKm2.toFixed(2)} km² of historical interpolation. The early-evidence marsh base covers ${landscape.regionalMarshBaseline.fullWeightAreaKm2.toFixed(2)} km², with separate later surface layers. Other areas use historical controls and provisional broad relief. Waterways and structure exclusions remain separate. The detailed scene and flood solver still use their existing surfaces.`;
const cv = trial.validation.bySurface;
$('trial-summary').textContent =
  `Trial support: ${trial.counts.sampledSupportAreaKm2.toFixed(2)} km². Held-out ground predictions: ${cv.ground.supportedPredictions}/${cv.ground.heldOut}, mean absolute error ${cv.ground.meanAbsoluteErrorMetres} m; streets: ${cv.road.supportedPredictions}/${cv.road.heldOut}, ${cv.road.meanAbsoluteErrorMetres} m. These test internal consistency, not historical accuracy. Dry-land embankments and joins remain to be reconciled.`;
for (const cell of audit.reviewPriorityCells.slice(0, 16)) {
  const button = document.createElement('button');
  button.textContent = `E${cell.boundsBNG[0]} N${cell.boundsBNG[1]} · ${(cell.beyond250mSampleAreaM2 / 1e6).toFixed(2)} km² sparse`;
  button.onclick = () => {
    selectedSite = null;
    selected = '';
    $('reach').value = '';
    fit(cell.boundsBNG, 0.2);
    $('selection').textContent =
      `${cell.action} ${cell.surfaceReviewIds.length} existing ground/street records to check. Source coverage: ${cell.sourceCoverageStatus.replaceAll('-', ' ')}. ${cell.cachedUnreadMosaics.length ? 'Cached maps with no completed reading or snapshot record: ' + cell.cachedUnreadMosaics.join(', ') : cell.mosaics.length ? 'Transcribed source mosaics: ' + cell.mosaics.join(', ') : 'Check period-map availability before extending the surface.'}`;
  };
  $('elevation-priorities').append(button);
}
for (const residual of trial.largeResidualReview) {
  const m = auditById.get(residual.id),
    button = document.createElement('button');
  button.dataset.observation = m.id;
  button.textContent = `${m.value_ft} ft ${m.surfaceFamily} · prediction error ${residual.errorMetres > 0 ? '+' : ''}${residual.errorMetres.toFixed(2)} m`;
  button.onclick = () => {
    selectedSite = null;
    selected = '';
    $('reach').value = '';
    const [e, n] = m.positionBNG;
    fit([e - 150, n - 150, e + 150, n + 150], 0);
    const checked = trial.targetedMapChecks.find((r) => r.id === m.id);
    $('selection').textContent =
      `${m.id}: observed ${m.value_ft} ft (${m.provisionalODNMetres.toFixed(2)} m provisional ODN); withheld prediction ${residual.predictedODNMetres.toFixed(2)} m. ${checked ? checked.decision : 'Keep the observed reading unless source review establishes an error.'} ${m.notes} Source: ${m.mosaics.join(', ')}.`;
  };
  $('elevation-outliers').append(button);
}
const requestedElevation = new URLSearchParams(location.search).get('elevation');
if (['off', 'coverage', 'trial', 'landscape', 'landscape-evidence'].includes(requestedElevation))
  $('elevation-view').value = requestedElevation;
$('inspect').textContent = 'Point to the ground or a height mark to inspect the source.';
fit(audit.regionalSupplement.reviewAreas[new URLSearchParams(location.search).get('area')] || bounds, 0);
