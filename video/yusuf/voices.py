"""Synthesize all vocal lines with a warm natural lead voice (Lessac) into vo/ and a soft second voice (Amy) into vo2/.
No pitch shifting is applied later - natural, friendly voices."""
import os, wave
from piper import PiperVoice
from piper.config import SynthesisConfig

LINES = {
    'intro1': 'Bubbles, bubbles! Pop, pop, pop!', 'intro2': "Baby Yusuf! Let's play!", 'letsgo': "Let's go!",
    'sky': 'Floating in the sky!', 'high': 'Flying way up high!', 'pop1': 'Pop!', 'next': 'What color is next?',
    'hey': 'Hey!', 'woohoo': 'Woo hoo!', 'rainbow': 'Rainbow bubbles everywhere!', 'clap': 'Clap, clap!',
    'yay': 'Yay! Clap your hands!', 'yay2': 'Yaaay!', 'bye': 'Bye bye, bubbles! See you soon!',
}
for c in ['red', 'yellow', 'blue', 'green', 'purple']:
    LINES[c] = c.capitalize() + '!'
    LINES[f'{c}_b'] = f'{c.capitalize()} bubbles, {c} bubbles!'

for model, out, ls in (('en_US-lessac-medium', 'vo', 0.9), ('en_US-amy-medium', 'vo2', 0.9)):
    v = PiperVoice.load(f'voice/{model}.onnx'); os.makedirs(out, exist_ok=True)
    cfg = SynthesisConfig(length_scale=ls, noise_scale=0.6, noise_w_scale=0.8)
    for k, s in LINES.items():
        with wave.open(f'{out}/{k}.wav', 'wb') as w:
            v.synthesize_wav(s, w, syn_config=cfg)
    print(model, 'done')
