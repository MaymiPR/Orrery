"""Character stage (MEASUREMENTS.md "Character"): what Compression and Focus do, measured on the stage alone.

    python probe_char.py small      the small-signal response (noise at -70 / -80 dBFS) per Focus and Compression
    python probe_char.py static     the gain of a 1 kHz tone against level (staircase) per Compression
"""
import sys
import numpy as np
import nulltest_lib as nl
import wr_ref as h

FS = 48000
BANDS = (31, 63, 125, 250, 500, 1000, 2000, 4000, 8000, 12000, 16000, 20000)


def transfer(x, y, n=8192):
    from scipy.signal import csd, welch
    f, pxy = csd(x, y, fs=FS, nperseg=n)
    _, pxx = welch(x, fs=FS, nperseg=n)
    return f, pxy / pxx


def at(f, H, fr):
    return [20 * np.log10(np.abs(H[np.argmin(np.abs(f - b))])) for b in fr]


def small():
    jobs, labels = [], []
    for level in (-80.0, -70.0):
        x = nl.stereo(nl.noise(3.0, level)).astype(np.float32)
        for comp in (-50, 0, 50):
            for focus in (-50, -25, 0, 25, 50):
                jobs.append(dict(x=x, norm=h.ONLY('CHAR'), params={'Compression': comp, 'Focus': focus}))
                labels.append((level, comp, focus))
    ys = h.render_many(jobs, cache=True)
    print('level comp focus | ' + ' '.join(f'{b:>6d}' for b in BANDS) + ' | lag')
    for (level, comp, focus), j, y in zip(labels, jobs, ys):
        f, H = transfer(j['x'][0, FS // 2:], y[0, FS // 2:])
        lag = nl.find_lag(j['x'][0], y[0], 64)
        print(f'{level:5.0f} {comp:4d} {focus:5d} | ' + ' '.join(f'{v:+6.2f}' for v in at(f, H, BANDS)) + f' | {lag}')


def static():
    levels = np.arange(-60.0, 1.0, 3.0)
    x = nl.steps(list(levels), 0.4, f=1000.0)
    x = nl.stereo(x).astype(np.float32)
    jobs = [dict(x=x, norm=h.ONLY('CHAR'), params={'Compression': c, 'Focus': 0}) for c in (-50, -25, 0, 25, 50)]
    ys = h.render_many(jobs, cache=True)
    seg = int(0.4 * FS)
    print('in dBFS | gain dB at Compression -50 -25 0 25 50')
    for k, lv in enumerate(levels):
        a, b = k * seg + seg // 2, (k + 1) * seg
        g = [20 * np.log10(np.sqrt(np.mean(y[0, a:b] ** 2)) / np.sqrt(np.mean(x[0, a:b] ** 2))) for y in ys]
        print(f'{lv:6.0f} | ' + ' '.join(f'{v:+7.2f}' for v in g))



def eqshape(save=None):
    """the Focus EQ's shape where the dynamics hold a constant gain (Compression -50, noise at -38 dBFS rms)"""
    x = nl.stereo(nl.noise(6.0, -38.0)).astype(np.float32)
    focus = list(range(-50, 51, 10))
    ys = h.render_many([dict(x=x, norm=h.ONLY('CHAR'), params={'Compression': -50, 'Focus': fo}) for fo in focus], cache=True)
    out = {}
    for fo, y in zip(focus, ys):
        f, H = transfer(x[0, FS:], y[0, FS:], 16384)
        out[fo] = H
    if save: np.savez(save, f=f, **{str(k): v for k, v in out.items()})
    fr = (20, 31, 45, 63, 90, 125, 180, 250, 355, 500, 710, 1000, 1400, 2000, 2800, 4000, 5600, 8000, 11000, 16000, 20000)
    print('focus | ' + ' '.join(f'{b:>6d}' for b in fr))
    for fo in focus:
        print(f'{fo:5d} | ' + ' '.join(f'{v:+6.2f}' for v in at(f, out[fo], fr)))
    print('delta per 10 focus (dB), from -50..50 fit, and the linearity residual:')
    d = np.array([20 * np.log10(np.abs(out[fo])) for fo in focus])
    A = np.vstack([np.ones(len(focus)), np.array(focus) / 10.0]).T
    coef, res, *_ = np.linalg.lstsq(A, d, rcond=None)
    print('slope | ' + ' '.join(f'{v:+6.3f}' for v in at(f, 10 ** (coef[1] / 20), fr)))
    lin = np.max(np.abs(A @ coef - d), axis=0)
    print('nonlin| ' + ' '.join(f'{lin[np.argmin(np.abs(f - b))]:6.3f}' for b in fr))


if __name__ == '__main__':
    {'small': small, 'static': static, 'eqshape': eqshape}[sys.argv[1]]()
