"""Oncoal song ad: re-cuts the v3 promo cards to the sung track, adds Sanaa / Shibam / Aden scenes
and word-synced Arabic lyric captions. Output: oncoal_song_ad.mp4 (1080x1920, 30 fps, 44 s)."""
import json, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFilter
from render_pro import font, text_img, ease, eio, W, H, GOLD, CREAM, ORANGE, BG

FPS, DUR = 30, 44.0
SRC = 'oncoal_promo_v3.mp4'      # cards: slot i occupies [4i, 4i+4), end card 36-44
SONG = 'assets/song/oncoal_song.mp3'
OUT = 'oncoal_song_ad.mp4'
XF = 0.25                          # crossfade length

# ---- source frames (1080x1920) -------------------------------------------------------------
import os, functools
FR = '/tmp/oncoal_src_frames'
if not os.path.exists(f'{FR}/done'):
    os.makedirs(FR, exist_ok=True)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', SRC, '-q:v', '2', f'{FR}/%04d.jpg'], check=True)
    open(f'{FR}/done', 'w').close()
NSRC = len([f for f in os.listdir(FR) if f.endswith('.jpg')])
@functools.lru_cache(maxsize=8)
def src_at_n(n): return np.asarray(Image.open(f'{FR}/{n + 1:04d}.jpg').convert('RGB'))
def src_at(t): return src_at_n(min(int(round(t * FPS)), NSRC - 1))

def card(slot, a=0.3, b=3.7):
    """Play the settled part of card `slot`, stretched to whatever length the segment needs."""
    def f(u):  # u in [0,1]
        return src_at(slot * 4 + a + (b - a) * u)
    return f

def end_card(u, length):
    return src_at(min(36.3 + u * length, 43.95))

# ---- city stills with Ken Burns ------------------------------------------------------------
def cover(path, zoom=1.0):
    im = Image.open(path).convert('RGB')
    s = max(W / im.width, H / im.height) * 1.18 * zoom
    return im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)

