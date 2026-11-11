"""Vector drawing primitives for kids' coloring pages.

Every shape is white-filled with a thick round black outline, so later shapes
hide earlier ones (painter's order) and the result is a clean line drawing.
In colour mode a palette maps the same fills to real colours (used on covers).
"""
import math

SW = 7  # default outline width (in 1000-unit art space)
W, H = 1000, 1150  # art canvas


class Pal:
    """c('#hex') -> the colour in colour mode, white in line-art mode."""

    def __init__(self, color=False):
        self.color = color

    def __call__(self, hex_):
        return hex_ if self.color else "#fff"


def _st(w=SW):
    return f'stroke="#000" stroke-width="{w}" stroke-linejoin="round" stroke-linecap="round"'


def circle(cx, cy, r, fill="#fff", w=SW):
    return f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{fill}" {_st(w)}/>'


def ellipse(cx, cy, rx, ry, fill="#fff", rot=0, w=SW):
    t = f' transform="rotate({rot} {cx} {cy})"' if rot else ""
    return f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="{fill}" {_st(w)}{t}/>'


def path(d, fill="#fff", w=SW):
    return f'<path d="{d}" fill="{fill}" {_st(w)}/>'


def line(d, w=SW):
    return path(d, "none", w)


def dot(cx, cy, r):
    return f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="#000"/>'


def rect(x, y, w_, h_, rx=0, fill="#fff", w=SW):
    return f'<rect x="{x}" y="{y}" width="{w_}" height="{h_}" rx="{rx}" fill="{fill}" {_st(w)}/>'


def g(*items, t=""):
    tt = f' transform="{t}"' if t else ""
    return f"<g{tt}>" + "".join(items) + "</g>"


def tube(d, width, fill="#fff", w=SW):
    """A stroked path drawn as an outlined tube (tails, stems, ropes)."""
    return (
        f'<path d="{d}" fill="none" stroke="#000" stroke-width="{width + 2 * w}" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<path d="{d}" fill="none" stroke="{fill}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"/>'
    )


def _bez(p, t):
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = p
    u = 1 - t
    x = u**3 * x0 + 3 * u * u * t * x1 + 3 * u * t * t * x2 + t**3 * x3
    y = u**3 * y0 + 3 * u * u * t * y1 + 3 * u * t * t * y2 + t**3 * y3
    dx = 3 * u * u * (x1 - x0) + 6 * u * t * (x2 - x1) + 3 * t * t * (x3 - x2)
    dy = 3 * u * u * (y1 - y0) + 6 * u * t * (y2 - y1) + 3 * t * t * (y3 - y2)
    n = math.hypot(dx, dy) or 1
    return x, y, -dy / n, dx / n


def bez_pt(p, t):
    x, y, _, _ = _bez(p, t)
    return x, y


def taper(p, w0, w1, fill="#fff", open_start=True, rings=(), w=SW, end_cap=True):
    """Tapered limb along a cubic bezier p=[(x,y)*4]. Start can be left open so
    it blends seamlessly into a body drawn before it."""
    N = 48
    L, R = [], []
    for i in range(N + 1):
        t = i / N
        x, y, nx, ny = _bez(p, t)
        r = (w0 + (w1 - w0) * t) / 2
        L.append((x + nx * r, y + ny * r))
        R.append((x - nx * r, y - ny * r))
    fmt = lambda pt: f"{pt[0]:.1f},{pt[1]:.1f}"
    re = w1 / 2
    cap = f"A{re:.1f},{re:.1f} 0 0 1 {fmt(R[-1])}" if end_cap else f"L{fmt(R[-1])}"
    side = "M" + fmt(L[0]) + "".join("L" + fmt(q) for q in L[1:]) + cap + "".join("L" + fmt(q) for q in reversed(R))
    out = f'<path d="{side}Z" fill="{fill}" stroke="none"/>'
    if open_start:
        out += line(side, w)
    else:
        rs = w0 / 2
        out += line(side + f"A{rs:.1f},{rs:.1f} 0 0 1 {fmt(L[0])}", w)
    for t in rings:
        i = round(t * N)
        out += line(f"M{fmt(L[i])}L{fmt(R[i])}", w * 0.8)
    return out


def fluffy(cx, cy, r, n=12, fill="#fff", ry=None, w=SW, rot=0):
    """Scalloped circle (wool, manes, clouds, bushes)."""
    ry = ry or r
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n + math.radians(rot)
        pts.append((cx + r * math.cos(a), cy + ry * math.sin(a)))
    d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        br = math.hypot(b[0] - a[0], b[1] - a[1]) * 0.56
        d += f"A{br:.1f},{br:.1f} 0 0 1 {b[0]:.1f},{b[1]:.1f}"
    return path(d + "Z", fill, w)


