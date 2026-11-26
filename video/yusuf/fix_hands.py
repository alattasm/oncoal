"""Redraw Yusuf's hands with correct anatomy (5 fingers each) and bake a bubble wand into a real grip.

Right hand (image right): fist wrapped around the wand stick - 4 curled fingers + thumb over them.
Left hand (image left): open waving hand - thumb + 4 spread fingers.
Writes yusuf_hands.png and prints the ring centre (source px) used as bubble emitter.
"""
import math, json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SS = 4                                   # supersampling
SKIN, SKIN_SH, SKIN_HL = (253, 199, 158), (238, 168, 128), (255, 220, 190)
LINE = (70, 34, 24)
src = Image.open('yusuf_clean.png').convert('RGBA')
A = np.array(src).astype(int)
Wd, Ht = src.size
is_blue = lambda px: (px[..., 2] > px[..., 0] + 50) & (px[..., 3] > 30)


SKINM = (A[..., 0] > 205) & (A[..., 1] > 130) & (A[..., 2] > 95) & (A[..., 0] - A[..., 2] > 40) & (A[..., 3] > 30)
SKIN_NEAR = np.array(Image.fromarray((SKINM * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(9))) > 0


def erase(poly, keep_blue=True, extra_keep=None, skin_only=True):
    m = Image.new('L', src.size); ImageDraw.Draw(m).polygon(poly, fill=255)
    m = (np.array(m) > 0) & (SKIN_NEAR if skin_only else True)   # right hand: skin only, never hair
    if keep_blue: m &= ~is_blue(A)
    if extra_keep is not None: m &= ~extra_keep
    A[m, 3] = 0
    return m


# --- erase original hands (only non-blue pixels inside hand polygons) ---
yy, xx = np.mgrid[0:Ht, 0:Wd]
ear = (xx < 735) & (yy < 372)            # protect ear / hair
erase([(690, 380), (730, 360), (760, 300), (790, 250), (815, 260), (840, 270), (850, 330), (820, 400), (810, 470),
       (820, 540), (700, 540), (695, 460)], extra_keep=ear)
erase([(40, 470), (60, 400), (140, 380), (170, 360), (230, 380), (260, 440), (300, 500), (310, 640), (200, 640), (90, 600), (40, 540)], skin_only=False)
sl = (xx > 700) & (xx < 748) & (yy > 465) & (yy < 515) & ~is_blue(A)   # leftover wrist sliver by the cuff
A[sl, 3] = 0
base = Image.fromarray(A.astype(np.uint8))
cuffs = np.array(Image.open('yusuf_clean.png').convert('RGBA'))
cuff_mask = is_blue(cuffs.astype(int)) & (((xx > 690) & (xx < 860) & (yy > 440) & (yy < 600)) | ((xx > 150) & (xx < 340) & (yy > 480) & (yy < 680)))
cuff_layer = np.zeros_like(cuffs); cuff_layer[cuff_mask] = cuffs[cuff_mask]
cuff_layer = Image.fromarray(cuff_layer)

# hi-res drawing layers
L_stick = Image.new('RGBA', (Wd * SS, Ht * SS)); ds = ImageDraw.Draw(L_stick)
L_hand = Image.new('RGBA', (Wd * SS, Ht * SS)); dh = ImageDraw.Draw(L_hand)
S = lambda p: (p[0] * SS, p[1] * SS)


def capsule(d, p0, p1, w, fill, outline=None, ow=0):
    """Rounded finger segment p0->p1 of width w (source px)."""
    for col, ww in ([(outline, w + 2 * ow)] if outline else []) + [(fill, w)]:
        d.line([S(p0), S(p1)], fill=col, width=int(ww * SS))
        for p in (p0, p1):
            r = ww * SS / 2; c = S(p)
            d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=col)


def ellipse(d, c, rx, ry, fill, outline=None, ow=0):
    if outline:
        d.ellipse([S((c[0] - rx - ow, c[1] - ry - ow)), S((c[0] + rx + ow, c[1] + ry + ow))], fill=outline)
    d.ellipse([S((c[0] - rx, c[1] - ry)), S((c[0] + rx, c[1] + ry))], fill=fill)


# ================= RIGHT HAND: fist gripping the wand =================
ang = math.radians(-24)                  # stick tilt (top leans right)
ux, uy = math.sin(-ang) * -1, -math.cos(ang)   # unit vector pointing up the stick
ux, uy = -math.sin(ang), -math.cos(ang)
fx, fy = 772, 418                        # fist centre
px_, py_ = -uy, ux                       # perpendicular (across the fist)
stick_bot = (fx - ux * 44, fy - uy * 44)
stick_top = (fx + ux * 215, fy + uy * 215)
ring_c = (stick_top[0] + ux * 70, stick_top[1] + uy * 70)
# stick (behind fingers)
capsule(ds, stick_bot, stick_top, 15, (175, 125, 255), (85, 55, 150), 4)
capsule(ds, (stick_bot[0] - px_ * 3, stick_bot[1] - py_ * 3), (stick_top[0] - px_ * 3, stick_top[1] - py_ * 3), 4, (215, 185, 255))
# ring
R = 66
for col, w in (((85, 55, 150), 26), ((255, 110, 195), 17), ((255, 175, 225), 5)):
    ds.ellipse([S((ring_c[0] - R, ring_c[1] - R)), S((ring_c[0] + R, ring_c[1] + R))], outline=col, width=int(w * SS))
