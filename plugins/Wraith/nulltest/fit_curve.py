"""Character stage, the compressor's static curve as measured (MEASUREMENTS.md "Character"): on 1 kHz
staircases at every Compression setting (probe_static.py) the reference's curve is one curve of the driven level, its
slope rising smoothly from about 0.08 to 0.54 dB per dB over the 12 dB under its kink, to about 0.935 at it and on to
0.99 some 30 dB above it. One quadratic knee and one ratio leave 0.2 to 0.45 dB on either side of the kink. The model:
the slope at nine knots 5 dB apart, linear between them (Character.h, cmpCurve*), the first knot's level and the
make-up with them, fitted with CMA-ES (fit_char.run_cma), the dynamics as shipped, on fit_overshoot.py's cases plus
staircases, pink noise at low drive, a sweep and loud material at Compression +50; a held-out set is reported beside
it.

    python fit_curve.py [--iters 60] [--penalty 2] [--out renders/char_curve.json] [--start renders/char_curve.json]
    python fit_curve.py --eval [--start renders/char_curve.json]
"""
import argparse, json, os
import numpy as np
import nulltest_lib as nl
import wr_ref as h
import fit_char as fc
import fit_overshoot as fo

STEP = 5.0
START = [0.02, 0.1, 0.3, 0.85, 0.94, 0.945, 0.96, 0.975, 0.985]      # read off probe_static.py's reference curve
PARAMS = [('cmpCurveStartDb', -30.0, -40.0, -20.0, False), ('cmpMakeupDb', 0.322768, -6.0, 6.0, False)] + \
         [(f'cmpCurveSlope{k}', v, 0.0, 1.0, False) for k, v in enumerate(START)]
FIXED = {'cmpCurveStepDb': STEP}
OFF = {'cmpCurveStepDb': 0.0}      # --eval: the shipped knee and ratio beside the table


def cases():
    train, held = fo.cases()
    stairs = lambda f: nl.stereo(nl.steps(list(np.arange(-56.0, 1.0, 2.0)), 0.25, f=f)).astype(np.float32)
    s = lambda x: nl.stereo(x).astype(np.float32)
    train = train + [('stairs 1k c0 f8', stairs(1000), 0, 8), ('stairs 1k c-50 f50', stairs(1000), -50, 50),
                     ('stairs 1k c50 f8', stairs(1000), 50, 8),
                     ('pink c-50 f0', s(nl.pink(3.0, -18, seed=6)), -50, 0),
                     ('pink c-50 f50', s(nl.pink(3.0, -18, seed=8)), -50, 50),
                     ('pink c0 f0', s(nl.pink(3.0, -18, seed=13)), 0, 0),
                     ('sweep c50 f-30', s(nl.sweep(3.0, -12.0)), 50, -30),
                     ('sweep c0 f8', s(nl.sweep(3.0, -12.0)), 0, 8),
                     ('pink c50 f50 loud', s(nl.pink(3.0, -12, seed=14)), 50, 50),
                     ('music c50 f50 loud', s(nl.music(4.0, -6, seed=15)), 50, 50)]
    held = held + [('stairs 5k c0 f8', stairs(5000), 0, 8), ('pink c-50 f-30', s(nl.pink(3.0, -14, seed=10)), -50, -30)]
    return train, held


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--iters', type=int, default=60)
    ap.add_argument('--out', default=os.path.join(h.PLUGIN, 'nulltest', 'renders', 'char_curve.json'))
    ap.add_argument('--start', default=None)
    ap.add_argument('--eval', action='store_true')
    ap.add_argument('--sigma', type=float, default=0.08)
    ap.add_argument('--penalty', type=float, default=0.0,
                    help='weight on each training case\'s loss against the shipped curve (0: the plain mean)')
    a = ap.parse_args()
    train, held = cases()
    tj, hj = fc.jobs_of(train), fc.jobs_of(held)
    tref = h.render_many(tj, 'ref', cache=True); href = h.render_many(hj, 'ref', cache=True)
    start = json.load(open(a.start)) if a.start else {}
    if a.eval:
        for label, t in (('shipped curve', OFF), ('fitted table', dict(FIXED, **{k: start.get(k, s) for k, s, *_ in PARAMS}))):
            for name, cs, jb, rf in (('train', train, tj, tref), ('held-out', held, hj, href)):
                res = fc.evaluate([t], jb, rf)[0]
                print(f'{label}, {name}: ' + ', '.join(f'{c[0]} {r:.1f}' for c, r in zip(cs, res)) + f' | mean {np.mean(res):.2f} dB', flush=True)
        return
    if a.penalty > 0:             # a case that gets worse than with the shipped curve counts (1 + penalty) times
        base = np.array(fc.evaluate([OFF], tj, tref)[0])
        plain = fc.evaluate
        def penalised(tunes, jobs, refs):
            out = plain(tunes, jobs, refs)
            return [list(np.array(r) + a.penalty * np.maximum(0.0, np.array(r) - base)) if jobs is tj else r for r in out]
        fc.evaluate = penalised
    best = fc.run_cma(fc.from_tune(start, PARAMS), tj, tref, a.iters, a.sigma, a.out, PARAMS, FIXED)
    t = fc.to_tune(best[0], PARAMS, FIXED)
    print(json.dumps(t, indent=1))
    hres = fc.evaluate([t], hj, href)[0]
    for (name, *_), r in zip(held, hres): print(f'held-out {name:18s} {r:7.1f} dB')
    print(f'held-out mean {np.mean(hres):7.2f} dB')


if __name__ == '__main__':
    main()
