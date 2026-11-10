"""The doubler's voice filter (MEASUREMENTS.md "Doubler"): the voices' response regressed on the
input read at their tracked (wobbling) delays (measurements/Wraith/dbl_fir_a / _b.npy, from short-window cross-
correlation tracking) fitted with a gain, a first-order high-pass and two RBJ low-passes, plus the delay shift the
filters' group delay calls for.

    python fit_voice_filter.py
"""
import os
import numpy as np
from scipy.optimize import least_squares
import wr_ref as h

FS, PRE, N = 48000, 24, 4096
D = os.path.join(h.ROOT, 'measurements', 'Wraith')


def hp1(f, z):
    k = np.tan(np.pi * f / FS); b0 = 1 / (1 + k)
    return b0 * (1 - z) / (1 - (1 - k) / (1 + k) * z)


def lp2(f, q, z):
    w = 2 * np.pi * f / FS; c, al = np.cos(w), np.sin(w) / (2 * q)
    return ((1 - c) / 2 * (1 + 2 * z + z * z)) / ((1 + al) - 2 * c * z + (1 - al) * z * z)


def model(p, z, w):
    g, fh, f1, q1, f2, q2, tau = p
    return g * hp1(np.exp(fh), z) * lp2(np.exp(f1), np.exp(q1), z) * lp2(np.exp(f2), np.exp(q2), z) * np.exp(1j * w * tau)


if __name__ == '__main__':
    hc = np.mean([np.load(os.path.join(D, f'dbl_fir_{v}.npy')) for v in 'ab'], 0)
    Hm = np.fft.rfft(np.roll(np.concatenate([hc, np.zeros(N - len(hc))]), -PRE))
    fr = np.fft.rfftfreq(N, 1 / FS); w = 2 * np.pi * fr / FS; z = np.exp(-1j * w)
    m = fr > 15
    p0 = [0.35, np.log(400), np.log(11000), np.log(0.7), np.log(14000), np.log(0.7), 0.0]
    res = lambda p: (lambda e: np.concatenate([e.real, e.imag]))((model(p, z, w) - Hm)[m])
    r = least_squares(res, p0)
    e = 10 * np.log10(np.sum(r.fun ** 2) / np.sum(np.abs(Hm[m]) ** 2))
    g, fh, f1, q1, f2, q2, tau = r.x
    print(f'fit {e:.1f} dB: gain {g:.4f}, high-pass {np.exp(fh):.1f} Hz, low-passes {np.exp(f1):.0f} Hz Q {np.exp(q1):.3f}, '
          f'{np.exp(f2):.0f} Hz Q {np.exp(q2):.3f}, delay shift {tau:.2f} samples')
    Mo = model(r.x, z, w)
    print('|model| - |measured| dB:', ' '.join(f'{f}:{20 * np.log10(abs(Mo[int(f * N / FS)]) / abs(Hm[int(f * N / FS)])):.2f}' for f in [30, 100, 300, 1000, 3000, 8000, 12000, 15000, 18000]))
