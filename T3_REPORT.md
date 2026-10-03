# T3 report: yard edges and road corridors

3 October 2026. Worktree branch `worktree-agent-a8104d11ba9088ca9`.

## Bottom line

- **Steps:** no yard-edge or corridor step of more than 2.5 m over less than 3 m is left in the network or extension meshes. Network went from 702 to 0 and extension from 80 to 0. Core fell from 422 to 106 and groundMesh from 3 to 2, with no new core edges. System stays at 214, all of them pre-existing.
- **Bromley trench:** filled. Between the bank crest and the gas works yard edge, the lowest drawn ground went from −0.72 m (42 of 65 profiles below −0.3 m) to −0.10 m (none below −0.3 m).
- **Abbey Lane:** graded to the existing 1.8 m `abbey-mill-crossing` deck. I did not change `infrastructure.json` (see Decision 1).
  - At each deck end, and at the first ground beyond the preserved tidal mud, the drawn road surface is now within 0.00 m of the deck.
  - Before, the road surface stood 1.45 m (west) and 1.31 m (east) above the deck within 2 m of it.
  - One exception remains: a sag of up to 0.12 m (west) and 0.18 m (east) where 0.5 to 1.5 m of check-protected preserved mud lies just beyond each deck end.
- **Abbey Lane side slopes:** these now fall at 1:1.5, except where a building, preserved tidal mud or the core/groundMesh seam stands at the edge. Every remaining steep edge is listed below with its cause.
- **Other criteria:** T2 wall fill is unchanged at 37.19 %. Both landscape checks pass. `npm test` passes 13 of 15 (the two known failures). No object's seating changed.

## Setup

- My branch started at 116c0ae, behind `main`, with no local changes. I fast-forwarded it to `main` (edf59cc) before starting.
- At that base, `check_main_landscape.py` failed on a stale `infrastructure.json` input hash (T7 renamed roads). Re-running the unchanged builder gave byte-identical `.f32` files and changed only that hash. "Before" below therefore means the committed geometry.
  - I saved it to `scratchpad/t3/base/` and used it for every before figure and render.

## What changed

I changed only `scripts/build_main_landscape.py`, then regenerated `docs/data/main-landscape-1900.json` and its `background`, `core`, `extension`, `level`, `network` and `system` `.f32` files. `faces` and `weight` are byte-identical.

1. **Edge batters** (`edge_batter`, `edge_caps`, called from `base()`).
   - Pads and street corridors stay level inside their outlines, as before.
   - Outside, the ground takes the level of the nearest edge point minus distance/1.5, wherever that is above the existing ground, out to at most 8 m. So the batter is 1:1.5 and its width follows the level difference. The edge level is the pad level for a pad and the corridor's own inverse-distance street level for a road (`road_fit_levels`, split out of `road_levels`).
   - A higher neighbour's batter may run into a lower yard, which removed the gas works frontage against Manure Works #1018 pad edges. It never runs onto a street corridor.
   - Limits (`edge_caps`):
     - Ground may stand no steeper than 1:1.5 above low water from the water's edge, and never over water.
     - Ground may stand no steeper than 1:1.5 above a building's ground from its footprint. That ground is the building's premises level, or its unraised ground if it has no pad. So fill never buries a wall.
     - "Footprints" means T2's set (factory buildings, holders, mapped factories, houses, terraces) plus the High Street frontages, housing rows, the station and its supporting buildings, and the corn mill.
   - The batter never lowers ground.
2. **Bank-foot frontage** (`frontages`, `frontage_levels`).
   - I cast rays every metre from each pad edge to the nearest regional shoreline. A ray is kept if it is 0.6 to 40 m long and crosses no water, no part of the yard itself, and no railway embankment. Consecutive kept rays bound a strip.
   - Inside the strip, ground is made up to the lower of the yard level and the bank-crest profile, and the batter treats the strip as a source.
   - At Bromley the strip is 11,591 m². In total there are 42 strips over 46,928 m², but for most pads near marsh level the effect is centimetres.
   - My first version let rays cross the LT&SR. It filled 4,473 m² between the gas works and the railway and lifted 898 embankment vertices by more than 1 m. I excluded railways (see "Side effects").
