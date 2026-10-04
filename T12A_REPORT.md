# T12a report: road bridges drawn as structures

Branch `worktree-agent-add2f3e3349c9c75e`. At the start the worktree was behind main (116c0ae). I fast-forwarded it to main 911c8b7 before starting. Later I merged main 64552cc (T8 sewer earthwork, T10 tram rails) as the coordinator asked. All checks below were run after that merge.

## Summary

Every `roadBridges` record is now drawn as the structure its style names:

- **Five High Street bridges:** stone or brick segmental arches. Each has abutments at the drawn water edges, a river pier with cutwaters at Pegshole, spandrel walls, a projecting arch ring, a string course, 1.0 m parapets with 0.12 m coping, end piers, and splayed wing walls.
- **Three Mills Lea bridge and two provisional lanes:** decks on iron girders or timber beams, on brick abutments, with railings.
- **Abbey Lane:** its old 0.4 m slab and brick parapets are kept, and brick abutments added.

The approach fill is no longer drawn between the abutment faces. The road surface is unchanged: deck setts, footways and `ground()` are all the same. A stored before-sample proves this to the millimetre, and the tram check still passes.

`npm test` passes 15 of 17. The two failures are the known `check_flood_demo.mjs` and `check_drainage_connections.mjs`. The new `check_road_bridges.mjs` passes, and so does T10's `check_tram_rails.mjs`.

## Evidence found, per bridge

Sources available in the repository:

- **VCH Essex VI pp 57–61.** Cited in each record for the structural family only. The text is **not** in the repository or `reference/`, and I did not read it. All proportions are marked as estimates.
- **`data/maps/district-road-traces.json` notes.** These say:
  - Bow Bridge is "one granite-faced span completed 1839".
  - The St Thomas arch count "is not established by the written source".
  - The bridge names follow the 19th-century transposition.
  - The three lane connections are provisional.
- **OS five-foot plan 1893–96**, read with `factory_map_sources.mosaic()`. Zoom 18 (about 0.4 m per pixel) is the highest zoom in the tile archive. It shows each named crossing and its parapet or road edge lines. **The abutment faces under the deck cannot be read at this resolution.** I therefore did not use the plan for abutment positions or skew.
- **OS 25-inch height observations** (`data/maps/lower-lea-region/height-observations.opus-2026-10-02.geojson`). Bench marks are cut on the Pegs Hole Bridge parapet, at St Michael's Bridge, and on the "hatched south parapet / retaining wall of the Bow Bridge east approach". This is evidence of masonry parapets and walled approaches. The observations also include spot heights on the crossings; see Decision 1.
- **Photo catalogue.** No archive image shows these bridges, so no elevation detail was copied from a photograph.
- **Drawn water polygons.** I measured where the water polygons as `app.js` draws them cross each route, on the centreline and on both deck edges. These model measurements set the abutment stations and the skew (`waterEdges` in the register).

| Bridge | Documented / mapped | Measured in model | Estimated |
|---|---|---|---|
| Bow | granite-faced single span, 1839; stone family; parapet bench mark on the east approach | Lea crosses obliquely: water 2–29 m on the centreline, 6.5–30.5 m and 0–27.25 m on the two edges. Skew 0.4 m per m | segmental span 26.5 m, rise, ring, parapet |
| Pegshole | stone, 2 arches (record); parapet bench mark; crown spot height | water 10.75–24.75 m on the centreline, wider on the south-east edge | 2 × 8.6 m arches, 1.8 m pier with cutwaters |
| St Thomas | brick family; arch count not established | water 8.5–15 m, flaring on the left edge | 1 arch of 8.75 m, 3 brick rings |
| St Michael's | stone family; bench mark at the bridge | both banks oblique, skew −0.18 | 12.75 m arch |
| Channelsea (High St) | stone family; tramway spot heights on it | oblique, skew −0.3 | 10.25 m arch |
| Three Mills Lea | style deck (record also says archCount 1); bench mark at the west abutment | water 24.25–38 m | iron girders 0.8 m, timber deck, iron railings |
| Abbey Lane | no style in the record | channel cuts 20–27.5 m | brick abutments; slab and parapets kept |
| Marshgate Lane (prov.) | provisional; deck or culvert unresolved | water 7.75–15.25 m | timber deck and railings |
| Cook's Road (prov.) | provisional | water 15.5 m wide | iron girders (too long for plain timber without river trestles) |
| Three Mills footpath (prov.) | provisional | water reaches the route only on its right edge, from 8 m, and runs past the route end | timber; second abutment at the route end |

