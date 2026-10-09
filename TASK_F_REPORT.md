# Task F: core infill (9 October 2026)

Branch `task-f-core-buildings`, from the task E head (0848322). The author asked which buildings in the core are not modelled, defined the core (north: the North London / Victoria Park branch; east: the GE Woolwich branch; south: the Bromley gasworks; west: the factories on the Lee Navigation) without the housing districts in the south-west (Bow, Bromley, Old Ford) and north-east (Stratford), and chose to start with the core south of the GE main line. North of the main line (a few factories and the Great Eastern works) is a later batch.

## What changed

- **Audit.** The author's `london_buildings_1891-96_corr_v1.gpkg` against every outline the scene draws (factory ranges, holders and structures, ground-plan terraces, houses, mapped factories and holders, High Street frontages, housing rows with sculleries and privies, the south-west rows, the Abbey Mills station plan), 1 m tolerance. Footprints of 30 m² and over with under 10% modelled. Scratch tools and maps: main checkout `reference/unmodelled-footprints/` and `reference/task-e-tools/`.
- **Selection register `data/maps/core-infill-selection.json`:** the area, the method, 118 chosen outlines with their site, label, storeys and material, and 116 held back with reasons:
  - 42 already decided by an earlier review (classified outlines, excluded context, reviewed domestic outlines, chimney bases);
  - 38 outbuildings in the OS-traced housing district south of Stratford High Street (excluded with the housing districts);
  - 18 more than 2 m² inside a drawn road corridor, 8 over the drawn water (road trace or footprint to be checked on the OS);
  - 8 already modelled as tank structures;
  - Abbey Mill (corn): the scene draws a 112 m² box where the OS outline is 395 m²;
  - one on the interpreted riverside path of the High Street vista.
- **Building register `data/maps/core-infill-footprint-alignment.json`**, written by `scripts/prepare_core_infill_alignment.py` and read by `build_factory_buildings.py`:
  - 118 ranges: 61 sheds, 29 buildings, 20 outbuildings, 6 houses or shops, 2 two-storey ranges (10,388 m² of outline); 45 in reviewed factory sites (the East London Soap Works' minor buildings among them), 3 in the new Bow Foundry site (793), 70 in 11 context sites (92xx, grouped by nearest street; model groupings, not parcels);
  - each outline clipped 0.15 m clear of every existing scene building (0.35 m from the High Street frontage outlines, which yield to factory ranges within 0.3 m), so no reviewed range or frontage is trimmed;
  - storeys, materials, uses and roof forms are typological estimates by size and position; 4 of 300 m² and over are flagged for individual reading (OS, Goad where a sheet exists).
- **Checks of reviewed sites** (Howards, Crystal/Barber, East Channelsea north, the refinery, the sugar house, Williams asphalte, and the shared `factory_alignment_checks.check_register` counts) pin the reviewed ranges and leave `-infill-` ranges to the infill register.
- **`docs/lib/ground-sampler.js`:** a point on an edge two triangles share could fall a few 1e-5 outside both after single-precision rounding and read nothing (a Bridge Court road-edge sample fell through to the coarse fallback level). A point no triangle covers is now tried again with a 1e-4 edge margin; wherever a triangle covers the point the strict test still decides, so no found height changes.
- `check_road_bridges.mjs` sample refreshed: Bow Bridge's east approach by up to 0.011 m (the road surface re-cut round new buildings beside it) and one St Thomas's Bridge sample that read a hairline gap.
- **Cascade:** factory buildings, High Street frontages, housing detail, infrastructure, river terrain, river network, historic elevation, river system, regional landscape, main landscape, landscape flood, factory yards, drainage, flood demo, wharf cranes, regional footprints, manifest. Housing detail gives up 1 scullery and 4 privies (generated) to OS outlines.

## Checks

- `npm test` 22/22.
- Python `check_*.py`: 42 pass, the same 33 known failures as at the F3 commit (hash pins, frozen snapshots, the `site256-range-1` render snapshot that stops most site checks early, `check_gltf`, `check_panorama`).

## Renders

Before (task E head) and after, at mid-tide: south of Stratford High Street, Bow and Marshgate, Pudding Mill, east of Abbey Mill. Main checkout `reference/unmodelled-footprints/core-infill-before-after.png`.

## Not done, and for the author

- North of the GE main line (about 225 buildings in some 20 sites) and the Great Eastern works.
- The 116 held back, above; the road and water cases need the OS read against the traced roads and water.
- The four buildings of 300 m² and over, to be read individually.
- `build_panorama_data.py` also reads the factory buildings; the panorama data was not rebuilt.
