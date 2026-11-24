"""Kishki "From Farm to Fire" cooking promo (1920x1080, 30 fps, cinematic letterbox).
Three chapters – chicken, lamb, beef – each: farm -> fresh cut -> grill/smoke -> served.
Stock clips (Pexels, see broll/CREDITS.txt) + the shop's own photos.

Usage: python3 kashki_cooking.py [target_seconds] -> kashki_cooking_nomusic.mp4
"""
import os, sys, math, subprocess, numpy as np
os.environ.setdefault('NO_PRICES', '1')
import kashki_promo as K
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

W, H, FPS, HERE, UP = K.W, K.H, K.FPS, K.HERE, K.UP
B = f'{HERE}/broll'
BAR = 120  # letterbox bar height

# (kind, src, start/box, dur, style, ar, en)   style: big = chapter card, low = lower third, none
SEGS = [
 ('video', f'{B}/fire_flames.mp4', 0.0, 4.5, 'title', 'من المزرعة… إلى النار', 'FROM FARM TO FIRE'),
 # chicken
 ('video', f'{B}/white_chickens_feeding.mp4', 0.5, 3.0, 'big', 'دجاج طازج', 'FARM-FRESH CHICKEN'),
 ('photo', f'{HERE}/ai/chicken_trays_test.jpg', (0, 0, 2048, 1152), 2.6, 'none', '', ''),
 ('video', f'{B}/cook_chicken_grill.mp4', 0.0, 3.6, 'low', 'على الفحم', 'CHARCOAL GRILLED'),
 ('video', f'{B}/cook_chicken_smoke.mp4', 0.0, 3.0, 'none', '', ''),
 ('video', f'{B}/cook_chicken_skewers.mp4', 0.0, 3.0, 'low', 'أسياخ دجاج', 'CHICKEN SKEWERS'),
 # lamb
 ('video', f'{B}/sheep_close.mp4', 0.5, 3.0, 'big', 'غنم طازج', 'FARM-FRESH LAMB'),
 ('video', f'{B}/cook_lamb_chops.mp4', 0.0, 3.6, 'low', 'ريش غنم', 'LAMB CHOPS'),
 ('video', f'{B}/cook_kebab_smoke.mp4', 0.0, 3.4, 'low', 'كباب على الجمر', 'KEBAB ON EMBERS'),
 ('video', f'{B}/cook_kebab_coals.mp4', 0.0, 3.0, 'none', '', ''),
 ('video', f'{B}/cook_lamb_spit.mp4', 0.0, 3.2, 'low', 'غنم مشوي', 'SLOW-ROASTED LAMB'),
 # beef
 ('video', f'{B}/cows_pasture.mp4', 0.5, 3.0, 'big', 'لحم بقري طازج', 'FARM-FRESH BEEF'),
 ('photo', f'{UP}/4ad90696-image.jpg', (0, 200, 2000, 1325), 2.6, 'none', '', ''),
 ('video', f'{B}/cook_steak_ongrill.mp4', 0.0, 3.4, 'low', 'ستيك على النار', 'STEAK ON THE FIRE'),
 ('video', f'{B}/cook_steak_flames.mp4', 0.0, 3.2, 'none', '', ''),
 ('video', f'{B}/cook_steak_sliced.mp4', 0.0, 3.4, 'low', 'طري… وعصاري', 'TENDER & JUICY'),
 # outro
 ('photo', f'{UP}/2222e64c-image.jpg', (0, 150, 2000, 1275), 3.0, 'none', '', ''),
 ('outro', None, None, 6.0, 'none', '', ''),
]

def grade(img):
    a = np.asarray(img).astype(np.float32)
    a = (a - 128) * 1.12 + 128                     # contrast
    a[..., 0] *= 1.05; a[..., 2] *= 0.92           # warm
    lum = a.mean(axis=2, keepdims=True); a = lum + (a - lum) * 1.12   # saturation
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

