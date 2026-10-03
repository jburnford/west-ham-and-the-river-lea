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

- [Regional Lower Lea review](docs/lower-lea-region.html): explore the broader river source, 2003 relief, historical height observations and candidate connection gaps from Lea Bridge to the Thames. This is the evidence/terrain preview for extending the 1900 model; the regional relief has not yet been historically corrected or made into a flood simulation.
- [Flood the 3D landscape](docs/index.html?flood=1): raise a uniform river level over a 1.22 km² test area, compare the dry scene and inspect views of Three Mills and the sewer crossing. Water reaches only connected ground across the modelled banks. This first geometric version omits flow timing, rainfall and drainage; existing interpreted terrain and structure heights are retained.
- Interactive [flood experiment](docs/flood-demo.html): run a one-hour rising-water, western-surge or rainfall scenario around the c1900 Manor Road drainage crossing; compare a working culvert with a blockage, replay results and download the selected frame. These are controlled experiments on a bounded historical terrain model, not calibrated reconstructions of individual floods. See the [model and validation notes](scenes/channelsea-sewer-panorama/TOPOGRAPHY_RESEARCH.md#interactive-flood-demo).
- District exploration: choose **Fly over the district** or select 99 destinations including all 63 factory groups from **Fly to**. WASD or the pad moves, Q/E or Lower/Higher changes height, and the speed selector controls travel speed. Click the expanded map to fly to a location. Home/reset or **Return to the bridge** restores bridge movement. Flight is a viewing tool with no building collisions.
- Bounded bridge movement: WASD or hold the direction buttons; north/south buttons cross the walkway. Drag/arrow keys turn, plus/minus zoom, and Home/reset restores position and view.
- Six story views: working river, Abbey Mills, Bromley gasworks, homes beside West Ham Gas Works, northern streets and the corn mill.
- Location map showing the live camera position, movement boundary and horizontal field of view.
- Great Eastern Railway northern boundary: a mapped embankment corridor with tracks and bridge openings; [railway evidence and review notes](scenes/channelsea-sewer-panorama/GREAT_EASTERN.md) distinguish the plan from provisional levels and junction detail.
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

`npm test` runs every `scripts/check_*.mjs` and summarises passes and failures (no npm packages are installed; the scripts only need Node).

## GIS exports

The model data is written in a local scene frame, metres east and south of the sewer bridge origin recorded in `docs/data/ground-plan.json`. Two scripts convert it back to British National Grid (EPSG:27700) so the reconstruction can be opened in QGIS or any GIS, independent of the browser renderer:

```sh
npm run export:gis   # or run the two scripts below directly
python3 scripts/export_terrain_geotiff.py --verify   # terrain grids → exports/gis/terrain/*.tif (needs numpy, tifffile)
python3 scripts/export_geopackage.py --verify        # footprints, water, roads → exports/gis/west-ham-model-1900.gpkg (needs geopandas, pyogrio, shapely)
```

Scene-Y rasters hold the renderer's vertical unit; the `*-odn.tif` variants add the provisional ODN offset from `terrain-1900.json`, which is a working assumption rather than a survey calibration. `exports/` is ignored by git; regenerate after changing the model data. See [GIS export notes](scenes/channelsea-sewer-panorama/GIS_EXPORTS.md) and the [portability plan](MODEL_PORTABILITY_PLAN.md).

Browser checks cover view selection, bounded camera movement, keyboard/pointer controls, zoom, map/evidence dialogs, mobile overflow and WebGL failure. Screenshots and the latest report are in [review/](scenes/channelsea-sewer-panorama/review/). These are software-rendered Chromium checks, not a physical-phone performance assessment.

The scene renders on interaction and resize, with a timed animation loop only while movement is held. Static meshes are batched by material. A 512 × 384 reflection pass follows the camera; the directional shadow map is rendered once for the static scene. The latest focused terrain review records 20 main-pass draw calls (about 4.2 million triangles), plus 19 reflection-pass calls. These are separate rendering costs. Terrain data and a generated mud texture add to the local renderer and scene data. Phone and website development are currently deferred at the author’s request.

London VIII.32, VIII.22 and VIII.42 have now been inspected. The author’s wider OS screenshot extends housing coverage eastwards. The scene also includes the continuous raised sewer, mapped railway routes, seven factory-range studies, interpreted gardens and Abbey Mill without a windmill. See the local reference ledger. Next research priority: improve sheet registration with multiple control points, identify individual factory buildings in figures 3 and 4, and fit photograph landmarks to the camera. The bridge was rebuilt during 1900–1902; a final scene date must account for that change.

The 24 September visual pass adds varied factory rooflines and loading facades, metre-scaled brick/slate/timber materials, surface relief, damp staining, static shadows and soft ground-contact shading. The river reflects the actual scene and the mud has irregular relief and wetter edges. This remains an interpretive reconstruction; individual buildings and camera alignment need further work. See [the refinement record](scenes/channelsea-sewer-panorama/REALISM.md).

The latest [terrain pass](scenes/channelsea-sewer-panorama/TERRAIN.md) adds detailed mud and depth-aware water north and south, a raised Mill Mead bank, 19 allotment sheds, irregular coal loads and a boarded Abbey Mill without a windmill. Fifteen approximate southwest terrace groups and 20 industrial ranges extend the distant landscape. Eight supplied map screenshots, including the dated 1905 comparison, are archived with local source notes. Use `python3 scripts/review_terrain.py` for the current focused desktop render checks.

The subsequent [lighting and infrastructure pass](scenes/channelsea-sewer-panorama/LIGHTING_AND_INFRASTRUCTURE.md) supersedes the earlier lighting setup and flat railway levels. It adds 50 map-traced road/lane studies with provisional grey/brown period surfaces, raised railway embankments and crossings, and separate Three Mills landmarks. The sediment mask now protects dry ground from wet-mud shading. Latest desktop exports and error checks are `review/lighting-*.png` and `review/lighting-checks.json`; earlier rendering counts describe earlier passes.

## GitHub Pages

The [river network expansion](scenes/channelsea-sewer-panorama/RIVER_NETWORK.md)
adds provisional bank relief along the existing GIS channels and records the
new City Mills, fire-insurance and marsh-housing references. The 1948 aerial
is a later comparison; its 1930s embankments are excluded from the c1900 scene.

A 56-second landscape social video, with a lower camera route and local voiceover,
can be exported from the same scene. Preview the camera with `?film=1&quality=full`.
See [the social film workflow](scenes/channelsea-sewer-panorama/SOCIAL_FILM.md).
Local MP4s, subtitles and review frames live in `exports/`, outside the published site.

The public website is the `docs/` folder, which now holds the redesigned front end (full-viewport scene, scroll-driven chapters, eased camera transitions, poster frame and self-hosted type; see `docs/README.md`). The previous front end is preserved unchanged in `docs0/` and can be served locally the same way. GitHub Pages publishes from branch **main**, folder **/docs**, at https://jimclifford.ca/west-ham-and-the-river-lea/ (the standard GitHub Pages address redirects to the account’s existing custom domain). The `.nojekyll` marker serves the static assets without Jekyll processing. All runtime imports and asset URLs are relative, so the project URL works without a custom domain.

Generated scene data and the bundled Three.js renderer are committed: GitHub does not need to run Python or install packages to serve this site. After changing a generator, regenerate its outputs under `docs/data/` before committing. Browser rendering still requires WebGL2 and sufficient device memory; the detailed desktop scene has not been tuned for low-powered phones.

The book PDF, reference photographs/maps, original model archive, local planning/memory and review screenshots stay outside the public repository. Their local paths in research ledgers document provenance and are not website dependencies.

The [completed factory coverage pass](scenes/channelsea-sewer-panorama/FACTORY_BUILDINGS.md) adds 507 individually recorded ranges across 43 works within the agreed district. Open `factory-atlas.html` on the local site to inspect buildings and sources. Heights and most roofs remain reconstruction estimates.

The [district street and bridge pass](scenes/channelsea-sewer-panorama/STREETS_AND_BRIDGES.md) adds High Street, Sugar House Lane and connecting streets, with the five pre-1933 High Street crossings. Use **Fly to → Bridges** for close views. Three lane connections remain provisional, and the western Three Mills approach has a documented housing-registration gap.

## Current modelling checkpoint

A [dated elevation model](scenes/channelsea-sewer-panorama/TOPOGRAPHY_RESEARCH.md)
now adjusts about 26.9 hectares around Abbey Mills, Mill Mead and
Plaistow Level using thirteen reviewed 1890s ground observations and three Manor
Road surface heights, with a provisional ODN reference. Four ground interpolation
areas and a separate road profile preserve intervening structures; about 16.5
hectares has full interpolation support. The 1900
surface keeps source dates, uncertainty and coverage separate; the future 1850
scenario requires its own observations and period geometry. The principal flood
cases are 1888, 1897, 1904 and 1928, before the major 1930s works; 1898 is a
secondary rainfall case. Absolute Three Mills flood levels remain unresolved. Use
`?terrainEpoch=baseline` to compare the earlier inferred terrain. Rebuild the
overlay with `python3 scripts/build_historic_elevation.py` after changing its
terrain/infrastructure inputs, then regenerate the scene manifest.

The 1900 terrain also includes about 206 m of the mapped Plaistow drain east of
Manor Road. Source traces and four sluice locations are retained in
`data/maps/historic-drainage-1900.json`. Its bed and standing-water levels are
explicit assumptions; the possible railway/road culvert is not an enabled
flood connection. Run `python3 scripts/check_historic_drainage.py` alongside
the elevation checks and `python3 -u scripts/review_historic_elevation.py --drainage-only`
for the baseline, revised-ground and tide comparison.

The [drainage connection review](docs/drainage-connections.html) compares five
possible connection/gate scenarios without calculating flood levels or flows.
The candidate crossing is about 45 m long and intersects two railway routes.
About 182 m of Manor Road is now restored at the crossing, profiled from three
1890s road spot heights (6.6, 6.2 and 6.5 feet). Its local ground and adjoining
railway alignment have been adjusted together. Railway formation height and
culvert dimensions remain provisional; east-to-west passage is the preferred
connection scenario, with blockage and reverse flow retained for comparison.
Rebuild this review with `python3 scripts/build_drainage_connections.py`, check
it with `node scripts/check_drainage_connections.mjs`, and use the terrain
browser review's `--connections-only` option to exercise the interactive page.
Use `--manor-only` for the road/railway views, and run
`python3 scripts/check_manor_road.py` plus `node scripts/check_manor_road.mjs`
to check source heights, ground contact, railway clearance and epoch isolation.
The same review now includes four provisional culvert sections, with road-cover
checks and a deeper alternative requiring approach-channel excavation. Its working
opening is 0.9 m wide by 0.6 m high; these dimensions are assumptions. A mapped
road-over-rail bridge farther south exposes a conflict in the inherited constant
railway height, so that formation must be revised before hydraulic use. Run
`node scripts/check_culvert_section.mjs` to check the section scenarios.

The eastern strip between Channelsea and the Woolwich railway now has 137
individually reviewed roof ranges across twenty additional factory/context sites.
These replace the repeated sketch blocks and rough frontage envelopes with OS
exteriors, including three roofs traced directly where the supplied extract was
incomplete. Open courts remain open. The district now has 681 ranges at 63 sites;
627 ranges use supplied footprints and sixteen use direct map traces.
New eaves, storeys and gables are explicit estimates; this pass does not assert
fire-insurance coverage. Use **Fly to → Channelsea — eastern works and market**.
The next context pass adds the mapped open ground at Stratford, Caledonian and
Halling wharves, preserving the earlier yards and their stock. Victoria Stone
Works now has its twenty open working cells marked on the ground; their exact
apparatus and construction remain unresolved.

The supplied GIS railway layer also exposed the missing northwest connection.
That route now joins the Woolwich branch through the mapped Stratford low-level
underpass, with interpreted heights and a short continuation of the Great Eastern
main line. The eleven depot sidings share three complete throat segments with
matched rail heights. Use **Fly to → Stratford — northern railway connections**.
Junction layout is checked against the large-scale OS sheets; the GIS supplies
the broad routes. A closer station review corrects the running pair past
Stratford Market's covered structures and preserves the mapped booking-bridge
crossing, with earth slopes kept clear of the station bodies.
The paired street review also corrects eighteen housing roof bands and removes
four duplicate envelopes drawn over rear gardens. Housing heights and household
counts remain estimates.
The detailed source and validation record is in
[FOOTPRINT_ALIGNMENT.md](scenes/channelsea-sewer-panorama/FOOTPRINT_ALIGNMENT.md).


The regional plan layer now covers historic West Ham plus a 3 km buffer, while
existing 3D buildings are progressively matched to the supplied footprints.
The first pass corrects 26 factory ranges and the Abbey Mills station complex.
The ink-works and Imperial Saw Mills compound passes add 27 corrected ranges,
bringing the factory total to 53 while preserving the Goad compartments and roof
interpretations. The Oil Wharf pass brings that total to 62, clears two spurious
blocks from open ground and restores four petroleum tanks plus a disused tank.
Cook’s Road now clears the mapped stores and mill frontage.
The Howards pass adds 83 source-linked ranges in 53 reviewed groups, bringing
the district total to 145. Its old mill is traced directly from OS, eighteen
chimney positions are corrected, and the waterfront bank retains the millrace.
The Sugar House / cooperage and Winstone pass brings the total to 163, including
three added low compartments. It corrects lane access and the chimney opening,
and restores the mapped cooperage working yard. The western continuation adds
38 source-linked ranges at Hodson, Dane, Winstone and Wildash, bringing the total
to 201. Eleven omitted rooms are added and two duplicate sheet-edge models are
removed; four chimney positions, the riverbank and lane clearance are corrected.
The Crystal Wharf / Barber pass adds 21 source-linked ranges, bringing the total
to 222. It replaces four open-yard blocks with the mapped northern factory row,
adds thirteen omitted rooms, corrects two chimneys and restores two working yards.
All 40 eastern Sugar House Lane ranges now have source links. The High Street
starch, tin-box and confectionery pass adds 18 linked ranges, bringing the total
to 240, with four omitted rooms and a corrected Hogarth chimney. The Bow Bridge
bone and chemical works pass brings the total to 250. Its 17 ranges include twelve
supplied-outline matches and five rooms traced directly from OS, replacing the
earlier provisional transfers. Two omitted rooms and a mapped 50-foot retort
chimney are added, with the adjoining riverbank corrected locally.
Hunt's neighbouring soap works now has ten source-linked ranges, bringing the
district total to 260 at sixteen sites. The furnace rooms, office/laboratory and
engine room are restored; two chimney positions and two local bank controls are
corrected. Shared factory-room divisions and elevations remain interpreted.
The Lascelles and British Ultramarine pass adds six source-linked ranges, bringing
the total to 266 at eighteen sites. It records two narrow OS sheet-join corrections,
retains the Ultramarine chimney opening and clears the southern lane frontage.
Williams wharf and French Asphalte add 17 source-linked ranges, bringing the total
to 283 at nineteen sites, plus two rooms directly traced from OS. The omitted
room 704 is restored, a boundary lean-to is reassigned to Ultramarine, and two
chimneys and the adjoining lane are aligned. Missing sheet-edge geometry is
recorded separately from supplied outlines; existing elevations are retained.
The refinery, machinery-depot and printing-works pass adds seventeen source-linked
ranges, reaching 300 at twenty sites. Five omitted rooms are restored, the northern
storage shed is directly traced, and both chimneys follow mapped bases. Local
lane and pavement corrections retain the façades through a narrow frontage.
Abbey's supporting group now adds eight mapped buildings, four lower annexes and
five revised access routes; roof forms and elevations remain interpreted.
See [the continuation notes](scenes/channelsea-sewer-panorama/CONTINUE_FOOTPRINT_MATCHING.md)
for the next sites, authoring files, rebuild commands and completed checks.

The Kendrick / Usher continuation adds eight source-linked ranges, reaching 308
at twenty-three sites. Two missing rooms are restored, both Kendrick sheet-seam
gaps have explicit OS completions, and Usher's main factory is directly traced.
The scene now has 546 ranges; the 40 ft chimney follows its mapped base and the
northern lane clears the corrected walls. Existing heights and roofs are retained.

Northern Three Mills adds twenty source-linked ranges, reaching 328 at twenty-four
sites. The scene has 547 ranges after restoring timber room 828. One omitted
outline is directly traced and one small Goad-only outbuilding remains provisional.
Mapped chimney/tank positions and a revised works passage complete this northern
pass. The southern continuation matches eight more ranges and three tanks,
reaching 336 source-linked ranges. House/Clock Mills and the wharf ranges are next.

The House/Clock Mill and wharf continuation aligns the remaining eight mapped
Three Mills ranges, bringing the district to 344 source-linked ranges plus eleven
direct OS traces. Clock-tower and kiln details follow the corrected footprint;
the mill-court bend and eastern footpath now clear the mapped walls. One small
Three Mills outbuilding remains a provisional Goad transfer.

Ratner and Albion now have seven source-linked ranges, with their mapped
courtyards restored. One former soap-yard boundary model and its inferred chimney
are removed after OS review. The scene has 546 ranges, 89 chimneys and 351
source-linked ranges; eleven more ranges have direct OS traces.

Bow Flour Mills, rubber/oilskin and felt works add twelve source-linked ranges.
Two industrial blocks over domestic terraces and their inferred chimney are
removed; the rubber works courtyard stays open. Bow Road and its bridge move
locally onto the mapped carriageway, and two wharf-bank controls clear Albion
Wharf. Current totals: 545 ranges, 88 chimneys, 363 source-linked ranges and
eleven direct OS traces. Heights and roofs remain interpretations.

Cook’s East London Soap Works, Bow Bridge Wharf, Magnet Wharf and the limeworks
now have 48 more source-linked ranges. Four Cook chimneys and two existing lime
kilns are repositioned, with heights retained. Local road and bank corrections
clear the mapped wharf walls. Current totals: 545 ranges, 88 chimneys, 411
source-linked ranges and eleven direct OS traces.

St Thomas corn mill, Smith’s brush/fibre works, Bow Brewery and the mineral-water
works add twenty source-linked ranges. The mill’s covered water interface and
Smith warehouse overhang remain; the road shortcut through the mill is removed.
The mineral-water ranges now clear St Mary’s Church and the brewery courtyard
stays open. Current totals: 545 ranges, 88 chimneys, 431 source-linked ranges
and eleven direct OS traces.

Jeffrey’s marine glue works, Marshgate chemical works and Alderson’s rope works
add twenty-five source-linked ranges and one directly traced ropewalk. An
unsupported workshop is removed from the rope yard, and three chimney bases
follow the maps. Totals: 544 ranges, 88 chimneys, 456 source-linked ranges and
twelve direct OS traces. Heights and internal divisions remain interpretations.

Ritchie’s jute mill, Crown/Johnson works, the London and Glasgow Foundry,
Ornamental Moulding Works and the western chemical buildings add 37 source-linked
ranges and one directly traced roof. The complete large Crown Chemical Works
roof is included. Local road approaches now clear the mapped walls. Current
totals:544 ranges, 88 chimneys, 493 source-linked ranges and thirteen direct traces.
