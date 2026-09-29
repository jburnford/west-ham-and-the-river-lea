# Social film

A 56-second narrated landscape tour rendered from the actual scene, starting above the
Northern Outfall Sewer and drifting between the working river, Bromley gasworks,
Abbey Mills, Abbey Lane and West Ham Gas Works, northern streets, and Abbey Mill.
The revised camera stays 18–24 metres above the scene datum, close to rooftop
level, with 25–38° vertical fields of view. The first portrait export used
70–110 metre viewpoints and exposed too much of the unfinished outskirts.
The author requested landscape for YouTube, Bluesky and LinkedIn, a lower route,
and a voiceover, while retaining the original 56-second length.

The narration condenses the six existing website stories. The opening draws on the
sewer story; the closing credits Jim Clifford and links to the project. Each
chapter lasts seven seconds. Landscape frames show the chapter title; the spoken
story is also provided as an SRT sidecar. The persistent caption identifies this as a
reconstruction in progress, around 1900. No new historical evidence or model
geometry is introduced. Source notes for each caption are included in the
exported storyboard JSON. The initial silent portrait MP4 remains in `exports/`
for comparison; the revised deliverable is `channelsea-social-landscape.mp4`.

## Preview

Serve `docs/` as usual and open `/?film=1&quality=full`. Click the image or press
Space to pause/play; Home returns to the beginning. Reduced-motion users start
with a still. The normal website retains its existing camera and controls.
The preview uses the window dimensions at startup; reload after changing shape.

## Export

Python Playwright with Chromium, FFmpeg and ffprobe must already be installed.
The script starts and stops its own loopback server, serving only `docs/`.

```sh
# Inspect the eight landscape shots before a full render on the WSL laptop.
python3 scripts/render_social_film.py --stills --wsl-gpu

# Generate the 56-second narration with the local British male voice.
python3 scripts/narrate_social_film.py --voice bm_george

# Landscape, 1920 × 1080, 24 fps, H.264 MP4 with AAC narration.
python3 scripts/render_social_film.py --wsl-gpu --audio exports/voiceover/landscape-narration.wav

# Optional portrait layout of the revised route.
python3 scripts/render_social_film.py --wsl-gpu --width 1080 --height 1920 --output exports/channelsea-social-portrait-v2.mp4
```

Outputs live under `exports/`, outside the website and Git. Each export includes
eight JPEG storyboard images, the caption/camera manifest, encoder log and a
verification report. Rendering is offline: every frame is drawn at its exact
timestamp, so playback speed does not depend on the machine's WebGL speed.
Software rendering can take substantially longer than the running time.
Frames are cached using a fingerprint of the scene files and render settings;
rerunning an interrupted export resumes those frames. The default OpenGL backend
uses Mesa on this machine. Use `--angle swiftshader` if OpenGL is unavailable.
The first completed export uses `--wsl-gpu`: the RTX 500 Ada rendered 1,344
full-resolution frames in about 213 seconds, with no browser errors. Mesa
software rendering is much slower. The export is 56 seconds at 24 fps, H.264,
1080 × 1920, with 4:2:0 pixels. Three software workers were stopped once the
hardware route was verified; their partial frame caches remain resumable.

`docs/social-film.js` holds the editable captions and camera route. The normal
scene construction is reused through an optional query-gated import in `app.js`.
The exporter checks browser errors, dimensions, codec, pixel format, frame count
and duration before reporting success. Output uses `yuv420p` and fast-start MP4.
The revised landscape export passed full audio/video decoding and frame review:
1920 × 1080, 1,344 frames at 24 fps, exactly 56 seconds for both H.264 video and
AAC voice, approximately 50 MB. The author approved the George voice sample.

## Voiceover

The author wants no paid SaaS and describes the project as noncommercial.
`python3 scripts/test_local_voiceover.py` creates three short British Kokoro
auditions under `exports/voiceover/`, using existing local packages and CUDA.
It reuses cached weights and downloads missing voice files into that export
directory. `scripts/narrate_social_film.py` then generates the actual narration
from the chapter text in `docs/social-film.js`. It aligns each passage to its
seven-second shot, checks that it fits without cutting words, and normalizes
the assembled track to −16 LUFS with −1.5 dB true-peak headroom. It exports a
56-second WAV, actual cue timings in JSON, and synchronized SRT captions.
The default voice is Kokoro's British male George. The source and timed takes
are retained so the delivery can be reviewed or replaced independently of video.

The RTX 500 Ada test generated Emma, George and Fable samples, 13–16 seconds
each, in roughly 3–7 seconds, with peak PyTorch allocations of 799–856 MiB.
See `exports/voiceover/local-gpu-test.json` for measurements and phonemes.
The audition temporarily disables unrelated spaCy factory plugins within its
own process to avoid the installed transformer plugin's version conflict.

Fish Audio S2 Pro is the cluster candidate. The official inference guide
recommends at least 24 GB VRAM. Plato's `platogpu003` offers a 40 GB MIG slice,
requested with `--gres=gpu:3g.40gb:1`, in `plato_gpu_short`; the user's account
is `hpc_p_clifford`. The node was idle when checked, but no job was submitted.
S2 Pro has not been installed or benchmarked in this task.

Sources: [Kokoro](https://huggingface.co/hexgrad/Kokoro-82M),
[British voice list](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md),
[Fish S2 Pro](https://huggingface.co/fishaudio/s2-pro),
[Fish inference requirements](https://speech.fish.audio/inference/).
