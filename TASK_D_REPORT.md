# Task D report: Three Mills Lane over the House Mill race, and the Channelsea junction (5 October 2026)

This work was done directly in the parent session, without agents. Branch `task-d-three-mills-channelsea` (worktree `../book_website-taskc`), from main `841fbbd`. It reworks the two task C follow-ups the author called "janky" (plan, open fundamentals): the House Mill race culvert and the ledges at the Channelsea junction on the core edge.

## Summary

- **Three Mills Lane runs flat over the House Mill race.** The race is open water again under the lane, so the back rivers and the Lea are joined through Three Mills (task C's culvert cut them off).
  - A new deck, `house-mill-race-crossing`, carries the lane over the race at the OS level on the spot, 16.2 ft (2.706 m).
  - The deck is a flush slab: carriageway and both footways at street level, no parapets. The OS draws none; the lane runs on unbroken between the mill and the river wall.
  - **Before:** the drawn lane sagged from 2.6 m to 0.93 m in a V about 16 m long, and leaned by up to 0.4 m across its width.
  - **After:** the deck is level at 2.73 m. The lane is 2.66-2.69 m for 15 m either side, with no cross-fall.
- **The core seam no longer re-triangulates the streets.** Task C dropped a deck because adding it re-triangulated the whole connected setts surface. The new deck is cut out of the street meshes after they are triangulated, and only where it lies: 6 carriageway and 11 footway triangles change, all over the race. Before, about 300 triangles moved, some over a kilometre away. `check_main_landscape` passes.
- **The Channelsea junction at the core edge.**
  - **Low water:** the straight band across the channel at the core edge is gone; the mud runs through.
  - **High water:** the west-bank jog and the mud sliver at the tongue tip are gone.
  - The fix is a new traced OS mud flat, `abbey-creek-mouth-flats`. It carries the core's mud shelf on to the core edge and the OS high-water line about 8 m out down the west (Long Wall) bank. The flat rises to just under high water at the traced line, and the landscape bank starts there.
- **A flood consequence (decision for the author).** On main, the Mill Meads marsh spilled into the Channelsea at 3.49 m ODN through a notch in the west bank. The notch was made by the old -0.1 m land seam at the core edge. The new bank closes it; the marsh now spills at about 3.86 m ODN. Connected land at the 3.5 m ODN stage falls from 73.9 ha to 51.1 ha; the other stages are unchanged.
- **A side effect of task C undone.** The culvert had changed the shoreline topology the regional bank crest is interpolated along. That moved ground far from Three Mills: for example, four Oil Wharf tanks rose 0.11-0.37 m. Opening the race restores the pre-culvert values exactly (see Smoke).
- **Checks:**
  - `npm test`: 21 of 21.
  - Python checks: 41 pass. The other 34 fail identically on main, except `check_gltf`, which needs the git-ignored `.glb` exports this worktree lacks.

## Three Mills Lane and the House Mill race

**What the OS gives.** On the five-foot plan the race runs under the mill and under Three Mills Lane to the Lea. The lane runs on unbroken between the mill and the river wall, and no parapet or railing is drawn. The spot height on the lane at the race is 16.2 ft (sh_538304_182814), which converts to 2.706 m scene y.

**The deck** (`data/maps/district-road-traces.json`, mirrored in `remaining-trades-context-alignment.json`, which the alignment checks compare):

- 7 m along the lane centreline, from (-602.2, 396.1) by the route vertex at (-601, 396) to (-595.3, 395.1).
- The reviewed race passage (3 m display width) crosses it at 2.0-5.0 m.
- Height 2.706 m. The span records `width` 9.2 (carriageway plus both 1.1 m footways), `carriagewayWidth` 7 and `gradedApproach`.

**The form** (`data/maps/road-bridge-forms.json` and its copy in `docs/road-bridges.js`):

- `slab-deck`, as at the Abbey Mill crossing.
- Brick abutments at the water edges (2.0 and 5.0 m, 1 m long).
- `parapets: false`, a new register flag: `road-bridges.js` draws no parapet or railing when it is set.
- `docs/infrastructure.js` draws a deck that records `carriagewayWidth` as setts between two footway strips, 0.03 m above the road as off the deck.

**Why the earlier attempt failed, and the fix.**

- Every deck is cut out of the street surface before the street polygons are triangulated. The setts, carriageway and footway polygons are each one connected surface, and GEOS's constrained Delaunay picks different diagonals across the whole surface once any vertex changes.
- Measured on this deck: 54 setts, 16 macadam and 249 footway triangles changed, as far away as x 570 and z -965. The landscape fits its ground under every road triangle, so the whole fit moves; task C saw `check_main_landscape` fail by 0.016 m at Bridge Court.
- Fix (`scripts/build_infrastructure.py`, `LOCAL_CUT_DECKS` and `local_cut`): this deck is cut after triangulation. Triangles overlapping it are dropped, and only the rest of their area is triangulated again, with no new vertices on its outline (no T-junctions with the kept triangles). The road-area assertion is taken against the cut surface, and no kept triangle may overlap the deck by more than the 1 mm rounding.

**The ground under and beside the lane** (`scripts/build_main_landscape.py`):

- The deck takes the graded approach the Abbey Mill crossing has: street level for 2 m beyond each end, then at most 1 in 20, with the bank beside it cut back. The `gradedApproach` flag turns it on.
- **Street readings reach across a graded deck.** A street's level comes from its own OS readings by inverse distance, never through water. The only reading near the race is the one on the deck, so once the race was open water the lane west of it had no reading in reach. It fell to the marsh field: about 1.2 m, drawn as a 0.6 m dip 5 m west of the deck.
  - A graded deck carries its street over the water, so the corridor's readings now reach across it.
  - Abbey Lane, the only other graded deck, has no reading within 120 m of its crossing, so nothing changes there.
- `core_river_connections.py` is unchanged. It culverts a passage only under a street with no deck; with the deck, the House Mill race is one open, tidal passage again (21 m² more tidal water).

## The Channelsea junction at the core edge

**What was wrong.** The core tile (x -235..65, z -320..350) and the river network meet at z 350, where Abbey Creek joins the Channelsea.

- **The square cut at z 340.** The core's tidal mud follows its shelf study (`ground-plan.json` `bankStudies`), which was cut off square at z 340, 10 m inside the core edge. South of that line the core had plain ground beside the water. At low water this showed as a straight band across the channel and the tongue tip. At high water, ground below high water sat outside the tide outline: 22 m² of hollows, up to 2.1 m deep, along that line.
- **The west-bank jog.** The shelf study follows the OS high-water line about 8 m out from the mapped channel. The network south of the edge carried only its generic 5 m shelf, so the bank jogged about 3 m at z 350 (29 m² of hollows, up to 1.3 m deep).
- **The seam notch.** On land, both meshes taper to -0.1 m within 3 m of the core edge. On the west bank this cut a notch through the bank, which is where the Mill Meads marsh spilled (see the flood numbers).

**What the OS shows** (dark-line transects across the mosaic every 5 m from z 320 to 430, recorded in the register):

- On the west bank the high-water line is the toe of the hatched Long Wall bank, about 8 m outside the mapped channel. It runs at x -177.35 (z 330), -184.5 (340), -190.95 (350), -195.15 (360), -202.65 (370), -206.5 (380), -216.15 (395) and -222.35 (400).
  - North of z 340 this is the line the shelf study already follows.
  - The register's `notTraced` note said the lower Channelsea was within 5 m. Here it is not; the note is corrected.
- "Mud" is lettered at the tongue tip.
- South-east of Abbey Creek the high-water line closes onto the generic shelf by z 355.

**Changes:**

- **`data/maps/os-tide-levels.json`.**
  - A third mud flat, `abbey-creek-mouth-flats` (2,383 m²). It runs from the channel centre line to the traced west-bank line from z 332 to 400, closing onto the generic shelf by z 410. At the mouth it takes in the tongue tip and the channel margins to the core edge, and on the south-east side it runs from the shelf study's edge to the shelf.
  - Its traced lines are recorded as `highWaterLines`.
  - New section value `flatRimMetres` (2); the `notTraced` text is updated.
- **`scripts/tide_levels.py`.**
  - `flat_rim`: on a flat with a traced high-water line, the mud rises over 2 m to 6 cm under high water, as the core caps its mud, and holds that for the last metre to the line.
    - Without the rim, the flat's edge was 0.5-1 m below high water, and the bank behind it began there. The water then stood over a strip of lower ground (a ledge at high water).
    - The held metre keeps the rim on the network's 1 m bands.
  - `flat_seam`: the level where the meshes meet on a flat. `SHORE_OFFSET_M` moves here from the network builder.
- **`scripts/build_river_terrain.py`** (core):
  - The flats join the core's mud bed, so the study's square cut is gone.
  - The raised river-right bank (which fades out towards z 350) is kept off the flats.
  - Flats take the rim.
  - At the core edge a flat meets the network at `flat_seam` (with the rim), from exact distances, not the -0.1 land seam.
- **`scripts/build_river_network.py`:**
  - The same seam on flats.
  - Flats take the rim. Flat membership includes the boundary: a vertex on the traced line takes the rim.
  - Former grid vertices on a flat take their own section instead of interpolating from a band triangle. A band triangle can reach across the traced line to marsh beyond it; that left one vertex at -0.02 m and a 7 m² hollow behind it.
- **`scripts/build_main_landscape.py`:** beside an OS flat the bank band is measured from the flat's outer edge plus 3 m (`FLAT_BANK_M`), not from the low-water shoreline inside the flat. Without this, the crest behind the 8 m flat fell below high water.
  - This applies to the task C flats at Four Mills too. There it removes a 45 m² hollow up to 1.4 m deep at (-629, 1066).
  - The register is read through the landscape's input hashes.

## Numbers

| | Before (main 841fbbd) | After |
|---|---|---|
| Three Mills Lane over the race, drawn road (centre / ±2.5 m) | min 0.93 / 0.86 / 1.00 m, V about 16 m long | 2.726 m flat on the deck; 2.66-2.69 m for 15 m either side |
| House Mill race | culverted under the lane (21 m²), two dead-end stubs | one open tidal passage under a flush slab deck |
| Road bridges | 10 | 11 |
| Street triangles changed by the deck | about 300 across the district (cut before triangulation) | 6 carriageway, 11 footway, all over the race |
| Tide outline | 159,458 m² | 159,643 m² |
| Traced OS mud flats | 2 (10,036 m²) | 3 (12,419 m²) |
| Ground below high water just outside the tide (1 m grid, x -240..-110, z 320..420) | 111 m², deepest 2.12 m | 75 m², deepest 0.38 m; the seam jog (29 m²) and the z 340 line (22 m²) gone |
| The same at Four Mills (x -700..-590, z 890..1180) | 391 m² | 344 m² |
| Connected land, 1.9 / 2.5 / 3.5 / 4.5 / 5.5 m ODN | 0 / 0.03 / 73.87 / 105.69 / 114.48 ha | 0 / 0.03 / 51.09 / 105.63 / 114.47 ha |
| Plinths | 159 | 160 (one new at site 419; House Mill and the Three Mills wharf plinths move 0.01-0.19 m with the ground at the race; a few elsewhere by 2 cm or less) |

The 3.5 m ODN change is the closed seam notch. The 22.8 ha of Mill Meads marsh that connected at 3.49 m ODN through cell (-190, 348) now connects at about 3.86 m ODN.

## Structural diffs

- `infrastructure.json`:
  - `roadBridges` (the new deck);
  - `roadSurfaces/setts`, `roadTriangles` and `shoulderTriangles` (the local cut);
  - `roads` (Three Mills Lane's record carries the new span).
- `river-network.json`:
  - `reviewedConnections` (the race passage is one polygon, no `culvertedUnder`);
  - `tide/polygons`;
  - `bankMesh`, `vertices`, `triangles`, `baseGround`;
  - `retainingEdges/routes` (the race shoreline).
  - Height range unchanged.
- `river-system-1900.json`: `bankSections`, `baseGround`, `coreBedCorrections`, `tidalCoreBedCorrections`, `waterPolygons`, `reaches`, `extensionPolygons`, hashes.
- `river-terrain.json`: unchanged; its `.f32` and `.rgba` change.
- `main-landscape-1900.json`:
  - `continuousBanks/profileCount` 27 to 28;
  - `networkTidalWater` counts;
  - `osGroundLevels` marsh control counts;
  - plinths;
  - hashes, with `os-tide-levels.json` new among them.
- The rest of the cascade is regenerated (historic elevation, floods, yards, drainage, cranes, manifest).
- Builders run in the task C order, except that the flood demo now follows the drainage connections, whose hash it stores.

## Checks

- **`npm test`: 21 of 21.**
- **`check_road_bridges.mjs`.**
  - Stored sample refreshed. Against main's actual state only St Thomas (0.001 m), St Michael's (0.001 m) and the Hunts Lane connection (up to 0.009 m) moved, plus the new deck's entry.
  - Section 5 changed: a bridge whose register form has `parapets: false` must have no parapet or railing; every other bridge still needs both.
- **`check_core_river_connections.py`:** new assertions that the House Mill race is one uncut passage, not culverted, and inside the moving tide.
- **`check_river_tides.py`:** comment only (the culvert note); the no-tide-across-undecked-streets test is unchanged and passes.
- **`check_three_mills_north_alignment.py`:** its count of Three Mills Lane spans excludes the new race deck. It still fails at its old assertion (site256-range-1), as on main.
- **Python checks: 41 pass.** These include all those task C listed: `check_river_tides`, `check_river_system`, `check_river_banks`, `check_marsh_ditches`, `check_core_river_connections`, `check_landscape_flood`, `check_main_landscape`, `check_historic_elevation`, `check_scene_data`, `check_district_streets`, `check_western_completion`, `check_factory_yards` and `check_manor_road`.
  - The 34 that fail here fail on main too, with the same assertion. They were run there with `git status` checked before and after; nothing was written. One exception, `check_gltf`, passes on main but needs the git-ignored `.glb` exports, which this worktree lacks.
  - Most of the 34 are one-off alignment checks and stale input hashes from earlier rounds.
- **ESLint and Prettier are clean** on the changed JS.

## Renders

Before: main on 4173. After: this branch on 4210. Same cameras: `cameras.json`, with sheets `sheet-*.png` in `reference/photo-review-2026-10-03/views-taskd/`.

| View | Verdict |
|---|---|
| Three Mills Lane from the Lea, low and high water (`tml-north-*`) | Fixed. Before, the lane sagged in a V to the race with a fill curtain under it. After, it runs level, with the race opening and its slab under it. The green bank faces in front of the lane either side of the race are still jagged (pre-existing). |
| Three Mills Lane at lane level (`tml-lane-east-high`, `tml-lane-west-low`) | The lane runs level to House Mill; no dip. |
| Three Mills Lane in plan (`tml-plan-*`) | Unchanged in plan; the race is under the lane. |
| From the south, in the back river (`tml-south-low`) | Unchanged (the race runs under the mill there). |
| Junction in plan, low water (`cj-plan-low`) | Fixed. The straight band across the channel at the core edge is gone; the mud runs on. |
| Junction in plan, high water (`cj-plan-high`) | Fixed. The west-bank jog and the mud sliver at the tongue tip are gone. An intermediate version drew the rim 2 cm above high water and showed it as a dark line along both traced edges; the rim is now 6 cm under. |
| Junction from the west, low and high water (`cj-west-*`) | Fixed. At low water the notch and wedge at the junction are gone; at high water the dark gap at the core edge is gone. |
| Abbey Creek mouth from the south-east, low water (`cj-mouth-low`) | Fixed. The pale wedge at the seam is gone. |
| From the south over the manure works (`cj-south-*`), from the north (`cj-north-low`) | Small changes along the west bank; no new ledge. |

## Smoke

`review_smoke.py` (scratch copy with 900 s waits): `taskd-before` (main on 4173) against `taskd-after` (4210). Both have **0 page errors**. There are 20 differences:

- **The new deck.** `roadBridges` rises from 10 to 11 and `namedBridges` gains `house-mill-race-crossing`. Bridge structure triangles rise by 188 (abutments, slab). `destinationCount` rises from 140 to 141, the deck's walk-on destination.
- **Mesh counts.**
  - River network: 931,889 to 932,241 vertices; 1,843,627 to 1,844,315 triangles.
  - Landscape replacement counts move with them. The extension mesh has 792 fewer vertices; it changes only at the junction (x -242..-99, z 350..405).
  - Total triangles rise by 730. Tufts fall from 4,795 to 4,788.
- **`continuousBanks.profileCount`: 27 to 28.** The regional bank crest is interpolated along each merged shoreline of the river system between its OS readings. Opening the race joins the Three Mills back-river and Lea shorelines again, so the crest is interpolated along the same lines as before task C's culvert.
  - The culvert had quietly moved ground far from Three Mills. This task restores it.
  - Every remaining smoke difference is that restoration: four Oil Wharf tanks (x -1120..-1143) are reseated 0.11-0.37 m lower, one chimney top 0.36 m higher, and three wharf cranes on ground 0.005-0.08 m lower. Each matches the pre-culvert value in task C's own smoke snapshot (`smoke-taskc-after.json`, taken before the culvert) exactly.
  - In the landscape heights this restoration is most of the 25,192 network and 19,919 system vertices that move by more than 2 cm.

**Builders are deterministic.** Infrastructure, core terrain, network and landscape were rerun, and every output compared byte for byte the same.

## Not done

- **The rest of the lower Channelsea.** The west-bank high-water line continues about 8 m out below z 410 and is not traced; the generic 5 m shelf is used there.
- **Leftover hollows.** Small hollows below high water remain along the new bank (no more than 3 m² each, up to 0.38 m). Main's other hollows at the junction (on the Abbey Creek south bank near z 345-352) are unchanged.
- **Three Mills bank faces.** The jagged green bank faces along the Lea in front of Three Mills Lane are unchanged.
- **Exports.** GeoTIFF, GeoPackage and glTF exports were not rerun.
- **Probes not kept.** The scratch probes used for the road and pit measurements (`scripts/_probe_*.mjs`) are not committed.

## What I was unsure of

- **The deck's construction.** A slab on brick abutments is an estimate; the OS shows only that the lane runs on over the race. The 7 m length and the 3 m display passage are interpretations.
- **The west-bank high-water line** is read as the toe of the hatched Long Wall bank, about 8 m out. The lettering H.W.M.O.T. is on that line further down the river; at the junction the line is read from its continuity. Three transect points (z 345, 365, 390) were interpolated where the line was masked by figures or hatching.
- **The rim** is a display device. The OS line is where the ground meets high water, and the rim makes the drawn ground do that.

## Decisions for the author

1. **The 3.5 m ODN flood stage.** Closing the seam notch changes the flood page: at 3.5 m ODN, 51.1 ha are connected instead of 73.9 ha. The old figure depended on a model artefact, a gap through the Long Wall bank at the core edge. I recommend keeping the new figure. The alternative is to model a deliberate low point, such as a sluice, if the evidence shows one.
2. **Parapets on the race deck.** None is drawn, following the OS. If a photograph shows a parapet or railing on the lane by House Mill, set `parapets` back and choose a form.
3. **Tracing the rest of the lower Channelsea.** I recommend doing it later, with the towing-path work, so the west bank is consistent down to Bow Creek.
