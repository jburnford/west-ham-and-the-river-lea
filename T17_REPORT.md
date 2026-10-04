# T17 report: High Street frontage ranges moved off the road

4 October 2026. Branch `worktree-agent-adc4180d72815f8b3`. At the start the worktree was behind main, so I fast-forwarded it to 493123a with `git merge main`. I did not merge main again after T15. Scratch work, overlays, renders and tables are in `/tmp/claude-1000/-home-jic823-book-website/158d731a-06ad-4794-89f0-96291b5302cd/scratchpad/t17/` (called `t17/` below).

## Summary

- **Six ranges re-registered.** `high-street-01…05` and `-30` now have their street face on the printed OS building line, 7.4–9.6 m from the retraced centreline. They moved 5.5–9.3 m south-east and now cover the drawn blocks (EPFL footprint cover 0.80–0.97; it was 0.00).
- **Road overlap gone.** With T13's 1.1 m shoulder, road overlap for all six is 0 m²; it was 31–185 m² each. Every range is built whole (retained fraction 1.0).
- **`high-street-09` (Marshgate corner P.H.): both the range and the lane are wrong.** I moved the range onto the printed P.H. block. The modelled Marshgate Lane runs about 3 m west of the printed lane, so the builder still trims the lane side (retained 0.58). That needs a road retrace, which is outside my files.
- **`check_high_street_frontages.py` does not fully pass.** Every frontage assertion passes. It now stops at a vista path, `wall-lane-south`, which crosses factory range `site419-range-1` by 1.99 m². That fault was already on main but hidden behind the earlier `high-street-01` failure. Fixing it needs `data/maps/wall-river-vista.json` or factory data, which I may not edit, so I stopped there.
- **Other checks.** `npm test` is 14/17, the same three failures as main. The smoke test has no page errors and 7 differences, all explained.

## Where the ranges are defined

- **Register:** `data/maps/high-street-frontages.json`. Each range is a 4-point `footprint` in scene metres. Its `sourceAxis` (mosaic pixels on bounds [-1130,-390,-480,200]) is the footprint's centre line, with the depth split half to each side of it.
- **Builder:** `scripts/build_high_street_frontages.py`. It trims each footprint against factories, ground-plan houses, water and every road buffered by width/2 + 0.8 m.
- **Why the old ranges stood in the road:** `docs/data/high-street-frontages.json` had not been rebuilt since ed15f11, before T13 and later road and factory changes.
- **No builder defect found;** the builder is unchanged.

## Method

- **Frontage reading.** For each range I cast perpendicular rays from the retraced Stratford High Street centreline every 0.25 m along its length. Each ray stops at the first EPFL 1891–96 footprint (`reference/historic-building-footprints-2026-09-28/current-scene-buildings-bng.geojson`, traced from the same OS sheets).
- **Fit.** I fitted a straight frontage line through the readings, dropping readings more than 0.6 m from the median (passages and gaps).
- **New plan.** The near face goes on that line, at the same along-street position. Depth, storeys, height and roof are unchanged.
- **Visual check.** I checked each one by eye on the OS five-foot mosaic (`factory_map_sources.mosaic()`, tiles read from the main checkout).
- **What the register records.** Each moved range now carries `priorFootprint`, `priorSourceAxis` and `priorRotationDegrees` (09 also has `priorSourceDepth`), plus `sourceFootprintFids` and an `osRegistration` block. That block keeps the OS reading (`osReading`, the evidence) separate from `interpretation`.
- **Reproducible.** `t17/apply.py` regenerates the register edits from 493123a and is idempotent.

## Per range

All distances are from the retraced centreline. Overlap is the T13 buildings-in-road measure (carriageway plus 1.1 m shoulder), shown as total / carriageway.

| Range | OS reading (printed line) | Street face before → after | Move | Rotation | EPFL cover before → after | Road overlap before (main) → after |
|---|---|---|---|---|---|---|
| high-street-01 | 8.41 m (72 readings) | −0.85/−0.59 → 8.33/8.44 | 9.33 m (dx 7.29, dz 5.83) | −38.17° → −38.47° | 0.00 → 0.92 | 184.8 / 158.7 → 0 / 0 |
| high-street-02 | 8.47 m (91) | −0.31/0.12 → 8.23/8.73 | 8.58 m (5.06, 6.93) | −37.02° → −36.86° | 0.00 → 0.93 | 161.1 / 136.5 → 0 / 0 |
| high-street-03 | 7.52 m (34) | 1.47/1.07 → 7.41/7.66 | 6.37 m (4.76, 4.24) | −40.95° → −36.40° | 0.00 → 0.88 | 47.8 / 38.8 → 0 / 0 |
| high-street-04 | 8.51 m (40) | 2.75/2.50 → 8.22/8.73 | 5.88 m (3.11, 4.99) | −40.14° → −35.56° | 0.00 → 0.97 | 42.6 / 32.1 → 0 / 0 |
| high-street-05 | 9.31 m (117) | 3.26/4.54 → 9.60/9.15 | 5.48 m (3.71, 4.04) | −37.70° → −40.74° | 0.00 → 0.80 | 108.5 / 72.5 → 0 / 0 |
| high-street-30 | 7.70 m (63) | 1.03/0.76 → 7.67/7.42 | 6.72 m (4.98, 4.51) | −54.62° → −54.95° | 0.00 → 0.80 | 30.6 / 16.3 → 0 / 0 |
| high-street-09 | P.H. block, see below | in Marshgate Lane → on the P.H. block | 10.16 m (−0.32, 10.15) | −43.3° → −38.4° | 0.34 (overlap part) → 0.81 | 95.9 / 79.0 → 4.0 / 0.0 (shoulder only) |

