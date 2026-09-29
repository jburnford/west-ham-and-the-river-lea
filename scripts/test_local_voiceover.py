"""Audition three British Kokoro voices on the local CUDA GPU, without a service.

Reuses installed packages and cached model weights. Missing files download to
exports/voiceover/models; samples and measured GPU use stay under exports/voiceover.
"""
import json
from pathlib import Path
import time

from huggingface_hub import hf_hub_download
import numpy as np
import soundfile as sf
import spacy
import torch
from kokoro import KModel, KPipeline

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'exports/voiceover'
REPO = 'hexgrad/Kokoro-82M'
REVISION = 'f3ff3571791e39611d31c381e3a41a3af07b4987'
TEXT = ('Around nineteen hundred, a walk above the Channelsea revealed an industrial world. '
        'Barges supplied the riverside works. Abbey Mills pumped London’s sewage. '
        'Beyond the houses stood the gas holders of West Ham and Bromley-by-Bow.')


def cached(filename):
    try:
        return hf_hub_download(REPO, filename, revision=REVISION, local_files_only=True)
    except FileNotFoundError:
        return hf_hub_download(REPO, filename, revision=REVISION, cache_dir=OUT / 'models')


def load_pipeline():
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA is unavailable in this process. Run with access to the local GPU.')
    torch.set_num_threads(2)
    model = KModel(repo_id=REPO, config=cached('config.json'), model=cached('kokoro-v1_0.pth')).to('cuda').eval()
    # This audition uses spaCy's small English pipeline. Do not auto-import
    # unrelated installed plugins (the system's transformer addon is incompatible
    # with its transformers version). No installed packages are changed.
    registry = spacy.util.registry._entry_point_factories
    previous_entry_points = registry.entry_points
    try:
        registry.entry_points = False
        pipeline = KPipeline(lang_code='b', repo_id=REPO, model=model)
    finally:
        registry.entry_points = previous_entry_points
    return pipeline


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    pipeline = load_pipeline()
    report = {'model': REPO, 'revision': REVISION, 'device': torch.cuda.get_device_name(0),
              'text': TEXT, 'samples': [], 'model_url': 'https://huggingface.co/hexgrad/Kokoro-82M'}
    print(f'Loaded Kokoro on {report["device"]}', flush=True)
    for voice in ['bf_emma', 'bm_george', 'bm_fable']:
        voice_path = cached(f'voices/{voice}.pt')
        torch.cuda.reset_peak_memory_stats()
        started = time.monotonic()
        segments = list(pipeline(TEXT, voice=voice_path, speed=.94))
        audio = np.concatenate([segment.audio.cpu().numpy() for segment in segments])
        torch.cuda.synchronize()
        path = OUT / f'kokoro-{voice}-sample.wav'
        sf.write(path, audio, 24000, subtype='PCM_16')
        sample = {'voice': voice, 'file': path.name, 'duration_seconds': len(audio) / 24000,
                  'generation_seconds': time.monotonic() - started,
                  'peak_cuda_allocated_MiB': torch.cuda.max_memory_allocated() / 1024**2,
                  'phonemes': [segment.phonemes for segment in segments]}
        report['samples'].append(sample)
        print(json.dumps({k: v for k, v in sample.items() if k != 'phonemes'}), flush=True)
    (OUT / 'local-gpu-test.json').write_text(json.dumps(report, indent=2) + '\n')
    (OUT / 'sample-script.txt').write_text(TEXT + '\n')


if __name__ == '__main__':
    main()
