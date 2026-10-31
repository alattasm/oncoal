"""Oncoal promo v2 (1080x1920, 30 fps): AI-upscaled dishes, menu-style price cards, steam, grading."""
import math, subprocess, sys, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

W, H, FPS, DUR = 1080, 1920, 30, 44.0
BG = (28, 18, 14)
ORANGE, GOLD, CREAM, MUTED = (236, 146, 70), (246, 196, 120), (246, 236, 222), (196, 176, 156)

def font(name, size, var=None):
    f = ImageFont.truetype(f'fonts/{name}.ttf', size, layout_engine=ImageFont.Layout.RAQM)
    if var: f.set_variation_by_name(var)
    return f

def text_img(s, f, fill, rtl=False, glow=None, track=0, shadow=True):
    kw = {'direction': 'rtl', 'language': 'ar'} if rtl else {}
    pad = 50
    if track and not rtl:
        ws = [f.getlength(c) for c in s]
        l, t, r, b = f.getbbox(s)
        w = int(sum(ws) + track * (len(s) - 1))
        im = Image.new('RGBA', (w + pad * 2, b - t + pad * 2)); d = ImageDraw.Draw(im); x = pad
        for c, cw in zip(s, ws):
            d.text((x, pad - t), c, font=f, fill=fill); x += cw + track
    else:
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

def grade(im):
    im = ImageEnhance.Color(im).enhance(1.3)
    im = ImageEnhance.Contrast(im).enhance(1.12)
    im = ImageEnhance.Brightness(im).enhance(1.04)
    a = np.asarray(im).astype(np.float32)
    a[..., 0] *= 1.05; a[..., 2] *= 0.9
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

def load_dish(name):
    src = Image.open(f'assets/hd/{name}.png').convert('RGB')
    w, h = src.size; m = int(min(w, h) * 0.075)
    return grade(src.crop((m, m, w - m, h - m)))

