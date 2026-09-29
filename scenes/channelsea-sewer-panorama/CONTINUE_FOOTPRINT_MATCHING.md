# Continue building-by-building footprint matching

Checkpoint: 29 September 2026, recovered after WSL restart. The author wants an approximate but convincing
circa-1900 reconstruction. Continue adjusting existing 3D models to the supplied
building footprints, site by site. Exact architectural accuracy is not required,
but record the distinction between map evidence and interpreted elevations.

## Start here

1. Read local `MEMORY.md`, this file, `FOOTPRINT_ALIGNMENT.md` and
   `ABBEY_STATION_ALIGNMENT.md`.
2. Check `git status` before editing: another workflow is collecting heights.
3. The live site is **docs/**, normally served on **localhost:4175**. Check the
   existing server before starting another. `docs2/` is an alternative version;
   leave it alone. Do not push/deploy unless requested.
4. Inspect current data and source polygons before assuming a model matches one
   source feature. A single polygon can combine several factory compartments.

## Completed model alignment

- 163 source-linked factory ranges at ten sites, including 24 Slater & Palmer /
  Marshgate Mills ink-works ranges. First-pass registry:
  `data/maps/factory-footprint-alignment.json`. It retains original outlines,
  source IDs, changes in position/area and previous roof/height interpretations.
- Ink-works continuation: `data/maps/ink-works-footprint-alignment.json` adds 13
  ranges in ten explicit groups, including shared outlines for 25/26, 28/29 and
  9/10, plus three corrected chimney bases. Source 2452's chimney hole is retained.
  A 0.77 m² source overlap at the eastern store is recorded and cleared in the
  renderer. Firelighter and warehouse 24 have no source outline in the extract;
  their Goad models remain pending separate OS tracing.
- Imperial Saw Mills continuation: `data/maps/sawmill-footprint-alignment.json`
  adds 14 ranges in eight groups, completing all 16 existing site-797 ranges.
  Seven mill compartments share a corrected outline; the northern Towers
  slaughterhouse retains its separate courtyard arrangement. The internal boiler
  chimney moves with its parent, without claiming a mapped base. Cook’s Road is
  retraced locally in `district-road-traces.json`, preserving the bridge approach.
  Additional plant outline 455070 has no existing model and remains deferred.
- Oil Wharf continuation: `data/maps/oil-wharf-footprint-alignment.json` corrects
  five ranges and adds four, retaining the earlier filling-shed match. Two
  spurious rectangles are removed with their prior records retained. The ten
  resulting ranges include the adjacent dwelling row, identified separately.
  Four petroleum tanks and one northern disused tank follow OS/Goad evidence;
  two tank circles absent from the extract are traced and locally registered.
  A named working-yard envelope supplies barrel stock and tank exclusions.
  Northern Cook’s Road now clears the stores; sawmill frontage and bridge remain.
- Howards continuation: `data/maps/howards-footprint-alignment.json` aligns 83
  ranges in 53 reviewed groups containing 101 supplied source polygons. The old
  mill (644) is directly traced from OS; shed 524 moves with its Goad neighbour;
  shed 620 remains explicitly deferred. All 86 site-260 ranges are accounted for.
  Eighteen chimney positions are corrected: two mapped bases and sixteen local
  department transfers. `data/maps/city-mills-bank-alignment.json` reconciles
  twelve bank vertices with the waterfront buildings while retaining the millrace.
  The saved source geometry, earlier compartments and roof/height evidence remain.
- Sugar House / cooperage and Winstone continuation:
  `data/maps/sugar-house-footprint-alignment.json` adds 18 source-linked ranges
  in 14 groups (19 source polygons), including three previously omitted low
  cooperage compartments. Together with earlier range 14, 19 of site 964's 31
  ranges are aligned. The five-storey Sugar House keeps its paired roof. One
  chimney moves into its mapped sawmill opening, with a narrower interpreted
  base; height retained. Sugar House Lane and its works passage are re-read
  locally. A separate mapped cooperage-yard envelope restores its working surface
  and two small timber groups. Crystal Wharf and Barber ranges 17–28 await review.
- Abbey Mills main station: corrected orientation (~35.88°), main cross and two
  lower rear boiler wings. Source outline 459 includes the whole attached
  complex; do not enlarge the ornate station to fill it. Chimney bases use
  source IDs 257848 and 277380. Authoring/runtime plan:
  `data/maps/abbey-station-plan.json`, `docs/data/abbey-station-plan.json`.
- Source fit is a geometric comparison, not a historical-accuracy score.
- Abbey supporting group: eight buildings plus four lower annexes, including
  source 6687, both chimney-side buildings, the lodge and southwest cluster.
  `data/maps/abbey-supporting-buildings.json` retains source polygons and five
  period-map access traces. These volumes use the station plan and shared factory
  renderer, separately from the industrial ranges. Heights and roofs remain
  interpreted. Tiny features 1064653 and 1162448 are explicitly deferred.
- The broader scene has 43 factory sites, 512 ranges, 89 factory chimneys,
  196 terrace rows / 3,204 houses and 83 modeled yards.
- Housing rows have not yet been aligned to the supplied regional footprints.

Useful local destinations:

- `http://localhost:4175/?view=pumping-station`
- `http://localhost:4175/?view=factory-940`
- `http://localhost:4175/?view=sawmill-yard`
- `http://localhost:4175/?view=factory-9001`
- `http://localhost:4175/?view=city`
- `http://localhost:4175/?view=factory-964`
- `http://localhost:4175/?view=west-ham-region`

## Source data

Original author-supplied file (read only):
`/mnt/c/Users/jic823/Dropbox/2026/london_buildings_1891-96_corr_v1.gpkg`.
Its building layer has 1,299,040 features in EPSG:3857. The study-area selection
has 238,052 features. Research extracts are outside Git:

- `reference/historic-building-footprints-2026-09-28/current-scene-buildings-bng.geojson`
- `reference/historic-building-footprints-2026-09-28/west-ham-buffer-buildings-bng.geojson.gz`
- `reference/footprint-model-alignment/deferred-candidates.json`
- `reference/footprint-model-alignment/corrected-ranges.png`
- `reference/abbey-mills-alignment/source-shapes.json`

BNG origin: E538900,N183209. Scene x = E − 538900; z = 183209 − N.
Research vectors retain original `sourceFid`. Runtime footprint plans are
115 transparent tiles plus an overview (~4 MB), not thousands of new meshes.
They cover historic West Ham plus a 3 km buffer. Regional ground is provisional.

## Next working sequence

Next review the remaining Sugar House Lane groups: Crystal Wharf / Dane / Talbot
and Barber (site 964 ranges 17–28), then western site 947 and sites 256/572/573.
The cooperage and Winstone pass is complete. Crystal Wharf's earlier ranges
24–26 partly cover open yard; inspect the Goad labels and OS buildings before
reclassifying or replacing them. Do not snap these rectangles to nearby sources.
The Howards, Oil Wharf, Imperial Saw Mills and ink-works compound passes
are complete apart from explicit omissions; the firelighter
and warehouse 24 remain explicit source omissions needing direct map tracing.
Howards shed 620 also needs a direct map trace. Shed 524 retains a transferred
Goad outline without claiming an individual supplied-footprint match.
Abbey's supporting buildings and access pass is complete;
see `ABBEY_STATION_ALIGNMENT.md` for the two deferred small features and its
separate rebuild sequence.

For each site:

1. Overlay current models, source polygons and period map. Inspect the image.
2. Decide whether each source feature represents one model or several attached
   compartments; preserve useful Goad divisions, uses, floor evidence and roofs.
3. Add explicit source-linked authoring corrections. Avoid blind nearest-polygon
   snapping and do not rerun a broad automatic selection without reviewing it.
4. Move attached features with their parent where appropriate. Check roofs,
   chimneys, streets, riverbanks, holder rings and neighboring volumes together.
5. Regenerate dependent yards and footprint masks, run appropriate geometry
   checks and inspect actual browser views.
6. Record completed and deferred buildings, then continue to the next site.

Housing needs row bodies, individual rear extensions and shared yard boundaries
considered together. A whole terrace should not be stretched to fit a single
house polygon. Some conflicts require re-registering streets or riverbanks in
the same pass. Old Lea connectivity/locks remain a separate deferred task.

## Build and review

Main authoring sources are under `data/maps/`; generated site data under
`docs/data/`. Do not edit only the generated JSON. Typical factory rebuild:

```sh
python3 scripts/build_factory_buildings.py
python3 scripts/build_infrastructure.py
python3 scripts/build_factory_yards.py
python3 scripts/build_housing_detail.py
python3 scripts/build_regional_footprints.py
python3 scripts/build_scene_manifest.py
```

If changing the City Mills bank register, rebuild `build_panorama_data.py`
before this sequence and `build_river_network.py` after infrastructure but before
the final manifest. Saved Howards JSON is sufficient for routine factory builds;
`prepare_howards_alignment.py` additionally needs the private source extract,
OS mosaic and `reference/footprint-model-alignment/howards-before.json`.

The regional raster build requires the local research extract and the existing
`/home/jic823/swipe_map/site/data/Water_1895.geojson`. Abbey's fitter also needs
the local footprint extract; its saved JSON is sufficient to run the website.
No generator runs on GitHub Pages. The cache manifest must match public modules
and assets after changes.

Relevant checks:

```sh
python3 scripts/check_factory_buildings.py
python3 scripts/check_factory_footprint_alignment.py
python3 scripts/check_sawmill_footprint_alignment.py
python3 scripts/check_oil_wharf_alignment.py
python3 scripts/check_howards_alignment.py
python3 scripts/check_sugar_house_alignment.py
python3 scripts/check_abbey_station_plan.py
python3 scripts/check_factory_yards.py
python3 scripts/check_housing_detail.py
python3 scripts/check_western_completion.py
python3 scripts/check_district_streets.py
node scripts/check_district_navigation.mjs
python3 scripts/review_factory_buildings.py --station-only --url http://127.0.0.1:4175
python3 scripts/review_factory_buildings.py --footprints-only --url http://127.0.0.1:4175
python3 scripts/review_factory_buildings.py --ink-only --url http://127.0.0.1:4175
python3 scripts/review_factory_buildings.py --sawmill-only --url http://127.0.0.1:4175
python3 scripts/review_factory_buildings.py --oil-wharf-only --url http://127.0.0.1:4175
python3 scripts/review_factory_buildings.py --howards-only --url http://127.0.0.1:4175
python3 scripts/review_factory_buildings.py --sugar-house-only --url http://127.0.0.1:4175
```

Geometry checks, 77 navigation destinations, four Abbey views and five factory
alignment views passed before the initial checkpoint. The continuation adds
supporting-building and route-clearance checks; all seven Abbey browser views
passed and were visually inspected.
The ink-works continuation passes the geometry/clearance checks and four focused
browser views, including the retained chimney opening and three moved stacks.
The sawmill continuation passes its group/stack/road checks, the district street
audit and five visually inspected browser views. All 16 mill/Towers ranges and
the transferred chimney reached the renderer, without browser/shader errors.
The Oil Wharf pass adds six inspected browser views, covering the four-tank
group, northern disused tank, stores, road and neighbouring sawmill frontage.
Diagnostics confirm ten ranges and five tanks; geometry and clearance checks pass.
The Howards review was interrupted after its first image before the WSL restart.
On 29 September all seven views were rerun and visually inspected; all 86 ranges
and 18 corrected chimneys reached the renderer with no browser/shader errors.
Howards source agreement is at least 99.157% per rendered group. Factory, all
alignment, yard, housing, Abbey, western, street and 77-destination checks pass.
The Sugar House pass also passes source/compartment, roof-direction, chimney-hole,
road-junction and yard checks. Minimum rendered group agreement is 99.855%.
All six final browser views passed and were visually inspected after the yard
correction; diagnostics confirm all 31 eastern ranges and the corrected chimney,
with no browser/shader errors.
Private source comparisons and the immutable pre-pass snapshot are under
`reference/footprint-model-alignment/sugar-*`; use the snapshot when regenerating
the authoring register. Routine builds need only the saved register.
Oil Wharf, Howards and Sugar House form the 29 September continuation checkpoint
after `7f078c0`. This checkpoint is local; no push or deployment.
Browser screenshots and diagnostics
are local under `scenes/channelsea-sewer-panorama/review/`. No mobile audit.
Latest local asset revision: `f8b93c9befe9` (all public asset hashes verified).

## Preserve these corrections

- Regional ground and context-water meshes exclude the detailed ground envelope;
  otherwise the flat background obscures submerged riverbeds.
- Retain the original detailed tidal range; historical elevation data has not
  yet established a replacement vertical datum.
- Source/date differences matter. Modern station photographs supply surviving
  architecture, while the period map/engraving supplies the c1900 arrangement.
- Large GeoPackages, LiDAR archives, reference images and review exports remain
  outside Git. `MEMORY.md` is also intentionally local and ignored.

## Parallel height work — leave with the author and Claude

The actively growing source is **reference/spot-heights/heights.geojson**, not the
older 105-point `readings.geojson` prototype. Re-read it when needed; counts go
stale quickly. The author reports **1,773 distinct marks** during the Oil Wharf
pass; this is an author-reported count, not a new coverage audit. The earlier
1,083-mark audit found about 50% of West Ham within 500 m of a mark. Do not
overwrite or merge their extraction scripts/readings.

The prototype-only `prepare_historic_height_controls.py` is not an importer for
the expanded schema. Separate ground, banks, structures and benchmark mounting
contexts. Values are reported in feet above Liverpool OD; no Newlyn conversion
or scene-y alignment has been established. Do not apply a 0–40 ft cutoff across
the wider region. The 2003 terrain mosaic is downloaded but not integrated.
See `TOPOGRAPHY_RESEARCH.md` for coverage and datum limitations.
