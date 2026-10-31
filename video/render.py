"""Render the Oncoal promo (1080x1920, 30 fps) and mux with music.wav."""
import math, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS, DUR = 1080, 1920, 30, 44.0
BG, CARD = (36, 24, 19), (58, 42, 34)
ORANGE, CREAM = (232, 146, 74), (243, 230, 211)

def font(name, size, var=None):
    f = ImageFont.truetype(f'fonts/{name}.ttf', size, layout_engine=ImageFont.Layout.RAQM)
    if var: f.set_variation_by_name(var)
    return f

def text_img(s, f, fill, rtl=False, spacing=0, glow=None):
    kw = {'direction': 'rtl', 'language': 'ar'} if rtl else {}
    if spacing:
        s = ' '.join(s) if spacing == 1 else s
    l, t, r, b = f.getbbox(s, **kw)
    pad = 40
    im = Image.new('RGBA', (r - l + pad * 2, b - t + pad * 2))
    ImageDraw.Draw(im).text((pad - l, pad - t), s, font=f, fill=fill, **kw)
    if glow:
        g = Image.new('RGBA', im.size)
        ImageDraw.Draw(g).text((pad - l, pad - t), s, font=f, fill=glow, **kw)
        g = g.filter(ImageFilter.GaussianBlur(18))
        im = Image.alpha_composite(g, im)
    return im