def blob(cx, cy, r, seed=1, n=7, fill="#fff", w=SW):
    """Smooth organic spot (giraffe spots, rocks, puddles)."""
    import random

    rnd = random.Random(seed)
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n + rnd.uniform(-0.2, 0.2)
        rr = r * rnd.uniform(0.75, 1.15)
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    mids = [((pts[i][0] + pts[(i + 1) % n][0]) / 2, (pts[i][1] + pts[(i + 1) % n][1]) / 2) for i in range(n)]
    d = f"M{mids[-1][0]:.1f},{mids[-1][1]:.1f}"
    for i in range(n):
        d += f"Q{pts[i][0]:.1f},{pts[i][1]:.1f} {mids[i][0]:.1f},{mids[i][1]:.1f}"
    return path(d + "Z", fill, w)


def star(cx, cy, r, fill="#fff", w=SW, rot=-90, inner=0.5):
    pts = []
    for i in range(10):
        rr = r if i % 2 == 0 else r * inner
        a = math.radians(rot + 36 * i)
        pts.append(f"{cx + rr * math.cos(a):.1f},{cy + rr * math.sin(a):.1f}")
    return path("M" + "L".join(pts) + "Z", fill, w)


def heart(cx, cy, s=1, fill="#fff", w=SW):
    return g(path("M0,30C-50,-5,-30,-52,0,-25C30,-52,50,-5,0,30Z", fill, w / s), t=f"translate({cx},{cy}) scale({s})")


def poly(pts, fill="#fff", w=SW):
    return path("M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z", fill, w)


# ---------------------------------------------------------------- faces
def eye(cx, cy, r=24):
    return dot(cx, cy, r) + f'<circle cx="{cx - r * .32:.1f}" cy="{cy - r * .34:.1f}" r="{r * .4:.1f}" fill="#fff"/>' + f'<circle cx="{cx + r * .35:.1f}" cy="{cy + r * .3:.1f}" r="{r * .16:.1f}" fill="#fff"/>'


def happy_eye(cx, cy, r=22):
    return line(f"M{cx - r},{cy + 6} Q{cx},{cy - r} {cx + r},{cy + 6}", SW * 1.1)


def blush(cx, cy, c, rx=24, ry=13):
    return ellipse(cx, cy, rx, ry, c("#ffb3c1"), w=4)


def smile(cx, cy, wd=22):
    return line(f"M{cx - wd},{cy} Q{cx},{cy + wd * .9} {cx + wd},{cy}")


def open_smile(cx, cy, wd=26, c=None):
    tongue = ""
    if c:
        tongue = path(f"M{cx - wd * .5},{cy + wd * .55} Q{cx},{cy + wd * .2} {cx + wd * .5},{cy + wd * .55} Q{cx},{cy + wd * 1.05} {cx - wd * .5},{cy + wd * .55}Z", c("#ff8fa3"), 0)
    return path(f"M{cx - wd},{cy} Q{cx},{cy + wd * 1.6} {cx + wd},{cy}Z", "#000" if not c else "#3b1d1d", SW * .8) + tongue


def face(cx, cy, c, dx=70, r=24, mouth="smile", blush_dx=None, mw=22, my=38):
    bd = blush_dx or dx + 30
    out = eye(cx - dx, cy, r) + eye(cx + dx, cy, r)
    out += blush(cx - bd, cy + 42, c) + blush(cx + bd, cy + 42, c)
    if mouth == "smile":
        out += smile(cx, cy + my, mw)
    elif mouth == "open":
        out += open_smile(cx, cy + my - 6, mw, c)
    return out


# ---------------------------------------------------------------- scenery
def ground(y, c, color="#a8e07a", amp=30):
    return path(f"M-20,{y}C250,{y - amp} 650,{y + amp} 1020,{y - amp * .3}L1020,{H + 20}L-20,{H + 20}Z", c(color))


def hill(y, c, color="#c8f0a0", amp=80):
    return path(f"M-20,{y}C200,{y - amp} 450,{y - amp} 600,{y - 10}C750,{y - amp * 1.4} 900,{y - amp} 1020,{y - 20}L1020,{H + 20}L-20,{H + 20}Z", c(color))


def sky_bg(c, color="#d6f0ff"):
    return f'<rect x="-20" y="-20" width="{W + 40}" height="{H + 40}" fill="{c(color)}"/>'


def cloud(cx, cy, s=1, c=None, fill=None):
    f = fill or (c("#ffffff") if c else "#fff")
    d = "M20,90A30,30 0 0 1 40,45A42,42 0 0 1 108,24A36,36 0 0 1 162,48A26,26 0 0 1 182,90A260,60 0 0 1 20,90Z"
    return g(path(d, f, SW / s), t=f"translate({cx - 100 * s},{cy - 60 * s}) scale({s})")


