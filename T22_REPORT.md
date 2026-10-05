# T22 report: the Bromley/Bow terrace drawn at its OS levels

4–5 October 2026. Branch `worktree-agent-af9b8982435e57d6c`, worktree `/home/jic823/book_website/.claude/worktrees/agent-af9b8982435e57d6c`. Based on `main` at `c0a7a43` (T21 merged; `git merge main` was a fast-forward). Scratch: `/tmp/claude-1000/-home-jic823-book-website/61f71781-342b-470a-9012-cb46325e06a9/scratchpad/t22/` (called `t22/` below). The author approved the task ("fix it now"; T21 decision 1, option a).

## Bottom line

- **The terrace west of the Lea and Bow Creek is now drawn at its OS levels.** Before, the scene drew the river network's flat floor at about 0 m there. Now the main landscape applies in full over the **terrace zone**, which is the core box west of x −628 (T21's west strip, with the High Street to Bow Bridge).
  - It is drawn as a 5 m mesh.
  - It uses the regional ground grid, corrected to 116 OS readings: 87 terrace, 24 street and 5 yard. The terrace readings include 9 towing paths.
  - It is also corrected to the regional bank crest along the shorelines, wherever no reading is near.
- **West-side ground readings (103) against the drawn ground:**
  - median drawn − OS: **−7.21 → 0.00 m**;
  - 90th percentile of |drawn − OS|: **8.31 → 0.45 m**;
  - **94 of 103** within ±0.6 m (before: 2).
- **High Street (13 readings):** median −1.95 → 0.00, p90 4.17 → 0.03 m.
- **Terrace zone, all 116 readings (exceptions included):** median 0.006 m, p90 0.445 m. All 9 readings beyond ±0.6 m are listed exceptions with reasons (table below).
- **East of x −628, T21's results are unchanged.** Every T21 zone has the same median, p90 and count, except one improvement: Three Mills Lane at the bridge improves from −2.25 to −1.66 m.
- **Seating: no building, chimney, kiln, tank, frontage or housing row in the west stands more than 0.19 m off the median drawn ground under its footprint.**
  - Before: 66 of 579 were off by more than 0.3 m (59 buried, 7 floating), up to 2.47 m.
  - East: 29 → 18 objects beyond 0.3 m. None got worse; the remaining 18 are T21-era items.
  - On sloping footprints the extremes remain (numbers below).
- **Three Mills Bridge** takes its OS deck level: 21.2 ft = 4.23 m (was a 2.2 m estimate; the prior is kept). Without it, the raised Three Mills Lane would have fallen 2.8 m into a cutting to reach the deck. **No other deck moved.**
- **Checks:**
  - `npm test` **21/21**, with T21's check extended for the terrace;
  - lint and format clean;
  - cascade deterministic (two full runs, identical bytes);
  - smoke: **0 page errors**, 19 differences, all explained.
- **Flood:** `landscape-flood-1900` figures are unchanged, because it reads the historic scaffold (T21 decision 5). The 1897 and 1904 accounts still read plausibly.

## What changed and why

### 1. Register (`data/maps/os-ground-levels.json`, `scripts/prepare_os_ground_levels.py`)

- **New `terraceZone`** `[-1280, -240, -628, 1160]` with `terraceFeatherMetres` 60.
- **New use `terrace`.** It covers ground readings in the west strip, and High Street readings under T21's support threshold, that are neither street nor premises. These are open ground, streets the model does not draw, towing paths and yards of sites without a pad.
- **The same rules as T21 otherwise:**
  - a street reading within half the width + 6 m of a drawn street is a `street` reading;
  - inside the zone, a **yard-setting** reading within 1.5 m of a site is a `premises` reading and creates that site's pad.
- **Result: 114 readings changed use, all in the west strip and High Street:**
  - 85 none → terrace;
  - 13 + 8 none → street (west strip and High Street);
  - 5 none → premises (255, 421 ×2, 417, 260);
  - 2 High Street none → terrace.
- **Per-reading decisions, each with evidence:**
  - 9 towing-path `embankment_top` readings → ground/terrace. The path is the ground beside the river.
  - 2 East London Soap Works readings "rails at grade in the works yard" → ground/terrace.
  - St Leonard's Street on Four Mills Bridge over the Limehouse Cut → structure/none. It is a deck level, and neither the street nor the bridge is drawn there.
- **9 new exceptions** (below). The text of T21's Three Mills Lane exception is updated for the new deck level.
- No reading east of the zone changed.

### 2. Ground (`scripts/build_main_landscape.py`, `scripts/os_ground_levels.py`)

- **Support.** The terrace weight is 1 inside the zone. It falls by smoothstep to 0 over 60 m outside the core box, on the zone's west, north and south sides only.
  - The regional early-marsh support was 0 there, which is why nothing was drawn.
  - The terrace readings do not extend T21's 30 m support beyond the zone.
