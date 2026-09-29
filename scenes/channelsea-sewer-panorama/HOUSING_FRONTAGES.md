# Housing and street frontage audit

The September 26 audit compares the model's housing and streets on the same source maps: OS London VIII.32, VIII.22, the supplied eastern mosaic, and the archived NLS five-foot map west of the Old Lea. The model now contains 76 street/lane traces and 112 retained housing ranges after the junction splits. The authored corrections are in [housing-road-traces.json](../../data/maps/housing-road-traces.json); original coarse housing traces remain intact for comparison.

## Corrections

- Added the missing residential street grids, including streets serving the northern and eastern housing. Corrected roads that previously ran along houses or rear plots.
- Re-read 50 housing records, including frontage labels and corner endpoints. Paul Street and several north-western and eastern axes had followed streets or back gardens. Some retained axes remain simplified main envelopes rather than individual footprints.
- Divided coarse terraces at mapped street junctions. Generated segments retain their original source-row ID and a record of the streets that caused the split. The builder rejects a split that would remove most of a row, requiring a source correction instead.
- Removed one duplicated eastern garden axis, `os-row-79`. Its neighbouring mapped frontages remain represented.
- Re-registered nine western rows to the common NLS map. Six additional axes from the older, approximate screenshot fall on open plots or institutional grounds in that map and are suppressed pending dated evidence. This is an uncertainty decision, not proof that later housing was absent. Three other western axes were already excluded for water/industrial conflicts.
- Cleared the western Three Mills Lane approach. Rear gardens have not been supplied with invented through-streets.

## Verification

`python3 scripts/check_housing_frontages.py` checks every rendered housing range: no street centreline through a house, no material housing overlap, and accessible parallel street frontage at seven or more of nine sampled points. The check uses actual rendered road surfaces and rejects approaches blocked by another housing range. The 16 m frontage reach allows front gardens and approximate envelopes; it does not establish historical access rights. It writes a per-range report to `reference/housing-street-audit/frontage-checks.json`.

`python3 scripts/review_housing_street_maps.py` overlays the corrected source axes and roads on each source sheet. Those blue envelopes precede the generated junction splits. `python3 scripts/review_district_streets.py` captures fourteen browser views, including five housing sectors. `check_scene_data.py` accounts for every original northern/eastern row through its retained segments or documented omission.

Rebuild with `build_panorama_data.py`, `build_southwest_context.py`, then `build_infrastructure.py`. Factory data must already be available; changes to district factory street corridors also require `build_factory_buildings.py` before infrastructure.

## Dense housing pass — 27 September 2026

`build_housing_detail.py` derives the rendered terrace layout from the existing source ranges. It retains all 108 terrace rows (the four separate Abbey Lane house ranges keep their individual models), giving 1,781 interpreted household frontages. Sixty-seven rows move towards their existing streets by up to 8 m where clearance permits. The original source centres remain recorded, and both the scene and its maps use the derived positions.

The 1,779 enclosed rear plots are clipped to their house bay, neighbouring plots, roads, rivers, railways and factory buildings. Opposing plots can meet at a shared boundary; there is no automatically generated back lane. The pass adds 1,733 attached sculleries, 1,641 privies and 4,307 wall segments. Forecourt paving reaches the existing street edge rather than leaving an accidental grass strip. Roofs, party-wall chimney groups, sash divisions, doors, gutters and downpipes distinguish the front from the rear.

These are estimated household arrangements within the mapped neighbourhood, following the author's preference for a close visual reconstruction. Plot depths are capped at 18 m; isolated or incomplete blocks can still have open ground beyond. Exact household plans and occupancy are not asserted.

Rebuild `build_housing_detail.py` after changes to housing, roads, factories or frontages, then `build_scene_manifest.py`. The application loads `docs/data/housing-detail.json` without rewriting the original mapped rows. `check_housing_detail.py` checks plot overlaps, road/water clearance, attached sculleries and contained outbuildings; `check_housing_frontages.py` now checks the derived rendered rows. Both passed. The browser review `review_factory_buildings.py --housing-only --url http://localhost:4175` captured seven views, including street level and rear yards, with no browser or shader errors.

Local destinations: `?view=housing`, `?view=housing-street`, and `?view=northern-housing`.

## Mill Meads block correction — 27 September 2026

The author's closer map prompted a second pass using the full-resolution VIII.32 image already held locally. `data/maps/mill-meads-housing.json` records 22 revised or added ranges and seven block envelopes in the source sheet's coordinate frame. It replaces the generic household count with 16 along the five principal Roberts/Beck/Lucas ranges, adds the missing west side of Napier Road, and adds six short Abbey Lane frontage ranges. Seven rows are added overall; the existing fifteen ranges are retained with revised main-body axes and dimensions.

Mapped block boundaries now constrain these rear plots instead of the global 18 m cap. Compact adjoining yards behind Roberts and Beck contrast with the deeper Godfrey/Napier/Ross plots. Earlier automatic movements towards streets are disabled for the revised ranges. Short return ranges are fitted clear of the approximately registered carriageways; their precise ends, counts and architectural elevations remain interpretations. The principal 16-house count follows the author's reading.

The current district layer contains 115 terrace rows, 1,864 household fronts, 1,862 yards, 1,805 sculleries and 1,716 privies. All 119 housing ranges, including the four separate Abbey Lane pairs, pass the street-access check. The 22 revised ranges also clear the full carriageway widths. The compact-versus-deep yard contrast and specified house counts have regression checks. Three local browser views review the revised blocks (`review_factory_buildings.py --millmeads-only`). The close destination is `?view=millmeads-blocks`.

