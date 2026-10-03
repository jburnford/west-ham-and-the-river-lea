# Northern Outfall Sewer at High Street

Preview: http://localhost:4175/?view=sewer-high-street

The user's `sewerhighstreet.png` shows the critical bend: the sewer runs broadly
westward from High Street and southeast toward Abbey Mills. The previous model
extrapolated the Abbey Mills bearing 1,400 m northwest through the junction.
The replacement western trace is registered to the archived NLS five-foot OS
mapping, with source pixels and converted coordinates retained in
`data/maps/sewer-high-street.json`. Its intersection with the current High Street
trace is approximately (-564.9, -364.7) in scene metres.

High Street passes **over the enclosed sewer**. It does not pass under a
continuous elevated sewer-top walkway. The OS road remains uninterrupted at
the crossing. Thames Water's [18 December 2024 engineering account](https://www.thameswater.co.uk/news/2024/dec/nos-stratford-glass-lining)
identifies the sewer beneath High Street as supporting the carriageway and
describes the Victorian pipes as dating from 1860–65. That establishes the
crossing relationship; the modern works do not establish the precise 1900
facade, road width or barrel count. No modern repair details are modelled.

The render now cuts the sewer-top surface and railings at the carriageway,
grades their approach to meet the street, and keeps the enclosed cover below
the crossing. The nearby side streets receive only the local junction transition,
not a blanket height increase. The Channelsea viewing platform remains at its
existing reference height.

The 3.5 m crossing surface remains an **estimate**. The visible OS road spot
height near the crossing reads 24.7 ft, against BM 22.40 ft at St Michael's.
Their roughly 0.7 m difference, applied to the existing 2.8 m bridge estimate,
sets a working local relationship. It does not calibrate the district's absolute
datum. Approach lengths, cover depth, surrounding ground levels and the
nineteenth-century internal section remain unresolved. The graded top surface
is not a sewer invert: do not infer a hydraulic gradient from it.

The inspected western trace ends beyond the Great Eastern Main Line. The
remaining eastern extension is still the earlier skyline interpretation.
The sewer's railway crossing and river aqueduct structures need separate
period evidence; they are not settled by this High Street correction.

## Channelsea enclosure and elevation dependencies — 30 September 2026

The author identified the crossing as a platform without its sewer. Inspection
found only the 0.48 m fascia in the current renderer and the saved earlier
renderer; no enclosure was being rendered. This was not traced to deletion
by the new terrain overlay. `docs/sewer-crossing.js` now adds an enclosed
girder mass beneath the deck and two bank abutments. The local photograph
`reference/Images and Figures/NewNewhamImages/Channelsea River & Abbey Mills Pumping Station.jpg`
shows the deep stiffened girder face, but does not provide surveyed dimensions
or a securely established pre-rebuilding date.

[Historic England 1392549](https://historicengland.org.uk/listing/the-list/list-entry/1392549?section=official-list-entry)
describes the 1900–02 rebuilding, with five nine-foot sewers replacing three,
and two central piers. This repair does not backdate those five barrels or
assign central pier locations to the earlier crossing. The 60 m exterior
reach, 2.9 m enclosure depth below the existing 0.5 m cover, plate spacing,
bank abutment sections and foundation embedment are working assumptions.
The enclosure follows every existing route bend; bank support footprints
lie outside the mapped waterways. Internal sections and hydraulic inverts
remain unknown. This is provisional exterior massing, not a calibrated
hydraulic obstruction or a finished reconstruction of either bridge phase.

The deck, enclosure and support tops share `sewerSurfaceHeight`; the walking
camera already follows the same Channelsea crest reference. Foundation bottoms
sample the local ground at the support centre and corners. A change to sewer
height moves the structure and walker together; a ground change adjusts the
support height without moving the sewer. A support whose ground rises above
its bearing now fails visibly instead of silently creating inverted geometry.

`node scripts/check_sewer_crossing.mjs` raycasts the actual generated enclosure
below both channels and across the walking width, including the joined bends,
then changes sewer and ground levels independently to
check these relationships. `review_historic_elevation.py --sewer-only` renders
both river faces in baseline and 1900 modes, checks the enclosure and support
geometry diagnostics, and retains the high-tide and surrounding-infrastructure
checks. The standard terrain review now includes these exterior views too.

Rebuild ground plan, infrastructure and High Street data in that order. Run
`check_scene_data.py`, `check_district_streets.py`,
`check_sewer_high_street.mjs`, and `review_wall_river_vista.py`. The latter now
includes an overview, road-level approach and sewer-top approach at this junction.
