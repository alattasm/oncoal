"""Original track, produced mix: maqam Hijaz on D, 6/8 (Hadrami zarbadi feel), oud + violins + qanun.
Buses: oud (body EQ) + octave oud, bass, mirwas/riq/claps, drone pad, swells and impacts; stereo + reverb."""
import numpy as np, wave
SR, DUR = 44100, 44.0
E8 = 1 / 6                      # 6/8, one bar per second
N = int(SR * (DUR + 2))
rng = np.random.default_rng(21)
bus = {k: np.zeros((N, 2)) for k in ('oud', 'bass', 'perc', 'pad', 'fx', 'str')}
CENTS = [0, 100, 400, 500, 700, 800, 1000]      # Hijaz

def freq(deg, base=146.83):
    o, d = divmod(deg, 7)
    return base * 2 ** ((CENTS[d] + 1200 * o) / 1200)

def add(b, sig, t, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i >= N: return
    n = min(len(sig), N - i)
    bus[b][i:i + n, 0] += sig[:n] * gain * np.sqrt(0.5 * (1 - pan))
    bus[b][i:i + n, 1] += sig[:n] * gain * np.sqrt(0.5 * (1 + pan))

def ks(f, dur, bright=0.5, decay=0.996):
    n = int(SR * (dur + 0.5)); p = max(2, int(SR / f))
    buf = np.convolve(rng.uniform(-1, 1, p), [bright, 1 - bright], 'same')
    out = np.empty(n)
    for i in range(n):
        j = i % p; out[i] = buf[j]
        buf[j] = decay * 0.5 * (buf[j] + buf[(j + 1) % p])
    env = np.ones(n); k = int(SR * dur); env[k:] = np.linspace(1, 0, n - k) ** 2
    out *= env
    out[:150] += rng.uniform(-0.25, 0.25, 150) * np.linspace(1, 0, 150)   # pick
    return out

def oud_note(deg, t, dur, g, pan=0.15, octave=0):
    f = freq(deg) * 2 ** octave
    if dur >= 4 * E8:                       # risha tremolo
        step = E8 / 2
        for j in range(int(dur / step)):
            add('oud', ks(f, step * 1.15, 0.6), t + j * step + rng.normal(0, .003), g * (0.75 + 0.25 * (j == 0)), pan)
    else:
        add('oud', ks(f, dur * 1.05), t + rng.normal(0, .003), g, pan)

def violin(f, dur):
    n = int(SR * (dur + 0.15)); tt = np.arange(n) / SR
    vib = 1 + 0.006 * np.sin(2 * np.pi * 5.5 * tt) * np.clip(tt / 0.25, 0, 1)
    ph = 2 * np.pi * np.cumsum(f * vib) / SR
    s = sum(np.sin(h * ph) / h ** 1.25 for h in range(1, 12))
    return s * np.clip(tt / 0.08, 0, 1) * np.clip((dur + 0.15 - tt) / 0.15, 0, 1)

def strings(deg, t, dur, g):
    f = freq(deg) * 2
    for det, pan in ((0.996, -0.6), (1.0, 0.0), (1.004, 0.6)):
        add('str', violin(f * det, dur), t + rng.uniform(0, .02), g, pan)

def qanun(deg, t, g=0.12):
    add('oud', ks(freq(deg) * 4, 0.25, 0.8, 0.997), t, g, rng.uniform(-.6, .6))

def bass(f, t, dur, g=0.5):
    n = int(SR * dur); tt = np.arange(n) / SR
    s = np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(4 * np.pi * f * tt)
    s *= np.clip(tt / 0.01, 0, 1) * np.exp(-tt * 2.2) * np.clip((dur - tt) / 0.05, 0, 1)
    add('bass', s, t, g)

def dum(t, g=1.0):
    n = int(SR * 0.4); tt = np.arange(n) / SR
    f = 120 * np.exp(-tt * 10) + 62
    add('perc', np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 9), t, g)