- **Correction.**
  - **Inside the zone:** the regional ground (`filled`) plus a Gaussian-process correction, with the same kernel as T21 (40 m length, 0.1 m noise, per dry compartment). Its controls are:
    - the terrace readings;
    - the zone's street readings, at the ground under the road surface (−0.065 m);
    - the zone's yard readings;
    - **370 bank-crest controls**: the regional bank crest, which comes from the OS bank-top readings along each bank, placed every 15 m along the shorelines and 4 m inland, wherever no OS reading lies within 15 m. Streets (+5 m) and the 30 m around road bridges are excluded.
  - **East of x −628:** T21's own correction (marsh readings and rail side only) applies unchanged. The two are blended over 20 m *inside* the zone edge.
  - **Why the bank controls are needed:** the regional grid ran at terrace height to the water's edge. It stood 2.2–3.3 m above the OS towing paths. Without the bank controls, the bank band drew that height at the shore, and in an intermediate build it tilted the Limehouse Cut banks over the water (render `t22/pairs-v4/t22-maltings-from-cut.jpg`).
- **Mesh.** The regional ground mesh now also covers the zone and its feather band, at a **5 m step**; the rest keeps its 20 m step.
  - The two grids are aligned. On the join, 549 fine vertices take the coarse surface (at most 1.20 m), so no crack opens.
  - Ground-mesh vertices: 292,695 → 575,370. Drawn area: 12.81 → 13.51 km².
- **Pads.** Inside the zone and its band, a site has a premises pad only where the OS gives its yard level:
  - 255 Lime Works 2.49;
  - 421 Albion Works (surface through 2 readings);
  - 417 Four Mills Distillery 2.68;
  - 260 Howard & Sons 2.74 (was 2.69, from the regional yard median).

  Every other terrace site stands on the corrected terrace. These include the 22 T21 "marsh-supported estimate" pads in the zone, such as 942 (pottery, 1.55) and 939 (0.85). Pads: 58 → 37.
- **Seats.** Some objects are now seated on the **median drawn ground under their footprint** (2 m samples; eight points round round plant):
  - every object inside the zone without a pad, or belonging to a terrace site without one;
  - every object inside the core box that lies outside its site's pad outline (`siteGround[].outsideIds`, 52 objects). For example, the East London Soap Works' 31 ranges are traced 200 m from site 796's outline.

  The seats are recorded per object id in `main-landscape-1900.json` `seats` (602). `docs/main-landscape.js` `seat()` reads them; no site ids appear in JavaScript.
  - Why this rule: the 10 m level field only approximates the drawn surface beside banks, walls and batters. In an intermediate build it left the Three Mills mill buildings 1.2–2.1 m low.
  - Building edge caps use the same rule, which moved 455 core-tile vertices by −0.24 to 0 m beside four outside-pad buildings at Abbey Mills and site 1125.
- **Wharf walls on the terrace.** A retaining wall whose ground 6 m behind lies in the zone carries its coping at the higher of the bank crest and that ground: its pad, street or the corrected terrace (`terraceWalls`).
- **Street corridors** keep T21's rule: inverse distance from their own readings, never through water.
  - Their readings are also controls of the terrace surface, so street and ground meet.
  - I tried a variant that laid the corridors on the terrace surface itself. It made the St Thomas and Pegs Hole approaches sag 0.3 m to their bridge cones, so I reverted it.

### 3. Three Mills Bridge (`data/maps/district-road-traces.json`, `remaining-trades-context-alignment.json`, `road-bridge-forms.json`, `docs/road-bridges.js`)

- `three-mills-lea-bridge` height 2.2 → **4.23 m**: the OS spot height on the bridge, sh_538259_182802, 21.2 ft. The record now carries `priorHeight` 2.2 and `heightEvidence`.
- The same change was made in the remaining-trades register, whose bridge record must equal the road's.
- The bridge-forms note "spot heights … are not used to change any height" now records this one exception, identically in the JSON and JS copies.
- `infrastructure.json` was rebuilt (6 paths changed: the bridge and its span record). Infrastructure and housing reached a fixed point in one round; `housing-detail.json` is byte-identical.

### 4. Checks changed

- **`scripts/check_os_ground_levels.mjs`:**
  - the use list adds `terrace`;
  - new section 5 asserts the terrace zone: at least 90 applied readings, median ≤ 0.3, p90 ≤ 0.6 *including exceptions*;
  - every object with a recorded seat is seated on it (577 objects).

  No existing assertion was relaxed.
- **`scripts/check_road_bridges.mjs`:** the `BEFORE` sample was refreshed with `--write-sample` (details below).
- **`scripts/check_remaining_trades_context.py`:** the bridge-versus-prior comparison excludes `height`/`priorHeight`/`heightEvidence`, and now asserts `priorHeight == prior height`.
  - This check fails on base before it reaches that line ("Stratford High Street — Channelsea approach"), so the edited line itself is not exercised. See Checks.

## Residuals before and after (drawn − OS, metres; ground-type readings)

