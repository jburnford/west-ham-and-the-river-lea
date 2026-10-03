# GIS exports of the model

3 October 2026. First export of the reconstruction data to standard GIS formats, as the first workstream of [the portability plan](../../MODEL_PORTABILITY_PLAN.md).

## What is exported

`python3 scripts/export_terrain_geotiff.py --verify` writes 15 GeoTIFFs to `exports/gis/terrain/`:

- The detailed 0.4 m Channelsea tile: interpreted baseline heights, land cover classes, the sediment mask, and the heights as rendered in the 1900 main landscape (scene Y and provisional ODN).
- The 1 m dated open-ground reconstruction for 1900: target, scene, weight, ODN, and the drainage, road and zone masks.
- The 10 m regional early-marsh field applied across the main 1900 scene: level (scene Y and provisional ODN) and weight.

`python3 scripts/export_geopackage.py --verify` writes 36 layers and 17,844 features to `exports/gis/west-ham-model-1900.gpkg`: industrial site and river outlines from the supplied GIS, 681 registered factory ranges with their evidence text, High Street frontages, Abbey Mills and its supporting buildings, the factory study envelopes that the registered ranges supersede, 192 housing rows with plots, forecourts, rear extensions, privies and plot walls, gas holders, factory structures, roads, bridges, railways, the sewer, marsh ditches, reviewed river connections, tidal extent, retaining edges, the regional river system, yards and yard tracks, the allotment garden and its beds, and the mapped trees.

Both are EPSG:27700. `exports/` is ignored by git, so regenerate after model changes.

## How the conversion works

Every scene coordinate is metres east (x) and south (z) of the origin recorded in `docs/data/ground-plan.json`: easting 538900, northing 183209, the approximate listed grid reference of the sewer bridge. Easting = 538900 + x and northing = 183209 − z. Vertex grids are written point-registered; the 10 m field, whose metadata declares cell centres, is area-registered.

Rotated rectangles (study envelopes, the mill, garden beds) are rebuilt from centre, size and rotation. The script calibrates the rotation sign against the 192 housing rows, which carry both a rotation and an explicit footprint, and refuses to run if the worst corner error exceeds half a metre. On this data the worst error is 0.000 m.

## Validation so far

- Every GeoTIFF reads back with the EPSG:27700 key and a tiepoint within the scene extent. Every GeoPackage layer reads back with its written count and CRS.
- Independent position check: the Wikidata coordinate for Abbey Mills Pumping Station converts to easting 538771, northing 183204. The exported main building envelope has its centroid at 538719, 183223, 55 m away. The Wikidata point is imported from Wikipedia and marks the complex rather than the 1868 building, so this is a sanity check against mirroring or a gross offset, not a precision test.
- The Wikidata coordinate for Abbey Mill (the watermill) is given to whole seconds and lands 420 m from the model's OS-anchored mill. That point is too coarse to use.

## Still to do

- Open the GeoPackage in QGIS over the georeferenced NLS tiles in `reference/nls-tiles` and confirm the Abbey Mills envelope, the Abbey Lane houses and the Bromley holders sit on their mapped positions. This is the precision check the Wikidata comparison cannot give.
- Confirm the ODN rasters against a known benchmark once the vertical reference is no longer provisional.
- CityJSON export of the buildings with heights, epochs and sources, when the model is stable enough to deposit.

## glTF export of the rendered scene

Added later on 3 October 2026 as the third workstream. `scripts/export_gltf.py` loads the site headlessly with `?export=1`; `app.js` then skips releasing the CPU vertex buffers, tags everything it adds with a layer name through a `mark()` call between assembly steps, and batches per material and layer rather than per material only. `docs/scene-export.js` clones the chosen layer's meshes with world transforms baked in and writes binary glTF 2.0 with the vendored Three.js exporter (`docs/vendor/three/GLTFExporter.js`, three 0.180.0, MIT). The Python side pulls the file out in slices, then writes the scene origin, axes and placement rule into `asset.extras`. `scripts/check_gltf.py` verifies the container, the origin tag, that every mesh lies inside the district, and that buffer lengths agree.

Layers and triangle counts at the time of writing: terrain 3,113,293; ground 2,115,545; housing 1,734,128; yards 356,963; infrastructure 256,404; gas-holders 240,640; factory-buildings 232,625; waterfront 208,201; study-buildings 61,128; sewer 56,655; trees 31,488; plus 236,052 untagged (lights, regional plan planes and other objects added after batching). First exports: factory-buildings 24.8 MB with 17 meshes, 11 embedded images and extents x −1297..209, y −0.3..62.4, z −845..1294 m; sewer 7.0 MB with 4 meshes and a crest no higher than 8.6 m. Both pass the structural check.

What does not travel: the weathering, contact-shadow and river-reflection shaders, and bump maps, which glTF has no slot for. Surfaces arrive as metallic-roughness materials with their base colour textures. The terrain and ground layers are large and non-indexed; export them only when a consumer needs the relief itself rather than the GeoTIFF.

Still to do: open a layer in Blender beside the GeoTIFF and GeoPackage and confirm coincidence; a Godot import as the open-engine test.

## Limits

The GeoTIFF and GeoPackage exports hold the model data, not the rendered detail. Facade windows, chimney forms, barges, clods and yard textures are generated by the JavaScript at page load; the glTF export above is the route to those, and it carries geometry and colour textures but not the shader-based weathering.
