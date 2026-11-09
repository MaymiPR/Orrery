"""The mid band's steady gain against level, reference against ours: a 700 Hz tone in 1.5 s steps from -44 to +4 dBFS
(character only), the fundamental and the 3rd harmonic of each step's settled half by lock-in. The difference in the
fundamental shows the static curve and the shaper together; the 3rd harmonic re the fundamental shows the shaper's
drive, which separates them.

    python measure_mid_static.py [amount 0..1] [freq]"""
import sys
import numpy as np
import tgp

FS = tgp.FS; PRE = 2 * FS; STEP = int(1.5 * FS)
LEVELS = np.arange(-44, 5, 2.0)


def lock(y, f, a, b):
    t = np.arange(a, b) / FS
    return 2 * np.abs(np.mean(y[a:b] * np.exp(-2j * np.pi * f * t)))


if __name__ == '__main__':
    amt = float(sys.argv[1]) if len(sys.argv) > 1 else 0.5
    f0 = float(sys.argv[2]) if len(sys.argv) > 2 else 700.0
    n = PRE + STEP * len(LEVELS); t = np.arange(n) / FS
    a = np.zeros(n); a[PRE:] = np.repeat(10 ** (LEVELS / 20), STEP)
    x = (a * np.sin(2 * np.pi * f0 * t)).astype(np.float32)
    j = dict(x=x, norm={**tgp.CHAR_ONLY, 'Character': amt}, raw=True)
    r = tgp.render_many([j], 'ref', cache=True)[0][0]; o = tgp.render_many([j], 'model')[0][0]
    print(f'{amt * 200:.0f} %, {f0:.0f} Hz:  level   H1 ref (dB re in)   ours-ref (dB)   H3/H1 ref (dB)  ours-ref (dB)')
    for i, L in enumerate(LEVELS):
        s0, s1 = PRE + i * STEP + STEP // 2, PRE + (i + 1) * STEP
        h1r, h1o = lock(r, f0, s0, s1), lock(o, f0, s0, s1)
        h3r, h3o = lock(r, 3 * f0, s0, s1), lock(o, 3 * f0, s0, s1)
        print(f'{L:+6.0f}   {20 * np.log10(h1r / 10 ** (L / 20)):+9.4f}   {20 * np.log10(h1o / h1r):+9.4f}   '
              f'{20 * np.log10(h3r / h1r):9.2f}   {20 * np.log10(h3o / h1o) - 20 * np.log10(h3r / h1r):+7.3f}')
