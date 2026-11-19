"""Assemble 'Baby Yusuf and the Robin', Part 1 (English anime short), from 28 clips.

Inputs:
  clips/shotNN.mp4          28 x 8 s clips
  audio/yNN.wav             Yusuf lines, pitch-tuned to about 340 Hz
  audio/nNN.mp3             narrator
  audio/bN.mp3, audio/mN.mp3  Baba and Mama lines
  ../audio/music.wav        score, looped to length

Output: baby_yusuf_robin_part1.mp4 (1920x1080, 30 fps)

Clip audio is dropped. Rain, thunder, birdsong and cat sounds are synthesized here.
"""
import subprocess, wave, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1920, 1080, 30
CLIP, XF = 8.0, 0.5
STEP = CLIP - XF
N = 28
END_HOLD = 5.0
TOTAL = (N - 1) * STEP + CLIP + END_HOLD
SR = 44100
F = '../../fonts/'
shot = lambda k: (k - 1) * STEP

Y, NA, BA, MA = 'Y', 'N', 'B', 'M'
# (file, shot, offset, speaker, caption)
LINES = [
    ('audio/n00.mp3', 1, 0.6, NA, 'The long, snowy winter was finally over...|and spring was here!'),
    ('audio/y00.wav', 2, 0.4, Y, 'Mama! Baba! This one!|The purple and yellow flowers!'),
    ('audio/m0.mp3', 2, 4.9, MA, "Great choice, Yusuf! They're beautiful."),
    ('audio/y01.wav', 3, 1.2, Y, 'Now our door is so pretty!'),
    ('audio/n01.mp3', 4, 0.2, NA, 'Two hours later...'),
    ('audio/y02.wav', 4, 2.2, Y, 'Whoa! Someone built a nest in our flowers!'),
    ('audio/b0.mp3', 5, 0.4, BA, 'Hmm... was that nest there when we bought it?'),
    ('audio/y03.wav', 5, 4.2, Y, "I don't know!"),
    ('audio/n02.mp3', 6, 0.2, NA, 'That evening, there was a surprise inside the nest.'),
    ('audio/y04.wav', 6, 3.9, Y, 'An egg... a blue egg!|Is it plastic? Is it a trick?'),
    ('audio/y05.wav', 7, 2.6, Y, 'One... two eggs!'),
    ('audio/y06.wav', 8, 1.6, Y, 'One... two... three eggs!'),
    ('audio/y07.wav', 9, 0.4, Y, 'Four! Count with me!|One, two, three, four!'),
    ('audio/n03.mp3', 9, 5.4, NA, 'A real Mama Robin had chosen|their flower pot to be her home.'),
    ('audio/y08.wav', 10, 2.4, Y, "Good morning, Mama Robin!|Shhh... she's keeping her eggs warm."),
    ('audio/y09.wav', 11, 0.6, Y, "Look! Another robin! That's Papa Robin!|He brought her lunch!"),
    ('audio/y10.wav', 12, 1.0, Y, "Good job, Papa Robin! You're the guard!"),
    ('audio/y11.wav', 13, 0.5, Y, 'Mama Robin must be hungry and thirsty!|Here you go!'),
    ('audio/n04.mp3', 13, 4.6, NA, 'Every day, Yusuf visited his new friend.|They were becoming best friends.'),
    ('audio/y12.wav', 14, 3.2, Y, 'Today I ate pancakes! Do you like pancakes?'),
    ('audio/n05.mp3', 15, 1.0, NA, 'But someone else had spotted the nest...'),
    ('audio/y13.wav', 17, 0.8, Y, "Hey, kitty! No, no, no!|That's Mama Robin's home!"),
    ('audio/y14.wav', 18, 0.8, Y, 'Go find your own breakfast, kitty!'),
    ('audio/m1.mp3', 18, 4.4, MA, "Yusuf, you're so brave!"),
    ('audio/y15.wav', 19, 0.5, Y, "Now everybody knows.|This is Mama Robin's house!"),
    ('audio/n06.mp3', 19, 4.6, NA, 'Then one day, dark clouds rolled in.|Drip... drop... splash!'),
    ('audio/y16.wav', 20, 3.9, Y, "Oh no! It's raining! The eggs will get wet!"),
    ('audio/y17.wav', 21, 0.6, Y, 'Baba, quick! The cardboard! Make a roof!'),
    ('audio/b1.mp3', 21, 4.4, BA, 'Good thinking, Yusuf!'),
    ('audio/y18.wav', 22, 1.5, Y, 'Yay! The roof works!'),
    ('audio/n07.mp3', 23, 2.4, NA, 'That night, a big storm came...'),
    ('audio/y19.wav', 24, 1.8, Y, 'Mama Robin is all alone in the storm!|Baba, we have to help her!'),
    ('audio/b2.mp3', 25, 0.8, BA, 'Stay close to me, Yusuf.'),
    ('audio/y20.wav', 25, 3.4, Y, 'Okay, Baba!'),
    ('audio/y21.wav', 26, 1.6, Y, "Don't worry, Mama Robin. I'll keep you dry!"),
    ('audio/y22.wav', 27, 1.4, Y, 'We did it! Everybody is safe!'),
    ('audio/y23.wav', 28, 0.8, Y, "Rain again? No problem!|I'm here, Mama Robin!"),
    ('audio/n08.mp3', 28, 7.6, NA, 'And Yusuf kept his robin friends safe...|Part two, coming soon!'),
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


for t in (1.0, 3.0, 5.2):
    song(shot(1) + t)
song(shot(10) + 5.0, 3, .1)
song(shot(11) + 4.8, 4, .12)
song(shot(12) + 5.5, 3, .12)
song(shot(14) + 1.5, 3, .1)
song(shot(16) + 1.0, 6, .22, 3200)                 # alarm chirps
song(shot(16) + 3.5, 6, .22, 3200)
meow(shot(15) + 5.5)
whoosh(shot(17) + 0.4)
meow(shot(18) + 0.3)
rain(shot(19) + 6.5, shot(23), .35)                 # day rain
rain(shot(23), shot(27) + 0.5, .8)                  # night storm
thunder(shot(23) + 0.8, 1.0)
thunder(shot(24) + 0.6, .7)
thunder(shot(25) + 5.5, .8)
thunder(shot(26) + 4.5, .6)
song(shot(27) + 2.5, 4, .14)
rain(shot(28), shot(28) + CLIP, .2)                 # sunny drizzle
song(shot(28) + 5.0, 3, .1)

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
a, b = int(shot(23) * SR), int((shot(27) + 1) * SR)
storm[a:b] = .45
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
title_png('build/title.png', 'Baby Yusuf and the Robin', 'A True Story  -  Part 1')
title_png('build/end.png', 'To Be Continued...', 'Baby Yusuf and the Robin  -  Part 2 coming soon')


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
ov = [('build/title.png', .8, 6.6, 300), ('build/end.png', TOTAL - END_HOLD + .3, TOTAL, 60)] + caps
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
                'baby_yusuf_robin_part1.mp4'], check=True)
print('done', TOTAL)
