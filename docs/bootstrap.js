// Keep startup failures visible even when a module itself cannot be loaded.
const startupTimer = setTimeout(() => {
  const loading = document.querySelector('#loading');
  if (loading) loading.textContent = 'The landscape is taking longer than expected. Try reloading this page. The story below is available while it loads.';
}, 15000);
import('./app.js').catch(error => {
  const loading = document.querySelector('#loading');
  if (loading) loading.textContent = location.protocol === 'file:'
    ? 'The panorama needs a web server. Open the published website, or serve the docs folder locally, then reload.'
    : 'The panorama could not start. Try reloading, or use a browser with WebGL2 enabled. The story below is still available.';
  console.error('Panorama startup:', error);
}).finally(() => clearTimeout(startupTimer));
