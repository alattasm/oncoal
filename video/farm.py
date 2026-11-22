"""OnCoal farm-to-table reel (1080x1920, 30 fps) from the owner's own footage.
Only on-screen text: the title "مطعم Oncoal".

Usage:  python3 farm.py <uploads dir>   -> oncoal_farm_nomusic.mp4
Then:   VIDEO=oncoal_farm_nomusic.mp4 ./mux.sh music_hadrami.wav oncoal_farm.mp4
"""
import os, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
SRC = sys.argv[1] if len(sys.argv) > 1 else 'footage'
TMP = tempfile.mkdtemp()

# (kind, file, start_or_None, duration)
SHOTS = [
    ('v', 'IMG_9935.mov', 1.8, 4.5),   # green trees (title)
    ('v', 'IMG_0225.mov', 2.0, 4.5),   # fields
    ('v', 'IMG_0219.mov', 1.0, 5.0),   # sheep
    ('i', 'IMG_0217.jpeg', None, 2.5), # sheep photo
    ('v', 'IMG_0211.mov', 0.0, 3.0),   # cows
    ('i', 'carcass.jpeg', None, 3.0),  # hanging carcass
    ('p', 'IMG_8835.jpeg', None, 4.5), # cold room rail, panned left -> right
    ('i', 'coldroom_crop.jpg', None, 3.0),  # close-up, cropped so no face is visible
    ('v', 'IMG_9794.mov', 3.0, 5.0),   # marinated meat display
    ('v', 'IMG_9959.mov', 1.0, 3.0),   # display trays (landscape)
]
END = 6.0


def run(cmd): subprocess.run(cmd, check=True)


def title_png(path, size=150):
    """The single title, Arabic + Latin, with a soft shadow."""
    f = ImageFont.truetype('fonts/Cairo.ttf', size, layout_engine=ImageFont.Layout.RAQM)
    f.set_variation_by_name('Black')
    s = 'مطعم Oncoal'
    l, t, r, b = f.getbbox(s, direction='rtl', language='ar')
    pad = 60
    txt = Image.new('RGBA', (r - l + 2 * pad, b - t + 2 * pad))
    ImageDraw.Draw(txt).text((pad - l, pad - t), s, font=f, fill=(246, 236, 222), direction='rtl', language='ar')
    out = Image.new('RGBA', txt.size)
    sh = Image.new('RGBA', txt.size, (0, 0, 0, 0)); sh.putalpha(txt.getchannel('A').point(lambda v: v * .8))
    out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)), (0, 8))
    glow = Image.new('RGBA', txt.size, (236, 146, 70, 0)); glow.putalpha(txt.getchannel('A').point(lambda v: v * .55))
    out.alpha_composite(glow.filter(ImageFilter.GaussianBlur(28)))
    out.alpha_composite(txt)
    if out.width > W - 80:
        out = out.resize((W - 80, int(out.height * (W - 80) / out.width)), Image.LANCZOS)
    out.save(path)


FILL = f'scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1'
GRADE = 'eq=contrast=1.06:saturation=1.12,unsharp=5:5:0.6'


