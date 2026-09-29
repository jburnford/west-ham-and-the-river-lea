# Continue building-by-building footprint matching

Checkpoint: 28 September 2026. The author wants an approximate but convincing
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

- 26 source-linked factory ranges at nine sites, including 11 Slater & Palmer /
  Marshgate Mills ink-works ranges. Registry:
  `data/maps/factory-footprint-alignment.json`. It retains original outlines,
  source IDs, changes in position/area and previous roof/height interpretations.
- Abbey Mills main station: corrected orientation (~35.88°), main cross and two
  lower rear boiler wings. Source outline 459 includes the whole attached
  complex; do not enlarge the ornate station to fill it. Chimney bases use
  source IDs 257848 and 277380. Authoring/runtime plan:
  `data/maps/abbey-station-plan.json`, `docs/data/abbey-station-plan.json`.
- Source fit is a geometric comparison, not a historical-accuracy score.
- The broader scene has 43 factory sites, 507 ranges, 89 factory chimneys,
  196 terrace rows / 3,204 houses and 81 modeled yards.
- Housing rows have not yet been aligned to the supplied regional footprints.

Useful local destinations:

- `http://localhost:4175/?view=pumping-station`
- `http://localhost:4175/?view=factory-940`
- `http://localhost:4175/?view=sawmill-yard`
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

Finish the Abbey Mills site around the corrected landmark: review the southern
outbuilding (source 6687), small buildings near the chimney bases and their
relationship to access paths. Then finish the ink-works compound ranges,
especially source polygons shared by ranges 25/26 and 28/29. Review the Imperial
Saw Mills complex as a group, then Howards and the remaining factory sites.

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
python3 scripts/build_factory_yards.py
python3 scripts/build_housing_detail.py
python3 scripts/build_regional_footprints.py
python3 scripts/build_scene_manifest.py
```

The regional raster build requires the local research extract and the existing
`/home/jic823/swipe_map/site/data/Water_1895.geojson`. Abbey's fitter also needs
the local footprint extract; its saved JSON is sufficient to run the website.
No generator runs on GitHub Pages. The cache manifest must match public modules
and assets after changes.

Relevant checks:

```sh
python3 scripts/check_factory_buildings.py
python3 scripts/check_factory_footprint_alignment.py
python3 scripts/check_abbey_station_plan.py
python3 scripts/check_factory_yards.py
python3 scripts/check_housing_detail.py
python3 scripts/check_western_completion.py
node scripts/check_district_navigation.mjs
python3 scripts/review_factory_buildings.py --station-only --url http://127.0.0.1:4175
python3 scripts/review_factory_buildings.py --footprints-only --url http://127.0.0.1:4175
```

Geometry checks, 77 navigation destinations, four Abbey views and five factory
alignment views passed before this checkpoint. Browser screenshots and diagnostics
are local under `scenes/channelsea-sewer-panorama/review/`. No mobile audit.
Latest public asset revision: `adb95f9a8f13`.

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
stale quickly. Last coverage audit observed 1,083 marks (837 spots, 246 BMs),
with about 50% of West Ham within 500 m of a mark. The author then began working
on the southwest. Do not overwrite or merge their extraction scripts/readings.

The prototype-only `prepare_historic_height_controls.py` is not an importer for
the expanded schema. Separate ground, banks, structures and benchmark mounting
contexts. Values are reported in feet above Liverpool OD; no Newlyn conversion
or scene-y alignment has been established. Do not apply a 0–40 ft cutoff across
the wider region. The 2003 terrain mosaic is downloaded but not integrated.
See `TOPOGRAPHY_RESEARCH.md` for coverage and datum limitations.
