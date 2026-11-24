"""Chicken-only cut of the Kishki promo (1920x1080): farm intro + shop's own black-tray chicken shots.
Usage: python3 kashki_chicken.py [target_seconds] -> kashki_chicken_nomusic.mp4"""
import os, sys, subprocess
os.environ.setdefault('NO_PRICES', '1')
import kashki_promo as K
UP, HERE = K.UP, K.HERE
SEGS = [
 ('title_in', None, 4.0, None, []),
 ('video', (f'{HERE}/broll/white_chickens_feeding.mp4', 0.0), 4.5, ('دجاج من مزارع كندا', 'CANADIAN FARM CHICKEN'), [], False),
 ('trays', None, 11.0, ('دجاج طازج كل يوم', 'FRESH CHICKEN DAILY'), [], False),
 ('photo', (f'{UP}/d0817bd4-image.jpg', (0, 300, 1000, 862)), 3.5, ('دجاج متبّل', 'MARINATED CHICKEN'), []),
 ('video', (f'{UP}/ce006880-IMG_2013.mov', 1.0), 3.5, ('دجاج متبّل', 'MARINATED CHICKEN'), [], False),
 ('video', (f'{UP}/1f983b78-IMG_2014.mov', 0.0), 3.5, ('متبّل بدون عظم', 'BONELESS MARINATED'), [], False),
 ('video', (f'{UP}/0beabd04-IMG_9767.mov', 12.0), 4.0, ('جاهز للشوي', 'READY TO GRILL'), [], False),
 ('title_out', None, 6.0, None, []),
]
K.SEGS = SEGS
K.RIBS.clear(); K.TAGIMG.clear()
for i, s in enumerate(SEGS):
    if s[3] and s[3] not in K.RIBS: K.RIBS[s[3]] = K.ribbon(*s[3])
    K.TAGIMG[i] = []
from PIL import Image, ImageDraw
TRAYS = [((0, 350), 'دجاج كامل', 'WHOLE CHICKEN'), ((280, 640), 'دبابيس', 'DRUMSTICKS'), ((625, 960), 'أجنحة', 'WINGS'),
         ((960, 1315), 'صدور بدون عظم', 'BONELESS BREAST'), ((1275, 1650), 'أفخاذ', 'THIGHS'), ((1575, 1920), 'أرباع دجاج', 'LEG QUARTERS')]
def render_trays(i, dur):
    out = f'{K.TMP}/tr{i:02d}.mp4'
    W, H = K.W, K.H
    src = Image.open(f'{HERE}/ai/chicken_trays_test.jpg').convert('RGB').resize((W, H), Image.LANCZOS).convert('RGBA')
    labels = [(K.text_img(a, K.cairo(76), (255, 255, 255), rtl=True), K.text_img(e, K.mont(34), K.YEL)) for _, a, e in TRAYS]
    ff = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(K.FPS), '-i', '-',
                           '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    N = int(round(dur * K.FPS)); intro = 1.2; step = (dur - intro) / len(TRAYS)
    for n in range(N):
        t = n / K.FPS
        z = 1 + 0.04 * t / dur
        fr = src.resize((int(W * z), int(H * z)), Image.BILINEAR).crop((int((W * z - W) / 2), int((H * z - H) / 2), int((W * z - W) / 2) + W, int((H * z - H) / 2) + H))
        if t >= intro:
            k = min(int((t - intro) / step), len(TRAYS) - 1); tt = t - intro - k * step
            (x0, x1), _, _ = TRAYS[k]
            a = int(150 * K.ease(min(t - intro, 0.4) / 0.4))
            m = Image.new('RGBA', (W, H), (0, 0, 0, a)); d = ImageDraw.Draw(m)
            d.rectangle((x0, 0, x1, H), fill=(0, 0, 0, 0))
            fr.alpha_composite(m)
            ImageDraw.Draw(fr).rectangle((x0 + 3, 60, x1 - 3, H - 60), outline=K.GOLD + (255,), width=6)
            la, le = labels[k]; kk = K.back(tt / 0.45); cx = min(max((x0 + x1) / 2, 360), W - 360)
            pill = Image.new('RGBA', (la.width - 20, 150)); ImageDraw.Draw(pill).rounded_rectangle((0, 0, pill.width - 1, 149), 30, fill=K.RED + (235,))
            K.put(fr, pill, cx, H - 200, K.ease(tt / 0.2), kk)
            K.put(fr, la, cx, H - 225, K.ease(tt / 0.2), kk); K.put(fr, le, cx, H - 160, K.ease(tt / 0.2), kk)
        K.put(fr, K.LOGO_SM, 160, 110, 0.95); K.put(fr, K.HALAL, W - 150, 130, 0.95, 0.8)
        ff.stdin.write(fr.convert('RGB').tobytes())
    ff.stdin.close(); ff.wait(); return out

if __name__ == '__main__':
    os.chdir(HERE)
    target = float(sys.argv[1]) if len(sys.argv) > 1 else None
    base = sum(s[2] for s in SEGS) - K.XF * (len(SEGS) - 1)
    k = (target / base) if target else 1.0
    durs = [s[2] * k for s in SEGS]
    files = [render_trays(100 + i, durs[i]) if s[0] == 'trays' else K.render_seg(100 + i, s, durs[i]) for i, s in enumerate(SEGS)]
    inputs = sum([['-i', f] for f in files], [])
    chain, off, prev = [], 0, '0:v'
    for i in range(1, len(files)):
        off += durs[i - 1] - K.XF; lab = f'v{i}'
        chain.append(f'[{prev}][{i}:v]xfade=transition=fade:duration={K.XF}:offset={off:.3f}[{lab}]'); prev = lab
    subprocess.run(['ffmpeg', '-y', '-v', 'error', *inputs, '-filter_complex', ';'.join(chain), '-map', f'[{prev}]',
                    '-c:v', 'libx264', '-preset', 'slow', '-crf', '19', '-pix_fmt', 'yuv420p', '-r', str(K.FPS), '-movflags', '+faststart',
                    'kashki_chicken_nomusic.mp4'], check=True)
    print('done', sum(durs) - K.XF * (len(durs) - 1))
