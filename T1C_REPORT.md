# T1c report: completing the Northern Outfall Sewer

Branch `worktree-agent-a6d87929c4559f387`. The worktree started at 116c0ae, without T8. I ran `git merge main` (a fast-forward to 3ad5652, "Delegation plan: record T8 outcome", which includes "Merge T8: sewer embankment as an earthwork...") before starting. All the work below sits on top of 3ad5652.

## What changed and why

1. **`scripts/build_panorama_data.py`, sewer block only.**
   - **Route extensions.** A new `sewer_route_extensions()` replaces the two straight end-bearing extrapolations. The traced points are constants: `SEWER_WEST_TRACE`, `SEWER_EAST_TRACE`, `SEWER_EAST_END_X` and `SEWER_WICK_LANE_CROSSING`.
     - Source: crest centrelines read from the OS London five-foot plan, 1893–96 revision, using `factory_map_sources.mosaic()` with layer `os-london-five-foot-1893`, read-only from the main checkout's `reference/nls-tiles`. I picked points on the crest between the slope hachures and the "NORTHERN OUTFALL SEWER" lettering, then checked them by overlaying the trace on crops.
     - Reading accuracy is about 2–4 m. My pick at the old western start lands 2 m from the existing trace.
     - The data record gets new keys `routeExtensions` (west and east, each with mapped and inferred metres, source and evidence) and `portal`. `extensionMetres` now holds the inferred length (418.2), and `evidence` is rewritten to match.
   - **Portal.** A new `portal_cut()` adds a `portal` bank obstacle 0.3 m east of the portal face, so the bank ends inside the headwall with a `kind: portal` bank end. The crest stops flush with the portal face.
   - **Toe waves keep the old chainage.** `EarthBank` takes an `origin`: the toe, blend and swell waves are measured from the pre-T1c western start. Without this, moving the route start would have shifted the waves along the whole bank. With it, the earlier stretch keeps its form, including all of the High Street bank.
   - **Unchanged by design:** the water and railway clipping, the road openings, the garden and the High Street correction file.
2. **`scripts/build_infrastructure.py`.** Six lines: the crest polygon is cut flush at the portal face instead of ending in a round cap.
3. **`docs/sewer-crossing.js`.**
   - **Trough refactor.** The Channelsea trough loop became `trough(parent, from, to, floor, maxStep)`. The Channelsea calls it with its old arguments, so its geometry is unchanged (its `bounds` in the report are unchanged).
   - **Water spans.** New `waterSpans()` pairs consecutive water `bankEnds` that face each other across a channel. Each pair other than the Channelsea gets:
     - an iron trough with the same mitred section and plate-girder relief. It runs 2 m into the bank behind the deepest point of each end wall within the crest width.
     - two brick abutments. Each is a block from 0.2 m proud of the end-wall face to 3 m behind it, with faces parallel to the skewed bank end and sides along the deck.
     - piers only where the clear span exceeds the Channelsea's clear span of 45.71 m.
   - **Interpretation constants** are in `spanAssumptions`: embedment 2 m, minimum soffit 1.4 m, segment length 6 m, pier length 2 m.
     - The minimum soffit keeps the trough 0.3 m above illustrative high water (`tide.high` 1.1 m). This matters at the City Mill River, where the sewer descends towards Stratford High Street and the deck is only 3.6–4.1 m high. There the trough is 1.7–2.2 m deep instead of 2.9 m.
   - **Portal.** New `sewerPortal()` draws a brick headwall across the deck end, 17 m wide (the crest plus 1 m either side) and 1.55 m deep, with a parapet 1.2 m above the walk. It has a stone coping and a blind segmental arch ring in dressed stone (10 m span) on its west face. All of this is in `portalAssumptions`, labelled interpretation. The bank end wall (`bankEndWalls`, unchanged) runs down both slopes from it.
   - **Mill Meads arch.** The road level for the arches is now sampled at five points on the street centreline under the deck, not at the street edges.
   - **Report.** The report gains `spans` and `portal`.
4. **`scripts/check_sewer_crossing.mjs`.** Assertions added; none edited. They check that:
   - every water span other than the Channelsea is reported;
   - a raycast at mid-span hits a trough at y ≥ 1.1;
   - raycasts at both abutment centres hit brick;
   - the pier count follows the rule;
   - the portal exists, with a `portal` end wall and a parapet above the walk.
