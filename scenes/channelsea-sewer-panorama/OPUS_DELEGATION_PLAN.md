# Delegating the 3D modelling to Opus: trial plan and review protocol

3 October 2026. Written for a fresh session. Purpose: hand the remaining landscape fixes and one full site-modelling job to Opus 5.5 agents, one at a time, and judge from the results whether Opus can be relied on for the 3D modelling work going forward.

## Where the project stands

Repository: `/home/jic823/book_website`, branch `main`, clean at commit `bf063a6`. Everything below is committed. Local, git-ignored reports from today's agents are in `reference/photo-review-2026-10-03/reports/`:

| Report | What it holds |
|---|---|
| `elevation-numeric.md` / `.json` | Root causes of the elevation seams, a ten-item fix list, ten check cameras |
| `elevation-seams.md` / `.json` | 95 visual findings in 12 issues from 119 renders, with cameras to re-check after fixes |
| `site-924-proposal.md` / `.json` | The Bromley gasworks proposal, since integrated and committed |
| `photo-catalogue.md` / `.json` | 68 reference images catalogued; four in scope |
| `flood-evidence.md` / `.json` | 25 flood accounts from the book; 1897 and 1904 are the plausibility checks |
| `footprint-gaps-started-zones.json` | Footprints without models, by site |

Rendered views for comparison: `views-seams/` (the 119-camera sweep before any fix), `views-numeric-before/`, `views-numeric-after2/` and `views-fixcheck/` (after the renderer fixes).

Verification harness, all committed:

```sh
python3 -m http.server 4173 --bind 127.0.0.1 --directory docs   # serve first, keep running
npm test                                                          # 13 of 15 pass; the two flood checks fail on a known stale hash
python3 scripts/review_smoke.py <label> --compare drawn-ground    # headless diagnostic snapshot; 'drawn-ground' is the current baseline
python3 scripts/render_views.py <cameras.json> --out=<dir>        # PNGs for a camera list; about 40 s a view after a 5 min scene load
python3 scripts/footprint_gap_audit.py                            # footprint coverage, started zones
python3 scripts/export_geopackage.py --verify                     # regenerate after model changes
```

Camera lists: `reference/photo-review-2026-10-03/cameras-seams.json` (128, unique labels), `cameras-numeric-checks.json` (10), `cameras-fixcheck.json` (6). The agents' own re-check cameras are inside their JSON reports.

## How today's agents performed

Four audit agents and one proposal agent ran today on Opus, read-only, 230,000 to 345,000 tokens each, 10 to 26 minutes each.

- **Accurate and useful.** The numeric agent found that every new cliff traces to four rules in the landscape builder, corrected two of the parent's own misattributions, and quantified the wall voids. The visual agent found 95 defects, caught a camera-label bug in the parent's tooling, and gave corrected cameras for the author's screenshots. The flood agent matched every quotation to the PDF text.
- **The one proposal integrated cleanly.** The Bromley proposal followed the builder's record schema closely enough to paste in with two mechanical adaptations (strip a `proposal` key, add an empty `groups` list the builder expects). The rebuild changed only site 924 and passed the builder's own water and overlap assertions.
- **Gaps.** Agents could not render or run browsers, so they could not verify their own visual claims. The proposal needed the parent to make seven small judgement calls (eaves heights, storeys). Two agents wrote to the same scratch directory and one overwrote the other's file.

So far Opus has been trusted to read and propose, never to edit. The trial below lets it edit, in isolation, and measures the result.

## Trial design

Six tasks, run **one at a time**, each in its own git worktree (`Agent` tool with `isolation: "worktree"`, `model: "opus"`), so the shared checkout is never touched. The agent commits on its branch and writes a short report. The parent reviews, verifies and merges or rejects. Keep the session budget in mind: one agent at a time, no more, and pause if usage passes about 60 percent of the five-hour limit.

Every brief carries the same rules: the project standard (realistic, not exact; evidence recorded separately from interpretation; no photograph as a texture); the scene frame (x east, z south, y up, metres from E538900 N183209); the exact files it may change; the acceptance criteria; the commands it must run before reporting; and the instruction to stop and report rather than widen scope if something unexpected appears.

### T1. Sewer deck spans bare ground

Problem: `scripts/build_panorama_data.py` removes the sewer's earth banks inside a 79 m circle around the origin and wherever the GIS marks water, so the deck floats over flat land with daylight beneath (21 sweep views, issue I3 in `elevation-seams.md`).

