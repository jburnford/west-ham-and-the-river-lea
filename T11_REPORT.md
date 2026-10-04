# T11 report: path corridors on the ground, and the network tidal outline in the water mask

3 October 2026. Worktree branch `worktree-agent-a7a03fc7860a54619`.

## Bottom line

- **A (path causeway): the causeway is gone, but the 95 % acceptance figure is not met.**
  - The Mill Mead riverbank path no longer stands on a 2.19 m strip. Its ground is now whatever the marsh, the bank band and the wall fill make it. The 2.4 m cliff where the street reading's 120 m reach ended (z ≈ 72) is gone.
  - Using 1.5 m either side as "adjacent ground", the drawn surface is within 0.15 m on 82.1 % of the 2 m stations. It was 85.5 % before. The target is 95 %.
  - 25 of the 31 failing stations are where the mapped route climbs obliquely up and down the inland slope of the regional 14 m bank band (z 20–64), which lifts the ground to the 3.4 m crest. On a cross slope, ground 1.5 m either side always differs from the path by more than 0.15 m.
  - The before figure passes only because the old 8 m wide flat corridor made "adjacent ground" equal the causeway top.
- **B (tidal outline):**
  - Inside the network tide outline, the bank blend and the batters now raise no vertex, except within 5 m of a mapped building footprint. That exception was needed to avoid new steps (see Decision 1).
  - The Old Lea fin vertex (−1051, −618) is back to 0.62 m, its pre-blend height. It was 2.31 m.
  - The Bow Locks saw-tooth is **not** cured. It is in the raw river-network mesh: a 1 m raster staircase of the bank line. Vertex evidence is below.
- **Other acceptance criteria all hold:**
  - No step count rose: core went down from 106 to 52; the others are unchanged.
  - T2 wall fill is unchanged at 37.19 %.
  - Bromley trench minimum is unchanged at −0.10 m.
  - Abbey Lane deck ends are unchanged.
  - Seating is unchanged: 0 of 1,125 objects moved more than 0.05 m.
  - The sewer bank toes near the path are unchanged.
  - Both landscape checks pass, and `npm test` passes 13 of 15 (the two known failures).

## Setup

- My worktree started at 116c0ae, behind `main`, with no local changes. I fast-forwarded it to `main` (6ab7ef6, which includes "Merge T3 …") before starting.
- Running the unchanged builder reproduced the committed `.f32` files byte for byte. I used them as "base" for every before figure, render and smoke snapshot.
- Scratch folder: `/tmp/claude-1000/-home-jic823-book-website/158d731a-06ad-4794-89f0-96291b5302cd/scratchpad/t11/`. It holds the tools, builds `v1`–`v4`, the renders and the logs.

## What I changed

Only `scripts/build_main_landscape.py`, plus the regenerated `docs/data/main-landscape-1900.json`, `.core.f32`, `.network.f32` and `.level.f32`. The `background`, `extension`, `system`, `faces` and `weight` files are byte-identical to before. I changed no check script and no count assertion.

### A. Path corridors (`kind == 'path'`)

**Cause.** The Mill Mead riverbank path was a street-reading corridor. Its single reading, `sh_538874_183253` (2.19 m), is the Abbey Road / Abbey Lane spot height by the Abbey Mill bridge, not a level on the path.
- `road_fit_levels` spread that reading over the 4 m half-width corridor for the first 120 m of the path. `edge_batter` then battered the corridor sides at 1:1.5.
- No other path has street readings, so no other path was affected.

**Change.**
- A path corridor is no longer a street corridor. It takes no level of its own, raises no batter of its own, and no longer blocks neighbouring batters or wall fill.
- Its ground is whatever the marsh, the bank band, pads and wall fill make it. `docs/infrastructure.js` already draws path triangles 0.05 m above the ground, and that is the "few centimetres of made-up surface".
- Streets, lanes and roads are untouched.
- **One exception.** Inside the Northern Outfall Sewer embankment footprint (sewer bank and crest triangles from `infrastructure.json`, plus a 1 m margin), the path corridor keeps its former street level, in a 379 m² stub.
  - The sewer bank's lower vertices, including its toes, are drawn by interpolating to `terrain.level`. Without the stub, the toes at (−36.2, 11.0) and (−35.5, 11.3) would drop by about 2 m.
  - T8's trim of the route to the embankment toe will make the stub almost moot once both branches merge.
- New JSON record `pathCorridors`: method, per-corridor details (name, width, length, the reading no longer applied, stub area), and evidence separating mapped, observed and interpreted.

### B. Network tidal outline in the blend and batter mask