5. **`docs/data/ground-plan.json`** (`neighbourhood.sewer` only) and **`docs/data/infrastructure.json`** (`sewerBanks`, `sewerCrestTriangles`, `sewerRailEdges` only) are patched in place by scratch scripts. Triangles that are geometrically identical to committed ones keep their committed form; the only differences there were vertex rotation and `0` versus `0.0`. A clean rebuild of the plan's sewer key matches the patched file geometrically (verified). `docs/app.js` is not changed; it needed nothing.

## Water spans

Chainages are measured from the new route start at the portal. They are 492.66 m larger than before because the route now starts further west.

| span | chainage (old) | bank-end length | clear span | piers | trough | soffit |
|---|---|---|---|---|---|---|
| Lea at Old Ford (new), x −1576..−1553 | 229.9–250.8 | 20.9 m | 21.0 m | 0 | 219.5–257.8 | 4.0 |
| Lea branch, x −1168..−1137 | 646.5–678.8 (153.9–186.2) | 32.3 m | 29.1 m | 0 | 639.9–687.9 | 4.0 |
| crossing near x −883..−849 | 938.2–974.8 (445.5–482.1) | 36.6 m | 34.7 m | 0 | 927.8–983.0 | 4.0 |
| City Mill River, x −616..−591 | 1218.7–1244.4 (726.0–751.7) | 25.7 m | 23.7 m | 0 | 1213.6–1250.0 | 1.4 (clamped) |
| Channelsea (unchanged module) | 1923.9–1971.6 | 47.7 m | 45.7 m | 0 (no in-channel pier, as before) | ±30 m from anchor | 4.0 |

No span needs piers: the Channelsea module has none and its clear span is the longest.

## Extensions: mapped and inferred lengths

| end | mapped (five-foot) | inferred | ends at |
|---|---|---|---|
| west | 492.7 m, from (−1790.5, −702.5) to the old start (−1317.8, −567.4), crossing the Lea at Old Ford | 0 m | Wick Lane portal: the lane's east kerb, where the five-foot marks B.M. 35.3 |
| east | 2093.3 m, from the last OS VIII.32 point (349.54, 51.25) to the edge of five-foot coverage at (2289.2, 687.0) | 418.2 m, on the last mapped bearing | (2700, 765.2), Blind Lane, the West Ham borough boundary |

- **East route.** The old 1400 m extrapolation ran north of east past the mapped bend. The five-foot plan shows the bend at x ≈ 700, a run south-east across the London, Tilbury and Southend Railway, and a run through Plaistow. The mapped 348 m from 349.5 to 697.8 keeps the old line, which agrees with the five-foot within 2 m. Beyond x 2289 the five-foot tiles are blank or missing. The OS six-inch second edition shows the embankment on the inferred line within a few metres, but I did not use it as a trace.
- **Ground at the east end.** The end at x 2700 is inside the landscape base ground (`replacementBaseGround` reaches ±2750 m; ground exists under the toe cap, checked). It is also at the fog distance from the scene, with about 5% visibility at 2700 m.
- **Ground at the west end.** Ground exists at both ends: the regional marsh mesh, or the flat base ground just west of the mesh edge at the portal's north-west corner. Neither end floats in the renders.

## Mill Meads works road arch (not restored)

| | rise | crown clearance | edge clearance |
|---|---|---|---|
| before T3 (T1b report) | 3.51 | 6.51 | 4.71 |
| base (in-browser smoke) | 1.05 | 4.05 | 3.30 |
| after, centreline samples | **1.49** | **4.49** | 3.44 |

Abbey Lane is unchanged (3.16 / 6.16 / 4.41).

**Not back to 3.5 / 6.5.** I probed the drawn ground meshes the way the browser's `drawnGround` does. The street centreline under the deck is itself a ramp in the T3 landscape: 1.66 at the north crest edge, 0.95 at the centre and 0.08 at the south edge. Before T3 it was about −0.36. `infrastructure.js` lays the road on that same ground. The edge samples were only part of the problem: the arch is low because the road under it now climbs 1.7 m.

