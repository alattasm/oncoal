"""Kashki family shopping story (1920x1080, 30 fps) for the in-store TV.

A family goes grocery shopping at Kashki: beef & veal, lamb & goat, fresh + marinated chicken,
cart fills up, and they say it's some of the best meat around. Uses the shop's own photos.

Usage:  python3 kashki_story.py            -> renders kashki_story_nomusic.mp4
        python3 kashki_story.py 5 12.5 ... -> preview stills into $PREVIEW_DIR (default /tmp)
Then:   ffmpeg -i kashki_story_nomusic.mp4 -i ../video/music_pro2.wav ... (see bottom of README / commit)
"""
import math, os, subprocess, sys, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, '..', 'video', 'fonts')
UP = os.environ.get('UPLOADS', '/root/.claude/uploads/7c825678-363e-58c3-b667-e0a3402e7eba')
W, H, FPS = 1920, 1080, 30
BG = (22, 14, 11)
RED, GOLD, CREAM, MUTED, YEL = (211, 50, 42), (240, 192, 96), (255, 246, 236), (179, 161, 145), (255, 210, 63)
INK = (40, 26, 20)

T = dict(intro=(0, 4), arrive=(4, 9.5), beef=(9.5, 16.5), lamb=(16.5, 22.5), chicken=(22.5, 29.5),
         cart=(29.5, 34.5), verdict=(34.5, 40), outro=(40, 45))
DUR = 45


def font(name, size, var=None):
    f = ImageFont.truetype(os.path.join(FONTS, f'{name}.ttf'), size, layout_engine=ImageFont.Layout.RAQM)
    if var: f.set_variation_by_name(var)
    return f
cairo = lambda s, v='Bold': font('Cairo', s, v)
bebas = lambda s: font('Bebas', s)
mont = lambda s: font('Montserrat', s, 'Bold')


def text_img(s, f, fill, rtl=False, glow=None, shadow=True):
    kw = {'direction': 'rtl', 'language': 'ar'} if rtl else {}
    pad = 50; l, t, r, b = f.getbbox(s, **kw)
    im = Image.new('RGBA', (r - l + pad * 2, b - t + pad * 2))
    ImageDraw.Draw(im).text((pad - l, pad - t), s, font=f, fill=fill, **kw)
    out = Image.new('RGBA', im.size)
    if shadow:
        sh = Image.new('RGBA', im.size); sh.putalpha(im.getchannel('A').point(lambda v: v * 0.7))
        out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)), (0, 6))
    if glow:
        g = Image.new('RGBA', im.size, glow[:3] + (0,)); g.putalpha(im.getchannel('A').point(lambda v: v * glow[3] / 255))
        out.alpha_composite(g.filter(ImageFilter.GaussianBlur(22)))
    out.alpha_composite(im); return out
ar = lambda s, size=64, fill=CREAM, v='Bold', glow=None: text_img(s, cairo(size, v), fill, rtl=True, glow=glow)
en = lambda s, size=34, fill=GOLD: text_img(s, mont(size), fill)

def ease(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3
def back(x):
    x = min(max(x, 0), 1); c = 1.70158; return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2

def put(frame, im, cx, cy, alpha=1.0, scale=1.0, rot=0):
    if alpha <= 0.01 or scale <= 0.01: return
    if rot: im = im.rotate(rot, Image.BICUBIC, expand=True)
    if abs(scale - 1) > 0.005:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
    if alpha < 0.999:
        im = im.copy(); im.putalpha(im.getchannel('A').point(lambda v: int(v * alpha)))
    frame.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


# ---------- background ----------
yy, xx = np.mgrid[0:H, 0:W]
r = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H * 0.4) / H) ** 2)
v = np.clip(1 - r * 1.25, 0, 1)[..., None]
bg = Image.fromarray(np.clip(np.array(BG, float) * (0.55 + 0.8 * v) + np.array([70, 18, 8]) * v ** 3, 0, 255).astype(np.uint8)).convert('RGBA')
d = ImageDraw.Draw(bg)
bd = ImageDraw.Draw(bg); bd.rounded_rectangle((14, 14, W - 15, H - 15), radius=24, outline=GOLD + (90,), width=2)