**Change.**
- `blend_water` = the builder's regional water ∪ the river-network `tide.polygons` (what `app.js` draws as water and tidal water), minus a 5 m buffer around mapped building footprints.
- `blend_surface` treats it as water: vertices inside keep their native height, as beds already did. `edge_caps` treats it as water: batters never rise inside it and are capped at 1:1.5 from its edge.
- Street levels, wall land sides, the wall fill, `open_shore` and `clear_wall_faces` keep the regional mask.
  - 1,303 m of the 2,092 m of interpretive retaining wall stands inside the tide outline. Putting the fill under the new mask would have removed most of T2's fill.
  - The acceptance criterion names the blend and batters only, so the fill is still allowed inside the outline.

**New tidal faces (`tidal_faces`, network and core only).**
- Freezing alone (build v1) left cliffs at the outline: native shelf about 0.2–1.6 m inside, bank crest about 3.4 m just outside. That raised network steps from 0 to 278 and core steps from 106 to 366.
- So blended ground outside the outline may now stand no steeper than 1:1.5 above the native tidal ground. This is measured along network mesh edges, or across the core grid.
- It never lowers ground below its pre-blend height, and never acts in street corridors or building footprints.
- It lowered 9,701 network vertices and 10,509 core vertices (`faceLowering` in the JSON). The fill is then applied as before.

