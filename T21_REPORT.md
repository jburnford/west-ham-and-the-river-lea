# T21 report: the drawn ground on the OS spot heights

4 October 2026. Branch `worktree-agent-ad3ea3861f3c486ad`, worktree `/home/jic823/book_website/.claude/worktrees/agent-ad3ea3861f3c486ad`. Based on `main` at `116c0ae` after `git merge main` (includes T20 `cd55517`). Scratch: `/tmp/claude-1000/-home-jic823-book-website/61f71781-342b-470a-9012-cb46325e06a9/scratchpad/t21/` (called `t21/` below).

## Bottom line

- **I measured all 380 OS five-foot spot heights and bench marks in the core box against the drawn ground.** 214 are spot heights on the ground; 86 are bench marks; 80 sit on structures.
  - Before: the ground readings had a median of −1.81 m (drawn minus OS) and a 90th-percentile error of 8.06 m.
  - **Two separate problems** cause this:
    - **East of the Lea and Bow Creek** (the marsh, the works, the streets): the drawn ground was 1–3 m low at the yards, streets and railway side. The cause was builder rules (findings below).
    - **The Bromley/Bow terrace west of the Lea, and the High Street towards Bow Bridge**: the drawn ground is the old flat floor at about 0 m, while the OS gives 15–36 ft (2.4–9.0 m scene). This is 2–9 m too low across about 0.6 km².
- **I fixed the east and stopped at step 2 for the west** (decision 1). Raising the terrace means re-seating hundreds of buildings, building a new bank along the west side of the Lea, re-levelling Bow Bridge and the High Street, and changing the flood picture. That is far more than a ground-and-road task, and it needs the author.
- **East of the Lea, the drawn ground now honours the OS.** I applied 98 ground readings:
  - median drawn − OS **0.00 m**;
  - 90th percentile of |drawn − OS| **0.20 m** (before: −0.22 and 1.49);
  - **91 of 98 within ±0.6 m** (before: 72).
  - The other 7 are listed exceptions, each with its reason (table below).
- What changed on the ground:
  - The premises pads take their OS yard levels: manure works 1018 −0.1 → 1.1–2.7 m on the yard readings; Three Mills Distillery −0.06 → 2.29 m; the gas works on its own readings.
  - The streets take their OS street levels.
  - The marsh between works is corrected to the OS marsh readings and interpolated between them.
  - Abbey Road meets the Woolwich branch rail top at the OS level crossing (13.5 ft, 1.88 m). The short deck is gone.
- **The LT&SR at-grade section (chainage 300–700) now sits within 0.21 m of the drawn ground** 7–10 m either side (before: 1.2–3.1 m). The 232 m retaining wall that held the bank off site 1018 is no longer needed and is gone.
- **Checks**:
  - `npm test` **21/21**: 20 plus a new `check_os_ground_levels.mjs`. One stored sample was refreshed (`check_road_bridges.mjs`, explained below); no assertion was weakened.
  - Builders deterministic.
  - Network-mesh steps 6 → 6; core steps 52 → 18.
  - Smoke: 0 page errors, 27 differences, all explained.

## Step 1: measurements (before)

Tool: `t21/measure.mjs` builds the drawn ground exactly as the page does: `terrainDetails().level`, which is the core tile, then the highest drawn landscape mesh, then the level fields, as in `check_tram_rails.mjs`. It also builds the real road meshes from `infrastructure()`.

For every reading in the core box it compares:
- street readings with the drawn road surface;
- all other readings with the drawn ground.

Conversion: scene y = (ft − 1.3) × 0.3048 − 1.83544.

How the readings are classified (`data/maps/os-ground-levels.json`, field `category`):

| Category | Settings | Should equal the drawn ground? |
|---|---|---|
| ground (214) | spot heights: street 147*, yard, marsh, open_ground, embankment_foot, other/unset (towing paths, works ground) | yes: the road surface for streets, the ground otherwise |
| mark (86) | every OS bench mark (`type bench_mark`) | no: it is cut on a wall, post, building or bridge, normally 0.2–1.5 m above its ground; used as a check |
| structure (80) | spot heights with setting bridge, building, wall_top, embankment_top, railway | no: deck, wall-top, bank-top or rail levels |

\* Some street readings are not on a drawn street (marsh tracks, footpaths). They are ground, and are applied as marsh. Two settings were overridden with reasons: `sh_538907_182862` "road north of railway" (reader setting `railway`) counts as ground, and the "walled band" reading counts as a structure.

Zones are defined in the register's `zones`:
- west strip: x < −628, the Bromley/Bow terrace;
- High Street: within 45 m of its centreline;
- Three Mills / Mill Meads: x −628..−300;
- Abbey Mills: x −300..120, z < 340;
- Channelsea east: x ≥ 120;
- LT&SR corridor: within 35 m of the line;
- Bromley gasworks: x < −150, z > 620;
- Abbey marsh south: the marsh south of the LT&SR.

