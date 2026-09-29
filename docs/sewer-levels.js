// Surface-cover estimates at High Street, not a sewer invert/flow model.
export function sewerSurfaceHeight(x,z,sewer,crossing) {
  const distance=Math.hypot(x-crossing.centre[0],z-crossing.centre[1]);
  const t=Math.min(1,Math.max(0,(distance-12)/crossing.sewerApproachLength));
  return crossing.surfaceHeight+(sewer.height-crossing.surfaceHeight)*t*t*(3-2*t);
}
export function highStreetSurfaceHeight(x,z,crossing) {
  const distance=Math.hypot(x-crossing.centre[0],z-crossing.centre[1]);
  const t=Math.min(1,Math.max(0,(distance-12)/crossing.roadApproachLength));
  const side=Math.min(...crossing.roadRoute.slice(1).map((b,i)=>{
    const a=crossing.roadRoute[i],dx=b[0]-a[0],dz=b[1]-a[1];
    const u=Math.min(1,Math.max(0,((x-a[0])*dx+(z-a[1])*dz)/(dx*dx+dz*dz)));
    return Math.hypot(x-a[0]-u*dx,z-a[1]-u*dz);
  }));
  const lateral=Math.min(1,Math.max(0,(side-crossing.roadWidth/2-2)/28));
  return .185+(crossing.surfaceHeight-.185)*(1-t*t*(3-2*t))*(1-lateral*lateral*(3-2*lateral));
}
