# T1 report: the sewer deck spans bare ground

Branch `worktree-agent-af9b9ab3c4423c998`. The branch started 19 commits behind `main` (at 116c0ae, without the delegation plan), so I fast-forwarded it to `main` 72d97c8 before starting. All the work below is on top of 72d97c8.

## What changed and why

1. **`scripts/build_panorama_data.py`, sewer bank clipping only.**
   - Removed the 79 m `bridge_opening` circle and the `water.buffer(2)` clip against the GIS rivers.
   - The banks are now clipped against the water the browser actually draws, set back 1.5 m (`SEWER_WATER_SETBACK`). A new `drawn_water()` copies the union that `app.js` (lines 744–774) and `river-system.js` draw: tide shelves, reviewed connections, retained/isolated channels, marsh ditches, river-system water and terrain pools. Pieces of drawn water under 50 m² are ignored, so the embankment fills one 2 × 6 m marsh pool at the Channelsea east end. Without this rule the bank would wrap around the pool.
   - Why drawn water rather than the GIS rivers: the GIS rivers miss the water the sewer actually crosses. At x −1167..−1139 (sewer-toe-1, "slab over water") the GIS has no river at all, and at the Channelsea the drawn tidal shelf is about 5 m wider than the GIS on each side.
   - The railway corridor clip (6 m) is unchanged.
   - Bank outline runs that face water or the railway are densified (a vertex every 2 m and at the crest edge), so the bank keeps its full profile right up to its end. Before, it sagged to toe height between distant corners.
   - The sample grid now sits on one fixed 12 m lattice (`SEWER_BANK_LATTICE = (2, 0)`) instead of each piece's own bounds. Moving a bank end then re-triangulates only near that end. The phase (2, 0) is the lattice the High Street stretch was originally built on, so its triangles stay identical.
   - New data `neighbourhood.sewer.bankEnds` holds 10 runs (8 water, 2 railway). Each has its `kind`, centreline `chainage` and points `[x, y, z]` in the bank convention. There is also `bankEndsEvidence`: positions are derived from the mapped channel and railway; the wall form is interpreted.
2. **`docs/sewer-crossing.js`.**
   - New `bankEndWalls()` draws a brick end wall (headwall plus wing walls in one face) along every `bankEnds` run. It is 0.8 m thick on the water side and its top follows the bank surface exactly as `app.js` lifts bank vertices (+0.1 m coping). The footing is `level() − 0.6`. It is one mesh, named `bank-end-wall`.
   - The two Channelsea `abutment` boxes now stand 0.2 m proud of the end walls at the actual bank ends (centres at about −25 m and +24 m from the anchor). Before, they were at ±29 m. If `bankEnds` is missing, they fall back to the old positions.
   - The report now includes `endWalls: {count, kinds}`. The iron trough (±30 m) is unchanged; its ends now sit inside the embankment, which is where the sewer barrels would be.
3. **`docs/data/ground-plan.json`**: `neighbourhood.sewer.banks` regenerated, `bankEnds` and `bankEndsEvidence` added, patched in place. **`docs/data/infrastructure.json`**: `sewerBanks` regenerated (the browser draws these: the ground-plan banks after the road-opening cuts), patched in place. `scripts/build_infrastructure.py` is not changed.

Patch procedure (scratch scripts, not in the repo):
- Run `build_panorama_data.py`, keep its output, restore the committed file, and copy only the three sewer keys across.
- Then run `build_infrastructure.py` against the patched plan and copy only `sewerBanks` across.
- The infrastructure rebuild differed from the committed file only in `sewerBanks`, and the patched file is byte-identical to that rebuild.
- `build_infrastructure.py` needs the git-ignored `reference/spot-heights/mosaics/*` files. I symlinked or copied them from the main checkout for the build and removed them afterwards.

## Structural diff (Python, path-level, against HEAD)

```
ground-plan.json
  /neighbourhood/sewer/bankEnds          added
  /neighbourhood/sewer/bankEndsEvidence  added
  /neighbourhood/sewer/banks             list 2015 -> 2430
  3 differing paths
infrastructure.json
  /sewerBanks                            list 2423 -> 2893
  1 differing path
```

