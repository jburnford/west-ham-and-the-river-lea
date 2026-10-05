// Road bridge structures about 1900: arches, piers, abutments, spandrels, parapets, railings and
// wing walls under and beside the decks recorded in infrastructure.json roadBridges.
// Register: data/maps/road-bridge-forms.json, copied here as bridgeForms (scripts/check_road_bridges.mjs
// fails if the copies differ). Structural families come from the bridge records; spans follow the
// drawn water; rises, ring depths, parapets and every other dimension are estimates.
// The road surface itself (deck setts and footways) stays in infrastructure.js, unchanged.
import { createTriangleBatcher } from './lib/geometry.js';

export const bridgeForms = {
  description:
    'Structural form chosen for each road bridge in docs/data/infrastructure.json roadBridges, about 1900: arches, abutments, piers, parapets or railings, and wing walls. The bridge records (route, width, deck height, style, arch count) are not changed here; this register adds the structure under and beside the deck. docs/road-bridges.js carries an identical copy as bridgeForms, and scripts/check_road_bridges.mjs fails if the two differ.',
  frame:
    'Stations are metres along each bridge route from its first point. Offsets are metres across it, positive on the left (the normal (-uz, ux)). An abutment face lies at station abutment + skew * offset, so skew is the shift of the face per metre across the deck: one number when both faces are parallel, or a pair [first, second abutment] when each face follows its own bank. Heights are scene y metres; the static water surface is y 0.06 and the animated tide reaches y 1.1.',
  sources: [
    {
      id: 'vch',
      citation:
        'Victoria County History, Essex VI, pp. 57-61, as cited in each roadBridges evidence string for the structural family (stone or brick arch, deck).',
      use: 'Structural family only. The text is not held in this repository and was not read for this task; spans, rises, ring depths and parapet forms are estimates.',
    },
    {
      id: 'road-trace-notes',
      citation: 'data/maps/district-road-traces.json notes',
      use: 'Bow Bridge is one granite-faced span completed 1839; St Thomas brick arch count is not established by the written source; High Street bridge names follow the nineteenth-century transposition; the three lane connections are provisional, with deck or culvert unresolved.',
    },
    {
      id: 'os-five-foot',
      citation:
        'OS London five-foot plan, 1893-96 revision, NLS tiles read with scripts/factory_map_sources.py mosaic() at zoom 18 (about 0.4 m per pixel)',
      use: 'Named crossings and the parapet or road edge lines across each river. At this resolution the abutment faces under the deck cannot be read; the plan does show each crossing as one continuous carriageway between buildings.',
    },
    {
      id: 'os-heights',
      citation:
        'data/maps/lower-lea-region/height-observations.opus-2026-10-02.geojson (OS 25-inch, 1893-96 revision, feet above OD Liverpool)',
      use: "Bench marks cut on the Pegs Hole Bridge parapet, at St Michael's Bridge and on the hatched south parapet of the Bow Bridge east approach show masonry parapets there. Spot heights on the crossings are compared with the recorded deck heights in the T12a report; they are not used to change any height. The one exception is Three Mills Bridge, re-levelled by T22 (October 2026) to its OS five-foot spot height (21.2 ft, 4.23 m scene) in data/maps/district-road-traces.json, the prior 2.2 m estimate kept there as priorHeight.",
    },
    {
      id: 'photo-catalogue',
      citation: 'reference/photo-review-2026-10-03/reports/photo-catalogue.md',
      use: 'No archive image shows these bridges, so no elevation detail is copied from a photograph.',
    },
    {
      id: 'drawn-water',
      citation:
        'Water polygons as drawn by docs/app.js (tide, reviewed connections, retained rivers, marsh ditches, river system)',
      use: 'Abutment stations sit at the drawn water edges measured along each route on the centreline and both deck edges (waterEdges below). For the five High Street crossings T12c re-measured the edges after the T13 retrace every 0.05 m along the route and every 0.5 m across the deck (bankEdges lists them every metre) and fitted one straight face line to each bank. They are model measurements, not surveyed abutments.',
    },
  ],
  defaults: {
    springing: 0.5,
    parapetHeight: 1,
    copingHeight: 0.12,
    parapetThickness: 0.45,
    railingHeight: 1.05,
    clearZoneMargin: 2,
    abutmentEndClearance: 0.3,
    evidence:
      'Estimates for every bridge: springing 0.44 m above the static water so the arch feet stand clear of it; masonry parapet 1.0 m plus 0.12 m coping (about 1.1 m above the carriageway, 1.0 m above the footway); railings 1.05 m. Approach fill is not drawn within 2 m of either deck edge between the abutment faces. Arch abutment faces stay at least 0.3 m inside the route ends at both deck edges (abutmentEndClearance), so the arch ring never reaches past the deck; the masonry behind a face may run on under the approach.',
    deckFootway: { inset: 0.9, width: 1.15, base: 0.025, thickness: 0.12, minCarriageway: 1 },
    streetFootway: 1.1,
    approachGrade: 0.12,
    deckEndBlend: 2,
    deckEndFootwayTaper: 6,
    deckEndEvidence:
      'Deck ends (T18, October 2026). Interpretation and estimates; no source in the repository shows the kerb layout or the road levels at the bridge heads. Recorded from the model as drawn before T18: the deck footway box in docs/infrastructure.js (deckFootway: centre inset 0.9 m from the deck edge, 1.15 m wide, 0.025 m above the deck setts, 0.12 m thick, so its top is 0.145 m above the recorded deck height; from T18 the boxes are drawn only where they leave at least minCarriageway, 1 m, of setts between them, so the 2.2 m Three Mills Lane footpath deck, whose two boxes overlapped, is now a plain deck that its path meets flush) and the 1.1 m street footway that scripts/build_infrastructure.py draws beside every street (streetFootway). Rule: within the approach band (half the deck width plus streetFootway either side of the route) the drawn road and footway take the deck road level (deck height less 0.065 m, so the setts meet flush) at each route end and fall at approachGrade (0.12 m per metre, the grade docs/infrastructure.js already used; scripts/build_main_landscape.py still fits the ground to the earlier rule, as BRIDGE_CONE, which only ever lies below this one) along the road, level across it; outside the band the fall is measured from the band edge. Before T18 the fall was measured from the route line in every direction, so the approach sloped 0.12 m per metre across the road and met the level deck 0.26-0.58 m low (T12C_REPORT.md). Within deckEndBlend (2 m) of the deck end the approach is blended (smoothstep) to the deck road level, so the road meets the deck flush where the street is higher as well as lower. The street footway is carried onto the deck footway over deckEndFootwayTaper (6 m): its kerb line draws in from the street carriageway edge to the deck footway kerb, and its surface rises from the street footway level (0.03 m above the road) to the deck footway top. The 6 m taper and the kerb rise are estimates chosen so the footway is continuous.',
  },
  bridges: {
    'bow-bridge': {
      form: 'stone-arch',
      arches: 1,
      abutments: [4.35, 30.5],
      skew: [0.67, 0.21],
      crownDepth: 0.9,
      ringDepth: 0.6,
      abutmentLength: 2.5,
      waterEdges: { centre: [4.2, 30], left: [8.35, 31.25], right: [0.8, 28.65] },
      bankEdges: {
        offsets: [-6, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 6],
        start: [0.8, 0.75, 1.45, 2.15, 2.8, 3.5, 4.2, 4.9, 5.6, 6.25, 6.95, 7.65, 8.35],
        end: [28.65, 29, 29.2, 29.4, 29.6, 29.8, 30, 30.2, 30.4, 30.6, 30.8, 31, 31.25],
      },
      evidence:
        'Documented: one granite-faced span completed 1839 (road-trace notes), stone family (VCH as cited); bench mark on the hatched south parapet of the east approach (OS 25-inch). Mapped: the crossing on the OS five-foot plan; the T13 retrace laid the span on the road axis and read the west and east banks 34 and 10 degrees from square to the road. Measured in the model (T12c, on the T13 span of 32.2 m): the drawn water edges on the deck run at +0.67 m (west bank) and +0.21 m (east bank) per metre across it, 34 and 12 degrees from square to the road (bankEdges). Interpretation: each abutment face follows its own bank (west 0.10 m into the water, east 0.50 m back on the bank at the centreline; the setback is 0.5 m except where the face must stay 0.3 m inside the deck end at a deck edge); the segmental arch splays between the two faces with one crown and springing, 28.9 m along the road at the right deck edge, 26.1 m on the centreline and 23.4 m at the left. The square-ended deck stays on the road axis. Estimated: crown soffit 0.9 m below the deck, springing 0.5 m, ring and parapet dimensions. The 1901-06 rebuilding is not shown.',
      priorAbutments: [3, 29.5],
      priorSkew: 0.4,
      priorWaterEdges: { centre: [2, 29], left: [6.5, 30.5], right: [0, 27.25] },
      priorEvidence:
        'Documented: one granite-faced span completed 1839 (road-trace notes), stone family (VCH as cited); bench mark on the hatched south parapet of the east approach (OS 25-inch). Mapped: the crossing on the OS five-foot plan. Measured in the model: the River Lea crosses the route obliquely, so the abutment faces follow the bank with a skew of 0.4 m per metre. Estimated: one segmental arch of 26.5 m along the road, crown soffit 0.9 m below the deck, springing 0.5 m, ring and parapet dimensions. The 1901-06 rebuilding is not shown.',
      priorNote:
        'Values measured by T12a on the previous span, which T13 (3 October 2026) moved onto the retraced road axis and shortened; they no longer describe this span and are kept for the record only.',
    },
    'pegshole-bridge': {
      form: 'stone-arch',
      arches: 2,
      abutments: [0.5, 15.65],
      skew: [0.03, -0.12],
      pier: 1.8,
      crownDepth: 0.6,
      ringDepth: 0.45,
      abutmentLength: 2.5,
      waterEdges: { centre: [0.95, 15.1], left: [1, 14.5], right: [-0.85, 16.3] },
      bankEdges: {
        offsets: [-6, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 6],
        start: [-0.85, -0.55, 0.05, 0.95, 0.95, 0.95, 0.95, 0.95, 0.95, 0.95, 1, 1, 1],
        end: [16.3, 15.6, 15.5, 15.4, 15.3, 15.2, 15.1, 15, 14.9, 14.8, 14.7, 14.6, 14.5],
      },
      evidence:
        "Documented: stone family and two arches (VCH as cited, in the record). Mapped: Peg's Hole Bridge over the Three Mills Back River on the OS five-foot plan; bench mark on its parapet and a spot height at the bridge crown (OS 25-inch). The T13 retrace read the banks 1 and 19 degrees from square on the OS; the drawn water's east bank is only 7 degrees, and the faces follow the drawn water. Measured in the model (T12c, on the T13 span of 18.1 m): the drawn water edges on the deck run at +0.03 m (west bank) and -0.12 m (east bank) per metre across it, 2 and 7 degrees from square to the road (bankEdges). At the right deck edge (offsets -4.5 to -6 m) a river-system water polygon runs on 0.4-0.85 m beyond the route start under the approach; the face cannot follow it inside the deck. Interpretation: each abutment face follows its own bank (west 0.40 m back on the bank, east 0.50 m back on the bank at the centreline; the setback is 0.5 m except where the face must stay 0.3 m inside the deck end at a deck edge); the arches splay between the two faces with one crown and springing, each 7.1 m along the road at the right deck edge, 6.7 m on the centreline and 6.2 m at the left. The square-ended deck stays on the road axis. Estimated: a 1.8 m river pier with cutwaters on the line midway between the faces, rise, ring and parapet dimensions.",
      priorAbutments: [8, 27],
      priorSkew: 0,
      priorWaterEdges: { centre: [10.75, 24.75], left: [5.75, 29], right: [9.75, 25.5] },
      priorEvidence:
        "Documented: stone family and two arches (VCH as cited, in the record). Mapped: Peg's Hole Bridge over the Three Mills Back River on the OS five-foot plan; bench mark on its parapet and a spot height at the bridge crown (OS 25-inch). Measured in the model: the water widens on the left (south-east) edge, so the abutments are set between the centreline and edge water lines. Estimated: two segmental arches of 8.6 m on a 1.8 m river pier with cutwaters, rise, ring and parapet dimensions.",
      priorNote:
        'Values measured by T12a on the previous span, which T13 (3 October 2026) moved onto the retraced road axis and shortened; they no longer describe this span and are kept for the record only.',
    },
    'st-thomas-bridge': {
      form: 'brick-arch',
      arches: 1,
      abutments: [0.9, 8.25],
      skew: [-0.01, -0.06],
      crownDepth: 0.6,
      ringDepth: 0.35,
      abutmentLength: 2,
      waterEdges: { centre: [1.4, 7.8], left: [-3.65, 12.5], right: [1.4, 8.15] },
      bankEdges: {
        offsets: [-6, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 6],
        start: [1.4, 1.4, 1.4, 1.4, 1.4, 1.4, 1.4, 1.35, 1.35, 1.35, 1.35, 1.35, -3.65],
        end: [8.15, 8.1, 8.05, 8, 7.95, 7.85, 7.8, 7.75, 7.7, 7.65, 7.6, 7.55, 12.5],
      },
      evidence:
        "Documented: brick family (VCH as cited); the arch count is not established by the written source (road-trace notes). Mapped: Sir Thomas D'Akers Bridge over the western Waterworks arm (OS five-foot plan); the T13 retrace read the banks 1 and 3 degrees from square. Measured in the model (T12c, on the T13 span of 8.9 m): the drawn water edges on the deck run at -0.01 m (west bank) and -0.06 m (east bank) per metre across it, 1 and 3 degrees from square to the road (bankEdges). Along the left deck edge (offsets 5.5-6 m) the tide water polygon runs on beyond both route ends under the approaches (its dry gap for the road ends 5.0-5.5 m left of the centreline, short of the 6 m deck edge); the faces cannot follow it inside the deck. Interpretation: each abutment face follows its own bank (west 0.50 m back on the bank, east 0.45 m back on the bank at the centreline; the setback is 0.5 m except where the face must stay 0.3 m inside the deck end at a deck edge); the segmental arch splays between the two faces with one crown and springing, 7.6 m along the road at the right deck edge, 7.3 m on the centreline and 7.0 m at the left. The square-ended deck stays on the road axis. Estimated: one segmental brick arch with three brick rings, rise and parapet dimensions; a brick parapet with stone coping.",
      priorAbutments: [7, 15.75],
      priorSkew: 0,
      priorWaterEdges: { centre: [8.5, 15], left: [3, 19.25], right: [8.75, 15.75] },
      priorEvidence:
        "Documented: brick family (VCH as cited); the arch count is not established by the written source (road-trace notes). Mapped: Sir Thomas D'Akers Bridge over the western Waterworks arm (OS five-foot plan). Measured in the model: centreline water 8.5-15 m; the drawn water flares on the left edge and is left partly under the abutment there. Estimated: one segmental brick arch of 8.75 m with three brick rings, rise and parapet dimensions; a brick parapet with stone coping.",
      priorNote:
        'Values measured by T12a on the previous span, which T13 (3 October 2026) moved onto the retraced road axis and shortened; they no longer describe this span and are kept for the record only.',
    },
    'st-michaels-bridge': {
      form: 'stone-arch',
      arches: 1,
      abutments: [1.4, 14.15],
      skew: [-0.17, -0.14],
      crownDepth: 0.7,
      ringDepth: 0.5,
      abutmentLength: 2.5,
      waterEdges: { centre: [1.9, 13.65], left: [-4.15, 17.85], right: [2.9, 14.5] },
      bankEdges: {
        offsets: [-6, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 6],
        start: [2.9, 2.75, 2.55, 2.4, 2.25, 2.05, 1.9, 1.75, 1.55, 1.4, 1.25, 1.05, -4.15],
        end: [14.5, 14.4, 14.25, 14.1, 13.95, 13.8, 13.65, 13.55, 13.4, 13.25, 13.1, 12.95, 17.85],
      },
      evidence:
        "Documented: stone family (VCH as cited). Mapped: St Michael's Bridge over the eastern Waterworks arm (OS five-foot plan) with a bench mark at the bridge (OS 25-inch); the T13 retrace read the banks 9 and 8 degrees from square. Measured in the model (T12c, on the T13 span of 15.3 m): the drawn water edges on the deck run at -0.17 m (west bank) and -0.14 m (east bank) per metre across it, 10 and 8 degrees from square to the road (bankEdges). Along the left deck edge (offsets 5.5-6 m on the west bank, 6 m on the east) the tide water polygon runs on beyond the route ends under the approaches (its dry gap for the road ends 5.25 m left of the centreline at the west end, short of the 6 m deck edge); the faces cannot follow it inside the deck. Interpretation: each abutment face follows its own bank, 0.5 m back on the bank; the segmental arch splays between the two faces with one crown and springing, 12.6 m along the road at the right deck edge, 12.8 m on the centreline and 12.9 m at the left. The square-ended deck stays on the road axis. Estimated: rise, ring and parapet dimensions.",
      priorAbutments: [8, 20.75],
      priorSkew: -0.18,
      priorWaterEdges: { centre: [8.5, 20.25], left: [7.25, 19.25], right: [9.5, 21.25] },
      priorEvidence:
        "Documented: stone family (VCH as cited). Mapped: St Michael's Bridge over the eastern Waterworks arm (OS five-foot plan) with a bench mark at the bridge (OS 25-inch). Measured in the model: both drawn banks cross the route at the same oblique angle, skew -0.18 m per metre. Estimated: one segmental arch of 12.75 m, rise, ring and parapet dimensions.",
      priorNote:
        'Values measured by T12a on the previous span, which T13 (3 October 2026) moved onto the retraced road axis and shortened; they no longer describe this span and are kept for the record only.',
    },
    'channelsea-high-street-bridge': {
      form: 'stone-arch',
      arches: 1,
      abutments: [2.55, 13.9],
      skew: [-0.32, -0.03],
      crownDepth: 0.65,
      ringDepth: 0.45,
      abutmentLength: 2.5,
      waterEdges: { centre: [3.05, 13.4], left: [-4.3, 18.75], right: [5, 13.6] },
      bankEdges: {
        offsets: [-6, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 6],
        start: [5, 4.65, 4.35, 4, 3.7, 3.35, 3.05, 2.75, 2.4, 2.1, -3.5, -3.8, -4.3],
        end: [13.6, 13.55, 13.55, 13.5, 13.45, 13.45, 13.4, 13.4, 13.35, 18.3, 18.3, 18.25, 18.75],
      },
      evidence:
        'Documented: stone family (VCH as cited). Mapped: Channel Sea Bridge on the OS five-foot plan, with tramway spot heights on it (OS 25-inch); the T13 retrace read the banks 18 and 2 degrees from square. Measured in the model (T12c, on the T13 span of 14.4 m): the drawn water edges on the deck run at -0.32 m (west bank) and -0.03 m (east bank) per metre across it, 18 and 2 degrees from square to the road (bankEdges). On the left 3 m of the deck (offsets 3-6 m) the tide water polygon runs on beyond both route ends under the approaches: its dry gap for the road reaches only 2.25-3.5 m left of the centreline (the pre-T13 road lay 3.6-6.3 m to the right, which suggests the gap was cut for it). The faces cannot follow that water inside the deck. Interpretation: each abutment face follows its own bank, 0.5 m back on the bank; the segmental arch splays between the two faces with one crown and springing, 9.6 m along the road at the right deck edge, 11.4 m on the centreline and 13.1 m at the left. The square-ended deck stays on the road axis. Estimated: rise, ring and parapet dimensions.',
      priorAbutments: [20.75, 31],
      priorSkew: -0.3,
      priorWaterEdges: { centre: [21.25, 30.25], left: [18.75, 29.75], right: [23.25, 32.5] },
      priorEvidence:
        'Documented: stone family (VCH as cited). Mapped: Channel Sea Bridge on the OS five-foot plan, with tramway spot heights on it (OS 25-inch). Measured in the model: the Channelsea crosses the route obliquely, skew -0.3 m per metre. Estimated: one segmental arch of 10.25 m, rise, ring and parapet dimensions. The long route either side of the water is drawn as walled approach, as before.',
      priorNote:
        'Values measured by T12a on the previous span, which T13 (3 October 2026) moved onto the retraced road axis and shortened; they no longer describe this span and are kept for the record only.',
    },
    'three-mills-lea-bridge': {
      form: 'iron-deck',
      abutments: [23.75, 38.5],
      girderDepth: 0.8,
      abutmentLength: 1.5,
      waterEdges: { centre: [24.25, 38], left: [24.25, 37], right: [24.25, 38.25] },
      evidence:
        "Recorded style deck (the record's archCount 1 is retained in infrastructure.json but a deck has no arch). Mapped: Three Mills Bridge over the River Lea on the OS five-foot plan, with a bench mark at its west abutment (OS 25-inch). Measured in the model: water 24.25-38 m on the route. Estimated: wrought-iron girders 0.8 m deep on brick abutments, timber deck, iron railings; walled approaches on the land either side.",
    },
    'abbey-mill-crossing': {
      form: 'slab-deck',
      abutments: [19.5, 28],
      abutmentLength: 1.2,
      waterEdges: { centre: [24.5, 27.5], left: [22.25, 27.5], right: [20, 25.75] },
      evidence:
        'The record has no structural style; its 0.4 m slab and brick parapets are kept as drawn before, because the T3 landscape holds the bank 0.1 m below that slab. Measured in the model: the two channel cuts reach 20-27.5 m on the route. Added estimate: brick abutments at the water edges. Construction remains interpreted, as the record says.',
    },
    'marshgate-lane-connection-0': {
      form: 'timber-deck',
      provisional: true,
      abutments: [7, 18.5],
      beamDepth: 0.35,
      abutmentLength: 1.2,
      waterEdges: { centre: [7.7, 15.55], left: [7.15, 18.25], right: [8.15, 15.15] },
      evidence:
        'Provisional connection (record): deck versus culvert unresolved and not a documented named bridge. Drawn as the plainest reading, a timber deck on timber beams and brick abutments at the drawn water edges, with timber railings. All dimensions estimated. T18 (October 2026): the span moved with the Marshgate Lane retrace onto the printed lane (same stations along the lane). Measured in the model on the new span every 0.05 m: the GIS channel (docs/data/ground-plan.json rivers) crosses at 7.7-15.55 m on the centreline, 8.15-15.15 m on the right edge and 7.15-18.25 m on the left (east) edge, where the river along the east side of the lane reaches under the deck; the far abutment is moved from 16.0 to 18.5 m so that the walled approach does not stand in it. The tide shelf polygon in docs/data/river-network.json also reaches under the left edge from 2.0 m; it was cut for the prior lane and is left to a river-network rebuild (T18_REPORT.md).',
      priorAbutments: [7, 16],
      priorWaterEdges: { centre: [7.75, 15.25], left: [8, 17.25], right: [7.25, 13.5] },
      priorEvidence:
        'Provisional connection (record): deck versus culvert unresolved and not a documented named bridge. Drawn as the plainest reading, a timber deck on timber beams and brick abutments at the drawn water edges, with timber railings. All dimensions estimated.',
      priorNote:
        'Abutments and water edges measured on the prior span, which T18 (4 October 2026) moved with the Marshgate Lane retrace; kept for the record only.',
    },
    'hunts-lane-connection-0': {
      form: 'iron-deck',
      provisional: true,
      abutments: [2.75, 19.25],
      girderDepth: 0.6,
      abutmentLength: 1.2,
      waterEdges: { centre: [3.25, 18.75], left: [3.75, 20.5], right: [2.25, 17.25] },
      evidence:
        "Provisional Cook's Road connection (record): deck versus culvert unresolved. The drawn water is 15.5 m wide on the route, too long for plain timber beams without river trestles, so iron girders on brick abutments are drawn, with iron railings. All dimensions estimated.",
    },
    'three-mills-lane-beside-distillery-connection-0': {
      form: 'timber-deck',
      provisional: true,
      abutments: [7.5, 11.93],
      beamDepth: 0.3,
      abutmentLength: 1,
      waterEdges: { centre: [15.75, null], left: [16, null], right: [8, null] },
      evidence:
        'Provisional footpath deck or culvert (record). The drawn water reaches the route only on its right edge from 8 m and runs on beyond the route end, so the second abutment is put at the route end (its face 1 m inside it). Timber deck, beams and railings on brick abutments; all dimensions estimated.',
    },
  },
};

