"""The doubler's two voices against each other (MEASUREMENTS.md "Doubler"). Their delays run in
antiphase around one centre (MEASUREMENTS.md 7.1), so twice a cycle they are equal; there the side output (L - R, Stereo 1)
holds only the voices' difference: two identical voices cancel to nothing, two different ones leave what differs.
White noise in, the side output's level in 2 ms windows over time, against the input's; the minima fall where the
modulation crosses zero.

    python probe_dbl_voices2.py
"""
import numpy as np
import nulltest_lib as nl
import ts as h

FS = 48000
RATE, PHASE = 0.502995, 0.9972           # the modulation (MEASUREMENTS.md 7.1): sin (2 pi (rate t + phase))


def main():
    from scipy.signal import butter, sosfiltfilt
    lp = butter(6, 3000, fs=FS, output='sos')            # under 3 kHz the delays' last few us between them do not count
    x = nl.noise(12.0, -18, seed=41); x = (x[0] if np.ndim(x) == 2 else x).astype(np.float32)
    xl = sosfiltfilt(lp, x.astype(float))
    w = FS // 1000                                       # 1 ms windows: the delays differ by under 5 us within one
    # the moments the delays are equal: rate t + phase = k / 2; and, between them, the extremes
    ks = np.arange(1, int(2 * RATE * len(x) / FS) + 2)
    eq = ((ks / 2 - PHASE) / RATE * FS).astype(int)
    eq = eq[(eq > FS // 2) & (eq < len(x) - w)]
    ex = ((ks / 2 + 0.25 - PHASE) / RATE * FS).astype(int)
    ex = ex[(ex > FS // 2) & (ex < len(x) - w)]
    for r in ('ref', 'model'):
        y = h.render_many([dict(x=nl.stereo(x), norm=h.ONLY('DBL'), params={'Doubler Mix': 1.0, 'Doubler Stereo': 1.0})], r, cache=r == 'ref')[0].astype(float)
        s = sosfiltfilt(lp, 0.5 * (y[0] - y[1]))
        m = sosfiltfilt(lp, 0.5 * (y[0] + y[1]))
        lvl = lambda sig, at: 10 * np.log10(np.mean([np.mean(sig[a:a + w] ** 2) for a in at]) / np.mean([np.mean(xl[a:a + w] ** 2) for a in at]))
        print(f'{r:5s} under 3 kHz, re the input: side at equal delays {lvl(s, eq - w // 2):6.1f} dB, side at the extremes {lvl(s, ex - w // 2):6.1f} dB, '
              f'mid at equal delays {lvl(m, eq - w // 2):6.1f} dB  ({len(eq)} crossings)', flush=True)


if __name__ == '__main__':
    main()
