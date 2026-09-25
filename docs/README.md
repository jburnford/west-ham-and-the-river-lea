# docs — published front end

The redesigned front end for the Channelsea panorama, published by GitHub Pages. The 3D scene, materials, terrain, infrastructure and bridge-movement modules are unchanged from the previous front end, which is preserved in `docs0/`; only the page, styling and interaction layer are new.

## What changed

- The scene fills the first viewport. Title and controls sit over it; page content begins on scroll.
- Six chapters plus a free-exploration step scroll over the pinned scene. Entering a chapter eases the camera to its view instead of cutting.
- A static poster frame (`poster.jpg`) shows immediately, with a progress bar tied to the data downloads, then the live renderer fades in and eases from the poster pose to the opening view.
- A persistent minimap inset (desktop) opens the full location plan. The source notes are an inline section rather than a dialog.
- Self-hosted type: Libre Caslon Text (display and reading) and Archivo (interface labels). Both are under the SIL Open Font Licence; see `fonts/OFL-*.txt`.
- Keyboard walking, WASD, drag-to-look, native dialog, WebGL fallback and the `window.panoramaReview` diagnostic all carry over. When WebGL fails the poster remains as a still.

## Quality tiers

Phones and small tablets (coarse pointer and a short screen side under 900 px, or a reported device memory of 4 GB or less) get a lighter build: terrain sampled at half resolution, about a third of the scattered clods and grass, a 1024 px shadow map, a 256 × 192 reflection, no multisampling and a device pixel ratio of 1. Backdrop blur is also dropped on touch devices. Everything else, including every mapped building, is unchanged. Force a tier with `?quality=lite` or `?quality=full`.

In both tiers the static geometry is batched through preallocated typed arrays and the CPU copies are released after upload, which roughly halves the memory held by the page compared with the previous front end.

## Run locally

From the repository root:

```sh
python3 -m http.server 4173 --bind 127.0.0.1 --directory docs
```

Open http://localhost:4173/. The previous front end can be served the same way from `docs0/`.

`docs/data`, `docs/vendor` and `docs/assets` are real copies, as GitHub Pages requires; the generators under `scripts/` continue to write into `docs/data/`. `docs0/` carries its own identical copies.

## Regenerating the poster

`poster.jpg` is a 1920 × 1080 render of the scene at the arrival pose (yaw 194°, pitch −3°, field of view 71°), which is where `app.js` starts before easing to the opening view. Re-render it whenever the scene changes materially.
