# Spot-height extraction prototype: OS London five-foot, 1893–96

**Scope.** 15 mosaics (zoom 18, 4×4 tiles, 1-tile overlap). Claude read 7 of them (Mill Meads, Channelsea, Abbey Mills, Three Mills, High Street). EPFL text polygons land on the matching lettering within 1 m, confirming the georeferencing.

**Readings.** 129 readings reduce to 105 distinct marks: 84 spot heights (6.3–31.6 ft) and 21 bench marks (9.77–28.25 ft). I found **no water levels**. Figures over channels are wall tops (dots on the bank).
- Marsh and low ground: 6.3–7.7 ft
- Drain banks: 8.4–9.7 ft
- Abbey Lane streets: 7.6–10.8 ft
- High Street and bridges: 15.3–22.4 ft
- River walls: 16.4–18.9 ft
- Northern Outfall Sewer: 31.6 ft

**Datum.** Heights are in feet above Ordnance Datum (Liverpool). With Trinity High Water at about 12.5 ft O.D., the meads sit roughly 5 ft below ordinary high tide and the walls 4–6 ft above it. No Newlyn correction applied.

**EPFL agreement.** 8 EPFL labels with digits fall in the area read. 7 agree exactly. The eighth, "M.730", is my B.M.17·39 misread by EPFL; it matched only on its text box, because the pheon sits 16 m from the text centroid. 97 of my marks have no EPFL label.

**Failure modes.**
- Digits are about 6 px tall. Reading needs 2× crops; 3/8, 6/9 and dot position need 4–8×.
- The survey dot is easily confused with the middot decimal, and it sits left, right or above the figures. About a third of dot positions are estimates.
- OS sheet joins (tint change, 1–2 px offset) cross three mosaics, and figures on crop edges were split.
- Milepost figures ("Ilford 4 / London 3") risk false positives.
- Duplicates across overlapping mosaics are not independent measurements.

**Reliability.** Values are probably 90–95% correct: about 98% for high-confidence reads. Position is ±3 m where the dot was seen and ±5–10 m otherwise.

**Scaled pipeline.** Needs an API key for the anthropic SDK.
1. Cut each mosaic into overlapping 512 px crops, upscale 2×, and request tool-use JSON.
2. Run a 4–8× verification call on every detection.
3. Snap each mark to its dot with classical CV.
4. Merge across overlaps and validate: B.M. to 2 dp, spots to 1 dp, 0–40 ft.
5. Send low-confidence marks to human review.

The downloaded area (about 700 mosaics) implies 6–10k vision calls.
