# T12c report: road-bridge register re-derived after the T13 retrace

4 October 2026. Branch `worktree-agent-a64e73c3e860d731a`. At the start the worktree was behind main (116c0ae), so I fast-forwarded it to main 493123a, which includes T13. I did not merge main again: the coordinator said main has moved on (T15 railways, landscape rebuild) but none of my files changed there, and they will merge.

Files changed: `data/maps/road-bridge-forms.json`, `docs/road-bridges.js`, `scripts/check_road_bridges.mjs`, and this report. Nothing else.

## Summary

- The five retraced High Street bridges now have new register entries, measured from the drawn water on the T13 spans. The register and the module copy match.
- Each abutment face now follows its own bank. `skew` can be a pair, one value per abutment, and the arch barrel splays between two faces that are not parallel. The deck stays square-ended on the road axis. I did not touch `infrastructure.json`.
- `node scripts/check_road_bridges.mjs` passes again, and so does `check_tram_rails.mjs`. `npm test` passes 15 of 17; the two failures are the known `check_drainage_connections.mjs` and `check_flood_demo.mjs`.
- No assertion was removed. One assertion now encodes a changed rule, explained below. Two assertions were added or extended.
- **Stale before this change, for the record:** main's module clamped the old abutments. That left St Thomas and the Channelsea with *negative* arch spans: no arch was drawn, and both bridges rendered as blank walls over the river. Pegshole drew 2.9 m arches and St Michael's a 4.9 m arch, 5–8 m away from the banks.

## What I re-derived, per bridge

**Method.**

- **Measurement.** I used the same water polygons as the check: tide, reviewed connections, retained rivers, marsh ditches and river system. I sampled them every 0.05 m along each T13 span, every 0.5 m across the 12 m deck. Polygon seams under 0.3 m wide were merged.
- **Bank lines.** I fitted one straight line to each bank's edge points. Only points whose edge lies inside the route were used.
- **Face placement.** Each face was set 0.5 m back from the water onto the bank, which is T12a's practice. The setback is smaller where the face would otherwise come within 0.3 m of a route end at a deck edge; that limit is the new `abutmentEndClearance`.
- **Rounding.** Stations are rounded to 0.05 m and skews to 0.01.
- **New fields.** The register now records `bankEdges`: the start and end edges every metre across the deck.
- **Prior values.** The old values are kept as `priorAbutments`, `priorSkew`, `priorWaterEdges` and `priorEvidence`, with a `priorNote` saying that T13 moved and shortened the spans.
- **Unchanged.** Crown depth, ring depth, pier width and abutment length are unchanged. The crown clearances already met the 0.3 m rule, and nothing in the retrace bears on them.

| Bridge | New abutments (centreline) | Skew west / east (deg from square) | Setback west / east | Notes |
|---|---|---|---|---|
| Bow | 4.35, 30.5 | +0.67 / +0.21 (34° / 12°) | −0.10 (0.1 m into water) / 0.5 | T13 read 34° / 10° on the OS. The west face is held 0.3 m inside the deck end at the right edge |
| Pegshole | 0.5, 15.65 | +0.03 / −0.12 (2° / 7°) | 0.4 / 0.5 | T13 read the east bank at 19° on the OS; the drawn water says 7°, and I followed the drawn water |
| St Thomas | 0.9, 8.25 | −0.01 / −0.06 (1° / 3°) | 0.5 / 0.45 | matches T13 |
| St Michael's | 1.4, 14.15 | −0.17 / −0.14 (10° / 8°) | 0.5 / 0.5 | matches T13 (9° / 8°) |
| Channelsea | 2.55, 13.9 | −0.32 / −0.03 (18° / 2°) | 0.5 / 0.5 | matches T13 (18° / 2°) |

**The other five bridges are unchanged.** I re-measured their water edges at 0.05 m. Every value is within 0.25 m of the register, which is T12a's sampling step. Their routes did not change, so their data is not stale.

