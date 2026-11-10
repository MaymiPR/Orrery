"""Where does the high band's release act: on the detector's level before the static curve (our law), or on the gain
reduction in dB after it (an instant level, the static curve, then a one-pole attack / release on the reduction)?
The reference's band gain after 8 kHz tone drops from 0 dBFS to several depths, and on a rising staircase (measure_high_release.py's
probes, read through the measured shaper by measure_mid_release.gains), fitted with each structure; the gain traces are compared
as 1 ms medians in dB.

    python probe_gr_drop.py [amount 0..1] [--fit]     (--fit: fit the reduction-smoothing structure; else the current law only)
Writes measurements/Positron/character/grdrop_<amount>.json."""
import json, os, sys
import numpy as np
from scipy.optimize import least_squares
import po_ref, charsim_lib as C, charmodel_lib as CM, nulltest as N
import measure_mid_release as R, measure_high_release as H
from measure_high_gain_noise import header_laws

FS = po_ref.FS
F = 8000.0
DEPTHS = (-3, -5, -7, -9, -11, -15, -21, -45)
HOLD, AFTER = 1.0, 1.0


def probes():
    xs = [H.drop_signal(0.0, b, F, HOLD, AFTER) for b in DEPTHS]
    st, levs, n = H.staircase(F, -24.0, 3.0, 1.0, 0.25)
    return xs + [st], len(levs) * n


def ms_db(n, i0, i1):
    """1 ms medians of a gain trace (dB) over [i0, i1)"""
    w = FS // 1000
    return np.array([20 * np.log10(np.nanmedian(n[i:i + w])) for i in range(i0, i1 - w + 1, w)])


def windows(ns):
    """per probe: 1 ms medians from 50 ms before the drop to 400 ms after it; the staircase whole"""
    i0 = int((0.5 + HOLD) * FS)
    return [ms_db(n, i0 - FS // 20, i0 + int(0.4 * FS)) for n in ns[:-1]] + [ms_db(ns[-1], 0, len(ns[-1]))]


def model_traces(xs, law):
    """our band gain on the probes for a law (charsim, the plug-in's gain computer), on the nonlinear-stage mid signal"""
    p = {k: v for k, v in law.items() if k in C.NAMES}
    if len(_mids) != len(xs):
        _mids[:] = [0.5 * (sb[2][0] + sb[2][1]) for sb in (CM.prep(x)[1] for x in xs)]
    return [C.band_gain(m, p, peak=1)[N.PRE:] for m in _mids]


_mids = []


def err(a, b):
    ok = np.isfinite(a) & np.isfinite(b)
    return np.sqrt(np.mean((a[ok] - b[ok]) ** 2))


if __name__ == '__main__':
    amt = float(sys.argv[1]) if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 1.0
    R.BAND, R.FREQ = 2, F
    row = int(round(amt * 16)); law = header_laws(row)['high']
    xs, nst = probes()
    ref = windows(R.gains(xs, amt, True))
    cur = windows(model_traces(xs, law))
    names = [f'drop to {b}' for b in DEPTHS] + ['staircase']
    print('current law: rms error (dB) per probe:', ' '.join(f'{err(r, c):.3f}' for r, c in zip(ref, cur)))
    res = {'current': {n: err(r, c) for n, r, c in zip(names, ref, cur)}}
    if '--fit' in sys.argv:
        keys = ['mix', 'thresh', 'knee', 'ratio', 'gainAttack', 'gainRelease']
        lo, hi = [0.0, -40, 0.0, 1.0, 0.01, 1.0], [1.0, 0.0, 30, 20, 50, 2000]
        base = dict(law, attack=0.001, release=0.001, attack2=0, release2=0, slowOffset=0, fallRate=0)
        def resid(q):
            mt = windows(model_traces(xs, dict(base, **dict(zip(keys, q)))))
            return np.concatenate([np.nan_to_num(m - r) for m, r in zip(mt, ref)])
        best = None
        for ga, gr in ((1.0, 100.0), (0.3, 200.0), (3.0, 60.0)):
            q0 = [law['mix'], law['thresh'], max(law['knee'], 0.5), law['ratio'], ga, gr]
            r = least_squares(resid, q0, bounds=(lo, hi), x_scale='jac', max_nfev=200)
            if best is None or r.cost < best.cost: best = r
            print('start', ga, gr, '->', {k: round(v, 4) for k, v in zip(keys, r.x)}, 'cost', round(r.cost, 3), flush=True)
        fl = dict(base, **dict(zip(keys, best.x)))
        mt = windows(model_traces(xs, fl))
        print('reduction smoothed: rms error (dB) per probe:', ' '.join(f'{err(r, m):.3f}' for r, m in zip(ref, mt)))
        res['gr_smoothed'] = {n: err(r, m) for n, r, m in zip(names, ref, mt)}
        res['gr_law'] = {k: float(v) for k, v in zip(keys, best.x)}
    out = os.path.join(po_ref.ROOT, 'measurements', 'Positron', 'character', f'grdrop_{amt}.json')
    json.dump(res, open(out, 'w'), indent=1)
