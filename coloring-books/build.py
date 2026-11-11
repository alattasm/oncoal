"""Build print-ready kids' coloring books.

    python3 build.py                 # all books
    python3 build.py book_animals    # one book

For each book, writes to output/<slug>/:
  <slug>-printable.pdf  every page once (for digital download / home printing)
  <slug>-kdp-interior.pdf  each coloring page followed by a blank back page,
                         so markers never bleed through (for print-on-demand)
  <slug>-cover.png      front cover, 2550x3300 px (8.5x11 in @ 300 DPI)
  pages-300dpi/         every page as a 300 DPI PNG (Etsy / digital shops)
All line art is pure vector, so the PDFs are sharp at any size.
"""
import importlib, math, pathlib, subprocess, sys, shutil
from prims import Pal, W, H, star, heart, circle, path, line, ellipse, rect, poly, sparkle, g

HERE = pathlib.Path(__file__).parent
OUT = HERE / "output"
BOOKS = ["book_animals", "book_sea", "book_vehicles"]
BRAND_AR, BRAND_EN = "بيبي يوسف", "Baby Yusuf"
AR_DIGITS = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")
_uid = [0]


def uid():
    _uid[0] += 1
    return f"u{_uid[0]}"


def art_svg(fn, color=False, width="100%", border=10, radius=44):
    k = uid()
    return (
        f'<svg viewBox="-8 -8 {W + 16} {H + 16}" width="{width}" xmlns="http://www.w3.org/2000/svg">'
        f'<defs><clipPath id="{k}"><rect width="{W}" height="{H}" rx="{radius}"/></clipPath></defs>'
        f'<g clip-path="url(#{k})">{fn(Pal(color))}</g>'
        f'<rect width="{W}" height="{H}" rx="{radius}" fill="none" stroke="#000" stroke-width="{border}"/></svg>'
    )


def outlined(text, size=110, fill="#fff", stroke="#000", sw=12, w=1000, h=150, y=None, font="Lalezar", extra=""):
    y = y or h * .78
    return (
        f'<svg viewBox="0 0 {w} {h}" width="100%" xmlns="http://www.w3.org/2000/svg">{extra}'
        f'<text x="{w / 2}" y="{y}" text-anchor="middle" direction="rtl" font-family="{font}" font-size="{size}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round" paint-order="stroke">{text}</text></svg>'
    )


def star_badge(n, label="لوّنتها!"):
    s = star(40, 40, 34, "#fff", 4)
    return f'<div class="done"><svg viewBox="0 0 80 80" width="38">{s}</svg><span dir="rtl">{label}</span></div>'


CSS = """
@font-face{font-family:Lalezar;src:url('FONT_L')}
@font-face{font-family:Marhey;src:url('FONT_M')}
@page{size:8.5in 11in;margin:0}
*{box-sizing:border-box}
html,body{margin:0;padding:0;background:#fff}
body{font-family:Marhey,Lalezar,sans-serif;color:#000;-webkit-print-color-adjust:exact;print-color-adjust:exact}
.page{width:8.5in;height:11in;position:relative;overflow:hidden;page-break-after:always;break-after:page;display:flex;flex-direction:column;align-items:center;padding:.42in .6in .38in}
.page:last-child{page-break-after:auto;break-after:auto}
.ttl{width:100%;height:1.12in;display:flex;align-items:center;justify-content:center}
.ttl svg{height:1.12in;width:auto}
.art{width:100%;margin-top:.04in}
.foot{width:100%;display:flex;justify-content:space-between;align-items:center;margin-top:.08in;font-size:15px}
.done{display:flex;align-items:center;gap:6px;font-family:Marhey;font-weight:600}
.num{font-family:Lalezar;font-size:20px;border:3px solid #000;border-radius:999px;min-width:44px;height:44px;display:flex;align-items:center;justify-content:center}
.en{font-family:Lalezar;font-size:22px;letter-spacing:1px;min-width:1.6in}
.done{min-width:1.6in;justify-content:flex-end}
.mid{display:flex;align-items:center;gap:8px}
.brand{font-family:Lalezar;font-size:15px;color:#555;letter-spacing:.5px}
.blank{display:block}
.blank .note{position:absolute;bottom:.5in;width:100%;left:0;text-align:center;font-size:13px;color:#999}
"""


def coloring_page(i, ar, en, fn):
    return (
        f'<section class="page"><div class="ttl">{outlined(ar, 120, h=150, w=900)}</div>'
        f'<div class="art">{art_svg(fn)}</div>'
        f'<div class="foot"><span class="en">{en}</span><span class="mid"><span class="num">{str(i).translate(AR_DIGITS)}</span><span class="brand">© {BRAND_EN}</span></span>{star_badge(i)}</div></section>'
    )


