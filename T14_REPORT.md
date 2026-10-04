# T14 report: river bank mesh along the shoreline, retaining walls on mesh edges

3 October 2026. Worktree branch `worktree-agent-a64e73c3e860d731a`.

## Bottom line

- **A (bank staircase): fixed in the river-network build.** Land within 8 m of the mapped channels is now triangulated in bands that follow offset lines of the mapped shoreline. The bank section is evaluated from exact distances, keeping the former average placement, so it is smooth instead of stepping with a 1 m raster.
  - Bow Locks, T11's row test: the largest step of the drawn waterline between adjacent rows fell from 0.51 m to **0.11 m** (95th percentile 0.43 → 0.04 m).
  - Network-wide, on plain bank, waterline profiles that step by more than 0.3 m fell from 153 to 1 pair (95th percentile 0.40 → 0.03 m).
  - The 1.1 m high-water line and the crest behave the same way; the numbers are below.
  - In the renders the Bow Locks saw-tooth, the bank at route 14 and the ridge across the river at x = −1050 are gone.
- **B (retaining walls): every network-mesh wall vertex lies on a mesh edge.** The worst of 576 vertices is 3.9 mm off. The wall's land face, 0.16 m from the wall line, is also a line of mesh edges.
  - In a scratch rebuild of the chain (river system, then main landscape; not committed), T2's fill coverage rose from 37.19 % to **64.75 %**.
- **Core walls:**
  - Routes 15 and 21 (94 m) are moved onto the core's bank line, the landward edge of its tidal mud. The worst vertex is 0.38 m from that edge.
  - Routes 16 and 17 (255 m) stay where they are. Mapped factory buildings stand inside the core's channel section there, so the mud edge runs through them.
- **What the parent must know before merging:**
  - The mesh topology changed: 604,312 → 906,907 vertices and 1,188,610 → 1,793,723 triangles. The committed main landscape no longer fits it.
  - Until the landscape is rebuilt, the default page stops with "The landscape data could not load", after the console warning "Main landscape network topology differs".
  - For the same reason three `npm test` checks fail in the worktree (12/17).
  - In my scratch rebuild the landscape builder, both landscape checks, the ground sampler and the river-system checks all pass.
  - `build_historic_elevation.py` needs a one-line fix before it is rebuilt (Decision 2).

## Setup

- My worktree started at 116c0ae, behind `main`, with no local changes. I fast-forwarded it to `main` (3fffd45) first.
- Running the unchanged builder reproduced the committed mesh byte for byte, so the committed files are my "base". `river-network.json` differed only in `planSha256` (ground-plan.json has changed since the last build) and one coordinate at 1e-14.
- Git-ignored inputs missing from the worktree were supplied without writing to the main checkout:
  - symlinks to the main checkout's `reference/spot-heights/mosaics/*`;
  - a copy of `reference/topography-research-2026-09-28/terrain-epochs`;
  - a local `scenes/channelsea-sewer-panorama/review`.
- Scratch folder: `/tmp/claude-1000/-home-jic823-book-website/158d731a-06ad-4794-89f0-96291b5302cd/scratchpad/t14/`.
  - Measuring tools: `measure.py`, `meshcheck.py`, `wallcheck.py`, `wallbuild.py`, `sawtooth2.py`, `crest_window.py`, `trunc.py`, `syswater.py`, `hillshade.py`.
  - The base files are in `base/`, the after files in `after/`.
  - Renders and logs are in the same folder.
  - `clone/` is a full scratch copy of the worktree with the new mesh, in which I rebuilt the river system and main landscape.
  - `clone-base/` is the same with the base mesh and a freshly rebuilt landscape.

## What I changed

Only `scripts/build_river_network.py` and the regenerated `docs/data/river-network.{json,f32,u32,rgb,silt,cover}`.

- I did not change `river_bank_sections.py`. It builds the regional river-system banks; I only import its `Distance` helper.
- I did not change `docs/river-network.js`: the file layout is unchanged.
- I changed no check script.
- The retaining-wall routes are computed in the builder, not read from a data file, so the relocation is done there and recorded in the JSON.

