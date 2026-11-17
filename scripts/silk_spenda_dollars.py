#!/usr/bin/env python3
"""Silk logo: falling sugar granules -> "$" glyphs (board version of
assets/logo_spenda_dollars.png).

The Spenda logo is traced gr_poly art on F.SilkS and B.SilkS (same coords on
both faces). Per face, a similarity transform px -> mm is fitted (Umeyama,
reflection allowed) from the 8 largest holes of the packet outline in a trace
of assets/logo_spenda.png to the same holes in the largest silk polygon
(residual 0.000 mm). Silk polygons whose back-projected bbox lies in the
free-fall zone (px y > 660, x < 602, same zone as scripts/logo_spenda_dollars.py)
are deleted; granules still in the packet mouth stay.

Each deleted granule becomes a solid "$" (DejaVu Serif Bold, vector-traced at
800 px) at its centroid, drawn directly in board coords so it reads the right
way: height = clip(1.7 x granule size, H_MIN, H_MAX) x U(0.85, 1.25), random
rotation +-75 deg, seed 7. Biggest first; a glyph that would come within GAP
of an earlier one shrinks (x0.85) and is dropped below H_MIN. Glyphs must sit
0.3 mm inside the main outline, as in place_logo.py, and GAP clear of
OBST: a 40 px/mm raster (origin = board bbox corner) of F/B mask openings
plus all other F/B silk, made from a --strip run (granules removed, no $).

    PYTHONPATH=/opt/data/pylibs python3 scripts/silk_spenda_dollars.py --strip
    (export F/B.Silkscreen + F/B.Mask SVGs with kicad-cli, rasterise at
    40 px/mm, union -> OBST png), then on a clean board:
    OBST=<png> PYTHONPATH=/opt/data/pylibs python3 scripts/silk_spenda_dollars.py

    PYTHONPATH=/opt/data/pylibs python3 scripts/silk_spenda_dollars.py [--dry]
"""
import sys, re, uuid
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, '/opt/data/sucralose/scripts')
from logo_fit import trace, umeyama, blocks, BOARD
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient
from shapely import affinity
from shapely.ops import unary_union
sys.path.insert(0, '/opt/data/tmp/logo')
from fit import MAIN

FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf'
ZY, ZX = 660, 602
H_MIN, H_MAX, GAP = 1.3, 2.6, 0.2   # mm; JLC silk: 0.15 mm line, ~1 mm text
src = open(BOARD).read()
keep = MAIN.buffer(-0.3)
import os
from PIL import ImageFilter
OBST = os.environ.get('OBST')
K, OX, OY = 40, 51.0, 49.0   # obstacle raster px/mm and board-bbox origin
if OBST:
    ob = np.asarray(Image.open(OBST).convert('L').filter(ImageFilter.MinFilter(2 * int(GAP * K) + 1))) < 128


def clear(g):
    if not OBST:
        return True
    x0, y0, x1, y1 = [int(v) for v in ((g.bounds[0]-OX)*K-2, (g.bounds[1]-OY)*K-2, (g.bounds[2]-OX)*K+3, (g.bounds[3]-OY)*K+3)]
    m = Image.new('1', (x1 - x0, y1 - y0), 0)
    dr = ImageDraw.Draw(m)
    for part in (g.geoms if hasattr(g, 'geoms') else [g]):
        dr.polygon([((x-OX)*K-x0, (y-OY)*K-y0) for x, y in part.exterior.coords], fill=1)
    return not (np.asarray(m) & ob[y0:y1, x0:x1]).any()

# unit "$": traced once at 800 px, normalised to height 1, centred on its bbox
f = ImageFont.truetype(FONT, 800)
l, t, r, b = f.getbbox('$')
im = Image.new('L', (r - l + 40, b - t + 40), 255)
ImageDraw.Draw(im).text((20 - l, 20 - t), '$', font=f, fill=0)
im.save('/opt/data/cache/scratch/dollar_800.png')
D = unary_union(trace('/opt/data/cache/scratch/dollar_800.png', 128))
x0, y0, x1, y1 = D.bounds
D = affinity.scale(affinity.translate(D, -(x0 + x1) / 2, -(y0 + y1) / 2), 1 / (y1 - y0), 1 / (y1 - y0), origin=(0, 0))

