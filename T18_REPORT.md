# T18 report: bridge deck ends, Marshgate Lane, Three Mills dwelling

4 October 2026. Branch `worktree-agent-a8468f47e4226f36e`, on top of main `d9980e9` (main has not moved since). Scratch work, measurement scripts, overlays and renders are in `/tmp/claude-1000/-home-jic823-book-website/61f71781-342b-470a-9012-cb46325e06a9/scratchpad/t18/` (called `t18/` below).

Commits, in order:

| Commit | What |
|---|---|
| `78c7588` | Part 1: deck ends flush; deck-end footways; bridge-check sample refreshed |
| `097d76e` | Part 2: Marshgate Lane retraced; connection deck moved with it |
| `dd5796a` | Part 3: Three Mills dwelling (`site419-range-1`) re-registered on its printed block |
| `5bae2c6` | Separate water commit: river-system water cut back from the approach roads |
| `ad34c1e` | Alderson context check follows the Marshgate retrace |
| (last) | This report |

## 1. What changed and why

### Part 1 (T12d): bridge deck ends

**Cause.** `ground()` in `docs/infrastructure.js` raised the road near a bridge with a cone, `deck − 0.065 − 0.12 × distance from the route line`. Distance from the line grows across the road as well as along it. So at the deck end the approach fell 0.12 m per metre towards the kerbs, and the level deck stood 0.26–0.58 m above it. The street footway (6–7.1 m from the centreline) did not line up with the deck footway box (4.5–5.7 m), so it ended against the parapet.

**Choice: the rule changed in JavaScript, plus geometry from the builder.** The alternative was to fix the road elevation profiles at source. I did not, because a road record carries only one `elevationProfile`, and that profile overrides the landscape road for the whole record. Each High Street record crosses four or five bridges, so this would have replaced the street's measured levels everywhere.

- **New shared rule: `deckEndLevel()` in `docs/road-bridges.js`.** It is used by `ground()` in `infrastructure.js` and by `roadGround()` in `docs/tram-rails.js`, which mirrors `ground()`.
  - Distance is measured from the deck rectangle, not from the route line. The rectangle is the route ends plus half the deck width plus the 1.1 m street footway.
  - So the approach is level across the road at each deck end and falls at the same 0.12 m per metre along it.
  - Within 2 m of the deck end the street level is blended (smoothstep) to the deck road level. The road therefore meets the deck flush whether the street is lower or higher.
- **Deck-end footways.** `scripts/build_infrastructure.py` lays a 6 m taper strip at each end of every bridge with deck footways (16 strips, 874 triangles, new key `deckEndFootways`).
  - The strip follows the approach road's own line, turning from the deck axis where a connection deck meets its lane at a bend.
  - Its kerb draws in from the street carriageway edge to the deck footway kerb.
  - It is kept out of the carriageway and street-footway meshes. `roads`, which the railway and sewer openings read, is unchanged.
  - `infrastructure.js` draws the strip rising from street-footway level to the deck-footway top, with kerb faces, and earth fill below where the approach is raised.
- **Facts are in the register.** These values are in `data/maps/road-bridge-forms.json` defaults, with a `deckEndEvidence` string:
  - `deckFootway` (the box that `infrastructure.js` used to draw from literals);
  - `streetFootway`, `approachGrade`, `deckEndBlend` and `deckEndFootwayTaper`;
  - `minCarriageway`. The 2.2 m Three Mills Lane footpath deck, whose two footway boxes overlapped, is now a plain deck that its path meets flush.
- **Mirrors updated:**
  - The vista start height in `scripts/build_high_street_frontages.py` mirrors the cone and now uses the same rule (1.37 → 1.53 m).
  - `scripts/build_main_landscape.py` also mirrors the cone. I may not edit it, so it still fits the ground to the old rule. The old rule only ever lies below the new one, so ground never stands above the new road. A scratch cascade confirms this (section 4).