# soap film inside ring
film = Image.new('RGBA', L_stick.size); ImageDraw.Draw(film).ellipse([S((ring_c[0] - R + 8, ring_c[1] - R + 8)), S((ring_c[0] + R - 8, ring_c[1] + R - 8))], fill=(200, 230, 255, 60))
L_stick.alpha_composite(film, (0, 0)); L_stick = Image.alpha_composite(film, L_stick)
ds = ImageDraw.Draw(L_stick)

# wrist / back of hand going down into the cuff
capsule(dh, (fx + 4, fy + 20), (fx + 6, 492), 50, SKIN, LINE, 3)
# four curled fingers wrapping the stick, stacked along the stick axis (index on top)
W_F = 25
for k in range(4):
    off = 30 - k * 21                    # along stick
    cx, cy = fx + ux * off, fy + uy * off
    half = 37 - k * 2.5                  # little finger slightly shorter
    a = (cx - px_ * half, cy - py_ * half); b = (cx + px_ * (half - 4), cy + py_ * (half - 4))
    capsule(dh, a, b, W_F, SKIN, LINE, 3)
# finger shading + knuckle highlights (redrawn on top for depth)
for k in range(4):
    off = 30 - k * 21; cx, cy = fx + ux * off, fy + uy * off; half = 37 - k * 2.5
    a = (cx - px_ * (half - 6) - ux * 4, cy - py_ * (half - 6) - uy * 4)
    b = (cx + px_ * (half - 10) - ux * 4, cy + py_ * (half - 10) - uy * 4)
    capsule(dh, a, b, 7, SKIN_SH)
    hx, hy = cx + px_ * (half - 14) + ux * 5, cy + py_ * (half - 14) + uy * 5
    ellipse(dh, (hx, hy), 6, 3.5, SKIN_HL)
# thumb: comes from the side and wraps over the index finger
t0 = (fx - px_ * 34 - ux * 4, fy - py_ * 34 - uy * 4)
t1 = (fx - px_ * 2 + ux * 46, fy - py_ * 2 + uy * 46)
capsule(dh, t0, t1, 27, SKIN, LINE, 3)
capsule(dh, (t0[0] + ux * 2 + px_ * 6, t0[1] + uy * 2 + py_ * 6), (t1[0] - px_ * 1, t1[1] - py_ * 1), 8, SKIN_HL)
# thumbnail
nx, ny = t1[0] - ux * 4 + px_ * 1, t1[1] - uy * 4 + py_ * 1
ellipse(dh, (nx, ny), 6, 5, (255, 225, 210), LINE, 1.5)

# ================= LEFT HAND: open, waving, 5 fingers =================
pc = (205, 515)                          # palm centre
capsule(dh, (pc[0] + 20, pc[1] + 25), (255, 615), 56, SKIN, LINE, 3)       # wrist into cuff
fingers = [  # base, tip, width   (pinky -> index), then thumb
    ((180, 548), (112, 572), 21),
    ((172, 525), (92, 518), 23),
    ((176, 502), (98, 462), 24),
    ((192, 483), (140, 418), 23),
]
for b, t, w in fingers:
    capsule(dh, b, t, w, SKIN, LINE, 3)
thumb = ((232, 488), (262, 425), 25)
capsule(dh, thumb[0], thumb[1], thumb[2], SKIN, LINE, 3)
ellipse(dh, pc, 46, 48, SKIN, LINE, 3)
# re-fill to merge palm with finger bases (keeps outer outline, hides inner seams)
for b, t, w in fingers + [thumb]:
    mid = (b[0] + (t[0] - b[0]) * 0.25, b[1] + (t[1] - b[1]) * 0.25)
    capsule(dh, b, mid, w - 1, SKIN)
ellipse(dh, pc, 44, 46, SKIN)
capsule(dh, (pc[0] + 20, pc[1] + 25), (250, 600), 52, SKIN)
# palm creases & shading
dh.arc([S((168, 480)), S((238, 560))], 120, 220, fill=SKIN_SH + (255,), width=3 * SS)
for b, t, w in fingers + [thumb]:       # fingertip highlights + nails hint
    hx, hy = t[0] + (b[0] - t[0]) * 0.12, t[1] + (b[1] - t[1]) * 0.12
    ellipse(dh, (hx, hy), w * 0.22, w * 0.16, SKIN_HL)

# ----------- composite -----------
down = lambda im: im.resize((Wd, Ht), Image.LANCZOS)
out = base.copy()
out.alpha_composite(down(L_stick))
out.alpha_composite(down(L_hand))
out.alpha_composite(cuff_layer)
out.save('yusuf_hands.png')
json.dump({'ring': ring_c, 'ring_r': R}, open('yusuf_hands.json', 'w'))
print('ring centre', [round(v, 1) for v in ring_c])
