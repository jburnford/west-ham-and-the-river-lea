# T9 report: Bromley gasworks retort houses, site 924

3 October 2026. Branch `worktree-agent-a2695c36cd2333a97`. Nothing rendered.

## Worktree base

The worktree was created at `116c0ae`, behind `main`. I fast-forwarded it to `main` at `e60757d` (`git merge --ff-only main`, run inside the worktree) before starting. Nothing was written to the main checkout.

While I worked, `main` moved on to `6ab7ef6` (the T3 merge). Those commits touch none of this task's inputs or outputs: `docs/data/factory-buildings.json`, `docs/data/ground-plan.json`, `docs/data/factory-yards.json`, `data/maps/` and the builder are all unchanged. So I did not merge again. All before/after figures below are measured against `e60757d`.

## What changed

- `data/maps/bromley-gasworks-footprint-alignment.json`:
  - `buildings`: two re-registration entries, for `site924-os-13` and `site924-os-14`. The list was empty before.
  - `structures`: 25 position corrections, for the 24 flues and the boiler stack. The list was empty before.
  - `method`: the closing sentence "Retort-house envelopes left for a later pass." now describes this pass.
- `docs/data/factory-buildings.json`, regenerated.
- This report.

I did not touch `scripts/build_factory_buildings.py` or `data/maps/factory-building-traces.json`. The register's existing correction mechanism was enough. It is the same one other sites use for `modelId` re-registration and parent-transferred chimneys.

## Where things are defined (step 1)

- **Retort houses.** `site924-os-13` and `site924-os-14` are legacy `rectPixels` envelopes in `data/maps/factory-building-traces.json`, both with 11 m eaves, 4.2 m rise, 2 bays and roof axis x.
- **Flues.** The 24 flues are also in `factory-building-traces.json` (`stack-924-retort-{1,2}-{-1,1}-{1..6}`), as children placed by `parentBuildingId` and `localPosition`.
- **Boiler stack: the brief and the audit are wrong here.** `stack-924-boiler-photo` is not a child of `os-13` or `os-14`. It is placed by `pixelPosition` on the `os-bromley-production` crop, and it stands inside the eastern utility range `site924-os-15`, which this task does not move.

## Registration offset at site 924 (step 2)

I measured the offset by fitting the outline ink of 20 GeoPackage outlines on the site to the cached NLS five-foot mosaic. These include fids 49 and 46, the L-range, the purifier sheds and vessels, and 4790/24074. The search grid was ±3 m at 0.25 m steps, then refined at 0.05 m.

- **Result:** the GeoPackage outlines sit **1.70 m west and 0.40 m south** of the printed lines (median).
- **Spread:** every outline fell within 1.60–1.80 m W and 0.25–0.45 m S.
- **Comparison:** this is effectively the same as site 865 (1.75 m W, 0.25 m S).

As in the existing Bromley register and in T6, the supplied outlines are used **unshifted**, in the GeoPackage frame.

## What moved, and by how much (steps 2–4)

### Retort-house envelopes

Each new envelope is the GeoPackage outline (one part, no holes), simplified at 0.15 m.

| | `site924-os-13` (fid 49) | `site924-os-14` (fid 46) |
|---|---|---|
| Old envelope | 108 × 70 m, 7,560 m², centre (−376.0, 1125.0), axis 44.00° | 112 × 68 m, 7,616 m², centre (−258.0, 1231.0), axis 44.00° |
| Source outline | 6,327.2 m², centroid (−367.819, 1118.351) | 6,386.7 m², centroid (−245.896, 1239.567) |
| New envelope | 6,338.5 m², centroid (−367.821, 1118.340), axis 44.94°, 94.9 × 67.3 m | 6,391.9 m², centroid (−245.859, 1239.579), axis 44.69°, 95.3 × 67.6 m |
| New vs outline | max deviation (Hausdorff) 0.145 m; area +11 m² (+0.18 %); centroid 0.011 m apart | max deviation 0.140 m; area +5 m² (+0.08 %); centroid 0.039 m apart |
| Move | centre 10.5 m (+8.2 x, −6.7 z); area −1,221 m²; axis +0.94° | centre 14.9 m (+12.1 x, +8.6 z); area −1,224 m²; axis +0.69° |
| IoU of old envelope with new | 0.65 | 0.71 |

