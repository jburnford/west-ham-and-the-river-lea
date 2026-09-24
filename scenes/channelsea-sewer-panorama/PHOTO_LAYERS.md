# Photo-informed detail pass

23 September 2026. The photographs below were visually inspected to guide original geometry in `docs/photo-details.js`. They are not displayed in the site and are not used as textures. This pass adds observable forms; it does not establish a measured photogrammetric reconstruction.

| Reference | Visible evidence used | Implemented layer | Remaining uncertainty |
| --- | --- | --- | --- |
| Figure 4: Channelsea south of Abbey Mills, 1900 | Exposed central bed, narrow channels, barges close to the camera, timber banks, industrial skyline | Shallow irregular bed relief between the mapped channels; lighter hulls and retaining planks | Tidal elevation, bank profile, exact boat positions and sizes; relief is estimated and tapers at the channel edges |
| Figure 3: Abbey Mills / Ingham Clarke / Bromley Gas Works, 1902 | Rounded barge ends, deep cargo holds, deck timbers, dense cargo mounds; arched factory windows, round openings, curved parapets and roof vents | Open-hold barges with curved rims, deck seams, cleats, mooring ropes and small cargo pieces; facade and roof studies for the existing factory blocks | Individual vessel identity, cargo identification for each load, building identification and orientation. The same facade vocabulary is used across several provisional sites; this is not a claim that they shared one design |
| Channelsea River & Abbey Mills Pumping Station, period view / Figure 9 | Twin tall shafts with horizontal bands and expanded crowns; central station silhouette | Banded chimney shafts, flared crowns and more distinct roof/lantern silhouette | This is another viewpoint, not the panorama camera. Stack dimensions and the southeast location remain estimates |
| Abbey Mills main building, The wub, 2022 | Arched windows, contrasting masonry, cornices, steep roofs, dormers, corner turrets, octagonal glazed lantern and finials | Two tiers of framed windows, masonry bands, mansard-like roof profiles, projecting dormers, stepped lantern, turrets and finials | Modern colours and surviving details do not establish their circa-1900 state. Simplified dimensions, exact bay counts and facade orientation require map/photograph matching |
| Bromley gasholders, The wub, 2022; historical controls in the reference notes | Column capitals and shallow lattice girders, frame and bell distinction | More detailed columns, capitals, shallow connecting girders and segmented bell on the existing single-holder study | The distant study remains at the listed No. 4 location; it is not identified as the prominent holder in Figure 3. No later third tier or full-height diagonal additions are introduced |

Modern-photo credits and links: [Abbey Mills](../../reference/abbey-mills-modern/README.md) and [Bromley holders](../../reference/bromley-gasholders/README.md), both The wub / Wikimedia Commons, CC BY-SA 4.0. Historical photographs remain internal references with publication rights unresolved.

## How this relates to the ground plan

The crossing anchor, camera, river channels, industrial parcels, station anchor and single-holder anchor are unchanged. Existing factory study boxes remain within their respective GIS parcels; small facade mouldings project beyond the study boxes. These are still illustrative building placements inside **site polygons**, not traced individual building footprints.

The new bed surface is triangulated only within the inferred exposed-bed area outside the mapped channels. Its elevation is a procedural estimate below one metre above the scene's arbitrary water datum; it is not measured terrain. Haze is an interpretive means of separating foreground and distance, not a pollution simulation.

Next priority: use the historical plans to replace the repeated facade studies with identified, individually modelled waterfront buildings. Match the photograph's camera before treating its apparent sizes and spacing as surveyed geometry.


## Housing and gasworks extension

The subsequent neighbourhood pass supersedes the single-holder arrangement: six West Ham circles and 28 residential row envelopes are now traced from inspected OS VIII.32 and VIII.22 scans, with four Abbey Lane pairs and seven Bromley holders. Photograph comparisons and registration limitations are recorded in [the neighbourhood reference ledger](../../reference/neighbourhood-context/README.md). The latest browser report records 16 draw calls and 676,104 triangles in the opening view. This is a software-rendered check, not a phone benchmark.


## Current extension (supersedes the counts above)

