# Reading guide: OS five-foot spot heights (1893–96)

You read the height figures on one 1024 px mosaic (zoom 18, about 0.37 m/px). Run the commands from `/home/jic823/book_website`. `R` is your reader name (`opus-c`), `M` is the mosaic (`m18_131063_87125`) and `D` is your scratch directory.

## Procedure

1. **Claim.** `python3 scripts/spot_height_manifest.py claim R 1`, or `assign R M` if you were given M.
2. **Joins.** `python3 scripts/spot_height_crop.py sheet M` lists OS sheet joins, where offsets may occur.
3. **Sweep.** `python3 scripts/spot_height_crop.py sweep M --out D` writes 9 crops (448 px, 2×, 160 px overlap), with a grid every 64 px in **mosaic** coordinates. Read every crop, list every candidate and add the crop's bounds to `crop_bounds_checked`.
4. **Zoom** on every candidate: `python3 scripts/spot_height_crop.py zoom M PX PY --out D` (6×, ±40 px; the crosshair marks PX,PY). Use `--scale 8 --half 30` for 3/8, 6/9, 1/7 and the dot. Confirm the digits, then find the dot or pheon and re-zoom on it.
5. **Write** `reference/spot-heights/readings/M.R.json` (schema below): write to `M.R.json.tmp`, then `mv`.
6. **Check** with `python3 scripts/spot_height_merge.py --check reference/spot-heights/readings/M.R.json` and fix what it reports.
7. **Mark done** with `python3 scripts/spot_height_manifest.py done R M`, or `release R M` if you cannot finish.

Do not run the full merge, edit `manifest.json` by hand, or touch other readers' files.

## Schema

```json
{
  "mosaic": "M", "reader": "R",
  "area": "...", "method": "...", "legibility": "...; sheet joins at ...",
  "crop_bounds_checked": [[0,0,448,448], [288,0,736,448], "..."],
  "readings": [
    {"type": "spot" | "bench_mark", "value_ft": 8.6, "raw": "8·6",
     "px": 96, "py": 261, "confidence": "high" | "medium" | "low",
     "setting": "street",
     "notes": "place; dot position; how confirmed"}
  ],
  "non_height_marks": ["milepost 'Ilford 4 / London 3' at 210,300"],
  "unreadable_regions": [
    {"px0": 1000, "py0": 490, "px1": 1024, "py1": 515, "reason": "figure cut by east edge"}
  ]
}
```

`px, py` is the **survey dot** for a spot height, or the **point of the pheon** for a bench mark, not the text centre. If you cannot find the dot, give the centre of the figures, say so in `notes` and use at most `medium`.

## Setting field (required from now on)

Every reading needs a `setting`: the kind of ground or structure the height describes. The project wants low marsh ground, street levels and the points either side of embankments, with wall tops and bridges kept separate. Use exactly one of these values:

- `marsh`: low wet ground only. This means ground named as marsh, meads, mead, level, moor or osier bed, grazing beside the foreshore, or open ground in the Lea, Channelsea or Bow Creek valley below about 15 ft.
- `open_ground`: parks, recreation grounds, fields, gardens, allotments, nurseries, brick fields, cemeteries and churchyards, and any other unbuilt ground on the terrace.
- `street`: road, lane, pavement or street corner, including tramway streets.
- `yard`: works yard, goods yard, station yard or forecourt, or made ground inside premises.
- `embankment_top`: the crest of a railway, sewer or flood bank, or a towing path on a bank. Locate the survey dot on that surface; nearby foreshore or marsh does not count merely because it adjoins a bank.
- `embankment_foot`: ground at the foot of a bank.
- `wall_top`: river wall, quay, lock side or canal wall, including figures written over a channel with the dot on the wall.
- `bridge`: bridge deck, approach ramp, or a B.M. on a parapet or abutment.
- `railway`: a dot on the rails at grade, not on an embankment.
- `building`: a B.M. on a building or ordinary wall at street level, or a figure written on a building.
- `water`: a genuine water level. None has been found so far.
- `other`: none of the above. Say what it is in `notes`.

Rules:

- **Classify by what the dot or pheon stands on**, not by where the lettering is.
- **Check both sides of bank hatching.** A dot in the adjoining marsh is a marsh-ground observation, not a bank crest. A dot on the slope or margin is not automatically its highest point. Describe the precise position in the notes. A benchmark cut on a bank face is not automatically a ground level at the foot.
- **`marsh` or `open_ground`: go by the place word first.** Marsh, meads, level, moor and osier bed are `marsh`. Park, field, garden, allotment, nursery, brick field, cemetery and recreation ground are `open_ground`, even in the valley. When the map gives no place word and the ground is just open, use the value: below 15 ft is `marsh`, and 15 ft or more is `open_ground`. The merge applies the same rule to old notes that say only "open ground", and flags those marks `setting_rule: "value_fallback"`.
- **A bench mark on a bridge parapet (or abutment) is `bridge`. A B.M. on an ordinary wall** (house, church, works or boundary wall) **is `building`.**
- **A figure at the foot of an embankment is `embankment_foot`, even if it is on a road.**
- On rails, the setting depends on the ground. Rails at grade are `railway`, and rails on an embankment are `embankment_top`. Tram rails in a street are `street`.
- A figure written directly under a B.M. with no dot of its own (the ground level at the B.M.) takes the setting of that ground, usually `street`.
- Keep describing the place in `notes` as before. `setting` does not replace `notes`.
- `--check` rejects any value outside this list. Readings written before this field existed have their setting inferred from `notes` at merge time (`setting_source: "inferred"`). Your value is recorded as `"reader"` and takes precedence.

## Rules from the prototype

- **Digits are about 6 px tall.** 2× finds them; 6–8× confirms 3/8, 6/9, 1/7 and the decimal.
- **Dot versus middot.** The decimal is a middot (`8·6`). The survey dot is separate, left, right or above the figure. The middot is never the position.
- **Bench marks** are written `B.M.` with a pheon, to **2 dp** (`B.M.10·79`). **Spot heights** are **1 dp**. If a value breaks this, re-zoom; if it still does, give it `low`.
- **Plausible range depends on where you are.** In the Lea valley and the marshes expect 0–50 ft (marsh 6–8, streets 8–22, walls 16–19, sewer bank about 31; bridges over railways up to about 49). The ground climbs the gravel terrace to the north and east, so around Forest Gate, Upton, Leytonstone and Wanstead Flats values of 60–100 ft are normal (82·5 has been seen in the north-east). Southwards, on Plaistow Level, Canning Town and the Thames-side marshes, the ground drops to 3–5 ft and 4·0 or lower is normal; a small value is not a misread. Re-check anything outside the range for its setting, but do not lower a clear high value because it looks large.
- **Figures over channels need their dots traced to the measured surface.** A dot on a wall may establish a wall height; lettering over water alone does not. Do not infer a water level from text placement. No genuine water-level marks have yet been identified in this collection.
- **NOT heights:** mileposts ("Ilford 4 / London 3"), house numbers, acreages (`1·234`), parcel numbers, S.P., F.P., W.M., F.B. and rotated "Towing Path" lettering. Put notable ones in `non_height_marks`.
- **Sheet joins** cause 1–2 px offsets and tint changes; zoom on figures that cross one.
- **Grey fill is a missing tile**; pure white is off-sheet. Record both in `unreadable_regions`.
- **Edges.** Record every figure that is whole inside the mosaic, including in overlap strips; the merge removes duplicates. A figure cut by the edge goes in `unreadable_regions`.
- **Confidence.** `high` means unambiguous digits at 6×+ and the dot found. `medium` means one digit or the dot is uncertain. `low` means plausible only. **Prefer `low` to a guess**: low readings go to review, while a wrong `high` poisons the data. Never invent a value.

## Worked example

In crop r0c0, `B.M.10·79` sits at about 350–380, 255–265. `zoom M 390 253` shows clear digits and the pheon point at 390,253.

```json
{"type": "bench_mark", "value_ft": 10.79, "raw": "B.M.10·79", "px": 390, "py": 253,
 "confidence": "high", "setting": "building",
 "notes": "building by the Northern Outfall Sewer; pheon right of text, confirmed at 6x"}
```

`8·7` is legible, but no dot is visible even at 8×:

```json
{"type": "spot", "value_ft": 8.7, "raw": "8·7", "px": 499, "py": 243, "confidence": "medium",
 "setting": "street", "notes": "road north of the sewer; dot not found, position = centre of figures"}
```

## Field notes from readers (added 2026-09-28, from opus-b)

- **Interpuncts in spaced street lettering act as survey dots.** In names like `H·A·N·C·O·C·K R·O·A·D` a figure is often placed beside one of the middots, and that middot is the survey dot. Record as `medium` and name the letters in `notes`.
- **On tramway and railway streets the dot sits on a rail** and reads as a tick or thickening of the rail line. Do not class these as missing dots.
- **Most dots in towns are not survey dots.** `F.P.`, `F.A.`, `H`, `C.`, `S.P.`, `S.B.` each carry their own dot, and the dash-dot county boundary along the Lea is full of dots. Never attach a figure to one of these.
- **Figures on foreshore or mud beside an embankment are embankment-top heights** (dot on the embankment). No water levels have been found on these sheets.
- **B.M. text can sit 20–50 px from its pheon, and figures over buildings may have no dot.** Search at least a 120 px window at 4× before recording the position as estimated.
- **Zoom in two steps.** 6× on an 80 px window finds dots; separating 3/8, 6/8, 9/2 needs 8–10× on a 36–50 px window. Persistent cases are `low`.
- **Look-alikes.** Rotated lettering such as the `ing` of `Towing Path` can pass for `11·9` at 2×. Check every candidate at zoom.
- **Edge figures** cut by the mosaic edge belong in `unreadable_regions`; they are usually whole in the neighbouring mosaic.

## Field notes from readers (added 2026-09-28, from opus-c)

- **Railway spot heights: the dot is on the rails**, with the figures written 20–35 px to one side outside the embankment hatching. Look for an isolated dot on the rails before recording "no dot".
- **Pheons can be 30–40 px from the B.M. text, even across a road.** Search at 6× over ±40 px around the text before placing a bench mark at its text.
- **Settings and levels seen so far:** open marsh 6–11 ft; made streets 12–16; river walls and banks 14–19; GER running lines 15–17, Stratford Works 21–24, station B.M. 27·63; sewer bank 31; rail-over-rail bridges to 49.
- **The `sheet` command misses weak joins.** Look for straight lines with a tint change yourself even when it reports none.

## Hard rule: an image you did not see does not exist (added 2026-09-28)

If the Read tool returns anything like `[media removed: request limit]` or otherwise fails to show the image, you have NOT seen that crop. Stop reading that mosaic at once. Do not write or keep any reading derived from an unseen image, do not mark the mosaic `done`, and report the failure in your hand-back with the mosaic name and the crops affected. Writing readings you did not see is the one failure that poisons the dataset. If it happens, re-open the crops later or leave the mosaic for another reader (`python3 scripts/spot_height_manifest.py release <reader> <mosaic>`).

State in the `method` field of every JSON that all crops and zooms were viewed successfully.

## Field notes from readers (added 2026-09-28, from opus-d)

- **Railway figures are often written below the embankment hatching**, with the dot 25–35 px away on the rails; record as medium with the dot noted as inferred if you cannot see it.
- **In goods yards figures often sit on the corner of a shaded yard with no dot.** Position = centre of figures, medium.
- **A small triangle with a centre dot is a survey station.** A figure beside it is a spot height whose position is the triangle's centre; record it as such and say so in `notes`.
- **Figures ending within 2–3 px of the mosaic edge** may have a clipped trailing digit: record in `unreadable_regions` as well as the reading, and lower confidence.

## Field notes from readers (added 2026-09-28, from opus-e)

- **F.P. marks in dense terraces sit right against figures.** If the only nearby dot could be the F.P.'s own trailing dot or a street-name interpunct, record the height as `medium` and do not treat that dot as the survey dot.
- **More settings:** Stratford station platforms 21–23 ft; Angel Lane bridge approach climbs 30 → 39 with a parapet B.M. at 40·27; Lea towing path 22–24·5, well above the marsh beside it; Carpenter's Road and Woolwich Road terraces 12–15 on made ground.
- **A weak horizontal sheet join runs across the 87128/87131 mosaic rows** at about py 938 (87128) / py 170 (87131). The `sheet` tool does not report it.

## 25-inch gap-fill mosaics (q18_*)

Where the five-foot has no sheets (the hole east of the Channelsea, and edge rows) there are `q18_*` mosaics cut from the OS **25-inch (1:2,500)** County Series on the same lattice. They live in `reference/spot-heights/mosaics-25inch/`, are tier 4 (zone `gap_fill`) in the manifest, and the edition is **inferred** to be the 1893–96 revision (see `edition_notes` in `mosaics-25inch/lattice_index.json`). The commands are unchanged: `claim R 1 --layer q18` (or `assign R q18_…`), then `sheet`, `sweep`, `zoom`, `--check` and `done`, all with the `q18_…` name. The tools find the folder from the prefix. Write `readings/q18_X_Y.R.json` with the same schema.

- **Digits are about 12–14 px tall**, twice the five-foot size. 2× finds everything, and 4–6× on a ±40 px window confirms it.
- **Spot heights are whole feet** in small italic figures (`4`, `8`, `31`), beside a small `+`, `×` or dot on the road, path or bank. That mark is the position. Record them as `"raw": "31"`, `"value_ft": 31`. They have **no decimal**, so do not invent one.
- **Bench marks** are `B.M.` + pheon to **1 dp** (`B.M.32·4`). The pheon point is the position.
- **Not heights:** upright parcel numbers (`104`) and acreages to 3 dp (`4·818`, `·653`); `B.S.`, `B.P.`, `C.R.`, `C.S.`, `S.P.`; triangles.
- Sheet joins are thin straight lines with the acreage repeated on both sides.
- Values are still **feet above OD (Liverpool)**. The merge may combine a q18 mark with the same mark on an m18 mosaic, and a whole-foot `8` agrees with `8·3`.

## 1848–51 skeleton mosaics (s18_*)

The `s18_*` mosaics in `reference/spot-heights/mosaics-1848/` come from the **OS London 1:5,280 skeleton survey of 1848–51** (the Metropolitan Commission of Sewers levelling). They cover the whole extent on the same lattice and are tier 5 (zone `skeleton_1848`), in the same Olympic Park → Abbey Mills → outward order. Use `claim R 1 --layer s18` and the usual commands with the `s18_…` name.

- **It is a levelling map.** Figures and B.M.s sit along roads, drain banks, sewers and river walls. The marsh interior is blank paper, so many mosaics have no readings; write the file with `"readings": []`.
- **Digits are about 7–8 px tall** in fine grey-brown engraving, with a heavy middot that is often spaced (`8 · 6`). Read at 6–8×. Spot heights are **1 dp**, and the survey dot is a separate small dot beside the figure.
- **Bench marks are 1 dp** here (`B.M.16·6`), not 2 dp.
- **Datum.** No datum note appears on the tiles. The sidecar `datum` records it as OD Liverpool **by inference**, because its B.M.s agree with the 1890s values to a few tenths of a foot (see `datum_notes` in `mosaics-1848/lattice_index.json`). Report the figures as written.
- **Separate observations.** The merge never combines an s18 mark with an m18 or q18 mark, even at the same spot. The 1848–51 levels are an earlier survey, and the landscape (railways, Abbey Mills, the docks) changed in between. Each mark carries `layer`, `source`, `survey_dates` and `datum` from its sidecar, and skeleton marks get ids `sk_E_N`.

## Field notes from readers (added 2026-09-28, from opus-f)

- **Always check for sheet joins by eye.** The `sheet` tool missed two of four joins in one batch; horizontal tint steps near py ~737–742 recur across the 87122 mosaic row.
- **A flat-based 2 reads as 3 at 2×** on yard corners; confirm at 10–14× before recording.
- **North Stratford reaches 30–37 ft** (Temple Mill Lane bridge B.M.36·56, Chobham Road 31–35, Major Road 25–30). Do not doubt these values.
- **Contact sheets save image loads.** Combine several zoom panels into one image, each panel labelled with its mosaic-pixel window. A small helper script in your own scratch directory is fine.

## Field notes from readers (added 2026-09-28, from opus-h)

- **Recurring joins:** horizontal near py ~937 on the 87128 row and py ~738 on the 87122 row; vertical at px ~546 on the 131054 column. Expect them even when `sheet` is silent.
- **An F.P.'s own dot can sit on either side of the letters** (`·F.P` or `F.P·`). A figure whose only nearby dot lines up with an F.P. is `medium`.
- **Survey-station triangles often have no figure beside them.** Only record a height when a figure is actually there.
- **Real heights sit between the letters of rotated "Towing Path" lettering** on the Hackney Cut (21·7–22·6). Zoom before dismissing them as look-alikes.

