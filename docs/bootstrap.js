// Keep startup failures visible even when a module itself cannot be loaded.
const say = (text) => { const el = document.querySelector('#loading-text'); if (el) el.textContent = text; document.querySelector('#loading')?.classList.add('is-stalled'); };
const startupTimer = setTimeout(() => say('The landscape is taking longer than expected. The stories below are readable while it loads; reload if nothing appears.'), 20000);
import('./app.js').catch(error => {
  say(location.protocol === 'file:'
    ? 'The panorama needs a web server. Open the published website, or serve this folder locally, then reload.'
    : 'The panorama could not start. Try reloading, or use a browser with WebGL2 enabled. The stories below are still available.');
  console.error('Panorama startup:', error);
}).finally(() => clearTimeout(startupTimer));
