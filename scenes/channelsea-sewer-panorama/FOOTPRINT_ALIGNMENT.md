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
In that first pass no source polygon was assigned to two models. Polygons with holes/multiple parts,
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

## Ink-works compound continuation, 28 September 2026

Thirteen additional ranges at Slater & Palmer / Marshgate Mills now match twelve
source polygons in ten reviewed groups. Together with the earlier eleven, this
aligns 24 of the site's 26 existing ranges, and brings the district total to 39
aligned factory ranges. The two remaining ranges are explicit source omissions.

The separate register `data/maps/ink-works-footprint-alignment.json` retains the
source polygons, original Goad envelopes, compartment divisions, height/roof
parameters and three chimney-base corrections. It is applied after the original
26-entry register. The reviewed mappings are:

| Goad/model range | Source feature IDs | Interpretation |
| --- | --- | --- |
| 25 and 26 | 2452 | Shared outer boundary; retain separate lampblack compartments and the chimney opening |
| 28 and 29 | 3305 | Shared outer boundary; retain the narrow southern range |
| 9 and 10 | 250895 | Two retained grinding bays within one OS outline |
| 2 | 102264, 52500 | Adjacent source polygons form the warehouse/office range |
| 4 | 52044, 592063 | Adjacent source polygons form the grinding-house range |
| 27 | 310941 | Individual lampblack chamber |
| 30 | 130019 | Individual lampblack store |
| 23 | 22797 | Boiler house, beside the previously corrected warehouse |
| 7 | 236901 | Mixing bay |
| 8 | 581251 | Mixing bay |

The OS mosaic `m18_131063_87137` and original July 1893 Goad F3 were inspected
together. The Goad registration had shifted the southern workshop row and small
end chambers by several metres. Shared source outlines are partitioned using
the relative widths of the original Goad compartments, with orientation fitted
to the source edges. These internal divisions remain interpretations; OS does
not independently establish them. Existing uses, floor marks, eaves heights,
roof rises, axes and bay counts are retained. No new factory ranges were added.

The western 80-foot chimney moves 4.50 m to base 1002254, inside a hole in outline
2452. That hole now survives into wall and roof geometry, with its interior walls
facing the opening. The other chimney bases move 0.96 m to 1087528 and 1.62 m to
954257. Their Goad height evidence and interpreted shaft profiles remain intact.

Source outlines 3305 and 130019 overlap by about 0.77 m² along a shared edge.
The register explicitly records this discrepancy; the smaller store takes
precedence in the rendered seam. Group-level rendered/source intersection over
union is at least 99.89%, compared with 17.1–84.9% before correction. This is
agreement with the supplied geometry, not historical accuracy.

`site940-firelighter` and `site940-24` are clearly visible on both period maps but
absent from the supplied extract in this location. Their existing Goad models
remain, pending separate OS tracing. Small source features without existing 3D
counterparts also remain in the flat plan layer; this pass does not claim to
model every ancillary structure or item of plant.

`prepare_ink_works_alignment.py` regenerates only these explicit reviewed groups
from the private source extract; it does not run nearest-polygon selection.
Routine builds need only the saved JSON. After the factory build, regenerate
infrastructure, factory yards, housing detail, regional footprints and the scene
manifest. `check_factory_footprint_alignment.py` verifies complete group coverage,
nonoverlapping internal divisions, preserved source holes and elevation evidence,
the documented seam exception and chimney placement, including the plinth fitting
inside the opening. The normal factory, yard, housing, Abbey, western-completion
and 77-destination checks pass.

Use `python3 scripts/review_factory_buildings.py --ink-only --url http://127.0.0.1:4175`
for the compound plan, lampblack ranges, workshop row and chimney opening.
All four views rendered without browser/shader errors and were visually
inspected. Browser diagnostics confirm all 507 ranges and the three corrected
chimney positions reached the renderer. Local asset revision: `1848da5c2e59`.
Private before/after overlays, OS/Goad comparisons and measurements are under
`reference/footprint-model-alignment/ink-*` and `verified-ink-groups.json`.

Next after the Imperial Saw Mills pass below: review Howards. The two
ink-works source omissions need direct map tracing rather than polygon matching.

First-pass verification: factory geometry/chimney checks, corrected-outline comparisons,
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

## Imperial Saw Mills continuation, 28 September 2026

Fourteen additional ranges in eight reviewed groups bring the district total to
53 source-linked factory ranges. All 16 existing ranges at site 797 now have
source matches, including the previously corrected stoves and covered stable.
The four northern ranges belong to the separate Towers slaughterhouse tenancy;
they retain their courtyard rather than becoming a single sawmill block.

`data/maps/sawmill-footprint-alignment.json` records these explicit matches:

| Model group | Source feature IDs | Interpretation |
| --- | --- | --- |
| Main mill | 858, 24984 | Seven retained Goad compartments within a shared outer boundary |
| Stable | 58007, 94509 | Two adjacent outlines form the existing range |
| Engine house | 201211 | Individual source outline |
| Office | 638578 | Individual source outline, with reviewed veneer-store seam |
| Towers north | 436569, 226632, 564637 | Courtyard range assembled from adjacent outlines |
| Towers east | 750620, 580324, 613094, 576605 | Courtyard range assembled from adjacent outlines |
| Towers west | 754482, 480984, 571284, 561604 | Courtyard range assembled from adjacent outlines |
| Towers south | 485487 | Detached courtyard entrance range |

The OS five-foot mosaic `m18_131060_87140` and July 1893 Goad F2 were inspected
together. The main outline is partitioned into the covered link, mill link,
three-storey small mill, eastern range, veneer store, basement mill and iron mill.
The register retains the interpreted cut coordinates, previous outlines, uses,
floor marks, louvred upper-storey evidence, basement notation and roof materials.
Existing eaves heights, roof rises, axes and bay counts remain unchanged.

The internal boiler chimney moves with the basement mill using its relative room
position. No separate source base was identified; its position and 30 m height
remain interpretations. The additional engine-side plant outline 455070 lacks
an existing model and remains in the regional plan layer pending plant review.

The old Cook’s Road chord cut through the corrected veneer store and office.
The short section beside the mill is retraced from the OS mosaic; the road width,
surface interpretation, route outside this section and bridge approach are
preserved. `district-road-traces.json` retains the previous trace and the reviewed
mosaic pixels. Generated roads and shoulders now clear the entire complex.

Office outline 638578 overlaps main outline 858 by about 0.20 m². This source
conflict is recorded explicitly; the taller veneer store takes precedence at the
rendered seam. Group-level rendered/source intersection over union is at least
99.53%, with the other seven groups above 99.99%. This measures agreement with
the supplied geometry, not historical accuracy.

`prepare_sawmill_alignment.py` regenerates only these reviewed groups from the
private extract. Routine builds use the saved register. After the factory build,
regenerate infrastructure, yards, housing detail, regional footprints and the
scene manifest. `check_sawmill_footprint_alignment.py` checks all 16 site ranges,
source coverage, preserved height/roof evidence, the courtyard opening, internal
chimney placement, Cook’s Road clearance and the retained bridge connection.
The district street audit now also includes Abbey’s separately rendered paths
and its replacement route list.

Factory/alignment, yard, housing, Abbey, western railway/industry, district street
and all 77 navigation checks pass. Five browser views (yard, plan, workshops,
Cook’s Road and Towers courtyard) rendered without browser/shader errors and
were visually inspected. Diagnostics confirm all 16 site ranges and the moved
chimney reached the renderer. Run
`python3 scripts/review_factory_buildings.py --sawmill-only --url http://127.0.0.1:4175`.
Local asset revision: `89260f10115c`. No commit or deployment.

Private comparisons and measurements are under
`reference/footprint-model-alignment/sawmill-*` and `verified-sawmill-groups.json`.
Next: Howards. Small plant features and the two ink-works source omissions remain
explicitly deferred.

## Oil Wharf continuation, 28 September 2026

The author's next priority was the oil yard beside the timber mill. The earlier
model contained two rectangles over mapped open ground, a large block spanning
the tank yard, and three displaced tanks. OS five-foot mosaics
`m18_131060_87140` / `m18_131057_87140` and July 1893 Goad F2 establish a much
more open arrangement. Goad labels petroleum stores, a filling shed, four iron
petroleum tanks and a separate northern disused tank. Its proposed additional
tanks are not modelled as existing structures.

