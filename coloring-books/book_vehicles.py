"""Book 3: Vehicles (مركباتي المرحة)."""
from prims import *


def wheel(x, y, r, c):
    o = circle(x, y, r, c("#5b5b6b")) + circle(x, y, r * .55, c("#d9dde3")) + circle(x, y, r * .18, c("#9aa7b8"), 5)
    return o


def road(c, y=900):
    o = rect(-20, y, 1040, 300, 0, c("#b8bcc6"))
    for x in range(20, 1000, 150):
        o += rect(x, y + 95, 90, 18, 9, c("#fff"), 5)
    return o


def town(c, y=900):
    o = sky_bg(c) + sun(860, 150, 55, c) + cloud(180, 150, 1, c) + cloud(560, 110, .6, c)
    o += hill(y - 60, c, "#c8f0a0", 70)
    o += tree(90, y, .8, c) + tree(930, y, .75, c)
    return o + road(c, y)


def eyes_smile(cx, cy, c, dx=40, r=20, mw=24):
    return eye(cx - dx, cy, r) + eye(cx + dx, cy, r) + smile(cx, cy + 40, mw) + blush(cx - dx - 30, cy + 30, c, 18, 10) + blush(cx + dx + 30, cy + 30, c, 18, 10)


def car(c):
    o = town(c)
    rd = "#ff6b6b"
    a = path("M120,880L120,760Q120,700 190,690L300,680L390,560Q410,540 450,540L640,540Q680,540 700,565L790,680L850,690Q900,700 900,760L900,880Q900,900 880,900L140,900Q120,900 120,880Z", c(rd))
    a += path("M330,680L410,580L500,580L500,680Z", c("#cfeeff")) + path("M530,580L640,580Q660,580 672,595L740,680L530,680Z", c("#cfeeff"))
    a += eye(440, 635, 20) + eye(600, 635, 20)
    a += line("M515,560L515,890M560,720L600,720", 6)
    a += ellipse(870, 740, 26, 34, c("#fff3a8")) + rect(100, 800, 60, 34, 12, c("#d9dde3")) + rect(860, 800, 60, 34, 12, c("#d9dde3"))
    a += smile(820, 800, 24) + blush(780, 770, c, 18, 10)
    a += wheel(300, 900, 82, c) + wheel(720, 900, 82, c)
    for x, y in [(60, 830), (40, 870), (70, 790)]:
        a += line(f"M{x},{y}L{x - 40},{y}", 6)
    return o + a


def bus(c):
    o = town(c)
    ye = "#ffd23f"
    a = rect(90, 470, 830, 420, 50, c(ye))
    for x in (150, 320, 490):
        a += rect(x, 520, 140, 130, 18, c("#cfeeff"))
    a += rect(670, 520, 120, 330, 18, c("#cfeeff")) + line("M730,520L730,850", 6)
    a += rect(820, 520, 70, 150, 18, c("#cfeeff"))
    a += eye(220, 585, 16) + smile(220, 620, 14) + eye(390, 590, 16) + smile(390, 625, 14) + eye(560, 585, 16) + smile(560, 620, 14)
    a += path("M90,700L920,700", "none") + line("M90,690L650,690", 6)
    a += f'<text x="370" y="800" text-anchor="middle" font-family="Fredoka" font-weight="700" font-size="80" fill="#fff" stroke="#000" stroke-width="9" paint-order="stroke" stroke-linejoin="round">SCHOOL BUS</text>'
    a += ellipse(900, 760, 22, 34, c("#fff3a8")) + rect(70, 840, 80, 36, 12, c("#d9dde3")) + rect(870, 840, 80, 36, 12, c("#d9dde3"))
    a += poly([(40, 560), (60, 540), (90, 540), (110, 560), (110, 590), (90, 610), (60, 610), (40, 590)], c("#ff6b6b"))
    a += wheel(260, 900, 78, c) + wheel(740, 900, 78, c)
    return o + a


