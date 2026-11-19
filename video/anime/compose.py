"""Assemble 'Baby Youssef and Robin' (English anime short) from the generated clips.

Inputs:  clips/shotNN.mp4 (16 x 8 s, 1344x768), audio/nNN.mp3 (narrator), audio/kid_yNN.wav
         (Youssef, pitch-raised), audio/music.wav.
Output:  baby_youssef_and_robin.mp4 (1920x1080, 30 fps).
Clip audio is dropped; ambience (birdsong, wind, petal poof) is synthesised here.
"""
import subprocess, wave, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1920, 1080, 30
CLIP, XF = 8.0, 0.5
STEP = CLIP - XF
END_HOLD = 4.0
TOTAL = 15 * STEP + CLIP + END_HOLD           # 124.5 s
SR = 44100
F = '../fonts/'
shot = lambda k: (k - 1) * STEP               # start time of shot k (1-based)

# ---------------- dialogue timeline: (file, start, speaker, caption) ----------------
LINES = [
    ('audio/n00.mp3',     shot(1) + 0.3, 'N', 'One sunny morning, in a garden full of flowers,|a little bird family woke up, high in the old tree.'),
    ('audio/kid_y00.wav', shot(2) + 0.6, 'Y', 'Good morning, sunshine!'),
    ('audio/n01.mp3',     shot(2) + 2.6, 'N', 'Baby Youssef ran outside to play.'),
    ('audio/n02.mp3',     shot(3) + 0.3, 'N', 'Suddenly... whoosh! A strong wind shook the tree,|and the baby bird tumbled down!'),
    ('audio/kid_y01.wav', shot(4) + 0.6, 'Y', 'Oh no! A little bird!'),
    ('audio/n03.mp3',     shot(5) + 0.8, 'N', 'The little bird was scared, and all alone.'),
    ('audio/kid_y02.wav', shot(6) + 0.8, 'Y', "Don't be scared. I'm your friend.|I'll call you... Robin!"),
    ('audio/kid_y03.wav', shot(7) + 0.8, 'Y', 'Your nest is way up there...|but your wings are still too small.'),
    ('audio/n04.mp3',     shot(8) + 0.7, 'N', 'So Youssef made him a cozy little home.'),
    ('audio/n05.mp3',     shot(9) + 0.6, 'N', 'He gave him water, tiny seeds,|and lots and lots of love.'),
    ('audio/kid_y04.wav', shot(10) + 0.8, 'Y', 'Look, Robin! Flap, flap, flap!'),
    ('audio/n06.mp3',     shot(11) + 0.5, 'N', 'Robin tried... and tumbled!|But Youssef cheered him on.'),
    ('audio/kid_y05.wav', shot(12) + 0.5, 'Y', 'You can do it, Robin!'),
    ('audio/n07.mp3',     shot(12) + 3.1, 'N', 'And then... Robin flew!'),
    ('audio/n08.mp3',     shot(13) + 0.8, 'N', 'Robin flew all the way home, back to his mommy.'),
    ('audio/kid_y06.wav', shot(14) + 1.5, 'Y', 'Bye-bye, Robin...'),
    ('audio/n09.mp3',     shot(15) + 0.4, 'N', 'The next morning, Youssef heard|a happy little song at his window.'),
    ('audio/kid_y07.wav', shot(15) + 5.2, 'Y', 'Robin! You came back!'),
    ('audio/n10.mp3',     shot(16) + 0.3, 'N', 'From that day on, Robin visited Youssef every single morning.|Because kindness... makes the best friends.'),
    ('audio/kid_y08.wav', shot(16) + 8.8, 'Y', 'Best friends forever!'),
]

def dur(path):
    return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                                          '-of', 'csv=p=0', path]).decode())

def load(path):
    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', path, '-f', 's16le', '-ac', '1', '-ar', str(SR), '-'])
    return np.frombuffer(raw, '<i2').astype(np.float32) / 32768

# ---------------- text overlays rendered with PIL ----------------
def font(name, size, var=None):
    f = ImageFont.truetype(F + name + '.ttf', size)
    if var: f.set_variation_by_name(var)
    return f

