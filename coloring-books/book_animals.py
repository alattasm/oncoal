"""Book 1: Cute animals (حيواناتي اللطيفة)."""
from prims import *


def scene_meadow(c, sun_at=(150, 170), cloud_at=((760, 150, 1.1),), flowers=((110, 960), (890, 975)), gy=880):
    out = sky_bg(c) + sun(*sun_at, 62, c)
    for cx, cy, s in cloud_at:
        out += cloud(cx, cy, s, c)
    out += hill(gy - 40, c) + ground(gy, c)
    for i, (fx, fy) in enumerate(flowers):
        out += flower(fx, fy, 1, c, ["#ff9ec7", "#b39cff", "#ffb36b"][i % 3])
    for x, y in [(60, 1100), (300, 1120), (720, 1110), (950, 1090), (520, 1135)]:
        out += tuft(x, y)
    return out


def cat(c):
    o = scene_meadow(c, flowers=((110, 960), (890, 975)))
    o += butterfly(420, 190, 1, c)
    org = "#ffb46b"
    a = tube("M640,1010C790,1010 820,860 760,800", 46, c(org))
    a += ellipse(500, 910, 165, 140, c(org)) + ellipse(500, 935, 95, 90, c("#fff1de"))
    a += ellipse(392, 1035, 58, 30, c(org)) + ellipse(608, 1035, 58, 30, c(org))
    for x in (448, 552):
        a += ellipse(x, 1028, 42, 33, c(org)) + line(f"M{x - 12},{1045}L{x - 12},{1060}M{x + 12},{1045}L{x + 12},{1060}", 5)
    a += path("M325,600L338,400L452,500Z", c(org)) + path("M675,600L662,400L548,500Z", c(org))
    a += path("M352,555L360,445L428,505Z", c("#ffb3c1")) + path("M648,555L640,445L572,505Z", c("#ffb3c1"))
    a += ellipse(500, 610, 218, 172, c(org))
    a += line("M470,445L478,488M500,440L500,490M530,445L522,488")
    a += eye(420, 610, 27) + eye(580, 610, 27)
    a += path("M486,648L514,648L500,664Z", "#000", 5)
    a += line("M468,672Q484,690 500,672Q516,690 532,672")
    a += blush(366, 668, c) + blush(634, 668, c)
    a += line("M282,630L352,645M285,672L352,668M718,630L648,645M715,672L648,668", 5)
    return o + a


def dog(c):
    o = scene_meadow(c, sun_at=(860, 160), cloud_at=((200, 160, 1.0), (560, 110, .7)), flowers=((90, 980),))
    # ball + bone
    o += circle(830, 1030, 62, c("#6ec6ff")) + line("M772,1010Q830,1060 888,1010M830,968Q800,1030 830,1092", 6)
    o += path("M95,1085a22,22 0 1 1 30,-28l60,0a22,22 0 1 1 30,28a22,22 0 1 1 -30,28l-60,0a22,22 0 1 1 -30,-28Z", c("#fff6e0"))
    br = "#e8b07a"
    a = tube("M650,930Q770,880 750,790", 34, c(br)) + line("M790,770Q805,790 798,812M812,760Q832,790 822,822", 5)
    a += ellipse(500, 935, 160, 135, c(br))
    a += ellipse(500, 965, 85, 80, c("#fff1de"))
    for x in (430, 570):
        a += path(f"M{x - 42},970L{x - 42},1045Q{x - 42},1065 {x - 20},1065L{x + 20},1065Q{x + 42},1065 {x + 42},1045L{x + 42},970Z", c(br))
        a += line(f"M{x - 12},1045L{x - 12},1065M{x + 12},1045L{x + 12},1065", 5)
    a += path("M380,800Q500,840 620,800L625,835Q500,875 375,835Z", c("#ff6b6b"))
    a += circle(500, 870, 26, c("#ffd84d")) + heart(500, 872, .45, c("#ff6b6b"), 5)
    a += ellipse(500, 625, 205, 178, c(br))
    a += ellipse(585, 590, 62, 58, c("#a86b3c"))
    a += path("M330,520C245,530 235,710 300,750C345,775 368,700 355,615Z", c("#a86b3c"))
    a += path("M670,520C755,530 765,710 700,750C655,775 632,700 645,615Z", c("#a86b3c"))
    a += ellipse(500, 695, 88, 64, c("#fff1de"))
    a += path("M485,722Q485,775 500,775Q515,775 515,722Z", c("#ff8fa3"), 6)
    a += ellipse(500, 665, 32, 21, "#000")
    a += line("M500,686L500,712M466,708Q483,728 500,712Q517,728 534,708")
    a += eye(425, 595, 25) + eye(578, 592, 25)
    a += blush(360, 690, c) + blush(640, 690, c)
    return o + a


