"""Baby Yusuf - the store mascot, drawn in the same style as the books.

yusuf(c) returns SVG in a 1000x1000 box (bust, holding a crayon).
With Pal(True) it is the full-colour character; with Pal(False) a coloring page.
"""
from prims import *

SKIN, HAIR, SHIRT = "#f2c7a2", "#3a2416", "#2f80ed"


def crayon_tilted(x, y, c, col="#ff4d6d", ang=-35, s=1):
    o = path("M-22,0L-22,-150L22,-150L22,0Z", c(col)) + path("M-22,-150L0,-205L22,-150Z", c("#ffe0b8"))
    o += path("M-8,-185L0,-205L8,-185Z", c(col), 5) + line("M-22,-30L22,-30M-22,-120L22,-120", 5)
    return g(o, t=f"translate({x},{y}) rotate({ang}) scale({s})")


def yusuf(c, crayon=True):
    sk, hr, sh = c(SKIN), c(HAIR), c(SHIRT)
    o = ""
    # back hair: full, messy, wavy volume ending around the ears
    o += fluffy(500, 385, 250, 10, hr, ry=205, rot=12)
    # body: t-shirt + arms
    o += rect(462, 630, 76, 70, 20, sk)
    o += path("M300,1010L322,760Q330,705 410,690Q500,675 590,690Q670,705 678,760L700,1010Z", sh)
    o += line("M432,694Q500,735 568,694", 6)
    o += star(500, 860, 70, c("#ffd84d"))
    o += tube("M330,770Q300,860 312,925", 62, sk) + circle(314, 940, 42, sk)
    o += path("M345,705Q300,720 290,790L370,815Q385,750 400,700Z", sh)
    if crayon:
        o += tube("M668,770Q735,720 752,660", 62, sk)
        o += crayon_tilted(760, 655, c, ang=28, s=1.05)
        o += circle(762, 628, 44, sk) + line("M736,612Q750,602 765,608M738,634Q752,626 768,632", 5)
        o += path("M655,705Q700,715 720,780L640,815Q625,750 600,700Z", sh)
    else:
        o += tube("M670,770Q700,860 688,925", 62, sk) + circle(686, 940, 42, sk)
        o += path("M655,705Q700,720 710,790L630,815Q615,750 600,700Z", sh)
    # ears + face
    o += ellipse(292, 515, 30, 40, sk) + ellipse(708, 515, 30, 40, sk)
    o += ellipse(500, 485, 205, 178, sk)
    # face
    o += eye(418, 512, 36) + eye(588, 516, 36)
    o += line("M380,470Q398,462 416,466M592,470Q610,466 626,474", 5)
    o += line("M490,560Q502,574 516,562", 6)
    o += open_smile(503, 604, 30, c)
    o += blush(368, 590, c, 34, 18) + blush(640, 594, c, 34, 18)
    # front hair: messy fringe with the long lock between the eyes
    o += path("M292,500Q275,268 500,250Q722,262 714,495Q700,430 668,398Q652,422 628,424Q605,402 594,360Q578,430 546,488Q540,430 518,384Q488,402 455,388Q428,374 410,350Q394,402 360,414Q328,436 318,488Q306,478 292,500Z", hr)
    o += line("M560,300Q600,330 615,380M440,290Q420,320 425,360M500,275Q505,320 498,360M650,320Q665,360 668,395", 5)
    # wispy strands on top
    o += line("M470,255Q450,215 420,205M520,252Q545,200 590,195M560,256Q600,225 640,232", 6)
    # little curls over the ears
    o += path("M296,430Q268,470 285,505Q300,480 318,472Z", hr) + path("M704,430Q732,470 715,505Q700,480 682,472Z", hr)
    return o


if __name__ == "__main__":
    import subprocess, pathlib, sys
    here = pathlib.Path(__file__).parent
    out = here / "output" / "mascot"
    out.mkdir(parents=True, exist_ok=True)
    for name, col in [("baby-yusuf-cartoon", True), ("baby-yusuf-lineart", False)]:
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="150 120 720 900" width="1440" height="1800">{yusuf(Pal(col))}</svg>'
        (out / f"{name}.svg").write_text(svg)
        html = out / "t.html"
        html.write_text(f'<html><body style="margin:0;background:transparent">{svg}</body></html>')
        subprocess.run(["node", "-e", f"""const {{chromium}}=require('playwright');(async()=>{{const b=await chromium.launch();const p=await b.newPage({{viewport:{{width:1440,height:1800}}}});await p.goto('file://{html}');await p.screenshot({{path:'{out / (name + ".png")}',omitBackground:true}});await b.close();}})()"""], check=True)
        html.unlink()
    print("ok")
