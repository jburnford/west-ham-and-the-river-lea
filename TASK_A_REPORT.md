# Task A report: bridge decks, the LT&SR west of Bow Creek, and the river walls (5 October 2026)

This work was done directly in the parent session, not by a delegated agent. Branch `task-a-decks-walls` (worktree `../book_website-taska`), from main `25701a7`. It follows the author's rule "follow the maps". It covers T22's decisions 2, 3, 4 and 5.

## Summary

- **Pegs Hole Bridge** now carries the High Street at its OS crown, 19.1 ft = **3.59 m** (was 3.0 m). The street rises to it from its OS levels on either side: 2.65 m 45 m west and 3.07 m 44 m east.
- **Marshgate Lane connection deck:** **2.93 m** (was 1.5 m). The lane has no OS reading on the crossing itself, so the deck takes the lane level the OS gives either side: 2.65 m at the High Street corner and 3.19 m 17 m beyond the deck, interpolated along the lane.
- **Cook's Road connection deck:** **2.8 m** (was 1.5 m). The lane has no OS reading, so this is the drawn terrace level at the lane's east end and beside the deck ends (2.4–2.9 m).
- **LT&SR west of Bow Creek** is drawn for the first time. It runs 227 m from the end of T20's approach to the St Leonard's Street bridge. It is traced on the OS rails and levelled on two OS rail readings (28.6 ft and 32.1 ft).
- **River walls:** the OS masonry walls at **Sun Mills** (108 m) and **Four Mills** (78 m) are now retaining-wall routes on the drawn shoreline, drawn as brick walls.
  - Their copings meet the OS wall-top readings: Four Mills 2.89 m against 16.8 ft = 2.89 m, and Sun Mills 2.32 m against 14.7 ft = 2.25 m.
  - The **Bow Bridge and Magnet wharves** are not done (see below).
- `npm test`: **21 of 21** (see the end of this report).

## Decks

The deck heights live in `data/maps/district-road-traces.json`, with a copy for Marshgate Lane in `remaining-trades-context-alignment.json`. Each change keeps the old value as `priorHeight`, with a `heightEvidence` note.

The source note in `road-bridge-forms.json` and its copy in `docs/road-bridges.js` now lists these re-levels alongside T22's Three Mills Bridge.

| Bridge | Deck before | Deck after | Basis |
|---|---:|---:|---|
| Pegs Hole | 3.0 | 3.59 | OS crown 19.1 ft (`sh_538117_183327`); parapet bench mark 20.61 ft = 4.05 m |
| Marshgate Lane connection | 1.5 | 2.93 | Interpolated from the OS lane levels either side (`sh_538078_183283`, `sh_538054_183338`) |
| Cook's Road connection | 1.5 | 2.8 | No OS reading on the lane; the drawn terrace beside it |

In the road-bridge check, the sample rows changed only for these three bridges: by +0.59, +1.43 and +1.30 m. I refreshed the sample (`check_road_bridges.mjs`).

**Marshgate Lane is still low between its OS readings.**

