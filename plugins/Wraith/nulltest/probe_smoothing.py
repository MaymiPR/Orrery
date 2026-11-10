"""How the reference moves to a new parameter value: a steady tone, one parameter jumps at a block boundary
(automation), and the gain is read sample by sample (MEASUREMENTS.md "Smoothing").

    python probe_smoothing.py [--plugin ref|model]
"""
import argparse
import numpy as np
import wr_ref as h

FS = 48000
AT = 47 * 512        # a block boundary


def gain_trace(y, x):
    # the tone's instantaneous gain from the analytic signals (both at 1 kHz)
    from scipy.signal import hilbert
    return np.abs(hilbert(y)) / np.maximum(np.abs(hilbert(x)), 1e-12)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--plugin', default='ref')
    a = ap.parse_args()
    n = FS
    t = np.arange(n) / FS
    x = (0.1 * np.sin(2 * np.pi * 1000 * t)).astype(np.float32)
    cases = [('Input Gain 0 -> +6', h.NONE, 'Input Gain', 0.75),
             ('Output Gain 0 -> -6', h.NONE, 'Output Gain', 0.25),
             ('EQ High 0.03 -> +12 (tone at 1 kHz)', h.ONLY('EQ'), 'EQ High Gain', 1.0)]
    for name, norm, pname, to in cases:
        y = h.render(x, a.plugin, norm=norm, auto=[(pname, AT, to)])
        g = 20 * np.log10(gain_trace(y[0], x))
        seg = g[AT - 64: AT + 2048]
        g0, g1 = np.median(g[AT - 2000: AT - 200]), np.median(g[AT + 8000: AT + 12000])
        frac = (seg - g0) / (g1 - g0 + 1e-12)
        def cross(level):
            i = np.argmax(frac >= level)
            return (i - 64) / FS * 1000
        print(f'{name:38s} {g0:+.2f} -> {g1:+.2f} dB; 10 % at {cross(0.1):.2f} ms, 50 % at {cross(0.5):.2f} ms, '
              f'90 % at {cross(0.9):.2f} ms, 99 % at {cross(0.99):.2f} ms')


if __name__ == '__main__':
    main()