def caption_png(text, speaker, path):
    f = font('Montserrat', 46, 'Bold')
    rows = text.split('|')
    fill = (255, 255, 255) if speaker == 'N' else (255, 226, 92)
    lh = 60
    img = Image.new('RGBA', (W, lh * len(rows) + 60))
    d = ImageDraw.Draw(img)
    for i, r in enumerate(rows):
        w = d.textlength(r, font=f)
        d.text(((W - w) / 2, 30 + i * lh), r, font=f, fill=fill, stroke_width=5, stroke_fill=(30, 20, 40))
    sh = img.copy().filter(ImageFilter.GaussianBlur(6))
    sh.putalpha(sh.getchannel('A').point(lambda a: int(a * .6)))
    out = Image.new('RGBA', img.size); out.alpha_composite(sh, (0, 4)); out.alpha_composite(img)
    out.save(path)
    return out.height

def title_png(path, big, small):
    img = Image.new('RGBA', (W, 420))
    d = ImageDraw.Draw(img)
    fb, fs = font('Dancing', 150, 'Bold'), font('Montserrat', 44, 'SemiBold')
    w = d.textlength(big, font=fb)
    d.text(((W - w) / 2, 40), big, font=fb, fill=(255, 255, 255), stroke_width=8, stroke_fill=(40, 90, 170))
    if small:
        w = d.textlength(small, font=fs)
        d.text(((W - w) / 2, 270), small, font=fs, fill=(255, 240, 200), stroke_width=4, stroke_fill=(60, 40, 30))
    glow = img.filter(ImageFilter.GaussianBlur(14))
    out = Image.new('RGBA', img.size); out.alpha_composite(glow); out.alpha_composite(img)
    out.save(path)

# ---------------- ambience / SFX ----------------
rng = np.random.default_rng(5)
amb = np.zeros(int(SR * (TOTAL + 1)), np.float32)

def put(sig, t, g):
    i = int(t * SR); n = min(len(sig), len(amb) - i)
    if n > 0: amb[i:i + n] += sig[:n] * g

def chirp(f0=3200, f1=4800, d=.09):
    n = int(SR * d); tt = np.arange(n) / SR
    f = f0 + (f1 - f0) * np.sin(np.pi * tt / d)
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * tt / d) ** 2).astype(np.float32)

def song(t, n=4, g=.18, base=3000):
    for k in range(n):
        put(chirp(base + rng.uniform(-300, 600), base + 1800 + rng.uniform(-400, 400), rng.uniform(.06, .12)),
            t + k * rng.uniform(.11, .2), g)

def wind(t, d, g=.5):
    n = int(SR * d); x = rng.standard_normal(n).astype(np.float32)
    y = np.empty(n, np.float32); a = 0.
    tt = np.arange(n) / SR
    c = .01 + .05 * np.sin(np.pi * tt / d) ** 2
    for i in range(n): a += c[i] * (x[i] - a); y[i] = a
    put(y * np.sin(np.pi * tt / d) * 6, t, g)

def poof(t):
    n = int(SR * .35); tt = np.arange(n) / SR
    put((rng.standard_normal(n) * np.exp(-tt / .06)).astype(np.float32) * .5, t, .35)

for t in np.arange(0.8, 7.5, 1.4): song(shot(1) + t, 3, .14)          # dawn birdsong
wind(shot(3) - .3, 6.5, .9); song(shot(3) + 1, 3, .2, 3600)            # gust + alarmed chirps
song(shot(5) + 3.5, 2, .12, 3400); song(shot(5) + 6.5, 2, .12)          # timid chirps
song(shot(6) + 3.2, 3, .16); song(shot(7) + 3.8, 4, .16)
song(shot(8) + 4.2, 3, .14); song(shot(9) + 4.2, 3, .14)
song(shot(10) + 3.6, 4, .16); poof(shot(11) + 3.6)
song(shot(12) + 1.6, 5, .18); song(shot(12) + 5.2, 5, .16)
song(shot(13) + 4.6, 3, .12)
for t in (1.2, 2.2, 3.4): song(shot(15) + t, 5, .2, 3300)                 # window song
song(shot(16) + 6.0, 4, .16)

