"""Original 'Bubble Color Song' for Baby Yusuf - high-energy kids-pop arrangement.
120 BPM, C major (finale up a tone). Four-on-the-floor kick, clap+snare, 16th hats, bouncy octave bass,
offbeat synth stabs, square lead doubled by glockenspiel, sparkle arps, fills + risers + crashes,
side-chain pump, bubble pops and TTS vocals with kid-chorus layers and hype shouts. Writes song.wav.
Timeline (s): intro 0-8, colours 8-88 (16 s each), finale 88-104, ending 104-108."""
import numpy as np, wave
from scipy.signal import lfilter, butter, sosfilt

SR, BPM = 44100, 120
BEAT = 60 / BPM; BAR = 4 * BEAT; S16 = BEAT / 4
DUR = 108.0
N = int(SR * (DUR + 1))
rng = np.random.default_rng(7)
BUSES = ('lead', 'glock', 'stab', 'arp', 'pad', 'bass', 'kick', 'drm', 'fx', 'vox')
bus = {k: np.zeros((N, 2)) for k in BUSES}
COLORS = ['red', 'yellow', 'blue', 'green', 'purple']
T_COL0, SEC, T_FIN, T_END = 8.0, 16.0, 88.0, 104.0
kick_times = []

mf = lambda m: 440 * 2 ** ((m - 69) / 12)
def tt(d): return np.arange(int(SR * d)) / SR


def add(b, sig, t, g=1.0, pan=0.0):
    i = int(round(t * SR))
    if i >= N or i < 0: return
    n = min(len(sig), N - i)
    if sig.ndim == 2:
        bus[b][i:i + n] += sig[:n] * g; return
    bus[b][i:i + n, 0] += sig[:n] * g * np.sqrt(0.5 * (1 - pan))
    bus[b][i:i + n, 1] += sig[:n] * g * np.sqrt(0.5 * (1 + pan))


def lp(x, fc, order=2):
    return sosfilt(butter(order, min(fc, SR * 0.45), 'low', fs=SR, output='sos'), x)


def hp(x, fc, order=2):
    return sosfilt(butter(order, fc, 'high', fs=SR, output='sos'), x)


def saw(f, x, detune=0.0):
    ph = (f * (1 + detune) * x) % 1.0
    return 2 * ph - 1


def square(f, x, pw=0.5):
    return np.where((f * x) % 1.0 < pw, 1.0, -1.0)


def adsr(x, d, a=0.005, dec=0.1, s=0.6, r=0.08):
    env = np.where(x < a, x / a, s + (1 - s) * np.exp(-(x - a) / dec))
    return env * np.clip((d - x) / r, 0, 1)


# ---------------------------------------------------------------- instruments
def lead(m, t, d, g=0.16):
    f = mf(m); x = tt(d + 0.1)
    vib = 1 + 0.004 * np.sin(2 * np.pi * 5.5 * x) * np.clip((x - 0.15) / 0.2, 0, 1)
    ph = np.cumsum(f * vib) / SR
    s = np.where(ph % 1 < 0.5, 1.0, -1.0) * 0.6 + (2 * (ph * 1.004 % 1) - 1) * 0.4
    s = lp(s, 4200) * adsr(x, d + 0.1, 0.004, 0.18, 0.55, 0.06)
    add('lead', s, t, g, 0.0)


def glock(m, t, g=0.22, pan=0.25):
    f = mf(m); x = tt(1.4)
    s = (np.sin(2 * np.pi * f * x) * np.exp(-x * 3.2) + 0.4 * np.sin(2 * np.pi * f * 2.76 * x) * np.exp(-x * 10)
         + 0.2 * np.sin(2 * np.pi * f * 5.4 * x) * np.exp(-x * 20)) * np.clip(x / 0.002, 0, 1)
    add('glock', s, t, g, pan)


