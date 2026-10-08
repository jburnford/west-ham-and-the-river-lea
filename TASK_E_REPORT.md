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

# F1: the ground north of the core, to the OS (6 October 2026)

Done directly in the parent session, on `task-e-flood-model` after `2621cb2` (work in progress, committed when the author had to leave). The author agreed F1-F3 on 6 October and decision 1 above is answered by it. Scratch work (measuring scripts, flood dumps, the pre-F1 data) is in the session scratchpad `…/9d88d6ca-…/scratchpad/f1/`.

## Summary

- **The Stratford zone** (scene x -1800..-150, z -2450..-240: the High Street to Temple Mills, north of the core box) is drawn at its OS levels.
  - **Readings.** The 132 applied OS ground readings there: median drawn − OS **-1.08 → -0.009 m**; median |drawn − OS| 0.031 m; 113 within ±0.6 m (33 before). The other 19 are listed exceptions, each with its reason.
  - **The core box is unchanged** in its results. The terrace check figures are identical (116 readings, median 0.006, p90 0.246 m). Inside the box, ground moved only along its north edge, where street corridors and pads straddle it: core tile ≤ 0.014 m, network ≤ 0.07 m, extension ≤ 0.5 m.
- **The flood at high water (3.414 m ODN):**

| | Before F1 | After F1 |
|---|---|---|
| Mill Meads fills at | 2.23 m ODN (from the north, at (-546, -379)) | 3.78 m ODN (over the Abbey Mills ground at (-36, 11)) |
| Stratford Marsh basins fill at | 2.31-3.41 m ODN | 3.72-4.07 m ODN |
| The Carpenters Road works fill at | 2.95 m ODN | 4.02 m ODN |
| The upper Channelsea takes the tide at | 1.84 m ODN (through Temple Mills) | 3.64 m ODN (over the Abbey Mill gate only) |
| Land wet at high water, Stratford zone | 73.7 ha | 11.9 ha |
| Land wet at high water, core box | 31.2 ha | 1.3 ha |
| Land wet at high water, whole model | 205.3 ha | 108.7 ha |

  The connected-land stage table: 2.5 m ODN 42.87 → 1.32 ha; 3.5 m ODN 306.77 → 157.00 ha.