3. **Abbey Lane and the deck** (`graded_decks`, `deck_zones`, `deck_under`, all limited to `abbey-mill-crossing`).
   - The Abbey Lane corridor level is clipped to deck − 0.065 m (the road-surface offset in `docs/infrastructure.js`) for 2 m beyond each deck end. Beyond that it may differ from the deck by at most 1 in 20 per metre.
     - The west street reading sh_538874_183253 (2.19 m, 8.1 m from the deck) is kept to within about 0.03 m.
   - Within 20 m of the deck, the regional bank band no longer lifts the corridor to the 3.0 to 3.2 m bank crest. That lift had made a 3.19 m hump at the west deck end and 3.01 m at the east end. The bank beside the corridor is cut back to rise at 1:1.5 from the street edge.
   - Under the deck slab, the bank is held 0.1 m below the slab's underside (1.3 m) and rises beside it at 1:1.5. The bank crest had stood up to 3.3 m, through the slab.
   - All core lowering (2,267 vertices, at most 1.98 m) lies inside x −31..29, z −62..−36.
4. **`level.f32`** is `base()` with batters and frontage, except in cells within one cell diagonal of a footprint without a premises pad. Those keep the unbattered value, so no building is lifted off ground that the batter is not allowed to raise.
5. **JSON.** Two new records, each with method and evidence that separate mapped, observed and estimated:
   - `edgeBatters`, with a per-pad frontage area list;
   - `abbeyMillCrossingApproach`, with the deck height and the two street readings, and saying the deck height is interpreted.

   There is one new `limitations` entry. `inputHashes` gains `high-street-frontages.json`, `housing-detail.json` and `abbey-station-plan.json` (now 28).

## Numbers

Steps use T2's `measure_walls.py` (rise over 2.5 m across under 3 m, unique edges; core counts both diagonals).

| Mesh | Before | After | New edges |
|---|---|---|---|
| network | 702 | **0** | 0 |
| extension | 80 | **0** | 0 |
| core | 422 | **106** | 0 |
| system | 214 | 214 | 0 |
| groundMesh | 3 | **2** | 0 |

- The 106 core edges left are preserved tidal mud (the core north edge and the Channelsea) and corridor shoulders running through building footprints (Abbey Stores Yard). Neither may be changed under the brief.
- groundMesh: the 2 left are the coarse bank faces noted by the audit.

**Bromley** (`bromley.py`): 65 profiles across the gas works river frontage, x −640..−500, z 690..1010.

| | Before | After |
|---|---|---|
| Lowest ground between bank crest and yard edge | −0.722 m (z 1000) | **−0.103 m** (z 975) |
| Profiles below −0.3 m | 42 | **0** |

- Strict reading: 31 profiles still dip more than 0.5 m below both crest and pad. The dip floor is about −0.10 m, in two places:
  - at z 865–905 and z 960–1010, where the landscape weight is 0–0.3 next to the shore, so the builder keeps the native network ground;
  - where the river-to-yard gap is longer than 40 m.

**Abbey Lane** (`abbey.py`, `deckends.py`). The drawn road surface, as `infrastructure.js` draws it (max(ground, deck − 0.065 − 0.12·d) + 0.065), minus the 1.8 m deck:

| | Before, west / east | After, west / east |
|---|---|---|
| At the deck end | 0.00 / 0.00 | 0.00 / 0.00 |
| Worst within 2 m | +1.45 / +1.31 | −0.12 / −0.18 (sag over preserved mud) |
| At the first ground beyond the mud (2 m) | +1.45 / +1.31 | **0.00 / 0.00** |
| Largest jump between 0.5 m stations, within 12 m | 1.16 / 1.49 | 0.12 / 0.18 |

Abbey Lane corridor sides: 166 perpendiculars every 2 m within 120 m of the bridge, dry ground only, steepest fall per 0.25 m. Steeper than 1:1.5 (with 10 % tolerance for bilinear sampling of the 0.4 m grid):

| | Before | After |
|---|---|---|
| Steeper than 1:1.5 | 136 | **31** |
| Building footprint at the edge | 6 | 6 |
| Building within 4 m (fill held off its wall) | 4 | 2 |
| Preserved tidal mud | 8 | 15 |
| Core/groundMesh seam at x ≥ 64.5 | 5 | 7 |
| Unexplained | 113 | **1** (0.76, bank face beside the east deck end) |

The steepest remaining edges (up to 1:0.17) are the Abbey Stores Yard building on the north side east of the bridge, whose footprint the corridor's 3 m shoulder overlaps.

**T2 wall fill:** 37.19 % within 0.5 m at 1 m and 3 m, unchanged (41.76 % at 1 m; 73.03 % at 3 m).

**Vertices changed against before:**

| File | Raised | Lowered |
|---|---|---|
| network | 13,588 | 0 |
| core | 19,877 | 2,267 (Abbey Mill crossing only) |
| extension | 2,892 | 0 |
| system | 174 | 0 |
| groundMesh | 840 | 0 |
| `level.f32` cells | 543 changed (at most +3.77 / −0.57) | |

