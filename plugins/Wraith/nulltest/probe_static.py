"""The Character stage's static curve per Compression setting (MEASUREMENTS.md "Character"): a 1 kHz
tone stepped in 2 dB steps of 0.5 s from -60 to 0 dBFS; the stage's gain (output over input RMS, the step's last
0.2 s) on the reference and on our processor, and the difference, per Compression value. With the drive taken out
(0.2 dB per step above -50) the curves of all Compression settings should fall on one line if the knob is the drive
only.

    python probe_static.py [--tune renders/x.json] [--focus 8] [--freq 1000]
"""
import argparse, json
import numpy as np
import nulltest_lib as nl
import ts as h

FS = 48000
LEVELS = list(np.arange(-60.0, 1.0, 2.0))
STEP = 0.5


def gains(y, x):
    out = []
    for k in range(len(LEVELS)):
        a, b = int((k * STEP + STEP - 0.2) * FS), int((k + 1) * STEP * FS)
        out.append(20 * np.log10(np.sqrt(np.mean(y[:, a:b] ** 2)) / np.sqrt(np.mean(x[:, a:b] ** 2))))
    return np.array(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tune', default=None)
    ap.add_argument('--focus', type=float, default=8)
    ap.add_argument('--freq', type=float, default=1000.0)
    a = ap.parse_args()
    tune = json.load(open(a.tune)) if a.tune else None
    x = nl.stereo(nl.steps(LEVELS, STEP, f=a.freq)).astype(np.float32)
    comps = (-50, -25, 0, 25, 50)
    jobs = [dict(x=x, norm=h.ONLY('CHAR'), params={'Compression': c, 'Focus': a.focus}) for c in comps]
    refs = h.render_many(jobs, 'ref', cache=True)
    ours = h.render_many([dict(j, tune=tune) if tune else j for j in jobs], 'model')
    print('input dBFS ' + ' '.join(f'{l:6.0f}' for l in LEVELS[::2]))
    for c, r, o in zip(comps, refs, ours):
        gr, go = gains(r, x), gains(o, x)
        drive = 0.2 * (c + 50)
        print(f'c{c:+3d} ref  ' + ' '.join(f'{v - drive:6.2f}' for v in gr[::2]) + '   (gain minus the drive)')
        print(f'     ours-ref ' + ' '.join(f'{v:6.2f}' for v in (go - gr)[::2]), flush=True)


if __name__ == '__main__':
    main()
