# River network expansion — 25 September 2026

## Regional bank sections, 1 October 2026

The expanded river system now has shoreline-following cross-sections instead
of a uniform two-metre grid apron. Constrained polygon bands model submerged
beds, muddy river margins, earth slopes and steeper canal banks. The added
geometry covers approximately 46.9 km of shoreline; the existing detailed core
is retained. Native map outlines and their control records remain unchanged.

Limehouse Cut has approximately 5.0 km of interpreted brick facing and stone
coping. Hackney Cut retains earth banks rather than assuming continuous masonry.
These are provisional material and section choices, not a surveyed wall
inventory. The parameter file, `data/maps/lower-lea-region/bank-sections-1900.json`,
keeps the geometry epoch, illustrative water-relative heights, bed assumptions
and source notes together. It does not assign hydraulic capacities or backdate
the 1930s flood works.

Banks follow the outer boundary of the combined water network, preserving
confluences, bridge openings and mill passages. Explicit source-window
boundaries remain open. Banks fade into preserved local ground and existing
building/road surfaces; building, bridge and sewer elevations are unchanged.
The original local flood calculation remains unchanged.

The river explorer includes close views of Old Lea earth banks, Hackney Cut
and Limehouse Cut. Rebuild with `python3 scripts/build_river_system.py`, then
run `scripts/check_river_system.py` and `scripts/check_river_banks.py` before
`scripts/build_scene_manifest.py`. The bank check measures actual rendered
coverage, checks shoreline placement and verifies passage and boundary
clearance. Browser review uses `scripts/review_historic_elevation.py
--river-system-only`.

## Tidal correction and refinement, 26 September

The subsequent [marsh/ditch pass](MARSH_DITCHES.md) supersedes the mesh counts
and generic low-bank section below: 594,581 vertices and 1,170,034 triangles,
including the lower marsh and map-traced ditches. General tidal crests are now
raised above that marsh, with provisional retaining edges at working plots.

The author specifies tidal channels throughout the scene except the Old Lea
from the Limehouse Cut lock northward. The current generator distinguishes
that retained reach (GIS ids 18, 22, 10018, 10022) from the tidal channels,
including Bow Creek (id 0). It adds exposed sediment margins using the existing
Channelsea water datum of 0.06 scene metres and the same sediment texture. This
is a visual common tide state, not surveyed bathymetry or a tidal simulation.
Inferred mud shelves taper toward grass; roads and industry footprints limit
their landward extent. The detailed Channelsea terrain remains unchanged.

`river-network.silt` supplies a separate per-vertex sediment blend; the original
GIS water polygons are retained. The new relief contains 468,737 vertices and
919,216 triangles. `check_river_tides.py` verifies exposed mud on the principal
tidal channels and excludes it from the retained reach away from confluences.
The [refinement record](REFINEMENT.md) also covers path continuity, facade detail,
district contact shading, review cameras and outstanding work.

## Earlier expansion record

The first expansion gives the 15 existing GIS water features submerged beds and
bank relief outside the detailed Channelsea terrain. It retains the supplied
channel outlines and removes the flat ground beneath them. The indexed mesh
contains 370,141 vertices and 723,578 triangles at a 1 m grid spacing; the narrow
corridor avoids a district-wide dense terrain mesh. The original detailed core
is retained, with matching boundary levels and a small outer ground offset to
prevent coplanar flicker. Industrial parcels and road corridors suppress bank
height where needed to retain their existing ground level.

Three Mills Wall River is the branch west of Mill Mead, as corrected by the
author. The c1900 photograph looking south from High Street informs its grassy
raised east bank. All section heights, widths and bed depths are estimates.
Generic bank sections elsewhere are an initial terrain scaffold. They do not
represent a surveyed embankment or retaining-wall inventory.

## Source chronology and next detailed areas

The author-defined extent is the Great Eastern Main Line in the north,
Bromley-by-Bow gasworks in the south, Channelsea in the east and Old Lea in
the west. Three Mills is included. See [research scope and evidence](RESEARCH_SCOPE.md)
for the recovered planning reports and feature-by-feature chronology.

- Five fire-insurance screenshots are archived unchanged under
  `reference/author-river-plans-2026-09-25/`, with hashes and the author's
  provisional **1885–1890** dating. They comprise three overlapping areas with
  two near-duplicate pairs. Sheet dates and registration remain unverified.
- The separate `marsh housing.png` is an OS screenshot with an unverified date.
  Do not transfer the fire-insurance date estimate to it. The author prioritises
  this housing between the Channelsea and Three Mills rivers. Existing rows
  os-row-1 through os-row-18 already represent Roberts, Beck, Lucas, Godfrey,
  Marsh, Ross, Allwyn, Abbey Lane, Livingstone and Stanley streets. This pass
  adds a coverage review view, without duplicating those rows. Rear extensions,
  courtyards and a complete comparison with the new screenshot remain to trace.
- Two City Mills / Howards images are archived under
  `reference/city-mills-howards/`. The Foxlinks photograph is probably from the
  north looking south according to the author. Its parent page captions it
  about 1914 near the old flood-gate; that secondary date and camera remain
  unverified against the original photographic record.
  The other is captioned **City Mills, from High Road** and is recorded as from
  the company's circa 1897 pamphlet. The author identifies it as the southern
  view. It shows masonry river edges and an arched opening, which are not yet
  individually modelled. Register the fire-insurance plan before placing these
  features or attempting an exact photographic match. Existing GIS site 260 is
  a parcel envelope, not the factory's individual building footprints.
