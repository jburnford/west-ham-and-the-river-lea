# Northern railway connection and western Old Lea industry

The author requested these two additions on 27 September 2026 as the final major landscape additions before preparing a narrated flyover. The active scene remains `docs/`; this pass does not modify or export the earlier social film.

## Railway

`data/maps/woolwich-northern-connection.json` records the Woolwich branch curve and corridor from the archived georeferenced NLS five-foot OS map. The added 1,039.4 m section, with four bridge gaps, joins the southeastern pair of the four Great Eastern main-line tracks, curves around the northern housing and continues south past Stratford Market to the existing branch. It represents the connection, not the complete Stratford station, depot, siding or signalling layout.

`scripts/woolwich_connection.py` generates two continuous tracks, sleepers, ballast, earth slopes, retaining ends and bridge gaps. A cosine grade matches the main line's 8.5 m formation to the existing branch's 5.5 m formation over 460 m. These heights remain model estimates. The old northern branch endpoint was 28.37 m east of the mapped corridor; it moves west and blends into the next existing branch point, clearing the Bridge Road housing instead of passing through it.

Bridge openings clear the full source road corridors, including short portions absent from the clipped road surface, and the extra northern Channelsea water context. Track coordinates and levels agree at both joins. The detailed railway renderer now accepts two-track formations as well as the existing four-track main line. The continuation is a separate infrastructure record, giving five rendered railway records overall.

## Western industry

`data/maps/west-bank-industry.json` contains 48 individual mapped range envelopes across ten sites:

| Site | Works |
| --- | --- |
| 259 | Bow Brewery |
| 420 | Ratner Safe Works |
| 421 | Albion oil and grease works and the adjoining disused soap works |
| 422 | Bow Flour Mills and Albion Wharf |
| 423 | Indiarubber and oilskin manufactory |
| 424 | Felt Works |
| 792 | Mineral water manufactory |
| 563 | London and Glasgow Foundry |
| 941 | Ornamental moulding works |
| 230 | Imperial/Crown chemical works beside the Three Mills approach |

Building envelopes were read separately from the local OS tile mosaics. The saved source-frame pixels and world footprints preserve the interpretation. Original industry GIS supplies the site identities and parcel context, with separately traced yard extensions for Albion Wharf, the disused soap works and moulding works. The builder removes these sites from the former west-of-Old-Lea exclusions, and their detailed buildings replace the earlier generic context blocks automatically.

Heights, roof bays, ten brick chimneys and yard stock are explicit visual interpretations. The added chimneys are **not** claimed as transcribed OS/Goad symbols. Their placement is within inferred steam/process ranges, and each has source and interpretation notes. Institutional grounds and residential plots north of Bow Bridge were not filled with invented factories. The foundry gate-office envelope moves approximately one metre inward to clear the registered Hancock Road carriageway.

The entire factory layer now contains **43 sites, 507 ranges and 89 chimneys**. The working-surface layer contains 81 yards, 32 clear wear routes and 148 stock groups, including existing timber seasoning stacks. Existing Mill Meads and other housing records remain unchanged; their derived plots were rebuilt against the new obstacles.

## Verification and review

`check_western_completion.py` checks both railway joins, matching track pairs and levels, maximum grade, bridge openings, housing/factory clearance and the added western building coverage. Existing factory, yard, housing, street, Great Eastern, navigation and sewer checks also pass. Six browser views cover the junction, branch corridor and western works; none reported browser or shader errors.

`review_western_completion_maps.py` saves factory and railway overlays in `reference/western-completion/`. `review_factory_buildings.py --completion-only --url http://localhost:4175` captures the six scene views.

Direct local destinations:

- `?view=woolwich-junction`
- `?view=western-industry`
- `?view=bow-works`
- `?view=three-mills-west`

Rebuild in order: `build_factory_buildings.py`, `build_infrastructure.py`, `build_housing_detail.py`, `build_infrastructure.py` again after any housing changes, `build_factory_yards.py`, then `build_scene_manifest.py`. The map review uses the already archived NLS tiles; no new map download is needed.