def stab(notes, t, g=0.10, d=0.16):
    x = tt(d + 0.05); s = np.zeros_like(x)
    for m in notes:
        f = mf(m)
        s += saw(f, x) + saw(f, x, 0.007) * 0.8 + saw(f, x, -0.007) * 0.8
    env = np.exp(-x * 9) * np.clip((d + 0.05 - x) / 0.03, 0, 1) * np.clip(x / 0.003, 0, 1)
    s = lp(s * env, 3200)
    st = np.stack([s * 0.9, lp(np.roll(s, 300), 3000)], 1)  # width
    add('stab', st, t, g)


def arp_note(m, t, g=0.05, pan=0.0):
    f = mf(m); x = tt(0.18)
    s = square(f, x, 0.25) * np.exp(-x * 22) * np.clip(x / 0.002, 0, 1)
    add('arp', lp(s, 6000), t, g, pan)


def pad(notes, t, d, g=0.05):
    x = tt(d + 0.3); s = np.zeros_like(x)
    for m in notes:
        f = mf(m)
        for dt in (-0.006, 0, 0.006): s += saw(f, x, dt)
    s = lp(s, 1800) * np.clip(x / 0.25, 0, 1) * np.clip((d + 0.3 - x) / 0.3, 0, 1)
    add('pad', np.stack([s, np.roll(s, 500)], 1), t, g)


def bass(m, t, d, g=0.32):
    f = mf(m); x = tt(d)
    s = np.sin(2 * np.pi * f * x) + 0.5 * lp(saw(f, x), 900)
    s *= np.clip(x / 0.004, 0, 1) * np.clip((d - x) / 0.03, 0, 1) * (0.7 + 0.3 * np.exp(-x * 8))
    add('bass', s, t, g)


def kick(t, g=1.0):
    x = tt(0.4); f = 140 * np.exp(-x * 30) + 48
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 7.5)
    s[:120] += np.linspace(1, 0, 120) * 0.6        # click
    add('kick', np.tanh(s * 1.6), t, g)
    kick_times.append(t)


def snare(t, g=0.4):
    x = tt(0.25); nz = hp(rng.uniform(-1, 1, len(x)), 1500)
    body = np.sin(2 * np.pi * 190 * x) * np.exp(-x * 25)
    add('drm', nz * np.exp(-x * 18) * 0.8 + body * 0.5, t, g, 0.05)


def clap(t, g=0.35):
    x = tt(0.3); nz = hp(rng.uniform(-1, 1, len(x)), 900)
    env = sum(np.exp(-np.maximum(x - o, 0) * 60) * (x >= o) for o in (0, 0.01, 0.021)) * 0.5 + np.exp(-x * 14) * 0.6
    add('drm', lp(nz * env, 7000), t, g, -0.1)


def hat(t, g=0.06, open_=False, pan=0.3):
    x = tt(0.25 if open_ else 0.05); nz = hp(rng.uniform(-1, 1, len(x)), 7000)
    add('drm', nz * np.exp(-x * (12 if open_ else 80)), t, g, pan)


def crash(t, g=0.22):
    x = tt(2.0); nz = hp(rng.uniform(-1, 1, (len(x), 2)), 4500)
    add('drm', nz * np.exp(-x * 2.2)[:, None], t, g)


def riser(t, d, g=0.12):
    x = tt(d); nz = rng.uniform(-1, 1, len(x))
    # sweep: progressively less low-passed noise + rising tone
    s = np.concatenate([lp(nz[i:i + 2205], 400 + 9000 * (i / len(x)) ** 2) for i in range(0, len(x), 2205)])[:len(x)]
    tone = np.sin(2 * np.pi * np.cumsum(300 + 900 * (x / d) ** 2) / SR) * 0.25
    add('fx', (s + tone) * (x / d) ** 2, t, g)


def pop(t, g=0.45, f0=500, pan=0.0):
    x = tt(0.12); f = f0 + 1800 * x / 0.12
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 35)
    s[:80] += rng.uniform(-0.6, 0.6, 80)
    add('fx', s, t, g, pan)


