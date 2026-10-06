# Plan: rain, river, mills and tide flooding for the c.1890s model

Handoff plan for a new session, written 5 October 2026. The author asked for the square flood view to be replaced by flooding that comes mainly from rain and shows how the mills and locks dammed the Lower Lea.

Read first:

- `CLAUDE.md`
- `WORKTREE_GUIDE.md`
- `scenes/channelsea-sewer-panorama/OPUS_DELEGATION_PLAN.md`, the open fundamentals
- `TASK_C_REPORT.md` and `TASK_D_REPORT.md`
- the memory notes `flood-model-direction`, `tide-evidence`, `follow-the-maps` and `agent-delegation-lessons`

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

## 5. Phases and acceptance criteria

**Phase 0: evidence and register (author checkpoint before any modelling).**

- Read the book chapters on the mills, the Lea and flooding in full (start with chapters 1 and 6). Note what the text establishes about heads, gate operation, millers' and navigation disputes, and the 1809, 1888 and later floods, with page numbers.
- Survey the OS five-foot mosaic (`scripts/factory_map_sources.py` `mosaic`) at every control, with crops.
- Draft `lea-control-structures.json`: every number marked "estimate" or "mapped", with its method.
- **Deliverable:** the register, crops, and a short note listing every estimate. **Stop for the author's review.**

**Phase 1: whole-model flood grid.**

- New builder replacing `build_landscape_flood.py`: whole extent, finer core cells, per-source connection levels.
- Old behaviour reproduced for the tidal source. Compare connected land at 1.9, 2.5, 3.5, 4.5 and 5.5 m ODN with the current figures, which are 0 / 0.03 / 51.09 / 105.63 / 114.47 ha in the old box after task D.
- No straight edges at the old box; no water on ground above its level; checks updated (`check_landscape_flood.py`).

**Phase 2: pounds.**

- `docs/lib/pounds.js` with unit checks.
- The non-tidal reaches move off the single 0.06 datum to their pound levels at median flow and working heads. This changes the drawn retained water, the river network's retained ids and the marsh ditch levels, so plan the cascade.
- Renders: City Mills, Pudding Mill, Three Mills, Abbey Mill and Bow Locks, each showing a visible step at its structure.

**Phase 3: rain.**

- Fill and spill with outfalls and tide-locking.
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