Files: `scripts/build_panorama_data.py` (bank clipping only), `docs/data/ground-plan.json` (regenerated `neighbourhood.sewer.banks` and nothing else, patched in place because a full rebuild re-splits terrace rows), `scripts/build_infrastructure.py` and `docs/data/infrastructure.json` if the sewer bank triangles there must follow, `docs/sewer-crossing.js` for abutments at the water edges.

Acceptance: banks reach to within 6 m of rendered water at the Channelsea and at every other water crossing of the sewer; abutments or piers close the remaining gap; the High Street crossing unchanged; `check_sewer_crossing.mjs` and `check_sewer_high_street.mjs` pass; a structural diff of the two JSON files shows no change outside the sewer arrays; re-render `sewer-toe-6s`, `sewer-toe-7s`, `author-1-corrected` and the three bridge cameras in `cameras-fixcheck.json` and confirm no daylight under the deck over land.

### T2. Retaining walls with fill behind them

Problem: wall crests are weighted from a sample at the water's edge and saw-tooth; the ground 1 m behind the wall is more than 0.5 m below the crest along the whole 2,092 m.

Files: `scripts/build_main_landscape.py` (wall crest weight and a land-side berm 0 to 6 m wide), regenerated `docs/data/main-landscape-1900.*`.

Acceptance: ground within 0.5 m of the crest at 1 m and 3 m behind the wall on at least 95 percent of wall length; adjacent crest jumps under 0.1 m; `check_main_landscape.mjs` and `.py` pass with their count assertions updated only where the change explains them; re-render `05-route14-wall-trough` from `cameras-numeric-checks.json` and the visual agent's wall cameras; the author's second screenshot problem gone at the suggested camera position (−555, 2.5, 760) target (−600, 2, 660).

### T3. Yard edges and road corridors

Problem: site levels and street levels are applied inside outlines with no slopes, producing vertical faces (702 of 776 new steps) and a trench between bank foot and yard edge at Bromley; Abbey Lane is a plateau with 2.5 m vertical sides and a bridge deck below both approaches.

Files: `scripts/build_main_landscape.py` (`base()`, `surface()`, `road_levels()`), regenerated landscape data; optionally `docs/data/infrastructure.json` deck height for `abbey-mill-crossing` with evidence.

