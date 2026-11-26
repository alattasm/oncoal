"""Original 'Bubble Color Song' for Baby Yusuf: 120 BPM, C major, glockenspiel + ukulele + bass + kid drums,
bubble-pop SFX and Piper TTS vocal lines (pitched up slightly). Writes song.wav (44.1 kHz stereo).
Timeline (seconds): intro 0-8, colors 8-88 (16 s each), finale 88-104, end chord 104-108."""
import numpy as np, wave

SR, BPM = 44100, 120
BEAT = 60 / BPM; BAR = 4 * BEAT
DUR = 108.0
N = int(SR * (DUR + 1))
rng = np.random.default_rng(7)
bus = {k: np.zeros((N, 2)) for k in ('mel', 'uke', 'bass', 'drm', 'sfx', 'vox')}
COLORS = ['red', 'yellow', 'blue', 'green', 'purple']
T_COL0, SEC = 8.0, 16.0
T_FIN, T_END = 88.0, 104.0

mf = lambda m: 440 * 2 ** ((m - 69) / 12)


def add(b, sig, t, g=1.0, pan=0.0):
    i = int(t * SR)
    if i >= N or i < 0: return
    n = min(len(sig), N - i)
    bus[b][i:i + n, 0] += sig[:n] * g * np.sqrt(0.5 * (1 - pan))
    bus[b][i:i + n, 1] += sig[:n] * g * np.sqrt(0.5 * (1 + pan))


def tt(d): return np.arange(int(SR * d)) / SR


def glock(m, t, g=0.3, pan=0.2):
    f = mf(m); x = tt(1.6)
    s = (np.sin(2 * np.pi * f * x) * np.exp(-x * 3) + 0.4 * np.sin(2 * np.pi * f * 2.76 * x) * np.exp(-x * 9)
         + 0.2 * np.sin(2 * np.pi * f * 5.4 * x) * np.exp(-x * 18))
    s *= np.clip(x / 0.002, 0, 1)
    add('mel', s, t, g, pan)


def pluck(m, t, g=0.12, pan=-0.3, d=0.9):
    f = mf(m); x = tt(d)
    s = sum(np.sin(2 * np.pi * f * k * x) / k ** 1.3 * np.exp(-x * (3 + 2.5 * k)) for k in range(1, 7))
    s *= np.clip(x / 0.003, 0, 1)
    add('uke', s, t, g, pan)


def bass(m, t, d, g=0.35):
    f = mf(m); x = tt(d)
    s = (np.sin(2 * np.pi * f * x) + 0.25 * np.sin(4 * np.pi * f * x)) * np.exp(-x * 1.5)
    s *= np.clip(x / 0.01, 0, 1) * np.clip((d - x) / 0.04, 0, 1)
    add('bass', s, t, g)


def kick(t, g=0.9):
    x = tt(0.35); f = 110 * np.exp(-x * 25) + 50
    add('drm', np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 10), t, g)


def clap(t, g=0.35):
    x = tt(0.25); nz = rng.uniform(-1, 1, len(x))
    nz = np.diff(np.concatenate([[0], nz]))  # brighten
    env = np.exp(-x * 30) + 0.6 * (np.exp(-np.maximum(x - 0.012, 0) * 30) * (x > 0.012))
    add('drm', nz * env, t, g, 0.1)


def shaker(t, g=0.08, pan=0.4):
    x = tt(0.08); nz = np.diff(np.concatenate([[0], rng.uniform(-1, 1, len(x))]))
    add('drm', nz * np.exp(-x * 60), t, g, pan)


def pop(t, g=0.45, f0=500, pan=0.0):
    x = tt(0.12); f = f0 + 1800 * x / 0.12
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 35)
    s[:80] += rng.uniform(-0.6, 0.6, 80)
    add('sfx', s, t, g, pan)


def sparkle(t, g=0.12):
    for k, m in enumerate([84, 88, 91, 96]):
        glock(m, t + k * 0.06, g, 0.5 - k * 0.3)


def chime_whoosh(t, g=0.1):
    x = tt(1.2); f = 300 + 900 * x
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * x / 1.2) ** 2 * 0.5
    add('sfx', s, t, g)