def blank_page():
    return '<section class="page blank"><div class="note">هذه الصفحة فارغة عمداً حتى لا تتسرّب الألوان للرسمة التالية</div></section>'


# ---------------------------------------------------------------- extra pages
def deco_border(color=False, accent="#ffd84d"):
    """Stars and hearts around the edge of an 1000x1300 frame."""
    o = '<rect x="20" y="20" width="960" height="1260" rx="50" fill="none" stroke="#000" stroke-width="9"/>'
    o += '<rect x="44" y="44" width="912" height="1212" rx="34" fill="none" stroke="#000" stroke-width="4" stroke-dasharray="2 16" stroke-linecap="round"/>'
    pts = [(90, 90), (910, 90), (90, 1210), (910, 1210)]
    for x, y in pts:
        o += star(x, y, 46, accent if color else "#fff", 7)
    return o


def name_page(book):
    c = Pal(False)
    o = deco_border()
    o += f'<text x="500" y="200" text-anchor="middle" direction="rtl" font-family="Lalezar" font-size="118" fill="#fff" stroke="#000" stroke-width="12" paint-order="stroke" stroke-linejoin="round">هذا الكتاب ملك</text>'
    for y, label in [(330, "الاسم:"), (430, "العمر:")]:
        o += f'<text x="840" y="{y}" text-anchor="start" direction="rtl" font-family="Marhey" font-weight="700" font-size="46">{label}</text>'
        o += line(f"M160,{y + 8}L690,{y + 8}", 5).replace('stroke-width="5"', 'stroke-width="5" stroke-dasharray="4 14"')
    o += rect(150, 500, 700, 620, 40, "#fff", 7)
    o += f'<text x="500" y="1180" text-anchor="middle" direction="rtl" font-family="Marhey" font-weight="700" font-size="42">ارسم نفسك هنا!</text>'
    for x, y, s in [(205, 560, .9), (795, 560, .9), (205, 1065, .9), (795, 1065, .9)]:
        o += heart(x, y, s)
    o += f'<text x="500" y="1238" text-anchor="middle" direction="rtl" font-family="Lalezar" font-size="34">© {BRAND_AR} · {BRAND_EN}</text>'
    return f'<section class="page"><svg viewBox="0 0 1000 1300" width="100%" height="100%">{o}</svg></section>'


def crayon(x, y, s=1):
    o = path(f"M{x},{y}L{x + 150 * s},{y}L{x + 150 * s},{y + 46 * s}L{x},{y + 46 * s}Z")
    o += path(f"M{x + 150 * s},{y}L{x + 195 * s},{y + 16 * s}Q{x + 205 * s},{y + 23 * s} {x + 195 * s},{y + 30 * s}L{x + 150 * s},{y + 46 * s}Z")
    o += line(f"M{x + 30 * s},{y}L{x + 30 * s},{y + 46 * s}M{x + 120 * s},{y}L{x + 120 * s},{y + 46 * s}", 5)
    o += path(f"M{x},{y}Q{x - 16 * s},{y + 23 * s} {x},{y + 46 * s}Z")
    return o


def test_page(book):
    o = deco_border()
    o += '<text x="500" y="200" text-anchor="middle" direction="rtl" font-family="Lalezar" font-size="112" fill="#fff" stroke="#000" stroke-width="12" paint-order="stroke" stroke-linejoin="round">جرّب ألوانك هنا!</text>'
    o += '<text x="500" y="275" text-anchor="middle" direction="rtl" font-family="Marhey" font-weight="600" font-size="34">لوّن كل قلم بلون مختلف لتعرف شكل ألوانك قبل البدء</text>'
    for r in range(7):
        for col in range(3):
            o += crayon(110 + col * 280, 340 + r * 128, 1)
    return f'<section class="page"><svg viewBox="0 0 1000 1300" width="100%" height="100%">{o}</svg></section>'