Acceptance: no yard-edge or corridor step over 2.5 m rise across under 3 m anywhere in the river-network or extension meshes (the numeric agent's measurement, repeatable from its JSON); no trench below −0.3 m between bank foot and yard edge at Bromley; re-render `00`, `01`, `02`, `03`, `06`, `07` from `cameras-numeric-checks.json`.

### T4. Shore-edge rule and junction end caps

Problem: one builder rule lifts bank vertices near water to full crest everywhere, creating 367 cliffs on the Hackney Cut and lifting river-network end-cap triangles into river-system water, which shows as fins at junctions.

Files: `scripts/build_main_landscape.py` (apply the rule only near recorded masonry), `scripts/river_bank_sections.py` or the river-network build for end caps inside river-system water, regenerated data.

Acceptance: fins no higher than before (at most 1.56 m above water); zero network bank triangles over system water polygons; Hackney Cut cliffs removed where the policy records earth banks; re-render `08-hackney-cut-lip-cliff`, `09-old-lea-junction-fin`, `connection-bow-locks`, `connection-three-mills`, and the author's third-screenshot camera (−612, 2.5, 872) target (−582, 0.5, 846).

### T5. Regional water plane extents

Problem: the regional river system's static water is opaque pale blue with hard rectangular edges and a straight seam against the reflective network water; one rectangle sticks out of the Lea at Bromley.

Files: `scripts/build_river_system.py` and `docs/data/river-system-1900.json` (water polygons clipped to channels and trimmed where network water already exists), `docs/river-system.js` only if the material needs to match.

Acceptance: no regional water polygon extends beyond its reach's bank lines by more than 1 m; no overlap with network water; re-render `lea-west-bank-along-800`, `lea-west-bank-along-900` and the `views-test/bromley` overhead.

### T6. A complete site, end to end: Leather Cloth Works, site 865

Problem: 43 footprints, 7,521 m², without models; the largest remaining industrial gap. This task tests modelling, not repair: the agent proposes and implements.

Files: a new `data/maps/leather-cloth-footprint-alignment.json` register (follow `bromley-gasworks-footprint-alignment.json`), its line in `scripts/build_factory_buildings.py`, regenerated `docs/data/factory-buildings.json`, and nothing else.

Acceptance: structural diff of `factory-buildings.json` confined to site 865; every added building carries footprint, height and roof evidence strings that state what is mapped and what is estimated; the builder's water and overlap assertions pass; `npm test` unchanged; smoke snapshot shows only site-865 diagnostics changing; the agent renders nothing (parent renders a site overhead and two low views and judges plausibility against the OS mosaic).

## Review protocol for each task

1. **Diff review.** Only the permitted files changed. Structural JSON diffs confined to the stated arrays or site. No invented sources; every new evidence string distinguishes mapped from estimated. No change to the bank policy or vertical reference without saying so.
2. **Checks.** `npm test` at the same pass count as before, or better, with any changed count assertion explained in the report.
3. **Snapshot.** `review_smoke.py <task> --compare <previous>`: no page errors; diagnostic differences all explained by the task.
4. **Renders.** The task's named cameras before and after, viewed side by side; the problem gone and nothing new broken in frame.
5. **Numeric re-audit** where the task has one: the step counts, wall-void length, overlap areas or coverage figures from the agent reports, recomputed.
6. **Report quality.** Did the agent say what it did not do, what it was unsure of, and what the parent should decide?

Record each task's outcome in the table below as merged, merged with parent edits, or rejected, with the number of parent interventions.

## Decision rule

Opus can be relied on for the 3D modelling if at least four of the six tasks merge with no more than minor parent edits, no task introduces a regression that the checks or renders catch after merge, and the evidence strings in T6 survive a reading against the OS without correction. If the audits are reliable but implementations need substantial parent repair, keep Opus for audits and proposals and have the parent or Astra implement. Either outcome is a useful answer; record it in this file.

## Outcomes

| Task | Agent tokens | Outcome | Parent interventions | Notes |
|---|---|---|---|---|
| T1 | 314k, 69 min | merged | 0 edits; 1 scope extension accepted | Banks now stop 1.5 m from drawn water at all 4 crossings, brick end walls close them, Channelsea abutments moved to the real bank ends. Agent added two keys (`bankEnds`, `bankEndsEvidence`) beyond the stated arrays, justified. Found that GIS rivers were the wrong clipping basis and used the drawn water instead. Correctly identified sewer-toe-6s as an Abbey Lane road-opening wedge outside its scope (follow-up). Rendered and inspected its own views. Open: Mill Mead path (x≈−37) now buried under 44 m of bank; stale `infrastructure.json` hashes in 6 derived files; no piers at the 3 non-Channelsea crossings. |
| T2 | | | | |
| T3 | | | | |
| T4 | | | | |
| T5 | 233k, 81 min | merged | 0 edits; premise correction accepted | Agent showed the brief was partly wrong: no regional polygon overshot its banks, and the Bromley "rectangle" is the real Limehouse Cut head drawn in an opaque pale material. Fixed by sharing the network water material and trimming 588.6 m² of overlap with network water at 9 junctions (now 0). Two new builder assertions. Renders confirm the seams gone and water reflective. Open: hash cascade (`river-system-1900.json` hash stored in elevation-audit, elevation-trial, main-landscape, lower-lea landscape), and the river system must be rebuilt after T1 and T6 change `ground-plan.json` and `factory-buildings.json`; geopackage export not regenerated. |
| T6 | | | | |

## Also pending, not part of the trial

- From T1: the Abbey Lane and Mill Meads works road openings through the sewer bank still end in open wedges (sewer-toe-6s); extend the end walls there, which needs `build_panorama_data.py` to read road routes or an `app.js` change. Decide whether the Mill Mead riverbank path gets an opening through the extended bank. `review_smoke.py` times out at its 60 s wait even on base files; lengthen the wait.

- Re-render the 14 railway sweep views lost to the label collision (`cameras-seams.json` now has unique labels).
- Road names: the eastern "Warton Road" is probably West Ham Lane; the model's "Angel Lane" is misplaced; the High Street lacks tram rails (horse trams, no wires, correct for 1900).
- Retort-house re-registration at Bromley (moves 24 flues and the boiler stack).
- Flood plausibility runs against the 1897 and 1904 accounts once the landscape fixes land.
- Astra's two flood checks fail on a stale terrain hash until the flood field is rebuilt.
- `docs2/` still needs deleting by the author.
