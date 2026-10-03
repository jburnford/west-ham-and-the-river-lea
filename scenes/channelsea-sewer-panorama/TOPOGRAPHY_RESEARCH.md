# Main industrial scene: regional marsh integration (2 October 2026)

- `scripts/build_main_landscape.py` produces `docs/data/main-landscape-1900.*`.
  It consumes the frozen early-derived regional ground/weight, continuous bank
  policy, frozen audit and existing detailed scene geometry. `main-landscape.js`
  loads/applies it AFTER historic elevation and river-system adjustments.
- Native core/network/system/extension meshes retain XY/topology. Early marsh
  levels replace dry ground within the interpreted envelope. A subdivided mesh
  replaces the remaining flat placeholders within that envelope. Outer terrain
  is retained. Channel beds, exposed tidal mud and drain water are protected.
- Banks use longitudinal crest profiles (77 accepted controls across 28 bank
  components; unobserved components explicitly inferred). Existing masonry
  edges follow those profiles. Railway slopes meet the new ground but station
  grades and bridges retain their existing geometry; sewer crest/cover remain
  continuous and native side slopes are refitted at their feet.
- 58 premises floors: three have same-premises yard observations; other floors
  conservatively use local marsh estimates, retaining at least the former
  interpreted -0.1 m scene floor. These are estimates, not measured fill depths.
  Nine accepted street controls remain local to mapped road corridors. Buildings,
  holders, chimneys, housing, yard stock and trees are seated on revised ground.
- Comparison points (scene Y; add 1.83544 m for provisional ODN): Pudding–City
  1.4291, neighbouring western Stratford 1.3923, northern Mill Meads .1954,
  Abbey -.6717, western Plaistow -.9221. Stratford pair differs by about 4 cm;
  this is model agreement, NOT demonstrated historical accuracy.
- `?mainLandscape=baseline` preserves the previous dated scene for comparison;
  `?terrainEpoch=baseline` also disables the adapter. Neither changes sources.
- Validation: `scripts/check_main_landscape.mjs`, `check_main_landscape.py`,
  `check_continuous_structures.py`; browser runner
  `review_historic_elevation.py --main-landscape-only --url http://127.0.0.1:4175`.
  Screenshots/report: `scenes/channelsea-sewer-panorama/review/main-marsh-*.png`
  and `main-landscape-checks.json`. Regenerate scene manifest after asset edits.
- The experimental flood solver still has its previous field. Do NOT describe
  the visible landscape integration as a calibrated flood simulation or claim
  30 cm accuracy. No commit/deployment performed.

Continuous regional structures completed in the same pass:
- `regional_continuous_structures.py`, policy
  `data/maps/lower-lea-region/continuous-embankments-1900.json`, fine structures
  buffers and ground/surface visibility in `lower-lea-landscape.js` replace
  isolated bank dots with along-shore crests; full sewer crest and separate
  bridge decks. Open waterways/source-window boundaries remain open.
- The 11.3 ft point `sh_538907_182862` was visually checked on full mosaic
  `reference/spot-heights/mosaics/m18_131072_87143.png`: footpath NORTH of railway,
  not rail formation. Local surface-role override records this; frozen audit
  and reader files are unchanged. Therefore all six rail routes retain native
  interpreted grades rather than fitting that footpath point.


---

# Terrain sources and study extent — 28 September 2026

## Working accuracy standard

Elevation changes must also review dependent structures: building foundations,
yard and street connections, railway formation, sewer enclosure/supports,
walkways and water surfaces. Give each component an explicit reference
(ground, structural crest, or independently controlled water level); do not
apply a blanket vertical translation. Verify both contacts and clearances in
exterior views, since a camera on a deck cannot reveal a missing structure
underneath it. The Channelsea repair and its independent ground/crest mutation
checks are documented in [SEWER_HIGH_STREET.md](SEWER_HIGH_STREET.md).

The user specifies **very good to excellent accuracy, not 100% perfection**.
Proceed with defensible, documented approximations rather than waiting for
complete archival verification. Prioritise uncertainties that materially affect
terrain or flooding: vertical datum, ground levels, channel connectivity and
barrier heights. Use plausible ranges or alternative scenarios for consequential
unknowns, and distinguish observations from assumptions. Missing minor detail
should not block a useful reconstruction; research requirements below identify
ways to improve confidence, not universal prerequisites for modelling progress.

## Lower Lea expansion plan — Lea Bridge to the Thames

The author accepts the present landscape flood view as a first draft and asks
for the whole Lower Lea to become floodable. The next deliverable is a continuous
c1900 river and landscape model from Lea Bridge to the Thames, followed by layers
for river flow, tides, rainfall and drainage. Aim for very good to excellent
accuracy through progressive correction; incomplete minor detail must not hold
up the first regional version.

Recurring local flooding remains the baseline problem. The major events of
1888, 1897, 1904 and 1928 are separate, more severe comparisons, not the complete
flood chronology. Mill controls, upstream development, navigation changes,
low-lying land and tidal conditions must eventually work together in the model.

### Starting position and evidence

- The first flood view covers 1.22112 km² around the existing scene. It uses a
  uniform stage, four-neighbour connectivity and conservative 4 m cells. Only
  about 13.3% of this domain has full reviewed historical field support.
- The original `Lower_River_Lea.geojson` in the neighbouring `swipe_map` checkout
  has 23 features and extends beyond the clipped panorama: approximately
  E536018–539586 / N180574–186624. Endpoint coverage and period completeness need
  checking against maps; this bounding box is not the future flood domain.
  Two source geometries fail validity checks. Repair copies with an audit rather
  than editing the original or assuming touching polygons establish flow.
- `Water_1895.geojson`, `Water_First_Series.geojson` and `TQ_TidalWater.geojson`
  provide further candidates for channels, water bodies and the Thames connection.
  Their dates and feature meanings must be checked before combining them. These
  are source datasets, not a verified hydraulic network.
- The current height collection has 4,152 records: 3,211 spots and 941 benchmarks.
  Most describe streets or buildings; 124 are labelled open ground and 122 marsh.
  These are candidates, not newly approved controls. The older audit describing
  1,083 records is out of date. The existing terrain still uses 13 reviewed field
  controls, so expanding their use is a practical priority.
- The downloaded 2003 terrain mosaic covers 91.62% of the existing 108.67 km²
  regional research area at its 10 m working resolution. That is research-area
  coverage, not a coverage statistic for the new flood domain. Use it for broad
  relief after historical correction, not as an unmodified 1900 surface.

### 1. Establish the full domain and river inventory

Use Lea Bridge as the northern study limit and Bow Creek's Thames connection as
the southern end. Include both sides of the valley and the low ground around
Hackney Marshes, Stratford, Bow, West Ham, Canning Town and Leamouth. Locate the
lateral boundaries from terrain and possible flood routes, not borough limits or
an arbitrary buffer beside the river. The numerical domain may extend beyond the
visible study limits where that prevents boundary conditions distorting results.
The wider borough-plus-3 km research area remains a source envelope; it need not
all receive detailed hydraulic or building geometry.

Copy and hash the relevant source data into a self-contained project snapshot.
Catalogue every main reach, branch, junction, island, mill race, lock, weir,
sluice, drainage connection and terminal boundary. Use stable IDs with source,
date and confidence. Divide authoring/review into Lea Bridge–Stratford,
Stratford–Three Mills and Three Mills–Thames, but join them into one model.

Deliverable: an overview map showing present coverage, required additions,
period water routes, proposed floodplain bounds and unresolved connections.
Check every apparent disconnection and crossing against the source maps; retain
real isolated water bodies and controlled links rather than snapping them open.

### 2. Build continuous regional ground and bank levels

Refresh the height audit and review additional controls across the whole domain.
Keep marsh floors, street surfaces, raised yards, embankment feet, bank crests,
bridge decks and benchmarks separate. Prioritise controls that change flood
routes or storage. A benchmark only becomes a ground constraint when its physical
relationship to the ground is known.

Use the early terrain mosaic to establish broad rising ground and valley relief,
with c1900 corrections for later fill, transport works, flood schemes and channel
changes. Preserve source dates, datum conversions, missing-data masks and
uncertainty. Water-surface LiDAR returns cannot supply channel-bed measurements.
Use documented section estimates and plausible ranges where bed surveys are absent.

Replace isolated height patches and flat fallback ground with a continuous
historical working surface. Blend source transitions where the land is continuous;
retain actual walls, banks, cuttings and raised streets as explicit features.
Unknown ground must remain identified as unknown or estimated, not silently act
as a dry wall or a drainage outlet.

Deliverable: one coherent regional surface, with ground and bank evidence shown
separately, longitudinal river profiles and representative valley cross-sections.

### 3. Remove artificial seams and produce the first regional flood preview

Audit the visible straight lines against four distinct causes: the current
rectangular boundary, raster stair-steps/four-neighbour routing, edges of historical
height-support areas meeting flat ground, and real mapped linear earthworks.
Do not remove genuine barriers simply to make the water look smoother.

Keep tile edges invisible to the calculation by sharing boundary elevations and
water exchange. Preserve narrow bank crests as explicit barriers instead of
inflating entire coarse cells to the highest point. Begin with roughly 5–10 m
regional floodplain cells, with finer 1–2 m representation where narrow channels,
banks and openings matter; confirm the working resolution through comparison.
Display refinement may smooth the raster appearance only if it does not create
new connections or change the calculated water extent.

Extend the present connected-inundation preview over the completed river network
and regional surface. It remains a clearly labelled geometric first layer, with
separate retained/isolated waters and an explicit limit to the common tidal stage.

Deliverable: the whole study area can be explored and flooded in the browser,
with an overview and local views. Moving an internal tile boundary must not move
a flood edge. Expanding the external domain must not materially change inundation
in the central study area without an identified physical reason.

### 4. Bring structures and landscape levels into agreement

