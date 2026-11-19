"""Original cheerful kids' track for 'Baby Youssef in the Jungle' ep1 (46 s), plus cartoon SFX
synced to the animation timeline. C major, 120 bpm: marimba melody, pizzicato bass, ukulele-like
strums, shaker + soft kick. Writes music.wav."""
import numpy as np, wave
SR = 44100; DUR = 46.0; BPM = 120; B = 60 / BPM
rng = np.random.default_rng(3)
L = np.zeros(int(SR * (DUR + 1))); R = np.zeros_like(L)

def add(sig, t, g=1.0, pan=0.0):
    i = int(t * SR); n = min(len(sig), len(L) - i)
    if n <= 0: return
    L[i:i+n] += sig[:n] * g * (1 - pan) ; R[i:i+n] += sig[:n] * g * (1 + pan)

def env(n, a=0.005, d=0.3):
    tt = np.arange(n) / SR
    return np.clip(tt / a, 0, 1) * np.exp(-tt / d)

def mf(m): return 440 * 2 ** ((m - 69) / 12)

def marimba(m, dur=0.5):
    n = int(SR * (dur + .4)); tt = np.arange(n) / SR; f = mf(m)
    s = np.sin(2*np.pi*f*tt) + .35*np.sin(2*np.pi*f*4*tt)*np.exp(-tt/.05) + .15*np.sin(2*np.pi*f*10*tt)*np.exp(-tt/.02)
    return s * env(n, .002, .28)

def pluck(m, dur=0.4, bright=.5):
    f = mf(m); n = int(SR * (dur + .3)); p = max(2, int(SR / f))
    buf = rng.uniform(-1, 1, p); out = np.empty(n)
    for i in range(n):
        out[i] = buf[i % p]; buf[i % p] = .996 * (bright * buf[i % p] + (1 - bright) * buf[(i+1) % p])
    return out * np.clip((dur + .3 - np.arange(n)/SR) / .1, 0, 1)

def kick():
    n = int(SR * .25); tt = np.arange(n)/SR
    return np.sin(2*np.pi*(55 + 90*np.exp(-tt/.03))*tt) * np.exp(-tt/.09)
def shaker():
    n = int(SR * .06); return rng.uniform(-1, 1, n) * np.exp(-np.arange(n)/SR/.015)
def clap():
    n = int(SR * .15); s = rng.uniform(-1, 1, n) * np.exp(-np.arange(n)/SR/.04)
    return np.convolve(s, [1, -0.9], 'same')

# chord progression (4 beats each): C G Am F
CH = [(48, [60, 64, 67]), (43, [59, 62, 67]), (45, [60, 64, 69]), (41, [60, 65, 69])]
MEL = [  # (beat offset in 16-beat phrase, midi, length beats)
 (0,72,1),(1,74,.5),(1.5,76,.5),(2,79,1),(3,76,1),(4,74,1),(5,71,.5),(5.5,74,.5),(6,79,2),
 (8,76,1),(9,77,.5),(9.5,76,.5),(10,72,1),(11,69,1),(12,72,1),(13,74,.5),(13.5,76,.5),(14,72,2)]
MEL2 = [(0,79,.5),(.5,77,.5),(1,76,1),(2,74,.5),(2.5,72,.5),(3,74,1),(4,79,1),(5,83,1),(6,81,2),
 (8,84,1),(9,83,.5),(9.5,81,.5),(10,79,1),(11,77,1),(12,76,1),(13,74,1),(14,72,2)]