`t22/base/` is unchanged main; `t22/final/` is this branch. Both are classified with the final register, so "before" includes the reclassified towing paths. Maps: `t22/final/resmap.png` (left: residuals; right: change in drawn ground).

| Zone | n | median before | p90 before | within ±0.6 before | median after | p90 after | within ±0.6 after |
|---|---:|---:|---:|---:|---:|---:|---:|
| **West strip (Bromley/Bow)** | 103 | −7.21 | 8.31 | 2 | **0.00** | **0.45** | **94** |
| **High Street** | 13 | −1.95 | 4.17 | 3 | **0.00** | **0.03** | **13** |
| Three Mills / Mill Meads (applied) | 19 | 0.00 | 1.11 | 14 | 0.00 | 1.11 | 14 |
| Abbey Mills (applied) | 9 | 0.00 | 0.07 | 9 | 0.00 | 0.07 | 9 |
| Channelsea east (applied) | 19 | 0.00 | 0.10 | 19 | 0.00 | 0.10 | 19 |
| LT&SR corridor | 12 | 0.02 | 0.09 | 11 | 0.02 | 0.09 | 11 |
| Bromley gasworks (applied) | 23 | 0.00 | 0.19 | 22 | 0.00 | 0.19 | 22 |
| Abbey marsh south (applied) | 13 | 0.00 | 0.02 | 13 | 0.00 | 0.02 | 13 |
| **All applied** | 211 | −1.12 | 8.07 | 93 | **0.00** | **0.25** | **195** |

Where the readings come from:

- Before, the west median was −7.21 m because the floor was at about 0 against 15–36 ft.
- After, by use: street 24 (the road surface), terrace 87, premises 5.
- `check_os_ground_levels.mjs` (all applied, exceptions excluded): median 0.006 m, p90 0.070 m.

**Bench marks** (drawn − mark): west strip (36) median −0.78 m, High Street (5) median −0.59 m, so the marks stand 0.6–0.8 m above the ground, as expected for marks on walls (before: −7.84 and −1.96 m). Four marks stand below the drawn ground, three of them by 0.05–0.26 m. The largest is the Bow Tank Works corner mark, 33.1 ft, which is 0.99 m below the drawn ground. The street readings at the same corner give 36.4 ft, so the mark is about 1 m below the street. I left it as a conflict.

**Exceptions** (applied readings beyond ±0.6 m; full text in the register):

| Reading | OS ft (scene) | after | Reason |
|---|---|---:|---|
| sh_538201_182860 | 15.0 (2.34) | −3.33 | Towing path that falls inside the drawn Lea (the GIS channel is wider than the OS one here). |
| sh_538054_183338 | 17.8 (3.19) | −2.23 | Marshgate Lane, 17 m south of the provisional 1.5 m Marshgate Lane connection deck. The lane is cut down to the deck (decision 4). |
| sh_538085_182100 | 14.8 (2.28) | −1.59 | Limehouse Cut towing path, 1.0 m from the drawn Cut edge, on coarse river-system bank triangles. |
| sh_538236_182814 | 14.2 (2.10) | −1.27 | Towing path dot 1.2 m from the drawn Lea edge, on the model's 3 m earth bank face. The crest stands at the OS level 2–3 m back. |
| sh_538047_183035 | 14.7 (2.25) | −1.15 | Same, 1.5 m from the water. |
| sh_538072_183022 | 14.4 (2.16) | −0.98 | Same, 1.5 m. |
| sh_538128_182907 | 14.5 (2.19) | −0.66 | Same, 1.9 m. |
| sh_537628_183260 | 14.2 (2.10) | +0.72 | Old Ford towing path inside the bank band, where the regional bank crest (2.98 m) is drawn. |
| sh_537671_183228 | 14.1 (2.07) | +0.91 | Same. |

## Seating (seat = `landscapeLift` − 0.1, against the median drawn ground under the footprint)

