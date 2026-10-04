# Building a new scene in a git worktree

4 October 2026. For anyone (Astra, an agent, a collaborator) starting a new scene such as Silvertown in this repository without disturbing the live checkout at `/home/jic823/book_website`. Written after a day in which seventeen agent branches were built this way and merged.

## 1. Why a worktree

The main checkout is served live on port 4173 and must always load. Several people and agents edit it, and the generated data files are single-line JSON that cannot be merged by hand. A worktree gives you a full, isolated copy of the repository on your own branch, in your own folder, that the main checkout never sees until a reviewer merges it.

Rules that follow from this:

- Never write into `/home/jic823/book_website` itself from a worktree task. Read from it freely.
- Never `git stash` in a worktree; the stash is shared across all worktrees. Make a WIP commit instead.
- Stage explicit paths. Never `git add -A` or `git commit -a` in a shared-file area.

## 2. Set up

```sh
cd /home/jic823/book_website
git worktree add ../book_website-silvertown -b silvertown main
cd ../book_website-silvertown
```

Two things are git-ignored and therefore absent from a fresh worktree. Link them read-only from the main checkout; never commit them:

```sh
ln -s /home/jic823/book_website/node_modules node_modules
ln -s /home/jic823/book_website/reference reference    # NLS tiles, EPFL OS text, photo review, cached mosaics
```

Serve your worktree on a port nobody else uses. 4173 is main. Agents today used 4174 to 4194. Pick 4200 or above and check it is free:

```sh
ss -ltn | grep 4200 || python3 -m http.server 4200 --bind 127.0.0.1 --directory docs &
```

Record the baseline before changing anything:

```sh
npm test            # 16 of 18 pass on main as of 4 Oct 2026; check_flood_demo and check_drainage_connections fail on known stale hashes
npm run lint && npm run format:check
```

## 3. The project standard (applies to every record you add)

- **Realistic, not exact.** Evidence is recorded separately from interpretation. Every data record carries an `evidence` string (or `footprintEvidence`, `heightEvidence`, `roofEvidence`, `alignmentEvidence`) that says what is mapped or documented and what is estimated, and from which source. Height, storey, roof and function notes for buildings open with "Explicit estimate" unless a source gives them.
- **No photograph is ever used as a texture.** Photographs inform geometry and materials through written notes.
- **Do not invent sources.** Cite only files in the repository or the read-only `reference/` folder, by path. Type-based reasoning ("a works of this kind usually had...") is allowed if labelled as such.
- **Facts live in data, not JavaScript.** Positions, heights, names, exclusions and special cases go in registers under `data/maps/` and are built into `docs/data/`. JavaScript draws; it does not know site IDs. See `MODEL_PORTABILITY_PLAN.md`.
- **One coordinate frame.** Scene x east, z south, y up, metres from E538900 N183209 (EPSG:27700), recorded in `docs/data/ground-plan.json` `origin`. Keep this origin for Silvertown so the model stays one object; Silvertown is roughly x +1,500 to +2,500, z +2,500 to +3,200 in that frame. Before building, check how far the regional landscape (`docs/data/lower-lea-region/`), the river system (`river-system-1900.json`) and the OS tile cache (`reference/nls-tiles/`) actually reach; extend them with evidence before placing anything on ground that does not exist.
- **Prior values are kept.** When you move or re-register something, keep the old value in a `prior*` field with a note saying why it moved.

## 4. Where a new scene's files go

| What | Where | Notes |
|---|---|---|
| Brief and running notes | `scenes/silvertown/README.md`, `ASSUMPTIONS.md`, topic notes as needed | Follow `scenes/channelsea-sewer-panorama/` for the pattern; write the brief before geometry. |
| Source traces and registers | `data/maps/silvertown-*.json` (GeoJSON for traces, EPSG:27700; JSON registers for buildings, bridges, roads) | One register per topic. Look at `data/maps/bromley-gasworks-footprint-alignment.json` (buildings), `road-bridge-forms.json` (structures), `district-road-traces.json` (roads). |
| Builders | `scripts/build_silvertown_*.py` | Read registers, write `docs/data/silvertown-*.json` and binary grids. Builders must be deterministic: running twice gives identical bytes. Record `inputHashes` of every input as the existing builders do. |
| Built data | `docs/data/silvertown-*.json`, `.f32`, `.u32` | Generated only; never hand-edited. |
| Drawing modules | `docs/silvertown*.js`, `docs/silvertown.html` | A new page or mode. Do not edit `docs/app.js` beyond a few registration lines until the planned app.js split lands; say exactly which lines you added. Reuse `docs/lib/` helpers; do not add another random generator or triangle batcher. |
| Checks | `scripts/check_silvertown_*.mjs` (Node) and `.py` (Python) | `scripts/run_checks.mjs` runs every `scripts/check_*.mjs` automatically, so a new `.mjs` check is in `npm test` as soon as it exists. Assert geometry (nothing over water, nothing inside a footprint, heights within tolerance, register and module copies agree). |
| Manifest | `docs/data/scene-manifest.json` | Run `npm run manifest` after adding modules or data so the published site cache-busts them. |

## 5. Shared files: coordinate before touching

