"""OnCoal story reel (1080x1920, 30 fps): a family of five's first visit, half lamb mandi / half grilled chicken platter.

Usage:  python3 story.py            -> renders oncoal_family_story_nomusic.mp4
        python3 story.py 3 12.5 ... -> saves preview stills to $PREVIEW_DIR (default /tmp)
Then:   VIDEO=oncoal_family_story_nomusic.mp4 ./mux.sh music_pro2.wav oncoal_family_story.mp4
"""
import math, os, subprocess, sys, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

W, H, FPS = 1080, 1920, 30
BG = (28, 18, 14)
ORANGE, GOLD, CREAM, MUTED = (236, 146, 70), (246, 196, 120), (246, 236, 222), (196, 176, 156)
INK = (40, 26, 20)

# scene timeline (start, end)
T_INTRO, T_DOOR, T_MENU, T_ORDER, T_PLATTER, T_TABLE, T_OUTRO = (0, 4), (4, 9.5), (9.5, 15), (15, 20), (20, 27), (27, 34), (34, 40)
DUR = T_OUTRO[1]


def font(name, size, var=None):
    f = ImageFont.truetype(f'fonts/{name}.ttf', size, layout_engine=ImageFont.Layout.RAQM)
    if var: f.set_variation_by_name(var)
    return f

cairo = lambda s, v='Bold': font('Cairo', s, v)
mont = lambda s: font('Montserrat', s, 'Bold')
bebas = lambda s: font('Bebas', s)


def text_img(s, f, fill, rtl=False, glow=None, shadow=True):
    kw = {'direction': 'rtl', 'language': 'ar'} if rtl else {}
    pad = 50
    l, t, r, b = f.getbbox(s, **kw)
    im = Image.new('RGBA', (r - l + pad * 2, b - t + pad * 2))
    ImageDraw.Draw(im).text((pad - l, pad - t), s, font=f, fill=fill, **kw)
    out = Image.new('RGBA', im.size)
    if shadow:
        sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); sh.putalpha(im.getchannel('A').point(lambda v: v * 0.7))
        out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)), (0, 6))
    if glow:
        g = Image.new('RGBA', im.size, glow[:3] + (0,)); g.putalpha(im.getchannel('A').point(lambda v: v * glow[3] / 255))
        out.alpha_composite(g.filter(ImageFilter.GaussianBlur(22)))
    out.alpha_composite(im)
    return out

ar = lambda s, size=64, fill=CREAM, v='Bold', glow=None: text_img(s, cairo(size, v), fill, rtl=True, glow=glow)
en = lambda s, size=40, fill=ORANGE: text_img(s, mont(size), fill)


def ease(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3
def back(x):
    x = min(max(x, 0), 1); c = 1.70158
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def put(frame, im, cx, cy, alpha=1.0, scale=1.0, rot=0):
    if alpha <= 0.01 or scale <= 0.01: return
    if rot: im = im.rotate(rot, Image.BICUBIC, expand=True)
    if abs(scale - 1) > 0.005:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
    if alpha < 0.999:
        im = im.copy(); im.putalpha(im.getchannel('A').point(lambda v: int(v * alpha)))
    frame.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


def grade(im):
    im = ImageEnhance.Color(im).enhance(1.25)
    im = ImageEnhance.Contrast(im).enhance(1.1)
    a = np.asarray(im).astype(np.float32); a[..., 0] *= 1.04; a[..., 2] *= 0.92
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

def load_dish(name, d):
    src = Image.open(f'assets/hd/{name}.png').convert('RGB')
    w, h = src.size; m = int(min(w, h) * 0.13)
    return grade(src.crop((m, m, w - m, h - m))).resize((d, d), Image.LANCZOS).filter(ImageFilter.UnsharpMask(2, 60, 2))

def circle_mask(d):
    m = Image.new('L', (d * 3, d * 3)); ImageDraw.Draw(m).ellipse((0, 0, d * 3 - 1, d * 3 - 1), fill=255)
    return m.resize((d, d), Image.LANCZOS)


# ---------- background + embers ----------
yy, xx = np.mgrid[0:H, 0:W]
r = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H * 0.45) / H) ** 2)
v = np.clip(1 - r * 1.3, 0, 1)[..., None]
bg = Image.fromarray(np.clip(np.array(BG, float) * (0.55 + 0.8 * v) + np.array([46, 20, 0]) * v ** 3, 0, 255).astype(np.uint8)).convert('RGBA')
eg = Image.new('L', (40, 40)); ImageDraw.Draw(eg).ellipse((14, 14, 26, 26), fill=255)
ember = Image.new('RGBA', (40, 40)); ember.paste(Image.new('RGBA', (40, 40), (255, 160, 70, 255)), mask=eg.filter(ImageFilter.GaussianBlur(5)))
ember_sizes = {s: ember.resize((s, s), Image.BILINEAR) for s in range(8, 41, 4)}
rng = np.random.default_rng(7)
EMB = [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(40, 140), rng.uniform(0.3, 1.0), rng.uniform(0, 6.28)) for _ in range(45)]