def plane(c):
    o = sky_bg(c) + sun(140, 140, 55, c)
    for x, y, s in [(820, 180, 1), (200, 900, 1.2), (780, 960, 1.1), (520, 1060, .8), (130, 560, .7)]:
        o += cloud(x, y, s, c)
    bl = "#6ec6ff"
    a = path("M700,500L800,320Q830,300 850,330L840,540Z", c("#ff6b6b"))
    a += ellipse(560, 500, 170, 45, c("#ff6b6b"), rot=-12)
    a += path("M180,560Q180,470 300,470L780,480Q860,490 880,560Q870,620 780,630L300,640Q180,640 180,560Z", c(bl))
    a += ellipse(500, 570, 200, 55, c("#ff6b6b"), rot=8)
    for x in (380, 470, 560, 650):
        a += circle(x, 510, 24, c("#cfeeff"))
    a += path("M180,560Q200,500 260,490L260,560Z", c("#cfeeff"))
    a += eye(220, 540, 16) + line("M200,600Q230,615 255,600", 6)
    a += line("M60,520L130,520M40,570L130,570M70,620L130,620", 6)
    return o + a


def rocket(c):
    o = sky_bg(c, "#2b2d6e" if c.color else "#fff")
    for x, y, r in [(120, 150, 26), (850, 120, 30), (180, 520, 18), (880, 600, 22), (720, 300, 14), (300, 300, 14), (820, 900, 20), (150, 900, 24)]:
        o += star(x, y, r, c("#fff3a8"))
    o += circle(160, 340, 60, c("#ffb36b")) + ellipse(160, 340, 110, 26, "none", rot=-15) + path("M60,365Q160,330 260,315", "none")
    o += circle(850, 420, 70, c("#b39cff")) + circle(830, 400, 14, c("#d9c9ff"), 5) + circle(870, 450, 10, c("#d9c9ff"), 5)
    o += moon(860, 1040, 70, c)
    a = fluffy(500, 1000, 90, 9, c("#ffb34d"), ry=120) + fluffy(500, 975, 55, 7, c("#ffe066"), ry=75)
    a += path("M380,700L280,880L390,850Z", c("#ff6b6b")) + path("M620,700L720,880L610,850Z", c("#ff6b6b"))
    a += path("M500,180Q650,330 640,620L620,880L380,880L360,620Q350,330 500,180Z", c("#eef3f8"))
    a += path("M500,180Q570,250 600,320L400,320Q430,250 500,180Z", c("#ff6b6b"))
    a += rect(400, 880, 200, 40, 14, c("#9aa7b8"))
    a += circle(500, 490, 90, c("#9aa7b8")) + circle(500, 490, 68, c("#cfeeff"))
    a += eyes_smile(500, 475, c, 28, 16, 18)
    a += line("M380,700L620,700", 6) + path("M500,700L500,880", "none") + line("M500,700L500,880", 6)
    return o + a


def train(c):
    o = sky_bg(c) + sun(150, 140, 55, c) + cloud(820, 150, 1, c)
    o += hill(820, c, "#c8f0a0", 80) + ground(900, c)
    o += rect(-20, 960, 1040, 22, 8, c("#b07a4f"))
    for x in range(0, 1000, 70):
        o += rect(x, 985, 30, 60, 6, c("#c98d5a"), 5)
    o += rect(-20, 1030, 1040, 22, 8, c("#b07a4f"))
    a = fluffy(690, 280, 50, 8, c("#eef3f8")) + fluffy(610, 220, 40, 7, c("#eef3f8")) + fluffy(540, 170, 30, 6, c("#eef3f8"))
    a += path("M660,500L650,380L730,380L720,500Z", c("#5b5b6b")) + rect(635, 360, 110, 34, 10, c("#5b5b6b"))
    # carriage
    a += rect(40, 660, 330, 220, 26, c("#7cc96b"))
    a += rect(80, 560, 90, 100, 14, c("#ffd23f")) + rect(200, 590, 120, 70, 14, c("#ff9ec7"))
    a += circle(125, 610, 14, "none", 5) + star(260, 625, 26)
    a += line("M370,840L460,840", 10)
    # engine
    a += rect(450, 500, 420, 380, 30, c("#ff6b6b"))
    a += rect(450, 400, 210, 160, 24, c("#ff6b6b")) + rect(480, 430, 150, 110, 16, c("#cfeeff"))
    a += eye(530, 480, 16) + eye(585, 480, 16) + smile(557, 512, 16)
    a += circle(860, 690, 40, c("#fff3a8")) + rect(700, 600, 160, 60, 12, c("#ffd23f"))
    a += eyes_smile(765, 750, c, 50, 22, 26)
    a += path("M870,820L940,900L870,900Z", c("#9aa7b8"))
    for x, r in [(110, 55), (300, 55), (540, 60), (700, 60), (840, 50)]:
        a += wheel(x, 900, r, c)
    a += line("M540,900L840,900", 10)
    return o + a


