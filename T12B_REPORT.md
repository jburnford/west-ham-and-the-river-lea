# T12b report: landscape cut back from the road bridges

4 October 2026. Worktree branch `worktree-agent-a588af8c3b7bad49b`.

## Setup

- The worktree started at 116c0ae, without the T15 merge. I ran `git merge main` (fast-forward to 660b924, which includes 62ddae2 "Merge T15 …").
- Part-way through, main gained T12c (road-bridge register re-derived) and T17 (High Street frontages moved). T17 changes a hashed input of the landscape, `high-street-frontages.json`. I committed my work (d648629), merged main again (076ad7f) and rebuilt the landscape on the merged inputs (bb82b10).
- **"Main" below means main's builder re-run on the current main inputs** (`scratchpad/t12b/mainrb`). Main's committed landscape is stale against T17. The rebuild changes only `network.f32` and `level.f32`, near the moved frontages.
- Scratch folder: `/tmp/claude-1000/-home-jic823-book-website/158d731a-06ad-4794-89f0-96291b5302cd/scratchpad/t12b/`.

## What I changed and why

I changed only:
- `scripts/build_main_landscape.py`;
- the regenerated `docs/data/main-landscape-1900.json` and its `background`, `core`, `extension`, `level`, `network` and `system` `.f32` files (`faces` and `weight` are byte-identical);
- `scripts/check_main_landscape.mjs` (new assertions only).

The cause in one line: `docs/infrastructure.js` draws every street, footway and path triangle on the drawn ground under its vertices. Near a bridge it raises the road to a cone (deck − 0.065 − 0.12 m per metre). Nothing ever fitted the landscape to that road. So:
- ground poked through between road vertices;
- the bridge approaches stood on vertical earth curtains up to 4.7 m high (Bow);
- the low provisional decks had ground above them.

### New section: road bridges and road corridors (record `roadBridgeClearance` in the JSON)

1. **Approach embankments.** Under every road triangle within reach of a bridge cone, the ground is made up to the cone. Beyond the road edge it falls at 1:1.5. It never rises:
   - over water, nor steeper than 1:1.5 from the low-water edge or a span footprint;
   - over a building, nor steeper than 1:1.5 from its footprint (the existing `edge_caps`);
   - steeper than 1:1.5 from the outer edge of its own mesh.

   The mesh-edge cap was added after a 2.6 m cliff appeared where the network mesh ends west of Bow Bridge. Where a cap applies, the road keeps a short curtained approach. The bridge's wing walls and walled approach cover most of that.
2. **Approach cuttings, on the bridge's own road only** (corridor plus 1.2 m of footway, within 40 m, crossing streets excluded). The road ground may be no higher than the deck road level for 2 m from the deck, then rises at 1 in 20 (T3's Abbey Lane rule), with 1:1.5 cut sides. This acts at Marshgate Lane and the Three Mills footpath.
3. **Span clearance.** Inside each span footprint, ground is held at or below the water edge (low water + 0.02 = 0.08 m). The footprint is the union of:
   - the drawn low water between its first and last crossing on lines parallel to the deck, across the deck width, carried 2 m beyond each edge;
   - the register clear zone between the abutment faces, placed as `road-bridges.js` places them (`data/maps/road-bridge-forms.json` is now a hashed input: 29 hashes).
4. **No ground above a road.** Every landscape vertex inside a road or deck triangle, or within one mesh edge of one, is capped at that triangle's drawn surface less up to 0.04 m. Beyond that, ground above a road is cut back at 1:1.5.
   - The vertices that the road's own vertices take their height from (the triangles or core cell containing each road vertex) are capped in 4 passes only. Unlimited passes made the road chase the ground down and sink whole lanes by up to 2.3 m (Three Mills Lane by the distillery). One pass left 156 offending samples. Every other vertex is then capped in one pass that leaves the road where it stands (`roadVertexGroundChangeMetres` 0.0).
   - The 20 m regional mesh is cut along the road triangles (an overlay, so each piece lies wholly inside or outside each triangle). Its triangles inside a street are therefore planar with it. Triangles 74,540 → 97,804.
   - Road heights are modelled as the page computes them: float32 positions, the same point-in-triangle tolerance, and the 10 m level-field fallback where no mesh covers a road vertex.