### Mesh (A)

- **Shore bands.** Land within 8 m is triangulated by constrained Delaunay in bands between offset lines of the mapped outline: 0, 0.16, 0.5, 1, 1.5 … 6, 7 and 8 m. Vertices are about every metre along the shore.
  - 0 m is the outline itself.
  - 0.16 m is the land face of a 0.32 m wall standing on it.
  - The 0.5 m spacing covers the mud shelf and the crest; 1 m covers the back slope.
- **The grid elsewhere.** Channel beds and ground beyond 8 m keep the 1 m grid. Grid cells cut by the shoreline or by the 8 m line are clipped and triangulated on shared vertices; those two lines carry a vertex at every grid-line crossing.
  - The mesh outline is unchanged (boundary length 20,016.0 → 20,018.2 m). The extra 2.2 m is one hairline crack, at most 0.2 mm wide, at (−690.5, 239).
  - There are no T-junctions, no non-manifold edges and no reversed or flat triangles after float32 rounding.
- **Vertex indices kept.** Every vertex of the former grid keeps its index and position. Inside the bands it is inserted into the band triangle that contains it, at that triangle's height, so the surface is unchanged and no vertex is left out of the triangles.
  - The river system's `coreBedCorrections` still name the same points.
  - The 1 m nodes that `marshLevel` in `docs/river-network.js` reads are still there.
- **Land section.** Section functions, crest heights, widths and the photograph-bank profile are unchanged. Their distance inputs used to be 1 m raster distance transforms. They are now exact distances to the shoreline, the nearest tidal channel and sites/roads, and the Wall River east edge is taken per 0.25 m row, interpolated.
  - The raster distances ran on average 0.30–0.40 m (shoreline) and 0.45 m (sites and roads) beyond the exact ones, and stepped row by row.
  - So 0.35 m and 0.45 m are added to the exact distances. Each section keeps its former average placement, but smooth.
  - Without this offset the waterline sits exactly on the outline, but every land vertex moves about 0.4 m seaward (p95 height change 0.19 m against 0.08 m now). I built and measured that version too; see Unsure.
- **Bed.** Bed (water) grid vertices keep their raster heights exactly.
- **Mesh shoreline.** The outline is closed and then opened by 0.25 m (mitred) before meshing. The drawn water polygons are unchanged.
  - 7.85 m² of gaps under 0.5 m between channel pieces are closed. Most is the 1 cm gap where two GIS pieces meet at x = −1050: the old mesh had a 0.07 m land ridge across the river there (render `x-join-1050-across`). The 72 grid nodes in closed gaps take the mean bed of their mapped-water neighbours.
  - 2.1 m² of water slivers under 0.5 m wide are ignored. These are clip tails at x = −1400 and −1050.
- **JSON.** New record `bankMesh`: method, ring offsets, vertex counts, `meshShoreline`, and evidence separating mapped from estimated.

### Retaining walls (B)

- The wall routes are computed as before, from the GIS outline. That outline is the 0 m band line, so every network-mesh wall vertex and segment lies on mesh edges. The 0.16 m land face is a band line too.
- **Core walls.** Routes inside the detailed core move from the GIS outline to the landward edge of the core terrain's exposed tidal mud.
  - The mud test is the same one the main landscape uses: `river-terrain.rgba` sediment > 200 and bank < 80.
  - The edge is found every 1 m along the land-side normal, then median-filtered over 7 m and averaged over 5 m.
  - The offset tapers to zero within 10 m of the core boundary.
  - Vertices are every 2 m inside the core; outside it the original vertices are kept.
  - A route whose new line would cross mapped buildings by more than 1 m is left alone and reported.
- **JSON.** New record `retainingEdges.relocatedRoutes`:
  - `routes`, each with `priorRoute`, mean and max offset, and distance from the mud edge;
  - `notRelocated`, with the reason and figures;
  - method and evidence. Mapped: the GIS outline and the plot. Estimated: the core channel section, so the new line is an interpreted bank line, not a surveyed wall.

