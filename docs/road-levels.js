// Road observations remain separate from field-ground interpolation.
export function roadProfileHeight(x, z, profile, epoch) {
  if (!profile || profile.geometryEpoch !== epoch) return null;
  let best = Infinity,
    along = 0,
    total = 0;
  for (let i = 1; i < profile.route.length; i++) {
    const a = profile.route[i - 1],
      b = profile.route[i],
      dx = b[0] - a[0],
      dz = b[1] - a[1],
      length = Math.hypot(dx, dz);
    const t = Math.max(0, Math.min(1, ((x - a[0]) * dx + (z - a[1]) * dz) / (length * length)));
    const d = Math.hypot(x - a[0] - t * dx, z - a[1] - t * dz);
    if (d < best) {
      best = d;
      along = total + t * length;
    }
    total += length;
  }
  if (best > profile.widthMetres / 2 + profile.shoulderMetres + 0.01) return null;
  const cs = profile.controls;
  if (along <= cs[0].distance) return cs[0].heightScene;
  for (let i = 1; i < cs.length; i++)
    if (along <= cs[i].distance) {
      const t = (along - cs[i - 1].distance) / (cs[i].distance - cs[i - 1].distance);
      return cs[i - 1].heightScene * (1 - t) + cs[i].heightScene * t;
    }
  return cs.at(-1).heightScene;
}