**Pegshole "3.3 m² footway hole".** This is not a gap in the road mesh. It is factory range `site947-range-2`, which stands on the footway line at the Pegshole east corner.
- `factory-buildings.json` predates T13, so the range was trimmed for the old road (2.79 of the 3.3 m², plus 0.42 m² of the standard 0.15 m building clearance).
- In this branch the new deck-end footway runs between the kerb and that building (footway in the 4.5–7.1 m band at that corner: 0.07 → 3.2 m²).
- A rebuild of `factory-buildings.json` trims the range by 9.9 m² and the corner footway fills (scratch: 2.99 of 3.3 m² footway; 0.31 m² is the building clearance).

### Separate commit: water at the deck corners

**River-system water.** `scripts/build_river_system.py` now trims the drawn water planes by the drawn street, footway and deck-end surfaces within 12 m beyond every route end.
- Only the one piece that reached an approach is cut: Pegshole west, 2.28 → 0 m².
- Every binary river-system file is byte-identical, so the landscape topology is untouched.

**Tide polygons: not done (outside my files).** The tide polygons under the approaches (59.8 m² at eight deck ends) come from `docs/data/river-network.json` (`build_river_network.py`), not from the river system. The river network was last built before T13.
- A scratch rebuild of the river network with the current roads takes them to 0 m² and also clears 62 m² of tide shelf under the retraced Marshgate Lane.
- Its vertex count is unchanged (`river-network.f32` same size; `.u32/.rgb/.cover` identical), so it should not break the landscape topology.
- I did not commit it because it is outside my file list.

### Part 2: Marshgate Lane

**Reading the OS.** I read the printed carriageway on the OS five-foot mosaic in straightened strips and in cross-profiles every 2 m along the prior centreline (`t18/straight.py`, `t18/lines.py`).
- The edges are the dotted kerbs where they are printed, otherwise the printed building face that bounds the carriageway: the east face from the High Street to the bridge, and St Thomas Mills at the north end.
- The prior trace ran a median 3.75 m (up to 6.6 m) west of the printed carriageway. It ran 1.5 m inside the printed P.H. at the corner and along the house fronts further north. T17's "about 3 m" was its average near the corner.

**New centreline.**
- It is the kerb midpoints, simplified at 0.3 m (`t18/retrace_marshgate.py`).
- It starts on the High Street centreline.
- It ends in the forecourt in front of St Thomas Mills (OS spot height 16.5). The prior trace ran on 39 m to the mill through the printed house row.
- The 4.4 m printed passage beside the mill is not modelled: a 7 m carriageway with footways would stand in `site257-mill` and `site257-south`. The mill's footprint lies about 1.5 m west of its printed face.

**The connection deck.**
- The provisional deck keeps its prior stations and moves with the lane. Its route now follows the lane's own vertices (3 → 4 points).
- The GIS channel along the lane's east side reaches 18.25 m along the deck's left edge, so the far abutment moves from 16.0 to 18.5 m in the register, with priors kept. This keeps the walled approach out of the water. It changes non-deck-end data in `road-bridge-forms.json`; see the decisions section.

**Other effects.**
- Width is kept at 7 m.
- The ground-plan river polygon on the east side lies 1–2 m inside the printed lane, so the builder's usual 0.6 m water clearance trims 64.7 m² (9 %) off the east edge of the 7 m corridor between 31 and 116 m.
- Register record: priors (`priorPoints`, `priorSourcePixels`, `priorBridgeSpanPoints`, `priorAlignmentEvidence`), the readings and the fit are in `t18Retrace` in `data/maps/district-road-traces.json`.

**Hotham, Randal and Barnby Streets** lie at z −500 to −741, outside the core box (z −280 to 1200). They are left as they are.

### Part 3: `wall-lane-south` and the Three Mills dwelling

