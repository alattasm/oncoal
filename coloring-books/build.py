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
BRAND_EN = "Baby Yusuf"
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


def outlined(text, size=110, fill="#fff", stroke="#000", sw=12, w=1000, h=150, y=None, font="Fredoka", extra=""):
    y = y or h * .78
    size = min(size, w * 1.6 / max(len(text), 1))  # shrink long titles to fit
    return (
        f'<svg viewBox="0 0 {w} {h}" width="100%" xmlns="http://www.w3.org/2000/svg">{extra}'
        f'<text x="{w / 2}" y="{y}" text-anchor="middle" font-family="{font}" font-size="{size}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round" paint-order="stroke">{text}</text></svg>'
    )


def star_badge(n, label="I colored it!"):
    s = star(40, 40, 34, "#fff", 4)
    return f'<div class="done"><svg viewBox="0 0 80 80" width="38">{s}</svg><span>{label}</span></div>'


CSS = """
@font-face{font-family:Fredoka;src:url('FONT_F');font-weight:300 700}
svg text{font-weight:700}
@page{size:8.5in 11in;margin:0}
*{box-sizing:border-box}
html,body{margin:0;padding:0;background:#fff}
body{font-family:Fredoka,sans-serif;font-weight:600;color:#000;-webkit-print-color-adjust:exact;print-color-adjust:exact}
.page{width:8.5in;height:11in;position:relative;overflow:hidden;page-break-after:always;break-after:page;display:flex;flex-direction:column;align-items:center;padding:.42in .6in .38in}
.page:last-child{page-break-after:auto;break-after:auto}
.ttl{width:100%;height:1.12in;display:flex;align-items:center;justify-content:center}
.ttl svg{height:1.12in;width:auto}
.art{width:100%;margin-top:.04in}
.foot{width:100%;display:flex;justify-content:space-between;align-items:center;margin-top:.08in;font-size:15px}
.done{display:flex;align-items:center;gap:6px;font-family:Fredoka;font-weight:600}
.num{font-family:Fredoka;font-size:20px;border:3px solid #000;border-radius:999px;min-width:44px;height:44px;display:flex;align-items:center;justify-content:center}
.en{font-family:Fredoka;font-size:22px;letter-spacing:1px;min-width:1.6in}
.done{min-width:1.6in;justify-content:flex-end}
.mid{display:flex;align-items:center;gap:8px}
.brand{font-family:Fredoka;font-size:15px;color:#555;letter-spacing:.5px}
.blank{display:block}
.blank .note{position:absolute;bottom:.5in;width:100%;left:0;text-align:center;font-size:13px;color:#999}
"""


def coloring_page(i, ar, en, fn):
    return (
        f'<section class="page"><div class="ttl">{outlined(en, 120, h=150, w=900)}</div>'
        f'<div class="art">{art_svg(fn)}</div>'
        f'<div class="foot"><span class="en brand">© {BRAND_EN}</span><span class="num">{i}</span>{star_badge(i)}</div></section>'
    )


def blank_page():
    return '<section class="page blank"><div class="note">This page is intentionally left blank to prevent colors from bleeding through.</div></section>'


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
    o += f'<text x="500" y="175" text-anchor="middle" font-family="Fredoka" font-size="110" fill="#fff" stroke="#000" stroke-width="12" paint-order="stroke" stroke-linejoin="round">This Book</text>'
    o += f'<text x="500" y="285" text-anchor="middle" font-family="Fredoka" font-size="110" fill="#fff" stroke="#000" stroke-width="12" paint-order="stroke" stroke-linejoin="round">Belongs To</text>'
    for y, label in [(390, "Name:"), (475, "Age:")]:
        o += f'<text x="160" y="{y}" text-anchor="start" font-family="Fredoka" font-weight="700" font-size="46">{label}</text>'
        o += line(f"M330,{y + 8}L840,{y + 8}", 5).replace('stroke-width="5"', 'stroke-width="5" stroke-dasharray="4 14"')
    o += rect(150, 530, 700, 590, 40, "#fff", 7)
    o += f'<text x="500" y="1180" text-anchor="middle" font-family="Fredoka" font-weight="700" font-size="42">Draw yourself here!</text>'
    for x, y, s in [(205, 590, .9), (795, 590, .9), (205, 1065, .9), (795, 1065, .9)]:
        o += heart(x, y, s)
    o += f'<text x="500" y="1238" text-anchor="middle" font-family="Fredoka" font-size="34">© {BRAND_EN}</text>'
    return f'<section class="page"><svg viewBox="0 0 1000 1300" width="100%" height="100%">{o}</svg></section>'


