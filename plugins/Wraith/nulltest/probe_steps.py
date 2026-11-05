"""The Character compressor's gain after level steps and through drums (MEASUREMENTS.md "Character"),
read through the side channel (probe_side.gain_traj): the reference against our processor.

    python probe_steps.py steps [comp]     1 kHz from -40 dBFS up to a level for 1.5 s and back: the gain at set times
    python probe_steps.py drums [comp]     the gain through the drum loop: mean, spread and the error between the two
    python probe_steps.py bursts [comp]    bursts of -10 dBFS of growing length from -40 dBFS: the reduction they leave
"""
import sys
import numpy as np
import nulltest_lib as nl
import probe_side as ps

FS = 48000
AT_MS = [1, 3, 10, 30, 64, 128, 256, 512, 1000, 1450]


def gain_db(x, render, comp, focus):
    z = ps.gain_traj(np.asarray(x, np.float32), FS, render, Compression=comp, Focus=focus)
    return 20 * np.log10(np.abs(z) + 1e-12)


def steps(comp=0, focus=8):
    for lev in (-30, -20, -10, 0):
        x = nl.steps([-40, lev, -40], 1.5)
        g = {r: gain_db(x, r, comp, focus) for r in ('ref', 'model')}
        for phase, t0 in (('up', int(1.5 * FS)), ('down', int(3.0 * FS))):
            base = {r: g[r][t0 - FS // 100] for r in g}
            print(f'-40 -> {lev:+d} dBFS {phase:4s}  before: ref {base["ref"]:6.1f} model {base["model"]:6.1f} dB')
            for r in g:
                print(f'   {r:5s}', ' '.join(f'{g[r][t0 + int(a * FS / 1000)]:6.1f}' for a in AT_MS))
        print('   ms   ', ' '.join(f'{a:6d}' for a in AT_MS), flush=True)


def drums(comp=50, focus=50):
    x = nl.drums(4, -6.0)
    x = x[0] if np.ndim(x) == 2 else x
    g = {r: gain_db(x, r, comp, focus)[FS // 2:] for r in ('ref', 'model')}
    d = g['model'] - g['ref']
    print(f'drums, compression {comp:+d}, focus {focus:+d}: mean gain ref {g["ref"].mean():.2f} model {g["model"].mean():.2f} dB;'
          f' model - ref mean {d.mean():+.2f}, rms {np.sqrt(np.mean(d * d)):.2f}, 5/50/95 % {np.percentile(d, 5):+.2f}'
          f' {np.percentile(d, 50):+.2f} {np.percentile(d, 95):+.2f} dB')
    # through one bar: the gain every 10 ms
    for r in g:
        print(f'   {r:5s}', ' '.join(f'{v:5.1f}' for v in g[r][:FS // 2:FS // 100]))
    np.save(f'renders/gain_drums_c{comp}_f{focus}.npy', np.stack([g['ref'], g['model']]))


def bursts(comp=0, focus=8):
    for ms in (1, 3, 10, 30, 100, 300):
        n = int(ms * FS / 1000)
        x = np.concatenate([nl.tone(1000, 1.0, -40), nl.tone(1000, n / FS, -10), nl.tone(1000, 1.0, -40)])
        t0 = FS + n
        g = {r: gain_db(x, r, comp, focus) for r in ('ref', 'model')}
        print(f'{ms:4d} ms burst  ', ' | '.join(f'{r} before {g[r][FS - 480]:6.1f} end {g[r][t0 - 1]:6.1f} '
              f'+10 {g[r][t0 + 480]:6.1f} +100 {g[r][t0 + 4800]:6.1f} +300 {g[r][t0 + 14400]:6.1f}' for r in g), flush=True)


if __name__ == '__main__':
    what = sys.argv[1] if len(sys.argv) > 1 else 'steps'
    comp = int(sys.argv[2]) if len(sys.argv) > 2 else (50 if what == 'drums' else 0)
    {'steps': lambda: steps(comp), 'drums': lambda: drums(comp), 'bursts': lambda: bursts(comp)}[what]()
