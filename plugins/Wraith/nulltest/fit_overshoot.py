"""Character stage, the compressor's overshoot (MEASUREMENTS.md "Character"): after a step up the
reference's reduction overshoots its steady value by about 0.3 of it and comes back over a few hundred ms, and after
a short burst it lets go slowly, after a long one fast (probe_steps.py). The model: a share of the reduction above
its slow average, with its own attack and release (Character.h, cmpTr*), fitted with CMA-ES (fit_char.run_cma)
together with the compressor's constants on the stage's null: level steps, bursts, drums and music; a held-out set
is reported beside it.

    python fit_overshoot.py [--iters 60] [--out renders/char_tr.json] [--start renders/char_tr.json]
    python fit_overshoot.py --dynamics-only ...   the static curve, attack and make-up as shipped
    python fit_overshoot.py --eval [--start renders/char_tr.json] [--off]
"""
import argparse, json, os
import numpy as np
import nulltest_lib as nl
import wr_ref as h
import fit_char as fc

FS = 48000
# name, start, low, high, log scale
PARAMS = [('cmpTrAmount', 0.3, 0.0, 1.0, False), ('cmpTrAvgAttackMs', 150.0, 5.0, 3000.0, True),
          ('cmpTrAvgReleaseMs', 50.0, 1.0, 3000.0, True), ('cmpTrAttackMs', 3.0, 0.05, 100.0, True),
          ('cmpTrReleaseMs', 250.0, 5.0, 3000.0, True), ('cmpTrSmoothMs', 5.0, 0.05, 300.0, True),
          ('cmpThresholdDb', -16.513105, -40.0, 0.0, False), ('cmpRatio', 33.420335, 1.2, 100.0, True),
          ('cmpKneeDb', 6.581593, 0.0, 30.0, False), ('cmpAttackMs', 1.342135, 0.02, 50.0, True),
          ('cmpReleaseLowMs', 53.289792, 1.0, 2000.0, True), ('cmpReleaseHighMs', 137.583366, 1.0, 2000.0, True),
          ('cmpReleaseSwitchDb', 13.288304, 0.0, 40.0, False), ('cmpMakeupDb', 0.322768, -6.0, 6.0, False)]
FIXED = {}           # everything else as shipped (Tuning.h)
# --dynamics-only: the static curve, attack and make-up as shipped; the overshoot and the two release times fitted
DYN = [p for p in PARAMS if p[0].startswith('cmpTr') or p[0].startswith('cmpRelease')]
# --eval --off: the stage before the overshoot (no overshoot, the earlier release times)
BEFORE = {'cmpTrAmount': 0.0, 'cmpReleaseLowMs': 53.289792, 'cmpReleaseHighMs': 137.583366, 'cmpReleaseSwitchDb': 13.288304}


def cases():
    st = lambda levels, f=1000.0: nl.stereo(nl.steps(levels, 1.0, f=f)).astype(np.float32)
    bursts = [nl.tone(1000, 1.0, -40)]
    for ms in (1, 3, 10, 30, 100, 300):
        bursts += [nl.tone(1000, ms / 1000, -10), nl.tone(1000, 1.0, -40)]
    bursts = nl.stereo(np.concatenate(bursts)).astype(np.float32)
    s = lambda x: nl.stereo(x).astype(np.float32)
    train = [('steps 1k c0 f8', st([-40, -20, -40, -10, -40, 0, -40]), 0, 8),
             ('steps 1k c50 f50', st([-40, -30, -40, -20, -40, -10, -40]), 50, 50),
             ('bursts 1k c0 f8', bursts, 0, 8),
             ('drums c50 f50', s(nl.drums(3.0, -6)), 50, 50),
             ('drums c0 f8', s(nl.drums(3.0, -6)), 0, 8),
             ('music c0 f8', s(nl.music(4.0, -10)), 0, 8),
             ('music c50 f50', s(nl.music(4.0, -16, seed=7)), 50, 50),
             ('pink c0 f8', s(nl.pink(3.0, -18, seed=2)), 0, 8),
             ('pink c50 f50', s(nl.pink(3.0, -24, seed=3)), 50, 50),
             ('pink c-25 f0', s(nl.pink(3.0, -20, seed=5)), -25, 0),
             ('music c25 f-30', s(nl.music(4.0, -12, seed=12)), 25, -30)]
    held = [('music c25 f-30', s(nl.music(4.0, -12, seed=11)), 25, -30),
            ('pink c-25', s(nl.pink(3.0, -20, seed=4)), -25, 0),
            ('drums c50 f20', s(nl.drums(3.0, -10, seed=9)), 50, 20),
            ('steps 150 c0 f8', st([-40, -20, -40, -10, -40], 150.0), 0, 8)]
    return train, held


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--iters', type=int, default=60)
    ap.add_argument('--out', default=os.path.join(h.PLUGIN, 'nulltest', 'renders', 'char_tr.json'))
    ap.add_argument('--start', default=None)
    ap.add_argument('--eval', action='store_true')
    ap.add_argument('--off', action='store_true', help='with --eval: the stage before the overshoot')
    ap.add_argument('--sigma', type=float, default=0.12)
    ap.add_argument('--dynamics-only', action='store_true', help='fit the overshoot and the release times only')
    a = ap.parse_args()
    params = DYN if a.dynamics_only else PARAMS
    train, held = cases()
    tj, hj = fc.jobs_of(train), fc.jobs_of(held)
    tref = h.render_many(tj, 'ref', cache=True); href = h.render_many(hj, 'ref', cache=True)
    start = json.load(open(a.start)) if a.start else {}
    if a.eval:
        t = BEFORE if a.off else {k: start.get(k, s) for k, s, *_ in PARAMS}
        for label, cs, jb, rf in (('train', train, tj, tref), ('held-out', held, hj, href)):
            res = fc.evaluate([t], jb, rf)[0]
            for (name, *_), r in zip(cs, res): print(f'{label:8s} {name:18s} {r:7.1f} dB')
            print(f'{label:8s} mean {np.mean(res):7.2f} dB', flush=True)
        return
    best = fc.run_cma(fc.from_tune(start, params), tj, tref, a.iters, a.sigma, a.out, params, FIXED)
    t = fc.to_tune(best[0], params, FIXED)
    print(json.dumps(t, indent=1))
    hres = fc.evaluate([t], hj, href)[0]
    for (name, *_), r in zip(held, hres): print(f'held-out {name:18s} {r:7.1f} dB')
    print(f'held-out mean {np.mean(hres):7.2f} dB')


if __name__ == '__main__':
    main()