Adjust buildings, yards, roads, rail profiles, sewer earthworks, crossings and
water surfaces together as the regional terrain changes. Use explicit references
to ground, crest, deck or independently controlled water. Preserve bridge openings
below decks; treat mills, weirs and gates as controls rather than solid buildings
blocking the entire channel. Resolve the known railway/road-bridge height conflict
before treating those railways as reliable flood barriers.

This work accompanies each terrain expansion, rather than waiting until the end.
Keep detailed modelling around existing focal sites; use mapped building masses
and land-use areas elsewhere. Completing every facade is not a prerequisite for
regional flooding.

Deliverable: contact/clearance checks and repeatable exterior views, including the
sewer enclosure, river crossings, low streets and mill complexes, without floating
buildings, buried roads or lost structures.

### 5. Add movement, storage and drainage

Replace the common-stage preview with upstream river inflows at the northern
boundary and a downstream Thames water-level boundary at, or beyond, Bow Creek's
mouth. Check the downstream boundary placement with a short Thames reach or a
supported local stage transfer. Allow internal river levels to respond to flow,
channel geometry and structures rather than setting every reach to the same tide.
Represent the wider upstream watershed through inflow hydrographs initially;
reconstructing its entire landscape is a later option, not a dependency.

Connect channel flow to a two-dimensional floodplain so water can overtop banks,
spread, collect and remain after the tide falls. Then add rainfall, drainage
outfalls, sluices, culverts and pumping in order of their effect on results.
Record mill/weir/gate controls and operations by date. Begin uncertain controls
with explicit open/restricted/closed scenarios. Use the existing local solver as
a tested starting component, but demonstrate stability, conservation, resolution
sensitivity and agreement with reference cases before scaling it across the region.

Deliverable: a complete rise-and-fall sequence with depths, connected routes,
stored water and drainage time. Every inflow, outflow and storage change is
accounted for; water must not disappear when a slider is lowered.

### 6. Test ordinary flooding, then the four major events

Start with ordinary tide cycles, rainfall and constrained drainage. Run tide,
river inflow and rainfall separately, then in combination, to distinguish recurring
local ponding from major inundation. Test recovery between successive cycles.
Do not tune every scenario into a widespread disaster.

Build distinct 1888, 1897, 1904 and 1928 cases using their available evidence and
event-year infrastructure. Keep source claims separate from model assumptions.
Compare observed locations, reported street depths, flood extent and persistence;
do not turn a cellar depth into a ground water level. Use the Three Mills marks
as relative constraints until their absolute heights and datum are established.
Use river-flow and tide records with explicit transfer uncertainty rather than
applying remote gauge values directly to the whole Lower Lea.

Reserve some observations for independent checking rather than fitting all of
them. Vary uncertain bank heights, channel sections, roughness, gate states and
boundary levels. Report which conclusions remain stable across plausible values.
Numerical precision alone does not establish historical accuracy.

Deliverable: a defensible range of outcomes for each event and a documented
account of recurring local flooding, with major discrepancies identified for
correction rather than hidden by visual smoothing.

### 7. Preserve change through time and keep the model usable

Establish c1900 as the first complete regional baseline. Store dated changes to
channels, ground, banks, mills, navigation controls, roads, railways, sewers and
pumps as separate evidence-backed records. This must support the later move back
to 1848–50 and comparisons forward to 1928 without carrying later works into an
earlier scene. Do not average heights from different periods into one surface.

Separate hydraulic resolution from rendering detail. Tile the terrain and use
levels of detail for distant buildings; do not load a uniformly detailed 1 m
landscape over the whole valley. Keep computational tile boundaries physically
transparent and preserve consistent contacts when render detail changes. Run
longer hydraulic experiments offline if needed and load their results for smooth
browser playback. Retain the present live water-level experiment as a quick review
tool alongside those event runs.

Completion means a continuous, dated river system from Lea Bridge to the Thames;
a floodable landscape on both banks without artificial internal boundaries;
consistent structures; credible ordinary and major-flood behaviour; and uncertainty
that is visible and tested. The immediate next milestone is the full-domain
coverage/topology map and a continuous regional terrain preview—not all the
hydraulic and historical layers at once.

## Regional coverage and terrain preview — 1 October 2026

The first expansion milestone is available at `/lower-lea-region.html`, linked
from the 3D flood view's assumptions panel. It shows a 49 km² review window,
E535000–542000 / N180000–187000, with the original broader river routes and a
continuous 10 m lattice cropped from the 2003 relief mosaic. This is an evidence
preview: the rectangular window is not an approved flood boundary, the terrain
is not yet corrected to 1900, and no regional hydraulic simulation is applied.

The four original water layers are copied byte-for-byte into
`data/maps/lower-lea-region/sources/`, with origin paths and SHA256 checksums in
`sources.json`. The height collection is frozen separately in
`height-observations.snapshot.geojson`; a rebuild does not silently absorb later
transcriptions. `config.json` defines the review window and audit tolerances.

All 23 primary source reaches are present as 26 polygon parts. Two invalid
primary features are repaired on derived copies, with area changes recorded and
map review still required. Repair individual polygon parts before unioning water
coverage: repairing an overlapping MultiPolygon as one object can introduce dry
holes. Bow Creek loses about 807 m² of double-counted area through the union;
valid original water parts remain covered. The first-series layer contains the
same two repair cases. Original geometries are retained unchanged.

The contact audit finds four geometric groups and seven gaps within 15 m:
small Bow Creek part gaps, Three Mills Back River/Pudding Mill River, two
Waterworks gaps, Channelsea/Abbey Creek, and Bow Back River/Lea. These are candidate
review locations, not evidence of seven missing culverts or four hydraulically
isolated systems. No gap is snapped shut and no contact is assigned a gate state
or flow direction. Larger gaps and endpoint completeness still require map review.

The window contains 3,937 historical height observations, including the 13
already-applied field controls. Other readings remain unapplied and retain their
source datum, surface classification, confidence and disputes. The viewer can
show ground candidates alone or add streets, structures and benchmarks.

The exact source crop has 93.68% valid terrain. Missing values remain NaN with a
separate validity mask; no observations or modern elevations fill gaps. Rendering
uses a coloured relief image, and inspection reads the original float heights.
The 2003 surface includes later earthworks and water returns; it must not be used
as a c1900 flood surface or as channel bathymetry. Undated tidal-water context is
labelled separately from the primary river source and optional historical layers.

Build and check:

```sh
python3 scripts/build_lower_lea_region.py
python3 scripts/check_lower_lea_region.py
python3 scripts/build_scene_manifest.py
python3 -u scripts/review_historic_elevation.py --region-only --url http://127.0.0.1:4175
```

The builder reads the snapshotted GIS and the existing research raster, and writes
`docs/data/lower-lea-region/`. Data checks pass for source hashes, crop registration,
missing-value preservation, polygon validity, preservation of overlapping water
coverage, and independently recomputed gap distances. Browser checks pass for
layers, reach/gap selection, coordinate/height inspection, keyboard and pointer
navigation, and a 390 px mobile layout without overflow or console errors.
Desktop and mobile screenshots were inspected; reports are `review/lower-lea-region-*`.

Next: review source joins and river endpoints against period sheets, register
mill/lock/weir controls, and select additional ground and bank observations for
historical correction of the regional surface. The existing 3D landscape and its
bounded flood calculation are unchanged except for the link to this preview.

## Expanded dated terrain model — 30 September 2026

### First flooding view on the 3D landscape

Open `/?flood=1` on the local site (currently port 4175). This is the author's
requested basic first layer: raise a common river stage and see connected
inundation on the existing landscape. The slider spans 1.9–5.5 m ODN, starting
at 3.5; these are test values, not reconstructed events. Overview, Three Mills
and sewer-crossing cameras, a dry comparison, a north-up depth map and a visual
water-level rise are available. There is no simulated clock or flow rate.
The flood view defaults to the lighter scene-detail tier, with the same flood
surface and footprint geography; `&quality=full` restores full rendering detail.
While water is displayed, plain channel materials and the depth overlay avoid
two extra district reflection passes and reuse static shadows. The dry comparison
restores the original water materials and reflection behaviour.

`scripts/build_landscape_flood.py` composes the existing 1900 ground grid with
railway and sewer earthworks, road-profile paving and interpreted retaining walls.
It changes no source geometry. Crossings over mapped tidal water remain open
underneath. A 1 m sampling halo prevents thin retaining walls disappearing;
4 m cells conservatively retain the maximum 1 m sample. The domain is scene
[-510,-320,550,832], 265 × 288 cells, 1.22112 km². About 13.3% of the complete
domain has full reviewed field support; much of the remainder is inherited scene
interpretation, including banks. The inherited railway-height conflict remains
explicitly unresolved rather than silently moving visible structures.

A minimum-path-maximum calculation records the lowest river stage that can reach
each cell over four-neighbour surface paths. Seeds lie at least halfway inside
mapped tidal polygons. All tidal reaches share the test stage; mill controls and
upstream routing are omitted. Low areas behind a bank stay dry until a connection
opens at the chosen level. Lowering the level recomputes the connected extent;
it does not retain ponding or calculate drainage. This is a connected geometric
inundation view, not the local-inertial solver used by the smaller drainage demo.
The later hydraulic layers can replace its stage/extent calculation.

`docs/landscape-flood.js` draws depth-coloured water directly over the original
scene; buildings and the sewer remain intact. The gold rectangle marks the
computed extent. Tidal channel surfaces outside it follow the same visual stage,
but overbank flooding outside the rectangle is not calculated. Building interiors,
small drainage openings, rainfall, storage history and velocities are excluded.
Generated binaries and provenance live in `docs/data/landscape-flood-1900.*`.

```sh
python3 scripts/build_landscape_flood.py
python3 scripts/check_landscape_flood.py
python3 scripts/build_scene_manifest.py
python3 -u scripts/review_historic_elevation.py --landscape-flood-only --url http://127.0.0.1:4175
```

