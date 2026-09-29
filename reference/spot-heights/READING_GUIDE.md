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
- `embankment_top`: the crest of a railway, sewer or flood bank, or a towing path on a bank. Figures on foreshore beside a bank also count.
- `embankment_foot`: ground at the foot of a bank.
- `wall_top`: river wall, quay, lock side or canal wall, including figures written over a channel with the dot on the wall.
- `bridge`: bridge deck, approach ramp, or a B.M. on a parapet or abutment.
- `railway`: a dot on the rails at grade, not on an embankment.
- `building`: a B.M. on a building or ordinary wall at street level, or a figure written on a building.
- `water`: a genuine water level. None has been found so far.
- `other`: none of the above. Say what it is in `notes`.

Rules:

- **Classify by what the dot or pheon stands on**, not by where the lettering is.
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
- **Figures over channels are wall tops**, with the dot on the bank. There are no water levels.
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