## What I built

### Register: `data/maps/road-bridge-forms.json`

The register gives each bridge's form, abutment stations, skew, crown depth, ring depth, pier width, girder or beam depth, `waterEdges` and an `evidence` string saying what is mapped and what is estimated. It also lists the sources and the defaults.

How the register reaches the page: it is **embedded** as `bridgeForms` in `docs/road-bridges.js`. I did not add a build/copy step, because loading a new JSON at runtime would have needed edits to the `app.js` data list next to the tram lines. `check_road_bridges.mjs` fails if the module copy and the register differ (`deepEqual`). So there is no `scripts/build_road_bridge_forms.py` and no `docs/data/road-bridge-forms.json`.

### `docs/road-bridges.js` (new)

This module builds every structure into one triangle batcher, giving **one merged mesh per material: 4 meshes** (stone, brick, iron, wood). UVs are in metres.

- **Arches:**
  - Segmental barrels through the springing (0.5 m) and the crown soffit (deck minus `crownDepth`), sheared to the skew.
  - Abutment faces from a footing up to the springing. The footing is 0.3 m below the lower of the drawn bed and the water.
  - The Pegshole pier, with pyramid-capped cutwaters.
  - Spandrel walls built column by column. Over each arch they run from the soffit; over piers and abutments, from the footing; on the land parts of the route, from 0.4 m below the drawn ground (a walled approach, as the Bow parapet bench mark suggests). In every case they rise to the deck.
  - A 0.05 m proud arch ring and a string course under the deck.
  - Parapets 0.45 m thick, 1.0 m high, with a 0.55 × 0.12 m stone coping. Stone parapets on stone bridges; brick with stone coping on the brick bridge.
  - End piers at the route ends.
  - Wing walls from each abutment corner, splayed 30° back into the land. Their length is 0.9 × (deck − springing), clamped to 2–5 m. Their tops slope from the deck down to the bank.
- **Decks:**
  - Brick abutments at the water edges (1.0–1.5 m deep).
  - Brick walled approaches on the land parts of the route.
  - A timber deck (0.12 m) under the setts, with outer and middle wrought-iron girders and 1.5 m cross girders, or timber beams.
  - Iron or timber railings 1.05 m high (posts every 1.8–2 m, top and middle rails).
  - Short wing walls.
  - Abbey Lane keeps its 0.4 m stone slab, so the T3 landscape that holds the bank 0.1 m below the slab underside still fits. Its brick parapets are 1.0 m plus coping (before: 0.9 m).
- **End closures.** A closure under each route end is set 0.05 m inside, so it never shares a plane with the approach fill.
- **`bridgeClearance()`.** Gives the plan zone between the abutment faces, out to 2 m beyond each deck edge. It returns the pieces of an edge that lie outside every zone.

### `docs/infrastructure.js`

- The fill curtains in `surface()` now go through `clearance.outside()`, so no fill is drawn between the abutment faces.
- The old bridge loop is reduced to the deck sett box and the footway boxes. These are unchanged, so the road surface and the tram rails are untouched. It then calls `roadBridges()`.
- `ground()` is untouched.
- The return value gains `bridgeStructures` (meshes, triangles, forms). This is the one intended smoke-snapshot difference.

### `scripts/check_road_bridges.mjs` (new; `run_checks.mjs` picks up every `check_*.mjs` automatically, so it needed no edit)

The check builds the real `infrastructure()` module, as the tram check does, and asserts:

1. The register equals `bridgeForms`. Every record has a form of its recorded family, arch counts match, provisional flags match, and the registered abutments lie under the deck (not silently moved).
2. The drawn road surface along every bridge route is unchanged within 1 mm. Holes must stay holes. It compares 3 rows (centreline and both carriageway sides) every metre, from 4 m before each route to 4 m beyond it, against the stored sample `BEFORE`, taken from commit 911c8b7.
3. Every arch crown soffit is at least 0.3 m above the water, the springing is above the water, and the rise is possible.
4. Nothing is below the water inside a drawn water polygon, except abutments, piers, cutwaters and wing walls.
5. Every non-provisional bridge has a parapet or railing on both sides, at least 0.9 m above the deck and running the full route.
6. No approach-fill vertex lies inside a clear zone. There is a 0.3 m tolerance for the 0.25 m edge subdivision.

