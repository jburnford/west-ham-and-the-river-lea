// Interpreted overcast daylight, shared by the sky, materials and river reflection.
// No date/time or measured historic lighting is implied.
export function lighting(THREE, renderer, scene) {
  const settings = {
    exposure: 1.12, skyIntensity: .82, environmentIntensity: .85,
    diffuseIntensity: 2.5, keyIntensity: 1.7, hazeDensity: .00065
  };
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = settings.exposure;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.shadowMap.autoUpdate = false;
  renderer.shadowMap.needsUpdate = true;

  // One continuous directional sky avoids the old cube-face gradients/seams.
  // The bright cloud opening agrees with the broad northwest key light.
  const keyDirection = new THREE.Vector3(-190, 330, -200).normalize();
  const canvas = document.createElement('canvas'); canvas.width = 1024; canvas.height = 512;
  const context = canvas.getContext('2d'), pixels = context.createImageData(1024, 512);
  const horizon = new THREE.Color('#c3c7c7'), zenith = new THREE.Color('#98a3ae');
  const ground = new THREE.Color('#77756b'), cloud = new THREE.Color('#e4e2d9');
  const colour = new THREE.Color(), direction = new THREE.Vector3();
  const smooth = v => v * v * (3 - 2 * v);
  for (let y = 0; y < 512; y++) {
    const latitude = (.5 - (y + .5) / 512) * Math.PI;
    const height = Math.sin(latitude), radius = Math.cos(latitude);
    for (let x = 0; x < 1024; x++) {
      const longitude = ((x + .5) / 1024 - .5) * Math.PI * 2;
      direction.set(radius * Math.cos(longitude), height, radius * Math.sin(longitude));
      if (height >= 0) {
        colour.copy(horizon).lerp(zenith, Math.pow(height, .65));
        const opening = Math.pow(Math.max(0, direction.dot(keyDirection)), 5);
        colour.lerp(cloud, opening * .6);
        // Low-contrast, non-repeating cloud layers, continuous at the seam/poles.
        const variation = Math.sin(direction.x * 9 + direction.y * 5 + direction.z * 3)
          * Math.sin(direction.z * 11 - direction.x * 4 + direction.y * 7)
          + .35 * Math.sin(direction.x * 24 + direction.z * 19 - direction.y * 11);
        colour.multiplyScalar(1 + variation * .045 * smooth(Math.min(1, height * 5)));
      } else colour.copy(horizon).lerp(ground, smooth(Math.min(1, -height * 3)));
      colour.convertLinearToSRGB();
      const i = (y * 1024 + x) * 4;
      pixels.data[i] = colour.r * 255; pixels.data[i + 1] = colour.g * 255;
      pixels.data[i + 2] = colour.b * 255; pixels.data[i + 3] = 255;
    }
  }
  context.putImageData(pixels, 0, 0);
  const sky = new THREE.CanvasTexture(canvas);
  sky.colorSpace = THREE.SRGBColorSpace; sky.mapping = THREE.EquirectangularReflectionMapping;
  scene.background = sky; scene.environment = sky;
  scene.backgroundIntensity = settings.skyIntensity;
  scene.environmentIntensity = settings.environmentIntensity;
  // Match fog radiance to the visible horizon before the common exposure transform.
  scene.fog = new THREE.FogExp2(horizon.clone().multiplyScalar(settings.skyIntensity), settings.hazeDensity);
  scene.add(new THREE.HemisphereLight('#e0e6ec', '#928578', settings.diffuseIntensity));
  const key = new THREE.DirectionalLight('#f0eee7', settings.keyIntensity);
  key.position.set(-190, 330, -160); key.target.position.set(0, 0, 40);
  key.castShadow = true; key.shadow.mapSize.set(2048, 2048);
  Object.assign(key.shadow.camera, { left: -360, right: 360, top: 400, bottom: -360, near: 1, far: 950 });
  key.shadow.normalBias = .12; key.shadow.bias = -.00012;
  scene.add(key, key.target);
  return settings;
}
