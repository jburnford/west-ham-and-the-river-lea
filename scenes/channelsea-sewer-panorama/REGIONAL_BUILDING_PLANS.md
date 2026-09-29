# Regional building plans — 28 September 2026

The author's preferred next stage is a complete flat building plan, progressively
replaced by researched 3D models. The local preview now includes that layer for
the historic West Ham borough plus its 3 km buffer. This is a building layout,
not a new reconstruction of regional terrain or building heights.

## Evidence and coverage

Author-supplied `london_buildings_1891-96_corr_v1.gpkg`, read without modification
from `/mnt/c/Users/jic823/Dropbox/2026/`. Its named building layer contains
1,299,040 features in EPSG:3857. The selected study area contains 238,052 source
features. Features can be buildings, parts, outbuildings or continuous blocks:
this is not a count of houses. File naming supplies the 1891–96 date; authorship,
classification definitions and reuse terms have not been independently established.
This pass is local and does not publish the supplied data.

The boundary is the previously selected 1911 West Ham County Borough polygon,
GBHGIS unit 10025904, buffered 3 km in British National Grid. The buffered area
is 108.67 km². Source polygons that intersect it are retained whole in the
research extract, with source IDs and classifications. The viewing envelope is
BNG E534400–545600, N176400–189100. Scene coordinates use the existing origin
E538900, N183209, x east and z south.

`scripts/review_historic_building_gpkg.py` inspects and extracts the source.
Local, Git-ignored outputs in `reference/historic-building-footprints-2026-09-28/`
include compressed BNG vectors, a scene extract, inspection metadata, a
comparison image and an overlap CSV. These are the source for future modelling.
The original GeoPackage is roughly 611 MiB and is not copied into the website.

Some supplied outlines differ from hand-built model envelopes. Overlap statistics
are review prompts, not accuracy scores; the detailed models have not been moved
or replaced automatically.

## Website implementation

`scripts/build_regional_footprints.py` generates `docs/data/regional-footprints/`:

- A transparent regional overview and 115 sharper 1 km tiles, about 0.98 m/pixel.
- 234,886 source features retain visible geometry after masking existing factory,
  house and gas-holder models and modeled roads. Masking buffers avoid doubled
  edges but are not historical boundaries.
- An additional flat historical water plan uses the existing project
  `Water_1895.geojson`. It does not change the detailed tidal system.
- Approximately 4.02 MB total, including the tile index and water image.

`docs/regional-footprints.js` uses flat textured surfaces rather than hundreds
of thousands of meshes. Nearby tiles load two at a time, retaining at most 20
high-detail textures (8 in lite mode); the coarse overview fills the remainder.
Existing terrain is sampled for the overlay within the detailed scene. Regional
ground outside it is provisional, not calibrated to ODN. The ground material
matches the detailed scene; the camera near plane increases with altitude to
avoid depth flicker between close surfaces at regional distances.

The Building plans checkbox controls the outlines in both scene and maps. The
map dialog switches between Detailed district and Whole region; clicking either
map flies to that point. The minimap widens automatically outside the detailed
area. Flight bounds cover the full envelope, height reaches 2,400 m and the
Regional speed is 300 m/s. Added destinations:

- `?view=west-ham-region`
- `?view=forest-gate-plan`
- `?view=plaistow-plan`

Historical elevation transcription remains with the author and Claude. The 2003
terrain mosaic is not yet wired into this regional ground.

## Gradual replacement

Work by neighborhood or industrial site. Inspect source footprints against the
period maps, associate source feature IDs with each reviewed model, then create
heights and architectural details supported by the available evidence. Rebuild
the plan tiles after adding models so their outlines are masked automatically.
Keep the source vectors unchanged for future review. Flats remain useful context
where 3D modelling is unfinished; arbitrary extrusion is not required.

## Verification

`node scripts/check_district_navigation.mjs` checks all 76 destinations, expanded
bounds and bridge return. `scripts/review_regional_footprints.py` exercises the
actual local application: three regional destinations, nearby tile loading,
layer off/on, whole-region map travel and return to the original bridge.
Screenshots and browser diagnostics are stored in the ignored review directory.
Final desktop checks passed with no browser/shader errors or failed tiles;
regional, local-plan, map and bridge screenshots were visually inspected.
JavaScript syntax, Python compilation and `git diff --check` also passed.
No deployment or mobile performance audit is included in this pass.

After editing public modules/data, run `python3 scripts/build_scene_manifest.py`
to update cache fingerprints.
