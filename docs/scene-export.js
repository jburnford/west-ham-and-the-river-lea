// Export the assembled scene as glTF, one layer at a time. Loaded only with
// ?export=1, where app.js also keeps the CPU copies of the vertex buffers that
// it would otherwise release after upload. Driven from scripts/export_gltf.py.
import { GLTFExporter } from './vendor/three/GLTFExporter.js';

export function installSceneExport({ THREE, scene, origin, revision }) {
  const meshes = () => {
    const list = [];
    scene.traverse((object) => {
      if (object.isMesh && object.geometry?.getAttribute('position')) list.push(object);
    });
    return list;
  };
  const triangles = (mesh) => {
    const geometry = mesh.geometry,
      count = geometry.index ? geometry.index.count : geometry.getAttribute('position').count;
    const range = geometry.drawRange;
    return Math.floor(Math.min(count - range.start, range.count) / 3);
  };
  const layerOf = (mesh) => mesh.userData.layer || 'untagged';

  // Triangle and mesh counts per layer, largest first, so the caller can choose what to export.
  function layers() {
    const totals = new Map();
    for (const mesh of meshes()) {
      const name = layerOf(mesh);
      const entry = totals.get(name) || { layer: name, meshes: 0, triangles: 0 };
      entry.meshes++;
      entry.triangles += triangles(mesh);
      totals.set(name, entry);
    }
    return [...totals.values()].sort((a, b) => b.triangles - a.triangles);
  }

  // The exporter ignores drawRange, so a mesh that draws part of a shared indexed geometry
  // (the canal coping) gets an index slice; attributes stay shared.
  const exportGeometry = (geometry) => {
    const range = geometry.drawRange;
    if (range.count === Infinity || !geometry.index) return geometry;
    const sliced = new THREE.BufferGeometry();
    for (const [name, attribute] of Object.entries(geometry.attributes)) sliced.setAttribute(name, attribute);
    sliced.setIndex(
      new THREE.BufferAttribute(geometry.index.array.subarray(range.start, range.start + range.count), 1)
    );
    return sliced;
  };

  // Binary glTF for one layer. Clones share the live geometries, so nothing is copied
  // until the exporter serialises; world transforms are baked into each clone.
  async function glb(layer) {
    const group = new THREE.Group();
    group.name = `West Ham c1900 — ${layer}`;
    group.userData = {
      layer,
      revision,
      origin,
      axes: 'x east, y up, z south; metres from the origin',
      note: 'Interpretive reconstruction. Evidence and limits are recorded in the repository notes.',
    };
    for (const mesh of meshes()) {
      if (layerOf(mesh) !== layer || !mesh.visible) continue;
      mesh.updateWorldMatrix(true, false);
      const clone = new THREE.Mesh(exportGeometry(mesh.geometry), mesh.material);
      clone.name = mesh.name || layer;
      clone.applyMatrix4(mesh.matrixWorld);
      group.add(clone);
    }
    const exporter = new GLTFExporter();
    return exporter.parseAsync(group, { binary: true, onlyVisible: true });
  }

  // page.evaluate cannot return hundreds of megabytes in one call, so the harness
  // prepares a layer, then pulls it in base64 slices.
  let pending = null;
  const api = {
    origin,
    layers,
    async prepare(layer) {
      pending = new Uint8Array(await glb(layer));
      return pending.length;
    },
    slice(offset, length) {
      const part = pending.subarray(offset, offset + length);
      let text = '';
      for (let i = 0; i < part.length; i += 0x8000)
        text += String.fromCharCode.apply(null, part.subarray(i, i + 0x8000));
      return btoa(text);
    },
    release() {
      pending = null;
    },
  };
  window.sceneExport = api;
  return api;
}