Honest options:
- (a) sample only the centre point: rise 2.2, crown clearance 5.2, but less headroom at the north portal;
- (b) have the landscape owner lower the corridor under the deck;
- (c) accept 1.49.

I kept the conservative centreline maximum.

## Structural diffs (path level, against HEAD 3ad5652)

```
ground-plan.json (patched; only neighbourhood.sewer differs, asserted)
  bankEnds 16 -> 19 (+1 portal, +2 Old Ford water)   banks 11490 -> 14653
  crest (flat at the portal, new east line)          route 17 -> 40
  evidence, bankEndsEvidence, bankFormEvidence (text)
  extensionMetres 1400 -> 418.2                      portal, routeExtensions added
infrastructure.json (patched; only these three differ, asserted)
  sewerBanks 11459 -> 14622   sewerCrestTriangles 2032 -> 2904   sewerRailEdges 4 lines, longer
```

- **Bank triangles** changed only:
  - west of x ≈ −1300 (the new stretch and the old western cap) and east of x ≈ 330 (the old extrapolation);
  - plus two diagonal flips each near x −700 and x −400, with the same vertices.
- **High Street.** Zero bank or crest triangles change within 60 m of the High Street centre (canonical comparison). `sewerHighStreet` is untouched.
- **Rail edges.** Points change only from x −1316 westward (the old start is now a mitred join) and east of the High Street from x 349.
- **Full-rebuild drift, not carried over:** in `ground-plan`, terraces 99 → 98 and garden `accessCorridors` 15 → 16 (both known; garden beds unchanged); in `infrastructure`, the road-mesh drift.
- **File sizes:** `ground-plan.json` 1.23 → 1.47 MB; `infrastructure.json` 10.11 → 10.43 MB.

## Checks

- **`npm test`:** 13/15, with the known `check_drainage_connections` (missing git-ignored mosaic) and `check_flood_demo` (stale hash) failing.
- **`check_sewer_crossing.mjs`:** PASS, with the new span and portal assertions. **`check_sewer_high_street.mjs`:** PASS.
- **Prettier and ESLint** are clean on both changed JS files.
- **Python checks that pass:** great_eastern (one sewer crossing, headroom > 3 m), gardens (153 plots), continuous_structures, river_banks, core_river_connections, north_london_connection, housing_frontages, abbey_station_plan and manor_road.
- **`check_scene_data.py` FAILS** because of this change. Line 56 asserts that the route *starts* with `sewer-high-street.json` `westernRoute`, and the route now starts at Wick Lane. The file is outside my permitted list, so I did not edit it.
  - With that one line relaxed in a scratch copy (westernRoute must appear contiguously in the route), every other assertion passes.
  - The proposed line is `k=sewer['route'].index(correction['westernRoute'][0]); assert sewer['route'][k:k+len(correction['westernRoute'])] == correction['westernRoute']`.
- **Fail on stale input hashes:** main_landscape (ground-plan) and landscape_flood (infrastructure); these need the landscape rebuild that another agent owns. river_system fails on a missing git-ignored reference file.

## Smoke

`review_smoke.py t1c-sewer-complete --compare t1c-base`, run from a scratch copy with a 900 s tween wait, on port 4187. The base was a `git archive` of HEAD `docs/`. Screenshots timed out (environment); the JSON is complete. **0 page errors**, draw calls unchanged at 150. There are 9 differences:

- `triangles` 8,178,310 → 8,213,669 and `reflection.triangles` +35,359. Most of this is the 1.75 km of extra route: parapet rail boxes (about 20k), deck slab boxes (about 7k) and bank (+3.2k) and crest (+0.9k) triangles. The rest is trough segments and girder relief at four spans, abutments, three new end walls and the portal.
- `sewerCrossing.bounds.abutment.min/max`: about 1 mm. Chainages are rounded to 0.01 m and all shifted by the new route start.
- `endWalls`: 16 → 19; kinds gain `portal`.
- `portal`: new.
- `spans`: new (table above).
- `roadArches`: Mill Meads 1.05 → 1.49 (above); Abbey Lane edge clearance 4.40 → 4.41.

After the smoke run I recoloured the portal's arch ring from brick to stone. That only moves the ring's triangles from the brick mesh to the coping mesh.

