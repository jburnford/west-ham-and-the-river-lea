# West Ham model: portability and code-health plan

Working plan, 2 October 2026. Follows the code review of `docs/` on the same date.

The end goal is a 3D model of West Ham and the lower Lea that can serve many public history and research projects, not only the Channelsea website. This plan sets out what is already portable, what is tied to the browser, the work needed to free it, and when to do that work relative to continued building.

## 1. Where the model stands

The project has four layers with different portability.

| Layer | Where it lives | Portable today |
|---|---|---|
| Source GIS and map traces | `data/maps/*.geojson`, EPSG:27700 | Yes. Opens in QGIS as is. |
| Built model data | `docs/data/*.json` and binary grids, local metres | Yes, after a small conversion. Origin and projection are recorded in `ground-plan.json`; the vertical datum, ODN offset and uncertainty are in `terrain-1900.json`. |
| Procedural 3D detail | Generated at page load by the JavaScript modules | No. Facades, chimneys, barges, the sewer, Abbey Mills and yard surfaces exist only in the running browser. |
| Simulation and rules | Flood solver, tides, sewer and road levels, in plain JS | Runs in Node already. Portable to other languages with effort. |

The built data is the real model and the asset to protect. The browser renderer is one consumer of it. The lock-in is confined to the procedural layer, and the exit is glTF, the open interchange format every engine and Blender read. Three.js ships an exporter for it.

## 2. What the code review found

The code is coherent and not a slop mess. Modules are small, dependencies are injected, loaders validate their inputs, twelve Node check scripts test the pure modules, and performance work is deliberate and explained. Four kinds of debt have accumulated through iterative generation:

1. `docs/app.js` does five jobs: page interaction, SVG plans, scene assembly, material batching, and URL-mode dispatch. The scene cannot be built without the page.
2. Scene facts are hardcoded in JavaScript: chimney site IDs, an excluded holder, barge placements, plan bounds, contact-shadow bounds written twice, and special cases keyed on individual building IDs in `photo-details.js` and `factory-buildings.js`.
3. Helpers are re-invented per file: nine copies of the same random generator, three `tri`/`quad` batchers, four polygon-to-shape converters, three bilinear grid samplers, two GLSL noise functions.
4. No formatter, linter or test runner. Two formatting styles coexist. Several diagnostic fields are constants rather than measurements. `docs0/` and `docs2/` are old copies still in the published tree.

## 3. Workstreams

### A. Data exports to GIS formats

No 3D knowledge needed. Touches only new scripts and an `exports/` output folder, so it does not conflict with Astra's elevation work.

- `scripts/export_terrain_geotiff.py`. Read each `terrain-*.json` and its Float32 grids, add the origin, write GeoTIFFs in EPSG:27700 with rasterio. Write both the scene-height grid and the ODN grid, with the offset and uncertainty in the file tags. One file per epoch.
- `scripts/export_geopackage.py`. Write one GeoPackage per epoch with layers for industrial sites, building footprints with heights and evidence fields, housing rows, rivers and water polygons, marsh ditches, roads, railways, bridges, the sewer route and the gas holders. Convert local coordinates by adding the easting to x and subtracting z from the northing. Carry the evidence text fields through as attributes, since the footprint records already hold them.
- Validation. Open both in QGIS over the NLS tiles already in `reference/nls-tiles`. The bridge origin must land at TQ 38900 83209 and the Abbey Mills footprint must sit on the mapped building. Record the check in `scenes/channelsea-sewer-panorama/`.
- Later, optional. A CityJSON export of the buildings with heights, epochs and sources, so the model can be deposited and cited as a dataset independent of any renderer.

Flood research benefits first. A hydrologist with QGIS or HEC-RAS can take Astra's elevation grids directly once the GeoTIFF export exists.

### B. Code hygiene

Small, mechanical, and safe to do incrementally. Items marked "after Astra lands" would otherwise conflict with their uncommitted files.

- Add `package.json` with an `npm test` that runs every `scripts/check_*.mjs`. Add Prettier and ESLint configs. Agree one style.
- Create `docs/lib/` with `prng.js`, `geometry.js` for the shared box, cylinder, beam, tri, quad and polygon-shape helpers, and `grid.js` for bilinear sampling. Use these in all new code immediately. Migrate existing modules as each is next touched.
- Move hardcoded scene facts into data. Add a `chimneyStudies` list and an `excludedHolders` list to the ground plan, barge placements to a data file, and a per-building `style` or `landmark` field to replace the ID-keyed special cases. Write the contact-shadow bounds once and pass them to the shader as a uniform.
- Remove constant diagnostic fields such as `floodReady:false`, `tideConnected:false`, `capacityCalibrated:false`, `surfaceTriangles:0` and `railFormationHeight:5.5`. Keep measured values only.
- Delete `docs2/`. Move `docs0/` to a git tag or branch and remove it from the published tree. Correct the header comment in `app.js` that still names the docs2 redesign.
- After Astra lands: one whole-repo format commit, then the ESLint pass.

### C. Separate scene assembly and export glTF

The step that unlocks game engines and Blender. Depends on B for the shared helpers and on the formatting pass being done first, or the split will be hard to review.

