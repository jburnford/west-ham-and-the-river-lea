# T6 report: Leather Cloth Works, site 865

3 October 2026. Branch `worktree-agent-a20b88593b5ddb6a5`. Nothing rendered.

## Before I started: the worktree base

The worktree was created at `116c0ae`, 19 commits behind `main` (`72d97c8`). At that commit the delegation plan, the Bromley register, `footprint_gap_audit.py` and the review tooling did not exist. I fast-forwarded the worktree branch to `main` (`git merge --ff-only main`, run inside the worktree). Nothing was written to the main checkout. All diffs and checks below are measured against `72d97c8`.

## What changed

- New `data/maps/leather-cloth-footprint-alignment.json`: 31 buildings, 1 chimney, and an `additionalSites` entry for 865. That entry lifts the site's old exclusion as "East of Channelsea".
- `scripts/build_factory_buildings.py`: one line, adding the register to `group_registers`.
- `docs/data/factory-buildings.json`, regenerated.
- This report.

## What is mapped

**Supplied outlines.** The GeoPackage has 50 outlines more than 5 % inside the site polygon, totalling 7,998 m². The gap list's 43 is lower because seven central outlines (15181, 110973, 324678, 820133, 1049981, 1230246, 1291498) were outside the audit's "started" zone until the site was registered.

**OS labels.** The EPFL text layer gives only two labels on the site:
- "Leather Cloth Works" at about (372, −358);
- "Reservoir" at about (417, −411).

There is no "Chy.", boiler, tank or department label. The roads are "C.R. ABBEY ROAD" (west), "EASTBOURNE" (north) and, on the south side, OS lettering "S T E P H…" (EPFL label "STEPH"). I found no full name for the south road in the repository, so the records call it "the south road". The "Stephen's Road" entries in the repository are a different street, about 2 km east (spot height at E541417).

**Registration.** At this site the GeoPackage outlines sit 1.75 m west and 0.25 m south of the printed outlines in the cached NLS mosaic. I fitted this offset to the outline ink of 17 supplied footprints, and every one agreed to within 0.25 m. As at Bromley, the supplied outlines are used unshifted. Only my three traced roofs were moved into the GeoPackage frame.

**A large omission in the GeoPackage.** The OS shows a continuous hatched (roofed) block along the south road with no supplied outline: about 2,010 m², running from the east wall of fid 4408 to the pair of sheds 13648 and 7607. Its neighbours are all supplied. The GeoPackage outline for 4408 simply stops at the join between two OS sheets, although the hatching runs on. I traced the block from the mosaic:
1. hand-read wall lines;
2. each line snapped to the printed ink (±1.5 m, ±4° search);
3. corners taken at the line intersections;
4. the result shifted into the GeoPackage frame and clipped against the supplied neighbours.

The OS draws no internal walls in this block. I split it into three roofs with two modelling cuts: the yard edge extended east, and a line dropped square to the road wall from the corner of the open notch. The traced vertices in the mosaic frame are stored on each record (`tracedOutlineMosaicFrame`, `registrationShiftToSourceFrame`). **This goes beyond the 43 listed footprints; see judgement call 1.**

## The programme and why