`data/maps/oil-wharf-footprint-alignment.json` corrects five existing ranges,
adds four source-backed ranges and retains the earlier `oilwharf-2` filling-shed
match (18435). The two removed rectangles, `oilwharf-0` and `oilwharf-8`, retain
their prior records and reasons for reclassification. The site has ten ranges;
the district now has 509 ranges, of which 62 are linked to supplied footprints.

| Range | Source feature IDs | Interpretation |
| --- | --- | --- |
| Petroleum store F (`oilwharf-1`) | 5843 | Corrected waterfront store, clearing the tank yard |
| Roadside store N (`oilwharf-3`) | 85938 | Corrected store beside the filling shed |
| Detached store C (`oilwharf-4`) | 857458, 788844, 234020, 709244 | Adjacent OS compartments retained as one range |
| Cook’s Road dwellings (`oilwharf-5`) | 705774, 750552, 742081, 693202, 680145, 730406, 683899 | Contextual housing, distinguished from oil-production buildings |
| Northern stores (`oilwharf-7`) | 13285, 15121, 205514 | Petroleum stores B1/B2 and annexe A |
| Petroleum store E | 14095 | Newly represented adjoining waterfront range |
| Eastern store annexes | 35525, 583733 | Newly represented attached B/G ranges |
| Office | 692188, 776579, 904389, 923683, 1297524, 1132988, 1173979 | Office 538 and small attached compartments |
| Detached iron-roof range | 185430 | Range 544; specific use unresolved despite the internal `pump` ID |

Existing elevation/roof interpretations are retained. The four additions use
explicitly inferred low pitched envelopes; Goad's iron roof is retained on 544.
Dwelling elevations remain pending the grouped housing pass. Small source overlaps
of 0.37 m² at stores E/F and 0.16 m² at the filling shed/office are recorded and
partitioned at the rendered seams. Minimum new-group rendered/source intersection
over union is 99.928%; this is dataset agreement, not historical accuracy.

Tank outlines 73371 and 74874 fix two of the four petroleum-tank centres and
radii. The other two circles are missing from the extract, so their centres and
16.5-pixel radii are read from the OS mosaic. A local translation, fitted from
the two available circle centres, reconciles the roughly 1.7 m difference between
the map and supplied geometry. Source 73958 fixes the northern disused tank.
All five tank heights remain interpreted at 4 m, preserving the prior three
heights. No tank volume or modern operating status is inferred from these models.

The northern Cook’s Road trace formerly followed the southern kerb and clipped
the roadside stores. Its centreline is re-read between the mapped edges; the
sawmill frontage from mosaic pixel 400,458 onward and bridge approach are retained.
`district-road-traces.json` preserves both earlier reviews and source pixels.

A named Oil Wharf working envelope replaces anonymous context in this area. It
follows the mapped yard arrangement approximately, with six interpreted barrel
groups placed in clear space. The envelope, stock locations and surface finish
are not surveyed parcel or paving evidence. Yard surfaces, stock and regional
flat-plan masks now exclude the five tank bodies. The adjoining lime/cement
works, small detached features, cranes and gates remain deferred.

Routine builds read the saved JSON. `prepare_oil_wharf_alignment.py` regenerates
only the explicit reviewed matches from the private source extract.
`check_oil_wharf_alignment.py` checks coverage, elevations, documented seams,
tank separation, water/road/building clearance and the reopened yard. Rebuild
factory data, infrastructure, yards, housing detail, regional masks and manifest.
The usual factory, previous alignment, sawmill, street, yard, housing, Abbey,
western-completion and 77-destination checks pass.

Source crops, before/after overlays and measured results remain private under
`reference/footprint-model-alignment/oilwharf-*` and `verified-oil-wharf.json`.

Six browser views passed without browser/shader errors and were visually
inspected: plan, tanks, waterfront stores, northern stores, Cook’s Road and the
neighbouring sawmill frontage. Diagnostics confirm all ten ranges and five tank
positions/radii/heights reached the renderer. Use
`python3 scripts/review_factory_buildings.py --oil-wharf-only --url http://127.0.0.1:4175`.
Local asset revision: `886ca5c58068`. The preceding Abbey/ink/sawmill work was
committed locally as `7f078c0`; this Oil Wharf continuation remains uncommitted.

## Howards continuation, recovered 29 September 2026

The Howards / City Mills pass was implemented on 28 September and its interrupted
browser review completed after the WSL restart on 29 September. It accounts for
all 86 existing site-260 ranges, preserving their Goad uses and elevation evidence:

- 83 ranges match 101 supplied polygons in 53 explicitly reviewed groups.
- Old mill 644, missing from the extract, uses four corners traced directly from
  the georeferenced OS five-foot mosaic. Its existing photographic interpretation
  of the pale upper exterior and roof is retained.
- Shed 524 retains its dimensions and relative position beside process house
  520, rotating/translating with that match. The tiny source circle initially
  considered nearby is not claimed as a shed footprint.
- Detached riverside shed 620 remains at its Goad trace pending a direct OS trace.

`data/maps/howards-footprint-alignment.json` records the source polygons, previous
outlines, compartment divisions, height/roof parameters and unresolved evidence.
Shared external outlines include the northern mills, central workshops, salts
compound, ether/acid departments, Quinine and mercurial/potash works. Internal
divisions use the earlier Goad proportions and remain interpreted. Five small
source overlaps (0.049–0.342 m²) are retained in the evidence and resolved at the
rendered seams. Minimum rendered group agreement is 99.157%, a geometric measure
against the supplied extract, not historical accuracy. District totals remain
509 ranges and 89 chimneys; 145 ranges now link to supplied footprints.

All eighteen Howards chimneys move with the corrected plan. Two identifiable
OS bases (1092039 and 1223064) supply independent centres; sixteen other positions
are transferred with their local departments using relative Goad positions.
Existing shaft heights and profiles remain unchanged.

`data/maps/city-mills-bank-alignment.json` records twelve local bank-vertex
corrections, with previous positions and inspected OS mosaic pixels. These clear
the southern island buildings and retain the narrow millrace and its connections.
The old mill's intentional crossing remains explicitly recorded; no other Howards
range overlaps water. The opposite bank and the wider Old Lea connectivity are
outside this correction.

Routine rebuilds use the saved registers. For bank changes, build panorama data,
factory buildings, infrastructure, river network, factory yards, housing detail,
regional footprints and the scene manifest in that order. Recreating the Howards
register with `prepare_howards_alignment.py` additionally requires the private
source extract, OS mosaic and `howards-before.json` snapshot.

`check_howards_alignment.py` verifies complete accounting, source-group coverage,
preserved elevation evidence, seams, all chimney positions, local bank changes,
millrace continuity and water clearance. Factory, earlier alignment, yards,
housing, Abbey, western-completion, streets and all 77 navigation destinations
also pass. Seven desktop browser views were visually inspected: overview,
northern works, Epsom court, Quinine, old mill, mercurial works and southern ranges.
No browser/shader errors occurred; diagnostics confirm all 86 ranges and eighteen
corrected chimney positions reached the renderer.

Run `python3 scripts/review_factory_buildings.py --howards-only --url http://127.0.0.1:4175`.
Private source overlays and measurements are under
`reference/footprint-model-alignment/howards-*` and `verified-howards.json`;
browser captures and `howards-alignment-checks.json` are under the scene's
`review/` directory. Local asset revision: `b579ba9706a5`, verified against the
public asset hashes after restart. No deployment or mobile audit.

Next: Sugar House Lane groups and the remaining factory sites. Howards shed 620
and the two ink-works omissions remain separate direct-tracing tasks; housing
still needs a grouped row/rear-extension/yard pass.

## Sugar House, cooperage and Winstone, 29 September 2026

Eighteen ranges now use nineteen supplied polygons in fourteen reviewed groups
at eastern Sugar House Lane (site 964). Fifteen existing ranges are corrected;
three omitted low cooperage compartments are added. With the earlier range-14
match, nineteen of the site's 31 ranges are aligned. District totals are now
512 ranges and 163 source-linked ranges; chimney and factory-site counts remain
89 and 43. This pass covers the cooperage and Winstone compound, not all the
northern Crystal Wharf or southern Barber buildings.