- Split `app.js` into `page.js` for interaction, plans, loading and URL modes, and `scene-assembly.js` which takes loaded data and returns the scene, materials and handles. The assembly module must not read the DOM. Canvas texture generation moves behind an injected factory so Node can supply `node-canvas` or skip textures.
- Replace the `window.sceneAssetUrl` global with a resolver passed into the loaders.
- Add `scripts/export_gltf.mjs`. Load the data, run the assembly in Node, and write one glTF per epoch with Three's exporter. The custom weathering shaders and river reflections will not travel. Procedural textures bake to images. Record both limits in the export notes.
- Validate by importing into Blender with the BlenderGIS add-on alongside the GeoTIFF and GeoPackage from A. Terrain, footprints and the glTF must coincide. Then import the glTF into Godot as the open engine test.

### D. A rule for new work

From now on, anything that counts as a historical claim belongs in `docs/data`, not in a JavaScript literal. The JavaScript may decide how to draw a chimney; the data decides where chimneys were and how tall. This keeps new work accumulating in the portable layer and makes the future glTF export reproducible.

## 4. Sequencing and coordination

Astra is working on elevation modelling for flood simulation. Treat `terrain-details.js`, `historic-elevation.js`, `river-system.js`, `landscape-flood.js`, `flood-solver.js` and the terrain build scripts as in flux. Nothing in A touches them. B's helper library and data-moves can avoid them. The format pass and the C split wait until their branch is committed.

Because the checkout is shared, every cleanup commit stages explicit paths only.

Suggested order:

1. Now. Workstream A in full. Workstream B: tooling, `docs/lib/`, the new-work rule, delete `docs2/`.
2. Now, as modules are touched. B: move hardcoded facts into data, drop constant diagnostics.
3. When Astra's elevation work is committed. B: format and lint pass in one commit. Then C: the split, then the glTF export and the Blender and Godot checks.
4. When the model is stable enough to cite. A: CityJSON export and deposit.

## 5. Timing: convert at the end, or fix now and keep building?

Fix the structure now and keep building on it. Do not defer to a final conversion.

- The cost of the cleanup grows with every module added on the current pattern. The cost of the data exports does not grow, because they are driven by file formats rather than by code volume. Doing A now is therefore nearly free and immediately useful; doing B now is cheapest it will ever be.
- The lock-in lives in the procedural layer, and that layer is where most new detail is being added. Each week of building under the old pattern adds more hardcoded facts that a final conversion would have to dig out of JavaScript. Adopting rule D now reverses that trend without slowing the building.
- A final conversion is a large, risky, single event at the moment the model is most valuable. Incremental portability means the model is always one script away from GIS and, after C, one script away from an engine. That also lets collaborators join early with their own tools.
- The exception is the glTF export itself. Its polish can wait, because the glTF is a derived artefact that is cheap to regenerate once C exists. Build C once, then regenerate as the model grows.

What this costs in building time: Workstream A is a few days and needs no 3D knowledge. B's tooling and library are a day. The C split is a few days of focused work once the formatting is settled. The data-move items are small and ride along with modules that are being edited anyway.

## 6. Progress

3 October 2026:

- Workstream A: `scripts/export_terrain_geotiff.py` and `scripts/export_geopackage.py` written and verified. See [GIS export notes](scenes/channelsea-sewer-panorama/GIS_EXPORTS.md). QGIS check over the NLS tiles still to do.
- Workstream B: `package.json` with `npm test` running every check through `scripts/run_checks.mjs`. `docs/lib/` created with `prng.js`, `grid.js` and `geometry.js`, tested by `scripts/check_lib.mjs` against the inline copies they replace. No existing module migrated yet; migration waits until Astra's elevation pass is committed. `docs2/` archived to `exports/docs2-archive-2026-10-03.tar.gz`; removal from the tree is left for the author. Prettier and ESLint not yet added.
- Later on 3 October, after Astra's pass was committed: Prettier and ESLint added (`npm run format`, `npm run lint`), the whole hand-written front end and check scripts formatted in one pass, and ESLint's only real findings fixed (stubbed browser globals in two check scripts, three unused variables). The eight inline random generators, the elevation grid sampler and app.js's box, cylinder, beam and surface helpers now come from `docs/lib/`. `scripts/review_smoke.py` records the scene's diagnostic snapshot headlessly; before and after the refactor it reports 8,150,351 triangles, 151 draw calls, no page errors and no content differences.
- Two pre-existing check failures remain: `check_drainage_connections.mjs` and `check_flood_demo.mjs` assert hashes of `terrain-1900.json` recorded when the flood field was built, and that file has since changed. Astra's notes say the flood field has not been rebuilt to match the new landscape, so these are expected until it is.

## 7. Done when

- GeoTIFF and GeoPackage exports exist per epoch, open in QGIS at the right place, and are documented.
- `npm test` runs all checks. Prettier and ESLint are configured and the tree is clean.
- No scene fact is written as a JavaScript literal; all special cases are data fields.
- `docs2/` is gone and `docs0/` is a tag.
- `scene-assembly.js` builds the scene without a DOM, and `export_gltf.mjs` writes a glTF that imports into Blender and Godot at the right position.
