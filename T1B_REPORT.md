# T1b report: the sewer road openings

Branch `worktree-agent-aea507263de6c6553`. The branch started at 116c0ae, behind `main` and without T1. I fast-forwarded it to `main` 2341c97 (which includes T1, c4aca8c) before starting. All the work below sits on top of 2341c97.

## What changed and why

The infrastructure builder cut the banks at four streets, not two:

| street | where | what it does at the sewer |
|---|---|---|
| Abbey Lane | chainage 1224, x ≈ −197 | passes under the sewer, 42° skew |
| Mill Meads works road | chainage 1574, x ≈ 116 | passes under the sewer, 30° skew |
| Godfrey Street | x ≈ −534, z ≈ −322 | ends at the bank toe; bank up to 2.3 m there |
| Ross Road | x ≈ −431, z ≈ −253 | ends at the bank toe; bank up to 1.0 m there |

Stratford High Street is the fifth cut and is left exactly as before. The Mill Mead riverbank path is a `path`, so it was never cut, and it still is not.

1. **`scripts/build_panorama_data.py`**
   - New `sewer_road_openings()` reads the street routes and widths from `docs/data/infrastructure.json` (`roads`), skipping paths and the High Street. The road list there is assembled from five trace files plus the station and Manor Road modules, so reading the built list is the only way to match it without copying that assembly. It is the same kind of file-order dependency as T1's `drawn_water()`, and there is no value cycle: street routes and widths do not depend on the sewer.
   - The street corridors, buffered 1.5 m (`SEWER_ROAD_SETBACK`, the same as the old `roads.buffer(1.5)`), become a third bank obstacle, `road`. This means the cut is made here, with T1's densified ends (a vertex every 2 m and at the crest edge). The bank therefore keeps its full profile up to the end wall. If the infrastructure builder had kept making the cut, the bank edge would sag between 12 m lattice points while the wall top followed the exact profile. That is why `banks` had to change.
   - `sewer_bank_ends()` then emits `road` runs. The new `annotate_road_ends()` adds `road` (the street name) and `roadWidth` to each run. Where the street passes under the deck it also adds `roadAxis`: the street centreline chord from crest edge to crest edge.
   - The allotment garden is still clipped against the bank without the road cuts (`garden_bank`), so the garden beds do not move.
   - `bankEndsEvidence` now covers road ends and the arch: positions follow the mapped streets; the arch form, rise and springing are interpreted.
2. **`scripts/build_infrastructure.py`**: the sewer bank cut now skips streets that the ground plan has already cut and named in `bankEnds`. In practice only Stratford High Street is still cut here, exactly as before. Two lines changed (`road_names`, `precut`) and one comment was updated.
3. **`docs/sewer-crossing.js`**
   - `bankEndWalls()` is unchanged in behaviour. It already walls any run, so the 6 road runs get brick end and wing walls with no special code. Its winding helper moved into a shared `faceSink()`.
   - New `sewerRoadArches()` draws one brick skew arch per `roadAxis` opening, as one mesh named `sewer-road-arch`:
     - It springs from the front faces of the two end walls. The span is measured from the wall runs (8.40 m at Abbey Lane, 7.43 m at Mill Meads).
     - The portals lie along the deck edges, parallel to the sewer. The spandrel top is hidden inside the 0.48 m deck slab.
     - The arch is segmental: the crown is 0.75 m below the slab underside and the springing is 3 m above the highest road sample (rise capped at a semicircle, minimum 0.8 m). An arch ring stands 0.1 m proud on each portal.
     - All of these numbers are in `roadArchAssumptions`, with an "interpretation, not a documented structure" comment.
   - The report now includes `roadArches: {count, arches: [{road, span, rise, crownClearance, edgeClearance, skewDegrees}]}`.
4. **`docs/data/ground-plan.json`** and **`docs/data/infrastructure.json`** are patched in place (below). The check scripts are not changed.

Patch procedure (scratch scripts, not in the repo):
- Run `build_panorama_data.py`, keep its output, restore the committed file, and copy across only `banks`, `bankEnds` and `bankEndsEvidence`.
- Run `build_infrastructure.py` against the patched plan. Its full output differs from the committed file only in `sewerBanks`, so I kept that rebuild as-is.
- The infrastructure build needs the git-ignored mosaics `m18_131075_87146.{json,png}`. I symlinked them from the main checkout and removed the links afterwards.

