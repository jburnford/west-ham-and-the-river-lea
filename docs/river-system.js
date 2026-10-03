// The regional waterways are part of the normal reconstruction. Their mapped
// geometry is deliberately independent of the local inundation experiment.
export async function loadRiverSystem(load) {
  const data=await load('./data/river-system-1900.json');
  const buffers=await Promise.all([data.positionFile,data.indexFile,data.sedimentFile,data.landcoverFile,data.faceFile,data.faceUVFile].map(file=>load(`./data/${file}`,'buffer')));
  data.positions=new Float32Array(buffers[0]);data.indices=new Uint32Array(buffers[1]);
  data.sediment=new Uint8Array(buffers[2]);data.cover=new Uint8Array(buffers[3]);
  data.faces=new Float32Array(buffers[4]);data.faceUV=new Float32Array(buffers[5]);
  if(data.positions.length!==data.vertices*3||data.indices.length!==data.triangles*3)throw Error('Regional river geometry dimensions differ');
  if(data.sediment.length!==data.vertices||data.cover.length!==data.vertices*2||data.faces.length!==data.faceVertices*3||data.faceUV.length!==data.faceVertices*2)throw Error('Regional bank attributes differ');
  return data;
}

export function applyRiverSystem(data) {
  const system=data.riverSystem;
  data.riverNetwork.baseGround=system.baseGround;
  for(const i of system.coreBedCorrections)data.riverNetwork.positions[i*3+1]=Math.min(-.7,data.riverNetwork.positions[i*3+1]);
  for(const adjustment of system.railwayGroundAdjustments||[]){
    const railway=data.infrastructure.railways.find(r=>r.id===adjustment.railwayId);
    const vertex=railway?.embankment[adjustment.triangle]?.[adjustment.vertex];
    if(!vertex||Math.abs(vertex[1]-adjustment.beforeY)>1e-6)throw Error('Railway ground adjustment does not match its source geometry');
    vertex[1]=adjustment.afterY;
  }
}