**Residuals before (drawn − OS, metres; ground readings; "applied" = the ones T21 applies):**

| Zone | ground n | median | p90 abs | within ±0.6 | applied n | median | p90 abs |
|---|---:|---:|---:|---:|---:|---:|---:|
| West strip (Bromley/Bow) | 93 | −7.52 | 8.39 | 1 | 0 | – | – |
| High Street | 13 | −2.36 | 4.17 | 1 | 3 | −1.42 | 2.19 |
| Three Mills / Mill Meads | 22 | −0.62 | 2.30 | 11 | 19 | −0.48 | 1.35 |
| Abbey Mills | 11 | −0.06 | 2.12 | 8 | 9 | 0.00 | 0.53 |
| Channelsea east | 20 | −0.01 | 0.98 | 16 | 19 | −0.02 | 1.06 |
| LT&SR corridor | 12 | −1.38 | 1.94 | 3 | 12 | −1.38 | 1.94 |
| Bromley gasworks | 29 | −0.02 | 1.54 | 21 | 23 | −0.02 | 0.54 |
| Abbey marsh south | 14 | −0.22 | 0.61 | 12 | 13 | −0.20 | 0.41 |
| **All** | **214** | **−1.81** | **8.06** | **73** | **98** | **−0.22** | **1.49** |

Bench marks before: median 2.78 m above the drawn ground in all zones. West of the Lea they stood 7–12 m above it.

Maps (drawn − OS at every ground reading on the OS mosaic; black ring = applied):
- `t21/base/resmap.png` (before);
- `t21/final/resmap.png` (after, with a second panel showing the change in drawn ground);
- `t21/base/gridmaps.png`: the drawn ground, the regional landscape ground grid, which source draws each point, and the main landscape weight.

Per-reading tables: `t21/base/classified.json`, `t21/final/classified.json`.

## Step 2: why (each gap traced to its rule)

1. **The west terrace has no drawn ground.**
   - The main landscape applies only where the regional early-marsh weight (`lower-lea-region/landscape-1900.early-weight.f32`) is above 0.
   - West of about x −700 that weight is 0, and no landscape mesh covers it. `level()` falls through to `riverNetwork.marshLevel()`, which returns **0** outside the network grid, and the page draws the river network's flat `baseGround` there.
   - Yet the regional ground grid already holds the terrace: at (−900, 600) it gives 7.86 m against OS 33.7 ft (8.04 m). The detailed scene simply never draws it.
   - The High Street west of Bow Creek and the north-east corner by Abbey Road (support weight 0.01 at the level crossing) have the same cause.
2. **Premises pads** (`build_main_landscape.py`, "premises levels").
   - A pad took OS yard readings only through the regional `laterSurfaceLayers` kind-11 features, matched by site name. Only three sites had any: Howard & Sons, St Leonard's Wharf and the Gas Works.
   - Every other pad was `max(-0.1, median(early-marsh ground around the outline))`. So the manure works 1018 sat at −0.1 against its yard reading of 13.4 ft (1.85 m), and Three Mills Distillery 419 at −0.06 against its 14.8–14.9 ft (2.28–2.31 m).
   - The 1018 B.M. 15.94 ft is on a wall (crane oval), 2.5 ft above the yard spot height, so the yard level is 13.4 ft, not 15.94.
3. **Streets.**
   - Street corridors took readings only from the regional kind-10 features: 6 streets and 9 readings.
   - The other 21 OS street readings on drawn streets were never used. These include Abbey Road at the level crossing, Abbey Lane's six marsh readings, Three Mills Lane, the High Street at Pegs Hole and St Thomas, and Marshgate Lane.
   - A street reading was also used as the corridor ground, not as the road surface, so roads were drawn 0.065 m high.
   - The bank band (within 14 m of the regional shoreline) drew the river bank crest across street corridors. For example, Abbey Lane by the Channelsea was lifted to 1.9 m against its OS 9.5 ft (0.66 m).
4. **The marsh.**
   - The marsh is the regional early-marsh ground (1848–51 low-lane proxies plus later anchors), sampled at 10 m. Where it is supported it matches the 1890s marsh readings within 0.1 m.
   - It misses the made or raised ground near the works and railway. Examples: "south of railway" 10.7 ft against −0.56 drawn; the LT&SR bank foot 7.5–7.9 ft, 0.6–0.8 m low; Mill Meads between the drains 8.4–9.7 ft, 0.4–1.1 m low; the marsh footpaths 0.3–0.7 m low.
