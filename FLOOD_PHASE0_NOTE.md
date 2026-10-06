# Flood model, Phase 0: evidence and structure register (5 October 2026)

Branch `task-e-flood-model` (worktree `../book_website-taske`), from main `e59ad25` (task D, fast-forwarded locally, not pushed). This is the Phase 0 checkpoint in `FLOOD_MODEL_PLAN.md`: nothing in the model has changed. The deliverables are:

- the draft register `data/maps/lea-control-structures.json`;
- OS five-foot crops at every control, in `reference/flood-model-phase0/crops/` in the main checkout (git-ignored), with a contact sheet `reference/flood-model-phase0/contact-sheet.jpg`. Each crop shows the model's channel outlines (blue), OS spot heights converted to scene y (red), and a 50 m scene grid;
- this note: what the evidence says, every estimate, and the decisions for the author.

## What I read

- **The book, in full:** chapter 1 (PDF pp. 40-68) and chapter 6 (pp. 176-206), plus their notes. I also read the flood and drainage passages in the foreword (p. 19) and chapter 3 (pp. 90-93), and the conclusion (p. 212).
- **VCH Essex vi, "West Ham: Ancient mills"** (pp. 89-93). This is the book's source for the mills (ch. 1 note 11), and it gives each mill's state in the 1890s.
- **The Lee and Stort page on Bow Locks**, already in the repo. It covers lock dates and dimensions, the Four Mills' control of Bow Lock, the 1898 tide-gate proposal and the 1928 rises above normal head.
- **The OS five-foot plan** at every control. The EPFL text layer was searched for every Lock, Weir, Sluice, Flood Gate, Mill and tide label between Temple Mills and Bromley.
- **The existing registers:** the control sites, the flood events, the tide levels and the OS ground levels.

## What the evidence says

1. **This was a system of tide mills, not a chain of steady pounds.** The OS letters "Highest point to which Ordinary Tides flow" beside the weir at Temple Mills bridge (x -1328, z -2273), 2.3 km up the Waterworks River. Ordinary tides therefore passed the Stratford mills.
   - Book p. 46: the mills let the flood in through one-way gates, held it, and ran the ebb through the wheels.
   - Book p. 49: in 1824 the flood "did not extend below the mill dams". The upstream inhabitants blamed "this damming and penning up of the Lea", and an eighteenth-century embankment built to trap more tide for Three Mills and Four Mills.
   - For the model, a working mill's pond fills to the tide's high water and is then *held* while the tide falls. A flood comes when high Lea flow arrives while the ponds are full and the tide outside is high.
   - This changes plan section 4.2: pond levels depend on the tide's state and the gates, not only on flow (decision 2).
2. **Two mills still worked c.1895; the others were works or gone** (VCH):
   - Three Mills: Nicholson's gin distillery from 1872, with tide-driven wheels still in use into the 1930s (the Prescott sluice was built so they could run longer).
   - Abbey Mill (Corn): Hunt family tenants 1881-1936; it had stopped by 1929.
   - City Mills: Howards & Sons, chemists, held the whole site; corn-grinding is last recorded in 1818.
   - St Thomas's (Pudding) Mill: Du Barry's Patent Food, with no evidence of water power.
   - **Waterworks Mill (Saynes): gone by 1893-4.** The existing control site `waterworks-mill` has no 1890s structure.
3. **Abbey Mill kept the tide out rather than holding a tide pond.** Ordinary tides stopped there (task C). The upper Channelsea's towing path (11.5 ft, 1.27 m) and Channel Sea Road (1.10-1.21 m) lie below ordinary high water (1.578 m), so the mill's gates must have shut against the flood.
   - This is the clearest single example of the teaching point: without the gates, the tide would have covered the Stratford streets twice a day.
4. **The Navigation held a "normal head".**
   - On 7 January 1928 the water rose 7 ft 8 in above normal head at Bromley and 7 ft 7 in at Old Ford. The Thames peak that night was 5.02-5.21 m ODN. Together these put the head at about 2.8 m ODN, **0.95 m scene**.
   - High water of ordinary tides (1.578) rose above that head, so at high tide Bow Lock stood level. A 1946 photograph shows the gates open at both ends.
   - Beside the Tidal Lock the OS draws a long stepped masonry overfall (about 70 m). I read it as the overshoot that sets the head; the book measures the 1892/1908 canal standard from "the overshot level at Bow Lock" (p. 200).
5. **The Limehouse Cut leaves the tidal Lea through Bromley Lock**, below Bow Locks, by way of the Sun Mills/Four Mills mud basin. The Four Mills no longer had a dam of their own: by 1893-96 the site was a distillery and a corn mill. Its historical control was Bow Lock itself, until the pound lock of 1852.
6. **The back rivers were shallow and silted.**
   - The back rivers were "navigable only during bimonthly spring tides" (p. 200), and the proposed canal bed was six feet below the overshot level, about -0.9 m scene.
   - The model's back-river beds lie at -2.1 to -3.7 m (medians by channel), 1.2-2.8 m deeper than the depth the 1908 engineers proposed to dredge to (decision 4).
