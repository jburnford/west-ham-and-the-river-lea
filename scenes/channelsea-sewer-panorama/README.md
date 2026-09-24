# Above the Channelsea: West Ham's boulevard

First-scene brief, 23 September 2026. The author has selected a panorama from the Northern Outfall Sewer crossing over the Channelsea. This replaces the earlier open choice of a riverside neighbourhood as the first scene.

**Visitor experience**

Stand at pedestrian eye level on the elevated sewer crossing and look around the industrial landscape, provisionally circa 1900–1902. Begin looking south along the river, using the supplied photographs as visual anchors. The visitor can turn, look down at the channel and banks, and open a few short stories attached to visible places. Visitors can now move within a bounded rectangle on the bridge, crossing between parapets and shifting along the walkway at fixed eye height. This supersedes the original stationary-camera brief.

The period is a working range based on the supplied 1900 and 1902 photographs. The final reconstruction will need a declared date or range and a record of any features whose evidence comes from different years. A first camera now uses the crossing's listed grid reference with a provisional offset toward the south parapet. Its height, bearing and field of view are review settings, not a solved photograph match. See [the implemented assumptions](ASSUMPTIONS.md).

**Why this viewpoint matters**

The book provides an unusually direct connection between a visual experience and its historical argument. Chapter 3, “Living in West Ham,” discusses J.J. Terrett's 1902 pamphlet and his sarcastic description of the Northern Outfall Sewer walkway as West Ham's “boulevard.” He juxtaposed the public promenade with the gasworks, sewage pumping station, chemical works and soap factory around it.

This provides the opening story: a place to walk also exposed residents to the infrastructure and industry that sustained London. Visitors can discover the relationships between work, river transport, sanitation, pollution and public space by looking around one place. Attribute Terrett's language and political perspective; do not present his rhetoric as an unmediated description by all local residents.

The author has clarified that Figures 3 and 4 show different directions and different gasworks: the 1902 close-up is associated with the northward West Ham works, the wide 1900 view with the southward Bromley works. Earlier notes treating both as southward views are superseded. The photographs' lens, crop and exact camera placements still need comparison with a map. Figure 9 is a further view of the landscape and sewer; it should not automatically be treated as another exposure from the panorama's final camera position.

**Reference set**

| Reference | Role in reconstruction | What remains uncertain |
| --- | --- | --- |
| Book Figure 4 / `reference/Images and Figures/Figure2_4 Channelsea River, south of Abbey Mills 1900.jpg` | Principal southward composition: exposed banks, narrow water channels, barges, riverside structures and industrial skyline. | Exact bearing, position, focal length and water elevation. |
| Book Figure 3 / `reference/Images and Figures/Figure2_3 Abbey Mills Ingham Clarke & Co Bromley Gas Works 1902.jpg` | Barges, industrial facades, chimneys, retaining structures and gas-holder detail visible from the crossing. | Relationship of its framing to Figure 4; whether adjacent structures changed between photographs. |
| Book Figure 9 / `reference/Images and Figures/NewNewhamImages/Channelsea River & Abbey Mills Pumping Station.jpg` | Wider relationship between the river, Northern Outfall Sewer and pumping station. | Photo date, camera placement and correspondence with the other views. |
| `reference/Images and Figures/Figure4_2.png` | Alternate image version of the Figure 9 view. | Not independent evidence of another direction. |
| 1890s OS town plans and existing river/industry GIS | Ground plan, bridge position, channel shape, factory plots and names. | The exact sheet(s), alignment and any changes before the working scene date. |
| Fire-insurance plans, when available for the location | Building materials, storeys and industrial detail where recorded. | Coverage, revision dates, legend interpretation and source access. |
| [Modern Abbey Mills reference photograph and source notes](../../reference/abbey-mills-modern/README.md) | Surviving roof forms, lantern, windows, brick and stone detail; one verified CC BY-SA 4.0 exterior downloaded. | Historical paint, later alterations, and missing chimney stacks; the modern photo's viewpoint is not the panorama camera. |
| [Bromley-by-Bow gasholder photograph and source notes](../../reference/bromley-gasholders/README.md) | Modern guide-frame details, individual-holder chronology and a verified CC BY-SA 4.0 reference photograph. | Match holder identities and period gas-bell silhouettes; exclude later height alterations and establish visibility from the panorama camera. |

The 1900 photograph depicts exposed riverbed and relatively little water. Start with that observed condition when matching its composition; a still photograph does not establish a complete tidal or flood simulation. Do not label exposed sediment as a measured depth of sewage or assign pollution concentrations without evidence.

