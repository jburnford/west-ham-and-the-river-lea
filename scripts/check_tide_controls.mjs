import assert from 'node:assert/strict';
import { tideLevel, tideControls } from '../docs/tides.js';
const low = 0.06,
  high = 1.1;
for (const [phase, expected] of [
  [0, low],
  [0.25, 0.58],
  [0.5, high],
  [0.75, 0.58],
  [1, low],
])
  assert.ok(Math.abs(tideLevel(phase, low, high) - expected) < 1e-9);
const nodes = new Map();
for (const id of ['#tide-level', '#tide-play', '#tide-state'])
  nodes.set(id, {
    value: '0',
    listeners: {},
    addEventListener(e, f) {
      this.listeners[e] = f;
    },
    setAttribute() {},
  });
globalThis.document = { hidden: false, querySelector: (s) => nodes.get(s), addEventListener() {} };
let next;
globalThis.requestAnimationFrame = (f) => {
  next = f;
  return 1;
};
globalThis.cancelAnimationFrame = () => {
  next = null;
};
const control = tideControls({ config: { low, high, cycleSeconds: 90 }, apply() {}, render() {} });
const slider = nodes.get('#tide-level'),
  button = nodes.get('#tide-play');
assert.equal(control.snapshot().playing, false);
button.listeners.click();
next(0);
for (const [time, expected] of [
  [22500, 0.58],
  [45000, high],
  [67500, 0.58],
  [90000, low],
]) {
  next(time);
  assert.ok(Math.abs(control.snapshot().level - expected) < 1e-9);
}
slider.value = '100';
slider.listeners.input();
assert.equal(control.snapshot().level, high);
assert.equal(control.snapshot().playing, false);
button.listeners.click();
next(100000);
globalThis.document.hidden = true;
next(110000);
next(150000);
globalThis.document.hidden = false;
next(160000);
assert.equal(control.snapshot().level, high, 'Hidden interval must not advance tide');
next(182500);
assert.ok(Math.abs(control.snapshot().level - 0.58) < 1e-9);
control.pause();
assert.equal(next, null);
console.log('Tide controls passed: complete cycle, endpoints, manual pause, and no hidden-tab time jump.');
