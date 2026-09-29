"""Generate a local Kokoro narration, aligned to the film's eight seven-second shots."""
import argparse
import json
from pathlib import Path
import subprocess
import textwrap

import numpy as np
import soundfile as sf
import torch

from test_local_voiceover import load_pipeline, cached, REPO, REVISION
from render_social_film import timestamp

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--voice', choices=['bm_george', 'bf_emma', 'bm_fable'], default='bm_george')
    parser.add_argument('--output', type=Path, default=ROOT / 'exports/voiceover/landscape-narration.wav')
    args = parser.parse_args()
    # Read the same chapter text and timings that drive the camera, without a browser.
    manifest = json.loads(subprocess.check_output([
        'node', '--input-type=module', '-e',
        "import {duration,chapters} from './docs/social-film.js'; console.log(JSON.stringify({duration,chapters}));"
    ], cwd=ROOT))
    pipeline = load_pipeline()
    voice = cached(f'voices/{args.voice}.pt')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    work = args.output.parent / args.voice
    work.mkdir(exist_ok=True)
    rate = 24000
    track = np.zeros(round(manifest['duration'] * rate), dtype=np.float32)
    cues, report = [], []
    for i, chapter in enumerate(manifest['chapters']):
        torch.cuda.reset_peak_memory_stats()
        results = list(pipeline(chapter['narration'], voice=voice, speed=.96))
        audio = np.concatenate([r.audio.cpu().numpy() for r in results])
        # Remove generated edge silence, keeping a small natural breath margin.
        active = np.flatnonzero(np.abs(audio) > .008)
        if not active.size:
            raise RuntimeError(f'Silent narration for chapter {i}')
        audio = audio[max(0, active[0] - 1200):min(len(audio), active[-1] + 2400)]
        raw = work / f'{i:02}-raw.wav'
        sf.write(raw, audio, rate, subtype='PCM_16')
        available = chapter['end'] - chapter['start'] - .65
        tempo = max(1., len(audio) / rate / available)
        if tempo > 1.25:
            raise RuntimeError(f'Chapter {i} is too long for natural delivery: {len(audio)/rate:.2f}s')
        fitted = work / f'{i:02}-timed.wav'
        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(raw),
                        '-af', f'atempo={tempo:.7f}', '-ar', str(rate), str(fitted)], check=True)
        audio, _ = sf.read(fitted, dtype='float32')
        start = chapter['start'] + .3
        offset = round(start * rate)
        if offset + len(audio) > round((chapter['end'] - .2) * rate):
            raise RuntimeError(f'Chapter {i} exceeds its narration slot')
        track[offset:offset + len(audio)] = audio
        end = start + len(audio) / rate
        cues.append(f'{i+1}\n{timestamp(start)} --> {timestamp(end)}\n'
                    + textwrap.fill(chapter['narration'], width=60) + '\n')
        item = {'chapter': i, 'text': chapter['narration'], 'start': start, 'end': end,
                'tempo': tempo, 'peak_cuda_MiB': torch.cuda.max_memory_allocated() / 1024**2}
        report.append(item)
        print(json.dumps(item), flush=True)
    raw_track = work / 'assembled.wav'
    sf.write(raw_track, track, rate, subtype='PCM_16')
    # Consistent speech level, with peak headroom for the final AAC encode.
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(raw_track),
                    '-af', 'loudnorm=I=-16:TP=-1.5:LRA=7', '-ar', '48000', str(args.output)], check=True)
    args.output.with_suffix('.srt').write_text('\n'.join(cues))
    args.output.with_suffix('.json').write_text(json.dumps({
        'model': REPO, 'revision': REVISION, 'voice': args.voice, 'duration': manifest['duration'],
        'chapters': report}, indent=2) + '\n')
    print(f'Narration ready: {args.output}', flush=True)


if __name__ == '__main__':
    main()
