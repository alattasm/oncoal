"""Replace the cartoon-character print on Yuyu's sweater with the bluebird print, frame by frame.

Per frame: find the print as neutral/bluish black blobs sitting on the royal-blue sweater (hair is brown, letter
eyes are small) plus the warm-white areas next to them (skin is excluded), inpaint them blue,
then paste the bird print (bird_print.png) over the print's smoothed box - clipped to sweater pixels so hands and
arms in front of the chest stay in front. Box position/size are smoothed over time to avoid jitter.

Usage: python3 shirt_swap.py IN.mp4 OUT.mp4 [preview_t ...]
"""
import os, subprocess, sys
import numpy as np, cv2
from PIL import Image
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
SRC, OUT = sys.argv[1], sys.argv[2]
PREV = [float(a) for a in sys.argv[3:]]
SW, SH, FPS = 1024, 576, 24
BIRD = Image.open(os.path.join(HERE, 'bird_print.png')).convert('RGBA')
BA = BIRD.width / BIRD.height


def analyse(im):
    a = im.astype(int); r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx = a.max(2); mn = a.min(2)
    sweater = (b > r + 50) & (b > g + 30) & (g < 140)                       # royal-blue clothes (incl. shadows)
    black = (mx < 80) & (b >= r - 5) & (b - r < 50)                         # print black: neutral/bluish (hair is brown)
    lab, n = ndi.label(ndi.binary_closing(black, iterations=2))
    if n == 0: return dict(sweater=sweater, prt=None)
    sizes = ndi.sum(black, lab, range(1, n + 1))
    # the print = the largest black blob whose outline partly touches the royal-blue sweater
    best, best_sz = None, 0
    for i in np.argsort(sizes)[::-1][:6]:
        sz = sizes[i]
        if sz < 120: break
        blob = lab == i + 1
        ring = ndi.binary_dilation(blob, iterations=3) & ~blob
        if (ring & sweater).sum() > 0.2 * max(ring.sum(), 1) and sz > best_sz:
            best, best_sz = blob, sz
    if best is None: return dict(sweater=sweater, prt=None)
    blk = best & black
    white = (mn > 165) & (r - b < 50) & (g - b < 35)                        # warm white of the print (skin is excluded)
    body = ndi.binary_fill_holes(ndi.binary_closing(sweater | blk, iterations=4))
    prt = blk | (white & ndi.binary_dilation(blk, iterations=40) & body)
    if prt.sum() < 250: return dict(sweater=sweater, prt=None)
    py, px = np.where(prt)
    return dict(sweater=sweater, prt=prt, box=(px.min(), py.min(), px.max(), py.max()), c=(px.mean(), py.mean()))


def frames():
    p = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-i', SRC, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    n = SW * SH * 3
    while True:
        b = p.stdout.read(n)
        if len(b) < n: break
        yield np.frombuffer(b, np.uint8).reshape(SH, SW, 3)


# pass 1: detect boxes, smooth them
info = []
for f in frames():
    d = analyse(f)
    info.append((d['c'][0], d['c'][1], d['box'][2] - d['box'][0], d['box'][3] - d['box'][1]) if d and d.get('prt') is not None else None)
N = len(info); arr = np.full((N, 4), np.nan)
for i, v in enumerate(info):
    if v: arr[i] = v
valid = ~np.isnan(arr[:, 0])
print(f'print found in {valid.sum()} / {N} frames')
for c in range(4):                                   # fill short gaps, then smooth
    idx = np.where(valid)[0]
    arr[:, c] = np.interp(np.arange(N), idx, arr[idx, c])
    k = 7 if c < 2 else 15
    arr[:, c] = ndi.uniform_filter1d(arr[:, c], k, mode='nearest')
# don't draw the bird during long stretches with no print (turned away / fully covered)
gap = ~valid; run = ndi.label(gap)[0]; long_gap = np.zeros(N, bool)
for j in range(1, run.max() + 1):
    if (run == j).sum() > 12: long_gap |= run == j