- Britain from Above EAW014561 is catalogued as **Towler and Son Ltd Riverbank
  Works on the Three Mills Wall River**, **16 April 1948**. It is archived under
  `reference/three-mills-aerial-1948/`, with its catalogue page. It should not be
  identified as Howards merely because it was supplied beside those images.
  **The author dates the later embankments to the 1930s.** This aerial has not
  supplied geometry to the c1900 scene. Do not backdate its engineered walls,
  channel alterations or industrial ranges. Prescott Cut remains excluded.

Reference photographs stay outside the public web root and are not textures.
Source and date records are separate from inferred geometry. The earlier
photographs' masonry and grassy banks do not establish continuity of the later
engineered river works.

The later Sugar House photograph supplied during review led to ASE historic
building record 2013200 (September 2013), archived in
`reference/sugar-house-building-sequence/`. The west face matches its Plate 49.
The report dates the tall warehouse (Building 16) to 1882; adjoining warehouses
15, 17 and 17a fall between the 1894 and 1916 maps, grouped as circa 1900. The
low white gable traces appear to relate to west-side Building 15. Its precise
construction year remains unresolved; the provisional fire-insurance sheet
dating must be checked before narrowing this bracket. No new Sugar House
geometry has been introduced in this river pass.

## Rebuild and review

```sh
python3 scripts/build_river_network.py
python3 scripts/review_river_network.py
```

The generator uses the existing ground plan, detailed terrain metadata and
infrastructure. Regenerate this layer after changing those inputs. Runtime
loading/rendering is in `docs/river-network.js`; generated positions, colours,
indices and metadata are under `docs/data/river-network.*`.

The review script serves only `docs/` on a temporary loopback port and uses the
local WSL NVIDIA browser configuration. It captures the full river network,
two Wall River views, Three Mills junction, the original Channelsea view, marsh
housing coverage and existing City Mills coverage. Results live in the ignored
`review/` folder. The City Mills coverage image documents unfinished massing;
it is not a reconstruction matched to the newly supplied photographs.

All seven views passed browser/shader checks after resumption, as did
the existing geographic, bridge-movement and JavaScript syntax checks. The
expanded seven-view report records the final desktop review. No new phone
performance audit or deployment is part of this pass.

## Subsequent factory coverage, 26 September 2026

The [factory pass](FACTORY_BUILDINGS.md) supersedes the earlier research-only
status above. It adds the building ranges and all nine Bromley holder positions.
Four original GIS river continuations now extend the western clip to the Old Lea
beside the complete soap and saw mills. The rebuilt relief has 411,593 vertices
and 804,496 triangles across 19 source features. `factory-west-context.json` is
an additional rebuild input. The original c1900 chronology exclusions remain.


## Reviewed passages integrated into the core — 1 October 2026

`scripts/core_river_connections.py` now converts the reviewed map connections into
seven local scene patches, projecting endpoints onto the existing reconciled banks.
It preserves the original water polygons and building footprints. The applied
connections are Three Mills, Pudding Mill, Abbey Mill, Bow lock, the western Bow
Back mouth, the local Waterworks seam and one Bow Creek seam. Another Bow Creek
seam lies beyond the existing clipped scene and remains deferred.

The same generated connection records are included in river-network.json,
terrain-1900.json and landscape-flood-1900.json. Detailed terrain and outer river
banks are cut below the water at the passages; epoch protections include them.
The main water surfaces and SVG plans include the new connections. The lock gap
has a separate static water surface and is excluded from the animated tidal
coverage between the original channels. Buildings, bridge decks and the sewer
retain their elevations. Three Mills has one connection group for the shared
upstream water, rather than duplicate capacities for the two source polygons.

Display widths of 2–4 m and a provisional bed at -0.7 scene metres are explicit
modelling assumptions. They establish visible geometric continuity, not measured
wheel openings, sill elevations or hydraulic capacities. The flood preview still
uses a common stage across mapped tidal reaches; it does not yet simulate mill
losses or gate operation. The wider Limehouse Cut branch and upper Channelsea
works corridor require bank tracing before insertion into the core geometry.

Rebuild order: build_river_terrain.py, build_river_network.py,
build_historic_elevation.py, build_landscape_flood.py, build_lower_lea_region.py,
build_scene_manifest.py. Run check_core_river_connections.py alongside the tide,
historic-elevation and landscape-flood checks. The browser flood review now checks
that these connection records reach the main scene, plus the preserved sewer.
# Regional river system checkpoint — 1 October 2026

