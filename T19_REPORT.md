# T19 report: four Lower Lea industrial sites completed on their GeoPackage outlines (924, 1018, 258, 398)

4 October 2026. Branch `worktree-agent-a3974729fa7a985e2`, based on `main` at `d9980e9` (fast-forward; `main` had not moved when I finished). Scratch files are in `/tmp/claude-1000/-home-jic823-book-website/61f71781-342b-470a-9012-cb46325e06a9/scratchpad/t19/` (called `t19/` below).

## What changed and why

| File | Change |
|---|---|
| `data/maps/bromley-gasworks-footprint-alignment.json` | Site 924. The four remaining legacy envelopes retired (`removedBuildings`, each keeping `priorFootprint`, `priorCentre`, `priorAreaM2`, `priorRotationDegrees`); five `additionalBuildings` on their GeoPackage outlines; a new `classifiedOutlines` list; one sentence added to `method`. |
| `data/maps/manure-works-footprint-alignment.json` (new) | Site 1018, modelled on the Bromley register. The three legacy envelopes retired; nine buildings and two chimneys added; Goad F18 registration and its residuals recorded in `goadRegistration`. |
| `data/maps/mill-brush-footprint-alignment.json` | Site 258. Ten `additionalBuildings` for the northern Smith's fibre works; five more records kept, not built, in `heldForRoadRegistration`; `classifiedOutlines`; the old `deferred` entry for 1166/492753/834044/802229 is marked resolved; `method` extended. |
| `data/maps/crown-johnson-footprint-alignment.json` | Site 398. Fifteen `additionalBuildings` on the unmodelled northern Johnson outlines; `classifiedOutlines`; the deferred entry for 125888/861166/948832/236176 is marked resolved; `method` extended. |
| `scripts/build_factory_buildings.py` | One line: the new register is appended to `group_registers`. Nothing else changed. |
| `docs/data/factory-buildings.json`, `docs/data/factory-yards.json` | Regenerated. |
| `data/maps/factory-building-traces.json` | **Not touched.** The 1018 envelopes are retired through the new register's `removedBuildings`. The builder already supports this for any group register, and it moves them into `reclassifiedFeatures` with their reasons. |

### Method common to all four sites

- **Footprints.** Every new footprint is a GeoPackage outline (`reference/historic-building-footprints-2026-09-28/west-ham-buffer-buildings-bng.geojson.gz`). It is used unshifted in the GeoPackage frame, as T6 and T9 did. Touching outlines are merged with a 0.2 m mitred closing, then simplified at 0.15 m; the maximum deviation is written into each record. Supplied holes are kept.
- **Checked against the OS.** Each outline was checked against the OS five-foot 1893 mosaic (`scripts/factory_map_sources.py` `mosaic()`). Only outlines the OS draws shaded (roofed) were modelled.
- **Splitting an outline.** I split an outline only where a Goad insurance plan draws a compartment wall and there is a reason to give the parts different heights or materials. The Goad sheets were registered to the outlines by a similarity fit (below).
- **Evidence strings.** Every added record has `footprintEvidence` (cites the fid and the mosaic), `heightEvidence` and `roofEvidence` (both open with "Explicit estimate") and `functionEvidence`.
  - The function string opens with "Explicit estimate" when the use is my interpretation.
  - It quotes Goad when Goad letters the use ("Manure Shed", "Stable & Loft", "Fibre Machinery", "Off.").
  - It says "no use given" when Goad gives none.
- **Storeys, materials, roofs.** Storey figures, wood/brick colours and the roof mark T come from Goad. "T" is read as tile from the 1926 Goad key (`reference/factory-building-survey/goad-symbol-key-1926.jpg`, a later legend). The renderer draws its standard roof colour regardless.
- **Eaves.** Eaves use the builder's own storey values: 3.8 m for one storey, 5.35 m for one and a half, 6.9 m for two, 10.0 m for three.

### Goad registrations

The geometry source is always the GeoPackage outline. Goad is used to place cuts and the two 1018 chimneys, so its fit matters. Residuals are in `t19/residuals.json`.

