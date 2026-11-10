"""Character stage: the fixed phase part (MEASUREMENTS.md "Character"). The measured response divided by the fitted
Focus EQ cascade (fit_focus_eq.py) leaves a phase that does not depend on Focus; it is fitted here with a delay and
second-order all-passes, and the whole model is checked in the complex domain.

    python fit_allpass.py [--n 4]
"""
import argparse, json
import numpy as np
from scipy.optimize import least_squares
from fit_focus_eq import model_db, FS
from focus_eq_lib import load


def ap2(fr, q, z):
    w0 = 2 * np.pi * fr / FS; c = np.cos(w0); al = np.sin(w0) / (2 * q)
    b = np.array([1 - al, -2 * c, 1 + al]); a = np.array([1 + al, -2 * c, 1 - al])
    return (b[0] + b[1] * z + b[2] * z * z) / (a[0] + a[1] * z + a[2] * z * z)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--n', type=int, default=4); ap.add_argument('--joint', action='store_true'); a = ap.parse_args()
    d = load(); f_all = d['f']
    sel = np.unique(np.round(np.geomspace(60, 22000, 400) / (f_all[1] - f_all[0])).astype(int))
    f = f_all[sel]; z = np.exp(-1j * 2 * np.pi * f / FS)
    m = json.load(open('renders/focus_eq2.json'))
    focus = sorted(int(k) for k in d.files if k != 'f')
    ex = np.array([d[str(fo)][sel] / model_db(m['sections'], fo, z)[1] for fo in focus])
    exc = np.angle(np.mean(ex / np.abs(ex), axis=0))
    def resp(p):
        H = np.exp(-1j * 2 * np.pi * f / FS * p[0])
        for k in range(a.n): H = H * ap2(np.exp(p[1 + 2 * k]), np.exp(p[2 + 2 * k]), z)
        return H
    best = None
    rng = np.random.default_rng(1)
    lo = [0] + [np.log(20), np.log(0.05)] * a.n; hi = [64] + [np.log(23900), np.log(20)] * a.n
    for trial in range(200):
        p0 = [rng.uniform(0, 6)] + sum([[np.log(np.exp(rng.uniform(np.log(30), np.log(20000)))), np.log(rng.uniform(0.2, 2))] for _ in range(a.n)], [])
        r = least_squares(lambda p: np.angle(resp(p) * np.exp(-1j * exc)), np.clip(p0, lo, hi), bounds=(lo, hi), max_nfev=2000)
        e = np.degrees(np.sqrt(np.mean(r.fun ** 2)))
        if best is None or e < best[1]: best = (r.x, e)
    p = best[0]
    print(f'delay {p[0]:.3f} samples, phase rms {best[1]:.3f} deg; all-passes ' +
          ', '.join(f'{np.exp(p[1 + 2 * k]):.2f} Hz Q {np.exp(p[2 + 2 * k]):.4f}' for k in range(a.n)))
    for k, fo in enumerate(focus):
        e = model_db(m['sections'], fo, z)[1] * resp(p) / d[str(fo)][sel]
        print(f'focus {fo:4d}: complex error {20 * np.log10(np.sqrt(np.mean(np.abs(e - 1) ** 2))):.1f} dB (60 Hz to 22 kHz)')
    m['delay'] = float(p[0]); m['allpass'] = [[float(np.exp(p[1 + 2 * k])), float(np.exp(p[2 + 2 * k]))] for k in range(a.n)]
    json.dump(m, open('renders/focus_eq2.json', 'w'), indent=1)



def joint():
    """refine the magnitude sections, the all-passes and the delay together on the complex error (30 Hz to 22 kHz)"""
    from fit_focus_eq import pack, unpack, bounds
    d = load(); f_all = d['f']
    sel = np.unique(np.round(np.geomspace(30, 22000, 500) / (f_all[1] - f_all[0])).astype(int))
    f = f_all[sel]; z = np.exp(-1j * 2 * np.pi * f / FS)
    m = json.load(open('renders/focus_eq2.json'))
    focus = sorted(int(k) for k in d.files if k != 'f')
    kinds = [s[0] for s in m['sections']]; na = len(m['allpass'])
    p0 = np.concatenate([pack(m['sections']), [m['delay']], np.log(np.array(m['allpass'])).ravel()])
    lo, hi = bounds(kinds)
    lo = np.concatenate([lo, [0], [np.log(15), np.log(0.05)] * na]); hi = np.concatenate([hi, [64], [np.log(23900), np.log(20)] * na])
    meas = {fo: d[str(fo)][sel] for fo in focus}
    wgt = np.where(f < 60, 0.3, 1.0)
    def model(p, fo):
        ns = len(pack(m['sections']))
        H = model_db(unpack(kinds, p[:ns]), fo, z)[1] * np.exp(-1j * 2 * np.pi * f / FS * p[ns])
        for k in range(na): H = H * ap2(np.exp(p[ns + 1 + 2 * k]), np.exp(p[ns + 2 + 2 * k]), z)
        return H
    def res(p):
        out = []
        for fo in focus:
            e = model(p, fo) / meas[fo] - 1
            out += [e.real * wgt, e.imag * wgt]
        return np.concatenate(out)
    r = least_squares(res, np.clip(p0, lo + 1e-9, hi - 1e-9), bounds=(lo, hi), max_nfev=3000, x_scale='jac')
    ns = len(pack(m['sections']))
    m['sections'] = unpack(kinds, r.x[:ns]); m['delay'] = float(r.x[ns])
    m['allpass'] = [[float(np.exp(r.x[ns + 1 + 2 * k])), float(np.exp(r.x[ns + 2 + 2 * k]))] for k in range(na)]
    for fo in focus:
        e = model(r.x, fo) / meas[fo]
        good = f > 60
        print(f'focus {fo:4d}: complex error {20 * np.log10(np.sqrt(np.mean(np.abs(e[good] - 1) ** 2))):.1f} dB above 60 Hz, '
              f'{20 * np.log10(np.sqrt(np.mean(np.abs(e - 1) ** 2))):.1f} dB from 30 Hz')
    json.dump(m, open('renders/focus_eq2.json', 'w'), indent=1)


if __name__ == '__main__':
    import sys
    joint() if '--joint' in sys.argv else main()