def boing(t, g=0.18):
    x = tt(0.45); f = 220 + 160 * np.sin(2 * np.pi * 9 * x) * np.exp(-x * 4) + 200 * x
    add('fx', np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 5), t, g)


def blub(t, g=0.07, pan=0.0):
    x = tt(0.08); f = 700 + 1600 * (x / 0.08) ** 0.6
    add('fx', np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * x / 0.08), t, g, pan)


def sparkle(t, g=0.12):
    for k, m in enumerate([84, 88, 91, 96, 100]):
        glock(m, t + k * 0.05, g, 0.6 - k * 0.3)


# ---------------------------------------------------------------- song data
CH = [(60, 64, 67), (55, 59, 62), (57, 60, 64), (53, 57, 60), (60, 64, 67), (55, 59, 62), (53, 57, 60), (55, 59, 62)]
ROOT = [36, 43, 45, 41, 36, 43, 41, 43]
MEL = [
    [(0, 72, .5), (.5, 72, .5), (1, 76, 1), (2, 79, 1), (3, 76, 1)],
    [(0, 74, 1), (1, 71, 1), (2, 74, 1.5), (3.5, 79, .5)],
    [(0, 72, .5), (.5, 72, .5), (1, 76, 1), (2, 81, 1), (3, 79, 1)],
    [(0, 77, 1), (1, 76, .5), (1.5, 76, .5), (2, 74, 2)],
    [(0, 72, .5), (.5, 72, .5), (1, 76, 1), (2, 79, 1), (3, 76, 1)],
    [(0, 79, 1), (1, 77, 1), (2, 76, 1), (3, 74, 1)],
    [(0, 72, .5), (.5, 74, .5), (1, 76, .5), (1.5, 77, .5), (2, 79, 1), (3, 84, 1)],
    [(0, 83, 1), (1, 79, 1), (2, 77, .5), (2.5, 76, .5), (3, 74, 1)],
]


def drums_bar(tb, fill=False, half=False):
    for b in range(4):
        kick(tb + b * BEAT, 1.0 if b % 2 == 0 else 0.9)
    if not half:
        for b in (1, 3):
            clap(tb + b * BEAT); snare(tb + b * BEAT, 0.25)
    for s in range(16):
        if s % 4 == 2: hat(tb + s * S16, 0.09, open_=True, pan=0.35)
        else: hat(tb + s * S16, 0.05 if s % 2 else 0.035, pan=-0.3 + 0.04 * s)
    if fill:   # snare roll over beats 3-4, crescendo
        for s in range(8):
            snare(tb + 2 * BEAT + s * S16, 0.12 + 0.05 * s)


def band_bar(tb, b, tr=0, lead_on=True, arp_on=True, full=True):
    ch = [n + tr for n in CH[b]]; r = ROOT[b] + tr
    for e in range(8):                                # octave-bouncing bass
        bass(r + (12 if e % 2 else 0), tb + e * BEAT / 2, BEAT / 2 * 0.85, 0.30 if e % 2 else 0.34)
    for e in (0.5, 1.5, 2.5, 3.5):                    # offbeat stabs
        stab([n + 12 for n in ch], tb + e * BEAT, 0.075 if full else 0.05)
    pad(ch, tb, BAR, 0.035)
    if arp_on:
        seq = [ch[0] + 24, ch[1] + 24, ch[2] + 24, ch[1] + 24]
        for s in range(16):
            arp_note(seq[s % 4] + (12 if s % 8 == 7 else 0), tb + s * S16, 0.035, -0.5 + (s % 4) * 0.33)
    if lead_on:
        for beat, m, d in MEL[b]:
            lead(m + tr, tb + beat * BEAT, d * BEAT * 0.92)
            glock(m + tr + 12, tb + beat * BEAT, 0.14)


