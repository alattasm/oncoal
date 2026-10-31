"""Original Yemeni-style track: Bayati on D, oud (Karplus-Strong), mirwas drum, claps, copper plate."""
import numpy as np, wave
SR = 44100
BPM = 120
E8 = 60 / BPM / 2          # eighth note = 0.25 s
DUR = 44.0
rng = np.random.default_rng(7)
mix = np.zeros(int(SR * (DUR + 2)))

# Bayati on D with half-flat second (cents)
CENTS = [0, 150, 300, 500, 700, 800, 1000]
def freq(deg, base=146.83):
    o, d = divmod(deg, 7)
    return base * 2 ** ((CENTS[d] + 1200 * o) / 1200)

def add(sig, t, gain=1.0):
    i = int(t * SR)
    n = min(len(sig), len(mix) - i)
    mix[i:i + n] += sig[:n] * gain

def oud(f, dur, bright=0.5):
    n = int(SR * (dur + 0.6))
    p = int(SR / f)
    buf = rng.uniform(-1, 1, p)
    buf = np.convolve(buf, [bright, 1 - bright], 'same')
    out = np.empty(n)
    for i in range(n):
        out[i] = buf[i % p]
        buf[i % p] = 0.996 * 0.5 * (buf[i % p] + buf[(i + 1) % p])
    env = np.ones(n)
    k = int(SR * dur)
    env[k:] = np.linspace(1, 0, n - k)
    # body resonance: light lowpass + plectrum click
    out = np.convolve(out * env, np.ones(4) / 4, 'same')
    out[:200] += rng.uniform(-0.3, 0.3, 200) * np.linspace(1, 0, 200)
    return out

def note(deg, t, dur, gain=0.5, oct_low=False):
    f = freq(deg)
    if dur >= 4 * E8:   # risha tremolo on long notes
        step = E8 / 2
        for j in range(int(dur / step)):
            add(oud(f, step * 1.2, 0.6), t + j * step, gain * (0.8 if j else 1))
    else:
        add(oud(f, dur * 1.1), t, gain)
    if oct_low:
        add(oud(f / 2, dur * 1.3, 0.3), t, gain * 0.6)

def mirwas(t, kind):
    n = int(SR * 0.35); tt = np.arange(n) / SR
    if kind == 'D':
        f = 110 * np.exp(-tt * 9) + 70
        s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 11)
        add(s, t, 0.9)
    else:
        s = np.sin(2 * np.pi * 420 * tt) * np.exp(-tt * 35) * 0.5
        s += rng.uniform(-1, 1, n) * np.exp(-tt * 60) * 0.5
        add(s, t, 0.55)

def clap(t):
    n = int(SR * 0.2); tt = np.arange(n) / SR
    s = np.zeros(n)
    for off in (0, 0.008, 0.017):
        k = int(off * SR)
        s[k:] += rng.uniform(-1, 1, n - k) * np.exp(-tt[:n - k] * 45)
    s = np.diff(s, prepend=0)
    add(s, t, 0.3)

def sahn(t):  # copper plate
    n = int(SR * 0.6); tt = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * f * tt) * a for f, a in ((1830, .5), (2730, .4), (3990, .3), (5170, .2)))
    add(s * np.exp(-tt * 9), t, 0.07)

# drone pad (D + A), swelling
tt = np.arange(len(mix)) / SR
drone = sum(np.sin(2 * np.pi * f * tt + np.sin(tt * .3 + f)) * a for f, a in ((73.42, .5), (110.0, .3), (146.83, .2)))
denv = np.clip(tt / 3, 0, 1) * np.clip((DUR + 0.5 - tt) / 3, 0, 1)
mix += drone * denv * 0.09

# intro taqsim (0-4 s, free rhythm)
for deg, t, d in [(0, 0.15, 1.0), (1, 1.2, .3), (2, 1.5, .3), (3, 1.8, .5), (4, 2.3, .9), (3, 3.2, .25), (2, 3.45, .25), (1, 3.7, .3)]:
    note(deg, t, d, 0.55, oct_low=(d > .8))

PH = {
 'A': [(4,2),(3,1),(4,1),(5,2),(4,1),(3,1),(2,2),(1,1),(2,1),(3,4)],
 'B': [(2,1),(3,1),(4,2),(3,1),(2,1),(1,2),(0,1),(1,1),(2,1),(1,1),(0,4)],
 'C': [(7,2),(6,1),(5,1),(6,2),(5,1),(4,1),(5,2),(4,1),(3,1),(4,4)],
 'D': [(4,1),(5,1),(4,1),(3,1),(2,2),(3,1),(2,1),(1,2),(2,1),(1,1),(0,4)],
}
order = 'ABADCDCBD'   # 9 phrases x 4 s = 36 s, from 4 s to 40 s
t = 4.0
for k, name in enumerate(order):
    for deg, n8 in PH[name]:
        note(deg, t, n8 * E8, 0.5, oct_low=(n8 >= 2))
        t += n8 * E8

# rhythm: 2/4 bars, sixteenth grid  D . T D | . T T .
pat = ['D', None, 'T', 'D', None, 'T', 'T', None]
s16 = E8 / 2
bar = 4.0
while bar < 40.0:
    for i, k in enumerate(pat):
        if k: mirwas(bar + i * s16 + rng.normal(0, .004), k)
    if bar >= 8: clap(bar + 2 * s16); clap(bar + 6 * s16)
    if bar >= 12: sahn(bar)
    bar += 1.0

# ending: tonic tremolo + final dum
note(0, 40.0, 3.0, 0.55, oct_low=True)
mirwas(40.0, 'D'); sahn(40.0)

# reverb
ir_n = int(SR * 1.6)
ir = rng.normal(0, 1, ir_n) * np.exp(-np.arange(ir_n) / SR * 4)
ir[0] = 0
wet = np.fft.irfft(np.fft.rfft(mix, len(mix) + ir_n) * np.fft.rfft(ir, len(mix) + ir_n))[:len(mix)]
out = mix + wet / np.abs(wet).max() * np.abs(mix).max() * 0.25
out = out[:int(SR * DUR)]
fade = int(SR * 1.5); out[-fade:] *= np.linspace(1, 0, fade)
out = np.tanh(out / np.abs(out).max() * 1.4) * 0.9
st = np.stack([out, np.roll(out, 300) * 0.97], 1)
with wave.open('music.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((st * 32767).astype(np.int16).tobytes())
print('ok')