**`level()` against the drawn ground.** Measured on 2.78 km² of non-water land outside the core, on a 2 m grid, by the audit's method. My before figures reproduce the audit's (38,604 / 199,972 m²).

| | Before | After |
|---|---|---|
| Within ±0.3 m | 91.2 % | 91.7 % |
| More than 1 m above | 13,976 m² | 8,576 m² |
| More than 0.3 m below | 204,680 m² | 191,484 m² |

So the sampler is slightly better, not worse.

**Seating:** of all 1,125 seated objects (replicating `applyMainLandscape`), **0** changed their landscape lift by more than 0.05 m.

## Side effects

- **`railwaySlopes`.** The toe ground is `base()`, so it now follows the batters:
  - LT&SR: 583 of 10,242 embankment vertices raised, at most 2.73 m (227 by more than 1 m). They lie along the gas works north edge (x −500..−275, z 475..575), where the embankment's lower slope now meets the pad batter instead of marsh.
  - GER Woolwich branch: 54 vertices (at most 0.19 m). Abbey Mills curve: 2 vertices (at most 0.34 m).
  - Formation stations, routes and bridges are unchanged; the `.mjs` check confirms this.
- **`replacements.extension.changedVertices`** went from 474,695 to 474,285. 410 extension vertices that the blend had lowered are now raised back to within 1e-6 of their original height by a batter.
- **The T1b Mill Meads works road arch** is flatter (rise 3.51 → 1.05 m, crown clearance 6.51 → 4.05 m).
  - Its "road level" is the maximum of `level()` samples across the 44 m bank width. Samples near the northern end of the bank now sit on the corridor batter, about 1.2 to 2.5 m higher.
  - The road under the sewer itself is unchanged (−0.38 m). The street there lies outside its readings' 120 m reach, a gap that existed before.

## Checks

- `python3 scripts/check_main_landscape.py`: PASS (28 source hashes). It failed at base on the stale hash.
- `node scripts/check_main_landscape.mjs`: PASS (808 seated objects).
- No count assertion was changed.
- `npm test`: 13 of 15. The failures are the known ones:
  - `check_flood_demo.mjs`: stale `terrain-1900.json` hash;
  - `check_drainage_connections.mjs`: git-ignored `reference/spot-heights/mosaics` absent from the worktree.

## Renders

Served from this worktree on 4182. For "before" I copied the base landscape files into `docs/data`, rendered, then restored the final files. PNGs are in `scratchpad/t3/views-before/` and `views-after/`.

- **`bridge-abbey-mill-crossing-approach-a`: fixed.** Before: a full-width, pleated 2.5 m vertical green face across the view. After: the face is gone and the ground rises smoothly to the approach (the camera is now just above the graded ground).
- **`channelsea-along--50` (15, 2, −50): now legible.** Before, the camera stood inside the 3.0 m bank crest at the east deck end, and the view was a slab and a bank interior. After, it is 0.2 m above the graded road at deck level, looking past the deck end to the cut-back bank and the mud under the bridge. One grass tuft shows on the bank top. Nothing looks broken.
- **`x-abbey-lane-overview`** (added, high view south of the crossing): the pleated vertical face along the Abbey Lane corridor west of the river is replaced by a graded slope. The vertical face east of the mill along the river is unchanged. It is preserved mud against the raised bank (audit item 5, outside T3).
- **`00-abbey-lane-bridge-causeway`:** almost identical; a small change at the far left. The camera looks across water and mud at the mill and wall, and the corridor is barely in frame.
- **`01-abbey-lane-causeway-south-face`:** the hard pleated green wall at mid-distance is softened into a slope; the far approach still reads as raised ground.
- **`02-mill-mead-path-corridor`:** the vertical pleated face below the sewer deck is gone, replaced by a graded rise.
- **`03-mill-meads-works-road-tent`:** visually identical. The tents are in the 20 m groundMesh, which I did not re-triangulate (see "What I did not do").
- **`06-gasworks-pad-cliff-south`: uninformative.** Before and after, a single slope fills the frame at close range. My added `x-gasworks-south-edge-high` shows the LT&SR embankment between camera and pad, so it is also uninformative for the pad edge. The steps there are measured gone (extension 80 → 0).
- **`07-gasworks-river-trench`:** no visible change, because the camera faces along the bank, not across the frontage.
  - Added `x-bromley-frontage-high`: before, a dark groove ran between the bank and the yard with a crease line. After, the bank top runs into the yard and only a faint line remains.
  - Added `x-bromley-frontage-low`: no visible change.