The register is `data/maps/sugar-house-footprint-alignment.json`. Its saved source
geometry and earlier footprints support routine builds without the private
extract. `prepare_sugar_house_alignment.py` reconstructs it from that extract,
the OS mosaic and the saved `reference/footprint-model-alignment/sugar-before.json`.
Do not replace that pre-pass snapshot with current generated data.

| Model ranges | Source IDs | Reviewed interpretation |
| --- | --- | --- |
| 1, 3, 4, 6 | 1231 | Winstone main works, retaining four Goad compartments |
| 2 | 91401 | Winstone southeast range |
| 5 | 305125, 1075088 | Goad 594 acid chamber |
| 7 | 13976 | 1882 Sugar House, five storeys and paired roof retained |
| 8 | 10438, 950788, 952756 | Main cooperage and its small projecting bays |
| 9 | 193674 | Southern boiler range |
| 10, 11 | 10706 | Beam house and arched-cellar range, split at the mapped elbow |
| 12 | 832965 | Boiler room |
| 13 | 823808, 837886 | Entrance office |
| 15 | 4803 | Banding warehouse and sawmill, with chimney opening |
| 16 | 619800 | Mechanical shop |
| Added western sawmill | 101293 | Goad 566, low adjoining volume |
| Added stable | 65393 | Goad 578, separate low stable |
| Added southern rooms | 112632, 329600 | Goad 580 and eastern annex |

The earlier Goad use/height/roof evidence remains attached to existing ranges.
Winstone's main roof axis follows its northern wall rather than the oblique
southern street frontage. The beam house and cellar retain different roof
directions within their shared exterior. New low compartments use an estimated
3.8 m eaves height and 2.2 m roof rise; their source plans are firmer evidence
than those elevations. This does not resolve the construction dates of later
Sugar House additions identified in the archaeological survey.

The sawmill chimney now uses base 1142465 inside source 4803's opening. Its
22 m height remains an estimate. The interpreted shaft radius changes from
1.05 to 0.65 m so the rendered plinth fits the mapped opening with clearance;
the source does not establish an exact shaft profile.

Sugar House Lane's cooperage-side controls move slightly west and the works
passage moves into the mapped gap south of Winstone's buildings. Prior points,
map pixels and local review coordinates are retained in `district-road-traces.json`.
Widths and surface interpretations remain unchanged, with the passage still
joining the lane. Four small source-edge overlaps and a 0.038 m² street-buffer
corner sliver remain explicit in the register and are cleared in the renderer.
Minimum rendered group/source agreement is 99.855%, not historical accuracy.

The original parcel layer omitted much of the cooperage yard. A separate
map-informed envelope (yard 96401, parent site 964) now supplies approximately
3,946 m² of working surface after exclusions, with two small timber groups.
Ground finish, wear routes and stock are interpreted. There are now 83 yard
surfaces, 33 clear wear routes and 161 stock groups across the district.

Rebuilt factory buildings, infrastructure, river-network road exclusions, yards,
housing clearances, regional plan masks and the scene manifest. The dedicated
`check_sugar_house_alignment.py` covers source/compartment accounting, preserved
elevations, separate roof directions, chimney-plinth clearance, road-junction
continuity and yard coverage. Factory, earlier alignment, yards, housing,
streets, Abbey, western-completion and 77 navigation checks pass.

The focused browser review is
`python3 scripts/review_factory_buildings.py --sugar-house-only --url http://127.0.0.1:4175`.
All six final views passed and were visually inspected after the yard correction,
covering the site plan, warehouse, cooperage, chimney opening, Winstone works
and works passage. Diagnostics confirm all 31 eastern ranges and the corrected
chimney with no browser/shader errors. Asset revision `f8b93c9befe9` matches all
public asset hashes. Captures and diagnostics are in the scene's private `review/`
directory; source overlays and `verified-sugar-house.json` remain under
`reference/footprint-model-alignment/`. No deployment or mobile audit.

Next review site 964 ranges 17–28 (Barber and Crystal Wharf / Dane / Talbot).
The Goad overlay shows that several previous Crystal Wharf rectangles partly
cover open yard; reclassify them from map evidence before assigning source IDs.
Then continue western site 947 and sites 256/572/573. Their before-state and
labelled OS/Goad comparisons are saved alongside this pass.


## West of the cooperage — 29 September 2026

After committing the preceding work as `6dc446d`, the author prioritized the
western side of Sugar House Lane. `west-sugar-footprint-alignment.json` records
38 aligned ranges in 34 reviewed groups using 58 supplied source polygons.
All 27 existing site-947 ranges are corrected, with eleven additional rooms at
Hodson, Dane, Winstone and Wildash. Previous heights, roof rises and bay counts
remain; the new low volumes have explicitly interpreted elevations.

The northern Hodson factory/warehouse and courtyard perimeter retain separate
compartments within shared OS outlines. Victoria Buildings retain the joined
tenement exteriors. The Dane calcining rooms, Winstone's detached stores and
large riverside hall, and the Wildash court are now registered separately.
Two old site-569 rectangles duplicate Wildash rooms drawn at the edge of Goad
F17 (the repeated F30 block and label 892). Their full prior records are retained
as removed duplicates; Kendrick's two actual ranges remain. Small Goad 876 and
882/884 annexes, minor roof projections and equipment remain explicit omissions.

Chimney bases 1107028, 1031260 and 1108526 supply three corrected stack positions.
Two interpreted base radii narrow to 0.65 m to fit their mapped plinths. The
fourth stack transfers within its Goad 860 room without claiming an independent
OS base; all four previous 22 m shaft heights remain.

`west-sugar-bank-alignment.json` reconciles ten local Three Mills Back River
controls. Four opposite-bank points move slightly west to preserve an open
channel alongside the corrected waterfront buildings. Bridge connections and
banks beyond this local section remain. Sugar House Lane is re-read through the
opposing works frontages, whose narrowest mapped gap is 7.85 m. Its interpreted
carriageway changes from 7 to 5.2 m with additional bend controls and retained
southern connections. Two High Street controls shift northwest by 2.5 m to
clear the machinery store. Prior points and source pixels are preserved in
`westSugarAlignment`; these reconciliations are not surveyed road/bank dimensions.

Three supplied-outline seam overlaps (0.019–0.221 m²) and one 0.021 m² pavement
mitre are explicitly recorded. Minimum rendered group agreement is 99.874%.
This measures geometric agreement, not historical architectural accuracy.

Browser inspection identified missing working ground in the original parcel
layer. Yard 94701 restores the OS/Goad industrial-ground envelope between Dane,
Winstone, Wildash, the lane and the river. Its exclusions follow the corrected
buildings and access; finish remains interpreted. No equipment or stock is added.
It does not claim one occupier or an exact cadastral boundary.

The reproducible authoring script is `prepare_west_sugar_alignment.py`; it needs
the private source extract and immutable `west-sugar-before.json` snapshot.
Routine builds use the saved register alone. `check_west_sugar_alignment.py`
checks group unions, inherited elevations, rendered clipping, duplicate removal,
chimney bases, road clearance, channel continuity and restored yard coverage.

All geometry, earlier alignment, yard, housing, street, Abbey, western-completion
and 77-destination checks passed. The focused browser command is
`python3 scripts/review_factory_buildings.py --west-sugar-only --url http://127.0.0.1:4175`.
Its seven views cover the plan, Hodson, river frontage, Dane, Winstone, Wildash
and the narrow lane. All seven final views passed after yard restoration,
with the affected plan/Dane/Winstone/Wildash views visually inspected. No
browser/shader errors; all 38 western ranges and four stack positions confirmed.
Asset revision `268ce5651e76` matches all public hashes. Private captures and
diagnostics remain in `review/`.
The district now has 521 ranges, 43 sites, 89 chimneys and 201 source-linked
ranges. The western continuation remains local and uncommitted; no deployment.

Next: the remaining eastern site-964 ranges 17–28 (Crystal Wharf / Dane / Talbot
and Barber), followed by sites 256/572/573. The old northern Crystal Wharf
rectangles require reclassification against Goad before any source assignment.


## Crystal Wharf, Barber and southern ink works — 29 September 2026

The next authorized continuation resolves all twelve formerly deferred site-964
ranges (17–28). `data/maps/crystal-barber-footprint-alignment.json` records
21 aligned ranges in 21 reviewed groups: eight existing ranges corrected and
thirteen separately identified rooms added. Four earlier rectangles, ranges
24–27, cover labelled open Crystal Wharf/cooperage yard on Goad F3 and are
removed, with their complete prior records retained. Their replacement is the
actual mapped Talbot/Dane row to the north, not a nearest-polygon assignment.
All 40 current eastern Sugar House Lane ranges are now source-linked.

