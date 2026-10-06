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
- **Not added: the basin.** The east-west water south of the station is closed at both ends on the 1893 plan. It is square at the west by the south building; at the east it stops short of the Long Wall bank, with no lock, sluice or culvert lettered. The barges came to the quay on the Channelsea. Whether the cut was a coal basin, a cooling pond or a drain is for the author.
- **Checks:** `npm test` 22/22. `check_factory_yards.py`, `check_landscape_flood.py`, `check_east_depot_tracks.py` and `check_core_river_connections.py` pass. The cascade was rerun.
