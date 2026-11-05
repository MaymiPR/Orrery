"""Character stage, the Focus EQ (MEASUREMENTS.md "Character"): the stage's response where its dynamics hold a constant
gain (Compression -50, noise at -38 dBFS: probe_char.py eqshape) at Focus -50 ... 50, fitted with one cascade of RBJ
filters whose gains move linearly with Focus (gain = a + b * Focus / 50), on magnitude and phase together.

    python fit_focus_eq.py [--sections spec]    prints the fit, the error per Focus value, and the C++ table
"""
import argparse, json, os
import numpy as np
from scipy.optimize import least_squares
import probe_char as pc

FS = 48000
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'renders', 'focus_eq.npz')
# section kinds: hp (2nd-order high-pass: f, q), ls / hs (shelf: f, q, a, b), pk (peak: f, q, a, b), lp (low-pass)
START = [('hp', 30, 0.8), ('hp', 60, 0.6), ('ls', 180, 0.7, -6, 0), ('pk', 360, 2.0, 3, 1), ('pk', 1150, 0.9, 3, 2),
         ('pk', 2400, 2.0, -1, 0), ('pk', 5000, 1.2, 3, 2), ('pk', 8000, 3.0, -3, 0), ('pk', 11000, 2.0, 2, 1),
         ('lp', 19000, 0.7)]


def biquad(kind, f, q, g=0.0):
    A = 10 ** (g / 40); w0 = 2 * np.pi * f / FS; c = np.cos(w0); s = np.sin(w0); al = s / (2 * q)
    if kind == 'pk':
        b = [1 + al * A, -2 * c, 1 - al * A]; a = [1 + al / A, -2 * c, 1 - al / A]
    elif kind == 'hp':
        b = [(1 + c) / 2, -(1 + c), (1 + c) / 2]; a = [1 + al, -2 * c, 1 - al]
    elif kind == 'lp':
        b = [(1 - c) / 2, 1 - c, (1 - c) / 2]; a = [1 + al, -2 * c, 1 - al]
    else:
        k = 2 * np.sqrt(A) * al
        if kind == 'ls':
            b = [A * ((A + 1) - (A - 1) * c + k), 2 * A * ((A - 1) - (A + 1) * c), A * ((A + 1) - (A - 1) * c - k)]
            a = [(A + 1) + (A - 1) * c + k, -2 * ((A - 1) + (A + 1) * c), (A + 1) + (A - 1) * c - k]
        else:
            b = [A * ((A + 1) + (A - 1) * c + k), -2 * A * ((A - 1) + (A + 1) * c), A * ((A + 1) + (A - 1) * c - k)]
            a = [(A + 1) - (A - 1) * c + k, 2 * ((A - 1) - (A + 1) * c), (A + 1) - (A - 1) * c - k]
    return np.array(b) / a[0], np.array(a) / a[0]


def response(secs, focus, f):
    z = np.exp(-1j * 2 * np.pi * f / FS)
    H = np.ones_like(z)
    for s in secs:
        kind, fr, q = s[0], s[1], s[2]
        g = s[3] + s[4] * focus / 50.0 if kind in ('pk', 'ls', 'hs') else 0.0
        b, a = biquad(kind, fr, q, g)
        H *= (b[0] + b[1] * z + b[2] * z * z) / (a[0] + a[1] * z + a[2] * z * z)
    return H


def pack(secs):
    p = []
    for s in secs:
        p += [np.log(s[1]), np.log(s[2])] + (list(s[3:5]) if s[0] in ('pk', 'ls', 'hs') else [])
    return np.array(p, float)


def unpack(kinds, p):
    out, i = [], 0
    for k in kinds:
        if k in ('pk', 'ls', 'hs'):
            out.append((k, np.exp(p[i]), np.exp(p[i + 1]), p[i + 2], p[i + 3])); i += 4
        else:
            out.append((k, np.exp(p[i]), np.exp(p[i + 1]))); i += 2
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--start', default=None, help='JSON file with a section list to start from')
    ap.add_argument('--phase', type=float, default=0.0, help='weight of the phase error (0: magnitude only)')
    ap.add_argument('--delay', type=float, default=0.0, help='a pure delay in samples to add to the model')
    a = ap.parse_args()
    if not os.path.exists(DATA):
        pc.eqshape(save=DATA)
    d = np.load(DATA)
    f_all = d['f']
    sel = np.unique(np.round(np.geomspace(18, 21000, 400) / (f_all[1] - f_all[0])).astype(int))
    f = f_all[sel]
    focus = [int(k) for k in d.files if k != 'f']
    meas = {fo: d[str(fo)][sel] for fo in focus}
    secs = json.load(open(a.start)) if a.start else START
    kinds = [s[0] for s in secs]

    def resid(p):
        ss = unpack(kinds, p)
        r = []
        for fo in focus:
            e = np.log(response(ss, fo, f) * np.exp(-1j * 2 * np.pi * f / FS * a.delay) / meas[fo])
            r += [e.real * 8.686] + ([np.angle(np.exp(1j * e.imag)) * a.phase] if a.phase else [])
        return np.concatenate(r)

    lo = [];  hi = []
    for s in secs:
        lo += [np.log(15), np.log(0.1)] + ([-30, -30] if s[0] in ('pk', 'ls', 'hs') else [])
        hi += [np.log(23500), np.log(20)] + ([30, 30] if s[0] in ('pk', 'ls', 'hs') else [])
    r = least_squares(resid, np.clip(pack(secs), lo, hi), bounds=(lo, hi), max_nfev=20000, x_scale='jac')
    ss = unpack(kinds, r.x)
    for s in ss:
        print('  ' + ', '.join(f'{v:.4f}' if isinstance(v, float) else repr(v) for v in s))
    for fo in focus:
        e = response(ss, fo, f) * np.exp(-1j * 2 * np.pi * f / FS * a.delay) / meas[fo]
        print(f'focus {fo:4d}: magnitude error max {np.max(np.abs(20 * np.log10(np.abs(e)))):.3f} dB, '
              f'rms {np.sqrt(np.mean((20 * np.log10(np.abs(e))) ** 2)):.3f} dB, phase rms {np.degrees(np.sqrt(np.mean(np.angle(e) ** 2))):.2f} deg, '
              f'complex error {20 * np.log10(np.sqrt(np.mean(np.abs(e - 1) ** 2))):.1f} dB')
    json.dump([[float(v) if not isinstance(v, str) else v for v in s] for s in ss], open(os.path.join(os.path.dirname(DATA), 'focus_eq_fit.json'), 'w'))


if __name__ == '__main__':
    main()
