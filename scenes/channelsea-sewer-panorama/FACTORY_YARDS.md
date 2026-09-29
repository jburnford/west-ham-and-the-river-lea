# Factory working surfaces

29 September cooperage continuation: a separately recorded OS/Goad envelope
restores the Chippindale cooperage yard omitted from the original industrial
parcels. Yard 96401 belongs to factory site 964 and supplies about 3,946 m² of
working surface after building, road, river and chimney exclusions. Two small
timber groups and the surface finish remain interpretations. The register is
`data/maps/sugar-house-footprint-alignment.json`; the district now has 83 yard
surfaces, 33 clear wear routes and 161 stock groups.

The first yard refinement replaces the repeated four-metre mud texture and
grid-based colour noise on industrial parcels. A single district surface map
now gives each yard uneven, non-repeating colour, dirt at building edges,
patches of damp ground and restrained wear across clear access space. Cinder,
earth and stone-dust palettes distinguish groups of works. The texture is applied
directly to the existing land meshes, receives their shadows and follows their
levels. No overlapping yard planes or additional surface triangles are needed.

Exposed yard-to-grass margins now fade inward with an irregular, varying width,
rounding off the squared parcel corners. The old rectangular tint beneath the
yard atlas is removed so it cannot show through the transition. Building and
holder edges, water, roads, stock groups and access wear are protected from this
softening. The eroded surface margin is interpretive; source parcel geometry
remains unchanged.

The geometry comes from the existing industrial GIS parcels, western wharf
context and registered factory/frontage footprints. Yard surfaces are cut away
from buildings, holder rings, mapped roads and water. Some source parcels and
registered ranges do not align completely: this pass does not invent a new
site boundary to hide those registration discrepancies. In particular, the
Sugar House surroundings still need the parcel/building alignment review.

Small timber stacks, barrels, crates, pipes and coal/stone piles stand near
factory ranges in clear yard space. Placement is deterministic, sparse and
checked against buildings, roads, water, holders, mapped chimney bases and the wear routes. These are
**typological interpretations**, as are the surface materials, damp patches and
wear. They are not traced historical stockpiles, surveyed gateways or evidence
that every mapped industrial parcel was entirely hard-surfaced. Precise gates,
boundary walls, loading arrangements and paving need site-specific evidence.

New Imperial Saw Mills (site 797) now has 72 larger timber stacks across its
restored full yard. Deals and thinner boards have varied
lengths, heights and widths, bearers beneath them, and crosswise spacers between
layers. Rows align with the mapped mill ranges and leave working aisles and
vacant positions. Their exact dimensions, contents and arrangement are modelling
choices, not a transcription of stock shown on a historical plan. The author's
27 September map prompted restoration of the original GIS feature 797, which
had been clipped at scene x=-1050. Its full boundary agrees with the labelled
timber yard on the archived NLS map; it takes precedence over the anonymous
western context polygon without extending into the Oil Wharf south of the road.

The [Goad refinement](GOAD_REFINEMENT.md) updates the sawmill building cuts and
recalculates stock positions; individual stacks remain interpretive.

Six internal line traces follow the parallel yard tracks and curved branches
on the OS map. Ten visible pieces remain after clearing registered buildings,
roads and water. Their paired rails, gauge and sleepers are inferred; the map
has not established motive power or a connection to the Great Eastern Railway.
Stacks leave at least three metres to the track centrelines. The old
`oilwharf-6` rectangular building envelope was a misreading of the western
linear feature: it is removed from rendered buildings, with the former record
preserved under `reclassifiedFeatures` in the authored factory register.

The road separating the sawmill and Oil Wharf is corrected to **Cook’s Road**,
as labelled on the map and corroborated by sections 3.1.6–7 of the
[Wessex Archaeology / Crossrail XPM09 building survey](https://learninglegacy.crossrail.co.uk/wp-content/uploads/2020/01/C262-PML-XPM09-Pudding-Mill-Lane-Non-listed-Built-Heritage-Recording-Report.pdf).
The same survey identifies the oil wharf as Rowatts Wharf in the 1894–5 directory,
but notes its absence from later directory entries; this pass does not assign
that company confidently to the c1900 scene.

28 September Oil Wharf continuation: a separate reviewed working envelope now
occupies the oil yard south of Cook’s Road, with six interpreted barrel groups.
Four mapped petroleum tanks and the northern disused tank exclude yard surfaces,
stock and flat-plan masks. Building blocks previously covering open ground are
removed. See [FOOTPRINT_ALIGNMENT.md](FOOTPRINT_ALIGNMENT.md); the source and
boundary interpretation are in `data/maps/oil-wharf-footprint-alignment.json`.

The timber-yard trace and source ledger is `data/maps/sawmill-yard.json`.
`python3 scripts/review_sawmill_map.py` produces the source-map overlay: restored
parcel in green, track lines in red and interpreted stock in blue. Next reviews
for this sheet are lime/cement wharf apparatus,
roadside houses and the East London Soap Works boundaries. Track-end/gate detail
needs closer source comparison before adding carts or loading equipment.
Use <http://localhost:4175/?view=sawmill-yard> for the new timber-yard view.

Implementation: `scripts/build_factory_yards.py`, `docs/data/factory-yards.json`
and `docs/factory-yards.js`. Rebuild the data after changing site, building or
street geometry, then run `scripts/build_scene_manifest.py` so browser asset
versions remain coherent.

Validation: `python3 scripts/check_factory_yards.py` checks polygon validity,
surface overlap and circulation/stock clearances. The fixed cameras in
`scripts/review_factory_buildings.py` cover City Mills, Sugar House Lane,
Three Mills, both gasworks and the original bridge view. Before/after captures
are kept in the local `review/` folder. Preview Sugar House Lane at
<http://localhost:4175/?view=sugar>.
