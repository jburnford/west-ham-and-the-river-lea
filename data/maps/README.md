# NLS London 1:1,056 map metadata

Source: https://maps.nls.uk/os/townplans-england/london-1056-1890s.html

Imported `metadata_nls_os_london_1056_2026-09-23_091420.geojson` from the user-supplied Dropbox path on 2026-09-23.
The original export is preserved byte-for-byte (SHA-256: `9e763db7a56935c0ac92ab0e52d5761753a89104123d50b9648ebf1145fb3463`).
It contains 753 sheet records with footprint polygons, titles, image IDs and NLS viewer URLs. It does not contain map scans or tile-service URLs.

## Spatial shortlist

- 53 distinct sheet records overlap either supplied study layer.
- West Ham: 49 records; estimated footprint coverage 96.78% of the supplied 1911 borough polygon.
- Lower Lea: 20 records; estimated footprint coverage 100.00% of the supplied river polygons.

`west-ham-lower-lea-sheets.geojson` preserves whole sheet footprints and source properties, with overlap flags added.
`west-ham-lower-lea-sheets.csv` provides the same shortlist as a table with sheet titles and viewer links.
`study-area-footprint-gaps.geojson` contains study-area geometry outside the union of selected footprints.

## Method and limits

Reference layers (read only):
- `/home/jic823/swipe_map/site/data/WestHam_1911.geojson`
- `/home/jic823/swipe_map/site/data/Lower_River_Lea.geojson`

All input coordinates are longitude/latitude. Selection uses positive-area polygon intersection in those coordinates, excluding boundary-only contact. Coverage areas are measured after projection to British National Grid (EPSG:27700), using the union of sheet footprints so overlapping sheets are not double-counted.

The lower Lea source had 2 invalid polygons; these were repaired in memory with Shapely `buffer(0)` before union. The West Ham source had 0 invalid polygons. Source files were not changed.

The metadata footprints are rectangular extents, not verified masks of mapped content. Coverage percentages are approximate and do not confirm usable imagery at every location. The river calculation covers only the supplied water polygons, not a surrounding river corridor. The 1911 borough boundary is a selection aid, not a claim about the boundary at the maps' survey dates. Map scans have not been downloaded or checked.

## NLS georeferenced tile layers (added 25 September 2026)

`nls-layers.json` registers the National Library of Scotland seamless map layers that cover the West Ham study area between 1800 and 1920, with series identifications, date ranges, tile URL templates, zoom limits and the layers deliberately excluded. `scripts/fetch_nls_tiles.py` downloads every tile inside the study box for each layer into `reference/nls-tiles/` (outside the public repository), writes a manifest, and stitches a georeferenced quick-look mosaic per layer. Tiles are CC-BY National Library of Scotland; credit "Reproduced with the permission of the National Library of Scotland" with a link to https://maps.nls.uk/ wherever they appear.