# ---------------- harmony / melody ----------------
CHORDS = [(60, 64, 67), (55, 59, 62, 67), (57, 60, 64), (53, 57, 60, 65)] * 2
CHORDS[6] = (53, 57, 60, 65); CHORDS[7] = (55, 59, 62, 67)
ROOTS = [36, 43, 45, 41, 36, 43, 41, 43]
MEL = [
    [(0, 72, .5), (.5, 72, .5), (1, 76, 1), (2, 79, 1), (3, 76, 1)],
    [(0, 74, 1), (1, 71, 1), (2, 74, 2)],
    [(0, 72, .5), (.5, 72, .5), (1, 76, 1), (2, 81, 1), (3, 79, 1)],
    [(0, 77, 1), (1, 76, 1), (2, 74, 2)],
    [(0, 72, .5), (.5, 72, .5), (1, 76, 1), (2, 79, 1), (3, 76, 1)],
    [(0, 79, 1), (1, 77, 1), (2, 76, 1), (3, 74, 1)],
    [(0, 72, .5), (.5, 74, .5), (1, 76, 1), (2, 77, 1), (3, 74, 1)],
    [(0, 72, 2), (2, 67, .5), (2.5, 71, .5), (3, 74, 1)],
]


def section(t0, bars=8, mel=True, full=True, transpose=0):
    for b in range(bars):
        tb = t0 + b * BAR; ch = [n + transpose for n in CHORDS[b % 8]]
        # ukulele strum pattern: D . D U . U D U
        for k, (beat, up) in enumerate([(0, 0), (1, 0), (1.5, 1), (2.5, 1), (3, 0), (3.5, 1)]):
            notes = ch[::-1] if up else ch
            for j, n in enumerate(notes):
                pluck(n + 12, tb + beat * BEAT + j * 0.012, 0.09 if up else 0.12)
        bass(ROOTS[b % 8] + transpose, tb, BEAT * 1.6)
        bass(ROOTS[b % 8] + transpose + 7, tb + 2 * BEAT, BEAT * 1.6)
        if full:
            kick(tb); kick(tb + 2 * BEAT); kick(tb + 2.5 * BEAT, 0.5)
            clap(tb + BEAT); clap(tb + 3 * BEAT)
            for e in range(8): shaker(tb + e * BEAT / 2, 0.07 if e % 2 else 0.05)
        if mel:
            for beat, m, d in MEL[b % 8]:
                glock(m + transpose, tb + beat * BEAT, 0.26)


# ---------------- vocals ----------------
def load_vox(name, pitch=1.1):
    with wave.open(f'vo/{name}.wav') as w:
        sr = w.getframerate(); a = np.frombuffer(w.readframes(w.getnframes()), np.int16) / 32768.0
    # trim silence
    nz = np.where(np.abs(a) > 0.01)[0]
    a = a[max(nz[0] - 200, 0): nz[-1] + 800]
    # pitch/speed up (kid-like brightness) and resample to SR
    n_out = int(len(a) * SR / sr / pitch)
    return np.interp(np.linspace(0, len(a) - 1, n_out), np.arange(len(a)), a)


def vox(name, t, g=1.0, chorus=False, pitch=1.1):
    s = load_vox(name, pitch)
    add('vox', s, t, g, 0)
    if chorus:   # "group of kids" layer: higher, slightly late, panned
        add('vox', load_vox(name, pitch * 1.12), t + 0.025, g * 0.55, -0.5)
        add('vox', load_vox(name, pitch * 1.06), t + 0.045, g * 0.5, 0.5)


# intro: 4 bars, glock arpeggios + light drums from bar 2
for b in range(4):
    tb = b * BAR
    for k, m in enumerate([72, 76, 79, 84, 79, 76, 79, 84]):
        glock(m, tb + k * BEAT / 2, 0.18, -0.2 + 0.05 * k)
    bass(36 if b % 2 == 0 else 43, tb, BAR * 0.9)
    if b >= 2:
        kick(tb); kick(tb + 2 * BEAT); clap(tb + BEAT); clap(tb + 3 * BEAT)
