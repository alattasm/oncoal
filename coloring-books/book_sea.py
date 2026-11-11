"""Book 2: Under the sea (عالم البحر العجيب)."""
from prims import *


def soft_star(cx, cy, r, inner=.52, fill="#fff", w=SW, rot=-90):
    pts = []
    for i in range(10):
        rr = r if i % 2 == 0 else r * inner
        a = math.radians(rot + 36 * i)
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    mid = lambda a, b: ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    d = "M%.1f,%.1f" % mid(pts[-1], pts[0])
    for i in range(10):
        m = mid(pts[i], pts[(i + 1) % 10])
        d += "Q%.1f,%.1f %.1f,%.1f" % (pts[i][0], pts[i][1], m[0], m[1])
    return path(d + "Z", fill, w)


def seaweed(x, y, h, c, s=1, flip=1):
    return taper([(x, y), (x - 45 * flip * s, y - h * .35), (x + 45 * flip * s, y - h * .7), (x, y - h)], 34 * s, 16 * s, c("#6cc25a"), open_start=False)


def coral(x, y, s, c, col="#ff8fa3"):
    d = f"M{x},{y}L{x},{y - 120 * s}M{x},{y - 60 * s}Q{x - 50 * s},{y - 70 * s} {x - 55 * s},{y - 130 * s}M{x},{y - 80 * s}Q{x + 50 * s},{y - 90 * s} {x + 50 * s},{y - 150 * s}"
    return tube(d, 24 * s, c(col))


def shell(x, y, s, c):
    o = path(f"M{x - 40 * s},{y}Q{x - 50 * s},{y - 55 * s} {x},{y - 60 * s}Q{x + 50 * s},{y - 55 * s} {x + 40 * s},{y}Z", c("#ffd1b3"))
    for dx in (-22, 0, 22):
        o += line(f"M{x + dx * .4 * s},{y}L{x + dx * s},{y - 52 * s}", 5)
    return o + path(f"M{x - 14 * s},{y}L{x + 14 * s},{y}L{x + 8 * s},{y + 12 * s}L{x - 8 * s},{y + 12 * s}Z", c("#ffd1b3"), 5)


def small_fish(x, y, s, c, col="#ffd84d", flip=False):
    o = path(f"M{x + 40 * s},{y}L{x + 75 * s},{y - 28 * s}L{x + 75 * s},{y + 28 * s}Z", c(col))
    o += ellipse(x, y, 52 * s, 34 * s, c(col)) + eye(x - 22 * s, y - 6 * s, 9 * s) + line(f"M{x + 5 * s},{y - 26 * s}Q{x - 6 * s},{y} {x + 5 * s},{y + 26 * s}", 5)
    return g(o, t=f"translate({2 * x},0) scale(-1,1)") if flip else o


def sand(c, y=1010):
    o = path(f"M-20,{y}Q150,{y - 40} 330,{y}T700,{y - 10}T1020,{y}L1020,1170L-20,1170Z", c("#ffe6a8"))
    for px, py in [(120, 1080), (420, 1110), (760, 1090), (900, 1130), (260, 1135)]:
        o += dot(px, py, 4) + dot(px + 18, py + 8, 3)
    return o


def sea(c, weeds=True, fish=True, extra=""):
    o = sky_bg(c, "#9edcf7")
    o += line("M-20,60Q120,30 250,60T520,60T790,60T1060,60", 6)
    if weeds:
        o += seaweed(70, 1060, 330, c) + seaweed(130, 1080, 230, c, .8, -1) + seaweed(920, 1060, 300, c, 1, -1)
        o += coral(830, 1070, 1, c)
    o += sand(c)
    o += shell(260, 1080, .9, c) + shell(700, 1110, .7, c)
    o += bubbles([(880, 200, 26), (920, 280, 16), (860, 330, 12), (120, 260, 20), (90, 330, 12)], c)
    if fish:
        o += small_fish(150, 160, .8, c, "#ffb36b") + small_fish(820, 430, .7, c, "#b39cff", flip=True)
    return o + extra


