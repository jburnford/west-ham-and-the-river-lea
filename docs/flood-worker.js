import { FloodModel } from './flood-solver.js';
self.onmessage = async ({ data: { terrain, params, duration = 3600, interval = 60 } }) => {
  try {
    const model = new FloodModel(terrain, params);
    const bed = Float32Array.from(model.bed);
    self.postMessage({ type: 'ready', bed }, [bed.buffer]);
    for (let time = 0; time <= duration; time += interval) {
      model.advance(time);
      const depth = Float32Array.from(model.h),
        stats = model.stats();
      self.postMessage({ type: 'frame', depth, stats }, [depth.buffer]);
      await new Promise((resolve) => setTimeout(resolve, 0));
    }
    self.postMessage({ type: 'done', stats: model.stats() });
  } catch (error) {
    self.postMessage({ type: 'error', message: error.message });
  }
};
