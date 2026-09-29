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

Rebuild ground plan, infrastructure and High Street data in that order. Run
`check_scene_data.py`, `check_district_streets.py`,
`check_sewer_high_street.mjs`, and `review_wall_river_vista.py`. The latter now
includes an overview, road-level approach and sewer-top approach at this junction.
