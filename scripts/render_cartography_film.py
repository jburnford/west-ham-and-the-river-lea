"""Draft render of the map-led film in scenes/cartography-film/film.json.

Three cached stages, each skipped when its outputs already exist:
  1. narration: one Kokoro clip per narration unit (local GPU, British voice);
  2. capture:   3840x2160 stills of the maps page with all controls hidden;
  3. render:    eased pans and zooms, dissolves, wipes and captions drawn in Python,
                piped to ffmpeg as H.264 with the narration track and an SRT sidecar.

Usage:  python3 scripts/render_cartography_film.py [--only s3-dock] [--fresh-audio] [--fresh-stills]
Output: exports/cartography-film/cartography-film-draft.mp4 (exports/ is outside Git).
"""
import argparse, asyncio, hashlib, json, re, subprocess, sys, textwrap, threading, time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / 'scenes/cartography-film/film.json'
OUT = ROOT / 'exports/cartography-film'
W, H, FPS = 1920, 1080, 24
CW, CH = 3840, 2160          # capture size: k=2 is the view at native detail
RATE = 24000
XFADE = 0.7                   # dissolve between shots, seconds
GAP = 0.45                    # pause between narration units within a shot
BG = (230, 226, 213)          # maps page background
INK = (15, 23, 22)
PARCHMENT = (241, 234, 216)
GOLD = (214, 165, 77)
GAMMA = {'six-inch-2nd': 1.12}

# ---------------------------------------------------------------- narration
ONES = 'zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen'.split()
TENS = 'zero ten twenty thirty forty fifty sixty seventy eighty ninety'.split()

