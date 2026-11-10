"""Experiment: a first-order highpass in front of the mid band's detector only (0 dB at 700 Hz), no law refitted,
the character section in Python (charmodel_lib.py with the plug-in's table) against the reference on program signals.

    python probe_mid_det.py [amount 0..1] fc ...          residual per signal (dB) for each corner, 0 = none
(fc/2: a second-order Butterworth highpass instead, also 0 dB at 700 Hz)"""
import sys
import numpy as np
from scipy.signal import lfilter
import po_ref, nulltest as N, null_stress as S, charmodel_lib as CM, ident_lib as I, charsim_lib as C
from measure_high_gain_noise import header_laws

FS = po_ref.FS


def hp(x, fc, f0=700.0, order=1):
    if order == 2:
        from scipy.signal import butter, sosfilt, sosfreqz
        sos = butter(2, fc, 'highpass', fs=FS, output='sos')
        return sosfilt(sos, x) / abs(sosfreqz(sos, [f0], fs=FS)[1][0])
    k = np.tan(np.pi * fc / FS); b = np.array([1, -1]) / (1 + k); a = np.array([1, (k - 1) / (1 + k)])
    z = np.exp(-2j * np.pi * f0 / FS); g = abs((b[0] + b[1] * z) / (a[0] + a[1] * z))
    return lfilter(b / g, a, x)


def band_det(xb, sb, law, makeup_db, width_db, fc):
    """charmodel.band with the detector's mid and side through hp(fc)"""
    p = {k: v for k, v in law.items() if k in C.NAMES}
    m, sd = 0.5 * (sb[0] + sb[1]), 0.5 * (sb[0] - sb[1])
    fc, order = (fc, 1) if not isinstance(fc, tuple) else fc
    if fc > 0: m, sd = hp(m, fc, order=order), hp(sd, fc, order=order)
    g = C.band_gain(m, p, side=sd, peak=int(law.get('peak', 0)))
    d = law.get('shapeDry', 0.0); k = law['k']
    u = g * sb; e = (1 - d) * (np.sin(k * u) / k - u)
    y = xb - sb + u + e
    M = 10 ** (makeup_db / 20); W = 10 ** (width_db / 20)
    mm, s = (0.5 * (y[0] + y[1]) + 0.5 * law.get('shapeMid', 0.0) * (e[0] + e[1])) * M, 0.5 * (y[0] - y[1]) * M * W
    return np.stack([mm + s, mm - s])


SIGS = {'pink -6': lambda: N.sig_noise(-6), 'pink -18': lambda: N.sig_noise(-18), 'music -10': lambda: N.sig_music(-10),
        'music -2': lambda: N.sig_music(-2), 'drums -6': lambda: N.sig_drums(-6), 'bass -6': lambda: S.sig_bass(-6),
        'pink -10': lambda: N.sig_noise(-10)}

if __name__ == '__main__':
    amt = float(sys.argv[1]); fcs = [(float(a.split('/')[0]), int(a.split('/')[1]) if '/' in a else 1) for a in sys.argv[2:]]
    row = int(round(amt * 16)); laws = header_laws(row)
    pad = lambda x: np.concatenate([np.zeros((2, N.PRE), np.float32), np.vstack([x, x]) if x.ndim == 1 else x], -1)
    xs = {k: pad(f()) for k, f in SIGS.items()}
    refs = po_ref.render_many([dict(x=x, norm={**po_ref.CHAR_ONLY, 'Character': amt}, raw=True) for x in xs.values()], 'ref', cache=True)
    print('fc (Hz)  ' + '  '.join(f'{k:>9}' for k in xs))
    for fc in fcs:
        out = []
        for (k, x), r in zip(xs.items(), refs):
            xb, sb = CM.prep(x)
            y = sum(band_det(xb[b], sb[b], laws[CM.NAMES[b]], I.GAINS16[b][row], CM.WIDTH[CM.NAMES[b]][row], fc if b == 1 else (0, 1)) for b in range(3))
            out.append(N.residual_db(r, y))
        print(f'{fc[0]:5.0f}/{fc[1]}  ' + '  '.join(f'{v:9.2f}' for v in out), flush=True)