5. **`build_historic_elevation.py` reads spot heights, but they do not reach the drawn ground.** Three reasons:
   - It uses 13 hand-picked controls (`terrain-epochs.json` `controlIds`) in four zones.
   - It sets its weight to zero within 8 m of every road, site, building, railway, sewer and drain, and within 23 m of every river (`protections`). Two of its 13 controls have applied weight 0.
   - Its result reaches `build_main_landscape.py` only as the "old" height (`old_historic`). Wherever the regional weight is 1, `blend_surface` replaces that height completely with the regional `base()`. So inside the marsh envelope its spot heights have no visible effect.
6. **Road elevation profiles.** Only Manor Road (drainage crossing) has one (`manor_road.py`). Abbey Road had none, and no street reading was in reach, so it stayed at marsh level (−0.07) under the T20 deck.
7. **River-system bands.** No systematic error. River-system vertices changed in only 118 places (max −0.28 m).

## What changed and why

### New register `data/maps/os-ground-levels.json`, from `scripts/prepare_os_ground_levels.py`

- All 380 readings: value, scene level, position, zone, category, and support weight. It also carries:
  - a **use**: `premises` 19, `street` 21, `marsh` 58, `none` 282, the last always with a reason;
  - an **exception** text for the 7 applied readings still beyond ±0.6 m.
- The script holds the rules: street within half-width + 6 m of a drawn street; premises within 1.5 m of a padded site outline. It also holds 15 per-reading decisions, each with its evidence.
- It is deterministic and re-reads `reference/spot-heights/heights.geojson`.
- The rule I am least sure of is the not-applied west: the 93 west-strip ground readings and the 10 High Street readings with support below 0.9 (decision 1).

### `scripts/os_ground_levels.py` (new) and `scripts/build_main_landscape.py`

- **Premises pads.**
  - A site with OS yard readings takes them: level with one reading, or their inverse-distance surface (power 2, 3 m softening) with several. Each reading is honoured, and the pad is level where the readings agree.
  - Pads beside a railway the OS draws at grade also take the ground the railway level register implies there: formation − 0.1 m, 9 m from the line, every 20 m (`rail-side` controls). The OS draws no cutting or bank hatching there, so the yard meets the line.
  - Prior values are kept in `priorGroundSceneY`/`priorMethod`.
  - Pads that changed: 419 Three Mills Distillery −0.06 → 2.29; 1018 Manure Works −0.10 → 2.12 (median; surface 1.1–2.7); 1125 Oil & Stearine −0.10 → 1.20 (rail-side only, no yard reading); 924 Gas Works 3.00 → 2.79 (median; now a surface through its 14 readings and the rail side, 2.5–3.3 inside the works, falling to rail level along the LT&SR fence).
  - Unmeasured pads now take the median of the corrected marsh around them: 253 −0.03 → 0.10, 560 1.13 → 1.28, 561 0.98 → 1.20, 562 0.13 → 0.15, 965 0.17 → 0.20.
- **Building seating.** `docs/main-landscape.js` gains `premisesLevel()`, the same inverse-distance surface. A building on a multi-reading pad is seated at its own centre. This is data-driven; no site IDs appear in JavaScript.
- **Streets.**
  - Each corridor takes the regional and the register street readings.
  - Street readings are road-surface levels, so the corridor ground is 0.065 m below them. This also changes the 9 regional readings by 6.5 cm.
  - Inside a street corridor with its own level, the bank band no longer draws the river bank crest across the street. Within 3 m of the shoreline only the bank face remains. Inside the river-network tidal outline the street takes the regional water mask, as the wall fill already did.
  - Abbey Lane's graded deck approach (T3) and footpath stubs (T11) keep their own rules.
- **Marsh correction.**
  - The regional early-marsh ground plus a correction to the 58 marsh readings and 114 rail-side points. The correction is a Gaussian-process mean of the residuals (length 40 m, noise 0.1 m), solved separately in each dry compartment between the rivers (field ditches do not divide), and clipped to the compartment's residual range.
  - It fades to nothing about 100 m from the readings and over 60 m outside the core box, and is applied east of x −628 only.
- **Support.** Within 30 m of an applied reading outside the early-marsh support, the landscape applies, feathered over 20 m. This adds 462 field cells, mostly the Abbey Road level crossing, St Mary's Abbey site and the river-edge readings.
- **Output.** `osGroundLevels` is recorded in `main-landscape-1900.json`, and the register is a hashed input.

### Level crossing: `scripts/build_infrastructure.py` and `data/maps/railway-levels.json`

- A street the railway register marks `osForm: "level crossing"` (Abbey Road on the Woolwich branch, chainage 167.5–179.7) is no longer an opening. The line runs through at its formation and no deck is drawn. The road surface meets the 13.5 ft rail top.
- The register's evidence text is updated, with the T20 text kept as `priorEvidence`. **No railway level, route or footprint changed.**

## Residuals after