## Structural diff (Python, path-level, against HEAD 2341c97)

```
ground-plan.json
  /neighbourhood/sewer/bankEnds          list 10 -> 16
  /neighbourhood/sewer/bankEndsEvidence  text extended (road ends, arch)
  /neighbourhood/sewer/banks             list 2430 -> 2621
  3 differing paths
infrastructure.json
  /sewerBanks                            list 2893 -> 2651
  1 differing path
```

- **bankEnds:** the 10 T1 runs (8 water, 2 railway) are byte-identical. There are 6 new `road` runs: Godfrey Street ×1, Ross Road ×1, Abbey Lane ×2 and Mill Meads works road ×2. The last four carry `roadAxis`.
- **Full rebuild:** a full `build_panorama_data.py` rebuild also differs in `/neighbourhood/terraces` (99 → 98). That is the known drift and it is not carried over. Garden beds are unchanged.
- **banks:** 117 triangles removed and 308 added, all near the four streets. The Godfrey Street cut re-triangulates some bank 28–40 m from the High Street centre, but no changed triangle touches the High Street opening. The 45 `sewerBanks` triangles within 3 m of the High Street opening are identical to before.
- **Bank left over a street corridor:** 0.000 m² for all four streets.
- **Unchanged:** `sewerCrestTriangles`, `sewerRailEdges`, `sewerHighStreet`, the roads and the railways.

## Checks

| | base 2341c97 (per T1) | after |
|---|---|---|
| `npm test` | 13/15 | 13/15 |
| `check_sewer_crossing.mjs` | PASS | PASS (no assertion edits) |
| `check_sewer_high_street.mjs` | PASS | PASS (no assertion edits) |
| `check_drainage_connections.mjs` | FAIL | FAIL. Without reference files it stops on the missing git-ignored mosaic. With the mosaic linked, it fails on stale `infrastructure.json` (known, already stale after T1). |
| `check_flood_demo.mjs` | FAIL (stale `terrain-1900.json`) | FAIL (same) |

- `prettier --check` and `eslint` are clean on `docs/sewer-crossing.js`.
- Python checks pass: continuous_structures, manor_road, core_river_connections, gardens (153 plots, unchanged), great_eastern ("sewer headroom >3 m"), north_london_connection, river_banks, scene_data.
- Python checks that fail as at base:
  - main_landscape: stale ground-plan hash.
  - landscape_flood: stale infrastructure hash.
  - regional_marsh, river_system, regional_landscape, lower_lea_region: missing git-ignored reference files.

## Render verdicts

- **Setup:** before = a `git archive` of HEAD `docs/`; after = this worktree's `docs/`. Both were served on port 4178 with the same cameras. No page errors.
- **Where the files are:** cameras in scratch `cameras-t1b.json`; images in scratch `views-before/` and `views-t1b-after/`, under `/tmp/claude-1000/-home-jic823-book-website/158d731a-06ad-4794-89f0-96291b5302cd/scratchpad/`.

| camera | verdict |
|---|---|
| `sewer-toe-6s` | **Fixed.** Before: smooth sliced wedge, with the gasholder seen straight through under the deck. After: a brick wing wall closes the bank end and steps down to the toe. The skew arch portal with its proud ring carries the deck over Abbey Lane; daylight only through the arch. |
| `sewer-toe-6n` | Unchanged. The Abbey Lane opening is out of frame (right of view); continuous bank and deck. |
| `sewer-toe-8s` | **Fixed** (left edge). Before: the bank wedge with sky under the deck. After: a coped wall end and the arch portal. |
| `sewer-toe-8n` | Uninformative: the camera stands against a building wall, and before and after look identical. |
| `t1b-abbey-lane-west` (on the lane, west side) | **Fixed.** Before: two wedges and open sky under the deck. After: wing walls both sides lead into a skew segmental arch; the road runs through it with clear headroom. |
| `t1b-abbey-lane-east` | **Fixed**, same reading from the east. |
| `t1b-mill-meads-road-north` | **Fixed.** Before: two bank wedges and open sky under the deck. After: wing walls and an arch over the setts. |
| `t1b-mill-meads-road-south` | **Fixed.** The skewed portal reads correctly. The street surface south of the bank is half-buried under green ground in both before and after. That is a ground or road issue outside this task. |
| `t1b-godfrey-street` | **Fixed.** A low coped brick retaining wall now closes the street end at the bank toe, where before the bank ended in a sliced edge. |
| `t1b-ross-road` | **Fixed**, the same low wall at the street end. |