**What the OS shows** (`t18/overlays/three-mills-dwelling-old-red-new-blue-path-black.png`):
- The F.P. (footpath) strip is about 6 m wide, between the river-bank line (x −568.4 at z 350) and the hatched dwelling block (Goad 802). The vista path already runs in it, 0.2 m from its centre at z 350.
- The block's west face prints at x −562.8 (z 346.7) to −561.8 (z 350.7). The modelled `site419-range-1` (EPFL fid 738916) stood 1.94 / 1.81 m west of that face, and its east wall about 1.9 / 1.8 m west of the printed wall.

**So the corner was wrong, not the path.**
- `data/maps/three-mills-north-footprint-alignment.json`: the footprint is moved 1.87 m along its own axis and 0.05 m across it (clear of range 2, whose shared wall bends). Shape, area and rotation are unchanged.
- The EPFL outline is kept as `priorEpflWorldFootprint`; the reading is in `osRegistration` (`osReading` / `interpretation`).
- The vista route is not moved; its evidence now records the OS reading, with `priorEvidence` kept.
- Ranges 2 and 3 read 1.8–2.0 m west of their printed faces as well, and range 4 0.4 m. They are not moved (see the decisions section).

## 2. Numbers before and after

Deck ends, from `t18/measure_deck_ends.mjs` (`ROOT=<checkout> node measure_deck_ends.mjs`).
- **What it measures.** It builds the real `infrastructure()` scene as `check_road_bridges.mjs` does. Then, 0.02 m outside every route end, it measures:
  - the deck sett top (h + 0.02) minus the approach road, every 0.25 m across the deck carriageway;
  - the deck footway top (h + 0.145) minus the highest approach footway or deck-end footway, every 0.05 m from kerb to parapet face.
- **Outputs:** before (main) is in `t18/deck-ends-before.txt`; after is in `t18/deck-ends-after.txt`.

| Deck ends | Road step before | after | Footway step before | after |
|---|---|---|---|---|
| Bow, Pegshole, St Thomas, St Michael's, Channelsea (10 ends) | 0.558–0.563 m | 0.021–0.022 m | no footway at all (42/42 samples empty) | 0.002 m |
| Abbey Mill crossing (2 ends; no deck footways) | 0.41 m | 0.020 m | – | – |
| Marshgate / Hunts Lane / Three Mills Lea (6 ends) | 0.03–0.26 m | 0.020 m | no footway (46/46 empty) | 0.002–0.005 m |
| Three Mills Lane footpath deck (path, 2.2 m) | 0.155 m | 0.035 m | – (now a plain deck) | – |

The maximum road step in the box is 0.563 → 0.035 m, and the maximum footway step is 0.002–0.005 m. Both meet the ≤ 0.05 m target.

| Other measure | Before | After |
|---|---|---|
| Pegshole east corner, footway in the 4.5–7.1 m band 0–3 m out | 0.07 m² | 3.2 m² (6.16 m² after a factory rebuild) |
| Drawn river-system water under approach roads | 2.28 m² | 0 |
| Tide polygons under approach roads | 59.8 m² | 59.8 m² (0 after a river-network rebuild) |
| Marshgate Lane: median / max deviation from the printed carriageway centre (53 stations) | 3.75 / 6.6 m | 0.067 / 0.28 m; a second, independent profile pass along the new line finds kerb midpoints within ±0.35 m from 20 to 136 m |
| `high-street-09` retained fraction | 0.577 (72.9 m²) | 1.0 (126.4 m²) |
| Buildings in Marshgate Lane (> 0.5 m², carriageway + 1.1 m) | 1 (hs-09, 4.0 m²) | 0 |
| `wall-lane-south` ribbon over buildings | 1.99 m² (`site419-range-1`) | 0 after the factory rebuild (scratch); 1.99 m² in this branch |

## 3. Structural diffs (against `d9980e9`)