def sailboat(c):
    o = sky_bg(c) + sun(150, 140, 60, c) + cloud(820, 140, 1, c)
    for x, y in [(300, 250), (720, 330), (620, 230)]:
        o += line(f"M{x - 30},{y}Q{x - 15},{y - 20} {x},{y}Q{x + 15},{y - 20} {x + 30},{y}", 6)
    a = tube("M500,260L500,800", 18, c("#b07a4f"))
    a += path("M480,280L470,760L180,760Z", c("#fff6e0"))
    a += path("M520,330L800,760L525,760Z", c("#ff9ec7"))
    a += path("M510,250L510,180L610,210Z", c("#ff6b6b"))
    a += path("M140,790L860,790L780,920Q760,940 730,940L270,940Q240,940 220,920Z", c("#ff7b54"))
    a += line("M175,840L825,840", 6)
    for x in (320, 420, 580, 680):
        a += circle(x, 885, 20, c("#cfeeff"))
    a += eye(470, 880, 18) + eye(530, 880, 18) + smile(500, 905, 18)
    w = path("M-20,920Q60,880 140,920T300,920T460,920T620,920T780,920T940,920T1100,920L1100,1170L-20,1170Z", c("#5aa9f2"))
    for x, y in [(100, 1020), (600, 1040), (300, 1110), (800, 1100)]:
        w += line(f"M{x},{y}Q{x + 30},{y - 15} {x + 60},{y}Q{x + 90},{y + 15} {x + 120},{y}", 5)
    return o + a + w


def firetruck(c):
    o = town(c)
    rd = "#ff4d4d"
    a = rect(80, 600, 600, 280, 26, c(rd))
    a += rect(660, 520, 260, 360, 40, c(rd)) + rect(700, 560, 180, 130, 20, c("#cfeeff"))
    a += eye(760, 615, 18) + eye(820, 615, 18) + smile(790, 650, 18)
    a += rect(740, 480, 100, 40, 14, c("#6ec6ff")) + line("M760,470L740,440M790,465L790,430M820,470L840,440", 6)
    a += line("M60,560L640,470M60,600L640,510", 8)
    for i in range(9):
        x0 = 60 + i * 70
        a += line(f"M{x0},{560 - i * 10.9:.0f}L{x0},{600 - i * 10.9:.0f}", 7)
    a += circle(250, 740, 80, c("#ffd23f")) + circle(250, 740, 30, c("#d9dde3")) + tube("M330,740Q420,700 450,760Q470,800 520,790", 18, c("#ffd23f"))
    a += rect(420, 650, 220, 130, 16, c("#fff3a8"))
    a += f'<text x="530" y="735" text-anchor="middle" font-family="Fredoka" font-weight="700" font-size="58" fill="#fff" stroke="#000" stroke-width="7" paint-order="stroke">FIRE</text>'
    a += rect(900, 800, 60, 40, 12, c("#d9dde3")) + ellipse(910, 740, 20, 30, c("#fff3a8"))
    a += wheel(230, 900, 80, c) + wheel(560, 900, 80, c) + wheel(790, 900, 80, c)
    return o + a


