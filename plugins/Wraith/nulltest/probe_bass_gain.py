"""The Character stage's steady gain on bass tones, reference against our processor (MEASUREMENTS.md "Character"): a tone
at -10 dBFS in the compression range, its gain read through the side channel (probe_side.gain_traj).
Relative to 1 kHz, the difference says how much louder (negative) or quieter (positive) our compressor's detector hears
that frequency than the reference's, divided by the curve's slope there (about 0.93). A sharper reading of the
detector's weighting in the bass than probe_det_weight.py.

    python probe_bass_gain.py
"""
import os
import numpy as np
import nulltest_lib as nl
from probe_side import gain_traj
import ts as h

FS = 48000
FREQS = [30, 40, 50, 60, 70, 80, 100, 130, 160, 200, 300, 1000]
FOCUS = [-50, 8, 50]


def main():
    out = {}
    for foc in FOCUS:
        err = []
        for f in FREQS:
            x = nl.tone(f, 1.0, -10.0)
            zr = gain_traj(x, FS, 'ref', Compression=0, Focus=foc); zo = gain_traj(x, FS, 'model', Compression=0, Focus=foc)
            s = slice(len(x) // 2, len(x) - 2000)
            err.append(np.mean(20 * np.log10(np.abs(zo[s]))) - np.mean(20 * np.log10(np.abs(zr[s]))))
        err = np.array(err) - err[-1]
        out[f'f{foc}'] = err
        print(f'focus {foc:+3d}: ours - ref gain re 1 kHz', ' '.join(f'{f}:{v:+.2f}' for f, v in zip(FREQS, err)), flush=True)
    np.savez(os.path.join(h.ROOT, 'measurements', 'Wraith', 'char', 'bass_gain_err.npz'), freqs=FREQS, **out)


if __name__ == '__main__':
    main()