def process(f, i):
    d = analyse(f); out = f.copy()
    if d is None: return out
    if d.get('prt') is not None:                     # remove the old print: fill with the surrounding sweater blue
        m = ndi.binary_dilation(d['prt'], iterations=6)
        src_ok = (d['sweater'] & ~m).astype(np.float32)
        num = cv2.GaussianBlur(f.astype(np.float32) * src_ok[..., None], (0, 0), 18)
        den = cv2.GaussianBlur(src_ok, (0, 0), 18)[..., None]
        fill = np.where(den > 0.02, num / np.maximum(den, 1e-3), np.array([20, 60, 190], np.float32))
        soft = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 2)[..., None]
        out = (out * (1 - soft) + fill * soft).astype(np.uint8)
    if long_gap[i]: return out
    cx, cy, bw, bh = arr[i]
    w = max(40, min(280, 1.15 * max(bw, bh * BA)))
    h = w / BA
    bird = BIRD.resize((int(w), int(h)), Image.LANCZOS)
    x0, y0 = int(cx - w / 2), int(cy - h / 2)
    # mask: everything on the clothes except skin (hands/arms in front stay in front)
    a = f.astype(int); r, g, b = a[..., 0], a[..., 1], a[..., 2]
    skin = (r > 140) & (r - g > 38) & (g - b > 12) & (g > 90)       # real skin is redder than the print white
    skin = ndi.binary_dilation(ndi.binary_opening(skin, iterations=1), iterations=1)
    prt = d['prt'] if d.get('prt') is not None else np.zeros((SH, SW), bool)
    body = ndi.binary_fill_holes(ndi.binary_closing(d['sweater'] | prt, iterations=12))
    allow = ndi.binary_dilation(body, iterations=22) & ~skin          # generous: the print may break the clothes outline
    # sweater-blue patch covering the whole old print (robust to imperfect detection), bird on top
    rbw, rbh = bw, bh
    if d.get('prt') is not None:
        bx = d['box']; rbw, rbh = max(bw, bx[2] - bx[0]), max(bh, bx[3] - bx[1])
    near = d['sweater'] & ~prt
    yy, xx = np.ogrid[:SH, :SW]
    sel = near & (np.abs(xx - cx) < rbw) & (np.abs(yy - cy) < rbh)
    blue = np.median(f[sel], 0) if sel.sum() > 50 else np.array([20, 60, 190])
    ex, ey = 0.68 * rbw + 8, 0.68 * rbh + 8
    ell = ((xx - cx) / ex) ** 2 + ((yy - cy) / ey) ** 2
    patch_a = np.clip((1.0 - ell) / 0.25, 0, 1) * allow
    pa = patch_a[..., None]
    out = (out * (1 - pa) + blue * pa).astype(np.uint8)
    canvas = Image.new('RGBA', (SW, SH)); canvas.alpha_composite(bird, (max(0, x0), max(0, y0)), (max(0, -x0), max(0, -y0)))
    ca = np.array(canvas).astype(float)
    ca[..., 3] *= allow
    # match sweater lighting
    swb = f[d['sweater']].mean(0) if d['sweater'].any() else np.array([30, 70, 200])
    shade = np.clip(swb.sum() / np.array([30, 70, 200]).sum(), 0.6, 1.25)
    ca[..., :3] *= shade
    al = ca[..., 3:4] / 255.0
    return (out * (1 - al) + np.clip(ca[..., :3], 0, 255) * al).astype(np.uint8)


if PREV:
    od = os.environ.get('PREVIEW_DIR', '/tmp')
    for i, f in enumerate(frames()):
        for t in PREV:
            if abs(i / FPS - t) < 0.5 / FPS:
                Image.fromarray(process(f, i)).save(f'{od}/swap_{t}.png'); print('saved', t)
    sys.exit()
ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{SW}x{SH}', '-r', str(FPS), '-i', '-',
                       '-c:v', 'libx264', '-crf', '15', '-preset', 'fast', '-pix_fmt', 'yuv420p', OUT], stdin=subprocess.PIPE)
for i, f in enumerate(frames()):
    ff.stdin.write(process(f, i).tobytes())
ff.stdin.close(); ff.wait(); print('done ->', OUT)