t0 = 0.0; beat = 0
total_beats = int((DUR - .5) / B)
for bi in range(total_beats):
    t = bi * B
    ch_root, ch = CH[(bi // 4) % 4]
    fade = 1.0 if t < 43 else max(0, 1 - (t - 43) / 3)
    # bass on 1 and 3, walk on 4
    if bi % 2 == 0: add(pluck(ch_root, .45, .3), t, .55 * fade)
    # ukulele strum on 2 and 4 (and off-beats)
    for k, d in ((0.0, 1), (0.5, -1)):
        if (bi % 2 == 1) or k == .5:
            for j, m in enumerate(ch[::d]):
                add(pluck(m, .25, .6), t + k * B + j * .012, .16 * fade, pan=.3)
    # drums
    if t >= 2.4:
        if bi % 2 == 0: add(kick(), t, .6 * fade)
        if bi % 4 == 3 and t > 6: add(clap(), t, .18 * fade)
        for k in range(4): add(shaker(), t + k * B / 4, (.05 if k % 2 else .08) * fade, pan=-.4)
    # melody: phrase of 16 beats, alternate tunes, rest during intro first 2 beats
    ph = bi % 16; tune = MEL if (bi // 16) % 2 == 0 else MEL2
    for off, m, ln in tune:
        if off >= ph and off < ph + 1 and t > 1.5:
            add(marimba(m, ln * B), t + (off - ph) * B, .32 * fade, pan=-.15)
            add(marimba(m + 12, ln * B), t + (off - ph) * B, .06 * fade, pan=.2)

# ---------- SFX synced to the animation ----------
def whoosh(d=.45):
    n = int(SR*d); x = rng.uniform(-1,1,n); tt=np.arange(n)/SR
    y = np.zeros(n); a = 0
    for i in range(n):                         # sweeping one-pole filter
        c = .02 + .25*np.sin(np.pi*tt[i]/d); a += c*(x[i]-a); y[i] = a
    return y * np.sin(np.pi*tt/d) * 3
def boing(d=.5):
    n=int(SR*d); tt=np.arange(n)/SR
    f = 180 + 220*np.exp(-tt/.12) + 25*np.sin(2*np.pi*14*tt)
    return np.sin(2*np.pi*np.cumsum(f)/SR) * np.exp(-tt/.2)
def sparkle(t):
    for i, m in enumerate([84, 88, 91, 96]): add(marimba(m, .3), t + i * .07, .22, pan=.3)
def pop():
    n=int(SR*.12); tt=np.arange(n)/SR
    return np.sin(2*np.pi*(900*np.exp(-tt/.02)+200)*tt)*np.exp(-tt/.03)
def sob(t):
    for k in range(3):
        n=int(SR*.22); tt=np.arange(n)/SR
        f=520-200*tt/.22; add(np.sin(2*np.pi*np.cumsum(f)/SR)*np.sin(np.pi*tt/.22)*.6, t+k*.32, .25, pan=.5)
def trumpet(t):  # elephant toot
    n=int(SR*.7); tt=np.arange(n)/SR; f=330+60*np.sin(np.pi*tt/.7)
    ph=2*np.pi*np.cumsum(f)/SR; s=sum(np.sin(h*ph)/h for h in range(1,9))
    add(s*np.clip(tt/.05,0,1)*np.clip((.7-tt)/.15,0,1)*.4, t, .5, pan=.4)
def cheer(t, d=1.5):
    n=int(SR*d); x=rng.uniform(-1,1,n); y=np.convolve(x,np.ones(30)/30,'same')
    add(y*np.sin(np.pi*np.arange(n)/n)*3, t, .25)

for tc in (6.0, 14.0, 22.0, 32.0, 40.0): add(whoosh(), tc - .45, .5)
sparkle(1.0); add(boing(), 2.6, .35)                   # title pops, baby springs up
add(boing(.4), 17.25, .45, pan=.3)                     # Mimo lands
sob(22.8); sob(24.6)                                    # Filo cries
for k in range(6): add(pop(), 26.5 + k * .33, .15, pan=.3)  # climbing taps
sparkle(28.6); add(pop(), 28.6, .3)                     # grabs balloon
trumpet(31.6); trumpet(33.0)                            # happy toot
cheer(32.3, 2.0); sparkle(32.6); sparkle(36.4)
sparkle(40.6)

mix = np.stack([L, R], 1)[:int(SR * DUR)]
mix /= np.abs(mix).max() / .9
fade = np.ones(len(mix)); k = int(SR * 1.0); fade[-k:] = np.linspace(1, 0, k); mix *= fade[:, None]
with wave.open('music.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype('<i2').tobytes())
print('ok', len(mix) / SR)
