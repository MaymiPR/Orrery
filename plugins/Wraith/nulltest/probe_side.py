"""The Character stage seen through the side channel (MEASUREMENTS.md "Character"). Its detector
hears the mid signal only and its one gain is applied to both channels, so with L = d + p and R = d - p the drive d
sets the gain and the side output (L - R) / 2 is that gain times the stage's linear filters applied to p alone:
    eq        clicks on the side under a steady mid drive (the gain held still): the Focus EQ's impulse response
    gain      a 12 kHz tone on the side under drums / steps on the mid: the gain trajectory, sample by sample
Data to measurements/Wraith/char.

    python probe_side.py eq [fs]
    python probe_side.py gain
"""
import os, sys
import numpy as np
import nulltest_lib as nl
import wr_ref as h

OUT = os.path.join(h.ROOT, 'measurements', 'Wraith', 'char')
FOCUS = [-50, -30, -10, 0, 8, 20, 35, 50]
PERIOD = 0.25          # s between side clicks
IRLEN = 8192


def ms(d, p):
    return np.stack([d + p, d - p]).astype(np.float32)


def eq_ir(fs=48000, render='ref', comp=-50, drive_db=-34.0, click_db=-30.0, focus=FOCUS):
    """per Focus value: the side's impulse response (mean over the clicks) and the clicks' spread (dB re the mean)"""
    secs = 6.0
    n = int(secs * fs)
    d = nl.noise(secs, drive_db, fs=fs, pink=True, seed=7)
    p = np.zeros(n, np.float32)
    at = np.arange(int(0.5 * fs), n - IRLEN, int(PERIOD * fs))
    p[at] = 10 ** (click_db / 20)
    jobs = [dict(x=ms(d, p), norm=h.ONLY('CHAR'), params={'Compression': comp, 'Focus': f}) for f in focus]
    jobs += [dict(x=ms(d, 0 * p), norm=h.ONLY('CHAR'), params={'Compression': comp, 'Focus': f}) for f in focus]
    ys = h.render_many(jobs, render, fs=fs, cache=render != 'model')
    out = {}
    for k, f in enumerate(focus):
        s = 0.5 * (ys[k][0] - ys[k][1]) - 0.5 * (ys[k + len(focus)][0] - ys[k + len(focus)][1])
        segs = np.stack([s[a:a + IRLEN] for a in at]) / 10 ** (click_db / 20)
        m = segs.mean(0)
        spread = 10 * np.log10(np.mean((segs - m) ** 2) / np.mean(m ** 2))
        out[f] = (m, spread)
    return out


def gain_traj(x_mid, fs=48000, render='ref', fp=12000.0, pdb=-46.0, **params):
    """the gain (complex amplitude of the side tone's response, relative to its median) through x_mid, per sample"""
    n = len(x_mid)
    t = np.arange(n) / fs
    p = (10 ** (pdb / 20) * np.sin(2 * np.pi * fp * t)).astype(np.float32)
    jobs = [dict(x=ms(x_mid, p), norm=h.ONLY('CHAR'), params=params), dict(x=ms(x_mid, 0 * p), norm=h.ONLY('CHAR'), params=params)]
    y, y0 = h.render_many(jobs, render, fs=fs, cache=render != 'model')
    s = 0.5 * (y[0] - y[1]) - 0.5 * (y0[0] - y0[1])
    z = s * np.exp(-2j * np.pi * fp * t) * 2 / 10 ** (pdb / 20)
    # complex demodulation: a 2-pole low-pass at 3 kHz, run forwards and backwards (no lag)
    from scipy.signal import butter, filtfilt
    b, a = butter(4, 3000 / (fs / 2))
    z = filtfilt(b, a, z.real) + 1j * filtfilt(b, a, z.imag)
    return z


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    what = sys.argv[1]
    if what == 'eq':
        fs = int(sys.argv[2]) if len(sys.argv) > 2 else 48000
        for render in ('ref', 'model'):
            r = eq_ir(fs, render)
            np.savez(os.path.join(OUT, f'eq_ir_{render}_{fs}.npz'), focus=np.array(list(r)), ir=np.stack([v[0] for v in r.values()]),
                     spread=np.array([v[1] for v in r.values()]))
            print(render, ' '.join(f'{f}:{v[1]:.1f}' for f, v in r.items()), '(spread dB)')
    elif what == 'gain':
        fs = 48000
        sigs = {'drums': nl.drums(4, -6.0), 'music': nl.stereo(nl.music(4, -10.0)).mean(0), 'steps': nl.steps([-40, -10, -30, -6, -50, -20, -12, -60], 0.5)}
        for name, x in sigs.items():
            for comp, foc in ((0, 8), (50, -30), (-50, 50)):
                zr = gain_traj(x, fs, 'ref', Compression=comp, Focus=foc)
                zo = gain_traj(x, fs, 'model', Compression=comp, Focus=foc)
                np.savez(os.path.join(OUT, f'gain_{name}_{comp}_{foc}.npz'), ref=zr, ours=zo, x=x)
                sk = fs // 10
                d = 20 * np.log10(np.abs(zr[sk:]) / np.abs(zo[sk:]))
                print(f'{name:6s} comp {comp:+3d} focus {foc:+3d}: |g| ref/ours median {np.median(d):+.2f} dB, '
                      f'p5 {np.percentile(d, 5):+.2f}, p95 {np.percentile(d, 95):+.2f}', flush=True)
