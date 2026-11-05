"""The high band's release after a tone drops to -45 dBFS, from several levels and after several hold times: does its
speed follow the reduction (the same slope at the same level, whatever the start), the time since the drop, or how long
the band was compressed before? midrel.py's gain traces (8 kHz, --band high) read as detector level (midrel2.level_of).

    python hirel.py [amount 0..1] [freq]
Prints, per case, the detector level every 10 ms after the drop and its slope (dB/s), ref and ours."""
import sys
import numpy as np
import tgp, nulltest as N
import midrel as R, midrel2 as R2
from hightrace3 import header_laws

FS = tgp.FS
CASES = [(0, 3.0), (-3, 3.0), (-6, 3.0), (-9, 3.0), (0, 1.0), (0, 0.3), (0, 0.1), (0, 0.03)]
AFTER = 1.0


def signal(a, hold, f):
    n1, n2 = int(hold * FS), int(AFTER * FS); t = np.arange(n1 + n2) / FS
    lev = np.where(t < hold, 10 ** (a / 20), 10 ** (-45 / 20))
    x = (lev * np.sin(2 * np.pi * f * t)).astype(np.float32)
    x = np.concatenate([np.zeros(N.PRE + int(0.5 * FS), np.float32), x])     # 0.5 s of silence before the tone
    return np.vstack([x, x])