Ninety-two housing-row envelopes are now modelled. The sewer has a continuous raised crest and earth banks, with mapped local bends and inferred distant continuations. OS VIII.42 supplies the railway north of Bromley gasworks; the north–south branch and junction curve are also traced. Seven southern factory-range envelopes replace nine former grid blocks. Forty-five interpreted garden beds lie on mapped open land west of the river. Abbey Mill is a provisional mass in its mapped site; no windmill is included because the book dates the illustration to c1800.

The author identifies the 1902 close-up with the northern West Ham gasworks view, and the wide 1900 photograph with the southern Bromley view. The filename’s Bromley attribution is not treated as authoritative. Architectural details inspired by the close-up remain comparative studies at other sites; exact facades have not been established. See the latest browser report for rendering counts and the assumptions ledger for registration and height limits.

## Visual refinement, 24 September 2026

Both original river photographs were inspected again. The southern view informs the irregular exposed mud, subdued water reflections and plain industrial ranges; the northern view informs the arched openings, curved parapets, loading frontage and roof ventilators. The previous universal curved-parapet treatment is superseded: only the site-253 northern studies retain it. Long mapped ranges now have varied roof sections, doors, gutters and downpipes. Section wall heights step down by up to 1.3 m from the existing estimate, with roof ridges about 2.6 m above the wall. These are modelling choices within existing envelopes, not evidence for particular factory elevations.

Surface textures and relief are procedural original work. Soft contact shading follows existing envelopes; the water reflects the 3D reconstruction. Neither represents additional historical evidence. No boats, houses, gas holders or industrial footprints were relocated in this pass. The remaining gap is individual building identification and photograph/camera fitting, rather than texture resolution alone.

## Latest terrain and mill pass, 24 September 2026

The [terrain record](TERRAIN.md) supersedes the earlier bed, garden and rendering-count descriptions. Detailed mud, channel depths and wet edges now continue north and south. The west bank rises above the low allotment ground; 19 varied sheds and irregular cultivated rows replace the rectangular bed studies. Dense irregular coal mounds replace the coarse cargo surfaces. The mill’s boarded upper floors, masonry base and interlocking gables follow the author’s proposed continuity from the c1800 illustration, without the windmill; the c1900 elevation is unconfirmed. Southwest terrace/industrial groups extend the distant context, with approximate registration and interpreted elevations. The eight new supplied maps, including the 1905 comparison, have a separate [reference ledger](../../reference/author-map-extracts-2026-09-24/README.md).

## Supplied 1868 engraving: station revision, 24 September 2026

The author supplied a viewable, watermarked image after the [Mary Evans page](https://www.maryevans.com/contributors/coi/abbey-mills-pumping-station-london-1868-45687726.html) could not be retrieved. The earlier pending-access note is superseded. The original file is archived unchanged at `reference/abbey-mills-1868/`, with its SHA-256 and source record. The catalogue URL supplies the 1868 label; the original print publication and full catalogue attribution have not been verified.

Visible features used: broad moulded chimney bases, arched base recesses, slender decorated shafts, pointed/openwork chimney crowns, two tiers of façade arches, five-bay wing ends, dormers, small roof pavilions, ridge cresting and the central octagonal lantern. All additions are original geometry; the source image and its watermark remain reference-only and are not used as a public texture.

The original blunt chimney tops are replaced with corbelled collars, tapered cores, curved outer ribs and pinnacles. The model tops reach about 54.65 m, close to the previous approximate 54 m. The main station lantern is reduced from about 40 m to 36.7 m: the engraving shows a lower station roofline relative to the chimneys. These heights and the detailed crown geometry are **interpretations**, not measurements derived reliably from one perspective engraving. Station/stack anchors and wing envelopes remain as before. Five-bay end elevations, projecting entrance surrounds, alternating arch masonry, upper-window divisions, additional dormers and ridge ironwork give the façades and roof more depth.

The image depicts an earlier state than the c1900 target. Survival of individual details into the target date remains an explicit continuity assumption; monochrome shading does not establish brick/roof colours. The low ancillary ranges and exact camera match are not newly reconstructed from this single view.

Review: `scripts/review_station_1868.py`, with exports `review/station-1868-wide.png`, `review/station-1868-detail.png` and diagnostics `review/station-1868-checks.json`. The previous station view remains in `review/before-1868-station/`.
