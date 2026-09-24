// Original branch and leaf geometry at traced OS tree symbols.
// These later-map positions are a continuity hypothesis, not dated c1900 planting records.
export function mappedTrees({THREE,scene,data,level,beam}) {
  let seed=1914;
  const rnd=()=>{seed=(seed*1664525+1013904223)>>>0;return seed/4294967296;};
  const canvas=document.createElement('canvas');canvas.width=canvas.height=128;
  const ctx=canvas.getContext('2d');
  // Separate leaf silhouettes leave real gaps in each small foliage spray.
  for(let i=0;i<38;i++) {
    const x=16+rnd()*96,y=16+rnd()*96,v=155+Math.floor(rnd()*90);
    ctx.fillStyle=`rgb(${v},${v},${v-15})`;
    ctx.beginPath();ctx.ellipse(x,y,6+rnd()*6,4+rnd()*4,rnd()*Math.PI,0,Math.PI*2);ctx.fill();
  }
  const texture=new THREE.CanvasTexture(canvas);texture.colorSpace=THREE.SRGBColorSpace;
  texture.anisotropy=4;
  const leaves=['#687447','#788153','#879160','#737f50'].map(color=>new THREE.MeshStandardMaterial({
    color,map:texture,alphaTest:.45,side:THREE.DoubleSide,roughness:.95}));
  leaves.forEach(material=>{material.userData.preserveUV=true;});
  const bark=new THREE.MeshStandardMaterial({color:'#726957',roughness:1});
  const [x0,z0,x1,z1]=data.terrain.bounds;
  for(const spec of data.mappedTrees.trees) {
    const {x,z,height:h,crownRadius:r}=spec;
    const y=x>=x0&&x<=x1&&z>=z0&&z<=z1?Math.max(.05,level(x,z)):0;
    const lean=(rnd()-.5)*.7;
    beam(scene,[x,y,z],[x+lean,y+h*.62,z+.15],.19+rnd()*.1,bark);
    for(let j=0;j<9;j++) {
      const angle=j*2.399+rnd()*.4,by=y+h*(.3+j*.037);
      const reach=r*(.55+rnd()*.35),dx=Math.cos(angle)*reach,dz=Math.sin(angle)*reach;
      const end=[x+dx,by+h*.23,z+dz];
      beam(scene,[x+lean*.5,by,z],end,.07+rnd()*.025,bark);
      for(let k=0;k<3;k++)beam(scene,end,[end[0]+(rnd()-.5)*1.7,end[1]+.7+rnd(),end[2]+(rnd()-.5)*1.7],.018,bark);
    }
    // Volumetric, asymmetric crowns with small leaf sprays, not solid geometric balls.
    for(let j=0;j<540;j++) {
      const a=rnd()*Math.PI*2,v=rnd()*2-1,rad=Math.cbrt(rnd());
      const ring=Math.sqrt(1-v*v),lobe=1+.15*Math.sin(a*5+v*3);
      const mesh=new THREE.Mesh(new THREE.PlaneGeometry(1,1),leaves[j%leaves.length]);
      mesh.position.set(x+lean+Math.cos(a)*ring*r*rad*lobe,y+h*.7+v*h*.3*rad,z+Math.sin(a)*ring*r*rad*lobe);
      const size=1.3+rnd()*1.1;mesh.scale.set(size,size*(.7+rnd()*.5),1);
      mesh.rotation.set(rnd()*Math.PI,rnd()*Math.PI,rnd()*Math.PI);
      scene.add(mesh);
    }
  }
  return {count:data.mappedTrees.trees.length,sourceYear:1914,continuityHypothesis:true};
}