| Sheet | Fit | Overlap IoU | GeoPackage vertices to the fitted Goad building edge (median / 90th percentile) |
|---|---|---|---|
| F18, `reference/factory-building-survey/goad-f18.tiff` (not georeferenced before) | Similarity fit maximising the overlap of Goad building colours with fids 1524, 944, 863177: 0.1594 m/px, rotation 20.4° | 0.866 | 0.42 / 1.67 m. Five hand-read corner controls: RMS 2.26 m, max 3.53 m (my reading of corners at 0.16 m/px is the weak part). |
| F3 at 258 | Local refit starting from the regional `goad-f3-marsh` registration; shifted 5.1 m, −3.2 m | 0.894 | 0.40 / 1.20 m |
| F3 at 398 | Same method; shifted 8.0 m, −2.9 m | 0.650 (Goad marks this works "under alterations, July 1893", so its plan differs from the OS) | 0.47 / 2.39 m |

### Site 924, Bromley-by-Bow Gas Works

The legacy envelopes `os-15`, `os-16`, `os-4` and `os-9` are retired and replaced by five records:

| New record | Fids | Replaces | Notes |
|---|---|---|---|
| `b924-eastern-range` | 4790 | west part of `os-15` | `os-15` was a 40 × 35 m rectangle about 6 m north-east of the drawn block, over open yard |
| `b924-boiler-range` | 233453 + 24074 + 198842 | north-east part of `os-15` | Keeps the hole at fid 926100, on which T9's 32 m `stack-924-boiler-photo` stands |
| `b924-north-east-range` | 713151 + 35247 | `os-16` | |
| `b924-garden-house` | 20695 | `os-4` | A house-like building in landscaped grounds |
| `b924-yard-shed-bm17` | 494073 | `os-9` | |

- **Heights** keep the legacy values (3.8 m; 6.9 m for the house) and are labelled as explicit estimates.
- **Gantries.** The two coal gantries (34850 + 459328 and 37343 + 441135) are drawn dotted and stippled, from the retort houses out over the tramway and dock wall. The renderer has no gantry or elevated kind, so they are recorded in `classifiedOutlines` and not drawn.
- **Other classified features:**
  - the unshaded features on the retort-house ends (777740, 851236, 860071);
  - small unshaded compartments;
  - holder column bases;
  - the purifier vessels.

### Site 1018, F.S. Hempleman & Co., Blood Manure Works & Wharf

**Names.** Goad F18 names the works "F.S. Hempleman & Co., Blood Manure Works & Wharf" (lot F.222) and prints "(Admission refused)".

**What was wrong.** The three legacy envelopes stood mostly over open ground:
- about 6 m north of the west range, on the riverside;
- over the gap between the ranges (the OS oval "C", B.M. 15.94).

**What replaces them.** Nine records on fids 1524, 863177 and 944, cut at Goad walls. Material, roof mark and storeys are all from Goad F18.

| Record | Goad | Use | Material | Roof | Storeys |
|---|---|---|---|---|---|
| `b1018-manure-shed-west` | L | Manure Shed, Ovens | wood | T | 1 |
| `b1018-engine-smithy` | K | Engine, Smithy | wood | — | 1 |
| `b1018-stable-loft` | J | Stable & Loft | wood | T | 2 |
| `b1018-stable-annex` | unlettered (fid 863177) | — | wood | — | 1 |
| `b1018-raw-material-store` | F | Store for raw material, Ovens | wood | — | 1½ (figure read as "1-2" or "1½") |
| `b1018-manure-shed-east` | E + D + G | Manure Shed / Ovens / Cartway | wood | — | 1 |
| `b1018-brick-range-c` | C | — | brick | — | 2 |
| `b1018-store-office` | B | Store & Off. | brick | — | 3 |
| `b1018-cart-shed` | A | Cart Shed | wood | — | 1 |

**Chimneys.** Two chimneys stand on the Goad chimney symbols, placed through the fit and stored by `parentBuildingId` + `localPosition`:
- `stack-1018-ovens-d`: printed **40'**, so 12.19 m, `mappedHeightFeet` 40.
- `stack-1018-engine-l`: no printed height; 12.19 m is an explicit type-based estimate.

**Railway.** Fid 944 was first clipped 6.1 m off the LT&SR centreline, which removed 20.9 m² at its east end. The 6.1 m is:
- the 4 m crest half-width;
- plus the 0.5 m formation band;
- plus T15's 1.5 m wall gap;
- plus 0.1 m.

