# Reconstruction scope and evidence — 25 September 2026

28 September terrain research expands to the historic West Ham borough plus
a 3 km buffer. See [terrain sources and coverage](TOPOGRAPHY_RESEARCH.md).
This is a terrain study extent; the detailed factory brief remains separate.

Latest author direction: continue until all factories are covered, **building by building**.
The [completed factory coverage register](FACTORY_BUILDINGS.md) records 434 ranges
across 32 sites, the retained Abbey Mill and explicit exclusions at the agreed boundaries.

## Author-defined extent

The current expansion covers the area bounded by:

| Edge | Boundary |
| --- | --- |
| North | **Great Eastern Main Line**, north of City Mills |
| South | **Bromley-by-Bow gasworks**, including the works as southern context |
| East | **Channelsea River** |
| West | **Old River Lea** |

Include City Mills / Howards and Sons, Sugar House Lane, the marsh housing,
Mill Mead, Three Mills and its distillery, and the Bromley gasworks. The author
explicitly distinguished the northern main line from the Woolwich branch
already represented beside the Channelsea. These are research/model-development
limits, not a newly surveyed polygon or an implemented camera restriction.
Do not substitute a modern conservation-area boundary for this extent.

The working date remains approximately **1900–1902**. Earlier maps and later
photographs need feature-by-feature comparison. The 1930s flood-relief works,
Prescott Cut and subsequent rebuilding are excluded from the period scene.

## Sources recovered

Downloaded reports, extracted searchable text, selected page renders and a
checksum manifest are in `reference/planning-research-2026-09-25/`. They remain
outside the published website. PDF page numbers below count from the first
page of the file; printed page numbers can differ.