## Numbers (base → after)

### Counts, files, area, heights

| | Base | After |
|---|---|---|
| Vertices (all in triangles) | 604,312 | 906,907 |
| Triangles | 1,188,610 | 1,793,723 (+51 %) |
| `.f32` / `.u32` | 7.25 / 14.26 MB | 10.88 / 21.52 MB |
| Plan area of the whole mesh | 594,305.0 m² | 594,305.0 m² |
| Bank plan area, land within 14 m | 232,673.5 m² | 232,691.7 m² (+0.008 %) |
| Bank surface area (3D), same | 246,053 m² | 245,178 m² (**−0.36 %**) |
| Height range | −1.716 … 2.054 | −1.716 … 2.054 |

- **No vertex below the old lowest bed or above the old highest crest.**
- **Local bounds.** Against the old mesh within 1.5 m, 4,068 vertices stand more than 0.02 m above the old local maximum and 1,061 more than 0.02 m below the old local minimum.
  - Most excesses are under 0.12 m, where the smooth section replaces the raster's row-to-row steps.
  - The larger ones are at source-window clip lines and narrow GIS features the raster missed: x = −1400, x = −1050, z ≈ −950, Bow Creek at (−500, 1350), and the narrow inlets west of Bow Locks.
- **Land grid vertices:** 104,775 changed by more than 1 mm. p95 0.084 m, mean −0.002 m, maximum 1.65 m (at a clip tail).
- **Bed grid vertices:** unchanged, except the 72 gap nodes and one sliver node that is now land.

### A: smoothness

The step is the change in distance from the mapped shoreline between adjacent points.

**Bow Locks, within 30 m of (−597, 859):**

| Measure | Base | After |
|---|---|---|
| T11's row test (0.5 m rows, z 845–875, drawn 0.06 m waterline): max / p95 | 0.507 / 0.432 m | **0.105 / 0.041 m** |
| Normal profiles every 0.5 m, waterline: max / p95 | 0.58 / 0.20 m | **0.04 / 0.04 m** |
| 1.1 m (high-water) contour: max (pairs over 0.3 m) | 0.652 (22) | 0.444 (7) |
| 1.4 m contour | 0.644 (71) | 0.395 (6) |
| 0.065 m contour, any distance from shore | 0.672 (38) | 0.608 (2) |
| Crest (normal profiles, centre of the top 5 cm): max / p95 | 4.15 / 0.82 m | 2.48 / 0.66 m |

- The 1.1 m and 1.4 m steps over 0.3 m are all at (−589…−578, 836…849), where those lines turn round the channel end at the lock entrance.
- The two 0.065 m pairs are on the landward toe of the back slope at the same channel end, 6.2–6.8 m from the water, where the ground is nearly flat.
- The crest there is a flat top (retained side and the channel end), so its position along a normal is ill-defined. Renders and the plan hillshade `hs/bow-final2.png` show a smooth crest and smooth contours.

**Whole network, plain bank only.** Plain bank excludes ground within 4 m of sites and roads, 5 m of the core, 4 m of passages, the marsh, and the photograph path and Wall River vista bank.

| Measure | Base | After |
|---|---|---|
| Profiles every 1 m (about 1,460 pairs), waterline: p95 / over 0.3 m / max | 0.396 / 153 / 0.70 | **0.030 / 1 / 0.36** |
| Profiles, high water (1.1 m) | 0.213 / 10 / 0.62 | **0.003 / 1** |
| Profiles, crest | 0.425 / 181 / 3.3 | **0.000 / 10** |
| 0.065 m contour, adjacent points | 0.413 / 6,584 / 0.98 | **0.030 / 18 / 0.61** |
| 1.1 m contour | 0.205 / 199 / 0.98 | **0.003 / 27 / 0.57** |
| 1.4 m contour | 0.379 / 5,978 / 0.95 | **0.005 / 27 / 0.52** |

