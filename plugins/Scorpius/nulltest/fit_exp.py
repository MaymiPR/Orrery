"""The shared expander (MEASUREMENTS.md 3), against the reference's gain over time: 1 kHz tones whose level steps (drops
from above and below the threshold, rises, short bursts, repeated bursts, stairs), compression on at amount 0 so only
the expander acts, the gain in dB per 1 ms (one period). Prints the rms and largest error per pattern; FIT=1 fits the
constants (threshold, slope, the hold after the level last reached the threshold, the hold below it, the release).
The detector reads the group's output and its mid; STEREO=1 checks that with tones in one channel, inverted, at half
level and out of phase.
    python fit_exp.py"""
import os
import numpy as np
from scipy.optimize import minimize
import harness as o

FS = 48000
SPEC = dict(params={**o.ONLY('comp'), 'Comp Amount': 0})
KEYS = ['expThresholdDb', 'expSlope', 'expHoldMs', 'expShortHoldMs', 'expReleaseMs']


def pattern(segs):
    """a 1 kHz sine whose peak level steps: [(seconds, dBFS), ...]"""
    lev = np.concatenate([np.full(int(d * FS), 10 ** (l / 20)) for d, l in segs])
    return (lev * np.sin(2 * np.pi * 1000 * np.arange(len(lev)) / FS)).astype(np.float32)


def patterns():
    P = {}
    for hi in (-40, -56, -58, -60, -62, -66, -70):
        for lo in (-76, -85):
            P[f'drop {hi}>{lo}'] = [(1.0, -85), (0.5, hi), (2.5, lo)]
    P['drop -62>-68'] = [(1.0, -85), (0.5, -62), (2.5, -68)]
    P['drop -50>-62'] = [(1.0, -85), (0.5, -50), (2.5, -62)]
    P['rise -85>-66'] = [(1.0, -85), (1.0, -66)]
    P['rise -76>-62'] = [(1.0, -76), (1.0, -62)]
    for d in (0.002, 0.01, 0.05):
        P[f'burst -50 {d * 1000:.0f}ms'] = [(1.0, -76), (d, -50), (2.5, -76)]
        P[f'burst -60 {d * 1000:.0f}ms'] = [(1.0, -76), (d, -60), (1.5, -76)]
    P['bursts -62 20/100'] = [(1.0, -76)] + [(0.02, -62), (0.08, -76)] * 10 + [(1.0, -76)]
    P['bursts -62 20/300'] = [(1.0, -76)] + [(0.02, -62), (0.28, -76)] * 5 + [(1.0, -76)]
    P['stairs down'] = [(1.0, -85), (0.4, -58), (0.4, -61), (0.4, -64), (0.4, -67), (0.4, -70), (1.0, -85)]
    P['stairs up'] = [(1.0, -85), (0.4, -70), (0.4, -67), (0.4, -64), (0.4, -61), (0.4, -58), (1.0, -85)]
    return {k: pattern(v) for k, v in P.items()}


def traj(y, x):
    y = np.asarray(y, np.float64); x = np.asarray(x, np.float64); m = len(x) // 48
    return 10 * np.log10(np.sum(y[:m * 48].reshape(m, 48) ** 2, 1) / np.sum(x[:m * 48].reshape(m, 48) ** 2, 1))


X = patterns()
REF = [traj(r[0], x) for r, x in zip(o.render_many([dict(x=x, **SPEC) for x in X.values()], cache=True), X.values())]


def errors(v=None):
    tune = dict(zip(KEYS, v)) if v is not None else {}
    Y = o.render_many([dict(x=x, tune=tune, **SPEC) for x in X.values()], plugin='model')
    return [traj(y[0], x)[10:] - r[10:] for y, x, r in zip(Y, X.values(), REF)]   # (the first 10 ms: the render's ramp)


def report(v=None):
    for n, e in zip(X, errors(v)):
        print(f'{n:20s} rms {np.sqrt(np.mean(e ** 2)):5.2f}  largest {np.max(np.abs(e)):5.2f} dB')


if __name__ == '__main__':
    report()
    if os.environ.get('FIT'):
        cost = lambda v: float(np.sqrt(np.mean(np.concatenate(errors(v)) ** 2)))
        r = minimize(cost, [-58.18, 2.03, 1100.0, 100.0, 100.0], method='Nelder-Mead', options=dict(xatol=0.05, fatol=0.001, maxiter=120))
        print('fit', dict(zip(KEYS, np.round(r.x, 3))), round(r.fun, 4))
    if os.environ.get('STEREO'):
        t = np.arange(3 * FS) / FS; s = slice(2 * FS, None)
        for lv in (-60, -64, -68):
            a = 10 ** (lv / 20) * np.sin(2 * np.pi * 1000 * t); b = 10 ** (lv / 20) * np.sin(2 * np.pi * 1000 * t + 1.0)
            S = {'L only': [a, 0 * a], 'R inverted': [a, -a], 'R -6 dB': [a, 0.5 * a], 'R 1 rad later': [a, b]}
            xs = [np.array(v, np.float32) for v in S.values()]
            jobs = [dict(x=x, **SPEC) for x in xs]
            g = lambda y, x: 10 * np.log10(np.mean(np.asarray(y, np.float64)[0][s] ** 2) / np.mean(x[0][s].astype(np.float64) ** 2))
            pairs = zip(S, xs, o.render_many(jobs, cache=True), o.render_many(jobs, plugin='model'))
            print(lv, '  '.join(f'{k}: {g(r, x):6.2f} / {g(m, x):6.2f}' for k, x, r, m in pairs))
