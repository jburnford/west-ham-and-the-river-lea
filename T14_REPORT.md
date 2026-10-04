# T14 report: river bank mesh along the shoreline, retaining walls on mesh edges

3–4 October 2026. Worktree branch `worktree-agent-a64e73c3e860d731a`, based on `main` at 3fffd45. I have not merged later `main`, as instructed.

## Bottom line

- **A (bank staircase): fixed in the river-network build.** Land within 8 m of the mapped channels is now triangulated in bands that follow offset lines of the mapped shoreline. The bank section comes from exact distances, keeping its former average placement, so it no longer steps with a 1 m raster.
  - **Bow Locks, T11's row test.** The largest step of the drawn waterline between adjacent rows fell from 0.51 m to **0.11 m** (95th percentile 0.43 → 0.04 m).
  - **Network-wide, plain bank.** Waterline profile steps over 0.3 m fell from 153 pairs to 1 (95th percentile 0.40 → 0.03 m).
  - **Renders.** The Bow Locks saw-tooth, the near bank at route 14 and the ridge across the river at x = −1050 are gone, in the raw network and in a scratch rebuild with the landscape.
- **B (retaining walls): all network-mesh wall vertices lie on mesh edges.** The worst of 576 is 3.9 mm off an edge. The wall's land face, 0.16 m from the wall line, is also a line of mesh edges.
  - In a scratch rebuild of river system and main landscape (not committed), T2's fill coverage rose from 37.19 % to **64.71 %**.
- **The four core walls (15, 16, 17, 21) are not moved.** The reasons are below.
  - For 15 and 21 the builder computes and records a bank-line route within 0.38 m of the core's mud edge (`coreWallRelocation.routes[].proposedRoute`). It is not applied: the core terrain's 0.4 m grid has no edges on that line, and in a scratch rebuild the landscape fill raised ground teeth on its water face.
  - For 16 and 17 the mud edge runs through mapped factory buildings.
  - One constant (`APPLY_CORE_WALL_RELOCATION`) switches 15 and 21 over.
- **What the parent must know:**
  - The mesh topology changed: 604,312 → 924,788 vertices, 1,188,610 → 1,829,479 triangles.
  - Until the landscape is rebuilt, the default page stops with "The landscape data could not load", after the console warning "Main landscape network topology differs". Three `npm test` checks fail for the same reason (12/17).
  - After a scratch rebuild everything passes except `check_road_bridges.mjs`, whose hard-coded road-surface table moves by up to 9 cm (Decision 3).
  - `build_historic_elevation.py` needs a one-line fix before it is rebuilt (Decision 2).

## Setup

- **Starting point.** My worktree started at 116c0ae, behind `main`, with no local changes. I fast-forwarded it to 3fffd45. Running the unchanged builder reproduced the committed mesh byte for byte, so the committed files are "base".
- **Missing inputs.** Git-ignored inputs missing from the worktree were supplied without writing to the main checkout: symlinks to the main checkout's `reference/spot-heights/mosaics/*`, a copy of `reference/topography-research-2026-09-28/terrain-epochs`, and a local `scenes/channelsea-sewer-panorama/review`.
- **Scratch folder:** `/tmp/claude-1000/-home-jic823-book-website/158d731a-06ad-4794-89f0-96291b5302cd/scratchpad/t14/`. It holds:
  - the measuring tools: `measure.py`, `meshcheck.py`, `wallcheck.py`, `wallbuild.py`, `sawtooth2.py`, `crest_window.py`, `trunc.py`, `syswater.py`, `hillshade.py`, `ring5*.py`;
  - `base/`, `after/` and `after-nobias/` (a variant without the placement offset; see Unsure);
  - the renders and logs;
  - `clone/`, a full scratch copy of the worktree with the new mesh, in which I rebuilt river system and main landscape;
  - `clone-base/`, the same with the base mesh and a freshly rebuilt landscape, used as the control.

## What I changed

Only `scripts/build_river_network.py` and the regenerated `docs/data/river-network.{json,f32,u32,rgb,silt,cover}`. Commits: 9c7be27 (first version), then a follow-up with the final mesh (no line on the tidal outline, placement offset, core walls proposed rather than moved) and this report.