## First remaining-district housing pass — 27 September 2026

The wider author map triggered a review of all 93 remaining terrace ranges. `data/maps/district-housing-review.json` records each retained range and 62 additions, supported by the saved full-resolution VIII.22/VIII.32 sheets, the eastern overview and locally archived NLS five-foot tiles. The accepted Mill Meads pass stays intact.

- Northwest: 23 added ranges around Gibbins, Blyth, Rosher, Grace, Leet and the upper Carpenters/Warton streets. Main street faces and short cross-street fronts now enclose the blocks that the earlier distant model omitted.
- Northeast: 19 added cross-street ranges, principally at St Thomas/Rokeby and Warton, complete the ends of the long Pitchford/Langthorne/Paul/Barnby/Hotham/Randal blocks. Existing Bridge Road end frontages are retained rather than duplicated. House divisions are estimated range by range.
- East: eight short Eastbourne/Portway frontages complete the Montague/Harcourt and southern street blocks. The existing diagonal street pattern is retained.
- West: 12 added ranges and re-registered retained housing around Priory, Franklin, Washington, Jefferson, Hancock, Sherman and Otis, using the larger-scale NLS source. Several previous street traces had been offset; six are replaced and the neighbouring streets added. The Empson/Imperial edge remains an approximate interpretation around the independently registered works and Three Mills approach.

There are now 177 terrace ranges, 2,972 interpreted house fronts, 2,963 enclosed yards, 2,863 sculleries and 2,743 privies. The four separate Abbey Lane house ranges remain individual models. Thirty-two reviewed block envelopes constrain the district plots; terraces facing each other across a street are not treated as sharing a rear boundary. House bodies are narrower in depth because the former rectangular envelopes included rear wings. New frontage axes are fitted to registered street edges and trimmed clear of neighbouring buildings; those adjustments are recorded in the generated data.

Rebuild order after source changes: `build_infrastructure.py`, `build_housing_detail.py`, then `build_infrastructure.py` again so road surfaces use the final housing envelopes, and `build_scene_manifest.py`. Infrastructure now reads the derived housing layout and the district review's street records. Constrained polygon triangulation removes the small uncovered junction fragments exposed at Hancock and Rosher roads.

Checks passed for all 181 rendered housing ranges, household plot clearance and source coverage, all 92 streets, the Great Eastern corridor, and the sewer/High Street crossing. Eight browser views cover the housing regions plus street and rear-yard details. Direct destinations: `?view=gibbins-leet`, `?view=eastern-housing`, `?view=portway-housing`, `?view=western-housing`.

These are close visual reconstructions: the review does not establish exact house plans, every commercial/residential use, or measured historic elevations. Schools, churches and corner shops still need distinct architectural treatment.

## Jute mill and West Ham gasworks correction — 27 September 2026

The author correctly identified that the earlier district pass left substantial gaps immediately beside the jute mill and around West Ham Gasworks. Reviewing existing row records was not sufficient evidence that the mapped blocks were complete. The full-resolution VIII.22 and VIII.32 sheets were inspected again at household scale for this correction.

Nineteen missing ranges are added and nine existing ranges are re-traced. Both Biggerstaff Road faces now appear beside the mill, together with the Warton end frontage, Preston/Robinson sides and short Carpenters/High Street ranges. Biggerstaff Road moves from the rear of its mill-side houses to the mapped carriageway between the terraces. The incorrectly named Wharton housing road becomes Preston Road; the school-side road becomes Robinson Road. Warton Road continues to High Street. The old “School frontage street” followed the backs of High Street plots and is removed; those houses face High Street instead. School and chapel sites are left out of housing infill.

Around the gasworks, the additions complete the principal missing Union/William street faces, the Stanley junction and gasworks-facing row, and the Stanley–Livingstone triangle. Union Court is a narrow mapped connection rather than a generic rear lane. Six new block masks retain the larger mapped rear plots and short corner plots. Source-sheet registration remains approximate, especially across the Stanley/Livingstone sheet boundary; source axes are retained alongside the final fitted positions. These are interpreted terraces, not a claim about every corner property's use or exact historic house count.

The district now contains 196 terrace ranges and 3,204 estimated household fronts, with 3,191 rear plots; four separate Abbey Lane paired-house ranges remain unchanged. `focusedReview` in `district-housing-review.json` identifies this pass explicitly. `fitToStreet` permits re-traced existing rows, as well as new rows, to be fitted clear of carriageways and neighbours. The accepted Mill Meads ranges remain unchanged.

Housing, street, railway, navigation and sewer checks pass. Three browser views inspect these specific areas, rather than using distant northeastern views as evidence of completion: `?view=jute-housing`, `?view=gasworks-housing`, and `?view=livingstone-housing`. Source-map overlays are saved in `reference/housing-street-audit/jute-gasworks-os22.png` and `stanley-livingstone-os32.png`.

## Remaining limits

The model still simplifies end houses, corner returns and front gardens. Rear extensions and plot walls now have an interpreted district-wide treatment; individual differences remain to be refined. Heights, house divisions, road widths and paving are interpretations. Descriptive road names indicate labels that have not been securely read. The source-map registrations are approximate and should not be treated as a measured survey.

Some connections away from housing frontages remain clipped by independently registered water or factory geometry: approximately 4.8 m on the Channelsea north approach, 20 m at the gasworks end of South Street, 6.7 m at the bank end of Channelsea Road, 9.9 m at a High Street context junction and 4.7 m at the Eastbourne Road end. The old Mill Mead riverbank path is also interrupted by the water mask. These require a separate bank/factory-boundary reconciliation; they do not justify adding undocumented bridges or lanes through gardens.