It also prints, without asserting, a landscape-intrusion report for T12b.

I did not edit `check_bridge_movement.mjs` or `check_culvert_section.mjs`; both pass unchanged.

## Per-bridge table

Water: the static surface is y 0.06 and the tide animates to y 1.1. "Span" is the clear span along the road. Clearance is soffit minus 0.06; the clearance over the 1.1 m high tide is 1.04 m less. The landscape column comes from `level()` sampled every 0.25 m along the span and at 9 offsets across it.

| Bridge | Style / form | Arches | Span (m) | Deck (m) | Crown soffit or deck underside (m) | Clearance over water (m) | Landscape still intrudes? (for T12b) |
|---|---|---|---|---|---|---|---|
| Bow | stone-arch | 1 | 26.5 | 4.8 | 3.90 | 3.84 | No: no ground inside the arch or above the deck. The ground beside the bridge is about −0.1 m on both banks, so the approach is a 4.8 m walled causeway |
| Pegshole | stone-arch | 2 | 2 × 8.6 (17.2 clear) | 3.0 | 2.40 | 2.34 | **Yes:** the ground rises 1.67 m above the arch soffit at the west abutment (station 8, offset +3). 7 % of span samples are inside the arches; 23 % of the span floor stands above the water |
| St Thomas | brick-arch | 1 | 8.75 | 2.6 | 2.00 | 1.94 | **Yes:** 0.94 m above the soffit at the east abutment (station 15.75, offset +6). 4 % inside the arch; ground 0.02 m above the deck at station 0.5, offset −6 |
| St Michael's | stone-arch | 1 | 12.75 | 2.8 | 2.10 | 2.04 | No: nothing inside the arch or above the deck |
| Channelsea (High St) | stone-arch | 1 | 10.25 | 3.3 | 2.65 | 2.59 | No inside the arch. The brown tidal-mud bank in front of the bridge hides the springing from the span camera |
| Three Mills Lea | iron-deck | – | 14.75 | 2.2 | 1.28 | 1.22 | No |
| Abbey Lane | slab-deck | – | 8.5 | 1.8 | 1.40 | 1.34 | No; 70 % of the span floor stands above the water (two cuts) |
| Marshgate Lane (prov.) | timber-deck | – | 9.0 | 1.5 | 1.03 | 0.97 | **Yes:** the ground reaches 0.30 m above the deck underside at the east abutment, and stands up to 0.93 m above the deck on the route (station 25.5) |
| Cook's Road (prov.) | iron-deck | – | 16.5 | 1.5 | 0.78 | 0.72 | No (the girders dip below the 1.1 m high tide) |
| Three Mills footpath (prov.) | timber-deck | – | 4.43 | 1.5 | 1.08 | 1.02 | **Yes:** the ground stands 1.03 m above the deck at the route start |