def dish(name, d, ring=12):
    src = load_dish(name).resize((d, d), Image.LANCZOS).filter(ImageFilter.UnsharpMask(2, 60, 2))
    S = d + 260; c = S // 2
    out = Image.new('RGBA', (S, S))
    sh = Image.new('L', (S, S)); ImageDraw.Draw(sh).ellipse((c - d // 2, c - d // 2 + 40, c + d // 2, c + d // 2 + 60), fill=200)
    out.paste(Image.new('RGBA', (S, S), (0, 0, 0, 255)), mask=sh.filter(ImageFilter.GaussianBlur(40)))
    glow = Image.new('L', (S, S)); ImageDraw.Draw(glow).ellipse((c - d // 2 - ring - 6,) * 2 + (c + d // 2 + ring + 6,) * 2, fill=110)
    out.paste(Image.new('RGBA', (S, S), ORANGE + (255,)), mask=glow.filter(ImageFilter.GaussianBlur(26)))
    ring_im = Image.new('RGBA', (S * 2, S * 2)); dr = ImageDraw.Draw(ring_im)
    dr.ellipse(((c - d // 2 - ring) * 2,) * 2 + ((c + d // 2 + ring) * 2,) * 2, fill=GOLD)
    dr.ellipse(((c - d // 2 - ring + 4) * 2,) * 2 + ((c + d // 2 + ring - 4) * 2,) * 2, fill=ORANGE)
    out.alpha_composite(ring_im.resize((S, S), Image.LANCZOS))
    mask = Image.new('L', (d * 2, d * 2)); ImageDraw.Draw(mask).ellipse((0, 0, d * 2 - 1, d * 2 - 1), fill=255)
    out.paste(src, (c - d // 2, c - d // 2), mask.resize((d, d), Image.LANCZOS))
    # soft top-left highlight for a glossy plate feel
    hl = Image.new('L', (S, S)); ImageDraw.Draw(hl).ellipse((c - d // 2 + 40, c - d // 2 + 30, c, c - 40), fill=40)
    out.alpha_composite(Image.composite(Image.new('RGBA', (S, S), (255, 240, 220, 255)), Image.new('RGBA', (S, S)), hl.filter(ImageFilter.GaussianBlur(50))))
    return out

def backdrop(name):
    src = load_dish(name).resize((H, H), Image.BICUBIC).crop(((H - W) // 2, 0, (H - W) // 2 + W, H))
    src = src.filter(ImageFilter.GaussianBlur(45))
    a = np.asarray(src).astype(np.float32) * 0.38
    a = a * 0.75 + np.array(BG) * 0.25
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert('RGBA')

def ease(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3
def eio(x): x = min(max(x, 0), 1); return x * x * (3 - 2 * x)
def back(x):
    x = min(max(x, 0), 1); c = 1.6
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2

def put(frame, im, cx, cy, alpha=1.0, scale=1.0, rot=0):
    if alpha <= 0.01 or scale <= 0.01: return
    if rot: im = im.rotate(rot, Image.BICUBIC)
    if abs(scale - 1) > 0.004:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
    if alpha < 0.999:
        im = im.copy(); im.putalpha(im.getchannel('A').point(lambda v: int(v * alpha)))
    frame.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

def pill(parts, h=104, padx=48, fill=ORANGE):
    widths = [p.width - 100 for p in parts]
    w = sum(widths) + padx * 2 + 26 * (len(parts) - 1)
    im = Image.new('RGBA', (w + 60, h + 60)); d = ImageDraw.Draw(im)
    sh = Image.new('L', im.size); ImageDraw.Draw(sh).rounded_rectangle((30, 40, 30 + w, 40 + h), h // 2, fill=160)
    im.paste(Image.new('RGBA', im.size, (0, 0, 0, 255)), mask=sh.filter(ImageFilter.GaussianBlur(14)))
    d.rounded_rectangle((30, 30, 30 + w, 30 + h), h // 2, fill=fill)
    d.rounded_rectangle((30, 30, 30 + w, 30 + h // 2), h // 2, fill=tuple(min(255, c + 18) for c in fill))
    d.rectangle((30 + h // 2, 30 + h // 2 - 10, 30 + w - h // 2, 30 + h // 2), fill=tuple(min(255, c + 18) for c in fill))
    x = 30 + padx
    for p, pw in zip(parts, widths):
        im.alpha_composite(p, (x - 50, 30 + h // 2 - p.height // 2)); x += pw + 26
    return im

def shine(im, k):
    """light sweep across a sprite, k in 0..1"""
    if k <= 0 or k >= 1: return im
    w, h = im.size
    band = Image.new('L', (w, h)); x = int(-200 + (w + 400) * k)
    ImageDraw.Draw(band).polygon([(x, 0), (x + 90, 0), (x + 30, h), (x - 60, h)], fill=120)
    band = Image.composite(band.filter(ImageFilter.GaussianBlur(12)), Image.new('L', (w, h)), im.getchannel('A'))
    out = im.copy(); out.alpha_composite(Image.composite(Image.new('RGBA', (w, h), (255, 255, 255, 255)), Image.new('RGBA', (w, h)), band))
    return out

# ---------- fonts ----------
bebas = lambda s: font('Bebas', s)
cairo = lambda s, v='Bold': font('Cairo', s, v)
mont = lambda s, v='SemiBold': font('Montserrat', s, v)

def price_card(rows, note=None, w=880):
    rh = 78; h = 50 + rh * len(rows) + (50 if note else 0) + 10
    rows_im = []
    for label, price in rows:
        r = Image.new('RGBA', (w, rh)); d = ImageDraw.Draw(r)
        lf, pf = mont(38, 'SemiBold'), bebas(60)
        d.text((44, rh // 2), label, font=lf, fill=CREAM, anchor='lm')
        pw = pf.getlength(price)
        d.text((w - 44, rh // 2 + 2), price, font=pf, fill=GOLD, anchor='rm')
        x0, x1 = 44 + lf.getlength(label) + 18, w - 44 - pw - 18
        for x in range(int(x0), int(x1), 14): d.ellipse((x, rh // 2 + 8, x + 4, rh // 2 + 12), fill=(150, 120, 95))
        rows_im.append(r)
    card = Image.new('RGBA', (w + 80, h + 80))
    sh = Image.new('L', card.size); ImageDraw.Draw(sh).rounded_rectangle((40, 55, 40 + w, 55 + h), 36, fill=170)
    card.paste(Image.new('RGBA', card.size, (0, 0, 0, 255)), mask=sh.filter(ImageFilter.GaussianBlur(24)))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle((40, 40, 40 + w, 40 + h), 36, fill=(30, 20, 16, 235), outline=(120, 80, 50), width=2)
    d.rounded_rectangle((40, 40, 40 + w, 46), 3, fill=ORANGE)
    noteim = text_img(note, mont(28, 'Medium'), MUTED, shadow=False) if note else None
    return card, rows_im, noteim, h

SCENES = [
    dict(en='CHICKEN', sub='MANDI  ·  SHAWAYA', ar='دجاج', img='chicken', desc='Cooked over coal, served on fragrant rice',
         rows=[('Full Chicken', '$39.99'), ('Half Chicken', '$19.99'), ('Quarter Chicken', '$11.99')], note='BBQ Full $42.99  ·  Half $21.99'),
    dict(en='LAMB', sub='MANDI  ·  MAZBI  ·  MUHAMAR', ar='لحم', img='lamb', desc='Tender, slow-cooked lamb over spiced rice',
         rows=[('Single Lamb Mandi', '$24.99'), ('Single Lamb Mazbi', '$24.99'), ('Double Lamb Muhamar', '$48.99')], note='Double Mandi or Mazbi $48.99'),
    dict(en='MIX PLATTER', sub='CHICKEN  +  LAMB', ar='مكس', img='mix', desc='The best of both on one platter',
         rows=[('Quarter Mix', '$22.99'), ('Single Mix', '$44.99'), ('Double Mix', '$67.99')], note='Served with rice & sauces'),
    dict(en='FISH', sub='FRIED  ·  ROASTED', ar='سمك', img='fish', desc='Whole fish, served with rice and sauces',
         rows=[('Fried Fish', '$44.99'), ('Roasted Fish', '$44.99'), ('Molokhia', '$10.99')], note=None),
    dict(en='BROASTED', sub='CRISPY  ·  GOLDEN', ar='بروستد', img='broasted_stock', desc='Crispy, golden, perfect for sharing',
         rows=[('4 Pieces', '$16.99'), ('8 Pieces', '$29.99'), ('12 Pieces', '$42.99')], note='With fries, garlic sauce & buns'),
    dict(en='BAKERY & SWEETS', sub='MUTABAQ  ·  FATIRAH  ·  MASSOUB', ar='مخبوزات وحلا', img='mutabaq', desc='Fresh from our oven, sweet and savory',
         rows=[('Mutabaq Malah', '$6.99'), ('Fatirah Cheese & Honey', '$10.99'), ('Massoub', '$12.99')], note=None),
]
for i, s in enumerate(SCENES):
    s['dish'] = dish(s['img'], 700)
    s['bg'] = backdrop(s['img'])
    s['num'] = text_img(f'{i + 1:02d}', bebas(64), ORANGE, shadow=False)
    s['sub_im'] = text_img(s['sub'], mont(30, 'Bold'), GOLD, track=6)
    s['en_im'] = text_img(s['en'], bebas(150 if len(s['en']) < 12 else 120), CREAM, track=4)
    s['ar_im'] = text_img(s['ar'], cairo(72, 'Black'), ORANGE, rtl=True)
    s['desc_im'] = text_img(s['desc'], font('Dancing', 54, 'Bold'), CREAM)
    s['card'], s['rows'], s['note_im'], s['card_h'] = price_card(s['rows'], s['note'])

# ---------- other scenes ----------
hero = dish('chicken', 860); hero_bg = backdrop('chicken')
hook1 = text_img('HUNGRY?', bebas(230), CREAM, glow=ORANGE + (170,), track=8)
hook2 = text_img('جوعان؟', cairo(110, 'Black'), ORANGE, rtl=True)
logo_en = text_img('ONCOAL', bebas(310), CREAM, glow=ORANGE + (200,), track=10)
logo_ar = text_img('اونكول', font('Ruqaa', 170), ORANGE, rtl=True)
logo_tag = text_img('YEMENI KITCHEN  ·  COOKED OVER COAL', mont(32, 'Bold'), GOLD, track=5)
logo_script = text_img('Special & Delicious', font('Dancing', 76, 'Bold'), ORANGE)
rule = Image.new('RGBA', (560, 3), GOLD + (230,))
GRID = ['chicken', 'lamb', 'mix', 'broasted_stock', 'fish', 'mutabaq', 'full_mandi', 'massoub', 'mazbi']
grid_imgs = [dish(n, 280, 7) for n in GRID]
grid_bg = backdrop('mix')
g1 = text_img('SOMETHING FOR EVERYONE', bebas(110), CREAM, track=4)
g2 = text_img('All platters served with rice & sauces', font('Dancing', 54, 'Bold'), GOLD)
g3 = pill([text_img('100% ZABIHAH HALAL', bebas(68), BG, shadow=False), text_img('حلال', cairo(46, 'Black'), BG, rtl=True, shadow=False)])
cta = pill([text_img('ORDER NOW', bebas(96), BG, shadow=False), text_img('اطلب الآن', cairo(52, 'Black'), BG, rtl=True, shadow=False)], h=140, padx=64)
c_hours = text_img('SERVED DAILY  ·  12 PM – CLOSE', mont(34, 'Bold'), CREAM, track=4)
c_hours_ar = text_img('يومياً من ١٢ الظهر حتى الإغلاق', cairo(46, 'SemiBold'), MUTED, rtl=True)
c_dine = text_img('A taste of Yemen', font('Dancing', 58, 'Bold'), GOLD)
end_bg = backdrop('lamb')
base_bg = Image.new('RGBA', (W, H), BG + (255,))

# steam + embers sprites
def blob(size, a):
    m = Image.new('L', (size, size)); ImageDraw.Draw(m).ellipse((size // 4,) * 2 + (size * 3 // 4,) * 2, fill=a)
    im = Image.new('RGBA', (size, size), (255, 245, 235, 255)); im.putalpha(m.filter(ImageFilter.GaussianBlur(size // 7))); return im
STEAM = blob(220, 255)
EMB = Image.new('RGBA', (40, 40)); em = Image.new('L', (40, 40)); ImageDraw.Draw(em).ellipse((14, 14, 26, 26), fill=255)
EMB.paste(Image.new('RGBA', (40, 40), (255, 170, 80, 255)), mask=em.filter(ImageFilter.GaussianBlur(5)))
rng = np.random.default_rng(5)
SP = [(rng.uniform(-1, 1), rng.uniform(0, 1), rng.uniform(0.7, 1.3), rng.uniform(0, 6.28)) for _ in range(16)]
EP = [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(60, 160), rng.uniform(.4, 1), rng.uniform(0, 6.28)) for _ in range(40)]

def steam(f, t, cx, top, spread, alpha=1.0):
    for ox, ph0, sp, ph in SP:
        k = (t * 0.32 * sp + ph0) % 1.0
        x = cx + ox * spread + 50 * math.sin(t * 1.3 + ph) * k
        y = top - k * 520
        a = math.sin(k * math.pi) * 0.13 * alpha
        put(f, STEAM, x, y, a, 0.6 + k * 1.4)

def embers(f, t, alpha=1.0):
    for x0, y0, sp, sz, ph in EP:
        y = (y0 - sp * t) % (H + 80) - 40
        x = x0 + 28 * math.sin(t * .8 + ph)
        a = (0.3 + 0.7 * abs(math.sin(t * 2.2 + ph))) * min(1, y / 500 + .1) * 0.7 * alpha
        put(f, EMB, x, y, a, 0.35 + sz * 0.6)

# ---------- scene renderers (local time t) ----------
def s_hook(f, t):
    put(f, hero, W / 2, 1130, ease(t / .4), 1.0 + 0.06 * t, rot=-3 * t)
    steam(f, t, W / 2, 760, 260)
    k = back((t - .5) / .5); put(f, hook1, W / 2, 250, ease((t - .5) / .2), k)
    k = ease((t - 1.1) / .5); put(f, hook2, W / 2, 440 + 30 * (1 - k), k)

def s_logo(f, t):
    put(f, logo_script, W / 2, 610, ease(t / .5), 0.9 + 0.1 * ease(t / .5))
    k = back((t - .2) / .6); put(f, logo_en, W / 2, 820, ease((t - .2) / .3), 0.7 + 0.3 * k)
    k = ease((t - .7) / .6); put(f, logo_ar, W / 2, 1060, k, 0.85 + 0.15 * k)
    k = eio((t - 1.1) / .6); put(f, rule, W / 2, 1185, k, max(k, .01))
    k = ease((t - 1.3) / .6); put(f, logo_tag, W / 2, 1265 + 20 * (1 - k), k)

def s_dish(f, t, s):
    k = back(t / .7)
    put(f, s['dish'], W / 2, 640, ease(t / .3), 0.6 + 0.4 * k + 0.035 * t, rot=-5 * t)
    steam(f, t, W / 2, 330, 200, ease(t / .8))
    k = ease((t - .15) / .5); put(f, s['num'], 120, 150, k)
    put(f, s['sub_im'], W / 2, 150 + 20 * (1 - k), k)
    k = ease((t - .3) / .5); put(f, s['en_im'], W / 2 - 0, 1105 + 50 * (1 - k), k)
    k = ease((t - .45) / .5); put(f, s['ar_im'], W / 2, 1238 + 30 * (1 - k), k)
    k = ease((t - .6) / .5); put(f, s['desc_im'], W / 2, 1325, k)
    cy = 1365 + s['card_h'] // 2 + 40
    k = ease((t - .75) / .5); put(f, s['card'], W / 2, cy + 40 * (1 - k), k)
    top = cy - s['card_h'] // 2 + 25 + 39
    for j, r in enumerate(s['rows']):
        k = ease((t - .95 - j * .15) / .4); put(f, r, W / 2 + 40 * (1 - k), top + j * 78, k)
    if s['note_im']:
        k = ease((t - 1.5) / .4); put(f, s['note_im'], W / 2, top + len(s['rows']) * 78 + 10, k)

def s_grid(f, t):
    k = ease(t / .5); put(f, g1, W / 2, 230 + 30 * (1 - k), k)
    for i, im in enumerate(grid_imgs):
        cx, cy = 200 + (i % 3) * 340, 560 + (i // 3) * 330
        k = back((t - .2 - i * .08) / .45)
        put(f, im, cx, cy + 6 * math.sin(t * 2 + i), ease((t - .2 - i * .08) / .2), k)
    k = ease((t - 1.3) / .5); put(f, g2, W / 2, 1560, k)
    k = back((t - 1.7) / .5); put(f, g3, W / 2, 1700, ease((t - 1.7) / .2), k)

def s_end(f, t):
    pulse = 1 + 0.012 * math.sin(t * math.pi * 2)
    k = back(t / .7); put(f, logo_en, W / 2, 470, ease(t / .3), (0.75 + 0.25 * k) * pulse)
    k = ease((t - .4) / .6); put(f, logo_ar, W / 2, 700, k, 0.85 + 0.15 * k)
    k = eio((t - .8) / .6); put(f, rule, W / 2, 830, k, max(k, .01))
    k = ease((t - 1.0) / .6); put(f, c_dine, W / 2, 920, k)
    k = back((t - 1.4) / .6)
    put(f, shine(cta, ((t - 2.2) % 2.0) / 0.9), W / 2, 1110, ease((t - 1.4) / .2), k * (1 + 0.02 * math.sin(t * 6)))
    k = ease((t - 1.9) / .6); put(f, c_hours, W / 2, 1300, k)
    k = ease((t - 2.1) / .6); put(f, c_hours_ar, W / 2, 1375, k)
    k = back((t - 2.5) / .5); put(f, g3, W / 2, 1520, ease((t - 2.5) / .2), k * 0.85)

TIMELINE = [(0, 4, 'hook'), (4, 8, 'logo')] + [(8 + 4 * i, 12 + 4 * i, i) for i in range(6)] + [(32, 36, 'grid'), (36, 44, 'end')]
BGS = {'hook': hero_bg, 'logo': base_bg, 'grid': grid_bg, 'end': end_bg}
for i, s in enumerate(SCENES): BGS[i] = s['bg']

# post: vignette + grain
yy, xx = np.mgrid[0:H, 0:W]
VIG = (1 - 0.55 * np.clip(np.sqrt(((xx - W / 2) / (W * .75)) ** 2 + ((yy - H * .45) / (H * .7)) ** 2), 0, 1) ** 2)[..., None].astype(np.float32)
GRAIN = [rng.normal(0, 5, (H, W, 1)).astype(np.float32) for _ in range(4)]

def scene_layer(key, lt):
    f = Image.new('RGBA', (W, H))
    if key == 'hook': s_hook(f, lt)
    elif key == 'logo': s_logo(f, lt)
    elif key == 'grid': s_grid(f, lt)
    elif key == 'end': s_end(f, lt)
    else: s_dish(f, lt, SCENES[key])
    return f

def frame_at(t, n=0):
    for a, b, key in TIMELINE:
        if a <= t < b: break
    lt, T = t - a, b - a
    # background with crossfade from the previous scene
    f = BGS[key].copy()
    idx = TIMELINE.index((a, b, key))
    if idx and lt < .4:
        f = Image.blend(BGS[TIMELINE[idx - 1][2]], f, eio(lt / .4))
    embers(f, t, 0.8 if key in ('logo', 'end') else 0.4)
    layer = scene_layer(key, lt)
    out_k = ease((lt - (T - .3)) / .3) if key != 'end' else 0
    if out_k > 0:   # exit: push forward and fade
        sc = 1 + 0.12 * out_k
        layer = layer.resize((int(W * sc), int(H * sc)), Image.BILINEAR).crop(
            (int((W * sc - W) / 2), int((H * sc - H) / 2), int((W * sc - W) / 2) + W, int((H * sc - H) / 2) + H))
        layer.putalpha(layer.getchannel('A').point(lambda v: int(v * (1 - out_k))))
    f.alpha_composite(layer)
    a = np.asarray(f.convert('RGB')).astype(np.float32)
    if idx and lt < .18:   # warm flash on the cut
        a += (np.array(ORANGE, np.float32) * 0.35) * (1 - lt / .18)
    a = a * VIG + GRAIN[n % 4]
    fade = min(1, t / .4, (DUR - t) / .8)
    a *= max(fade, 0)
    return np.clip(a, 0, 255).astype(np.uint8)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        for ts in sys.argv[1:]:
            Image.fromarray(frame_at(float(ts))).save(f'/tmp/claude-0/-home-user-oncoal/fb0ac52a-6330-5bc9-a2c9-5c62305f79fc/scratchpad/p_{ts}.jpg', quality=88)
        raise SystemExit
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-maxrate', '14M', '-bufsize', '28M', '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
                           'oncoal_promo_v2_nomusic.mp4'], stdin=subprocess.PIPE)
    for n in range(int(DUR * FPS)):
        ff.stdin.write(frame_at(n / FPS, n).tobytes())
        if n % 300 == 0: print(n, flush=True)
    ff.stdin.close(); ff.wait(); print('done')