## Field notes from readers (added 2026-09-28, from opus-j)

- **A figure written directly under a B.M. value with no dot of its own is the ground level at the bench mark** (e.g. B.M.25·88 over 23·6). Record it as a spot height, `medium`, at the centre of the figures.
- **Interpunct rule refined:** a dot after the last letter of a street name (`R·` in HENNIKER, `D·` in ROAD) is not an interpunct and can be the survey dot. A dot between two letters is ambiguous: `medium`.
- **6 versus 8 is as common a confusion as 3 versus 8** on these sheets and often stays ambiguous at 12×. Use `low`.
- **The `sheet` tool can report hatching as a join.** Confirm any reported join by eye before recording it. The vertical join at px ~546 on the 131054 column is real and the tool misses it.

## Hard rule, strengthened (added 2026-09-28 after a third incident)

Three readers have now written readings from images that were never shown to them. Each time the Read tool returned `[media removed: request limit]` for every image of a mosaic, and the reader carried on as if it had seen them. The damage was caught only by luck (a mismatch in an overlap strip). So:

1. **Open images one or two at a time and look at each result before the next step.** A blocked result is easy to miss when several are opened together.
2. **If any image is blocked, stop.** Wait about 90 seconds (`sleep 90`) and re-open it. The block has cleared within a few minutes every time so far. Retry up to three times.
3. **If it is still blocked, release the mosaic** (`python3 scripts/spot_height_manifest.py release <reader> <mosaic>`) and move on. Never write a JSON for it.
4. **Before writing any JSON, list in `method` the crops and contact sheets you viewed** and state that every one of them displayed. If you cannot say that truthfully, do not write the file.
5. **Never mark `done` a mosaic whose images you did not all see.**

## Field notes from readers (added 2026-09-28, from opus-i)

- **5 versus 6 in small figures:** the 5 has a flat top bar, the 6 a rounded top. Confirm at 20–24×.
- **A small "5" beside a boundary-stone mark is not a height.**
- **Boundary lines drawn as rows of dots** (Leyton Road, Temple Mill Lane) hide survey dots; place such figures at their centre, `medium`.
- **Joins:** horizontal at py ~538–543 on the 87116 row; vertical at px ~68 on 131066_87116; py ~742 on 131072_87122 is real.

## Correction to the hard rule: "[media removed: request limit]" in your history is NOT a load failure (added 2026-09-28)

Four readers have now "discovered" that images they worked from were never shown to them, withdrawn their files, and re-read. In every case the withdrawn readings matched independent readers on 93–100% of marks. They were real. What happened is this: after you have viewed many images, older ones are dropped from your context and replaced by the placeholder `[media removed: request limit]`. When you later look back through your own history you see the placeholder and conclude you never saw the image. You did. The placeholder is an artefact of memory, not of loading.

So the rule is now:

1. **Judge each image at the moment you open it.** If the Read result shows you the picture, you have seen it; read what you need from it there and then, and write your candidate values down in your notes immediately, because the image will not stay in your context.
2. **A load failure is a Read result that shows no picture at the time you open it.** Only then: wait, retry, or release the mosaic.
3. **Do not withdraw or re-read a mosaic because earlier images in your history now show the placeholder.** Trust the readings you wrote at the time. If you have doubts, say so in your hand-back and the coordinator will run the overlap check and, if needed, order an independent second read.
4. Keep the habits that help: one or two images per step, values noted at once, a marker sheet to check positions.

## Field notes from readers (added 2026-09-28, from opus-k)

- **Upton (E 540400–541000, N 184100–184700) is a flat gravel terrace at 31–36 ft**; bench marks on walls 33·5–36·4. The survey dot there is usually written directly above the figure.
- **Plashet Road boundary is plain dashes**, so a single dot beside a figure is its survey dot (`high`). **Gipsy Lane / C.R. boundary is a line of large dots**; figures there get `medium`.
- **A marker sheet** (a box drawn on the mosaic at each recorded pixel, then viewed) catches 2–12 px position errors cheaply.

## Field notes from readers (added 2026-09-28, from opus-m)

- **The small italic 3 renders like an 8 or 9 at 14–24×** on the Upton sheets. High zoom alone cannot settle a final 3/8/9; compare the doubtful digit with a known digit in the same figure at about 16×.
- **Zoom can flip a 6/8 reading.** LANCZOS upscaling at 16–24× can close the top of a 6. Take 6/8 readings at 8–10× and mark `low` if two zoom levels disagree.
- **Gipsy Lane / Green Street:** large boundary dots at 9–10 px spacing plus interpunct lettering. A survey dot is often the extra dot that breaks the regular spacing; record as `medium`.
- **Bench-mark pheons on the terrace sit 15–45 px from their text.**

## Field notes from readers (added 2026-09-28, from opus-l)

