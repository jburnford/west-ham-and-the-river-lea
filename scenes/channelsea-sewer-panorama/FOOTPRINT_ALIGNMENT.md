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