Every 1018 render polygon is now at least 6.10 m from the centreline. I simulated T15's rule (`footprint.buffer(1.5, mitre)` against `line.buffer(4.5)`): no new formation conflict.

### Site 258, Augustus Smith brush and fibre works

**What is added.** The northern Smith's fibre works: OS "Brush & Fibre Works"; Goad F3 lots 817–846. Ten records:
- Fid 1166 is cut at Goad F3 walls into five parts:
  - north room 817 (1 storey);
  - west wooden range 824/828 (wood, 1 storey);
  - two-storey block (keeps the hole of chimney base 1073893, under the existing 50 ft `stack-258-1149-1128`);
  - Fibre Machinery shed (wood, 1 storey);
  - east range on Marshgate Lane (2 storeys, "Disused Eng.").
- Single-outline records:
  - boiler house 492753 (Goad grey, so `metal`; hatched boilers);
  - south range 11876;
  - house 842 (105760, "D", 2 storeys);
  - cottage 844 (386554, "D", 1 storey);
  - rooms 846 (44759, "1=2", so 1.5 storeys).

**Water clip.** The west wooden range overlapped the drawn Pudding Mill river polygon by 1.45 m². I clipped off the 3.09 m² of it that lies within 0.15 m of that polygon, and the record says so. Without the clip, `check_factory_buildings.py` fails on it (more than 1 m² in water).

**Held, not built.** Five records sit in `heldForRoadRegistration`: the 820 room of 1166, office 753274, and 587186, 808876, 834044. The registered Marshgate Lane corridor covers more than half of each, so the builder would clip them to nothing or to slivers. Three would have had no render polygon at all, which `check_factory_buildings.py` rejects. See "Decisions" item 1.

### Site 398, Crown Works / Johnson chemical works

Fifteen records on the unmodelled northern outlines.

**Storeys and materials:**
- 79794 is cut at a Goad F3 wall into a two-storey wooden block and a one-storey wooden range.
- Goad gives one storey for: 737100 and 115749 (wood); 885016 (wood); 93040, 250214 and 60939 (brick).
- 236176 is 1½ storeys (Goad prints both 1 and 2 in it).
- Explicit one-storey estimates, because Goad shows only an outline, blank ground or illegible figures: 598184, 641316, 545686, 786213, 125888, 861166.

**Classified, not modelled:**
- **105484, 506142, 832905, 992504.** These lie inside the 398 parcel, but Goad F3 letters them "Bakehouse, Oven, Off. & Stores" and draws a gangway ("Gang.") from them into the Du Barry patent food factory, site 257. Modelling them under 398 would misattribute them, and modelling them under 257 is outside this task's sites. See "Decisions" item 2.
- 948832: a circle, read as plant.
- Fittings under 11 m².
- A Goad chimney symbol with neither a height nor an OS base.

## Numbers before and after

### Gap audit by site

From `scripts/footprint_gap_audit.py`, run as a scratch copy (`t19/gap_audit_copy.py`) that writes to `t19/audit-*`. The rows are uncovered footprints counted to a site (coverage under 30 %), as count / m².

| Site | Before | After |
|---|---|---|
| 924 | 229 / 3,270 | 229 / 3,270 |
| 1018 | 2 / 1,564 | **0 / 0** |
| 258 | 12 / 2,218 | **6 / 158** |
| 398 | 27 / 1,112 | **13 / 197** |
| District (started zones) | 7,409 / 210,911 m²; 202 over 100 m² | 7,393 / 206,439 m²; 195 over 100 m² |
| Model polygons without footprint support | 116 | 115 (`site1018-os-2` gone) |

My baseline does not match two of the brief's figures (924: 3,079; 258: 2,072). Today's audit on unchanged `main` gives 3,270 and 2,218. The 1018 and 398 figures do match.

### Uncovered area inside each parcel

The per-site count above cannot register 924's improvement: an outline at 56–70 % cover counts as "covered". So I also measured the uncovered footprint area inside each parcel, using the audit's own cover polygons (`t19/parcel_metric.py`).

