# Task C report: the tide re-levelled from the OS (5 October 2026)

This work was done directly in the parent session, without agents. Branch `task-c-tide` (worktree `../book_website-taskc`), from main `f8c238b`. It is the first item in the work queue: the tide range (`OPUS_DELEGATION_PLAN.md`, open fundamentals).

## Summary

- **Levels.** Low water **-2.0 m** (was 0.06) and high water **1.58 m** (was 1.1), scene y; ODN about -0.17 m and 3.41 m. The range is **3.6 m** (was 1.04 m).
- **Extent.** The moving tide now reaches the OS high-water mark where the OS draws mud beyond the mapped channel:
  - the east flat at Four Mills and Sun Mills, with the mud island;
  - the Sun Mills mud basin.
  - In the Channelsea core, the existing shelf study already followed the OS lines; it is re-levelled, not re-traced.
- **Tidal limit at Abbey Mill.** The OS letters "Highest Point to which the O.T. flow" at Abbey Mill. The Channelsea above the mill (channels 12 and 13) is now still water, and the mill race is the step. The author confirmed: "there must have been a step around Abbey Mill".
- **Bow Creek is tidal to the Thames** (author, during the task). The regional river system's Bow Creek and Thames-mouth water now rises and falls with the network's tide, on tidal beds and banks.
- **Banks.** The generic tidal bank crest rises from 1.65 to **2.22 m**, the median of the OS towing-path readings. High water would otherwise have stood at the crest.
  - Retaining walls now reach down to **-2.5 m**, below low water.
- `npm test`: **21 of 21**. Builders are deterministic, checked by rerunning and comparing bytes.

## What the OS gives

The five-foot plan (1893-96) draws the H.W.M.O.T. and L.W.M.O.T. lines and letters the mud. It prints no level for either line, so the levels come from the readings around them (`data/maps/os-ground-levels.json`). Scene y = ODN - 1.835 m.

**High water.**

- The H.W.M.O.T. runs along the wall faces at Three Mills, Sun Mills and Four Mills, and at the toe of the hatched east banks.
- Ordinary tides therefore stood below the tidal-reach wall tops and towing paths:
  - the side of the Tidal Lock, 14.53 ft (2.20 m);
  - the Sun Mills wall, 14.7 ft (2.25 m);
  - the Bow Creek towing path, 14.9-15.8 ft (2.31-2.58 m);
  - the Lea towing paths above Bow Locks, 14.1-15.0 ft (2.07-2.34 m).
- They stood above the marsh behind the banks, 4.2-9.7 ft (-0.95 to 0.73 m). The author describes that marsh as lower than the rivers at high tide.
- Trinity High Water, 12 ft 6 in above OD (from *The Engineer*, already in `historic-flood-events.json`), is **1.58 m**. It falls inside that bracket and is the model's high water.
  - Ordinary tides averaged a little lower (the OS mark is the mean of springs and neaps).
  - In my first message I mislabelled the Lea towing paths as 13.1-13.7 ft. The scene levels I gave were right.

**Low water.**