**`docs/data/infrastructure.json`**
- **Changed:** `roads` (Marshgate Lane only), `roadTriangles` 8,152 → 8,451, `shoulderTriangles` 16,740 → 16,588.
- **`roadSurfaces`:** setts 1,172 → 1,415, macadam 6,604 → 6,632, cinder 417 → 455. These are re-triangulated where the deck-end strips cut them and along Marshgate Lane.
- **`roadBridges`:** only the `marshgate-lane-connection-0` route.
- **Added:** `deckEndFootways`.
- **Identical:** `railways`, every sewer key, `pathTriangles` and all text keys.
- **Determinism:** the builder run twice gives identical bytes, and the fixed point with housing is reached at once.

**`docs/data/housing-detail.json`:** unchanged; the fixed point is immediate.

**`docs/data/high-street-frontages.json`**
- `high-street-09` is whole.
- The `high-street-access` start height changes 1.372 → 1.527 m (sections likewise).
- `wall-lane-south` evidence plus `priorEvidence`.
- 3 coordinates of other buildings differ in the 14th decimal place.
- Deterministic.

**`docs/data/river-system-1900.json`:** `waterPolygons[7]` (28 → 31 vertices) and `inputHashes['docs/data/infrastructure.json']` only. Every `.f32/.u32/.silt/.cover` is identical, and two runs give identical bytes.

**Registers**
- `road-bridge-forms.json` (and its module copy): deck-end defaults, and the Marshgate deck abutments, water edges and priors.
- `district-road-traces.json`: Marshgate Lane, as described above.
- `three-mills-north-footprint-alignment.json`: `site419-range-1` record and its group's `reconciledPolygons`.
- `wall-river-vista.json`: one evidence string.

## 4. Checks

**`npm test`: 15 of 18** (main is 18 of 18). The three failures follow from the infrastructure change and clear in the cascade:
- `check_drainage_connections.mjs` and `check_flood_demo.mjs`: stale hash of `infrastructure.json`.
- `check_main_landscape.mjs`: ground above road on the moved Marshgate Lane and re-triangulated approaches, because the landscape was fitted to the old roads.

**Scratch cascade.** In a scratch mirror (`t18/mirror4`) I ran factory-buildings, frontages, historic elevation, river system, then landscape.
- `check_main_landscape.mjs` passes, as do `check_tram_rails.mjs`, `check_main_landscape.py` and `check_high_street_frontages.py`.
- `check_road_bridges.mjs` fails only on its stored road sample (the landscape under the approaches moved), as the cascade recipe expects.

**Changed assertions**
- **`scripts/check_road_bridges.mjs`:** the `BEFORE` road sample is refreshed with `--write-sample`, because the approaches now meet the decks and Marshgate's deck moved. It must be refreshed again after the landscape cascade. No other assertion is changed.
- **`scripts/check_three_mills_north_alignment.py`:**
  - Before, a group's footprint had to equal its EPFL source. Now a record that carries `osRegistration` must equal the source moved by the recorded vector, with the same 0.05 m² / 0.02 m² / IoU > 0.9995 tolerances. The vector must be a unit direction and under 3 m.
  - Other records are unchanged.
  - The check failed on main (`site924-os-17`). In this branch it fails on `three-mills-north-dwelling-802`, because `factory-buildings.json` is not rebuilt. After the factory rebuild (scratch) it fails on `site256-range-1`, the stale street trim T13 left.
- **`scripts/check_alderson_rope_context.py`:**
  - It pinned Marshgate Lane to the remaining-trades trace. Now, when the lane carries `t18Retrace`, it requires that trace kept exactly as `priorPoints` and `priorBridgeSpanPoints`, the same deck id, and the new centreline within 0.5 m (median) of the recorded readings.
  - All the mapped-roof clearance assertions are unchanged and pass.
  - The check passes on main and passes here.

