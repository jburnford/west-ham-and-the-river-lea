# T2 report: retaining walls with fill behind them

3 October 2026. Worktree branch `worktree-agent-add461e9935cdd0a3`.

## Bottom line

The saw-tooth crest is fixed: the largest step between adjacent crest vertices fell from 0.648 m to 0.078 m. The free-standing walls are much improved in every render. The fill acceptance criterion is **not met**. Ground within 0.5 m of the crest at both 1 m and 3 m behind the wall went from 0 % to 37 % of wall length in the committed version, against a target of 95 %. The target cannot be reached inside the permitted files without breaking another rule (see "Why 95 % is out of reach"). Step counts did not increase on any mesh, and the checks pass.

## Setup notes

- The worktree branch started 19 commits behind `main` and did not contain `build_main_landscape.py`. It had no local changes, so I fast-forwarded it to `main` (72d97c8) before starting.
- At that base, `check_main_landscape.py` already failed on a stale `ground-plan.json` input hash. Re-running the unchanged builder gave byte-identical meshes and changed only that hash, so the 706835e ground-plan change had no geometric effect. My regeneration refreshes the hash.
- The scratchpad directory is shared with the other task agents (T1 and T5 files were in it, and one `views-after/` directory was already in use). After I noticed, I moved all my files into `scratchpad/t2/`. One of my render runs had started writing into the shared `views-after/`; I stopped it and re-ran.

## What changed

Only `scripts/build_main_landscape.py` and the regenerated `docs/data/main-landscape-1900.json`, `.network.f32` (6,511 vertices raised, none lowered) and `.core.f32` (2 cells, at most +0.18 m) changed. `system`, `extension`, `background`, `faces`, `level` and `weight` are byte-identical to before.

1. **Crest.** For each wall, the crest is `1.65 + w6·(bankCrest − 1.65)`. Here `w6` is the marsh weight sampled 6 m behind the wall on its land side, and `bankCrest` is the existing observed along-bank profile. The land side is the side with fewer wet samples 1 to 5 m out. The result gets a 20 m running mean along the wall, then a grade-limited upper envelope (at most 0.02 m per metre). Range is 1.65 to 3.44 m, with no adjacent jump of 0.1 m or more.
2. **Fill** (`wall_fill`, `fill_behind_walls`). On the land side, the ground is filled level with the coping out to 3.4 m from the wall line, then falls at 1:1.5 until it meets existing ground. This happens at any marsh weight. The fill never lowers ground. It is excluded from:
   - water;
   - street corridors (`road_fits`);
   - building footprints: factory-buildings render polygons and holders, plus ground-plan `mappedFactories`, `houses` and `terraces`.

   Where there is no wall (beyond wall ends, ditch mouths) it is battered at 1:1.5 down to the unwalled water's edge, and in the core tile down to preserved tidal mud. 23 raised vertices lie beyond 6.16 m from the wall, at most 7.86 m out. Median raise is 0.94 m, maximum 2.87 m.
3. **Wall faces and steps in the river-network mesh** (`clear_wall_faces`). The 1 m mesh triangles straddle the 0.32 m wall. The first version of the fill dragged green "teeth" of ground up the wall's water face; renders showed them clearly. Two limits fix this:
   - Land vertices of triangles that straddle a wall are held down, so no ground stands more than 0.3 m above low water (or above its unfilled height) at the water face.
   - No filled vertex stands more than 2.4 m above a mesh neighbour.
4. **JSON.** New record `retainingEdgeFill` with `crestMethod`, `fillMethod` and an `evidence` string. Mapped: the shoreline and plot edges the interpretive walls follow, and the high-confidence wall_top and embankment_top readings. Estimated: the coping grade, the berm width and batter, and the fill. There is one new `limitations` entry. `inputHashes` gains `river-network.u32`, `river-system-1900.u32` and `factory-buildings.json`.

## Numbers

