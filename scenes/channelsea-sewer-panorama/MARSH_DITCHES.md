# Mill Meads ditches and relative water levels

Preview: http://localhost:4175/?view=marsh-ditches

The author's `ditches.png`, archived in `reference/marsh-ditches/user-map.png`,
identifies the marsh drains as an important landscape feature. Thirteen reaches
(about 1,472 m of centreline) are traced from the archived NLS five-foot map in
`data/maps/marsh-ditches.json`. The register retains source pixels, the mosaic
transform and metric routes. `reference/marsh-ditches/source-overlay.png` shows
the generated outlines on the source. Field boundaries without blue water
marking are not automatically converted into ditches.

Mapped interruptions remain at the central footpath and the separate northern
heads. No sluice, culvert or open breach through a riverbank is inferred solely
to make the blue lines connect. The generated channel outlines retain over 99%
of each traced envelope, while preserving the existing riverbank corridor,
roads, footpaths and buildings. Widths of 3–6 m and all sections are estimates.

## Relative levels

The author emphasises that the marsh lies below the rivers at high tide. This
pass therefore treats ditch beds, marsh ground and defensive riverbank crests
as distinct levels, rather than painting blue lines on flat land:

| Feature | Working local height |
|---|---:|
| Ditch bed | down to −0.40 m |
| Displayed low-water plane | 0.06 m, shared with Channelsea |
| Marsh surface | about 0.34 m |
| Illustrative regular high-water reference | 1.10 m |
| General earth-bank crest / retaining edge | about 1.65 m |
| Wall River photograph section | existing 2.05 m crest |

These numbers establish the intended relationship only. They are not measured
historic tide heights, surveyed drainage gradients, or a flood simulation. The
water starts at the existing low-tide display level. The Tide control can now
raise river water to the illustrative regular high-water reference. The earlier
1.40 m maximum was reduced by 0.30 m following the author's spillover review;
flood tides are outside the current control's range. Ditch pools stay at their
original level; this does not establish free tidal communication.

Open tidal banks now rise above the lower marsh. Narrow provisional masonry
retaining edges occupy industrial river frontages where a broad earth slope
would conflict with working plots. Their individual materials, heights and
extent still need photographic or engineering-plan evidence. They must not be
treated as a traced wall inventory or as the later 1930s concrete works. The
author's retained Old Lea exception remains excluded from the tidal treatment.

## Implementation and checks

`scripts/marsh_ditches.py` supplies shared geometry and sections to both the
extended network and the detailed Channelsea terrain, allowing the eastern
drains to cross the old scene boundary. Flat background ground is removed below
the new marsh surface. Water and mud expose the cut beds; the ditch network is
also present on the location maps. Allotment envelopes exclude the mapped
ditches, and their beds/sheds sample the extended terrain instead of a zero
height outside the former Channelsea grid.

Rebuild ground plan, detailed terrain and river network in that order:

```sh
python3 scripts/build_panorama_data.py
python3 scripts/build_river_terrain.py
python3 scripts/build_river_network.py
python3 scripts/check_marsh_ditches.py
python3 scripts/check_river_tides.py
python3 scripts/review_wall_river_vista.py
```

The new geometry check verifies mapped coverage, actual bed depth, lower marsh,
retained path gaps and clearance from allotments and protected riverbanks.
Browser views cover the marsh from above, at low level, and across the eastern
drain, alongside the existing river and street regression views.