def rabbit(c):
    o = scene_meadow(c, sun_at=(150, 150), cloud_at=((780, 140, 1.0),), flowers=((880, 970),))
    o += mushroom(130, 1080, 1.0, c) + mushroom(230, 1090, .6, c)
    wh = "#f7f2ff"
    a = fluffy(665, 990, 42, 9, c("#fff"))
    a += ellipse(430, 390, 50, 150, c(wh), rot=-10) + ellipse(570, 390, 50, 150, c(wh), rot=10)
    a += ellipse(431, 400, 24, 110, c("#ffb3c1"), rot=-10) + ellipse(569, 400, 24, 110, c("#ffb3c1"), rot=10)
    a += ellipse(500, 945, 150, 140, c(wh))
    a += ellipse(415, 1068, 64, 32, c(wh)) + ellipse(585, 1068, 64, 32, c(wh))
    # carrot held across the tummy
    a += tube("M575,835Q590,790 615,775M582,840Q615,815 648,820M570,832Q565,795 578,770", 14, c("#7cc96b"))
    a += path("M525,830Q580,795 610,850L455,1030Q435,1042 430,1022Z", c("#ff9a3c"))
    a += line("M540,880L562,892M515,915L537,928M490,950L510,960M470,985L485,992", 5)
    a += ellipse(462, 958, 40, 32, c(wh), rot=-30) + ellipse(565, 865, 40, 32, c(wh), rot=-30)
    a += ellipse(500, 660, 195, 162, c(wh))
    a += eye(428, 650, 26) + eye(572, 650, 26)
    a += ellipse(500, 690, 17, 12, c("#ff8fa3"), w=5)
    a += path("M486,716h28v24q0,6 -6,6h-16q-6,0 -6,-6Z", "#fff", 5) + line("M500,716v30", 4)
    a += line("M500,702L500,716M474,712Q487,724 500,716Q513,724 526,712")
    a += blush(372, 705, c) + blush(628, 705, c)
    a += line("M300,670L360,680M305,705L360,700M700,670L640,680M695,705L640,700", 5)
    return o + a


def lion(c):
    o = sky_bg(c, "#fff1c9") + sun(840, 170, 70, c) + cloud(200, 150, .9, c)
    o += acacia(170, 870, 1, c) + ground(880, c, "#f3d27a") + hill(1140, c, "#e9c46a", 30)
    for x, y in [(80, 1100), (330, 1125), (700, 1110), (940, 1090)]:
        o += tuft(x, y, 1.2)
    ye, mn = "#ffd166", "#e8913a"
    a = tube("M640,1010C760,1030 830,960 800,880", 22, c(ye)) + fluffy(800, 865, 32, 7, c(mn))
    a += ellipse(500, 960, 150, 125, c(ye)) + ellipse(500, 990, 80, 75, c("#fff1c9"))
    for x in (430, 570):
        a += ellipse(x, 1062, 52, 34, c(ye)) + line(f"M{x - 14},1072L{x - 14},1092M{x + 14},1072L{x + 14},1092", 5)
    a += fluffy(500, 615, 238, 15, c(mn))
    a += circle(372, 470, 42, c(ye)) + circle(628, 470, 42, c(ye)) + circle(372, 470, 22, c("#ffb3c1")) + circle(628, 470, 22, c("#ffb3c1"))
    a += ellipse(500, 630, 168, 152, c(ye))
    a += circle(468, 690, 42, c("#fff1c9")) + circle(532, 690, 42, c("#fff1c9"))
    a += path("M472,652Q500,640 528,652Q518,678 500,680Q482,678 472,652Z", "#000", 5)
    a += line("M500,680L500,700")
    for x, y in [(455, 690), (440, 708), (545, 690), (560, 708)]:
        a += dot(x, y, 5)
    a += eye(438, 595, 26) + eye(562, 595, 26)
    a += line("M410,555Q435,545 458,555M542,555Q565,545 590,555", 6)
    a += blush(388, 680, c) + blush(612, 680, c)
    return o + a


