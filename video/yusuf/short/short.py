"""Vertical YouTube Short (1080x1920) from the 16:9 ABC clip: blurred fill background, rounded framed video,
bouncing 'BABY YUYU' title, and kid-friendly lyric captions (letters pop in one by one, each in its own colour).
Audio: mix.wav (ElevenLabs voice-changed vocal + beat-aligned ElevenLabs background loop).

Usage: python3 short.py SRC.mp4 [preview_t ...]
"""
import math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
import render as R                        # reuse glyph/word/plain helpers + fonts

W, H, FPS = 1080, 1920, 24
SRC = sys.argv[1]
SW, SH = 1024, 576
COLS = [(238, 48, 62), (255, 150, 30), (255, 208, 30), (58, 196, 78), (38, 140, 245), (160, 72, 222), (255, 110, 190)]
LYR = [
    (0.0, 'Hello, hello, I\'m Baby Yuyu!'), (1.8, 'Come and dance, I\'ll sing with you'),
    (3.3, 'Clap your hands and move your feet'), (4.6, 'Let\'s sing letters to the beat!'),
    (6.8, 'ABCDEFG'), (9.0, 'Come dance along with me'), (10.2, 'HIJKLMN'), (12.1, 'Jump up high and clap again'),
    (13.7, 'OPQRSTU'), (16.4, 'Wiggle, wiggle, Baby Yuyu'), (18.3, 'VWXYZ'), (20.4, 'Dance along and sing with me'),
    (22.3, 'Clap, clap, clap, hip hip hooray!'), (24.8, 'We learned our ABCs today!'), (26.6, 'Dance with Yuyu'),
    (27.6, 'One, two, three, learning letters happily!'), (30.2, ''),
]
VID_Y = 560                                # top of framed video
VW, VH = 1040, int(1040 * SH / SW)


def rounded_mask(w, h, r):
    m = Image.new('L', (w * 3, h * 3)); ImageDraw.Draw(m).rounded_rectangle([0, 0, w * 3 - 1, h * 3 - 1], r * 3, fill=255)
    return m.resize((w, h), Image.LANCZOS)


MASK = rounded_mask(VW, VH, 46)
FRAME = Image.new('RGBA', (VW + 24, VH + 24))
ImageDraw.Draw(FRAME).rounded_rectangle([0, 0, VW + 23, VH + 23], 56, fill=(255, 255, 255, 255))
SHADOW = Image.new('RGBA', (VW + 80, VH + 80))
ImageDraw.Draw(SHADOW).rounded_rectangle([30, 40, VW + 50, VH + 60], 60, fill=(20, 10, 60, 120))
SHADOW = SHADOW.filter(ImageFilter.GaussianBlur(18))


def wrap(text, size, maxw):
    f = R.font(size); words = text.split(); lines, cur = [], ''
    for w_ in words:
        t = (cur + ' ' + w_).strip()
        if f.getlength(t) > maxw and cur: lines.append(cur); cur = w_
        else: cur = t
    return lines + ([cur] if cur else [])


def caption(fr, t):
    idx = max(i for i, (s, _) in enumerate(LYR) if s <= t)
    s, text = LYR[idx]; e = LYR[idx + 1][0] if idx + 1 < len(LYR) else s + 3
    if not text: return
    k = (t - s) / 0.35
    cy = 1500
    if text.isupper() and ' ' not in text:          # letters line: pop letters one by one
        n = len(text); step = (e - s - 0.2) / n; size = 150 if n > 5 else 170
        f = R.font(size); gap = 10
        ws = [f.getlength(c) for c in text]; total = sum(ws) + gap * (n - 1); x = W / 2 - total / 2
        for i, ch in enumerate(text):
            ti = s + i * step; kk = (t - ti) / 0.3
            if kk > 0:
                active = 1 + 0.25 * math.exp(-max(0, t - ti) * 6)
                R.put(fr, R.glyph(ch, size, COLS[i % len(COLS)]), x + ws[i] / 2, cy - 14 * math.sin(t * 6 + i), 1, R.back(kk) * active, 5 * math.sin(t * 4 + i))
            x += ws[i] + gap
        return
    lines = wrap(text, 76, 960)
    for j, ln in enumerate(lines):
        y = cy - (len(lines) - 1) * 50 + j * 100
        R.put(fr, R.plain(ln, 76, (255, 255, 255), (60, 40, 160), 10), W / 2, y, 1, R.back(k) * (1 + 0.02 * math.sin(t * 8)))


