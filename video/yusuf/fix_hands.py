"""Keep Yusuf's original hands and add the missing fingers in the same style (5 per hand).

Original right hand (raised, image right): thumb + 2 fingers -> add ring + little finger below them.
Original left hand (image left): thumb + 2 fingers -> add index (up-left) + little finger (below).
New fingers are drawn UNDER the original sprite so the original palm covers their bases.
Writes yusuf_hands.png.
"""
import math
from PIL import Image, ImageDraw, ImageFilter

SS = 4
SKIN, SHADE, HL, LINE = (253, 199, 158), (236, 164, 124), (255, 222, 194), (70, 34, 24)
src = Image.open('yusuf_clean.png').convert('RGBA')
Wd, Ht = src.size
S = lambda p: (p[0] * SS, p[1] * SS)


def capsule(d, p0, p1, w, fill):
    d.line([S(p0), S(p1)], fill=fill, width=int(w * SS))
    for p in (p0, p1):
        r = w * SS / 2; c = S(p)
        d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=fill)


def finger(d, base, tip, w):
    """Finger in the original's style: dark outline, skin fill, soft shade on the lower edge, tip highlight."""
    dx, dy = tip[0] - base[0], tip[1] - base[1]; L = math.hypot(dx, dy); ux, uy = dx / L, dy / L
    nx, ny = -uy, ux
    if ny < 0: nx, ny = -nx, -ny          # shade on the lower side
    capsule(d, base, tip, w + 5.5, LINE)
    capsule(d, base, tip, w, SKIN)
    o = w * 0.22
    capsule(d, (base[0] + nx * o, base[1] + ny * o), (tip[0] - ux * w * 0.35 + nx * o, tip[1] - uy * w * 0.35 + ny * o), w * 0.45, SHADE)
    capsule(d, (base[0] - nx * o * 0.4, base[1] - ny * o * 0.4), (tip[0] - ux * w * 0.3 - nx * o * 0.4, tip[1] - uy * w * 0.3 - ny * o * 0.4), w * 0.42, SKIN)
    hx, hy = tip[0] - ux * w * 0.35 - nx * w * 0.12, tip[1] - uy * w * 0.35 - ny * w * 0.12
    r = w * 0.17
    d.ellipse([S((hx - r * 1.4, hy - r)), S((hx + r * 1.4, hy + r))], fill=HL)
    kx, ky = base[0] + ux * L * 0.55, base[1] + uy * L * 0.55          # knuckle crease
    d.line([S((kx - nx * w * 0.25, ky - ny * w * 0.25)), S((kx + nx * w * 0.15, ky + ny * w * 0.15))], fill=SHADE + (255,), width=2 * SS)


layer = Image.new('RGBA', (Wd * SS, Ht * SS)); d = ImageDraw.Draw(layer)
# right hand: ring + little finger under the middle finger (pointing up-right like the others)
finger(d, (782, 398), (836, 350), 24)
finger(d, (778, 425), (826, 395), 21)
# left hand: index between thumb and the left-pointing finger, little finger under the lowest finger
finger(d, (184, 468), (126, 412), 25)
finger(d, (198, 568), (134, 606), 22)
layer = layer.resize((Wd, Ht), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.4))

out = Image.new('RGBA', (Wd, Ht)); out.alpha_composite(layer); out.alpha_composite(src)
out.save('yusuf_hands.png')
print('saved yusuf_hands.png')
