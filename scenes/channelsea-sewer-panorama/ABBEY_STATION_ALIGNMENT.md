# Abbey Mills Pumping Station — plan and architectural refinement

28 September 2026. The prior procedural station was a north-aligned 54 × 48 m
cross at (-185,-13), with both chimneys on provisional diagonal offsets. The
supplied historical outline is rotated about 36 degrees and includes lower rear
boiler wings in addition to the ornate main station. Treating the complete
outline as the main Greek cross would distort the building.

## Evidence

- Author-supplied `london_buildings_1891-96_corr_v1.gpkg`, footprint 459: complete
  station/boiler outline. Chimney-base footprints 257848 and 277380.
- OS five-foot map, local mosaic `m18_131069_87140.png`: inspected to distinguish
  the central station, rear wings, chimney bases and adjoining site buildings.
- Existing local 2022 photograph by The wub: surviving architectural detail.
- Author-supplied Mary Evans 1868 engraving 45687726: period silhouette and lost
  chimney upper parts. An illustration, not a measured elevation.
- [Historic England main-station record](https://historicengland.org.uk/listing/the-list/list-entry/1190476):
  cross plan, mansard slate roofs, two storeys and dormers, polychrome arches,
  five-bay arm ends and central octagonal lantern.
- [Historic England chimney-base record](https://historicengland.org.uk/listing/the-list/list-entry/1357995):
  surviving northwest/southeast bases and their elaborate brick/stone treatment.

## Changes

`data/maps/abbey-station-plan.json` retains the source outline, fitted body plan,
source IDs and interpretation. A compact runtime copy is in `docs/data/`.
`build_abbey_station_plan.py` fits the position and orientation of a manually
interpreted set of body rectangles, after the map inspection established their
arrangement. Main cross: 42 m transverse arm, 52.5 m long arm, widths 20 and 16 m.
Two lower 29 × 20 m rear wings complete the main mapped outline. The widths,
compartment interpretation and roof heights remain approximate.

`photo-details.js` now positions and rotates these elements from the plan.
Dormers, arm-end façades, roof cresting and corner turrets follow the revised
body dimensions. The lower lantern transition has been adjusted and masonry
colours distinguish the stock brick, red dressings and pale stonework. Existing
upper chimney profiles and heights remain interpreted; their bases have been
repositioned from the source polygons and reduced in width to match their plan
scale. Modern paint colour is not asserted as a circa-1900 measurement.

The station/boiler body has 95.4% intersection-over-union with source footprint
459, compared with 51.6% for the previous main cross. This is footprint agreement,
not 95.4% historical accuracy. Ornamental projections are outside that body-fit
metric. No vertical-datum or terrain calibration is introduced.

The station appears on the location map and its body/chimney masks suppress the
regional flat outlines beneath the modeled buildings. The direct destination is
`?view=pumping-station`.

## Checks and remaining work

`check_abbey_station_plan.py` reconstructs the rendered body parameters, checks
source overlap, validates the chimney-base centres and checks water clearance.
The 77-destination navigation check and JavaScript syntax checks pass. Four local
browser views inspect the plan, front, boiler wings and view from the sewer
bridge. No browser/shader errors occurred in the first visual review.

## Supporting buildings and access, 28 September continuation

Eight supporting buildings and four lower annexes now use their complete source
outlines. They previously appeared only in the regional flat plan layer. The
saved authoring register is `data/maps/abbey-supporting-buildings.json`:

| Building | Source feature IDs |
| --- | --- |
| Entrance lodge and two annexes | 319303, 1062450, 1067767 |
| Northern outbuilding and annex | 47165, 1014887 |
| Northwest chimney-side building and annex | 578410, 1016967 |
| Southeast chimney-side building | 816877 |
| Southern outbuilding | 6687 |
| Three southwest/drain-side buildings | 68075, 774880, 74478 |

The lodge is labelled on the map; other names describe location, not an identified
historical use. All twelve volumes retain the source polygons, including the
southern building's stepped end. Pitched roofs follow each outline's long axis;
annexes have lower lean-to roofs. Heights, roof forms, openings and materials are
interpretations, not measurements. Exact source-outline agreement does not
establish historical accuracy. Gate-side feature 1064653 and the tiny drain-side
projection 1162448 remain deferred because their function is unclear.

The old approach crossed the northwest chimney base and ended inside the revised
station. Five replacement access routes follow corridors read from the period
OS mosaic, with an entrance joined to the existing Abbey Lane. Pixel traces and
their georeferencing are retained in the authoring register. Widths, surfacing
and the short southern forecourt connection remain interpreted. Road surfaces
and shoulders exclude the station, stacks and supporting buildings.

`abbey_support.py` derives the supporting ranges and routes, and provides common
building exclusions for infrastructure, yards, housing and tree checks. The
station generator publishes these in its existing authoring/runtime plan. The
shared factory renderer draws the new volumes separately from the 507 industrial
ranges. They also appear on the location map and mask the regional flat layer.
Factory yards, housing clearances and regional plan tiles have been regenerated.

Rebuild this group in order:

```sh
python3 scripts/build_abbey_station_plan.py
python3 scripts/build_infrastructure.py
python3 scripts/build_factory_yards.py
python3 scripts/build_housing_detail.py
python3 scripts/build_mapped_trees.py
python3 scripts/build_regional_footprints.py
python3 scripts/build_scene_manifest.py
```

The expanded geometry check covers all twelve source-linked volumes, lower
annexes, water/drain clearance, road surfaces, route continuity at Abbey Lane,
tree clearance and agreement between saved authoring/runtime plans. Existing
factory, yard, housing, western-completion and 77-destination checks also pass.
The browser review includes the full site, southern group and entrance, alongside
the four earlier station views. All seven rendered without browser/shader errors
and were visually inspected; the diagnostics confirm all twelve supporting
volumes reached the renderer. Local source comparison:
`reference/abbey-mills-alignment/support-source-overlay.png`.

Precise ornamental carving, confirmed outbuilding uses and elevations, the two
deferred small features and detailed gate/rail arrangements remain unresolved.
The independent height-extraction work and terrain datum are unchanged.
