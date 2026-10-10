// Keep the explore panel clear of what sits below it. On short or narrow windows the panel shares a column with the
// walking and flying controls, the zoom buttons and the location map (and, before the reader scrolls, the title), so
// with the tide section open it ran over them. Its height is capped at the free space above the first of these it
// would meet, and it scrolls inside that.
const OBSTACLES = ['#bridge-controls', '#flight-controls', '.tools', '#minimap', '#hero'];
const GAP = 12,
  MIN_HEIGHT = 120;

function shown(element) {
  if (!element || !element.getClientRects().length) return false;
  for (let e = element; e && e !== document.body; e = e.parentElement) {
    const style = getComputedStyle(e);
    if (style.display === 'none' || style.visibility === 'hidden') return false;
  }
  return true;
}

function fit(panel) {
  panel.style.maxHeight = '';
  if (!shown(panel)) return;
  const box = panel.getBoundingClientRect();
  let limit = window.innerHeight - GAP;
  for (const selector of OBSTACLES) {
    const element = document.querySelector(selector);
    if (!shown(element)) continue;
    const r = element.getBoundingClientRect();
    // Only what lies below the panel's top edge and shares its column.
    if (r.top > box.top + 40 && r.left < box.right && r.right > box.left) limit = Math.min(limit, r.top - GAP);
  }
  if (box.bottom > limit) panel.style.maxHeight = `${Math.max(MIN_HEIGHT, limit - box.top)}px`;
}

export function keepTravelPanelClear() {
  const panel = document.querySelector('#travel-panel');
  if (!panel) return;
  let pending = 0;
  const schedule = () => {
    if (!pending) pending = requestAnimationFrame(() => ((pending = 0), fit(panel)));
  };
  addEventListener('resize', schedule);
  addEventListener('scroll', schedule, { passive: true });
  // Opening the panel or its tide section, and switching between walking and flying, change what needs room.
  document.addEventListener('toggle', schedule, true);
  new MutationObserver(schedule).observe(document.body, { attributes: true, attributeFilter: ['class'] });
  const sizes = new ResizeObserver(schedule);
  for (const selector of OBSTACLES) document.querySelectorAll(selector).forEach((e) => sizes.observe(e));
  schedule();
}