These come from my sampler, which reproduces the audit's method: 1 m stations, top-most rendered ground at 1, 3 and 6 m beyond the 0.16 m half-width. It matches the audit's before figures (void at 3 m: 871 m against the audit's 866 m; at 6 m: 510 m against 512 m; identical network, system, extension and groundMesh step counts).

Wall length is 2,092.5 m on 32 routes, before and after. Variants A to C were built and measured; only D is committed:

| | Before | A: fill only | B: + face clearing | C: + 2.4 m edge limit | **D: + building exclusion (committed)** |
|---|---|---|---|---|---|
| Within 0.5 m of crest at 1 m and 3 m | 0.0 % | 79.3 % | 61.9 % | 49.6 % | **37.2 %** |
| Within 0.5 m at 1 m only | 0.0 % | 79.5 % | 62.2 % | 49.9 % | **41.8 %** |
| Within 0.5 m at 3 m only | 58.2 % | 84.5 % | 84.3 % | 84.1 % | **73.1 %** |
| Median gap (crest minus ground) at 1 m / 3 m | 1.58 / 0.33 | 0.00 / 0.05 | 0.31 / 0.05 | 0.50 / 0.05 | **0.68 / 0.07** |
| Largest adjacent crest jump | 0.648 (354 over 0.1) | 0.078 | 0.078 | 0.078 | **0.078 (0 over 0.1)** |
| Steps: network | 776 | 3,986 | 1,957 | 776 | **776** |
| Steps: system / extension / groundMesh | 573 / 80 / 3 | same | same | same | **573 / 80 / 3** |
| Steps: core | 422* | 448 → 422 after mud cap | 422 | 422 | **422** |
| Ground at the wall's water face above high water (0.1 m out) | 0 m | 327 m | 0 m | 0 m | **0 m** |

\*My core count is 422, against the audit's 347, because I count both cell diagonals; it is unchanged before and after. With the mud cap, the core has 0 new edges. The step criterion is a rise over 2.5 m across under 3 m on unique mesh edges.

Coverage in D by what stands behind the wall:
- Open ground behind: 679 of 1,187 m (57 %).
- A building within 3 m behind: 44 of 397 m (11 %).
- Walls on core tidal mud: 3 of 350 m (1 %).
- The last 4 m at wall ends: 52 of 159 m (33 %).

In D the "failures" are mostly a narrow gutter within about 1.4 m of the wall (median 0.68 m deep), not the old V-trough (1.58 m deep at 1 m, crest-high ground at 4 to 6 m).

## Why 95 % is out of reach in the permitted files

1. **Channelsea core walls (routes 15, 16, 17, 21; 350 m, 17 % of length) stand on preserved tidal mud.** The 0 to 5 m strip behind them is core "exposed tidal mud", rising from 0.1 to 1.3 m. `check_main_landscape.mjs` requires every mud cell to keep its exact height, and the builder states mud is a channel-bed study. Filling it would need a policy change and a non-count check change. The walls sit about 6 m into the core's own channel section. The real fix is to move these wall routes to the core bank top or drop them, in the river-network build (out of scope).
2. **The 1 m river-network mesh has no vertices on the wall line.** Any triangle straddling the wall interpolates between water-side and land-side heights. Full fill at 1 m (variant A, 79 %) puts ground teeth up the water face and adds 3,210 step edges. Keeping the face clean costs the first row of land vertices (B, C). The proper fix is to insert the wall lines as constraints in the river-network mesh build (`scripts/build_river_network.py` / `river_bank_sections.py`), or the audit's renderer fill wedge in `docs/river-network.js`. Both are out of scope.
3. **About 400 m of wall has a factory building within 3 m behind it.** "Do not raise ground over buildings" leaves the building, not fill, behind the wall there.
4. **Wall ends.** The fill is battered at 1:1.5 to the unwalled shore beyond each end, so the last 2 to 4 m of each wall is not full height. Wall returns, or continuing the fill along the shore, would make earth cliffs.

## Checks

- `python3 scripts/check_main_landscape.py`: PASS (25 source hashes; it was failing at the base on the stale hash).
- `node scripts/check_main_landscape.mjs`: PASS. No count assertions changed in either check.
- `npm test`: 13 of 15, the same as the baseline. In this worktree the two failures are:
  - `check_flood_demo.mjs`: stale `terrain-1900.json` hash, the known failure.
  - `check_drainage_connections.mjs`: fails here because the git-ignored `reference/spot-heights/mosaics/*.json` is absent from the worktree. It failed identically before my change.

## Renders

Renders served from this worktree on port 4175. "Before" renders came from the main checkout on 4173, whose `main-landscape` and `river-network` files I confirmed are byte-identical to the base. The machine was heavily loaded (other agents rendering in parallel). All PNGs are in `scratchpad/t2/`: `views-before/`, `views-after/` (variant A), `views-after-clear/` (B) and `views-committed/` (D).

- **`05-route14-wall-trough`** (−200, 1.8, 424): the camera is inside a building. Before and after both show a brick wall filling the frame, so it shows nothing. I added `wall-r14-water-side` instead. Before: wall clean, a long roofed building directly behind it. Variant A had obvious green teeth up the wall face. Committed: the face is clean except for a few small bumps at the waterline, under 0.3 m above low water.
- **`lea-west-bank-along-900`**: before, the route 12 wall stood as a free slab above lower ground. Committed: the ground behind is filled and only a short end of the wall's water face shows. The problem is gone. In the B and D renders there is a soft dark smear on the regional water at the right. Its nearest changed vertex is 26 m away and it was absent in the A render, so I think it is a lighting or shadow artifact unrelated to this change, but I have not proved that.
- **Author's camera** (−555, 2.5, 760) → (−600, 2, 660): before and after are identical. The camera sits in a hollow facing a grassed bank, and no wall is visible. There is no retaining-wall route within about 150 m of this camera (the nearest is route 12 at about (−631, 920)). So the author's second-screenshot problem is not reproduced here, and T2 cannot affect it. The gasworks pad edge near x −550, z 725 to 790 (T3) is more likely what the author saw.
- **Extra views:**
  - `wall-r4-land-close`, `wall-r4-land-side`, `wall-r31-land-close`, `wall-r7-land-close`: before, the walls stand free above a trough with saw-toothed copings. Committed: the coping sits just above the fill along the wall. On route 7 a visible stepped gutter line (0.3 to 0.8 m) remains where the fill meets the wall. The far-bank walls are filled too.
  - `wall-r1-water-side`, `wall-r4-water-side`: clean, with no teeth. A shows teeth; D does not.
  - `wall-r16-water-side` (core mud route): unchanged.

## Smoke snapshot

`review_smoke.py t2-wall-fill --compare drawn-ground --url=http://127.0.0.1:4175`: ready, 0 page errors, 8,154,223 triangles, 151 draw calls. There is exactly one diagnostic difference: `.mainLandscape.replacements.network.changedVertices` 410085 → 410295. These are the network vertices that the blend left unchanged and the fill now raises; most filled vertices had already been changed by the blend. The screenshot timed out under the software renderer; the script treats this as non-fatal. The script exits 1 whenever there is any difference.

## What I did not do

- I did not move, drop or re-mesh any wall route.
- I did not change the renderer, the tidal-mud policy, pad levels, `level.f32` (object seating is unchanged), the flood inputs (the flood builder still uses the constant 1.65 m `crestHeight`), the river-system canal faces, or anything for T3 to T5.
- I did not commit variants A to C.

## Unsure

- Whether the parent prefers A (79 % fill, water-face teeth, +3,210 step edges), B (62 %, no teeth, +1,181 steps all within 2 m of a wall) or the committed D.
- Raising the berm over pad polygons within the existing 14 m bank band (3,621 raised vertices are inside site polygons). I read "do not raise ground over pads" as not extending fill beyond what the bank band already raises, and not over building footprints. Pad `groundSceneY` values are unchanged.

## Decisions for the parent

1. Accept D, or choose A, B or C. Each is a few constants or lines in the builder; the measured numbers are above.
2. Commission the out-of-scope fix that would meet the target: put the wall lines into the river-network mesh as constraints, or a renderer fill wedge, plus relocating the four Channelsea core walls to the core bank top.
3. `factory-buildings.json` is now a hashed input. Any change to it, including T6, makes `main-landscape` stale until rebuilt. The same is already true of `ground-plan.json` and `river-system-1900.json`, which T1 and T5 are editing.
4. Replace camera `05-route14-wall-trough`, which is inside a building. `wall-r14-water-side` (−232.9, 4.1, 410.5) → (−236.0, 2.6, 429.1) and `wall-r4-land-close` (−782.6, 5.0, −251.4) → (−783.4, 3.4, −233.3) work.
