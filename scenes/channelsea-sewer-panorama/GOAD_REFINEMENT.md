# Factory-by-factory Goad refinement

The public [Layers of London Goad overlay](https://www.layersoflondon.org/map/overlays/goad-1887)
can be navigated directly with the browser. Overlay selection, hiding pins,
centering on factory coordinates and changing scale have been verified. The
read-only `scripts/research_goad_overlay.py --all-sites` captures the existing
factory register and the northeast jute mill. These are research references
outside `docs/`, not textures or runtime dependencies.

The site's **1887** layer title is not a safe date for every constituent sheet.
The matching original F2 and F4 sheets both have **July 1893** printed in their
headings. Original sheets are used for labels and tracing; the georeferenced OS
comparison controls model placement. Neither the web overlay nor our manual
registration should be treated as survey precision.

## First three sites

| Site | Implemented changes | Remaining uncertainty |
| --- | --- | --- |
| Imperial Sawmills, 797 | Six broad OS envelopes replaced by twelve mapped compartments: mill and veneer store, engine room, stoves, stable/dwelling, covered links and office. Iron roofs and an upper louvred window treatment follow legible notes. | Local map registration, metric heights, roof pitches, facade openings and exact working apparatus. Four northern OS ranges are Towers slaughterhouse context, a separate tenant, retained in this survey group. |
| Edward Cook & Co., East London Soap Works, 796 | Twenty-two broad OS envelopes replaced by 31 named production, storage and support ranges. Different heights distinguish the steam-copper ranges and warehouses. Bone/manure and tallow areas are recorded separately. | Approximate registration, some obscured storey marks, roof forms and detailed elevations. Mabbers & Son is identified as a neighbouring tenancy within the survey group. |
| Wm Ritchie & Sons, London Spinning Mills, 1017 | Eleven ranges added: the broad spinning/winding/weaving shed, preparing and batching rooms, calendering, warehouse, office, smithy, boiler/engine ranges and detached jute warehouse. Full supplied GIS parcel restored, open yard retained, three small interpreted bale groups added. Three adjacent street segments traced from OS. | Roof-bay profile, window arrangement, elevations and finer machinery details. The surrounding housing, complete street connections and railway-side ditch remain a further local pass. |

The jute mill was previously excluded as north of the railway. Its location
south/east of the now-correct main-line alignment places it inside the agreed
scene. The Goad plan identifies jute while the OS sheet labels the mill cotton;
the discrepancy is retained in the site record. It has not been resolved by
silently changing one source's wording.

The main jute shed's note mentions wood, glass, iron and slate roofing. Repeated
glazed roof bays are an interpretation of that note; their profile, number and
orientation are not measured historical northlights. Engine power recorded in
a range name is an annotation, not a model of the machine or a measured building
dimension. Map numbers have not been used as metre heights.

The [1876 account by W. Glenny Crory](https://www.mernick.org.uk/thhol/easlonind01.html)
identifies Ritchie & Sons and describes bale storage, linked production stages
and steam power. It is earlier contextual evidence, not a room-by-room plan
for 1893. His approving remarks about employers and working conditions are his
judgements, not neutral findings adopted by the reconstruction.

The author-supplied soap-works engraving is archived as
`reference/factory-building-survey/author-2026-09-27/east-london-soap-engraving-undated.jpg`.
It depicts a tall riverside block, lower adjoining buildings, repeated openings,
a chimney and the railway bridge. Its publication date and relationship to the
1893 ranges remain to be established; it has not overridden the dated plan.

## Survey status and repeatable checks

The [chimney-symbol pass](FACTORY_CHIMNEYS.md) adds 54 traced stacks across
19 site groups, including 19 adjacent height readings. It replaces the seven
earlier chimney entries and preserves their records. This is separate from the
still-pending detailed building reviews.

The [survey register](../../data/maps/factory-refinement-survey.json) records
which factories have received this refinement and which have only had an
overlay reference captured. The wider pass is **not complete**. Original source
envelopes superseded here remain in `supersededRanges` in the authored register.

Source-map comparisons:

- [Sawmill on OS](../../reference/factory-building-survey/review/goad-sawmill-os-overlay.png)
  and [Goad tracing](../../reference/factory-building-survey/review/goad-sawmill-source-overlay.png).
- [Soap works on OS](../../reference/factory-building-survey/review/goad-soap-os-overlay.png)
  and [Goad tracing](../../reference/factory-building-survey/review/goad-soap-source-overlay.png).
- [Jute mill on OS](../../reference/factory-building-survey/review/goad-jute-os-overlay.png)
  and [Goad tracing](../../reference/factory-building-survey/review/goad-jute-source-overlay.png).

```sh
python3 scripts/build_factory_buildings.py
python3 scripts/build_infrastructure.py
python3 scripts/build_factory_yards.py
python3 scripts/build_scene_manifest.py
python3 scripts/review_goad_factory_maps.py
python3 scripts/check_factory_buildings.py
python3 scripts/check_factory_yards.py
python3 scripts/check_great_eastern.py
python3 scripts/check_district_streets.py
node scripts/check_district_navigation.mjs
python3 scripts/review_factory_buildings.py --url http://localhost:4175 --goad-only
```

Local destinations: [sawmill](http://localhost:4175/?view=sawmill-yard),
[soap works](http://localhost:4175/?view=factory-796), and
[jute mill](http://localhost:4175/?view=ritchie-jute).
