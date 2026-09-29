# Animated tide study

Open http://localhost:4175/?view=wall-vista and expand **Tide** under the
destination menu. The slider sets low through high water; **Play tide** runs a
90-second low–high–low cycle. Manual adjustment pauses playback. The scene
starts paused, including for visitors who request reduced motion. Hidden tabs
do not advance the cycle, and animation renders are capped at 12 per second.

The regular range is 0.06–1.10 m in the model's existing local coordinates. The
author reported spillover at the initial 1.40 m setting; normal high water has
been lowered by 0.30 m to leave more clearance below the banks. Flood conditions
are outside the current control's range. Some higher mud shelves remain exposed
at normal high water. This is not a measured historical range or tide prediction. There
are no claims about clock time, spring/neap variation, phase lag between
channels, lock operation, or current speeds. All tidal channels rise together.

The moving surface covers the mapped tidal rivers and their interpreted
river-side shelves. Industrial yards, landward road approaches, lower marsh,
and isolated drains are excluded. The original low-water surface remains
underneath, preserving pools and ditches. Old Lea channel IDs 18, 22, 10018 and
10022 stay at their retained level, following the author's correction.

Separate reflection planes follow the moving river surface and the fixed
water respectively. The four Channelsea lighters rise with the surface in
separate material batches. Closed bottoms follow the curved hulls, and both
water shaders exclude the actual open-hold outlines so river water cannot
appear inside the boats. Visible floor planking distinguishes an empty hold
from the river surface. Their
freeboard, moorings and grounding remain illustrative rather than simulated.
Shadows update when those batches move. Static terrain and river walls do not
move; their intersection with the water determines the visible shoreline.

The old whole-tile low-water rectangle has been removed: fixed low water now
follows the river shelf outlines, retained channels, mapped ditches and modeled
pools. This removes an artificial straight water seam through the fields at the
original terrain boundary. The subsequent [garden pass](GARDENS.md) unifies
ground materials and replaces flat cultivation tiles with surfaces following
the terrain across that boundary.

The author has also flagged the Old Lea's connections to the back rivers and
missing lock structures. This is recorded under subsequent area reviews in
`REFINEMENT.md`; retained water levels remain provisional pending that work.

Implementation: `docs/tides.js`, `docs/app.js`, `docs/realism.js`,
`docs/photo-details.js`, and generated `river-network.json` from
`scripts/build_river_network.py`. The envelope is deliberately bounded: this
does not simulate overtopping or calculate connected flood extents.

Checks: `scripts/check_river_tides.py` verifies channel coverage and excludes
retained river, marsh and drains. `scripts/check_tide_controls.mjs` exercises a
complete cycle and scrubbing. `scripts/review_tides.py` drives actual browser
controls, checks water/barge movement and both reflection planes, captures
low/high views of Wall River, Channelsea and the marsh, and checks keyboard
and narrow-screen controls. Review images and reports are local artifacts in
`scenes/channelsea-sewer-panorama/review/`.