def fish(c):
    o = sea(c)
    col = "#ffb34d"
    a = path("M680,610L860,470Q900,610 860,750Z", c("#ff7b54"))
    a += line("M720,560L840,510M730,610L860,610M720,660L840,710", 5)
    a += path("M380,470Q470,330 620,460Z", c("#ff7b54")) + path("M420,740Q480,830 560,750Z", c("#ff7b54"))
    a += ellipse(480, 610, 240, 175, c(col))
    a += line("M560,445Q520,610 560,775", 7) + line("M640,480Q610,610 640,740", 7)
    for x, y in [(450, 520), (500, 590), (450, 660), (500, 720)]:
        a += line(f"M{x - 20},{y}Q{x},{y + 22} {x + 20},{y}", 5)
    a += ellipse(560, 650, 60, 32, c("#ff7b54"), rot=-30)
    a += circle(340, 560, 50, "#fff") + eye(340, 565, 32)
    a += path("M250,650Q285,690 320,655", "none") + line("M252,650Q285,690 322,652")
    a += blush(380, 650, c, 22, 12)
    a += bubbles([(220, 560, 18), (190, 490, 12), (210, 430, 8)], c)
    return o + a


def whale(c):
    o = sky_bg(c, "#d6f0ff") + sun(150, 140, 55, c) + cloud(800, 130, .9, c)
    bl = "#7fb8ff"
    # spout
    o2 = tube("M470,330Q470,240 470,200M470,240Q420,180 380,200M470,240Q520,180 560,200", 26, c("#bfe6ff"))
    for x, y in [(370, 230), (570, 230), (420, 160), (520, 160), (470, 150)]:
        o2 += path(f"M{x},{y - 20}Q{x + 16},{y} {x},{y + 12}Q{x - 16},{y} {x},{y - 20}Z", c("#8fd3ff"), 5)
    a = path("M160,620Q160,370 460,370Q720,370 770,560L880,430Q950,440 915,530Q880,600 800,620Q760,790 470,800Q160,800 160,620Z", c(bl))
    a += path("M200,680Q460,780 740,660Q700,780 470,790Q260,790 200,680Z", c("#dceeff"))
    for y in (712, 740, 765):
        a += line(f"M{280 + (y - 700) * 2},{y}Q470,{y + 25} {650 - (y - 700) * 2},{y - 10}", 5)
    a += ellipse(560, 640, 75, 30, c(bl), rot=30)
    a += eye(320, 560, 30) + line("M215,640Q260,670 300,650") + blush(370, 620, c)
    a += line("M560,470Q590,450 620,470M600,520Q630,500 660,520", 5)
    w = path("M-20,780Q100,740 220,780T460,780T700,780T940,780T1180,780L1180,1170L-20,1170Z", c("#5aa9f2"))
    for x, y in [(100, 900), (600, 920), (300, 1030), (800, 1050), (480, 1110)]:
        w += line(f"M{x},{y}Q{x + 30},{y - 15} {x + 60},{y}Q{x + 90},{y + 15} {x + 120},{y}", 5)
    return o + o2 + a + w + small_fish(800, 960, .8, c, "#ffd84d", True)


def octopus(c):
    o = sea(c, fish=False) + small_fish(170, 180, .8, c, "#ffb36b") + small_fish(830, 160, .7, c, "#7cc96b", True)
    pk = "#c89cff"
    a = ""
    tents = [
        [(380, 600), (300, 700), (180, 760), (200, 880)],
        [(430, 640), (390, 760), (300, 880), (380, 960)],
        [(480, 650), (470, 790), (420, 900), (500, 990)],
        [(520, 650), (540, 790), (600, 900), (520, 990)],
        [(570, 640), (610, 760), (700, 880), (620, 960)],
        [(620, 600), (700, 700), (820, 760), (800, 880)],
    ]
    for t in tents:
        a += taper(t, 80, 30, c(pk))
        for tt in (.45, .62, .78):
            x, y = bez_pt(t, tt)
            a += circle(x, y, 10 * (1.1 - tt * .5), c("#f3e8ff"), 4)
    a += ellipse(500, 470, 215, 205, c(pk))
    for x, y, r in [(400, 360, 22), (600, 350, 16), (650, 420, 12), (360, 430, 12)]:
        a += circle(x, y, r, c("#e3d0ff"), 5)
    a += eye(430, 500, 30) + eye(570, 500, 30) + open_smile(500, 570, 30, c)
    a += blush(370, 565, c) + blush(630, 565, c)
    return o + a