const ARCH_FORMS = new Set(['stone-arch', 'brick-arch']);

// Stations along a polyline route; positions at (station, offset), offset positive on the left.
export function routeFrame(route) {
  const segments = [];
  let length = 0;
  for (let i = 1; i < route.length; i++) {
    const a = route[i - 1],
      b = route[i],
      l = Math.hypot(b[0] - a[0], b[1] - a[1]);
    segments.push({ a, s0: length, length: l, ux: (b[0] - a[0]) / l, uz: (b[1] - a[1]) / l });
    length += l;
  }
  const segmentAt = (s) => segments.find((g) => s <= g.s0 + g.length) || segments.at(-1);
  // Beyond either end the first or last segment is extended.
  const at = (s, v = 0) => {
    const g = s < 0 ? segments[0] : segmentAt(s),
      d = s - g.s0;
    return [g.a[0] + g.ux * d - g.uz * v, g.a[1] + g.uz * d + g.ux * v];
  };
  const tangent = (s) => {
    const g = s < 0 ? segments[0] : segmentAt(s);
    return [g.ux, g.uz];
  };
  // Station and offset of a plan point, from the nearest segment.
  const project = (x, z) => {
    let best = null;
    segments.forEach((g, i) => {
      const dx = x - g.a[0],
        dz = z - g.a[1];
      // Interior segment ends are clamped; the first and last segments run on beyond the route.
      let t = dx * g.ux + dz * g.uz;
      if (i > 0) t = Math.max(0, t);
      if (i < segments.length - 1) t = Math.min(g.length, t);
      const dist = Math.hypot(dx - g.ux * t, dz - g.uz * t);
      if (!best || dist < best.dist) best = { s: g.s0 + t, v: -dx * g.uz + dz * g.ux, dist };
    });
    return best;
  };
  return { segments, length, at, tangent, project };
}

