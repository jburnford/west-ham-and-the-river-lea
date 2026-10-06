# Task E report (interim): flood model phases 0-1 and the river banks (5 October 2026)

This work was done directly in the parent session. Branch `task-e-flood-model` (worktree `../book_website-taske`, server on 4211), from main `e59ad25`. Main was fast-forwarded to task D locally, as the plan's setup asks; it is not pushed. The plan is `FLOOD_MODEL_PLAN.md`; the Phase 0 evidence and the author's answers are in `FLOOD_PHASE0_NOTE.md`.

## Summary

- **Phase 0 (evidence and register).** `data/maps/lea-control-structures.json` has 25 records, revised after the author's review.
  - The c.1890s working mills are Three Mills, Abbey Mill, Pudding Mill (holding water) and City Mills (in part).
  - There was no mill on the Waterworks River; its flood gate stands on the old mill site.
  - The Navigation is walled off from the Three Mills pond. The 1860s plan letters an "Overfall" between them at the head of the island above Three Mills.
- **Phase 1 (whole-model flood grid).** The `?flood` page's square 1.2 km² box is replaced.
  - The grid now covers 15 km² of modelled ground, from Lea Bridge to the Thames.
  - The drawn ground is sampled every metre and kept in 2 m cells.
  - The page draws a 2 m grid over the back rivers and the core and a 10 m grid elsewhere, with smoothed edges and no box.
  - The Abbey Mill gates are shut against the tide.
  - The Thames frontage, which the regional ground draws with no wall, is the closed edge of the model.
- **The river banks (author: "fix the rivers").** Three OS flood banks the model drew 1-3 m low are now drawn at the OS levels on their crests. They are in a new register, `data/maps/os-flood-banks.json`:
  - the Long Wall (Mill Meads);
  - the Channelsea east bank and river wall at the West Ham Chemical Works;
  - the Short Wall (east bank of the Three Mills Wall River).
- **Result.** The marsh east of the Channelsea (680 ha including Canning Town and Plaistow) no longer floods at high water.
  - Before the bank fix it filled at 2.56 m ODN, below ordinary high water (3.41 m), through a 0.72 m notch in the Channelsea bank.
  - It now holds to 4.09 m ODN.
- **Checks.**
  - `npm test`: 21 of 21.
  - Python checks: the same set passes and fails as on main. The exception is `check_gltf`, which needs the git-ignored `.glb` exports this worktree lacks.

## Phase 1: the whole-model grid

**Builder** (`scripts/build_landscape_flood.py`, rewritten):

- **The modelled ground** is the main landscape's weight field, plus every mapped water polygon and the core tile. Cells outside it never carry water.
- **Sampling.** The ground is sampled every metre (`sample_drawn_ground.mjs`, 40.6 M samples in about 20 s). Railway and sewer embankments, retaining walls and the shut Abbey Mill gate are composed on top, and 1 m samples are reduced to 2 m cells keeping the highest.
- **Connection levels** are computed by greyscale reconstruction by erosion (four-neighbour). `check_landscape_flood.py` compares it with the old heap method on random grids.
- **Outputs:**
  - a fine grid, x -1300..600, z -981..1199, 950 × 1090;
  - a coarse grid, 10 m, 580 × 700, each cell the lowest level of its 2 m cells;
  - levels stored as uint16 centimetres;
  - a stage table of land connected from 1.5 to 6.0 m ODN, for the whole model, the fine box, the rest and the old box.
- **Land figures** exclude every mapped water polygon. The old figures counted the Navigation and other non-tidal water as land.

**Page** (`docs/landscape-flood.js`): both grids are drawn as half-float textures with linear filtering, so the shoreline is a contour, not cell outlines. The fine box is cut out of the coarse plane, and the dashed box outline is gone. The browser review (`review_landscape_flood.py`) passes; its low-stage check now allows the 1 ha of channel-edge cells.

**Connected land, ha:**

| ODN | Old box, main | Whole model, Phase 1 | Whole model, after the banks | Old box, after the banks |
|---|---|---|---|---|
| 1.9 | 0 | 0.96 | 0.96 | 0.00 |
| 2.5 | 0.03 | 43.67 | 42.87 | 24.94 |
| 3.5 | 51.09 | 989.02 | 306.77 | 30.49 |
| 4.5 | 105.63 | 1310.47 | 1309.93 | 95.91 |
| 5.5 | 114.47 | 1375.98 | 1375.98 | 104.21 |

The old-box column differs from main for three reasons: the land figures now exclude water; the grid is finer; and water now arrives from outside the old box. The 2.5 m figure is Mill Meads (see below).

## The river banks

**What was wrong.** The core box has 61 OS bank-top and wall-top readings. 20 were drawn more than 0.5 m below their OS level. Some of these are road ramps; the flood banks among them were:

- **The Long Wall.** The model drew no bank on its line. Its only bank was a 2 m strip at the tidal outline 20-30 m east, and the hatched embankment itself was low marsh (-0.3 m under the 17.4 and 17.8 ft readings).
- **The Channelsea east bank.**
  - The river wall at the works was drawn at 2.0-2.5 m against 3.04-3.22 m.
  - The curved hatched bank north of it, from the outfall sewer round to the works, 20-30 m east of the water, was not drawn at all.
  - A 0.72 m notch at z 153 let the whole south-east marsh fill.
- **The Short Wall** was drawn at 1.65-2.78 m against 2.86-3.22 m.

**Method** (`data/maps/os-flood-banks.json`; `scripts/build_main_landscape.py`, `raise_to_flood_banks`):

- Each bank is traced along the middle of its hatched band, or the wall line, on the five-foot plan.
- Its crest runs through the OS readings on it, by chainage, and is held beyond the end readings.
- Land within 1.5 m of the line is raised to the crest, then falls at 1.5 : 1 to the ground. Ground is raised only.
- Nothing inside the drawn river or tidal water is raised. Marsh ditches are built over, since they passed the banks by sluices, shut at high water.
- Where the drawn water is wider than the OS bank (the works wall, the Short Wall by the Mill Meads drain), the water's land edge along that stretch carries the crest.
- The raise comes after the core's preserved tidal mud, so a wall can stand on mud that lies outside the drawn outline.

**After.** Drawn crest (the highest 2 m cell within 6 m of the line) against the OS readings:

| Bank | OS readings | Minimum along the line | Median |
|---|---|---|---|
| Long Wall | 2.98-3.29 | 2.98 | 3.11 |
| Channelsea east bank | 2.98-3.22 | 2.99 | 3.07 |
| Short Wall | 2.86-3.22 | 2.51 | 3.04 |

- At each of the 16 readings the drawn crest is within 0.05 m of the OS level.
- 46 core vertices of preserved tidal mud were raised. They lie under the works river wall, where the core's mud runs outside the drawn tidal outline. `check_main_landscape.mjs` now requires every changed mud vertex to be a rise, and their number to equal the count the landscape records (`osFloodBanks.raisedTidalMudVertices`); all other mud keeps its channel section exactly.
- Vertices raised: Long Wall 30,690; Channelsea east bank 19,927; Short Wall 4,042.
- No seat or plinth changed.

**Renders.** `reference/photo-review-2026-10-03/views-taske/sheet-*.png` (main checkout) shows main and task E at high water. The Long Wall stands across Mill Meads in plan; the Short Wall is a continuous bank with its path. At the West Ham works the river wall is an earth bank face in front of the buildings, not yet a masonry face (see below).

## Not done, and why

- **Mill Meads still fills at 2.23 m ODN, from the north.** The water enters at a low Waterworks River bank north of the High Street (-546, -379). Outside the core box the regional ground has no High Street causeway, so the water passes round the core's north edge.
  - Outside the core the regional "early-marsh" ground lies below the OS readings. Median by area: Stratford Marsh -1.08 m, Temple Mills -0.79 m, east -0.48 m, south -0.58 m.
  - That is outside the agreed core box, and it is the author's decision.
- **The marsh on the Poplar side of Bow Creek, south of the core** (about 97 ha) floods at about 3.39 m ODN, just under ordinary high water. That is regional ground and banks outside the core box (map: `reference/flood-model-phase0/whole-model-stages.jpg` in the main checkout).
- **The tide can enter the upper Channelsea from its head at Temple Mills** through the regional channel network (Waterworks River to the Channelsea), bypassing the Abbey Mill gate.
- **The works wall face.** The OS draws a masonry river wall at the West Ham works. The model now has an earth bank face there; a retaining-wall face like the Four and Sun Mills walls (`os-river-walls.json`) would be truer.
- **Smaller banks not traced:** the bank west of Mill Meads along x -405 (no reading), the Wall River west bank by the Asphalte Works, the Abbey Creek Wharf bank (16.9 ft), and the Harrow Bridge Wharf bank (0.27 m low).
- **The West Ham Chemical Works yard** is drawn about 2 m under its OS yard readings (13.5 ft): the "building" readings there have use none.
- **The region index** (`docs/data/lower-lea-region/index.json`) is left as on main: the river system stores its hash, and rebuilding it after the flood grid would break that. `check_lower_lea_region` fails here, as on main.

## Decisions for the author

1. Fit the regional ground north of the core (Stratford Marsh, the High Street, the Waterworks River banks) to the OS readings before Phase 2? The rain-up-river flood plays out there.
2. Raise the back-river beds (Phase 0 decision 4)?
3. A masonry face for the works river wall?

Then Phase 2: pounds and ponds, with the tide-mill rule, the Navigation's overfalls and the working mills agreed in Phase 0.