**Water beyond the route ends, which no face on the deck can meet.** At some deck corners the drawn water runs on past a route end, under the approach road:

- **Pegshole, right edge** (offsets −4.5 to −6 m): a river-system polygon, 0.4–0.85 m past the west end.
- **St Thomas, left edge** (5.5–6 m): the tide polygon, past both ends.
- **St Michael's, left edge** (5.5–6 m on the west bank, 6 m on the east): the tide polygon.
- **Channelsea, left 3 m of the deck** (3–6 m): the tide polygon, past both ends.

At St Thomas, St Michael's and the Channelsea, the dry gap that the tide polygon leaves for the road ends 2.25–5.5 m left of the centreline, short of the 6 m deck edge. At the Channelsea the previous road lay 3.6–6.3 m to the right, which suggests the gap was cut for the old line. This is the river-network data, which belongs to T14 or the parent. I recorded it in the evidence strings and did not touch it.

## Module changes (`docs/road-bridges.js`)

- **`bridgeLayout`.** It takes `skew` as a number or as a pair, and provides:
  - `face(i, v)`: the station of abutment face `i` at offset `v`;
  - `between(s, v)`: whether a point lies in the opening;
  - `section(v)`: the arches and piers at an offset. Each arch runs face to face with the same springing and crown, so the span varies across the deck;
  - `edgeSpans`: the spans at the two deck edges.
- **Where faces may go (changed rule).** Before, every abutment *body* had to lie under the deck, so the face had to be at least `abutmentLength` (2.5 m) from a route end. That is impossible on the shortened spans. The rule now depends on the form:
  - **Arch forms:** the *face* stays at least `abutmentEndClearance` (0.3 m) inside the route at both deck edges. The masonry behind it may run on under the approach, where the end closure and the approach fill close it.
  - **Deck forms:** the old rule is kept, so those five bridges are unchanged.
- **Drawing.**
  - **Barrel:** drawn in rows across the deck (six rows at Bow), each row an arch from face to face.
  - **Abutment faces:** each follows its own bank.
  - **Pegshole pier:** sits on the line midway between the faces.
  - **Spandrels, ring and wing walls:** use each edge's own section and each face's own skew.
  - **Ring:** its extrados is clamped inside the route.
- **Clear zone (`bridgeClearance`).** It uses the two face lines. It now also stops at the route ends: a strongly skewed face line, carried on past a deck edge, would otherwise reach onto the approach and remove its fill. Main's zone already did this, by 0.2 m at Bow. With the stop, Bow's approach fill is 1.75 m² *more* than on main. Total approach fill is otherwise within 1 m².
- **Interpretation, recorded in each evidence string:** skewed abutment faces following the drawn banks, with an arch that splays between them. This is a common form for oblique crossings, but no source shows these bridges' actual abutments.

## Check changes (`scripts/check_road_bridges.mjs`)

- **"Abutments moved under the deck":** kept. Its comment now states the form-dependent rule above.
- **Added:** each face lies within 1 m of the registered `bankEdges` at every offset whose edge falls inside the route.
- **Extended:** the segmental-rise test now also checks the spans at both deck edges.
- **Landscape report** (printed, not asserted): rewritten to sample the splayed openings.
- **Unchanged:** the road-surface sample (`BEFORE`), the water, parapet and fill assertions.

## Table: before (main 493123a, as drawn) and after

"Face to water" is the largest distance between a face and the drawn water edge, over every metre across the deck where the edge lies inside the route.