// Plan layout of one bridge: abutment faces, arches and piers, and the levels that follow from
// the record and the form. Each abutment face is a straight line across the deck at station
// abutment + skew * offset; skew is one number (both faces parallel) or one per abutment, so each
// face can follow its own bank. Between two faces that are not parallel the arch barrel splays:
// at every offset it is a segmental arch from face to face with the same springing and crown, so
// its span varies across the deck. section(v) gives the arches and piers at offset v.
export function bridgeLayout(bridge, form, defaults = bridgeForms.defaults) {
  const frame = routeFrame(bridge.route),
    width = bridge.width,
    height = bridge.height,
    half = width / 2,
    skews = Array.isArray(form.skew) ? [...form.skew] : [form.skew || 0, form.skew || 0],
    abutmentLength = form.abutmentLength ?? 1.2,
    arch = ARCH_FORMS.has(form.form);
  let [a0, a1] = form.abutments;
  // Deck abutment bodies stay under the recorded deck. Arch abutment faces stay inside the route at
  // both deck edges, by abutmentEndClearance; the masonry behind a face may run on under the
  // approach, where the end closure and the approach fill close it.
  const keep = (k) => (arch ? (defaults.abutmentEndClearance ?? 0) : abutmentLength) + Math.abs(k) * half;
  a0 = Math.max(a0, keep(skews[0]));
  a1 = Math.min(a1, frame.length - keep(skews[1]));
  const face = (i, v) => (i ? a1 + skews[1] * v : a0 + skews[0] * v);
  const layout = {
    bridge,
    form,
    frame,
    width,
    half,
    height,
    skews,
    abutmentLength,
    a0,
    a1,
    face,
    arches: [],
    piers: [],
  };
  // Inside the opening between the two faces, at station s and offset v.
  layout.between = (s, v) => s > face(0, v) && s < face(1, v);
  if (arch) {
    const n = form.arches,
      pier = n > 1 ? form.pier : 0,
      springing = form.springing ?? defaults.springing,
      crown = height - form.crownDepth,
      rise = crown - springing;
    const section = (v) => {
      const f0 = face(0, v),
        f1 = face(1, v),
        span = (f1 - f0 - (n - 1) * pier) / n,
        radius = (span * span) / 4 / rise / 2 + rise / 2,
        arches = [],
        piers = [];
      for (let i = 0; i < n; i++) {
        const from = f0 + i * (span + pier);
        arches.push({ from, to: from + span, mid: from + span / 2, span, radius });
        if (i) piers.push({ from: from - pier, to: from });
      }
      return { v, f0, f1, span, radius, arches, piers };
    };
    const centre = section(0);
    Object.assign(layout, {
      section,
      arches: centre.arches,
      piers: centre.piers,
      span: centre.span,
      radius: centre.radius,
      // Arch spans at the right and left deck edges.
      edgeSpans: [section(-half).span, section(half).span],
      springing,
      crown,
      rise,
      ringDepth: form.ringDepth,
    });
    // Soffit height at station s under an arch taken from section(v).
    layout.soffit = (a, s) =>
      springing + Math.sqrt(Math.max(0, a.radius * a.radius - (s - a.mid) ** 2)) - (a.radius - rise);
  } else {
    const depth = form.form === 'iron-deck' ? form.girderDepth : form.form === 'timber-deck' ? form.beamDepth : 0;
    layout.deckUnderside = form.form === 'slab-deck' ? height - 0.4 : height - 0.12 - depth;
    layout.span = a1 - a0;
  }
  return layout;
}

