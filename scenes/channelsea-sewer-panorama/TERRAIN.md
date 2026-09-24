# River terrain and material study — 24 September 2026

The author's current direction is texture and topology, with phone and website development deferred. Figure 2.4 supplies the southern reference: torn mud, smooth water in deeper cuts, dense coal cargo, a raised bank on the right of the south-facing view, and sheds on low-lying Mill Mead behind it. The author also requested the same river-surface treatment north of the bridge and identified a conspicuous polygon/hexagon artefact to remove.

## Implemented

- One indexed ground mesh spans local x −235 to 65 m and z −320 to 350 m, sampled at 0.4 m. It replaces the flat ground inside that rectangle, with submerged channel floors, shelves, small pools and drainage cuts on both sides of the bridge. GIS channel routes anchor the study; the rendered tidal margins and small cuts are inferred.
- The southern river-right bank rises above the lower ground behind it. The model's local levels range approximately −1.74 to 3.46 m around a water plane at 0.06 m. The author supplied the low-Mill-Mead interpretation; the actual levels and bank profile are modelling estimates, not measurements from the photograph.
- 102 short drainage cuts and 15 shallow pools break up the surface. Their locations are procedural interpretations. Small flattened, irregular clods replace the conspicuous pale polygon fragments seen in an intermediate review. Continuous metre-based texture coordinates on the terrain prevent individual triangle faces from becoming texture tiles.
- An original generated sediment texture supplies torn silt and fine wet creases. It is applied on both sides of the bridge at a nominal 2 m tile size. Its intensity supplies fine bump relief, not measured displacement. No archive image was supplied to the image generator or used as a texture. Asset: `docs/assets/textures/tidal-mud-v1.png`; full text prompt and provenance: adjacent `tidal-mud-v1.json`. Generated with the built-in imagegen tool.
- A depth/moisture atlas differentiates channel water from shallow silty margins. Water remains opaque/turbid and reflects the actual provisional scene; this is not a water-quality or tidal simulation.
- The three loaded southern barges now contain continuous coal mounds with 1,450 small irregular pieces each. The existing hull positions are retained.
- Nineteen varied plank sheds, low fences, barrels and uneven cultivated rows occupy the existing allotment area. Their individual forms and positions are interpretations; the mapped/author-identified garden envelope is retained.
- Abbey Mill now has interlocking pitched gables, boarded upper floors, small windows, masonry below and a low waterside cover, informed by the c1800 illustration. Its interpreted main wall height is 11.5 m, with varied ranges and ridges above. The main 14 × 8 m envelope and anchor remain; the low cover projects beyond it. The author's continuity hypothesis informs the c1900 form. No windmill tower, cap or sails are included.

The eight newly supplied map extracts are archived unchanged in `reference/author-map-extracts-2026-09-24/`, with an inventory and inspection notes. They help distinguish industrial ranges/courts, river branches and open land. The last is labelled 1905 and remains a dated comparison rather than proof of every feature in 1900. The southwest extract informs 15 distant terrace groups and 20 industrial ranges within existing GIS parcels. Three further terrace traces are withheld for conflicts with industrial land. The approximate registration uses seven holder centres; the 1.14 m residual is an internal model fit, not historical accuracy. Range footprints, elevations and house divisions remain interpreted; see the reference README and `data/maps/southwest-context-traces.json`.

## Rebuild and review

```sh
python3 scripts/build_panorama_data.py
python3 scripts/build_river_terrain.py
python3 scripts/build_southwest_context.py
python3 scripts/check_scene_data.py
python3 scripts/review_terrain.py
```

The terrain generator needs NumPy, SciPy, Shapely and Pillow. It writes `docs/data/river-terrain.json`, `.f32` heights and `.rgba` depth/moisture data. Assertions check finite heights, submerged channels, the raised bank and lower allotment ground. Runtime geometry is in `docs/terrain-details.js`; materials and depth-aware water are in `docs/realism.js`.

The review script uses the existing local viewer at port 4173, hides its overlays only in exports and captures south, mud detail, Mill Mead, the southwest distance, Abbey Mill, the northern river and northern context. This pass does not run phone/layout development checks. `review/terrain-checks.json` records the latest completed desktop review and shader-error checks. Current render cost is about 4.2 million triangles in the main pass, with a separate reflection pass; earlier browser-report counts describe the earlier scene.

Remaining visual limits: the model still lacks a solved photographic camera match; some broader banks and industrial forms remain schematic; the generated fine texture contains its own tonal shading and is not a calibrated PBR scan. Further geometry should be guided by the source photographs and registered maps, rather than introducing arbitrary rocks or debris.

The subsequent [lighting and infrastructure pass](LIGHTING_AND_INFRASTRUCTURE.md) supersedes the earlier lighting setup and flat railway levels. It adds 50 map-traced road/lane studies with provisional grey/brown period surfaces, raised railway embankments and crossings, and separate Three Mills landmarks. The sediment mask now protects dry ground from wet-mud shading. Latest desktop exports and error checks are `review/lighting-*.png` and `review/lighting-checks.json`; earlier rendering counts describe earlier passes.

## Garden scale and tree follow-on

The original small garden patch and its 19 sheds are superseded by the broader central allotment interpretation described in `LIGHTING_AND_INFRASTRUCTURE.md`. The author supplied later OS tree/allotment detail (viewer 1914) and a 1945 aerial for garden scale; individual plots and c1900 continuity remain inferred. There are now 308 model beds, with pale/brown soil, low planted rows and scattered sheds. Mapped access routes and earlier waterways remain clear. Outside the dense terrain rectangle, garden objects use the surrounding ground datum rather than clamping to an unrelated edge height. Sixteen tree symbols are rendered separately from `docs/mapped-trees.js`. See `review/mill-trees-checks.json` for current counts. Prescott Cut is later than the target scene and remains excluded.