| Zone | ground n | median | p90 abs | within ±0.6 | applied n | median | p90 abs |
|---|---:|---:|---:|---:|---:|---:|---:|
| West strip (Bromley/Bow) | 93 | −7.52 | 8.39 | 1 | 0 | – | – |
| High Street | 13 | −1.95 | 4.17 | 3 | 3 | 0.00 | 0.01 |
| Three Mills / Mill Meads | 22 | 0.00 | 2.14 | 14 | 19 | 0.00 | 1.11 |
| Abbey Mills | 11 | 0.00 | 2.01 | 9 | 9 | 0.00 | 0.07 |
| Channelsea east | 20 | 0.00 | 0.12 | 19 | 19 | 0.00 | 0.10 |
| LT&SR corridor | 12 | 0.02 | 0.09 | 11 | 12 | 0.02 | 0.09 |
| Bromley gasworks | 29 | 0.00 | 1.45 | 22 | 23 | 0.00 | 0.19 |
| Abbey marsh south | 14 | 0.00 | 0.03 | 13 | 13 | 0.00 | 0.02 |
| **All** | **214** | **−1.24** | **8.06** | **92** | **98** | **0.00** | **0.20** |

East of the west strip (121 ground readings, including the 10 unapplied High Street ones): median 0.00, p90 2.25, 91 within ±0.6 m. The p90 is set by the unapplied and structure-context readings listed next.

Bench marks east of the west strip now stand a median 0.6–1.5 m above the drawn ground, by zone. That is plausible for marks on walls and posts. Four stand below it, all within 0.09–0.90 m:
- 1018 B.M. 15.94 (position uncertain), 0.09 m;
- a fence post at the gas works edge (20 m mesh), 0.90 m;
- a fence-line mark on the marsh, 0.09 m;
- the gateway mark on the gas works ramp road, 0.60 m.

**Every applied reading still outside ±0.6 m** (`exception` in the register):

| Reading | Zone | OS ft (scene) | before | after | Reason |
|---|---|---|---:|---:|---|
| sh_538304_182814 | Three Mills | 16.2 (2.71) | −2.53 | −2.25 | Three Mills Lane at the Lea east bank. The bridge deck (2.2 m; OS bridge 21.2 ft = 4.23 m) ends 25 m short of the drawn water, so the lane crosses water and the bank face rises from it. Bridge structure: decision 3. |
| sh_538279_182756 | Three Mills | 15.2 (2.40) | −1.33 | −1.10 | Bank top 1.6 m from the Lea water. The model's earth bank face (T11/T14) stands where the OS implies a quay edge. |
| sh_538459_183075 | Mill Meads | 9.7 (0.73) | −1.12 | −1.12 | Between two parallel drains, inside the drawn ditch polygons (native drain section kept). |
| sh_538458_183000 | Mill Meads | 8.7 (0.42) | −0.76 | −0.76 | Same. |
| sh_538508_182732 | Three Mills | 15.5 (2.49) | −0.79 | −0.79 | Distillery corner on the Channelsea edge. The tidal face rises 1:1.5 from the tidal shelf (T11). |
| sh_538412_182627 | LT&SR | 15.9 (2.62) | −0.57 | −0.93 | Gas works pad edge by Bow Creek. The 20 m regional mesh spans the edge with tilted triangles. |
| sh_538735_182518 | gasworks | 6.8 (−0.16) | +0.47 | +0.71 | Same, 4 m outside the 924 outline. |

**Ground readings not applied, east of the west strip** (`use: none`; the full reasons are in the register):

| Reading | OS ft | after | Reason |
|---|---|---:|---|
| 10 High Street readings | 15.3–28.6 | −1.15 to −6.49 | Outside the landscape support towards Bow Bridge (decision 1). |
| sh_538337_183143, sh_538345_183055 | 17.3, 16.9 | −2.42, −2.40 | The Short Wall lane on the Lea river wall, inside the tidal outline. Raising it needs the wall and bank (decision 4). A first attempt drew a 2.6 m cliff at the lane edge (21 new mesh steps) and was reverted. |
| sh_538316_183215 | 17.9 | −1.17 | Short Wall, north of the drawn lane. |
| sh_538462_182436, sh_538592_182437 | 21.1, 14.0 | −1.32, +0.73 | On the gas works road ramp down from the Bow Creek bridge approach (not drawn). |
| sh_538640_182438, sh_538681_182464 | 5.6, 5.6 | +1.94, +2.39 | Marsh-level road outside the works fence, inside the 924 outline. |
| sh_538525_182269, sh_538572_182205 | 16.7, 16.4 | −3.16, −0.91 | Works made ground 6–9 m outside the 924 outline. |
| sh_538851_183160 | 18.9 | −3.69 | Bank-crest level on the strip by the sewer bank. As a marsh control it raised a 3.5 m mound over the mud flats, so it was removed. |
| sh_538886_182938 | 17.3 | −2.01 | Ambiguous figures. Conflicts with B.M. 13.17 ft on the building beside it. |
| sh_538776_182863 | 16.9 | −2.50 | Low confidence, dot not located. 1.7 m above the wharf readings beside it. |
| sh_539156_183134 | 3.4 | +1.68 | Manor Road's local dip under the sewer aqueduct. Not drawn. The marsh correction raised the ground here by 1 m. |

