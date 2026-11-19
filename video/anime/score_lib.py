"""Build a scored music bed from cue segments, plus simple action 'hit' SFX."""
import numpy as np


def build_score(load, L, SR, cues, xf=1.5):
    """cues: list of (wav_path, start_s, end_s, offset_s). Returns float32 array of length L."""
    out = np.zeros(L, np.float32)
    cache = {}
    for path, a, b, off in cues:
        if path not in cache:
            m = load(path)
            cache[path] = m / (np.abs(m).max() + 1e-6)
        m = cache[path]
        n = int((b - a + xf) * SR)
        i0 = int(off * SR) % len(m)
        seg = np.resize(np.roll(m, -i0), n).astype(np.float32)
        k = int(xf * SR)
        env = np.ones(n, np.float32)
        env[:k] = np.linspace(0, 1, k)
        env[-k:] = np.linspace(1, 0, k)
        s = int(max(a - xf / 2, 0) * SR)
        e = min(s + n, L)
        out[s:e] += (seg * env)[:e - s]
    return out


def hit(SR, rng, big=True):
    n = int(SR * (1.6 if big else .8))
    tt = np.arange(n) / SR
    boom = np.sin(2 * np.pi * (45 + 80 * np.exp(-tt / .08)) * tt) * np.exp(-tt / (.5 if big else .25))
    crack = rng.standard_normal(n) * np.exp(-tt / .03) * .4
    return (boom + crack).astype(np.float32)


def riser(SR, rng, d=1.5):
    n = int(SR * d)
    tt = np.arange(n) / SR
    f = 200 + 1800 * (tt / d) ** 2
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * .3 + rng.standard_normal(n) * .3 * (tt / d)
    return (s * (tt / d) ** 1.5).astype(np.float32)
