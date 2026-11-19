"""Whether the gain smoothing depends on the host's block size (MEASUREMENTS.md "Smoothing"): the input gain jumps
at a sample that is a block boundary at every size tried, while a tone plays. Prints, per block size, the residual in
the 50 ms after the jump of the reference against itself at 512, of our processor against itself at 512, and of our
processor against the reference at the same size.

    python probe_block_smoothing.py [--fs 48000]
"""
import argparse
import numpy as np
import wr_ref as h

AT = 47 * 512
SIZES = (512, 256, 128, 64, 32)


def db(a, b):
    return 10 * np.log10(float(np.sum(np.asarray(a, np.float64) ** 2)) / (float(np.sum(np.asarray(b, np.float64) ** 2)) + 1e-30) + 1e-30)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--fs', type=int, default=48000)
    a = ap.parse_args()
    fs = a.fs
    t = np.arange(int(1.5 * fs)) / fs
    x = np.tile((0.25 * np.sin(2 * np.pi * 1000.0 * t)).astype(np.float32), (2, 1))
    job = dict(x=x, norm=h.NONE, auto=[('Input Gain', AT, 0.75)])
    if fs in h.SETTLE:
        job['settle'] = h.SETTLE[fs]
    win = slice(AT, AT + int(0.05 * fs))
    out = {}
    for plugin in ('ref', 'model'):
        for b in SIZES:
            out[plugin, b] = h.render_many([job], plugin, fs=fs, block=b, cache=plugin == 'ref')[0]
    print(f'{fs} Hz, Input Gain 0.5 -> 0.75 at sample {AT}, the 50 ms after it')
    print('block   reference vs its 512   ours vs our 512   ours vs the reference')
    for b in SIZES:
        r, o = out['ref', b], out['model', b]
        print(f'{b:5d}   {db(r[:, win] - out["ref", 512][:, win], out["ref", 512][:, win]):18.1f}   '
              f'{db(o[:, win] - out["model", 512][:, win], out["model", 512][:, win]):15.1f}   {db(o[:, win] - r[:, win], r[:, win]):21.1f}')


if __name__ == '__main__':
    main()
