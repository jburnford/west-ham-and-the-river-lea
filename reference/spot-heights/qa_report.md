# Spot-height merge: QA report

4393 readings in 235 files (195 mosaics; readers: opus-a 7, opus-aa 5, opus-ab 5, opus-ac 5, opus-ad 5, opus-ae 5, opus-af 5, opus-ag 5, opus-ah 5, opus-ai 5, opus-aj 5, opus-ak 5, opus-al 8, opus-am 5, opus-an 8, opus-ao 5, opus-ap 8, opus-aq 2, opus-b 8, opus-c 6, opus-d 6, opus-e 6, opus-f 6, opus-g 6, opus-h 6, opus-i 6, opus-j 6, opus-k 6, opus-l 5, opus-m 5, opus-n 5, opus-o 5, opus-p 5, opus-q 5, opus-r 5, opus-s 5, opus-t 5, opus-u 5, opus-v 5, opus-w 5, opus-x 5, opus-y 5, opus-z 5) -> **2256 distinct marks**.
Clustering: same type, within 6 m, value within 0.15 ft; same-file readings never merged; disagreeing values at one spot flagged as disputed.

## Marks by type and confidence

| type | n | high | medium | low | disputed | range ft |
|---|---:|---:|---:|---:|---:|---|
| bench_mark | 512 | 425 | 61 | 26 | 11 | 4.25-48.57 |
| spot | 1744 | 1012 | 679 | 53 | 35 | 2.90-52.00 |

Marks seen by 1 / 2 / 3+ readers: 1094 / 768 / 394; seen in more than one mosaic: 977.
Position spread of repeated readings (max distance from mark centre): median 0.4 m, 90th pct 1.4 m, max 4.8 m.

## Marks by layer

