// Mapped plan alignment; railway levels and construction details are interpreted.
export function greatEastern({ THREE, scene, m, railway: r, box, surface, ballast }) {
  const earth = m.ground.clone();
  earth.userData = {};
  earth.onBeforeCompile = (shader) => {
    shader.vertexShader = 'varying vec3 railGround;\n' + shader.vertexShader;
    shader.vertexShader = shader.vertexShader.replace(
      '#include <begin_vertex>',
      '#include <begin_vertex>\nrailGround=(modelMatrix*vec4(position,1.0)).xyz;'
    );
    shader.fragmentShader =
      `varying vec3 railGround;
      float railHash(vec2 p) {
        vec3 q=fract(vec3(p.xyx)*.1031);
        q+=dot(q,q.yzx+33.33);
        return fract((q.x+q.y)*q.z);
      }
      float railNoise(vec2 p) {
        vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);
        return mix(mix(railHash(i),railHash(i+vec2(1,0)),f.x),
          mix(railHash(i+vec2(0,1)),railHash(i+vec2(1,1)),f.x),f.y);
      }
    ` + shader.fragmentShader;
    shader.fragmentShader = shader.fragmentShader.replace(
      '#include <map_fragment>',
      `#include <map_fragment>
      diffuseColor.rgb*=.73+.20*railNoise(railGround.xz*.12)
        +.12*railNoise(railGround.xz*.73)+.05*railNoise(railGround.xz*3.1);`
    );
  };
  earth.customProgramCacheKey = () => 'railway-earth';
  surface(r.embankment, earth, 0, true);
  const stations = r.stations;
  const point = (s, offset, dy) => [s[0] + s[3] * offset, s[2] + dy, s[1] + s[4] * offset];
  function strip(rows, left, right, low, high, material) {
    const triangles = [];
    const quad = (a, b, c, d) => triangles.push([a, b, c], [a, c, d]);
    for (let i = 1; i < rows.length; i++) {
      const a = rows[i - 1],
        b = rows[i];
      quad(point(a, left, high), point(a, right, high), point(b, right, high), point(b, left, high));
      if (high !== low) {
        quad(point(a, left, low), point(b, left, low), point(b, left, high), point(a, left, high));
        quad(point(a, right, high), point(b, right, high), point(b, right, low), point(a, right, low));
      }
    }
    // Unlike a terrain triangle, these include vertical faces. Preserve winding
    // and render both sides so side webs remain visible from below the bridge.
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(triangles.flat(2), 3));
    geometry.computeVertexNormals();
    const mesh = new THREE.Mesh(geometry, material);
    scene.add(mesh);
  }
  const ballastMaterial = ballast.clone();
  ballastMaterial.side = THREE.DoubleSide;
  const railMaterial = m.iron.clone();
  railMaterial.side = THREE.DoubleSide;
  const half = r.crestHalfWidth - 0.2,
    bridgeHalf = r.crestHalfWidth - 0.1;
  strip(stations, -half, half, 0, 0.18, ballastMaterial);
  for (let track = 0; track < r.tracks; track++) {
    const offset = (track - (r.tracks - 1) / 2) * r.trackSpacing;
    for (const side of [-1, 1])
      strip(
        stations,
        offset + (side * r.gauge) / 2 - 0.038,
        offset + (side * r.gauge) / 2 + 0.038,
        0.33,
        0.46,
        railMaterial
      );
  }
  function at(distance) {
    const i = Math.min(stations.length - 2, Math.max(0, Math.floor((distance / r.length) * (stations.length - 1))));
    const a = stations[i],
      b = stations[i + 1],
      t = Math.min(1, Math.max(0, (distance - a[5]) / (b[5] - a[5])));
    return a.map((v, j) => v + (b[j] - v) * t);
  }
  // Shared sleeper geometry avoids thousands of independent meshes at startup.
  const count = Math.floor(r.length / 0.75) + 1;
  const sleepers = new THREE.InstancedMesh(new THREE.BoxGeometry(0.25, 0.15, 2.6), m.wood, count * r.tracks);
  const dummy = new THREE.Object3D();
  let index = 0;
  for (let n = 0; n < count; n++) {
    const s = at(n * 0.75);
    for (let track = 0; track < r.tracks; track++) {
      const offset = (track - (r.tracks - 1) / 2) * r.trackSpacing;
      dummy.position.fromArray(point(s, offset, 0.255));
      dummy.rotation.set(0, Math.atan2(s[3], s[4]), 0);
      dummy.updateMatrix();
      sleepers.setMatrixAt(index++, dummy.matrix);
    }
  }
  sleepers.userData.keepIndexed = true;
  sleepers.castShadow = true;
  sleepers.receiveShadow = true;
  sleepers.instanceMatrix.needsUpdate = true;
  sleepers.computeBoundingSphere();
  scene.add(sleepers);
  const walls = [];
  for (const [a, b] of r.retainingEdges) {
    const lowA = [a[0], -0.1, a[2]],
      lowB = [b[0], -0.1, b[2]];
    walls.push([a, lowA, b], [b, lowA, lowB]);
  }
  const brick = m.brick.clone();
  brick.side = THREE.DoubleSide;
  // surface() fixes upward winding only; DoubleSide also exposes vertical cuts.
  surface(walls, brick, 0, true);
  for (const bridge of r.bridges) {
    const rows = [
      at(bridge.start),
      ...stations.filter((s) => s[5] > bridge.start && s[5] < bridge.end),
      at(bridge.end),
    ];
    strip(rows, -bridgeHalf, bridgeHalf, -0.65, -0.02, railMaterial);
    for (const side of [-1, 1]) {
      strip(rows, side * (half - 0.05) - 0.09, side * (half - 0.05) + 0.09, -0.6, 0.75, railMaterial);
      strip(rows, side * (half - 0.05) - 0.22, side * (half - 0.05) + 0.22, 0.72, 0.8, railMaterial);
    }
    for (let distance = bridge.start + 1; distance < bridge.end; distance += 3) {
      const s = at(distance),
        girder = box(scene, s[0], s[2] - 0.63, s[1], 0.22, 0.32, half * 2, m.iron);
      girder.rotation.y = Math.atan2(s[3], s[4]);
    }
  }
  // Restore only the small northern channel context required at the approach.
  function water(polygons, material, height) {
    for (const rings of polygons) {
      const shape = new THREE.Shape(rings[0].map(([x, z]) => new THREE.Vector2(x, -z)));
      for (const hole of rings.slice(1))
        shape.holes.push(new THREE.Path(hole.map(([x, z]) => new THREE.Vector2(x, -z))));
      const mesh = new THREE.Mesh(new THREE.ShapeGeometry(shape), material);
      mesh.rotation.x = -Math.PI / 2;
      mesh.position.y = height;
      scene.add(mesh);
    }
  }
  water(r.northernWater, m.water, 0.06);
  water(r.northernWater, m.tidalWater, 0.06);
  surface(
    r.northernBanks.flatMap(([a, b, c, d]) => [
      [a, b, c],
      [a, c, d],
    ]),
    earth,
    0,
    true
  );
  return {
    id: r.id,
    length: r.length,
    tracks: r.tracks,
    bridges: r.bridges.length,
    sleepers: index,
    sewerCrossing: r.sewerCrossing,
  };
}