- The remaining contour maxima are at the x = −1400 clip tail (the mesh ignores that sliver; my measure does not), at low-gradient toes and at channel ends.
- In the Lea west window (x −700…−600, z 700…1300) the low-water contour fell from 0.897 m max (494 pairs over 0.3 m) to 0.571 m (15). The remainder is where the line leaves the shore at plot frontages: route 12 at x ≈ −631, and z ≈ 721–729.

### B: walls

| | Result |
|---|---|
| Network-mesh wall vertices (30 routes; core parts excluded) | 576; max distance to a mesh edge **0.0039 m**; 0 over 0.05 m |
| Same, segments sampled every 0.5 m | max 0.002 m (core boundary of route 17: 0.105 m) |
| Land-face points 0.16 m landward | 1,470; max **0.000 m** |
| Core-wall vertices | lie on the core's 0.4 m grid, which is not in my files: up to 0.19 m from a core grid line |

**Core walls:**

| Route | Length | Result |
|---|---|---|
| 15 | 52.7 m | **moved** 7.65 m mean (8.16 max). Independent mud-edge contour: max 0.38 m, median 0.09 m from the new vertices. Crosses no building. |
| 21 | 40.8 m | **moved** 7.50 m mean. Max 0.23 m, median 0.06 m from the mud edge. Crosses no building. |
| 16 | 95.9 m | **not moved.** The mud-edge line would cross buildings for 80.9 m. Nearest building median 1.9 m from the outline; at 92 % of stations a building lies inside the mud edge. |
| 17 | 159.3 m | **not moved.** Would cross buildings for 90.4 m. Nearest building median 5.6 m; 96 % of stations. |

On 16 and 17 the building frontage is the real bank line (render `x-wall-r16-water-side`: buildings stand right behind the wall).