def tak(t, g=0.5, pan=0.0):
    n = int(SR * 0.15); tt = np.arange(n) / SR
    s = np.sin(2 * np.pi * 440 * tt) * np.exp(-tt * 40) * 0.6 + np.diff(rng.uniform(-1, 1, n + 1)) * np.exp(-tt * 70) * 0.4
    add('perc', s, t, g, pan)

def riq(t, g=0.18, pan=-0.4):
    n = int(SR * 0.12); tt = np.arange(n) / SR
    s = np.diff(np.diff(rng.uniform(-1, 1, n + 2))) * np.exp(-tt * 35)
    s += sum(np.sin(2 * np.pi * f * tt) for f in (5200, 6900, 8100)) * 0.05 * np.exp(-tt * 30)
    add('perc', s, t, g, pan)

def clap(t, g=0.3):
    n = int(SR * 0.2); tt = np.arange(n) / SR; s = np.zeros(n)
    for off in (0, 0.008, 0.017, 0.024):
        k = int(off * SR); s[k:] += rng.uniform(-1, 1, n - k) * np.exp(-tt[:n - k] * 40)
    add('perc', np.diff(s, prepend=0), t, g, rng.uniform(-.3, .3))

def swell(t_end, dur=1.5, g=0.25):
    n = int(SR * dur); tt = np.arange(n) / SR
    s = np.diff(rng.uniform(-1, 1, n + 1)) * (tt / dur) ** 3
    add('fx', s, t_end - dur, g, -0.3); add('fx', s[::-1][::-1] * 0.9, t_end - dur, g, 0.3)

def impact(t, g=0.9):
    n = int(SR * 2.5); tt = np.arange(n) / SR
    f = 70 * np.exp(-tt * 4) + 38
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 2.5)
    s += rng.uniform(-1, 1, n) * np.exp(-tt * 3) * 0.12
    add('fx', s, t, g)

# ---- drone pad (D-A-D) with slow movement ----
tt = np.arange(N) / SR
pad = np.zeros(N)
for f, a in ((73.42, .5), (110.0, .35), (146.83, .25), (220.0, .1)):
    for det in (-0.25, 0.25):
        pad += np.sin(2 * np.pi * (f + det) * tt + rng.uniform(0, 6)) * a
pad *= np.clip(tt / 3, 0, 1) * np.clip((DUR - tt) / 3, 0, 1) * (0.75 + 0.25 * np.sin(tt * 0.5))
bus['pad'][:, 0] += pad * 0.07; bus['pad'][:, 1] += np.roll(pad, 400) * 0.07

# ---- intro: violins hold, oud taqsim 0-4 s ----
strings(0, 0.0, 3.8, 0.05); strings(4, 0.0, 3.8, 0.035)
for deg, t, d in [(0, 0.2, .8), (1, 1.05, .25), (2, 1.3, .5), (3, 1.85, .25), (4, 2.1, .8), (3, 2.95, .2), (2, 3.15, .2), (1, 3.35, .4)]:
    oud_note(deg, t, d, 0.55)
swell(4.0)

PH = {
 'A': [(4,3),(5,1),(4,2),(3,3),(2,1),(3,2),(4,6),(3,2),(2,2),(1,2)],
 'B': [(2,2),(3,1),(4,3),(5,2),(4,1),(3,3),(2,2),(1,2),(2,2),(0,6)],
 'C': [(7,3),(6,1),(5,2),(6,3),(5,1),(4,2),(5,2),(4,2),(3,2),(4,6)],
 'D': [(4,2),(3,1),(2,3),(3,2),(4,1),(5,3),(4,2),(3,2),(2,2),(1,1),(0,5)],
}
ROOT = {'A': [73.42, 98.0, 73.42, 110.0], 'B': [98.0, 87.31, 73.42, 73.42],
        'C': [110.0, 98.0, 110.0, 98.0], 'D': [98.0, 92.5, 82.4, 73.42]}
