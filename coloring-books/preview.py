"""Render a contact sheet of a book's art (line + colour) for quick visual checks."""
import sys, importlib, pathlib, asyncio
from prims import Pal, W, H
import subprocess

HERE = pathlib.Path(__file__).parent
mod = importlib.import_module(sys.argv[1])
color = len(sys.argv) > 2 and sys.argv[2] == "color"
only = [a for a in sys.argv[3:] if not a.endswith(".png")] or None
cells = []
for ar, en, fn in mod.BOOK["pages"]:
    if only and fn.__name__ not in only: continue
    cells.append(f'<div><svg viewBox="0 0 {W} {H}" width="330" height="380"><defs><clipPath id="k{en}"><rect width="{W}" height="{H}" rx="40"/></clipPath></defs><g clip-path="url(#k{en})">{fn(Pal(color))}</g><rect width="{W}" height="{H}" rx="40" fill="none" stroke="#000" stroke-width="10"/></svg><p>{en}</p></div>')
html = f"""<html><head><style>@font-face{{font-family:Fredoka;src:url('{(HERE/'fonts/Fredoka.ttf').as_uri()}');font-weight:300 700}} body{{display:flex;flex-wrap:wrap;gap:10px;margin:10px;background:#fff}} p{{margin:0;text-align:center;font:14px sans-serif}}</style></head><body>{''.join(cells)}</body></html>"""
out = HERE.parent / "coloring-books" / "_preview.html"
out.write_text(html)
png = sys.argv[-1] if sys.argv[-1].endswith('.png') else "/tmp/claude-0/-home-user-oncoal/bc9ba23f-c93d-57d1-9314-8fa95f4b00c5/scratchpad/prev.png"
subprocess.run(["node", str(HERE / "shot.js"), str(out), png], check=True)
out.unlink()
