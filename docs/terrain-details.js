// Inferred landform and working surfaces, based on Figure 2.4.
// Original geometry only; source photograph is not used as a surface texture.
export async function loadTerrain(load) {
  // Optional loader lets the page report download progress; default keeps plain fetch.
  const json=load?url=>load(url,'json'):async url=>{const r=await fetch(url);if(!r.ok) throw new Error('River terrain metadata unavailable');return r.json();};
  const buffer=load?url=>load(url,'buffer'):async url=>{const r=await fetch(url);if(!r.ok) throw new Error(`Terrain asset unavailable: ${url}`);return r.arrayBuffer();};
  const terrain=await json('./data/river-terrain.json');
  const files=await Promise.all([terrain.heightFile,terrain.propertyFile,terrain.landcoverFile].map(file=>buffer(`./data/${file}`)));
  terrain.levels=new Float32Array(files[0]);terrain.properties=new Uint8Array(files[1]);
  terrain.landcover=new Uint8Array(files[2]);
  if(terrain.levels.length!==terrain.width*terrain.height || terrain.properties.length!==terrain.levels.length*4 || terrain.landcover.length!==terrain.levels.length) throw new Error('Terrain dimensions do not match');
  terrain.mudImage=new Image();terrain.mudImage.src='./assets/textures/tidal-mud-v1.png';
  await terrain.mudImage.decode();
  return terrain;
}

