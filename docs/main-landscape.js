// The early marsh reconstruction, applied to the detailed industrial scene.
import { gridSample } from './historic-elevation.js';

export async function loadMainLandscape(load) {
  const query = new URLSearchParams(location.search);
  if (query.get('terrainEpoch') === 'baseline' || query.get('mainLandscape') === 'baseline') return null;
  const meta = await load('./data/main-landscape-1900.json');
  const entries = await Promise.all(
    Object.entries(meta.files).map(async ([key, file]) => [
      key,
      new Float32Array(await load(`./data/${file}`, 'buffer')),
    ])
  );
  const grids = Object.fromEntries(entries);
  for (const [key, values] of entries) if (!values.every(Number.isFinite)) throw Error(`Invalid main landscape ${key}`);
  const f = meta.field,
    field = {
      ...f,
      bounds: [f.bounds[0] + f.step / 2, f.bounds[1] + f.step / 2, f.bounds[2] - f.step / 2, f.bounds[3] - f.step / 2],
    };
  if (grids.level.length !== f.width * f.height || grids.weight.length !== grids.level.length)
    throw Error('Main landscape field dimensions differ');
  const weight = (x, z) =>
    x < f.bounds[0] || x > f.bounds[2] || z < f.bounds[1] || z > f.bounds[3]
      ? 0
      : gridSample(grids.weight, field, x, z);
  const level = (x, z, previous = -0.1) => previous + weight(x, z) * (gridSample(grids.level, field, x, z) - previous);
  return { meta, grids, weight, level };
}

// Premises ground at (x, z): the pad level, or, where the pad carries several OS yard readings
// (controls [x, z, y]), their inverse-distance surface (power 2, distances under 3 m counted as 3 m),
// exactly as scripts/os_ground_levels.py premises_level() draws the pad.
export function premisesLevel(pad, x, z) {
  if (!pad.controls || pad.controls.length < 2) return pad.groundSceneY;
  let total = 0,
    sum = 0;
  for (const [cx, cz, cy] of pad.controls) {
    const d = Math.max(3, Math.hypot(x - cx, z - cz)),
      w = 1 / (d * d);
    total += w;
    sum += w * cy;
  }
  return sum / total;
}

export function applyMainLandscape(data, landscape) {
  if (!landscape) return;
  if (data.elevation?.meta.epoch !== landscape.meta.epoch) throw Error('Main landscape epoch mismatch');
  const { meta, grids } = landscape;
  const replace = (positions, key, stride = 3) => {
    const heights = grids[key];
    if (heights.length !== positions.length / stride) throw Error(`Main landscape ${key} topology differs`);
    for (let i = 0; i < heights.length; i++) positions[i * stride + (stride === 3 ? 1 : 0)] = heights[i];
  };
  replace(data.terrain.levels, 'core', 1);
  replace(data.riverNetwork.positions, 'network');
  replace(data.riverSystem.positions, 'system');
  replace(data.riverSystem.faces, 'faces');
  replace(data.elevation.grids.extension, 'extension');
  data.riverNetwork.baseGround = meta.replacementBaseGround;
  data.riverSystem.regionalGround = meta.replacementRegionalGround;
  data.riverNetwork.retainingEdges.crestProfiles = meta.retainingEdgeCrests;
  for (const profile of meta.railwaySlopes) {
    const rail = data.infrastructure.railways.find((r) => r.name === profile.name);
    if (!rail || rail.embankment.length !== profile.heights.length)
      throw Error('Main landscape railway topology differs');
    rail.embankment.forEach((tri, i) => tri.forEach((v, j) => (v[1] = profile.heights[i][j])));
  }
  const premises = new Map(meta.siteGround.map((p) => [p.siteId, p]));
  // Objects traced outside their site's pad outline are seated on the ground drawn under them (outsideIds).
  const outside = new Set(meta.siteGround.flatMap((p) => (p.outsideIds ?? []).map((id) => `${p.siteId}:${id}`)));
  let seated = 0;
  const seat = (b) => {
    if (!b) return;
    const [x, z] = b.centre ?? [b.x, b.z];
    if (!Number.isFinite(x) || !Number.isFinite(z)) return;
    const pad = outside.has(`${b.siteId}:${b.id}`) ? undefined : premises.get(b.siteId),
      w = landscape.weight(x, z),
      seatY = b.id === undefined ? undefined : meta.seats?.[b.id];
    // Objects with a recorded seat stand on the median drawn ground under their footprint (build_main_landscape.py).
    if (seatY !== undefined) b.landscapeLift = seatY + 0.1;
    else b.landscapeLift = pad ? w * (premisesLevel(pad, x, z) + 0.1) : landscape.level(x, z) + 0.1;
    if (Math.abs(b.landscapeLift) > 0.001) seated++;
  };
  const n = data.neighbourhood;
  for (const b of [
    ...data.factoryBuildings.buildings,
    ...data.factoryBuildings.structures,
    ...data.factoryBuildings.holders,
    ...data.factoryStudies,
    ...(data.southwest?.industrialRanges ?? []),
    ...n.mappedFactories,
    ...n.holders,
    ...n.houses,
    ...data.housingDetail.rows,
    ...data.highStreetFrontages.buildings,
    ...data.stationPlan.supportingBuildings,
  ])
    seat(b);
  seat(data.stationPlan);
  seat(n.mill);
  landscape.review = {
    active: true,
    epoch: meta.epoch,
    replacements: meta.replacements,
    groundMeshVertices: meta.groundMeshVertices,
    seatedObjects: seated,
    premises: meta.siteGround.length,
    streetControls: meta.roadControlIds.length,
    continuousBanks: meta.continuousBanks,
    probes: meta.probes,
    railwayGradesRetained: true,
    sewerCrestRetained: true,
    floodReady: false,
  };
  data.mainLandscape = landscape;
}

export function mainLandscapeGround({ THREE, scene, material, landscape }) {
  if (!landscape) return;
  const positions = landscape.grids.groundMesh,
    geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  const uv = new Float32Array((positions.length / 3) * 2);
  for (let i = 0; i < positions.length / 3; i++) uv.set([positions[i * 3], positions[i * 3 + 2]], i * 2);
  geometry.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
  geometry.computeVertexNormals();
  const mesh = new THREE.Mesh(geometry, material);
  mesh.name = 'Regional marsh ground in industrial reconstruction';
  mesh.receiveShadow = true;
  scene.add(mesh);
}
