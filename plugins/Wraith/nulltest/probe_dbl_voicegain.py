"""Each of the doubler's voices, its gain over time per band (MEASUREMENTS.md "Doubler"). White noise
in, Mix 1, Stereo 1; the input and the side output (L - R: the two voices with opposite signs) band-passed alike; per
5 ms the cross-correlation of the two around each voice's own delay (MEASUREMENTS.md 7.1's modulation) gives that voice's gain
in that band at that moment. A voice whose response does not move keeps one gain; a response that follows the voice's
own delay shows as a gain that rises and falls with it.

    python probe_dbl_voicegain.py
"""
import numpy as np
from scipy.signal import butter, sosfiltfilt
import nulltest_lib as nl
import ts as h

FS = 48000
RATE, PHASE, CENTRE, DEPTH = 0.502995, 0.9972, 7.5727, 1.5027      # as tracked (MEASUREMENTS.md 7.1; the centre includes the filters)
BANDS = [(150, 400), (400, 1000), (1000, 2500), (2500, 5000), (5000, 8000), (8000, 12000)]


def main():
    x = nl.noise(12.0, -18, seed=43); x = (x[0] if np.ndim(x) == 2 else x).astype(np.float32)
    win, hop = int(0.010 * FS), int(0.005 * FS)
    for r in ('ref', 'model'):
        y = h.render_many([dict(x=nl.stereo(x), norm=h.ONLY('DBL'), params={'Doubler Mix': 1.0, 'Doubler Stereo': 1.0})], r, cache=r == 'ref')[0].astype(float)
        s = 0.5 * (y[0] - y[1])
        print(f'{r}: each voice\'s gain in a band (dB, re its median) by its own delay, short (6.07 ms) ... long (9.08 ms)')
        for lo, hi in BANDS:
            sos = butter(4, [lo, hi], btype='band', fs=FS, output='sos')
            xb, sb = sosfiltfilt(sos, x.astype(float)), sosfiltfilt(sos, s)
            rows = {0: [], 1: []}
            for c in range(FS, len(x) - win - FS // 50, hop):
                t = (c + win / 2) / FS
                sn = np.sin(2 * np.pi * (RATE * t + PHASE))
                for v, sign in ((0, -1), (1, +1)):
                    d = (CENTRE + sign * DEPTH * sn) * 1e-3 * FS       # voice a: centre - depth sin, voice b: + (Doubler.h)
                    di = int(round(d))
                    seg = sb[c:c + win]; ref = xb[c - di:c - di + win]
                    g = np.dot(seg, ref) / np.dot(ref, ref)
                    rows[v].append((d / FS * 1e3, abs(g)))
            ga, gb = np.median([g for _, g in rows[0]]), np.median([g for _, g in rows[1]])
            out = [f'voice a over voice b {20 * np.log10(ga / gb):+5.2f} dB']
            for v in (0, 1):
                a = np.array(rows[v]); dl, gl = a[:, 0], 20 * np.log10(a[:, 1] + 1e-12)
                edges = np.linspace(CENTRE - DEPTH, CENTRE + DEPTH, 6)
                prof = [np.median(gl[(dl >= edges[k]) & (dl < edges[k + 1])]) - np.median(gl) for k in range(5)]
                out.append(f'voice {"ab"[v]}: ' + ' '.join(f'{p:+5.2f}' for p in prof))
            print(f'  {lo:5d}-{hi:5d} Hz  ' + ' | '.join(out), flush=True)


if __name__ == '__main__':
    main()
