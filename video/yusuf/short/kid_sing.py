"""Make the ABC song SUNG in a little-boy voice (free-plan friendly).

Input:  jess.mp3      - ElevenLabs Voice Changer output (original song re-sung by a built-in voice; same timing)
        vocals.mp3    - ElevenLabs Audio Isolation of the original song (the child singer's melody)
Method: WORLD vocoder. Keep the converted voice's timbre and words, replace its pitch contour with the
        original child melody (exact notes), and warp the spectral envelope up a little (shorter vocal tract
        -> child-like, not chipmunk). Writes kid_sung.wav in WORKDIR.

Usage:  python3 kid_sing.py WORKDIR [formant_ratio]
"""
import os, sys
import numpy as np, librosa, pyworld as pw, soundfile as sf

WD = sys.argv[1]; FR = float(sys.argv[2]) if len(sys.argv) > 2 else 1.14
SR = 44100; HOP = 5.0
x, _ = librosa.load(os.path.join(WD, 'jess.mp3'), sr=SR, mono=True)
o, _ = librosa.load(os.path.join(WD, 'vocals.mp3'), sr=SR, mono=True)
n = min(len(x), len(o)); x, o = x[:n].astype(np.float64), o[:n].astype(np.float64)

f0x, t = pw.harvest(x, SR, f0_floor=90, f0_ceil=800, frame_period=HOP); f0x = pw.stonemask(x, f0x, t, SR)
f0o, to = pw.harvest(o, SR, f0_floor=90, f0_ceil=800, frame_period=HOP); f0o = pw.stonemask(o, f0o, to, SR)
sp = pw.cheaptrick(x, f0x, t, SR); ap = pw.d4c(x, f0x, t, SR)
m = min(len(f0x), len(f0o)); f0x, f0o, sp, ap = f0x[:m], f0o[:m], sp[:m], ap[:m]

# target pitch: the child's melody where it is voiced; elsewhere the converted contour moved up by the median ratio
vo, vx = f0o > 0, f0x > 0
ratio = np.median(f0o[vo & vx] / f0x[vo & vx]) if np.any(vo & vx) else 1.6
f0 = np.where(vx, np.where(vo, f0o, f0x * ratio), 0.0)
# smooth jumps a little (5 frames) on voiced runs
k = 5; sm = np.convolve(np.where(f0 > 0, np.log(np.maximum(f0, 1)), 0), np.ones(k) / k, 'same')
cnt = np.convolve((f0 > 0).astype(float), np.ones(k) / k, 'same')
f0 = np.where(f0 > 0, np.exp(sm / np.maximum(cnt, 1e-6)), 0.0)

# formant warp: spectral envelope stretched upward by FR
bins = sp.shape[1]; src = np.arange(bins) / FR
sp_w = np.stack([np.interp(src, np.arange(bins), np.log(fr)) for fr in sp]); sp_w = np.exp(sp_w)
ap_w = np.stack([np.interp(src, np.arange(bins), a) for a in ap])

y = pw.synthesize(f0, sp_w, ap_w, SR, HOP)
y = y / (np.abs(y).max() + 1e-9) * 0.9
sf.write(os.path.join(WD, 'kid_sung.wav'), y, SR)
print('median F0 converted', int(np.median(f0x[vx])), '-> sung', int(np.median(f0[f0 > 0])), 'Hz; formant x', FR)
