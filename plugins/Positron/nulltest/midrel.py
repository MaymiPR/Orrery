"""The mid band's gain n(t) after level steps of a steady tone, reference against ours: does the release (and the
attack) keep one speed at every depth, or does it change with the level or the reduction? The low and high bands'
outputs (charmodel.py with the plug-in's table) are taken off the output, the rest is inverted through the mid shaper
(hightrace2.invert) and read as the band gain in dB, one median per cycle.

    python midrel.py [amount 0..1] [freq] [--band high]     default 0.5 (100 %), 700 Hz, the mid band
Prints the reduction (dB) at fixed times after each step, ref and ours, and the time each takes to cover 50 / 90 %
of the change."""
import sys
import numpy as np
import tgp, nulltest as N, ident as I, charmodel as CM
from hightrace2 import invert
from hightrace3 import header_laws

FS = tgp.FS
BAND = 1
FREQ = 700.0
EXTRA = {}            # law overrides for our side (experiments), {'high': {'fallRate': 46}}
STEPS = [(0, -10), (0, -20), (0, -30), (0, -45), (-6, -12), (-12, -24), (-20, -30), (-20, -45),
         (-45, 0), (-30, 0), (-20, 0), (-12, 0), (-30, -12), (-45, -20)]
HOLD = 3.0
TIMES = [-0.005, -0.002, 0.001,0.003, 0.01, 0.03, 0.06, 0.1, 0.2, 0.3, 0.5, 1.0, 2.0, 2.9]


def step_signal(a, b, f):
    n = int(HOLD * FS); t = np.arange(2 * n) / FS
    lev = np.where(t < HOLD, 10 ** (a / 20), 10 ** (b / 20))
    x = (lev * np.sin(2 * np.pi * f * t)).astype(np.float32)
    x = np.concatenate([np.zeros(N.PRE, np.float32), x])
    return np.vstack([x, x])


def gains(xs, amt, ref):
    row = int(round(amt * 16)); laws = header_laws(row)
    for b, e in EXTRA.items(): laws[b] = dict(laws[b], **e)
    jobs = [dict(x=x, norm={**tgp.CHAR_ONLY, 'Character': amt}, raw=True) for x in xs]
    rs = tgp.render_many(jobs, 'ref', cache=True) if ref else None
    out = []
    for i, x in enumerate(xs):
        xb, sb = CM.prep(x)
        ys = [CM.band(xb[b], sb[b], laws[CM.NAMES[b]], I.GAINS16[b][row], CM.WIDTH[CM.NAMES[b]][row]) for b in range(3)]
        y = rs[i] if ref else sum(ys)
        B = BAND
        yh = (y - sum(ys[b] for b in range(3) if b != B))[0]
        M = 10 ** (I.GAINS16[B][row] / 20); k, d = laws[CM.NAMES[B]]['k'], laws[CM.NAMES[B]]['shapeDry']
        s = sb[B][0]
        u = invert(yh / M - (xb[B][0] - s), k, d)
        from scipy.ndimage import maximum_filter1d
        env = maximum_filter1d(np.abs(s), int(2 * FS / FREQ) + 1)      # the local amplitude (two cycles)
        with np.errstate(all='ignore'): n = np.where(np.abs(s) > 0.3 * env, u / s, np.nan)
        out.append(n[N.PRE:])
    return out


def at(n, t0, t, w):
    i = int((t0 + t) * FS)
    return 20 * np.log10(np.nanmedian(n[max(0, i - w // 2):i + w // 2]))


if __name__ == '__main__':
    if '--band' in sys.argv:
        i = sys.argv.index('--band'); BAND = CM.NAMES.index(sys.argv[i + 1]); del sys.argv[i:i + 2]
    amt = float(sys.argv[1]) if len(sys.argv) > 1 else 0.5
    f = float(sys.argv[2]) if len(sys.argv) > 2 else 700.0
    FREQ = f; w = int(round(FS / f))
    xs = [step_signal(a, b, f) for a, b in STEPS]
    nr, no = gains(xs, amt, True), gains(xs, amt, False)
    print('times (ms):', ' '.join('%7g' % (t * 1000) for t in TIMES))
    for (a, b), r, o in zip(STEPS, nr, no):
        pre_r, pre_o = at(r, 0, HOLD - 0.05, 4 * w), at(o, 0, HOLD - 0.05, 4 * w)
        tr = np.array([at(r, HOLD, t, w) for t in TIMES]); to = np.array([at(o, HOLD, t, w) for t in TIMES])
        print(f'{a:+4d} -> {b:+4d} dBFS   before: ref {pre_r:7.3f} ours {pre_o:7.3f}')
        print('   ref ', ' '.join('%7.3f' % v for v in tr))
        print('   ours', ' '.join('%7.3f' % v for v in to))
        print('   diff', ' '.join('%7.3f' % v for v in to - tr))
