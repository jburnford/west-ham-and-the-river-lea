# Plan: rain, river, mills and tide flooding for the c.1890s model

Handoff plan for a new session, written 5 October 2026. The author asked for the square flood view to be replaced by flooding that comes mainly from rain and shows how the mills and locks dammed the Lower Lea.

Read first:

- `CLAUDE.md`
- `WORKTREE_GUIDE.md`
- `scenes/channelsea-sewer-panorama/OPUS_DELEGATION_PLAN.md`, the open fundamentals
- `TASK_C_REPORT.md` and `TASK_D_REPORT.md`
- the memory notes `flood-model-direction`, `tide-evidence`, `follow-the-maps` and `agent-delegation-lessons`
- `FLOOD_PHASE0_NOTE.md` and `TASK_E_REPORT.md` (task E so far)

## 0. Status, 7 October 2026: start here

**Branch and worktree.**

- Work is on branch `task-e-flood-model`, in worktree `/home/jic823/book_website-taske`. Continue on this branch, from its head.
  - Serve it with `python3 -m http.server 4211 --bind 127.0.0.1 --directory docs`, run from the worktree.
- Nothing from tasks D or E is live:
  - `origin/main` (GitHub Pages) is at `841fbbd`.
  - Local `main` is at `e59ad25` (task D, 3 commits ahead, unpushed).
  - Task E is unmerged.
  - Merging and pushing wait for the author.

**Done.**

- **Phase 0:** `data/maps/lea-control-structures.json`, revised after the author's review (see section 6).
- **Phase 1:** the whole-model flood grid (`scripts/build_landscape_flood.py`, `docs/landscape-flood.js`).
- **OS flood banks** (the author: "fix the rivers"): `data/maps/os-flood-banks.json`, raised in `scripts/build_main_landscape.py` (`raise_to_flood_banks`).
- **F1** (the ground north of the core, to the OS): done 6 October 2026, commits `2621cb2`, `42d842e` and `b2426a4`. Reported in `TASK_E_REPORT.md` under "F1" and "F1 follow-up".
- **Phase V** (volume, not a switch): done 6 October 2026, commits `a65be7f` and `ef0479e`.
  - Builder `scripts/flood_basins.py`, the depression hierarchy, wired into `build_landscape_flood.py` (schema 3).
  - Router `docs/lib/flood-volume.js`.
  - Presets in `data/maps/flood-scenarios.json`.
  - The `?flood` page: a volume view, with the old view kept as "Connected extent".
  - Check `scripts/check_flood_volume.mjs`.
  - `TASK_E_REPORT.md` "Phase V".
- **Abbey Mills station yard and coal railway:** 6 October 2026, commits `4187e69`, `05ddc83` and `5c78dbf`.
  - New register `data/maps/made-ground.json`: the yard at 3.95 m ODN from the 2003 EA LiDAR, and the coal track bed. `raise_to_made_ground` in `build_main_landscape.py`.
  - Coal sidings and lead to the Channelsea quay traced from the 1893 plan: `data/maps/abbey-mills-coal.json`, drawn as cinder yard site 9101 by `build_factory_yards.py`.
  - The yard is dry under any rain and first wet by a 1.05 m surge.
  - The 2003 LiDAR is in `reference/topography-research-2026-09-28/tiles-2003`; read the tiles with Pillow (no GDAL or imagecodecs here). It matches the 1890s OS on streets within 0.25 m, but Mill Meads was filled later.

**Open questions for the author.**

- F1: the Channelsea head closures (inferred, not lettered); trimming the 2 m network-join ring (+1.8 MB).
- Phase V: the preset rain totals (placeholders); the "without the mills and locks" comparison for Phase 2.
- Going live: merging and pushing tasks D and E.

**Next, in this order (proposed 7 October 2026; the author has not yet chosen):**

1. **F2** (back-river beds, section 5). The longest cascade: it starts at the river terrain. Review renders at low water.
2. **F3 with the coal-quay wall.** The works wall face and the Abbey Mills coal quay wall both go into `data/maps/os-river-walls.json`, in one cascade.
   - The quay wall: the OS double line on the Channelsea west bank from the sewer bridge south past the quay; see `abbey-mills-coal.json` `unloading`.
