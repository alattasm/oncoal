"""Lollipop colour video: retimed Kling clip + kid voice calling each colour at its change + instrumental
music + action SFX + big pop-in colour words. 1920x1080.

Usage: python3 lollipop.py WORKDIR [preview_t ...]
WORKDIR holds retimed.mp4, music.mp3, vo/all.mp3 + vo/all_words.json, sfx/{slurp,sparkle,burst,cheer}.mp3
"""
import json, math, os, subprocess, sys
import numpy as np, librosa, soundfile as sf
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
import render as R

WD = sys.argv[1]; PREV = [float(a) for a in sys.argv[2:]]
W, H, FPS = 1920, 1080, 24
SR = 44100
DUR = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0',
                            os.path.join(WD, 'retimed.mp4')], capture_output=True, text=True).stdout)
# colour change moments in the retimed video (seconds) and colours
EVENTS = [('RED', 2.6, (238, 48, 62)), ('ORANGE', 4.35, (255, 140, 30)), ('YELLOW', 4.9, (255, 205, 30)),
          ('GREEN', 6.4, (58, 196, 78)), ('BLUE', 7.9, (38, 120, 245)), ('PURPLE', 10.4, (160, 72, 222)),
          ('BROWN', 11.9, (150, 95, 55)), ('RAINBOW', 13.95, None)]
RAINBOW = [(238, 48, 62), (255, 140, 30), (255, 205, 30), (58, 196, 78), (38, 120, 245), (160, 72, 222), (255, 110, 190)]


def build_audio():
    n = int(DUR * SR); mix = np.zeros((2, n))
    # music bed
    mus, _ = librosa.load(os.path.join(WD, 'music.mp3'), sr=SR, mono=False)
    m = np.zeros((2, n)); m[:, :min(n, mus.shape[1])] = mus[:, :n]
    m /= np.abs(m).max() + 1e-9
    # voice: cut words from the single take
    y, _ = librosa.load(os.path.join(WD, 'vo', 'all.mp3'), sr=SR, mono=True)
    words = json.load(open(os.path.join(WD, 'vo', 'all_words.json')))
    starts = {w[2]: w[0] for w in words}; ends = {w[2]: w[1] for w in words}
    order = [w[2] for w in words]

    def cut(a, b):
        seg = y[int(max(0, a - 0.04) * SR):int((b + 0.12) * SR)]
        seg, _ = librosa.effects.trim(seg, top_db=38)
        f = min(int(0.015 * SR), len(seg) // 4)
        seg = seg.copy(); seg[:f] *= np.linspace(0, 1, f); seg[-f:] *= np.linspace(1, 0, f)
        return seg / (np.abs(seg).max() + 1e-9)
    voice = np.zeros(n)

    def put(seg, t, g=1.0):
        a = int(t * SR); b = min(n, a + len(seg)); voice[a:b] += g * seg[:b - a]
    put(cut(starts['hi'], ends['yuyu']), 0.15)
    for name, t, _ in EVENTS[:-1]:
        k = name.lower(); put(cut(starts[k], ends[k]), t + 0.05)
    put(cut(starts['rainbow'], ends.get('yay', ends['rainbow'] + 1.0)), EVENTS[-1][1] + 0.05)
    # sfx
    sfx = np.zeros((2, n))

    def put_sfx(name, t, g):
        s, _ = librosa.load(os.path.join(WD, 'sfx', name + '.mp3'), sr=SR, mono=True)
        s /= np.abs(s).max() + 1e-9
        a = int(t * SR); b = min(n, a + len(s))
        k = min((b - a) // 4, int(0.12 * SR)); s = s.copy(); s[b - a - k:b - a] *= np.linspace(1, 0, k)
        sfx[:, a:b] += g * s[:b - a]
    for t in (2.25, 4.15, 11.95 + 0.5):                     # licks
        put_sfx('slurp', t, 0.35)
    for _, t, _ in EVENTS[:-1]:                             # transformations
        put_sfx('sparkle', t - 0.1, 0.45)
    put_sfx('burst', EVENTS[-1][1] - 0.05, 0.6)
    put_sfx('cheer', EVENTS[-1][1] + 1.2, 0.45)
    # duck music under voice
    e = np.convolve(np.abs(voice), np.ones(int(0.08 * SR)) / int(0.08 * SR), 'same')
    duck = 1 - 0.45 * np.clip(e / (e.max() * 0.25 + 1e-9), 0, 1)
    mix = m * 0.55 * duck + np.stack([voice, voice]) * 0.95 + sfx * 0.8
    fo = int(0.8 * SR); mix[:, -fo:] *= np.linspace(1, 0, fo)
    mix = np.tanh(mix / np.abs(mix).max() * 1.2) / np.tanh(1.2) * 0.95
    sf.write(os.path.join(HERE, 'mix_lollipop.wav'), mix.T, SR)
    print('audio', round(n / SR, 2), 's')


def overlay(fr, t):
    cur = None
    for i, (name, t0, col) in enumerate(EVENTS):
        if t >= t0: cur = (i, name, t0, col)
    if cur is None: return
    i, name, t0, col = cur
    t1 = EVENTS[i + 1][1] if i + 1 < len(EVENTS) else DUR + 1
    a = 1 - R.clamp((t - (t1 - 0.12)) / 0.12)
    cols = RAINBOW if col is None else [col]
    size = 210 if len(name) <= 6 else 190
    R.word(fr, name, W / 2, 170, size, cols, t0, t, 0.05, alpha=a, pulse=0.12 * math.exp(-max(0, t - t0) * 5))


def frames():
    p = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-i', os.path.join(WD, 'retimed.mp4'), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                         stdout=subprocess.PIPE)
    sz = W * H * 3
    while True:
        b = p.stdout.read(sz)
        if len(b) < sz: break
        yield b


def compose(b, t):
    fr = Image.frombytes('RGB', (W, H), b).convert('RGBA')
    overlay(fr, t)
    return fr.convert('RGB')


if __name__ == '__main__':
    os.chdir(HERE)
    if PREV:
        od = os.environ.get('PREVIEW_DIR', '/tmp')
        for i, b in enumerate(frames()):
            for t in PREV:
                if abs(i / FPS - t) < 0.5 / FPS: compose(b, i / FPS).save(f'{od}/lolli_{t}.png'); print('saved', t)
        sys.exit()
    build_audio()
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-i', 'mix_lollipop.wav', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
                           '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', 'baby_yuyu_lollipop.mp4'], stdin=subprocess.PIPE)
    for i, b in enumerate(frames()):
        ff.stdin.write(compose(b, i / FPS).tobytes())
    ff.stdin.close(); ff.wait(); print('done -> baby_yuyu_lollipop.mp4')