export function terrainDetails({THREE,scene,materials:m,data,box,cylinder,beam,random,density=1}) {
  const t=data.terrain,[x0,z0,x1,z1]=t.bounds;
  function level(x,z) {
    if(x<x0 || x>x1 || z<z0 || z>z1) return 0;
    const fx=Math.max(0,Math.min(t.width-1.001,(x-x0)/t.step)),fz=Math.max(0,Math.min(t.height-1.001,(z-z0)/t.step));
    const i=Math.floor(fx),j=Math.floor(fz),u=fx-i,v=fz-j,at=(a,b)=>t.levels[b*t.width+a];
    return (at(i,j)*(1-u)+at(i+1,j)*u)*(1-v)+(at(i,j+1)*(1-u)+at(i+1,j+1)*u)*v;
  }
  const terrainMaterial=m.bed.clone();terrainMaterial.color.set('#e1ddd2');terrainMaterial.vertexColors=true;
  terrainMaterial.userData.terrainAtlas=true;
  const position=new Float32Array(t.width*t.height*3),uv=new Float32Array(t.width*t.height*2),color=new Float32Array(position.length);
  const dry=new THREE.Color('#a39a87'),land=new THREE.Color('#99a17d'),yard=new THREE.Color('#b3a691'),cultivated=new THREE.Color('#958768'),wet=new THREE.Color('#77776c');
  for(let z=0;z<t.height;z++) for(let x=0;x<t.width;x++) {
    const i=z*t.width+x,wx=x0+x*t.step,wz=z0+z*t.step;
    position.set([wx,t.levels[i],wz],i*3);uv.set([wx,wz],i*2);
    const bed=t.properties[i*4+3]/255,moisture=t.properties[i*4+1]/255;
    const base=t.landcover[i]===1?yard:t.landcover[i]===2?cultivated:land;
    const c=base.clone().lerp(dry,bed).lerp(wet,moisture*bed*.55);
    color.set(c.toArray(),i*3);
  }
  const indices=new Uint32Array((t.width-1)*(t.height-1)*6);let k=0;
  for(let z=0;z<t.height-1;z++) for(let x=0;x<t.width-1;x++) {
    const a=z*t.width+x,b=a+1,c=a+t.width,d=c+1;
    indices.set((x+z)%2?[a,c,d,a,d,b]:[a,c,b,b,c,d],k);k+=6;
  }
  const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.BufferAttribute(position,3));
  geometry.setAttribute('uv',new THREE.BufferAttribute(uv,2));geometry.setAttribute('color',new THREE.BufferAttribute(color,3));
  geometry.setIndex(new THREE.BufferAttribute(indices,1));geometry.computeVertexNormals();
  const terrainMesh=new THREE.Mesh(geometry,terrainMaterial);terrainMesh.userData.keepIndexed=true;
  terrainMesh.receiveShadow=true;terrainMesh.castShadow=true;scene.add(terrainMesh);

  // Torn clods and small ridges catch light above the lower-frequency ground mesh.
  // They are flattened mud, not scattered large stones or invented refuse.
  const clod=m.bed.clone();clod.color.set('#555448');clod.bumpScale=.08;
  const lumps=Array.from({length:9},(_,variant)=>{
    const geometry=new THREE.IcosahedronGeometry(1,0),p=geometry.getAttribute('position');
    for(let i=0;i<p.count;i++) {
      const x=p.getX(i),y=p.getY(i),z=p.getZ(i);
      const scale=1+.27*Math.sin(x*7.3+y*14.2+z*5.9+variant*1.7);
      p.setXYZ(i,x*scale,y*scale,z*scale);
    }
    geometry.computeVertexNormals();return geometry;
  });
  let clodCount=0;
  for(let attempt=0;attempt<145000*density;attempt++) {
    const x=-160+random()*205,z=-270+random()*480;
    const ix=Math.round((x-x0)/t.step),iz=Math.round((z-z0)/t.step),i=iz*t.width+ix,h=level(x,z);
    if(t.properties[i*4+3]<200 || t.properties[i*4+2]>80 || h<.09 || h>1.9) continue;
    const radius=.025+Math.pow(random(),2)*.12;
    const mesh=new THREE.Mesh(lumps[clodCount%lumps.length],clod);
    mesh.scale.set(radius*(1+random()),radius*(.16+random()*.3),radius*(.7+random()*1.2));
    mesh.position.set(x,h-.012,z);mesh.rotation.set((random()-.5)*.3,random()*Math.PI,(random()-.5)*.3);scene.add(mesh);clodCount++;
  }

  // A narrow worn crest, occasional retaining timbers and irregular fence posts
  // make the river-right flood bank legible above the lower allotments.
  for(let i=1;i<t.bankRoute.length;i++) {
    const [ax,az]=t.bankRoute[i-1],[bx,bz]=t.bankRoute[i];
    if(i%2===0) {
      const y=level(bx,bz);
      const post=box(scene,bx,y-.12,bz,.11,.9+random()*.35,.1,m.wood);post.rotation.z=(random()-.5)*.13;
      if(i>2) beam(scene,[ax,level(ax,az)+.55,az],[bx,y+.55,bz],.014,m.iron);
    }
    if(i%5===0 && az<180) {
      for(let p=0;p<4;p++) {
        const x=ax+2.8,z=az+p*.8,y=level(x,z);
        const stake=box(scene,x,y-.45,z,.18,.8,.12,m.wood);stake.rotation.z=.14;
      }
    }
  }

  const tar=m.roof.clone();tar.color.set('#4a4b44');tar.map=m.wood.map;tar.bumpMap=m.wood.bumpMap;tar.userData.surface='wood';
  let sheds=0;
  const plotSoils=['#a29378','#8e8067','#a99b80'].map(color=>{const mat=m.ground.clone();mat.color.set(color);return mat;});
  const crops=['#78805c','#90906b','#677452'].map(color=>new THREE.MeshStandardMaterial({color,roughness:1}));
  for(let i=0;i<data.neighbourhood.garden.beds.length;i++) {
    const b=data.neighbourhood.garden.beds[i],ground=level(b.x,b.z);
    box(scene,b.x,ground+.015,b.z,b.width,.035,b.depth,plotSoils[i%plotSoils.length]);
    // Uneven furrows and paths occupy the existing plot footprints.
    for(let z=-b.depth/2+.7;z<b.depth/2;z+=1.3) {
      const row=box(scene,b.x,ground-.03,b.z+z,b.width-.8,.14+random()*.12,.36,m.bed);row.rotation.z=(random()-.5)*.02;
      if(i%5!==0 && Math.floor(z*10)%3!==0)box(scene,b.x,ground+.12,b.z+z,b.width-1,.13+random()*.2,.25,crops[i%3]);
    }
    if(i%7!==0 && i%19!==0) continue;
    const w=2.5+random()*.95,d=2.8+random()*1.3,h=1.7+random()*.65;
    const g=new THREE.Group();g.position.set(b.x,level(b.x,b.z-3),b.z-3);g.rotation.y=(random()-.5)*.24;scene.add(g);sheds++;
    box(g,0,0,0,w,h,d,m.wood);
    for(const sign of [-1,1]) {
      for(let x=-w/2+.12;x<w/2;x+=.22) box(g,x,.03,sign*(d/2+.02),.025,h-.03,.035,m.dark);
      for(let z=-d/2+.12;z<d/2;z+=.24) box(g,sign*(w/2+.02),.03,z,.035,h-.03,.024,m.dark);
    }
    box(g,-w*.18,.05,d/2+.06,.74,h*.82,.08,m.dark);
    box(g,w*.25,h*.46,d/2+.065,.45,.43,.04,m.window);
    box(g,w*.25,h*.44,d/2+.095,.53,.04,.09,m.wood);
    const roof=box(g,0,h,0,w+.4,.12,d+.4,tar);roof.rotation.z=(i%2?1:-1)*.13;
    // Patch boards, roof battens and a low leaning fence; no modern sheet plastics.
    box(g,-w*.22,h+.1,0,.14,.07,d+.35,m.wood);
    box(g,w*.32,h+.1,0,.12,.06,d+.35,m.wood);
    for(let p=0;p<4;p++) {
      const post=box(g,w/2+.6,.05,-d/2+p*1.25,.1,.75+random()*.3,.1,m.wood);post.rotation.z=.07;
    }
    box(g,w/2+.6,.52,.1,.07,.07,d+1,m.wood);
    cylinder(g,-w/2-.45,0,d/2-.35,.24,.28,.68,m.wood,10);
  }
  // Low mixed grass and coarse weeds on open land; no invented trees or species.
  // Mapped working sites, allotments, roads and exposed sediment remain clear.
  const vegetation=[];let vegetationCount=0,plantSeed=902;
  const plantRandom=()=>{plantSeed=(plantSeed*1664525+1013904223)>>>0;return plantSeed/4294967296;};
  const roadSegments=data.infrastructure.roads.flatMap(r=>r.route.slice(1).map((b,i)=>({a:r.route[i],b,width:r.width/2+2})));
  function onRoad(x,z) {return roadSegments.some(({a,b,width})=>{
    const dx=b[0]-a[0],dz=b[1]-a[1],u=Math.max(0,Math.min(1,((x-a[0])*dx+(z-a[1])*dz)/(dx*dx+dz*dz)));
    return Math.hypot(x-a[0]-u*dx,z-a[1]-u*dz)<width;
  });}
  for(let attempt=0;attempt<36000*density;attempt++) {
    const x=x0+plantRandom()*(x1-x0),z=z0+plantRandom()*(z1-z0);
    const ix=Math.round((x-x0)/t.step),iz=Math.round((z-z0)/t.step),i=iz*t.width+ix;
    if(t.landcover[i]!==0 || t.properties[i*4+3]>100 || t.levels[i]<.08 || onRoad(x,z))continue;
    const y=level(x,z),height=.18+plantRandom()*.48;
    for(let blade=0;blade<3;blade++) {
      const angle=plantRandom()*Math.PI*2,dx=Math.cos(angle)*.065,dz=Math.sin(angle)*.065;
      const lean=(plantRandom()-.5)*.22;
      vegetation.push(x-dx,y,z-dz,x+dx,y,z+dz,x+lean,y+height,z+.1);
    }
    vegetationCount++;
  }
  const grass=new THREE.MeshStandardMaterial({color:'#838961',roughness:1,side:THREE.DoubleSide});
  const grassGeometry=new THREE.BufferGeometry();grassGeometry.setAttribute('position',new THREE.Float32BufferAttribute(vegetation,3));grassGeometry.computeVertexNormals();
  scene.add(new THREE.Mesh(grassGeometry,grass));
  return {level,terrainMaterial,clodCount,sheds,vegetationCount};
}
