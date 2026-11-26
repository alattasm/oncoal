"""Prepare the full-body Yusuf sprite: cut-out -> remove brand prints (cartoon character print, clothing label,
shoe logos) by inpainting -> add a yellow star on the sweater. Writes yusuf2_clean.png."""
import math
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter

im = Image.open('yusuf2_cut.png').convert('RGBA'); a = np.array(im)
rgb = a[..., :3].astype(int); r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
H, W = r.shape; yy, xx = np.mgrid[0:H, 0:W]
blue = (b > r + 60) & (b > g + 25)
m1 = (xx > 300) & (xx < 700) & (yy > 455) & (yy < 860) & ~blue & (a[..., 3] > 100)          # print
m2 = (xx > 480) & (xx < 600) & (yy > 860) & (yy < 925) & ~blue                              # label
m3 = (yy > 1305) & (r < 90) & (g < 100) & (b > 60) & (b > r + 15) & (a[..., 3] > 100)       # shoe logos
k = np.ones((7, 7), np.uint8)
out = cv2.cvtColor(a[..., :3], cv2.COLOR_RGB2BGR)
for m, rad in ((m1, 25), (m2, 9), (m3, 7)):
    out = cv2.inpaint(out, cv2.dilate(m.astype(np.uint8) * 255, k), rad, cv2.INPAINT_TELEA)
res = Image.fromarray(np.dstack([cv2.cvtColor(out, cv2.COLOR_BGR2RGB), a[..., 3]]))

# yellow star on the chest (drawn 4x then downsampled)
SS, cx, cy, R = 4, 505, 640, 78
st = Image.new('RGBA', (W * SS, H * SS)); d = ImageDraw.Draw(st)
def pts(rad, inner=0.45, rot=-math.pi / 2, dx=0, dy=0):
    return [((cx + dx + (rad if k % 2 == 0 else rad * inner) * math.cos(rot + k * math.pi / 5)) * SS,
             (cy + dy + (rad if k % 2 == 0 else rad * inner) * math.sin(rot + k * math.pi / 5)) * SS) for k in range(10)]
d.polygon(pts(R + 5), fill=(40, 30, 70, 255))
d.polygon(pts(R), fill=(255, 205, 40, 255))
d.polygon(pts(R * 0.62, dx=-6, dy=-8), fill=(255, 228, 110, 255))
st = st.resize((W, H), Image.LANCZOS)
res.alpha_composite(st)
res.save('yusuf2_clean.png')
print('saved yusuf2_clean.png')
