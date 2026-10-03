# T7 report: road names (Warton Road, Angel Lane)

Branch `worktree-agent-a046c27b5f8b1f81c`. Before starting I fast-forwarded the branch from `116c0ae` to main `a7e9352`. The worktree had been created 30 commits behind main and did not have `review_smoke.py`, T1, T1b or T6. The fast-forward did not touch the main checkout.

## Evidence used
- **OS London five-foot 1893–96 mosaic.** NLS tiles `os-london-five-foot-1893`, zoom 18, read through `factory_map_sources.mosaic` from the main checkout's read-only tile cache. I read every label myself from the crops below.
- **EPFL OS text layer** (`londonos_texts_postcorrected.gpkg`, EPSG:27700). I converted label centroids to scene coordinates and used them as a cross-check.
- **The saved OS VIII.22 scan** (`reference/neighbourhood-context/os-viii22.jpg`). This is the source of the sheet-22 pixel traces, so it shows what the tracer actually clicked on.

## Streets examined

| Model name | Printed name read (scene x,z) | Action |
|---|---|---|
| **Warton Road** (eastern, (237,-878)→(327,-437)) | "…T HAM LANE" beside the Police Station at about (248,-868). "WEST HAM LANE" at about (365,-640). EPFL has HAM (235,-889), LANE (258,-859), WEST (352,-692), LANE (386,-614). The street turns into "ABBEY ROAD" south of the junction near (370,-500). | **Renamed "West Ham Lane"** |
| **Warton Road upper housing** ((-372,-828)→(-267,-720)) | "WARD ROAD" on the only street joining the same two streets (the road to the north, where EPFL reads ROSHER, and Stratford High Street), parallel to the trace. EPFL has WARD (-369,-790) and ROAD (-330,-750). | **Renamed "Ward Road"** |
| **Warton Road northern section** ((-700,-700)→(-470,-497)) | "WARTON" printed on the north–south arm north of the railway bridge, at (-744,-758). "ROAD" printed on this traced south-east arm, at (-688,-677), 7 m from the trace. | Unchanged: this is Warton Road |
| **Angel Lane** ((-67,-803)→(-28,-687)) | No printed street under the trace. On both the mosaic and the VIII.22 scan it crosses house plots in the block bounded by Bridge Road, Devon Terrace and Albion Street. The nearest names are RAILWAY PLACE, MOUNT PLACE, DEVON TERRACE and ALBION STREET. ANGEL LANE is printed about 600 m north, near (-72,-1357), with "Angel Lane Bridge" at (-77,-1482). | Name unchanged, flagged in its `alignmentEvidence` |
| **Angel Lane block passage** ((-27,-766)→(-2,-699)) | Same block. It runs from Railway Place to Albion Street through plots, roughly on the line of Mount Place, and follows no printed street. | Name unchanged, flagged in its `alignmentEvidence` |
| **"Angel Lane block"** (row labels in `os-neighbourhood-traces.json`, rows os-row-54/55/56) | Same block, no printed name. | Unchanged. It feeds `ground-plan.json`, which I was not allowed to rebuild. |
| **"Wharton Road"** (`housing-road-traces.json`) | Not examined. It is already removed by `removeRoadNames` in the housing review, so it is never rendered. | Unchanged |

Every renamed road's `alignmentEvidence` now cites the crop centres, the printed label and its position, the EPFL labels, and what is still estimated.

## Geometry problems found (not fixed, out of scope)
- **West Ham Lane trace.** It runs 5 m from the printed lane at the north end and 35–55 m west of it from the middle southward. It was traced at the VIII.22 sheet edge, and the lane straddles the join with VIII.23. South of Paul Street it runs over the east frontage of Arthingworth Street. The seven `district-*-east-return` rows keyed to it probably front Arthingworth Street on the map.
- **Ward Road trace.** It lies 15–30 m north-east of the printed carriageway, across a yard and buildings, on both the mosaic and the scan.
- **Angel Lane and the block passage.** These look like lines drawn through a block, not mistraced streets. Deleting or retracing them is a geometry decision.