- The L.W.M.O.T. runs along the mapped channel outline (the GIS layer the model's shoreline follows). This holds at Four Mills, on Bow Creek, and on Abbey Creek and the Channelsea below Abbey Mill.
- The marsh drains emptied through sluices at low water. Low water therefore stood below the lowest drained marsh (-0.95 to -0.49 m, by the Abbey Mills sluices) and below their drain beds.
- **-2.0 m** (about OD) is an estimate within that bound.
- Supporting evidence: the author's G2G modelled flow file for the Lea at Feildes Weir (1891-1910) gives a median of 4.6 m³/s and Q95 of 2.0 m³/s. That is a shallow stream at low water, consistent with the OS's narrow low-water channel.

**Form check against the author's photographs** (form only; modern tides are higher):

- At House Mill, high water stands about 1 m below the quay.
- Low water exposes 4-4.5 m of wall.

## Changes

**New register and helper**

- `data/maps/os-tide-levels.json` holds:
  - the levels, with the readings that bracket them;
  - the tidal limit;
  - the tidal bank crest;
  - the display sections;
  - the two traced mud-flat polygons, with their evidence.
- `scripts/tide_levels.py` reads the register. It is shared by the network, core, regional and connection builders.

**Builders**

- `build_river_network.py`:
  - **Beds.** Tidal beds run from 0.6 m above low water at the shoreline to 1.7 m below it, so a mud margin shows inside the outline at low water. Shelves rise from that edge to the crest over 5 m.
  - **Mud flats.** The OS flats rise from the same edge to 0.2 m below high water over 12 m. The mesh is extended over them, they are cut from `baseGround`, and they are added to the tide polygons and coloured as silt.
  - **Core seam.** Where a tidal channel crosses the edge of the detailed core, both meshes meet 0.6 m below low water, using exact distances on both sides. The old seam was -0.1, which dammed the channel at low water. This is the pale straight bar the author saw on the Channelsea at the Abbey Creek mouth.
  - **Tidal limit.** Channels 12 and 13 leave the tide. Their works frontages keep their retaining edges: 36 routes and 2,352 m, unchanged.
  - **Tide record.** `tide.low` and `tide.high` come from the register, and `retainingEdges` carries crest 2.22 and base -2.5.
- `core_river_connections.py`: a passage into a channel above the tidal limit is not tidal. This is the Abbey Mill race.
- `build_river_terrain.py`, the Channelsea core:
  - tidal beds and mud as in the network;
  - northern shelves only below Abbey Mill;
  - mud capped 6 cm under high water, so the shelf study's clods no longer stand out of the water;
  - pools carry their own water level (the fifth field);
  - the same seam rule as the network.
- `river_bank_sections.py` and `build_river_system.py`: regional Bow Creek, the Thames mouth and their seams are tidal.
  - They get tidal beds and banks.
  - Their drawn water moves to `tidalWaterPolygons` at `tideLow`.
  - Network vertices under that water are lowered to 0.6 m below low water, not -0.7 (`tidalCoreBedCorrections`).
- `marsh-ditches.json`: `illustrativeHighWater` is retired. `build_river_system.py` and `build_panorama_data.py` accept the new pool field.

**Scene modules**

- `docs/app.js`:
  - The tidal water is one moving surface from low water up, always visible. The static tidal plane at 0.06 is gone.
  - The Channelsea head is drawn as still water.
  - Pools use their own level.
  - Lighters are placed at low water.
- `docs/river-system.js`: tidal regional water in the network's tidal material, so the tide control lifts it.
- `docs/realism.js`: the tidal reflection runs at every stage.
- `docs/photo-details.js`: barge base height is a parameter.
- `docs/sewer-crossing.js`: the trough's minimum soffit is 1.9 m, keeping the same 0.3 m clearance over high water.

**Checks and tools**

- `check_river_tides.py`, `check_marsh_ditches.py`, `check_historic_elevation.mjs`, `check_core_river_connections.py`, `check_landscape_flood.py`: see Checks.
- `check_road_bridges.mjs`: stored road sample refreshed.
- `scripts/render_views.py`: a camera may carry `"tide": 0..1`.

## Numbers

| | Before (main f8c238b) | After |
|---|---|---|
| Low / high water (scene y) | 0.06 / 1.1 | -2.0 / 1.578 |
| Tide polygons (network) | 174,592 m² | 159,479 m² (+3,836 OS flats beyond the old shelf; -18,949 above Abbey Mill) |
| Traced OS mud flats | none | 10,036 m² (2 polygons) |
| Regional tidal water | 0 | 654,492 m² (Bow Creek to the Thames); still regional water 309,041 m² |
| Network mesh | 924,788 vertices | 931,618 vertices (the flats) |
| Network / core height range | -1.72..2.05 / -1.74..3.46 | -3.70..2.26 / -3.70..3.46 |
| Core pools | 17 | 10 (none above Abbey Mill) |
| Generic tidal crest / wall base | 1.65 / -0.55 | 2.22 / -2.5 |
| Connected land, 1.9 / 2.5 / 3.5 / 4.5 / 5.5 m ODN | 0 / 30 m² / 78.3 / 105.5 / 113.8 ha | 1 m² / 316 m² / 73.9 / 105.7 / 114.5 ha |
| Plinths (main landscape) | 157 | 160 |

## Structural diffs

`river-network.json` changes at these keys:

- `tide/{low,high,polygons,evidence,register}`
- `retainingEdges/{crestHeight,baseHeight,routes,coreWallRelocation,osRiverWalls/walls}`: route vertices move with the new mesh shoreline, and lengths are unchanged.
- `aboveTidalLimitChannelIds` (new)
- `tidalChannelIds` (12 and 13 removed)
- `reviewedConnections/connections`: `abbey-mill` is no longer tidal.
- `marshDitches/levels`, `baseGround`, `bankMesh/gridVertices`, `vertices`, `triangles`, `heightRange`

`river-system-1900.json`:

- new: `tidalWaterPolygons`, `tidalReachIds`, `tideLow`, `tidalCoreBedCorrections` (791 vertices), `tidalCoreBedLevel`
- `waterPolygons` keeps only the still regional water.
- `coreBedCorrections` falls from 7,031 to 5,860.

`river-terrain.json`: `pools` gains a level field (`poolFormat`), and `tideRegister` is new. The rest of the cascade is regenerated (landscape, historic elevation, floods, yards, drainage, cranes, manifest).

## Checks

- **`npm test`: 21 of 21.** Python checks pass: `check_river_tides`, `check_river_system`, `check_river_banks`, `check_marsh_ditches`, `check_core_river_connections`, `check_landscape_flood`, `check_main_landscape`, `check_historic_elevation`, `check_scene_data`, `check_district_streets`, `check_western_completion`, `check_factory_yards`, `check_manor_road`.
- **Changed assertions:**
  - `check_river_tides.py`:
    - Levels must equal the register, with low < retained < high < crest.
    - Walls must reach below low water.
    - The OS flats must lie inside the tide, between low and high water, and be drawn as mud.
    - Tidal beds must lie below low water away from the edges.
    - No tide may pass Abbey Mill, and there must be no tidal mud along channels 12 and 13.
    - The old "high <= 1.1" guard (against a rejected 1.4 m setting) is replaced by the register check.
    - Channel 13 leaves the exposed-shelf list.
  - `check_marsh_ditches.py`: reads high water from `tide.high`.
  - `check_historic_elevation.mjs`: the tide must equal the register (was 0.06/1.1).
  - `check_core_river_connections.py`: only locks and the Abbey Mill race are non-tidal, and no tide crosses them.
  - `check_landscape_flood.py`: at 1.9 m ODN, partial channel-edge cells under 2 m² may count as land.
    - Before, it had to be exactly 0. It is now 1 m²: one cell below Abbey Mill, 94% inside the tidal water, whose remaining 6% is intertidal mud at -0.5 m.
    - The enclosed-bowl test at the higher stages is unchanged.
  - `check_road_bridges.mjs`: stored sample refreshed. Only the Hunts Lane connection's west approach moved, by at most 0.022 m.
- Lint and prettier are clean on the changed JS.

## Renders

Before (main on 4173) and after (task C on 4210), each at low and high water, are in `reference/photo-review-2026-10-03/views-taskc/`. Each `final-*.png` sheet holds four panels. The cameras are in `cameras.json`.

| View | Verdict |
|---|---|
| House Mill (`final-house-mill`) | Better. At low water, mud shows at the foot of the mill frontage and along the left bank. At high water, water reaches the quay foot. The camera sits low in the channel; the mill-race arches are not in frame. |
| Four Mills (`final-four-mills`, `final-four-mills-air`) | Better. At low water the arcaded Four Mills wall stands on exposed mud, the channel narrows, and the mud island and the Sun Mills basin are bare. At high water both are covered and the water spreads east over the flat. Before, the two stages looked almost the same. |
| Channelsea at Abbey Mills (`final-abbey-mills-channelsea`) | Better. At low water it is a narrow stream between steep mud banks, with a lighter at the stream edge, like the author's 1920s-30s aerial. At high water it fills bank to bank. |
| Abbey Creek mouth (`final-abbey-creek-mouth`, `-plan`) | Fixed. Before, a pale straight bar crossed the water at the core edge at low water. After, the bed is continuous across the seam (-2.6 m on both sides). A colour change in the bed remains where the two meshes meet. |
| Bow Creek south edge (`final-bow-creek-south-edge`) | Improved. The water no longer steps at z 1364. The regional and network banks still meet with an abrupt change of form. |
| Regional Bow Creek (`final-bow-creek-regional`) | New. It now rises and falls, with its banks above high water. A bridge across it shows more of its structure at low water. |

## Smoke

`review_smoke.py` (scratch copy with 900 s waits): `taskc-before` (main on 4173) against `taskc-after` (4210). Both have **0 page errors**. There are 22 differences, all expected:

- **Mesh and triangle counts.** River network and landscape replacement counts move with the new mesh. The draw-call count rises by one (the tidal regional water).
- **Triangles fall by 263k.** Terrain clods drop from 22,656 to 8,703: the shelf study's clods are now under water or capped.
  - Vegetation tufts rise from 4,013 to 4,817.
- **Reflection.** It now renders two planes at every stage. Its tidal level at load is -2.0, the page's low-water start.
- **Bed corrections.** `riverSystem.coreBedCorrections` falls from 7,031 to 5,860; the rest are the new tidal corrections.
- **Sewer crossing.** The abutment foundations reach down to -1.51 m (were -0.09), following the lower bed.
- **Channelsea crane at Abbey Mills (-20.7, -135).** It stands on 2.98 m ground (was 1.12 m), on the Abbey Chemical and Varnish works wharf edge above the mill.
  - Before, it sat on the tidal mud shelf.
  - With the head now still water, it stands at yard and wall-top level.

## Not done

- **The Lea between Bow Bridge and Bow Locks (channel 18)** stays still at the retained level, under the earlier rule (Old Lea above the Limehouse Cut lock). It steps against the tidal Three Mills Back River at (-706, 313), where the OS shows no lock. This is recorded in the plan as a question for the author.
- **Abbey Mill ground** is drawn at 0.3-0.4 m beside the mill, where the OS reads 14.5 ft and the road over the mill 16.5 ft (about 2.2-2.3 m). The flood grid reaches it at 2.5 m ODN (316 m²). Recorded in the plan.
- **Other edges of the core box.** Only Bow Creek was made tidal in the regional system. The Lea north of the box stays still.
- **Exports.** GeoTIFF, GeoPackage and glTF exports were not rerun.

Added to the plan's to-do list at the author's request: towing paths made consistent (carry the Wall River photograph model down the river), the Three Mills Lea Bridge abutments, the Lime & Cement Wharf, and Laboratory Yard at City Mills (next task).

## What I was unsure of

- **Low water.** -2.0 m is bounded, not measured. Anything from about -1.5 to -2.5 m fits the OS evidence. The bed depths (1.7 m below low water) are display estimates.
- **High water.** It is Trinity High Water, a spring-tide figure. Mean ordinary high water was somewhat lower.
- **The flats' shape** between the two OS lines (a 12 m ramp, then just below high water) is an interpretation.

## Decisions for the author

1. **Channel 18** (the Lea from Bow Bridge to Bow Locks): tidal or retained? I recommend tidal, because the OS shows no lock at the Three Mills junction and runs "C.C. at L.W." along it. The alternative keeps the step there.
2. **The flood page's lowest stage** (1.9 m ODN) was the old low water. It could now start at the new low water or at the marsh level.
3. **Tidal crest 2.22 m** uses the Lea and Bow Creek towing paths. Bow Creek's readings alone give 2.43 m.