yy, xx = np.mgrid[0:H, 0:W]
VIG = Image.fromarray((np.clip(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.62)) ** 2, 0, 1) ** 1.6 * 170).astype(np.uint8))
VIGNETTE = Image.new('RGBA', (W, H), (0, 0, 0, 255)); VIGNETTE.putalpha(VIG)
BARS = Image.new('RGBA', (W, H)); bd = ImageDraw.Draw(BARS)
bd.rectangle((0, 0, W, BAR), fill=(0, 0, 0, 255)); bd.rectangle((0, H - BAR, W, H), fill=(0, 0, 0, 255))
LOGO = K.text_img('كشكي', K.cairo(64), K.YEL, rtl=True, glow=K.RED + (140,))
TAG = K.text_img('HALAL  ·  FARM FRESH', K.mont(22), (200, 190, 175))

def big_card(ar, en):
    a = K.text_img(ar, K.cairo(150), (255, 255, 255), rtl=True, glow=(0, 0, 0, 200))
    e = K.text_img(en, K.bebas(64), K.GOLD)
    return a, e
def low_third(ar, en):
    a = K.text_img(ar, K.cairo(62), (255, 255, 255), rtl=True)
    e = K.text_img(en, K.mont(26), K.GOLD)
    return a, e
CARDS = {i: (big_card if s[4] in ('big', 'title') else low_third)(s[5], s[6]) for i, s in enumerate(SEGS) if s[4] != 'none'}

OUT_LOGO = K.text_img('كشكي', K.cairo(240), K.YEL, rtl=True, glow=K.RED + (210,))
OUT_1 = K.text_img('من المزرعة إلى سفرتك', K.cairo(70), (255, 255, 255), rtl=True)
OUT_2 = K.text_img('KISHKI HALAL SUPERMARKET', K.bebas(56), K.GOLD)
OUT_3 = K.pill('يلا على كشكي!')

def ember_layer(t, n=28, seed=3):
    rng = np.random.default_rng(seed); L = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(L)
    for _ in range(n):
        x0, sp, ph, r = rng.uniform(0, W), rng.uniform(60, 160), rng.uniform(0, 6.28), rng.uniform(2, 5)
        y = H - ((t * sp + ph * 200) % (H + 100)); x = x0 + 30 * math.sin(t + ph)
        a = int(200 * (0.5 + 0.5 * math.sin(t * 3 + ph)))
        d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 150, 60, a))
    return L.filter(ImageFilter.GaussianBlur(1.5))

def compose(fr, t, dur, i, seg):
    f = fr.convert('RGBA'); f.alpha_composite(VIGNETTE)
    style = seg[4]
    if style in ('big', 'title'):
        dim = Image.new('RGBA', (W, H), (0, 0, 0, int(110 * (1 - K.ease((t - dur + 0.8) / 0.6))))); f.alpha_composite(dim)
        a, e = CARDS[i]; k = K.ease((t - 0.15) / 0.7); out = 1 - K.ease((t - dur + 0.7) / 0.5)
        K.put(f, a, W / 2, H / 2 - 30 + 40 * (1 - k), k * out, 0.92 + 0.08 * k)
        line = Image.new('RGBA', (int(520 * k) + 1, 3), K.GOLD + (255,)); K.put(f, line, W / 2, H / 2 + 75, k * out)
        K.put(f, e, W / 2, H / 2 + 125, K.ease((t - 0.5) / 0.6) * out)
        if style == 'title': f.alpha_composite(ember_layer(t))
    elif style == 'low':
        a, e = CARDS[i]; k = K.ease((t - 0.3) / 0.5); out = 1 - K.ease((t - dur + 0.5) / 0.4)
        x = W - 120 - a.width / 2 + 60 * (1 - k)
        K.put(f, a, x, H - BAR - 105, k * out); K.put(f, e, W - 120 - e.width / 2 + 60 * (1 - k), H - BAR - 45, k * out)
        bar = Image.new('RGBA', (6, 110), K.RED + (255,)); K.put(f, bar, W - 85, H - BAR - 80, k * out)
    f.alpha_composite(BARS)
    K.put(f, LOGO, 140, BAR / 2, 0.95); K.put(f, TAG, W - 40 - TAG.width / 2 + 50, BAR / 2, 0.8)
    return f