The northern additions follow Goad compartments 526–540. The surviving
cooperage wood shed (544) and office/dwelling (542) remain separately identified.
Southern additions include the Barber bone-shed annex, stable/loft (588), long
riverside shed (592), attached ink-factory rooms and shed 610. The attached
southern rooms retain the supplied small opening. Every source ID and exterior
is saved in the register. Existing eaves heights, roof rises, axes and bay counts
are retained. New low rooms use interpreted 3.8 m eaves; Dane 528 uses 5.35 m,
informed by its Goad 1½-floor annotation. These are not measured elevations.

Southern chimney base 1230955 fixes the stack position between the Barber
courtyard range and riverside shed. Its interpreted radius narrows from 1.05 to
0.5 m so its plinth fits the mapped base; the previous 22 m height remains.
The northern boiler chimney transfers within corrected Dane compartment 532
near its southern dividing wall. No independent OS base is claimed; its printed
50 ft height remains 15.24 m. The earlier cooperage chimney is unchanged.

Two separately recorded working-ground envelopes, yards 96402 and 96403, restore
Crystal Wharf/Talbot and Barber/southern ink-works surfaces. Buildings, roads,
water and chimney bases are excluded. Finish remains interpreted; these are
not cadastral or single-occupier claims, and no stock or equipment is added.
Roads and riverbanks require no additional changes in this pass. Small isolated
features/plant bases 1217966, 1065632 and 1242744 remain deferred rather than
being classified as complete buildings.

`prepare_crystal_barber_alignment.py` uses the private footprint extract, OS
mosaic and immutable `reference/footprint-model-alignment/crystal-barber-before.json`.
Routine builds use the saved register. `check_crystal_barber_alignment.py`
checks the old/new accounting, unique source use, retained heights and roofs,
source exteriors, openings, stack bases, road/water clearance and yard coverage.
Minimum rendered source agreement is 99.977%, a geometric comparison only.

Factory, all earlier alignment, yard, housing, street, Abbey, western-completion
and 77 navigation checks pass. The focused browser command is
`python3 scripts/review_factory_buildings.py --crystal-barber-only --url http://127.0.0.1:4175`.
All seven views were visually inspected: Crystal plan, oblique, open yard and
boiler chimney, Barber plan and chimney, and the southern ink courtyard. No
browser/shader errors; all 40 eastern ranges and three chimney positions
confirmed. Source overlays and review exports remain local. Asset revision
`964a1116a09c` matches all public asset hashes. No mobile audit or deployment.

Current district totals: 530 ranges, 43 sites, 89 chimneys, 222 source-linked
ranges, 85 yards, 35 wear routes and 160 stock groups. Both this and the western
continuation remain uncommitted after `6dc446d`. Next review sites 256/572/573.


## High Street starch, tin-box and confectionery works — 29 September 2026

`data/maps/abbey-west-footprint-alignment.json` records eighteen source-linked
ranges in fifteen reviewed groups. Sites 256, 572 and 573 now contain 5, 3 and 8
ranges respectively, all linked to supplied exteriors. Two additional matches
resolve the immediately adjoining Bow Bridge office and smithy, site 254 ranges
15/14. The district total is 240 source-linked ranges at fifteen sites.

The original rectangles need substantial re-registration. Several cross the
High Street houses or open factory yards. Source 2797 supplies the complete
Harvey and Neville starch exterior, divided into the retained northern factory,
eastern stoves and southern rooms. The three room divisions are approximate
Goad interpretations within that exterior, not surveyed OS party walls. Source
25658 similarly retains two adjoining pickle/preserve compartments. The former
starch range 4 lies across the Goad domestic/shop frontage at number 89: its
industrial volume is removed and the full prior record retained. This does not
claim that the domestic frontage has received a housing reconstruction pass.

Bryant and May's main tin-box factory uses sources 26098/652278/927475, the
japanning room and stoves use 22346/1039391/838929, and the eastern store uses
827748. The large Hogarth confectionery factory follows source 1902. Its western
rooms/office, eastern compartments and riverside stables remain separate ranges.
Four omitted rooms are added: engine/boiler room 35713, corrugated courtyard shed
506627, the southern eastern-room group and southern end range 16280 (Goad 635).
All source IDs and saved geometries are in the register. Existing heights, roof
rises, bay counts and axes are retained; new 3.8 m eaves and pitched roofs are
explicit estimates. A source footprint does not establish these elevations.

Hogarth's Goad 624 engine chimney moves to independent source base 993523. Its
previous interpreted 22 m height and 1.05 m radius remain. The rendered plinth
fits within the source base and clears the surrounding factory roofs.

The corrected western Hogarth rooms exposed neighbouring Bow Bridge envelopes
that had crossed their boundary. OS/Goad F17 matches place the office (502) at
493587 and smithy (504) at 492587/838996. Process ranges 12/13 transfer with the
office correction, approximately 1.21 m west and 5.83 m south, keeping their
existing forms and elevations. These two transfers have no independent source
exteriors and are excluded from the matched count. Their full plant and boundary
interpretation awaits the remaining Bow Bridge works pass; this is a local
boundary reconciliation, not a completed site-254 survey.

A 0.52 m² starch-frontage corner meets the existing High Street pavement corridor.
The source and street controls are retained and that corner is cleared by the
renderer. No road or riverbank authoring changes are required. Minimum rendered
group agreement is 99.933%, measuring geometry only. Minor back-frontage stores
and starch plant features remain explicit omissions. Existing yard surfaces are
regenerated against the new buildings: 85 yards, 36 wear routes, 159 stock groups.

`prepare_abbey_west_alignment.py` requires the private supplied-footprint extract
and immutable `reference/footprint-model-alignment/abbey-west-before.json`.
Routine builds use the saved register alone. `check_abbey_west_alignment.py`
checks source accounting, shared-compartment unions, retained elevations, the
domestic reclassification, chimney plinth, neighbour transfers and clearances.
Factory, all previous alignments, yards, housing, streets, Abbey, western
completion and all 77 navigation destinations pass.

The focused browser command is
`python3 scripts/review_factory_buildings.py --abbey-west-only --url http://127.0.0.1:4175`.
Seven views passed and were visually inspected: overall plan, starch works,
High Street frontage, tin-box rooms, Hogarth compound, chimney base and the Bow
Bridge boundary. All sixteen site-256/572/573 ranges and the corrected stack
position reached the renderer without browser/shader errors. Asset revision
`0967fc8d0e4d` matches every public asset hash. No mobile audit or deployment.

Current totals: 533 ranges, 43 sites and 89 chimneys. This pass and the preceding
western/Crystal continuations remain local and uncommitted after `6dc446d`.
Next: the remaining Bow Bridge bone and chemical works (254), including its
provisional process-room transfers and mapped plant classification.

## Bow Bridge bone and chemical works, 29 September 2026

The site-254 continuation accounts for seventeen ranges: twelve supplied-outline
matches, including the two earlier office/smithy matches, and five direct OS
traces. Ten newly source-linked ranges in seven groups bring the district total
to 250 at fifteen sites. Two omitted rooms are added. Heights, roof forms and
internal Goad divisions remain interpretations.

Authoring register: `data/maps/bow-works-footprint-alignment.json`, prepared by
`scripts/prepare_bow_works_alignment.py`. Supplied-outline groups:

| Goad use / number | Supplied source IDs | Current ranges |
| --- | --- | --- |
| Animal charcoal warehouse 500 | 7377 | added charcoal warehouse |
| Bone mill 506 | 9935 | 13 |
| Mill annex 508 | 236456 | added mill annex |
| Bones shed 522 | 42611 | 3 |
| Stable / bone store 518 | 624951 | 4 |
| Crushing 524 | 214735, 1012516, 1027327, 900941 | 9, 8 |
| Boiling 532–536 | 9807 | 7, 10, 11 |

