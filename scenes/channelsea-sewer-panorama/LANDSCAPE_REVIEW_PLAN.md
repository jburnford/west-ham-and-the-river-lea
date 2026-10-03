# Landscape review and completion plan

3 October 2026. Reviewing the started areas of the West Ham reconstruction with Opus agents: repair the gaps left by the elevation integration, find buildings that do not match the 1891–96 footprints or are missing, and add them. The rest of West Ham follows later under a separate plan.

## Scope and standard

**Area.** The "started zones": every registered industrial site plus a 60 m neighbourhood around every modelled building. That is 2.06 km² covering the Channelsea, Abbey Mills, Mill Meads, Stratford High Street, Marshgate Lane, Sugar House Lane, Three Mills, both gasworks, the eastern strip to the Woolwich railway and the northern streets.

**Standard.** Realistic, not exact. The author's stated aim is an approximate but convincing circa-1900 landscape. Every change records map evidence separately from interpreted elevations. No archive photograph is displayed or used as a texture; the reference photographs guide materials, storeys, roof forms and street character only.

**Flood work.** The elevation integration was done so floods can be simulated, and it is not finished. The goal there is also realism, not engineering accuracy: there are no exact historical flood level records. The evidence is the photographs the author has gathered and the newspaper accounts of flood coverage in the book. Those are plausibility checks on the simulation, not calibration targets.

## What the measurements say today

Two audits were run on 3 October and their outputs are in `reference/photo-review-2026-10-03/` (local, ignored by git).

**Footprints without models** (`footprint-gaps-started-zones.json`). Of 36,938 footprints from the author's 1891–96 GeoPackage inside the district window, 7,290 lie in the started zones with less than 30 % model coverage, totalling 211,014 m². By size: 28 over 400 m², 179 between 100 and 400 m², 3,037 between 25 and 100 m², 4,046 under 25 m². The small ones are mostly outbuildings behind housing rows and will largely be judged acceptable. Registered sites with the most missing floor area:

| Site | Missing footprints | Missing m² |
|---|---|---|
| 924 Gas Works (Bromley) | 173 | 9,026 |
| 865 Leather Cloth Works | 43 | 7,521 |
| 258 Brush and Mat Manufactory | 13 | 2,221 |
| 1018 Manure Works | 2 | 1,564 |
| 514 Imperial Spinning Mills | 13 | 1,434 |
| 873 West Ham Gas Works | 54 | 1,170 |
| 398 Chemical Works | 28 | 1,118 |
| 419 Three Mills Distillery | 28 | 829 |
| 510 City of London Match Works | 12 | 492 |
| 796 East London Soap Works | 9 | 480 |
| 260 Howard & Sons | 40 | 450 |
| 230 Imperial Works | 18 | 397 |
| 792 Mineral Water Manufactory | 5 | 347 |

Outside industrial sites: 6,598 footprints and 180,041 m², which is where missing housing rows, chapels, pubs, schools and shops will be found. The 207 missing footprints of 100 m² or more are the first list to work through.

**Models without footprints.** 35 factory ranges, 9 High Street frontages, 70 housing rows and 3 gas holders have under 30 % footprint support. The holders (Bromley 9, West Ham OS 5) may post-date the 1891–96 survey, which is a dating question rather than an error. The 3,610 generated rear extensions and privies are interpretive by design.

**Elevation seams** (numerical scan of the main-landscape height files against their predecessors):