def outro(t):
    f = K.BG.copy(); f.alpha_composite(ember_layer(t, 40, 9))
    pulse = 1 + 0.015 * math.sin(t * math.pi * 2)
    k = K.back(t / .7); K.put(f, OUT_LOGO, W / 2, 380, K.ease(t / .3), k * pulse)
    k = K.ease((t - .6) / .6); K.put(f, OUT_1, W / 2, 590 + 30 * (1 - k), k)
    k = K.ease((t - 1.0) / .6); K.put(f, OUT_2, W / 2, 680 + 30 * (1 - k), k)
    k = K.back((t - 1.5) / .5); K.put(f, OUT_3, W / 2, 830, K.ease((t - 1.5) / .2), k)
    f.alpha_composite(BARS)
    return f

def render(i, seg, dur):
    out = f'{K.TMP}/ck{i:02d}.mp4'
    ff = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    N = int(round(dur * FPS)); kind = seg[0]
    if kind == 'photo':
        src = grade(K.load_photo(seg[1], seg[2], pink='4ad90696' in seg[1]))
    frames = K.video_frames(seg[1], seg[2], dur + 0.3, pink=False) if kind == 'video' else None
    last = None
    for n in range(N):
        t = n / FPS
        if kind == 'outro':
            f = outro(t)
        else:
            if kind == 'photo':
                p = t / dur; z = 1.0 + 0.10 * p
                cw, ch = src.width / z / 1.15, src.height / z / 1.15
                cx, cy = src.width / 2 + (p - 0.5) * 50, src.height / 2
                fr = src.crop((int(cx - cw / 2), int(cy - ch / 2), int(cx + cw / 2), int(cy + ch / 2))).resize((W, H), Image.BILINEAR)
            else:
                raw = next(frames, None) or last; last = raw
                z = 1.0 + 0.05 * t / dur
                fr = grade(raw.resize((int(W * z), int(H * z)), Image.BILINEAR).crop((int(W * (z - 1) / 2), int(H * (z - 1) / 2), int(W * (z - 1) / 2) + W, int(H * (z - 1) / 2) + H)))
            f = compose(fr, t, dur, i, seg)
        ff.stdin.write(f.convert('RGB').tobytes())
    ff.stdin.close(); ff.wait(); return out

if __name__ == '__main__':
    os.chdir(HERE)
    XF = 0.4
    target = float(sys.argv[1]) if len(sys.argv) > 1 else None
    base = sum(s[3] for s in SEGS) - XF * (len(SEGS) - 1)
    k = (target / base) if target else 1.0
    durs = [s[3] * k for s in SEGS]
    files = [render(i, s, durs[i]) for i, s in enumerate(SEGS)]
    inputs = sum([['-i', f] for f in files], [])
    chain, off, prev = [], 0, '0:v'
    for i in range(1, len(files)):
        off += durs[i - 1] - XF; lab = f'v{i}'
        tr = 'fadeblack' if SEGS[i][4] == 'big' or SEGS[i][0] == 'outro' else 'fade'
        chain.append(f'[{prev}][{i}:v]xfade=transition={tr}:duration={XF}:offset={off:.3f}[{lab}]'); prev = lab
    subprocess.run(['ffmpeg', '-y', '-v', 'error', *inputs, '-filter_complex', ';'.join(chain), '-map', f'[{prev}]',
                    '-c:v', 'libx264', '-preset', 'slow', '-crf', '19', '-pix_fmt', 'yuv420p', '-r', str(FPS), '-movflags', '+faststart',
                    'kashki_cooking_nomusic.mp4'], check=True)
    print('done', sum(durs) - XF * (len(durs) - 1))