# ---------- photos from the shop ----------
def photo(path, box, size, pink=True, radius=32, border=GOLD):
    im = Image.open(path).convert('RGB').crop(box)
    a = np.asarray(im).astype(float)
    if pink: a[..., 2] *= 0.80; a[..., 1] *= 1.05
    im = Image.fromarray(a.clip(0, 255).astype('uint8'))
    im = ImageEnhance.Contrast(im).enhance(1.1)
    im = ImageOps.fit(im, size, Image.LANCZOS).filter(ImageFilter.UnsharpMask(2, 50, 2))
    w, h = size; S = 3
    m = Image.new('L', (w * S, h * S)); ImageDraw.Draw(m).rounded_rectangle((0, 0, w * S - 1, h * S - 1), radius * S, fill=255)
    m = m.resize(size, Image.LANCZOS)
    out = Image.new('RGBA', (w + 80, h + 80))
    sh = Image.new('L', out.size); ImageDraw.Draw(sh).rounded_rectangle((40, 56, w + 40, h + 56), radius, fill=200)
    out.paste(Image.new('RGBA', out.size, (0, 0, 0, 255)), mask=sh.filter(ImageFilter.GaussianBlur(22)))
    out.paste(im, (40, 40), m)
    ImageDraw.Draw(out).rounded_rectangle((38, 38, w + 41, h + 41), radius + 2, outline=border, width=5)
    return out

def circ(path, box, dd, pink=True):
    im = Image.open(path).convert('RGB').crop(box)
    a = np.asarray(im).astype(float)
    if pink: a[..., 2] *= 0.80; a[..., 1] *= 1.05
    im = ImageOps.fit(Image.fromarray(a.clip(0, 255).astype('uint8')), (dd, dd), Image.LANCZOS)
    m = Image.new('L', (dd * 3, dd * 3)); ImageDraw.Draw(m).ellipse((0, 0, dd * 3 - 1, dd * 3 - 1), fill=255)
    out = Image.new('RGBA', (dd + 12, dd + 12)); ImageDraw.Draw(out).ellipse((0, 0, dd + 11, dd + 11), fill=GOLD)
    out.paste(im, (6, 6), m.resize((dd, dd), Image.LANCZOS)); return out

P_BEEF = photo(f'{UP}/44ac7e94-image.jpg', (0, 0, 1512, 1000), (880, 580))
P_BEEF2 = photo(f'{UP}/5071876d-image.jpg', (0, 60, 1700, 900), (880, 580))
P_LAMB = photo(f'{UP}/a5daddff-image.jpg', (230, 560, 1250, 880), (880, 520))
P_CHK = photo(f'{UP}/79be129e-image.jpg', (1080, 660, 1990, 1150), (700, 460))
P_MAR = photo(f'{UP}/68f25c4a-image.jpg', (100, 500, 1412, 1400), (700, 460), pink=False)
CART_ITEMS = [circ(f'{UP}/44ac7e94-image.jpg', (200, 0, 1100, 800), 150), circ(f'{UP}/9a2a905f-image.jpg', (1430, 560, 1660, 930), 150),
              circ(f'{UP}/a5daddff-image.jpg', (810, 600, 1120, 860), 150), circ(f'{UP}/79be129e-image.jpg', (1560, 680, 1960, 1060), 150),
              circ(f'{UP}/68f25c4a-image.jpg', (200, 400, 1300, 1400), 150, pink=False), circ(f'{UP}/5071876d-image.jpg', (0, 120, 520, 700), 150)]


