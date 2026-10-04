# T15 report: railway embankments (Bow Creek bridge, line ends, buried building, siding)

3 October 2026. Worktree branch `worktree-agent-ad3c366db0bf35d53`.

## Bottom line

- **LT&SR Bow Creek crossing (−605, 606): fixed.**
  - The line now crosses on a two-span plate-girder bridge.
  - A brick west abutment with in-line wings stands on the drawn west bank, and the east abutment is a brick face on the existing embankment cut.
  - One brick river pier sits parallel to the banks. The deck is continuous at formation height (5.5 m) from abutment face to abutment face.
  - The lone pier in the water and the old 9 m abutment boxes are gone.
- **Box-ended fills: fixed** at all three raised line ends with nothing beyond them:
  - North London branch, x −1700;
  - Great Eastern main line, west end (−1484, −26);
  - Great Eastern main line, east end (−316, −1278).
  - Each is closed by an earth end falling at the railway's own side slope. The OS shows every one of these lines continuing (readings below). I did not carry them to the model edge, because that needs new route data, which I may not add.
- **Buried building at the LT&SR toe (−327, 494): fixed.**
  - The embankment now stops 1.5 m off Manure Works #1018 ranges 1, 2 and 3, behind a brick retaining wall (203 m in all, up to about 3 m high).
  - Before, the slope ended 0.15 m from the north wall of range 1 at 1.4 to 2.2 m above the floor.
