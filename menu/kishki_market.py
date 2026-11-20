"""Kishki Halal Supermarket promo (1920x1080, 30 fps): store walk-through clips with Arabic/English section
captions, logo intro/outro. Song is muxed on afterwards.

Usage: python3 kishki_market.py [target_seconds]  -> kishki_market_nomusic.mp4
"""
import os, sys, subprocess, math
import kashki_promo as K          # shared helpers (fonts, text, ribbon, logo, frame reader)
from PIL import Image, ImageFilter

W, H, FPS, XF = K.W, K.H, K.FPS, K.XF
UP = K.UP
V = {k: next(f'{UP}/{f}' for f in os.listdir(UP) if f.startswith(k)) for k in ('68d5c961', '0302bc19', '1649684e', '0dfcfd4c')}

SUBT = K.text_img('سوبرماركت حلال', K.cairo(80), K.CREAM, rtl=True)
NAME_EN = K.text_img('KISHKI HALAL SUPERMARKET', K.bebas(64), K.GOLD)
FAMILY = K.text_img('كل اللي يحتاجه بيتك في مكان واحد', K.cairo(56, 'Bold'), K.CREAM, rtl=True)
CTA = K.pill('يلا على كشكي!')

def caption_card(ar, en):
    a = K.text_img(ar, K.cairo(72), (255, 255, 255), rtl=True)
    e = K.text_img(en, K.mont(32), K.YEL)
    return a, e

# (start, duration, arabic caption, english caption)
SEGS = [
    ('title_in', None, 4.0, None),
    ('0302bc19', 0.0, 5.0, ('كشكي سوبرماركت حلال', 'KISHKI HALAL SUPERMARKET')),
    ('0302bc19', 20.0, 4.5, ('خضار وفواكه طازجة', 'FRESH FRUIT & VEGETABLES')),
    ('1649684e', 8.0, 4.5, ('مواد غذائية ومعلبات', 'GROCERIES & PANTRY')),
    ('1649684e', 14.0, 4.5, ('آيس كريم ومثلجات', 'ICE CREAM & TREATS')),
    ('1649684e', 26.5, 4.5, ('مخبوزات ومنتجات يومية', 'BAKERY & DAILY ESSENTIALS')),
    ('68d5c961', 0.0, 4.5, ('مجمدات', 'FROZEN FOODS')),
    ('68d5c961', 19.0, 4.5, ('سناكات وحلويات', 'SNACKS & SWEETS')),
    ('68d5c961', 13.0, 4.5, ('أدوات منزلية', 'HOUSEWARES')),
    ('0dfcfd4c', 0.0, 4.5, ('قسم اللحوم الطازجة', 'FRESH HALAL MEAT')),
    ('0dfcfd4c', 7.5, 4.5, ('كل احتياجات البيت', 'EVERYTHING FOR YOUR HOME')),
    ('title_out', None, 7.0, None),
]
CAPS = {i: caption_card(*s[3]) for i, s in enumerate(SEGS) if s[3]}

def title_in(t):
    f = K.BG.copy()
    k = K.back((t - .2) / .8); K.put(f, K.LOGO, W / 2, 380, K.ease((t - .2) / .3), 0.6 + 0.4 * k)
    k = K.ease((t - 1.0) / .6); K.put(f, SUBT, W / 2, 600 + 30 * (1 - k), k)
    k = K.ease((t - 1.4) / .6); K.put(f, NAME_EN, W / 2, 700 + 30 * (1 - k), k)
    k = K.back((t - 1.8) / .5); K.put(f, K.HALAL, W / 2, 880, K.ease((t - 1.8) / .2), k)
    return f

def title_out(t):
    f = K.BG.copy(); pulse = 1 + 0.02 * math.sin(t * math.pi * 2)
    k = K.back(t / .7); K.put(f, K.LOGO, W / 2, 320, K.ease(t / .3), k * pulse)
    k = K.ease((t - .6) / .6); K.put(f, SUBT, W / 2, 540 + 30 * (1 - k), k)
    k = K.ease((t - 1.0) / .6); K.put(f, FAMILY, W / 2, 650 + 30 * (1 - k), k)
    k = K.ease((t - 1.3) / .6); K.put(f, NAME_EN, W / 2, 740 + 30 * (1 - k), k)
    k = K.back((t - 1.8) / .5); K.put(f, CTA, W / 2, 890, K.ease((t - 1.8) / .2), k)
    return f

def render_seg(i, seg, dur):
    out = f'{K.TMP}/mk{i:02d}.mp4'
    ff = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    N = int(round(dur * FPS)); src = seg[0]
    frames = K.video_frames(V[src], seg[1], dur + 0.2, pink=False) if src in V else None
    last = None
    for n in range(N):
        t = n / FPS
        if src == 'title_in': f = title_in(t)
        elif src == 'title_out': f = title_out(t)
        else:
            fr = next(frames, None) or last; last = fr
            fr = fr.filter(ImageFilter.UnsharpMask(2, 60, 2))
            f = fr.convert('RGBA'); f.alpha_composite(K.SHADE)
            a, e = CAPS[i]; k = K.ease((t - 0.3) / 0.5); out_k = 1 - K.ease((t - (dur - 0.5)) / 0.4)
            K.put(f, a, W / 2, H - 175 + 30 * (1 - k), k * out_k); K.put(f, e, W / 2, H - 100 + 30 * (1 - k), k * out_k)
            K.put(f, K.LOGO_SM, 160, 110, 0.95); K.put(f, K.HALAL, W - 150, 130, 0.95, 0.8)
        ff.stdin.write(f.convert('RGB').tobytes())
    ff.stdin.close(); ff.wait(); return out

if __name__ == '__main__':
    os.chdir(K.HERE)
    target = float(sys.argv[1]) if len(sys.argv) > 1 else None
    base = sum(s[2] for s in SEGS) - XF * (len(SEGS) - 1)
    k = (target / base) if target else 1.0
    durs = [s[2] * k for s in SEGS]
    files = [render_seg(i, s, durs[i]) for i, s in enumerate(SEGS)]
    inputs = sum([['-i', f] for f in files], [])
    chain, off, prev = [], 0, '0:v'
    for i in range(1, len(files)):
        off += durs[i - 1] - XF; lab = f'v{i}'
        chain.append(f'[{prev}][{i}:v]xfade=transition={"slideleft" if i % 3 == 0 else "fade"}:duration={XF}:offset={off:.3f}[{lab}]'); prev = lab
    subprocess.run(['ffmpeg', '-y', '-v', 'error', *inputs, '-filter_complex', ';'.join(chain), '-map', f'[{prev}]',
                    '-c:v', 'libx264', '-preset', 'slow', '-crf', '19', '-pix_fmt', 'yuv420p', '-r', str(FPS), '-movflags', '+faststart',
                    'kishki_market_nomusic.mp4'], check=True)
    print('done', sum(durs) - XF * (len(durs) - 1))
