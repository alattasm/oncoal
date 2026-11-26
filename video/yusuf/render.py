"""Baby Yusuf - Bubble Color Song (1920x1080, 30 fps, 108 s). Original 2D animation.

Usage:  python3 render.py               -> yusuf_bubbles_nomusic.mp4, then mux with song.wav
        python3 render.py 3 20.5 ...    -> preview stills into $PREVIEW_DIR (default /tmp)
"""
import math, os, subprocess, sys
from functools import lru_cache
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS, DUR = 1920, 1080, 30, 108.0
BEAT = 0.5; BAR = 2.0
T_COL0, SEC, T_FIN, T_END = 8.0, 16.0, 88.0, 104.0
COLORS = [('RED', (238, 48, 62)), ('YELLOW', (255, 208, 30)), ('BLUE', (38, 112, 245)),
          ('GREEN', (58, 196, 78)), ('PURPLE', (160, 72, 222))]
EXTRA = [(255, 120, 190), (255, 150, 40), (40, 200, 220)]
ALLC = [c for _, c in COLORS] + EXTRA
HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, '..', 'fonts', 'Fredoka.ttf')


@lru_cache(None)
def font(size, var='Bold'):
    f = ImageFont.truetype(FONT, size); f.set_variation_by_name(var); return f


def clamp(x, a=0.0, b=1.0): return min(max(x, a), b)
def ease(x): x = clamp(x); return 1 - (1 - x) ** 3
def back(x):
    x = clamp(x); c = 2.2
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2
def smooth(x): x = clamp(x); return x * x * (3 - 2 * x)


def put(fr, im, cx, cy, alpha=1.0, scale=1.0, rot=0.0):
    if alpha <= 0.01 or scale <= 0.01: return
    if abs(scale - 1) > 0.005:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
    if abs(rot) > 0.05: im = im.rotate(rot, Image.BICUBIC, expand=True)
    if alpha < 0.99:
        im = im.copy(); im.putalpha(im.getchannel('A').point(lambda v: int(v * alpha)))
    fr.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


# ---------------------------------------------------------------- text
@lru_cache(None)
def glyph(ch, size, fill, stroke=None, shadow=True):
    f = font(size); stroke = stroke if stroke is not None else max(6, size // 11)
    pad = stroke + 30
    l, t, r, b = f.getbbox(ch, stroke_width=stroke)
    im = Image.new('RGBA', (r - l + pad * 2, b - t + pad * 2))
    d = ImageDraw.Draw(im)
    d.text((pad - l, pad - t), ch, font=f, fill=fill, stroke_width=stroke, stroke_fill=(255, 255, 255))
    # inner shine
    shine = Image.new('RGBA', im.size)
    ImageDraw.Draw(shine).text((pad - l, pad - t - size * 0.04), ch, font=f, fill=(255, 255, 255, 70))
    m = Image.new('L', im.size); ImageDraw.Draw(m).text((pad - l, pad - t), ch, font=f, fill=255)
    sa = np.minimum(np.array(shine.getchannel('A')), np.array(m)) * (np.arange(im.height)[:, None] < im.height * 0.48)
    shine.putalpha(Image.fromarray(sa.astype(np.uint8)))
    out = Image.new('RGBA', im.size)
    if shadow:
        sh = Image.new('RGBA', im.size, (20, 40, 90, 0)); sh.putalpha(im.getchannel('A').point(lambda v: int(v * 0.45)))
        out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)), (0, 0))
        out = out.transform(out.size, Image.AFFINE, (1, 0, -4, 0, 1, -8))
    out.alpha_composite(im); out.alpha_composite(shine)
    return out


def word(fr, s, cx, cy, size, colors, t_in, t, stagger=0.06, wobble=True, alpha=1.0, pulse=0.0):
    """Draw word letter by letter, letters pop in with bounce."""
    f = font(size); widths = [f.getlength(c) for c in s]
    total = sum(widths) + 4 * (len(s) - 1); x = cx - total / 2
    for i, ch in enumerate(s):
        w = widths[i]
        if ch != ' ':
            k = (t - t_in - i * stagger) / 0.45
            sc = back(k) * (1 + pulse)
            col = colors[i % len(colors)]
            dy = (-14 * math.sin(t * 5 + i * 0.9)) if wobble else 0
            rot = (4 * math.sin(t * 3.2 + i * 1.3)) if wobble else 0
            if k > 0: put(fr, glyph(ch, size, col), x + w / 2, cy + dy - (1 - ease(k)) * 60, alpha, sc, rot)
        x += w + 4


