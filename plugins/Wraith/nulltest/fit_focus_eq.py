"""Character stage, the Focus EQ (MEASUREMENTS.md "Character"). The measured response splits into a
Focus-dependent magnitude and an excess phase that does not depend on Focus (a fixed all-pass and delay). So:
1. the magnitude at every Focus value is fitted with one cascade of RBJ sections (high-passes fixed, peaks and shelves
   with gain a + b * Focus / 50), grown greedily: each round adds a peak where the joint residual is largest and refits
   everything;
2. the excess phase (measured phase less the minimum phase of the measured magnitude) is fitted with a delay and
   second-order all-passes.
Writes renders/focus_eq2.json (the sections, the all-passes, the delay) for fit checks and Source/dsp/FocusEq.h.

    python fit_focus_eq.py [--rounds 12] [--allpass 4]
"""
import argparse, json, os
import numpy as np
from scipy.optimize import least_squares
from focus_eq_lib import biquad, load, FS

HERE = os.path.dirname(os.path.abspath(__file__))


def sect_resp(kind, fr, q, g, z):
    b, a = biquad(kind, fr, q, g)
    return (b[0] + b[1] * z + b[2] * z * z) / (a[0] + a[1] * z + a[2] * z * z)


def model_db(secs, focus, z):
    H = np.ones_like(z)
    for s in secs:
        g = s[3] + s[4] * focus / 50.0 if s[0] in ('pk', 'ls', 'hs') else 0.0
        H = H * sect_resp(s[0], s[1], s[2], g, z)
    return 20 * np.log10(np.abs(H)), H


def pack(secs):
    p = []
    for s in secs: p += [np.log(s[1]), np.log(s[2])] + (list(s[3:5]) if s[0] in ('pk', 'ls', 'hs') else [])
    return np.array(p, float)


def unpack(kinds, p):
    out, i = [], 0
    for k in kinds:
        if k in ('pk', 'ls', 'hs'): out.append([k, float(np.exp(p[i])), float(np.exp(p[i + 1])), float(p[i + 2]), float(p[i + 3])]); i += 4
        else: out.append([k, float(np.exp(p[i])), float(np.exp(p[i + 1]))]); i += 2
    return out


def bounds(kinds):
    lo, hi = [], []
    for k in kinds:
        lo += [np.log(10), np.log(0.1)] + ([-40, -40] if k in ('pk', 'ls', 'hs') else [])
        hi += [np.log(23900), np.log(30)] + ([40, 40] if k in ('pk', 'ls', 'hs') else [])
    return np.array(lo), np.array(hi)