| Site | Before (m²) | After (m²) |
|---|---|---|
| 924 | 4,129 (1,517 with the purifier fix below) | 3,879 (1,266) |
| 1018 | 1,618 | 25 |
| 258 | 1,957 | 369 |
| 398 | 1,087 | 221 |

At 924, cover of 713151, 35247, 20695 and 494073 rose from 0.56–0.70 to at least 0.70.

### A sign error in the audit's purifier rows

**`footprint_gap_audit.py` mirrors purifier rows.**
- It lays `purifierBank` vessels along (cos r, −sin r).
- `docs/factory-buildings.js` draws them along (cos r, sin r).

So the 44 fitted vessels at 924, about 2,234 m², are counted as uncovered although the scene draws them on the OS vessels. A scratch variant with the renderer's sense (`t19/gap_audit_fixed.py`) puts 924 at **201 / 1,036 m²** before and after. I did not change the audit: it is not in my file list.

### What is left uncovered

- **924 (1,036 m² with the fix):**
  - the two gantries, 349 m²;
  - unshaded retort-end features, 70 m²;
  - a gangway, 25 m²;
  - a framed box, 21 m²;
  - small compartments;
  - about 170 holder column bases of 2–4 m².
- **1018 (25 m² of area):** the 20.9 m² railway hold-off strip, plus slivers.
- **258 (158 m²):**
  - the four held outlines on Marshgate Lane (587186, 753274, 808876, 834044);
  - 802229, a 1.3 m-wide diagonal "fibre" feature, classified;
  - 1075308, a corn-mill symbol belonging to site 257.

  The area measure is higher (369 m²) because the builder clips about 230 m² of the lane-side roofs to the misregistered street corridor.
- **398 (197 m²):**
  - the Du Barry bakehouse outlines 105484 and 506142;
  - small fittings;
  - the circle 948832.

**Side effect.** "Outside-sites" grows by 6 footprints / 67 m² at about (−145, 377). Registering buildings at 1018's east end widens the audit's 60 m "started" zone there, as T6 saw at 865.

## Structural diffs

Script: `t19/fbdiff.py`. Compared against `t19/rebuild-base/` (the committed inputs rebuilt clean) and against the committed files (`t19/base-data/`).

### `docs/data/factory-buildings.json`

- **Top-level keys:** unchanged.
- **`sources.author-os-footprints-1891-96.method`:** text grows, 8,453 → 10,090 chars; this is the three `method` additions plus the new register.
- **`reclassifiedFeatures`:** +7 (`site924-os-4`, `-9`, `-15`, `-16`; `site1018-os-1`, `-2`, `-3`).
- **`footprintAlignment.groupRegisters`:** + `manure-works-footprint-alignment.json`.
- **`counts`:**
  - ranges 728 → 760;
  - chimneys 89 → 91;
  - chimneysWithMappedHeights 20 → 21.
- **`sites`:** only `buildingCount` changes, at 258, 398, 924 and 1018.
- **`buildings`:** +39, −7, at sites 258, 398, 924 and 1018 only. Existing order is kept, and no existing building changes against the rebuilt base.
- **`structures`:** +2 (the 1018 stacks); existing order kept.
- **Geometry audit** (`reference/factory-building-survey/review/geometry-audit.json`, my local copy):
  - the `site1018-os-2`/`-3` overlap is gone;
  - new render adjustments are confined to my records: four 258 lane-side street trims (49–76 m² each), a 2.2 m² trim on `b398-lane-building`, and a 4.4 m² shared-wall partition between `b924-eastern-range` and `b924-boiler-range`;
  - water intersections are unchanged.
- **Against the committed file only:** three more buildings differ: `site256-range-1`, `site947-range-2` and `site789-os-2` (street trims). This is **pre-existing**. A clean rebuild of unchanged `main` produces exactly the same three changes, because the committed file predates T13's road retrace.
- **Determinism:** the builder run twice gives identical bytes.

### `docs/data/factory-yards.json`

The builder is unchanged. Two runs give identical bytes.