- The river-network mesh gained 799 near-vertical steps (more than 2.5 m rise across under 3 m). None existed before. They cluster along the west bank of the Lea between Three Mills and Bromley gasworks, scene x −700 to −600, z 600 to 1,300, with a smaller group at x −1,100, z −700.
- The historic extension mesh has 79 triangles rising more than 3 m across 3 m edges, at a 3.0 m bank crest meeting −0.54 m marsh around x −149, z 449.
- The detailed 0.4 m tile has 35 % more neighbour steps over 0.8 m than before. Its edges still meet the network mesh within 0.2 m, so the tile boundary is not the problem.
- The author's second screenshot, beside the Bromley holders looking north-west along the river, shows a brick retaining wall standing free with nothing behind it: the crest follows the new bank profile while the marsh ground behind has dropped, leaving the wall as a thin slab above a void. Retaining walls need fill behind them. Either the land-side ground is lifted to the crest within a berm of a few metres along every `retainingEdges` route, or `river-network.js` adds a fill wedge from crest to ground behind each wall. The same crest-against-marsh step explains the 3.0 m against −0.54 m cliffs in the extension mesh.
- The author's third screenshot, at a junction where an extended reach meets an original channel, shows angular bank fins: the bank sections of the extension wrap the end cap of the original channel polygon and stand as pointed wedges over the water, with the new reach's water sitting inside a sleeve of bank. The join between the core river network and the regional river system needs its end caps removed where a channel continues, and the two bank sections merged into one profile across the junction. The relevant code is `scripts/river_bank_sections.py` and the crossings recorded in `river-system-1900.json`.
- The author's fourth screenshot, looking north along a channel towards the railway, shows the regional landscape as it stands: one flat green surface, a plain embankment with two iron decks on brick abutments, and nothing else. Moving north the scene reads as unfinished. Part of that is correct history, since the valley north of Stratford High Street was still marsh, allotments and railway land in 1900, but it needs to read as open marsh rather than as an empty render. This is a context problem, not a seam, and it gets its own workstream below.
- The author's first screenshot from the sewer bridge shows a sheared ground slab crossing the river, grass tufts floating in mid-air and a stepped bank face. None of the scans explains the slab, which points at geometry built from the ground sampler after the ground moved: bridge-approach fill triangles, the scaled sewer banks, or vegetation and clods placed from one sampler while the drawn ground comes from another. This needs a visual sweep.

## Workstreams

Agents are launched with the Agent tool on the Opus model, in the background, each with a bounded brief, an explicit file list and a report path under `reference/photo-review-2026-10-03/reports/`. Agents read and propose; only the parent session edits data, rebuilds, verifies and commits. At most one headless browser runs at a time, so the rendering agent has exclusive browser use and the others are file-only.

### W0. Tooling the agents need (parent, first)

- Turn today's ad-hoc audit into `scripts/footprint_gap_audit.py` writing both the district-window and started-zone reports, with the footprint `sourceFid` carried through (today's run dropped it).
- `scripts/render_views.py`: take a JSON list of cameras (position, target, fov, label) and write PNGs through the existing `?river-review` renderer, so agents can request views without driving a browser themselves.
- `docs/scene-audit.js` (optional, for W2): in `?export=1` mode, record the placement of every small ground object before batching and raycast each one against the ground layer, reporting the gap. This is how floating tufts and clods are found numerically rather than by eye.
- Commit the three.

### W1. Reference photograph catalogue (one agent, vision)

Input: the 67 screenshots in `reference/photo-review-2026-10-03/`. For each: subject, street or site, approximate date, visible source or credit, whether it falls inside the started zones, which model elements it informs (wall material, storeys, roof form, chimneys, shopfronts, street furniture, water edge) and a reminder that it is reference only. Output `photo-catalogue.json` and a short markdown summary grouping photographs by site. Several will be outside scope (Boleyn Tavern on Barking Road, Green Street in Upton Park, the 1786 marsh view); the catalogue says so and keeps them for the later West Ham plan.

### W2. Elevation seam sweep (two agents, sequential browser use)

Agent A, visual: reproduce the author's four screenshots first (sewer bridge slab, free-standing wall by the Bromley holders, junction fins where a reach was extended, the bare northern view), then sweep about 40 low viewpoints along the Channelsea, Abbey Creek, the Lea west bank hotspots, the sewer and its bank toes, each road bridge approach, and each railway toe. Log every artifact with camera, description, severity and suspected mesh. Output `elevation-seams.json` with cameras that reproduce each one.

Agent B, numerical: classify the 799 network steps and 79 extension cliffs as intended bank or artifact against the continuous-bank policy in `data/maps/lower-lea-region/continuous-embankments-1900.json` and the retaining-edge crests in `main-landscape-1900.json`; run the scene-audit raycast and list floating or buried objects by layer. Output `elevation-numeric.json`.