**Building-frontage exception (5 m).**
- Without it (build v3), 62 network steps appeared. All were at riverside buildings whose footprints touch the outline (Three Mills distillery #292–294, footprints 354, 377–379): a 2.86 m footprint vertex sat next to a frozen 0.15 m tidal vertex.
- Lowering ground under a building would expose a gap under its wall. So within 5 m of a footprint the building frontage keeps the bank blend, and the 1:1.5 face runs from the frozen shelf up to it.
- This covers 8,446 of the 75,933 m² of tide outline that lies outside the regional water.

New JSON record `networkTidalWater`: method, `nativeVerticesKept` (network 39,420; core 115,659), face method, `faceLowering`, and evidence.

## Numbers (base → after)

**Steps** (T2's `measure_walls.py`: rise over 2.5 m across under 3 m):

| Mesh | Before | After |
|---|---|---|
| network | 0 | 0 |
| extension | 0 | 0 |
| core | 106 | **52** (0 new edges, 68 gone) |
| system | 214 | 214 |
| groundMesh | 2 | 2 |

Intermediate builds, for the parent's information:
- v1 (freeze only): network 278, core 366.
- v3 (faces, no building exception): network 62, core 52, fill 37.14 %.

**Other acceptance checks:**
- T2 wall fill, within 0.5 m at 1 m and 3 m: 37.19 % → **37.19 %**. At 1 m only: 41.76 → 41.76. At 3 m only: 73.03 → 72.74.
- Bromley trench minimum: −0.103 → **−0.103** (0 profiles below −0.3).
- Abbey Lane deck ends: identical. 0.00 at each end; worst within 2 m −0.12 (west) / −0.18 (east), over preserved mud as T3 reported.
- Seating (`seats.mjs`, all 1,125 objects): **0** moved more than 0.05 m.

**Sewer bank toes within 15 m of the path:** heights at (−36.2, 11.0), (−35.5, 11.3) and (−19.0, −29.6) are 2.06 / 2.15 / 1.35 m before and after, **unchanged**. The other sewer-bank vertices in the stub are also unchanged, because the core ground under them did not change.

**A: Mill Mead riverbank path** (`path.py`, 173 stations every 2 m along 346 m; drawn surface as `infrastructure.js` draws it):

| | Before | After |
|---|---|---|
| Within 0.15 m of ground 1.5 m either side | 85.5 % | **82.1 %** (target 95 %, **not met**) |
| Same, outside the sewer zone | 83.2 % | 79.9 % |
| Within 0.15 m of ground 6 m either side (beyond the old 4 m shoulder) | 49.1 % | 49.1 % |
| Within 0.15 m of the ground under the centreline | 98.8 % | 93.6 % |
| Median ground above the −0.1 marsh, whole path | −0.20 m | −0.20 m |
| Median ground above −0.1, the formerly raised first 120 m outside the sewer zone | **2.72 m** | **1.35 m** |
| Largest change of drawn surface between 2 m stations | 1.04 m (the reach-end cliff) | 0.84 m |

Notes on the table:
- The whole-path median is unchanged because about 230 m of the path already lay beyond the reading's 120 m reach, on marsh at −0.26 to −0.38 m.
- In the formerly raised section, the 1.35 m median that remains is the bank band crest.
- The 6 m figure is a poor measure: on the river side, 6 m out is often the Channelsea bed.

**What the 31 failures after the change are:**
- 25 are on the bank band (stations 60–108 m, z 19–65). The route climbs the band's inland slope obliquely from z 20 to 40, runs just inland of the 3.4 m crest to z 56, and descends to z 64. The cross fall there is up to about 0.7 m over 3 m.
- 3 are the 1:1.5 ramp off the sewer stub (z 9–13).
- 1 is at the Abbey Lane end, inside the sewer zone.
- 2 were already failing before (z 144–146, a ditch edge).
- The bank band, a 14 m crest from the regional shoreline, is the bank policy I was told not to change. The native core terrain also has a raised river-right bank of about 3.3 m there.

**B: tidal outline** (`tidecheck.py`, `tidal.py`):
- Network and core vertices inside the tide outline but outside the regional water, outside the building exception, that end above max(pre-blend height, water edge 0.08 m):
  - Before: network 36,703 and core 7,471 not explained by fill.
  - After: **0** not explained by fill. 1,936 network vertices are raised only by the T2 wall fill (fill level at or above their final height). Core: 0.
  - Inside the 5 m building exception, 7,000 network vertices still stand above that limit (at most 3.11 m above pre-blend), as before.
- Fin vertex (−1051, −618): pre-blend 0.62, before 2.31, **after 0.62**.
- Network edges crossing the tide outline with |dy| over 1.0 / 1.5 / 2.0 m: 1,762 / 795 / 539 before → 1,835 / 843 / 540 after; maximum 2.40 both.
- Vertices changed against base:
  - network: 47,245 lowered (median 0.53, at most 3.19 m); 1,769 raised (at most 1.25 m).
  - core: 16,918 lowered (median 0.59, at most 3.16 m); 6,006 raised (at most 1.42 m).
  - The raises are tidal vertices that the blend used to lower and that now keep their native height.
  - `level.f32`: 155 cells lowered (the former path corridor and its batters, and batters now capped at the outline); none raised.

**Bow Locks bank** (network mesh within 30 m of (−597, 859)):

| | Before | After |
|---|---|---|
| Waterline vertices | 178 | 178 |
| Max jump between adjacent waterline vertices | 0.75 m | 0.75 m |
| 95th percentile jump | 0.65 m | 0.65 m |
| Waterline vertex heights, max / median | 1.03 / 0.21 m | 1.03 / 0.20 m |
| Bank-top ridge | 2.0–2.2 m (blend-raised) | 1.5–1.6 m (native) |

**Why the saw-tooth is not cured.** The waterline position is set by the raw river-network heights and is identical in raw, before and after (`sawtooth.py`). Row by row, the 0.06 m crossing advances exactly 1 m in x per 1 m row, with 2 m jumps at z 856, 862, 868 and 870, and a 3.8 m jump at z 872 (x −607.9 → −611.7). The raw ridge (1.61 m) steps the same way, for example (−596, 856), (−597, 857), (−599, 858), (−600, 859).

So the bank face is a 1 m raster staircase of a diagonal shoreline. Drawn with the mesh's fixed triangle diagonal, it gives the teeth. This is the audit's I9, made in the river-network build. No landscape-builder mask can cure it.

## Checks

- `node scripts/check_main_landscape.mjs`: PASS (exit 0).
- `python3 scripts/check_main_landscape.py`: PASS (exit 0; 28 source hashes; streetControls 9, unchanged).
- `npm test`: **13/15**, failing only `check_drainage_connections.mjs` (git-ignored mosaics absent from the worktree) and `check_flood_demo.mjs` (stale `terrain-1900.json` hash), as known.

## Renders

- Served from this worktree on 4185. Before and after use otherwise identical docs. PNGs are in `t11/views-before[-extra]/` and `t11/views-after[-extra]/`. Changed-pixel share is in brackets.
- I added two cameras for the path, because neither required path camera shows the causeway well:
  - `x-path-along-north`: (−62, 4, 100) → (−42, 1.5, 30);
  - `x-path-side-causeway`: (−85, 6, 40) → (−42, 1.5, 45).

Verdict per camera:

- **`02-mill-mead-path-corridor`** (0.4 %): uninformative. The camera stands inside the sewer embankment footprint looking out under the sewer, before and after. The only change is a small sloped path piece in the distance (the ramp off the sewer stub).
- **Overhead (−40, 90, 40)** (1.5 %): almost identical. Seen from above, the path strip and the bank look the same; the height change does not show in a plan view. `x-path-overhead-south` (1.4 %) shows the same.
- **`x-path-along-north`** (2.1 %): **fixed.** Before: the path ran onto a raised flat strip that ended in a vertical earth face across the path (the 120 m reach end). After: the path lies on the marsh, then rises with the ground onto the bank toward the sewer. There is no strip and no face.
- **`x-path-side-causeway`** (3.5 %): after, the path visibly follows the ground: up over the bank band hump and down again, with a short ramp at the sewer stub. Straight path triangles cut slight chords over the hump.
- **`x-path-along-south`** (1.4 %): unchanged marsh section.
- **`09-old-lea-junction-fin`** (19.6 %): **fixed.** The dark triangular pyramid beside the brick pier is gone.
  - The bank is now terraced: native shelf, then a 1:1.5 green face, then the crest. It reads as an earth bank with flat facets, not a smooth slope.
  - One squared green block face remains mid-frame, where the T2 wall fill beyond route 2's start meets the face. It is earth, not a fin, but it is not pretty.
- **Author's Bow Locks camera** (24.5 %): **saw-tooth not cured,** as explained above. The bank top beside the water is lower (native shelf) and shows more mud face; the teeth are unchanged.
- **`connection-bow-locks`** (0.9 %): essentially identical. The far bank is marginally lower; nothing new is broken.

## Smoke snapshot

- I took a base snapshot first (`t11-base`), from this worktree, before writing `docs/data`. I then ran a scratch copy of `review_smoke.py` with a 900 s tween wait.
- Result: `t11-paths-watermask --compare t11-base`: ready, **0 page errors**, 8,169,881 triangles, 150 draw calls. The screenshot timed out, which the script treats as non-fatal. It exits 1 because there are differences.
- **7 differences:**
  1. `replacements.core.changedVertices` 1,008,374 → 994,676: core tidal cells now keep their native height.
  2. `replacements.core.changeRangeMetres` max 3.37 → 2.94: the largest core raise was inside the outline.
  3. `replacements.network.changedVertices` 410,401 → 372,870: network tidal vertices now keep their native height.
  4. `terrain.vegetationTufts` 3,574 → 3,541: core bank ground changed in the Channelsea tidal outline and along the path.
  5. `terrain.clods` 22,625 → 22,635: same cause.
  6. `triangles` +53: I take these to be the tuft and clod geometry; I did not trace them.
  7. `reflection.triangles` +53: same as 6.
- There is no `sewerCrossing` difference, so the Mill Meads works road arch that T3 changed is untouched.

## What I did NOT do

- I did not trim, re-route or re-trace the path (T8's work), and changed no route, width or reading in any input.
- I did not change the bank band, lip rule, wall crests, wall fill, end caps or T3 batters. Their side effects are measured above: fill unchanged, Bromley unchanged, deck unchanged, and the core steps fell.
- I did not touch the river-network or river-system builds, the renderer, the flood inputs or the GeoTIFF/GeoPackage export. The export is now stale, like the rest of the cascade.
- I did not fix the Bow Locks saw-tooth.
- I did not apply the new mask to the T2 fill (which would break the 37 % criterion), to street levels, or to wall side choice.

## Unsure

- **Whether "adjacent ground" should mean 1.5 m out.** I chose it as the nearest ground clear of the 2 m path. At any offset the path fails wherever it climbs the bank band obliquely. The before figure (85.5 %) only looks good because the old corridor flattened its own surroundings.
- **The 5 m building-frontage exception** is a judgement call. 4 m is about the minimum that lets a 1:1.5 face span the 2.7 m difference.
- **The sewer stub.** It keeps the toes unchanged now. After T8's trim, the path's corridor will cover little or none of the footprint, so the parent's rebuild will change those toes regardless of this branch. That follows from T8's trim, not from my rule.
- I did not prove that the +53 triangles are tufts and clods.

## Decisions for the parent

1. **The building-frontage exception.** Accept it (no new steps; 7,000 network tidal vertices beside riverside buildings keep the blend). Or drop it and accept 62 new network steps at those buildings. Or commission quay walls along those frontages.
2. **Path acceptance.** Meeting 95 % would need one of:
   - the path re-traced onto the bank crest line, or along the toe of the bank band (route data, T8 territory);
   - a narrower bank band where a mapped path runs inland of the crest (a bank-policy change);
   - a revised criterion, for example "within 0.15 m of the ground beneath it" (93.6 % now, held back by the coarse path triangles across the bank hump).
3. **The Bow Locks saw-tooth and other network bank faces (I9)** need the river-network build: smooth the shelf rasterisation, or triangulate the bank faces along the outline.
4. **Rebuild after merging T8.** The path trim will remove the sewer-stub ramp. Re-run `build_main_landscape.py` and both checks.
