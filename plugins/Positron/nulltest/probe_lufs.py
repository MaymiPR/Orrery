"""Probe for the I/O readouts in short-term LUFS mode (the reference's settings page, I/O metering: Short-term LUFS &
Peak): tones at 1 kHz, 100 Hz and 10 kHz and pink noise, all at -20 dBFS, a pink-noise step from -30 to -10 dBFS and
silence after each part, so the window and the decay show. Also the expected short-term loudness (ITU-R BS.1770
K-weighting, 3 s window) of the signal on one channel and on both.

    python probe_lufs.py                         writes renders/work/lufs_probe.f32 (mono float32 48 kHz) and .json
    RefCapture "<reference.vst3>" "<reference name>" film.raw in=<that file> rows=0,0.32
    python probe_lufs.py --expected              per segment: the expected short-term LUFS at its end"""
import json, os, sys
import numpy as np
from scipy.signal import lfilter
import po_ref

FS = po_ref.FS
OUT = os.path.join(po_ref.WORK, 'lufs_probe')


def kweight(x):
    """BS.1770 K-weighting at 48 kHz: the high shelf, then the high-pass (the standard's coefficients)"""
    b1, a1 = [1.53512485958697, -2.69169618940638, 1.19839281085285], [1.0, -1.69065929318241, 0.73248077421585]
    b2, a2 = [1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621]
    return lfilter(b2, a2, lfilter(b1, a1, x))


def short_term(x, channels=2):
    """short-term loudness (LUFS) over the last 3 s at every sample, the same signal on `channels` channels"""
    y = kweight(x) ** 2; w = 3 * FS
    c = np.concatenate([[0.0], np.cumsum(y)])
    ms = (c[w:] - c[:-w]) / w
    return np.concatenate([np.full(w - 1, -np.inf), -0.691 + 10 * np.log10(channels * np.maximum(ms, 1e-30))])


def signal():
    t = lambda s: np.arange(int(s * FS)) / FS
    tone = lambda f, s, db: 10 ** (db / 20) * np.sin(2 * np.pi * f * t(s))
    pink = lambda s, db, seed: po_ref.noise(s, db, seed=seed, pink=True)
    sil = lambda s: np.zeros(int(s * FS))
    segs = [('silence', sil(2)), ('1 kHz -20', tone(1000, 5, -20)), ('silence', sil(4)), ('pink -20', pink(5, -20, 1)),
            ('silence', sil(4)), ('100 Hz -20', tone(100, 5, -20)), ('silence', sil(4)), ('10 kHz -20', tone(10000, 5, -20)),
            ('silence', sil(4)), ('pink -30', pink(4, -30, 2)), ('pink -10', pink(5, -10, 3)), ('silence', sil(6))]
    x = np.concatenate([s for _, s in segs]).astype(np.float32)
    meta, pos = [], 0
    for name, s in segs:
        meta.append(dict(label=name, start=pos / FS, secs=len(s) / FS)); pos += len(s)
    return x, meta


if __name__ == '__main__':
    x, meta = signal()
    if '--expected' in sys.argv:
        st1, st2 = short_term(x.astype(np.float64), 1), short_term(x.astype(np.float64), 2)
        for m in meta:
            i = int((m['start'] + m['secs']) * FS) - 1
            print(f"{m['label']:12s} ends at {m['start'] + m['secs']:5.1f} s: short-term {st1[i]:7.2f} LUFS (one channel), {st2[i]:7.2f} (both)")
        raise SystemExit
    os.makedirs(po_ref.WORK, exist_ok=True)
    x.tofile(OUT + '.f32'); json.dump(meta, open(OUT + '.json', 'w'), indent=1)
    print(OUT + '.f32', f'{len(x) / FS:.1f} s')