## Structural diffs (against the merged base, `t21/base/data/`)

- `infrastructure.json`: Woolwich branch `crossings` 1 → 0 and `crossingDetails` 1 → 0 (Abbey Road), embankment triangles 9241 → 9310. Nothing else. `housing-detail.json` is byte-identical: infrastructure and housing reached a fixed point in one round.
- `main-landscape-1900.*`. Changed float values (max change):

  | File | Changed values | Range (m) |
  |---|---|---|
  | `core` | 582,817 | −2.55..+2.19 |
  | `network` | 222,038 | −0.58..+3.56 |
  | `extension` | 347,962 | −1.78..+2.55 |
  | `background` (20 m mesh) | 26,066 | −1.53..+3.53 |
  | `level` | 13,729 | −1.63..+3.53 |
  | `weight` | 462 | +0..+1 (support extension) |
  | `system` | 118 | −0.28..−0.005 |

  `faces` is unchanged.
- `main-landscape-1900.json`:
  - `siteGround` (pads above);
  - new `osGroundLevels`;
  - `roadControlIds` 9 → 30;
  - `railwaySlopes`: LT&SR and Abbey Mills curve slopes refitted to the new ground (max 3.15 / 2.21 m); Woolwich +69 triangles;
  - `railwayWorks`: LT&SR hold-off walls 210 faces / 231.9 m → none, Woolwich opening-cut walls 8 / 33.2 m → none; the Bow Creek approach and the opening-cut walls are unchanged;
  - `retainingEdgeCrests`: 7 of 32 wall routes, with coping changes of 0.003–0.24 m. Routes 1, 14 and 31 change most (0.16, 0.24, 0.11 m), where the support extension or weight changed behind the wall;
  - `roadBridgeClearance.pass`: counts changed, footprints unchanged; the underpass levels −0.017 → −0.042 (Abbey Lane) and −0.378 → −0.356 (Mill Meads road);
  - probes: Northern Mill Meads 0.195 → 0.232, Abbey marsh −0.672 → −0.574 (the progression assertion still holds);
  - tidal-face, junction-cap and replacement counts;
  - input hashes.
- `landscape-flood-1900.*`: 30 bed cells, 16 connection cells and 17 kind cells changed. These are the Woolwich embankment rastered across Abbey Road. The figures are unchanged (below).
- Input hashes only: `terrain-1900.json` (infrastructure hash; every `.f32` is byte-identical), `river-system-1900.json`, `drainage-connections-1900.json`, `flood-demo-1900.json`, `wharf-cranes.json`.
- `docs/scene-manifest.json`: fingerprints.
- `factory-yards.json`: byte-identical.