**Python checks** (`t18/pychecks.py`, 75 checks): main 39 pass. After T18:
- **Newly failing on stale hashes or the stale landscape:** `check_historic_elevation`, `check_landscape_flood`, `check_main_landscape` (all on `infrastructure.json`).
- **Fails earlier than before:** `check_three_mills_north_alignment` (above).
- **Now passes:** `check_river_system` (it failed after Part 1 on the infrastructure hash; the separate commit rebuilt it).
- **Still failing as on main:**
  - `check_high_street_frontages.py`, on `wall-lane-south` until `factory-buildings.json` is rebuilt; it passes in the scratch rebuild.
  - `check_remaining_trades_context` and `check_mill_brush_context`, which pin the old Marshgate points among other things.
  - The `site924-os-17` family.
- `check_district_streets` passes.

**Other checks:** `npm run lint` shows only the existing warning in `docs/factory-buildings.js`, and `format:check` only the existing `eslint.config.js`; both are untouched. The changed JS is clean.

## 5. Render verdicts

Cameras are in `t18/cams-t18.json` (18). Image folders:
- Before: main on 4173, `t18/views-before/`.
- After: this branch on 4201, `t18/views-after/`.
- Scratch cascade: `t18/mirror4` on 4219, `t18/views-cascade2/`.

Note: `t18/views-cascade/` was rendered from port 4202, which turned out to be another agent's server. Ignore it.

**Deck ends** (`t18-<bridge>-<west|east>-a.png`, plus `t18-pegshole-east-b.png`)
- **Before:** at every deck end a pale vertical end face, 0.3–0.6 m high, with the rails stepping up it. The deck footways end as a raised box.
- **After:** the setts run flush onto the deck, the rails run straight on, and a pale footway strip draws in to each deck footway.
- **Pegshole east-b:** a narrow footway now runs between the kerb and `site947-range-2`.
- **Defect in this branch:** St Thomas, St Michael's and Pegshole show green ground patches poking through the re-triangulated setts, because the landscape is stale.

**Marshgate** (`t18-marshgate-ph-corner-eye`, `-ph-corner-oblique`, `-deck-north`, `-mill-end-oblique`)
- The P.H. now stands whole at the corner, and the lane runs east of it between the P.H. and the opposite building, as printed.
- **Defect in this branch:** the stale landscape covers much of the new lane in green. North of the deck the lane hugs the river: its east edge is trimmed by the GIS river, and the house row west of it is open ground, because those houses are not modelled.

**`wall-lane-south`:** unchanged in this branch, because `factory-buildings.json` is not rebuilt.

**Pegshole west corner (overhead):** the deck-end strips and bridge-head paving are visible at the corners. The small regional water patch under the approach is gone.

### Scratch cascade renders

`t18/views-cascade2/`, from `t18/mirror4` served on 4219. The mirror ran factory buildings, frontages, historic elevation, river system and landscape on this branch.

- **Bow, Pegshole, St Michael's, Channelsea:** flush deck ends. The green patches are gone, except a small one at the corner of the St Michael's west footway.
- **Pegshole east-b:** `site947-range-2` is trimmed back, and a continuous footway runs past it onto the deck footway.
- **St Thomas east: a stronger wave across the approach than on main.** This is the T12b open item (road sinks where triangles span a bank), and the re-triangulated setts here make it more visible. It needs a look on main after the cascade.
- **Marshgate:** the lane is clean and continuous from the High Street past the whole P.H. to the deck and along the river to the forecourt.
- **`wall-lane-south`:** the dwelling is moved east, clear of the path. The odd green slivers in the eye view are on main as well.

## 6. Smoke

Script: `t18/smoke.py t18-final --compare main-after-cascade --url=http://127.0.0.1:4201`. Result: **0 page errors**, 153 draw calls, and 8 differences.
- `highStreetFrontages.windows` 638 → 644: `high-street-09` built whole.
- `infrastructure.bridgeStructures.triangles` 8,712 → 8,824: the Marshgate deck's 4-point route and longer far abutment.
- `triangles` +6,275 and `reflection.triangles` +6,272: the deck-end footways (top, kerbs and fill), more road triangles and the frontage.
- `tramRails` stations 1,320 → 1,310, vertices 31,680 → 31,440, triangles 31,656 → 31,416, rise [0.0043, 0.0109] → [0.005, 0.0092]: the rails need fewer subdivisions now that the surface near the decks is level across.

