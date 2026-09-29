# Continue building-by-building footprint matching

Checkpoint: 29 September 2026, recovered after WSL restart. The author wants an approximate but convincing
circa-1900 reconstruction. Continue adjusting existing 3D models to the supplied
building footprints, site by site. Exact architectural accuracy is not required,
but record the distinction between map evidence and interpreted elevations.

Commit checkpoint: `d6c9335` contains the six completed continuations through
southern Three Mills, including shared authoring records and tank-safe yard
exclusions. The later House/Clock Mill and wharf continuation is local and
uncommitted. Separate height work and `docs2/` remain excluded.

## Start here

1. Read local `MEMORY.md`, this file, `FOOTPRINT_ALIGNMENT.md` and
   `ABBEY_STATION_ALIGNMENT.md`.
2. Check `git status` before editing: another workflow is collecting heights.
3. The live site is **docs/**, normally served on **localhost:4175**. Check the
   existing server before starting another. `docs2/` is an alternative version;
   leave it alone. Do not push/deploy unless requested.
4. Inspect current data and source polygons before assuming a model matches one
   source feature. A single polygon can combine several factory compartments.

## Completed model alignment

- 344 source-linked factory ranges at twenty-four sites, including 24 Slater & Palmer /
  Marshgate Mills ink-works ranges. First-pass registry:
  `data/maps/factory-footprint-alignment.json`. It retains original outlines,
  source IDs, changes in position/area and previous roof/height interpretations.
- Ink-works continuation: `data/maps/ink-works-footprint-alignment.json` adds 13
  ranges in ten explicit groups, including shared outlines for 25/26, 28/29 and
  9/10, plus three corrected chimney bases. Source 2452's chimney hole is retained.
  A 0.77 m² source overlap at the eastern store is recorded and cleared in the
  renderer. Firelighter and warehouse 24 have no source outline in the extract;
  their Goad models remain pending separate OS tracing.
- Imperial Saw Mills continuation: `data/maps/sawmill-footprint-alignment.json`
  adds 14 ranges in eight groups, completing all 16 existing site-797 ranges.
  Seven mill compartments share a corrected outline; the northern Towers
  slaughterhouse retains its separate courtyard arrangement. The internal boiler
  chimney moves with its parent, without claiming a mapped base. Cook’s Road is
  retraced locally in `district-road-traces.json`, preserving the bridge approach.
  Additional plant outline 455070 has no existing model and remains deferred.
- Oil Wharf continuation: `data/maps/oil-wharf-footprint-alignment.json` corrects
  five ranges and adds four, retaining the earlier filling-shed match. Two
  spurious rectangles are removed with their prior records retained. The ten
  resulting ranges include the adjacent dwelling row, identified separately.
  Four petroleum tanks and one northern disused tank follow OS/Goad evidence;
  two tank circles absent from the extract are traced and locally registered.
  A named working-yard envelope supplies barrel stock and tank exclusions.
  Northern Cook’s Road now clears the stores; sawmill frontage and bridge remain.
- Howards continuation: `data/maps/howards-footprint-alignment.json` aligns 83
  ranges in 53 reviewed groups containing 101 supplied source polygons. The old
  mill (644) is directly traced from OS; shed 524 moves with its Goad neighbour;
  shed 620 remains explicitly deferred. All 86 site-260 ranges are accounted for.
  Eighteen chimney positions are corrected: two mapped bases and sixteen local
  department transfers. `data/maps/city-mills-bank-alignment.json` reconciles
  twelve bank vertices with the waterfront buildings while retaining the millrace.
  The saved source geometry, earlier compartments and roof/height evidence remain.
- Sugar House / cooperage and Winstone continuation:
  `data/maps/sugar-house-footprint-alignment.json` adds 18 source-linked ranges
  in 14 groups (19 source polygons), including three previously omitted low
  cooperage compartments. Together with earlier range 14, 19 of site 964's 31
  ranges are aligned. The five-storey Sugar House keeps its paired roof. One
  chimney moves into its mapped sawmill opening, with a narrower interpreted
  base; height retained. Sugar House Lane and its works passage are re-read
  locally. A separate mapped cooperage-yard envelope restores its working surface
  and two small timber groups. Its twelve deferred ranges are resolved below.
- West of the cooperage: `data/maps/west-sugar-footprint-alignment.json`
  aligns all 27 existing site-947 ranges and eleven added rooms in 34 groups.
  Hodson, Dane, Winstone and Wildash remain separate mapped compounds; previous
  roof/height interpretations are retained. Three chimney bases are source-linked;
  the fourth transfers within its Goad room. Two duplicated Wildash edge records
  from F17 are removed from site 569, leaving its two actual Kendrick ranges.
  `west-sugar-bank-alignment.json` reconciles ten local river controls while
  preserving a continuous channel. Sugar House Lane gains bend controls and a
  5.2 m estimated carriageway to fit the 7.85 m gap with pavements; southern
  connections remain. A small High Street shift clears the machinery store. Yard 94701 restores
  the omitted western working ground.
- Crystal Wharf / Barber: `data/maps/crystal-barber-footprint-alignment.json`
  resolves the remaining twelve old site-964 ranges. Eight are corrected and
  four open-yard rectangles are removed; thirteen omitted rooms are added,
  making 21 newly source-linked ranges and all 40 eastern ranges aligned. Two
  chimneys are corrected: mapped base 1230955 and a Goad boiler-room transfer
  retaining its printed 50 ft height. Yards 96402/96403 restore working ground
  without stock. Small isolated plant features remain explicitly deferred.
- High Street starch, tin-box and confectionery compounds:
  `data/maps/abbey-west-footprint-alignment.json` adds 18 source-linked ranges in
  fifteen groups. All current site-256/572/573 ranges (5/3/8) are aligned. Four
  omitted Hogarth rooms are added, one misclassified industrial rectangle over
  a domestic frontage is removed, and chimney base 993523 is matched. Two Bow
  Bridge boundary rooms are also aligned. Its two provisional process-room
  transfers are superseded by the Bow Bridge continuation below.
- Bow Bridge bone and chemical works:
  `data/maps/bow-works-footprint-alignment.json` adds ten source-linked ranges
  in seven groups and five directly traced OS rooms. Two omitted rooms are added;
  site 254 now has seventeen ranges, twelve source-linked and five direct traces.
  Internal Goad divisions and elevations remain interpreted. Five chimneys are
  reviewed: four mapped bases, including a new printed 50-foot retort chimney,
  and one Goad-room transfer. `bow-works-bank-alignment.json` reconciles ten
  works-side River Lea controls while preserving the opposite bank and channel.
  Hunt's neighbouring range 564-1 received a provisional 2 m southward move;
  the full source review below supersedes it.
- Hunt's soap works: `data/maps/hunt-works-footprint-alignment.json` aligns all
  ten current ranges in six groups. Three omitted rooms are added: western
  furnaces, office/laboratory and southern engine room. Five existing process
  rooms share the main supplied OS exterior, retaining interpreted Goad cuts.
  The stables and two-storey dwelling retain their distinct forms. The 80-foot
  boiler chimney follows source base 1013155; the western 22 m chimney transfers
  approximately within its Goad room. `hunt-works-bank-alignment.json` adjusts
  two local controls, including a further correction to shared Bow Bridge vertex
  39, clearing the furnace rooms while retaining the opposite bank.
- Lascelles / British Ultramarine:
  `data/maps/lascelles-ultramarine-footprint-alignment.json` links all six existing
  ranges in five groups. Two narrow gaps at an OS sheet join are explicitly
  reconciled, keeping the continuous Goad exterior and southern chimney opening.
  The 60-foot shaft follows base 986471. The final Sugar House Lane control moves
  3.5 m west to clear the process house; upstream controls and width remain.
  Earlier heights and roofs are retained. Northern Williams wharf boundary rooms
  are resolved in the following pass.
- Williams wharf / French Asphalte:
  `data/maps/williams-asphalte-footprint-alignment.json` adds seventeen source-linked
  ranges in fourteen groups, two direct OS traces and the omitted Goad 704 room.
  An explicit 127.897 m² OS completion supplies the missing eastern sheet edge
  of the western Asphalte body. Internal room cuts remain interpreted; raw source
  polygons are retained separately. The boundary lean-to moves to Ultramarine
  site 566 while keeping its stable model ID. Both Asphalte stacks are corrected,
  one to mapped base 1087863 (printed 60 feet), the other within its Goad room.
  Two southern lane controls move 1.5 m west, clearing three mapped façades.
  Site 568 has eighteen ranges; site 566 has four. Existing elevations remain.
- Refinery / printing / machinery depot:
  `data/maps/refinery-printing-footprint-alignment.json` accounts for all thirteen
  former site-567 ranges and adds rooms 652, 684, 685, 686 and 682. Seventeen
  ranges match supplied outlines; storage shed 688 is a direct OS trace because
  it is absent from the extract. Chimneys follow bases 1201365 and 1146475,
  retaining inferred 22 m heights with narrower interpreted shafts. The lane
  gains two bend controls, and the passage reconnects and clears the shed.
  Four mapped façades use a documented 0.55 m minimum pavement clearance where
  the opposing buildings leave 6.712 m; carriageway width stays 5.2 m. Actual
  pavement meshes clip against those retained walls. Prior elevations remain.
- Abbey Mills main station: corrected orientation (~35.88°), main cross and two
  lower rear boiler wings. Source outline 459 includes the whole attached
  complex; do not enlarge the ornate station to fill it. Chimney bases use
  source IDs 257848 and 277380. Authoring/runtime plan:
  `data/maps/abbey-station-plan.json`, `docs/data/abbey-station-plan.json`.
- Source fit is a geometric comparison, not a historical-accuracy score.
- Abbey supporting group: eight buildings plus four lower annexes, including
  source 6687, both chimney-side buildings, the lodge and southwest cluster.
  `data/maps/abbey-supporting-buildings.json` retains source polygons and five
  period-map access traces. These volumes use the station plan and shared factory
  renderer, separately from the industrial ranges. Heights and roofs remain
  interpreted. Tiny features 1064653 and 1162448 are explicitly deferred.
- The broader scene has 43 factory sites, 547 ranges, 90 factory chimneys,
  196 terrace rows / 3,204 houses and 85 modeled yards (37 wear routes, 160 stock groups).
  Eleven factory ranges use direct OS traces; two retain local Goad transfers.
- Kendrick / Usher: `data/maps/kendrick-usher-footprint-alignment.json` adds
  eight linked ranges, two OS seam completions and one direct main-factory trace.
  Varnish room 612 and two-floor room 620 are restored. The 40 ft chimney follows
  base 1154445; a matching hole keeps its plinth clear. Two local lane controls
  preserve northern walls. All seven prior elevations and roofs are retained.
- Northern Three Mills: `data/maps/three-mills-north-footprint-alignment.json`
  adds twenty source-linked ranges in fifteen groups, direct OS range 824 and a
  provisional local Goad 800 transfer. Timber room 828 is restored. The 31 m
  inferred chimney height and two 6 m tank heights are retained at mapped bases.
  The public lane/bridge remain; a narrower works passage clears the north rooms.
  Southern and mill/wharf rendered geometry is unchanged.
- Southern Three Mills: `data/maps/three-mills-south-footprint-alignment.json`
  aligns eight existing ranges (21–28) in five groups and three mapped tanks.
  The warehouse notch stays open; existing heights and roofs are preserved.
  Shared authoring records and a preflight clearance check reduce repeated work.
  Small gangways, rounded plant features and gas apparatus remain deferred.
- House/Clock Mills and bonded wharf: `three-mills-landmark-footprint-alignment.json`
  matches eight existing ranges in six groups. Millrace overlaps are retained;
  weatherboarding, kiln caps and clock tower follow the corrected footprints.
  The mill-court bend retains its 7 m carriageway; its eastern F.P. is re-read as
  a 2.2 m interpreted footpath. Main bridge and western approach are unchanged.
- Housing rows have not yet been aligned to the supplied regional footprints.

Useful local destinations:

- `http://localhost:4175/?view=pumping-station`
- `http://localhost:4175/?view=factory-940`
- `http://localhost:4175/?view=sawmill-yard`
- `http://localhost:4175/?view=factory-9001`
- `http://localhost:4175/?view=city`
- `http://localhost:4175/?view=factory-964`
- `http://localhost:4175/?view=factory-254`
- `http://localhost:4175/?view=factory-564`
- `http://localhost:4175/?view=factory-566`
- `http://localhost:4175/?view=factory-568`
- `http://localhost:4175/?view=factory-567`
- `http://localhost:4175/?view=factory-570`
- `http://localhost:4175/?view=west-ham-region`

## Source data

Original author-supplied file (read only):
`/mnt/c/Users/jic823/Dropbox/2026/london_buildings_1891-96_corr_v1.gpkg`.
Its building layer has 1,299,040 features in EPSG:3857. The study-area selection
has 238,052 features. Research extracts are outside Git:

- `reference/historic-building-footprints-2026-09-28/current-scene-buildings-bng.geojson`
- `reference/historic-building-footprints-2026-09-28/west-ham-buffer-buildings-bng.geojson.gz`
- `reference/footprint-model-alignment/deferred-candidates.json`
- `reference/footprint-model-alignment/corrected-ranges.png`
- `reference/abbey-mills-alignment/source-shapes.json`

BNG origin: E538900,N183209. Scene x = E − 538900; z = 183209 − N.
Research vectors retain original `sourceFid`. Runtime footprint plans are
115 transparent tiles plus an overview (~4 MB), not thousands of new meshes.
They cover historic West Ham plus a 3 km buffer. Regional ground is provisional.

## Next working sequence

Next review the nearby western-bank compounds: Ratner Safe Works (420), Albion
(421), Bow Flour Mills (422), Indiarubber/Oilskin (423) and Felt Works (424),
in manageable groups. Three Mills now has 36 source-linked ranges and one direct
trace; only Goad 800 remains provisional. Gangways and minor plant projections
are explicit separate omissions. Preserve the landmark anchors and mapped
millrace relationships established in the mill/wharf continuation.
Kendrick north, Usher and Kendrick south (569/570/571) are accounted for with
2/5/2 ranges. Source 20821 belongs to northern Kendrick; it is separate from
947-25/source 16620. Both Kendrick sheet-seam gaps have explicit OS completions;
Usher's main L-shaped room is a direct trace. Goad's uncertain northern 1–2 floor
boundary and the southern July 1893 construction status remain documented.
Site 567 now has eighteen accounted-for ranges. Williams / French Asphalte's eighteen ranges are accounted
for, including the added 704 room and the lean-to reassigned to Ultramarine.
Broader working-ground envelopes for Williams, Asphalte, Lascelles and Ultramarine
remain a separate parcel-review task. Lascelles and Ultramarine's seven current
ranges are source-linked, with explicit sheet-join reconciliation.
Hunt's ten ranges are source-linked;
its small platforms, service projections and western empties strip remain
explicitly deferred plant/yard details. Bow Bridge site 254's
seventeen ranges are accounted for. Its Goad 530 open-under structure, water
tower, tanks and small projections remain explicitly deferred plant features.
Current ranges at sites 256/572/573, western 947 and eastern 964 are source-linked. Small western Goad 876 and 882/884 annexes and eastern
isolated plant features 1217966, 1065632 and 1242744 remain explicit omissions.
Crystal Wharf's former ranges 24–27 were removed after OS/Goad review identified
open yard; their prior records remain in the continuation register.
The Howards, Oil Wharf, Imperial Saw Mills and ink-works compound passes
are complete apart from explicit omissions; the firelighter
and warehouse 24 remain explicit source omissions needing direct map tracing.
Howards shed 620 also needs a direct map trace. Shed 524 retains a transferred
Goad outline without claiming an individual supplied-footprint match.
Abbey's supporting buildings and access pass is complete;
see `ABBEY_STATION_ALIGNMENT.md` for the two deferred small features and its
separate rebuild sequence.

For each site:

1. Overlay current models, source polygons and period map. Inspect the image.
2. Decide whether each source feature represents one model or several attached
   compartments; preserve useful Goad divisions, uses, floor evidence and roofs.
3. Add explicit source-linked authoring corrections. Avoid blind nearest-polygon
   snapping and do not rerun a broad automatic selection without reviewing it.
4. Move attached features with their parent where appropriate. Check roofs,
   chimneys, streets, riverbanks, holder rings and neighboring volumes together.
5. Regenerate dependent yards and footprint masks, run appropriate geometry
   checks and inspect actual browser views.
6. Record completed and deferred buildings, then continue to the next site.

Housing needs row bodies, individual rear extensions and shared yard boundaries
considered together. A whole terrace should not be stretched to fit a single
house polygon. Some conflicts require re-registering streets or riverbanks in
the same pass. Old Lea connectivity/locks remain a separate deferred task.

## Build and review

Main authoring sources are under `data/maps/`; generated site data under
`docs/data/`. Do not edit only the generated JSON. Typical factory rebuild:

```sh
python3 scripts/build_factory_buildings.py
python3 scripts/build_infrastructure.py
python3 scripts/build_factory_yards.py
python3 scripts/build_housing_detail.py
python3 scripts/build_regional_footprints.py
python3 scripts/build_scene_manifest.py
```

If changing the City Mills, western Sugar House, Bow Bridge or Hunt bank registers,
rebuild `build_panorama_data.py`
before this sequence and `build_river_network.py` after infrastructure but before
the final manifest. Saved Howards JSON is sufficient for routine factory builds;
`prepare_howards_alignment.py` additionally needs the private source extract,
OS mosaic and `reference/footprint-model-alignment/howards-before.json`.

The regional raster build requires the local research extract and the existing
`/home/jic823/swipe_map/site/data/Water_1895.geojson`. Abbey's fitter also needs
the local footprint extract; its saved JSON is sufficient to run the website.
No generator runs on GitHub Pages. The cache manifest must match public modules
and assets after changes.

Relevant checks:

```sh
python3 scripts/check_factory_buildings.py
python3 scripts/check_factory_footprint_alignment.py
python3 scripts/check_sawmill_footprint_alignment.py
python3 scripts/check_oil_wharf_alignment.py
python3 scripts/check_howards_alignment.py
python3 scripts/check_sugar_house_alignment.py
python3 scripts/check_west_sugar_alignment.py
python3 scripts/check_crystal_barber_alignment.py
python3 scripts/check_abbey_west_alignment.py
python3 scripts/check_bow_works_alignment.py
python3 scripts/check_hunt_works_alignment.py
python3 scripts/check_lascelles_ultramarine_alignment.py
python3 scripts/check_williams_asphalte_alignment.py
python3 scripts/check_refinery_printing_alignment.py
python3 scripts/check_kendrick_usher_alignment.py
python3 scripts/check_three_mills_north_alignment.py
python3 scripts/check_three_mills_south_alignment.py
python3 scripts/check_three_mills_landmark_alignment.py
python3 scripts/check_abbey_station_plan.py
python3 scripts/check_factory_yards.py
python3 scripts/check_housing_detail.py
python3 scripts/check_western_completion.py
python3 scripts/check_district_streets.py
node scripts/check_district_navigation.mjs
python3 scripts/review_factory_buildings.py --station-only --url http://127.0.0.1:4175
python3 scripts/review_factory_buildings.py --footprints-only --url http://127.0.0.1:4175
python3 scripts/review_factory_buildings.py --ink-only --url http://127.0.0.1:4175
python3 scripts/review_factory_buildings.py --sawmill-only --url http://127.0.0.1:4175
python3 scripts/review_factory_buildings.py --oil-wharf-only --url http://127.0.0.1:4175
python3 scripts/review_factory_buildings.py --howards-only --url http://127.0.0.1:4175
python3 scripts/review_factory_buildings.py --sugar-house-only --url http://127.0.0.1:4175
python3 scripts/review_factory_buildings.py --west-sugar-only --url http://127.0.0.1:4175
python3 scripts/review_factory_buildings.py --crystal-barber-only --url http://127.0.0.1:4175
python3 scripts/review_factory_buildings.py --abbey-west-only --url http://127.0.0.1:4175
python3 scripts/review_factory_buildings.py --bow-works-only --url http://127.0.0.1:4175
python3 scripts/review_factory_buildings.py --hunt-works-only --url http://127.0.0.1:4175
python3 scripts/review_factory_buildings.py --lascelles-ultramarine-only --url http://127.0.0.1:4175
python3 scripts/review_factory_buildings.py --williams-asphalte-only --software-gl --url http://127.0.0.1:4175
python3 scripts/review_factory_buildings.py --refinery-printing-only --software-gl --url http://127.0.0.1:4175
python3 scripts/review_factory_buildings.py --kendrick-usher-only --software-gl --url http://127.0.0.1:4175
python3 scripts/review_factory_buildings.py --three-mills-landmarks-only --software-gl --url http://127.0.0.1:4175
```

If WSL's hardware-backed review loses its WebGL context, add `--software-gl`
to the factory review command. This uses SwiftShader for local captures and
records the graphics backend in the report; it does not alter the public app.

Geometry checks, 77 navigation destinations, four Abbey views and five factory
alignment views passed before the initial checkpoint. The continuation adds
supporting-building and route-clearance checks; all seven Abbey browser views
passed and were visually inspected.
The ink-works continuation passes the geometry/clearance checks and four focused
browser views, including the retained chimney opening and three moved stacks.
The sawmill continuation passes its group/stack/road checks, the district street
audit and five visually inspected browser views. All 16 mill/Towers ranges and
the transferred chimney reached the renderer, without browser/shader errors.
The Oil Wharf pass adds six inspected browser views, covering the four-tank
group, northern disused tank, stores, road and neighbouring sawmill frontage.
Diagnostics confirm ten ranges and five tanks; geometry and clearance checks pass.
The Howards review was interrupted after its first image before the WSL restart.
On 29 September all seven views were rerun and visually inspected; all 86 ranges
and 18 corrected chimneys reached the renderer with no browser/shader errors.
Howards source agreement is at least 99.157% per rendered group. Factory, all
alignment, yard, housing, Abbey, western, street and 77-destination checks pass.
The Sugar House pass also passes source/compartment, roof-direction, chimney-hole,
road-junction and yard checks. Minimum rendered group agreement is 99.855%.
All six final browser views passed and were visually inspected after the yard
correction; diagnostics confirm all 31 eastern ranges and the corrected chimney,
with no browser/shader errors.
Private source comparisons and the immutable pre-pass snapshot are under
`reference/footprint-model-alignment/sugar-*`; use the snapshot when regenerating
the authoring register. Routine builds need only the saved register.
Oil Wharf, Howards and eastern Sugar House were committed as `6dc446d` on
29 September. The western, Crystal Wharf / Barber, High Street, Bow Bridge and Hunt
continuations were subsequently committed as `527d3e9`. No push
or deployment. The western private immutable snapshot is `west-sugar-before.json` in
`reference/footprint-model-alignment/`; routine builds need only the saved register.
Browser screenshots and diagnostics
are local under `scenes/channelsea-sewer-panorama/review/`. No mobile audit.
Western continuation: all geometry/clearance and 77 navigation checks pass;
seven final browser views pass after restoring the yard, with affected views
visually inspected. Minimum western group agreement is 99.874%.
Crystal Wharf / Barber: all geometry, clearance and navigation checks pass;
seven browser views passed and were visually inspected, with all 40 eastern
ranges and three chimney positions confirmed and no browser/shader errors.
Minimum new-group agreement is 99.977%. The immutable pre-pass snapshot is
`reference/footprint-model-alignment/crystal-barber-before.json`;
`prepare_crystal_barber_alignment.py` needs it and the private source/maps.
Routine builds use the saved register. Two restored yards bring the total to 85.
High Street compounds: eighteen new source-linked ranges in fifteen groups;
all geometry/clearance, prior alignment and 77 navigation checks pass. Seven
browser views passed and were visually inspected, confirming the sixteen ranges
at sites 256/572/573 and corrected Hogarth stack without browser/shader errors.
Minimum rendered source agreement is 99.933%, including a recorded 0.52 m²
High Street pavement corner. `prepare_abbey_west_alignment.py` needs the private
extract and immutable `reference/footprint-model-alignment/abbey-west-before.json`;
routine builds use the saved register. Road/bank authoring is unchanged.
Bow Bridge: all geometry, earlier alignment, clearance, yard, housing, street,
Abbey, western and 77 navigation checks pass. Seven browser views passed and
were visually inspected, confirming seventeen ranges and five chimney positions
without browser/shader errors. Minimum rendered supplied-outline group agreement
is 99.979%; direct OS traces are counted separately. The four independent chimney
bases clear roofs and the channel remains open. `prepare_bow_works_alignment.py`
requires the private extract, cached OS maps and immutable snapshots
`reference/footprint-model-alignment/bow-works-before.json` and
`bow-works-ground-before.json`. Routine builds use the saved registers.
Hunt's soap works: ten supplied-outline ranges in six groups, including three
additions. All geometry/clearance, prior alignment, yard, housing, street, Abbey,
western and 77 navigation checks pass. Six browser views passed and were visually
inspected, confirming all ten ranges and both chimney positions without browser
or shader errors. Minimum group agreement is 99.977%; the checked local Lea
channel is 23.98 m wide. `prepare_hunt_works_alignment.py` needs the private
extract and immutable `hunt-works-before.json` / `hunt-works-ground-before.json`
snapshots in `reference/footprint-model-alignment/`. Routine builds use saved JSON.
Lascelles / Ultramarine: all six ranges pass the source, sheet-join, retained-height,
chimney-hole, lane and neighbour checks. Earlier alignment, factory, yard, housing,
street, Abbey, western and 77 navigation checks pass. The prepare script is
idempotent, including the lane correction. It needs the private extract, cached
OS maps and immutable `reference/footprint-model-alignment/lascelles-ultramarine-before.json`.
Routine builds use saved JSON. Minimum agreement with reconciled outlines is
99.999%; raw Ultramarine agreement is lower because the explicit seam strips are
absent from the supplied extract. See `FOOTPRINT_ALIGNMENT.md` for both measures.
Six browser views passed and were visually inspected with `--software-gl`,
confirming all six ranges and the 60-foot chimney without browser/shader errors.
Two preceding hardware-backed attempts lost their WebGL context; the software
review completed successfully. The broader Lascelles/Ultramarine working-ground
envelopes remain for a separate parcel review alongside Williams wharf.
Williams / French Asphalte: seventeen source-linked ranges, two direct OS traces,
added 704, corrected lean-to attribution, two chimneys and the local lane pass
geometry and clearance checks. All prior alignment, factory, yard, housing,
street, Abbey, western and 77 navigation checks pass. Preparation is byte-for-byte
idempotent; routine builds use saved JSON. Source preparation requires the private
extract, cached OS tiles and immutable `williams-asphalte-before.json`; run it
after Lascelles/Ultramarine preparation when regenerating both road corrections.
Minimum completed-reference agreement is 99.998%; western Asphalte raw-source
agreement is 82.186% because its eastern map completion is absent from the extract.
Six Williams/Asphalte browser views passed with SwiftShader and were visually
inspected, confirming all eighteen site-568 ranges, the reassigned lean-to and
both chimney positions without browser/shader errors. Yard-envelope review remains
separate. Regional masking now covers 234,606 visible features in 115 tiles.
Refinery / printing / machinery depot: all eighteen site-567 ranges are accounted
for (seventeen source-linked plus storage shed 688 directly traced), including
five additions. New source/trace, chimney, road and neighbour checks pass, as do
all preceding alignment, factory, yards, housing, streets, Abbey, western and
77 navigation checks. Minimum rendered source agreement is 99.980%. Existing
factory geometry outside site 567 is unchanged. The narrow lane keeps its 5.2 m
carriageway; four recorded façades have an interpreted 0.55 m minimum pavement
clearance, with actual pavement meshes clipped against the mapped walls.
Preparation is byte-for-byte idempotent. Run it after the Lascelles and Williams
preparations if regenerating all authoring registers; saved JSON suffices for
routine scene builds. Regional masking now covers 234,589 visible features.
Six refinery/printing browser views passed with SwiftShader and were visually
inspected, including the narrow lane and stepped northern shed; all eighteen
ranges and both mapped chimneys rendered without browser/shader errors.
Latest local asset revision: `962666bb4d46` (all public asset hashes verified).

## Preserve these corrections

- Regional ground and context-water meshes exclude the detailed ground envelope;
  otherwise the flat background obscures submerged riverbeds.
- Retain the original detailed tidal range; historical elevation data has not
  yet established a replacement vertical datum.
- Source/date differences matter. Modern station photographs supply surviving
  architecture, while the period map/engraving supplies the c1900 arrangement.
- Large GeoPackages, LiDAR archives, reference images and review exports remain
  outside Git. `MEMORY.md` is also intentionally local and ignored.

## Parallel height work — leave with the author and Claude

The actively growing source is **reference/spot-heights/heights.geojson**, not the
older 105-point `readings.geojson` prototype. Re-read it when needed; counts go
stale quickly. The author reports **1,773 distinct marks** during the Oil Wharf
pass; this is an author-reported count, not a new coverage audit. The earlier
1,083-mark audit found about 50% of West Ham within 500 m of a mark. Do not
overwrite or merge their extraction scripts/readings.

The prototype-only `prepare_historic_height_controls.py` is not an importer for
the expanded schema. Separate ground, banks, structures and benchmark mounting
contexts. Values are reported in feet above Liverpool OD; no Newlyn conversion
or scene-y alignment has been established. Do not apply a 0–40 ft cutoff across
the wider region. The 2003 terrain mosaic is downloaded but not integrated.
See `TOPOGRAPHY_RESEARCH.md` for coverage and datum limitations.

Kendrick / Usher preparation is last in the authoring sequence, after the
refinery/printing preparation. Routine builds use the saved JSON registers.
Focused browser review: `python3 scripts/review_factory_buildings.py
--kendrick-usher-only --software-gl`. The software GL flag avoids the recurring
WSL hardware-context loss; inspect all six generated views.

Kendrick/Usher final verification: all geometry and prior alignment checks pass;
six SwiftShader views passed and were visually inspected. Manifest
`5461589935f6` matches all 25 module/139 asset hashes. Regional coverage is
234,579 visible features, 115 tiles (4.01 MB). Current yard counts are
85 surfaces, 36 wear routes and 160 stock groups. Changes remain uncommitted.

Northern Three Mills authoring: `prepare_three_mills_north_alignment.py` uses the
private source extract, cached map and immutable `three-mills-before.json`.
It is idempotent and follows the Kendrick/Usher pass in a full regeneration.
The new works-passage record is replaced by name, never duplicated. Routine
scene builds use the saved JSON.

Northern Three Mills final checks: all geometry and earlier alignment checks pass,
with six inspected SwiftShader views and a final tank capture after the radius
adjustment. Manifest `1669da522491` matches 25 module/139 asset hashes. Regional
coverage is 234,569 visible features, 115 tiles (4.01 MB); yards 85/36/160.
Factory progress: 355 of 547 ranges have reviewed source matches or direct traces;
190 still need alignment and two retain provisional transfers. Twenty-seven sites
have some remaining work; sixteen are complete for their current building ranges.
Housing's 196 rows remain a separate footprint-alignment task.


Southern Three Mills authoring: `prepare_three_mills_south_alignment.py` uses
`three-mills-south-before.json` and the private source extract; saved output is
byte-for-byte idempotent. North/south preparation shares
`factory_alignment_records.py`. Run the southern check with `--preflight`
before regenerating dependent layers. Runtime checks preserve every other
building and structure, including the eight pending mill/wharf ranges.

The southern tank review also fixes yard exclusions: all modeled tanks are now
blocked, resolving a barrel group inside a vessel. Yards retain 85/36/160 and
clear all tanks. Housing remains 196/3204/3191. Regional coverage is 234,558
visible features in 115 tiles (4.01 MB). Manifest `9acadf9c9fc7` matches all
25 module/139 asset hashes. Geometry, prior alignment, yard, housing, street,
Abbey, western-completion and 77 navigation checks pass.

Final southern browser review: all three SwiftShader views passed and were
visually inspected (`review/three-mills-south-{plan,tanks,court}.png`). The report
`review/three-mills-south-alignment-checks.json` confirms all 38 site ranges,
the engine chimney and five fitted tanks reach the renderer without browser or
shader errors. Final manifest: `9acadf9c9fc7`. Changes remain uncommitted.

Mill/wharf geometry and all earlier factory alignment checks pass, along with
street, yard, housing, Abbey, western-completion and 77 navigation checks.
Regional coverage is 234,550 visible features, 115 tiles (4.01 MB); yards remain
85/36/160 and housing 196/3204/3191. Manifest `5cd6e03c4929` matches all 25 module
and 139 asset hashes. The saved source register and road preparation are
byte-for-byte idempotent.

All four landmark browser views passed without errors and were inspected. The
House Mill close view exposed generic window frames behind the weatherboarding
and dormers mostly buried in the pitched roof. The renderer now suppresses the
covered masonry openings and seats dormers against the actual roof plane;
a focused House Mill follow-up checks these final presentation fixes.

The final House Mill follow-up passed and was visually inspected: weatherboard
openings are clear and dormers meet the roof plane. All landmark/tank anchors
also pass the renderer checks. Final revision remains `5cd6e03c4929`.