- I did not change `river_bank_sections.py`. It builds the regional river-system banks; I only import its `Distance` helper.
- I did not change `docs/river-network.js`: the file layout is unchanged.
- I changed no check script.

### Mesh (A)

- **Shore bands.** Land within 8 m is triangulated by constrained Delaunay in bands between offset lines of the mapped outline at 0, 0.16, 0.5, 1 … 4.5, 4.9, 5.1, 5.5, 6, 7 and 8 m. Vertices are about every metre along the shore.
  - 0 m is the outline itself.
  - 0.16 m is the land face of a 0.32 m wall standing on it.
  - Spacing is 0.5 m over the mud shelf and crest, 1 m on the back slope.
  - There is deliberately **no line at 5 m**. That is where the tidal outline lies (`tide.polygons` = tidal channels buffered by 5 m). Vertices on it fell either side of it at random, and the landscape keeps native heights inside the outline and raises outside. In a scratch rebuild that showed as humps along the crest at Bow Locks. With lines at 4.9 and 5.1 m the humps are gone.
- **The grid elsewhere.** Channel beds and ground beyond 8 m keep the 1 m grid. Grid cells cut by the shoreline or by the 8 m line are clipped and triangulated on shared vertices; those two lines carry a vertex at every grid-line crossing.
  - The mesh outline is unchanged (boundary length 20,016.0 → 20,018.2 m). The extra 2.2 m is one hairline crack, at most 0.2 mm wide, at (−690.5, 239).
  - There are no T-junctions, no non-manifold edges and no reversed or flat triangles after float32 rounding.
- **Vertex indices kept.** Every vertex of the former grid keeps its index and position. Inside the bands it is inserted into the band triangle that contains it, at that triangle's height, so the surface is unchanged and no vertex is left out of the triangles.
  - The river system's `coreBedCorrections` still name the same points.
  - The 1 m nodes read by `marshLevel` in `docs/river-network.js` are still there.
- **Land section.** The section functions, crest heights, widths and photograph-bank profile are unchanged. Their distance inputs used to be 1 m raster distance transforms. They are now exact distances to the shoreline, the nearest tidal channel and sites/roads, and the Wall River east edge is taken per 0.25 m row, interpolated.
  - The raster distances ran on average 0.30–0.40 m (shoreline) and 0.45 m (sites and roads) beyond the exact ones.
  - So 0.35 m and 0.45 m are added to the exact distances. Each section keeps its former average placement but is smooth.
  - Bed (water) grid vertices keep their raster heights.
- **Mesh shoreline.** The outline is closed and then opened by 0.25 m (mitred). The drawn water polygons are unchanged.
  - 7.85 m² of gaps under 0.5 m between channel pieces are closed. Most is the 1 cm gap where two GIS pieces meet at x = −1050, where the old mesh had a 0.07 m land ridge across the river. The 72 grid nodes in closed gaps take the mean bed of their mapped-water neighbours.
  - 2.1 m² of water slivers under 0.5 m wide (clip tails at x = −1400 and −1050) make no banks.
- **JSON.** New record `bankMesh`: method, ring offsets, counts, `meshShoreline`, and evidence separating mapped from estimated.

### Retaining walls (B)

- **Wall routes** are computed exactly as before and are **identical to base**. The GIS outline is the 0 m band line, so every network-mesh wall vertex and segment lies on mesh edges. The 0.16 m land face is a band line too.
- **Core walls: `relocate_core_walls()`** computes, for each route inside the detailed core, a route on the landward edge of the core terrain's exposed tidal mud.
  - The mud test is the one the main landscape uses: `river-terrain.rgba` sediment > 200 and bank < 80.
  - The edge is found every 1 m along the land-side normal, median-filtered over 7 m and averaged over 5 m.
  - The offset tapers to zero within 10 m of the core boundary.
  - A route whose new line would cross mapped buildings by more than 1 m is reported as not relocatable.
- **JSON.** The result is recorded in `retainingEdges.coreWallRelocation`:
  - `applied: false`, with `notAppliedReason`;
  - per-route `proposedRoute`, `priorRoute`, mean and max offset, and distance from the mud edge;
  - `notRelocated` (16, 17) with figures and reason;
  - method and evidence. Mapped: the GIS outline and the plot. Estimated: the core channel section, so the proposed line is an interpreted bank line, not a surveyed wall.