def two(n):
    if n < 20: return ONES[n]
    return TENS[n // 10] + ('' if n % 10 == 0 else '-' + ONES[n % 10])

def year_words(y):
    hi, lo = divmod(y, 100)
    if lo == 0: return two(hi) + ' hundred'
    if lo < 10: return two(hi) + ' oh-' + ONES[lo]
    return two(hi) + ' ' + two(lo)

def decade_words(y):  # 1930 -> nineteen-thirties
    hi, lo = divmod(y, 100)
    t = TENS[lo // 10]
    return two(hi) + '-' + (t[:-1] + 'ies' if t.endswith('y') else t + 's')

def spoken(text, say):
    text = re.sub(r'\b(1[6-9]\d0)s\b', lambda m: decade_words(int(m.group(1))), text)
    text = re.sub(r'\b(1[6-9]\d\d)\b', lambda m: year_words(int(m.group(1))), text)
    for written, sound in say.items():
        text = re.sub(rf'\b{re.escape(written)}\b', sound, text)
    return text

def narrate(spec, units, fresh):
    import soundfile as sf
    sys.path.insert(0, str(ROOT / 'scripts'))
    todo = [u for u in units if fresh or not u['wav'].exists()]
    if todo:
        import torch
        from test_local_voiceover import load_pipeline, cached
        pipeline = load_pipeline()
        voice = cached(f"voices/{spec['voice']}.pt")
        for u in todo:
            audio = np.concatenate([r.audio.cpu().numpy() for r in pipeline(u['say'], voice=voice, speed=spec['speed'])])
            active = np.flatnonzero(np.abs(audio) > .008)
            audio = audio[max(0, active[0] - 1200):min(len(audio), active[-1] + 2400)]
            u['wav'].parent.mkdir(parents=True, exist_ok=True)
            sf.write(u['wav'], audio, RATE, subtype='PCM_16')
            print(f"  voice {u['wav'].name}: {len(audio)/RATE:.1f}s  {u['say'][:60]}", flush=True)
        del pipeline; torch.cuda.empty_cache()
    for u in units:
        u['dur'] = sf.info(u['wav']).duration

# ---------------------------------------------------------------- capture
HIDE_CSS = """
.site,.panel,.timeline,.divider,.leaflet-control-container,.leaflet-bounds-pane,.no-script{display:none!important}
html,body{margin:0!important;overflow:hidden!important}
#map{position:fixed!important;inset:0!important;width:100vw!important;height:100vh!important}
.leaflet-tile{transition:none!important}
"""

def still_path(view, layer, size):
    key = hashlib.sha1(f'{view}|{layer}|{size}'.encode()).hexdigest()[:12]
    return OUT / 'stills' / f"{layer}-{view.replace('/', '_')}-{size[0]}x{size[1]}-{key}.png"

class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *a): pass

async def capture(jobs):
    from playwright.async_api import async_playwright
    srv = ThreadingHTTPServer(('127.0.0.1', 0), partial(Quiet, directory=str(ROOT / 'docs')))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    port = srv.server_address[1]
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(args=['--disable-3d-apis'])
            for (view, layer, size), path in jobs.items():
                page = await browser.new_page(viewport={'width': size[0], 'height': size[1]})
                await page.goto(f'http://127.0.0.1:{port}/maps/#{view}/on:{layer}/v:')
                await page.wait_for_function('window.mapsReview && window.mapsReview.map')
                await page.add_style_tag(content=HIDE_CSS)
                z, lat, lng = (float(x) for x in view.split('/'))
                await page.evaluate(f'(() => {{ const m = mapsReview.map; m.invalidateSize(false); m.setView([{lat}, {lng}], {z}, {{animate: false}}); }})()')
                t0 = time.time()
                await page.wait_for_timeout(1500)
                while time.time() - t0 < 45:
                    pending = await page.evaluate("[...document.querySelectorAll('img.leaflet-tile')].filter(i => !i.complete).length")
                    if pending == 0: break
                    await page.wait_for_timeout(500)
                await page.wait_for_timeout(1200)
                path.parent.mkdir(parents=True, exist_ok=True)
                await page.screenshot(path=str(path))
                await page.close()
                print(f'  still {path.name} ({time.time()-t0:.0f}s)', flush=True)
            await browser.close()
    finally:
        srv.shutdown()

# ---------------------------------------------------------------- drawing
def ease(x):
    x = min(1., max(0., x)); return x * x * (3 - 2 * x)

class Still:
    """A captured map with a half-size level for wide framings (cheap mipmapping)."""
    def __init__(self, path, layer=''):
        img = cv2.cvtColor(cv2.imread(str(path)), cv2.COLOR_BGR2RGB)
        # The five-foot scans read pale on video: darken midtones so linework holds.
        # The six-inch sheets are printed darker and need only a touch.
        g = GAMMA.get(layer, 1.45)
        img = cv2.LUT(img, (255 * (np.arange(256) / 255.) ** g).astype(np.uint8))
        self.l0 = img
        self.l1 = cv2.resize(img, (img.shape[1] // 2, img.shape[0] // 2), interpolation=cv2.INTER_AREA)

    def frame(self, u, v, k, w=W, h=H):
        h0, w0 = self.l0.shape[:2]
        s = (w / w0) * k                          # output px per level-0 px
        cw, ch = w / s, h / s                     # visible source size
        cx = min(max(u * w0, cw / 2), w0 - cw / 2) if cw < w0 else w0 / 2
        cy = min(max(v * h0, ch / 2), h0 - ch / 2) if ch < h0 else h0 / 2
        src, sc, cx2, cy2 = (self.l1, s * 2, cx / 2, cy / 2) if s < .75 else (self.l0, s, cx, cy)
        M = np.float32([[sc, 0, w / 2 - sc * cx2], [0, sc, h / 2 - sc * cy2]])
        return cv2.warpAffine(src, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=BG)

def fonts():
    from fontTools.ttLib import TTFont
    out = {}
    for name, src in {'serif': 'caslon-400-normal.woff2', 'sans': 'archivo-100-900-normal.woff2'}.items():
        ttf = OUT / 'fonts' / src.replace('.woff2', '.ttf')
        if not ttf.exists():
            ttf.parent.mkdir(parents=True, exist_ok=True)
            f = TTFont(ROOT / 'docs/fonts' / src); f.flavor = None; f.save(ttf)
        out[name] = ttf
    return out

def font(path, size, weight=None):
    f = ImageFont.truetype(str(path), size)
    if weight:
        try: f.set_variation_by_axes([weight])
        except Exception: pass
    return f

def spaced(text, n=2):
    return (' ' * 0).join(ch + ' ' * n if ch != ' ' else '  ' for ch in text)

class Overlay:
    """Pre-rendered RGBA text plates, blended per frame with an opacity."""
    def __init__(self, F):
        self.F, self.cache = F, {}

    def plate(self, kind, text):
        key = (kind, text)
        if key in self.cache: return self.cache[key]
        layer = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
        if kind == 'title':
            f = font(self.F['sans'], 34, 620); t = spaced(text)
            b = d.textbbox((0, 0), t, font=f); tw, th = b[2] - b[0], b[3] - b[1]
            x, y = 96, H - 170
            d.rounded_rectangle([x - 26, y - 22, x + tw + 26, y + th + 26], 6, fill=(15, 23, 22, 205))
            d.rectangle([x - 26, y - 22, x - 20, y + th + 26], fill=GOLD + (255,))
            d.text((x - b[0], y - b[1]), t, font=f, fill=PARCHMENT + (255,))
        elif kind == 'map':
            f = font(self.F['sans'], 20, 600); t = spaced('MAP · ' + text, 1)
            b = d.textbbox((0, 0), t, font=f); tw, th = b[2] - b[0], b[3] - b[1]
            x, y = W - 64 - tw, 56
            d.rounded_rectangle([x - 16, y - 12, x + tw + 16, y + th + 14], 5, fill=(15, 23, 22, 185))
            d.text((x - b[0], y - b[1]), t, font=f, fill=PARCHMENT + (235,))
        elif kind == 'word':
            f = font(self.F['serif'], 120); b = d.textbbox((0, 0), text, font=f)
            tw, th = b[2] - b[0], b[3] - b[1]; x, y = 96, H - 120 - th
            d.text((x - b[0] + 3, y - b[1] + 4), text, font=f, fill=(15, 23, 22, 150))
            d.text((x - b[0], y - b[1]), text, font=f, fill=INK + (255,))
        elif kind.startswith('side'):
            f = font(self.F['sans'], 22, 620); t = spaced(text, 1)
            b = d.textbbox((0, 0), t, font=f); tw, th = b[2] - b[0], b[3] - b[1]
            x = 40 if kind == 'side-left' else W - 40 - tw
            y = 56
            d.rounded_rectangle([x - 14, y - 12, x + tw + 14, y + th + 14], 5, fill=(15, 23, 22, 200))
            d.text((x - b[0], y - b[1]), t, font=f, fill=PARCHMENT + (255,))
        arr = np.asarray(layer).astype(np.float32)
        ys, xs = np.nonzero(arr[..., 3])
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        crop = arr[y0:y1, x0:x1]
        self.cache[key] = (y0, y1, x0, x1, crop[..., :3], crop[..., 3:] / 255.)
        return self.cache[key]

    def blend(self, frame, kind, text, alpha):
        """Blend a plate into the frame in place, touching only the plate's bounding box."""
        if alpha <= 0: return frame
        y0, y1, x0, x1, rgb, a = self.plate(kind, text); a = a * alpha
        region = frame[y0:y1, x0:x1]
        frame[y0:y1, x0:x1] = region * (1 - a) + rgb * a
        return frame

def card(F, lines):
    img = Image.new('RGB', (W, H), INK); d = ImageDraw.Draw(img)
    y = 330
    f0 = font(F['serif'], 72); d.text((W // 2, y), lines[0], font=f0, fill=PARCHMENT, anchor='mm'); y += 120
    d.rectangle([W // 2 - 40, y - 30, W // 2 + 40, y - 27], fill=GOLD)
    f1 = font(F['sans'], 28, 420)
    for line in lines[1:]:
        for part in textwrap.wrap(line, 90):
            d.text((W // 2, y + 20), part, font=f1, fill=(205, 200, 186), anchor='mm'); y += 50
        y += 12
    return np.asarray(img).astype(np.float32)

# ---------------------------------------------------------------- timeline
def build(spec):
    shots, units, t = [], [], 0.
    for i, s in enumerate(spec['shots']):
        s = dict(s); s.setdefault('kind', 'map')
        s['units'] = [{'text': u, 'say': spoken(u, spec['say']),
                       'wav': OUT / 'voice' / f"{s['id']}-{j}-{hashlib.sha1((spoken(u, spec['say'])+spec['voice']+str(spec['speed'])).encode()).hexdigest()[:8]}.wav"}
                      for j, u in enumerate(s.get('units', []))]
        units += s['units']; shots.append(s)
    return shots, units

def place(shots):
    t = 0.
    for i, s in enumerate(shots):
        s['start'] = t - XFADE if i else 0.
        cur = s['start'] + (XFADE if i else 0.) + s.get('lead', .5)
        for u in s['units']:
            u['start'] = cur; cur += u['dur'] + GAP
        end = (cur - GAP + s.get('tail', .5)) if s['units'] else s['start'] + s['dur']
        s['end'] = end; t = end
    return t

def stills_needed(s):
    k = s['kind']
    if k == 'map': return [(s['view'], s['layer'], (CW, CH))]
    if k == 'seq': return [(x['view'], x['layer'], (CW, CH)) for x in s['stills']]
    if k == 'wipe': return [(s['view'], l, (CW, CH)) for l in s['layers']]
    if k == 'split':  # each half: 960x1080 shown, captured at 1920x2160 for detail
        return [(s['view'], l, (CW // 2, CH)) for l in s['layers']]
    return []

def draw_shot(s, t, S, OV, F):
    p = (t - s['start']) / max(1e-6, s['end'] - s['start'])
    m = s.get('motion', [[.5, .5, 1.6], [.5, .5, 1.8]]); e = ease(p)
    u, v, k = [a + (b - a) * e for a, b in zip(*m)]
    kind = s['kind']
    if kind == 'map':
        fr = S[stills_needed(s)[0]].frame(u, v, k).astype(np.float32)
    elif kind == 'seq':
        n = len(s['stills']); i = min(n - 1, int(p * n)); q = ease(p * n - i)
        u2, v2, k2 = [a + (b - a) * q for a, b in zip(*m)]
        fr = S[stills_needed(s)[i]].frame(u2, v2, k2).astype(np.float32)
        fr = OV.blend(fr, 'word', s['stills'][i]['caption'], min(1., (p * n - i) * 6))
    elif kind == 'wipe':
        a, b = (S[x].frame(u, v, k).astype(np.float32) for x in stills_needed(s))
        w0, w1 = s.get('wipe', [.2, .8]); x = int(W * ease((p - w0) / (w1 - w0)))
        fr = a.copy(); fr[:, :x] = b[:, :x]
        if 0 < x < W: fr[:, max(0, x - 2):x + 2] = PARCHMENT
        left, right = s['labels']
        fr = OV.blend(fr, 'side-right', left, 1. if x < W - 300 else 0.)
        fr = OV.blend(fr, 'side-left', right, 1. if x > 300 else 0.)
    elif kind == 'split':
        a, b = (S[x].frame(.5, .5, 1., W // 2, H).astype(np.float32) for x in stills_needed(s))
        fr = np.concatenate([a, b], axis=1); fr[:, W // 2 - 2:W // 2 + 2] = PARCHMENT
        fr = OV.blend(fr, 'side-left', s['labels'][0], 1.); fr = OV.blend(fr, 'side-right', s['labels'][1], 1.)
    elif kind == 'card':
        fr = s.setdefault('_card', card(F, s['lines'])).copy()
    if s.get('map') and kind in ('map', 'seq'):
        fr = OV.blend(fr, 'map', s['map'], 1.)
    for c in s.get('captions', []):
        a = min(ease((p - c['at']) * 8), ease((c['until'] - p) * 8))
        fr = OV.blend(fr, c['style'], c['text'], a)
    return fr

# ---------------------------------------------------------------- main
def srt_time(x):
    ms = int(round(x * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--only', help='render a single shot id, for checking framing')
    ap.add_argument('--fresh-audio', action='store_true'); ap.add_argument('--fresh-stills', action='store_true')
    args = ap.parse_args()
    spec = json.loads(SPEC.read_text())
    shots, units = build(spec)
    print('1/3 narration', flush=True); narrate(spec, units, args.fresh_audio)
    total = place(shots)
    print(f'    {len(units)} units, film {total/60:.1f} min', flush=True)

    print('2/3 stills', flush=True)
    jobs = {key: still_path(*key) for s in shots for key in stills_needed(s)}
    todo = {k: p for k, p in jobs.items() if args.fresh_stills or not p.exists()}
    if todo: asyncio.run(capture(todo))
    S = {k: Still(p, k[1]) for k, p in jobs.items()}

    F = fonts(); OV = Overlay(F)
    if args.only:
        shots = [s for s in shots if s['id'] == args.only]
        off = shots[0]['start']; total = shots[0]['end'] - off
        for s in shots: s['start'] -= off; s['end'] -= off
        for u in shots[0]['units']: u['start'] -= off
        units = shots[0]['units']
    name = f"cartography-film-{args.only}" if args.only else 'cartography-film-draft'

    # Narration track and subtitles.
    import soundfile as sf
    track = np.zeros(int((total + 1) * RATE), np.float32); cues = []
    for i, u in enumerate(units):
        a, _ = sf.read(u['wav'], dtype='float32'); o = int(u['start'] * RATE)
        track[o:o + len(a)] += a[:len(track) - o]
        cues.append(f"{i+1}\n{srt_time(u['start'])} --> {srt_time(u['start'] + u['dur'])}\n{textwrap.fill(u['text'], 64)}\n")
    raw = OUT / f'{name}-voice-raw.wav'; voice = OUT / f'{name}-voice.wav'
    sf.write(raw, track, RATE, subtype='PCM_16')
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(raw), '-af', 'loudnorm=I=-16:TP=-1.5:LRA=7', '-ar', '48000', str(voice)], check=True)
    (OUT / f'{name}.srt').write_text('\n'.join(cues))

    print(f'3/3 frames ({total:.0f}s)', flush=True)
    mp4 = OUT / f'{name}.mp4'
    enc = subprocess.Popen(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
                            '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                            '-i', str(voice), '-map', '0:v', '-map', '1:a',
                            '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p',
                            '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', str(mp4)], stdin=subprocess.PIPE)
    n = int(total * FPS); t0 = time.time()
    for f in range(n):
        t = f / FPS
        active = [s for s in shots if s['start'] <= t < s['end']]
        if not active: active = [shots[-1]]
        fr = draw_shot(active[-1], t, S, OV, F)
        if len(active) > 1:   # dissolve from the previous shot
            a = ease((t - active[-1]['start']) / XFADE)
            fr = draw_shot(active[0], t, S, OV, F) * (1 - a) + fr * a
        g = min(1., t / .8, (total - t) / 1.2)    # fade in from and out to black
        enc.stdin.write((fr * max(0., g)).clip(0, 255).astype(np.uint8).tobytes())
        if f % (FPS * 20) == 0: print(f'    {t:6.1f}s  {(time.time()-t0)/max(1,f)*1000:.0f} ms/frame', flush=True)
    enc.stdin.close(); enc.wait()
    meta = {'film': str(mp4.relative_to(ROOT)), 'duration_s': round(total, 2), 'frames': n,
            'shots': [{'id': s['id'], 'start': round(s['start'], 2), 'end': round(s['end'], 2)} for s in shots]}
    (OUT / f'{name}.json').write_text(json.dumps(meta, indent=1))
    print(f'Done: {mp4}', flush=True)

if __name__ == '__main__':
    main()
