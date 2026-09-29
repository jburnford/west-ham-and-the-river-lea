// Keep startup failures visible even when a module itself cannot be loaded.
const say = (text) => { const el = document.querySelector('#loading-text'); if (el) el.textContent = text; document.querySelector('#loading')?.classList.add('is-stalled'); };
const startupTimer = setTimeout(() => say('The landscape is taking longer than expected. The stories below are readable while it loads; reload if nothing appears.'), 20000);
async function startScene() {
  const response=await fetch('./scene-manifest.json',{cache:'no-store'});
  if(!response.ok)throw new Error('Scene manifest unavailable');
  const manifest=await response.json();
  const base=new URL('./',location.href);
  const local=['localhost','127.0.0.1','[::1]'].includes(location.hostname);
  // Local review must also see edits made since the last manifest generation.
  const nonce=local?`&preview=${Date.now().toString(36)}`:'';
  const imports=Object.fromEntries(Object.entries(manifest.modules).map(([source,target])=>
    [new URL(source,base).href,new URL(target+nonce,base).href]));
  const map=document.createElement('script');map.type='importmap';map.textContent=JSON.stringify({imports});
  document.head.append(map);
  window.sceneRevision=manifest.revision;
  window.sceneAssetUrl=url=>new URL(manifest.assets[url]||url,base).href;
  await import('./app.js');
}
startScene().catch(error => {
  say(location.protocol === 'file:'
    ? 'The panorama needs a web server. Open the published website, or serve this folder locally, then reload.'
    : 'The panorama could not start. Try reloading, or use a browser with WebGL2 enabled. The stories below are still available.');
  console.error('Panorama startup:', error);
}).finally(() => clearTimeout(startupTimer));
