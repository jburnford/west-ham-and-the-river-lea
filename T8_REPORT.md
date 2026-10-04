# T8 report: the sewer embankment as an earthwork, and the Mill Mead path stopped at its toe

Branch `worktree-agent-acc9d4e2818aaad07`. The branch started at 116c0ae, behind `main` and without the delegation plan. I fast-forwarded it to `main` 103ea97 before starting. All the work below sits on top of 103ea97.

## What changed and why

1. **`scripts/build_panorama_data.py`: sewer bank shaping only.** A new `EarthBank` class sets the bank's plan and section.
   - **Toe outline.** The bank footprint is the centreline buffered 22 m with rounded joins and caps. Each footprint vertex is then moved radially to its own toe offset: `22 + Σ a·sin(2πd/λ + φ)`, a separate seeded sum for each side.
     - Seed `SEWER_TOE_SEED = 1864`.
     - Three waves with amplitudes 1.0, 0.6 and 0.4 m, so the amplitude bound is ±2.0 m (`SEWER_TOE_AMPLITUDE`). Wavelengths are drawn from 120–180, 55–85 and 28–40 m.
     - The variation tapers to the plain 22 m over the last 60 m of the inferred far extensions, so the far round caps agree.
   - **Section (convex–concave earth profile).** `u` runs from the crest edge (0) to the local toe (1). The fall is `(1−k)u + k·smoothstep(u)`, with `k` varying slowly from 0.35 to 0.65 along each side. A swell of at most 0.1 m, `sin(πu)·sin(2πd/λ)`, vanishes at the crest edge and the toe.
     - Result: a soft shoulder, a steeper middle and a spreading foot.
     - Example section at chainage 1600: slopes of 0.43 → 0.44 → 0.56 → 0.57 → 0.56 → 0.55 → 0.42 per metre outwards.
   - **Height convention.** The bank now reaches the full sewer height (7.4 in the bank convention, which is exactly `cover`) at the crest edge. Under the crest sheet it sits at 7.3, so no faces coincide.
     - The old profile stopped at 7.25, and its 12 m lattice did not sample the crest edge. The bank therefore sagged to 5.8–6.2 there, leaving the pale deck slab showing along the crest. That is the brown/pale band in the before render of `sewer-toe-7s`.
   - **Sampling.** Sample rows run along the slope at u = 0, 0.25, 0.5 and 0.78 (`SEWER_BANK_ROWS`), every 5 m within 1300 m of the origin and every 15 m beyond. The toe outline has a vertex every 4 m, and the crest interior keeps a sparse 12 m lattice.
     - Triangulation is Delaunay plus a constrained fill of any concave remainder, so the bank's coverage is exact (134,570 m²).
   - **Bank ends.** T1/T1b's densified end vertices (every 2 m and at the crest edge) are kept. `bankEnds` is recomputed with the new height function, so the end walls follow the curved profile.
   - **Garden.** The allotment garden is still clipped against the earlier straight 22 m mitred outline (`laid_out`), so the garden beds do not move, even in a full rebuild. Garden-bed overlap with the new bank: 0 m².
   - **`bankFormEvidence`** is new. It says what is kept from the record (centreline, 15 m crest, 44 m base as a mean, about 7.4 m height from author guidance; "exact nineteenth-century section unresolved"). It also says what is interpreted: the rounded toe outline, the seed and amplitude, the profile form and the swell.
   - **Crest outline unchanged.** The `crest` polygon and the infrastructure crest and rail edges keep their mitred joins. The route's bends are gentle (at most 15.6°), so a mitre at 7.5 m adds at most 0.07 m (0.2 m at the 22 m toe). The "square" look came from the coarse mesh and the single plane, not from the mitres. Keeping the crest unchanged also keeps the High Street crossing untouched.
2. **`scripts/build_infrastructure.py`**
   - **(a) Path guard.** A new assert: no path surface may lie inside the sewer bank footprint ("A path runs through the sewer embankment"). At base the only path that failed it was the Mill Mead path (90.7 m²).
   - **(b) Crest split.** The crest is split along the bank outline, so the browser can grass the part over earth and keep stone over the openings without a sawtooth seam.
     - Crest triangles that touch an opening are re-triangulated into an earth part and a deck part. All others keep their old triangulation.
     - The High Street stretch (the opening plus 3 m) is excluded from the split.