def sun(cx, cy, r, c, face_=True):
    out = ""
    for i in range(12):
        a = math.radians(i * 30)
        r1, r2 = r * 1.25, r * (1.55 if i % 2 == 0 else 1.42)
        out += line(f"M{cx + r1 * math.cos(a):.1f},{cy + r1 * math.sin(a):.1f}L{cx + r2 * math.cos(a):.1f},{cy + r2 * math.sin(a):.1f}", SW * 1.3)
    out += circle(cx, cy, r, c("#ffd84d"))
    if face_:
        s = r / 70
        out += happy_eye(cx - 24 * s, cy - 6 * s, 12 * s) + happy_eye(cx + 24 * s, cy - 6 * s, 12 * s)
        out += smile(cx, cy + 18 * s, 18 * s) + blush(cx - 42 * s, cy + 14 * s, c, 12 * s, 7 * s) + blush(cx + 42 * s, cy + 14 * s, c, 12 * s, 7 * s)
    return out


def moon(cx, cy, r, c):
    d = f"M{cx},{cy - r}A{r},{r} 0 1 0 {cx},{cy + r}A{r * .75},{r * .9} 0 1 1 {cx},{cy - r}Z"
    return path(d, c("#fff3a8")) + happy_eye(cx - r * .55, cy - r * .1, r * .14) + smile(cx - r * .5, cy + r * .3, r * .14)


def tuft(x, y, s=1):
    return line(f"M{x - 16 * s},{y}L{x - 20 * s},{y - 26 * s}M{x - 4 * s},{y}L{x - 2 * s},{y - 36 * s}M{x + 10 * s},{y}L{x + 18 * s},{y - 26 * s}", SW * .9)


def flower(x, y, s, c, petal="#ff9ec7", center="#ffd84d", stem_h=110, n=6):
    out = tube(f"M{x},{y}Q{x - 8 * s},{y + stem_h * .5} {x},{y + stem_h}", 10 * s, c("#7cc96b"))
    out += ellipse(x + 26 * s, y + stem_h * .62, 24 * s, 11 * s, c("#7cc96b"), rot=-30)
    for i in range(n):
        a = 2 * math.pi * i / n
        out += circle(x + 24 * s * math.cos(a), y + 24 * s * math.sin(a), 18 * s, c(petal))
    out += circle(x, y, 16 * s, c(center))
    return out


def mushroom(x, y, s, c):
    out = path(f"M{x - 22 * s},{y}Q{x - 26 * s},{y - 50 * s} {x - 18 * s},{y - 60 * s}L{x + 18 * s},{y - 60 * s}Q{x + 26 * s},{y - 50 * s} {x + 22 * s},{y}Z", c("#fff4e0"))
    out += path(f"M{x - 70 * s},{y - 55 * s}Q{x - 70 * s},{y - 135 * s} {x},{y - 135 * s}Q{x + 70 * s},{y - 135 * s} {x + 70 * s},{y - 55 * s}Q{x},{y - 40 * s} {x - 70 * s},{y - 55 * s}Z", c("#ff6b6b"))
    out += circle(x - 30 * s, y - 95 * s, 13 * s, c("#fff")) + circle(x + 22 * s, y - 108 * s, 10 * s, c("#fff")) + circle(x + 40 * s, y - 75 * s, 8 * s, c("#fff"))
    return out


def butterfly(x, y, s, c, col="#b39cff"):
    out = ellipse(x - 30 * s, y - 20 * s, 32 * s, 26 * s, c(col), rot=-25) + ellipse(x + 30 * s, y - 20 * s, 32 * s, 26 * s, c(col), rot=25)
    out += ellipse(x - 24 * s, y + 18 * s, 22 * s, 18 * s, c("#ffb3e6"), rot=25) + ellipse(x + 24 * s, y + 18 * s, 22 * s, 18 * s, c("#ffb3e6"), rot=-25)
    out += circle(x - 32 * s, y - 22 * s, 9 * s, c("#fff")) + circle(x + 32 * s, y - 22 * s, 9 * s, c("#fff"))
    out += ellipse(x, y, 9 * s, 36 * s, c("#5b4a8a"))
    out += line(f"M{x - 3 * s},{y - 34 * s}Q{x - 10 * s},{y - 60 * s} {x - 24 * s},{y - 64 * s}M{x + 3 * s},{y - 34 * s}Q{x + 10 * s},{y - 60 * s} {x + 24 * s},{y - 64 * s}", SW * .7)
    return out


