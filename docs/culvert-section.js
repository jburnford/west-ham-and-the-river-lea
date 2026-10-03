export function selectCulvertCase(data,id,epoch='1900') {
  if(epoch!==data.geometryEpoch)throw new Error('Culvert sections need separate period evidence');
  const c=data.cases.find(c=>c.id===id);
  if(!c)throw new Error('Unknown culvert section');
  return {...c,geometryEpoch:epoch,hydraulicReady:false};
}

export function mountCulvertSection(data,epoch) {
  const select=document.querySelector('#culvert-case'),svg=document.querySelector('#culvert-section');
  for(const c of data.cases)select.add(new Option(c.name,c.id));
  select.value=data.defaultCase;
  function draw() {
    const c=selectCulvertCase(data,select.value,epoch);
    svg.replaceChildren();
    const x=s=>65+s/data.lengthMetres*660,y=h=>290-(h+.1)/2.3*230;
    const add=(tag,attrs,text)=>{
      const e=document.createElementNS('http://www.w3.org/2000/svg',tag);
      for(const [k,v] of Object.entries(attrs))e.setAttribute(k,v);
      if(text)e.textContent=text;svg.append(e);return e;
    };
    for(const h of [0,.5,1,1.5,2]){
      add('line',{x1:65,x2:725,y1:y(h),y2:y(h),stroke:'#ddd'});
      add('text',{x:55,y:y(h)+4,'text-anchor':'end',class:'map-label'},h.toFixed(1));
    }
    add('text',{x:65,y:28,class:'map-label'},'Height in metres ODN — provisional datum');
    const low=[c.westInvertODN,c.eastInvertODN],high=low.map(v=>v+c.heightMetres);
    add('polygon',{points:[[0,low[0]],[data.lengthMetres,low[1]],[data.lengthMetres,high[1]],[0,high[0]]].map(([s,h])=>`${x(s)},${y(h)}`).join(' '),fill:'#e2eadd',stroke:'#246f65','stroke-dasharray':'6 3'});
    add('polygon',{points:[[0,high[0]],[data.lengthMetres,high[1]],[data.lengthMetres,high[1]+data.roofThicknessMetres],[0,high[0]+data.roofThicknessMetres]].map(([s,h])=>`${x(s)},${y(h)}`).join(' '),fill:'#bcb29f'});
    for(const r of data.railwayCrossings) {
      add('line',{x1:x(r.station),x2:x(r.station),y1:66,y2:280,stroke:'#a18459','stroke-dasharray':'3 5'});
      add('text',{x:x(r.station),y:45,'text-anchor':'middle',class:'map-label'},r.name.includes('junction')?'Junction railway':'Woolwich railway');
      add('text',{x:x(r.station),y:59,'text-anchor':'middle',class:'map-label'},`${r.formationODN.toFixed(2)} m (unverified)`);
    }
    const road=data.roadSpan;
    add('polyline',{points:road.stations.map((s,i)=>`${x(s)},${y(road.surfaceODN[i])}`).join(' '),fill:'none',stroke:'#605749','stroke-width':5});
    add('text',{x:x((road.stations[0]+road.stations.at(-1))/2),y:y(Math.max(...road.surfaceODN))-13,'text-anchor':'middle',class:'node-label'},'Manor Road');
    for(const s of [0,10,20,30,40,data.lengthMetres]){
      add('line',{x1:x(s),x2:x(s),y1:290,y2:295,stroke:'#555'});
      add('text',{x:x(s),y:310,'text-anchor':'middle',class:'map-label'},s.toFixed(s===data.lengthMetres?1:0));
    }
    add('text',{x:65,y:333,class:'map-label'},'West ← intended drainage · distance along candidate crossing (m) · East');
    const cover=Math.abs(c.minimumRoadCoverMetres)<.005?'approximately 0 m (roof reaches the road surface)':`${c.minimumRoadCoverMetres.toFixed(2)} m`;
    document.querySelector('#culvert-result').textContent=
      `${c.widthMetres.toFixed(2)} m wide × ${c.heightMetres.toFixed(2)} m high. Assumed inlet ${c.eastInvertODN.toFixed(2)} m ODN; outlet ${c.westInvertODN.toFixed(2)} m ODN. Minimum cover above the assumed roof: ${cover}. `+
      (c.fitsCoverAssumption?'Fits our provisional cover allowance.':'Does not fit our provisional cover allowance.')+
      (c.approachRegradingRequired?` Requires the approach drain to be lowered by ${c.inletLoweringMetres.toFixed(2)} m; this change has not been applied to the landscape.`:'');
    const r=data.railwayHeightReview;
    document.querySelector('#railway-height-review').textContent=`A mapped road-over-rail bridge about ${Math.round(r.distanceFromDrainCrossingMetres)} m farther south gives an estimated road deck of ${r.deckEstimateODN.toFixed(2)} m ODN. The inherited constant railway formation is ${r.inheritedFormationODN.toFixed(2)} m ODN, already ${r.formationAboveDeckMetres.toFixed(2)} m above that deck estimate. The railway profile needs correction before it can serve as a flood barrier; this bridge does not give a measured track height at the drain crossing.`;
    window.culvertSectionReview=c;
  }
  select.addEventListener('change',draw);draw();
}