Numerical checks use an enclosed bowl, bank overtopping, an opened passage,
diagonal barriers and independent connected-component labels on the actual grid.
Extent grows monotonically with stage; these tests verify geometry, not historical
accuracy. Review outputs are `review/landscape-flood-*`.
The final software-WebGL review passes in the lighter rendering tier: river-level
changes, dry comparison, raise/pause, all three views, preserved sewer enclosure
and a 390 px mobile layout without overflow or console errors. Overview, Three
Mills, sewer and mobile screenshots were visually inspected. Full-detail software
capture timed out; this does not establish physical-device performance.

### Wider floodplain is the primary modelling objective

Catchment and mill controls are also central. Chapter 6 describes accelerated
water delivery through the straightened Middle Lea and early-1890s upstream
flood works, reduced rainwater absorption with watershed development, and
restricted passage through the Lower Lea's bridges, mills and obstructed channels.
Chapter 1's 1824 dispute concerns tidal storage for Three Mills and Four Mills;
retain its warning that the committee reports represent the complainants' case.
Represent upstream inflow hydrographs, dated mill/weir/gate operations and
navigation reaches together with downstream tidal levels and floodplain storage.
Do not assume uniform canalisation or identical effects for every intervention.
Development changes runoff and the number of people and properties exposed.

Further author clarification: recurring local flooding is the baseline problem;
1888, 1897, 1904 and 1928 are selected major events, not the only floods. Test
ordinary tidal cycles and rainfall with constrained drainage as well as extreme
event conditions. Track local ponding, persistence and recovery between cycles.
Do not require bank overtopping for every local flood or assign a single mechanism
to every major event. Present-day recurrence needs separate evidence and modern
infrastructure; the 1900 model cannot establish it.

Author correction, 30 September 2026: the demo gives too much prominence to
railway embankments. Model the bowl-like former marshland and tidal riverbank
overtopping as the main landscape and flood mechanisms; roads, railways,
culverts and sluices modify movement and drainage within that system. Chapter 6
explicitly describes ground below high-tide level and bank overtopping in 1897
and 1904. Retain the separate rainfall mechanism for the 1888 evidence.

The current 540 × 160 m crossing test contains no tidal river or riverbank.
Its western-stage pulse tests local backwater, not overtopping. Do not present
its results as an explanation of the district's historical flooding. The page
now states this distinction prominently; the existing solver remains a useful
component and the local test a secondary diagnostic.

The first geometric layer above connects the mapped tidal river network to the
existing wider surface. The next hydraulic iteration should improve the period
surface and bank crests separately from marsh floors. Identify which riverbank
levels and enclosing higher ground are supported;
13 reviewed field controls and 164,553 m² of supported terrain do not yet define
the whole basin. Use explicit plausible ranges where crest or terrain evidence
is incomplete, rather than inventing a bowl or treating rendered banks as surveys.
Drive a tidal rise, overtopping, recession and retained ponding; record overtopping
volume separately from rainfall and drainage exchange. Compare tide/surge alone,
rain alone and their combination before making culvert blockage the main contrast.
Check the sequence of inundation and persistence in mapped low areas against the
chapter's located observations. All changed ground must carry dependent structures
with it according to their actual ground/crest/water references.

### Interactive flood demo

Open `/flood-demo.html` on the local site. The page automatically runs a one-hour
rising-water experiment; **Compare blocked culvert** runs the same conditions
with the connection closed. Playback, minute-by-minute inspection, ground
provenance and selected-frame JSON downloads work for either one or two runs.
Western surge and rainfall presets, one-way or unrestricted flow, a test pump,
rail formation and common elevation adjustments expose the important assumptions.
The simulation runs in browser workers; no service or WebGL is required.

The dedicated 1900 grid covers scene x=0–540, z=520–680: 8.64 hectares in
270 × 80 cells at 2 m. About 67.5% of grid locations have full support from the
existing historical field surface before roads, railways and drains are applied.
Remaining field cells interpolate reviewed period controls separately on each
side of the railway. They remain visibly marked as estimated. Road paving follows
the restored profile. The western candidate ditch is extended to an explicit test
outlet; its slope, section and outlet conditions are assumptions. Other domain
edges are closed. No mapped factory footprint intersects this small domain.

The local railway formation defaults to an assumed 1.6 m ODN, adjustable from
1.0 to 1.9 m. This range allows more than 3 m clearance beneath the estimated
southern road bridge after the modelled rail height and a 0.5 m roof allowance.
It is a common local grade for the two routes, not a measured longitudinal
profile. The main 3D railway remains unchanged and still needs the joint profile,
branch and bridge correction described below. The flood demo changes none of the
existing 3D terrain, sewer, structure or texture assets. A common elevation shift
in the experiment moves ground, road, rail, channel and culvert inverts together;
the prescribed water levels remain fixed.