## Numbers (base → after)

### Counts, files, area, heights

| | Base | After |
|---|---|---|
| Vertices (all in triangles) | 604,312 | 924,788 |
| Triangles | 1,188,610 | 1,829,479 (+54 %) |
| `.f32` / `.u32` | 7.25 / 14.26 MB | 11.10 / 21.95 MB |
| Plan area of the whole mesh | 594,305.0 m² | 594,305.0 m² |
| Bank plan area, land within 14 m | 232,673.5 m² | 232,691.7 m² (+0.008 %) |
| Bank surface area (3D), same | 246,053 m² | 245,207 m² (**−0.34 %**) |
| Height range | −1.716 … 2.054 | −1.716 … 2.054 |

- **No vertex below the old lowest bed or above the old highest crest.**
- **Local bounds.** Against the old mesh within 1.5 m, 4,164 vertices stand more than 0.02 m above the old local maximum and 1,063 more than 0.02 m below the old local minimum.
  - Most excesses are under 0.12 m, where the smooth section replaces the raster's row-to-row steps.
  - The larger ones are at source-window clip lines and narrow GIS features the raster missed: x = −1400, x = −1050, z ≈ −950, Bow Creek at (−500, 1350), and the narrow inlets west of Bow Locks.
- **Land grid vertices:** 104,685 changed by more than 1 mm. p95 0.083 m, mean −0.002 m, maximum 1.65 m (at a clip tail).
- **Bed grid vertices:** unchanged, except the 72 gap nodes and one sliver node that is now land.

### A: smoothness

The step is the change in distance from the mapped shoreline between adjacent points.

**Bow Locks, within 30 m of (−597, 859):**

| Measure | Base | After |
|---|---|---|
| T11's row test (0.5 m rows, z 845–875, drawn 0.06 m waterline): max / p95 | 0.507 / 0.432 m | **0.105 / 0.041 m** |
| Normal profiles every 0.5 m, waterline: max / p95 | 0.58 / 0.20 m | **0.04 / 0.04 m** |
| 1.1 m (high-water) contour: max (pairs over 0.3 m) | 0.652 (22) | 0.382 (5) |
| 1.4 m contour | 0.644 (71) | 0.395 (4) |
| 0.065 m contour, any distance from shore | 0.672 (38) | 0.608 (2) |
| Crest (normal profiles, centre of the top 5 cm): max / p95 | 4.15 / 0.82 m | 2.48 / 0.67 m |

- The remaining 1.1 m and 1.4 m pairs over 0.3 m are where those lines turn round the channel end at the lock entrance, (−589…−578, 836…849).
- The two 0.065 m pairs are on the nearly flat landward toe of the back slope at that channel end, 6.2–6.8 m from the water.
- The crest is a flat top there, so its position along a normal is ill-defined. The renders and the plan hillshade `hs/bow-final2.png` show a smooth crest.

**Whole network, plain bank only.** Plain bank excludes ground within 4 m of sites and roads, 5 m of the core, 4 m of passages, the marsh, and the photograph path and Wall River vista bank.

| Measure | Base | After |
|---|---|---|
| Profiles every 1 m (about 1,460 pairs), waterline: p95 / over 0.3 m / max | 0.396 / 153 / 0.70 | **0.030 / 1 / 0.36** |
| Profiles, high water (1.1 m) | 0.213 / 10 | **0.003 / 1** |
| Profiles, crest | 0.425 / 181 | **0.000 / 10** |
| 0.065 m contour, adjacent points | 0.413 / 6,584 / 0.98 | **0.030 / 18 / 0.61** |
| 1.1 m contour | 0.205 / 199 / 0.98 | **0.003 / 26 / 0.50** |
| 1.4 m contour | 0.379 / 5,978 / 0.95 | **0.005 / 21 / 0.52** |

- The remaining maxima are at the x = −1400 clip tail (the mesh ignores that sliver; my measure does not), at low-gradient toes and at channel ends.
- **Lea west window** (x −700…−600, z 700…1300): the low-water contour fell from 0.897 m max (494 pairs over 0.3 m) to 0.571 m (14). The high-water contour fell from 0.913 m (52) to 0.468 m (4). What is left is where the lines leave the shore at plot frontages: route 12 at x ≈ −631, and z ≈ 721–729.

