# Matching 3D models to regional footprints

First implementation pass, 28 September 2026: 26 factory ranges at nine sites
now use individual outlines from the author's `london_buildings_1891-96_corr_v1.gpkg`.
The initial emphasis is Slater & Palmer / Marshgate Mills (11 ink-works ranges),
with clear matches at the marine glue works, chemical works, rope works, Sugar
House Lane, New Imperial Saw Mills, both gasworks and Oil Wharf.

## Method and limits

`data/maps/factory-footprint-alignment.json` is the authoring register. Each entry
retains the original outline, source feature ID, corrected world polygon,
previous roof interpretation and a comparison of area, position and orientation.
The scene generator reads this register after the original Goad/OS traces, so
those earlier traces and their building-use evidence remain recoverable.

Source geometries are transformed from EPSG:3857 through BNG into the existing
scene origin E538900,N183209. Outlines are simplified at 0.05 m. The source's
orthogonal orientation closest to the prior roof axis controls roof direction;
existing eaves heights, roof rise, bay count and roof type remain unchanged.
This changes plan geometry, not the terrain datum or building-height evidence.

The selection uses individual source polygons with nearby centroids and modest
area changes. Ink-works candidates were reviewed together on a site overlay;
all accepted outlines were visually inspected in the before/after comparison.
No source polygon is assigned to two models. Polygons with holes/multiple parts,
shared compartments, major shifts, or conflicts with current riverbanks are
recorded for later review rather than silently absorbed into one model.
The landmarks with bespoke architectural interpretation also need separate review.

Original street, holder and neighboring-building clearances still take precedence
in the final renderer. Seven corrected outlines have small further cuts; the
largest remaining differences are beside the rope-works street and Sugar House
Lane. The rendered/source overlap is at least 89.2%, with a median of 100%.
This is agreement with this dataset, not proof of historical positional accuracy.

The existing 43 factory sites, 507 ranges and 89 chimneys are retained. Yard stock
and housing-yard clearances were regenerated against the changed buildings. The
regional plan tiles are also regenerated so the flat layer reflects the new masks.
Housing rows have not yet been realigned to the supplied footprints.

## Rebuild and checks

`prepare_factory_footprint_alignment.py` prepares the first-pass register from the
private source extract. Routine scene rebuilds need only the saved register:

```sh
python3 scripts/build_factory_buildings.py
python3 scripts/build_factory_yards.py
python3 scripts/build_housing_detail.py
python3 scripts/build_regional_footprints.py
python3 scripts/build_scene_manifest.py
python3 scripts/check_factory_buildings.py
python3 scripts/check_factory_footprint_alignment.py
python3 scripts/check_factory_yards.py
python3 scripts/check_housing_detail.py
python3 scripts/check_western_completion.py
python3 scripts/review_factory_buildings.py --footprints-only --url http://127.0.0.1:4175
```

Private comparison images, original generated factory data, deferred candidates
and measured overlap improvements are in `reference/footprint-model-alignment/`.
Browser renders are in `scenes/channelsea-sewer-panorama/review/`.

Next passes should review compound buildings as groups, keeping their Goad
compartments and roof forms while correcting their external boundary. River-edge
buildings need a paired review of the footprint and bank. Terraced housing needs
row-body, rear-extension and yard geometry considered together, rather than
stretching an entire row to a single source polygon.

Final verification: factory geometry/chimney checks, corrected-outline comparisons,
yard clearances, housing detail, western railway/industry checks and all 76
navigation destinations passed. Five desktop browser views (ink works overhead
and lane, West Ham gasworks, sawmill and Bromley gasworks) rendered without
browser/shader errors and were visually inspected. Median source intersection-
over-union for the corrected ranges improved from 63.5% to 100% after rendering.
JavaScript/Python syntax checks and `git diff --check` passed. Public cache
revision: `4abe1c29f4d6`. Local only; no commit or deployment.

The regional background was also cut away from the detailed ground envelope
after visual review showed it obscuring submerged riverbeds. Its ground and
context-water meshes now extend outside that envelope only; the detailed tidal
bed and water geometry retain their original depths.