def chart_page(book):
    pages = book["pages"]
    cells = ""
    for i, (ar, en, fn) in enumerate(pages, 1):
        cells += (
            f'<div class="cell"><div class="thumb">{art_svg(fn, border=14, radius=60)}</div>'
            f'<div class="lab"><span>{ar}</span><svg viewBox="0 0 80 80" width="52">{star(40, 40, 36, "#fff", 4.5)}</svg></div></div>'
        )
    return (
        '<section class="page"><style>.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:.12in .16in;width:100%;margin-top:.1in}'
        '.cell{display:flex;flex-direction:column;align-items:center}.thumb{width:100%}.lab{display:flex;align-items:center;gap:6px;font-family:Lalezar;font-size:22px;margin-top:2px}</style>'
        f'<div class="ttl">{outlined("لوحة نجومي", 120, h=150, w=900)}</div>'
        '<div style="font-family:Marhey;font-weight:600;font-size:17px;text-align:center" dir="rtl">كلما أنهيت تلوين رسمة، لوّن النجمة التي بجانبها. اجمع كل النجوم واحصل على شهادتك!</div>'
        f'<div class="grid" dir="rtl">{cells}</div></section>'
    )


def rosette(cx, cy, r):
    o = path(f"M{cx - r * .5},{cy + r * .6}L{cx - r * .8},{cy + r * 1.9}L{cx - r * .45},{cy + r * 1.65}L{cx - r * .25},{cy + r * 2}L{cx},{cy + r * .7}Z")
    o += path(f"M{cx + r * .5},{cy + r * .6}L{cx + r * .8},{cy + r * 1.9}L{cx + r * .45},{cy + r * 1.65}L{cx + r * .25},{cy + r * 2}L{cx},{cy + r * .7}Z")
    from prims import fluffy
    o += fluffy(cx, cy, r, 16)
    o += circle(cx, cy, r * .72) + star(cx, cy, r * .5)
    return o


def certificate_page(book):
    o = deco_border()
    o += rosette(500, 300, 120)
    o += '<text x="500" y="640" text-anchor="middle" direction="rtl" font-family="Lalezar" font-size="104" fill="#fff" stroke="#000" stroke-width="12" paint-order="stroke" stroke-linejoin="round">شهادة الفنان الصغير</text>'
    o += '<text x="500" y="740" text-anchor="middle" direction="rtl" font-family="Marhey" font-weight="600" font-size="40">تُمنح هذه الشهادة بكل فخر إلى</text>'
    o += line("M180,850L820,850", 5).replace('stroke-width="5"', 'stroke-width="5" stroke-dasharray="4 14"')
    o += f'<text x="500" y="950" text-anchor="middle" direction="rtl" font-family="Marhey" font-weight="600" font-size="36">لإكمال تلوين كتاب «{book["title"]}»</text>'
    o += '<text x="500" y="1005" text-anchor="middle" direction="rtl" font-family="Marhey" font-weight="600" font-size="36">بإبداع وتميّز. أحسنت يا بطل!</text>'
    for x, lab in [(770, "التاريخ"), (230, "التوقيع")]:
        o += line(f"M{x - 140},1130L{x + 140},1130", 5)
        o += f'<text x="{x}" y="1180" text-anchor="middle" font-family="Marhey" font-weight="600" font-size="32">{lab}</text>'
    o += star(500, 1140, 38) + star(420, 1160, 20) + star(580, 1160, 20)
    o += f'<text x="500" y="1238" text-anchor="middle" direction="rtl" font-family="Lalezar" font-size="34">من {BRAND_AR} · {BRAND_EN}</text>'
    return f'<section class="page"><svg viewBox="0 0 1000 1300" width="100%" height="100%">{o}</svg></section>'


