// Navigation limits inside the bridge crest, not surveyed historical dimensions.
export function createBridgeWalker(sewer) {
  const route=sewer.route;
  const middle=route.reduce((best,p,i)=>Math.hypot(...p)<Math.hypot(...route[best])?i:best,0);
  const before=route[middle-1],after=route[middle+1];
  // Bisect the two local bearings so the rectangle clears both parapets at the bend.
  const incoming=Math.hypot(...before),outgoing=Math.hypot(...after);
  const dx=after[0]/outgoing-before[0]/incoming,dz=after[1]/outgoing-before[1]/incoming;
  const length=Math.hypot(dx,dz),axis=[dx/length,dz/length];
  const across=[-axis[1],axis[0]];
  const limits={along:24,across:5.5};
  const position={along:0,across:limits.across};
  const clamp=(n,max)=>Math.max(-max,Math.min(max,n));
  function set(along,cross) {
    position.along=clamp(along,limits.along);position.across=clamp(cross,limits.across);
  }
  function world(along=position.along,cross=position.across) {
    return [axis[0]*along+across[0]*cross,sewer.height+1.6,axis[1]*along+across[1]*cross];
  }
  return {
    move(dx,dz) { set(position.along+dx*axis[0]+dz*axis[1],position.across+dx*across[0]+dz*across[1]); },
    side(name) { set(position.along,name==='north'?-limits.across:limits.across); },
    reset() { set(0,limits.across); },
    world,
    corners() {return [[-24,-5.5],[24,-5.5],[24,5.5],[-24,5.5]].map(([a,c])=>{const [x,_,z]=world(a,c);return [x,z];});},
    snapshot() {return {...position,limits:{...limits},axis:[...axis],acrossAxis:[...across]};}
  };
}