Storeys follow a stated rule, not evidence:
- large sheds are one tall storey with 5.5 m eaves;
- compact detached blocks of 150–300 m² are two storeys;
- house-type outlines with bays, and the long street front, are two storeys (the builder's default of 6.9 m eaves);
- small ancillary buildings are one storey, 3.0–4.2 m.

Roofs are slate gables. Ranges deeper than about 18 m get ridge-and-furrow with spans of 9–14 m. Roof rise is 0.27 × bay span, capped at 4 m, which is the builder's own formula. All walls are stock brick.

| Record | Source | m² | Storeys / eaves | Roof | Reading |
|---|---|---|---|---|---|
| b865-north-hall | fid 150 (main block) | 2,005 | 1 / 5.5 | 4 spans | great shed beside the reservoir |
| b865-reservoir-range | fid 150 (south strip) | 1,571 | 1 / 6.5 | 1 span, 17.6 m | long range; drying stoves as a type-based reading |
| b865-reservoir-range-west-bay, -east-spur | fid 150 (lobes) | 195, 64 | 1 / 4.5 | gable | projections cut off so the range keeps an even span |
| b865-hall-west-adjuncts | 995306, 1018319, 1043032 | 17 | 1 / 2.8 | gable | cells on the Abbey Road wall |
| b865-garden-house | 65662, 1100167 | 131 | 2 / 6.9 | gable | detached house in the works garden |
| b865-eastbourne-road-lodge | 826726, 901022 | 38 | 1 / 3.4 | gable | boundary lodge |
| b865-reservoir-corner-building | 165507 | 81 | 1 / 4.0 | gable | possibly a pump house (unlabelled) |
| b865-central-block | 15181 | 287 | 2 / 6.9 | gable | block at the OS works label |
| b865-central-annex | 110973, 1049981 | 102 | 1 / 4.2 | gable | attached range |
| **b865-boiler-house** + **stack-865-boiler-house** | 24851, 909790, 975990; chimney on 1061509 | 234 | 1 / 6.0; stack 22 m | gable | see below |
| b865-yard-building-south / -west | 178340; 324678, 787182, 940179 | 78, 102 | 1 / 4.0, 3.8 | gable | yard buildings |
| b865-garden-hut | 820133 | 25 | 1 / 3.0 | gable | hut in a dotted enclosure |
| b865-east-compound-building | 407156 | 57 | 1 / 3.6 | gable | building in the walled east compound |
| b865-abbey-road-house (+ annex) | 54167; 910781, 937447 | 141, 24 | 2 / 6.9; 1 / 3.0 | gable | house or office at the Abbey Road entrance |
| b865-north-west-yard-building | 184684, 904977, 1232732 | 93 | 1 / 3.6 | gable | at the OS sheet join |
| b865-abbey-road-range-north, -cells, -range-south | 112042; 838603, 846702, 868731; 70944 | 97, 62, 123 | 1 / 3.2–3.6 | gable | narrow boundary ranges |
| b865-main-shed-west | 3440, 966017 | 738 | 1 / 5.5 | 2 spans | large shed |
| b865-yard-block (+ lean-to) | 26347; 758415 | 207, 32 | 2 / 6.9; 1 / 3.0 | gable; lean | compact block |
| b865-sw-corner-shed | 4408, 913012 | 650 | 1 / 5.5 | 2 spans | corner shed |
| **b865-street-range** | OS trace | 762 | 2 / 6.9 | 2 spans | street front on the south road |
| **b865-l-wing** | OS trace + 1022465 | 347 | 1 / 5.5 | 2 spans, ridges N–S | wing into the yard |
| **b865-east-shed** | OS trace | 905 | 1 / 5.5 | 2 spans | shed east of the open notch |
| b865-east-shed-annex | 801184 | 27 | 1 / 4.0 | gable | projecting room |
| b865-south-road-shed-west / -east | 13648; 7607 | 308, 455 | 1 / 5.5 | 1 and 2 spans, gable to the street | pair of sheds |

The bold traced records are not in the GeoPackage.

**Boiler house and chimney.** Range 24851 has a small square drawn open in it. The GeoPackage cuts that square from the range as a hole and also supplies it as its own polygon (fid 1061509, 2.1 × 1.9 m). I read this as a chimney base:
- The chimney is a square brick stack placed on that fid.
- Its height is 22 m, the typological value the project already uses for unmeasured stacks.
- The range keeps the hole (`worldHoles`), the same "mapped chimney well" convention the renderer already supports.

The boiler-house function follows from that reading; nothing on the OS labels it.

The totals are 31 records and 9,955 m² of roof:
- 7,941 m² from 45 supplied outlines;
- 2,014 m² traced.

## Structural diff of `docs/data/factory-buildings.json`

I produced this with a short script (`fbdiff.py`, kept outside the repository) against the `72d97c8` file:

```
top-level keys unchanged: True
sources.author-os-footprints-1891-96.method: text appended (718 chars)   <- this register's method string
excludedSites: +0 -1; removed [865]
structures: +1 -0 changed 0; site [865]; existing order kept
footprintAlignment.groupRegisters: +['data/maps/leather-cloth-footprint-alignment.json']
sites: +1 -0 changed 0; site [865]
buildings: +31 -0 changed 0; site [865]; existing order kept
counts.chimneys 88 -> 89, counts.ranges 697 -> 728, counts.sites 63 -> 64
```

No existing building or structure changed, including the render polygons. Every record carries `footprintEvidence`, `heightEvidence` and `roofEvidence`. Every `heightEvidence` opens with "Explicit estimate".

## Builder assertions and geometry audit

- `python3 scripts/build_factory_buildings.py` runs with no assertion failures. These cover polygon validity, unique ids, every site having ranges, no excluded site registered, and holders clear of water and buildings. I also rebuilt the baseline first: it reproduced the committed file byte for byte.
- In `geometry-audit.json` only `counts` differs from the baseline. Water intersections (5), source-range overlaps (5), render adjustments and fully covered ranges are identical, so site 865 adds none. No 865 range takes a street trim; I did not verify why no registered street corridor touches the site.
- Overlaps among the new records are at most 0.5 m², at shared walls. There are no collisions with housing rows, rear extensions, privies or neighbourhood houses.

## npm test

13/15 pass, the same count as expected.

- `check_flood_demo.mjs` fails on the known stale `terrain-1900.json` hash.
- `check_drainage_connections.mjs` fails in this worktree for an environmental reason first: it hashes git-ignored `reference/spot-heights/mosaics/*`, which a worktree does not have. I hashed its inputs in Python, reading the missing files from the main checkout. Everything matches except the same stale `docs/data/terrain-1900.json`, so in the main checkout it fails on the known hash.
- The two checks that read factory data (`check_district_navigation`, `check_main_landscape`) pass.

## Smoke snapshot

The official command, `python3 scripts/review_smoke.py t6-leather-cloth --compare drawn-ground --url=http://127.0.0.1:4177`, failed twice for environmental reasons. The scene reached `ready`, but the hard-coded 60 s wait for the arrival tween to settle timed out under the software renderer, with other agents' headless browsers running at the same time. I ran an identical copy kept outside the repository, changed only to point `ROOT` at this worktree and to allow 900 s for the tween. The served docs were this worktree's, on port 4177, and the baseline was `smoke-drawn-ground.json` copied from the main checkout. The screenshot timed out, which the script treats as a courtesy. Result: 0 page errors and 11 differences, all from site 865:

```
destinationCount 128 -> 129            (one Factories destination per registered site)
factoryBuildings.chimneyTops           (+ stack-865-boiler-house only; no other entry changed)
factoryBuildings.chimneys 88 -> 89
factoryBuildings.ranges 697 -> 728
factoryBuildings.roofPlanes 1622 -> 1702   (+80 = 2 x the 40 roof bays of the new records)
factoryBuildings.siteChimneys.865 null -> 1
factoryBuildings.siteRanges.865 null -> 31
factoryBuildings.sites 63 -> 64
factoryBuildings.windows 9677 -> 10071
reflection.triangles / triangles +8,210
```

I re-ran the same copy after the final evidence-string edits (`smoke-t6-leather-cloth-final.json`). It gave the identical 11 differences and 0 page errors. Changing two record ids afterwards (`b865-south-road-shed-*`) does not affect the snapshot: building ids are not part of it, and the geometry audit and structural diff were re-run after the change.

## Footprint gap audit

`footprint_gap_audit.py` would read the git-ignored footprint source and write into `reference/photo-review-2026-10-03`, which belongs to the main checkout. So I ran copies kept outside the repository: they read this worktree's `docs/data` (and a baseline copy of it), read the source extract read-only from the main checkout, and write their reports to my scratch folder. The baseline run reproduces the published figures exactly (7,447 uncovered in started zones; site 865 at 43 / 7,521 m²).

| | Uncovered footprints at 865 | m² |
|---|---|---|
| Before | 43 | 7,521 |
| After | 7 | 43 |

The seven left are fid 802028 (27 m², not modelled; see below) and six fittings of 0.8–5.3 m². Chimney base 1061509 counts as covered by the stack.

Two side effects of registering the site:
- Across the district, uncovered footprints in started zones fall from 7,447 to 7,425 (218,446 → 211,372 m²). But "outside-sites" rises by 14 footprints and 403 m², because registering 865 grows the started zone over neighbouring terraces.
- "Model polygons without footprint support" rises from 120 to 123: the three traced roofs, as expected.

## Mapped versus estimated, in brief

- **Mapped:** every outline (45 supplied outlines, unshifted; three roofs traced from the OS hatching); the open square read as a chimney base; the site name; the reservoir.
- **Estimated:** every height, storey count, roof form, span count, pitch, material, chimney height and profile, and every function. No Goad sheet, photograph or document about this works was found in the repository or the reference folder, and none is cited.
- **Modelling cuts with no OS wall:** fid 150 split into hall, range, west bay and east spur; the traced block split into street range, wing and east shed.

## What I did not do

- Fid 802028 (27 m², GeoPackage class "compound") is not modelled. On the OS it is drawn as a crossed outline where the great shed meets the south-west yard. It may be a covered way or an open structure rather than a roof.
- Six fittings are not modelled: 1088836, 1025151, 1113424, 1115301, 1230246 and 1291498.
- The reservoir is not modelled as water or as a tank.
- A grey stippled patch south-west of the great shed, at the OS sheet join, has no supplied outline and is not modelled.
- I did not use north-light (saw-tooth) roofs. The renderer's `lean` multi-bay roof does not draw the vertical glazed faces.
- There are no ridge ventilators (the renderer has none) and no hipped roofs on the two houses (not a renderer option).
- I rendered nothing and did not touch the landscape, panorama or river builders.

## What I was unsure of

- Whether the hatched south block missing from the GeoPackage is one building or several. I chose three roofs.
- Whether fid 150, 3,838 m² with no drawn internal lines on a stippled sheet, is one shed. The split is for roofing only.
- The chimney reading of the open square in 24851. It is consistent with how the project treats small square bases elsewhere, but no OS label confirms it.
- The name of the south road. The site's yard surface and other layers do not name it.

## Judgement calls for the parent

1. **Traced roofs (2,014 m²) outside the 43-footprint list.** I added three OS-traced records (`b865-street-range`, `b865-l-wing`, `b865-east-shed`). The alternative is to delete those three records and leave the south frontage open. That would match the GeoPackage but not the OS, and the render would show a large empty strip where the OS is most built up. The three records are self-contained, and nothing else depends on them.
2. **Frame of the traced roofs.** I shifted them into the GeoPackage frame, (−1.75, +0.25) m, so they meet the supplied neighbours cleanly. The alternative is to leave them in the mosaic frame: they would then sit on the printed lines but overlap 4408 and 26347 by about 1.7 m.
3. **Splitting fid 150** into a 4-span hall, a 17.6 m single-span range and two lobes. The alternative is one record with ridges parallel to the arm and a single roof over the whole L.
4. **Reservoir range: one tall storey, 6.5 m (drying-stove reading).** The alternative is 5.5 m like the other sheds, or two storeys.
5. **Two-storey rule** for compact blocks of 150–300 m² (central block, yard block), the two houses and the street range. The alternative is one storey everywhere except the houses.
6. **Chimney at fid 1061509, 22 m square stack, boiler-house function for 24851.** The alternative is to model no chimney and give 24851 the generic small-building treatment.
7. **Merging touching cells into one record:** the 1 m strips into the boiler house, the porch into the house, the Abbey Road cells. The alternative is separate low records, or leaving them unmodelled.
8. **Fid 802028 skipped.** The alternative is a low roofed record of 3 m.

## Reproducibility

The register was generated by a scratch script kept outside the repository (`gen.py`). Its inputs:
- the GeoPackage extract (`west-ham-buffer-buildings-bng.geojson.gz`, read-only from the main checkout);
- the cached NLS tiles via `scripts/factory_map_sources.py`;
- the EPFL text layer.

The traced vertices and the registration shift are stored in the register, so the traced records can be checked without the script.