def embers(frame, t, k=0.7):
    for x0, y0, sp, sz, ph in EMB:
        y = (y0 - sp * t) % (H + 80) - 40
        x = x0 + 30 * math.sin(t * 0.8 + ph)
        a = (0.4 + 0.6 * abs(math.sin(t * 2 + ph))) * min(1, y / 400 + 0.2)
        put(frame, ember_sizes[min(8 + int(sz * 32) // 4 * 4, 40)], x, y, alpha=max(0, a) * k)


# ---------- family characters (flat illustration, drawn at 3x then downsampled) ----------
SKIN = [(198, 146, 108), (176, 124, 88), (214, 166, 126), (190, 136, 98), (205, 156, 116)]

def person(h, shirt, skin, hijab=None, hair=(34, 24, 20), upper=False):
    S = 3; hh = h * S; w = int(hh * 0.5); cx = w // 2
    im = Image.new('RGBA', (w, hh + 4 * S)); d = ImageDraw.Draw(im)
    r = hh * 0.12; hy = r + 2 * S
    body_top, body_bot = hy + r * 1.05, hh * (0.62 if not upper else 1.0)
    bw = hh * 0.17
    if not upper:  # legs
        lw = bw * 0.42
        d.rounded_rectangle((cx - bw * 0.9, body_bot - 20, cx - bw * 0.9 + lw * 2, hh), radius=lw, fill=(46, 40, 52))
        d.rounded_rectangle((cx + bw * 0.9 - lw * 2, body_bot - 20, cx + bw * 0.9, hh), radius=lw, fill=(46, 40, 52))
    if hijab:
        d.ellipse((cx - r * 1.35, hy - r * 1.3, cx + r * 1.35, hy + r * 1.45), fill=hijab)
        d.rounded_rectangle((cx - bw * 1.05, body_top - r * 0.2, cx + bw * 1.05, body_bot + (hh * 0.1 if not upper else 0)), radius=bw, fill=shirt)
        d.polygon([(cx - r * 1.25, hy + r * 0.4), (cx + r * 1.25, hy + r * 0.4), (cx + bw * 1.15, body_top + r * 0.9), (cx - bw * 1.15, body_top + r * 0.9)], fill=hijab)
        d.ellipse((cx - r * 0.82, hy - r * 0.85, cx + r * 0.82, hy + r * 0.95), fill=skin)
    else:
        d.rounded_rectangle((cx - bw, body_top, cx + bw, body_bot), radius=bw * 0.8, fill=shirt)
        d.ellipse((cx - r, hy - r, cx + r, hy + r), fill=skin)
        d.chord((cx - r * 1.04, hy - r * 1.08, cx + r * 1.04, hy + r * 0.7), 180, 360, fill=hair)
    # eyes + smile
    ey = hy + r * 0.05
    for sx in (-1, 1):
        d.ellipse((cx + sx * r * 0.36 - 3 * S, ey - 3 * S, cx + sx * r * 0.36 + 3 * S, ey + 3 * S), fill=(30, 20, 16))
    d.arc((cx - r * 0.38, hy + r * 0.05, cx + r * 0.38, hy + r * 0.62), 20, 160, fill=(120, 50, 40), width=int(2.5 * S))
    return im.resize((w // S, (hh + 4 * S) // S), Image.LANCZOS)

FAMILY_SPEC = [  # height, shirt, skin, hijab
    (560, (58, 92, 120), SKIN[0], None),          # dad
    (520, (120, 44, 52), SKIN[2], (70, 52, 80)),  # mom
    (430, (214, 142, 60), SKIN[4], None),         # teen
    (360, (70, 130, 96), SKIN[3], (220, 120, 120)),  # daughter
    (280, (236, 196, 90), SKIN[1], None),         # little one
]
WALKERS = [person(h, s, k, hj) for h, s, k, hj in FAMILY_SPEC]
SEATED = [person(int(h * 0.8), s, k, hj, upper=True) for h, s, k, hj in FAMILY_SPEC]


# ---------- static scene pieces ----------
# intro
i_kicker = en('A TRUE STORY FROM OUR TABLES', 34, GOLD)
i_t1 = ar('أول زيارة', 150, CREAM, 'Black', glow=ORANGE + (160,))
i_t2 = ar('عائلة من ٥ أفراد… أول مرة في اونكول', 56)
i_t3 = en('A family of five. Their first time at OnCoal.', 36, MUTED)
logo_ar = text_img('اونكول', font('Ruqaa', 120), ORANGE, rtl=True)

def caption(a, e):
    return ar(a, 66, CREAM, 'Black'), en(e, 38, GOLD)

# door
def make_door():
    w, h = 520, 900
    im = Image.new('RGBA', (w + 120, h + 160)); ox, oy = 60, 120
    glow = Image.new('L', im.size); ImageDraw.Draw(glow).rounded_rectangle((ox - 30, oy - 30, ox + w + 30, oy + h), radius=w // 2, fill=170)
    im.paste(Image.new('RGBA', im.size, ORANGE + (255,)), mask=glow.filter(ImageFilter.GaussianBlur(40)))
    inner = Image.new('RGBA', (w, h))
    g = np.linspace(0, 1, h)[:, None] * np.ones((1, w))
    col = np.stack([255 - 30 * g, 214 - 80 * g, 150 - 90 * g, np.full_like(g, 255)], -1).astype(np.uint8)
    inner = Image.fromarray(col, 'RGBA')
    m = Image.new('L', (w, h)); ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h + w), radius=w // 2, fill=255)
    im.paste(inner, (ox, oy), m)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((ox - 14, oy - 14, ox + w + 14, oy + h + w), radius=w // 2 + 14, outline=GOLD, width=14)
    d.rectangle((ox - 40, oy + h, ox + w + 40, oy + h + 160), fill=(0, 0, 0, 0))
    # lattice hint
    for i in range(1, 6):
        y = oy + h * i / 6
        d.line((ox + 30, y, ox + w - 30, y), fill=(255, 230, 190, 60), width=3)
    return im
door = make_door()
door_sign = text_img('اونكول', font('Ruqaa', 110), ORANGE, rtl=True, glow=ORANGE + (200,))
door_sub = en('ONCOAL  ·  WATERLOO', 30, GOLD)
door_cap = caption('دخلوا علينا لأول مرة', 'First time walking in')

# menu
LAMB, CHICK = load_dish('lamb', 560), load_dish('chicken', 560)
def menu_card():
    w, h = 900, 980
    im = Image.new('RGBA', (w, h)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=40, fill=(38, 26, 21, 245), outline=GOLD, width=4)
    put(im, en('MENU', 54, GOLD), w / 2 - 110, 90); put(im, ar('المنيو', 60, GOLD), w / 2 + 110, 86)
    d.line((90, 160, w - 90, 160), fill=GOLD + (120,), width=2)
    rows = [(LAMB, 'لحم مندي', 'LAMB MANDI', '$24.99'), (CHICK, 'دجاج شواية', 'GRILLED CHICKEN', '$11.99')]
    for i, (src, a, e, p) in enumerate(rows):
        y = 200 + i * 380
        th = src.resize((300, 300), Image.LANCZOS)
        d.ellipse((w - 370, y - 6, w - 58, y + 306), fill=ORANGE)
        im.paste(th, (w - 364, y), circle_mask(300))
        put(im, ar(a, 64, CREAM, 'Black'), 300, y + 90)
        put(im, en(e, 30, MUTED), 300, y + 170)
        put(im, text_img(p, bebas(76), ORANGE), 300, y + 245)
    return im
menu = menu_card()
check = Image.new('RGBA', (120, 120)); cd = ImageDraw.Draw(check)
cd.ellipse((4, 4, 116, 116), fill=ORANGE); cd.line((32, 62, 52, 84, 90, 38), fill=BG + (255,), width=13, joint='curve')
menu_q = caption('لحم ولا دجاج؟', 'Lamb or chicken?')
menu_a = caption('ليش نختار؟ الاثنين!', 'Why choose? Both!')

# order ticket
def ticket():
    w, h = 760, 900
    im = Image.new('RGBA', (w, h + 40)); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, w, h), fill=(250, 244, 232))
    for x in range(0, w, 40): d.polygon([(x, h), (x + 20, h + 26), (x + 40, h)], fill=(250, 244, 232))
    return im
TICKET = ticket()
T_LINES = [
    (text_img('ORDER  #001', bebas(80), INK, shadow=False), 90),
    (text_img('TABLE OF 5  ·  FIRST VISIT', mont(30), (150, 110, 80), shadow=False), 165),
    (None, 215),
    (text_img('½  لحم مندي', cairo(66, 'Black'), INK, rtl=True, shadow=False), 300),
    (text_img('HALF LAMB MANDI', mont(30), (150, 110, 80), shadow=False), 370),
    (text_img('½  دجاج شواية', cairo(66, 'Black'), INK, rtl=True, shadow=False), 470),
    (text_img('HALF GRILLED CHICKEN', mont(30), (150, 110, 80), shadow=False), 540),
    (None, 600),
    (text_img('صحن عائلي كبير · نص بنص', cairo(52, 'Bold'), (200, 90, 30), rtl=True, shadow=False), 680),
    (text_img('ONE BIG FAMILY PLATTER', mont(32), (200, 90, 30), shadow=False), 750),
]
order_cap = caption('الطلب وصل المطبخ', 'Order in. Coals ready.')

# platter
def platter(d=820):
    S = d + 200; c = S // 2
    im = Image.new('RGBA', (S, S))
    sh = Image.new('L', (S, S)); ImageDraw.Draw(sh).ellipse((c - d // 2, c - d // 2 + 50, c + d // 2, c + d // 2 + 70), fill=210)
    im.paste(Image.new('RGBA', (S, S), (0, 0, 0, 255)), mask=sh.filter(ImageFilter.GaussianBlur(40)))
    glow = Image.new('L', (S, S)); ImageDraw.Draw(glow).ellipse((c - d // 2 - 20, c - d // 2 - 20, c + d // 2 + 20, c + d // 2 + 20), fill=120)
    im.paste(Image.new('RGBA', (S, S), ORANGE + (255,)), mask=glow.filter(ImageFilter.GaussianBlur(30)))
    rim = Image.new('RGBA', (S * 2, S * 2)); rd = ImageDraw.Draw(rim)
    for i, col in enumerate([(150, 150, 150), (222, 222, 218), (176, 176, 172), (236, 236, 232)]):
        o = i * 10
        rd.ellipse(((c - d // 2 + o) * 2,) * 2 + ((c + d // 2 - o) * 2,) * 2, fill=col)
    im.alpha_composite(rim.resize((S, S), Image.LANCZOS))
    fd = d - 90
    food = Image.new('RGB', (fd, fd))
    food.paste(load_dish('lamb', fd).crop((0, 0, fd // 2, fd)), (0, 0))
    food.paste(load_dish('chicken', fd).crop((fd // 2, 0, fd, fd)), (fd // 2, 0))
    seam = Image.new('L', (fd, fd)); ImageDraw.Draw(seam).rectangle((fd // 2 - 14, 0, fd // 2 + 14, fd), fill=255)
    fl = food.copy().filter(ImageFilter.GaussianBlur(16)); food.paste(fl, (0, 0), seam.filter(ImageFilter.GaussianBlur(10)))
    im.paste(food, (c - fd // 2, c - fd // 2), circle_mask(fd))
    return im
PLATTER = platter()
steam_puff = Image.new('RGBA', (220, 220)); sm = Image.new('L', (220, 220)); ImageDraw.Draw(sm).ellipse((50, 50, 170, 170), fill=90)
steam_puff.paste(Image.new('RGBA', (220, 220), (255, 250, 240, 255)), mask=sm.filter(ImageFilter.GaussianBlur(28)))
lab_l = (ar('لحم مندي', 58, CREAM, 'Black'), en('LAMB MANDI', 30, GOLD))
lab_r = (ar('دجاج شواية', 58, CREAM, 'Black'), en('GRILLED CHICKEN', 30, GOLD))
plat_cap = caption('صحن كبير… نص لحم ونص دجاج', 'One big platter. Half & half.')

# family at the table
def bubble(lines, flip=False):
    imgs = lines
    w = max(i.width for i in imgs) - 40; h = sum(i.height - 70 for i in imgs) + 50
    im = Image.new('RGBA', (w + 20, h + 50)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w + 19, h), radius=36, fill=CREAM)
    tx = (w * 0.25) if not flip else (w * 0.75)
    d.polygon([(tx - 20, h - 2), (tx + 20, h - 2), (tx + (-10 if flip else 10), h + 44)], fill=CREAM)
    y = 25
    for i in imgs:
        im.alpha_composite(i, (int((w + 20 - i.width) / 2), y - 45)); y += i.height - 70
    return im
B = lambda a, e: bubble([text_img(a, cairo(54, 'Black'), INK, rtl=True, shadow=False), text_img(e, mont(30), (190, 90, 30), shadow=False)])
BUBBLES = [  # (bubble, x, y, start time)
    (B('خرافي!', 'This is amazing!'), 210, 860, 1.2),
    (B('الرز يجنن', 'The rice though…'), 790, 820, 2.1),
    (B('يا سلام', 'So tender!'), 470, 660, 3.0),
    (B('أكثر!', 'More please!'), 920, 1010, 3.8),
]
TABLE_Y = 1330
table_img = Image.new('RGBA', (1000, 300)); td = ImageDraw.Draw(table_img)
td.rounded_rectangle((0, 0, 999, 60), radius=20, fill=(110, 70, 42)); td.rectangle((40, 60, 960, 300), fill=(74, 46, 28))
td.line((0, 6, 1000, 6), fill=GOLD + (160,), width=4)
tbl_cap = caption('وعجبهم الأكل مرة!', 'And they loved every bite.')

# outro
o_t1 = ar('أول زيارة… وأكيد مو آخر وحدة', 64, CREAM, 'Black')
o_t2 = en('First visit. Definitely not the last.', 36, GOLD)
o_logo_en = text_img('ONCOAL', bebas(250), CREAM, glow=ORANGE + (200,))
o_info = en('WATERLOO, ON  ·  100% HALAL  ·  DAILY FROM 12 PM', 30, MUTED)
o_cta = ar('زورونا مع العيلة', 60, BG, 'Black', glow=None)
def pill(im, padx=60, h=120):
    w = im.width - 100 + padx * 2; p = Image.new('RGBA', (w, h)); ImageDraw.Draw(p).rounded_rectangle((0, 0, w - 1, h - 1), h // 2, fill=ORANGE)
    p.alpha_composite(im, (w // 2 - im.width // 2, h // 2 - im.height // 2)); return p
o_pill = pill(text_img('زورونا مع العيلة', cairo(56, 'Black'), BG, rtl=True, shadow=False))
divider = Image.new('RGBA', (520, 3), ORANGE + (200,))


# ---------- scenes ----------
def show_caption(f, cap, t, y=1640, out_at=None):
    k = ease((t - 0.2) / 0.5); a = k * (1 - ease((t - out_at) / 0.3) if out_at else 1)
    put(f, cap[0], W / 2, y + 30 * (1 - k), a)
    put(f, cap[1], W / 2, y + 85 + 30 * (1 - k), a)

def scene_intro(f, t):
    put(f, i_kicker, W / 2, 560, ease(t / .5))
    k = back((t - .3) / .7); put(f, i_t1, W / 2, 760, ease((t - .3) / .3), 0.7 + 0.3 * k)
    put(f, divider, W / 2, 900, ease((t - .9) / .5), ease((t - .9) / .5))
    k = ease((t - 1.1) / .6); put(f, i_t2, W / 2, 1000 + 30 * (1 - k), k)
    k = ease((t - 1.4) / .6); put(f, i_t3, W / 2, 1080 + 30 * (1 - k), k)
    k = ease((t - 1.9) / .6); put(f, logo_ar, W / 2, 1300, k, 0.8 + 0.2 * k)

def scene_door(f, t):
    put(f, door, W / 2, 900, ease(t / .6))
    put(f, door_sign, W / 2, 330, ease((t - .2) / .6))
    put(f, door_sub, W / 2, 430, ease((t - .4) / .6))
    order = [0, 2, 1, 3, 4]
    for n, i in enumerate(order):
        p = WALKERS[i]
        k = (t - 0.4 - n * 0.32) / 3.0      # walk progress
        if k <= 0: continue
        kk = ease(min(k, 1))
        x = -150 + (W / 2 + 40 - n * 6 + 150) * kk
        sc = 1 - 0.45 * kk
        y = 1420 - p.height * sc / 2 - 260 * kk - 10 * abs(math.sin(t * 7 + n))
        put(f, p, x, y, 1 - ease((k - 0.85) / 0.25), sc)
    floor = Image.new('RGBA', (W, 4), GOLD + (80,)); put(f, floor, W / 2, 1420, ease(t / .6))
    show_caption(f, door_cap, t - 0.6)

def scene_menu(f, t):
    k = back(t / .7); put(f, menu, W / 2, 820, ease(t / .3), 0.85 + 0.15 * k)
    for j, ts in enumerate((2.2, 2.6)):
        kk = back((t - ts) / .45); put(f, check, W / 2 - 330, 420 + j * 380, ease((t - ts) / .2), kk)
    if t < 2.6: show_caption(f, menu_q, t, out_at=2.3)
    else: show_caption(f, menu_a, t - 2.4)

def scene_order(f, t):
    k = ease(t / .6); put(f, TICKET, W / 2, 860 + 200 * (1 - k), k, rot=-2 + 2 * k)
    top = 860 + 200 * (1 - k) - TICKET.height / 2
    for j, (im, y) in enumerate(T_LINES):
        if im is None:
            kk = ease((t - 0.5 - j * 0.28) / .3)
            if kk > 0: put(f, Image.new('RGBA', (int(600 * kk), 3), (200, 170, 140, 255)), W / 2, top + y, k)
            continue
        kk = ease((t - 0.5 - j * 0.28) / .3); put(f, im, W / 2, top + y, kk * k)
    show_caption(f, order_cap, t - 0.4)

def scene_platter(f, t):
    k = back(t / .8)
    put(f, PLATTER, W / 2, 860, ease(t / .3), 0.6 + 0.4 * k + 0.02 * t / 7, rot=-3 * t)
    for s in range(6):   # steam
        ph = (t * 0.45 + s / 6) % 1
        put(f, steam_puff, W / 2 - 220 + s * 90 + 40 * math.sin(t + s), 700 - 520 * ph, (1 - ph) * ease((t - .6) / .6) * 0.7, 0.8 + ph)
    for lab, x, d in ((lab_l, 250, 1), (lab_r, 830, -1)):
        kk = ease((t - 1.6) / .5)
        put(f, lab[0], x, 1380 + 30 * (1 - kk), kk); put(f, lab[1], x, 1440 + 30 * (1 - kk), kk)
    show_caption(f, plat_cap, t - 0.8, y=1620)

SEAT_X = [190, 395, 600, 790, 960]
SEAT_ORDER = [0, 1, 2, 3, 4]
def scene_table(f, t):
    for j, i in enumerate(SEAT_ORDER):
        p = SEATED[i]
        kk = back((t - j * 0.12) / .5)
        put(f, p, SEAT_X[j], TABLE_Y - p.height / 2 + 40 + 5 * math.sin(t * 3 + j), ease((t - j * .12) / .2), kk)
    put(f, table_img, W / 2, TABLE_Y + 150, ease(t / .4))
    plat = PLATTER.resize((PLATTER.width // 2, PLATTER.height // 4), Image.BILINEAR)
    put(f, plat, W / 2, TABLE_Y + 10, ease((t - .4) / .4), back((t - .4) / .5))
    for b, bx, by, ts in BUBBLES:
        put(f, b, bx, by, ease((t - ts) / .2), back((t - ts) / .45))
    show_caption(f, tbl_cap, t - 0.5, y=1700)

def scene_outro(f, t):
    pulse = 1 + 0.015 * math.sin(t * math.pi * 2)
    k = ease(t / .6); put(f, o_t1, W / 2, 520 + 30 * (1 - k), k)
    k = ease((t - .3) / .6); put(f, o_t2, W / 2, 610 + 30 * (1 - k), k)
    k = back((t - .7) / .7); put(f, o_logo_en, W / 2, 860, ease((t - .7) / .3), k * pulse)
    k = ease((t - 1.1) / .6); put(f, logo_ar, W / 2, 1060, k, 0.85 + 0.15 * k)
    put(f, divider, W / 2, 1170, ease((t - 1.4) / .5), ease((t - 1.4) / .5))
    k = ease((t - 1.6) / .6); put(f, o_info, W / 2, 1250, k)
    k = back((t - 2.1) / .5); put(f, o_pill, W / 2, 1420, ease((t - 2.1) / .2), k)

SCENES = [(T_INTRO, scene_intro), (T_DOOR, scene_door), (T_MENU, scene_menu), (T_ORDER, scene_order),
          (T_PLATTER, scene_platter), (T_TABLE, scene_table), (T_OUTRO, scene_outro)]

def frame_at(t):
    f = bg.copy(); embers(f, t)
    for (a, b), fn in SCENES:
        if a <= t < b:
            fn(f, t - a)
            fade = min(1, (b - t) / 0.35) if b < DUR else 1
            if fade < 1: f = Image.blend(bg, f, fade)
            break
    g = min(1, t / .5, (DUR - t) / .8)
    if g < 1: f = Image.blend(Image.new('RGBA', (W, H), (0, 0, 0, 255)), f, max(g, 0))
    return f.convert('RGB')


if __name__ == '__main__':
    if len(sys.argv) > 1:
        out = os.environ.get('PREVIEW_DIR', '/tmp')
        for ts in sys.argv[1:]:
            frame_at(float(ts)).save(f'{out}/story_{ts}.jpg', quality=85)
        raise SystemExit
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
                           'oncoal_family_story_nomusic.mp4'], stdin=subprocess.PIPE)
    for n in range(int(DUR * FPS)):
        ff.stdin.write(frame_at(n / FPS).tobytes())
        if n % 150 == 0: print(n, flush=True)
    ff.stdin.close(); ff.wait(); print('done')
