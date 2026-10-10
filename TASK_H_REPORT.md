# Task H: north infill, Stratford Marsh (10 October 2026)

Branch `task-h-north-buildings`, from `main` 3e2da35. The author asked to continue the missing buildings north of the G.E.R. main line
(task F's later batch) and chose roads first; the Great Eastern works (north of the North London line, outside the core) wait for a
later batch.

## What changed

- **Audit** of the author's 1891-96 footprints north of the main line inside the core area: 530 footprints of 30 m² and over with
  under 10% modelled (70,139 m²). East of the Old River Lea (x > -1380, Stratford Marsh) is this batch; the Bow goods yard, the
  Hair & Wool Works and the Old Ford / Hackney Wick strip west of the Lee Navigation (factory sites, the streets they front onto, and
  254 housing footprints in the excluded districts) are left for a later batch, since no street is traced there.
- **Roads**, traced on the OS five-foot plan (NLS tiles) and added to `data/maps/district-road-traces.json`:
  - *Carpenters Road — Stratford Marsh section* (671 m, 7.5 m wide): from the northern section under the main line, past Star Works,
    the Distillery, the Tallow and Engineering Works and the Goods Depot, to the Channel Sea Junction signal box and on as a lane to
    its end by B.M. 18.92. 243 of 326 stations matched kerbs; median kerb width 7.2 m.
  - *Warton Road — Stratford Marsh section* (329 m, 9 m): from Carpenters Road south past the Chemical, Oil and Chemical, Hudson Bay
    and Varnish works to its northern section under the main line. 155 of 166 stations; kerbs 8.7 m.
  - *Marshgate Lane — north of the sewer* (141 m, 6 m): beside the Pudding Mill River from 30 m north of the Northern Outfall Sewer
    to the Bone Works.
  - Method: a rough line read from the plan, refined to the midpoint of the printed kerbs (or the bounding faces) in cross-profiles
    every 2 m, after removing lettering and marks shorter than 3 m along the road. The OS street spot heights already in the
    register lie 0.0-0.8 m from the new centrelines. The main line gains three street openings (chainage 1016-1031, 1218-1231; the
    Marshgate opening was dropped with the lane's southern stretch).
  - `scripts/prepare_os_ground_levels.py` assigns the street readings automatically; one yard-coded reading printed in Carpenters
    Road (sh_538302_184060) is assigned to it by decision.
- **Buildings**: `data/maps/north-infill-selection.json` -> `scripts/prepare_core_infill_alignment.py north` (the script now takes a
  batch; task F's output is byte-identical) -> `data/maps/north-infill-footprint-alignment.json`, registered in
  `build_factory_buildings.py`. 192 buildings (88 outbuildings, 64 sheds, 35 two-storey ranges, 5 others; 32,305 m²) in 19 factory
  sites and 5 context sites (93xx). 13 of the sites were excluded earlier as "North of the Great Eastern Main Line" and are added
  here (88 buildings). Typology as task F; 30 of 300 m² and over flagged for individual reading. Factory sites 87 -> 111 (with the
  context groupings), ranges 1027 -> 1219.
- **Yards at the tidal frontage**: four task H sites front the tidal water with no OS yard reading (Lea Bank Soap and Candle Works,
  Lea Valley Distillery, Victoria Oil and Candle Works, Marshgate Works). Their marsh-estimated pads (1.16-1.49 m) lay below high
  water, and the frontage rule (ground within 5 m of a building takes the bank blend) carried them to the water's edge, flooding
  the wharves at every high tide. `build_main_landscape.py` now floors those four at high water + 0.15 m (1.73 m).
- **Cascade**: factory buildings, High Street frontages, housing detail, infrastructure, OS ground levels, river terrain, river
  network, historic elevation, river system, regional landscape, main landscape, landscape flood, factory yards, drainage, flood demo,
  wharf cranes, regional footprints, lite meshes, scene manifest.

## Checks

- `npm test` 23/23.
- Python `check_*.py`: 42 pass; the same 33 fail as at task F's commit (identical set: hash pins, frozen snapshots, the
  `site256-range-1` render snapshot, `check_gltf`, `check_panorama`).
- River-network ground against main 3e2da35: 1,936 vertices move more than 0.3 m, all within 25 m of the new buildings or roads;
  60 fall from above to below high water (bank faces at the distillery and Marshgate Works frontages, now drawn at 1:1.5 from the
  water's edge), 1,723 rise from below to above it (the raised yards).

## Renders

Main checkout `reference/unmodelled-footprints/task-h/task-h-before-after.png` (four views at mid-tide), with the audit maps
`h-overview.png` and `ge-works.png`.

## Not done, and for the author

1. **Marshgate Lane between the sewer viaduct and the main-line bridge** (about 140 m) is not modelled. The plan shows the river
   between hatched banks, a hatched tongue (11.7) east of it, a crossing at its south end and a junction at spot height 22.5 beyond
   the river; the lane's course is not legible. A guessed line on the river's east side cut the bank by up to 1.8 m and fell below
   high water, so it was dropped.
2. **Footprint registration**: the author's footprints sit about 1.9 m west (and 0.4 m north) of the NLS mosaic that the roads are
   traced on, in every window measured, north and south (`reference/task-e-tools/infill/footprint_offset.py`). This affects the
   whole model and is the likely reason roads and buildings keep clashing. Nine buildings are held back here (seven inside the
   Warton Road and Marshgate Lane corridors, including two Varnish Works ranges of 595 and 714 m², and two over water), as task F held
   back 18. Recommend a project-wide decision on which frame to move.
3. The same high-water yard floor would also raise four reviewed sites south of the main line (Blue Works 566, West Ham Chemical
   875, Abbey Mills Chemical 876, Marshgate Mills 940); not changed.
4. Later batches: the Old Ford / Hackney Wick strip and Bow goods yard (with their streets: Wick Lane, Stour Road, Iceland Road,
   Dye House Lane, White Post Lane), and the Great Eastern works north of the core.
5. Seen in passing, also on main: a large flat dark rectangle in the sky looking north-east from about (-1010, 20, -680).
6. The author's 1860s engraving of the East London Soap Works is saved in `reference/factory-building-survey/east-london-soap-works-engraving/`;
   a comparison render from the engraver's viewpoint is still to do.
