"""The doubler's voice filter, its magnitude per frequency (MEASUREMENTS.md "Doubler"). At Stereo 1 the
side output (L - R) / 2 is g k (a - b): the two voices, delayed by c -+ d sin(...), through the same filter H. Its power
at a steady tone, averaged over whole cycles of the modulation, is (g k)^2 |H|^2 2 (1 - J0(4 pi f d)): the modulation's
part is the same on both plug-ins (same depth), so the reference's side power over ours, tone by tone, is the voice
filters' magnitude ratio |H_ref / H_ours| (times one constant, g k's ratio). Also the dry-path test at Stereo 0
(mid less the dry path holds both voices and the lows).

    python probe_dbl_voiceresp.py [--tune renders/x.json]
"""
import argparse, json
import numpy as np
import nulltest_lib as nl
import ts as h

FS = 48000
FREQS = [30, 50, 70, 100, 150, 200, 300, 400, 500, 700, 1000, 1500, 2000, 3000, 4000, 6000, 8000, 10000, 12000, 14000, 16000, 18000]
SECS = 2 / 0.502995 + 1.0          # two whole cycles of the modulation after a second of settling


def fundamental(s, f0):
    """the power of s at the tone's own frequency: the band the modulation spreads it over (f0 x 2 pi rate depth, and
    5 Hz), not its harmonics (at 30 Hz the voices' third harmonic is 8 dB above the fundamental)"""
    S = np.abs(np.fft.rfft(s.astype(float) * np.hanning(len(s)))) ** 2; f = np.fft.rfftfreq(len(s), 1 / FS)
    half = max(5.0, 1.5 * f0 * 2 * np.pi * 0.503 * 1.503e-3)
    return S[np.abs(f - f0) <= half].sum()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tune', default=None)
    a = ap.parse_args()
    tune = json.load(open(a.tune)) if a.tune else None
    xs = [nl.tone(f0, SECS, -12) for f0 in FREQS]
    jobs = [dict(x=nl.stereo(np.asarray(x, np.float32)), norm=h.ONLY('DBL'), params={'Doubler Mix': 1.0, 'Doubler Stereo': 1.0}) for x in xs]
    refs = h.render_many(jobs, 'ref', cache=True)
    ours = h.render_many([dict(j, tune=tune) if tune else j for j in jobs], 'model')
    n = int(2 / 0.502995 * FS)
    rows = []
    for f0, r, o in zip(FREQS, refs, ours):
        sr, so = 0.5 * (r[0] - r[1])[-n:], 0.5 * (o[0] - o[1])[-n:]
        rows.append((f0, 10 * np.log10(fundamental(sr, f0) / fundamental(so, f0))))
    ref1k = dict(rows)[1000]
    print('voice filter, the reference re ours (dB, re 1 kHz): ' + ' '.join(f'{f}:{v - ref1k:+.1f}' for f, v in rows))
    print(f'(at 1 kHz the side power ratio itself: {ref1k:+.2f} dB)')


if __name__ == '__main__':
    main()
