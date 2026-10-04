# T10 report: horse-tram rails on Stratford High Street

Branch `worktree-agent-ace7af4b19e1bc11a`. The worktree was created at `116c0ae`, behind main. Before starting I fast-forwarded it to main `e60757d`. Nothing was written to the main checkout.

## Evidence found

There is good evidence for the tramway, and it shows **double track** along the whole modelled High Street.

- **OS London five-foot plan (1:1056, surveyed 1891–95, published 1893–96).** I used the NLS tile mosaics cached in `reference/spot-heights/mosaics/` (`m18_131060_87140`, `m18_131063_87137`, `m18_131063_87140`, `m18_131066_87134`, `m18_131069_87131`). They draw **four parallel rail lines** in the carriageway from Bow Road, over Bow Bridge, Pegs Hole, St Thomas and St Michael's bridges and the Channelsea bridge, to Stratford Bridge. I checked this by eye at 4–8× zoom at Bow Bridge, Pegs Hole and the Channelsea bridge.
  - I also scanned a cross-profile every 5 m along the modelled centreline. The four-line pattern was found at **239 of 284 stations**. The misses are lettering, bridge names, and the stretch from William Street to Park Lane, where the modelled centreline runs off the drawn carriageway (see below).
  - Line spacing within each pair: median **1.40 m** (interquartile range 1.30–1.40) at 0.38 m per pixel. This is consistent with standard gauge, but the map cannot tell 1,435 mm from nearby gauges.
  - Track centres: median **2.70 m** (interquartile range 2.60–2.80).
  - I saw no single-track section and no passing loop.
- **EPFL text layer** (`reference/epfl-london-os-text/londonos_texts_postcorrected.gpkg`) has two labels reading "TRAMWAY":
  - label 104206 at about scene (−953, 48), by the Bow granary on the High Street;
  - label 86528 at about scene (−160, −892), just north of Stratford Bridge.
- **Spot-height reader notes** (`data/maps/lower-lea-region/height-observations.opus-2026-10-02.geojson`) mention the rails along the whole route. Examples: "Stratford High Street tramway … dot a solid blob on the north rail", "High Street tramway at West Street; dot between the rails", and "tramway at Channel Sea Bridge; dot on rail above figure".
- **Photo catalogue** (`reference/photo-review-2026-10-03/reports/photo-catalogue.md`). The Broadway views 091809 and 091819 (c1904) show horse cars boarded "ALDGATE, WHITECHAPEL, MILE END, BOW & STRATFORD" on granite setts, with flush grooved rails and no wires. I looked at both images. They are about 460 m beyond the modelled street, so they document the service and the rail type, not this stretch of track. Photo 091910 dates the electric trams to 1905. No photograph of the High Street itself exists in the catalogue. No photograph was used as a texture.

## What I built

- **`data/maps/high-street-tramway.json`**: the evidence register. Each record (operation, track, rail, route) says what is mapped or documented and what is estimated, and cites sources by file path. Estimated values:
  - gauge 1,435 mm (standard gauge assumed);
  - track centres 2.70 m (rounded map measurement);
  - corners eased into 25 m radius curves (a typical value, not measured);
  - rail head 60 mm, groove 30 mm, lip 16 mm;
  - head 7 mm above the setts (a rendering allowance, not a claim that the rails stood proud);
  - colours.
- **`scripts/build_tram_rails.py` → `docs/data/tram-rails.json`**: checks the register against `infrastructure.json` (road names and bridge ids exist, gauge, rise between 5 and 10 mm, every record has an evidence string), then publishes it with its SHA-256.
- **`docs/tram-rails.js`**:
  - **Route.** It joins the two High Street route records from `data.infrastructure` at run time, so the rails follow any later road retrace. It rounds each corner into a curve so the gauge holds through bends.
  - **Track.** It lays two tracks centred on the modelled centreline. Each rail is three flush strips (lip, black groove, wheel-polished head) with the groove on the gauge side.
  - **Heights.** Each rail point sits 7 mm above the surface the reader actually sees. That surface is the road triangles, interpolated linearly exactly as drawn, with vertex heights from a copy of `ground()` in `infrastructure.js`. On the five High Street bridges it is the deck top instead (`bridge.height + 0.02`).
  - **Subdivision.** Stations are added only where needed: every 4 m at most, refined to 0.05 m where the surface creases or steps.
  - **Mesh.** Everything is one merged indexed mesh with vertex colours, kept out of the per-material batch (`keepIndexed`). Its material uses a polygon offset so the strips do not flicker against the setts at distance.
  - There are no poles, wires, trams or horses.
