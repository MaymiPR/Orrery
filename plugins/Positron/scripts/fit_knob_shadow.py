"""Measures the shadow the reference's plate knobs cast on the plate (reference/shots/silence.png, 200 %): a smooth
model fitted for measuring only, printed with its darkness table and written to reference/knob_shadow_fit.txt
(git-ignored). No shipped file is its output any more: shared/ui/KnobShadow.h is our own shadow formula (a swept,
softened disc plus a contact shadow) with hand-picked tokens, read off these numbers (darkest direction, darkness at
the edge, how fast it falls off).

Model (smooth, so it cannot ripple): darkness(d, a) = A(a) * g(d), factor = 1 - darkness
  d = distance beyond the knob's edge (design px), a = angle from up, clockwise
  A(a) = max(0, 3-harmonic angle series)           (where the light comes from)
  g(d) = w1 exp(-d / t1) + w2 exp(-d / t2)          (a tight contact shadow and a long soft one)
fitted by least squares to the plate brightness around the three knobs (labels, grille, plate edge and the other
knobs' shadows excluded)."""
import numpy as np
from PIL import Image
from scipy.optimize import least_squares

im = np.asarray(Image.open('reference/shots/silence.png').convert('RGB')).astype(float)
g = im.mean(2)
BASE = 70.0
knobs = [(45.755, 313.11), (754.745, 313.11), (841.74, 313.11)]
R = 25.06
D, A, F = [], [], []
for cx, cy in knobs:
    for dr in np.arange(1.5, 80.0, 1.0):
        for a in np.radians(np.arange(0, 360, 5)):
            x = cx + (R + dr) * np.sin(a); y = cy - (R + dr) * np.cos(a)
            if y < 280 or y > 357 or x < 4 or x > 884: continue
            if any(ox - 95 < x < ox and abs(y - oy) < 50 for ox, oy in knobs if (ox, oy) != (cx, cy)): continue
            if 176 <= x <= 560 and y < 352: continue
            if any(np.hypot(x - ox, y - oy) < R + 1.5 for ox, oy in knobs if (ox, oy) != (cx, cy)): continue
            X, Y = int(round(2 * x)), int(round(2 * y))
            D.append(dr); A.append(a); F.append(np.median(g[Y - 2:Y + 3, X - 2:X + 3]) / BASE)
D, A, F = map(np.array, (D, A, F))


def model(p, d, a):
    c = p[:7]
    amp = c[0] + c[1] * np.cos(a) + c[2] * np.sin(a) + c[3] * np.cos(2 * a) + c[4] * np.sin(2 * a) + c[5] * np.cos(3 * a) + c[6] * np.sin(3 * a)
    w1, t1, w2, t2 = p[7:]
    return 1 - np.maximum(0, amp) * (w1 * np.exp(-d / abs(t1)) + w2 * np.exp(-d / abs(t2)))


p0 = [0.3, -0.1, -0.3, 0, 0, 0, 0, 1.5, 6.0, 0.5, 25.0]
lo = [-2] * 7 + [0, 2, 0, 10]; hi = [2] * 7 + [5, 10, 3, 40]
fit = least_squares(lambda p: model(p, D, A) - np.minimum(F, 1.05), p0, loss='soft_l1', f_scale=0.05, bounds=(lo, hi))
p = fit.x
res = model(p, D, A) - F
print('rms residual', np.sqrt((res ** 2).mean()).round(4), 'params', p.round(4))
for dr in (2, 8, 16, 24, 40, 60):
    print(f'd {dr:3d}:', ' '.join(f'{model(p, dr, np.radians(a)):4.2f}' for a in range(0, 360, 30)))
import io, contextlib
A_ = np.radians(np.arange(0, 360, 0.5))
edge = model(p, 0.0, A_)
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    print('params', p.round(4))
    print('darkest direction', np.degrees(A_[np.argmin(edge)]).round(1), 'deg, edge factor', edge.min().round(3))
    for dr in (0, 4, 8, 16, 24, 40, 60, 80):
        print(f'd {dr:3d}:', ' '.join(f'{model(p, dr, np.radians(a)):4.2f}' for a in range(0, 360, 15)))
print(buf.getvalue(), end='')
open('reference/knob_shadow_fit.txt', 'w', newline='\n').write(buf.getvalue())
