"""midrel.py's gain traces turned into the mid detector's level (dB), through the band's static law (which matches the
reference's steady gain to 0.01 dB), and the release's speed in dB/s against that level: one release time or two?

    python midrel2.py [amount] [--band high [freq]]"""
import sys
import numpy as np
import midrel as R
from hightrace3 import header_laws

FS = R.FS
STEP = 0.05


def level_of(n, law):
    """detector level (dB, sine peak) from the band gain n through the soft-knee law"""
    mix, th, kn = law['mix'], law['thresh'], law['knee']; sl = 1 - 1 / law['ratio']
    lv = np.linspace(-80, 20, 20001); over = lv - th
    g = np.where(2 * over >= kn, sl * over, np.where(2 * over > -kn, sl * (over + kn / 2) ** 2 / (2 * kn), 0.0))
    nn = (1 - mix) + mix * 10 ** (-g / 20)
    ok = g > 1e-4                       # only where the curve is invertible
    return np.interp(n, nn[ok][::-1], lv[ok][::-1], left=np.nan, right=np.nan)


if __name__ == '__main__':
    f = 700.0
    if '--band' in sys.argv:
        i = sys.argv.index('--band'); R.BAND = R.CM.NAMES.index(sys.argv[i + 1]); f = float(sys.argv[i + 2]); del sys.argv[i:i + 3]
    R.FREQ = f
    amt = float(sys.argv[1]) if len(sys.argv) > 1 else 0.5
    law = header_laws(int(round(amt * 16)))[R.CM.NAMES[R.BAND]]
    steps = [(0, -20), (0, -30), (0, -45), (-12, -24), (-20, -45)]
    xs = [R.step_signal(a, b, f) for a, b in steps]
    nr, no = R.gains(xs, amt, True), R.gains(xs, amt, False)
    if R.BAND == 2: STEP = 0.02
    w = int(FS * 0.01)
    for (a, b), r, o in zip(steps, nr, no):
        print(f'{a:+d} -> {b:+d} dBFS: detector level (dB) every 50 ms, and its slope (dB/s)')
        i0 = int(R.HOLD * FS)
        rows = []
        for t in np.arange(0.0, 1.2, STEP):
            i = i0 + int(t * FS)
            lr = level_of(np.nanmedian(r[i:i + w]), law); lo = level_of(np.nanmedian(o[i:i + w]), law)
            rows.append((t, lr, lo))
        for k in range(1, len(rows)):
            t, lr, lo = rows[k]; sr = (lr - rows[k - 1][1]) / STEP; so = (lo - rows[k - 1][2]) / STEP
            if np.isfinite(lr) or np.isfinite(lo):
                print(f'   {t*1000:5.0f} ms  ref {lr:7.2f} ours {lo:7.2f}   slope ref {sr:7.1f} ours {so:7.1f}')
