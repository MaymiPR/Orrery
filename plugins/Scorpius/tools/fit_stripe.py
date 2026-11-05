"""The visualiser stripe: measures its glow in a film of the reference and compares a film of ours with it. A measuring
tool: it writes no shipped file. Its numbers become tokens of the analytic glow in Source/ui/StripeGlow.h (a profile
down the stripe of our own shape, a bell along it per channel); no table of it is copied into the source.

    python fit_stripe.py orion.raw                 measures the glow, prints its tokens
    python fit_stripe.py orion.raw ours.raw        prints the statistics the particles were matched on, for both

The films: tools/RefCapture at 200 % (Orion's state with prefs.uiScaling=2, nulltest/refstate.py; ours with
uiScale="2.0"), rows=0.66,0.775 (the stripe's band), in= the probe signal below (1 kHz tone, mono float32 48 kHz):
1.5 s silence, then with 1.5 s of silence after each: -60 dB 2 s then -10 dB 2 s; -10 then -60; -60 1.5 s, 0.3 s gap,
-10 1.5 s; -55, -50, -45, -40, -35 dB 1.5 s each; -60 then -40 2 s each; -60 1 s, a 0.2 s rise to -10, -10 1.8 s.
WINDOWS are the stretches where the reference's stripe is fully lit; its frame at 0.5 s is the idle stripe.
"""
import os
import sys
import numpy as np
from scipy import ndimage
from scipy.optimize import least_squares

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'Positron', 'nulltest'))
from filmtools import Film  # noqa: E402

WINDOWS = [(3.8, 5.4), (7.2, 9.5), (14.6, 15.7), (26.5, 27.7), (29.5, 30.7), (34.5, 36.2), (39.0, 40.7)]
STOPS = [5.5, 9.0, 11.0, 15.8, 18.8, 21.8, 24.8, 27.8, 30.8, 36.3, 40.8]   # where the tone stops or drops
BAND_TOP = 266.5                       # design y of the film's first row (2 rows per design px)


def frames(f):
    return np.stack([f.frame(i) for i in range(f.n) if any(a < f.t[i] < b for a, b in WINDOWS)]).astype(np.float32)


def fit_glow(f):
    """the 20th percentile of the lit frames less the idle frame, as a profile down the stripe times a bell along it
    per channel; prints the bells' tokens and where the profile peaks (a report, not a source file)"""
    idle = f.at(0.5).astype(np.float32)
    d = np.clip(np.percentile(frames(f), 20, axis=0) - idle, 0, None)[11:82, 20:1756]
    xs = (np.arange(20, 1756) + 0.5) / 2
    ys = (np.arange(11, 82) + 0.5) / 2 + BAND_TOP
    U, s, Vt = np.linalg.svd(d.mean(-1), full_matrices=False)
    Y = U[:, 0] * np.sign(U[:, 0].sum()); Y = Y / Y.max()
    bell = lambda p, x: p[1] * np.exp(-((x - p[0]) / p[2]) ** 2) + p[3] * np.exp(-np.abs(x - p[0]) / p[4])
    fits = []
    for c in range(3):
        X = (d[..., c] * Y[:, None]).sum(0) / (Y ** 2).sum()
        fits.append(least_squares(lambda p: bell(p, xs) - X, [460, 30, 120, 30, 80]).x)
    model = np.stack([Y[:, None] * bell(fits[c], xs)[None, :] for c in range(3)], -1)
    print('glow fit rms %.2f (mean %.2f)' % (np.sqrt(((model - d) ** 2).mean()), d.mean()))
    print('profile down the stripe: peak at y %.2f; mean above y 286 %.2f, y 286 ... 296 %.2f, y 296 ... 303 %.2f'
          % (ys[Y.argmax()], Y[ys < 286].mean(), Y[(ys >= 286) & (ys < 296)].mean(), Y[(ys >= 296) & (ys < 303)].mean()))
    for name, p in zip(('red', 'green', 'blue'), fits):
        print('bell %-5s centre %.1f  width %.1f  strength %.0f  core %.0f  core width %.1f (grey levels)' % (name, *p[[0, 2, 1, 3, 4]]))


def stats(name, f):
    st = frames(f)
    L = st.mean(-1)
    idle = f.at(0.5).astype(np.float32).mean(-1)
    p20 = np.percentile(L, 20, axis=0)
    mean = L.mean(0)
    rows = lambda img: ' '.join('%3.0f' % img[y:y + 4, 100:1676].mean() for y in range(10, 84, 4))
    cols = lambda img: ' '.join('%3.0f' % img[15:80, x:x + 74].mean() for x in range(0, 1776, 74))
    print('==', name, '(%d lit frames)' % len(st))
    print(' glow (p20 - idle) by rows ', rows(p20 - idle))
    print(' particles (mean - p20) rows', rows(mean - p20))
    print(' glow along                ', cols(p20 - idle))
    print(' particles along           ', cols(mean - p20))
    # particles per frame (local maxima 30 above the 20th percentile) by 2 design px across the stripe
    count = np.zeros(23); peaks = [[] for _ in range(23)]
    for k in range(0, len(L), 2):
        d = np.clip(L[k] - p20, 0, None)
        ys, xs = np.nonzero((d == ndimage.maximum_filter(d, size=3)) & (d > 30))
        for y, v in zip(ys, d[ys, xs]): count[y // 4] += 1; peaks[y // 4].append(v)
    n = len(range(0, len(L), 2))
    print(' particles/frame by rows   ', ' '.join('%3.0f' % (c / n) for c in count))
    print(' their median peak         ', ' '.join('%3.0f' % (np.median(p) if p else 0) for p in peaks))
    # how fast the particle layer changes (frame-to-frame correlation)
    part = L[:, 15:80, 100:1676] - p20[15:80, 100:1676]
    print(' particle layer correlation', ' '.join('lag %d: %.2f' % (lag, np.mean([np.corrcoef(part[k].ravel(), part[k + lag].ravel())[0, 1]
                                                                            for k in range(0, len(part) - lag, 2)])) for lag in (1, 2, 4, 10)))
    # brightness after each stop (0 idle, 1 lit)
    full = np.mean([f.at(t)[22:78, 30:1740].astype(float).mean() for t in np.arange(7.5, 9.0, 0.1)])
    base = f.at(0.5)[22:78, 30:1740].astype(float).mean()
    b = lambda t: (f.at(t)[22:78, 30:1740].astype(float).mean() - base) / (full - base)
    for e in STOPS:
        print(' after %4.1f s:' % e, ' '.join('%.2f' % b(e + dt) for dt in np.arange(0, 1.3, 0.15)))


if __name__ == '__main__':
    ref = Film(sys.argv[1])
    if len(sys.argv) == 2:
        fit_glow(ref)
    else:
        stats('reference', ref)
        stats('ours', Film(sys.argv[2]))