### B: walls

| | Result |
|---|---|
| Network-mesh wall vertices (30 routes; core parts excluded) | 576; max distance to a mesh edge **0.0039 m**; 0 over 0.05 m |
| Land-face points 0.16 m landward | 1,470; max **0.000 m** |
| Core walls 15, 16, 21 and the core part of 17 | on the core's 0.4 m grid, which is not in my files |

**Core walls:**

| Route | Length | Result |
|---|---|---|
| 15 | 53.0 m | Proposed route 7.65 m inland (8.16 max). Independent mud-edge contour: max 0.38 m, median 0.09 m from it. Crosses no building. **Not applied.** |
| 21 | 41.8 m | Proposed 7.50 m inland. Max 0.23 m, median 0.06 m from the mud edge. **Not applied.** |
| 16 | 95.9 m | **Not relocatable.** The mud-edge line would cross buildings for 80.9 m. Nearest building median 1.9 m from the outline; a building lies inside the mud edge at 92 % of stations. |
| 17 | 159.3 m | **Not relocatable.** Would cross buildings for 90.4 m. Nearest building median 5.6 m; 96 % of stations. |

**Why 15 and 21 are not moved.** I first built with them moved and rebuilt the landscape in scratch (render `views-cascade-v1/x-wall-r15-relocated.png`).
- The landscape fill raised core cells on the water side of the moved wall: a row of ground teeth up its face, because the 0.4 m core grid has no edge on the wall line.
- The landscape's land-side test (wet samples 1–5 m out) became a tie on both sides (96 ambiguous stations).
- The wall rose 3.1–3.5 m above a mud slope.

Kept on the outline (`views-cascade/x-wall-r15-relocated.png`), the wall stands clean at the water's edge as before. Moving them is a one-constant change once the core mesh carries the wall lines or the landscape builder clears core wall faces (Decision 5).

