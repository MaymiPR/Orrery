"""Character stage, the Focus EQ's top end per sample rate (MEASUREMENTS.md "Character"). The two sections
that shape the top of the stage's response (a broad low-pass and a narrow cut, fitted at 48 kHz just under its Nyquist)
do not carry over to other rates: at 44.1 kHz the stage's response is 0.3 to 0.6 dB higher at 10 to 15 kHz with 6 to 8
degrees more phase than ours, at 88.2 and 96 kHz 1 to 2 dB lower. They are refitted per rate to the stage's complex
response there (side-channel clicks, probe_side.py eq), every other section fixed, and stored per rate in
renders/focus_eq2_rates.json for make_focus_eq.py (Character.h uses the nearest rate in the table).

With all sections (MEASUREMENTS.md 4.2): at 44.1, 88.2 and 96 kHz every section from 80 Hz up and the four all-passes are
refitted per rate (--all --ap), the model's level per Focus value held to the 48 kHz model's (--level, the EQ sits
before the detector), its gain real (--real), the bins weighted as pink noise is (--pink), over the whole band
(--wide, up to 0.48 fs). One run per rate, merged with focus_rates_lib.py.

    python fit_focus_hf.py [44100 48000 88200 96000]
    python fit_focus_hf.py --all --ap --level --real --wide --pink 96000 focus_eq2_rates_q96.json
    --delay: a fractional delay per rate in the model as well (0.01 to 0.03 samples; not in the plug-in)
"""
import json, os, sys
import numpy as np
from scipy.optimize import least_squares
import probe_side as ps

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'renders', 'focus_eq2_rates.json')
FOCUS = [-50, -30, -10, 0, 8, 20, 35, 50]


def section(kind, fs, f0, q, g, z):
    """RBJ, w0 = 2 pi f / fs (Source/dsp/Biquad.h), f clamped below Nyquist as Character.h does"""
    A = 10 ** (g / 40); w0 = 2 * np.pi * min(f0, 0.49 * fs) / fs; c = np.cos(w0); s = np.sin(w0); al = s / (2 * q)
    if kind == 'pk': b, a = [1 + al * A, -2 * c, 1 - al * A], [1 + al / A, -2 * c, 1 - al / A]
    elif kind == 'hp': b, a = [(1 + c) / 2, -(1 + c), (1 + c) / 2], [1 + al, -2 * c, 1 - al]
    else: b, a = [(1 - c) / 2, 1 - c, (1 - c) / 2], [1 + al, -2 * c, 1 - al]
    return (b[0] + b[1] * z + b[2] * z * z) / (a[0] + a[1] * z + a[2] * z * z)


def model(secs, aps, fs, focus, z):
    H = np.ones_like(z)
    for s in secs: H = H * section(s[0], fs, s[1], s[2], s[3] + s[4] * focus / 50 if s[0] == 'pk' else 0.0, z)
    for f0, q in aps:
        w0 = 2 * np.pi * f0 / fs; c = np.cos(w0); al = np.sin(w0) / (2 * q)
        H = H * ((1 - al) - 2 * c * z + (1 + al) * z * z) / ((1 + al) - 2 * c * z + (1 - al) * z * z)
    return H


def thiran(d, z):
    """a first-order all-pass delaying low frequencies by d samples (--delay); z = e^-jw"""
    if d <= 0: return np.ones_like(z)
    a = (1 - d) / (1 + d)
    return (a + z) / (1 + a * z)


