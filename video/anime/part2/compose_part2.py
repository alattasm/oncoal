"""Assemble 'Baby Yusuf and the Robin', Part 2 (English anime short), from 13 clips.

Inputs:
  clips/shotNN.mp4          28 x 8 s clips
  audio/yNN.wav             Yusuf lines, pitch-tuned to about 340 Hz
  audio/nNN.mp3             narrator
  audio/bN.mp3, audio/mN.mp3  Baba and Mama lines
  ../audio/music.wav        score, looped to length

Output: baby_yusuf_robin_part2.mp4 (1920x1080, 30 fps)

Clip audio is dropped. Rain, thunder, birdsong and cat sounds are synthesized here.
"""
import subprocess, wave, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1920, 1080, 30
CLIP, XF = 8.0, 0.5
STEP = CLIP - XF
N = 13
END_HOLD = 10.0
TOTAL = (N - 1) * STEP + CLIP + END_HOLD
SR = 44100
F = '../../fonts/'
shot = lambda k: (k - 1) * STEP

Y, NA, BA, MA = 'Y', 'N', 'B', 'M'
LINES = [
    ('audio/n00.mp3', 1, 0.3, NA, 'About two weeks later...'),
    ('audio/y00.wav', 1, 2.4, Y, 'Did you hear that? Tap, tap... crack!|Hello, babies!'),
    ('audio/y01.wav', 2, 1.5, Y, 'Welcome to the world, little robins!'),
    ('audio/y02.wav', 3, 1.0, Y, "They're so hungry!|Can you open your mouth that wide?"),
    ('audio/n01.mp3', 4, 0.3, NA, 'Mama and Papa Robin took turns, all day long.'),
    ('audio/y03.wav', 4, 4.5, Y, "Mama's back! Now Papa's going!|Back and forth, back and forth!"),
    ('audio/y04.wav', 5, 2.0, Y, 'Here, Papa Robin! For the hard workers!'),
    ('audio/n02.mp3', 6, 0.3, NA, 'One day, a big shadow passed over the porch...'),
    ('audio/y05.wav', 6, 4.3, Y, 'Oh no! A big bird wants the babies!|Baba! Baba!'),
    ('audio/y06.wav', 8, 0.5, Y, 'Shoo! Shoo! Go away!|These babies are my friends!'),
    ('audio/b0.mp3', 8, 5.0, BA, 'Go on, shoo! Leave them alone!'),
    ('audio/y07.wav', 9, 1.5, Y, "You're safe now, little ones.|I'll always protect you."),
    ('audio/n03.mp3', 10, 0.3, NA, 'Day by day, the babies grew bigger and bigger.'),
    ('audio/y08.wav', 10, 4.6, Y, 'The nest is getting crowded!'),
    ('audio/y09.wav', 11, 1.0, Y, "Flap, flap, flap! You're getting so strong!"),
    ('audio/n04.mp3', 12, 0.2, NA, 'Then one morning, it was time!'),
    ('audio/y10.wav', 12, 3.3, Y, 'Bye-bye, little robins! Have fun!|Come back and visit me!'),
    ('audio/m0.mp3', 12, 7.1, MA, 'Goodbye, little ones! Fly safe!'),
    ('audio/y11.wav', 13, 2.6, Y, 'Hello, robin! I missed you!'),
    ('audio/n05.mp3', 13, 5.6, NA, "This story really happened, right at Yusuf's front door.|Now, every time he hears a robin sing, he smiles and waves hello."),
]
COLORS = {Y: (255, 226, 92), NA: (255, 255, 255), BA: (150, 210, 255), MA: (255, 170, 205)}


def load(path):
    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', path, '-f', 's16le', '-ac', '1', '-ar', str(SR), '-'])
    return np.frombuffer(raw, '<i2').astype(np.float32) / 32768


def font(name, size, var=None):
    f = ImageFont.truetype(F + name + '.ttf', size)
    if var:
        f.set_variation_by_name(var)
    return f


def caption_png(text, spk, path):
    f = font('Montserrat', 46, 'Bold')
    rows = text.split('|')
    lh = 60
    img = Image.new('RGBA', (W, lh * len(rows) + 60))
    d = ImageDraw.Draw(img)
    for i, r in enumerate(rows):
        w = d.textlength(r, font=f)
        d.text(((W - w) / 2, 30 + i * lh), r, font=f, fill=COLORS[spk], stroke_width=5, stroke_fill=(30, 20, 40))
    sh = img.copy().filter(ImageFilter.GaussianBlur(6))
    sh.putalpha(sh.getchannel('A').point(lambda a: int(a * .6)))
    out = Image.new('RGBA', img.size)
    out.alpha_composite(sh, (0, 4))
    out.alpha_composite(img)
    out.save(path)
    return out.height