- **`docs/app.js`, 6 lines added**, nothing else touched:
  - the import, next to the `infrastructure` import (line 15);
  - `tramRails` in the `window.panoramaReview` report, after `infrastructure:` (line 475);
  - the call directly after the `infrastructure(...)` call in `buildScene`, so it inherits the `infrastructure` layer tag (line 808);
  - the `load('./data/tram-rails.json')` entry, its destructured name `tramRailsData`, and `data.tramRails = tramRailsData` in the data-loading block (lines 1241, 1258, 1272).

  The sewer-bank section is not touched.
- **`scripts/check_tram_rails.mjs`**. `run_checks.mjs` discovers every `check_*.mjs` file automatically, so it did not need editing. The check assembles the data as `app.js` does, builds the rails, then runs the real `infrastructure()` in Node (real `three`, stub canvas). It measures the rails against the road and deck meshes that module actually produces, not against the tram module's own copy. It asserts:
  - every rail vertex lies within 5 m of the High Street centreline (1 m inside the kerb);
  - the running edges of each track are 1.435 m ± 1 cm apart everywhere;
  - the rail head is above the drawn road by more than 1 mm and no more than 20 mm, at every vertex and every strip midpoint (except within 0.1 m of a deck end);
  - any rail vertex inside a river-system reach polygon (Channelsea and the four others) lies on a High Street bridge deck, and the rails do cross the Channelsea on its deck.

## Check and smoke results

- **`npm test`: 14/16.** `check_tram_rails.mjs` passes. The two known failures remain: `check_flood_demo.mjs` and `check_drainage_connections.mjs` ("Stale source docs/data/terrain-1900.json").
- **New check output:**
  - gauge 1.4350–1.4351 m;
  - widest rail point 2.54 m from the centreline;
  - rail 3.5–10.1 mm above the drawn road at midpoints, exactly 7.0 mm at every vertex;
  - 805 rail vertices over water, all on decks (96 over the Channelsea);
  - runs in about 10 s.
- **Prettier and eslint** are clean on `docs/tram-rails.js`, `docs/app.js` and `scripts/check_tram_rails.mjs`.
- **Smoke test.** I took a base snapshot (`t10-base`) from an unchanged copy of the worktree's `docs` before any change. Then I ran a scratch copy of `review_smoke.py` with the settle wait raised to 900 s: `t10-tram-rails --compare drawn-ground --url=http://127.0.0.1:4184`. Result: ready, **0 page errors**, 18 differences against `drawn-ground`.
  - 16 of those 18 are already present between `drawn-ground` and my unchanged base: factory site 865, sewer-crossing end walls and road arches, landscape vertex counts, destination count. They come from other work merged before `e60757d`.
  - Against my own base there are exactly 5 differences, all from this change:
    - `tramRails` added;
    - triangles 8,167,680 → 8,208,336 (+40,656);
    - draw calls 150 → 151;
    - reflection-pass triangles +40,656;
    - reflection-pass draw calls +1.
  - The screenshot timed out and was skipped (the script treats it as optional).

## Render verdict per camera

I rendered from an unchanged copy of `docs` ("before") and from the worktree ("after"), both served on 4184. PNGs are in the scratch folder `t10/views-before` and `t10/views-after` (not committed).