`docs/flood-solver.js` uses conservative cell volumes and local-inertial face
flows with Manning friction, an adaptive gravity-wave timestep and a donor
limiter to keep wetting/drying non-negative. The method follows the simplified
momentum approach of [Bates et al. (2010)](https://doi.org/10.1016/j.jhydrol.2010.03.027).
The candidate culvert is a separate head-driven link with entrance/exit losses,
barrel friction and optional one-way control. Its partially wetted section is an
approximation, not a calibrated inlet-control rating. Rain adds volume; the
optional pump removes only available water, up to 0.08 m³/s. Prescribed-stage
boundaries exchange measured volumes through faces rather than overwriting cell
depths. Initial storage plus boundary inflow and rainfall, minus outflow and
pumping, is checked against current storage.

The boundary pulse is synthetic: five minutes at base level, fifteen minutes
rising, fifteen at peak, twenty falling and five at base. Default eastern peak
is 1.65 m ODN; western and eastern base levels are 0.65 and 0.82 m. No infiltration,
urban sewer network, observed gate schedule or historical pumping capacity is
included. The page and exports identify these limitations and reject other
terrain epochs. The 1888, 1897, 1904 and 1928 events still require dated geometry,
local boundary transfer and comparison with independent flood observations.

Rebuild after changing the source terrain, infrastructure or drainage graph:

```sh
python3 scripts/build_flood_demo.py
python3 scripts/build_scene_manifest.py
node scripts/check_flood_solver.mjs
node scripts/check_flood_demo.mjs
python3 -u scripts/review_historic_elevation.py --flood-only --url http://127.0.0.1:4175
```

Inputs are in `data/maps/flood-demo-1900.json`; the generated grid retains source
hashes in `docs/data/flood-demo-1900.json`. Numerical checks cover still water,
wetting and drying, barriers, culvert direction and resistance, rainfall, pumping,
boundary exchange and timestep refinement. Six full-hour scenarios conserve
water to better than 0.00001 m³. The default open/blocked comparison gives peak
flooded land of 3.36/3.82 hectares respectively, counting depths above 5 cm outside
channel cells. A western surge produces reverse flow only through the unrestricted
connection. These are regression results for controlled inputs, not estimates of
the historical floods or proof of field accuracy.

Browser checks exercise real workers, comparison, playback, inspection,
provenance, selected-frame export, cancellation and a 390 px mobile viewport.
Reports and desktop/mobile screenshots are saved in `review/flood-demo-*`.

### Culvert sections and railway-height conflict

`data/maps/culvert-section-1900.json` adds four provisional sections to the
connection review, generated by `scripts/culvert_section.py`. The working
rectangular equivalent opening is 0.9 m wide and 0.6 m high, with an assumed
east-to-west slope of 0.002. Its eastern invert continues the existing **assumed**
drain bed at 0.524 m ODN across the unrendered approach; the western invert is
0.434 m ODN. Neither level is observed. A 0.15 m roof and 0.25 m minimum cover
are modelling allowances, not engineering specifications or structural checks.

Checking the whole road/shoulder crossing gives about 0.299 m minimum cover for
the working section. A smaller 0.6 × 0.45 m opening at slope0.001 leaves0.442m.
A 1.2 × 0.9 m opening at the original bed brings the roof to the road surface
and fails. Lowering that larger opening0.3m restores0.299m cover but requires
lowering the approach drain. This alternative is not applied automatically to
the 3D terrain. No opening area is converted into a discharge; downstream head,
sluice operation, losses and the western outfall remain unresolved. The existing
graph retains null observed inverts/capacities and hydraulicReady=false.

The southern mosaic `m18_131072_87149` shows Manor Road passing over the railway.
Two independent readers agree on road bridge spots21.2ft and20.8ft. Interpolating
between their positions at the modelled rail crossing gives a provisional road
deck6.018mODN, about277m south of the drain crossing. The inherited constant rail
formation7.335mODN is already1.318m above it, before rails or clearance. This
invalidates the constant formation as a calibrated railway/flood-barrier profile.
It does not establish a track height at the drainage crossing. Next geometry
work must revise the railway longitudinal profile, branch joins and road bridge
together; the current scene railway has not been lowered by this section study.
Source image, sidecar and both reading files are hashed in the connection data.

The interactive longitudinal section separates measured road heights from assumed
culvert dimensions and marks railway levels off scale/unverified. Node checks
independently recompute roof cover and test the rejected/deeper cases and epoch
guards. Desktop/mobile browser checks exercise all four sections independently
of the five topology scenarios. All3D asset hashes remain unchanged in this pass.

### Manor Road at the drainage crossing

The 181.6 m bounded road section is restored from `m18_131075_87146` in
`data/maps/manor-road-1900.json`. The centreline follows the carriageway rather
than the roadside drain. Three road spots, independently read by opus-af and
opus-ah, are 6.6, 6.2 and 6.5 feet; the 6.20-foot kerb benchmark is retained as
context, not fitted as a carriageway spot. With the shared provisional datum,
the road surface is approximately 1.62, 1.49 and 1.58 m ODN. Linear interpolation
sets the profile. Width 6 m, shoulders 1.1 m, paving and earthwork transitions
are interpretations. The bounded ends are review limits, not historical termini.

The Woolwich railway alignment beside this section is also retraced, with 80 m
joins to the earlier route. Minimum road/rail centreline separation is 14.71 m;
the paved road and shoulders clear the rendered ballast. Its inherited 5.5 m
scene formation remains provisional. Map S.P. symbols are signal posts, not
railway height observations. Other railway routes and the sewer assets remain
unchanged. The terrain overlay locally replaces road/rail-foot protection only
within the reviewed road earthwork; the railway deck is not translated.

`terrain-1900.road-mask.u8` distinguishes this earthwork from field interpolation.
The terrain grid under the road is 0.065 m below its surface, which is rendered
from the same profile. The ODN grid therefore contains **subgrade** there: future
flood preparation must compose the road surface from `roadProfiles`, not treat
the terrain grid alone as a finished hydraulic DEM. Road observations are dated
separately from the 1900 continuation assumption; other epochs cannot load them
automatically. Source images, sidecars and both readings are hashed.

Rebuild order: `build_infrastructure.py`, `build_river_network.py`,
`build_historic_elevation.py`, `build_drainage_connections.py`, then
`build_scene_manifest.py`. Road checks cover measured levels, ground contact,
rail clearance and separate epoch selection; the drainage, terrain and sewer
regression checks remain required. Browser review: `review_historic_elevation.py
--manor-only`.
Road, terrain, drainage, sewer and topology checks passed. The full-scene browser
comparison also passed, including unchanged sewer/railway diagnostics between
terrain modes and unchanged isolated drainage at high river tide. Overhead and
ground-level road views were inspected; report `review/manor-road-checks.json`.

### Mapped drainage added to the ground model

`data/maps/historic-drainage-1900.json` retains source pixel traces from the
five-foot mosaics `m18_131072_87146` and `m18_131075_87146`, four labelled sluice
locations, and a possible connection beneath the railway/Manor Road corridor.
The blue-filled channel east of Manor Road has a continuous double-line western
reach. Only this identifiable open channel is currently cut into the terrain.
The uncoloured western junction feature remains an unresolved candidate, and
the underground crossing remains disabled as a hydraulic connection. Sluice
locations are approximate map positions, not surveyed gate or invert locations.
Neither gate operation nor invert heights have been assigned.

The builder renders 205.8 m inside supported ground (scene bounds
315,565 to 520,600), changing 1,021 grid nodes. It preserves the full map trace
beyond that window. Model ends fade over 6 m; these are coverage boundaries,
not evidence of dams, physical channel ends or outlets. Do not use them as
closed boundaries in a future flood solver.

The section is an explicit working assumption: 5 m bank-top width, 2 m bed
width, bed 0.9 m below the lowest surrounding interpolated rim, and 0.3 m of
standing water. This produces roughly the mapped water width but is not a
surveyed cross-section. The water level is held independently of Channelsea's
illustrative tide. Sluice operation and downstream connectivity must be added
before coupling it to a flood event. These assumptions apply only to the
1900 scene; other epochs still require their own review.

The cut modifies the shared target grid before generating the scene and ODN
exports, so the sampler, extension mesh and exported levels agree. Local 1 m
mesh refinement resolves the narrow banks. Water triangles are clipped against
the actual rendered bed, avoiding a water stripe floating over the ground.
`terrain-1900.drainage-mask.u8` identifies assumed channel sections separately
from interpolated field heights. The ODN export includes these assumed bed
levels; its values are not all observed or interpolated field ground. Source
imagery, sidecars and trace JSON hashes are retained in the metadata.

Validation: `check_historic_drainage.py` checks the trace, epoch isolation,
disabled uncertain connections, protected structures, unaffected height
controls, section mask and bed/water geometry. The existing elevation checks
retain their field-height bounds outside the new drainage mask. The browser
review's `--drainage-only` option captures overview and close views in baseline
and 1900 modes, verifies water independence at high tide, and compares the
sewer crossing, buildings and railway diagnostics between terrain modes.

### Drainage connections and crossing audit

The separate [connection review](../../docs/drainage-connections.html) now
represents six locations and four reaches in a dated graph. Following the
author's engineering interpretation, the preferred reconstruction is a probable
culverted connection draining east to west with effective controls against
return flow. Ditches on both sides, alignment and mapped sluices support that
interpretation. Nearby eastern ground readings of6.3–6.4ft versus4.5–4.9ft west
of the crossing support it too (approximately0.4–0.6m difference); they are
ground readings, not invert or water levels. A sluice label does not prove an
automatic flap gate. The default scenario represents intended passage when
downstream water permits, not continuous drainage regardless of head.
The evidence-only scenario enables just the mapped eastern channel and remains
a sensitivity comparison, not the preferred historical interpretation. Other scenarios
assume the western feature is a drain with passing sluices, and vary the
crossing between blocked, east-to-west only, west-to-east only and unrestricted.
Results describe possible connectivity, not actual flow, flood extent or timing.
No invert, capacity, pump or confirmed outfall has been assigned. The northern
sluice remains isolated because its connecting route has not been reviewed.

The 45.04 m candidate crossing is a chord between map trace endpoints, not a
surveyed barrel alignment. It crosses both the Woolwich branch and the Abbey
Mills junction curve in the current infrastructure model. Their inherited
formation heights are interpretations. The closest current road route is over
400 m away: the historical Manor Road section is missing from the road geometry
at this crossing. A map-derived road context is drawn in the review only; no
road embankment or underground opening has been added to the 3D terrain.
Resolve that geometry and its level before using this corridor hydraulically.

The 1907 inquiry, printed p.29 note1 / PDF p.53, supports distinguishing open
marsh drainage, sewer capacity and pumping. Chapter6 of the author's book,
PDF p.182 and note21, identifies flood-related pumping failures in1875/1888.
Neither source identifies this culvert's dimensions. The 1848–51 skeleton
mosaics show railway/Marsh Lane context but too little field drainage to infer
continuity or disappearance. The graph rejects reuse for other epochs.
A same-name Manor Road drainage agreement in the
[Essex Archives catalogue](https://www.essexarchivesonline.co.uk/result_details.aspx?ThisRecordsOffSet=1&id=1201477),
D/Z346/11321/1036, concerns Hackney Borough Council and is not accepted as
confirmation of this West Ham crossing.

Source/configuration: `data/maps/drainage-connections-1900.json`; build with
`scripts/build_drainage_connections.py` after the terrain/drainage build, then
refresh the scene manifest. `check_drainage_connections.mjs` checks source
hashes, graph endpoints, every direction/scenario, the isolated sluice, and
epoch guards. `review_historic_elevation.py --connections-only` exercises the
actual desktop/mobile controls and keyboard node selection. These checks pass;
the desktop and mobile screenshots were inspected. Terrain, structure geometry
and water levels were not changed in this connection-review pass.

### Field-ground interpolation

The default scene applies a bounded **1900 open-ground reconstruction** to
the northwestern low ground, southern Mill Mead and two areas of Plaistow Level.
Thirteen 1890s readings supply four separate interpolation zones. The affected
area is approximately **26.4 ha**, including transitions; approximately **16.3 ha**
has full interpolation weight. This expands the initial 8.4 ha / four-reading
pass. Changes relative to the previous inferred scene range from -0.94 to +0.22 m.
This remains a partial district elevation model.

The working relation is `height ODN = scene y + 1.83544 m`, provisionally derived
by retaining the scene's 7.4 m sewer crest and converting the historic 31.6 ft
crest with the OS local -1.3 ft Liverpool-to-Newlyn correction. It preserves the
established view and railway joins. The datum uncertainty is estimated at 0.3 m;
interpolated ground uncertainty is separately estimated at 0.5 m. Neither is a
statistically measured confidence interval. The historical Liverpool attribution
still needs sheet-margin verification. Existing tide levels are unchanged
illustrations, not calibrated historical water levels.

The four native source crops were inspected, including broader context for the
two northern observations. Ground readings of 7.6/6.3 ft north and 7.7/7.3 ft
south are kept separate from benchmarks, bank crests and uncertain drain figures.
Their original machine-inferred surface labels are preserved; the explicit
surface review is in `data/maps/terrain-epochs.json`.

The expansion adds nine reviewed readings on Plaistow Level: 4.5/4.9/5.7/5.5 ft
west of Manor Road and 4.7/3.9/4.9/6.3/6.4 ft to the east. Each was inspected
at native 6x with wider context; crops are retained in `terrain-epochs/control-review`.
Two west-side readings have a marsh versus unmade-path classification disagreement,
but both readers agree on value and position. No raised earthwork is shown at
those dots. Explicit reviewed approximations allow adjacent-ground use while
preserving the original conflict; disputed values and wall/benchmark readings
remain excluded. Boundary/drain-side readings are ground references, not inverts
or water levels. Existing mapped drainage corridors remain protected.

Each interpolation zone now has its own geographic bounds and feathering.
Expanding the export rectangle cannot spread the original Mill Mead readings
into Plaistow Level or blend the new east and west areas across Manor Road.
Only those bounded areas replace the existing flat ground mesh. This is a
practical compartment approximation, not a surveyed flood-connectivity model.
The nine new controls receive full interpolation weight and are fitted within
grid precision. Three additional, unused readings of 6.4/6.4/6.5 ft at nearby
unmade path/plot margins give residuals of -0.085/-0.072/-0.087 m. These check
local consistency only: they do not validate the provisional datum or imply
centimetre accuracy throughout the reconstruction.

Buildings and industrial pads, road corridors, railways, sewer embankments,
riverbanks and drainage corridors are protected in this first pass. The same
height transform applies to both existing terrain meshes; a tessellated mesh
replaces the old flat ground within the trial where required. Gardens sample
the resulting surface, including negative local heights on defended dry land.
Horizontal geometry is unchanged. Two northern control positions fall inside
the earlier interpreted sewer/industrial protection and one southern control
falls in its transition. They constrain adjacent ground, but are **not fitted at
those protected positions**. The overlay records each control's applied weight;
The conflict review now identifies the rendered sewer-bank triangles themselves
as overlapping the northern ground dots, as well as the broad gasworks boundary.
Those readings retain adjacent-ground use; forcing them onto the bank surface
would be inappropriate. A separate bank-section refinement remains necessary.
Per-control metadata records nearby protection categories, the source review,
any explicitly resolved surface classification and the applied ground elevation.

### Dates and future change

`data/maps/terrain-epochs.json` separates observation survey ranges, reconstruction
year, geometry epoch and vertical datum. The active 1900 scenario explicitly
accepts the 1890s observations as a continuity assumption. The 1848–51 skeleton
survey has its own source profile and a reserved 1850 scenario, but no merged
observations were available in this snapshot. Its period geometry is also
unresolved. An 1850 request is rejected rather than displaying 1900 sewers,
railways, fill or drains. No cross-epoch averaging or automatic interpolation
between years is performed. Building construction dates are not inferred.

The builder keeps content-addressed copies of the original collection under
`reference/topography-research-2026-09-28/terrain-epochs/`. Routine rebuilds use
the recorded snapshot; `--refresh-observations` explicitly captures a newer one
without changing the live collection, reader claims or merge results. Nearby
observations, including rejected types and any future earlier layer, remain in
the research catalogue with their original properties. New epochs require their
own authorized controls and period geometry; their surfaces can then be compared
only where both dates have support in a common datum.

### Flood work

The user-defined principal comparison cases are **1888, 1897, 1904 and 1928**,
before the major **1930s Lower Lea engineering works**. The 1898 rainfall event
remains secondary. 1928 is now a full modelling target as well as a flood-mark
calibration case. The 1888 newspaper account establishes a July–August rainfall
sequence; exact principal-event timing remains under review. Separate 1888 and
1928 terrain placeholders require period observations and geometry, with no
automatic reuse of the 1900 surface or pump/lock configuration.

Chapter 6 of the author's book confirms the tidal floods of **29 November
1897** and **30 December 1904**. Both are modelling targets. The rainfall flood
of **29 October 1898** (chapter 6, note 10) is a separate event. The supplied
July 1985 Three Mills photograph shows the 1897, 1904 and 7 January 1928 marks
in ascending order; Figure 19 identifies the eroded bottom date as 29.11.97.
Exact wall location, absolute heights and metric mark separations remain unset.

`data/maps/historic-flood-events.json` records the book, photo, event dates,
relative mark ordering, reported street depths and dated infrastructure changes.
Reported four-foot depths in some Stratford roads in 1897 and two feet in
Stratford High Street in 1904 are local descriptions, not uniform flood surfaces.
The 1928 event also provides calibration research for the upper mark.
The 1897/1898/1904 terrain epochs require period-geometry review before rendering;
the 1900 scene is not automatically substituted. In particular, the Channelsea
sewer bridge was rebuilt/widened in 1900–02. The unbuilt Morley/Tween scheme
of 1908–09 and the actual 1930s Lower Lea changes must remain distinct.

The supplied 1907 Outer London Inquiry report (Howarth and Wilson, printed p29,
PDF p53) describes made ground, former ditches lost to building, and improved
sewers/pumping. It dates enlargement of the Northern Outfall Sewer to 1906;
individual commissioning dates and the relationship to bridge works require
review. Its optimism that serious floods would not recur is contemporary opinion.
The [Thames exhibition](https://thames250exhibition.com/flood-management/) points
to daily Teddington head/tail readings from 1892, a lead for freshwater conditions
in the earlier events rather than a Three Mills tidal elevation.

The actual PLA/BODC 1928 spreadsheets and processed station series are now
saved under `reference/topography-research-2026-09-28/flood-evidence/bodc/`.
The [published dataset](https://doi.org/10.5285/b66afb2c-cd53-7de9-e053-6c86abc0d251)
gives event peaks of 4.1346 m ODN at Southend (6 January 23:49), 4.6306 m at
Tilbury (7 January 00:09), 5.0243 m at Gallions (00:58), and 5.2115 m at Old
Swan Pier/London Bridge (01:10). Each peak height/time was checked against the
raw spreadsheet. These are station observations, not assigned Three Mills levels.
Published decimal places do not imply historical millimetre accuracy.

The [authors' code](https://github.com/ivanhaigh/Thames-Sea-Level-Data) and
[datum table](https://www.nature.com/articles/s41597-022-01223-7/tables/4) give
London Bridge's THW correction as +3.459 m, whereas Gallions uses +3.475 m.
The common 18 ft 3 in / 5.55 m claim is not adopted as modern ODN. The 1931
*Engineer* table gives London Bridge +5 ft 9 in THW and describes THW as
12.50 ft above historical OD; that is a different datum.
The downloaded MATLAB loader adds 12 hours to every PM hour, shifting some
12-noon records to the next day. Specific event peaks check out, but a continuous
hydrograph requires timestamp review. Original files remain unchanged.

[NRFA](https://nrfaapps.ceh.ac.uk/nrfa/nrfa-api.html) gauged and naturalised daily
flows for both Feildes Weir (38001) and Kingston (39001) have been downloaded
for November 1897–January 1928. Recorded event-day means (m³/s) are:

| Event | Feildes Weir, gauged | Thames, gauged |
| --- | ---: | ---: |
| 1897-11-29 | 1.47 | 25.0 |
| 1898-10-29 | 0.475 | 16.4 |
| 1904-12-30 | 2.15 | 28.1 |
| 1928-01-07 | 22.7 | 522.0 |

The comparison does not support replacing the chapter's 1904 surge account with
a large upstream river flood. It does not independently prove a surge either.
Feildes' early record reflects mills/gates and three daily lock-keeper readings;
Kingston's historical series derives from Teddington. Naturalised values are
retained separately. A daily mean is not a peak or a Lower Lea hydrograph.
Acknowledgement: Data from the UK National River Flow Archive.

`scripts/review_historic_flood_evidence.py` reproduces these comparisons, source
hashes, peak checks and 29-day flow windows in `event-comparison.json`.
The BODC transfer stopped within its photographs, but all retained data members
were complete and CRC-checked; `download-manifest.json` records their identities.
The 1909–28 dredging programme is corroborated by the
[PLA baseline report](https://pla.co.uk/sites/default/files/2024-03/Baseline-Document-for-Maintenance-Dredging-june2007.pdf).
The supplied numerical claims of 2 m deepening, 0.7 m tidal-range increase and
1.5 m Southend surge residual remain unverified; none is applied to earlier events.
Sheerness exact-date ledgers and LCC/Lee Conservancy archive references remain
research leads. Monthly mean sea level cannot supply an event peak.

The first terrain export includes a separate support-weight grid, source-zone
grid and ODN ground raster. Unsupported, protected and transition cells are NaN
in the ODN export, not zero. River/rail/sewer/drain protection geometries are
archived separately with their inherited height status and unknown construction
dates. They are not yet validated hydraulic barriers. Water boundary levels,
drainage/sluice/culvert connectivity and breaches remain to be established before
simulating inundation. This incomplete raster must not be treated as a complete
flood DEM or used to claim historical flood depths.

### Bow Locks evidence added 30 September 2026

The [Bow Locks history](http://www.leeandstort.co.uk/Bow_Locks.htm) transcribes
a 7 January 1928 flood report, citing **TNA RAIL 845/112**. Around 01:30 it
reports water approximately 8 ft 6 in above normal head at Limehouse (2.591 m),
7 ft 8 in at Bromley (2.337 m), and 7 ft 7 in at Old Ford (2.311 m).
These are local relative levels, not ODN elevations, street depths or measured
surge residuals. The definition and absolute datum of each normal head remain
unresolved; the archive original has not yet been inspected. Stranded barges
above Three Mills and flooding of the Bromley staff houses supply qualitative
checks. The page's colour photograph shows the same flood-mark arrangement,
without resolving the exact wall location or providing a metric scale.

Its chronology separates a rejected 1898 Three Mills junction tide-gate proposal,
Bow lock improvement in 1900, duplication in 1931, and tidal-exclusion work in
2000. These are recorded as period constraints pending original plans and
operating records. The precise state within 1900 remains unresolved. The page,
photograph, conversions and provenance are retained in the research directory
and flood ledger; no absolute flood level or hydraulic barrier has been applied.

### West Ham pumps and Tideway comparison evidence — 30 September 2026

[HELT's history](https://heltrust.org.uk/our-past) distinguishes West Ham's beam
pumps discharging into the Northern Outfall Sewer from three centrifugal storm
pumps discharging into the Channelsea. Its 42 ft pump lift is a hydraulic height
difference, not an absolute elevation. [Historic England 1357997](https://historicengland.org.uk/listing/the-list/list-entry/1357997)
dates the engine house to 1897 and beam-engine installation to 1900. Exact
commissioning remains unresolved; full capacity must not be assumed for 1897/98.
No model discharge is assigned without pump curves, catchment/storage, tidal
outlet controls and event operating evidence. GLIAS newsletter 333 identifies
installation correspondence reportedly surviving at the 1982 Newcomen visit.

The supplied [Tideway Appendix Q](https://www.tideway.london/media/2114/53-heritage-statement-appendix-q-abbey-mills-pumping-station.pdf)
(January 2013) separates Abbey Mills Station B (1891–96) and C (1910–14), para
Q.3.9. The visually checked existing-features drawing, PDF page 35,
`DCO-PP-26X-ABMPS-270003`, explicitly places Tunnel Datum 100 m below ODN.
Five approximate spot levels 105.22, 105.35, 105.73, 105.67 and 105.22 m
therefore become 5.22, 5.35, 5.73, 5.67 and 5.22 m ODN. These are modern
comparison points with coordinates pending georeferencing, not 1900 controls.
The 105.40 m legend example is not a measured point. The 109.00 m shaft label
belongs to Lee Tunnel works shown as existing at the future start of Tideway
construction; it is not historic open ground. Section AA (PDF39) is illustrative.

The gazetteer points to underlying archaeological records: MOLA **ABM11**
(PDF21/printed17) for buried surfaces and gravel relief, and PCA **TMI03**
(PDF26/printed22) for 18th/19th-century alluvium under later made ground at
Three Mills. Original logs and sections are needed before inferring historic
surface heights or fill thickness. Sources and comparison observations are in
the flood ledger.

### Rainfall account of 1888 — user-supplied Trove transcription

[Trove article 107325485](https://trove.nla.gov.au/newspaper/article/107325485)
was inaccessible because of a bot-check, but the user supplied its OCR and
corrected the issue date to **14 September 1888**, superseding an initial 1897
attribution. It credits the News of the World of August 5 and describes a storm
on July 30 followed by additional downpours. The working event is therefore an
1888 rainfall sequence, not the November 1897 tide or a September 1888 flood.
The host newspaper title and original scan remain unverified.

Reported three-foot water on the Tilbury railway near Plaistow and six-foot
water in a Grafton Road cellar are separate local depth observations with
unknown floor/track reference elevations. Basement flooding around Barking Road
and Victoria Docks, low-ground inundation around Temple Mills/Hackney Marshes,
and portable/fire-engine pumping provide geographic and drainage evidence.
These do not establish a tidal surge, a river elevation or a mechanical failure.
The OCR's `Gin` at Freemasons Lane is retained as unresolved, not silently
converted to a six-inch control. No event-day hydrograph or absolute flood
surface has been assigned.

### Build and review

```sh
python3 scripts/build_historic_elevation.py
python3 scripts/check_historic_elevation.py
node scripts/check_historic_elevation.mjs
python3 scripts/build_scene_manifest.py
python3 scripts/review_historic_elevation.py --url http://127.0.0.1:4175
```

Build the dated overlay **after** any terrain, river, infrastructure or building
regeneration; its input hashes are checked for stale dependencies. Public assets
are `docs/data/terrain-1900.*` and `terrain-epochs.json`; the browser module is
`docs/historic-elevation.js`. The default preview uses 1900. Use
`?terrainEpoch=baseline` to compare the earlier inferred scene. The dates are
model inputs; no unsupported historical time-slider has been added.

Research outputs include `1900-terrain-review.png`, `checks.json`, dated
observations and protection geometry. Browser captures and comparisons are in
`scenes/channelsea-sewer-panorama/review/historic-elevation-checks.json` and
`elevation-*.png`. Numerical checks cover chronology guards, source exclusions,
datum conversion, protected geometry, ground-mesh coverage, independent local
height comparisons, compartment boundaries and unchanged tide levels. Browser
review includes both new Plaistow Level areas alongside the four original views. OS benchmark/offset source data is available under the Open Government
Licence; retain Ordnance Survey attribution with the derived height data.

The sections below document the earlier research baseline and prototype.

The author requests terrain for **West Ham and the region within 3 km of its
historic boundaries**. Use the existing 1911 county-borough polygon as the working
boundary, rather than modern Newham, the parliamentary constituency or the much
larger registration district. Source: `/home/jic823/swipe_map/site/data/WestHam_1911.geojson`,
GBHGIS unit **10025904**, `g_year=1911`, `g_status=CB`. This is a working historical
extent; any differences from c1900 have not been audited. Its computed area is
20.23 km²; the borough plus an outward 3,000 m buffer in EPSG:27700 is **108.67 km²**.
This expands the terrain research area, not the detailed factory-building brief.

The author considers pre-2007 terrain a useful approximation: the 1930s changes
matter, but the post-2007 transformation was much larger. Aim for a convincing
landscape, not an exact reconstruction of every historical ground level.

## Confirmed data

[EA dated DTM archive](https://www.data.gov.uk/dataset/8275e71e-1516-42a1-bb0c-4fa73807fe2b/lidar-dtm-time-stamped-tiles)
contains pre-Olympic surveys across this area. **2003 should be the first-choice
candidate**, supplemented by other early dates where necessary. DTM removes
surface objects; it does not undo earthworks, industrial fill or land reclamation.

The current [EA OGC catalogue](https://environment.data.gov.uk/spatialdata/survey-index-files/ogc/features/v1/collections/LIDAR_DTM_Time_Stamped_Extents/items?f=json&bbox=-0.063,51.469,0.096,51.583&limit=10000)
returned all 1,115 matching records, with no omitted pages. Intersecting their
footprints with the buffered borough gives:

| Survey year | Coverage of study area |
| --- | ---: |
| 1999 | 20.88% |
| 2002 | 17.61% |
| **2003** | **92.62%** |
| 2005 | 1.59% |
| 2007 | 91.12% |
| 2012 | 97.07% |

These percentages measure the union of catalogue polygons, not verified valid
height pixels. Overlapping tiles/resolutions are not counted twice. Invalid
source polygon topology is repaired before measuring. The 2003 holdings include
0.5 m and 1 m products, principally 22 February, with other February/November
flights. Point checks confirm 2003 records at the model's Three Mills, Abbey Mills
and City Mills anchors and at approximate Stratford and Forest Gate locations.
See `coverage-summary.json` for their full dates, tiles and survey identifiers.

**Important catalogue correction:** the older ArcGIS `LIDAR_Tiles_Catalogues`
service exposed only 2007/2012 entries in the initial small query. The current
OGC catalogue additionally exposes 1999/2002/2003 coverage. Do not repeat the
initial inference that the centre of the scene has no pre-2007 survey.

The [2022 composite DTM](https://www.data.gov.uk/dataset/01b3ee39-da3f-47b6-83da-dc98e73a461f/lidar-composite-digital-terrain-model-dtm-1m)
is available at 1 m, in metres ODN and British National Grid. A **10 m sampled
GeoTIFF has been downloaded** for the entire study envelope, E534400–545600 /
N176400–189100. It is 1,120 × 1,270 float heights and about 5.7 MB on disk. This
is a comparison/reference surface, not the historical model. The separate
National LIDAR index confirms local 2017–18 and December 2020 surveys. Composite
year is not an assertion that every height was surveyed that year.

**The 2003 rasters are now downloaded and reduced to a working mosaic.** Ten
archives (1.76 GB, kept outside Git/publication) contain the selected 1 m products,
with 0.5 m products for two southern-edge tiles where 1 m was not offered.
The build uses 124 distinct rasters intersecting the study area. At 10 m working
resolution, requiring at least half the source pixels in each cell to be valid,
**91.62% of the study area has usable heights (99.56 km²)**. Missing cells remain
NaN; there is no hidden interpolation across water or missing survey coverage.

The working heightfield is 5.69 MB uncompressed; the compressed research package
including heights, source IDs and valid-pixel support is 3.08 MB. Source date,
resolution and checksums remain available for every contributing raster. Latest
2003 date wins valid overlaps, with finer resolution preferred on equal dates.

Approximate **110 × 110 m sample windows**, not exact site levels, give:

| Sample | 2003 median | Modern median | Median paired difference |
| --- | ---: | ---: | ---: |
| Forest Gate (E540500 N185500) | 11.32 m | 11.30 m | −0.05 m |
| Northeastern high ground (E540500 N187500) | 24.13 m | 24.15 m | approximately 0 m |
| Stadium vicinity (E538000 N184500) | 8.12 m | 13.95 m | +5.65 m |

These are screening observations: modern 10 m WCS samples and older 10 m cell
medians differ in aggregation, and geoid/processing/water effects are not yet
corrected. Their difference is not a precise survey of earthwork volumes. Do not
infer a 1900 surface directly from the 2003 valley levels. The comparison image
shows conspicuous Olympic-site changes alongside much more stable regional relief.

The current downloader endpoint is
`https://environment.data.gov.uk/tiles/collections/survey/search` (POST a GeoJSON
Polygon with `Content-Type: application/geo+json`). Its records contain download
URIs; append `?subscription-key=public`. The bare archive URI returned 404 in this
session; the public-key URI returned the dated ZIP. See `download-search.json`
and `selected-downloads.json`, rather than reconstructing tile IDs manually.

## Reconstruction method

1. Build a pre-2007 DTM mosaic, prioritising 2003; preserve survey-date and
   valid-data masks. Compare the modern extract to locate large later changes.
2. Use the older broad relief directly where historic maps and continued street
   patterns support it, especially the rising ground toward Forest Gate and
   Wanstead. Remove remaining modern transport embankments/earthworks locally.
3. Correct the lower Lea using c1890–1900 spot heights, marsh boundaries, roads,
   photographs and known changes. Restore period channels separately, including
   the pre-Prescott-Cut landscape. Do not use LiDAR water returns as river-bed
   measurements. Keep historic bank crests, marsh floors and water elevations
   separate so tidal animation remains coherent.
4. Do not flatten all land above zero: above sea level and below high tide can
   both be true. Historical streets/industrial yards may already have been raised.
   Retain period fill where justified; archaeological natural deposits are not
   automatically the occupied surface in 1900.
5. Align vertical datums before connecting terrain to the scene. The current
   scene uses an arbitrary local datum (including its tide heights), not ODN.
   Historical OS levels require checking their legend, feet/metres and datum;
   a benchmark is a mark on a structure, not necessarily the adjacent ground.
   [OS publishes Liverpool-to-Newlyn corrections](https://www.ordnancesurvey.co.uk/geodesy-positioning/legacy-data/datum-height-differences).
   Older EA surveys also use differing geoid/transform versions, recorded in the
   inventory. Do not treat an uncorrected subtraction as precise ground change.
6. Publish a cropped/downsampled heightfield with additional detail near the
   rivers; keep full rasters out of `docs/`. Reposition buildings, yards, roads
   and rail grades against the final surface together to avoid buried/floating
   objects. Blend masks rather than creating height steps at survey boundaries.

The [MoLAS–PCA PDZ12 evaluation (2008)](https://archaeologydataservice.ac.uk/catalogue/adsdata/arch-702-1/dissemination/pdf/molas1-40627_1.pdf),
printed p.4 / PDF p.12, records contemporary ground around 6.9 m OD near
Livingstone Road/High Street and 3.4 m toward Union Street, with substantial
ground raising and likely in-situ alluvium around 2–2.5 m OD. These are useful
local constraints, not elevations to impose over the whole marsh. Its
stratigraphic sections can help separate building-period consolidation from
later fill.

## Local research artefacts and reproduction

Everything downloaded is under `reference/topography-research-2026-09-28/`, which
is already excluded from Git/publication:

- `study-area.geojson`: BNG borough boundary and exact 3 km buffer.
- `buffer-archive-index.json`: current EA catalogue response for the full envelope.
- `survey-inventory.csv`, `coverage-summary.json`: filtered products and coverage.
- `west-ham-buffer-modern-dtm-10m.tif`: full-envelope modern comparison grid.
- `terrain-source-review.png`: modern relief alongside 2003 catalogue coverage.
- `sources.json`: URLs, acquisition details and file checksums.
- `tiles-2003/*.zip`: original dated raster packages.
- `early-terrain-2003-10m.f32` and `.npz`: reduced historical-reference surface.
- `early-terrain-2003-10m.json`: source checksums, pixel coverage and sample windows.
- `early-modern-terrain-comparison.png`: old/modern/difference panels.

Rebuild the offline coverage audit and preview:

```sh
MPLCONFIGDIR=/tmp/topography-matplotlib python3 scripts/review_topography_sources.py
MPLCONFIGDIR=/tmp/topography-matplotlib python3 scripts/build_early_terrain.py
```

The scripts check catalogue completeness, raster geometry, source dates, ZIP CRCs
for used rasters, and provenance/coverage masks. Both previews have been visually
inspected. No public scene terrain or tide values changed in this
research pass. EA elevation data is provided under the Open Government Licence;
preserve Environment Agency attribution with derived public assets. Retain
GBHGIS attribution for the existing borough boundary and check its source licence
before publishing the boundary itself.

The author is recording historical map heights with Claude. Leave that
transcription to them; retain original readings, units, sheet/date, position,
spot-height versus benchmark type and uncertain readings. Use those controls for
the next historical adjustment and vertical-datum alignment step.

## Author's spot-height prototype — 28 September 2026

Read `reference/spot-heights/PROTOTYPE.md`, the merged `readings.geojson`, raw
reading notes and `evaluation.json`. The supplied data contains 105 distinct
marks: 84 spots and 21 benchmarks; 53 high, 47 medium and 5 low confidence.
Seven of the eight matched EPFL digit labels agree, but this small matched subset
does not establish the prototype's proposed 90–95% accuracy across all readings.
Within-source confidence and repeated crops are not independent validation.

The reported Liverpool heights imply marsh ground about 1.92–2.35 m, river-wall
levels about 5.00–5.76 m, and the sewer crest reading of 31.6 ft about 9.63 m.
These are unit conversions, not Newlyn elevations or scene y-coordinates. The
prototype's Trinity High Water comparison is not yet independently verified and
must not directly set the tide animation. Its summary says no water levels were
found, while several drain-mark notes remain uncertain (e.g. sh072); preserve
that uncertainty until the marks are checked.

`scripts/prepare_historic_height_controls.py` writes a separate staging GeoJSON
and audit in `reference/topography-research-2026-09-28/historic-controls/`.
It preserves every original property and adds metres in the stated Liverpool
datum, scene horizontal coordinates, and provisional surface review categories.
ODN height and scene y remain null; interpolation is disabled for every point.
Four records explicitly describe low ground; six drain-bank marks need review;
21 benchmark mounting contexts remain unresolved. Other records concern roads,
yards, banks, walls, sewer or unclear surfaces. A wall top must not become a
terrain control for the marsh beside it. Likewise a benchmark on a building or
bridge is not necessarily at ground level.

WGS84-to-BNG coordinate consistency is within 0.011 m, attributable to rounding;
this verifies coordinate handling only, not claimed map accuracy. The notes say
roughly a third of dot positions are estimated. Future records should separate
value confidence, dot/position confidence and observed surface type.

Before scaling, replace the proposed hard 0–40 ft acceptance range with a broad
regional plausibility flag. The earlier northeastern terrain sample is about
24 m (79 ft): a 40 ft cutoff would discard plausible high-ground readings.
Keep original values, uncertain digits, dot locations and source crops available
for review. No prototype source files were modified, no extraction API calls
were made, and the public scene terrain/tides were not recalibrated in this pass.


### Connection and mill review — 1 October 2026

The author supplied nine map crops identifying Abbey Mill (Corn), a Waterworks
River floodgate, City Mills (Chemical), the Marshgate Lane lock/under-bridge route,
Pudding Mill River through St. Thomas’s Mills, the western Bow Back mouth, Old
Ford’s separate lock and side floodgate, and the upper back-river/Channelsea
network. Original crops are retained under `data/maps/lower-lea-region/evidence`.
`connection-review.json` records evidence, route constraints and dated observations.
Source river names are retained. The author's correction distinguishes the Old
Lea from the Navigation and its downstream Waterworks/City Mill branches; do not
rename every nearby reach from proximity alone.

Direct comparison of the cached georeferenced five-foot layer and skeleton survey
now covers five sites (ten native-resolution crops). Reproduce with
`scripts/prepare_lower_lea_map_review.py`; crop metadata includes global tile/pixel
registration, corners and tile/image hashes. Layer dates are c.1848–51 and 1893;
individual sheet margins have not yet been checked. The sparse early survey cannot
establish absence of a later-labelled gate.

- Bow Back's western mouth is open on both map layers. The 2.08 m source gap is
  classified as a mapping seam at a mapped navigation junction, not a proposed gate.
- Old Ford Lock and the side channel appear on both layers. The later sheet labels
  Flood Gates on the lateral route separately from the navigation lock. Two site
  markers are located; neither operating state nor sill is inferred.
- Pudding Mill passes through the St. Thomas’s Mills site. Its 30.36 m separation
  exceeds the original 15 m gap search: an explicit schematic structure route now
  preserves that connection, without carving an open bypass through buildings.
  The author's 1890s poor-flow account and the book's 1908–09 evidence stay distinct.
- Abbey Mill and the divided channel/crossing layout are compared in both layers;
  the mill is distinct from Abbey Mills pumping station. No single solid dam inferred.
- Templemills Bridge has a **Weir** explicitly labelled on the later map. The 1.78 m
  Waterworks source-part seam (5/6) is now a control review, not ordinary continuity.

The viewer includes eleven mill/lock/gate sites, two broader network review areas,
five approximate map-located site markers, three navigation interfaces (including
touching polygons), three provisional tiny ordinary seams, and the separately
confirmed Bow Back navigation-mouth seam. The rejected 1898 Three Mills tide-gate
proposal stays excluded. Geometry contacts are still separate from hydraulic
passage; there are no invented capacities, crest/sill elevations or permanent gate
states. The regional terrain and existing 3D flood solver have not changed.

Next: trace bank-to-bank openings and remaining upstream routes on these full maps,
apply the reviewed network repairs to the derived hydraulic geometry, then add
stage-dependent passage/storage at controls. Channel beds under bridges and mills
must remain separate from road decks/building footprints. Test more/less restricted
openings alongside upstream inflow and downstream tide, retaining dated changes.


### Three Mills through-building connection — 1 October 2026

Author supplied a further map crop and explicitly confirmed the route through the
mill buildings. Added the original to the evidence register. Native cached map
comparison now includes Three Mills in both layers (six sites / twelve crops).
The original river polygons 1 and 2 meet above the mill buildings; Bow Creek part
0-2 resumes below them. The shortest separation from reach 1 is 25.73 m, outside
the earlier 15 m search, explaining why this was not one of the seven flagged gaps.

A second explicit structure route now joins that shared upstream water area to
Bow Creek in the regional review. The Three Mills control group counts once;
source feature boundaries must not create duplicate mill capacities. Its site
marker is located from the georeferenced later map. Both map layouts support the
through-building route, but individual wheel passages, sill heights, gate settings
and discharge remain unresolved. No open bypass or solid building dam is inferred.
This is a schematic network connection, not yet a change to the 3D flood solver.
Data checks verify the upstream contact, downstream part, single control group
and absence of invented bypass/capacity. Browser checks include the Three Mills view.


### Bow Locks, Limehouse Cut and Bow Creek — 1 October 2026

Direct comparison now includes this junction: seven sites / fourteen native crops.
The mapped Navigation and through creek remain separate beside the tidal lock
passages. The early skeleton explicitly shows the Bromley Lock approach farther
south; the later sheet labels Tide Lock and Bromley Lock at distinct positions.
Keep the Limehouse Cut approach dated rather than imposing today's junction on
all epochs. It is not yet a separately traced hydraulic branch in this regional
source inventory.

The Navigation source18 and Bow Creek part0-2 are separated by 15.065 m at the lock,
just outside the automatic 15 m gap search. An explicit schematic lock-passage
route and control constraint now preserve that connection. There are four reviewed
navigation interfaces including this route, and three explicit structure routes
(Pudding Mill, Three Mills and Bow lock). The marker comes from the georeferenced
later map; sill, capacity, gate settings and precise c1900 rebuilding state remain
unresolved. Neither this change nor the mill review changes existing 3D hydraulics.


### Blue six-inch second-edition network review — 1 October 2026

At the author's request, reviewed cached `six-inch-2nd` maps directly. The blue
water fill is better for following the network across the five-foot sheet seams.
Five native-resolution panels, with tile/image hashes and coordinate registration,
are reproducible through `scripts/prepare_lower_lea_six_inch_review.py`. The layer
contains sheets dated within 1888–1913; do not treat it as one 1900 observation.
The northwestern Lea Bridge endpoint remains outside this particular panel review.

The Cut approaches from the southwest and joins the Navigation west of Bow Creek;
this canal junction is separate from the lock passage into the tidal creek. The
Cut still needs its own traced regional branch. The northern overview separates
Old Lea, Waterworks River and the Navigation/Hackney Cut rather than conflating
parallel channels. Waterworks branches farther north and runs east of the Old Lea.

A larger omission is now recorded: upper Channelsea polygons 10 and 11 stop
192.95 m apart beside the Artificial Manure Works. Both the blue map and detailed
five-foot map show the intervening branching corridor, Potter's Ditch and passages
near the works. Trace these, including potentially covered sections, rather than
opening a straight 193 m channel. The small-gap audit alone missed this corridor.

The southern review follows Three Mills' separate downstream water, the Abbey
Creek entry and Bow Creek to the Thames. Blue colour establishes mapped water,
not common water levels, open gates or discharge capacity. Findings and a direct
map-layer link are included in the regional review; existing flood physics remain
unchanged.


## Working regional landscape — 2 October 2026

The regional surface now combines accepted historical ground/street
interpolation with explicitly estimated broad relief. The user is managing
further Opus transcription; landscape construction proceeds from the existing
collection. `scripts/build_regional_landscape.py` creates a 10 m ODN height
field over the existing 49 km² review window. All accepted historical trial
cells are retained exactly. Additional eligible controls anchor their nearest
10 m cell outside that support; shared cells use the median reading.

Outside these anchors, a 100 m Gaussian broad-relief prior from the 2003 terrain
receives a screened harmonic correction with a 350 m decay length. Correction
edges stop at mapped water and reviewed canal/structure exclusions. This avoids
an abrupt height switch at the historical trial boundary while retaining
regional relief farther away. The smoothing and decay distances are modelling
assumptions; estimated areas may retain later fill and cuttings. The Gaussian
prior is broad relief, not independently verified historical ground.

The surface covers 45.2018 km² of land: 16.2041 km² historical interpolation,
0.0164 km² additional control cells, 13.4025 km² estimated land within 350 m
of anchors along dry grid paths, and 15.5788 km² distant or disconnected
modern-relief estimates. Water/structure exclusions occupy 1.1888 km² and
2.6094 km² still lacks source coverage. Missing ground remains NaN; exclusion
boundaries do not establish bank crests, channel beds or hydraulic barriers.

The user accepts reviewed 1848–51 marsh-ground levels as lower-bound estimates
for 1900 where the same land survives, with later development potentially
raising the surface. Keep source date, datum and surface role; review evidenced
excavation or changed channels locally. This policy is recorded in
`data/maps/lower-lea-region/regional-landscape-policy-1900.json`. No 1848 ground
constraints are present in the current input, so none is claimed as applied.

`/lower-lea-landscape.html` displays a 20 m mesh of 219,364 triangles derived
from the working raster. Every complete triangle is checked against mapped
exclusions. The view supports elevation/evidence colours, explicit vertical
exaggeration, true scale, height inspection, keyboard navigation and mobile.
The regional map offers `?elevation=landscape` and `landscape-evidence` modes.
Products and provenance are in `docs/data/lower-lea-region/landscape-1900.json`.

Numerical checks preserve historical values and source gaps, verify solver
boundary/decay behaviour, and independently check every mesh face against
water. Browser checks cover both views, evidence modes, inspection, scale,
keyboard and mobile; screenshots were inspected. This is a working landscape,
not a demonstration of uniform 30 cm accuracy. The detailed scene and flood
solver retain their existing terrain until structures and bank contacts have
been reconciled against the regional surface.


### Marsh prior and new Opus observations — 2 October 2026

The author identifies the 11.2/10.8 ft City Mill marsh readings as ground outside
the bank hatching; the higher 17.4/16.7 ft readings belong to the banks. The
13.9 ft Knobshill Cottage garden is another local surface. The marsh readings
support only about 12 cm northward rise. The initial regional estimate retained
excess modern-relief variation here. Its reviewed field interior now follows
these two ground readings (2.8956–3.01752 m provisional ODN), with a 5 m edge
strip reserved for banks/transitions. This is an interpreted field estimate,
not an observation across every interior cell; evidence class 6 marks it.

The author also specifies about 12 ft historical OD as the default expectation
for marsh without better evidence. The model now uses that prior within the
existing identified marsh footprints, retaining actual observations as stronger
constraints. It does not flatten the whole valley or treat terraces as marsh.
The first scope includes four reviewed low-ground patches and the marsh-ditches
footprint, with a documented perimeter transition. Class 7 marks estimated
areas using this prior; the prior is adjusted by nearby historical anchors.
Further mapped marsh outlines can extend its scope.

An explicit frozen Opus update adds 336 unique observations and reconciles 44
shifted IDs to existing records. Reviewed surface decisions remain authoritative;
one possible duplicate is withheld. Both the 4,508-record source collection and
manifest are captured beside the immutable original snapshot, so ongoing reader
claims do not change a build. Six bank/lane/towpath-margin readings around
Imperial Saw Mill north of High Street have explicit user surface restrictions:
they remain evidence of raised surfaces, excluded from general ground fitting.
The raw source classifications and values remain available.

The audit now contains 4,337 observations and 1,245 usable ground/street controls.
Historical interpolation covers 17.9073 km², up 1.7032 km². Total working land
remains 45.2018 km²; the gain is historical support within that land. Numerical,
source, marsh-prior and browser checks pass. The City Mill marsh preset and
height/evidence views expose the correction. Banks and detailed structures still
require reconciliation before this surface is used by the flood solver.


### Pudding–City field: correction of the adjacent-compartment error — 2 October 2026

The user's subsequent screenshot identified a different field from the one
corrected above. The 11.2/10.8 ft observations are east of City Mill River;
the conspicuous plateau lies west of City Mill, between that river and Pudding
Mill / Old Lea. This western field retained roughly 9–10.6 m provisional ODN
from the 2003 prior. Those heights were not supported by historical ground data.

Five full cached five-foot mosaics were reviewed to identify the open field,
Knobshill Cottage garden and the works farther south. The new
`data/maps/lower-lea-region/pudding-city-marsh-1900.json` records the 96,696 m²
river-bounded footprint, source hashes, native-map southern review limit and
separate garden footprint. The southern cutoff conservatively excludes the
works; it is a modelling limit, not a surveyed bank.

The whole footprint now starts from the author's 12 ft marsh expectation.
Its 868 unconstrained interior cells are fixed at 3.26136 m provisional ODN,
explicitly classed as estimated marsh, not newly observed ground. Seven garden
cells retain the local 13.9 ft level, and 51 bank cells use the existing reviewed
Old Lea east-bank patch and its four bank-margin readings. These raised local
surfaces have their own evidence class. Historical ground/street constraints
still take precedence. The 5 m field-edge strip can transition toward the local
banks without retaining modern infill as a fictitious perimeter ridge.

Six samples across the former plateau now read 3.26136 m. The garden reads
3.84048 m; the reviewed bank estimates range up to 5.27304 m. Numerical checks
preserve all historical raster/control values, validate source hashes, keep
water out of every display face, and test the western field specifically.
Browser checks pass, including the new Pudding–City preset and deep link;
height and evidence screenshots show the broad raised plateau removed.
Distance to historical anchors now excludes estimated constraint cells.
Historical interpolation remains 17.9073 km². The main detailed scene and
flood solver have not adopted this regional surface yet.


## Regional early-marsh substrate — 2 October 2026, late evening

The user's whole-marsh correction supersedes the isolated flat Pudding–City
patch. A selected review of 57 early readings accepted 45 low-lane/ground-margin
proxies and excluded 12 raised/crossing/benchmark comparisons. See
`data/maps/lower-lea-region/marsh-baseline-1848-review.json` for source hashes,
coordinates, original values, roles and confidence; this is not full sheet
transcription. Full analysis, source crops and CSV are published at
`docs/lower-lea-marsh-evidence.html` by `scripts/build_marsh_evidence_report.py`.

Ranges: Hackney/Temple 13.5–15.4 ft, northern Leyton one point at 15.2 ft; Stratford west
10.9–12.7, east 10.5–10.7; northern Mill Meads 7.9–8.6; Abbey marsh 4.4–5.8;
Plaistow west 3.4–4.9, east 4.6–5.7; southern approaches 5.6–6.2. The southern
Mill Meads later 7.7/7.3 ft readings remain valid: do not confuse that compartment
with the lower Abbey/Plaistow marsh to its east. The book's 1805 map and early
industry discussion establish broad historic marsh/development, not exact
boundaries or point heights. Liverpool datum remains inferred.

The regional envelope covers 11.7267 km² at full early weight. Continuous IDW
with 100 m smoothing and 600 m Gaussian distance taper uses all 45 proxies; a 120 m
outer blend is explicitly interpretive. Corrections from modern/non-marsh
terrain cannot enter its interior. Only explicit marsh or independently
reviewed ground can adjust this substrate. Workhouse 29.7 ft and ten unreviewed
premises/embankment-foot controls no longer distort the early marsh estimate.

Later street/yard/shoreline/railway/sewer fits are confined to existing geometry,
with provenance for measured versus interpreted levels. Model outputs preserve
both underlying ground and final surfaces. The original historical TIN remains
an unchanged separate experiment. Some later readings still lack usable
footprints: inventory and optional 3D markers retain these gaps explicitly.
Narrow walls/continuous defences cannot be established by this 10 m raster / 20 m
mesh. No flood integration or valley-wide 30 cm accuracy is claimed.

The initial outer transition was visually too abrupt because fixed historical
TIN cells overrode its partial weights. The final composition explicitly blends
the solved outer surface into adjacent marsh-side ground across that strip
(2.276 km²; evidence class14). It is an estimated transition, not an exact
historical control surface. Numerical checks require adjacent marsh/transition
cells to differ by less than 30 cm and preserve the original source values in
provenance where the displayed boundary surface is blended.

Final validation passed: `scripts/check_regional_landscape.py` and the regional
browser checks through `scripts/review_historic_elevation.py --region-only`.
Maximum adjacent marsh/transition ground difference was 0.0654 m (a modelling
continuity check, not an accuracy estimate). Final example ground levels in the
original feet: Pudding–City (537650,184100)12.02, west neighbour(537300,184100)
11.91, northern Mill Meads(538550,183200)7.95, southern reviewed point(538500,
182850)7.70, Abbey(539200,182900)5.10, western Plaistow(539800,181800)4.30.
Reviewed final browser screenshots for Pudding–City, Mill Meads and Plaistow;
source/evidence report and mobile layouts also passed.
