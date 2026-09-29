// Photo-informed timber/path study on the existing GIS east bank. Dimensions are estimates.
export function wallRiverVista({ THREE, scene, materials: m, data, box, beam }) {
  const bank=data.bank, samples=bank.samples, y=bank.crestHeight;
  const wood=m.wood.clone();wood.color.set('#716b5e');
  const dark=m.wood.clone();dark.color.set('#484b42');
  const path=m.ground.clone();path.color.set('#b5aa94');
  const positions=[],uv=[];
  function triangle(a,b,c) { positions.push(...a,...b,...c);for(const p of [a,b,c])uv.push(p[0]/5500,p[2]/5500); }
  function plank(a,b,height,thickness,material) {
    const dx=b[0]-a[0],dz=b[2]-a[2],length=Math.hypot(dx,dz);
    const g=new THREE.Group();g.position.set((a[0]+b[0])/2,0,(a[2]+b[2])/2);g.rotation.y=-Math.atan2(dz,dx);scene.add(g);
    box(g,0,(a[1]+b[1])/2,0,length,height,thickness,material);
  }
  for(let i=1;i<samples.length;i++) {
    const [ax,az]=samples[i-1],[bx,bz]=samples[i],left=bank.pathLandOffset+bank.pathWidth/2,right=bank.pathLandOffset-bank.pathWidth/2;
    const a=[ax+left,y+.025,az],b=[bx+left,y+.025,bz],c=[bx+right,y+.025,bz],d=[ax+right,y+.025,az];
    triangle(a,c,b);triangle(a,d,c);
    // Timber toe, a low path rail and the close-boarded plot boundary.
    plank([ax+.22,.05,az],[bx+.22,.05,bz],bank.toeHeight,.16,dark);
    for(const rise of [.23,.64])plank([ax+bank.railOffset,y+rise,az],[bx+bank.railOffset,y+rise,bz],.12,.10,wood);
    const distance=Math.hypot(bx-ax,bz-az),steps=Math.ceil(distance/.25);
    for(let k=0;k<steps;k++) {
      const t=(k+.5)/steps,x=ax+(bx-ax)*t+bank.boundaryOffset,z=az+(bz-az)*t;
      const g=new THREE.Group();g.position.set(x,0,z);g.rotation.y=-Math.atan2(bz-az,bx-ax);scene.add(g);
      box(g,0,y,0,distance/steps*.92,1.25+.08*Math.sin(i*2+k),.07,wood);
    }
    if(i%2===0) {
      for(const [offset,h] of [[bank.boundaryOffset,1.4],[bank.railOffset,.9],[.22,.83]])box(scene,bx+offset,offset<1?.02:y,bz,.16,h,.16,dark);
      beam(scene,[bx+bank.railOffset,y+.72,bz],[bx+bank.railOffset-1,y-.2,bz+.2],.06,wood);
    }
  }
  for(const connection of data.connections)for(let i=1;i<connection.sections.length;i++) {
    const [a,d]=connection.sections[i-1],[b,c]=connection.sections[i];
    triangle(a,b,c);triangle(a,c,d);
  }
  for(const [x,z] of [samples[0],samples.at(-1)])for(const [offset,height] of [[bank.boundaryOffset,1.4],[bank.railOffset,.9]])
    box(scene,x+offset,y,z,.18,height,.18,dark);
  const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));geometry.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));geometry.computeVertexNormals();
  const mesh=new THREE.Mesh(geometry,path);mesh.name='Wall River photograph-study path';mesh.receiveShadow=true;scene.add(mesh);
  for(const tree of data.trees) {
    const nearest=samples.reduce((a,b)=>Math.abs(b[1]-tree.z)<Math.abs(a[1]-tree.z)?b:a);
    const x=nearest[0]+tree.offset,z=tree.z,h=tree.height;
    beam(scene,[x,y,z],[x+.25,y+h,z],.17,wood);
    for(let j=0;j<10;j++) {
      const angle=j*2.399,height=y+h*(.36+j*.045),spread=1.6+(j%3)*.5;
      const end=[x+Math.cos(angle)*spread,height+1.2,z+Math.sin(angle)*spread];
      beam(scene,[x+.1,height,z],end,.055,wood);
      for(let k=0;k<3;k++)beam(scene,end,[end[0]+Math.cos(angle+k)*.7,end[1]+.6+k*.2,end[2]+Math.sin(angle+k)*.7],.016,wood);
    }
  }
  return {pathLength:samples.at(-1)[1]-samples[0][1],connections:data.connections.length,trees:data.trees.length,provisional:true};
}