# ---------- characters (flat illustration) ----------
SKIN = [(198, 146, 108), (176, 124, 88), (214, 166, 126), (190, 136, 98), (205, 156, 116)]
def person(h, shirt, skin, hijab=None, hair=(34, 24, 20)):
    S = 3; hh = h * S; w = int(hh * 0.5); cx = w // 2
    im = Image.new('RGBA', (w, hh + 4 * S)); d = ImageDraw.Draw(im)
    r = hh * 0.12; hy = r + 2 * S
    body_top, body_bot = hy + r * 1.05, hh * 0.62; bw = hh * 0.17; lw = bw * 0.42
    d.rounded_rectangle((cx - bw * 0.9, body_bot - 20, cx - bw * 0.9 + lw * 2, hh), radius=lw, fill=(46, 40, 52))
    d.rounded_rectangle((cx + bw * 0.9 - lw * 2, body_bot - 20, cx + bw * 0.9, hh), radius=lw, fill=(46, 40, 52))
    if hijab:
        d.ellipse((cx - r * 1.35, hy - r * 1.3, cx + r * 1.35, hy + r * 1.45), fill=hijab)
        d.rounded_rectangle((cx - bw * 1.05, body_top - r * 0.2, cx + bw * 1.05, body_bot + hh * 0.1), radius=bw, fill=shirt)
        d.polygon([(cx - r * 1.25, hy + r * 0.4), (cx + r * 1.25, hy + r * 0.4), (cx + bw * 1.15, body_top + r * 0.9), (cx - bw * 1.15, body_top + r * 0.9)], fill=hijab)
        d.ellipse((cx - r * 0.82, hy - r * 0.85, cx + r * 0.82, hy + r * 0.95), fill=skin)
    else:
        d.rounded_rectangle((cx - bw, body_top, cx + bw, body_bot), radius=bw * 0.8, fill=shirt)
        d.ellipse((cx - r, hy - r, cx + r, hy + r), fill=skin)
        d.chord((cx - r * 1.04, hy - r * 1.08, cx + r * 1.04, hy + r * 0.7), 180, 360, fill=hair)
    ey = hy + r * 0.05
    for sx in (-1, 1):
        d.ellipse((cx + sx * r * 0.36 - 3 * S, ey - 3 * S, cx + sx * r * 0.36 + 3 * S, ey + 3 * S), fill=(30, 20, 16))
    d.arc((cx - r * 0.38, hy + r * 0.05, cx + r * 0.38, hy + r * 0.62), 20, 160, fill=(120, 50, 40), width=int(2.5 * S))
    return im.resize((w // S, (hh + 4 * S) // S), Image.LANCZOS)

FAM = [person(420, (58, 92, 120), SKIN[0]),                    # dad
       person(390, (120, 44, 52), SKIN[2], (70, 52, 80)),      # mom
       person(320, (214, 142, 60), SKIN[4]),                   # son
       person(270, (70, 130, 96), SKIN[3], (220, 120, 120))]   # daughter

def cart_img(fill_n=0, items=None, sc=1.0):
    w, h = 300, 260
    im = Image.new('RGBA', (w + 40, h + 40)); d = ImageDraw.Draw(im)
    d.line((10, 20, 50, 20, 70, 60), fill=(200, 200, 205), width=10, joint='curve')
    d.polygon([(60, 60), (w + 20, 60), (w - 10, 190), (95, 190)], fill=(200, 200, 205, 60), outline=(220, 220, 225), width=7)
    for i in range(1, 5):
        x = 60 + i * (w - 40) / 5; d.line((x, 62, x + 10 - i * 4, 188), fill=(220, 220, 225, 140), width=3)
    d.line((90, 215, w - 20, 215), fill=(200, 200, 205), width=8)
    for x in (115, w - 40): d.ellipse((x - 18, 222, x + 18, 258), fill=(60, 60, 66), outline=(200, 200, 205), width=5)
    return im
CART = cart_img()


# ---------- reusable bits ----------
def bubble(a, e=None, size=50):
    t1 = text_img(a, cairo(size, 'Black'), INK, rtl=True, shadow=False)
    imgs = [t1] + ([text_img(e, mont(26), (190, 70, 30), shadow=False)] if e else [])
    w = max(i.width for i in imgs) - 40; hh = sum(i.height - 70 for i in imgs) + 44
    im = Image.new('RGBA', (w + 20, hh + 46)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w + 19, hh), radius=34, fill=CREAM)
    tx = w * 0.3; d.polygon([(tx - 18, hh - 2), (tx + 18, hh - 2), (tx - 6, hh + 40)], fill=CREAM)
    y = 22
    for i in imgs: im.alpha_composite(i, (int((w + 20 - i.width) / 2), y - 45)); y += i.height - 70
    return im

def tag(name, price, sale=False):
    t1 = text_img(name, cairo(40, 'Black'), CREAM, rtl=True, shadow=False)
    t2 = text_img(price, bebas(70), YEL if sale else CREAM, shadow=False)
    t3 = text_img('/lb', mont(22), MUTED, shadow=False)
    w = t1.width + t2.width + t3.width - 230; hgt = 110
    im = Image.new('RGBA', (w + 60, hgt + 20)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w + 59, hgt), 22, fill=(58, 13, 9, 240) if sale else (13, 9, 7, 235), outline=RED if sale else GOLD, width=4)
    x = 20; im.alpha_composite(t3, (x - 40, 4)); x += t3.width - 90
    im.alpha_composite(t2, (x - 40, -18)); x += t2.width - 80
    im.alpha_composite(t1, (x - 30, -14))
    if sale:
        s = text_img('عرض', cairo(26, 'Black'), (255, 255, 255), rtl=True, shadow=False)
        p = Image.new('RGBA', (s.width - 40, 46)); ImageDraw.Draw(p).rounded_rectangle((0, 0, p.width - 1, 45), 23, fill=RED)
        p.alpha_composite(s, ((p.width - s.width) // 2, (46 - s.height) // 2))
        out = Image.new('RGBA', (im.width + 20, im.height + 30)); out.alpha_composite(im, (0, 30)); out.alpha_composite(p, (out.width - p.width - 10, 0))
        return out
    return im

def caption(a, e):
    return ar(a, 60, CREAM, 'Black'), en(e, 30, GOLD)
def show_caption(f, cap, t, y=975, out_at=None):
    k = ease((t - 0.2) / 0.5); a = k * ((1 - ease((t - out_at) / 0.3)) if out_at else 1)
    put(f, cap[0], W / 2, y + 25 * (1 - k), a); put(f, cap[1], W / 2, y + 55 + 25 * (1 - k), a)

def pill(im, h=104, col=RED):
    w = im.width - 100 + 120; p = Image.new('RGBA', (w, h)); ImageDraw.Draw(p).rounded_rectangle((0, 0, w - 1, h - 1), h // 2, fill=col)
    p.alpha_composite(im, (w // 2 - im.width // 2, h // 2 - im.height // 2)); return p

def kenburns(im, t, dur, z=0.06):
    return 1 + z * min(t / dur, 1)


# ---------- static texts ----------
LOGO = text_img('كشكي', cairo(200, 'Black'), YEL, rtl=True, glow=RED + (200,))
LOGO_S = text_img('كشكي', cairo(110, 'Black'), YEL, rtl=True, glow=RED + (180,))
i_t1 = ar('يوم المقاضي', 140, CREAM, 'Black', glow=RED + (170,))
i_t2 = ar('العيلة رايحة تقضي من كشكي 🛒', 58)
i_t2 = ar('العيلة رايحة تقضي من كشكي', 58)
i_t3 = en('SHOPPING DAY  ·  THE FAMILY IS HEADING TO KASHKI', 30, MUTED)
divider = Image.new('RGBA', (520, 3), GOLD + (200,))

def storefront():
    w, h = 1100, 640
    im = Image.new('RGBA', (w, h + 40)); d = ImageDraw.Draw(im)
    d.rectangle((40, 150, w - 40, h), fill=(48, 32, 26))
    for i in range(12):  # awning stripes
        x0 = 20 + i * (w - 40) / 12
        d.polygon([(x0, 110), (x0 + (w - 40) / 12, 110), (x0 + (w - 40) / 12, 210), (x0, 210)], fill=RED if i % 2 == 0 else CREAM)
    for i in range(12):
        x0 = 20 + i * (w - 40) / 12; d.pieslice((x0, 180, x0 + (w - 40) / 12, 240), 0, 180, fill=RED if i % 2 == 0 else CREAM)
    d.rounded_rectangle((260, 0, w - 260, 120), 22, fill=(20, 12, 10), outline=GOLD, width=5)
    im.alpha_composite(LOGO_S, (w // 2 - LOGO_S.width // 2, 60 - LOGO_S.height // 2))
    # windows with glow + door
    for x0 in (90, w - 410):
        d.rounded_rectangle((x0, 280, x0 + 320, 520), 14, fill=(255, 214, 150), outline=GOLD, width=6)
        d.line((x0 + 160, 280, x0 + 160, 520), fill=GOLD, width=5)
    d.rounded_rectangle((w // 2 - 110, 290, w // 2 + 110, h), 14, fill=(255, 196, 120), outline=GOLD, width=6)
    d.ellipse((w // 2 + 60, 460, w // 2 + 80, 480), fill=GOLD)
    d.rectangle((0, h, w, h + 40), fill=(80, 60, 50))
    t = text_img('لحوم حلال طازجة', cairo(36, 'Black'), INK, rtl=True, shadow=False)
    d.rectangle((40, 240, w - 40, 268), fill=(20, 12, 10))
    t = text_img('لحوم حلال طازجة يومياً', cairo(26, 'Black'), GOLD, rtl=True, shadow=False)
    im.alpha_composite(t, (w // 2 - t.width // 2, 254 - t.height // 2))
    return im
SHOP = storefront()
arr_cap = caption('وصلنا كشكي!', 'Here we are at Kashki!')

beef_cap = caption('أول شي: العجل والبقري', 'First stop: veal & beef')
B_DAD1 = bubble('شوف الستيك! عليه عرض', 'Look, steaks on sale!')
B_MOM1 = bubble('وخذ مفروم للكبة', 'Grab ground beef too')
TAG_B = [tag('ستيك ستربلوين', '$14.49', True), tag('ستيك ريب', '$9.99', True), tag('لحم مفروم', '$6.99')]

lamb_cap = caption('وبعدين الغنم والماعز', 'Then lamb & goat')
B_SON = bubble('فخذ ماعز لغدا الجمعة!', 'Goat leg for Friday lunch!')
TAG_L = [tag('فخذ ماعز', '$15.99'), tag('مكعبات ماعز', '$7.99')]

chk_cap = caption('والدجاج… طازج ومتبّل', 'And chicken, fresh & marinated')
B_GIRL = bubble('أبي المتبّل!', 'I want the marinated one!')
B_MOM2 = bubble('جاهز للشوي، ما يبي تعب', 'Ready to grill, no effort')
TAG_C = [tag('دجاج كامل', '$3.59'), tag('دجاج متبّل', '$3.99')]

cart_cap = caption('السلة امتلت 🛒', 'Cart is full')
cart_cap = caption('السلة امتلت… وكلها طازجة', 'A full cart, all of it fresh')

ver_cap = caption('وكان رأي العيلة…', "And the family's verdict…")
VB = [(bubble('من أفضل اللحوم!', 'Some of the best meat!', 54), 0),
      (bubble('طازج كل يوم', 'Fresh every day'), 1),
      (bubble('والأسعار حلوة', 'Great prices too'), 2),
      (bubble('راجعين الأسبوع الجاي!', "We'll be back next week!"), 3)]

o_t1 = ar('لحوم حلال طازجة يومياً', 64, CREAM, 'Black')
o_t2 = ar('عجل · بقري · غنم · ماعز · دجاج · متبّلات', 44, GOLD)
o_t3 = en('FRESH HALAL MEAT  ·  EVERY DAY', 30, MUTED)
o_pill = pill(text_img('زورونا مع العيلة', cairo(52, 'Black'), (255, 255, 255), rtl=True, shadow=False))


# ---------- scenes ----------
def family_line(f, t, x0, y_floor, alpha=1, scale=1.0, bob=True, gap=150):
    for i, p in enumerate(FAM):
        kk = back((t - i * 0.12) / 0.5)
        y = y_floor - p.height * scale / 2 - (6 * abs(math.sin(t * 3 + i)) if bob else 0)
        put(f, p, x0 + i * gap * scale, y, ease((t - i * .12) / .2) * alpha, kk * scale)

def scene_intro(f, t):
    put(f, CART, W / 2, 190, ease(t / .5), back(t / .6), rot=6 * math.sin(t * 2))
    k = back((t - .3) / .7); put(f, i_t1, W / 2, 390, ease((t - .3) / .3), 0.7 + 0.3 * k)
    put(f, divider, W / 2, 490, ease((t - .9) / .5), ease((t - .9) / .5))
    k = ease((t - 1.1) / .6); put(f, i_t2, W / 2, 560 + 25 * (1 - k), k)
    k = ease((t - 1.4) / .6); put(f, i_t3, W / 2, 630 + 25 * (1 - k), k)
    k = ease((t - 1.9) / .6); put(f, LOGO, W / 2, 830, k, 0.8 + 0.2 * k)

def scene_arrive(f, t):
    put(f, SHOP, W / 2 + 220, 520, ease(t / .6), 0.92 + 0.03 * ease(t / 5))
    for n, p in enumerate(FAM):
        k = (t - 0.3 - n * 0.25) / 3.4
        if k <= 0: continue
        kk = ease(min(k, 1)); sc = 1 - 0.5 * kk
        x = -120 + (W / 2 + 230 - n * 10 + 120) * kk
        y = 870 - p.height * sc / 2 - 10 * abs(math.sin(t * 7 + n))
        put(f, p, x, y, 1 - ease((k - 0.88) / 0.2), sc)
    k = (t - 0.3) / 3.4
    if 0 < k < 1.05: put(f, CART, -60 + (W / 2 + 160) * ease(min(k, 1)), 830, 1 - ease((k - 0.88) / 0.2), 0.55 - 0.25 * ease(min(k, 1)))
    show_caption(f, arr_cap, t - 0.8)

def photo_scene(f, t, photos, tags, bubbles, cap, dur):
    # photos on the right half, family on the left
    for j, (ph, x, y, ts) in enumerate(photos):
        k = ease((t - ts) / .6); put(f, ph, x + 60 * (1 - k), y, k, kenburns(ph, t, dur) * (0.94 + 0.06 * k))
    for j, (tg, x, y, ts) in enumerate(tags):
        put(f, tg, x, y, ease((t - ts) / .25), back((t - ts) / .45))
    family_line(f, t, 170, 880, scale=0.95, gap=140)
    put(f, CART, 720, 815, ease(t / .4), 0.5)
    for b, x, y, ts in bubbles:
        put(f, b, x, y, ease((t - ts) / .2), back((t - ts) / .45))
    show_caption(f, cap, t - 0.3)

def scene_beef(f, t):
    photo_scene(f, t, [(P_BEEF2, 1390, 330, 0.0), (P_BEEF, 1290, 600, 2.6)],
                [(TAG_B[0], 1500, 160, 1.0), (TAG_B[1], 1130, 520, 1.6), (TAG_B[2], 1560, 800, 3.4)],
                [(B_DAD1, 345, 190, 1.2), (B_MOM1, 580, 370, 3.6)], beef_cap, 7)

def scene_lamb(f, t):
    photo_scene(f, t, [(P_LAMB, 1330, 430, 0.0)],
                [(TAG_L[0], 1540, 200, 1.0), (TAG_L[1], 1120, 690, 1.8)],
                [(B_SON, 470, 420, 1.4)], lamb_cap, 6)

def scene_chicken(f, t):
    photo_scene(f, t, [(P_CHK, 1180, 330, 0.0), (P_MAR, 1520, 640, 1.8)],
                [(TAG_C[0], 1040, 120, 0.8), (TAG_C[1], 1600, 880 - 60, 2.6)],
                [(B_GIRL, 640, 380, 1.4), (B_MOM2, 345, 190, 3.4)], chk_cap, 7)

def scene_cart(f, t):
    put(f, CART, W / 2, 600, 1, 2.0)
    for j, it in enumerate(CART_ITEMS):
        ts = 0.3 + j * 0.45; k = ease((t - ts) / .55)
        if k <= 0: continue
        tx = W / 2 - 170 + (j % 3) * 150 + 20; ty = 545 - (j // 3) * 100
        x = tx + (1 - k) * (300 if j % 2 else -300); y = ty - (1 - k) * 600
        put(f, it, x, y, min(1, k * 3), 0.8, rot=(1 - k) * 90)
    put(f, CART.crop((40, 150, CART.width, 235)), W / 2 + 20, 600 + 75 * 2 - 128, 1, 2.0) if False else None
    show_caption(f, cart_cap, t - 0.6, y=905)

def scene_verdict(f, t):
    xs = [560, 790, 1010, 1210]
    for i, p in enumerate(FAM):
        kk = back((t - i * 0.12) / .5)
        put(f, p, xs[i], 900 - p.height / 2 - 6 * abs(math.sin(t * 3 + i)), ease((t - i * .12) / .2), kk)
    put(f, CART, 1460, 830, ease(t / .4), 0.8)
    pos = [(390, 330), (760, 150), (1130, 300), (1490, 470)]
    for b, i in VB:
        ts = 0.8 + i * 0.8
        put(f, b, pos[i][0] + 40, pos[i][1], ease((t - ts) / .2), back((t - ts) / .45))
    show_caption(f, ver_cap, t - 0.2, y=975)

def scene_outro(f, t):
    pulse = 1 + 0.015 * math.sin(t * math.pi * 2)
    k = back(t / .7); put(f, LOGO, W / 2, 330, ease(t / .3), k * pulse)
    put(f, divider, W / 2, 470, ease((t - .6) / .5), ease((t - .6) / .5))
    k = ease((t - .7) / .6); put(f, o_t1, W / 2, 545 + 25 * (1 - k), k)
    k = ease((t - 1.0) / .6); put(f, o_t2, W / 2, 630 + 25 * (1 - k), k)
    k = ease((t - 1.3) / .6); put(f, o_t3, W / 2, 700 + 25 * (1 - k), k)
    k = back((t - 1.8) / .5); put(f, o_pill, W / 2, 830, ease((t - 1.8) / .2), k)

SCENES = [('intro', scene_intro), ('arrive', scene_arrive), ('beef', scene_beef), ('lamb', scene_lamb),
          ('chicken', scene_chicken), ('cart', scene_cart), ('verdict', scene_verdict), ('outro', scene_outro)]

def frame_at(t):
    f = bg.copy()
    for name, fn in SCENES:
        a, b = T[name]
        if a <= t < b:
            fn(f, t - a)
            fade = min(1, (b - t) / 0.35) if b < DUR else 1
            if fade < 1: f = Image.blend(bg, f, fade)
            break
    g = min(1, t / .5, (DUR - t) / .8)
    if g < 1: f = Image.blend(Image.new('RGBA', (W, H), (0, 0, 0, 255)), f, max(g, 0))
    return f.convert('RGB')


if __name__ == '__main__':
    os.chdir(HERE)
    if len(sys.argv) > 1:
        out = os.environ.get('PREVIEW_DIR', '/tmp')
        for ts in sys.argv[1:]: frame_at(float(ts)).save(f'{out}/kashki_{ts}.jpg', quality=85)
        raise SystemExit
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
                           'kashki_story_nomusic.mp4'], stdin=subprocess.PIPE)
    for n in range(int(DUR * FPS)):
        ff.stdin.write(frame_at(n / FPS).tobytes())
        if n % 150 == 0: print(n, flush=True)
    ff.stdin.close(); ff.wait(); print('done')