def minphase_excess(H):
    N = 2 * (len(H) - 1)
    logm = np.log(np.maximum(np.abs(H), 1e-12))
    c = np.fft.ifft(np.concatenate([logm, logm[-2:0:-1]])).real
    w = np.zeros(N); w[0] = 1; w[1:N // 2] = 2; w[N // 2] = 1
    return H / np.exp(np.fft.fft(c * w))[:len(H)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--rounds', type=int, default=12)
    ap.add_argument('--allpass', type=int, default=4)
    a = ap.parse_args()
    d = load()
    f_all = d['f']
    focus = sorted(int(k) for k in d.files if k != 'f')
    sel = np.unique(np.round(np.geomspace(20, 22000, 500) / (f_all[1] - f_all[0])).astype(int))
    f = f_all[sel]; z = np.exp(-1j * 2 * np.pi * f / FS)
    meas = np.array([20 * np.log10(np.abs(d[str(fo)][sel])) for fo in focus])
    w = np.where(f < 40, 0.3, 1.0)                                  # the deep high-pass region is noisy

    secs = [['hp', 45.0, 2.0], ['hp', 120.0, 0.6], ['lp', 21000.0, 0.7]]
    def fit(secs):
        kinds = [s[0] for s in secs]
        lo, hi = bounds(kinds)
        def res(p):
            ss = unpack(kinds, p)
            return np.concatenate([(model_db(ss, fo, z)[0] - meas[k]) * w for k, fo in enumerate(focus)])
        r = least_squares(res, np.clip(pack(secs), lo + 1e-9, hi - 1e-9), bounds=(lo, hi), max_nfev=4000, x_scale='jac')
        return unpack(kinds, r.x), np.sqrt(np.mean(r.fun ** 2))
    secs, err = fit(secs)
    print(f'start: rms {err:.3f} dB')
    for rnd in range(a.rounds):
        e = np.array([model_db(secs, fo, z)[0] - meas[k] for k, fo in enumerate(focus)])
        joint = np.mean(np.abs(e), axis=0) * w
        i = int(np.argmax(joint))
        # slope of the residual against Focus at that frequency: the new peak's b
        b = float(np.polyfit(np.array(focus) / 50.0, -e[:, i], 1)[0])
        a0 = float(-np.mean(e[:, i]))
        best = None
        for q in (0.7, 2.0, 5.0):
            trial, terr = fit(secs + [['pk', float(f[i]), q, a0, b]])
            if best is None or terr < best[1]: best = (trial, terr)
        secs, err = best
        print(f'round {rnd + 1}: peak near {f[i]:.0f} Hz, rms {err:.3f} dB')
    for k, fo in enumerate(focus):
        e = model_db(secs, fo, z)[0] - meas[k]
        print(f'focus {fo:4d}: rms {np.sqrt(np.mean((e * w) ** 2)):.3f} dB, max {np.max(np.abs(e[f > 40])):.3f} dB (above 40 Hz)')

    # the excess phase, fixed: delay + all-passes (fitted where the response is not deep in the high-pass)
    ex = np.array([np.angle(minphase_excess(d[str(fo)])[sel]) for fo in focus])
    exc = np.angle(np.mean(np.exp(1j * ex), axis=0))
    m = f > 60
    def ap_resp(p):
        H = np.exp(-1j * 2 * np.pi * f / FS * p[0])
        for k in range(a.allpass):
            fr, q = np.exp(p[1 + 2 * k]), np.exp(p[2 + 2 * k])
            w0 = 2 * np.pi * fr / FS; c = np.cos(w0); al = np.sin(w0) / (2 * q)
            bb = np.array([1 - al, -2 * c, 1 + al]); aa = np.array([1 + al, -2 * c, 1 - al])
            H = H * (bb[0] + bb[1] * z + bb[2] * z * z) / (aa[0] + aa[1] * z + aa[2] * z * z)
        return H
    best = None
    rng = np.random.default_rng(0)
    for trial in range(30):
        p0 = [rng.uniform(0, 8)] + sum([[np.log(rng.uniform(100, 20000)), np.log(rng.uniform(0.3, 3))] for _ in range(a.allpass)], [])
        lo = [0] + [np.log(20), np.log(0.1)] * a.allpass; hi = [40] + [np.log(23900), np.log(20)] * a.allpass
        r = least_squares(lambda p: np.angle(ap_resp(p)[m] * np.exp(-1j * exc[m])), p0, bounds=(lo, hi), max_nfev=3000)
        e = np.degrees(np.sqrt(np.mean(r.fun ** 2)))
        if best is None or e < best[1]: best = (r.x, e)
    p = best[0]
    print(f'excess phase: delay {p[0]:.3f} samples, rms error {best[1]:.2f} deg; all-passes ' +
          ', '.join(f'{np.exp(p[1 + 2 * k]):.1f} Hz Q {np.exp(p[2 + 2 * k]):.3f}' for k in range(a.allpass)))
    # complex check of the whole model against the measurement
    for k, fo in enumerate(focus):
        Hm = model_db(secs, fo, z)[1] * ap_resp(p)
        e = Hm / d[str(fo)][sel]
        good = f > 60
        print(f'focus {fo:4d}: complex error {20 * np.log10(np.sqrt(np.mean(np.abs(e[good] - 1) ** 2))):.1f} dB above 60 Hz')
    json.dump({'sections': secs, 'delay': float(p[0]),
               'allpass': [[float(np.exp(p[1 + 2 * k])), float(np.exp(p[2 + 2 * k]))] for k in range(a.allpass)]},
              open(os.path.join(HERE, 'renders', 'focus_eq2.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