5. **Streets under the Northern Outfall Sewer.** Through `road_fit_levels`, a street keeps the marsh level at the middle of the opening (Mill Meads works road −0.378 m) for 2 m from the opening axis, then rises at 1 in 20. The Mill Meads works road reading at Abbey Road (2.83 m) used to reach 116 m and stop under the deck. Abbey Lane's opening has no reading in reach, so nothing changes there.

Channel beds in drawn water and preserved tidal mud are never changed. Nothing in the pass touches `level.f32`; it changes only through item 5.

### Checks added (`check_main_landscape.mjs`)

- **Span footprints.** Every bridge has one. No landscape vertex inside it (core, network, system, extension, regional mesh) stands above the water edge. Core preserved tidal mud is counted separately and exempt: it is the surveyed channel bed, asserted unchanged earlier in the same check.
- **Road corridors.** The check builds the real `infrastructure()` and samples every street, footway and path triangle on a 1 m barycentric grid. It asserts that the drawn ground is never more than 0.05 m above the highest drawn road surface there. Holes in the road mesh are skipped. Samples whose core cell touches preserved mud are reported, not asserted.

No count assertion was changed in either landscape check.

## Per-bridge table (main → after)

Column notes:
- Deck = deck height (m). Approach meeting the deck = drawn road surface 0.25 m off each deck end.
- Footprint vertex max = highest landscape vertex inside my footprint.
- Zone ground = highest ground sampled every 0.25 m between the merged register's abutment faces across the deck. It includes interpolation across the zone edge.
- Steepest side = steepest dry ground slope across the approach sides, every 1 m over 30 m. 1:1.5 is 0.67. On the 1 m and 2 m grids a 1:1.5 batter reads up to 0.94 along a mesh diagonal.