## Files changed
- `data/maps/housing-road-traces.json`: one road name. Evidence appended on three roads: West Ham Lane, plus the flags on Angel Lane and Angel Lane block passage.
- `data/maps/district-housing-review.json`: one road name with its evidence. Street and front-street names on eight rows: seven now West Ham Lane, one now Ward Road.
- `data/maps/east-bridge-road-housing.json`: four street-name fields on one row, `district-leywick-morley-east-east-return`, inside its `priorReview` and `priorPublishedRow`.
  - These are recorded copies only; `apply_review` takes the street from the district review row.
  - Re-running `east_bridge_housing.py` (`prepare()`) would bring back "Warton Road" from the git-ignored baselines in `reference/`.
- `docs/data/infrastructure.json`: names and evidence patched in place (see below).
- `docs/data/housing-detail.json`: names patched in place (see below).
- I did not change `district-road-traces.json` or `os-neighbourhood-traces.json`.
- No JS in `docs/` and no check script matches these names, so nothing there changed.
  - The only "Warton" or "Angel Lane" strings in scripts are spot-height notes, in `spot_height_setting.py` and the lower-lea elevation audit. These refer to the real places.
  - `docs/infrastructure.js` keys only bridges by name, and none of those changed.

## Why I patched instead of rebuilding
**`build_infrastructure.py`.** A rebuild with the **unchanged** inputs on HEAD already gives different road meshes from the committed file:
- 159,895 differing leaves in `roadTriangles`, `shoulderTriangles` and `roadSurfaces`;
- `shoulderTriangles` goes from 16545 to 16528;
- `sewerBanks` is identical.

That stale mesh comes from earlier inputs and is not my change, so following your rule I patched the names in place.

To prove the rename has no effect on geometry, I rebuilt in a scratch mirror with and without the renames. The only differences were two road `name` fields and four `alignmentEvidence` fields. The in-place patch script also asserts that every other road key is identical.

**`build_housing_detail.py`.** This writes `docs/data/housing-detail.json`. It keys row frontage fitting by street name, through rows from `district_housing.apply_review` and `east_bridge_housing.apply_review`. Rebuilt from the patched infrastructure, the output differs from the committed file only in the renamed rows' `street`/`frontStreet`, plus two last-digit float differences:
- `walls[2829]`
- `forecourts[19]`

Those two float differences also appear when rebuilding with no changes at all, so I patched only the names in place.

## Structural diffs (HEAD vs commit)
- `docs/data/infrastructure.json`: 6 leaves.
  - roads[39] `name` Warton Road → West Ham Lane, plus its `alignmentEvidence`;
  - roads[73] `name` Warton Road upper housing → Ward Road, plus its `alignmentEvidence`;
  - roads[40] Angel Lane and roads[41] Angel Lane block passage: `alignmentEvidence` flag only.
- `docs/data/housing-detail.json`: 16 leaves, all `rows[].street`/`rows[].frontStreet`. Seven rows go to West Ham Lane and `district-warton-upper` goes to Ward Road.
- `district-housing-review.json`: 18 leaves (8 street, 8 frontStreet, 1 road name, 1 road evidence).
- `housing-road-traces.json`: 4 leaves (1 name, 3 evidence).
- `east-bridge-road-housing.json`: 4 leaves (prior-record street fields).

## Checks
- **`npm test`: 13/15.**
  - `check_flood_demo.mjs` fails on the known stale `terrain-1900.json` hash.
  - `check_drainage_connections.mjs` fails in the worktree because the git-ignored `reference/spot-heights/mosaics` files are missing. Run in the mirror with `reference/` available, it fails on the known stale `infrastructure.json` hash. HEAD's file (`a99ecc…`) already did not match the expected `91ffdf…`; my patch only changes the actual hash to `fb3732…`.
