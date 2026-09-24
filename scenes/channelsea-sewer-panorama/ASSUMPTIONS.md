# Spatial review model — 23 September 2026

This ledger describes the implemented study in `docs/app.js`. Numeric values below are modelling inputs, **not claims of measured historical dimensions** unless explicitly identified as source coordinates.

| Element | Input and status |
| --- | --- |
| Coordinate frame | EPSG:27700; origin easting 538900, northing 183209. Local x points east, z south. All distances in metres. |
| Crossing anchor | Historic England listing 1392549: TQ 38900 83209, an approximate listed location. Converted with pyproj to longitude 0.0010593154, latitude 51.5307115265. Not a surveyed photo camera. |
| Camera and movement | A 48 × 11 m rectangle bisects the local sewer bearings, entirely inside the crest with at least 0.5 m clearance at its corners. Start at the middle of its southern edge. WASD/button movement is view-relative, 3 m/s while held, with a 0.5 m initial step. Eye height stays 9 m in the local datum (deck 7.4 + 1.6). Limits are an interaction choice, not a survey. |
| Opening composition | Bearing 184°, pitch −11°, vertical FOV 56°. Chosen for review against Figure 4, not a solved lens/landmark fit. Aspect ratio changes horizontal FOV; the map cone reflects this. |
| Sewer and crossing | Continuous 15 m crest at height 7.4 m, sloping to a 44 m base. Mapped bends translated to the existing bridge anchor; 1.4 km inferred continuation at each end. Earth banks exclude waterways, railway corridors and a 110 m opening around the camera. Heights follow the author’s roof-level description; engineering details and distant extensions remain schematic. |
| River channels | Supplied `Lower_River_Lea.geojson`; transformed, clipped, simplified at 0.4 m. These narrow water polygons do not establish the complete exposed riverbed. |
| River terrain | Continuous 0.4 m grid north and south, x −235 to 65 m, z −320 to 350 m. Channels, muddy shelves, 102 small rills, 15 pools and the raised west bank are inferred from mapped routes and photo/author interpretation. Levels −1.74 to 3.46 m around water 0.06 m are modelling estimates, not a shoreline survey or tide model. |
| Factory plots | Supplied `Industry_1893-95.geojson`; used as site pads. No assertion that parcel outlines are building footprints. |
| Factory forms | Seven simplified main-range envelopes read from VIII.32 and VIII.42 replace the grid studies at five southern sites. Other sites retain contained illustrative blocks. Heights, arched facades, parapets and chimney locations remain interpreted. The independent OS/GIS registration produces some parcel-edge discrepancies. |
| Abbey Mills | Main building anchor 538715, 183222 from listing 1190476; schematic cross of 54 × 20 m and 20 × 48 m wings, walls 13 m, steep roofs, arched windows, dormers, turrets and an octagonal lantern/finial reaching an interpreted 36.7 m after comparison with the supplied 1868 engraving. Five-bay wing ends, polychrome arch surrounds and ridge cresting. Image-informed detail; rotation, dimensions, colours and bay counts remain provisional. |
| Pumping-station stacks | NW anchor based on listing 1357995, 538674, 183259; SE position mirrored provisionally. Both silhouettes about 54.65 m high. Broad decorated bases, slender shafts and pointed openwork crowns follow the supplied 1868 engraving; dimensions and survival into c1900 remain interpreted. Listed bases support the existence of lost stacks, not these upper dimensions. |
| Bromley gas holders | Seven surviving positions from the modern site plan, registered relative to No.6. Radius 31 m, frame height 23 m, two-tier period studies. Bell heights and architectural details interpreted; lost Nos.3 and 5 absent. |
| West Ham gas holders | Six circles traced on OS VIII.32 and VIII.22; radii approximately 16–25 m. Heights 26 m, column count 24 and bell levels are modelling estimates. |
| Housing | Four Abbey Lane pairs and 92 main terrace-row envelopes traced from OS scans. Rounded metadata bounds provide approximate registration, not survey accuracy. Two-storey walls 6.4–6.5 m; roofs, chimneys and facade divisions interpreted. |
| Barges and wharf | Four original vessel studies, approximately 5.4 × 21 m, with curved ends, open holds, cargo, cleats, ropes and deck timbers; two channels and near-bank placements chosen from Figure 4's composition. Timber edge and posts along the eastern channel are interpreted. No vessel identities or exact positions claimed. |
| Surface/lighting | Original procedural building textures, generated sediment colour/bump texture and depth-aware reflective water; colours, haze and lighting are interpretive. No photograph textures or smoke effects. Continuous terrain includes submerged channels; all fine relief remains inferred. |

See [the photo-layer ledger](PHOTO_LAYERS.md) for the visible evidence used in the second modelling pass and its limits.

## Source trail

