"""EQ stage: impulse responses of the reference's low and high shelves at several gains and rates, fitted with RBJ
shelves (MEASUREMENTS.md "EQ"). Prints f0 and Q per shelf and rate and the time-domain null of each fit.

    python fit_eq.py
"""
import numpy as np
from scipy.optimize import least_squares
from scipy.signal import lfilter
import ts as h

RATES = (44100, 48000, 88200, 96000)
CASES = [('EQ Low Gain', g) for g in (12.0, 6.0, -12.0)] + [('EQ High Gain', g) for g in (12.0, 6.0, -12.0)]


def shelf(fs, f0, q, g, low, warp):
    A = 10 ** (g / 40)
    w0 = 2 * np.arctan(np.pi * f0 / fs) if warp else 2 * np.pi * f0 / fs
    c, s = np.cos(w0), np.sin(w0); al = s / (2 * q); k = 2 * np.sqrt(A) * al
    if low:
        b = [A * ((A + 1) - (A - 1) * c + k), 2 * A * ((A - 1) - (A + 1) * c), A * ((A + 1) - (A - 1) * c - k)]
        a = [(A + 1) + (A - 1) * c + k, -2 * ((A - 1) + (A + 1) * c), (A + 1) + (A - 1) * c - k]
    else:
        b = [A * ((A + 1) + (A - 1) * c + k), -2 * A * ((A - 1) + (A + 1) * c), A * ((A + 1) + (A - 1) * c - k)]
        a = [(A + 1) - (A - 1) * c + k, 2 * ((A - 1) - (A + 1) * c), (A + 1) - (A - 1) * c - k]
    return np.array(b) / a[0], np.array(a) / a[0]


def db(x): return 20 * np.log10(np.sqrt(np.mean(np.square(x))) + 1e-30)


def main():
    out = {}
    for fs in RATES:
        n = fs
        x = np.zeros(n, np.float32); x[100] = 0.1
        other = {'EQ Low Gain': 0.0, 'EQ High Gain': 0.0}
        jobs = [dict(x=x, norm=h.ONLY('EQ'), params=dict(other, **{name: g})) for name, g in CASES]
        ys = h.render_many(jobs, fs=fs, cache=True)
        for (name, g), y in zip(CASES, ys):
            ir = y[0, 100:] / 0.1
            low = name == 'EQ Low Gain'
            imp = np.zeros_like(ir); imp[0] = 1.0
            best = None
            for warp in (False, True):
                def res(p):
                    b, a = shelf(fs, p[0], p[1], g, low, warp)
                    return (lfilter(b, a, imp) - ir)[:8192]
                for f0 in ((150, 300) if low else (5000, 10000)):
                    r = least_squares(res, [f0, 0.7], bounds=([10, 0.1], [fs * 0.49, 10]))
                    b, a = shelf(fs, r.x[0], r.x[1], g, low, warp)
                    null = db(lfilter(b, a, imp) - ir) - db(ir)
                    if best is None or null < best[0]: best = (null, r.x, warp)
            null, (f0, q), warp = best
            print(f'{fs:6d} {name:12s} {g:+5.1f} dB: f0 {f0:9.3f} Hz  Q {q:.5f}  warp {warp}  null {null:7.1f} dB')
            out[(fs, name, g)] = (f0, q, warp, null)
    return out


if __name__ == '__main__':
    main()