@lru_cache(None)
def plain(s, size, fill, stroke_fill=(255, 255, 255), stroke=None):
    f = font(size); stroke = stroke or max(5, size // 10); pad = stroke + 20
    l, t, r, b = f.getbbox(s, stroke_width=stroke)
    im = Image.new('RGBA', (r - l + pad * 2, b - t + pad * 2))
    ImageDraw.Draw(im).text((pad - l, pad - t), s, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
    sh = Image.new('RGBA', im.size, (20, 40, 90, 0)); sh.putalpha(im.getchannel('A').point(lambda v: int(v * 0.35)))
    out = Image.new('RGBA', im.size); out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(5)), (0, 0))
    out = out.transform(out.size, Image.AFFINE, (1, 0, -3, 0, 1, -6)); out.alpha_composite(im)
    return out


# ---------------------------------------------------------------- bubbles
@lru_cache(None)
def bubble(col, r, glossy=True):
    """Glossy toy-ball style bubble sprite of radius r."""
    s = 2 * r + 8; S = s * 2; R = r * 2
    y, x = np.mgrid[0:S, 0:S].astype(float); c0 = S / 2
    d = np.hypot(x - c0, y - c0) / R
    col = np.array(col, float)
    # shading: light from upper-left
    lx, ly = (x - c0 + R * 0.35) / R, (y - c0 + R * 0.4) / R
    shade = np.clip(1.28 - 0.42 * np.hypot(lx, ly), 0.72, 1.25)
    rgb = np.clip(col[None, None] * shade[..., None] + (shade[..., None] - 1).clip(0) * 255, 0, 255)
    rim = np.clip((d - 0.82) / 0.18, 0, 1)[..., None]
    rgb = rgb * (1 - 0.22 * rim)
    a = np.clip((1 - d) * R / 1.5, 0, 1)
    if glossy:
        alpha = a * 0.93
    else:   # soap: transparent centre, coloured rim
        alpha = a * (0.35 + 0.6 * np.clip((d - 0.55) / 0.45, 0, 1))
    # highlights
    hx, hy = (x - (c0 - R * 0.38)) / (R * 0.28), (y - (c0 - R * 0.42)) / (R * 0.18)
    hl = np.clip(1 - np.hypot(hx, hy), 0, 1) ** 0.6
    hx2, hy2 = (x - (c0 + R * 0.45)) / (R * 0.1), (y - (c0 + R * 0.42)) / (R * 0.1)
    hl2 = np.clip(1 - np.hypot(hx2, hy2), 0, 1) * 0.7
    h = np.maximum(hl, hl2)[..., None]
    rgb = rgb * (1 - h) + 255 * h
    alpha = np.maximum(alpha, np.maximum(hl, hl2) * a)
    im = Image.fromarray(np.dstack([rgb, alpha * 255]).astype(np.uint8), 'RGBA')
    return im.resize((s, s), Image.LANCZOS)


def draw_bubble(fr, col, x, y, r, glossy=True, alpha=1.0):
    r = int(round(max(r, 3) / 2) * 2)
    put(fr, bubble(col, r, glossy), x, y, alpha)


def pop_fx(d, x, y, r, k, col):
    """k in 0..1: ring + droplets."""
    a = int(255 * (1 - k))
    rr = r * (1 + 0.8 * k)
    d.ellipse([x - rr, y - rr, x + rr, y + rr], outline=col + (a,), width=max(2, int(6 * (1 - k))))
    for j in range(8):
        ang = j * math.pi / 4 + 0.3
        dist = r * (1.1 + 1.4 * k); dr = max(2, r * 0.16 * (1 - k))
        px, py = x + math.cos(ang) * dist, y + math.sin(ang) * dist
        d.ellipse([px - dr, py - dr, px + dr, py + dr], fill=(255, 255, 255, a))