# ---------------- voices + music mix (with ducking) ----------------
voice = np.zeros_like(amb)
for path, t, spk, _ in LINES:
    s = load(path)
    s = s / (np.abs(s).max() + 1e-6) * (.92 if spk == 'N' else .95)
    i = int(t * SR); voice[i:i + len(s)] += s[:len(voice) - i]

music = load('audio/music.wav')[:len(amb)]
music = np.pad(music, (0, len(amb) - len(music)))
env = np.convolve((np.abs(voice) > .02).astype(np.float32), np.ones(int(SR * .25)) / (SR * .25), 'same')
env = np.clip(env * 3, 0, 1)
duck = 1 - .55 * np.convolve(env, np.ones(int(SR * .3)) / (SR * .3), 'same')
fade = np.ones_like(amb); k0, k1 = int(SR * (TOTAL - 3.5)), int(SR * TOTAL)
fade[k0:k1] = np.linspace(1, 0, k1 - k0); fade[k1:] = 0
fade[:int(SR * 1.5)] = np.linspace(0, 1, int(SR * 1.5))
music = music / (np.abs(music).max() + 1e-6) * .42 * duck * fade
mix = voice + music + amb * fade
mix = mix[:int(SR * TOTAL)]
mix = np.tanh(mix * 1.1) / np.tanh(1.1)
with wave.open('build/mix.wav', 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(mix, -1, 1) * 32000).astype('<i2').tobytes())

# ---------------- video graph ----------------
title_png('build/title.png', 'Baby Youssef & Robin', 'A little story about kindness')
title_png('build/end.png', 'The End', 'Kindness makes the best friends')
caps = []
for i, (path, t, spk, text) in enumerate(LINES):
    p = f'build/cap{i:02d}.png'; h = caption_png(text, spk, p)
    caps.append((p, t, t + dur(path) + .35, h))

inputs, filt = [], []
for k in range(1, 17):
    inputs += ['-i', f'clips/shot{k:02d}.mp4']
    pad = f',tpad=stop_mode=clone:stop_duration={END_HOLD}' if k == 16 else ''
    filt.append(f'[{k-1}:v]scale=1920:-2:flags=lanczos,crop=1920:1080,fps={FPS},setsar=1,format=yuv420p{pad}[v{k}]')
prev = 'v1'
for k in range(2, 17):
    filt.append(f'[{prev}][v{k}]xfade=transition=fade:duration={XF}:offset={shot(k):.3f}[x{k}]')
    prev = f'x{k}'
idx = 16
overlays = [('build/title.png', .8, 6.2, (H - 420) // 2 - 120), ('build/end.png', TOTAL - END_HOLD + .2, TOTAL, -30)]
overlays += [(p, a, b, H - h - 30) for p, a, b, h in caps]
for p, a, b, y in overlays:
    inputs += ['-loop', '1', '-t', f'{TOTAL}', '-i', p]
    fi = f'[{idx}:v]format=rgba,fade=t=in:st={a:.2f}:d=0.3:alpha=1,fade=t=out:st={b-0.3:.2f}:d=0.3:alpha=1[o{idx}]'
    filt.append(fi)
    filt.append(f'[{prev}][o{idx}]overlay=0:{y}:enable=\'between(t,{a:.2f},{b:.2f})\'[y{idx}]')
    prev = f'y{idx}'; idx += 1
filt.append(f'[{prev}]fade=t=in:st=0:d=1,fade=t=out:st={TOTAL-1.2:.2f}:d=1.2[vout]')
inputs += ['-i', 'build/mix.wav']
cmd = ['ffmpeg', '-y', '-v', 'error', *inputs, '-filter_complex', ';'.join(filt), '-map', '[vout]', '-map', f'{idx}:a',
       '-t', f'{TOTAL}', '-c:v', 'libx264', '-preset', 'medium', '-crf', '23', '-pix_fmt', 'yuv420p',
       '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', 'baby_youssef_and_robin.mp4']
subprocess.run(cmd, check=True)
print('done', TOTAL)