The large continuous factory body is hatched on OS but absent from the supplied
extract. Its exterior is traced from the cached OS mosaic and divided into five
Goad rooms: ammonia/retorts 510/512 (range 12), bone store 514 (1), tallow/bone
boiling 516 (2), stores 520 (5) and manure 526/528 (6). These records use
`os-1893-direct-trace` and do not claim supplied source IDs. Adjacent mapped rooms
and chimney bases are excluded from the body; a sub-square-metre disconnected
tracing seam is discarded. The northern western bend was checked against OS
before the final build. The earlier provisional transfers of ranges 12/13 are
explicitly superseded. Effective district totals are six direct traces and two
local transfers, avoiding stale double-counting of those earlier records.

Four independent chimney bases are matched: 1011348 (printed 100 ft), 1089134
(60 ft), 1172266 (50 ft) and newly added retort base 1044201 (50 ft / 15.24 m).
The first three interpreted shaft radii reduce to 1.2, 0.8 and 0.65 m so their
plinths fit the mapped openings; the new shaft radius is 0.85 m. The boiling
house's other stack transfers within its corrected Goad room, retaining its
interpreted 22 m height without claiming an independent base. Source 9807's
chimney opening is retained. All four independent plinths fit their mapped bases
and clear rendered building volumes; all five shaft positions clear water.

`data/maps/bow-works-bank-alignment.json` moves ten works-side River Lea controls
west by 1.8–5.3 m to reconcile the simplified water polygon with the OS walls.
The opposite bank and wider Old Lea connections remain unchanged. The local
channel retains at least 6.15 m between reviewed bank segments. This is local
map reconciliation, not a surveyed shoreline. Hunt's neighbouring site-564 range
1 moves provisionally 2 m south, removing a 9.16 m² overlap with the corrected
boiling house while retaining its form and elevations. That transfer remains
outside the source-linked count pending the full soap-works review. Roads are
unchanged by this pass.

The Goad 530 open-under structure, water tower, tanks and small projections
remain deferred plant features. They are not filled with generic building
volumes. The immutable private snapshots are
`reference/footprint-model-alignment/bow-works-before.json` and
`bow-works-ground-before.json`; preparation also needs the private source extract
and cached maps. Routine builds use the saved JSON registers.

The ground plan, buildings, infrastructure, river mesh, yards, housing exclusions,
regional footprint masks and manifest are regenerated. District totals are
535 ranges, 43 sites, 90 chimneys, 85 yards, 36 wear routes and 159 stock groups.
The new Bow checker and all earlier alignment, factory, yard, housing, street,
Abbey, western and 77-destination navigation checks pass. Minimum rendered
supplied-outline group agreement is 99.979%, a geometry comparison rather than
a historical-accuracy score. Direct traces are checked separately against the
saved OS exterior and compartment partition.

`python3 scripts/review_factory_buildings.py --bow-works-only --url http://127.0.0.1:4175`
passed seven visually inspected views: plan, mill, process rooms, retorts, manure,
boiling and riverbank. All seventeen ranges and five chimney positions reached
the renderer without browser or shader errors. Asset revision `6ee0ae172d9a`
matches all 25 module and 139 asset hashes. No mobile audit or deployment.
This pass and the western, Crystal/Barber and High Street continuations remain
uncommitted after factory commit `6dc446d`. Next: Hunt's Bow Bridge soap works,
site 564, currently seven ranges.

## Hunt's Bow Bridge soap works, 29 September 2026

All ten current site-564 ranges now link to supplied outlines in six reviewed
groups. Seven existing ranges are corrected and three omitted rooms are added,
bringing the district to 538 ranges and 260 source-linked ranges at sixteen
sites. The authoring register is `data/maps/hunt-works-footprint-alignment.json`,
prepared by `scripts/prepare_hunt_works_alignment.py`.

| Mapped group | Supplied source IDs | Ranges |
| --- | --- | --- |
| Main process body and southern projection | 1461, 938428 | existing 1–5 |
| Stables, Goad 554 | 73603 | existing 6 |
| Dwelling, Goad 552 | 381084 | existing 7 |
| Western furnace rooms | 100277 | added |
| Office/laboratory, Goad 538 | 842322 | added |
| Southern engine room | 858006 | added |

The continuous OS process exterior retains five interpreted Goad compartments:
northern boiling/cutting/drying/packing, central process rooms with boilers,
southern bay 548, southeastern room 550 and smithy 542. Their previous eaves,
roof rise, direction and bay counts are retained. The Goad sheet records
admission refused, so the interior divisions remain approximate. The separate
stables retain low eaves and the dwelling retains its interpreted two-storey
6.9 m eaves. New rooms use interpreted 3.8 m eaves and low pitched roofs. The
provisional 2 m transfer of range 1 from the Bow Bridge pass is superseded; only
Howards shed 524 remains in the effective local-transfer count.

The boiler chimney is placed on supplied base 1013155, retaining its printed
80-foot height (24.384 m) and interpreted 1.05 m radius. Its plinth fits the base
and clears building roofs. The western shaft has no independent supplied base:
its position transfers proportionally with the corrected process body, then
moves 2 m east and south to retain the Goad relationship inside the process
rooms beside the furnace wing. Its inferred 22 m height remains unchanged.

The simplified River Lea polygon crossed about 20 m² of the newly restored
furnace outline. `data/maps/hunt-works-bank-alignment.json` adjusts works-side
vertices 39 and 40 west by 1 m and 3.5 m respectively. Vertex 39 follows the
earlier Bow Bridge correction. The opposite bank is retained; the checked local
channel remains 23.98 m wide. This is map reconciliation, not a surveyed bank.
All ten building outlines clear buffered water and road corridors, and Hunt's
rooms no longer overlap the corrected Bow Bridge boiling house.

Sources 859135, 1062021, 1001071, 969335 and 1228456 remain deferred tank/platform
and small service details. The western empties strip and lightweight sheds
also need separate yard/plant interpretation. No generic full-height room is
assigned to those features. Private OS/Goad comparisons and the immutable
`hunt-works-before.json` and `hunt-works-ground-before.json` snapshots are under
`reference/footprint-model-alignment/`. Preparation requires those snapshots and
the private source extract; routine builds use the saved registers.

The dependent ground, infrastructure, river mesh, yards, housing exclusions,
regional masks and cache manifest are rebuilt. There are 43 sites, 538 ranges,
90 chimneys, 85 yards, 36 wear routes and 160 stock groups. No road authoring or
new yard envelope is introduced in this pass. Minimum rendered supplied-outline
group agreement is 99.977%, a geometry comparison rather than an architectural
accuracy measure.

The Hunt checker, all prior factory alignment checks, factory/yard/housing,
street, Abbey, western and 77 navigation checks pass. The focused command
`python3 scripts/review_factory_buildings.py --hunt-works-only --url http://127.0.0.1:4175`
passed six visually inspected views: plan, process rooms, furnaces, boilers,
stables/dwelling and the Bow Bridge boundary. All ten ranges and two chimney
positions reached the renderer without browser/shader errors. Asset revision
`73acc66175bb` matches all 25 module and 139 asset hashes. No mobile audit or
deployment. This and the four preceding continuations remain uncommitted after
factory commit `6dc446d`. Next: Lascelles stone/terra cotta and British Ultramarine
works, sites 565/566, currently three ranges each.

## Commit checkpoint, 29 September 2026

At the author's request, the western Sugar House, Crystal/Barber, High Street,
Bow Bridge and Hunt continuations were committed as `527d3e9`,
“Align western Sugar House, High Street and Bow Bridge factory footprints.”
The 46-file commit includes authoring registers, generators/checks, dependent
scene assets and documentation. Height-extraction work and `docs2/` were excluded.
No push or deployment. The author then requested the continuation below.

## Lascelles / British Ultramarine, 29 September 2026

Six existing ranges at sites 565/566 now link to supplied outlines in five groups.
No ranges are added or removed. The district remains at 538 ranges, 43 sites and
90 chimneys, with 266 source-linked ranges at eighteen sites.
`data/maps/lascelles-ultramarine-footprint-alignment.json` is prepared by
`scripts/prepare_lascelles_ultramarine_alignment.py`; routine builds need only
the saved register.

| Group | Supplied source IDs | Model ranges |
| --- | --- | --- |
| Lascelles main terra cotta factory | 6127 | 565-1 |
| Lascelles southern room, Goad 628 | 102625 | 565-2 |
| Lascelles northern room, Goad 626 | 473976 | 565-3 |
| Ultramarine main process house | 5241, 4566 | 566-1 |
| Ultramarine southern bays | 13778, 48472 | 566-2/3 |