- **Heights and roofs are unchanged:** 11 m eaves, 4.2 m rise, two ridges along the long axis.
- **What the OS shows:** each house is one shaded block with no internal walls, no flue squares, no chimney bases and no "Chy." label.
- **EPFL text layer:** no labels on either building. Around them it has only "DOCK", "TRAMWAY", spot heights and "B.M." lines.

### Flues (24)

There is no OS evidence for the flues, so I could not fit them to anything. Each flue keeps its fractional place in its block. Its (along, across) fraction of the old envelope is mapped onto the outline's rectangle (minimum rotated rectangle, on the new axis), and the flue takes the parent's new rotation.

- **Rows:** v = ±25.8 to ±26.0 m, previously ±27 and ±26.
- **Along the block:** u = ±7.4 to ±38.8 m, previously ±8.8 to ±44.
- **Bay step:** 17.6 m becomes 15.5 m (north block) and 15.0 m (south block).
- **Distances moved:** 9.1–13.7 m in the north block and 8.0–21.7 m in the south block.
- **Before the move,** 8 of the 24 flues stood outside their source outline, by up to 11.4 m. **None do now.**

### Boiler stack

The stack was refitted to GeoPackage fid 926100. This is a 3.55 × 3.53 m square drawn open in range outline 24074, where it is a hole: the "small square feature" the original placement cites.

- **Move:** 1.89 m, from (−263.826, 1136.875) to (−265.687, 1137.180).
- **Why it was off:** the old centre sat on the printed square in the mosaic frame, which is the same 1.7 m W / 0.4 m S frame difference measured above.
- **Unchanged:** height (32 m), radius (1.5 m), profile and parent range.
- **Fit to the square:** the 3.6 m round plinth slightly exceeds the 3.5 m square.

### Evidence strings

Every corrected record says what is mapped and what is estimated:
- The `footprintEvidence` of the two houses comes from the register `review`. The old text is kept as `priorFootprintEvidence`.
- The `positionEvidence` of each of the 25 stacks comes from the register `review`. The old text is kept as `priorPositionEvidence` and the old position as `priorPosition`.

## Structural diff of `docs/data/factory-buildings.json`

I produced this with `fbdiff.py` in my scratch folder, comparing against the `e60757d` file.

```
top-level keys unchanged: True
sources.author-os-footprints-1891-96.method: text changed (8057 -> 8453 chars)   <- this register's method string
structures: +0 -0 changed 25; order kept; all site 924
   x, z, priorPosition, positionEvidence, priorPositionEvidence: 25 (24 flues + boiler stack)
   rotation, parentFractions: 24 flues
   sourceFootprintFid, sourcePolygons: stack-924-boiler-photo
footprintAlignment.matchedRanges 627 -> 629
footprintAlignment.parentTransferredChimneys 11 -> 35
footprintAlignment.matchedChimneyBases 32 -> 33
buildings: +0 -0 changed 3; order kept; all site 924
   site924-os-13, -14: footprint, worldFootprint, x, z, rotation, width, depth, localBounds, areaM2,
       renderPolygons, renderAreaM2, footprintEvidence, priorFootprintEvidence, priorFootprint,
       priorRotation, footprintSource, sourceFootprintFid, footprintAlignment
   site924-os-17: renderPolygons, renderAreaM2 only (1,299.14 -> 1,415.32 m2)
counts: unchanged (64 sites, 728 ranges, 89 chimneys)
```

**One record outside the named set changed: `site924-os-17`.** This is the central building with the triangle, already registered on fid 1095. Its source geometry is untouched. Before, the oversized `os-14` envelope overlapped it, and the builder's overlap partition (taller range wins) cut 116 m² from its rendered roof. With `os-14` on its outline, that cut no longer happens. In `geometry-audit.json`, the only difference is that this `renderAdjustments` entry has gone. Water intersections (5), source overlaps (5) and fully covered ranges are all identical.

## Flue and stack relationship to the parent