1. **`bridge-channelsea-high-street-bridge-span`** (−210.19, 1.5, −754.28) → (−246.76, 1.65, −780.51), fov 60. Identical before and after. The camera is below deck level beside the river, so the deck surface is not visible. Nothing is disturbed.
2. **High Street at eye level from the north-east end** (−196.15, 1.8, −853.97) → (−246.76, 2.6, −780.51), fov 60. The road surface there is at 0.185 m. Double track reads clearly as four flush dark lines in the setts, running up the approach to the bridge. At close range each rail shows a lighter head, black groove and dark lip. No z-fighting, gaps or floating.
3. **Overhead of the bridge** (−247, 60, −740) → (−247, 0, −781), fov 50. Four thin lines run continuously across the Channelsea deck and onto both approaches, inside the parapets. Otherwise unchanged.
4. **Extra close view on the bridge** (−226.5, 4.7, −806.5) → (−258, 3.6, −765), fov 50. The rails follow the deck. This view shows the existing 0.30 m step where the road meets the deck end (see below). The rails climb it in a 5 cm ramp, so they look as if they step up the deck face, as the road does.

## Triangle and draw-call cost

- **40,656 triangles and 40,680 vertices** in one merged mesh, **+1 draw call** in the main pass and +1 in the reflection pass.
- That is 0.5% of the scene's 8.17 million triangles.
- Built from 1,695 cross-sections over 1,415.6 m of route.

## What I did not do

- I did not model crossovers, points, rail joints, drainage boxes, trams, horses, poles or wires.
- I did not extend the rails along Bow Road or beyond Stratford Bridge (outside the modelled High Street).
- I did not change the road alignment, the bridges, the road/deck steps or the holes, all of which belong to other modules.
- I did not regenerate `docs/scene-manifest.json` (not in my file list). Locally the new module and data file load without it.

## Findings in other modules (not fixed)

1. **The modelled High Street centreline is off the drawn carriageway in places.**
   - Along most of the route the drawn rails lie a median 1.3–1.6 m south-east of it.
   - At the Channelsea bridge the offset is about 4–5 m; the model's centreline runs along the north-west footway.
   - Between William Street and Park Lane the model's route bends up to about 8 m north-west into the frontage. There the separate 6 m "High Street housing frontage" road follows the true carriageway better.
   - The rails follow the modelled road, as the corridor check requires, so they inherit these offsets. They will move with any retrace.
2. **Road-to-deck steps at all five High Street bridges.** The approach road ends 0.08–0.33 m below the deck top: Channelsea 0.30 m, Bow Bridge 0.27–0.29 m, St Michael's 0.28–0.30 m.
3. **Two small holes in the drawn road surface:**
   - a triangular gap of about 0.5 m at the north-west side of the Bow Bridge west end;
   - a sliver along the junction of the two High Street route records at (−371, −654).

   The rails cross both on the plane of the adjoining road. That is 43 of 26,701 check samples, plus a few at the very north-east end of the route.

## What I was unsure of

- **Gauge.** It is assumed, not read from the map.
- **Track centres and curve radius.** The 2.70 m track centres are a map measurement good to about ±0.2 m. The 25 m curve radius is a typical value, not measured.
- **Date.** The OS predates the scene by 5–9 years. I found nothing in the repository about relaying or a change of track form by 1900.
- **Rail look.** The head colour looks slightly cool and bright at close range; that is a matter of taste.
- **The copied height formula.** `docs/tram-rails.js` repeats the `ground()` height formula from `infrastructure.js`. If that formula changes, `check_tram_rails.mjs` will fail, because it measures against the real meshes. The rails would then need the copy updated.

## Decisions for the parent

1. Whether to retrace the High Street centreline onto the OS carriageway (William Street–Park Lane, and the Channelsea bridge). The rails will follow automatically.
2. Whether the owners of `infrastructure.js` / `build_infrastructure.py` should close the road/deck steps and the two holes.
3. Whether to regenerate `docs/scene-manifest.json` for the published site, so the new module and data file get cache-busting fingerprints.
4. Whether to export `ground()` from `infrastructure.js` later, so the tram module can drop its copy.