# ---------------------------------------------------------------- cover
def cover_page(book):
    bg1, bg2 = book["cover_bg"]
    acc = book["accent"]
    byname = {fn.__name__: (ar, fn) for ar, en, fn in book["pages"]}
    tiles = ""
    for i, name in enumerate(book["cover_pages"]):
        ar, fn = byname[name]
        rot = [-5, 4, 3, -4][i]
        tiles += f'<div class="tile" style="transform:rotate({rot}deg)">{art_svg(fn, color=True, border=12)}</div>'
    n = str(len(book["pages"])).translate(AR_DIGITS)
    burst = star(100, 100, 92, "#ff4d6d", 6, inner=.78).replace('<path', '<path ') + f'<text x="100" y="98" text-anchor="middle" font-family="Lalezar" font-size="52" fill="#fff">{n}</text><text x="100" y="140" text-anchor="middle" font-family="Lalezar" font-size="32" fill="#fff">رسمة</text>'
    sp = "".join(f'<div class="sp" style="left:{x}%;top:{y}%;width:{s}px">{f"<svg viewBox=\'0 0 80 80\'>{star(40, 40, 34, c, 4)}</svg>"}</div>' for x, y, s, c in [(6, 5, 46, "#ffd84d"), (88, 4, 40, "#6ec6ff"), (4, 60, 34, "#ff9ec7"), (91, 63, 38, "#b39cff"), (72, 12, 28, "#7cc96b")])
    return f"""<section class="page cover" style="background:linear-gradient(170deg,{bg1},{bg2});padding:.5in .55in">
<style>.cover .tiles{{display:grid;grid-template-columns:1fr 1fr;gap:.18in;width:70%;margin-top:.12in}}
.cover .tile{{background:#fff;padding:.08in;border-radius:.2in;box-shadow:0 .06in .14in rgba(0,0,0,.18)}}
.cover .sub{{font-family:Lalezar;font-size:34px;background:{acc};color:#fff;border:4px solid #000;border-radius:999px;padding:.02in .4in .06in;margin-top:.02in}}
.cover .en{{font-family:Lalezar;font-size:30px;letter-spacing:2px;margin-top:.05in}}
.cover .burst{{position:absolute;right:.35in;bottom:.45in;width:1.55in;transform:rotate(12deg)}}
.cover .age{{position:absolute;left:.45in;bottom:.6in;font-family:Lalezar;font-size:30px;background:#fff;border:4px solid #000;border-radius:.2in;padding:.06in .22in;transform:rotate(-6deg)}}
.cover .sp{{position:absolute}}
.cover .logo{{display:flex;align-items:center;gap:8px;font-family:Lalezar;font-size:26px;background:#fff;border:4px solid #000;border-radius:999px;padding:.02in .3in .04in;margin-bottom:-.05in}}</style>
{sp}
<div class="logo"><span>{BRAND_AR}</span><svg viewBox="0 0 60 60" width="30">{heart(30, 32, .7, "#ff4d6d", 5)}</svg><span>{BRAND_EN}</span></div>
<div style="width:100%">{outlined(book["title"], 150, fill=acc, sw=16, h=190, w=1000, y=150)}</div>
<div class="sub" dir="rtl">{book["subtitle"]}</div>
<div class="en">{book["en_title"].upper()}</div>
<div class="tiles">{tiles}</div>
<svg class="burst" viewBox="0 0 200 200">{burst}</svg>
<div class="age" dir="rtl">للأعمار ٣ - ٨</div>
</section>"""


# ---------------------------------------------------------------- assemble
def html_doc(body):
    css = CSS.replace("FONT_L", (HERE / "fonts/Lalezar-Regular.ttf").as_uri()).replace("FONT_M", (HERE / "fonts/Marhey.ttf").as_uri())
    return f'<!doctype html><html lang="ar"><head><meta charset="utf-8"><style>{css}</style></head><body>{body}</body></html>'


def render(html, out):
    tmp = out.with_suffix(".html")
    tmp.write_text(html)
    subprocess.run(["node", str(HERE / "shot.js"), str(tmp), str(out), "816"], check=True)
    tmp.unlink()


def build(modname):
    book = importlib.import_module(modname).BOOK
    d = OUT / book["slug"]
    if d.exists():
        shutil.rmtree(d)
    (d / "pages-300dpi").mkdir(parents=True)
    slug = book["slug"]
    cover = cover_page(book)
    front = [name_page(book), test_page(book)]
    pages = [coloring_page(i, ar, en, fn) for i, (ar, en, fn) in enumerate(book["pages"], 1)]
    back = [chart_page(book), certificate_page(book)]

    printable = [cover] + front + pages + back
    render(html_doc("".join(printable)), d / f"{slug}-printable.pdf")

    kdp = [front[0], blank_page(), front[1], blank_page()]
    for p in pages:
        kdp += [p, blank_page()]
    kdp += [back[0], blank_page(), back[1]]
    if len(kdp) % 2:
        kdp.append(blank_page())
    render(html_doc("".join(kdp)), d / f"{slug}-kdp-interior.pdf")

    render(html_doc(cover), d / "cover.pdf")
    subprocess.run(["pdftoppm", "-r", "300", "-png", "-singlefile", str(d / "cover.pdf"), str(d / f"{slug}-cover")], check=True)
    (d / "cover.pdf").unlink()
    subprocess.run(["pdftoppm", "-r", "300", "-png", "-gray", str(d / f"{slug}-printable.pdf"), str(d / "pages-300dpi" / "page")], check=True)
    # page 1 is the colour cover: re-render it in colour
    first = sorted((d / "pages-300dpi").glob("page-*.png"))[0]
    shutil.copy(d / f"{slug}-cover.png", first)
    print("built", d)


if __name__ == "__main__":
    for m in sys.argv[1:] or BOOKS:
        build(m)
