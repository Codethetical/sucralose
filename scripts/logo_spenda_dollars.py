#!/usr/bin/env python3
"""assets/logo_spenda.png -> assets/logo_spenda_dollars.png (alt version).

Every free-falling granule below the packet is erased and replaced by a "$"
at the same spot: size follows the granule's size with random jitter, and the
rotation is random. Glyphs are drawn like the granules (dark ink outline,
light fill), rendered at 4x and downsampled. Granules still inside the torn
mouth are left alone. Deterministic (seed 7).

    /opt/data/venvs/cad/bin/python scripts/logo_spenda_dollars.py
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

SRC, DST = 'assets/logo_spenda.png', 'assets/logo_spenda_dollars.png'
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf'
SS = 4  # supersample

g = np.asarray(Image.open(SRC).convert('L')).astype(float)
ink = g < 235
lab, n = ndimage.label(ndimage.binary_dilation(ink, iterations=2))  # one label per granule
lab = np.where(ink, lab, 0)
objs = ndimage.find_objects(lab)
big = np.argmax([((lab[s] == i + 1).sum()) for i, s in enumerate(objs)]) + 1  # packet outline

# granules: ink components in the lower-left fall zone that are not part of the packet
gran = []
for i, s in enumerate(objs):
    if i + 1 == big:
        continue
    y0, y1, x0, x1 = s[0].start, s[0].stop, s[1].start, s[1].stop
    if y0 > 662 and x1 < 600:
        gran.append((i + 1, (y0 + y1) / 2, (x0 + x1) / 2, max(y1 - y0, x1 - x0)))

rep = np.isin(lab, [k for k, *_ in gran])
erase = ndimage.binary_dilation(rep, iterations=3) & ~ndimage.binary_dilation(ink & ~rep, iterations=1)
out = np.where(erase, 255.0, g)

rng = np.random.default_rng(7)
font_cache = {}
occupied = np.zeros_like(ink)
placed = 0
for k, cy, cx, d in sorted(gran, key=lambda t: -t[3]):  # biggest first
    if d < 6:
        continue  # specks: erase only
    h = float(np.clip(d * 1.7, 17, 46) * rng.uniform(0.8, 1.3))
    ang = rng.uniform(-75, 75)
    for _ in range(6):  # shrink until it does not touch an earlier glyph
        px = int(round(h * SS))
        f = font_cache.setdefault(px, ImageFont.truetype(FONT, px))
        sw = max(1, int(round(px * 0.06)))
        l, t, r, b = f.getbbox('$', stroke_width=sw)
        tile = Image.new('L', (r - l + 4 * sw, b - t + 4 * sw), 255)
        ImageDraw.Draw(tile).text((2 * sw - l, 2 * sw - t), '$', font=f, fill=238,
                                  stroke_width=sw, stroke_fill=60)
        tile = tile.rotate(ang, resample=Image.BICUBIC, expand=True, fillcolor=255)
        tile = tile.resize((max(1, tile.width // SS), max(1, tile.height // SS)), Image.LANCZOS)
        a = np.asarray(tile).astype(float)
        y0, x0 = int(round(cy - a.shape[0] / 2)), int(round(cx - a.shape[1] / 2))
        sl = (slice(y0, y0 + a.shape[0]), slice(x0, x0 + a.shape[1]))
        gm = a < 250
        if not (occupied[sl] & ndimage.binary_dilation(gm, iterations=2)).any() and not (out[sl] < 200)[gm].any():
            break
        h *= 0.85
    if h < 12:
        continue
    out[sl] = np.minimum(out[sl], a)
    occupied[sl] |= gm
    placed += 1

print(f'{len(gran)} granule components, {placed} replaced with $')
Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(DST, optimize=True)
print('wrote', DST)
