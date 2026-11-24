"""Kashki promo video (1920x1080, 30 fps) for the shop TV: the shop's own photos & clips, price tags, logo.
No characters. Music/song is muxed on afterwards.

Usage: python3 kashki_promo.py [target_seconds]   -> kashki_promo_nomusic.mp4
"""
import os, sys, subprocess, math, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
FONTS = os.path.join(HERE, '..', 'video', 'fonts')
UP = os.environ.get('UPLOADS', '/root/.claude/uploads/7c825678-363e-58c3-b667-e0a3402e7eba')
TMP = os.environ.get('TMPDIR_SEG', '/tmp/kashki_seg'); os.makedirs(TMP, exist_ok=True)
W, H, FPS = 1920, 1080, 30
RED, GOLD, CREAM, MUTED, YEL, INK = (211, 50, 42), (240, 192, 96), (255, 246, 236), (179, 161, 145), (255, 210, 63), (40, 26, 20)
XF = 0.5  # crossfade seconds
NO_PRICES = bool(os.environ.get('NO_PRICES'))  # NO_PRICES=1 -> no price tags, output kashki_promo_noprices_nomusic.mp4

def font(name, size, var=None):
    f = ImageFont.truetype(os.path.join(FONTS, f'{name}.ttf'), size, layout_engine=ImageFont.Layout.RAQM)
    if var: f.set_variation_by_name(var)
    return f
cairo = lambda s, v='Black': font('Cairo', s, v)
bebas = lambda s: font('Bebas', s)
mont = lambda s: font('Montserrat', s, 'Bold')

def text_img(s, f, fill, rtl=False, glow=None, shadow=True):
    kw = {'direction': 'rtl', 'language': 'ar'} if rtl else {}
    pad = 50; l, t, r, b = f.getbbox(s, **kw)
    im = Image.new('RGBA', (r - l + pad * 2, b - t + pad * 2))
    ImageDraw.Draw(im).text((pad - l, pad - t), s, font=f, fill=fill, **kw)
    out = Image.new('RGBA', im.size)
    if shadow:
        sh = Image.new('RGBA', im.size); sh.putalpha(im.getchannel('A').point(lambda v: v * 0.75))
        out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)), (0, 6))
    if glow:
        g = Image.new('RGBA', im.size, glow[:3] + (0,)); g.putalpha(im.getchannel('A').point(lambda v: v * glow[3] / 255))
        out.alpha_composite(g.filter(ImageFilter.GaussianBlur(24)))
    out.alpha_composite(im); return out

