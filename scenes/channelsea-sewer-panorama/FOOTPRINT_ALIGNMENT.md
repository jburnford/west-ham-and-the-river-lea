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