# ---------------------------------------------------------------- scene assets
def build_background():
    bg = Image.new('RGBA', (W, H))
    top, bot = np.array([70, 160, 245]), np.array([175, 225, 255])
    g = np.linspace(0, 1, H)[:, None] ** 0.9
    sky = (top * (1 - g) + bot * g)[:, None, :].repeat(W, 1)
    bg = Image.fromarray(np.dstack([sky, np.full((H, W), 255)]).astype(np.uint8), 'RGBA')
    d = ImageDraw.Draw(bg)
    xs = np.arange(0, W + 1, 8)
    # far hills
    yb = 720 + 40 * np.sin(xs / 260 + 1) + 25 * np.sin(xs / 120)
    d.polygon([(0, H)] + list(zip(xs, yb)) + [(W, H)], fill=(130, 205, 110))
    # little houses on far hills
    for hx, hc in [(980, (255, 170, 120)), (1120, (255, 220, 140)), (240, (180, 200, 255))]:
        hy = 720 + 40 * math.sin(hx / 260 + 1) + 25 * math.sin(hx / 120) + 6
        d.rectangle([hx - 28, hy - 40, hx + 28, hy], fill=hc, outline=(90, 70, 60), width=3)
        d.polygon([(hx - 38, hy - 38), (hx, hy - 72), (hx + 38, hy - 38)], fill=(220, 80, 70), outline=(90, 50, 40))
        d.rectangle([hx - 8, hy - 22, hx + 8, hy], fill=(120, 80, 50))
    # near hill / ground
    yn = 830 + 30 * np.sin(xs / 330 + 2.2) + 12 * np.sin(xs / 90)
    d.polygon([(0, H)] + list(zip(xs, yn)) + [(W, H)], fill=(84, 182, 72))
    d.line(list(zip(xs, yn)), fill=(60, 150, 55), width=6)
    rng = np.random.default_rng(3)
    for _ in range(140):
        x = rng.uniform(0, W); y0 = 830 + 30 * math.sin(x / 330 + 2.2) + 12 * math.sin(x / 90)
        y = rng.uniform(y0 + 25, H)
        if rng.random() < 0.45:
            c = [(255, 255, 255), (255, 220, 60), (255, 130, 170), (190, 140, 255)][rng.integers(4)]
            for k in range(5):
                a = k * 2 * math.pi / 5
                d.ellipse([x + 7 * math.cos(a) - 5, y + 7 * math.sin(a) - 5, x + 7 * math.cos(a) + 5, y + 7 * math.sin(a) + 5], fill=c)
            d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(255, 190, 40))
        else:
            d.line([(x, y), (x - 4, y - 14)], fill=(60, 150, 55), width=3)
            d.line([(x, y), (x + 5, y - 12)], fill=(60, 150, 55), width=3)
    # tree trunk + branches (canopy is built by bubbles)
    tr = Image.new('RGBA', (W, H)); td = ImageDraw.Draw(tr)
    brown, dark = (150, 95, 55), (100, 60, 35)
    trunk = [(370, 900), (395, 700), (400, 560), (380, 470), (470, 470), (455, 560), (460, 700), (500, 900)]
    td.polygon(trunk, fill=brown, outline=dark)
    for (x0, y0, x1, y1, w) in [(425, 520, 250, 330, 34), (425, 520, 620, 310, 34), (425, 480, 430, 210, 32),
                                (300, 380, 190, 300, 18), (560, 360, 680, 270, 18), (430, 300, 340, 190, 16),
                                (430, 300, 520, 180, 16), (250, 330, 220, 230, 14), (620, 310, 640, 210, 14)]:
        td.line([(x0, y0), (x1, y1)], fill=dark, width=w + 8)
        td.line([(x0, y0), (x1, y1)], fill=brown, width=w)
        td.ellipse([x1 - w / 2, y1 - w / 2, x1 + w / 2, y1 + w / 2], fill=brown)
    sh = Image.new('RGBA', (W, H)); ImageDraw.Draw(sh).ellipse([280, 880, 600, 925], fill=(30, 90, 30, 90))
    bg.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)))
    bg.alpha_composite(tr)
    return bg


