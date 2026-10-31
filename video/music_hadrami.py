"""Original Hadrami-style track (the genre of Abu Bakr Salem, no copied melody):
maqam Rast with half-flat 3rd/7th, 6/8 zarbadi-feel rhythm, oud + violin section, hajir/mirwas, claps."""
import numpy as np, wave
SR = 44100
BAR = 1.0                  # one 6/8 bar per second, phrases of 4 bars match the 4 s scene cuts
E8 = BAR / 6
DUR = 44.0
rng = np.random.default_rng(11)
mix = np.zeros(int(SR * (DUR + 2)))
CENTS = [0, 200, 350, 500, 700, 900, 1050]          # Rast on C

def freq(deg, base=130.81):
    o, d = divmod(deg, 7)
    return base * 2 ** ((CENTS[d] + 1200 * o) / 1200)

def add(sig, t, gain=1.0):
    i = int(t * SR); n = min(len(sig), len(mix) - i)
    mix[i:i + n] += sig[:n] * gain

def oud(f, dur, bright=0.5):
    n = int(SR * (dur + 0.6)); p = int(SR / f)
    buf = np.convolve(rng.uniform(-1, 1, p), [bright, 1 - bright], 'same')
    out = np.empty(n)
    for i in range(n):
        out[i] = buf[i % p]
        buf[i % p] = 0.996 * 0.5 * (buf[i % p] + buf[(i + 1) % p])
    env = np.ones(n); k = int(SR * dur); env[k:] = np.linspace(1, 0, n - k)
    out = np.convolve(out * env, np.ones(4) / 4, 'same')
    out[:200] += rng.uniform(-0.3, 0.3, 200) * np.linspace(1, 0, 200)
    return out

def violin(f, dur):
    n = int(SR * (dur + 0.15)); tt = np.arange(n) / SR
    vib = 1 + 0.006 * np.sin(2 * np.pi * 5.5 * tt) * np.clip(tt / 0.25, 0, 1)
    ph = 2 * np.pi * np.cumsum(f * vib) / SR
    s = sum(np.sin(h * ph) / h ** 1.3 for h in range(1, 12))
    env = np.clip(tt / 0.07, 0, 1) * np.clip((dur + 0.15 - tt) / 0.15, 0, 1)
    # section: three slightly detuned players
    return s * env

def note(deg, t, dur, gain=0.5):
    f = freq(deg)
    if dur >= 4 * E8:
        step = E8 / 2
        for j in range(int(dur / step)):
            add(oud(f, step * 1.2, 0.6), t + j * step, gain * (0.8 if j else 1))
    else:
        add(oud(f, dur * 1.1), t, gain)
    if dur >= 2 * E8:
        add(oud(f / 2, dur * 1.3, 0.3), t, gain * 0.5)
    for det in (0.997, 1.0, 1.003):
        add(violin(f * 2 * det, dur), t + rng.uniform(0, .015), gain * 0.06)

def drum(t, kind):
    n = int(SR * 0.45); tt = np.arange(n) / SR
    if kind == 'D':                      # hajir: deep frame drum
        f = 90 * np.exp(-tt * 8) + 55
        s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 8)
        add(s, t, 1.0)
    else:                                # mirwas tak
        s = np.sin(2 * np.pi * 380 * tt) * np.exp(-tt * 35) * 0.5
        s += rng.uniform(-1, 1, n) * np.exp(-tt * 60) * 0.5
        add(s, t, 0.5)

def clap(t):
    n = int(SR * 0.2); tt = np.arange(n) / SR; s = np.zeros(n)
    for off in (0, 0.009, 0.019):
        k = int(off * SR); s[k:] += rng.uniform(-1, 1, n - k) * np.exp(-tt[:n - k] * 45)
    add(np.diff(s, prepend=0), t, 0.32)

def sahn(t):
    n = int(SR * 0.6); tt = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * f * tt) * a for f, a in ((1830, .5), (2730, .4), (3990, .3), (5170, .2)))
    add(s * np.exp(-tt * 9), t, 0.06)

tt = np.arange(len(mix)) / SR
drone = sum(np.sin(2 * np.pi * f * tt + np.sin(tt * .3 + f)) * a for f, a in ((65.41, .5), (98.0, .3), (130.81, .2)))
mix += drone * np.clip(tt / 3, 0, 1) * np.clip((DUR + 0.5 - tt) / 3, 0, 1) * 0.08

# intro: free taqsim with violin answer
for deg, t, d in [(0, 0.1, 1.0), (2, 1.15, .3), (3, 1.45, .3), (4, 1.75, .8), (5, 2.6, .25), (4, 2.85, .25), (3, 3.1, .3), (2, 3.4, .55)]:
    note(deg, t, d, 0.55)

PH = {
 'A': [(4,3),(5,1),(4,2),(3,3),(2,1),(3,2),(4,6),(3,2),(2,2),(1,2)],
 'B': [(2,2),(3,1),(4,3),(5,2),(4,1),(3,3),(2,2),(1,2),(2,2),(0,6)],
 'C': [(7,3),(6,1),(5,2),(6,3),(5,1),(4,2),(5,2),(4,2),(3,2),(4,6)],
 'D': [(4,2),(3,1),(2,3),(3,2),(4,1),(5,3),(4,2),(3,2),(2,2),(1,1),(0,5)],
}
t = 4.0
for name in 'ABACDCBAD':
    for deg, n8 in PH[name]:
        note(deg, t, n8 * E8, 0.5); t += n8 * E8

pat = ['D', None, 'T', 'D', 'T', 'T']     # 6/8 zarbadi-style lilt
bar = 4.0
while bar < 40.0:
    for i, k in enumerate(pat):
        if k: drum(bar + i * E8 + rng.normal(0, .004), k)
    if bar >= 8: clap(bar + 2 * E8); clap(bar + 5 * E8)
    if bar >= 12: sahn(bar)
    bar += BAR

note(0, 40.0, 3.0, 0.55); drum(40.0, 'D'); sahn(40.0)

ir_n = int(SR * 1.8)
ir = rng.normal(0, 1, ir_n) * np.exp(-np.arange(ir_n) / SR * 3.5); ir[0] = 0
wet = np.fft.irfft(np.fft.rfft(mix, len(mix) + ir_n) * np.fft.rfft(ir, len(mix) + ir_n))[:len(mix)]
out = (mix + wet / np.abs(wet).max() * np.abs(mix).max() * 0.28)[:int(SR * DUR)]
fade = int(SR * 1.5); out[-fade:] *= np.linspace(1, 0, fade)
out = np.tanh(out / np.abs(out).max() * 1.4) * 0.9
st = np.stack([out, np.roll(out, 300) * 0.97], 1)
with wave.open('music_hadrami.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((st * 32767).astype(np.int16).tobytes())
print('ok')
