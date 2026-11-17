import re, sys, json, numpy as np
from PIL import Image
import potrace
from shapely.geometry import Polygon
sys.path.insert(0, '/opt/data/tmp/be'); from geo import blocks

BOARD = '/opt/data/sucralose/pcb/sucralose.kicad_pcb'
t = open(BOARD).read()

def silk(layer):
    out = []
    for s, e, b in blocks(t, 'gr_poly'):
        if '"%s"' % layer in b:
            p = [tuple(map(float, m)) for m in re.findall(r'\(xy ([-\d.]+) ([-\d.]+)\)', b)]
            out.append(Polygon(p).buffer(0))
    return out

def trace(path, thr=170):
    a = np.array(Image.open(path).convert('L'))
    bits = a < thr
    bm = potrace.Bitmap(~bits)
    pl = bm.trace(turdsize=2, alphamax=1.0, opticurve=True, opttolerance=0.2)
    polys = []
    for c in pl:
        pts = [(c.start_point.x, c.start_point.y)]
        for sg in c:
            if sg.is_corner:
                pts += [(sg.c.x, sg.c.y), (sg.end_point.x, sg.end_point.y)]
            else:
                p0 = pts[-1]
                for k in range(1, 7):
                    u = k / 6
                    pts.append(tuple((1-u)**3*p0[i] + 3*(1-u)**2*u*(sg.c1.x, sg.c1.y)[i] + 3*(1-u)*u**2*(sg.c2.x, sg.c2.y)[i] + u**3*(sg.end_point.x, sg.end_point.y)[i] for i in range(2)))
        if len(pts) >= 3:
            polys.append(Polygon(pts).buffer(0))
    polys = [q for q in polys if not q.is_empty]
    polys.sort(key=lambda q: -q.area)
    shape = polys[0]
    for q in polys[1:]:
        shape = shape.symmetric_difference(q)
    shape = shape.buffer(0)
    return list(shape.geoms) if hasattr(shape, 'geoms') else [shape]

def umeyama(src, dst, reflect):
    src, dst = np.asarray(src), np.asarray(dst)
    ms, md = src.mean(0), dst.mean(0)
    S, D = src - ms, dst - md
    U, sig, Vt = np.linalg.svd(D.T @ S / len(src))
    d = np.eye(2)
    if reflect: d[1, 1] = -1 if np.linalg.det(U @ Vt) > 0 else 1
    else: d[1, 1] = 1 if np.linalg.det(U @ Vt) > 0 else -1
    R = U @ d @ Vt
    s = (sig * np.diag(d)).sum() / (S ** 2).sum() * len(src)
    T = md - s * R @ ms
    return s, R, T

if __name__ == '__main__':
    px = trace('/opt/data/sucralose/assets/logo_spenda.png')
    px.sort(key=lambda q: -q.area)
    print('px comps', len(px), [round(q.area) for q in px[:12]])
    for L in ('F.SilkS', 'B.SilkS'):
        bd = silk(L); bd.sort(key=lambda q: -q.area)
        print(L, len(bd), [round(q.area, 2) for q in bd[:12]])