def title_png(path, big, small):
    img = Image.new('RGBA', (W, 440))
    d = ImageDraw.Draw(img)
    fb, fs = font('Dancing', 140, 'Bold'), font('Montserrat', 46, 'SemiBold')
    w = d.textlength(big, font=fb)
    d.text(((W - w) / 2, 40), big, font=fb, fill=(255, 255, 255), stroke_width=8, stroke_fill=(190, 80, 30))
    w = d.textlength(small, font=fs)
    d.text(((W - w) / 2, 270), small, font=fs, fill=(255, 240, 200), stroke_width=4, stroke_fill=(60, 40, 30))
    glow = img.filter(ImageFilter.GaussianBlur(14))
    out = Image.new('RGBA', img.size)
    out.alpha_composite(glow)
    out.alpha_composite(img)
    out.save(path)


# ---------------- SFX ----------------
rng = np.random.default_rng(7)
L = int(SR * (TOTAL + 1))
amb = np.zeros(L, np.float32)


def put(sig, t, g):
    i = int(t * SR)
    n = min(len(sig), L - i)
    if n > 0:
        amb[i:i + n] += sig[:n] * g


def lowpass(x, a):
    y = np.empty_like(x)
    acc = 0.
    for i in range(len(x)):
        acc += a * (x[i] - acc)
        y[i] = acc
    return y


def chirp(f0, f1, d):
    n = int(SR * d)
    tt = np.arange(n) / SR
    f = f0 + (f1 - f0) * np.sin(np.pi * tt / d)
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * tt / d) ** 2).astype(np.float32)


def song(t, n=4, g=.14, base=2600):
    for k in range(n):
        put(chirp(base + rng.uniform(-200, 500), base + 1500 + rng.uniform(-300, 300), rng.uniform(.07, .14)),
            t + k * rng.uniform(.12, .22), g)


def rain(t0, t1, g):
    n = int(SR * (t1 - t0))
    x = rng.standard_normal(n).astype(np.float32)
    x = x - lowpass(x, .08)                       # hiss
    drops = np.zeros(n, np.float32)
    for _ in range(int((t1 - t0) * 40)):
        i = rng.integers(0, n - 800)
        drops[i:i + 800] += rng.standard_normal(800).astype(np.float32) * np.exp(-np.arange(800) / 120)
    env = np.ones(n, np.float32)
    k = min(n // 4, int(SR * 1.5))
    env[:k] = np.linspace(0, 1, k)
    env[-k:] = np.linspace(1, 0, k)
    put((x * .35 + drops * .25) * env, t0, g)


def thunder(t, g=1.0):
    n = int(SR * 4)
    tt = np.arange(n) / SR
    crack = rng.standard_normal(n).astype(np.float32) * np.exp(-tt / .08)
    rumble = lowpass(rng.standard_normal(n).astype(np.float32), .004) * 30 * np.exp(-tt / 1.4) * (1 + .5 * np.sin(2 * np.pi * 3 * tt))
    put(crack * .5 + rumble, t, g)


def meow(t):
    n = int(SR * .6)
    tt = np.arange(n) / SR
    f = 500 + 350 * np.sin(np.pi * tt / .6)
    s = sum(np.sin(h * 2 * np.pi * np.cumsum(f) / SR) / h for h in range(1, 6))
    put((s * np.sin(np.pi * tt / .6)).astype(np.float32), t, .18)


def whoosh(t):
    n = int(SR * .5)
    x = rng.standard_normal(n).astype(np.float32)
    put(lowpass(x, .15) * np.sin(np.pi * np.arange(n) / n) * 3, t, .5)


def screech(t, g=.3):
    n = int(SR * .9)
    tt = np.arange(n) / SR
    f = 2600 - 1200 * tt / .9
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) + .5 * rng.standard_normal(n)
    put((lowpass(s.astype(np.float32), .35) * np.sin(np.pi * tt / .9) ** .5).astype(np.float32), t, g)


def flutter(t, d=1.2, g=.25):
    n = int(SR * d)
    x = rng.standard_normal(n).astype(np.float32)
    env = (np.sin(2 * np.pi * 14 * np.arange(n) / SR) > .3).astype(np.float32)
    put(lowpass(x, .2) * env * 2, t, g)


for k, t in ((1, 5.5), (2, 4.5), (3, 3.0), (3, 5.5), (4, 1.0), (5, 5.5), (9, 4.0), (10, 2.0), (11, 4.5)):
    song(shot(k) + t, 5, .14, 3400)                  # baby cheeps
