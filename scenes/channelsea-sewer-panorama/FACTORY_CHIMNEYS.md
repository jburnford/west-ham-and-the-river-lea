# Factory chimney survey — 27 September 2026

The initial Goad pass recorded **54 traced chimney symbols across 19 site
groups**, replacing seven earlier entries. Nineteen have adjacent height figures
read in feet and converted to metres. The remaining heights are explicitly
estimated. These counts exclude Abbey Mills' existing photograph-based towers
and the separate distant context chimneys.

The subsequent [gasworks photograph comparison](GASWORKS_PHOTO_REVIEW.md) adds
one Bromley boiler stack and 24 interpreted retort-house flues, taking the
runtime total to **79** across 20 site groups. These interpret the aerial
skyline; their heights, repeated spacing and continuity into c1900 are modelling
choices, not Goad symbol readings.

The author's [lower symbol key](https://forum.casebook.org/filedata/fetch?id=662696&d=1627645051)
identifies square and round factory chimney symbols separately from boilers,
hydrants and hoists. Its copyright date is **1926**: it supports interpretation
of matching symbols, not the date of the factories. The
[upper key](https://forum.casebook.org/filedata/fetch?id=662695&d=1627645051)
also explains storeys, basements, roof materials and abbreviations. Both images
are archived under `reference/factory-building-survey/goad-symbol-key-1926*`.

All implemented positions were read on the original **July 1893 F2, F3, F4 and
F17 sheets** already listed in the factory source register. Each chimney keeps
its original pixel centre, source registration, height reading or estimate,
and a separate explanation of the interpreted shaft profile. An adjacent
engine's horsepower is not a chimney height. The original seven records remain
in `supersededStructures` for comparison.

| Site group | Mapped chimneys |
| --- | ---: |
| Howards and Sons, including southern process departments | 18 |
| Edward Cook soapworks | 4 |
| Imperial Sawmills | 1 |
| Ritchie jute mill | 1 |
| Slater & Palmer | 3 |
| Jeffrey marine glue | 2 |
| Marshgate Lane chemical works | 1 |
| Augustus Smith brush/fibre works | 2 |
| Crown Works / Johnson | 1 |
| West Sugar House Lane works | 4 |
| East Sugar House Lane works | 3 |
| Confectionery works | 1 |
| Bow Bridge bone works | 4 |
| Hunt soapworks | 2 |
| Usher printing ink | 1 |
| Oil refinery / printing ranges | 2 |
| French Asphalte | 2 |
| British Ultramarine | 1 |
| Three Mills distillery | 1 |

Notable readings include **120 feet** beside Cook's boiler/economiser chimney
and **200 feet** beside Ritchie's circular flue symbol. Howards has two explicitly
labelled iron chimneys. Diameter, taper, brick colour, crown detail, and the
continuation of a mapped base section up the shaft remain interpretations.
The small common ground offset is a model datum, not a surveyed foundation level.

The shafts now have tapered sides, base plinths, projecting rims and recessed
open throats. Yard stock and wear routes avoid their bases. Geometry checks
verify that shafts stand above intersecting roofs and do not obstruct streets,
water, holders or each other. Browser checks compare the rendered chimney IDs
with the register and capture the factory skyline and a close crown view.

This is a cross-site chimney pass, not a claim that every factory review is
complete. Gasworks and the remaining OS-only sites need further chimney evidence.
The white-lead symbol near F3 pixel (1090,1953) is retained here as a follow-up:
its factory grouping and surrounding missing ranges need resolving before it
is assigned to an existing site. Boiler flues at additional small tenants should
continue to be checked during each factory review. The survey register records
these distinctions; a site with no traced stack is not an assertion of absence.

```sh
python3 scripts/build_factory_buildings.py
python3 scripts/build_factory_yards.py
python3 scripts/build_scene_manifest.py
python3 scripts/review_factory_chimney_maps.py
python3 scripts/check_factory_buildings.py
python3 scripts/check_factory_yards.py
python3 scripts/review_factory_buildings.py --url http://localhost:4175 --chimneys-only
```

The reproducible symbol cards are in
`reference/factory-building-survey/review/chimneys/symbols-1.jpg` through
`symbols-5.jpg`. Marginal red ticks locate the traced point without obscuring
the symbol itself.

Local views: [Howards](http://localhost:4175/?view=factory-260),
[soapworks](http://localhost:4175/?view=factory-796),
[jute mill](http://localhost:4175/?view=ritchie-jute).
