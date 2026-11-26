"""Vertical YouTube Short (1080x1920) from the 16:9 ABC clip: blurred fill background, rounded framed video,
bouncing 'BABY YUYU' title, and kid-friendly lyric captions (letters pop in one by one, each in its own colour).
Audio: mix.wav (ElevenLabs voice-changed vocal + beat-aligned ElevenLabs background loop).

Usage: [SHORT_CFG=bubbles] [SHORT_DUR=45] python3 short.py SRC.mp4 [preview_t ...]
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
LYR = [   # timings from word-level transcription of the Eleven Music song; letter lines carry per-letter times
    (0.0, ''), (3.0, "Hello, hello, I'm Baby Yuyu!"), (5.8, "Come and dance, I'll sing with you"),
    (8.4, 'Clap your hands and move your feet'), (10.6, "Let's sing letters to the beat!"),
    (13.9, 'ABCDEFG', [13.96, 14.5, 14.9, 15.3, 15.55, 15.75, 15.95]), (16.2, 'Come and dance along with me'),
    (18.8, 'HIJKLMN', [18.86, 19.8, 20.16, 20.6, 20.85, 21.1, 21.4]), (21.7, 'Jump up high and clap again'),
    (23.9, 'OPQRSTU', [23.96, 25.1, 25.6, 26.22, 26.64, 27.1, 27.45]), (27.7, 'Wiggle, wiggle, Baby Yuyu!'),
    (29.9, 'VWXYZ', [30.0, 30.36, 30.94, 31.64, 32.18]), (32.5, 'Now I know my ABC!'),
    (34.9, 'Clap, clap, clap! Hip hip hooray!'), (37.5, 'We learned our ABCs today!'), (40.4, 'Yay! Bye bye!'), (46.0, ''),
]
SUBTITLE, BG_MODE, AUDIO, OUT = 'ABC Song', 'letters', 'mix.wav', 'baby_yuyu_abc_short.mp4'
if os.environ.get('SHORT_CFG') == 'bubbles':        # Bubble colour song (Eleven Music take 2 word timings)
    RED_, BLUE_, YEL_, GRN_ = (238, 48, 62), (38, 140, 245), (255, 208, 30), (58, 196, 78)
    LYR = [
        (0.0, ''), (5.2, "Hello, hello, I'm Baby Yuyu!"), (8.6, "I've got magic bubbles for you!"),
        (11.8, 'Big ones, small ones, floating high'), (14.8, 'Colorful bubbles in the sky!'),
        (17.7, 'Red, red, apples on the tree', {'big': 'RED', 'col': RED_}),
        (20.8, 'Blue, blue, look up with me!', {'big': 'BLUE', 'col': BLUE_}),
        (23.7, 'Yellow, yellow, sunshine bright', {'big': 'YELLOW', 'col': YEL_}),
        (26.6, 'Green, green, what a lovely sight!', {'big': 'GREEN', 'col': GRN_}),
        (29.6, "Pop, pop, pop! Let's sing along!", {'big': 'POP!', 'col': None}),
        (32.7, 'Colors make a happy song!'), (35.7, 'Clap your hands and dance with me'),
        (38.8, 'Baby Yuyu, one, two, three!'), (41.8, 'Yay! Bye bye!'), (46.0, ''),
    ]
    SUBTITLE, BG_MODE, AUDIO, OUT = 'Bubble Song', 'bubbles', 'mix_bubbles.wav', 'baby_yuyu_bubble_short.mp4'
if os.environ.get('SHORT_CFG') == 'bubbles2':       # bird-sweater bubble video, 30 s song (Eleven Music take 2 timings) + SFX
    RED_, BLUE_, YEL_, GRN_ = (238, 48, 62), (38, 140, 245), (255, 208, 30), (58, 196, 78)
    LYR = [
        (0.0, "Hello, hello, I'm Baby Yuyu!"), (2.8, "I've got magic bubbles for you!"),
        (4.9, 'Big ones, small ones, floating high'), (7.0, 'Colorful bubbles in the sky!'),
        (9.1, 'Red, red, apples on the tree', {'big': 'RED', 'col': RED_}),
        (11.3, 'Blue, blue, look up with me!', {'big': 'BLUE', 'col': BLUE_}),
        (13.5, 'Yellow, yellow, sunshine bright', {'big': 'YELLOW', 'col': YEL_}),
        (15.7, 'Green, green, what a lovely sight!', {'big': 'GREEN', 'col': GRN_}),
        (17.7, 'Watch the magic bubbles go...'),
        (20.0, "Pop, pop, pop! Let's sing along!", {'big': 'POP!', 'col': None}),
        (22.2, 'Colors make a happy song!'), (24.4, 'Clap your hands and dance with me'),
        (26.5, 'Baby Yuyu, one, two, three!'), (28.6, 'Yay!'), (31.0, ''),
    ]
    SUBTITLE, BG_MODE, AUDIO, OUT = 'Bubble Song', 'bubbles', 'mix_bubbles2.wav', 'baby_yuyu_bubble2_short.mp4'
DUR_END = float(os.environ.get('SHORT_DUR', '30.4'))
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
    idx = max(i for i, L in enumerate(LYR) if L[0] <= t)
    s, text = LYR[idx][:2]; extra = LYR[idx][2] if len(LYR[idx]) > 2 else None
    times = extra if isinstance(extra, list) else None; big = extra if isinstance(extra, dict) else None
    e = LYR[idx + 1][0] if idx + 1 < len(LYR) else s + 3
    if not text: return
    k = (t - s) / 0.35
    cy = 1500
    if text.isupper() and ' ' not in text:          # letters line: pop letters one by one
        n = len(text); step = (e - s - 0.2) / n; size = 150 if n > 5 else 170
        f = R.font(size); gap = 10
        ws = [f.getlength(c) for c in text]; total = sum(ws) + gap * (n - 1); x = W / 2 - total / 2
        for i, ch in enumerate(text):
            ti = times[i] if times else s + i * step; kk = (t - ti) / 0.3
            if kk > 0:
                active = 1 + 0.25 * math.exp(-max(0, t - ti) * 6)
                R.put(fr, R.glyph(ch, size, COLS[i % len(COLS)]), x + ws[i] / 2, cy - 14 * math.sin(t * 6 + i), 1, R.back(kk) * active, 5 * math.sin(t * 4 + i))
            x += ws[i] + gap
        return
    if big:                                          # big colour word above the lyric line
        cols = [big['col']] if big['col'] else COLS
        R.word(fr, big['big'], W / 2, 1360, 170, cols, s, t, 0.06, pulse=0.1 * math.exp(-max(0, t - s) * 4))
        cy = 1560
    lines = wrap(text, 76, 960)
    for j, ln in enumerate(lines):
        y = cy - (len(lines) - 1) * 50 + j * 100
        R.put(fr, R.plain(ln, 76, (255, 255, 255), (60, 40, 160), 10), W / 2, y, 1, R.back(k) * (1 + 0.02 * math.sin(t * 8)))


_rng = np.random.default_rng(4)
BG_LETTERS = []
for i, ch in enumerate('ABCDEFGHIJKLMNOPQRSTUVWXYZ' * 2):
    # spread across the margins (above / below the framed video), drifting upward and looping
    BG_LETTERS.append(dict(ch=ch, x=_rng.uniform(70, W - 70), y0=_rng.uniform(0, H), size=int(_rng.uniform(90, 150)),
                           col=COLS[i % len(COLS)], sp=_rng.uniform(35, 70), ph=_rng.uniform(0, 6.28), rot=_rng.uniform(-15, 15)))


def bg_letters(fr, t):
    for L in BG_LETTERS:
        y = (L['y0'] - L['sp'] * t) % (H + 200) - 100
        if VID_Y - 90 < y < VID_Y + VH + 90 or 140 < y < 480: continue   # keep the video and title areas clear
        x = L['x'] + 25 * math.sin(t * 1.2 + L['ph'])
        R.put(fr, R.glyph(L['ch'], L['size'], L['col'], None, False), x, y, 0.55, 1 + 0.06 * math.sin(t * 3 + L['ph']),
              L['rot'] + 8 * math.sin(t * 1.5 + L['ph']))


BG_BUBBLES = [dict(x=_rng.uniform(60, W - 60), y0=_rng.uniform(0, H), r=int(_rng.uniform(22, 60)), col=COLS[i % len(COLS)],
                   sp=_rng.uniform(40, 90), ph=_rng.uniform(0, 6.28), glossy=bool(i % 3)) for i in range(46)]


def bg_bubbles(fr, t):
    for b in BG_BUBBLES:
        y = (b['y0'] - b['sp'] * t) % (H + 200) - 100
        if VID_Y - 70 < y < VID_Y + VH + 70 or 140 < y < 480: continue   # keep the video and title areas clear
        x = b['x'] + 30 * math.sin(t * 1.4 + b['ph'])
        R.draw_bubble(fr, b['col'], x, y, b['r'] * (1 + 0.05 * math.sin(t * 4 + b['ph'])), b['glossy'], 0.75)


def compose(src_rgb, t):
    im = Image.frombytes('RGB', (SW, SH), src_rgb)
    # background: cover-scale + heavy blur (done small for speed) + soft colour wash
    small = im.resize((96, 54), Image.BILINEAR).filter(ImageFilter.GaussianBlur(3))
    bgw = int(H * SW / SH)
    bg = small.resize((bgw, H), Image.BILINEAR).crop(((bgw - W) // 2, 0, (bgw - W) // 2 + W, H)).convert('RGBA')
    wash = Image.new('RGBA', (W, H), (255, 255, 255, 50)); bg.alpha_composite(wash)
    fr = bg
    bg_letters(fr, t) if BG_MODE == 'letters' else bg_bubbles(fr, t)
    # bobbing framed video
    bob = 6 * math.sin(t * 2 * math.pi / 1.346)
    x0 = (W - VW) // 2; y0 = int(VID_Y + bob)
    fr.alpha_composite(SHADOW, (x0 - 40, y0 - 40))
    fr.alpha_composite(FRAME, (x0 - 12, y0 - 12))
    v = im.resize((VW, VH), Image.LANCZOS).convert('RGBA'); v.putalpha(MASK)
    fr.alpha_composite(v, (x0, y0))
    # title
    R.word(fr, 'BABY YUYU', W / 2, 250, 132, COLS, 0.0, t + 1, 0.05)
    R.put(fr, R.plain(SUBTITLE, 74, (255, 255, 255), (238, 48, 62), 10), W / 2, 420, 1, 1 + 0.04 * math.sin(t * 2 * math.pi / 0.673))
    caption(fr, t)
    # little sparkles in the corners on the beat
    d = ImageDraw.Draw(fr)
    for i, (sx, sy) in enumerate([(90, 470), (990, 470), (110, 1760), (970, 1760)]):
        tw = 0.5 + 0.5 * math.sin(t * 5 + i * 1.6); r = 18 + 16 * tw
        pts = [(sx + (r if k % 2 == 0 else r * 0.42) * math.cos(t + k * math.pi / 5 - math.pi / 2),
                sy + (r if k % 2 == 0 else r * 0.42) * math.sin(t + k * math.pi / 5 - math.pi / 2)) for k in range(10)]
        d.polygon(pts, fill=(255, 225, 70, 255), outline=(255, 255, 255, 255))
    out = fr.convert('RGB')
    f = min(1.0, t / 0.3, max(0.0, (DUR_END - t) / 0.8))
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
                           '-i', AUDIO, '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
                           '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
    for i, b in enumerate(frames()):
        ff.stdin.write(compose(b, i / FPS).tobytes())
    ff.stdin.close(); ff.wait(); print('done ->', OUT)