song(shot(1) + 0.4, 3, .08, 2600)
screech(shot(6) + 2.0)
screech(shot(7) + 1.0, .35)
song(shot(7) + 3.0, 6, .2, 3200)
whoosh(shot(8) + 0.3)
flutter(shot(8) + 2.5)
screech(shot(8) + 6.2, .25)
flutter(shot(11) + 0.5, 3, .2)
flutter(shot(12) + 0.8, 2, .2)
for t in (0.8, 2.0, 4.8, 6.4):
    song(shot(13) + t, 5, .16, 2800)
for t in (8.5, 10.5, 12.5):
    song(shot(13) + t, 4, .1, 2800)

# ---------------- voice + music mix ----------------
voice = np.zeros(L, np.float32)
for path, k, off, spk, _ in LINES:
    s = load(path)
    s = s / (np.abs(s).max() + 1e-6) * (.95 if spk == Y else .9)
    i = int((shot(k) + off) * SR)
    voice[i:i + len(s)] += s[:L - i]

m = load('../audio/music.wav')
xf = int(SR * 3)
loop = m.copy()
while len(loop) < L:
    fade = np.linspace(0, 1, xf)
    loop[-xf:] = loop[-xf:] * (1 - fade) + m[:xf] * fade
    loop = np.concatenate([loop, m[xf:]])
music = loop[:L]
env = np.convolve((np.abs(voice) > .02).astype(np.float32), np.ones(int(SR * .25)) / (SR * .25), 'same')
duck = 1 - .55 * np.clip(env * 3, 0, 1)
storm = np.ones(L, np.float32)                      # quieter score under the storm
fade = np.ones(L, np.float32)
k0, k1 = int(SR * (TOTAL - 3.5)), int(SR * TOTAL)
fade[k0:k1] = np.linspace(1, 0, k1 - k0)
fade[k1:] = 0
fade[:int(SR * 1.5)] = np.linspace(0, 1, int(SR * 1.5))
music = music / (np.abs(music).max() + 1e-6) * .4 * duck * storm * fade
mix = (voice + music + amb * fade)[:int(SR * TOTAL)]
mix = np.tanh(mix * 1.1) / np.tanh(1.1)
with wave.open('build/mix.wav', 'wb') as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((np.clip(mix, -1, 1) * 32000).astype('<i2').tobytes())

# ---------------- video ----------------
title_png('build/title.png', 'Baby Yusuf and the Robin', 'A True Story  -  Part 2')
title_png('build/end.png', 'The End', 'This story really happened!')


def dur(p):
    return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p]))


caps = []
for i, (p, k, off, spk, text) in enumerate(LINES):
    png = f'build/cap{i:02d}.png'
    h = caption_png(text, spk, png)
    t = shot(k) + off
    caps.append((png, t, t + dur(p) + .3, H - h - 30))

inputs, filt = [], []
for k in range(1, N + 1):
    inputs += ['-i', f'clips/shot{k:02d}.mp4']
    pad = f',tpad=stop_mode=clone:stop_duration={END_HOLD}' if k == N else ''
    filt.append(f'[{k-1}:v]scale=1920:-2:flags=lanczos,crop=1920:1080,fps={FPS},setsar=1,format=yuv420p{pad}[v{k}]')
prev = 'v1'
for k in range(2, N + 1):
    filt.append(f'[{prev}][v{k}]xfade=transition=fade:duration={XF}:offset={shot(k):.3f}[x{k}]')
    prev = f'x{k}'
idx = N
ov = [('build/title.png', .8, 6.6, 300), ('build/end.png', TOTAL - 3.6, TOTAL, 60)] + caps
for p, a, b, y in ov:
    inputs += ['-loop', '1', '-t', f'{TOTAL}', '-i', p]
    filt.append(f'[{idx}:v]format=rgba,fade=t=in:st={a:.2f}:d=0.3:alpha=1,fade=t=out:st={b-0.3:.2f}:d=0.3:alpha=1[o{idx}]')
    filt.append(f"[{prev}][o{idx}]overlay=0:{y}:enable='between(t,{a:.2f},{b:.2f})'[y{idx}]")
    prev = f'y{idx}'
    idx += 1
filt.append(f'[{prev}]fade=t=in:st=0:d=1,fade=t=out:st={TOTAL-1.2:.2f}:d=1.2[vout]')
inputs += ['-i', 'build/mix.wav']
subprocess.run(['ffmpeg', '-y', '-v', 'error', *inputs, '-filter_complex', ';'.join(filt), '-map', '[vout]',
                '-map', f'{idx}:a', '-t', f'{TOTAL}', '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
                '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart',
                'baby_yusuf_robin_part2.mp4'], check=True)
print('done', TOTAL)