**Walls, batters and bridges recomputed** (T2/T3/T11/T12b/T14 measures, `t21/final/walls.txt` with T3's `measure_walls.py`):

| Measure | Before | After |
|---|---|---|
| Wall fill within 0.5 m at 1 and 3 m | 67.37 % | 68.47 % |
| Void behind walls at 3 m | 516 m | 494 m |
| Steps > 2.5 m over < 3 m: core | 52 | 18 |
| Steps: network | 6 | 6 |
| Steps: system | 214 | 214 |
| Steps: extension | 0 | 0 |
| Steps: groundMesh | 2 | 2 |

- Span footprints are unchanged.
- `check_main_landscape.mjs` passes: no ground above a road or within a span.
- The Bromley trench and Abbey Lane deck-end rules were not touched.

## Checks

- **`npm test` 21/21** (`t21/npmtest-final.log`): the 20 existing checks plus the new **`scripts/check_os_ground_levels.mjs`**. The new check asserts:
  - the register copies of every core-box spot height (value, position, scene level);
  - that every unapplied reading gives a reason;
  - every applied reading within the register's 0.6 m unless it carries an exception;
  - applied median ≤ 0.3 and p90 ≤ 0.6 (measured: 0.008 and 0.074 among non-exceptions);
  - each premises reading is a control of its pad, met by `premisesLevel()` within 0.1 m.
- **Changed stored sample**: `check_road_bridges.mjs` `BEFORE` was refreshed with `--write-sample`. Every difference is an approach rising onto its deck instead of sagging to the bridge cone; no deck station changed. Full arrays: `t21/bridge-sample.json`.

  | Bridge | Stations | Before (m) | After (m) |
  |---|---|---|---|
  | Pegshole east approach | 19–22 | 2.53–2.89 | 2.74–2.96 |
  | St Thomas west approach | −4..−1 | 2.12–2.48 | 2.53–2.77 |
  | Marshgate Lane, both ends | −4..0, 26–29 | 1.03–1.47 | 1.45–1.60 |
  | Three Mills Lea bridge east end | 58–61 | 1.74–2.16 | 2.19–2.28 |

  On the St Thomas kerb rows the stations at −2/−1 keep their old cone heights (2.36, 2.53), so a 0.3–0.4 m dip remains there between the raised street and the deck. The centre row is smooth. A variant that removed it drew ground 0.11 m above a deck-end footway (failing `check_main_landscape.mjs`), so I dropped it.
- No other assertion changed.
- Python checks (`t21/pychecks-final.txt`) pass: `check_main_landscape`, `check_historic_elevation`, `check_river_system`, `check_factory_yards`, `check_factory_buildings`, `check_manor_road`, `check_east_depot_tracks`, `check_western_completion`, `check_stratford_station_rail_alignment`, `check_scene_data`.
  - `check_east_channelsea_context` fails as before, on the frozen Woolwich route (T20 decision 5).
  - Checks that write under `reference/` wrote into a private copy of `reference/topography-research-2026-09-28/terrain-epochs` (its other children are links).
- Lint and Prettier are clean on `docs/main-landscape.js`, `scripts/check_os_ground_levels.mjs` and `scripts/check_road_bridges.mjs`.
- **Determinism.** The full cascade was run twice; all 50 generated data files are byte-identical (`t21/final-determinism.txt`). Infrastructure and housing are at a fixed point. The register script is reproducible.
- **LT&SR at grade** (`t21/final/ltsr.txt`): at chainage 300–700 the formation is within 0.09–0.21 m of the drawn ground at 7 and 10 m either side. At 15 m the worst is 0.24 m. Before: 1.2–3.1 m.

## Flood plausibility

- **`landscape-flood-1900.json` connected land is unchanged**: 4.5 m ODN 112.86 ha, 5.5 m ODN 113.84 ha (also 2.5 m 85.10 and 3.5 m 111.58).
  - That grid is built from `terrain-1900.scene.f32`, the historic elevation over the earlier scaffold. It does not use the drawn main landscape, so ground fixes in the drawn scene never reach it. This is worth a decision (5).
- Supplementary indicator only (`t21/drawnflood.py`). This is a connected uniform stage on the drawn 4 m ground inside the landscape support, seeded from the network tide polygons, and with no embankments as barriers:
  - 3.5 m ODN: 99.6 → 95.5 ha;
  - 4.5 m: 108.0 → 111.9 ha;
  - 5.5 m: 128.4 → 128.4 ha.

  The 4.5 m figure rises because some ground fell. The gas works pad near the LT&SR dropped about 1 m to the rail level. Abbey Lane by the Channelsea dropped about 1.3 m to its OS level, and the bank crest no longer runs across it.
- **1897 / 1904 accounts** (`reference/photo-review-2026-10-03/reports/flood-evidence.md`): these still read plausibly.
  - The High Street between Pegs Hole and St Thomas now stands at 4.6–4.8 m ODN (was 2.4–3.9). This is its OS level.
  - The Stratford marsh roads, for example Abbey Lane, stand at 2.3–2.7 m ODN, about 2 m lower.
  - FE18 (1904, "two feet flowing down the High Street", about 5.2–5.4 m ODN) and FE11 (1897, "roads four feet under water", about 3.5–3.9 m ODN on those marsh roads) therefore fit the marker order 1897 < 1904. They also fit the inference that the 1897 roads were lower marsh roads, at least 0.6 m below the High Street. The works yards (10–18 ft) stay above the lower stage.
  - Still-water reasoning only, as the evidence file cautions.

## Renders

Before: main on 4173, `t21/before/`. After: worktree on 4206, `t21/after-final/`. Side-by-side: `t21/pairs-final/*.jpg`. I opened every image. (`t21/after/` and `t21/pairs-v8/` are an intermediate build.)

| Camera | Verdict |
|---|---|
| `t21-ltsr-manure-rail` (−120, 3.6, 395) | Before: the line on a 2 m bank with an earth slope in the foreground. After: track level with the ground, and the manure works lifted onto its yard level beside the line. |
| `t21-ltsr-manure-oblique` | The 1018 works stand on their raised yard; the T19 buildings sit on the ground; the Channelsea bank face is unchanged. |
| `t21-abbey-road-crossing` (120, 4, −180) | Before: the road dips to a short iron deck under a raised line. After: Abbey Road rises to the line and crosses it level. No deck. |
| `t21-abbey-road-crossing-high` | Shows the crossing and the cost of the local support patch. The ground around the crossing is raised to the OS (about 1.9–3 m) in a roughly 50 m patch, with an irregular edge where it meets the Woolwich ramp bank. Beyond it the north-east corner is still the flat floor (decision 1). |
| `t21-abbey-creek-wharf` | The wharf ground and buildings sit about 1.6 m higher. |
| `t21-three-mills-yard` | Before: the ground stood over the ground-floor windows of the distillery (pad −0.06, wall fill 1.9). After: the building sits on its yard and its lowest windows are clear. |
| `t21-three-mills-oblique` | The distillery island is on one yard level and meets its river walls. No visible step. |
| `t21-west-strip-street`, `t21-west-strip-oblique` | Unchanged: the terrace is still drawn flat at 0 (decision 1). |
| `t21-high-street-bow-bridge` | Unchanged: the road still climbs from 0.2 m to the 4.8 m Bow Bridge deck (decision 1). |
| `t21-st-thomas-bridge` | Before: the road sagged into the bridge and the frontage ground sat below the footway. After: a level High Street at its OS height, with footway and frontage ground on one level. |
| `t21-gasworks-holders-ne` | The holders sit about 0.5–1 m lower, with the ground falling towards the LT&SR fence. No floating or buried tanks. |
| `t21-mill-meads` | The marsh is slightly higher (0.2–0.5 m); the drains are unchanged. |
| `t21-core-overhead` | No visible artefact at this distance; the gas works pad is slightly darker near the railway. |

## Smoke

`smoke-t21-ground-levels` against `main-before-t21`, both on 4206; the baseline was taken from the unchanged merged worktree at the start (`t21/smoke-after.log`). **Ready, 0 page errors**, 8,934,090 triangles (+2,600), 154 draw calls. 27 differences, all explained:

1. `infrastructure.railwayWorks`:
   - LT&SR added 1057 → 714, removed 420 → 38, wall faces 350 → 140: the hold-off wall along site 1018 and the earth fitted to it are gone, because the ground beside the line now meets the formation; the Bow Creek approach and opening cuts remain.
   - Woolwich wall faces 8 → 0: the Abbey Road deck's cut-end faces are gone with the deck.
2. `infrastructure.bridgeStructures.triangles` 8828 → 8824: `docs/road-bridges.js` sizes wing ends and footings from the drawn ground (`level()`), and one such piece became degenerate on the raised approach ground. No deck changed (the bridge road sample is identical on the decks).
3. `factoryBuildings.chimneyTops` (28 of 96) and `tanks` (11 of 16):
   - Three Mills Distillery stack and tanks +2.34 m (pad −0.06 → 2.29);
   - Bromley retort and boiler stacks −0.07 to −0.45 m and scrubbers −0.03 to +0.04 m (the 924 pad surface through its readings and the rail side);
   - the 1018 chimneys +1.90 m (ovens) and +3.14 m (engine house, at the west end by the goods shed, where the rail-side ground is 2.9–3.0 m).
   Each building is seated on its premises level.
4. `gardens.surfaceSamples` (1,559 of 2,208): the Mill Meads allotments follow the marsh correction, +0.2 to +0.34 m at the samples.
5. `wharfCranes.placed`: the manure works crane ground 2.393 → 2.559 and the Imperial Works wharf 1.324 → 1.447, on the new pads and ground.
6. `mainLandscape`:
   - `probes` (Northern Mill Meads +0.04, Abbey marsh +0.10), `replacements` (changed-vertex counts and ranges), and `seatedObjects` 919 → 947: 28 more objects with a non-zero lift on raised pads;
   - `streetControls` 9 → 23 (the register's street readings plus the regional ones).
7. `sewerCrossing.roadArches`: the Abbey Lane and Mill Meads road arch clearances change by 0.03 m, following the street level under the sewer, which is the marsh at the opening (underpass levels −0.017 → −0.042 and −0.378 → −0.356).
8. `terrain.clods` +3 and `vegetationTufts` 3507 → 4013: ground decoration placed by ground height and slope (more dry ground above the tufts' threshold on the raised yards and marsh).
9. `tramRails`:
   - stations 1354 → 1184, triangles and vertices −4,080: the rails are laid piece by piece along the drawn road's surface breaks, and the High Street from Pegs Hole to St Thomas is now level on its OS readings instead of a sag;
   - `riseMetres` [0.004, 0.010] → [0.003, 0.012]: still seated, and `check_tram_rails.mjs` passes.
10. `triangles` and `reflection.triangles` +2,600: the tufts, clods and tram pieces above, and the Woolwich embankment across Abbey Road (+69 triangles).

## What I did not do

- **The west terrace and the High Street towards Bow Bridge** (decision 1): 103 ground readings, 2–9 m above the drawn floor.
- **Bridge decks**: Three Mills Lea bridge 2.2 m against OS 4.23 m and 25 m short of the water; Pegshole, St Michael's and Bow are T12a's open item.
- **The Short Wall lane and river wall, and the Long Wall bank**: wall-top readings 17–18 ft drawn at about −0.3 m.
- **The gas works road ramp and the works fence outline** beyond the ground-plan polygon.
- **A finer 20 m regional mesh at pad edges.** T3 dropped a refinement; two exceptions remain because of it.
- **The north-east corner (Abbey Road / St Mary's) beyond the 50 m patch**: still the flat floor.
- The GeoPackage/GeoTIFF export was not regenerated.

## What I was unsure of

- **Rail-side ground.** Taking "no hatching" to mean the ground beside the line is at formation − 0.1 is T20's interpretation. It sets the gas works edge along the LT&SR and the whole 1125 pad (no yard reading of its own).
- **IDW pad surfaces** are honest at each reading, but between distant readings they are an estimate. The 924 holder area is about 1 m lower than before on that basis.
- **The 0.065 m road-surface convention** now applies to all street readings, including the earlier regional ones.
- **Three judgement calls**:
  - 18.9 ft by the sewer bank: bank crest, not marsh;
  - 17.3 ft at Abbey Mills: conflicts with the B.M.;
  - Manor Road's 3.4 ft dip under the aqueduct.

## Decisions for the reviewer and the author

1. **The terrace west of the Lea (and the High Street to Bow Bridge, and the north-east corner by Abbey Road) is drawn 2–9 m too low.**
   - *My choice:* stop and record it. None of the 103 readings are applied.
   - *Options:*
     - (a) Extend the main landscape over the terrace from the regional ground grid, which already matches the OS there (7.86 against 8.04 m at (−900, 600)). This gives a new 10 m-to-mesh ground over about 0.6 km² and re-seats the west-strip works, the housing rows and the High Street frontages through the level field. It also means a bank or wharf wall along the west side of the Lea (the OS has 15–17 ft at the water and 24–36 ft inland), re-levelled Bow Bridge approaches and High Street, the tram rails following, and the flood grid. This is its own task.
     - (b) Record the terrace as out of scope for the detailed 1900 scene and keep the flat floor, with this register saying so.
     - (c) A halfway step: streets and frontage pads only. Not recommended, because it would leave steps everywhere.
2. **Abbey Road crossing patch.**
   - *Choice:* raise a roughly 50 m patch around the crossing to the OS, so that the level crossing works.
   - *Alternative:* wait for option 1(a) and keep T20's deck.
3. **Bridge decks**: Three Mills Lea bridge (OS 21.2 ft on the bridge) and T12a's list. Re-levelling and lengthening the Three Mills deck would let Three Mills Lane meet its 16.2 ft reading.
4. **The Short Wall and Long Wall**: model the river walls and banks under the lane and path (wall-top readings 16.9–18.1 ft).
5. **The flood grid** reads the historic scaffold, not the drawn ground.
   - *Choice:* left as is; its figures are unchanged.
   - *Alternative:* rebuild `build_landscape_flood.py` from the main landscape so that flood views follow the drawn ground.
6. **Rail-side ground** (as above). The alternative is to leave the gas works edge and site 1125 on their previous estimates, which puts a 1–1.6 m bank back on the LT&SR's south side at chainage 420–480.

## Regeneration on main after merging

Generated files in this branch are cascaded. If main moves, run in this order:

1. `python3 scripts/prepare_os_ground_levels.py`, only if the spot heights change.
2. `python3 scripts/build_infrastructure.py`, then `(cd scripts && python3 build_housing_detail.py)`; repeat until stable.
3. `build_historic_elevation.py`, `build_river_system.py`, `build_main_landscape.py`.
4. `build_flood_demo.py`, `build_landscape_flood.py`, `build_factory_yards.py`, `build_drainage_connections.py`, `build_flood_demo.py`.
5. `build_wharf_cranes.py`, `build_scene_manifest.py`.
6. `node scripts/check_road_bridges.mjs --write-sample`, if the sample differs.

`build_historic_elevation.py` writes into `reference/topography-research-2026-09-28/terrain-epochs`.

## Files

- New:
  - `data/maps/os-ground-levels.json`
  - `scripts/prepare_os_ground_levels.py`
  - `scripts/os_ground_levels.py`
  - `scripts/check_os_ground_levels.mjs`
  - `T21_REPORT.md`
- Changed:
  - `scripts/build_main_landscape.py`
  - `scripts/build_infrastructure.py`
  - `docs/main-landscape.js`
  - `data/maps/railway-levels.json` (evidence text only)
  - `scripts/check_road_bridges.mjs` (sample)
- Regenerated:
  - `docs/data/infrastructure.json`
  - `main-landscape-1900.json/.background/.core/.extension/.level/.network/.system/.weight.f32`
  - `terrain-1900.json`
  - `river-system-1900.json`
  - `landscape-flood-1900.json/.bed/.connection/.kind`
  - `flood-demo-1900.json`
  - `drainage-connections-1900.json`
  - `wharf-cranes.json`
  - `docs/scene-manifest.json`
