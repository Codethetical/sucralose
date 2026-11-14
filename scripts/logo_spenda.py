#!/usr/bin/env python3
"""assets/logo_splenda.jpg -> assets/logo_spenda.png ("Spenda", no (R) mark).

Same edit as the board silk (scripts/silk_spenda.py): delete the 'l' and the
(R), slide "enda" back along the S->a axis until the p-e gap equals the
existing letter gap (min of p-l and l-e), "Sp" fixed. Letters are the dark
connected components of the wordmark; erased areas are refilled from the
surrounding packet shading (normalised Gaussian convolution).

    /opt/data/venvs/cad/bin/python scripts/logo_spenda.py
"""
import numpy as np
from PIL import Image
from scipy import ndimage

SRC, DST = 'assets/logo_splenda.jpg', 'assets/logo_spenda.png'
g = np.asarray(Image.open(SRC).convert('L')).astype(float)
dark = g < 128
lab, n = ndimage.label(dark)
objs = ndimage.find_objects(lab)


def comp_at(x0, x1, y0, y1, min_px):
    """Largest component whose bbox lies inside the given window."""
    best = None
    for i, s in enumerate(objs):
        if x0 <= s[1].start and s[1].stop <= x1 and y0 <= s[0].start and s[0].stop <= y1:
            c = int((lab[s] == i + 1).sum())
            if c >= min_px and (best is None or c > best[1]):
                best = (i + 1, c)
    return best[0]


# windows from the component survey of the 1254x1254 original
S = comp_at(430, 570, 320, 530, 1000)
P = comp_at(540, 630, 360, 510, 1000)
L = comp_at(595, 665, 295, 435, 1000)
E = comp_at(645, 710, 325, 420, 1000)
N = comp_at(685, 780, 300, 405, 1000)
D = comp_at(755, 840, 225, 375, 1000)
A = comp_at(820, 900, 240, 345, 1000)
SW = comp_at(600, 895, 325, 475, 3000)
R = [i + 1 for i, s in enumerate(objs) if 895 <= s[1].start and s[1].stop <= 920 and 295 <= s[0].start and s[0].stop <= 318]
assert len({S, P, L, E, N, D, A, SW}) == 8 and R, (S, P, L, E, N, D, A, SW, R)

mask = lambda ids: np.isin(lab, ids)
grow = lambda m, r=3: ndimage.binary_dilation(m, iterations=r)
dist_between = lambda m1, m2: ndimage.distance_transform_edt(~m1)[m2].min()

target = min(dist_between(mask([P]), mask([L])), dist_between(mask([L]), mask([E])))
c = lambda i: np.array(ndimage.center_of_mass(lab == i))  # (y, x)
u = c(A) - c(S); u /= np.linalg.norm(u)

TAIL = [E, N, D, A]
tail_m = mask(TAIL)
lo, hi = 0.0, 200.0
for _ in range(40):  # bisection on the slide distance (px)
    mid = (lo + hi) / 2
    sh = ndimage.shift(tail_m.astype(float), -u * mid, order=1) > 0.5
    lo, hi = (mid, hi) if dist_between(mask([P]), sh) > target else (lo, mid)
shift = -u * lo

# background estimate: blur of the pixels that are not ink or ink fringe
ink = grow(dark, 3)
w = ndimage.gaussian_filter((~ink).astype(float), 10)
bgv = ndimage.gaussian_filter(np.where(ink, 0, g), 10) / np.maximum(w, 1e-6)

# paper grain: a smooth fill alone shows as flat ghost shapes, so add
# synthetic grain matched to the packet's own high-frequency statistics
# (borrowing real texture drags in the packet's inner rule line).
resid = g - ndimage.gaussian_filter(g, 2)
erase = grow(mask([L] + TAIL + R), 4)
ring = grow(erase, 12) & ~erase & ~grow(g < 225, 2)
rng = np.random.default_rng(0)
noise = ndimage.gaussian_filter(rng.standard_normal(g.shape), 0.7)
tex = noise / noise.std() * resid[ring].std() * 0.6
# feathered blend so the erased shapes have no hard edge
alpha = np.clip(ndimage.gaussian_filter(erase.astype(float), 2.5) * 1.6, 0, 1)
alpha[grow(mask([L] + TAIL + R), 1)] = 1.0
out = alpha * (bgv + tex) + (1 - alpha) * g
layer = np.where(grow(tail_m, 1), g, 255.0)
moved = ndimage.shift(layer, shift, order=1, cval=255.0)
out = np.minimum(out, moved)

new_tail = ndimage.shift(tail_m.astype(float), shift, order=1) > 0.5
print(f'slide {lo:.1f} px; p-e {dist_between(mask([P]), new_tail):.1f} px (target {target:.1f}); '
      f'enda-to-swoosh {dist_between(mask([SW]), new_tail):.1f} px (was {dist_between(mask([SW]), tail_m):.1f})')
Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(DST, optimize=True)
print('wrote', DST)