def build_cloud(seed, w):
    rng = np.random.default_rng(seed)
    im = Image.new('RGBA', (w + 80, int(w * 0.85) + 80)); d = ImageDraw.Draw(im)
    base = im.height - 60
    blobs = [(w * f, base - rng.uniform(0.15, 0.4) * w * (1 - abs(f - 0.5)), w * rng.uniform(0.16, 0.24)) for f in np.linspace(0.18, 0.82, 5)]
    for x, y, r in blobs:
        d.ellipse([40 + x - r, y - r, 40 + x + r, y + r], fill=(255, 255, 255, 255))
    d.rounded_rectangle([40 + w * 0.05, base - w * 0.16, 40 + w * 0.95, base + 4], radius=int(w * 0.08), fill=(255, 255, 255, 255))
    a = np.array(im.getchannel('A')).astype(float)
    shade = np.linspace(1, 0.86, im.height)[:, None]
    rgb = np.dstack([255 * shade, 255 * shade, 255 * (0.95 + 0.05 * shade)] ).repeat(im.width, 1) if False else None
    out = Image.new('RGBA', im.size, (236, 244, 255, 0)); out.putalpha(im.getchannel('A'))
    top = Image.new('RGBA', im.size, (255, 255, 255, 0))
    m = im.getchannel('A').transform(im.size, Image.AFFINE, (1, 0, 0, 0, 1, 10))
    top.putalpha(m); out.alpha_composite(top)
    return out.filter(ImageFilter.GaussianBlur(1.2))


def build_sun():
    S = 360; im = Image.new('RGBA', (S, S)); d = ImageDraw.Draw(im); c = S / 2
    for k in range(12):
        a = k * math.pi / 6
        pts = [(c + 120 * math.cos(a - 0.13), c + 120 * math.sin(a - 0.13)), (c + 175 * math.cos(a), c + 175 * math.sin(a)),
               (c + 120 * math.cos(a + 0.13), c + 120 * math.sin(a + 0.13))]
        d.polygon(pts, fill=(255, 200, 40))
    return im


def build_sun_face():
    S = 260; im = Image.new('RGBA', (S, S)); d = ImageDraw.Draw(im); c = S / 2
    d.ellipse([c - 105, c - 105, c + 105, c + 105], fill=(255, 214, 50), outline=(245, 170, 30), width=6)
    d.ellipse([c - 80, c - 95, c + 30, c - 20], fill=(255, 236, 120))
    for ex in (-38, 38):
        d.ellipse([c + ex - 11, c - 30, c + ex + 11, c + 2], fill=(70, 40, 20))
        d.ellipse([c + ex - 4, c - 26, c + ex + 3, c - 18], fill=(255, 255, 255))
    d.arc([c - 45, c - 15, c + 45, c + 50], 20, 160, fill=(150, 60, 20), width=8)
    for ex in (-62, 62):
        d.ellipse([c + ex - 16, c + 8, c + ex + 16, c + 26], fill=(255, 150, 110))
    return im


def build_yusuf(height=860):
    im = Image.open(os.path.join(HERE, 'yusuf_clean.png')).convert('RGBA')
    sc = height / im.height
    im = im.resize((int(im.width * sc), height), Image.LANCZOS)
    # soft white outline sticker effect
    a = im.getchannel('A')
    halo = Image.new('RGBA', im.size, (255, 255, 255, 0)); halo.putalpha(a.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(1)))
    out = Image.new('RGBA', im.size); out.alpha_composite(halo); out.alpha_composite(im)
    return out, sc


def build_wand():
    """Bubble wand: stick + ring. Returns sprite and ring centre offset."""
    im = Image.new('RGBA', (220, 300)); d = ImageDraw.Draw(im)
    d.line([(60, 290), (140, 110)], fill=(90, 60, 160), width=18)
    d.line([(60, 290), (140, 110)], fill=(170, 120, 255), width=12)
    d.ellipse([105, 15, 205, 115], outline=(90, 60, 160), width=20)
    d.ellipse([105, 15, 205, 115], outline=(255, 120, 200), width=13)
    return im


# ---------------------------------------------------------------- choreography
YH = 860
YX, YBASE = 1530, 1110         # centre-x of Yusuf, bottom y


def yusuf_pose(t):
    intro = back((t - 0.8) / 1.0)
    x = YX + (1 - intro) * 700
    bob = abs(math.sin(math.pi * t / BEAT)) * 20
    rot = math.sin(math.pi * t / (2 * BEAT)) * 3.0
    if t > T_END: bob *= 0.6
    return x, YBASE - bob, rot