def crayon(x, y, s=1):
    o = path(f"M{x},{y}L{x + 150 * s},{y}L{x + 150 * s},{y + 46 * s}L{x},{y + 46 * s}Z")
    o += path(f"M{x + 150 * s},{y}L{x + 195 * s},{y + 16 * s}Q{x + 205 * s},{y + 23 * s} {x + 195 * s},{y + 30 * s}L{x + 150 * s},{y + 46 * s}Z")
    o += line(f"M{x + 30 * s},{y}L{x + 30 * s},{y + 46 * s}M{x + 120 * s},{y}L{x + 120 * s},{y + 46 * s}", 5)
    o += path(f"M{x},{y}Q{x - 16 * s},{y + 23 * s} {x},{y + 46 * s}Z")
    return o


def test_page(book):
    o = deco_border()
    o += '<text x="500" y="180" text-anchor="middle" font-family="Fredoka" font-size="84" fill="#fff" stroke="#000" stroke-width="11" paint-order="stroke" stroke-linejoin="round">Test Your Colors!</text>'
    o += '<text x="500" y="245" text-anchor="middle" font-family="Fredoka" font-weight="600" font-size="34">Color each crayon to see how</text><text x="500" y="290" text-anchor="middle" font-family="Fredoka" font-weight="600" font-size="34">your colors look before you start!</text>'
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
            f'<div class="lab"><span>{en}</span><svg viewBox="0 0 80 80" width="52">{star(40, 40, 36, "#fff", 4.5)}</svg></div></div>'
        )
    return (
        '<section class="page"><style>.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:.12in .16in;width:100%;margin-top:.1in}'
        '.cell{display:flex;flex-direction:column;align-items:center}.thumb{width:100%}.lab{display:flex;align-items:center;gap:4px;font-family:Fredoka;font-weight:700;font-size:16px;white-space:nowrap;margin-top:2px}</style>'
        f'<div class="ttl">{outlined("My Star Chart", 120, h=150, w=900)}</div>'
        '<div style="font-family:Fredoka;font-weight:600;font-size:17px;text-align:center">Each time you finish a picture, color its star. Collect all the stars to earn your certificate!</div>'
        f'<div class="grid">{cells}</div></section>'
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
    o += rosette(500, 230, 100)
    big = 'fill="#fff" stroke="#000" stroke-width="12" paint-order="stroke" stroke-linejoin="round"'
    o += f'<text x="500" y="555" text-anchor="middle" font-family="Fredoka" font-size="100" {big}>Little Artist</text><text x="500" y="660" text-anchor="middle" font-family="Fredoka" font-size="100" {big}>Certificate</text>'
    o += f'<text x="500" y="745" text-anchor="middle" font-family="Fredoka" font-weight="600" font-size="38">This certificate is proudly presented to</text>'
    o += line("M180,850L820,850", 5).replace('stroke-width="5"', 'stroke-width="5" stroke-dasharray="4 14"')
    for y, t, wgt in [(925, "for completing the coloring book", 600), (972, f"“{book['en_title']}”", 700), (1019, "with creativity and great colors.", 600), (1066, "Well done, superstar!", 700)]:
        o += f'<text x="500" y="{y}" text-anchor="middle" font-family="Fredoka" font-weight="{wgt}" font-size="34">{t}</text>'
    for x, lab in [(230, "Date"), (770, "Signature")]:
        o += line(f"M{x - 140},1150L{x + 140},1150", 5)
        o += f'<text x="{x}" y="1192" text-anchor="middle" font-family="Fredoka" font-weight="600" font-size="30">{lab}</text>'
    o += star(500, 1160, 34) + star(425, 1175, 18) + star(575, 1175, 18)
    o += f'<text x="500" y="1240" text-anchor="middle" font-family="Fredoka" font-size="30">Presented by {BRAND_EN}</text>'
    return f'<section class="page"><svg viewBox="0 0 1000 1300" width="100%" height="100%">{o}</svg></section>'


# ---------------------------------------------------------------- cover
def cover_title(t, acc):
    words = t.split()
    if len(t) > 13 and len(words) > 1:
        k = min(range(1, len(words)), key=lambda i: abs(len(" ".join(words[:i])) - len(" ".join(words[i:]))))
        lines = [" ".join(words[:k]), " ".join(words[k:])]
    else:
        lines = [t]
    size = min(150, min(1000 * 1.6 / len(l) for l in lines))
    h = int(size * 1.02 * len(lines) + 40)
    txt = "".join(f'<text x="500" y="{size * (i + .9) + 10:.0f}" text-anchor="middle" font-family="Fredoka" font-size="{size:.0f}" fill="{acc}" stroke="#000" stroke-width="16" stroke-linejoin="round" paint-order="stroke">{l}</text>' for i, l in enumerate(lines))
    return f'<div style="width:100%"><svg viewBox="0 0 1000 {h}" width="100%">{txt}</svg></div>'


def cover_page(book):
    bg1, bg2 = book["cover_bg"]
    acc = book["accent"]
    byname = {fn.__name__: (ar, fn) for ar, en, fn in book["pages"]}
    tiles = ""
    for i, name in enumerate(book["cover_pages"]):
        ar, fn = byname[name]
        rot = [-5, 4, 3, -4][i]
        tiles += f'<div class="tile" style="transform:rotate({rot}deg)">{art_svg(fn, color=True, border=12)}</div>'
    n = len(book["pages"])
    burst = star(100, 100, 92, "#ff4d6d", 6, inner=.78).replace('<path', '<path ') + f'<text x="100" y="98" text-anchor="middle" font-family="Fredoka" font-size="52" fill="#fff">{n}</text><text x="100" y="140" text-anchor="middle" font-family="Fredoka" font-size="32" fill="#fff">PAGES</text>'
    sp = "".join(f'<div class="sp" style="left:{x}%;top:{y}%;width:{s}px">{f"<svg viewBox=\'0 0 80 80\'>{star(40, 40, 34, c, 4)}</svg>"}</div>' for x, y, s, c in [(6, 5, 46, "#ffd84d"), (88, 4, 40, "#6ec6ff"), (4, 60, 34, "#ff9ec7"), (91, 63, 38, "#b39cff"), (7, 33, 28, "#7cc96b")])
    return f"""<section class="page cover" style="background:linear-gradient(170deg,{bg1},{bg2});padding:.5in .55in">
<style>.cover .tiles{{display:grid;grid-template-columns:1fr 1fr;gap:.16in;width:64%;margin-top:.1in}}
.cover .tile{{background:#fff;padding:.08in;border-radius:.2in;box-shadow:0 .06in .14in rgba(0,0,0,.18)}}
.cover .sub{{font-family:Fredoka;font-size:34px;background:{acc};color:#fff;border:4px solid #000;border-radius:999px;padding:.02in .4in .06in;margin-top:.02in}}
.cover .en{{font-family:Fredoka;font-size:30px;letter-spacing:2px;margin-top:.05in}}
.cover .burst{{position:absolute;right:.35in;bottom:.45in;width:1.55in;transform:rotate(12deg)}}
.cover .age{{position:absolute;left:.45in;bottom:.6in;font-family:Fredoka;font-size:30px;background:#fff;border:4px solid #000;border-radius:.2in;padding:.06in .22in;transform:rotate(-6deg)}}
.cover .sp{{position:absolute}}
.cover .logo{{display:flex;align-items:center;gap:8px;font-family:Fredoka;font-size:26px;background:#fff;border:4px solid #000;border-radius:999px;padding:.02in .3in .04in;margin-bottom:-.05in}}</style>
{sp}
<div class="logo"><svg viewBox="0 0 60 60" width="30">{heart(30, 32, .7, "#ff4d6d", 5)}</svg><span>{BRAND_EN}</span></div>
{cover_title(book["en_title"], acc)}
<div class="sub">Coloring Book for Kids</div>
<div class="tiles">{tiles}</div>
<svg class="burst" viewBox="0 0 200 200">{burst}</svg>
<div class="age">Ages 3 - 8</div>
</section>"""


# ---------------------------------------------------------------- assemble
def full_cover(book, n_pages):
    """KDP paperback wrap cover: back + spine + front, 0.125in bleed all round.
    White paper spine = pages x 0.002252in. Under 79 pages KDP forbids spine text."""
    bleed, trim_w, trim_h = .125, 8.5, 11
    spine = n_pages * .002252
    W_ = bleed * 2 + trim_w * 2 + spine
    H_ = trim_h + bleed * 2
    bg1, bg2 = book["cover_bg"]
    acc = book["accent"]
    front = cover_page(book).replace('<section class="page cover" style="background:linear-gradient(170deg,{0},{1});padding:.5in .55in">'.format(bg1, bg2),
        f'<section class="page cover" style="position:absolute;top:0;left:{bleed + trim_w + spine:.4f}in;width:{trim_w + bleed}in;height:{H_}in;background:transparent;padding:.6in .68in .6in .55in">')
    front = front.replace(".cover .burst{{position:absolute;right:.35in;bottom:.45in".replace("{{", "{"), ".cover .burst{position:absolute;right:.5in;bottom:.6in")
    front = front.replace(".cover .age{position:absolute;left:.45in;bottom:.6in", ".cover .age{position:absolute;left:.5in;bottom:.75in")
    others = [fn for ar, en, fn in book["pages"] if fn.__name__ not in book["cover_pages"]][:6]
    thumbs = "".join(f'<div class="bt">{art_svg(fn, color=True, border=14)}</div>' for fn in others)
    n = len(book["pages"])
    bullets = [f"{n} adorable, original illustrations", "Big, bold lines perfect for little hands",
               "Single-sided pages - no bleed-through", "Bonus: Star Chart & Little Artist Certificate",
               "Large 8.5 x 11 inch pages"]
    back = f"""<div class="back" style="position:absolute;top:0;left:0;width:{bleed + trim_w}in;height:{H_}in;padding:{bleed + .55}in .6in .6in {bleed + .6}in">
<style>.back{{display:flex;flex-direction:column;align-items:center;font-family:Fredoka}}
.back .logo{{display:flex;align-items:center;gap:8px;font-weight:700;font-size:24px;background:#fff;border:4px solid #000;border-radius:999px;padding:.02in .3in .04in}}
.back h2{{font-size:46px;margin:.18in 0 .06in;color:{acc};-webkit-text-stroke:2px #000;paint-order:stroke fill;text-align:center}}
.back p.lead{{font-size:19px;font-weight:600;text-align:center;margin:0 .2in .12in;line-height:1.35}}
.back ul{{list-style:none;padding:0;margin:0 0 .16in;font-size:19px;font-weight:600;background:#fff;border:4px solid #000;border-radius:.2in;padding:.12in .3in;width:88%}}
.back li{{margin:.04in 0}} .back li:before{{content:"★ ";color:{acc}}}
.back .grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:.14in;width:82%}}
.back .bt{{background:#fff;padding:.05in;border-radius:.14in;box-shadow:0 .04in .1in rgba(0,0,0,.15)}}</style>
<div class="logo"><svg viewBox="0 0 60 60" width="28">{heart(30, 32, .7, "#ff4d6d", 5)}</svg><span>{BRAND_EN}</span></div>
<h2>Hours of Coloring Fun!</h2>
<p class="lead">Let your little one's imagination shine with cute, happy pictures made just for small hands and big smiles.</p>
<ul>{"".join(f"<li>{b}</li>" for b in bullets)}</ul>
<div class="grid">{thumbs}</div>
</div>"""
    css = f"@page{{size:{W_:.4f}in {H_}in;margin:0}} body{{width:{W_:.4f}in;height:{H_}in;position:relative;overflow:hidden;background:linear-gradient(170deg,{bg1},{bg2})}}"
    return f"<style>{css}</style>" + back + front, W_, H_, spine


def html_doc(body):
    css = CSS.replace("FONT_F", (HERE / "fonts/Fredoka.ttf").as_uri())
    return f'<!doctype html><html lang="en"><head><meta charset="utf-8"><style>{css}</style></head><body>{body}</body></html>'


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

    n_int = int(subprocess.run(["pdfinfo", str(d / f"{slug}-kdp-interior.pdf")], capture_output=True, text=True).stdout.split("Pages:")[1].split()[0])
    body, cw, ch, spine = full_cover(book, n_int)
    render(html_doc(body), d / f"{slug}-kdp-cover.pdf")
    print(f"  KDP cover {cw:.3f} x {ch:.3f} in, spine {spine:.4f} in, interior {n_int} pages")
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