def crab(c):
    o = sea(c)
    rd = "#ff7a6b"
    a = ""
    for sgn in (-1, 1):
        for i, yy in enumerate((760, 810, 860)):
            x0 = 500 + sgn * 170
            a += tube(f"M{x0},{yy}L{x0 + sgn * 110},{yy + 30 + i * 10}L{x0 + sgn * 140},{yy + 110 + i * 10}", 26, c(rd))
    for sgn in (-1, 1):
        a += tube(f"M{500 + sgn * 170},700Q{500 + sgn * 260},640 {500 + sgn * 270},540", 38, c(rd))
        cx, cy = 500 + sgn * 280, 470
        a += ellipse(cx - sgn * 30, cy - 10, 60, 90, c(rd), rot=-sgn * 15)
        a += ellipse(cx + sgn * 45, cy - 20, 40, 75, c(rd), rot=sgn * 25)
    a += tube("M440,640L420,520M560,640L580,520", 20, c(rd))
    a += circle(420, 500, 45, "#fff") + circle(580, 500, 45, "#fff") + eye(420, 505, 25) + eye(580, 505, 25)
    a += ellipse(500, 730, 230, 145, c(rd))
    for x, y, r in [(400, 670, 14), (600, 670, 14), (380, 760, 9), (620, 760, 9)]:
        a += circle(x, y, r, c("#ffb3a8"), 5)
    a += open_smile(500, 740, 40, c) + blush(400, 720, c) + blush(600, 720, c)
    return o + a


def starfish(c):
    o = sea(c)
    a = soft_star(500, 640, 330, .5, c("#ffb36b"), rot=-90)
    for k in range(5):
        ang = math.radians(-90 + 72 * k)
        for rr in (150, 210, 265):
            a += circle(500 + rr * math.cos(ang), 640 + rr * math.sin(ang), 14 - rr / 40, c("#ffd84d"), 5)
    a += eye(445, 620, 30) + eye(555, 620, 30) + smile(500, 690, 34) + blush(410, 680, c) + blush(590, 680, c)
    return o + a


def jellyfish(c):
    o = sea(c)

    def jelly(cx, cy, s, col):
        j = ""
        for k, dx in enumerate((-120, -60, 0, 60, 120)):
            x = cx + dx * s
            j += tube(f"M{x},{cy + 200 * s}Q{x - 40 * s},{cy + 300 * s} {x},{cy + 380 * s}T{x},{cy + 540 * s}", 18 * s, c("#ffd6f2"))
        j += path(f"M{cx - 200 * s},{cy + 200 * s}Q{cx - 200 * s},{cy - 60 * s} {cx},{cy - 60 * s}Q{cx + 200 * s},{cy - 60 * s} {cx + 200 * s},{cy + 200 * s}"
                  + "".join(f"Q{cx + (150 - 100 * i) * s},{cy + 240 * s} {cx + (100 - 100 * i) * s},{cy + 200 * s}" for i in range(4)) + "Z", c(col))
        j += eye(cx - 60 * s, cy + 90 * s, 24 * s) + eye(cx + 60 * s, cy + 90 * s, 24 * s) + smile(cx, cy + 140 * s, 24 * s)
        j += blush(cx - 105 * s, cy + 135 * s, c, 22 * s, 12 * s) + blush(cx + 105 * s, cy + 135 * s, c, 22 * s, 12 * s)
        j += line(f"M{cx - 120 * s},{cy + 20 * s}Q{cx - 100 * s},{cy - 25 * s} {cx - 55 * s},{cy - 35 * s}", 6)
        return j

    return o + jelly(230, 250, .5, "#9ed8ff") + jelly(520, 360, 1, "#ff9ed8")