order = 'ABACDCBAD'
t = 4.0
for k, name in enumerate(order):
    t0 = t
    for deg, n8 in PH[name]:
        oud_note(deg, t, n8 * E8, 0.5, 0.15)
        if k >= 2: oud_note(deg, t + 0.012, n8 * E8, 0.2, -0.5, octave=-1)
        if k >= 4 and n8 >= 2: strings(deg, t, n8 * E8, 0.045 if k < 6 else 0.06)
        t += n8 * E8
    if k >= 3:                                   # qanun arpeggio fills on the last bar of each phrase
        for j, d in enumerate((0, 2, 4, 7, 4, 2)): qanun(d, t0 + 3 + j * E8)
    for b_, f in enumerate(ROOT[name]):
        bass(f, t0 + b_, 0.4, 0.55); bass(f, t0 + b_ + 3 * E8, 0.3, 0.4)

# rhythm: 6/8 bars, dum . tak dum tak tak
bar = 4.0
while bar < 40.0:
    sec = int(bar)
    dum(bar, 1.0); dum(bar + 3 * E8, 0.8)
    tak(bar + 2 * E8, 0.5, 0.2); tak(bar + 4 * E8, 0.4, -0.2); tak(bar + 5 * E8, 0.5, 0.2)
    tak(bar + 1 * E8, 0.15, 0.3)
    if sec >= 8:
        for i in range(12): riq(bar + i * E8 / 2 + rng.normal(0, .003), 0.1 + 0.08 * (i % 2 == 0))
    if sec >= 12: clap(bar + 2 * E8); clap(bar + 5 * E8)
    bar += 1.0
impact(4.0); swell(36.0, 1.0, 0.18); impact(36.0, 0.6)

# ---- ending ----
strings(0, 40.0, 3.2, 0.06); oud_note(0, 40.0, 3.0, 0.55); oud_note(0, 40.01, 3.0, 0.3, -0.5, octave=-1)
dum(40.0, 1.1); bass(73.42, 40.0, 2.5, 0.6); impact(40.0, 0.5)

# ---- mixing ----
def fft_eq(x, bands):
    X = np.fft.rfft(x, axis=0); f = np.fft.rfftfreq(len(x), 1 / SR)
    g = np.ones_like(f)
    for fc, db, q in bands:
        g *= 10 ** (db / 20 * np.exp(-0.5 * (np.log2(np.maximum(f, 1) / fc) * q) ** 2))
    return np.fft.irfft(X * g[:, None], len(x), axis=0)

def reverb(x, sec, amt):
    n = int(SR * sec); out = np.zeros_like(x)
    for c in range(2):
        ir = rng.normal(0, 1, n) * np.exp(-np.arange(n) / SR * (6.9 / sec)); ir[:int(SR * .02)] = 0
        L = len(x) + n
        out[:, c] = np.fft.irfft(np.fft.rfft(x[:, c], L) * np.fft.rfft(ir, L), L)[:len(x)]
    return x + out / (np.abs(out).max() + 1e-9) * np.abs(x).max() * amt

oud = fft_eq(bus['oud'], [(220, 4, 2.5), (480, 3, 3), (1100, 2, 3), (3000, 1.5, 2), (7000, -8, 1), (90, -6, 2)])
mix = (reverb(oud, 1.8, 0.35) * 1.0 + bus['bass'] * 0.8 + reverb(bus['perc'], 0.9, 0.15) * 0.9
       + reverb(bus['pad'], 2.5, 0.5) + reverb(fft_eq(bus['str'], [(6000, -10, 1), (2500, 2, 2)]), 2.2, 0.45) + reverb(bus['fx'], 2.0, 0.3) * 0.8)
mix = mix[:int(SR * DUR)]
fade = int(SR * 1.5); mix[-fade:] *= np.linspace(1, 0, fade)[:, None]
mix /= np.abs(mix).max()
mix = np.tanh(mix * 2.2) / np.tanh(2.2) * 0.93            # glue / loudness
with wave.open('music_pro2.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print('ok')
