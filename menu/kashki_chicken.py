"""Chicken-only cut of the Kishki promo (1920x1080): farm intro + shop's own black-tray chicken shots.
Usage: python3 kashki_chicken.py [target_seconds] -> kashki_chicken_nomusic.mp4"""
import os, sys, subprocess
os.environ.setdefault('NO_PRICES', '1')
import kashki_promo as K
UP, HERE = K.UP, K.HERE
SEGS = [
 ('title_in', None, 4.0, None, []),
 ('video', (f'{HERE}/broll/white_chickens_feeding.mp4', 0.0), 4.5, ('دجاج من مزارع كندا', 'CANADIAN FARM CHICKEN'), [], False),
 ('photo', (f'{UP}/2d9eeb7d-image.jpg', (0, 480, 2000, 1250)), 4.5, ('دجاج طازج كل يوم', 'FRESH CHICKEN DAILY'), []),
 ('photo', (f'{UP}/d0817bd4-image.jpg', (0, 300, 1000, 862)), 4.0, ('دبابيس وأرباع', 'DRUMSTICKS & QUARTERS'), []),
 ('photo', (f'{UP}/6f0b5640-image.jpg', (0, 250, 1000, 812)), 4.0, ('أرباع دجاج', 'LEG QUARTERS'), []),
 ('photo', (f'{UP}/d0817bd4-image.jpg', (1250, 250, 2000, 672)), 4.0, ('أجنحة دجاج', 'CHICKEN WINGS'), []),
 ('photo', (f'{UP}/33cfe328-image.jpg', (1150, 220, 2000, 698)), 4.0, ('أجنحة متبّلة', 'MARINATED WINGS'), []),
 ('photo', (f'{UP}/33cfe328-image.jpg', (120, 250, 1050, 773)), 4.0, ('صدور بدون عظم', 'BONELESS BREAST'), []),
 ('video', (f'{UP}/ce006880-IMG_2013.mov', 1.0), 4.0, ('دجاج متبّل', 'MARINATED CHICKEN'), [], False),
 ('video', (f'{UP}/1f983b78-IMG_2014.mov', 0.0), 4.0, ('متبّل بدون عظم', 'BONELESS MARINATED'), [], False),
 ('video', (f'{UP}/0beabd04-IMG_9767.mov', 12.0), 4.0, ('جاهز للشوي', 'READY TO GRILL'), [], False),
 ('title_out', None, 6.0, None, []),
]
K.SEGS = SEGS
K.RIBS.clear(); K.TAGIMG.clear()
for i, s in enumerate(SEGS):
    if s[3] and s[3] not in K.RIBS: K.RIBS[s[3]] = K.ribbon(*s[3])
    K.TAGIMG[i] = []
if __name__ == '__main__':
    os.chdir(HERE)
    target = float(sys.argv[1]) if len(sys.argv) > 1 else None
    base = sum(s[2] for s in SEGS) - K.XF * (len(SEGS) - 1)
    k = (target / base) if target else 1.0
    durs = [s[2] * k for s in SEGS]
    files = [K.render_seg(100 + i, s, durs[i]) for i, s in enumerate(SEGS)]
    inputs = sum([['-i', f] for f in files], [])
    chain, off, prev = [], 0, '0:v'
    for i in range(1, len(files)):
        off += durs[i - 1] - K.XF; lab = f'v{i}'
        chain.append(f'[{prev}][{i}:v]xfade=transition=fade:duration={K.XF}:offset={off:.3f}[{lab}]'); prev = lab
    subprocess.run(['ffmpeg', '-y', '-v', 'error', *inputs, '-filter_complex', ';'.join(chain), '-map', f'[{prev}]',
                    '-c:v', 'libx264', '-preset', 'slow', '-crf', '19', '-pix_fmt', 'yuv420p', '-r', str(K.FPS), '-movflags', '+faststart',
                    'kashki_chicken_nomusic.mp4'], check=True)
    print('done', sum(durs) - K.XF * (len(durs) - 1))