3. **Phase 2** (pounds). It replaces Phase V's single held river level, which acts only on water outside the tide polygons. Then Phases 3-5.

**Tools.** `scripts/flood_diagnostics.py`, on a dump made with `FLOOD_DUMP=… python3 scripts/build_landscape_flood.py`:

- `pour x z`: the basin at a point and where it fills from;
- `spills [level] [x0 z0 x1 z1]`: land spill crests below a level in the core box (or the given box);
- `banks`: the registered banks against their OS readings;
- `readings`: OS bank-top and wall-top readings drawn more than 0.5 m low.

**Worktree setup.**

- Git-ignored inputs are linked per entry, including nested folders such as `reference/spot-heights/mosaics`.
- The book PDF is linked into the worktree root; `check_drainage_connections` needs it.

## 1. Purpose (author's direction)

- **Most flooding came from too much rain, not from the tide.** Three mechanisms matter:
  - rain on the marsh, which ponds behind the banks when the tide-locked sluices cannot drain it;
  - rain upstream, arriving as high Lea flow;
  - the tide or a surge, which mattered less often.
- **The mills and locks made a line of dams across the Lower Lea.** Their held heads, combined with rain upstream, made the floods.
- **Teaching aim.** One of the project's key lessons is the human nature of this landscape long before heavy industrialisation. The flood view should let a visitor see that the "natural" marsh river was already engineered: mill heads, locks, flood gates, sluices and banks.
- **Period: the 1890s now.** The OS five-foot plan (1893-96) is the base. Later, once the landscape is built, later features will be stripped away step by step towards an 1809 model, the Wanstead flood year. The author also has the 1860s OS; that is a separate project. Do not start either here.
- **Estimates are expected.** The author's book probably has no head heights. Head, crest and gate levels will be estimated, labelled as estimates in the registers, with the readings that bound them.

## 2. Where things stand (main after task D)

| Piece | State |
|---|---|
| `?flood` view (`docs/landscape-flood.js`, `scripts/build_landscape_flood.py`, `docs/data/landscape-flood-1900.*`) | A precomputed 4 m grid over a fixed box, x -510..550 and z -320..832 (1.22 km²). Each cell stores its highest ground (`bed`) and the lowest level at which water can reach it from tidal cells (`connection`). The page draws one translucent plane over the box, with its own slider from 1.9 to 5.5 m ODN, and swaps the scene's water to a plain material. At high levels the water fills the box and stops square at its edges. It misses Three Mills and the Lea west of x -510, and the edges are stepped at 4 m. |
| Tide (`docs/tides.js`, `docs/data/river-network.json` `tide`, `data/maps/os-tide-levels.json`, `scripts/tide_levels.py`) | Low water -2.0 m and high water 1.578 m (scene y; ODN = y + 1.835). The tidal limit is at Abbey Mill. The moving water is drawn over fixed tide polygons, the "envelope". |
| Non-tidal water | One flat datum, 0.06 m scene (`tide_levels.RETAINED`, "historical levels unresolved"), for the Old Lea above the locks, the Channelsea above Abbey Mill, the moats and the marsh ditches. **The model has no pounds, no heads and no falls.** This is the main gap for the teaching aim. |
| Mills and locks | Three are geometric passages in `core_river_connections.py`: Pudding Mill, Three Mills (the House Mill race, under a deck since task D) and Bow Locks (the lock passage). The Abbey Mill race is the tidal-limit step. |
| Control-site register | `data/maps/lower-lea-region/connection-review.json` (built into `docs/data/lower-lea-region/index.json` `connectionReview`). It lists 11 control sites: Abbey Mill (Corn), Three Mills, City Mill, Waterworks Mill, the Waterworks River flood gate, Pudding Mill/St Thomas's Mills, Bow Locks, the lock beside Marshgate Lane bridge, Old Ford Lock, the Old Ford side floodgate and the Temple Mills weir. Each has evidence ids (book-ch1, book-ch6 and the author's maps) and period comparisons. `futureHydraulics` already specifies the parameters `crestODN`, `sillODN`, `openingWidthMetres` and `operatingState`, with requirements: both sides of a control, upstream storage, and backwater with river input and downstream tide. A proposed Three Mills tide gate (1898) is recorded as rejected and inactive. |
| Rain solver prototype | `docs/flood-solver.js` (local-inertial routing, rain in mm/h, culvert, gate, pump), `docs/flood-demo.html` and `docs/flood-worker.js`, with `scripts/build_flood_demo.py` and `check_flood_demo.mjs` / `check_flood_solver.mjs`. It covers a 540 × 160 m strip only. |
| Ground | `docs/data/main-landscape-1900.*`. Banks, walls and streets are fitted to the OS levels in the core box; the regional landscape extends to BNG 535000-542000 E, 180000-187000 N. |
| Flood evidence | `data/maps/historic-flood-events.json`: 1897-11-29, 1898-10-29, 1904-12-30, 1928-01-07 (surge) and `1888-07-30-rainfall-sequence` (rainfall and local drainage; no river peak or surge established). It also holds relative marks and period-change constraints (local fill, drainage, the Northern Outfall Sewer). |
| Flow | `G2G_Oudin_flow_1891_2015.csv`: the author's file, untracked, 86 MB, in the main checkout root. Daily G2G modelled flows by NRFA station; **column `38001` is the Lee at Feildes Weir**. Over 1891-1910 the median is 4.6 m³/s, Q95 is 2.0 and the peak is 40.9 on 15 Nov 1894. Daily means, not event peaks. |
| Book | `West Ham and the River Lea_ A Social and E - Jim Clifford.pdf`, in the main checkout root. Git-ignored and never committed: **keep it out of commits and pushes.** The register cites chapters 1 and 6. |

