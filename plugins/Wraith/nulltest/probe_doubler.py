"""Doubler (MEASUREMENTS.md "Doubler"): the doubler alone.

    python probe_doubler.py repeat      are two renders of one input identical (is the modulation seeded)?
    python probe_doubler.py clicks      a click every 50 ms at full wet: the voices' delays and gains over time
    python probe_doubler.py mix         the dry / wet law against Mix and what Stereo does
"""
import sys
import numpy as np
import nulltest_lib as nl
import ts as h

FS = 48000


def repeat():
    x = nl.stereo(nl.noise(3.0, -18)).astype(np.float32)
    j = dict(x=x, norm=h.ONLY('DBL'), params={'Doubler Mix': 1.0})
    a, b = h.render_many([j, dict(j)], cache=False)
    print('two renders differ by', round(nl.residual_db(a, b), 1), 'dB')


def clicks():
    n = 4 * FS; period = FS // 20
    x = np.zeros(n, np.float32); x[period::period] = 0.5
    for stereo in (1.0, 0.0):
        y = h.render_many([dict(x=nl.stereo(x), norm=h.ONLY('DBL'), params={'Doubler Mix': 1.0, 'Doubler Stereo': stereo})], cache=True)[0] / 0.5
        print(f'Stereo {stereo}:')
        for k in range(1, 12):
            seg = y[:, k * period: (k + 1) * period]
            out = []
            for ch in (0, 1):
                s = np.abs(seg[ch])
                pk = [i for i in np.argsort(s)[::-1][:40] if s[i] > 0.05 * s.max()]
                # group peaks closer than 8 samples, keep the largest of each group
                groups = []
                for i in sorted(pk, key=lambda i: -s[i]):
                    if all(abs(i - g) > 8 for g in groups): groups.append(i)
                out.append(' '.join(f'{g / FS * 1000:6.2f}ms:{seg[ch, g]:+.3f}' for g in sorted(groups)[:6]))
            print(f'  click {k:2d} at {k * period / FS:5.2f} s  L {out[0]}  |  R {out[1]}')


def mix():
    x = nl.stereo(nl.noise(3.0, -18)).astype(np.float32)
    wet = h.render_many([dict(x=x, norm=h.ONLY('DBL'), params={'Doubler Mix': 1.0})], cache=True)[0]
    for m in (0.0, 0.1, 0.3, 0.5, 1.0):
        y = h.render_many([dict(x=x, norm=h.ONLY('DBL'), params={'Doubler Mix': m})], cache=True)[0]
        # least squares y = d x + w wet
        A = np.stack([x.ravel(), wet.ravel()], 1)
        (d, w), *_ = np.linalg.lstsq(A, y.ravel(), rcond=None)
        r = y.ravel() - A @ np.array([d, w])
        print(f'Mix {m:.2f}: dry {d:.4f} wet {w:.4f}  residual {10 * np.log10(np.sum(r ** 2) / np.sum(y ** 2) + 1e-30):.1f} dB')



def trajectories(stereo=0.0, secs=4.0, show=True):
    """sub-sample delays of the two voices at every click (Stereo 0: both voices in both channels)"""
    n = int(secs * FS); period = FS // 20
    x = np.zeros(n, np.float32); x[period::period] = 0.5
    y = h.render_many([dict(x=nl.stereo(x), norm=h.ONLY('DBL'), params={'Doubler Mix': 1.0, 'Doubler Stereo': stereo})], cache=True)[0] / 0.5
    t, d1, d2 = [], [], []
    for k in range(1, n // period - 1):
        seg = y[0, k * period + int(0.004 * FS): k * period + int(0.012 * FS)]
        env = np.abs(seg)
        # the two largest separated peaks; parabolic interpolation on each
        i1 = int(np.argmax(env)); env2 = env.copy(); env2[max(0, i1 - 10): i1 + 10] = 0; i2 = int(np.argmax(env2))
        def sub(i):
            a, b, c = env[i - 1], env[i], env[i + 1]
            return i + 0.5 * (a - c) / (a - 2 * b + c) + int(0.004 * FS)
        p = sorted([sub(i1), sub(i2)])
        t.append(k * period / FS); d1.append(p[0] / FS * 1000); d2.append(p[1] / FS * 1000)
    t, d1, d2 = map(np.array, (t, d1, d2))
    if show:
        for k in range(0, len(t), 4): print(f'{t[k]:5.2f} s  d1 {d1[k]:6.3f} ms  d2 {d2[k]:6.3f} ms  sum {d1[k] + d2[k]:6.3f}')
    return t, d1, d2


if __name__ == '__main__':
    {'repeat': repeat, 'clicks': clicks, 'mix': mix, 'traj': trajectories}[sys.argv[1]]()
