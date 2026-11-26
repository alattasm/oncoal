"""Build the Short's audio with the toddler voice: ElevenLabs eleven_v4 line clips (kid/NN.mp3) are trimmed and
time-fitted (pitch kept) into each lyric slot of the original song, then mixed over the beat-aligned ElevenLabs
background loop (bgm2.mp3, C major ~89 BPM). Writes mix.wav next to this script.

Usage: python3 kid_mix.py WORKDIR   (WORKDIR holds kid/, kid/lines.json, bgm2.mp3, instrumental.wav)
"""
import json, os, sys
import numpy as np, librosa, soundfile as sf

SR = 44100
WD = sys.argv[1]; HERE = os.path.dirname(os.path.abspath(__file__))
lines = json.load(open(os.path.join(WD, 'kid', 'lines.json')))
DUR = 30.6
n = int(DUR * SR)

# ---- vocal track
voc = np.zeros(n); fits = []; prev_end = 0.0
for i, (s, e, txt) in enumerate(lines):
    y, _ = librosa.load(os.path.join(WD, 'kid', f'{i:02d}.mp3'), sr=SR, mono=True)
    y, _ = librosa.effects.trim(y, top_db=35)
    # squeeze long internal pauses to 80 ms
    iv = librosa.effects.split(y, top_db=35); gap = np.zeros(int(0.08 * SR))
    y = np.concatenate(sum([[y[p:q], gap] for p, q in iv], [])[:-1]) if len(iv) > 1 else y
    slot = (lines[i + 1][0] if i + 1 < len(lines) else DUR - 0.3) - s - 0.05
    d = len(y) / SR
    rate = min(max(d / slot, 1.18), 1.5)      # consistent quick toddler pace, pitch preserved
    y = librosa.effects.time_stretch(y, rate=rate)
    y = y / (np.abs(y).max() + 1e-9)
    start = max(s, prev_end + 0.06)          # never overlap the previous line; catch up in roomier slots
    a = int(start * SR); b = min(a + len(y), n); prev_end = start + len(y) / SR
    fade = min(int(0.02 * SR), len(y) // 4)
    y[:fade] *= np.linspace(0, 1, fade); y[-fade:] *= np.linspace(1, 0, fade)
    voc[a:b] += y[:b - a]
    fits.append((i, round(rate, 2), round(start - s, 2)))
print('line, stretch, delay_s:', fits)
sf.write(os.path.join(WD, 'kid_vocal.wav'), voc, SR)

# ---- background loop, beat aligned to the song
bg, _ = librosa.load(os.path.join(WD, 'bgm2.mp3'), sr=SR, mono=False)
y22 = librosa.load(os.path.join(WD, 'instrumental.wav'), sr=22050)[0]
_, sb = librosa.beat.beat_track(y=y22, sr=22050); sbt = librosa.frames_to_time(sb, sr=22050)
_, bb = librosa.beat.beat_track(y=librosa.to_mono(bg), sr=SR); bbt = librosa.frames_to_time(bb, sr=SR)
per_s, per_b = np.median(np.diff(sbt)), np.median(np.diff(bbt)); rate = per_b / per_s
bg = np.stack([librosa.effects.time_stretch(bg[c], rate=rate) for c in range(2)]); bbt = bbt / rate
b0 = bbt[1]; nb = int((bg.shape[1] / SR - b0 - 0.3) / per_s) // 4 * 4
seg = bg[:, int(b0 * SR):int((b0 + nb * per_s) * SR)]; xf = int(0.04 * SR); fade = np.linspace(0, 1, xf)
out = np.zeros((2, n + seg.shape[1])); pos = int((sbt[0] % (4 * per_s)) * SR) - seg.shape[1]
while pos < out.shape[1]:
    s_ = seg.copy(); s_[:, :xf] *= fade; s_[:, -xf:] *= fade[::-1]
    a, b = max(pos, 0), min(pos + s_.shape[1], out.shape[1]); out[:, a:b] += s_[:, a - pos:b - pos]; pos += s_.shape[1] - xf
bgl = out[:, :n]; env = np.ones(n); env[:int(0.3 * SR)] = np.linspace(0, 1, int(0.3 * SR)); env[-int(1.2 * SR):] = np.linspace(1, 0, int(1.2 * SR))
bgl = bgl * env / (np.abs(bgl).max() + 1e-9)

# ---- mix: duck music under the voice
v = np.tanh(voc * 1.4) / np.tanh(1.4)
e = np.convolve(np.abs(v), np.ones(int(0.1 * SR)) / int(0.1 * SR), 'same'); duck = 1 - 0.35 * np.clip(e / (e.max() * 0.25 + 1e-9), 0, 1)
mix = np.stack([v, v]) * 0.85 + bgl * 0.45 * duck
mix = mix / np.abs(mix).max() * 0.95
sf.write(os.path.join(HERE, 'mix.wav'), mix.T, SR)
print('mix.wav', round(n / SR, 2), 's')