holes = lambda q: sorted((Polygon(h) for h in q.interiors), key=lambda h: -h.area)[:8]
ref = holes(max(trace('/opt/data/sucralose/assets/logo_spenda.png'), key=lambda q: q.area))


def ring_with_holes(g):
    g = orient(g, sign=1.0)
    ring = list(g.exterior.coords)[:-1]
    for hc in sorted((list(h.coords)[:-1] for h in g.interiors), key=lambda h: -Polygon(h).area):
        _, ri, hi = min(((rx-hx)**2 + (ry-hy)**2, ri, hi) for hi, (hx, hy) in enumerate(hc) for ri, (rx, ry) in enumerate(ring))
        hc = hc[hi:] + hc[:hi]
        ring = ring[:ri+1] + hc + [hc[0]] + ring[ri:]
    return ring


cuts, adds, report = [], [], []
for L in ('F.SilkS', 'B.SilkS'):
    blk = [(s, e, Polygon([tuple(map(float, m)) for m in re.findall(r'\(xy ([-\d.]+) ([-\d.]+)\)', b)]).buffer(0))
           for s, e, b in blocks(src, 'gr_poly') if '"%s"' % L in b]
    big = holes(max(blk, key=lambda x: x[2].area)[2])
    a = np.array([q.centroid.coords[0] for q in ref]); b = np.array([q.centroid.coords[0] for q in big])
    fits = [umeyama(a, b, r) for r in (False, True)]
    res = [np.abs((s * (R @ a.T)).T + T - b).max() for s, R, T in fits]
    s, R, T = fits[int(np.argmin(res))]
    assert min(res) < 0.05, res
    inv = lambda p: np.linalg.solve(s * R, np.asarray(p) - T)
    gran = []
    for st, en, q in blk:
        c = np.array([inv(p) for p in q.exterior.coords])
        if c[:, 1].min() > ZY and c[:, 0].max() < ZX and q.area < 3:
            cuts.append((st, en))
            x0_, y0_, x1_, y1_ = q.bounds
            gran.append((q.centroid.x, q.centroid.y, max(x1_ - x0_, y1_ - y0_)))
    rng = np.random.default_rng(7)
    placed, hs = [], []
    for cx, cy, d in sorted(gran, key=lambda g: -g[2]):
        h = float(np.clip(d * 1.7, H_MIN, H_MAX) * rng.uniform(0.85, 1.25))
        ang = rng.uniform(-75, 75)
        ok = False
        while h >= H_MIN:
            g = affinity.translate(affinity.rotate(affinity.scale(D, h, h, origin=(0, 0)), ang, origin=(0, 0)), cx, cy)
            if keep.contains(g) and not any(g.distance(p) < GAP for p in placed) and clear(g):
                ok = True
                break
            h *= 0.85
        if ok:
            placed.append(g); hs.append(h)
    for g in ([] if '--strip' in sys.argv else placed):
        for part in (g.geoms if hasattr(g, 'geoms') else [g]):
            pts = ' '.join('(xy %.4f %.4f)' % p for p in ring_with_holes(part))
            adds.append('\t(gr_poly\n\t\t(pts %s)\n\t\t(stroke (width 0) (type solid))\n\t\t(fill yes)\n\t\t(layer "%s")\n\t\t(uuid "%s")\n\t)\n' % (pts, L, uuid.uuid4()))
    report.append(f'{L}: fit {"mirror" if np.linalg.det(R) < 0 else "direct"} resid {min(res):.3f} mm; '
                  f'granules removed {len(gran)}; $ placed {len(placed)}, height {min(hs):.2f}-{max(hs):.2f} mm')

print('\n'.join(report))
if '--dry' not in sys.argv:
    out = src
    for st, en in sorted(cuts, reverse=True):
        out = out[:st] + out[en:]
    out = re.sub(r'\n\t\n', '\n', out)
    pos = out.find('\n\t(gr_line') + 1
    out = out[:pos] + ''.join(adds) + out[pos:]
    open(BOARD, 'w').write(out)
    print('wrote', BOARD)