| Bridge | Registered → drawn abutments, before | Face to water W / E before (m) | Arch span before (m) | Abutments / skews after | Face to water W / E after (m) | Arch span after: right edge / centre / left edge (m) |
|---|---|---|---|---|---|---|
| Bow | 3, 29.5 → same; skew 0.4 | 2.95 / 1.55 | 26.5 | 4.35, 30.5; 0.67 / 0.21 | **0.47 / 0.59** | 28.91 / 26.15 / 23.39 |
| Pegshole | 8, 27 → **8, 15.55 (moved)** | 7.95 / 1.05 | 2 × 2.88 | 0.5, 15.65; 0.03 / −0.12 | **0.54 / 0.65** | 2 × (7.13 / 6.67 / 6.22) |
| St Thomas | 7, 15.75 → **7, 6.95 (moved)** | 5.65 / 1.20 | **−0.05: no arch** | 0.9, 8.25; −0.01 / −0.06 | **0.50 / 0.46** | 7.65 / 7.35 / 7.05 |
| St Michael's | 8, 20.75 → **8, 12.85 (moved)** | 6.18 / 1.00 | 4.85 | 1.4, 14.15; −0.17 / −0.14 | **0.53 / 0.50** | 12.57 / 12.75 / 12.93 |
| Channelsea | 20.75, 31 → **20.75, 11.9 (moved)** | 17.75 / 2.05 | **−8.85: no arch** | 2.55, 13.9; −0.32 / −0.03 | **0.53 / 0.51** | 9.61 / 11.35 / 13.09 |

On every bridge, before and after:

- **Crown clearance over the static water** is unchanged: Bow 3.84, Pegshole 2.34, St Thomas 1.94, St Michael's 2.04, Channelsea 2.59 m.
- **Lowest soffit over any drawn water in the opening:** 0.44 m after, on all five, where the water reaches the springing at a face. This meets the 0.3 m requirement. Before, it was 0.44 where an arch existed, and there was no opening at St Thomas or the Channelsea.
- **Approach fill:** 0 fill vertices inside the clear zone, before and after.
  - Fill over drawn water within 2 m of the deck occurs only on the route-end planes, in the corner water described above. It is the same before and after: Pegshole 66, St Thomas 42, St Michael's 90, Channelsea 24 vertices.
- **Parapets:** full deck length on both sides (asserted).
- **Five deck bridges:** identical before and after.

## Checks, lint, smoke, renders

- **`npm test`:** 15/17 pass. Failing: `check_drainage_connections.mjs` and `check_flood_demo.mjs`, the known pair. `check_road_bridges.mjs` and `check_tram_rails.mjs` both pass. The full run was repeated on the committed code.
- **Prettier and eslint:** clean on both changed JS files. The register JSON parses.
- **Smoke.** I used a scratch copy of `review_smoke.py` that waits up to 600 s for the tween and writes into my scratch folder.
  - **Base:** `t12c-base`, taken on main at 493123a (port 4173) before main moved on.
  - **After:** `t12c-bridges`, port 4192.
  - **0 page errors.** There are 3 differences, all from the bridge structures: `infrastructure.bridgeStructures.triangles` 7,224 → 8,674, and `triangles` / `reflection.triangles` +1,442. The increase comes from the barrels drawn in rows across the deck, and from the two arches (St Thomas, Channelsea) that had negative spans before and now exist.
  - The script exits 1 whenever any difference exists; these are the intended ones.
  - The PNG screenshot timed out, as it did for the base. The JSON is the comparison.
