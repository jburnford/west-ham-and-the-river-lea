# T13 report: street corridors retraced on the OS five-foot plan

3 October 2026. Branch `worktree-agent-a996728b271b783f4`, commit 0689860 on top of 4f98cb5. The agent could not write this file itself (the harness blocked report `.md` writes), so the parent saved its hand-back message here, lightly condensed. Overlays and tables are in the scratch folder `t13/` (`overlays/`, `strips/`, `bir_table.md`, `birc_after.json`), copied to `reference/photo-review-2026-10-03/views-t13/`.

## Summary

- **Stratford High Street:** both records now follow the midpoint of the double tram track drawn on the OS 1:1056 plan. Median deviation from the OS rail centre 0.02 m (was 1.90 m); maximum 1.85 m (was 9.97 m); stations over 0.5 m: 2 of 106 (was 96), both explained (bridge lettering at 600 m; a 1.5 m OS sheet-join step at 700 m).
- **The five High Street bridges** are laid on the road axis (no longer 0.7–3.8° skewed to the road and 0.4–5.7 m to one side) and shortened to the water (34–49 m → 9–32 m).
- **West Ham Lane and Ward Road** retraced onto their printed carriageways (kerb midpoints read in straightened strips); moved a median of 22–23 m, up to 59 m.
- **Arthingworth Street and Railway Place** added; **Albion Street** retraced; **Abbey Road northern section** added (the southern 155 m of the old "West Ham Lane" trace).
- **Angel Lane, Angel Lane block passage and High Street housing frontage** deleted (no printed street under any of them); kept in `removedRoads` with reasons.
- **The two T10 holes** fixed at source (span realignment; junction moved onto a straight piece).
- **Rebuild:** `infrastructure.json` and `housing-detail.json` rebuilt to a fixed point; a clean rebuild reproduces them byte for byte, so the 160k-leaf road-mesh drift is resolved.
- **Builder defect fixed:** GEOS "Unable to find a convex corner" on one shoulder sliver along Bridge Road; `triangles()` now catches it, snaps to 1 µm and retries.

## High Street fit

Rails detected automatically in 1 m cross-profiles (1,150 detections over 1,463 m), checked by eye at every bridge and both ends. Robust spline, residual median 0.12 m, fitted per OS sheet and blended over 682–712 m. Vertices 12 → 46 (main) and 5 → 12 (Channelsea approach). Rails hidden by lettering, the sewer crossing (780–850 m) and the Great Eastern viaduct (1,070–1,170 m): interpolated, not verified. Width kept at 12 m; legible kerbs are 9.4–13 m apart, so 12 m is 0.5–1 m generous in places. Bow brewery (`west-259-2`) now 6.154 m from the centreline (was 6.787); `shoulderWidth` 0.78 → 0.13, priors kept.

## Bridges

| Bridge | New span (m along route) | Length new / old | Bank skew from square | Old: angle to road, side offset |
|---|---|---|---|---|
| bow-bridge | 91.2–123.4 | 32.2 / 39.3 | 34°, 10° | 2.6°, −2.1/−0.5 m |
| pegshole-bridge | 454.8–472.9 | 18.1 / 34.3 | 1°, 19° | 0.7°, +1.9/+1.6 m |
| st-thomas-bridge | 600.0–608.9 | 9.0 / 17.8 | 1°, 3° | 3.8°, +0.4/−0.8 m |
| st-michaels-bridge | 661.4–676.7 | 15.4 / 29.9 | 9°, 8° | 0.8°, −2.1/−3.0 m |
| channelsea-high-street-bridge | 1303.0–1317.4 | 14.4 / 49.2 | 18°, 2° | 3.2°, −3.6/−5.7 m |

"Square to the river within 5°" is not met for four bridges because the OS does not allow it: the High Street runs straight over oblique crossings 9–22° from square. Spans are on the road; the skew stays in the banks as drawn. Square-ended decks must reach past a skewed bank by about half the width times tan(skew) plus 0.6 m or the corners leave holes; skewed abutment faces would need `infrastructure.js`.

## Housing decisions

Seven `district-*-east-return` rows: `barnby-hotham`, `hotham-randal`, `randal-skelton` re-keyed to Arthingworth Street (cover 0.00→0.85, 0.74→0.83, 0.05→0.27); `pitchford-langthorne`, `langthorne-paul`, `paul-barnby` stay on the lane; `leywick-morley-east` re-keyed to Abbey Road northern section. `os-row-34/35/36` trimmed 18.8/17.5/10.2 m where they crossed Arthingworth Street. `os-row-54-part-1` and `os-row-55` re-axed onto Railway Place and Albion Street terraces (cover 0.71→0.85, 0.52→0.94); `os-row-66` pinned with `fitToStreet: false`. Paul Street and Northern residential street 2 extended 17.2 and 14.1 m to the new lane.