- **Geometric change only at the four sites:**

  | Site | Area (m²) | Lost (m²) | Gained (m²) | Other |
  |---|---|---|---|---|
  | 258 | 2,564 → 936 | 1,629 | 0 | wear route 1 → 0 |
  | 398 | 3,332 → 2,416 | 916 | 0 | 2 → 1 stock groups (`barrels`); route rerouted |
  | 924 | 202,913 → 203,419 | 261 | 768 | the strips the old envelopes cut out are returned to yard |
  | 1018 | 2,201 → 1,604 | 1,612 | 1,015 | yard now between the new ranges; 0 → 1 stock group (`crates`) |

- `counts.wearRoutes` 33 → 32 (the 258 route).
- `buildingEdges`: 374 → 382, all the changed rings at the four sites.
- **25 other yard sites change bytes only:** symmetric difference 0.00 m² (ring-start churn, as T16 found).
- **`softEdges`** (11,045 → 10,820):
  - the net change is at the four sites;
  - about 3,500 points elsewhere are re-sampled, not moved. The builder samples each boundary from its ring start, so ring-start churn shifts the sample positions along unchanged edges.
- `tracks`, `workingGrids`, `bounds` and evidence are unchanged.

## Checks with pass counts

- **Builder assertions** (polygon validity, ids, water, overlaps, holders): pass. `waterChecks` stays at 5. `overlapChecks` goes from 5 to 4.
- **`python3 scripts/check_factory_buildings.py`:** pass, "91 registered chimneys …; Factory checks passed: 64 sites, 760 ranges".
- **`python3 scripts/check_factory_yards.py`:** pass, "91 valid yard surfaces, 32 clear wear routes, 176 stock groups".
- **`npm test`: 16/18. The baseline in this worktree was 18/18**, once I linked the git-ignored spot-height mosaics and the book PDF.
  - **`check_flood_demo.mjs`:** "Stale source docs/data/factory-buildings.json". This is the expected stale hash; `flood-demo-1900.json` stores a hash of the factory file. I did not edit hashes.
  - **`check_railway_embankments.mjs`:** "embankment vertices inside building footprints" for the nine `b1018-*` records, with the LT&SR (1–55 vertices each).
    - Cause: the committed `main-landscape-1900.json` still holds the LT&SR fill 1.5 m off the *retired* envelopes, which stood 10.5–14 m from the centreline. The new outlines stand 6.1–7.6 m from it.
    - After the landscape cascade, `build_main_landscape.py`'s `RAIL_GAP` rule will cut the fill 1.5 m off the new footprints.
    - I checked that rule on every 1018 footprint: none comes within the conflict band (smallest clearance 4.60 m against 4.5 m), so the check's "3 recorded conflicts" assertion is not affected.
    - This is a stale-cascade failure. Data ownership stays with the landscape builder.
- **Factory-related Python checks** (55 run; `t19/pychecks-*.json`). Same result on committed `main` and on T19: 26 of 55 pass, with identical failure messages.
  - The 29 failures are pre-existing on `main`. Most stop at `site924-os-17` (T9) or `site256-range-1` (T13) in the shared before-file comparison; others are street and yard assertions.
  - **Masked assertions my registers will trip once those are fixed:**
    - `check_mill_brush_alignment.py` asserts `not r.get('additionalBuildings')`.
    - `check_crown_johnson_alignment.py` asserts exactly 10 site-398 buildings; there are now 25.

    Both checks encode "this pass added nothing". They need a one-line update each, outside my file list.
  - I excluded checks that write into the main checkout's `reference/` through symlinks (`check_district_streets`, `check_housing_frontages`, the historic-elevation and drainage checks).
- **My worktree's `reference/`.** It is a real folder of per-entry symlinks into the main checkout, with local copies of `factory-building-survey/review/` and `footprint-model-alignment/verified-*`. So the builder's `geometry-audit.json` and the checks' `verified-*.json` were written locally, not into `/home/jic823/book_website`.

## Render verdict per camera

Renders are at 1280 × 720:
- "after": `t19/renders-after/<label>.png`, served from this worktree on 4202;
- "before": `t19/renders-before/<label>.png`, served from `main` on 4173.

I opened every image.