**OS levels at or near the structures** (`data/maps/os-ground-levels.json` readings, scene y). Use these to bound heads and crests:

- **Abbey Mill:** B.M. on the building, sh_538879_183257, 2.785; Abbey Road at the tidal-limit note, sh_538874_183253, 2.188.
- **Three Mills:** the bridge, 3.70 and 4.23; the lane at the House Mill race, 2.706; the lane by the W.M., 2.249.
- **Bow Creek:** the side of the Tidal Lock, sh_538275_182327, 2.197; the Sun Mills wall, 2.249-2.401.
- **Four Mills Distillery:** 2.676 and 3.416.
- **City Mills:** a yard to the south, 2.737.
- **St Thomas's Mills:** 3.45 and 2.798.
- **Bromley Lock:** a street beside it, 5.449.
- **The marsh sluices:** sh_538469_182979, a culvert/sluice, 0.746; sh_538923_182626, by the Sluice, -0.86; sh_539070_182630, -0.83; sh_539172_182787, Manor Road by the Sluice, -0.22.
- **Towing paths** (bank crests): 2.07-2.58.

## 3. What the visitor should get

One water panel in the main scene, replacing the separate `?flood` page:

1. **Tide**: low to high water, as now, plus a surge allowance.
2. **Lea flow**: m³/s from upstream. The scale and presets come from the G2G record: dry summer, median, wet winter, and the 1894 peak.
3. **Rain on the marsh**: a storm total in mm.
4. **The mills and locks**: each structure (or a group switch) can be set "working: head held", "gates drawn" or "shut". With the same rain, the visitor sees what the dams do.

Behaviour:

- The water stays continuous: the same material and level surfaces as the tide, over the whole modelled ground, with no box edges and no 4 m steps.
- Short captions explain each mechanism and say plainly which levels are estimates.

## 4. Model design

All facts go in `data/maps` registers; builders write `docs/data`; the browser only evaluates. Keep the shared origin (EPSG:27700, E538900 N183209, scene x east, z south, y up).

### 4.1 Structure register (new: `data/maps/lea-control-structures.json`)

One record per control, starting from the 11 control sites plus any the OS five-foot plan shows that they miss (check the Bow Back Rivers, the Channelsea head, the Abbey Creek sluices, Bromley Lock and the Limehouse Cut). Each record holds:

- id and name;
- type: tidal mill, mill head, lock, weir, flood gate or sluice;
- location and line across the channel (scene and BNG);
- the reach (channel ids) above and below;
- crest or sill level and opening width. These are estimates, each with its bounding readings and method;
- operating states, and the default for c.1895 with its evidence;
- dated existence (follow `futureHydraulics`: 1848-50, 1888, 1897, 1900, 1904, 1928);
- sources: book page, OS sheet, period comparison.

**Three Mills is a tidal mill** (it impounded the flood tide and milled on the ebb). Record how its pond and the tide interact; the House Mill race passage is under the task D deck.

### 4.2 Pound levels from flow (a pure function, `docs/lib/pounds.js`)

- **Flood state (author, 6 October 2026).** Flood water is released (gates drawn); the head is what the flow needs to pass the structure's limited opening, so the restriction, not a held head, makes the flood. Ordinary days keep the working heads.
- **Steady state.** Given the Lea flow Q, the structure states and the tide level, compute each pound's water level from the sea upward:
  - The tail level is the tide (below the tidal limit) or the pound below.
  - The head is the greater of the tail level and the crest plus the weir head for the flow over or through the opening (an estimated discharge coefficient, recorded).
  - Split the flow between parallel routes (the Bow Back Rivers) by opening.
- Channel friction between structures can wait; record it as a limitation.
- Unit-test it: monotonic in Q; drawn gates lower the heads; tidal tail levels propagate only up to the next structure.

### 4.3 Spill onto the land (replaces `build_landscape_flood.py`)

- Rebuild the grid over **the whole drawn ground**: 2 m (or 1 m) in the core box, coarser over the regional landscape. Take the highest drawn surface per cell, including walls, embankments and streets, as now.
- For **each pound and for the tidal water**, precompute each cell's connection level from that source (minimax path, as `connection_levels` does now). Store it only where it is below a cap such as 6 m ODN, so the files stay small.
- In the browser, a cell is wet if any source's current level exceeds its connection level from that source. The water surface there sits at that source's level.
- Pounds spill into each other over the land where banks are low. That is part of the lesson; check it is shown, not hidden by a single level.

### 4.4 Rain on the marsh (fill and spill first)

- **Builder.** Find the closed hollows (a priority-flood depression hierarchy on the same grid), their catchments, and their storage-to-level curves. Record which drain or sluice each empties through: the marsh drains in `river-network.json` `marshDitches` and the OS sluice readings above.
- **Browser.** The rain total times the catchment fills each hollow, which spills into its neighbour or its outfall when full.
- **Tide-locking.** An outfall drains only while the water outside (the tide or the pound) is below its sill. For a storm, the drainable share depends on the tide cycle; start with a simple rule and record it: drains open for the low-water part of each tide, below the sill.
- The existing solver (`flood-solver.js`) is the later step, for showing how a storm builds over time. Do not scale it to the whole model in this task.

### 4.5 Drawing

- Draw the wet areas as water at their levels, using the scene's water material (`materials.tidalWater` / `materials.water`), not a separate translucent plane.
- Smooth the edges: interpolate the level-minus-connection field per fragment rather than sampling cells, or contour it on the CPU.
- Keep it fast on a phone (the lite tier): no per-frame grid rebuilds; textures at most 2048².
- Later, consider deriving the tide outline itself from the tidal connection field ("ground below high water that connects to the channel"; see the junction notes in `TASK_D_REPORT.md`). At ordinary tides it adds almost nothing on land.

### 4.6 Volume, not a switch (Phase V; author, 6 October 2026)

**The problem.** The Phase 1 grid stores, per cell, the lowest level at which a source reaches it (a minimax path). The page draws every cell below the chosen level as wet, at that level. So a basin goes from dry to full as soon as the level passes its rim: Mill Meads (27 ha, rim 3.78 m ODN, floor median 2.07 m ODN) jumps to 1.7 m deep. Real water arrives as a volume and fills the lowest ground first.

