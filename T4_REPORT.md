# T4 report: shore-edge lip rule and junction end caps

3 October 2026. Worktree branch `worktree-agent-a816f4b4815dc8caf`.

## Bottom line

- **Hackney Cut / Old Lea cliffs are gone.** The lip rule now applies only near recorded masonry. All 367 river-system steps that the rule made, and all 74 river-network ones, are gone or back to their base state.
- **Fins over river-system water are gone.** Above-water surface inside system water went from 8.36 m² to 0.00 m². Network triangles standing above water at their centroid went from 22 to 0. The highest vertex of any triangle over system water went from 1.74 m to 0.13 m above water.
- **Old Lea junction.** Four of the five fins in camera `09` are gone. One remains, and it has a different cause (see "Not fixed").
- **No mesh gained a step.** T2's wall-fill coverage is unchanged at 37.19 %. All checks pass at the base count (13 of 15).
- **Only one file changed by hand:** `scripts/build_main_landscape.py`, plus the regenerated landscape outputs. The river-network build and its outputs are untouched.

## Base state (before my change)

- My branch started at 116c0ae, behind `main`. It had no local changes, so I fast-forwarded it to `main` (feaa7aa) before starting.
- At base, `check_main_landscape.py` failed on stale input hashes for four files: `ground-plan.json`, `infrastructure.json`, `river-system-1900.json` and `factory-buildings.json`. `check_main_landscape.mjs` passed. `npm test` passed 13 of 15.
- Re-running the unchanged builder gave byte-identical `.f32` files. Only those four hashes changed in the JSON, so T1, T1b, T5 and T6 had no geometric effect on the landscape. "Before" below means the committed geometry.

## What I changed

`scripts/build_main_landscape.py`:

1. **Lip rule** (in `blend_surface`). The old rule set `rise = 1` wherever a bank vertex was within 0.6 m of the regional shoreline and had stood more than 0.5 m above water. Such a vertex now keeps a raised edge only on a recorded raised shore:
   - **Within 1.5 m of recorded masonry:** lifted to the crest as before. Masonry means the river-system `canalFacingRoutes` (Limehouse Cut brick faces, whose copings follow the crest) and the river-network `retainingEdges`. This applied to 526 system vertices and 2 network vertices.
   - **Inside a reviewed river-system terrain patch whose recorded shore transition is 0.6 m or less:** held at its previous reviewed height, but never above the crest. This applied to 686 system vertices in `waterworks-east-margin`, `waterworks-upper-bank` and `potters-ditch-low-ground`, which have a recorded 0–0.3 m shore transition. Without this, the reviewed Waterworks bank face would be lowered unevenly: to 1.0–2.95 m depending on the marsh weight, against a uniform 3.2 m before.
   - **Everywhere else:** the builder's existing 0–3 m smoothstep earth face. This covers earth and canal-earth banks; the bank policy says "no continuous masonry assumed on Hackney Cut".
2. **Junction end caps** (new `cap_junction_ends`, river-network mesh only). A network vertex within 3 m of drawn river-system water (`waterPolygons`) is capped. The cap starts at the water edge (low water + 0.02 m) and rises by smoothstep to the vertex's existing height 3 m from that water. This is the same face the system's own banks have.
   - Recorded raised shores (as above) are excluded.
   - No vertex is lowered more than 2.4 m below a mesh neighbour, so the cap cannot create a step. A first version without this limit made 2 new network steps.
   - Result: 1,254 vertices lowered, at most 1.47 m, all at network/system junctions. The main clusters are Bow Locks / Limehouse Cut head, Bow Creek, the Old Lea / City Mill junction, the network step at (−1100, −700), the sewer at (−1157, −532), (−1400, −350), (−1035, 84) and (−245, −944).
   - I clamped heights rather than dropping triangles. Dropping them would change `river-network.u32`, and every consumer stores that file's hash. It would also leave holes, because the system mesh does not extend under network triangles.
3. **JSON.** Two new records, each with method and evidence strings that separate mapped from estimated:
   - `shoreLip`: method, per-mesh `lipVertices` counts, `steepShorePatches`, evidence.
   - `junctionEndCaps`: method, `loweredVertices` 1254, `maxLoweringMetres` 1.47, evidence.

