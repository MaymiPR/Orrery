"""The plate's Filter, from its impulse responses (render_plate_filter.py; MEASUREMENTS.md "Reverb"):
- run to run: the 5.2 kHz impulse twice;
- is the Filter one fixed low-pass after the plate: each setting's response against the 20 kHz one through a fixed
  filter (the best per frequency over the whole response) and, in time, the spectrum of early and late windows re the
  20 kHz response's same windows (a fixed filter gives the same ratio in every window; damping in the tail gives a ratio
  that falls with time);
- does the impulse predict the noise capture (linear and still in time);
- ours (WrRender, the plate, Mix 1) beside the reference at each setting.

    python probe_plate_filter.py
"""
import os
import numpy as np
from scipy.signal import fftconvolve
import nulltest_lib as nl
import wr_ref as h

FS = 48000
REF = os.path.join(h.ROOT, 'reference', 'Wraith')
HZ = [2000, 5206, 8042, 11425, 20000]
BANDS = [(500, 1000), (1000, 2000), (2000, 4000), (4000, 6000), (6000, 9000), (9000, 13000), (13000, 20000)]
WIN = [(0.0, 0.05), (0.05, 0.2), (0.2, 0.5), (0.5, 1.0), (1.0, 2.0)]


def ir(hz, b=''):
    return np.load(os.path.join(REF, f'plate_filter_{hz}{b}.npy')).astype(float)


def band_db(x, lo, hi):
    X = np.abs(np.fft.rfft(x, 1 << 17)) ** 2; f = np.fft.rfftfreq(1 << 17, 1 / FS)
    return 10 * np.log10(X[(f >= lo) & (f < hi)].sum() + 1e-30)


def ours(hz):
    x = np.zeros(int(4.0 * FS), np.float32); x[0] = 0.5
    y = h.render_many([dict(x=nl.stereo(x), norm=dict(h.ONLY('REV'), **{'Reverb Type': 1.0, 'Reverb Mix': 1.0}),
                            params={'Reverb Filter': float(hz)})], 'model')[0]
    return y.astype(float) / 0.5


def main():
    a, b = ir(5206), ir(5206, '_b')
    print(f'run to run (5.2 kHz twice): {10 * np.log10(np.sum((a - b) ** 2) / np.sum(a ** 2) + 1e-30):.1f} dB')
    full = ir(20000)
    print('\nthe reference: each Filter setting re 20 kHz, per band (dB), in time windows (s)')
    print('window       ' + ' '.join(f'{lo // 1000 if lo >= 1000 else lo}-{hi // 1000}k'.rjust(8) for lo, hi in BANDS))
    for hz in HZ[:-1]:
        y = ir(hz)
        for t0, t1 in WIN:
            s = slice(int(t0 * FS), int(t1 * FS))
            print(f'{hz:5d} {t0:.2f}-{t1:.2f} ' + ' '.join(f'{band_db(y[0, s], lo, hi) - band_db(full[0, s], lo, hi):8.1f}' for lo, hi in BANDS))
    # does the impulse at 11.4 kHz predict the noise capture
    xn = nl.noise(3.0, -18, seed=31); xn = (xn[0] if np.ndim(xn) == 2 else xn).astype(float)
    yn = np.load(os.path.join(REF, 'plate_filter_noise_11425.npy')).astype(float)
    y = ir(11425)
    pred = np.stack([fftconvolve(xn, y[c])[:len(xn)] for c in (0, 1)])
    n = min(pred.shape[1], yn.shape[1])
    print(f'\nthe 11.4 kHz impulse predicts the noise capture to {nl.residual_db(yn[:, FS // 2:n], pred[:, FS // 2:n]):.1f} dB')
    # ours at each setting, by the same windows
    print('\nours re the reference at each setting: whole response null, and level per band (dB) in the first and a late window')
    for hz in HZ:
        o, r = ours(hz), ir(hz)
        n = min(o.shape[1], r.shape[1])
        out = [f'null {nl.residual_db(r[:, :n], o[:, :n]):6.1f}']
        for t0, t1 in ((0.0, 0.05), (0.5, 1.0)):
            s = slice(int(t0 * FS), int(t1 * FS))
            out.append(f'{t0:.2f}-{t1:.2f}: ' + ' '.join(f'{band_db(o[0, s], lo, hi) - band_db(r[0, s], lo, hi):+5.1f}' for lo, hi in BANDS))
        print(f'{hz:5d} ' + ' | '.join(out), flush=True)


if __name__ == '__main__':
    main()