The supplied Ultramarine polygons stop at opposing edges of the OS sheet join,
leaving a roughly 1.2 m registration gap. Goad shows a continuous works body.
Two narrow, explicitly saved connector polygons reconcile that join: about
22.41 m² in the main house and 20.32 m² in the southern bays. They join only the
paired sheet edges, preserving the exterior walls and source 13778's chimney
hole. The source polygons remain unmodified in the evidence register; connector
geometry is a separate interpretation. Existing southern bay proportions, all
eaves heights, roof rises, directions and bay counts are retained.

Lascelles' rendered groups agree with raw supplied outlines by at least 99.987%.
Ultramarine's raw-source agreement is 98.161% for the main house and 95.723% for
the southern bays because the rendered bodies include the recorded join strips.
Agreement with the reconciled outlines is about 99.999%. These measures test
geometry, not historical architectural accuracy.

The Ultramarine chimney moves to independent base 986471, retaining the printed
60-foot height (18.288 m) and interpreted 1.05 m radius. Its plinth fits the base
and retained roof opening. The final Sugar House Lane control moves 3.5 m west:
the former coarse road/pavement corridor clipped 34.02 m² from the process house.
The revised corridor was inspected against the OS gap between the works; width
remains 5.2 m and all upstream controls are unchanged. Original points and pixel
coordinates remain in the road register's `lascellesUltramarineAlignment` record.
Both works now clear roads, water and neighbouring building volumes without
losing their supplied exterior to renderer clipping. Bank authoring is unchanged.

Small projections 1105121 and 908578 remain deferred. Northern Williams wharf
rooms and the boundary lean-to (sources 108655, 445081, 59238, 585845 and 656439)
remain for the full site-568 review, including the omitted Goad 704 room and
range 17's affiliation. Existing adjoining models are retained. Private OS/Goad
comparisons, the road overlay and immutable `lascelles-ultramarine-before.json`
are under `reference/footprint-model-alignment/`. Preparation needs that snapshot,
the private footprint extract and cached OS maps.

Infrastructure, yards, housing exclusions, regional masks and the manifest are
rebuilt. Yard totals are 85 surfaces, 38 clear wear routes and 160 stock groups;
no new yard envelope is introduced. The new checker, earlier alignment checks,
factory, street, yard, housing, Abbey, western and 77 navigation checks pass.

The six browser views passed and were visually inspected: plan, Lascelles
factory, lane, Ultramarine process house, chimney opening and Williams boundary.
All six ranges and the corrected chimney reached the renderer without browser
or shader errors using the review tool's new `--software-gl` option. Two earlier
hardware-backed WSL attempts lost their WebGL context, so the successful run
used SwiftShader. The report records that backend; public rendering settings
are unchanged. This is not a hardware compatibility or mobile audit.

Asset revision `42e380428366` matches all 25 module and 139 asset hashes.
Preparation was rerun to verify that neither the joins nor lane control move
again. The pass remains uncommitted after `527d3e9`; no push or deployment.
Next: Williams wharf / French Asphalte (568), including the Ultramarine boundary,
then site 567. Broader Lascelles/Ultramarine working-ground envelopes remain for
a separate parcel review; existing ground coverage stays provisional there.


## Williams wharf / French Asphalte, 29 September 2026

The register `data/maps/williams-asphalte-footprint-alignment.json` accounts for
all eighteen existing ranges, restores the omitted Goad 704 room, and corrects
the site attribution of the boundary lean-to. Seventeen ranges are source-linked
in fourteen groups; two eastern Asphalte rooms absent from the extract are
separate direct OS traces. The district now has 539 ranges, 90 chimneys and
283 source-linked ranges at nineteen sites, plus eight direct traces and one
local Goad transfer.

| Group | Supplied source IDs | Models |
| --- | --- | --- |
| Asphalte dwelling 668 | 179094 | 568-1 |
| Asphalte stables 670 | 65438 | 568-2 |
| Asphalte west 674/672 | 5501, 739969 | 568-3/4/10/11 |
| Engine room | 190393, 499290 | 568-5 |
| Tank-over bay / eastern boilers | 161128 / 114965 | 568-7 / 568-8 |
| Northern process 680 / storage 676 | Direct OS traces | 568-6 / 568-9 |
| Williams 694 / 696 / 698 | 225068 / 693774 / 64119 | 568-12 / 568-13 / 568-14 |
| Williams 700 / 702 | 108655 / 445081, 59238 | 568-15 / 568-16 |
| Ultramarine boundary lean-to | 656439 | 568-17, reassigned to site 566 |
| Williams riverside 706 | 148247 | 568-18 |
| Williams 704 | 585845 | new 568-704 |

The source extract stops at the vertical OS sheet edge through the Asphalte
works. The missing eastern walls are visible in the cached five-foot map. The
western group retains all supplied geometry and adds an explicitly recorded
127.897 m² map completion. Its raw-source agreement is 82.186%, compared with
23.212% before alignment; agreement with the completed reference is 99.998%.
These are geometric comparisons, not historical-accuracy scores. Source geometry,
completion polygon, mosaic bounds and pixel coordinates remain independently
reviewable. The four Goad west-body compartments use interpreted north/south
cuts; the narrow seam tip joins the furnace bay below. Room 680's direct trace
is trimmed against the supplied engine/tank edges to avoid duplicate volumes.

Goad F17 places the boundary lean-to south of Williams' dividing wall, inside
British Ultramarine. Its existing ID is retained with `priorSiteId` and attribution
evidence; site 566 gains that fourth range. Added room 704 has Goad's two-floor
mark and an interpreted 6.9 m eaves height. All eighteen existing heights, roof
rises, axes and bay counts are preserved. No storey estimate is silently changed.

The eastern chimney follows mapped base 1087863 and retains its printed 60 feet
(18.288 m). Its interpreted radius narrows from 1.05 to 0.65 m so the plinth fits
the mapped base. The other chimney keeps its inferred 22 m height and transfers
within the corrected 674 compartment; no independent mapped base is asserted.

Sugar House Lane's controls 12 and 13 move 1.5 m west within the mapped lane,
removing over 15 m² of corridor overlap with the Asphalte dwelling and Williams
694/700. Width 5.2 m and all other controls, including the preceding Ultramarine
correction, remain. Earlier coordinates/pixels are saved in
`williamsAsphalteAlignment`; the checker verifies the complete chain of changes.

`prepare_williams_asphalte_alignment.py` requires the private source extract,
cached OS tiles and immutable `williams-asphalte-before.json`. Routine builds
use only the saved register. If regenerating multiple authoring registers, apply
this preparation after Lascelles/Ultramarine so the lane corrections remain in
order. `check_williams_asphalte_alignment.py` checks supplied-source uniqueness,
raw/completed geometry, trace coordinates, retained elevations, site attribution,
road/water/neighbour clearance, both chimney placements and the 60-foot plinth.

Small service projections 1008000, 905626, 895423, 915272, 965896, 1042207 and
1042217 remain deferred for classification. Broader working-ground envelopes
for this block still need an OS parcel review. Rebuilt existing yards have
85 surfaces, 36 clear wear routes and 161 stock groups; no yard is added here.

Validation: all new and preceding alignment checks, factory clearance, yards,
housing, streets, Abbey, western completion and 77 navigation checks pass.
The preparation is byte-for-byte idempotent. Six browser views passed using
SwiftShader and were visually inspected: Asphalte plan/process/boilers, Williams
plan/riverfront and the Ultramarine boundary. All eighteen site-568 ranges,
the reassigned lean-to and both corrected chimney positions reached the renderer;
no browser or shader errors were reported. This is a software-rendering review,
not a new hardware or mobile audit. The broad provisional grass areas remain
part of the deferred yard-envelope review.

Asset revision `b02fb580dce5` matches all 25 module and 139 asset hashes. Regional
masking covers 234,606 visible features in 115 tiles (4.01 MB). This continuation
and the preceding Lascelles/Ultramarine pass remain local and uncommitted after
`527d3e9`. Next: site 567, oil refinery / machinery and printing (thirteen ranges).


## Refinery / printing works / machinery depot, 29 September 2026

