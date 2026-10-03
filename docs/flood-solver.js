// Conservative local-inertial surface routing; controlled research demo, not event calibration.
const G=9.81;
export function hydrograph(time,p,side) {
  const base=side==='west'?.65:.82;
  if(p.preset==='rain')return base;
  if((p.preset==='surge'?'west':'east')!==side)return base;
  // Synthetic 1h pulse: 5min initial, 15min rise, 15min hold, 20min fall, 5min recovery.
  const t=time/60;
  const f=t<5?0:t<20?(t-5)/15:t<35?1:t<55?(55-t)/20:0;
  return base+(p.peak-base)*f;
}
export function parameters(data,input={}) {
  if(data.epoch!=='1900')throw new Error('Demo requires reviewed 1900 geometry');
  const p={preset:'inflow',peak:1.65,gate:'east-to-west',rain:0,pump:false,railFormation:data.railFormationODN??1.6,verticalShift:0,...input};
  if(!['inflow','surge','rain'].includes(p.preset)||!['east-to-west','both','blocked'].includes(p.gate))throw new Error('Unknown flood scenario');
  for(const [key,min,max] of [['peak',.5,3],['rain',0,100],['railFormation',.5,2],['verticalShift',-.5,.5]])
    if(!Number.isFinite(p[key])||p[key]<min||p[key]>max)throw new Error(`Invalid ${key}`);
  return p;
}
export function makeBed(data,p) {
  const n=data.width*data.height,b=new Float64Array(n);
  for(let i=0;i<n;i++) {
    let h=data.bed[i];
    if(data.ground) {
      h=data.ground[i]*(1-data.railInfluence[i])+p.railFormation*data.railInfluence[i];
      h=h*(1-data.roadInfluence[i])+data.roadHeight[i]*data.roadInfluence[i];
      h+=(Math.min(h,data.channelBed[i])-h)*data.channelInfluence[i];
    }
    b[i]=h+p.verticalShift;
    if(!Number.isFinite(b[i]))throw new Error('Non-finite ground');
  }
  return b;
}
export function culvertDischarge(c,eastLevel,westLevel,p,data) {
  if(!c||p.gate==='blocked')return 0;
  const diff=eastLevel-westLevel;
  if(Math.abs(diff)<1e-10 || (diff<0&&p.gate==='east-to-west'))return 0;
  const forward=diff>0,up=forward?eastLevel:westLevel,down=forward?westLevel:eastLevel;
  const invUp=(forward?c.eastInvertODN:c.westInvertODN)+p.verticalShift;
  const invDown=(forward?c.westInvertODN:c.eastInvertODN)+p.verticalShift;
  const depth=Math.min(c.heightMetres,Math.max(0,up-invUp));
  const head=Math.max(0,up-Math.max(down,invDown,invUp));
  if(depth<1e-6||head<=0)return 0;
  const area=c.widthMetres*depth;
  const perimeter=c.widthMetres+2*depth+(depth>=c.heightMetres?c.widthMetres:0);
  const radius=area/perimeter;
  const resistance=(data.culvertEntranceExitLoss??1.5)+2*G*(data.culvertManning??.025)**2*c.lengthMetres/radius**(4/3);
  return (forward?1:-1)*area*Math.sqrt(2*G*head/resistance);
}
export class FloodModel {
  constructor(data,input={},initialDepth=null) {
    this.data=data;this.p=parameters(data,input);this.nx=data.width;this.nz=data.height;this.n=this.nx*this.nz;
    this.dx=data.cellSizeMetres;this.area=this.dx**2;this.bed=makeBed(data,this.p);
    this.h=new Float64Array(this.n);this.maxDepth=new Float32Array(this.n);this.time=0;
    if(initialDepth) {if(initialDepth.length!==this.n)throw new Error('Initial grid length mismatch');this.h.set(initialDepth);}
    else for(let i=0;i<this.n;i++)if(data.kind?.[i]===4) {
      const x=(i%this.nx+.5)/this.nx;
      this.h[i]=Math.max(0,.65+(.82-.65)*x-this.bed[i]);
    }
    if(!this.h.every(v=>Number.isFinite(v)&&v>=0))throw new Error('Invalid initial water depth');
    const a=[],b=[],side=[],width=[];
    const edge=(i,j,s=0,w=this.dx)=>{a.push(i);b.push(j);side.push(s);width.push(w);};
    for(let z=0;z<this.nz;z++)for(let x=0;x<this.nx;x++) {
      const i=z*this.nx+x;
      if(x+1<this.nx)edge(i,i+1);
      if(z+1<this.nz)edge(i,i+this.nx);
    }
    for(const q of data.boundaries||[])edge(q.cell,-1,q.side==='west'?1:2,q.width);
    this.a=Int32Array.from(a);this.b=Int32Array.from(b);this.side=Uint8Array.from(side);this.width=Float64Array.from(width);
    this.q=new Float64Array(a.length);this.flux=new Float64Array(a.length);this.out=new Float64Array(this.n);this.scale=new Float64Array(this.n);
    this.initialVolume=this.volume();this.boundaryIn=0;this.boundaryOut=0;this.rainVolume=0;this.pumpVolume=0;this.culvertNetVolume=0;this.steps=0;this.lastCulvertFlow=0;
    this.maxDepth.set(this.h);
  }
  volume(){let v=0;for(const h of this.h)v+=h*this.area;return v;}
  step(maxDt=1) {
    let maxH=.001;for(const h of this.h)maxH=Math.max(maxH,h);
    const dt=Math.min(maxDt,1,.6*this.dx/Math.sqrt(G*maxH));
    const rain=this.p.rain/1000/3600*dt;
    if(rain){for(let i=0;i<this.n;i++)this.h[i]+=rain;this.rainVolume+=rain*this.area*this.n;}
    this.out.fill(0);
    for(let k=0;k<this.a.length;k++) {
      const i=this.a[k],j=this.b[k],hi=this.bed[i]+this.h[i];
      const hj=j<0?hydrograph(this.time+dt/2,this.p,this.side[k]===1?'west':'east'):this.bed[j]+this.h[j];
      const sill=j<0?this.bed[i]:Math.max(this.bed[i],this.bed[j]);
      const flowDepth=Math.max(0,Math.max(hi,hj)-sill);
      const rough=j>=0&&this.data.kind?.[i]===4&&this.data.kind?.[j]===4?(this.data.manningChannel??.035):(this.data.manningField??.055);
      const length=j<0?this.dx/2:this.dx;
      this.q[k]=flowDepth<1e-6?0:(this.q[k]-G*flowDepth*dt*(hj-hi)/length)/(1+G*dt*rough**2*Math.abs(this.q[k])/flowDepth**(7/3));
      const f=this.q[k]*this.width[k];this.flux[k]=f;
      if(f>0)this.out[i]+=f;else if(j>=0)this.out[j]-=f;
    }
    const c=this.data.culvert;
    let cq=c?culvertDischarge(c,this.bed[c.eastCell]+this.h[c.eastCell],this.bed[c.westCell]+this.h[c.westCell],this.p,this.data):0;
    if(cq>0)this.out[c.eastCell]+=cq;else if(cq<0)this.out[c.westCell]-=cq;
    for(let i=0;i<this.n;i++)this.scale[i]=this.out[i]>0?Math.min(1,this.h[i]*this.area/(dt*this.out[i])):1;
    for(let k=0;k<this.a.length;k++) {
      const i=this.a[k],j=this.b[k],f=this.flux[k];
      const scale=f>0?this.scale[i]:j>=0?this.scale[j]:1;
      const vol=f*scale*dt;this.q[k]*=scale;
      this.h[i]-=vol/this.area;
      if(j>=0)this.h[j]+=vol/this.area;
      else if(vol>0)this.boundaryOut+=vol;else this.boundaryIn-=vol;
    }
    if(c&&cq) {
      cq*=this.scale[cq>0?c.eastCell:c.westCell];
      this.h[c.eastCell]-=cq*dt/this.area;this.h[c.westCell]+=cq*dt/this.area;
      this.culvertNetVolume+=cq*dt;
    }
    this.lastCulvertFlow=cq;
    if(c&&this.p.pump) {
      const vol=Math.min(this.h[c.eastCell]*this.area,(this.data.testPumpCapacityM3s??.08)*dt);
      this.h[c.eastCell]-=vol/this.area;this.pumpVolume+=vol;
    }
    for(let i=0;i<this.n;i++) {
      if(!Number.isFinite(this.h[i])||this.h[i]<-1e-9)throw new Error('Unstable water depth');
      if(this.h[i]<0)this.h[i]=0; // floating-point roundoff only; checked against ledger
      this.maxDepth[i]=Math.max(this.maxDepth[i],this.h[i]);
    }
    this.time+=dt;this.steps++;
    return dt;
  }
  advance(target){while(this.time<target-1e-8)this.step(target-this.time);return this.stats();}
  stats() {
    let wet=0,max=0,eastVolume=0,westVolume=0;
    for(let i=0;i<this.n;i++) {
      if(this.h[i]>.05&&this.data.kind?.[i]!==4)wet+=this.area;
      max=Math.max(max,this.h[i]);
      const x=this.data.bounds?this.data.bounds[0]+(i%this.nx+.5)*this.dx:(i%this.nx+.5)*this.dx;
      if(x>=280)eastVolume+=this.h[i]*this.area;else westVolume+=this.h[i]*this.area;
    }
    const volume=this.volume(),expected=this.initialVolume+this.boundaryIn+this.rainVolume-this.boundaryOut-this.pumpVolume;
    return {time:this.time,volume,wetAreaM2:wet,maxDepth:max,eastVolume,westVolume,initialVolume:this.initialVolume,boundaryIn:this.boundaryIn,boundaryOut:this.boundaryOut,rainVolume:this.rainVolume,pumpVolume:this.pumpVolume,culvertNetVolume:this.culvertNetVolume,culvertFlow:this.lastCulvertFlow,massError:volume-expected,steps:this.steps};
  }
}