For Abbey Mills itself, combine modern architectural photographs with the period site plan and historical views. The two former chimney stacks must be represented according to period evidence, rather than copying today's silhouette. Historic England records the surviving bases northwest and southeast of the station; their upper geometry and height remain modelling inputs to establish. Modern fences, vehicles, site equipment and later buildings are not features of the historical panorama.

**Reconstruction sequence**

1. Locate the historical sewer crossing on the relevant OS sheet. Place the photographs' estimated sightlines and match several identifiable landmarks to determine an initial camera position and height. Preserve the uncertainty of the fit.
2. Build simple geometry for the crossing, ground, riverbanks and main building volumes. Match the southward photographic view before adding detail.
3. Extend the model around the camera using mapped footprints and additional sources. Prioritise visible silhouettes and important landmarks. Assign heights, roofs and facades separately as documented or estimated. Do not turn the existing photographs into an assumed complete 360-degree record.
4. Review the blockout from both bridge sides and along the permitted walkway. Check skyline, relative scale, occlusion, river width and which named sites are actually visible. Retain the option to preview only a supported viewing sector while the surrounding reconstruction develops.
5. Add supported architectural detail, restrained materials and atmosphere. Mark atmospheric conditions and colour as interpreted where only monochrome evidence exists. Keep dramatic smoke or moving workers out unless there is a deliberate, documented interpretive reason to include them.
6. Render a full panoramic image after all viewing directions have been reviewed. Use a seamless 2:1 equirectangular image for the complete 360-degree version, plus a lightweight opening still and accessible labelled views. Test seams, poles and scale in the viewer. A partial panorama must have explicit rotation limits and must not be stretched across a full sphere.

A 3D model is the authoring source. The first public viewer can use a rendered panorama with hotspots, reducing the need to load and render an entire industrial district on visitors' phones. Retain the source model so future versions can add new dates or viewpoints. A local Three.js viewer and procedural study model are now implemented in `docs/`, with six story directions and an SVG location map. A finished photographic/equirectangular panorama has not been rendered.

**Initial story points**

- **The river as a working route:** barges and waterside premises connect local industry to transport and supplies.
- **The sewer beneath your feet:** explain the structure carrying the visitor and its place in London's sanitation infrastructure.
- **The industries around the walk:** identify visible works against the map and connect them to employment and environmental costs.
- **West Ham's “boulevard”:** introduce Terrett's criticism and the wider debate over public amenities and municipal spending.

Locate hotspots after identifying features in the model. Terrett's relative descriptions of right, left, ahead and behind are literary evidence, not surveyed bearings. Do not infer compass directions from them. More distant stories, including Millennium Mills and the Stratford engine shed, belong behind navigation links unless their actual visibility from this position is established.

Each hotspot opens a short paragraph with optional deeper evidence. Provide an equivalent list beneath the panorama. Drag/touch and keyboard controls, a reset view and an optional orientation map support exploration. No autoplay rotation, mandatory audio or movement-based controls are needed.

**First reviewable result**

A first review model is available at `http://localhost:4173/` when the server in the [project README](../../README.md) is running. The location map shows the selected camera and its live field of view; this is not a fitted photographic sightline. The south-facing scene now includes barges, interpreted exposed bed, timber banks and factory studies after comparison with Figure 4. It remains to be aligned rigorously to the photographs. Review screenshots and browser-check results are in [review/](review/).

The original stripped-down blockout was too empty and its bridge deck dominated the view. The revised camera sits near the parapet, with a more useful foreground and denser factory frontage. These changes improve composition without resolving the underlying architectural uncertainties. The reference images remain internal scene-development material unless their publication use is separately established.

A further [photo-informed detail pass](PHOTO_LAYERS.md) now adds rounded, open-hold barges, ropes and planking; curved industrial parapets and arched windows; Abbey Mills' roofs, dormers, lantern and banded stacks; and column/girder details on the gas-holder study. The exposed-bed surface has shallow inferred relief outside the mapped channels. Browser and geographic checks pass; precise architectural identification and photograph matching remain outstanding.

The crossing sheet, London VIII.32, and its northern neighbour VIII.22 have now been inspected. Their housing row envelopes and six West Ham holder circles are modelled, alongside seven Bromley holders. See the [source and tracing ledger](../../reference/neighbourhood-context/README.md). The next substantive task is to refine map registration, identify individual factory buildings against the photographs, and fit the camera using several landmarks. Historic England dates the bridge's rebuilding and widening to 1900–1902; use that chronology when choosing the final scene date.

The current author priority is texture and topology, with phone and website development deferred. The latest [terrain and material study](TERRAIN.md) adds north/south channel relief, detailed sediment, coal, the raised Mill Mead bank and allotment sheds; revises the mill without a windmill; and extends the southwest distance using the supplied maps. The additional map labelled 1905 is catalogued as a later comparison. Current screenshots are `review/terrain-*.png`.
