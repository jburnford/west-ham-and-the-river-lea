# Wall River photograph and High Street frontages

Open the working camera at **http://localhost:4175/?view=wall-vista**. The destination menu also has **Wall River — photograph study** and **High Street frontages**. The 6 m eye level is an estimate; district flight now permits heights down to 2 m for bank-level inspection.

The supplied photograph is `reference/Images and Figures/PossibleCover_Three Mills Wall London Fireworks Co 1900.jpg`. The supplied High Street screenshot is archived unchanged in `reference/wall-river-vista/highstreet-user-map.png`. Its map date is not independently established by the screenshot. Footprints use the already archived NLS five-foot mapping in the same coordinate frame as the factory ranges.

## Implemented

The [High Street register](../../data/maps/high-street-frontages.json) records 34 main envelopes between Bow Bridge and the Great Eastern railway, including corner ranges, the River Street/Bridge Street group, Harrow Wharf frontages and bank-side premises. Thirty-three produce additional rendered ranges; one is already covered or eliminated by the existing geometry masks. These are range envelopes, not 33 identified individual houses. Uses, precise rear additions and occupants remain unassigned. Heights, two-storey facades, pitched roofs and plain entrances are typological estimates.

Existing factory and housing ranges take precedence. Generated footprints are clipped against those buildings, streets, waterways and each other. Four additions retain less than 65% of their coarse source rectangle; their source and rendered areas are recorded explicitly. These need finer footprint tracing, particularly around side-lane junctions. New buildings appear on both location maps.

The [photographic study](../../data/maps/wall-river-vista.json) distinguishes visible features from metric estimates. It adds a 114 m worn path, close-boarded plot boundary, lower timber rail with braces, timber-retained bank toe and three leafless tree studies on the east bank. The underlying river relief is rebuilt to support the raised path. Individual tree positions, the 2.05 m crest, widths and timber construction are estimates. Two bank-side building placements are moved 8 m landward to reconcile source-map buildings with the GIS bank and keep the path clear; their source-registered footprints remain in the register. The western waterside range has an estimated masonry plinth.

## Camera and architectural limits

The first [refinement pass](REFINEMENT.md) connects both ends of the photograph
path to the surrounding routes, including the southern Wall lane approach to
Three Mills. Three explicit connection records carry their inferred alignment
and levels; clearance and endpoint tests cover them. The corner premises now
share the adjacent buildings' provisional 8 m landward adjustment and raised
ground-floor datum. Exposed tidal mud follows the author's district-wide tide
correction, so this low-tide scene is not a water-level match to the photograph.

This is a working comparison view, not a calibrated reconstruction. The broad grassy western margin, channel bends, foreground building details and distant warehouse proportions still differ from the photograph. No claim is made that the two foreground ranges have been positively identified. Neither the modern concrete embankments nor later channel engineering supplies this section.

The existing Sugar House is a candidate for the distant gabled mass. The [2008 heritage assessment, printed p21](https://www.newham.gov.uk/downloads/file/8216/document-20) describes its prominent asymmetrical gables and double-ridged roof. That resemblance does not by itself prove the camera position. [Clifford's article, footnote 13](https://jimclifford.wordpress.com/wp-content/uploads/2010/04/west-ham-hybrid-landscape.pdf) records the photograph's caption and interprets it as a high-tide view; that is not an independent level survey. The original archive reference, final photographic fit and detailed foreground facades remain to establish.

## Rebuild and review

After the ground plan, factories and infrastructure are current, run:

```sh
python3 scripts/build_high_street_frontages.py
python3 scripts/build_river_network.py
python3 scripts/check_high_street_frontages.py
python3 scripts/review_high_street_map.py
python3 scripts/review_wall_river_vista.py
```

The independent geometry check accounts for every source record, verifies clearance from other buildings, rendered roads and water, and checks the path for building/channel intersections. The browser review captures three candidate sightlines, a plan view and High Street. `review_district_navigation.py` checks the destination and direct URL alongside the existing controls. Reference photographs stay outside the public web root and are not used as textures.