if __name__ == '__main__':
    amt = float(sys.argv[1]) if len(sys.argv) > 1 else 0.5
    f = float(sys.argv[2]) if len(sys.argv) > 2 else 8000.0
    R.BAND, R.FREQ = 2, f
    law = header_laws(int(round(amt * 16)))['high']
    xs = [signal(a, h, f) for a, h in CASES]
    nr, no = R.gains(xs, amt, True), R.gains(xs, amt, False)
    w = int(FS * 0.004); dt = 0.01
    for (a, h), r, o in zip(CASES, nr, no):
        i0 = int((0.5 + h) * FS)
        print(f'{a:+d} dBFS for {h * 1000:.0f} ms, then -45: level ref / ours, slope ref / ours (dB/s)')
        prev = None
        for t in np.arange(0.0, 0.32, dt):
            i = i0 + int(t * FS)
            lr = R2.level_of(np.nanmedian(r[i - w // 2:i + w // 2]), law); lo = R2.level_of(np.nanmedian(o[i - w // 2:i + w // 2]), law)
            if prev is not None and np.isfinite(lr) and lr > law['thresh'] + 0.5:
                print(f'   {t * 1000:4.0f} ms  {lr:7.2f} {lo:7.2f}   {(lr - prev[0]) / dt:7.1f} {(lo - prev[1]) / dt:7.1f}')
            prev = (lr, lo)


def staircase(f, lo=-24.0, hi=3.0, step=0.5, hold=0.25):
    """a rising tone staircase (only the attack acts), its levels"""
    levs = np.arange(lo, hi + 1e-9, step); n = int(hold * FS)
    t = np.arange(len(levs) * n) / FS
    a = np.repeat(10 ** (levs / 20), n)
    x = (a * np.sin(2 * np.pi * f * t)).astype(np.float32)
    x = np.concatenate([np.zeros(N.PRE, np.float32), x])
    return np.vstack([x, x]), levs, n


def static_curve(amt, f):
    """the band gain n (dB) at each step of the staircase, ref and ours: (levels, n_ref, n_ours)"""
    x, levs, n = staircase(f)
    R.BAND, R.FREQ = 2, f
    nr, no = R.gains([x], amt, True)[0], R.gains([x], amt, False)[0]
    med = lambda g: np.array([20 * np.log10(np.nanmedian(g[i * n + n // 2:(i + 1) * n])) for i in range(len(levs))])
    return levs, med(nr), med(no)


def level_through(nd, levs, curve):
    """detector level from a band gain (dB) through a measured static curve (monotone part)"""
    ok = curve < -1e-3
    c, l = curve[ok], levs[ok]
    return np.interp(nd, c[::-1], l[::-1], left=np.nan, right=np.nan)


def own_curve_slopes(amt, f):
    """the release slopes with each plug-in's traces read through its own static curve"""
    levs, cr, co = static_curve(amt, f)
    print('static curve (dB): level, ref n, ours n')
    for l, a, b in zip(levs[::4], cr[::4], co[::4]): print(f'   {l:6.1f} {a:8.3f} {b:8.3f}')
    xs = [signal(a, 3.0, f) for a in (0, -6)]
    nr, no = R.gains(xs, amt, True), R.gains(xs, amt, False)
    w = int(FS * 0.004); dt = 0.01
    for a, r, o in zip((0, -6), nr, no):
        i0 = int(3.5 * FS)
        print(f'{a:+d} dBFS, then -45, each read through its own curve: level ref / ours, slope ref / ours (dB/s)')
        prev = None
        for t in np.arange(0.0, 0.3, dt):
            i = i0 + int(t * FS)
            lr = level_through(20 * np.log10(np.nanmedian(r[i - w // 2:i + w // 2])), levs, cr)
            lo = level_through(20 * np.log10(np.nanmedian(o[i - w // 2:i + w // 2])), levs, co)
            if prev is not None and np.isfinite(lr):
                print(f'   {t * 1000:4.0f} ms  {lr:7.2f} {lo:7.2f}   {(lr - prev[0]) / dt:7.1f} {(lo - prev[1]) / dt:7.1f}')
            prev = (lr, lo)


def release_summary(amt, f, starts=(0, -6)):
    """median release slope (dB/s) 40 .. 200 ms after the drop, each plug-in through its own static curve"""
    levs, cr, co = static_curve(amt, f)
    xs = [signal(a, 3.0, f) for a in starts]
    nr, no = R.gains(xs, amt, True), R.gains(xs, amt, False)
    w = int(FS * 0.004); out = []
    for r, o in zip(nr, no):
        i0 = int(3.5 * FS); tt = np.arange(0.04, 0.2, 0.01)
        lr = np.array([level_through(20 * np.log10(np.nanmedian(r[i0 + int(t * FS) - w // 2:i0 + int(t * FS) + w // 2])), levs, cr) for t in tt])
        lo = np.array([level_through(20 * np.log10(np.nanmedian(o[i0 + int(t * FS) - w // 2:i0 + int(t * FS) + w // 2])), levs, co) for t in tt])
        out.append((np.nanmedian(np.diff(lr)) / 0.01, np.nanmedian(np.diff(lo)) / 0.01))
    return out


if __name__ == '__main__' and '--summary' in sys.argv:
    pass


def drop_signal(a, b, f, hold=1.0, after=1.0):
    n1, n2 = int(hold * FS), int(after * FS); t = np.arange(n1 + n2) / FS
    x = (np.where(t < hold, 10 ** (a / 20), 10 ** (b / 20)) * np.sin(2 * np.pi * f * t)).astype(np.float32)
    return np.vstack([np.concatenate([np.zeros(N.PRE + int(0.5 * FS), np.float32), x])] * 2)


def depth_slopes(amt, f, a=0.0, targets=(-3, -5, -7, -9, -11, -13, -15, -18, -21, -25, -30, -45), hold=1.0):
    """the release slope just after a drop from a to each target (10 .. 40 ms, or until 1 dB above the target), each
    plug-in through its own static curve"""
    levs, cr, co = static_curve(amt, f)
    xs = [drop_signal(a, b, f, hold) for b in targets]
    nr, no = R.gains(xs, amt, True), R.gains(xs, amt, False)
    w = int(FS * 0.004); i0 = int((0.5 + hold) * FS)
    print(f'{a:+.0f} dBFS for {hold:.1f} s, then the target: slope (dB/s) in 10 ms steps, ref / ours')
    for b, r, o in zip(targets, nr, no):
        rows = []
        for t in np.arange(0.005, 0.2, 0.01):
            i = i0 + int(t * FS)
            lr = level_through(20 * np.log10(np.nanmedian(r[i - w // 2:i + w // 2])), levs, cr)
            lo = level_through(20 * np.log10(np.nanmedian(o[i - w // 2:i + w // 2])), levs, co)
            rows.append((lr, lo))
        rows = np.array(rows); sl = np.diff(rows, axis=0) / 0.01
        txt = ' '.join(f'{p:5.0f}/{q:<4.0f}' for (p, q), (l1, _) in zip(sl[:8], rows[1:9]) if np.isfinite(p) and l1 > max(b, levs[0]) + 1)
        print(f'   to {b:+4d}: {txt}')
