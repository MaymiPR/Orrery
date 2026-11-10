"""What the Character stage's detector hears, by frequency (MEASUREMENTS.md "Character"): a mid tone stepped
up in level, its gain read through the side channel (probe_side.gain_traj, a 12 kHz probe the detector does not hear);
the level at which the gain has fallen a set amount below its quiet value is where the detector reads the same level at
every frequency. Its inverse, normalised to 1 kHz, is the detector's frequency weighting. Against it, the stage's own
response at that Focus (side-channel clicks, probe_side.py eq) says how much of the Focus EQ the detector hears.

    python probe_det_weight.py [render] [exp]    render: ref (default) or model; exp: the expander's side (the level
                                                 where the gain comes within 6 dB of its plateau from below)
"""
import os, sys
import numpy as np
import nulltest_lib as nl
from probe_side import gain_traj
import wr_ref as h

FS = 48000
FREQS = [40, 60, 100, 150, 200, 300, 500, 700, 1000, 1500, 2000, 3000, 5000, 7000, 10000, 14000]
LEVELS = np.arange(-60.0, 0.1, 2.0)
HOLD = 0.25
DROP = 6.0          # dB below the quiet gain


def weight(render='ref', comp=0, focus=8, expander=False):
    out = []
    for f in FREQS:
        x = nl.steps(list(LEVELS), HOLD, f=f)
        z = gain_traj(x, FS, render, Compression=comp, Focus=focus)
        g = 20 * np.log10(np.abs(z) + 1e-12)
        n = int(HOLD * FS)
        steady = np.array([np.median(g[k * n + n // 2: (k + 1) * n - 200]) for k in range(len(LEVELS))])
        top = steady.max()
        if expander:
            # the expander's side: the first step (from the quietest) that comes within DROP of the plateau
            above = np.where(steady > top - DROP)[0]
            k = above[0]
            if k == 0: out.append(np.nan); continue
            a, b = steady[k - 1] - (top - DROP), steady[k] - (top - DROP)
            out.append(LEVELS[k - 1] + 2.0 * a / (a - b))
            continue
        below = np.where((steady < top - DROP) & (np.arange(len(steady)) > np.argmax(steady)))[0]
        if len(below) == 0: out.append(np.nan); continue
        k = below[0]
        # interpolate the level where the gain crosses top - DROP
        a, b = steady[k - 1] - (top - DROP), steady[k] - (top - DROP)
        out.append(LEVELS[k - 1] + 2.0 * a / (a - b))
    out = np.array(out)
    return -(out - out[FREQS.index(1000)])


if __name__ == '__main__':
    render = sys.argv[1] if len(sys.argv) > 1 else 'ref'
    exp = len(sys.argv) > 2 and sys.argv[2] == 'exp'
    os.makedirs(os.path.join(h.ROOT, 'measurements', 'Wraith', 'char'), exist_ok=True)
    print('f       ' + ' '.join(f'{f:>6d}' for f in FREQS))
    res = {}
    for focus in (-50, 8, 50):
        w = weight(render, 0, focus, exp)
        res[focus] = w
        print(f'focus {focus:+3d} ' + ' '.join(f'{v:+6.1f}' for v in w), flush=True)
    np.savez(os.path.join(h.ROOT, 'measurements', 'Wraith', 'char', f'det_weight_{render}{"_exp" if exp else ""}.npz'), freqs=FREQS,
             **{f'f{k}': v for k, v in res.items()})