def helicopter(c):
    o = sky_bg(c) + sun(860, 160, 55, c) + cloud(160, 160, 1, c) + cloud(800, 950, 1.1, c) + cloud(200, 1000, .9, c)
    ye = "#ffd23f"
    a = tube("M500,300L500,370", 22, c("#9aa7b8"))
    a += path("M140,290Q500,250 860,290Q500,320 140,290Z", c("#9aa7b8"))
    a += taper([(600, 560), (720, 520), (800, 480), (860, 440)], 110, 46, c(ye))
    a += circle(865, 430, 52, "none", 6) + line("M865,375L865,485M810,430L920,430", 8) + circle(865, 430, 12, c("#9aa7b8"), 5)
    a += path("M260,800L760,800M330,740L310,800M650,740L670,800", "none") + tube("M240,800L760,800Q790,800 800,770", 16, c("#9aa7b8")) + tube("M340,720L330,800M640,720L650,800", 14, c("#9aa7b8"))
    a += ellipse(470, 560, 250, 190, c(ye))
    a += path("M260,520Q270,410 420,400L420,560L262,560Z", c("#cfeeff"))
    a += eye(320, 480, 18) + eye(380, 480, 18) + smile(350, 515, 16)
    a += line("M220,600Q230,620 270,630", 6) + blush(300, 610, c, 20, 11)
    a += rect(470, 450, 130, 130, 20, c("#cfeeff"))
    a += star(560, 650, 34, c("#ff6b6b"))
    return o + a


def tractor(c):
    o = sky_bg(c) + sun(150, 140, 55, c) + cloud(820, 150, 1, c) + hill(820, c) + fence(760, c) + ground(900, c)
    for x, y in [(60, 1110), (480, 1130), (930, 1100)]:
        o += tuft(x, y)
    gr = "#7cc96b"
    a = tube("M680,560L680,420", 26, c("#5b5b6b")) + fluffy(700, 360, 34, 7, c("#eef3f8")) + fluffy(740, 300, 24, 6, c("#eef3f8"))
    a += rect(240, 420, 280, 300, 24, c(gr)) + rect(275, 455, 210, 170, 18, c("#cfeeff"))
    a += eye(340, 530, 18) + eye(420, 530, 18) + smile(380, 565, 18)
    a += rect(220, 400, 320, 40, 14, c("#ff6b6b"))
    a += path("M500,600L820,620Q860,625 860,670L860,820L500,820Z", c(gr))
    a += line("M720,640L720,800M760,640L760,800M800,640L800,800", 5)
    a += ellipse(850, 690, 18, 28, c("#fff3a8"))
    a += wheel(340, 820, 170, c) + wheel(760, 870, 100, c)
    for k in range(12):
        ang = 2 * math.pi * k / 12
        a += line(f"M{340 + 150 * math.cos(ang):.0f},{820 + 150 * math.sin(ang):.0f}L{340 + 172 * math.cos(ang):.0f},{820 + 172 * math.sin(ang):.0f}", 6)
    return o + a


def balloon(c):
    o = sky_bg(c) + sun(150, 140, 55, c)
    for x, y, s in [(830, 200, 1), (160, 700, 1), (860, 760, .9), (480, 1080, 1.2)]:
        o += cloud(x, y, s, c)
    o += line("M780,420Q795,400 810,420Q825,400 840,420M200,330Q212,312 225,330Q238,312 250,330", 6)
    o += ellipse(800, 560, 70, 85, c("#b39cff")) + line("M760,640L780,700M840,640L820,700", 4) + rect(770, 700, 60, 40, 8, c("#c98d5a"), 5)
    d = "M500,140Q760,140 760,420Q760,560 600,700L400,700Q240,560 240,420Q240,140 500,140Z"
    a = path(d, c("#ff6b6b"))
    a += path("M500,140Q400,250 400,420Q400,560 450,700L550,700Q600,560 600,420Q600,250 500,140Z", c("#ffd23f"))
    a += path("M500,140Q470,300 470,420Q470,580 485,700L515,700Q530,580 530,420Q530,300 500,140Z", c("#6ec6ff"))
    a += path("M250,470Q500,520 750,470", "none") + line("M246,470Q500,530 754,470", 6)
    a += eyes_smile(500, 380, c, 55, 24, 26)
    a += rect(400, 690, 200, 34, 12, c("#c98d5a"))
    a += line("M420,724L440,820M580,724L560,820M480,724L485,820M520,724L515,820", 6)
    a += path("M410,820L590,820L570,940Q565,955 550,955L450,955Q435,955 430,940Z", c("#e0b081"))
    a += line("M420,860L580,860M425,900L575,900M470,820L470,955M530,820L530,955", 5)
    return o + a