`data/maps/refinery-printing-footprint-alignment.json` resolves all thirteen
previous site-567 ranges and adds five omitted rooms. Seventeen ranges match
supplied outlines; the northern storage shed is directly traced from OS. The
scene now has 544 ranges, 43 sites and 90 chimneys, with 300 source-linked ranges
at twenty sites, nine direct OS traces and one local Goad transfer. Goad identifies
separate printing, varnish, machinery-depot, oil-storage and tar-boiling uses
within the older aggregate site label; the revised names retain those distinctions.

| Range / use | Supplied source IDs |
| --- | --- |
| 567-1, colour mixing | 299098 |
| 567-2, printing engine and southern rooms | 435489, 808632 |
| 567-3, varnish range | 236310, 835502, 1030800, 1052054 |
| 567-4, varnish boiling | 859743 |
| 567-5, varnish store | 693111 |
| 567-6, depot 658 | 486602 |
| 567-7, depot factory | 222267 |
| 567-8, low depot 654 | 150510 |
| 567-9, shed 666 | 87744 |
| 567-10, smithy 664/662 | 38428 |
| 567-11, stables and boiler house | 23884 |
| 567-12, eastern printing rooms | 299237, 829931 |
| Added 652 | 872149 |
| Added oil stores 686 | 822606, 842580 |
| Added oil stores 685 / 684 | 753096 / 554547 |
| Added tar-boiling room 682 | 311225 |
| 567-13, northern storage shed 688 | Direct OS trace; absent from extract |

The storage trace retains its southern projections and ten recorded map corners,
with mosaic bounds and source pixels saved independently. The thirteen existing
eaves heights, roof rises, axes and bay counts remain unchanged. Added low rooms
use interpreted 3.8 m eaves; Goad 682 labels an iron roof but no measured height
is claimed. Small features 1004609 and 964482, the ramp outlines 775297/774492,
and an ambiguous northern open bay adjoining 660 remain explicitly deferred.

Both Goad chimney symbols have identifiable OS bases: 1201365 beside the printing
engine and 1146475 beside depot room 658. Their inferred 22 m heights remain.
Interpreted radii narrow from 1.05 m to 0.45/0.55 m respectively so the plinths
fit the mapped bases and clear the adjacent rooms. Neither height is a printed
map measurement.

The old Sugar House Lane corridor cut roughly 65 m² from the two western printing
ranges. Re-reading the centreline introduces two bend controls and shifts the
neighbouring controls locally. The opposing supplied façades at 567-1 and 947-24
leave only 6.712 m. The existing 5.2 m carriageway fits, but a default 1.1 m
pavement on each side does not. The road register therefore records a 0.55 m
minimum building clearance for four specific façades (567-1/2 and 947-24/25).
This is an interpreted clearance, not a surveyed pavement width.

`factory_street_clearance.py` applies that explicit exception to building
exclusions. Infrastructure already clips pavement meshes against the retained
walls, so the actual pavements narrow naturally while the carriageway remains
continuous. Other buildings keep the default clearance. Saved prior road points
and pixels, the replacement segment and affected model IDs make this reversible.
The works passage reconnects to the revised lane and its eastern endpoint moves
4.2 m north, clearing storage shed 688; its 4 m width and middle control remain.
Earlier lane and passage checks verify the chain of corrections.

`prepare_refinery_printing_alignment.py` requires the private extract, cached
OS tiles and immutable `reference/footprint-model-alignment/refinery-printing-before.json`.
It is byte-for-byte idempotent. If regenerating authoring registers, run it after
Lascelles/Ultramarine and Williams/Asphalte so road changes are applied in order.
Routine scene builds use saved JSON. The dedicated checker verifies independent
source IDs, exact rendered exteriors, the OS trace, preserved elevations, road
connections, both mapped plinths and the narrow frontage on both sides.
Minimum rendered source agreement is 99.980%; this geometric measure is not a
historical-accuracy score.

The factory, infrastructure, yard, housing and regional layers are regenerated.
Existing yard exclusions give 85 surfaces, 37 clear wear routes and 160 stock
groups. No new working-ground envelope is introduced. The broader neighbouring
yard-envelope review remains separate.

All new and prior alignment checks, factory/road/water clearance, yards, housing,
Abbey, western completion and 77 navigation checks pass. Six SwiftShader browser
views passed and were visually inspected: plan, printing frontage, narrow lane,
machinery-depot court, oil/tar rooms and northern storage. All eighteen ranges
and both corrected chimney positions reached the renderer, without browser or
shader errors. Hardware and mobile rendering were not re-audited.

Asset revision `962666bb4d46` matches all 25 module and 139 asset hashes. Regional
masking covers 234,589 visible features in 115 tiles (4.01 MB). This pass remains
uncommitted alongside Lascelles/Ultramarine and Williams/Asphalte after `527d3e9`.
Next: Kendrick northern works (569), checking its overlap with already linked
947-25/source 16620, then Usher (570) and Kendrick southern works (571).

## Kendrick northern/southern works and Usher — 29 September 2026

`kendrick-usher-footprint-alignment.json` accounts for the seven existing ranges
at sites 569/570/571 and restores two rooms. Eight resulting ranges are linked
to supplied outlines; Usher's main L-shaped factory is a direct OS trace.
The district now has 546 ranges, 308 source-linked ranges at twenty-three sites,
ten direct OS traces and one local Goad transfer. Existing heights, roof rises,
axes and bay counts are retained.

| Model / Goad room | Supplied source features |
| --- | --- |
| 569-2, northern stables | 709193, 707542 |
| 569-3, northern boiler works 600 | 20821 plus explicit OS completion |
| 570-1, northern rooms 608/610 | 667726, 664504 |
| 570-2, main factory 606 | Direct OS trace; supplied body absent beyond sheet seam |
| 570-3, southern room 614 | 763215 |
| 570-4, engine/boiler rooms 616 | 802249, 892564, 1182516 |
| Added varnish-coppers room 612 | 767195 |
| 571-1, southern boiler works 622 | 186608 plus explicit OS completion |
| Added two-floor room 620 | 189399 |

The northern Kendrick shed is separate from already linked 947-25/source 16620.
The misleading overlap came from its old approximate rectangle. A 0.056 m²
independent-digitisation overlap is removed in favour of that prior neighbour;
both original source geometries remain available in their registers.

All three compounds cross the same source-extract sheet seam. The northern
Kendrick completion adds 52.907 m² and the southern completion adds 127.850 m²,
joining the independently supplied eastern two-floor room. Their map pixels,
mosaic bounds and source polygons are saved separately. Raw source agreement
is 81.723% and 37.506% respectively because the extract omits these sections;
agreement with the explicitly reconciled outlines is at least 99.998%.
These are geometric checks, not historical-accuracy scores.

Usher's L-shaped exterior follows the cached OS wall lines. Its western
compartment division follows the retained engine-room vector edge, and an
opening preserves independent chimney base 1154445. The square shaft moves
there and retains its printed 40 ft (12.192 m) height. Its interpreted radius
narrows from 1.05 m to 0.5 m so the plinth fits the mapped opening.

The added varnish room uses interpreted one-floor/3.8 m eaves; no printed floor
count is claimed. Goad labels the eastern Kendrick room two floors, represented
by interpreted 6.9 m eaves. The northern 1–2-floor annotation lacks a clear
internal boundary, so its previous low model is retained. Goad labels the
southern range under construction in July 1893; the OS shows a continuous
footprint and the c.1900 model retains its earlier interpreted completed roof.
Small projection 1135652 remains deferred pending classification.

Two local lane-centre controls, saved under `kendrickUsherAlignment`, clear the
northern completed façade. Every previous control and the 5.2 m width remain;
no new pavement exception is introduced. The refinery checker now verifies its
prior correction against this pass's saved baseline, preserving the full chain.
Riverbanks are unchanged. Yard exclusions regenerate to 85 surfaces, 36 clear
wear routes and 160 stock groups; no new yard envelope is introduced.

Preparation requires the private extract, cached OS tiles and immutable
`reference/footprint-model-alignment/kendrick-usher-before.json`. It is
byte-for-byte idempotent. Regenerate it after the refinery/printing authoring
pass; routine scene builds use the saved JSON. The dedicated checker verifies
source uniqueness, original versus completed outlines, the traced L-shaped
body and chimney hole, retained elevations, road clearance, neighbouring
volumes and the mapped plinth. All earlier alignment checks and the regenerated
factory, road, yard, housing, Abbey, western and 77 navigation checks pass.