def city(path, label, sub, credit, pan=(0.5, 0.5, 0.5, 0.5), z=(1.0, 1.12), warm=True):
    base = cover(path)
    if warm:
        a = np.asarray(base).astype(np.float32); a[..., 0] *= 1.06; a[..., 2] *= 0.9
        base = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    lab = text_img(label, font('Ruqaa', 150), GOLD, rtl=True, glow=ORANGE + (170,))
    subi = text_img(sub, font('Cairo', 44, 'SemiBold'), CREAM, rtl=True)
    cred = text_img(credit, font('Cairo', 22, 'Regular'), (220, 210, 200), shadow=True)
    vign = Image.new('L', (W, H), 0); d = ImageDraw.Draw(vign)
    for i in range(60): d.rectangle((i * 6, i * 9, W - i * 6, H - i * 9), outline=int(150 * (1 - i / 60)))
    for y in range(700): d.line((0, y, W, y), fill=max(int(200 * (1 - y / 700) ** 1.3), 0))   # top scrim for the title
    vign = vign.filter(ImageFilter.GaussianBlur(60))
    shade = Image.new('RGB', (W, H), BG)
    def f(u):
        k = eio(u); zz = z[0] + (z[1] - z[0]) * k
        fx = pan[0] + (pan[2] - pan[0]) * k; fy = pan[1] + (pan[3] - pan[1]) * k
        sc = min(base.width / W, base.height / H)                # crop box in base pixels
        bw, bh = W * sc / zz, H * sc / zz
        x0 = (base.width - bw) * fx; y0 = (base.height - bh) * fy
        fr = base.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + bw, y0 + bh))
        fr = Image.composite(shade, fr, vign)
        fr = fr.convert('RGBA')
        al = ease(u * 4)
        for im, cy in ((lab, 330), (subi, 470)):
            t = im.copy(); t.putalpha(t.getchannel('A').point(lambda v: v * al))
            fr.alpha_composite(t, (W // 2 - im.width // 2, cy - im.height // 2 + int(30 * (1 - al))))
        fr.alpha_composite(cred, (W - cred.width - 10, 1500))
        return np.asarray(fr.convert('RGB'))
    return f

CRED = {l.split(':')[0]: l for l in open('assets/city/CREDITS.txt', encoding='utf-8').read().splitlines()}
def credit(k):
    line = CRED[k]; by = line.split(' by ')[1].split(',')[0].split(' (')[0].strip(); lic = line.split(', ')[-2]
    return f'Photo: {by} · {lic} · Wikimedia Commons'

# ---- timeline (cut points follow the sung lines, from the speech-to-text word timings) -----
SEG = [
    (0.0, 3.3, city('assets/city/sanaa1.jpg', 'صنعاء', 'من اليمن… إلى سفرتك', credit('sanaa1.jpg'), (0.5, 0.15, 0.5, 0.45), (1.0, 1.15))),
    (3.3, 6.8, card(0)),
    (6.8, 8.8, city('assets/city/shibam.jpg', 'حضرموت', 'شبام', credit('shibam.jpg'), (0.35, 0.5, 0.6, 0.5), (1.05, 1.15))),
    (8.8, 11.2, city('assets/city/aden.jpg', 'عدن', 'كريتر', credit('aden.jpg'), (0.55, 0.4, 0.8, 0.4), (1.0, 1.12))),
    (11.2, 14.3, card(1)),
    (14.3, 16.6, card(2)),
    (16.6, 21.8, card(3)),
    (21.8, 24.4, card(4)),
    (24.4, 26.9, card(6)),
    (26.9, 32.2, card(5)),
    (32.2, 34.8, city('assets/city/sanaa2.jpg', 'حياكم الله', 'صنعاء', credit('sanaa2.jpg'), (0.5, 0.2, 0.5, 0.4), (1.0, 1.1))),
    (34.8, 37.3, card(7)),
    (37.3, 39.1, card(8)),
    (39.1, 44.0, None),
]

def frame_at(t):
    for i, (a, b, f) in enumerate(SEG):
        if a <= t < b or i == len(SEG) - 1:
            u = (t - a) / (b - a)
            cur = end_card(t - a, b - a) if f is None else f(u)
            if i and t - a < XF:                      # crossfade from previous segment
                pa, pb, pf = SEG[i - 1]; pu = min((t - pa) / (pb - pa), 1.0)
                prev = pf(pu) if pf else end_card(t - pa, pb - pa)
                k = eio((t - a) / XF)
                cur = (prev * (1 - k) + cur * k).astype(np.uint8)
            return cur

# ---- lyric captions, word-synced -----------------------------------------------------------
LYR = ['بعدوو بعدوو', 'بعدوو من طريقنا', 'هذا اونكول هذا اونكول', 'أحلى مندي عندنا', 'أفضل لحوم لحومنا',
       'أفضل لحوم لحومنا', 'ما حد ينافس طبخنا', 'ما حد ينافس طبخنا', 'وكل الزباين أهلنا', 'وكل الزباين أهلنا',
       'مرحبا بكم لعندنا', 'مرحبا بكم لعندنا', 'هذا اونكول هذا اونكول', 'بعدوو عن طريقنا']
# the transcriber hears "اونكول" as two words ("هادون كل"), so each brand line maps to 4 sung words
words = [w for w in json.load(open('assets/song/transcript.json'))['words'] if w['type'] == 'word']
lines, i = [], 0
for L in LYR:
    toks = L.split(); n = 4 if 'اونكول' in L else len(toks)
    ws = words[i:i + n]; i += n
    if 'اونكول' in L:   # merge pairs back into display words
        times = [(ws[0]['start'], ws[0]['end']), (ws[0]['end'], ws[1]['end']), (ws[2]['start'], ws[2]['end']), (ws[2]['end'], ws[3]['end'])]
    else:
        times = [(w['start'], w['end']) for w in ws]
    lines.append((L, toks, times))
assert i == len(words), (i, len(words))
for k, (L, toks, times) in enumerate(lines):   # each line stays up until the next one starts
    nxt = lines[k + 1][2][0][0] if k + 1 < len(lines) else 42.5
    lines[k] = (L, toks, times, times[0][0] - 0.15, min(nxt - 0.1, times[-1][1] + 1.6))

capf = font('Cairo', 74, 'Black')
def word_img(w, col): return text_img(w, capf, col, rtl=True, shadow=True)
cache = {}
def caption(L, toks, times, t):
    gap = 22
    imgs = []
    for j, w in enumerate(toks):
        sung = t >= times[j][0]
        col = GOLD if sung else CREAM
        key = (w, sung)
        if key not in cache: cache[key] = word_img(w, col)
        imgs.append(cache[key])
    tw = sum(im.width - 100 for im in imgs) + gap * (len(imgs) - 1)
    out = Image.new('RGBA', (W, 260))
    bg = Image.new('L', (W, 260)); ImageDraw.Draw(bg).rounded_rectangle(
        (W // 2 - tw // 2 - 40, 60, W // 2 + tw // 2 + 40, 200), 70, fill=175)
    out.paste(Image.new('RGBA', (W, 260), (18, 10, 6, 255)), mask=bg.filter(ImageFilter.GaussianBlur(6)))
    x = W // 2 + tw // 2                      # right-to-left
    for j, im in enumerate(imgs):
        w_ = im.width - 100
        pop = 1.0
        if times[j][0] <= t < times[j][0] + 0.18: pop = 1.08 - 0.08 * (t - times[j][0]) / 0.18
        tmp = im if pop == 1.0 else im.resize((int(im.width * pop), int(im.height * pop)))
        out.alpha_composite(tmp, (x - w_ - 50 - (tmp.width - im.width) // 2, 130 - tmp.height // 2))
        x -= w_ + gap
    return out

def overlay(fr, t):
    im = Image.fromarray(fr).convert('RGBA')
    for L, toks, times, a, b in lines:
        if a <= t < b:
            c = caption(L, toks, times, t)
            al = min(ease((t - a) / 0.2), ease((b - t) / 0.2))
            c.putalpha(c.getchannel('A').point(lambda v: v * al))
            im.alpha_composite(c, (0, 1640 + int(20 * (1 - al))))
    if t >= 43.2:                              # fade to black
        k = (t - 43.2) / 0.8
        im = Image.blend(im, Image.new('RGBA', im.size, (0, 0, 0, 255)), min(k, 1))
    return np.asarray(im.convert('RGB'))

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:                      # preview stills: python3 song_ad.py 5 10 ...
        for s in sys.argv[1:]:
            Image.fromarray(overlay(frame_at(float(s)), float(s))).save(f'/tmp/prev_{s}.png')
        sys.exit()
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                            '-r', str(FPS), '-i', '-', '-i', SONG, '-map', '0:v', '-map', '1:a',
                            '-af', f'afade=t=out:st={DUR - 0.8}:d=0.8', '-t', str(DUR),
                            '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
                            '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
    for n in range(int(DUR * FPS)):
        t = n / FPS
        enc.stdin.write(overlay(frame_at(t), t).tobytes())
    enc.stdin.close(); enc.wait()
    print('wrote', OUT)