## Buildings in the road (overlaps over 0.5 m²)

| | Total | In carriageway | Building wrong | Road wrong | Footway pinch only |
|---|---|---|---|---|---|
| Before | 127 | 31 | 61 | 21 | 45 |
| After | 122 | 32 | 59 | 22 | 41 |

Fixed: nine rows and frontage ranges (listed in `bir_table.md`). **Flagged, not mine:** High Street frontages `high-street-01…05` and `-30` are registered 6–9 m north-west of the drawn buildings and now sit in the carriageway (up to 185 m²); `high-street-24` is the exception (road about 0.5 m too wide). Pre-existing on roads not retraced: site 865 buildings against Abbey Road and Eastbourne Road (road wrong, OS cover about 1.0), `site873-os-1` against South Street, `high-street-09` on Marshgate Lane, `southwest-row-11` on Empson Street, and about 40 shoulder-only touches. Full table in `bir_table.md`.

## Structural diff

`infrastructure.json`: `roads` still 102 (changed: High Street ×2, West Ham Lane, Ward Road, Albion Street, two street ends; added: Abbey Road northern section, Arthingworth Street, Railway Place; removed: Angel Lane ×2, High Street housing frontage); `roadTriangles` 7,750 → 8,152; `shoulderTriangles` 16,545 → 16,740; five bridge spans changed; `railways`: only the GER Woolwich branch northern connection changed (its road clearance includes the High Street, which moved about 5 m at the viaduct; embankment 6,455 → 6,482 triangles; this is what breaks the landscape's stored railway topology); sewer items changed only where the retrace forces it: `sewerHighStreet.centre` moved 3.29 m, 82 bank and 22 crest triangles replaced within 35 m, rail-edge ends moved about 2.9 m. `housing-detail.json`: 17 row footprints changed; houses 3,035 → 3,017; yards 2,991 → 2,957.

## Regeneration

```
python3 scripts/build_infrastructure.py
(cd scripts && python3 build_housing_detail.py)
# repeat until neither output changes (three passes in the worktree, two on main after the T1c merge)
python3 scripts/build_main_landscape.py   # required, or the page stops at "The landscape data could not load"
```

## Checks

Worktree `npm test` 12/16: the two known failures plus `check_main_landscape` and `check_tram_rails` on "Main landscape railway topology differs" (expected until the landscape rebuild; both pass in a mirror with that one railway record restored, as does `check_sewer_high_street`). Python: `check_district_streets` fail → pass (one road-name line added for the Manor Road drainage crossing); newly failing because they pin the old High Street: `check_bow_flour_context`, `check_bow_magnet_context`, `check_mill_brush_context` (brewery shoulder 0.78), `check_remaining_trades_context`, `check_west_sugar_alignment`, `check_abbey_west_alignment`; `check_factory_yards` now fails on site 397 (yard 8.1 m² inside the printed West Ham Lane); `check_high_street_frontages` still fails on `high-street-01`.

## Renders (mirror on 4188; landscape still old in all after views)

Bow Bridge: span shorter and in line with the road on both approaches; before, visibly kinked. Channelsea span: arch face-on and shorter. Channelsea overhead: deck square across the road on the rail line; the four tram lines run continuously over it. Junction overhead: the dog-leg and its gap are gone. New: small white wedges at the deck-end corners 6–7.1 m from the centreline and the 0.3 m road-to-deck step, both `infrastructure.js` matters.

## Not done / unsure

Not edited: `infrastructure.js`, `sewer-crossing.js`, `tram-rails.js`, the landscape builder, `ground-plan.json`, `high-street-frontages.json`, factory data, alignment registers; no width, height, style or arch count changed; Hotham, Randal and Barnby Streets and `os-row-34/35/36` not retraced; `os-neighbourhood-traces.json` labels untouched. Unsure: the two interpolated High Street stretches; kerb midpoints read by eye; bank lines at St Thomas, St Michael and the Channelsea from the model outline; `randal-skelton` (cover 0.27); Abbey Road northern section not joined to Abbey Road.

## Decisions for the parent

1. Rebuild the main landscape after merging, then refresh the drainage hash.
2. Six register checks pin the old High Street: update the registers or record exceptions.
3. Skewed crossings: keep square-ended spans on the road axis, or draw skewed abutment faces in `infrastructure.js`.
4. `infrastructure.js`: close the deck-corner wedges and the road-to-deck step.
5. Move `high-street-01…05` and `-30` 6–9 m south-east onto the drawn frontages.
6. Rebuild `factory-yards.json` (site 397 reaches into the lane).
7. Later: retrace Hotham, Randal and Barnby Streets and their rows; join Abbey Road; rename "Warton Road northern section".
