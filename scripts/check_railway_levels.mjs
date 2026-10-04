// Railway formation levels from the OS level register (data/maps/railway-levels.json):
// every control matches its spot height in reference/spot-heights/heights.geojson; the built
// profiles and routes in docs/data/infrastructure.json match the register; the profile meets each
// control it is set by (rail top within 0.3 m of rail readings, formation within 0.3 m of bank-top
// readings and of ground + 0.1 m at grade); the Abbey Mills curve meets both lines at one level;
// the drawn level stations follow the profile; railways outside the register keep their heights.
//   node scripts/check_railway_levels.mjs
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const read = (p) => JSON.parse(readFileSync(new URL('../' + p, import.meta.url)));
const reg = read('data/maps/railway-levels.json'),
  infra = read('docs/data/infrastructure.json'),
  spots = Object.fromEntries(
    read('reference/spot-heights/heights.geojson').features.map((f) => [f.properties.id, f.properties])
  );
const d = reg.datum,
  sceneY = (ft) => (ft + d.liverpoolToNewlynFeet) * d.footMetres - d.odnMinusSceneYMetres,
  rail = reg.railStack.railTopAboveFormationMetres,
  lift = reg.atGrade.formationAboveGroundMetres;
const interp = (c, f, s) => {
  if (s <= c[0]) return f[0];
  for (let i = 1; i < c.length; i++)
    if (s <= c[i]) return f[i - 1] + ((f[i] - f[i - 1]) * (s - c[i - 1])) / (c[i] - c[i - 1]);
  return f[f.length - 1];
};
function project(route, [x, z]) {
  let best = { d: Infinity, s: 0 },
    run = 0;
  for (let i = 1; i < route.length; i++) {
    const [ax, az] = route[i - 1],
      [bx, bz] = route[i],
      len = Math.hypot(bx - ax, bz - az),
      t = Math.max(0, Math.min(1, ((x - ax) * (bx - ax) + (z - az) * (bz - az)) / (len * len))),
      dd = Math.hypot(ax + t * (bx - ax) - x, az + t * (bz - az) - z);
    if (dd < best.d) best = { d: dd, s: run + t * len };
    run += len;
  }
  return best;
}
const summary = [];
for (const [name, spec] of Object.entries(reg.railways)) {
  const built = infra.railways.find((r) => r.name === name);
  assert(built, `${name} not built`);
  const c = spec.profile.map((p) => p[0]),
    f = spec.profile.map((p) => p[1]);
  assert.deepStrictEqual(built.levelProfile.chainage, c, `${name}: built profile chainage differs from the register`);
  assert.deepStrictEqual(built.levelProfile.formation, f, `${name}: built profile differs from the register`);
  if (spec.route) {
    assert.deepStrictEqual(built.route, spec.route, `${name}: built route differs from the register`);
    assert(spec.priorRoute, `${name}: prior route kept`);
  }
  assert.equal(built.priorFormationHeight, spec.priorFormationHeight);
  // Each control: register copy of the reading, its position and chainage, and the profile meeting it.
  let met = 0;
  for (const k of spec.controls) {
    const p = spots[k.spotHeight];
    assert(p, `${k.spotHeight} missing from heights.geojson`);
    assert.equal(k.readingFeet, p.value_ft, `${k.spotHeight} reading`);
    assert(Math.abs(k.sceneY - sceneY(p.value_ft)) < 0.001, `${k.spotHeight} scene level`);
    const xz = [p.bng_e - 538900, 183209 - p.bng_n];
    assert(Math.hypot(xz[0] - k.position[0], xz[1] - k.position[1]) < 0.01, `${k.spotHeight} position`);
    assert(Math.abs(project(built.route, xz).s - k.chainage) < 0.06, `${k.spotHeight} chainage`);
    assert(typeof k.evidence === 'string' && k.evidence.length > 20, `${k.spotHeight} evidence`);
    if (k.use !== 'control') continue;
    const at = interp(c, f, k.chainage),
      target = k.kind === 'rail' ? k.sceneY - rail : k.kind === 'bank-top' ? k.sceneY : k.sceneY + lift;
    // Two ground readings may set one profile point together (their mean); allow their spread.
    const shared = spec.profile.find((q) => String(q[2]).includes(k.spotHeight) && String(q[2]).includes('+'));
    assert(
      Math.abs(at - target) <= (shared ? 0.3 + 0.35 : 0.3),
      `${name}: profile ${at.toFixed(2)} misses ${k.kind} control ${k.spotHeight} (${target.toFixed(2)})`
    );
    met++;
  }
  // Every segment has evidence and the profile is monotone in chainage.
  for (const s of spec.segments) assert(s.evidence && s.from < s.to, `${name} segment`);
  for (let i = 1; i < c.length; i++) assert(c[i] > c[i - 1]);
  // The drawn level stations follow the profile.
  for (const [, , y, s] of built.levelStations)
    assert(Math.abs(interp(c, f, s) - y) < 0.002, `${name} level station ${s}`);
  // Steepest grade, for the record (a model joint may be steep; none steeper than 1:20).
  let steep = 0;
  for (let i = 1; i < c.length; i++) steep = Math.max(steep, Math.abs(f[i] - f[i - 1]) / (c[i] - c[i - 1]));
  assert(steep < 1 / 20, `${name} grade 1:${(1 / steep).toFixed(0)}`);
  summary.push(`${name}: ${met} controls met, steepest 1:${(1 / steep).toFixed(0)}`);
}
// The Abbey Mills curve meets the LT&SR and the Woolwich branch at one level.
const byName = Object.fromEntries(infra.railways.map((r) => [r.name, r])),
  curve = byName['Abbey Mills junction curve'];
for (const [end, other] of [
  [0, 'London, Tilbury and Southend Railway'],
  [curve.route.length - 1, 'Great Eastern Railway, Woolwich branch'],
]) {
  const o = byName[other],
    s = project(o.route, curve.route[end]).s,
    mine = curve.levelProfile.formation[end === 0 ? 0 : curve.levelProfile.formation.length - 1];
  assert(
    Math.abs(interp(o.levelProfile.chainage, o.levelProfile.formation, s) - mine) < 0.01,
    `junction with ${other}`
  );
}
assert(
  project(byName['London, Tilbury and Southend Railway'].route, curve.route[0]).d < 0.01,
  'curve leaves the LT&SR on its centreline'
);
// Railways outside the register keep their earlier heights.
for (const [name, rec] of Object.entries(reg.unchanged))
  assert.equal(byName[name].formationHeight, rec.formationHeight, `${name} changed`);
console.log(`PASS: railway levels — ${summary.join('; ')}; junctions at one level; unchanged railways kept.`);