def wand_tip(t, sc, ys):
    """Ring centre in frame coords (wand is held in Yusuf's raised hand, image-right)."""
    x, yb, rot = yusuf_pose(t)
    hx, hy = 770 * sc, 450 * sc                       # hand in scaled sprite coords
    w_im, h_im = ys.width, ys.height
    # offset from sprite centre, rotated about bottom-centre pivot
    px, py = hx - w_im / 2, hy - h_im
    a = math.radians(rot)
    rx = px * math.cos(a) + py * math.sin(a); ry = -px * math.sin(a) + py * math.cos(a)
    hand = (x + rx, yb + ry)
    return hand, (hand[0] + 95, hand[1] - 185)


def section_of(t):
    if T_COL0 <= t < T_FIN: return int((t - T_COL0) // SEC)
    return None


def make_particles():
    rng = np.random.default_rng(11)
    # canopy targets: Poisson-ish sampling inside ellipse
    targets = []
    cx, cy, rx, ry = 430, 330, 330, 230
    tries = 0
    while len(targets) < 150 and tries < 20000:
        tries += 1
        u, v = rng.uniform(-1, 1, 2)
        if u * u + v * v > 1: continue
        p = (cx + u * rx, cy + v * ry)
        r = rng.uniform(34, 62) * (1 - 0.25 * (u * u + v * v))
        if all(math.hypot(p[0] - q[0], p[1] - q[1]) > 0.62 * (r + q[2]) for q in targets):
            targets.append((p[0], p[1], r))
    rng.shuffle(targets)
    per = len(targets) // 5
    stuck, free, bigpops = [], [], []
    for i, (name, col) in enumerate(COLORS):
        t0 = T_COL0 + i * SEC
        tg = sorted(targets[i * per:(i + 1) * per], key=lambda q: -q[1])   # fill from bottom up
        launch = np.linspace(t0 + 0.4, t0 + 9.5, len(tg)) + rng.uniform(-0.1, 0.1, len(tg))
        for (x, y, r), tl in zip(tg, launch):
            stuck.append(dict(t=tl, x=x, y=y, r=r, col=col, ph=rng.uniform(0, 6.28), fly=rng.uniform(1.2, 1.7)))
        for k in range(46):
            ts = t0 + rng.uniform(0, 15.2)
            free.append(dict(t=ts, life=rng.uniform(2.6, 4.6), r=rng.uniform(14, 40), col=col, vx=-rng.uniform(140, 420),
                             vy=-rng.uniform(60, 220), ph=rng.uniform(0, 6.28), glossy=rng.random() < 0.55))
        # three big bubbles popping on the "Pop pop pop" beats
        for k in range(3):
            bigpops.append(dict(t_in=t0 + 8.2 + k * 0.25, t_pop=t0 + 10 + k * BEAT, x=820 + k * 200, y=520 - 60 * (k % 2), r=70, col=col))
    # finale: rainbow storm
    for k in range(260):
        ts = T_FIN + rng.uniform(-0.2, 16)
        col = ALLC[rng.integers(len(ALLC))]
        src = 'wand' if rng.random() < 0.5 else 'ground'
        free.append(dict(t=ts, life=rng.uniform(2.5, 5.0), r=rng.uniform(16, 46), col=col, vx=-rng.uniform(80, 420) if src == 'wand' else rng.uniform(-60, 60),
                         vy=-rng.uniform(80, 260), ph=rng.uniform(0, 6.28), glossy=rng.random() < 0.6, src=src, gx=rng.uniform(80, 1300)))
    return stuck, free, bigpops


def make_confetti():
    rng = np.random.default_rng(5); out = []
    bursts = [T_COL0 + i * SEC for i in range(5)] + [T_FIN, T_FIN + 4, T_END]
    for tb in bursts:
        for k in range(150):
            out.append(dict(t=tb + rng.uniform(0, 0.25), x=rng.uniform(-100, W + 100), y=-rng.uniform(20, 300),
                            vx=rng.uniform(-60, 60), vy=rng.uniform(260, 480), w=rng.uniform(22, 36), h=rng.uniform(11, 17),
                            spin=rng.uniform(3, 9), ph=rng.uniform(0, 6.28), col=ALLC[rng.integers(len(ALLC))]))
    return out


def draw_confetti(d, t):
    for c in G['conf']:
        a = t - c['t']
        if a < 0 or a > 3.2: continue
        x = c['x'] + c['vx'] * a + 40 * math.sin(a * 3 + c['ph']); y = c['y'] + c['vy'] * a
        if y > H + 30: continue
        ang = c['ph'] + c['spin'] * a; sq = abs(math.cos(a * c['spin'] * 0.7 + c['ph']))
        w, h = c['w'] / 2, c['h'] / 2 * (0.3 + 0.7 * sq)
        ca, sa = math.cos(ang), math.sin(ang)
        pts = [(x + px * ca - py * sa, y + px * sa + py * ca) for px, py in ((-w, -h), (w, -h), (w, h), (-w, h))]
        alpha = int(255 * clamp((3.2 - a) / 0.6))
        d.polygon(pts, fill=c['col'] + (alpha,))


def star(d, x, y, r, col, rot=0.0, alpha=255):
    pts = []
    for k in range(10):
        rr = r if k % 2 == 0 else r * 0.45
        a = rot + k * math.pi / 5 - math.pi / 2
        pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    d.polygon(pts, fill=col + (alpha,), outline=(255, 255, 255, alpha))


# ---------------------------------------------------------------- frame
G = {}


def init():
    G['bg'] = build_background()
    G['clouds'] = [(build_cloud(s, w), x0, y, sp) for s, w, x0, y, sp in
                   [(1, 300, 200, 120, 14), (2, 220, 1100, 70, 10), (3, 360, 1500, 190, 18), (4, 200, 700, 260, 12)]]
    G['sun'] = build_sun(); G['sunface'] = build_sun_face()
    G['yusuf'], G['ysc'] = build_yusuf(YH)
    G['wand'] = build_wand()
    G['stuck'], G['free'], G['big'] = make_particles()
    G['conf'] = make_confetti()


def emit_pos(t):
    return wand_tip(t, G['ysc'], G['yusuf'])[1]


def render(t):
    fr = G['bg'].copy()
    sec = section_of(t)
    # clouds
    for im, x0, y, sp in G['clouds']:
        x = (x0 + sp * t) % (W + 500) - 250
        put(fr, im, x, y + 6 * math.sin(t * 0.7 + x0))
    # sun
    put(fr, G['sun'], 1000, 135, 1, 1 + 0.03 * math.sin(t * 4), rot=-t * 18)
    put(fr, G['sunface'], 1000, 135, 1, 1 + 0.02 * math.sin(math.pi * t / BEAT))
    fx = Image.new('RGBA', (W, H)); fd = ImageDraw.Draw(fx)

    # stuck bubbles (fly from wand to tree, then stay)
    for b in G['stuck']:
        if t < b['t']: continue
        k = (t - b['t']) / b['fly']
        if k < 1:
            sx, sy = emit_pos(b['t'])
            cxp, cyp = (sx + b['x']) / 2 + 120, min(sy, b['y']) - 260
            e = smooth(k)
            x = (1 - e) ** 2 * sx + 2 * (1 - e) * e * cxp + e * e * b['x']
            y = (1 - e) ** 2 * sy + 2 * (1 - e) * e * cyp + e * e * b['y']
            r = b['r'] * (0.35 + 0.65 * e)
            draw_bubble(fr, b['col'], x, y, r)
        else:
            j = t - b['t'] - b['fly']
            land = 1 + 0.18 * math.exp(-j * 6) * math.sin(j * 25)
            x = b['x'] + 3 * math.sin(t * 1.6 + b['ph']); y = b['y'] + 3 * math.cos(t * 1.3 + b['ph'])
            r = b['r'] * land
            if t > T_END + 1.2:      # final pop of the whole tree
                kk = (t - (T_END + 1.2 + (b['ph'] / 6.28) * 1.5)) / 0.3
                if kk > 1: continue
                if kk > 0: pop_fx(fd, x, y, b['r'], kk, b['col']); continue
            draw_bubble(fr, b['col'], x, y, r)

    # free floating bubbles
    for b in G['free']:
        a = t - b['t']
        if a < 0 or a > b['life'] + 0.3: continue
        if b.get('src') == 'ground':
            sx, sy = b['gx'], 900
        else:
            sx, sy = emit_pos(b['t'])
        x = sx + b['vx'] * a + 30 * math.sin(a * 2.2 + b['ph'])
        y = sy + b['vy'] * a + 12 * math.sin(a * 3 + b['ph']) - 10 * a * a
        if a <= b['life']:
            r = b['r'] * min(1, 0.3 + a * 2.5)
            draw_bubble(fr, b['col'], x, y, r, b['glossy'], alpha=0.95)
        else:
            pop_fx(fd, x, y, b['r'], (a - b['life']) / 0.3, b['col'])

    # big bubbles on "pop pop pop"
    for b in G['big']:
        if t < b['t_in'] or t > b['t_pop'] + 0.45: continue
        if t < b['t_pop']:
            k = back((t - b['t_in']) / 0.5)
            x, y = b['x'], b['y'] + 10 * math.sin(t * 3 + b['x'])
            draw_bubble(fr, b['col'], x, y, b['r'] * k * (1 + 0.04 * math.sin(t * 9)))
        else:
            k = (t - b['t_pop']) / 0.45
            pop_fx(fd, b['x'], b['y'], b['r'], k, b['col'])
            put(fx, plain('POP!', 74, b['col']), b['x'], b['y'], 1 - clamp((k - 0.6) / 0.4), back(k / 0.5), rot=-10 + 10 * (b['x'] % 3))
    fr.alpha_composite(fx)

    # Yusuf + wand
    x, yb, rot = yusuf_pose(t)
    ys = G['yusuf']
    hand, tip = wand_tip(t, G['ysc'], ys)
    if rot:
        big = Image.new('RGBA', (ys.width, ys.height * 2)); big.alpha_composite(ys, (0, 0))
        big = big.rotate(rot, Image.BICUBIC, center=(ys.width / 2, ys.height))
        fr.alpha_composite(big, (int(x - ys.width / 2), int(yb - ys.height)))
    else:
        fr.alpha_composite(ys, (int(x - ys.width / 2), int(yb - ys.height)))
    wa = rot + 8 * math.sin(math.pi * t / BEAT)
    put(fr, G['wand'].rotate(wa, Image.BICUBIC, expand=True), hand[0] + 45, hand[1] - 90)

    # ---------------- text layers
    if t < 8.2:
        a = 1 - clamp((t - 7.4) / 0.6)
        word(fr, 'BABY YUSUF', 760, 300, 150, ALLC[:5] + [EXTRA[0], EXTRA[1]] * 3, 0.3, t, 0.09, alpha=a)
        if t > 2.2:
            put(fr, plain('Bubble Color Song', 64, (255, 255, 255), (40, 110, 230)), 760, 470, a, back((t - 2.2) / 0.5))
    elif t < T_FIN:
        i = sec; name, col = COLORS[i]; t0 = T_COL0 + i * SEC
        a = 1 - clamp((t - (t0 + SEC - 0.5)) / 0.4)
        pulse = 0.18 * math.exp(-max(0, t - (t0 + 12)) * 5) if t >= t0 + 12 else 0
        beat_p = 0.06 * math.exp(-((t - T_COL0) % BEAT) * 9)
        word(fr, name, 800, 960, 190, [col], t0 + 0.05, t, 0.07, alpha=a, pulse=pulse + beat_p)
        sl = Image.new('RGBA', (W, H)); sd = ImageDraw.Draw(sl)
        for k in range(6):
            ang = k * math.pi / 3 + t * 0.8
            tw = 0.5 + 0.5 * math.sin(t * 6 + k * 1.7)
            if t > t0 + 0.6:
                star(sd, 800 + 330 * math.cos(ang), 950 + 95 * math.sin(ang), 14 + 14 * tw, (255, 230, 80), t * 2 + k, int(255 * a * (0.4 + 0.6 * tw)))
        fr.alpha_composite(sl)
        if t0 + 14 <= t < t0 + SEC:
            k = (t - t0 - 14) / 0.4
            put(fr, plain('What color is next?', 58, (255, 255, 255), (40, 110, 230)), 800, 620,
                1 - clamp((t - t0 - 15.5) / 0.4), back(k), rot=3 * math.sin(t * 4))
    elif t < T_END:
        tf = t - T_FIN
        if tf < 7.8:
            word(fr, 'RAINBOW', 760, 900, 170, ALLC, 0.1 + T_FIN, t, 0.07, alpha=1 - clamp((tf - 7.4) / 0.4))
        if 4 <= tf < 8:
            put(fr, plain('Yay!', 150, (255, 120, 190)), 760, 560, 1 - clamp((tf - 7.5) / 0.5), back((tf - 4) / 0.5), rot=8 * math.sin(t * 5))
        if 8 <= tf < 12.5:
            for k, (name, col) in enumerate(COLORS):
                tk = T_FIN + 8 + k * 1.0
                if t >= tk:
                    put(fr, glyph(name[0], 150, col), 360 + k * 200, 900 + -12 * math.sin(t * 5 + k), 1 - clamp((tf - 12) / 0.5), back((t - tk) / 0.4))
                    put(fr, plain(name.capitalize(), 40, col), 360 + k * 200, 1020, 1 - clamp((tf - 12) / 0.5), back((t - tk) / 0.4))
        if tf >= 12.2:
            put(fr, plain('Bye bye, bubbles!', 96, (255, 255, 255), (40, 110, 230)), 760, 560, 1, back((tf - 12.2) / 0.5), rot=3 * math.sin(t * 3))
    else:
        word(fr, 'BABY YUSUF', 760, 360, 150, ALLC[:5] + [EXTRA[0], EXTRA[1]] * 3, T_END, t, 0.06)
        put(fr, plain('Bye bye!  See you soon!', 70, (255, 255, 255), (40, 110, 230)), 760, 540, 1, back((t - T_END - 0.8) / 0.5))
    # persistent corner logo after intro
    if 8.2 <= t < T_END:
        put(fr, logo(), 170, 70, smooth((t - 8.2) / 0.5) * 0.95)
    cl = Image.new('RGBA', (W, H)); draw_confetti(ImageDraw.Draw(cl), t); fr.alpha_composite(cl)
    # fade in / out
    out = fr.convert('RGB')
    if T_COL0 <= t < T_END + 0.5:
        z = 1 + 0.014 * math.exp(-((t - T_COL0) % BEAT) * 8)
        zw, zh = int(W * z), int(H * z)
        out = out.resize((zw, zh), Image.BILINEAR).crop(((zw - W) // 2, (zh - H) // 2, (zw - W) // 2 + W, (zh - H) // 2 + H))
    f = min(clamp(t / 0.5), clamp((DUR - t) / 0.8))
    if f < 1: out = Image.blend(Image.new('RGB', (W, H), (0, 0, 0)), out, f)
    return out


@lru_cache(None)
def logo():
    im = Image.new('RGBA', (320, 120)); x = 20
    for i, ch in enumerate('BABY YUSUF'):
        if ch == ' ': x += 16; continue
        g = glyph(ch, 44, (ALLC[:5] + [EXTRA[0], EXTRA[1]] * 3)[i], 6, False)
        im.alpha_composite(g, (int(x - 36), int(60 - g.height / 2)))
        x += font(44).getlength(ch) + 1
    return im


def work(i):
    if 'bg' not in G: init()
    return render(i / FPS).tobytes()


if __name__ == '__main__':
    os.chdir(HERE)
    if len(sys.argv) > 1:
        init(); od = os.environ.get('PREVIEW_DIR', '/tmp')
        for a in sys.argv[1:]:
            render(float(a)).save(f'{od}/yusuf_{a}.png'); print('saved', a)
        sys.exit()
    n = int(DUR * FPS)
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                           '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p', 'yusuf_bubbles_nomusic.mp4'],
                          stdin=subprocess.PIPE)
    with Pool(4) as p:
        for k, buf in enumerate(p.imap(work, range(n), chunksize=8)):
            ff.stdin.write(buf)
            if k % 300 == 0: print(f'{k}/{n}', flush=True)
    ff.stdin.close(); ff.wait()
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', 'yusuf_bubbles_nomusic.mp4', '-i', 'song.wav', '-c:v', 'copy', '-c:a', 'aac',
                    '-b:a', '192k', '-shortest', 'baby_yusuf_bubbles.mp4'], check=True)
    print('done -> baby_yusuf_bubbles.mp4')