| Source | Useful evidence and limits |
| --- | --- |
| [MoLAS–PCA waterways survey, September 2008](https://archaeologydataservice.ac.uk/catalogue/adsdata/arch-702-1/dissemination/pdf/molas1-47769_1.pdf) | 533 pages, historical maps and engineering drawings. PDF pp. 54–56 distinguish nineteenth-century bank changes; pp. 61–63 explain the 1930s scheme. Figures 14–15, 17, 33–34 and 37 are particularly useful. Proposed works are not proof of completion. |
| [Three Mills conservation appraisal, May 2021](https://www.newham.gov.uk/downloads/file/8242/document-22) | Historic maps on pp. 11–12, chronology pp. 10–13, standing buildings from p. 22. Modern photographs need checks against rebuilding. |
| [Sugar House Lane heritage assessment, April 2008](https://www.newham.gov.uk/downloads/file/987/sugarhouselaneheritageassessment) | District development and surviving industrial buildings; complements the more detailed 2013 building record. |
| [Sugar House Lane conservation appraisal, January 2010](https://www.newham.gov.uk/downloads/file/989/sugarhouselaneconservationareaappraisalandmanagementplan) | Street and building context, map comparisons, conservation inventory. |
| [PDZ12 archaeological evaluation, 2008](https://archaeologydataservice.ac.uk/catalogue/adsdata/arch-702-1/dissemination/pdf/molas1-40627_1.pdf) | Sites OL-08507 / OL-08707: housing district south of High Street, east of Livingstone Road. Excavated remains and levels, not a complete terrace elevation survey. |
| [Abbey Mills Tideway heritage statement, Appendix Q](https://www.tideway.london/media/2114/53-heritage-statement-appendix-q-abbey-mills-pumping-station.pdf) | Pumping-station fabric, setting and views. Its gasworks summary should be checked against the detailed Historic England holder records. |
| [Sugar House Lane planning report, 2012](https://www.london.gov.uk/sites/default/files/public%3A/public%3A/PAWS/media_id_186021/sugar_house_lane_stratford_report.pdf) | Application LTGOUT/12/00336; a route to archaeological conditions and supporting documents, not measured historical geometry. |

## Decisions for the next model pass

| Feature | Evidence | Modelling consequence / remaining uncertainty |
| --- | --- | --- |
| Northern railway | User identification; waterways survey Fig. 37, PDF p. 425, reproduces an 1890 Great Eastern Railway blueprint. | Register the main-line alignment against period OS mapping. Existing Woolwich-branch geometry does not establish this boundary. The survey's coloured overlays are modern annotations. |
| City Mills banks and waterways | Waterways survey §§6.4–6.5, PDF pp. 54–55. | The report dates infilling of the Spilemans intake and Howards dock to 1892–1894/6. Compare the supplied provisional 1885–90 plans with later mapping before retaining these features in c1900. Open cricket/allotment land between sewer and railway should not be filled with invented factories. |
| Wall River / Waterworks banks | Waterways survey §§8.1–8.4, PDF pp. 61–63; Figs. 33–34, PDF pp. 421–422. | Major widening, rerouting and concrete walls belong to 1931–35. Earlier banks include masonry and earth; neither universal grass slopes nor universal concrete walls are supported. |
| Howards photographs | Company pamphlet c1897; [Foxlinks caption](https://www.foxlinks.com/howard-sons/) attributes the other view to about 1914, near the old flood-gate. | North-to-south orientation remains the author's hypothesis. The 1914 attribution is secondary, not an independently verified exposure date. The Foxlinks article also discusses the later Ilford works: keep the sites separate. |
| Sugar House and additions | [ASE report 2013200, September 2013](https://archaeologydataservice.ac.uk/catalogue/adsdata/arch-480-1/dissemination/pdf/archaeol6-159592_1.pdf), §§5.6, 5.8, 6.14, 6.15.8, Figs. 5–6 and 21, Plate 49. | Building 16 dates to 1882. Buildings 15, 17 and 17a fall between the 1894 and 1916 maps, described as c1900. The supplied modern west-face photograph appears to show traces of Building 15. The exact extension year remains unresolved; dated insurance sheets may narrow it. |
| Three Mills | 2021 appraisal pp. 10–13; [House Mill Trust](https://housemill.org.uk/about-us/); listed records [House Mill](https://historicengland.org.uk/listing/the-list/list-entry/1080970), [Clock Mill](https://historicengland.org.uk/listing/the-list/list-entry/1191269). | Surviving mills provide strong architectural references. Miller's House was reconstructed in 1992–93 with a modern rear: do not copy that rear into c1900. Distillery buildings require their own phase comparison. Current model dimensions remain estimates. |
| Period Three Mills photos | [Eastside Community Heritage, CANA/P/21](https://catalogue.eastsidecommunityheritage.org/catalogue_item/canals/photographs-connected-to-the-canals-project/a-selection-of-photographs-taken-around-the-three-mills-a-grade-1-listed-site): /11 catalogued c1900, /17 nineteenth century. | Catalogue read; photographs not successfully retrieved or visually assessed in this pass. Several neighbouring records show possible 1993 refurbishment. Collection lists noncommercial-use permission; preserve individual credits and terms. |
| Bromley-by-Bow gasworks | [Historic England No. 7 record](https://historicengland.org.uk/listing/the-list/list-entry/1080995), amended 2021. | Nine original holders, with Nos. 3 and 5 subsequently demolished. The factory pass now renders all nine circles, registered against the period OS. Third tiers on Nos. 1 and 3 date to 1925–27; the gasworks rail link dates to 1916. Both are too late for this scene. No. 7 is approximately 23 m high, 62 m diameter, with two tiers of 24 columns. Match holder numbers before applying dimensions. |

## Planning and archive follow-up

Newham's [LLDC transfer page](https://www.newham.gov.uk/planning-development-conservation/london-legacy-development-corporation-lldc)
is the starting point for former LLDC records. Planning powers transferred on
1 December 2024; historical documents may still be migrating.

The Bromley developer's [2024 update](https://bromley-by-bow.com/2024-update)
links to [Newham application S16Y3CJYFRH00](https://pa.newham.gov.uk/online-applications/applicationDetails.do?activeTab=documents&keyVal=S16Y3CJYFRH00),
application **23/02033/OUT**. A [decision-notice mirror](https://docs.planning.org.uk/20250819/208/SZY233JYN2A00/dht10h4t8qy4a9wf.pdf)
identifies a Montagu Evans Heritage Statement, version 5, September 2023.
That statement and the archaeological environmental-statement appendices remain
retrieval targets; the council document tab could not be reached this pass.
Historic England also cites Conisbee's June 2018 structural appraisal and
Montagu Evans' January 2021 enhanced-listing report. Neither has been read here.

Historic England's House Mill drawing catalogue has ground-floor plan
**MD96/05114**, first-floor plan **MD96/05116**, third-floor **MD96/05121**,
fourth-floor **MD96/05157**, waterwheel/sluice **MD96/05146**, and millstone
**MD96/05148** leads. These are catalogue leads, not measurements extracted
from inspected drawings.

The subsequent [factory implementation](FACTORY_BUILDINGS.md) registers and models
individual ranges across the full agreed district and corrects the Bromley holder
count. The river relief remains inferred; many roof forms and elevations remain
estimates. See the factory register for implemented coverage, evidence limits and checks.
