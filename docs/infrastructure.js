// Approximate mapped streets and rail corridors; surfaces/levels are interpretations.
import { highStreetSurfaceHeight } from './sewer-levels.js';
import { greatEastern } from './great-eastern.js';
export function infrastructure({THREE,scene,materials:m,data,box,level}) {
  const infra=data.infrastructure,[x0,z0,x1,z1]=data.terrain.bounds;
  // Original code-generated paving: no modern blacktop or painted road markings.
  // Surface assignment is provisional, not a claim about street adoption records.
  function roadMaterial(kind) {
    const canvas=document.createElement('canvas');canvas.width=canvas.height=512;
    const ctx=canvas.getContext('2d');let seed=kind==='setts'?479:kind==='macadam'?871:316;
    const rnd=()=>{seed=(seed*1664525+1013904223)>>>0;return seed/4294967296;};
    ctx.fillStyle=kind==='setts'?'#777970':kind==='macadam'?'#aaa292':'#938775';ctx.fillRect(0,0,512,512);
    if(kind==='setts')for(let row=0;row<16;row++)for(let col=-1;col<9;col++) {
      const value=Math.floor(132+rnd()*34);
      ctx.fillStyle=`rgb(${value},${value+1},${value-3})`;
      ctx.fillRect(col*64+(row%2)*32+2,row*32+2,60,28);
    }
    for(let i=0;i<40000;i++) {
      const value=kind==='cinder'?45+rnd()*120:80+rnd()*125;
      ctx.fillStyle=`rgba(${value},${value},${value-8},${.05+rnd()*.2})`;
      const size=kind==='cinder'?1+rnd()*3:1+rnd();ctx.fillRect(rnd()*512,rnd()*512,size,size);
    }
    const texture=new THREE.CanvasTexture(canvas);texture.colorSpace=THREE.SRGBColorSpace;
    texture.wrapS=texture.wrapT=THREE.RepeatWrapping;texture.repeat.set(.5,.5);texture.anisotropy=8;
    const bump=texture.clone();bump.colorSpace=THREE.NoColorSpace;bump.needsUpdate=true;
    const material=m.stone.clone();material.color.set('#b6af9f');material.map=texture;material.bumpMap=bump;
    material.bumpScale=kind==='setts'?.018:kind==='cinder'?.024:.009;material.roughness=.96;
    return material;
  }
  const roads=Object.fromEntries(['macadam','setts','cinder'].map(kind=>[kind,roadMaterial(kind)]));
  const pavement=m.stone.clone();pavement.color.set('#aaa392');pavement.roughness=.96;
  const path=m.ground.clone();path.color.set('#9b9078');
  const ballast=m.stone.clone();ballast.color.set('#605e55');
  const earth=m.ground.clone();earth.color.set('#777463');
  const ground=(x,z)=>{
    let h=x>=x0&&x<=x1&&z>=z0&&z<=z1?Math.max(.12,level(x,z)):.12;
    h=Math.max(h,highStreetSurfaceHeight(x,z,infra.sewerHighStreet)-.065);
    for(const bridge of infra.roadBridges)for(let i=1;i<bridge.route.length;i++) {
      const a=bridge.route[i-1],b=bridge.route[i],dx=b[0]-a[0],dz=b[1]-a[1];
      const t=Math.max(0,Math.min(1,((x-a[0])*dx+(z-a[1])*dz)/(dx*dx+dz*dz)));
      const distance=Math.hypot(x-a[0]-t*dx,z-a[1]-t*dz);
      h=Math.max(h,bridge.height-.065-distance*.12);
    }
    return h;
  };
  function surface(triangles,material,offset=0,hasHeight=false) {
    const vertices=[], supports=[];
    for(const tri of triangles) {
      const points=tri.map(p=>hasHeight?p:[p[0],ground(...p)+offset,p[1]]);
      // Consistent upward winding for Shapely's x/z triangles.
      const [a,b,c]=points;
      if((b[0]-a[0])*(c[2]-a[2])-(b[2]-a[2])*(c[0]-a[0])>0)points.reverse();
      vertices.push(...points.flat());
      if(!hasHeight && points.some(p=>p[1]>.4)) {
        // Fill raised bridge approaches down to the ground instead of leaving
        // the road as a floating sheet. Internal faces disappear inside the fill.
        for(let j=0;j<3;j++) {
          const a=points[j], b=points[(j+1)%3];
          const low=p=>[p[0],Math.max(.1,level(p[0],p[2])),p[2]];
          supports.push(...a,...low(a),...b,...b,...low(a),...low(b));
        }
      }
    }
    const geometry=new THREE.BufferGeometry();
    geometry.setAttribute('position',new THREE.Float32BufferAttribute(vertices,3));
    const uv=[];
    for(let i=0;i<vertices.length;i+=3)uv.push(vertices[i],vertices[i+2]);
    geometry.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));geometry.computeVertexNormals();
    scene.add(new THREE.Mesh(geometry,material));
    if(supports.length) {
      const fill=new THREE.BufferGeometry();
      fill.setAttribute('position',new THREE.Float32BufferAttribute(supports,3));
      const uv=[];for(let i=0;i<supports.length;i+=3)uv.push(supports[i],supports[i+1]);
      fill.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));fill.computeVertexNormals();
      scene.add(new THREE.Mesh(fill,earth));
    }
  }
  for(const [kind,triangles] of Object.entries(infra.roadSurfaces))surface(triangles,roads[kind],.065);
  surface(infra.shoulderTriangles,pavement,.095);
  surface(infra.pathTriangles,path,.05);
  function segment(a,b) {
    const length=Math.hypot(b[0]-a[0],b[1]-a[1]),g=new THREE.Group();
    g.position.set((a[0]+b[0])/2,0,(a[1]+b[1])/2);g.rotation.y=-Math.atan2(b[1]-a[1],b[0]-a[0]);scene.add(g);
    return {g,length};
  }
  for(const bridge of infra.roadBridges) for(let i=1;i<bridge.route.length;i++) {
    const {g,length}=segment(bridge.route[i-1],bridge.route[i]);
    if(bridge.style?.endsWith('-arch')) {
      const material=bridge.style==='brick-arch'?m.brick:m.stone;
      const count=bridge.archCount||1, bay=length/count, pier=count>1?1.1:.7;
      // Simple segmental openings. Materials and arch counts are documented;
      // clearances, voussoir dimensions and deck heights remain interpretations.
      for(let arch=0;arch<count;arch++) {
        const left=-length/2+arch*bay+pier/2, right=left+bay-pier;
        const shape=new THREE.Shape();
        shape.moveTo(left,bridge.height-.4);shape.lineTo(right,bridge.height-.4);
        for(let j=0;j<=32;j++) {
          const t=1-j/32;
          shape.lineTo(left+(right-left)*t,.3+(bridge.height-1.0)*Math.pow(Math.sin(Math.PI*t),.65));
        }
        shape.closePath();
        const geometry=new THREE.ExtrudeGeometry(shape,{depth:bridge.width,bevelEnabled:false,steps:1});
        const mesh=new THREE.Mesh(geometry,material);mesh.position.z=-bridge.width/2;g.add(mesh);
      }
      for(let j=0;j<=count;j++)box(g,-length/2+j*bay,-.15,0,pier,bridge.height-.25,bridge.width);
    }
    box(g,0,bridge.height-.4,0,length,.4,bridge.width,m.stone);
    if(bridge.surface)box(g,0,bridge.height,0,length,.02,bridge.width,roads[bridge.surface]);
    const parapet=bridge.style==='stone-arch'?m.stone:m.brick;
    for(const sign of [-1,1]) {
      box(g,0,bridge.height,sign*(bridge.width/2-.15),length,.9,.3,parapet);
      box(g,0,bridge.height+.9,sign*(bridge.width/2-.15),length,.12,.42,m.stone);
      if(bridge.style)box(g,0,bridge.height+.025,sign*(bridge.width/2-.9),length,.12,1.15,pavement);
    }
  }
  for(const railway of infra.railways) {
    if(railway.detailedMainline || railway.detailedRailway) {
      const detail=greatEastern({THREE,scene,m,railway,box,surface,ballast});
      if(railway.detailedMainline)scene.userData.greatEastern=detail;
      else (scene.userData.railConnections ||= []).push(detail);
      continue;
    }
    surface(railway.embankment,earth,0,true);
    const h=railway.formationHeight;
    for(let i=1;i<railway.route.length;i++) {
      const {g,length}=segment(railway.route[i-1],railway.route[i]);
      box(g,0,h,0,length,.24,8.6,ballast);
      for(const track of [-1.8,1.8]) {
        for(const rail of [-.718,.718])box(g,0,h+.33,track+rail,length,.13,.09,m.iron);
        for(let x=-length/2;x<length/2;x+=2.5)box(g,x,h+.24,track,.22,.18,2.4,m.wood);
      }
    }
    for(const crossing of railway.crossings) {
      for(let i=1;i<crossing.length;i++) {
        const {g,length}=segment(crossing[i-1],crossing[i]);
        box(g,0,h-.5,0,length,.5,8.6,m.iron);
        for(const sign of [-1,1])box(g,0,h-.5,sign*4.15,length,1.15,.22,m.iron);
      }
      // Abutments at the gap edges keep water/road space clear beneath the span.
      for(const end of [0,crossing.length-1]) {
        const a=crossing[end],b=crossing[end===0?1:end-1],{g}=segment(a,b);
        const q=new THREE.Group();q.position.set(a[0],0,a[1]);q.rotation.y=g.rotation.y;scene.add(q);
        box(q,0,.05,0,1.3,h-.55,9,m.brick);
      }
    }
  }
  return {roadRoutes:infra.roads.length,roadBridges:infra.roadBridges.length,
    namedBridges:infra.roadBridges.map(b=>b.id||b.name),raisedRailways:infra.railways.length,railFormationHeight:5.5};
}