export function riverSystem({THREE,scene,data,materials,surfaces}) {
  const geometry=new THREE.BufferGeometry();
  geometry.setAttribute('position',new THREE.BufferAttribute(data.positions,3));
  geometry.setAttribute('sediment',new THREE.BufferAttribute(data.sediment,1,true));
  geometry.setAttribute('landCover',new THREE.BufferAttribute(data.cover,2,true));
  geometry.setIndex(new THREE.BufferAttribute(data.indices,1));
  const uv=new Float32Array(data.vertices*2);
  for(let i=0;i<data.vertices;i++)uv.set([data.positions[i*3],data.positions[i*3+2]],i*2);
  geometry.setAttribute('uv',new THREE.BufferAttribute(uv,2));geometry.computeVertexNormals();geometry.computeBoundingSphere();
  const [earthGroup,copingGroup]=data.bankSections.materialGroups;
  geometry.setDrawRange(earthGroup.start,earthGroup.count);
  const coping=materials.stone.clone();coping.color.set('#8b8977');coping.roughness=.95;surfaces.weather(coping);
  const mesh=new THREE.Mesh(geometry,materials.land);mesh.name='Lower Lea river system — shaped beds and banks';mesh.userData.keepIndexed=true;mesh.receiveShadow=true;scene.add(mesh);
  // Share GPU attributes but retain separate single-material meshes: the
  // scene's batching and tide traversal expect one material per object.
  const copingGeometry=new THREE.BufferGeometry();
  for(const [name,attribute] of Object.entries(geometry.attributes))copingGeometry.setAttribute(name,attribute);
  copingGeometry.setIndex(geometry.index);copingGeometry.setDrawRange(copingGroup.start,copingGroup.count);
  copingGeometry.boundingSphere=geometry.boundingSphere.clone();
  const copingMesh=new THREE.Mesh(copingGeometry,coping);copingMesh.name='Limehouse Cut — stone coping';copingMesh.userData.keepIndexed=true;copingMesh.receiveShadow=true;scene.add(copingMesh);
  const faceGeometry=new THREE.BufferGeometry();
  faceGeometry.setAttribute('position',new THREE.BufferAttribute(data.faces,3));
  faceGeometry.setAttribute('uv',new THREE.BufferAttribute(data.faceUV,2));faceGeometry.computeVertexNormals();
  const masonry=materials.brick.clone();masonry.color.set('#7e7969');masonry.side=THREE.DoubleSide;masonry.userData.preserveUV=true;surfaces.weather(masonry);
  const faces=new THREE.Mesh(faceGeometry,masonry);faces.name='Limehouse Cut — interpreted brick canal edges';faces.receiveShadow=true;scene.add(faces);
  // Static illustrative water. New upstream channels are not silently added
  // to the tide animation or used as unrestricted flood seeds.
  const water=new THREE.MeshStandardMaterial({color:0x73979a,roughness:.5,side:THREE.DoubleSide});
  const group=new THREE.Group();group.name='Lower Lea river system — mapped water';
  for(const rings of data.waterPolygons){
    const shape=new THREE.Shape(rings[0].map(([x,z])=>new THREE.Vector2(x,-z)));
    for(const hole of rings.slice(1))shape.holes.push(new THREE.Path(hole.map(([x,z])=>new THREE.Vector2(x,-z))));
    const surface=new THREE.Mesh(new THREE.ShapeGeometry(shape),water);
    surface.rotation.x=-Math.PI/2;surface.position.y=data.waterLevel;group.add(surface);
  }
  scene.add(group);
  return {epoch:data.epoch,pieces:data.reaches.length,passages:data.crossings.length,
    bounds:data.bounds,triangles:data.triangles,coreBedCorrections:data.coreBedCorrections.length,
    reachIds:data.reaches.map(r=>r.id),floodDomainChanged:false,capacityCalibrated:false,
    railwayGroundAdjustments:(data.railwayGroundAdjustments||[]).length,
    banks:{method:data.bankSections.method,shoreLengthMetres:data.bankSections.modelledShoreLengthMetres,
      canalFacingLengthMetres:data.bankSections.canalFacingLengthMetres,faceVertices:data.faceVertices,
      materialGroups:data.bankSections.materialGroups,geometryEpoch:data.bankSections.geometryEpoch,
      terrainPatches:data.bankSections.terrainPatches||[]}};
}

export function installRiverExplorer({views,travel}) {
  document.body.classList.add('is-flood-view');
  const panel=document.createElement('section');panel.className='landscape-flood-panel';
  panel.setAttribute('aria-label','Lower Lea river system');
  panel.innerHTML='<p class="flood-kicker">c.1900 · RIVER NETWORK</p><h2>Lea Bridge to the Thames</h2><p>Follow the Old Lea, the back rivers and the navigation channels through the lower valley.</p><div class="flood-actions"></div><p class="flood-caveat">Early map readings now shape the broad marsh floor: roughly 12 ft in Stratford, 8 ft in northern Mill Meads and 4–6 ft around Abbey and Plaistow. River banks, railway and sewer embankments rise continuously above it; industrial yards have their own levels. Sparse ground, unmeasured banks and premises fill remain estimates. The flood experiment still uses its previous terrain; mill and lock operation also needs modelling before wider flooding.</p><a href="./lower-lea-marsh-evidence.html">Review the marsh-height evidence</a><br><a href="./maps/#15/51.530/-0.010/on:six-inch-2nd/v:">Compare the historical map</a><br><a href="./">Return to the landscape</a>';
  const selected=views.filter(v=>v.id.endsWith('-rivers')||v.id.endsWith('-banks'));
  for(const view of selected){
    const button=document.createElement('button');button.textContent=view.name.split(' — ')[0];
    button.dataset.riverView=view.id;button.addEventListener('click',()=>travel(view));
    panel.querySelector('.flood-actions').append(button);
  }
  document.querySelector('.stage').append(panel);travel(selected[0]);
}