### Street face against the printed line

This is measured from the face to the EPFL frontage at 41 points; readings more than 3 m away count as passages and are excluded.

- **Within 1 m:** 02 (max 0.19 m), 03 (0.90), 04 (0.20), 05 (0.49), 30 (0.21). Medians are all within 0.05 m.
- **Exception, 01:** median −0.01 m, but 4 of 41 samples (about 2 m) exceed 1 m at the south-west corner. That is where a small porch or bay prints 1.5 m in front of the line, and the line itself steps back. Listed, not corrected.

### Range notes

- **01.** The OS steps the building line back 2.4 m for the south-west 4 m (readings 10.8–11.0 m) behind that porch. The prior range ran across the forecourt, so I shortened the south-west end by 4.2 m (width 23.65 → 19.45 m). This is the only width change among the six.
- **03.** Shifted 1.5 m north-east along the street. Without the shift, its south-west 1.5 m stood over an open passage (readings 22–30 m).
- **05.** A passage of about 3 m through the printed row (readings 29.5 m or none) lies under the range. I kept the range continuous; the model has no arches.
- **30 (school).** The printed school block runs to 24.1 m from the centreline. The range's back face is at about 24.2 m, so depth 16.7 m is kept.
- **09, what the OS shows.** The P.H. is one shaded block on the south-west side of Marshgate Lane at the High Street corner (EPFL sourceFid 91288, 108 m²). It is about 13.3–13.9 m along the lane and 10.2 m across. The printed lane between its face and the block opposite is about 6.2 m wide.
- **09, what was wrong.** The prior range stood 7 m north-west of the P.H. and 6–7 m into the lane. It is now on the block: width across the lane 9.5 m kept, length 11.1 → 13.3 m because the OS prints one block of that length. The modelled lane centreline runs only 0.2 m from the P.H. face, which is why the builder trims it to 0.58 (72.9 m² rendered, up from 12.4 m² if rebuilt where it was).
- **24 (Harrow Wharf).** Left alone as instructed. After the rebuild it is trimmed to 0.84 (2.8 m² shoulder touch, 0 m² carriageway). The road is about 0.5 m too wide there.

### Overlap with other buildings

- I tested all seven moved ranges against every footprint in T13's inventory: housing rows, sculleries, privies, factory buildings, legacy factory ranges, ground-plan houses, station buildings, the mill and the other frontage ranges. Overlap is 0.0000 m² for all.
- None of them overlaps a factory yard (over 0.05 m²).
- I rebuilt `housing-detail.json` in a scratch mirror with the new frontages, and it came out byte-identical to the committed file.

## Rebuild side effects (not caused by the moves)

Rebuilding `docs/data/high-street-frontages.json` from current inputs, even with the register unchanged, also changes the following (`t17/cmp_hsf.py` shows these lines match an unmoved rebuild):

- **`high-street-06` is now kept (33 → 34 buildings).** At ed15f11 it was omitted because factory range `site789-os-3` covered it; that range has since been re-registered elsewhere. I updated the check's count assertion to 34 and wrote this reason in a comment there.
- **Retained fractions change:** `-07` 0.84 → 1.0, `-08` 0.79 → 1.0, `-13` 0.29 → 0.67, `-14` 0.71 → 0.72, `-19` 0.79 → 0.72, `-20` 0.88 → 0.60, `-24` 0.93 → 0.84. The renderPolygons of `-15/16/17/18/25/31` changed only in vertex order or rounding.
- **Vista:** the `high-street-access` start height moved 1.80 → 1.37 m because the bridge heights changed in T13. `build_river_network.py` (T14) reads this vista.
- **Factory yards:** `high-street-13`, now larger, overlaps the yard of site 256 by 27 m². `check_factory_yards.py` therefore fails at site 256 instead of 397, its main-branch failure. In a scratch mirror, rebuilding `factory-yards.json` makes `check_factory_yards.py` pass completely, including 397.

## Checks