- The deck and its approaches now meet. Before, the lane was cut 1.7 m down to the deck.
- Between the OS reading 17 m south of the deck (3.19 m) and the next OS lane level at the St Thomas's Mills corner (2.80 m, 58 m on), the drawn lane falls to the terrace ground under it, 1.2–1.4 m.
- It did this before task A as well (T22's sample: 1.1–1.8 m there). T22 put the miss down to the deck cutting, but the deck was not the cause.
- At the reading the miss is now −1.54 m, against −1.7 m before. The reading stays a listed exception in `prepare_os_ground_levels.py`, with the corrected reason.
- **Likely cause, not proven:** the T22 terrace correction works per dry compartment of the river mask, and the lane runs 2.5 m beside a channel. The street readings do not carry along the lane between readings.
- This is the next fundamentals fix for that lane (render `t22-marshgate-connection`: the camera stands in the low stretch).

## LT&SR west of Bow Creek

**A separate record, not a longer route.** The line is a register-added railway, *London, Tilbury and Southend Railway, west of Bow Creek*, in `data/maps/railway-levels.json` (`addedRoute: true`). Every chainage on the main LT&SR route stays as it was: the Bow Creek bridge, the controls, Manor Road and the Abbey Mills junction. `railway_levels.added_railways()` feeds it to `build_infrastructure.py` as a plain railway. It starts exactly where the main route's west approach ends (station −16.8), square-ended. The approach no longer gets its earth end.

**Route.** I traced it on the five-foot plan at zoom 18. Four rails, two running lines, read on cross-sections:

| x | OS centreline z |
|---:|---:|
| −605 | 602.5 |
| −700 | 641.8 |
| −770 | 669.8 |
| −800 | 681.0 |
| −855 | 697.0 |

- The main route's first segment, which the Bow Creek bridge follows, lies about 3 m south of the OS centreline at the creek.
- The new route keeps that heading for 15 m and joins the OS centreline by x −700.
- It ends at x −834, 3 m short of the St Leonard's Street kerb line.

**Levels**

| Chainage | Formation | Basis |
|---:|---:|---|
| 0 | 5.08 | Level with the approach (the main route's west-end control, 25.5 ft) |
| 78.6 | 6.03 | `sh_538203_182575`, rail 28.6 ft |
| 166.3 | 7.09 | `sh_538122_182541`, rail 32.1 ft |
| 227.3 | 7.09 | Held level; no reading (interpretation) |

- Grades are about 1 in 83.
- The bench mark on the Steam Boiler Works boundary (25.75 ft) is recorded as a check.
- `check_railway_levels.mjs` meets both controls.

**On the ground**

- The bank stands about 4 m above the drawn ground at the creek. It falls to nothing by chainage 75 (x ≈ −690), which matches the OS hatching on the north side from the creek to the boiler works.
- Further west the formation stands 0.05–0.15 m above T22's terrace. The OS draws no hatching there.
- No building is held off and nothing is buried.

**Registers**

- `railway-bridge-forms.json` (and its copy in `docs/railway-bridges.js`) has an updated `london-tilbury-and-southend-west` line end and a new `london-tilbury-and-southend-bromley` end.
- The open-edge test in `check_railway_embankments.mjs` now treats an added route's embankment as continuing the line it starts from. Without that, the meeting cross-section would read as an open box end.

**Not drawn:** St Leonard's Street, its bridge over the line (deck 47.3 ft on hatched ramps) and Bromley Station. The line stops short of the street.

## River walls

**How the walls are built.**

- New register: `data/maps/os-river-walls.json`, with OS-traced lines, wall-top readings, evidence and the cases not modelled.
- `build_river_network.py` makes the drawn shoreline within 4.5 m of each line a retaining-wall route, as T14's routes are made.
- The new routes are appended (indices 32–34), so the existing route numbers are unchanged. They are recorded under `retainingEdges.osRiverWalls`.
- The network mesh files are byte-identical, because the shoreline already had its edges. Only `river-network.json` changed.
- The copings come from T22's terrace-wall rule, not from a new rule.

**Sun Mills:** a continuous double line on the OS from the Tidal Lock to the mud basin south of the mill. 107.8 m of the 124 m traced became walls. The north end beside the Tidal Lock is already T14's route 12.

**Four Mills:**

- A coursed masonry band about 4 m wide along the distillery frontage; 77.5 m of 77.2 m traced became walls.
- The band's width suggests a battered face or an apron. The model draws a vertical wall.

**Not done: the Bow Bridge and Magnet wharves.** The drawn water there does not follow the OS banks: the GIS channel south-east of Bow Bridge crosses mapped buildings. A wall on that shoreline would stand off the real edge, so the water outline needs retracing first. Recorded in the register's `notModelled`.

## Renders

There are 13 cameras: T22's views at Marshgate, Cook's Road, Four Mills, Sun Mills, the LT&SR at Bow Creek, St Leonard's Street, the west oblique and Bow Bridge east, plus five new ones. The before/after pairs are in the session scratchpad (`pairs/`).

| View | What changed |
|---|---|
| `a-pegshole-west` | The High Street rises gently to the bridge crown. The tram rails follow. |
| `t22-cooks-road-connection` | The deck and railings now sit level with the raised ground, not in a dip. |
| `t22-marshgate-connection` | The deck is up. The camera stands in the low middle of the lane (open item above). |
| `a-ltsr-west-overhead`, `-oblique`, `t22-ltsr-bow-creek-west` | The line runs on from the Bow Creek bridge between the works to St Leonard's Street. The earth end has gone. |
| `t22-four-mills-from-river`, `t22-sun-mills-from-river` | Brick river walls where there were earth faces and a mud slope. |

## Regeneration

Order, as for T22:

1. Infrastructure and housing (stable after one pass).
2. `prepare_os_ground_levels.py`.
3. `build_river_network.py`.
4. Historic elevation, river system, main landscape, floods, yards, drainage, cranes and manifest.
5. `check_road_bridges.mjs --write-sample`.

The flood figures logged by the build are unchanged from T22: 4.5 m ODN 112.86 ha, 5.5 m 113.84 ha. The flood grid still reads the historic scaffold (task B). The GeoPackage and GeoTIFF exports were not rerun.

## Checks

- **`npm test`: 21 of 21.**
- These Python checks pass: `check_scene_data`, `check_main_landscape`, `check_river_system`, `check_district_streets`, `check_historic_elevation`, `check_marsh_ditches`, `check_river_tides`, `check_western_completion`, `check_factory_yards`, `check_manor_road`.
- Two Python checks outside `npm test` **already fail on main `25701a7`**, and still fail:
  - `check_three_mills_landmark_alignment.py` (`site256-range-1`, unchanged).
  - `check_remaining_trades_context.py`. It holds every road it did not itself change equal to an old baseline. On main the High Street and its Channelsea approach already differ from that baseline (since T13). Task A adds Cook's Road, because of its deck height.

## Decisions for the author

1. **Marshgate Lane between its readings:** carry the street readings along the lane corridor in the terrace zone, so the lane runs 3.19 → 2.80 m instead of dipping to 1.2 m. This is the next fix I'd make; I didn't make it here.
2. **The LT&SR beyond St Leonard's Street:** drawing the street bridge (deck 47.3 ft), its ramps (39.9 ft) and Bromley Station would let the line run on to the box edge.
3. **Bow wharves:** retrace the Lea outline at Bow Bridge on the OS, then add the wharf walls to the same register.
4. **Four Mills section:** the OS band is about 4 m wide. A battered wall or an apron would be closer to it than the vertical wall now drawn.
