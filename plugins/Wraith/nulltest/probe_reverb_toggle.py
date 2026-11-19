"""What the reverb does when it is switched off and on again while a tail rings (MEASUREMENTS.md "Reverb"): a noise
burst, the reverb fully wet, the stage's power (or, with --bypass, the plug-in's bypass) switched off shortly after
the burst and on again half a second later, and a second burst after that.
The output after the switch back on is compared with three stand-ins, all from a render that never switched:
    ran on    the same samples of that render (the reverb kept computing while it was off)
    paused    that render from the moment of the switch off (the state was frozen and carried on)
    cleared   a render whose input is silent before the switch back on (the state was cleared)
Prints, for the reference and for our processor, the level after the switch back on and the residual against each
stand-in, in dB.

    python probe_reverb_toggle.py [--fs 48000]
"""
import argparse
import numpy as np
import nulltest_lib as nl
import wr_ref as h

BLOCK = 512


def db(a, b=None):
    e = float(np.sum(np.asarray(a, np.float64) ** 2))
    if b is None:
        return 10 * np.log10(e + 1e-30)
    return 10 * np.log10(e / (float(np.sum(np.asarray(b, np.float64) ** 2)) + 1e-30) + 1e-30)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--fs', type=int, default=48000)
    ap.add_argument('--bypass', action='store_true', help='switch the whole plug-in off and on with Bypass instead')
    a = ap.parse_args()
    fs = a.fs
    n = 4 * fs
    x = np.zeros((2, n), np.float32)
    burst = nl.stereo(nl.noise(0.5, -18.0, fs=fs)).astype(np.float32)
    start = int(0.2 * fs)
    x[:, start:start + burst.shape[1]] = burst
    second = int(1.5 * fs)
    x[:, second:second + burst.shape[1]] = 0.5 * burst[:, ::-1]
    off = int(0.75 * fs) // BLOCK * BLOCK
    on = int(1.25 * fs) // BLOCK * BLOCK
    base = dict(x=x, norm=h.ONLY('REV'), params={'Reverb Mix': 1.0, 'Reverb Filter': 20000})
    if fs in h.SETTLE:
        base['settle'] = h.SETTLE[fs]
    name, away, back = ('Bypass', 1.0, 0.0) if a.bypass else ('Reverb State', 0.0, 1.0)
    fresh = x.copy()
    fresh[:, :on] = 0.0
    jobs = [base, dict(base, auto=[(name, off, away), (name, on, back)]), dict(base, x=fresh)]
    span = int(1.5 * fs)
    print(f'{name}, {fs} Hz: off at {off / fs:.3f} s, on at {on / fs:.3f} s; windows of 1.5 s after the switch on')
    for plugin in ('ref', 'model'):
        steady, toggled, cleared = h.render_many(jobs, plugin, fs=fs, block=BLOCK, cache=plugin == 'ref')
        after = toggled[:, on:on + span]
        ran, paused = steady[:, on:on + span], steady[:, off:off + span]
        print(f'{plugin:6s} level after the switch on {db(after):7.1f} dB (never switched: {db(ran):7.1f} dB; '
              f'while off: {db(toggled[:, off + BLOCK:on]):7.1f} dB)   residual against ran on {db(after - ran, ran):7.1f} dB, '
              f'paused {db(after - paused, paused):7.1f} dB, cleared {db(after - cleared[:, on:on + span], cleared[:, on:on + span]):7.1f} dB')


if __name__ == '__main__':
    main()
