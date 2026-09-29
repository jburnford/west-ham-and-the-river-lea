// A visual cycle in the model's local datum, not a historical tide prediction.
export function tideLevel(phase, low, high) {
  return low + (high - low) * (1 - Math.cos(phase * Math.PI * 2)) / 2;
}

export function tideControls({ config, apply, render }) {
  const slider = document.querySelector('#tide-level');
  const button = document.querySelector('#tide-play');
  const output = document.querySelector('#tide-state');
  let phase = 0, playing = false, frame = 0, last = null;
  const snapshot = () => ({ phase, playing, level: tideLevel(phase, config.low, config.high),
    low: config.low, high: config.high, cycleSeconds: config.cycleSeconds,
    retainedLevel: config.low, ditchLevel: config.low });
  function paint() {
    const state = snapshot(), fraction = (state.level - config.low) / (config.high - config.low);
    slider.value = String(Math.round(fraction * 100));
    const label = fraction < .005 ? 'Low water' : fraction > .995 ? 'High water'
      : `${playing ? (phase < .5 ? 'Rising' : 'Falling') : 'Water level'} · ${Math.round(fraction * 100)}%`;
    output.textContent = label;
    slider.setAttribute('aria-valuetext', label);
    button.textContent = playing ? 'Pause tide' : 'Play tide';
    button.setAttribute('aria-pressed', String(playing));
    apply(state);
  }
  function tick(now) {
    if (!playing) return;
    if (document.hidden) { last = null; frame = requestAnimationFrame(tick); return; }
    if (last === null) last = now;
    // Keep the expensive panorama/reflection renders to at most 12 per second.
    if (now - last >= 1000 / 12) {
      phase = (phase + (now - last) / (config.cycleSeconds * 1000)) % 1;
      last = now; paint(); render();
    }
    frame = requestAnimationFrame(tick);
  }
  function pause() {
    playing = false; cancelAnimationFrame(frame); last = null; paint();
  }
  slider.addEventListener('input', () => {
    const fraction = Number(slider.value) / 100;
    pause();
    phase = Math.acos(1 - 2 * fraction) / (2 * Math.PI);
    paint(); render();
  });
  button.addEventListener('click', () => {
    if (playing) pause();
    else { playing = true; last = null; paint(); frame = requestAnimationFrame(tick); }
    render();
  });
  document.addEventListener('visibilitychange', () => { last = null; });
  slider.disabled = button.disabled = false;
  paint();
  return { snapshot, pause };
}