These are generated single-line JSON or binary files. Two branches editing one of them will conflict and the conflict cannot be resolved by hand; the only resolution is to regenerate from merged sources.

- `docs/data/infrastructure.json` and `housing-detail.json` (roads, bridges, railways, sewer banks, housing rows): rebuilt together to a fixed point with `python3 scripts/build_infrastructure.py` and `(cd scripts && python3 build_housing_detail.py)`, repeated until neither changes.
- `docs/data/ground-plan.json` (core plan, sewer): a full rebuild of `build_panorama_data.py` also re-splits terrace rows; today's convention is to patch only the arrays you own, with a structural diff proving nothing else changed.
- `docs/data/main-landscape-1900.*` (the ground): `build_main_landscape.py`, about four minutes. Hashes many inputs; see section 6.
- `docs/data/river-network.*`, `river-system-1900.json`, `factory-buildings.json`, `factory-yards.json`, `high-street-frontages.json`, `terrain-1900.json`, the flood files.

If Silvertown needs to change one of these, say so in your brief and keep that change in its own commit so the reviewer can regenerate it on main after the merge.

## 6. The hash cascade

Derived files store `inputHashes` of what they were built from. Changing an input makes the dependent checks fail until the dependents are rebuilt, in this order:

1. `build_river_network.py` (if the core rivers changed)
2. `build_river_system.py` (reads `ground-plan.json`, `factory-buildings.json`, the network)
3. `build_main_landscape.py` (reads infrastructure, ground plan, river system, factory buildings, housing, frontages, station plan)
4. `build_historic_elevation.py`, the flood builders, `build_factory_yards.py`, `build_drainage_connections.py`, `build_scene_manifest.py`, `export_geopackage.py --verify`
5. Refresh stored samples in checks that keep them (`check_road_bridges.mjs --write-sample`, the infrastructure hash in `check_drainage_connections.mjs`)

Do not run the whole cascade in your branch unless your task is the cascade. Rebuild what your change requires, list what you left stale, and let the reviewer run the rest on main.

## 7. Verify before you ask for a merge

- `npm test` at least as good as your baseline, with every changed assertion explained in your report. `npm run lint` and `npm run format:check` clean on changed JS.
- Builders deterministic: run twice, compare bytes.
- Structural diff of every generated file you touched: which keys changed and why. A short Python script that loads old and new JSON and lists differing paths is enough.
- Smoke snapshot: `python3 scripts/review_smoke.py <label> --compare main-after-t13 --url=http://127.0.0.1:4200`. The stock script's two 60 s waits time out on a loaded machine; copy it to scratch and raise both to 900 s. Snapshots live in the git-ignored `scenes/channelsea-sewer-panorama/review/`; copy `smoke-main-after-t13.json` from the main checkout if your worktree lacks it. Zero page errors; every diagnostic difference explained.
- Renders: write a camera list (`[{label, position:[x,y,z], target:[x,y,z], fov}]`) and run `python3 scripts/render_views.py cams.json --out=<dir> --url=http://127.0.0.1:4200`. Render the same cameras against main on 4173 for a before set. Look at every image; do not describe a render you have not opened. The scene takes about five minutes to load and about 40 s a view.
- OS overlays where you placed anything from the map: crop the mosaic with `scripts/factory_map_sources.py` `mosaic(bounds, layer='os-london-five-foot-1893')` and draw old positions in red and new in blue.

## 8. Write the report

`scenes/silvertown/REPORT-<date>.md` or `<TASK>_REPORT.md` at the repository root, committed on your branch, with these sections in this order: what changed and why; numbers before and after; structural diffs; checks with pass counts and every changed assertion; render verdict per camera; smoke differences; what you did not do; what you were unsure of; decisions for the reviewer, each with your choice and the alternative. Say plainly anything you could not verify. The reports from 3 October (`T1_REPORT.md` to `T17_REPORT.md`) are the models; `T13_REPORT.md` and `T6_REPORT.md` are the fullest.

## 9. Commit and hand over

- Commit on your branch with a message that says what changed in the scene, not which files. End with your attribution line (Astra: use your own name and model).
- Before handing over, `git merge main` into your branch and resolve conflicts in source files; if a generated file conflicts, take either side and regenerate it, then run the checks again.
- Tell the reviewer: branch name, worktree path, the report path, the exact regeneration commands if any generated shared file must be rebuilt on main, and which servers you left running.
- The reviewer merges with `git merge --no-ff`, runs any regeneration on main, reruns `npm test` and the smoke, records the outcome, and removes the worktree with `git worktree remove`. Do not remove your own worktree until the merge is confirmed.

## 10. Silvertown: suggested first steps

1. Brief in `scenes/silvertown/README.md`: period (match c1900 unless the book argues otherwise), extent in the shared frame, what the scene is for, and which book chapters it draws on.
2. Evidence register before geometry: which OS sheets cover it (five-foot and 25-inch), what the EPFL footprint layer holds there, which photographs in the catalogue are in scope, what the book says. Note gaps explicitly.
3. Check coverage: regional landscape, river system (the Thames and the docks are not modelled yet), OS tile cache. Extending the ground and water is its own task with its own evidence; do it first, in its own commit.
4. Then sites, one register each, built and checked as in sections 4 and 7, each in a commit that can be reviewed alone.