| Camera | Verdict |
|---|---|
| `t19-924-overhead` | The eastern range and boiler range now sit on the drawn block, with the boiler stack in the open well. The narrow north-east range has moved onto its outline. The retort houses and `os-17` are unchanged. No stray yard gaps. |
| `t19-924-low` | Before: one big low envelope in front of the stack. After: the eastern range in front and the boiler range behind it with the stack. Nothing pokes through a roof. |
| `t19-924-house-low` | The garden house has moved about 3 m onto its outline. Otherwise the view is unchanged. |
| `t19-1018-overhead` | Before: two long envelopes partly over the riverside. After: two broken ranges along the railway, with the taller stable and store blocks and a cinder yard between the ranges. |
| `t19-1018-low` | The dark wooden ranges are visible: the west manure shed in the foreground, the two-storey stable and loft with its annex, and the east sheds beyond, with a chimney at the far end. The brick store at the east end is too far off to read. The west shed's pad reads slightly above the river wall, which was already the case. |
| `t19-1018-from-railway` (extra) | From the LT&SR formation: the new ranges stand close below the line. Their walls are partly hidden by the stale embankment slope until the landscape cascade cuts the fill back. This is the visual counterpart of the `check_railway_embankments` failure. |
| `t19-258-overhead` | The northern fibre works now fills the formerly empty triangular yard between the Pudding Mill river and Marshgate Lane. **The lane-side roofs stop at the drawn road edge, about 4–6 m short of the OS frontage** (road registration issue; see "Decisions" item 1). |
| `t19-258-low` | A long two-storey brick range along the lane, gable roofs, and the dark metal boiler house at the right. No floating or buried parts are visible. |
| `t19-398-overhead` | The open northern half of the Crown/Johnson parcel is now built up as on the OS. The new blocks sit beside the existing site-398 ranges without overlaps. |
| `t19-398-low` | A courtyard of one- and two-storey brick and wooden ranges around a yard with a barrel stock group. The lane-corner building is at the right. |

**OS overlays** (old red, new blue, render polygons cyan, GeoPackage outlines green, held 258 records orange, chimneys magenta):
- `t19/overlay-924-east.png`
- `t19/overlay-924-south.png`
- `t19/overlay-1018.png`
- `t19/overlay-258.png`
- `t19/overlay-398.png`
- `t19/goad-warp-1018.png`: the Goad F18 fit, with the cut lines and chimneys.

## Smoke differences

I ran a scratch copy of `scripts/review_smoke.py` (`t19/smoke_copy.py`) with both waits raised to 900 s: `t19-four-sites --compare main-after-cascade --url=http://127.0.0.1:4202`. Result: **0 page errors**. The screenshot timed out, which the script treats as a courtesy. 15 differences:

| Difference | Explanation |
|---|---|
| `factoryBuildings.ranges` 728 → 760 | +39 − 7 |
| `siteRanges` 924 33 → 34; 1018 3 → 9; 258 7 → 17; 398 10 → 25 | Per-site record changes above |
| `chimneys` 89 → 91, `chimneysWithMappedHeights` 20 → 21, `siteChimneys.1018` null → 2 | The two 1018 stacks |
| `chimneyTops` | +`stack-1018-engine-l`, +`stack-1018-ovens-d`; every existing entry identical |
| `roofPlanes` 1702 → 1768, `windows` 9997 → 10236 | The new roofs and walls |
| `factoryYards.wearRoutes` 33 → 32 | The 258 yard route |
| `mainLandscape.seatedObjects` 817 → 843 | Net new factory records seated on a non-zero ground level |
| `triangles` / `reflection.triangles` +4,978 | Geometry of the above |

Nothing outside the four sites changed.

## What I did not do

- I did not run the landscape, river-system, terrain or flood cascade, or `export_geopackage.py`. I changed no roads, infrastructure, landscape or JS.
- I did not model:
  - the gantries (no renderer kind);
  - the Goad boilers or tanks inside roofs;
  - the Goad chimney at Johnson's lot 564 (no height, no OS base);
  - the Du Barry bakehouse outlines;
  - the five held 258 records.
- I did not fix `footprint_gap_audit.py` (purifier sign) or the two site checks (`check_mill_brush_alignment`, `check_crown_johnson_alignment`). Both are outside my files.
- I did not use Goad to *change* any GeoPackage exterior. It only places internal cuts and the 1018 chimneys.

## What I was unsure of

- **Goad figures:**
  - 1018 B's "3" (storeys?) and F's "1-2"/"1½";
  - the "2" on the 258 north dwelling (now held).