| Bridge | Deck | Footprint vertex max | Zone ground max | Approach meeting the deck, start / end | Approach ground at 1 m (centreline), start / end | Steepest side, start / end |
|---|---|---|---|---|---|---|
| Bow | 4.8 | −0.03 → **0.08** | −0.10 → 0.23 | 4.52 / 4.53 (unchanged) | −0.10 / −0.10 → **2.88 / 1.82** | 0.93 / 0.72 → 0.68 / 0.74 |
| Pegshole | 3.0 | 0.08 (1 vertex above) → **0.08** | 0.24 → 0.29 | 2.74 / 2.73 → 2.73 / 2.73 | 1.16 / 1.87 → 1.18 / 2.25 | 1.25 / 0.91 → 0.94 / 0.93 |
| St Thomas | 2.6 | 0.11 → **0.08** | 0.14 → 0.23 | 2.36 / 2.36 → 2.35 / 2.35 | 0.83 / 1.61 → 1.35 / 1.61 | 1.29 / 0.45 → 1.26 / 0.56 |
| St Michael's | 2.8 | 0.10 → **0.08** | 0.14 → 0.24 | 2.56 / 2.54 → 2.55 / 2.54 | 1.68 / 1.59 → 1.69 / 1.60 | 0.97 / 1.02 → 0.87 / 0.94 |
| Channelsea (High St) | 3.3 | 0.12 → **0.08** | 0.11 → 0.20 | 3.03 / 3.03 (unchanged) | −0.10 / −0.10 → **2.21 / 1.08** | 0.90 / 0.78 → 0.90 / 0.78 |
| Marshgate Lane (prov.) | 1.5 | **1.18** → 0.08 | 1.17 → 0.86 (4 samples above 0.5) | **2.01 / 2.44 → 1.48 / 1.49** | 1.84 / 2.42 → 1.39 / 1.37 | 0.34 / 1.04 → 0.44 / 0.69 |
| Cook's Road (prov.) | 1.5 | 0.65 → **0.08** | 0.45 → 0.41 | 1.46 / 1.44 → 1.44 / 1.44 | 0.57 / −0.10 → 1.30 / 1.31 | 0.35 / 0.41 → 0.49 / 0.62 |
| Three Mills Lea | 2.2 | 0.00 → 0.08 | −0.01 → 0.19 | 2.16 / 2.16 (unchanged) | −0.10 / 0.61 → −0.10 / **2.01** | 0.01 / 0.49 → 0.01 / 0.94 |
| Three Mills footpath (prov.) | 1.5 | **2.04** → 0.08 | 0.81 → 0.23 | no road triangles on the route | 2.63 / 0.05 → 1.40 / 0.16 | 0.39 / 0.98 → **1.09** / 0.94 |
| Abbey Lane | 1.8 | only preserved mud (max 0.87, unchanged) | 0.78 (mud) | 1.81 / 1.81 (unchanged) | unchanged | 2.17 / 2.41 unchanged (T3's mud-edge faces) |

Ground above the deck anywhere on the route:

| Bridge | Main | After |
|---|---|---|
| Marshgate Lane | +0.93 | −0.04 |
| Three Mills footpath | +1.02 | −0.07 |
| All others | below the deck | below the deck (unchanged) |

T12b's specific items against T12a's figures:

- **Bow.** Before, the approaches were 4.7 m vertical curtains on −0.1 m ground. Now they are earth embankments, about 2.9 m (start) and 1.8 m (end) high 1 m from the deck. They rise at 1:1.5 from the water edge to the cone and fall at 1:1.5 at the sides, held 1:1.5 off the frontage buildings.
  - The "mound in the arch" in the author's screenshot was the river bank in front of the camera and the far bank through the arch. No landscape stood inside the arch on main once T13 and T12c had moved the spans.
- **Pegshole (1.67 m) and St Thomas (0.94 m) above the soffit.** These were T12a's figures on the old routes and register. On main with T12c's register, T12a's own report in `check_road_bridges.mjs` already showed no ground touching a soffit. That is still so after.
- **Marshgate Lane (0.93 m above the deck) and the Three Mills footpath (1.03 m above it).** Both fixed.
- **Abutment edges.** In the zone column, the sampled maxima (up to 0.29 m at the High Street arches) sit at the abutment face lines. There the embankment or bank rises at 1:1.5 from 0.08 m at the footprint edge. This is interpolation across the edge, not a vertex inside it.

## Mill Meads works road arch (smoke `sewerCrossing.roadArches`)

| | Main | After |
|---|---|---|
| Rise | 1.49 | **3.49** |
| Crown clearance | 4.49 | **6.49** |
| Edge clearance | 3.44 | 4.69 |
| Street centreline under the deck (5 samples) | 1.66 / 1.39 / 0.95 / 0.51 / 0.08 | −0.34 / −0.35 / −0.38 / −0.39 / −0.39 |

## Road corridors: samples with ground more than 0.05 m above the drawn road

My probe samples on a 1 m barycentric grid and compares against the highest drawn road surface.

| | Samples | Main | After |
|---|---|---|---|
| Carriageway | 304,595 | 6,887 (worst 1.39 m) | **0** (worst 0.035) |
| Footway | 207,445 | 816 (worst 1.36 m) | **6** (worst 0.22) |
| Path | 4,256 | 111 (worst 0.65 m) | **0** |

- The 6 footway samples are at Abbey Lane, over preserved tidal mud that the check requires unchanged. T3 reported the same sag.
- The new check samples triangle edges too: carriageway 380,335, footway 295,281 and path 6,113 samples, 0 offending. 125 and 483 samples lie on cells touching preserved mud and are reported separately.

## Step, fill, trench and seating figures

| | Main (rebuilt) | After |
|---|---|---|
| Steps: core / network / system / extension / groundMesh | 52 / 0 / 214 / 0 / 2 | **52 / 0 / 214 / 0 / 2** (core: 0 new, 0 gone) |
| T2 fill within 0.5 m at 1 m and 3 m | 37.19 % | **37.19 %** (1 m: 41.76 → 41.76; 3 m: 72.74 → 72.59) |
| Bromley trench minimum | −0.103 m | **−0.103 m** (0 profiles below −0.3) |
| Seated objects moved more than 0.05 m (of 1,126) | | **3, not 0** |

The 3 seated objects that moved are Abbey Stores Yard ranges 8, 9 and 10 (site 9008), which moved by −0.75, −0.78 and −0.88 m.
- They have no premises pad, so they are seated on the 10 m level field.
- Bilinear sampling of the field had lifted them about 1 m above the drawn ground (seat 0.68–0.89 against drawn ground −0.12 to −0.32). The cause was the 2.83 m reading of the neighbouring Mill Meads works road corridor.
- Item 5 lowers that corridor. They now sit at −0.10 to 0.04, still 0.2–0.3 m above the drawn ground.
- This is a correction, but it breaks the letter of the criterion; see Decisions.

## Checks, npm test and smoke

- `python3 scripts/check_main_landscape.py`: PASS (29 hashes).
- `node scripts/check_main_landscape.mjs`: PASS, including the two new assertions.
- `node scripts/check_railway_embankments.mjs`: PASS.
- `node scripts/check_tram_rails.mjs`: PASS. Rise above the road is 0.004–0.011.
- **`npm test`: 15/18. Main is now 16/18, because T12c's merge made `check_road_bridges.mjs` pass there. So this is one worse than main.**
  - The failure is assertion 2, T12a's stored road-surface sample along each bridge route ±4 m ("abbey-mill-crossing: road surface at station −1 m, row 0, was 1.845, now 1.823").
  - My change necessarily alters that surface where the brief asks it to: Marshgate approaches lowered up to 0.97 m.
  - The 4 support passes also lower it near some decks: St Thomas up to 0.37 m at 2–4 m off the deck on the outer rows; St Michael's 0.17; Cook's Road 0.16; Pegshole 0.05; Abbey 0.02. Bow, Channelsea, Three Mills Lea and the footpath are unchanged.
  - The deck-end samples (0 and 1 m) are unchanged except at Marshgate.
  - A scratch copy of the check with only assertion 2 removed passes every other assertion. I did not edit `check_road_bridges.mjs` (T12c's file).
  - The other two failures are the known `check_drainage_connections.mjs` and `check_flood_demo.mjs`.
- **Smoke** (scratch copy waiting 600 s for ready and 900 s for the tween; server on 4194):
  - `t12b-bridges --compare main-after-t13`: ready, **0 page errors**, 25 differences. Most of them came with the merges (T15 railway works and bridges, T12c structures, T17 frontages).
  - So I also captured current main from 4173 (`main-now-4173`, 0 page errors) and compared the two snapshots. **14 differences, all mine:**
    - `mainLandscape.groundMeshVertices` 223,620 → 293,412: the regional mesh is cut along the roads.
    - `replacements.core/network/system`, changed vertices and ranges: the embankments (network max +4.35 m at Bow) and the cuttings.
    - `sewerCrossing.roadArches`, Mill Meads: 3.49 / 6.49 / 4.69.
    - `tramRails` stations 1,713 → 1,306, triangles 41,088 → 31,320: the High Street surface is smoother, so the adaptive rail subdivision needs fewer stations. Rails still seated (riseMetres 0.0043–0.0109).
    - `infrastructure.bridgeStructures.triangles` 8,674 → 8,710: `road-bridges.js` builds spandrel and footing columns from the drawn ground, which changed at the abutments.
    - `terrain.clods` 22,635 → 22,653.
    - `triangles` and `reflection.triangles` +13,772: regional mesh +23,264, tram rails −9,768, the rest tufts, clods and bridge columns. I did not trace the last few hundred.

## Renders

- After: `views-after3/`, from 4194 on the final merged build.
- Before: `views-before2/`, from 4173 (main; its landscape is stale against T17, which does not touch these views).
- Earlier before set: `views-before/`.

Verdicts:

- **Eye-level Bow** (−990, 2.5, 122): **fixed.** The 4.7 m vertical brown wall along the east approach is replaced by a grass embankment rising to the road. The west approach is the same. The arch reads clear over the water. The bank in the foreground is the river bank (unchanged).
- **`bridge-bow-bridge-span`: improved.** Both approaches now read as grassed embankments instead of dark walls. The camera's own bank still hides the springing.
- **Author's Bow view** (−940, 55, 150): **improved, modest at this height.** The approach sides are battered rather than walled; the deck and arch are unchanged.
- **Added `x-bow-from-river-south`:** the arch is clear. A grass slope now meets the west abutment and wing wall.
- **Added `x-bow-approach-east-side`:** the setts run on a grassed embankment.
- **`bridge-pegshole-bridge-span`: uninformative.** The camera is inside a building, before and after, as T12a found.
  - Added `x-pegshole-from-river`: both arches are clear over the water before and after, and the mud strip at the arch feet is unchanged.
- **`bridge-st-thomas-bridge-span`: no visible change** (distant).
  - Added `x-st-thomas-from-river`: the arch is clear. A small green rise on the right approach at main is now graded.
- **`t1b-mill-meads-road-north`: fixed.** Before, the arch was flat and green ground showed through the setts under it. After, the arch is tall, the road dips cleanly under the sewer, and no ground shows on the road.
- **Marshgate** (derived: `x-marshgate-deck-from-north` (−835.6, 3.2, −80) → (−845.1, 1.4, −112.3); `x-marshgate-from-river` (−818.5, 1.2, −107) → (−842, 1, −100)): **fixed.**
  - Before, the road stood above the deck and green ground swallowed its far end.
  - After, the road descends to the deck, the whole deck and both railings show, and the far approach is visible.
  - From the river the right-hand ground now sits at deck level instead of rising above it.

## What I did NOT do

- I edited no deck heights, routes, register entries, `infrastructure.js`, `road-bridges.js`, `check_road_bridges.mjs` or `scene-manifest.json`.
- **Three Mills Lea west approach:** no embankment. No adjustable mesh covers it; it lies on the flat −0.1 m replacement base. The road stays on a curtain there.
- **Preserved tidal mud** under the Abbey Lane footways and deck is not cut.
- I did not raise any road over a bank (the alternative to cutting the bank); see Unsure.
- I did not refresh T12a's stored road-surface sample.

## What I was unsure of

- **Road vertices sink at a few places.** The 4 support passes let the road follow the ground down where a road triangle spans a bank.
  - Road vertices sinking more than 0.25 m against main (measured before the second merge): about 117 near bridges and 205 elsewhere.
  - Some are intended (the Mill Meads underpass; the Marshgate and footpath cuttings).
  - Some are side effects: Three Mills Wall lane drops about 0.8 m along roughly 90 m where it crossed the bank band crest; a few High Street footway rows by St Thomas drop 0.37 m.
  - Fewer passes leave ground above the road (3 passes: 11 samples off preserved mud; 1 pass: 156; both measured before the second merge). Raising roads over the crests would be the other answer.
- **Building–road overlaps.** Ground under the edge of a building that stands over a footway is cut to the road, for example `high-street-09` on Marshgate Lane. The building keeps its seat, so a small gap may show under such walls. These are T13's registration conflicts.
- **Bow east approach.** A parapet bench mark shows a walled south side; the batter is held off the frontage buildings anyway.
- **The Mill Meads dip to marsh level** is interpretation, as T1b drew it. The nearest readings are 115 m away and 2.1–2.8 m.
- **Batter steepness** reads up to 0.94 on the 1 m mesh (grid diagonals). The footpath's cut side reaches 1.09 where a crossing lane is excluded from the cut.

## Decisions for the parent

1. **Refresh `check_road_bridges.mjs`'s stored sample** (`--write-sample`) after merging. The approach surfaces change by design: Marshgate, plus the small support-pass changes listed above. Until then `npm test` is 15/18 against main's 16/18.
2. **Accept the 3 Abbey Stores Yard seat moves.** The alternative is to keep `level.f32` free of the underpass rule, which leaves them about 1 m in the air.
3. **Accept the road-support passes (4) and the sinking they cause, or ask for road raising over banks** (a road-surface change).
4. **Rebuild the landscape after any further input change.** `road-bridge-forms.json` is now a hashed landscape input, so T12d's deck-end work will stale it.
5. **Three Mills Lea west approach** needs ground that the landscape can adjust (or a walled approach) if it is wanted.

## Files

- `/home/jic823/book_website/.claude/worktrees/agent-a588af8c3b7bad49b/scripts/build_main_landscape.py`
- `/home/jic823/book_website/.claude/worktrees/agent-a588af8c3b7bad49b/scripts/check_main_landscape.mjs`
- `/home/jic823/book_website/.claude/worktrees/agent-a588af8c3b7bad49b/docs/data/main-landscape-1900.json` and `.background/.core/.extension/.level/.network/.system.f32`
- Renders: `scratchpad/t12b/views-before/`, `views-before2/`, `views-after3/`
- Probes and tools: `scratchpad/t12b/probe.mjs`, `batter.py`, `fpverts.py`, `t12c_zone.py`, `sink.py`, `measure2.sh`
