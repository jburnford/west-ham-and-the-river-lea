"""Render the existing WebGL scene to a captioned MP4, one deterministic frame at a time.

Requires Python Playwright/Chromium and ffmpeg. Serves only docs/ on loopback.
Use --stills for the storyboard; default output is a 56-second, 1920x1080 MP4.
"""
import argparse
import asyncio
import base64
import hashlib
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import subprocess
from threading import Thread
import time

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


def timestamp(seconds):
    milliseconds = round(seconds * 1000)
    return f'{milliseconds // 3600000:02}:{milliseconds // 60000 % 60:02}:{milliseconds // 1000 % 60:02},{milliseconds % 1000:03}'


async def render(args, url):
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    review = output.parent / (output.stem + '-review')
    review.mkdir(exist_ok=True)
    errors = []
    async with async_playwright() as p:
        graphics_env = dict(os.environ)
        if args.wsl_gpu:
            graphics_env.update(GALLIUM_DRIVER='d3d12', MESA_D3D12_DEFAULT_ADAPTER_NAME='NVIDIA')
        browser = await p.chromium.launch(headless=True, args=[
            '--no-sandbox', '--enable-webgl', f'--use-angle={args.angle}',
            '--ignore-gpu-blocklist',
            '--enable-unsafe-swiftshader', '--disable-dev-shm-usage'], env=graphics_env)
        page = await browser.new_page(viewport={'width': args.width, 'height': args.height}, device_scale_factor=1)
        page.set_default_timeout(180000)
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
        await page.goto(url + '/?film=1&capture=1&quality=full', wait_until='load')
        await page.wait_for_function('Boolean(window.socialFilm)')
        graphics = await page.evaluate('''() => {
            const gl = document.querySelector('#panorama canvas').getContext('webgl2');
            const ext = gl.getExtension('WEBGL_debug_renderer_info');
            return ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : 'unknown';
        }''')
        print(f'Graphics: {graphics}', flush=True)
        manifest = await page.evaluate('({duration: socialFilm.duration, chapters: socialFilm.chapters})')
        manifest.update(width=args.width, height=args.height, fps=args.fps,
                        audio=str(args.audio.resolve()) if args.audio else False, graphics=graphics)
        (review / 'storyboard.json').write_text(json.dumps(manifest, indent=2) + '\n')
        subtitles = []
        for i, chapter in enumerate([] if args.frames_only else manifest['chapters']):
            started_shot = time.monotonic()
            t = chapter['start'] + 4
            data = await page.evaluate('(t) => socialFilm.frame(t)', t)
            (review / f'{i:02}-{chapter["start"]:02}s.jpg').write_bytes(base64.b64decode(data.split(',')[1]))
            subtitles.append(f'{i + 1}\n{timestamp(chapter["start"])} --> {timestamp(chapter["end"])}\n'
                             f'{chapter["title"].replace(chr(10), " ")}\n{chapter["text"]}\n')
            print(f'Storyboard {i + 1}/8 captured in {time.monotonic() - started_shot:.1f}s', flush=True)
        if args.audio and not args.frames_only:
            subtitles_path = args.audio.with_suffix('.srt')
            if subtitles_path.exists():
                shutil.copyfile(subtitles_path, output.with_suffix('.srt'))
        elif not args.frames_only:
            output.with_suffix('.srt').write_text('\n'.join(subtitles))
        if errors:
            raise RuntimeError('\n'.join(errors))
        if not args.stills:
            frames = round(manifest['duration'] * args.fps)
            fingerprint = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode())
            for path in sorted((ROOT / 'docs').rglob('*')):
                if path.is_file():
                    fingerprint.update(str(path.relative_to(ROOT / 'docs')).encode())
                    fingerprint.update(path.read_bytes())
            frame_dir = review / ('frames-' + fingerprint.hexdigest()[:16])
            frame_dir.mkdir(exist_ok=True)
            async def cached_frame(frame):
                frame_path = frame_dir / f'{frame:05}.jpg'
                if frame_path.exists():
                    return frame_path.read_bytes()
                data = await page.evaluate('(t) => socialFilm.frame(t)', frame / args.fps)
                jpeg = base64.b64decode(data.split(',')[1])
                pending = frame_path.with_suffix(f'.tmp-{os.getpid()}')
                pending.write_bytes(jpeg)
                pending.replace(frame_path)
                return jpeg
            if args.frames_only:
                for frame in range(args.start_frame, min(frames, args.end_frame or frames)):
                    await cached_frame(frame)
                    if frame % args.fps == 0:
                        print(f'Cached frame {frame}/{frames}', flush=True)
                await browser.close()
                return
            started = time.monotonic()
            # The pipe provides backpressure. Offline rendering preserves every frame,
            # even when software WebGL cannot draw at real-time playback speed.
            temporary = output.with_name(output.stem + '.partial.mp4')
            with (review / 'ffmpeg.log').open('w') as log:
                audio_options = (['-i', str(args.audio.resolve()), '-map', '0:v:0', '-map', '1:a:0',
                                  '-c:a', 'aac', '-b:a', '192k', '-t', str(manifest['duration'])]
                                 if args.audio else ['-an'])
                encoder = subprocess.Popen([
                    'ffmpeg', '-hide_banner', '-loglevel', 'warning', '-y',
                    '-f', 'image2pipe', '-vcodec', 'mjpeg', '-framerate', str(args.fps), '-i', '-',
                    *audio_options, '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
                    '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(temporary)
                ], stdin=subprocess.PIPE, stderr=log)
                try:
                    for frame in range(frames):
                        encoder.stdin.write(await cached_frame(frame))
                        if frame % args.fps == 0:
                            print(f'{frame // args.fps:02}/{manifest["duration"]} seconds rendered '
                                  f'({time.monotonic() - started:.0f}s elapsed)', flush=True)
                        if errors:
                            raise RuntimeError('\n'.join(errors))
                    encoder.stdin.close()
                    if encoder.wait() != 0:
                        raise RuntimeError(f'ffmpeg failed: {review / "ffmpeg.log"}')
                    temporary.replace(output)
                finally:
                    if encoder.poll() is None:
                        encoder.terminate()
                        encoder.wait()
            probe = json.loads(subprocess.check_output([
                'ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(output)]))
            video = probe['streams'][0]
            assert int(video['nb_frames']) == frames, video
            assert (video['width'], video['height']) == (args.width, args.height), video
            assert video['codec_name'] == 'h264' and video['pix_fmt'] == 'yuv420p', video
            assert abs(float(probe['format']['duration']) - manifest['duration']) < .1, probe
            if args.audio:
                audio_stream = next(s for s in probe['streams'] if s['codec_type'] == 'audio')
                assert audio_stream['codec_name'] == 'aac', audio_stream
                assert abs(float(audio_stream['duration']) - manifest['duration']) < .1, audio_stream
            (review / 'verification.json').write_text(json.dumps({'probe': probe, 'browser_errors': errors}, indent=2) + '\n')
            print(f'Verified {output}', flush=True)
        await browser.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'exports/channelsea-social-landscape.mp4')
    parser.add_argument('--width', type=int, default=1920)
    parser.add_argument('--height', type=int, default=1080)
    parser.add_argument('--audio', type=Path, help='Narration WAV aligned to the 56-second film; its SRT is copied alongside.')
    parser.add_argument('--fps', type=int, default=24)
    parser.add_argument('--stills', action='store_true')
    parser.add_argument('--angle', choices=['swiftshader', 'gl', 'default'], default='gl')
    parser.add_argument('--wsl-gpu', action='store_true', help='Try Mesa D3D12 on the local NVIDIA GPU under WSL.')
    parser.add_argument('--frames-only', action='store_true', help='Cache a range for another encoder process.')
    parser.add_argument('--start-frame', type=int, default=0)
    parser.add_argument('--end-frame', type=int)
    args = parser.parse_args()
    if args.audio and not args.audio.is_file():
        parser.error('Narration audio file does not exist.')
    if args.width < 320 or args.height < 320 or args.width % 2 or args.height % 2 or not 1 <= args.fps <= 60:
        parser.error('Use even dimensions of at least 320 pixels and fps between 1 and 60.')
    if args.start_frame < 0 or (args.end_frame is not None and args.end_frame <= args.start_frame):
        parser.error('Frame range must be non-negative and have an end after its start.')
    if args.frames_only and args.stills:
        parser.error('--frames-only and --stills are mutually exclusive.')
    if not args.stills and (not shutil.which('ffmpeg') or not shutil.which('ffprobe')):
        parser.error('ffmpeg and ffprobe must be installed.')
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(ROOT / 'docs')))
    Thread(target=server.serve_forever, daemon=True).start()
    try:
        asyncio.run(render(args, f'http://127.0.0.1:{server.server_port}'))
    finally:
        server.shutdown()
        server.server_close()


if __name__ == '__main__':
    main()