- **Renders.** Before: main on 4173, at `<scratch>/t12c/before/`. After: worktree on 4192, final code, at `<scratch>/t12c/after2/`. I looked at each PNG.
  - **Note on an earlier pass.** An earlier after pass (`after/`) may have loaded the code before the clear-zone route-end stop. It is pixel-identical to `after2` except for a 13 × 50 px strip in the Bow overhead, at the deck-end corner, where the approach fill is now kept.
  - **`bridge-bow-bridge-span`: modest improvement.** The arch now springs further along the road at the near (west) side, following the skewed bank. The wing-wall coping line moved accordingly. The near bank still hides the springing, as T12a reported.
  - **Bow overhead (−1000, 70, 60): small change.**
    - Before: a pale wedge at the south-east deck corner over the approach. This is the wing-wall coping showing through the low approach, probably one of the "white wedges".
    - After: smaller, with a dark fill strip at the deck end.
    - From 70 m the arch is not visible.
  - **Author's Bow view (−940, 55, 150): improved, small at this distance.** The west abutment and wing now sit on the oblique bank, and the arch opening is offset accordingly.
  - **Channelsea overhead: little visible change** from 60 m (781 px changed). The parapets and deck are unchanged.
    - The deck-corner wing walls are now at the skewed faces.
    - The exposed deck-end faces are visible as pale strips at both ends; that is the step described below.
  - **`pegshole-from-river` (derived camera on the river 18 m left of the span, looking at its centre): improved.** Before: two narrow 2.9 m arches set inboard, with a long solid wall and a wing wall cutting across. After: two 6.2–7.1 m segmental arches filling the channel, the pier and cutwater on the channel line, and the wing walls at the banks.
  - **Added views.**
    - **`x-st-thomas-…` and `x-channelsea-…` (from the river): fixed.** Both were blank walls before (negative spans). Now there is a brick arch at St Thomas and a 9.6–13.1 m splayed stone arch at the Channelsea, both over the water.
    - **`x-st-michaels-…`: fixed.** It shows a 12.75 m arch spanning the channel; before, a 4.85 m arch.
    - **`x-pegshole-…-river-right` and `x-bow-from-river`:** arches bank to bank. The Bow arch is visibly asymmetric because of the splay.

## For the `infrastructure.js` owner: deck-end steps and wedges, per bridge

These were measured on the `infrastructure()` scene built as the check builds it. They are the same before and after T12c: none of this geometry is mine.

**Road-to-deck step:** deck top (h + 0.02) minus the drawn approach road, at 0.25 m / 1 m off the deck end.

| Bridge, end | Centre | Right carriageway (−4.4 m) | Left carriageway (+4.4 m) |
|---|---|---|---|
| Bow W | 0.30 / 0.41 | 0.55 / 0.57 | 0.55 / 0.57 |
| Bow E | 0.29 / 0.38 | 0.55 / 0.57 | 0.55 / 0.57 |
| Pegshole W | 0.28 / 0.35 | 0.55 / 0.57 | 0.55 / 0.56 |
| Pegshole E | 0.29 / 0.40 | 0.55 / 0.57 | 0.55 / 0.58 |
| St Thomas W | 0.26 / 0.27 | 0.55 / 0.57 | 0.55 / 0.57 |
| St Thomas E | 0.26 / 0.28 | 0.48 / 0.28 | 0.55 / 0.57 |
| St Michael's W | 0.26 / 0.27 | 0.51 / 0.39 | 0.55 / 0.57 |
| St Michael's E | 0.28 / 0.34 | 0.55 / 0.57 | 0.55 / 0.57 |
| Channelsea W | 0.29 / 0.39 | 0.55 / 0.57 | 0.55 / 0.57 |
| Channelsea E | 0.29 / 0.39 | 0.55 / 0.57 | 0.55 / 0.57 |

- **The deck is level, but the approach is cambered.** 0.05 m off each end, the exposed vertical end face is a wedge: 0.26–0.27 m high at the centre and 0.68–0.74 m at the carriageway edges, with an area of 4.7–5.45 m² per end.
  - That face is the stone end closure or the abutment back drawn by `road-bridges.js`, so it reads pale.
  - These, or the wing-wall copings below, are probably the "white wedges at the deck corners"; see "What I was unsure of".
- **Footway step: 0.80–0.91 m** from the deck footway box top (h + 0.145) down to the approach footway at 6.6 m.
  - The approach footway (6.1–7.1 m from the centreline) does not line up with the deck footway box (4.5–5.7 m). It ends against the parapet end pier, and beside the deck there is nothing at 6–7.1 m.