// Plan test for the space between the abutment faces, within a margin either side of the deck.
// Approach fill must not be drawn there.
export function bridgeClearance(bridges, forms = bridgeForms) {
  const margin = forms.defaults.clearZoneMargin;
  const zones = bridges
    .filter((b) => forms.bridges[b.id])
    .map((b) => {
      const layout = bridgeLayout(b, forms.bridges[b.id], forms.defaults),
        reach = b.width / 2 + margin,
        xs = b.route.map((p) => p[0]),
        zs = b.route.map((p) => p[1]),
        pad = reach + Math.max(...layout.skews.map(Math.abs)) * reach;
      return {
        layout,
        reach,
        box: [Math.min(...xs) - pad, Math.min(...zs) - pad, Math.max(...xs) + pad, Math.max(...zs) + pad],
      };
    });
  const near = (x0, z0, x1, z1) =>
    zones.filter(
      (q) =>
        Math.max(x0, x1) >= q.box[0] &&
        Math.min(x0, x1) <= q.box[2] &&
        Math.max(z0, z1) >= q.box[1] &&
        Math.min(z0, z1) <= q.box[3]
    );
  // A skewed face line, carried on past a deck edge, can cross the route end; the zone stops there,
  // since beyond the route end is the approach, whose fill must stay.
  const insideZone = (q, x, z) => {
    const p = q.layout.frame.project(x, z);
    return p.s > 0 && p.s < q.layout.frame.length && q.layout.between(p.s, p.v) && Math.abs(p.v) <= q.reach;
  };
  return {
    zones,
    inside: (x, z) => near(x, z, x, z).some((q) => insideZone(q, x, z)),
    // Pieces of the edge a-b ([x, y, z] points) that lie outside every clear zone.
    outside(a, b) {
      const candidates = near(a[0], a[2], b[0], b[2]);
      if (!candidates.length) return [[a, b]];
      const n = Math.max(1, Math.ceil(Math.hypot(b[0] - a[0], b[2] - a[2]) / 0.25)),
        lerp = (t) => a.map((v, i) => v + (b[i] - v) * t),
        runs = [];
      let start = null;
      for (let i = 0; i < n; i++) {
        const m = lerp((i + 0.5) / n),
          out = !candidates.some((q) => insideZone(q, m[0], m[2]));
        if (out && start === null) start = i;
        if (!out && start !== null) {
          runs.push([lerp(start / n), lerp(i / n)]);
          start = null;
        }
      }
      if (start !== null) runs.push([lerp(start / n), b]);
      return runs;
    },
  };
}

