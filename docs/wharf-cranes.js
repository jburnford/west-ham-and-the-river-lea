// Wharf and yard cranes at the OS five-foot crane symbols. Data: docs/data/wharf-cranes.json,
// built from data/maps/os-cranes.json by scripts/build_wharf_cranes.py. The OS gives position
// only; the form (stone base, iron post, inclined jib, tie rods, winch) is one type-based
// interpretation of a hand-worked iron crane, and the jib direction is chosen by the builder.

// Crane parts in local metres: x along the jib, y up, z across. Returns [kind, matrix-ready spec].
export function craneParts(form) {
  const { baseSize, baseHeight, postHeight, postRadius, jibFoot, jibReach, jibTipHeight, jibRadius, tieRadius } = form;
  const top = baseHeight + postHeight,
    foot = [0, baseHeight + jibFoot, 0],
    tip = [jibReach, baseHeight + jibTipHeight, 0];
  return [
    { kind: 'box', material: 'stone', centre: [0, baseHeight / 2, 0], size: [baseSize, baseHeight, baseSize] },
    { kind: 'beam', material: 'iron', a: [0, baseHeight, 0], b: [0, top, 0], radius: postRadius },
    { kind: 'beam', material: 'iron', a: foot, b: tip, radius: jibRadius },
    { kind: 'beam', material: 'iron', a: [0, top, 0.06], b: tip, radius: tieRadius },
    { kind: 'beam', material: 'iron', a: [0, top, -0.06], b: tip, radius: tieRadius },
    { kind: 'beam', material: 'iron', a: tip, b: [tip[0], tip[1] - form.hookDrop, 0], radius: 0.012 },
    {
      kind: 'box',
      material: 'wood',
      centre: [-0.55, baseHeight + form.winchSize[1] / 2, 0],
      size: form.winchSize,
    },
  ];
}

export function wharfCranes({ THREE, scene, data, level, materials }) {
  const spec = data.wharfCranes;
  if (!spec) return null;
  const positions = { stone: [], iron: [], wood: [] };
  const matrix = new THREE.Matrix4(),
    local = new THREE.Matrix4(),
    up = new THREE.Vector3(0, 1, 0);
  const add = (geometry, key, transform) => {
    const g = geometry.toNonIndexed().applyMatrix4(transform);
    positions[key].push(...g.getAttribute('position').array);
    geometry.dispose();
    g.dispose();
  };
  const placed = [];
  for (const crane of spec.cranes) {
    const ground = level(crane.x, crane.z);
    // Scene x east, z south: heading is measured in the xz plane from +x toward +z.
    matrix.makeRotationY(-(crane.headingDegrees * Math.PI) / 180).setPosition(crane.x, ground, crane.z);
    for (const part of craneParts(spec.form)) {
      if (part.kind === 'box') {
        local.makeTranslation(...part.centre);
        add(new THREE.BoxGeometry(...part.size), part.material, matrix.clone().multiply(local));
      } else {
        const a = new THREE.Vector3(...part.a),
          b = new THREE.Vector3(...part.b),
          delta = b.clone().sub(a);
        local.compose(
          a.clone().add(b).multiplyScalar(0.5),
          new THREE.Quaternion().setFromUnitVectors(up, delta.clone().normalize()),
          new THREE.Vector3(1, 1, 1)
        );
        add(
          new THREE.CylinderGeometry(part.radius, part.radius, delta.length(), 8),
          part.material,
          matrix.clone().multiply(local)
        );
      }
    }
    placed.push({ id: crane.id, ground: +ground.toFixed(3) });
  }
  const group = new THREE.Group();
  group.name = 'Wharf and yard cranes (OS crane symbols)';
  for (const [key, array] of Object.entries(positions)) {
    if (!array.length) continue;
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(array, 3));
    geometry.computeVertexNormals();
    const mesh = new THREE.Mesh(geometry, materials[key]);
    mesh.name = `crane:${key}`;
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    group.add(mesh);
  }
  scene.add(group);
  return { cranes: placed.length, deferred: spec.deferred.length, placed };
}
