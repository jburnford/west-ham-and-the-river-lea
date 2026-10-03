import { sewerSurfaceHeight } from './sewer-levels.js';

// Exterior massing at Channelsea, not a surveyed sewer section or invert.
// The 1900–02 rebuilding straddles our scene date: do not silently assign its
// five barrels / two central piers to the earlier three-barrel bridge.
export const crossingAssumptions = Object.freeze({
  halfLength: 30, coverDepth: .5, enclosureDepth: 2.9,
  abutmentLength: 3, foundationEmbedment: .6,
  status: 'provisional exterior; rebuilding phase unresolved',
  source: 'https://historicengland.org.uk/listing/the-list/list-entry/1392549',
});

export function sewerCrossing({ THREE, scene, sewer, crossing, level, materials }) {
  const spec = crossingAssumptions;
  const route = sewer.route;
  const anchor = route.findIndex(p => Math.hypot(...p) < .01);
  if (anchor < 1) throw new Error('Channelsea sewer anchor missing');
  const distances = [0];
  for (let i=1;i<route.length;i++) distances.push(distances[i-1]+Math.hypot(route[i][0]-route[i-1][0],route[i][1]-route[i-1][1]));
  const origin=distances[anchor];
  function point(d) {
    const s=origin+d, i=distances.findIndex((v,j)=>j>0 && v>=s);
    if(i<1) throw new Error('Sewer route does not cover Channelsea crossing');
    const t=(s-distances[i-1])/(distances[i]-distances[i-1]);
    return route[i-1].map((v,k)=>v+(route[i][k]-v)*t);
  }
  const cover=(p)=>sewerSurfaceHeight(...p,sewer,crossing);
  function section(d,width) {
    const p=point(d),a=point(d-.01),b=point(d+.01);
    const incoming=[p[0]-a[0],p[1]-a[1]],outgoing=[b[0]-p[0],b[1]-p[1]];
    const normal=v=>{const n=Math.hypot(...v);return [-v[1]/n,v[0]/n];};
    const na=normal(incoming),nb=normal(outgoing),sum=[na[0]+nb[0],na[1]+nb[1]];
    const n=Math.hypot(...sum),m=sum.map(v=>v/n),scale=width/2/(m[0]*na[0]+m[1]*na[1]);
    return [-1,1].map(side=>[p[0]+side*m[0]*scale,p[1]+side*m[1]*scale]);
  }
  const group=new THREE.Group();group.name='channelsea-sewer-crossing';scene.add(group);
  const bounds={};
  function box(parent,kind,x,y,z,w,h,d,material) {
    if(!(h>0))throw new Error(`Invalid Channelsea ${kind} height`);
    const mesh=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),material);
    mesh.position.set(x,y+h/2,z);mesh.name=kind;parent.add(mesh);
    return mesh;
  }
  // Include every mapped bend, so the enclosure remains directly below the deck.
  const stops=[-spec.halfLength,...distances.map(d=>d-origin).filter(d=>d>-spec.halfLength && d<spec.halfLength),spec.halfLength];
  for(let i=1;i<stops.length;i++) {
    const a=point(stops[i-1]),b=point(stops[i]);
    const length=Math.hypot(b[0]-a[0],b[1]-a[1]),ha=cover(a),hb=cover(b);
    const span=new THREE.Group();span.position.set((a[0]+b[0])/2,(ha+hb)/2,(a[1]+b[1])/2);
    span.rotation.y=-Math.atan2(b[1]-a[1],b[0]-a[0]);span.rotation.z=Math.atan2(hb-ha,length);group.add(span);
    const bottom=-spec.coverDepth-spec.enclosureDepth, width=sewer.crestWidth-.6;
    // Miter both ends: independent rectangular boxes leave an open wedge on
    // the outside of a bend, even when their centre lines meet.
    const sa=section(stops[i-1],width),sb=section(stops[i],width);
    const ring=[sa[1],sa[0],sb[0],sb[1]],tops=[ha,ha,hb,hb].map(h=>h-spec.coverDepth);
    const vertices=[...ring.flatMap(([x,z],j)=>[x,tops[j]-spec.enclosureDepth,z]),
      ...ring.flatMap(([x,z],j)=>[x,tops[j],z])];
    const geometry=new THREE.BufferGeometry();
    geometry.setAttribute('position',new THREE.Float32BufferAttribute(vertices,3));
    geometry.setIndex([0,1,2,0,2,3,4,7,6,4,6,5,0,4,5,0,5,1,
      1,5,6,1,6,2,2,6,7,2,7,3,3,7,4,3,4,0]);
    geometry.computeVertexNormals();
    const enclosure=new THREE.Mesh(geometry,materials.iron);enclosure.name='enclosure';group.add(enclosure);
    // Restrained plate-girder relief, informed by the local Abbey Mills photograph.
    // Spacing and section sizes are interpretation, not measured details.
    for(const side of [-1,1]) {
      for(const y of [bottom,bottom+spec.enclosureDepth-.12])
        box(span,'girder-flange',0,y,side*(width/2),length+.15,.12,.18,materials.iron);
      for(let x=-length/2+.4;x<length/2;x+=2.4)
        box(span,'girder-stiffener',x,bottom,side*(width/2),.12,spec.enclosureDepth,.18,materials.iron);
    }
  }
  // Foundations follow local ground; their tops follow the sewer, independently.
  // Bank locations checked against the mapped river; no new in-channel pier.
  for(const d of [-spec.halfLength+1,spec.halfLength-1]) {
    const p=point(d),a=point(d-.1),b=point(d+.1);
    const angle=Math.atan2(b[1]-a[1],b[0]-a[0]),axis=[Math.cos(angle),Math.sin(angle)];
    const samples=[level(...p)];
    for(const along of [-spec.abutmentLength/2,spec.abutmentLength/2])for(const across of [-sewer.crestWidth/2,sewer.crestWidth/2])
      samples.push(level(p[0]+along*axis[0]-across*axis[1],p[1]+along*axis[1]+across*axis[0]));
    const bottom=Math.min(...samples)-spec.foundationEmbedment;
    const top=cover(p)-spec.coverDepth-spec.enclosureDepth;
    const support=box(group,'abutment',p[0],bottom,p[1],spec.abutmentLength,top-bottom,sewer.crestWidth,materials.brick);
    support.rotation.y=-angle;
  }
  group.updateMatrixWorld(true);
  for(const kind of ['enclosure','abutment']) {
    const extent=new THREE.Box3();let count=0;
    group.traverse(o=>{if(o.isMesh && o.name===kind){extent.union(new THREE.Box3().setFromObject(o));count++;}});
    bounds[kind]={count,min:extent.min.toArray(),max:extent.max.toArray()};
  }
  return {status:spec.status,floodReady:false,deckHeight:cover([0,0]),bounds};
}
