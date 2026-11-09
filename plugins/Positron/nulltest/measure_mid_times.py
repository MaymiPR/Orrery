"""The mid detector's attack and release time constants read directly from tone steps (measure_mid_release.py's gain traces,
turned into detector level by measure_mid_release2.level_of): each step's level trace is fitted by a one-pole mean-square detector,
L(t) = 10 log10(P1 + (P0 - P1) exp(-t / tau)) + 3.01, tau and the end level free. One tau per step; if the detector is
a one-pole in the power domain, every step gives the same tau.

    python measure_mid_times.py [amount ...] [--deep]      --deep: only the steps that read the release cleanly (to -45 dBFS)"""
import sys
import numpy as np
from scipy.optimize import least_squares
import measure_mid_release as R, midrel2 as R2
from measure_high_trace3 import header_laws

FS = R.FS
STEPS = [(0, -20), (0, -30), (0, -45), (-12, -24), (-20, -45), (-6, -18),
         (-45, 0), (-30, 0), (-20, 0), (-30, -12), (-45, -20), (-24, -6)]


START = 0.0


def fit_tau(lv, t):
    ok = np.isfinite(lv)
    if ok.sum() < 10: return np.nan
    def f(q):
        tau, e, s = q; p1 = 10 ** ((e - 3.0103) / 10); p0 = 10 ** ((s - 3.0103) / 10)
        return 10 * np.log10(np.maximum(p1 + (p0 - p1) * np.exp(-t[ok] / tau), 1e-30)) + 3.0103 - lv[ok]
    r = least_squares(f, [0.1, lv[ok][-1], START], bounds=([1e-3, -90, -90], [5, 20, 20]))
    return r.x[0] * 1000, 20 * np.log10(max(1e-12, np.sqrt(np.mean(r.fun ** 2))))


if __name__ == '__main__':
    import measure_mid_times as _self
    if '--deep' in sys.argv: STEPS = [(0, -45), (-20, -45), (-45, 0), (-30, 0)]; sys.argv.remove('--deep')
    amts = [float(a) for a in sys.argv[1:]] or [0.5]
    for amt in amts:
        law = header_laws(int(round(amt * 16)))['mid']
        xs = [R.step_signal(a, b, 700.0) for a, b in STEPS]
        nr, no = R.gains(xs, amt, True), R.gains(xs, amt, False)
        print(f'amount {amt * 200:.0f} %: table attack {law["attack"]:.1f} ms, release {law["release"]:.1f} ms')
        w = int(FS * 0.005); i0 = int(R.HOLD * FS)
        t = np.arange(0.0, 1.5, 0.005)
        for (a, b), r, o in zip(STEPS, nr, no):
            res = []
            for n in (r, o):
                lv = np.array([R2.level_of(np.nanmedian(n[i0 + int(tt * FS) - w // 2:i0 + int(tt * FS) + w // 2]), law) for tt in t])
                # only where the band is compressing clearly (the level is read through the knee)
                lv[lv < law['thresh'] - law['knee'] / 2 + 3] = np.nan

                _self.START = a
                res.append(fit_tau(lv, t))
            kind = 'release' if b < a else 'attack '
            print(f'   {a:+4d} -> {b:+4d} dBFS {kind}: ref tau {res[0][0]:7.1f} ms (fit {res[0][1]:6.1f} dB)   ours {res[1][0]:7.1f} ms (fit {res[1][1]:6.1f} dB)')
