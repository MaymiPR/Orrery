"""The doubler's modulation, tracked the same way on the reference and on our processor (MEASUREMENTS.md "Doubler"):
white noise in, Mix 1, Stereo 1; per 5 ms the cross-correlation of the side output (L - R, which holds
the two voices with opposite signs and none of the dry path or the lows) with the input, upsampled 16 times. Its
positive peak is the first voice's delay, its negative peak the second's. A sine of free rate, phase, centre and depth
is then fitted to each track: what it leaves is what the modulation is not.

    python probe_dbl_rate.py [fs] [secs] [tune.json]
"""
import json, sys
import numpy as np
from scipy.optimize import least_squares
import nulltest_lib as nl
import wr_ref as h

HOP, UP = 240, 16


def tracks(y, x, fs):
    WIN = 1024 * fs // 48000
    s = 0.5 * (y[0] - y[1]).astype(np.float64)
    x = x.astype(np.float64)
    lo, hi = int(0.004 * fs), int(0.0115 * fs)
    t, da, db = [], [], []
    w = np.hanning(WIN)
    for c in range(fs // 5, len(x) - WIN - hi, HOP * fs // 48000):
        xs = x[c - hi: c + WIN] * 1.0
        xs[:hi] = 0                                             # the input that the window's output can see
        X = np.fft.rfft(xs, 2 * (WIN + hi))
        S = np.fft.rfft(np.concatenate([np.zeros(hi), s[c: c + WIN] * w]), 2 * (WIN + hi))
        r = np.fft.irfft(S * np.conj(X), UP * 2 * (WIN + hi)) * UP
        seg = r[UP * lo: UP * hi]
        i, j = int(np.argmax(seg)), int(np.argmin(seg))
        t.append((c + WIN / 2) / fs)
        da.append((lo + i / UP) / fs * 1000); db.append((lo + j / UP) / fs * 1000)
    return np.array(t), np.array(da), np.array(db)


def fit(t, d, sign):
    f = lambda p: p[0] - sign * p[1] * np.sin(2 * np.pi * (p[2] * t + p[3]))
    r = least_squares(lambda p: f(p) - d, [7.5, 1.5, 0.5, 0.0])
    e = d - f(r.x)
    keep = np.abs(e) < 5 * np.median(np.abs(e)) + 1e-3        # drop the windows where the two voices cross
    r = least_squares(lambda p: (f(p) - d)[keep], r.x)
    return r.x, (d - f(r.x))[keep].std()


def run(fs=48000, secs=8.0, tune=None):
    x = nl.noise(secs, -18, fs=fs, seed=21)
    j = dict(x=nl.stereo(x), norm=h.ONLY('DBL'), params={'Doubler Mix': 1.0, 'Doubler Stereo': 1.0})
    out = {}
    for who in ('ref', 'model'):
        y = h.render_many([dict(j, tune=tune or {})] if who == 'model' else [j], who, fs=fs, cache=who == 'ref')[0]
        t, da, db = tracks(y, x, fs)
        out[who] = (t, da, db)
        for nm, d, sg in (('a', da, 1), ('b', db, -1)):
            p, rms = fit(t, d, sg)
            print(f'{who:5s} {fs} voice {nm}: centre {p[0]:.4f} ms depth {p[1]:.4f} ms rate {p[2]:.6f} Hz phase {p[3] % 1:.5f} '
                  f'cycles; left over {rms * 1000:.1f} us rms', flush=True)
    return out


if __name__ == '__main__':
    fs = int(sys.argv[1]) if len(sys.argv) > 1 else 48000
    secs = float(sys.argv[2]) if len(sys.argv) > 2 else 8.0
    tune = json.load(open(sys.argv[3])) if len(sys.argv) > 3 else None
    run(fs, secs, tune)