**Scratch rebuild of the chain** (`clone/`; T2's `measure_walls.py`). The committed landscape is stale; a fresh rebuild on the base mesh (`clone-base/`) gives exactly the committed figures (37.19 %, 0 network steps), so the changes below come from this branch.

| | Committed | Scratch rebuild, new mesh |
|---|---|---|
| Within 0.5 m of crest at 1 m and 3 m | 37.19 % | **64.75 %** |
| At 1 m only / 3 m only | 41.76 / 72.74 % | 69.42 / 77.97 % |
| Void at 1 m | 1,218.7 m | 639.5 m |
| Largest adjacent crest jump | 0.078 | 0.078 |
| Ground above high water at the wall's water face | 0 m | 93.5 m: routes 15 and 21, whose water side is now the core mud bank top, by design |
| Steps (network / core / system) | 0 / 52 / 214 | **3** / 52 / 214 |

- **The 3 new network steps** are at (−665, −219) and (−635, −256). There a Stratford High Street corridor vertex, held at about 2.6 m, now sits 0.3–0.9 m from a preserved tidal vertex (Decision 4). Without the placement offset there were 18 such steps.
- **The rebuilt river system** changes only its JSON (`coreBedCorrections`, hashes); its mesh files are byte-identical. After it, no network vertex in drawn system water stands above −0.7 m.
- **Remaining fill failures** are mainly:
  - core routes 16 and 17 (preserved mud);
  - route 14 (building behind);
  - routes 6, 8, 20 and 29;
  - wall ends;
  - the 1 m station on moved routes 15 and 21 (Decision 5).

## Checks

- **River-network Python checks, base and after:** `check_river_tides`, `check_marsh_ditches`, `check_core_river_connections`, `check_gardens`, `check_regional_marsh`, `check_river_banks` and `check_abbey_station_plan` all PASS.
- **Stale hashes, base and after:**
  - `check_main_landscape.py` and `check_historic_elevation.py` fail on a stale `ground-plan.json` hash.
  - `check_river_system.py` fails on the same at base, and now first on `river-network.json`.
  - In `clone/` (rebuilt), `check_river_system.py`, `check_main_landscape.py`, `check_main_landscape.mjs`, `check_ground_sampler.mjs` and `check_river_banks.py` all PASS.
- **All 75 `scripts/check_*.py`:** the same exit code before and after for every one. Many fail at base because git-ignored reference folders are missing from the worktree. `check_panorama.py` tests whatever is served on 4173, not this worktree.
- **`npm test` in the worktree: 12/17.**
  - `check_main_landscape.mjs`, `check_road_bridges.mjs` and `check_tram_rails.mjs` fail with "Main landscape network topology differs": the stale landscape against the new mesh. Expected until the parent rebuilds.
  - `check_flood_demo.mjs`: known (stale `terrain-1900.json`).
  - `check_drainage_connections.mjs`: known. With the mosaics present it now stops at a stale `infrastructure.json` hash, which is not from this branch.
- **`npm test` in `clone/` (rebuilt): 14/17.** Only the two known failures plus `check_road_bridges.mjs`.
  - That check holds a hard-coded table of road-surface heights at 1 mm tolerance. 44 stations on four bridge approaches differ, by up to 9 cm (st-thomas-bridge, marshgate-lane-connection-0, hunts-lane-connection-0, st-michaels-bridge).
  - Every other assertion in it passes, including "only footings and piers in the channel".
  - On the base mesh with a fresh landscape (`clone-base/`) the same check passes, so these differences come from this change.
- **I changed no check script and no assertion.**

## Smoke

- **Base snapshots first,** from this worktree on 4189, with a scratch copy of `review_smoke.py` that waits 900 s for the tween and can append a query:
  - `t14-base` (default page): 0 page errors, 8,261,290 triangles.
  - `t14-base-raw` (`&mainLandscape=baseline`): 0 page errors, 8,164,665 triangles.
- **`t14-after-raw --compare t14-base-raw`:** ready, **0 page errors**, 4 differences, all explained:
  - `riverNetwork.vertices` 604,312 → 906,907 and `riverNetwork.triangles` 1,188,610 → 1,793,723: the mesh.
  - `triangles` and `reflection.triangles` +605,323: the mesh (+605,113) plus 210 wall triangles, because moved routes 15 and 21 have 21 more segments at 10 triangles each.
- **`t14-after` (default page):** never ready; the script timed out after 600 s.
  - A probe shows no page error. The app catches the throw, logs the console warning "Main landscape network topology differs", and shows its stall message.
  - This is the expected consequence of the stale landscape and goes when it is rebuilt.
- **Screenshots** timed out under the software renderer, which the script treats as non-fatal.

## Renders

- Folders, all under `t14/`:
  - `views-before-raw/`, `views-after-raw/`: this worktree, `&mainLandscape=baseline`, so the raw network without the landscape blend. The stale blend cannot be applied to the new mesh at all.
  - `views-before-blend/`: base with the committed landscape.
  - `views-cascade/`: `clone/`, with the rebuilt river system and landscape.
  - `views-base-cascade/`: `clone-base/`, base mesh with a rebuilt landscape.
- **`author-bow-locks`:** **fixed.** Before, the waterline and the bank toe zig-zag in 1–4 m teeth. After, both are smooth curves following the channel.
- **`connection-bow-locks`:** the junction looks the same.
  - In the raw after render, the band vertices inside the Limehouse Cut water are not yet lowered (stale `coreBedCorrections`). This shows as a faint lip at the far end of the passage.
  - The rebuilt river system corrects it: 0 vertices left above −0.7 m.
- **`lea-west-bank-across-1200`:** from this distance the far bank is a thin strip. Before, its crest was scalloped; after, it is even.
- **`wall-r14-water-side`:** **fixed.** The near bank's saw-toothed waterline is now a straight smooth edge. The far wall and the building are unchanged.
- **`x-join-1050-across`:** **fixed.** Before, a thin ridge line crossed the river and both banks were ragged. After, the river is clear and both banks are smooth.
- **`x-bow-locks-overhead`:** the staircase banks are now smooth offset curves. The notched outline of the strip's west end is the mapped GIS outline, unchanged.
- **`x-wall-r4-water-side`, `x-lea-west-bank-along-900`, `x-wall-r16-water-side`:** no visible change apart from a smoother bank top.
- CASCADE_RENDERS

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

- I did not rebuild or commit the river system, main landscape, historic elevation, flood or lower-lea-region outputs. The scratch rebuilds are evidence only.
- I did not touch `river_bank_sections.py`, `docs/river-network.js`, any check, T13/T15/T16 files, or the core terrain.
- I did not change water polygons, bed heights (apart from the 72 gap nodes) or the bank section functions and heights.
- I did not move core routes 16 and 17.
- I did not smooth the underwater bed. Its first raster row still steps beside the shoreline. It is always under opaque water (tide 0.06–1.1 m), and the drawn waterline wobbles by at most about 5 cm because of it.

## Unsure

- **The placement offset (0.35 m / 0.45 m).** I chose to keep the sections where the raster had them on average, which is the reading of "do not change the bank policy heights" that moves the least: p95 0.08 m, mean −0.002 m. The alternative is exact distances with no offset (`after-nobias/` in scratch). That puts the waterline exactly on the GIS line (Bow Locks row test 0.24 m), but moves every bank about 0.4 m seaward (p95 0.19 m) and gave 18 rather than 3 landscape steps. Either is a one-constant change.
- **The mud edge as the core "bank line"** for routes 15 and 21. The crest of the core's mud bank is about 1.5–2 m nearer the water. I chose the edge so that the land behind is not preserved mud and can be filled.
- **Band width and ring spacing** (8 m; 0.5 m up to 6 m) are judgement calls. Wider or denser bands add triangles.
- **Not verified:** I did not run `build_historic_elevation.py`, the flood or lower-lea-region builds, the GeoTIFF/GeoPackage export or the glTF export on the new mesh.

## Decisions for the parent

1. **Rebuild order after merging:**
   - `build_river_system.py` first. Until then, 1,812 new network vertices inside drawn system water stand up to 1.5 m at junctions such as Bow Locks.
   - `build_main_landscape.py` next. Until then the default page stops. My scratch build took 6.5 min and passed both landscape checks.
   - Then historic elevation (after Decision 2), the landscape flood and the lower-lea-region index for their hashes, and the GIS exports.
2. **Patch `build_historic_elevation.py` before rebuilding it** (not in my files). It writes every network vertex into a 1 m grid with `(x - x0).astype(int)`. Run unchanged, the new off-grid vertices would overwrite 9,307 baseline nodes by up to 1.27 m. Keep only grid vertices (all still present, at their drawn heights):

   ```python
   inside = (...existing test...) & (positions[:, 0] == np.round(positions[:, 0])) & (positions[:, 2] == np.round(positions[:, 2]))
   ```

3. **`check_road_bridges.mjs`.** Its recorded road-surface table must be refreshed after the rebuild, or its tolerance widened. The approaches drape over the changed bank, by up to 9 cm at the St Thomas bridge west approach. The base-mesh rebuild passes this check.
4. **The 3 network steps at the High Street** in the rebuilt landscape: street-corridor vertices next to preserved tidal vertices, which the landscape builder exempts from the tidal 1:1.5 face. T15 or the parent: batter the street edge to the tidal outline, or accept them.
5. **Moved walls 15 and 21 in the landscape builder.** The GIS water is now about 7.5 m away, so the land-side test (wet samples 1–5 m out) is a tie on both sides. It falls back to the left-hand side, which happens to be land for both. Their crest came out at 3.06 m and 3.53 m, and the fill 1 m behind reaches 2.0–2.5 m. Consider a longer probe or the core mud mask for the side, and check the crest rule there.
6. **Routes 16 and 17 and the core channel section.** The core terrain's tidal mud runs about 7.5 m inland, under factory buildings that front the river. Trim the river-terrain channel section to the building frontage (a river-terrain task), or accept walls on preserved mud.
7. **File size.** The network mesh grows from 1.19 M to 1.79 M triangles (+7.3 MB for `.f32` and `.u32` together). Accept that, or narrow the bands (for example to 6 m), or thin the rings beyond the crest.