# ---------------------------------------------------------------- vocals
def load_vox(name, folder='vo'):
    with wave.open(f'{folder}/{name}.wav') as w:
        sr = w.getframerate(); a = np.frombuffer(w.readframes(w.getnframes()), np.int16) / 32768.0
    nz = np.where(np.abs(a) > 0.01)[0]
    a = a[max(nz[0] - 200, 0): nz[-1] + 800]
    n_out = int(len(a) * SR / sr)               # resample only - natural pitch
    return np.interp(np.linspace(0, len(a) - 1, n_out), np.arange(len(a)), a)


def vox(name, t, g=1.0, chorus=False):
    add('vox', load_vox(name), t, g, 0)
    if chorus:   # a second friendly voice singing along softly
        add('vox', load_vox(name, 'vo2'), t + 0.02, g * 0.4, 0.35)


# ---------------------------------------------------------------- arrangement
# INTRO (0-8): sparkly glock + bass pulse, then build with snare roll + riser, drop at 8.0
for b in range(4):
    tb = b * BAR
    for k, m in enumerate([72, 76, 79, 84, 79, 76, 79, 84]):
        glock(m, tb + k * BEAT / 2, 0.2, -0.3 + 0.08 * k)
        arp_note(m + 12, tb + k * BEAT / 2, 0.025)
    pad(CH[b * 2 % 8], tb, BAR, 0.04)
    if b >= 1:
        for e in range(4): kick(tb + e * BEAT, 0.7 + 0.1 * b)
    if b >= 2:
        for e in range(8): bass(ROOT[b * 2 % 8] + (12 if e % 2 else 0), tb + e * BEAT / 2, BEAT / 2 * 0.8, 0.26)
        clap(tb + BEAT); clap(tb + 3 * BEAT)
        for s in range(16): hat(tb + s * S16, 0.03 + 0.002 * s)
for s in range(16):                                   # final-bar snare build
    snare(3 * BAR + s * S16, 0.08 + 0.02 * s)
riser(4.0, 4.0, 0.16)
for k in range(3): pop(1.6 + k * 0.5, 0.4, 500 + 150 * k)
vox('intro1', 0.4)
vox('intro2', 4.2, 1.0, chorus=True)
vox('letsgo', 6.9, 1.0, chorus=True)
sparkle(7.6)

# COLOUR SECTIONS
for i, c in enumerate(COLORS):
    t0 = T_COL0 + i * SEC
    crash(t0); boing(t0 + 0.05)
    for b in range(8):
        tb = t0 + b * BAR
        drums_bar(tb, fill=(b == 7))
        band_bar(tb, b, lead_on=True, arp_on=(b >= 2))
    riser(t0 + 6 * BAR, 2 * BAR, 0.12)
    vox(c, t0 + 0.05, 1.05, chorus=True)
    vox(f'{c}_b', t0 + BAR)
    vox('sky', t0 + 2 * BAR + 0.1)
    vox(f'{c}_b', t0 + 3 * BAR)
    vox('high', t0 + 4 * BAR + 0.1)
    for k in range(3):
        vox('pop1', t0 + 5 * BAR + k * BEAT, 0.95, chorus=True)
        pop(t0 + 5 * BAR + k * BEAT, 0.6, 450 + 200 * k, (-0.4, 0, 0.4)[k])
    vox('hey', t0 + 5 * BAR + 3 * BEAT, 1.0, chorus=True)
    vox(c, t0 + 6 * BAR + 0.05, 1.1, chorus=True)
    sparkle(t0 + 6 * BAR)
    vox('woohoo', t0 + 6 * BAR + 2.2 * BEAT, 0.8, chorus=True)
    if i < len(COLORS) - 1:
        vox('next', t0 + 7 * BAR + 0.05, 0.9)
    for k in range(18):                               # bubbling texture
        blub(t0 + rng.uniform(0.3, 15.5), 0.06, rng.uniform(-.9, .9))
    for k in range(8):
        pop(t0 + rng.uniform(0.5, 15), 0.14, rng.uniform(600, 1100), rng.uniform(-.8, .8))

# FINALE (88-104): key up a tone, everything on
crash(T_FIN, 0.28); boing(T_FIN)
for b in range(8):
    tb = T_FIN + b * BAR
    drums_bar(tb, fill=(b == 7))
    band_bar(tb, b, tr=2, lead_on=True, arp_on=True)