Figures from the F1 build (`flood_diagnostics.py pour -300 200` and the dump): filling Mill Meads to its rim takes about 450,000 m³. Its lowest 6 ha are wet with about 9,000 m³, roughly 35 mm of rain on the bowl itself with the sluices tide-locked.

**Builder** (extend `scripts/build_landscape_flood.py`, or a new `build_flood_basins.py`; same 2 m grid, bed, `inside` and water masks):

- **A depression hierarchy** over the land cells (priority-flood merge tree). For each basin, record:
  - its spill level and where it spills: a sibling basin, its parent, or water (a channel or source);
  - its stage–area–volume table (5 cm steps);
  - its rain catchment (the land cells that drain to it);
  - its outfalls: the marsh drains and sluices (`river-network.json` `marshDitches`, the sluice records in `lea-control-structures.json`), with their sills.
- **Merge noise.** Merge basins shallower than about 5 cm or smaller than about 0.1 ha into their parent (thresholds recorded).
- **A basin-id texture** at 2 m (fine box) and 10 m (outside), plus a per-basin table, in `docs/data`.
- **Keep the connection levels.** They say which basins each source can reach and over which crest; the "connected extent" view can stay as a mode.

**Sources, as volumes:**

- **Rain.** Storm total (mm) × catchment, less the outfall drainage. Drains run only in the low-water part of each tide, below their sill (section 4.4), for the chosen duration in tides.
- **Tide or surge over a bank.** Weir flow over the basin's spill crest, Q = C·L·(h − crest)^1.5. L is the crest length at the spill level; C is an estimate, recorded. Integrate over the time the tide curve (`docs/tides.js` cycle, peak raised by the surge) stands above the crest. A surge 5 cm over a rim for one tide then puts a thin sheet in the bottom of the bowl.
- **River.** In Phase V, the same weir rule from a level held by the river for the chosen duration. Phase 2 replaces that level with the pound levels from flow.

**Browser** (pure functions in `docs/lib/`, unit-tested; `docs/landscape-flood.js` draws):

- Route the volumes down the hierarchy: fill each basin, then spill the excess to its target. Water spilled to a channel is lost in Phase V.
- Each basin's level comes from its stage–volume table. A cell is wet where its bed is below its basin's level.
- Per-basin levels go in a small texture updated on input; no per-frame grid rebuild (lite tier).

**Acceptance:**

- **Volume is conserved:** in = stored + spilled + drained, to 0.1 %.
- **Monotone:** more rain, a higher surge or a longer duration never lowers any basin's level.
- No water above its basin level, and none on ground above it.
- **The author's cases:**
  - modest rain with tide-locked sluices wets the lowest Mill Meads hollows;
  - the Abbey Mills pumping station ground stays dry until the inputs are large;
  - a just-overtopping surge for one tide fills only part of a large basin.
- Renders at presets (dry day, the 1888-07-30 rainfall estimate, a winter storm with high tides), and the author's two views (Mill Meads allotments; north of the railway from the High Street).

**Read first:** `data/maps/historic-flood-events.json` (the 1888 rainfall sequence, relative marks) and the book's flood accounts, for plausible totals; label every total as an estimate.

## 5. Phases and acceptance criteria

**Phase 0: evidence and register (author checkpoint before any modelling). Done 5 October 2026.**

- Read the book chapters on the mills, the Lea and flooding in full (start with chapters 1 and 6). Note what the text establishes about heads, gate operation, millers' and navigation disputes, and the 1809, 1888 and later floods, with page numbers.
- Survey the OS five-foot mosaic (`scripts/factory_map_sources.py` `mosaic`) at every control, with crops.
- Draft `lea-control-structures.json`: every number marked "estimate" or "mapped", with its method.
- **Deliverable:** the register, crops, and a short note listing every estimate. **Stop for the author's review.**

**Phase 1: whole-model flood grid. Done 5 October 2026** (the figures are in `TASK_E_REPORT.md`; the old-box comparison differs because land now excludes all mapped water and water arrives from outside the old box).