`crest`, `route`, `sewerCrestTriangles`, `sewerRailEdges` and `sewerHighStreet` are unchanged. A full `build_panorama_data.py` rebuild differs from the patched file only in `/neighbourhood/terraces` (99 → 98). That is the drift you already knew about and it is not carried over. Garden beds are unchanged even in a full rebuild.

## Checks

| | base 72d97c8 | after |
|---|---|---|
| `npm test` | 13/15 | 13/15 |
| `check_sewer_crossing.mjs` | PASS | PASS (no assertion edits) |
| `check_sewer_high_street.mjs` | PASS | PASS |
| `check_drainage_connections.mjs` | FAIL (missing reference file; with the files present, stale `terrain-1900.json`) | FAIL, now first on stale `infrastructure.json` |
| `check_flood_demo.mjs` | FAIL (stale `terrain-1900.json`) | FAIL (same) |

`infrastructure.json`'s hash was current before this change. It is now stale in the `inputHashes` of `drainage-connections-1900`, `flood-demo-1900`, `landscape-flood-1900`, `main-landscape-1900`, `river-system-1900` and `terrain-1900`. `ground-plan.json` was already stale in those files (and in `river-network.json` `planSha256`) before this change.

Python checks I ran after the change:
- Pass: check_gardens, check_continuous_structures, check_great_eastern, check_scene_data, check_north_london_connection, check_river_banks, check_core_river_connections, check_manor_road, check_regional_marsh.
- Fail on hashes that were already stale at base, so none of these flipped: check_river_system and check_main_landscape (ground-plan hash), check_landscape_flood (now infrastructure first; ground-plan was stale at base).
- Fail on missing git-ignored reference files: several other checks.
- check_panorama.py is hard-wired to port 4173, so it ran against the main checkout. Its result says nothing about this branch.

## Numbers

Bank-to-water distance, measured from every bank-end vertex to the nearest drawn water:

| crossing (chainage, x) | before | after |
|---|---|---|
| Lea branch d 155–184, x −1167..−1139 (toe-1) | bank over the water: 1,089 m² of bank on drawn water, no cut | 1.49–1.51 m both sides |
| d 448–480, x −883..−851 | 420 m² of bank over water | 1.49–1.51 m |
| d 728–750, x −614..−593 (west of High Street) | 285 m² of bank over water | 1.49–1.51 m |
| Channelsea d 1433–1472, x −22..+16 | 40–64 m gaps (56 m west, 62 m east on the centreline); about 1,710 m² of crest strip over bare land | west 1.49–1.51 m; east 1.50–1.92 m (1.92 at a step in the drawn water edge) |

- At every crossing the end wall's front face is about 0.7 m from the water edge.
- Bare land under the 15 m crest at the four crossings is now only the 1.5 m setback strips (49–65 m² per crossing), which the 0.8 m walls partly occupy.
- Bank triangles: ground-plan 2,015 → 2,430; infrastructure 2,423 → 2,893.
- End walls: 10 runs, 2,860 triangles.
- Scene: +3,330 triangles in both the main and the reflection pass; draw calls unchanged at 151.

High Street:
- Every bank triangle and surface sample from the High Street centre eastward is identical to before.
- 74 of the 120 triangles within 40 m are identical.
- The only changed bank surface is 10–40 m west of the centre, where the bank end at the d 728–750 water moved off the water. Mean change 0.04 m, max 0.99 m in bank-height units there.

## Render verdicts

Renders were served from this worktree on port 4174 and are in the scratch folder `views-after/`. There were no page errors.