The main scene now includes the wider mapped river system, with a dedicated
[river view](http://127.0.0.1:4175/?rivers=1&quality=lite). This is a geometry
checkpoint before the regional flood model. The existing local flood calculation
has not been expanded.

`scripts/build_river_system.py` combines the primary reaches with historical
Hackney Cut and Limehouse Cut polygons, reviewed crossings and native map-pixel
traces at Lea Bridge, upper Channelsea and the Thames mouth. The derived assets
retain source hashes, explicit controls and unassigned hydraulic capacities.
The current detailed core takes precedence over the older regional GIS copy.

`scripts/check_river_system.py` checks actual polygon continuity, provenance,
mesh dimensions and protection of the local flood bed. Browser checks capture
six views and verify the sewer enclosure and mobile layout. Small reconciliation
fragments remain for cleanup; bed depths, bank sections and passage widths are
provisional. Mill losses and lock operation still require modelling.

## Mapped ordinary-tide limits — 1 October 2026

`data/maps/lower-lea-region/tidal-limits-1900.json` records the two Temple Mills
annotations supplied by the author and checked against the registered five-foot
crop. The western dotted cross-channel line intersects River Lea reach16. The
eastern annotation locator falls on Channelsea reach10, close to the separate
Waterworks/Temple Mills weir; its exact leader and channel association remain to
be verified before assigning a hydraulic cross-section.

These constrain the upstream reach of **ordinary** tides, not flood maxima or
water elevations. Neither is an impermeable boundary. Source dates, positions,
uncertainties and null water levels are retained separately for future epoch and
tidal-propagation work. The present display and local flood solver are unchanged.

## Direct bank and marsh height review — 1 October 2026

`data/maps/lower-lea-region/height-surface-review-1900.json` records twelve
observations inspected on full native five-foot maps and at8x. Source mosaics,
survey-dot pixels, corrected BNG positions and detail crops are retained.
The regional builder applies these reviews over the immutable transcription
snapshot, preserving original classifications and notes.

The11.2ft and10.8ft Waterworks-side dots lie on adjoining low ground outside
the bank hatching; both change from bank-top to marsh. The16.4ft dot lies in
Temple Mill Lane between ditches, and its old position was about9m west of the
actual dot. The21.5ft Hackney Cut point is on the eastern towing path, despite
its older west-bank note. Nearby B.M.12.98 is a separate benchmark and is not
a marsh-floor spot height.

These corrections update the height inventory, not the rendered elevations.
Fit the surrounding marsh, bank profile and attached structures together before
using them for overtopping. Retain original feet/datum; no new ODN calibration
or same-height assumption for1848–50 is introduced. The reading guide now
explicitly excludes adjacent marsh/foreshore from automatic bank-top assignment.

## First applied regional marsh surface — 1 October 2026

`marsh-surface-1900.json` and `scripts/regional_marsh_surface.py` now build a
38,499m² dry-ground patch north of the Victoria Park Branch railway and west
of the Old Lea. Two directly reviewed field dots,14.0ft and13.3ft, constrain
the surface. The13.3ft dot was checked on the native map and at8x in this pass.
Heights use the existing provisional source-datum conversion, giving3.87096m
and3.65760m ODN respectively; these are model conversions, not new survey ties.

The river-margin slope meets the adjacent reconstructed ground, with no added
unsupported raised crest. The patch follows the river polygon on its eastern
side; north/west/south transitions fade into the uncorrected scene. Terrain
triangles replace the old flat floor and share the same height function with
the adjoining bank mesh. No existing buildings/roads overlap the patch and
the detailed core remains outside it. Bed/water levels and flood solver remain
unchanged. The new `surveyed-marsh-banks` camera shows this first applied patch.

A compartment check rejected the initial proposed fit between western bank
marks18.6/17.1ft and low-margin marks11.2/10.8ft: the latter fall on the other
side of the mapped Waterworks channel. They are now explicitly withheld from
terrain fitting pending channel/foreshore reconciliation. Their previous
classification review does not authorise interpolation across the river.

`check_regional_marsh.py` verifies the actual rendered triangle heights at
both dots (about3–4mm residual), complete coverage, no overlapping dry faces,
no flat-floor overlap, preserved water and detailed core, and exact agreement
at shared bank/marsh vertices. These numerical residuals are not historical
accuracy estimates. Rebuild regional inventory, river system, scene manifest;
run regional-marsh, river-bank, river-system, region and local-flood checks.

## Applied Old Lea and Pudding Mill bank margins — 1 October 2026

`bank-margin-surface-1900.json` fits four reviewed bank-margin dots: 18.6 ft,
17.1 ft, 17.2 ft and 17.3 ft. The last two were inspected on native five-foot
mosaic `m18_131057_87131` and its 8x crops. The 17.3 ft dot belongs to the
EAST bank of the Pudding Mill River head, below its fork from the Old Lea;
it must not lift the main Old Lea bank farther west. The selected dry strip
now follows both mapped reaches and stops before Knobshill Cottage. It covers
about 359 m of shoreline and 4,966 m² (previously 225 m and 3,065 m²).

The provisional conversion gives 5.27304, 4.81584, 4.84632 and 4.87680 m ODN.
These dots measure local bank-margin surfaces, not continuous maximum crests.
Longitudinal interpolation, side slopes and transitions into the surrounding
unreconstructed ground remain interpretations. The 11.2/10.8 ft points across
Waterworks remain withheld; the lower 12.1/13.5 ft readings farther south are
not used in this bank fit. The earlier 38,499 m² marsh patch and its two ground
controls remain unchanged. Bank heights never become marsh-floor controls.

The regional inventory now contains 15 directly reviewed observations. Six
controls are active in display terrain; the generated `terrainPatches` records
are authoritative for that status. Source observation-review flags continue
to describe the inventory stage. Water/bed levels and flood hydraulics remain
provisional; this pass does not change the flood solver.

Checks cover all six rendered control positions, complete nonoverlapping dry
surfaces, channel clearance, shared mesh edges and preservation of detailed
terrain. Source hashes, river banks/network and existing local flood checks
pass. New `surveyed-pudding-banks` camera gives a view around the fork;
`surveyed-lea-banks` retains the earlier close view.

Browser review passed six desktop bank views plus the 390px layout, with no
page errors and unchanged sewer diagnostics. The new fork image was visually
inspected. Small angular water/margin fragments at the junction remain a
separate geometry-cleanup task. Scene fingerprint: `0eeff74e66e1`.

## Low ground opposite Knobshill Cottage — 1 October 2026

Direct inspection of the five-foot mosaic `m18_131057_87131` confirms that
`sh_537494_184017`, 12.1 ft, is open ground between the Old Lea and Pudding
Mill River. Its dot is outside the bank hatching. A ditch bounds the ground
to the south; the cottage and its garden lie across Pudding Mill River.
The 13.5 ft dot farther southeast appears on a track and is not used here.

`knobshill-ground-surface-1900.json` defines a 3,934.995 m² dry compartment.
Its southern outline follows the ditch's north edge in native map pixels;
water polygons supply the river boundaries. A 10 m transition at the review
outline avoids a hard step into unreviewed ground. No ditch invert, discharge
or flood-barrier height is inferred from that transition. The single ground
dot supplies a local level estimate; internal slope remains unmeasured.

With the existing provisional datum, 12.1 ft converts to 3.29184 m ODN and
scene Y 1.4564 m. This is about 1.585 m below the 17.3 ft bank observation
on the other side of Pudding Mill River. They belong to separate surfaces.
The shared terrain helper now accepts a map-traced review outline while
retaining the original rectangular configurations for earlier patches.
All three applied patches are disjoint; no cottage, path or existing modelled
structure is lifted by this change. The flood solver remains unchanged.

There are now 16 reviewed observations and seven applied display controls.
Checks pass for actual rendered heights, dry seams, water clearance, complete
coverage, source hashes, unchanged earlier patch areas and local flood results.
Native pixel-to-BNG checks verify the traced outline; explicit exclusions cover
the cottage garden, eastern track and land south of the ditch. Mesh fit errors
do not measure historical accuracy. Source comparison:
`reference/river-height-review-2026-10-01/knobshill-ground-review-overlay.png`.
New camera: `knobshill-marsh-banks` (Low marsh). Scene: `26c58a1fa0b8`.

Browser review passed seven desktop views and the 390px layout, with zero
page errors and unchanged sewer diagnostics. The new low-marsh screenshot
was visually inspected: ground and river-edge transitions are smooth.

## Northern marsh and railway foot extended together — 1 October 2026

The 13.0 ft and 13.3 ft readings immediately north of the Victoria Park branch
are ground observations at the embankment foot. Native 8x crops show their dots
outside the railway boundary and hatching. They are retained as
`embankment_foot`, not railway formation or bank-crest measurements.

The northern marsh now uses four ground observations, with spatial inverse
squared-distance interpolation in the same dry compartment. Its western and
southern extent has grown from about 3.85 to 6.13 hectares. The two new ground
controls convert provisionally to 3.56616 and 3.65760 m ODN (scene Y 1.73072
and 1.82216 m). Estimated slopes between observations remain uncertain.

The railway footprint is excluded from the ground mesh. The northern earth
slope receives generated height adjustments using the same ground field,
weighted down to zero at the existing 3 m scene formation. Track geometry,
formation height and southern slope remain intact. The source infrastructure
file is retained; `applyRiverSystem` validates and applies the explicit
vertex adjustments before scene geometry is built. Other infrastructure,
including the sewer, is outside this adjustment.

A seam test checks actual rendered ground against adjusted railway toe
positions, rather than merely evaluating the same interpolation formula.
It detected boundary-rounding exclusions that left alternate vertices at
placeholder height. A tiny sampling tolerance now handles mathematical
boundary points without expanding the terrain footprint. The earlier Old Lea
bank and Knobshill ground patches remain separate and retain their areas.
The mapped Waterworks-side dots inspected during this pass remain unapplied:
their relationship to the current shoreline needs reconciliation.

New camera: `railway-marsh-banks` (Railway foot). This remains display-terrain
reconstruction; the regional flood solver is not calibrated by this pass.

Final numerical checks pass nine active survey controls and 160 railway-toe
locations; maximum ground/toe mismatch is 8.4 mm (mesh fit, not historical
accuracy). The bank mesh now also excludes about 106 m² beneath the adjusted
embankment, avoiding a second overlapping surface. Runtime checks confirm that
only the listed earth-slope vertices change and reject mismatched source data.
Scene fingerprint: `339d57109c71`; 663,554 regional terrain triangles.

Browser review passed eight desktop views and the 390px layout with no page
errors and unchanged sewer diagnostics. The railway-foot view was visually
inspected: terrain meets the earth slope continuously; their material boundary
remains visible.

## Waterworks River eastern margin — 2 October 2026

The native five-foot map places the 14.6 ft, 14.7 ft and 15.2 ft dots on the
EASTERN margin of Waterworks River, west of the narrow parallel drains.
The earlier description of 15.2 ft as west-bank ground was incorrect.
These dots establish local margin elevations, not a continuous flood-bank
crest. The legacy `embankment_top` inventory grouping is retained with this
explicit qualification and `bank-margin` surface roles.

`waterworks-margin-surface-1900.json` fits a 6 m wide dry strip, about 254 m
of shoreline and 1,339 m². The shared provisional conversion gives 4.05384,
4.08432 and 4.23672 m ODN. The narrow illustrative water-edge transition
preserves the readings close to the bank line; its cross-section and the
landward transition remain interpreted. Neither the parallel drainage strips
nor the Channelsea bank receives these heights.

The original source river polygon slightly covered the 15.2 ft dot. A native
map trace removes 30.290 m² of that overrun, confined to a short eastern-edge
section. The generator retains the original source inventory and records the
removed polygons in reach provenance. No water is added; the opposite bank,
component count and all neighbouring river contacts are preserved. See
`reference/river-height-review-2026-10-01/waterworks-shore-review.png`.

There are now 21 reviewed observations and 12 active display controls in four
separate patches. Geometry checks pass all controls, dry seams, coverage and
water clearance, plus the earlier railway-toe checks. The local flood solver
and its results remain unchanged. New view: `waterworks-margin-banks`.
Scene fingerprint `f619948de47c`; 663,612 regional terrain triangles.

Browser review passed nine desktop views and the 390px layout with no page
errors and unchanged sewer diagnostics. The native shoreline comparison and
Waterworks view were visually inspected. A faint outer bank/ground seam
remains a visual-cleanup item; wider ground elevations remain provisional.

## Upper Waterworks bank beside the Artificial Manure Works — 2 October 2026

A separate dry compartment north of the connecting watercourse now follows
three bank observations: 17.8 ft at the Potter's Ditch corner, 18.0 ft beside
the works, and 17.8 ft farther south. The bank hatching and the actual survey
dots are visible on native five-foot mosaic `m18_131057_87119`. The corner
locator was refined from pixel 795,438 to 795,440. This new patch remains
separate from the previously reconstructed lower Waterworks margin across water.

The enlarged map resolves the formerly uncertain 18.0 ft dot at 845,655, in
bank hatching west of the number. Two source records represented this same
observation. `sh_537659_185146` is canonical; `sh_537672_185146`, previously
located at the printed figure, is explicitly retained as a withheld duplicate.
The model must not count those entries as independent ground and bank controls.

`waterworks-upper-bank-surface-1900.json` applies a six-metre strip covering
1,147.136 m² and about 196 m of shoreline. The shared provisional datum yields
5.02920, 5.09016 and 5.02920 m ODN. These local bank surfaces do not establish
a continuous maximum crest. Water-side and landward slopes remain interpreted.
The neighbouring 15.1 ft observation is across Potter's Ditch and is excluded;
the correction stays outside the factory buildings and yards.

The inventory now has 24 reviewed entries, including the explicit duplicate,
and the display terrain uses 15 distinct survey dots across five disjoint
patches. Checks pass all actual mesh/control heights, complete dry coverage,
water clearance, source hashes and the 160 railway-toe locations. The previous
four patches retain their areas, and the river network and local flood results
are unchanged. Mesh-fit errors do not measure historical accuracy.

New camera: `waterworks-upper-banks` (Upper Waterworks). Scene fingerprint
`6e6bb6bf3892`; 663,612 regional terrain triangles. The wider regional flood
model remains unfinished.

Browser review passed ten desktop bank/marsh views and the 390px layout with
no page errors and unchanged sewer diagnostics. The upper-bank screenshot
was visually inspected: the reconstructed bank is continuous at the water
edge; wider adjoining ground and bank cross-sections remain provisional.

## Temple Mills bank path — 2 October 2026

The east bank/path north of Templemills Bridge now follows three mapped
surface heights: 16.8, 16.7 and 16.8 ft. The northern dot was missing from the
frozen inventory and is retained in `height-observations.additional.geojson`
with its native mosaic, pixel, map date and coordinate provenance. It lies
at pixel 567,606 on `m18_131057_87113`; the two southern observations are at
612,58 and 642,275 on `m18_131057_87116`. The original snapshot is unchanged.

`temple-mills-bank-path-1900.json` adds 1,844.336 m² of dry bank/path surface,
limited to an eight-metre margin east of Waterworks River. The fit tapers
before the bridge and northern buildings. Road, bridge, weir and benchmark
heights remain separate; widths and cross-sections are interpreted. The
provisional datum gives 4.72440, 4.69392 and 4.72440 m ODN.

The inventory now contains 3,938 observations and 25 reviewed entries,
including the previously identified duplicate. Display terrain uses 18
distinct dots across six disjoint patches. Checks pass actual mesh heights,
complete dry coverage, water clearance, source registration, bank/network
geometry and 160 railway-toe joins. Earlier patch areas and local flood
results are preserved. This changes display terrain; regional flood
calibration remains unfinished. Mesh-fit precision is not historical accuracy.

New camera: `temple-mills-path-banks`. Scene fingerprint `7b3bda0295cc`;
663,612 regional terrain triangles.

Browser review passed eleven desktop bank/marsh views and the 390px layout,
with no page errors and unchanged sewer diagnostics. The source crop and
Temple Mills view were visually inspected; the bank meets the water edge,
with a faint outer transition still visible against provisional adjoining ground.

## Low ground beside Potter’s Ditch — 2 October 2026

The small area of ground north of Potter’s Ditch and west of the Channelsea
now follows the mapped 14.6 and 15.1 ft observations. These are ground/margin
readings, separate from the hatched raised bank beside the manure works
across the water. The 14.6 ft dot is at native pixel 933,211 on
`m18_131057_87119`; the 15.1 ft locator was refined from 940,404 to the dot
centre at 939,401. The former retains its `open_ground` classification;
selecting an open-ground control no longer requires relabelling it as marsh.

`potters-ditch-ground-surface-1900.json` restricts the surface to 4,189.660 m²
of the same dry compartment. The river outline already clears both dots,
so no water geometry was changed. The native-map review envelope excludes
the northern bridge/building and the raised works bank. A ten-metre blend
at its western edge marks an uncertain transition, not a mapped embankment.
Two dots support local interpolation; the cross-valley slope, water-edge
profile and wider ground remain interpreted. Provisional elevations are
4.05384 and 4.20624 m ODN.

There are now 26 reviewed entries (including the existing duplicate), with
20 distinct survey dots applied to seven separate display-terrain patches.
All previous patch areas remain unchanged. Source registration, actual
mesh/control heights, dry coverage, water clearance, bank/network geometry,
railway earthworks and local flood checks pass. The new mesh agrees with
the two targets within 0.000415 m; this is numerical fit, not historical
accuracy. The full regional flood terrain remains unfinished.

New camera: `potters-ditch-banks`. Scene fingerprint `d217bdd38d55`;
664,026 regional terrain triangles. Map review illustration:
`reference/river-height-review-2026-10-02/potters-ground-review.png`.

Browser review passed twelve desktop views and the 390px layout, with no
page errors and unchanged sewer diagnostics. The Potter’s Ditch screenshot
was visually inspected: the ground surface is continuous. Its western
transition and existing angular water junctions remain visual cleanup items.

## Old Lea–City Mill bank and lower ground — 2 October 2026

The previously withheld 11.2 and 10.8 ft observations are now assigned to
the correct dry compartment, east of City Mill River and west of Waterworks
River. The complete native mosaic resolves the channel-side ambiguity:
their dots lie beyond the landward ends of the bank hatching. The earlier
review mistakenly called this margin Waterworks. Their previous withholding
notes remain in `priorTerrainUse`; the original observation snapshot is intact.

Two separate dots within the bank hatching provide 17.4 ft at pixel 35,364
and 16.7 ft at 231,706 on `m18_131060_87128`. The northern observation lies
on the Old Lea GIS reach, immediately upstream of the City Mill reach.
The bank profile must therefore use both `Lower_River_Lea-15` and `-7`.
It must not draw heights from the opposite western Old Lea bank.

`city-mill-ground-surface-1900.json` fits two bank and two ground series
separately across 39,003.755 m² of the river-bounded dry compartment. The
bank-to-ground slope is interpreted between the mapped observations; the
unsurveyed interior and Waterworks-side bank still have uncertainty. The
north and south review limits blend over 12m and are not physical levees.
No water outlines, channel links or structures were moved.

The inventory now has 28 reviewed entries including one duplicate, and
eight display-terrain patches use 24 distinct survey dots. All seven earlier
patch areas remain unchanged. New map comparison:
`reference/river-height-review-2026-10-02/city-mill-ground-review.png`.
New camera: `city-mill-ground-banks`. This work remains display-terrain
reconstruction; full regional flood calibration is still unfinished.

Checks pass source registration, all 24 rendered control heights (within
3cm), complete dry coverage, water clearance, no overlap with factories or
the detailed core, and railway slope joins. The bank tests now cover mixed
bank/ground controls and the Old Lea–City Mill reach boundary. River-network
and local flood results remain unchanged. The largest new mesh residual is
2.874cm at the 10.8ft ground dot; numerical fit does not establish historical
accuracy. Scene fingerprint `f9b87d4a42ed`; 668,517 terrain triangles.

Browser review passed thirteen desktop views and the 390px layout, with no
page errors and unchanged sewer diagnostics. The City Mill view was visually
inspected: the raised bank and lower field are visible. Existing angular
junction fragments and outer review transitions remain cleanup items.


## Regional ground and street evidence pass — 2 October 2026

The first regional audit now retains streets as important surface constraints.
Of 3,938 records, 123 ground and 943 street observations pass the first screening;
benchmarks, bridge decks, banks and railways remain separate. Inferred surface
classifications and ambiguous readings remain available for targeted review.
The source snapshot is unchanged. Within the sampled 750 m river corridor,
47.28% of dry ground lies within 250 m of a usable ground/street candidate,
compared with 16.86% using ground alone. Distance is a coverage diagnostic,
not a vertical error estimate or permission to interpolate across barriers.

The ground/street trial uses linear triangles with no water intersection and
no edge over 500 m, producing 15.6183 km² of supported 10 m raster cells in the
49 km² review window. Unsupported cells remain NaN; 2003 terrain is not a fill.
Five-fold holdout gives mean absolute errors of 0.229 m for 87/123 ground
predictions and 0.253 m for 789/943 street predictions. Corresponding 90th
percentiles are 0.466 m and 0.591 m. Unsupported holdouts and larger residuals
are retained. These assess internal consistency, not historical accuracy.

The author regards approximately 30 cm as a useful working target given
imprecise historical flood inputs. This is not a bound on all terrain error.
Prioritise missing coverage, consequential barriers and routes, and plausible
water-level ranges over marginal interpolation improvements. Street levels
anchor developed ground; marsh lanes may approximate neighbouring ground
without an assumed large or fixed fill correction. Targeted inspection confirms
the low Chargeable Lane 3.4 ft dot despite a +2.15 m holdout prediction error;
the observation stays. Evidence and the interpretation standard are recorded
in `data/maps/lower-lea-region/regional-elevation-review-1900.json`.

Build with `scripts/build_regional_elevation_audit.py`, then
`scripts/build_regional_elevation_trial.py`; check with
`scripts/check_regional_elevation.py` and `scripts/check_lower_lea_region.py`.
The regional browser review exercises evidence/trial/reference modes, filters,
source inspection, gap priorities and 390 px layout. The trial screenshot was
visually inspected. View `lower-lea-region.html?elevation=trial` locally.

No scene or solver elevations changed. The eight reviewed display patches,
detailed core and structures remain intact. Next reconcile dry-land barriers,
existing reviewed surfaces and transition geometry, extend the sparse valley
coverage, and then connect the regional surface to flood testing.

Targeted follow-up confirmed two previously inferred Carpenter’s Road street
observations (13.1 and 12.7 ft) below the distinct high-level railway. They now
qualify for the trial; they improve evidence proximity but water-crossing
exclusions still prevent local triangles. The map also exposes 27 holdout
residuals over 1 m and distinguishes unread cached maps from absent coverage.
Of 111 river-corridor review cells, 62 intersect cached period maps with no
completed manifest reading or snapshot record, 39 have cached maps to revisit,
and 10 lie outside the cached period-map coverage. The source manifest and
original observations remain unchanged. The western E536500/N184000 cell
provides a concrete next reading batch of nine cached five-foot mosaics.


## Western regional gap expansion — 2 October 2026

Added 27 directly checked observations from cached five-foot maps around
Victoria Park and Hackney Wick: 10 park/path/church-ground and 17 street
levels. They live in `regional-elevation-supplement-1900.json`; the frozen
snapshot and original regional source index remain unchanged. Native dot
positions, map registrations, hashes, cropped evidence and surface roles are
retained by `scripts/regional_elevation_sources.py`. An overlapping 15.9 ft
reading was excluded as a duplicate; ambiguous candidates remain withheld.
This targeted pass does not mark the original reading manifest complete.

The audit now contains 3,965 records and the trial uses 1,093 candidates
(133 ground, 960 streets). Supported raster area increased by 0.3900 km² to
16.0083 km². Held-out mean absolute errors are 0.236 m for 93/133 supported
ground predictions and 0.258 m for 798/960 street predictions. These remain
internal consistency measures, not uniform error bounds. The western
E536500/N184000 priority cell now has no sampled dry area more than 250 m
from a usable candidate; that proximity does not imply full surface support.

Five native-map exclusions protect the Bathing Lake and immediate margin,
Hertford Union canal/lock/towpath corridors, and two smaller mapped water
features. The canal envelopes are deliberately conservative interpolation
exclusions, not precise water polygons or hydraulic barriers. The western
dry dock still needs a separate footprint before terrain extends there.

Direct map review confirms Campbell Road’s 44.9 ft outlier beside the railway
cutting near the bridge. Retain the measured road height and reconcile the
road/cutting geometry; do not lower it to surrounding averages. Source checks
also retain new White Post Lane 16.4 ft, St Augustine’s path 42.5 ft and
Cassland Road 40.9 ft observations despite large held-out prediction errors.

Source/numerical checks, existing regional coverage checks, syntax checks and
browser desktop/mobile review pass. The western preview and source overlays
were inspected. Use `lower-lea-region.html?elevation=trial&area=western`.
No 3D or flood mesh changed; existing reviewed patches and structures remain
intact. Continue consequential coverage gaps and terrain/structure joins.


## Northern marsh lanes — 2 October 2026

Added 13 directly inspected observations around Homerton Road, Temple Mills
Road/Lane, Old Lea and Waterworks River (10 street, 3 ground). Four existing
Templemills Road/Lane dots now have direct surface reviews. The supplemental
file holds 40 additions in total; the audit has 3,978 observations, preserving
the original snapshot and source index. Two inferred Hackney Cut observations
(22.6 and 21.4 ft) proved to be bank/towpath dots, not railway-side road/ground.
The audit retains their original settings alongside reviewed classifications.

A sixth interpolation exclusion follows the uncoloured double-line drain
west of Temple Mills. Source crops and overlay establish its route; the
conservative envelope prevents interpolation across it. The trace ends at
this mosaic edge and does not supply a hydraulic level or barrier. Other
narrow drains farther east still need tracing before terrain extends there.

The trial uses 1,110 controls (136 ground, 974 streets), with 1,926 accepted
triangles and 16.0731 km² of supported raster, an increase of 0.0648 km².
The isolated northern 16.9 ft ground dot remains unsupported. Evidence within
250 m now covers 55.16% of the sampled dry river corridor, up from 51.50%.
Evidence proximity does not imply a supported terrain surface.

Supported holdout MAE remains 0.236 m ground and 0.257 m streets; all three
new ground holdouts are unsupported, so these averages do not validate the
new sparse marsh area. No new >1 m residual appeared in this batch. Numerical,
source, exclusion, regional and browser checks pass; source overlays inspected.
Use `lower-lea-region.html?elevation=trial&area=northern` for the new view.
The main scene and flood solver have not received these trial elevations.


## Hackney Marsh interior — 2 October 2026

Added 15 directly checked marsh observations: 11 interior ground dots and four
on the unhatched path toward Homerton Road. Native dots, source hashes and 6x
crops are retained in the regional supplement, now 55 additions. The audit
contains 3,993 records; the immutable source snapshot and index remain intact.
Maps around the isolated Waterworks River dot chiefly supply bank and siding
levels, so the pass followed the clear marsh traverse to the west instead.

The trial now has 1,125 candidates (151 ground, 974 streets), 1,939 accepted
triangles and 16.1862 km² of supported raster, up 11.31 hectares. Ten new dots
participate in triangles. Five northwest dots on the nearly straight survey
traverse remain unsupported, as does the previous isolated Waterworks dot.
The new surface joins the Homerton Road coverage without crossing Old Lea;
source-map overlays were inspected. Existing six exclusions remain in force.

River-corridor evidence proximity within 250 m increases to 57.30%, from 55.16%.
This is distinct from supported surface area. Supported ground holdout MAE is
0.233 m and street MAE 0.257 m. Only two of the 15 new holdouts are supported;
the averages do not establish uniform historical accuracy across the marsh.
No new residual exceeds one metre. Source/numerical and regional checks pass;
browser review covers the expanded Northern marsh review and existing views.
No main scene or flood-solver elevations changed.


## Cow Bridge and adjoining source coverage — 2 October 2026

Fetched 30 adjoining native NLS five-foot tiles and built three western
mosaics with the existing registration. This closes a source-cache gap without
changing the original reading manifest. Added two clear marsh readings east
of Water Works Bridge and six street readings around Maindee Street, Maiwand
Road, Pepin Road and Elmcroft Street. Sources, fixed hashes, native dot pixels
and 6x crops are retained. The supplement now has 63 observations, audit 4,001.

The two marsh dots continue the same nearly straight traverse; they remain
unsupported and do not close the northwest marsh surface gap. Six new street
dots support an additional 1.79 hectares west of the canal. The trial totals
1,133 candidates (153 ground, 980 roads), 1,943 accepted triangles and
16.2041 km² of supported raster.

Two additional conservative exclusion envelopes cover Hackney Cut, its banks
and towpath, and the parallel East London Water Works Waste Channel. Explicit
24-native-pixel margins include bank and join uncertainty. They prevent ground
interpolation across the corridor but do not define hydraulic levels, barriers
or calibrated widths. Source overlays confirm the street terrain stays west
of the corridor. Eight supplemental exclusions are now active.

River-corridor candidate proximity within 250 m reaches 58.94%; this still
must not be confused with surface support. Ground/street holdout mean absolute
errors are 0.233/0.256 m; only two new street holdouts are supported, and no
new residual exceeds one metre. Numerical, source, regional and browser checks
pass. The main scene and flood solver have not received trial elevations.


## Eastern Temple Mills lanes and drains — 2 October 2026

Confirmed seven existing lane/track readings, including three previously
classified as ground or marsh. These now have explicit street-surface reviews;
one resolved surface conflict retains its original flag and source setting.
Native source hashes, full-map context and enlarged reading crops are retained.
The audit still contains 4,001 observations, including 63 supplemental dots.

Traced missing flanking and field drains and the hatched bank north of the
Artificial Manure Works track. Twelve additional conservative exclusion
polygons bring the total to 20. They prevent interpolation across these
features; they do not establish hydraulic widths or bank/water levels.

The seven reviewed controls do not form supported triangles once these
boundaries are respected. Supported area remains 16.2041 km², with 1,943
accepted triangles and 1,105 participating controls. Total candidates rise
to 1,140 (153 ground, 987 streets). River-corridor evidence proximity within
250 m reaches 60.18%, which is distinct from supported terrain coverage.
All seven new holdouts are unsupported; existing supported ground/street
mean absolute errors remain 0.233/0.256 m, without a uniform accuracy claim.

The Eastern marsh review button and `?elevation=trial&area=eastern` link show
the remaining gaps. Numerical, source, regional and browser checks pass;
source overlays and the final preview were inspected. Interior observations
within the drain compartments remain necessary. The southern brickfield
drain/pool needs tracing before expansion into that area. No main scene or
flood-solver elevations changed.