def seahorse(c):
    o = sea(c)
    ye = "#ffd166"
    a = taper([(470, 840), (360, 900), (390, 1010), (480, 980)], 66, 26, c(ye))
    a += path("M600,470Q720,520 700,620Q690,700 610,730Z", c("#ffb36b")) + line("M620,520L680,560M625,580L690,610M620,640L670,670", 5)
    a += taper([(470, 420), (640, 520), (620, 760), (470, 860)], 190, 66, c(ye), rings=(.3, .4, .5, .6, .7, .8, .9))
    a += ellipse(300, 400, 100, 34, c(ye), rot=-4) + line("M202,395L202,412", 6)
    a += poly([(440, 270), (460, 220), (480, 268)], c("#ffb36b")) + poly([(480, 270), (510, 225), (520, 280)], c("#ffb36b")) + poly([(515, 290), (555, 255), (548, 310)], c("#ffb36b"))
    a += ellipse(460, 360, 105, 92, c(ye))
    a += eye(470, 345, 28) + blush(500, 400, c, 22, 12) + ""
    return o + a


def dolphin(c):
    o = sky_bg(c, "#d6f0ff") + sun(840, 150, 55, c) + cloud(180, 130, .9, c) + cloud(560, 90, .6, c)
    gr = "#8ab6e8"
    a = path("M770,830Q700,800 690,880Q740,860 790,880Q800,920 850,950Q860,880 830,840Q900,820 920,760Q850,770 800,810Z", c(gr))
    a += path("M500,450Q560,330 660,330Q610,400 630,490Z", c(gr))
    a += path("M800,830Q790,620 640,500Q520,410 380,420Q290,428 250,470L160,500Q148,522 175,532L262,540Q330,585 450,575Q600,565 690,680Q740,750 750,840Z", c(gr))
    a += path("M262,540Q330,585 450,575Q600,565 690,680Q740,750 750,840Q700,700 600,640Q480,600 380,620Q300,600 262,540Z", c("#e3efff"), 5)
    a += ellipse(520, 610, 75, 30, c(gr), rot=40)
    a += eye(340, 470, 26) + line("M178,528Q215,545 258,538", 6) + blush(390, 520, c)
    w = path("M-20,820Q100,780 220,820T460,820T700,820T940,820T1180,820L1180,1170L-20,1170Z", c("#5aa9f2"))
    for x, y in [(80, 940), (560, 960), (260, 1060), (760, 1080)]:
        w += line(f"M{x},{y}Q{x + 30},{y - 15} {x + 60},{y}Q{x + 90},{y + 15} {x + 120},{y}", 5)
    sp = ""
    for x, y, s in [(700, 770, 1), (880, 760, .8), (640, 800, .7), (930, 800, .6)]:
        sp += path(f"M{x},{y - 22 * s}Q{x + 18 * s},{y} {x},{y + 12 * s}Q{x - 18 * s},{y} {x},{y - 22 * s}Z", c("#8fd3ff"), 5)
    return o + a + w + sp


def sea_turtle(c):
    o = sea(c)
    gr, sh = "#8fd16e", "#6cbf5a"
    a = ellipse(330, 440, 120, 50, c(gr), rot=-35) + ellipse(690, 440, 120, 50, c(gr), rot=35)
    a += ellipse(360, 800, 90, 42, c(gr), rot=35) + ellipse(660, 800, 90, 42, c(gr), rot=-35)
    a += path("M500,830L475,880L525,880Z", c(gr))
    a += circle(500, 330, 95, c(gr))
    a += eye(462, 320, 22) + eye(538, 320, 22) + smile(500, 365, 22) + blush(430, 360, c, 18, 10) + blush(570, 360, c, 18, 10)
    a += ellipse(500, 620, 210, 230, c(sh))
    hexp = [(500 + 70 * math.cos(math.radians(60 * i + 30)), 620 + 70 * math.sin(math.radians(60 * i + 30))) for i in range(6)]
    a += poly(hexp, c("#a6e38f"))
    for (x, y), (ex, ey) in zip(hexp, [(670, 700), (500, 850), (330, 700), (330, 540), (500, 390), (670, 540)]):
        a += line(f"M{x:.1f},{y:.1f}L{ex},{ey}")
    return o + a


