"""What the mid band's detector hears (probe_det_spectrum.py's method for the mid band): a quiet 700 Hz probe (-40 dBFS) rides
along with a steady sine pump at frequency f; the probe's gain, read by lock-in over the settled second (each pump
rendered with the probe and with it inverted, half the difference kept), is the mid band's gain reduction caused by
the pump, so against f it traces the detector's frequency response. Reference against ours, character only.

    python probe_mid_det_spectrum.py [amount 0..1] [pump dBFS ...]
    python probe_mid_det_spectrum.py [amount] --map      each pump read as the in-band (450 Hz) level giving the same reduction,
                                            each plug-in through its own curve: the detector's response in dB
    --tune KEY=V (repeatable): our processor with a DSP constant overridden (tgp's tune, e.g. mid.cubic.8=0.996)"""
import sys
import numpy as np
import tgp

FS = tgp.FS; PRE = FS
FP = 700.0; PROBE = 10 ** (-40 / 20)
TUNE = {a.split('=')[0]: float(a.split('=')[1]) for i, a in enumerate(sys.argv) if i and sys.argv[i - 1] == '--tune'}
FREQS = [60, 90, 120, 157, 200, 300, 450, 1000, 1500, 2000, 2400, 2700, 3000, 3500, 4000, 5000, 8000]


def probe_gain(y, n):
    t = np.arange(n) / FS
    seg = slice(PRE + FS // 2, n - FS // 4)
    return np.abs(np.mean((y * np.exp(-2j * np.pi * FP * t))[seg])) * 2 / PROBE


def gains(amt, freqs, levs, n):
    """probe gain (dB re the probe alone) per (pump frequency, level), reference and ours"""
    t = np.arange(n) / FS
    probe = PROBE * np.sin(2 * np.pi * FP * t)
    pumps = [np.sin(2 * np.pi * f * t) * 10 ** (l / 20) for f, l in zip(freqs, levs)] + [0 * t]
    jobs = [dict(x=(p + s * probe).astype(np.float32), norm={**tgp.CHAR_ONLY, 'Character': amt}) for p in pumps for s in (1, -1)]
    out = []
    for y in (tgp.render_many(jobs, 'ref', cache=True), tgp.render_many([dict(j, tune=TUNE) for j in jobs], 'model')):
        g = [probe_gain(0.5 * (y[2 * i][0] - y[2 * i + 1][0]), n) for i in range(len(pumps))]
        out.append(20 * np.log10(np.array(g[:-1]) / g[-1]))
    return out


if __name__ == '__main__' and '--map' in sys.argv:
    amt = float(sys.argv[1]) if not sys.argv[1].startswith('--') else 0.5
    n = PRE + 2 * FS
    cl = np.arange(-30.0, 3.01, 1.0)
    cr, co = gains(amt, [450] * len(cl), cl, n)
    fl = [(f, l) for l in (-6.0, -12.0, 0.0) for f in FREQS if f != 450]
    gr, go = gains(amt, [f for f, _ in fl], [l for _, l in fl], n)
    inv = lambda g, c: np.interp(-g, -c, cl) if -g > -c[0] else np.nan       # the curve falls with level
    print(f'amount {amt}: pump level (dBFS) and the in-band level each plug-in reads it as; diff = ours - ref (dB)')
    for (f, l), a, b in zip(fl, gr, go):
        la, lb = inv(a, cr), inv(b, co)
        print(f'{l:+5.0f} dBFS {f:6d} Hz   gain ref {a:+7.3f} ours {b:+7.3f}   reads as ref {la:7.2f} ours {lb:7.2f}   diff {lb - la:+.2f}', flush=True)
    raise SystemExit


if __name__ == '__main__':
    args = [a for a in sys.argv[1:]]
    amt = float(args[0]) if args else 0.5
    levs = [float(a) for a in args[1:]] or [-6.0, -12.0]
    n = PRE + 2 * FS; t = np.arange(n) / FS
    probe = PROBE * np.sin(2 * np.pi * FP * t)
    for lev in levs:
        pumps = [np.sin(2 * np.pi * f * t) * 10 ** (lev / 20) for f in FREQS] + [0 * t]
        jobs = [dict(x=(p + s * probe).astype(np.float32), norm={**tgp.CHAR_ONLY, 'Character': amt}) for p in pumps for s in (1, -1)]
        rr = tgp.render_many(jobs, 'ref', cache=True); oo = tgp.render_many(jobs, 'model')
        g = lambda y, i: probe_gain(0.5 * (y[2 * i][0] - y[2 * i + 1][0]), n)
        br, bo = g(rr, len(FREQS)), g(oo, len(FREQS))
        print(f'amount {amt}, pump {lev} dBFS: probe gain re probe alone (dB)')
        for i, f in enumerate(FREQS):
            a, b = 20 * np.log10(g(rr, i) / br), 20 * np.log10(g(oo, i) / bo)
            print(f'{f:6d} Hz   ref {a:+7.3f}   ours {b:+7.3f}   diff {b - a:+.3f}', flush=True)