## Smoke

`review_smoke.py t1b-road-openings --compare drawn-ground --url=http://127.0.0.1:4178`, run from a scratch copy that waits 900 s for `tweening` (the stock 60 s wait times out) and writes to the worktree's git-ignored `scenes/channelsea-sewer-panorama/review/`. The screenshot step timed out (environment); the JSON is complete.

- **Base files (`t1b-base`) vs drawn-ground:** 0 page errors and 5 differences. These are exactly T1's 5 already-merged differences: triangles, reflection triangles, abutment min and max, and `endWalls`.
- **T1b vs drawn-ground:** 0 page errors and 6 differences:
  - `triangles` 8,154,223 → 8,159,419 and `reflection.triangles` 8,158,721 → 8,163,917. Against base that is +1,866 in each pass: 1,260 road end-wall triangles + 848 arch triangles − 242 bank triangles.
  - `sewerCrossing.bounds.abutment.min/max`: T1's change, identical to base.
  - `sewerCrossing.endWalls`: `{count: 16, kinds: [railway, road, water]}`, compared with 10 / [railway, water] at base.
  - `sewerCrossing.roadArches`: new. It reports the in-browser terrain clearances: Abbey Lane span 8.40 m, rise 3.16 m, crown 6.16 m and road-edge 4.41 m above the road, skew 42.2°; Mill Meads works road span 7.43 m, rise 3.51 m, crown 6.51 m, edge 4.71 m, skew 29.7°.
- Draw calls are unchanged at 151.

## What I did NOT do

- I did not touch the High Street crossing, its spec, or its bank cut.
- I did not cut the embankment for the Mill Mead riverbank path (T1's open question).
- I did not change the deck, crest, parapet rails or `app.js`. The rails still run straight over the arches.
- I did not add new assertions to the check scripts. The arch is verified by a scratch raycast probe (a clear road at 1, 3 and 4.5 m; the arch overhead; walls 8.4 m apart) and by the smoke values.
- I did not update any stale `inputHashes`. `infrastructure.json` and `ground-plan.json` are stale in the derived files, as they already were after T1.
- I did not fix the half-buried Mill Meads works road surface south of the sewer.

## What I was unsure of

- **Arch form.** It is wholly interpretation: segmental brick skew arch, 3 m springing above the road, a single ring proud of the face. I have not seen a source for the NOS structure at Abbey Lane or the Mill Meads works road. Real crossings may be iron girders on brick abutments, or a square-ended arch with a skewed face.
- **Wing walls.** They run the full 44 m width of the embankment, along the street at the 1.5 m setback, descending with the bank. A real structure might have shorter, splayed wing walls and the bank slope returning around them.
- **Godfrey Street and Ross Road.** These streets only reach the toe. I gave them the same retaining wall because the brief says every cut road. A gentle slope or the street simply ending at the bank would be equally plausible.
- **Road level.** The road level is the maximum of nine `level()` samples across the road under the deck. The road surface is drawn 0.065 m above terrain, so reported clearances are about 0.07 m high.

## Decisions for the parent

1. Accept the road keys inside `bankEnds` entries (`road`, `roadWidth`, `roadAxis`) and the extended `bankEndsEvidence`. `sewer-crossing.js` only receives `neighbourhood.sewer`, so the arch geometry has to travel there.
2. Accept that `banks` changed: the cut moved from the infrastructure builder into the panorama builder so the bank keeps its profile to the wall.
3. Accept the new file-order dependency: `build_panorama_data.py` reads `infrastructure.json` roads. Rerun it after street traces change, then rerun `build_infrastructure.py`.
4. Whether Godfrey Street and Ross Road should keep their toe walls.
5. Whether to add a regression assertion for the arches (count 2, edge clearance > 3.5 m) in `check_sewer_crossing.mjs`.
6. When to rebuild the derived files whose `inputHashes` point at the older `ground-plan.json` / `infrastructure.json`.