The builder places a child chimney from the parent's centroid and rotation. The register correction then sets the final centre. The renderer stands every chimney on the ground (`baseHeight` 0.34 m), so "on the roof" means two things: the plan position is inside the parent outline, and the crown is above the roof.

| Measure (24 flues) | Before | After |
|---|---|---|
| Plan offset from parent centre, \|u\| along | 8.80–44.00 m | 7.43–38.75 m |
| Plan offset, \|v\| across | 26.00–27.00 m | 25.83–25.98 m |
| Inside parent footprint and render polygon | 24/24 (of the old envelope) | 24/24 |
| Full square plinth (radius × 1.2) inside parent | 24/24 | 24/24 |
| Distance to the nearest parent wall | 8.00 m | 7.38–7.95 m |
| Inside the *source* outline | 16/24 (8 outside, by up to 11.4 m) | 24/24 (7.37–7.91 m inside) |
| Crown above eaves (11 m) | 7.84–8.64 m | 7.84–8.64 m |
| Crown above ridge (15.2 m) | 3.64–4.44 m | 3.64–4.44 m |
| Crown above the local roof surface | 5.86–6.72 m | 5.86–6.72 m |

- **Boiler stack:** inside `site924-os-15` and its render polygon, with the round plinth fully covered, before and after. Its distance to the nearest wall changed from 14.5 m to 16.0 m. Its crown is 25.4 m above the range's ridge.
- **Stale `localPosition`:** the output rows of the 24 flues still carry their old `localPosition`. The builder computes a position from it, then overwrites that position with the register's `centre`. The effective offsets differ from the stored ones by up to 6.6 m. This matches the 8 existing parent-transferred chimneys elsewhere (for example `west-259-7-stack`), which also keep a stale `localPosition`. See decision 3.

## Check results

- **`python3 scripts/build_factory_buildings.py`** runs with no assertion failures: polygon validity, unique ids, site coverage, holders clear of water and buildings. The rebuild is byte-identical when run again. The baseline rebuild before my edits reproduced the committed file byte for byte.
- **`npm test`: 13/15.** The two failures are the expected ones:
  - `check_flood_demo.mjs`: stale `terrain-1900.json` hash.
  - `check_drainage_connections.mjs`: ENOENT on the git-ignored `reference/spot-heights/mosaics/*`, which the worktree does not have.
  - The two checks that read factory data (`check_district_navigation`, `check_main_landscape`) pass.
- **`scripts/check_factory_buildings.py` (not in `npm test`) fails before and after on the same record, `stack-865-boiler-house`.** That T6 stack has neither `pixelPosition` nor `parentBuildingId`. I ran a scratch copy that skips only that one record. It passes on both baseline and final data, including "crowns above roofs, bases clear of rivers, roads, holders and other shafts" and "no overlapping building volumes".
- **`scripts/check_factory_yards.py` (not in `npm test`) fails before and after.** I ran a scratch copy that reports every blocked yard instead of stopping at the first:
  - Site 865 is blocked by 9,279 m² both times.
  - **Site 924 is blocked by 6,618 m² at baseline and 8,017 m² after.**
  - The cause: `docs/data/factory-yards.json` was generated before the Bromley register existed, so its yard surfaces are drawn around the old envelopes. The re-registered houses and flues now stand on more of that stale yard.
  - Fixing this means rerunning `build_factory_yards.py`, which writes a file outside my permitted list. I did not do it.
- `scripts/check_scene_data.py` and `scripts/check_east_depot_tracks.py` pass.

### Footprint gap audit

I ran a copy of the script with paths patched: it reads the worktree's `docs/data`, reads the footprint source read-only from the main checkout, and writes into my scratch folder. The baseline run gives 7,425 uncovered in started zones, the same as T6's published "after" figure.

| | District, uncovered in started zones | Site 924 uncovered |
|---|---|---|
| Before | 7,425 (211,372 m²) | 225 / 3,022 m² |
| After | 7,429 (211,620 m²) | **229 / 3,270 m²** |

**This acceptance criterion is not met: site 924's figure is 4 footprints and 248 m² worse.** All four are small outlines next to the houses that the old oversized envelopes covered by accident. Under the new envelopes their cover is 0–0.7 %. None is a roofed building on the OS:

- **34850 (178 m²):** the dotted-outline, bottle-shaped overhead coal gantry off the south-west side of the northern house. It is the twin of 37343, which the audit already classes as "overhead coal gantry, not a ground building". The audit report named 459328 as the twin, but the drawn twin at this house is 34850. Before, the old envelope covered it partially (41.9 %).
- **777740 (30 m²):** an unshaded rectangle on the south-east end of the northern house.
- **851236 (21 m²):** an unshaded circle on the same end.
- **860071 (19 m²):** an unshaded circle on the north-west end of the southern house.

The circles could be open tanks or wells; they sit beside small stepped symbols drawn on the walls. Covering any of the four honestly would mean new records, which is outside this task's scope, so I stopped there. See decision 1.

"Model polygons without footprint support" is 123 both times.

## Overlay

- `/tmp/claude-1000/-home-jic823-book-website/158d731a-06ad-4794-89f0-96291b5302cd/scratchpad/t9/t9-retort-overlay.png`: OS mosaic crop.
  - Red: old envelopes, old flue squares and the old stack circle.
  - Blue: new envelopes on fids 49 and 46, new flues and the new stack.
  - Green: the stack base square, fid 926100.
  - Grey lines join each flue's old and new positions.
- `/tmp/claude-1000/-home-jic823-book-website/158d731a-06ad-4794-89f0-96291b5302cd/scratchpad/t9/t9-boiler-detail.png`: an 8× crop of the stack on the printed square and on fid 926100.

The generator, diff and check scripts are in the same folder: `make_t9.py`, `offset_fine.py`, `fbdiff.py`, `check_flues.py`, `gap_audit_copy.py`, `check_yards_copy.py`, `check_fb_copy.py`.

## What I did not do

- I did not re-register `os-15`, `os-16`, `os-4` or `os-9`. These are the audit's other optional legacy envelopes, and they are outside this brief. The boiler stack still stands in the legacy `os-15` envelope, which the audit scored at IoU 0.62 against its own outlines.
- I did not model the gantries (34850, 37343), the unshaded circles and rectangle at the house ends, or the small stepped symbols drawn on the short ends.
- I did not change any height, roof form, flue count, flue height or stack radius. I added no ridge ventilators.
- I did not regenerate `factory-yards.json`, and I rendered nothing.

## What I was unsure of

- **Flue placement rule.** I used proportional transfer, which shrinks the bay step to about 15 m. Two alternatives:
  - keep the 17.6 m step, leaving end flues about 3.5 m from the gable walls;
  - keep the old wall setbacks of 10 m from the ends and 8 m from the long walls.

  All three keep every flue inside the outline. The flue rows are an interpretation of the 1924 aerial in any case.
- **Moving the boiler stack.** It is not a child of the retort houses. I moved it because the brief says to fit the stack to an OS square where one is shown, and fid 926100 is exactly that square. The stack now uses the GeoPackage frame, while its legacy parent range `os-15` does not.
- I could not verify the flue count or positions against any c1900 source. None is in the repository.

## Decisions for the parent

1. **Gap-audit regression at site 924 (+4 footprints, +248 m²).** It is caused by removing false cover, not by a modelling loss. Options:
   - accept it;
   - in a separate task, add the two gantries as elevated structures and the three open features as low structures (structures do not count as cover in the audit, so this would not move the figure);
   - change the audit to count structures as cover (the audit report's question 7).
2. **Stale `factory-yards.json`.** The site 924 yard overlap was already 6,618 m² from the earlier Bromley pass and is now 8,017 m². Rerunning `build_factory_yards.py` needs owner approval, because it is outside this task's files.
3. **Stale `localPosition` on the 24 flues.** Option A: leave it, which matches existing practice. Option B: in a follow-up, rewrite `localPosition` in `factory-building-traces.json` to the new effective offsets so the output is self-consistent.
4. **Boiler stack 1.89 m move.** To revert it, delete its single entry from the register's `structures` list.
5. **Commit attribution.** As the brief instructed, the commit message ends with `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`. The session's own attribution reminder named a different model line.
