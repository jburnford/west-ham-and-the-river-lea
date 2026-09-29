# Terrain sources and study extent — 28 September 2026

The author requests terrain for **West Ham and the region within 3 km of its
historic boundaries**. Use the existing 1911 county-borough polygon as the working
boundary, rather than modern Newham, the parliamentary constituency or the much
larger registration district. Source: `/home/jic823/swipe_map/site/data/WestHam_1911.geojson`,
GBHGIS unit **10025904**, `g_year=1911`, `g_status=CB`. This is a working historical
extent; any differences from c1900 have not been audited. Its computed area is
20.23 km²; the borough plus an outward 3,000 m buffer in EPSG:27700 is **108.67 km²**.
This expands the terrain research area, not the detailed factory-building brief.

The author considers pre-2007 terrain a useful approximation: the 1930s changes
matter, but the post-2007 transformation was much larger. Aim for a convincing
landscape, not an exact reconstruction of every historical ground level.

## Confirmed data

[EA dated DTM archive](https://www.data.gov.uk/dataset/8275e71e-1516-42a1-bb0c-4fa73807fe2b/lidar-dtm-time-stamped-tiles)
contains pre-Olympic surveys across this area. **2003 should be the first-choice
candidate**, supplemented by other early dates where necessary. DTM removes
surface objects; it does not undo earthworks, industrial fill or land reclamation.

The current [EA OGC catalogue](https://environment.data.gov.uk/spatialdata/survey-index-files/ogc/features/v1/collections/LIDAR_DTM_Time_Stamped_Extents/items?f=json&bbox=-0.063,51.469,0.096,51.583&limit=10000)
returned all 1,115 matching records, with no omitted pages. Intersecting their
footprints with the buffered borough gives:

| Survey year | Coverage of study area |
| --- | ---: |
| 1999 | 20.88% |
| 2002 | 17.61% |
| **2003** | **92.62%** |
| 2005 | 1.59% |
| 2007 | 91.12% |
| 2012 | 97.07% |

These percentages measure the union of catalogue polygons, not verified valid
height pixels. Overlapping tiles/resolutions are not counted twice. Invalid
source polygon topology is repaired before measuring. The 2003 holdings include
0.5 m and 1 m products, principally 22 February, with other February/November
flights. Point checks confirm 2003 records at the model's Three Mills, Abbey Mills
and City Mills anchors and at approximate Stratford and Forest Gate locations.
See `coverage-summary.json` for their full dates, tiles and survey identifiers.

**Important catalogue correction:** the older ArcGIS `LIDAR_Tiles_Catalogues`
service exposed only 2007/2012 entries in the initial small query. The current
OGC catalogue additionally exposes 1999/2002/2003 coverage. Do not repeat the
initial inference that the centre of the scene has no pre-2007 survey.

The [2022 composite DTM](https://www.data.gov.uk/dataset/01b3ee39-da3f-47b6-83da-dc98e73a461f/lidar-composite-digital-terrain-model-dtm-1m)
is available at 1 m, in metres ODN and British National Grid. A **10 m sampled
GeoTIFF has been downloaded** for the entire study envelope, E534400–545600 /
N176400–189100. It is 1,120 × 1,270 float heights and about 5.7 MB on disk. This
is a comparison/reference surface, not the historical model. The separate
National LIDAR index confirms local 2017–18 and December 2020 surveys. Composite
year is not an assertion that every height was surveyed that year.

**The 2003 rasters are now downloaded and reduced to a working mosaic.** Ten
archives (1.76 GB, kept outside Git/publication) contain the selected 1 m products,
with 0.5 m products for two southern-edge tiles where 1 m was not offered.
The build uses 124 distinct rasters intersecting the study area. At 10 m working
resolution, requiring at least half the source pixels in each cell to be valid,
**91.62% of the study area has usable heights (99.56 km²)**. Missing cells remain
NaN; there is no hidden interpolation across water or missing survey coverage.

The working heightfield is 5.69 MB uncompressed; the compressed research package
including heights, source IDs and valid-pixel support is 3.08 MB. Source date,
resolution and checksums remain available for every contributing raster. Latest
2003 date wins valid overlaps, with finer resolution preferred on equal dates.

Approximate **110 × 110 m sample windows**, not exact site levels, give:

| Sample | 2003 median | Modern median | Median paired difference |
| --- | ---: | ---: | ---: |
| Forest Gate (E540500 N185500) | 11.32 m | 11.30 m | −0.05 m |
| Northeastern high ground (E540500 N187500) | 24.13 m | 24.15 m | approximately 0 m |
| Stadium vicinity (E538000 N184500) | 8.12 m | 13.95 m | +5.65 m |

These are screening observations: modern 10 m WCS samples and older 10 m cell
medians differ in aggregation, and geoid/processing/water effects are not yet
corrected. Their difference is not a precise survey of earthwork volumes. Do not
infer a 1900 surface directly from the 2003 valley levels. The comparison image
shows conspicuous Olympic-site changes alongside much more stable regional relief.

The current downloader endpoint is
`https://environment.data.gov.uk/tiles/collections/survey/search` (POST a GeoJSON
Polygon with `Content-Type: application/geo+json`). Its records contain download
URIs; append `?subscription-key=public`. The bare archive URI returned 404 in this
session; the public-key URI returned the dated ZIP. See `download-search.json`
and `selected-downloads.json`, rather than reconstructing tile IDs manually.

## Reconstruction method

1. Build a pre-2007 DTM mosaic, prioritising 2003; preserve survey-date and
   valid-data masks. Compare the modern extract to locate large later changes.
2. Use the older broad relief directly where historic maps and continued street
   patterns support it, especially the rising ground toward Forest Gate and
   Wanstead. Remove remaining modern transport embankments/earthworks locally.
3. Correct the lower Lea using c1890–1900 spot heights, marsh boundaries, roads,
   photographs and known changes. Restore period channels separately, including
   the pre-Prescott-Cut landscape. Do not use LiDAR water returns as river-bed
   measurements. Keep historic bank crests, marsh floors and water elevations
   separate so tidal animation remains coherent.
4. Do not flatten all land above zero: above sea level and below high tide can
   both be true. Historical streets/industrial yards may already have been raised.
   Retain period fill where justified; archaeological natural deposits are not
   automatically the occupied surface in 1900.
5. Align vertical datums before connecting terrain to the scene. The current
   scene uses an arbitrary local datum (including its tide heights), not ODN.
   Historical OS levels require checking their legend, feet/metres and datum;
   a benchmark is a mark on a structure, not necessarily the adjacent ground.
   [OS publishes Liverpool-to-Newlyn corrections](https://www.ordnancesurvey.co.uk/geodesy-positioning/legacy-data/datum-height-differences).
   Older EA surveys also use differing geoid/transform versions, recorded in the
   inventory. Do not treat an uncorrected subtraction as precise ground change.
6. Publish a cropped/downsampled heightfield with additional detail near the
   rivers; keep full rasters out of `docs/`. Reposition buildings, yards, roads
   and rail grades against the final surface together to avoid buried/floating
   objects. Blend masks rather than creating height steps at survey boundaries.

The [MoLAS–PCA PDZ12 evaluation (2008)](https://archaeologydataservice.ac.uk/catalogue/adsdata/arch-702-1/dissemination/pdf/molas1-40627_1.pdf),
printed p.4 / PDF p.12, records contemporary ground around 6.9 m OD near
Livingstone Road/High Street and 3.4 m toward Union Street, with substantial
ground raising and likely in-situ alluvium around 2–2.5 m OD. These are useful
local constraints, not elevations to impose over the whole marsh. Its
stratigraphic sections can help separate building-period consolidation from
later fill.

## Local research artefacts and reproduction

Everything downloaded is under `reference/topography-research-2026-09-28/`, which
is already excluded from Git/publication:

- `study-area.geojson`: BNG borough boundary and exact 3 km buffer.
- `buffer-archive-index.json`: current EA catalogue response for the full envelope.
- `survey-inventory.csv`, `coverage-summary.json`: filtered products and coverage.
- `west-ham-buffer-modern-dtm-10m.tif`: full-envelope modern comparison grid.
- `terrain-source-review.png`: modern relief alongside 2003 catalogue coverage.
- `sources.json`: URLs, acquisition details and file checksums.
- `tiles-2003/*.zip`: original dated raster packages.
- `early-terrain-2003-10m.f32` and `.npz`: reduced historical-reference surface.
- `early-terrain-2003-10m.json`: source checksums, pixel coverage and sample windows.
- `early-modern-terrain-comparison.png`: old/modern/difference panels.

Rebuild the offline coverage audit and preview:

```sh
MPLCONFIGDIR=/tmp/topography-matplotlib python3 scripts/review_topography_sources.py
MPLCONFIGDIR=/tmp/topography-matplotlib python3 scripts/build_early_terrain.py
```

The scripts check catalogue completeness, raster geometry, source dates, ZIP CRCs
for used rasters, and provenance/coverage masks. Both previews have been visually
inspected. No public scene terrain or tide values changed in this
research pass. EA elevation data is provided under the Open Government Licence;
preserve Environment Agency attribution with derived public assets. Retain
GBHGIS attribution for the existing borough boundary and check its source licence
before publishing the boundary itself.

The author is recording historical map heights with Claude. Leave that
transcription to them; retain original readings, units, sheet/date, position,
spot-height versus benchmark type and uncertain readings. Use those controls for
the next historical adjustment and vertical-datum alignment step.

## Author's spot-height prototype — 28 September 2026

Read `reference/spot-heights/PROTOTYPE.md`, the merged `readings.geojson`, raw
reading notes and `evaluation.json`. The supplied data contains 105 distinct
marks: 84 spots and 21 benchmarks; 53 high, 47 medium and 5 low confidence.
Seven of the eight matched EPFL digit labels agree, but this small matched subset
does not establish the prototype's proposed 90–95% accuracy across all readings.
Within-source confidence and repeated crops are not independent validation.

The reported Liverpool heights imply marsh ground about 1.92–2.35 m, river-wall
levels about 5.00–5.76 m, and the sewer crest reading of 31.6 ft about 9.63 m.
These are unit conversions, not Newlyn elevations or scene y-coordinates. The
prototype's Trinity High Water comparison is not yet independently verified and
must not directly set the tide animation. Its summary says no water levels were
found, while several drain-mark notes remain uncertain (e.g. sh072); preserve
that uncertainty until the marks are checked.

`scripts/prepare_historic_height_controls.py` writes a separate staging GeoJSON
and audit in `reference/topography-research-2026-09-28/historic-controls/`.
It preserves every original property and adds metres in the stated Liverpool
datum, scene horizontal coordinates, and provisional surface review categories.
ODN height and scene y remain null; interpolation is disabled for every point.
Four records explicitly describe low ground; six drain-bank marks need review;
21 benchmark mounting contexts remain unresolved. Other records concern roads,
yards, banks, walls, sewer or unclear surfaces. A wall top must not become a
terrain control for the marsh beside it. Likewise a benchmark on a building or
bridge is not necessarily at ground level.

WGS84-to-BNG coordinate consistency is within 0.011 m, attributable to rounding;
this verifies coordinate handling only, not claimed map accuracy. The notes say
roughly a third of dot positions are estimated. Future records should separate
value confidence, dot/position confidence and observed surface type.

Before scaling, replace the proposed hard 0–40 ft acceptance range with a broad
regional plausibility flag. The earlier northeastern terrain sample is about
24 m (79 ft): a 40 ft cutoff would discard plausible high-ground readings.
Keep original values, uncertain digits, dot locations and source crops available
for review. No prototype source files were modified, no extraction API calls
were made, and the public scene terrain/tides were not recalibrated in this pass.