- **Checks.**
  - `npm test` 21/21. `check_os_ground_levels.mjs` now covers the zone. Two other checks needed work: `check_road_bridges.mjs` sample refreshed (St Michael's Bridge approaches only), and `check_railway_embankments.mjs` passes after a builder fix (below).
  - Python checks: the same 41 pass and 34 fail as before F1.
  - The builders are deterministic (reruns byte-identical).

## What changed

**The register** (`data/maps/os-ground-levels.json`, `scripts/prepare_os_ground_levels.py`).
- A `stratfordZone` and a new use, `stratford`: every ground reading on the drawn marsh in the zone that is not a street or premises reading.
- Readings where the regional early-marsh support is 0, or beyond the regional marsh outline, are not applied, each with its reason. That is Stratford town and Hackney Wick on the terrace, which the model does not draw.
- Street readings on drawn streets set their corridors. The High Street causeway now carries its OS levels north of the core.
- Core entries are unchanged.
- Three decisions (a reading inside the drawn City Mill River; a low-confidence West Ham Gas Works figure; a Hertford Union towing path off the drawn marsh) and 19 exceptions (bank faces, tidal-outline shelves, the marsh edge beside water, pad batters).

**The ground** (`scripts/build_main_landscape.py`, `scripts/os_ground_levels.py`).
- **A Stratford correction grid.** It interpolates the zone's residuals against the core-corrected ground, as T21/T22 did:
  - every applied reading is a control, streets at the ground under the road;
  - the kernel is 60 m, because the readings are sparser (median spacing 68 m against 51 m in the core);
  - it is 0 on the core's north edge and full 20 m north of it, and fades out over 60 m beyond the zone.
  - Residuals before it: median +0.70 m, range -1.61..+3.93 m. This is the 1890s made ground of the Carpenters Road district, the High Street and the railway lands standing on the 1848 marsh.
- **Support.** It is extended round the applied readings as in the core, but not within 15 m of mapped water nor beyond the regional marsh outline. Raising it there put a 1.7 m sill across the Channelsea where no mesh draws its bed, and lifted Stratford town's level field above a street.
- **The bank blend.** It uses a weight in which water cells take their neighbours' weight. The 10 m weight field is 0 in water, so the banks got 0.3-0.9 of the regional bank crest, although that crest already runs through the OS bank-top readings. The exported weight is unchanged.
- **The river-network join.**
  - The river-system mesh stops 4-8 m short of the network's rectangle, and the 20 m background mesh bridged the gap. On the Waterworks River bank at the network's north edge, a 20 m triangle fell from the 2.4 m crest to its water-edge vertex, and the tide entered the Carpenters Road works through the notch at 0.5 m.
  - A 6 m ring either side of the network edge is now meshed at 2 m and joined to the 20 m mesh as the terrace mesh is. Vertices the road pass sets are left alone at the join.
  - Background mesh: 574,494 → 727,893 vertices; `background.f32` 6.9 → 8.7 MB.
- **Railway abutments.** A cut embankment end within 1.5 m of water is measured against the water edge, not the base ground behind the bank face. The North London branch at the Hackney Cut gains 7 abutment faces (5.3 m), because its toes rose with the OS ground to 2.3 m beside the bank face. One more 0.7 m face appears at the LT&SR Bow Creek approach.

**The Channelsea head** (`data/maps/lea-control-structures.json`).
- Three new closures where the river-system Channelsea meets the Waterworks River: the head at Temple Mills, Potter's Ditch, and the head of the embanked channel above the Manure Works.
  - Each is a `tideBarrier` at the OS bank level beside it (2.92, 3.19 and 3.19 m scene; estimates, with their bounding readings).
  - The closure line runs 2 m outside the Waterworks River edge across the Channelsea mouth. The three together cut every Channelsea reach off from it.
- **Evidence.** The plan draws no open passage at any of them: the hatched Waterworks River bank runs unbroken across the heads. The OS also letters Abbey Mill "Highest Point to which the O.T. flow" on the Channelsea, while ordinary tides reached Temple Mills weir on the Waterworks River. No sluice is lettered at these heads; the OS "Sluice" labels near Temple Mills are on marsh drains.

**Tools.** `scripts/flood_diagnostics.py spills` takes a box.

## Renders

`reference/photo-review-2026-10-03/views-taske-f1/` (main checkout) has before-F1 (`0aec8c0`) and after pairs (`cameras.json`) and the high-water maps (`hw0-*`, `hw5-*`).
- **The High Street by the Waterworks River.** The terraces' yard walls no longer stand on wedges above ground falling away from the houses: the yards lie near street level.
- **The Hackney Cut.** The North London bridge has its abutment face.
- **Stratford Marsh in plan, the Channelsea by the High Street and Temple Mills.** No jumps.

## Not done, and why

- **Old Ford and Hackney Wick, west of the Navigation, and the Bow strip at (-1350, -250)** are wet just under high water. In the Phase 1 grid the Navigation is joined to the tide through the channel network; Phase 2 holds it at its pound level. The Hackney Cut towing paths are drawn up to 4 m under the OS where they lie beyond the drawn marsh.
- **Embankments north of the core in the flood grid.**
  - The Northern Outfall Sewer bank is composed there at 7.40 m against its OS 7.7-8.0 m crest readings: it holds.
  - The G.E.R. High Meads loop embankment is not drawn: 1.29 m against the OS 2.62 m. It is not a flood barrier that matters at high water, but it wants drawing.
- **The North London branch formation** (an interpreted 3.0 m, "lower formation at the OS-confirmed underpass") now stands barely above the OS ground at the Hackney Cut (2.8-4.4 m). Its level wants the railway level register treatment.
- **The West Ham Gas Works pad** (site 873) is a 0.15 m marsh estimate with no reliable yard reading.
- **The join ring** runs round the whole network rectangle. The gaps were found on its north edge; trimming the ring to where the meshes actually part would save most of the 1.8 MB.
- **The 4 m strip with no bed mesh** where the Waterworks River and the Channelsea cross the network edge remains. The flood grid reads 0.0 m there (a sill below the channel beds, as before F1).
- **The Poplar side of Bow Creek** (about 97 ha, wet at 3.39 m ODN) is unchanged; it was lower priority in the plan.

## Decisions for the author

1. The Channelsea head closures are inferred from the OS lettering and the unbroken bank, not from a lettered sluice. Is that right, or did the head pass water at some states of the tide?
2. Trim the 2 m join ring to the network's north edge (smaller download), or keep it whole?
3. Next: F2 (back-river beds), then F3 (the works wall face), then Phase 2.

## F1 follow-up: holes in the flood grid, and the bank band (6 October 2026)

The author saw, in the `?flood` view at about 4.2 m ODN: a line of 10 m squares in the Mill Meads allotments that never flooded; marsh north of the railway left dry in patches; and seams in the water.

- **Cause: holes in the modelled ground.**
  - `build_landscape_flood.py` read the main-landscape weight by nearest 10 m cell. Every cell centred in water (weight 0) cut a strip up to 10 m wide out of the bank beside it, and isolated zero cells cut 10 m squares out of the marsh.
  - The grid treats cells outside the modelled ground as never wet, so these 18.1 ha of holes stood as walls along nearly every river and drain, and as the dry squares at Mill Meads.
  - The builder now reads the weight as `docs/main-landscape.js` `weight()` does (bilinear between cell centres). Holes are down to 7.3 ha, all at the Thames end beyond the core. The Mill Meads squares are gone.
- **What the walls hid.** The Waterworks River west bank above Carpenters Road is drawn as an embankment on the OS, with a regional crest of 3.07 m. It was drawn at 1.45 m, because the regional support is 0 on the bank land there as well as in the water. With the walls gone, Stratford Marsh behind it took the tide at 3.10 m ODN.
  - In the Stratford zone, every cell within 25 m of mapped water now takes the highest weight within 20 m for the bank blend (blend only; the exported weight is unchanged). The field now fills at 3.74 m ODN.
- **Land wet at high water:** Stratford zone 11.9 → 11.6 ha; core box 1.3 → 1.4 ha; whole model 108.7 → 160.1 ha.
  - The whole-model rise is land the walls had hidden: Old Ford and Hackney Wick west of the Navigation, and the Lea above Temple Mills.
  - In the Phase 1 grid the Navigation is joined to the tide; Phase 2 holds it at its pound level.
  - A patch by Bow Goods Station is the Lea channel itself, drawn by the river network but outside the mapped water polygons, so the grid counts it as land.
- **What still stays dry at 4.2 m ODN, and why.**
  - The marsh between the Old River Lea and the Waterworks River north of the High Street takes the tide only at 4.7-4.9 m ODN. That is over its embanked banks, which the OS bank-top readings put at 4.0-5.0 m ODN.
  - In the tide-only, volume-free grid, a basin is all dry below its rim and all wet above it (the author's "switch"). These marshes flooded from rain and from river flow standing above the tide, which Phases 2-3 add.
- **Round dry islands about 60 m across.** These are humps the correction raises round single high readings, for example two "open ground south of the Victoria Park Branch" readings at 5.2 and 5.9 m ODN (probably railway made ground). They follow the OS, but the shape is the kernel's, not the ground's.
- **Seams.** Some straight edges in the water are railway embankments (the High Meads loop, the Victoria Park branch). I have not traced every one.
- **Checks.** `npm test` 21/21; `check_landscape_flood.py` passes; the downstream rebuild was rerun.

# Phase V: volume, not a switch (6 October 2026)

The author: the landscape was a bowl. Mill Meads probably flooded all the time, while the Abbey Mills pumping station ground flooded only when things got really bad. The connected-level grid could not show that: a basin went from dry to full as soon as a source passed its rim. Rain, the tide and the river now arrive as volumes and fill the lowest ground first.

## Summary

- **The ground as hollows.** `scripts/flood_basins.py` splits the same 2 m ground into 119 hollows. Where two meet at a saddle they form a parent basin (49); a basin that reaches water is attached to it (69). Each basin has a stage–volume table at 5 cm steps.
- **Routing in the browser** (`docs/lib/flood-volume.js`, pure functions, about 1 ms a scenario):
  - Rain: a storm total on each hollow's whole catchment. A full hollow spills into the hollow across its saddle, or out to the water.
  - Tide, surge and river: weir flow over each crest while the source stands above it, integrated over the tide curve or the held duration. Water stands above the crest up to the source level; the rest goes back.
  - Marsh sluices: they drain at an estimated rate while the water outside is below their sill, in every tide of the duration.
- **The page** (`?flood`) opens on the volume view, with five presets and controls for rain, duration (one tide, one day, three days), surge and the held river level. The Phase 1 view stays as "Connected extent". The water is drawn at each basin's level, with the shoreline cut where the interpolated depth reaches zero.
- **The author's cases:**
  - Mill Meads holds 456,000 m³ to its tidal crest at 3.78 m ODN (as F1). 20 mm of rain in one tide puts 23 cm in its lowest hollow (1.76 m ODN), more than 2 m below the rim.
  - A surge 5 cm over the crest for one tide leaves a 4 cm sheet in the bottom of the bowl (1.57 m ODN).
  - **The pumping station does not behave as the author expects** (see "Not done").

## What changed

**Builder** (`build_landscape_flood.py`, schema 3, about 75 s):
- **Hollows too small to matter are filled.**
  - Hollows smaller than 0.1 ha at their rim: area closing, 31,100 m³ in all.
  - Hollows shallower than 5 cm: filled to their rim, 5,300 m³.
  - The filled ground (the "hierarchy bed") now serves both views.
- **Water cells are outlets:** tidal (the tide polygons, 2 patches) and river (other mapped water, 9 patches; patches under 0.01 ha count as ground).
  - Each hollow's catchment is grown by a minimax priority flood: a cell joins whichever minimum or outlet reaches it at the lowest level over the ground.
  - A plain watershed was tried first and was wrong at the banks. A half-water 2 m cell at a polygon edge carries the bank crest (4.45 m by Mill Meads), and the watershed let the river claim the land behind it below that crest, so Mill Meads spilled at 3.56 m. The check now includes this case.
- **Merging** is in saddle order (Kruskal). A basin that meets a water patch, or ground already draining to one, is attached there.
  - Crest profiles: for each attached basin, the saddle level of every 2 m cell edge it shares with the water or the ground across.
- **Sluices.** Each of the ten marsh sluices in `lea-control-structures.json` drains the lowest hollow within 16 m of its mapped point, to the nearest water.
- **New files:**
  - `fine-basin.u16` (2.1 MB), the basin of each 2 m cell;
  - `coarse-basin.u16` and `coarse-basin-bed.u16` (0.8 MB each), the regional cells. A 10 m cell takes the basin of its lowest 2 m cell, and the mean ground of its cells in that basin; the lowest cell alone drew whole squares wet under a few centimetres.
  - `basin-volumes.f32` (25 KB), the stage tables.
  - The JSON gains `volume` (242 KB in all).
- **Scenario presets** live in `data/maps/flood-scenarios.json` with their evidence; every total is labelled an estimate.

**Estimates** (in the JSON `volume.parameters.estimates`):
- Weir coefficient 1.6. Free overfall overstates inflow once a basin fills; the water stands no higher than the source in any case.
- Sluice discharge 0.3 m³/s each: about a 0.6 m culvert under 0.5 m of head, reduced for flap, silt and weed.
- Sluice sills: the lowest drawn ground within 16 m (the ditch bed).
- No rain total for 1888 was found: the report gives none. The preset uses 50 mm over three days.

## Presets (land under water, the whole model; 2 m area around the core in brackets)

| Preset | Land wet | Rain in | Drained | Run off | Standing |
|---|---|---|---|---|---|
| Ordinary day | 1.1 ha (0.6) | 0 | 0 | 0 | 10,100 m³ |
| Summer storms, 1888 (50 mm, three days) | 427 ha (54) | 697,000 m³ | 129,000 | 35,000 | 539,000 |
| Winter storm, high tides (40 mm, a day, +0.4 m) | 406 ha (51) | 558,000 | 73,000 | 27,000 | 467,000 |
| Surge to the 1928 height (+1.7 m, one tide) | 747 ha (138) | 0 | 23,000 | 0 | 8.4 million |
| River held at 3.4 m ODN for a day, 20 mm | 375 ha (45) | 279,000 | 33,000 | 11,000 | 1.1 million |

- Most of the rain-wet area is the flat regional marsh outside the core: Plaistow Levels and the Stratford marshes. That ground is still the early-marsh surface outside the F1 zone.
- The ordinary-day water is one hollow at Bow, west of the Lea (−1053, 76): its crest is 1.41 m ODN, below the retained river datum (1.895 m) that the model holds in the non-tidal water beside it. This is F1's "Bow strip" again; Phase 2's pound levels and the ground there decide it.

## Checks

- `scripts/check_flood_volume.mjs` (new; in `npm test`, 22/22 pass):
  - a hand-built two-hollow model: own rain, spill, merge, the crest overflow, a thin surge sheet, the surge cap and a tide-locked sluice;
  - on the built model, volume balances to 1e-15 over 432 combinations of rain, surge, duration and river level;
  - levels never fall with more rain or a higher surge, nor with a longer duration for the tide and river;
  - no drawn water stands above its basin level;
  - the author's cases.
  - It writes `scenes/channelsea-sewer-panorama/review/flood-volume-checks.json`.
- `check_landscape_flood.py` adds a synthetic hierarchy (two hollows behind a bank whose edge cell is half water) and passes at schema 3. `check_core_river_connections.py` and `check_river_system.py` pass.
- The builder is deterministic.

## Renders

Renders at each preset, with five cameras:
- **Overview.**
- **Mill Meads in plan and oblique** (the allotments). On an ordinary day Mill Meads is dry. In the 1888 preset its southern half is under a shallow sheet up to the allotment furrows, and the water reaches the ground beside the Abbey Mills station.
- **North of the railway from the High Street.** Rain stands in the hollow beside the Waterworks River.
- **Stratford in plan.**
- **Fixed after the first renders:**
  - 10 m squares drawn wet by their lowest corner (speckle, striping);
  - z-fighting under sheets a few centimetres deep (a depth bias on the water);
  - a seam at the fine-box edge: the regional surface now runs under it and is cut in the shader where the 2 m surface begins.

## Not done, and why

- **The pumping-station ground floods too easily.**
  - In the drawn model the station (BNG 538719, 183223) stands at 1.88 m ODN on the same continuous low plain as Mill Meads, 35 cm above its floor. It is in the same hollow, so 50 mm of rain in one tide wets it.
  - No OS reading lies within 109 m of the station; its ground is interpolated from the streets and marsh around it. I have not raised it without evidence.
  - The 1888 report of "a fire engine to pump out a pumping station" may be West Ham's own station rather than Abbey Mills.
- **The river source** acts only on water outside the tide polygons, at one held level. The back rivers up to Temple Mills are tidal in the model, so high Lea flow does not raise them yet. Phase 2's pounds replace the held level.
- **No losses.** All rain on a catchment runs off: no soakage and no town sewers. Totals on the town's streets are overstated.
- **Timing.** Water is shown at the peak of the chosen conditions, not as it builds. The solver step (Phase 3) is unchanged.
- **The water material.** It is still the depth-tinted translucent layer, not the scene's water material (plan section 4.5).

## Decisions for the author

1. The pumping station: does the book or another source put its yard on made ground above the marsh? If so, I need a level, and the OS sheet may show one I have not found.
2. The preset totals (1888: 50 mm over three days; winter storm: 40 mm in a day with high water 0.4 m above ordinary) are placeholders. Are there figures you prefer?
3. Next, per the plan: F2 (back-river beds), then F3, then Phase 2.

## Phase V follow-up: the Abbey Mills station yard and its coal railway (6 October 2026)

**The station yard.** On the drawn ground the station stood at 1.88 m ODN in the Mill Meads hollow and flooded at 50 mm of rain. The author doubted it: the Metropolitan Board's engineers knew the marsh flooded, and no account of the station flooding has been found.
- **Evidence:** the Environment Agency 1 m LiDAR, flown 22 February 2003 (before the Olympic works), from `reference/topography-research-2026-09-28/tiles-2003`.
  - Against the 1890s OS readings within 550 m, its streets agree within 0.25 m and the sewer bank top within 0.03 m. The Mill Meads marsh readings are 1.8-4.4 m higher in 2003: later fill (the author: Prescott Channel spoil).
  - Round the 1868 engine house the 2003 ground is 3.98 m ODN within 4 m of the walls, 3.91 m at 4-10 m, 3.80 m at 10-20 m and 3.34 m at 20-35 m. On every side it is 3.78-4.03 m within 10 m.
- **Change:** a new register, `data/maps/made-ground.json`. The yard, 15 m round the building, is raised to 3.95 m ODN (estimate), falling at 1 in 12 to the marsh. `build_main_landscape.py` `raise_to_made_ground`: raise only, never in river, tidal or ditch water, nor on exposed tidal mud.
- **Effect:** the yard is its own hollow. No rain up to 150 mm over any duration reaches it, because Mill Meads spills to the tide at 3.78 m first. A surge of 1.05 m over ordinary high water is the first to reach it. `check_flood_volume.mjs` now asserts this.
- The 1888 "pumping station" flooding was probably West Ham's own station beside Bow Creek (author).

**The coal railway** (author: "add the tracks and basin for the coal").
- **Traced from the 1893 plan:** `data/maps/abbey-mills-coal.json`, by a line follower on the plan's rail lines (smoothed, good to about a metre).
  - A fan of four sidings along the engine house's north-east side joins one lead.
  - The lead runs south-east along the foot of the sewer bank, passes under the Long Wall path ramp, and turns south onto the Channelsea quay below the sewer bridge, where barges were unloaded.
  - The track does not join the G.E.R.: it ends at the river.
- **Bed:** the tracks lie on made ground (`made-ground.json` `abbey-mills-coal-sidings`).
  - It is level with the yard (3.95 m) through the fan, where the 2003 LiDAR is 3.86-4.29 m.
  - It then rises at about 1 in 72 to the quay at 4.9 m, the OS bank and wall tops there.
  - East of x -90 the 2003 ground is a later 9 m earthwork, so the lead's level is interpolated.
- **Drawing:** a cinder yard of its own (`build_factory_yards.py`, site 9101), drawn by `factory-yards.js` like the sawmill track. The rails stop a metre short of the path ramp, which reads as the track passing under it.
- **The unloading place** (the author's "basin") is the Channelsea quay where the lead turns south. The author, from the photographs: barges could unload only near high water; at low water they lay on the mud below the tidal limit.
  - The OS draws a river wall (a continuous double line) along that bank. It goes into `os-river-walls.json` with F3, which uses the same mechanism and the same rebuild.
- The east-west water south of the station is closed at both ends on the 1893 plan: probably a drain or pond, not a barge basin. Not added.
- **Checks:** `npm test` 22/22. `check_factory_yards.py`, `check_landscape_flood.py`, `check_east_depot_tracks.py` and `check_core_river_connections.py` pass. The cascade was rerun.

# F2: the back-river beds (7 October 2026)

The back rivers' beds were drawn 1.7 m below low water, like Bow Creek. The evidence puts them higher: all the back rivers were silted in 1908, the Pudding Mill River almost choked, and they were "navigable only during bimonthly spring tides". They are now silted beds that rise from a low-water stream at Three Mills to shoals at the heads, where the rivers leave the Old Lea and the Navigation. Scratch work (measuring and render scripts, before and after renders) is in the session scratchpad `…/1d5564dc-…/scratchpad/f2/`.

**Two revisions the same day.** First: It set one level per group (-0.4 scene, Pudding Mill +0.1), which left every bed bare until half tide. The author: too high and abrupt; the Pudding Mill River should be the worst, and could be dry at low tide; the silting should start at the top, where the rivers join the Old Lea, or be gradual. The book does not say the beds were dry until half tide: it gives the spring-tide navigation, the 1908 silting and the canal standard, which bound the shoals, not the whole bed. Second, on the profile below, the author said there should be some water all the way up to the Old Lea at low tide, "maybe a foot or so which isn't enough to float a large barge", and "the water is coming from both directions". So a low-water stream now runs down from the heads, and the tide rises over it from Three Mills. Third, the author: the seam should be where the back rivers start, not where the detailed network ends. So the profile, the tide and the stream now run on through the regional reaches to the Old Lea.

## Summary

- **New register `data/maps/back-river-beds.json`.** Every level is an estimate, recorded with its method.
  - **Outlet, Three Mills** (the House Mill race): **-2.2 scene (-0.37 m ODN)**, just below low water. A narrow low-water stream survives at the foot of the pond, as on the Channelsea below Abbey Mill (the author's 1920s-30s aerial). It meets the race passage (-2.6) without a step.
  - **Heads**: **0.0 (1.84 m ODN)**, where each river leaves the Old Lea or the Navigation:
    - the Waterworks River at (-1226, -1270), the City Mill River at (-1251, -1142) and the Pudding Mill River at (-1401, -914), all where they leave the Old Lea (regional reach Lower_River_Lea-15);
    - the Bow Back River at its mouth on the Navigation.
    - The Waterworks River's reaches above its junction (towards Temple Mills) are a channel of the Lea itself and are not raised. These are the shoals that limited navigation: ordinary high water gives 1.6 m over them and springs about 1.9 m, so loaded lighters passed only at spring tides. They lie above the 1892/1908 canal standard, "six feet below the overshot level at Bow Lock" (book p. 200; -0.88), which was proposed as a deepening of "clogged" beds (p. 201).
  - **Between them** the bed rises gradually along the water: t = a / (a + b), with a and b the distances along the channels to the outlet and to the nearest head. The distances run over all the back-river water, the network's channels and the regional reaches alike (`scripts/back_river_profile.py`), so there is no step where the detailed network ends.
  - **The Pudding Mill River** (8, 9, 21) stands **0.6 m above the profile** throughout, blended out over about 10 m where it meets the others. It is dry at low tide everywhere (lowest point 0.00 on 8, -0.57 at its junction), following the 1908 accounts (pp. 68, 203-204) and the author.
- **The low-water stream** (`lowWaterStream` in the register): the Lea's water running down the silted beds from the heads when the tide is out, a foot (0.3 m) over the thalweg, level across the channel and sloping from 0.3 at the heads to -1.9 at Three Mills; never below low water.
  - The scene draws the higher of the stream and the tide: at low water the stream shows alone; the rising tide comes up from Three Mills and covers it reach by reach.
  - It is drawn as its own still mesh (`river-network.stream.*`, about 31,000 triangles) with the tidal water's material.
  - The Pudding Mill River has none: dry at low tide.
- **The section** is a V in the silt. Inside the mapped outline the bed falls evenly from 0.9 m above the thalweg at the shoreline to the thalweg on the centreline (over the local half-width, at most 15 m). So the foot of water covers only 19-27 % of each river's bed at low water, a narrow stream in wide mud. The bank face outside rises from that edge to the bank crest over the same 5 m shelf as before.
- **Unchanged:** Bow Creek (0) and the Channelsea below Abbey Mill with Abbey Creek (14), the scoured tidal reaches below the mills; the Channelsea above Abbey Mill and the Navigation, which are still water.

**Beds, before → after** (bed vertices more than 1 m inside the outline; scene y; low water -2.0, mid-tide -0.21, high water 1.58):

| Channel | Before: lowest / median | After: lowest / median / highest | Bed wet at low water | Bed bare at mid-tide |
|---|---|---|---|---|
| Three Mills Wall River (1) | -3.70 / -3.63 | -2.19 / -1.53 / -0.27 | 19 % | 0 % |
| Three Mills Back River (2) | -3.70 / -3.16 | -2.14 / -1.43 / 0.00 | 9 % | 0 % |
| Waterworks River (3), High Street | -3.70 / -3.53 | -1.05 / -0.84 / -0.04 | 0 | 4 % |
| Waterworks River (4), to the north edge | -3.70 / -3.10 | -0.79 / -0.13 / 0.77 | 0 | 57 % |
| City Mill River (7) | -3.70 / -2.89 | -0.92 / -0.28 / 0.75 | 0 | 44 % |
| Bow Back River (17) | -3.70 / -3.10 | -0.58 / -0.05 / 0.78 | 0 | 72 % |
| Pudding Mill River (8) | -3.63 / -2.45 | 0.00 / 0.61 / 1.32 | 0 | 100 % |
| Pudding Mill River (9) and link (21) | -3.70 / -2.64 | -0.57 / 0.12 / 0.67 | 0 | 95 % |

## What changed

- **New `scripts/back_river_profile.py`:** the profile over all the back-river water.
  - It works on a 1 m grid of the network's corrected channels, the regional reaches as the river system draws them, and the passages; joins under 0.5 m are closed, as at x -1050. Two cells stay unconnected.
  - It gives the thalweg, the stream level and the bed by the shared section. `build_river_network.py` and `build_river_system.py` both read it.
  - It covers the network's west-context pieces of the Pudding Mill and Bow Back rivers (10008, 10017), which had kept the old deep bed.
- `scripts/tide_levels.py` reads the register (`BACK_RIVER_PROFILE`, `BACK_RIVER_ABOVE`, `BACK_RIVER_STREAM`, `back_river_thalweg`, `silted_bed`); `tidal_shelf` takes the bed edge it starts from.
- `docs/river-network.js` loads the stream (`lowWaterStream`) and draws it; `docs/app.js` adds it after the tidal surface and leaves it out of the meshes the tide moves (`userData.fixedLevel`; `keepIndexed` keeps it out of the per-material batch).
- `scripts/build_river_network.py`:
  - the thalweg field: distances along the silted water (8-connected 1 m raster, Dijkstra) from the outlet and from the heads. A 195 m² piece of the City Mill River's north arm joins the rest only beyond the network's edge; it takes the head level;
  - silted beds and their bank faces in `section()`, including the Wall River photograph bank;
  - the reviewed passages between back rivers (Pudding Mill, the Waterworks 3/4 seam, the Bow Back River mouth) take the thalweg instead of the tidal seam bed (-2.6). The Three Mills race keeps -2.6;
  - the low-water stream mesh over all the back-river water: the 1 m cells it wets, at the thalweg plus its depth (`river-network.stream.f32/.u32`, about 41,000 triangles);
  - `river-network.json` gains `backRiverBeds` and `lowWaterStream`;
  - the final assertion allows silted beds above the 0.06 still-water datum, but below high water.
- `scripts/build_river_system.py`:
  - the regional back-river reaches and the passages between them are tidal (`tidalReachIds`), so their water moves with the tide;
  - `river_bank_sections.py` gives them the silted bed and starts their bank faces at its edge. Their beds have rings out to 15 m inside the shore so the V reaches its centreline; other reaches keep two rings;
  - network vertices within 1.5 m of the back-river water are no longer lowered as "caps", either to -0.7 or to -2.6 under the tide. The network's ground inside the regional reaches takes the silted bed instead.
- `scripts/build_main_landscape.py`:
  - **span clearance:** a road-bridge span whose water is all silted back river is cleared to the highest silted bed under it, not to the 0.08 still-water edge (`roadBridgeClearance.spanLevels`: Pegs Hole 0.14, Hunts Lane 0.67, Marshgate Lane 0.71). Otherwise the banks under those bridges would be cut into a trench beside the bed;
  - `cap_junction_ends` leaves silted beds alone: channel beds keep their heights, as the builder's rule says.
- **Checks:**
  - `check_river_tides.py`: the "tidal bed below low water" rule excludes the back rivers. They must instead have a stream at Three Mills, silted heads and a Pudding Mill River dry at low water, all below high water. The stream must lie in the back rivers and their passages, between low water and the heads' level plus 0.31 m, reach Three Mills and every head except Pudding Mill's, and be absent from the Pudding Mill River;
  - `check_core_river_connections.py`: the silted passages lie at or below the highest thalweg;
  - `check_main_landscape.mjs` reads `spanLevels`;
  - `check_landscape_flood.py`: its component test now allows the same 1 cm quantisation as the check above it. One Wall River cell has bed 2.50 and connection 2.49 m ODN, and is wet at the 2.5 m stage;
  - `check_road_bridges.mjs` sample refreshed (see Checks).
- **Cascade:** river network, historic elevation, river system, main landscape, landscape flood, factory yards, drainage, flood demo, wharf cranes, manifest. Drainage, flood demo, wharf cranes and terrain change only in their input hashes. The river terrain is unchanged.
- **Flood model:** 121 hollows (120 before). The author's cases in `check_flood_volume.mjs` are unchanged: Mill Meads 1.76 m ODN at 20 mm; the pumping-station yard dry under any rain.

## Checks

- `npm test` 22/22. `check_road_bridges.mjs`: the stored sample was refreshed for the first version (only the Hunts Lane connection's approach moved, by up to 0.025 m); the revised profile matches it.
- Python `check_*.py`: 41 pass. Against the same commands on the branch head before F2 (a scratch worktree), there are no new failures. Two now pass:
  - `check_main_landscape.py`, which failed at the head on a stale `abbey-mills-coal.json` hash;
  - `check_core_river_connections.py`, which failed in the scratch tree only because a review folder was missing.
  - `check_remaining_trades_context.py` fails on both. It reports a different road each run (set order), and its inputs are untouched.
- The river network, river system and main landscape builders are deterministic (reruns byte-identical; the network rechecked on the revised profile).

## Renders

Before and after, at low and high water: an overview in plan; the Three Mills pond from House Mill; the High Street junction; the Pudding Mill and Bow Back rivers; the Waterworks River north of the railway; along the Wall River, the City Mill River, the Pudding Mill River and the Back River; the seams at the network's north edge. Sheets are in the main checkout's `reference/flood-model-f2/`.

- **Low water:**
  - before: every back river was a deep slot of water between tall dark mud faces;
  - now: a narrow stream runs down the middle of every back river from the heads to Three Mills, between wide mud banks; the Pudding Mill River is dry;
  - Bow Creek, the Navigation and the Channelsea keep their water.
- **Rising tide:** the tide comes up from Three Mills and widens the water over the mud reach by reach; it overtops the stream at the heads only after half tide, and covers the Pudding Mill River last. Renders at low water, 25 % and 50 % of the tide.
- **High water:** the same as before, bank to bank.
- **At the network's north and west edges** the mud ends against the regional still water, drawn at 0.06 as before.

## Not done, and why

- **The Old Lea at the heads** (Lower_River_Lea-15 and -22) keeps the regional still water at 0.06. At high water the tide in a back river stands above it at the junction until Phase 2 gives the Old Lea its level.
- **No individual shoals.** The profile is smooth between the outlet and the heads; the evidence gives no bar positions.
- **The Three Mills race** keeps its deep tail-race bed under the deck; its sill is unknown (the House Mill Trust may hold a record).
- **The ponds.** Above Three Mills the back rivers were the mill pond, held near the last high water while the tide fell. The model still drains them with the tide; Phase 2 holds them.

## Decisions for the author

1. Are the levels acceptable: the bed at -0.37 m ODN at Three Mills rising to 1.84 m ODN at the heads, a foot of stream in it at low tide, the Pudding Mill River 0.6 m higher and dry?
2. May F2 be committed? Next, per the plan: F3 with the Abbey Mills coal-quay river wall (one cascade through `os-river-walls.json`), then Phase 2.

# F2 follow-up: fixes after review, and the Lee Navigation bridge (7-8 October 2026)

## What changed

- **Dark mud on dry land east of the Waterworks River:** `river_bank_sections.fields()` draws tidal mud only on the shelf (`d<=5`).
- **Tracks sinking east of the Waterworks crossing** (an F1 effect): `os-ground-levels.json` `stratfordAtGradeRailways` (from `prepare_os_ground_levels.py`) and the "RAIL CUTS" clamp in `build_main_landscape.py`. The formation stays at 3.0 (the author: the OS is guidance, not a target).
- **Seam at the old core edge:** the back-river shelf no longer fades at the network edge; `siltedCoreBedCorrections` in `build_river_system.py` (network bank caps in silted water go to the shared bed), applied in `docs/river-system.js` and the landscape.
- **High water over the North London bridge decks:** `docs/great-eastern.js` no longer draws `northernWater` (a tidal copy at 0.06 rose 3.58 m with the tide).
- **The Lee Navigation at the North London crossing:** `crossing-517-518` runs between the middles of the two pieces' facing ends (`centreline: true`), not their nearest corners, 12 m east of the canal. The `nl-hackney-cut` bridge form moved -8.8 m in chainage with it.
- **The North London line over the Hackney Cut** (the author chose): `canalLift` {5.5, holdTo 100, rampTo 400} in `north-london-connection.json`, so the rails clear the towing paths.
- **The Lee Navigation was blocked under that bridge** (the author's screenshot: a brick wall filled the span). The embankment footprint opened only over the 1895 GIS water, and the cut's two pieces stop either side of the line, so the fill and its 5.5 m retaining walls crossed the canal. `canal_passage()` in `north_london_connection.py` now computes the same passage from Water_1895 pieces 517/518 (recorded as `canalPassage` in the register) and the builder opens the embankment over it. The line's own `bridges` gained chainage 53.2-74.6; `bridgeIntervals()` in `docs/railway-bridges.js` (was `addedBridgeIntervals`) merges it with the register's `nl-hackney-cut` (54.0-73.5), so one deck is drawn.
- **Regional landscape rebuilt** (`build_regional_landscape.py`, last built 5 October): its canal banks overlapped the moved Hackney Cut passage by 685 m². The rebuild also brings the regional grid up to the railway formations added since (2,146 of 452,018 10 m cells change by more than 0.1 m, nearly all kind 13, railway formation). In the main landscape only a few vertex counts change, and the Abbey Road spot height now falls on the 3.2 m path stub north of the sewer (not applied in either case). Flood grid: 28 fine and 3 coarse cells change; closed-hollow volume 31,292 → 31,313 m³; `check_flood_volume.mjs` cases unchanged.
- **Tried and reverted:** a regional 5 m shelf ring with a tidal-face limit (held OS bank crests up to 1.4 m low; `check_os_ground_levels` failed); the network using the shared bed everywhere / a nearest-cell `bed_at` fallback (moved about 700 core vertices up to 4.5 m).

## Checks

- `npm test` 22/22; the `check_road_bridges.mjs` sample refreshed (Hunts Lane approach, up to 0.003 m).
- `check_river_banks.py` now requires silted back-river bed vertices to lie on the registered bed (`back_river_profile`); the vertices that broke the old "0.35 m under the water" rule (9,832) all lie exactly on it. Every other bed vertex keeps that rule.
- Python `check_*.py`: 42 pass (41 after F2). The 33 failures are hash pins, frozen snapshots and the `site256-range-1` alignment checks; none is new.
- Renders: the Hackney Cut under the North London bridge from the water and from above, at low and high tide (main checkout `reference/flood-model-f2/lee-navigation-bridge-before-after.png`).

## Still open for the author

- The regional bank faces past the old core edge are steeper and higher than the network's (they stand at their OS crests): accept, or lower the network side?
- The North London line ends at x -1700 in a 3 m earth end, about 45 m past the cut; the GIS route runs on to x -2212.

# F3: the West Ham Chemical Works river wall and the Abbey Mills coal quay (8 October 2026)

## What changed

- **Two OS river walls** in `data/maps/os-river-walls.json`, traced on the five-foot plan at 8 px per metre (the task A mechanism: the drawn shoreline within 4.5 m of each line becomes a retaining-wall route in `build_river_network.py`):
  - `west-ham-chemical-works-river-wall`: the straight double line along the works frontage, z 211.5 to 268 at x about -23.3 (57 m drawn). North of z 211 the OS draws a hatched earth bank, not a wall, so that stretch keeps the os-flood-banks.json bank. The 17.9 ft wall-top reading (sh_538885_182963, 3.22 m scene) stands on the strip behind it; the coping is 2.91-3.15 m.
  - `abbey-mills-coal-quay-wall`: the double line on the Channelsea west bank from the Northern Outfall Sewer bridge to about z 43, where the coal lead ends (40 m drawn). No reading on the wall; the coping (3.32-3.5 m) is the model's, the higher of the bank crest and the ground behind.
  - Each records `quayWidthMetres` (7 and 6 m, the OS strip behind the wall): the wall fill stands level with the coping over that width, then falls at 1:1.5. Other walls keep the 3 m berm.
- **`build_main_landscape.py`, the core behind OS walls** (`osGroundLevels.osRiverWallLand`):
  - the core's tidal-mud study had mud up to the works buildings and on the quay, and preserved mud blocks the wall fill, so the first build left the works wall standing on the foreshore with the river behind it at high water. 3,681 core vertices within 10 m on the land side of the OS wall routes are no longer kept as mud, and the 1:1.5 cap above the mud in front does not reach across the wall;
  - the core's 0.4 m grid has no edges on the wall line, so cells across it stood up through the wall's water face as dark teeth. The core within 0.6 m behind each OS wall is held at -2.0 (the wall body reaches -2.5), so the rise to the fill lies behind the brick.
- `data/maps/abbey-mills-coal.json` `unloading.wallFace` records the quay wall.
- **Cascade:** river network, historic elevation, river system, main landscape, landscape flood, factory yards, drainage, flood demo, wharf cranes, manifest.

## Renders

Before (the F2 commit) and after, at low and high water: the works frontage from the Channelsea and from above; the coal quay from the water and from above. Main checkout `reference/flood-model-f2/f3-river-walls-before-after.png`. The works wall now holds a level quay strip to the buildings at high water; the coal quay wall stands behind the moored barge, the ground behind it level with the coping.

## Not done, and why

- The quay strips draw in the dark ground colour of the mud they replace (the core's land cover); a yard surface was not asked for.
- From above, a thin dark fringe runs along the top of each wall: the 0.6 m slot behind it.