def shark(c):
    o = sea(c)
    gy = "#a9b8c9"
    a = path("M720,600L880,470Q860,600 880,740Z", c(gy))
    a += path("M440,440Q500,280 600,300Q560,380 590,450Z", c(gy))
    a += path("M140,620Q200,430 460,420Q700,420 760,600Q700,770 460,780Q200,780 140,620Z", c(gy))
    a += path("M160,660Q400,700 720,650Q660,770 460,775Q240,775 160,660Z", c("#eef3f8"))
    a += line("M560,560Q545,600 560,640M600,560Q585,600 600,640M640,565Q625,600 640,635", 5)
    a += ellipse(470, 700, 90, 34, c(gy), rot=25)
    a += path("M200,660Q260,700 340,670L320,690L300,672L280,694L260,672L240,690L220,668Z", "#fff", 6)
    a += eye(290, 570, 28) + blush(360, 630, c)
    return o + a


def puffer(c):
    o = sea(c)
    ye = "#ffe066"
    a = ""
    for k in range(16):
        ang = 2 * math.pi * k / 16
        bx, by = 500 + 215 * math.cos(ang), 600 + 215 * math.sin(ang)
        tx, ty = 500 + 275 * math.cos(ang), 600 + 275 * math.sin(ang)
        px, py = -math.sin(ang) * 22, math.cos(ang) * 22
        a += poly([(bx + px, by + py), (tx, ty), (bx - px, by - py)], c("#ffb34d"), 6)
    a += path("M690,600L800,520Q830,600 800,680Z", c("#ffb34d"))
    a += circle(500, 600, 230, c(ye))
    a += path("M290,660Q500,860 710,660Q620,820 500,825Q380,820 290,660Z", c("#fff6c9"), 5)
    for x, y in [(560, 430), (620, 500), (380, 450)]:
        a += circle(x, y, 16, c("#ffb34d"), 5)
    a += eye(420, 560, 32) + eye(580, 560, 32) + ellipse(500, 650, 26, 22, "#3b1d1d", w=6)
    a += blush(360, 630, c) + blush(640, 630, c)
    return o + a


def submarine(c):
    o = sea(c, fish=False) + small_fish(170, 170, .7, c, "#ffb36b") + small_fish(820, 890, .7, c, "#ff9ec7", True)
    ye = "#ffd23f"
    a = tube("M560,370L560,260L640,260", 22, c("#9aa7b8")) + rect(625, 240, 50, 40, 10, c("#9aa7b8"))
    a += rect(430, 360, 200, 120, 30, c("#ff7b54"))
    a += path("M800,560L880,500L880,740L800,680Z", c("#9aa7b8")) + ellipse(880, 620, 20, 130, c("#ff7b54"))
    a += rect(120, 450, 720, 310, 155, c(ye))
    for x in (300, 470, 640):
        a += circle(x, 590, 62, c("#cfeeff")) + circle(x, 590, 48, "none", 5)
    a += small_fish(300, 595, .5, c, "#7cc96b") + g(eye(458, 585, 12) + eye(490, 585, 12) + smile(474, 610, 10)) + small_fish(640, 595, .5, c, "#b39cff", True)
    a += line("M180,700L780,700", 6)
    for x in range(200, 780, 60):
        a += dot(x, 730, 6)
    a += bubbles([(920, 520, 18), (960, 470, 12), (950, 410, 8)], c)
    return o + a


PAGES = [
    ("سمكة", "Fish", fish), ("حوت", "Whale", whale), ("أخطبوط", "Octopus", octopus), ("سلطعون", "Crab", crab),
    ("نجمة البحر", "Starfish", starfish), ("قنديل البحر", "Jellyfish", jellyfish), ("فرس البحر", "Seahorse", seahorse),
    ("دلفين", "Dolphin", dolphin), ("سلحفاة بحرية", "Sea Turtle", sea_turtle), ("قرش لطيف", "Shark", shark),
    ("سمكة منتفخة", "Pufferfish", puffer), ("غواصة", "Submarine", submarine),
]

BOOK = dict(
    slug="sea",
    title="عالم البحر العجيب",
    en_title="Wonderful Sea World",
    subtitle="كتاب تلوين للأطفال",
    accent="#1e88e5",
    cover_bg=("#d6f0ff", "#8fd3ff"),
    cover_pages=["fish", "octopus", "whale", "crab"],
    pages=PAGES,
)