def digger(c):
    o = sky_bg(c) + sun(860, 150, 55, c) + cloud(180, 150, 1, c) + ground(880, c, "#e9c46a")
    o += path("M720,880Q760,800 840,800Q920,800 960,880Z", c("#c98d5a"))
    for x in (90, 940):
        o += path(f"M{x - 40},1060L{x},940L{x + 40},1060Z", c("#ff9a3c")) + line(f"M{x - 25},1020L{x + 25},1020M{x - 13},985L{x + 13},985", 7) + rect(x - 55, 1050, 110, 24, 8, c("#ff9a3c"))
    ye = "#ffd23f"
    a = tube("M500,640L640,420L820,560", 50, c(ye))
    a += path("M800,560L900,560Q920,640 860,690L790,690Q780,640 800,560Z", c("#9aa7b8"))
    a += line("M810,690L800,720M840,690L838,722M870,690L875,720", 8)
    a += rect(180, 820, 560, 140, 70, c("#5b5b6b"))
    for x in (260, 380, 500, 620):
        a += circle(x, 890, 40, c("#9aa7b8"))
    a += rect(200, 690, 520, 130, 26, c(ye))
    a += rect(260, 470, 240, 230, 26, c(ye)) + rect(290, 500, 180, 140, 18, c("#cfeeff"))
    a += eye(350, 560, 18) + eye(410, 560, 18) + smile(380, 595, 18)
    a += circle(640, 420, 24, c("#9aa7b8")) + circle(500, 640, 24, c("#9aa7b8"))
    a += line("M560,740L700,740", 6)
    return o + a


def icecream_truck(c):
    o = town(c)
    pk = "#ff9ec7"
    a = rect(80, 470, 600, 420, 40, c(pk)) + rect(660, 580, 260, 310, 40, c(pk))
    a += rect(700, 620, 170, 120, 18, c("#cfeeff"))
    a += eye(760, 670, 18) + eye(820, 670, 18) + smile(790, 705, 18)
    a += path("M80,520Q130,470 180,520Q230,470 280,520Q330,470 380,520Q430,470 480,520Q530,470 580,520Q630,470 680,520L680,470Q680,430 640,430L120,430Q80,430 80,470Z", c("#6ec6ff"))
    a += rect(130, 560, 380, 180, 20, c("#fff6e0"))
    for i, x in enumerate((200, 320, 440)):
        a += path(f"M{x - 30},670L{x},740L{x + 30},670Z", c("#e0b081")) + line(f"M{x - 18},690L{x + 18},690", 4)
        a += circle(x, 650, 34, c(["#ff9ec7", "#7cc96b", "#ffe066"][i]))
    a += circle(560, 380, 34, c("#ffe066")) + path("M530,390L560,470L590,390Z", c("#e0b081")) + line("M560,470L560,430", 0)
    a += rect(600, 640, 40, 120, 10, "none", 5)
    a += ellipse(910, 760, 20, 30, c("#fff3a8")) + rect(870, 840, 80, 36, 12, c("#d9dde3"))
    a += wheel(260, 900, 78, c) + wheel(760, 900, 78, c)
    return o + a


PAGES = [
    ("سيارة", "Car", car), ("باص المدرسة", "School Bus", bus), ("طائرة", "Airplane", plane), ("صاروخ", "Rocket", rocket),
    ("قطار", "Train", train), ("قارب شراعي", "Sailboat", sailboat), ("سيارة إطفاء", "Fire Truck", firetruck),
    ("هليكوبتر", "Helicopter", helicopter), ("جرّار", "Tractor", tractor), ("منطاد", "Hot Air Balloon", balloon),
    ("حفّارة", "Digger", digger), ("سيارة الآيس كريم", "Ice Cream Truck", icecream_truck),
]

BOOK = dict(
    slug="vehicles",
    title="مركباتي المرحة",
    en_title="My Fun Vehicles",
    subtitle="كتاب تلوين للأطفال",
    accent="#e63946",
    cover_bg=("#e8f4ff", "#b8e0ff"),
    cover_pages=["car", "rocket", "train", "balloon"],
    pages=PAGES,
)