The check also counts vertices below the water inside water polygons. All of them belong to abutments, piers, cutwaters or wing walls. Where the drawn water flares beyond the abutment (Pegshole and St Thomas left edges, Cook's Road, the Three Mills footpath), most of the wing walls stand in the water: 66 vertices each at Pegshole, St Thomas, Cook's Road and the footpath.

## Checks and smoke

- **`npm test`:** 15/17 pass. Failing: `check_drainage_connections.mjs` and `check_flood_demo.mjs`, the known failures; they also failed on the base. The base had 13/15. Main's merge added `check_tram_rails.mjs`, and I added `check_road_bridges.mjs`.
- **Prettier and eslint:** clean on all changed JS files.
- **Smoke.** I used a scratch copy of `review_smoke.py` that waits 400 s for the tween. The base snapshot `t12a-base` was taken on 911c8b7 before the merge; `t12a-road-bridges` was taken after it. There were **0 page errors** and 9 differences:
  - **Mine:** `infrastructure.bridgeStructures` (new review field). `triangles` / `drawCalls` / `reflection.*` rose by +56,805 triangles and +1 draw call in the default view; that figure also includes T10's tram rails (40,920 triangles), which came in with the merge.
  - **From the merge, not mine:**
    - `tramRails`: T10's module.
    - `infrastructure.roadRoutes` 101 → 102: T10/T8 changes to `infrastructure.json`.
    - `sewerCrossing.roadArches[0].edgeClearance` 4.41 → 4.40: T8.
    - `terrain.vegetationTufts` 3574 → 3628: T8 changes to `ground-plan.json`.
  - I could not take a fresh base on the merged main. Making a scratch copy of `docs/` and temporarily checking out main's `infrastructure.js` in the worktree were both refused by the permission system. So the merge differences are explained from the T8/T10 diffs, not proved by a same-base comparison.

## Triangle and draw-call cost

I measured headless on the merged data, with `infrastructure()` and the full railways, original module against T12a:

- **Meshes:** 2639 → 2561 (**−78**). The old bridges were about 80 separate box and extrude meshes; the new structures are 4 merged meshes, and the deck road and footway boxes are kept.
- **Triangles:** 258,559 → 265,065 (**+6,506**). The bridge structures alone are 8,226 triangles.
- **Approach-fill (earth) triangles:** 68,846 → 68,850. The edges cut at the zone boundaries add 4.

## Render verdicts

Cameras come from `cameras-seams.json`, plus the author's overhead. Before renders: `<scratchpad>/t12a/before/`. After: `<scratchpad>/t12a/after/`, plus five close river-level views (`x-*`) that I added to verify the structure. The x-views were not rendered on the base code: making a base copy of `docs/` to serve was refused by the permission system.

- **`bridge-bow-bridge-span`: improved.**
  - Before: a flat, full-length extruded arch springing at the route ends, with white see-through slivers at both ends.
  - After: a stone segmental arch springing at the water edges, string course, coping and end piers. The slivers are gone.
  - The near bank (the camera is 1.5 m up on ground at about 1 m) still hides the springing and the water. That is the landscape, not the bridge.
  - Pale diagonal lines on the spandrels are the wing-wall copings seen end-on.
- **`bridge-bow-bridge-approach-a`: improved.** The white sliver ends at the crest are replaced by stone end piers and parapets. The setts (now with T10's tram rails) are unchanged.
- **`author-bow-bridge-overhead`: improved, modest at this height.**
  - Parapets with coping, end piers and the wing walls at the four river corners are visible.
  - The white end quads seen before at the deck joint are gone.
  - From 70 m up the arch itself cannot be seen. The deck reads much as before.
- **`bridge-channelsea-high-street-bridge-span`: improved but partly hidden.** The old 49 m flat arch is replaced by a 10.25 m stone arch with walled approaches, but the brown tidal-mud bank between the camera and the bridge hides most of the opening. `x-channelsea-from-river` shows the arch clear over the water, with wing walls and the abutments standing in the water.
- **`bridge-pegshole-bridge-span`: no information.** The camera stands inside a building in both before and after (brick wall and floor fill the frame).
  - `x-pegshole-from-river` (added) shows two segmental arches on a pier with a triangular cutwater. Water passes under both.
  - Landscape mounds stand inside both arches at the abutments, matching the 1.67 m intrusion in the table.
- **`bridge-st-thomas-bridge-span`: improved (distant).** A small brick arch with parapet now shows beyond the two river banks, where before there was a flat slab.
  - `x-st-thomas-close` (added) shows the brick arch, string course and coping clearly.
  - The grey landscape banks come right up to the spandrel on both sides.
- **`bridge-three-mills-lea-bridge-span`: improved.** The slab with masonry edges is now a dark girder deck between brick abutments with iron railings. The water passes under.
- **Added: `x-bow-from-river` and `x-st-michaels-from-river`.**
  - Bow: the full arch, ring, string course, coping and end pier read well.
  - St Michael's: the arch, wing walls and water read well.
  - The St Michael's view also contains unexplained non-bridge objects; see "What I was unsure of".

## What I did NOT do

- I did not edit `infrastructure.json`, the landscape, `ground()` or `app.js`. `app.js` needed no change, because `road-bridges.js` is imported by `infrastructure.js`.
- I did not change any deck height, width, route or arch count, including the contradictory `archCount: 1` on the Three Mills deck.
- I did not fix the two coordinator findings from T10 below. Both would change the road surface, which this task had to keep unchanged.
  1. **Road steps up onto every High Street deck end.** T10 measured 0.08–0.33 m at the deck end. My sample, 1 m off the deck, shows:

     | Bridge | West end (m) | East end (m) |
     |---|---|---|
     | Bow | 0.39 | 0.36 |
     | Pegshole | 0.28 | 0.36 |
     | St Thomas | 0.21 | 0.11 |
     | St Michael's | 0.40 | 0.27 |
     | Channelsea | 0.40 | 0.37 |
     | Three Mills Lea | 0.17 | 0.14 |
     | Cook's Road | 0.13 | 0.14 |

     Marshgate Lane is the other way round: the road there stands 0.36 m and 0.94 m *above* its deck. The cause is that the road `elevationProfile` (`roadProfileHeight`) takes precedence over the bridge cone in `ground()`, and it is lower near the decks. A fix belongs in the road profiles (`build_infrastructure.py` / `road-traces.json`). Changing `ground()` would move the tram rails and break `check_tram_rails.mjs` and this task's road-surface sample.
  2. **Holes in the road surface** at the Bow Bridge west end (about −1051, 127–128) and a sliver at the junction of the two High Street routes near (−371, −654). T10 also reports one near (−190, −864). These are gaps in `infrastructure.json` `roadSurfaces`, so they belong to the infrastructure builder. My sample stores them as holes (`null`), and the check would flag them if they changed.
- I did not regenerate `docs/scene-manifest.json`; it is outside my file list. `road-bridges.js` is not in the manifest, so it loads unversioned: correct locally, but not cache-busted on the published site.
- I added no refuges, lamp standards, bollards or tram-specific details on the bridges. Nothing was copied from a photograph.

## What I was unsure of

- **Abutment positions and skew** come from the drawn water polygons, not from the OS plan, which at 0.4 m per pixel does not show abutments under the deck. Where the water polygon flares at one deck edge (Pegshole and St Thomas left edges), I set the abutments by the centreline. The flare is left partly under the abutment and wing walls, which stand in drawn water.
- **Arch shapes** are segmental with a springing of 0.5 m, and the crown depth is my estimate. The 1839 Bow arch may have been elliptical; I found no source for its shape or span in the repository.
- **The VCH text was not read** (not available here).
- **Wing walls** seen square-on from the river read as pale diagonal coping lines across the spandrel. The geometry is right (walls along the banks, coming towards a viewer in the river), but it could be toned down.
- **Unexplained objects in `x-st-michaels-from-river`:** a dark beam overhead and a brown band with curved strokes to the right of the bridge. They are not bridge geometry: there is no timber or iron in the St Michael's form, and the band sits outside the bridge. I could not compare with a base render of that camera.

## Decisions for the parent

1. **Deck heights against OS spot heights.** Scene y = (ft − 1.3) × 0.3048 − 1.835, using the `verticalReference` in `terrain-1900.json`, ±0.3 m. On that basis three decks look low:

   | Crossing | OS reading | Scene y (m) | Recorded deck (m) | Deck is low by (m) |
   |---|---|---|---|---|
   | Three Mills Bridge | spot height 21.2 ft "on Three Mills Bridge" | 4.23 | 2.2 | **2.0** |
   | St Michael's | spot height 21.8 ft (position uncertain, "no dot found"); bench mark 22.40 ft | 4.41; 4.60 | 2.8 | **1.6** |
   | Pegs Hole | spot height 19.1 ft "bridge crown"; parapet bench mark 20.61 ft | 3.59; 4.05 | 3.0 | **0.6** |

   For comparison:
   - Channelsea: 19.7 ft on the tramway gives 3.77 against a 3.3 deck (+0.47).
   - St Thomas: 16.5 ft by the bridge gives 2.80 against 2.6.
   - Bow: 22.1 ft at the east end gives 4.50 against 4.8. The bench mark on the east-approach parapet, 23.77 ft, gives 5.01.

   Raising decks is a `road-traces.json` / `build_infrastructure.py` change, and it would move the road surface and the tram rails. It needs a coordinated pass with T10 and T12b. The forms here follow any new height automatically.
2. **Approve or adjust the register's abutment stations and skews.** They are model measurements and could be refined by a higher-resolution OS reading.
3. **Run `npm run manifest` after merge** so `road-bridges.js` is versioned.
4. **T12b inputs:** see the per-bridge table. Pegshole (1.67 m into the west arch) and St Thomas (0.94 m into the east side) need ground cut back inside the arches. Marshgate Lane and the Three Mills footpath have ground standing above their decks. At Bow the ground is about −0.1 m beside a 4.8 m deck, so the walled approaches are tall; T12b may want approach banks there.
5. **Road steps and holes from T10:** route to the infrastructure builder, as above.