def main():
    every = '--all' in sys.argv        # every section per rate, on all eight Focus values
    wide = '--wide' in sys.argv        # the whole band up to 0.45 fs (not only up to 20 kHz), from the 48 kHz sections
    with_ap = '--ap' in sys.argv       # the four all-passes per rate as well
    # --level: hold the model's level per Focus value to the shipped 48 kHz model's (only the gain's phase free). The
    # Focus EQ sits before the detector, so a level the fit is free to move changes what the compressor hears.
    level = '--level' in sys.argv
    out_name = next((a for a in sys.argv[1:] if a.endswith('.json')), None)
    m0 = json.load(open(OUT))
    secs = [list(x) + [0.0, 0.0] if len(x) == 3 else list(x) for x in m0['sections']]
    aps = m0['allpass']
    top = [i for i, s in enumerate(secs) if s[1] > 20000]            # the two sections above 20 kHz
    rates = m0.get('rates', {})
    g48 = {}
    if level:                          # the shipped 48 kHz model's gain against the reference, per Focus value
        s48 = [list(s) for s in secs]
        for i, v in rates.get('48000', {}).items(): s48[int(i)][1:5] = v
        r48 = ps.eq_ir(48000, 'ref', focus=FOCUS)
        for F in FOCUS:
            A = np.fft.rfft(r48[F][0]); f = np.fft.rfftfreq(len(r48[F][0]), 1 / 48000); m = (f > 30) & (f < 20000)
            M = model(s48, aps, 48000, F, np.exp(-1j * 2 * np.pi * f[m] / 48000))
            g48[F] = abs(np.sum(A[m] * np.conj(M)) / np.sum(np.abs(M) ** 2))

    # --real: a real, positive gain per Focus value (a constant phase across the band is nothing filters can make);
    # --delay: a fractional delay per rate (samples) in the model, fitted with the rest
    real, with_delay = '--real' in sys.argv, '--delay' in sys.argv
    pink = '--pink' in sys.argv        # weight the bins as pink noise does (1 / f in power): the lows count as in music

    def gain(A, M, F):
        if level and real: return g48[F]
        g = np.sum(A * np.conj(M)) / np.sum(np.abs(M) ** 2)
        if level: return g / abs(g) * g48[F]
        return abs(g) if real else g

    for fs in [int(v) for v in sys.argv[1:] if v.isdigit()] or [44100, 48000, 88200, 96000]:
        focus = FOCUS if fs in (44100, 48000) or every else [-50, 8, 50]
        # every section but the ones under 80 Hz: the clicks see nothing under 30 Hz, and a section there is the same
        # filter in Hz at any rate, so it keeps its 48 kHz values
        fit = [i for i, s in enumerate(secs) if s[1] >= 80.0] if every else top
        base = [list(s) for s in secs]
        if not wide:
            for i, v in rates.get(str(fs), {}).items(): base[int(i)][1:5] = v      # this rate's top end as the start
        r = ps.eq_ir(fs, 'ref', focus=focus)
        data = []
        top_hz = 0.48 * fs if wide else min(20000, 0.45 * fs)
        for F in focus:
            A = np.fft.rfft(r[F][0]); f = np.fft.rfftfreq(len(r[F][0]), 1 / fs); m = (f > 30) & (f < top_hz)
            data.append((F, A[m], np.exp(-1j * 2 * np.pi * f[m] / fs), 1 / np.sqrt(f[m]) if pink else np.ones(int(m.sum()))))

        def unpack(p):
            ss = [list(s) for s in base]; j = 0
            for i in fit:
                ss[i][1] = float(np.exp(p[j])); ss[i][2] = float(np.exp(p[j + 1])); j += 2
                if ss[i][0] == 'pk': ss[i][3], ss[i][4] = float(p[j]), float(p[j + 1]); j += 2
            al = [[float(np.exp(p[j + 2 * k])), float(np.exp(p[j + 2 * k + 1]))] for k in range(len(aps))] if with_ap else aps
            d = float(p[-1]) if with_delay else 0.0
            return ss, al, d

        def errs(ss, al, d=0.0):
            out = []
            for F, A, z, w in data:
                M = model(ss, al, fs, F, z) * thiran(d, z) * w; g = gain(A * w, M, F)
                out.append(10 * np.log10(np.sum(np.abs(A * w - g * M) ** 2) / np.sum(np.abs(A * w) ** 2)))
            return out

        def res(p):
            ss, al, d = unpack(p); out = []
            for F, A, z, w in data:
                M = model(ss, al, fs, F, z) * thiran(d, z) * w; g = gain(A * w, M, F)
                e = (A * w - g * M) / np.sqrt(np.sum(np.abs(A * w) ** 2)); out += [e.real, e.imag]
            return np.concatenate(out)

        p0, lo, hi = [], [], []
        for i in fit:
            s = base[i]
            flo = 1000.0 if i in top else 20.0                        # nothing below the band the clicks measure
            p0 += [np.log(s[1]), np.log(s[2])]; lo += [np.log(flo), np.log(0.1)]; hi += [np.log(0.499 * fs), np.log(2.0 if s[0] != 'pk' else 80.0 if i in top else max(8.0, 1.5 * s[2]))]
            if s[0] == 'pk': p0 += [s[3], s[4]]; lo += [-90.0, -60.0] if i in top else [-30.0, -30.0]; hi += [60.0, 60.0] if i in top else [30.0, 30.0]
        if with_ap:
            for f0, q in aps: p0 += [np.log(f0), np.log(q)]; lo += [np.log(20.0), np.log(0.1)]; hi += [np.log(0.499 * fs), np.log(5.0)]
        if with_delay: p0 += [0.3]; lo += [0.0]; hi += [2.0]
        lo, hi = np.array(lo), np.array(hi)
        r = least_squares(res, np.clip(p0, lo + 1e-6, hi - 1e-6), bounds=(lo, hi))
        ss, al, d = unpack(r.x)
        print(f'{fs}: before', ' '.join(f'{v:.1f}' for v in errs(base, aps)), '| after', ' '.join(f'{v:.1f}' for v in errs(ss, al, d)),
              f'| delay {d:+.3f} samples' if with_delay else '', flush=True)
        rates[str(fs)] = {str(i): [float(v) for v in ss[i][1:5]] for i in fit}
        if with_ap: m0.setdefault('rate_allpass', {})[str(fs)] = al
        if with_delay: m0.setdefault('rate_delay', {})[str(fs)] = d
    m0['rates'] = rates
    out = os.path.join(HERE, 'renders', out_name) if out_name else OUT
    json.dump(m0, open(out, 'w'), indent=1)
    print('wrote', os.path.basename(out))


if __name__ == '__main__':
    main()
