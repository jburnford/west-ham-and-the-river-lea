# Plan: rain, river, mills and tide flooding for the c.1890s model

Handoff plan for a new session, written 5 October 2026. The author asked for the square flood view to be replaced by flooding that comes mainly from rain and shows how the mills and locks dammed the Lower Lea.

Read first:

- `CLAUDE.md`
- `WORKTREE_GUIDE.md`
- `scenes/channelsea-sewer-panorama/OPUS_DELEGATION_PLAN.md`, the open fundamentals
- `TASK_C_REPORT.md` and `TASK_D_REPORT.md`
- the memory notes `flood-model-direction`, `tide-evidence`, `follow-the-maps` and `agent-delegation-lessons`
- `FLOOD_PHASE0_NOTE.md` and `TASK_E_REPORT.md` (task E so far)

## 0. Status, 8 October 2026 (F2 committed): start here

**8 October, later: F3 COMMITTED (the West Ham Chemical Works river wall and the Abbey Mills coal-quay wall; `TASK_E_REPORT.md` "F3"). Branch `task-e-flood-model` is pushed to origin (a branch only: `main` and the live site are untouched; tasks D and E are not merged). Next: Phase 2, the pounds.**

**9 October: task F (core infill, `TASK_F_REPORT.md`) is on branch `task-f-core-buildings`, built on the task E head and checked out in this same worktree. Do Phase 2 on top of it (the buildings change the landscape and flood inputs), or merge it into `task-e-flood-model` first.**

**Phase 2 handoff (start here in a new session).**