## Smoke snapshot

I ran a scratch copy of `review_smoke.py` with a 900 s tween wait, served from this worktree.

- **Base snapshot (`t3-base`, base landscape files):** 0 page errors, 8,167,680 triangles. Its 19 differences against `drawn-ground` are exactly the ones T4 reported, from T1b, T2, T4, T5 and T6.
- **After (`t3-yard-edges --compare t3-base`):** ready, **0 page errors**, 8,169,828 triangles, 150 draw calls. The screenshot timed out, which the script treats as non-fatal; it exits 1 because there are differences.
- **6 differences:**
  1. `.mainLandscape.replacements.extension.changedVertices` 474,695 → 474,285: explained under "Side effects".
  2. `.sewerCrossing.roadArches` (Mill Meads works road) rise 3.51 → 1.05, crown clearance 6.51 → 4.05, edge clearance 4.71 → 3.29: explained under "Side effects".
  3. `.terrain.vegetationTufts` 3,404 → 3,574: more core ground is now dry and not on a vertical lip, so the tuft skip rules admit more.
  4. `.terrain.clods` 22,613 → 22,625: more clods.
  5. `.triangles` +2,148: about the tuft geometry.
  6. `.reflection.triangles` +2,148: as above.

  I did not trace the clod rule (item 4) or confirm that the +2,148 triangles are tufts rather than road-support fill.

## What I did not do

- **I did not change `infrastructure.json` or the deck height.** The 1.8 m comes from `data/maps/road-traces.json` (`bridgeSpans`), which I may not edit. A rebuild of `build_infrastructure.py` would undo a patch to the generated JSON.
- **I did not re-triangulate the 20 m groundMesh.** I built and measured it, and dropped it. Refining cells crossed by a batter to 2 m:
  - added 87,000 triangles (74,540 → 161,948);
  - removed the tents;
  - but exposed 58 groundMesh steps (2 → 60), against "groundMesh must not increase". They are corridor shoulders cutting through building footprints and the ends of a street's 120 m reading reach (Mill Meads works road, Abbey Road).
  - The code is kept at `scratchpad/t3/groundmesh_refinement_dropped.py.txt`.
- **I did not touch:**
  - the preserved tidal mud;
  - the bank policy outside the 20 m Abbey Lane deck approach;
  - the lip rule, end caps, wall fill and wall crests (all byte-identical in effect; fill coverage is unchanged);
  - the renderer, the flood inputs or the GeoTIFF/GeoPackage export (now stale).
- **I graded no bridge other than `abbey-mill-crossing`.** The High Street bridges sit on corridors whose readings mostly do not reach the deck ends.

## Unsure

- **The frontage fill is an interpretation:** made ground at yard level between yard and river bank. It removes the trench, but no survey shows these frontages. The 40 m reach and the railway exclusion are judgement calls.
- **The sag beside each deck end.** I read "within 0.1 m at both ends" as satisfied at the deck ends and at the first gradable ground, with the ≤0.18 m sag over protected mud reported, not hidden.
- **The deck-approach exemption from the bank band** is a local change to how the bank band treats Abbey Lane. It is justified by the street reading (2.19 m) 8 m from the deck, against a 3.2 m bank crest.

## Decisions for the parent

1. **Deck height.** Both Abbey Lane street readings stand above the 1.8 m deck: 2.19 m at 8.1 m west and 2.40 m at 34 m east. The graded approach therefore dips about 0.45 m to the bridge at 1 in 20.
   - Raising the deck to about 2.2–2.3 m in `road-traces.json` would remove the dip, then rebuild infrastructure and this landscape. Interpolating along the road between the two readings gives about 2.25 m at the deck. This is evidence-based, but there is no reading on the deck.
   - `DECK_*` in the builder already follows the deck height, so a deck change needs no code change.
2. **The 0.12–0.18 m sag over preserved mud at the deck ends.** Either extend the deck route about 2 m each way (`road-traces.json`), let the corridor override the mud preserve under a road (a check change), or accept it.
3. **The groundMesh tents.** If wanted, accept the refinement above together with a rule for corridor shoulders that cross buildings and for gaps in a street's reading reach.
4. **The T1b Mill Meads works road arch** is now flatter, through its `level()` maximum sampling. Re-check or re-tune `docs/sewer-crossing.js` if the arch matters.
5. **New hashed inputs.** `high-street-frontages.json`, `housing-detail.json` and `abbey-station-plan.json` are now hashed inputs to the main landscape, so any edit to them makes it stale. The GeoTIFF/GeoPackage export is stale.