## Render verdicts

Before and after renders are in `<scratchpad>/t1c/views-before/`, `views-after/` and `views-after2/`. The scratchpad is `/tmp/claude-1000/-home-jic823-book-website/158d731a-06ad-4794-89f0-96291b5302cd/scratchpad`.

| camera | verdict |
|---|---|
| author City Mill (−60,3,460) as given | Shows a long low wall far from the sewer; identical before and after. That camera does not frame the sewer. |
| `t1c-city-mill` (−625,2.5,−345 → −597,4,−395), on the river, span at chainage 1218.7–1244.4 | **Fixed.** Before: bare slab with railings. After: the iron trough with girder relief sits under the deck between the brick end walls. |
| author west end (−1250,4,−560) | The camera now sits inside the extended bank slope, so it shows the deck underside. Uninformative; the old end no longer exists. |
| `t1c-west-end-wide` | **Fixed.** Continuous embankment and rails run on west towards Old Ford. |
| `t1c-old-ford` and `-top` | **New span reads correctly.** A trough on abutments, brick end walls on both banks, daylight only over water. |
| `t1c-wick-lane-portal`, `-close`, `-oblique`, `-top`, `t1c-portal-deck` | **Portal reads correctly.** A brick headwall with stone coping and a stone blind arch ring, with wing walls down the slopes. From the walk, a parapet closes the end. The oblique view shows a pale strip along the far crest edge near the portal that I did not trace (possibly the deck slab edge where the bank meets the crest). |
| `t1c-east-bend`, `t1c-east-along` | **East line now follows the mapped bend and runs south-east.** Continuous bank, toes on the ground. |
| `t1c-east-end` | The bank ends in a rounded earthwork cap on the ground at x 2700, as the old east end did. |
| `sewer-toe-1s` (Lea branch) | **Fixed.** The trough now shows under the deck where there was bare slab. |
| `t1-crossing-448` | **Fixed.** Trough visible under the deck. |
| `t1b-mill-meads-road-north` | Arch slightly higher (rise 1.05 → 1.49). It still looks flat, and the green ground still shows through the setts under it (landscape). |
| `author-1-corrected` (Channelsea) | Unchanged, as intended. |

## What I did NOT do

- I did not model Wick Lane, the London, Tilbury and Southend crossing, or the streets in Plaistow. The bank runs continuously over the unmodelled railway and streets on the extensions.
- I left out the five-foot plan's embankment between Wick Lane and the North London Railway, and the penstock chamber, on the author's direction that the sewer is covered there.
- I did not trace from the six-inch beyond the five-foot coverage, as instructed. I did not add a trough "entering" the portal (no span runs up to it).
- I did not change `app.js`, the Channelsea module's geometry, the High Street crossing, the landscape, `check_scene_data.py` or any `inputHashes`.

## What I was unsure of

- **Mill Meads arch target.** The target is unreachable without changing the landscape or the arch rule (above).
- **City Mill trough.** The trough there is drawn shallower to stay above high water. The real sewer section and level west of the High Street are unresolved; it may have dipped or crossed differently.
- **Portal form.** The headwall's position at the east kerb is mapped. Its form is wholly interpreted. The five-foot plan suggests the sewer actually bridged Wick Lane (B.M. 35.3 at the crossing, the lane at about 24–26 ft either side) and stayed embanked to the railway.
- **Trace accuracy.** It is limited by hand reading at 2–4 m.
- **Vertex shifts.** The east bank vertices from x 330 shift by centimetres, because the old segment was re-subdivided. This is harmless, but it is churn.

## Decisions for the parent

1. Apply the one-line relaxation to `scripts/check_scene_data.py` line 56, or ask me to.
2. Mill Meads arch: option (a), (b) or (c) above.
3. Accept the new `neighbourhood.sewer` keys `portal` and `routeExtensions`, and `extensionMetres` now meaning the inferred eastern length.
4. Whether to open the bank for the London, Tilbury and Southend Railway at x ≈ 750 (needs a trace of that railway), and whether Wick Lane should become a modelled street with the sewer bridging it.
5. Schedule the landscape and derived-file rebuild for the new `ground-plan.json` and `infrastructure.json` hashes. The landscape's own sewer handling still knows only the old route.