- Jim Clifford, *West Ham and the River Lea*: figures 3 and 4 provide period river views; the author’s direction correction below supersedes the earlier assumption that both face south. The author's local photographs remain reference-only.
- [Northern Outfall Sewer bridge](https://historicengland.org.uk/listing/the-list/list-entry/1392549): location and rebuilding/widening, 1900–1902.
- [Abbey Mills](https://historicengland.org.uk/listing/the-list/list-entry/1190476), [former chimney bases](https://historicengland.org.uk/listing/the-list/list-entry/1357995), [Bromley holders](https://historicengland.org.uk/listing/the-list/list-entry/1190911): landmark positions, form and chronology. Listing text is available under OGL v3.0; no Historic England maps or photographs are copied.
- [London VIII.32](https://maps.nls.uk/view/101201748): supplied NLS metadata identifies this as the crossing sheet, revised 1893 and published 1895. Direct retrieval returned HTTP 405; the full Commons/Rumsey copies of this sheet and VIII.22 have now been inspected. [Tracing and photograph ledger](../../reference/neighbourhood-context/README.md).
- `data/maps/panorama-source-provenance.json`: original GIS paths, checksums, clipping bounds and invalid-geometry repairs. Rights for public release of supplied GIS remain to be documented.

## What the model can and cannot establish

The data establish an initial relative ground plan. The six scene directions are useful for reviewing the location and testing the experience. The map's cone is the camera's current field, **not an inferred photograph sightline or a visibility analysis**. Do not use this model to assert that every drawn feature was visible, or that an absent feature did not exist.

Photograph matching must determine camera placement, elevation and lens jointly, using multiple identifiable features. Fix that fit and a historical date before committing detailed architecture. Distant and reverse directions remain incomplete. Exporting a finished 360° panorama is premature.

## Further mapped layers and orientation correction

- Railway routes: G.E.R. Woolwich branch east of the factories, the London, Tilbury and Southend line north of Bromley gasworks, and the Abbey Mills junction curve. Tracks follow OS VIII.32/42. Track levels, spacing, sleepers and bridges are schematic.
- Gardens: author identifies them south of the pumping station, consistent with the western foreground in the wide photograph. Uneven furrows and 19 varied plank sheds occupy mapped open land west of the river; these replace the earlier 45 uniform beds. Boundaries, divisions, crops and sheds are interpreted; this is not a traced allotment plan.
- Abbey Mill (Corn): mapped site 252, main 14 × 8 m study, interpreted walls 11.5 m, with boarded upper floors, masonry base, interlocking gables and a low waterside cover. The author proposes continuity from the c1800 building by analogy with Three Mills; this is not a confirmed c1900 elevation. Figure 1 is dated c1800 in the book. No surviving c1900 windmill is established and none is modelled.
- Author’s correction, 23 September 2026: the close-up 1902 view and wide 1900 view show different gasworks. The north-facing 1902 view is associated with West Ham Gas Works; the wide south-facing view with Bromley. The local filename mentioning Bromley is not reliable evidence for orientation. Exact photo camera fits remain unresolved.

Movement and direction are independent: story buttons change the view while preserving position; north/south buttons preserve the along-bridge offset and facing direction. Reset/Home restores both. Map marker and cone follow the camera. Movement is disabled without WebGL and stops on focus loss, hidden page, dialog opening and pointer release. Atmosphere now uses overcast diffuse light, grey haze, uneven brick weathering and dull brown-grey water, as an interpretation of the period photographs and author’s description rather than measured colours or pollution concentration.

## Visual refinement assumptions, 24 September 2026

The new roof sections, loading doors, gutters and ventilators vary the existing factory studies without moving their envelopes. Curved parapets are restricted to northern site 253; this is a comparative use of the northern photograph, not a confirmed identification. Section walls vary by 0–1.3 m below the previous range height; pitched roofs rise approximately 2.6 m, with selected ventilators above them.

Mud relief is subdivided and reshaped with deterministic noise inside the existing bed triangles. Its boundaries and the mapped water polygons are preserved. Fine roughness, wetness, weathering, overcast colours and shadows are interpretive rendering choices. The contact-shading atlas is derived from model envelopes, not mapped marks on the ground. Planar reflections show the provisional scene from the moving camera; they do not validate its historical accuracy. Archive photographs remain reference-only.

## Southwest context and new map references, 24 September 2026

Fifteen distant terrace groups use approximate axes from the supplied southwest extract. Three conflicting traces are withheld. Twenty industrial ranges are contained in existing GIS site polygons, excluding water and railway space. Building elevations, divisions and range footprints remain estimates. Seven holder controls fit the screenshot to the existing model, with 1.14 m residual; the historical overlay itself may differ by tens of metres. The broad 1905 map checks landscape relationships but does not independently date these circa-1900 building studies. See [the supplied-map ledger](../../reference/author-map-extracts-2026-09-24/README.md) and [terrain record](TERRAIN.md).

The subsequent [lighting and infrastructure pass](LIGHTING_AND_INFRASTRUCTURE.md) supersedes the earlier lighting setup and flat railway levels. It adds 50 map-traced road/lane studies with provisional grey/brown period surfaces, raised railway embankments and crossings, and separate Three Mills landmarks. The sediment mask now protects dry ground from wet-mud shading. Latest desktop exports and error checks are `review/lighting-*.png` and `review/lighting-checks.json`; earlier rendering counts describe earlier passes.