- **`python3 scripts/check_high_street_frontages.py`: fails at `('wall-lane-south', 'building')`.** That is the vista path versus `site419-range-1`, 1.99 m², and the same 1.99 m² is in main's published file. Main failed earlier, on `('high-street-01','roads')`. A scratch copy that only reports this assertion passes everything else: 34 ranges clear of roads, water, buildings and each other, all sources accounted for, path and ramp checks. `t17/check_skip_ribbon.py` is that copy.
- **Builder's own assertions:** pass. It retains 34 ranges; the ones under 0.65 are `-09` 0.58, `-16`, `-18`, `-20`, `-25`, none of them caused by the moves.
- **`npm test`: 14/17,** the same as main: `check_drainage_connections.mjs`, `check_flood_demo.mjs`, and `check_road_bridges.mjs` (pegshole abutments, pending T12c). `check_main_landscape.mjs` passes.
- **Others:** `check_east_depot_tracks.py` passes. `check_factory_yards.py` fails at site 256, as described above.
- **Smoke test.** I took the base from a `git archive 493123a docs` mirror served on 4194, then compared the worktree on 4193 (scratch copy of `review_smoke.py` with both waits raised to 1,800 s and 900 s). No page errors. The 7 differences:
  - ranges 33 → 34 and site ranges 33 → 34 (`high-street-06`)
  - roof planes 66 → 68
  - windows 630 → 638
  - `mainLandscape.seatedObjects` 816 → 817
  - triangles +106, reflection triangles +106

  All of these come from the extra kept range. The moves change geometry but not counts.

## Renders

Before is main on 4173, which has moved on since my base (T15 merged, landscape rebuilt). After is my worktree on 4193. Files are in `t17/views-before/` and `t17/views-after/`.

- **`bow-author`** (−940, 55, 150) → (−1034, 2, 117): before, the road deck runs straight into the near south-east terrace. After, the full carriageway is visible east of Bow Bridge with the terrace behind it, and 01 is shorter at its bridge end.
- **`bow-north-overhead`** (−1030, 60, 10): before, the ranges cover half the road. After, the road is full width, with the ranges along its south-east edge.
- **`eye-high-street-to-bow-bridge`** (−962, 2.5, 66) → bridge: before, a range gable stands in the middle of the road. After, the street is open and the frontage lines the left side.
  - The briefed point (−960, 2.5, 110) is 40 m off the street, behind the terrace. I rendered it as `eye-literal-960-110` (open ground and the back of 01) and added this on-street camera.
- **Extra views:** `school-range-30-overhead` (the school is no longer on the footway) and `marshgate-ph-09-overhead` (the P.H. stands beside the lane head instead of in the lane).
- **Where the stale landscape shows.** The worktree landscape was not rebuilt. In the eye-level view there is a grass strip of about 1.3 m between the 1.1 m modelled footway and the building faces at 8.4 m. The ground also still shows unchanged terrain or pads where the old ranges stood: a brown patch near the school, darker ground by 01. These should settle when the parent rebuilds the main landscape.

## Overlays (prior red, new blue, render polygon magenta, EPFL green, road edges orange)

In `t17/overlays/`: `ov_high-street-01-02.png`, `ov_high-street-03-04.png`, `ov_high-street-05.png`, `ov_high-street-30.png`, `ov_high-street-09.png`, `ov_bow_overview.png`. The buildings-in-road table (main, unmoved rebuild, T17) is `t17/bir_t17_table.md`.

## Not done

- **Files not touched:** `wall-river-vista.json`, factory data, `infrastructure.json` (Marshgate Lane), `factory-yards.json`, `housing-detail.json`, the main landscape, and T12c/T14/T15 files.
- **Not changed in the ranges:** storeys, heights, roofs or facades of any range.
- **Not re-registered:** `high-street-24`, or any range other than the seven.

## Unsure

- The EPFL footprints were used as the reading of the printed building line. They match the print to within about 0.2 m where I checked, but I did not compare every metre by eye.
- 01's south-west step and porch are read from blurred print.
- 09's length (13.3 m) is a judgement between the OS block length of 13.3–13.9 m and the prior 11.1 m.
- The ~3 m Marshgate Lane offset is measured against EPFL faces on both sides of the lane; I did not check it with strips as T13 did.

## Decisions for the parent

1. In the cascade, rebuild the main landscape, `factory-yards.json` (fixes sites 256 and 397) and the river network (vista start height 1.80 → 1.37 m). Housing-detail does not change.
2. `wall-lane-south` crosses `site419-range-1` by 2 m². Move the path's route points near (−564, 346)–(−565.2, 350) about 1.5 m west in `wall-river-vista.json`, or rule the factory corner wrong. Until then `check_high_street_frontages.py` fails on this one line.
3. Retrace Marshgate Lane between the High Street and about (−842, −99). It is about 3 m west of the printed lane and runs over the P.H. and a 24 m² building opposite. After that, 09 will be built whole.
4. Optionally narrow the High Street at Harrow Wharf (`-24`) by about 0.5 m, or accept the trim.
5. Accept or veto 01's 4.2 m shortening and 09's 13.3 m length.