vox('rainbow', T_FIN + 0.1, 1.05, chorus=True)
vox('clap', T_FIN + BAR + 0.6, 0.9, chorus=True)
vox('yay', T_FIN + 2 * BAR, 1.0, chorus=True)
vox('woohoo', T_FIN + 3 * BAR + 0.5, 0.9, chorus=True)
for k, c in enumerate(COLORS):
    vox(c, T_FIN + 4 * BAR + k * 2 * BEAT, 1.0, chorus=True)
    pop(T_FIN + 4 * BAR + k * 2 * BEAT, 0.45, 500 + 120 * k)
vox('bye', T_FIN + 6 * BAR + 0.2, 1.0, chorus=True)
for k in range(30):
    blub(T_FIN + rng.uniform(0, 16), 0.06, rng.uniform(-.9, .9))
for k in range(16):
    pop(T_FIN + rng.uniform(0, 16), 0.15, rng.uniform(600, 1200), rng.uniform(-.8, .8))

# ENDING (104-108): big chord hit + cheer
crash(T_END, 0.3); kick(T_END)
for j, m in enumerate([62, 66, 69, 74, 78, 81, 86]):
    glock(m + 12, T_END + j * 0.06, 0.2)
stab([74, 78, 81, 86], T_END, 0.12, d=1.2)
pad([62, 66, 69], T_END, 3.0, 0.06)
bass(38, T_END, 2.0, 0.4)
vox('yay2', T_END + 0.3, 1.0, chorus=True)
sparkle(T_END + 1.0)

# ---------------------------------------------------------------- mix
def reverb(x, secs=1.4, wet=0.18):
    n = int(SR * secs); ir = rng.normal(0, 1, (n, 2)) * np.exp(-np.arange(n) / SR * 4.5)[:, None]
    ir[:int(SR * 0.012)] = 0
    L = 1 << int(np.ceil(np.log2(len(x) + n)))
    out = np.stack([np.fft.irfft(np.fft.rfft(x[:, c], L) * np.fft.rfft(ir[:, c], L), L)[:len(x)] for c in range(2)], 1)
    return x + wet * out / (np.max(np.abs(out)) + 1e-9) * np.max(np.abs(x))


# side-chain pump envelope from kick hits
pump = np.ones(N)
for kt in kick_times:
    i = int(kt * SR); n = min(int(SR * 0.22), N - i)
    if n > 0: pump[i:i + n] = np.minimum(pump[i:i + n], 1 - 0.55 * np.exp(-np.arange(n) / SR * 14))

gains = {'lead': 0.75, 'glock': 0.8, 'stab': 0.9, 'arp': 0.8, 'pad': 0.8, 'bass': 0.95, 'kick': 0.9, 'drm': 0.75, 'fx': 0.85}
pumped = sum(bus[k] * gains[k] for k in ('stab', 'arp', 'pad', 'bass')) * pump[:, None]
music = pumped + sum(bus[k] * gains[k] for k in ('lead', 'glock', 'fx'))
music = reverb(music, 1.2, 0.16) + bus['kick'] * gains['kick'] + bus['drm'] * gains['drm']
vx = reverb(bus['vox'] * 1.7, 0.6, 0.07)
vx = vx + 0.12 * hp(vx.T, 2500).T            # gentle presence
env = np.abs(vx).max(1)
k = int(SR * 0.08); env = np.convolve(env, np.ones(k) / k, 'same')
duck = 1 - 0.3 * np.clip(env / (env.max() * 0.3), 0, 1)
mix = music * duck[:, None] + vx
mix = mix[:int(SR * DUR)]
fo = int(SR * 1.2); mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
mix = np.tanh(mix / np.max(np.abs(mix)) * 1.6) / np.tanh(1.6) * 0.95
with wave.open('song.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print('song.wav', mix.shape[0] / SR, 's')