def elephant(c):
    o = scene_meadow(c, sun_at=(860, 150), cloud_at=((180, 150, 1.0),), flowers=((90, 960), (920, 1000)))
    gr = "#b9c7e6"
    a = tube("M690,930Q745,950 750,1000", 12, c(gr))
    for x in (370, 450, 560, 640):
        a += path(f"M{x - 38},900L{x - 38},1060Q{x - 38},1078 {x - 20},1078L{x + 20},1078Q{x + 38},1078 {x + 38},1060L{x + 38},900Z", c(gr))
        a += line(f"M{x - 18},1078Q{x - 10},1062 {x},1078M{x},1078Q{x + 10},1062 {x + 18},1078", 5)
    a += ellipse(505, 905, 205, 130, c(gr))
    a += ellipse(305, 590, 128, 150, c(gr), rot=-12) + ellipse(695, 590, 128, 150, c(gr), rot=12)
    a += ellipse(315, 595, 82, 105, c("#ffc2d1"), rot=-12) + ellipse(685, 595, 82, 105, c("#ffc2d1"), rot=12)
    a += ellipse(500, 580, 172, 158, c(gr))
    a += taper([(500, 660), (505, 780), (470, 860), (395, 850)], 80, 48, c(gr), rings=(.45, .6, .75))
    a += eye(435, 565, 25) + eye(565, 565, 25)
    a += blush(395, 640, c) + blush(605, 640, c)
    a += line("M410,520Q435,505 458,515M542,515Q565,505 590,520", 6)
    # water drops from trunk
    for x, y, s in [(340, 810, 1), (300, 760, .8), (350, 740, .7)]:
        a += path(f"M{x},{y - 22 * s}Q{x + 18 * s},{y} {x},{y + 12 * s}Q{x - 18 * s},{y} {x},{y - 22 * s}Z", c("#8fd3ff"), 5)
    return o + a


def bear(c):
    o = sky_bg(c) + cloud(800, 150, 1, c) + sun(150, 150, 55, c)
    o += tree(110, 900, 1.15, c) + tree(890, 880, 1.0, c) + ground(880, c)
    o += bee(320, 210, 1, c) + bee(700, 300, .8, c, flip=True)
    o += line("M375,215Q420,250 450,215Q480,180 520,230", 4) + line("M640,300Q600,330 580,290", 4)
    for x, y in [(60, 1100), (300, 1120), (720, 1110), (950, 1090)]:
        o += tuft(x, y)
    br = "#c98d5a"
    a = circle(355, 440, 55, c(br)) + circle(645, 440, 55, c(br)) + circle(355, 440, 30, c("#f0c9a0")) + circle(645, 440, 30, c("#f0c9a0"))
    a += ellipse(500, 940, 172, 145, c(br)) + ellipse(500, 965, 108, 98, c("#f0c9a0"))
    for x in (405, 595):
        a += ellipse(x, 1065, 62, 38, c(br)) + ellipse(x, 1068, 22, 15, c("#f0c9a0"), w=5)
    # honey pot
    a += path("M430,860Q395,960 445,1015L555,1015Q605,960 570,860Z", c("#f2a541"))
    a += ellipse(500, 860, 82, 22, c("#ffd84d")) + path("M440,868Q445,900 458,890Q470,880 470,900Q475,915 488,900L490,870Z", c("#ffd84d"), 5)
    a += ellipse(505, 950, 48, 32, c("#fff4cc"))
    a += f'<text x="505" y="964" text-anchor="middle" font-family="Fredoka" font-weight="700" font-size="28" fill="#fff" stroke="#000" stroke-width="5" paint-order="stroke">HONEY</text>'
    a += ellipse(395, 905, 48, 36, c(br), rot=30) + ellipse(605, 905, 48, 36, c(br), rot=-30)
    a += ellipse(500, 640, 192, 165, c(br))
    a += ellipse(500, 705, 72, 54, c("#f0c9a0"))
    a += ellipse(500, 683, 27, 18, "#000")
    a += line("M500,700L500,716M476,722Q488,736 500,716Q512,736 524,722")
    a += eye(430, 622, 25) + eye(570, 622, 25)
    a += blush(380, 700, c) + blush(620, 700, c)
    return o + a