Regenerated outputs:
- `main-landscape-1900.json`
- `main-landscape-1900.network.f32`: 1,273 vertices lowered, none raised.
- `main-landscape-1900.system.f32`: 1,538 vertices lowered (median 1.21 m, at most 3.21 m), none raised.

`core`, `extension`, `background`, `faces`, `level` and `weight` are byte-identical to base. The 85 core vertices that met the lip condition are all preserved tidal mud, so nothing changed there. No check script was changed.

## Numbers

**Steps** use the audit's rule: a rise over 2.5 m across under 3 m, on unique edges. They come from T2's `measure_walls.py`, copied to my scratch folder.

| Mesh | Before | After | Note |
|---|---|---|---|
| network | 776 | **702** | The 74 lip-rule edges are gone. The 702 left are all Bromley Gas Works / St Leonard's pad edges (T3), untouched. |
| system | 573 | **214** | 0 new step edges. 206 are pre-existing raw-mesh edges at `waterworks-upper-bank`, the same before and after. 8 are lip edges in that patch, unchanged from base. |
| core | 422 | 422 | |
| extension | 80 | 80 | |
| groundMesh | 3 | 3 | |

Breakdown of the 367 system steps the builder made, by location:

| Location | Before | After |
|---|---|---|
| `old-lea-east-bank-margin` (camera 08, the audit's "Hackney Cut") | 162 | 0 |
| `city-mill-bank-and-ground` | 97 | 0 |
| `potters-ditch-low-ground` | 57 | 0 |
| `temple-mills-bank-path` | 28 | 0 |
| `waterworks-upper-bank` | 23 | 8 (unchanged) |

**Fins.** Network triangles whose centroid lies inside the current river-system `waterPolygons`:

| | Before | After |
|---|---|---|
| Triangles with any vertex more than 0.05 m above water | 234 | 20 |
| Highest vertex above water | 1.74 m | **0.13 m** |
| Triangles standing above water at the centroid | 22 | **0** |
| Sampled above-water area inside system water | 8.36 m² | **0.00 m²** |
| Vertices *inside* system water above water | 0 | 0 |

- At base, every vertex inside system water was already at or below −0.76 m because of the system's `coreBedCorrections`. Every "fin" was a straddler: a triangle whose raised vertex stands just outside the polygon. The 20 left after the change are 1 m triangles whose outside vertex is at most 0.19 m high.
- **Audit definition.** T5 trimmed the system water polygons away from network water, so the audit's 3.38 m fins at (−1052, −623) now lie inside network tide water. Against the pre-T5 polygons:
  - highest vertex: 3.38 → 2.25 m;
  - triangles above water at the centroid: 94 → 22;
  - above-water area: 26.9 → 8.6 m².
- The one remaining 2.25 m triangle is not an end cap (see "Not fixed").

**T2 wall fill** (`measure_walls.py`):

| | Before | After |
|---|---|---|
| Within 0.5 m of crest at both 1 m and 3 m behind the wall | 37.19 % | **37.19 %** |
| At 1 m only | 41.76 % | 41.76 % |
| At 3 m only | 73.08 % | 73.03 % (about 1 m of wall, where an end cap lowered fill beside system water) |

## Checks

- `python3 scripts/check_main_landscape.py`: PASS (25 source hashes). It failed at base on stale hashes.
- `node scripts/check_main_landscape.mjs`: PASS.
- `npm test`: 13 of 15, the same as base. The two failures are the known ones:
  - `check_flood_demo.mjs`: stale `terrain-1900.json` hash.
  - `check_drainage_connections.mjs`: the git-ignored `reference/spot-heights/mosaics/*.json` is missing from the worktree.
- No other derived file stores a hash of the main-landscape files. `export_terrain_geotiff.py` reads them, and I did not re-export.

## Renders

- Served from this worktree on port 4181. For "before" I copied the base landscape files into `docs/data` temporarily, rendered, then restored the final files. Both runs use otherwise identical docs.
- PNGs are in `scratchpad/t4/views-before/` and `views-after/`. Changed-pixel share is in brackets.

Verdict per camera:

- **`08-hackney-cut-lip-cliff`** (23 % changed). **Fixed.** Before: a vertical 3 m earth wall rising straight out of the water along the whole bank. After: a rounded earth bank with a low pale strip at the waterline. That strip is the smoothstep toe, which takes the low-ground sediment colour. Straight seams across it at panel joins are visible but minor. `x-hackney-cut-overview` (6 %) confirms this along the reach and on both banks.
- **`09-old-lea-junction-fin`** (16 %). **Mostly fixed.** Before: five tall triangular wedges standing in the water. After: four are gone and the bank is a continuous slope. One dark pyramid remains at the left beside the brick pier (see "Not fixed").
- **`connection-bow-locks`** (0 %). Identical. The end caps lowered there are out of frame or too small to change any pixel. Nothing new is broken.
- **`connection-three-mills`** (0 %). Identical. The audit found no overlap here, and none was changed.
- **`network-steps-1100-700`** (0 %). Identical, and the view shows clean earth banks either way.
- **Author's camera** (−612, 2.5, 872) → (−582, 0.5, 846) (0 %). **Not fixed.** The jagged, saw-toothed bank edge against the water is still there. Those vertices are 14–20 m from system water, inside the network's own tide polygon, and not lip vertices. This is the audit's I9 (network bank faces drawn on the 1 m grid), not the lip rule or an end cap.
- `x-waterworks-upper-bank` (0.01 %). Unchanged, as intended.

## Smoke snapshot

- `review_smoke.py t4-lip-rule --compare drawn-ground --url=http://127.0.0.1:4181` was run from a scratch copy with a 900 s tween wait (`scratchpad/t4/review_smoke_t4.py`). Result: ready, **0 page errors**, 8,167,680 triangles, 150 draw calls. The screenshot timed out, which the script treats as non-fatal.
- There are 19 differences against `drawn-ground`. That snapshot predates T1 to T6, so I also took a base snapshot (`smoke-t4-base`) from this worktree before my change.
- **Base against after: exactly 2 differences, both from T4:**
  - `.mainLandscape.replacements.network.changedVertices` 410295 → 410401: vertices the blend had left at their old height that the end caps now lower.
  - `.mainLandscape.replacements.system.changedVertices` 398533 → 398221: lip vertices now held at their previous reviewed height count as unchanged.
- The other 17 `drawn-ground` differences are identical in the base snapshot, so they come from earlier merged work:
  - `factoryBuildings.*`, site 865, and `triangles` / `reflection.triangles`: T6.
  - `sewerCrossing.*` end walls, road arches and abutment bounds: T1b.
  - `drawCalls` / `reflection.drawCalls` 151 → 150: T5's shared water material.
  - `network.changedVertices` 410085 → 410295: T2.
  - `destinationCount` 128 → 129: present at base. I did not trace which earlier commit caused it.
- Snapshots are in `scenes/channelsea-sewer-panorama/review/` (git-ignored) in this worktree.

## Not fixed (outside the lip rule and end caps)

1. **The remaining Old Lea fin.** Vertex (−1051, −618) is raised from 0.62 to 2.31 m. It stands inside the network tide polygon, 1.1 m beyond the start of retaining-wall route 2 and 9.3 m from system water. It is raised by the generic bank blend: the builder's "water" union does not include network tide polygons, so it treats the vertex as dry bank 0.6–3 m from the regional shoreline. It is neither a lip vertex nor fill. Fixing it means deciding how the regional bank band treats ground inside network tide polygons, which affects many network bank faces.
2. **Saw-toothed network bank edges** (author's camera, I9). These have the same root cause as item 1.
3. **Pre-existing raw-mesh steps.** The 206 at `waterworks-upper-bank` belong to the reviewed patch's recorded 0.3 m shore transition and are left as they are.
4. **Not done:** I did not touch the river-network or river-system builds, the renderer, the GeoTIFF export, the flood inputs, or T3's pad edges.

## Unsure

- **Whether to exempt the steep-shore patches.** Treating all non-masonry shores as earth would bring system steps to 24 (all pre-existing). But it lowers the reviewed Waterworks bank unevenly, so I kept the exemption.
- **The two thresholds.** The 1.5 m masonry reach and the 3 m end-cap reach are judgement calls. They match the audit's 1.5 m test and the builder's 3 m face.

## Decisions for the parent

1. Accept the steep-patch exemption, or drop it (system steps 214 → 24, uneven Waterworks bank).
2. Commission a follow-up for network ground inside network tide polygons that the regional bank band lifts. That would cover the last Old Lea fin and the saw-toothed bank at the author's camera.
3. The GeoTIFF/GeoPackage export reads the main-landscape files and is now stale, like the rest of the rebuild cascade.