Six SwiftShader browser views passed and were visually inspected: compound plan,
northern yard and lane, Usher engine court and lane frontage, and southern
Kendrick range. All nine ranges and the corrected 40 ft chimney reached the
renderer without browser or shader errors. Asset revision `5461589935f6` matches
all 25 module and 139 asset hashes. Regional masking covers 234,579 visible
features in 115 tiles (4.01 MB). The pass remains uncommitted alongside the three
preceding continuations after `527d3e9`. Next: Three Mills distillery (419),
checking dedicated landmark models before matching its 37 current ranges.

## Northern Three Mills distillery — 29 September 2026

`three-mills-north-footprint-alignment.json` accounts for ranges 1–20 and 29,
plus restored timber room 828. Twenty ranges follow supplied outlines in fifteen
explicit groups; Goad 824 is a direct OS trace and small outbuilding 800 retains
a provisional local Goad placement. Site 419 now has 38 ranges, of which sixteen
southern/mill/wharf ranges await the next continuation. The district has 547
ranges, 328 source-linked ranges at twenty-four sites, eleven direct OS traces
and two provisional local Goad transfers. All twenty-one existing northern
height and roof interpretations are retained.

| Models / Goad rooms | Supplied source features |
| --- | --- |
| 419-1–5, dwellings 802–806 | 738916, 494587, 428628, 511713, 569447 respectively |
| 419-7, room 808 | 138138 |
| 419-8, northern range 818 | 30608, 63457 |
| 419-9–12, engine/boiler rooms 812/814/816 | 9057, 125904 |
| 419-13/14, process rooms 820/822 | 7180, 921093 |
| 419-16/17, three-floor ranges 840/838 | 1622 |
| 419-18, room 836 | 17105 |
| 419-19, rooms 832/834 | 26002 |
| 419-20, range 830 | 5218 |
| 419-29, room 826 | 886593 |
| Added one-floor timber room 828 | 118464 |
| 419-15, three-floor range 824 | Direct four-corner OS trace; absent from supplied extract |
| 419-6, small timber outbuilding 800 | Provisional local Goad transfer; no OS match |

The Goad plan expressly says admission was refused and the distillery was
sketched from outside observation. Internal room boundaries remain schematic.
Within the engine/boiler exterior, the northern 812 room, southern 814 room and
eastern 816 room are distinguished; two prior low roof bays remain within 814.
The two larger paired ranges use west/east divisions proportioned from Goad.
No claim is made that these internal cuts are independently surveyed walls.
Minimum agreement of rendered linked exteriors with the supplied polygons is
99.976%; this is geometric agreement, not a historical-accuracy score.

The former Goad 800 rectangle was miscentred over the footpath. Its centre was
re-read at Goad pixel 1221,2459 and locally translated using the five matched
dwelling centres, retaining its previous dimensions and elevation. Its separate
OS outline and persistence into c.1900 are not established. The saved record
explicitly preserves that uncertainty rather than assigning a source polygon.
The added 828 room has a Goad one-floor mark and timber colouring, represented
by interpreted 3.8 m eaves and a low gable.

The engine chimney follows independent round base 892638. Its inferred 31 m
height and 1.5 m radius remain; the plinth fits the mapped base and clears the
rooms. Tanks 869/870 follow circular sources 144175/145527, with 5.109/5.086 m fitted circular radii
and their prior inferred 6 m heights. The slightly irregular outlines have
equal-area radii that overlap by 0.078 m; fitting each circle inside its outline
keeps the vessels separate. Both radius calculations remain recorded. The metal tank stage 810, rectangular tank
813, ditch and small external projections remain deferred plant/yard features.

The old eastern road alignment cut more than 250 m² from the corrected northern
rooms. The public Three Mills Lane approach, 7 m width and bridge span remain
through the mill entrance. Its former eastern extension is replaced by a
separate 5.2 m interpreted works passage; the adjoining entrance is re-read at
the same width. Opposing mapped façades leave minimum gaps of 7.629 m beside the
engine/boiler block and 7.925 m by range 824, accommodating the ordinary 1.1 m
clearance either side. These widths remain interpretations, not pavement surveys.
Prior points, pixels and widths are saved under `threeMillsNorthAlignment`.
The two passage records connect exactly; the district now has 99 routes.
No bank changes are made, and all non-target factory render geometry is retained,
including House Mill, Clock Mill, kilns, wharves and the southern distillery.

`prepare_three_mills_north_alignment.py` requires the private extract, cached OS
map and immutable `three-mills-before.json` snapshot. It is byte-for-byte
idempotent and follows Kendrick/Usher in the full authoring sequence. Routine
scene builds use saved JSON. The dedicated checker verifies source uniqueness,
rendered exteriors, preserved elevations, the direct trace and provisional shed,
road connections and clearance, independent chimney/tank bases, and unchanged
surrounding factory geometry.

All prior and new alignment checks, factory/road/water clearances, yards, housing,
Abbey, western completion and 77 navigation checks pass. Six SwiftShader views
were checked visually; after fitting the tank radii, their focused view was
re-rendered and the final radii, centres and heights verified in the renderer.
No browser or shader errors occurred. Final asset revision `1669da522491` matches
all 25 module and 139 asset hashes. Regional masking covers 234,569 visible
features in 115 tiles (4.01 MB); yards remain 85 surfaces, 36 wear routes and
160 stock groups. This fifth continuation after `527d3e9` remains uncommitted.
Next: southern ranges 21–28, followed by the eight mill/wharf ranges.


## Southern Three Mills distillery — 29 September 2026

`three-mills-south-footprint-alignment.json` aligns eight existing ranges in five
reviewed groups. No building is added or removed: district totals remain 547
ranges at 43 sites, with 336 source-linked ranges at twenty-four sites, eleven
direct OS traces and two provisional local transfers.

| Existing ranges | Supplied source features | Interpretation |
| --- | --- | --- |
| 21–24 | 344 | Grain warehouse/kilns 846/848 and process rooms 850/852; preserve the open southern notch |
| 25 | 132768, 396886 | Southern room 854 |
| 26 | 34266, 835014 | Narrow range 854 and timber annex 856 |
| 27 | 27300, 27774, 26435, 64758, 38030, 912850, 822473, 809347 | Two-floor process block 858, including its western rooms |
| 28 | 36050 | Gas house 860 |

The warehouse/process split follows the mapped notch. Other divisions within
344 retain Goad width proportions, with interpreted internal walls and roofs.
Goad explicitly records an outside sketch survey after admission was refused.
All eight existing eaves heights, roof rises, axes and bay counts are retained;
the warehouse model still uses one height across its kiln end. Separate kiln
heights have not been reconstructed in this footprint pass.

The three existing tanks 863/864/865 follow circular sources 464133/458700/462633.
Their heights remain inferred at 6 m. Radii fit inside the supplied outlines at
the rounded rendered centres; equal-area radii are recorded for comparison.
Checks cover tank pairs, all factory bodies, roads and water before rebuilding.

Northern gangways 167022/29937, rounded feature 219295 and small wall projections
need separate roof/plant interpretation. Circular features 444596/486835 and
gas-house projections have no existing models and remain deferred. The eight
House/Clock Mill and wharf ranges are the next coordinated millrace review.

Authoring uses the immutable `three-mills-south-before.json` and private source
extract. `factory_alignment_records.py` is shared with the northern pass;
routine builds use saved JSON. The southern check supports `--preflight` so
source coverage, partitions, elevations and plant spacing settle before the
expensive dependent builds. The browser review reuses the common Three Mills
renderer checks and captures three focused views.

Yard checking found a barrel group inside a southern tank. Both generation and
validation now exclude all modeled tanks, replacing the Oil Wharf-only rule.
The rebuilt yards retain 85 surfaces, 36 wear routes and 160 stock groups, all
clear of the tank bodies. Regional coverage is 234,558 visible source features
in 115 tiles (4.01 MB); housing remains 196 rows / 3,204 houses / 3,191 rear yards.

Final southern browser review: all three SwiftShader views passed and were
visually inspected (`review/three-mills-south-{plan,tanks,court}.png`). The report
`review/three-mills-south-alignment-checks.json` confirms all 38 site ranges,
the engine chimney and five fitted tanks reach the renderer without browser or
shader errors. Final manifest: `9acadf9c9fc7`. Changes remain uncommitted.