def owl(c):
    o = sky_bg(c, "#c9cdf6") + moon(830, 170, 75, c)
    for x, y, r in [(150, 140, 30), (300, 260, 20), (620, 120, 24), (120, 420, 18), (900, 420, 22), (500, 230, 14)]:
        o += star(x, y, r, c("#fff3a8"))
    o += path("M-20,1000Q500,960 1020,1010L1020,1170L-20,1170Z", c("#9bd67e"))
    for x, y in [(80, 1100), (300, 1120), (720, 1110), (950, 1090)]:
        o += tuft(x, y)
    o += tube("M-20,930Q500,900 1020,950", 46, c("#b07a4f"))
    for x, y, r in [(150, 880, -35), (860, 905, 35), (280, 878, -20), (740, 895, 25)]:
        o += ellipse(x, y, 40, 18, c("#7cc96b"), rot=r)
    pu = "#b69cdb"
    a = path("M330,560L318,410L430,488Z", c(pu)) + path("M670,560L682,410L570,488Z", c(pu))
    a += ellipse(500, 720, 205, 255, c(pu))
    a += ellipse(500, 815, 130, 140, c("#f3e8ff"))
    for y in (740, 800, 860):
        for x in range(440, 580, 40):
            a += line(f"M{x - 16},{y}Q{x},{y + 16} {x + 16},{y}", 5)
    a += ellipse(312, 760, 55, 130, c("#9a7fc4"), rot=12) + ellipse(688, 760, 55, 130, c("#9a7fc4"), rot=-12)
    a += circle(420, 610, 88, c("#fff")) + circle(580, 610, 88, c("#fff"))
    a += eye(425, 615, 42) + eye(575, 615, 42)
    a += path("M478,670L522,670L500,712Z", c("#ffb34d"))
    for x in (440, 560):
        for dx in (-22, 0, 22):
            a += ellipse(x + dx, 940, 13, 24, c("#ffb34d"), w=6)
    return o + a


def giraffe(c):
    o = sky_bg(c, "#fff1c9") + sun(860, 160, 62, c) + cloud(650, 110, .8, c)
    o += acacia(160, 900, .95, c) + ground(900, c, "#f3d27a") + hill(1140, c, "#e9c46a", 30)
    for x, y in [(80, 1110), (320, 1125), (900, 1100)]:
        o += tuft(x, y, 1.2)
    ye, sp = "#ffd166", "#d98c3f"
    a = tube("M760,880Q800,920 800,980", 10, c(ye)) + fluffy(800, 990, 16, 6, c(sp))
    for x in (470, 540, 660, 730):
        a += path(f"M{x - 26},900L{x - 26},1060L{x + 26},1060L{x + 26},900Z", c(ye)) + rect(x - 28, 1050, 56, 32, 8, c("#8a5a35"))
    a += ellipse(600, 880, 185, 105, c(ye))
    for x, y, r, s in [(520, 860, 34, 3), (610, 905, 30, 4), (680, 850, 32, 5), (720, 920, 22, 6), (560, 930, 20, 7)]:
        a += blob(x, y, r, s, fill=c(sp), w=5)
    a += taper([(470, 860), (430, 700), (400, 560), (410, 440)], 120, 92, c(ye), end_cap=True)
    for t, r, s in [(.2, 26, 8), (.42, 24, 9), (.62, 22, 10), (.8, 20, 11)]:
        x, y = bez_pt([(470, 860), (430, 700), (400, 560), (410, 440)], t)
        a += blob(x + (8 if s % 2 else -10), y, r, s, fill=c(sp), w=5)
    a += tube("M380,320L372,260M450,320L458,260", 16, c(ye)) + circle(372, 255, 20, c(sp)) + circle(458, 255, 20, c(sp))
    a += ellipse(300, 345, 48, 22, c(ye), rot=-25) + ellipse(530, 345, 48, 22, c(ye), rot=25)
    a += ellipse(415, 380, 118, 98, c(ye))
    a += ellipse(415, 445, 92, 55, c("#ffe8b0"))
    a += dot(385, 440, 8) + dot(445, 440, 8) + smile(415, 465, 24)
    a += eye(370, 370, 22) + eye(460, 370, 22)
    a += line("M352,345L345,333M362,341L360,328M478,345L485,333M468,341L470,328", 5)
    a += blush(330, 415, c) + blush(500, 415, c)
    return o + a