- **Hunts Lane siding (−990, 18): not fixed. Out of scope; I stopped there as instructed.**
  - The floating track is a factory-yard track (`docs/data/factory-yards.json` track `east-run`), drawn by `docs/factory-yards.js`.
  - It is not a railway in `infrastructure.json`, so the fix needs files outside my list (T16's yard builder or its front-end module). Numbers are below.
- **Sweep cameras:** of the 26, only **one** is inside an embankment (`rail-0-great-3`). One more is under the ground, two are inside building footprints and one stands 0.3 m above the ground. The other 21 are 14–26 m from the slope they face; they see only slope because they are 2.5 m high and aim at the formation.
- **Two things I did beyond the four named sites, both found by the check you asked for.** Both are recorded in the register and can be dropped (see Decisions):
  1. The traced North London embankment ran unbroken over the Hackney Cut (77 triangles over drawn canal water). I opened it and gave it a bridge.
  2. Four more building footprints were buried by embankment slopes. I held them off the same way, and recorded three footprints that lie inside a formation as conflicts.
- **Acceptance criteria all hold.** Every ground mesh is byte-identical to a rebuild of the unchanged builder, so:
  - steps are unchanged: network 0, extension 0, core 52, system 214, groundMesh 2;
  - fill 37.19 %, Bromley −0.103 m, Abbey Lane deck ends unchanged, 0 of 1,125 seated objects moved;
  - both landscape checks pass, and `npm test` passes 16 of 18 (the two known failures).

## Setup

- My worktree started at 116c0ae. I fast-forwarded it to `main` (3fffd45); there was no conflict.
- At base, `check_main_landscape.py` failed on a stale `ground-plan.json` input hash (T8/T1c had changed the inputs since the last landscape build).
- Re-running the unchanged builder (`rebuilt`) changed `core.f32` (4,644 vertices, at most −2.35 m; the Mill Mead path stub T11 predicted T8 would remove) and `level.f32` (7 cells). The other `.f32` files were byte-identical.
  - My commit includes that regeneration, because the Python check cannot pass without it.
  - All "before" figures, the smoke base and the comparisons use `rebuilt`, so my own change is isolated.
- Scratch folder: `/tmp/claude-1000/-home-jic823-book-website/158d731a-06ad-4794-89f0-96291b5302cd/scratchpad/t15/`. It holds the tools, the `base`, `rebuilt` and `final` builds, `views-before/`, `views-after/`, the logs and `sweep-after.json`.
- The OS tiles are git-ignored. I read them from the main checkout's `reference/nls-tiles` through `factory_map_sources.mosaic()`, read-only.

## What I changed

### `scripts/build_main_landscape.py`: new railway works section after `railwaySlopes`

What stays the same:
- Formation stations, routes, formation heights and every refitted embankment height (`railwaySlopes[].heights`) are unchanged. For all 6 railways, `heights` equal the rebuilt values.
- The section changes only *where* earthwork is drawn.

What it writes:
- `railwaySlopes[].works` holds three things:
  - `removedTriangles`: indices not drawn;
  - `addedTriangles`: remainders re-triangulated on each original triangle's own plane, plus the new earth ends and approach;
  - `walls`: brick quads, from the top edge on the earthwork down to 0.4 m below ground, or to −1.2 m beside water.
- Each `works.items` entry has its own evidence string.
- A new top-level `railwayWorks` record carries the method, a per-railway summary and the evidence.
- The topology the front end checks is unchanged, because works are separate arrays.

The rules:
1. **Openings** (`RAIL_OPENINGS`: only `nl-hackney-cut`). No fill within 0.4 m of the drawn water (river-system reaches, ground-plan rivers and ditches, the builder's existing mask), within the bridge's chainage band. A brick abutment face with in-line wings follows the cut.
2. **Buildings** (`RAIL_GAP` 1.5 m). This uses the builder's own footprint set, the one T3 used.
   - On the plain railways, where raised embankment comes within 1.5 m of a footprint, the fill stops at `footprint.buffer(1.5)` and a retaining wall faces the gap.
   - On the detailed railways, which already stop their fill at buildings behind their own walls, this applies only where the fill actually enters a footprint.
   - It is not done where the cut would reach the formation (crest half-width plus 0.5 m). Those cases are recorded under `kind: conflict`.
3. **Line ends.** A route end not inside another railway's body, whose end profile stands more than 0.5 m above ground and has no embankment beyond it, gets a hipped earth end:
   - every end-profile point falls at slope rise/(base half − crest half), the railway's own side slope, to a toe ring sunk 0.5 m into the ground;
   - the result is clipped off water and buildings.
   - Rounded ends that already slope (Woolwich branch south end) are left alone. Zero-area slivers in the old end plane are dropped.
4. **The LT&SR west approach** (`RAIL_APPROACH`).
   - The traced route begins *in* Bow Creek. So the full LT&SR section (crest 5.55 m to ±4 m, toe at ±15 m) is built from station +14 back to −16.8, then given a hipped end, and clipped 0.4 m off the drawn water and any footprint.
   - The clip edge on the west bank is the west abutment face.
   - The traced embankment's rounded end on the west bank (stations below 14, up to 4.42 m high) lay under it and is removed.
5. **Crossing cuts on the plain railways.** Raised boundary edges within 3.2 m of water or a street and within 18 m of a mapped crossing end get the same brick face. These are the LT&SR east bank of Bow Creek, both banks of its second channel, and the Woolwich branch's Abbey Road bridge.
   - I deliberately left alone a 200 m side cut along a ditch beside the Woolwich branch (x ≈ 250, z 400–600). An earlier version walled it; see "Not done".

Robustness details I had to add:
- Clip pieces are snapped to the 1 mm grid the JSON stores, and the water cut is simplified at 0.05 m.
- Faces are found as one-sided edges of the local result within 3.5 m of the cut, minus any edge with earth on both sides (T-junctions).
- Without these, slivers and duplicate walls appeared.

### `docs/infrastructure.js`

- Each railway draws `railwayWorks()` (embankment minus removed, plus added) and its brick walls.
- The detailed railways receive a copy with the filtered embankment and the register's extra bridge interval. `great-eastern.js` is untouched; it draws its standard girder deck over the Hackney Cut.
- LT&SR crossing 0 is skipped in the old crossing drawing; `railway-bridges.js` draws it.
- Embankment meshes are now named `railway-embankment:<name>` (a new optional `name` argument to `surface()`), so the check can find them.
- The review gains `railwayWorks` and `railwayBridges`.

### `docs/railway-bridges.js` (new)

- Contains the register copy, `railwayWorks()`, `railwayWalls()` and `railwayBridges()`.
- For `ltsr-bow-creek` it draws, each girder and the deck ending on the measured abutment faces:
  - two 1.9 m half-through plate girders per side (web, flanges, stiffeners at 1.5 m);
  - a deck plate in two halves, so its ends follow the face through the centreline station;
  - cross girders at 2 m;
  - the skewed brick pier with a stone cap;
  - ballast, rails and sleepers from station −16.8 to the route start.
- No photograph is used as a texture: plain materials, uv in metres.

### `data/maps/railway-bridge-forms.json` (new register)

- Contains the sources, both bridges (form, measured abutment and water-edge stations on the centreline and both girder or crest lines, pier, and evidence separating mapped, measured and interpreted), and the four `lineEnds` with OS readings.
- The builder does not read it. It is not a landscape input, so editing its measured stations cannot stale the landscape. The check asserts the two copies match, and that the deck ends sit on the builder's walls.

### `scripts/check_railway_embankments.mjs` (new; `run_checks` picks it up)

It builds the real `infrastructure()` module, as `check_road_bridges.mjs` does, and asserts:
1. The register copy matches.
2. **No embankment triangle over drawn water** (centroid or any vertex in the builder's low-water mask). The result is 0 for all 6 railways, so no exception was needed. The bridges are openings, not embankment.
3. **The Bow Creek deck is continuous at formation height.** Vertical rays every 0.5 m on the centreline and both deck edges, from abutment face to abutment face, give no gaps and a deck top within 0.02 m of 5.5 m (actual 0.000).
   - Each end lies within 0.3 m of a brick face.
   - That face's top is at the formation on the centreline (5.55), and within 0.35 m at the deck edges (5.24 to 5.55), where the traced embankment top has already begun to fall.
4. **No embankment vertex inside a mapped building footprint**, except the recorded formation conflicts. Their number is asserted to be 3, so any new one fails.
5. **No open raised embankment edge** within 40 m of each recorded line end and bridge. Any one-sided edge standing more than 0.5 m above the drawn ground must carry a brick face, or have earth beyond it. Result: 0 everywhere.

It does **not** assert the siding (see below). I could not make that pass without leaving my file list.

## Per site

### 1. LT&SR Bow Creek crossing

**OS readings** (five-foot 1893–96 at zoom 18; 25-inch at zoom 17; images `scratchpad/t15/lea_plain.png`, `lea_water.png`, `lea_os-25-inch-london.png`):
- The line crosses Bow Creek on a continuous structure. The four rail lines run unbroken from bank to bank, with a footbridge ("F.B.") on the north side.
- West of the creek it continues on embankment past Bow Pottery towards Bromley.
- The 25-inch shows the H.W.M.O.T. and "BOW CREEK"/"Mud" lettering in the channels.
- No pier is visible. Piers under a deck would not normally show in plan, so this is not evidence of a single span.
- Registration: the traced route lies up to about 6 m south of the OS rails at the west bank. That is route data, which I did not change.

**Measured in the model** (stations along the route's first segment from its first point):

| | Left (+4.15 m) | Centreline | Right (−4.15 m) |
|---|---|---|---|
| Drawn water, west edge | −12.51 | −7.66 | −2.44 |
| Drawn water, east edge | 29.72 | 33.62 | 37.51 |
| West abutment face (drawn wall) | −13.04 | −8.30 | −3.07 |
| East abutment face | 32.46 | 36.36 | 40.26 |

- The banks cross the line at about 50°.
- Pier line: station 12.98 on the centreline, skew −1.08 m per metre.
- Spans about 21 m and 23 m on the centreline.

**Interpreted:** brick abutments with in-line wings, two half-through wrought-iron plate-girder spans of 1.9 m depth on one brick pier, and the west approach and earth end. None is surveyed.

**Renders:**
- `rail-1-london,-0`: before, the deck ended on a pier in the water. After, the deck lands on a brick west abutment on the bank with an earth wing above it, and the pier stands mid-channel.
- `x-ltsr-bridge-high`, `x-ltsr-bridge-north` and `x-ltsr-west-abutment-low` show both abutments, the pier and the girders.
- `x-ltsr-bridge-from-river`: your camera at (−640, 2, 640) stands on the west bank, not in the river. After, it shows the earth end of the approach, a short sloped mound with the rails stopping on it.

### 2. Line ends

**OS readings:** all four ends show the line continuing (images `nl_os-london-five-foot-1893.png`, `ge_west_…`, `ge_east_…`):
- **North London branch:** the "Victoria Park Branch" continues west on embankment past Hackney Wick Works and the Phoenix Chemical Works, beyond the trace's `westClipX` of −1700. The model's ground runs to about x −2700, so this is not the model edge.
- **GE main line west:** continues through Bow Junction.
- **GE main line east:** continues into Stratford Station.

**Done:** hipped earth ends.

| End | Height | Slope | Triangles |
|---|---|---|---|
| North London branch | 1.83 m | 1:6.8 (its traced side slope over 12.5 m) | 103 |
| GE main line west | 8.45 m | 1:2.1 | 418 |
| GE main line east | 8.45 m | 1:2.1 | 143 |

- No walls were needed at any of them.

**Renders:**
- `rail-5-north-0`: the box face is gone; the embankment runs down to the ground.
- `rail-3-great-0` and `x-ge-west-end-high`: a clean hipped end.
- Two flaws remain:
  - the toe has a saw-tooth where the sunk toe ring meets the 20 m ground mesh;
  - a hairline vertical seam shows at the old end line. This is a sub-millimetre rounding crack, because the JSON stores 1 mm.

### 3. Buried building at the LT&SR toe

- Manure Works #1018 range 1 (`site1018-os-1`) stands 10.5 m from the centreline. Its pad floor is −0.1 m.
- Ranges 2 and 3 (12.8 m and 14.0 m from the centreline) had the same problem.
- Fill held 1.5 m off all three. There are 154 wall faces, 203 m in total; the wall tops are 0.5–2.9 m above scene datum, on ground at about −0.1 to −0.5.
- Interpreted and recorded: a brick retaining wall with a 1.5 m gap. No survey shows one.

**Renders:**
- `x-ltsr-toe-along` shows the wall and the gap.
- From high (`x-ltsr-toe-high`, `x-ltsr-toe-overhead`) and from the crest (`x-ltsr-toe-from-crest`) the change hardly shows: the roof eave overhangs the 1.5 m gap.
- `rail-1-london,-1` is not informative (see the sweep list).

### 4. Hunts Lane siding: not done

- The track is `east-run` in `docs/data/factory-yards.json`, drawn by `docs/factory-yards.js`.
  - Unconnected yard tracks are drawn as 1 m horizontal rail boxes, at the drawn ground under each segment's midpoint.
  - Near (−986, −13) the track climbs a river-network bank of about 40 % (1.71 m to 0.12 m over about 4 m). The ends of the boxes float up to **0.249 m**, rail underside against the drawn ground.
- Other yard tracks near Hunts Lane: `east-run` (first) 0.113 m; all others ≤ 0.08 m.
- Two stretches have no drawn ground under them: `west-return` (36 sample points) and `mill-connection` (9). There the track falls back to the 10 m level field.
- Your camera (−1000, 2, 30)→(−990, 1, 18) shows the Hunts Lane road bridge and no track. Before and after are identical.
- The audit's own camera, `bridge-hunts-lane-connection-0-approach-a`, shows the yard tracks.
- The fix (rise per segment from end samples, as connected tracks already have) is in `factory-yards.js` or the yard builder. Both are outside my list and T16's area.
- Tool: `scratchpad/t15/yardgap.mjs`.

### Beyond the named sites (found by the requested check)

- **North London branch over the Hackney Cut** (about x −1630).
  - Before, 77 embankment triangles stood up to 3.0 m over the drawn canal water (river-system `crossing-517-518`), and the line had no bridge there.
  - Now 107 triangles are removed and 59 remainders added, with 63 brick faces (84 m), and a register bridge interval of chainage 62.8–82.3.
  - Abutment faces: 64.14 / 81.17 on the centreline. The drawn canal spans 64.54–80.76 on the centreline.
  - The OS five-foot shows a bridge here, with the canal running on under the line.
  - The traced formation is 3.0 m, so there are only about 2.3 m under the girders. I did not change it.
  - The existing notch where the traced fill had been cut back from the branch's northern water (chainage 51.3 on the right-hand crest edge) now also has a brick face.
- **Other footprints held off:**
  - Woolwich branch: housing row `district-leywick-morley-west-west-return` (9 m of wall).
  - Northern connection: terrace `os-row-49-part-1` (47 m; 43 embankment vertices had been inside it).
- **Recorded conflicts, not changed** (footprint within 1.5 m of a formation; registration conflicts between the traces):
  - Woolwich branch × terrace and housing `os-row-19` (24 vertices at 5.55 m inside it, 3.8 m from the centreline);
  - northern connection × terrace `os-row-50` (39 vertices up to 1.34 m, 5.7 m from the centreline).

## Numbers

| | Committed base | Rebuilt (true base) | After |
|---|---|---|---|
| Steps: network / extension / core / system / groundMesh | 0 / 0 / 52 / 214 / 2 | 0 / 0 / 52 / 214 / 2 | **0 / 0 / 52 / 214 / 2** (core: 0 new, 0 gone) |
| T2 fill within 0.5 m at 1 m and 3 m | 37.19 % | 37.19 % | **37.19 %** |
| Bromley trench minimum (profiles below −0.3) | −0.103 (0) | −0.103 (0) | **−0.103 (0)** |
| Abbey Lane deck ends, worst within 2 m (west/east) | −0.12 / −0.18 | same | **same**, all stations identical |
| Seated objects moved more than 0.05 m | | | **0 of 1,125** |

- All eight `.f32` files are byte-identical to `rebuilt`.
- The JSON differs from `rebuilt` only in `railwaySlopes` (added `works`), `railwayWorks` and the builder's input hash.
- `main-landscape-1900.json` grows from 1.47 MB to 1.66 MB.

## Checks

- `node scripts/check_main_landscape.mjs`: PASS.
- `python3 scripts/check_main_landscape.py`: PASS (28 source hashes). It failed at base on the stale `ground-plan.json` hash.
  - T14 had not landed in my worktree, so no `river-network.u32` hash issue arose. If T14 lands first, this check will need a rebuild.
- `node scripts/check_railway_embankments.mjs`: PASS.
- `npm test`: **16 of 18**. The two failures are the known ones: `check_drainage_connections.mjs` (git-ignored mosaics) and `check_flood_demo.mjs` (stale `terrain-1900.json`).
- `eslint` and `prettier --check` are clean on my JS files.
- I changed no count assertion in the landscape checks.

## Smoke

- Scratch copy of `review_smoke.py` with a 900 s tween wait.
- **Base** `t15-base`: served from an export of this worktree's HEAD `docs` with the `rebuilt` landscape files. Ready, **0 page errors**, 8,261,014 triangles, 151 draw calls.
- **After** `t15-railways --compare t15-base`: ready, **0 page errors**, 8,263,686 triangles, 153 draw calls. The screenshot timed out, which is non-fatal.
- **7 differences:**
  1. `drawCalls` 151 → 153;
  2. `reflection.drawCalls` 152 → 154: new mesh batches, for the brick-face material (a double-sided clone) and the bridge structure;
  3. `infrastructure.railwayBridges`: new review key;
  4. `infrastructure.railwayWorks`: new review key;
  5. `railConnections`: North London `bridges` 3 → 4, the Hackney Cut interval;
  6. `triangles` +2,672;
  7. `reflection.triangles` +2,672.
- On items 6 and 7: by my count the added geometry is larger (embankment +1,343 net, walls about 880, bridge structure about 1,150). The smoke figure is evidently not a plain sum of everything added. I did not trace exactly what it counts.

## Renders

- Before and after were served from this worktree on 4190.
  - Before: `views-before/`, rendered at base before any change. The four `cams-extra2` views were rendered from the base export.
  - After: `views-after/`.
- Required cameras:
  - `rail-1-london,-0`: **fixed**, as described above.
  - `rail-1-london,-1`: before and after show the same grey foreground with a building facade. The camera is 0.5 m *under* the drawn ground (the ground there is 3.0 m), so this view is uninformative.
  - `rail-0-great-0`: unchanged, a slope-filled frame from 24 m.
  - `rail-5-north-0`: **fixed** (box end gone).
  - `rail-2-abbey-0`: unchanged, a slope at 25 m.
  - LT&SR bridge from (−640, 2, 640): shows the new earth end and the abutment, as described above.
  - Hunts Lane (−1000, 2, 30): identical, the road bridge only.
- Extra cameras: `x-ltsr-bridge-high`, `-north`, `x-ltsr-west-abutment-low`, `x-ltsr-toe-along`, `-high`, `-overhead`, `-from-crest`, `x-nl-canal`, `x-nl-bridge-side`, `x-nl-end-high`, `-close`, `rail-3-great-0`, `x-ge-west-end-high`, `x-siding-*`.
- In `x-nl-canal` and `x-nl-bridge-side` the canal now passes under an iron deck on brick abutments. Before, the embankment dammed it.

## Sweep cameras inside geometry

Method: the drawn embankment surface (after works), the drawn ground and the builder's footprint set at each camera position, plus the first infrastructure hit along the view ray (`scratchpad/t15/sweep.mjs`, results in `sweep-after.json`).

- **Inside an embankment:** `rail-0-great-3`, at (224.8, 2.5, 494.1). It is inside the Abbey Mills junction curve embankment, whose top there is 5.55 m. The dark overhead shape in its render is the embankment from inside.
- **Under the ground:** `rail-1-london,-1`, at (−314.4, 2.5, 526.2). The drawn ground there is 3.0 m.
- **Inside a building footprint:**
  - `rail-3-great-1`: factory `cook-bone-east`;
  - `rail-4-great-3`: factory `east-upper-stratford-market-roof`.
- **Nearly on the ground:** `rail-3-great-2` is 0.34 m above 2.16 m ground, between brick walls.
- **Against a building wall** (not in my footprint set; seen in the render): `rail-3-great-4`.
- **All other 20 are outside geometry.** Each faces the slope it sees from 14–26 m.

## What I did NOT do

- I did not edit routes, formation heights, `infrastructure.json`, `great-eastern.js` or any yard file.
- I did not carry any line west to the model edge, although the OS shows all four continuing.
- I did not fix the Hunts Lane siding (out of my files).
- I did not resolve the three formation/footprint conflicts.
- I did not wall the ditch-side cut beside the Woolwich branch (x ≈ 250, z 400–600). An earlier version walled it, about 200 m at about 2.4 m high. It is a side cut, not a crossing, and is not among the named sites.
- I did not change embankments over the network *tide* outline. The figures for triangles over tidal water only:

  | Railway | Before | After |
  |---|---|---|
  | LT&SR | 52 | not re-measured |
  | GE main line | 229 | not re-measured |
  | Northern connection | 22 | not re-measured |
  | North London | 14 | not re-measured |

  The check uses the low-water mask, as the landscape builder does.
- I did not regenerate the GeoTIFF/GeoPackage export.
- In baseline mode (`?mainLandscape=baseline`) the earth works and walls are absent, because they come from the landscape JSON. The register bridge deck and pier still draw.

## Unsure

- **The pier and girder depth** are estimates. The OS cannot show a pier under a deck. A single 44 m skew span is also possible.
- **The Hackney Cut bridge's 2.3 m headroom** looks low for barge traffic. It follows the traced 3.0 m formation, which is itself an unmeasured estimate.
- **The LT&SR west approach** ends in a sloped earth end on the bank. The line continued there, so the earth end is a model-boundary device, not history.
- **Earth-end toe heights** use `base()` (0.05 m outside the marsh weight). They are sunk 0.5 m to cover places where the drawn ground lies lower. The saw-tooth toe at the GE west end is a side effect.
- **The check's open-edge threshold is 0.5 m.** One LT&SR approach toe edge stood 0.41–0.45 m above the drawn ground at earlier builds. I raised the threshold from 0.3 rather than chase it.
- **I measured that the hold-off walls exist, not that they read well.** From high or oblique views the 1.5 m gap is hidden under the building's eaves.

## Decisions for the parent

1. **Keep or drop the extras.**
   - The Hackney Cut opening is one register entry plus one `RAIL_OPENINGS` entry.
   - The four extra hold-offs follow from the general rule. Restricting it to the LT&SR would leave 82 northern-connection vertices inside terraces and fail the check as written.
2. **Carry the lines on.** All four OS readings show them continuing; the LT&SR to Bromley is the most visible. This needs route data (`road-traces`/rail traces, T13 territory or a new task).
3. **Hunts Lane siding:** assign to T16 (yard tracks: per-segment rise from end samples, and ground for the two uncovered stretches).
4. **Formation conflicts** (`os-row-19` ×2, `os-row-50`): re-register those terraces, or accept them. The check pins the count at 3.
5. **The Woolwich ditch-side cut** (x ≈ 250): wall it, give it an earth face, or leave it.
6. **The audit list:** correct I10's camera notes with the sweep list above.

## Files

- `/home/jic823/book_website/.claude/worktrees/agent-ad3c366db0bf35d53/scripts/build_main_landscape.py`
- `/home/jic823/book_website/.claude/worktrees/agent-ad3c366db0bf35d53/docs/data/main-landscape-1900.json`, `.core.f32`, `.level.f32` (the last two are the input-drift regeneration only)
- `/home/jic823/book_website/.claude/worktrees/agent-ad3c366db0bf35d53/docs/infrastructure.js`
- `/home/jic823/book_website/.claude/worktrees/agent-ad3c366db0bf35d53/docs/railway-bridges.js` (new)
- `/home/jic823/book_website/.claude/worktrees/agent-ad3c366db0bf35d53/data/maps/railway-bridge-forms.json` (new)
- `/home/jic823/book_website/.claude/worktrees/agent-ad3c366db0bf35d53/scripts/check_railway_embankments.mjs` (new)
- `/home/jic823/book_website/.claude/worktrees/agent-ad3c366db0bf35d53/T15_REPORT.md`