7. **Rain flooding is in the book.** It gives three causes (pp. 178-179): heavy rain overwhelming the sewers, which caused minor floods in the low districts; major or prolonged rain swelling a Lower Lea "obstructed by bridges, mills, and pollution" (1888); and North Sea surges (1897, 1904, 1928). Pages 180-181 add that the Middle Lea's 1890s flood works sped flood water down to an unimproved Lower Lea. Pumps were drowned in 1875 and 1888 (p. 182).

## The structure list (c.1895 defaults proposed)

| Structure | Type | Default c.1895 | Basis |
|---|---|---|---|
| Three Mills | tidal mill | working: fill on the flood, hold, run on the ebb | VCH; book pp. 46, 67, 202 |
| Abbey Mill (Corn) | mill head at the tidal limit | working: tide shut out, river released at low water | VCH; OS tide note |
| Bow Locks | tidal pound lock | working; level at high tide | Lee and Stort |
| Three Mills overfall | weir, Navigation into the pond | fixed; crest = normal head | "Overfall" on the 1860s plan; 1898 proposal |
| Bow overshoot | weir | fixed; crest = normal head | OS hatching; book p. 200 |
| Bromley Lock | lock (Limehouse Cut) | working | OS; 1916 and 1928 reports |
| City Mills | mill head + flood gates | working in part (author) | 1860s and 1893 plans; VCH; book p. 205 |
| Waterworks River flood gate | flood gate on the old Waterworks Mill site | open | OS 1848 and 1893; book p. 205 |
| Waterworks Mill | — | **absent** | VCH |
| St Thomas's (Pudding) Mill | mill head | working, head held (author) | embanked head on the 1893 plan; VCH; book p. 204 |
| Marshgate Lane lock | lock (Bow Back River) | working | OS; author |
| Old Ford Lock | lock | working (upstream boundary) | OS |
| Old Ford flood gates | flood gate | shut; drawn in floods | OS |
| Temple Mills weir | weir | fixed; tidal limit | OS |
| Four Mills | — | no control in the 1890s (kept for 1809) | OS; Lee and Stort; VCH |
| 10 OS sluices | marsh drain sluices | tide-locked outfalls | OS labels |

## Every estimate

Values are in scene y (ODN = y + 1.835). "Documented" means a source gives it; everything else below is an estimate.

| Quantity | Value (range) | Method |
|---|---|---|
| Navigation normal head (Bow pound, Limehouse Cut) | 0.95 (0.75-1.25) | 1928 Thames peak about 5.1 m ODN, less 7 ft 7-8 in above normal head |
| Bow overshoot crest | = normal head | definition; crest length about 70 m on the plan (40-80) |
| Bow Lock sill | -1.2 (-1.8 to -0.9) | below the 1908 canal standard bed; chamber 20 ft documented |
| Three Mills pond, full | 1.578 | the tide's high water (documented mechanism) |
| Three Mills pond, drawn-down floor | 0.0 (-0.9 to 0.6) | no sill survey; silted beds above -0.9 (book p. 200) |
| Three Mills opening | 8 m (4-12) | wheel bays and race, not mapped; discharge coefficient 0.6 |
| Abbey Mill retained level (upper Channelsea) | 0.6 (0.06-1.0) | below the towing path (1.27) and Channel Sea Road (1.10-1.21) |
| Abbey Mill gate top | 1.8 (1.6-2.2) | at least ordinary high water; below Abbey Road (2.19) |
| Abbey Mill opening | 10 m (6-14) | two passages read on the plan |
| City Mills held head (if working) | 1.578 | as Three Mills |
| City Mills, Waterworks gate, St Thomas's, Marshgate lock openings | 6, 5, 3, 5 m | read on the crops |
| Pudding Mill held head / floor | 1.578 / 0.3 (-0.5 to 1.0) | as a tide mill; small embanked head |
| Three Mills overfall crest, length | = normal head; 15 m (8-20) | link width at the footbridge |
| Old Ford upper pound (Hackney Cut) | 2.5 (1.9-3.5) | below the lock-side readings (4.08-4.23) |
| Temple Mills weir crest | 1.7 (1.578-2.2) | ordinary tides stopped there; street 15.8 ft (2.58) by the bridge |
| Weir coefficient | 1.6 (SI) | generic broad-crested weir |
| Sluice sills | unknown | below the adjacent marsh readings (-0.86 to -0.22 at the Abbey Creek sluices) |
| Lea flow presets | see below | G2G 38001, daily means |

**Unknown, with no estimate yet:**

- the gate and sill levels at City Mills, the Waterworks flood gate, Marshgate lock and the Old Ford flood gates;
- every marsh outfall, including Mill Meads (the ditches run to the Long Wall at about (-415, 460));
- the Three Mills race sills.

## Corrections to the plan