def compose(src_rgb, t):
    im = Image.frombytes('RGB', (SW, SH), src_rgb)
    # background: cover-scale + heavy blur (done small for speed) + soft colour wash
    small = im.resize((96, 54), Image.BILINEAR).filter(ImageFilter.GaussianBlur(3))
    bgw = int(H * SW / SH)
    bg = small.resize((bgw, H), Image.BILINEAR).crop(((bgw - W) // 2, 0, (bgw - W) // 2 + W, H)).convert('RGBA')
    wash = Image.new('RGBA', (W, H), (255, 255, 255, 50)); bg.alpha_composite(wash)
    fr = bg
    # bobbing framed video
    bob = 6 * math.sin(t * 2 * math.pi / 1.346)
    x0 = (W - VW) // 2; y0 = int(VID_Y + bob)
    fr.alpha_composite(SHADOW, (x0 - 40, y0 - 40))
    fr.alpha_composite(FRAME, (x0 - 12, y0 - 12))
    v = im.resize((VW, VH), Image.LANCZOS).convert('RGBA'); v.putalpha(MASK)
    fr.alpha_composite(v, (x0, y0))
    # title
    R.word(fr, 'BABY YUYU', W / 2, 250, 132, COLS, 0.0, t + 1, 0.05)
    R.put(fr, R.plain('ABC Song', 74, (255, 255, 255), (238, 48, 62), 10), W / 2, 420, 1, 1 + 0.04 * math.sin(t * 2 * math.pi / 0.673))
    caption(fr, t)
    # little sparkles in the corners on the beat
    d = ImageDraw.Draw(fr)
    for i, (sx, sy) in enumerate([(90, 470), (990, 470), (110, 1760), (970, 1760)]):
        tw = 0.5 + 0.5 * math.sin(t * 5 + i * 1.6); r = 18 + 16 * tw
        pts = [(sx + (r if k % 2 == 0 else r * 0.42) * math.cos(t + k * math.pi / 5 - math.pi / 2),
                sy + (r if k % 2 == 0 else r * 0.42) * math.sin(t + k * math.pi / 5 - math.pi / 2)) for k in range(10)]
        d.polygon(pts, fill=(255, 225, 70, 255), outline=(255, 255, 255, 255))
    out = fr.convert('RGB')
    f = min(1.0, t / 0.3, max(0.0, (30.4 - t) / 0.6))
    if f < 1: out = Image.blend(Image.new('RGB', (W, H), (255, 255, 255)), out, f)
    return out


def frames():
    p = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-i', SRC, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    n = SW * SH * 3
    while True:
        b = p.stdout.read(n)
        if len(b) < n: break
        yield b


if __name__ == '__main__':
    os.chdir(HERE)
    if len(sys.argv) > 2:
        od = os.environ.get('PREVIEW_DIR', '/tmp'); want = [float(a) for a in sys.argv[2:]]
        for i, b in enumerate(frames()):
            t = i / FPS
            for w_ in want:
                if abs(t - w_) < 0.5 / FPS: compose(b, t).save(f'{od}/short_{w_}.png'); print('saved', w_)
        sys.exit()
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-i', 'mix.wav', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
                           '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', 'baby_yuyu_abc_short.mp4'], stdin=subprocess.PIPE)
    for i, b in enumerate(frames()):
        ff.stdin.write(compose(b, i / FPS).tobytes())
    ff.stdin.close(); ff.wait(); print('done -> baby_yuyu_abc_short.mp4')