def ease(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3
def back(x):
    x = min(max(x, 0), 1); c = 1.70158; return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2

def put(frame, im, cx, cy, alpha=1.0, scale=1.0):
    if alpha <= 0.01 or scale <= 0.01: return
    if abs(scale - 1) > 0.005: im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
    if alpha < 0.999: im = im.copy(); im.putalpha(im.getchannel('A').point(lambda v: int(v * alpha)))
    frame.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

# ---------- overlay pieces ----------
def tag(name, price, sale=False):
    t1 = text_img(name, cairo(54), CREAM, rtl=True, shadow=False)
    t2 = text_img(price, bebas(96), YEL if sale else CREAM, shadow=False)
    t3 = text_img('/lb', mont(28), MUTED, shadow=False)
    w = t1.width + t2.width + t3.width - 250; h = 140
    im = Image.new('RGBA', (w + 60, h + 50)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 40, w + 59, h + 40), 26, fill=(58, 13, 9, 235) if sale else (13, 9, 7, 225), outline=RED if sale else GOLD, width=5)
    x = 22; im.alpha_composite(t3, (x - 44, 48)); x += t3.width - 96
    im.alpha_composite(t2, (x - 44, 20)); x += t2.width - 84
    im.alpha_composite(t1, (x - 30, 24))
    if sale:
        s = text_img('عرض · SALE', cairo(30), (255, 255, 255), rtl=True, shadow=False)
        p = Image.new('RGBA', (s.width - 50, 56)); ImageDraw.Draw(p).rounded_rectangle((0, 0, p.width - 1, 55), 28, fill=RED)
        p.alpha_composite(s, ((p.width - s.width) // 2, (56 - s.height) // 2)); im.alpha_composite(p, (im.width - p.width - 16, 10))
    return im

def ribbon(ar, en):
    t = text_img(ar, cairo(66), (255, 255, 255), rtl=True, shadow=False)
    e = text_img(en, bebas(40), YEL, shadow=False)
    w = t.width + e.width - 110; h = 110
    im = Image.new('RGBA', (w + 90, h + 14)); d = ImageDraw.Draw(im)
    d.polygon([(0, 0), (w + 90, 0), (w + 90, h), (0, h), (36, h / 2)], fill=RED)
    d.rectangle((0, h, w + 90, h + 10), fill=(92, 15, 11))
    im.alpha_composite(e, (40, (h - e.height) // 2 + 2)); im.alpha_composite(t, (40 + e.width - 70, (h - t.height) // 2 - 4))
    return im

LOGO = text_img('كشكي', cairo(260), YEL, rtl=True, glow=RED + (210,))
LOGO_SM = text_img('كشكي', cairo(84), YEL, rtl=True, glow=RED + (160,))
SUB = text_img('لحوم حلال طازجة يومياً', cairo(70), CREAM, rtl=True)
SUB_EN = text_img('FRESH HALAL MEAT  ·  EVERY DAY', mont(34), GOLD)
CATS = text_img('عجل · بقري · غنم · ماعز · دجاج · متبّلات', cairo(48, 'Bold'), GOLD, rtl=True)
BEST = text_img('من أفضل اللحوم', cairo(84), CREAM, rtl=True, glow=RED + (150,))
def pill(s):
    t = text_img(s, cairo(56), (255, 255, 255), rtl=True, shadow=False)
    p = Image.new('RGBA', (t.width + 20, 116)); ImageDraw.Draw(p).rounded_rectangle((0, 0, p.width - 1, 115), 58, fill=RED)
    p.alpha_composite(t, ((p.width - t.width) // 2, (116 - t.height) // 2)); return p
CTA = pill('يلا على كشكي!')
HALAL = None
def halal_seal(d=150):
    S = 3; im = Image.new('RGBA', (d * S, d * S)); dr = ImageDraw.Draw(im); c = d * S / 2
    pts = []
    for i in range(48):
        r = (d * S / 2 - 2) if i % 2 == 0 else (d * S / 2 * 0.88); a = math.pi * i / 24
        pts.append((c + r * math.cos(a), c + r * math.sin(a)))
    dr.polygon(pts, fill=GOLD); im = im.resize((d, d), Image.LANCZOS)
    t = text_img('حلال', cairo(44), INK, rtl=True, shadow=False); im.alpha_composite(t, ((d - t.width) // 2, (d - t.height) // 2 - 12))
    e = text_img('HALAL', bebas(26), INK, shadow=False); im.alpha_composite(e, ((d - e.width) // 2, (d - e.height) // 2 + 28))
    return im
HALAL = halal_seal()

# dark gradient bg for title cards
yy, xx = np.mgrid[0:H, 0:W]
rr = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H * 0.45) / H) ** 2); vv = np.clip(1 - rr * 1.25, 0, 1)[..., None]
BG = Image.fromarray(np.clip(np.array((22, 14, 11), float) * (0.55 + 0.8 * vv) + np.array([90, 20, 8]) * vv ** 3, 0, 255).astype(np.uint8)).convert('RGBA')

# ---------- sources ----------
def load_photo(path, box, pink=True):
    im = Image.open(path).convert('RGB').crop(box)
    a = np.asarray(im).astype(float)
    if pink: a[..., 2] *= 0.80; a[..., 1] *= 1.05
    im = Image.fromarray(a.clip(0, 255).astype('uint8'))
    im = ImageEnhance.Contrast(im).enhance(1.12); im = ImageEnhance.Color(im).enhance(1.08)
    return ImageOps.fit(im, (int(W * 1.15), int(H * 1.15)), Image.LANCZOS)

def video_frames(path, start, dur, pink=True):
    cmd = ['ffmpeg', '-v', 'error', '-ss', str(start), '-t', str(dur), '-i', path,
           '-vf', f'fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-']
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE); n = W * H * 3
    while True:
        buf = p.stdout.read(n)
        if len(buf) < n: break
        a = np.frombuffer(buf, np.uint8).reshape(H, W, 3).astype(np.float32)
        if pink: a[..., 2] *= 0.82; a[..., 1] *= 1.04
        yield Image.fromarray(a.clip(0, 255).astype(np.uint8))
    p.wait()

# ---------- segments ----------
# kind, source, duration, section ribbon, tags [(name, price, sale)]
SEGS = [
 ('title_in', None, 4.0, None, []),
 # farm intro (stock clips in broll/, see broll/CREDITS.txt) – animals moving and eating on green pasture
 ('video', (f'{HERE}/broll/sheep_close.mp4', 0.0), 4.5, ('من المزرعة لين بيتك', 'FARM TO TABLE'), [], False),
 ('video', (f'{HERE}/broll/cow_eating_close.mp4', 0.0), 4.5, ('أبقار ترعى على الطبيعة', 'GRAZING ON OPEN PASTURE'), [], False),
 ('video', (f'{HERE}/broll/cows_hay.mp4', 0.0), 4.5, ('تتغذى على البرسيم', 'FED ON ALFALFA & HAY'), [], False),
 ('video', (f'{UP}/dd0c97dc-IMG_0219.mov', 2.0), 4.5, ('من المزرعة مباشرة', 'STRAIGHT FROM THE FARM'), [], False),
 ('photo', (f'{UP}/05e6b31f-image.jpg', (0, 480, 1500, 1324)), 4.0, ('غنم طازج', 'FRESH LAMB'), [], False),
 ('photo', (f'{UP}/ec9c5f0d-image.jpg', (0, 500, 1125, 1133)), 4.0, ('عجول مختارة', 'SELECTED CATTLE'), [], False),
 ('video', (f'{HERE}/broll/white_chickens_feeding.mp4', 0.0), 4.5, ('دجاج من مزارع كندا', 'CANADIAN FARM CHICKEN'), [], False),
 ('video', (f'{UP}/f54c8ff6-IMG_1564.mov', 3.0), 4.5, ('عجل وبقري', 'VEAL & BEEF'), []),
 ('photo', (f'{UP}/44ac7e94-image.jpg', (0, 0, 1512, 900)), 4.0, ('عجل وبقري', 'VEAL & BEEF'), [('ستيك ستربلوين', '$14.49', 1)]),
 ('photo', (f'{UP}/5071876d-image.jpg', (0, 40, 1700, 1000)), 4.0, ('عجل وبقري', 'VEAL & BEEF'), [('ستيك ريب', '$9.99', 1), ('ستيك ريب بالعظم', '$7.99', 1)]),
 ('photo', (f'{UP}/25bcd118-image.jpg', (0, 420, 1500, 1264)), 4.0, ('نقانق طازجة', 'FRESH SAUSAGES'), [], False),
 ('photo', (f'{UP}/cf06db3a-image.jpg', (0, 260, 1500, 1104)), 4.0, ('كفتة متبّلة', 'SEASONED KOFTA'), [], False),
 ('video', (f'{HERE}/broll/chicken_leg_quarters.mp4', 0.0), 4.0, ('أرباع دجاج', 'LEG QUARTERS'), [], False),
 ('video', (f'{HERE}/broll/chicken_drumsticks.mp4', 0.0), 4.0, ('دبابيس وأفخاذ', 'DRUMSTICKS & THIGHS'), [], False),
 ('video', (f'{HERE}/broll/chicken_breast.mp4', 0.0), 3.5, ('صدور دجاج', 'CHICKEN BREAST'), [], False),
 ('video', (f'{UP}/ce006880-IMG_2013.mov', 1.0), 4.0, ('دجاج متبّل', 'MARINATED'), [('دجاج متبّل بالعظم', '$3.99', 0)], False),
 ('video', (f'{UP}/1f983b78-IMG_2014.mov', 0.0), 4.0, ('دجاج متبّل', 'MARINATED'), [('متبّل بدون عظم', '$8.49', 0)], False),
 ('video', (f'{UP}/0beabd04-IMG_9767.mov', 12.0), 4.5, ('جاهز للشوي', 'READY TO GRILL'), [], False),
 ('photo', (f'{UP}/4f1a9e60-image.jpg', (0, 640, 1500, 1484)), 4.0, ('مشاوي على الفحم', 'BBQ SKEWERS'), [], False),
 ('title_out', None, 7.0, None, []),
]

def overlay(f, t, dur, seg, idx):
    rib, tags = seg[3], seg[4]
    # bottom shade for legibility
    if rib or tags: f.alpha_composite(SHADE)
    if rib:
        r = RIBS[rib]; k = ease((t - 0.15) / 0.45); put(f, r, W - r.width / 2 + 40 + (1 - k) * r.width, 120, 1)
    put(f, LOGO_SM, 160, 110, 0.95); put(f, HALAL, 150, H - 130, 0.95, 0.8)
    n = len(tags)
    for j, tg in ([] if NO_PRICES else enumerate(TAGIMG[idx])):
        ts = 0.5 + j * 0.45; x = W - 80 - tg.width / 2 - j * 0 ; y = H - 150 - (n - 1 - j) * 175
        put(f, tg, x, y, ease((t - ts) / .2), back((t - ts) / .45))

SHADE = Image.new('RGBA', (W, H))
_g = np.zeros((H, W, 4), np.uint8); prof = np.clip((np.arange(H) - H * 0.45) / (H * 0.55), 0, 1) ** 1.5 * 190
_g[..., 3] = prof[:, None].astype(np.uint8); SHADE = Image.fromarray(_g, 'RGBA')
RIBS = {}; TAGIMG = {}
for i, s in enumerate(SEGS):
    if s[3] and s[3] not in RIBS: RIBS[s[3]] = ribbon(*s[3])
    TAGIMG[i] = [tag(*x) for x in s[4]]

def title_in(t, dur):
    f = BG.copy()
    k = back((t - 0.2) / 0.8); put(f, LOGO, W / 2, 420, ease((t - .2) / .3), 0.6 + 0.4 * k)
    k = ease((t - 1.0) / .6); put(f, SUB, W / 2, 640 + 30 * (1 - k), k)
    k = ease((t - 1.4) / .6); put(f, SUB_EN, W / 2, 730 + 30 * (1 - k), k)
    k = back((t - 1.8) / .5); put(f, HALAL, W / 2, 900, ease((t - 1.8) / .2), k)
    return f

def title_out(t, dur):
    f = BG.copy(); pulse = 1 + 0.02 * math.sin(t * math.pi * 2)
    k = back(t / .7); put(f, LOGO, W / 2, 330, ease(t / .3), k * pulse)
    k = ease((t - .6) / .6); put(f, BEST, W / 2, 560 + 30 * (1 - k), k)
    k = ease((t - 1.0) / .6); put(f, CATS, W / 2, 680 + 30 * (1 - k), k)
    k = ease((t - 1.3) / .6); put(f, SUB_EN, W / 2, 760 + 30 * (1 - k), k)
    k = back((t - 1.8) / .5); put(f, CTA, W / 2, 900, ease((t - 1.8) / .2), k)
    return f

def render_seg(i, seg, dur):
    out = f'{TMP}/seg{i:02d}.mp4'
    ff = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    N = int(round(dur * FPS)); kind = seg[0]
    pink = seg[5] if len(seg) > 5 else True
    if kind == 'photo':
        src = load_photo(seg[1][0], seg[1][1], pink); zin = i % 2 == 0
    frames = video_frames(seg[1][0], seg[1][1], dur + 0.2, pink) if kind == 'video' else None
    last = None
    for n in range(N):
        t = n / FPS
        if kind == 'title_in': f = title_in(t, dur)
        elif kind == 'title_out': f = title_out(t, dur)
        else:
            if kind == 'photo':
                p = t / dur; z = (1.0 + 0.12 * p) if zin else (1.12 - 0.12 * p)
                cw, ch = src.width / z / 1.15 * 1.0, src.height / z / 1.15
                cx = src.width / 2 + (p - 0.5) * 60 * (1 if zin else -1); cy = src.height / 2
                fr = src.crop((int(cx - cw / 2), int(cy - ch / 2), int(cx + cw / 2), int(cy + ch / 2))).resize((W, H), Image.BILINEAR)
            else:
                fr = next(frames, None) or last
            last = fr
            f = fr.convert('RGBA'); overlay(f, t, dur, seg, i)
        ff.stdin.write(f.convert('RGB').tobytes())
    ff.stdin.close(); ff.wait()
    return out

if __name__ == '__main__':
    target = float(sys.argv[1]) if len(sys.argv) > 1 else None
    base = sum(s[2] for s in SEGS) - XF * (len(SEGS) - 1)
    k = (target / base) if target else 1.0
    durs = [s[2] * k for s in SEGS]
    files = []
    for i, s in enumerate(SEGS):
        files.append(render_seg(i, s, durs[i])); print('seg', i, flush=True)
    # xfade chain
    inputs = sum([['-i', f] for f in files], [])
    chain, off, prev = [], 0, '0:v'
    for i in range(1, len(files)):
        off += durs[i - 1] - XF
        lab = f'v{i}'
        chain.append(f'[{prev}][{i}:v]xfade=transition={"slideleft" if i in (6, 11, 12, 13) else "fade"}:duration={XF}:offset={off:.3f}[{lab}]')
        prev = lab
    subprocess.run(['ffmpeg', '-y', '-v', 'error', *inputs, '-filter_complex', ';'.join(chain), '-map', f'[{prev}]',
                    '-c:v', 'libx264', '-preset', 'slow', '-crf', '19', '-pix_fmt', 'yuv420p', '-r', str(FPS), '-movflags', '+faststart',
                    'kashki_promo_noprices_nomusic.mp4' if NO_PRICES else 'kashki_promo_nomusic.mp4'], check=True)
    print('done', sum(durs) - XF * (len(durs) - 1))