- **Where:** worktree `/home/jic823/book_website-taske`, branch `task-e-flood-model`, served with `python3 -m http.server 4211 --bind 127.0.0.1 --directory docs` from the worktree. Show the author renders before committing; commit with explicit paths (never the book PDF, the G2G CSV or `node_modules`), then push the branch when asked.
- **Read first:** section 4.1 (structure register), 4.2 (pound levels from flow), section 5 "Phase 2", section 6 (the author's answers: the mill ponds are held at the last high water while the tide falls, not steady pounds; the Navigation is walled off from the Three Mills pond and holds its level at the Three Mills overfall and the Bow overshoot; in floods gates are drawn and the restricted openings make the head; Lea flow is a slider in m³/s with G2G ticks Q95 2.0, median 4.6, 1894 peak 40.9, running to about 60; default an ordinary day).
- **Inputs:** `data/maps/lea-control-structures.json` (28 structures, 3 not found; openings and sills are estimates to set); the G2G Feildes Weir flows `G2G_Oudin_flow_1891_2015.csv` (86 MB, in the MAIN checkout root, untracked; its date format switches in 1900; true 1891-1910 peak 56.1 on 15 June 1903); the Navigation's normal head about 0.95 scene from the 1928 rises; the tidal limit at Abbey Mill; `tide_levels.RETAINED` (0.06, from `os-tide-levels.json` `retainedLevel`) is the single still datum to replace.
- **What it changes:** the retained water the river network and river system draw (the Old Lea at the back-river heads, the back rivers' regional continuations north of z -941 / west of x -1050 at 0.06 over a bed 2.2 m below, the Channelsea above Abbey Mill, the Navigation), the river network's retained ids, the marsh ditch levels and Phase V's single held river level in `docs/lib/flood-volume.js`. The back rivers above Three Mills become the held mill pond instead of draining with the tide.
- **Plan:** `docs/lib/pounds.js` as a pure function with unit checks first (monotonic in Q; drawn gates lower heads; a tidal tail propagates only to the next structure); then the drawn levels at median flow and working heads; then the full cascade; renders at City Mills, Pudding Mill, Three Mills, Abbey Mill and Bow Locks, each showing a step at its structure. Offer the author the "without the mills and locks" comparison (proposed, not agreed).
- **Cascade:** infrastructure, river_terrain, river_network, historic_elevation, river_system, main_landscape, landscape_flood, factory_yards, drainage_connections, flood_demo, wharf_cranes, lite_meshes, scene_manifest (about 15-25 min; `build_lite_meshes.py` bakes the composed network heights for the phone tier, and `check_river_network_lite.mjs` fails if it is skipped). `build_regional_landscape.py` is NOT in it: whenever the river system is rebuilt, rerun it (about 1 min; `check_regional_landscape.py` pins the river-system hash), then cascade from main_landscape.
- **Checks at the F3 commit:** `npm test` 22/22; Python `check_*.py` 42 pass. The 33 known failures are hash pins (`check_regional_elevation`, `check_lower_lea_region`), frozen snapshots (`*_context`, `check_east_bridge_housing`, `check_east_wharf_yards`, `check_west_sugar_alignment`), the `site256-range-1` alignment checks, `check_gltf` (no exports) and `check_panorama` (needs its own server).
- **Tools:** main checkout `reference/task-e-tools/` (git-ignored; README): cascade.sh, checks.sh, render.py, the ID-colour probe, a ground-sampling probe. One headless browser at a time; kill servers by PID, not `pkill -f` (it kills the calling shell).
- **Still open for the author:** the regional bank faces past the old core edge (steeper than the network's); the North London line's end at x -1700; the colour of the quay strips behind the F3 walls; the Phase V preset rain totals; merging tasks D and E into main and going live.

**8 October: F2, its fixes and the Lee Navigation bridge are COMMITTED on `task-e-flood-model` (author approved); report `TASK_E_REPORT.md` "F2 follow-up". Next: F3 with the coal-quay wall, then Phase 2. Still open for the author: the regional bank faces past the old core edge (below), and the North London line's end at x -1700.** The notes below are the record of the 7-8 October session.

**Session of 7-8 October (F2 fixes).**

- Done, full cascade run (8 Oct), author has seen most of it:
  - Dark mud patch: `river_bank_sections.fields()` tidal mud now only on the shelf (`d<=5`).
  - Tracks buried east of the Waterworks crossing (an F1 effect): `os-ground-levels.json` `stratfordAtGradeRailways` (generated by `prepare_os_ground_levels.py`), clamp "RAIL CUTS" in `build_main_landscape.py`. Formation 3.0 kept (author: the OS is guidance, not a target).
  - Seam at the old core edge: back-river shelf no longer fades at the network edge (`river_bank_sections.py`); `siltedCoreBedCorrections` in `build_river_system.py` (network bank caps in silted water to the shared bed), applied in `docs/river-system.js` and the landscape; network silted water kept wet in `blend_surface`.
  - High tide over the North London bridge decks: `docs/great-eastern.js` no longer draws `northernWater` (a tidal copy at 0.06 rose 3.58 m).
  - Lee Navigation shifted east at the crossing: `crossing-517-518` now `centreline: true` (`data/maps/lower-lea-region/river-system-1900.json`, `end_centre()` in `build_river_system.py`); `nl-hackney-cut` bridge form moved -8.8 m chainage in BOTH `data/maps/railway-bridge-forms.json` and `docs/railway-bridges.js`.
  - North London line raised over the Hackney Cut (author chose): `canalLift` {5.5, holdTo 100, rampTo 400} in `data/maps/north-london-connection.json` and `prepare()`, used by `height()` in `north_london_connection.py`.
- Reverted after checks: a regional 5 m shelf ring plus tidal-face limit in the landscape matched the network's bank heights at the seam, but held OS bank crests up to 1.4 m low (`check_os_ground_levels` failed; Stratford flood banks). Regional banks are back at their OS crests, so the regional bank faces past the old edge are again steeper and higher than the network's (renders `reference/flood-model-f2/f2v6-*`). **Ask the author:** accept that, or lower the network-side limit instead.
- Also tried and reverted: network using the shared bed everywhere / `bed_at` nearest-cell fallback (moved about 700 core vertices, up to 4.5 m).
- **Fixed 8 Oct (shown to the author, not committed): the Lee Navigation under the North London bridge.** `canal_passage()` in `scripts/north_london_connection.py` computes the Hackney Cut passage from Water_1895 pieces 517/518 (the same route as the river system's `crossing-517-518`, 16 m), recorded as `canalPassage` in `data/maps/north-london-connection.json`; `build_north_london_connection` adds it to the openings. The footprint no longer covers the canal; no retaining edges cross it; the line's own `bridges` gained 53.2-74.6, and `bridgeIntervals()` in `docs/railway-bridges.js` (was `addedBridgeIntervals`) merges it with the register's `nl-hackney-cut` (54.0-73.5) so one deck is drawn. Full cascade run. Sheet: main `reference/flood-model-f2/lee-navigation-bridge-before-after.png`.
- Checks after it: `npm test` 22/22 (Hunts Lane sample refreshed, 3 mm). Python: 36 of 75 fail, nearly all hash pins, frozen snapshots and `site256-range-1` alignment checks. Against the pre-F2 head (scratch worktree, which lacks ignored inputs so only some checks compare) two pass there and fail now, both from the F2 work, not the bridge: `check_river_banks` (bed sections must sit 0.35 m under water; the F2 silted beds rise to 0.0 and +0.6) and `check_continuous_structures` (the regional landscape's canal banks, built 5 Oct, overlap the moved `crossing-517-518` passage by 685 m² at about (-1629,-1344); the regional landscape is not in the cascade). Author 8 Oct: fix both. `check_river_banks` now requires silted bed vertices to lie on the registered bed; the regional landscape was rebuilt (`build_regional_landscape.py`) and the cascade run again from the main landscape. 42 Python checks pass, no new failures.
- Checks: `npm test` 21/22. Remaining failure `check_road_bridges.mjs`: Hunts Lane sample moved 3 mm; paste the output of `node scripts/check_road_bridges.mjs --write-sample` into the script's stored sample. Python check set not run this session.
- Then: show the author, commit F2 (explicit paths; never the book PDF or the G2G CSV), F3 with the coal-quay wall, Phase 2.
- Tools (session scratchpad `/tmp/claude-1000/-home-jic823-book-website/c8e77054-…/scratchpad/`, may not survive): `cascade.sh` (`STEPS=` subset), `render.py OUT CAMS stage…` (`PORT`), `probe_server.py` + `probe.py` (ID-colour render). A scratch HEAD worktree `scratchpad/base` (port 4212) may still be registered: `git worktree prune`. **Run one headless browser at a time** (WSL crashed with two).

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

- **F2** (the back-river beds): 7 October 2026. New register `data/maps/back-river-beds.json`: a silted bed rising along the water from -2.2 scene (a low-water stream) at the Three Mills race to 0.0 (1.84 m ODN) shoals at the heads where the rivers leave the Old Lea and the Navigation; the Pudding Mill River 0.6 m above that, dry at low tide (author). A low-water stream a foot deep runs down the other back rivers from the heads (author: 'the water is coming from both directions'): its own still mesh `river-network.stream.*`; the scene draws the higher of it and the tide. All estimates. Drawn by `build_river_network.py` (`section()`, `river-network.json` `backRiverBeds`); road-bridge spans over the back rivers clear to the silted bed (`main-landscape-1900.json` `roadBridgeClearance.spanLevels`). `TASK_E_REPORT.md` "F2".

**F2 handoff (7 October 2026, evening). Built, checked, NOT committed; the author approved the look ("looking great") but has not said "commit".**

- **State of the worktree:** everything is uncommitted on `task-e-flood-model` (41 changed or new files; `git status`). The cascade was run in full after the last change. `npm test` 22/22, `check_river_tides.py`, `check_core_river_connections.py`, `check_main_landscape.py`, `check_river_system.py`, `check_landscape_flood.py` and `check_factory_yards.py` pass. The full Python check set was last compared before the move of the heads: no new failures against the branch head.
- **What F2 now is** (details in `TASK_E_REPORT.md` "F2"):
  - register `data/maps/back-river-beds.json`;
  - shared module `scripts/back_river_profile.py`, read by both `build_river_network.py` and `build_river_system.py`;
  - silted V-shaped beds rising from -2.2 scene at the Three Mills race to 0.0 at the heads where the rivers leave the Old Lea (Waterworks (-1226, -1270), City Mill (-1251, -1142), Pudding Mill (-1401, -914)) and the Navigation (Bow Back, (-1050, 72));
  - the Pudding Mill River 0.6 m higher and dry at low tide;
  - a low-water stream 0.3 m deep down the others (`river-network.stream.*`, drawn still by `docs/river-network.js` `lowWaterStream`; the scene shows the higher of the stream and the tide);
  - the regional back-river reaches are tidal.
- **Open, being checked when the session ended:** the author saw "something funny happening in the north with the branch line and the river crossings": the North London connection (`infrastructure.json` railway `north-london-connection`) where it crosses the Waterworks River (Lower_River_Lea-5) and the Old Lea (Lower_River_Lea-15) at about (-1225..-1261, -1363..-1375), about 90 m north of the new Waterworks head. The author's screenshot shows the tracks sinking into the ground south of the river, a pale strip, and jagged light edges along the water.
  - Compare against the before-F2 tree: renders `scratchpad/f2/v6` (after) and `b6` (before) with `cams6.json`. Port 4212 serves the branch head before F2 from the scratch worktree `scratchpad/f2/base` (`git worktree add --detach`; remove it with `git worktree remove` when done).
  - **Rendered before the session ended: F2 caused it.** `reference/flood-model-f2/f2v5-north-london-crossing-before-after.png` (main checkout; left before, right after; cameras in `cams6.json`: `nl-crossing-south` [-1200, 40, -1130] → [-1245, 0, -1380], `nl-crossing-close` [-1215, 15, -1300] → [-1240, 0, -1375]). After F2 a large dark mud-coloured patch lies on dry land east of the Waterworks River near its head, and a dark band runs beside that channel; before F2 it was grass. So the silted bed or its mud colour reaches land outside the water there. First suspects: the network's land override in `section()` (`bed=back.bed_at(...)`, which also sets `sediment=1`), `back_river_profile.Profile.geometry` (closing buffer, the regional reach 4 rebuilt with the network channel in its box), and the bank `mud`/`bed_edge` in `river_bank_sections.fields()`. Measure which mesh the dark vertices belong to (network, system or landscape) before changing anything.
  - Other suspects for the tracks: the river system's `railwayGroundAdjustments` (it adjusts ground under that railway), the new bed rings in `river_bank_sections.py`, or the reaches turned tidal. If the before render shows the same, it predates F2 and is a separate fix.
- **Then:** show the author, commit F2 (explicit paths; never the book PDF or the G2G CSV), then F3 with the coal-quay wall, then Phase 2 (the Old Lea at the heads is still regional still water at 0.06, so at high water the back rivers' tide stands above it at the junctions).
- **Tools left in the session scratchpad** (`/tmp/claude-1000/-home-jic823-book-website/1d5564dc-…/scratchpad/f2/`, may not survive): `cascade.sh` (full cascade; `STEPS=` to start later), `render.py` (renders on port `PORT`, cameras from `CAMS`, tide stages low/high/percent), `pychecks.sh` (all Python checks to a file), `beds.py`. Sheets for the author are in the main checkout's `reference/flood-model-f2/` (git-ignored).
- **The author's wider question (7 October):** the seams between the detailed and regional parts of the model should be extended across the project; eventually Silvertown, the Royal Docks and Canning Town, then the rest of West Ham and the Lower Lea Valley. Not started. The F2 pattern (facts in a register, one shared module that both meshes call, so the extent of a detailed mesh is only its level of detail) is the proposed way; an inventory of the seams (every place two builders or zones meet and what each does differently) is the first step.

**Open questions for the author.**

- F1: the Channelsea head closures (inferred, not lettered); trimming the 2 m network-join ring (+1.8 MB).
- Phase V: the preset rain totals (placeholders); the "without the mills and locks" comparison for Phase 2.
- F2: the revised profile (outlet, head and the Pudding Mill offset).
- Going live: merging and pushing tasks D and E.

**Next, in this order (author, 7 October 2026):**

1. ~~F2~~ done.
2. **F3 with the coal-quay wall.** The works wall face and the Abbey Mills coal quay wall both go into `data/maps/os-river-walls.json`, in one cascade.
   - The quay wall: the OS double line on the Channelsea west bank from the sewer bridge south past the quay; see `abbey-mills-coal.json` `unloading`.
3. **Phase 2** (pounds). It replaces Phase V's single held river level, which acts only on water outside the tide polygons. Then Phases 3-5.
   - The back rivers' regional continuations (north of z -941, west of x -1050) still draw still water at 0.06 over a bed 2.2 m below it; give them their pound levels and silted beds then.

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
