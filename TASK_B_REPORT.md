# Task B report: Marshgate Lane, building seats and plinths, and the flood grid on the drawn ground (5 October 2026)

This work was done directly in the parent session, without agents. Branch `task-b-ground` (worktree `../book_website-taskb`), from main `bea8632`. It covers task A's open item (Marshgate Lane), T22 decisions 6 and 7 (seating), and T21 decision 5 (flood grid).

## Summary

- **Marshgate Lane** now runs at its OS level from the connection deck to St Thomas's Mills: **3.19 m** against the OS 17.8 ft = 3.19 m. Before, it dipped to 1.2–1.4 m.
  - The OS reading that was task A's exception (`sh_538054_183338`) is now met exactly, and the exception is gone.
- **Building seats:** 17 more objects are seated on the median drawn ground under them. These are T22's east outliers and a few others, all off by more than 0.3 m.
- **Plinths:** **157** buildings on sloping ground or over a bank edge now stand on a brick plinth. It reaches from below the lowest ground under the footprint up to the seat (new `docs/building-plinths.js`).
- **The flood grid** is built from the **drawn ground**, not the historic scaffold, with each wall at its drawn coping.
  - The connected land at a given stage falls a lot, because the drawn ground is T21/T22's OS-corrected ground (table below).
- `npm test`: 21 of 21 (see Checks).

## Marshgate Lane

**Cause.** It was not the deck and not the terrace correction (that correction gives 2.7–3.1 m along the lane). I traced it pass by pass in the landscape build:

1. The lane runs along the west bank of the Pudding Mill River (GIS channel 9, tidal). Its centreline is 2.4–2.9 m from the drawn water.
2. Within 3 m of the shoreline the main landscape lowers a street to the bank face, towards low water. This rule was meant for open banks.
3. So the lane's east-edge vertices sat at 0.3–0.9 m.
4. The road surface takes its height from the ground under its own vertices, so the road tilted from 3.13 m at the centreline to 0.4 m at the edge.
5. The road-support clamp then carried that tilt across the whole lane over its passes. The builder's own comment warns of this: "a steep road triangle over a bank would sink a whole lane".

**What the OS shows.** The lane's east kerb is a continuous double line on the water's edge, from the lock to St Thomas's Mills. There is no bank slope between the lane and the water, and the lane reads 17.8 ft beside it. I read that as a river wall carrying the lane edge.

**Changes**

- `data/maps/os-river-walls.json`: new wall `marshgate-lane-river-wall`, traced on the channel's west edge from the deck end to the channel corner at the mills. It becomes a 73.8 m retaining route.
- `scripts/build_river_network.py`: OS-traced walls are now interrupted only by **road bridges**, not by every road corridor, because a street may run along a wall top. Sun Mills and Four Mills are unchanged.
- `scripts/build_main_landscape.py`: new **walled-street rule**.
  - A street-corridor vertex within 5 m of a recorded masonry edge (a retaining wall or a canal face) keeps its street level up to the edge instead of falling down a bank face.
  - It changed 841 network vertices, **all on Marshgate Lane**. 154 core-grid vertices were already at street level and did not move. The system, extension and regional meshes are byte-identical.
  - Recorded as `walledStreets`.

**Result along the lane** (road surface, every 4 m):

| Stretch | Before | After |
|---|---|---|
| High Street corner | 2.64 | 2.64 |
| Over the deck | 2.95 | 2.95 |
| s 56–64 | 2.30–3.08 | 3.08–3.19 |
| s 68–116 | 1.17–2.06 | 3.05–3.19 |
| s 120–136 | 2.42–3.17 | 3.19 |

The bridge-check sample changed only at the Marshgate connection approach (up to 0.33 m), and I refreshed it.

## Seats

T22 seated the terrace objects on the median drawn ground under their footprints. **Task B extends this to every object in the core box** whose current seat (its pad, or the level field at its centre) stands more than 0.3 m off that median. 17 objects were affected (`seatOutliers` in `main-landscape-1900.json`, each with its prior seat):

- The varnish works riverside rooms: +0.71 and +1.09 m.
- The Abbey Road rooms: −0.55 and −0.56 m.
- Several east marsh works ranges: +0.3 to +1.13 m.
- The Langthorn northwest range: +0.96 m.
- Gasholder `bromley-5`: 0 → 1.88 m. It now stands at the gasworks yard level; the ground had been showing through inside the holder.
- The 924 weighbridge hut: 2.94 → 1.39 m.
- Others.

## Plinths

