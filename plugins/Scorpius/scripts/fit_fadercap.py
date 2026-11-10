"""Measures the parallels' fader cap of the reference (at 200 %): a measuring tool, it writes no shipped file.

    python fit_fadercap.py [reference.png]      (default: reference/scorpius/ui200_idle.png, the sub fader at level 0)

It prints the geometry and a few greys as tokens; the cap's size is what the editor uses (Source/ui/Controls.h, where
the suite's own cap is drawn; an earlier drawing of ours shaded it from these greys); its tables are never copied
into the source. The four caps of the reference are the same image. The model it measures with, in the
capture's pixels (2 per design px), supersampled 4 x 4 per pixel so edges are covered as they are rendered:
  - a rounded rectangle (left, top, right, bottom, corner radius) on black;
  - inside its edge, rings one pixel wide (thickness fitted), each a piecewise-linear table over the angle around it;
  - the face: a grey that depends only on the angle around the cap's centre, period 180 degrees (spun metal), a
    piecewise-linear table; the pixel ring around the groove has a table of its own (it is a little darker);
  - the groove: a rounded bar, one grey on its edge ring and one inside.
The greys are linear in the samples, so they are solved by least squares (with a little smoothing on the tables, which
some angles hardly reach); the geometry is fitted around that with Nelder-Mead. The report gives the sizes in design
px, the rim's grey where it faces up, right, down and left, the face's darkest and lightest grey and the angle of the
darkest, and the groove's greys.
"""
import os
import sys
import numpy as np
from PIL import Image
from scipy.optimize import minimize

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'reference', 'scorpius', 'ui200_idle.png')
X0, Y0 = 1228, 440                                   # crop around the sub fader's cap (capture pixels)
c = np.asarray(Image.open(SRC).convert('L')).astype(float)[Y0:Y0 + 70, X0:X0 + 92]
H, W = c.shape
SS, RINGS, RSTEPS, STEPS = 4, 4, 96, 48
off = (np.arange(SS) + 0.5) / SS
jj, ii = np.meshgrid(np.arange(W), np.arange(H))
px = jj[:, :, None] + np.tile(off, SS)[None, None, :]
py = ii[:, :, None] + np.repeat(off, SS)[None, None, :]
mask = np.zeros_like(c, bool)
mask[12:62, 2:88] = True                             # the cap and a margin of black (not the track above it)


def inside(x, y, l, t, r, b, R):
    """distance inside a rounded rectangle (negative outside)"""
    qx = np.abs(x - (l + r) / 2) - ((r - l) / 2 - R)
    qy = np.abs(y - (t + b) / 2) - ((b - t) / 2 - R)
    return R - np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) - np.minimum(np.maximum(qx, qy), 0)


def hats(u, steps):
    for q in range(steps):
        yield np.maximum(0, 1 - np.minimum(np.abs(u - q), steps - np.abs(u - q)))


def basis(g):
    l, t, r, b, R, th, gl, gr, gt, gb, gR = g
    cx, cy = (l + r) / 2, (t + b) / 2
    d = inside(px, py, l, t, r, b, R)
    dg = inside(px, py, gl, gt, gr, gb, gR)
    cap, groove = d > 0, dg > 0
    halo = cap & ~groove & (dg > -th)
    cols = [(~cap).mean(-1), (cap & groove & (dg < th)).mean(-1), (cap & groove & (dg >= th)).mean(-1)]
    phi = (np.arctan2((px - cx) / ((r - l) / 2), -(py - cy) / ((b - t) / 2)) % (2 * np.pi)) / (2 * np.pi) * RSTEPS
    ring = np.floor(d / th).astype(int)
    for k in range(RINGS):
        m = cap & ~groove & (ring == k)
        cols += [(m * w).mean(-1) for w in hats(phi, RSTEPS)]
    u = (np.arctan2(px - cx, -(py - cy)) % np.pi) / np.pi * STEPS
    for region in (cap & ~groove & (ring >= RINGS) & ~halo, cap & ~groove & (ring >= RINGS) & halo):
        cols += [(region * w).mean(-1) for w in hats(u, STEPS)]
    return np.stack([x[mask] for x in cols], 1)


def solve(A, v, smooth=2.0):
    """least squares with a second-difference penalty on the angle tables (some angles are hardly reached)"""
    n = A.shape[1]
    rows = []
    for base, steps, w in [(3 + k * RSTEPS, RSTEPS, smooth * 0.25) for k in range(RINGS)] + [(n - 2 * STEPS, STEPS, smooth), (n - STEPS, STEPS, smooth)]:
        for q in range(steps):
            row = np.zeros(n)
            row[base + (q - 1) % steps] += w; row[base + q] -= 2 * w; row[base + (q + 1) % steps] += w
            rows.append(row)
    Aa = np.vstack([A, np.array(rows)])
    va = np.concatenate([v, np.zeros(len(rows))])
    return np.linalg.lstsq(Aa, va, rcond=None)[0]


def error(g):
    A = basis(g)
    co = solve(A, c[mask])
    return ((c[mask] - A @ co) ** 2).mean()


g0 = [6.83, 12.0, 81.0, 58.0, 4.0, 1.0, 11.6, 75.4, 33.0, 37.0, 1.9]      # l t r b R ring | groove l r t b R
fit = minimize(error, g0, method='Nelder-Mead', options=dict(maxiter=3000, xatol=1e-3, fatol=1e-3))
g = fit.x
A = basis(g)
co = solve(A, c[mask])
rms = np.sqrt(((c[mask] - A @ co) ** 2).mean())
inner = mask & (c > 30)
print('geometry', np.round(g, 3).tolist(), 'rms %.2f' % rms)

l, t, r, b, R, th, gl, gr, gt, gb, gR = g
cx, cy = (l + r) / 2, (t + b) / 2
rim = np.array(co[3:3 + RINGS * RSTEPS]).reshape(RINGS, RSTEPS)
face = co[3 + RINGS * RSTEPS:3 + RINGS * RSTEPS + STEPS]
halo = co[3 + RINGS * RSTEPS + STEPS:]
steps = np.arange(STEPS) * 180.0 / STEPS
print('tokens (design px, greys 0 ... 255):')
print('  halfW %.2f  halfH %.2f  corner %.2f  ring %.2f' % ((r - l) / 4, (b - t) / 4, R / 2, th / 2))
print('  groove halfW %.2f  halfH %.2f  corner %.2f  centre (%.2f, %.2f)  core %.0f  edge %.0f'
      % ((gr - gl) / 4, (gb - gt) / 4, gR / 2, ((gl + gr) / 2 - cx) / 2, ((gt + gb) / 2 - cy) / 2, co[2], co[1]))
for k in range(RINGS):
    q = RSTEPS // 4
    print('  rim ring %d: up %.0f  right %.0f  down %.0f  left %.0f' % (k, rim[k][0], rim[k][q], rim[k][2 * q], rim[k][3 * q]))
print('  face: darkest %.0f at %.0f deg, lightest %.0f at %.0f deg (clockwise from up); by the groove %.2f of it'
      % (face.min(), steps[face.argmin()], face.max(), steps[face.argmax()], halo.mean() / face.mean()))