- **sewer-toe-7s** (Channelsea, from the south): fixed. The embankment is continuous under the deck and no sky shows beneath it.
- **author-1-corrected** (on the Channelsea under the trough): fixed. The trough emerges from a brick end wall; daylight under the trough is over water only.
- **bridge-abbey-mill-crossing-approach-a**: fixed for the sewer. The deck ends on a brick wall at the Channelsea. The pleated ground face in the foreground is I1 (ground mesh), not this task.
- **sewer-toe-1s** (Lea branch): fixed. The slab overhanging the river is gone; a brick wall closes the bank and the deck spans the water.
- **sewer-toe-6s: NOT fixed, looks the same as before.** The wedge and daylight here come from the **Abbey Lane road opening** that `build_infrastructure.py` cuts (`roads.buffer(1.5)`), not from the water clip or the circle. See "not done".
- **bridge-bow-bridge-span** and **bridge-channelsea-high-street-bridge-span**: the sewer is not in frame (these bridges are hundreds of metres away). Nothing related to this task is visible and nothing changed.
- Extra views:
  - sewer-toe-7n: continuous bank.
  - t1-channelsea-west-wall and t1-channelsea-under-deck: end walls at both Channelsea ends.
  - t1-crossing-448-water: walls on both sides of the span. A green sloping sheet at the far left is, I believe, the Great Eastern main-line embankment rising to its bridge over the sewer, but I did not confirm this.
  - t1-woolwich-along-rail: the railway passes under the deck between thin brick wall ends.
  - sewer-toe-8s: the Mill Meads works road opening still has its wedge, as before.
  - t1-crossing-728 put the camera inside a solid, so the frame is useless; t1-crossing-728-water reads normally.

`review_smoke.py t1-sewer-banks --compare drawn-ground --url=http://127.0.0.1:4174`:
- The stock script timed out twice at its 60 s `tweening` wait. Base files on the same server time out the same way, so this is the environment, not the change.
- With a scratch copy that waits longer: the base files give **0 differences** against `drawn-ground`. The T1 files give **0 page errors and 5 differences**, all expected:
  - `triangles` 8,154,223 → 8,157,553 and `reflection.triangles` +3,330: 2,860 wall triangles plus 470 extra bank triangles.
  - `sewerCrossing.bounds.abutment.min/max`: the abutments moved from ±29 m to the real bank ends. Their footing minimum rises from −0.78 to −0.09 because `level()` is higher at the new positions.
  - `sewerCrossing.endWalls`: null → `{count: 10, kinds: [railway, water]}`.
- The smoke JSONs are in the git-ignored `scenes/channelsea-sewer-panorama/review/`.

## What I did not do

- **Road openings.** Abbey Lane (d 1224, toe-6) and Mill Meads works road (d 1574, toe-8) still end in open wedges. That cut lives in `build_infrastructure.py`, and `sewer-crossing.js` only receives `neighbourhood.sewer` and `sewerHighStreet`. So walls there would need either the road crossings in `bankEnds`, which means `build_panorama_data` reading road routes, or an `app.js` change.
- **The `level()` toe-height problem**: not attempted.
- **No piers in the channels**, and no trough at the other three crossings. The deck over those is still the generic 0.48 m slab with brick walls at each end.
- Did not update any stale `inputHashes`.
- Did not touch the High Street crossing spec.
- Left the Channelsea trough at ±30 m.

## What I was unsure of

- **Mill Mead riverbank path** (mapped on VIII.32, x ≈ −37) is now buried for about 44 m under the extended Channelsea bank (90 m² of path under bank). Paths do not cut sewer banks in `build_infrastructure.py`. It may in fact have passed through a land arch or creep in the embankment.
- Reading the previous build's `river-network.json` / `river-system-1900.json` inside `build_panorama_data.py` is a file-order dependency. There is no value cycle (those builders never read the sewer), but this script must be rerun after the water changes. The docstring says so.
- The east Channelsea abutment box sits where the drawn water edge has a step, so it may sit partly behind the oblique wall.
- One brick end wall per bank end (wing walls in the same plane) is an interpretation. It is not a documented NOS abutment.

## Decisions for the parent

1. Accept the new `bankEnds` / `bankEndsEvidence` keys in `neighbourhood.sewer`. They go beyond "banks and crest", but the end walls cannot be placed without them.
2. Whether to give the Abbey Lane and Mill Meads road openings the same walls (needs a small scope extension, above).
3. Whether the Mill Mead path should pass through an opening in the embankment.
4. When to rebuild the derived files whose `inputHashes` now point at an older `infrastructure.json`.
5. Whether to add piers or troughs at the three non-Channelsea crossings.