- **One real hole:** at Pegshole east end, left side, there is no footway surface for 0–3 m off the deck at 5.95–7.05 m (3.3 m²). No other approach or deck gap is larger than 0.01 m².
- **Wing walls show through the approach footway.** Their copings stand up to 0.53–0.60 m above it, within about 0.4 m past the deck-end corners: Bow 18, Pegshole 15, St Thomas 33, St Michael's 18, Channelsea 21 vertices.
  - On main this was Bow 15, Channelsea 66 vertices at up to 1.11 m, and 0 at Pegshole, St Thomas and St Michael's, whose wing walls then stood well inside the deck.
  - The cause is the step: the approach is 0.55–0.75 m below the deck at the kerb. Raising the approach to the deck would bury them.
- **Suggested fix, not done.** In `ground()`, let the bridge cone (`bridge.height − 0.065 − 0.12·d`) win over `roadProfileHeight` within a few metres of each deck end, and blend the camber out to flat at the deck end. Alternatively, fix the road `elevationProfile`s at the source (`build_infrastructure.py`). Either change moves the road surface and the tram rails, so `check_road_bridges.mjs` (stored `BEFORE` sample) and `check_tram_rails.mjs` must be refreshed in the same change.

## What I did NOT do

- I did not edit `infrastructure.json`, `infrastructure.js`, the river network, the landscape or `app.js`. No span was moved, and no deck height, width, arch count or style was changed.
- I did not fix the deck-end step, the end-face wedges, the footway misalignment or the Pegshole footway hole (all `infrastructure.js` or builder matters).
- I did not change the five deck bridges.
- I did not run `npm run manifest`, and I did not merge main again.

## What I was unsure of

- **Faces follow the drawn water, not the OS.** At Pegshole the drawn east bank is 7° from square against T13's 19° OS reading, so the face could be up to about 1.3 m off the printed bank at the deck edges ((tan 19° − tan 7°) × 6 m). If the water polygon is corrected, re-derive.
- **The splayed arch is my interpretation.** At Bow the span varies 23.4–28.9 m across the deck under one crown. A real 1839 bridge over a 34°/12° crossing may instead have had a skew arch with parallel faces and the difference taken in the wing walls. No source in the repository settles this.
- **Bow's west face** is 0.1 m into the water at the centreline, so that it stays 0.3 m inside the deck end at the right edge. The drawn bank curves there (0.75–0.8 m at offsets −5 to −6).
- **The "white wedges":** there are two candidates, and both come from the deck-end step. One is the cambered end-face wedge; the other is the wing-wall copings showing through the low approach (the Bow overhead crop shows the second). I did not prove which one T13 and T10 saw.
- **Water owned by T14.** The water polygons used here are main's at 493123a. T14 is editing the river network now, so a merged T14 could move the drawn edges. The new assertion compares faces with the *registered* `bankEdges`, not with live water, so it will not break on a T14 merge, but the register could then be stale again.

## Decisions for the parent

1. **Keep or change the splayed-arch interpretation.** The alternative is parallel faces with one skew, where up to about 3 m of the Bow west bank would be taken by the wing walls.
2. **Water polygons at the deck corners.** Ask T14 (or the river-network owner) to move the tide-polygon road gap onto the T13 road at St Thomas, St Michael's and the Channelsea, and to check the river-system polygon at the Pegshole west corner. Then re-run the edge measurement; the scripts are in my scratch `t12c/` (`measure.mjs`, `derive.py`, `update_register.py`, `embed.py`).
3. **Pegshole east bank: 19° (OS) or 7° (drawn water).** If the OS reading is right, the water polygon is wrong there.
4. **Deck-end step.** Route the step, the wedge and the footway findings above to the `infrastructure.js` and road-profile owner, as one coordinated change with the two stored check samples.
5. **Possible check:** live drawn water against the registered `bankEdges`. I did not add it; it would catch staleness after river-network edits, at the cost of failing on any such edit until the register is re-derived.
