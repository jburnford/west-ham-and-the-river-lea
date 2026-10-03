// Deterministic pseudo-random numbers for procedural detail. The same seed
// always gives the same sequence, so a review screenshot is reproducible.
// This is the linear congruential generator the scene modules each used to
// paste inline; new code should import it from here instead.
export function createRandom(seed) {
  let state = seed >>> 0;
  return () => {
    state = (state * 1664525 + 1013904223) >>> 0;
    return state / 4294967296;
  };
}