def shot(i, kind, name, ss, dur):
    out = f'{TMP}/s{i:02d}.mp4'
    src = os.path.join(SRC, name)
    fade = f'fade=t=in:st=0:d=0.25,fade=t=out:st={dur - 0.25}:d=0.25'
    if kind == 'v':
        inp = ['-ss', str(ss), '-t', str(dur), '-i', src]
        vf = f'{FILL},fps={FPS},{GRADE},{fade}'
    elif kind == 'p':  # wide photo: slow horizontal pan
        inp = ['-loop', '1', '-framerate', str(FPS), '-t', str(dur), '-i', src]
        vf = (f"scale=-2:{H},crop={W}:{H}:x='(iw-ow)*min(t/{dur},1)':y=0,setsar=1,{GRADE},{fade}")
    else:  # still photo: slow Ken Burns push-in
        n = int(dur * FPS)
        inp = ['-loop', '1', '-t', str(dur), '-i', src]
        vf = (f'scale={W * 2}:{H * 2}:force_original_aspect_ratio=increase,crop={W * 2}:{H * 2},'
              f"zoompan=z='1+0.08*on/{n}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d={n}:s={W}x{H}:fps={FPS},"
              f'setsar=1,{GRADE},{fade}')
    if i == 0:  # title fades in over the opening shot
        inp += ['-loop', '1', '-i', f'{TMP}/title.png']
        fc = (f'[0:v]{vf}[b];[1:v]format=rgba,fade=t=in:st=0.8:d=0.8:alpha=1,'
              f'fade=t=out:st={dur - 1.2}:d=0.7:alpha=1[t];[b][t]overlay=(W-w)/2:H*0.72:shortest=1')
        run(['ffmpeg', '-y', '-v', 'error', *inp, '-filter_complex', fc, '-an', '-t', str(dur),
             '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', out])
    else:
        run(['ffmpeg', '-y', '-v', 'error', *inp, '-vf', vf, '-an', '-t', str(dur),
             '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', out])
    return out


def end_card(i):
    """Blurred, darkened meat footage behind the title."""
    out = f'{TMP}/s{i:02d}.mp4'
    src = os.path.join(SRC, 'IMG_9794.mov')
    fc = (f'[0:v]{FILL},fps={FPS},gblur=sigma=28,eq=brightness=-0.28:saturation=1.1,'
          f'fade=t=in:st=0:d=0.6,fade=t=out:st={END - 0.8}:d=0.8[b];'
          f'[1:v]format=rgba,fade=t=in:st=0.5:d=0.8:alpha=1[t];'
          f"[b][t]overlay=(W-w)/2:(H-h)/2:shortest=1")
    run(['ffmpeg', '-y', '-v', 'error', '-ss', '10', '-t', str(END), '-i', src,
         '-loop', '1', '-i', f'{TMP}/title_big.png', '-filter_complex', fc, '-an', '-t', str(END),
         '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', out])
    return out


def prep():
    """Cold-room close-up: crop away the selfie (face), then make it bright, fresh and glossy."""
    from PIL import ImageEnhance, ImageOps, ImageChops
    im = Image.open(os.path.join(SRC, 'IMG_0261.jpeg')).convert('RGB').crop((1000, 0, 1936, 1640))
    im = ImageOps.autocontrast(im, cutoff=0.5)
    im = im.point(lambda v: int(255 * (v / 255) ** 0.5))           # lift shadows/mids (brighter)
    im = ImageEnhance.Contrast(im).enhance(1.0)
    im = ImageEnhance.Brightness(im).enhance(1.12)
    im = ImageEnhance.Color(im).enhance(1.45)                       # fresh red meat
    r, g, b = im.split()                                            # cool the grey cast slightly toward clean white
    im = Image.merge('RGB', (r, g.point(lambda v: min(255, v * 1.02)), b.point(lambda v: min(255, v * 1.04))))
    im = im.filter(ImageFilter.UnsharpMask(4, 110, 2))
    # glossy sheen: soft bloom from the highlights
    hi = im.point(lambda v: max(0, v - 170) * 3).filter(ImageFilter.GaussianBlur(18))
    im = ImageChops.screen(im, ImageEnhance.Brightness(hi).enhance(0.6))
    im.save(os.path.join(SRC, 'coldroom_crop.jpg'), quality=95)


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    prep()
    title_png(f'{TMP}/title.png', 130)
    title_png(f'{TMP}/title_big.png', 170)
    parts = [shot(i, *s) for i, s in enumerate(SHOTS)] + [end_card(len(SHOTS))]
    with open(f'{TMP}/list.txt', 'w') as fh:
        fh.writelines(f"file '{p}'\n" for p in parts)
    run(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', f'{TMP}/list.txt',
         '-c', 'copy', '-movflags', '+faststart', 'oncoal_farm_nomusic.mp4'])
    print('total', sum(s[3] for s in SHOTS) + END, 's -> oncoal_farm_nomusic.mp4')
