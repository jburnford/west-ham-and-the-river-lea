# West Ham & the River Lea — website prototype

A public-history adaptation of Jim Clifford's book. The first working scene is a view with bounded movement on the Northern Outfall Sewer crossing above the Channelsea, provisionally around 1900–1902.

For the latest author preferences, historical corrections and unfinished work, consult the local project memory (kept outside the public repository).

## Run locally

From this directory:

```sh
python3 -m http.server 4173 --bind 127.0.0.1 --directory docs
```

Open **http://localhost:4173/**. Serve only `docs/`: the book, archive reference photographs and large source models stay outside the web root. Opening `index.html` directly will not load JavaScript modules and scene data correctly.

The site has no build step or runtime external requests. Three.js 0.180.0 and its MIT licence are bundled in `docs/vendor/three/`. WebGL2 is required for the 3D view; the HTML stories and SVG location map remain available when WebGL fails. A modern browser with JavaScript is required for the map and view controls.

## What works

- Bounded bridge movement: WASD or hold the direction buttons; north/south buttons cross the walkway. Drag/arrow keys turn, plus/minus zoom, and Home/reset restores position and view.
- Six story views: working river, Abbey Mills, Bromley gasworks, homes beside West Ham Gas Works, northern streets and the corn mill.
- Location map showing the live camera position, movement boundary and horizontal field of view.
- Source notes distinguishing mapped geography from inferred scene detail.
- Responsive layout, keyboard-operable dialogs and a WebGL fallback.
- Photo-informed modelling layers: curved open-hold barges and mooring details; planked retaining edges and shallow bed relief; arched industrial facades; Abbey Mills' windows, dormers, lantern and banded chimneys; more detailed gas-holder columns and girders. Geometry and procedural textures are original; no archive photograph is displayed or used as a texture. [Photo-to-model notes](scenes/channelsea-sewer-panorama/PHOTO_LAYERS.md) distinguish visible evidence from estimates.

This is a **local review model**, not a finished historical reconstruction. Camera alignment, elevations, industrial buildings, vessel placement and colours remain provisional. It is not a complete 360-degree reconstruction: surrounding unmodelled land is visible when turning. Abbey Mills is schematic. Seven Bromley holders and six map-traced West Ham holders now appear; the two lost Bromley holders remain absent. Ninety-two residential row envelopes and four Abbey Lane pairs follow the OS maps, with approximate registration and interpreted elevations. The two previously supplied GLBs are catalogued separately and are not placed in this scene.

See [the panorama brief](scenes/channelsea-sewer-panorama/README.md), [assumptions](scenes/channelsea-sewer-panorama/ASSUMPTIONS.md), and the local wider project plan.

## Data and verification

The clipped source snapshot lives in `data/maps/panorama-source-context.geojson`. Its provenance records hashes of the original `swipe_map` river and industry datasets. This repo does not require the other checkout to regenerate scene data. Industrial polygons describe sites, not building footprints. Publication rights for the supplied GIS remain to be recorded.

```sh
python3 scripts/build_panorama_data.py  # needs pyproj and shapely
python3 scripts/build_river_terrain.py  # needs numpy, scipy, shapely, Pillow
python3 scripts/build_southwest_context.py # needs numpy, shapely
python3 scripts/build_infrastructure.py # needs numpy, shapely, pyproj
python3 scripts/check_scene_data.py     # geographic invariants, same dependencies
node scripts/check_bridge_movement.mjs # bounds, crest clearance and fixed eye height
python3 scripts/check_panorama.py       # needs Python Playwright + Chromium; server running
```

Browser checks cover view selection, bounded camera movement, keyboard/pointer controls, zoom, map/evidence dialogs, mobile overflow and WebGL failure. Screenshots and the latest report are in [review/](scenes/channelsea-sewer-panorama/review/). These are software-rendered Chromium checks, not a physical-phone performance assessment.

The scene renders on interaction and resize, with a timed animation loop only while movement is held. Static meshes are batched by material. A 512 × 384 reflection pass follows the camera; the directional shadow map is rendered once for the static scene. The latest focused terrain review records 20 main-pass draw calls (about 4.2 million triangles), plus 19 reflection-pass calls. These are separate rendering costs. Terrain data and a generated mud texture add to the local renderer and scene data. Phone and website development are currently deferred at the author’s request.

London VIII.32, VIII.22 and VIII.42 have now been inspected. The author’s wider OS screenshot extends housing coverage eastwards. The scene also includes the continuous raised sewer, mapped railway routes, seven factory-range studies, interpreted gardens and Abbey Mill without a windmill. See the local reference ledger. Next research priority: improve sheet registration with multiple control points, identify individual factory buildings in figures 3 and 4, and fit photograph landmarks to the camera. The bridge was rebuilt during 1900–1902; a final scene date must account for that change.

The 24 September visual pass adds varied factory rooflines and loading facades, metre-scaled brick/slate/timber materials, surface relief, damp staining, static shadows and soft ground-contact shading. The river reflects the actual scene and the mud has irregular relief and wetter edges. This remains an interpretive reconstruction; individual buildings and camera alignment need further work. See [the refinement record](scenes/channelsea-sewer-panorama/REALISM.md).

The latest [terrain pass](scenes/channelsea-sewer-panorama/TERRAIN.md) adds detailed mud and depth-aware water north and south, a raised Mill Mead bank, 19 allotment sheds, irregular coal loads and a boarded Abbey Mill without a windmill. Fifteen approximate southwest terrace groups and 20 industrial ranges extend the distant landscape. Eight supplied map screenshots, including the dated 1905 comparison, are archived with local source notes. Use `python3 scripts/review_terrain.py` for the current focused desktop render checks.

The subsequent [lighting and infrastructure pass](scenes/channelsea-sewer-panorama/LIGHTING_AND_INFRASTRUCTURE.md) supersedes the earlier lighting setup and flat railway levels. It adds 50 map-traced road/lane studies with provisional grey/brown period surfaces, raised railway embankments and crossings, and separate Three Mills landmarks. The sediment mask now protects dry ground from wet-mud shading. Latest desktop exports and error checks are `review/lighting-*.png` and `review/lighting-checks.json`; earlier rendering counts describe earlier passes.

## GitHub Pages

The public website is the `docs/` folder, which now holds the redesigned front end (full-viewport scene, scroll-driven chapters, eased camera transitions, poster frame and self-hosted type; see `docs/README.md`). The previous front end is preserved unchanged in `docs0/` and can be served locally the same way. GitHub Pages publishes from branch **main**, folder **/docs**, at https://jimclifford.ca/west-ham-and-the-river-lea/ (the standard GitHub Pages address redirects to the account’s existing custom domain). The `.nojekyll` marker serves the static assets without Jekyll processing. All runtime imports and asset URLs are relative, so the project URL works without a custom domain.

Generated scene data and the bundled Three.js renderer are committed: GitHub does not need to run Python or install packages to serve this site. After changing a generator, regenerate its outputs under `docs/data/` before committing. Browser rendering still requires WebGL2 and sufficient device memory; the detailed desktop scene has not been tuned for low-powered phones.

The book PDF, reference photographs/maps, original model archive, local planning/memory and review screenshots stay outside the public repository. Their local paths in research ledgers document provenance and are not website dependencies.