- **Anchor each sweep crop as you open it:** write one concrete visible detail (a street name, a building label) into your notes for each crop before moving on. It proves to yourself later that the crop displayed, and it stops the "did I see it?" doubt that has cost four readers a re-read.
- **Autocontrast makes italic 3s and 6s look like 8s.** Use contrast stretching to find dots, never to decide a digit.
- **Italic 3s have looped tops** that read as 8 at 20–30×. Compare with another 3 on the same sheet before doubting one.
- **Upton plateau:** 32–35 ft with wall bench marks at 36–38 (highest so far B.M.37·99 at Meggs' Almshouses); West Ham Park 29·6–30; Dacre Road down to 25.

## Field notes from readers (added 2026-09-28, from opus-n)

- **Check positions with a marker sheet before marking done.** Reading positions off the tick labels of 8× contact sheets gave 2–11 px errors on every mosaic; the marker sheet caught them all.
- **Blocky (nearest-neighbour) versus smoothed zoom can disagree on 5/6 and 3/5.** When they disagree, record `low`.
- **More settings:** Pelly Road / Dacre Road pocket 25–28 ft; the open field west of Percy Road 29·9–31·4; Upton Park station roads 28–30; Green Street railway bridge approach climbs to 35·7.

## The mechanical test for "did I see it?" (added 2026-09-28, after a fifth false alarm)

Five readers have now reported that images "never displayed", including one who was sure the placeholder came back at the moment of opening. In every case the overlap check showed their readings matching independent readers on 93–100% of marks. The readings were made from real pictures; the memory of the event was wrong. So do not rely on memory at all:

- **The moment you open a crop, write its anchor into your notes file** (a street name or label you can see, e.g. `r1c2: HAM PARK ROAD, church`). Do this before anything else. If a crop truly shows no picture, you will have nothing to write, and THAT is the only signal that counts as a load failure.
- **A file whose crops all have anchors was read from real images.** Do not withdraw it later, whatever your history looks like.
- If you finish a mosaic and find a crop with no anchor, re-open only that crop.

## Field notes from readers (added 2026-09-28, from opus-o)

- **Compare a doubtful final digit with the leading digit of the same figure at 8×** (the 3 of 3x·3); keep 16–20× for 5/6 and 0/6.
- **The G-shaped italic 6 differs from the oval upright 0**; several figures read as x·0 at 2× are really x·6.
- **West Ham Park** falls from about 34 ft on Ham Park Road to 27·5–28 in its south-west corner. **Forest Gate / Romford Road** 32–34, easing to 31 at Henderson Road.

## Field notes from readers (added 2026-09-28, from opus-p)

- **Recurring joins:** py ~376–378 on the 87137 row; py ~185 on the 87131 row; py ~951 on the 87128 row. The `sheet` tool reports false vertical joins on dense terrace hatching.
- **Interpunct lettering:** ST. STEPHEN'S and PLASHET have interpuncts; YORK, CHESTER, REDCLYFFE, LANE and GROVE do not, so a dot beside a figure there is more likely the survey dot.
- **A 2× sweep crop can turn italic 0 and 3 into 8 or 9** (B.M.30·30 read as 80·30 at 2×). Always confirm the leading digit at 12× or more.
- **Plaistow north:** 25–28 ft north of the Southend Railway, 23–24 around Queen's Road and St Mary's Road; bridge approaches are local highs (35·7, B.M.35·23).

## Field notes from readers (added 2026-09-28, from opus-q)

- **Matching digits in the same figure are the same digit.** On the Romford Road sheets (87122 row) every italic 3 renders as 8 at 10–14×; 33·3 and 33·4 were settled this way. A final 3 or 8 standing alone stays `low`.
- **Recurring join** at py ~738–748 on the 87122 row; the tool reports false vertical joins on the 87137 row.
- **Settings:** West Ham Park south-edge road 28–31 ft; Park Road / Pelly Road / Terrace Road pocket 22–27; Milton Road South 19·7; Pelly Road bridge over the LT&SR B.M.31·12.

## Field notes from readers (added 2026-09-28, from opus-r)

- **Marks in the overlap strip of two mosaics you read yourself are duplicates, not confirmation.** Only another reader's file is independent.
- **Romford Road tramway rails carry regularly spaced dots**, like the Gipsy Lane boundary; figures beside them are `medium` at the centre of the figures.
- **PLASHET interpuncts** also apply to Plashet Road (131099 column).
- **Settings:** Woodgrange / the School / Shrewsbury Road 33–35 ft with wall B.M.s to 37·34; Green Street falls south from 31·8 to 27 at Boleyn Castle; Plashet Road bridge over the LT&SR 36·6–37·5.

## Field notes from readers (added 2026-09-28, from opus-s)

- **Recurring joins:** vertical px ~650–656 on m18_131084_87122; the 87128/87131 row join also appears at py ~944 / ~176 on the 131081 column.
- **Interpunct lettering:** T·E·R·R·A·C·E, R·O·A·D (Pelly Road), P·A·R·K ROAD, N·O·R·W·I·C·H. GROVE, CLOVA, STRATFORD and ROAD on Ham Park Road have none.
- **Settings:** The Grove / Norwich Road, Forest Gate 34–37 ft (B.M.37·17); Portway 26–27; Park Road and Stratford Road, West Ham 18–22, down to 14·3 near Valetta Grove.
- **Keep the marker-sheet rule.** It corrected 4–7 positions per mosaic, one by 12 px.

## Field notes from readers (added 2026-09-28, from opus-u)

- **Confirm bench-mark decimals at 12×.** A 2× sweep turned B.M.16·94 into 16·04; italic 9 becomes 0 as easily as 3 becomes 8.
- **Portway:** the dash-dot "Parly. Boro. & Ward Bdy." line carries dots and ticks against the figures; place those at their centre, `medium`.
- **Lone-digit rule clarified:** a final 8 that clearly differs from a leading 3 in the same figure is NOT alone; it may be `high` if the difference is plain at 12×.
- **Interpuncts:** HARBERSON (R·B only), B·O·L·E·Y·N, P·R·I·O·R·Y, W·A·R·W·I·C·K. TUDOR, VAUGHAN, ALICE, SHREWSBURY have none.
- **Settings:** Harberson Road 19–20 ft; Park Road and Stork Road, Plaistow 14·6–17; Plaistow Grove and Ann Street 12·4–14; Priory and Boleyn Roads 25–27.

## Field notes from readers (added 2026-09-28, from opus-t)

- **Plaistow the village (streets around Broadway, North Street, St Mary's Road) is 20–24 ft**; wall B.M.s there 22·8–28. The 3–5 ft figures in the earlier range note refer to Plaistow Level, the marsh south of the LT&SR toward Canning Town and the Thames, not to the village.
- **Forest Gate north reaches about 40 ft (B.M.40·82 at the Woodgrange Road club)**, not 60–100; the higher terrace is further north-east toward Wanstead Flats.
- **Interpuncts:** W·ESTERN, SO·UTHERN, CR·EDON, A· in ST MARY'S. **Recurring vertical joins** px ~942 on 131093_87119 and ~932 on 131093_87140.
- **B.M. text can sit across the street from its pheon** (55 px). **Contact-sheet panels need ±12–14 px** around a figure centre or edge digits get clipped.

## Field notes from readers (added 2026-09-28, from opus-v)

- **South-west marsh tier levels:** Canning Town streets 4–9 ft; Bow Creek walls 16–18; wharves 16–19 with wall B.M.s 18–19·4; Barking Road 26 on its embankment, 34·5 at the Iron Bridge, 17–17·6 over the station railway; the G.E.R. goods depot is made ground at 17–19·5, not marsh.
- **Embankment pairs exist here:** e.g. Barking Road 26·1 on the carriageway and 16·1 at the foot by the steps. Record both, `embankment_top` and `embankment_foot`.
- **Joins:** horizontal py ~195 on the 87158 row / ~962 on the 87155 row (columns 131072–131075); vertical px ~346 on 131075_87158.
- **Contact-sheet tick labels misled positions by 3–19 px.** Use a numeric dot-centroid helper and the marker sheet to fix them.
- **Interpuncts:** TUCKER·STREET, STEPHENSON (P·H), WELLINGTON (G·T).

## Field notes from readers (added 2026-09-28, from opus-w)

- **Approach ramps:** a hatched earth ramp or bank carrying a road up to a bridge is `embankment_top` (its foot is `embankment_foot`); the masonry approach, deck and parapet are `bridge`. The Iron Bridge over Bow Creek is the type case: 14·4 street at the base, 16·7 and 26·1 on the earth ramp (embankment_top), 34·5 deck and B.M.31·48 parapet (bridge), 16·1 on the wharf at the ramp foot (embankment_foot).
- **M.P. (mooring post) figures at wharves are not heights.**
- **Recurring join:** py ~964–966 on the 87155 row = py ~197 on the 87158 row; the tool misses it.
- **Canning Town streets 3·3–9 ft are laid directly on the marsh**; the riverside wharves and Orchard Place stand 7–12 ft higher on made ground (15–19·5). A value of 16–19 at the Bow Creek edge is real.
- **Cover every strip.** The overlap check compares your edge strips with the neighbours; a strip with far fewer marks than the neighbour's is flagged. Sweep the edge crops as carefully as the centre.

## Field notes from readers (added 2026-09-28, from opus-y)

- **The 87158-row join (py ~196–198) extends east at least to column 131081**; the tool misses it.
- **Interpuncts:** EXING (X·I), BEACONSFIELD (E·A), BLANCHE (N·C), HERMIT (E·), INDIA (N·D, I·A), EAST (T·), BENLEDI (B·E), ORCHARD STREET.
- **F.P. with two dots** on the Bromley/Poplar sheets: the F.P.'s own dot plus a separate survey dot; the second is the true position.
- **Levels:** Hallsville / Exing Road / Beaconsfield Road 2·9–3·6 ft, Forty Acre Lane 3·7–4·5, the lowest streets read so far; Bow Creek walls 17·2–17·9 over inland ground of 5·7–6; Poplar dock-side made ground (East India Dock Road, Orchard Street) 14·5–18.

## Field notes from readers (added 2026-09-28, from opus-x)

- **Joins:** the 87158-row join (py ~197) also runs west onto column 131069; the vertical px ~347 join also appears on 131075_87152.
- **Hallsville Road varies by location:** near Newton Street it is 7·6–7·8 ft; the 2·9–3·6 range belongs to Exing Road and Beaconsfield Road further east.
- **Interpuncts (Canning Town):** ..CK STREET (K·S), STREET (R·E), VICTORIA (O·), HALLSVILLE (S·), ARKWRIGHT (R·), MANOR (R·), ROAD (D· on Manor Road).
- **6/8 runs both ways:** a 6·x at 2× and 8× can be 8·x at 22×. Compare with a known 6 and a known 8 on the same sheet.
- **Raised school grounds** (13·3–13·4 over 7·5–8·3 streets) are made ground: use `yard`.
- **Walled masonry ramps** rising to a bridge are `bridge`; hatched earth ramps are `embankment_top`.

## Field notes from readers (added 2026-09-28, from opus-z)

- **B.M. first decimals 8/9 flip at 12×** (8·86 vs 9·86). Check at 20× and against the raw pixels, not 12× alone.
- **A closed lower bowl turns 5 into 6 in small upright figures** (10·5 vs 10·6); compare with a known 5 on the same sheet, else `low`.
- **No interpuncts:** BECKTON ROAD, LANSDOWNE ROAD, BOYD ROAD, STAR LANE. **Interpuncts:** O·R·C·H·A·R·D, S·T·R·E·E·T (Mary and Lawrence Streets), P·L·A·C·E.
- **Joins:** py ~393 on the 87164 row (tool misses it on 131072); px ~345 on the 131075 column.
- **Levels:** Canning Town interior streets 3·7–5 ft; Leamouth / Orchard Place / Orchard Street 10·5–18 on made ground; East India Dock quays 15·6–17·5.

## Field notes from readers (added 2026-09-28, from opus-aa)

- **Smoothed zoom at 22× closes the top of an italic 5**, so 5·5 can look like 6·6. Judge 5/6 at 8–12× against a flat-topped 5 on the same sheet; if 12× and 22× disagree, record `low`.
- **B.M. pheons on a fence line or road edge with no wall drawn** stay `other`; say "fence" or "kerb" in `notes`.
- **Joins:** py ~391 on 131078_87164; py ~768 (ditches blue north of it, uncoloured south) and px ~350 on 131075_87149; vertical tint step px ~347 on 131075_87152.
- **Levels:** Canning Town NE (Blanche Street, Chargeable Street) 3·6–4·5 ft; works yards on the marsh edge 15–17·65 (Thames Iron Works 16·2), 10–12 ft above the marsh.

## Field notes from readers (added 2026-09-28, from opus-ab)

- **Take 6/8 at 6–8×** on the Canning Town marsh sheets; 10× and above closes the top of a 6 (even the known 6 of B.M.16·68).
- **Joins:** the py ~964–966 join on the 87155 row runs across columns 131066–131081; on 131072_87149 the strong join is at py ~765–767.
- **G.P.O. figures (e.g. "G.P.O. 4¼") are not heights.** MORGAN has an interpunct after the G.
- **Manor Road embankment pairs:** 4·0–4·2 at the ramp foot against 11·6–13·5 on the hatched ramp, deck 20·8–21·2, east approach falling 20·8 → 11·7 → 6·1.
- **Levels:** open marsh and Canning Town / Poplar interior streets 4–9 ft; made ground (river walls, wharves, dock quays, Wall Road, Orchard Street) 15–20·6.

## Field notes from readers (added 2026-09-28, from opus-ac)

- **Joins:** vertical px ~637 on 131084_87158 and probably px ~57 on 131066_87161; the py ~768 join also on 131078_87149; py ~388–391 across the 87164 row.
- **Interpuncts:** L·A·N·E (Forty Acre Lane), R· in FORD'S PARK ROAD, A· in VICTORIA, U·N and C·K in BRUNSWICK.
- **6/8 in B.M. second decimals** flips between zoom levels even when the leading 6 of the same figure is clear; compare the raw pixel profile with that leading 6, and leave it `low` if still unsettled.
- **Levels:** ditch banks and open marsh north of Canning Town 2·9–3·5 ft, the lowest yet; Hermit Road / Beaconsfield Road / Hoy Street 2·9–6·6; Poplar interior streets 7–9·7; East India Dock Road 14·9–16 on made ground.

## Field notes from readers (added 2026-09-28, from opus-ad)

- **Joins:** vertical px ~637 continues on 131084_87155; horizontal py ~767 on 131069/131072_87149; vertical px ~342 on 131075_87167 running into the river.
- **Custom House E–W road is lettered R·O·A D·** (no dot between A and D).
- **Leamouth wharf frontages:** dots are inseparable from mooring-post dots; expect `medium`.
- **Contact-sheet centring:** centres estimated from 2× sweeps tend to fall 5–10 px left of the figure; centre panels on the figure's right half.

*Coordinator's note:* field notes should give typical ranges by setting, not exact values for named marks, so that later QA second reads stay blind. Earlier notes that quote exact values are left as they are, but QA mosaics are now chosen to avoid them.

## Field notes from readers (added 2026-09-28, from opus-ae)

- **False joins:** the tool reports "LIKELY" vertical joins on hatched school blocks (131081_87149). **Missed joins:** px ~634 on 131084_87161; px ~57–59 on the 131066 column.
- **6/8 on the gas-works and iron-works sheets:** figures that read 18·x at 2× often show an open-topped 6 at 7–12×. Compare with a closed 8 in a B.M. on the same sheet.
- **False dot:** the ball end of an italic C (e.g. in BUTCHERS) looks like a survey dot; check raw pixels.
- **Interpuncts:** HERMIT ROAD (O·A, H·E), CHARGEABLE (R·G), SUFFOLK (F·O).
- **Typical ranges by setting on the marsh edge:** made-ground works (gas works, iron works, dry docks) 16–21 ft beside open ground at 6–9; wharves 14–18; marsh roads run 2–3 ft above the marsh beside them.

## Field notes from readers (added 2026-09-28, from opus-af)

- **Check each candidate's position with a 5–8× region view before building contact sheets;** centres read off the 2× grid can be 12–20 px out.
- **Plaistow Level:** B.M. pheons sit on long fence or drain lines across the marsh; record those bench marks as `other` (say "fence") and the spot dots on the same line as `marsh`.
- **Quays:** figures under "Crane" labels have no survey dot of their own (the only dot is the crane pivot); `medium` at the centre of the figures.
- **Typical ranges, Poplar / Blackwall:** interior streets 8–13 ft; East India Dock Road tramway 15–16; dock quays and premises 17–20 (B.M.s to 22); graving-dock and river walls 15–18; road bridges over the railway 23–24.
- **Joins:** vertical px ~637 on 131084_87152; horizontal py ~392 on 131066_87164.

## Field notes from readers (added 2026-09-28, from opus-ag)

- **Joins:** vertical px ~633–634 runs the full height of the 131084 column (87161, 87164); vertical px ~824 on 131063_87158; the tool's other "LIKELY" joins on 131084_87164 are false.
- **Interpuncts:** VICTORIA DOCK ROAD (I·A, C·K), W·O·O·L in NORTH WOOLWICH ROAD, L·E in ST LEONARD, R·U / C·K in BRUNSWICK, T·T in ABBOTT, L·L in HALL, a dot before the R of RIVETT.
- **B.M.s on marsh-drain kerbs and railway fences** are common on the Abbey Mills marsh, sometimes a pheon in a small diamond: `other`.
- **Typical ranges:** open marsh 4–5 ft; marsh tracks 6–7·5; Canning Town streets 5–7·5; Poplar interior streets 8–10; sidings on a bank 11–12; railway bridge approaches 13–17; goods-depot made ground and dock quays 16–19·5.

## 25-inch field notes (added 2026-09-29, from opus-ak)

- **Figures sit 20–40 px from their + or × marker,** sometimes across a fence line; pair each figure with the nearest isolated cross and say so in `notes`. The crosses are plainly different from dotted-boundary dots.
- **Not heights on this layer:** parcel numbers and acreages (e.g. `5 / ·653`, `51·488`) with their braces and arrows; S-shaped tie marks on drains; the dots of "Stone" and "Post" labels.
- **Blank marsh sheets are normal**; an empty reading file is a valid result. Sweep all nine crops anyway.
- **Legibility:** italic whole feet 12–14 px tall, legible at 2×; 5× contact sheets settle nearly everything. No 3/8 or 6/8 trouble so far.
- **Join:** py ~780 on 131096_87149 = py ~12 on 131096_87152 (tool misses it). Typical ranges on the hole's west edge: estate and lanes north of the LT&SR 14–19 ft; marsh and marsh roads south of it 4–7.

## Field notes from readers (added 2026-09-29, from opus-aj)

- **Typical ranges:** Custom House / Freemasons Road streets 5·5–8 ft, B.M.s on buildings 7–11; Poplar interior streets 9–11; East India Dock Road 10–16; Dock Wall Road and dock premises 19–20 (B.M.s to 22); Thames river-wall and quay frontage at Blackwall / Victoria Dock 16–18; road embankments and railway bridges near Custom House 20–30.
- **Interpuncts:** FREEMASONS (several), GRANGE (Custom House), QUIXLEY (L·E), PRESTAGE STREET (gap dot), DOCK WALL ROAD (before R), BUTCHERS HEDGE (H·E).
- **Quays and river walls:** the survey dot often sits at a wall vertex or on the wall line 5–10 px from the figure; crane circles and bollard dots are not survey dots.
- **Join:** full-width py ~586–590 on 131078_87170 (over river). School-block hatching on 131081_87146 gives false "LIKELY" joins.

## 25-inch field notes (added 2026-09-29, from opus-al)

- **Typical ranges on Plaistow Level:** marsh fields and drain banks 4–6 ft; B.M.s on boundary stones, fences and culverts 5–9; marsh roads about 6, flush with the marsh; lanes and estate roads north of the LT&SR 11–21, falling toward the railway; road bridges over the LT&SR high 20s.
- **B.M. decimals can be unprinted** ("6 6"): apply the 1 dp convention and record `medium`.
- **Pheons at boundary stones** sit among the B.S. tie circles; take the point where the barbs converge, `medium`. Figures beside B.S./C.S. junctions may have no cross at all: centre of figures, `medium`.
- **Crosses vary in weight** (thin `+` to bold 4-point star); all are survey marks.
- **Italic 9 vs 8:** a 9's tail can close into a small loop; an 8 has two bowls of similar size. Raw pixels settle it.
- **OS sheet edge:** a neat line, then white off-sheet margin, then grey missing tiles; record the margin separately.
- **Join:** horizontal py ~782 (87149 row) = py ~14 (87152 row) across columns 131099–131102.

## Field notes from readers (added 2026-09-29, from opus-am)

- **Typical ranges:** Custom House street grid 3·8–7·6 ft with building B.M.s 7–10; Poplar interior streets 9–13; Poplar main roads (East India Dock Road west, Bow Lane, High Street) 15–22; Royal Victoria Dock jetty and quay walls 19–21·6 (figures over water with the dot on the jetty wall).
- **Interpuncts:** R·O·B·I·N H·O·O·D L·A·N·E, N·E·W B·A·R·N, D·E·N·M·A·R·K, WOOLMORE·STREET gap dot, O·R in FREDERICK'S ROAD.
- **B.M. contact panels:** centre them on the decimals, not the "B.M." letters; 2× centres fall 5–10 px left.
- **Poplar terraces:** expect many `low` B.M. decimals (5/6 and 6/8 unsettled at 12–20×).

## 25-inch field notes (added 2026-09-29, from opus-an)

- **Typical ranges:** marsh interior about 4 ft; marsh roads about 6; marsh B.M.s on boundary stones and culverts 5–7; lanes between the Level and the estates 15–17 with fence-line B.M.s mid-20s; new estate streets on the East Ham / Upton Park terrace 21–30 rising northward, house-corner B.M.s 26–33.
- **Crosses on estate streets** sit in the carriageway 12–30 px from the figure, often between the letters of a spaced street name; those streets have no other interpuncts, so the cross is safe (`high`).
- **Pheons** may be sideways or inverted, hidden under a letter of the street name, with the B.M. text 50–70 px away across the road.
- **Look-alikes:** tree symbols pass for an italic 3 at 2×; large district-name display letters are not heights.
- **Sheet edge on the 131105 column:** neat line at px ~444–452, then white margin, then grey missing tiles (columns 131107–131108).
- **Joins:** py ~785 on 87149; py ~290 and px ~452 on 87134; px ~452 on 87131.

## Field notes from readers (added 2026-09-29, from opus-ao)

- **Typical ranges, Bromley-by-Bow west of the Lea:** streets 24–32 ft; street bridges over the railway 45–49 on the deck with ramps in the high 30s; road bridges over Bow Creek 32–33 with earth approaches about 30; creek walls 14–16, hatched east bank 15–19.
- **Typical ranges, Abbey Mills marsh:** sewer crest about 31 against 3–4 at its foot; LT&SR embankment 12–20 with its foot at 7–8; open marsh 4–5 with fence-line B.M.s 4–5; chemical-works channel frontages 17–18.
- **Thames-edge quays and lock sides:** 16–18 with B.M.s to about 19·6; dots at wall vertices among mooring-post dots, so mostly `medium`.
- **Italic 3s render closed on Bromley-by-Bow** (look like 8 at 20×); final 3/8 stays `low` there.
- **Joins:** py ~763 on 131063_87149; py ~567–570 across the 87143 row.

## 25-inch field notes (added 2026-09-29, from opus-ap)

- **Typical ranges:** Wanstead Flats heath roads about 50 ft; Manor Park / Little Ilford field terrace and lanes 30–35 (fence-line B.M.s low 30s, `other`); East Ham estate streets north of the LT&SR 28–32 with house-corner B.M.s 30–34; marsh roads south of the LT&SR about 6, marsh interior often blank.
- **The C.R. lane boundary is a line of large round dots**; survey crosses are easy to tell apart, so those are `high`.
- **Pheons point every way and sit 40–60 px from the text**, occasionally 130 px.
- **Joins:** a vertical join at px ~443–460 runs down the whole 131105 column; py ~13–14 on 87152.
- **Figures on a mosaic's north or south edge often have their cross or text on the neighbouring mosaic**; record the figure and note the missing part.

## Field notes from readers (added 2026-09-29, from opus-aq)

- **South Bromley / Poplar north of East India Dock Road:** streets 17–23 ft, wall B.M.s 19–24; Limehouse Cut towing path 15–15·5. The 8–13 range applies only to the southern Poplar interior.
- **LT&SR east of Abbey Mills runs near grade (4–10 ft)** where the sewer crosses over it: dots on rails there are `railway`, not `embankment_top`.
- **Sewer bridges and aqueducts:** abutment B.M.s sit at marsh level (5–8 ft, `bridge`); a figure at the tip of a wing slope is mid-height, `other`.
- **Plaistow west:** earth ramps over the sewer 22–30 (`embankment_top`) running out at about 15; Lower Road / Whitwell Road streets 6–9 rising to 13–20 toward Charles and Meredith Streets.
- **Joins:** py ~192 on 131060_87158; py ~960 on 131060_87155; py ~571 on 131078_87143. **Interpuncts:** HOWARD'S (·O), FIRST (S·T), AVENUE (E·), WHITWELL, SUFFOLK, RAILWAY STREET, BURCHAM, KERBEY (E·R).

## 25-inch field notes (added 2026-09-29, from opus-ar)

- **Typical ranges:** East Ham Level marsh roads 6–8, road-fence and culvert B.M.s 5–8; East Ham / Little Ilford estate streets and the C.R. lane 28–32 with house B.M.s 32–34, field tracks east of the lane falling to 20–26; road bridges over the LT&SR at East Ham high 30s; northern edge roads on the Aldersbrook / Wanstead side 52–65 falling southward, fence and gate B.M.s there mid-50s to mid-60s (`other`).
- **Traps:** survey triangles usually carry no figure; small (~8 px) digits on railway fence lines are doubtful (`low`); a "B" cut by an edge beside a pheon may be "B P" (boundary post), not B.M.
- **Joins:** the 131105 column join (px ~440–450) continues on the 87158 and 87161 rows; py ~15–17 on 131108_87152. The 131108 column mosaics on rows 87128–87152 are fully on-sheet.

## 25-inch field notes (added 2026-09-29, from opus-at)

- **Typical ranges:** East Ham Level marsh road about 8, road-side and culvert B.M.s 5–8 (`other`), marsh interior blank; C.R. lane footway 30–32 with fence and house B.M.s 32–34, field tracks east of it 25–31, Jews Farm Lane 20–22; Wanstead Flats heath road 45–50 with fence B.M.s 50–51; the cemetery north-east of the Flats: paths 36–47 (`open_ground`), chapel and Lodge B.M.s mid-40s (`building`), path-edge and fence B.M.s 37–46 (`other`).
- **On marsh roads the cross sits in the road between its dotted edges** with the figure 40 px away beyond the road line. A figure can sit up to 50 px from its only cross on the far side of a lane; pair it and say so.
- **Dots beside "Stone" / "Stones" labels are not crosses.** A pheon or B.M. text at a mosaic edge often has its other half on the neighbour.

## Field notes from readers (added 2026-09-29, from opus-as)

- **Bromley north of the Limehouse Cut is 32–35 ft** with wall B.M.s to about 36; the terrace south of St Leonard's Road is 19–24. **The Cut towing path is 14–15·5** while the road beside it is 20–23: record separately.
- **Plaistow west and north-west:** earth ramps over the sewer about 30 at the crest, running out at 15; streets near the sewer 16–22, falling to 5–9 toward Whitwell Road and the Ward Boundary.
- **Poplar / Blackwall:** main-road frontage 13–20; back streets 7–11; rail-depot made ground 15–18.
- **A leading 1 against a row of kerb dots can look like 3**; if the leading digit is the only doubt, `low`.
- **Joins:** py ~768 on 131087_87149; px ~817–822 on 131063_87167. **Interpuncts:** EMPSON, COLIN, BURCHAM, WHITWELL, NEWMAN, HOWARD'S, FIRST, HILL, ROAD at St Leonard's Road.

## Field notes from readers (added 2026-09-29, from opus-av)

- **Royal Victoria Dock and Tidal Basin:** jetty and quay walls 16·5–19·5, wall B.M.s 19–21·5, sidings and yards 18–19; Custom House streets and North Woolwich Road 6–9.
- **Custom House east (Freemasons Road grid):** streets 5·5–7·5, building B.M.s 7·8–9, unbuilt ground 5–6·5.
- **Poplar (East India Dock Road to High Street):** tramway 19–23 with dots on the rails, side streets 21–24, High Street 18·5–20·5.
- **Cumberland Farm lanes east of Canning Town are 11–16 ft**, farmland not marsh; do not assume 3–8 across that area.
- **Joins:** py ~771 on 131087_87149; px ~630 on 131084_87170. **Interpuncts:** FREEMASONS, NORTH WOOLWICH ROAD, WOODSTOCK ROAD, HIGH STREET, BATH STREET.

## Field notes from readers (added 2026-09-29, from opus-au)

- **Plaistow Marsh north of Beckton Road:** open marsh 5–6 ft; unmade dotted-edge estate roads 6–7; Beckton Road and marsh-edge roads 6–9; B.M.s on buildings, fences and boundary lines 7–11.
- **Northern Outfall Sewer east of Abbey Mills:** crest 30–31 with crest-edge B.M.s low 30s (`embankment_top`); road ramps over it from the low 20s to about 30.
- **Royal Victoria Dock north quays:** quays and yards between warehouses 21–22, warehouse B.M.s 22–24, jetty walls and swing-bridge ends 19–19·5; rail tracks and yards north of the warehouse line can be 7–10 ft lower, so do not "correct" a lone 7–10 there.
- **Interpuncts:** R·O·A·D on the marsh-edge road; ROAD in Beckton Road; STREET (T·R, R·E) on Chrisp and Railway Streets; BURCHAM (H·A); ST LEONARD'S AVENUE ('S·A). The tool reports many false joins over dock-water wash.

## Field notes from readers (added 2026-09-29, from opus-ax)

- **Limehouse Cut, Poplar reach:** south canal wall 14·5–15·5 (`wall_top`, dot on the wall line); building B.M.s along the Cut 16–17; streets and works south of it 20–24.
- **Plaistow, Barking Road / St Andrew's:** streets 19–23, wall B.M.s 21–23; the road over the sewer bank high 20s.
- **Poplar dock premises by Millwall Junction:** two made-ground levels, about 10–11 and 17–18, warehouse B.M.s 19–20 on the upper one.
- **Plaistow Marsh / Recreation Ground:** open marsh 5–6; surrounding streets 6–8·5; building B.M.s 8·8–10·7; fence B.M.s 7–10 (`other`).
- **On the Poplar 87155/87158 sheets 18·x at 2× can be 16·x**: check the leading pair at 6–10× as well as the decimal.
- **Joins:** py ~771 on 131090_87149; py ~954 on 131057_87155 (= py ~186 on 131057_87158). **Interpuncts:** CHRISP·STREET, BARCHESTER, GUILDFORD, ELLESMERE, GIRAUD, LION STREET, SHARMAN ST, NEWMAN.

## Field notes from readers (added 2026-09-29, from opus-aw)

- **Bromley north of the railway:** streets 28–34, workhouse grounds about 29; street bridges over the railway deck high 40s, earth ramps high 30s.
- **Plaistow west and south-west:** streets 12–15 in the low pocket north of the sewer causeways, 17–24 toward Balaam Street and Howard's Road; house B.M.s 15–24; sewer and causeway crests about 30, ramps 21–23 running out at about 15.
- **Custom House, Victoria Dock Road frontage:** streets 5–7, building B.M.s 7·5–10, railway at grade about 7.
- **Joins:** py ~762 on 131060_87149; px ~640 and py ~574 on 131084_87143; py ~400 on 131090_87164. **Interpuncts:** BRICKFIELD, EMPSON, COLIN, UPPER ROAD, CHESTERTON, NEWMAN, ETHEL, HIGH, WOODSTOCK ROAD.
- **Coordinator's note:** the area descriptions in assignment briefs are approximate; the sidecar centroid in the mosaic JSON is authoritative.

## Field notes from readers (added 2026-09-29, from opus-ay)

- **Poplar interior (Upper North Street to Grundy Street):** streets 14–23 rising eastward, building B.M.s 16–24. **Bromley north of Devons Road:** 23–27, B.M.s 24–29.
- **Royal Victoria Dock:** quays and mooring apron 17·5–19·5 (`wall_top`, mooring-post dots crowd the survey dots); warehouse B.M.s 19·5–24; rail yards north of the warehouse line 20–22; sidings north of the Custom House bank 7–10; streets south of the dock-estate bank 6–7·5 with B.M.s 9·5–11.
- **Traps:** a 2× 19·x on a B.M. can be 18·x (check the leading pair at 12–20× against known 9s); a 2× x·73 decimal can be x·23.
- **Joins:** py ~186–190 on 131057_87158; py ~597 on 131087_87170. **Interpuncts:** RICARDO, SOUTHILL, MARKET, NORTH, DEVON'S, CLYDE ROAD, EVELYN ROAD.

## Field notes from readers (added 2026-09-29, from opus-az)

- **Bromley north of the railway:** streets 32–35 falling to 28–30 at the railway and station forecourt; earth ramps to the street bridge high 30s, deck and parapet high 40s; wall B.M.s low to high 30s.
- **Plaistow Marsh by Regent's Lane:** lanes 5–6 flush with the marsh (also 5–6); the Toll Gates road 7·5–8·5; B.M.s on sluices, fences and road edges 5–10 (`other`).
- **Poplar between East India Dock Road and High Street:** tramway and main roads 15–21; the Wade Street pocket and lanes south of it 11–15 down to about 8; Woodstock Road low 20s.
- **Figures written on terrace blocks with no dot** are classed `building` (they probably give the road level in front).
- **Joins:** py ~761 on 131060_87149; px ~925 (sheet edge, white margin east) on the 131093 column rows 87155/87158. **Interpuncts:** BRICKFIELD, THOMAS, EMPSON, COLIN, WASHINGTON, SHIRBUTT, WOODSTOCK ROAD, PRINCE; none in BRUCE ROAD, JEFFERSON, REGENT'S LANE.

## Field notes from readers (added 2026-09-29, from opus-bb)

- **Royal Victoria Dock south quay apron:** 17·5–18·5 (`wall_top`), warehouse B.M.s about 19; dock-estate bank foot on the Custom House side 6–7, with open ground between bank and road reaching the low teens (not marsh); fence B.M.s there 8–9 (`other`).
- **West India Dock bonded warehouses:** two made-ground levels, 10·5–11·5 on the railway side and 17·5–18 on the south quay road; warehouse B.M.s 19–20.
- **Poplar, Wade Street / Wade's Place pocket:** streets 11–15, building B.M.s 12·5–16; Dolphin Lane and the low road south of High Street 7·5–9.
- **Traps:** an italic 9 reads as 2 at 2×; a 2× 6 in a B.M. leading digit can be a closed 8 at 5–12×.
- **Joins:** py ~760 on 131057_87149; py ~401 and px ~921 on the 131093 column. **Interpuncts:** ROUNTON, DEVON'S, SHIRBUTT, WOODSTOCK, HIGH, the Custom House R·O·A D.

## Field notes from readers (added 2026-09-29, from opus-ba)

- **Prince Regent's Lane south of Barking Road** sits a few feet above the open ground beside it: lane and marsh tracks 5–11 falling southward; a lane figure of 8–11 there is normal.
- **Plaistow north of the sewer:** streets 18–23, tramway dots on rails; road crossings of the sewer bank high 20s (`embankment_top`); building B.M.s 20–27.
- **2× sweeps turn closed 8s into 3 or 7** (24·88 → 24·38, 22·23 → 22·73, 18·25 → 19·25). Every B.M. decimal needs 6× and 12× panels.
- **Dots in P·RINCE, ·REGENT'S and BALAAM ·A** occur only beside figures and behave as survey dots.
- **Joins:** px ~924 on 131093_87161; py ~571–576 on 131087_87143 (both reported correctly by the tool).

## Field notes from readers (added 2026-09-29, from opus-bd)

- **Bromley north-west:** streets low 30s in the north falling to low 20s toward Commercial Road; house and works B.M.s 24–39; road bridges over the North London Railway mid-40s on the deck; streets beside the cutting in the 40s, cutting-edge fence B.M.s about 50 (`other`).
- **Poplar, Upper North Street area:** streets 15–23 falling eastward; building B.M.s 16–23.
- **2× decimal traps again:** a round-topped 6 read as 5; a closed 8 read as 9 in the leading pair. Check B.M. decimals at 6× and 12× every time.
- **Interpuncts:** FAIRFOOT, SPANBY R·OAD, K N· (Knapp), S·HERWOOD, FE·RN, SUF·FOLK, STRE·ET, P·E·K·I·N, U·P·P·E·R N·O·R·T·H, B·R·U·C·E, DEVON'S. **Join:** px ~533 on the 131054 column (real, reported by the tool); false horizontal joins over dock water on 131093_87167.

## Field notes from readers (added 2026-09-29, from opus-bc)

- **Bow terrace (High Street, Bow and streets south):** streets 31–37, wall B.M.s 29–37; Bow Road tramway 20–22 near Bow Bridge rising to 28–32 westward; Lea towing path 14–15; riverside works yards 15–20.
- **Bow Common / Furze Street:** streets 20–25, building B.M.s 21–26. **Limehouse Cut north reach:** canal wall about 14·5 (`wall_top`), Bow Common Bridge deck about 22, streets beside the Cut 14–16 rising to 20–23 about 150 m south.
- **Prince Regent's Lane, Plaistow north-east:** railway bridge deck high 20s, earth ramp mid-20s, lane falling to the low teens southward across open fields.
- **Traps:** italic final 3s in B.M. decimals close to look like 8 at 20× on the Bow Common sheets (`low`); large-dot "Und." boundary chains along the Limehouse Cut lanes hide survey dots (`medium`).
- **Joins:** px ~537 on the 131054 column; py ~562 on 131060_87143; py ~773 and sheet edge px ~928 on 131093_87149. **Interpuncts:** FURZE, GALE, SUFFOLK, WASHINGTON, HANCOCK, PRIORY STREET, SABBARTON, STREET; none in JEFFERSON.

## Field notes from readers (added 2026-09-29, from opus-bf)

- **Limehouse / West India Dock north:** quay road between warehouses and sheds 17·5–18 (`yard`), warehouse B.M.s 18·5–19·5; the strip north of the warehouses toward the railway wall 11–12·5 (two levels about 6 ft apart, neither a misread); streets north of the Coal Depot 8–11; Pennyfields and King Street 12–19.
- **Bow west of Bromley:** streets and tramway 38–45; road bridges over the railway 45–46·5 on the deck; cutting-edge fence B.M.s about 50 (`other`).
- **On the Bow sheets a 2× sweep shows 38·x as 36·x**; expect `low` there unless 7–12× settles it.
- **Convert region-view centres against the crop's grid labels**, not its pixel position; 2× centres were 10–35 px out.
- **Joins:** py ~563 across the 87143 row (131054–131060); px ~531–541 on the 131054 column.

## Field notes from readers (added 2026-09-29, from opus-be)

- **Old Ford / Bromley north of the North London Railway:** flat terrace, streets 30–34, wall B.M.s 32–35 (occasionally near 39); figures on terrace blocks 33–37.
- **Poplar / Limehouse (87161 and 87164 rows):** north of East India Dock Road streets 17–23·6 falling east to 15–18; south of it 12–19 falling to 8–12 toward Wade Street; tramway dots on rails 16·5–22; building B.M.s 12·5–22·6.
- **Royal Victoria Dock south quay:** apron and dock walls 16·5–18, warehouse B.M.s about 20; a low apron at 10–12·5 at the foot of a hatched bank between warehouses and the barge basin, basin quay walls 14–15·5.
- **Traps:** 18·x at 2× may be 18·8 not 18·6; B.M. 19·xx at 2× may be 18·xx; 18·7 may read as 19·7 (compare a known 18 at 16×); an x·0 at 6× can be a G-shaped x·6 at 8×.
- **Joins:** py ~598 and px ~918 on 131093_87170; px ~531–535 on all 131054 rows; py ~385 on 131054_87164.

## Field notes from readers (added 2026-09-29, from opus-bh)

- **Forest Gate NE, north of Romford Road:** streets 34–37 in the north falling to 32–33 on Romford Road; house-wall B.M.s 34–35, occasionally about 38.
- **Plaistow NE / Boleyn:** streets 24–27 north of the Barking Road side, falling to 21–23 toward it; kerb and footway-edge B.M.s low 20s (`other`).
- **East Ham north fields:** open field and footpath 33–36 (`open_ground`); estate streets 32–35·5; school and house B.M.s 36–37·5.
- **East Ham / LT&SR (Katherine Road):** streets 25–30; road bridge parapet B.M. about 40, earth ramp mid-30s, ramp foot about 29. Record all three separately.
- **Traps:** in B.M. leading pairs the italic 3 and 8 look identical at 12× (try 8×; else `low`); a 2× x·64 was x·84 at 6× and 12×. **No interpuncts** in CREDON, LANCASTER, CLAREMONT, SHREWSBURY, LANE; dots in VICTORIA (T·O), LAW·RENCE, KATHERINE (·E).

## Field notes from readers (added 2026-09-29, from opus-bg)

- **Forest Gate by the station:** north of the railway streets 39–42, wall B.M.s 40–41·5 (the local high); south of it (Woodgrange Road, Earlham Grove) streets 33–36, B.M.s 35–37.
- **Upton Park / East Ham border estates (131102 column):** new estate streets 32–36 in the north falling to 27–31 toward the LT&SR; fence-line B.M.s mid-30s (`other`); road bridge ramp mid-30s, parapet B.M. about 40.
- **Plaistow north-west:** village streets 20–23 with building B.M.s 21–26; Pelly Road bridge approaches mid-to-high 20s, parapet B.M. low 30s. **Limehouse:** the Coal Depot road, Dingle Lane and Dolphin Lane go down to 8–11.
- **Trap:** on the Forest Gate sheets the leading digits of 33·x and 38·x render alike at 8–12×; leave `low` if unsettled.
- **Joins:** py ~952 on 131102_87128 = py ~184 on 131102_87131. **Interpuncts:** LANCASTER, ..BURY, ..ESTER ROAD, PLASHET, MILTON, AVENUE, EARLHAM, CHURCH, HIGH, PENNYFIELDS; none in GROVE or WOODGRANGE (except W·O beside a figure).

## Field notes from readers (added 2026-09-29, from opus-bi)

- **Plaistow north-west / Abbey Farm edge:** streets 11–14 in the Plaistow Grove / Plaistow Road pocket, rising north-east to 17–22 toward Park Road and Stratford Road; building B.M.s 13–20. The Plaistow Station bridge ramps (earth, `embankment_top`) run from about 21 to the high 20s, bridge-end B.M.s high 20s to about 30 (`bridge`); the station forecourt (`yard`) is low teens. The south-west quarter of the Abbey Farm sheet is blank farmland.
- **Forest Gate west, north of the GER (Wellington, Odessa, Essex Streets):** streets 38–42 and wall B.M.s 41–42, higher than the "about 40" quoted earlier; 36–38 belongs to the GER side and Earlham Grove is 35–36; Hamfrith Road and the Romford Road tramway 30–32.
- **East Ham / Katherine Road bridge:** parapet B.M. about 40, earth ramp mid-30s, ramp feet about 29 on both sides; the terrace around is 25–30, lowest at the east end of Victoria Avenue.
- **Traps:** a 2× x·6 can be a closed x·8 at 6–8×; a raw-pixel check settles it (two counters for an 8, one for a 6). A lone final 6 after a 5 can close at 12×; judge it at 8×.
- **Interpuncts:** V·I·C·T·O·R·I·A and L·A·N·E on the East Ham sheet; ODESSA (A·); STATION (T·) at Plaistow; O·A in MAUD ROAD; S·T in PLAISTOW.
- **Joins:** py ~375–378 across the 87137 row (column 131081) with a real 1–3 px offset; px ~637–640 on 131084_87140 (the tool's horizontal step at py ~380 there is not visible by eye); py ~746 on 131081_87122.

## Field notes from readers (added 2026-09-29, from opus-bj)

- **West Ham between Romford Road and Ham Park Road:** streets 24–29, falling to 22–26 on Vicarage Lane and the streets south of Ham Park Road; wall B.M.s 23–31. The main east–west road there carries the dash-dot Parly. Boro. & Ward boundary, so figures on it are `medium` at best.
- **Plaistow village (Church Street, St Mary's Road, North Street, High Street, The Broadway):** 20–23; lanes south of High Street high teens; Pelly Road bridge deck high 20s, parapet B.M. low 30s. Most `medium` figures there have no dot of their own, only a street-name interpunct.
- **Woodgrange / Forest Gate east:** roads beside the railways and Romford Road flat at 31·8–33·2, wall B.M.s 33–35·6. **Woodgrange Park Cemetery:** drives 31·8–32·6, the path outside the south wall 33, wall B.M.s about 35; fields to the south 33–36, occasionally 38 (`open_ground`).
- **Trap:** on the cemetery sheet italic final 3s look exactly like the leading 3 at 12–14× and raw pixels do not settle them; expect several `low` there. UNION ROAD (not Street) on 131078_87128.
- **Joins:** py ~940–943 on 131078_87128 = py ~172–176 on 131078_87131; py ~754 with a strong tint step on 131102_87122.

## Field notes from readers (added 2026-09-29, from opus-bl)

- **Plaistow south-east toward the Barking Road (Greengate, Cave, Hollybush, Samson, Pragell Streets, the Tramway Depot road):** streets 19–22·5 falling gently south; fields to the north 21–22 (`open_ground`); building B.M.s 21·8–25·2. This is terrace, not marsh.
- **Stratford Green / Cedars Road:** streets 27–30; the Romford Road tramway there 29–30, falling to 26·5–28 on the Fairland Road side; wall B.M.s 27·5–32. Tram rails and interpuncts leave few dots that are certainly survey dots, so expect many `medium`.
- **West Ham south (Church Street, Gift Lane, Plaistow Road, Harberson Road):** the main road under the Parly. Boro. & Ward boundary mid-20s rising east; Church Street about 23, churchyard about 21; Plaistow Road falls from about 20 at the School to the low teens southward toward Abbey Farm, and Plaistow Grove to 12–14. School yards stand 1–2 ft above the street (`yard`). A B.M. may have only a tick for a pheon with a ground-level figure under it; record both.
- **Trap:** on the Stratford and West Ham sheets the italic final 3 stays open on the left at 12×, clearly unlike the closed 8s, so a lone final 3 there may be `medium` rather than automatically `low`.
- **Interpuncts:** C·E·D·A·R·S, S·A·M·S·O·N, P·R·A·G·E·L·L, G·R·E·E·N·G·A·T·E, P·L·A·I·S·T·O·W (S·, O·), O· in ROMFORD.
- **Joins:** py ~576 on 131090_87143 and 131093_87143 (tint step); the OS sheet edge is at px ~930 on 131093_87143 south of py 576 with white off-sheet paper east of it; the tool's vertical joins on both mosaics are false.

## Field notes from readers (added 2026-09-29, from opus-bk)

- **Forest Gate north / Wanstead Park (87116 row, columns 131090–131093):** streets 39–42 north of the Tottenham & Forest Gate line, easing to 36–38 south of it and 35–36·5 south of the G.E.R.; house-wall B.M.s 38–41·5; road-bridge B.M. over the T&FG about 41·5 (`bridge`). No heath figures here.
- **Upton Park south by Boleyn Castle and the Barking Road (columns 131099–131102):** streets 21–29 falling south-west to 21–23 on Barking Road; wall B.M.s 23–29; fence-line B.M.s 21–23 (`other`); the open field south of Barking Road and the unbuilt south-east are blank.
- **Traps:** on the Forest Gate sheets 33/38 stays unsettled at 8–14× and in raw pixels, as already warned. A centred 7× position sheet run after the marker sheet caught 2–12 px position errors on several marks; run one before `done`.
- **Interpuncts:** B·O·L·E·Y·N, P·R·I·O·R·Y, A R·R A G O N, P·A·R·R, TYL·NEY, WOODGRAN·GE (N·G), PLAISTOW (S·, W·); none in BARKING, CHESTNUT, GODWIN or ANN STREET.
- **Joins:** py ~551–553 across the 87116 row (131090–131093), missed by the tool; px ~942 on 131093_87116; py ~384 on 131102_87137; py ~377–379 on 131081_87137.

## Field notes from readers (added 2026-09-29, from opus-bo)

- **Plaistow Road / Plaistow Grove pocket north of Abbey Farm:** streets 11–14, Abbey Farm fields 9·5–12 (`open_ground`), building B.M.s 10–17. The same B.M. value can legitimately appear twice on one road; record both.
- **Barking Road east of Upton Park:** 22–27 rising westward; building B.M.s mid-to-high 20s. **Blind Lane / White Horse road (Plaistow south-east):** 19–23, fence-line B.M.s 21–25 (`other`).
- **Manor Park Cemetery (131099_87116, not Forest Gate streets):** drives about 37 (`open_ground`); the road south of the T&FG line 32–36; the railway corridor carries no figures.
- **Traps:** on the Barking Road sheet the same glyph serves as the second digit in 23·x and 28·x figures; when raw pixels match, choose from the road profile and mark `low`. At the Manor Park chapel a B.M. leading 6 at 6–12× conflicted with an 8 in raw pixels; record `low` with the alternative in notes.
- **Interpuncts:** GREENGATE (E·E and after the final E); PLAISTOW (S·, O·); GROVE (V·E); ROAD (·R); STREET on Greengate Street (after the T); BLIND LANE has interpuncts plus a row of boundary dots, so figures there are `medium`.
- **Joins and edges:** py ~576 on 131090_87143 (the tool says ~571; its vertical joins there are false); py ~375–377 on 131078_87137; py ~552–555 on 131099_87116; the OS sheet edge at py ~579 on 131099_87143, with white off-sheet paper to py 768 and grey missing tiles below.

## Field notes from readers (added 2026-09-29, from opus-bp)

- **Stratford south / West Ham west (131075 column, rows 87128–87131):** tramway main road 26–30 rising eastward; side streets 23–27 falling south-west toward West Ham Lane; West Ham Lane 21–25, and streets west of its southern end drop to the high teens; building B.M.s 21–31. A B.M. pheon can sit up to about 50 px from its text, across a road; a plain figure under the text is then the ground level.
- **Manor Park (131102–131105):** tramway 32–34 rising to the high 30s on the Woodgrange Park bridge, parapet B.M. high 30s (`bridge`); cemetery drives and the strip outside 32–34 (`open_ground`); the C.R. lane 31–32·5; fields to the south 33–35.
- **Forest Gate north, west of Woodgrange Road:** streets 40–42, house B.M.s 41–44; Woodgrange Road falls to about 39·5 at the T&FG viaduct and 38 south of it.
- **Look-alike:** a small three-stroke arrow like a pheon with no "B.M." text can sit beside a plain spot height; treat it as the spot's position, not a bench mark.
- **Traps:** on the Manor Park cemetery sheets italic final 3s and 8s stay unsettled at 7–16× and in raw pixels (expect several `low`); on the Stratford sheets the italic 3 stays open, so 3 and 8 separate cleanly.
- **Joins and edges:** py ~551 across the 87116 row continues onto column 131087 (missed by the tool); px ~357 down the 131075 column on 87128 and 87131 (missed by the tool on 87128); py ~938–941 on 131075_87128 = py ~170–173 on 131075_87131; on 131105_87122 a neat line at px ~462 and an edge at py ~757 with white off-sheet margin beyond.

## Field notes from readers (added 2026-09-29, from opus-bq)

- **Wanstead Flats edge north of Forest Gate (87113 row):** streets 39–47 and wall B.M.s 41–48; the road along the Flats edge low-to-mid 40s rising east; roads running south off it fall to about 38–40. The heath interior north of the edge road carries no figures. This is above the 38–42 quoted for Forest Gate north and well below the 60–100 range note.
- **Maryland Point / Stratford north:** streets 34–37 falling toward the G.E.R., wall B.M.s 35–39; a road-bridge approach over the G.E.R. cutting stands 2–3 ft above the adjoining street (`bridge`).
- **Stratford Broadway / The Grove / Water Lane:** streets flat at 27–30, wall B.M.s 30–32; many `medium` beside interpuncts in WATER and CEDARS.
- **Trap:** on the Capel Road sheets an italic 3 reads as 8 at 12× but correctly at 8×.
- **Interpuncts:** C·A·P·E·L; W·A·T·E·R; CEDARS (R·S); TYL·NEY; ALBERT (T·); ROAD (A·D, D·, O·).
- **Joins:** px ~945 full height on 131093_87113; a probable vertical join at px ~357 on 131075_87125 (missed by the tool; the same line runs down the 131075 column); py ~375 on 131078_87137; a faint possible join at py ~12 on 131078_87119.

## Field notes from readers (added 2026-09-30, from opus-br)

- **West Ham Cemetery / Forest Gate north-west:** cemetery drives high 30s to about 41 (`open_ground`); chapel and Lodge wall B.M.s high 30s to low 40s; Cemetery Road 37–39; Wellington Road 40–41; school and house B.M.s low 40s.
- **Wanstead Flats edge (Forest Road / Woodford Road, 87113 row west):** streets 44–48 in the north falling to about 41 southward on Woodford Road; house B.M.s 43–48; the Strode / Bignold / Station Road pocket 42–45. The recurring trap here is 6/8 in the second digit (46·x against 48·x); the Flats themselves carry no figures.
- **West Ham south / Abbey Mills edge:** West Ham Lane about 20 falling to 14–15 southward; churchyard low 20s; Church Street 18–23; streets toward Abbey Road and Eastbourne Road 12–16; wall B.M.s 13–24. Expect many `medium` from the dash-dot boundary, interpuncts and F.P. dots.
- **Abbey Farm / sewer crossing the LT&SR:** farm fields 9·5–12 (`open_ground`); the LT&SR near grade 8·5–9·5 (`railway`) with the hatched band beside it 4–6·5 (`embankment_foot`); sewer crest about 31 (`embankment_top`); abutment B.M. high single figures (`bridge`).
- **Tip:** a hole-counting helper (threshold, then count enclosed counters) separated 8 from 6/9 better than eyeballing 12× zooms; a LANCZOS zoom can close a 6 into an 8, so check raw pixels.
- **Joins the tool misses:** py ~548 across the 87116 row on column 131081; px ~357 on 131075_87128 (and py ~938 there runs the full width, not just x 0–256); px ~353 on 131075_87134.

## Field notes from readers (added 2026-09-30, from opus-bs)

- **Wanstead Flats south edge (87113 row, columns 131090–131096):** the edge road 42–47 rising east, wall B.M.s 44–48; roads running south fall to 38–42 within about 350 m; cemetery ground at the east end high 30s.
- **Manor Park north of the G.E.R.:** cemetery drives and streets 36–40; road bridges over the station cutting mid-40s (`bridge`); south of the G.E.R. streets 32–34 with wall B.M.s mid-30s. White Post Lane 32–35, its railway-bridge B.M. high 30s, ramp foot low-to-mid 30s (`embankment_foot`).
- **East Ham south-west, White Horse Lane:** 23–25 on the lane; road-edge B.M.s about 25 with no wall drawn (`other`).
- **Traps:** on the Capel Road / Cranmer Road sheet a 2× x·9 can be a two-bowled x·8 at 10–16×; compare with known open-tailed 9s on the same sheet. On the Manor Park station sheet italic 3s render closed at 8–12× (expect several `low`). An upright figure on railway tracks is not a height. A B.M. pheon can sit about 50 px from its two-line text.
- **Interpuncts:** C·A·P·E·L; TYL·NEY (Y·L); WIN·IFRED (N·); W·H·I·T·E P·O·S·T C.R. L·A·N·E (with a large-dot boundary line along it, so figures are `medium`); W·H·I·T·E H·O·R·S·E L·A·N·E (E·); A·D in Whittaker ROAD; none in WOODFORD.
- **Joins and edges:** px ~177–179 full height on 131096_87113; py ~555–557 on 131102_87116; px ~460–465 on 131105_87119; the OS sheet edge at py ~580 on 131102_87143 with white margin to 768 and grey tiles below.

## Field notes from readers (added 2026-09-30, from opus-bt)

- **Stratford north-west (Maryland Point / Water Lane):** tramway 32–35, its survey marks being small arrow-ticks on the rails; the road beside the railway about 33; Water Lane south of the railway and the Cedars Road / Manbey Grove area 29–31; wall B.M.s mid-to-high 30s.
- **West Ham south toward Abbey Mills (Ham Street to Napier Road):** streets 10–15 falling south-east; open ground at the south edge about 9–10. Figures written on terrace blocks with no dot can read several feet below the street; record them as `building`, not `street`. A raised walled way (double wall lines with posts, no hatching) crossing that open ground stands high teens; record it as `other` and describe it in notes (possibly a sewer or causeway).
- **Forest Gate north below the Flats (Thorpe / Pevensey / Station Road):** 46–49 in the north-west falling to 40–44 toward the School and Station Road.
- **Manor Park Cemetery north:** drives 37–38 (`open_ground`); Capel Road along the Flats edge falls from the high 40s in the west to the low-to-mid 40s in the east.
- **Trap on Capel Road:** the second digit of a 4x·9 figure shows an upper counter in raw pixels like a 9, while 3s elsewhere on that sheet show none, so raw pixels cannot settle 3 against 9 in a leading pair there; mark it `low`.
- **Joins:** py ~744 and px ~359 on 131075_87122; px ~352–356 full height and py ~372 on 131075_87137; px ~653 full height on 131084_87113 (missed by the tool); py ~548 on 131081_87116.

## Field notes from readers (added 2026-09-30, from opus-bu)

- **Wanstead Flats south-west edge (131081 column, 87113 row):** terrace streets high 40s and a house-corner B.M. about 50, higher than the 39–47 quoted for the rest of the 87113 row; streets fall to the low-to-mid 40s about 250 m south; cemetery paths and chapel B.M.s there low 40s.
- **Forest Gate west (Cruikshank / Trevelyan / Buckingham Roads):** streets 36–40 falling south; house-corner B.M.s 38–39·5.
- **Maryland Point west:** the Leytonstone Road tramway flat at about 33–34, with small three-stroke arrows on the rails (no B.M. text) marking the spot positions; streets to the east rise to about 36–37; wall B.M.s 35–39. The Maryland Square / Albert Square area carries no figures.
- **Little Ilford by the LT&SR:** roads 33–35; a bridge-abutment B.M. high 30s (`bridge`); fields south of the railway blank.
- **Tip:** small italic 6 and 8 in B.M. decimals look alike at 12–14×; comparing raw pixels with a known 6 on the same sheet (upper part filled, one lower counter) works better than zooming further.
- **Joins and edges:** py ~546–548 on 131078_87116 (missed by the tool); px ~355–357 full height on 131075_87119 (real); px ~460 full height on 131105_87119; on 131108_87122 the sheet edge at py ~757 over missing tiles.

## Field notes from readers (added 2026-09-30, from opus-bv)

- **West Ham south / Abbey Marsh edge:** streets 11–16 falling south-east; marsh and open ground south of the streets 9–10 (`marsh`); marsh roads 8–11, about flat with the marsh. Northern Outfall Sewer crest low 30s (`embankment_top`). A road passing under a sewer aqueduct drops to 3–4 ft directly beside a crest near 32; this is not a misread. Aqueduct B.M.s: abutment about 11, parapet low 30s (`bridge`).
- **Manor Park station:** bridge deck and approaches low-to-mid 40s, station-side roads high 30s; Forest Road falls from the high 30s to about 33; the Romford Road tramway at Manor Park flat at 33–34; wall B.M.s mid-to-high 30s; a B.M. on a cattle trough is `other`.
- **Wanstead Flats:** roads and avenues across the Flats 46–50 falling southward; B.M.s there 48–50 (a pheon on nothing drawn is `other`). The heath interior, copses and ponds carry no figures, so a near-empty file is normal.
- **Traps:** figures written just below a road's edge line with no dot of their own, where the only dot is a lettering interpunct across the line, go at the centre of the figures as `medium`. Heavy Romford Road ink fills counters, so a final 5 or 8 there often stays `low`. A 2× x·9 and 15·0 on the Abbey sheets came out x·8 and 16·0 at zoom; compare against flat-topped 5s on the same sheet.
- **Joins and edges:** px ~352 full height on 131075_87140 (missed by the tool); py ~558–560 and px ~462–466 on 131105_87116; px ~945 full height on 131093_87110. On both Flats mosaics (87110 row) py 0–256 is missing tiles and py 256–~353 white margin above the OS neat line.

## Field notes from readers (added 2026-09-30, from opus-bw)

- **Stratford Market / Bridge Road pocket (131072 column, 87134 row):** streets 12–14 with building B.M.s 13·5–15, a low made-ground pocket well below the 27–30 of Stratford Broadway; do not "correct" low-teens values there. The market sidings and railway corridor carry no figures.
- **Wanstead Flats interior (87110 row):** the avenue and roads across the Flats 46–50, B.M.s on trees, posts and walls about 48–52 (`other` for tree/post/open ground). Figures follow the drawn roads, not the open heath.
- **Manor Park / Flats edge (131102 column):** the edge road 42–44 with wall B.M.s 44–46 on the F.W. wall line; roads running south fall to 37–39 within about 250 m; a raised approach to a cutting bridge can stand about 5 ft above the adjoining street with no hatching drawn.
- **Little Ilford / Manor Park east:** streets 33–35·6; a road bridge over the LT&SR cutting has a wing-wall B.M. high 30s (`bridge`) with the ramp foot about 34.
- **Trap:** on the Forest Gate west sheet a second digit that looks like 6 at 8–12× can show a faint upper counter in raw pixels like the 8s on the same sheet; where they disagree, record `low`.
- **Joins:** py ~546–548 full width on 131078_87116 (missed by the tool); none on 131072_87134 or 131108_87119.

## Field notes from readers (added 2026-09-30, from opus-ca)

- **Leytonstone south-east, south of the T&FG line (131081_87110, not Wanstead Flats):** streets very flat at 48–51, open ground by the Vicarage low 50s, building B.M.s 50–55 (church highest). This is higher than Forest Gate.
- **Manor Park north-west, Forest Drive / Wanstead Road:** 39–44, fence B.M.s 41–45 (`other`); a second digit of 6 or 8 in 4x·x figures there often stays `low`. The heath interior carries no figures.
- **Little Ilford east:** open fields either side of the LT&SR cutting 29–33 (`open_ground`); footbridge parapet B.M. high 30s (`bridge`). A figure whose digit is hidden by bank hatching goes in `unreadable_regions`, not readings.
- **Stratford Market pocket:** streets 12–14, building B.M.s 13·5–15 (confirmed by a second reader).
- **Abbey Mills / Channelsea:** walled, unhatched approaches to the road bridge over the G.E.R. from the mid-20s to about 28, parapet low 30s (`bridge`); raised lanes with hatching on one side low 20s (`embankment_top`); made-ground strips between the Channelsea and the sewer bank 17–19; Channelsea bank path low teens; Abbey Road mid-teens. Sewer crest and the drop under the aqueduct as already noted.
- **Joins and edges:** px ~466–468 full height on 131105_87113 (missed by the tool); py ~344 on 131081_87110; on 131111_87122 the OS neat line at py ~760 with white margin to 768 and grey missing tiles below.

## Field notes from readers (added 2026-09-30, from opus-bz)

- **Leytonstone south / Cann Hall (87113 row, column 131078):** streets 45–49 in the north-east falling to about 40 on the south-west roads; house B.M.s high 40s. The Wanstead Slip and the Jews' Cemetery are blank.
- **Stratford north, Leytonstone Road (131075_87116):** the tramway 33–38 falling south, mostly with no dot (`medium`); streets to the east 36–38; wall B.M.s 35–40. Leading 3/8 and 5/6 stay unsettled there even at 16× and in raw pixels.
- **Abbey Road / Mortham Street pocket (131072_87137):** streets 12–15 and wall B.M.s 13·5–17·5, well below Stratford. Walled sewer or ramp bands over the railway climb from the high teens to about 31 with no hatching drawn (`embankment_top`, bridge B.M. `bridge`).
- **Flats south-west edge (131084_87110):** streets 47–50 falling toward the T&FG line; house B.M.s about 49–53.
- **Little Ilford / Manor Park north (131108_87116):** Romford Road 33–34·5; the avenues to the south 35–36; house B.M.s 36–38.
- **Traps:** a 2× final 0 or 1 can be a 9 or 6 at zoom (four 2× misreads corrected on these sheets). Pheons sit 30–55 px from their text on all these sheets, and a pheon can read like a "K" at 2×.
- **Joins:** px ~359–362 and py ~546 on 131075_87116 (the tool's py ~587 and ~762 there are false); py ~560 full width on 131108_87116 (the tool gives it from x 256 only); py ~370 on 131072_87137; neat lines at py ~350 and px ~655 on 131084_87110.

## Field notes from readers (added 2026-09-30, from opus-cb)

- **Leytonstone south-east (131081_87110):** streets flat at 48–51 with a slight rise toward the church; wall B.M.s 50–55 (confirmed by a second reader).
- **Leytonstone Road / High Road tramway south of the Wanstead terrace:** about 37–40 falling south, with rung-like ticks on the rails marking the spots; the terrace east of it rises to 48–49 about 250 m east, then eases to 40–41 on Blenheim Road; kerb B.M.s are `other`.
- **Leyton side of Stratford north (Dunmore / Ashlin / Chandos Roads):** streets 33–36, tramway 33·5–38; the dotted boundary line, interpuncts and F.P. dots crowd the survey dots, so expect many `medium`.
- **Little Ilford east:** the Avenue 32–36; Church Road falls east to 28–29 by the Rectory, lower than the 33–35 of the other Little Ilford roads.
- **Wanstead Flats south edge at Aldersbrook:** the road along the 3 ft fence wall about 44, tracks across the Flats about 44, lower than the 46–50 of the western Flats avenues.
- **Traps:** small italic 5 against 6 in final digits stays unsettled in raw pixels on the Worsley / Blenheim Road sheet; a B.M. final 3 at 2× became a closed 9 at zoom on the Flats-edge fence wall.
- **Joins:** px ~358 full height on 131075_87113; py ~544–545 full width on 131072_87116 (the tool's py ~587 and ~710 there are false).

## Field notes from readers (added 2026-09-30, from opus-cc)

- **Cann Hall / Leytonstone south (131078_87110):** streets 47–53 rising north-east; the church wall B.M. mid-50s; kerb B.M.s `other`.
- **Wanstead Flats north-west (131084_87107):** roads across the Flats 50–55 falling south; terrace-wall B.M. mid-50s.
- **Aldersbrook edge of the Flats (131105_87110, 131108_87113):** the edge road 41–45 falling east; fence B.M.s mid-40s (`other`); the road-bridge deck over the G.E.R. cutting high 40s with parapet B.M. about 50 (`bridge`), about 8 ft above the road just south; Romford Road at Manor Park 32–34, wall B.M.s mid-30s. Milepost figures ("Ilford 1 / London 6") are not heights.
- **Trap:** on the Leytonstone Road sheet a second-digit 5 against 6 splits template matching from the 12–14× view in both directions; leave it `low` unless raw pixels and zoom agree. Flat-topped 5s in the same sheet's clear figures make good templates.
- **Caution on template matching (coordinator, after QA):** one reader matched unknown digits against known digits on the same sheet by normalised correlation. On the Leytonstone Road sheet that method called 5 in three figures where two or three independent readers read 6 at zoom. Use template matching only as a tie-breaker, never to overrule a clear 8–12× view, and mark any figure where the two disagree `low`. A lone final 3 against 8 still stays unsettled.
- **Joins:** px ~466–468 on 131105_87110 from py 360 down, with a stained sheet east of it; py ~338–344 on 131078_87110; px ~355–358 and py ~546–548 on 131075_87116 (the tool's py ~587 and ~762 there are false).

## Field notes from readers (added 2026-09-30, from opus-ce)

- **Little Ilford (Church Road / Little Ilford Lane):** lanes and roads 23–28 falling east toward the Roding; fields and churchyard 26–28 (`open_ground`); boundary B.M.s mid-20s (`other`).
- **Manor Park east, south of the G.E.R.:** Romford Road 32–34 in the west easing to about 25 near Little Ilford Lane; open ground beside the lane high 20s; building B.M.s high 20s to mid-30s.
- **131108_87110 is the City of London Cemetery,** not the Flats: nearly blank, one boundary B.M. mid-40s.
- **Leytonstone north (Harrow, Acacia, Newcomen Roads, High Road):** streets 49–54; building B.M.s low-to-mid 50s.
- **Traps:** a 2× 28·x can be 26·x; a B.M. decimal pair 86 at 2× can look like 66 at zoom. On the Leytonstone sheets survey dots sit in the lettering line (R·O, H·A, B·Y) even in names with no other interpuncts, so expect many `medium`.
- **Tip:** a hole counter (4× bicubic, count enclosed counters and note whether each is upper or lower) separates 6 (one lower), 9 (one upper), 8 (two) and 3 (none) well. Template matching was unreliable on italic 3s; tie-breaker only.
- **Joins and edges:** py ~342–347 full width on 131078_87110; on 131114_87119 the OS neat line at px ~755 with white margin to 768 and grey tiles beyond.

## Field notes from readers (added 2026-09-30, from opus-cd)

- **Stratford north / Leyton (Victoria and Dunmore Road grid):** streets 32–37 falling west and south, occasionally near 30; the High Road tramway there 38–41; wall B.M.s low 40s.
- **Leytonstone south (Harrow Green to Napier Road):** the tramway climbs from about 40 to about 49 northward; side streets 48–51; house B.M.s mid-40s to about 54. A B.M. pheon can sit about 50 px away across the tramway.
- **Leytonstone by the Flats (131081_87107):** streets flat at 50–53; the road along the Flats edge about 51, with its figures written north of the dash-dot Parly./U.D. boundary and dots often missing (`medium`).
- **Little Ilford Lane (131111 column):** 26–28, noticeably below the 33–36 of the avenues just west.
- **Traps:** a 4x·x second digit of 6 or 8 on the Worsley Road sheets stays split (raw pixels say 8, the 8× nearest-neighbour view says 6); leave it `low`. Rail ticks can sit 10–13 px from a tramway figure. Grid-label estimates on 2× sweep crops were 20–40 px out; compute centres from the pixel position against the crop origin.
- **Interpuncts:** NAPIER (E·R), R·O in ROAD on Napier Road, WRAGBY (B·Y), VICTORIA (R·I), HARROW (H·A), WORSLEY (O·R), BLENHEIM (·B, H·E), THIRD AVENUE (after D, E·N).
- **Joins:** py ~563 full width on 131111_87116 (the tool gives x 0–768 only); py ~343–345 and px ~362–364 on 131075_87110; px ~358–362 on 131075_87113; none on 131081_87107 or 131072_87113.

## Field notes from readers (added 2026-09-30, from opus-cf)

- **Leytonstone north (Montague Road, 131081 column):** streets rise steadily from the low 50s to the low 60s northward; house and hall B.M.s mid-50s to about 60. This is the highest ground read so far on the five-foot sheets.
- **North-west tip of Wanstead Flats:** tracks across the heath mid-to-high 50s; the heath interior carries no figures.
- **Leyton south (Holy Trinity / Birkbeck Road / Union Road):** streets about 50–53 in the north-east falling to 40–41 on the south-west tramway (rail ticks, so `medium`); building B.M.s 42–53. A B.M. with no pheon within about 60 px goes at the centre of its text as `medium`, `other`.
- **Little Ilford Lane by the Roding:** the lane 24–28; house and lane-edge fence B.M.s high 20s (`building` / `other`); fields, ponds and the Spring to the east carry no figures.
- **Interpuncts:** ILFORD (F·O, I·L), ·LITTLE, MONTAGUE (U·), HARROW (R·), WOODHOUSE (D·), HOLLOWAY (O·), BIRKBECK (R·K).
- **Joins and edges:** py ~150 full width on 131081_87104 and 131084_87104 (missed by the tool); py ~564 full width on 131114_87116 (missed by the tool); py ~343–346 on 131072_87110; neat line px ~656 on 131084_87104; sheet edge px ~757 on 131114_87116.

## Field notes from readers (added 2026-09-30, from opus-ch)

- **Marsh south of Beckton Road (131096–131105 on the 87158 row):** open marsh 4–6 beside the ditches (`marsh`); Beckton Road and the other marsh roads 6–8, only 1–3 ft above the marsh (`street`); B.M.s on ditch crossings or culverts 5–7 (`other`). No embankments, wall tops, bridges or made-ground figures on this row; much of the area is blank. BECKTON has no interpuncts, so a dot beside it is a survey dot.
- **Small-digit trap on the marsh sheets:** a closed lower bowl occurs in 5s as well as 6s, so a hole count cannot separate 5 from 6. The difference is at the top: a 5 has a flat bar and a stem, a 6 a curved top. Compare with a flat-topped 5 on the same sheet at 8–12×; mark `low` if unsettled.
- **Leyton south (Union Road / Birkbeck Road):** italic 3 and 8 are not separable in raw pixels there (the 3s also show two weak loops), so a lone final 3/8 stays `low` even when 8–12× looks like an open 3.
- **Edges and joins:** the OS sheet edge runs at py ~207–210 across the top of the 87158 row (131096–131105), with white paper above; on 131096_87158 a full-height vertical join at px ~157, with a darker sheet west of it; on 131105_87158 only x 0–444, y 210–1024 is on-sheet. py ~343 full width on 131072_87110 (the tool gives x 256–768 only).

## Field notes from readers (added 2026-09-30, from opus-ci)

- **Marsh south of Beckton Road / Plaistow Level north of Custom House (87161 row, columns 131096–131105):** open marsh and ditch banks 4·5–6·5, occasionally about 7 (`marsh`); B.M.s on ditch crossings and culverts 5·5–8 (`other`).
- **New estate streets on the marsh (Tree in Pound Lane, Baxter Road, Alnwick Road):** 5–7, flush with the marsh, not raised (`street`); house and terrace-corner B.M.s 7–9·5 (`building`). No figures above about 10 in the row; made ground and dock works lie further south.
- **Survey dots here often sit 10–18 px from their figure,** across a road edge line (figure written outside the road, dot inside it).
- **Lone interpuncts:** POUND·LANE has only a D·L dot; ALNWICK one dot between I and C; BAXTER none.
- **Trap:** a 5 with a closed lower bowl is common on these sheets; a raw-pixel check (flat top bar with the right side open just below it = 5) was more reliable than 12× views, which round the top.
- **Joins and edges:** full-height join at px ~156 on 131096_87161 (western sheet darker, ditches uncoloured; the same line as px ~157 on 131096_87158); OS neat line at px ~443 on 131105_87161 with white margin to 512 and grey tiles beyond.

## Field notes from readers (added 2026-09-30, from opus-cg)

- **Leytonstone north (131078_87104):** the High Road tramway from the low 60s at the railway crossing down to the high 50s; side streets 53–60; wall B.M.s 59–61. The highest ground on the five-foot sheets.
- **Leytonstone south by Harrow Green:** the tramway 47–55; streets to the west reach the mid-to-high 50s; Harrow, Chichester and Napier Roads flat at 48–50.
- **Little Ilford north-east:** lanes 25–28; the tree-lined avenue and Aldersbrook Lane fall east to about 19–22, the lowest ground on that terrace.
- **Aldersbrook, City of London Cemetery:** paths 30–33 (`open_ground`); the footbridge B.M. over the G.E.R. low 30s (`bridge`).
- **Trap:** on the Leytonstone and Little Ilford sheets B.M. decimal pairs 86/66/68 and a lone second or final 6/8 disagree between 6×, 12× and raw pixels; leave them `low`.
- **Positions (coordinator, reconciling two readers):** one reader slipped 20–40 px trusting 2× grid labels, another slipped 40 px trusting image-pixel positions in a region view. Neither shortcut is safe on its own: the centred 7× position sheet is the check that catches both, so never skip it.
- **Interpuncts acting as survey dots:** L·, W· in LANSDOWNE; ·A in ROAD; N·O in MONTAGUE; F·O in ILFORD.
- **Joins:** py ~150 full width on 131078_87104 (the same line as on 131081 and 131084; missed by the tool); px ~364 full height on 131075_87107 (the tool gives part only); on 131114_87113 the OS sheet edge at px ~758; on 131111_87110 missing tiles py 0–256 and white margin to ~364.

## Field notes from readers (added 2026-09-30, from opus-cj)

- **Custom House estate on the marsh (Baxter, Alnwick, Prince of Wales, Royal and Leyes Roads):** streets 5·8–7·1, flush with the marsh; building B.M.s about 7·8–11. **Connaught Road** stands about 3 ft higher at 9·5–10; a raised road toward a P.H. low teens (`embankment_top`).
- **G.E.R. Beckton Branch:** at grade 7·5–10 (`railway`); on its bank to the Docks Cut bridge 9–12 (`embankment_top`), with culvert heads at the bank foot about 10 (`other`); bridge wing-wall B.M. low teens (`bridge`).
- **Marsh and the Docks Cut:** marsh north of the Cut 4–7·8; the Cut's north bank 5–7·5; culvert, sluice and boundary-stone B.M.s 5·5–7·5 (`other`). No dock quays, wall tops or made ground above about 13·5 on the 87164 row; the dock works lie further south.
- **Open question (coordinator):** stops inside the Docks Cut lettering ("Alber.t", "C.ut") sit directly above figures written inside the Cut. One reader took them as survey dots on the north bank (`medium`/`low`). Judge each for yourself: a survey dot is usually solid and round; a lettering stop sits on the baseline of the letters. Say in notes which you think it is.
- **Traps:** a 2× sweep turned 6·1 into 8·1; a 9·x can read 6 at 8–12× yet show two counters in raw pixels (leave `low`).
- **Joins and edges:** py ~404–406 full width across the 87164 row (131099–131105; the tool says ~400–402); on 131105_87164 four OS sheets meet, with a join at py ~406 over x 0–441 and px ~441 below it (8 px offset in the drain lines), white off-sheet paper east of px 441 above py ~408 and grey tiles at x 512–1024, y 0–256; on 131108_87164 missing tiles py 0–256 and white margin to the neat line at py ~408.

## Field notes from readers (added 2026-09-30, from opus-ck)

- **Dock row east of Custom House (87167 row, the Royal Albert Dock end):** quay surfaces about 18–18·5; B.M.s on the quay-edge wall line about 20; the south quay about 18. The Docks Cut banks and the marsh north of the rail yard 4–7 (`marsh`). The railway bank at the Cut crossing low teens with its foot about 7 (`embankment_top` / `embankment_foot`); crossing-parapet B.M. `bridge`. Rail yards, warehouse roofs, the marsh interior and the dock water are blank.
- **Custom House estate north of Connaught Road:** streets 5–6, flush with the marsh; house and school B.M.s 7–9·5; Connaught Road about 9·5 at the top of the hatched slope down to the railway cutting.
- **Survey dots inside water-feature lettering:** on the Docks Cut the dot is sometimes placed within the lettering (between r and t of "Albert", between C and u of "Cut"), with the figure written in the channel below. These dots occur only beside figures, so two readers now treat them as survey dots (`medium`).
- **Hydrants on quays** are drawn "·H"; where a quay figure has "·H·", the trailing dot may be the survey dot (`medium`).
- **Small leading 6s close up at 12× on these sheets;** read 6 against 8 at 6× and compare with a closed 8 in a B.M. on the same sheet.
- **Joins:** px ~150–153 full height and py ~403 full width on 131096_87164; px ~440 full height on 131105_87167 (western sheet uncoloured, eastern with blue water). The tool's joins at py ~475/660 and px ~453 on 131096_87164, py ~498–531 on 131105_87167 and py ~316/495/531 on 131108_87167 are warehouse shading, bank hatching or fence lines.

## Setting rule for docks and channels (coordinator, 2026-09-30)

- **Quays:** judge by where the dot is. A dot on the drawn quay-edge wall line, or a B.M. on that wall, is `wall_top`. A dot on the open quay surface or apron away from the edge line (between warehouses, by hydrants, on quay roads) is `yard`, because it is the made-ground surface, not a wall. Do not class a whole quay as `wall_top`.
- **Channel banks with no wall drawn** (the Docks Cut banks, ditch banks): the figure is ground level, so use `marsh` (or `embankment_top` if a hatched bank is drawn). "Figures over channels are wall tops" applies only where a wall is drawn.

## Field notes from readers (added 2026-09-30, from opus-cl)

- **Royal Victoria / Albert Dock row (87167 / 87170):** quay surfaces and quay walls 18–18·5 (surface `yard`, edge wall line `wall_top`, per the dock rule above); warehouse and quay-edge B.M.s 19–21; dock premises beside a bridge approach low 20s; the swing-bridge parapet mid-20s with its walled approach low 20s (`bridge`); Connaught Road 9·5–10 with the railways beside it at grade 9–10; raised roads toward the P.H. low teens; south-quay corners and jetty heads can be 15·5–17. Hatched spoil banks on the marsh south of the docks run from the low teens to the high 20s above marsh at 6–7 (record crest and foot separately).
- **Lettering-stop dots on the Docks Cut:** a second independent reader judged both ("Alber.t", "C.ut") to be survey dots: solid, round and slightly below the letter baseline, with the figure in the channel below. Treat them as survey dots (`medium` where the dot touches a letter).
- **3 against 8 in small italic figures:** check in raw pixels whether the digit is open at the middle-left; an 8 is closed there and a 3 is open, even when both show end closures at 12×.
- **Quays:** mooring posts and H (hydrant) marks carry their own dots; a dot straight after an H is plausible as a survey dot but is `medium`.
- **Joins:** px ~150–152 on 131096_87167 (west sheet colours the dock water blue; the tool's py ~295 and ~378 there are false); py ~598–604 full width across the 87170 row; px ~437–440 on 131105_87170. The tool reports false joins along warehouse tint edges on the 87170 row.

## Field notes from readers (added 2026-09-30, from opus-cm)

- **Quay setting, measured (adopted as the working rule):** a dot on the drawn edge line or within 2–4 px of it, at the coping, is `wall_top`; a dot 5 px or more clear of the edge line, on the open quay or dry-dock head, is `yard`. A B.M. on a thin fence or quay-road line with no wall drawn is `other`. State the distance in the reading's notes.
- **Albert and Victoria Dock quays:** edge-line dots and open quay both 18–18·5 (so the setting, not the value, tells them apart); edge-wall B.M.s about 20; timber-yard quay corners on Victoria Dock's south-west lower at 15·5–17; a hatched spoil bank inside the dock estate high 20s.
- **Connaught Passage bridge:** abutment B.M. mid-20s; unhatched ramp low 20s (`bridge`); the road falls to the high teens at the dock-railway level crossing; Connaught Road on its hatched bank south of the dock 12–16 (`embankment_top`).
- **Silvertown / Oriental Road:** streets 6–6·5, flush with the marsh; terrace B.M.s 8–9; bank-foot road 5·8–6·3. The large marsh west of the railway bank is blank.
- **Leyton, Cathall Road / Trinity Street:** streets 51–57 falling south-east; the Ongar Branch road-bridge parapet about 70 (`bridge`), earth ramps 60–67 (`embankment_top`); building B.M.s 52–59; the R.C. Cemetery blank.
- **Trap:** on the Silvertown terrace sheet a B.M. middle digit that reads 3 at every zoom can have raw pixels identical to the leading 8 of the same figure; leave it `low`.
- **Joins:** py ~600 full width on the 87170 row (131096–131102; on 131096 east of px 150 only); px ~150 full height on 131096_87170 (blue-tinted western sheet; the same line as px ~156 on 131096_87158/87161).

## Field notes from readers (added 2026-10-02, from opus-cq)

- **Old Ford west of the North London Railway (Usher / Parnell / Lefevre / Armagh / Cardigan Roads):** northern junctions and house B.M.s low-to-mid 40s; streets fall south-east to about 30–31 on Old Ford Road. This is higher than the 30–34 quoted earlier for Old Ford / Bromley.
- **Old Ford / Bow east of the cutting:** goods-yard streets about 28–33; Fairfield Road about 30, dipping to the mid 20s under the railway bridge (abutment B.M. about 4 ft above the road), rising again to low-to-mid 30s south of it; streets fall east to 23–26 at Clay Hall / Summer Street. The road bridge over the North London cutting: road either side mid-to-high 30s, parapet B.M. high 30s (`bridge`).
- **Lea at Old Ford:** towing-path strip at the bank toe 13·5–15 (`embankment_foot`, dot 5 px clear of the river edge); the Northern Outfall Sewer crest 33–35 either side of the river (`embankment_top`); aqueduct abutment B.M. mid-teens (`bridge`); a figure written on the aqueduct well below the crest is `bridge`, `medium`, surface uncertain; wharf lane high teens; Old Ford Road falls from the high 20s to the low 20s toward the river.
- **Leytonstone north (second read):** High Road tramway mid 50s to low 60s, ticks on the rails; side streets 53–64; house B.M.s mid 50s to mid 60s.
- **Traps:** on the Old Ford west sheet the italic 3 is closed at the middle-left in raw pixels like an 8, so the raw-pixel 3/8 test fails there; treat a lone 3/8 as `low`. FAIRFIELD, LEFEVRE and FORD carry dots only beside figures; treat those as survey dots (`medium`).
- **Joins (all missed by the tool):** px ~540–541 full height on all three 131054 rows (87134, 87137, 87140); py ~365 on 131054_87137 and 131051_87137; py ~148 and px ~364 on 131075_87104.

## Field notes from readers (added 2026-10-02, from opus-cp)

- **Lea at Bow Bridge / Marshgate (the East London Soap Works area):** works yards and sidings 15–18 on made ground along the foot of the G.E.R. bank (`yard` / `railway`); lanes 16–18 (Marshgate Lane, the lane east of the works); building B.M.s about 18; the goods yard north of the railway low 20s; the Lea towing path 14–14·5; Stratford High Street tramway 15–17 rising to about 22 at the bridge end; the Bow-side main road 20–22; Bow back streets 20–35 rising westward. No marsh-level ground on these sheets (lowest about 14).
- **Bow Bridge:** record the road at each end of the bridge as `bridge` and the B.M. on the hatched approach wall as `bridge`; pheons on approach walls sit 15–45 px from their text.
- **Joins:** py ~360–369 across the 87137 row on columns 131057–131060 (the tool misses it on 131060); py ~600 full width on 131099_87170.
- **Quay rule, confirmed:** two independent readers of 131099_87170 agreed on all seven quay figures (four `wall_top` at 0–4 px from the edge line, three `yard` at 6–70 px clear).

## Setting rule for towing paths (coordinator, 2026-10-02)

- A towing path standing on a hatched bank is `embankment_top`. A towing path at the foot of a bank (railway or sewer) is `embankment_foot`. A towing path on level ground beside the river with no bank drawn is `open_ground` (it is a walkable ground surface), not `other`. A dot on the river-edge wall line itself is `wall_top`.

## Field notes from readers (added 2026-10-02, from opus-cs)

- **Soap works / Marshgate (131060_87137), confirmed by a second reader:** bank-foot works yards, sidings and lanes 15–18; building B.M.s on the works and mills about 18; the junction north of the G.E.R. bank low 20s; no marsh-level ground.
- **Bow between Roman Road and the G.E.R. (131048 column, rows 87137–87140):** streets 38–46, highest at the north-west and around Roman Road (42–44), falling to 34–39 toward Tredegar and Coborn Roads near the railway; house B.M.s 40–46.
- **Hackney Wick (131051_87128):** the terrace west of the N.L.R. embankment 38–44 with B.M.s to the mid-40s; east of it the ground drops about 20 ft within roughly 150 m along White Post Lane, to 16–18 by the chemical works. That is a real terrace edge, not a misread.
- **Hertford Union towing path:** about 22–25 (`open_ground` where level), well above the Lea and Cut towing paths at 14–15; the lock-side B.M. mid-20s (`wall_top`). Regularly spaced dots along a canal bank with no figures are not survey dots.
- **Traps:** on the Bow sheets italic 8 and 9 finals close alike; judging each against a 9 inside the same figure at 12× works, but a lone final 8/9 stays `low`. On the Old Ford sheets 3 and 8 separated at 10× lanczos though 8× nearest-neighbour made them look alike. "B. Ps" at a railway crossing are boundary posts, not B.M.s.
- **Interpuncts (dot only beside a figure):** CARDIGAN (A·N), LIBRA (·L), ROMAN (A·), ROAD (R·O, A·D, D·), PARNELL (N·), FORD (F·, R·), STEPHEN'S (E·P), TREDEGAR (·R).
- **Joins the tool missed:** py ~364 on 131048_87137; py ~366 on 131060_87137; py ~932–935 on 131051_87128 (the canal is coloured only north of it).

## Field notes from readers (added 2026-10-02, from opus-cr)

- **The ground rises westward from the Lea at Old Ford and Bow:** Lea towing-path strip 13·7–14·6 (`embankment_foot`, dot in the 9–12 px strip between the river edge and the bank-foot line); riverside yards and lanes 15–18; Old Ford Road from 21–24 near the river to 28–30, then 35–37; the Old Ford / Bow terrace 30–42; the Northern Outfall Sewer crest 33–35 on both sides of the Lea, with the aqueduct's abutment B.M. about 16 (roughly 18 ft below the crest). A B.M. on the river edge line with no wall drawn is `other`, not `wall_top`. Two independent readers agreed on every crest, towing-path and aqueduct setting on 131054_87134.
- **Bow, east of Bow Church:** the Bow Road tramway 40–43 (the 20–22 near Bow Bridge applies only to the reach right by the river); its rails carry the C.R. boundary dots, so tramway figures there are `medium` at best. The terrace between the G.E.R. and Bow Road (Malmesbury Road, Alfred Street, Addington Road) is flat at 39–42 with wall B.M.s 42–44.
- **Old Ford (Cardigan / Tredegar / Mostyn Roads):** streets 30–39 rising west and south; wall B.M.s 31–43.
- **Hertford Union Canal at Wick Lane:** bank ground mid 20s with no wall drawn (`open_ground`); lock-side ground low-to-mid 30s; Wick Lane bridge B.M. mid 30s (`bridge`); Wick Lane under the North London Railway bridge low 20s.
- **North London Railway road bridge at Old Ford Station:** deck mid 40s (`bridge`), approach road about 40.
- **Interpuncts only beside figures:** ADDINGTON (A·D, O·N), ALFRED (F·), ·M in MALMESBURY, ·S in MARY ·STREET, M·O of MOSTYN, O· of ROAD there. "Whitechapel 2 / Stratford 1¼" is a milepost, not a height.
- **Trap:** B.M. first decimals 8 against 9, and 6 against 8, can read one way at 8–12× and the other in raw pixels; leave them `low`.
- **Joins the tool misses:** py ~168 full width on 131051_87131 (the canal is blue only north of it; the tool's px ~403 there is false); py ~563 full width on 131051_87143; px ~542 full height on 131054_87134.

## Field notes from readers (added 2026-10-02, from opus-ct)

- **Hackney Wick works district north of White Post Lane (Wallis Road, Prince Edward Road, Tallow Works):** streets 16–18, building B.M.s 17–18, lowest about 16: flat made-ground works streets, not marsh. White Post Lane falls about 23 ft east across the N.L.R. (confirmed by two independent readers, every value agreeing).
- **Victoria Park east end:** drives and open ground 45–48·5 (`open_ground`); park-edge path B.M.s high 40s on a fenced edge (`other`); park-edge roads and lodge B.M.s 40–47.
- **Hertford Union lock at the Lock Houses (Victoria Park):** lock side low 40s (`wall_top`); road-bridge parapet B.M. mid-40s (`bridge`). Bottom Lock further east is about 20 ft lower (low-to-mid 20s), so the canal steps down toward the Lea.
- **Bow, Coborn Road / Malmesbury Road:** streets 38–44, dipping to 33–34 at the G.E.R. crossing; wall B.M.s 33–44. Coborn Road figures sit among the large-dot C.R. boundary chain and B.S. stones (`medium`).
- **Mile End / Bow Road tramway near Wellington Road:** 40–44 falling east (`medium`, the rails carry the C.R. boundary dots); wall B.M.s 40–44; side streets toward Back Alley 37–39.
- **Trap (131048_87143 and 131048_87131):** the raw-pixel hole counter gave 9-like single upper counters for figures that look like 8 at 8–10×, and faint counters inside clear 9s; on these sheets it cannot settle 8 against 9 (`low`).
- **Joins:** py ~168 on 131048_87131 and py ~564 on 131048_87143 (both missed by the tool); py ~935 on 131051_87128; the tool's py ~537 on 131051_87125 is false (works buildings).

## Field notes from readers (added 2026-10-02, from opus-cu)

- **Victoria Park:** drives and paths 42·5–48 (`open_ground`); path-edge and boundary-stone B.M.s mid-40s with no wall drawn (`other`).
- **Old Ford Road / Roman Road / Ford Road / St Stephen's Road (131045 column):** flat at 42–44·5, wall B.M.s 42·7–45, higher than the 30–34 quoted earlier for "Old Ford / Bromley". The whole area from Victoria Park through Roman Road to Mile End Road is flat gravel terrace at 42–48, falling only toward the N.L.R. and canal at Hackney Wick (22–28) and toward South Grove (37–40).
- **Mile End Road tramway at Tredegar Square / Coborn Road:** 42–45; South Grove falls to 37–40; building B.M.s 40–46. Tram-rail dots, C.R. boundary dots and crosses, F.P. and H dots crowd the figures (`medium`).
- **Hertford Union canal bridges are humped:** the Three Colt Bridge deck and mid-parapet B.M. reach the low 50s, about 8 ft above the lane either side (`bridge`); do not "correct" a leading 5 there. A B.M. at the end of a parapet can be about 10 ft lower than the mid-parapet one.
- **Wick Lane:** 23–29 south-east of the N.L.R., falling from 38–44 by St Mark's Church; the lock-side figure at Old Ford Lock is `wall_top` when its dot is within 3 px of the drawn lock wall.
- **Trap:** on 131048_87128 and 131051_87131 a known italic 6 shows a weak upper counter in raw pixels, so the hole-counter rule for 6 against 8 is unreliable there; lone 6/8 digits stay `low`.
- **Joins the tool missed:** py ~934 full width on 131048_87128; py ~362–364 and px ~251–254 full length on 131045_87137; px ~253 full height on 131045_87134; py ~166–168 on 131051_87131 (its px ~403 is false).

## Field notes from readers (added 2026-10-02, from opus-cw)

- **Hackney Cut east towing path, on its hatched bank:** 21–23 (`embankment_top`, dots about 6 px outside the water-edge line, no wall drawn); a towing-path B.M. there is `other`. This is higher than the 14–15 of the Lea and Limehouse Cut towing paths further south. Hackney Marsh east of the Cut carries no figures.
- **Works streets by the Cut north of White Post Lane (Victoria Road, Prince Edward Road):** 16·5–19; building B.M.s 17–18·5. Riseholme Street and the church road 21–26; Cadogan Terrace and the park edge 30–40 (C·/G· interpuncts, so `medium`).
- **Victoria Park:** the north-west edge road about 40; the park centre around the Cricket Ground 45–48·5 (`open_ground`); pavilion B.M. high 40s (`building`).
- **City of London and Tower Hamlets Cemetery (Bow Common side):** paths 32–38 falling from the entrance (`open_ground`); boundary and B.S. B.M.s are `other`; boundary dot chains crowd figures there. South Grove / Maplin Street 36–39·5; Bow Common Lane about 32–33.
- **Interpuncts only beside figures:** C· and G· in CADOGAN; Y· in ALLEY; R·E in STREET; W· and M· in BOW COMMON; I·C in VICTORIA; R· in ROAD (Victoria Road).
- **Trap:** on the Hackney Cut sheet a final digit that looked like 8 at 2× reads 9 at 6× and 12×; a lone 8/9 there stays `low`.
- **Joins:** px ~251–253 full height on 131045_87134 (missed by the tool); py ~737–738 full width on 131051_87122 (missed; water blue only south of it); py ~761–763 on 131048_87149; px ~253–254 and py ~935 on 131045_87128.

## Field notes from readers (added 2026-10-02, from opus-cv)

- **Globe Town / Mile End Old Town (131045 column, rows 87140–87143):** streets flat at 40–44; house B.M.s 41–45; the Grove Road tramway a little lower, high 30s to about 41; Coborn Road dips to the low-to-mid 30s at and under the G.E.R.
- **Tower Hamlets Cemetery and the Bromley edge (131051_87149):** cemetery ground low-to-mid 30s (`open_ground`); chapel B.M.s high 30s to low 40s (`building`); lanes on the north side high 30s; streets toward the gasworks low-to-mid 30s; rails at the Gas Factory Junction about 30–31 (`railway`).
- **Victoria Park centre:** lawns and drives 45–47·5, falling to the low 40s south of the Bathing Lake; B.M.s on park footpaths or boundary stones are `other`. The Hertford Union lock at the Lock Houses is low 40s (two independent readers agree on every value there).
- **Interpuncts acting as survey dots:** BACK ALLEY (B·A, Y·), WELLINGTON (T·O), SOUTH (T·), FAIRFOOT (I·R), KNAPP (N·), MORGAN (G·A), the ·S of STREET on Morgan Street, the A· of ANTILL; none in ROMAN ROAD there.
- **Traps:** an italic final 9 can read as 0 at 8× and 9 at 12×; raw pixels (a single upper counter) settle it toward 9, otherwise `low`. A pheon can be absent near B.M. text at a mosaic's east edge (it is on the neighbour). The Hertford Union lock-side dot can sit 4 px from the chamber line with a vertex dot nearby; state both in notes.
- **Joins the tool missed:** py ~168 full width on 131048_87131 and 131045_87131 (plus px ~253 below it on 131045_87131); px ~252 full height on 131045_87140; px ~252 and py ~580 on 131045_87143. The tool's py ~762 on 131051_87149 is real.

## Field notes from readers (added 2026-10-02, from opus-cx)

- **Hackney Cut towing path, confirmed by a second reader:** 21–23 (`embankment_top`); the dots sit 6–7 px east of the water-edge line, on a strip about 8 px wide before the hatching starts; intensity profiles across the channel locate the edge line, strip and slope.
- **Mile End Road / Grove Road tramways:** flat at 39–44, survey marks as wedges or ticks on the rails; building B.M.s 40–44, rising to the mid-40s at the Regent's Canal bridge (`bridge`).
- **Bow Common gas works:** surrounding streets and open ground 29–35; Bow Common Lane falls south to 24–26; junction tracks low 30s at grade (`railway`); B.M.s on boundary or bank-foot lines with no wall drawn are `other`.
- **South Hackney:** Wick Road low 20s, rising west and south-west to 35–40 along Victoria Park Road; park-edge and churchyard ground 34–43 (`open_ground`); church, lodge and school B.M.s 22–43.
- **Hackney Wick north-west (Gainsborough Road):** streets 17–20; the road under the N.L.R. bridge low 20s (`embankment_foot`); church and school B.M.s 20–23.
- **Interpuncts beside figures:** I·C and R·I in VICTORIA; G·A in MORGAN; ·S in STREET at Tredegar Square; I·R in FAIRFOOT; N· in KNAPP; ·C in WICK; V·I in VICTORIA PARK ROAD; the final H· of GAINSBOROUGH.
- **Raw-pixel note:** on 131045_87125 the italic 3s are open at the middle-left, so the 3/8 test works there for single digits, but still not for B.M. decimal pairs.
- **Joins the tool misses:** py ~736–737 full width on 131048_87122 and 131051_87122; px ~249–250 on 131045_87146. The px ~253 join on 131045_87125 is real.

## Field notes from readers (added 2026-10-02, from opus-cy)

- **Mile End / Burdett Road:** the tramway falls from about 39 at Mile End Road to the mid 30s, then to about 33 toward Bow Common; side streets 32–38; house B.M.s 35–43.
- **Regent's Canal bridges:** a Mile End Road deck in the mid 40s with its parapet B.M. about 3 ft higher; a lower canal bridge can have its parapet B.M. about 3 ft below the road beside it. Both `bridge`.
- **Bow Common / Lockhart Street terrace:** flat at 31–35, building B.M.s mid 30s. **St Paul's Road, Bromley:** high 20s falling east to the mid 20s; house B.M.s 22–31; a boundary dot-and-cross chain along it makes several figures `medium`.
- **Hackney Cut / Waste Channel towing path at Wick Lane:** 21–22 on the hatched bank (`embankment_top`); Temple Mill lane across the marsh 16–17 at grade, with a lane-edge B.M. mid-teens (`other`); the Wick Lane canal bridge is humped, its parapet about 8 ft above the road at each end. The open Hackney Marsh carries no figures.
- **Traps:** on the Hackney Marsh sheet final 8s show a weak lower counter that the known 9s lack, but keep a lone final 8/9 `low`. A 2× grid estimate was 25 px out (run the centred position sheet). A pheon touching a small circle at a house corner is probably on a post (`building`, `medium`).
- **Dots that act as survey dots (only beside figures):** W· and M· in BOW COMMON, ·L of LANE, M· of MILL in Temple Mill, B· of BRIDGE, R·E of STREET, D· of Canal Road, ·A of St Paul's Road.
- **Joins:** py ~757 and px ~249 on 131045_87149 (the tool reports both); py ~762 on 131051_87149.

## Field notes from readers (added 2026-10-02, from opus-cz)

- **Lea at Temple Mills (131054_87116):** open ground west of the river 14·5–16 (`marsh` below 15, `open_ground` above, by the value rule where no place word is lettered); unfenced dotted-edge tracks across it 15–17; Templemills Road approach banks to the Lea bridge 18–22 (`embankment_top`), the bridge-parapet B.M. high 20s (`bridge`), the road running south-west about 16–17. "Highest point to which Ordinary Tides flow" is a note, not a height. No reservoirs or filter beds on this sheet.
- **Hackney Cut towing path north of White Post Lane:** 21–22 (`embankment_top`, dots 7–8 px east of the water-edge line); towing-path B.M.s straddling the edge line with no wall drawn are low 20s (`other`); Homerton Road on its approach bank high teens.
- **Homerton / Wick Road:** Wick Road 21–23, rising west and north-west to 30–31 at Brooksby's Walk and to the high 30s / low 40s by the North London Railway bank.
- **Mile End / Burdett Road (south of the canal):** streets 32–34, the tramway 33–34 (dots on the rails), house and chapel B.M.s 35–37. The Regent's Canal, Johnson's Lock, wharves and towing path there carry no figures. A pheon at a small circular feature by the tram rails is `other`.
- **Positions:** on the Mile End sheet 2× centres for B.M. text were 10–25 px left of the decimals; measure text extents numerically before building 12× panels. A 2× position for one figure on the Homerton sheet was 18 px off.
- **Interpuncts acting as survey dots:** R·O and M·I in TEMPLEMILLS ROAD; W· and M·M in BOW COMMON; ·C in WICK on Wick Road.
- **Joins the tool misses:** px ~547 full height and py ~536–540 full width on 131054_87116; px ~254–256 full height and py ~735–737 full width on 131045_87122.

## Field notes from readers (added 2026-10-02, from opus-da)

- **Hackney Marsh roads:** at grade 14·5–17 with no hatching (`street`); B.M.s on open marsh beside the roads with nothing drawn under them mid-teens (`other`). Homerton Road's hatched causeway east of Marsh Gate is only 1–2 ft above the at-grade road (16·7–18, `embankment_top`); Marsh Hill and Homerton Road at Marsh Gate about 16·5; Homerton rises west to the low 20s within about 100 m. Most of the marsh carries no figures.
- **Waste Channel / Hackney Cut towing path north of Wicklane Bridge (second read, every value agreeing):** 21·4–22 on the landward strip about 5–6 px inside a thin edge line with no wall drawn (`embankment_top`); a B.M. on that edge line is `other`; the hatched ramp crest at the bridge end low 20s (`embankment_top`); the humped bridge parapet about 30 (`bridge`).
- **Leyton terrace east of the Lea at Temple Mills (Crownfield / Colegrave / Edith / Chandos Roads):** streets 34–36·5, wall B.M.s 35–37·5, falling to about 30 at the north-west; about 18–20 ft above the marsh roads.
- **Burdett Road at St Paul's Road (Stepney):** tramway 29–33 with dots on the rails; St Paul's Road 28–30; wall B.M.s 30–34. The F.P· pheon at St Paul's Church is drawn sideways.
- **Trap:** on the Homerton Road sheet a second digit that reads 5 at 8× looks round-topped like a 6 at 9–14× next to known flat-topped 5s; keep these `low`.
- **Joins the tool misses:** py ~543 full width on 131069_87116 (its py ~837 and ~884 do not show); py ~538 full width on 131051_87116; px ~255 on 131045_87119 (the tool says ~250; paler western sheet); a pale band at py ~957–965 on 131048_87155.

## Field notes from readers (added 2026-10-02, from opus-db)

- **Lea Valley north of Temple Mills (87113 row, columns 131057–131063):** the valley floor here is not low marsh. Open fields, riverside strips and lanes are 15·5–17·5 (`open_ground` by the value rule; no marsh, meads or level lettering; no filter beds or reservoirs). Lettered names: Waterworks River, QUARTER, Ruckholt (Site of), Templemills Sidings, Cambridge Old Main Line, Loughton Epping & Ongar Branch, Westdown Road. Fence and river-edge B.M.s mid-to-high teens (`other`; a B.M. on a drawn river revetment is `wall_top`). Ground near the sidings low 20s; fields north of the sidings near Ruckholt low-to-mid 30s. Sidings at grade 17–18 (`railway`); the Ongar branch cutting high 20s with its crest high 30s. Westdown Road, Leyton, 22–33 rising north.
- **Temple Mills (second read, every value agreeing):** open ground west of the Lea about 15; tracks 15–17; Templemills Road approach banks 18–22 (`embankment_top`); bridge parapet B.M. high 20s.
- **Limehouse Cut, north side to Burdett Road:** streets 20–25·5 (Burdett Road tramway about 25); building B.M.s 21–27; the Cut frontage, wharves and works carry no figures.
- **Trap:** on the Waterworks River sheet the 2× sweep read 16·xx B.M.s as 18·xx and the reverse; comparing all the B.M.s on the sheet side by side in one 6×/10× strip settled the 6s and 8s.
- **Joins:** px ~838 full height on 131063_87113 (tool correct; its px ~901 is false); none on 131057_87113, 131060_87113 or 131051_87158.

## Field notes from readers (added 2026-10-02, from opus-dc)

- **Hackney Marsh (lettered MARSH beside the Lea):** open marsh and marsh tracks 14·5–16 (`marsh` where lettered); roads at grade only 0–1·5 ft higher, 14·8–17 (`street`); B.M.s on open marsh with nothing drawn mid-teens (`other`). This is a marsh floor in the mid-teens, not the 6–10 ft marsh further south.
- **Marshgate Bridge (Homerton Road over the Hackney Cut):** earth ramps about 18–22 (`embankment_top`); the west approach deck and the parapet B.M. high 20s (`bridge`); Homerton Road falls to about 15 at grade on the marsh east of the bridge. The Hackney Cut east towing path there 21·5–22·3 (dots 6–8 px outside the water-edge line).
- **Leyton west of Leyton Road (Westdown, Cranbourne, Mill and Frith Roads):** 22–37 rising north, about 350 m from the railway to the high 30s; house B.M.s high 20s to high 30s; the Ongar Branch rails in the cutting high 20s; rails by Temple Mills about 17·5.
- **Stepney north of the Regent's Canal (Rhodeswell Road area):** streets 24–34; house B.M.s high 20s to mid 30s; the canal bridge approach a few feet above the road beside it; the canal, towing path and wharves there carry no figures.
- **Trap:** on the Stepney and Leyton terrace sheets second-digit and final 6/8 stayed unsettled at 7–12× in both smoothed and nearest-neighbour views; expect several `low`.
- **Joins the tool misses:** py ~538 on 131051_87116; py ~537 on 131048_87116 (the tool says ~531); py ~957–960 on 131045_87155; px ~547–548 on 131054_87113 (the tool says ~551).

## Field notes from readers (added 2026-10-02, from opus-dd)

- **Hackney Marsh (lettered, so `marsh` even above 15):** open marsh and the Lea's riverside strip 14·5–16·5, no lower than the open ground (no wall drawn, so ground, not `wall_top`); marsh tracks 14·5–17 falling south-west (`street`); building B.M.s by the Lea bridge high teens. Homerton Road's causeway at Marsh Gate is only 1–2 ft above the at-grade road.
- **Ongar branch cutting by Westdown Road:** floor about 29 (two readers split between `railway` and `embankment_foot`; use `railway` for a figure on the rails, `embankment_foot` for one at the toe of the cutting side), east crest high 30s (`embankment_top`). Fields near Ruckholt 33–35.
- **Leyton east of the Ongar branch (Millais–Downsell grid):** streets 29·5–33 rising to 35–41 in the north-east; house B.M.s 31–38. No railway or marsh there.
- **Burdett Road, Limehouse (west of the road, down to the Cut):** the tramway 25–29·5 (ticks on the rails are the survey marks), side streets 29·5–31; wall B.M.s 25–33. The Cut frontage, wharves and works carry no figures.
- **Two-line B.M.s:** a two-line "B.M. / value" can have its pheon about 22 px away on the opposite road edge; a rotated "T" in the street lettering beside it looks like a pheon.
- **Interpuncts beside figures:** DOWNSELL (·E, O·); ROAD on Millais Road (A·D).
- **Joins:** py ~537 full width on 131045_87116 (missed by the tool) and px ~253–256 full height there; none on 131069_87113, 131051_87113 or 131048_87158.
