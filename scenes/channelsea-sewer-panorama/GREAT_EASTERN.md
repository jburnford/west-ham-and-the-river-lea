# Great Eastern Railway: northern boundary

27 September connection update: the two-track Woolwich branch now continues north to the southeastern main-line track pair through its mapped curve. Both joins match in plan and height. See [WESTERN_COMPLETION.md](WESTERN_COMPLETION.md) for the source, provisional levels and checks.

Local view: **http://localhost:4175/?view=great-eastern**. The destination menu
also includes **Great Eastern Railway — northern boundary**.

The scene now includes a continuous 1.64 km main-line corridor from the Old Lea
crossing, behind the soap works and Marshgate district, towards the Channelsea
and Stratford approach. This is a separate route from the existing Woolwich
branch and southern railways. Four running tracks, timber sleepers, ballast,
grass banks, masonry retaining cuts and interpreted iron bridge decks establish
the northern edge of the reconstruction.

## Evidence and interpretation

The plan alignment was traced from the archived, georeferenced NLS OS London
five-foot tiles (1893 revision / 1894 publication). The authored points and
source-image coordinates are in
[`great-eastern-mainline.json`](../../data/maps/great-eastern-mainline.json).
The generated [overview overlay](../../reference/factory-building-survey/review/great-eastern-overview-overlay.png)
and [Stratford approach overlay](../../reference/factory-building-survey/review/great-eastern-east-overlay.png)
show the route in red and the interpreted embankment footprint in green.

The four continuous tracks are an initial simplification. The map has additional
sidings and junction tracks, particularly towards Stratford; this pass does not
claim to reconstruct their complete layout. Standard gauge is represented, but
track spacing, sleeper spacing, ballast width and construction details are
interpretive.

Formation height is provisionally 8.5 m in the scene's local vertical datum,
rising smoothly to 11.5 m around the Northern Outfall Sewer. These are model
levels, **not surveyed heights or Ordnance Datum values**. The sewer remains at
its existing 7.4 m model crest; the lowest bridge soffit across its corridor is
10.74 m, leaving approximately 3.34 m clearance in the model. Historical railway
gradients and bridge elevations need engineering drawings or other evidence.

Six gaps in the embankment keep mapped water, roads and the sewer corridor open.
The cuts and bridge forms are inferred from these clearances. They should not be
read as six individually identified historical bridge designs. The grass-bank
slopes and retaining-wall positions also need refinement against more detailed
railway evidence.

The original scene crop stopped short of the northern Channelsea crossing.
The necessary water polygons and their original boundary lines were restored
from the supplied Lower River Lea GIS and stored in the railway source JSON.
Only water outside the existing scene polygons is added. Bank geometry follows
the original channel edges, avoiding an artificial dam at the crop boundary.
These added banks are inferred; the water participates in the existing tidal
animation.

The Great Eastern Railway Society catalogue lists **RE014, GER Bow to Stratford
Widening 1893**, a notice of special arrangements. This is a research lead only:
the notice itself has not been read, and no track count or dimensions were
deduced from its title. See the
[GERS catalogue](https://mail.gersociety.org.uk/files-emporium-home/gers-downloadable-files?limit=50&order=DESC&page=12&sort=rating).

## Rebuild and review

```sh
python3 scripts/build_infrastructure.py
python3 scripts/build_scene_manifest.py
python3 scripts/check_great_eastern.py
node scripts/check_district_navigation.mjs
python3 scripts/review_great_eastern_map.py
python3 scripts/review_factory_buildings.py --url http://localhost:4175 --railway-only
```

The geometry checks cover continuous alignment, gradients, finite heights,
track containment and clearance from mapped roads, rivers, the sewer and
registered factory buildings. Browser review covers six positions: overview,
soap works bank, sewer crossing, City River vicinity, northern approach and
track level. Captures and the browser report are in `review/great-eastern-*`.

Follow-up work: resolve the circa-1900 track and junction layout; research each
bridge's form and level; refine abutments, bank toes and railway boundaries;
add supported signals, fencing and lineside structures. Stratford station and
works beyond the selected scene edge are not yet modelled.