// docs/infrastructure.js draws street triangles this far above ground().
const ROAD_OFFSET = 0.065;

// The drawn road level near the decks (deckEndEvidence in the register): docs/infrastructure.js
// ground() and docs/tram-rails.js roadGround() pass their street level through this, so the road,
// its footways and the rails meet each deck flush. Distance is measured from the deck rectangle
// (route ends, and half the deck width plus the street footway either side), not from the route
// line, so the approach is level across the road at the deck end and falls along it.
export function deckEndLevel(bridges, defaults = bridgeForms.defaults) {
  const grade = defaults.approachGrade,
    blend = defaults.deckEndBlend,
    items = bridges.map((b) => {
      const frame = routeFrame(b.route),
        band = b.width / 2 + defaults.streetFootway,
        deck = b.height - ROAD_OFFSET,
        // Beyond this the fall has reached 5 m below datum, under anything drawn.
        reach = band + (deck + 5) / grade,
        xs = b.route.map((p) => p[0]),
        zs = b.route.map((p) => p[1]);
      return {
        frame,
        band,
        deck,
        box: [Math.min(...xs) - reach, Math.min(...zs) - reach, Math.max(...xs) + reach, Math.max(...zs) + reach],
      };
    });
  return (x, z, street) => {
    let h = street;
    for (const q of items) {
      if (x < q.box[0] || x > q.box[2] || z < q.box[1] || z > q.box[3]) continue;
      const p = q.frame.project(x, z),
        d = Math.hypot(Math.max(0, -p.s, p.s - q.frame.length), Math.max(0, Math.abs(p.v) - q.band));
      h = Math.max(h, q.deck - grade * d);
      if (d < blend) {
        const t = d / blend;
        h = q.deck + (h - q.deck) * t * t * (3 - 2 * t);
      }
    }
    return h;
  };
}
export function roadBridges({ THREE, scene, materials: m, bridges, level, waterLevel, collect = false }) {
  const batch = createTriangleBatcher(),
    defaults = bridgeForms.defaults,
    parts = collect ? [] : null,
    review = [];
  let tag = null;
  const record = (a, b, c) => {
    if (!parts) return;
    let entry = parts.at(-1);
    if (!entry || entry.bridge !== tag.bridge || entry.part !== tag.part)
      parts.push((entry = { ...tag, positions: [] }));
    entry.positions.push(...a, ...b, ...c);
  };
  // A planar polygon (3 or 4 [x, y, z] points) wound to face along `normal`; metre-scale UVs on the
  // face plane unless given.
  function face(material, points, normal, uv) {
    const [p0, p1, p2] = points,
      e1 = [p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]],
      e2 = [p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2]],
      cross = [e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2], e1[0] * e2[1] - e1[1] * e2[0]];
    let pts = points,
      uvs = uv;
    if (cross[0] * normal[0] + cross[1] * normal[1] + cross[2] * normal[2] < 0) {
      pts = [...points].reverse();
      uvs = uv && [...uv].reverse();
    }
    if (!uvs) {
      const flat = Math.abs(normal[1]) > 0.7,
        tl = Math.hypot(normal[2], normal[0]) || 1,
        t = [normal[2] / tl, 0, -normal[0] / tl];
      uvs = pts.map((p) => (flat ? [p[0], p[2]] : [p[0] * t[0] + p[2] * t[2], p[1]]));
    }
    batch.triangle(material, pts[0], pts[1], pts[2], [uvs[0], uvs[1], uvs[2]]);
    record(pts[0], pts[1], pts[2]);
    if (pts.length === 4) {
      batch.triangle(material, pts[0], pts[2], pts[3], [uvs[0], uvs[2], uvs[3]]);
      record(pts[0], pts[2], pts[3]);
    }
  }
  // Box from plan corners: c is [x, z] centre, u the [ux, uz] long axis; y0 to y1. No bottom face.
  function block(material, c, u, length, width, y0, y1, bottom = false) {
    if (y1 - y0 < 1e-4 || length < 1e-4) return;
    const n = [-u[1], u[0]],
      corner = (i, j, y) => [
        c[0] + (u[0] * length * i) / 2 + (n[0] * width * j) / 2,
        y,
        c[1] + (u[1] * length * i) / 2 + (n[1] * width * j) / 2,
      ];
    const sides = [
      [
        [1, -1],
        [1, 1],
        [u[0], 0, u[1]],
      ],
      [
        [-1, 1],
        [-1, -1],
        [-u[0], 0, -u[1]],
      ],
      [
        [1, 1],
        [-1, 1],
        [n[0], 0, n[1]],
      ],
      [
        [-1, -1],
        [1, -1],
        [-n[0], 0, -n[1]],
      ],
    ];
    for (const [[i0, j0], [i1, j1], normal] of sides)
      face(material, [corner(i0, j0, y0), corner(i1, j1, y0), corner(i1, j1, y1), corner(i0, j0, y1)], normal);
    face(material, [corner(-1, -1, y1), corner(1, -1, y1), corner(1, 1, y1), corner(-1, 1, y1)], [0, 1, 0]);
    if (bottom)
      face(material, [corner(-1, -1, y0), corner(1, -1, y0), corner(1, 1, y0), corner(-1, 1, y0)], [0, -1, 0]);
  }
  // Vertical wall face through plan columns [x, z, bottom, top], facing `side` (+1 left of travel).
  function wallFace(material, columns, side) {
    for (let i = 1; i < columns.length; i++) {
      const [ax, az, ab, at] = columns[i - 1],
        [bx, bz, bb, bt] = columns[i];
      if (at - ab < 1e-4 && bt - bb < 1e-4) continue;
      const l = Math.hypot(bx - ax, bz - az);
      if (l < 1e-5) continue;
      const normal = [(-(bz - az) / l) * side, 0, ((bx - ax) / l) * side];
      face(
        material,
        [
          [ax, ab, az],
          [bx, bb, bz],
          [bx, Math.max(bb, bt), bz],
          [ax, Math.max(ab, at), az],
        ],
        normal
      );
    }
  }
  const lowest = (points) => Math.min(...points.map(([x, z]) => level(x, z)));

  for (const bridge of bridges) {
    const form = bridgeForms.bridges[bridge.id];
    if (!form) continue;
    const L = bridgeLayout(bridge, form, defaults),
      { frame, width: W, height: h, skews, a0, a1, abutmentLength: lab, face: faceAt } = L,
      half = W / 2,
      arch = ARCH_FORMS.has(form.form),
      body = form.form === 'brick-arch' ? m.brick : arch ? m.stone : m.brick,
      // Plan points in route stations and offsets.
      p3 = (s, v, y) => {
        const [x, z] = frame.at(s, v);
        return [x, y, z];
      },
      tangent = frame.tangent(frame.length / 2),
      u3 = [tangent[0], 0, tangent[1]];
    const set = (part) => (tag = { bridge: bridge.id, part });
    // Footing: below the lower of the drawn bed and the water, under a face line (station at offset v).
    const footing = (line) =>
      Math.min(
        waterLevel,
        lowest(
          [-half, -half / 2, 0, half / 2, half].flatMap((v) => {
            const s = line(v);
            return [frame.at(s, v), frame.at(s + 0.5, v), frame.at(s - 0.5, v)];
          })
        )
      ) - 0.3;
    const foot0 = footing((v) => faceAt(0, v)),
      foot1 = footing((v) => faceAt(1, v));
    const pierFoot = arch
      ? L.piers.map((p, i) =>
          footing((v) => {
            const q = L.section(v).piers[i];
            return (q.from + q.to) / 2;
          })
        )
      : [];
    const info = {
      id: bridge.id,
      form: form.form,
      provisional: Boolean(form.provisional),
      abutments: [+a0.toFixed(2), +a1.toFixed(2)],
      skews: skews.map((k) => +k.toFixed(3)),
      clearSpan: +(a1 - a0 - L.piers.reduce((s, p) => s + p.to - p.from, 0)).toFixed(2),
    };

    if (arch) {
      const springing = L.springing,
        rows = Math.max(2, Math.ceil(Math.abs(skews[1] - skews[0]) * W)),
        sections = Array.from({ length: rows + 1 }, (_, r) => L.section(-half + (W * r) / rows));
      // Soffit: each arch barrel from face to face, in rows across the deck. Where the two faces are
      // not parallel the span changes from row to row and the barrel splays.
      set('arch');
      L.arches.forEach((_, i) => {
        const n = Math.max(12, Math.ceil(Math.max(...sections.map((q) => q.arches[i].span)) / 0.5));
        const grid = sections.map((q) => {
          const a = q.arches[i];
          let arc = 0,
            last = null;
          return Array.from({ length: n + 1 }, (_, j) => {
            const s = a.from + ((a.to - a.from) * j) / n,
              y = L.soffit(a, s);
            if (last) arc += Math.hypot(s - last[0], y - last[1]);
            last = [s, y];
            return { p: p3(s, q.v, y), uv: [arc, q.v] };
          });
        });
        for (let r = 0; r < rows; r++)
          for (let j = 0; j < n; j++) {
            const c = [grid[r][j], grid[r][j + 1], grid[r + 1][j + 1], grid[r + 1][j]];
            face(
              body,
              c.map((q) => q.p),
              [0, -1, 0],
              c.map((q) => q.uv)
            );
          }
      });
      // Abutment faces below the springing, each along its own bank, and river piers with cutwaters.
      set('abutment');
      for (const [i, foot, dir] of [
        [0, foot0, 1],
        [1, foot1, -1],
      ]) {
        const s0 = faceAt(i, -half),
          s1 = faceAt(i, half);
        face(
          body,
          [p3(s0, -half, foot), p3(s1, half, foot), p3(s1, half, springing), p3(s0, -half, springing)],
          [u3[0] * dir, 0, u3[2] * dir]
        );
      }
      const right = L.section(-half),
        left = L.section(half);
      L.piers.forEach((_, i) => {
        const foot = pierFoot[i],
          pr = right.piers[i],
          pl = left.piers[i];
        set('pier');
        for (const [key, dir] of [
          ['from', -1],
          ['to', 1],
        ])
          face(
            body,
            [
              p3(pr[key], -half, foot),
              p3(pl[key], half, foot),
              p3(pl[key], half, springing),
              p3(pr[key], -half, springing),
            ],
            [u3[0] * dir, 0, u3[2] * dir]
          );
        set('cutwater');
        const top = springing + 0.4,
          // Shift of the pier centre line per metre across the deck.
          pierSkew = ((pl.from + pl.to) / 2 - (pr.from + pr.to) / 2) / W;
        for (const side of [-1, 1]) {
          const p = side > 0 ? pl : pr,
            v0 = side * half,
            mid = (p.from + p.to) / 2,
            noseS = mid + pierSkew * side,
            nose = side * (half + 1.0),
            outward = [-u3[2] * side, 0, u3[0] * side];
          for (const s of [p.from, p.to]) {
            const dir = s === p.from ? -1 : 1,
              normal = [outward[0] + u3[0] * dir, 0, outward[2] + u3[2] * dir];
            face(body, [p3(s, v0, foot), p3(noseS, nose, foot), p3(noseS, nose, top), p3(s, v0, top)], normal);
            face(body, [p3(s, v0, top), p3(noseS, nose, top), p3(mid, v0, top + 0.6)], [normal[0], 1, normal[2]]);
          }
        }
      });
      // Spandrel walls on both faces, from the soffit (or footing, or ground on the approaches) up
      // to the deck, in route stations so the walls end exactly at the route ends.
      for (const side of [-1, 1]) {
        const v = side * half,
          q = side > 0 ? left : right,
          kinds = [],
          end = frame.length;
        const cuts = [0, q.f0 - lab, q.f0, ...q.arches.flatMap((a) => [a.from, a.to]), q.f1, q.f1 + lab, end];
        const edges = [...new Set(cuts.map((x) => Math.min(end, Math.max(0, x))))].sort((p, r) => p - r);
        for (let i = 1; i < edges.length; i++) kinds.push([edges[i - 1], edges[i]]);
        for (const [from, to] of kinds) {
          if (to - from < 1e-4) continue;
          const mid = (from + to) / 2,
            archHere = q.arches.find((a) => mid > a.from && mid < a.to),
            pierHere = q.piers.findIndex((p) => mid > p.from && mid < p.to),
            abutHere = mid >= q.f0 - lab && mid <= q.f1 + lab;
          // The wall over a pier or abutment is that pier's or abutment's side face.
          set(archHere ? 'spandrel' : pierHere >= 0 ? 'pier' : abutHere ? 'abutment' : 'approach-wall');
          const n = archHere ? Math.max(12, Math.ceil((to - from) / 0.5)) : Math.max(1, Math.ceil((to - from) / 1));
          const columns = [];
          for (let j = 0; j <= n; j++) {
            const s = from + ((to - from) * j) / n,
              [x, z] = frame.at(s, v);
            const bottom = archHere
              ? L.soffit(archHere, s)
              : pierHere >= 0
                ? pierFoot[pierHere]
                : abutHere
                  ? mid < q.f0
                    ? foot0
                    : foot1
                  : Math.min(h, level(x, z) - 0.4);
            columns.push([x, z, bottom, h + 0.02]);
          }
          wallFace(body, columns, side);
        }
        // Projecting arch ring (archivolt) on the face; its extrados is kept within the route.
        set('ring');
        const proud = side * (half + 0.05);
        for (const a of q.arches) {
          const n = Math.max(12, Math.ceil((a.to - a.from) / 0.5)),
            centreY = springing - (a.radius - L.rise),
            outer = (s) => {
              const dx = s - a.mid,
                y = L.soffit(a, s) - centreY,
                r = Math.hypot(dx, y);
              return [
                Math.min(end, Math.max(0, a.mid + (dx * (r + L.ringDepth)) / r)),
                centreY + (y * (r + L.ringDepth)) / r,
              ];
            };
          for (let j = 0; j < n; j++) {
            const sa0 = a.from + ((a.to - a.from) * j) / n,
              sb0 = a.from + ((a.to - a.from) * (j + 1)) / n,
              [oa, ya] = outer(sa0),
              [ob, yb] = outer(sb0),
              sa = L.soffit(a, sa0),
              sb = L.soffit(a, sb0),
              out = [-u3[2] * side, 0, u3[0] * side];
            face(body, [p3(sa0, proud, sa), p3(sb0, proud, sb), p3(ob, proud, yb), p3(oa, proud, ya)], out);
            face(body, [p3(sa0, v, sa), p3(sb0, v, sb), p3(sb0, proud, sb), p3(sa0, proud, sa)], [0, -1, 0]);
            face(body, [p3(oa, v, ya), p3(ob, v, yb), p3(ob, proud, yb), p3(oa, proud, ya)], [0, 1, 0]);
          }
        }
        // String course just under the deck, along the whole face.
        set('string');
        const c = frame.at(frame.length / 2, side * half);
        block(m.stone, c, tangent, frame.length, 0.14, h - 0.32, h - 0.12, true);
      }
      info.arches = L.arches.length;
      info.span = +L.span.toFixed(2);
      info.edgeSpans = L.edgeSpans.map((s) => +s.toFixed(2));
      info.springing = L.springing;
      info.crownSoffit = +L.crown.toFixed(3);
      info.rise = +L.rise.toFixed(3);
      info.crownClearance = +(L.crown - waterLevel).toFixed(3);
    } else {
      // Deck bridges: brick abutments at the water edges, walled approaches on land, a timber or
      // iron deck between, or the recorded slab.
      const under = L.deckUnderside,
        plank = form.form === 'slab-deck' ? h - 0.4 : h - 0.12;
      set('abutment');
      for (const [from, to, foot] of [
        [a0 - lab, a0, foot0],
        [a1, a1 + lab, foot1],
      ]) {
        const mid = (from + to) / 2;
        block(m.brick, frame.at(mid), frame.tangent(mid), to - from, W + 0.6, foot, plank, true);
      }
      set('deck');
      for (const g of frame.segments) {
        const mid = g.s0 + g.length / 2;
        block(form.form === 'slab-deck' ? m.stone : m.wood, frame.at(mid), [g.ux, g.uz], g.length, W, plank, h, true);
      }
      // Girders or beams over the span, bearing 0.3 m into each abutment.
      const beams =
        form.form === 'iron-deck'
          ? [-half + 0.2, ...(W > 4 ? [0] : []), half - 0.2].map((v) => [v, 0.3, m.iron])
          : form.form === 'timber-deck'
            ? (W > 3 ? [-0.375, -0.125, 0.125, 0.375] : [-0.3, 0.3]).map((f) => [f * W, 0.25, m.wood])
            : [];
      set(form.form === 'iron-deck' ? 'girder' : 'beam');
      const s0 = a0 - 0.3,
        s1 = a1 + 0.3;
      for (const g of frame.segments) {
        const from = Math.max(s0, g.s0),
          to = Math.min(s1, g.s0 + g.length);
        if (to <= from) continue;
        for (const [v, thick, material] of beams)
          block(material, frame.at((from + to) / 2, v), [g.ux, g.uz], to - from, thick, under, plank, true);
        if (form.form === 'iron-deck')
          for (let s = Math.ceil(from / 1.5) * 1.5; s < to; s += 1.5)
            block(m.iron, frame.at(s), frame.tangent(s), 0.15, W - 0.4, plank - 0.35, plank, true);
      }
      // Walled approaches on land between the route ends and the abutments.
      set('approach-wall');
      for (const side of [-1, 1])
        for (const [from, to] of [
          [0, a0 - lab],
          [a1 + lab, frame.length],
        ]) {
          if (to - from < 1e-3) continue;
          const n = Math.max(1, Math.ceil(to - from)),
            columns = [];
          for (let j = 0; j <= n; j++) {
            const s = from + ((to - from) * j) / n,
              [x, z] = frame.at(s, side * half);
            columns.push([x, z, Math.min(plank, level(x, z) - 0.4), plank]);
          }
          wallFace(m.brick, columns, side);
        }
      info.deckUnderside = +under.toFixed(3);
      info.deckClearance = +(under - waterLevel).toFixed(3);
    }

    // Parapets (masonry) or railings, both sides, the full route length.
    const masonry = arch || form.form === 'slab-deck';
    for (const side of [-1, 1]) {
      const name = side > 0 ? 'left' : 'right';
      if (masonry) {
        set(`parapet-${name}`);
        const material = form.form === 'stone-arch' ? m.stone : m.brick,
          thick = arch ? defaults.parapetThickness : 0.3,
          top = h + defaults.parapetHeight;
        for (const g of frame.segments) {
          const mid = g.s0 + g.length / 2,
            u = [g.ux, g.uz];
          block(material, frame.at(mid, side * (half - thick / 2)), u, g.length, thick, h, top);
          block(
            m.stone,
            frame.at(mid, side * (half - thick / 2)),
            u,
            g.length,
            thick + 0.1,
            top,
            top + defaults.copingHeight,
            true
          );
        }
        if (arch) {
          // End piers where the parapets meet the approaches.
          set('end-pier');
          for (const s of [0.35, frame.length - 0.35]) {
            const c = frame.at(s, side * (half - 0.35));
            block(material, c, frame.tangent(s), 0.7, 0.7, h, top + 0.25);
            block(m.stone, c, frame.tangent(s), 0.85, 0.85, top + 0.25, top + 0.37, true);
          }
        }
      } else {
        set(`railing-${name}`);
        const iron = form.form === 'iron-deck',
          material = iron ? m.iron : m.wood,
          post = iron ? 0.08 : 0.12,
          rail = defaults.railingHeight,
          v = side * (half - post / 2);
        const stations = [0];
        for (const g of frame.segments) {
          const n = Math.max(1, Math.ceil(g.length / (iron ? 1.8 : 2)));
          for (let j = 1; j <= n; j++) stations.push(g.s0 + (g.length * j) / n);
        }
        for (const s of stations)
          block(material, frame.at(Math.min(s, frame.length - 1e-6), v), frame.tangent(s), post, post, h, h + rail);
        for (const g of frame.segments) {
          const mid = g.s0 + g.length / 2;
          for (const [y, size] of [
            [h + rail - 0.07, iron ? 0.06 : 0.1],
            [h + 0.5, iron ? 0.04 : 0.08],
          ])
            block(material, frame.at(mid, v), [g.ux, g.uz], g.length, size, y, y + size * (iron ? 1 : 1.4), true);
        }
      }
    }

    // Wing walls: from each abutment corner along the bank, splayed back into the approach.
    set('wing');
    const wingLength = arch ? Math.min(5, Math.max(2, (h - L.springing) * 0.9)) : 1.5,
      wingTop = arch ? h - 0.12 : L.deckUnderside;
    for (const [i, foot, land] of [
      [0, foot0, -1],
      [1, foot1, 1],
    ])
      for (const side of [-1, 1]) {
        // Along the face line (skewed), outward, then turned 30 degrees towards the land.
        const k = skews[i],
          fl = Math.hypot(k, 1),
          fs = (k * side) / fl,
          fv = side / fl,
          ds = Math.cos(Math.PI / 6) * fs + Math.sin(Math.PI / 6) * land,
          dv = Math.cos(Math.PI / 6) * fv,
          dl = Math.hypot(ds, dv);
        const start = [faceAt(i, side * half), side * half],
          dir = [ds / dl, dv / dl],
          columns = [],
          back = [];
        const end = frame.at(start[0] + dir[0] * wingLength, start[1] + dir[1] * wingLength),
          endTop = Math.min(wingTop, Math.max(level(...end) + 0.45, (arch ? L.springing : waterLevel) + 0.3));
        for (let j = 0; j <= 5; j++) {
          const t = j / 5,
            s = start[0] + dir[0] * wingLength * t,
            v = start[1] + dir[1] * wingLength * t,
            [x, z] = frame.at(s, v),
            [bx, bz] = frame.at(s + land * 0.5, v),
            top = wingTop + (endTop - wingTop) * t,
            bottom = Math.min(foot, level(x, z) - 0.4, top);
          columns.push([x, z, bottom, top]);
          back.push([bx, bz, bottom, top]);
        }
        // Water-facing side, back side, top and end. The side sign makes each face point outward.
        const face0 = frame.at(start[0], start[1]),
          face1 = frame.at(start[0] + dir[0], start[1] + dir[1]),
          toBack = frame.at(start[0] + land, start[1]),
          cross = (face1[0] - face0[0]) * (toBack[1] - face0[1]) - (face1[1] - face0[1]) * (toBack[0] - face0[0]),
          wallSide = cross > 0 ? -1 : 1;
        wallFace(body, columns, wallSide);
        wallFace(body, back, -wallSide);
        for (let j = 1; j < columns.length; j++)
          face(
            m.stone,
            [
              [columns[j - 1][0], columns[j - 1][3], columns[j - 1][1]],
              [columns[j][0], columns[j][3], columns[j][1]],
              [back[j][0], back[j][3], back[j][1]],
              [back[j - 1][0], back[j - 1][3], back[j - 1][1]],
            ],
            [0, 1, 0]
          );
        const e = columns.at(-1),
          b = back.at(-1);
        face(
          body,
          [
            [e[0], e[2], e[1]],
            [b[0], b[2], b[1]],
            [b[0], b[3], b[1]],
            [e[0], e[3], e[1]],
          ],
          [e[0] - columns.at(-2)[0], 0, e[1] - columns.at(-2)[1]]
        );
      }

    // End closures under the deck at both route ends, set 0.05 m inside so they never fight the
    // approach fill drawn on the same line.
    for (const [s, dir] of [
      [0.05, -1],
      [frame.length - 0.05, 1],
    ]) {
      // Where an abutment reaches the route end the closure is the abutment's back.
      const reach = Math.abs(skews[dir < 0 ? 0 : 1]) * half;
      set((dir < 0 ? s + reach >= a0 - lab : s - reach <= a1 + lab) ? 'abutment' : 'closure');
      const t = frame.tangent(s),
        top = arch ? h : L.deckUnderside,
        foot = lowest([-half, 0, half].map((v) => frame.at(s, v))) - 0.4;
      if (foot < top)
        face(
          body,
          [
            [...frame.at(s, -half), foot],
            [...frame.at(s, half), foot],
            [...frame.at(s, half), top],
            [...frame.at(s, -half), top],
          ].map(([x, z, y]) => [x, y, z]),
          [t[0] * dir, 0, t[1] * dir]
        );
    }
    review.push(info);
  }
  const meshes = batch.build(THREE, scene, { name: 'Road bridge structures' });
  const triangles = meshes.reduce((sum, mesh) => sum + mesh.geometry.getAttribute('position').count / 3, 0);
  return { bridges: review, meshes: meshes.length, triangles, parts };
}