def bee(x, y, s, c, flip=False):
    out = ellipse(x - 8 * s, y - 34 * s, 20 * s, 28 * s, c("#e8f7ff"), rot=-20) + ellipse(x + 14 * s, y - 32 * s, 18 * s, 26 * s, c("#e8f7ff"), rot=20)
    out += ellipse(x, y, 44 * s, 30 * s, c("#ffd84d"))
    out += line(f"M{x - 8 * s},{y - 28 * s}Q{x - 14 * s},{y} {x - 8 * s},{y + 28 * s}M{x + 12 * s},{y - 27 * s}Q{x + 6 * s},{y} {x + 12 * s},{y + 27 * s}", SW * 1.6)
    out += path(f"M{x - 44 * s},{y - 4 * s}L{x - 60 * s},{y}L{x - 44 * s},{y + 6 * s}Z", "#000", SW * .6)
    out += eye(x + 28 * s, y - 6 * s, 6 * s) + smile(x + 30 * s, y + 10 * s, 7 * s)
    return g(out, t=f"translate({2 * x},0) scale(-1,1)") if flip else out


def tree(x, y, s, c, kind="round"):
    out = path(f"M{x - 28 * s},{y}Q{x - 18 * s},{y - 90 * s} {x - 20 * s},{y - 170 * s}L{x + 20 * s},{y - 170 * s}Q{x + 18 * s},{y - 90 * s} {x + 28 * s},{y}Z", c("#b07a4f"))
    out += fluffy(x, y - 240 * s, 115 * s, 11, c("#7cc96b"))
    out += circle(x - 40 * s, y - 250 * s, 13 * s, c("#ff6b6b")) + circle(x + 35 * s, y - 210 * s, 13 * s, c("#ff6b6b")) + circle(x + 20 * s, y - 290 * s, 13 * s, c("#ff6b6b"))
    return out


def acacia(x, y, s, c):
    out = path(f"M{x - 16 * s},{y}Q{x - 8 * s},{y - 80 * s} {x - 40 * s},{y - 150 * s}L{x - 22 * s},{y - 158 * s}Q{x},{y - 110 * s} {x + 6 * s},{y - 120 * s}Q{x + 20 * s},{y - 150 * s} {x + 40 * s},{y - 165 * s}L{x + 52 * s},{y - 152 * s}Q{x + 20 * s},{y - 110 * s} {x + 16 * s},{y}Z", c("#b07a4f"))
    out += fluffy(x, y - 190 * s, 150 * s, 16, c("#8fd16e"), ry=45 * s)
    return out


def palm(x, y, s, c, lean=40):
    p = [(x, y), (x + lean * .3 * s, y - 120 * s), (x + lean * .8 * s, y - 220 * s), (x + lean * s, y - 300 * s)]
    out = taper(p, 46 * s, 30 * s, c("#c98d5a"), open_start=False, rings=(.15, .3, .45, .6, .75, .88), end_cap=True)
    tx, ty = p[3]
    for ang, ln in [(-160, 150), (-125, 140), (-60, 145), (-20, 150), (20, 120), (160, 120)]:
        a = math.radians(ang)
        ex, ey = tx + ln * s * math.cos(a), ty + ln * s * math.sin(a) + 40 * s
        mx, my = tx + ln * .5 * s * math.cos(a), ty + ln * .5 * s * math.sin(a) - 35 * s
        out += path(f"M{tx},{ty}Q{mx},{my - 20 * s} {ex},{ey}Q{mx},{my + 30 * s} {tx},{ty}Z", c("#6cc25a"))
        out += line(f"M{tx},{ty}Q{mx},{my + 5 * s} {ex},{ey}", SW * .6)
    for dx, dy in [(-14, 14), (12, 16), (0, 30)]:
        out += circle(tx + dx * s, ty + dy * s, 13 * s, c("#8a4b2a"))
    return out


def fence(y, c, x0=-20, x1=1020, step=95):
    out = rect(x0, y + 20, x1 - x0, 24, 6, c("#e0b081")) + rect(x0, y + 80, x1 - x0, 24, 6, c("#e0b081"))
    x = x0 + 30
    while x < x1:
        out += path(f"M{x},{y + 140}L{x},{y}L{x + 24},{y - 26}L{x + 48},{y}L{x + 48},{y + 140}Z", c("#f2c999"))
        x += step
    return out


def bubbles(pts, c):
    out = ""
    for x, y, r in pts:
        out += circle(x, y, r, c("#e3f6ff"), SW * .8) + line(f"M{x - r * .55},{y - r * .1}A{r * .6},{r * .6} 0 0 1 {x - r * .1},{y - r * .55}", SW * .6)
    return out


def sparkle(x, y, s=1):
    return line(f"M{x},{y - 22 * s}L{x},{y + 22 * s}M{x - 22 * s},{y}L{x + 22 * s},{y}", SW * .8)