The PNG screenshot timed out, as it does on main.

## 7. What I did not do

- **Landscape and cascade:** I did not run the landscape rebuild or the cascade in the branch. They were run only in scratch.
- **River network:** I did not rebuild it, so the tide polygons under eight deck ends and under Marshgate Lane remain.
- **`factory-buildings.json`:** I did not rebuild it. Part 3 and the Pegshole corner footway therefore need that rebuild on main.
- **Landscape builder:** I did not port the new deck-end rule to `scripts/build_main_landscape.py` (`road_ground` / `bridge_cone`).
- **Three Mills ranges 2 and 3:** not moved, though they are offset 1.8–2.0 m like range 1.
- **Marshgate widths:** not changed. 7 m is kept, against 3.4–6.5 m printed between kerbs.
- **Pinned registers:** I did not update the Marshgate points held in `remaining-trades-context-alignment.json` and `mill-brush-context-alignment.json`, which those (already failing) checks pin.
- **Hotham, Randal and Barnby Streets:** outside the box.

## 8. What I was unsure of

- **Kerb reading.** On the east side between the High Street and the bridge no kerb is printed, so I took the building face as the carriageway edge. A footway there would move the centre about 0.5–1 m west over that 25 m.
- **Mill forecourt end.** The lane ends in the forecourt rather than reaching the mill. The prior end was not printed lane either.
- **Deck-end footway at the Pegshole east corner.** Until the factory rebuild it is a 1.4 m strip beside a building that stands on the footway line.
- **In-branch Marshgate deck approach.** The deck's High Street end ramps 0.45 m in 2 m in this branch, because the street level at the new lane position comes from the stale landscape. The landscape builder's approach-cutting rule should flatten it; I saw no ramp in the scratch-cascade checks, but did not measure it there.
- **GIS-to-print offset at Three Mills.** I measured it on range 1 alone (and noted it for ranges 2–4). I did not check whether it is a sheet-wide offset of the EPFL tracing.

**Process note: an accidental write to main's `reference/`.**
- Several Python checks write report files into `reference/`, including `check_district_streets.py` and the `check_*_alignment.py` scripts.
- My first run of all checks on a baseline copy wrote generated, git-ignored check reports into the main checkout's `reference/` through the symlink, around 13:56. The baseline copy was main's own code and data. Examples: `reference/district-streets/geometry-checks.json` and `reference/footprint-model-alignment/verified-*.json`.
- After that I replaced those symlinks with private copies in the worktree.

## 9. Decisions for the reviewer

1. **Rebuild on main in this order:**
   - factory buildings, then frontages;
   - optionally the river network, for the tide polygons; this is outside my scope but verified in scratch;
   - historic elevation, river system, landscape, then the flood builders, factory yards, drainage, manifest;
   - finally refresh the road-bridge sample.

   **Alternative:** skip the factory rebuild and move the vista path 1.5 m west instead. I advise against it: the OS shows the building was wrong.
2. **Port `deckEndLevel()` to the landscape builder's `road_ground`.** Without the port the landscape stays slightly below the new deck-end road, covered by fill curtains. The port should be a follow-up task, since I was not allowed to touch that file.
3. **Marshgate deck far abutment (16 → 18.5 m).** This changes non-deck-end data in `road-bridge-forms.json`. The alternative was to leave a walled approach standing in the river, which fails `check_road_bridges.mjs`.
4. **Marshgate north end.** I ended the lane in the forecourt. The alternatives are to keep the prior two "mill approach" controls through the printed house row, or to narrow the lane.
5. **Re-register Three Mills ranges 2 and 3** by the same OS reading, so the terrace row stays in line.
6. **Correct the GIS river along the east side of Marshgate Lane.** It lies 1–2 m inside the printed lane. This is river-data work.