- **The rule.** Where the drawn ground under a footprint falls more than 0.3 m below the building's seat (sampled every 2 m and at the outline vertices), a brick plinth is drawn. It runs from 0.1 m below the lowest ground to the seat + 0.1.
- **The numbers.** 157 buildings, 61 of them over 1 m:
  - The largest are riverside buildings whose footprints reach the bank or water: the Walmsley grain store on the Lea (4.04 m), a building by the Bow Bridge east approach (3.85 m), and St Thomas's Mill (3.5 m).
  - Smith's fibre works dry room (3.5 m) and the Bell match works ranges by the Cut (2.8–3.4 m).
- **Where it lives.** Factory ranges, High Street frontages and housing rows get plinths; round plant does not. The renderer is `docs/building-plinths.js`, one merged brick mesh, called from `app.js` after the cranes.
- **Form.** Interpretation (a stepped or battered base). Where a plinth reaches the water it reads as a river wall under the building, which is probably right for the grain store and the mills, but not checked against the OS for each building.
- `check_main_landscape.mjs` now asserts that every recorded plinth is drawn and stands at least 0.3 m tall.

## Flood grid on the drawn ground

- **Ground.** `build_landscape_flood.py` takes its ground from `scripts/sample_drawn_ground.mjs`. That script builds the page's own drawn ground (the main landscape, the river network and river system meshes, and the core tile), as `terrainDetails().level` does, on the flood grid's 1 m lattice (about 3 s). Before, the flood grid read `terrain-1900.scene.f32`.
- **Walls.** They now stand at their drawn copings (`retainingEdgeCrests`), not the old 1.65 m placeholder.
- **Embankments and paving** are composed on top as before.
- **The record.** `landscape-flood-1900.json` records `groundSource`.

| Stage | Before (scaffold) | After (drawn ground) |
|---|---:|---:|
| 1.9 m ODN | 0.00 ha | 0.00 ha |
| 2.5 m ODN | 85.10 ha | 0.00 ha |
| 3.5 m ODN | 111.58 ha | 78.29 ha |
| 4.5 m ODN | 112.86 ha | 105.51 ha |
| 5.5 m ODN | 113.84 ha | 113.84 ha |

**Reading this**

- T21 measured the drawn ground before its correction at a median 1.81 m below the OS. The old flood grid still read that uncorrected scaffold, so it flooded the marsh at stages the OS ground stands above.
- T22's supplementary figure for T21's east area on the drawn ground was 90.9 ha at 3.5 m with no barriers. With walls and embankments the figure is 78.3 ha.
- The 1897 and 1904 accounts in `flood-evidence.md` should be re-read against these figures; I have not done that.
- `check_landscape_flood.py` and `check_flood_demo.mjs` pass.

## Renders

There are 9 cameras (session scratchpad, `tb/pairs/`); the before views are from main.

- `b-marshgate-lane-north`: the lane is level with a brick wall to the river, where before it tilted down to the water.
- `b-grain-store-lea`: a brick plinth closes the open strip under the grain store at the water.
- `b-bromley-5`: the ground no longer shows inside the holder. The camera sits inside the frame, so this is not a good view.
- `b-bow-bridge-site788`, `b-st-thomas-mill`, `b-varnish-riverside`, `b-east-513`: small or no visible change from these positions.

## Checks

- **`npm test`: 21 of 21.** `check_road_bridges.mjs` was refreshed (Marshgate only); `check_main_landscape.mjs` has the new plinth assertions.
- **Python checks pass:** `check_scene_data`, `check_main_landscape`, `check_river_system`, `check_district_streets`, `check_historic_elevation`, `check_marsh_ditches`, `check_river_tides`, `check_western_completion`, `check_factory_yards`, `check_manor_road`, `check_landscape_flood`.
- The two checks that already failed on main (`check_three_mills_landmark_alignment`, `check_remaining_trades_context`) were not re-run.

## Regeneration

1. `prepare_os_ground_levels.py` (the exception removed).
2. River network, historic elevation, river system, main landscape.
3. Flood demo, landscape flood (now calls node), yards, drainage, cranes, manifest.
4. `check_road_bridges.mjs --write-sample`.

Infrastructure is unchanged. The GeoPackage and GeoTIFF exports were not rerun.

## Decisions for the author

1. **The flood figures** change a lot: no connected land at 2.5 m ODN, and 78 ha at 3.5 m. This now follows the OS-corrected ground. The flood page's default stage (3.5 m) and its captions may need another look.
2. **Plinths at the water:** the largest plinths are riverside buildings standing on the bank face. Some of those footprints may be traced too far into the river; the OS would decide case by case.
3. **The walled-street rule** is general. Today it only changes Marshgate Lane, but any street later drawn beside a wall or canal face will run level to it.