- **The F18 controls.** Hand-read corner controls disagree by up to 3.5 m. The colour-overlap fit itself is tighter (median 0.42 m).
- **Whether 587186/808876/834044 belong to Smith's works.** They have separate Goad lot numbers (813, 815) and lie in the 258 parcel only.
- **398 "under alterations".** Several outlines the OS shades are blank or outline-only on Goad, which suggests building work between the surveys. I modelled them because the OS, the geometry authority, shows them roofed.
- **The Goad "COOPERS" lettering** at 398 may name a tenant or department rather than describe the block I attached it to.

## Decisions for the reviewer

1. **Marshgate Lane registration at 258.**
   - *My choice:* model the lane-side records and let the builder clip them to the registered corridor (about 230 m² clipped). Hold the five records the corridor would erase in `heldForRoadRegistration`.
   - *Alternative:* re-register the Marshgate Lane trace in `data/maps/district-road-traces.json` first. Here its centreline runs along the building frontage, 4–6 m west of the OS street. Then move the held records into `additionalBuildings`. This is a roads task.
2. **Du Barry bakehouse (105484, 506142, 832905, 992504).**
   - *My choice:* classify, not model. They are in the 398 parcel but are Du Barry's (site 257) on Goad.
   - *Alternative:* add them to the mill-brush register under siteId 257 in a follow-up.
3. **Retire-and-replace at 924, instead of T9-style `buildings` corrections.**
   - *My choice:* retire and replace. A correction cannot replace the legacy `heightEvidence` ("Inferred storey count, not supplied by OS."), and the brief requires "Explicit estimate". Replacing also lets `os-15` become two records.
   - *Cost:* the four ids change. Prior geometry is kept in each new record (`priorModelId`, `priorFootprint`, `priorRotationDegrees`, `priorFootprintEvidence`, `priorHeightEvidence`) and in `reclassifiedFeatures`.
   - *Alternative:* `buildings` corrections that keep the ids, with legacy height text.
4. **1018 railway hold-off.**
   - *My choice:* clip 20.9 m² of fid 944 at its east end to keep 6.1 m from the LT&SR centreline.
   - *Alternative:* keep the full outline and accept a recorded formation conflict.
   - **For the author:** the OS shows these works directly beside the tracks with no embankment hachures, but the traced formation is 5.5 m high. After the cascade the scene will show a retaining wall up to about 4.8 m high 1.5 m from the sheds. If the line was near grade here, the formation height, not the buildings, is what should change.
5. **Goad-based splits.**
   - *My choice:* split 1524, 944, 1166 and 79794 at Goad walls (1018 into 9 records, 258's 1166 into 5).
   - *Alternative:* one record per outline at a single height. Fewer records, but the two-storey stable, the brick store and the two-storey fibre block would be lost.
6. **Two 1018 chimneys from Goad.**
   - *My choice:* add both; one has a printed 40 ft height, the other an estimated one.
   - *Alternative:* drop `stack-1018-engine-l`, which has no printed height.
7. **Gantries at 924.** They need a new structure kind in `docs/factory-buildings.js` (an elevated deck on posts). The register records them with evidence, ready for that.
8. **Audit fix.** Correct the purifier sense in `footprint_gap_audit.py`. 924's audited gap would fall from 3,270 to 1,036 m².
9. **Site checks.** Update `check_mill_brush_alignment.py` (allow `additionalBuildings`) and `check_crown_johnson_alignment.py` (count 25) when the pre-existing failures in front of those assertions are fixed.

## Regeneration on `main` after merging

```sh
python3 scripts/build_factory_buildings.py   # reproduces docs/data/factory-buildings.json (+3 pre-existing street-trim changes if main still predates them)
python3 scripts/build_factory_yards.py        # about 5 minutes
```

Then run the cascade so the hashes and the LT&SR hold-off catch up:
- `build_river_system.py`;
- `build_main_landscape.py`;
- the terrain and flood builders;
- `build_scene_manifest.py`;
- `export_geopackage.py --verify`.

Files left stale: `main-landscape-1900.*` (also the embankment hold-off at 1018), `river-system-1900.json`, `terrain-1900.json`, `flood-demo-1900.json` and the GeoPackage export.
