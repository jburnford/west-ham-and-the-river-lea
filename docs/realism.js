// Original procedural surfaces in metres; archive photographs are references only.
export function realism(THREE, renderer, scene, data, options = {}) {
  let seed = 194;
  const random = () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; };
  function texture(kind, relief = false) {
    seed = { brick: 194, roof: 729, mud: 305, wood: 918, stone: 611, grass: 817 }[kind];
    const c = document.createElement('canvas'); c.width = c.height = 512;
    const ctx = c.getContext('2d');
    ctx.fillStyle = relief ? '#999999' : '#b4b1a8'; ctx.fillRect(0, 0, 512, 512);
    if (kind === 'brick' || kind === 'roof') {
      const rows = kind === 'brick' ? 24 : 12, columns = kind === 'brick' ? 8 : 10;
      const w = 512 / columns, h = 512 / rows;
      ctx.fillStyle = relief ? '#505050' : '#77766e'; ctx.fillRect(0, 0, 512, 512);
      for (let row = 0; row < rows; row++) for (let col = -1; col <= columns; col++) {
        const x = (col + (row % 2) * .5) * w, y = row * h, shade = 145 + random() * 55;
        ctx.fillStyle = relief ? `rgb(${shade},${shade},${shade})` : `rgb(${shade + 12},${shade + 9},${shade})`;
        ctx.fillRect(x + 1, y + 1, w - 2, h - 2);
        ctx.fillStyle = relief ? '#b0b0b0' : 'rgba(235,227,205,.12)'; ctx.fillRect(x + 1, y + 1, w - 2, 1);
      }
    }
    for (let i = 0; i < 22000; i++) {
      const v = 65 + random() * 150;
      ctx.fillStyle = `rgba(${v},${v},${v},${.04 + random() * .16})`;
      ctx.fillRect(random() * 512, random() * 512, kind === 'wood' || kind==='grass' ? 1 : 1 + random() * 3, kind === 'wood' ? 10 + random() * 40 : kind==='grass'?2+random()*6:1 + random() * 3);
    }
    if (kind === 'mud') {
      // Wrapped value noise: seamless, without a repeated wave/checker pattern.
      const pixels = ctx.getImageData(0, 0, 512, 512);
      const octaves = [5, 13, 37, 91].map((size, i) => ({ size,
        values: Array.from({ length: size * size }, random), weight: [38, 23, 12, 7][i] }));
      const sample = (layer, x, y) => {
        const px = x / 512 * layer.size, py = y / 512 * layer.size;
        const ix = Math.floor(px), iy = Math.floor(py), fx = px - ix, fy = py - iy;
        const sx = fx * fx * (3 - 2 * fx), sy = fy * fy * (3 - 2 * fy);
        const v = (dx, dy) => layer.values[((iy + dy) % layer.size) * layer.size + (ix + dx) % layer.size];
        return (v(0, 0) * (1 - sx) + v(1, 0) * sx) * (1 - sy) + (v(0, 1) * (1 - sx) + v(1, 1) * sx) * sy;
      };
      for (let y = 0; y < 512; y++) for (let x = 0; x < 512; x++) {
        const n = octaves.reduce((sum, layer) => sum + (sample(layer, x, y) - .5) * layer.weight, 0);
        const i = (y * 512 + x) * 4;
        for (let k = 0; k < 3; k++) pixels.data[i + k] += n;
      }
      ctx.putImageData(pixels, 0, 0);
    }
    const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping;
    t.colorSpace = relief ? THREE.NoColorSpace : THREE.SRGBColorSpace;
    t.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
    const size = { brick: 1.84, roof: 3, mud: 4, wood: 2, stone: 3, grass: 3 }[kind];
    t.repeat.set(1 / size, 1 / size); return t;
  }
  const textures = {};
  const make = (color, kind, roughness = .9) => {
    const material = new THREE.MeshStandardMaterial({ color, roughness });
    material.userData.surface = kind;
    if (kind) {
      textures[kind] ||= [texture(kind), texture(kind, true)];
      [material.map, material.bumpMap] = textures[kind];
      material.bumpScale = { brick: .018, roof: .025, mud: .085, wood: .028, stone: .018, grass: .015 }[kind];
    }
    return material;
  };
  const materials = {
    ground: make('#9ca583', 'grass'), bed: make('#646359', 'mud'), plot: make('#b5aa97', 'mud'),
    brick: make('#a89c87', 'brick'), roof: make('#646967', 'roof'), iron: make('#414947', null, .65),
    stone: make('#b0ada1', 'stone'), bell: make('#697370', null, .62), wood: make('#655e50', 'wood'),
    dark: make('#222725'), window: make('#35423f', null, .34), coal: make('#272b2c', 'stone', .48),
    water: make('#656c65', null, .28)
  };
  materials.bed.userData.wetBed = true;
  // One land treatment across the detailed tile, outer marsh and flat ground.
  materials.land = materials.ground.clone();
  materials.land.map = null; materials.land.bumpMap = null;
  materials.land.userData.sharedTerrain = true;
  materials.land.defaultAttributeValues = { ...materials.land.defaultAttributeValues,
    sediment: [0], landCover: [0,0] };
  // Original generated sediment texture; no archive image is used here.
  // Reuse its intensity for fine bump relief, not measured displacement.
  const sediment=new THREE.Texture(data.terrain.mudImage);sediment.needsUpdate=true;
  sediment.wrapS=sediment.wrapT=THREE.RepeatWrapping;sediment.repeat.set(.5,.5);
  sediment.colorSpace=THREE.SRGBColorSpace;sediment.anisotropy=Math.min(8,renderer.capabilities.getMaxAnisotropy());
  const sedimentRelief=sediment.clone();sedimentRelief.colorSpace=THREE.NoColorSpace;sedimentRelief.needsUpdate=true;
  materials.bed.map=sediment;materials.bed.bumpMap=sedimentRelief;materials.bed.bumpScale=.065;
  materials.iron.metalness = .5; materials.bell.metalness = .4;

  // Static soft contact shading, baked from existing reconstruction envelopes.
  // This is visual grounding, not surveyed ground marks or a new building layer.
  const contactBounds=[-1600,-1050,650,1700], contactWidth=2250, contactDepth=2750;
  const contactCanvas = document.createElement('canvas'); contactCanvas.width = contactCanvas.height = 2048;
  const contactContext = contactCanvas.getContext('2d');
  contactContext.fillStyle = 'white'; contactContext.fillRect(0, 0, 2048, 2048);
  contactContext.scale(2048/contactWidth,2048/contactDepth); contactContext.translate(-contactBounds[0],-contactBounds[1]);
  const registered=new Set(data.factoryBuildings.sites.map(s=>s.id));
  const footprints = [...data.factoryStudies.filter(b=>!registered.has(b.siteId)), ...data.neighbourhood.mappedFactories.filter(b=>!registered.has(b.siteId)),
    ...data.neighbourhood.houses, ...data.neighbourhood.terraces, ...data.southwest.rows, data.neighbourhood.mill,
    { x: -185, z: -13, width: 54, depth: 20 }, { x: -185, z: -13, width: 20, depth: 48 }];
  for (const b of footprints) {
    contactContext.save(); contactContext.translate(b.x, b.z); contactContext.rotate(-(b.rotation || 0) * Math.PI / 180);
    contactContext.shadowBlur = 6; contactContext.shadowColor = 'rgba(0,0,0,.7)';
    contactContext.fillStyle = '#666666'; contactContext.fillRect(-b.width / 2, -b.depth / 2, b.width, b.depth);
    contactContext.restore();
  }
  for(const b of [...data.factoryBuildings.buildings,...data.highStreetFrontages.buildings])for(const p of b.renderPolygons) {
    contactContext.save();contactContext.shadowBlur=5;contactContext.shadowColor='rgba(0,0,0,.65)';contactContext.fillStyle='#777777';
    contactContext.beginPath();
    for(const ring of [p.outer,...p.holes]) {ring.forEach(([x,z],i)=>i?contactContext.lineTo(x,z):contactContext.moveTo(x,z));contactContext.closePath();}
    contactContext.fill('evenodd');contactContext.restore();
  }
  const contactMap = new THREE.CanvasTexture(contactCanvas);

  const noise = `
    float grainHash(vec2 p) { return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453); }
    float grainNoise(vec2 p) {
      vec2 i=floor(p), f=fract(p); f=f*f*(3.0-2.0*f);
      return mix(mix(grainHash(i),grainHash(i+vec2(1,0)),f.x),
        mix(grainHash(i+vec2(0,1)),grainHash(i+vec2(1,1)),f.x),f.y);
    }
  `;
  function weather(material) {
    if (!material.userData.surface) return;
    const wet = material.userData.wetBed, terrain=material.userData.terrainAtlas, shared=material.userData.sharedTerrain, soil=material.userData.gardenSoil, silt=material.userData.networkSediment || shared, wall = ['brick', 'wood'].includes(material.userData.surface);
    material.onBeforeCompile = shader => {
      shader.uniforms.contactMap = { value: contactMap };
      if(shared&&material.userData.yardAtlas) {
        shader.uniforms.yardAtlas={value:material.userData.yardAtlas};
        shader.uniforms.yardBounds={value:material.userData.yardBounds};
      }
      if(silt)shader.uniforms.networkMud={value:materials.bed.map};
      if(terrain) {
        shader.uniforms.landAtlas={value:riverBed};
        shader.uniforms.landBounds={value:new THREE.Vector4(bx0,bz0,bx1-bx0,bz1-bz0)};
      }
      shader.vertexShader = 'varying vec3 surfacePosition;\n' + shader.vertexShader;
      shader.vertexShader = shader.vertexShader.replace('#include <begin_vertex>', '#include <begin_vertex>\nsurfacePosition = (modelMatrix * vec4(position,1.0)).xyz;');
      if(silt) {
        shader.vertexShader='attribute float sediment; varying float bankSediment;\n'+shader.vertexShader;
        shader.vertexShader=shader.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\nbankSediment=sediment;');
      }
      if(shared) {
        shader.vertexShader='attribute vec2 landCover; varying vec2 groundCover;\n'+shader.vertexShader;
        shader.vertexShader=shader.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\ngroundCover=landCover;');
      }
      shader.fragmentShader = 'uniform sampler2D contactMap; varying vec3 surfacePosition;\n' + noise + shader.fragmentShader;
      if(terrain)shader.fragmentShader='uniform sampler2D landAtlas; uniform vec4 landBounds;\n'+shader.fragmentShader;
      if(silt)shader.fragmentShader='uniform sampler2D networkMud; varying float bankSediment;\n'+shader.fragmentShader;
      if(shared)shader.fragmentShader='varying vec2 groundCover;\n'+shader.fragmentShader;
      if(shared&&material.userData.yardAtlas)shader.fragmentShader='uniform sampler2D yardAtlas; uniform vec4 yardBounds;\n'+shader.fragmentShader;
      shader.fragmentShader = shader.fragmentShader.replace('#include <map_fragment>', `
        ${terrain?'vec3 dryLandColour=diffuseColor.rgb;':''}
        #include <map_fragment>
        ${shared?`// Garden paths remain grassy/earthy; individual plots carry soil.
          diffuseColor.rgb*=.44+.045*sin(surfacePosition.x*.11+2.0*sin(surfacePosition.z*.071))*sin(surfacePosition.z*.095+sin(surfacePosition.x*.13))
            +.022*sin(surfacePosition.x*.63+sin(surfacePosition.z*.49))*sin(surfacePosition.z*.72+sin(surfacePosition.x*.44));
          diffuseColor.rgb*=mix(vec3(1.0),vec3(.94,.81,.65),groundCover.y*.35);`:''}
        ${silt?`vec3 mud=texture2D(networkMud,surfacePosition.xz*.5).rgb*vec3(.39,.38,.33);
          mud*=mix(.52,1.0,smoothstep(.06,.85,surfacePosition.y));
          diffuseColor.rgb=mix(diffuseColor.rgb,mud,bankSediment);`:''}
        ${terrain?`float sedimentMask=texture2D(landAtlas,(surfacePosition.xz-landBounds.xy)/landBounds.zw).a;
          diffuseColor.rgb=mix(dryLandColour*(.50+.10*grainNoise(surfacePosition.xz*.7)),diffuseColor.rgb,sedimentMask);`:''}
        float patches=${shared||soil?'0.65+.10*sin(surfacePosition.x*.33+surfacePosition.z*.19)*sin(surfacePosition.z*.23-surfacePosition.x*.14)':'grainNoise(surfacePosition.xz*.17)+.4*grainNoise(surfacePosition.xz*.83)'};
        diffuseColor.rgb *= .76 + patches*.26;
        ${shared&&material.userData.yardAtlas?`vec2 yardUv=(surfacePosition.xz-yardBounds.xy)/yardBounds.zw;
          vec4 yard=texture2D(yardAtlas,vec2(yardUv.x,1.0-yardUv.y));
          diffuseColor.rgb=mix(diffuseColor.rgb,yard.rgb*vec3(.402,.371,.323),yard.a);`:''}
        vec2 contactUv=vec2((surfacePosition.x+1600.0)/2250.0,1.0-(surfacePosition.z+1050.0)/2750.0);
        float contact=texture2D(contactMap,clamp(contactUv,vec2(0),vec2(1))).r;
        diffuseColor.rgb *= 1.0-(1.0-contact)*.65*(1.0-smoothstep(.0,3.0,surfacePosition.y));
        ${wall ? `float baseDamp=1.0-smoothstep(.0,3.2,surfacePosition.y);
          float runs=grainNoise(surfacePosition.xz*2.2+surfacePosition.y*.035);
          diffuseColor.rgb *= (1.0-.28*baseDamp)*(.83+.22*runs);` : ''}
        ${wet ? `float dryness=smoothstep(.09,.72,surfacePosition.y);
          diffuseColor.rgb *= mix(vec3(1.0),mix(vec3(.48,.53,.52),vec3(1.0),dryness),${terrain?'sedimentMask':'1.0'});` : ''}
      `);
      if (wet) shader.fragmentShader = shader.fragmentShader.replace('#include <roughnessmap_fragment>', `#include <roughnessmap_fragment>\nroughnessFactor=mix(.42,.95,${terrain?'max(1.0-sedimentMask,':''}smoothstep(.09,.72,surfacePosition.y)${terrain?')':''});`);
    };
    material.customProgramCacheKey = () => `weather-${wet}-${wall}-${terrain}-${silt}-${shared}-${soil}`;
  }

  function metricUV(geometry, sourceGeometry) {
    const p = geometry.getAttribute('position'), n = geometry.getAttribute('normal');
    if (!n) return;
    const uv = new Float32Array(p.count * 2);
    const cylinder = sourceGeometry?.type === 'CylinderGeometry' ? sourceGeometry.parameters : null;
    const originalUv = geometry.getAttribute('uv');
    // Each face uses a horizontal tangent and a perpendicular slope tangent.
    // This also gives the roof lofts proper, physically scaled texture coordinates.
    for (let i = 0; i < p.count; i++) {
      const nx = n.getX(i), ny = n.getY(i), nz = n.getZ(i), len = Math.hypot(nx, nz);
      if (cylinder && Math.abs(ny) < .9) {
        uv[i * 2] = originalUv.getX(i) * Math.PI * (cylinder.radiusTop + cylinder.radiusBottom);
        uv[i * 2 + 1] = originalUv.getY(i) * cylinder.height;
      }
      else if (Math.abs(ny) > .65) { uv[i * 2] = p.getX(i); uv[i * 2 + 1] = p.getZ(i); }
      else {
        const ux = nz / len, uz = -nx / len;
        uv[i * 2] = p.getX(i) * ux + p.getZ(i) * uz;
        uv[i * 2 + 1] = p.getX(i) * ny * uz + p.getY(i) * len - p.getZ(i) * ny * ux;
      }
    }
    geometry.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
  }

  // Separate reflection planes for tidal water and the retained river/drains.
  materials.tidalWater = materials.water.clone();
  let tideHeight = data.riverNetwork.tide.low;
  // Masks use the same placements as the rendered lighters. Only their open
  // hold interiors are excluded; river water still meets the outside hulls.
  const bargeHolds = Array.from({length:4},()=>new THREE.Vector4(-10000,-10000,1,0));
  const riverBed=new THREE.DataTexture(data.terrain.properties,data.terrain.width,data.terrain.height,THREE.RGBAFormat);
  riverBed.minFilter=riverBed.magFilter=THREE.LinearFilter;riverBed.needsUpdate=true;
  const [bx0,bz0,bx1,bz1]=data.terrain.bounds;
  function reflector(material, level) {
  const target = new THREE.WebGLRenderTarget(options.reflectionWidth || 512, options.reflectionHeight || 384, { type: THREE.HalfFloatType });
  const reflectionCamera = new THREE.PerspectiveCamera(), matrix = new THREE.Matrix4();
  const clip = new THREE.Plane(new THREE.Vector3(0, 1, 0), -.07);
  material.onBeforeCompile = shader => {
    shader.uniforms.riverReflection = { value: target.texture };
    shader.uniforms.riverMatrix = { value: matrix };
    shader.uniforms.riverBed = { value: riverBed };
    shader.uniforms.bargeHolds = { value: bargeHolds };
    shader.uniforms.bedBounds = { value: new THREE.Vector4(bx0,bz0,bx1-bx0,bz1-bz0) };
    shader.vertexShader = 'uniform mat4 riverMatrix; varying vec4 riverCoord; varying vec3 riverPosition;\n' + shader.vertexShader;
    shader.vertexShader = shader.vertexShader.replace('#include <begin_vertex>', `#include <begin_vertex>
      riverPosition=(modelMatrix*vec4(position,1.0)).xyz;
      riverCoord=riverMatrix*vec4(riverPosition,1.0);`);
    shader.fragmentShader = 'uniform sampler2D riverReflection; uniform sampler2D riverBed; uniform vec4 bedBounds; uniform vec4 bargeHolds[4]; varying vec4 riverCoord; varying vec3 riverPosition;\n' + noise + shader.fragmentShader;
    shader.fragmentShader = shader.fragmentShader.replace('#include <opaque_fragment>', `
      for (int i=0;i<4;i++) {
        vec2 delta=riverPosition.xz-bargeHolds[i].xy;
        float c=bargeHolds[i].z,s=bargeHolds[i].w;
        vec2 local=vec2(c*delta.x-s*delta.y,s*delta.x+c*delta.y);
        // Exact inner-hold outline: straight sides and the quadratic end.
        if(abs(local.x)<2.05 && local.y<6.8 &&
           local.y>-7.2+.8*pow(local.x/2.05,2.0)) discard;
      }
      vec2 riverUv=riverCoord.xy/riverCoord.w;
      vec2 ripple=vec2(sin(riverPosition.x*2.8+riverPosition.z*.6),cos(riverPosition.z*3.4-riverPosition.x*.4));
      ripple *= .0012 + .001*grainNoise(riverPosition.xz*.8);
      vec3 reflected=texture2D(riverReflection,clamp(riverUv+ripple,vec2(.002),vec2(.998))).rgb;
      float facing=abs(dot(normalize(cameraPosition-riverPosition),vec3(0,1,0)));
      vec2 bedUv=(riverPosition.xz-bedBounds.xy)/bedBounds.zw;
      float inside=step(0.0,bedUv.x)*step(0.0,bedUv.y)*step(bedUv.x,1.0)*step(bedUv.y,1.0);
      float depth=mix(.6,texture2D(riverBed,bedUv).r,inside)+max(0.0,riverPosition.y-.06)/2.4;
      float fresnel=.12+.65*pow(1.0-facing,3.0);
      vec3 sediment=mix(vec3(.15,.14,.115),vec3(.044,.058,.054),smoothstep(.0,.65,depth));
      outgoingLight=mix(mix(outgoingLight,sediment,.58),reflected,fresnel);
      outgoingLight *= .965 + .035*grainNoise(riverPosition.xz*vec2(2.5,13.0));
      #include <opaque_fragment>`);
  };
  const reflectionStats = {};
  function reflect(camera) {
    const waterMeshes = [];
    scene.traverse(o => { if (o.isMesh && [materials.water,materials.tidalWater].includes(o.material)) { waterMeshes.push([o,o.visible]); o.visible = false; } });
    reflectionCamera.copy(camera);
    const direction = camera.getWorldDirection(new THREE.Vector3()); direction.y *= -1;
    reflectionCamera.position.y = 2 * level() - camera.position.y;
    clip.constant = -level() - .01;
    reflectionCamera.up.set(0, -1, 0);
    reflectionCamera.lookAt(reflectionCamera.position.clone().add(direction));
    reflectionCamera.updateMatrixWorld();
    matrix.set(.5,0,0,.5, 0,.5,0,.5, 0,0,.5,.5, 0,0,0,1);
    matrix.multiply(reflectionCamera.projectionMatrix).multiply(reflectionCamera.matrixWorldInverse);
    const previousTarget = renderer.getRenderTarget(), previousClip = renderer.clippingPlanes;
    renderer.clippingPlanes = [clip]; renderer.setRenderTarget(target);
    renderer.render(scene, reflectionCamera);
    reflectionStats.drawCalls = renderer.info.render.calls;
    reflectionStats.triangles = renderer.info.render.triangles;
    reflectionStats.width = target.width; reflectionStats.height = target.height;
    renderer.setRenderTarget(previousTarget); renderer.clippingPlanes = previousClip;
    waterMeshes.forEach(([o,visible]) => { o.visible = visible; });
  }
  return { reflect, reflectionStats };
  }
  const fixed = reflector(materials.water, () => data.riverNetwork.waterLevel);
  const moving = reflector(materials.tidalWater, () => tideHeight);
  const reflectionStats = {};
  function reflect(camera) {
    fixed.reflect(camera);
    const animated = tideHeight > data.riverNetwork.waterLevel + .00001;
    if (animated) moving.reflect(camera);
    Object.assign(reflectionStats, fixed.reflectionStats, { planes: animated ? 2 : 1, tidalLevel: tideHeight });
  }
  return { materials, weather, metricUV, reflect, reflectionStats,
    excludeBargeHolds: barges => {
      barges.forEach(([x,z,angle],i)=>bargeHolds[i].set(x,z,Math.cos(angle*Math.PI/180),Math.sin(angle*Math.PI/180)));
      reflectionStats.excludedBargeHolds=barges.length;
    },
    setTideLevel: value => { tideHeight = value; } };
}