def turtle(c):
    o = sky_bg(c) + sun(150, 150, 55, c) + cloud(780, 140, 1, c)
    o += ground(820, c) + path("M600,1060Q600,1000 800,1000Q1000,1000 1000,1060Q1000,1120 800,1120Q600,1120 600,1060Z", c("#9fdcff"))
    o += path("M690,1060a40,22 0 1 0 80,0a40,22 0 1 0 -80,0Z", c("#7cc96b")) + line("M730,1060L765,1050", 5)
    o += flower(90, 900, .9, c) + flower(920, 830, .8, c, "#b39cff")
    for x, y in [(60, 1110), (300, 1120), (480, 1100)]:
        o += tuft(x, y)
    gr, sh = "#8fd16e", "#6cbf5a"
    a = path("M720,815L790,840L725,858Z", c(gr))
    for x, y in [(350, 880), (690, 880)]:
        a += ellipse(x, y, 50, 60, c(gr))
        a += line(f"M{x - 18},{y + 40}L{x - 18},{y + 52}M{x},{y + 42}L{x},{y + 55}M{x + 18},{y + 40}L{x + 18},{y + 52}", 5)
    a += taper([(330, 780), (260, 730), (240, 650), (250, 610)], 70, 66, c(gr), end_cap=False)
    a += circle(245, 590, 82, c(gr))
    a += eye(215, 580, 18) + eye(280, 580, 18) + smile(250, 625, 20) + blush(200, 620, c, 16, 9) + blush(300, 620, c, 16, 9)
    a += path("M300,860Q300,560 520,560Q740,560 740,860Z", c(sh))
    hx, hy, hr = 520, 720, 68
    hexp = [(hx + hr * math.cos(math.radians(60 * i)), hy + hr * math.sin(math.radians(60 * i))) for i in range(6)]
    a += poly(hexp, c("#a6e38f"))
    for (x, y), (ex, ey) in zip(hexp, [(740, 760), (640, 860), (400, 860), (300, 760), (420, 590), (640, 590)]):
        a += line(f"M{x:.1f},{y:.1f}L{ex},{ey}")
    a += line("M300,858Q520,885 740,858", 6)
    return o + a


def camel(c):
    o = sky_bg(c, "#ffe9c7") + sun(820, 170, 70, c)
    o += path("M-20,900Q250,780 520,880T1020,860L1020,1170L-20,1170Z", c("#f7d08a"))
    o += palm(70, 960, .85, c, 15) + palm(905, 930, .95, c, -40)
    o += path("M-20,1000Q300,940 600,1010T1020,990L1020,1170L-20,1170Z", c("#f3c06b"))
    o += line("M120,1080Q200,1060 260,1080M640,1110Q700,1090 760,1110", 5)
    be = "#e7b77a"
    a = tube("M745,830Q790,900 770,960", 12, c(be))
    for x in (390, 450, 620, 680):
        a += path(f"M{x - 22},840L{x - 22},1050L{x + 22},1050L{x + 22},840Z", c(be)) + ellipse(x, 1058, 32, 16, c("#b58251"))
        a += ellipse(x, 960, 25, 18, c(be), w=5)
    a += path("M330,840Q315,740 420,720Q520,520 650,705Q760,730 750,840Q735,910 540,910Q345,910 330,840Z", c(be))
    # saddle cloth with Gulf pattern
    a += path("M440,700Q530,600 625,700L640,820L425,820Z", c("#e63946"))
    a += path("M440,760L640,760L640,820L425,820Z", c("#2a9d8f"))
    for x in range(440, 640, 34):
        a += poly([(x, 760), (x + 17, 790), (x + 34, 760)], c("#ffd166"), 4)
    for x in range(440, 650, 30):
        a += line(f"M{x},822L{x},850", 4) + circle(x, 858, 9, c("#ffd166"), 4)
    a += taper([(395, 790), (350, 700), (300, 640), (300, 540)], 96, 76, c(be))
    a += ellipse(345, 430, 20, 34, c(be), rot=30)
    a += ellipse(270, 495, 112, 76, c(be), rot=-6)
    a += ellipse(190, 528, 64, 52, c("#f3d0a2"))
    a += ellipse(165, 512, 7, 10, "#000", w=0) + line("M168,552Q192,566 222,550", 6)
    a += eye(288, 472, 25) + line("M268,446L260,432M287,441L287,426M306,446L314,432", 5)
    a += blush(320, 525, c, 20, 11)
    return o + a
    return o + a


