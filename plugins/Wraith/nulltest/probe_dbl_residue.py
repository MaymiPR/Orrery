"""The doubler's voices, what a filtered delayed copy does not explain (MEASUREMENTS.md "Doubler"). The
side output (L - R, Mix 1, Stereo 1) holds the two voices with opposite signs and neither the dry path nor the lows.
Four tests on the reference, beside our processor:

    python probe_dbl_residue.py silence    the side and mid output on digital silence (a noise or a hum of its own)
    python probe_dbl_residue.py level      white noise at -40 / -28 / -16 / -4 dBFS: the voices' level against the input's,
                                            per band (a linear path scales with the input, added noise does not)
    python probe_dbl_residue.py repeat     the same input twice, fresh instances: what differs between runs
    python probe_dbl_residue.py tones      steady tones: harmonics, and sidebands other than the modulation's
"""
import sys
import numpy as np
import nulltest_lib as nl
import wr_ref as h

FS = 48000
P = {'Doubler Mix': 1.0, 'Doubler Stereo': 1.0}
BANDS = [(20, 200), (200, 1000), (1000, 4000), (4000, 8000), (8000, 12000), (12000, 16000), (16000, 24000)]


def render(x, r):
    return h.render_many([dict(x=nl.stereo(np.asarray(x, np.float32)), norm=h.ONLY('DBL'), params=P)], r, cache=r == 'ref')[0]


def side(y):
    return 0.5 * (y[0] - y[1])


def bands_db(s, ref=None):
    """the energy per band (dB re full scale), or re another signal's per band"""
    S = np.abs(np.fft.rfft(s * np.hanning(len(s)))) ** 2; f = np.fft.rfftfreq(len(s), 1 / FS)
    R = None if ref is None else np.abs(np.fft.rfft(ref * np.hanning(len(ref)))) ** 2
    out = []
    for lo, hi in BANDS:
        m = (f >= lo) & (f < hi)
        out.append(10 * np.log10((S[m].sum() + 1e-30) / ((R[m].sum() if R is not None else len(s) ** 2 / 4) + 1e-30)))
    return out


def head():
    return 'band (Hz)      ' + ' '.join(f'{lo // 1000 if lo >= 1000 else lo}-{hi // 1000}k'.rjust(8) for lo, hi in BANDS)


def silence():
    x = np.zeros(3 * FS)
    for r in ('ref', 'model'):
        y = render(x, r)[:, FS:]
        print(f'{r:5s} side rms {nl.rms_db(side(y)):7.1f} dBFS, mid rms {nl.rms_db(0.5 * (y[0] + y[1])):7.1f} dBFS, peak {20 * np.log10(np.max(np.abs(y)) + 1e-30):7.1f} dBFS')


def level():
    print(head())
    for lev in (-40, -28, -16, -4):
        x = nl.noise(4.0, lev, seed=4)
        x = x[0] if np.ndim(x) == 2 else x
        for r in ('ref', 'model'):
            s = side(render(x, r))[FS // 2:]
            print(f'{r:5s} {lev:+4d} dBFS  ' + ' '.join(f'{v:8.1f}' for v in bands_db(s, x[FS // 2:])), flush=True)


def repeat():
    x = nl.noise(4.0, -16, seed=4)
    x = x[0] if np.ndim(x) == 2 else x
    a = side(h.render_many([dict(x=nl.stereo(x), norm=h.ONLY('DBL'), params=P)], 'ref', cache=False)[0])[FS // 2:]
    b = side(h.render_many([dict(x=nl.stereo(x), norm=h.ONLY('DBL'), params=P)], 'ref', cache=False)[0])[FS // 2:]
    print('run to run, the side output: difference', f'{10 * np.log10(np.sum((a - b) ** 2) / np.sum(a ** 2) + 1e-30):.1f} dB re the side')
    print(head()); print('difference re side  ' + ' '.join(f'{v:8.1f}' for v in bands_db(a - b, a)))


def tones():
    for f0, lev in ((100, -12), (1000, -12), (5000, -12), (1000, -40)):
        x = nl.tone(f0, 4.0, lev)
        for r in ('ref', 'model'):
            s = side(render(x, r))[FS:]
            S = np.abs(np.fft.rfft(s * np.hanning(len(s)))); f = np.fft.rfftfreq(len(s), 1 / FS)
            k0 = np.argmin(np.abs(f - f0)); c = S[max(0, k0 - 40):k0 + 41].max()
            harm = [20 * np.log10(S[np.argmin(np.abs(f - j * f0)) - 3:np.argmin(np.abs(f - j * f0)) + 4].max() / c) for j in (2, 3) if j * f0 < FS / 2]
            # what lies away from the carrier: 30 Hz to 200 Hz off it (not the 0.5 Hz modulation's sidebands), and the
            # floor far from it
            off = (np.abs(f - f0) > 30) & (np.abs(f - f0) < 200)
            far = (np.abs(f - f0) > 1000) & (f > 50) & (np.abs(f - 2 * f0) > 100) & (np.abs(f - 3 * f0) > 100)
            print(f'{r:5s} {f0:5d} Hz {lev:+d} dBFS: side {nl.rms_db(s):6.1f} dBFS; H2 H3 ' + ' '.join(f'{v:6.1f}' for v in harm)
                  + f'; 30-200 Hz off the tone {20 * np.log10(S[off].max() / c):6.1f} dB; floor far from it'
                  f' {20 * np.log10(np.sqrt(np.mean(S[far] ** 2)) / c):6.1f} dB (per bin re the tone)', flush=True)


if __name__ == '__main__':
    {'silence': silence, 'level': level, 'repeat': repeat, 'tones': tones}[sys.argv[1] if len(sys.argv) > 1 else 'level']()
