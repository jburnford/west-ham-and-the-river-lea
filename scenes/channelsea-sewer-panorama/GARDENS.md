# Garden surfaces and the former terrain seam

The author's September 26 screenshot showed two defects together: a straight
brown/green boundary across Mill Meads and cultivation rows partly disappearing
into the surrounding ground. The detailed Channelsea tile painted its garden
extent brown, while the extended marsh used a separate grass material. Garden
detail was placed as flat boxes above single sampled plot heights.

Both terrain meshes and the surrounding flat ground now share one land shader,
with consistent world-coordinate shading and separate sediment/land-cover
attributes. The old tile-wide brown garden paint is gone. Soil appears on
cultivated patches, with grassy/earthy access gaps between them. The terrain
meshes receive building shadows but no longer cast self-shadows across the
nearly flat marsh. The original water-plane seam was addressed separately in
the tide pass.

`docs/gardens.js` tessellates soil patches onto the actual ground on both sides
of the join. Crop clumps also sample that ground. The interpreted layout has
153 plots of varying size, aligned with the mapped field edge, with shared
access gaps, fallow areas, planting interruptions and a small number of sheds.
This replaces 290 identical 7 × 14 m beds and repeated tall stripe geometry.

The mapped outer extent and all ditch/river/access exclusions remain. Individual
divisions, crop forms, fallow state and sheds are **interpretations**, not a
survey of 153 historical tenancies. The broader allotment extent itself draws
on later mapping and remains provisional for c1900; its source note is retained
in `ground-plan.json`.

Rebuild in order: `build_panorama_data.py`, `build_river_terrain.py`, then
`build_river_network.py`. The network now includes `river-network.cover`, with
yard and garden-cover attributes matching the detailed terrain's land-cover
data. `check_gardens.py` checks non-overlap, ditch clearance, and 199 height/cover
samples along the join. After `review_tides.py`, run
`check_gardens.py --rendered` to compare actual rendered soil vertices with the
underlying terrain triangles. Browser views include the join from above and
the plots at low level, as well as the regular-tide and barge regressions.