Primary layer of each mark (the winning reading's; five-foot first). 1890s layers (five-foot, 25-inch) may share a mark; the 1848-51 skeleton never joins them (ids sk_E_N).

| layer | scale | epoch | n | spot | bench_mark | high | medium | low | disputed | also on another layer | median ft | range ft |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| five-foot | 1:1056 | 1890s | 2192 | 1698 | 494 | 1385 | 728 | 79 | 46 | 0 | 17.4 | 2.90-48.57 |
| 25-inch | 1:2500 | 1890s | 64 | 46 | 18 | 52 | 12 | 0 | 0 | 0 | 28.0 | 4.00-52.00 |

## Marks by setting

| setting | n | spot | bench_mark | high | medium | low | from reader | inferred | of which value fallback | setting conflict | median ft | range ft |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| marsh | 69 | 68 | 1 | 55 | 14 | 0 | 46 | 23 | 18 | 14 | 6.3 | 2.90-16.50 |
| open_ground | 53 | 50 | 3 | 38 | 14 | 1 | 14 | 39 | 13 | 12 | 28.1 | 10.70-35.00 |
| street | 1224 | 1223 | 1 | 687 | 497 | 40 | 696 | 528 | 0 | 32 | 18.0 | 2.90-52.00 |
| yard | 90 | 86 | 4 | 56 | 30 | 4 | 62 | 28 | 0 | 19 | 16.8 | 6.10-29.10 |
| embankment_top | 124 | 117 | 7 | 88 | 35 | 1 | 27 | 97 | 0 | 27 | 17.2 | 6.20-39.10 |
| embankment_foot | 15 | 10 | 5 | 14 | 1 | 0 | 6 | 9 | 0 | 5 | 13.0 | 3.40-18.00 |
| wall_top | 97 | 81 | 16 | 52 | 41 | 4 | 77 | 20 | 0 | 8 | 17.4 | 13.87-24.35 |
| bridge | 78 | 46 | 32 | 52 | 25 | 1 | 26 | 52 | 0 | 10 | 25.0 | 5.46-48.57 |
| railway | 37 | 35 | 2 | 23 | 11 | 3 | 13 | 24 | 0 | 5 | 16.6 | 7.00-32.10 |
| building | 423 | 17 | 406 | 343 | 58 | 22 | 243 | 180 | 0 | 13 | 19.1 | 4.50-40.82 |
| other | 32 | 2 | 30 | 23 | 8 | 1 | 32 | 0 | 0 | 5 | 7.7 | 4.25-35.00 |
| unknown | 14 | 9 | 5 | 6 | 6 | 2 | 0 | 0 | 0 | 0 | 15.5 | 8.80-32.20 |

Setting from readers for 1242 marks, inferred from notes (spot_height_setting.py) for 1000, unknown for 14 (0.6%).

## Inter-reader agreement (mosaics read by two or more readers)

| mosaic | readers | both | value agrees (<=0.15) | exact | only A | only B | pos. spread median / max m |
|---|---|---:|---:|---:|---:|---:|---|
| m18_131054_87125 | opus-g / opus-k | 17 | 17 | 17 | 0 | 0 | 0.5 / 6.0 |
| m18_131054_87128 | opus-h / opus-j | 16 | 16 | 16 | 0 | 0 | 0.4 / 1.1 |
| m18_131057_87125 | opus-d / opus-f | 15 | 15 | 15 | 0 | 0 | 0.4 / 1.1 |
| m18_131060_87128 | opus-c / opus-e | 15 | 15 | 15 | 0 | 0 | 0.5 / 1.9 |
| m18_131060_87134 | opus-h / opus-i | 14 | 14 | 14 | 1 | 1 | 1.2 / 3.7 |
| m18_131066_87134 | opus-b / opus-d | 25 | 24 | 24 | 2 | 3 | 0.7 / 2.5 |
| m18_131066_87167 | opus-aj / opus-am | 35 | 35 | 34 | 1 | 0 | 0.4 / 2.0 |
| m18_131069_87125 | opus-e / opus-g | 31 | 31 | 31 | 0 | 0 | 0.7 / 5.8 |
| m18_131069_87128 | opus-f / opus-h | 34 | 34 | 34 | 0 | 0 | 0.8 / 7.9 |
| m18_131069_87131 | opus-g / opus-k | 34 | 34 | 34 | 0 | 0 | 0.4 / 3.0 |
| m18_131072_87128 | opus-i / opus-l | 35 | 35 | 35 | 1 | 1 | 0.7 / 4.8 |
| m18_131072_87146 | opus-ag / opus-ai | 14 | 14 | 14 | 1 | 1 | 0.4 / 2.4 |
| m18_131072_87149 | opus-ab / opus-ad | 18 | 17 | 17 | 0 | 0 | 0.4 / 2.3 |
| m18_131072_87158 | opus-v / opus-x | 31 | 30 | 30 | 0 | 0 | 0.4 / 5.3 |
| m18_131075_87143 | opus-ao / opus-aq | 22 | 22 | 22 | 0 | 0 | 0.7 / 2.6 |
| m18_131075_87146 | opus-af / opus-ah | 20 | 20 | 20 | 0 | 0 | 0.4 / 4.8 |
| m18_131075_87152 | opus-aa / opus-x | 15 | 15 | 14 | 1 | 0 | 0.0 / 0.7 |
| m18_131078_87149 | opus-ac / opus-ae | 13 | 13 | 13 | 3 | 3 | 0.8 / 5.1 |
| m18_131078_87158 | opus-w / opus-y | 31 | 31 | 31 | 2 | 2 | 0.5 / 4.3 |
| m18_131078_87164 | opus-aa / opus-ac | 27 | 26 | 26 | 0 | 0 | 0.4 / 5.9 |
| m18_131081_87134 | opus-u / opus-v | 28 | 28 | 28 | 0 | 0 | 0.8 / 6.0 |
| m18_131081_87155 | opus-ab / opus-z | 29 | 29 | 29 | 0 | 0 | 0.4 / 3.7 |
| m18_131081_87158 | opus-y / opus-z | 31 | 30 | 30 | 0 | 0 | 0.4 / 2.0 |
| m18_131084_87122 | opus-s / opus-u | 15 | 15 | 15 | 1 | 1 | 0.5 / 1.5 |
| m18_131084_87128 | opus-o / opus-q | 15 | 13 | 13 | 1 | 1 | 0.4 / 5.5 |
| m18_131084_87155 | opus-ad / opus-af | 24 | 24 | 24 | 0 | 0 | 0.7 / 4.2 |
| m18_131084_87161 | opus-ae / opus-ag | 17 | 15 | 14 | 0 | 0 | 0.4 / 1.7 |
| m18_131087_87128 | opus-l / opus-o | 19 | 18 | 18 | 2 | 2 | 0.5 / 4.1 |
| m18_131087_87137 | opus-q / opus-s | 20 | 20 | 20 | 2 | 2 | 0.5 / 3.7 |
| m18_131087_87158 | opus-ai / opus-aj | 20 | 20 | 20 | 0 | 0 | 0.4 / 0.8 |
| m18_131087_87164 | opus-am / opus-ao | 23 | 22 | 22 | 0 | 0 | 0.4 / 2.1 |
| m18_131090_87128 | opus-k / opus-m | 24 | 24 | 23 | 0 | 0 | 0.4 / 3.3 |
| m18_131090_87140 | opus-t / opus-w | 17 | 17 | 17 | 1 | 1 | 0.4 / 0.7 |
| m18_131093_87134 | opus-m / opus-n | 20 | 20 | 19 | 0 | 0 | 0.4 / 4.5 |
| m18_131096_87134 | opus-n / opus-p | 25 | 23 | 22 | 0 | 0 | 0.8 / 5.6 |
| m18_131096_87137 | opus-r / opus-t | 15 | 15 | 15 | 0 | 0 | 0.7 / 1.9 |
| m18_131099_87128 | opus-p / opus-r | 22 | 21 | 21 | 0 | 0 | 1.1 / 2.2 |
| q18_131099_87146 | opus-ak / opus-al | 7 | 7 | 7 | 0 | 0 | 0.5 / 1.2 |
| q18_131099_87155 | opus-al / opus-an | 4 | 4 | 4 | 0 | 0 | 0.6 / 0.8 |
| q18_131105_87131 | opus-an / opus-ap | 5 | 5 | 5 | 1 | 2 | 1.1 / 1.5 |

Overall: value agreement 828/842 = 98.3% (exact 97.6%); marks found by both readers 842/882 = 95.5%; position spread median 0.5 m.

### Disputes
- sh_538578_183745 spot: opus-b 10·9 vs opus-d 10·2
- sh_539126_182432 spot: opus-ab 11·6 vs opus-ad 11·8
- sh_538997_181536 spot: opus-v 18·6 vs opus-x 13·6
- sh_539716_180909 spot: opus-aa 5·6 vs opus-ac 5·8
- sh_540048_181519 bench_mark: opus-y B.M.6·66 vs opus-z B.M.6·86
- sh_540178_184435 spot: opus-o 35·6 vs opus-q 35·0
- sh_540015_184251 spot: opus-o 30·6 vs opus-q 30·0
- sh_540172_181108 bench_mark: opus-ae B.M.6·32 vs opus-ag B.M.8·32
- sh_540060_181099 spot: opus-ae 5·8 vs opus-ag 5·6
- sh_540237_184432 spot: opus-l 34·8 vs opus-o 34·6
- sh_540689_180999 spot: opus-am 6·6 vs opus-ao 5·6
- sh_541443_184060 spot: opus-n 29·8 vs opus-p 29·3
- sh_541260_183806 bench_mark: opus-n B.M.35·78 vs opus-p B.M.3?·78
- sh_541739_184607 spot: opus-p 35·8 vs opus-r 35·3

## Cross-reader agreement on shared marks (any mosaic, including overlap strips)

1162 marks read by 2+ readers: value agreement (<= 0.15 ft) 1128/1162 = 97.1%, exact 1116/1162 = 96.0%; distance between readers' positions median 0.5 m, max 7.9 m.
These come from overlap strips between neighbouring mosaics read by different readers; they are not a substitute for full double reads of whole mosaics.

## All disputed marks

- sh_538255_185638 spot values {'opus-h': [22.3], 'opus-i': [22.8]} (opus-h:m18_131063_87116@952,142=22.3(m); opus-i:m18_131066_87116@174,137=22.8(m))
- sh_537953_185588 spot values {'opus-h': [15.4], 'opus-i': [16.4]} (opus-h:m18_131063_87116@132,254=15.4(h); opus-i:m18_131060_87116@899,253=16.4(l))
- sh_540256_184948 bench_mark values {'opus-q': [33.57], 'opus-s': [35.57], 'opus-u': [35.57]} (opus-s:m18_131084_87122@896,612=35.57(h); opus-u:m18_131084_87122@895,611=35.57(m); opus-q:m18_131087_87122@127,609=33.57(m))
- sh_540587_184805 bench_mark values {'opus-l': [34.28], 'opus-n': [34.23], 'opus-o': [34.23], 'opus-q': [34.23]} (opus-n:m18_131087_87125@1003,256=34.23(h); opus-q:m18_131087_87122@1015,1015=34.23(m); opus-o:m18_131090_87122@238,1021=34.23(m); opus-l:m18_131090_87125@237,256=34.28(l))
- sh_541353_184609 spot values {'opus-m': [31.3], 'opus-n': [31.9]} (opus-n:m18_131096_87125@746,839=31.9(l); opus-m:m18_131096_87128@746,71=31.3(l))
- sh_541739_184607 spot values {'opus-p': [35.8], 'opus-r': [35.3]} (opus-r:m18_131099_87125@1015,872=35.3(l); opus-p:m18_131099_87128@1016,106=35.8(l); opus-r:m18_131099_87128@1015,104=35.3(l))
- sh_540690_184492 bench_mark values {'opus-k': [36.36], 'opus-m': [36.38]} (opus-k:m18_131090_87128@492,337=36.36(l); opus-m:m18_131090_87128@491,335=36.38(l))
- sh_540178_184435 spot values {'opus-o': [35.6], 'opus-q': [35.0]} (opus-o:m18_131084_87128@649,452=35.6(m); opus-q:m18_131084_87128@649,452=35.0(l))
- sh_540237_184432 spot values {'opus-l': [34.8], 'opus-o': [34.6], 'opus-q': [34.6]} (opus-q:m18_131084_87128@809,461=34.6(m); opus-o:m18_131084_87128@808,461=34.6(l); opus-l:m18_131087_87128@37,466=34.8(l); opus-o:m18_131087_87128@40,466=34.6(l))
- sh_540015_184251 spot values {'opus-o': [30.6], 'opus-q': [30.0], 'opus-s': [30.0]} (opus-s:m18_131081_87128@966,935=30.0(h); opus-s:m18_131081_87131@965,167=30.0(h); opus-q:m18_131084_87128@197,934=30.0(h); opus-o:m18_131084_87128@197,934=30.6(m); opus-o:m18_131084_87131@197,166=30.6(m))
- sh_538897_184218 bench_mark values {'opus-i': [20.79], 'opus-j': [20.19], 'opus-l': [20.79]} (opus-j:m18_131072_87131@262,172=20.19(h); opus-i:m18_131072_87128@261,940=20.79(m); opus-l:m18_131072_87128@263,939=20.79(l))
- sh_541443_184060 spot values {'opus-m': [29.8], 'opus-n': [29.8], 'opus-p': [29.3, 29.8], 'opus-r': [29.9]} (opus-m:m18_131096_87131@942,777=29.8(l); opus-n:m18_131096_87134@947,24=29.8(l); opus-p:m18_131096_87134@950,22=29.3(l); opus-p:m18_131099_87131@176,784=29.8(l); opus-r:m18_131099_87134@181,24=29.9(l))
- sh_540872_184026 spot values {'opus-k': [33.6], 'opus-l': [33.6], 'opus-m': [33.6], 'opus-n': [33.5]} (opus-m:m18_131093_87134@179,69=33.6(m); opus-k:m18_131090_87131@947,838=33.6(l); opus-l:m18_131090_87134@947,70=33.6(l); opus-k:m18_131093_87131@179,837=33.6(l); opus-n:m18_131093_87134@178,69=33.5(l))
- sh_541360_183972 bench_mark values {'opus-m': [33.94], 'opus-n': [33.94], 'opus-p': [33.84]} (opus-m:m18_131096_87131@716,1019=33.94(h); opus-n:m18_131096_87134@717,250=33.94(m); opus-p:m18_131096_87134@716,249=33.84(l))
- sh_540268_183929 spot values {'opus-n': [30.6], 'opus-q': [30.8]} (opus-q:m18_131084_87134@851,285=30.8(h); opus-n:m18_131087_87134@83,283=30.6(l))
- sh_540305_183890 spot values {'opus-n': [26.3], 'opus-q': [28.3]} (opus-q:m18_131084_87134@950,392=28.3(m); opus-n:m18_131087_87134@180,394=26.3(m))
- sh_541260_183806 bench_mark values {'opus-n': [35.78], 'opus-p': [30.78]} (opus-n:m18_131096_87134@436,690=35.78(l); opus-p:m18_131096_87134@435,690=30.78(l))
- sh_538578_183745 spot values {'opus-b': [10.9], 'opus-d': [10.2]} (opus-b:m18_131066_87134@908,653=10.9(l); opus-d:m18_131066_87134@909,655=10.2(l); opus-b:m18_131069_87134@141,653=10.9(l))
- sh_540596_183716 spot values {'opus-l': [25.8], 'opus-n': [25.6], 'opus-p': [25.6], 'opus-q': [25.6], 'opus-s': [25.6]} (opus-n:m18_131087_87134@951,882=25.6(h); opus-l:m18_131090_87134@183,882=25.8(h); opus-p:m18_131090_87137@182,114=25.6(h); opus-s:m18_131087_87137@951,114=25.6(m); opus-q:m18_131087_87137@951,114=25.6(l))
- sh_538397_183656 spot values {'opus-a': [21.3], 'opus-b': [21.9], 'opus-d': [21.9]} (opus-d:m18_131066_87134@416,878=21.9(m); opus-a:m18_131066_87137@418,113=21.3(m); opus-b:m18_131066_87134@414,881=21.9(l))
- sh_538486_183653 spot values {'opus-a': [15.8], 'opus-b': [15.6], 'opus-d': [15.6]} (opus-b:m18_131066_87134@653,897=15.6(m); opus-d:m18_131066_87134@654,897=15.6(m); opus-a:m18_131066_87137@653,125=15.8(m))
- sh_539767_182564 spot values {'opus-ac': [5.0], 'opus-ae': [5.0, 6.0], 'opus-ah': [5.0], 'opus-aj': [5.0]} (opus-ah:m18_131078_87146@942,851=5.0(h); opus-aj:m18_131081_87146@174,850=5.0(h); opus-ac:m18_131078_87149@943,84=5.0(l); opus-ae:m18_131078_87149@942,82=5.0(l); opus-ae:m18_131081_87149@174,82=6.0(l))
- sh_538304_182442 spot values {'opus-ah': [16.3], 'opus-ao': [15.3]} (opus-ao:m18_131063_87149@845,303=15.3(m); opus-ah:m18_131066_87149@77,303=16.3(l))
- sh_538640_182438 spot values {'opus-ad': [5.8], 'opus-ah': [5.6]} (opus-ah:m18_131066_87149@977,339=5.6(l); opus-ad:m18_131069_87149@210,339=5.8(l))
- sh_539126_182432 spot values {'opus-ab': [11.6], 'opus-ad': [11.8]} (opus-ab:m18_131072_87149@746,390=11.6(l); opus-ad:m18_131072_87149@746,391=11.8(l))
- sh_538872_182281 spot values {'opus-aa': [5.8], 'opus-ab': [5.6], 'opus-ad': [5.6], 'opus-x': [5.6]} (opus-x:m18_131072_87152@52,10=5.6(h); opus-ad:m18_131069_87149@821,778=5.6(m); opus-aa:m18_131069_87152@820,10=5.8(m); opus-ad:m18_131072_87149@52,778=5.6(m); opus-ab:m18_131072_87149@53,778=5.6(l))
- sh_538868_182279 bench_mark values {'opus-aa': [7.38], 'opus-ab': [7.36], 'opus-ad': [7.36], 'opus-x': [7.38]} (opus-aa:m18_131069_87152@809,17=7.38(m); opus-x:m18_131072_87152@42,16=7.38(m); opus-ad:m18_131069_87149@812,784=7.36(l); opus-ab:m18_131072_87149@43,785=7.36(l); opus-ad:m18_131072_87149@44,784=7.36(l))
- sh_540303_182260 spot values {'opus-af': [6.5], 'opus-ai': [5.5], 'opus-am': [5.5]} (opus-ai:m18_131084_87149@822,941=5.5(h); opus-af:m18_131084_87152@822,172=6.5(h); opus-am:m18_131087_87152@54,173=5.5(h))
- sh_538335_182238 spot values {'opus-ae': [18.5], 'opus-ah': [15.5], 'opus-ai': [18.5], 'opus-ao': [15.5]} (opus-ai:m18_131063_87152@912,88=18.5(h); opus-ao:m18_131063_87149@912,855=15.5(m); opus-ah:m18_131066_87149@144,854=15.5(m); opus-ae:m18_131066_87152@144,86=18.5(l))
- sh_538301_182170 spot values {'opus-ae': [16.1], 'opus-ai': [18.1]} (opus-ai:m18_131063_87152@820,266=18.1(h); opus-ae:m18_131066_87152@44,266=16.1(l))
- sh_539482_182024 spot values {'opus-aa': [4.6], 'opus-x': [4.5], 'opus-y': [4.5]} (opus-x:m18_131075_87152@905,746=4.5(h); opus-y:m18_131078_87152@138,746=4.5(h); opus-aa:m18_131075_87152@905,746=4.6(l))
- sh_539957_182011 spot values {'opus-aa': [5.6], 'opus-ab': [5.5], 'opus-z': [5.5]} (opus-ab:m18_131081_87155@643,50=5.5(h); opus-z:m18_131081_87155@643,50=5.5(h); opus-aa:m18_131081_87152@643,818=5.6(l))
- sh_539802_181999 spot values {'opus-aa': [6.5], 'opus-ab': [6.5], 'opus-w': [6.8], 'opus-y': [6.5], 'opus-z': [6.5]} (opus-aa:m18_131081_87152@226,839=6.5(h); opus-ab:m18_131081_87155@226,71=6.5(h); opus-z:m18_131081_87155@226,71=6.5(h); opus-y:m18_131078_87152@994,835=6.5(l); opus-w:m18_131078_87155@995,71=6.8(l))
- sh_538575_181928 spot values {'opus-ab': [17.9], 'opus-ae': [17.8]} (opus-ae:m18_131066_87152@766,940=17.8(h); opus-ab:m18_131066_87155@766,172=17.9(l))
- sh_538340_181563 spot values {'opus-ab': [6.3], 'opus-ag': [8.3]} (opus-ag:m18_131063_87158@877,367=8.3(m); opus-ab:m18_131066_87158@109,367=6.3(l))
- sh_538997_181536 spot values {'opus-v': [18.6], 'opus-x': [13.6]} (opus-v:m18_131072_87158@334,490=18.6(m); opus-x:m18_131072_87158@334,490=13.6(l))
- sh_540048_181519 bench_mark values {'opus-ac': [6.86], 'opus-y': [6.66], 'opus-z': [6.86]} (opus-y:m18_131081_87158@850,613=6.66(m); opus-z:m18_131081_87158@850,610=6.86(l); opus-ac:m18_131084_87158@83,613=6.86(l))
- sh_540175_181462 spot values {'opus-ac': [6.6], 'opus-ae': [6.5], 'opus-ag': [6.6]} (opus-ac:m18_131084_87158@420,777=6.6(m); opus-ag:m18_131084_87161@419,8=6.6(m); opus-ae:m18_131084_87161@422,9=6.5(l))
- sh_540172_181108 bench_mark values {'opus-ae': [6.32], 'opus-ag': [8.32]} (opus-ag:m18_131084_87161@385,960=8.32(m); opus-ag:m18_131084_87164@385,192=8.32(m); opus-ae:m18_131084_87161@386,964=6.32(l))
- sh_540060_181099 spot values {'opus-ac': [6.8], 'opus-ae': [5.8], 'opus-ag': [5.6], 'opus-z': [6.6]} (opus-ag:m18_131084_87161@84,977=5.6(m); opus-ag:m18_131084_87164@84,209=5.6(m); opus-z:m18_131081_87161@852,977=6.6(l); opus-ac:m18_131081_87164@853,210=6.8(l); opus-ae:m18_131084_87161@84,977=5.8(l))
- sh_538491_181092 bench_mark values {'opus-ac': [16.89], 'opus-af': [16.69]} (opus-ac:m18_131066_87161@481,879=16.89(h); opus-af:m18_131066_87164@480,109=16.69(m))
- sh_538273_181043 spot values {'opus-ah': [16.8], 'opus-am': [16.9]} (opus-am:m18_131063_87164@659,232=16.9(m); opus-ah:m18_131063_87161@658,990=16.8(l))
- sh_540689_180999 spot values {'opus-am': [6.6], 'opus-ao': [5.6]} (opus-am:m18_131087_87164@996,523=6.6(l); opus-ao:m18_131087_87164@997,523=5.6(l))
- sh_539716_180909 spot values {'opus-aa': [5.6], 'opus-ac': [5.8]} (opus-ac:m18_131078_87164@682,694=5.8(h); opus-aa:m18_131078_87164@682,693=5.6(l))
- sh_539711_180831 spot values {'opus-aa': [6.9], 'opus-ac': [6.9], 'opus-ae': [6.8]} (opus-ac:m18_131078_87164@664,902=6.9(h); opus-aa:m18_131078_87164@664,903=6.9(m); opus-ae:m18_131078_87167@664,135=6.8(l))
- sh_538479_180707 bench_mark values {'opus-aj': [14.05], 'opus-am': [14.06]} (opus-am:m18_131066_87167@418,379=14.06(h); opus-aj:m18_131066_87167@419,379=14.05(l))

## Value histogram (2 ft bins, distinct marks)

```
    2-4   ft   28 ####
    4-6   ft  160 #######################
    6-8   ft  262 #####################################
    8-10  ft  119 #################
   10-12  ft   73 ##########
   12-14  ft   98 ##############
   14-16  ft  174 #########################
   16-18  ft  280 ########################################
   18-20  ft  145 #####################
   20-22  ft   87 ############
   22-24  ft   84 ############
   24-26  ft   74 ###########
   26-28  ft   89 #############
   28-30  ft  103 ###############
   30-32  ft  142 ####################
   32-34  ft  169 ########################
   34-36  ft  130 ###################
   36-38  ft   25 ####
   38-40  ft    5 #
   40-42  ft    3 
   42-44  ft    0 
   44-46  ft    0 
   46-48  ft    1 
   48-50  ft    2 
   50-52  ft    2 
   52-54  ft    1 
```

## Rule checks (per reading)

All readings pass: five-foot spots 1 dp / bench marks 2 dp, 25-inch spots 0 dp / bench marks 1 dp, skeleton spots and bench marks 1 dp; raw matches value_ft; values 0-120 ft.

Different types at the same spot:
- sh_539014_181449 spot 16·6 and sh_539017_181447 bench_mark B.M.19·01 within 3 m (one mark typed two ways?)

## Unreadable regions reported: 290
- m18_131054_87119.opus-j.json: [543, 0, 549, 1024] vertical sheet join at px ~546 (no figures on it)
- m18_131054_87122.opus-h.json: [0, 732, 1024, 744] horizontal sheet join at py~738 (line + tint step; not reported by the tool)
- m18_131054_87122.opus-h.json: [542, 0, 550, 1024] vertical sheet join at px~546 (line + tint step; reported weak by the tool only for y 768-1024)
- m18_131054_87122.opus-h.json: [455, 1010, 485, 1024] 21·7 ends 2-3 px above the south edge; its dot may lie south of the edge
- m18_131054_87125.opus-g.json: [0, 322, 14, 336] figure ending '·00' (probably a B.M.) cut by west edge
- m18_131054_87125.opus-g.json: [555, 1010, 585, 1024] 21·1 within 3 px of south edge (recorded medium)
- m18_131054_87125.opus-k.json: [0, 312, 16, 330] figure '·00' (probably a B.M.) cut by west edge on Wallis Road
- m18_131054_87125.opus-k.json: [540, 0, 548, 1024] vertical sheet join at px ~544 (tint step); no figures crossed
- m18_131054_87128.opus-h.json: [544, 0, 550, 1024] vertical sheet join at px~546 (line + tint change; water colour stops at it)
- m18_131054_87128.opus-h.json: [0, 930, 1024, 944] horizontal sheet join at py~937 (tint step, brown-tinted sheet south of it; tool did not report it)
- m18_131054_87128.opus-h.json: [0, 684, 4, 700] 'B' of B.M.24·35 touches the west edge
- m18_131054_87128.opus-j.json: [0, 684, 6, 700] B of B.M.24·35 clipped by the west edge (value itself whole and read)
- m18_131054_87128.opus-j.json: [0, 932, 1024, 942] horizontal sheet join at py ~937 (no figures on it)
- m18_131054_87131.opus-j.json: [120, 1016, 160, 1024] figure (tops of digits only) cut by the south edge beside the Northern Outfall Sewer / Wick Lane
- m18_131054_87131.opus-j.json: [0, 165, 1024, 175] horizontal sheet join at py ~170 (no figures on it)
- m18_131057_87116.opus-j.json: [630, 470, 715, 530] dense lettering and boundary-stone symbols at Templemills Bridge; pheon of B.M.19·23 not identifiable
- m18_131057_87116.opus-j.json: [0, 530, 1024, 540] horizontal sheet join at py ~535 (no figures on it)
- m18_131057_87119.opus-g.json: [1005, 456, 1024, 470] B.M. value cut by east edge (pheon at about 998,462)
- m18_131057_87122.opus-f.json: [0, 734, 1024, 740] weak horizontal sheet join (tint step) not detected by the tool; no figure is cut by it
- m18_131057_87131.opus-g.json: [0, 624, 3, 636] B of B.M.22·84 cut by west edge (digits whole, recorded)
- m18_131060_87116.opus-i.json: [1010, 10, 1024, 30] figure beginning '16' cut by the east edge (dot at ~1015,19)
- m18_131060_87116.opus-i.json: [0, 530, 1024, 545] sheet join
- m18_131060_87128.opus-c.json: [990, 578, 1024, 596] B.M. value cut by the east edge (B.M.14·76, read on m18_131063_87128); its pheon at 964,597 is inside this mosaic
- m18_131060_87128.opus-e.json: [990, 578, 1024, 592] B.M. figure cut by the east edge (pheon at 965,596 inside); read in the eastern neighbour
- m18_131060_87158.opus-aq.json: [1008, 595, 1024, 630] lone dot at 1013,603 by the east edge with no figure inside the mosaic (figure presumably east of the edge)
- m18_131063_87116.opus-h.json: [0, 530, 840, 542] horizontal sheet join at py~536 (tint step; darker sheet to the south)
- m18_131063_87116.opus-h.json: [832, 0, 842, 1024] vertical sheet join at px~837 (line + tint step)
- m18_131063_87116.opus-h.json: [935, 0, 960, 25] possible pheon at 943,13 with no B.M. text inside the mosaic; text probably north of the edge
- m18_131063_87119.opus-e.json: [832, 0, 844, 1024] sheet join at px ~838; tint change and possible 1-2 px offsets; no figures on it
- m18_131063_87134.opus-b.json: [1000, 490, 1024, 515] figure '14·?' cut by the east edge of the mosaic; read it in m18_131066_87134
- m18_131063_87134.opus-b.json: [1000, 1005, 1024, 1024] figure '·96' or similar cut by the SE corner; needs m18_131066_87137
- m18_131063_87137.opus-b.json: [1000, 370, 1024, 395] figure '26·?' cut by the east edge; read it in m18_131066_87137
- m18_131063_87149.opus-ao.json: [0, 376, 12, 390] figure ending 0·1 cut by west edge
- m18_131063_87149.opus-ao.json: [824, 0, 834, 1024] vertical sheet join
- m18_131063_87149.opus-ao.json: [0, 760, 1024, 768] horizontal sheet join
- m18_131063_87152.opus-ai.json: [388, 0, 416, 5] figure 24·x cut by the north edge above 'Urinal'
- m18_131063_87152.opus-ai.json: [0, 646, 10, 658] figure '..4' cut by the west edge
- m18_131063_87152.opus-ai.json: [855, 1014, 905, 1024] B.M.18·45(?) text cut by the south edge; pheon not visible
- m18_131063_87158.opus-ag.json: [440, 1012, 475, 1024] 18·8 within 1-2 px of the bottom edge; recorded but check against the southern neighbour
- m18_131063_87158.opus-ag.json: [820, 0, 828, 1024] vertical sheet join at px ~824
- m18_131063_87164.opus-am.json: [988, 982, 1024, 996] B.M.12·04 text cut by east edge, pheon outside the mosaic (read whole in 131066_87167)
- m18_131063_87164.opus-am.json: [1008, 164, 1024, 176] 15·4 ends ~1 px from east edge
- m18_131063_87164.opus-am.json: [320, 1014, 400, 1024] 16·9 and B.M.16·68 touch the bottom edge
- m18_131063_87164.opus-am.json: [818, 0, 828, 1024] vertical sheet join at px ~822-824
- m18_131066_87116.opus-i.json: [165, 0, 190, 20] pheon at the north edge, B.M. text off-mosaic
- m18_131066_87116.opus-i.json: [0, 538, 1024, 548] horizontal sheet join
- m18_131066_87116.opus-i.json: [63, 0, 73, 1024] vertical sheet join
- m18_131066_87119.opus-f.json: [64, 0, 74, 1024] vertical sheet join with strong tint step; western sheet nearly blank, no figures cut
- m18_131066_87125.opus-c.json: [995, 380, 1024, 405] B.M. with pheon (arrow at 1000,399) whose value is cut by the east edge of the mosaic; read it on the mosaic to the east
- m18_131066_87128.opus-d.json: [515, 1015, 540, 1024] figure 12·6 (?) cut by the south edge
- m18_131066_87131.opus-e.json: [0, 162, 1024, 174] sheet join at py ~168; possible 1-2 px offsets; no figures on it
- m18_131066_87131.opus-e.json: [60, 0, 68, 1024] probable vertical sheet join or fold at px ~64; no figures on it
- m18_131066_87134.opus-b.json: [990, 150, 1024, 190] figure '18·?' cut by the east edge; read it in m18_131069_87134
- m18_131066_87134.opus-d.json: [1010, 165, 1024, 180] 18·4 ends at the east edge; a clipped trailing digit cannot be excluded
- m18_131066_87146.opus-b.json: [990, 215, 1024, 240] B.M. 15·9? in the crane oval, cut by the east edge; needs m18_131069_87146
- m18_131066_87146.opus-b.json: [0, 100, 12, 120] figure '·2' (21·2 on Three Mills Bridge) cut by the west edge; read in m18_131063_87146
- m18_131066_87149.opus-ah.json: [318, 1006, 352, 1024] B.M. figure (B.M.20·?) cut by the south edge beside a pheon at ~345,1020
- m18_131066_87152.opus-ae.json: [0, 350, 4, 366] B.M. letters of B.M.17·19 cut by the west edge
- m18_131066_87152.opus-ae.json: [110, 1014, 150, 1024] B.M.18·45 text clipped by the south edge
- m18_131066_87152.opus-ae.json: [985, 566, 1024, 586] B.M. figure cut by the east edge (only B.M.1 visible); pheon at ~987,571
- m18_131066_87152.opus-ae.json: [55, 0, 61, 1024] probable vertical sheet join at px ~57-59
- m18_131066_87161.opus-ac.json: [372, 1016, 395, 1024] figure '1?·1' cut by the bottom edge
- m18_131066_87161.opus-ac.json: [54, 0, 61, 1024] probable sheet join at px ~57
- m18_131066_87161.opus-ac.json: [688, 0, 706, 8] 7·4 within 1 px of top edge; dot may be off-sheet
- m18_131066_87164.opus-af.json: [0, 534, 20, 560] B.M. '?2·53' cut by the west edge (B and leading digit lost); pheon at ~4,538 on house front; whole in the western neighbour
- m18_131066_87164.opus-af.json: [300, 330, 1024, 560] East India Dock basin water, no heights
- m18_131066_87167.opus-aj.json: [0, 400, 20, 420] 7·7 at the west edge; its survey dot may lie outside the mosaic
- m18_131066_87167.opus-aj.json: [0, 815, 16, 838] 7·3 starts at the west edge; leading digit may be clipped
- m18_131066_87167.opus-am.json: [0, 822, 12, 836] figure "?7·3" cut by west edge (leading digit may be missing); read in western neighbour
- m18_131066_87167.opus-am.json: [0, 584, 20, 600] B.M.19·67 text begins at the west edge; recorded but check against neighbour
- m18_131066_87167.opus-am.json: [0, 400, 20, 416] 7·7 begins ~3 px from west edge; recorded but a leading digit cannot be excluded
- m18_131066_87167.opus-am.json: [48, 0, 58, 1024] vertical sheet join at px ~52-54
- m18_131069_87122.opus-f.json: [998, 590, 1024, 606] B.M. text by Waddington Road cut by east edge; value beyond edge
- m18_131069_87122.opus-f.json: [0, 739, 1024, 745] weak horizontal sheet join (tint step) not detected by the tool; no figure cut
- m18_131069_87128.opus-f.json: [0, 932, 1024, 942] horizontal sheet join with tint change; 16·0 at 414,930 just above it reads clearly
- m18_131069_87128.opus-f.json: [1004, 886, 1024, 906] figure '18·?' with dot at 1002,897 cut by east edge
- m18_131069_87128.opus-f.json: [0, 1010, 12, 1024] figure ending '·0' cut by west edge / south-west corner
- m18_131069_87128.opus-f.json: [395, 1012, 445, 1024] B.M.19·20 text within 3-7 px of south edge; pheon probably in the mosaic to the south
- m18_131069_87128.opus-h.json: [1006, 886, 1024, 904] figure '18·?' cut by the east edge (dot at 1001,896)
- m18_131069_87128.opus-h.json: [0, 1010, 12, 1024] figure '·0' cut by the west/south corner
- m18_131069_87128.opus-h.json: [0, 932, 1024, 944] horizontal sheet join, tint change and 1-2 px offsets
- m18_131069_87128.opus-h.json: [70, 230, 100, 255] 24·2 partly obscured by rails; dot not separable from rails
- m18_131069_87131.opus-g.json: [1012, 120, 1024, 136] figure '16..' cut by east edge (dot at 1001,127)
- m18_131069_87131.opus-g.json: [1008, 688, 1024, 706] B.M.15·2? cut by east edge; pheon probably at 988,707
- m18_131069_87131.opus-g.json: [1006, 960, 1024, 976] 13·5 clipped at east edge (recorded low)
- m18_131069_87131.opus-g.json: [910, 1016, 930, 1024] figure 13·5? cut by south edge
- m18_131069_87131.opus-g.json: [0, 246, 8, 258] figure ending '·0' cut by west edge
- m18_131069_87131.opus-k.json: [0, 248, 10, 260] figure '·0' cut by west edge on Kennard Road
- m18_131069_87131.opus-k.json: [1016, 120, 1024, 136] figure '16...' cut by east edge
- m18_131069_87131.opus-k.json: [1008, 688, 1024, 704] B.M.15·2. cut by east edge (pheon at 988,706 inside)
- m18_131069_87131.opus-k.json: [1010, 958, 1024, 975] 13·5 trailing digit at the east edge, possibly clipped
- m18_131069_87131.opus-k.json: [895, 1015, 925, 1024] figure '13·5' cut by south edge
- m18_131069_87131.opus-k.json: [0, 164, 1024, 174] horizontal sheet join at py ~168-170; no figure crosses it
- m18_131069_87134.opus-b.json: [995, 450, 1024, 480] figure '13·?' cut by the east edge, dot at about 1009,469; needs the mosaic to the east
- m18_131069_87158.opus-x.json: [110, 1012, 145, 1024] marks cut by the S edge (possible figure below)
- m18_131069_87167.opus-af.json: [415, 0, 440, 8] 17·0 touches the north edge; read whole but recorded medium
- m18_131069_87167.opus-af.json: [300, 90, 1024, 400] East India (Export) Dock basin water, no heights
- m18_131069_87167.opus-af.json: [200, 560, 1024, 1024] River Thames, no heights
- m18_131072_87119.opus-j.json: [0, 22, 10, 58] west edge: pheon at ~8,30 whose B.M. text lies off-mosaic, and a figure ending '5' at ~2,52 cut by the edge
- m18_131072_87122.opus-i.json: [0, 737, 1024, 747] sheet join; 1-2 px offsets
- m18_131072_87125.opus-h.json: [0, 340, 4, 366] 'B' of B.M.40·27 clipped by the west edge (value whole)
- m18_131072_87128.opus-i.json: [370, 1015, 400, 1024] figure (possibly 17·8) and a dot cut by the south edge
- m18_131072_87128.opus-i.json: [0, 934, 1024, 944] sheet join; 1-2 px offsets
- m18_131072_87128.opus-l.json: [370, 1012, 400, 1024] figure (17·6?) and a pheon-like mark cut by the south edge
- m18_131072_87128.opus-l.json: [0, 885, 5, 900] pheon of B.M.20·32 cut by the west edge
- m18_131072_87128.opus-l.json: [0, 930, 1024, 945] horizontal sheet join; 1-2 px offsets
- m18_131072_87131.opus-j.json: [960, 0, 1010, 5] bench-mark figures ('21·31'?) cut by the north edge; pheon at ~985,22 on Mark Street; whole on the mosaic to the north
- m18_131072_87131.opus-j.json: [1010, 380, 1024, 395] figure '25..' cut by the east edge (West Ham Lane / Aldworth Road)
- m18_131072_87131.opus-j.json: [1015, 705, 1024, 725] figure cut by the east edge
- m18_131072_87131.opus-j.json: [0, 790, 10, 806] figure '?·3' with dot at ~4,805 cut by the west edge
- m18_131072_87131.opus-j.json: [145, 1018, 170, 1024] figure (13·5?) cut by the south edge in Albion Street
- m18_131072_87131.opus-j.json: [0, 168, 1024, 176] horizontal sheet join at py ~172; B.M.20·19 pheon lies on it
- m18_131072_87143.opus-ao.json: [0, 656, 14, 672] figure reading 7·1 at west edge, a leading digit may be cut off (it is whole in the western neighbour)
- m18_131072_87143.opus-ao.json: [0, 564, 1024, 572] horizontal sheet join
- m18_131072_87146.opus-ag.json: [0, 52, 10, 68] figure ('..8', probably a B.M. value with its pheon at ~15,60 by the S.B.) cut by the west edge
- m18_131072_87146.opus-ai.json: [0, 52, 20, 70] figure '..8' and a pheon beside 'S.B.' cut by the west edge (B.M. text lies in the western neighbour)
- m18_131072_87149.opus-ab.json: [0, 760, 1024, 770] sheet join with tint step and 2-5 px line offsets; no figures cut
- m18_131072_87152.opus-x.json: [0, 0, 1024, 3] grey strip along N edge
- m18_131072_87155.opus-v.json: [0, 804, 6, 818] figure cut by the W edge (final 2 visible); lies in the mosaic to the west
- m18_131072_87158.opus-v.json: [0, 36, 6, 50] figure cut by the W edge (final digit 2 visible)
- m18_131072_87158.opus-v.json: [0, 594, 30, 606] B.M.9·18 (digits whole, B. and pheon beyond the W edge); read it in the mosaic to the west
- m18_131072_87158.opus-v.json: [1004, 630, 1024, 642] 16·5 cut by the E edge; whole in m18_131075_87158
- m18_131072_87158.opus-v.json: [650, 1008, 690, 1024] 34·5 within 4 px of the S edge, faint; check in the mosaic to the south
- m18_131072_87158.opus-x.json: [0, 35, 10, 55] figure '2' cut by W edge
- m18_131072_87158.opus-x.json: [0, 590, 30, 610] B.M.?9·18 cut by W edge, pheon off mosaic
- m18_131072_87158.opus-x.json: [1000, 630, 1024, 650] figure '16..' cut by E edge, dot at 1008,637
- m18_131072_87158.opus-x.json: [655, 1012, 680, 1024] 34·5 touches S edge
- m18_131072_87161.opus-w.json: [0, 744, 4, 760] leading digit of 16·0 against the west edge; value recorded as read
- m18_131072_87164.opus-z.json: [1005, 835, 1024, 870] B.M.10·98 text cut by the east edge (whole in 131075_87164)
- m18_131072_87164.opus-z.json: [1008, 318, 1024, 340] 15·2 ends 1 px from the east edge; recorded, confidence lowered
- m18_131072_87164.opus-z.json: [830, 388, 1024, 398] horizontal sheet join py~393 (east part)
- m18_131072_87167.opus-ad.json: [1005, 85, 1024, 100] B.M. text cut by the east edge (Orchard Place)
- m18_131072_87167.opus-ad.json: [995, 430, 1024, 462] B.M.18·1x text and pheon at the east edge by the Crane; final digit may be clipped
- m18_131075_87143.opus-ao.json: [338, 556, 352, 574] faint rotated lettering at the sheet-join corner, illegible at 8x
- m18_131075_87143.opus-ao.json: [348, 0, 356, 1024] vertical sheet join
- m18_131075_87143.opus-ao.json: [0, 566, 1024, 574] horizontal sheet join
- m18_131075_87146.opus-af.json: [1000, 680, 1024, 700] B.M. text cut by the east edge; whole in the eastern neighbour
- m18_131075_87146.opus-af.json: [1012, 766, 1024, 786] isolated dot at ~1021,776 whose figure lies beyond the east edge
- m18_131075_87146.opus-ah.json: [1000, 682, 1024, 696] B.M. figure (B.M.5..) cut by east edge beside the ditch
- m18_131075_87146.opus-ah.json: [1015, 770, 1024, 784] survey dot at 1022,777 whose figure lies beyond the east edge
- m18_131075_87146.opus-ah.json: [0, 876, 6, 892] figure fragment cut by west edge
- m18_131075_87149.opus-aa.json: [1016, 0, 1024, 16] isolated survey dot at 1022,9 whose figure lies beyond the east edge
- m18_131075_87152.opus-x.json: [625, 1012, 650, 1024] 'M' lettering cut by S edge
- m18_131075_87158.opus-v.json: [160, 0, 185, 4] bottom of a figure cut by the north edge; whole in the mosaic to the north
- m18_131075_87158.opus-v.json: [640, 0, 710, 10] 7·3 and B.M.9·25 text touch the north edge (B.M. tops clipped); whole in the mosaic to the north
- m18_131075_87161.opus-w.json: [0, 266, 18, 286] figure '·48' (probably a B.M. value) cut by the west edge
- m18_131075_87161.opus-w.json: [1006, 552, 1024, 572] 'B.M.' text at the east edge, value off the mosaic
- m18_131075_87161.opus-w.json: [336, 0, 346, 1024] vertical sheet join (tint step); no figures on it
- m18_131075_87164.opus-z.json: [340, 0, 350, 1024] vertical sheet join px~345
- m18_131075_87164.opus-z.json: [0, 388, 1024, 398] horizontal sheet join py~393
- m18_131078_87149.opus-ac.json: [0, 764, 1024, 772] sheet join at py ~768
- m18_131078_87149.opus-ac.json: [745, 1012, 775, 1024] B.M. on Hermit Road with value cut by the bottom edge
- m18_131078_87149.opus-ac.json: [425, 0, 452, 10] 5·0 within 1 px of the top edge; its dot may be off-sheet
- m18_131078_87149.opus-ae.json: [745, 1010, 780, 1024] B.M. figure on Hermit Road cut by the south edge (only B.M. and tops of digits visible)
- m18_131078_87149.opus-ae.json: [310, 1012, 350, 1024] B.M.6·59 text touches south edge; base of digits clipped 1-2 px
- m18_131078_87149.opus-ae.json: [0, 764, 1024, 772] horizontal sheet join (tint step) at py ~768
- m18_131078_87155.opus-w.json: [1005, 945, 1024, 966] spot height '5·?' with dot at ~1019,963 cut by east edge
- m18_131078_87155.opus-w.json: [790, 1008, 830, 1024] 'B.M.' text at bottom edge, value off the mosaic
- m18_131078_87155.opus-w.json: [0, 962, 1024, 968] horizontal sheet join (tint step); figures 7·6 at 336,958 and 7·3 at 540,965 sit against it
- m18_131078_87155.opus-w.json: [90, 0, 135, 4] pheon of B.M.8·64 probably above the top edge
- m18_131078_87158.opus-w.json: [1005, 180, 1024, 200] spot height '5·?' with dot ~1019,194 cut by east edge (final digit at x 1022-1024)
- m18_131078_87158.opus-w.json: [0, 194, 1024, 200] horizontal sheet join; 7·6 at 337,192 and 7·3 dot at 540,198 sit against it
- m18_131078_87158.opus-y.json: [1005, 180, 1024, 200] figure 5·? cut by east edge (whole in m18_131081_87158)
- m18_131078_87158.opus-y.json: [0, 194, 1024, 200] horizontal sheet join, tint step
- m18_131078_87164.opus-aa.json: [1008, 682, 1024, 702] B.M. text ('B' over '6..') cut by the east edge
- m18_131078_87164.opus-ac.json: [1014, 684, 1024, 704] B.M. figure 'B / 6..' cut by east edge
- m18_131078_87164.opus-ac.json: [0, 386, 720, 396] sheet join tint step at py ~391
- m18_131078_87167.opus-ae.json: [1000, 420, 1024, 440] B.M. at the east edge; its value is off the mosaic
- m18_131081_87131.opus-s.json: [1008, 528, 1024, 546] isolated dot at 1019,537 by east edge; its figure is beyond the mosaic edge
- m18_131081_87149.opus-ae.json: [0, 764, 1024, 772] horizontal sheet join at py ~768
- m18_131081_87149.opus-ae.json: [1016, 790, 1024, 810] 3·6 figure ends 4 px from the east edge; CHARGEABLE lettering cut
- m18_131081_87155.opus-ab.json: [20, 1010, 80, 1024] B.M. text cut by the bottom edge (value off-mosaic)
- m18_131081_87155.opus-ab.json: [0, 960, 1024, 970] sheet join with tint change; 5·8 dot lies on it
- m18_131081_87155.opus-z.json: [0, 960, 1024, 970] horizontal sheet join py~964-966 (tint step)
- m18_131081_87155.opus-z.json: [20, 1012, 70, 1024] B.M. text cut by south edge (B.M.6·84, whole in 87158)
- m18_131081_87158.opus-y.json: [0, 195, 1024, 201] horizontal sheet join, tint step
- m18_131081_87158.opus-z.json: [0, 192, 1024, 202] horizontal sheet join py~197 (tint step, 1-2 px offsets possible)
- m18_131081_87161.opus-z.json: [625, 0, 650, 6] figure (4·3, whole in 87158) cut by north edge; its dot at ~643,4
- m18_131081_87164.opus-ac.json: [1010, 805, 1024, 818] figure '5·?' cut by the east edge
- m18_131081_87164.opus-ac.json: [0, 384, 700, 392] sheet join tint step at py ~388
- m18_131081_87164.opus-ac.json: [330, 0, 350, 8] 4·6 at top edge; dot may be off-sheet
- m18_131081_87167.opus-ag.json: [1004, 34, 1024, 50] figure '5·..' cut by the east edge (its dot at ~1008,42)
- m18_131081_87170.opus-ao.json: [0, 524, 16, 538] 17·1 figure starts 2 px from west edge; its dot may lie beyond the edge
- m18_131081_87170.opus-ao.json: [0, 588, 1024, 594] horizontal sheet join
- m18_131084_87137.opus-s.json: [1004, 652, 1024, 670] figure 24·? cut by east edge
- m18_131084_87137.opus-s.json: [1004, 862, 1024, 885] bench mark B.M.31·?? cut by east edge (pheon ~1020,833)
- m18_131084_87137.opus-s.json: [0, 974, 14, 990] figure ?·4 cut by west edge
- m18_131084_87149.opus-ai.json: [985, 510, 1008, 530] figure 13·6 overlapped by rotated ABBEY STREET lettering and pavement dots; leading digit uncertain
- m18_131084_87155.opus-ad.json: [1012, 742, 1024, 762] figure beginning '8' with its dot at (1019,746) cut by the east edge
- m18_131084_87155.opus-af.json: [1012, 740, 1024, 760] figure (leading 8 with dot at ~1022,745) cut by east edge; belongs to the eastern neighbour
- m18_131084_87158.opus-ac.json: [0, 192, 1024, 202] sheet join at py ~197
- m18_131084_87158.opus-ac.json: [633, 0, 641, 1024] vertical sheet join at px ~637
- m18_131084_87158.opus-ac.json: [862, 1010, 885, 1024] 7·0 within 2 px of the bottom edge
- m18_131084_87161.opus-ae.json: [1006, 860, 1024, 882] spot height 5·x cut by the east edge
- m18_131084_87161.opus-ae.json: [630, 0, 638, 1024] vertical sheet join at px ~634
- m18_131084_87161.opus-ag.json: [1008, 860, 1024, 878] figure '5·..' cut by the east edge (between R·O lettering of ..CK'S ROAD); read it on the eastern neighbour
- m18_131084_87164.opus-ag.json: [1008, 94, 1024, 110] figure '5·..' cut by the east edge
- m18_131084_87164.opus-ag.json: [0, 388, 1024, 396] horizontal sheet join at py ~392
- m18_131084_87164.opus-ag.json: [630, 0, 638, 1024] vertical sheet join at px ~633-634, sheet content differs across it
- m18_131084_87167.opus-am.json: [0, 610, 8, 626] figure (ending in 5) cut by the west edge
