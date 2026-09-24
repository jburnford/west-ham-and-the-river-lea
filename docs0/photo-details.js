// Original geometry informed by the local photo references. See PHOTO_LAYERS.md.
// Dimensions and placement remain study assumptions; no photo is used as a texture.
export function photoDetails({ THREE, scene, materials: m, box, cylinder, beam, random }) {
  const brickLight=m.brick.clone();brickLight.color.set('#b2ab96');
  const red=m.brick.clone();red.color.set('#8d6f58');
  const trim=m.stone.clone();trim.color.set('#99978b');
  const green=m.iron.clone();green.color.set('#62776d');

  function archShape(w,h) {
    const s=new THREE.Shape(),r=w/2;
    s.moveTo(-r,0);s.lineTo(r,0);s.lineTo(r,h-r);s.absarc(0,h-r,r,0,Math.PI,false);s.lineTo(-r,0);
    return s;
  }
  function arch(parent,x,y,z,w,h,rotation=0,frame=trim) {
    const g=new THREE.Group();g.position.set(x,y,z);g.rotation.y=rotation;parent.add(g);
    const outer=archShape(w+.5,h+.25),inner=archShape(w,h);
    outer.holes.push(new THREE.Path(inner.getPoints(16)));
    g.add(new THREE.Mesh(new THREE.ExtrudeGeometry(outer,{depth:.22,bevelEnabled:false,curveSegments:8}),frame));
    const glass=new THREE.Mesh(new THREE.ShapeGeometry(inner,12),m.window);glass.position.z=.02;g.add(glass);
    box(g,0,0,.05,.09,h,.06,trim);
    for(let v=.9;v<h-.4;v+=1.1) box(g,0,v,.05,w,.06,.06,trim);
    box(g,0,-.14,.08,w+.6,.2,.4,trim);
    return g;
  }
  function curveBeam(parent,points,r,material) {
    const curve=new THREE.CatmullRomCurve3(points.map(p=>new THREE.Vector3(...p)));
    parent.add(new THREE.Mesh(new THREE.TubeGeometry(curve,32,r,5,false),material));
  }
  function roofLoft(parent,levels,material=m.roof) {
    const vertices=[];
    for(let i=1;i<levels.length;i++) {
      const [y0,w0,d0]=levels[i-1],[y1,w1,d1]=levels[i];
      const lower=[[-w0/2,y0,-d0/2],[w0/2,y0,-d0/2],[w0/2,y0,d0/2],[-w0/2,y0,d0/2]];
      const upper=[[-w1/2,y1,-d1/2],[w1/2,y1,-d1/2],[w1/2,y1,d1/2],[-w1/2,y1,d1/2]];
      for(let j=0;j<4;j++) {const k=(j+1)%4;for(const v of [lower[j],upper[j],upper[k],lower[j],upper[k],lower[k]]) vertices.push(...v);}
    }
    const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(vertices,3));geometry.computeVertexNormals();
    parent.add(new THREE.Mesh(geometry,material));
  }
  function finial(parent,x,y,z,h=3) {
    cylinder(parent,x,y,z,.05,.09,h,m.iron,6);
    cylinder(parent,x,y+h*.65,z,.22,.22,.35,trim,8);
    beam(parent,[x-.5,y+h*.82,z],[x+.5,y+h*.82,z],.055,m.iron);
  }
  function station() {
    const g=new THREE.Group();g.position.set(-185,0,-13);scene.add(g);
    // Author's supplied Mary Evans 1868 engraving: original geometry only.
    // Relative silhouettes guide these estimates; this is not a measured elevation.
    function stationArch(parent,x,y,z,w,h,rotation=0) {
      const a=arch(parent,x,y,z,w,h,rotation,red),r=w/2+.15;
      for(let i=0;i<11;i++) {
        const angle=(i+.5)*Math.PI/11;
        const block=box(a,Math.cos(angle)*r,h-w/2+Math.sin(angle)*r-.13,.25,.25,.3,.16,i%2?red:trim);
        block.rotation.z=angle-Math.PI/2;
      }
      return a;
    }
    function octagonalRoof(parent,x,z,profile) {
      for(let i=1;i<profile.length;i++) {
        const [y0,r0]=profile[i-1],[y1,r1]=profile[i];
        cylinder(parent,x,y0,z,r1,r0,y1-y0,m.roof,8);
      }
    }
    for(const [w,d] of [[54,20],[20,48]]) {
      box(g,0,0,0,w,13,d,brickLight);
      for(const y of [.35,6.4,12.7]) {
        box(g,0,y,0,w+.5,.3,d+.5,trim);
      }
      roofLoft(g,[[13,w+1,d+1],[18,w-4,d-5],[20,w-12,d-12]]);
      box(g,0,19.9,0,w-12,.15,d-12,m.roof);
      for(const sign of [-1,1]) {
        for(let x=-w/2+4;x<w/2-2;x+=5.6) {
          if(w===20 || Math.abs(x)<11) continue;
          for(const [y,h] of [[1.2,4.8],[8,3.5]]) stationArch(g,x,y,sign*(d/2+.02),2.5,h,sign===1?0:Math.PI);
        }
        for(let z=-d/2+4;z<d/2-2;z+=5.6) {
          if(d===20 || Math.abs(z)<11) continue;
          for(const [y,h] of [[1.2,4.8],[8,3.5]]) stationArch(g,sign*(w/2+.02),y,z,2.5,h,sign===1?Math.PI/2:-Math.PI/2);
        }
      }
    }
    // Five-bay arm ends: paired storeys, projecting piers and central porch.
    for(const [x,z,angle] of [[0,24,0],[27,0,Math.PI/2],[0,-24,Math.PI],[-27,0,-Math.PI/2]]) {
      const front=new THREE.Group();front.position.set(x,0,z);front.rotation.y=angle;g.add(front);
      for(const bx of [-7.2,-3.6,0,3.6,7.2]) {
        stationArch(front,bx,1.15,.04,2.45,4.7);
        const window=stationArch(front,bx,7.8,.04,2.45,bx===0?4.0:3.65);
        // Slender internal columns give the upper openings more depth.
        for(const dx of [-.47,.47])cylinder(window,dx,.15,.18,.055,.055,2.75,trim,6);
      }
      for(const bx of [-9,-5.4,-1.8,1.8,5.4,9]) {
        box(front,bx,.4,.16,.4,12.1,.38,trim);
        box(front,bx,6.2,.25,.62,.4,.55,trim);
      }
      const porch=new THREE.Group();porch.position.z=.7;front.add(porch);
      for(const bx of [-1.7,1.7]) {box(porch,bx,.4,0,.55,4.1,1.4,brickLight);box(porch,bx,4.35,.05,.8,.35,1.5,trim);}
      stationArch(porch,0,.4,.78,2.8,4.65);
      roofLoft(porch,[[5.15,4.3,2],[6.25,.06,2]],trim);
      for(let bx=-9.5;bx<10;bx+=1.3)box(front,bx,12,.1,.45,.65,.6,trim);
    }
    // Dormers project from the steep lower roof slopes.
    for(const x of [-21,-15,15,21]) for(const sign of [-1,1]) {
      const dormer=new THREE.Group();dormer.position.set(x,14,sign*9);dormer.rotation.y=sign===1?0:Math.PI;g.add(dormer);
      box(dormer,0,0,0,3.5,3,2.5,trim);arch(dormer,0,.3,1.28,2,2.5,0,trim);
      const cap=new THREE.Mesh(new THREE.ConeGeometry(2.5,1.6,4),m.roof);cap.rotation.y=Math.PI/4;cap.position.y=3.7;dormer.add(cap);
      finial(dormer,0,4.4,0,1.3);
    }
    for(const z of [-18,18])for(const sign of [-1,1]) {
      const dormer=new THREE.Group();dormer.position.set(sign*9,14,z);dormer.rotation.y=sign*Math.PI/2;g.add(dormer);
      box(dormer,0,0,0,3.2,2.7,2.5,trim);stationArch(dormer,0,.2,1.28,1.8,2.3);
      roofLoft(dormer,[[2.7,3.6,2.9],[4.0,.05,2.9]]);finial(dormer,0,4.0,0,1.3);
    }
    // More compact lantern, below the tall chimney crowns as in the engraving.
    cylinder(g,0,13,0,4.7,7.1,8,m.roof,8);
    cylinder(g,0,21,0,4.7,4.7,8,red,8);
    for(let i=0;i<8;i++) {
      const angle=(i+.5)*Math.PI/4,rr=4.7*Math.cos(Math.PI/8)+.04;
      const face=stationArch(g,Math.sin(angle)*rr,21.4,Math.cos(angle)*rr,2.4,6.8,angle);
      for(const dx of [-.48,.48])cylinder(face,dx,.2,.17,.07,.07,5.8,green,6);
      beam(face,[-1.5,6.9,.05],[0,8.3,.05],.14,trim);beam(face,[0,8.3,.05],[1.5,6.9,.05],.14,trim);
      const edge=i*Math.PI/4;
      cylinder(g,Math.sin(edge)*4.8,20.8,Math.cos(edge)*4.8,.2,.26,8.5,trim,8);
      finial(g,Math.sin(edge)*4.8,29.3,Math.cos(edge)*4.8,1.4);
    }
    octagonalRoof(g,0,0,[[29,5.2],[29.5,5.4],[31,4.4],[32.8,2.3],[34.2,.25]]);finial(g,0,34.2,0,2.5);
    // Corner turrets and cornice teeth visible in the modern architectural reference.
    for(const [x,z] of [[-11,-11],[-11,11],[11,-11],[11,11]]) {
      cylinder(g,x,8,z,1.9,2.2,9.5,brickLight,8);
      octagonalRoof(g,x,z,[[17.5,2.7],[18,2.8],[19.3,1.8],[20.8,.2]]);finial(g,x,20.8,z,2);
      for(let i=0;i<8;i++) {const a=(i+.5)*Math.PI/4;arch(g,x+Math.sin(a)*1.82,14.3,z+Math.cos(a)*1.82,.6,1.8,a,trim);}
    }
    for(let x=-26;x<27;x+=1.5) for(const z of [-10.25,10.25]) box(g,x,12,z,.6,.7,.7,trim);
    // Fine ridge cresting and pinnacles break the previously plain roof silhouette.
    for(let x=-20;x<=20;x+=1.2)if(Math.abs(x)>6) {
      beam(g,[x-.5,20.2,0],[x,20.95,0],.045,m.iron);beam(g,[x,20.95,0],[x+.5,20.2,0],.045,m.iron);
    }
    for(let z=-17;z<=17;z+=1.2)if(Math.abs(z)>6) {
      beam(g,[0,20.2,z-.5],[0,20.95,z],.045,m.iron);beam(g,[0,20.95,z],[0,20.2,z+.5],.045,m.iron);
    }
    // Broad decorated bases, slender shafts and pointed openwork crowns.
    // Both remain on the previous provisional anchors; dimensions are interpreted.
    for(const [x,z] of [[-41,-37],[41,37]]) {
      const stack=new THREE.Group();stack.position.set(x,0,z);g.add(stack);
      cylinder(stack,0,0,0,5.7,6.4,.65,trim,8);
      cylinder(stack,0,.65,0,4.6,5.7,5.4,brickLight,8);
      cylinder(stack,0,6.05,0,5.7,4.6,.55,trim,8);
      cylinder(stack,0,6.6,0,2.55,5.7,1.8,brickLight,8);
      cylinder(stack,0,8.4,0,2.5,2.5,.4,trim,8);
      for(let i=0;i<8;i++) {
        const angle=(i+.5)*Math.PI/4,rr=4.9;
        stationArch(stack,Math.sin(angle)*rr,1.25,Math.cos(angle)*rr,1.35,3.7,angle);
      }
      cylinder(stack,0,8.8,0,1.55,2.25,35.2,brickLight,8);
      const radius=y=>2.25-(y-8.8)*.7/35.2;
      for(let y=11;y<43;y+=3.3) {
        cylinder(stack,0,y,0,radius(y)+.035,radius(y)+.035,.13,trim,8);
        // Sparse diagonal masonry ribs suggest the engraved shaft's diaper pattern.
        for(let i=0;i<8;i++) {
          const a=(i+.5)*Math.PI/4,nx=Math.sin(a),nz=Math.cos(a),tx=Math.cos(a),tz=-Math.sin(a),rr=radius(y)*.924+.015;
          const p=(u,v)=>[nx*rr+tx*u,y+v,nz*rr+tz*u];
          beam(stack,p(-.5,0),p(.5,2.5),.035,red);beam(stack,p(.5,0),p(-.5,2.5),.035,red);
        }
      }
      cylinder(stack,0,44,0,2.1,1.55,.8,trim,8);
      cylinder(stack,0,44.8,0,2.2,2.2,.35,trim,16);
      cylinder(stack,0,45.15,0,1.35,1.65,2.0,brickLight,8);
      cylinder(stack,0,47.15,0,.22,1.15,5.7,brickLight,8);
      for(let i=0;i<8;i++) {
        const a=i*Math.PI/4,s=Math.sin(a),c=Math.cos(a);
        curveBeam(stack,[[s*1.9,45.2,c*1.9],[s*1.25,47,c*1.25],[s*1.45,49,c*1.45],[s*.65,51.6,c*.65],[s*.2,53,c*.2]],.095,trim);
        finial(stack,s*1.45,49,c*1.45,2.2);
      }
      finial(stack,0,52.85,0,1.8);
    }
    scene.userData.stationStudy={reference:'Mary Evans 45687726, supplied 1868 engraving',wingEndBays:5,chimneys:2,chimneyHeight:54.65,lanternHeight:36.7,dimensionsInterpreted:true};
    return g;
  }
  function factory(b) {
    const g=new THREE.Group();g.position.set(b.x,.15,b.z);scene.add(g);
    g.rotation.y=(b.rotation||0)*Math.PI/180;
    // Keep the mapped envelope. Roof divisions/elevations are comparative studies,
    // not identifications of individual buildings in the historic photographs.
    const curved=b.siteId===253, sections=b.mapped?Math.max(1,Math.round(b.depth/23)):1;
    const span=b.depth/sections;
    for(let section=0;section<sections;section++) {
      const part=new THREE.Group();part.position.z=-b.depth/2+(section+.5)*span;g.add(part);
      const w=b.width,d=span,h=b.height-(section%3)*.65;
      const wall=(b.siteId===512 || b.siteId===253)?brickLight:m.brick;
      box(part,0,0,0,w,h,d,wall);
      // Low pitched industrial ranges, with a raised ventilator on selected roofs.
      roofLoft(part,[[h,w+.65,d+.35],[h+2.6,.08,d+.35]]);
      for(const sign of [-1,1]) {
        const front=new THREE.Group();front.position.z=sign*(d/2+.02);front.rotation.y=sign===1?0:Math.PI;part.add(front);
        const shape=new THREE.Shape();shape.moveTo(-w/2,h);shape.lineTo(w/2,h);
        if(curved) { shape.lineTo(w/2,h+.65);shape.quadraticCurveTo(0,h+6.5,-w/2,h+.65); }
        else { shape.lineTo(0,h+2.6); }
        shape.closePath();front.add(new THREE.Mesh(new THREE.ExtrudeGeometry(shape,{depth:.3,bevelEnabled:false,curveSegments:12}),wall));
        if(curved) {
          const oculus=new THREE.Mesh(new THREE.CircleGeometry(.64,16),m.window);oculus.position.set(0,h+1.2,.32);front.add(oculus);
          const ring=new THREE.Mesh(new THREE.TorusGeometry(.78,.12,5,16),wall);ring.position.set(0,h+1.2,.34);front.add(ring);
        }
        // Tall loading entrance and narrower windows break the repeated frontage.
        box(front,0,.08,.32,2.5,Math.min(4,h-1),.18,m.wood);
        for(const x of [-w*.31,w*.31]) {
          arch(front,x,1.25,.32,1.65,2.8,0,wall);
          if(h>10) arch(front,x,5.6,.32,1.5,2.5,0,wall);
        }
        box(front,0,.04,.3,w,.38,.4,m.stone);
        for(let z=-d/2+2.5,bay=0;z<d/2-1;z+=4.3,bay++) {
          const side=new THREE.Group();side.position.set(sign*(w/2+.025),0,z);side.rotation.y=sign===1?Math.PI/2:-Math.PI/2;part.add(side);
          if(bay%5===2) {
            box(side,0,.1,.08,2.2,3.8,.16,m.wood);
            box(side,0,3.9,.17,2.6,.22,.45,wall);
            for(const x of [-.85,-.42,0,.42,.85]) box(side,x,.15,.18,.025,3.65,.02,m.dark);
          } else arch(side,0,1.4,.08,1.6,2.8,0,wall);
          if(h>9.5 && !(b.siteId===875 && bay%3===1)) arch(side,0,5.7,.08,1.5,2.5,0,wall);
          box(side,-2.05,0,.05,.42,h,.4,wall);
        }
        // Eaves shadows, rainwater pipes and a dark plinth ground each range.
        box(part,sign*(w/2+.2),h-.2,0,.32,.22,d+.6,m.iron);
        box(part,sign*(w/2+.04),.05,0,.12,.55,d,m.dark);
        for(const z of [-d/2+.5,d/2-.5]) {
          cylinder(part,sign*(w/2+.26),.2,z,.075,.075,h,m.iron,6);
          beam(part,[sign*(w/2+.26),.4,z],[sign*(w/2+.65),.15,z],.08,m.iron);
        }
      }
      if((section+b.siteId)%2===0) {
        box(part,0,h+2.35,0,2.2,.65,d*.62,m.dark);
        roofLoft(part,[[h+3,3,d*.65],[h+3.55,.08,d*.65]]);
        for(let z=-d*.27;z<d*.3;z+=1.3) box(part,0,h+2.35,z,2.25,.65,.1,m.wood);
      }
      box(part,0,h+2.55,0,.18,.16,d+.5,m.stone);
    }
    return g;
  }
  function barge(x,z,angle,loaded) {
    const g=new THREE.Group();g.position.set(x,.14,z);g.rotation.y=angle*Math.PI/180;scene.add(g);
    const shape=new THREE.Shape();shape.moveTo(-2.7,-7.8);shape.bezierCurveTo(-2.7,-11.8,2.7,-11.8,2.7,-7.8);
    shape.lineTo(2.7,7.2);shape.bezierCurveTo(2.7,11.3,-2.7,11.3,-2.7,7.2);shape.closePath();
    const hole=new THREE.Path();hole.moveTo(-2.05,-6.8);hole.lineTo(-2.05,6.4);hole.quadraticCurveTo(0,8,2.05,6.4);hole.lineTo(2.05,-6.8);hole.closePath();shape.holes.push(hole);
    const hull=new THREE.Mesh(new THREE.ExtrudeGeometry(shape,{depth:1.45,bevelEnabled:true,bevelSize:.12,bevelThickness:.1,bevelSegments:1,steps:1,curveSegments:16}),m.wood);
    hull.rotation.x=-Math.PI/2;g.add(hull);
    box(g,0,.24,0,4.4,.12,14.5,m.dark);
    // Outer rubbing strakes and transverse timbers frame a visibly hollow hold.
    const rim=shape.getPoints(32).map(p=>[p.x,1.54,-p.y]);curveBeam(g,rim,.12,m.wood);
    curveBeam(g,rim.map(([a,_,c])=>[a,.5,c]),.10,m.dark);
    for(const zz of [-5.5,0,5.5]) box(g,0,1.3,zz,4.7,.18,.23,m.wood);
    for(const zz of [-8.4,8.4]) {
      box(g,0,1.5,zz,.25,.2,2.2,m.wood);
      cylinder(g,0,1.5,zz,.18,.18,.5,m.iron,8);box(g,0,1.9,zz,.9,.12,.15,m.iron);
    }
    // Plank seams on solid end decks and small cleats suggest the scale of a working lighter.
    for(let xx=-2;xx<=2;xx+=.4) for(const zz of [-8.1,8]) box(g,xx,1.48,zz,.025,.04,2.6,m.dark);
    if(loaded) {
      // A continuous load beneath densely packed angular coal and fines.
      // Several intersecting humps, not a few large rounded boulders.
      const mound=(x,z)=>.85+1.8*Math.pow(Math.max(0,1-(x/2.05)**2),.8)*Math.pow(Math.max(0,1-(z/7.2)**2),.7)
        +.13*Math.sin(z*1.7+x*3.1)*Math.max(0,1-Math.abs(x)/2.1);
      const geometry=new THREE.PlaneGeometry(4.05,14,20,60);
      geometry.rotateX(-Math.PI/2);
      const p=geometry.getAttribute('position');
      for(let i=0;i<p.count;i++) p.setY(i,mound(p.getX(i),p.getZ(i))+(random()-.5)*.12);
      geometry.computeVertexNormals();g.add(new THREE.Mesh(geometry,m.coal));
      const pieces=Array.from({length:7},(_,variant)=>{
        const geometry=new THREE.IcosahedronGeometry(1,0),p=geometry.getAttribute('position');
        for(let i=0;i<p.count;i++) {
          const x=p.getX(i),y=p.getY(i),z=p.getZ(i),factor=1+.3*Math.sin(x*7+y*13+z*17+variant);
          p.setXYZ(i,x*factor,y*factor,z*factor);
        }
        geometry.computeVertexNormals();return geometry;
      });
      for(let i=0;i<1450;i++) {
        const xx=(random()-.5)*3.9,zz=(random()-.5)*13.5;
        const radius=.045+Math.pow(random(),2)*.19;
        const chunk=new THREE.Mesh(pieces[i%pieces.length],m.coal);
        chunk.scale.set(radius*(.7+random()),radius*(.6+random()*.8),radius*(.7+random()));
        chunk.position.set(xx,mound(xx,zz)+radius*.12,zz);chunk.rotation.set(random()*3,random()*3,random()*3);g.add(chunk);
      }
    }
    curveBeam(g,[[0,1.9,-8.4],[1,.8,-11],[2,.1,-14]],.045,m.wood);
    return g;
  }
  function waterfront() {
    const wharf=[[23,25],[32,55],[40,90],[21,116],[4,132]];
    for(let i=1;i<wharf.length;i++) {
      const [ax,az]=wharf[i-1],[bx,bz]=wharf[i],length=Math.hypot(bx-ax,bz-az),a=Math.atan2(bx-ax,bz-az);
      for(let y=.1;y<2.8;y+=.35) {
        const plank=box(scene,(ax+bx)/2,y,(az+bz)/2,.55,.29,length,m.wood);plank.rotation.y=a;
      }
      for(let d=0;d<length;d+=3) {const t=d/length;
        cylinder(scene,ax+(bx-ax)*t,0,az+(bz-az)*t,.24,.3,3.2,m.wood,7);
      }
      const cap=box(scene,(ax+bx)/2,2.8,(az+bz)/2,1.1,.2,length,m.wood);cap.rotation.y=a;
    }
    // Mooring posts stand on both banks; ropes sag to their attachment points.
    for(const [x,z] of [[29,46],[36,71],[-31,34],[-40,92]]) {
      cylinder(scene,x,0,z,.3,.4,2.1,m.wood,8);
      curveBeam(scene,[[x,1.8,z],[x+2,.8,z+4],[x+4,1.8,z+8]],.055,m.wood);
    }
  }
  function holder(spec) {
    const g=new THREE.Group();g.position.set(spec.x,0,spec.z);g.scale.set(spec.radius/31,spec.height/28,spec.radius/31);scene.add(g);
    const bellTop=spec.bellHeight*28/spec.height;
    cylinder(g,0,0,0,30,30,2,m.stone,56);cylinder(g,0,2,0,28,28,bellTop-2,m.bell,56);
    cylinder(g,0,bellTop,0,24,28,1.8,m.bell,56);
    for(let i=0;i<spec.columns;i++) {
      const a=i*Math.PI*2/spec.columns,b=(i+1)*Math.PI*2/spec.columns,x=Math.cos(a)*31,z=Math.sin(a)*31;
      cylinder(g,x,2,z,.32,.48,26,m.iron,8);
      for(const y of [2,14,27]) {cylinder(g,x,y,z,.7,.7,.7,trim,8);cylinder(g,x,y+.7,z,.45,.65,.5,m.iron,8);}
      for(const y of [15,28]) {
        const ex=Math.cos(b)*31,ez=Math.sin(b)*31;
        beam(g,[x,y,z],[ex,y,ez],.2,m.iron);beam(g,[x,y-.9,z],[ex,y-.9,ez],.18,m.iron);
        // Shallow lattice girders, not the later full-height diagonal alterations.
        for(let j=0;j<4;j++) {const t=j/4,u=(j+1)/4;
          beam(g,[x+(ex-x)*t,y,z+(ez-z)*t],[x+(ex-x)*u,y-.9,z+(ez-z)*u],.07,m.iron);
        }
      }
      const bx=Math.cos(a)*28.04,bz=Math.sin(a)*28.04;
      beam(g,[bx,2,bz],[bx,bellTop,bz],.07,m.iron);
    }
    for(const y of [bellTop*.3,bellTop*.55,bellTop*.8,bellTop]) {
      const ring=new THREE.Mesh(new THREE.TorusGeometry(28.06,.065,4,56),m.iron);ring.rotation.x=Math.PI/2;ring.position.y=y;g.add(ring);
    }
    return g;
  }
  function houses(spec) {
    const g=new THREE.Group();g.position.set(spec.x,0,spec.z);g.rotation.y=spec.rotation*Math.PI/180;scene.add(g);
    const w=spec.width,d=spec.depth,h=spec.wallHeight;
    box(g,0,0,0,w,h,d,brickLight);roofLoft(g,[[h,w+.7,d+.7],[h+3,w-5,1]]);
    box(g,0,h+2.95,0,w-5,.1,1,m.roof);
    for(const y of [.35,3.3,6.1]) box(g,0,y,0,w+.25,.15,d+.25,red);
    for(const sign of [-1,1]) {
      // Paired entrances, round-headed windows and projecting gabled end bays.
      box(g,sign*4.5,0,d/2+.5,3.8,h,1.4,brickLight);
      const bay=new THREE.Group();bay.position.set(sign*4.5,0,d/2+.5);g.add(bay);
      roofLoft(bay,[[h,4.3,2],[h+2,.05,2]],m.roof);
      for(const y of [1,4]) arch(g,sign*4.5,y,d/2+1.23,1.5,2.1,0,red);
      arch(g,sign*1.2,.15,d/2+.05,1.2,2.6,0,red);
      arch(g,sign*1.2,4,d/2+.05,1.3,2.1,0,red);
      for(const xx of [1.4,4.5]) for(const y of [1,4]) arch(g,sign*xx,y,-d/2-.05,1.3,2.1,Math.PI,red);
      box(g,sign*3,h+1.3,-1,1.1,2.8,.85,m.brick);box(g,sign*3,h+3.9,-1,1.4,.25,1.1,trim);
      for(const xx of [-.25,.25]) cylinder(g,sign*3+xx,h+4.2,-1,.12,.15,.6,red,8);
    }
    return g;
  }
  function terrace(spec) {
    const g=new THREE.Group();g.position.set(spec.x,0,spec.z);g.rotation.y=spec.rotation*Math.PI/180;scene.add(g);
    const w=spec.width,d=spec.depth,h=spec.wallHeight,bay=w/spec.bays;
    // Continuous street roof, repeated stacks and two-storey facades: original geometry.
    // Only the row envelope is mapped; bay divisions and elevations are interpreted.
    box(g,0,0,0,w,h,d,brickLight);
    roofLoft(g,[[h,w+.4,d+.4],[h+2.4,w+.4,.08]]);
    box(g,0,h+2.35,0,w+.4,.15,.18,m.roof);
    for(let i=0;i<spec.bays;i++) {
      const x=-w/2+(i+.5)*bay;
      for(const sign of [-1,1]) {
        const z=sign*(d/2+.05);
        for(const y of [1.2,4.1]) for(const offset of [-bay*.22,bay*.22]) {
          if(y===1.2 && offset<0) continue;
          box(g,x+offset,y,z,1.05,1.6,.12,m.window);
          box(g,x+offset,y-.13,z+sign*.06,1.2,.15,.25,trim);
          box(g,x+offset,y+1.65,z+sign*.03,1.2,.2,.2,red);
          box(g,x+offset,y+.7,z+sign*.08,1.05,.06,.08,trim);
        }
        box(g,x-bay*.22,.12,z,.95,2.2,.12,m.window);
      }
      if(i%2===0) {
        box(g,x,h+1.6,0,1.3,1.8,.8,m.brick);
        box(g,x,h+3.3,0,1.5,.25,1,trim);
        for(const offset of [-.4,0,.4]) cylinder(g,x+offset,h+3.55,0,.1,.14,.65,red,6);
      }
    }
    return g;
  }
  function mill(spec) {
    const g=new THREE.Group();g.position.set(spec.x,0,spec.z);g.rotation.y=spec.rotation*Math.PI/180;scene.add(g);
    const w=spec.width,d=spec.depth,h=spec.height;
    const boarding=m.wood.clone();boarding.color.set('#9a9e93');
    const boardsDark=m.wood.clone();boardsDark.color.set('#666d65');
    const tiles=m.roof.clone();tiles.color.set('#7b7160');
    // The c1800 image informs the interlocking gables, weatherboard upper floors
    // and masonry base. Survival of this form in 1900 is the author's hypothesis.
    box(g,0,0,0,w,3.1,d,brickLight);
    const ranges=[{x:-w*.325,w:w*.35,d:d*.94,h:h+.6,ridge:'z'},
      {x:0,w:w*.30,d:d,h:h-.35,ridge:'x'},
      {x:w*.325,w:w*.35,d:d*.94,h:h-.05,ridge:'z'}];
    for(const range of ranges) {
      const part=new THREE.Group();part.position.x=range.x;g.add(part);
      box(part,0,3.1,0,range.w,range.h-3.1,range.d,boarding);
      const rise=range.ridge==='z'?2.55:2.25;
      const top=range.ridge==='z'?[range.h+rise,.06,range.d+.3]:[range.h+rise,range.w+.3,.06];
      roofLoft(part,[[range.h,range.w+.35,range.d+.35],top],tiles);
      // Timber gable infill and thin horizontal lap boards carry the mill's scale.
      for(const sign of [-1,1]) {
        if(range.ridge==='z') {
          const shape=new THREE.Shape();shape.moveTo(-range.w/2,range.h);shape.lineTo(range.w/2,range.h);shape.lineTo(0,range.h+rise);shape.closePath();
          const face=new THREE.Mesh(new THREE.ShapeGeometry(shape),boarding);face.position.z=sign*(range.d/2+.01);if(sign<0) face.rotation.y=Math.PI;part.add(face);
          box(part,0,range.h+.45,sign*(range.d/2+.025),.65,.65,.06,m.window);
        }
        for(let y=3.1;y<range.h;y+=.22) {
          box(part,0,y,sign*(range.d/2+.025),range.w,.035,.06,boardsDark);
          box(part,sign*(range.w/2+.025),y,0,.06,.035,range.d,boardsDark);
        }
        for(const y of [3.9,6.65,9.35]) {
          if(y+1.05>range.h) continue;
          for(const x of [-range.w*.24,range.w*.24]) {
            box(part,x,y,sign*(range.d/2+.06),.72,1.03,.06,m.window);
            for(const edge of [-1,1]) box(part,x+edge*.4,y-.05,sign*(range.d/2+.095),.085,1.14,.07,boarding);
            box(part,x,y-.08,sign*(range.d/2+.1),.94,.1,.12,boarding);
            box(part,x,y+.48,sign*(range.d/2+.105),.74,.055,.06,boarding);
          }
          box(part,sign*(range.w/2+.055),y,0,.06,1.03,.76,m.window);
        }
      }
    }
    for(const sign of [-1,1]) {
      for(const x of [-w*.32,0,w*.32]) {
        arch(g,x,.22,sign*(d/2+.06),1.6,2.45,sign===1?0:Math.PI,brickLight);
        box(g,x,.22,sign*(d/2+.12),1.45,2.1,.09,m.wood);
      }
      for(const x of [-w*.18,w*.18]) {
        box(g,x,.08,sign*(d/2+.18),.24,3.05,.25,m.wood);
        beam(g,[x,.9,sign*(d/2+.18)],[x+(x<0?.75:-.75),3.03,sign*(d/2+.18)],.1,m.wood);
      }
    }
    // A low sloping wheel-house cover follows the earlier image's waterside form.
    // Mechanism and hydraulic levels are not reconstructed from that image.
    const cover=new THREE.Group();cover.position.set(-w*.27,0,d/2+.65);g.add(cover);
    box(cover,0,0,0,3.3,1.3,2,brickLight);
    const hood=box(cover,0,1.35,0,3.6,.14,2.35,tiles);hood.rotation.x=-.42;
    box(cover,0,.1,1.02,1.15,1.03,.06,m.dark);
    box(g,w*.39,h-1,-d*.28,.8,2.2,.65,brickLight);
    // Deliberately no windmill tower, cap or sails in the c1900 interpretation.
    return g;
  }
  function threeMills() {
    // Separate from Abbey Mill. Listed grid references locate these distant studies:
    // House Mill TQ3828582826; Clock Mill TQ3833482799. Dimensions/rotation estimated.
    const pale=m.wood.clone();pale.color.set('#c0bdb0');
    const house=new THREE.Group();house.position.set(-615,0,383);house.rotation.y=-.28;scene.add(house);
    box(house,0,0,0,36,10,16,brickLight);
    box(house,0,2.2,-8.04,22,7.8,.12,pale);
    for(let y=2.3;y<10;y+=.27)box(house,0,y,-8.12,22,.035,.04,m.wood);
    roofLoft(house,[[10,36.6,16.6],[16,36.6,.06]]);
    for(const sign of [-1,1]) {
      for(let i=0;i<10;i++)for(const y of [1,4,7]) {
        const x=-16.2+i*3.6;
        box(house,x,y,sign*8.15,1.15,1.8,.08,m.window);
        box(house,x,y-.1,sign*8.2,1.4,.14,.18,pale);
      }
      for(const y of [11,13.5])for(const x of [-10,0,10]) {
        const z=sign*(y===11?5.7:2.4);
        box(house,x,y,z,2,1.5,1.6,pale);
        box(house,x,y+.15,z+sign*.85,1.3,1.05,.08,m.window);
        box(house,x,y+1.5,z,2.3,.15,1.9,m.roof);
      }
    }
    const clock=new THREE.Group();clock.position.set(-566,0,410);clock.rotation.y=-.28;scene.add(clock);
    box(clock,-4,0,0,32,13.5,14,m.brick);
    const clockRoof=new THREE.Group();clockRoof.position.x=-4;clock.add(clockRoof);
    roofLoft(clockRoof,[[13.5,32.5,14.5],[17,32.5,.06]]);
    for(const sign of [-1,1])for(let i=0;i<8;i++)for(const y of [1,4.1,7.2,10.3]) {
      const x=-18+i*4;
      box(clock,x,y,sign*7.05,1.3,1.95,.1,m.window);
      box(clock,x,y-.12,sign*7.12,1.55,.15,.18,trim);
    }
    // Drying kilns and clock turret; later replacement cowls are omitted.
    for(const z of [-4.8,4.8]) {
      box(clock,18,0,z,11,9,9.4,m.brick);
      cylinder(clock,18,9,z,.45,7.2,7,m.roof,16);
    }
    const tx=12,tz=12;
    box(clock,tx,0,tz,5.2,10,5.2,brickLight);
    cylinder(clock,tx,10,tz,2.8,3.1,4,brickLight,8);
    cylinder(clock,tx,14,tz,2.25,2.6,3.8,pale,8);
    cylinder(clock,tx,17.8,tz,1.8,2.3,1.9,pale,8);
    cylinder(clock,tx,19.7,tz,0,2.3,2,m.roof,8);
    for(const sign of [-1,1]) {
      const dial=new THREE.Mesh(new THREE.CircleGeometry(.82,20),pale);
      dial.position.set(tx,16.2,tz+sign*2.48);if(sign<0)dial.rotation.y=Math.PI;clock.add(dial);
      box(clock,tx,16.2,tz+sign*2.51,.06,.59,.04,m.iron);
      box(clock,tx+.19,16.15,tz+sign*2.52,.43,.06,.04,m.iron);
    }
    finial(clock,tx,21.7,tz,1.5);
    return {house,clock};
  }
  return {station,factory,barge,waterfront,holder,houses,terrace,mill,threeMills};
}