- **Smoke test.** I served the worktree's `docs` on 4180 and ran a scratch copy of `review_smoke.py` with the wait raised to 900 s: `t7-road-names --compare drawn-ground`. Result: ready, **0 page errors**, 17 differences. The screenshot timed out and was skipped, which the script treats as optional.
  - All 17 differences come from work merged after the `drawn-ground` snapshot, not from me:
    - **T6, site 865:** factory sites 63→64, ranges 697→728, roofPlanes 1622→1702, chimneys 88→89, windows 9677→10071, chimneyTops, siteRanges/siteChimneys 865.
    - **T1b, sewer:** `sewerCrossing.endWalls` and `roadArches` added, abutment bounds changed.
    - **Totals:** triangles, draw calls, reflection triangles/draw calls, and destinationCount 128→129. I assume the extra destination is T6 but did not confirm it.
  - To isolate my change, I served a scratch copy of the same docs with HEAD's `infrastructure.json` and `housing-detail.json` and ran `t7-base --compare t7-road-names`: **0 differences**.
  - The snapshot does not contain road names, so navigation labels are unaffected.

## Crops (scratch, with routes drawn)
Directory: `/tmp/claude-1000/-home-jic823-book-website/158d731a-06ad-4794-89f0-96291b5302cd/scratchpad/t7/`. Red is the examined route, blue is the other model roads. Labels show the old names, because the crops were drawn before the edit.

- **Mosaic crops** (centre x,z / half-width in metres):
  - `overview_east.png` (280,-660 / 300)
  - `warton_a_north.png` (260,-830 / 80)
  - `warton_b_mid.png` (320,-680 / 80)
  - `warton_c_south.png` (335,-530 / 80)
  - `overview_west.png` (-480,-680 / 300)
  - `warton_upper_housing.png` (-320,-775 / 75)
  - `warton_northern_a.png` (-700,-720 / 90)
  - `warton_northern_b.png` (-560,-580 / 90)
  - `angel_overview.png` and `angel_raw.png` (-30,-760 / 110)
  - `angel_lane_printed_south.png` (-80,-1300 / 160)
  - `angel_lane_printed_north.png` (-100,-1600 / 160)
- **VIII.22 scan crops** (sheet-pixel traces): `scan_angel.png`, `scan_warton_upper.png`, `scan_warton_east_n.png`, `scan_warton_east_s.png`, `scan_warton_northern.png`.
- **Scripts:** `crop.py`, `scan.py`, `rename.py`, `patch_infra.py`, `patch_housing.py`, `jdiff.py`, `review_smoke_long.py`.

## What I did NOT do
- I moved no geometry, rebuilt neither builder output for commit, and did not touch `build_main_landscape.py`, `main-landscape-1900.*` or `ground-plan.json`.
- I did not rename row IDs that contain "warton", for example `district-warton-upper`.
- I did not update `HOUSING_FRONTAGES.md` or `LANDSCAPE_REVIEW_PLAN.md`; both were outside the permitted files. The plan still lists the T7 conflict as open.
- I did not rename the generic names I passed in the crops, such as "Northern residential street 1/2", which sit near Pitchford Street and Langthorne Street. They were out of scope.
- No web sources were used.

## Unsure
- **Ward Road.** The trace is nowhere on the printed carriageway, so this rename is a judgement. I made it because the trace links the same two streets, runs parallel to Ward Road, and has no other street between; "Warton" was probably a misreading of "WARD".
- **Angel Lane.** By the same standard you could call it unnamed, but no printed street matches its route at all, so I left the name as you instructed.

## Decisions for the parent
1. Keep or revert the Ward Road rename.
2. Delete or retrace Angel Lane and Angel Lane block passage. They match no mapped street, and the real Angel Lane is about 600 m north.
3. Retrace West Ham Lane on the mosaic (25–55 m error in the middle), and decide whether the seven east-return rows should front Arthingworth Street.
4. "Warton Road northern section" is now the only Warton Road in the model. Rename it to plain "Warton Road" in a later pass if wanted. That would touch both `district-road-traces.json` and the housing review, because they key on the same name.
5. A full rebuild of `infrastructure.json` would bring in the stale road-mesh changes described above; that needs its own task.