for k in range(3): pop(0.6 + 1.1 + k * 0.5, 0.4, 500 + 150 * k)
vox('intro1', 0.5)
vox('intro2', 4.3)
sparkle(7.5)

# color sections
for i, c in enumerate(COLORS):
    t0 = T_COL0 + i * SEC
    section(t0)
    chime_whoosh(t0 - 0.6)
    vox(c, t0 + 0.05, 1.0, chorus=True)
    vox(f'{c}_b', t0 + BAR)
    vox('sky', t0 + 2 * BAR + 0.1)
    vox(f'{c}_b', t0 + 3 * BAR)
    vox('high', t0 + 4 * BAR + 0.1)
    for k in range(3):
        vox('pop1', t0 + 5 * BAR + k * BEAT * 1.0, 0.9, chorus=True)
        pop(t0 + 5 * BAR + k * BEAT, 0.55, 450 + 200 * k, (-0.4, 0, 0.4)[k])
    vox(c, t0 + 6 * BAR + 0.05, 1.05, chorus=True)
    sparkle(t0 + 6 * BAR)
    if i < len(COLORS) - 1:
        vox('next', t0 + 7 * BAR + 0.1, 0.85)
    # random ambient bubble pops during the section
    for k in range(10):
        pop(t0 + rng.uniform(0.5, 15), 0.12, rng.uniform(600, 1100), rng.uniform(-.8, .8))

# finale: key up a whole step, full band
section(T_FIN, 8, True, True, transpose=2)
vox('rainbow', T_FIN + 0.1, 1.0, chorus=True)
vox('yay', T_FIN + 2 * BAR, 1.0, chorus=True)
for k, c in enumerate(COLORS):
    vox(c, T_FIN + 4 * BAR + k * 2 * BEAT, 0.95, chorus=True)
    pop(T_FIN + 4 * BAR + k * 2 * BEAT, 0.4, 500 + 120 * k)
vox('bye', T_FIN + 6 * BAR + 0.2, 1.0)
for k in range(14):
    pop(T_FIN + rng.uniform(0, 16), 0.15, rng.uniform(600, 1200), rng.uniform(-.8, .8))
# ending chord
for j, m in enumerate([60, 64, 67, 72, 76, 79, 84]):
    glock(m + 2, T_END + j * 0.07, 0.25)
    pluck(m + 2, T_END + j * 0.015, 0.12, d=2.5)
bass(38, T_END, 2.5, 0.4); kick(T_END); sparkle(T_END + 0.6)


# ---------------- mix ----------------
def reverb(x, secs=1.4, wet=0.18):
    n = int(SR * secs); ir = rng.normal(0, 1, (n, 2)) * np.exp(-np.arange(n) / SR * 4.5)[:, None]
    ir[:int(SR * 0.012)] = 0
    L = 1 << int(np.ceil(np.log2(len(x) + n)))
    out = np.stack([np.fft.irfft(np.fft.rfft(x[:, c], L) * np.fft.rfft(ir[:, c], L), L)[:len(x)] for c in range(2)], 1)
    return x + wet * out / np.max(np.abs(out)) * np.max(np.abs(x))


gains = {'mel': 0.9, 'uke': 0.8, 'bass': 0.9, 'drm': 0.75, 'sfx': 0.8, 'vox': 1.5}
music = sum(bus[k] * gains[k] for k in ('mel', 'uke', 'bass', 'drm', 'sfx'))
music = reverb(music, 1.3, 0.2)
vx = reverb(bus['vox'] * gains['vox'], 0.8, 0.12)
# duck music under vocals
env = np.abs(vx).max(1)
k = int(SR * 0.08); env = np.convolve(env, np.ones(k) / k, 'same')
duck = 1 - 0.35 * np.clip(env / (env.max() * 0.3), 0, 1)
mix = music * duck[:, None] + vx
# fade out tail
mix = mix[:int(SR * DUR)]
fo = int(SR * 1.5); mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
mix = np.tanh(mix / np.max(np.abs(mix)) * 1.3) * 0.92
with wave.open('song.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print('song.wav', mix.shape[0] / SR, 's')