def sheep(c):
    o = sky_bg(c) + sun(860, 160, 58, c) + cloud(180, 160, 1, c) + cloud(520, 110, .6, c)
    o += hill(700, c) + fence(690, c) + ground(890, c)
    o += flower(120, 970, .9, c) + flower(900, 985, .9, c, "#ffb36b")
    for x, y in [(60, 1110), (300, 1120), (720, 1110), (950, 1090)]:
        o += tuft(x, y)
    a = ""
    for x in (390, 460, 545, 615):
        a += tube(f"M{x},950L{x},1060", 30, c("#5b5b6b"))
    a += fluffy(500, 860, 210, 18, c("#fffaf0"), ry=150)
    a += ellipse(375, 580, 62, 26, c("#5b5b6b"), rot=20) + ellipse(625, 580, 62, 26, c("#5b5b6b"), rot=-20)
    a += ellipse(500, 610, 120, 130, c("#7a7a8c"))
    a += fluffy(500, 500, 82, 10, c("#fffaf0"), ry=55)
    a += eye(458, 615, 22) + eye(542, 615, 22)
    a += smile(500, 680, 22) + blush(430, 665, c, 18, 10) + blush(570, 665, c, 18, 10)
    a += path("M455,520Q500,560 545,520", "none")
    return o + a


def duck(c):
    o = sky_bg(c) + sun(150, 150, 55, c) + cloud(780, 150, 1, c)
    o += ground(800, c)
    o += tube("M860,880L860,700", 10, c("#7cc96b")) + ellipse(860, 690, 18, 50, c("#a86b3c")) + tube("M930,880L930,740", 10, c("#7cc96b")) + ellipse(930, 730, 16, 44, c("#a86b3c"))
    ye = "#ffe066"
    a = path("M700,760Q760,640 800,650Q790,720 760,800Z", c(ye))
    a += ellipse(500, 820, 260, 150, c(ye))
    a += path("M470,770Q560,720 660,770Q650,860 560,870Q480,860 470,770Z", c("#ffd23f"))
    a += line("M500,800Q560,815 630,790M510,830Q560,840 620,822", 5)
    a += circle(360, 580, 130, c(ye))
    a += fluffy(360, 445, 24, 6, c(ye))
    a += path("M240,600Q170,585 165,620Q175,650 245,640Z", c("#ff9a3c"))
    a += line("M172,622Q205,625 243,620", 5)
    a += eye(315, 560, 23) + eye(405, 560, 23)
    a += blush(285, 630, c, 20, 11) + blush(445, 625, c, 20, 11)
    a += path("M-20,900Q120,870 250,900Q380,930 500,900Q620,870 750,900Q880,930 1020,900L1020,1170L-20,1170Z", c("#8fd3ff"))
    for x, y in [(80, 990), (620, 1010), (240, 1100), (820, 1090)]:
        a += line(f"M{x},{y}Q{x + 30},{y - 15} {x + 60},{y}Q{x + 90},{y + 15} {x + 120},{y}", 5)
    return o + a


PAGES = [
    ("قطة", "Cat", cat), ("كلب", "Dog", dog), ("أرنب", "Rabbit", rabbit), ("أسد", "Lion", lion),
    ("فيل", "Elephant", elephant), ("دبدوب", "Bear", bear), ("بومة", "Owl", owl), ("زرافة", "Giraffe", giraffe),
    ("سلحفاة", "Turtle", turtle), ("جمل", "Camel", camel), ("خروف", "Sheep", sheep), ("بطة", "Duck", duck),
]

BOOK = dict(
    slug="animals",
    title="حيواناتي اللطيفة",
    en_title="My Cute Animals",
    subtitle="كتاب تلوين للأطفال",
    accent="#ff8c42",
    cover_bg=("#fff1c9", "#ffd6a5"),
    cover_pages=["cat", "lion", "rabbit", "elephant"],
    pages=PAGES,
)
