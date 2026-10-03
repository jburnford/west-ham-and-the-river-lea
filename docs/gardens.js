// Interpreted allotment divisions and crops; the mapped outer extent is retained.
import { createRandom } from './lib/prng.js';
export function plotPoint(plot, x, z) {
  const angle = ((plot.rotation || 0) * Math.PI) / 180,
    c = Math.cos(angle),
    s = Math.sin(angle);
  return [plot.x + x * c - z * s, plot.z + x * s + z * c];
}

export function gardens({ THREE, scene, materials: m, data, box, cylinder, level }) {
  const soils = ['#827159', '#77674f', '#918068', '#897963'].map((color) => {
    const material = m.plot.clone();
    material.color.set(color).multiplyScalar(0.5);
    material.map = null;
    material.bumpMap = null;
    material.userData.gardenSoil = true;
    return material;
  });
  const greens = ['#626d47', '#727855', '#586343'].map(
    (color) => new THREE.MeshStandardMaterial({ color, roughness: 1, side: THREE.DoubleSide })
  );
  const tar = m.roof.clone();
  tar.color.set('#4a4b44');
  let sheds = 0,
    planted = 0,
    fallow = 0,
    patches = 0;
  const surfaceSamples = [];
  // Tessellated surfaces follow both terrain grids instead of sitting on one
  // flat height picked at the plot centre. Keep every soil vertex above ground.
  function patch(plot, cx, cz, width, depth, material, offset = 0.045) {
    const geometry = new THREE.PlaneGeometry(width, depth, Math.ceil(width), Math.ceil(depth));
    geometry.rotateX(-Math.PI / 2);
    const p = geometry.getAttribute('position');
    for (let i = 0; i < p.count; i++) {
      let [x, z] = plotPoint(plot, cx + p.getX(i), cz + p.getZ(i));
      x += 0.055 * Math.sin(x * 2.3 + z * 1.7);
      z += 0.055 * Math.cos(x * 1.9 - z * 2.1);
      const ground = level(x, z);
      p.setXYZ(i, x, ground + offset, z);
      if (i % 17 === 0) surfaceSamples.push([x, z, ground + offset]);
    }
    geometry.computeVertexNormals();
    scene.add(new THREE.Mesh(geometry, material));
    patches++;
  }
  for (const [i, b] of data.neighbourhood.garden.beds.entries()) {
    const random = createRandom(b.seed || i + 1);
    const type = random();
    // Some plots rest; soil patches have walking space and varied divisions.
    if (type < 0.14) {
      fallow++;
      continue;
    }
    const head = b.shed ? 4 : 1.2,
      depth = b.depth - head - 1;
    const strips = b.width > 10 ? 3 : 2,
      gap = 0.6,
      width = (b.width - 1.4 - (strips - 1) * gap) / strips;
    for (let strip = 0; strip < strips; strip++) {
      const cx = -b.width / 2 + 0.7 + width / 2 + strip * (width + gap),
        cz = -head / 2;
      // Short cross paths divide a long plot into unequal cultivation patches.
      const split = 0.38 + random() * 0.22,
        d1 = depth * split - 0.35,
        d2 = depth * (1 - split) - 0.35;
      patch(b, cx, cz - (depth - d1) / 2, width, d1, soils[(i + strip) % soils.length]);
      patch(b, cx, cz + (depth - d2) / 2, width, d2, soils[(i + strip + 1) % soils.length]);
      if (type < 0.36) continue;
      const vertices = [],
        tri = (...points) => vertices.push(...points.flat());
      for (let row = -depth / 2 + 0.45; row < depth / 2 - 0.25; row += 0.85 + random() * 0.25) {
        if (Math.abs(row - (-depth / 2 + d1 + 0.35)) < 0.55) continue;
        for (let col = -width / 2 + 0.18; col < width / 2 - 0.1; col += 0.36 + random() * 0.16) {
          if (random() < 0.18) continue;
          const [x, z] = plotPoint(b, cx + col, cz + row),
            y = level(x, z) + 0.07;
          const radius = 0.1 + random() * 0.09,
            h = 0.07 + random() * 0.14;
          tri([x - radius, y, z], [x, y + h, z], [x + radius, y, z]);
          tri([x, y, z - radius], [x, y + h, z], [x, y, z + radius]);
          const r = radius * 1.3;
          tri([x - r, y + h * 0.65, z], [x, y + h, z + r], [x + r, y + h * 0.65, z]);
          tri([x + r, y + h * 0.65, z], [x, y + h, z - r], [x - r, y + h * 0.65, z]);
        }
      }
      const geometry = new THREE.BufferGeometry();
      geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
      geometry.computeVertexNormals();
      scene.add(new THREE.Mesh(geometry, greens[(i + strip) % greens.length]));
      planted++;
    }
    if (!b.shed) continue;
    const w = 2.3 + random() * 0.55,
      d = 2.6 + random() * 0.55,
      h = 1.6 + random() * 0.4;
    const [sx, sz] = plotPoint(b, -b.width / 2 + 2, b.depth / 2 - 2);
    const ground = Math.max(
      ...[-1, 1].flatMap((dx) => [-1, 1].map((dz) => level(sx + (dx * w) / 2, sz + (dz * d) / 2)))
    );
    const g = new THREE.Group();
    g.position.set(sx, ground + 0.035, sz);
    g.rotation.y = (-(b.rotation || 0) * Math.PI) / 180;
    scene.add(g);
    sheds++;
    box(g, 0, 0, 0, w, h, d, m.wood);
    box(g, -w * 0.2, 0.02, d / 2 + 0.03, 0.65, h * 0.83, 0.07, m.dark);
    box(g, w * 0.25, h * 0.48, d / 2 + 0.045, 0.4, 0.35, 0.05, m.window);
    const roof = box(g, 0, h, 0, w + 0.35, 0.11, d + 0.35, tar);
    roof.rotation.z = (i % 2 ? 1 : -1) * 0.1;
    for (let x = -w / 2 + 0.2; x < w / 2; x += 0.28) box(g, x, 0, d / 2 + 0.02, 0.025, h, 0.02, m.dark);
    cylinder(g, -w / 2 - 0.4, 0, d / 2 - 0.3, 0.22, 0.25, 0.6, m.wood, 8);
  }
  return {
    sheds,
    review: {
      plots: data.neighbourhood.garden.beds.length,
      patches,
      plantedStrips: planted,
      fallow,
      sheds,
      surfaceSamples,
    },
  };
}