def dish(name, d, ring=10):
    src = Image.open(f'assets/{name}.png').convert('RGB')
    w, h = src.size
    m = int(min(w, h) * 0.07)                       # trim the menu's own ring
    src = src.crop((m, m, w - m, h - m)).resize((d, d), Image.BICUBIC)
    src = src.filter(ImageFilter.UnsharpMask(3, 90, 2))
    S = d + ring * 2 + 120
    out = Image.new('RGBA', (S, S))
    c = S // 2
    glow = Image.new('L', (S, S))
    ImageDraw.Draw(glow).ellipse((c - d // 2 - ring - 10,) * 2 + (c + d // 2 + ring + 10,) * 2, fill=150)
    glow = glow.filter(ImageFilter.GaussianBlur(30))
    out.paste(Image.new('RGBA', (S, S), ORANGE + (255,)), mask=glow)
    ImageDraw.Draw(out).ellipse((c - d // 2 - ring,) * 2 + (c + d // 2 + ring,) * 2, fill=ORANGE)
    mask = Image.new('L', (d * 2, d * 2))
    ImageDraw.Draw(mask).ellipse((0, 0, d * 2 - 1, d * 2 - 1), fill=255)
    out.paste(src, (c - d // 2, c - d // 2), mask.resize((d, d), Image.LANCZOS))
    return out

def ease(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3
def back(x):
    x = min(max(x, 0), 1); c = 1.70158
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2

def put(frame, im, cx, cy, alpha=1.0, scale=1.0, rot=0):
    if alpha <= 0.01 or scale <= 0.01: return
    if rot: im = im.rotate(rot, Image.BICUBIC)
    if abs(scale - 1) > 0.005:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
    if alpha < 0.999:
        a = im.getchannel('A').point(lambda v: int(v * alpha))
        im = im.copy(); im.putalpha(a)
    frame.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

def pill(parts, h=110, padx=46):
    widths = [p.width - 80 for p in parts]
    w = sum(widths) + padx * 2 + 24 * (len(parts) - 1)
    im = Image.new('RGBA', (w, h))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, w - 1, h - 1), h // 2, fill=ORANGE)
    x = padx
    for p, pw in zip(parts, widths):
        im.alpha_composite(p, (x - 40, h // 2 - p.height // 2))
        x += pw + 24
    return im

# ---------- static assets ----------
bebas = lambda s: font('Bebas', s)
cairo = lambda s, v='Bold': font('Cairo', s, v)
F = {
    'script': font('Dancing', 64, 'Bold'),
    'label': font('Montserrat', 34, 'Bold'),
}
bg = Image.new('RGBA', (W, H), BG + (255,))
yy, xx = np.mgrid[0:H, 0:W]
r = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H * 0.42) / H) ** 2)
v = np.clip(1 - r * 1.3, 0, 1)[..., None]
base = np.array(BG, float)
arr = base * (0.55 + 0.75 * v) + np.array([40, 18, 0]) * v ** 3
bg = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert('RGBA')

ember = Image.new('RGBA', (40, 40))
eg = Image.new('L', (40, 40)); ImageDraw.Draw(eg).ellipse((14, 14, 26, 26), fill=255)
ember.paste(Image.new('RGBA', (40, 40), (255, 160, 70, 255)), mask=eg.filter(ImageFilter.GaussianBlur(5)))
rng = np.random.default_rng(3)
P = [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(40, 140), rng.uniform(0.3, 1.0), rng.uniform(0, 6.28)) for _ in range(55)]
ember_sizes = {s: ember.resize((s, s), Image.BILINEAR) for s in range(8, 41, 4)}

def embers(frame, t):
    for x0, y0, sp, sz, ph in P:
        y = (y0 - sp * t) % (H + 80) - 40
        x = x0 + 30 * math.sin(t * 0.8 + ph)
        a = (0.4 + 0.6 * abs(math.sin(t * 2 + ph))) * min(1, y / 400 + 0.2)
        s = 8 + int(sz * 32) // 4 * 4
        put(frame, ember_sizes[min(s, 40)], x, y, alpha=max(0, a) * 0.8)

SCENES = [
    dict(en='CHICKEN', ar='دجاج', items='مندي · شواية · مشوي على الفحم', price='$11.99', img='chicken', sats=['full_mandi', 'half_mandi']),
    dict(en='LAMB', ar='لحم', items='مندي · مظبي · محمّر', price='$24.99', img='lamb', sats=['mazbi', 'double_mandi']),
    dict(en='MIX PLATTERS', ar='مكس', items='دجاج ولحم في صحن واحد', price='$22.99', img='mix', sats=[]),
    dict(en='FISH & SIDES', ar='سمك', items='سمك مقلي · سمك مشوي · ملوخية', price='$3.99', img='fish', sats=['molokhia', 'lamb_edam']),
    dict(en='BROASTED', ar='بروستد', items='٤ · ٨ · ١٢ قطعة مع البطاطس', price='$16.99', img='broasted', sats=[]),
    dict(en='BAKERY & DESSERT', ar='مخبوزات وحلا', items='مطبق · فطيرة · معصوب · عريكة', price='$5.99', img='mutabaq', sats=['massoub']),
]
for i, s in enumerate(SCENES):
    s['label'] = text_img(f'{i + 1:02d}  ·  {s["en"]}', F['label'], ORANGE)
    s['line'] = Image.new('RGBA', (220, 4), ORANGE + (255,))
    s['ar_img'] = text_img(s['ar'], cairo(170, 'Black'), CREAM, rtl=True, glow=ORANGE + (120,))
    s['items_img'] = text_img(s['items'], cairo(52, 'SemiBold'), CREAM, rtl=True)
    s['pill'] = pill([text_img(s['price'], bebas(84), BG), text_img('ابتداءً من', cairo(46, 'Bold'), BG, rtl=True)])
    s['dish'] = dish(s['img'], 600)
    s['sat_imgs'] = [dish(n, 210, 7) for n in s['sats']]

logo_en = text_img('ONCOAL', bebas(300), CREAM, glow=ORANGE + (200,))
logo_ar = text_img('اونكول', font('Ruqaa', 170), ORANGE, rtl=True)
intro_script = text_img('Special & Delicious', F['script'], ORANGE)
intro_tag = text_img('مطبخ يمني أصيل على الفحم', cairo(60, 'SemiBold'), CREAM, rtl=True)
letters = [text_img(c, bebas(300), CREAM, glow=ORANGE + (200,)) for c in 'ONCOAL']

GRID = ['chicken', 'lamb', 'mix', 'full_mandi', 'broasted', 'mazbi', 'fish', 'massoub', 'mutabaq']
grid_imgs = [dish(n, 270, 6) for n in GRID]
g_t1 = text_img('كل الأطباق تُقدّم مع الرز والصوصات', cairo(56, 'Bold'), CREAM, rtl=True)
g_pill = pill([text_img('100% ZABIHAH HALAL', bebas(70), BG), text_img('حلال', cairo(46, 'Black'), BG, rtl=True)])

o_tag = text_img('على الفحم · بطعم اليمن', cairo(62, 'Bold'), CREAM, rtl=True)
o_hours_ar = text_img('يومياً من ١٢ الظهر حتى الإغلاق', cairo(50, 'SemiBold'), CREAM, rtl=True)
o_hours_en = text_img('SERVED DAILY  ·  12 PM – CLOSE', F['label'], ORANGE)
o_cta = pill([text_img('زورونا اليوم', cairo(54, 'Black'), BG, rtl=True)], h=120, padx=60)
divider = Image.new('RGBA', (520, 3), ORANGE + (200,))

# ---------- scenes ----------
def scene_intro(f, t):
    put(f, intro_script, W / 2, 620, ease(t / .6), 0.9 + 0.1 * ease(t / .6))
    x0 = W / 2 - 3 * 150 + 75
    for i, L in enumerate(letters):
        k = ease((t - 0.4 - i * 0.09) / 0.5)
        put(f, L, x0 + i * 150 + (0 if i < 5 else -6), 860 + 80 * (1 - k), k)
    k = ease((t - 1.3) / .6); put(f, logo_ar, W / 2, 1100, k, 0.85 + 0.15 * k)
    k = ease((t - 2.0) / .6); put(f, divider, W / 2, 1240, k, k)
    k = ease((t - 2.2) / .6); put(f, intro_tag, W / 2, 1330 + 30 * (1 - k), k)

def scene_dish(f, t, s, T=4.0):
    out = ease((t - (T - .35)) / .35)
    a = 1 - out; dx = -260 * out
    k = ease(t / .5);  put(f, s['label'], W / 2 + dx, 250, k * a)
    put(f, s['line'], W / 2 + dx, 305, k * a, k)
    k = back(t / .7);  put(f, s['dish'], W / 2 + dx, 760, ease(t / .3) * a, 0.55 + 0.45 * k + 0.03 * t / T, rot=-6 * t)
    pos = [(860, 1010), (220, 1010)]
    for j, im in enumerate(s['sat_imgs']):
        k = back((t - .7 - j * .15) / .5)
        put(f, im, pos[j][0] + dx, pos[j][1], ease((t - .7 - j * .15) / .2) * a, k, rot=8 * t)
    k = ease((t - .35) / .5); put(f, s['ar_img'], W / 2 + dx, 1250 + 60 * (1 - k), k * a)
    k = ease((t - .6) / .5);  put(f, s['items_img'], W / 2 + dx, 1420 + 40 * (1 - k), k * a)
    k = back((t - .95) / .5); put(f, s['pill'], W / 2 + dx, 1580, ease((t - .95) / .2) * a, k)

def scene_grid(f, t, T=8.0):
    a = 1 - ease((t - (T - .4)) / .4)
    for i, im in enumerate(grid_imgs):
        cx, cy = 210 + (i % 3) * 330, 450 + (i // 3) * 330
        k = back((t - i * .12) / .5)
        put(f, im, cx, cy + 6 * math.sin(t * 2 + i), ease((t - i * .12) / .2) * a, k)
    k = ease((t - 1.6) / .6); put(f, g_t1, W / 2, 1520 + 40 * (1 - k), k * a)
    k = back((t - 2.2) / .5); put(f, g_pill, W / 2, 1680, ease((t - 2.2) / .2) * a, k)

def scene_outro(f, t, T=8.0):
    pulse = 1 + 0.015 * math.sin(t * math.pi * 2)
    k = back(t / .7);         put(f, logo_en, W / 2, 640, ease(t / .3), k * pulse)
    k = ease((t - .5) / .6);  put(f, logo_ar, W / 2, 900, k, 0.85 + 0.15 * k)
    k = ease((t - 1.0) / .6); put(f, divider, W / 2, 1040, k, k)
    k = ease((t - 1.2) / .6); put(f, o_tag, W / 2, 1140 + 30 * (1 - k), k)
    k = ease((t - 1.6) / .6); put(f, o_hours_ar, W / 2, 1260 + 30 * (1 - k), k)
    k = ease((t - 1.8) / .6); put(f, o_hours_en, W / 2, 1340, k)
    k = back((t - 2.4) / .5); put(f, o_cta, W / 2, 1520, ease((t - 2.4) / .2), k)

def frame_at(t):
    f = bg.copy()
    embers(f, t)
    if t < 4:
        scene_intro(f, t)
        k = ease((t - 3.6) / .4)
        if k > 0: f = Image.blend(f, bg, k)
    elif t < 28:
        i = int((t - 4) // 4); scene_dish(f, (t - 4) - i * 4, SCENES[i])
    elif t < 36:
        scene_grid(f, t - 28)
    else:
        scene_outro(f, t - 36)
    fade = min(1, t / .5, (DUR - t) / .8)
    if fade < 1:
        f = Image.blend(Image.new('RGBA', (W, H), (0, 0, 0, 255)), f, max(fade, 0))
    return f.convert('RGB')

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:      # preview stills
        for ts in sys.argv[1:]:
            frame_at(float(ts)).save(f'/tmp/claude-0/-home-user-oncoal/fb0ac52a-6330-5bc9-a2c9-5c62305f79fc/scratchpad/f_{ts}.jpg', quality=85)
        raise SystemExit
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-i', 'music.wav', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
                           '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', 'oncoal_promo.mp4'], stdin=subprocess.PIPE)
    for n in range(int(DUR * FPS)):
        ff.stdin.write(frame_at(n / FPS).tobytes())
        if n % 150 == 0: print(n, flush=True)
    ff.stdin.close(); ff.wait()
    print('done')