Parent: merge the two into a fix list per cause (fill behind retaining walls, channel-junction end caps where the extended reaches meet the original channels, bank profile smoothing, bridge fill rebuilt from the final ground, sewer bank scaling, object seating). The retaining-wall fill is already a confirmed item and can start before the sweep finishes. Fixes to Astra's elevation modules are coordinated with Astra; fixes to seating and fills are parent work.

### W3. Building audit and additions, site by site (one agent per site cluster)

Order by missing area: 924 Gas Works, 865 Leather Cloth Works, 258 Brush and Mat, 1018 Manure Works, 514 Imperial Spinning Mills, 398 Chemical Works, 419 Three Mills Distillery, 510 Match Works, 796 Soap Works, 260 Howard & Sons, 230 Imperial Works, 792 Mineral Water, then West Ham Gas Works 873, whose fifteen remaining ranges Astra had paused. Then the non-industrial list: the 207 missing footprints over 100 m², classified as missing rows, public buildings or shops.

Each agent receives: the site's entries from the gap audit, the site's existing register (`data/maps/*-footprint-alignment.json`), the existing cached OS five-foot mosaic crops under `reference/`, any Goad coverage already recorded, and the photo catalogue entries for that site. It returns: proposed register additions (world footprint from the source polygon, eaves height, storeys, roof form and material as explicit estimates with evidence strings), proposed deletions or adjustments of unsupported ranges, and open questions. It does not edit files.

Parent: apply each proposal through the existing register and `build_factory_buildings.py`, rebuild, run `npm test`, run the smoke snapshot, render the site's review views, and commit one site at a time.

### W4. Flood plausibility evidence (one agent, reading)

Read the book's flood passages (the PDF is in the repository root; Chapter 2 and the drainage sections of Chapters 3 and 5 are the likely places) and the gathered photographs for flood scenes. Produce `flood-evidence.json`: each account with date, streets or works named, described depth or extent, and the source. The parent then runs the landscape-flood tool at levels that reproduce each account's extent and records whether the named streets flood and the dry ones stay dry. Disagreements become either a terrain fix or a note that the evidence is ambiguous. No claim of calibrated accuracy is made.

### W5. Northern and regional context (one agent, maps, then parent)

The regional ground beyond the started zones is a single flat material. In 1900 the land north of the High Street was Stratford and Hackney marsh, allotments, osier beds and the Temple Mills railway lands, with Carpenters Road's industrial strip along the Lea. The agent reads the six-inch and five-foot OS sheets for the area north to Lea Bridge and returns a context plan: ditch and drain lines, field boundaries and hedgerows, osier and allotment areas, tree groups from the OS symbols, the Temple Mills sidings extent, and the Carpenters Road frontage as a list of footprints with estimated heights. It also marks the stage boundary: how far north the detailed treatment should extend before the regional building-plan planes take over.

Parent: give the regional ground a marsh treatment driven by that plan (ditch lines cut into the land material, field-boundary texture variation, tree groups placed from the mapped symbols), put proper wing walls and parapets on the railway crossings, and fade the regional footprint planes in at the stage boundary rather than leaving a hard edge. Heights north of the boundary stay provisional and are labelled so in the evidence notes. This is the first step of the later plan for the rest of West Ham, so its outputs are written to be extended.

## Sequence

1. W0 tooling, then W1 and W2 start together; W4 and the W5 map reading start in parallel because they only read.
2. W3 begins with the three largest sites while W2 runs, since it needs maps more than photographs. Later sites use the W1 catalogue.
3. Elevation fixes land before building additions in the same area, so new buildings seat on final ground.
4. Each completed site or fix is a separate commit with its own smoke comparison and review screenshots.

## Done when

- The author's screenshot view and the 40 sweep views show no floating objects, sheared slabs or unintended cliffs.
- Every registered site in the table above has either modelled ranges for its footprints of 100 m² or more, or a recorded reason not to.
- The 207 large non-industrial footprints are each modelled, deferred with a reason, or shown to be already covered.
- Flood evidence from the book is recorded and each account has been compared with the simulation once.
- Looking north from the High Street reads as 1900 marsh and railway land, with a deliberate stage boundary, not as empty ground.
- The GeoPackage and glTF exports are regenerated.