- New builder replacing `build_landscape_flood.py`: whole extent, finer core cells, per-source connection levels.
- Old behaviour reproduced for the tidal source. Compare connected land at 1.9, 2.5, 3.5, 4.5 and 5.5 m ODN with the current figures, which are 0 / 0.03 / 51.09 / 105.63 / 114.47 ha in the old box after task D.
- No straight edges at the old box; no water on ground above its level; checks updated (`check_landscape_flood.py`).

**Fundamentals before Phase 2 (author, 6 October 2026: "add those three corrections").** Each one is checked with `scripts/flood_diagnostics.py` and renders before and after, then runs the cascade (main landscape → landscape flood → factory yards → drainage → flood demo → wharf cranes → manifest; F2 starts earlier, at the river terrain).

- **F1. Regional ground north of the core, to the OS.** Outside the core box the regional "early-marsh" ground lies below the OS readings. Median by area: Stratford Marsh north of the High Street -1.08 m, Temple Mills -0.79 m, east -0.48 m, south -0.58 m; a tenth of readings are 2.5-3.4 m low.
  - The rain-up-river flood plays out north of the core, so start with the zone from the High Street to the Waterworks River flood gate and Temple Mills. Fit the ground to the OS ground readings, as T21/T22 did inside the core (`os_ground_levels.py`, `data/maps/os-ground-levels.json`, which covers only the core box). The readings are in `reference/spot-heights/heights.geojson`.
  - **Stratford High Street causeway.** It is missing outside the core box: the drawn ground runs at about 0.2-0.4 m scene where the road should stand. Mill Meads (22 ha) fills at 2.23 m ODN, entering at a low Waterworks River bank north of the High Street (-546, -379) and passing round the core's north edge.
  - **Waterworks River banks** north of the High Street: hatched on the plan; give them their OS crests (an `os-flood-banks.json` record or the T21 method).
  - **The Channelsea head.** The regional channel network joins the Channelsea to the tidal Waterworks River near Temple Mills (Potter's Ditch, the Artificial Manure Works passage), so the tide reaches the upper Channelsea round the Abbey Mill gates. Check the OS for sluices there (the five-foot plan has labels at (-905, -2282), (-946, -2369) and on the Channelsea west bank at (-1183, -1582)) and close or gate that link.
  - **The Poplar side of Bow Creek south of the core** (about 97 ha) floods at about 3.39 m ODN, just under ordinary high water: the same regional problem to the south. Lower priority than the north.
  - **Done when:**
    - drawn-minus-OS medians in the fitted zone are within 0.1 m;
    - `flood_diagnostics.py spills 3.414` finds no land spill below ordinary high water into Mill Meads or Stratford Marsh;
    - `pour -300 200` reports Mill Meads filling above high water.
  - This leaves the core box, which `follow-the-maps` kept for later; the author approved it for this zone on 6 October 2026.
- **F2. Back-river beds.** The model's back-river beds lie at -2.1 to -3.7 m scene (medians by channel: Wall River -3.22, Back River -2.55, Waterworks -2.89/-2.55, City Mill -2.12, Pudding Mill -2.12, Bow Back -2.55).
  - The evidence puts them much higher. The back rivers were "navigable only during bimonthly spring tides" (book p. 200). The 1892/1908 canal standard was "six feet below the overshot level at Bow Lock", about -0.9 m scene, proposed as a dredging, so the silted beds stood above it.
  - Raise the beds of channels 1, 2, 3, 4, 7, 8, 9, 17 and 21. The level is an estimate, recorded in a register with its method; the lea-control-structures register's drawdown estimates give the range. Bow Creek and the tidal reaches below Three Mills stay as they are.
  - This changes the drawn mud at low water on every back river. Start the cascade at the river terrain and river network (task C order) and review renders at low water.
  - Phase 2's ponds depend on these beds.
- **F3. A masonry face for the West Ham Chemical Works river wall.** The OS draws a river wall (double line) along the works frontage from z 190 to 273 at x about -19. Task E gave it the right crest (3.04-3.22 m) as an earth bank face in front of the buildings (`ew-oblique-high` render).
  - Add it to `data/maps/os-river-walls.json` (the task A mechanism: a retaining-wall route on the drawn shoreline, coping from the wall-top readings), so it draws as masonry.
  - Keep the `os-flood-banks.json` crest behind it, and keep the 46 raised tidal-mud vertices accounted for in `check_main_landscape.mjs`.

**F1 done 6 October 2026** (`TASK_E_REPORT.md` "F1" and "F1 follow-up"): the Stratford zone at the OS (median drawn − OS -1.08 → -0.009 m over 132 readings), the Channelsea head closed, the network-join seam meshed, and the flood grid's holes removed. Mill Meads now fills at 3.78 m ODN.

**Phase V: volume, not a switch (author, 6 October 2026). Done 6 October 2026.** See section 4.6 for the design and acceptance criteria. It comes before F2 and F3. It takes over Phase 3's fill and spill, and extends it to the tide and the river.

**Phase 2: pounds.**

- `docs/lib/pounds.js` with unit checks.
- The non-tidal reaches move off the single 0.06 datum to their pound levels at median flow and working heads. This changes the drawn retained water, the river network's retained ids and the marsh ditch levels, so plan the cascade.
- Renders: City Mills, Pudding Mill, Three Mills, Abbey Mill and Bow Locks, each showing a visible step at its structure.

**Phase 3: rain over time.** (The fill and spill moved into Phase V.)

- The storm as it builds over hours (`flood-solver.js` where it helps), outfalls and tide-locking refined.
- Test cases: a dry day; the 1888-07-30 rainfall sequence (estimated total, labelled); a winter storm with high tides.
- Checks: water volume is conserved; hollows fill in order; no water on ground above its level.

**Phase 4: controls and teaching.**

- Tide, Lea flow, rain and structure states in the main tide panel (`docs/tides.js`, `docs/app.js` registration only).
- Presets and captions.
- Retire the `?flood` page, keeping its assumptions text. Keep `flood-demo.html` as the linked drainage experiment.

**Phase 5: verification and report.**

- `npm test` at baseline; Python checks compared against main.
- Smoke (scratch copy of `review_smoke.py` with 900 s waits); renders before and after at low and high water and at flood presets.
- Report `TASK_E_REPORT.md` in the house style (`TASK_C_REPORT.md` / `TASK_D_REPORT.md`).
- Update the plan's open fundamentals.

## 6. Decisions for the author (ask at the Phase 0 checkpoint)

**Answered 5-6 October 2026:**

- **The mills.** Pudding Mill held water. City Mills was operational to some extent. The Waterworks River had no mill: its flood gate stands on the old mill site. Three Mills and Abbey Mill were working.
- **The ponds.** A working mill's pond is held at the last high water while the tide falls, not a steady pound (this changes 4.2).
- **The Navigation** is walled off from the Three Mills pond. It held its level at the Three Mills overfall and the Bow overshoot, and let the river through to Bow Creek.
- **Flood types.** Several kinds eventually; the flood from rain up river comes first.
- **Corrections.** F1-F3 above, before Phase 2.
- **Volume first (6 October 2026).** The connected-level view is a switch; flooding should come as volumes filling the lowest ground first (Mill Meads often, the Abbey Mills ground only in bad floods). Phase V comes next, before F2 and F3.

**Answered 6 October 2026 (decisions 2-5 below):**

- **Flow (2): a slider** in m³/s, ticked at the G2G presets: dry summer (Q95 2.0), median (4.6) and the 15 November 1894 peak (40.9). G2G gives daily means, so the slider runs past the peak (about 60) and the caption says event peaks were higher.
- **Rain (3): a storm total in mm**, because fill and spill needs only the volume. It is paired with a duration in tides (one tide, one day, three days), which sets how many low-water windows the tide-locked sluices get. Rain over time waits for the solver.
- **Structures (4): no switches per structure.** In a flood the millers and lock keepers are taken to have released flood water (gates drawn), but the passages were still so narrow that they held the river up and caused the flooding (author). So the heads come from the flow through each structure's limited opening. The opening widths and sill levels are the key estimates. A single "without the mills and locks" comparison (an open channel) is proposed; it waits for the author's agreement.
- **Default view (5): an ordinary day**, with the 1894 peak one click away as a preset.

Decision 1 (the structure list) was answered on 5 October (above).

1. **The structure list** for c.1895: which mills were working and holding heads, and which were works by then (for example City Mills (Chemical) and St Thomas's Mills (Patent Food)). Is the default "working heads held" or "as the 1890s operated"?
2. **The flow control:** in m³/s with G2G presets, or as named scenarios only?
3. **The rain control:** a storm total (mm) is simplest. Is rain intensity over time (the solver) wanted later?
4. **Whether the user may switch individual structures**, or only "mills working" against "gates drawn".
5. **The default flood view:** an ordinary day, or a dated event?

## 7. Working notes (lessons from tasks A-D)

**Setup**

- Work in a worktree on a new branch from main (merge task D first). Symlink the git-ignored inputs per entry: `reference/` entries, `node_modules`, the book PDF if needed. Use a free http.server port; 4173 is main.

**Cascade order**

- River terrain → river network → historic elevation → river system → main landscape → landscape flood → factory yards → drainage connections → flood demo (it stores the drainage hash) → wharf cranes → manifest. About 15 minutes.
- Refresh `check_road_bridges.mjs --write-sample` if any approach moves.

**Side effects to watch**

- Opening or closing a passage changes the river system's shoreline topology, and with it the regional bank-crest interpolation (`regional_continuous_structures.Banks`). That moves ground far away; check the smoke diff for distant seated objects.
- Re-triangulating connected street polygons moves the whole road fit. Cut new decks locally (`LOCAL_CUT_DECKS`).

**Checks**

- 34 Python `check_*.py` fail on main too (stale one-off alignment checks and hashes). Compare their messages with main's; don't expect them to pass.
- `check_gltf` needs the git-ignored `.glb` exports.
- Builders must be deterministic: rerun and compare bytes.

**Habits**

- Measure, don't eyeball. Probe drawn heights with a Node script built from `check_main_landscape.mjs`, with points passed in from a file, and map "ground below high water just outside the tide" to find ledges.
- Do not `pkill -f` a pattern that appears in your own shell command.
- Follow the maps: OS and Goad evidence beat earlier defaults.
- Fundamentals before features.
- Stage explicit paths; never commit the book PDF or the G2G CSV.

**Lessons from Phase V and Abbey Mills (6 October 2026)**

- Water cells at a polygon edge can carry a bank crest (a 2 m cell keeps its highest sample). Catchments must be grown by a minimax priority flood from outlets at their own ground, not by a plain watershed with outlets forced low.
- A regional 10 m cell drawn wet by its lowest 2 m cell speckles shallow sheets. Use the mean ground of its cells in that basin, and a depth bias on the water material.
- The landscape check protects exposed tidal mud: only recorded flood-bank vertices may change it. New raises must take `preserve`.
- Yard tracks must lie inside a yard surface and stay 0.95 m clear of buildings, water and roads (`check_factory_yards.py`).
- Do not `pkill -f` a pattern that appears in your own command (it kills the shell); WSL crashed once mid-task (6 October). Commit WIP on the branch at milestones.

**Lessons from F1 (6 October 2026)**

- The flood grid's modelled ground must read the landscape weight as the page does (bilinear). Read by nearest cell, it left 18 ha of never-wet holes that stood as walls along every bank.
- Where no mesh draws (gaps between the river-network and river-system meshes; Stratford town), the page and the flood grid fall back to the 10 m level field wherever the weight is above 0. Raising the weight there draws sills across channels and lifts streets. Keep the exported weight at 0 in water and outside the marsh outline; widen only the blend weight.
- Swapping files inside the worktree for a baseline check is blocked by the harness. Check the baseline out with `git worktree add --detach <scratch> <commit>` instead, and remove it after.
- `scratchpad/f1/flood_render.py` renders the `?flood` page at set levels (`?river-review=1&flood=1`, the stage slider set through its input event).