Tools: `t22/seat.mjs` (builds the page's `level()`, samples every footprint at 2 m) and `t22/seatstats.py`. Tables: `t22/base/seat.txt` and `t22/final/seat.txt`. East changes: `t22/final/seatdiff-east.txt`.

| | n | beyond 0.3 m | floating > 0.3 | buried > 0.3 | p90 of the absolute offset | max |
|---|---:|---:|---:|---:|---:|---:|
| West, before | 579 | 66 | 7 | 59 | 0.35 | 2.47 |
| **West, after** | 579 | **0** | 0 | 0 | 0.01 | **0.19** |
| East, before | 295 | 29 | 12 | 17 | 0.28 | 1.98 |
| East, after | 295 | 18 | 6 | 12 | 0.16 | 1.98 |

The 579 west objects are 468 factory ranges, 42 chimneys, 18 kilns, 5 tanks, 25 High Street frontages and 21 housing rows.

- East: 19 objects changed by more than 0.1 m and **none got worse**. Those that changed are the Three Mills mill buildings and outside-pad buildings at Abbey Mills and 1125.
- The 18 remaining east items are all T21-era. They include holder bromley-5 (−1.98) and the 924 weighbridge hut (+1.47) (decision 7).
- **Sloping footprints** (west, after): the ground at the highest point of a footprint stands above the seat by a median 0.08 m, p90 0.43 m, max 2.92 m (32 objects over 0.6 m). The seat stands above the lowest point by a median 0.08, p90 0.66, max 3.65 m (66 over 0.6 m). Before, these were p90 1.32 / 0.16.
  - The large values are buildings whose traced footprints reach over a bank face or into the water:
    - site788-os-1 at Bow Bridge;
    - b229-grain-store over the Limehouse Cut (it overhung the water on main too);
    - site257-mill;
    - b942-kiln-range;
    - b475 ranges on the Limehouse Cut bank slope.
  - A single seat per object cannot follow them. Stepped seating is decision 6.
- **Cranes** use `level()` at their point at runtime, so they always stand on the drawn ground.
  - Smoke `wharfCranes.placed`: 8 cranes moved, for example Albion wharf 0 → 2.97, Bow Flour wharf −0.10 → 2.97 and St Leonard's wharf 0.62 → 1.68.
  - `build_wharf_cranes.py` was rerun; only the input hash changed.
- Housing extensions, privies, walls and plots, yard stock, trees and tram rails all sample the drawn ground at runtime and follow it.

## River edges

**Wall copings** (T2/T14 retaining-wall routes; `t22/final/walls-routes.txt`). **Lengths are unchanged.**

- In the zone: 18 routes, 972.6 m, of which 848.5 m changed.
- Outside the zone, only route 4 changed (188.6 m, the feather band north of the box, +0.0–0.23 m).

| Route (centre) | Length m | Coping before | Coping after |
|---|---:|---|---|
| 1 (−742, −228) | 326.1 | 2.30–2.89 | 2.61–2.93 |
| 10 (−973, −35), Bow back river at Imperial Saw Mills | 87.3 | 1.65–2.48 | 2.98–3.00 |
| 22, 23 (−1002, 37), (−973, 6) | 14.6, 5.2 | 1.65 | 2.32–2.34 |
| 26, 27 (−722, 222), (−739, 162), Lea west bank by the Soap works | 90.1, 83.2 | 1.86–2.12 | 2.28–2.36 |
| 12 (−632, 923), Sun Mills frontage | 17.9 | 1.97–1.98 | 2.24–2.25 |
| 6, 8, 9, 24, 25, 29, 30 | 15–57 each | 2.01–2.59 | 2.27–2.69 |
| 31 (−586, 72), Short Wall | 114.0 | 2.34–2.58 | unchanged |

- The 1.65 m interpretive crests in the zone are gone. Copings now sit at the bank crest or at the yard behind.
- OS checks: the Sun Mills river-wall line reads 14.7 ft (2.25 m), drawn 2.24–2.25; the Lea towing path reads 2.07–2.34 m.
- **T2 fill measure** (T3's `measure_walls.py`, `t22/final/walls.txt`): fill within 0.5 m at 1 and 3 m 68.47 → **70.19 %**; void behind walls at 3 m 494.0 → **385.8 m**; at 6 m 766.6 → 485.1 m.
- **T3 batters:** the bank-foot frontage strips go from 42 to 23, because terrace sites without OS yard readings no longer have pads.
- **T12b clearance:**
  - span footprints are identical;
  - span-clearance lowering covers 300 → 539 network vertices (the raised banks under the Three Mills, Marshgate and Cook's Road decks);
  - approach embankments: network 6,192 → 3,221 vertices raised, 4.46 → 3.09 m max (less fill is needed now that the ground is higher);
  - approach cuttings: network 1,470 → 2,540 vertices and ground mesh 242 → 1,984 vertices lowered, 1.42 → 1.69 m max (mainly the lane connections, decision 4).
- **Water polygons are unchanged.**
- **Earth banks versus walls:** the Lea, Bow Creek and Bow back river banks without wall routes stay earth banks. They run on T11/T14's 3 m smoothstep face from the water edge to the crest, and the crest is now at the OS towing-path level. The Limehouse Cut's masonry canal faces (river-system `canalFacingRoutes`) follow the bank crest (2.17–2.3 m; OS towing path 2.28–2.37).
- **Steep edges** (rise > 2.5 m over < 3 m):
  - network 6 → 11: 5 new edges at the Marshgate Lane connection, where the raised bank meets the span-clearance ground under the 1.5 m deck (decision 4);
  - system 214 → 309: about 95 new edges along the Limehouse Cut canal faces between bed and coping. The renders show a clean wall there;
  - core 18 → 18; extension 0 → 0; ground mesh 2 → 2.
- **Not modelled as walls:** the OS "masonry river wall" along Four Mills and Sun Mills, and the Bow Bridge and Magnet wharf edges. There are no network wall routes there, so they are earth faces. Adding routes needs a river-network rebuild (decision 3).

## Bridges, approaches and railways

**Road-bridge sample refreshed** (`t22/bridge-sample.json`). No deck station changed except Three Mills Bridge.

| Bridge | Stations | Before | After | Why |
|---|---|---|---|---|
| Three Mills Lea bridge | all | 1.72–2.24 | 3.75–4.25 | Deck 2.2 → 4.23 (OS). |
| Bow Bridge east approach | 33–36 | 4.34–4.70 | 4.42–4.73 | The street (OS 22.1 ft = 4.50 at the east end) no longer sags to the cone. |
| Pegs Hole east approach | 19–22 | 2.74–2.96 | 2.94–3.04 | OS 17.4 ft = 3.07 east of the bridge. |
| St Thomas east approach | 10–12 | 2.33–2.51 | 2.48–2.54 | Raised ground. |
| St Michael's west approach | −4..−1 | 2.33–2.69 | 2.33–2.70 | Small. |
| Marshgate Lane connection (1.5 deck) | 26–29 | 1.31–1.55 | 1.48–1.59 | The lane rises away from the deck. |
| Cook's Road connection (1.5 deck) | −4..0, 29–32 | 1.01–1.47 | 1.50–1.60 | The lane rises away from the deck. |

**Decks whose approach now needs a different level** (decisions 4 and 5):

- **Marshgate Lane connection** (provisional, 1.5 m, deck or culvert unresolved): OS Marshgate Lane is 17.8 ft = 3.19 m, 17 m south of it. The lane is cut down 1.7 m to the deck.
- **Cook's Road connection** (provisional, 1.5 m): the raised bank ground around it is 2.5–3.1 m, so it now sits in a dip (render `t22-cooks-road-connection`).
- **Pegs Hole Bridge:** the OS crown is 19.1 ft = 3.59 m against the 3.0 m deck. The approaches meet the 3.0 m deck, so I did not move it.
- Bow Bridge (4.8 m; approaches 4.11 and 4.50 m by the OS) and St Thomas (2.6 m; OS 2.80 m beside it) need nothing.

**Railways** (T20 levels unchanged; `t22/final/rail.txt`):

- **G.E.R. main line** across the north-west corner of the box (chainage 270–340, formation 8.5 m): the ground under the bank rises from about 0–1.2 m to 2.0–4.0 m, so the bank is now 4.5–6.5 m high. The OS siding at its foot (15.3 ft = 2.43 m) and the bench mark at its foot (3.27 m) fit.
  - **Nothing is buried.** The rail level is unmeasured; T20 kept 8.5 m.
- **LT&SR west of Bow Creek:** the model draws only T20's 17 m approach stub (formation 5.08, hipped end). The OS line continues west through Bromley on a bank: rail 28.6 ft = 6.49 m at x −697 and 32.1 ft = 7.55 m at x −778.
  - The raised terrace now meets the stub's end at 2.6–3.3 m (30 m west) and 3.6–4.7 m (50 m west).
  - The stub is not buried, but the line beyond it is missing (decision 2).
- `check_railway_embankments.mjs` failed in one intermediate build, on an open edge of that approach, when the terrace correction reached across the zone edge. Keeping T21's correction east of x −628 fixed it.
- The North London line is not in the box.

## Flood

- **`landscape-flood-1900.json` connected land is unchanged:** 2.5 m ODN 85.10 ha, 3.5 m 111.58, 4.5 m 112.86, 5.5 m 113.84 ha. Its `.f32`/`.u8` grids are byte-identical; only input hashes changed.
  - It reads `terrain-1900.scene.f32` (the historic scaffold), which is byte-identical. The drawn ground does not reach it (T21 decision 5).
- **Supplementary indicator** (`t22/drawnflood2.py`; connected uniform stage on the drawn 4 m ground, seeded from the network tide, no barriers):

  | Area | 3.5 m ODN | 4.5 m ODN | 5.5 m ODN |
  |---|---|---|---|
  | T21's east area | 99.3 → 90.9 ha | 113.1 → 110.8 ha | 129.6 ha (unchanged) |
  | Whole box | 179.1 → 98.9 ha | 191.8 → 125.5 ha | 208.2 → 152.1 ha |

  On main, the flat-floor terrace flooded at every stage, which was an artefact.
- **1897 and 1904 accounts** (`reference/photo-review-2026-10-03/reports/flood-evidence.md`): these still read plausibly.
  - FE18 (1904, two feet down Stratford High Street, about 5.2–5.4 m ODN on the 4.0–4.8 m ODN street) and FE11 (1897, marsh roads four feet under, about 3.5–3.9 m ODN) keep their order. The High Street readings are 4.84 / 4.57 / 4.00 m ODN, the same as T21 within 0.12 m.
  - The terrace streets, at 7–11 m ODN, stand above both stages. That fits the book: neither event floods Bow or Bromley proper.
  - The west riverside yards (Four Mills 4.5 m ODN, towing paths 3.9–4.2 m ODN) lie under the 1904 stage and at the 1897 stage, consistent with "a surge over the Lower Lea banks". This is still-water reasoning only.

## Structural diffs (against `t22/base/data`, the unchanged main)

- **`main-landscape-1900.*` `.f32`:**

  | File | Changed values | Range (m) | Note |
  |---|---:|---|---|
  | `background` | 292,695 → 575,370 vertices; 3.5 → 6.9 MB | — | Terrace mesh |
  | `network` | 219,107 | −2.05..+4.53 | |
  | `system` | 10,694 | −0.95..+3.92 | |
  | `faces` | 1,341 | 0..+1.56 | Cut copings |
  | `level` | 10,664 | −4.02..+3.95 | |
  | `weight` | 9,430 | 0..+1 | |
  | `core` | 455 | −0.24..0 | Edge caps beside outside-pad buildings |
  | `extension` | 0 | — | Unchanged |

- **`main-landscape-1900.json`:**
  - `siteGround` (37 pads, `outsideIds`);
  - new `seats`/`seatMethod`;
  - `osGroundLevels`: `correctionGrid` now spans the box, with a new `correctionGridPrior`, `terraceSupport`, `terraceMeshStepMetres`, `terraceSeam`, `terraceWalls`, `marshControls` (174 readings, 370 bank crests) and street corridors for 7 more streets;
  - `roadControlIds` 23 → 43 (in the page review this shows as `streetControls`);
  - `retainingEdgeCrests` (above);
  - `edgeBatters.frontages` 42 → 23;
  - `networkTidalWater` counts and `junctionEndCaps` 2,616 → 2,731;
  - `railwaySlopes` (G.E.R. main line toes refitted to the raised ground; LT&SR approach triangles);
  - `roadBridgeClearance.pass` (above);
  - input hashes.
  - Probes (Northern Mill Meads 0.232, Abbey marsh −0.574) are unchanged.
- **`infrastructure.json`:** Three Mills Bridge only (6 paths).
- **Byte-identical:** `housing-detail.json`, `factory-yards.json`, the landscape-flood grids and `terrain-1900.*.f32`.
- **Hashes only:** `terrain-1900.json`, `river-system-1900.json`, `flood-demo-1900.json`, `drainage-connections-1900.json`, `landscape-flood-1900.json`, `wharf-cranes.json`.
- **`scene-manifest.json`:** fingerprints.
- **East of x −628 the drawn ground changed in 84 cells of 4 m, by more than 0.1 m:**
  - at Three Mills Bridge (the deck);
  - within 8 m of the zone edge, where mesh triangles span it;
  - at the east part of the pottery site 942, whose T21 marsh pad (1.55) is gone because its centre lies in the zone.

## Checks

- **`npm test` 21/21** (`t22/npmtest-final.log`). Changed assertions are described above; none was weakened.
- **Lint and Prettier** are clean on `docs/main-landscape.js`, `docs/road-bridges.js`, `scripts/check_os_ground_levels.mjs` and `scripts/check_road_bridges.mjs`.
- **Python checks** (`t22/pychecks-final.txt`): all pass except 3, which **fail identically on base `c0a7a43`**. I ran them on an exported copy of base to confirm:
  - `check_east_channelsea_context` (frozen Woolwich route, T20 decision 5);
  - `check_remaining_trades_context` ("Stratford High Street — Channelsea approach");
  - `check_three_mills_landmark_alignment` ("site256-range-1").

  The passing checks are `check_main_landscape`, `check_historic_elevation`, `check_river_system`, `check_factory_yards`, `check_factory_buildings`, `check_manor_road`, `check_east_depot_tracks`, `check_western_completion`, `check_stratford_station_rail_alignment`, `check_scene_data` and `check_district_streets`.
- **Builders deterministic:** the full cascade was run twice and all generated files are identical (`t22/final-determinism.txt`).
- Checks that write under `reference/` wrote into a private copy of `reference/topography-research-2026-09-28/terrain-epochs`.

## Renders

Before: main on 4173, `t22/before2/` (and `t22/before/` for a first camera set). After: this worktree on 4207, `t22/after-final/`. Side by side: `t22/pairs-final/*.jpg`. The cameras put the eye 1.7 m above each scene's own drawn ground, so "before" sits on the old floor. I opened every image.

| Camera | Verdict |
|---|---|
| `t22-west-overhead`, `t22-west-oblique` | No seam or artefact at this distance. The works, including Cleugh's sawtooth sheds and Berger's starch works, sit on the plateau as before. The terrace is visually flat because it is a plateau at 6–9 m. |
| `t22-box-west-edge` (120 m up over x −1280) | No visible step at the box edge. The 60 m feather is not apparent among the regional plans. |
| `t22-bow-bridge-west` | **Fixed.** Before: the High Street climbed from about 0.2 m to the 4.8 m Bow Bridge deck between the frontages. After: a level street at its OS 4.1 m runs into the bridge, and the frontages stand on it. |
| `t22-bow-bridge-east` | **Fixed.** Before: a steep climb to the deck. After: a near-level street (OS 4.50 at the bridge end) rising gently onto the deck. |
| `t22-lea-west-bank-from-water`, `-from-bridge` | The west-bank works now stand higher above the towing path. The bank is an earth face rising to the towing-path crest. The view from Three Mills Bridge is now taken from the 4.23 m deck. |
| `t22-four-mills-from-river`, `t22-sun-mills-from-river` | The yards are raised from about 0 to about 2.7 m behind the earth bank. The buildings stand on them, with no gaps. The OS stone river wall is not drawn (decision 3). |
| `t22-maltings-from-cut` | The Cut's brick faces now carry the coping at the bank crest, with level yards behind. An intermediate build (`t22/pairs-v4/`) showed tilted banks over the water; the bank-crest controls fixed it. |
| `t22-cut-match-works` | The Cut wall with the match works behind on rising ground. One small shed on the slope shows its downhill wall foot (sloping footprint). |
| `t22-pottery-petroleum-lea` | The pottery and petroleum store on the slope down to the Lea. The ground rises between the ranges. One kiln base stands on lower ground at the left. |
| `t22-cleugh-imperial-street`, `t22-cleugh-mill-from-imperial-street` | The Imperial Street terrace houses stand on their footway, now at the OS level. Cleugh's mill is hidden behind them from both cameras; see the oblique. |
| `t22-berger-powis-road` | Berger's starch works from the corner of Powis Road (OS 33.0 ft = 7.83 m). Unchanged in look; the whole scene is lifted about 7.6 m. |
| `t22-st-leonards-street`, `t22-priory-street` | The streets rise as the OS gives them (Priory Street 8.25 → 6.52 m, falling east). The footway kerbs read as thin lines. No ground steps (transect at Priory Street: smooth ±0.1 m across 28 m). |
| `t22-west-strip-street` | Unchanged in look (same camera height relative to the ground). |
| `t22-three-mills-lane-west` | Before: the lane fell to the 2.2 m deck. After: the lane runs gently down from 5.9 m onto the 4.23 m deck. |
| `t22-marshgate-connection` | The lane now rises from the 1.5 m deck to its OS level. A raised bank stands beside the deck (decision 4). |
| `t22-cooks-road-connection` | The provisional deck now sits in a dip in the raised ground (decision 4). |
| `t22-ltsr-bow-creek-west` | T20's approach mound is now lower relative to the raised ground, and Bow Creek shows in its channel to the right. The line beyond is not drawn (decision 2). |

## Smoke

`t22-terrace` against `main-before-t22`. The baseline was taken from the unchanged worktree at the start. Both were served on 4207. Log: `t22/smoke-after.log`.

**Ready, 0 page errors**, 9,043,785 triangles (+109,695), 154 draw calls. 19 differences:

1. `factoryBuildings.chimneyTops` (62 of 96), `kilns` (19), `tanks` (5): the west plant on the terrace, +0.3 to +8.2 m.
   - East of x −628: stack-568 +0.07 and kiln-942-4 +0.32 (outside-pad seats).
   - Outside the box: Howard & Sons stacks +0.05 (pad 2.69 → 2.74 from its OS yard reading) and stacks 790/939/258 −0.06 to +0.44. These sites lie in the feather band and lost their marsh pads.
2. `infrastructure.bridgeStructures.triangles` 8824 → 8820: `road-bridges.js` sizes wing footings from the drawn ground, which is now higher at the lane connections.
3. `mainLandscape.groundMeshVertices` 292,695 → 575,370; `premises` 58 → 37; `replacements.network/system` counts and ranges; `seatedObjects` 947 → 1173; `streetControls` 23 → 43.
4. `tramRails` stations 1184 → 1147, −888 triangles, `riseMetres` [0.003, 0.012] → [0.002, 0.016]: the High Street between Bow Bridge and Pegs Hole is now level on its readings instead of climbing, so fewer pieces are needed. The rails are still seated.
5. `wharfCranes.placed`: 8 cranes on raised ground (listed above).
6. `triangles` and `reflection.triangles` +109,695: the 5 m terrace mesh.

## What I did not do

- **Model the OS masonry river walls** at Four Mills and Sun Mills, and the Bow Bridge and Magnet wharves, as walls. They are earth faces, because no wall route exists there (decision 3).
- **Move the provisional lane-connection decks** (Marshgate Lane, Cook's Road) or Pegs Hole Bridge (decisions 4 and 5).
- **Draw the LT&SR through Bromley** west of Bow Creek (decision 2).
- **The Short Wall and Long Wall** (T21 decision 4): untouched. The zone stops at x −628.
- **The north-east corner by Abbey Road** (T21 decision 1): still the flat floor outside T21's patch.
- **Stepped seating** for buildings on slopes and bank faces (decision 6).
- **East seating outliers from T21** (18; decision 7).
- **Rebuild the flood grid from the drawn ground** (T21 decision 5).
- **The GeoPackage/GeoTIFF export** was not regenerated.

## What I was unsure of

- **Bank-crest controls.** The regional bank crest (OS bank-top readings interpolated along each bank) pins the ground 4 m inland, every 15 m, where no reading is near. Where works stand on high ground right at a bank (the match works on the Cut), this pulls their ground down towards the bank. The 15 m clearance from readings and the street and bridge exclusions limit this, but the rule is mine.
- **The Gaussian-process length (40 m)** shapes the slope between terrace and river as a smooth ramp, not the OS hatched bank. I did not trace the hatching.
- **The 60 m feather outside the box** is a ramp from the terrace down to the flat floor. It is invisible in the renders, but it is not evidence.
- **Unpadding terrace sites.** The terrace sites without OS yard readings lost their flat T21 pads (for example 942 at 1.55, 939 at 0.85). Their ground now follows the corrected terrace, which may be less level than a real yard.
- **The 5 m mesh** doubles the background file (3.5 → 6.9 MB).

## Decisions for the reviewer and the author

1. **Terrace zone edge at x −628.**
   - *Choice:* T21's west strip, so that T21's ground east of it is kept exactly.
   - *Alternative:* follow the Lea's west bank line, which would include the strip of land west of the Lea at x −628..−600, near Three Mills, that T21 drew as marsh.
2. **LT&SR west of Bow Creek** (OS rail 6.49–7.55 m through Bromley).
   - *Choice:* not drawn; T20's 17 m stub kept.
   - *Alternative:* a task to extend the line west on its OS bank, now that the ground beside it is right.
3. **River walls at Four Mills, Sun Mills and the Bow wharves.**
   - *Choice:* earth faces at the OS crest.
   - *Alternative:* add wall routes in the river network (`build_river_network.py` and the T14 band mesh), so that the wharf walls stand at their OS wall-top readings (14.7–16.8 ft).
4. **Provisional lane-connection decks** (Marshgate Lane, Cook's Road; 1.5 m estimates; deck or culvert unresolved).
   - *Choice:* kept, because no OS reading exists on them. The approaches now rise away from them, and Marshgate Lane is cut 1.7 m below its OS level 17 m away.
   - *Alternative:* raise both to about 2.8–3.1 m (the OS lane and bank levels), or draw them as culverts at road level.
5. **Pegs Hole Bridge.**
   - *Choice:* the 3.0 m deck kept.
   - *Alternative:* raise it to its OS crown, 19.1 ft = 3.59 m, which the OS reading would support. That would put a 0.5 m hump on the High Street and move the tram rails.
6. **Sloping footprints.**
   - *Choice:* one seat per object (the median drawn ground).
   - *Alternative:* stepped plinths or per-range splits on slopes. 66 west objects have a corner more than 0.6 m above the ground, and 32 have ground more than 0.6 m above their seat.
7. **East seating outliers (T21-era, 18 objects).**
   - *Choice:* left as they are.
   - *Alternative:* seat them by the same median-ground rule. That is a one-line extension of the `seats` selection.
8. **Three Mills Bridge re-levelled to the OS 4.23 m.**
   - *Alternative:* keep 2.2 m. The lane would then fall 2.8 m in a cutting.
   - The east end still stops 25 m short of the drawn water (T21 decision 3).

## Regeneration on main after merging

Generated files in this branch are cascaded (commit `5fabc71`). If main moves, run in this order:

1. `python3 scripts/prepare_os_ground_levels.py` (only if the spot heights or `ground-plan`/`infrastructure` change).
2. `python3 scripts/build_infrastructure.py`, then `(cd scripts && python3 build_housing_detail.py)`, repeating until stable.
3. `build_historic_elevation.py`, `build_river_system.py`, `build_main_landscape.py` (about 7 minutes).
4. `build_flood_demo.py`, `build_landscape_flood.py`, `build_factory_yards.py`, `build_drainage_connections.py`, `build_flood_demo.py`, `build_wharf_cranes.py`, `build_scene_manifest.py`.
5. `node scripts/check_road_bridges.mjs --write-sample` if the sample differs.

## Files

- **Changed (sources):**
  - `data/maps/os-ground-levels.json`
  - `data/maps/district-road-traces.json`
  - `data/maps/remaining-trades-context-alignment.json`
  - `data/maps/road-bridge-forms.json`
  - `scripts/prepare_os_ground_levels.py`
  - `scripts/os_ground_levels.py`
  - `scripts/build_main_landscape.py`
  - `docs/main-landscape.js`
  - `docs/road-bridges.js`
  - `scripts/check_os_ground_levels.mjs`
  - `scripts/check_road_bridges.mjs`
  - `scripts/check_remaining_trades_context.py`
- **Regenerated:**
  - `docs/data/main-landscape-1900.json/.background/.core/.faces/.level/.network/.system/.weight.f32`
  - `infrastructure.json`
  - `terrain-1900.json`
  - `river-system-1900.json`
  - `landscape-flood-1900.json`
  - `flood-demo-1900.json`
  - `drainage-connections-1900.json`
  - `wharf-cranes.json`
  - `docs/scene-manifest.json`
- **New:** `T22_REPORT.md`.