- **G2G statistics.** The CSV changes date format in 1900 (ISO before, dd/mm/yyyy after), so the plan's "1891-1910" figures cover 1891-1899 only. Corrected figures for Feildes Weir (38001):

  | | 1891-1910 | 1891-1899 |
  |---|---|---|
  | Median | 4.35 m³/s | 4.59 |
  | Q95 | 2.06 | 1.99 |
  | Peak | **56.1 (15 June 1903)** | 40.9 (15 November 1894) |

  Seasonal figures for 1891-1910:
  - summer (July to September) median 3.04, Q95 1.62;
  - winter (December to February) median 6.33, Q10 12.9.

  These are modelled natural flows. In dry summers the waterworks took most of the Lea (book pp. 66, 79), so the back rivers saw far less than this.
- **The control-site register's "Waterworks Mill"** has no 1890s structure. Its 1890s control is the Flood Gate.
- **"Abbey Lock tide gates" and the "Three Mills Overshoot"** are not drawn on the 1893-96 sheet (register `notFound`).

## Decisions for the author

1. **Which mills held water in the 1890s?** I propose Three Mills and Abbey Mill working, with City Mills, St Thomas's and the Waterworks gate passing water (no evidence of milling). The alternative is "all ancient mill sites holding heads". That reads better for the teaching aim but goes beyond the evidence for c.1895. It would suit the 1809 model.
2. **Tide-mill ponds instead of steady pounds (plan 4.2).** A working mill holds its pond at the last high water while the tide falls, down to its drawn-down floor. Proposed rule for the scene:
   - pond level = max(tide, held level), where the held level runs from the high water down to the floor as milling goes on;
   - the Lea flow adds to the pond, and the excess spills over the overshoot and the banks.
   - The visitor's tide slider then shows the ponds standing above a falling tide. A "gates drawn" switch shows the same rivers draining to low water.
3. **The Navigation and the back rivers.** The OS draws no gate where the Three Mills Back River meets the Navigation near Bow Bridge (x about -800, z 150-250). The 1898 proposal for a tide gate there was rejected. The Bow Back River's west mouth is also open. So either the Navigation's head and the Three Mills pond were one water body at low tide, or there was a control the OS does not show. Which reading should the model follow? A record of the Navigation level at Three Mills would settle it; LMA ACC 2423 may hold one.
4. **Back-river beds.** The model's back-river beds lie 1.2-2.8 m below the canal depth the engineers proposed to dredge to in 1908. Raise them as a fundamental before the pounds are built? It changes the drawn mud at low water on every back river.
5. **The plan's five questions still stand:**
   - flow in m³/s with the G2G presets above, or named scenarios;
   - rain as a storm total in mm;
   - switches per structure or one "mills working / gates drawn" switch;
   - the default flood view.

Next, after the author's answers: Phase 1 (the whole-model flood grid), which does not depend on these decisions, then Phase 2 with the levels agreed here.

## Author review and map re-check (5 October 2026)

The author's answers:

- Pudding Mill must have held water.
- City Mills was probably still working to some extent.
- The Waterworks stream had no mill.
- Decision 2: yes.
- There is some kind of wall between the Navigation and the Three Mills pond; perhaps it held the Navigation's level and let the river through to Bow Creek.
- Floods: several kinds eventually, but the flood from rain up river comes first.

I compared the 1893 plan with the 1860s 1:1,056 plan and the 1848-51 skeleton survey. The crops are named `cmp-*.png`.

- **The Navigation and the Three Mills pond are walled apart**, as the author thought.
  - From Bow Bridge to Three Mills a strip of land carrying the Bow Bridge chemical works runs between the Navigation (with the towing path) and the Three Mills Back River. Below that strip, the garden island above the mill separates them.
  - At the head of the island the 1860s plan letters **"Overfall"** (about x -711, z 311). The 1893 plan draws a short link there with a footbridge.
  - This is the "Three Mills Overshoot" of the 1898 proposal. The Navigation was held at its normal head by this overfall and the stepped overfall at Bow Locks, and its surplus ran into the pond and through Three Mills to Bow Creek. At high tide the pond rose above the head.
  - My decision-3 reading (an open junction near Bow Bridge) was wrong. The register now has a `three-mills-overfall` record.
- **The Bow Back River is new.** It is not on the 1860s plan. By 1893 it runs from an open mouth on the Navigation to the Marshgate Lane lock, the only navigable link between the Navigation and the back rivers.
- **Pudding Mill.** The river runs only under St Thomas's Mill: "(Corn)" in the 1860s, "(Patent Food)" in 1893. In 1893 the head channel above the mill has a hatched embankment, a raised mill head. Default: working, head held.
- **City Mills** spans the City Mill River at the footbridge on both plans. Default: working, reduced opening.
- **Waterworks River.** The 1848-51 survey draws buildings across the river where the 1893 plan letters "Flood Gate". That is the old Waterworks (Saynes) Mill, gone by 1893-4; the gate stands on its site.

**Next.**

- The first flood scenario is high Lea flow from rain up river. It meets the working mills (Three Mills, Pudding Mill, City Mills, Abbey Mill) and the Navigation's overfalls.
  - The G2G presets are above.
  - The 1894 peak (40.9 m³/s, daily mean) is the 1890s case; 1903 (56.1) is the largest in 1891-1910.
- Phase 1 (the whole-model flood grid) goes ahead.
- Decision 4 (raise the back-river beds) is still open; Phase 2 needs it.
