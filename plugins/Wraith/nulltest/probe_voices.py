"""The doubler's voices against the measured delay trajectory (MEASUREMENTS.md "Doubler"): the
reference's voices (output less the dry path, Mix 1, Stereo 0) regressed on the input read at the two voices'
delays, through a short FIR per voice. What the regression leaves is what a delay-line model cannot explain.

    python probe_voices.py [taps]
"""
import sys
import numpy as np
from scipy.signal import resample_poly
import nulltest_lib as nl
import wr_ref as h

FS = 48000
CENTER, DEPTH, RATE = 7.58, 1.505, 0.5


def delayed(x, dms, up=8):
    """x read dms (per sample, ms) ago: 8x oversampling, then linear interpolation"""
    xu = resample_poly(x.astype(np.float64), up, 1)
    pos = (np.arange(len(x)) - dms * 1e-3 * FS) * up
    return np.interp(pos, np.arange(len(xu)), xu, left=0.0)


def regress(x, v, taps, skip):
    t = np.arange(len(x)) / FS
    s = np.sin(2 * np.pi * RATE * t)
    a, b = delayed(x, CENTER - DEPTH * s), delayed(x, CENTER + DEPTH * s)
    cols = []
    for sig in (a, b):
        for k in range(taps): cols.append(np.concatenate([np.zeros(k), sig[:len(sig) - k]])[skip:])
    A = np.stack(cols, 1)
    hcoef, *_ = np.linalg.lstsq(A, v[skip:], rcond=None)
    e = v[skip:] - A @ hcoef
    return 10 * np.log10(np.sum(e ** 2) / np.sum(v[skip:] ** 2)), hcoef.reshape(2, taps)


if __name__ == '__main__':
    taps = int(sys.argv[1]) if len(sys.argv) > 1 else 32
    for name, x in (('pink -18', nl.pink(4, -18, seed=3)), ('music -10', nl.stereo(nl.music(4, -10)).mean(0)),
                    ('drums -6', nl.drums(4, -6))):
        r = h.render_many([dict(x=nl.stereo(x), norm=h.ONLY('DBL'), params={'Doubler Mix': 1.0, 'Doubler Stereo': 0.0})], 'ref', cache=True)[0]
        v = r[0].astype(np.float64) - 1.0017 * x
        db, hc = regress(x, v, taps, FS // 2)
        H = np.abs(np.fft.rfft(hc, 4096, axis=1)); fr = np.fft.rfftfreq(4096, 1 / FS)
        pts = [30, 60, 100, 300, 1000, 3000, 6000, 10000, 15000]
        print(f'{name:10s} unexplained {db:6.1f} dB; voice gain at', ' '.join(f'{f}:{20 * np.log10(H[0][int(f * 4096 / FS)]):.1f}/{20 * np.log10(H[1][int(f * 4096 / FS)]):.1f}' for f in pts),
              ' dc sign', np.sign(hc.sum(1)))