3. **`data/maps/road-traces.json`**: the Mill Mead riverbank path is now two records.
   - "Mill Mead riverbank path" (south, 298.5 m) starts at the south toe. Its new first point is (1039.0, 728.7) px.
   - "Mill Mead riverbank path, north of the sewer" (3.2 m) runs from the mapped start (1059, 654) to the north toe at (1057.7, 659.0).
   - Each record has a `routeEvidence` string. It says which part is the mapped OS VIII.32 trace and which end point is estimated (cut where the mapped path meets the later embankment, 0.25 m clear of the modelled toe). It also says that no tunnel, creep or steps is mapped or documented.
   - No tunnel, steps or ramp was added.
4. **`docs/app.js`, crest drawing only (the `mark('sewer')` block).** Each `sewerCrestTriangles` triangle is classified by whether its centroid lies over a `sewerBanks` triangle (10 m grid hash, point-in-triangle).
   - Earth triangles: `materials.ground` (the bank's grass), with the bank's UV mapping (`x/5500, −z/5500`).
   - Deck triangles (over water, railway or street openings): `materials.stone`, as before.
   - The bank mesh, deck boxes and rails are unchanged.
   - Prettier and ESLint are clean.
5. **`docs/data/ground-plan.json`** and **`docs/data/infrastructure.json`** are patched in place (below). `docs/sewer-crossing.js` and the check scripts are not changed.

**Patch procedure** (scratch scripts in `<scratchpad>/t8/`):
- Ran `build_panorama_data.py`, restored the committed file, and swapped in only `neighbourhood.sewer` (the script asserts that only `banks`, `bankEnds` and `bankFormEvidence` differ).
- Ran `build_infrastructure.py` against the patched plan, with the git-ignored mosaic `m18_131075_87146.*` symlinked from the main checkout and removed afterwards. I then copied across:
  - `sewerBanks`, `sewerCrestTriangles` and `sewerRailEdges`;
  - the two Mill Mead records in place of the one (the script asserts all other routes are identical);
  - `pathTriangles` (the script asserts that every non-Mill-Mead path triangle is identical, in content and order, between the committed file and the rebuild).

## Structural diffs (path-level, against HEAD 103ea97)

```
ground-plan.json (patched)
  /neighbourhood/sewer/banks             list 2621 -> 11490
  /neighbourhood/sewer/bankEnds          list 16 -> 16
  /neighbourhood/sewer/bankFormEvidence  added
  3 differing paths
infrastructure.json (patched)
  /roads                list 101 -> 102   (Mill Mead record replaced by its two parts, same position)
  /pathTriangles        list 320 -> 303   (Mill Mead 145 -> 128; all other path triangles identical)
  /sewerBanks           list 2651 -> 11459
  /sewerCrestTriangles  list 1684 -> 2032 (1551 identical; 133 next to openings re-cut into 481)
  4 differing paths
```

- **bankEnds:** the same 16 runs (8 water, 6 road, 2 railway).
  - Every chainage is identical except Godfrey Street (831.36 → 831.62) and Ross Road (955.11 → 955.60), which are toe-only ends.
  - Every `roadAxis` is identical.
  - Run end points move only where they meet the new toe. Wall tops reach 7.40 instead of 7.25.
- **Unchanged:** `crest`, route, `sewerHighStreet`, `sewerRailEdges` (byte-identical), railways, roads other than the path, and garden beds.
- **High Street:** the crest triangles within 20 m of the crossing centre are identical. Between 20 and 50 m, crest triangles changed only beside the d 726–751 water opening about 33 m west (its deck split).
- **Bank inside the High Street cut** (street half-width + 1.5 m): 0 m² both before and after.
- **Full-rebuild drift that is not carried over:**
  - `ground-plan`: `/neighbourhood/terraces` 99 → 98 (known), and `/neighbourhood/garden/accessCorridors` 15 → 16 (see "not done").
  - `infrastructure`: `roadTriangles`, `shoulderTriangles` and `roadSurfaces` (the known road-mesh drift).
- **File sizes:** `ground-plan.json` 613 KB → 1.23 MB; `infrastructure.json` 9.49 → 10.09 MB. The extra bank triangles are needed to carry the curved profile.

## Acceptance numbers

| criterion | result |
|---|---|
| crest width | 15.06 m mean (crest area / length); outline unchanged |
| base width | toe-vertex offsets 20.05–23.99 m, mean 21.96 → 43.93 m mean base (record 44) |
| height | 7.40 at the crest edge (record 7.4; the old mesh reached 7.25) |
| toe variation | ±2.0 m bound, measured −1.95/+1.99 m (limit ±3) |
| rounded joins and caps | toe outline: yes. The crest keeps its mitres (≤0.07 m at these bends) |
| profile not a single plane | convex shoulder, steeper middle, concave foot; 0.1 m swell |
| Mill Mead `pathTriangles` inside the bank footprint | 0 m²; minimum clearance 0.23 m. Centreline ends are 0.41 m (south) and 0.54 m (north) from the toe |
| any path triangle inside the footprint | 0 m² (now asserted by the builder) |

## Checks

| | base 103ea97 | after |
|---|---|---|
| `npm test` | 13/15 | **13/15** (the same two fail) |
| `check_sewer_crossing.mjs` | PASS | PASS (no assertion edits) |
| `check_sewer_high_street.mjs` | PASS | PASS (no assertion edits) |
| `check_bridge_movement.mjs` | PASS | PASS |
| `check_drainage_connections.mjs` | FAIL: missing git-ignored mosaic | FAIL, same cause |
| `check_flood_demo.mjs` | FAIL: stale `terrain-1900.json` hash | FAIL, same cause |

Python checks:
- **Pass:** gardens, continuous_structures, great_eastern, scene_data, housing_frontages, abbey_station_plan, north_london_connection, river_banks, core_river_connections. Also manor_road, which needs the mosaic temporarily linked.
- **Fail identically on base data** (I ran these on the base files to confirm):
  - check_district_streets: `('b865-garden-house', 70.59)`.
  - check_high_street_frontages: `('high-street-01', 'roads')`.
- **Fail on missing git-ignored reference files:** three_mills_landmark, east_channelsea ×2, sawmill, oil_wharf, river_system.
- **Fail on stale input hashes:**
  - check_landscape_flood: `infrastructure.json` was already stale at base (`main-landscape` records a99e…, base was fb37…).
  - check_main_landscape: its recorded `ground-plan.json` hash matched base (eb9b…) and is now stale. `infrastructure.json` was already stale there.
  - Both need the landscape rebuild that another agent owns.

## Renders

- Before: `<scratchpad>/t8/views-before/`. After: `<scratchpad>/t8/views-after/`.
- Scratchpad: `/tmp/claude-1000/-home-jic823-book-website/158d731a-06ad-4794-89f0-96291b5302cd/scratchpad/t8/`.
- Served from this worktree on port 4183. No page errors.

| camera | verdict |
|---|---|
| overhead Channelsea (0,120,60) | **Fixed.** Before: a pale 15 m stone strip with straight hard edges. After: a grassed crest continuous with the slopes. The stone shows only over the Channelsea span, with clean seams at both end walls. The toe edges now wander gently. |
| `author-1-corrected` | Unchanged, as expected. The trough emerges from the brick end wall; daylight only over water. |
| `sewer-toe-7s` | **Fixed.** Before: the bank sagged below the deck, showing a pale band and brown triangles along the crest. After: a continuous grassed slope with a soft shoulder and foot right up to the rail. One small dark chip remains at the crest edge at the far left (see "unsure"). |
| `sewer-toe-6s` | T1b's wing wall still meets the bank. Its coping now follows the curved profile: convex near the top, concave at the foot. The arch is unchanged. There is a similar small chip at the crest edge, top left. |
| low view from the Mill Mead side (−45,2,70) | Not informative, before or after. The camera sits against the landscape's raised path corridor (the green slab on the right), which is not mine. |
| extra `t8-mill-mead-along-bank-raised` (y 4.5) | The cinder path runs to the embankment foot and stops. The grassed bank and the trough are behind it. The raised landscape path block is visible on the left. |
| extra `t8-path-toe-overhead` | The south path strip ends at the toe. The 3.2 m north stub is too small to read. The stepped green terraces beside the path are the landscape's raised path corridor (not mine). |
| extra `t8-path-south-toe-low` | Dominated by the landscape's raised path corridor slab. |
| extra `t8-high-street-overhead` | The crossing looks as before: road clear, crest and rails stop at the carriageway. The new form is visible on both sides. |
| extra `t8-crossing-726-overhead` | Clean grass/stone seam at both ends of the span. |

One intermediate render, before I split the crest triangulation, showed a sawtooth grass/stone seam at the span ends. That is why `build_infrastructure.py` now re-cuts the crest triangles next to the openings.

## Smoke

`review_smoke.py` was run from a scratch copy with a 900 s `tweening` wait. The screenshot step timed out (environment); the JSON is complete.

- **`t8-base` vs `drawn-ground`:** 0 page errors and 19 differences. These are all from work merged since that baseline was taken (factory site 865, T1/T1b sewer walls and arches, landscape vertex counts, destinations).
- **`t8-sewer-form` vs `drawn-ground`:** 0 page errors and 21 differences.
- **`t8-base` → `t8-sewer-form`:** 5 differences, each explained:
  - `triangles` 8,167,680 → 8,176,939 and `reflection.triangles` +9,259: the bank +8,808, the crest +348 and paths −17. The rest is end walls with a few more points per run, plus the extra tufts.
  - `infrastructure.roadRoutes` 101 → 102: the path split.
  - `terrain.vegetationTufts` 3404 → 3462: `terrain-details.js` no longer keeps tufts off the deleted 45 m path stretch. Most of these lie under the bank.
  - `sewerCrossing.roadArches`: Abbey Lane `edgeClearance` 4.41 → 4.40 and Mill Meads `span` 7.43 → 7.42. These come from the end-run points moving at the toe.
- Draw calls are unchanged at 150.

## What I did NOT do

- **Landscape.** I did not touch the landscape and did not rebuild it. The raised path corridor at about 2.2 m over the marsh and the path's painted strip on the landscape mesh are not mine, and they need a landscape rebuild after the path trim.
  - Note for that rebuild: `build_main_landscape.py` looks up the path by name (`laterSurfaceLayers` feature "Mill Mead riverbank path", spot height `sh_538874_183253` at about (−26, −44)). That name now binds to the south part, but the spot height lies beside the north stub.
- **Garden access corridors.** I did not patch `neighbourhood.garden.accessCorridors`. It is built from the sheet-32 road traces, so a full rebuild changes it from 15 to 16 corridors. The garden beds come out unchanged in a full rebuild (verified).
- **Other data.** I did not touch `sewer-crossing.js` or the check assertions, and did not update any stale `inputHashes` or `scene-manifest.json`.
- **Crest outline.** I did not round the crest outline (reason above).
- **No new structure.** No tunnel, creep, steps or ramp for the path.

## What I was unsure of

- **Crest chips.** A small dark chip at the crest edge shows in `sewer-toe-7s` and `sewer-toe-6s`, top left. My best guess is that a straight deck-box corner pokes past the rounded crest-edge row at a bend, or that there is a short sag between two crest-edge samples. I did not trace it.
- **North stub.** The 3.2 m north stub is faithful to the trace, but it reads as nothing. Dropping it is a reasonable alternative.
- **Path end points.** These were computed against this toe line. If the bank form or seed changes, the trace ends must be recomputed (the builder assert will catch a path reaching into the bank).
- **Grassed crest.** This is the brief's direction. I have not seen a source showing the crest's c1900 surface (grass, gravel walk or something else).
- **Data size.** The plan file roughly doubles in size.

## Decisions for the parent

1. Accept the split of the Mill Mead path into two named trace records. Alternatively, drop the 3.2 m north stub.
2. Accept the bank top at the full sewer height at the crest edge (7.4, not 7.25). It removes the visible deck strip, and the end wall tops rise by 0.15 m.
3. Accept the crest split in `build_infrastructure.py` and the grass/stone classification in `app.js`, rather than a new data key.
4. Accept keeping the mitred crest outline so that the High Street crossing stays untouched. The alternative is rounding it (≤0.07 m change; crest triangles near the High Street would re-triangulate).
5. Schedule the landscape rebuild for the path trim, and decide which path record the spot height `sh_538874_183253` should bind to.
6. Accept the larger `ground-plan.json` (1.23 MB) and `infrastructure.json` (+0.6 MB), or ask for coarser rows (`SEWER_BANK_SPACING`, `SEWER_BANK_ROWS`).
