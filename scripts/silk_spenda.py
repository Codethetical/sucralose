#!/usr/bin/env python3
"""Silk wordmark "Splenda" -> "Spenda" on both faces.

The wordmark is traced gr_poly art (scripts/silk_trace_logo.py), one polygon
per letter. Per face, in gr_poly file order: S=129 p=127 l=112 e=119 n=118
d=124 a=123, (R) mark = 93 + 106, swoosh = 102. Deletes the 'l', then closes
the gap by sliding "enda(R)" back along the S->a axis. "Sp" stays put: the
swoosh starts under the p, and moving p forward lands it on the swoosh
(half-and-half closing measured p-to-swoosh 0.000 mm). Target p-e spacing
= the existing letter spacing (p-l and l-e minimum distance, 0.51 mm).

    python3 scripts/silk_spenda.py [--dry]
"""
import sys, re, math
from shapely.geometry import Polygon
from shapely.affinity import translate

BOARD = '/opt/data/sucralose/pcb/sucralose.kicad_pcb'
L_IDX, HEAD, TAIL = 112, (129, 127), (119, 118, 124, 123, 93, 106)
S_IDX, A_IDX, P_IDX, E_IDX, SWOOSH = 129, 123, 127, 119, 102
src = open(BOARD).read()


class Blk:
    """One top-level gr_poly: m[1] = pts body, m[2] = face, start(1)/end(1) span the pts body."""
    def __init__(self, st, en, face, ps, pe):
        self._s, self._e, self.face, self._ps, self._pe = st, en, face, ps, pe
    def __getitem__(self, k): return {1: src[self._ps:self._pe], 2: self.face}[k]
    def start(self, g=0): return self._ps if g == 1 else self._s
    def end(self, g=0): return self._pe if g == 1 else self._e


def gr_polys():
    i = 0
    while True:
        st = src.find('\n\t(gr_poly\n', i)
        if st < 0: return
        st += 1; en = src.find('\n\t)\n', st) + 4  # includes trailing newline
        b = src[st:en]; lm = re.search(r'\(layer "([FB])\.SilkS"\)', b)
        ps = src.find('(pts', st); pe = src.find('\n\t\t)', ps)
        if lm: yield Blk(st, en, lm[1], ps, pe)
        i = en - 1


def pts_of(body):
    return [(float(a), float(b)) for a, b in re.findall(r'\(xy ([-\d.]+) ([-\d.]+)\)', body)]


edits = []  # (start, end, replacement)
for face in 'FB':
    blks = [m for m in gr_polys() if m[2] == face]
    P = {i: Polygon(pts_of(blks[i][1])) for i in set(HEAD + TAIL + (L_IDX, SWOOSH))}
    s, a = P[S_IDX].centroid, P[A_IDX].centroid
    ux, uy = a.x - s.x, a.y - s.y; n = math.hypot(ux, uy); ux, uy = ux / n, uy / n
    target = min(P[P_IDX].distance(P[L_IDX]), P[L_IDX].distance(P[E_IDX]))
    lo, hi = 0.0, 10.0  # total closing distance, bisection on p-e spacing
    for _ in range(60):
        mid = (lo + hi) / 2
        d = P[P_IDX].distance(translate(P[E_IDX], -ux * mid, -uy * mid))
        lo, hi = (mid, hi) if d > target else (lo, mid)
    shift = lo
    hd, tl = (0.0, 0.0), (-ux * shift, -uy * shift)
    sw = P[SWOOSH]
    print(f'{face}: delete l, close {shift:.3f} mm (enda(R) back {shift:.3f}, Sp fixed); '
          f'p-e {translate(P[P_IDX], *hd).distance(translate(P[E_IDX], *tl)):.3f} (target {target:.3f}); '
          f'min to swoosh {min(translate(P[i], *(hd if i in HEAD else tl)).distance(sw) for i in HEAD + TAIL if i not in (93, 106)):.3f}')
    for i in HEAD + TAIL:
        m = blks[i]; dx, dy = hd if i in HEAD else tl
        body = re.sub(r'\(xy ([-\d.]+) ([-\d.]+)\)',
                      lambda q: f'(xy {float(q[1]) + dx:.6f} {float(q[2]) + dy:.6f})', m[1])
        edits.append((m.start(1), m.end(1), body))
    edits.append((blks[L_IDX].start(), blks[L_IDX].end(), ''))

if '--dry' not in sys.argv:
    for st, en, rep in sorted(edits, reverse=True):
        src = src[:st] + rep + src[en:]
    open(BOARD, 'w').write(src)
    print('written')
