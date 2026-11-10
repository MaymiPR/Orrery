"""Automation nulls: a parameter jumps at a block boundary while noise or a tone plays, reference against our
processor (MEASUREMENTS.md "Smoothing"). Prints the residual over the second after the jump.

    python null_auto.py [--fs 48000]
"""
import argparse
import numpy as np
import nulltest_lib as nl
import wr_ref as h

AT = 47 * 512


def cases():
    return [('Input Gain +6', h.NONE, 'Input Gain', 0.75),
            ('Output Gain -6', h.NONE, 'Output Gain', 0.25),
            ('EQ High +12', h.ONLY('EQ'), 'EQ High Gain', 1.0),
            ('EQ Low -12', h.ONLY('EQ'), 'EQ Low Gain', 0.0)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--fs', type=int, default=48000)
    a = ap.parse_args()
    fs = a.fs
    x = nl.stereo(nl.noise(1.5, -18.0, fs=fs)).astype(np.float32)
    jobs = [dict(x=x, norm=norm, auto=[(name, AT, to)]) for _, norm, name, to in cases()]
    ref = h.render_many(jobs, 'ref', fs=fs, cache=True)
    ours = h.render_many(jobs, 'model', fs=fs)
    for (label, *_), r, o in zip(cases(), ref, ours):
        seg = slice(AT - 256, AT + fs // 4)
        print(f'{label:16s} jump {nl.residual_db(r[:, seg], o[:, seg]):7.1f} dB   whole {nl.residual_db(r, o):7.1f} dB')


if __name__ == '__main__':
    main()
