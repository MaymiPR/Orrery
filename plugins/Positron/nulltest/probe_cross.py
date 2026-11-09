"""Cross-band probe: quiet tones above the mid band (-50 dBFS each, too quiet for the high band's detector) under a
loud masker below 1.5 kHz (lowpassed pink noise), character only. The tones' gain (lock-in over the settled part) in
the reference and in ours, against the same tones alone. Shows whether the bands below change what happens up there.

    python probe_cross.py [amount 0..1] [masker dBFS RMS ...]"""
import sys
import numpy as np
from scipy.signal import butter, sosfiltfilt
import tgp

FS = tgp.FS; PRE = 2 * FS; SECS = 4
FREQS = [1500.0, 2200.0, 2700.0, 3300.0, 4100.0, 5300.0, 6700.0, 8300.0, 11100.0, 14300.0]


def lockin(y, f, a, b):
    t = np.arange(a, b) / FS
    return 2 * np.abs(np.mean(y[a:b] * np.exp(-2j * np.pi * f * t)))


if __name__ == '__main__':
    amt = float(sys.argv[1]) if len(sys.argv) > 1 else 0.5
    levels = [float(v) for v in sys.argv[2:]] or [-30.0, -18.0, -12.0, -6.0]
    n = PRE + SECS * FS; t = np.arange(n) / FS
    probes = sum(10 ** (-50 / 20) * np.sin(2 * np.pi * f * t + 1.7 * i) for i, f in enumerate(FREQS))
    m = sosfiltfilt(butter(8, 1000.0, 'low', fs=FS, output='sos'), tgp.noise(n / FS, 0, seed=7, pink=True))
    m /= np.sqrt(np.mean(m ** 2))
    jobs = [dict(x=probes.astype(np.float32), norm={**tgp.CHAR_ONLY, 'Character': amt}, raw=True)]
    for L in levels:
        jobs.append(dict(x=(probes + m * 10 ** (L / 20)).astype(np.float32), norm={**tgp.CHAR_ONLY, 'Character': amt}, raw=True))
    r = tgp.render_many(jobs, 'ref', cache=True); o = tgp.render_many(jobs, 'model')
    a, b = PRE + FS // 2, n
    g = lambda ys: np.array([[20 * np.log10(lockin(y[0], f, a, b) / 10 ** (-50 / 20)) for f in FREQS] for y in ys])
    gr, go = g(r), g(o)
    print('probe Hz        ' + ' '.join(f'{f:7.0f}' for f in FREQS))
    print('alone  ref      ' + ' '.join(f'{v:+7.3f}' for v in gr[0]))
    print('       ours-ref ' + ' '.join(f'{v:+7.3f}' for v in go[0] - gr[0]))
    for i, L in enumerate(levels):
        print(f'masker {L:+.0f} ref-alone ' + ' '.join(f'{v:+7.3f}' for v in gr[i + 1] - gr[0]))
        print(f'           ours-alone ' + ' '.join(f'{v:+7.3f}' for v in go[i + 1] - go[0]))
