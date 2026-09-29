# River network expansion — 25 September 2026

## Tidal correction and refinement, 26 September

The subsequent [marsh/ditch pass](MARSH_DITCHES.md) supersedes the mesh counts
and generic low-bank section below: 594,581 vertices and 1,170,034 triangles,
including the lower marsh and map-traced ditches. General tidal crests are now
raised above that marsh, with provisional retaining edges at working plots.

The author specifies tidal channels throughout the scene except the Old Lea
from the Limehouse Cut lock northward. The current generator distinguishes
that retained reach (GIS ids 18, 22, 10018, 10022) from the tidal channels,
including Bow Creek (id 0). It adds exposed sediment margins using the existing
Channelsea water datum of 0.06 scene metres and the same sediment texture. This
is a visual common tide state, not surveyed bathymetry or a tidal simulation.
Inferred mud shelves taper toward grass; roads and industry footprints limit
their landward extent. The detailed Channelsea terrain remains unchanged.

`river-network.silt` supplies a separate per-vertex sediment blend; the original
GIS water polygons are retained. The new relief contains 468,737 vertices and
919,216 triangles. `check_river_tides.py` verifies exposed mud on the principal
tidal channels and excludes it from the retained reach away from confluences.
The [refinement record](REFINEMENT.md) also covers path continuity, facade detail,
district contact shading, review cameras and outstanding work.

## Earlier expansion record

The first expansion gives the 15 existing GIS water features submerged beds and
bank relief outside the detailed Channelsea terrain. It retains the supplied
channel outlines and removes the flat ground beneath them. The indexed mesh
contains 370,141 vertices and 723,578 triangles at a 1 m grid spacing; the narrow
corridor avoids a district-wide dense terrain mesh. The original detailed core
is retained, with matching boundary levels and a small outer ground offset to
prevent coplanar flicker. Industrial parcels and road corridors suppress bank
height where needed to retain their existing ground level.

Three Mills Wall River is the branch west of Mill Mead, as corrected by the
author. The c1900 photograph looking south from High Street informs its grassy
raised east bank. All section heights, widths and bed depths are estimates.
Generic bank sections elsewhere are an initial terrain scaffold. They do not
represent a surveyed embankment or retaining-wall inventory.

## Source chronology and next detailed areas

The author-defined extent is the Great Eastern Main Line in the north,
Bromley-by-Bow gasworks in the south, Channelsea in the east and Old Lea in
the west. Three Mills is included. See [research scope and evidence](RESEARCH_SCOPE.md)
for the recovered planning reports and feature-by-feature chronology.

- Five fire-insurance screenshots are archived unchanged under
  `reference/author-river-plans-2026-09-25/`, with hashes and the author's
  provisional **1885–1890** dating. They comprise three overlapping areas with
  two near-duplicate pairs. Sheet dates and registration remain unverified.
- The separate `marsh housing.png` is an OS screenshot with an unverified date.
  Do not transfer the fire-insurance date estimate to it. The author prioritises
  this housing between the Channelsea and Three Mills rivers. Existing rows
  os-row-1 through os-row-18 already represent Roberts, Beck, Lucas, Godfrey,
  Marsh, Ross, Allwyn, Abbey Lane, Livingstone and Stanley streets. This pass
  adds a coverage review view, without duplicating those rows. Rear extensions,
  courtyards and a complete comparison with the new screenshot remain to trace.
- Two City Mills / Howards images are archived under
  `reference/city-mills-howards/`. The Foxlinks photograph is probably from the
  north looking south according to the author. Its parent page captions it
  about 1914 near the old flood-gate; that secondary date and camera remain
  unverified against the original photographic record.
  The other is captioned **City Mills, from High Road** and is recorded as from
  the company's circa 1897 pamphlet. The author identifies it as the southern
  view. It shows masonry river edges and an arched opening, which are not yet
  individually modelled. Register the fire-insurance plan before placing these
  features or attempting an exact photographic match. Existing GIS site 260 is
  a parcel envelope, not the factory's individual building footprints.
- Britain from Above EAW014561 is catalogued as **Towler and Son Ltd Riverbank
  Works on the Three Mills Wall River**, **16 April 1948**. It is archived under
  `reference/three-mills-aerial-1948/`, with its catalogue page. It should not be
  identified as Howards merely because it was supplied beside those images.
  **The author dates the later embankments to the 1930s.** This aerial has not
  supplied geometry to the c1900 scene. Do not backdate its engineered walls,
  channel alterations or industrial ranges. Prescott Cut remains excluded.

Reference photographs stay outside the public web root and are not textures.
Source and date records are separate from inferred geometry. The earlier
photographs' masonry and grassy banks do not establish continuity of the later
engineered river works.

The later Sugar House photograph supplied during review led to ASE historic
building record 2013200 (September 2013), archived in
`reference/sugar-house-building-sequence/`. The west face matches its Plate 49.
The report dates the tall warehouse (Building 16) to 1882; adjoining warehouses
15, 17 and 17a fall between the 1894 and 1916 maps, grouped as circa 1900. The
low white gable traces appear to relate to west-side Building 15. Its precise
construction year remains unresolved; the provisional fire-insurance sheet
dating must be checked before narrowing this bracket. No new Sugar House
geometry has been introduced in this river pass.

## Rebuild and review

```sh
python3 scripts/build_river_network.py
python3 scripts/review_river_network.py
```

The generator uses the existing ground plan, detailed terrain metadata and
infrastructure. Regenerate this layer after changing those inputs. Runtime
loading/rendering is in `docs/river-network.js`; generated positions, colours,
indices and metadata are under `docs/data/river-network.*`.

The review script serves only `docs/` on a temporary loopback port and uses the
local WSL NVIDIA browser configuration. It captures the full river network,
two Wall River views, Three Mills junction, the original Channelsea view, marsh
housing coverage and existing City Mills coverage. Results live in the ignored
`review/` folder. The City Mills coverage image documents unfinished massing;
it is not a reconstruction matched to the newly supplied photographs.

All seven views passed browser/shader checks after resumption, as did
the existing geographic, bridge-movement and JavaScript syntax checks. The
expanded seven-view report records the final desktop review. No new phone
performance audit or deployment is part of this pass.

## Subsequent factory coverage, 26 September 2026

The [factory pass](FACTORY_BUILDINGS.md) supersedes the earlier research-only
status above. It adds the building ranges and all nine Bromley holder positions.
Four original GIS river continuations now extend the western clip to the Old Lea
beside the complete soap and saw mills. The rebuilt relief has 411,593 vertices
and 804,496 triangles across 19 source features. `factory-west-context.json` is
an additional rebuild input. The original c1900 chronology exclusions remain.