**Scratch rebuild of the chain** (`clone/`: river system, then main landscape, then T2's `measure_walls.py`; not committed). The control, `clone-base/`, is the base mesh with a freshly rebuilt landscape. It gives exactly the committed figures (37.19 %, 0 network steps), so every change below comes from this branch.

| | Committed / control | Scratch rebuild, new mesh |
|---|---|---|
| Within 0.5 m of crest at 1 m and 3 m | 37.19 % | **64.71 %** |
| At 1 m only / 3 m only | 41.76 / 72.74 % | 69.37 / 73.46 % |
| Void at 1 m | 1,218.7 m | 640.9 m |
| Largest adjacent crest jump | 0.078 | 0.078 |
| Ground above high water at the wall's water face | 0 m | 0 m |
| Steps (network / core / system) | 0 / 52 / 214 | **3** / 52 / 214 |

- **The 3 new network steps** are at (−665, −219), (−635, −256) and (−633, −285). There a Stratford High Street corridor vertex, held at about 2.65 m, sits 0.4–0.9 m from a vertex on the 0.12 m tidal shelf (Decision 4).
- **The rebuilt river system** changes only its JSON (`coreBedCorrections`, hashes); its mesh files are byte-identical. After it, no network vertex in drawn system water stands above −0.7 m.
- **Remaining fill failures** are mainly:
  - core routes 15, 16, 17 and 21 (on preserved mud, about 350 m);
  - route 14 (building behind);
  - routes 6, 8, 20 and 29;
  - wall ends.

## Checks

- **River-network Python checks, base and after:** `check_river_tides`, `check_marsh_ditches`, `check_core_river_connections`, `check_gardens`, `check_regional_marsh`, `check_river_banks` and `check_abbey_station_plan` all PASS.
- **Stale hashes, base and after:**
  - `check_main_landscape.py` and `check_historic_elevation.py` fail on a stale `ground-plan.json` hash.
  - `check_river_system.py` fails on that hash at base, and now first on `river-network.json`.
  - In `clone/` (rebuilt), `check_river_system.py`, `check_main_landscape.py`, `check_main_landscape.mjs`, `check_ground_sampler.mjs` and `check_river_banks.py` all PASS.
- **All 75 `scripts/check_*.py`:** the same exit code before and after for every one. This was run on the first committed version; the final mesh differs only in the ring set and the walls. Many fail at base because git-ignored reference folders are missing from the worktree. `check_panorama.py` tests whatever is served on 4173, not this worktree.
- **`npm test` in the worktree: 12/17.**
  - `check_main_landscape.mjs`, `check_road_bridges.mjs` and `check_tram_rails.mjs` fail with "Main landscape network topology differs": the stale landscape against the new mesh. Expected until the rebuild.
  - `check_flood_demo.mjs`: known (stale `terrain-1900.json`).
  - `check_drainage_connections.mjs`: known. With the mosaics present it now stops at a stale `infrastructure.json` hash, which is not from this branch.
- **`npm test` in `clone/` (rebuilt): 14/17.** The two known failures plus `check_road_bridges.mjs`.
  - That check holds a hard-coded table of road-surface heights at 1 mm tolerance. 45 stations on four bridge approaches differ, by up to 9 cm: st-thomas-bridge 16, marshgate-lane-connection-0 21, hunts-lane-connection-0 5, st-michaels-bridge 3.
  - Every other assertion in it passes, including "only footings and piers in the channel".
  - The control rebuild (`clone-base/`) passes the whole check, so the differences come from this change.
- **I changed no check script and no assertion.**

## Smoke

- **Base snapshots first,** from this worktree on 4189, with a scratch copy of `review_smoke.py` that waits 900 s for the tween and can append a query:
  - `t14-base` (default page): 0 page errors, 8,261,290 triangles.
  - `t14-base-raw` (`&mainLandscape=baseline`): 0 page errors, 8,164,665 triangles.
- **`t14-after-raw --compare t14-base-raw`** (final mesh): ready, **0 page errors**, 4 differences, all explained:
  - `riverNetwork.vertices` 604,312 → 924,788 and `riverNetwork.triangles` 1,188,610 → 1,829,479;
  - `triangles` (8,164,665 → 8,805,534) and `reflection.triangles`, each +640,869, exactly the mesh's extra triangles. The wall routes are unchanged.
- **`t14-after` (default page),** run on the first committed mesh: never ready; the script timed out after 600 s.
  - A probe shows no page error. The app catches the throw, logs the console warning "Main landscape network topology differs", and shows its stall message.
  - This is the expected consequence of the stale landscape and goes when it is rebuilt.
- **Screenshots** time out under the software renderer, which the script treats as non-fatal.

## Renders

All folders are under `t14/`:
- `views-before-raw/`, `views-after-raw/`: this worktree with `&mainLandscape=baseline`, so the raw network without the landscape blend. The stale blend cannot be applied to the new mesh at all.
- `views-before-blend/`: base with the committed landscape.
- `views-base-cascade/` and `views-cascade/`: the control and the new mesh, each with a freshly rebuilt landscape. This is the fair before and after of the final look.

| Camera | Verdict |
|---|---|
| `author-bow-locks` | **Fixed.** Before, the waterline and bank toe zig-zag in 1–4 m teeth (raw, committed blend and control alike). After, both are smooth curves. With the landscape the bank reads as native shelf, a 1:1.5 face and the crest, all smooth. The first rebuild showed crest humps; the 4.9/5.1 m lines removed them. |
| `connection-bow-locks` | Unchanged junction in the rebuilt landscape. In the raw render, band vertices inside the Limehouse Cut water are not yet lowered (stale `coreBedCorrections`), a faint lip that the river-system rebuild removes. |
| `lea-west-bank-across-1200` | From this distance the far bank is a thin strip. Its crest was scalloped and is now even. |
| `wall-r14-water-side` | **Fixed.** The near bank's saw-toothed waterline is a smooth edge. The far wall is clean and the building unchanged. |
| `x-join-1050-across` | **Fixed.** Before, a thin ridge line crossed the river and both banks were ragged. After, the river is clear and the banks are smooth. |
| `x-wall-r4-land-close` | With the landscape, the fill now reaches the wall coping behind route 4. |
| `x-wall-r15-relocated` | With the wall kept on the outline: a clean wall face, as in the control. The moved version (v1) showed teeth. |
| `x-bow-locks-overhead`, `x-wall-r4-water-side`, `x-lea-west-bank-along-900`, `x-wall-r16-water-side` | No visible change apart from smoother bank lines. |

## Stale hashes after this change

| File | Stored hash of |
|---|---|
| `main-landscape-1900.json` | `river-network.json`, `.f32`, `.u32` |
| `river-system-1900.json` | `river-network.json`, `.f32` |
| `terrain-1900.json` | `river-network.json`, `.f32` |
| `landscape-flood-1900.json` | `river-network.json` |
| `lower-lea-region/index.json` | `river-network.json` |

All but the last were already stale on `ground-plan.json` at base.

## What I did NOT do

- I did not rebuild or commit the river system, main landscape, historic elevation, flood or lower-lea-region outputs. The scratch rebuilds used `main` as of 3fffd45, not the later `main` with T13/T15 and the two landscape rebuilds.
- I did not touch `river_bank_sections.py`, `docs/river-network.js`, any check, T13/T15/T16 files, or the core terrain.
- I did not change water polygons, bed heights (apart from the 72 gap nodes), the bank section functions and heights, or the wall routes.
- I did not move any core wall.
- I did not smooth the underwater bed. Its first raster row still steps beside the shoreline. It is always under opaque water (tide 0.06–1.1 m), and the drawn waterline wobbles by at most about 5 cm because of it.

## Unsure

- **The placement offset (0.35 m / 0.45 m).** I kept the sections where the raster had them on average, the reading of "do not change the bank policy heights" that moves least: p95 0.08 m, mean −0.002 m. Without the offset (`after-nobias/`):
  - the waterline sits exactly on the GIS line (Bow Locks row test 0.24 m);
  - every bank moves about 0.4 m seaward (p95 0.19 m);
  - the rebuilt landscape had 18 rather than 3 steps.
- **Core walls.** I preferred not to ship a visible regression (teeth) over meeting "relocate" literally. The proposal for 15 and 21 is ready if the parent prefers otherwise.
- **Band width and ring spacing** (8 m; 0.5 m up to 6 m) are judgement calls; wider or denser bands add triangles.
- **Results on the moved-on `main` were not verified.** The scratch rebuilds predate T13's road retrace and T15's railways. The High Street steps and road-bridge figures may differ after the parent's rebuild.
- **Not run:** `build_historic_elevation.py`, the flood or lower-lea-region builds, and the GIS and glTF exports, on the new mesh.

## Decisions for the parent

1. **Rebuild order after merging:**
   - `build_river_system.py` first. Until then, 2,033 new network vertices inside drawn system water stand up to 1.5 m at junctions such as Bow Locks.
   - `build_main_landscape.py` next. Until then the default page stops. My scratch build took 6.5 min and passed both landscape checks.
   - Then historic elevation (after Decision 2), the landscape flood and the lower-lea-region index for their hashes, and the GIS exports.
2. **Patch `build_historic_elevation.py` before rebuilding it** (not in my files). It writes every network vertex into a 1 m grid with `(x - x0).astype(int)`. Run unchanged, the new off-grid vertices would overwrite 9,304 baseline nodes by up to 1.28 m. Keep only grid vertices (all still present, at their drawn heights):

   ```python
   inside = (...existing test...) & (positions[:, 0] == np.round(positions[:, 0])) & (positions[:, 2] == np.round(positions[:, 2]))
   ```

3. **`check_road_bridges.mjs`.** Refresh its recorded road-surface table after the rebuild, or widen its 1 mm tolerance. The approaches drape over the changed bank, by up to 9 cm at the St Thomas bridge west approach; the control rebuild passes.
4. **The 3 network steps at the High Street** in the rebuilt landscape: street-corridor vertices next to the tidal shelf, which the landscape builder exempts from the tidal 1:1.5 face. T15 or the parent: batter the street edge to the tidal outline, or accept them.
5. **Core walls.**
   - To move 15 and 21, set `APPLY_CORE_WALL_RELOCATION = True` once either the core terrain carries the wall lines, or the landscape builder clears core wall faces (as `clear_wall_faces` does for the network) and takes the land side from the mud mask rather than wet samples 1–5 m out.
   - For 16 and 17, the core channel section runs under factory buildings that front the river. Trim it to the building frontage in the river-terrain build, or accept walls on preserved mud.
6. **File size.** The network mesh grows from 1.19 M to 1.83 M triangles (+11.5 MB for `.f32` and `.u32` together). Accept that, or narrow the bands (for example to 6 m), or thin the rings beyond the crest.
