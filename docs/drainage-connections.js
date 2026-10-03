// Topology only: an enabled arc expresses a possibility, never a discharge.
import {mountCulvertSection} from './culvert-section.js';
export function analyseConnections(data,scenarioId,start,epoch='1900') {
  if(epoch!==data.geometryEpoch)throw new Error(`Drainage connections for ${epoch} need separate period evidence.`);
  const scenario=data.scenarios.find(s=>s.id===scenarioId);
  if(!scenario)throw new Error('Unknown drainage scenario');
  const ids=new Set(data.nodes.map(n=>n.id));
  if(!ids.has(start))throw new Error('Unknown starting location');
  if(!['closed','east-to-west','west-to-east','both'].includes(scenario.crossing))throw new Error('Unknown crossing operation');
  const arcs=[];
  for(const edge of data.edges) {
    if(!ids.has(edge.from)||!ids.has(edge.to))throw new Error('Dangling drainage connection');
    let forward=false,reverse=false;
    if(edge.kind==='mapped-channel')forward=reverse=true;
    else if(edge.kind==='candidate-drain')forward=reverse=scenario.westernPassage===true;
    else if(edge.kind==='possible-culvert') {
      forward=['west-to-east','both'].includes(scenario.crossing);
      reverse=['east-to-west','both'].includes(scenario.crossing);
    } else throw new Error('Unknown drainage evidence type');
    if(forward)arcs.push({edgeId:edge.id,from:edge.from,to:edge.to});
    if(reverse)arcs.push({edgeId:edge.id,from:edge.to,to:edge.from});
  }
  const reached=new Set([start]),queue=[start];
  while(queue.length) {
    const node=queue.shift();
    for(const arc of arcs)if(arc.from===node&&!reached.has(arc.to)){reached.add(arc.to);queue.push(arc.to);}
  }
  return {scenario:scenario.id,start,reachable:[...reached].sort(),arcs,hydraulicReady:false};
}

export async function mountDrainageReview() {
  const response=await fetch('./data/drainage-connections-1900.json',{cache:'no-store'});
  if(!response.ok)throw new Error('Drainage evidence could not be loaded');
  const data=await response.json(),epoch=new URLSearchParams(location.search).get('epoch')||'1900';
  const scenario=document.querySelector('#scenario'),start=document.querySelector('#start');
  for(const s of data.scenarios)scenario.add(new Option(s.name,s.id));
  for(const n of data.nodes)start.add(new Option(n.name,n.id));
  scenario.value=data.defaultScenario;start.value='manor-east';
  const svg=document.querySelector('#network');
  function element(tag,attrs={},text,parent=svg) {
    const e=document.createElementNS('http://www.w3.org/2000/svg',tag);
    for(const [key,value] of Object.entries(attrs))e.setAttribute(key,value);
    if(text)e.textContent=text;parent.append(e);return e;
  }
  function update() {
    const result=analyseConnections(data,scenario.value,start.value,epoch);
    svg.replaceChildren();
    const defs=element('defs'),marker=element('marker',{id:'arrow',viewBox:'0 0 10 10',refX:8,refY:5,markerWidth:5,markerHeight:5,orient:'auto-start-reverse'},null,defs);
    element('path',{d:'M0,0 L10,5 L0,10 Z',fill:'#246f65'},null,marker);
    element('rect',{x:315,y:565,width:205,height:35,fill:'#e2eadd'});
    element('text',{x:410,y:620,'text-anchor':'middle',class:'map-label'},'Ground model covers this reach');
    for(const r of data.railways)element('polyline',{points:r.route.map(p=>p.join(',')).join(' '),class:'railway'});
    element('polyline',{points:data.roadContext.route.map(p=>p.join(',')).join(' '),class:'road'});
    element('text',{x:300,y:470,class:'map-label'},'Manor Road');
    element('text',{x:300,y:485,class:'map-label'},data.crossingAudit.roadGeometryPresentAtCrossing?'(road profile restored)':'(map only here)');
    element('text',{x:5,y:405,class:'map-label'},'N ↑');
    element('path',{d:'M5,640 H105 M5,636 V644 M105,636 V644',stroke:'#555',fill:'none'});
    element('text',{x:55,y:659,'text-anchor':'middle',class:'map-label'},'100 metres');
    for(const edge of data.edges) {
      const forward=result.arcs.some(a=>a.edgeId===edge.id&&a.from===edge.from);
      const reverse=result.arcs.some(a=>a.edgeId===edge.id&&a.from===edge.to);
      const relevant=result.arcs.some(a=>a.edgeId===edge.id&&result.reachable.includes(a.from));
      const path=element('polyline',{points:edge.route.map(p=>p.join(',')).join(' '),
        fill:'none',stroke:relevant?'#246f65':'#999',
        'stroke-width':edge.kind==='possible-culvert'?4:3,
        'stroke-dasharray':edge.kind==='mapped-channel'?'none':'6 4',
        'marker-start':reverse&&relevant?'url(#arrow)':'none','marker-end':forward&&relevant?'url(#arrow)':'none'});
      element('title',{},`${edge.kind}; ${edge.lengthMetres.toFixed(1)} metres; invert and capacity unknown`,path);
    }
    const letters=['W','M','R','E','T','N'];
    data.nodes.forEach((n,i)=>{
      const group=element('g',{tabindex:0,role:'button','aria-label':`Start at ${n.name}`,class:'node'});
      const [x,z]=n.position;
      element('circle',{cx:x,cy:z,r:7,fill:result.reachable.includes(n.id)?'#246f65':'#faf6eb',stroke:'#263c36','stroke-width':n.id===result.start?2.5:1},null,group);
      element('text',{x,y:z-12,'text-anchor':'middle',class:'node-label'},letters[i],group);
      element('title',{},n.name,group);
      const select=()=>{start.value=n.id;update();};
      group.addEventListener('click',select);
      group.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();select();}});
    });
    document.querySelector('#description').textContent=data.scenarios.find(s=>s.id===result.scenario).description;
    const names=data.nodes.filter(n=>result.reachable.includes(n.id)).map(n=>n.name);
    document.querySelector('#result').textContent=`Possible connected locations: ${names.join('; ')}.`;
    document.querySelector('#crossing').textContent=`The candidate route is ${data.crossingAudit.lengthMetres.toFixed(1)} m long and intersects ${data.crossingAudit.railwayIntersections.length} modelled railway routes. Its alignment, invert and opening size remain unverified.`;
    document.querySelector('#road-warning').textContent=data.crossingAudit.warning;
    window.drainageConnectionReview={...result,epoch:data.geometryEpoch,renderedLengthMetres:data.renderedReach.lengthMetres};
  }
  scenario.addEventListener('change',update);start.addEventListener('change',update);update();
  mountCulvertSection(data.culvertSection,epoch);
}

if(typeof document!=='undefined')mountDrainageReview().catch(error=>{
  document.querySelector('#result').textContent=error.message;
  document.querySelectorAll('select').forEach(s=>s.disabled=true);
  console.error(error);
});
