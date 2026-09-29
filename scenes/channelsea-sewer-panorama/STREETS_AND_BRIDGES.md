# District streets and bridges

The September 26 street pass adds Stratford High Street, Sugar House Lane, Marshgate Lane, Hunts Lane, River Street, Bridge Street, Bridge Court and a works passage. It retraces the Three Mills approach and yard lanes. The complete infrastructure layer now contains 76 routes and ten road crossing records. The location map shows roads and bridges; the **Fly to → Bridges** menu provides close views.

## Sources and date

Centrelines were read on the archived NLS georeferenced five-foot OS mapping revised in 1893, using the same scene origin as the factories. [Authored traces](../../data/maps/district-road-traces.json) retain source pixels and converted scene coordinates. Source-map overlays and reference images stay in `reference/district-streets/`, outside the public web root.

[Victoria County History, Essex VI, pp. 57–61](https://www.british-history.ac.uk/vch/essex/vol6/pp57-61) supplies the bridge chronology and structural families:

| Crossing | c1900 model |
|---|---|
| Bow Bridge | One granite-faced stone span, completed 1839. The iron replacement opened in 1906; construction began in 1901, overlapping the scene’s provisional date. This model uses the pre-construction form. |
| Pegshole Bridge | Two stone arches over Three Mills Back River. This is the nineteenth-century name, formerly St Thomas’s. |
| St Thomas’s Bridge | Brick, formerly Pegshole, over the western Waterworks arm. One opening is an estimate; the text does not establish its arch count. |
| St Michael’s / Harrow Bridge | One stone arch over the eastern Waterworks arm. |
| Channelsea Bridge, High Street | One stone span. Its layered earlier and widened arch fabric is simplified. |

The three intermediate bridges were replaced by Groves Bridge in 1933 during the 1931–35 river works. Those later structures and channels are excluded.

The user’s [1851 guide illustration](https://commons.wikimedia.org/wiki/File:ECR(1851)_p18b_-_Bow_Bridge.jpg) depicts the older multiple-arch bridge. The [Mackenzie painting](https://upload.wikimedia.org/wikipedia/commons/4/42/Frederick_Mackenzie_-_Bow_Bridge_-_9532.jpg) shows an earlier pointed arch. Both remain comparisons, not templates for the 1839 span. The old-bridge plan reproduced on [LondonWiki](https://londonwiki.co.uk/StratfordHistory/HistoryofBowBridge.shtml) likewise records the earlier structure.

## Geometry and limitations

The [Northern Outfall Sewer/High Street review](SEWER_HIGH_STREET.md) corrects
the earlier assumption that every road passed below the sewer crest. High Street
passes over the enclosed sewer; its surface and the sewer-top approaches now
meet, with the walkway and railings interrupted at the carriageway.

Road widths, paving, levels, bridge clearances and arch proportions are estimates. High Street and selected working lanes use interpreted setts; other streets retain macadam or cinder surfaces. No paving assignment establishes street adoption status. Bridge approaches include supporting fill.

The street overlay exposed conflicts with approximate factory envelopes. The builder now reserves the mapped street and pavement corridors before partitioning ranges. Selected Sugar House Lane, Magnet Wharf and Three Mills frontage placements were corrected, with their previous offsets retained. Source envelopes stay in the evidence register; rendered footprints record the street trim separately. All 434 ranges remain represented. These corrections improve physical consistency but are not a measured building survey.

Three short connections at Marshgate Lane, Hunts Lane and the Three Mills yard reconcile discrepancies between road traces and independently registered GIS banks. They are explicitly labelled **provisional connection** in the destination menu. Their deck versus culvert construction and exact bank lines remain unresolved. They should not be cited as three documented historical bridges.

The [housing frontage audit](HOUSING_FRONTAGES.md) now clears the western Three Mills approach by correcting the independent housing registration. It adds residential streets, revises misplaced building axes and splits coarse rows at junctions. A 4.8 m gap on the northern Channelsea approach remains a GIS-bank discrepancy outside the explicit bridge span; no additional historical crossing has been invented.

## Verification

Run `python3 scripts/build_factory_buildings.py` before `python3 scripts/build_infrastructure.py` when street traces change. The factory builder uses the street corridors, and infrastructure then uses the corrected factory footprints.

`python3 scripts/check_district_streets.py` checks the five High Street structural families, the explicit provisional status of the other connections, road/factory clearance and internal street continuity. It requires the western approach to be continuous and bounds the separate Channelsea bank discrepancy. The factory geometry checker still verifies all 32 groups and 434 ranges. `python3 scripts/review_district_streets.py` renders fourteen overview, bridge and housing views in the real application; `python3 scripts/review_district_navigation.py` exercises the live navigation controls, including the bridge menu.
